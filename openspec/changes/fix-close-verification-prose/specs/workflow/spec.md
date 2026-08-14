# Delta Spec: workflow

## MODIFIED Requirements

### Requirement `BR-workflow-005`: Atomic close

The CLI SHALL dry-run readiness, require an explicit documentation disposition, merge delta clauses
by stable ID, apply explicit retention, synchronize human-readable completion fields, and archive a
change without leaving partially applied current specs or stale lifecycle prose.

#### Scenario `SC-workflow-005`: Close precondition fails

- **WHEN** a task, acceptance item, evidence, documentation disposition, or merge baseline is not ready
- **THEN** close SHALL fail before mutating current specs, lifecycle prose, or the change directory

#### Scenario `SC-workflow-011`: Retention preserves link integrity

- **WHEN** summary or minimal retention would delete a registered temporary file
- **THEN** close SHALL reject any retained Markdown link to that file before mutation

#### Scenario `SC-workflow-012`: Later behavior evolution remains idempotent

- **WHEN** a later archived change modifies, renames, or removes the same stable behavior ID
- **THEN** repeating the earlier close SHALL compare the replayed terminal lineage with the current spec
- **AND** a later ADDED operation SHALL NOT recycle the stable ID

#### Scenario `SC-workflow-006`: Repeated close

- **WHEN** close is invoked for a change already archived with the same identity
- **THEN** it SHALL report the archived result without duplicating clauses or archive directories

#### Scenario `SC-workflow-013`: Lifecycle identity is unique

- **WHEN** active and archived change catalogs are scanned
- **THEN** duplicate non-empty requirement IDs SHALL fail status, verify, close, and allocation before mutation

#### Scenario `SC-workflow-016`: Completion prose reflects observed Close results

- **WHEN** a Close transaction succeeds
- **THEN** proposal and verification lifecycle prose SHALL match the actual documentation, merge, revision, completion, archive, and post-move validation results
- **AND** it SHALL NOT claim an unobserved explicit dry-run or idempotent re-check

#### Scenario `SC-workflow-017`: Markdown lifecycle structure is ambiguous

- **WHEN** a lifecycle section or field is duplicated, fenced, or nested
- **THEN** Close SHALL preserve fenced and nested content and reject ambiguous duplicate top-level structure before mutation
