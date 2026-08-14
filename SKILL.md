---
name: dev-spec-flow
description: Risk-driven, spec-driven full-stack development workflow for building or changing non-trivial features, systems, apps, pages, APIs, refactors, migrations, and bug fixes. Use when a request needs durable requirements, coordinated implementation, acceptance evidence, review, or lifecycle closure. Turns fuzzy intent into an OpenSpec-style change, selects research, design, tests, and specialist review by uncertainty and failure risk, keeps work moving through implementation, then synchronizes durable documentation and archives the change. Skip trivial one-line edits that do not change durable behavior or decisions.
---

<!-- docs-architect-meta {"schema_version":1,"id":"SYS-dev-spec-flow","type":"system-doc","title":"Dev Spec Flow canonical workflow","status":"active","owners":[],"sources":["SKILL.md","references/**","templates/**","scripts/**"],"update_when":["The workflow, artifact contract, verification policy, close behavior, or runtime tooling changes"],"relations":[{"type":"documents","target":"REQ-2026-001"}],"evidence":[],"affected_docs":[],"verified_at":null,"verified_against":null} -->

# Dev Spec Flow

Turn a development request into a traceable change without forcing every task through the same ceremony. Use composable actions, choose assurance from failure risk, and finish with one close operation that updates durable truth and archives temporary context.

## Start With Context

Before writing:

1. Read applicable repository instructions, the current Git state, manifests, similar code, and existing `openspec/specs/`.
2. Detect available capabilities instead of assuming a platform has subagents, hooks, browser access, plan mode, or another Skill.
3. Preserve unrelated user changes. Follow explicit branch, commit, push, and approval instructions over defaults.
4. Resume an existing change when its requirement is the same intent. Do not create a duplicate change to restart work.

Use the bundled CLI when available:

```text
python <skill-root>/scripts/dev_spec_flow.py --root <project> new <slug> --title <title>
python <skill-root>/scripts/dev_spec_flow.py --root <project> status
python <skill-root>/scripts/dev_spec_flow.py --root <project> verify --change <slug>
python <skill-root>/scripts/dev_spec_flow.py --root <project> close <slug> --dry-run
```

Read [workflow.md](references/workflow.md) for detailed action contracts and resume behavior. Read other references only when their trigger applies.

## Use Composable Actions

```text
intake -> explore? -> propose/update -> apply -> verify? -> close
```

Actions are enabled by available inputs, not separated by mandatory phase gates. Revisit proposal, spec, design, or tasks whenever implementation produces new evidence.

- **intake**: identify or create one change, capture the request and approval source, assign a stable requirement ID, and record timestamps.
- **explore**: investigate only material uncertainty, novelty, version-sensitive APIs, UX direction, architecture, security, migration, or operational risk.
- **propose/update**: maintain the smallest useful artifact set and obtain a user decision only when a material choice or scope question remains.
- **apply**: execute dependency-ready tasks continuously, update durable plans when reality changes, and run impacted checks.
- **verify**: collect sufficient acceptance evidence and conduct risk-triggered review. This action can be lightweight for low-risk work.
- **close**: check readiness, merge delta specs, synchronize durable docs, resolve findings, compress temporary evidence, and archive atomically.

Do not stop between approved tasks merely to ask whether to continue. Stop only for unresolved intent that changes the result, missing external authority or secrets, destructive action requiring approval, or a repeated failure that cannot be resolved safely.

## Select Policy On Two Axes

Do not use one size label to decide documents, tests, and reviewer counts.

### Collaboration complexity

Use complexity to decide how much coordination material is useful:

- **small**: one clear behavior or local fix; concise proposal and task list.
- **medium**: multiple modules or collaborators; fuller delta spec and dependency-aware tasks.
- **large**: multiple domains, migration stages, or independently delivered slices; design and possibly multiple changes.

### Failure risk

Use risk to decide assurance. Consider blast radius, irreversible data change, security/privacy, money, concurrency, external contracts, unfamiliar technology, compliance, rollback difficulty, and production observability.

- **low**: existing checks plus focused runtime or inspection evidence may be enough.
- **medium**: add focused automated coverage for changed stable behavior and relevant boundary checks.
- **high**: require negative-path, migration/rollback, security, contract, concurrency, or operational evidence as applicable.

Read [risk-policy.md](references/risk-policy.md) when selecting or revising these values.

## Maintain One Artifact Model

Use `openspec/` as the change system:

```text
openspec/
  specs/<domain>/spec.md                 current observable behavior
  changes/<slug>/request.md              captured authority, when needed
  changes/<slug>/proposal.md             requirement and lifecycle truth
  changes/<slug>/specs/<domain>/spec.md  temporary delta
  changes/<slug>/design.md               optional change-local design
  changes/<slug>/tasks.md                execution plan and task state
  changes/<slug>/verification.md         single evidence manifest
  changes/<slug>/evidence/*              observed captures referenced by verification
  changes/archive/...                    compressed completed history
```

