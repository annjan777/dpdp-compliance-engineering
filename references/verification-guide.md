# Verification guide (Phase F)

Verification answers one question: **does the changed code do what the plan claimed, without breaking anything?** It does not answer "is the organisation compliant".

## Test matrix

Run the rows that match the changes made. Every run is recorded as a `verification` entry with the exact command and actual result.

| Area | Positive tests | Negative tests |
|---|---|---|
| Access control (SEC-02) | Owner can read and update own records. Authorised role can act. | Other user gets 403/404 (IDOR). Unauthenticated is rejected. Role escalation via request body fails. |
| Consent (CON-01, 03, 04) | Grant is recorded with notice version. Purpose runs when granted. | Default is not granted. Purpose doesn't run after withdrawal. Ledger history isn't editable through normal app paths. Core service works without optional consent. |
| Notice (NOT-01) | Consent request has a current notice version, data items, purposes and links. | Recording consent with an unknown or old notice version fails. |
| Rights (RGT-02, 03) | Summary lists the user's categories and recipients. Correction updates all copies. | User A can't get user B's summary. Erasure refused for legally retained data gives a recorded reason. |
| Erasure (RET-01, SEC-05) | Primary, child, derived, file and index data are removed. Processor delete is invoked. | No residue in caches, search or vector stores. Processing logs younger than one year survive. Logs older than the period are purged. |
| Erasure carry-over | — | Erase a user, then register a new one: the new account inherits no records, consent or log entries. Processor erasure request uses an identifier the processor holds. Non-owners can't trigger erasure. |
| Logging (SEC-03) | Personal-data access produces an audit event. | Log output contains no email, phone or health text for the flows tested. |
| Processors (FID-01) | Payload contains only registered fields. | Outbound personal data to an unregistered destination fails the test. |
| Breach (BRE-01, 02) | Incident computes the 72h deadline from `aware_at`. Templates include all r.7 items. | — |
| Children (CHD-02) | — | No tracking or ad events for child accounts. |
| Migrations | Forward and back on a copy. Row counts and constraints are as expected. | Failed migration leaves data intact. |
| Regression | The project's full existing test suite. | — |

## Recording a result

```yaml
verification:
  - id: T-007
    plan_id: P-003
    req_ids: [DPDP-RET-01, DPDP-SEC-05]
    test_ref: "tests/test_erasure.py::test_erasure_keeps_recent_processing_logs"
    command: "python -m pytest tests/test_erasure.py -q"
    executed: true
    result: pass            # pass | fail | error | not-run
    output_ref: ".dpdp/runs/2026-10-29-pytest.txt"
    executed_by: implementation-agent
    independent: false
    date: 2026-10-29
```

- `result: pass` needs `executed: true` and an `output_ref` you actually saved.
- A test that you wrote but couldn't run is `executed: false, result: not-run`, with the reason in `notes`.
- A failing test stays recorded as failing. Fix the code, then add a new run.

## Independent verifier checklist

The verifier is a different agent or a human. It starts from the assessment file and the diff, **not** from the implementer's summary.

1. Re-run the recorded commands. Results must match.
2. For each plan item marked `implemented`: open the changed files. Does the change do what `change` says? Does it cover every component listed in the finding (downstream processors, caches, indexes)?
3. Check tests assert behaviour, not just that a function exists. Watch for mocked-away logic, tests that can't fail, and skipped tests.
4. Check no security control was weakened. Diff auth middleware, CORS, CSRF and validation.
5. Check that no new personal data is collected or logged by the change itself.
6. Check citations: every `req_id` exists in the catalog. Every provision appears in `legal-sources.md`. No legal conclusion is stated as fact where a legal question is open.
7. Check statuses: nothing `verified` without an executed passing test. Nothing `not-currently-applicable` on reported evidence only.
8. Check the report language contains no compliance guarantee.
9. Record the outcome as `verification` entries with `independent: true` and file new findings for problems found.

## What "done" means

A finding is `verified` when:
- the plan item was approved where approval was required;
- the change is implemented;
- the tests covering its acceptance criteria were executed and passed;
- for material changes, an independent verification entry exists.

Even then, the report says "control implemented and tested". It never says "requirement met" or "compliant".
