<!-- docs-architect-meta {"schema_version":1,"id":"EVID-REQ-YYYY-NNN","type":"evidence","title":"Verification for REQ-YYYY-NNN","status":"draft","owners":[],"sources":["openspec/changes/<slug>/**"],"update_when":["Acceptance evidence, aggregate checks, reviews, findings, waivers, or documentation disposition changes"],"relations":[{"type":"validates","target":"REQ-YYYY-NNN"}],"acceptance":[{"id":"AC-1","status":"pending","validates":["AC-1","BR-<domain>-001","SC-<domain>-001"],"methods":[],"evidence":[],"reason":null,"authority":null}],"evidence":[],"documentation_checks":[],"reviews":[{"charter":"integrated","status":"pending","evidence":[]}],"unresolved_findings":[],"affected_docs":[],"verified_at":null,"verified_against":null} -->

# EVID-REQ-YYYY-NNN: Verification For <Change Title>

This is the single retained acceptance and completion evidence manifest. Keep the metadata and
tables aligned. Record only checks that were actually observed; planned evidence belongs in
`tasks.md`.

Acceptance result values are `pending`, `passed`, `failed`, `waived`, or `deferred`. A `waived`
result means an authorized `not_applicable` disposition and requires a reason, resolvable human
authority, and evidence proving that disposition. A `deferred` result requires a linked successor
issue or requirement and cannot satisfy close readiness without an authorized acceptance change.

## Acceptance Evidence

Evidence methods may be `existing-test`, `automated`, `command`, `runtime`, `inspection`, or
`screenshot`. Use the lowest stable layer that proves the outcome. Evidence references must point
to a repository-relative captured result, immutable revision, or durable URL.

| Acceptance | Validates | Result | Methods | Evidence reference | Observed result |
|---|---|---|---|---|---|
| `AC-1` | `REQ-YYYY-NNN#AC-1`, `BR-<domain>-001`, `SC-<domain>-001` | pending | inspection | TODO | TODO |

## Aggregate Checks

Run impacted checks during implementation and one proportionate aggregate gate before close. Do
not repeat the full suite at every task boundary unless a specific risk requires it.

| Command or procedure | Scope | Result | Evidence reference |
|---|---|---|---|
| TODO | TODO | passed / failed | TODO |

When docs-architect is configured, add the captured `impact`, `check`, and index results to
metadata `documentation_checks`. The Close CLI validates these references; the agent runs the
external Skill because its installation path is environment-specific. Each entry must include
one scalar `operation` (`impact`, `check`, or `index`) and reference a successful JSON capture
under this change's `evidence/` directory. A source test or unrelated command file does not count
as an observed capture.

For a multi-file worktree verified before commit, create a deterministic text capture under
`evidence/` containing the base commit, sorted repository-relative paths, each observed SHA-256,
deletions, and the worktree state. Anchor `verified_against` to that capture's own digest. Do not
use an arbitrary single file hash as the revision for a multi-file change; after the implementation
commit exists, prefer that immutable commit OID instead.

## Review Summary

Default to one integrated diff/spec review. Add specialist charters only for applicable risk
drivers. Raw reviewer output is temporary under the `summary` retention profile; retain only
actionable findings here. Use `compliance-review-report.md` only when an explicit audit or
compliance profile requires the full review record.

Mirror each performed review in metadata `reviews` with `charter`, `status`, and resolvable
evidence. Close requires the integrated charter and every registered specialist charter to pass.
The `security/privacy` charter is mandatory whenever proposal risk drivers include
`security-privacy`.

| Charter | Trigger | Result | Evidence reference |
|---|---|---|---|
| integrated | default | TODO | TODO |

## Findings And Dispositions

| Finding | Severity | Disposition | Authority or successor | Evidence |
|---|---|---|---|---|
| None recorded | - | - | - | - |

Unresolved findings must be blocking, explicitly waived by a resolvable authority, or linked to a
successor issue or requirement. Do not use free-text "fix later" as a close disposition.

## Documentation Disposition

- Result: pending / updated / no change required
- Current specs merged: no
- Current system or product docs reviewed: TODO
- Evidence-backed no-change reason, when applicable: TODO
- docs-architect checks, when integrated: TODO

## Limitations And Environment

- Environment or data limitations: none recorded.
- Untested boundaries: none recorded.
- Authorized waivers: none recorded.

## Completion Record

- Verified revision: TODO
- Verification completed at: TODO
- Close dry-run: not run
- Close result and archive location: pending
