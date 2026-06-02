"""Validate a downstream template sync marker against the on-disk file set."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from template_sync_materialization_helpers import (  # noqa: E402
    DEFAULT_MANIFEST_PATH,
    DEFAULT_MANIFEST_SCHEMA_PATH,
    DEFAULT_MARKER_PATH,
    DEFAULT_MARKER_SCHEMA_PATH,
    DEFAULT_REMOVE_LOCAL_AUTHORIZATION_TOKENS,
    REMOVAL_DECISION,
    DeferredProtectedCandidate,
    LocalOverride,
    MarkerPathOverlap,
    PathRelation,
    ProtectedFileDecision,
    TemplateSyncMaterializationError as MarkerValidationError,
    format_overlap_block,
    git_present_paths,
    iter_safe_repository_files,
    is_locally_overridden,
    load_json_mapping,
    load_yaml_mapping,
    normalize_repository_path as normalize_repository_path,
    parse_manifest_mappings,
    parse_marker_decision_data,
    repository_relative_path,
    resolve_repo_path,
    resolve_repo_root,
    selected_relation_for_path,
    unresolved_concrete_manifest_patterns,
    validate_protected_file_decisions,
    validate_schema,
)


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


def parse_marker(
    marker: dict[str, object],
) -> tuple[
    set[str],
    tuple[LocalOverride, ...],
    tuple[DeferredProtectedCandidate, ...],
    tuple[ProtectedFileDecision, ...],
]:
    """Extract included modules, local overrides, deferred candidates, and decisions."""
    marker_data = parse_marker_decision_data(marker)

    return (
        set(marker_data.included_modules),
        marker_data.local_overrides,
        marker_data.deferred_candidates,
        marker_data.protected_decisions,
    )


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
