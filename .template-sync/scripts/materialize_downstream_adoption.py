"""Materialize a selected template module set into a downstream work tree."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Collection, Iterable, Sequence

import yaml  # type: ignore[import-untyped]

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
    InlineBlockMarker,
    LocalOverride,
    ManifestMapping,
    MarkerDecisionData,
    ProtectedFileDecision,
    TemplateSyncMaterializationError,
    classify_repository_file,
    is_protected_instruction_path,
    iter_safe_repository_files,
    load_json_mapping,
    load_yaml_mapping,
    os_error_summary,
    parse_inline_block_marker,
    parse_manifest_mappings,
    parse_marker_decision_data,
    remove_inline_blocks_for_modules,
    resolve_safe_repository_target_path,
    selected_relation_for_path,
    validate_protected_file_decisions,
    validate_schema,
)

EXIT_SUCCESS = 0
EXIT_RUNTIME_FAILURE = 1
EXIT_DECISIONS_REQUIRED = 2
PLACEHOLDER_HELPER_PATH = ".github/scripts/replace-template-placeholders.py"
ADOPTION_MODES = ("minimal-preservation", "tailored")
TEMPLATE_TAKE_DECISION = "TAKE"
TEMPLATE_SKIP_DECISION = "SKIP"
PLACEHOLDER_DESTS = (
    "repository",
    "github_host",
    "codeowners_owner",
    "conduct_contact",
    "security_contact",
    "vscode_title",
)
MARKER_COPY_FIELDS = (
    "local_overrides",
    "protected_file_decisions",
    "deferred_protected_candidates",
    "instruction_contract_waivers",
)


class MaterializationError(RuntimeError):
    """Raised when first-adoption materialization cannot proceed safely."""


@dataclass(frozen=True)
class Decisions:
    """Resolved scalar and marker-shaped adoption decisions."""

    source_repo: str
    last_reviewed_template_commit: str | None
    included_modules: frozenset[str]
    marker_data: MarkerDecisionData
    raw_marker_fields: dict[str, Any]


@dataclass(frozen=True)
class Conflict:
    """One target path that was not overwritten by materialization."""

    path: str
    classification: str
    resolution: str
    recorded: bool


@dataclass
class Summary:
    """Deterministic operation summary emitted after reconciliation."""

    retained_modules: list[str]
    excluded_modules: list[str]
    default_adoption_mode: str
    created: set[str] = field(default_factory=set)
    updated: set[str] = field(default_factory=set)
    unchanged: set[str] = field(default_factory=set)
    skipped: set[str] = field(default_factory=set)
    protected: set[str] = field(default_factory=set)
    locally_overridden: set[str] = field(default_factory=set)
    deferred: set[str] = field(default_factory=set)
    recorded_removals: set[str] = field(default_factory=set)
    unmapped: set[str] = field(default_factory=set)
    excluded_paths: set[str] = field(default_factory=set)
    byte_only: set[str] = field(default_factory=set)
    placeholder_related: set[str] = field(default_factory=set)
    placeholder_notes: list[str] = field(default_factory=list)
    conflicts: list[Conflict] = field(default_factory=list)
    marker_status: str = "preview-only"
    marker_reason: str = ""
    computed_marker_preview: str | None = None

    @property
    def unrecorded_conflicts(self) -> tuple[Conflict, ...]:
        """Return conflicts that still require a concrete path-scoped decision."""
        return tuple(conflict for conflict in self.conflicts if not conflict.recorded)

    @property
    def recorded_conflicts(self) -> tuple[Conflict, ...]:
        """Return conflicts already recorded as unresolved decisions."""
        return tuple(conflict for conflict in self.conflicts if conflict.recorded)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Materialize selected copilot-repo-template modules into a downstream "
            "working tree without overwriting unrecorded conflicts."
        )
    )
    parser.add_argument(
        "--template-root",
        default=None,
        help="Template repository root. Defaults to the repository containing this script.",
    )
    parser.add_argument(
        "--target-root",
        required=True,
        help="Downstream repository root that receives the staged materialization.",
    )
    parser.add_argument(
        "--decisions-file",
        default=None,
        help=(
            "Repository-relative marker-shaped decisions file. When supplied, "
            "overlapping CLI source, commit, and module values must match it."
        ),
    )
    parser.add_argument(
        "--included-module",
        "--module",
        dest="included_modules",
        action="append",
        default=[],
        metavar="MODULE",
        help="Retained module name. May be repeated.",
    )
    parser.add_argument(
        "--included-modules",
        dest="included_modules_csv",
        default=None,
        metavar="MODULES",
        help="Comma-separated retained module names.",
    )
    parser.add_argument(
        "--source-repo",
        default=None,
        help="Canonical upstream template repository URL.",
    )
    parser.add_argument(
        "--last-reviewed-template-commit",
        default=None,
        help="Full lowercase reviewed upstream template commit SHA.",
    )
    parser.add_argument(
        "--default-adoption-mode",
        choices=ADOPTION_MODES,
        default="minimal-preservation",
        help=(
            "Default behavior posture used for reporting. This is not written as "
            "a marker-level default field."
        ),
    )
    parser.add_argument(
        "--repository",
        default=None,
        help="Replacement OWNER/REPO value for the existing placeholder helper.",
    )
    parser.add_argument(
        "--github-host",
        default=None,
        help="GitHub or GHES host for approved placeholder URL contexts.",
    )
    parser.add_argument(
        "--codeowners-owner",
        default=None,
        help="Replacement CODEOWNERS owner, e.g. @octocat or @org/team.",
    )
    parser.add_argument(
        "--conduct-contact",
        default=None,
        help="Replacement Code of Conduct contact method.",
    )
    parser.add_argument(
        "--security-contact",
        default=None,
        help="Replacement security contact email or intake address.",
    )
    parser.add_argument(
        "--vscode-title",
        default=None,
        help="Replacement VS Code window title.",
    )
    parser.add_argument(
        "--allow-conflicts",
        action="store_true",
        help=(
            "Exit zero while still skipping conflicted paths and leaving marker "
            "advancement governed by unrecorded conflicts."
        ),
    )
    return parser.parse_args(argv)


def default_template_root() -> Path:
    """Return the template root implied by this script's committed location."""
    return Path(__file__).resolve().parents[2]


