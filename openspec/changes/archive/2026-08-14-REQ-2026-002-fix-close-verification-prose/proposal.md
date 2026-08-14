<!-- docs-architect-meta {"schema_version":1,"id":"REQ-2026-002","type":"requirement","title":"Synchronize Close completion prose","status":"done","owners":[],"origin":{"kind":"request","ref":"openspec/changes/archive/2026-08-14-REQ-2026-002-fix-close-verification-prose/request.md"},"approval":{"kind":"request-record","ref":"openspec/changes/archive/2026-08-14-REQ-2026-002-fix-close-verification-prose/request.md"},"sources":["scripts/dev_spec_flow.py","templates/proposal.md","templates/verification.md","references/close-and-retention.md","tests/test_dev_spec_flow.py"],"update_when":["Close lifecycle prose, documentation disposition gates, or Markdown synchronization changes"],"relations":[{"type":"related_to","target":"REQ-2026-001"}],"dependencies":[],"acceptance":[{"id":"AC-1","text":"Close synchronizes proposal and verification lifecycle prose to the actual documentation, merge, revision, completion, archive, and post-move validation results","status":"passed","evidence":[{"kind":"command","ref":"openspec/changes/archive/2026-08-14-REQ-2026-002-fix-close-verification-prose/evidence/tests.txt","description":"Focused and full regression tests observed passing."}]},{"id":"AC-2","text":"Close planning and post-close validation labels describe only events actually performed and do not claim an implicit dry-run or idempotent re-check","status":"passed","evidence":[{"kind":"document","ref":"openspec/changes/archive/2026-08-14-REQ-2026-002-fix-close-verification-prose/evidence/review-integrated.md","description":"Integrated review confirms labels describe readiness planning and post-move validation only."}]},{"id":"AC-3","text":"Lifecycle prose synchronization preserves fenced and nested Markdown and rejects duplicate lifecycle sections or fields before mutation","status":"passed","evidence":[{"kind":"command","ref":"openspec/changes/archive/2026-08-14-REQ-2026-002-fix-close-verification-prose/evidence/tests.txt","description":"Fence, nested, duplicate field, and duplicate section regression tests observed passing."}]},{"id":"AC-4","text":"Close rejects pending or unknown documentation dispositions in both integrated and standalone repositories","status":"passed","evidence":[{"kind":"command","ref":"openspec/changes/archive/2026-08-14-REQ-2026-002-fix-close-verification-prose/evidence/tests.txt","description":"Standalone pending disposition readiness rejection observed passing."}]},{"id":"AC-5","text":"Close rollback restores proposal and verification bytes when archive movement or post-move validation fails","status":"passed","evidence":[{"kind":"command","ref":"openspec/changes/archive/2026-08-14-REQ-2026-002-fix-close-verification-prose/evidence/tests.txt","description":"Move and post-validation rollback tests observed passing."}]}],"evidence":[{"kind":"command","ref":"openspec/changes/archive/2026-08-14-REQ-2026-002-fix-close-verification-prose/evidence/tests.txt","description":"Captured unittest command and observed result."},{"kind":"command","ref":"openspec/changes/archive/2026-08-14-REQ-2026-002-fix-close-verification-prose/evidence/compile.txt","description":"Captured syntax compilation result."},{"kind":"command","ref":"openspec/changes/archive/2026-08-14-REQ-2026-002-fix-close-verification-prose/evidence/docs-check.json","description":"Captured docs-architect check result."},{"kind":"command","ref":"openspec/changes/archive/2026-08-14-REQ-2026-002-fix-close-verification-prose/evidence/docs-impact.json","description":"Captured docs-architect impact result."},{"kind":"command","ref":"openspec/changes/archive/2026-08-14-REQ-2026-002-fix-close-verification-prose/evidence/docs-index.json","description":"Captured docs-architect index write result."}],"affected_code":["scripts/dev_spec_flow.py","templates/proposal.md","templates/verification.md","references/close-and-retention.md","tests/test_dev_spec_flow.py"],"affected_docs":["SKILL.md"],"open_questions":[],"documentation_disposition":"updated","no_doc_change_scope":[],"no_doc_change_reason":null,"slug":"fix-close-verification-prose","complexity":"small","risk":{"level":"medium","drivers":["workflow-contract","destructive-archive"]},"retention":"summary","domains":["workflow"],"spec_baselines":{"workflow":"558490cab1a277f14cc38d8dfb7e923cefa8db5d61688d5732f185152bcab487"},"ephemeral_artifacts":[],"created_at":"2026-08-14T01:16:30+08:00","updated_at":"2026-08-14T15:39:28+08:00","status_changed_at":"2026-08-14T15:39:28+08:00","completed_at":"2026-08-14T15:39:28+08:00","archived_at":"2026-08-14T15:39:28+08:00","status_history":[{"status":"accepted","at":"2026-08-14T01:16:30+08:00","reason":"Change created"},{"status":"in_progress","at":"2026-08-14T01:31:00+08:00","reason":"Final Close audit found stale and ambiguous lifecycle prose"},{"status":"done","at":"2026-08-14T15:39:28+08:00","reason":"Close completed"}],"verified_at":"2026-08-14T15:45:00+08:00","verified_against":"39370df5896061f026fd4d42426869e20dca8799"} -->

# REQ-2026-002: Synchronize Close completion prose

## Need

The first Close implementation updated lifecycle metadata but could leave template prose such as
`pending Close`, or translate legacy dry-run/idempotence labels into claims that the current Close
did not perform. Ambiguous Markdown could also be rewritten inside examples.

## Scope

### In scope

- Synchronize proposal and verification completion prose during Close.
- Require an explicit documentation disposition in standalone and integrated repositories.
- Preserve code examples and nested lists; reject ambiguous duplicate lifecycle structure.
- Cover successful Close and transactional rollback with focused regression tests.

### Out of scope

- Rewriting historical evidence from `REQ-2026-001`.
- Persisting an idempotence result after a second Close invocation.
- General-purpose Markdown parsing outside lifecycle sections.

## Acceptance Criteria

- [x] `AC-1` - Close records actual documentation, merge, revision, completion, archive, and validation results.
- [x] `AC-2` - Lifecycle labels do not overclaim dry-run or idempotence events.
- [x] `AC-3` - Fenced/nested Markdown is preserved and duplicate lifecycle structure is rejected.
- [x] `AC-4` - Pending or unknown documentation dispositions block Close in all repository modes.
- [x] `AC-5` - Transaction failures restore lifecycle artifact bytes.

## Documentation Disposition

- Result: updated
- Affected docs: `SKILL.md`

## History

- 2026-08-14T01:16:30+08:00 - Change created.
- 2026-08-14T01:31:00+08:00 - Entered implementation after the final Close audit identified stale lifecycle prose.

- 2026-08-14T15:39:28+08:00 - Close completed; requirement archived.
