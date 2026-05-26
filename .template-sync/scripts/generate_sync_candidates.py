"""Generate a marker-aware template sync candidate table."""

from __future__ import annotations

import argparse
import fnmatch
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NoReturn

from validate_marker import (
    DEFAULT_MANIFEST_PATH,
    DEFAULT_MANIFEST_SCHEMA_PATH,
    DEFAULT_MARKER_PATH,
    DEFAULT_MARKER_SCHEMA_PATH,
    LocalOverride,
    MarkerValidationError,
    load_json_mapping,
    load_yaml_mapping,
    normalize_manifest_pattern,
    normalize_repository_path,
    pattern_specificity,
    relation_modules,
    repository_relative_path,
    resolve_repo_path,
    resolve_repo_root,
    validate_schema,
)

DEFAULT_RANGE_HEAD_REF = "template/main"
DEFAULT_TODO_PATH = "_TODO-repo-init.md"
TEMPLATE_UPDATE_PROCEDURE_PATH = "TEMPLATE_UPDATE_PROCEDURE.md"
PROTECTED_EXACT_PATHS = frozenset(
    {
        ".github/copilot-instructions.md",
        ".hermes.md",
        "AGENTS.md",
        "CLAUDE.md",
        "GEMINI.md",
    }
)
PROTECTED_GLOB_PATTERNS = (
    ".github/instructions/**",
    ".cursor/rules/**",
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
        "pre-commit run validate-template-sync-marker-valid-examples --all-files",
        "pre-commit run validate-example-config-schema --all-files",
        "pre-commit run validate-template-sync-manifest-schema --all-files",
        "pre-commit run validate-template-sync-marker-schema --all-files",
        "pytest tests/test_schema_examples.py -v",
    ),
    "template-onboarding": (
        "npm run lint:md",
        "npm run lint:md:links",
        "npm run lint:md:nested",
    ),
    "template-sync-support": (
        "python .template-sync/scripts/validate_marker.py --require-marker",
        "pre-commit run validate-template-sync-manifest --all-files",
        "pre-commit run validate-template-sync-marker --all-files",
    ),
    "terraform": (
        "terraform fmt -check -recursive",
        "tflint --recursive",
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
class DeferredProtectedCandidate:
    """A protected path carried forward in the marker for owner authorization."""

    path: str
    source_commit: str
    reason: str


@dataclass(frozen=True)
class MarkerData:
    """Marker values needed to evaluate changed upstream paths."""

    last_reviewed_template_commit: str | None
    included_modules: frozenset[str]
    local_overrides: tuple[LocalOverride, ...]
    deferred_candidates: tuple[DeferredProtectedCandidate, ...]


@dataclass(frozen=True)
class ManifestMapping:
    """One manifest path mapping row."""

    pattern: str
    requires_all: frozenset[str]
    requires_any: frozenset[str]
    notes: str | None
    unknown_modules: frozenset[str]


@dataclass(frozen=True)
class PathRelation:
    """The manifest module relation selected for a changed path."""

    patterns: tuple[str, ...]
    requires_all: frozenset[str]
    requires_any: frozenset[str]
    notes: tuple[str, ...]
    unknown_modules: frozenset[str]

    @property
    def is_cross_module(self) -> bool:
        """Return whether the relation spans multiple module concerns."""
        return bool(self.requires_any) or len(self.requires_all | self.requires_any) > 1

    @property
    def description(self) -> str:
        """Return a compact relation description for Markdown output."""
        parts: list[str] = []
        if self.requires_all:
            parts.append("requires all: " + ", ".join(sorted(self.requires_all)))
        if self.requires_any:
            parts.append("requires any: " + ", ".join(sorted(self.requires_any)))
        return "; ".join(parts) if parts else "no module relation"

    def is_retained_by(self, included_modules: frozenset[str]) -> bool:
        """Return whether marker modules satisfy this relation."""
        if not self.requires_all.issubset(included_modules):
            return False
        if self.requires_any and not self.requires_any.intersection(included_modules):
            return False
        return True


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
    protected_status: str
    notes: tuple[str, ...]


@dataclass(frozen=True)
class TodoItem:
    """One first-adoption checklist item that can be linked from the ledger."""

    line_number: int
    text: str
    is_complete: bool


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
    template_sync = marker.get("template_sync")
    if not isinstance(template_sync, dict):
        raise CandidateGenerationError("Marker must contain template_sync mapping.")

    last_reviewed = template_sync.get("last_reviewed_template_commit")
    if last_reviewed is not None and not isinstance(last_reviewed, str):
        raise CandidateGenerationError(
            "template_sync.last_reviewed_template_commit must be a string when present."
        )

    raw_included_modules = template_sync.get("included_modules")
    if not isinstance(raw_included_modules, list) or not all(
        isinstance(module, str) for module in raw_included_modules
    ):
        raise CandidateGenerationError("template_sync.included_modules must be a list of strings.")
    included_modules = frozenset(raw_included_modules)

    local_overrides: list[LocalOverride] = []
    for raw_override in template_sync.get("local_overrides", []):
        if not isinstance(raw_override, dict):
            raise CandidateGenerationError("Each local override must be a mapping.")
        raw_path = raw_override.get("path")
        default_decision = raw_override.get("default_decision")
        reason = raw_override.get("reason")
        if (
            not isinstance(raw_path, str)
            or not isinstance(default_decision, str)
            or not isinstance(reason, str)
        ):
            raise CandidateGenerationError(
                "Each local override must define string path, default_decision, and reason."
            )
        normalized_path, is_directory = normalize_repository_path(
            raw_path,
            "template_sync.local_overrides[].path",
        )
        local_overrides.append(
            LocalOverride(
                path=normalized_path,
                default_decision=default_decision,
                reason=reason,
                is_directory=is_directory,
            )
        )

    deferred_candidates: list[DeferredProtectedCandidate] = []
    for raw_candidate in template_sync.get("deferred_protected_candidates", []):
        if not isinstance(raw_candidate, dict):
            raise CandidateGenerationError("Each deferred protected candidate must be a mapping.")
        raw_path = raw_candidate.get("path")
        source_commit = raw_candidate.get("source_commit")
        reason = raw_candidate.get("reason")
        if (
            not isinstance(raw_path, str)
            or not isinstance(source_commit, str)
            or not isinstance(reason, str)
        ):
            raise CandidateGenerationError(
                "Each deferred protected candidate must define string path, source_commit, "
                "and reason."
            )
        normalized_path, _is_directory = normalize_repository_path(
            raw_path,
            "template_sync.deferred_protected_candidates[].path",
        )
        deferred_candidates.append(
            DeferredProtectedCandidate(
                path=normalized_path,
                source_commit=source_commit,
                reason=reason,
            )
        )

    return MarkerData(
        last_reviewed_template_commit=last_reviewed,
        included_modules=included_modules,
        local_overrides=tuple(local_overrides),
        deferred_candidates=tuple(deferred_candidates),
    )


def parse_manifest(manifest: dict[str, Any]) -> tuple[frozenset[str], tuple[ManifestMapping, ...]]:
    """Extract manifest modules and mapping rows without making owner decisions."""
    template_manifest = manifest.get("template_manifest")
    if not isinstance(template_manifest, dict):
        raise CandidateGenerationError("Manifest must contain template_manifest mapping.")

    raw_modules = template_manifest.get("modules")
    if not isinstance(raw_modules, list):
        raise CandidateGenerationError("template_manifest.modules must be a list.")

    module_names: set[str] = set()
    for raw_module in raw_modules:
        if not isinstance(raw_module, dict) or not isinstance(raw_module.get("name"), str):
            raise CandidateGenerationError("Every manifest module must define a string name.")
        module_names.add(raw_module["name"])

    raw_path_mappings = template_manifest.get("path_mappings")
    if not isinstance(raw_path_mappings, list):
        raise CandidateGenerationError("template_manifest.path_mappings must be a list.")

    mappings: list[ManifestMapping] = []
    for raw_mapping in raw_path_mappings:
        if not isinstance(raw_mapping, dict):
            raise CandidateGenerationError("Every path mapping must be a mapping.")
        raw_pattern = raw_mapping.get("pattern")
        if not isinstance(raw_pattern, str):
            raise CandidateGenerationError("Every path mapping must define a string pattern.")
        notes = raw_mapping.get("notes")
        if notes is not None and not isinstance(notes, str):
            raise CandidateGenerationError(f"{raw_pattern} notes must be a string.")

        requires_all = relation_modules(raw_mapping, "requires_all")
        requires_any = relation_modules(raw_mapping, "requires_any")
        referenced_modules = requires_all | requires_any
        mappings.append(
            ManifestMapping(
                pattern=normalize_manifest_pattern(raw_pattern),
                requires_all=requires_all,
                requires_any=requires_any,
                notes=notes,
                unknown_modules=frozenset(referenced_modules - module_names),
            )
        )

    return frozenset(module_names), tuple(mappings)


def selected_relation_for_path(
    relative_path: str,
    mappings: tuple[ManifestMapping, ...],
) -> PathRelation | None:
    """Return the best manifest relation for ``relative_path``."""
    matches: list[tuple[tuple[int, int, int], ManifestMapping]] = []
    for mapping in mappings:
        if fnmatch.fnmatchcase(relative_path, mapping.pattern):
            matches.append((pattern_specificity(mapping.pattern), mapping))

    if not matches:
        return None

    best_specificity = max(specificity for specificity, _mapping in matches)
    selected = [mapping for specificity, mapping in matches if specificity == best_specificity]
    patterns: list[str] = []
    requires_all: set[str] = set()
    requires_any: set[str] = set()
    notes: list[str] = []
    unknown_modules: set[str] = set()
    for mapping in selected:
        patterns.append(mapping.pattern)
        requires_all.update(mapping.requires_all)
        requires_any.update(mapping.requires_any)
        unknown_modules.update(mapping.unknown_modules)
        if mapping.notes:
            notes.append(mapping.notes)

    return PathRelation(
        patterns=tuple(patterns),
        requires_all=frozenset(requires_all),
        requires_any=frozenset(requires_any),
        notes=tuple(notes),
        unknown_modules=frozenset(unknown_modules),
    )


def describe_relation(relation: PathRelation | None) -> str:
    """Return a human-readable module relation description, or ``unmapped``."""
    return relation.description if relation is not None else "unmapped"


def relations_match(left: PathRelation | None, right: PathRelation | None) -> bool:
    """Return whether two relations resolve to the same module mapping."""
    if left is None or right is None:
        return left is None and right is None
    return left.requires_all == right.requires_all and left.requires_any == right.requires_any


def is_protected_instruction_path(relative_path: str) -> bool:
    """Return whether ``relative_path`` is a protected instruction/governance file."""
    if relative_path in PROTECTED_EXACT_PATHS:
        return True
    return any(fnmatch.fnmatchcase(relative_path, pattern) for pattern in PROTECTED_GLOB_PATTERNS)


def has_wildcard(pattern: str) -> bool:
    """Return whether ``pattern`` contains shell-style wildcard syntax."""
    return any(wildcard in pattern for wildcard in "*?[")


def is_protected_manifest_pattern(pattern: str) -> bool:
    """Return whether a manifest pattern names protected instruction paths."""
    if not has_wildcard(pattern):
        return is_protected_instruction_path(pattern)
    if pattern in PROTECTED_GLOB_PATTERNS:
        return True
    if pattern.startswith(".github/instructions/") or pattern.startswith(".cursor/rules/"):
        return True
    return any(fnmatch.fnmatchcase(path, pattern) for path in PROTECTED_EXACT_PATHS)


def manifest_pattern_matches_path(pattern: str, relative_path: str) -> bool:
    """Return whether a manifest pattern could cover ``relative_path``."""
    if has_wildcard(pattern):
        return fnmatch.fnmatchcase(relative_path, pattern)
    return pattern == relative_path


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


def todo_item_link(todo_path: Path, repo_root: Path, item: TodoItem) -> str:
    """Return a Markdown link to one checklist line."""
    todo_relative = repository_relative_path(todo_path, repo_root)
    return f"[line {item.line_number}]({todo_relative}#L{item.line_number})"


def matching_todo_links(
    *,
    path: str,
    modules: frozenset[str],
    is_protected: bool,
    todo_items: tuple[TodoItem, ...],
    todo_path: Path,
    repo_root: Path,
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
            links.append(todo_item_link(todo_path, repo_root, item))

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


def build_manifest_ledger_row(
    *,
    mapping: ManifestMapping,
    marker_data: MarkerData,
    manifest_modules: frozenset[str],
    todo_items: tuple[TodoItem, ...],
    todo_path: Path,
    repo_root: Path,
    default_adoption_mode: str,
) -> tuple[LedgerRow, tuple[LocalOverride, ...]]:
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

    if is_protected and decision != "needs maintainer decision":
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
            adoption_mode=adoption_mode_for_modules(
                modules,
                local_overrides,
                is_protected,
                default_adoption_mode,
            ),
            todo_link=matching_todo_links(
                path=mapping.pattern,
                modules=modules,
                is_protected=is_protected,
                todo_items=todo_items,
                todo_path=todo_path,
                repo_root=repo_root,
            ),
            validation_commands=validation_commands_for_modules(modules),
        ),
        local_overrides,
    )


