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
TERRAFORM_INLINE_BLOCK_PATHS = (
    ".pre-commit-config.yaml",
    ".github/workflows/auto-fix-precommit.yml",
    ".github/workflows/precommit-ci.yml",
)
TERRAFORM_INLINE_MARKER_BEGIN = "# template-sync: begin terraform-only"
TERRAFORM_INLINE_MARKER_END = "# template-sync: end terraform-only"
TERRAFORM_SHARED_SURFACE_TOKENS = {
    ".pre-commit-config.yaml": (
        "terraform-fmt",
        "terraform-validate",
        "terraform-tflint",
        ".github/scripts/terraform_hooks.py fmt",
        ".github/scripts/terraform_hooks.py validate",
        ".github/scripts/terraform_hooks.py tflint",
    ),
    ".github/workflows/auto-fix-precommit.yml": (
        "hashicorp/setup-terraform@v4",
        "terraform-linters/setup-tflint@v6",
        'terraform_version: "1.14.4"',
        'tflint_version: "v0.51.1"',
    ),
    ".github/workflows/precommit-ci.yml": (
        "hashicorp/setup-terraform@v4",
        "terraform-linters/setup-tflint@v6",
        'terraform_version: "1.14.4"',
        'tflint_version: "v0.51.1"',
    ),
}
MARKDOWN_INLINE_BLOCK_PATHS = (".pre-commit-config.yaml",)
MARKDOWN_INLINE_MARKER_BEGIN = "# template-sync: begin markdown-only"
MARKDOWN_INLINE_MARKER_END = "# template-sync: end markdown-only"
MARKDOWN_SHARED_SURFACE_TOKENS = {
    ".pre-commit-config.yaml": (
        "https://github.com/DavidAnson/markdownlint-cli2",
        "id: markdownlint-cli2",
    ),
}
PYTHON_INLINE_BLOCK_PATHS = (".pre-commit-config.yaml",)
PYTHON_INLINE_MARKER_BEGIN = "# template-sync: begin python-only"
PYTHON_INLINE_MARKER_END = "# template-sync: end python-only"
PYTHON_SHARED_SURFACE_TOKENS = {
    ".pre-commit-config.yaml": (
        "https://github.com/psf/black",
        "id: black",
        "https://github.com/astral-sh/ruff-pre-commit",
        "id: ruff-check",
    ),
}
YAML_INLINE_BLOCK_COUNTS = {
    ".pre-commit-config.yaml": 1,
    ".github/workflows/data-ci.yml": 2,
}
YAML_INLINE_MARKER_BEGIN = "# template-sync: begin yaml-only"
YAML_INLINE_MARKER_END = "# template-sync: end yaml-only"
YAML_SHARED_SURFACE_TOKENS = {
    ".pre-commit-config.yaml": (
        "https://github.com/adrienverge/yamllint",
        "id: yamllint",
        "args: [-c, .yamllint.yml]",
    ),
    ".github/workflows/data-ci.yml": (
        "YAML style enforcement per .yamllint.yml",
        "Run yamllint",
        "pre-commit run yamllint --all-files",
    ),
}
SCHEMA_INLINE_BLOCK_COUNTS = {
    ".pre-commit-config.yaml": 1,
    ".github/workflows/data-ci.yml": 2,
}
SCHEMA_INLINE_MARKER_BEGIN = "# template-sync: begin schema-only"
SCHEMA_INLINE_MARKER_END = "# template-sync: end schema-only"
SCHEMA_SHARED_SURFACE_TOKENS = {
    ".pre-commit-config.yaml": (
        "validate-example-config-valid-examples",
        "validate-template-sync-marker-valid-examples",
        "validate-example-config-schema",
        "validate-template-sync-manifest-schema",
        "validate-template-sync-marker-schema",
        "check-metaschema",
        "schemas/example-config.schema.json",
    ),
    ".github/workflows/data-ci.yml": (
        "pre-commit run validate-example-config-valid-examples --all-files",
        "pre-commit run validate-template-sync-marker-valid-examples --all-files",
        "pre-commit run validate-example-config-schema --all-files",
        "pre-commit run validate-template-sync-manifest-schema --all-files",
        "pre-commit run validate-template-sync-marker-schema --all-files",
    ),
}
SCHEMA_TEMPLATE_SYNC_SUPPORT_INLINE_BLOCK_COUNTS = {
    ".pre-commit-config.yaml": 1,
    ".github/workflows/data-ci.yml": 2,
}
SCHEMA_TEMPLATE_SYNC_SUPPORT_INLINE_MARKER_BEGIN = (
    "# template-sync: begin schema-template-sync-support-only"
)
SCHEMA_TEMPLATE_SYNC_SUPPORT_INLINE_MARKER_END = (
    "# template-sync: end schema-template-sync-support-only"
)
SCHEMA_TEMPLATE_SYNC_SUPPORT_SHARED_SURFACE_TOKENS = {
    ".pre-commit-config.yaml": (
        r"files: ^\.template-sync/manifest\.yml$",
        r"files: ^\.template-sync/marker\.yml$",
    ),
    ".github/workflows/data-ci.yml": (
        "pre-commit run validate-template-sync-manifest --all-files",
        "pre-commit run validate-template-sync-marker --all-files",
    ),
}
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


