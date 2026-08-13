<!-- docs-architect-meta {"schema_version":1,"id":"REQ-YYYY-NNN","type":"requirement","title":"TODO: concise observable outcome","status":"intake","owners":[],"origin":null,"approval":null,"sources":[],"update_when":["The accepted outcome, scope, risk, lifecycle state, or documentation impact changes"],"relations":[],"dependencies":[],"acceptance":[{"id":"AC-1","text":"TODO: observable acceptance outcome","status":"pending","evidence":[]}],"evidence":[],"affected_code":[],"affected_docs":[],"open_questions":[],"documentation_disposition":"pending","no_doc_change_scope":[],"no_doc_change_reason":null,"slug":"verb-led-change-slug","complexity":"small","risk":{"level":"low","drivers":[]},"retention":"summary","ephemeral_artifacts":[],"created_at":"<ISO-8601 timestamp with timezone>","updated_at":"<ISO-8601 timestamp with timezone>","status_changed_at":"<ISO-8601 timestamp with timezone>","completed_at":null,"archived_at":null,"status_history":[{"status":"intake","at":"<ISO-8601 timestamp with timezone>","reason":"Requirement recorded; approval not yet established"}]} -->

# REQ-YYYY-NNN: TODO: Concise Observable Outcome

Use this file as the requirement and lifecycle source of truth for one change. Keep the
metadata and prose aligned. Record approval only from a resolvable authority source, append
material status transitions to `status_history`, and never infer timestamps from file mtime.
An explicit imperative user request can authorize exactly the scope it states; when no durable
external authority exists, capture that request faithfully in `request.md` and use it as a
`request-record`. Analysis or proposal requests do not authorize implementation or Git/release
actions.

## Why

State the current problem or opportunity, who is affected, and why the change matters now.
Use `unknown` for facts that still require evidence.

## Outcome

Describe the user- or operator-observable result. Keep implementation choices in `design.md`.

## Scope

### In scope

- TODO

### Out of scope

- TODO

## Capability Changes

Each row must correspond to one delta file under `specs/<domain>/spec.md`.

| Domain | Change | Summary |
|---|---|---|
| `<domain>` | added / modified / removed / renamed | TODO |

## Acceptance Criteria

Keep IDs stable and keep this list aligned with metadata `acceptance`. A Scenario may support
an acceptance item, but it does not mechanically require a new automated test.

- [ ] `AC-1` - TODO: state an observable result

## Impact

- Affected code or configuration: unknown
- External contracts or dependencies: none known
- Data or migration impact: none known
- Rollback constraints: none known

## Documentation Disposition

Keep `documentation_disposition` as `pending` until current product or system documentation is
synchronized. For `no_change_required`, leave `affected_docs` empty, record the reviewed scope
in `no_doc_change_scope`, give a concrete reason, and link captured review evidence.

## Open Questions

- None recorded.

## History

Append material scope, acceptance, risk, approval, or status changes. Do not silently rewrite
approved criteria.

- `<timestamp>` - Requirement recorded.
