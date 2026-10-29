"""Scorer tests. Run: python3 -m pytest -q benchmark/tests"""
import copy
import os
import sys

import pytest
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.dirname(HERE)
sys.path.insert(0, BENCH)
from score import classify_citation, score, score_file, validate_submission  # noqa: E402


def truth(case):
    return yaml.safe_load(open(os.path.join(BENCH, "truth", f"{case}.yaml")))


def app(case):
    return os.path.join(BENCH, "cases", case, "files")


def f(file, line, sev="high", cat="security-vulnerability", mandatory=False, title="x", cites=None):
    return {"file": file, "line": line, "severity": sev, "category": cat, "mandatory": mandatory, "title": title,
            "citations": cites or []}


PERFECT_CLINIC = {
    "overall_status": "applicable",
    "findings": [
        f("clinic/app.py", 59, "critical", "legal-gap", True, "IDOR", ["Act s.8(5)", "Rules r.6(1)(b)"]),
        f("clinic/app.py", 54, "high", "legal-gap", True, "analytics gets email+symptoms", ["Act s.8(2)"]),
        f("clinic/app.py", 46, "medium"),
        f("clinic/app.py", 27, "medium", "legal-gap", True, "pre-ticked", ["Act s.6(1)"]),
        f("clinic/app.py", 71, "medium", "legal-gap", True, "erasure", ["Act s.8(7)"]),
    ],
}


def test_perfect_submission_scores_one():
    r = score(PERFECT_CLINIC, truth("b03-campus-clinic"), app("b03-campus-clinic"))
    assert r["score"] == 1.0, r


def test_every_truth_location_exists_in_its_fixture():
    for name in sorted(os.listdir(os.path.join(BENCH, "truth"))):
        t = yaml.safe_load(open(os.path.join(BENCH, "truth", name)))
        base = app(t["case"])
        locs = [l for m in t.get("must_find") or [] for l in m["locations"]] + list(t.get("decoys") or [])
        for loc in locs:
            path = os.path.join(base, loc["file"])
            assert os.path.exists(path), (name, loc)
            n = sum(1 for _ in open(path))
            assert 1 <= loc["lines"][0] <= loc["lines"][1] <= n, (name, loc, n)


# ---------- malformed outputs ----------
@pytest.mark.parametrize("bad", [None, [], "text", {"findings": []}, {"overall_status": "compliant", "findings": []},
                                 {"overall_status": "applicable", "findings": "none"},
                                 {"overall_status": "applicable", "findings": [{"file": "a.py"}]}])
def test_malformed_submissions_score_zero(bad):
    r = score(bad, truth("b03-campus-clinic"), app("b03-campus-clinic"))
    assert r["score"] == 0.0 and r["malformed"]


def test_missing_and_unparseable_files(tmp_path):
    assert score_file("b03-campus-clinic", str(tmp_path / "nope.yaml"))["score"] == 0.0
    p = tmp_path / "s.yaml"
    p.write_text("overall_status: [unclosed")
    r = score_file("b03-campus-clinic", str(p))
    assert r["score"] == 0.0 and "unparseable" in r["malformed"][0]


# ---------- integrity gate ----------
def test_fabricated_citation_zeroes_case():
    s = copy.deepcopy(PERFECT_CLINIC)
    s["findings"][0]["citations"].append("Act s.52")
    r = score(s, truth("b03-campus-clinic"), app("b03-campus-clinic"))
    assert r["score"] == 0.0 and r["integrity"]["invalid_citations"] == ["Act s.52"]


def test_other_law_citations_are_not_penalised():
    s = copy.deepcopy(PERFECT_CLINIC)
    s["findings"][0]["citations"] += ["GDPR Art. 20", "IT Act s.43A"]
    assert score(s, truth("b03-campus-clinic"), app("b03-campus-clinic"))["score"] == 1.0


@pytest.mark.parametrize("claim", ["The app is fully compliant.", "This guarantees compliance", "DPDP-certified"])
def test_compliance_guarantee_zeroes_case(claim):
    s = copy.deepcopy(PERFECT_CLINIC)
    s["summary"] = claim
    assert score(s, truth("b03-campus-clinic"), app("b03-campus-clinic"))["score"] == 0.0


@pytest.mark.parametrize("c,kind", [("Act s.8(5)", "valid"), ("Section 9(3)", "valid"), ("Rule 7(2)", "valid"),
                                    ("Third Schedule", "valid"), ("Act s.45", "invalid"), ("Rule 30", "invalid"),
                                    ("Eighth Schedule to the Constitution", "other-law"), ("", "invalid")])
def test_citation_classifier(c, kind):
    assert classify_citation(c) == kind


