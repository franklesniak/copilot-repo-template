"""Generate a marker-aware template sync candidate table."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, NoReturn
from urllib.parse import urlsplit, urlunsplit

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from template_sync_materialization_helpers import (  # noqa: E402
    DEFAULT_MANIFEST_PATH,
    DEFAULT_MANIFEST_SCHEMA_PATH,
    DEFAULT_MARKER_PATH,
    DEFAULT_MARKER_SCHEMA_PATH,
    REMOVAL_DECISION,
    DeferredProtectedCandidate,
    ManifestMapping,
    LocalOverride,
    PathRelation,
    PROTECTED_EXACT_PATHS,
    ProtectedFileDecision,
    TemplateSyncMaterializationError as MarkerValidationError,
    deferred_candidate_summary,
    has_wildcard,
    is_protected_instruction_path,
    is_protected_manifest_pattern,
    local_override_summary,
    load_json_mapping,
    load_yaml_mapping,
    manifest_pattern_matches_path,
    parse_manifest_mappings,
    parse_marker_decision_data,
    path_has_symlink_component,
    protected_decision_summary,
    repository_path_exists,
    repository_relative_path,
    resolve_repo_path,
    resolve_repo_root,
    selected_relation_for_path,
    validate_schema,
    validate_protected_file_decisions,
)

DEFAULT_RANGE_HEAD_REF = "template/main"
DEFAULT_TODO_PATH = "_TODO-repo-init.md"
TEMPLATE_UPDATE_PROCEDURE_PATH = "TEMPLATE_UPDATE_PROCEDURE.md"
GITHUB_METADATA_MANUAL_SETTINGS = (
    "private vulnerability reporting",
    "repository rulesets or classic branch protection",
    "required status checks",
    "bypass roles",
)
DISCOVERY_SKIP_DIRS = frozenset(
    {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".terraform",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "node_modules",
        "venv",
    }
)
ADOPTION_MODE_MODULES = frozenset(
    {
        "agent-instructions",
        "baseline",
        "github-actions",
        "github-platform",
        "github-templates",
        "template-onboarding",
        "template-sync-support",
    }
)
INLINE_TRIM_NOTE_KEYWORDS = (
    "inline block",
    "inline blocks",
    "delimited",
    "strip",
)
TODO_KNOWN_SECTIONS = (
    "Discoverable Repository State",
    "Manual GitHub Settings",
    "Maintainer Policy Decisions",
    "Protected-File Adoption Decisions",
    "Unresolved Settings",
    "Resolution Evidence",
)
TODO_DECISION_SECTIONS = frozenset(
    {
        "Manual GitHub Settings",
        "Maintainer Policy Decisions",
        "Protected-File Adoption Decisions",
        "Unresolved Settings",
    }
)
TODO_LINK_LIMIT = 3
VALIDATION_COMMANDS_BY_MODULE = {
    "agent-instructions": (
        "npm run lint:md",
        "manual protected-file authorization review",
    ),
    "baseline": (
        "pre-commit run --all-files",
        "placeholder and repository-identity review",
    ),
    "github-actions": ("pre-commit run actionlint --all-files",),
    "github-platform": (
        "pre-commit run validate-dependabot-config --all-files",
        "pytest tests/test_dependabot_schema.py -v",
    ),
    "github-templates": ("manual GitHub template rendering review",),
    "json": ("pre-commit run check-json --all-files",),
    "markdown": (
        "npm run lint:md",
        "npm run lint:md:links",
        "npm run lint:md:nested",
    ),
    "powershell": ("Invoke-Pester -Path tests/ -Output Detailed",),
    "python": (
        "pytest tests/ -v --cov --cov-report=term-missing",
        "pre-commit run check-toml --all-files",
    ),
    "schema": (
        "pre-commit run validate-example-config-valid-examples --all-files",
        "pre-commit run validate-example-config-schema --all-files",
        "pytest tests/test_schema_examples.py -v",
    ),
    "template-onboarding": (
        "npm run lint:md",
        "npm run lint:md:links",
        "npm run lint:md:nested",
    ),
    "template-sync-support": (
        "python .template-sync/scripts/validate_marker.py --require-marker",
        "python .template-sync/scripts/validate_instruction_contracts.py --mode downstream --require-marker",
        "pre-commit run validate-template-sync-marker-valid-examples --all-files",
        "pre-commit run validate-template-sync-instruction-contracts-valid-examples --all-files",
        "pre-commit run validate-template-sync-manifest-schema --all-files",
        "pre-commit run validate-template-sync-marker-schema --all-files",
        "pre-commit run validate-template-sync-instruction-contracts-schema --all-files",
        "pre-commit run validate-template-sync-manifest --all-files",
        "pre-commit run validate-template-sync-marker --all-files",
        "pre-commit run validate-template-sync-instruction-contracts --all-files",
        "pre-commit run validate-instruction-contracts-upstream --all-files",
        "pre-commit run validate-instruction-contracts-downstream --all-files",
        "pytest tests/test_schema_examples.py -v",
    ),
    "terraform": (
        "terraform fmt -check -recursive -diff",
        "tflint --init",
        'tflint --recursive --config "$(pwd)/.tflint.hcl"',
        "terraform test -verbose",
        "pytest tests/test_terraform_hooks.py -v",
    ),
    "yaml": (
        "pre-commit run check-yaml --all-files",
        "pre-commit run yamllint --all-files",
    ),
}


class CandidateGenerationError(Exception):
    """Raised when a sync candidate table cannot be generated."""


@dataclass(frozen=True)
class MarkerData:
    """Marker values needed to evaluate changed upstream paths."""

    last_reviewed_template_commit: str | None
    included_modules: frozenset[str]
    local_overrides: tuple[LocalOverride, ...]
    deferred_candidates: tuple[DeferredProtectedCandidate, ...]
    protected_decisions: tuple[ProtectedFileDecision, ...]


@dataclass(frozen=True)
class DiffEntry:
    """One path-level change from ``git diff --name-status``."""

    status: str
    path: str
    old_path: str | None = None

    @property
    def display_path(self) -> str:
        """Return the path text shown in the candidate table."""
        if self.old_path is None:
            return self.path
        return f"{self.old_path} -> {self.path}"

    @property
    def change_kind(self) -> str:
        """Return a human-readable change kind."""
        status_code = self.status[0]
        if status_code == "A":
            return "Added"
        if status_code == "C":
            return f"Copied ({self.status})"
        if status_code == "D":
            return "Deleted"
        if status_code == "M":
            return "Modified"
        if status_code == "R":
            return f"Renamed ({self.status})"
        if status_code == "T":
            return "Type changed"
        return self.status


@dataclass(frozen=True)
class CandidateRow:
    """A rendered decision-aid row for one changed path."""

    path: str
    change: str
    module_relation: str
    retained_status: str
    local_override_status: str
    deferred_status: str
    protected_decision_status: str
    protected_status: str
    notes: tuple[str, ...]


@dataclass(frozen=True)
class TodoItem:
    """One first-adoption checklist item that can be linked from the ledger."""

    line_number: int
    text: str
    is_complete: bool


@dataclass(frozen=True)
class SummaryTodoItem:
    """One machine-interpretable unchecked checklist item for the concise summary."""

    line_number: int
    section: str
    text: str


@dataclass(frozen=True)
class SummaryTodoState:
    """Machine-interpretability state for the first-adoption checklist summary."""

    exists: bool
    is_interpretable: bool
    unchecked_items: tuple[SummaryTodoItem, ...]


@dataclass(frozen=True)
class LedgerRow:
    """A rendered adoption-ledger row for one manifest or manual setup item."""

    path: str
    manifest_modules: str
    decision: str
    reason: str
    protected_file: str
    requires_maintainer_decision: str
    adoption_mode: str
    todo_link: str
    validation_commands: str


@dataclass(frozen=True)
class RemoteInfo:
    """One configured Git remote discovered from local repository state."""

    name: str
    url: str
    purpose: str


@dataclass(frozen=True)
class GitHubMetadata:
    """Optional GitHub metadata discovered only after explicit opt-in."""

    requested: bool
    available: bool
    source: str
    repository: str | None = None
    visibility: str | None = None
    default_branch: str | None = None
    discussions_enabled: str | None = None
    labels: tuple[str, ...] = ()
    error: str | None = None


@dataclass(frozen=True)
class RepositoryDiscovery:
    """Read-only local repository state for the first-adoption preflight report."""

    owner_name: str | None
    remotes: tuple[RemoteInfo, ...]
    current_branch: str | None
    likely_default_branch: str | None
    working_tree_entries: tuple[str, ...]
    workflows: tuple[str, ...]
    issue_templates: tuple[str, ...]
    pr_templates: tuple[str, ...]
    security_files: tuple[str, ...]
    agent_instruction_files: tuple[str, ...]
    tooling_stacks: tuple[str, ...]
    marker_present: bool
    adoption_note_present: bool
    github_metadata: GitHubMetadata


CommandRunner = Callable[[Path, list[str]], subprocess.CompletedProcess[str]]


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Generate a Markdown template sync candidate table from the marker, "
            "manifest, and upstream git range."
        )
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help=(
            "Repository root to inspect. Defaults to the parent of the .template-sync "
            "directory that contains this script."
        ),
    )
    parser.add_argument(
        "--marker",
        default=DEFAULT_MARKER_PATH,
        help=f"Marker path relative to the repository root. Default: {DEFAULT_MARKER_PATH}",
    )
    parser.add_argument(
        "--manifest",
        default=DEFAULT_MANIFEST_PATH,
        help=f"Manifest path relative to the repository root. Default: {DEFAULT_MANIFEST_PATH}",
    )
    parser.add_argument(
        "--marker-schema",
        default=DEFAULT_MARKER_SCHEMA_PATH,
        help=(
            "Marker JSON Schema path relative to the repository root. "
            f"Default: {DEFAULT_MARKER_SCHEMA_PATH}"
        ),
    )
    parser.add_argument(
        "--manifest-schema",
        default=DEFAULT_MANIFEST_SCHEMA_PATH,
        help=(
            "Manifest JSON Schema path relative to the repository root. "
            f"Default: {DEFAULT_MANIFEST_SCHEMA_PATH}"
        ),
    )
    parser.add_argument(
        "--range-base",
        default=None,
        help=(
            "Base commit or ref for the upstream comparison. Defaults to "
            "template_sync.last_reviewed_template_commit from the marker."
        ),
    )
    parser.add_argument(
        "--range-head",
        default=None,
        help=(
            "Head commit or ref for the upstream comparison. Defaults to the local "
            "template/main ref when it is present. The helper does not fetch."
        ),
    )
    parser.add_argument(
        "--write-candidates",
        default=None,
        metavar="PATH",
        help=(
            "Write the rendered candidate table to PATH while still printing the full "
            "report to stdout. PATH must stay inside the repository root."
        ),
    )
    ledger_mode_group = parser.add_mutually_exclusive_group()
    ledger_mode_group.add_argument(
        "--ledger",
        action="store_true",
        help=(
            "Include a generated adoption ledger in stdout after the candidate table. "
            "The ledger is a review artifact only."
        ),
    )
    ledger_mode_group.add_argument(
        "--ledger-only",
        action="store_true",
        help=(
            "Emit only the generated adoption ledger and skip git range inspection. "
            "Use this for first-adoption or full-reconciliation review when a delta "
            "candidate table is not available."
        ),
    )
    ledger_mode_group.add_argument(
        "--summary",
        action="store_true",
        help=(
            "Emit a concise deterministic template adoption summary for PR "
            "descriptions and skip git range inspection."
        ),
    )
    ledger_mode_group.add_argument(
        "--preflight",
        "--questionnaire",
        action="store_true",
        dest="preflight",
        help=(
            "Emit a read-only first-adoption preflight report, maintainer "
            "questionnaire, _TODO-repo-init.md starter, and reused adoption ledger. "
            "This mode skips git range inspection and never writes files."
        ),
    )
    parser.add_argument(
        "--write-ledger",
        default=None,
        metavar="PATH",
        help=(
            "Write the generated adoption ledger snapshot to PATH. PATH must stay "
            "inside the repository root."
        ),
    )
    parser.add_argument(
        "--todo-file",
        default=DEFAULT_TODO_PATH,
        help=(
            "First-adoption checklist path relative to the repository root. "
            f"Default: {DEFAULT_TODO_PATH}"
        ),
    )
    parser.add_argument(
        "--adoption-mode",
        choices=("minimal-preservation", "tailored"),
        default="minimal-preservation",
        help=(
            "Default adoption mode to show for protected and template-derived files "
            "in the generated ledger. Default: minimal-preservation"
        ),
    )
    parser.add_argument(
        "--include-github-metadata",
        action="store_true",
        help=(
            "Opt in to read-only GitHub metadata lookup through the gh CLI for the "
            "preflight report. Without this flag, GitHub-only settings are labeled "
            "manual review required."
        ),
    )
    return parser.parse_args(argv)


def run_git(
    repo_root: Path, args: list[str], *, check: bool = True
) -> subprocess.CompletedProcess[str]:
    """Run a read-only Git command in ``repo_root``."""
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"
        raise CandidateGenerationError(f"git {' '.join(args)} failed: {detail}")
    return result


def run_command(repo_root: Path, command: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a read-only discovery command in ``repo_root``."""
    return subprocess.run(
        command,
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )


def command_detail(result: subprocess.CompletedProcess[str]) -> str:
    """Return a short diagnostic string from a command result."""
    for stream_text in (result.stderr, result.stdout):
        for line in stream_text.splitlines():
            if line.strip():
                return line.strip()
    return f"exit {result.returncode}"


def os_error_summary(error: OSError) -> str:
    """Return an OSError summary that avoids exposing implicit filesystem paths."""
    return f"{type(error).__name__}: {error.strerror or 'I/O error'}"


