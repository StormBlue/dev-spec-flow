# Delta Spec: <domain>

Copy this file to `openspec/changes/<slug>/specs/<domain>/spec.md`. Describe observable
behavior, not implementation. Keep every `BR-*` and `SC-*` ID stable across title edits and
future changes. Each Scenario is an acceptance example, not a mandatory new test.

Delete unused sections before review.

## ADDED Requirements

### Requirement `BR-<domain>-001`: <Observable behavior>

The system SHALL <state one externally observable obligation>.

#### Scenario `SC-<domain>-001`: <Primary example>

- **WHEN** <precondition or action>
- **THEN** <observable result>
- **AND** <additional result, when needed>

#### Scenario `SC-<domain>-002`: <Boundary or failure example>

- **WHEN** <boundary or failure condition>
- **THEN** <observable result>

## MODIFIED Requirements

Copy the complete current clause, including every Scenario, then edit it. Preserve its `BR-*`
and existing `SC-*` IDs. Close replaces the current clause by stable ID and rejects an unknown
or duplicate target.

### Requirement `BR-<domain>-002`: <Current or updated title>

The system MUST <state the complete updated behavior>.

#### Scenario `SC-<domain>-003`: <Complete retained or updated example>

- **WHEN** <condition>
- **THEN** <result>

## REMOVED Requirements

Removal must identify the existing clause and explain compatibility or migration handling.

### Requirement `BR-<domain>-003`: <Removed behavior>

**Reason**: <why the behavior is removed>

**Migration**: <how users, callers, or data move safely; use `not applicable` with a reason>

## RENAMED Requirements

Use this only for a title-only rename. The stable behavior ID must not change. If behavior or
Scenarios also change, use `MODIFIED` with the complete clause instead.

- FROM: `BR-<domain>-004` <old title>
- TO: `BR-<domain>-004` <new title>
