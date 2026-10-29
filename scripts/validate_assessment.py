#!/usr/bin/env python3
"""Validate a DPDP engineering assessment (.dpdp/assessment.yaml or .json).

Mechanically enforces: status vocabularies, ID references, citation discipline,
no-developer-claim-only scoping, legal-question handling, commencement (in_force)
consistency, mandatory vs best-practice separation, approval gating, truthful test
records, no compliance guarantees, and no personal data or secrets in the record.

Usage: python3 validate_assessment.py <assessment.yaml> [--strict] [--repo DIR] [--catalog PATH] [--json]
--repo DIR also checks that recorded commits exist in DIR's git history and that output_ref
files exist, so evidence and test results cannot be invented.
Exit code 0 = no errors (warnings allowed unless --strict).
"""
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CATALOG = os.path.join(HERE, "..", "references", "requirements-catalog.yaml")

STATUSES = {"applicable", "partially-applicable", "potentially-applicable", "not-currently-applicable", "undetermined"}
CONFIDENCE = {"high", "medium", "low"}
TRUST = {"verified", "reported", "inferred", "agent-claim"}
STRONG_EVIDENCE_TYPES = {"legal-opinion", "notification"}
CATEGORY = {"legal-gap", "security-vulnerability", "operational-weakness", "best-practice"}
SEVERITY = {"critical", "high", "medium", "low"}
PRIORITY = {"P0", "P1", "P2", "P3"}
FINDING_STATUS = {"open", "planned", "in-progress", "implemented", "verified", "accepted-risk", "wont-fix", "superseded"}
APPROVAL = {"not-required", "pending", "approved", "rejected"}
APPROVERS = {"legal", "security", "management", "data-owner"}
RESULT = {"pass", "fail", "error", "not-run"}
IN_FORCE = {"yes", "no", "unknown"}

# Citation patterns (see references/legal-sources.md)
CITE_PATTERNS = [
    (re.compile(r"^Act s\.(\d+)(\(\w+\))*$"), 1, 44),
    (re.compile(r"^Act Sch\. item (\d+)$"), 1, 7),
    (re.compile(r"^Rules r\.(\d+)(\(\w+\))*$"), 1, 23),
    (re.compile(r"^Rules Sch\.(\d+)( Part [AB])?( item \d+)?$"), 1, 7),
    (re.compile(r"^G\.S\.R\. (843|844|845|846|892)\(E\)$"), None, None),
]
FREE_TEXT_CITES = [
    (re.compile(r"\bAct s\.(\d+)"), 1, 44),
    (re.compile(r"\bRules r\.(\d+)"), 1, 23),
    (re.compile(r"\bRules Sch\.(\d+)"), 1, 7),
    (re.compile(r"\b[Ss]ection (\d+) of the (DPDP|Digital Personal Data Protection) Act"), 1, 44),
    (re.compile(r"\bRule (\d+) of the (DPDP|Digital Personal Data Protection) Rules"), 1, 23),
]
FORBIDDEN_CLAIMS = re.compile(
    r"((fully|100\s*%|completely|totally)\s+(dpdp[- ]?)?compliant"
    r"|guarantee[sd]?\s+(full\s+|legal\s+)?compliance"
    r"|compliance\s+(is\s+)?guaranteed"
    r"|dpdp[- ]certified"
    r"|certif(y|ies|ied)\s+(that\s+)?(the\s+)?(app|application|system|product|service)\s+(is\s+)?compliant"
    r"|\b(app|application|system|product|service|portal)\s+is\s+(now\s+)?compliant\s+with\s+(the\s+)?(dpdp|act|rules))",
    re.I)