def _path_mapping_by_pattern() -> dict[str, dict[str, Any]]:
    """Return path mapping objects keyed by their exact pattern."""
    path_mappings = _template_manifest().get("path_mappings")
    assert isinstance(path_mappings, list), "path_mappings must be a list"

    rows: dict[str, dict[str, Any]] = {}
    for mapping in path_mappings:
        assert isinstance(mapping, dict), "each path mapping must be a mapping"
        pattern = mapping.get("pattern")
        assert isinstance(pattern, str), "path mapping pattern must be a string"
        rows[pattern] = mapping
    return rows


def _strip_inline_blocks(relative_path: str, marker_begin: str, marker_end: str) -> str:
    """Return file text after simulating a downstream sync without one module."""
    path = REPO_ROOT / relative_path
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    stripped_lines: list[str] = []
    is_inside_block = False
    has_seen_block = False

    for line_number, line in enumerate(lines, 1):
        stripped_line = line.strip()

        if stripped_line == marker_begin:
            assert (
                not is_inside_block
            ), f"{relative_path}:{line_number}: nested inline block for {marker_begin}"
            is_inside_block = True
            has_seen_block = True
            continue

        if stripped_line == marker_end:
            assert (
                is_inside_block
            ), f"{relative_path}:{line_number}: unmatched inline block end marker"
            is_inside_block = False
            continue

        if not is_inside_block:
            stripped_lines.append(line)

    assert not is_inside_block, f"{relative_path}: unclosed inline block for {marker_begin}"
    assert has_seen_block, f"{relative_path}: missing inline block for {marker_begin}"
    return "".join(stripped_lines)


def _strip_terraform_only_inline_blocks(relative_path: str) -> str:
    """Return file text after simulating a downstream sync without Terraform."""
    return _strip_inline_blocks(
        relative_path,
        TERRAFORM_INLINE_MARKER_BEGIN,
        TERRAFORM_INLINE_MARKER_END,
    )


def _strip_markdown_only_inline_blocks(relative_path: str) -> str:
    """Return file text after simulating a downstream sync without Markdown."""
    return _strip_inline_blocks(
        relative_path,
        MARKDOWN_INLINE_MARKER_BEGIN,
        MARKDOWN_INLINE_MARKER_END,
    )


def _strip_python_only_inline_blocks(relative_path: str) -> str:
    """Return file text after simulating a downstream sync without Python."""
    return _strip_inline_blocks(
        relative_path,
        PYTHON_INLINE_MARKER_BEGIN,
        PYTHON_INLINE_MARKER_END,
    )


def _strip_yaml_only_inline_blocks(relative_path: str) -> str:
    """Return file text after simulating a downstream sync without YAML."""
    return _strip_inline_blocks(
        relative_path,
        YAML_INLINE_MARKER_BEGIN,
        YAML_INLINE_MARKER_END,
    )


def _strip_schema_only_inline_blocks(relative_path: str) -> str:
    """Return file text after simulating a downstream sync without schemas."""
    return _strip_inline_blocks(
        relative_path,
        SCHEMA_INLINE_MARKER_BEGIN,
        SCHEMA_INLINE_MARKER_END,
    )


def _strip_schema_template_sync_support_only_inline_blocks(relative_path: str) -> str:
    """Return file text after simulating a sync without all combined modules."""
    return _strip_inline_blocks(
        relative_path,
        SCHEMA_TEMPLATE_SYNC_SUPPORT_INLINE_MARKER_BEGIN,
        SCHEMA_TEMPLATE_SYNC_SUPPORT_INLINE_MARKER_END,
    )


