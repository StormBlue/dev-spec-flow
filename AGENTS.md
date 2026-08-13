# dev-spec-flow repository instructions

`SKILL.md` is the canonical, platform-neutral workflow. Do not copy its policy into this file or create platform-specific forks of the workflow.

## Work in this repository

- Read `SKILL.md` and only the references relevant to the change.
- Keep runtime policy in `SKILL.md`, detailed guidance in `references/`, reusable output skeletons in `templates/`, and deterministic behavior in `scripts/dev_spec_flow.py`.
- Keep Claude, Cursor, Codex, and Grok differences limited to discovery syntax and capability detection. Do not assert capabilities solely from the platform name.
- Use stable IDs and explicit ISO 8601 lifecycle timestamps. Do not rely on directory order, file mtime, or mutable headings as identity.
- Treat Scenario as an acceptance example. Select evidence by risk; do not mechanically add one automated test per Scenario.
- Do not persist raw multi-agent review output by default. Preserve only actionable unresolved findings and the final evidence summary.
- A completed change must be closed: merge its delta, synchronize durable documentation, apply retention, and archive it.

## Validate changes

Run from the repository root:

```text
python -m unittest discover -s tests -v
python scripts/dev_spec_flow.py validate
python scripts/dev_spec_flow.py doctor --root .
```

For a dogfooded change, also run:

```text
python scripts/dev_spec_flow.py verify --root . --change <slug> --readiness
python scripts/dev_spec_flow.py close --root . <slug> --dry-run
```

Follow the user's explicit branch, commit, and push instructions. Otherwise use the repository's established Git policy and avoid destructive history rewriting.
