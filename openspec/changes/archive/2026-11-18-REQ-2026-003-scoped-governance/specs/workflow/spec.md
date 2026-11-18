# Delta Spec: workflow

## MODIFIED Requirements

### Requirement `BR-workflow-001`: Composable action lifecycle

The Skill SHALL route work through enabled actions rather than mandatory numbered phases.

#### Scenario `SC-workflow-001`: Low-risk clear change

- **WHEN** a requested change is clear, local, and low risk
- **THEN** the agent MAY skip external exploration and specialist review
- **AND** the agent SHALL verify and report the result; where policy permits a reversible repair, it MAY use no new governance files or one existing handoff note instead of opening a managed change

### Requirement `BR-workflow-006`: Single-truth documentation integration

The Skill SHALL reuse OpenSpec change artifacts as docs-architect requirement, plan, product-spec, and evidence records.

#### Scenario `SC-workflow-007`: Integrated project

- **WHEN** docs-architect is configured in the target project
- **THEN** the workflow SHALL synchronize and validate the existing artifacts
- **AND** it SHALL NOT create mirrored requirement or execution-plan files elsewhere

#### Scenario `SC-workflow-014`: Documentation handshake is operation-specific

- **WHEN** a managed change is ready to close under strict integration, or at high or critical risk under scoped integration
- **THEN** captured successful `impact`, `check`, and written `index` results SHALL each be present
- **AND** one unrelated command result SHALL NOT satisfy multiple operations

#### Scenario `SC-workflow-018`: Scoped close is not a full audit

- **WHEN** an opted-in low- or medium-risk managed change supplies a successful assessment covering the current files and revision baseline
- **THEN** the workflow MAY register that result once for documentation readiness, without publishing an index
- **AND** it SHALL still require behavior evidence and reject an unknown, affected or stale assessment.

## ADDED Requirements

### Requirement `BR-workflow-009`: Isolate historical catalog debt

An unrelated unreadable historical proposal SHALL NOT stop a targeted active verification. Catalog completeness SHALL be explicit rather than silently inferred.

#### Scenario `SC-workflow-019`: A legacy proposal has no readable identity

- **WHEN** a history entry cannot supply a valid ID
- **THEN** normal status SHALL list the readable entries with archive debt, while strict status SHALL fail
- **AND** new changes SHALL avoid sequential allocation from the incomplete catalog, and ambiguous writes SHALL fail.