def resolve_existing_root(raw_root: str | None, *, default: Path | None, name: str) -> Path:
    """Resolve and validate a directory root supplied by the operator."""
    root = Path(raw_root).expanduser() if raw_root is not None else default
    if root is None:
        raise MaterializationError(f"{name} is required.")
    resolved = root.resolve()
    if not resolved.is_dir():
        raise MaterializationError(f"{name} does not exist or is not a directory.")
    return resolved


def resolve_target_decisions_file(target_root: Path, raw_path: str) -> Path:
    """Resolve a repository-relative decisions file inside the target root."""
    return resolve_safe_repository_target_path(
        target_root,
        raw_path,
        field_name="--decisions-file",
    )


def load_validated_manifest_context(
    template_root: Path,
) -> tuple[dict[str, Any], tuple[str, ...], tuple[ManifestMapping, ...]]:
    """Load, schema-validate, and parse the template manifest."""
    manifest_path = resolve_safe_repository_target_path(
        template_root,
        DEFAULT_MANIFEST_PATH,
        field_name="manifest path",
    )
    manifest_schema_path = resolve_safe_repository_target_path(
        template_root,
        DEFAULT_MANIFEST_SCHEMA_PATH,
        field_name="manifest schema path",
    )
    manifest = load_yaml_mapping(manifest_path, template_root)
    manifest_schema = load_json_mapping(manifest_schema_path, template_root)
    validate_schema(manifest, manifest_schema, manifest_path, template_root)
    module_names, mappings = parse_manifest_mappings(manifest)
    template_manifest = manifest.get("template_manifest")
    if not isinstance(template_manifest, dict):
        raise MaterializationError("Manifest must contain template_manifest mapping.")
    raw_modules = template_manifest.get("modules")
    if not isinstance(raw_modules, list):
        raise MaterializationError("Manifest module definitions must be a list.")
    module_order = tuple(
        module["name"]
        for module in raw_modules
        if isinstance(module, dict) and isinstance(module.get("name"), str)
    )
    if set(module_order) != set(module_names):
        raise MaterializationError("Manifest module order does not match parsed modules.")
    return manifest, module_order, mappings


def split_cli_modules(args: argparse.Namespace) -> frozenset[str] | None:
    """Return CLI-supplied modules, or ``None`` when no module flag was supplied."""
    raw_modules: list[str] = []
    raw_modules.extend(args.included_modules)
    if args.included_modules_csv:
        raw_modules.extend(
            module.strip() for module in args.included_modules_csv.split(",") if module.strip()
        )
    if not raw_modules:
        return None
    return frozenset(raw_modules)


