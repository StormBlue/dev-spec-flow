<!-- docs-architect-meta {"schema_version":1,"id":"REQ-2026-003","type":"requirement","title":"Keep historical documentation debt off the implementation path","status":"done","owners":[],"origin":{"kind":"request","ref":"openspec/changes/archive/2026-11-18-REQ-2026-003-scoped-governance/request.md"},"approval":{"kind":"request-record","ref":"openspec/changes/archive/2026-11-18-REQ-2026-003-scoped-governance/request.md"},"sources":[],"update_when":["Scope, acceptance, risk, implementation, evidence, or documentation disposition changes"],"relations":[],"dependencies":[],"acceptance":[{"id":"AC-1","text":"A reversible fix can proceed with proportionate evidence; unrelated archive debt is visible without blocking the active task, and a scoped receipt cannot certify strict or high-risk close.","status":"passed","evidence":[{"kind":"command","ref":"openspec/changes/archive/2026-11-18-REQ-2026-003-scoped-governance/evidence/tests.txt","description":"Observed test suites, clean checkouts and end-to-end cross-skill validation"},{"kind":"log","ref":"openspec/changes/archive/2026-11-18-REQ-2026-003-scoped-governance/evidence/review.txt","description":"Integrated review of routing, strict compatibility, archive identity and distribution"}]}],"evidence":[{"kind":"command","ref":"openspec/changes/archive/2026-11-18-REQ-2026-003-scoped-governance/evidence/tests.txt","description":"Observed test suites, clean checkouts and end-to-end cross-skill validation"}],"affected_code":["scripts/dev_spec_flow.py","tests/test_dev_spec_flow.py"],"affected_docs":["SKILL.md","README.md"],"open_questions":[],"documentation_disposition":"updated","no_doc_change_scope":[],"no_doc_change_reason":null,"slug":"scoped-governance","complexity":"medium","risk":{"level":"medium","drivers":[]},"retention":"summary","domains":["workflow"],"spec_baselines":{"workflow":"58fbae22c5472388993f90c8e3f2f56f202beba5799904cf6d15247bdfaf3d96"},"ephemeral_artifacts":[],"created_at":"2026-11-18T13:34:59+08:00","updated_at":"2026-11-18T14:01:47+08:00","status_changed_at":"2026-11-18T14:01:47+08:00","completed_at":"2026-11-18T14:01:47+08:00","archived_at":"2026-11-18T14:01:47+08:00","status_history":[{"status":"accepted","at":"2026-11-18T13:34:59+08:00","reason":"Change created"},{"status":"in_progress","at":"2026-11-18T14:01:20+08:00","reason":"Implemented and verified the confirmed workflow changes"},{"status":"done","at":"2026-11-18T14:01:47+08:00","reason":"Close completed"}],"verified_at":"2026-11-18T14:01:20+08:00","verified_against":"823b8f53345c54a3e75c83bbb2f03730ad3a95e2","docs_policy_at_close":"strict"} -->

# REQ-2026-003: Keep historical documentation debt off the implementation path

## Need

- Routine repairs were delayed by unrelated archive and metadata failures. Give the implementing agent a reliable next action without certifying incomplete history.

## Scope

### In scope

- Risk-based routing, archive-aware discovery, scoped receipts, shared-install diagnostics and canonical package bytes.

### Out of scope

- Do not backfill historical approval or change the defaults of existing strict projects.

## Acceptance Criteria

- [x] `AC-1` - A reversible fix can proceed with proportionate evidence; unrelated archive debt is visible without blocking the active task, and a scoped receipt cannot certify strict or high-risk close.

## Documentation Disposition

- Result: updated
- Affected docs: `SKILL.md`, `README.md`

## History

- 2026-11-18T13:34:59+08:00 - Change created.

- 2026-11-18T14:01:47+08:00 - Close completed; requirement archived.
