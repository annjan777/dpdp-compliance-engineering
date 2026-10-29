#!/usr/bin/env python3
"""Deterministic scorer for the DPDP agent benchmark.

Scores one submission (dpdp-submission.yaml) against one case's ground truth.
Legal judgments flagged human_review in the truth file are reported, not scored.

Usage:
  python3 score.py --case b03-campus-clinic --submission path/to/dpdp-submission.yaml [--json]
  python3 score.py --runs-dir DIR          # score every DIR/<case>/<arm>/<run>/dpdp-submission.yaml
Scoring rules are documented in benchmark/README.md.
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
from validate_assessment import FORBIDDEN_CLAIMS, check_citation, load, walk_strings  # noqa: E402

STATUSES = {"applicable", "partially-applicable", "potentially-applicable", "not-currently-applicable", "undetermined"}
SEV = {"low": 1, "medium": 2, "high": 3, "critical": 4}
CATEGORIES = {"legal-gap", "security-vulnerability", "operational-weakness", "best-practice"}
LINE_TOLERANCE = 2
WEIGHTS = {"recall": 0.5, "status": 0.2, "precision": 0.15, "evidence": 0.15}


OTHER_LAW = re.compile(r"\b(gdpr|it act|information technology act|hipaa|aadhaar act|rti|ccpa|constitution|eighth schedule|article \d+ of the constitution|art\. ?\d+)\b", re.I)
SECTION = re.compile(r"^(?:dpdp(?:a)?\s*(?:act)?[,\s]*)?(?:act\s+)?(?:s\.|sec\.?|section)\s*(\d+)((?:\(\w+\))*)(?:\s+of the (?:dpdp|digital personal data protection) act(?:,? 2023)?)?$", re.I)
RULE = re.compile(r"^(?:dpdp\s*)?(?:rules\s+)?(?:r\.|rule)\s*(\d+)((?:\(\w+\))*)(?:\s+of the (?:dpdp|digital personal data protection) rules(?:,? 2025)?)?$", re.I)
SCHED = re.compile(r"^(?:dpdp\s*)?(?:rules\s+)?(?:sch\.|schedule)\s*(\d+|first|second|third|fourth|fifth|sixth|seventh)\b.*$", re.I)
ORD = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6, "seventh": 7}


def classify_citation(c):
    """'valid', 'invalid' (non-existent DPDP provision / unparseable), or 'other-law' (not scored).

    Accepts the registry format (Act s.8(5), Rules r.7(2)) and common variants (Section 8(5), Rule 7).
    shortcut: checks that the provision exists, not that it says what the agent claims; content errors
    such as 's.13 requires portability' need the LLM graders or human review.
    """
    if not isinstance(c, str) or not c.strip():
        return "invalid"
    c = c.strip()
    if check_citation(c):
        return "valid"
    if OTHER_LAW.search(c):
        return "other-law"
    c2 = re.sub(r"\s+", " ", c.replace("DPDP Act", "").replace("DPDPA", "")).strip(" ,")
    m = SECTION.match(c2) or SECTION.match(c)
    if m:
        return "valid" if 1 <= int(m.group(1)) <= 44 else "invalid"
    m = RULE.match(c2) or RULE.match(c)
    if m:
        return "valid" if 1 <= int(m.group(1)) <= 23 else "invalid"
    m = SCHED.match(c2) or re.match(r"^(first|second|third|fourth|fifth|sixth|seventh) schedule\b", c2, re.I)
    if m:
        n = ORD.get(m.group(1).lower()) or int(m.group(1))
        return "valid" if 1 <= n <= 7 else "invalid"
    return "invalid"


def _lines(f):
    """Return (start, end) for a finding; accepts line: N or lines: [a, b]."""
    if isinstance(f.get("lines"), list) and f["lines"]:
        a, b = f["lines"][0], f["lines"][-1]
    else:
        a = b = f.get("line")
    return (int(a), int(b)) if isinstance(a, int) and isinstance(b, int) else None


def _same_file(sub_path, truth_path):
    s = str(sub_path or "").replace("\\", "/").lstrip("./")
    return s == truth_path or s.endswith("/" + truth_path)


def _hits(f, loc):
    rng = _lines(f)
    if not rng or not _same_file(f.get("file"), loc["file"]):
        return False
    lo, hi = loc["lines"]
    return rng[0] <= hi + LINE_TOLERANCE and rng[1] >= lo - LINE_TOLERANCE


def validate_submission(sub):
    """Return a list of schema problems; empty means well-formed."""
    errs = []
    if not isinstance(sub, dict):
        return ["submission is not a mapping"]
    if sub.get("overall_status") not in STATUSES:
        errs.append(f"overall_status must be one of {sorted(STATUSES)}")
    if not isinstance(sub.get("findings"), list):
        errs.append("findings must be a list")
        return errs
    for i, f in enumerate(sub["findings"]):
        if not isinstance(f, dict):
            errs.append(f"findings[{i}] is not a mapping")
            continue
        if f.get("severity") not in SEV:
            errs.append(f"findings[{i}].severity must be one of {sorted(SEV)}")
        if f.get("category") not in CATEGORIES:
            errs.append(f"findings[{i}].category must be one of {sorted(CATEGORIES)}")
        if not isinstance(f.get("mandatory"), bool):
            errs.append(f"findings[{i}].mandatory must be true/false")
        if not f.get("file") or _lines(f) is None:
            errs.append(f"findings[{i}] needs file and line (or lines: [start, end])")
    return errs


def _file_lengths(app_dir):
    out = {}
    for root, _, files in os.walk(app_dir):
        for n in files:
            p = os.path.join(root, n)
            try:
                with open(p, encoding="utf-8", errors="ignore") as fh:
                    out[os.path.relpath(p, app_dir).replace("\\", "/")] = sum(1 for _ in fh)
            except OSError:
                pass
    return out


def score(sub, truth, app_dir):
    res = {"case": truth["case"], "malformed": [], "integrity": {}, "components": {}, "matched": {}, "false_positives": [],
           "human_review": {}, "notes": []}
    errs = validate_submission(sub)
    if errs:
        res["malformed"] = errs
        res["score"] = 0.0
        return res
    findings = sub["findings"]

    # Integrity gate: fabricated citations or compliance guarantees zero the case.
    bad_cites, other_law = [], []
    for c in [c for f in findings for c in (f.get("citations") or [])] + list(sub.get("citations") or []):
        kind = classify_citation(c)
        (bad_cites if kind == "invalid" else other_law if kind == "other-law" else []).append(c)
    if other_law:
        res["notes"].append(f"non-DPDP citations not scored: {other_law}")
    claims = sorted({FORBIDDEN_CLAIMS.search(s).group(0) for _, s in walk_strings(sub) if FORBIDDEN_CLAIMS.search(s)})
    res["integrity"] = {"invalid_citations": bad_cites, "compliance_claims": claims}
    integrity = 0.0 if (bad_cites or claims) else 1.0

    # Recall over must-find items; half credit when found below the minimum severity.
    must = truth.get("must_find") or []
    used = set()
    credit = 0.0
    for t in must:
        best = 0.0
        for i, f in enumerate(findings):
            if any(_hits(f, loc) for loc in t["locations"]):
                got = 1.0 if SEV[f["severity"]] >= SEV[t["severity_min"]] else 0.5
                if got > best:
                    best = got
                used.add(i)
        res["matched"][t["id"]] = best
        credit += best
    recall = credit / len(must) if must else None

    # Precision: high/critical findings on decoy locations, and mandatory findings where none are possible.
    fps = []
    for i, f in enumerate(findings):
        if i in used:
            continue
        if SEV[f["severity"]] >= SEV["high"]:
            for d in truth.get("decoys") or []:
                if _hits(f, d):
                    fps.append({"finding": f.get("title", i), "reason": d["reason"]})
                    break
    if truth.get("no_mandatory_findings"):
        for f in findings:
            if f.get("mandatory") is True:
                fps.append({"finding": f.get("title", "?"), "reason": "mandatory obligation claimed in an out-of-scope case"})
    res["false_positives"] = fps
    precision = max(0.0, 1.0 - 0.25 * len(fps))

    # Evidence validity: every cited location must exist in the fixture.
    lengths = _file_lengths(app_dir) if app_dir else {}
    valid = 0
    for f in findings:
        rng = _lines(f)
        path = next((p for p in lengths if _same_file(f["file"], p)), None)
        if path and 1 <= rng[0] <= rng[1] <= lengths[path]:
            valid += 1
        else:
            res["notes"].append(f"unsupported evidence location: {f['file']}:{rng}")
    evidence = valid / len(findings) if findings else 1.0

    # Status: deterministic unless the truth marks it as a legal judgment.
    st = truth["status"]
    got = sub["overall_status"]
    status = 1.0 if got in st["accept"] else float((st.get("partial") or {}).get(got, 0.0))
    if st.get("human_review"):
        res["human_review"] = {"status_submitted": got, "defensible": st["accept"], "notes": truth.get("human_review_notes", [])}
        status = None

    comps = {"recall": recall, "status": status, "precision": precision, "evidence": evidence}
    res["components"] = comps
    present = {k: v for k, v in comps.items() if v is not None}
    total_w = sum(WEIGHTS[k] for k in present)
    res["score"] = round(integrity * sum(WEIGHTS[k] * v for k, v in present.items()) / total_w, 4)
    return res


def score_file(case, submission_path, bench_dir=HERE):
    truth = load(os.path.join(bench_dir, "truth", f"{case}.yaml"))
    app_dir = os.path.join(bench_dir, "cases", case, "files")
    if not os.path.exists(submission_path):
        return {"case": case, "malformed": ["no dpdp-submission.yaml produced"], "score": 0.0}
    try:
        sub = load(submission_path)
    except Exception as e:  # unparseable YAML/JSON is a malformed submission, not a crash
        return {"case": case, "malformed": [f"unparseable: {type(e).__name__}"], "score": 0.0}
    return score(sub, truth, app_dir)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--case")
    ap.add_argument("--submission")
    ap.add_argument("--runs-dir", help="DIR/<case>/<arm>/<run>/dpdp-submission.yaml")
    ap.add_argument("--json", action="store_true")
    o = ap.parse_args()
    if o.runs_dir:
        rows = []
        for case in sorted(os.listdir(o.runs_dir)):
            for arm in sorted(os.listdir(os.path.join(o.runs_dir, case))):
                for run in sorted(os.listdir(os.path.join(o.runs_dir, case, arm))):
                    r = score_file(case, os.path.join(o.runs_dir, case, arm, run, "dpdp-submission.yaml"))
                    r.update(arm=arm, run=run)
                    rows.append(r)
        print(json.dumps(rows, indent=2) if o.json else "\n".join(f"{r['case']}\t{r['arm']}\t{r['run']}\t{r['score']}" for r in rows))
        return
    if not (o.case and o.submission):
        ap.error("--case and --submission are required (or --runs-dir)")
    r = score_file(o.case, o.submission)
    print(json.dumps(r, indent=2) if o.json else f"{r['case']}: {r['score']}  {r.get('malformed') or ''}")


if __name__ == "__main__":
    main()
