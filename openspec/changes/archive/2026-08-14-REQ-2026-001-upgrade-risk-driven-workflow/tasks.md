<!-- docs-architect-meta {"schema_version":1,"id":"PLAN-REQ-2026-001","type":"exec-plan","title":"Implement the risk-driven dev-spec-flow upgrade","status":"completed","owners":[],"sources":["openspec/changes/archive/2026-08-14-REQ-2026-001-upgrade-risk-driven-workflow/**"],"update_when":["Implementation progress, material discoveries, recovery, or verification results change"],"relations":[{"type":"implements","target":"REQ-2026-001"}],"acceptance":[],"evidence":[],"affected_docs":["README.md","SKILL.md","references/**"],"verified_at":"2026-08-14T00:25:00+08:00","verified_against":"2ad28f81781d949517bb275f753dcad6d4e80aac"} -->

# PLAN-REQ-2026-001: Implement the risk-driven dev-spec-flow upgrade

Task status is the execution source of truth. Resume an `in_progress` task first; otherwise select the highest-priority task whose dependencies are completed.

| ID | Priority | Status | Depends on | Implements | Task |
|---|---:|---|---|---|---|
| `T-001` | 1 | completed | - | AC-1, AC-2, AC-3 | Rewrite canonical Skill and repository adapter |
| `T-002` | 1 | completed | T-001 | AC-1, AC-2, AC-3, AC-4, AC-6, BR-workflow-001, BR-workflow-002, BR-workflow-003, BR-workflow-004, BR-workflow-006, BR-workflow-008 | Rewrite detailed workflow references |
| `T-003` | 1 | completed | T-001 | AC-2, AC-3, AC-4, AC-5, BR-workflow-003, BR-workflow-004, BR-workflow-005, BR-workflow-008 | Replace artifact templates |
| `T-004` | 1 | completed | T-001 | AC-4, AC-5, AC-7, AC-8, BR-workflow-005, BR-workflow-007, BR-workflow-008 | Implement lifecycle CLI and tests |
| `T-005` | 2 | completed | T-001 | AC-7, BR-workflow-007 | Add thin platform adapters and package metadata |
| `T-006` | 2 | completed | T-001 | AC-6, AC-7, BR-workflow-006, BR-workflow-007 | Rewrite README and docs-architect integration guidance |
| `T-007` | 1 | completed | T-002, T-003, T-004, T-005, T-006 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8 | Run tests, package validators, docs-architect checks, and forward tests |
| `T-008` | 1 | completed | T-007 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8 | Run risk-driven independent review and resolve findings |
| `T-009` | 1 | completed | T-008 | AC-9 | Commit the implementation, push `develop`, and verify the remote ref |

## Evidence plan

| Acceptance | Methods | Expected evidence |
|---|---|---|
| AC-1..AC-3 | inspection, command | policy search assertions and independent review |
| AC-4 | automated, command | lifecycle/status unit tests |
| AC-5 | automated, command | dry-run, merge, rollback, retention, idempotence tests |
| AC-6 | inspection, command | integration contract and docs-architect structural check fixture |
| AC-7 | automated, command | install/update/local-modification tests and doctor output |
| AC-8 | command | captured unittest and validate results |
| AC-9 | commit | remote `refs/heads/develop` equals local HEAD |

## Progress

- 2026-08-13T18:54:57+08:00 - Completed repository and external-practice audit; created `develop` from current `main`.
- 2026-08-13T19:10:00+08:00 - Rewrote canonical entry, README baseline, and removed tracked local Claude settings.
- 2026-08-13T20:27:26+08:00 - Completed canonical policy, references, templates, CLI, tests, adapters, and integration guidance; entered final validation and independent review.
- 2026-08-13T23:42:00+08:00 - Resolved independent review findings: current-spec link traversal is rejected before writes, revision anchors require an immutable commit or deterministic scoped capture, and post-move Close validation rolls back on failure.
- 2026-08-13T23:42:00+08:00 - Completed aggregate validation: 58 tests passed (1 Windows file-symlink case skipped for unavailable privilege), package validate/doctor passed, and docs-architect captures were refreshed.
- 2026-08-14T00:05:00+08:00 - Completed T-009 implementation boundary: commit `4a5717c4936b5daf28b558f2de4dc1b12caa3e64` was present on local `develop`; the final archive commit remains a distinct lifecycle boundary.
- 2026-08-14T00:21:00+08:00 - Re-ran final gates against implementation commit `99b971efd20c05cf12c1984b22aa92e48ddca171`: 59 tests passed with one privilege-limited skip; package, doctor, syntax, docs-architect, readiness, and remote-ref checks passed.
- 2026-08-14T00:21:05+08:00 - Final capture refresh started; subsequent hardening commit superseded `99b971e` with `2ad28f81781d949517bb275f753dcad6d4e80aac`.

## T-009 Completion Note

- Problem: the implementation was already committed and pushed, but the task row and remote capture still reflected the pre-push state.
- Implementation: recorded the immutable implementation commit and verified the remote branch through an explicit `git ls-remote` command capture before Close.
- Decision: keep the archive/Close commit separate from the implementation commit so the lifecycle boundary remains auditable.

## Recovery

- Safe resume: complete any `in_progress` tasks, then choose the next dependency-ready task.
- Rollback: use normal Git commits after implementation; do not destructively reset the shared branch.
