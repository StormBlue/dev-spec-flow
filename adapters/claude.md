# dev-spec-flow Project Adapter For Claude Code

Merge the relevant lines into the target repository's existing `CLAUDE.md`; do not replace
handwritten instructions. This adapter only exposes project truth. The installed `dev-spec-flow`
Skill owns the workflow.

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

- Use the installed `dev-spec-flow` Skill for non-trivial behavior changes.
- Detect available subagents, planning, browser, and documentation tools at runtime; do not rely on product-name assumptions.
- Preserve project-specific permission and safety rules outside this managed section.
- Update affected current docs and close the active change before claiming completion.
