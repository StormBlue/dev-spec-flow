from __future__ import annotations

import argparse
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import dev_spec_flow as flow


def namespace(**values: object) -> argparse.Namespace:
    return argparse.Namespace(**values)


class FlowTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write(self, relative: str, content: str | bytes) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
        return path

    def new_args(self, slug: str = "add-export", **overrides: object) -> argparse.Namespace:
        values: dict[str, object] = {
            "slug": slug,
            "title": "Add export",
            "complexity": "medium",
            "risk_level": "medium",
            "risk_driver": ["external-contract"],
            "retention": "summary",
            "domain": ["export"],
            "approved": True,
            "request": "User explicitly approved export.",
        }
        values.update(overrides)
        return namespace(**values)

    def create_change(self, slug: str = "add-export") -> flow.Change:
        payload, exit_code = flow.run_new(self.root, self.new_args(slug))
        self.assertEqual(exit_code, 0, payload)
        change = flow.find_change(self.root, slug, active_only=True)
        self.assertIsNotNone(change)
        return change  # type: ignore[return-value]

    def ready_change(self, slug: str = "add-export") -> flow.Change:
        change = self.create_change(slug)
        for artifact in (change.proposal, change.path / "tasks.md"):
            artifact.write_text(
                artifact.read_text(encoding="utf-8").replace("TODO", "Defined"),
                encoding="utf-8",
            )
        tasks = change.path / "tasks.md"
        tasks.write_text(
            tasks.read_text(encoding="utf-8").replace(
                "| `T-001` | 1 | pending |", "| `T-001` | 1 | completed |"
            ),
            encoding="utf-8",
        )
        proposal_text, proposal = flow.read_metadata(change.proposal)
        proposal["status"] = "in_progress"
        implementation_path = self.write("src/export.py", "implemented export\n")
        proposal["affected_code"] = [implementation_path.relative_to(self.root).as_posix()]
        proposal["status_history"].append(
            {"status": "in_progress", "at": proposal["updated_at"], "reason": "Implementation started"}
        )
        change.proposal.write_text(flow.replace_metadata(proposal_text, proposal), encoding="utf-8")
        verification_path = change.path / "verification.md"
        verification_text, verification = flow.read_metadata(verification_path)
        evidence_path = self.write(
            f"openspec/changes/{slug}/evidence/check.txt",
            "python -m unittest\nOK\n",
        )
        verification["acceptance"] = [
            {
                "id": "AC-1",
                "status": "passed",
                "validates": ["AC-1", "BR-export-001", "SC-export-001"],
                "methods": ["command"],
                "evidence": [
                    {
                        "kind": "command",
                        "ref": evidence_path.relative_to(self.root).as_posix(),
                        "description": "Observed passing check",
                    }
                ],
                "reason": None,
                "authority": None,
            }
        ]
        verification["evidence"] = [
            {
                "kind": "command",
                "ref": evidence_path.relative_to(self.root).as_posix(),
                "description": "Aggregate verification output",
            }
        ]
        verification["unresolved_findings"] = []
        verification["reviews"] = [
            {
                "charter": "integrated",
                "status": "passed",
                "evidence": [
                    {
                        "kind": "log",
                        "ref": evidence_path.relative_to(self.root).as_posix(),
                        "description": "Integrated diff and spec review completed",
                    }
                ],
            }
        ]
        verification["verified_at"] = proposal["updated_at"]
        verification["verified_against"] = (
            f"sha256:{flow.sha256_file(implementation_path)}@{implementation_path.relative_to(self.root).as_posix()}"
        )
        verification_path.write_text(
            flow.replace_metadata(verification_text, verification), encoding="utf-8"
        )
        return flow.find_change(self.root, slug, active_only=True)  # type: ignore[return-value]


class NewAndStatusTests(FlowTestCase):
    def test_new_creates_single_manifest_stable_ids_and_iso_times(self) -> None:
        change = self.create_change()

        self.assertEqual(change.metadata["id"], f"REQ-{flow.dt.datetime.now().year}-001")
        self.assertEqual(change.metadata["slug"], "add-export")
        self.assertTrue(flow.valid_iso(change.metadata["created_at"]))
        self.assertEqual(change.metadata["status"], "accepted")
        self.assertTrue((change.path / "request.md").is_file())
        self.assertTrue((change.path / "tasks.md").is_file())
        self.assertTrue((change.path / "verification.md").is_file())
        tasks_metadata = flow.read_metadata(change.path / "tasks.md")[1]
        self.assertNotIn("acceptance", tasks_metadata)
        delta = (change.path / "specs/export/spec.md").read_text(encoding="utf-8")
        self.assertIn("BR-export-001", delta)
        self.assertIn("SC-export-001", delta)
        self.assertEqual(len(flow.METADATA_RE.findall(change.proposal.read_text(encoding="utf-8"))), 1)

    def test_ids_do_not_recycle_archived_requirements(self) -> None:
        first = self.create_change("add-first")
        archive = self.root / "openspec/changes/archive/2026-01-01-first"
        archive.parent.mkdir(parents=True)
        os.replace(first.path, archive)

        second = self.create_change("add-second")

        self.assertTrue(second.metadata["id"].endswith("-002"))

    def test_status_orders_by_created_at_not_directory_name(self) -> None:
        zulu = self.create_change("z-change")
        alpha = self.create_change("a-change")
        text, metadata = flow.read_metadata(zulu.proposal)
        metadata["created_at"] = "2026-01-01T00:00:00+08:00"
        zulu.proposal.write_text(flow.replace_metadata(text, metadata), encoding="utf-8")
        text, metadata = flow.read_metadata(alpha.proposal)
        metadata["created_at"] = "2026-02-01T00:00:00+08:00"
        alpha.proposal.write_text(flow.replace_metadata(text, metadata), encoding="utf-8")

        payload, exit_code = flow.run_status(self.root, namespace())

        self.assertEqual(exit_code, 0, payload)
        self.assertEqual([item["slug"] for item in payload["changes"]], ["z-change", "a-change"])

    def test_new_rejects_unsafe_or_duplicate_slug(self) -> None:
        self.create_change()
        with self.assertRaises(flow.FlowError):
            flow.run_new(self.root, self.new_args())
        with self.assertRaises(flow.FlowError):
            flow.run_new(self.root, self.new_args("../escape"))


