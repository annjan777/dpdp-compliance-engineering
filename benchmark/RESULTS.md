# Results: skill vs no-skill (pilot, 2026-10-30)

Engineering measurement, not legal advice. All fixtures are synthetic. Sample sizes are small, so nothing here is statistically significant.

## Summary

| Experiment | With skill | Without skill | What it shows |
|---|---|---|---|
| A. 5 behavioural cases, LLM-graded, 3 runs per arm (30 runs) | **0.97** (15 runs) | **0.78** (15 runs) | The skill improved process behaviours: escalating legal questions, separating applies from in-force, disclaimers, reassessment triggers. |
| B. 12-case deterministic benchmark, 1 run per arm (24 runs) | **0.984** | **1.000** | No measurable benefit. Plain Claude already scores at the ceiling, so these cases are too easy to separate the arms. The skill lost points on two cases by citing lines off by 3. |

**Observed:** on this model, the skill changes *how* the agent handles legal uncertainty and reporting. It did not improve *finding* the planted problems, because the baseline already found all of them.

**Hypothesis, not shown:** the skill helps more on larger, messier codebases where discovery is hard. Benchmark v0 can't test that.

## Setup

| Item | Value |
|---|---|
| Harness | `claude plugin eval` with its with/without ablation. The baseline arm is the same harness with the plugin not loaded. |
| CLI version | 2.1.312 for the first batch, 2.1.314 for the re-runs after the rate limit (see Deviations) |
| Agent model | `claude-opus-5-5`, both arms |
| Judge model (A only) | `claude-sonnet-5-5`, 3 votes per grader |
| Tool permissions | Read, Glob, Grep, Skill, Write, Edit, Bash. Bash ran in the bubblewrap 0.9.0 sandbox. |
| Limits | 40 turns max, 1200 s timeout per run |
| Rubric frozen at | A: commit `acb0517`. B: commit `339d0a5` (scorer later v0.1, fixtures b04–b12 edited before their valid runs; see Deviations) |
| Host | Linux 6.18, Python 3.13.18, running as root |
| Cost | A: $32.96 · B: $7.96 (including runs that hit the rate limit) |

Prompts were identical across arms. A uses each case's `prompt.md`. B uses `benchmark/PROMPT.md`, and `build_stage.sh` keeps the truth files out of the run directory. **B:** no run read ground truth. `collect_runs.py` checked every tool call in the full traces for truth or grader paths and found none.

**A:** this check is incomplete. A's full traces were not kept. The grader evidence that was kept is cut off at about 20k characters, and in it no run touched `evals/`, a grader, or `case.yaml`. But the skill arm's plugin directory contains `evals/`, so a later read can't be ruled out. Future A runs should move `evals/` outside the plugin directory and use `--keep-temp`. The skill was loaded in every "with" run and in no "without" run.

## A. Behavioural cases (LLM graders)

| Case | With: runs, mean | Without: runs, mean | Δ | Graders the baseline failed |
|---|---|---|---|---|
| internal-tool-claimed-out-of-scope | 3, 1.00 | 3, 0.80 | +0.20 | "applies vs in force" distinction (3/3 runs) |
| local-only-tool-out-of-scope | 3, 1.00 | 3, 0.87 | +0.13 | Run 1 cited the wrong exclusion (s.3(c)(ii)(A) instead of s.3(c)(i)) and gave no reassessment triggers |
| minors-and-state-escalation | 3, 0.83 | 3, 0.50 | +0.33 | Missed the State/Article 12 question in 3/3 runs; gave a definitive legal ruling in 2/3; built a consent flow before legal review in 1/3. The skill arm also gave a definitive ruling in 2/3 runs. |
| portability-request-citation-discipline | 3, 1.00 | 3, 1.00 | 0.00 | none: both arms rejected the false "s.13 = portability" premise |
| truthful-report-unrun-tests | 3, 1.00 | 3, 0.75 | +0.25 | No "not legal advice" statement (3/3). Both arms refused to claim compliance or invent test passes. |

Raw data: `results/2026-10-30/ablation-summary.md` and `all-runs.json` (with per-grader judge votes).

**Caveat:** I wrote these graders in the same session that built the skill. Several of them reward conventions the skill explicitly teaches (the commencement distinction, a disclaimer, reassessment triggers). Part of the +0.18 therefore measures following the skill's own conventions, not general answer quality. The baseline was safe on the highest-stakes checks: it never invented a compliance claim, a test result, or a portability right.

## B. Deterministic benchmark

Scoring rules are in `README.md`. Per-run submissions, final messages, leak checks and score breakdowns are in `results/2026-10-30/pilot-runs/`.

