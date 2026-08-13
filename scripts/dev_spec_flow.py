#!/usr/bin/env python3
"""Manage dev-spec-flow changes and safely distribute the canonical Skill.

The tool deliberately uses only Python's standard library.  Markdown prose remains
human-owned; this module automates only identities, lifecycle metadata, structural
checks, stable-ID delta merging, close/archive transactions, and managed installs.
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import fnmatch
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Iterable, Sequence


METADATA_RE = re.compile(
    r"<!--\s*docs-architect-meta\s*(\{.*?\})\s*-->", re.DOTALL
)
REQ_HEADING_RE = re.compile(
    r"^### Requirement\s+`(?P<id>BR-[A-Za-z0-9][A-Za-z0-9-]*)`:\s*(?P<title>\S.*)$",
    re.MULTILINE,
)
SCENARIO_HEADING_RE = re.compile(
    r"^#### Scenario\s+`(?P<id>SC-[A-Za-z0-9][A-Za-z0-9-]*)`:\s*(?P<title>\S.*)$",
    re.MULTILINE,
)
DELTA_SECTION_RE = re.compile(
    r"^## (ADDED|MODIFIED|REMOVED|RENAMED) Requirements\s*$", re.MULTILINE
)
TASK_ID_RE = re.compile(r"^T-\d{3,}$")
REQ_ID_RE = re.compile(r"^REQ-(\d{4})-(\d{3,})$")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
WINDOWS_RESERVED = {
    "AUX", "CLOCK$", "CON", "NUL", "PRN",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}
REQUIRED_TIMES = ("created_at", "updated_at", "status_changed_at")
COMPLEXITIES = {"small", "medium", "large"}
RISK_LEVELS = {"low", "medium", "high", "critical"}
RETENTIONS = {"minimal", "summary", "compliance"}
TASK_STATES = {"pending", "ready", "in_progress", "blocked", "completed", "cancelled"}
FINAL_TASK_STATES = {"completed", "cancelled"}
EVIDENCE_RESULTS = {"pending", "passed", "failed", "waived", "deferred"}
EVIDENCE_METHODS = {"existing-test", "automated", "command", "runtime", "inspection", "screenshot"}
EVIDENCE_KINDS = {"test", "command", "log", "screenshot", "pull-request", "commit", "release", "document", "other"}
AUTHORITY_KINDS = {"commit", "document", "issue-state", "pull-request", "request-record"}
PROPOSAL_ACCEPTANCE_STATES = {"pending", "passed", "failed", "not_applicable"}
REVIEW_STATES = {"pending", "passed", "failed"}
REQUIRED_RISK_REVIEWS = {"security-privacy": "security/privacy"}
CAPTURED_OBSERVATION_KINDS = {"command", "log", "screenshot", "document"}
DOCS_OPERATIONS = {"impact", "check", "index"}
PACKAGE_OWNED_ROOTS = {"SKILL.md", "manifest.json", "scripts", "references", "templates", "adapters", "agents"}
REQUIREMENT_STATES = {
    "intake", "clarifying", "accepted", "planned", "in_progress", "verifying",
    "documented", "done", "deferred", "rejected", "superseded",
}
APPROVED_REQUIREMENT_STATES = {
    "accepted", "planned", "in_progress", "verifying", "documented", "done",
}
PACKAGE_MANIFEST = "manifest.json"
INSTALL_RECORD = ".dev-spec-flow-install.json"
JOURNAL = ".dev-spec-flow-close.json"
REVISION_CAPTURE_KIND = "dev-spec-flow-revision-capture"
PACKAGE_SCHEMA = 1
CHANGE_SCHEMA = 1


class FlowError(Exception):
    """Expected validation or safety failure."""


@dataclass(frozen=True)
class Clause:
    clause_id: str
    title: str
    text: str


@dataclass
class Delta:
    added: list[Clause]
    modified: list[Clause]
    removed: list[Clause]
    renamed: list[tuple[str, str, str]]
    scenario_ids: list[str]


@dataclass
class Change:
    path: Path
    proposal: Path
    metadata: dict[str, Any]


def now_iso() -> str:
    return dt.datetime.now().astimezone().replace(microsecond=0).isoformat()


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def normalize_relative(value: str) -> str:
    value = value.replace("\\", "/")
    while value.startswith("./"):
        value = value[2:]
    return value


def safe_relative(value: str) -> bool:
    if not isinstance(value, str) or not value:
        return False
    normalized = normalize_relative(value)
    win = PureWindowsPath(value)
    if PurePosixPath(normalized).is_absolute() or win.anchor or win.drive:
        return False
    parts = normalized.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        return False
    for part in parts:
        if part.endswith((".", " ")) or ":" in part:
            return False
        if part.split(".", 1)[0].upper() in WINDOWS_RESERVED:
            return False
    return True


def within(root: Path, relative: str) -> Path:
    if not safe_relative(relative):
        raise FlowError(f"Unsafe repository-relative path: {relative!r}")
    root = root.resolve()
    current = root
    for part in PurePosixPath(normalize_relative(relative)).parts:
        current = current / part
        try:
            linklike = current.is_symlink() or (
                hasattr(current, "is_junction") and current.is_junction()
            )
        except OSError:
            linklike = True
        if linklike:
            raise FlowError(f"Path traverses a symlink or junction: {relative!r}")
        if not current.exists():
            break
    result = (root / normalize_relative(relative)).resolve()
    try:
        result.relative_to(root)
    except ValueError as exc:
        raise FlowError(f"Path escapes root: {relative!r}") from exc
    return result


def path_is_linklike(path: Path) -> bool:
    try:
        if path.is_symlink() or (
            hasattr(path, "is_junction") and path.is_junction()
        ):
            return True
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
        return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))
    except FileNotFoundError:
        return False
    except OSError:
        return True


def require_real_directory(path: Path, label: str) -> None:
    if path_is_linklike(path):
        raise FlowError(f"{label} cannot be a symlink or junction: {path}")


def repository_root_for_change(change: Change) -> Path:
    for candidate in (change.path, *change.path.parents):
        if candidate.name == "openspec":
            return candidate.parent
    raise FlowError(f"Change is not under an openspec directory: {change.path}")


def valid_iso(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def parse_iso(value: str) -> dt.datetime:
    """Return an aware ISO timestamp normalized for reliable comparisons."""
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(dt.timezone.utc)


def git_commit_exists(root: Path, reference: str) -> bool:
    try:
        process = subprocess.run(
            ["git", "cat-file", "-t", reference], cwd=root,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
            text=True,
        )
    except OSError:
        return False
    return process.returncode == 0 and process.stdout.strip() == "commit"


def immutable_git_commit_resolves(root: Path, reference: Any) -> bool:
    return (
        isinstance(reference, str)
        and re.fullmatch(r"(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})", reference) is not None
        and git_commit_exists(root, reference)
    )


def https_reference(value: str) -> bool:
    return value.startswith("https://") and len(value) > len("https://")


def repository_reference_path(reference: str) -> str:
    return reference.split("::", 1)[0].split("#", 1)[0]


def evidence_reference_resolves(item: dict[str, Any], root: Path) -> bool:
    kind = item["kind"]
    reference = item["ref"].strip()
    if kind == "commit":
        return immutable_git_commit_resolves(root, reference)
    if kind == "release":
        return reference.lower() not in {"head", "latest", "main", "master", "develop"}
    if https_reference(reference):
        return True
    if kind == "pull-request":
        return False
    path_reference = repository_reference_path(reference)
    if not safe_relative(path_reference):
        return False
    try:
        return within(root, path_reference).is_file()
    except FlowError:
        return False


def valid_evidence_item(item: Any, root: Path) -> bool:
    return (
        isinstance(item, dict)
        and item.get("kind") in EVIDENCE_KINDS
        and isinstance(item.get("ref"), str) and bool(item["ref"].strip())
        and isinstance(item.get("description"), str) and bool(item["description"].strip())
        and evidence_reference_resolves(item, root)
    )


def captured_observation(item: Any, root: Path, change: Change) -> bool:
    """Return whether an evidence item points to a locally captured observation.

    A source test, commit, or arbitrary repository file can be useful supporting
    context, but it cannot prove that a command or review was actually observed.
    Captures are deliberately constrained to regular files under the change's
    evidence directory so a readiness check cannot be satisfied by a source stub.
    """
    if not valid_evidence_item(item, root) or item.get("kind") not in CAPTURED_OBSERVATION_KINDS:
        return False
    reference = item.get("ref")
    if not isinstance(reference, str) or not reference.strip():
        return False
    if any(token in reference for token in ("#", "::")):
        return False
    path_reference = repository_reference_path(reference)
    if path_reference != reference or not safe_relative(path_reference):
        return False
    try:
        path = within(root, path_reference)
        evidence_root = (change.path / "evidence").resolve()
        path.relative_to(evidence_root)
    except (FlowError, ValueError):
        return False
    return path.is_file() and not path_is_linklike(path)


def _read_local_json_capture(item: Any, root: Path, change: Change) -> dict[str, Any] | None:
    if not captured_observation(item, root, change):
        return None
    try:
        path = within(root, item["ref"])
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FlowError, OSError, UnicodeError, json.JSONDecodeError, KeyError):
        return None
    return value if isinstance(value, dict) else None


def docs_architect_capture(
    item: Any, root: Path, change: Change, operation: str
) -> bool:
    """Validate one captured docs-architect operation result."""
    if operation not in DOCS_OPERATIONS or not isinstance(item, dict):
        return False
    if item.get("operation") != operation or item.get("kind") not in {"command", "log"}:
        return False
    payload = _read_local_json_capture(item, root, change)
    if payload is None or payload.get("ok") is not True:
        return False
    if operation == "impact":
        return all(isinstance(payload.get(key), list) for key in ("changed_files", "affected_documents", "findings"))
    if operation == "check":
        summary = payload.get("summary")
        return isinstance(summary, dict) and summary.get("errors") == 0
    return (
        payload.get("write") is True
        and isinstance(payload.get("files"), dict)
        and isinstance(payload.get("findings"), list)
    )


def authority_resolves(authority: Any, root: Path) -> bool:
    if not isinstance(authority, dict) or authority.get("kind") not in AUTHORITY_KINDS:
        return False
    reference = authority.get("ref")
    if not isinstance(reference, str) or not reference.strip():
        return False
    if authority["kind"] == "commit":
        return immutable_git_commit_resolves(root, reference)
    if authority["kind"] in {"issue-state", "pull-request"}:
        return https_reference(reference)
    path_reference = reference.split("#", 1)[0]
    return safe_relative(path_reference) and within(root, path_reference).is_file()


def git_head_oid(root: Path) -> str | None:
    try:
        process = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"], cwd=root,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
            text=True,
        )
    except OSError:
        return None
    value = process.stdout.strip()
    return value.lower() if process.returncode == 0 and re.fullmatch(r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}", value) else None


def git_changed_paths(root: Path, base_commit: str) -> list[str] | None:
    """Return the current worktree delta from HEAD without rename ambiguity."""
    if git_head_oid(root) != base_commit.lower():
        return None
    commands = (
        ["git", "diff", "--name-only", "-z", "--no-renames", base_commit, "--"],
        ["git", "ls-files", "--others", "--exclude-standard", "-z", "--"],
    )
    changed: set[str] = set()
    for command in commands:
        try:
            process = subprocess.run(
                command, cwd=root, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, check=False,
            )
        except OSError:
            return None
        if process.returncode != 0:
            return None
        try:
            values = process.stdout.decode("utf-8", errors="strict").split("\0")
        except UnicodeError:
            return None
        for value in values:
            if not value:
                continue
            normalized = normalize_relative(value)
            if not safe_relative(normalized):
                return None
            changed.add(normalized)
    return sorted(changed)


def path_matches_scope(path: str, pattern: str) -> bool:
    path = normalize_relative(path)
    pattern = normalize_relative(pattern)
    if pattern.endswith("/**"):
        prefix = pattern[:-3].rstrip("/")
        return path == prefix or path.startswith(prefix + "/")
    return fnmatch.fnmatchcase(path, pattern)


def capture_scope(change: Change) -> list[str] | None:
    scope = change.metadata.get("affected_code")
    if not isinstance(scope, list) or not scope:
        return None
    normalized: list[str] = []
    for pattern in scope:
        if not isinstance(pattern, str) or not safe_relative(pattern):
            return None
        normalized.append(normalize_relative(pattern))
    return sorted(set(normalized)) if len(normalized) == len(set(normalized)) else None


def git_path_exists_at(root: Path, commit: str, relative: str) -> bool:
    try:
        process = subprocess.run(
            ["git", "cat-file", "-e", f"{commit}:{relative}"], cwd=root,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
        )
    except OSError:
        return False
    return process.returncode == 0


def revision_capture_payload(root: Path, change: Change, capture_relative: str) -> dict[str, Any]:
    """Build a deterministic capture of the change's declared implementation scope."""
    scope = capture_scope(change)
    base_commit = git_head_oid(root)
    if scope is None or base_commit is None:
        raise FlowError("Revision capture needs non-empty safe affected_code and a Git HEAD commit")
    changed = git_changed_paths(root, base_commit)
    if changed is None:
        raise FlowError("Cannot inspect the worktree against the current Git HEAD")
    scoped = sorted(
        path for path in changed
        if any(path_matches_scope(path, pattern) for pattern in scope)
    )
    if not scoped:
        raise FlowError("Revision capture scope contains no changed paths")
    if any(path_matches_scope(capture_relative, pattern) for pattern in scope):
        raise FlowError("Revision capture cannot include its own output path in affected_code")
    entries: list[dict[str, Any]] = []
    for relative in scoped:
        path = within(root, relative)
        if not path.exists():
            entries.append({"path": relative, "status": "deleted", "sha256": None})
            continue
        if path_is_linklike(path) or not path.is_file():
            raise FlowError(f"Revision capture path is not a regular file: {relative}")
        status = "modified" if git_path_exists_at(root, base_commit, relative) else "added"
        entries.append({"path": relative, "status": status, "sha256": sha256_file(path)})
    return {
        "schema_version": 1,
        "kind": REVISION_CAPTURE_KIND,
        "base_commit": base_commit,
        "scope": scope,
        "changed_paths": scoped,
        "worktree_state": "scoped-dirty",
        "entries": entries,
    }


