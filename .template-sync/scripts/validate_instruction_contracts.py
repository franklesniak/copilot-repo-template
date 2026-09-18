"""Validate required anchors and bounded policy sections in protected instruction files."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from bisect import bisect_left
from dataclasses import dataclass, replace
from itertools import pairwise
from pathlib import Path
from typing import Any, NoReturn, cast

import validate_marker
from template_sync_materialization_helpers import (
    LIST_MARKER_RE,
    MARKDOWN_FENCE_CONTEXT,
    MarkdownFence,
    active_fence_content,
    consume_blockquote_prefix,
    lines_outside_markdown_fences,
    markdown_lines,
    normalize_repository_path,
    parse_fence_close_from_content,
    parse_markdown_fence_open,
    read_repository_text,
)

DEFAULT_CONTRACTS_PATH = ".template-sync/instruction-contracts.yml"
DEFAULT_CONTRACTS_SCHEMA_PATH = "schemas/template-sync-instruction-contracts.schema.json"
VALIDATION_MODES = ("upstream-template", "downstream")
# Per-file local resource bound, independent of agent document-context settings.
MAXIMUM_INPUT_BYTES = 1024 * 1024
POLICY_CELL_WORD = (
    r"[^|\u0009-\u000d\u001c-\u0020\u0085\u00a0\u1680"
    r"\u2000-\u200a\u2028-\u2029\u202f\u205f\u3000\ufeff]"
)
# Explicit classes keep schema consumers and Python whitespace semantics equal.
POLICY_CELL_PATTERN = re.compile(rf"^{POLICY_CELL_WORD}+(?: {POLICY_CELL_WORD}+)*(?![\s\S])")
POLICY_HEADING_PATTERN = re.compile(r"^#{1,6} [^\r\n]*[^ \t\r\n](?![\s\S])")
# CommonMark 0.31.2 section 4.6. Comments retain their separate inline handling.
POLICY_HTML_LITERAL_START = re.compile(
    r"^ {0,3}<(?:pre|script|style|textarea)(?=[ \t>]|$)", re.IGNORECASE | re.ASCII
)
POLICY_HTML_LITERAL_END = re.compile(r"</(?:pre|script|style|textarea)>", re.IGNORECASE | re.ASCII)
POLICY_HTML_BLOCK_START = re.compile(
    r"^ {0,3}</?(?:address|article|aside|base|basefont|blockquote|body|caption|center|col|"
    r"colgroup|dd|details|dialog|dir|div|dl|dt|fieldset|figcaption|figure|footer|form|frame|"
    r"frameset|h[1-6]|head|header|hr|html|iframe|legend|li|link|main|menu|menuitem|nav|"
    r"noframes|ol|optgroup|option|p|param|search|section|summary|table|tbody|td|tfoot|th|"
    r"thead|title|tr|track|ul)(?=[ \t>]|/>|$)",
    re.IGNORECASE | re.ASCII,
)
POLICY_HTML_COMPLETE_TAG = re.compile(
    r"^ {0,3}(?:</[A-Za-z][A-Za-z0-9-]*[ \t]*>|"
    r"<(?![Pp][Rr][Ee](?=[ \t/>]))(?![Ss][Cc][Rr][Ii][Pp][Tt](?=[ \t/>]))"
    r"(?![Ss][Tt][Yy][Ll][Ee](?=[ \t/>]))(?![Tt][Ee][Xx][Tt][Aa][Rr][Ee][Aa](?=[ \t/>]))"
    r"[A-Za-z][A-Za-z0-9-]*(?:[ \t]+[A-Za-z_:][A-Za-z0-9_.:-]*"
    r"(?:[ \t]*=[ \t]*(?:[^ \t\"'=<>`]+|'[^']*'|\"[^\"]*\"))?)*[ \t]*/?>)[ \t]*$"
)
POLICY_HTML_BLANK_END = re.compile(r"^[ \t]*$")
POLICY_HTML_AMBIGUOUS_START = re.compile(
    r"^ {0,3}(?:<[Tt][Ee][Xx][Tt][Aa][Rr][Ee][Aa](?=[ \t>]|/>|$)|"
    r"</?(?:[Ss][Ee][Aa][Rr][Cc][Hh]|[Ss][Oo][Uu][Rr][Cc][Ee])(?=[ \t>]|/>|$)|<![a-z])"
)
POLICY_HTML_TEXTAREA_END = re.compile(r"</textarea>", re.IGNORECASE | re.ASCII)
POLICY_HTML_AMBIGUITY_PREFIX = "[unsupported HTML grammar] "


class InstructionContractValidationError(Exception):
    """Raised when instruction contract validation cannot produce a clean result."""


@dataclass(frozen=True)
class RequiredTable:
    """An exact ordered decision table in an operative Markdown section."""

    headers: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]


PolicyBlock = tuple[str, str | RequiredTable]


@dataclass(frozen=True)
class RequiredSection:
    """Complete ordered clauses and tables owned by one unique heading."""

    heading: str
    required_paragraphs: tuple[str, ...]
    required_tables: tuple[RequiredTable, ...]
    next_heading: str | None = None
    requires_modules: tuple[str, ...] = ()
    required_block_order: tuple[str, ...] = ()


@dataclass(frozen=True)
class PolicyLineIndex:
    """Positions and next-heading offsets for one operative document only."""

    positions: dict[str, list[int]]
    next_headings: list[int]


@dataclass(frozen=True)
class InstructionContract:
    """Required anchors for one protected instruction file."""

    path: str
    requires_modules: tuple[str, ...]
    required_headings: tuple[str, ...]
    required_phrases: tuple[str, ...]
    required_sections: tuple[RequiredSection, ...] = ()


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
        """Return whether validation found unwaived failures.

        A failure is any unwaived missing file, missing anchor, or stale
        protected-guide section.
        """
        return bool(
            self.missing_files or self.missing_anchors or self.stale_protected_guide_sections
        )


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Validate required headings, phrases, and bounded policy sections in protected instruction files "
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
    document = validate_marker.load_yaml_mapping(
        document_path, repo_root, maximum_bytes=MAXIMUM_INPUT_BYTES
    )
    schema = validate_marker.load_json_mapping(
        schema_path, repo_root, maximum_bytes=MAXIMUM_INPUT_BYTES
    )
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


def normalize_policy_paragraph(text: str) -> str:
    """Fold supported ASCII wrapping while retaining other literal characters."""
    return re.sub(r"[ \t\r\n]+", " ", text).strip(" ")


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


def parse_required_sections(raw_contract: dict[str, object]) -> tuple[RequiredSection, ...]:
    """Reject ambiguous normalized paragraphs and table shapes in section contracts."""
    sections: list[RequiredSection] = []
    headings: set[str] = set()
    successor_owners: dict[str | None, str] = {}
    for raw in cast(list[dict[str, Any]], raw_contract.get("required_sections", [])):
        heading = cast(str, raw["heading"])
        next_heading = cast(str | None, raw["next_heading"])
        for field, value in (("heading", heading), ("next_heading", next_heading)):
            if (value is None and field == "heading") or (
                value is not None and POLICY_HEADING_PATTERN.fullmatch(value) is None
            ):
                raise InstructionContractValidationError(
                    f"Noncanonical contract {field}: {value!r}"
                )
        if heading in headings:
            raise InstructionContractValidationError(f"Duplicate required section: {heading}")
        headings.add(heading)
        if next_heading == heading:
            raise InstructionContractValidationError(f"Self-successor section: {heading}")
        if next_heading in successor_owners:
            raise InstructionContractValidationError(
                f"Shared section successor {next_heading!r}: "
                f"{successor_owners[next_heading]} and {heading}"
            )
        successor_owners[next_heading] = heading
        requires_modules = _required_string_list(raw, "requires_modules")
        if "requires_modules" in raw and (
            not requires_modules or len(set(requires_modules)) != len(requires_modules)
        ):
            raise InstructionContractValidationError(
                f"Section requires_modules must be nonempty and unique: {heading}"
            )
        paragraphs = _required_string_list(raw, "required_paragraphs")
        normalized_paragraphs = [normalize_policy_paragraph(value) for value in paragraphs]
        if any(not value or value.isspace() for value in normalized_paragraphs):
            raise InstructionContractValidationError(
                f"Empty normalized contract paragraph: {heading}"
            )
        if len(set(normalized_paragraphs)) != len(normalized_paragraphs):
            raise InstructionContractValidationError(
                f"Duplicate normalized contract paragraph: {heading}"
            )
        tables: list[RequiredTable] = []
        for table in cast(list[dict[str, Any]], raw.get("required_tables", [])):
            headers = tuple(cast(list[str], table["headers"]))
            rows = tuple(tuple(row) for row in cast(list[list[str]], table["rows"]))
            if any(
                POLICY_CELL_PATTERN.fullmatch(cell) is None
                for row in (headers, *rows)
                for cell in row
            ):
                raise InstructionContractValidationError(
                    f"Noncanonical contract table cell: {heading}"
                )
            if any(len(row) != len(headers) for row in rows):
                raise InstructionContractValidationError(f"Ragged contract table: {heading}")
            if len({row[0] for row in rows}) != len(rows):
                raise InstructionContractValidationError(f"Duplicate table condition: {heading}")
            tables.append(RequiredTable(headers, rows))
        if len(set(tables)) != len(tables):
            raise InstructionContractValidationError(f"Duplicate contract table: {heading}")
        block_order = _required_string_list(raw, "required_block_order")
        if "required_block_order" in raw and (
            any(kind not in {"paragraph", "table"} for kind in block_order)
            or block_order.count("paragraph") != len(paragraphs)
            or block_order.count("table") != len(tables)
        ):
            raise InstructionContractValidationError(
                f"Block order must match paragraph and table counts: {heading}"
            )
        sections.append(
            RequiredSection(
                heading,
                paragraphs,
                tuple(tables),
                next_heading,
                requires_modules,
                block_order,
            )
        )
    successors = {section.heading: section.next_heading for section in sections}
    completed: set[str] = set()
    for section in sections:
        visited: set[str] = set()
        successor: str | None = section.heading
        while successor in successors and successor not in completed:
            assert successor is not None
            if successor in visited:
                raise InstructionContractValidationError(
                    f"Cyclic section successor chain: {section.heading}"
                )
            visited.add(successor)
            successor = successors[successor]
        completed.update(visited)
    return tuple(sections)


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
        path, is_directory = normalize_repository_path(
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
        required_sections = parse_required_sections(raw_contract)
        for section in required_sections:
            unknown_section_modules = set(section.requires_modules) - manifest_modules
            if unknown_section_modules:
                raise InstructionContractValidationError(
                    f"{path}: {section.heading} references unknown manifest module(s): "
                    + ", ".join(sorted(unknown_section_modules))
                )
        if not required_headings and not required_phrases and not required_sections:
            raise InstructionContractValidationError(
                f"{path} must define at least one required heading, phrase, or section."
            )

        contracts.append(
            InstructionContract(
                path=path,
                requires_modules=requires_modules,
                required_headings=required_headings,
                required_phrases=required_phrases,
                required_sections=required_sections,
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
        path, is_directory = normalize_repository_path(
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
        path, is_directory = normalize_repository_path(
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
            target_path, target_is_directory = normalize_repository_path(
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
        path, is_directory = normalize_repository_path(
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
    return read_repository_text(path, repo_root, maximum_bytes=MAXIMUM_INPUT_BYTES)


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
    for line in markdown_lines(text):
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
        if line[leading_spaces:].rstrip(" \t") == heading:
            return True
    return False


def is_policy_heading(line: str) -> bool:
    """Recognize live ATX boundaries, including an empty heading or a tab separator."""
    return re.match(r"^ {0,3}#{1,6}(?:[ \t]|$)", line) is not None


def is_policy_thematic_break(line: str) -> bool:
    """Recognize a thematic break without promoting four-space paragraph content."""
    return (
        re.fullmatch(r" {0,3}(?:(?:\*[ \t]*){3,}|(?:-[ \t]*){3,}|(?:_[ \t]*){3,})", line)
        is not None
    )


def starts_policy_list(line: str) -> bool:
    """Recognize a list outside a quote, including empty items and arbitrary starts."""
    return re.match(r"^ {0,3}(?:[-+*]|[0-9]{1,9}[.)])(?:[ \t]|$)", line) is not None


def policy_list_content_indent(line: str) -> int | None:
    """Return a top-level item's content margin, including empty/tabbed items.

    Padding beyond four columns starts item code and uses a one-column margin.
    The scanner retains potential nested content; it does not parse that code.
    """
    expanded = line.expandtabs(4)
    marker = re.match(r"^ {0,3}(?:[-+*]|[0-9]{1,9}[.)])(?= |$)", expanded)
    if marker is None or is_policy_thematic_break(line):
        return None
    rest = expanded[marker.end() :]
    padding = len(rest) - len(rest.lstrip(" "))
    return marker.end() + (padding if rest.strip(" \t") and 1 <= padding <= 4 else 1)


def quoted_policy_paragraph(line: str, was_paragraph: bool) -> bool | None:
    """Classify a quoted leaf; None means unsupported syntax must fail closed.

    Paragraphs and simple list paragraphs can continue lazily. Structural leaves
    cannot. Ambiguous HTML, table, or mixed nested containers are not guessed.
    """
    _depth, source_offset = consume_blockquote_prefix(line)
    source_content = line[source_offset:]
    prefix = re.match(r"[ \t]*(?:[-+*]|[0-9]{1,9}[.)])?[ \t]*", source_content)
    assert prefix is not None
    if "\t" in prefix.group():
        # Nested container tab columns need a full block parser. Keep the
        # original ambiguous region visible instead of guessing laziness.
        return None
    expanded = line.expandtabs(4)
    _depth, offset = consume_blockquote_prefix(expanded)
    content = expanded[offset:]
    if is_policy_thematic_break(content):
        return False
    item = LIST_MARKER_RE.match(content)
    if item is not None:
        if item.group("rest").startswith(" "):
            # More than four padding columns begin item code, not a paragraph.
            return False
        content = item.group("rest")
        if consume_blockquote_prefix(content)[0] or starts_policy_list(content):
            return None
        was_paragraph = False
    elif starts_policy_list(content):
        return False if re.fullmatch(r" {0,3}(?:[-+*]|[0-9]{1,9}[.)])[ \t]*", content) else None
    if not content.strip(" \t") or is_policy_heading(content) or is_policy_thematic_break(content):
        return False
    if re.match(r"^(?: {4}| *\t)", content):
        return was_paragraph
    if was_paragraph and re.fullmatch(r" {0,3}(?:=+|-+)[ \t]*", content):
        return False
    if not was_paragraph and content.lstrip(" ").startswith("["):
        # A reference definition can span lines and cannot establish laziness.
        # Keep ambiguous new leaves visible instead of guessing their grammar.
        return None
    if content.lstrip(" ").startswith("<") or "|" in content:
        return None
    return True


def policy_code_span_ends(lines: list[str]) -> dict[tuple[int, int], tuple[int, int]]:
    """Index nearest equal-width backtick runs without rescanning paragraph tails.

    Each line and run is visited once in reverse order. Block starts prevent
    earlier paragraphs from consuming their delimiters; same-line spans remain
    supported. Unmatched runs have no entry and remain literal in the scanner.
    """
    ends: dict[tuple[int, int], tuple[int, int]] = {}
    next_runs: dict[int, tuple[int, int]] = {}
    for row in range(len(lines) - 1, -1, -1):
        line = lines[row]
        for run in reversed(list(re.finditer(r"`+", line))):
            width = run.end() - run.start()
            if width in next_runs:
                ends[(row, run.start())] = next_runs[width]
            # An escaped first backtick leaves the remaining run as an opener.
            # Inside a span, however, only the whole raw run can close it.
            if width > 1 and width - 1 in next_runs:
                ends[(row, run.start() + 1)] = next_runs[width - 1]
            next_runs[width] = (row, run.end())
        if (
            not line.strip(" \t")
            or re.match(
                r"^(?: {4}| *\t| {0,3}(?:>|#{1,6}(?:[ \t]|$)|<!--|[-+*] |[0-9]+[.)] ))", line
            )
            or parse_markdown_fence_open(line, MARKDOWN_FENCE_CONTEXT) is not None
            or policy_html_block_end(line, paragraph_can_continue=True) is not None
            or POLICY_HTML_AMBIGUOUS_START.match(line) is not None
        ):
            next_runs.clear()
    return ends


def policy_html_block_end(line: str, *, paragraph_can_continue: bool) -> re.Pattern[str] | None:
    """Return a non-comment HTML block's end condition, or None for live text.

    Literal tags, processing instructions, declarations and CDATA use explicit
    terminators. Block tags and standalone complete tags end at a blank line.
    Only the standalone complete-tag family cannot interrupt a paragraph.
    """
    if POLICY_HTML_LITERAL_START.match(line):
        return POLICY_HTML_LITERAL_END
    if re.match(r"^ {0,3}<\?", line):
        return re.compile(r"\?>")
    if re.match(r"^ {0,3}<![A-Za-z]", line):
        return re.compile(r">")
    if re.match(r"^ {0,3}<!\[CDATA\[", line):
        return re.compile(r"\]\]>")
    if POLICY_HTML_BLOCK_START.match(line) or (
        not paragraph_can_continue and POLICY_HTML_COMPLETE_TAG.fullmatch(line)
    ):
        return POLICY_HTML_BLANK_END
    return None


def operative_markdown_lines(text: str) -> list[str]:
    """Read the deliberately narrow live policy subset, preserving block boundaries.

    Section contracts accept top-level ATX headings, paragraphs/list items, and
    pipe tables. Fences, block quotes, indented code, and raw HTML blocks cannot
    supply an obligation. Existing loose heading/phrase contracts keep their
    compatibility behavior. This is a static policy guard, not an agent runner.
    """
    lines = markdown_lines(text)
    span_ends = policy_code_span_ends(lines)
    backtick_run = re.compile(r"`+")
    result: list[str] = []
    quoted_paragraph_can_continue = False
    quoted_paragraph_depth = 0
    unsupported_quote = False
    paragraph_can_continue = False
    list_content_indent: int | None = None
    in_comment = False
    active_fence: MarkdownFence | None = None
    active_html_end: re.Pattern[str] | None = None
    code_end: tuple[int, int] | None = None
    for row, line in enumerate(lines):
        continued_comment = in_comment
        if active_html_end is not None:
            if active_html_end is POLICY_HTML_LITERAL_END and POLICY_HTML_TEXTAREA_END.search(line):
                result.append(POLICY_HTML_AMBIGUITY_PREFIX + line)
            if active_html_end.search(line):
                active_html_end = None
            result.append("")
            continue
        if active_fence is not None:
            content = active_fence_content(line, active_fence)
            if content is not None:
                if parse_fence_close_from_content(
                    content,
                    fence_character=active_fence.character,
                    minimum_length=active_fence.length,
                    allow_arbitrary_indent=active_fence.allow_arbitrary_indent,
                ):
                    active_fence = None
                result.append("")
                continue
            active_fence = None
        if not in_comment and code_end is None:
            if POLICY_HTML_AMBIGUOUS_START.match(line):
                # These starts differ between CommonMark 0.31.2 and GFM 0.29.
                # Keep document-level uncertainty visible even outside a section.
                result.append(POLICY_HTML_AMBIGUITY_PREFIX + line)
            expanded = line.expandtabs(4)
            indent = len(expanded) - len(expanded.lstrip(" "))
            quote_depth, quote_offset = consume_blockquote_prefix(expanded)
            quote_content = expanded[quote_offset:]
            if (
                quoted_paragraph_can_continue
                and max(quoted_paragraph_depth, quote_depth) > 1
                and quote_depth != quoted_paragraph_depth
                and quote_content.strip(" ")
                and len(quote_content) - len(quote_content.lstrip(" ")) >= 4
            ):
                # Omitted or changed nested containers can expose an indented
                # block and later live text. Do not guess paragraph laziness.
                unsupported_quote = True
                quoted_paragraph_can_continue = False
                result.append("[unsupported quoted policy] " + line)
                continue
            html_end = policy_html_block_end(
                line,
                paragraph_can_continue=(paragraph_can_continue or quoted_paragraph_can_continue),
            )
            ordered = re.match(r"^ {0,3}([0-9]{1,9})[.)](?:[ \t]|$)", line)
            if (
                paragraph_can_continue
                and list_content_indent is None
                and ordered is not None
                and int(ordered.group(1)) != 1
            ):
                # A non-1 start cannot interrupt a direct paragraph. Do not
                # let a stateless fence parser hide this live continuation.
                result.append("[unsupported ordered continuation] " + line)
                continue
            outside_block = (
                is_policy_heading(line)
                or starts_policy_list(line)
                or is_policy_thematic_break(line)
                or consume_blockquote_prefix(line)[0] > 0
                or re.match(r"^ {0,3}<!--", line) is not None
                or html_end is not None
                or parse_markdown_fence_open(line, MARKDOWN_FENCE_CONTEXT) is not None
            )
            if line.strip(" \t") and list_content_indent is not None:
                if indent >= list_content_indent and (
                    indent >= 4
                    or is_policy_heading(line)
                    or consume_blockquote_prefix(line)[0]
                    or re.match(r"^ {0,3}<!--", line)
                    or html_end is not None
                    or parse_markdown_fence_open(line, MARKDOWN_FENCE_CONTEXT) is not None
                ):
                    result.append("[unsupported nested policy] " + line)
                    continue
                if indent < list_content_indent and (not paragraph_can_continue or outside_block):
                    list_content_indent = None
            if not line.strip(" \t") or outside_block:
                paragraph_can_continue = False
            if not line.strip(" \t") or is_policy_heading(line):
                quoted_paragraph_can_continue = False
                unsupported_quote = False
            if html_end is not None:
                # An unquoted interrupting block ends the preceding quote;
                # its contents must not become live at a later heading.
                quoted_paragraph_can_continue = False
                unsupported_quote = False
            if unsupported_quote:
                # Preserve the entire ambiguous region in the failure identity;
                # none of its lines can masquerade as a required live clause.
                result.append("[unsupported quoted policy] " + line)
                continue
            if not consume_blockquote_prefix(line)[0]:
                item_indent = policy_list_content_indent(line)
                if item_indent is not None and (
                    list_content_indent is None or indent < list_content_indent
                ):
                    list_content_indent = item_indent
                if re.match(r"^ {0,3}(?:[-+*]|[0-9]{1,9}[.)]) {5,}[^ ]", expanded):
                    # More than four visual padding columns begin item code.
                    # Preserve its source instead of normalizing it into policy.
                    paragraph_can_continue = False
                    result.append("[unsupported list code] " + line)
                    continue
            active_fence = parse_markdown_fence_open(line, MARKDOWN_FENCE_CONTEXT)
            if active_fence is not None:
                quoted_paragraph_can_continue = False
                result.append("")
                continue
            if consume_blockquote_prefix(line)[0]:
                if not quoted_paragraph_can_continue:
                    quoted_paragraph_depth = 0
                leaf = quoted_policy_paragraph(line, quoted_paragraph_can_continue)
                unsupported_quote = leaf is None
                quoted_paragraph_can_continue = leaf is True
                if quoted_paragraph_can_continue:
                    quoted_paragraph_depth = max(quoted_paragraph_depth, quote_depth)
                else:
                    quoted_paragraph_depth = 0
                result.append("[unsupported quoted policy] " + line if unsupported_quote else "")
                continue
            if quoted_paragraph_can_continue:
                if (
                    starts_policy_list(line)
                    or is_policy_thematic_break(line)
                    or re.match(r"^ {0,3}<!--", line)
                ):
                    quoted_paragraph_can_continue = False
                elif re.match(r"^ {0,3}<", line) or "|" in line:
                    unsupported_quote = True
                    quoted_paragraph_can_continue = False
                    result.append("[unsupported quoted policy] " + line)
                    continue
                else:
                    result.append("")
                    continue
            if re.match(r"^(?: {4}| *\t)", line):
                result.append(
                    "[unsupported indented policy] " + line if paragraph_can_continue else ""
                )
                continue
            if html_end is not None:
                # A block start wins over inline delimiters on this whole line.
                if html_end is POLICY_HTML_LITERAL_END and POLICY_HTML_TEXTAREA_END.search(line):
                    result.append(POLICY_HTML_AMBIGUITY_PREFIX + line)
                active_html_end = None if html_end.search(line) else html_end
                paragraph_can_continue = False
                quoted_paragraph_can_continue = False
                list_content_indent = None
                result.append("")
                continue
        visible: list[str] = []
        elided_comment = in_comment
        column = 0
        while column < len(line):
            if code_end is not None:
                if row < code_end[0]:
                    visible.append(line[column:])
                    break
                visible.append(line[column : code_end[1]])
                column = code_end[1]
                code_end = None
            elif in_comment:
                end = line.find("-->", column)
                if end == -1:
                    break
                column = end + 3
                in_comment = False
                if line[column:].strip(" \t"):
                    visible.append("[unsupported comment tail] " + line)
                    break
            elif line[column] == "\\" and column + 1 < len(line):
                # Escaped delimiters are literal, including escaped backticks.
                visible.append(line[column : column + 2])
                column += 2
            elif line[column] == "`":
                run = backtick_run.match(line, column)
                assert run is not None
                width = len(run.group())
                code_end = span_ends.get((row, column))
                if code_end is None:
                    visible.append(run.group())
                    column += width
            elif line.startswith("<!--", column):
                end = line.find("-->", column + 2)
                block_comment = column <= 3 and not line[:column].strip(" ")
                if end == -1 and not block_comment:
                    # Inline comments need a complete delimiter. Wrapped forms
                    # are outside this subset and must never hide later policy.
                    visible.append("[unsupported inline comment] " + line[column:])
                    break
                comment_content = line[column + 4 : end]
                ambiguous_inline = end < column + 4 or (
                    comment_content.startswith((">", "->"))
                    or comment_content.endswith("-")
                    or "--" in comment_content
                )
                if end != -1 and not block_comment and ambiguous_inline:
                    # Use the shared CommonMark/GFM grammar. Renderer-specific
                    # inline forms must not hide a potentially visible clause.
                    visible.append("[unsupported inline comment] " + line[column:])
                    break
                if block_comment and end != -1 and line[end + 3 :].strip(" \t"):
                    visible.append("[unsupported comment tail] " + line)
                    break
                elided_comment = True
                if not block_comment and end != -1:
                    # A comment is an inline token boundary, not removable
                    # source text. Keep it before paragraph normalization so
                    # deleting it cannot synthesize links or other markup.
                    visible.append(line[column : end + 3])
                    column = end + 3
                    continue
                in_comment = end == -1
                column = column + 4 if in_comment else end + 3
            else:
                visible.append(line[column])
                column += 1
        observed = "".join(visible).strip(" \t")
        trailing_spaces = re.search(r" {2,}$", line)
        if (
            observed
            and trailing_spaces is not None
            and code_end is None
            and not in_comment
            and not is_policy_heading(line)
            and not observed.startswith("|")
        ):
            # Keep physical endings until the paragraph parser can distinguish
            # a hard break from harmless block-final padding.
            observed += trailing_spaces.group()
        if elided_comment and (
            (is_policy_heading(observed) and not is_policy_heading(line))
            or (starts_policy_list(observed) and not starts_policy_list(line))
            or observed.startswith("|")
        ):
            observed = "[unsupported comment structure] " + line
        result.append(observed)
        if observed:
            paragraph_can_continue = not (
                is_policy_heading(line)
                or is_policy_thematic_break(line)
                or observed.startswith("|")
                or re.match(r"^ {0,3}<!--", line)
                or re.fullmatch(r"(?:[-+*]|[0-9]{1,9}[.)])[ \t]*", observed)
            )
        elif not continued_comment and not in_comment:
            paragraph_can_continue = False
    return result


def index_policy_lines(lines: list[str]) -> PolicyLineIndex:
    """Index exact line occurrences and inclusive next-heading offsets once."""
    positions: dict[str, list[int]] = {}
    next_headings = [len(lines)] * (len(lines) + 1)
    for offset in range(len(lines) - 1, -1, -1):
        line = lines[offset]
        positions.setdefault(line, []).append(offset)
        next_headings[offset] = offset if is_policy_heading(line) else next_headings[offset + 1]
    for offsets in positions.values():
        offsets.reverse()
    return PolicyLineIndex(positions, next_headings)


def section_body(
    lines: list[str], heading: str, index: PolicyLineIndex | None = None
) -> list[str] | None:
    """Return one unique heading's direct body, ending at the next ATX heading."""
    if index is None:
        index = index_policy_lines(lines)
    matches = index.positions.get(heading, [])
    if len(matches) != 1:
        return None
    start = matches[0] + 1
    return lines[start : index.next_headings[start]]


