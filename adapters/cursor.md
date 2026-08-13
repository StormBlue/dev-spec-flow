---
description: Discover the project's dev-spec-flow artifacts and validation commands.
alwaysApply: true
---

# dev-spec-flow Project Discovery

Merge this template into an existing `.cursor/rules/*.mdc` rule or create one only when the team
explicitly wants a project-level Cursor adapter. Do not duplicate the installed Skill workflow.

- Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
- Documentation index: [docs/index.md](../../docs/index.md)
- Current behavior: [openspec/specs/](../../openspec/specs/)
- Active changes: [openspec/changes/](../../openspec/changes/)
- Project checks: `<verified project command>`
- Change readiness: `python <skill-root>/scripts/dev_spec_flow.py --root . verify --change <slug> --readiness`
- Documentation checks: `<verified docs-architect command, when configured>`

Use the installed `dev-spec-flow` Skill for non-trivial behavior changes. Detect subagent, browser,
planning, and documentation capabilities at runtime. Preserve existing path-scoped rules, and close
the active change before claiming completion.
