"""Validate a downstream template sync marker against the on-disk file set."""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Collection, Iterable, NoReturn

import jsonschema
import yaml  # type: ignore[import-untyped]

DEFAULT_MARKER_PATH = ".template-sync/marker.yml"
DEFAULT_MANIFEST_PATH = ".template-sync/manifest.yml"
DEFAULT_MARKER_SCHEMA_PATH = "schemas/template-sync-marker.schema.json"
DEFAULT_MANIFEST_SCHEMA_PATH = "schemas/template-sync-manifest.schema.json"
DEFAULT_REMOVE_LOCAL_AUTHORIZATION_TOKENS = ("remov", "delet")
SKIPPED_DISCOVERY_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "build",
    "dist",
    "node_modules",
    "__pycache__",
}
REMOVAL_DECISION = "REMOVE-LOCAL"


class MarkerValidationError(Exception):
    """Raised when marker-aware validation cannot produce a clean result."""


@dataclass(frozen=True)
class LocalOverride:
    """A marker local override path that suppresses consistency checks."""

    path: str
    default_decision: str
    reason: str
    is_directory: bool

    def matches(self, relative_path: str) -> bool:
        """Return whether this override applies to ``relative_path``."""
        if relative_path == self.path:
            return True
        if self.is_directory:
            return relative_path.startswith(f"{self.path}/")
        return False


@dataclass(frozen=True)
class DeferredProtectedCandidate:
    """A protected path awaiting owner authorization for an upstream change."""

    path: str
    source_commit: str
    reason: str


@dataclass(frozen=True)
class ProtectedFileDecision:
    """A path-scoped protected-file decision recorded in the marker."""

    path: str
    decision: str
    adoption_mode: str | None
    authorization_basis: str | None
    authorized_scope: str | None
    tailored_authorization_basis: str | None
    reason: str | None


@dataclass(frozen=True)
class MarkerPathOverlap:
    """Side-by-side marker records that apply to the same protected path."""

    path: str
    protected_decision: ProtectedFileDecision
    local_overrides: tuple[LocalOverride, ...]
    deferred_candidates: tuple[DeferredProtectedCandidate, ...]


@dataclass(frozen=True)
class PathRelation:
    """The manifest module relation selected for a repository path."""

    patterns: tuple[str, ...]
    requires_all: frozenset[str]
    requires_any: frozenset[str]

    @property
    def description(self) -> str:
        """Return a compact human-readable relation summary."""
        parts: list[str] = []
        if self.requires_all:
            parts.append("requires all: " + ", ".join(sorted(self.requires_all)))
        if self.requires_any:
            parts.append("requires any: " + ", ".join(sorted(self.requires_any)))
        return "; ".join(parts) if parts else "no module relation"

    def is_retained_by(self, included_modules: set[str]) -> bool:
        """Return whether ``included_modules`` satisfies this path relation."""
        if not self.requires_all.issubset(included_modules):
            return False
        if self.requires_any and not self.requires_any.intersection(included_modules):
            return False
        return True


@dataclass(frozen=True)
class ManifestMapping:
    """One path mapping row from the template sync manifest."""

    pattern: str
    requires_all: frozenset[str]
    requires_any: frozenset[str]

    @property
    def is_concrete(self) -> bool:
        """Return whether this mapping names a concrete path rather than a glob."""
        return not any(wildcard in self.pattern for wildcard in "*?[")


