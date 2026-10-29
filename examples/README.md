# Worked examples (hypothetical applications)

Both were run through the full workflow on 2026-10-29. Each folder has the app after the changes, plus a `.dpdp/` folder with:
- `assessment.yaml`
- `report.md`
- `scan.json`
- the saved test runs in `runs/`
- `changes.diff`, the diff from the baseline
- `git-history.txt`

Git history is not shipped. So validate these with `--strict` but without `--repo`.

| Example | Built assuming | Result | What it shows |
|---|---|---|---|
| `pocket-ledger/` | "DPDP doesn't apply" | **not-currently-applicable** (s.3(c)(i)), confidence high | The developer's claim is tested against code evidence, not accepted. No consent or notice machinery is added. A non-DPDP security fix is made, labelled `mandatory: false`. A first test that was itself wrong is recorded as a failed run, not hidden. Reassessment triggers are listed. |
| `campus-clinic/` | "internal university portal = outside DPDP" | **applicable** (in force from 2027-05-13), confidence medium, 9 legal questions | The claim is rejected. Requirements are mapped across four activities. 23 findings separate mandatory from optional. Approval gates apply. 8 plan items are implemented with 23 tests, and each new test is shown failing on older code. **Three rounds of independent verification found 11 defects the implementer's own tests missed**, including erased user IDs being reused, which leaked health data and consent to new users. All of these were fixed or filed honestly, including the implementer skipping an approval gate (F-22). |

Approvals marked "hypothetical" exist only to show how the gate works. A real run records real approvers.
