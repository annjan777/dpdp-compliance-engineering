# Applicability method (Phase B)

The question is never "does DPDP apply to this app?" in one step. It is: **for each processing activity, which obligations apply, under which conditions, from which date, and how sure are we?** Then roll up.

## The five statuses

| Status | Use when | Minimum record |
|---|---|---|
| `applicable` | All scope gates pass, no exemption applies, and the requirement's triggers hold, all on verified facts. | Verified evidence for each gate and trigger. |
| `partially-applicable` | Some activities, components or roles are covered and others are not, or an exemption removes some obligations but not others (e.g. s.17(1) leaves s.8(1) and s.8(5)). | Which parts are in and out, and why. |
| `potentially-applicable` | Coverage depends on a fact not yet confirmed or an interpretation that needs a lawyer. | At least one open `legal_questions` or `unknowns` entry that would decide it. |
| `not-currently-applicable` | A defensible basis puts the activity outside scope, supported by **verified** evidence (not just a statement) and a cited provision. | Basis provision, verified evidence, the facts that would change it (`reassessment_triggers`). |
| `undetermined` | There isn't enough information to reason at all (no repo access, no description of purpose). | What is missing and who can provide it. |

**Commencement is separate.** Every requirement also gets `in_force: yes | no | unknown`, with a `commencement` date. An obligation can be `applicable` and `in_force: no`. Report it as "applies from <date>". Don't downgrade it to not-applicable, and don't present it as currently enforceable.

**Confidence:**
- `high`: facts verified in code or config, and the provision is unambiguous.
- `medium`: facts verified but the interpretation is debatable, or the provision is clear but a key fact is reported.
- `low`: rests on assumptions or reported facts.

## Decision procedure (per processing activity)

Stop at the first gate that settles the question. Record every gate you passed.

**Gate 1 — Personal data?** (Act s.2(t))
- Is any data about an identifiable individual involved? Count indirect identifiers: user IDs linked to accounts, emails, phone numbers, IPs, device IDs, employee numbers, free text and chat logs about people, photos, voice, location, and AI prompts containing user content.
- Truly anonymous aggregates and data about legal entities only → this activity is out (record the evidence: schema, sample of fields).
- Pseudonymised or hashed but re-linkable by the organisation → treat as personal data, and raise a legal question if it matters.

**Gate 2 — Digital?** (Act s.3(a))
- Collected digitally, or collected on paper and digitised later → in. Paper never digitised → out for that activity.

**Gate 3 — Territorial nexus?** (Act s.3(a), s.3(b))
- Processing in India → in.
- Outside India and connected to offering goods or services to people in India → in.
- Outside India with no Indian offering → out, but record where users actually are. Incidental Indian users go to legal review.

**Gate 4 — Exclusions?** (Act s.3(c))
- (i) An individual's purely personal or domestic use. The *user's* own processing in a local-only tool can be outside. The *developer* is not processing at all if no data reaches them. Any telemetry, sync, crash reporting or support upload that reaches the developer creates a new activity that must be assessed separately.
- (ii) Data the Data Principal herself made public, or that someone was legally obliged to publish. Data scraped from public sources but published by someone else is not covered by this exclusion. Legal review.

**Gate 5 — Role.** (Act s.2(i), s.2(k), s.8(1)–(2))
- Who determines purpose and means? That organisation is the fiduciary for the activity.
- If the assessed organisation only processes on a client's instructions, it is a processor. Most duties sit with the fiduciary and reach the processor through the contract (s.8(1)–(2)). Record the processor's contractual duties as `partially-applicable`, and the fiduciary's duties as belonging to the client. Legal review on ambiguous roles.
- Internal tools still have a fiduciary: the employer. Employee data usually relies on s.7(i), which is a lawful ground, not an exemption.

