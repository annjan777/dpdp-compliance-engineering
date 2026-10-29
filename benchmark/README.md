# DPDP agent benchmark (v0, pilot)

A small, deterministic benchmark for coding agents (with or without a skill) that assess a repository under India's DPDP Act, 2023 and DPDP Rules, 2025. It measures whether the agent:

- reaches the right applicability status;
- finds the known problems at the right place and severity;
- avoids false positives on safe code;
- cites only DPDP provisions that exist;
- makes no compliance guarantees.

It does not measure legal correctness beyond that. Status calls that turn on a legal judgment are reported for human review, not scored.

**Status: pilot.** There are 12 small synthetic fixtures. The results are directional, not statistically meaningful (see Limitations).

## Layout

```
benchmark/
├── PROMPT.md          # the one prompt every case and arm receives
├── cases/<id>/files/  # the fixture repository the agent sees
├── truth/<id>.yaml    # ground truth (never copied into runs)
├── score.py           # deterministic scorer
├── build_stage.sh     # builds a run-staging dir without truth/
└── tests/             # scorer tests
```

## Cases

| ID | Trap it tests | Status scored? |
|---|---|---|
| b01-hr-portal-internal | "Internal tool, so exempt" claim; medical reasons exposed and broadcast | yes |
| b02-local-ledger | Personal-use exclusion (s.3(c)(i)); don't add consent machinery | yes |
| b03-campus-clinic | IDOR, PII to analytics, PII in logs, pre-ticked consent, partial deletion | yes |
| b04-school-ads | Children tracked for targeted ads; Sch.4 exemption doesn't cover ads | **human review** (State status) |
| b05-erasure-id-reuse | Erased id reused, next sign-up inherits posts and opt-in (verified by execution) | yes |
| b06-offshore-processor | s.17(1)(d) foreign-principal exemption; SSNs in logs | **human review** (role) |
| b07-rag-chatbot | Erasure must reach chat history and vectors; PII in LLM prompts | yes |
| b08-district-aggregates | No personal data; `patient_count` keyword trap | yes |
| b09-clean-notes-api | Controls already present; false-positive test | yes |
| b10-otp-secrets | OTP in logs, hardcoded payment secret | yes |
| b11-prisma-signup | TypeScript/Prisma; pre-ticked default and needless Aadhaar in schema | yes |
| b12-local-tool-telemetry | Personal tool plus crash telemetry, so partially applicable | yes |

## Scoring rules

Each case is scored from 0 to 1.

1. **Malformed:** no file, unparseable, or schema violations → 0.
2. **Integrity gate:** any invalid DPDP citation, or any compliance-guarantee phrase, sets the case score to 0.
   - Invalid citations include `Act s.52`, `Rule 30`, and unparseable references.
   - The guarantee-phrase detector is the same one the skill's validator uses.
   - Citations to other laws (GDPR, IT Act, the Constitution) are noted but not scored.
   - The scorer checks that a provision exists, not that it says what the agent claims.
3. **Recall (weight 0.5):** for each `must_find` item, is there a finding in the same file whose lines fall within ±2 of the truth range?
   - Full credit if the finding's severity is at least `severity_min`.
   - Half credit if it is lower.
   - When a case has no must-find items, recall is left out and the other weights renormalise.
4. **Status (weight 0.2):**
   - 1 if `overall_status` is in `accept`.
   - Partial credit as listed in `partial`.
   - Otherwise 0.
   - Left out and reported when `human_review: true`.
5. **Precision (weight 0.15):** 1 − 0.25 per false positive, with a floor of 0. A false positive is either:
   - a high or critical finding on a decoy range, or
   - any `mandatory: true` finding in a case where no DPDP obligation can apply.
6. **Evidence (weight 0.15):** the share of findings whose file exists and whose lines are within the file, allowing up to 2 lines past the end (scorer v0.1; see Changelog).

Score = integrity × (weighted mean of the components present).

**What this does not capture.** Whether a finding's title correctly explains the problem: a finding on the right line with the wrong explanation still matches. Remediation quality. Whether a cited provision is the right one. Reviewers should read `human_review` output and finding titles for the cases noted in the truth files.

## Run it

Run the pilot (with the skill, and the no-skill baseline):

```bash
benchmark/build_stage.sh /tmp/bench-stage
cd /tmp/bench-stage
claude plugin eval . --eval-dir bench-cases --runs 1 -j 3 \
  --model claude-opus-5-5 --allow-tools Write Edit Bash --scaffold --trust-plugin \
  --no-publish --keep-temp --threshold 0 --output-dir OUT --json OUT/result.json
python3 benchmark/collect_runs.py OUT/result.json RUNS_DIR
python3 benchmark/score.py --runs-dir RUNS_DIR
```

Score any other agent: give it `PROMPT.md` in a copy of `cases/<id>/files/`, then run `score.py --case <id> --submission dpdp-submission.yaml`.

## Limitations

- **Small and synthetic.** 12 cases, each under 60 lines, far easier than real code. Comments that gave the answer away were made neutral in b04–b12 before their first valid run (line numbers unchanged). b01–b03 had no such comments. In the pilot, the no-skill baseline scored 1.0 on b01 and b03, so detection on these easy cases does not separate the arms.
- **Written by the skill's author.** The cases and truth were written in the same session that built the skill, which is a conflict of interest. A third party should write a held-out set before anyone treats the scores as a comparison.
- **No held-out set yet.** Everything here is public, so a skill can overfit to it.
- **Location matching is coarse.** It is line-based, with ±2 lines tolerance.

## Scorer changelog

- **0.1 (after the pilot):** the evidence check now allows ranges that end up to 2 lines past the end of the file, the same tolerance as location matching. Why: a skill-arm finding cited `core.py` lines 26–31 in a 30-line file and lost evidence credit for a trivial off-by-one. All pilot runs were re-scored with 0.1, both arms alike.