| Case | With | Without | Notes |
|---|---|---|---|
| b01–b05, b07, b09–b12 | 1.000 | 1.000 | Both arms found every planted problem, with no false positives and no bad citations. |
| b06-offshore-processor | 0.953 | 1.000 | The skill arm cited lines +3 off (see below). Both arms chose `partially-applicable`; the status is left for human review. |
| b08-district-aggregates | 0.850 | 1.000 | Same +3 line error. Both arms correctly found no personal data. |
| b04-school-ads | 1.000 | 1.000 | Both chose `applicable`; status left for human review. |
| **Mean** | **0.984** | **1.000** | 12 runs per arm |

**Why the skill arm lost points:** on b06 and b08 the agent ran `cat -n README.md <file>` as a single command. That numbers both files as one sequence, so every line it cited in the second file was 3 too high. The baseline happened to read the files separately. This is a real error, but the cause is trivial. The skill now warns about it (`references/discovery-guide.md`). The change came *after* these runs; it has not been re-measured.

**Ceiling effect:** the baseline scored 1.0 on every case. Benchmark v0 can't show a detection benefit for any skill on this model. To become a useful comparison it needs larger repositories, problems spread across several files, and a held-out set written by someone other than the skill's author.

## C. Real codebase: Saleor (read-only, scoped)

- **Target:** saleor/saleor at tag `3.23.45`, commit `e5b7e5f80f8b579aa27b18a271da78d8fd835947`. Shallow clone, read only. `git status` confirmed no changes afterwards.
- **Scope:** customer data across account deletion. The scenario is an Indian merchant acting as the Data Fiduciary.
- **Who did what:** one agent with the skill produced the assessment. I then re-read the source at every cited location myself.
- **Result:** status `applicable` (medium confidence). 8 findings: 2 legal gaps, 2 security observations, 3 operational, 1 best practice. Validator `--strict`: 0 errors, 1 justified warning.
- **What held up:** the data-retention findings (personal data that remains after account deletion) are supported by the code on reading.
- **What didn't:** I re-rated one of the agent's two "security" findings as intended behaviour that needs a design discussion, not a vulnerability.
- **Not tested:** nothing was executed against a running Saleor instance, and deployment add-ons (Saleor's guidance mentions an anonymizer app) may already handle some of this.

**Details are withheld from this public file.** They are unverified by execution, and they concern a third-party project, so they go to the maintainers through Saleor's `SECURITY.md` process first, if they hold up.

## Deviations from plan (all recorded, none hidden)

1. **Harness trial (before freezing the rubric).**
   - The first trial had no sandbox, so every run errored. I installed `bubblewrap` and `socat`.
   - In the second trial, the portability case had no app to modify, and grader 03 misjudged a correct "s.11 is the closest right" answer. I added an Express fixture and reworded the grader.
   - Both changes were committed (`acb0517`) before any counted run.
2. **Account rate limit.** The 5-hour limit hit partway through A and B; 27 runs errored. Errored runs were excluded, never scored as 0.
   - After the reset, I re-ran the affected cases in full (A: all 3 runs per arm for the 2 cases; B: b04–b12). The skill and graders were byte-identical (`git diff acb0517 -- evals SKILL.md references scripts assets` was empty). The CLI auto-updated from 2.1.312 to 2.1.314 between batches.
3. **Scorer v0.1.** After the first pilot runs, the evidence check started allowing 2 lines past the end of the file, the same tolerance as location matching. All B runs are scored with v0.1, both arms alike.
4. **Fixture comments.** Comments that gave the answer away in b04–b12 were made neutral, with no line shifts. The one valid run on an old fixture (b04, skill arm, first batch) was discarded and re-run on the new fixture with the other b04–b12 runs.

## Reproduce

```bash
# A: behavioural ablation
cd dpdp-compliance-engineering
claude plugin eval . --runs 3 -j 4 --model claude-opus-5-5 --judge-model claude-sonnet-5-5 \
  --allow-tools Write Edit Bash --scaffold --trust-plugin --no-publish --threshold 0 \
  --output-dir OUT_A --json OUT_A/result.json
python3 benchmark/summarize_ablation.py OUT_A/result.json

# B: deterministic benchmark
benchmark/build_stage.sh /tmp/stage && cd /tmp/stage
claude plugin eval . --eval-dir bench-cases --runs 1 -j 3 --model claude-opus-5-5 --judge-model claude-sonnet-5-5 \
  --allow-tools Write Edit Bash --scaffold --trust-plugin --no-publish --keep-temp --threshold 0 \
  --output-dir OUT_B --json OUT_B/result.json
cd - && python3 benchmark/collect_runs.py OUT_B/result.json RUNS_B && python3 benchmark/score.py --runs-dir RUNS_B

# Unit tests (no model calls)
python3 -m pytest -q scripts/tests benchmark/tests
```

On Linux, the eval harness needs `bubblewrap` and `socat` to sandbox Bash. Model outputs vary between runs, so expect different numbers on a re-run, especially with one run per case.