def revision_capture_resolves(path: Path, root: Path, change: Change) -> bool:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or payload.get("kind") != REVISION_CAPTURE_KIND:
            return False
        base_commit = payload.get("base_commit")
        scope = payload.get("scope")
        changed_paths = payload.get("changed_paths")
        entries = payload.get("entries")
        if (
            payload.get("schema_version") != 1
            or
            not isinstance(base_commit, str)
            or not immutable_git_commit_resolves(root, base_commit)
            or not isinstance(scope, list)
            or not isinstance(changed_paths, list)
            or not isinstance(entries, list)
            or scope != capture_scope(change)
            or not changed_paths
            or changed_paths != sorted(changed_paths)
            or len(changed_paths) != len(set(changed_paths))
        ):
            return False
        if any(
            not isinstance(item, str) or not safe_relative(item)
            for item in [*scope, *changed_paths]
        ):
            return False
        if changed_paths != [entry.get("path") for entry in entries if isinstance(entry, dict)]:
            return False
        if any(
            not isinstance(entry, dict) or entry.get("path") != sorted(changed_paths)[index]
            for index, entry in enumerate(entries)
        ):
            return False
        for entry in entries:
            if not isinstance(entry, dict) or entry.get("status") not in {"added", "modified", "deleted"}:
                return False
            relative = entry.get("path")
            if not isinstance(relative, str) or not safe_relative(relative):
                return False
            if not any(path_matches_scope(relative, pattern) for pattern in scope):
                return False
            path_value = within(root, relative)
            if entry["status"] == "deleted":
                if (
                    entry.get("sha256") is not None
                    or path_value.exists()
                    or not git_path_exists_at(root, base_commit, relative)
                ):
                    return False
            else:
                expected_status = (
                    "modified" if git_path_exists_at(root, base_commit, relative) else "added"
                )
                if (
                    entry["status"] != expected_status
                    or not path_value.is_file()
                    or path_is_linklike(path_value)
                    or not isinstance(entry.get("sha256"), str)
                    or not SHA256_RE.fullmatch(entry["sha256"])
                    or sha256_file(path_value).lower() != entry["sha256"].lower()
                ):
                    return False
        # A post-close archive may be checked after HEAD advances; the captured
        # base still proves the observed implementation revision while hashes
        # prove that scoped files have not drifted.
        if payload.get("worktree_state") != "scoped-dirty":
            return False
        # While the repository is still at the capture's base commit, ensure
        # that no additional path entered the declared scope after capture.
        # Once Close creates a later commit, git_changed_paths() deliberately
        # returns None and the immutable base plus recorded hashes remain the
        # applicable anchor.
        current_changed = git_changed_paths(root, base_commit)
        if current_changed is not None:
            current_scoped = sorted(
                path for path in current_changed
                if any(path_matches_scope(path, pattern) for pattern in scope)
            )
            if current_scoped != changed_paths:
                return False
    except (FlowError, OSError, UnicodeError, json.JSONDecodeError, ValueError):
        return False
    return True


def revision_resolves(value: Any, root: Path, change: Change | None = None) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    if immutable_git_commit_resolves(root, value):
        return True
    match = re.fullmatch(r"sha256:([0-9a-fA-F]{64})@(.+)", value)
    if match is None or not safe_relative(match.group(2)):
        return False
    try:
        path = within(root, match.group(2))
    except FlowError:
        return False
    if not path.is_file() or path_is_linklike(path) or sha256_file(path).lower() != match.group(1).lower():
        return False
    if change is None:
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        payload = None
    if isinstance(payload, dict) and payload.get("kind") == REVISION_CAPTURE_KIND:
        try:
            path.relative_to((change.path / "evidence").resolve())
        except ValueError:
            return False
        return revision_capture_resolves(path, root, change)
    scope = capture_scope(change)
    if (
        scope is None
        or len(scope) != 1
        or any(character in scope[0] for character in "*?[")
        or normalize_relative(match.group(2)) != scope[0]
    ):
        return False
    # An exact, literal one-file scope plus a matching observed hash is the
    # narrow exception that does not need a repository-wide diff capture. When
    # Git is available, prove that no second path is dirty in that scope.
    head = git_head_oid(root)
    if head is None:
        return True
    changed = git_changed_paths(root, head)
    return changed is None or (
        scope[0] in changed
        and sum(1 for item in changed if path_matches_scope(item, scope[0])) == 1
    )


def metadata_from_text(text: str, source: str) -> dict[str, Any]:
    matches = METADATA_RE.findall(text)
    if len(matches) != 1:
        raise FlowError(f"{source} must contain exactly one docs-architect-meta object")
    try:
        value = json.loads(matches[0])
    except json.JSONDecodeError as exc:
        raise FlowError(f"Invalid metadata JSON in {source}: {exc}") from exc
    if not isinstance(value, dict):
        raise FlowError(f"Metadata in {source} must be a JSON object")
    return value


def read_metadata(path: Path) -> tuple[str, dict[str, Any]]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise FlowError(f"Cannot read {path}: {exc}") from exc
    return text, metadata_from_text(text, path.as_posix())


def metadata_comment(metadata: dict[str, Any]) -> str:
    encoded = json.dumps(metadata, ensure_ascii=False, separators=(",", ":"))
    return f"<!-- docs-architect-meta {encoded} -->"


def replace_metadata(text: str, metadata: dict[str, Any]) -> str:
    matches = list(METADATA_RE.finditer(text))
    if len(matches) != 1:
        raise FlowError("Managed Markdown must contain exactly one metadata object")
    match = matches[0]
    return text[: match.start()] + metadata_comment(metadata) + text[match.end() :]