def _strip_schema_template_sync_support_blocks_for_modules(
    relative_path: str,
    included_modules: set[str],
) -> str:
    """Return file text after applying combined-marker module presence semantics."""
    if {"schema", "template-sync-support"}.issubset(included_modules):
        return (REPO_ROOT / relative_path).read_text(encoding="utf-8")
    return _strip_schema_template_sync_support_only_inline_blocks(relative_path)


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
    repo_root_resolved = REPO_ROOT.resolve()
    paths = [path for path in COPY_READY_REFERENCE_FILES if path.suffix in REFERENCE_FILE_SUFFIXES]

    for root in COPY_READY_REFERENCE_ROOTS:
        _assert_root_within_repo(root, repo_root_resolved)
        root_resolved = root.resolve()
        for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
            directory = Path(dirpath)
            dirnames[:] = [
                dirname for dirname in dirnames if not (directory / dirname).is_symlink()
            ]
            for filename in filenames:
                path = directory / filename
                if path.suffix not in REFERENCE_FILE_SUFFIXES or path.is_symlink():
                    continue
                assert path.resolve().is_relative_to(
                    root_resolved
                ), f"discovered path must resolve within {root}: {path}"
                paths.append(path)

    return sorted(paths)


def _assert_root_within_repo(root: Path, repo_root_resolved: Path) -> None:
    """Reject ``root`` if it is a symlink or resolves outside ``repo_root_resolved``."""
    assert not root.is_symlink(), f"reference root must not be a symlink: {root}"
    assert root.resolve().is_relative_to(
        repo_root_resolved
    ), f"reference root must resolve within REPO_ROOT: {root}"


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


def test_terraform_inline_blocks_are_declared_for_template_sync() -> None:
    """Terraform-only inline blocks must be paired with manifest notes."""
    mappings = _path_mapping_by_pattern()

    for relative_path in TERRAFORM_INLINE_BLOCK_PATHS:
        text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        assert text.count(TERRAFORM_INLINE_MARKER_BEGIN) == 1
        assert text.count(TERRAFORM_INLINE_MARKER_END) == 1
        _strip_terraform_only_inline_blocks(relative_path)

        mapping = mappings.get(relative_path)
        assert mapping is not None, f"{relative_path} must have a manifest mapping"
        notes = mapping.get("notes")
        assert isinstance(notes, str), f"{relative_path} mapping must describe inline blocks"
        assert "Terraform-only inline block" in notes
        assert "terraform module is excluded" in notes


def test_non_terraform_sync_strips_terraform_tooling_from_shared_surfaces() -> None:
    """A simulated sync without Terraform must remove shared Terraform requirements."""
    for relative_path, forbidden_tokens in TERRAFORM_SHARED_SURFACE_TOKENS.items():
        stripped_text = _strip_terraform_only_inline_blocks(relative_path)
        for forbidden_token in forbidden_tokens:
            assert forbidden_token not in stripped_text, f"{relative_path}: {forbidden_token}"


def test_non_terraform_sync_leaves_shared_surfaces_as_valid_yaml() -> None:
    """Stripping Terraform-only blocks must not corrupt the host YAML document.

    A misplaced inline marker (begin/end inside a mapping, between a key and
    its value, or splitting a multi-line list element) would let the
    token-absence test above still pass while producing an unusable downstream
    config. Round-tripping each stripped text through ``yaml.safe_load`` and
    asserting a mapping top level catches that class of failure without
    pulling in pre-commit or Actions schema dependencies.
    """
    for relative_path in TERRAFORM_SHARED_SURFACE_TOKENS:
        stripped_text = _strip_terraform_only_inline_blocks(relative_path)
        try:
            parsed = yaml.safe_load(stripped_text)
        except yaml.YAMLError as error:
            raise AssertionError(
                f"{relative_path}: stripped text is not valid YAML: {error}"
            ) from error
        assert isinstance(parsed, dict), (
            f"{relative_path}: stripped YAML must load as a mapping, "
            f"got {type(parsed).__name__}"
        )


def test_terraform_sync_retains_terraform_tooling_in_shared_surfaces() -> None:
    """A sync that includes Terraform must keep the current aggregate validation surface."""
    for relative_path, required_tokens in TERRAFORM_SHARED_SURFACE_TOKENS.items():
        text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        for required_token in required_tokens:
            assert required_token in text, f"{relative_path}: {required_token}"


