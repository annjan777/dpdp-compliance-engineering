---
name: dpdp-compliance-engineering
description: Assess, implement and verify India DPDP Act 2023 / DPDP Rules 2025 privacy controls in a real codebase - web apps, APIs, portals, ERPs, auth services, data pipelines, AI chatbots. Use whenever someone asks whether DPDP applies to an app, wants a DPDP or Indian data-protection gap assessment, needs consent, notice, data-principal rights, erasure/retention, breach-notification, children's-data or processor controls built, or wants a privacy compliance report or traceability matrix for an Indian-facing system - even if they only say "privacy compliance", "personal data audit" or "is this app covered". Works stack-agnostically, starts by testing applicability instead of assuming it, separates mandatory obligations from best practice, and never certifies compliance.
license: Proprietary. Engineering aid, not legal advice.
---

# DPDP Compliance Engineering

Turn India's Digital Personal Data Protection Act, 2023 (the Act) and the DPDP Rules, 2025 (the Rules) into evidence-backed engineering work on a specific application.

This skill is an engineering aid. It produces facts, mapped requirements, code changes and verified test results. It does **not** produce legal conclusions that a qualified lawyer has not reviewed, and it never states that an application "is compliant".

## How this skill is organised

| Path | Read when |
|---|---|
| `references/legal-sources.md` | Before citing anything. The citation registry, commencement dates, and what the law does **not** say. |
| `references/requirements-catalog.yaml` | Phase B–C. Machine-readable requirement IDs, triggers, exceptions, evidence, tests. |
| `references/applicability-method.md` | Phase B. The decision procedure and the five status values. |
| `references/discovery-guide.md` | Phase A. What to look for, per stack and for AI systems. |
| `references/engineering-patterns.md` | Phase D–E. Control patterns and anti-patterns. |
| `references/verification-guide.md` | Phase F. Test matrix and the verifier checklist. |
| `references/multi-agent-protocol.md` | When more than one agent works on the assessment. |
| `assets/templates/` | The shared assessment file and the human-readable templates. |
| `assets/agents/` | Optional subagent definitions for platforms that support them. |
| `scripts/scan_personal_data.py` | Phase A. Heuristic signals (leads, not facts). |
| `scripts/validate_assessment.py` | After every phase. Enforces the rules below mechanically. |
| `scripts/render_report.py` | Phase G. Report and traceability matrix from the assessment file. |
| `examples/` | Two worked examples: one out of scope, one in scope with implemented and tested changes. |

Script paths are relative to this skill's directory. Find it with the path you loaded this file from.

## Project files (kept in the target repository, not in this skill)

All project-specific state lives in the target repo under `.dpdp/`:

- `.dpdp/config.yaml` — identity, stack, deployment, organisational role, approved policy choices. Copy from `assets/templates/project-config.example.yaml`. Never hardcode these in the skill.
- `.dpdp/assessment.yaml` — the single shared, structured record every phase and every agent reads and writes. Copy from `assets/templates/assessment.template.yaml`.
- `.dpdp/scan.json`, `.dpdp/report.md`, `.dpdp/runs/` — generated. `scan.json` quotes matched code lines; review it before committing in a repo that might contain real data.

If `.dpdp/assessment.yaml` already exists, this is a **reassessment**: read it first, keep existing IDs, and re-verify anything whose evidence may be stale (changed files, new vendors, new purposes, legal updates).

## Workflow

Run the phases in order. A single agent can run all of them. With several agents, follow `references/multi-agent-protocol.md`. After each phase, run:

```bash
python3 <skill>/scripts/validate_assessment.py .dpdp/assessment.yaml
```

Fix every error before moving on. Warnings need a written justification or a fix.

### Phase A — Discover

Establish facts before forming opinions.

1. Run `python3 <skill>/scripts/scan_personal_data.py <repo> --out .dpdp/scan.json`. Treat every hit as a lead to confirm, never as a finding.
2. Read the code, schema, configuration, infrastructure files and tests. Follow `references/discovery-guide.md`.
3. Fill `inventory` in the assessment: components, data subjects, data categories, processing activities (with purposes), flows, vendors.
4. Record each fact as an `evidence` item with a concrete reference (`path:line`, migration name, config key, test name). Mark every item's `trust`: `verified` (you saw it in an artifact), `reported` (a person said so), `inferred` (your deduction), or `agent-claim` (another agent said so and you have not re-checked).
5. Put what you could not confirm under `assumptions` or `unknowns`. Absence of code you didn't find is an unknown, not a fact.

Output: inventory plus a data-flow map (Mermaid in `assessment.yaml` → `inventory.flow_diagram`, or a separate file).

### Phase B — Assess applicability

Follow `references/applicability-method.md` exactly. In short:

- Assess **per processing activity**, then roll up to the application.
- Walk the tests in order: personal data? digital? territorial nexus? statutory exclusion? who decides purpose and means? exemption with **all** its conditions met? in force on the assessment date? requirement-specific trigger met?
- Use one of five statuses: `applicable`, `partially-applicable`, `potentially-applicable`, `not-currently-applicable`, `undetermined`.
- Record facts, assumptions, provisions (from `legal-sources.md` only), reasoning, confidence, and legal questions.
- A developer's or organisation's statement that "DPDP doesn't apply" is `reported` evidence. On its own it can never support `not-currently-applicable`.
- Separate **applicability** from **commencement**: an obligation can apply to the processing but not be in force yet. Record both (`status` and `in_force`).

Then map each relevant catalog requirement to the activities it touches (`requirements` list). Mark `legal_review: true` and add a `legal_questions` entry wherever the facts or the law don't settle it.

### Phase C — Gap assessment