def build_unmatched_local_override_row(
    *,
    local_override: LocalOverride,
    mappings: tuple[ManifestMapping, ...],
    todo_items: tuple[TodoItem, ...],
    todo_path: Path,
    repo_root: Path,
    default_adoption_mode: str,
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
        manifest_modules=relation.description if relation is not None else "unmapped",
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
        ),
        validation_commands=validation_commands_for_modules(modules),
    )


def build_manual_todo_ledger_row(
    *,
    todo_item: TodoItem,
    todo_path: Path,
    repo_root: Path,
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
        todo_link=todo_item_link(todo_path, repo_root, todo_item),
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
) -> tuple[LedgerRow, ...]:
    """Build the generated adoption ledger rows."""
    rows: list[LedgerRow] = []
    matched_overrides: set[LocalOverride] = set()
    for mapping in mappings:
        row, local_overrides = build_manifest_ledger_row(
            mapping=mapping,
            marker_data=marker_data,
            manifest_modules=manifest_modules,
            todo_items=todo_items,
            todo_path=todo_path,
            repo_root=repo_root,
            default_adoption_mode=default_adoption_mode,
        )
        rows.append(row)
        matched_overrides.update(local_overrides)

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
            )
        )

    for todo_item in todo_items:
        rows.append(
            build_manual_todo_ledger_row(
                todo_item=todo_item,
                todo_path=todo_path,
                repo_root=repo_root,
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
        "Deferred protected candidate | Protected instruction/governance file | Notes |"
    )
    divider = "| --- | --- | --- | --- | --- | --- | --- | --- |"
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