def test_markdown_inline_blocks_are_declared_for_template_sync() -> None:
    """Markdown-only inline blocks must be paired with manifest notes."""
    mappings = _path_mapping_by_pattern()

    for relative_path in MARKDOWN_INLINE_BLOCK_PATHS:
        text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        assert text.count(MARKDOWN_INLINE_MARKER_BEGIN) == 1
        assert text.count(MARKDOWN_INLINE_MARKER_END) == 1
        _strip_markdown_only_inline_blocks(relative_path)

        mapping = mappings.get(relative_path)
        assert mapping is not None, f"{relative_path} must have a manifest mapping"
        notes = mapping.get("notes")
        assert isinstance(notes, str), f"{relative_path} mapping must describe inline blocks"
        assert "Markdown-only inline block" in notes
        assert "markdown module is excluded" in notes


def test_non_markdown_sync_strips_markdown_tooling_from_shared_surfaces() -> None:
    """A simulated sync without Markdown must remove shared Markdown requirements."""
    for relative_path, forbidden_tokens in MARKDOWN_SHARED_SURFACE_TOKENS.items():
        stripped_text = _strip_markdown_only_inline_blocks(relative_path)
        for forbidden_token in forbidden_tokens:
            assert forbidden_token not in stripped_text, f"{relative_path}: {forbidden_token}"


def test_non_markdown_sync_leaves_shared_surfaces_as_valid_yaml() -> None:
    """Stripping Markdown-only blocks must not corrupt the host YAML document."""
    for relative_path in MARKDOWN_SHARED_SURFACE_TOKENS:
        stripped_text = _strip_markdown_only_inline_blocks(relative_path)
        try:
            parsed = yaml.safe_load(stripped_text)
        except yaml.YAMLError as error:
            raise AssertionError(
                f"{relative_path}: stripped text is not valid YAML: {error}"
            ) from error
        assert isinstance(parsed, dict), (
            f"{relative_path}: stripped YAML must load as a mapping, "
            f"got {type(parsed).__name__}"
        )


def test_markdown_sync_retains_markdown_tooling_in_shared_surfaces() -> None:
    """A sync that includes Markdown must keep the current Markdown validation surface."""
    for relative_path, required_tokens in MARKDOWN_SHARED_SURFACE_TOKENS.items():
        text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        for required_token in required_tokens:
            assert required_token in text, f"{relative_path}: {required_token}"


def test_python_inline_blocks_are_declared_for_template_sync() -> None:
    """Python-only inline blocks must be paired with manifest notes."""
    mappings = _path_mapping_by_pattern()

    for relative_path in PYTHON_INLINE_BLOCK_PATHS:
        text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        assert text.count(PYTHON_INLINE_MARKER_BEGIN) == 1
        assert text.count(PYTHON_INLINE_MARKER_END) == 1
        _strip_python_only_inline_blocks(relative_path)

        mapping = mappings.get(relative_path)
        assert mapping is not None, f"{relative_path} must have a manifest mapping"
        notes = mapping.get("notes")
        assert isinstance(notes, str), f"{relative_path} mapping must describe inline blocks"
        assert "Python-only inline block" in notes
        assert "python module is excluded" in notes


def test_non_python_sync_strips_python_tooling_from_shared_surfaces() -> None:
    """A simulated sync without Python must remove Python project hooks."""
    for relative_path, forbidden_tokens in PYTHON_SHARED_SURFACE_TOKENS.items():
        stripped_text = _strip_python_only_inline_blocks(relative_path)
        for forbidden_token in forbidden_tokens:
            assert forbidden_token not in stripped_text, f"{relative_path}: {forbidden_token}"


def test_non_python_sync_leaves_shared_surfaces_as_valid_yaml() -> None:
    """Stripping Python-only blocks must not corrupt the host YAML document."""
    for relative_path in PYTHON_SHARED_SURFACE_TOKENS:
        stripped_text = _strip_python_only_inline_blocks(relative_path)
        try:
            parsed = yaml.safe_load(stripped_text)
        except yaml.YAMLError as error:
            raise AssertionError(
                f"{relative_path}: stripped text is not valid YAML: {error}"
            ) from error
        assert isinstance(parsed, dict), (
            f"{relative_path}: stripped YAML must load as a mapping, "
            f"got {type(parsed).__name__}"
        )


