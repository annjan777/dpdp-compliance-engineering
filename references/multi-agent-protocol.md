# Multi-agent protocol

Five logical roles share one record, `.dpdp/assessment.yaml`. One agent may play every role. With several agents, each owns specific sections and treats the others' output as claims until checked.

## Roles

| Role | Owns (writes) | Reads | Hands off when |
|---|---|---|---|
| 1. Discovery | `project`, `inventory`, `evidence`, `assumptions`, `unknowns` | repo, config, `.dpdp/config.yaml` | inventory validated, data-flow map present |
| 2. Legal applicability | `applicability`, `requirements`, `legal_questions` | inventory, evidence, `legal-sources.md`, catalog | every activity has a status, and every uncertain item has a legal question |
| 3. Privacy and security engineering | `findings`, `plan` | all of the above, code | every finding has severity, priority and evidence, and every plan item has tests and acceptance criteria |
| 4. Implementation | code, tests, migrations, `implementation`, `verification` (`independent: false`) | approved plan items only | changes made and own tests executed |
| 5. Independent verification | `verification` (`independent: true`), new `findings` | diff, assessment, test output | checklist in `verification-guide.md` done |

Optional subagent definitions for platforms that support them are in `assets/agents/`.

## Trust rules

1. **Evidence written by another agent has `trust: agent-claim` for you.** Before you build a legal conclusion, a severity rating, or a "verified" status on it, re-open the referenced artifact. If it holds, add your own `verified` evidence item.
2. **Only role 2 sets applicability statuses.** Other roles can raise objections as `legal_questions` or as findings with category `operational-weakness`.
3. **No role answers a legal question.** A question is closed only with an `answer_source` naming a human (role, document, date).
4. **Role 4 implements only plan items with `approval_status: approved` or `approvals_required: []`.**
5. **Role 5 can't be the same agent instance that implemented the change.** If only one agent exists, it re-runs the checklist from a clean read of the diff, sets `independent: false`, and the report flags the lack of independent review.
6. **IDs are stable.** Never renumber. Add new IDs. Mark superseded items `status: superseded` with `superseded_by`.

## Hand-off message

When passing work, send a short message containing only:

- the assessment file path and the git commit;
- the IDs you added or changed;
- open blockers (legal question IDs, approval IDs);
- what the next role should do first.

Don't restate conclusions in the message. The receiver reads the file.

## Concurrency

Agents shouldn't edit the same section at once. Work through phases in order, or split by section ownership. Run `validate_assessment.py` before handing off. A failing validation blocks the hand-off.

## Escalation targets (named roles, filled per project in config)

- `legal_reviewer`: interpretation, notices, contracts, exemptions, children, State status.
- `security_owner`: key management, auth changes, incident process.
- `data_owner` / `product_owner`: behaviour changes, retention periods, purposes.
- `release_manager`: migrations and production rollout.