@dataclass(frozen=True)
class MarkerValidationReport:
    """Validation result details to print for the operator."""

    included_modules: tuple[str, ...]
    manifest_mapping_count: int
    unsafe_managed_paths: tuple[str, ...]
    missing_expected_files: tuple[tuple[str, PathRelation], ...]
    leftover_files: tuple[tuple[str, PathRelation], ...]
    local_overrides: tuple[LocalOverride, ...]
    deferred_candidates: tuple[DeferredProtectedCandidate, ...]
    protected_decisions: tuple[ProtectedFileDecision, ...]
    marker_path_overlaps: tuple[MarkerPathOverlap, ...]

    @property
    def has_failures(self) -> bool:
        """Return whether actual retained-template inconsistencies were found."""
        return bool(self.unsafe_managed_paths or self.missing_expected_files or self.leftover_files)


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Validate .template-sync/marker.yml against .template-sync/manifest.yml "
            "and the current repository files."
        ),
        epilog=(
            "Protected-file decision overlap checks fail when the same path has "
            "different protected_file_decisions.decision and local_overrides[].default_decision "
            "values, or when the same path appears in both protected_file_decisions and "
            "deferred_protected_candidates."
        ),
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help=(
            "Repository root to validate. Defaults to the parent of the .template-sync "
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
        "--require-marker",
        action="store_true",
        help="Fail when the marker file is absent instead of treating the run as a no-op.",
    )
    parser.add_argument(
        "--strict-remove-local-phrasing",
        action="store_true",
        help=(
            "Fail REMOVE-LOCAL protected-file decisions whose authorization_basis "
            "does not contain a configured removal token. Off by default."
        ),
    )
    parser.add_argument(
        "--remove-local-authorization-token",
        action="append",
        default=None,
        metavar="TOKEN",
        help=(
            "Case-insensitive substring token accepted by --strict-remove-local-phrasing. "
            "May be repeated. Defaults to: remov, delet."
        ),
    )
    parser.add_argument(
        "--remove-local-authorization-tokens",
        default=None,
        metavar="TOKENS",
        help=(
            "Comma-separated case-insensitive substring tokens accepted by "
            "--strict-remove-local-phrasing. Overrides are combined with repeated "
            "--remove-local-authorization-token values."
        ),
    )
    return parser.parse_args(argv)


def default_repo_root() -> Path:
    """Return the repository root implied by this script's committed location."""
    return Path(__file__).resolve().parents[2]


def resolve_repo_root(raw_repo_root: str | None) -> Path:
    """Resolve and validate the repository root argument."""
    repo_root = Path(raw_repo_root).expanduser() if raw_repo_root else default_repo_root()
    resolved = repo_root.resolve()
    if not resolved.is_dir():
        raise MarkerValidationError(
            f"Repository root does not exist or is not a directory: {repo_root}"
        )
    return resolved


def resolve_repo_path(repo_root: Path, raw_path: str) -> Path:
    """Resolve ``raw_path`` inside ``repo_root`` and reject path traversal."""
    candidate = Path(raw_path)
    if candidate.is_absolute():
        path = candidate.resolve()
    else:
        path = (repo_root / candidate).resolve()

    try:
        path.relative_to(repo_root)
    except ValueError as error:
        raise MarkerValidationError(f"Path escapes the repository root: {raw_path}") from error
    return path


def repository_relative_path(path: Path, repo_root: Path) -> str:
    """Return a POSIX-style path relative to the repository root."""
    return path.relative_to(repo_root).as_posix()


def load_json_mapping(path: Path, repo_root: Path) -> dict[str, Any]:
    """Load a JSON file that must contain a mapping."""
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        relative_path = repository_relative_path(path, repo_root)
        raise MarkerValidationError(f"Unable to read {relative_path}: {error}") from error
    except json.JSONDecodeError as error:
        relative_path = repository_relative_path(path, repo_root)
        raise MarkerValidationError(f"Invalid JSON in {relative_path}: {error}") from error
    if not isinstance(parsed, dict):
        relative_path = repository_relative_path(path, repo_root)
        raise MarkerValidationError(f"{relative_path} must contain a JSON object.")
    return parsed


def load_yaml_mapping(path: Path, repo_root: Path) -> dict[str, Any]:
    """Load a YAML file that must contain a mapping."""
    try:
        parsed = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as error:
        relative_path = repository_relative_path(path, repo_root)
        raise MarkerValidationError(f"Unable to read {relative_path}: {error}") from error
    except yaml.YAMLError as error:
        relative_path = repository_relative_path(path, repo_root)
        raise MarkerValidationError(f"Invalid YAML in {relative_path}: {error}") from error
    if not isinstance(parsed, dict):
        relative_path = repository_relative_path(path, repo_root)
        raise MarkerValidationError(f"{relative_path} must contain a YAML mapping.")
    return parsed


def validate_schema(
    document: dict[str, Any], schema: dict[str, Any], document_path: Path, repo_root: Path
) -> None:
    """Validate a loaded document against a Draft 2020-12 JSON Schema."""
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(document), key=lambda error: error.json_path)
    if not errors:
        return

    relative_path = repository_relative_path(document_path, repo_root)
    messages = "\n".join(f"  - {error.json_path}: {error.message}" for error in errors[:10])
    remaining = len(errors) - 10
    if remaining > 0:
        messages += f"\n  - ... {remaining} more validation error(s)"
    raise MarkerValidationError(f"Schema validation failed for {relative_path}:\n{messages}")