def test_python_sync_retains_python_tooling_in_shared_surfaces() -> None:
    """A sync that includes Python must keep the current Python project hooks."""
    for relative_path, required_tokens in PYTHON_SHARED_SURFACE_TOKENS.items():
        text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        for required_token in required_tokens:
            assert required_token in text, f"{relative_path}: {required_token}"


def test_yaml_inline_blocks_are_declared_for_template_sync() -> None:
    """YAML-only inline blocks must be paired with manifest notes."""
    mappings = _path_mapping_by_pattern()

    for relative_path, expected_count in YAML_INLINE_BLOCK_COUNTS.items():
        text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        assert text.count(YAML_INLINE_MARKER_BEGIN) == expected_count
        assert text.count(YAML_INLINE_MARKER_END) == expected_count
        _strip_yaml_only_inline_blocks(relative_path)

        mapping = mappings.get(relative_path)
        assert mapping is not None, f"{relative_path} must have a manifest mapping"
        notes = mapping.get("notes")
        assert isinstance(notes, str), f"{relative_path} mapping must describe inline blocks"
        assert "YAML-only inline block" in notes
        assert "yaml module is excluded" in notes


def test_non_yaml_sync_strips_yamllint_tooling_from_shared_surfaces() -> None:
    """A simulated sync without YAML must remove yamllint hooks and invocations."""
    for relative_path, forbidden_tokens in YAML_SHARED_SURFACE_TOKENS.items():
        stripped_text = _strip_yaml_only_inline_blocks(relative_path)
        for forbidden_token in forbidden_tokens:
            assert forbidden_token not in stripped_text, f"{relative_path}: {forbidden_token}"


def test_non_yaml_sync_leaves_shared_surfaces_as_valid_yaml() -> None:
    """Stripping YAML-only blocks must not corrupt the host YAML document."""
    for relative_path in YAML_SHARED_SURFACE_TOKENS:
        stripped_text = _strip_yaml_only_inline_blocks(relative_path)
        try:
            parsed = yaml.safe_load(stripped_text)
        except yaml.YAMLError as error:
            raise AssertionError(
                f"{relative_path}: stripped text is not valid YAML: {error}"
            ) from error
        assert isinstance(parsed, dict), (
            f"{relative_path}: stripped YAML must load as a mapping, "
            f"got {type(parsed).__name__}"
        )


def test_yaml_sync_retains_yamllint_tooling_in_shared_surfaces() -> None:
    """A sync that includes YAML must keep the current yamllint surfaces."""
    for relative_path, required_tokens in YAML_SHARED_SURFACE_TOKENS.items():
        text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        for required_token in required_tokens:
            assert required_token in text, f"{relative_path}: {required_token}"


def test_schema_inline_blocks_are_declared_for_template_sync() -> None:
    """Schema-only inline blocks must be paired with manifest notes."""
    mappings = _path_mapping_by_pattern()

    for relative_path, expected_count in SCHEMA_INLINE_BLOCK_COUNTS.items():
        text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        assert text.count(SCHEMA_INLINE_MARKER_BEGIN) == expected_count
        assert text.count(SCHEMA_INLINE_MARKER_END) == expected_count
        _strip_schema_only_inline_blocks(relative_path)

        mapping = mappings.get(relative_path)
        assert mapping is not None, f"{relative_path} must have a manifest mapping"
        notes = mapping.get("notes")
        assert isinstance(notes, str), f"{relative_path} mapping must describe inline blocks"
        assert "Schema-only inline block" in notes
        assert "schema module is excluded" in notes


def test_non_schema_sync_strips_schema_tooling_from_shared_surfaces() -> None:
    """A simulated sync without schemas must remove schema-owned validators."""
    for relative_path, forbidden_tokens in SCHEMA_SHARED_SURFACE_TOKENS.items():
        stripped_text = _strip_schema_only_inline_blocks(relative_path)
        for forbidden_token in forbidden_tokens:
            assert forbidden_token not in stripped_text, f"{relative_path}: {forbidden_token}"


def test_non_schema_sync_leaves_shared_surfaces_as_valid_yaml() -> None:
    """Stripping Schema-only blocks must not corrupt the host YAML document."""
    for relative_path in SCHEMA_SHARED_SURFACE_TOKENS:
        stripped_text = _strip_schema_only_inline_blocks(relative_path)
        try:
            parsed = yaml.safe_load(stripped_text)
        except yaml.YAMLError as error:
            raise AssertionError(
                f"{relative_path}: stripped text is not valid YAML: {error}"
            ) from error
        assert isinstance(parsed, dict), (
            f"{relative_path}: stripped YAML must load as a mapping, "
            f"got {type(parsed).__name__}"
        )