Compare each applicable or potentially applicable requirement with what the code actually does. Each finding gets:

- `category`: `legal-gap` (a mandatory obligation not met), `security-vulnerability`, `operational-weakness`, or `best-practice`.
- `mandatory`: true only for legal gaps against requirements whose status is `applicable` or `partially-applicable`.
- `severity` (critical/high/medium/low), `priority` (P0–P3), `technical_impact`, `evidence`, `applicability_status`.

Use the penalty Schedule of the Act (see `legal-sources.md`) and real exploitability to set severity. A security hole that exposes personal data is usually critical even when no DPDP obligation is in force yet.

When the Act does not apply, still record security weaknesses and proportionate privacy improvements, but as `security-vulnerability` / `best-practice` with `mandatory: false`.

### Phase D — Plan

One plan item per change, linked to findings. Each item states:

- files and components;
- the change;
- dependencies and migrations;
- risks;
- tests;
- acceptance criteria;
- `approvals_required` (`legal`, `security`, `management`, `data-owner`).

Order: critical security and in-force mandatory obligations first, then scheduled obligations, then best practice.

Stop and get approval (record it in `approval_status` / `approved_by`) before anything that:

- changes business logic or user-visible behaviour;
- touches production data, permissions or infrastructure;
- runs destructive migrations;
- depends on an unresolved legal question.

If no human is available, implement only the items with `approvals_required: []`, and leave the rest planned.

### Phase E — Implement

- Use the project's existing architecture, conventions, libraries and patterns. Extend an existing control before adding a new one. Don't build a second consent or audit system next to an existing one.
- Make the smallest change that satisfies the requirement. See `references/engineering-patterns.md` for patterns and for what not to build.
- Determine the lawful ground per purpose first. Add consent only where consent is the chosen ground. A legitimate use (s.7) needs no consent, and a consent banner is never a substitute for that analysis.
- Don't collect new personal data to support compliance reporting. Logs and audit trails should reference identifiers, not copy personal data.
- Migrations: reversible, tested on a copy, never run against production by this skill.
- Every change ships with tests (Phase F). Record `implementation` entries with files and commits.

### Phase F — Verify

- Run the tests. Record the exact command, the actual result, and where the output is (`verification` entries). A test counts as passed only if you executed it and saw it pass.
- Include negative tests (unauthorised access, bypassing withdrawal, erasure leaving residue) and the project's existing test suite as a regression check.
- Check that erasure and withdrawal reach downstream systems: processors, caches, search indexes, vector stores, analytics, backups (document backup expiry rather than editing backups), and legally required retention (Rules r.8(3)).
- Material changes get an **independent** review by a different agent or a human using the verifier checklist in `references/verification-guide.md` (`independent: true`).
- Passing tests show the code does what the tests check. They do not show legal compliance.

### Phase G — Report and maintain

```bash
python3 <skill>/scripts/validate_assessment.py .dpdp/assessment.yaml --strict --repo .
python3 <skill>/scripts/render_report.py .dpdp/assessment.yaml --out .dpdp/report.md
```

The report (template: `assets/templates/final-report.md`) has 12 sections, including limitations, unresolved questions, approvals pending, and the requirement → code → test traceability matrix.

Add `reassessment_triggers` to the assessment: new purpose, new data category, new vendor or region, new user group (especially children), Board/government notifications (SDF designation, transfer restrictions, s.17 exemptions), and the commencement dates still ahead.

## Non-negotiable rules

1. Technical implementation is never described as guaranteed legal compliance. Don't write "compliant", "fully compliant", "DPDP certified" or similar about the application.
2. Never conclude the Act is inapplicable only because a developer or organisation says so.
3. Never mark an obligation applicable without checking its actual conditions and exceptions, including commencement.
4. Never fabricate provisions, interpretations, evidence or test results. Cite only provisions listed in `references/legal-sources.md`. If the materials don't answer a question, record a legal question.
5. Never silently change business logic, production data, access permissions or infrastructure.
6. Never run destructive database operations or production migrations without recorded authorisation and a rollback path.
7. Never put secrets, credentials, personal data or production records in reports, evidence or test fixtures. Use synthetic data.
8. Never disable or weaken a security control to make a test pass.
9. Never duplicate an existing privacy mechanism. Extend it.
10. A privacy policy or consent banner is not evidence that the underlying controls work. Only code and executed tests are.
11. Never report unverified work as complete. A finding's status is `implemented` or `verified` only when the record supports it.
12. Escalate material legal ambiguity, high-risk architecture decisions and consequential production changes to a named human role.
13. Preserve existing functionality and security boundaries.
14. Make the smallest effective change consistent with the assessed requirements and approved design.
15. Keep mandatory obligations (`mandatory: true`) separate from optional improvements (`mandatory: false`).

`validate_assessment.py` checks rules 1, 2, 4 (citation format and catalog IDs), 7 (common PII and secret patterns), 11 and 15 mechanically. With `--repo`, it also confirms that recorded commits and test-output files exist. The other rules depend on your judgement.

## When to ask the user

Ask one targeted question only when an essential decision can't be inferred safely and a wrong guess is costly. Examples: the organisation's role (fiduciary vs processor), whether users can be under 18, whether the organisation is "State" under Article 12, or approval to change behaviour. If no one can answer, record the item in `legal_questions` or `unknowns`, choose the conservative path (treat as `potentially-applicable`, don't implement the risky change), and continue.

## Final message to the user

Keep it short:

- overall applicability status and confidence;
- the top gaps;
- what was changed;
- which tests ran and their real results;
- what still needs legal, security or management sign-off;
- where the report is.

Always state that this is an engineering assessment, not legal advice.
