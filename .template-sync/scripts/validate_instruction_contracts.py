"""Validate required anchors in retained protected instruction files."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NoReturn

import validate_marker

DEFAULT_CONTRACTS_PATH = ".template-sync/instruction-contracts.yml"
DEFAULT_CONTRACTS_SCHEMA_PATH = "schemas/template-sync-instruction-contracts.schema.json"
VALIDATION_MODES = ("upstream-template", "downstream")


class InstructionContractValidationError(Exception):
    """Raised when instruction contract validation cannot produce a clean result."""


@dataclass(frozen=True)
class InstructionContract:
    """Required anchors for one protected instruction file."""

    path: str
    requires_modules: tuple[str, ...]
    required_headings: tuple[str, ...]
    required_phrases: tuple[str, ...]


@dataclass(frozen=True)
class InstructionContractWaiver:
    """A marker waiver for one missing instruction-contract anchor."""

    path: str
    anchor: str
    reason: str
    authorization_basis: str


@dataclass(frozen=True)
class MissingAnchor:
    """A required heading or phrase that was not found in a retained file."""

    path: str
    anchor_type: str
    anchor: str


@dataclass(frozen=True)
class MissingFile:
    """A retained instruction contract whose file is absent without removal authorization."""

    path: str


@dataclass(frozen=True)
class AuthorizedRemoval:
    """A missing protected file skipped because marker authorization removed it."""

    path: str
    authorization_basis: str
    authorized_scope: str
    reason: str


@dataclass(frozen=True)
class SkippedContract:
    """A downstream contract skipped because its required modules are not retained."""

    path: str
    requires_modules: tuple[str, ...]


@dataclass(frozen=True)
class InstructionContractReport:
    """Instruction contract validation details to print for the operator."""

    mode: str
    contracts_checked: tuple[InstructionContract, ...]
    skipped_contracts: tuple[SkippedContract, ...]
    missing_files: tuple[MissingFile, ...]
    missing_anchors: tuple[MissingAnchor, ...]
    applied_waivers: tuple[InstructionContractWaiver, ...]
    authorized_removals: tuple[AuthorizedRemoval, ...]
    warnings: tuple[str, ...]

    @property
    def has_failures(self) -> bool:
        """Return whether validation found unwaived missing files or anchors."""
        return bool(self.missing_files or self.missing_anchors)


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Validate required headings and phrases in protected instruction files "
            "declared by .template-sync/instruction-contracts.yml."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Validation modes:\n"
            "  --mode upstream-template validates every contract against the template's "
            "own files, ignores marker-derived gating, and never fails merely because "
            ".template-sync/marker.yml is absent.\n"
            "  --mode downstream validates only contracts whose requires_modules are all "
            "listed in template_sync.included_modules from .template-sync/marker.yml.\n\n"
            "Warnings:\n"
            "  --mode upstream-template emits a non-blocking warning when the marker "
            "path exists, because that usually means the command is running against a "
            "downstream working tree that should use --mode downstream."
        ),
    )
    parser.add_argument(
        "--mode",
        choices=VALIDATION_MODES,
        required=True,
        help="Required validation mode. No implicit mode detection is performed.",
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
        "--contracts",
        default=DEFAULT_CONTRACTS_PATH,
        help=(
            "Instruction contract path relative to the repository root. "
            f"Default: {DEFAULT_CONTRACTS_PATH}"
        ),
    )
    parser.add_argument(
        "--contracts-schema",
        default=DEFAULT_CONTRACTS_SCHEMA_PATH,
        help=(
            "Instruction contract JSON Schema path relative to the repository root. "
            f"Default: {DEFAULT_CONTRACTS_SCHEMA_PATH}"
        ),
    )
    parser.add_argument(
        "--marker",
        default=validate_marker.DEFAULT_MARKER_PATH,
        help=(
            "Marker path relative to the repository root for --mode downstream. "
            f"Default: {validate_marker.DEFAULT_MARKER_PATH}"
        ),
    )
    parser.add_argument(
        "--marker-schema",
        default=validate_marker.DEFAULT_MARKER_SCHEMA_PATH,
        help=(
            "Marker JSON Schema path relative to the repository root for --mode downstream. "
            f"Default: {validate_marker.DEFAULT_MARKER_SCHEMA_PATH}"
        ),
    )
    parser.add_argument(
        "--manifest",
        default=validate_marker.DEFAULT_MANIFEST_PATH,
        help=(
            "Manifest path relative to the repository root. "
            f"Default: {validate_marker.DEFAULT_MANIFEST_PATH}"
        ),
    )
    parser.add_argument(
        "--manifest-schema",
        default=validate_marker.DEFAULT_MANIFEST_SCHEMA_PATH,
        help=(
            "Manifest JSON Schema path relative to the repository root. "
            f"Default: {validate_marker.DEFAULT_MANIFEST_SCHEMA_PATH}"
        ),
    )
    parser.add_argument(
        "--require-marker",
        action="store_true",
        help=(
            "In --mode downstream, fail when the marker file is absent instead of "
            "treating the run as a no-op."
        ),
    )
    parser.add_argument(
        "--skip-if-marker-present",
        action="store_true",
        help=(
            "In --mode upstream-template, exit 0 immediately without validating "
            "when the marker file exists. Intended for shared pre-commit and CI "
            "hooks that run upstream-template validation in the upstream template "
            "repository but should defer to --mode downstream in downstream forks."
        ),
    )
    return parser.parse_args(argv)


def load_schema_validated_yaml(
    document_path: Path,
    schema_path: Path,
    repo_root: Path,
) -> dict[str, Any]:
    """Load a YAML mapping and validate it against a JSON Schema."""
    document = validate_marker.load_yaml_mapping(document_path, repo_root)
    schema = validate_marker.load_json_mapping(schema_path, repo_root)
    validate_marker.validate_schema(document, schema, document_path, repo_root)
    return document


def load_manifest_modules(
    manifest_path: Path,
    manifest_schema_path: Path,
    repo_root: Path,
) -> set[str]:
    """Load the template manifest and return its declared module names."""
    manifest = load_schema_validated_yaml(manifest_path, manifest_schema_path, repo_root)
    module_names, _mappings = validate_marker.parse_manifest_mappings(manifest)
    return set(module_names)


def _required_string_list(
    raw_contract: dict[str, Any],
    field_name: str,
) -> tuple[str, ...]:
    """Return a tuple from an optional schema-validated string list."""
    values = raw_contract.get(field_name, [])
    if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
        path = raw_contract.get("path", "<unknown>")
        raise InstructionContractValidationError(f"{path} {field_name} must be a string list.")
    return tuple(values)


def parse_contracts(
    contracts_document: dict[str, Any],
    manifest_modules: set[str],
) -> tuple[InstructionContract, ...]:
    """Extract normalized instruction contracts from a schema-validated document."""
    raw_contracts = contracts_document.get("instruction_contracts")
    if not isinstance(raw_contracts, list):
        raise InstructionContractValidationError("instruction_contracts must be a list.")

    contracts: list[InstructionContract] = []
    seen_paths: set[str] = set()
    for raw_contract in raw_contracts:
        if not isinstance(raw_contract, dict):
            raise InstructionContractValidationError("Each instruction contract must be a mapping.")

        raw_path = raw_contract.get("path")
        if not isinstance(raw_path, str):
            raise InstructionContractValidationError("Each instruction contract must define path.")
        path, is_directory = validate_marker.normalize_repository_path(
            raw_path,
            "instruction_contracts[].path",
        )
        if is_directory:
            raise InstructionContractValidationError(
                f"instruction_contracts[].path must reference a file, not a directory: {raw_path}"
            )
        if path in seen_paths:
            raise InstructionContractValidationError(f"Duplicate instruction contract path: {path}")
        seen_paths.add(path)

        requires_modules = _required_string_list(raw_contract, "requires_modules")
        if not requires_modules:
            raise InstructionContractValidationError(f"{path} requires_modules must not be empty.")
        unknown_modules = set(requires_modules) - manifest_modules
        if unknown_modules:
            raise InstructionContractValidationError(
                f"{path} references unknown manifest module(s): "
                + ", ".join(sorted(unknown_modules))
            )

        required_headings = _required_string_list(raw_contract, "required_headings")
        required_phrases = _required_string_list(raw_contract, "required_phrases")
        if not required_headings and not required_phrases:
            raise InstructionContractValidationError(
                f"{path} must define at least one required heading or phrase."
            )

        contracts.append(
            InstructionContract(
                path=path,
                requires_modules=requires_modules,
                required_headings=required_headings,
                required_phrases=required_phrases,
            )
        )
    return tuple(contracts)


def load_contracts(
    contracts_path: Path,
    contracts_schema_path: Path,
    manifest_path: Path,
    manifest_schema_path: Path,
    repo_root: Path,
) -> tuple[InstructionContract, ...]:
    """Load and validate instruction contracts against the manifest taxonomy."""
    manifest_modules = load_manifest_modules(manifest_path, manifest_schema_path, repo_root)
    contracts_document = load_schema_validated_yaml(
        contracts_path, contracts_schema_path, repo_root
    )
    return parse_contracts(contracts_document, manifest_modules)


def parse_instruction_contract_waivers(
    marker_document: dict[str, Any],
) -> tuple[InstructionContractWaiver, ...]:
    """Extract normalized instruction-contract waivers from a marker document."""
    template_sync = marker_document.get("template_sync")
    if not isinstance(template_sync, dict):
        raise InstructionContractValidationError("Marker must contain template_sync mapping.")

    waivers: list[InstructionContractWaiver] = []
    seen_pairs: set[tuple[str, str]] = set()
    duplicate_pairs: set[tuple[str, str]] = set()
    for raw_waiver in template_sync.get("instruction_contract_waivers", []):
        if not isinstance(raw_waiver, dict):
            raise InstructionContractValidationError(
                "Each instruction contract waiver must be a mapping."
            )
        raw_path = raw_waiver.get("path")
        anchor = raw_waiver.get("anchor")
        reason = raw_waiver.get("reason")
        authorization_basis = raw_waiver.get("authorization_basis")
        if (
            not isinstance(raw_path, str)
            or not isinstance(anchor, str)
            or not isinstance(reason, str)
            or not isinstance(authorization_basis, str)
        ):
            raise InstructionContractValidationError(
                "Each instruction contract waiver must define string path, anchor, "
                "reason, and authorization_basis."
            )
        path, is_directory = validate_marker.normalize_repository_path(
            raw_path,
            "template_sync.instruction_contract_waivers[].path",
        )
        if is_directory:
            raise InstructionContractValidationError(
                "template_sync.instruction_contract_waivers[].path must reference a file, "
                f"not a directory: {raw_path}"
            )
        waiver_pair = (path, anchor)
        if waiver_pair in seen_pairs:
            duplicate_pairs.add(waiver_pair)
        seen_pairs.add(waiver_pair)
        waivers.append(
            InstructionContractWaiver(
                path=path,
                anchor=anchor,
                reason=reason,
                authorization_basis=authorization_basis,
            )
        )
    if duplicate_pairs:
        formatted_pairs = ", ".join(
            f"({path}, {anchor})" for path, anchor in sorted(duplicate_pairs)
        )
        raise InstructionContractValidationError(
            "Duplicate template_sync.instruction_contract_waivers (path, anchor) "
            f"pair(s): {formatted_pairs}"
        )
    return tuple(waivers)


def load_marker_for_downstream(
    marker_path: Path,
    marker_schema_path: Path,
    manifest_modules: set[str],
    repo_root: Path,
) -> tuple[
    set[str],
    tuple[validate_marker.ProtectedFileDecision, ...],
    tuple[InstructionContractWaiver, ...],
]:
    """Load downstream marker state needed by instruction-contract validation."""
    marker = load_schema_validated_yaml(marker_path, marker_schema_path, repo_root)
    (
        included_modules,
        _local_overrides,
        _local_path_ownership,
        _deferred_candidates,
        protected_decisions,
    ) = validate_marker.parse_marker(marker)
    unknown_included_modules = included_modules - manifest_modules
    if unknown_included_modules:
        raise InstructionContractValidationError(
            "Marker includes module(s) that are not defined by the manifest: "
            + ", ".join(sorted(unknown_included_modules))
        )
    return (
        included_modules,
        protected_decisions,
        parse_instruction_contract_waivers(marker),
    )


def read_instruction_file(repo_root: Path, relative_path: str) -> str | None:
    """Return instruction file text, or ``None`` when the file is absent."""
    path = validate_marker.resolve_repo_path(repo_root, relative_path)
    if not path.exists():
        return None
    if not path.is_file():
        raise InstructionContractValidationError(f"{relative_path} is not a regular file.")
    try:
        return path.read_text(encoding="utf-8")
    except OSError as error:
        error_summary = f"{type(error).__name__}: {error.strerror or 'I/O error'}"
        raise InstructionContractValidationError(
            f"Unable to read {relative_path}: {error_summary}"
        ) from error


def find_waiver(
    waivers: tuple[InstructionContractWaiver, ...],
    path: str,
    anchor: str,
) -> InstructionContractWaiver | None:
    """Return a waiver that matches ``path`` and ``anchor``, if present."""
    for waiver in waivers:
        if waiver.path == path and waiver.anchor == anchor:
            return waiver
    return None


def authorized_removal_for(
    protected_decisions: tuple[validate_marker.ProtectedFileDecision, ...],
    path: str,
) -> AuthorizedRemoval | None:
    """Return authorized removal details for an absent protected file, if present."""
    for protected_decision in protected_decisions:
        if (
            protected_decision.path == path
            and protected_decision.decision == validate_marker.REMOVAL_DECISION
        ):
            return AuthorizedRemoval(
                path=path,
                authorization_basis=protected_decision.authorization_basis or "",
                authorized_scope=protected_decision.authorized_scope or "",
                reason=protected_decision.reason or "",
            )
    return None


def strip_fenced_code_blocks(text: str) -> str:
    """Return ``text`` with CommonMark fenced code blocks removed.

    Required anchors must appear as live Markdown content; example anchors
    nested in a fenced code block should not satisfy the contract.
    """
    lines = text.splitlines()
    out: list[str] = []
    open_fence: str | None = None
    for line in lines:
        stripped = line.lstrip()
        if open_fence is None:
            if stripped.startswith("```") or stripped.startswith("~~~"):
                fence_char = stripped[0]
                run = 0
                while run < len(stripped) and stripped[run] == fence_char:
                    run += 1
                if run >= 3:
                    open_fence = fence_char * run
                    continue
            out.append(line)
        else:
            fence_char = open_fence[0]
            run = 0
            while run < len(stripped) and stripped[run] == fence_char:
                run += 1
            if run >= len(open_fence) and stripped[run:].strip() == "":
                open_fence = None
    return "\n".join(out)


def heading_is_present(text: str, heading: str) -> bool:
    """Return whether ``heading`` appears as a CommonMark ATX heading line.

    Per CommonMark, an ATX heading may have 0-3 leading spaces of indentation;
    lines with 4+ leading spaces or any leading tab character are indented code
    blocks rather than headings and cannot satisfy the contract.
    """
    for line in text.splitlines():
        leading_spaces = 0
        has_leading_tab = False
        for ch in line:
            if ch == " ":
                leading_spaces += 1
            elif ch == "\t":
                has_leading_tab = True
                break
            else:
                break
        if has_leading_tab or leading_spaces > 3:
            continue
        if line[leading_spaces:].rstrip() == heading:
            return True
    return False


def validate_contracts(
    *,
    mode: str,
    repo_root: Path,
    contracts: tuple[InstructionContract, ...],
    included_modules: set[str] | None = None,
    protected_decisions: tuple[validate_marker.ProtectedFileDecision, ...] = (),
    waivers: tuple[InstructionContractWaiver, ...] = (),
    warnings: tuple[str, ...] = (),
) -> InstructionContractReport:
    """Validate selected instruction contracts against the working tree."""
    checked_contracts: list[InstructionContract] = []
    skipped_contracts: list[SkippedContract] = []
    missing_files: list[MissingFile] = []
    missing_anchors: list[MissingAnchor] = []
    applied_waivers: list[InstructionContractWaiver] = []
    authorized_removals: list[AuthorizedRemoval] = []

    for contract in contracts:
        if included_modules is not None and not set(contract.requires_modules).issubset(
            included_modules
        ):
            skipped_contracts.append(
                SkippedContract(
                    path=contract.path,
                    requires_modules=contract.requires_modules,
                )
            )
            continue

        text = read_instruction_file(repo_root, contract.path)
        if text is None:
            authorized_removal = authorized_removal_for(protected_decisions, contract.path)
            if authorized_removal is not None:
                authorized_removals.append(authorized_removal)
            else:
                missing_files.append(MissingFile(path=contract.path))
            continue

        checked_contracts.append(contract)
        scannable_text = strip_fenced_code_blocks(text)
        for heading in contract.required_headings:
            if heading_is_present(scannable_text, heading):
                continue
            waiver = find_waiver(waivers, contract.path, heading)
            if waiver is not None:
                applied_waivers.append(waiver)
            else:
                missing_anchors.append(
                    MissingAnchor(
                        path=contract.path,
                        anchor_type="heading",
                        anchor=heading,
                    )
                )
        for phrase in contract.required_phrases:
            if phrase in scannable_text:
                continue
            waiver = find_waiver(waivers, contract.path, phrase)
            if waiver is not None:
                applied_waivers.append(waiver)
            else:
                missing_anchors.append(
                    MissingAnchor(
                        path=contract.path,
                        anchor_type="phrase",
                        anchor=phrase,
                    )
                )

    return InstructionContractReport(
        mode=mode,
        contracts_checked=tuple(checked_contracts),
        skipped_contracts=tuple(skipped_contracts),
        missing_files=tuple(missing_files),
        missing_anchors=tuple(missing_anchors),
        applied_waivers=tuple(dict.fromkeys(applied_waivers)),
        authorized_removals=tuple(authorized_removals),
        warnings=warnings,
    )


def print_report(report: InstructionContractReport) -> None:
    """Print a human-readable instruction contract report."""
    for warning in report.warnings:
        print(f"WARNING: {warning}")

    if report.has_failures:
        print("Instruction-contract validation failed.")
    elif report.applied_waivers:
        print("Instruction-contract validation passed with waivers.")
    else:
        print("Instruction-contract validation passed.")

    print(f"Mode: {report.mode}")
    print(f"Contracts checked: {len(report.contracts_checked)}")

    if report.skipped_contracts:
        print("\nContracts skipped by downstream module selection:")
        for skipped_contract in report.skipped_contracts:
            print(
                f"  - {skipped_contract.path} "
                f"(requires: {', '.join(skipped_contract.requires_modules)})"
            )

    if report.missing_files:
        print("\nRequired instruction files absent without authorized removal:")
        for missing_file in report.missing_files:
            print(f"  - {missing_file.path}")

    if report.missing_anchors:
        print("\nMissing required anchors:")
        for missing_anchor in report.missing_anchors:
            print(
                f"  - {missing_anchor.path}: missing required "
                f"{missing_anchor.anchor_type}: {missing_anchor.anchor}"
            )

    if report.authorized_removals:
        print("\nAuthorized removals skipped:")
        for authorized_removal in report.authorized_removals:
            print(f"  - {authorized_removal.path}")
            print(f"    authorization_basis: {authorized_removal.authorization_basis}")
            print(f"    authorized_scope: {authorized_removal.authorized_scope}")
            print(f"    reason: {authorized_removal.reason}")

    if report.applied_waivers:
        print("\nInstruction contract waivers applied:")
        for waiver in report.applied_waivers:
            print(f"  - {waiver.path}: {waiver.anchor}")
            print(f"    reason: {waiver.reason}")
            print(f"    authorization_basis: {waiver.authorization_basis}")


def fail(message: str) -> NoReturn:
    """Print an error and exit non-zero."""
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def main(argv: list[str] | None = None) -> int:
    """Run instruction-contract validation."""
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        repo_root = validate_marker.resolve_repo_root(args.repo_root)
        contracts_path = validate_marker.resolve_repo_path(repo_root, args.contracts)
        contracts_schema_path = validate_marker.resolve_repo_path(repo_root, args.contracts_schema)
        marker_path = validate_marker.resolve_repo_path(repo_root, args.marker)
        marker_schema_path = validate_marker.resolve_repo_path(repo_root, args.marker_schema)
        manifest_path = validate_marker.resolve_repo_path(repo_root, args.manifest)
        manifest_schema_path = validate_marker.resolve_repo_path(repo_root, args.manifest_schema)

        if args.mode == "downstream" and not marker_path.exists():
            marker_relative_path = validate_marker.repository_relative_path(marker_path, repo_root)
            if args.require_marker:
                raise InstructionContractValidationError(
                    f"Marker is required but was not found at {marker_relative_path}."
                )
            print(
                f"No marker found at {marker_relative_path}; "
                "instruction-contract validation skipped."
            )
            return 0

        manifest_modules = load_manifest_modules(manifest_path, manifest_schema_path, repo_root)
        contracts_document = load_schema_validated_yaml(
            contracts_path,
            contracts_schema_path,
            repo_root,
        )
        contracts = parse_contracts(contracts_document, manifest_modules)
        warnings: tuple[str, ...] = ()

        if args.mode == "upstream-template":
            marker_relative_path = validate_marker.repository_relative_path(marker_path, repo_root)
            if marker_path.exists():
                if args.skip_if_marker_present:
                    print(
                        f"--mode upstream-template skipped: {marker_relative_path} "
                        "is present and --skip-if-marker-present was supplied."
                    )
                    return 0
                warnings = (
                    "--mode upstream-template was invoked while "
                    f"{marker_relative_path} is present; use --mode downstream for "
                    "marker-gated downstream validation.",
                )
            report = validate_contracts(
                mode=args.mode,
                repo_root=repo_root,
                contracts=contracts,
                warnings=warnings,
            )
        else:
            included_modules, protected_decisions, waivers = load_marker_for_downstream(
                marker_path,
                marker_schema_path,
                manifest_modules,
                repo_root,
            )
            report = validate_contracts(
                mode=args.mode,
                repo_root=repo_root,
                contracts=contracts,
                included_modules=included_modules,
                protected_decisions=protected_decisions,
                waivers=waivers,
            )
    except (
        InstructionContractValidationError,
        validate_marker.MarkerValidationError,
    ) as error:
        fail(str(error))

    print_report(report)
    return 1 if report.has_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
