# dev-spec-flow Project Adapter For Codex

Merge the relevant lines into the target repository's existing `AGENTS.md`; never overwrite
project commands or scoped instructions. This adapter points to shared truth. The installed
`dev-spec-flow` Skill owns the workflow.

## Project Sources Of Truth

- Architecture: [ARCHITECTURE.md](ARCHITECTURE.md)
- Documentation index: [docs/index.md](docs/index.md)
- Current behavior: [openspec/specs/](openspec/specs/)
- Active changes: [openspec/changes/](openspec/changes/)

## Validation

- Project checks: `<verified project command>`
- Change readiness: `python <skill-root>/scripts/dev_spec_flow.py --root . verify --change <slug> --readiness`
- Documentation checks: `<verified docs-architect command, when configured>`

## Constraints

- Use `$dev-spec-flow` for non-trivial behavior changes.
- Detect multi-agent, planning, browser, and documentation capabilities at runtime; do not assume Codex lacks them.
- Preserve nested `AGENTS.md` scope and all project-specific safety constraints.
- Update affected current docs and close the active change before claiming completion.