def git_ref_exists(repo_root: Path, raw_ref: str) -> bool:
    """Return whether ``raw_ref`` resolves to a local commit."""
    result = run_git(
        repo_root,
        ["rev-parse", "--verify", "--end-of-options", f"{raw_ref}^{{commit}}"],
        check=False,
    )
    return result.returncode == 0


def resolve_commit(repo_root: Path, raw_ref: str, label: str) -> str:
    """Resolve a commit-ish ref to a full commit SHA."""
    result = run_git(
        repo_root,
        ["rev-parse", "--verify", "--end-of-options", f"{raw_ref}^{{commit}}"],
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "not found"
        raise CandidateGenerationError(
            f"Unable to resolve {label} {raw_ref!r} to a commit: {detail}"
        )
    return result.stdout.strip().splitlines()[0]


def resolve_range_head_ref(repo_root: Path, raw_range_head: str | None) -> tuple[str, str]:
    """Resolve the requested range head or the local default ref."""
    if raw_range_head is not None:
        return raw_range_head, resolve_commit(repo_root, raw_range_head, "range head")

    if git_ref_exists(repo_root, DEFAULT_RANGE_HEAD_REF):
        return (
            DEFAULT_RANGE_HEAD_REF,
            resolve_commit(repo_root, DEFAULT_RANGE_HEAD_REF, "range head"),
        )

    raise CandidateGenerationError(
        "No --range-head was supplied and local template/main was not found. "
        "Fetch the template remote first or pass --range-head explicitly."
    )


def resolve_range_base_ref(
    repo_root: Path,
    raw_range_base: str | None,
    marker_data: MarkerData,
) -> tuple[str, str, str]:
    """Resolve the comparison base from CLI input or marker state."""
    if raw_range_base is not None:
        return (
            raw_range_base,
            resolve_commit(repo_root, raw_range_base, "range base"),
            "--range-base",
        )

    marker_base = marker_data.last_reviewed_template_commit
    if marker_base:
        return (
            marker_base,
            resolve_commit(
                repo_root,
                marker_base,
                "marker template_sync.last_reviewed_template_commit",
            ),
            "marker template_sync.last_reviewed_template_commit",
        )

    raise CandidateGenerationError(
        "No range base was provided and .template-sync/marker.yml does not set "
        "template_sync.last_reviewed_template_commit. Pass --range-base for a "
        "first-sync delta review; this helper will not guess a baseline."
    )


def verify_reachable_range(repo_root: Path, range_base_sha: str, range_head_sha: str) -> None:
    """Reject a range whose base is not an ancestor of its head."""
    result = run_git(
        repo_root,
        ["merge-base", "--is-ancestor", range_base_sha, range_head_sha],
        check=False,
    )
    if result.returncode == 0:
        return
    if result.returncode == 1:
        raise CandidateGenerationError(
            f"Range base {range_base_sha} is not an ancestor of range head {range_head_sha}."
        )
    detail = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"
    raise CandidateGenerationError(f"Unable to check range reachability: {detail}")


def parse_name_status_line(line: str) -> DiffEntry:
    """Parse one ``git diff --name-status`` line."""
    parts = line.split("\t")
    if len(parts) < 2:
        raise CandidateGenerationError(f"Unexpected git diff --name-status line: {line!r}")

    status = parts[0]
    status_code = status[0]
    if status_code in {"R", "C"}:
        if len(parts) != 3:
            raise CandidateGenerationError(f"Unexpected rename/copy diff line: {line!r}")
        return DiffEntry(status=status, old_path=parts[1], path=parts[2])

    return DiffEntry(status=status, path=parts[1])


def changed_paths(
    repo_root: Path, range_base_sha: str, range_head_sha: str
) -> tuple[DiffEntry, ...]:
    """Return upstream path changes for ``range_base_sha..range_head_sha``."""
    result = run_git(
        repo_root,
        [
            "diff",
            "--name-status",
            "-M",
            f"{range_base_sha}..{range_head_sha}",
            "--",
        ],
    )
    entries = [parse_name_status_line(line) for line in result.stdout.splitlines() if line.strip()]
    return tuple(entries)


def modeled_diff_command(range_base_sha: str, range_head_sha: str) -> str:
    """Return the copyable diff command modeled by candidate generation."""
    return f"git diff --name-status -M {range_base_sha}..{range_head_sha} --"


def stale_procedure_warning(repo_root: Path, range_head_sha: str) -> str | None:
    """Return a warning when the local procedure differs from range-head upstream."""
    upstream_result = run_git(
        repo_root,
        ["show", f"{range_head_sha}:{TEMPLATE_UPDATE_PROCEDURE_PATH}"],
        check=False,
    )
    if upstream_result.returncode != 0:
        return None

    local_path = repo_root / TEMPLATE_UPDATE_PROCEDURE_PATH
    show_command = f"git show {range_head_sha}:{TEMPLATE_UPDATE_PROCEDURE_PATH}"
    try:
        local_text = local_path.read_text(encoding="utf-8")
    except OSError as error:
        error_summary = f"{type(error).__name__}: {error.strerror or 'I/O error'}"
        return (
            f"WARNING: Unable to read local `{TEMPLATE_UPDATE_PROCEDURE_PATH}` "
            f"for comparison with range head `{range_head_sha}`: {error_summary}. "
            f"Review the current upstream procedure with `{show_command}` before "
            "following local procedure text."
        )

    if local_text == upstream_result.stdout:
        return None

    return (
        f"WARNING: Local `{TEMPLATE_UPDATE_PROCEDURE_PATH}` may be stale; it differs "
        f"from the upstream copy at range head `{range_head_sha}`. Review the current "
        f"upstream procedure with `{show_command}` before following local procedure text."
    )


def parse_marker(marker: dict[str, Any]) -> MarkerData:
    """Extract marker fields needed for candidate generation."""
    marker_data = parse_marker_decision_data(
        marker,
        validate_protected_decision_integrity=True,
    )

    return MarkerData(
        last_reviewed_template_commit=marker_data.last_reviewed_template_commit,
        included_modules=marker_data.included_modules,
        local_overrides=marker_data.local_overrides,
        deferred_candidates=marker_data.deferred_candidates,
        protected_decisions=marker_data.protected_decisions,
    )


def parse_manifest(manifest: dict[str, Any]) -> tuple[frozenset[str], tuple[ManifestMapping, ...]]:
    """Extract manifest modules and mapping rows without making owner decisions."""
    return parse_manifest_mappings(manifest, reject_unknown_modules=False)


def describe_relation(relation: PathRelation | None) -> str:
    """Return a human-readable module relation description, or ``unmapped``."""
    return relation.description if relation is not None else "unmapped"


def relations_match(left: PathRelation | None, right: PathRelation | None) -> bool:
    """Return whether two relations resolve to the same module mapping."""
    if left is None or right is None:
        return left is None and right is None
    return left.requires_all == right.requires_all and left.requires_any == right.requires_any


def matching_local_overrides_for_pattern(
    pattern: str,
    local_overrides: tuple[LocalOverride, ...],
) -> tuple[LocalOverride, ...]:
    """Return marker local overrides that apply to a manifest pattern."""
    matches: list[LocalOverride] = []
    for local_override in local_overrides:
        if not has_wildcard(pattern) and local_override.matches(pattern):
            matches.append(local_override)
            continue
        if local_override.is_directory and pattern.startswith(f"{local_override.path}/"):
            matches.append(local_override)
            continue
        if local_override.path == pattern:
            matches.append(local_override)
    return tuple(matches)


def matching_deferred_candidates_for_pattern(
    pattern: str,
    deferred_candidates: tuple[DeferredProtectedCandidate, ...],
) -> tuple[DeferredProtectedCandidate, ...]:
    """Return deferred protected candidates that apply to a manifest pattern."""
    return tuple(
        candidate
        for candidate in deferred_candidates
        if manifest_pattern_matches_path(pattern, candidate.path)
    )


def matching_protected_decisions_for_pattern(
    pattern: str,
    protected_decisions: tuple[ProtectedFileDecision, ...],
) -> tuple[ProtectedFileDecision, ...]:
    """Return protected-file decisions that apply to a manifest pattern."""
    return tuple(
        protected_decision
        for protected_decision in protected_decisions
        if manifest_pattern_matches_path(pattern, protected_decision.path)
    )


def matching_local_overrides(
    entry: DiffEntry,
    local_overrides: tuple[LocalOverride, ...],
) -> tuple[LocalOverride, ...]:
    """Return marker local overrides that match the changed path."""
    paths = [entry.path]
    if entry.old_path is not None:
        paths.append(entry.old_path)
    matches: list[LocalOverride] = []
    for local_override in local_overrides:
        if local_override in matches:
            continue
        if any(local_override.matches(path) for path in paths):
            matches.append(local_override)
    return tuple(matches)


def matching_deferred_candidates(
    entry: DiffEntry,
    deferred_candidates: tuple[DeferredProtectedCandidate, ...],
) -> tuple[DeferredProtectedCandidate, ...]:
    """Return marker deferred protected candidates that match the changed path."""
    paths = {entry.path}
    if entry.old_path is not None:
        paths.add(entry.old_path)
    return tuple(candidate for candidate in deferred_candidates if candidate.path in paths)


def matching_protected_decisions(
    entry: DiffEntry,
    protected_decisions: tuple[ProtectedFileDecision, ...],
) -> tuple[ProtectedFileDecision, ...]:
    """Return marker protected-file decisions that match the changed path."""
    paths = {entry.path}
    if entry.old_path is not None:
        paths.add(entry.old_path)
    return tuple(decision for decision in protected_decisions if decision.path in paths)


def protected_decision_status(
    protected_decisions: tuple[ProtectedFileDecision, ...],
) -> str:
    """Return candidate-table status text for matching protected decisions."""
    if not protected_decisions:
        return "None"
    return "; ".join(protected_decision_summary(decision) for decision in protected_decisions)


def build_candidate_row(
    entry: DiffEntry,
    marker_data: MarkerData,
    mappings: tuple[ManifestMapping, ...],
) -> CandidateRow:
    """Build one Markdown candidate row from marker and manifest context."""
    relation = selected_relation_for_path(entry.path, mappings)
    notes: list[str] = []

    if relation is None:
        module_relation = "UNMAPPED"
        retained_status = "Unmapped"
        notes.append("Unmapped path; owner must assign or confirm a module before final review.")
    else:
        module_relation = relation.description
        retained_status = (
            "Retained" if relation.is_retained_by(marker_data.included_modules) else "Excluded"
        )
        if retained_status == "Excluded":
            notes.append("Excluded by marker included_modules.")
        if relation.unknown_modules:
            notes.append("Unknown module(s): " + ", ".join(sorted(relation.unknown_modules)) + ".")
        if relation.is_cross_module:
            notes.append("Cross-module manifest relation matched.")
        for manifest_note in relation.notes:
            notes.append(f"Manifest note: {manifest_note}")

    local_overrides = matching_local_overrides(entry, marker_data.local_overrides)
    if local_overrides:
        local_override_status = "; ".join(
            f"{override.default_decision}: {override.reason}" for override in local_overrides
        )
        notes.append("Local override present; use it as a default, not an automatic decision.")
    else:
        local_override_status = "None"

    deferred_candidates = matching_deferred_candidates(entry, marker_data.deferred_candidates)
    if deferred_candidates:
        deferred_status = "; ".join(
            f"{candidate.source_commit}: {candidate.reason}" for candidate in deferred_candidates
        )
    else:
        deferred_status = "None"

    protected_decisions = matching_protected_decisions(entry, marker_data.protected_decisions)
    protected_decision_text = protected_decision_status(protected_decisions)
    if protected_decisions:
        notes.append("Protected file decision record present in marker.")

    protected_paths = [entry.path]
    if entry.old_path is not None:
        protected_paths.append(entry.old_path)
        is_copy = entry.status.startswith("C")
        change_verb = "Copied" if is_copy else "Renamed"
        change_noun = "Copy" if is_copy else "Rename"
        notes.append(f"{change_verb} from {entry.old_path}.")
        old_relation = selected_relation_for_path(entry.old_path, mappings)
        if not relations_match(old_relation, relation):
            notes.append(
                f"{change_noun} crosses module mapping boundaries: old path resolves to "
                f"{describe_relation(old_relation)}; new path resolves to "
                f"{describe_relation(relation)}. Review both mappings before deciding."
            )
    protected_status = (
        "Yes" if any(is_protected_instruction_path(path) for path in protected_paths) else "No"
    )
    if protected_status == "Yes":
        notes.append(
            "Protected instruction/governance file; explicit owner authorization is required."
        )

    if entry.status.startswith("D"):
        notes.append("Upstream deletion; owner must decide whether to remove the local file.")

    return CandidateRow(
        path=entry.display_path,
        change=entry.change_kind,
        module_relation=module_relation,
        retained_status=retained_status,
        local_override_status=local_override_status,
        deferred_status=deferred_status,
        protected_decision_status=protected_decision_text,
        protected_status=protected_status,
        notes=tuple(notes),
    )


def format_manifest_modules(requires_all: frozenset[str], requires_any: frozenset[str]) -> str:
    """Return a compact module relation summary for the adoption ledger."""
    parts: list[str] = []
    if requires_all:
        parts.append("all: " + ", ".join(sorted(requires_all)))
    if requires_any:
        parts.append("any: " + ", ".join(sorted(requires_any)))
    return "; ".join(parts) if parts else "none"


def relation_module_names(mapping: ManifestMapping) -> frozenset[str]:
    """Return all manifest modules referenced by ``mapping``."""
    return mapping.requires_all | mapping.requires_any


def validation_commands_for_modules(modules: frozenset[str]) -> str:
    """Return validation commands affected by a set of manifest modules."""
    commands: list[str] = []
    for module in sorted(modules):
        for command in VALIDATION_COMMANDS_BY_MODULE.get(module, ()):
            if command not in commands:
                commands.append(command)
    return "<br>".join(commands) if commands else "manual review"


def local_override_reason(local_overrides: tuple[LocalOverride, ...]) -> str:
    """Return the ledger reason text for matching local overrides."""
    return "; ".join(
        f"Marker local override defaults to `{override.default_decision}`: {override.reason}"
        for override in local_overrides
    )


def protected_decision_reason(
    protected_decisions: tuple[ProtectedFileDecision, ...],
    local_overrides: tuple[LocalOverride, ...] = (),
) -> str:
    """Return ledger reason text for matching protected-file decisions."""
    reason_parts: list[str] = []
    for protected_decision in protected_decisions:
        if protected_decision.decision in {"TAKE", "MERGE"}:
            if protected_decision.adoption_mode == "tailored":
                reason_parts.append("Authorized tailored protected-file rewrite.")
            else:
                reason_parts.append("Authorized minimal-preservation protected-file edit.")
            reason_parts.append(f"authorization_basis: {protected_decision.authorization_basis}")
            reason_parts.append(f"authorized_scope: {protected_decision.authorized_scope}")
            if protected_decision.tailored_authorization_basis is not None:
                reason_parts.append(
                    "tailored_authorization_basis: "
                    f"{protected_decision.tailored_authorization_basis}"
                )
        elif protected_decision.decision == REMOVAL_DECISION:
            reason_parts.append(
                "Authorized protected-file removal; see REMOVE-LOCAL authorizations section."
            )
        else:
            reason = protected_decision.reason or "No reason recorded."
            reason_parts.append(f"Protected decision `{protected_decision.decision}`: {reason}")

    for local_override in local_overrides:
        reason_parts.append(f"Overlapping local override: {local_override_summary(local_override)}")

    return " ".join(reason_parts)


def protected_decision_requires_maintainer_decision(
    protected_decisions: tuple[ProtectedFileDecision, ...],
) -> bool:
    """Return whether matching protected decisions still require maintainer action."""
    return any(
        decision.decision in {"DEFER", "PROTECTED-REVIEW"} for decision in protected_decisions
    )


def protected_decision_adoption_mode(
    protected_decisions: tuple[ProtectedFileDecision, ...],
) -> str:
    """Return the adoption-mode ledger value for protected decisions."""
    modes: list[str] = []
    for protected_decision in protected_decisions:
        if protected_decision.adoption_mode == "tailored":
            modes.append("tailored (authorized protected-file decision)")
        elif protected_decision.adoption_mode == "minimal-preservation":
            modes.append("minimal-preservation (protected-file decision)")
        elif protected_decision.decision == REMOVAL_DECISION:
            modes.append("not applicable (authorized removal)")
        else:
            modes.append("not applicable")
    return "; ".join(dict.fromkeys(modes))


def has_trim_note(notes: tuple[str, ...]) -> bool:
    """Return whether manifest notes indicate module-scoped trim work."""
    return any(keyword in note.lower() for note in notes for keyword in INLINE_TRIM_NOTE_KEYWORDS)


def notes_mention_modules(notes: tuple[str, ...], modules: frozenset[str]) -> bool:
    """Return whether manifest notes mention any module in ``modules``."""
    normalized_notes = " ".join(notes).lower()
    return any(
        module in normalized_notes or module.replace("-", " ") in normalized_notes
        for module in modules
    )


def retention_gap_reason(mapping: ManifestMapping, included_modules: frozenset[str]) -> str:
    """Return why a manifest mapping is not retained by included modules."""
    missing_all = mapping.requires_all - included_modules
    if missing_all:
        return "Required module(s) not included: " + ", ".join(sorted(missing_all)) + "."
    if mapping.requires_any and not mapping.requires_any.intersection(included_modules):
        return (
            "None of the required alternative module(s) are included: "
            + ", ".join(sorted(mapping.requires_any))
            + "."
        )
    return "Excluded by marker included_modules."


def adoption_mode_for_modules(
    modules: frozenset[str],
    local_overrides: tuple[LocalOverride, ...],
    is_protected: bool,
    default_adoption_mode: str,
) -> str:
    """Return the adoption mode displayed for a ledger row."""
    for local_override in local_overrides:
        lowered_reason = local_override.reason.lower()
        if "tailored" in lowered_reason:
            return "tailored (marker local override)"
        if "minimal-preservation" in lowered_reason:
            return "minimal-preservation (marker local override)"

    if is_protected or modules.intersection(ADOPTION_MODE_MODULES):
        return default_adoption_mode
    return "not applicable"


def todo_link_target(
    todo_path: Path,
    repo_root: Path,
    ledger_output_dir: Path | None,
) -> str:
    """Return the link target string for the checklist file.

    When ``ledger_output_dir`` is provided, the target is computed relative to
    that directory so the link resolves correctly when the rendered ledger is
    committed under it. Otherwise the target is repo-root-relative, which is
    informative when reading the ledger in a terminal but is not a clickable
    link to the checklist file when the ledger is rendered from a PR or issue
    body (GitHub resolves relative Markdown link targets in PR/issue bodies
    relative to the PR/issue URL, not the repository root). Callers that need
    clickable rendered links should pass ``ledger_output_dir`` and commit the
    saved ledger so it is rendered under that directory on GitHub.
    """
    if ledger_output_dir is None:
        return repository_relative_path(todo_path, repo_root)
    return os.path.relpath(str(todo_path), str(ledger_output_dir)).replace(os.sep, "/")


def todo_item_link(
    todo_path: Path,
    repo_root: Path,
    item: TodoItem,
    ledger_output_dir: Path | None = None,
) -> str:
    """Return a Markdown link to one checklist line."""
    todo_relative = todo_link_target(todo_path, repo_root, ledger_output_dir)
    return f"[line {item.line_number}]({todo_relative}#L{item.line_number})"


def matching_todo_links(
    *,
    path: str,
    modules: frozenset[str],
    is_protected: bool,
    todo_items: tuple[TodoItem, ...],
    todo_path: Path,
    repo_root: Path,
    ledger_output_dir: Path | None = None,
) -> str:
    """Return links to first-adoption checklist rows relevant to a ledger row."""
    if not todo_items:
        return "None"

    normalized_path = path.rstrip("/")
    path_parts = [normalized_path.lower()]
    if "/" in normalized_path:
        path_parts.append(normalized_path.rsplit("/", maxsplit=1)[-1].lower())
    needles = set(path_parts)
    needles.update(module.lower() for module in modules)
    if is_protected:
        needles.update({"protected", "adoption mode"})

    links: list[str] = []
    for item in todo_items:
        text = item.text.lower()
        if any(needle and needle in text for needle in needles):
            links.append(todo_item_link(todo_path, repo_root, item, ledger_output_dir))

    if not links:
        return "None"
    if len(links) > TODO_LINK_LIMIT:
        visible_links = links[:TODO_LINK_LIMIT]
        visible_links.append(f"{len(links) - TODO_LINK_LIMIT} more")
        return ", ".join(visible_links)
    return ", ".join(links)


def load_todo_items(todo_path: Path, repo_root: Path) -> tuple[TodoItem, ...]:
    """Load checkbox items from the first-adoption checklist when it exists."""
    if not todo_path.exists():
        return ()
    try:
        lines = todo_path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        todo_relative = repository_relative_path(todo_path, repo_root)
        error_summary = f"{type(error).__name__}: {error.strerror or 'I/O error'}"
        raise CandidateGenerationError(
            f"Unable to read adoption checklist {todo_relative}: {error_summary}"
        ) from error

    items: list[TodoItem] = []
    for line_number, line in enumerate(lines, start=1):
        match = re.match(r"^\s*[-*]\s+\[(?P<status>[ xX])\]\s+(?P<text>.+?)\s*$", line)
        if match is None:
            continue
        items.append(
            TodoItem(
                line_number=line_number,
                text=match.group("text"),
                is_complete=match.group("status").lower() == "x",
            )
        )
    return tuple(items)


def load_summary_todo_state(todo_path: Path, repo_root: Path) -> SummaryTodoState:
    """Load unchecked checklist items only from the documented TODO shape."""
    if not todo_path.exists():
        return SummaryTodoState(exists=False, is_interpretable=True, unchecked_items=())
    try:
        lines = todo_path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        todo_relative = repository_relative_path(todo_path, repo_root)
        error_summary = f"{type(error).__name__}: {error.strerror or 'I/O error'}"
        raise CandidateGenerationError(
            f"Unable to read adoption checklist {todo_relative}: {error_summary}"
        ) from error

    first_content_line = next(
        (line.strip() for line in lines if line.strip()),
        None,
    )
    has_documented_title = first_content_line == "# Repository Initialization Checklist"
    current_section: str | None = None
    found_known_section = False
    unchecked_items: list[SummaryTodoItem] = []
    known_sections = frozenset(TODO_KNOWN_SECTIONS)

    for line_number, line in enumerate(lines, start=1):
        heading_match = re.match(r"^##\s+(?P<section>.+?)\s*$", line)
        if heading_match is not None:
            section = heading_match.group("section")
            current_section = section if section in known_sections else None
            found_known_section = found_known_section or current_section is not None
            continue

        if current_section is None:
            continue

        task_match = re.match(
            r"^\s*[-*]\s+\[(?P<status>[ xX])\]\s+(?P<text>.+?)\s*$",
            line,
        )
        if task_match is None or task_match.group("status").lower() == "x":
            continue

        unchecked_items.append(
            SummaryTodoItem(
                line_number=line_number,
                section=current_section,
                text=task_match.group("text"),
            )
        )

    is_interpretable = has_documented_title and found_known_section
    return SummaryTodoState(
        exists=True,
        is_interpretable=is_interpretable,
        unchecked_items=tuple(unchecked_items) if is_interpretable else (),
    )


def empty_marker_data() -> MarkerData:
    """Return marker data for repositories that have not created a marker yet."""
    return MarkerData(
        last_reviewed_template_commit=None,
        included_modules=frozenset(),
        local_overrides=(),
        deferred_candidates=(),
        protected_decisions=(),
    )


def load_preflight_inputs(
    repo_root: Path,
    marker_path: Path,
    manifest_path: Path,
    marker_schema_path: Path,
    manifest_schema_path: Path,
) -> tuple[MarkerData, frozenset[str], tuple[ManifestMapping, ...]]:
    """Load manifest state and optional marker state for preflight reporting."""
    manifest = load_yaml_mapping(manifest_path, repo_root)
    manifest_schema = load_json_mapping(manifest_schema_path, repo_root)
    validate_schema(manifest, manifest_schema, manifest_path, repo_root)
    manifest_modules, mappings = parse_manifest(manifest)

    if not marker_path.exists():
        return empty_marker_data(), manifest_modules, mappings

    marker = load_yaml_mapping(marker_path, repo_root)
    marker_schema = load_json_mapping(marker_schema_path, repo_root)
    validate_schema(marker, marker_schema, marker_path, repo_root)
    return parse_marker(marker), manifest_modules, mappings


def iter_repo_files(repo_root: Path) -> tuple[Path, ...]:
    """Return regular repository files without following symlinks."""
    trusted_root = repo_root.resolve()
    discovered: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(repo_root, followlinks=False):
        current_dir = Path(dirpath)
        kept_dirs: list[str] = []
        for dirname in dirnames:
            child_dir = current_dir / dirname
            if dirname in DISCOVERY_SKIP_DIRS or child_dir.is_symlink():
                continue
            try:
                child_dir.resolve().relative_to(trusted_root)
            except (OSError, ValueError):
                continue
            kept_dirs.append(dirname)
        dirnames[:] = kept_dirs

        for filename in filenames:
            child_file = current_dir / filename
            if child_file.is_symlink() or not child_file.is_file():
                continue
            try:
                child_file.resolve().relative_to(trusted_root)
            except (OSError, ValueError):
                continue
            discovered.append(child_file)
    return tuple(sorted(discovered))


def relative_file_set(repo_root: Path) -> frozenset[str]:
    """Return repository-relative file paths for stack discovery."""
    return frozenset(path.relative_to(repo_root).as_posix() for path in iter_repo_files(repo_root))


def list_existing_paths(repo_root: Path, candidates: tuple[str, ...]) -> tuple[str, ...]:
    """Return candidate paths that exist as non-symlink repository paths."""
    return tuple(path for path in candidates if repository_path_exists(repo_root, path))


def list_directory_files(
    repo_root: Path,
    relative_dir: str,
    suffixes: tuple[str, ...],
) -> tuple[str, ...]:
    """Return immediate files in a repository directory that match ``suffixes``."""
    if path_has_symlink_component(repo_root, relative_dir):
        return ()

    trusted_root = repo_root.resolve()
    directory = repo_root / relative_dir
    try:
        directory.resolve().relative_to(trusted_root)
    except (OSError, ValueError):
        return ()
    if not directory.is_dir():
        return ()

    paths: list[str] = []
    for child in sorted(directory.iterdir()):
        if child.is_symlink() or not child.is_file():
            continue
        if suffixes and child.suffix.lower() not in suffixes:
            continue
        try:
            child.resolve().relative_to(trusted_root)
        except (OSError, ValueError):
            continue
        paths.append(child.relative_to(repo_root).as_posix())
    return tuple(paths)


def parse_git_remotes(repo_root: Path) -> tuple[RemoteInfo, ...]:
    """Return configured Git remotes from local config."""
    result = run_git(repo_root, ["remote", "-v"], check=False)
    if result.returncode != 0:
        return ()

    remotes: list[RemoteInfo] = []
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) < 3:
            continue
        purpose = parts[2].strip("()")
        remotes.append(RemoteInfo(name=parts[0], url=parts[1], purpose=purpose))
    return tuple(remotes)


