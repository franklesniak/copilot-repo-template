"""Validate the template sync manifest contract and documentation mirror."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import jsonschema
import yaml  # type: ignore[import-untyped]

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / ".template-sync" / "manifest.yml"
MANIFEST_SCHEMA_PATH = REPO_ROOT / "schemas" / "template-sync-manifest.schema.json"
PROCEDURE_PATH = REPO_ROOT / "TEMPLATE_UPDATE_PROCEDURE.md"


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
    return sorted({value for value in values if values.count(value) > 1})


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