def test_schema_sync_retains_schema_tooling_in_shared_surfaces() -> None:
    """A sync that includes schemas must keep schema-owned validators."""
    for relative_path, required_tokens in SCHEMA_SHARED_SURFACE_TOKENS.items():
        text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        for required_token in required_tokens:
            assert required_token in text, f"{relative_path}: {required_token}"


def test_schema_template_sync_support_inline_blocks_are_declared() -> None:
    """Combined schema/template-sync blocks must be paired with manifest notes."""
    mappings = _path_mapping_by_pattern()

    for relative_path, expected_count in SCHEMA_TEMPLATE_SYNC_SUPPORT_INLINE_BLOCK_COUNTS.items():
        text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        assert text.count(SCHEMA_TEMPLATE_SYNC_SUPPORT_INLINE_MARKER_BEGIN) == expected_count
        assert text.count(SCHEMA_TEMPLATE_SYNC_SUPPORT_INLINE_MARKER_END) == expected_count
        _strip_schema_template_sync_support_only_inline_blocks(relative_path)

        mapping = mappings.get(relative_path)
        assert mapping is not None, f"{relative_path} must have a manifest mapping"
        notes = mapping.get("notes")
        assert isinstance(notes, str), f"{relative_path} mapping must describe inline blocks"
        assert "Schema-template-sync-support-only inline block" in notes
        assert "schema or template-sync-support module is excluded" in notes


def test_sync_missing_schema_or_template_sync_support_strips_combined_tooling() -> None:
    """Combined blocks must be removed when either required module is absent."""
    module_sets_missing_one_or_more = (
        {"template-sync-support"},
        {"schema"},
        set(),
    )

    for (
        relative_path,
        forbidden_tokens,
    ) in SCHEMA_TEMPLATE_SYNC_SUPPORT_SHARED_SURFACE_TOKENS.items():
        for included_modules in module_sets_missing_one_or_more:
            stripped_text = _strip_schema_template_sync_support_blocks_for_modules(
                relative_path,
                included_modules,
            )
            for forbidden_token in forbidden_tokens:
                assert (
                    forbidden_token not in stripped_text
                ), f"{relative_path}: {sorted(included_modules)}: {forbidden_token}"


def test_sync_missing_schema_or_template_sync_support_leaves_valid_yaml() -> None:
    """Stripping combined blocks must not corrupt the host YAML document."""
    module_sets_missing_one_or_more = (
        {"template-sync-support"},
        {"schema"},
        set(),
    )

    for relative_path in SCHEMA_TEMPLATE_SYNC_SUPPORT_SHARED_SURFACE_TOKENS:
        for included_modules in module_sets_missing_one_or_more:
            stripped_text = _strip_schema_template_sync_support_blocks_for_modules(
                relative_path,
                included_modules,
            )
            try:
                parsed = yaml.safe_load(stripped_text)
            except yaml.YAMLError as error:
                raise AssertionError(
                    f"{relative_path}: stripped text is not valid YAML: {error}"
                ) from error
            assert isinstance(parsed, dict), (
                f"{relative_path}: stripped YAML must load as a mapping, "
                f"got {type(parsed).__name__}"
            )


def test_schema_template_sync_support_sync_retains_combined_tooling() -> None:
    """A sync with both modules must keep combined validation blocks."""
    included_modules = {"schema", "template-sync-support"}

    for (
        relative_path,
        required_tokens,
    ) in SCHEMA_TEMPLATE_SYNC_SUPPORT_SHARED_SURFACE_TOKENS.items():
        text = _strip_schema_template_sync_support_blocks_for_modules(
            relative_path,
            included_modules,
        )
        assert text == (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        for required_token in required_tokens:
            assert required_token in text, f"{relative_path}: {required_token}"


def test_aggregate_precommit_workflow_is_not_python_scoped() -> None:
    """The aggregate pre-commit gate must survive excluding the Python module."""
    mappings = _path_mapping_by_pattern()
    precommit_mapping = mappings.get(".github/workflows/precommit-ci.yml")
    assert precommit_mapping is not None, "precommit-ci.yml must have a manifest mapping"
    assert precommit_mapping.get("requires_all") == ["baseline", "github-actions"]


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