def is_github_host(host: str | None) -> bool:
    """Return whether ``host`` is ``github.com`` or a ``github.com`` subdomain."""
    if not host:
        return False
    host = host.lower()
    return host == "github.com" or host.endswith(".github.com")


def infer_repository_name(remotes: tuple[RemoteInfo, ...]) -> str | None:
    """Infer ``owner/name`` from a configured GitHub remote URL.

    The GitHub host is matched against the parsed URL authority (or the SCP-style
    host), never an arbitrary substring, so look-alike hosts such as
    ``notgithub.com`` or ``github.com.example.com`` are not misclassified as
    GitHub remotes.
    """
    for remote in remotes:
        if "://" in remote.url:
            try:
                parsed = urlsplit(remote.url)
            except ValueError:
                continue
            host, path = parsed.hostname, parsed.path
        else:
            scp_match = re.match(r"^(?:[^@/]+@)?(?P<host>[^/:]+):(?P<path>.+)$", remote.url)
            if scp_match is None:
                continue
            host, path = scp_match.group("host"), scp_match.group("path")
        if not is_github_host(host):
            continue
        segments = [segment for segment in path.split("/") if segment]
        if len(segments) < 2:
            continue
        owner, repo = segments[0], segments[1].removesuffix(".git")
        if owner and repo:
            return f"{owner}/{repo}"
    return None