def normalize_repository_path(raw_path: str, field_name: str) -> tuple[str, bool]:
    """Normalize a marker path and return ``(path, is_directory_prefix)``."""
    if "\\" in raw_path:
        raise MarkerValidationError(f"{field_name} must use POSIX separators: {raw_path}")
    if raw_path.startswith("/"):
        raise MarkerValidationError(f"{field_name} must be repository-relative: {raw_path}")

    is_directory = raw_path.endswith("/")
    stripped = raw_path.strip("/")
    if not stripped:
        raise MarkerValidationError(f"{field_name} must not be empty: {raw_path}")
    parts = stripped.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise MarkerValidationError(f"{field_name} must not contain traversal segments: {raw_path}")
    return stripped, is_directory


def normalize_manifest_pattern(raw_pattern: str) -> str:
    """Validate and normalize a manifest path pattern."""
    if "\\" in raw_pattern:
        raise MarkerValidationError(f"Manifest patterns must use POSIX separators: {raw_pattern}")
    if raw_pattern.startswith("/"):
        raise MarkerValidationError(f"Manifest patterns must be repository-relative: {raw_pattern}")
    parts = raw_pattern.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise MarkerValidationError(
            f"Manifest patterns must not contain empty or traversal segments: {raw_pattern}"
        )
    return raw_pattern


def relation_modules(mapping: dict[str, Any], relation_key: str) -> frozenset[str]:
    """Return module names for one manifest relation key."""
    modules = mapping.get(relation_key, [])
    if not isinstance(modules, list):
        pattern = mapping.get("pattern", "<unknown>")
        raise MarkerValidationError(f"{pattern} {relation_key} must be a list.")
    if not all(isinstance(module, str) for module in modules):
        pattern = mapping.get("pattern", "<unknown>")
        raise MarkerValidationError(f"{pattern} {relation_key} values must be strings.")
    return frozenset(modules)


def parse_manifest_mappings(
    manifest: dict[str, Any],
) -> tuple[set[str], tuple[ManifestMapping, ...]]:
    """Extract module definitions and path mappings from a validated manifest."""
    template_manifest = manifest.get("template_manifest")
    if not isinstance(template_manifest, dict):
        raise MarkerValidationError("Manifest must contain template_manifest mapping.")

    raw_modules = template_manifest.get("modules")
    if not isinstance(raw_modules, list):
        raise MarkerValidationError("template_manifest.modules must be a list.")
    module_names: set[str] = set()
    for module in raw_modules:
        if not isinstance(module, dict) or not isinstance(module.get("name"), str):
            raise MarkerValidationError("Every manifest module must define a string name.")
        module_names.add(module["name"])

    raw_path_mappings = template_manifest.get("path_mappings")
    if not isinstance(raw_path_mappings, list):
        raise MarkerValidationError("template_manifest.path_mappings must be a list.")

    mappings: list[ManifestMapping] = []
    for raw_mapping in raw_path_mappings:
        if not isinstance(raw_mapping, dict):
            raise MarkerValidationError("Every path mapping must be a mapping.")
        raw_pattern = raw_mapping.get("pattern")
        if not isinstance(raw_pattern, str):
            raise MarkerValidationError("Every path mapping must define a string pattern.")
        mapping = ManifestMapping(
            pattern=normalize_manifest_pattern(raw_pattern),
            requires_all=relation_modules(raw_mapping, "requires_all"),
            requires_any=relation_modules(raw_mapping, "requires_any"),
        )
        if not mapping.requires_all and not mapping.requires_any:
            raise MarkerValidationError(f"{mapping.pattern} must reference at least one module.")

        unknown_modules = (mapping.requires_all | mapping.requires_any) - module_names
        if unknown_modules:
            raise MarkerValidationError(
                f"{mapping.pattern} references unknown manifest module(s): "
                + ", ".join(sorted(unknown_modules))
            )
        mappings.append(mapping)

    return module_names, tuple(mappings)


def optional_marker_string(
    raw_record: dict[str, Any],
    field_name: str,
    record_name: str,
) -> str | None:
    """Return an optional string field from a marker record."""
    value = raw_record.get(field_name)
    if value is None:
        return None
    if not isinstance(value, str):
        raise MarkerValidationError(f"{record_name}.{field_name} must be a string when present.")
    return value