SAFE_EMAIL_DOMAINS = ("example.com", "example.org", "example.net", ".invalid", ".example", ".test", "example.in")
PII_PATTERNS = [
    ("email address", re.compile(r"\b[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b")),
    ("Indian mobile number", re.compile(r"(?<!\d)(\+?91[ -]?)?[6-9]\d{9}(?!\d)")),
    ("Aadhaar-like number", re.compile(r"(?<!\d)[2-9]\d{3}[ -]?\d{4}[ -]?\d{4}(?!\d)")),
    ("PAN-like number", re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")),
    ("API key / secret", re.compile(r"(sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,}|xox[bp]-[A-Za-z0-9-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)")),
]
AGENT_SOURCE = re.compile(r"\b(agent|claude|gpt|llm|assistant|copilot|ai model)\b", re.I)


def load(path):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    if path.endswith(".json"):
        return json.loads(text)
    try:
        import yaml
    except ImportError:
        sys.exit("PyYAML is required for YAML files: pip install pyyaml (or pass a .json assessment)")
    return yaml.safe_load(text)


def as_date(v):
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    try:
        return dt.date.fromisoformat(str(v))
    except ValueError:
        return None


def walk_strings(node, path="$"):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from walk_strings(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk_strings(v, f"{path}[{i}]")
    elif isinstance(node, str):
        yield path, node


def lst(x):
    return x if isinstance(x, list) else ([] if x is None else [x])


class Report:
    def __init__(self):
        self.errors, self.warnings = [], []

    def err(self, where, msg):
        self.errors.append(f"{where}: {msg}")

    def warn(self, where, msg):
        self.warnings.append(f"{where}: {msg}")


def check_citation(c):
    for rx, lo, hi in CITE_PATTERNS:
        m = rx.match(c.strip())
        if m:
            if lo is None:
                return True
            n = int(m.group(1))
            return lo <= n <= hi
    return False


def validate(a, catalog, strict=False):
    r = Report()
    if not isinstance(a, dict):
        r.err("$", "assessment must be a mapping")
        return r
    cat = {q["id"]: q for q in catalog.get("requirements", [])}

    proj = a.get("project") or {}
    adate = as_date(proj.get("assessment_date"))
    if not adate:
        r.err("project.assessment_date", "missing or not an ISO date")
    for k in ("id", "name", "purpose"):
        if not proj.get(k):
            r.err(f"project.{k}", "required")

    # ---- ID registry ----
    ids = {}

    def reg(kind, items, key="id"):
        for i, it in enumerate(lst(items)):
            if not isinstance(it, dict):
                r.err(f"{kind}[{i}]", "must be a mapping")
                continue
            iid = it.get(key)
            if not iid:
                r.err(f"{kind}[{i}]", f"missing {key}")
                continue
            if iid in ids:
                r.err(f"{kind}[{i}]", f"duplicate id {iid}")
            ids[iid] = (kind, it)

    inv = a.get("inventory") or {}
    reg("evidence", a.get("evidence"))
    for sec in ("components", "data_subjects", "data_categories", "processing_activities", "flows", "vendors"):
        reg(f"inventory.{sec}", inv.get(sec))
    reg("assumptions", a.get("assumptions"))
    reg("unknowns", a.get("unknowns"))
    reg("legal_questions", a.get("legal_questions"))
    reg("findings", a.get("findings"))
    reg("plan", a.get("plan"))
    reg("verification", a.get("verification"))

    evidence = {e["id"]: e for e in lst(a.get("evidence")) if isinstance(e, dict) and e.get("id")}
    activities = {p["id"] for p in lst(inv.get("processing_activities")) if isinstance(p, dict)}
    lqs = {q["id"]: q for q in lst(a.get("legal_questions")) if isinstance(q, dict) and q.get("id")}
    unknowns = lst(a.get("unknowns"))

    def refs_exist(where, refs, kinds=None):
        for ref in lst(refs):
            if ref not in ids:
                r.err(where, f"reference {ref} not defined")
            elif kinds and ids[ref][0] not in kinds:
                r.err(where, f"reference {ref} is a {ids[ref][0]}, expected {kinds}")

    for eid, e in evidence.items():
        if e.get("trust") not in TRUST:
            r.err(f"evidence {eid}", f"trust must be one of {sorted(TRUST)}")
        if not e.get("ref"):
            r.err(f"evidence {eid}", "ref (where to re-check it) is required")

    def strong(ev_ids):
        """At least one evidence item that is verified or an authoritative document."""
        for x in lst(ev_ids):
            e = evidence.get(x)
            if e and (e.get("trust") == "verified" or e.get("type") in STRONG_EVIDENCE_TYPES):
                return True
        return False

    def cites_ok(where, cites):
        for c in lst(cites):
            if not isinstance(c, str) or not check_citation(c):
                r.err(where, f"citation '{c}' is not in the registry format/range (see references/legal-sources.md)")

    def has_open_question_or_unknown(target_id, listed_qs):
        if any(q in lqs for q in lst(listed_qs)):
            return True
        for q in lqs.values():
            if target_id in lst(q.get("related")):
                return True
        for u in unknowns:
            if isinstance(u, dict) and target_id in lst(u.get("affects")):
                return True
        return False

    # ---- Applicability ----
    ap = a.get("applicability") or {}
    ov = ap.get("overall") or {}
    if ov.get("status") not in STATUSES:
        r.err("applicability.overall.status", f"must be one of {sorted(STATUSES)}")
    if ov.get("confidence") not in CONFIDENCE:
        r.err("applicability.overall.confidence", f"must be one of {sorted(CONFIDENCE)}")
    cites_ok("applicability.overall.provisions", ov.get("provisions"))
    act_statuses = {}
    for i, act in enumerate(lst(ap.get("activities"))):
        w = f"applicability.activities[{i}]"
        aid = act.get("activity")
        if aid not in activities:
            r.err(w, f"activity {aid} not in inventory.processing_activities")
        st = act.get("status")
        act_statuses[aid] = st
        if st not in STATUSES:
            r.err(w, f"status must be one of {sorted(STATUSES)}")
        if act.get("confidence") not in CONFIDENCE:
            r.err(w, "confidence required (high|medium|low)")
        cites_ok(w + ".provisions", act.get("provisions"))
        refs_exist(w + ".facts", act.get("facts"), {"evidence"})
        refs_exist(w + ".legal_questions", act.get("legal_questions"), {"legal_questions"})
        if not act.get("reasoning"):
            r.err(w, "reasoning required")
        if st == "not-currently-applicable":
            if not act.get("provisions"):
                r.err(w, "not-currently-applicable needs the provision that places it out of scope")
            if not strong(act.get("facts")):
                r.err(w, "not-currently-applicable needs verified evidence; reported claims (e.g. a developer saying DPDP does not apply) are not enough")
        if st in ("potentially-applicable", "undetermined") and not has_open_question_or_unknown(aid, act.get("legal_questions")):
            r.err(w, f"{st} must name the legal question or unknown that would decide it")
    if activities and not lst(ap.get("activities")):
        r.err("applicability.activities", "every processing activity needs an applicability entry")
    missing = activities - set(act_statuses)
    if missing and lst(ap.get("activities")):
        r.err("applicability.activities", f"no entry for activities {sorted(missing)}")

    ost = ov.get("status")
    vals = set(act_statuses.values())
    if ost == "not-currently-applicable":
        if vals - {"not-currently-applicable"}:
            r.err("applicability.overall", f"cannot be not-currently-applicable while activities are {sorted(vals)}")
        if not ov.get("provisions"):
            r.err("applicability.overall", "not-currently-applicable needs a basis provision")
    if ost == "applicable" and vals and vals != {"applicable"}:
        r.warn("applicability.overall", f"overall 'applicable' but activities are {sorted(vals)}; consider partially-applicable")
    if ost in ("potentially-applicable", "undetermined") and not lqs and not unknowns:
        r.err("applicability.overall", f"{ost} requires open legal_questions or unknowns")
    if ov.get("legal_review_required") is False and any(q.get("status") == "open" and q.get("blocking") for q in lqs.values()):
        r.err("applicability.overall.legal_review_required", "false while blocking legal questions are open")

    # ---- Requirements ----
    req_status = {}
    for i, rq in enumerate(lst(a.get("requirements"))):
        w = f"requirements[{i}]"
        rid = rq.get("req_id")
        if rid not in cat:
            r.err(w, f"req_id {rid} not in requirements-catalog.yaml (do not invent requirement IDs)")
            continue
        st = rq.get("status")
        req_status[rid] = st
        if st not in STATUSES:
            r.err(w, f"status must be one of {sorted(STATUSES)}")
        refs_exist(w + ".activities", rq.get("activities"), {"inventory.processing_activities"})
        refs_exist(w + ".evidence", rq.get("evidence"), {"evidence"})
        comm = as_date(cat[rid].get("commencement"))
        if rq.get("in_force") not in IN_FORCE:
            r.err(w, "in_force must be yes|no|unknown")
        elif comm and adate:
            expected = "yes" if adate >= comm else "no"
            if rq.get("in_force") != expected:
                r.err(w, f"in_force is '{rq.get('in_force')}' but catalog commencement {comm} vs assessment date {adate} gives '{expected}'")
        if st == "not-currently-applicable" and not rq.get("rationale"):
            r.err(w, "not-currently-applicable needs a rationale (trigger not met / exception with evidence)")
        if st == "not-currently-applicable" and rq.get("evidence") and not strong(rq.get("evidence")):
            r.err(w, "not-currently-applicable rests only on reported/inferred evidence")
        if st in ("potentially-applicable", "undetermined") and not rq.get("legal_review") and not has_open_question_or_unknown(rid, []):
            r.err(w, f"{st} must set legal_review or link an unknown/legal question (related: [{rid}])")
        if rq.get("legal_review") and not any(rid in lst(q.get("related")) or rid in str(q.get("why", "")) for q in lqs.values()):
            r.err(w, f"legal_review is true but no legal question lists {rid} in related/why")

    # ---- Legal questions ----
    for qid, q in lqs.items():
        w = f"legal_questions {qid}"
        cites_ok(w + ".provisions", q.get("provisions"))
        if q.get("status") not in ("open", "answered"):
            r.err(w, "status must be open|answered")
        if q.get("status") == "answered":
            src = str(q.get("answer_source") or "")
            if not src:
                r.err(w, "answered questions need answer_source (a human legal source)")
            elif AGENT_SOURCE.search(src):
                r.err(w, f"answer_source '{src}' looks like an AI agent; only a qualified human can close a legal question")

    # ---- Findings ----
    findings = {f["id"]: f for f in lst(a.get("findings")) if isinstance(f, dict) and f.get("id")}
    for fid, f in findings.items():
        w = f"findings {fid}"
        for key, vocab in (("category", CATEGORY), ("severity", SEVERITY), ("priority", PRIORITY), ("status", FINDING_STATUS)):
            if f.get(key) not in vocab:
                r.err(w, f"{key} must be one of {sorted(vocab)}")
        if not isinstance(f.get("mandatory"), bool):
            r.err(w, "mandatory must be true/false")
        refs_exist(w + ".evidence", f.get("evidence"), {"evidence"})
        if not lst(f.get("evidence")):
            r.err(w, "evidence required")
        rid = f.get("req_id")
        if rid and rid not in cat:
            r.err(w, f"req_id {rid} not in catalog")
        if f.get("category") == "legal-gap":
            if not rid:
                r.err(w, "legal-gap must reference a catalog req_id")
            elif req_status.get(rid) not in ("applicable", "partially-applicable"):
                r.err(w, f"legal-gap against {rid} whose status is '{req_status.get(rid)}'; use best-practice or resolve applicability first")
            if f.get("mandatory") is not True:
                r.err(w, "legal-gap on an applicable requirement must be mandatory: true")
        elif f.get("mandatory") is True:
            r.err(w, "only legal-gap findings can be mandatory (keep optional improvements separate)")

    # ---- Plan / implementation / verification ----
    plans = {p["id"]: p for p in lst(a.get("plan")) if isinstance(p, dict) and p.get("id")}
    for pid, p in plans.items():
        w = f"plan {pid}"
        refs_exist(w + ".findings", p.get("findings"), {"findings"})
        for ap_ in lst(p.get("approvals_required")):
            if ap_ not in APPROVERS:
                r.err(w, f"approvals_required entry '{ap_}' not in {sorted(APPROVERS)}")
        if p.get("approval_status") not in APPROVAL:
            r.err(w, f"approval_status must be one of {sorted(APPROVAL)}")
        if lst(p.get("approvals_required")) and p.get("approval_status") == "not-required":
            r.err(w, "approvals_required is non-empty but approval_status is not-required")
        if p.get("approval_status") == "approved" and not p.get("approved_by"):
            r.err(w, "approved items need approved_by (role + date)")
        if not lst(p.get("tests")) or not lst(p.get("acceptance_criteria")):
            r.err(w, "tests and acceptance_criteria are required")

    implemented_plans = set()
    for i, im in enumerate(lst(a.get("implementation"))):
        w = f"implementation[{i}]"
        pid = im.get("plan_id")
        if pid not in plans:
            r.err(w, f"plan_id {pid} not defined")
            continue
        p = plans[pid]
        if lst(p.get("approvals_required")) and p.get("approval_status") != "approved":
            r.err(w, f"{pid} was implemented without recorded approval ({p.get('approvals_required')})")
        if not lst(im.get("files_changed")):
            r.err(w, "files_changed required")
        implemented_plans.add(pid)

    passed_plans, independent_plans = set(), set()
    for v in lst(a.get("verification")):
        if not isinstance(v, dict):
            continue
        w = f"verification {v.get('id')}"
        if v.get("result") not in RESULT:
            r.err(w, f"result must be one of {sorted(RESULT)}")
        if v.get("result") in ("pass", "fail", "error") and v.get("executed") is not True:
            r.err(w, f"result '{v.get('result')}' claimed without executed: true")
        if v.get("executed") is not True and v.get("result") != "not-run":
            r.err(w, "tests not executed must have result: not-run")
        if v.get("result") == "pass" and not v.get("output_ref"):
            r.err(w, "a pass needs output_ref pointing to the saved run output")
        if v.get("executed") and not v.get("command"):
            r.err(w, "executed tests need the exact command")
        if v.get("plan_id") and v.get("plan_id") not in plans:
            r.err(w, f"plan_id {v.get('plan_id')} not defined")
        for rid in lst(v.get("req_ids")):
            if rid not in cat:
                r.err(w, f"req_id {rid} not in catalog")
        if v.get("result") == "pass" and v.get("executed") is True and v.get("plan_id"):
            passed_plans.add(v["plan_id"])
            if v.get("independent") is True:
                independent_plans.add(v["plan_id"])

    for fid, f in findings.items():
        covering = {pid for pid, p in plans.items() if fid in lst(p.get("findings"))}
        if f.get("status") in ("implemented", "verified") and not covering & implemented_plans:
            r.err(f"findings {fid}", f"status {f.get('status')} but no implementation entry for its plan items")
        if f.get("status") == "verified":
            if not covering & passed_plans:
                r.err(f"findings {fid}", "status verified but no executed passing test is recorded for its plan items")
            elif f.get("severity") in ("critical", "high") and not covering & independent_plans:
                (r.err if strict else r.warn)(f"findings {fid}", "material finding verified without an independent verification entry")
        if f.get("status") in ("open", "planned") and f.get("severity") == "critical" and not covering:
            r.warn(f"findings {fid}", "critical finding has no plan item")

    # ---- Free-text checks: citations, claims, personal data / secrets ----
    for where, s in walk_strings(a):
        for rx, lo, hi in FREE_TEXT_CITES:
            for m in rx.finditer(s):
                n = int(m.group(1))
                if not lo <= n <= hi:
                    r.err(where, f"citation '{m.group(0)}' is outside the range of the source (fabricated?)")
        if FORBIDDEN_CLAIMS.search(s):
            r.err(where, f"compliance guarantee language: '{FORBIDDEN_CLAIMS.search(s).group(0)}'")
        for label, rx in PII_PATTERNS:
            for m in rx.finditer(s):
                if label == "email address" and m.group(1).lower().endswith(SAFE_EMAIL_DOMAINS):
                    continue
                if label == "Indian mobile number" and re.search(r"\d{4}-\d{2}-\d{2}", s[max(0, m.start()-3):m.end()+3]):
                    continue
                r.err(where, f"looks like a real {label}; never put personal data or secrets in the assessment")
                break

    # ---- Completeness / strict ----
    if not lst(a.get("reassessment_triggers")):
        (r.err if strict else r.warn)("reassessment_triggers", "list what would change the conclusions")
    if not (proj.get("disclaimer")):
        (r.err if strict else r.warn)("project.disclaimer", "state that this is an engineering assessment, not legal advice")
    for fid, f in findings.items():
        if f.get("category") == "legal-gap" and f.get("status") == "open" and not any(fid in lst(p.get("findings")) for p in plans.values()):
            r.warn(f"findings {fid}", "mandatory gap has no plan item")
    return r


def check_repo(a, repo, r):
    """Recorded commits and saved outputs must exist."""
    for i, im in enumerate(lst(a.get("implementation"))):
        for sha in re.findall(r"\b[0-9a-f]{7,40}\b", str(im.get("commit") or "")):
            ok = subprocess.run(["git", "-C", repo, "cat-file", "-e", sha + "^{commit}"],
                                capture_output=True).returncode == 0
            if not ok:
                r.err(f"implementation[{i}]", f"commit {sha} not found in {repo}")
    for v in lst(a.get("verification")):
        ref = v.get("output_ref") if isinstance(v, dict) else None
        if ref and not os.path.exists(os.path.join(repo, ref)):
            r.err(f"verification {v.get('id')}", f"output_ref {ref} does not exist in {repo}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("assessment")
    ap.add_argument("--catalog", default=DEFAULT_CATALOG)
    ap.add_argument("--strict", action="store_true", help="treat completeness warnings as errors (use before reporting)")
    ap.add_argument("--repo", help="target repository root: verify commits and output files exist")
    ap.add_argument("--json", action="store_true")
    o = ap.parse_args()
    a = load(o.assessment)
    rep = validate(a, load(o.catalog), o.strict)
    if o.repo:
        check_repo(a, o.repo, rep)
    if o.json:
        print(json.dumps({"errors": rep.errors, "warnings": rep.warnings}, indent=2))
    else:
        for e in rep.errors:
            print("ERROR  ", e)
        for w in rep.warnings:
            print("WARNING", w)
        print(f"\n{len(rep.errors)} error(s), {len(rep.warnings)} warning(s)")
    sys.exit(1 if rep.errors else 0)


if __name__ == "__main__":
    main()
