# Design: risk-driven workflow upgrade

## Context

The repository currently contains documentation only. Repeated lifecycle behavior is fragile when expressed solely as prompt prose, while platform-specific copies have already drifted.

## Decisions

### Canonical policy plus deterministic operations

Keep platform-neutral routing in `SKILL.md`. Put detailed choices in one-level references. Implement identity, timestamp, validation, merge, retention, archive, and installation safety in a Python standard-library CLI.

### Proposal metadata is the change manifest

Use one `docs-architect-meta` JSON comment in `proposal.md`; do not add `change.json`. Extra dev-spec-flow fields coexist with docs-architect schema v1 fields. Tasks remain the only task-state source.

### Stable-ID delta merge

Use `### Requirement \`BR-*\`` and `#### Scenario \`SC-*\``. Close parses `ADDED`, `MODIFIED`, `REMOVED`, and `RENAMED` sections by `BR-*`; duplicate or missing targets fail readiness before writes.

### Recoverable close

Close plans all writes in memory, validates the result, writes a journal, replaces files atomically, then moves the change. If an operation fails, restore pre-close bytes and leave the change active. An already archived ID is treated as idempotent success.

### Explicit retention registry

Summary retention removes only files listed in metadata `ephemeral_artifacts`; it never deletes by wildcard. Compliance retention keeps them. Durable artifacts and unresolved findings cannot be registered as ephemeral.

### Safe distribution

`manifest.json` records package version and hashes. Each install records the hashes it wrote. Before an update or managed deletion, validate the recorded package version, manifest hash, file set, and per-file hashes against the installed historical manifest; then overwrite or remove only paths owned by that validated manifest whose current hash still matches the install record.

This is an ownership and local-integrity boundary, not package-authenticity proof. A party able to rewrite both the install record and the historical manifest can forge a self-consistent history. Authenticity against that threat requires a signature, trusted registry metadata, or another external trust anchor; `update` and `doctor` must not claim to provide it.

### Evidence revision anchors

Verification uses an immutable implementation commit whenever one exists. If a multi-file worktree
must be verified before commit, the agent creates a deterministic JSON capture under `evidence/` with
the base commit, exact declared scope, sorted changed paths, observed hashes, deletion entries, and
worktree state, then anchors the manifest to that capture's digest. A single changed-file hash is
valid only for one literal implementation path and cannot stand in for a broader scope.

## Risks and mitigations

- Markdown parsing can be ambiguous: constrain stable headings and reject ambiguity instead of guessing.
- Close can mutate multiple files: precompute, journal, atomic replace, and rollback.
- docs-architect v1 has integration gaps: document its current compatibility and degrade to standalone checks rather than creating duplicate files.
- Platform conventions evolve: keep adapters thin and detect capabilities; require explicit Grok destination.

## Recovery

All lifecycle CLI mutations support dry-run. Close writes `.dev-spec-flow-close.json` inside the active change during the transaction and restores captured content if a write or move fails.