def parse_protected_file_decisions(
    template_sync: dict[str, Any],
) -> tuple[ProtectedFileDecision, ...]:
    """Extract normalized protected-file decision records from ``template_sync``."""
    protected_decisions: list[ProtectedFileDecision] = []
    for raw_decision in template_sync.get("protected_file_decisions", []):
        if not isinstance(raw_decision, dict):
            raise MarkerValidationError("Each protected file decision must be a mapping.")
        raw_path = raw_decision.get("path")
        decision = raw_decision.get("decision")
        if not isinstance(raw_path, str) or not isinstance(decision, str):
            raise MarkerValidationError(
                "Each protected file decision must define string path and decision."
            )
        normalized_path, is_directory = normalize_repository_path(
            raw_path,
            "template_sync.protected_file_decisions[].path",
        )
        if is_directory:
            raise MarkerValidationError(
                "template_sync.protected_file_decisions[].path must reference a file, "
                f"not a directory: {raw_path}"
            )
        protected_decisions.append(
            ProtectedFileDecision(
                path=normalized_path,
                decision=decision,
                adoption_mode=optional_marker_string(
                    raw_decision,
                    "adoption_mode",
                    "template_sync.protected_file_decisions[]",
                ),
                authorization_basis=optional_marker_string(
                    raw_decision,
                    "authorization_basis",
                    "template_sync.protected_file_decisions[]",
                ),
                authorized_scope=optional_marker_string(
                    raw_decision,
                    "authorized_scope",
                    "template_sync.protected_file_decisions[]",
                ),
                tailored_authorization_basis=optional_marker_string(
                    raw_decision,
                    "tailored_authorization_basis",
                    "template_sync.protected_file_decisions[]",
                ),
                reason=optional_marker_string(
                    raw_decision,
                    "reason",
                    "template_sync.protected_file_decisions[]",
                ),
            )
        )
    return tuple(protected_decisions)


def remove_local_authorization_tokens(
    repeated_tokens: list[str] | None,
    comma_separated_tokens: str | None,
) -> tuple[str, ...]:
    """Return normalized REMOVE-LOCAL strict-phrasing tokens."""
    raw_tokens: list[str] = []
    if comma_separated_tokens:
        raw_tokens.extend(comma_separated_tokens.split(","))
    if repeated_tokens:
        raw_tokens.extend(repeated_tokens)
    tokens = tuple(token.strip().lower() for token in raw_tokens if token.strip())
    return tokens or DEFAULT_REMOVE_LOCAL_AUTHORIZATION_TOKENS


def marker_path_overlaps(
    protected_decisions: tuple[ProtectedFileDecision, ...],
    local_overrides: tuple[LocalOverride, ...],
    deferred_candidates: tuple[DeferredProtectedCandidate, ...],
) -> tuple[MarkerPathOverlap, ...]:
    """Return marker records that overlap with protected-file decisions."""
    overlaps: list[MarkerPathOverlap] = []
    for protected_decision in protected_decisions:
        matching_local_overrides = tuple(
            local_override
            for local_override in local_overrides
            if local_override.matches(protected_decision.path)
        )
        matching_deferred_candidates = tuple(
            candidate
            for candidate in deferred_candidates
            if candidate.path == protected_decision.path
        )
        if matching_local_overrides or matching_deferred_candidates:
            overlaps.append(
                MarkerPathOverlap(
                    path=protected_decision.path,
                    protected_decision=protected_decision,
                    local_overrides=matching_local_overrides,
                    deferred_candidates=matching_deferred_candidates,
                )
            )
    return tuple(overlaps)


def protected_decision_summary(protected_decision: ProtectedFileDecision) -> str:
    """Return a compact protected-file decision summary."""
    parts = [f"decision={protected_decision.decision}"]
    if protected_decision.adoption_mode is not None:
        parts.append(f"adoption_mode={protected_decision.adoption_mode}")
    if protected_decision.authorization_basis is not None:
        parts.append(f"authorization_basis={protected_decision.authorization_basis}")
    if protected_decision.authorized_scope is not None:
        parts.append(f"authorized_scope={protected_decision.authorized_scope}")
    if protected_decision.tailored_authorization_basis is not None:
        parts.append(
            "tailored_authorization_basis=" f"{protected_decision.tailored_authorization_basis}"
        )
    if protected_decision.reason is not None:
        parts.append(f"reason={protected_decision.reason}")
    return "; ".join(parts)