Use stable IDs for requirement, acceptance, behavior, scenario, and task references. Store lifecycle timestamps and append-only status history in the proposal metadata. Sort by those timestamps, never by filesystem mtime or Markdown position. See [openspec-model.md](references/openspec-model.md).

An explicit imperative user request can authorize its stated scope without a second approval round. When no durable issue, commit, or document already records that authority, capture the request in `request.md` and point proposal `approval` to that resolvable request record. Do not turn a request to analyze, explore, or propose into approval to implement, commit, push, deploy, or destroy data.

Create `design.md` only when a technical choice, migration, security boundary, dependency, or cross-module interaction needs durable explanation. Promote only cross-change, architecturally significant decisions to an ADR.

## Plan Evidence, Not Test Counts

An acceptance criterion or Scenario is an observable example, not an instruction to add one permanent automated test. For each acceptance point select one or more evidence methods:

`existing-test`, `automated`, `command`, `runtime`, `inspection`, `screenshot`, or an explicitly authorized `waived`/`deferred` result.

Require new automated tests for stable contracts with meaningful regression value, reproducible defects, or security/migration/data boundaries. Avoid tests for trivial implementation detail and duplicate coverage that adds no confidence. During apply, run impacted checks; at verify or close, run the appropriate aggregate gate once. Record observed commands and results, not planned checks. See [verification.md](references/verification.md).

## Review From Risk

Default to one integrated diff/spec review. Add a specialist charter only when a risk driver justifies it, for example:

- security, permissions, privacy, or untrusted input;
- data migration, destructive change, or rollback;
- performance, concurrency, or resource limits;
- meaningful UI work requiring UX/accessibility review;
- external contract, cross-module integration, or operations.

Use isolated subagents when available to reduce author bias. Their raw output is temporary: return findings to the coordinator, aggregate and deduplicate them, and do not create one permanent report per reviewer. Zero findings need no file. Unresolved findings must become an accepted waiver, linked issue/requirement, or blocking item before close. See [review-policy.md](references/review-policy.md) and [review-agents.md](references/review-agents.md).

## Close Every Completed Change

Completion is not "implementation ended". Run close immediately when readiness is satisfied:

1. Confirm tasks, acceptance evidence, findings, decisions, and documentation disposition.
2. Merge delta clauses into current specs by stable behavior ID.
3. Synchronize affected current docs and significant ADRs, or record evidence-backed no-change reasoning.
4. Keep one verification/completion record; remove only explicitly registered temporary artifacts under the selected retention policy.
5. Require an explicit `updated` or `no_change_required` documentation disposition, synchronize the human-readable completion fields, write completion and archive timestamps, move the change into chronological archive, and validate the result.

Close must be dry-runnable, idempotent, and recoverable. Never claim success after a partial merge or failed documentation check. See [close-and-retention.md](references/close-and-retention.md).

## Cooperate With Docs Architect

When `docs-architect` and `.docs-architect.json` are present, use it for impact analysis, durable documentation synchronization, relationship checks, indexes, and gardening. Do not create a second documentation tree.

Map artifacts as follows:

- `proposal.md` = requirement
- `tasks.md` = execution plan
- `openspec/specs/<domain>/spec.md` = the only active product spec
- `verification.md` = evidence manifest
- `docs/` and `ARCHITECTURE.md` = current system documentation
- change-local `design.md` = temporary design; promote significant durable decisions to ADR

The delta spec is temporary and is not a second active product spec. If docs-architect is absent, follow the same boundaries in standalone mode. Read [docs-architect-integration.md](references/docs-architect-integration.md) before configuring or closing an integrated repository.

## Respect Runtime Capabilities

The workflow semantics are platform-neutral across Claude, Cursor, Codex, and Grok. Detect capabilities at runtime:

- run independent exploration or review concurrently only when supported;
- otherwise run the same charters sequentially;
- use available official documentation/search tools for version-sensitive work;
- do not hard-code platform-specific slash commands or claim missing capabilities from product name alone.

See [platforms.md](references/platforms.md) for packaging, installation, and conservative fallbacks.

## Finish With Evidence

Before reporting completion:

- run the project checks proportionate to the change;
- run `verify --readiness` and a `close --dry-run` when the CLI is available;
- execute close and confirm the active change is gone, the archive entry exists, and current specs contain the merged clauses;
- run docs-architect `check -> index --write -> check` when integrated;
- inspect Git status/diff and perform only the commit or push operations the user authorized.

Report the changed behavior, durable documents updated, evidence actually observed, retained risks or waivers, archive location, and Git result.