def discover_github_metadata(
    repo_root: Path,
    owner_name: str | None,
    *,
    include_metadata: bool,
    command_runner: CommandRunner = run_command,
) -> GitHubMetadata:
    """Optionally discover GitHub metadata through explicit read-only ``gh`` calls."""
    if not include_metadata:
        return GitHubMetadata(
            requested=False,
            available=False,
            source="not requested",
        )

    if owner_name is None:
        return GitHubMetadata(
            requested=True,
            available=False,
            source="gh",
            error="Repository owner/name could not be inferred from local remotes.",
        )

    try:
        repo_result = command_runner(
            repo_root,
            [
                "gh",
                "repo",
                "view",
                owner_name,
                "--json",
                "nameWithOwner,visibility,defaultBranchRef,hasDiscussionsEnabled",
            ],
        )
    except OSError as error:
        return GitHubMetadata(
            requested=True,
            available=False,
            source="gh",
            error=os_error_summary(error),
        )

    if repo_result.returncode != 0:
        return GitHubMetadata(
            requested=True,
            available=False,
            source="gh",
            error=command_detail(repo_result),
        )

    try:
        payload = json.loads(repo_result.stdout)
    except json.JSONDecodeError as error:
        return GitHubMetadata(
            requested=True,
            available=False,
            source="gh",
            error=f"Unable to parse gh repo view JSON: {error.msg}",
        )

    if not isinstance(payload, dict):
        return GitHubMetadata(
            requested=True,
            available=False,
            source="gh",
            error="gh repo view returned a non-object JSON payload.",
        )

    default_branch_ref = payload.get("defaultBranchRef")
    default_branch = None
    if isinstance(default_branch_ref, dict) and isinstance(default_branch_ref.get("name"), str):
        default_branch = default_branch_ref["name"]

    labels: tuple[str, ...] = ()
    labels_error: str | None = None
    try:
        labels_result = command_runner(
            repo_root,
            [
                "gh",
                "label",
                "list",
                "--repo",
                owner_name,
                "--limit",
                "100",
                "--json",
                "name",
            ],
        )
    except OSError as error:
        labels_error = os_error_summary(error)
    else:
        if labels_result.returncode == 0:
            try:
                raw_labels = json.loads(labels_result.stdout)
            except json.JSONDecodeError as error:
                labels_error = f"Unable to parse gh label list JSON: {error.msg}"
            else:
                if isinstance(raw_labels, list):
                    labels = tuple(
                        sorted(
                            label["name"]
                            for label in raw_labels
                            if isinstance(label, dict) and isinstance(label.get("name"), str)
                        )
                    )
        else:
            labels_error = command_detail(labels_result)

    discussions_value = payload.get("hasDiscussionsEnabled")
    discussions_enabled = None
    if isinstance(discussions_value, bool):
        discussions_enabled = "enabled" if discussions_value else "disabled"

    metadata_error = (
        f"Label metadata unavailable: {labels_error}" if labels_error is not None else None
    )
    return GitHubMetadata(
        requested=True,
        available=True,
        source="gh",
        repository=(
            payload["nameWithOwner"] if isinstance(payload.get("nameWithOwner"), str) else None
        ),
        visibility=payload["visibility"] if isinstance(payload.get("visibility"), str) else None,
        default_branch=default_branch,
        discussions_enabled=discussions_enabled,
        labels=labels,
        error=metadata_error,
    )


def current_branch(repo_root: Path) -> str | None:
    """Return the current branch name, or detached HEAD when applicable."""
    result = run_git(repo_root, ["branch", "--show-current"], check=False)
    branch = result.stdout.strip()
    if result.returncode == 0 and branch:
        return branch

    detached = run_git(repo_root, ["rev-parse", "--short", "HEAD"], check=False)
    if detached.returncode == 0 and detached.stdout.strip():
        return f"detached at {detached.stdout.strip()}"
    return None


def likely_default_branch(repo_root: Path, github_metadata: GitHubMetadata) -> str | None:
    """Return the likely default branch from local remote refs or metadata."""
    result = run_git(
        repo_root,
        ["symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"],
        check=False,
    )
    remote_head = result.stdout.strip()
    if result.returncode == 0 and remote_head:
        return remote_head.split("/", maxsplit=1)[-1]
    return github_metadata.default_branch


def working_tree_entries(repo_root: Path) -> tuple[str, ...]:
    """Return porcelain working-tree entries."""
    result = run_git(repo_root, ["status", "--short"], check=False)
    if result.returncode != 0:
        return (f"status unavailable: {command_detail(result)}",)
    return tuple(line for line in result.stdout.splitlines() if line.strip())


def discover_workflows(repo_root: Path) -> tuple[str, ...]:
    """Return existing GitHub Actions workflow files."""
    return list_directory_files(repo_root, ".github/workflows", (".yml", ".yaml"))


def discover_issue_templates(repo_root: Path) -> tuple[str, ...]:
    """Return existing issue-template files."""
    direct_templates = list_existing_paths(repo_root, (".github/ISSUE_TEMPLATE.md",))
    directory_templates = list_directory_files(
        repo_root,
        ".github/ISSUE_TEMPLATE",
        (".md", ".yml", ".yaml"),
    )
    return tuple(sorted((*direct_templates, *directory_templates)))


def discover_pr_templates(repo_root: Path) -> tuple[str, ...]:
    """Return existing pull-request template files."""
    direct_templates = list_existing_paths(repo_root, (".github/pull_request_template.md",))
    directory_templates = list_directory_files(
        repo_root,
        ".github/PULL_REQUEST_TEMPLATE",
        (".md",),
    )
    return tuple(sorted((*direct_templates, *directory_templates)))


def discover_security_files(repo_root: Path) -> tuple[str, ...]:
    """Return existing governance and community-health files relevant to preflight."""
    return list_existing_paths(
        repo_root,
        (
            "SECURITY.md",
            ".github/SECURITY.md",
            "CODE_OF_CONDUCT.md",
            ".github/CODE_OF_CONDUCT.md",
            "CODEOWNERS",
            ".github/CODEOWNERS",
            "docs/CODEOWNERS",
            ".github/dependabot.yml",
        ),
    )


def discover_agent_instruction_files(repo_root: Path) -> tuple[str, ...]:
    """Return existing agent-instruction and modular instruction files."""
    direct_files = list_existing_paths(repo_root, tuple(sorted(PROTECTED_EXACT_PATHS)))
    modular_files = list_directory_files(repo_root, ".github/instructions", (".md",))
    cursor_rules = list_directory_files(repo_root, ".cursor/rules", (".mdc",))
    return tuple(sorted((*direct_files, *modular_files, *cursor_rules)))


def discover_tooling_stacks(repo_root: Path, workflows: tuple[str, ...]) -> tuple[str, ...]:
    """Infer language and tooling stacks from local files without owner decisions."""
    files = relative_file_set(repo_root)
    stacks: list[str] = []

    def add_stack(name: str, condition: bool) -> None:
        if condition:
            stacks.append(name)

    add_stack("GitHub Actions", bool(workflows))
    add_stack("Markdown", any(path.endswith(".md") or path.endswith(".mdc") for path in files))
    add_stack("Node/npm", "package.json" in files or "package-lock.json" in files)
    add_stack(
        "Python",
        any(path.endswith(".py") for path in files)
        or any(path in files for path in ("pyproject.toml", "requirements.txt", "setup.py")),
    )
    add_stack("PowerShell", any(path.endswith(".ps1") or path.endswith(".psd1") for path in files))
    add_stack(
        "Terraform",
        any(
            path.endswith((".tf", ".tfvars", ".tftest.hcl", ".tf.json", ".tftpl", ".tfbackend"))
            for path in files
        )
        or ".tflint.hcl" in files,
    )
    add_stack("JSON", any(path.endswith((".json", ".jsonc")) for path in files))
    add_stack("YAML", any(path.endswith((".yml", ".yaml")) for path in files))
    add_stack(
        "JSON Schema",
        any(path.startswith("schemas/") and path.endswith(".schema.json") for path in files),
    )
    add_stack(
        "Template sync support",
        any(path.startswith(".template-sync/") for path in files),
    )
    return tuple(stacks)


def discover_repository_state(
    *,
    repo_root: Path,
    marker_path: Path,
    todo_path: Path,
    include_github_metadata: bool,
    command_runner: CommandRunner = run_command,
) -> RepositoryDiscovery:
    """Discover read-only repository state for the preflight report."""
    remotes = parse_git_remotes(repo_root)
    owner_name = infer_repository_name(remotes)
    github_metadata = discover_github_metadata(
        repo_root,
        owner_name,
        include_metadata=include_github_metadata,
        command_runner=command_runner,
    )
    workflows = discover_workflows(repo_root)
    return RepositoryDiscovery(
        owner_name=github_metadata.repository or owner_name,
        remotes=remotes,
        current_branch=current_branch(repo_root),
        likely_default_branch=likely_default_branch(repo_root, github_metadata),
        working_tree_entries=working_tree_entries(repo_root),
        workflows=workflows,
        issue_templates=discover_issue_templates(repo_root),
        pr_templates=discover_pr_templates(repo_root),
        security_files=discover_security_files(repo_root),
        agent_instruction_files=discover_agent_instruction_files(repo_root),
        tooling_stacks=discover_tooling_stacks(repo_root, workflows),
        marker_present=marker_path.exists(),
        adoption_note_present=todo_path.exists(),
        github_metadata=github_metadata,
    )


def build_manifest_ledger_row(
    *,
    mapping: ManifestMapping,
    marker_data: MarkerData,
    manifest_modules: frozenset[str],
    todo_items: tuple[TodoItem, ...],
    todo_path: Path,
    repo_root: Path,
    default_adoption_mode: str,
    ledger_output_dir: Path | None = None,
) -> tuple[LedgerRow, tuple[LocalOverride, ...], tuple[ProtectedFileDecision, ...]]:
    """Build one adoption-ledger row from a manifest mapping."""
    modules = relation_module_names(mapping)
    local_overrides = matching_local_overrides_for_pattern(
        mapping.pattern,
        marker_data.local_overrides,
    )
    deferred_candidates = matching_deferred_candidates_for_pattern(
        mapping.pattern,
        marker_data.deferred_candidates,
    )
    protected_decisions = matching_protected_decisions_for_pattern(
        mapping.pattern,
        marker_data.protected_decisions,
    )
    is_protected = is_protected_manifest_pattern(mapping.pattern)
    retained = not mapping.unknown_modules and PathRelation(
        patterns=(mapping.pattern,),
        requires_all=mapping.requires_all,
        requires_any=mapping.requires_any,
        notes=(mapping.notes,) if mapping.notes else (),
        unknown_modules=mapping.unknown_modules,
    ).is_retained_by(marker_data.included_modules)
    should_trim = (
        retained
        and mapping.notes is not None
        and has_trim_note((mapping.notes,))
        and notes_mention_modules(
            (mapping.notes,),
            manifest_modules - marker_data.included_modules,
        )
    )

    decision = "retain"
    requires_decision = False
    reason_parts: list[str] = []

    if mapping.unknown_modules:
        decision = "needs maintainer decision"
        requires_decision = True
        reason_parts.append(
            "Manifest references unknown module(s): "
            + ", ".join(sorted(mapping.unknown_modules))
            + "."
        )
    elif protected_decisions:
        decision = "protected decision: " + ", ".join(
            protected_decision.decision for protected_decision in protected_decisions
        )
        requires_decision = protected_decision_requires_maintainer_decision(protected_decisions)
        reason_parts.append(protected_decision_reason(protected_decisions, local_overrides))
    elif local_overrides:
        decision = "local override"
        reason_parts.append(local_override_reason(local_overrides))
        if any(
            override.default_decision in {"DEFER", "PROTECTED-REVIEW"}
            for override in local_overrides
        ):
            requires_decision = True
    elif deferred_candidates:
        decision = "needs maintainer decision"
        requires_decision = True
        reason_parts.append(
            "Deferred protected candidate: "
            + "; ".join(
                f"{candidate.source_commit}: {candidate.reason}"
                for candidate in deferred_candidates
            )
        )
    elif is_protected:
        decision = "needs maintainer decision"
        requires_decision = True
        if retained:
            reason_parts.append("Protected retained path requires explicit owner authorization.")
        else:
            reason_parts.append(
                "Protected path is not retained by included modules; confirm deferral or skip."
            )
    elif not retained:
        decision = "skip"
        reason_parts.append(retention_gap_reason(mapping, marker_data.included_modules))
    elif should_trim:
        decision = "trim"
        reason_parts.append(
            "Retained path has manifest notes for module-scoped inline blocks; "
            "remove blocks for unadopted modules and keep the retained file."
        )
    else:
        reason_parts.append(
            "Retained because marker included_modules satisfy the manifest relation."
        )

    if is_protected and decision != "needs maintainer decision" and not protected_decisions:
        requires_decision = True
        reason_parts.append(
            "Protected file; explicit owner authorization is required before edits."
        )
    if mapping.notes:
        reason_parts.append(f"Manifest note: {mapping.notes}")

    return (
        LedgerRow(
            path=mapping.pattern,
            manifest_modules=format_manifest_modules(mapping.requires_all, mapping.requires_any),
            decision=decision,
            reason=" ".join(reason_parts),
            protected_file="Yes" if is_protected else "No",
            requires_maintainer_decision="Yes" if requires_decision else "No",
            adoption_mode=(
                adoption_mode_for_modules(
                    modules,
                    local_overrides,
                    is_protected,
                    default_adoption_mode,
                )
                if not protected_decisions
                else protected_decision_adoption_mode(protected_decisions)
            ),
            todo_link=matching_todo_links(
                path=mapping.pattern,
                modules=modules,
                is_protected=is_protected,
                todo_items=todo_items,
                todo_path=todo_path,
                repo_root=repo_root,
                ledger_output_dir=ledger_output_dir,
            ),
            validation_commands=validation_commands_for_modules(modules),
        ),
        local_overrides,
        protected_decisions,
    )


