"""Generate a marker-aware template sync candidate table."""

from __future__ import annotations

import argparse
import fnmatch
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
        ["rev-parse", "--verify", f"{raw_ref}^{{commit}}"],
        check=False,
    )
    return result.returncode == 0


def resolve_commit(repo_root: Path, raw_ref: str, label: str) -> str:
    """Resolve a commit-ish ref to a full commit SHA."""
    result = run_git(
        repo_root,
        ["rev-parse", "--verify", f"{raw_ref}^{{commit}}"],
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
            "--find-renames",
            f"{range_base_sha}..{range_head_sha}",
            "--",
        ],
    )
    entries = [parse_name_status_line(line) for line in result.stdout.splitlines() if line.strip()]
    return tuple(entries)


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
        notes.append("Protected instruction file; explicit owner authorization is required.")

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


def markdown_cell(value: str) -> str:
    """Escape a value for inclusion in a Markdown table cell."""
    return value.replace("\n", "<br>").replace("|", r"\|")


def format_table(rows: tuple[CandidateRow, ...]) -> str:
    """Render candidate rows as a Markdown table."""
    header = (
        "| Path | Change | Matched module relation | Retained status | Local override | "
        "Deferred protected candidate | Protected instruction file | Notes |"
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
        return

    print(format_table(rows))


def fail(message: str) -> NoReturn:
    """Print an error and exit non-zero."""
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def main(argv: list[str] | None = None) -> int:
    """Generate the sync candidate table."""
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        repo_root = resolve_repo_root(args.repo_root)
        marker_path = resolve_repo_path(repo_root, args.marker)
        manifest_path = resolve_repo_path(repo_root, args.manifest)
        marker_schema_path = resolve_repo_path(repo_root, args.marker_schema)
        manifest_schema_path = resolve_repo_path(repo_root, args.manifest_schema)

        marker_data, manifest_modules, mappings = load_and_validate_inputs(
            repo_root=repo_root,
            marker_path=marker_path,
            manifest_path=manifest_path,
            marker_schema_path=marker_schema_path,
            manifest_schema_path=manifest_schema_path,
        )
        range_base_ref, range_base_sha, range_base_source = resolve_range_base_ref(
            repo_root,
            args.range_base,
            marker_data,
        )
        range_head_ref, range_head_sha = resolve_range_head_ref(repo_root, args.range_head)
        verify_reachable_range(repo_root, range_base_sha, range_head_sha)

        entries = changed_paths(repo_root, range_base_sha, range_head_sha)
        rows = tuple(build_candidate_row(entry, marker_data, mappings) for entry in entries)
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
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
