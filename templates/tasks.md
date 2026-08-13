<!-- docs-architect-meta {"schema_version":1,"id":"PLAN-REQ-YYYY-NNN","type":"exec-plan","title":"Implement REQ-YYYY-NNN","status":"draft","owners":[],"sources":["openspec/changes/<slug>/**"],"update_when":["Implementation progress, material discoveries, recovery steps, or verification results change"],"relations":[{"type":"implements","target":"REQ-YYYY-NNN"}],"cancellations":[],"evidence":[],"affected_docs":[],"verified_at":null,"verified_against":null} -->

# PLAN-REQ-YYYY-NNN: Implement <Change Title>

This file is the only task-state source of truth. Resume an `in_progress` task first. Otherwise,
select the highest-priority `ready` task whose dependencies are `completed`; do not rely on file
order or choose the first incomplete row.

Allowed task states: `pending`, `ready`, `in_progress`, `blocked`, `completed`, `cancelled`.
Record a reason when blocking or cancelling work. Keep task IDs stable after review begins.
For each cancelled task, add `{ "id", "reason", "authority" }` to metadata `cancellations`;
the authority must resolve under the same rules as a waiver.

## Tasks

| ID | Priority | Status | Depends on | Implements | Task |
|---|---:|---|---|---|---|
| `T-001` | 1 | ready | - | `AC-1`, `BR-<domain>-001` | TODO: smallest independently verifiable implementation step |
| `T-002` | 2 | pending | `T-001` | `AC-2`, `SC-<domain>-002` | TODO |

Tasks may combine implementation, documentation, or verification when that is the smallest useful
unit. Do not create a test task for every Scenario. Add automated coverage only when its regression
value and stability justify its maintenance cost.

## Evidence Plan

Choose one or more methods per acceptance item: `existing-test`, `automated`, `command`,
`runtime`, `inspection`, or `screenshot`. `waived` and `deferred` are result dispositions, not
methods. This table is a plan, not proof; observed results belong in `verification.md`.

| Acceptance | Method | Expected evidence |
|---|---|---|
| `AC-1` | inspection / command | TODO |

## Progress

Append only material milestones, blockers, scope changes, and recovery points. Normal task state
changes remain in the task table; per-task diary entries and per-task commits are not required.

- `<timestamp>` - Plan created.

## Discoveries And Decisions

- None recorded.

## Recovery

- Safe resume point: choose an `in_progress` task, otherwise the highest-priority dependency-ready task.
- Rollback or retry approach: TODO
- External blockers: none recorded.

## Close Readiness

- [ ] Every non-cancelled task is `completed`.
- [ ] Cancelled tasks have a scope decision or successor reference.
- [ ] Every acceptance item has an observed result in `verification.md`.
- [ ] Unresolved findings are blocking, explicitly waived, or linked to a successor.
- [ ] Documentation disposition and delta merge are ready for a close dry-run.