class DeltaMergeTests(FlowTestCase):
    def test_parse_delta_rejects_empty_or_malformed_requirement_sections(self) -> None:
        empty = self.write("empty.md", "## ADDED Requirements\n\n> none yet\n")
        with self.assertRaises(flow.FlowError):
            flow.parse_delta(empty)
        malformed = self.write(
            "malformed.md",
            "## ADDED Requirements\n\n### Requirement: missing identity\nThe system SHALL fail.\n",
        )
        with self.assertRaises(flow.FlowError):
            flow.parse_delta(malformed)

    def test_new_product_spec_has_active_docs_architect_metadata(self) -> None:
        delta = flow.Delta(
            [flow.Clause("BR-api-001", "List widgets", "### Requirement `BR-api-001`: List widgets\nThe system SHALL list widgets.\n\n#### Scenario `SC-api-001`: Success\n- **WHEN** requested\n- **THEN** return widgets")],
            [], [], [], ["SC-api-001"],
        )

        merged = flow.merge_delta(None, delta, "api")
        metadata = flow.metadata_from_text(merged, "merged")

        self.assertEqual(metadata["id"], "SPEC-api")
        self.assertEqual(metadata["type"], "product-spec")
        self.assertEqual(metadata["status"], "active")
        self.assertIn("BR-api-001", merged)

    def test_merge_add_modify_remove_and_rename_by_id(self) -> None:
        current = flow.product_spec_header("api") + """

### Requirement `BR-api-001`: Old title
The system SHALL return old data.

#### Scenario `SC-api-001`: Old case
- **WHEN** called
- **THEN** return old data

### Requirement `BR-api-002`: Remove me
The system SHALL expose legacy data.

#### Scenario `SC-api-002`: Legacy case
- **WHEN** called
- **THEN** return legacy data
"""
        delta = flow.Delta(
            [flow.Clause("BR-api-003", "Add me", "### Requirement `BR-api-003`: Add me\nThe system SHALL add data.\n\n#### Scenario `SC-api-003`: Add case\n- **WHEN** called\n- **THEN** add data")],
            [flow.Clause("BR-api-001", "Updated title", "### Requirement `BR-api-001`: Updated title\nThe system SHALL return new data.\n\n#### Scenario `SC-api-001`: Updated case\n- **WHEN** called\n- **THEN** return new data")],
            [flow.Clause("BR-api-002", "Remove me", "### Requirement `BR-api-002`: Remove me\n**Reason**: obsolete\n**Migration**: use new API")],
            [("BR-api-003", "Add me", "Added behavior")],
            ["SC-api-003", "SC-api-001"],
        )

        merged = flow.merge_delta(current, delta, "api")

        self.assertIn("BR-api-001`: Updated title", merged)
        self.assertIn("BR-api-003`: Added behavior", merged)
        self.assertNotIn("BR-api-002", merged)
        self.assertEqual(merged.count("BR-api-001"), 1)

    def test_merge_rejects_unknown_or_duplicate_targets(self) -> None:
        current = flow.product_spec_header("api")
        clause = flow.Clause("BR-api-999", "Missing", "### Requirement `BR-api-999`: Missing\nText\n\n#### Scenario `SC-api-999`: Case\n- WHEN x\n- THEN y")
        with self.assertRaises(flow.FlowError):
            flow.merge_delta(current, flow.Delta([], [clause], [], [], ["SC-api-999"]), "api")
        with self.assertRaises(flow.FlowError):
            flow.merge_delta(current, flow.Delta([], [], [clause], [], []), "api")

    def test_parse_delta_does_not_include_later_sections_in_clause(self) -> None:
        path = self.write(
            "delta.md",
            """## ADDED Requirements

### Requirement `BR-a-001`: Add
The system SHALL add.

#### Scenario `SC-a-001`: Works
- **WHEN** used
- **THEN** works

## REMOVED Requirements

### Requirement `BR-a-002`: Remove
**Reason**: obsolete
**Migration**: none required
""",
        )
        delta = flow.parse_delta(path)
        self.assertNotIn("REMOVED", delta.added[0].text)
        self.assertEqual(delta.removed[0].clause_id, "BR-a-002")

    def test_merge_preserves_trailing_non_requirement_sections(self) -> None:
        current = (
            flow.product_spec_header("api")
            + "\n### Requirement `BR-api-001`: Existing\nThe system SHALL work.\n\n"
            + "#### Scenario `SC-api-001`: Works\n- **WHEN** used\n- **THEN** work\n\n"
            + "## Notes\n\nKeep this appendix.\n"
        )
        replacement = flow.Clause(
            "BR-api-001", "Updated",
            "### Requirement `BR-api-001`: Updated\nThe system SHALL work better.\n\n"
            "#### Scenario `SC-api-001`: Works\n- **WHEN** used\n- **THEN** work better",
        )

        merged = flow.merge_delta(
            current, flow.Delta([], [replacement], [], [], ["SC-api-001"]), "api"
        )

        self.assertIn("## Notes\n\nKeep this appendix.", merged)
        self.assertEqual(merged.count("## Notes"), 1)