def build_unmatched_local_override_row(
    *,
    local_override: LocalOverride,
    mappings: tuple[ManifestMapping, ...],
    todo_items: tuple[TodoItem, ...],
    todo_path: Path,
    repo_root: Path,
    default_adoption_mode: str,
    ledger_output_dir: Path | None = None,
) -> LedgerRow:
    """Build a ledger row for a marker local override not consumed by any manifest mapping row."""
    display_path = local_override.path + ("/" if local_override.is_directory else "")
    relation = selected_relation_for_path(local_override.path, mappings)
    modules = relation.requires_all | relation.requires_any if relation is not None else frozenset()
    is_protected = is_protected_instruction_path(local_override.path)
    requires_decision = (
        is_protected
        or relation is None
        or local_override.default_decision in {"DEFER", "PROTECTED-REVIEW"}
    )
    reason = (
        f"Marker local override defaults to `{local_override.default_decision}`: "
        f"{local_override.reason}"
    )
    if relation is None:
        reason += " No manifest mapping currently matches this override path."

    return LedgerRow(
        path=display_path,
        manifest_modules=(
            format_manifest_modules(relation.requires_all, relation.requires_any)
            if relation is not None
            else "unmapped"
        ),
        decision="local override",
        reason=reason,
        protected_file="Yes" if is_protected else "No",
        requires_maintainer_decision="Yes" if requires_decision else "No",
        adoption_mode=adoption_mode_for_modules(
            modules,
            (local_override,),
            is_protected,
            default_adoption_mode,
        ),
        todo_link=matching_todo_links(
            path=display_path,
            modules=modules,
            is_protected=is_protected,
            todo_items=todo_items,
            todo_path=todo_path,
            repo_root=repo_root,
            ledger_output_dir=ledger_output_dir,
        ),
        validation_commands=validation_commands_for_modules(modules),
    )


def build_unmatched_protected_decision_row(
    *,
    protected_decision: ProtectedFileDecision,
    mappings: tuple[ManifestMapping, ...],
    todo_items: tuple[TodoItem, ...],
    todo_path: Path,
    repo_root: Path,
    ledger_output_dir: Path | None = None,
) -> LedgerRow:
    """Build a ledger row for a protected decision not consumed by a manifest mapping."""
    relation = selected_relation_for_path(protected_decision.path, mappings)
    modules = relation.requires_all | relation.requires_any if relation is not None else frozenset()
    is_protected = is_protected_instruction_path(protected_decision.path)
    return LedgerRow(
        path=protected_decision.path,
        manifest_modules=(
            format_manifest_modules(relation.requires_all, relation.requires_any)
            if relation is not None
            else "unmapped"
        ),
        decision=f"protected decision: {protected_decision.decision}",
        reason=protected_decision_reason((protected_decision,)),
        protected_file="Yes" if is_protected else "No",
        requires_maintainer_decision=(
            "Yes"
            if protected_decision_requires_maintainer_decision((protected_decision,))
            else "No"
        ),
        adoption_mode=protected_decision_adoption_mode((protected_decision,)),
        todo_link=matching_todo_links(
            path=protected_decision.path,
            modules=modules,
            is_protected=is_protected,
            todo_items=todo_items,
            todo_path=todo_path,
            repo_root=repo_root,
            ledger_output_dir=ledger_output_dir,
        ),
        validation_commands=validation_commands_for_modules(modules),
    )


def build_manual_todo_ledger_row(
    *,
    todo_item: TodoItem,
    todo_path: Path,
    repo_root: Path,
    ledger_output_dir: Path | None = None,
) -> LedgerRow:
    """Build a ledger row for one first-adoption checklist item."""
    status = "complete" if todo_item.is_complete else "open"
    return LedgerRow(
        path=repository_relative_path(todo_path, repo_root),
        manifest_modules="manual setup",
        decision="manual TODO",
        reason=f"{status}: {todo_item.text}",
        protected_file="No",
        requires_maintainer_decision="No" if todo_item.is_complete else "Yes",
        adoption_mode="recorded in checklist",
        todo_link=todo_item_link(todo_path, repo_root, todo_item, ledger_output_dir),
        validation_commands="manual first-adoption review",
    )


def build_adoption_ledger_rows(
    *,
    marker_data: MarkerData,
    manifest_modules: frozenset[str],
    mappings: tuple[ManifestMapping, ...],
    todo_items: tuple[TodoItem, ...],
    todo_path: Path,
    repo_root: Path,
    default_adoption_mode: str,
    ledger_output_dir: Path | None = None,
) -> tuple[LedgerRow, ...]:
    """Build the generated adoption ledger rows."""
    rows: list[LedgerRow] = []
    matched_overrides: set[LocalOverride] = set()
    matched_protected_decisions: set[ProtectedFileDecision] = set()
    for mapping in mappings:
        row, local_overrides, protected_decisions = build_manifest_ledger_row(
            mapping=mapping,
            marker_data=marker_data,
            manifest_modules=manifest_modules,
            todo_items=todo_items,
            todo_path=todo_path,
            repo_root=repo_root,
            default_adoption_mode=default_adoption_mode,
            ledger_output_dir=ledger_output_dir,
        )
        rows.append(row)
        matched_overrides.update(local_overrides)
        matched_protected_decisions.update(protected_decisions)

    for local_override in sorted(
        set(marker_data.local_overrides) - matched_overrides,
        key=lambda override: override.path,
    ):
        rows.append(
            build_unmatched_local_override_row(
                local_override=local_override,
                mappings=mappings,
                todo_items=todo_items,
                todo_path=todo_path,
                repo_root=repo_root,
                default_adoption_mode=default_adoption_mode,
                ledger_output_dir=ledger_output_dir,
            )
        )

    for protected_decision in sorted(
        set(marker_data.protected_decisions) - matched_protected_decisions,
        key=lambda decision: decision.path,
    ):
        rows.append(
            build_unmatched_protected_decision_row(
                protected_decision=protected_decision,
                mappings=mappings,
                todo_items=todo_items,
                todo_path=todo_path,
                repo_root=repo_root,
                ledger_output_dir=ledger_output_dir,
            )
        )

    for todo_item in todo_items:
        rows.append(
            build_manual_todo_ledger_row(
                todo_item=todo_item,
                todo_path=todo_path,
                repo_root=repo_root,
                ledger_output_dir=ledger_output_dir,
            )
        )

    return tuple(rows)


def markdown_cell(value: str) -> str:
    """Escape a value for inclusion in a Markdown table cell."""
    return value.replace("\n", "<br>").replace("|", r"\|")


def format_table(rows: tuple[CandidateRow, ...]) -> str:
    """Render candidate rows as a Markdown table."""
    header = (
        "| Path | Change | Matched module relation | Retained status | Local override | "
        "Deferred protected candidate | Protected file decision | "
        "Protected instruction/governance file | Notes |"
    )
    divider = "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"
    rendered_rows = [header, divider]
    for row in rows:
        rendered_rows.append(
            "| "
            + " | ".join(
                markdown_cell(cell)
                for cell in (
                    row.path,
                    row.change,
                    row.module_relation,
                    row.retained_status,
                    row.local_override_status,
                    row.deferred_status,
                    row.protected_decision_status,
                    row.protected_status,
                    "<br>".join(row.notes) if row.notes else "None",
                )
            )
            + " |"
        )
    return "\n".join(rendered_rows)


def format_ledger_table(rows: tuple[LedgerRow, ...]) -> str:
    """Render adoption-ledger rows as a Markdown table."""
    header = (
        "| Path | Manifest module(s) | Decision | Reason | Protected file | "
        "Requires maintainer decision | Adoption mode | `_TODO-repo-init.md` link | "
        "Validation command affected |"
    )
    divider = "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"
    rendered_rows = [header, divider]
    for row in rows:
        rendered_rows.append(
            "| "
            + " | ".join(
                markdown_cell(cell)
                for cell in (
                    row.path,
                    row.manifest_modules,
                    row.decision,
                    row.reason,
                    row.protected_file,
                    row.requires_maintainer_decision,
                    row.adoption_mode,
                    row.todo_link,
                    row.validation_commands,
                )
            )
            + " |"
        )
    return "\n".join(rendered_rows)


def format_protected_decision_records(marker_data: MarkerData) -> str | None:
    """Render protected-file decision records and overlapping marker context."""
    if not marker_data.protected_decisions:
        return None

    overlaps_by_path = {
        overlap.path: overlap
        for overlap in validate_protected_file_decisions(
            marker_data.protected_decisions,
            marker_data.local_overrides,
            marker_data.deferred_candidates,
        )
    }
    lines = [
        "## Protected File Decision Records",
        "",
        "These entries come from `template_sync.protected_file_decisions`.",
        "",
    ]
    for protected_decision in sorted(
        marker_data.protected_decisions,
        key=lambda decision: decision.path,
    ):
        lines.append(f"- `{protected_decision.path}`")
        lines.append(
            f"  - protected_file_decisions: {protected_decision_summary(protected_decision)}"
        )
        overlap = overlaps_by_path.get(protected_decision.path)
        if overlap is not None:
            for local_override in overlap.local_overrides:
                lines.append(f"  - local_overrides: {local_override_summary(local_override)}")
            for candidate in overlap.deferred_candidates:
                lines.append(
                    "  - deferred_protected_candidates: " f"{deferred_candidate_summary(candidate)}"
                )
    return "\n".join(lines)


def format_remove_local_authorizations(marker_data: MarkerData) -> str | None:
    """Render REMOVE-LOCAL authorization details in a distinct section."""
    remove_local_decisions = tuple(
        protected_decision
        for protected_decision in marker_data.protected_decisions
        if protected_decision.decision == REMOVAL_DECISION
    )
    if not remove_local_decisions:
        return None

    lines = [
        "## REMOVE-LOCAL Authorizations",
        "",
        (
            "Reviewers must verify that each authorization basis names the removed "
            "file and explicitly authorizes removal."
        ),
        "",
    ]
    for protected_decision in sorted(
        remove_local_decisions,
        key=lambda decision: decision.path,
    ):
        lines.append(f"- `{protected_decision.path}`")
        lines.append(f"  - authorization_basis: {protected_decision.authorization_basis}")
        lines.append(f"  - authorized_scope: {protected_decision.authorized_scope}")
        lines.append(f"  - reason: {protected_decision.reason}")
    return "\n".join(lines)


def format_adoption_ledger(
    *,
    marker_path: Path,
    manifest_path: Path,
    todo_path: Path,
    repo_root: Path,
    marker_data: MarkerData,
    rows: tuple[LedgerRow, ...],
    default_adoption_mode: str,
) -> str:
    """Render the generated adoption ledger as a Markdown snapshot."""
    marker_relative = repository_relative_path(marker_path, repo_root)
    manifest_relative = repository_relative_path(manifest_path, repo_root)
    todo_relative = repository_relative_path(todo_path, repo_root)
    todo_status = "found" if todo_path.exists() else "not found"
    included_modules = (
        ", ".join(f"`{module}`" for module in sorted(marker_data.included_modules)) or "none"
    )

    lines = [
        "# Template Adoption Ledger",
        "",
        (
            "Generated snapshot; review artifact only. "
            f"`{manifest_relative}` and `{marker_relative}` remain the authoritative "
            "machine-readable state. Regenerate this ledger before first-adoption, "
            "full-reconciliation, or protected-file review."
        ),
        "",
        f"- Marker: `{marker_relative}`",
        f"- Manifest: `{manifest_relative}`",
        f"- First-adoption checklist: `{todo_relative}` ({todo_status})",
        f"- Included modules: {included_modules}",
        f"- Default adoption mode: `{default_adoption_mode}`",
        "",
        format_ledger_table(rows) if rows else "No manifest mappings or manual TODO rows found.",
    ]
    protected_decision_records = format_protected_decision_records(marker_data)
    if protected_decision_records is not None:
        lines.extend(["", protected_decision_records])
    remove_local_authorizations = format_remove_local_authorizations(marker_data)
    if remove_local_authorizations is not None:
        lines.extend(["", remove_local_authorizations])
    return "\n".join(lines)


