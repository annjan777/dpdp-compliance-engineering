"""Deterministic tests for the skill's guard rails. Run: python3 -m pytest -q scripts/tests"""
import copy
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.dirname(HERE))
from validate_assessment import DEFAULT_CATALOG, Report, check_repo, load, validate  # noqa: E402

CATALOG = load(DEFAULT_CATALOG)
OUT_OF_SCOPE = os.path.join(SKILL, "examples", "pocket-ledger", ".dpdp", "assessment.yaml")
IN_SCOPE = os.path.join(SKILL, "examples", "campus-clinic", ".dpdp", "assessment.yaml")


def errors(a, strict=False):
    return validate(a, CATALOG, strict).errors


@pytest.fixture
def oos():
    return copy.deepcopy(load(OUT_OF_SCOPE))


@pytest.fixture
def ins():
    return copy.deepcopy(load(IN_SCOPE))


# ---------- the worked examples are valid ----------
def test_out_of_scope_example_passes_strict(oos):
    assert errors(oos, strict=True) == []


def test_in_scope_example_passes_strict(ins):
    assert errors(ins, strict=True) == []


# ---------- applicability handling ----------
def test_developer_claim_alone_cannot_put_app_out_of_scope(oos):
    act = oos["applicability"]["activities"][0]
    act["facts"] = ["E-001"]  # only the author's reported statement
    errs = errors(oos)
    assert any("verified evidence" in e for e in errs)


def test_out_of_scope_needs_basis_provision(oos):
    oos["applicability"]["overall"]["provisions"] = []
    assert any("basis provision" in e for e in errors(oos))


def test_overall_cannot_be_out_of_scope_when_an_activity_applies(ins):
    ins["applicability"]["overall"]["status"] = "not-currently-applicable"
    ins["applicability"]["overall"]["provisions"] = ["Act s.3(c)(i)"]
    assert any("cannot be not-currently-applicable" in e for e in errors(ins))


def test_potentially_applicable_needs_a_deciding_question(oos):
    act = oos["applicability"]["activities"][0]
    act["status"] = "potentially-applicable"
    act["legal_questions"] = []
    assert any("legal question or unknown" in e for e in errors(oos))


def test_in_force_must_match_commencement(ins):
    ins["requirements"][0]["in_force"] = "yes"  # 2027-05-13 provision on a 2026-10-29 assessment
    assert any("in_force" in e for e in errors(ins))


# ---------- citation discipline ----------
@pytest.mark.parametrize("bad", ["Act s.45", "Rules r.30", "Section 8 GDPR", "Act section 8", "Rules Sch.9"])
def test_fabricated_or_malformed_citations_rejected(oos, bad):
    oos["applicability"]["overall"]["provisions"] = [bad]
    assert any("citation" in e for e in errors(oos))


def test_out_of_range_citation_in_free_text_rejected(oos):
    oos["applicability"]["overall"]["reasoning"] += " See Act s.52 for the startup exemption."
    assert any("outside the range" in e for e in errors(oos))


def test_invented_requirement_id_rejected(oos):
    oos["requirements"].append({"req_id": "DPDP-PORT-01", "status": "applicable", "in_force": "no"})
    assert any("not in requirements-catalog" in e for e in errors(oos))


# ---------- uncertainty escalation ----------
def test_legal_review_flag_needs_a_question(ins):
    rq = next(r for r in ins["requirements"] if r["req_id"] == "DPDP-RET-01")
    for q in ins["legal_questions"]:
        q["related"] = [x for x in q.get("related", []) if x != "DPDP-RET-01"]
        q["why"] = q["why"].replace("DPDP-RET-01", "")
    assert rq["legal_review"] is True
    assert any("no legal question lists DPDP-RET-01" in e for e in errors(ins))


def test_agent_cannot_close_a_legal_question(ins):
    q = ins["legal_questions"][0]
    q.update(status="answered", answer="Yes", answer_source="legal-mapping agent")
    assert any("only a qualified human" in e for e in errors(ins))


def test_blocking_question_forbids_no_review_flag(ins):
    ins["applicability"]["overall"]["legal_review_required"] = False
    assert any("blocking legal questions" in e for e in errors(ins))


# ---------- code verification and truthful reporting ----------
def test_pass_without_execution_rejected(ins):
    ins["verification"][0]["executed"] = False
    assert any("without executed: true" in e for e in errors(ins))


def test_pass_without_saved_output_rejected(ins):
    ins["verification"][0]["output_ref"] = None
    assert any("output_ref" in e for e in errors(ins))


def test_verified_finding_needs_passing_test(ins):
    f = next(f for f in ins["findings"] if f["id"] == "F-09")  # planned, not implemented
    f["status"] = "verified"
    errs = errors(ins)
    assert any("F-09" in e and "no implementation entry" in e for e in errs)


def test_unapproved_change_cannot_be_implemented(ins):
    ins["implementation"].append({"plan_id": "P-09", "files_changed": ["clinic/app.py"], "commit": "x"})
    assert any("without recorded approval" in e for e in errors(ins))


@pytest.mark.parametrize("claim", ["The application is fully compliant.", "We guarantee compliance.",
                                   "Portal is now compliant with the DPDP Act", "DPDP-certified build"])
def test_compliance_guarantees_rejected(ins, claim):
    ins["next_steps"].append(claim)
    assert any("compliance guarantee" in e for e in errors(ins))


@pytest.mark.parametrize("leak", ["contact jane.roe@mailcorp.co", "call 9876543210", "aadhaar 2345 6789 0123",
                                  "key " + "sk-" + "x" * 30])  # key built at runtime so secret scanners ignore it
def test_personal_data_and_secrets_rejected(ins, leak):
    ins["evidence"][0]["summary"] = leak
    assert any("never put personal data" in e for e in errors(ins))


def test_synthetic_email_domains_allowed(ins):
    ins["evidence"][0]["summary"] = "fixture uses a@example.test"
    assert errors(ins) == errors(copy.deepcopy(load(IN_SCOPE)))


# ---------- mandatory vs optional ----------
def test_best_practice_cannot_be_mandatory(oos):
    oos["findings"][1]["mandatory"] = True
    assert any("only legal-gap findings can be mandatory" in e for e in errors(oos))


def test_legal_gap_needs_applicable_requirement(oos):
    oos["findings"][0].update(category="legal-gap", mandatory=True, req_id="DPDP-SCOPE-03")
    assert any("legal-gap against" in e for e in errors(oos))


def test_strict_requires_independent_check_for_material_verified_findings(ins):
    for v in ins["verification"]:
        v["independent"] = False
    assert errors(ins) == []  # warning only in normal mode
    assert any("independent" in e for e in errors(ins, strict=True))


def test_repo_check_rejects_invented_commit_and_output(oos, tmp_path):
    import subprocess
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    oos["implementation"][0]["commit"] = "deadbee"
    r = Report()
    check_repo(oos, str(tmp_path), r)
    assert any("commit deadbee not found" in e for e in r.errors)
    assert any("output_ref" in e for e in r.errors)
