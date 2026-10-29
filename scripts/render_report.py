#!/usr/bin/env python3
"""Render the 12-section DPDP engineering report and traceability matrix from an assessment.

Every line comes from the assessment record, so the report cannot claim more than the record shows.
Usage: python3 render_report.py <assessment.yaml> [--out report.md] [--catalog PATH]
Run validate_assessment.py --strict first.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate_assessment import DEFAULT_CATALOG, load, lst  # noqa: E402


def cell(v):
    if isinstance(v, list):
        v = ", ".join(str(x) for x in v)
    return str("" if v is None else v).replace("|", "\\|").replace("\n", " ")


def table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    out += ["| " + " | ".join(cell(c) for c in row) + " |" for row in rows]
    return out if rows else ["_None recorded._"]


def render(a, catalog):
    cat = {q["id"]: q for q in catalog.get("requirements", [])}
    p, inv, ap = a.get("project", {}), a.get("inventory", {}), a.get("applicability", {})
    ov = ap.get("overall", {})
    findings, plans = lst(a.get("findings")), lst(a.get("plan"))
    impl, ver, lqs = lst(a.get("implementation")), lst(a.get("verification")), lst(a.get("legal_questions"))
    disc = p.get("disclaimer") or "Engineering assessment, not legal advice."
    if "certify" not in disc.lower():
        disc += " This report records what was inspected, changed and tested. It does not certify legal compliance."
    L = [f"# DPDP engineering assessment report — {p.get('name', '')}", "", f"> {disc}", "",
         f"Assessment date: {p.get('assessment_date')} · Repo ref: {p.get('repo_ref', 'n/a')} · "
         f"Assessed by: {cell(p.get('assessed_by'))}", ""]

    L += ["## 1. Application overview", "", str(p.get("purpose", "")), "",
          f"Scope of assessment: {p.get('scope_of_assessment', 'not stated')}", "", "**Components**", ""]
    L += table(["ID", "Type", "Tech", "Location"], [[c.get("id"), c.get("type"), c.get("tech"), c.get("location")] for c in lst(inv.get("components"))])
    L += ["", "**Processing activities**", ""]
    L += table(["ID", "Activity", "Purpose", "Data", "Recipients", "Location", "Facts"],
               [[x.get("id"), x.get("name"), x.get("purpose"), x.get("data_categories"), x.get("recipients"), x.get("processing_location"), x.get("fact_status")]
                for x in lst(inv.get("processing_activities"))])
    if inv.get("flow_diagram"):
        L += ["", "**Data-flow map**", "", "```mermaid", inv["flow_diagram"].rstrip(), "```"]

    L += ["", "## 2. Applicability assessment and limitations", "",
          f"**Overall: {ov.get('status')}** (confidence: {ov.get('confidence')}; legal review required: {ov.get('legal_review_required')})", "",
          str(ov.get("reasoning", "")), ""]
    L += table(["Activity", "Status", "Lawful ground", "Provisions", "Confidence", "Reasoning"],
               [[x.get("activity"), x.get("status"), x.get("lawful_ground"), x.get("provisions"), x.get("confidence"), x.get("reasoning")] for x in lst(ap.get("activities"))])
    lim = lst(a.get("assumptions")) + lst(a.get("unknowns"))
    L += ["", "**Assumptions and unknowns (limitations)**", ""]
    L += table(["ID", "Text", "Affects"], [[x.get("id"), x.get("text"), x.get("affects")] for x in lim])

    L += ["", "## 3. Legal requirements considered and supporting evidence", ""]
    L += table(["Req ID", "Title", "Provisions", "Status", "In force", "Evidence", "Required action"],
               [[r.get("req_id"), cat.get(r.get("req_id"), {}).get("title"), cat.get(r.get("req_id"), {}).get("cites"),
                 r.get("status"), f"{r.get('in_force')} (from {cat.get(r.get('req_id'), {}).get('commencement')})",
                 r.get("evidence"), r.get("required_action")] for r in lst(a.get("requirements"))])

    L += ["", "## 4. Identified gaps", "", "Mandatory = legal gap against an applicable requirement. Everything else is a security, operational or optional improvement.", ""]
    L += table(["ID", "Req", "Category", "Mandatory", "Severity", "Priority", "Title", "Status"],
               [[f.get("id"), f.get("req_id"), f.get("category"), f.get("mandatory"), f.get("severity"), f.get("priority"), f.get("title"), f.get("status")]
                for f in sorted(findings, key=lambda f: (f.get("priority", "P9"), f.get("id", "")))])

    L += ["", "## 5. Changes implemented", ""]
    pmap = {x.get("id"): x for x in plans}
    L += table(["Plan", "Findings", "Change", "Approval"],
               [[i.get("plan_id"), pmap.get(i.get("plan_id"), {}).get("findings"), pmap.get(i.get("plan_id"), {}).get("change"),
                 pmap.get(i.get("plan_id"), {}).get("approved_by") or pmap.get(i.get("plan_id"), {}).get("approval_status")] for i in impl])
    not_done = [x for x in plans if x.get("id") not in {i.get("plan_id") for i in impl}]
    L += ["", "**Planned but not implemented**", ""]
    L += table(["Plan", "Change", "Approvals required", "Approval status"],
               [[x.get("id"), x.get("change"), x.get("approvals_required"), x.get("approval_status")] for x in not_done])

    L += ["", "## 6. Files and components modified", ""]
    L += table(["Plan", "Files", "Commit"], [[i.get("plan_id"), i.get("files_changed"), i.get("commit")] for i in impl])

    L += ["", "## 7. Database migrations and infrastructure changes", ""]
    mig = [[i.get("plan_id"), i.get("migrations")] for i in impl if lst(i.get("migrations"))]
    L += table(["Plan", "Migrations"], mig)

    L += ["", "## 8. Tests executed and their actual results", ""]
    L += table(["ID", "Test", "Command", "Executed", "Result", "Independent", "Output"],
               [[v.get("id"), v.get("test_ref"), v.get("command"), v.get("executed"), v.get("result"), v.get("independent"), v.get("output_ref")] for v in ver])
    if not any(v.get("independent") for v in ver):
        L += ["", "**No independent verification has been recorded.**"]

    L += ["", "## 9. Outstanding risks and unresolved issues", ""]
    open_f = [f for f in findings if f.get("status") not in ("verified", "wont-fix", "superseded")]
    L += table(["ID", "Title", "Severity", "Status"], [[f.get("id"), f.get("title"), f.get("severity"), f.get("status")] for f in open_f])
    L += ["", "**Open legal questions**", ""]
    L += table(["ID", "Question", "Blocking", "Owner"], [[q.get("id"), q.get("question"), q.get("blocking"), q.get("owner")] for q in lqs if q.get("status") != "answered"])
    if lst(a.get("outstanding_risks")):
        L += [""] + table(["ID", "Risk"], [[x.get("id"), x.get("text")] for x in lst(a.get("outstanding_risks"))])

    L += ["", "## 10. Items requiring legal, security or management approval", ""]
    rows = [[x.get("id"), x.get("approvals_required"), x.get("approval_status"), x.get("change")] for x in plans if lst(x.get("approvals_required")) and x.get("approval_status") != "approved"]
    rows += [[x.get("item"), x.get("needs"), "pending", x.get("reason")] for x in lst(a.get("approvals_pending"))]
    L += table(["Item", "Needs", "Status", "What"], rows)

    L += ["", "## 11. Recommended next steps", ""]
    L += [f"- {s}" for s in lst(a.get("next_steps"))] or ["_None recorded._"]
    L += ["", "**Reassess when:**", ""] + ([f"- {s}" for s in lst(a.get("reassessment_triggers"))] or ["_None recorded._"])

    L += ["", "## 12. Traceability matrix (requirement → finding → plan → code → test)", ""]
    rows = []
    impl_by = {i.get("plan_id"): i for i in impl}
    for r in lst(a.get("requirements")):
        rid = r.get("req_id")
        fs = [f for f in findings if f.get("req_id") == rid]
        if not fs:
            rows.append([rid, f"{r.get('status')} / in force: {r.get('in_force')}", "—", "—", "—", "—", "—"])
        for f in fs:
            ps = [x for x in plans if f.get("id") in lst(x.get("findings"))] or [{}]
            for pl in ps:
                vs = [v for v in ver if v.get("plan_id") == pl.get("id")] if pl else []
                res = "; ".join(f"{v.get('test_ref')}={v.get('result')}{' (indep.)' if v.get('independent') else ''}" for v in vs) or "not verified"
                rows.append([rid, f"{r.get('status')} / in force: {r.get('in_force')}", f.get("id"), pl.get("id", "—"),
                             cell(impl_by.get(pl.get("id"), {}).get("files_changed")) or "not implemented", res, f.get("status")])
    L += table(["Requirement", "Status", "Finding", "Plan", "Files", "Tests (result)", "Finding status"], rows)
    L += ["", "Rows without an executed passing test are not verified. A verified row means the control was implemented and tested, not that the legal requirement is met."]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("assessment")
    ap.add_argument("--out")
    ap.add_argument("--catalog", default=DEFAULT_CATALOG)
    o = ap.parse_args()
    md = render(load(o.assessment), load(o.catalog))
    if o.out:
        with open(o.out, "w", encoding="utf-8") as fh:
            fh.write(md)
        print(f"wrote {o.out}")
    else:
        print(md)


if __name__ == "__main__":
    main()
