<!-- docs-architect-meta {"schema_version":1,"id":"SPEC-workflow","type":"product-spec","title":"Workflow product specification","status":"active","owners":[],"sources":[],"update_when":["Observable workflow behavior changes"],"relations":[],"evidence":[],"affected_docs":[],"verified_at":null,"verified_against":null} -->

# Workflow Product Specification

## Requirements

### Requirement `BR-workflow-001`: Composable action lifecycle

The Skill SHALL route work through enabled actions rather than mandatory numbered phases.

#### Scenario `SC-workflow-001`: Low-risk clear change

- **WHEN** a requested change is clear, local, and low risk
- **THEN** the agent MAY skip external exploration and specialist review
- **AND** it SHALL still collect sufficient acceptance evidence and close the change

### Requirement `BR-workflow-002`: Independent complexity and risk

The Skill SHALL use collaboration complexity to select artifact detail and failure risk to select assurance strength.

#### Scenario `SC-workflow-002`: Small high-risk change

- **WHEN** a small code change affects authorization or irreversible data
- **THEN** the workflow SHALL remain concise in planning
- **AND** it SHALL apply high-assurance verification and specialist review

### Requirement `BR-workflow-003`: Evidence flexibility

The Skill SHALL allow each acceptance point to be proven by the most appropriate resolvable evidence method.

#### Scenario `SC-workflow-003`: Inspection is sufficient

- **WHEN** a prose-only behavior is fully established by focused inspection and existing checks
- **THEN** the workflow SHALL NOT require a redundant new automated test
- **AND** the observed inspection result SHALL be recorded

#### Scenario `SC-workflow-010`: Captured evidence is observed

- **WHEN** an acceptance item is marked passed
- **THEN** at least one evidence reference SHALL point to an observed capture under the change evidence directory
- **AND** a test source or arbitrary repository file alone SHALL NOT prove execution

### Requirement `BR-workflow-004`: Risk-triggered review retention

The Skill SHALL default to an integrated review and persist only actionable findings and a completion evidence summary.

#### Scenario `SC-workflow-004`: Isolated reviewers find no defects

- **WHEN** temporary isolated reviewers return no actionable findings
- **THEN** no per-reviewer report SHALL be retained under the summary profile

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

### Requirement `BR-workflow-006`: Single-truth documentation integration

The Skill SHALL reuse OpenSpec change artifacts as docs-architect requirement, plan, product-spec, and evidence records.

#### Scenario `SC-workflow-007`: Integrated project

- **WHEN** docs-architect is configured in the target project
- **THEN** the workflow SHALL synchronize and validate the existing artifacts
- **AND** it SHALL NOT create mirrored requirement or execution-plan files elsewhere

#### Scenario `SC-workflow-014`: Documentation handshake is operation-specific

- **WHEN** docs-architect integration is enabled and a change is ready to close
- **THEN** captured successful `impact`, `check`, and written `index` results SHALL each be present
- **AND** one unrelated command result SHALL NOT satisfy multiple operations

### Requirement `BR-workflow-007`: Safe canonical distribution

The package SHALL distribute one canonical Skill and update installed managed files only when their current hashes match the recorded installation state.

#### Scenario `SC-workflow-008`: Installed file was customized

- **WHEN** update detects a locally modified managed file
- **THEN** it SHALL preserve the file and report a conflict

#### Scenario `SC-workflow-015`: Installation ownership is verified

- **WHEN** update reads a managed installation record
- **THEN** package identity, target, scope, destination, owned paths, and hashes SHALL match
- **AND** an unowned or forged record SHALL fail before any deletion or replacement

### Requirement `BR-workflow-008`: Explicit chronological lifecycle

Change status and ordering SHALL use stable IDs and ISO 8601 lifecycle timestamps rather than file mtime or mutable headings.

#### Scenario `SC-workflow-009`: Status listing

- **WHEN** active and archived changes are listed
- **THEN** they SHALL be ordered by recorded lifecycle time and stable identity