def local_override_summary(local_override: LocalOverride) -> str:
    """Return a compact local override summary."""
    suffix = "/" if local_override.is_directory else ""
    return (
        f"path={local_override.path}{suffix}; "
        f"default_decision={local_override.default_decision}; "
        f"reason={local_override.reason}"
    )


def deferred_candidate_summary(candidate: DeferredProtectedCandidate) -> str:
    """Return a compact deferred protected candidate summary."""
    return f"source_commit={candidate.source_commit}; reason={candidate.reason}"


def format_overlap_block(overlap: MarkerPathOverlap) -> str:
    """Return a side-by-side marker overlap block for diagnostics."""
    lines = [
        f"  - {overlap.path}",
        f"    protected_file_decisions: {protected_decision_summary(overlap.protected_decision)}",
    ]
    for local_override in overlap.local_overrides:
        lines.append(f"    local_overrides: {local_override_summary(local_override)}")
    for candidate in overlap.deferred_candidates:
        lines.append(
            "    deferred_protected_candidates: " f"{deferred_candidate_summary(candidate)}"
        )
    return "\n".join(lines)


def validate_protected_file_decisions(
    protected_decisions: tuple[ProtectedFileDecision, ...],
    local_overrides: tuple[LocalOverride, ...],
    deferred_candidates: tuple[DeferredProtectedCandidate, ...],
    *,
    strict_remove_local_phrasing: bool = False,
    remove_local_tokens: tuple[str, ...] = DEFAULT_REMOVE_LOCAL_AUTHORIZATION_TOKENS,
) -> tuple[MarkerPathOverlap, ...]:
    """Validate protected-file decision integrity beyond JSON Schema checks."""
    seen_paths: set[str] = set()
    duplicate_paths: set[str] = set()
    for protected_decision in protected_decisions:
        if protected_decision.path in seen_paths:
            duplicate_paths.add(protected_decision.path)
        seen_paths.add(protected_decision.path)
    if duplicate_paths:
        raise MarkerValidationError(
            "Duplicate protected_file_decisions path(s): " + ", ".join(sorted(duplicate_paths))
        )

    overlaps = marker_path_overlaps(
        protected_decisions,
        local_overrides,
        deferred_candidates,
    )
    contradictions: list[str] = []
    for overlap in overlaps:
        mismatched_local_overrides = tuple(
            local_override
            for local_override in overlap.local_overrides
            if local_override.path == overlap.path
            and local_override.default_decision != overlap.protected_decision.decision
        )
        if mismatched_local_overrides:
            contradictions.append(
                format_overlap_block(
                    MarkerPathOverlap(
                        path=overlap.path,
                        protected_decision=overlap.protected_decision,
                        local_overrides=mismatched_local_overrides,
                        deferred_candidates=(),
                    )
                )
                + "\n    conflict: protected decision and local override decisions differ."
            )
        if overlap.deferred_candidates:
            contradictions.append(
                format_overlap_block(
                    MarkerPathOverlap(
                        path=overlap.path,
                        protected_decision=overlap.protected_decision,
                        local_overrides=(),
                        deferred_candidates=overlap.deferred_candidates,
                    )
                )
                + "\n    conflict: protected decision asserts current authorization while "
                "the deferred candidate is awaiting authorization."
            )
    if contradictions:
        raise MarkerValidationError(
            "Contradictory protected-file marker entries:\n" + "\n".join(contradictions)
        )

    if strict_remove_local_phrasing:
        normalized_tokens = tuple(token.lower() for token in remove_local_tokens if token)
        for protected_decision in protected_decisions:
            if protected_decision.decision != REMOVAL_DECISION:
                continue
            authorization_basis = protected_decision.authorization_basis or ""
            if not any(token in authorization_basis.lower() for token in normalized_tokens):
                raise MarkerValidationError(
                    f"{protected_decision.path} REMOVE-LOCAL authorization_basis must "
                    "contain at least one configured removal token: " + ", ".join(normalized_tokens)
                )

    return overlaps