def scalar_from_marker(
    marker_template_sync: dict[str, Any],
    field_name: str,
) -> str | None:
    """Return an optional string scalar from marker-shaped decision data."""
    value = marker_template_sync.get(field_name)
    if value is None:
        return None
    if not isinstance(value, str):
        raise MaterializationError(f"template_sync.{field_name} must be a string.")
    return value


def validate_cli_marker_overlap(
    *,
    cli_value: str | None,
    marker_value: str | None,
    name: str,
) -> str | None:
    """Return the resolved scalar after checking CLI and decisions-file agreement."""
    if cli_value is not None and marker_value is not None and cli_value != marker_value:
        raise MaterializationError(
            f"Conflicting {name}: CLI value does not match --decisions-file."
        )
    return marker_value if marker_value is not None else cli_value


def validate_module_overlap(
    *,
    cli_modules: frozenset[str] | None,
    marker_modules: frozenset[str] | None,
) -> frozenset[str] | None:
    """Return modules after checking CLI and decisions-file agreement."""
    if cli_modules is not None and marker_modules is not None and cli_modules != marker_modules:
        raise MaterializationError(
            "Conflicting included modules: CLI values do not match --decisions-file."
        )
    return marker_modules if marker_modules is not None else cli_modules


def load_decisions(
    args: argparse.Namespace,
    *,
    template_root: Path,
    target_root: Path,
    module_order: Sequence[str],
) -> Decisions:
    """Resolve CLI and marker-shaped decision data into one deterministic object."""
    marker_document: dict[str, Any] | None = None
    marker_data: MarkerDecisionData | None = None
    marker_template_sync: dict[str, Any] = {}
    if args.decisions_file is not None:
        decisions_path = resolve_target_decisions_file(target_root, args.decisions_file)
        marker_schema_path = resolve_safe_repository_target_path(
            template_root,
            DEFAULT_MARKER_SCHEMA_PATH,
            field_name="marker schema path",
        )
        marker_document = load_yaml_mapping(decisions_path, target_root)
        marker_schema = load_json_mapping(marker_schema_path, template_root)
        validate_schema(marker_document, marker_schema, decisions_path, target_root)
        parsed = parse_marker_decision_data(
            marker_document,
            validate_protected_decision_integrity=True,
        )
        marker_data = parsed
        raw_template_sync = marker_document.get("template_sync")
        if not isinstance(raw_template_sync, dict):
            raise MaterializationError("--decisions-file must contain template_sync mapping.")
        marker_template_sync = raw_template_sync

    cli_modules = split_cli_modules(args)
    marker_modules = marker_data.included_modules if marker_data is not None else None
    included_modules = validate_module_overlap(
        cli_modules=cli_modules,
        marker_modules=marker_modules,
    )
    if included_modules is None:
        raise MaterializationError(
            "At least one included module is required through CLI flags or --decisions-file."
        )

    source_repo = validate_cli_marker_overlap(
        cli_value=args.source_repo,
        marker_value=scalar_from_marker(marker_template_sync, "source_repo"),
        name="source repo",
    )
    if source_repo is None:
        raise MaterializationError("--source-repo is required unless --decisions-file supplies it.")

    reviewed_commit = validate_cli_marker_overlap(
        cli_value=args.last_reviewed_template_commit,
        marker_value=scalar_from_marker(
            marker_template_sync,
            "last_reviewed_template_commit",
        ),
        name="last reviewed template commit",
    )
    module_set = set(included_modules)
    unknown_modules = module_set - set(module_order)
    if unknown_modules:
        raise MaterializationError(
            "Selected module(s) are not defined by the manifest: "
            + ", ".join(sorted(unknown_modules))
        )

    raw_marker_fields: dict[str, Any] = {}
    if marker_document is not None:
        for field_name in MARKER_COPY_FIELDS:
            if field_name in marker_template_sync:
                raw_marker_fields[field_name] = marker_template_sync[field_name]

    resolved_marker_data = marker_data or MarkerDecisionData(
        last_reviewed_template_commit=reviewed_commit,
        included_modules=frozenset(included_modules),
        local_overrides=(),
        deferred_candidates=(),
        protected_decisions=(),
    )
    validate_protected_file_decisions(
        resolved_marker_data.protected_decisions,
        resolved_marker_data.local_overrides,
        resolved_marker_data.deferred_candidates,
    )

    return Decisions(
        source_repo=source_repo,
        last_reviewed_template_commit=reviewed_commit,
        included_modules=frozenset(included_modules),
        marker_data=resolved_marker_data,
        raw_marker_fields=raw_marker_fields,
    )


