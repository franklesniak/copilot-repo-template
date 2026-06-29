"""Validate required anchors in retained protected instruction files."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NoReturn, cast

import validate_marker
from template_sync_materialization_helpers import (
    MARKDOWN_FENCE_CONTEXT,
    lines_outside_markdown_fences,
)

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
class ProtectedGuideSectionObligation:
    """Protected-guide headings or phrases that are stale when modules are excluded."""

    key: str
    path: str
    target_modules: tuple[str, ...]
    stale_headings: tuple[str, ...]
    stale_phrases: tuple[str, ...]


@dataclass(frozen=True)
class ProtectedGuideReferenceObligation:
    """Protected-guide references that are stale when modules are excluded."""

    key: str
    path: str
    reference_kind: str
    target_modules: tuple[str, ...]
    target_path: str | None
    tokens: tuple[str, ...]


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
class StaleProtectedGuideSection:
    """A protected-guide heading or phrase that still describes an excluded module."""

    path: str
    contract_key: str
    anchor_type: str
    anchor: str
    target_modules: tuple[str, ...]


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
    stale_protected_guide_sections: tuple[StaleProtectedGuideSection, ...]
    applied_waivers: tuple[InstructionContractWaiver, ...]
    applied_protected_guide_waivers: tuple[validate_marker.ProtectedGuideContractWaiver, ...]
    authorized_removals: tuple[AuthorizedRemoval, ...]
    warnings: tuple[str, ...]

    @property
    def has_failures(self) -> bool:
        """Return whether validation found unwaived missing files or anchors."""
        return bool(
            self.missing_files or self.missing_anchors or self.stale_protected_guide_sections
        )


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
    raw_contract: dict[str, object],
    field_name: str,
) -> tuple[str, ...]:
    """Return a tuple from an optional schema-validated string list."""
    values = raw_contract.get(field_name, [])
    if not isinstance(values, list):
        path_value = raw_contract.get("path")
        path = path_value if isinstance(path_value, str) else "<unknown>"
        raise InstructionContractValidationError(f"{path} {field_name} must be a string list.")
    string_values: list[str] = []
    for value in cast(list[object], values):
        if not isinstance(value, str):
            path_value = raw_contract.get("path")
            path = path_value if isinstance(path_value, str) else "<unknown>"
            raise InstructionContractValidationError(f"{path} {field_name} must be a string list.")
        string_values.append(value)
    return tuple(string_values)


def parse_contracts(
    contracts_document: dict[str, Any],
    manifest_modules: set[str],
) -> tuple[InstructionContract, ...]:
    """Extract normalized instruction contracts from a schema-validated document."""
    raw_contracts = contracts_document.get("instruction_contracts")
    if not isinstance(raw_contracts, list):
        raise InstructionContractValidationError("instruction_contracts must be a list.")
    raw_contracts = cast(list[object], raw_contracts)

    contracts: list[InstructionContract] = []
    seen_paths: set[str] = set()
    for raw_contract in raw_contracts:
        if not isinstance(raw_contract, dict):
            raise InstructionContractValidationError("Each instruction contract must be a mapping.")
        raw_contract = cast(dict[str, object], raw_contract)

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


def parse_protected_guide_section_obligations(
    contracts_document: dict[str, Any],
    manifest_modules: set[str],
) -> tuple[ProtectedGuideSectionObligation, ...]:
    """Extract protected-guide stale-section obligations from a contract document."""
    raw_obligations = contracts_document.get("protected_guide_section_obligations", [])
    if not isinstance(raw_obligations, list):
        raise InstructionContractValidationError(
            "protected_guide_section_obligations must be a list."
        )

    obligations: list[ProtectedGuideSectionObligation] = []
    seen_keys: set[tuple[str, str]] = set()
    duplicate_keys: set[tuple[str, str]] = set()
    for raw_obligation in cast(list[object], raw_obligations):
        if not isinstance(raw_obligation, dict):
            raise InstructionContractValidationError(
                "Each protected guide section obligation must be a mapping."
            )
        raw_obligation = cast(dict[str, object], raw_obligation)

        key = raw_obligation.get("key")
        raw_path = raw_obligation.get("path")
        if not isinstance(key, str) or not isinstance(raw_path, str):
            raise InstructionContractValidationError(
                "Each protected guide section obligation must define key and path."
            )
        path, is_directory = validate_marker.normalize_repository_path(
            raw_path,
            "protected_guide_section_obligations[].path",
        )
        if is_directory:
            raise InstructionContractValidationError(
                "protected_guide_section_obligations[].path must reference a file, "
                f"not a directory: {raw_path}"
            )

        obligation_key = (path, key)
        if obligation_key in seen_keys:
            duplicate_keys.add(obligation_key)
        seen_keys.add(obligation_key)

        target_modules = _required_string_list(raw_obligation, "target_modules")
        if not target_modules:
            raise InstructionContractValidationError(f"{path} target_modules must not be empty.")
        unknown_modules = set(target_modules) - manifest_modules
        if unknown_modules:
            raise InstructionContractValidationError(
                f"{path} protected guide section obligation {key} references unknown "
                "manifest module(s): " + ", ".join(sorted(unknown_modules))
            )

        stale_headings = _required_string_list(raw_obligation, "stale_headings")
        stale_phrases = _required_string_list(raw_obligation, "stale_phrases")
        if not stale_headings and not stale_phrases:
            raise InstructionContractValidationError(
                f"{path} protected guide section obligation {key} must define at least "
                "one stale heading or phrase."
            )

        obligations.append(
            ProtectedGuideSectionObligation(
                key=key,
                path=path,
                target_modules=target_modules,
                stale_headings=stale_headings,
                stale_phrases=stale_phrases,
            )
        )

    if duplicate_keys:
        formatted_keys = ", ".join(f"({path}, {key})" for path, key in sorted(duplicate_keys))
        raise InstructionContractValidationError(
            "Duplicate protected_guide_section_obligations (path, key) pair(s): "
            f"{formatted_keys}"
        )
    return tuple(obligations)


def parse_protected_guide_reference_obligations(
    contracts_document: dict[str, Any],
    manifest_modules: set[str],
) -> tuple[ProtectedGuideReferenceObligation, ...]:
    """Extract protected-guide stale-reference obligations from a contract document."""
    raw_obligations = contracts_document.get("protected_guide_reference_obligations", [])
    if not isinstance(raw_obligations, list):
        raise InstructionContractValidationError(
            "protected_guide_reference_obligations must be a list."
        )

    obligations: list[ProtectedGuideReferenceObligation] = []
    seen_keys: set[tuple[str, str]] = set()
    duplicate_keys: set[tuple[str, str]] = set()
    for raw_obligation in cast(list[object], raw_obligations):
        if not isinstance(raw_obligation, dict):
            raise InstructionContractValidationError(
                "Each protected guide reference obligation must be a mapping."
            )
        raw_obligation = cast(dict[str, object], raw_obligation)

        key = raw_obligation.get("key")
        raw_path = raw_obligation.get("path")
        reference_kind = raw_obligation.get("reference_kind")
        if (
            not isinstance(key, str)
            or not isinstance(raw_path, str)
            or not isinstance(reference_kind, str)
        ):
            raise InstructionContractValidationError(
                "Each protected guide reference obligation must define key, path, "
                "and reference_kind."
            )
        path, is_directory = validate_marker.normalize_repository_path(
            raw_path,
            "protected_guide_reference_obligations[].path",
        )
        if is_directory:
            raise InstructionContractValidationError(
                "protected_guide_reference_obligations[].path must reference a file, "
                f"not a directory: {raw_path}"
            )

        obligation_key = (path, key)
        if obligation_key in seen_keys:
            duplicate_keys.add(obligation_key)
        seen_keys.add(obligation_key)

        target_modules = _required_string_list(raw_obligation, "target_modules")
        if not target_modules:
            raise InstructionContractValidationError(f"{path} target_modules must not be empty.")
        unknown_modules = set(target_modules) - manifest_modules
        if unknown_modules:
            raise InstructionContractValidationError(
                f"{path} protected guide reference obligation {key} references unknown "
                "manifest module(s): " + ", ".join(sorted(unknown_modules))
            )

        target_path = None
        raw_target_path = raw_obligation.get("target_path")
        if raw_target_path is not None:
            if not isinstance(raw_target_path, str):
                raise InstructionContractValidationError(
                    f"{path} protected guide reference obligation {key} target_path "
                    "must be a string."
                )
            target_path, target_is_directory = validate_marker.normalize_repository_path(
                raw_target_path,
                "protected_guide_reference_obligations[].target_path",
            )
            if target_is_directory:
                raise InstructionContractValidationError(
                    "protected_guide_reference_obligations[].target_path must reference "
                    f"a file, not a directory: {raw_target_path}"
                )

        tokens = _required_string_list(raw_obligation, "tokens")
        if reference_kind == "markdown-relative-link" and target_path is None:
            raise InstructionContractValidationError(
                f"{path} protected guide reference obligation {key} must define target_path."
            )
        if reference_kind in {"absolute-url", "prose-reference"} and not tokens:
            raise InstructionContractValidationError(
                f"{path} protected guide reference obligation {key} must define tokens."
            )

        obligations.append(
            ProtectedGuideReferenceObligation(
                key=key,
                path=path,
                reference_kind=reference_kind,
                target_modules=target_modules,
                target_path=target_path,
                tokens=tokens,
            )
        )

    if duplicate_keys:
        formatted_keys = ", ".join(f"({path}, {key})" for path, key in sorted(duplicate_keys))
        raise InstructionContractValidationError(
            "Duplicate protected_guide_reference_obligations (path, key) pair(s): "
            f"{formatted_keys}"
        )
    return tuple(obligations)


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
    template_sync = cast(dict[str, object], template_sync)

    waivers: list[InstructionContractWaiver] = []
    seen_pairs: set[tuple[str, str]] = set()
    duplicate_pairs: set[tuple[str, str]] = set()
    raw_waivers = template_sync.get("instruction_contract_waivers", [])
    if not isinstance(raw_waivers, list):
        raise InstructionContractValidationError("instruction_contract_waivers must be a list.")
    for raw_waiver in cast(list[object], raw_waivers):
        if not isinstance(raw_waiver, dict):
            raise InstructionContractValidationError(
                "Each instruction contract waiver must be a mapping."
            )
        raw_waiver = cast(dict[str, object], raw_waiver)
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
    tuple[validate_marker.ProtectedGuideContractWaiver, ...],
]:
    """Load downstream marker state needed by instruction-contract validation."""
    marker = load_schema_validated_yaml(marker_path, marker_schema_path, repo_root)
    marker_data = validate_marker.parse_marker_decision_data(marker)
    included_modules = set(marker_data.included_modules)
    protected_decisions = marker_data.protected_decisions
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
        marker_data.protected_guide_contract_waivers,
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


def find_protected_guide_waiver(
    waivers: tuple[validate_marker.ProtectedGuideContractWaiver, ...],
    *,
    path: str,
    contract_key: str,
    target_modules: tuple[str, ...],
    target_path: str | None = None,
) -> validate_marker.ProtectedGuideContractWaiver | None:
    """Return a matching protected-guide waiver, if present."""
    target_module_set = set(target_modules)
    for waiver in waivers:
        if waiver.path != path or waiver.contract_key != contract_key:
            continue
        if target_path is not None and waiver.target_path == target_path:
            return waiver
        if waiver.target_module is not None and waiver.target_module in target_module_set:
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


def protected_guide_obligation_applies(
    obligation_target_modules: tuple[str, ...],
    included_modules: set[str],
) -> bool:
    """Return whether a protected-guide obligation is stale for retained modules."""
    return set(obligation_target_modules).isdisjoint(included_modules)


def strip_fenced_code_blocks(text: str) -> str:
    """Return ``text`` with CommonMark fenced code blocks removed.

    Required anchors must appear as live Markdown content; example anchors
    nested in a fenced code block should not satisfy the contract.
    """
    return "\n".join(
        line
        for _line_number, line in lines_outside_markdown_fences(
            text,
            fence_context=MARKDOWN_FENCE_CONTEXT,
        )
    )


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
    protected_guide_section_obligations: tuple[ProtectedGuideSectionObligation, ...] = (),
    included_modules: set[str] | None = None,
    protected_decisions: tuple[validate_marker.ProtectedFileDecision, ...] = (),
    waivers: tuple[InstructionContractWaiver, ...] = (),
    protected_guide_waivers: tuple[validate_marker.ProtectedGuideContractWaiver, ...] = (),
    warnings: tuple[str, ...] = (),
) -> InstructionContractReport:
    """Validate selected instruction contracts against the working tree."""
    checked_contracts: list[InstructionContract] = []
    skipped_contracts: list[SkippedContract] = []
    missing_files: list[MissingFile] = []
    missing_anchors: list[MissingAnchor] = []
    stale_protected_guide_sections: list[StaleProtectedGuideSection] = []
    applied_waivers: list[InstructionContractWaiver] = []
    applied_protected_guide_waivers: list[validate_marker.ProtectedGuideContractWaiver] = []
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

    if included_modules is not None:
        missing_file_paths = {missing_file.path for missing_file in missing_files}
        authorized_removal_paths = {
            authorized_removal.path for authorized_removal in authorized_removals
        }
        for obligation in protected_guide_section_obligations:
            if not protected_guide_obligation_applies(
                obligation.target_modules,
                included_modules,
            ):
                continue

            text = read_instruction_file(repo_root, obligation.path)
            if text is None:
                authorized_removal = authorized_removal_for(
                    protected_decisions,
                    obligation.path,
                )
                if authorized_removal is not None:
                    if authorized_removal.path not in authorized_removal_paths:
                        authorized_removals.append(authorized_removal)
                        authorized_removal_paths.add(authorized_removal.path)
                elif obligation.path not in missing_file_paths:
                    missing_files.append(MissingFile(path=obligation.path))
                    missing_file_paths.add(obligation.path)
                continue

            scannable_text = strip_fenced_code_blocks(text)
            stale_sections: list[StaleProtectedGuideSection] = []
            for heading in obligation.stale_headings:
                if heading_is_present(scannable_text, heading):
                    stale_sections.append(
                        StaleProtectedGuideSection(
                            path=obligation.path,
                            contract_key=obligation.key,
                            anchor_type="heading",
                            anchor=heading,
                            target_modules=obligation.target_modules,
                        )
                    )
            for phrase in obligation.stale_phrases:
                if phrase in scannable_text:
                    stale_sections.append(
                        StaleProtectedGuideSection(
                            path=obligation.path,
                            contract_key=obligation.key,
                            anchor_type="phrase",
                            anchor=phrase,
                            target_modules=obligation.target_modules,
                        )
                    )
            if not stale_sections:
                continue
            protected_guide_waiver = find_protected_guide_waiver(
                protected_guide_waivers,
                path=obligation.path,
                contract_key=obligation.key,
                target_modules=obligation.target_modules,
            )
            if protected_guide_waiver is not None:
                applied_protected_guide_waivers.append(protected_guide_waiver)
            else:
                stale_protected_guide_sections.extend(stale_sections)

    return InstructionContractReport(
        mode=mode,
        contracts_checked=tuple(checked_contracts),
        skipped_contracts=tuple(skipped_contracts),
        missing_files=tuple(missing_files),
        missing_anchors=tuple(missing_anchors),
        stale_protected_guide_sections=tuple(stale_protected_guide_sections),
        applied_waivers=tuple(dict.fromkeys(applied_waivers)),
        applied_protected_guide_waivers=tuple(dict.fromkeys(applied_protected_guide_waivers)),
        authorized_removals=tuple(authorized_removals),
        warnings=warnings,
    )


def print_report(report: InstructionContractReport) -> None:
    """Print a human-readable instruction contract report."""
    for warning in report.warnings:
        print(f"WARNING: {warning}")

    if report.has_failures:
        print("Instruction-contract validation failed.")
    elif report.applied_waivers or report.applied_protected_guide_waivers:
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

    if report.stale_protected_guide_sections:
        print("\nStale protected-guide sections requiring owner review:")
        for stale_section in report.stale_protected_guide_sections:
            print(
                f"  - {stale_section.path}: {stale_section.contract_key}: stale "
                f"{stale_section.anchor_type}: {stale_section.anchor} "
                f"(target modules: {', '.join(stale_section.target_modules)})"
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

    if report.applied_protected_guide_waivers:
        print("\nProtected guide contract waivers applied:")
        for protected_guide_waiver in report.applied_protected_guide_waivers:
            print(f"  - {protected_guide_waiver.path}: {protected_guide_waiver.contract_key}")
            if protected_guide_waiver.target_path is not None:
                print(f"    target_path: {protected_guide_waiver.target_path}")
            if protected_guide_waiver.target_module is not None:
                print(f"    target_module: {protected_guide_waiver.target_module}")
            if protected_guide_waiver.linked_local_override_path is not None:
                print(
                    "    linked_local_override_path: "
                    f"{protected_guide_waiver.linked_local_override_path}"
                )
            print(f"    reason: {protected_guide_waiver.reason}")
            print(f"    authorization_basis: {protected_guide_waiver.authorization_basis}")


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
        protected_guide_section_obligations = parse_protected_guide_section_obligations(
            contracts_document,
            manifest_modules,
        )
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
                protected_guide_section_obligations=protected_guide_section_obligations,
                warnings=warnings,
            )
        else:
            (
                included_modules,
                protected_decisions,
                waivers,
                protected_guide_waivers,
            ) = load_marker_for_downstream(
                marker_path,
                marker_schema_path,
                manifest_modules,
                repo_root,
            )
            report = validate_contracts(
                mode=args.mode,
                repo_root=repo_root,
                contracts=contracts,
                protected_guide_section_obligations=protected_guide_section_obligations,
                included_modules=included_modules,
                protected_decisions=protected_decisions,
                waivers=waivers,
                protected_guide_waivers=protected_guide_waivers,
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