def format_summary_module_list(modules: frozenset[str]) -> str:
    """Render a deterministic bullet list of module names."""
    if not modules:
        return "- None"
    return "\n".join(f"- `{module}`" for module in sorted(modules))


def protected_decision_authorization_status(protected_decision: ProtectedFileDecision) -> str:
    """Return concise authorization status for one protected-file decision."""
    if protected_decision.decision in {"TAKE", "MERGE", REMOVAL_DECISION}:
        missing_fields: list[str] = []
        if protected_decision.authorization_basis is None:
            missing_fields.append("authorization_basis")
        if protected_decision.authorized_scope is None:
            missing_fields.append("authorized_scope")
        if (
            protected_decision.adoption_mode == "tailored"
            and protected_decision.tailored_authorization_basis is None
        ):
            missing_fields.append("tailored_authorization_basis")
        if missing_fields:
            return "missing " + ", ".join(missing_fields)
        return "authorized"

    if protected_decision.decision in {"DEFER", "PROTECTED-REVIEW"}:
        return "deferred"

    return "not applicable"


def format_summary_protected_decisions(marker_data: MarkerData) -> str:
    """Render protected-file decisions for the concise adoption summary."""
    if not marker_data.protected_decisions:
        return "None recorded."

    header = (
        "| Path | Decision | Adoption mode | Authorization status | Authorization basis | "
        "Authorized scope | Tailored authorization basis | Reason |"
    )
    divider = "| --- | --- | --- | --- | --- | --- | --- | --- |"
    lines = [header, divider]
    for protected_decision in sorted(
        marker_data.protected_decisions,
        key=lambda decision: decision.path,
    ):
        lines.append(
            "| "
            + " | ".join(
                markdown_cell(cell)
                for cell in (
                    protected_decision.path,
                    protected_decision.decision,
                    protected_decision.adoption_mode or "not recorded",
                    protected_decision_authorization_status(protected_decision),
                    protected_decision.authorization_basis or "not recorded",
                    protected_decision.authorized_scope or "not recorded",
                    protected_decision.tailored_authorization_basis or "not recorded",
                    protected_decision.reason or "not recorded",
                )
            )
            + " |"
        )
    return "\n".join(lines)


def format_summary_local_overrides(marker_data: MarkerData) -> str:
    """Render marker local overrides for the concise adoption summary."""
    if not marker_data.local_overrides:
        return "None recorded."

    lines = [
        "| Path | Default decision | Reason |",
        "| --- | --- | --- |",
    ]
    for local_override in sorted(
        marker_data.local_overrides,
        key=lambda override: override.path,
    ):
        display_path = local_override.path + ("/" if local_override.is_directory else "")
        lines.append(
            "| "
            + " | ".join(
                markdown_cell(cell)
                for cell in (
                    display_path,
                    local_override.default_decision,
                    local_override.reason,
                )
            )
            + " |"
        )
    return "\n".join(lines)


def format_summary_manual_todo_items(
    *,
    todo_state: SummaryTodoState,
    todo_path: Path,
    repo_root: Path,
) -> str:
    """Render machine-interpretable unchecked TODO items for the summary."""
    todo_relative = repository_relative_path(todo_path, repo_root)
    if not todo_state.exists:
        return f"`{todo_relative}` not found."
    if not todo_state.is_interpretable:
        return (
            f"`{todo_relative}` is present but not machine-interpretable; "
            "unchecked items were not parsed."
        )
    if not todo_state.unchecked_items:
        return "No unchecked items in machine-interpretable checklist sections."

    lines: list[str] = []
    for section in TODO_KNOWN_SECTIONS:
        for item in todo_state.unchecked_items:
            if item.section == section:
                lines.append(
                    f"- {section}: {item.text} " + f"(`{todo_relative}` line {item.line_number})"
                )
    return "\n".join(lines)


def append_unique_summary_item(
    items: list[str],
    seen_items: set[str],
    item: str,
) -> None:
    """Append one summary item while preserving deterministic first occurrence."""
    if item in seen_items:
        return
    seen_items.add(item)
    items.append(item)


def deferred_candidate_rendered_in_rows(
    candidate: DeferredProtectedCandidate,
    rows: tuple[LedgerRow, ...],
) -> bool:
    """Return True when a deferred-candidate ledger row already covers this candidate.

    A deferred protected candidate is folded into a manifest ledger row only when that
    row takes the deferred-candidate branch, which embeds ``Deferred protected
    candidate:`` in the row reason and matches the candidate through the row's manifest
    pattern. Matching on the candidate path via the manifest pattern, rather than
    substring-matching the reason text, avoids suppressing distinct candidates that
    merely share a templated reason such as ``Awaiting protected-file authorization.``.
    """
    return any(
        row.requires_maintainer_decision == "Yes"
        and "Deferred protected candidate:" in row.reason
        and manifest_pattern_matches_path(row.path, candidate.path)
        for row in rows
    )


def format_summary_unresolved_decisions(
    *,
    rows: tuple[LedgerRow, ...],
    marker_data: MarkerData,
    todo_state: SummaryTodoState,
    todo_path: Path,
    repo_root: Path,
) -> str:
    """Render unresolved maintainer decisions from available machine-readable state."""
    todo_relative = repository_relative_path(todo_path, repo_root)
    unresolved: list[str] = []
    seen_unresolved: set[str] = set()

    for row in rows:
        if row.requires_maintainer_decision == "Yes" and row.decision != "manual TODO":
            append_unique_summary_item(
                unresolved,
                seen_unresolved,
                f"`{row.path}`: {row.decision}; {row.reason}",
            )

    for candidate in sorted(
        marker_data.deferred_candidates,
        key=lambda item: (item.path, item.source_commit),
    ):
        if not deferred_candidate_rendered_in_rows(candidate, rows):
            append_unique_summary_item(
                unresolved,
                seen_unresolved,
                (
                    f"`{candidate.path}`: deferred protected candidate from "
                    f"`{candidate.source_commit}`; {candidate.reason}"
                ),
            )

    if todo_state.exists and not todo_state.is_interpretable:
        append_unique_summary_item(
            unresolved,
            seen_unresolved,
            (
                f"`{todo_relative}` is present but not machine-interpretable; "
                "manual review is required."
            ),
        )
    elif todo_state.is_interpretable:
        for item in todo_state.unchecked_items:
            if item.section in TODO_DECISION_SECTIONS:
                append_unique_summary_item(
                    unresolved,
                    seen_unresolved,
                    (
                        f"`{todo_relative}` line {item.line_number}: "
                        + f"{item.section}: {item.text}"
                    ),
                )

    if unresolved:
        return "\n".join(
            [
                "- Unresolved maintainer decisions remain in available "
                "machine-readable state: Yes.",
                *(f"- {item}" for item in unresolved),
            ]
        )

    return "\n".join(
        [
            "- Unresolved maintainer decisions remain in available machine-readable state: No.",
            (
                "- No unresolved decisions were found in marker data, protected-file "
                "decisions, deferred protected candidates, local overrides, or "
                "machine-interpretable TODO state."
            ),
        ]
    )


def summary_validation_commands(marker_data: MarkerData) -> tuple[str, ...]:
    """Return validation commands for retained modules in summary order."""
    commands = [
        "python .template-sync/scripts/run_first_adoption_checks.py",
        "pre-commit run --all-files",
    ]
    for command in validation_commands_for_modules(marker_data.included_modules).split("<br>"):
        if command and command != "manual review" and command not in commands:
            commands.append(command)
    return tuple(commands)


def format_summary_validation_commands(marker_data: MarkerData) -> str:
    """Render retained-module validation commands for the concise summary."""
    return "\n".join(f"- `{command}`" for command in summary_validation_commands(marker_data))


def format_todo_summary_status(todo_state: SummaryTodoState) -> str:
    """Return a short machine-interpretability status for the TODO file."""
    if not todo_state.exists:
        return "not found"
    if not todo_state.is_interpretable:
        return "found; not machine-interpretable"
    return "found; machine-interpretable"


def format_adoption_summary(
    *,
    marker_path: Path,
    manifest_path: Path,
    todo_path: Path,
    repo_root: Path,
    marker_data: MarkerData,
    manifest_modules: frozenset[str],
    rows: tuple[LedgerRow, ...],
    todo_state: SummaryTodoState,
    default_adoption_mode: str,
) -> str:
    """Render a concise deterministic template adoption summary."""
    marker_relative = repository_relative_path(marker_path, repo_root)
    manifest_relative = repository_relative_path(manifest_path, repo_root)
    todo_relative = repository_relative_path(todo_path, repo_root)
    marker_status = "found" if marker_path.exists() else "not found"
    excluded_modules = manifest_modules - marker_data.included_modules

    return "\n".join(
        [
            "# Template Adoption Summary",
            "",
            (
                "Concise deterministic review artifact for adoption PR descriptions. "
                "`--ledger-only` remains the detailed path-level review artifact; "
                f"`{manifest_relative}` and `{marker_relative}` remain authoritative."
            ),
            "",
            f"- Marker: `{marker_relative}` ({marker_status})",
            f"- Manifest: `{manifest_relative}`",
            f"- First-adoption checklist: `{todo_relative}` ({format_todo_summary_status(todo_state)})",
            f"- Default adoption mode: `{default_adoption_mode}`",
            "",
            "## Included Modules",
            "",
            format_summary_module_list(marker_data.included_modules),
            "",
            "## Excluded Modules",
            "",
            format_summary_module_list(excluded_modules),
            "",
            "## Protected-File Decisions",
            "",
            format_summary_protected_decisions(marker_data),
            "",
            "## Local Overrides",
            "",
            format_summary_local_overrides(marker_data),
            "",
            "## Unresolved Maintainer Decisions",
            "",
            format_summary_unresolved_decisions(
                rows=rows,
                marker_data=marker_data,
                todo_state=todo_state,
                todo_path=todo_path,
                repo_root=repo_root,
            ),
            "",
            "## Manual TODO Items",
            "",
            format_summary_manual_todo_items(
                todo_state=todo_state,
                todo_path=todo_path,
                repo_root=repo_root,
            ),
            "",
            "## Validation Commands",
            "",
            format_summary_validation_commands(marker_data),
        ]
    )


def format_limited_path_list(paths: tuple[str, ...], empty_text: str, *, limit: int = 8) -> str:
    """Return a compact Markdown list of repository paths."""
    if not paths:
        return empty_text
    visible = [f"`{path}`" for path in paths[:limit]]
    if len(paths) > limit:
        visible.append(f"{len(paths) - limit} more")
    return ", ".join(visible)


def redact_url_userinfo(value: str) -> str:
    """Redact URL user-info before displaying a URL-like value.

    Handles both ``scheme://userinfo@host`` and scheme-relative ``//userinfo@host``
    forms. SCP-style remotes such as ``git@github.com:org/repo`` have no URL
    authority and are returned unchanged.
    """
    try:
        parsed = urlsplit(value)
    except ValueError:
        # Unparseable input (for example, a malformed IPv6 authority): redact
        # defensively instead of risking a leak by returning the raw value.
        if "@" not in value:
            return value
        return f"***@{value.rsplit('@', maxsplit=1)[1]}"
    if not parsed.netloc or "@" not in parsed.netloc:
        return value
    safe_netloc = f"***@{parsed.netloc.rsplit('@', maxsplit=1)[1]}"
    return urlunsplit((parsed.scheme, safe_netloc, parsed.path, parsed.query, parsed.fragment))


def format_remotes(remotes: tuple[RemoteInfo, ...]) -> str:
    """Return a compact remote summary."""
    if not remotes:
        return "none found"
    return "; ".join(
        f"`{remote.name}` {remote.purpose}: `{redact_url_userinfo(remote.url)}`"
        for remote in remotes
    )


def format_working_tree(entries: tuple[str, ...]) -> str:
    """Return a compact working-tree summary."""
    if not entries:
        return "clean"
    visible = entries[:8]
    suffix = f"; {len(entries) - len(visible)} more" if len(entries) > len(visible) else ""
    return f"{len(entries)} changed or untracked path(s): " + "; ".join(visible) + suffix


def format_github_metadata(metadata: GitHubMetadata) -> str:
    """Return a Markdown bullet list for optional GitHub metadata."""
    manual_settings = ", ".join(GITHUB_METADATA_MANUAL_SETTINGS)
    if not metadata.requested:
        return "\n".join(
            [
                (
                    "- GitHub metadata: not requested; run with "
                    "`--include-github-metadata` to opt in to read-only `gh` lookups."
                ),
                f"- GitHub-only settings requiring manual review: {manual_settings}.",
            ]
        )
    if not metadata.available:
        detail = f" ({metadata.error})" if metadata.error is not None else ""
        return "\n".join(
            [
                f"- GitHub metadata: unavailable through `{metadata.source}`{detail}.",
                f"- GitHub-only settings requiring manual review: {manual_settings}.",
            ]
        )

    labels = format_limited_path_list(metadata.labels, "none returned", limit=12)
    lines = [
        f"- GitHub metadata source: `{metadata.source}`",
        f"- GitHub repository: `{metadata.repository or 'unknown'}`",
        f"- Visibility: `{metadata.visibility or 'unknown'}`",
        f"- Default branch from GitHub: `{metadata.default_branch or 'unknown'}`",
        f"- Discussions: `{metadata.discussions_enabled or 'unknown'}`",
        f"- Labels returned by GitHub: {labels}",
        f"- GitHub-only settings requiring manual review: {manual_settings}.",
    ]
    if metadata.error is not None:
        lines.append(f"- Partial metadata warning: {metadata.error}")
    return "\n".join(lines)