def policy_inventory_digest(expected: object, observed: object) -> str:
    """Bind a waiver to both the expected contract and its observed deviation."""
    return hashlib.sha256(
        json.dumps([expected, observed], ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def section_boundary_failure(
    lines: list[str], section: RequiredSection, index: PolicyLineIndex | None = None
) -> str | None:
    """Reject unknown section boundaries without claiming ownership beyond the declared end.

    Non-null successors must be unique. The mismatch identity includes all live
    content up to the declared successor (or EOF), so waiving one added heading
    cannot silently authorize changed content below that heading.
    """
    if index is None:
        index = index_policy_lines(lines)
    starts = index.positions.get(section.heading, [])
    start = starts[0] + 1 if len(starts) == 1 else 0
    successors = (
        index.positions.get(section.next_heading, []) if section.next_heading is not None else []
    )
    next_offset = index.next_headings[start]
    actual_next = lines[next_offset] if next_offset < len(lines) else None
    unique_successor = len(starts) == 1 and (
        section.next_heading is None or (len(successors) == 1 and successors[0] >= start)
    )
    if actual_next != section.next_heading or not unique_successor:
        end = successors[0] if len(successors) == 1 and successors[0] >= start else len(lines)
        observed = [normalize_policy_paragraph(line) for line in lines[start:end] if line]
        identity = policy_inventory_digest(
            section.next_heading, [actual_next, len(successors), observed]
        )
        return f"section:{section.heading}:boundary:{identity}"
    return None


def parse_policy_body(
    lines: list[str],
    *,
    blocks: list[PolicyBlock] | None = None,
    hard_breaks: list[str] | None = None,
) -> tuple[list[str], list[RequiredTable]]:
    """Parse full paragraph/list-item clauses and strict, unescaped pipe tables.

    Inline pipes and multiline table cells are outside this policy subset.
    Malformed tables raise rather than quietly dropping decision rows.
    """
    paragraphs: list[str] = []
    tables: list[RequiredTable] = []
    paragraph: list[str] = []

    def finish_paragraph() -> None:
        if not paragraph:
            return
        value = normalize_policy_paragraph(" ".join(paragraph))
        paragraphs.append(value)
        if blocks is not None:
            blocks.append(("paragraph", value))
        if hard_breaks is not None and any(
            line.endswith("  ")
            and not is_policy_thematic_break(line)
            and not is_policy_thematic_break(following)
            for line, following in pairwise(paragraph)
        ):
            hard_breaks.append("\n".join(paragraph))
        paragraph.clear()

    index = 0
    while index < len(lines):
        line = lines[index]
        boundary = (
            not line or is_policy_heading(line) or line.startswith("|") or starts_policy_list(line)
        )
        if boundary and paragraph:
            finish_paragraph()
        if line.startswith("|"):
            cells: list[tuple[str, ...]] = []
            while index < len(lines) and lines[index].startswith("|"):
                row = lines[index]
                if not row.endswith("|") or "\\|" in row:
                    raise InstructionContractValidationError("Malformed policy table row.")
                row_cells = tuple(cell.strip(" \t") for cell in row[1:-1].split("|"))
                if any(POLICY_CELL_PATTERN.fullmatch(cell) is None for cell in row_cells):
                    raise InstructionContractValidationError("Noncanonical observed policy cell.")
                cells.append(row_cells)
                index += 1
            if (
                len(cells) < 3
                or len(cells[0]) < 2
                or any(len(row) != len(cells[0]) for row in cells)
                or any(not re.fullmatch(r":?-{3,}:?", cell) for cell in cells[1])
                or any(not cell for row in (cells[0], *cells[2:]) for cell in row)
                or len({row[0] for row in cells[2:]}) != len(cells[2:])
            ):
                raise InstructionContractValidationError("Malformed or duplicate policy table.")
            table = RequiredTable(cells[0], tuple(cells[2:]))
            tables.append(table)
            if blocks is not None:
                blocks.append(("table", table))
            continue
        if line and not is_policy_heading(line):
            paragraph.append(line)
        index += 1
    finish_paragraph()
    return paragraphs, tables


def expected_policy_blocks(section: RequiredSection) -> list[PolicyBlock]:
    """Expand explicit or default interleaving without duplicating clause content."""
    order = section.required_block_order or (
        ("paragraph",) * len(section.required_paragraphs)
        + ("table",) * len(section.required_tables)
    )
    paragraphs = iter(normalize_policy_paragraph(value) for value in section.required_paragraphs)
    tables = iter(section.required_tables)
    return [(kind, next(paragraphs) if kind == "paragraph" else next(tables)) for kind in order]


def serialized_policy_blocks(blocks: list[PolicyBlock]) -> list[object]:
    """Keep typed source inventories serializable in content-bound waiver identities."""
    return [
        [kind, value.headers, value.rows] if isinstance(value, RequiredTable) else [kind, value]
        for kind, value in blocks
    ]


def section_applies(section: RequiredSection, included_modules: set[str] | None) -> bool:
    """Apply all sections upstream and only retained section module sets downstream."""
    return included_modules is None or set(section.requires_modules).issubset(included_modules)


def applicable_section_boundary(
    section: RequiredSection,
    sections: dict[str, RequiredSection],
    live_lines: set[str],
    included_modules: set[str] | None,
    cache: dict[str, str | None] | None = None,
) -> RequiredSection:
    """Skip only absent, inapplicable declared successors in an acyclic catalog.

    A present optional heading remains the exact boundary, including when the
    separate protected-guide checks require an explicit stale-section waiver.
    Applicable or uncontracted successors cannot be skipped.
    """
    successor = section.next_heading
    if cache is None:
        cache = {}
    skipped: list[str] = []
    while successor in sections and successor not in live_lines:
        assert successor is not None
        if successor in cache:
            successor = cache[successor]
            break
        following = sections[successor]
        if section_applies(following, included_modules):
            break
        skipped.append(successor)
        successor = following.next_heading
    for heading in skipped:
        cache[heading] = successor
    return replace(section, next_heading=successor)


def section_failures(
    text: str,
    sections: tuple[RequiredSection, ...],
    included_modules: set[str] | None = None,
) -> list[str]:
    """Return stable, individually waivable failures for scoped policy contracts."""
    failures: list[str] = []
    lines = operative_markdown_lines(text)
    ambiguous_html = [line for line in lines if line.startswith(POLICY_HTML_AMBIGUITY_PREFIX)]
    document_identity = hashlib.sha256(text.encode("utf-8")).hexdigest() if ambiguous_html else ""
    sections_by_heading = {section.heading: section for section in sections}
    live_lines = set(lines)
    line_index = index_policy_lines(lines)
    successor_cache: dict[str, str | None] = {}
    for section in sections:
        if not section_applies(section, included_modules):
            continue
        prefix = f"section:{section.heading}"
        expected_blocks = expected_policy_blocks(section)
        if ambiguous_html:
            expected_section = (
                section.heading,
                section.next_heading,
                section.required_paragraphs,
                [(table.headers, table.rows) for table in section.required_tables],
                section.required_block_order,
            )
            identity = policy_inventory_digest(
                expected_section, [ambiguous_html, document_identity]
            )
            failures.append(f"{prefix}:html-grammar:{identity}")
        boundary = applicable_section_boundary(
            section, sections_by_heading, live_lines, included_modules, successor_cache
        )
        boundary_failure = section_boundary_failure(lines, boundary, line_index)
        if boundary_failure is not None:
            failures.append(boundary_failure)
        body = section_body(lines, section.heading, line_index)
        if body is None:
            failures.append(prefix)
            body = []
        hard_breaks: list[str] = []
        paragraphs, _ = parse_policy_body(
            ["" if line.startswith("|") else line for line in body],
            hard_breaks=hard_breaks,
        )
        if hard_breaks:
            identity = policy_inventory_digest(
                serialized_policy_blocks(expected_blocks), hard_breaks
            )
            failures.append(f"{prefix}:hard-break:{identity}")
        malformed = False
        observed_blocks: list[PolicyBlock] = []
        observed_tables: object
        try:
            _, tables = parse_policy_body(body, blocks=observed_blocks)
        except InstructionContractValidationError:
            malformed = True
            tables = []
            observed_tables = {
                "malformed": [line for line in body if line.startswith("|")],
                "body": body,
            }
        else:
            observed_tables = {
                "parsed": [(table.headers, table.rows) for table in tables],
                "blocks": serialized_policy_blocks(observed_blocks),
            }
        table_identity = policy_inventory_digest(
            serialized_policy_blocks(expected_blocks), observed_tables
        )
        table_anchor = f"{prefix}:tables:{table_identity}"
        # Ordered, complete paragraphs prevent scattered keywords or reordered
        # decision steps from substituting for the operative contract.
        cursor = 0
        paragraph_offsets: dict[str, list[int]] = {}
        for offset, paragraph in enumerate(paragraphs):
            paragraph_offsets.setdefault(paragraph, []).append(offset)
        for paragraph in section.required_paragraphs:
            expected = normalize_policy_paragraph(paragraph)
            offsets = paragraph_offsets.get(expected, [])
            offset_index = bisect_left(offsets, cursor)
            if offset_index < len(offsets):
                cursor = offsets[offset_index] + 1
            else:
                identity = hashlib.sha256(expected.encode("utf-8")).hexdigest()
                failures.append(f"{prefix}:paragraph:{identity}")
        expected_paragraphs = [
            normalize_policy_paragraph(value) for value in section.required_paragraphs
        ]
        expected_positions: dict[str, int] = {}
        for offset, value in enumerate(expected_paragraphs):
            expected_positions.setdefault(value, offset)
        positions = [
            expected_positions[value] for value in paragraphs if value in expected_positions
        ]
        if any(value not in expected_positions for value in paragraphs) or positions != sorted(
            set(positions)
        ):
            identity = policy_inventory_digest(
                serialized_policy_blocks(expected_blocks), observed_tables
            )
            failures.append(f"{prefix}:paragraphs:{identity}")
        if malformed or tables != list(section.required_tables):
            failures.append(table_anchor)
        if section.required_paragraphs and section.required_tables and not malformed:
            expected_ranks = {block: offset for offset, block in enumerate(expected_blocks)}
            observed_ranks = [
                expected_ranks[block] for block in observed_blocks if block in expected_ranks
            ]
            if observed_ranks != sorted(observed_ranks):
                identity = policy_inventory_digest(
                    serialized_policy_blocks(expected_blocks),
                    serialized_policy_blocks(observed_blocks),
                )
                failures.append(f"{prefix}:blocks:{identity}")
    return list(dict.fromkeys(failures))


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

        for anchor in section_failures(text, contract.required_sections, included_modules):
            waiver = find_waiver(waivers, contract.path, anchor)
            if waiver is not None:
                applied_waivers.append(waiver)
            else:
                missing_anchors.append(MissingAnchor(contract.path, "section content", anchor))

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
                    (
                        "--mode upstream-template was invoked while "
                        f"{marker_relative_path} is present; use --mode downstream for "
                        "marker-gated downstream validation."
                    ),
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
