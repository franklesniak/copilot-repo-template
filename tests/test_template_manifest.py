"""Validate the template sync manifest contract and documentation mirror."""

from __future__ import annotations

import json
import os
import re
from collections import Counter
from pathlib import Path
from typing import Any

import jsonschema
import yaml  # type: ignore[import-untyped]

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / ".template-sync" / "manifest.yml"
MANIFEST_SCHEMA_PATH = REPO_ROOT / "schemas" / "template-sync-manifest.schema.json"
MARKER_SCHEMA_PATH = REPO_ROOT / "schemas" / "template-sync-marker.schema.json"
PROCEDURE_PATH = REPO_ROOT / "TEMPLATE_UPDATE_PROCEDURE.md"
COPY_READY_REFERENCE_ROOTS = (
    REPO_ROOT / "schemas",
    REPO_ROOT / "templates" / "json",
    REPO_ROOT / "templates" / "python",
    REPO_ROOT / "templates" / "yaml",
)
COPY_READY_REFERENCE_FILES = (
    REPO_ROOT / ".github" / "instructions" / "docs.instructions.md",
    REPO_ROOT / ".github" / "instructions" / "json.instructions.md",
    REPO_ROOT / ".github" / "instructions" / "yaml.instructions.md",
)
REFERENCE_FILE_SUFFIXES = {".json", ".md", ".yaml", ".yml"}
ONBOARDING_ONLY_REFERENCE_TOKENS = (
    "OPTIONAL_CONFIGURATIONS.md",
    "GETTING_STARTED_NEW_REPO.md",
    "GETTING_STARTED_EXISTING_REPO.md",
    "TEMPLATE_MAINTENANCE.md",
    "TEMPLATE_DESIGN_DECISIONS.md",
)
UPSTREAM_ONBOARDING_URL_RE = re.compile(
    r"https://github\.com/franklesniak/copilot-repo-template/blob/HEAD/"
    r"(?:OPTIONAL_CONFIGURATIONS\.md|GETTING_STARTED_NEW_REPO\.md|"
    r"GETTING_STARTED_EXISTING_REPO\.md|TEMPLATE_MAINTENANCE\.md|"
    r"\.github/TEMPLATE_DESIGN_DECISIONS\.md)(?:#[A-Za-z0-9._-]+)?"
)


def _load_manifest() -> dict[str, Any]:
    """Parse the manifest and return its top-level object."""
    with MANIFEST_PATH.open(encoding="utf-8") as manifest_file:
        parsed_manifest = yaml.safe_load(manifest_file)
    assert isinstance(parsed_manifest, dict), "manifest root must be a mapping"
    return parsed_manifest


def _template_manifest() -> dict[str, Any]:
    """Return the nested ``template_manifest`` object."""
    template_manifest = _load_manifest().get("template_manifest")
    assert isinstance(template_manifest, dict), "template_manifest must be a mapping"
    return template_manifest


def _load_manifest_schema() -> dict[str, Any]:
    """Parse the JSON Schema for the manifest."""
    schema = json.loads(MANIFEST_SCHEMA_PATH.read_text(encoding="utf-8"))
    assert isinstance(schema, dict), "manifest schema root must be a mapping"
    return schema


def _load_marker_schema() -> dict[str, Any]:
    """Parse the JSON Schema for the downstream sync marker."""
    schema = json.loads(MARKER_SCHEMA_PATH.read_text(encoding="utf-8"))
    assert isinstance(schema, dict), "marker schema root must be a mapping"
    return schema


def _module_rows_from_manifest() -> list[tuple[str, str]]:
    """Return ``(module_name, description)`` rows from the manifest."""
    modules = _template_manifest().get("modules")
    assert isinstance(modules, list), "modules must be a list"

    rows: list[tuple[str, str]] = []
    for module in modules:
        assert isinstance(module, dict), "each module must be a mapping"
        name = module.get("name")
        description = module.get("description")
        assert isinstance(name, str), "module name must be a string"
        assert isinstance(description, str), f"module {name} description must be a string"
        rows.append((name, description))
    return rows