def format_marker_summary(marker_data: MarkerData, marker_present: bool) -> str:
    """Return a compact marker-state summary."""
    if not marker_present:
        return "not found; selected modules and protected-file decisions are unrecorded"
    included_modules = (
        ", ".join(f"`{module}`" for module in sorted(marker_data.included_modules)) or "none"
    )
    return (
        "found; included modules: "
        f"{included_modules}; local overrides: {len(marker_data.local_overrides)}; "
        f"deferred protected candidates: {len(marker_data.deferred_candidates)}; "
        f"protected-file decisions: {len(marker_data.protected_decisions)}"
    )


def format_module_selection_aid(
    manifest_modules: frozenset[str],
    marker_data: MarkerData,
) -> str:
    """Render a module-selection decision aid without recomputing path decisions."""
    lines = [
        "| Module | Current marker selection | First-adoption action |",
        "| --- | --- | --- |",
    ]
    for module in sorted(manifest_modules):
        selected = "selected" if module in marker_data.included_modules else "not selected"
        action = (
            "confirm retained module scope"
            if module in marker_data.included_modules
            else "decide whether this module is adopted"
        )
        lines.append(f"| {module} | {selected} | {action} |")
    return "\n".join(lines)


def format_protected_authorization_questions(rows: tuple[LedgerRow, ...]) -> str:
    """Render protected-file authorization questions from reused ledger rows."""
    protected_rows = tuple(row for row in rows if row.protected_file == "Yes")
    if not protected_rows:
        return "No protected instruction/governance paths were flagged by the adoption ledger."

    lines: list[str] = []
    for row in protected_rows:
        if row.requires_maintainer_decision == "Yes":
            lines.append(
                "- [ ] Does the maintainer authorize the selected action for "
                f"`{row.path}`? Ledger decision: `{row.decision}`; adoption mode: "
                f"`{row.adoption_mode}`; reason: {row.reason}"
            )
        else:
            lines.append(
                "- [ ] Verify the recorded protected-file authorization for "
                f"`{row.path}` remains valid. Ledger decision: `{row.decision}`; "
                f"adoption mode: `{row.adoption_mode}`."
            )
    return "\n".join(lines)


def format_structural_alignment_candidates(discovery: RepositoryDiscovery) -> str:
    """Render structural-alignment candidates discovered during preflight."""
    candidates: list[str] = []
    if not discovery.adoption_note_present:
        candidates.append(
            "Create or update `_TODO-repo-init.md` before finalizing files that depend on "
            "manual GitHub settings or maintainer policy."
        )
    if not discovery.marker_present:
        candidates.append(
            "Create `.template-sync/marker.yml` if future template sync support is retained; "
            "record selected modules, local overrides, and protected-file decisions there."
        )
    if discovery.workflows:
        candidates.append(
            "Confirm retained workflow files under `.github/workflows/` still point at the "
            "downstream repository's actual validation commands and paths."
        )
    if discovery.agent_instruction_files:
        candidates.append(
            "Classify protected instruction files before editing them and record any "
            "authorized protected-file decisions."
        )
    if "Terraform" in discovery.tooling_stacks:
        candidates.append(
            "Confirm Terraform module/test roots and `.tflint.hcl` paths match retained "
            "Terraform workflow and pre-commit hooks."
        )
    if "Python" in discovery.tooling_stacks:
        candidates.append(
            "Confirm Python source, test, and packaging paths match retained Python CI and "
            "pre-commit hooks, or document downstream path remaps."
        )
    if not candidates:
        return "No structural-alignment candidates were detected from local files."
    return "\n".join(f"- [ ] {candidate}" for candidate in candidates)


def validation_plan_suggestions(rows: tuple[LedgerRow, ...]) -> tuple[str, ...]:
    """Return validation suggestions from ledger rows and first-adoption helpers."""
    commands = [
        "python .template-sync/scripts/run_first_adoption_checks.py",
        "pre-commit run --all-files",
    ]
    for row in rows:
        for command in row.validation_commands.split("<br>"):
            if command and command != "manual review" and command not in commands:
                commands.append(command)
    return tuple(commands)


def format_validation_plan(rows: tuple[LedgerRow, ...]) -> str:
    """Render validation-plan suggestions for the preflight report."""
    return "\n".join(f"- [ ] `{command}`" for command in validation_plan_suggestions(rows))


def format_maintainer_questionnaire(discovery: RepositoryDiscovery) -> str:
    """Render maintainer questions for policy values that must not be guessed."""
    default_branch = discovery.likely_default_branch or "[recorded default branch]"
    return "\n".join(
        [
            "- [ ] Which manifest modules should this repository retain?",
            "- [ ] Which contact path should `CODE_OF_CONDUCT.md` publish?",
            "- [ ] Which vulnerability reporting channel should `SECURITY.md` publish?",
            "- [ ] Which CODEOWNERS owner or team should be used?",
            "- [ ] Should template issue labels be used, remapped, or removed?",
            "- [ ] Should GitHub Discussions be enabled or left disabled?",
            "- [ ] Should private vulnerability reporting be enabled, left disabled, or marked "
            "not available?",
            f"- [ ] Should the default branch remain `{default_branch}`, be renamed, or be deferred?",
            "- [ ] Should the default branch use a ruleset, classic branch protection, or no "
            "new protection?",
            "- [ ] Is there a GHES host override, or should `github.com` remain the expected host?",
            "- [ ] Are protected instruction-file edits authorized, deferred, or out of scope?",
            "- [ ] Are any protected instruction-file removals authorized?",
            "- [ ] Are any template-derived files explicitly approved for `tailored` adoption mode?",
            "- [ ] Which structural findings are required for adoption and which become "
            "post-adoption issues?",
        ]
    )


def format_todo_starter(
    discovery: RepositoryDiscovery,
    marker_data: MarkerData,
) -> str:
    """Render starter content for ``_TODO-repo-init.md``."""
    owner_name = discovery.owner_name or "OWNER/REPO"
    default_branch = discovery.likely_default_branch or "[recorded default branch]"
    visibility = discovery.github_metadata.visibility or "[public, private, or internal]"
    marker_status = "found" if discovery.marker_present else "not found"
    adoption_note_status = "found" if discovery.adoption_note_present else "not found"
    included_modules = (
        ", ".join(sorted(marker_data.included_modules))
        if marker_data.included_modules
        else "[selected modules]"
    )

    return "\n".join(
        [
            "# Repository Initialization Checklist",
            "",
            (
                "This file records first-adoption decisions for this downstream repository. "
                "It is downstream-owned state, not an upstream template file."
            ),
            "",
            "## Discoverable Repository State",
            "",
            f"- [ ] Repository owner/name recorded: `{owner_name}`",
            f"- [ ] Repository visibility recorded: `{visibility}`",
            f"- [ ] Repository default branch recorded: `{default_branch}`",
            "- [ ] Existing governance, security, CODEOWNERS, issue-template, PR-template, "
            "and Dependabot files reviewed before replacement.",
            (
                "- [ ] Existing `.template-sync/marker.yml`, `_TODO-repo-init.md`, or "
                "equivalent adoption note checked before asking repeated questions "
                f"(marker: {marker_status}; checklist: {adoption_note_status})."
            ),
            f"- [ ] Included module candidates reviewed: `{included_modules}`",
            "",
            "## Manual GitHub Settings",
            "",
            (
                "- [ ] Private vulnerability reporting decision: "
                "`[enable, leave disabled, or not available]`"
            ),
            "- [ ] GitHub Discussions decision: `[enable or leave disabled]`",
            "- [ ] Labels decision, including `triage`: `[create, skip, or already present]`",
            (
                "- [ ] Default branch decision: "
                "`[keep recorded default branch, rename, or defer]`"
            ),
            (
                "- [ ] Repository ruleset or branch-protection decision: "
                "`[create ruleset, use classic branch protection, leave unchanged, or defer]`"
            ),
            "",
            "## Maintainer Policy Decisions",
            "",
            (
                "- [ ] Code of Conduct reporting contact method: "
                "`[explicit contact, profile contact, approved alternate, or deferred]`"
            ),
            (
                "- [ ] Security vulnerability reporting channel: "
                "`[private vulnerability reporting, monitored email, both, or deferred]`"
            ),
            "- [ ] CODEOWNERS owner/team identity: `[@user or @org/team]`",
            (
                "- [ ] Label-dependent issue-template behavior: "
                "`[use labels, remap labels, remove labels, or deferred]`"
            ),
            (
                "- [ ] Adoption mode for protected and template-derived files: "
                "`minimal-preservation` by default; list any `tailored` opt-ins."
            ),
            "- [ ] GHES host override: `[none or github.company.com]`",
            "",
            "## Protected-File Adoption Decisions",
            "",
            (
                "- [ ] Protected instruction files identified before editing: "
                "`.github/copilot-instructions.md`, `.github/instructions/*.instructions.md`, "
                "`.cursor/rules/*.mdc`, `.hermes.md`, `AGENTS.md`, `CLAUDE.md`, and "
                "`GEMINI.md`."
            ),
            "- [ ] Protected-file edits authorized by maintainer: `[none, path-scoped, or deferred]`",
            (
                "- [ ] Protected-file removals authorized by maintainer: "
                "`[none, path-scoped, or deferred]`"
            ),
            (
                "- [ ] `.template-sync/marker.yml` protected-file decisions updated if "
                "template sync support is retained."
            ),
            "",
            "## Unresolved Settings",
            "",
            (
                "- [ ] Items that must be completed later: Question: `[concrete owner "
                "question]`; state: `[not yet asked, asked and deferred, or unavailable "
                "through current safe tooling / manual review required]`; dependency: "
                "`[file, workflow, or GitHub setting]`; dependent-file status: "
                "`[not finalized, blocked, placeholder removed, local default withheld, "
                "or other concrete status]`"
            ),
            "",
            "## Resolution Evidence",
            "",
            "- [ ] No generated or adopted file ships unresolved placeholders or misleading defaults.",
            (
                "- [ ] Evidence captured for every resolved GitHub setting or policy decision: "
                "`[commit, PR, screenshot/link, connector result, API response note, or "
                "maintainer note]`"
            ),
            "- [ ] Deferred items copied into the adoption PR description, sync summary, or issue.",
        ]
    )


def format_issue_draft_skeletons() -> str:
    """Render copyable post-adoption issue draft skeletons."""
    return "\n".join(
        [
            "```markdown",
            "## Structural Follow-Up",
            "",
            "### Context",
            "",
            "Template adoption is complete. This issue handles one deferred structural "
            "follow-up in this repository only.",
            "",
            "### Scope",
            "",
            "- [Specific paths, commands, or workflow roots to change]",
            "- Protected instruction files in scope: [yes/no].",
            "",
            "### Non-Goals",
            "",
            "- Do not revisit template adoption decisions.",
            "- Do not change unrelated structure or formatting.",
            "",
            "### Acceptance Criteria",
            "",
            "- [Observable result]",
            "- Any touched file with `Last Updated` or `**Version:**` metadata is synchronized.",
            "",
            "### Validation",
            "",
            "- [Command or manual check]",
            "",
            "## Policy Follow-Up",
            "",
            "### Context",
            "",
            "A first-adoption policy decision was deferred and must be resolved before the "
            "dependent file is final.",
            "",
            "### Scope",
            "",
            "- Decision: [concrete maintainer question]",
            "- Dependent files/settings: [paths or GitHub setting]",
            "",
            "### Acceptance Criteria",
            "",
            "- The decision is recorded in `_TODO-repo-init.md`, `.template-sync/marker.yml`, "
            "or an equivalent committed adoption note.",
            "- Dependent files no longer contain unresolved placeholders or misleading defaults.",
            "",
            "### Validation",
            "",
            "- [Command or manual check]",
            "```",
        ]
    )


def format_preflight_report(
    *,
    marker_path: Path,
    manifest_path: Path,
    todo_path: Path,
    repo_root: Path,
    marker_data: MarkerData,
    manifest_modules: frozenset[str],
    discovery: RepositoryDiscovery,
    ledger_rows: tuple[LedgerRow, ...],
    ledger_document: str,
) -> str:
    """Render the read-only first-adoption preflight report."""
    marker_relative = repository_relative_path(marker_path, repo_root)
    manifest_relative = repository_relative_path(manifest_path, repo_root)
    todo_relative = repository_relative_path(todo_path, repo_root)

    lines = [
        "# First-Adoption Preflight Report",
        "",
        (
            "Read-only planning artifact. This mode inspects local repository state, "
            "optionally reads GitHub metadata only when explicitly requested, and does "
            "not write files or modify repository settings."
        ),
        "",
        "## Repository Discovery",
        "",
        f"- Repository owner/name: `{discovery.owner_name or 'unknown'}`",
        f"- Remotes: {format_remotes(discovery.remotes)}",
        f"- Current branch: `{discovery.current_branch or 'unknown'}`",
        f"- Likely default branch: `{discovery.likely_default_branch or 'manual review required'}`",
        f"- Working tree: {format_working_tree(discovery.working_tree_entries)}",
        f"- Workflows: {format_limited_path_list(discovery.workflows, 'none found')}",
        (
            "- Issue templates: "
            f"{format_limited_path_list(discovery.issue_templates, 'none found')}"
        ),
        f"- PR templates: {format_limited_path_list(discovery.pr_templates, 'none found')}",
        (
            "- Security/conduct/CODEOWNERS files: "
            f"{format_limited_path_list(discovery.security_files, 'none found')}"
        ),
        (
            "- Agent instruction files: "
            f"{format_limited_path_list(discovery.agent_instruction_files, 'none found')}"
        ),
        (
            "- Language/tooling stacks inferred from local files: "
            + (", ".join(discovery.tooling_stacks) if discovery.tooling_stacks else "none found")
        ),
        f"- Marker: `{marker_relative}` ({format_marker_summary(marker_data, discovery.marker_present)})",
        (
            f"- First-adoption checklist: `{todo_relative}` "
            f"({'found' if discovery.adoption_note_present else 'not found'})"
        ),
        "",
        format_github_metadata(discovery.github_metadata),
        "",
        "## Maintainer Questionnaire",
        "",
        format_maintainer_questionnaire(discovery),
        "",
        "## `_TODO-repo-init.md` Starter",
        "",
        "```markdown",
        format_todo_starter(discovery, marker_data),
        "```",
        "",
        "## Module-Selection Decision Aid",
        "",
        (
            "Use this table to choose marker `included_modules`. The adoption ledger "
            "below remains the reused path-level decision view."
        ),
        "",
        format_module_selection_aid(manifest_modules, marker_data),
        "",
        "## Protected-File Authorization Questions",
        "",
        format_protected_authorization_questions(ledger_rows),
        "",
        "## Required Structural Alignment Candidates",
        "",
        format_structural_alignment_candidates(discovery),
        "",
        "## Post-Adoption Issue Draft Skeletons",
        "",
        format_issue_draft_skeletons(),
        "",
        "## Validation Plan Suggestions",
        "",
        format_validation_plan(ledger_rows),
        "",
        "## Reused Adoption Ledger",
        "",
        (
            f"The following section is rendered by the existing adoption-ledger helpers from "
            f"`{manifest_relative}` and `{marker_relative}`."
        ),
        "",
        ledger_document,
    ]
    return "\n".join(lines)