**Gate 6 — Exemptions.** (Act s.17, Rules r.16)
- Apply an exemption only if **every** condition is evidenced. A notification-based exemption (s.17(2)(a), s.17(3), s.17(5), SDF exemptions) needs the notification itself.
- s.17(1) is **partial**: s.8(1) and s.8(5) still apply → usually `partially-applicable`.
- s.17(2)(b) research/archiving/statistics: needs (a) no decision specific to any Data Principal, and (b) Rules Sch.2 standards met. Missing either → not exempt.
- s.17(4) State: removes s.8(7), s.12(3), and s.12(2) for non-decision processing. Only for the State or its instrumentalities (Article 12). Legal review.
- Never invent an exemption. "Internal", "non-profit", "small", "academic", "government-funded", "no revenue", "only employees", "test data", "behind VPN" are not exemptions in the Act.

**Gate 7 — Lawful ground per purpose.** (Act s.4, s.7)
- Identify consent or a specific s.7 clause for each purpose. This decides which obligations attach:
  - consent → s.5 notice, s.6 consent duties, s.11–12 rights;
  - s.7(a) → s.11–12 rights apply, but no s.5 notice;
  - s.7(b)–(i) → no consent, no s.5 notice, and no s.11–12 rights.
- General duties (s.8, s.9, s.10, s.16) attach regardless of the ground.

**Gate 8 — Requirement triggers.** For each catalog requirement, check its `triggers` and `exceptions`. Examples:
- Children → only if subjects may be under 18.
- RET-02 → only if a Sch.3 class threshold is met.
- SDF-01 → only with a notification.
- CON-05 → only if a Consent Manager is used.

**Gate 9 — Commencement.** Compare the requirement's `commencement` with `project.assessment_date`.

## Roll-up to the application

| Activity results | Application status |
|---|---|
| All activities `applicable` | `applicable` |
| Mix of `applicable` and `not-currently-applicable`, or partial exemptions | `partially-applicable` |
| None `applicable`, at least one `potentially-applicable` | `potentially-applicable` |
| All `not-currently-applicable`, each with verified evidence | `not-currently-applicable` |
| Any activity `undetermined` and none `applicable` | `undetermined` |

Always list which activities drive the result.

## Handling "we assumed DPDP doesn't apply"

1. Record the claim as an evidence item with `trust: reported` and the reason given.
2. Test each reason against the gates. Typical reasons and what they actually mean:

| Claimed reason | Reality check |
|---|---|
| "It's an internal tool" | Employees are Data Principals. s.7(i) gives a ground but duties remain. |
| "We're a government or academic body" | Only s.17(4) (State, limited) or s.17(2)(b) (research with conditions). Legal review. |
| "We don't store anything sensitive" | The Act has no sensitivity threshold. |
| "Users are outside India" | s.3(b) for foreign processing; s.17(1)(d) for foreign principals under a foreign contract (partial). |
| "Data is public" | Only s.3(c)(ii), which is narrow. |
| "We're just a vendor" | Processor: contractual duties via s.8(1)–(2). Confirm the role. |
| "The Act isn't in force yet" | That is commencement, not applicability. Obligations apply from 13 May 2027. |
| "It's anonymised" | Verify re-identification risk. Pseudonymous data is usually still personal. |

3. Conclude `not-currently-applicable` only where verified evidence supports the reason.

## Outside-scope applications

When the result is `not-currently-applicable`:
- still record `security-vulnerability` findings (they matter regardless of DPDP);
- record proportionate `best-practice` findings with `mandatory: false`;
- note other possibly relevant obligations as legal questions without asserting them: contracts, sectoral regulators (RBI, IRDAI, health), IT Act provisions still in force, foreign laws for foreign users;
- add `reassessment_triggers` listing what would bring the activity into scope (adding telemetry, cloud sync, accounts, Indian users, minors).

## Legal questions

Each entry needs: the question, why it matters (which requirement or status depends on it), the provisions involved, whether it is `blocking` for implementation, a suggested owner role, and `status`. When answered, record `answer_source` (e.g. "legal counsel memo 2027-01-10"). An answer from another agent is not a legal answer.
