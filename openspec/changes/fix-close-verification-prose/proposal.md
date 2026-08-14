<!-- docs-architect-meta {"schema_version":1,"id":"REQ-2026-002","type":"requirement","title":"Synchronize Close completion prose","status":"in_progress","owners":[],"origin":{"kind":"request","ref":"openspec/changes/fix-close-verification-prose/request.md"},"approval":{"kind":"request-record","ref":"openspec/changes/fix-close-verification-prose/request.md"},"sources":["scripts/dev_spec_flow.py","templates/proposal.md","templates/verification.md","references/close-and-retention.md","tests/test_dev_spec_flow.py"],"update_when":["Close lifecycle prose, documentation disposition gates, or Markdown synchronization changes"],"relations":[{"type":"related_to","target":"REQ-2026-001"}],"dependencies":[],"acceptance":[{"id":"AC-1","text":"Close synchronizes proposal and verification lifecycle prose to the actual documentation, merge, revision, completion, archive, and post-move validation results","status":"pending","evidence":[]},{"id":"AC-2","text":"Close planning and post-close validation labels describe only events actually performed and do not claim an implicit dry-run or idempotent re-check","status":"pending","evidence":[]},{"id":"AC-3","text":"Lifecycle prose synchronization preserves fenced and nested Markdown and rejects duplicate lifecycle sections or fields before mutation","status":"pending","evidence":[]},{"id":"AC-4","text":"Close rejects pending or unknown documentation dispositions in both integrated and standalone repositories","status":"pending","evidence":[]},{"id":"AC-5","text":"Close rollback restores proposal and verification bytes when archive movement or post-move validation fails","status":"pending","evidence":[]}],"evidence":[],"affected_code":["scripts/dev_spec_flow.py","templates/proposal.md","templates/verification.md","references/close-and-retention.md","tests/test_dev_spec_flow.py"],"affected_docs":["SKILL.md"],"open_questions":[],"documentation_disposition":"updated","no_doc_change_scope":[],"no_doc_change_reason":null,"slug":"fix-close-verification-prose","complexity":"small","risk":{"level":"medium","drivers":["workflow-contract","destructive-archive"]},"retention":"summary","domains":["workflow"],"spec_baselines":{"workflow":"558490cab1a277f14cc38d8dfb7e923cefa8db5d61688d5732f185152bcab487"},"ephemeral_artifacts":[],"created_at":"2026-08-14T01:16:30+08:00","updated_at":"2026-08-14T01:31:00+08:00","status_changed_at":"2026-08-14T01:31:00+08:00","completed_at":null,"archived_at":null,"status_history":[{"status":"accepted","at":"2026-08-14T01:16:30+08:00","reason":"Change created"},{"status":"in_progress","at":"2026-08-14T01:31:00+08:00","reason":"Final Close audit found stale and ambiguous lifecycle prose"}],"verified_at":null,"verified_against":null} -->

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

- [ ] `AC-1` - Close records actual documentation, merge, revision, completion, archive, and validation results.
- [ ] `AC-2` - Lifecycle labels do not overclaim dry-run or idempotence events.
- [ ] `AC-3` - Fenced/nested Markdown is preserved and duplicate lifecycle structure is rejected.
- [ ] `AC-4` - Pending or unknown documentation dispositions block Close in all repository modes.
- [ ] `AC-5` - Transaction failures restore lifecycle artifact bytes.

## Documentation Disposition

- Result: updated
- Affected docs: `SKILL.md`

## History

- 2026-08-14T01:16:30+08:00 - Change created.
- 2026-08-14T01:31:00+08:00 - Entered implementation after the final Close audit identified stale lifecycle prose.