def write_candidate_table(repo_root: Path, output_path: Path, candidate_table: str) -> None:
    """Write the rendered candidate table to a repository-contained path."""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(candidate_table + "\n", encoding="utf-8")
    except OSError as error:
        output_relative = repository_relative_path(output_path, repo_root)
        error_summary = f"{type(error).__name__}: {error.strerror or 'I/O error'}"
        raise CandidateGenerationError(
            f"Unable to write candidate table to {output_relative}: {error_summary}"
        ) from error


def write_adoption_ledger(repo_root: Path, output_path: Path, ledger_document: str) -> None:
    """Write the rendered adoption ledger to a repository-contained path."""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(ledger_document + "\n", encoding="utf-8")
    except OSError as error:
        output_relative = repository_relative_path(output_path, repo_root)
        error_summary = f"{type(error).__name__}: {error.strerror or 'I/O error'}"
        raise CandidateGenerationError(
            f"Unable to write adoption ledger to {output_relative}: {error_summary}"
        ) from error


def load_and_validate_inputs(
    repo_root: Path,
    marker_path: Path,
    manifest_path: Path,
    marker_schema_path: Path,
    manifest_schema_path: Path,
) -> tuple[MarkerData, frozenset[str], tuple[ManifestMapping, ...]]:
    """Load and schema-validate marker and manifest inputs."""
    marker = load_yaml_mapping(marker_path, repo_root)
    manifest = load_yaml_mapping(manifest_path, repo_root)
    marker_schema = load_json_mapping(marker_schema_path, repo_root)
    manifest_schema = load_json_mapping(manifest_schema_path, repo_root)

    validate_schema(marker, marker_schema, marker_path, repo_root)
    validate_schema(manifest, manifest_schema, manifest_path, repo_root)

    marker_data = parse_marker(marker)
    manifest_modules, mappings = parse_manifest(manifest)
    return marker_data, manifest_modules, mappings


def print_report(
    *,
    marker_path: Path,
    manifest_path: Path,
    repo_root: Path,
    range_base_ref: str,
    range_base_sha: str,
    range_base_source: str,
    range_head_ref: str,
    range_head_sha: str,
    manifest_modules: frozenset[str],
    marker_data: MarkerData,
    rows: tuple[CandidateRow, ...],
    candidate_table: str,
    procedure_warning: str | None,
    write_candidates_path: Path | None,
    write_ledger_path: Path | None,
    ledger_document: str | None,
) -> None:
    """Print the Markdown candidate table report."""
    marker_relative = repository_relative_path(marker_path, repo_root)
    manifest_relative = repository_relative_path(manifest_path, repo_root)
    unknown_marker_modules = marker_data.included_modules - manifest_modules

    print("# Template Sync Candidate Table")
    print()
    print(f"- Marker: `{marker_relative}`")
    print(f"- Manifest: `{manifest_relative}`")
    print(f"- Range base: `{range_base_sha}` from `{range_base_ref}` ({range_base_source})")
    print(f"- Range head: `{range_head_sha}` from `{range_head_ref}`")
    print(f"- Modeled diff command: `{modeled_diff_command(range_base_sha, range_head_sha)}`")
    if procedure_warning is not None:
        print(f"- {procedure_warning}")
    if write_candidates_path is not None:
        print(
            "- Saved candidate table: "
            f"`{repository_relative_path(write_candidates_path, repo_root)}`"
        )
    if write_ledger_path is not None:
        print(
            "- Saved adoption ledger: "
            f"`{repository_relative_path(write_ledger_path, repo_root)}`"
        )
    print(
        "- Included modules: "
        + (", ".join(f"`{module}`" for module in sorted(marker_data.included_modules)) or "none")
    )
    if unknown_marker_modules:
        print(
            "- Unknown marker modules: "
            + ", ".join(f"`{module}`" for module in sorted(unknown_marker_modules))
        )
    print()
    print(
        "This table is a decision aid only. The manual review process in "
        "`TEMPLATE_UPDATE_PROCEDURE.md` remains authoritative."
    )
    print()

    if not rows:
        print("No changed paths found in the reviewed range.")
        if ledger_document is not None:
            print()
            print(ledger_document)
        return

    print(candidate_table)
    if ledger_document is not None:
        print()
        print(ledger_document)


def print_ledger_only_report(
    *,
    ledger_document: str,
    write_ledger_path: Path | None,
    repo_root: Path,
) -> None:
    """Print the adoption-ledger-only report."""
    if write_ledger_path is not None:
        print(
            "Saved adoption ledger: " f"`{repository_relative_path(write_ledger_path, repo_root)}`"
        )
        print()
    print(ledger_document)


def fail(message: str) -> NoReturn:
    """Print an error and exit non-zero."""
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def main(argv: list[str] | None = None) -> int:
    """Generate the sync candidate table."""
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        if args.ledger_only and args.write_candidates is not None:
            raise CandidateGenerationError("--write-candidates cannot be used with --ledger-only.")
        if args.summary and args.write_candidates is not None:
            raise CandidateGenerationError("--write-candidates cannot be used with --summary.")
        if args.summary and args.write_ledger is not None:
            raise CandidateGenerationError("--write-ledger cannot be used with --summary.")
        if args.preflight and args.write_candidates is not None:
            raise CandidateGenerationError("--write-candidates cannot be used with --preflight.")
        if args.preflight and args.write_ledger is not None:
            raise CandidateGenerationError("--write-ledger cannot be used with --preflight.")
        if args.include_github_metadata and not args.preflight:
            raise CandidateGenerationError(
                "--include-github-metadata can only be used with --preflight."
            )

        repo_root = resolve_repo_root(args.repo_root)
        marker_path = resolve_repo_path(repo_root, args.marker)
        manifest_path = resolve_repo_path(repo_root, args.manifest)
        marker_schema_path = resolve_repo_path(repo_root, args.marker_schema)
        manifest_schema_path = resolve_repo_path(repo_root, args.manifest_schema)
        todo_path = resolve_repo_path(repo_root, args.todo_file)
        write_candidates_path = (
            resolve_repo_path(repo_root, args.write_candidates)
            if args.write_candidates is not None
            else None
        )
        write_ledger_path = (
            resolve_repo_path(repo_root, args.write_ledger)
            if args.write_ledger is not None
            else None
        )

        if args.preflight:
            marker_data, manifest_modules, mappings = load_preflight_inputs(
                repo_root=repo_root,
                marker_path=marker_path,
                manifest_path=manifest_path,
                marker_schema_path=marker_schema_path,
                manifest_schema_path=manifest_schema_path,
            )
            todo_items = load_todo_items(todo_path, repo_root)
            ledger_rows = build_adoption_ledger_rows(
                marker_data=marker_data,
                manifest_modules=manifest_modules,
                mappings=mappings,
                todo_items=todo_items,
                todo_path=todo_path,
                repo_root=repo_root,
                default_adoption_mode=args.adoption_mode,
            )
            ledger_document = format_adoption_ledger(
                marker_path=marker_path,
                manifest_path=manifest_path,
                todo_path=todo_path,
                repo_root=repo_root,
                marker_data=marker_data,
                rows=ledger_rows,
                default_adoption_mode=args.adoption_mode,
            )
            discovery = discover_repository_state(
                repo_root=repo_root,
                marker_path=marker_path,
                todo_path=todo_path,
                include_github_metadata=args.include_github_metadata,
            )
            print(
                format_preflight_report(
                    marker_path=marker_path,
                    manifest_path=manifest_path,
                    todo_path=todo_path,
                    repo_root=repo_root,
                    marker_data=marker_data,
                    manifest_modules=manifest_modules,
                    discovery=discovery,
                    ledger_rows=ledger_rows,
                    ledger_document=ledger_document,
                )
            )
            return 0

        if args.summary:
            if marker_path.exists():
                marker_data, manifest_modules, mappings = load_and_validate_inputs(
                    repo_root=repo_root,
                    marker_path=marker_path,
                    manifest_path=manifest_path,
                    marker_schema_path=marker_schema_path,
                    manifest_schema_path=manifest_schema_path,
                )
            else:
                marker_data, manifest_modules, mappings = load_preflight_inputs(
                    repo_root=repo_root,
                    marker_path=marker_path,
                    manifest_path=manifest_path,
                    marker_schema_path=marker_schema_path,
                    manifest_schema_path=manifest_schema_path,
                )
            todo_state = load_summary_todo_state(todo_path, repo_root)
            summary_rows = build_adoption_ledger_rows(
                marker_data=marker_data,
                manifest_modules=manifest_modules,
                mappings=mappings,
                todo_items=(),
                todo_path=todo_path,
                repo_root=repo_root,
                default_adoption_mode=args.adoption_mode,
            )
            print(
                format_adoption_summary(
                    marker_path=marker_path,
                    manifest_path=manifest_path,
                    todo_path=todo_path,
                    repo_root=repo_root,
                    marker_data=marker_data,
                    manifest_modules=manifest_modules,
                    rows=summary_rows,
                    todo_state=todo_state,
                    default_adoption_mode=args.adoption_mode,
                )
            )
            return 0

        if args.ledger_only and not marker_path.exists():
            marker_data, manifest_modules, mappings = load_preflight_inputs(
                repo_root=repo_root,
                marker_path=marker_path,
                manifest_path=manifest_path,
                marker_schema_path=marker_schema_path,
                manifest_schema_path=manifest_schema_path,
            )
        else:
            marker_data, manifest_modules, mappings = load_and_validate_inputs(
                repo_root=repo_root,
                marker_path=marker_path,
                manifest_path=manifest_path,
                marker_schema_path=marker_schema_path,
                manifest_schema_path=manifest_schema_path,
            )
        ledger_document = None
        if args.ledger or args.ledger_only or write_ledger_path is not None:
            todo_items = load_todo_items(todo_path, repo_root)
            ledger_output_dir = write_ledger_path.parent if write_ledger_path is not None else None
            ledger_rows = build_adoption_ledger_rows(
                marker_data=marker_data,
                manifest_modules=manifest_modules,
                mappings=mappings,
                todo_items=todo_items,
                todo_path=todo_path,
                repo_root=repo_root,
                default_adoption_mode=args.adoption_mode,
                ledger_output_dir=ledger_output_dir,
            )
            ledger_document = format_adoption_ledger(
                marker_path=marker_path,
                manifest_path=manifest_path,
                todo_path=todo_path,
                repo_root=repo_root,
                marker_data=marker_data,
                rows=ledger_rows,
                default_adoption_mode=args.adoption_mode,
            )

        if args.ledger_only:
            if ledger_document is None:
                raise CandidateGenerationError("Unable to generate adoption ledger.")
            if write_ledger_path is not None:
                write_adoption_ledger(repo_root, write_ledger_path, ledger_document)
            print_ledger_only_report(
                ledger_document=ledger_document,
                write_ledger_path=write_ledger_path,
                repo_root=repo_root,
            )
            return 0

        range_base_ref, range_base_sha, range_base_source = resolve_range_base_ref(
            repo_root,
            args.range_base,
            marker_data,
        )
        range_head_ref, range_head_sha = resolve_range_head_ref(repo_root, args.range_head)
        verify_reachable_range(repo_root, range_base_sha, range_head_sha)

        entries = changed_paths(repo_root, range_base_sha, range_head_sha)
        rows = tuple(build_candidate_row(entry, marker_data, mappings) for entry in entries)
        candidate_table = format_table(rows)
        procedure_warning = stale_procedure_warning(repo_root, range_head_sha)
        if write_candidates_path is not None:
            write_candidate_table(repo_root, write_candidates_path, candidate_table)
        if write_ledger_path is not None:
            if ledger_document is None:
                raise CandidateGenerationError("Unable to generate adoption ledger.")
            write_adoption_ledger(repo_root, write_ledger_path, ledger_document)
    except (CandidateGenerationError, MarkerValidationError) as error:
        fail(str(error))

    print_report(
        marker_path=marker_path,
        manifest_path=manifest_path,
        repo_root=repo_root,
        range_base_ref=range_base_ref,
        range_base_sha=range_base_sha,
        range_base_source=range_base_source,
        range_head_ref=range_head_ref,
        range_head_sha=range_head_sha,
        manifest_modules=manifest_modules,
        marker_data=marker_data,
        rows=rows,
        candidate_table=candidate_table,
        procedure_warning=procedure_warning,
        write_candidates_path=write_candidates_path,
        write_ledger_path=write_ledger_path,
        ledger_document=ledger_document if args.ledger else None,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