def _path_mapping_rows_from_manifest() -> list[tuple[str, tuple[str, ...]]]:
    """Return ``(pattern, requires_all)`` rows from the manifest."""
    path_mappings = _template_manifest().get("path_mappings")
    assert isinstance(path_mappings, list), "path_mappings must be a list"

    rows: list[tuple[str, tuple[str, ...]]] = []
    for mapping in path_mappings:
        assert isinstance(mapping, dict), "each path mapping must be a mapping"
        pattern = mapping.get("pattern")
        requires_all = mapping.get("requires_all")
        assert isinstance(pattern, str), "path mapping pattern must be a string"
        assert isinstance(requires_all, list), f"{pattern} requires_all must be a list"
        assert all(
            isinstance(module, str) for module in requires_all
        ), f"{pattern} requires_all values must be strings"
        rows.append((pattern, tuple(requires_all)))
    return rows


def _extract_table_after_heading(markdown_text: str, heading: str) -> list[list[str]]:
    """Extract a Markdown table that immediately follows ``heading``."""
    lines = markdown_text.splitlines()
    try:
        heading_index = lines.index(heading)
    except ValueError as error:
        raise AssertionError(f"Missing heading {heading!r}") from error

    table_lines: list[str] = []
    table_started = False
    for line in lines[heading_index + 1 :]:
        if line.startswith("|"):
            table_started = True
            table_lines.append(line)
        elif table_started:
            break

    assert table_lines, f"No Markdown table found after {heading!r}"
    rows = [_split_markdown_table_row(line) for line in table_lines]
    return [row for row in rows if not _is_separator_row(row)]


def _split_markdown_table_row(line: str) -> list[str]:
    """Split one simple Markdown table row into stripped cell values."""
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _is_separator_row(row: list[str]) -> bool:
    """Return whether a parsed row is a Markdown table separator."""
    return all(cell and set(cell) <= {"-", ":"} for cell in row)


def _code_spans(markdown_cell: str) -> list[str]:
    """Extract inline-code spans from a Markdown table cell."""
    return re.findall(r"`([^`]+)`", markdown_cell)


def _module_rows_from_procedure() -> list[tuple[str, str]]:
    """Return module rows rendered in ``TEMPLATE_UPDATE_PROCEDURE.md``."""
    procedure_text = PROCEDURE_PATH.read_text(encoding="utf-8")
    table_rows = _extract_table_after_heading(procedure_text, "### Module Definitions")

    rows: list[tuple[str, str]] = []
    for module_cell, description_cell in table_rows[1:]:
        modules = _code_spans(module_cell)
        assert len(modules) == 1, f"expected one module code span in {module_cell!r}"
        rows.append((modules[0], description_cell))
    return rows


def _path_mapping_rows_from_procedure() -> list[tuple[str, tuple[str, ...]]]:
    """Return expanded path mapping rows rendered in ``TEMPLATE_UPDATE_PROCEDURE.md``."""
    procedure_text = PROCEDURE_PATH.read_text(encoding="utf-8")
    table_rows = _extract_table_after_heading(procedure_text, "### Path Mapping")

    rows: list[tuple[str, tuple[str, ...]]] = []
    for pattern_cell, modules_cell in table_rows[1:]:
        patterns = _code_spans(pattern_cell)
        modules = tuple(_code_spans(modules_cell))
        assert patterns, f"expected at least one pattern code span in {pattern_cell!r}"
        assert modules, f"expected at least one module code span in {modules_cell!r}"
        rows.extend((pattern, modules) for pattern in patterns)
    return rows


def _duplicates(values: list[str]) -> list[str]:
    """Return sorted duplicate values from ``values``."""
    counts = Counter(values)
    return sorted(value for value, count in counts.items() if count > 1)


def _copy_ready_reference_files() -> list[Path]:
    """Return copy-ready files scanned for onboarding-only relative references."""
    paths = [path for path in COPY_READY_REFERENCE_FILES if path.suffix in REFERENCE_FILE_SUFFIXES]

    for root in COPY_READY_REFERENCE_ROOTS:
        for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
            directory = Path(dirpath)
            dirnames[:] = [
                dirname for dirname in dirnames if not (directory / dirname).is_symlink()
            ]
            for filename in filenames:
                path = directory / filename
                if path.suffix in REFERENCE_FILE_SUFFIXES and not path.is_symlink():
                    paths.append(path)

    return sorted(paths)