def parse_marker(
    marker: dict[str, Any],
) -> tuple[
    set[str],
    tuple[LocalOverride, ...],
    tuple[DeferredProtectedCandidate, ...],
    tuple[ProtectedFileDecision, ...],
]:
    """Extract included modules, local overrides, deferred candidates, and decisions."""
    template_sync = marker.get("template_sync")
    if not isinstance(template_sync, dict):
        raise MarkerValidationError("Marker must contain template_sync mapping.")

    raw_included_modules = template_sync.get("included_modules")
    if not isinstance(raw_included_modules, list) or not all(
        isinstance(module, str) for module in raw_included_modules
    ):
        raise MarkerValidationError("template_sync.included_modules must be a list of strings.")
    included_modules = set(raw_included_modules)

    local_overrides: list[LocalOverride] = []
    for raw_override in template_sync.get("local_overrides", []):
        if not isinstance(raw_override, dict):
            raise MarkerValidationError("Each local override must be a mapping.")
        raw_path = raw_override.get("path")
        default_decision = raw_override.get("default_decision")
        reason = raw_override.get("reason")
        if (
            not isinstance(raw_path, str)
            or not isinstance(default_decision, str)
            or not isinstance(reason, str)
        ):
            raise MarkerValidationError(
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
            raise MarkerValidationError("Each deferred protected candidate must be a mapping.")
        raw_path = raw_candidate.get("path")
        source_commit = raw_candidate.get("source_commit")
        reason = raw_candidate.get("reason")
        if (
            not isinstance(raw_path, str)
            or not isinstance(source_commit, str)
            or not isinstance(reason, str)
        ):
            raise MarkerValidationError(
                "Each deferred protected candidate must define string path, source_commit, and reason."
            )
        normalized_path, is_directory = normalize_repository_path(
            raw_path,
            "template_sync.deferred_protected_candidates[].path",
        )
        if is_directory:
            raise MarkerValidationError(
                "template_sync.deferred_protected_candidates[].path must reference a file, "
                f"not a directory: {raw_path}"
            )
        deferred_candidates.append(
            DeferredProtectedCandidate(
                path=normalized_path,
                source_commit=source_commit,
                reason=reason,
            )
        )

    protected_decisions = parse_protected_file_decisions(template_sync)

    return (
        included_modules,
        tuple(local_overrides),
        tuple(deferred_candidates),
        protected_decisions,
    )


def pattern_specificity(pattern: str) -> tuple[int, int, int]:
    """Return a sortable specificity rank for a manifest path pattern."""
    is_exact = not any(wildcard in pattern for wildcard in "*?[")
    literal_length = sum(1 for character in pattern if character not in "*?[]")
    return (int(is_exact), literal_length, pattern.count("/"))


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
    requires_all: set[str] = set()
    requires_any: set[str] = set()
    patterns: list[str] = []
    for mapping in selected:
        requires_all.update(mapping.requires_all)
        requires_any.update(mapping.requires_any)
        patterns.append(mapping.pattern)
    return PathRelation(
        patterns=tuple(patterns),
        requires_all=frozenset(requires_all),
        requires_any=frozenset(requires_any),
    )


def is_locally_overridden(relative_path: str, local_overrides: tuple[LocalOverride, ...]) -> bool:
    """Return whether any marker local override covers ``relative_path``."""
    return any(local_override.matches(relative_path) for local_override in local_overrides)


def git_visible_paths(repo_root: Path) -> tuple[str, ...]:
    """Return tracked and untracked non-ignored file paths according to Git."""
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=repo_root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "git ls-files failed"
        raise MarkerValidationError(f"Unable to inspect Git-visible files: {message}")
    return tuple(sorted({path for path in result.stdout.splitlines() if path}))


def git_present_paths(repo_root: Path) -> tuple[str, ...]:
    """Return Git-visible paths that are present in the working tree."""
    present_paths: list[str] = []
    for relative_path in git_visible_paths(repo_root):
        path = repo_root / relative_path
        if path.exists() or path.is_symlink():
            present_paths.append(relative_path)
    return tuple(present_paths)


def unresolved_concrete_manifest_patterns(
    mappings: tuple[ManifestMapping, ...],
    present_paths: Iterable[str],
    allowlist_paths: Collection[str] = (),
    included_modules: set[str] | None = None,
    local_overrides: tuple[LocalOverride, ...] = (),
) -> tuple[tuple[str, PathRelation], ...]:
    """Return concrete manifest mappings missing from the supplied present paths."""
    present_path_set = set(present_paths)
    missing_patterns: list[tuple[str, PathRelation]] = []

    for pattern in sorted({mapping.pattern for mapping in mappings if mapping.is_concrete}):
        if pattern in allowlist_paths or is_locally_overridden(pattern, local_overrides):
            continue

        relation = selected_relation_for_path(pattern, mappings)
        if relation is None:
            continue
        if included_modules is not None and not relation.is_retained_by(included_modules):
            continue
        if pattern not in present_path_set:
            missing_patterns.append((pattern, relation))

    return tuple(missing_patterns)


def iter_safe_repository_files(repo_root: Path) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return safely discovered regular files and skipped symlink paths."""
    discovered: list[str] = []
    skipped_symlinks: list[str] = []
    root = repo_root.resolve()

    for current_root, dir_names, file_names in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current_root)
        retained_dir_names: list[str] = []
        for dir_name in dir_names:
            candidate = current_path / dir_name
            if dir_name in SKIPPED_DISCOVERY_DIRS:
                continue
            if candidate.is_symlink():
                skipped_symlinks.append(f"{repository_relative_path(candidate, root)}/")
                continue
            retained_dir_names.append(dir_name)
        dir_names[:] = retained_dir_names

        for file_name in file_names:
            file_path = current_path / file_name
            relative_path = repository_relative_path(file_path, root)
            if file_path.is_symlink():
                skipped_symlinks.append(relative_path)
                continue
            try:
                file_path.resolve().relative_to(root)
            except (OSError, ValueError):
                skipped_symlinks.append(relative_path)
                continue
            discovered.append(relative_path)

    return tuple(sorted(discovered)), tuple(sorted(skipped_symlinks))


def validate_marker_state(
    repo_root: Path,
    marker_path: Path,
    manifest_path: Path,
    marker_schema_path: Path,
    manifest_schema_path: Path,
    *,
    strict_remove_local_phrasing: bool = False,
    remove_local_tokens: tuple[str, ...] = DEFAULT_REMOVE_LOCAL_AUTHORIZATION_TOKENS,
) -> MarkerValidationReport:
    """Validate marker decisions against manifest mappings and on-disk files."""
    marker = load_yaml_mapping(marker_path, repo_root)
    manifest = load_yaml_mapping(manifest_path, repo_root)
    marker_schema = load_json_mapping(marker_schema_path, repo_root)
    manifest_schema = load_json_mapping(manifest_schema_path, repo_root)

    validate_schema(marker, marker_schema, marker_path, repo_root)
    validate_schema(manifest, manifest_schema, manifest_path, repo_root)

    manifest_modules, mappings = parse_manifest_mappings(manifest)
    included_modules, local_overrides, deferred_candidates, protected_decisions = parse_marker(
        marker
    )
    overlaps = validate_protected_file_decisions(
        protected_decisions,
        local_overrides,
        deferred_candidates,
        strict_remove_local_phrasing=strict_remove_local_phrasing,
        remove_local_tokens=remove_local_tokens,
    )
    unknown_included_modules = included_modules - manifest_modules
    if unknown_included_modules:
        raise MarkerValidationError(
            "Marker includes module(s) that are not defined by the manifest: "
            + ", ".join(sorted(unknown_included_modules))
        )

    present_paths = set(git_present_paths(repo_root))
    repository_files, skipped_symlinks = iter_safe_repository_files(repo_root)
    unsafe_managed_paths: list[str] = []
    for relative_path in skipped_symlinks:
        normalized_relative_path = relative_path.rstrip("/")
        if normalized_relative_path not in present_paths:
            continue
        if is_locally_overridden(normalized_relative_path, local_overrides):
            continue
        relation = selected_relation_for_path(normalized_relative_path, mappings)
        if relation is not None:
            unsafe_managed_paths.append(normalized_relative_path)

    leftover_files: list[tuple[str, PathRelation]] = []
    for relative_path in repository_files:
        if relative_path not in present_paths:
            continue
        if is_locally_overridden(relative_path, local_overrides):
            continue
        relation = selected_relation_for_path(relative_path, mappings)
        if relation is None:
            continue
        if not relation.is_retained_by(included_modules):
            leftover_files.append((relative_path, relation))

    missing_expected_files = unresolved_concrete_manifest_patterns(
        mappings=mappings,
        present_paths=present_paths,
        included_modules=included_modules,
        local_overrides=local_overrides,
    )

    return MarkerValidationReport(
        included_modules=tuple(sorted(included_modules)),
        manifest_mapping_count=len(mappings),
        unsafe_managed_paths=tuple(sorted(unsafe_managed_paths)),
        missing_expected_files=tuple(missing_expected_files),
        leftover_files=tuple(leftover_files),
        local_overrides=local_overrides,
        deferred_candidates=deferred_candidates,
        protected_decisions=protected_decisions,
        marker_path_overlaps=overlaps,
    )


def print_report(report: MarkerValidationReport) -> None:
    """Print a human-readable validation report."""
    if report.has_failures:
        print("Marker-aware template sync validation failed.")
    else:
        print("Marker-aware template sync validation passed.")
    print(f"Included modules: {', '.join(report.included_modules)}")
    print(f"Manifest mappings checked: {report.manifest_mapping_count}")

    if report.unsafe_managed_paths:
        print("\nTemplate-managed paths that are symlinks or resolve unsafely:")
        for relative_path in report.unsafe_managed_paths:
            print(f"  - {relative_path}")

    if report.leftover_files:
        print("\nFiles present on disk but not retained by included modules:")
        for relative_path, relation in report.leftover_files:
            print(f"  - {relative_path} ({relation.description})")

    if report.missing_expected_files:
        print("\nConcrete mapped files expected for included modules but missing:")
        for relative_path, relation in report.missing_expected_files:
            print(f"  - {relative_path} ({relation.description})")

    if report.local_overrides:
        print("\nLocal overrides skipped:")
        for local_override in report.local_overrides:
            suffix = "/" if local_override.is_directory else ""
            print(
                f"  - {local_override.path}{suffix} "
                f"({local_override.default_decision}): {local_override.reason}"
            )

    if report.deferred_candidates:
        print("\nDeferred protected candidates:")
        for candidate in report.deferred_candidates:
            print(f"  - {candidate.path} at {candidate.source_commit}: {candidate.reason}")

    if report.protected_decisions:
        print("\nProtected file decisions:")
        for protected_decision in report.protected_decisions:
            print(f"  - {protected_decision.path}: {protected_decision.decision}")
            if protected_decision.adoption_mode is not None:
                print(f"    adoption_mode: {protected_decision.adoption_mode}")
            if protected_decision.authorization_basis is not None:
                print(f"    authorization_basis: {protected_decision.authorization_basis}")
            if protected_decision.authorized_scope is not None:
                print(f"    authorized_scope: {protected_decision.authorized_scope}")
            if protected_decision.tailored_authorization_basis is not None:
                print(
                    "    tailored_authorization_basis: "
                    f"{protected_decision.tailored_authorization_basis}"
                )
            if protected_decision.reason is not None:
                print(f"    reason: {protected_decision.reason}")

    remove_local_decisions = tuple(
        protected_decision
        for protected_decision in report.protected_decisions
        if protected_decision.decision == REMOVAL_DECISION
    )
    if remove_local_decisions:
        print("\nREMOVE-LOCAL authorizations:")
        for protected_decision in remove_local_decisions:
            print(f"  - {protected_decision.path}")
            print(f"    authorization_basis: {protected_decision.authorization_basis}")
            print(f"    authorized_scope: {protected_decision.authorized_scope}")
            print(f"    reason: {protected_decision.reason}")

    if report.marker_path_overlaps:
        print("\nProtected decision overlaps:")
        for overlap in report.marker_path_overlaps:
            print(format_overlap_block(overlap))

    if not report.has_failures:
        print("\nNo retained-template inconsistencies found.")


def fail(message: str) -> NoReturn:
    """Print an error and exit non-zero."""
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def main(argv: list[str] | None = None) -> int:
    """Run marker-aware downstream sync validation."""
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        repo_root = resolve_repo_root(args.repo_root)
        marker_path = resolve_repo_path(repo_root, args.marker)
        manifest_path = resolve_repo_path(repo_root, args.manifest)
        marker_schema_path = resolve_repo_path(repo_root, args.marker_schema)
        manifest_schema_path = resolve_repo_path(repo_root, args.manifest_schema)

        if not marker_path.exists():
            marker_relative_path = repository_relative_path(marker_path, repo_root)
            if args.require_marker:
                raise MarkerValidationError(
                    f"Marker is required but was not found at {marker_relative_path}."
                )
            print(f"No marker found at {marker_relative_path}; nothing to validate.")
            return 0

        report = validate_marker_state(
            repo_root=repo_root,
            marker_path=marker_path,
            manifest_path=manifest_path,
            marker_schema_path=marker_schema_path,
            manifest_schema_path=manifest_schema_path,
            strict_remove_local_phrasing=args.strict_remove_local_phrasing,
            remove_local_tokens=remove_local_authorization_tokens(
                args.remove_local_authorization_token,
                args.remove_local_authorization_tokens,
            ),
        )
    except MarkerValidationError as error:
        fail(str(error))

    print_report(report)
    return 1 if report.has_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