class VerifyAndCloseTests(FlowTestCase):
    def test_readiness_rejects_test_source_as_observed_evidence(self) -> None:
        change = self.ready_change()
        source = self.write("tests/test_feature.py", "def test_feature(): pass\n")
        path = change.path / "verification.md"
        text, metadata = flow.read_metadata(path)
        metadata["acceptance"][0]["evidence"] = [{
            "kind": "test", "ref": f"{source.relative_to(self.root).as_posix()}::test_feature",
            "description": "Test definition exists",
        }]
        path.write_text(flow.replace_metadata(text, metadata), encoding="utf-8")
        result = flow.validate_change(change, readiness=True)
        self.assertFalse(result["ok"])
        self.assertTrue(any("captured observation" in error for error in result["errors"]))

    def test_security_privacy_driver_requires_specialist_review(self) -> None:
        change = self.ready_change()
        path = change.proposal
        text, metadata = flow.read_metadata(path)
        metadata["risk"]["drivers"] = ["security-privacy"]
        path.write_text(flow.replace_metadata(text, metadata), encoding="utf-8")
        result = flow.validate_change(change, readiness=True)
        self.assertFalse(result["ok"])
        self.assertTrue(any("security/privacy" in error for error in result["errors"]))

    def test_retention_rejects_markdown_link_to_ephemeral_file(self) -> None:
        change = self.ready_change()
        temporary = self.write("openspec/changes/add-export/review-security.md", "temporary\n")
        tasks = change.path / "tasks.md"
        tasks.write_text(tasks.read_text(encoding="utf-8") + "\nSee [review](review-security.md).\n", encoding="utf-8")
        text, metadata = flow.read_metadata(change.proposal)
        metadata["ephemeral_artifacts"] = ["review-security.md"]
        path = change.proposal
        path.write_text(flow.replace_metadata(text, metadata), encoding="utf-8")
        result = flow.validate_change(change, readiness=True)
        self.assertFalse(result["ok"])
        self.assertTrue(any("linked from tasks.md" in error for error in result["errors"]))
        self.assertTrue(temporary.exists())

    def test_duplicate_requirement_id_is_rejected_across_active_and_archive(self) -> None:
        first = self.create_change("first-change")
        second = self.create_change("second-change")
        text, metadata = flow.read_metadata(second.proposal)
        metadata["id"] = flow.read_metadata(first.proposal)[1]["id"]
        second.proposal.write_text(flow.replace_metadata(text, metadata), encoding="utf-8")
        with self.assertRaises(flow.FlowError) as caught:
            flow.scan_changes(self.root, include_archive=False)
        self.assertIn("Duplicate requirement IDs", str(caught.exception))

    def test_readiness_requires_completed_tasks_and_observed_evidence(self) -> None:
        change = self.create_change()
        result = flow.validate_change(change, readiness=True)

        self.assertFalse(result["ok"])
        joined = "\n".join(result["errors"])
        self.assertIn("all task rows", joined)
        self.assertIn("acceptance AC-1 is not passed", joined)
        self.assertIn("aggregate evidence", joined)
        self.assertIn("passed integrated review", joined)

    def test_task_rows_reject_emoji_machine_state_and_long_form_id(self) -> None:
        change = self.create_change()
        tasks = change.path / "tasks.md"
        original = tasks.read_text(encoding="utf-8")
        tasks.write_text(original.replace("pending", "✅", 1), encoding="utf-8")
        with self.assertRaises(flow.FlowError) as emoji_error:
            flow.task_rows(tasks)
        self.assertIn("Unsupported machine task state", str(emoji_error.exception))

        tasks.write_text(original.replace("T-001", "T-REQ-2026-001-001"), encoding="utf-8")
        with self.assertRaises(flow.FlowError) as id_error:
            flow.task_rows(tasks)
        self.assertIn("T-NNN", str(id_error.exception))

    def test_task_rows_reject_non_task_id_inside_task_table(self) -> None:
        change = self.create_change()
        tasks = change.path / "tasks.md"
        text = tasks.read_text(encoding="utf-8")
        text = text.replace(
            "| `T-001` | 1 | pending | - | AC-1, BR-export-001 | Refine the approved plan |",
            "| `T-001` | 1 | pending | - | AC-1, BR-export-001 | Refine the approved plan |\n"
            "| `X-002` | 1 | pending | - | AC-1 | Unfinished required work |",
        )
        tasks.write_text(text, encoding="utf-8")

        with self.assertRaises(flow.FlowError) as caught:
            flow.task_rows(tasks)

        self.assertIn("T-NNN", str(caught.exception))

    def test_readiness_requires_resolvable_approval(self) -> None:
        change = self.ready_change()
        text, metadata = flow.read_metadata(change.proposal)
        metadata["approval"] = None
        change.proposal.write_text(flow.replace_metadata(text, metadata), encoding="utf-8")
        (change.path / "request.md").unlink()

        result = flow.validate_change(
            flow.find_change(self.root, "add-export", active_only=True), readiness=True  # type: ignore[arg-type]
        )

        self.assertFalse(result["ok"])
        self.assertTrue(any("approval authority" in item for item in result["errors"]))

    def test_removed_behavior_requires_task_and_evidence_traceability(self) -> None:
        self.write(
            "openspec/specs/export/spec.md",
            flow.product_spec_header("export")
            + "\n### Requirement `BR-export-099`: Legacy export\n"
            + "The system SHALL support legacy export.\n\n"
            + "#### Scenario `SC-export-099`: Legacy path\n"
            + "- **WHEN** legacy export is requested\n- **THEN** it succeeds\n",
        )
        change = self.ready_change()
        (change.path / "specs/export/spec.md").write_text(
            "# Delta Spec: export\n\n## REMOVED Requirements\n\n"
            "### Requirement `BR-export-099`: Legacy export\n\n"
            "**Reason**: The legacy contract is retired.\n\n"
            "**Migration**: Consumers use the current export contract.\n",
            encoding="utf-8",
        )

        result = flow.validate_change(
            flow.find_change(self.root, "add-export", active_only=True), readiness=True  # type: ignore[arg-type]
        )

        self.assertFalse(result["ok"])
        joined = "\n".join(result["errors"])
        self.assertIn("BR-export-099", joined)

    def test_revision_rejects_symbolic_git_reference(self) -> None:
        with mock.patch.object(flow, "git_commit_exists", return_value=True):
            self.assertFalse(flow.revision_resolves("HEAD", self.root))
            self.assertFalse(flow.revision_resolves("develop", self.root))
            self.assertTrue(flow.revision_resolves("a" * 40, self.root))

    def test_revision_rejects_single_file_hash_without_exact_scope(self) -> None:
        change = self.ready_change()
        evidence = change.path / "evidence/check.txt"
        value = f"sha256:{flow.sha256_file(evidence)}@{evidence.relative_to(self.root).as_posix()}"
        text, metadata = flow.read_metadata(change.proposal)
        metadata["affected_code"] = ["src/*.py"]
        change.proposal.write_text(flow.replace_metadata(text, metadata), encoding="utf-8")
        refreshed = flow.find_change(self.root, "add-export", active_only=True)
        self.assertFalse(flow.revision_resolves(value, self.root, refreshed))

    def test_revision_capture_requires_deterministic_observed_scope(self) -> None:
        change = self.ready_change()
        capture = change.path / "evidence/revision-capture.json"
        with mock.patch.object(flow, "git_head_oid", return_value="a" * 40), \
             mock.patch.object(flow, "git_changed_paths", return_value=["src/export.py"]), \
             mock.patch.object(flow, "git_path_exists_at", return_value=False), \
             mock.patch.object(flow, "git_commit_exists", return_value=True):
            payload = flow.revision_capture_payload(
                self.root, change, capture.relative_to(self.root).as_posix()
            )
        capture.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
        value = f"sha256:{flow.sha256_file(capture)}@{capture.relative_to(self.root).as_posix()}"
        refreshed = flow.find_change(self.root, "add-export", active_only=True)
        with mock.patch.object(flow, "git_head_oid", return_value="a" * 40), \
             mock.patch.object(flow, "git_changed_paths", return_value=["src/export.py"]), \
             mock.patch.object(flow, "git_path_exists_at", return_value=False), \
             mock.patch.object(flow, "git_commit_exists", return_value=True):
            self.assertTrue(flow.revision_resolves(value, self.root, refreshed))
        capture.write_text(capture.read_text(encoding="utf-8").replace("scoped-dirty", "dirty"), encoding="utf-8")
        with mock.patch.object(flow, "git_head_oid", return_value="a" * 40), \
             mock.patch.object(flow, "git_changed_paths", return_value=["src/export.py"]), \
             mock.patch.object(flow, "git_path_exists_at", return_value=False), \
             mock.patch.object(flow, "git_commit_exists", return_value=True):
            self.assertFalse(flow.revision_resolves(value, self.root, refreshed))

    def test_close_dry_run_is_non_mutating(self) -> None:
        change = self.ready_change()
        before = {path: path.read_bytes() for path in change.path.rglob("*") if path.is_file()}

        payload, exit_code = flow.run_close(self.root, namespace(identifier="add-export", dry_run=True))

        self.assertEqual(exit_code, 0, payload)
        self.assertTrue(payload["dry_run"])
        self.assertFalse((self.root / "openspec/specs/export/spec.md").exists())
        self.assertEqual(before, {path: path.read_bytes() for path in change.path.rglob("*") if path.is_file()})

    def test_close_dry_run_does_not_recover_existing_journal(self) -> None:
        change = self.ready_change()
        evidence = change.path / "evidence/check.txt"
        original = evidence.read_bytes()
        evidence.write_text("mutated after interrupted close\n", encoding="utf-8")
        journal = {
            "schema_version": 1,
            "backups": {
                evidence.relative_to(self.root).as_posix(): flow.base64.b64encode(original).decode("ascii")
            },
        }
        journal_path = change.path / flow.JOURNAL
        journal_path.write_text(json.dumps(journal), encoding="utf-8")
        before = {path: path.read_bytes() for path in change.path.rglob("*") if path.is_file()}

        with self.assertRaises(flow.FlowError) as caught:
            flow.run_close(self.root, namespace(identifier="add-export", dry_run=True))

        self.assertIn("dry-run will not mutate", str(caught.exception))
        self.assertEqual(before, {path: path.read_bytes() for path in change.path.rglob("*") if path.is_file()})

    def test_close_merges_retains_summary_and_is_idempotent(self) -> None:
        change = self.ready_change()
        temporary_review = self.write(
            "openspec/changes/add-export/review-security.md", "resolved temporary review\n"
        )
        text, metadata = flow.read_metadata(change.proposal)
        metadata["ephemeral_artifacts"] = ["review-security.md"]
        change.proposal.write_text(flow.replace_metadata(text, metadata), encoding="utf-8")

        payload, exit_code = flow.run_close(self.root, namespace(identifier="add-export", dry_run=False))

        self.assertEqual(exit_code, 0, payload)
        archive = self.root / payload["archive"]
        self.assertTrue(archive.is_dir())
        self.assertFalse(temporary_review.exists())
        self.assertFalse((archive / "review-security.md").exists())
        self.assertTrue((archive / "verification.md").is_file())
        current = self.root / "openspec/specs/export/spec.md"
        self.assertIn("BR-export-001", current.read_text(encoding="utf-8"))
        spec_meta = flow.metadata_from_text(current.read_text(encoding="utf-8"), "spec")
        self.assertEqual(spec_meta["id"], "SPEC-export")
        archived_meta = flow.read_metadata(archive / "proposal.md")[1]
        self.assertEqual(archived_meta["status"], "done")
        self.assertTrue(flow.valid_iso(archived_meta["archived_at"]))
        archived_proposal = (archive / "proposal.md").read_text(encoding="utf-8")
        self.assertIn("- [x] `AC-1`", archived_proposal)
        self.assertIn("Close completed; requirement archived.", archived_proposal)
        archived_prefix = archive.relative_to(self.root).as_posix()
        self.assertEqual(archived_meta["approval"]["ref"], f"{archived_prefix}/request.md")
        task_meta = flow.read_metadata(archive / "tasks.md")[1]
        self.assertEqual(task_meta["status"], "completed")
        self.assertTrue(task_meta["verified_against"].startswith("sha256:"))
        self.assertEqual(task_meta["sources"], [f"{archived_prefix}/**"])
        verification_meta = flow.read_metadata(archive / "verification.md")[1]
        self.assertEqual(verification_meta["sources"], [f"{archived_prefix}/**"])
        self.assertEqual(
            verification_meta["evidence"][0]["ref"],
            f"{archived_prefix}/evidence/check.txt",
        )
        self.assertEqual(
            verification_meta["acceptance"][0]["evidence"][0]["ref"],
            f"{archived_prefix}/evidence/check.txt",
        )
        self.assertTrue(
            verification_meta["verified_against"].endswith(
                "@src/export.py"
            )
        )
        second, second_exit = flow.run_close(self.root, namespace(identifier="add-export", dry_run=False))
        self.assertEqual(second_exit, 0, second)
        self.assertTrue(second["idempotent"])

    def test_compliance_retention_keeps_registered_ephemeral_file(self) -> None:
        change = self.ready_change()
        self.write("openspec/changes/add-export/review-security.md", "audit pack\n")
        text, metadata = flow.read_metadata(change.proposal)
        metadata["retention"] = "compliance"
        metadata["ephemeral_artifacts"] = ["review-security.md"]
        change.proposal.write_text(flow.replace_metadata(text, metadata), encoding="utf-8")

        payload, exit_code = flow.run_close(self.root, namespace(identifier="add-export", dry_run=False))

        self.assertEqual(exit_code, 0, payload)
        self.assertTrue((self.root / payload["archive"] / "review-security.md").is_file())

    def test_minimal_retention_removes_only_registered_ephemeral_file(self) -> None:
        change = self.ready_change()
        self.write("openspec/changes/add-export/remove-me.txt", "temporary\n")
        kept = self.write("openspec/changes/add-export/keep-me.txt", "not registered\n")
        text, metadata = flow.read_metadata(change.proposal)
        metadata["retention"] = "minimal"
        metadata["ephemeral_artifacts"] = ["remove-me.txt"]
        change.proposal.write_text(flow.replace_metadata(text, metadata), encoding="utf-8")

        payload, exit_code = flow.run_close(self.root, namespace(identifier="add-export", dry_run=False))

        self.assertEqual(exit_code, 0, payload)
        archive = self.root / payload["archive"]
        self.assertFalse((archive / "remove-me.txt").exists())
        self.assertTrue((archive / kept.name).is_file())

    def test_retention_rejects_referenced_ephemeral_evidence(self) -> None:
        change = self.ready_change()
        text, metadata = flow.read_metadata(change.proposal)
        metadata["ephemeral_artifacts"] = ["evidence/check.txt"]
        change.proposal.write_text(flow.replace_metadata(text, metadata), encoding="utf-8")

        result = flow.validate_change(
            flow.find_change(self.root, "add-export", active_only=True), readiness=True  # type: ignore[arg-type]
        )

        self.assertFalse(result["ok"])
        self.assertTrue(any("referenced artifact" in item for item in result["errors"]))

    def test_waiver_requires_evidence_reason_and_authority(self) -> None:
        change = self.ready_change()
        path = change.path / "verification.md"
        text, metadata = flow.read_metadata(path)
        metadata["acceptance"][0] = {
            "id": "AC-1", "status": "waived", "methods": [], "evidence": [],
            "reason": "Approved exception", "authority": {"kind": "request-record", "ref": "openspec/changes/add-export/request.md"},
        }
        path.write_text(flow.replace_metadata(text, metadata), encoding="utf-8")

        result = flow.validate_change(flow.find_change(self.root, "add-export", active_only=True), readiness=True)  # type: ignore[arg-type]

        self.assertFalse(result["ok"])
        self.assertTrue(any("waived acceptance AC-1" in item for item in result["errors"]))

    def test_close_refuses_spec_changed_since_intake(self) -> None:
        self.write(
            "openspec/specs/export/spec.md",
            flow.product_spec_header("export") + "\n",
        )
        change = self.ready_change()
        current = self.root / "openspec/specs/export/spec.md"
        current.write_text(current.read_text(encoding="utf-8") + "external change\n", encoding="utf-8")

        with self.assertRaises(flow.FlowError) as caught:
            flow.run_close(self.root, namespace(identifier="add-export", dry_run=False))

        self.assertIn("changed since intake", str(caught.exception))
        self.assertTrue(change.path.is_dir())

    def test_close_rejects_non_directory_specs_root_before_mutation(self) -> None:
        change = self.ready_change()
        specs_root = self.root / "openspec/specs"
        specs_root.write_text("not a directory\n", encoding="utf-8")

        with self.assertRaises(flow.FlowError) as caught:
            flow.run_close(self.root, namespace(identifier="add-export", dry_run=False))

        self.assertIn("Current spec parent is not a directory", str(caught.exception))
        self.assertTrue(change.path.is_dir())
        self.assertEqual(specs_root.read_text(encoding="utf-8"), "not a directory\n")

    @unittest.skipUnless(os.name == "nt", "Windows junction behavior")
    def test_close_rejects_spec_domain_junction_before_external_mutation(self) -> None:
        change = self.ready_change()
        outside = self.root / "outside-spec-domain"
        outside.mkdir()
        sentinel = outside / "sentinel.txt"
        sentinel.write_text("keep", encoding="utf-8")
        specs_root = self.root / "openspec/specs"
        specs_root.mkdir()
        domain = specs_root / "export"
        result = os.system(f'cmd /c mklink /J "{domain}" "{outside}" >nul')
        self.assertEqual(result, 0)

        with self.assertRaises(flow.FlowError) as caught:
            flow.run_close(self.root, namespace(identifier="add-export", dry_run=False))

        self.assertIn("Current spec path cannot traverse", str(caught.exception))
        self.assertTrue(change.path.is_dir())
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")
        self.assertFalse((outside / "spec.md").exists())

    @unittest.skipUnless(os.name == "nt", "Windows symlink behavior")
    def test_close_rejects_spec_file_symlink_before_external_mutation(self) -> None:
        change = self.ready_change()
        specs_root = self.root / "openspec/specs/export"
        specs_root.mkdir(parents=True)
        outside = self.root / "outside-spec.md"
        outside.write_text("keep", encoding="utf-8")
        target = specs_root / "spec.md"
        result = os.system(f'cmd /c mklink "{target}" "{outside}" >nul')
        if result != 0:
            self.skipTest("file symlinks are unavailable")

        with self.assertRaises(flow.FlowError) as caught:
            flow.run_close(self.root, namespace(identifier="add-export", dry_run=False))

        self.assertIn("Current spec path cannot traverse", str(caught.exception))
        self.assertTrue(change.path.is_dir())
        self.assertEqual(outside.read_text(encoding="utf-8"), "keep")

    def test_close_rolls_back_spec_metadata_and_retention_when_move_fails(self) -> None:
        change = self.ready_change()
        temporary_review = self.write(
            "openspec/changes/add-export/review-security.md", "temporary\n"
        )
        proposal_before = change.proposal.read_bytes()
        verification_before = (change.path / "verification.md").read_bytes()
        text, metadata = flow.read_metadata(change.proposal)
        metadata["ephemeral_artifacts"] = ["review-security.md"]
        change.proposal.write_text(flow.replace_metadata(text, metadata), encoding="utf-8")
        proposal_before = change.proposal.read_bytes()
        real_replace = os.replace

        def fail_directory_move(source: object, destination: object) -> None:
            if Path(source) == change.path:
                raise OSError("simulated archive move failure")
            real_replace(source, destination)

        with mock.patch("scripts.dev_spec_flow.os.replace", fail_directory_move):
            with self.assertRaises(OSError):
                flow.run_close(self.root, namespace(identifier="add-export", dry_run=False))

        self.assertTrue(change.path.is_dir())
        self.assertEqual(change.proposal.read_bytes(), proposal_before)
        self.assertEqual((change.path / "verification.md").read_bytes(), verification_before)
        self.assertTrue(temporary_review.is_file())
        self.assertFalse((self.root / "openspec/specs/export/spec.md").exists())
        self.assertFalse((change.path / flow.JOURNAL).exists())

    def test_close_rolls_back_when_post_move_validation_fails(self) -> None:
        change = self.ready_change()
        temporary_review = self.write(
            "openspec/changes/add-export/review-security.md", "temporary\n"
        )
        text, metadata = flow.read_metadata(change.proposal)
        metadata["ephemeral_artifacts"] = ["review-security.md"]
        change.proposal.write_text(flow.replace_metadata(text, metadata), encoding="utf-8")
        proposal_before = change.proposal.read_bytes()
        verification_before = (change.path / "verification.md").read_bytes()

        with mock.patch.object(
            flow,
            "validate_archived_result",
            return_value=["simulated post-move validation failure"],
        ):
            with self.assertRaises(flow.FlowError) as caught:
                flow.run_close(self.root, namespace(identifier="add-export", dry_run=False))

        self.assertIn("Post-close validation failed", str(caught.exception))
        self.assertTrue(change.path.is_dir())
        self.assertEqual(change.proposal.read_bytes(), proposal_before)
        self.assertEqual((change.path / "verification.md").read_bytes(), verification_before)
        self.assertTrue(temporary_review.is_file())
        self.assertFalse((self.root / "openspec/specs/export/spec.md").exists())
        self.assertFalse((change.path / flow.JOURNAL).exists())
        archive_root = self.root / "openspec/changes/archive"
        self.assertFalse(archive_root.exists() and any(archive_root.iterdir()))

    def test_atomic_file_transaction_rolls_back_on_second_replace(self) -> None:
        first = self.write("one.txt", "old one")
        second = self.write("two.txt", "old two")
        real_replace = os.replace
        replacements = 0

        def fail_second(source: object, destination: object) -> None:
            nonlocal replacements
            replacements += 1
            if replacements == 2:
                raise OSError("simulated replacement failure")
            real_replace(source, destination)

        with mock.patch("scripts.dev_spec_flow.os.replace", fail_second):
            with self.assertRaises(OSError):
                flow.apply_file_transaction({first: b"new one", second: b"new two"})

        self.assertEqual(first.read_text(encoding="utf-8"), "old one")
        self.assertEqual(second.read_text(encoding="utf-8"), "old two")

    def test_ephemeral_registry_rejects_durable_and_escaping_paths(self) -> None:
        change = self.create_change()
        text, metadata = flow.read_metadata(change.proposal)
        metadata["ephemeral_artifacts"] = ["proposal.md", "../outside.md"]
        change.proposal.write_text(flow.replace_metadata(text, metadata), encoding="utf-8")
        refreshed = flow.find_change(self.root, "add-export", active_only=True)
        errors = flow.validate_ephemeral(refreshed)  # type: ignore[arg-type]
        self.assertTrue(any("durable" in item for item in errors))
        self.assertTrue(any("unsafe" in item for item in errors))

    def test_archive_reference_rewrite_is_prefix_bounded(self) -> None:
        value = {
            "owned": "openspec/changes/add-export/evidence/a.txt#L1",
            "root": "openspec/changes/add-export",
            "sibling": "openspec/changes/add-export-extra/evidence/a.txt",
            "prose": "See openspec/changes/add-export/evidence/a.txt",
            "external": "https://example.com/openspec/changes/add-export",
            "revision": "sha256:" + "a" * 64 + "@openspec/changes/add-export/evidence/a.txt",
        }
        rewritten = flow.rewrite_archived_references(
            value,
            "openspec/changes/add-export",
            "openspec/changes/archive/2026-08-13-req-2026-001-add-export",
        )
        self.assertEqual(
            rewritten["owned"],
            "openspec/changes/archive/2026-08-13-req-2026-001-add-export/evidence/a.txt#L1",
        )
        self.assertEqual(
            rewritten["root"],
            "openspec/changes/archive/2026-08-13-req-2026-001-add-export",
        )
        self.assertEqual(rewritten["sibling"], value["sibling"])
        self.assertEqual(rewritten["prose"], value["prose"])
        self.assertEqual(rewritten["external"], value["external"])
        self.assertEqual(
            rewritten["revision"],
            "sha256:" + "a" * 64 + "@openspec/changes/archive/2026-08-13-req-2026-001-add-export/evidence/a.txt",
        )

    def test_status_normalizes_timezone_before_sorting(self) -> None:
        first = self.create_change("first-change")
        second = self.create_change("second-change")
        text, metadata = flow.read_metadata(first.proposal)
        metadata["created_at"] = "2026-01-01T01:00:00+08:00"  # 2025-12-31 17:00Z
        first.proposal.write_text(flow.replace_metadata(text, metadata), encoding="utf-8")
        text, metadata = flow.read_metadata(second.proposal)
        metadata["created_at"] = "2025-12-31T18:00:00+00:00"
        second.proposal.write_text(flow.replace_metadata(text, metadata), encoding="utf-8")

        payload, exit_code = flow.run_status(self.root, namespace())

        self.assertEqual(exit_code, 0, payload)
        self.assertEqual([item["slug"] for item in payload["changes"]], ["first-change", "second-change"])

    def test_partial_archive_is_not_accepted_as_idempotent(self) -> None:
        change = self.ready_change()
        archive = self.root / "openspec/changes/archive/2026-08-13-partial"
        archive.parent.mkdir(parents=True, exist_ok=True)
        os.replace(change.path, archive)

        with self.assertRaises(flow.FlowError) as caught:
            flow.run_close(self.root, namespace(identifier="add-export", dry_run=False))

        self.assertIn("Archived change is incomplete", str(caught.exception))

    def test_corrupt_archived_acceptance_is_not_accepted_as_idempotent(self) -> None:
        change = self.ready_change()
        payload, exit_code = flow.run_close(
            self.root, namespace(identifier="add-export", dry_run=False)
        )
        self.assertEqual(exit_code, 0, payload)
        proposal_path = self.root / payload["archive"] / "proposal.md"
        text, metadata = flow.read_metadata(proposal_path)
        metadata["acceptance"][0]["evidence"] = []
        proposal_path.write_text(flow.replace_metadata(text, metadata), encoding="utf-8")

        with self.assertRaises(flow.FlowError) as caught:
            flow.run_close(self.root, namespace(identifier="add-export", dry_run=False))

        self.assertIn("Archived change is incomplete", str(caught.exception))

    def test_archive_root_file_is_rejected_before_close_mutation(self) -> None:
        change = self.ready_change()
        archive_root = self.root / "openspec/changes/archive"
        archive_root.write_text("not a directory\n", encoding="utf-8")

        with self.assertRaises(flow.FlowError) as caught:
            flow.run_close(self.root, namespace(identifier="add-export", dry_run=False))

        self.assertIn("Archive root is not a directory", str(caught.exception))
        self.assertTrue(change.path.is_dir())
        self.assertFalse((self.root / "openspec/specs/export/spec.md").exists())

    @unittest.skipUnless(os.name == "nt", "Windows junction behavior")
    def test_active_change_junction_is_rejected_without_external_mutation(self) -> None:
        change = self.ready_change()
        outside = self.root / "outside-change"
        os.replace(change.path, outside)
        result = os.system(f'cmd /c mklink /J "{change.path}" "{outside}" >nul')
        self.assertEqual(result, 0)
        proposal_before = (outside / "proposal.md").read_bytes()

        with self.assertRaises(flow.FlowError):
            flow.run_close(self.root, namespace(identifier="add-export", dry_run=False))

        self.assertEqual((outside / "proposal.md").read_bytes(), proposal_before)

    @unittest.skipUnless(os.name == "nt", "Windows junction behavior")
    def test_archived_change_junction_is_not_accepted_as_idempotent(self) -> None:
        change = self.ready_change()
        outside = self.root / "outside-archive"
        os.replace(change.path, outside)
        archive = self.root / "openspec/changes/archive/2026-08-13-external"
        archive.parent.mkdir(parents=True, exist_ok=True)
        result = os.system(f'cmd /c mklink /J "{archive}" "{outside}" >nul')
        self.assertEqual(result, 0)

        with self.assertRaises(flow.FlowError):
            flow.run_close(self.root, namespace(identifier="add-export", dry_run=False))

    @unittest.skipUnless(os.name == "nt", "Windows junction behavior")
    def test_archive_root_junction_is_rejected_without_external_mutation(self) -> None:
        change = self.ready_change()
        outside = self.root / "outside-archive-root"
        outside.mkdir()
        archive_root = self.root / "openspec/changes/archive"
        result = os.system(f'cmd /c mklink /J "{archive_root}" "{outside}" >nul')
        self.assertEqual(result, 0)

        with self.assertRaises(flow.FlowError) as caught:
            flow.run_close(self.root, namespace(identifier="add-export", dry_run=False))

        self.assertIn("Archive root cannot be a symlink or junction", str(caught.exception))
        self.assertTrue(change.path.is_dir())
        self.assertEqual(list(outside.iterdir()), [])
        self.assertFalse((self.root / "openspec/specs/export/spec.md").exists())