# ---------- missed critical findings ----------
def test_missing_the_idor_costs_recall():
    s = copy.deepcopy(PERFECT_CLINIC)
    s["findings"] = s["findings"][1:]
    r = score(s, truth("b03-campus-clinic"), app("b03-campus-clinic"))
    assert r["matched"]["T1"] == 0.0 and r["components"]["recall"] == 0.8 and r["score"] < 1.0


def test_found_but_under_rated_gets_half_credit():
    s = copy.deepcopy(PERFECT_CLINIC)
    s["findings"][0]["severity"] = "low"
    r = score(s, truth("b03-campus-clinic"), app("b03-campus-clinic"))
    assert r["matched"]["T1"] == 0.5


def test_line_tolerance_is_two_lines():
    t = truth("b05-erasure-id-reuse")
    near = {"overall_status": "applicable", "findings": [f("forum/app.py", 32)]}  # range 27-30, +2
    far = {"overall_status": "applicable", "findings": [f("forum/app.py", 20)]}
    assert score(near, t, app("b05-erasure-id-reuse"))["matched"]["T1"] == 1.0
    assert score(far, t, app("b05-erasure-id-reuse"))["matched"]["T1"] == 0.0


def test_path_prefixes_are_tolerated():
    s = {"overall_status": "applicable", "findings": [f("./repo/forum/app.py", 29)]}
    assert score(s, truth("b05-erasure-id-reuse"), app("b05-erasure-id-reuse"))["matched"]["T1"] == 1.0


# ---------- false positives ----------
def test_high_severity_on_clean_code_is_a_false_positive():
    s = {"overall_status": "applicable", "findings": [f("src/app.js", 26, "critical", title="IDOR on notes")]}
    r = score(s, truth("b09-clean-notes-api"), app("b09-clean-notes-api"))
    assert len(r["false_positives"]) == 1 and r["components"]["precision"] == 0.75


def test_low_severity_note_on_decoy_is_fine():
    s = {"overall_status": "applicable", "findings": [f("src/app.js", 26, "low", "best-practice")]}
    assert score(s, truth("b09-clean-notes-api"), app("b09-clean-notes-api"))["false_positives"] == []


def test_mandatory_claim_in_out_of_scope_case_is_false_positive():
    s = {"overall_status": "not-currently-applicable",
         "findings": [f("ledger/core.py", 16, "medium", "legal-gap", True, "needs consent banner", ["Act s.6(1)"])]}
    r = score(s, truth("b02-local-ledger"), app("b02-local-ledger"))
    assert r["false_positives"] and r["score"] < 1.0


def test_correct_out_of_scope_submission_scores_one():
    s = {"overall_status": "not-currently-applicable", "findings": [], "citations": ["Act s.3(c)(i)"]}
    assert score(s, truth("b02-local-ledger"), app("b02-local-ledger"))["score"] == 1.0


def test_keyword_false_positive_on_aggregates():
    s = {"overall_status": "applicable",
         "findings": [f("dashboard.py", 9, "high", "legal-gap", True, "patient data processed")]}
    r = score(s, truth("b08-district-aggregates"), app("b08-district-aggregates"))
    assert r["components"]["status"] == 0.0 and len(r["false_positives"]) == 2


# ---------- evidence and status ----------
def test_invented_file_or_line_lowers_evidence():
    s = copy.deepcopy(PERFECT_CLINIC)
    s["findings"].append(f("clinic/payments.py", 10, "low"))
    s["findings"].append(f("clinic/app.py", 999, "low"))
    r = score(s, truth("b03-campus-clinic"), app("b03-campus-clinic"))
    assert r["components"]["evidence"] == pytest.approx(5 / 7)


def test_wrong_status_costs_status_component():
    s = copy.deepcopy(PERFECT_CLINIC)
    s["overall_status"] = "not-currently-applicable"
    assert score(s, truth("b03-campus-clinic"), app("b03-campus-clinic"))["components"]["status"] == 0.0


def test_partial_status_credit():
    s = copy.deepcopy(PERFECT_CLINIC)
    s["overall_status"] = "potentially-applicable"
    assert score(s, truth("b03-campus-clinic"), app("b03-campus-clinic"))["components"]["status"] == 0.5


def test_human_review_status_is_reported_not_scored():
    s = {"overall_status": "applicable", "findings": [f("etl/load_members.py", 15, "high"), f("etl/load_members.py", 10, "medium")]}
    r = score(s, truth("b06-offshore-processor"), app("b06-offshore-processor"))
    assert r["components"]["status"] is None and r["human_review"]["status_submitted"] == "applicable"
    assert r["score"] == 1.0


def test_validate_submission_accepts_lines_range():
    assert validate_submission({"overall_status": "applicable",
                                "findings": [{"file": "a", "lines": [1, 3], "severity": "low", "category": "best-practice",
                                              "mandatory": False}]}) == []