def ordered_modules(module_order: Sequence[str], selected_modules: Collection[str]) -> list[str]:
    """Return selected modules in manifest display order."""
    selected = set(selected_modules)
    return [module for module in module_order if module in selected]


def computed_marker_document(
    *,
    decisions: Decisions,
    module_order: Sequence[str],
) -> dict[str, Any]:
    """Build the schema-valid marker document computed for this run."""
    template_sync: dict[str, Any] = {
        "source_repo": decisions.source_repo,
    }
    if decisions.last_reviewed_template_commit is not None:
        template_sync["last_reviewed_template_commit"] = decisions.last_reviewed_template_commit
    template_sync["included_modules"] = ordered_modules(
        module_order,
        decisions.included_modules,
    )
    for field_name in MARKER_COPY_FIELDS:
        if field_name in decisions.raw_marker_fields:
            template_sync[field_name] = decisions.raw_marker_fields[field_name]
    return {"template_sync": template_sync}


def marker_yaml(marker_document: dict[str, Any]) -> str:
    """Return deterministic marker YAML."""
    return yaml.safe_dump(marker_document, sort_keys=False, allow_unicode=False)


def validate_computed_marker(
    marker_document: dict[str, Any],
    *,
    template_root: Path,
) -> None:
    """Validate the computed marker document against the checked-in schema."""
    schema_path = resolve_safe_repository_target_path(
        template_root,
        DEFAULT_MARKER_SCHEMA_PATH,
        field_name="marker schema path",
    )
    schema = load_json_mapping(schema_path, template_root)
    marker_path = resolve_safe_repository_target_path(
        template_root,
        DEFAULT_MARKER_PATH,
        field_name="marker path",
    )
    validate_schema(marker_document, schema, marker_path, template_root)
    parse_marker_decision_data(marker_document, validate_protected_decision_integrity=True)


def validate_inline_markers(text: str, *, relative_path: str) -> None:
    """Validate inline template-sync marker pairing before module pruning."""
    stack: list[InlineBlockMarker] = []
    for line_number, line in enumerate(text.splitlines(keepends=True), 1):
        marker = parse_inline_block_marker(
            line,
            line_number=line_number,
            relative_path=relative_path,
        )
        if marker is None:
            continue
        if marker.kind == "begin":
            if stack:
                open_marker = stack[-1]
                raise MaterializationError(
                    f"{relative_path}:{line_number}: Nested template-sync inline marker "
                    f"inside {open_marker.name}."
                )
            stack.append(marker)
            continue
        if not stack:
            raise MaterializationError(
                f"{relative_path}:{line_number}: Unmatched template-sync inline marker end."
            )
        begin_marker = stack.pop()
        if begin_marker.name != marker.name:
            raise MaterializationError(
                f"{relative_path}:{line_number}: End marker {marker.name!r} does not "
                f"match begin marker {begin_marker.name!r} from line "
                f"{begin_marker.line_number}."
            )
    if stack:
        marker = stack[-1]
        raise MaterializationError(
            f"{relative_path}:{marker.line_number}: Unclosed template-sync inline marker: "
            f"{marker.name}."
        )