def sync_proposal_prose(
    text: str, acceptance: list[dict[str, Any]], timestamp: str
) -> str:
    statuses = {
        item.get("id"): item.get("status")
        for item in acceptance
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    seen: set[str] = set()
    checklist = re.compile(
        r"^(?P<prefix>\s*-\s*)\[[ xX]\](?P<body>\s*`(?P<id>AC-[A-Za-z0-9-]+)`\s*-\s*.*)$",
        re.MULTILINE,
    )

    def replace_check(match: re.Match[str]) -> str:
        identifier = match.group("id")
        if identifier not in statuses:
            return match.group(0)
        seen.add(identifier)
        checked = statuses[identifier] in {"passed", "not_applicable"}
        return f"{match.group('prefix')}[{'x' if checked else ' '}]{match.group('body')}"

    result = checklist.sub(replace_check, text)
    missing = set(statuses) - seen
    if missing:
        raise FlowError(
            "proposal prose is missing acceptance checklist entries: "
            + ", ".join(sorted(missing))
        )

    history = re.search(r"^## History\s*$", result, re.MULTILINE)
    if history is None:
        raise FlowError("proposal prose is missing a History section")
    next_section = re.search(r"^## \S.*$", result[history.end() :], re.MULTILINE)
    section_end = (
        history.end() + next_section.start() if next_section is not None else len(result)
    )
    entry = f"- {timestamp} - Close completed; requirement archived."
    section = result[history.end() : section_end].rstrip()
    if entry not in section:
        section = f"{section}\n\n{entry}" if section else f"\n\n{entry}"
    return result[: history.end()] + section + "\n" + result[section_end:].lstrip("\n")


def atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def apply_file_transaction(writes: dict[Path, bytes], deletes: Iterable[Path] = ()) -> None:
    delete_paths = list(dict.fromkeys(deletes))
    all_paths = list(dict.fromkeys([*writes, *delete_paths]))
    originals: dict[Path, bytes | None] = {}
    for path in all_paths:
        if path.exists() and not path.is_file():
            raise FlowError(f"Transaction target is not a regular file: {path}")
        originals[path] = path.read_bytes() if path.exists() else None
    changed: list[Path] = []
    try:
        for path, content in writes.items():
            if originals[path] == content:
                continue
            atomic_write(path, content)
            changed.append(path)
        for path in delete_paths:
            if path.exists():
                path.unlink()
                changed.append(path)
    except BaseException:
        for path in reversed(changed):
            original = originals[path]
            if original is None:
                path.unlink(missing_ok=True)
            else:
                atomic_write(path, original)
        raise


def changes_root(root: Path) -> Path:
    return root / "openspec" / "changes"


def current_spec_path(root: Path, domain: str) -> Path:
    """Resolve a current-spec path without accepting redirected filesystem nodes."""
    relative = f"openspec/specs/{normalize_relative(domain)}/spec.md"
    if not safe_relative(relative):
        raise FlowError(f"Unsafe current spec path: {relative}")
    root = root.resolve()
    current = root
    parts = PurePosixPath(normalize_relative(relative)).parts
    for index, part in enumerate(parts):
        current = current / part
        if path_is_linklike(current):
            raise FlowError(f"Current spec path cannot traverse a symlink or junction: {relative}")
        if not current.exists():
            break
        if index < len(parts) - 1 and not current.is_dir():
            raise FlowError(f"Current spec parent is not a directory: {current}")
    target = root / normalize_relative(relative)
    resolved = target.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise FlowError(f"Current spec path escapes repository root: {relative}") from exc
    if target.exists() and not target.is_file():
        raise FlowError(f"Current spec target is not a regular file: {target}")
    return target


def validated_archive_root(root: Path) -> Path:
    """Return the archive root after rejecting redirection and non-directories."""
    archive = changes_root(root) / "archive"
    if path_is_linklike(archive):
        raise FlowError(f"Archive root cannot be a symlink or junction: {archive}")
    if archive.exists() and not archive.is_dir():
        raise FlowError(f"Archive root is not a directory: {archive}")
    return archive


def scan_changes(root: Path, include_archive: bool = True) -> list[Change]:
    base = changes_root(root)
    if not base.is_dir():
        return []
    require_real_directory(base, "Changes root")
    validated_archive_root(root)
    proposals: list[Path] = []
    for path in base.iterdir():
        if path.name.startswith(".") or not path.is_dir():
            continue
        require_real_directory(path, "Change directory")
        if path.name == "archive":
            for archived in sorted(path.iterdir()):
                if archived.name.startswith(".") or not archived.is_dir():
                    continue
                require_real_directory(archived, "Archived change directory")
                proposal = archived / "proposal.md"
                if proposal.is_file():
                    proposals.append(proposal)
            continue
        proposal = path / "proposal.md"
        if proposal.is_file():
            proposals.append(proposal)
    catalog: list[Change] = []
    for proposal in proposals:
        _, metadata = read_metadata(proposal)
        catalog.append(Change(proposal.parent, proposal, metadata))
    by_id: dict[str, list[Change]] = {}
    for change in catalog:
        identifier = change.metadata.get("id")
        if isinstance(identifier, str) and identifier.strip():
            by_id.setdefault(identifier, []).append(change)
    duplicates = {
        identifier: matches
        for identifier, matches in by_id.items()
        if len(matches) > 1
    }
    if duplicates:
        details = "; ".join(
            f"{identifier}: {', '.join(item.proposal.relative_to(root).as_posix() for item in matches)}"
            for identifier, matches in sorted(duplicates.items())
        )
        raise FlowError(f"Duplicate requirement IDs in change catalog: {details}")
    if include_archive:
        return catalog
    return [item for item in catalog if item.path.parent.name != "archive"]


def find_change(root: Path, identifier: str, active_only: bool = False) -> Change | None:
    matches = []
    for change in scan_changes(root, include_archive=not active_only):
        if identifier in {
            change.path.name,
            str(change.metadata.get("slug", "")),
            str(change.metadata.get("id", "")),
        }:
            matches.append(change)
    if len(matches) > 1:
        raise FlowError(f"Change identifier is ambiguous: {identifier}")
    return matches[0] if matches else None


def allocate_requirement_id(root: Path, timestamp: str) -> str:
    year = dt.datetime.fromisoformat(timestamp).year
    maximum = 0
    seen: set[str] = set()
    for change in scan_changes(root):
        identifier = change.metadata.get("id")
        if not isinstance(identifier, str):
            continue
        if identifier in seen:
            raise FlowError(f"Duplicate requirement ID already exists: {identifier}")
        seen.add(identifier)
        match = REQ_ID_RE.fullmatch(identifier)
        if match and int(match.group(1)) == year:
            maximum = max(maximum, int(match.group(2)))
    return f"REQ-{year}-{maximum + 1:03d}"


def lifecycle_metadata(
    requirement_id: str,
    slug: str,
    title: str,
    complexity: str,
    risk_level: str,
    risk_drivers: list[str],
    retention: str,
    timestamp: str,
    approved: bool,
    domains: list[str],
) -> dict[str, Any]:
    status = "accepted" if approved else "intake"
    approval = {"kind": "request-record", "ref": f"openspec/changes/{slug}/request.md"} if approved else None
    return {
        "schema_version": CHANGE_SCHEMA,
        "id": requirement_id,
        "type": "requirement",
        "title": title,
        "status": status,
        "owners": [],
        "origin": {"kind": "request", "ref": f"openspec/changes/{slug}/request.md"} if approved else None,
        "approval": approval,
        "sources": [],
        "update_when": ["Scope, acceptance, risk, implementation, evidence, or documentation disposition changes"],
        "relations": [],
        "dependencies": [],
        "acceptance": [{"id": "AC-1", "text": "TODO: state an observable result", "status": "pending", "evidence": []}],
        "evidence": [],
        "affected_code": [],
        "affected_docs": [],
        "open_questions": [],
        "documentation_disposition": "pending",
        "no_doc_change_scope": [],
        "no_doc_change_reason": None,
        "slug": slug,
        "complexity": complexity,
        "risk": {"level": risk_level, "drivers": risk_drivers},
        "retention": retention,
        "domains": domains,
        "spec_baselines": {},
        "ephemeral_artifacts": [],
        "created_at": timestamp,
        "updated_at": timestamp,
        "status_changed_at": timestamp,
        "completed_at": None,
        "archived_at": None,
        "status_history": [{"status": status, "at": timestamp, "reason": "Change created"}],
        "verified_at": None,
        "verified_against": None,
    }


def proposal_text(metadata: dict[str, Any]) -> str:
    identifier = metadata["id"]
    title = metadata["title"]
    return f"""{metadata_comment(metadata)}

# {identifier}: {title}

## Need

- TODO: explain the problem, affected users, and desired outcome.

## Scope

### In scope

- TODO

### Out of scope

- TODO

## Acceptance Criteria

- [ ] `AC-1` - TODO: state an observable result and mirror it in metadata.

## Documentation Disposition

- Pending impact analysis.

## History

- {metadata['created_at']} - Change created.
"""


def tasks_text(
    requirement_id: str,
    slug: str,
    title: str,
    timestamp: str,
    domains: list[str],
) -> str:
    behavior_ids = [
        f"BR-{re.sub(r'[^a-z0-9]+', '-', domain.lower()).strip('-') or 'domain'}-001"
        for domain in domains
    ]
    metadata = {
        "schema_version": 1,
        "id": f"PLAN-{requirement_id}",
        "type": "exec-plan",
        "title": f"Implement {title}",
        "status": "draft",
        "owners": [],
        "sources": [f"openspec/changes/{slug}/**"],
        "update_when": ["Implementation progress, discoveries, recovery, or verification changes"],
        "relations": [{"type": "implements", "target": requirement_id}],
        "cancellations": [],
        "evidence": [],
        "affected_docs": [],
        "verified_at": None,
        "verified_against": None,
    }
    return f"""{metadata_comment(metadata)}

# {metadata['id']}: {metadata['title']}

Resume an `in_progress` task first. Otherwise select the highest-priority task whose dependencies are completed.

| ID | Priority | Status | Depends on | Implements | Task |
|---|---:|---|---|---|---|
| `T-001` | 1 | pending | - | {', '.join(['AC-1', *behavior_ids])} | Refine the approved plan |

## Evidence plan

| Acceptance | Methods | Expected evidence |
|---|---|---|
| AC-1 | inspection | TODO |

## Progress

- {timestamp} - Plan created.

## Recovery

- Safe resume: use the task selection rule above.
"""


def verification_text(
    requirement_id: str,
    slug: str,
    title: str,
    timestamp: str,
    domains: list[str],
    risk_drivers: list[str] | None = None,
) -> str:
    validates = ["AC-1"]
    for domain in domains:
        prefix = re.sub(r"[^a-z0-9]+", "-", domain.lower()).strip("-") or "domain"
        validates.extend([f"BR-{prefix}-001", f"SC-{prefix}-001"])
    metadata = {
        "schema_version": 1,
        "id": f"EVID-{requirement_id}",
        "type": "evidence",
        "title": f"Verification for {title}",
        "status": "active",
        "owners": [],
        "sources": [f"openspec/changes/{slug}/**"],
        "update_when": ["Acceptance evidence or unresolved findings change"],
        "relations": [{"type": "validates", "target": requirement_id}],
        "acceptance": [{
            "id": "AC-1", "status": "pending", "validates": validates,
            "methods": [], "evidence": [], "reason": None, "authority": None,
        }],
        "evidence": [],
        "documentation_checks": [],
        "reviews": [
            {"charter": "integrated", "status": "pending", "evidence": []},
            *[
                {"charter": REQUIRED_RISK_REVIEWS[driver], "status": "pending", "evidence": []}
                for driver in dict.fromkeys(risk_drivers or [])
                if driver in REQUIRED_RISK_REVIEWS
            ],
        ],
        "unresolved_findings": [],
        "verified_at": None,
        "verified_against": None,
        "created_at": timestamp,
        "updated_at": timestamp,
        "completed_at": None,
    }
    return f"""{metadata_comment(metadata)}

# {metadata['id']}: {metadata['title']}

## Acceptance Evidence

Mirror every proposal acceptance ID in metadata. Use `passed`, `failed`, `waived`, `deferred`, or `pending` as `status`.

## Commands And Observations

- None recorded.

## Review Summary

- Unresolved findings: none recorded.
"""


def delta_template(domain: str) -> str:
    prefix = re.sub(r"[^a-z0-9]+", "-", domain.lower()).strip("-") or "domain"
    return f"""# Delta Spec: {domain}

## ADDED Requirements

### Requirement `BR-{prefix}-001`: TODO behavior
The system SHALL describe an observable behavior.

#### Scenario `SC-{prefix}-001`: TODO example
- **WHEN** an observable event occurs
- **THEN** the specified result occurs
"""


def run_new(root: Path, args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    slug = args.slug
    if not SLUG_RE.fullmatch(slug):
        raise FlowError("slug must be lower-case kebab-case")
    if find_change(root, slug) is not None:
        raise FlowError(f"Change already exists: {slug}")
    domains = list(dict.fromkeys(args.domain or []))
    if not domains or any(not SLUG_RE.fullmatch(domain) for domain in domains):
        raise FlowError("At least one lower-case kebab-case --domain is required")
    timestamp = now_iso()
    identifier = allocate_requirement_id(root, timestamp)
    metadata = lifecycle_metadata(
        identifier, slug, args.title, args.complexity, args.risk_level,
        list(dict.fromkeys(args.risk_driver or [])), args.retention, timestamp,
        args.approved, domains,
    )
    for domain in domains:
        current = current_spec_path(root, domain)
        metadata["spec_baselines"][domain] = sha256_file(current) if current.is_file() else None
    target = changes_root(root) / slug
    if target.exists():
        raise FlowError(f"Target path already exists: {target}")
    writes: dict[Path, bytes] = {
        target / "proposal.md": proposal_text(metadata).encode(),
        target / "tasks.md": tasks_text(identifier, slug, args.title, timestamp, domains).encode(),
        target / "verification.md": verification_text(
            identifier, slug, args.title, timestamp, domains,
            list(dict.fromkeys(args.risk_driver or [])),
        ).encode(),
    }
    for domain in domains:
        writes[target / "specs" / domain / "spec.md"] = delta_template(domain).encode()
    if args.approved:
        request = args.request or "User approved this change in the current request."
        writes[target / "request.md"] = (
            f"# Request record for {identifier}\n\n{request.strip()}\n"
        ).encode()
    try:
        apply_file_transaction(writes)
    except BaseException:
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
        raise
    return {
        "ok": True,
        "id": identifier,
        "slug": slug,
        "path": target.relative_to(root).as_posix(),
        "created_at": timestamp,
        "files": sorted(path.relative_to(root).as_posix() for path in writes),
    }, 0


def parse_clauses(text: str, source: str) -> tuple[list[Clause], list[str]]:
    malformed_headings = [
        line.strip() for line in text.splitlines()
        if re.match(r"^### Requirement\b", line) and not REQ_HEADING_RE.match(line)
    ]
    if malformed_headings:
        raise FlowError(f"{source} contains a requirement without a stable BR ID")
    matches = list(REQ_HEADING_RE.finditer(text))
    clauses: list[Clause] = []
    ids: set[str] = set()
    scenarios: list[str] = []
    section_boundaries = [match.start() for match in re.finditer(r"^##\s+", text, re.MULTILINE)]
    for index, match in enumerate(matches):
        candidates = [len(text)]
        if index + 1 < len(matches):
            candidates.append(matches[index + 1].start())
        candidates.extend(position for position in section_boundaries if position > match.start())
        end = min(candidates)
        block = text[match.start():end].strip()
        identifier = match.group("id")
        if identifier in ids:
            raise FlowError(f"Duplicate requirement ID {identifier} in {source}")
        ids.add(identifier)
        clauses.append(Clause(identifier, match.group("title").strip(), block))
        scenarios.extend(item.group("id") for item in SCENARIO_HEADING_RE.finditer(block))
    duplicates = sorted({item for item in scenarios if scenarios.count(item) > 1})
    if duplicates:
        raise FlowError(f"Duplicate scenario IDs in {source}: {', '.join(duplicates)}")
    return clauses, scenarios


def delta_section_for(position: int, sections: list[re.Match[str]]) -> str | None:
    current = None
    for match in sections:
        if match.start() >= position:
            break
        current = match.group(1)
    return current


def parse_delta(path: Path) -> Delta:
    text = path.read_text(encoding="utf-8")
    sections = list(DELTA_SECTION_RE.finditer(text))
    if not sections:
        raise FlowError(f"Delta has no ADDED/MODIFIED/REMOVED/RENAMED section: {path}")
    clauses, scenarios = parse_clauses(text, path.as_posix())
    grouped: dict[str, list[Clause]] = {name: [] for name in ("ADDED", "MODIFIED", "REMOVED")}
    for clause in clauses:
        position = text.find(clause.text)
        section = delta_section_for(position, sections)
        if section not in grouped:
            raise FlowError(f"Requirement {clause.clause_id} is not in a clause-bearing delta section")
        grouped[section].append(clause)
        if section in {"ADDED", "MODIFIED"} and not SCENARIO_HEADING_RE.search(clause.text):
            raise FlowError(f"{section} requirement {clause.clause_id} needs a stable SC scenario")
        if section == "REMOVED" and (
            not re.search(r"^\*\*Reason\*\*:\s*\S", clause.text, re.MULTILINE)
            or not re.search(r"^\*\*Migration\*\*:\s*\S", clause.text, re.MULTILINE)
        ):
            raise FlowError(f"REMOVED requirement {clause.clause_id} needs Reason and Migration")
    all_ids = [clause.clause_id for values in grouped.values() for clause in values]
    duplicates = sorted({item for item in all_ids if all_ids.count(item) > 1})
    if duplicates:
        raise FlowError(f"Requirement appears in multiple delta operations: {', '.join(duplicates)}")
    renamed: list[tuple[str, str, str]] = []
    for index, section in enumerate(sections):
        if section.group(1) != "RENAMED":
            continue
        end = sections[index + 1].start() if index + 1 < len(sections) else len(text)
        body = text[section.end():end]
        pairs = re.findall(
            r"^-\s*FROM:\s*`(BR-[A-Za-z0-9-]+)`\s+(.+?)\s*$\s*^-\s*TO:\s*`(BR-[A-Za-z0-9-]+)`\s+(.+?)\s*$",
            body,
            re.MULTILINE,
        )
        meaningful = [line for line in body.splitlines() if line.strip() and not line.lstrip().startswith(">")] 
        if meaningful and len(pairs) * 2 != len(meaningful):
            raise FlowError(f"Invalid RENAMED syntax in {path}")
        for old_id, old_title, new_id, new_title in pairs:
            if old_id != new_id:
                raise FlowError("RENAMED keeps the same stable BR ID")
            renamed.append((old_id, old_title.strip(), new_title.strip()))
    rename_ids = [item[0] for item in renamed]
    if len(rename_ids) != len(set(rename_ids)) or set(rename_ids) & set(all_ids):
        raise FlowError(f"Ambiguous rename operation in {path}")
    if not all_ids and not renamed:
        raise FlowError(f"Delta contains no requirement operation: {path}")
    return Delta(grouped["ADDED"], grouped["MODIFIED"], grouped["REMOVED"], renamed, scenarios)


def validate_proposal(change: Change) -> list[str]:
    metadata = change.metadata
    errors: list[str] = []
    for key in ("id", "type", "title", "status", "slug", "complexity", "risk", "retention", "status_history"):
        if key not in metadata:
            errors.append(f"proposal metadata is missing {key}")
    if metadata.get("type") != "requirement":
        errors.append("proposal type must be requirement")
    if metadata.get("status") not in REQUIREMENT_STATES:
        errors.append("proposal has an unsupported requirement status")
    if not isinstance(metadata.get("id"), str) or not REQ_ID_RE.fullmatch(metadata.get("id", "")):
        errors.append("proposal id must match REQ-YYYY-NNN")
    if metadata.get("slug") != change.path.name and change.path.parent.name != "archive":
        errors.append("proposal slug must match its active directory")
    if metadata.get("complexity") not in COMPLEXITIES:
        errors.append("unsupported complexity")
    risk = metadata.get("risk")
    if not isinstance(risk, dict) or risk.get("level") not in RISK_LEVELS or not isinstance(risk.get("drivers", []), list):
        errors.append("risk must contain an allowed level and drivers array")
    if metadata.get("retention") not in RETENTIONS:
        errors.append("retention must be minimal, summary, or compliance")
    if metadata.get("status") in APPROVED_REQUIREMENT_STATES:
        root = repository_root_for_change(change)
        if not authority_resolves(metadata.get("approval"), root):
            errors.append("accepted or later proposal status needs resolvable approval authority")
    timestamps: dict[str, dt.datetime] = {}
    for key in REQUIRED_TIMES:
        value = metadata.get(key)
        if not valid_iso(value):
            errors.append(f"{key} must be an ISO 8601 timestamp")
        else:
            timestamps[key] = parse_iso(value)
    if len(timestamps) == len(REQUIRED_TIMES) and not (
        timestamps["created_at"]
        <= timestamps["status_changed_at"]
        <= timestamps["updated_at"]
    ):
        errors.append("lifecycle timestamps must satisfy created_at <= status_changed_at <= updated_at")
    optional_times: dict[str, dt.datetime] = {}
    for key in ("completed_at", "archived_at"):
        if metadata.get(key) is not None and not valid_iso(metadata.get(key)):
            errors.append(f"{key} must be null or ISO 8601")
        elif metadata.get(key) is not None:
            optional_times[key] = parse_iso(metadata[key])
    if "archived_at" in optional_times and "completed_at" not in optional_times:
        errors.append("archived_at requires completed_at")
    if "completed_at" in optional_times and "created_at" in timestamps and (
        optional_times["completed_at"] < timestamps["created_at"]
        or optional_times["completed_at"] > timestamps.get("updated_at", optional_times["completed_at"])
    ):
        errors.append("completed_at must be between created_at and updated_at")
    if "archived_at" in optional_times and (
        optional_times["archived_at"] < optional_times["completed_at"]
        or optional_times["archived_at"] > timestamps.get("updated_at", optional_times["archived_at"])
    ):
        errors.append("archived_at must be between completed_at and updated_at")
    history = metadata.get("status_history")
    if not isinstance(history, list) or not history:
        errors.append("status_history must be a non-empty array")
    else:
        previous: dt.datetime | None = None
        for entry in history:
            if not isinstance(entry, dict) or not isinstance(entry.get("status"), str) or not valid_iso(entry.get("at")):
                errors.append("each status_history entry needs status and ISO timestamp")
                continue
            current = parse_iso(entry["at"])
            if previous and current < previous:
                errors.append("status_history must be chronological")
            if "created_at" in timestamps and current < timestamps["created_at"]:
                errors.append("status_history cannot predate created_at")
            if "updated_at" in timestamps and current > timestamps["updated_at"]:
                errors.append("status_history cannot be newer than updated_at")
            previous = current
        if history and isinstance(history[-1], dict) and history[-1].get("status") != metadata.get("status"):
            errors.append("latest status_history state must equal proposal status")
        if (
            history
            and isinstance(history[-1], dict)
            and valid_iso(history[-1].get("at"))
            and "status_changed_at" in timestamps
            and parse_iso(history[-1]["at"]) != timestamps["status_changed_at"]
        ):
            errors.append("status_changed_at must equal the latest status_history timestamp")
    acceptance = metadata.get("acceptance", [])
    if not isinstance(acceptance, list):
        errors.append("acceptance must be an array")
    elif not acceptance:
        errors.append("proposal needs at least one acceptance item")
    else:
        ids = []
        for item in acceptance:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item.get("text"):
                errors.append("each acceptance item needs id and text")
                continue
            ids.append(item["id"])
            if item.get("status") not in PROPOSAL_ACCEPTANCE_STATES:
                errors.append(f"invalid proposal acceptance status for {item['id']}")
        if len(ids) != len(set(ids)):
            errors.append("proposal acceptance IDs must be unique")
    ephemeral = metadata.get("ephemeral_artifacts", [])
    if not isinstance(ephemeral, list) or any(not isinstance(item, str) or not safe_relative(item) for item in ephemeral):
        errors.append("ephemeral_artifacts must contain safe relative paths")
    return errors


def task_rows(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise FlowError(f"Missing task plan: {path}")
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    def cells_for(line: str) -> list[str] | None:
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            return None
        return [cell.strip().strip("`") for cell in stripped[1:-1].split("|")]

    expected_header = ["id", "priority", "status", "depends on", "implements", "task"]
    headers = [
        index for index, line in enumerate(lines)
        if (cells := cells_for(line)) is not None
        and [cell.lower() for cell in cells] == expected_header
    ]
    if len(headers) != 1:
        raise FlowError(f"Task plan must contain exactly one six-column task table: {path}")
    header = headers[0]
    if header + 1 >= len(lines):
        raise FlowError("Task table is missing its separator row")
    separators = cells_for(lines[header + 1])
    if (
        separators is None
        or len(separators) != len(expected_header)
        or any(re.fullmatch(r":?-{3,}:?", cell) is None for cell in separators)
    ):
        raise FlowError("Task table has an invalid separator row")

    rows = []
    index = header + 2
    while index < len(lines) and lines[index].lstrip().startswith("|"):
        cells = cells_for(lines[index])
        if cells is None or len(cells) != len(expected_header):
            raise FlowError(f"Malformed task table row at line {index + 1}")
        identifier = cells[0]
        if not TASK_ID_RE.fullmatch(identifier):
            raise FlowError(f"Task IDs must use change-local T-NNN form: {identifier}")
        dependencies = [] if cells[3] in {"", "-"} else [item.strip().strip("`") for item in cells[3].split(",")]
        implements = (
            [] if cells[4] in {"", "-"}
            else [item.strip().strip("`") for item in cells[4].split(",")]
        )
        rows.append({
            "id": identifier, "priority": cells[1], "status": cells[2].lower(),
            "dependencies": dependencies, "implements": implements,
        })
        index += 1
    if not rows:
        raise FlowError(f"No stable task rows found in {path}")
    ids = [row["id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise FlowError("Task IDs must be unique")
    invalid_states = [row for row in rows if row["status"] not in TASK_STATES]
    if invalid_states:
        raise FlowError(
            "Unsupported machine task state: "
            + ", ".join(f"{row['id']}={row['status']}" for row in invalid_states)
        )
    known = set(ids)
    for row in rows:
        missing = set(row["dependencies"]) - known
        if missing:
            raise FlowError(f"Task {row['id']} has missing dependencies: {', '.join(sorted(missing))}")
    visiting: set[str] = set()
    visited: set[str] = set()
    graph = {row["id"]: row["dependencies"] for row in rows}
    def visit(identifier: str) -> None:
        if identifier in visiting:
            raise FlowError("Task dependency graph contains a cycle")
        if identifier in visited:
            return
        visiting.add(identifier)
        for dependency in graph[identifier]:
            visit(dependency)
        visiting.remove(identifier)
        visited.add(identifier)
    for identifier in graph:
        visit(identifier)
    return rows


def verification_state(change: Change) -> tuple[dict[str, Any], list[str]]:
    path = change.path / "verification.md"
    if not path.is_file():
        raise FlowError(f"Missing verification manifest: {path}")
    _, metadata = read_metadata(path)
    root = repository_root_for_change(change)
    errors: list[str] = []
    if metadata.get("type") != "evidence":
        errors.append("verification metadata type must be evidence")
    if metadata.get("status") not in {"draft", "active", "completed"}:
        errors.append("verification status must be draft, active, or completed")
    top_evidence = metadata.get("evidence", [])
    if not isinstance(top_evidence, list):
        errors.append("verification evidence must be an array")
    elif any(not valid_evidence_item(item, root) for item in top_evidence):
        errors.append("verification has invalid or unresolved top-level evidence")
    items = metadata.get("acceptance", [])
    if not isinstance(items, list):
        errors.append("verification acceptance must be an array")
        items = []
    ids: list[str] = []
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            errors.append("each verification acceptance item needs an id")
            continue
        identifier = item["id"]
        ids.append(identifier)
        validates = item.get("validates", [])
        if (
            not isinstance(validates, list)
            or any(not isinstance(target, str) or not target.strip() for target in validates)
        ):
            errors.append(f"acceptance {identifier} validates must be an array of stable IDs")
        result = item.get("status", item.get("result"))
        if result not in EVIDENCE_RESULTS:
            errors.append(f"invalid evidence result for {identifier}")
        evidence = item.get("evidence", [])
        if not isinstance(evidence, list):
            errors.append(f"evidence for {identifier} must be an array")
            evidence = []
        elif any(not valid_evidence_item(evidence_item, root) for evidence_item in evidence):
            errors.append(f"acceptance {identifier} has invalid or unresolved evidence")
        methods = item.get("methods", [])
        if not isinstance(methods, list) or any(method not in EVIDENCE_METHODS for method in methods):
            errors.append(f"acceptance {identifier} has invalid evidence methods")
        elif result in {"passed", "waived"} and not methods:
            errors.append(f"completed acceptance {identifier} needs an evidence method")
        if result == "passed" and not evidence:
            errors.append(f"passed acceptance {identifier} needs evidence")
        if result == "waived" and (
            not evidence
            or not isinstance(item.get("reason"), str) or not item["reason"].strip()
            or not authority_resolves(item.get("authority"), root)
        ):
            errors.append(f"waived acceptance {identifier} needs evidence, reason, and resolvable authority")
    if len(ids) != len(set(ids)):
        errors.append("verification acceptance IDs must be unique")
    if "unresolved_findings" not in metadata:
        errors.append("verification metadata must declare unresolved_findings")
    unresolved = metadata.get("unresolved_findings", [])
    if not isinstance(unresolved, list):
        errors.append("unresolved_findings must be an array")
    documentation_checks = metadata.get("documentation_checks", [])
    if not isinstance(documentation_checks, list):
        errors.append("documentation_checks must be an array")
    elif any(not valid_evidence_item(item, root) for item in documentation_checks):
        errors.append("documentation_checks has invalid or unresolved evidence")
    reviews = metadata.get("reviews", [])
    if not isinstance(reviews, list) or not reviews:
        errors.append("verification metadata must declare at least one structured review")
    else:
        charters: list[str] = []
        for review in reviews:
            if (
                not isinstance(review, dict)
                or not isinstance(review.get("charter"), str)
                or not review["charter"].strip()
            ):
                errors.append("each review needs a non-empty charter")
                continue
            charter = review["charter"].strip()
            charters.append(charter)
            if review.get("status") not in REVIEW_STATES:
                errors.append(f"review {charter} has an invalid status")
            evidence = review.get("evidence", [])
            if not isinstance(evidence, list) or any(
                not valid_evidence_item(item, root) for item in evidence
            ):
                errors.append(f"review {charter} has invalid or unresolved evidence")
            elif review.get("status") == "passed" and not evidence:
                errors.append(f"passed review {charter} needs evidence")
        if len(charters) != len(set(charters)):
            errors.append("review charters must be unique")
    return metadata, errors


def pattern_has_match(root: Path, pattern: str) -> bool:
    if not safe_relative(pattern):
        return False
    if any(character in pattern for character in "*?["):
        try:
            return any(True for _ in root.glob(normalize_relative(pattern)))
        except (OSError, ValueError):
            return False
    try:
        return within(root, pattern).exists()
    except FlowError:
        return False


def patterns_overlap(left: str, right: str) -> bool:
    left = normalize_relative(left)
    right = normalize_relative(right)
    return (
        left == right
        or fnmatch.fnmatchcase(left, right)
        or fnmatch.fnmatchcase(right, left)
    )


def validate_documentation_readiness(
    root: Path, change: Change, verification: dict[str, Any]
) -> list[str]:
    if not (root / ".docs-architect.json").is_file():
        return []
    errors: list[str] = []
    checks = verification.get("documentation_checks", [])
    if not isinstance(checks, list):
        checks = []
    for operation in sorted(DOCS_OPERATIONS):
        if not any(docs_architect_capture(item, root, change, operation) for item in checks):
            errors.append(f"docs-architect integration needs a successful captured {operation} result")
    disposition = change.metadata.get("documentation_disposition")
    affected_docs = change.metadata.get("affected_docs", [])
    if disposition == "updated":
        if not isinstance(affected_docs, list) or not affected_docs:
            errors.append("updated documentation disposition needs affected_docs")
            affected_docs = []
        governed: list[dict[str, Any]] = []
        for relative in affected_docs:
            if not isinstance(relative, str) or not safe_relative(relative):
                errors.append(f"unsafe affected documentation path: {relative!r}")
                continue
            try:
                path = within(root, relative)
            except FlowError as exc:
                errors.append(str(exc))
                continue
            if not path.is_file():
                errors.append(f"affected documentation does not exist: {relative}")
                continue
            try:
                _, metadata = read_metadata(path)
            except FlowError:
                continue
            if metadata.get("type") == "system-doc" and metadata.get("status") == "active":
                governed.append(metadata)
        requirement_id = change.metadata.get("id")
        affected_code = change.metadata.get("affected_code", [])
        qualifying = False
        for metadata in governed:
            relations = metadata.get("relations", [])
            sources = metadata.get("sources", [])
            documents_requirement = isinstance(relations, list) and any(
                isinstance(relation, dict)
                and relation.get("type") == "documents"
                and relation.get("target") == requirement_id
                for relation in relations
            )
            source_overlap = (
                isinstance(sources, list)
                and isinstance(affected_code, list)
                and any(
                    isinstance(source, str) and isinstance(code, str)
                    and patterns_overlap(source, code)
                    for source in sources for code in affected_code
                )
            )
            qualifying = qualifying or documents_requirement or source_overlap
        if not qualifying:
            errors.append(
                "updated documentation disposition needs an active governed system-doc "
                "that documents the requirement or overlaps affected code"
            )
    elif disposition == "no_change_required":
        if affected_docs:
            errors.append("no_change_required documentation disposition needs empty affected_docs")
        scopes = change.metadata.get("no_doc_change_scope", [])
        if (
            not isinstance(scopes, list) or not scopes
            or any(not isinstance(scope, str) or not pattern_has_match(root, scope) for scope in scopes)
        ):
            errors.append("no_change_required needs a non-empty existing reviewed scope")
        reason = change.metadata.get("no_doc_change_reason")
        if (
            not isinstance(reason, str) or len(reason.strip()) < 12
            or reason.strip().lower() in {"none", "n/a", "not applicable", "todo"}
        ):
            errors.append("no_change_required needs a concrete reason")
        top = verification.get("evidence", [])
        if not isinstance(top, list) or not any(
            isinstance(item, dict)
            and item.get("kind") in {"command", "log", "document"}
            and valid_evidence_item(item, root)
            for item in top
        ):
            errors.append("no_change_required needs captured review evidence")
    else:
        errors.append("docs-architect is enabled but documentation disposition is pending")
    return errors


def delta_files(change: Change) -> list[Path]:
    base = change.path / "specs"
    return sorted(base.glob("**/spec.md")) if base.is_dir() else []


def validate_change(change: Change, readiness: bool = False) -> dict[str, Any]:
    # Re-read the proposal so callers cannot validate stale metadata after an
    # external edit (the CLI always scans fresh, but library callers may not).
    _, current_metadata = read_metadata(change.proposal)
    change = Change(change.path, change.proposal, current_metadata)
    errors = validate_proposal(change)
    warnings: list[str] = []
    deltas: dict[str, Delta] = {}
    seen_br: set[str] = set()
    seen_sc: set[str] = set()
    files = delta_files(change)
    if not files:
        errors.append("change has no delta spec files")
    for path in files:
        domain = path.relative_to(change.path / "specs").parent.as_posix()
        try:
            delta = parse_delta(path)
            deltas[domain] = delta
            identifiers = [clause.clause_id for group in (delta.added, delta.modified, delta.removed) for clause in group] + [item[0] for item in delta.renamed]
            overlap = seen_br & set(identifiers)
            if overlap:
                errors.append(f"BR IDs occur in multiple delta files: {', '.join(sorted(overlap))}")
            seen_br.update(identifiers)
            overlap_sc = seen_sc & set(delta.scenario_ids)
            if overlap_sc:
                errors.append(f"SC IDs occur in multiple delta files: {', '.join(sorted(overlap_sc))}")
            seen_sc.update(delta.scenario_ids)
        except (FlowError, OSError, UnicodeError) as exc:
            errors.append(str(exc))
    try:
        tasks = task_rows(change.path / "tasks.md")
        _, tasks_metadata = read_metadata(change.path / "tasks.md")
    except FlowError as exc:
        errors.append(str(exc))
        tasks = []
        tasks_metadata = {}
    try:
        verification, verification_errors = verification_state(change)
        errors.extend(verification_errors)
    except FlowError as exc:
        errors.append(str(exc))
        verification = {}
    baselines = change.metadata.get("spec_baselines")
    if not isinstance(baselines, dict):
        warnings.append("spec_baselines is absent; concurrent spec changes cannot be detected")
        baselines = {}
    root = repository_root_for_change(change)
    for domain in deltas:
        if domain not in baselines:
            warnings.append(f"no baseline hash recorded for domain {domain}")
            continue
        try:
            current = current_spec_path(root, domain)
        except FlowError as exc:
            errors.append(str(exc))
            continue
        actual = sha256_file(current) if current.is_file() else None
        if baselines[domain] != actual:
            errors.append(f"current spec changed since intake for domain {domain}")
    if readiness:
        for required_path in (change.proposal, change.path / "tasks.md", change.path / "verification.md"):
            if required_path.is_file() and re.search(r"(?i)(?:<TODO|\bTODO\b)", required_path.read_text(encoding="utf-8")):
                errors.append(f"required artifact still contains TODO placeholders: {required_path.name}")
        if change.metadata.get("status") not in {"accepted", "planned", "in_progress", "verifying", "documented"}:
            errors.append("proposal is not in a closable working state")
        if change.metadata.get("open_questions"):
            errors.append("proposal has unresolved open questions")
        if any(row["status"] not in FINAL_TASK_STATES for row in tasks):
            errors.append("all task rows must be completed before close")
        cancellations = tasks_metadata.get("cancellations", [])
        if not isinstance(cancellations, list):
            errors.append("task cancellations must be an array")
            cancellations = []
        cancellation_by_id = {
            item.get("id"): item for item in cancellations
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        }
        for row in tasks:
            if row["status"] != "cancelled":
                continue
            disposition = cancellation_by_id.get(row["id"])
            if (
                not isinstance(disposition, dict)
                or not isinstance(disposition.get("reason"), str)
                or not disposition["reason"].strip()
                or not authority_resolves(disposition.get("authority"), root)
            ):
                errors.append(
                    f"cancelled task {row['id']} needs a reason and resolvable authority"
                )
        proposal_acceptance = change.metadata.get("acceptance", [])
        expected = {item.get("id") for item in proposal_acceptance if isinstance(item, dict)}
        evidence_items = {
            item.get("id"): item for item in verification.get("acceptance", []) if isinstance(item, dict)
        }
        missing = expected - set(evidence_items)
        extra = set(evidence_items) - expected
        if missing:
            errors.append(f"acceptance IDs missing verification: {', '.join(sorted(str(item) for item in missing))}")
        if extra:
            errors.append(f"verification has unknown acceptance IDs: {', '.join(sorted(str(item) for item in extra))}")
        for identifier in sorted(expected & set(evidence_items)):
            if evidence_items[identifier].get("status", evidence_items[identifier].get("result")) not in {"passed", "waived"}:
                errors.append(f"acceptance {identifier} is not passed or waived")
            elif evidence_items[identifier].get("status", evidence_items[identifier].get("result")) == "passed":
                observations = evidence_items[identifier].get("evidence", [])
                if not any(captured_observation(item, root, change) for item in observations):
                    errors.append(f"acceptance {identifier} needs a captured observation under the change evidence directory")
        changed_behavior_ids = {
            clause.clause_id
            for delta in deltas.values()
            for clause in [*delta.added, *delta.modified, *delta.removed]
        }
        changed_behavior_ids.update(
            clause_id for delta in deltas.values() for clause_id, _, _ in delta.renamed
        )
        changed_scenario_ids = {
            scenario.group("id")
            for delta in deltas.values()
            for clause in [*delta.added, *delta.modified, *delta.removed]
            for scenario in SCENARIO_HEADING_RE.finditer(clause.text)
        }
        evidence_coverage: set[str] = set()
        for item in evidence_items.values():
            if item.get("status", item.get("result")) in {"passed", "waived"}:
                validates = item.get("validates", [])
                if isinstance(validates, list):
                    evidence_coverage.update(
                        target for target in validates if isinstance(target, str)
                    )
        missing_evidence_coverage = (
            expected | changed_behavior_ids | changed_scenario_ids
        ) - evidence_coverage
        if missing_evidence_coverage:
            errors.append(
                "acceptance evidence does not cover: "
                + ", ".join(sorted(str(item) for item in missing_evidence_coverage))
            )
        task_coverage = {
            target
            for row in tasks
            if row["status"] != "cancelled"
            for target in row.get("implements", [])
        }
        missing_task_coverage = (expected | changed_behavior_ids) - task_coverage
        if missing_task_coverage:
            errors.append(
                "non-cancelled tasks do not implement: "
                + ", ".join(sorted(str(item) for item in missing_task_coverage))
            )
        if verification.get("unresolved_findings"):
            errors.append("verification has unresolved findings")
        reviews = verification.get("reviews", [])
        if not isinstance(reviews, list) or not any(
            isinstance(review, dict)
            and review.get("charter") == "integrated"
            and review.get("status") == "passed"
            for review in reviews
        ):
            errors.append("verification needs a passed integrated review")
        elif any(
            not isinstance(review, dict) or review.get("status") != "passed"
            for review in reviews
        ):
            errors.append("all registered reviews must be passed before close")
        for review in reviews:
            if isinstance(review, dict) and review.get("status") == "passed" and not any(
                captured_observation(item, root, change) for item in review.get("evidence", [])
            ):
                errors.append(f"passed {review.get('charter', '<unknown>')} review needs a captured observation")
        required_reviews = {
            REQUIRED_RISK_REVIEWS[driver]
            for driver in change.metadata.get("risk", {}).get("drivers", [])
            if driver in REQUIRED_RISK_REVIEWS
        }
        review_by_charter = {
            review.get("charter"): review
            for review in reviews
            if isinstance(review, dict)
        }
        for charter in sorted(required_reviews):
            review = review_by_charter.get(charter)
            if not isinstance(review, dict) or review.get("status") != "passed":
                errors.append(f"risk driver requires a passed {charter} review")
            elif not any(captured_observation(item, root, change) for item in review.get("evidence", [])):
                errors.append(f"passed {charter} review needs a captured observation")
        if not valid_iso(verification.get("verified_at")) or not revision_resolves(
            verification.get("verified_against"), root, change
        ):
            errors.append("verification needs resolvable verified_at and verified_against completion anchors")
        aggregate_evidence = verification.get("evidence", [])
        if not isinstance(aggregate_evidence, list) or not any(
            isinstance(item, dict) and item.get("kind") in {"command", "log"}
            and captured_observation(item, root, change)
            for item in aggregate_evidence
        ):
            errors.append("verification needs captured command or log aggregate evidence")
        errors.extend(validate_documentation_readiness(root, change, verification))
        for warning in list(warnings):
            if warning.startswith("spec_baselines is absent") or warning.startswith("no baseline hash recorded"):
                errors.append(warning)
        errors.extend(validate_ephemeral(change))
    return {
        "ok": not errors,
        "id": change.metadata.get("id"),
        "slug": change.metadata.get("slug", change.path.name),
        "readiness": readiness,
        "errors": errors,
        "warnings": warnings,
        "domains": sorted(deltas),
        "tasks": tasks,
    }


def validate_ephemeral(change: Change) -> list[str]:
    errors: list[str] = []
    durable = {"proposal.md", "tasks.md", "design.md", "verification.md", "request.md"}
    root = repository_root_for_change(change)
    active_prefix = change.path.relative_to(root).as_posix()
    referenced_paths: set[str] = set()

    def collect(value: Any, key: str | None = None) -> None:
        if key == "ephemeral_artifacts":
            return
        if isinstance(value, dict):
            for child_key, child in value.items():
                collect(child, child_key)
        elif isinstance(value, list):
            for child in value:
                collect(child, key)
        elif isinstance(value, str) and not https_reference(value):
            revision = re.fullmatch(r"sha256:[0-9a-fA-F]{64}@(.+)", value)
            reference = revision.group(1) if revision else value
            reference = repository_reference_path(reference)
            if safe_relative(reference):
                referenced_paths.add(normalize_relative(reference))

    for path in (change.proposal, change.path / "tasks.md", change.path / "verification.md"):
        if path.is_file():
            try:
                collect(read_metadata(path)[1])
            except FlowError as exc:
                errors.append(str(exc))
    for relative in change.metadata.get("ephemeral_artifacts", []):
        if not isinstance(relative, str) or not safe_relative(relative):
            errors.append(f"unsafe ephemeral artifact: {relative!r}")
            continue
        normalized = normalize_relative(relative)
        if normalized in durable or normalized.startswith("specs/") or normalized == JOURNAL:
            errors.append(f"durable artifact cannot be ephemeral: {normalized}")
            continue
        target = within(change.path, normalized)
        if target.exists() and not target.is_file():
            errors.append(f"ephemeral artifact is not a regular file: {normalized}")
        repository_path = f"{active_prefix}/{normalized}"
        if change.metadata.get("retention") in {"minimal", "summary"} and repository_path in referenced_paths:
            errors.append(f"referenced artifact cannot be ephemeral: {normalized}")
    if change.metadata.get("retention") in {"minimal", "summary"}:
        registered = {
            normalize_relative(item)
            for item in change.metadata.get("ephemeral_artifacts", [])
            if isinstance(item, str) and safe_relative(item)
        }
        deleted_paths = {
            f"{active_prefix}/{relative}" for relative in registered
        }
        for source in sorted(change.path.rglob("*.md")):
            relative = source.relative_to(change.path).as_posix()
            if relative in registered or path_is_linklike(source):
                continue
            try:
                text = source.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                continue
            for target in markdown_link_targets(text):
                resolved = change_local_link_path(source, target, root, change.path)
                if resolved in deleted_paths:
                    errors.append(
                        f"referenced artifact cannot be ephemeral: {resolved} (linked from {relative})"
                    )
    return errors


def markdown_link_targets(text: str) -> list[str]:
    """Extract Markdown destinations while ignoring fenced code and metadata."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    text = re.sub(r"(?ms)^\s*```.*?^\s*```\s*$", "", text)
    targets: list[str] = []
    link_re = re.compile(r"!?\[[^\]]*\]\(\s*(?:<([^>]+)>|([^\s)]+))")
    definition_re = re.compile(r"^\s*\[[^\]]+\]:\s*(?:<([^>]+)>|(\S+))", re.MULTILINE)
    for match in (*link_re.finditer(text), *definition_re.finditer(text)):
        target = match.group(1) or match.group(2)
        if target:
            targets.append(target.strip())
    return targets


def change_local_link_path(source: Path, target: str, root: Path, change_path: Path) -> str | None:
    target = target.strip()
    if not target or re.match(r"(?:[a-z][a-z0-9+.-]*:|//|#)", target, re.IGNORECASE):
        return None
    target = target.split("#", 1)[0].split("?", 1)[0].strip()
    if not target:
        return None
    source_relative = source.relative_to(root).as_posix()
    if normalize_relative(target).startswith("openspec/"):
        candidate = PurePosixPath(normalize_relative(target))
    else:
        candidate = PurePosixPath(source_relative).parent / normalize_relative(target)
    normalized_parts: list[str] = []
    for part in candidate.parts:
        if part in {"", "."}:
            continue
        if part == "..":
            if not normalized_parts:
                return None
            normalized_parts.pop()
        else:
            normalized_parts.append(part)
    candidate_relative = "/".join(normalized_parts)
    try:
        candidate_path = within(root, candidate_relative)
        candidate_path.relative_to(change_path.resolve())
    except (FlowError, ValueError):
        return None
    return candidate_relative


def run_status(root: Path, args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    rows = []
    errors = []
    for change in scan_changes(root):
        metadata = change.metadata
        archived = change.path.parent.name == "archive"
        created = metadata.get("created_at")
        if not valid_iso(created):
            errors.append(f"{change.proposal.relative_to(root).as_posix()}: invalid created_at")
        rows.append({
            "id": metadata.get("id"), "slug": metadata.get("slug", change.path.name),
            "status": metadata.get("status"), "created_at": created,
            "completed_at": metadata.get("completed_at"), "archived_at": metadata.get("archived_at"),
            "archived": archived, "path": change.path.relative_to(root).as_posix(),
        })
    def chronology(item: dict[str, Any]) -> tuple[dt.datetime, str, str]:
        value = item.get("created_at")
        parsed = (
            dt.datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(dt.timezone.utc)
            if valid_iso(value)
            else dt.datetime.min.replace(tzinfo=dt.timezone.utc)
        )
        return parsed, item.get("id") or "", item["path"]
    rows.sort(key=chronology)
    return {"ok": not errors, "changes": rows, "errors": errors}, 1 if errors else 0


def run_verify(root: Path, args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    if args.change:
        change = find_change(root, args.change, active_only=True)
        if change is None:
            raise FlowError(f"Active change not found: {args.change}")
        payload = validate_change(change, args.readiness)
        return payload, 0 if payload["ok"] else 1
    results = [validate_change(change, args.readiness) for change in scan_changes(root, include_archive=False)]
    return {"ok": all(item["ok"] for item in results), "changes": results}, 0 if all(item["ok"] for item in results) else 1


def product_spec_header(domain: str) -> str:
    title = domain.replace("/", " / ").replace("-", " ").title()
    metadata = {
        "schema_version": 1, "id": f"SPEC-{domain.replace('/', '-')}",
        "type": "product-spec", "title": f"{title} product specification",
        "status": "active", "owners": [], "sources": [],
        "update_when": [f"Observable {domain} behavior changes"], "relations": [],
        "evidence": [], "affected_docs": [], "verified_at": None, "verified_against": None,
    }
    return f"{metadata_comment(metadata)}\n\n# {title} Product Specification\n\n## Requirements\n"


def merge_delta(current_text: str | None, delta: Delta, domain: str) -> str:
    if current_text is None:
        prefix = product_spec_header(domain).rstrip()
        suffix = ""
        existing: list[Clause] = []
    else:
        existing, _ = parse_clauses(current_text, f"openspec/specs/{domain}/spec.md")
        first = REQ_HEADING_RE.search(current_text)
        prefix = current_text[:first.start()].rstrip() if first else current_text.rstrip()
        suffix = ""
        if existing:
            last = existing[-1]
            last_start = current_text.find(last.text)
            last_end = last_start + len(last.text)
            suffix = current_text[last_end:].strip()
        if not existing and re.search(r"^### Requirement", current_text, re.MULTILINE):
            raise FlowError(f"Current spec {domain} contains legacy requirements without BR IDs")
    by_id = {item.clause_id: item for item in existing}
    order = [item.clause_id for item in existing]
    for item in delta.added:
        if item.clause_id in by_id:
            raise FlowError(f"ADDED target already exists in {domain}: {item.clause_id}")
        by_id[item.clause_id] = item
        order.append(item.clause_id)
    for item in delta.modified:
        if item.clause_id not in by_id:
            raise FlowError(f"MODIFIED target does not exist in {domain}: {item.clause_id}")
        by_id[item.clause_id] = item
    for item in delta.removed:
        if item.clause_id not in by_id:
            raise FlowError(f"REMOVED target does not exist in {domain}: {item.clause_id}")
        del by_id[item.clause_id]
        order.remove(item.clause_id)
    for identifier, old_title, new_title in delta.renamed:
        if identifier not in by_id:
            raise FlowError(f"RENAMED target does not exist in {domain}: {identifier}")
        old = by_id[identifier]
        if old.title != old_title:
            raise FlowError(f"RENAMED old title does not match {identifier} in {domain}")
        heading = f"### Requirement `{identifier}`: {new_title}"
        text = REQ_HEADING_RE.sub(heading, old.text, count=1)
        by_id[identifier] = Clause(identifier, new_title, text)
    blocks = [by_id[identifier].text.strip() for identifier in order]
    result = prefix + ("\n\n" + "\n\n".join(blocks) if blocks else "")
    if suffix:
        result += "\n\n" + suffix
    result += "\n"
    parsed, scenarios = parse_clauses(result, f"merged {domain}")
    if len(parsed) != len(order) or len(scenarios) != len(set(scenarios)):
        raise FlowError(f"Merged spec validation failed for {domain}")
    return result


def archived_match(root: Path, identifier: str) -> Change | None:
    archive = validated_archive_root(root)
    if not archive.is_dir():
        return None
    matches = []
    for proposal in archive.glob("*/proposal.md"):
        _, metadata = read_metadata(proposal)
        if identifier in {metadata.get("id"), metadata.get("slug"), proposal.parent.name}:
            matches.append(Change(proposal.parent, proposal, metadata))
    if len(matches) > 1:
        raise FlowError(f"Archived identifier is ambiguous: {identifier}")
    return matches[0] if matches else None


def delta_operations(delta: Delta) -> dict[str, tuple[str, Any]]:
    operations: dict[str, tuple[str, Any]] = {}
    for operation, clauses in (
        ("ADDED", delta.added), ("MODIFIED", delta.modified), ("REMOVED", delta.removed)
    ):
        for clause in clauses:
            operations[clause.clause_id] = (operation, clause)
    for identifier, old_title, new_title in delta.renamed:
        operations[identifier] = ("RENAMED", (old_title, new_title))
    return operations


def archived_lineage_events(
    root: Path, target: Change, domain: str, clause_id: str
) -> list[tuple[dt.datetime, Change, str, Any]]:
    """Return later archived operations touching one stable BR, chronologically."""
    target_time = parse_iso(target.metadata["archived_at"])
    events: list[tuple[dt.datetime, Change, str, Any]] = []
    for candidate in scan_changes(root, include_archive=True):
        if candidate.path == target.path or candidate.path.parent.name != "archive":
            continue
        for path in delta_files(candidate):
            candidate_domain = path.relative_to(candidate.path / "specs").parent.as_posix()
            if candidate_domain != domain:
                continue
            delta = parse_delta(path)
            operation = delta_operations(delta).get(clause_id)
            if operation is not None:
                archived_at = candidate.metadata.get("archived_at")
                if not valid_iso(archived_at):
                    raise FlowError(f"Archived lineage change has invalid archived_at: {candidate.path}")
                event_time = parse_iso(archived_at)
                if event_time == target_time:
                    raise FlowError(
                        f"Archived lineage is ambiguous for {domain}/{clause_id}: "
                        f"a later change shares archived_at {event_time.isoformat()}"
                    )
                if event_time > target_time:
                    events.append((event_time, candidate, operation[0], operation[1]))
    events.sort(key=lambda item: (item[0], item[1].metadata.get("id", ""), item[1].path.as_posix()))
    for index, event in enumerate(events):
        if index and event[0] == events[index - 1][0]:
            raise FlowError(
                f"Archived lineage is ambiguous for {domain}/{clause_id}: "
                f"multiple later changes share archived_at {event[0].isoformat()}"
            )
    return events


def validate_archived_delta_state(
    root: Path, target: Change, delta_path: Path, domain: str
) -> list[str]:
    """Validate a completed delta against the current spec after later lineage."""
    errors: list[str] = []
    delta = parse_delta(delta_path)
    current_path = current_spec_path(root, domain)
    if not current_path.is_file():
        return [f"archived delta is not reflected in current spec for {domain}"]
    current_text = current_path.read_text(encoding="utf-8")
    current_clauses, _ = parse_clauses(current_text, domain)
    current_by_id = {item.clause_id: item for item in current_clauses}
    operations = delta_operations(delta)
    for clause_id, (operation, payload) in operations.items():
        if operation == "ADDED":
            state: tuple[bool, Clause | None, str | None] = (True, payload, payload.title)
        elif operation == "MODIFIED":
            state = (True, payload, payload.title)
        elif operation == "REMOVED":
            state = (False, None, None)
        else:
            _old_title, new_title = payload
            state = (True, None, new_title)
        for _at, later_change, later_operation, later_payload in archived_lineage_events(
            root, target, domain, clause_id
        ):
            present, clause, title = state
            if later_operation == "ADDED":
                errors.append(f"archived lineage reuses stable ID {clause_id} in {later_change.path}")
                continue
            if not present:
                errors.append(f"archived lineage operates on removed ID {clause_id} in {later_change.path}")
                continue
            if later_operation == "MODIFIED":
                state = (True, later_payload, later_payload.title)
            elif later_operation == "REMOVED":
                state = (False, None, None)
            elif later_operation == "RENAMED":
                _old_title, new_title = later_payload
                if clause is not None:
                    heading = f"### Requirement `{clause_id}`: {new_title}"
                    text = REQ_HEADING_RE.sub(heading, clause.text, count=1)
                    clause = Clause(clause_id, new_title, text)
                state = (True, clause, new_title)
        present, clause, title = state
        actual = current_by_id.get(clause_id)
        if not present:
            if actual is not None:
                errors.append(f"archived removed clause is present in current spec: {clause_id}")
        elif clause is not None:
            if actual != clause:
                errors.append(f"archived delta clause is not current after lineage: {clause_id}")
        elif actual is None or actual.title != title:
            errors.append(f"archived rename is not current after lineage: {clause_id}")
    return errors


def validate_archived_result(root: Path, change: Change) -> list[str]:
    errors: list[str] = validate_proposal(change)
    metadata = change.metadata
    if metadata.get("status") != "done":
        errors.append("archived requirement is not done")
    if not valid_iso(metadata.get("completed_at")) or not valid_iso(metadata.get("archived_at")):
        errors.append("archived requirement lacks completion timestamps")
    archived_verification: dict[str, Any] = {}
    for relative, artifact_type in (("tasks.md", "exec-plan"), ("verification.md", "evidence")):
        path = change.path / relative
        if not path.is_file():
            errors.append(f"archived change is missing {relative}")
            continue
        try:
            _, artifact = read_metadata(path)
        except FlowError as exc:
            errors.append(str(exc))
            continue
        if artifact.get("type") != artifact_type or artifact.get("status") != "completed":
            errors.append(f"archived {relative} is not completed")
        if relative == "verification.md":
            archived_verification = artifact
    if archived_verification:
        _, verification_errors = verification_state(change)
        errors.extend(verification_errors)
        if archived_verification.get("unresolved_findings"):
            errors.append("archived verification has unresolved findings")
        reviews = archived_verification.get("reviews", [])
        if not isinstance(reviews, list) or not any(
            isinstance(review, dict)
            and review.get("charter") == "integrated"
            and review.get("status") == "passed"
            for review in reviews
        ):
            errors.append("archived verification lacks a passed integrated review")
        elif any(
            not isinstance(review, dict) or review.get("status") != "passed"
            for review in reviews
        ):
            errors.append("archived verification contains an incomplete review")
    for item in metadata.get("acceptance", []):
        if not isinstance(item, dict) or item.get("status") not in {"passed", "not_applicable"}:
            errors.append("archived proposal contains incomplete acceptance")
            continue
        evidence = item.get("evidence", [])
        if not isinstance(evidence, list) or not evidence or any(
            not valid_evidence_item(evidence_item, root) for evidence_item in evidence
        ):
            errors.append(f"archived acceptance {item.get('id', '<unknown>')} lacks valid evidence")
        elif item.get("status") == "passed" and not any(
            captured_observation(evidence_item, root, change) for evidence_item in evidence
        ):
            errors.append(
                f"archived acceptance {item.get('id', '<unknown>')} lacks captured observation"
            )
    if archived_verification:
        aggregate = archived_verification.get("evidence", [])
        if not isinstance(aggregate, list) or not any(
            isinstance(item, dict)
            and item.get("kind") in {"command", "log"}
            and captured_observation(item, root, change)
            for item in aggregate
        ):
            errors.append("archived verification lacks captured command or log aggregate evidence")
        reviews = archived_verification.get("reviews", [])
        if isinstance(reviews, list):
            for review in reviews:
                if isinstance(review, dict) and review.get("status") == "passed" and not any(
                    captured_observation(item, root, change)
                    for item in review.get("evidence", [])
                ):
                    errors.append(
                        f"archived review {review.get('charter', '<unknown>')} lacks captured observation"
                    )
            required_reviews = {
                REQUIRED_RISK_REVIEWS[driver]
                for driver in metadata.get("risk", {}).get("drivers", [])
                if driver in REQUIRED_RISK_REVIEWS
            }
            review_by_charter = {
                review.get("charter"): review
                for review in reviews
                if isinstance(review, dict)
            }
            for charter in sorted(required_reviews):
                review = review_by_charter.get(charter)
                if not isinstance(review, dict) or review.get("status") != "passed":
                    errors.append(f"archived requirement lacks passed {charter} review")
        errors.extend(validate_documentation_readiness(root, change, archived_verification))
    for path in delta_files(change):
        domain = path.relative_to(change.path / "specs").parent.as_posix()
        try:
            errors.extend(validate_archived_delta_state(root, change, path, domain))
        except FlowError as exc:
            errors.append(str(exc))
    errors.extend(validate_ephemeral(change))
    for relative in ("proposal.md", "tasks.md", "verification.md"):
        path = change.path / relative
        if not path.is_file():
            continue
        try:
            _, artifact = read_metadata(path)
        except FlowError:
            continue
        values: list[Any] = [artifact]
        while values:
            value = values.pop()
            if isinstance(value, dict):
                values.extend(value.values())
            elif isinstance(value, list):
                values.extend(value)
            elif isinstance(value, str) and not https_reference(value):
                revision = re.fullmatch(r"sha256:[0-9a-fA-F]{64}@(.+)", value)
                candidate = revision.group(1) if revision else repository_reference_path(value)
                if candidate.startswith(change.path.relative_to(root).as_posix() + "/"):
                    exists = (
                        pattern_has_match(root, candidate)
                        if any(character in candidate for character in "*?[")
                        else within(root, candidate).exists()
                    )
                    if not exists:
                        errors.append(f"archived metadata reference is missing: {candidate}")
    return list(dict.fromkeys(errors))


def rewrite_archived_references(value: Any, active_prefix: str, archive_prefix: str) -> Any:
    """Rewrite only repository paths owned by this archived change."""
    if isinstance(value, str):
        revision = re.fullmatch(r"(sha256:[0-9a-fA-F]{64}@)(.+)", value)
        if revision:
            rewritten_path = rewrite_archived_references(
                revision.group(2), active_prefix, archive_prefix
            )
            return revision.group(1) + rewritten_path
        normalized = normalize_relative(value)
        if normalized == active_prefix or normalized.startswith(active_prefix + "/"):
            return archive_prefix + normalized[len(active_prefix):]
        return value
    if isinstance(value, list):
        return [rewrite_archived_references(item, active_prefix, archive_prefix) for item in value]
    if isinstance(value, dict):
        return {
            key: rewrite_archived_references(item, active_prefix, archive_prefix)
            for key, item in value.items()
        }
    return value


def close_plan(root: Path, change: Change, timestamp: str) -> tuple[dict[Path, bytes], list[Path], Path, dict[str, Any]]:
    archive_root = validated_archive_root(root)
    check = validate_change(change, readiness=True)
    if not check["ok"]:
        raise FlowError("Close readiness failed: " + "; ".join(check["errors"]))
    writes: dict[Path, bytes] = {}
    for path in delta_files(change):
        domain = path.relative_to(change.path / "specs").parent.as_posix()
        target = current_spec_path(root, domain)
        current = target.read_text(encoding="utf-8") if target.is_file() else None
        writes[target] = merge_delta(current, parse_delta(path), domain).encode()
    proposal_text_value, proposal = read_metadata(change.proposal)
    date = dt.datetime.fromisoformat(timestamp).date().isoformat()
    archive = archive_root / f"{date}-{proposal['id']}-{proposal['slug']}"
    if archive.exists():
        raise FlowError(f"Archive target already exists: {archive}")
    active_prefix = change.path.relative_to(root).as_posix()
    archive_prefix = archive.relative_to(root).as_posix()
    verification_path = change.path / "verification.md"
    verification_text_value, verification = read_metadata(verification_path)
    tasks_path = change.path / "tasks.md"
    tasks_text_value, tasks_metadata = read_metadata(tasks_path)
    evidence_by_id = {
        item["id"]: item for item in verification.get("acceptance", []) if isinstance(item, dict) and "id" in item
    }
    for item in proposal.get("acceptance", []):
        evidence = evidence_by_id[item["id"]]
        evidence_result = evidence.get("status", evidence.get("result"))
        item["status"] = "passed" if evidence_result == "passed" else "not_applicable"
        item["evidence"] = evidence.get("evidence", [])
    proposal["status"] = "done"
    proposal["updated_at"] = timestamp
    proposal["status_changed_at"] = timestamp
    proposal["completed_at"] = timestamp
    proposal["archived_at"] = timestamp
    proposal["verified_at"] = verification.get("verified_at")
    proposal["verified_against"] = verification.get("verified_against")
    proposal["evidence"] = verification.get("evidence", [])
    proposal.setdefault("status_history", []).append({"status": "done", "at": timestamp, "reason": "Close completed"})
    proposal = rewrite_archived_references(proposal, active_prefix, archive_prefix)
    verification["status"] = "completed"
    verification["updated_at"] = timestamp
    verification["completed_at"] = timestamp
    verification = rewrite_archived_references(verification, active_prefix, archive_prefix)
    tasks_metadata["status"] = "completed"
    tasks_metadata["verified_at"] = verification.get("verified_at")
    tasks_metadata["verified_against"] = verification.get("verified_against")
    tasks_metadata = rewrite_archived_references(tasks_metadata, active_prefix, archive_prefix)
    proposal_text_value = sync_proposal_prose(
        proposal_text_value, proposal.get("acceptance", []), timestamp
    )
    writes[change.proposal] = replace_metadata(proposal_text_value, proposal).encode()
    writes[verification_path] = replace_metadata(verification_text_value, verification).encode()
    writes[tasks_path] = replace_metadata(tasks_text_value, tasks_metadata).encode()
    deletes: list[Path] = []
    if proposal.get("retention") in {"minimal", "summary"}:
        for relative in proposal.get("ephemeral_artifacts", []):
            target = within(change.path, relative)
            if target.is_file():
                deletes.append(target)
    return writes, deletes, archive, {"check": check, "proposal": proposal}


def run_close(root: Path, args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    change = find_change(root, args.identifier, active_only=True)
    if change is None:
        archived = archived_match(root, args.identifier)
        if archived:
            archived_errors = validate_archived_result(root, archived)
            if archived_errors:
                raise FlowError("Archived change is incomplete: " + "; ".join(archived_errors))
            return {"ok": True, "idempotent": True, "archive": archived.path.relative_to(root).as_posix()}, 0
        raise FlowError(f"Active change not found: {args.identifier}")
    if (change.path / JOURNAL).is_file():
        if args.dry_run:
            raise FlowError("Close recovery journal exists; dry-run will not mutate it. Run close without --dry-run to recover")
        recover_close(change.path / JOURNAL, root)
        refreshed = find_change(root, args.identifier, active_only=True)
        if refreshed is None:
            raise FlowError("Change disappeared while recovering its close journal")
        change = refreshed
    timestamp = now_iso()
    writes, deletes, archive, details = close_plan(root, change, timestamp)
    planned = {
        "ok": True, "dry_run": args.dry_run, "idempotent": False,
        "change": change.path.relative_to(root).as_posix(),
        "archive": archive.relative_to(root).as_posix(),
        "writes": sorted(path.relative_to(root).as_posix() for path in writes),
        "removes": sorted(path.relative_to(root).as_posix() for path in deletes),
        "completed_at": timestamp,
        "warnings": details["check"]["warnings"],
    }
    if args.dry_run:
        return planned, 0
    originals = {path: path.read_bytes() if path.exists() else None for path in {*writes, *deletes}}
    journal_path = change.path / JOURNAL
    backups = {
        path.relative_to(root).as_posix(): (
            None if content is None else base64.b64encode(content).decode("ascii")
        )
        for path, content in originals.items()
    }
    journal = json.dumps(
        {"schema_version": 1, **planned, "backups": backups},
        ensure_ascii=False, indent=2, sort_keys=True,
    ).encode() + b"\n"
    moved = False
    try:
        validated_archive_root(root)
        atomic_write(journal_path, journal)
        specs_root = (root / "openspec" / "specs").resolve()
        for path in writes:
            if path.name != "spec.md":
                continue
            try:
                relative = path.relative_to(specs_root)
            except ValueError:
                continue
            current_spec_path(root, relative.parent.as_posix())
        apply_file_transaction(writes, deletes)
        archive.parent.mkdir(parents=True, exist_ok=True)
        validated_archive_root(root)
        os.replace(change.path, archive)
        moved = True
        archived_proposal = archive / "proposal.md"
        if not archived_proposal.is_file():
            raise FlowError("Post-close validation failed: archived proposal is missing")
        _, archived_metadata = read_metadata(archived_proposal)
        archived_change = Change(archive, archived_proposal, archived_metadata)
        archived_errors = validate_archived_result(root, archived_change)
        if archived_errors:
            raise FlowError(
                "Post-close validation failed: " + "; ".join(archived_errors)
            )
        (archive / JOURNAL).unlink(missing_ok=True)
    except BaseException:
        if moved:
            os.replace(archive, change.path)
            moved = False
        restore_writes = {path: content for path, content in originals.items() if content is not None}
        restore_deletes = [path for path, content in originals.items() if content is None]
        apply_file_transaction(restore_writes, restore_deletes)
        journal_path.unlink(missing_ok=True)
        raise
    return planned, 0


def recover_close(journal_path: Path, root: Path) -> None:
    """Restore the pre-close bytes captured by an interrupted active close."""
    try:
        payload = json.loads(journal_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FlowError(f"Cannot recover invalid close journal {journal_path}: {exc}") from exc
    backups = payload.get("backups")
    if payload.get("schema_version") != 1 or not isinstance(backups, dict):
        raise FlowError(f"Unsupported close journal: {journal_path}")
    writes: dict[Path, bytes] = {}
    deletes: list[Path] = []
    for relative, encoded in backups.items():
        path = within(root, relative)
        if encoded is None:
            deletes.append(path)
        elif isinstance(encoded, str):
            try:
                writes[path] = base64.b64decode(encoded, validate=True)
            except ValueError as exc:
                raise FlowError(f"Invalid backup in close journal: {relative}") from exc
        else:
            raise FlowError(f"Invalid backup in close journal: {relative}")
    apply_file_transaction(writes, deletes)
    journal_path.unlink(missing_ok=True)


def canonical_package_files(skill_root: Path) -> list[str]:
    candidates: list[Path] = []
    for relative in ("SKILL.md",):
        path = skill_root / relative
        if path.is_file():
            candidates.append(path)
    for directory in ("references", "templates", "adapters", "agents"):
        base = skill_root / directory
        if base.is_dir():
            candidates.extend(path for path in base.rglob("*") if path.is_file())
    script = skill_root / "scripts" / "dev_spec_flow.py"
    if script.is_file():
        candidates.append(script)
    return sorted(path.relative_to(skill_root).as_posix() for path in candidates)


def parse_package_manifest(skill_root: Path) -> dict[str, Any]:
    path = skill_root / PACKAGE_MANIFEST
    if not path.is_file():
        raise FlowError("manifest.json is missing; run validate --refresh-manifest")
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FlowError(f"Invalid package manifest: {exc}") from exc
    if not isinstance(manifest, dict) or manifest.get("schema_version") != PACKAGE_SCHEMA:
        raise FlowError("Unsupported package manifest schema")
    if manifest.get("package") != "dev-spec-flow":
        raise FlowError("Package manifest package must be dev-spec-flow")
    if not isinstance(manifest.get("version"), str) or not manifest["version"].strip():
        raise FlowError("Package manifest version must be a non-empty string")
    files = manifest.get("files")
    normalized: dict[str, str] = {}
    if isinstance(files, dict):
        normalized = files
    elif isinstance(files, list):
        for item in files:
            if not isinstance(item, dict) or not isinstance(item.get("path"), str) or not isinstance(item.get("sha256"), str):
                raise FlowError("Invalid file entry in package manifest")
            normalized[item["path"]] = item["sha256"]
    else:
        raise FlowError("Package manifest files must be an object or array")
    if any(not safe_relative(path) or not isinstance(digest, str) or not SHA256_RE.fullmatch(digest) for path, digest in normalized.items()):
        raise FlowError("Package manifest contains an unsafe path or invalid hash")
    manifest = dict(manifest)
    manifest["files"] = normalized
    return manifest


def package_validation(skill_root: Path) -> tuple[list[str], list[str], dict[str, Any] | None]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        manifest = parse_package_manifest(skill_root)
    except FlowError as exc:
        return [str(exc)], warnings, None
    actual = set(canonical_package_files(skill_root))
    declared = set(manifest["files"])
    if actual != declared:
        missing = declared - actual
        undeclared = actual - declared
        if missing:
            errors.append(f"manifest files missing from package: {', '.join(sorted(missing))}")
        if undeclared:
            errors.append(f"runtime files missing from manifest: {', '.join(sorted(undeclared))}")
    for relative, digest in manifest["files"].items():
        path = within(skill_root, relative)
        if path.is_file() and sha256_file(path) != digest:
            errors.append(f"manifest hash mismatch: {relative}")
    return errors, warnings, manifest


def run_validate(root: Path, args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    skill_root = Path(__file__).resolve().parent.parent
    if args.refresh_manifest:
        files = {relative: sha256_file(skill_root / relative) for relative in canonical_package_files(skill_root)}
        existing: dict[str, Any] = {}
        manifest_path = skill_root / PACKAGE_MANIFEST
        if manifest_path.is_file():
            try:
                existing = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError):
                existing = {}
        manifest = {
            "schema_version": PACKAGE_SCHEMA,
            "package": "dev-spec-flow",
            "version": existing.get("version", "2.0.0"),
            "files": files,
        }
        atomic_write(manifest_path, (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode())
    errors, warnings, manifest = package_validation(skill_root)
    return {
        "ok": not errors, "manifest": PACKAGE_MANIFEST,
        "version": manifest.get("version") if manifest else None,
        "files": len(manifest.get("files", {})) if manifest else 0,
        "errors": errors, "warnings": warnings, "refreshed": args.refresh_manifest,
    }, 1 if errors else 0


def installation_destination(root: Path, target: str, scope: str, explicit: str | None) -> Path:
    def lexical_absolute(path: Path) -> Path:
        # resolve() would hide a destination symlink/junction before the
        # installer has a chance to reject it.
        return Path(os.path.abspath(os.fspath(path.expanduser())))

    if explicit:
        return lexical_absolute(Path(explicit))
    if target == "grok":
        raise FlowError("Grok installation requires an explicit --dest")
    if scope == "user":
        bases = {"codex": ".codex", "claude": ".claude", "cursor": ".cursor"}
        return lexical_absolute(Path.home() / bases[target] / "skills" / "dev-spec-flow")
    bases = {"codex": ".agents", "claude": ".claude", "cursor": ".cursor"}
    return lexical_absolute(root / bases[target] / "skills" / "dev-spec-flow")


def source_install_files(skill_root: Path, manifest: dict[str, Any]) -> dict[str, bytes]:
    result = {relative: within(skill_root, relative).read_bytes() for relative in manifest["files"]}
    result[PACKAGE_MANIFEST] = (skill_root / PACKAGE_MANIFEST).read_bytes()
    return result


def install_record(
    version: str,
    target: str,
    scope: str,
    destination: Path,
    contents: dict[str, bytes],
) -> bytes:
    payload = {
        "schema_version": 1, "package": "dev-spec-flow", "version": version,
        "target": target, "scope": scope,
        "destination": str(destination.resolve()),
        "files": {relative: sha256_bytes(content) for relative, content in sorted(contents.items())},
    }
    return (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def install_path_owned(relative: Any) -> bool:
    if not isinstance(relative, str) or not safe_relative(relative):
        return False
    normalized = normalize_relative(relative)
    if normalized == PACKAGE_MANIFEST or normalized == "SKILL.md":
        return True
    first = normalized.split("/", 1)[0]
    return first in {"scripts", "references", "templates", "adapters", "agents"}


def read_install_record(destination: Path) -> dict[str, Any]:
    path = destination / INSTALL_RECORD
    if not path.is_file():
        raise FlowError(f"Managed installation record is missing: {path}")
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FlowError(f"Invalid installation record: {exc}") from exc
    if not isinstance(record, dict) or not isinstance(record.get("files"), dict):
        raise FlowError("Invalid installation record shape")
    if record.get("schema_version") != 1 or record.get("package") != "dev-spec-flow":
        raise FlowError("Invalid managed installation identity")
    if record.get("target") not in {"codex", "claude", "cursor", "grok"}:
        raise FlowError("Invalid managed installation target")
    if record.get("scope") not in {"user", "project"}:
        raise FlowError("Invalid managed installation scope")
    if not isinstance(record.get("version"), str) or not record["version"].strip():
        raise FlowError("Invalid managed installation version")
    recorded_destination = record.get("destination")
    if not isinstance(recorded_destination, str) or not recorded_destination.strip():
        raise FlowError("Managed installation record has no destination ownership")
    try:
        if Path(recorded_destination).expanduser().resolve() != destination.resolve():
            raise FlowError("Managed installation record destination does not match its directory")
    except OSError as exc:
        raise FlowError(f"Invalid managed installation destination: {exc}") from exc
    for relative, digest in record["files"].items():
        if not install_path_owned(relative) or not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
            raise FlowError(f"Installation record contains an unowned or invalid file: {relative!r}")
    return record


def validate_install_history(destination: Path, record: dict[str, Any]) -> set[str]:
    """Validate the immutable-on-update boundary recorded by a prior install.

    The install record is intentionally kept in the destination so that an
    installation can be moved or inspected without a separate state database.
    It is therefore not sufficient as the sole authority for deletion: a
    modified record could name any otherwise-looking path under an owned root.
    The package manifest copied by the install is the historical file-set
    receipt.  Require the record and that receipt to agree before update (or
    health checks) can trust any path for replacement/deletion.
    """
    # Resolve the receipt through the same link/junction guard used for all
    # managed paths before opening it.
    manifest_path = within(destination, PACKAGE_MANIFEST)
    try:
        historical_manifest = parse_package_manifest(destination)
    except FlowError as exc:
        raise FlowError("Installed package manifest validation failed: " + str(exc)) from exc

    recorded_files = record["files"]
    recorded_manifest_digest = recorded_files.get(PACKAGE_MANIFEST)
    if recorded_manifest_digest is None:
        raise FlowError("Managed installation record does not own package manifest")
    if sha256_file(manifest_path) != recorded_manifest_digest:
        raise FlowError("Installed package manifest does not match installation record")
    if record.get("version") != historical_manifest.get("version"):
        raise FlowError("Managed installation version does not match historical package manifest")

    historical_files = set(historical_manifest["files"])
    if PACKAGE_MANIFEST in historical_files:
        raise FlowError("Historical package manifest cannot list itself as a package file")
    unowned = sorted(relative for relative in historical_files if not install_path_owned(relative))
    if unowned:
        raise FlowError(
            "Historical package manifest contains an unowned file: " + ", ".join(unowned)
        )
    for relative in sorted(historical_files):
        path = within(destination, relative)
        if path.exists() and not path.is_file():
            raise FlowError(f"Historical package manifest names a non-file path: {relative}")
    expected_files = historical_files | {PACKAGE_MANIFEST}
    recorded_paths = set(recorded_files)
    if recorded_paths != expected_files:
        missing = sorted(expected_files - recorded_paths)
        extra = sorted(recorded_paths - expected_files)
        details: list[str] = []
        if missing:
            details.append("missing=" + ", ".join(missing))
        if extra:
            details.append("extra=" + ", ".join(extra))
        raise FlowError(
            "Managed installation record does not match historical package manifest"
            + (" (" + "; ".join(details) + ")" if details else "")
        )

    mismatched = sorted(
        relative
        for relative, digest in historical_manifest["files"].items()
        if recorded_files.get(relative) != digest
    )
    if mismatched:
        raise FlowError(
            "Managed installation record hashes do not match historical package manifest: "
            + ", ".join(mismatched)
        )
    return expected_files


def check_destination_not_source(destination: Path, skill_root: Path) -> None:
    if (
        destination == skill_root
        or skill_root in destination.parents
        or destination in skill_root.parents
    ):
        raise FlowError("Installation destination cannot contain or be inside the source Skill")


def require_real_install_destination(destination: Path) -> None:
    """Reject a destination whose lexical path traverses a linklike directory."""
    for candidate in (destination, *destination.parents):
        if path_is_linklike(candidate):
            raise FlowError(
                "Installation destination cannot be or traverse a symlink or junction: "
                + str(candidate)
            )


def run_install(root: Path, args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    skill_root = Path(__file__).resolve().parent.parent
    errors, _, manifest = package_validation(skill_root)
    if errors or manifest is None:
        raise FlowError("Source package validation failed: " + "; ".join(errors))
    destination = installation_destination(root, args.target, args.scope, args.dest)
    require_real_install_destination(destination)
    check_destination_not_source(destination, skill_root)
    if destination.exists() and any(destination.iterdir()):
        raise FlowError("Destination is not empty; use update only for a managed installation")
    contents = source_install_files(skill_root, manifest)
    writes = {within(destination, relative): content for relative, content in contents.items()}
    writes[destination / INSTALL_RECORD] = install_record(
        manifest["version"], args.target, args.scope, destination, contents
    )
    apply_file_transaction(writes)
    return {"ok": True, "destination": str(destination), "files": len(contents), "version": manifest["version"]}, 0


def run_update(root: Path, args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    skill_root = Path(__file__).resolve().parent.parent
    errors, _, manifest = package_validation(skill_root)
    if errors or manifest is None:
        raise FlowError("Source package validation failed: " + "; ".join(errors))
    destination = installation_destination(root, args.target, args.scope, args.dest)
    require_real_install_destination(destination)
    check_destination_not_source(destination, skill_root)
    record = read_install_record(destination)
    if record.get("target") != args.target or record.get("scope") != args.scope:
        raise FlowError("Managed installation record target/scope does not match update request")
    historical_files = validate_install_history(destination, record)
    old = record["files"]
    contents = source_install_files(skill_root, manifest)
    conflicts: list[str] = []
    for relative, old_digest in old.items():
        if not safe_relative(relative):
            conflicts.append(relative)
            continue
        path = within(destination, relative)
        actual = sha256_file(path) if path.is_file() else None
        if actual != old_digest:
            conflicts.append(relative)
    for relative in set(contents) - set(old):
        if within(destination, relative).exists():
            conflicts.append(relative)
    if conflicts:
        return {"ok": False, "destination": str(destination), "conflicts": sorted(set(conflicts)), "errors": ["Local modifications or unmanaged collisions were preserved"]}, 1
    writes = {within(destination, relative): content for relative, content in contents.items()}
    writes[destination / INSTALL_RECORD] = install_record(
        manifest["version"], args.target, args.scope, destination, contents
    )
    # Keep the historical receipt as a second, independent deletion boundary.
    # This remains defensive if record handling changes later.
    deletes = [
        within(destination, relative)
        for relative in (set(old) - set(contents)) & historical_files
    ]
    apply_file_transaction(writes, deletes)
    return {"ok": True, "destination": str(destination), "updated": len(contents), "removed": len(deletes), "version": manifest["version"]}, 0


def installation_health(destination: Path, target: str | None = None, scope: str | None = None) -> dict[str, Any]:
    try:
        require_real_install_destination(destination)
        record = read_install_record(destination)
        validate_install_history(destination, record)
    except FlowError as exc:
        return {"ok": False, "destination": str(destination), "errors": [str(exc)], "modified": [], "missing": []}
    errors: list[str] = []
    if target is not None and record.get("target") != target:
        errors.append("Managed installation target does not match requested target")
    if scope is not None and record.get("scope") != scope:
        errors.append("Managed installation scope does not match requested scope")
    modified: list[str] = []
    missing: list[str] = []
    for relative, digest in record["files"].items():
        if not install_path_owned(relative):
            modified.append(relative)
            continue
        path = within(destination, relative)
        if not path.is_file():
            missing.append(relative)
        elif sha256_file(path) != digest:
            modified.append(relative)
    return {"ok": not modified and not missing and not errors, "destination": str(destination), "modified": sorted(modified), "missing": sorted(missing), "version": record.get("version"), "errors": errors}


def run_doctor(root: Path, args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    skill_root = Path(__file__).resolve().parent.parent
    package_errors, package_warnings, manifest = package_validation(skill_root)
    change_results = []
    try:
        change_results = [validate_change(change, False) for change in scan_changes(root, include_archive=False)]
    except FlowError as exc:
        package_errors.append(str(exc))
    installation = None
    if args.target:
        destination = installation_destination(root, args.target, args.scope, args.dest)
        installation = installation_health(destination, args.target, args.scope)
    errors = [*package_errors]
    if any(not item["ok"] for item in change_results):
        errors.append("One or more active changes failed structural validation")
    if installation is not None and not installation["ok"]:
        errors.append("Managed installation is missing or modified")
    payload = {
        "ok": not errors, "python": sys.version.split()[0],
        "python_supported": sys.version_info >= (3, 10),
        "package": {"version": manifest.get("version") if manifest else None, "errors": package_errors, "warnings": package_warnings},
        "changes": change_results, "installation": installation, "errors": errors,
    }
    if not payload["python_supported"]:
        payload["ok"] = False
        payload["errors"].append("Python 3.10 or newer is required")
    return payload, 0 if payload["ok"] else 1


def add_root_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", type=Path, default=argparse.SUPPRESS, help="Target repository root")


def add_json_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help="Emit JSON")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    add_root_argument(parser)
    add_json_argument(parser)
    subparsers = parser.add_subparsers(dest="command", required=True)

    new = subparsers.add_parser("new", help="Create a timestamped change skeleton")
    add_root_argument(new); add_json_argument(new)
    new.add_argument("slug"); new.add_argument("--title", required=True)
    new.add_argument("--complexity", choices=sorted(COMPLEXITIES), default="medium")
    new.add_argument("--risk-level", choices=sorted(RISK_LEVELS), default="medium")
    new.add_argument("--risk-driver", action="append", default=[])
    new.add_argument("--retention", choices=sorted(RETENTIONS), default="summary")
    new.add_argument("--domain", action="append", required=True)
    new.add_argument("--approved", action="store_true")
    new.add_argument("--request")

    status = subparsers.add_parser("status", help="List changes in lifecycle order")
    add_root_argument(status); add_json_argument(status)

    verify = subparsers.add_parser("verify", help="Validate change structure or close readiness")
    add_root_argument(verify); add_json_argument(verify)
    verify.add_argument("--change"); verify.add_argument("--readiness", action="store_true")

    close = subparsers.add_parser("close", help="Merge, retain, and archive a ready change")
    add_root_argument(close); add_json_argument(close)
    close.add_argument("identifier"); close.add_argument("--dry-run", action="store_true")

    validate = subparsers.add_parser("validate", help="Validate this canonical Skill package")
    add_root_argument(validate); add_json_argument(validate)
    validate.add_argument("--refresh-manifest", action="store_true")

    for name, help_text in (("install", "Install a managed canonical Skill"), ("update", "Safely update a managed installation")):
        command = subparsers.add_parser(name, help=help_text)
        add_root_argument(command); add_json_argument(command)
        command.add_argument("--target", choices=("codex", "claude", "cursor", "grok"), required=True)
        command.add_argument("--scope", choices=("user", "project"), default="user")
        command.add_argument("--dest")

    doctor = subparsers.add_parser("doctor", help="Diagnose package, project, and installation drift")
    add_root_argument(doctor); add_json_argument(doctor)
    doctor.add_argument("--target", choices=("codex", "claude", "cursor", "grok"))
    doctor.add_argument("--scope", choices=("user", "project"), default="user")
    doctor.add_argument("--dest")
    return parser


def print_text(command: str, payload: dict[str, Any]) -> None:
    if command == "status":
        for item in payload.get("changes", []):
            marker = "archive" if item["archived"] else item.get("status")
            print(f"{item.get('created_at') or 'unknown'}  {item.get('id') or '?'}  {marker}  {item.get('slug')}")
    elif command == "verify":
        targets = payload.get("changes", [payload])
        for item in targets:
            print(f"{item.get('id')}: {'ready' if item.get('ok') else 'not ready'}")
            for error in item.get("errors", []): print(f"ERROR: {error}")
            for warning in item.get("warnings", []): print(f"WARNING: {warning}")
    else:
        print(f"{command}: {'ok' if payload.get('ok') else 'failed'}")
        for key in ("id", "path", "destination", "archive", "version"):
            if payload.get(key) is not None: print(f"{key}: {payload[key]}")
        for error in payload.get("errors", []): print(f"ERROR: {error}")
        for warning in payload.get("warnings", []): print(f"WARNING: {warning}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = Path(getattr(args, "root", Path.cwd())).resolve()
    json_output = bool(getattr(args, "json", False))
    handlers = {
        "new": run_new, "status": run_status, "verify": run_verify,
        "close": run_close, "validate": run_validate, "install": run_install,
        "update": run_update, "doctor": run_doctor,
    }
    try:
        payload, exit_code = handlers[args.command](root, args)
    except (FlowError, OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        payload, exit_code = {"ok": False, "errors": [str(exc)]}, 1
    if json_output:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print_text(args.command, payload)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