def _module_enum_from_marker_schema() -> list[str]:
    """Return the baked module enum from the marker schema."""
    schema_defs = _load_marker_schema().get("$defs")
    assert isinstance(schema_defs, dict), "marker schema $defs must be a mapping"
    module_name = schema_defs.get("moduleName")
    assert isinstance(module_name, dict), "marker schema moduleName definition must be a mapping"
    enum = module_name.get("enum")
    assert isinstance(enum, list), "marker schema moduleName enum must be a list"
    assert all(isinstance(module, str) for module in enum), "moduleName enum values must be strings"
    return enum


def test_template_manifest_parses_successfully() -> None:
    """The committed manifest must be readable as YAML."""
    manifest = _load_manifest()
    assert "template_manifest" in manifest


def test_template_manifest_validates_against_schema() -> None:
    """The committed manifest must validate against its JSON Schema."""
    schema = _load_manifest_schema()
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(
        validator.iter_errors(_load_manifest()),
        key=lambda error: error.json_path,
    )
    assert not errors, "\n".join(f"{error.json_path}: {error.message}" for error in errors)


def test_template_manifest_module_names_are_unique() -> None:
    """Each module name must be declared exactly once."""
    names = [name for name, _description in _module_rows_from_manifest()]
    assert not _duplicates(names)


def test_template_manifest_path_patterns_are_unique() -> None:
    """Path mapping patterns must be unique until an explicit precedence rule exists."""
    patterns = [pattern for pattern, _requires_all in _path_mapping_rows_from_manifest()]
    assert not _duplicates(patterns)


def test_template_manifest_path_mapping_modules_exist() -> None:
    """Every path mapping must reference modules declared in the manifest."""
    modules = {name for name, _description in _module_rows_from_manifest()}
    unknown_modules = {
        module
        for _pattern, requires_all in _path_mapping_rows_from_manifest()
        for module in requires_all
        if module not in modules
    }
    assert not unknown_modules


def test_copy_ready_files_do_not_use_onboarding_only_relative_references() -> None:
    """Copy-ready module files must not assume template-onboarding is present."""
    failures: list[str] = []

    for path in _copy_ready_reference_files():
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            line_without_upstream_urls = UPSTREAM_ONBOARDING_URL_RE.sub("", line)
            for token in ONBOARDING_ONLY_REFERENCE_TOKENS:
                if token in line_without_upstream_urls:
                    relative_path = path.relative_to(REPO_ROOT).as_posix()
                    failures.append(f"{relative_path}:{line_number}: {token}")

    assert not failures, (
        "Copy-ready Markdown, YAML, and JSON files must use neutral wording or "
        "absolute upstream URLs for template-onboarding-only references:\n" + "\n".join(failures)
    )


def test_template_sync_marker_schema_module_enum_matches_manifest() -> None:
    """The marker schema's baked module enum must mirror the manifest."""
    manifest_modules = [name for name, _description in _module_rows_from_manifest()]
    assert _module_enum_from_marker_schema() == manifest_modules


def test_template_manifest_filtering_semantics_are_valid() -> None:
    """The manifest must keep the version 1 filtering semantics explicit."""
    filtering = _template_manifest().get("filtering")
    assert filtering == {
        "default_semantics": "AND",
        "path_matching": "most_specific_match_wins",
        "same_specificity_action": "union_modules",
        "unmapped_action": "surface_for_owner",
    }


def test_procedure_module_definitions_match_manifest() -> None:
    """The procedure's module table must mirror the manifest exactly."""
    assert _module_rows_from_procedure() == _module_rows_from_manifest()


def test_procedure_path_mapping_matches_manifest() -> None:
    """The procedure's path mapping table must mirror the manifest exactly."""
    assert _path_mapping_rows_from_procedure() == _path_mapping_rows_from_manifest()