def write_staged_candidate(
    *,
    template_root: Path,
    staging_root: Path,
    mappings: tuple[ManifestMapping, ...],
    included_modules: Collection[str],
    summary: Summary,
) -> tuple[str, ...]:
    """Populate the staging tree with retained, transformed template-managed files."""
    template_paths, skipped_symlinks = iter_safe_repository_files(template_root)
    if skipped_symlinks:
        managed_symlinks = [
            path.rstrip("/")
            for path in skipped_symlinks
            if selected_relation_for_path(path.rstrip("/"), mappings) is not None
        ]
        if managed_symlinks:
            raise MaterializationError(
                "Template-managed symlink path(s) cannot be materialized: "
                + ", ".join(sorted(managed_symlinks))
            )

    staged_paths: list[str] = []
    for relative_path in template_paths:
        relation = selected_relation_for_path(relative_path, mappings)
        if relation is None:
            summary.unmapped.add(relative_path)
            continue
        if not relation.is_retained_by(included_modules):
            summary.excluded_paths.add(relative_path)
            continue

        classification = classify_repository_file(template_root, relative_path)
        destination = resolve_safe_repository_target_path(
            staging_root,
            relative_path,
            field_name="staged path",
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        if classification.is_byte_only:
            destination.write_bytes(classification.bytes_content)
            summary.byte_only.add(relative_path)
        else:
            assert classification.text is not None
            validate_inline_markers(classification.text, relative_path=relative_path)
            filtered_text = remove_inline_blocks_for_modules(
                classification.text,
                included_modules,
                relative_path=relative_path,
            )
            destination.write_bytes(filtered_text.encode("utf-8"))
        staged_paths.append(relative_path)
    return tuple(sorted(staged_paths))


def placeholder_requested(args: argparse.Namespace) -> bool:
    """Return whether any placeholder replacement input was supplied."""
    return any(getattr(args, destination) is not None for destination in PLACEHOLDER_DESTS)


HELPER_FAILURE_OUTPUT_LINE_LIMIT = 20


def summarize_helper_failure(
    *,
    returncode: int,
    stdout: str,
    stderr: str,
    line_limit: int = HELPER_FAILURE_OUTPUT_LINE_LIMIT,
) -> str:
    """Return a bounded, path-safe placeholder-helper failure summary.

    The helper reports findings and ``PlaceholderError`` messages using
    repository-relative paths and only operates on the temporary staging tree,
    so a bounded tail of its captured ``stdout``/``stderr`` is safe to surface
    and lets the operator diagnose the failure without rerunning. Each stream is
    truncated to its most recent ``line_limit`` lines to keep the message
    minimal.
    """
    message_parts = [f"Placeholder helper failed with exit code {returncode}."]
    for label, stream in (("stdout", stdout), ("stderr", stderr)):
        lines = stream.splitlines()
        if not lines:
            continue
        shown = lines[-line_limit:]
        if len(lines) > len(shown):
            message_parts.append(
                f"Helper {label} (showing last {len(shown)} of {len(lines)} lines):"
            )
        else:
            message_parts.append(f"Helper {label}:")
        message_parts.extend(shown)
    return "\n".join(message_parts)


def run_placeholder_helper(
    *,
    args: argparse.Namespace,
    template_root: Path,
    staging_root: Path,
    summary: Summary,
) -> None:
    """Run the existing approved placeholder helper against the staging tree."""
    if not placeholder_requested(args):
        summary.placeholder_notes.append("skipped: no placeholder inputs supplied")
        return
    helper_path = resolve_safe_repository_target_path(
        template_root,
        PLACEHOLDER_HELPER_PATH,
        field_name="placeholder helper path",
    )
    if not helper_path.is_file():
        raise MaterializationError(
            "Placeholder inputs were supplied, but the template-root placeholder "
            f"helper is unavailable at {PLACEHOLDER_HELPER_PATH}."
        )
    if args.repository is None or args.security_contact is None:
        raise MaterializationError(
            "Placeholder replacement requires --repository and --security-contact."
        )

    command = [
        sys.executable,
        str(helper_path),
        "replace",
        "--repo-root",
        str(staging_root),
        "--repository",
        args.repository,
        "--security-contact",
        args.security_contact,
    ]
    optional_pairs = (
        ("--github-host", args.github_host),
        ("--codeowners-owner", args.codeowners_owner),
        ("--conduct-contact", args.conduct_contact),
        ("--vscode-title", args.vscode_title),
    )
    for flag, value in optional_pairs:
        if value is not None:
            command.extend([flag, value])

    with tempfile.TemporaryDirectory(prefix="template-adoption-byte-only-") as byte_directory:
        byte_root = Path(byte_directory)
        moved_byte_only_paths: list[tuple[Path, Path]] = []
        for relative_path in sorted(summary.byte_only):
            source = staging_root / relative_path
            if not source.exists():
                continue
            destination = byte_root / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(destination))
            moved_byte_only_paths.append((source, destination))

        try:
            result = subprocess.run(
                command,
                cwd=template_root,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except OSError as error:
            raise MaterializationError(
                f"Unable to run placeholder helper: {os_error_summary(error)}"
            ) from error
        finally:
            for source, destination in moved_byte_only_paths:
                source.parent.mkdir(parents=True, exist_ok=True)
                if destination.exists():
                    shutil.move(str(destination), str(source))

    for line in result.stdout.splitlines():
        if line.startswith("  - ") and ":" in line:
            path = line.removeprefix("  - ").split(":", 1)[0].strip()
            if path:
                summary.placeholder_related.add(path)
        elif line:
            summary.placeholder_notes.append(line)
    for line in result.stderr.splitlines():
        if line:
            summary.placeholder_notes.append(f"stderr: {line}")
    if result.returncode != 0:
        raise MaterializationError(
            summarize_helper_failure(
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )
        )
    if not summary.placeholder_related:
        summary.placeholder_notes.append("no approved placeholders were replaced")


def most_specific_local_override(
    relative_path: str,
    local_overrides: tuple[LocalOverride, ...],
) -> LocalOverride | None:
    """Return the most specific local override matching a repository path."""
    matches = [override for override in local_overrides if override.matches(relative_path)]
    if not matches:
        return None
    return sorted(matches, key=lambda override: (len(override.path), not override.is_directory))[-1]


def protected_decision_for_path(
    relative_path: str,
    protected_decisions: tuple[ProtectedFileDecision, ...],
) -> ProtectedFileDecision | None:
    """Return the exact protected-file decision for a path, if present."""
    for decision in protected_decisions:
        if decision.path == relative_path:
            return decision
    return None


def deferred_candidate_for_path(
    relative_path: str,
    deferred_candidates: tuple[DeferredProtectedCandidate, ...],
) -> DeferredProtectedCandidate | None:
    """Return the exact deferred protected candidate for a path, if present."""
    for candidate in deferred_candidates:
        if candidate.path == relative_path:
            return candidate
    return None


def conflict_for_non_protected_path(
    relative_path: str,
    *,
    recorded: bool,
    decision: str | None,
) -> Conflict:
    """Return an actionable non-protected conflict description."""
    if recorded:
        assert decision is not None
        return Conflict(
            path=relative_path,
            classification=f"recorded local_overrides {decision}",
            resolution=(
                "change the local_overrides entry to TAKE or SKIP to resolve, "
                "or keep it as a recorded unresolved decision"
            ),
            recorded=True,
        )
    return Conflict(
        path=relative_path,
        classification="unrecorded non-protected overwrite conflict",
        resolution=(
            "add template_sync.local_overrides with default_decision TAKE or SKIP, "
            "or record MERGE, DEFER, PROTECTED-REVIEW, or REMOVE-LOCAL"
        ),
        recorded=False,
    )


def conflict_for_protected_path(
    relative_path: str,
    *,
    recorded: bool,
    decision: str | None,
) -> Conflict:
    """Return an actionable protected-file conflict description."""
    if recorded:
        assert decision is not None
        return Conflict(
            path=relative_path,
            classification=f"recorded protected decision {decision}",
            resolution=(
                "change protected_file_decisions to TAKE or SKIP to resolve, "
                "or keep the protected path recorded as unresolved"
            ),
            recorded=True,
        )
    return Conflict(
        path=relative_path,
        classification="unrecorded protected-file decision required",
        resolution=(
            "add template_sync.protected_file_decisions or "
            "template_sync.deferred_protected_candidates for this concrete path"
        ),
        recorded=False,
    )


def write_staged_bytes(target_path: Path, bytes_content: bytes) -> None:
    """Write materialized bytes to the target path."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(bytes_content)


def ensure_regular_target(target_path: Path, relative_path: str) -> None:
    """Raise an actionable error when an existing target path is not a regular file.

    A directory or symlink where a regular file is expected would otherwise surface
    later as a path-stripped ``IsADirectoryError`` from a read or write. Failing here
    with the repository-relative ``relative_path`` lets the adopter resolve the
    conflict safely.
    """
    if target_path.exists() and not target_path.is_file():
        raise MaterializationError(
            f"Cannot reconcile {relative_path}: the target path exists but is not a "
            "regular file (for example a directory or a symlink to one). Resolve the "
            "conflict in the downstream repository, then rerun."
        )


def reconcile_staged_files(
    *,
    staging_root: Path,
    target_root: Path,
    staged_paths: Iterable[str],
    decisions: Decisions,
    summary: Summary,
) -> None:
    """Reconcile staged candidates into the target without overwriting conflicts."""
    for relative_path in sorted(staged_paths):
        staged_path = resolve_safe_repository_target_path(
            staging_root,
            relative_path,
            field_name="staged path",
        )
        target_path = resolve_safe_repository_target_path(
            target_root,
            relative_path,
            field_name="target path",
        )
        staged_bytes = staged_path.read_bytes()
        ensure_regular_target(target_path, relative_path)
        target_exists = target_path.exists()
        target_bytes = target_path.read_bytes() if target_exists else None
        is_identical = target_bytes == staged_bytes if target_exists else False
        is_protected = is_protected_instruction_path(relative_path)

        if is_protected:
            summary.protected.add(relative_path)
            decision = protected_decision_for_path(
                relative_path,
                decisions.marker_data.protected_decisions,
            )
            deferred_candidate = deferred_candidate_for_path(
                relative_path,
                decisions.marker_data.deferred_candidates,
            )
            if deferred_candidate is not None and decision is None:
                summary.deferred.add(relative_path)
                summary.conflicts.append(
                    conflict_for_protected_path(
                        relative_path,
                        recorded=True,
                        decision="deferred_protected_candidates",
                    )
                )
                continue
            if decision is None:
                summary.conflicts.append(
                    conflict_for_protected_path(
                        relative_path,
                        recorded=False,
                        decision=None,
                    )
                )
                continue
            if decision.decision == TEMPLATE_SKIP_DECISION:
                summary.skipped.add(relative_path)
                continue
            if decision.decision == TEMPLATE_TAKE_DECISION:
                if is_identical:
                    summary.unchanged.add(relative_path)
                elif target_exists:
                    write_staged_bytes(target_path, staged_bytes)
                    summary.updated.add(relative_path)
                else:
                    write_staged_bytes(target_path, staged_bytes)
                    summary.created.add(relative_path)
                continue
            if decision.decision == REMOVAL_DECISION:
                summary.recorded_removals.add(relative_path)
            else:
                summary.deferred.add(relative_path)
            summary.conflicts.append(
                conflict_for_protected_path(
                    relative_path,
                    recorded=True,
                    decision=decision.decision,
                )
            )
            continue

        local_override = most_specific_local_override(
            relative_path,
            decisions.marker_data.local_overrides,
        )
        if local_override is not None:
            summary.locally_overridden.add(relative_path)
            decision = local_override.default_decision
            if decision == TEMPLATE_SKIP_DECISION:
                summary.skipped.add(relative_path)
                continue
            if decision == TEMPLATE_TAKE_DECISION:
                if is_identical:
                    summary.unchanged.add(relative_path)
                elif target_exists:
                    write_staged_bytes(target_path, staged_bytes)
                    summary.updated.add(relative_path)
                else:
                    write_staged_bytes(target_path, staged_bytes)
                    summary.created.add(relative_path)
                continue
            if decision == REMOVAL_DECISION:
                summary.recorded_removals.add(relative_path)
            else:
                summary.deferred.add(relative_path)
            summary.conflicts.append(
                conflict_for_non_protected_path(
                    relative_path,
                    recorded=True,
                    decision=decision,
                )
            )
            continue

        if not target_exists:
            write_staged_bytes(target_path, staged_bytes)
            summary.created.add(relative_path)
        elif is_identical:
            summary.unchanged.add(relative_path)
        else:
            summary.conflicts.append(
                conflict_for_non_protected_path(
                    relative_path,
                    recorded=False,
                    decision=None,
                )
            )


def reconcile_marker(
    *,
    target_root: Path,
    decisions: Decisions,
    summary: Summary,
    computed_marker_text: str,
) -> None:
    """Apply marker advancement rules independently from file reconciliation."""
    has_support = "template-sync-support" in decisions.included_modules
    if not has_support:
        summary.marker_status = "preview-only"
        summary.marker_reason = "template-sync-support is not included"
        summary.computed_marker_preview = computed_marker_text
        return
    if summary.unrecorded_conflicts:
        summary.marker_status = "preview-only"
        summary.marker_reason = "unrecorded conflicts remain"
        summary.computed_marker_preview = computed_marker_text
        return

    marker_path = resolve_safe_repository_target_path(
        target_root,
        DEFAULT_MARKER_PATH,
        field_name="marker path",
    )
    ensure_regular_target(marker_path, DEFAULT_MARKER_PATH)
    marker_bytes = computed_marker_text.encode("utf-8")
    existing_bytes = marker_path.read_bytes() if marker_path.exists() else None
    if existing_bytes == marker_bytes:
        summary.marker_status = "unchanged"
        summary.marker_reason = "existing marker already equals computed marker"
        return
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.write_bytes(marker_bytes)
    summary.marker_status = "updated"
    summary.marker_reason = "computed marker written"


def sorted_items(items: Iterable[str]) -> list[str]:
    """Return deterministic display items."""
    return sorted(set(items))


def print_section(title: str, items: Iterable[str]) -> None:
    """Print a deterministic bullet section."""
    values = sorted_items(items)
    print(f"{title}:")
    if not values:
        print("  - (none)")
        return
    for value in values:
        print(f"  - {value}")


def print_conflicts(conflicts: Iterable[Conflict]) -> None:
    """Print actionable conflict details."""
    conflict_items = sorted(conflicts, key=lambda conflict: conflict.path)
    print("Conflicted paths:")
    if not conflict_items:
        print("  - (none)")
        return
    for conflict in conflict_items:
        state = "recorded" if conflict.recorded else "unrecorded"
        print(f"  - {conflict.path}: {state}; {conflict.classification}")
        print(f"    authorize: {conflict.resolution}")


def print_summary(summary: Summary) -> None:
    """Emit the deterministic human-readable materialization summary."""
    print("Materialization summary")
    print(f"Default adoption mode: {summary.default_adoption_mode}")
    print_section("Retained modules", summary.retained_modules)
    print_section("Excluded modules", summary.excluded_modules)
    print_section("Created paths", summary.created)
    print_section("Updated paths", summary.updated)
    print_section("Unchanged paths", summary.unchanged)
    print_section("Skipped paths", summary.skipped)
    print_conflicts(summary.conflicts)
    print_section("Protected paths", summary.protected)
    print_section("Locally overridden paths", summary.locally_overridden)
    print_section("Deferred paths", summary.deferred)
    print_section("Recorded but not applied removals", summary.recorded_removals)
    print_section("Unmapped template paths", summary.unmapped)
    print_section("Excluded template-managed paths", summary.excluded_paths)
    print_section("Byte-only paths", summary.byte_only)
    print_section("Placeholder-related paths", summary.placeholder_related)
    print_section("Placeholder notes", summary.placeholder_notes)
    print("Marker:")
    print(f"  - {summary.marker_status}: {summary.marker_reason}")
    if summary.recorded_conflicts:
        print("Recorded unresolved decisions remain:")
        for conflict in sorted(summary.recorded_conflicts, key=lambda item: item.path):
            print(f"  - {conflict.path}: {conflict.classification}")
    if summary.computed_marker_preview is not None:
        print("Computed marker preview:")
        for line in summary.computed_marker_preview.rstrip("\n").splitlines():
            print(f"  {line}")


def materialize(args: argparse.Namespace) -> Summary:
    """Run first-adoption materialization and return the operation summary."""
    template_root = resolve_existing_root(
        args.template_root,
        default=default_template_root(),
        name="--template-root",
    )
    target_root = resolve_existing_root(
        args.target_root,
        default=None,
        name="--target-root",
    )
    _manifest, module_order, mappings = load_validated_manifest_context(template_root)
    decisions = load_decisions(
        args,
        template_root=template_root,
        target_root=target_root,
        module_order=module_order,
    )

    marker_document = computed_marker_document(
        decisions=decisions,
        module_order=module_order,
    )
    validate_computed_marker(marker_document, template_root=template_root)
    computed_marker_text = marker_yaml(marker_document)

    retained_modules = ordered_modules(module_order, decisions.included_modules)
    excluded_modules = [
        module for module in module_order if module not in decisions.included_modules
    ]
    summary = Summary(
        retained_modules=retained_modules,
        excluded_modules=excluded_modules,
        default_adoption_mode=args.default_adoption_mode,
    )

    with tempfile.TemporaryDirectory(prefix="template-adoption-") as temporary_directory:
        staging_root = Path(temporary_directory)
        staged_paths = write_staged_candidate(
            template_root=template_root,
            staging_root=staging_root,
            mappings=mappings,
            included_modules=decisions.included_modules,
            summary=summary,
        )
        run_placeholder_helper(
            args=args,
            template_root=template_root,
            staging_root=staging_root,
            summary=summary,
        )
        reconcile_staged_files(
            staging_root=staging_root,
            target_root=target_root,
            staged_paths=staged_paths,
            decisions=decisions,
            summary=summary,
        )

    reconcile_marker(
        target_root=target_root,
        decisions=decisions,
        summary=summary,
        computed_marker_text=computed_marker_text,
    )
    return summary


def format_cli_error(error: Exception) -> str:
    """Return a user-facing error message that never leaks filesystem paths.

    ``OSError`` and its subclasses (including ``shutil.Error``) render their
    default string form with the offending absolute local path, so summarize
    them through :func:`os_error_summary`. Domain errors already carry
    intentional, path-safe messages and are returned unchanged.
    """
    if isinstance(error, OSError):
        return os_error_summary(error)
    return f"{error}"


def main(argv: Sequence[str] | None = None) -> int:
    """Run the materialization CLI."""
    args = parse_args(argv)
    try:
        summary = materialize(args)
    except (
        MaterializationError,
        TemplateSyncMaterializationError,
        OSError,
    ) as error:
        print(f"ERROR: {format_cli_error(error)}", file=sys.stderr)
        return EXIT_RUNTIME_FAILURE

    print_summary(summary)
    if summary.unrecorded_conflicts and not args.allow_conflicts:
        return EXIT_DECISIONS_REQUIRED
    return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())