class PackageInstallTests(FlowTestCase):
    def make_skill(self, files: dict[str, str], version: str = "1.0.0") -> Path:
        skill = self.root / "skill"
        for relative, content in files.items():
            path = skill / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        manifest = {
            "schema_version": 1,
            "package": "dev-spec-flow",
            "version": version,
            "files": {relative: flow.sha256_file(skill / relative) for relative in files},
        }
        (skill / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        return skill

    def install_args(self, destination: Path) -> argparse.Namespace:
        return namespace(target="codex", scope="user", dest=str(destination))

    def make_directory_link(self, link: Path, target: Path) -> None:
        """Create a directory symlink, falling back to a Windows junction."""
        try:
            os.symlink(target, link, target_is_directory=True)
        except (OSError, NotImplementedError):
            if os.name != "nt":
                self.skipTest("directory symlinks are unavailable")
            result = os.system(f'cmd /c mklink /J "{link}" "{target}" >nul')
            if result != 0:
                self.skipTest("directory junctions are unavailable")
        self.assertTrue(flow.path_is_linklike(link))

    def test_manifest_validation_detects_hash_drift(self) -> None:
        skill = self.make_skill({"SKILL.md": "original", "scripts/dev_spec_flow.py": "tool"})
        errors, _, _ = flow.package_validation(skill)
        self.assertEqual(errors, [])
        (skill / "SKILL.md").write_text("modified", encoding="utf-8")
        errors, _, _ = flow.package_validation(skill)
        self.assertTrue(any("hash mismatch" in item for item in errors))

    def test_manifest_requires_package_identity_and_version(self) -> None:
        skill = self.make_skill({"SKILL.md": "skill"})
        manifest_path = skill / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["package"] = "other"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaises(flow.FlowError):
            flow.parse_package_manifest(skill)

        manifest["package"] = "dev-spec-flow"
        manifest["version"] = ""
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaises(flow.FlowError):
            flow.parse_package_manifest(skill)

    def test_install_and_update_replace_only_unmodified_managed_files(self) -> None:
        skill = self.make_skill({"SKILL.md": "version one", "scripts/dev_spec_flow.py": "tool one"})
        destination = self.root / "installed"
        fake_script = skill / "scripts/dev_spec_flow.py"
        with mock.patch.object(flow, "__file__", str(fake_script)):
            installed, install_exit = flow.run_install(self.root, self.install_args(destination))
        self.assertEqual(install_exit, 0, installed)
        self.assertEqual((destination / "SKILL.md").read_text(encoding="utf-8"), "version one")

        (skill / "SKILL.md").write_text("version two", encoding="utf-8")
        manifest = json.loads((skill / "manifest.json").read_text(encoding="utf-8"))
        manifest["version"] = "2.0.0"
        manifest["files"]["SKILL.md"] = flow.sha256_file(skill / "SKILL.md")
        (skill / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        with mock.patch.object(flow, "__file__", str(fake_script)):
            updated, update_exit = flow.run_update(self.root, self.install_args(destination))
        self.assertEqual(update_exit, 0, updated)
        self.assertEqual((destination / "SKILL.md").read_text(encoding="utf-8"), "version two")

    def test_update_preserves_and_reports_local_modification(self) -> None:
        skill = self.make_skill({"SKILL.md": "version one", "scripts/dev_spec_flow.py": "tool one"})
        destination = self.root / "installed"
        fake_script = skill / "scripts/dev_spec_flow.py"
        with mock.patch.object(flow, "__file__", str(fake_script)):
            flow.run_install(self.root, self.install_args(destination))
        (destination / "SKILL.md").write_text("my local customization", encoding="utf-8")
        (skill / "SKILL.md").write_text("upstream version two", encoding="utf-8")
        manifest = json.loads((skill / "manifest.json").read_text(encoding="utf-8"))
        manifest["version"] = "2.0.0"
        manifest["files"]["SKILL.md"] = flow.sha256_file(skill / "SKILL.md")
        (skill / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

        with mock.patch.object(flow, "__file__", str(fake_script)):
            payload, exit_code = flow.run_update(self.root, self.install_args(destination))

        self.assertEqual(exit_code, 1, payload)
        self.assertIn("SKILL.md", payload["conflicts"])
        self.assertEqual((destination / "SKILL.md").read_text(encoding="utf-8"), "my local customization")

    def test_update_removes_only_unchanged_retired_managed_file(self) -> None:
        skill = self.make_skill({"SKILL.md": "skill", "templates/old.md": "old", "scripts/dev_spec_flow.py": "tool"})
        destination = self.root / "installed"
        fake_script = skill / "scripts/dev_spec_flow.py"
        with mock.patch.object(flow, "__file__", str(fake_script)):
            flow.run_install(self.root, self.install_args(destination))
        (skill / "templates/old.md").unlink()
        manifest = json.loads((skill / "manifest.json").read_text(encoding="utf-8"))
        del manifest["files"]["templates/old.md"]
        manifest["version"] = "2.0.0"
        (skill / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

        with mock.patch.object(flow, "__file__", str(fake_script)):
            payload, exit_code = flow.run_update(self.root, self.install_args(destination))

        self.assertEqual(exit_code, 0, payload)
        self.assertFalse((destination / "templates/old.md").exists())

    def test_update_rejects_forged_record_paths_before_deletion(self) -> None:
        skill = self.make_skill(
            {
                "SKILL.md": "skill",
                "templates/old.md": "old",
                "scripts/dev_spec_flow.py": "tool",
            }
        )
        destination = self.root / "installed"
        fake_script = skill / "scripts/dev_spec_flow.py"
        with mock.patch.object(flow, "__file__", str(fake_script)):
            flow.run_install(self.root, self.install_args(destination))

        user_file = destination / "templates/user-owned.md"
        user_file.write_text("keep me", encoding="utf-8")
        (skill / "templates/old.md").unlink()
        manifest = json.loads((skill / "manifest.json").read_text(encoding="utf-8"))
        del manifest["files"]["templates/old.md"]
        manifest["version"] = "2.0.0"
        (skill / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

        record_path = destination / flow.INSTALL_RECORD
        record = json.loads(record_path.read_text(encoding="utf-8"))
        record["files"]["templates/user-owned.md"] = flow.sha256_file(user_file)
        record_path.write_text(json.dumps(record), encoding="utf-8")

        with mock.patch.object(flow, "__file__", str(fake_script)):
            with self.assertRaises(flow.FlowError):
                flow.run_update(self.root, self.install_args(destination))

        self.assertTrue((destination / "templates/old.md").exists())
        self.assertTrue(user_file.exists())

    def test_update_rejects_forged_historical_manifest_before_deletion(self) -> None:
        skill = self.make_skill(
            {
                "SKILL.md": "skill",
                "templates/old.md": "old",
                "scripts/dev_spec_flow.py": "tool",
            }
        )
        destination = self.root / "installed"
        fake_script = skill / "scripts/dev_spec_flow.py"
        with mock.patch.object(flow, "__file__", str(fake_script)):
            flow.run_install(self.root, self.install_args(destination))

        user_file = destination / "templates/user-owned.md"
        user_file.write_text("keep me", encoding="utf-8")
        installed_manifest_path = destination / flow.PACKAGE_MANIFEST
        installed_manifest = json.loads(installed_manifest_path.read_text(encoding="utf-8"))
        installed_manifest["files"]["templates/user-owned.md"] = flow.sha256_file(user_file)
        installed_manifest_path.write_text(json.dumps(installed_manifest), encoding="utf-8")
        (skill / "templates/old.md").unlink()
        manifest = json.loads((skill / "manifest.json").read_text(encoding="utf-8"))
        del manifest["files"]["templates/old.md"]
        manifest["version"] = "2.0.0"
        (skill / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

        with mock.patch.object(flow, "__file__", str(fake_script)):
            with self.assertRaises(flow.FlowError):
                flow.run_update(self.root, self.install_args(destination))

        self.assertTrue((destination / "templates/old.md").exists())
        self.assertTrue(user_file.exists())

    def test_install_rejects_linklike_destination_before_writing(self) -> None:
        skill = self.make_skill({"SKILL.md": "skill", "scripts/dev_spec_flow.py": "tool"})
        outside = self.root / "outside"
        outside.mkdir()
        sentinel = outside / "sentinel.txt"
        sentinel.write_text("keep", encoding="utf-8")
        destination = self.root / "linked-install"
        self.make_directory_link(destination, outside)

        fake_script = skill / "scripts/dev_spec_flow.py"
        with mock.patch.object(flow, "__file__", str(fake_script)):
            with self.assertRaises(flow.FlowError):
                flow.run_install(self.root, self.install_args(destination))

        self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")
        self.assertFalse((outside / "SKILL.md").exists())

    def test_install_rejects_linklike_parent_before_creating_missing_destination(self) -> None:
        skill = self.make_skill({"SKILL.md": "skill", "scripts/dev_spec_flow.py": "tool"})
        outside = self.root / "outside-parent"
        outside.mkdir()
        linked_parent = self.root / "linked-parent"
        self.make_directory_link(linked_parent, outside)
        destination = linked_parent / "new-install"

        fake_script = skill / "scripts/dev_spec_flow.py"
        with mock.patch.object(flow, "__file__", str(fake_script)):
            with self.assertRaises(flow.FlowError):
                flow.run_install(self.root, self.install_args(destination))

        self.assertFalse((outside / "new-install").exists())
        self.assertFalse(destination.exists())

    def test_update_rejects_linklike_destination_before_writing_or_deleting(self) -> None:
        skill = self.make_skill(
            {
                "SKILL.md": "skill",
                "templates/old.md": "old",
                "scripts/dev_spec_flow.py": "tool",
            }
        )
        destination = self.root / "installed"
        fake_script = skill / "scripts/dev_spec_flow.py"
        with mock.patch.object(flow, "__file__", str(fake_script)):
            flow.run_install(self.root, self.install_args(destination))

        outside = self.root / "outside-installed"
        os.replace(destination, outside)
        self.make_directory_link(destination, outside)
        (skill / "templates/old.md").unlink()
        manifest = json.loads((skill / "manifest.json").read_text(encoding="utf-8"))
        del manifest["files"]["templates/old.md"]
        manifest["version"] = "2.0.0"
        (skill / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

        with mock.patch.object(flow, "__file__", str(fake_script)):
            with self.assertRaises(flow.FlowError):
                flow.run_update(self.root, self.install_args(destination))

        self.assertTrue((outside / "templates/old.md").exists())

    def test_install_rejects_grok_without_explicit_destination(self) -> None:
        with self.assertRaises(flow.FlowError):
            flow.installation_destination(self.root, "grok", "user", None)


class CliTests(FlowTestCase):
    def test_parser_accepts_root_before_or_after_subcommand(self) -> None:
        parser = flow.build_parser()
        before = parser.parse_args(["--root", str(self.root), "status"])
        after = parser.parse_args(["status", "--root", str(self.root)])
        self.assertEqual(before.root, self.root)
        self.assertEqual(after.root, self.root)

    def test_json_error_contract(self) -> None:
        with mock.patch("builtins.print") as printer:
            exit_code = flow.main(["--root", str(self.root), "--json", "close", "missing"])
        self.assertEqual(exit_code, 1)
        payload = json.loads(printer.call_args.args[0])
        self.assertFalse(payload["ok"])
        self.assertIn("not found", payload["errors"][0])


if __name__ == "__main__":
    unittest.main()
