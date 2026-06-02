"""Validate the template sync manifest contract and documentation mirror."""

from __future__ import annotations

import fnmatch
import importlib.util
import json
import os
import posixpath
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import unquote, urlsplit

import jsonschema
import pytest
import yaml  # type: ignore[import-untyped]

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / ".template-sync" / "manifest.yml"
VALIDATE_MARKER_PATH = REPO_ROOT / ".template-sync" / "scripts" / "validate_marker.py"
TEMPLATE_SYNC_SCRIPT_DIR = VALIDATE_MARKER_PATH.parent
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

if str(TEMPLATE_SYNC_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(TEMPLATE_SYNC_SCRIPT_DIR))

from template_sync_materialization_helpers import (  # noqa: E402
    INLINE_BLOCK_MARKER_RE,
    MismatchedInlineBlockError,
    MissingExpectedInlineBlockError,
    NestedInlineBlockError,
    UnclosedInlineBlockError,
    UnknownInlineBlockMarkerError,
    UnmatchedInlineBlockEndError,
    remove_inline_block_family,
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
        "validate-example-config-schema",
        "schemas/example-config.schema.json",
    ),
    ".github/workflows/data-ci.yml": (
        "pre-commit run validate-example-config-valid-examples --all-files",
        "pre-commit run validate-example-config-schema --all-files",
    ),
}
TEMPLATE_SYNC_SUPPORT_INLINE_BLOCK_COUNTS = {
    ".pre-commit-config.yaml": 1,
    ".github/workflows/data-ci.yml": 2,
}
TEMPLATE_SYNC_SUPPORT_INLINE_MARKER_BEGIN = "# template-sync: begin template-sync-support-only"
TEMPLATE_SYNC_SUPPORT_INLINE_MARKER_END = "# template-sync: end template-sync-support-only"
TEMPLATE_SYNC_SUPPORT_SHARED_SURFACE_TOKENS = {
    ".pre-commit-config.yaml": (
        "validate-template-sync-marker-valid-examples",
        "validate-template-sync-instruction-contracts-valid-examples",
        "validate-template-sync-manifest-schema",
        "validate-template-sync-marker-schema",
        "validate-template-sync-instruction-contracts-schema",
        r"files: ^\.template-sync/manifest\.yml$",
        r"files: ^\.template-sync/marker\.yml$",
        r"files: ^\.template-sync/instruction-contracts\.yml$",
        "validate-instruction-contracts-upstream",
        "validate-instruction-contracts-downstream",
        "--skip-if-marker-present",
    ),
    ".github/workflows/data-ci.yml": (
        "pre-commit run validate-template-sync-marker-valid-examples --all-files",
        "pre-commit run validate-template-sync-instruction-contracts-valid-examples --all-files",
        "pre-commit run validate-template-sync-manifest-schema --all-files",
        "pre-commit run validate-template-sync-marker-schema --all-files",
        "pre-commit run validate-template-sync-instruction-contracts-schema --all-files",
        "pre-commit run validate-template-sync-manifest --all-files",
        "pre-commit run validate-template-sync-marker --all-files",
        "pre-commit run validate-template-sync-instruction-contracts --all-files",
        "pre-commit run validate-instruction-contracts-upstream --all-files",
        "pre-commit run validate-instruction-contracts-downstream --all-files",
    ),
}
GITHUB_PLATFORM_INLINE_BLOCK_COUNTS = {
    ".pre-commit-config.yaml": 1,
    ".github/workflows/data-ci.yml": 2,
}
GITHUB_PLATFORM_INLINE_MARKER_BEGIN = "# template-sync: begin github-platform-only"
GITHUB_PLATFORM_INLINE_MARKER_END = "# template-sync: end github-platform-only"
GITHUB_PLATFORM_SHARED_SURFACE_TOKENS = {
    ".pre-commit-config.yaml": (
        "validate-dependabot-config",
        "Validate Dependabot configuration",
        r"files: ^\.github/dependabot\.yml$",
        "vendor.dependabot",
    ),
    ".github/workflows/data-ci.yml": (
        "validate-dependabot-config",
        "pre-commit run validate-dependabot-config --all-files",
        ".github/dependabot.yml",
        "vendor.dependabot",
    ),
}
REFERENCE_ONLY_INLINE_BLOCK_COUNTS = {
    "markdown-reference-only": {
        ".github/copilot-instructions.md": 2,
        ".cursor/rules/repository-instructions.mdc": 3,
        ".hermes.md": 3,
        "AGENTS.md": 3,
        "CLAUDE.md": 3,
        "GEMINI.md": 3,
    },
    "powershell-reference-only": {
        ".github/copilot-instructions.md": 2,
        ".cursor/rules/repository-instructions.mdc": 2,
        ".hermes.md": 2,
        "AGENTS.md": 2,
        "CLAUDE.md": 2,
        "GEMINI.md": 2,
    },
    "python-reference-only": {
        ".github/copilot-instructions.md": 1,
        ".cursor/rules/repository-instructions.mdc": 2,
        ".hermes.md": 2,
        "AGENTS.md": 2,
        "CLAUDE.md": 2,
        "GEMINI.md": 2,
    },
    "terraform-reference-only": {
        ".github/copilot-instructions.md": 3,
        ".cursor/rules/repository-instructions.mdc": 2,
        ".hermes.md": 2,
        "AGENTS.md": 2,
        "CLAUDE.md": 2,
        "GEMINI.md": 2,
    },
    "json-reference-only": {
        ".github/copilot-instructions.md": 1,
        ".cursor/rules/repository-instructions.mdc": 3,
        ".hermes.md": 3,
        "AGENTS.md": 3,
        "CLAUDE.md": 3,
        "GEMINI.md": 3,
    },
    "yaml-reference-only": {
        ".github/copilot-instructions.md": 1,
        ".cursor/rules/repository-instructions.mdc": 3,
        ".hermes.md": 3,
        "AGENTS.md": 3,
        "CLAUDE.md": 3,
        "GEMINI.md": 3,
    },
    "schema-reference-only": {
        ".github/copilot-instructions.md": 2,
        ".cursor/rules/repository-instructions.mdc": 3,
        ".hermes.md": 3,
        "AGENTS.md": 3,
        "CLAUDE.md": 3,
        "GEMINI.md": 3,
    },
}
REFERENCE_ONLY_MARKER_MODULES = {
    "markdown-reference-only": "markdown",
    "powershell-reference-only": "powershell",
    "python-reference-only": "python",
    "terraform-reference-only": "terraform",
    "json-reference-only": "json",
    "yaml-reference-only": "yaml",
    "schema-reference-only": "schema",
}
PROTECTED_ENTRY_POINT_REFERENCE_PATHS = (
    ".cursor/rules/repository-instructions.mdc",
    ".hermes.md",
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
)
PROTECTED_REFERENCE_MANIFEST_PATTERNS = {
    ".github/copilot-instructions.md": ".github/copilot-instructions.md",
    ".cursor/rules/repository-instructions.mdc": ".cursor/rules/**",
    ".hermes.md": ".hermes.md",
    "AGENTS.md": "AGENTS.md",
    "CLAUDE.md": "CLAUDE.md",
    "GEMINI.md": "GEMINI.md",
}
REFERENCE_ONLY_FORBIDDEN_ENTRY_POINT_TOKENS = {
    "markdown-reference-only": (
        "Documentation Writing Style",
        "docs.instructions.md",
        "npm run lint:md",
    ),
    "powershell-reference-only": (
        "Invoke-Pester -Path tests/ -Output Detailed",
        "powershell.instructions.md",
    ),
    "python-reference-only": (
        "pytest tests/ -v --cov --cov-report=term-missing",
        "python.instructions.md",
    ),
    "terraform-reference-only": (
        "terraform fmt -check -recursive",
        "terraform.instructions.md",
        "terraform test -verbose",
        "tflint --recursive",
    ),
    "json-reference-only": (
        "`check-json`",
        "json.instructions.md",
    ),
    "yaml-reference-only": (
        "`check-yaml`",
        "yaml.instructions.md",
        "`yamllint`",
    ),
    "schema-reference-only": (
        "check-jsonschema",
        "check-metaschema",
        "pytest tests/test_schema_examples.py -v",
        "schemas/README.md",
    ),
}
PROTECTED_PROTOCOL_HEADINGS_AFTER_REFERENCE_STRIP = {
    "AGENTS.md": (
        "## GitHub Plugin Usage",
        "## PR Review Workflow (Codex-adapted)",
    ),
    "CLAUDE.md": (
        "## Handling Code Review Comments",
        "## Automated Review Loop",
    ),
}
REFERENCE_FILE_SUFFIXES = {".json", ".md", ".yaml", ".yml"}
MARKDOWN_FILE_SUFFIXES = {".md", ".mdc"}
SKIPPED_DISCOVERY_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "node_modules",
}
ONBOARDING_ONLY_REFERENCE_TOKENS = (
    "OPTIONAL_CONFIGURATIONS.md",
    "GETTING_STARTED_NEW_REPO.md",
    "GETTING_STARTED_EXISTING_REPO.md",
    "TEMPLATE_MAINTENANCE.md",
    "TEMPLATE_DESIGN_DECISIONS.md",
)
SKIPPABLE_OPTIONAL_REFERENCE_PATHS = (
    "tests/test_dependabot_schema.py",
    "tests/fixtures/dependabot/auto-assignment.yml",
)
UPSTREAM_TEMPLATE_BLOB_ROOT = "https://github.com/franklesniak/copilot-repo-template/blob/HEAD/"
UPSTREAM_ONBOARDING_URL_RE = re.compile(
    re.escape(UPSTREAM_TEMPLATE_BLOB_ROOT)
    + r"(?:OPTIONAL_CONFIGURATIONS\.md|GETTING_STARTED_NEW_REPO\.md|"
    r"GETTING_STARTED_EXISTING_REPO\.md|TEMPLATE_MAINTENANCE\.md|"
    r"\.github/TEMPLATE_DESIGN_DECISIONS\.md)(?:#[A-Za-z0-9._-]+)?"
)
# Allow optional blockquote markers before a fence (e.g. ``> ```py``) so fenced
# code examples inside blockquotes are skipped like any other fenced block.
MARKDOWN_FENCE_RE = re.compile(r"^(?: {0,3}>)* {0,3}(?P<fence>`{3,}|~{3,})")
MARKDOWN_INLINE_LINK_RE = re.compile(
    r"(?<!!)\[[^\]\n]+\]\((?P<target><[^>\n]+>|[^)\s\n]+)(?:\s+[^)\n]*)?\)"
)
MARKDOWN_REFERENCE_DEFINITION_RE = re.compile(r"^ {0,3}\[[^\]\n]+\]:\s+(?P<target><[^>\n]+>|\S+)")
CONCRETE_PATTERN_ALLOWLIST = {
    ".template-sync/marker.yml": (
        "Downstream-local retained marker; mapped because downstream repos carry "
        "it but not committed in the upstream template."
    ),
}
SOURCE_REPO = "https://github.com/franklesniak/copilot-repo-template.git"
FULL_SHA = "0123456789abcdef0123456789abcdef01234567"


def _load_validate_marker_module() -> Any:
    """Import the marker validator script as a module for shared helper tests."""
    spec = importlib.util.spec_from_file_location(
        "template_sync_validate_marker",
        VALIDATE_MARKER_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


VALIDATE_MARKER = _load_validate_marker_module()


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


def _manifest_validation_errors(manifest: dict[str, Any]) -> list[jsonschema.ValidationError]:
    """Return sorted validation errors for ``manifest`` against the manifest schema."""
    validator = jsonschema.Draft202012Validator(_load_manifest_schema())
    return sorted(
        validator.iter_errors(manifest),
        key=lambda error: error.json_path,
    )


def _minimal_manifest_document(version: int, path_mapping: dict[str, Any]) -> dict[str, Any]:
    """Build a minimal manifest fixture for schema compatibility tests."""
    filtering: dict[str, str] = {
        "default_semantics": "AND",
        "path_matching": "most_specific_match_wins",
        "same_specificity_action": "union_modules",
        "unmapped_action": "surface_for_owner",
    }
    notes: dict[str, Any] = {
        "downstream_retention": "Downstream repositories keep the marker when syncing.",
    }

    if version == 1:
        notes["known_limitations"] = [
            {
                "path": ".github/workflows/data-ci.yml",
                "description": "Version 1 cannot model cross-module alternatives.",
                "future_work": "Move to manifest version 2 relation semantics.",
            }
        ]
    elif version == 2:
        filtering["requires_any_semantics"] = "OR"

    return {
        "template_manifest": {
            "version": version,
            "modules": [
                {"name": "baseline", "description": "Baseline files."},
                {"name": "github-actions", "description": "GitHub Actions workflows."},
                {"name": "json", "description": "JSON files."},
                {"name": "yaml", "description": "YAML files."},
                {"name": "schema", "description": "JSON Schema files."},
            ],
            "path_mappings": [path_mapping],
            "filtering": filtering,
            "notes": notes,
        }
    }


def _synthetic_manifest_document(path_mappings: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a version 2 manifest fixture for downstream marker-integrity tests."""
    modules = [
        {
            "name": "baseline",
            "description": "Baseline files.",
        },
        {
            "name": "github-actions",
            "description": "GitHub Actions files.",
        },
        {
            "name": "github-platform",
            "description": "GitHub platform files.",
        },
        {
            "name": "schema",
            "description": "Schema files.",
        },
        {
            "name": "template-onboarding",
            "description": "Template onboarding files.",
        },
        {
            "name": "template-sync-support",
            "description": "Template sync support files.",
        },
        {
            "name": "terraform",
            "description": "Terraform files.",
        },
        {
            "name": "yaml",
            "description": "YAML files.",
        },
    ]
    return {
        "template_manifest": {
            "version": 2,
            "modules": modules,
            "path_mappings": path_mappings,
            "filtering": {
                "default_semantics": "AND",
                "requires_any_semantics": "OR",
                "path_matching": "most_specific_match_wins",
                "same_specificity_action": "union_modules",
                "unmapped_action": "surface_for_owner",
            },
            "notes": {
                "downstream_retention": "Downstream repositories keep marker data for syncs.",
            },
        }
    }


def _marker_document(
    included_modules: list[str],
    *,
    local_overrides: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Build a schema-valid marker fixture for downstream integrity tests."""
    template_sync: dict[str, Any] = {
        "source_repo": SOURCE_REPO,
        "last_reviewed_template_commit": FULL_SHA,
        "included_modules": included_modules,
    }
    if local_overrides is not None:
        template_sync["local_overrides"] = local_overrides
    return {"template_sync": template_sync}


def _write_text(repo_root: Path, relative_path: str, text: str = "placeholder\n") -> None:
    """Write text below a fixture repository root."""
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> None:
    """Write YAML below a fixture repository root."""
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _copy_marker_validation_schemas(repo_root: Path) -> None:
    """Copy marker validation schemas into a fixture repository."""
    schemas_dir = repo_root / "schemas"
    schemas_dir.mkdir(parents=True, exist_ok=True)
    (schemas_dir / MARKER_SCHEMA_PATH.name).write_text(
        MARKER_SCHEMA_PATH.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (schemas_dir / MANIFEST_SCHEMA_PATH.name).write_text(
        MANIFEST_SCHEMA_PATH.read_text(encoding="utf-8"),
        encoding="utf-8",
    )


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
    """Return ``(pattern, referenced_modules)`` rows from the manifest."""
    return _path_mapping_rows_from_template_manifest(_template_manifest())


def _path_mapping_rows_from_manifest_document(
    manifest: dict[str, Any],
) -> list[tuple[str, tuple[str, ...]]]:
    """Return path-mapping rows from a manifest document object."""
    template_manifest = manifest.get("template_manifest")
    assert isinstance(template_manifest, dict), "template_manifest must be a mapping"
    return _path_mapping_rows_from_template_manifest(template_manifest)


def _path_mapping_rows_from_template_manifest(
    template_manifest: dict[str, Any],
) -> list[tuple[str, tuple[str, ...]]]:
    """Return path-mapping rows from a nested ``template_manifest`` object."""
    path_mappings = template_manifest.get("path_mappings")
    assert isinstance(path_mappings, list), "path_mappings must be a list"

    rows: list[tuple[str, tuple[str, ...]]] = []
    for mapping in path_mappings:
        assert isinstance(mapping, dict), "each path mapping must be a mapping"
        pattern = mapping.get("pattern")
        assert isinstance(pattern, str), "path mapping pattern must be a string"
        rows.append((pattern, _path_mapping_referenced_modules(mapping)))
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


def _relation_modules(mapping: dict[str, Any], relation_key: str) -> tuple[str, ...]:
    """Return module names for one path-mapping relation key."""
    pattern = mapping.get("pattern", "<unknown>")
    if relation_key not in mapping:
        return ()

    modules = mapping.get(relation_key)
    assert isinstance(modules, list), f"{pattern} {relation_key} must be a list"
    assert all(
        isinstance(module, str) for module in modules
    ), f"{pattern} {relation_key} values must be strings"
    return tuple(modules)


def _path_mapping_referenced_modules(mapping: dict[str, Any]) -> tuple[str, ...]:
    """Return every module referenced by a path mapping in deterministic order."""
    referenced_modules: list[str] = []

    for relation_key in ("requires_all", "requires_any"):
        for module in _relation_modules(mapping, relation_key):
            if module not in referenced_modules:
                referenced_modules.append(module)

    pattern = mapping.get("pattern", "<unknown>")
    assert referenced_modules, f"{pattern} must reference at least one module"
    return tuple(referenced_modules)


def _path_mapping_matches_modules(
    mapping: dict[str, Any],
    included_modules: set[str],
) -> bool:
    """Return whether ``included_modules`` satisfies a manifest path mapping."""
    requires_all = set(_relation_modules(mapping, "requires_all"))
    requires_any = set(_relation_modules(mapping, "requires_any"))

    if not requires_all.issubset(included_modules):
        return False
    if requires_any and not requires_any.intersection(included_modules):
        return False
    return True


def _path_mapping_relations_from_manifest() -> list[tuple[str, tuple[str, ...], tuple[str, ...]]]:
    """Return ``(pattern, requires_all, requires_any)`` rows from the manifest."""
    path_mappings = _template_manifest().get("path_mappings")
    assert isinstance(path_mappings, list), "path_mappings must be a list"

    rows: list[tuple[str, tuple[str, ...], tuple[str, ...]]] = []
    for mapping in path_mappings:
        assert isinstance(mapping, dict), "each path mapping must be a mapping"
        pattern = mapping.get("pattern")
        assert isinstance(pattern, str), "path mapping pattern must be a string"
        requires_all = _relation_modules(mapping, "requires_all")
        requires_any = _relation_modules(mapping, "requires_any")
        rows.append((pattern, requires_all, requires_any))
    return rows


def _pattern_specificity(pattern: str) -> tuple[int, int, int]:
    """Return a sortable specificity rank for a manifest path pattern."""
    is_exact = not _is_glob_pattern(pattern)
    literal_length = sum(1 for character in pattern if character not in "*?[]")
    return (int(is_exact), literal_length, pattern.count("/"))


def _is_glob_pattern(pattern: str) -> bool:
    """Return whether ``pattern`` uses fnmatch wildcard syntax."""
    return any(wildcard in pattern for wildcard in "*?[")


def _manifest_modules_for_path(
    relative_path: str,
    path_mapping_rows: list[tuple[str, tuple[str, ...]]] | None = None,
) -> tuple[str, ...] | None:
    """Return the modules for ``relative_path`` using manifest filtering semantics."""
    if path_mapping_rows is None:
        path_mapping_rows = _path_mapping_rows_from_manifest()

    matches: list[tuple[tuple[int, int, int], tuple[str, ...]]] = []

    for pattern, modules in path_mapping_rows:
        if fnmatch.fnmatchcase(relative_path, pattern):
            matches.append((_pattern_specificity(pattern), modules))

    if not matches:
        return None

    best_specificity = max(specificity for specificity, _modules in matches)
    selected_modules: list[str] = []
    for specificity, modules in matches:
        if specificity != best_specificity:
            continue
        for module in modules:
            if module not in selected_modules:
                selected_modules.append(module)
    return tuple(selected_modules)


def _git_tracked_paths(repo_root: Path) -> tuple[str, ...]:
    """Return paths tracked by git under ``repo_root`` using POSIX separators."""
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=repo_root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return tuple(path for path in result.stdout.splitlines() if path)


def _git_present_paths(repo_root: Path) -> tuple[str, ...]:
    """Return tracked and untracked non-ignored paths present in ``repo_root``."""
    return VALIDATE_MARKER.git_present_paths(repo_root)


def _unresolved_concrete_path_mapping_patterns(
    manifest: dict[str, Any],
    present_paths: Iterable[str],
    allowlist: Mapping[str, str],
    *,
    included_modules: set[str] | None = None,
    local_overrides: tuple[Any, ...] = (),
) -> list[str]:
    """Return concrete manifest patterns that do not resolve in the selected mode."""
    _module_names, mappings = VALIDATE_MARKER.parse_manifest_mappings(manifest)
    return [
        pattern
        for pattern, _relation in VALIDATE_MARKER.unresolved_concrete_manifest_patterns(
            mappings=mappings,
            present_paths=present_paths,
            allowlist_paths=set(allowlist),
            included_modules=included_modules,
            local_overrides=local_overrides,
        )
    ]


def _concrete_pattern_integrity_failures(
    repo_root: Path,
    manifest: dict[str, Any],
    allowlist: Mapping[str, str],
) -> list[str]:
    """Return concrete-pattern failures using upstream or downstream marker mode."""
    marker_path = repo_root / ".template-sync" / "marker.yml"
    if not marker_path.exists():
        return _unresolved_concrete_path_mapping_patterns(
            manifest,
            _git_tracked_paths(repo_root),
            allowlist,
        )

    marker = yaml.safe_load(marker_path.read_text(encoding="utf-8"))
    assert isinstance(marker, dict), "marker root must be a mapping"
    included_modules, local_overrides, _deferred_candidates, _protected_decisions = (
        VALIDATE_MARKER.parse_marker(marker)
    )
    return _unresolved_concrete_path_mapping_patterns(
        manifest,
        _git_present_paths(repo_root),
        {},
        included_modules=included_modules,
        local_overrides=local_overrides,
    )


def _run_marker_validator(repo_root: Path) -> subprocess.CompletedProcess[str]:
    """Run the marker validator script in require-marker mode."""
    return subprocess.run(
        [
            sys.executable,
            str(VALIDATE_MARKER_PATH),
            "--repo-root",
            str(repo_root),
            "--require-marker",
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _unmapped_tracked_paths(
    tracked_paths: Iterable[str],
    path_mapping_rows: list[tuple[str, tuple[str, ...]]],
) -> list[str]:
    """Return git-tracked paths that do not resolve to a manifest mapping."""
    return [
        tracked_path
        for tracked_path in tracked_paths
        if _manifest_modules_for_path(tracked_path, path_mapping_rows) is None
    ]


def _run_git(repo_root: Path, *args: str) -> None:
    """Run a git command in ``repo_root`` for manifest-integrity fixtures."""
    subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _marker_name_from_expected_pair(
    relative_path: str,
    marker_begin: str,
    marker_end: str,
) -> str:
    """Return the shared marker family name represented by one begin/end pair."""
    begin_match = INLINE_BLOCK_MARKER_RE.match(marker_begin)
    end_match = INLINE_BLOCK_MARKER_RE.match(marker_end)
    assert begin_match is not None, f"{relative_path}: invalid begin marker {marker_begin!r}"
    assert end_match is not None, f"{relative_path}: invalid end marker {marker_end!r}"
    assert begin_match.group("kind") == "begin", f"{relative_path}: expected begin marker"
    assert end_match.group("kind") == "end", f"{relative_path}: expected end marker"
    assert begin_match.group("name") == end_match.group("name"), (
        f"{relative_path}: marker pair names differ: "
        f"{begin_match.group('name')} != {end_match.group('name')}"
    )
    return begin_match.group("name")


def _strip_inline_blocks_from_text(
    text: str,
    relative_path: str,
    marker_begin: str,
    marker_end: str,
) -> str:
    """Return ``text`` after removing one complete inline block family."""
    return remove_inline_block_family(
        text,
        _marker_name_from_expected_pair(relative_path, marker_begin, marker_end),
        relative_path=relative_path,
    )


def _strip_inline_blocks(relative_path: str, marker_begin: str, marker_end: str) -> str:
    """Return file text after simulating a downstream sync without one module."""
    path = REPO_ROOT / relative_path
    return _strip_inline_blocks_from_text(
        path.read_text(encoding="utf-8"),
        relative_path,
        marker_begin,
        marker_end,
    )


def _reference_only_marker_begin(marker_name: str) -> str:
    """Return the Markdown-safe begin marker for a reference-only block."""
    return f"<!-- template-sync: begin {marker_name} -->"


def _reference_only_marker_end(marker_name: str) -> str:
    """Return the Markdown-safe end marker for a reference-only block."""
    return f"<!-- template-sync: end {marker_name} -->"


def _strip_reference_only_inline_blocks(relative_path: str, marker_name: str) -> str:
    """Return file text after stripping one reference-only marker family."""
    return _strip_inline_blocks(
        relative_path,
        _reference_only_marker_begin(marker_name),
        _reference_only_marker_end(marker_name),
    )


def _strip_reference_only_blocks_for_modules(
    relative_path: str,
    included_modules: set[str],
) -> str:
    """Return file text after applying reference-only module presence semantics."""
    text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
    path_marker_counts = {
        marker_name: path_counts[relative_path]
        for marker_name, path_counts in REFERENCE_ONLY_INLINE_BLOCK_COUNTS.items()
        if relative_path in path_counts
    }

    for marker_name, module_name in REFERENCE_ONLY_MARKER_MODULES.items():
        if module_name in included_modules or marker_name not in path_marker_counts:
            continue
        stripped_text = _strip_inline_blocks_from_text(
            text,
            relative_path,
            _reference_only_marker_begin(marker_name),
            _reference_only_marker_end(marker_name),
        )
        assert stripped_text != text, f"{relative_path}: {marker_name} did not strip"
        text = stripped_text
    return text


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


def _strip_template_sync_support_only_inline_blocks(relative_path: str) -> str:
    """Return file text after simulating a sync without template sync support."""
    return _strip_inline_blocks(
        relative_path,
        TEMPLATE_SYNC_SUPPORT_INLINE_MARKER_BEGIN,
        TEMPLATE_SYNC_SUPPORT_INLINE_MARKER_END,
    )


def _strip_github_platform_only_inline_blocks(relative_path: str) -> str:
    """Return file text after simulating a downstream sync without GitHub platform."""
    return _strip_inline_blocks(
        relative_path,
        GITHUB_PLATFORM_INLINE_MARKER_BEGIN,
        GITHUB_PLATFORM_INLINE_MARKER_END,
    )


def _strip_template_sync_support_blocks_for_modules(
    relative_path: str,
    included_modules: set[str],
) -> str:
    """Return file text after applying template-sync-support marker semantics."""
    if "template-sync-support" in included_modules:
        return (REPO_ROOT / relative_path).read_text(encoding="utf-8")
    return _strip_template_sync_support_only_inline_blocks(relative_path)


def test_shared_inline_block_strip_reports_typed_marker_errors() -> None:
    """The shared inline-block helper must reject malformed marker families explicitly."""
    cases = (
        (
            UnknownInlineBlockMarkerError,
            "# template-sync: begin unknown-only\nx\n# template-sync: end unknown-only\n",
        ),
        (
            NestedInlineBlockError,
            (
                "# template-sync: begin python-only\n"
                "# template-sync: begin yaml-only\n"
                "x\n"
                "# template-sync: end yaml-only\n"
                "# template-sync: end python-only\n"
            ),
        ),
        (
            MismatchedInlineBlockError,
            "# template-sync: begin python-only\nx\n# template-sync: end yaml-only\n",
        ),
        (
            UnclosedInlineBlockError,
            "# template-sync: begin python-only\nx\n",
        ),
        (
            UnmatchedInlineBlockEndError,
            "x\n# template-sync: end python-only\n",
        ),
        (
            MissingExpectedInlineBlockError,
            "x\n",
        ),
    )

    for error_type, text in cases:
        with pytest.raises(error_type):
            remove_inline_block_family(
                text,
                "python-only",
                relative_path="fixture.txt",
            )


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


def _split_procedure_relation_cell(
    modules_cell: str,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Split a procedure ``Module(s)`` cell into ``(requires_all, requires_any)``.

    A ``requires_any`` alternative set is rendered after a ``one of`` phrase (for
    example ``plus one of``). Code spans before the phrase are ``requires_all`` and
    code spans after it are ``requires_any``; cells without the phrase are
    ``requires_all`` only. This keeps the drift check sensitive to relation kind,
    not only to module names.
    """
    marker = re.search(r"one of", modules_cell, flags=re.IGNORECASE)
    if marker is None:
        return tuple(_code_spans(modules_cell)), ()
    requires_all = tuple(_code_spans(modules_cell[: marker.start()]))
    requires_any = tuple(_code_spans(modules_cell[marker.end() :]))
    return requires_all, requires_any


def _path_mapping_relations_from_procedure() -> list[tuple[str, tuple[str, ...], tuple[str, ...]]]:
    """Return ``(pattern, requires_all, requires_any)`` rows rendered in the procedure."""
    procedure_text = PROCEDURE_PATH.read_text(encoding="utf-8")
    table_rows = _extract_table_after_heading(procedure_text, "### Path Mapping")

    rows: list[tuple[str, tuple[str, ...], tuple[str, ...]]] = []
    for pattern_cell, modules_cell in table_rows[1:]:
        patterns = _code_spans(pattern_cell)
        requires_all, requires_any = _split_procedure_relation_cell(modules_cell)
        assert patterns, f"expected at least one pattern code span in {pattern_cell!r}"
        assert (
            requires_all or requires_any
        ), f"expected at least one module code span in {modules_cell!r}"
        rows.extend((pattern, requires_all, requires_any) for pattern in patterns)
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


def _markdown_files() -> list[Path]:
    """Return Markdown files discovered under the repository root."""
    repo_root_resolved = REPO_ROOT.resolve()
    _assert_root_within_repo(REPO_ROOT, repo_root_resolved)
    paths: list[Path] = []

    for dirpath, dirnames, filenames in os.walk(REPO_ROOT, followlinks=False):
        directory = Path(dirpath)
        dirnames[:] = [
            dirname
            for dirname in dirnames
            if dirname not in SKIPPED_DISCOVERY_DIRS and not (directory / dirname).is_symlink()
        ]
        for filename in filenames:
            path = directory / filename
            if path.suffix not in MARKDOWN_FILE_SUFFIXES or path.is_symlink():
                continue
            assert path.resolve().is_relative_to(
                repo_root_resolved
            ), f"discovered Markdown path must resolve within REPO_ROOT: {path}"
            paths.append(path)

    return sorted(paths)


def _retained_markdown_files() -> list[Path]:
    """Return Markdown files whose manifest ownership is not template-onboarding."""
    retained_paths: list[Path] = []

    for path in _markdown_files():
        relative_path = path.relative_to(REPO_ROOT).as_posix()
        modules = _manifest_modules_for_path(relative_path)
        assert modules is not None, f"{relative_path} must have a manifest mapping"
        if "template-onboarding" not in modules:
            retained_paths.append(path)

    return retained_paths


def _markdown_link_targets_outside_fences(path: Path) -> list[tuple[int, str]]:
    """Return Markdown link targets that appear outside fenced code blocks."""
    targets: list[tuple[int, str]] = []
    active_fence_character: str | None = None
    active_fence_length = 0

    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        fence_match = MARKDOWN_FENCE_RE.match(line)
        if fence_match is not None:
            fence = fence_match.group("fence")
            fence_character = fence[0]
            if active_fence_character is None:
                active_fence_character = fence_character
                active_fence_length = len(fence)
            elif fence_character == active_fence_character and len(fence) >= active_fence_length:
                active_fence_character = None
                active_fence_length = 0
            continue

        if active_fence_character is not None:
            continue

        targets.extend(
            (line_number, match.group("target")) for match in MARKDOWN_INLINE_LINK_RE.finditer(line)
        )
        reference_match = MARKDOWN_REFERENCE_DEFINITION_RE.match(line)
        if reference_match is not None:
            targets.append((line_number, reference_match.group("target")))

    return targets


def _resolve_relative_markdown_target(source_path: Path, target: str) -> str | None:
    """Return a repo-relative target path for local Markdown links."""
    stripped_target = target.strip()
    if stripped_target.startswith("<") and stripped_target.endswith(">"):
        stripped_target = stripped_target[1:-1]

    parsed_target = urlsplit(stripped_target)
    if parsed_target.scheme or parsed_target.netloc or stripped_target.startswith("#"):
        return None
    if not parsed_target.path or parsed_target.path.startswith("/"):
        return None

    source_parent = source_path.relative_to(REPO_ROOT).parent.as_posix()
    if source_parent == ".":
        source_parent = ""

    normalized_path = posixpath.normpath(posixpath.join(source_parent, unquote(parsed_target.path)))
    if normalized_path in {"", "."} or normalized_path.startswith("../"):
        return None
    return normalized_path


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
    errors = _manifest_validation_errors(_load_manifest())
    assert not errors, "\n".join(f"{error.json_path}: {error.message}" for error in errors)


def test_template_manifest_schema_accepts_version_1_manifest() -> None:
    """Manifest schema must preserve version 1 ``requires_all`` compatibility."""
    manifest = _minimal_manifest_document(
        1,
        {
            "pattern": "README.md",
            "requires_all": ["baseline"],
        },
    )

    errors = _manifest_validation_errors(manifest)

    assert not errors, "\n".join(f"{error.json_path}: {error.message}" for error in errors)


def test_template_manifest_schema_accepts_version_2_requires_any() -> None:
    """Manifest schema must accept version 2 path mappings with alternatives."""
    manifest = _minimal_manifest_document(
        2,
        {
            "pattern": ".github/workflows/data-ci.yml",
            "requires_all": ["github-actions"],
            "requires_any": ["json", "yaml", "schema", "template-sync-support"],
        },
    )

    errors = _manifest_validation_errors(manifest)

    assert not errors, "\n".join(f"{error.json_path}: {error.message}" for error in errors)


def test_template_manifest_schema_rejects_malformed_relation_combinations() -> None:
    """Schema validation must reject invalid v1/v2 relation shapes."""
    invalid_manifests = [
        _minimal_manifest_document(
            1,
            {
                "pattern": ".github/workflows/data-ci.yml",
                "requires_all": ["github-actions"],
                "requires_any": ["yaml"],
            },
        ),
        _minimal_manifest_document(
            2,
            {
                "pattern": ".github/workflows/data-ci.yml",
            },
        ),
        _minimal_manifest_document(
            2,
            {
                "pattern": ".github/workflows/data-ci.yml",
                "requires_all": [],
            },
        ),
        _minimal_manifest_document(
            2,
            {
                "pattern": ".github/workflows/data-ci.yml",
                "requires_all": ["github-actions"],
                "requires_any": [],
            },
        ),
    ]

    for manifest in invalid_manifests:
        assert _manifest_validation_errors(manifest)


def test_template_manifest_data_ci_mapping_uses_v2_boolean_semantics() -> None:
    """The data-file workflow must require GitHub Actions plus one owning module."""
    data_ci_mapping = _path_mapping_by_pattern()[".github/workflows/data-ci.yml"]

    assert _relation_modules(data_ci_mapping, "requires_all") == ("github-actions",)
    assert _relation_modules(data_ci_mapping, "requires_any") == (
        "json",
        "yaml",
        "schema",
        "template-sync-support",
    )
    assert _path_mapping_matches_modules(data_ci_mapping, {"github-actions", "json"})
    assert _path_mapping_matches_modules(data_ci_mapping, {"github-actions", "yaml"})
    assert _path_mapping_matches_modules(data_ci_mapping, {"github-actions", "schema"})
    assert _path_mapping_matches_modules(
        data_ci_mapping,
        {"github-actions", "template-sync-support"},
    )
    assert not _path_mapping_matches_modules(data_ci_mapping, {"github-actions"})
    assert not _path_mapping_matches_modules(data_ci_mapping, {"yaml", "schema"})
    assert not _path_mapping_matches_modules(data_ci_mapping, {"github-actions", "terraform"})


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


def test_top_level_python_tests_map_to_python_module() -> None:
    """Top-level Python test files must not fall through the recursive glob gap."""
    assert _manifest_modules_for_path("tests/__init__.py") == ("python",)
    assert _manifest_modules_for_path("tests/test_example.py") == ("python",)


def test_template_manifest_concrete_patterns_resolve_to_tracked_files() -> None:
    """Concrete manifest patterns must point at tracked paths unless allowlisted."""
    assert CONCRETE_PATTERN_ALLOWLIST == {
        ".template-sync/marker.yml": (
            "Downstream-local retained marker; mapped because downstream repos carry "
            "it but not committed in the upstream template."
        ),
    }

    unresolved_patterns = _concrete_pattern_integrity_failures(
        REPO_ROOT,
        _load_manifest(),
        CONCRETE_PATTERN_ALLOWLIST,
    )
    failure_message = (
        "Concrete manifest patterns must resolve to tracked files or be allowlisted:\n"
        + "\n".join(unresolved_patterns)
    )

    assert not unresolved_patterns, failure_message


def test_template_manifest_flags_unallowlisted_missing_concrete_patterns(
    tmp_path: Path,
) -> None:
    """A stale concrete path in a synthetic manifest must fail integrity checks."""
    (tmp_path / "tracked.txt").write_text("tracked\n", encoding="utf-8")
    manifest = _minimal_manifest_document(
        2,
        {
            "pattern": "missing.txt",
            "requires_all": ["baseline"],
        },
    )

    unresolved_patterns = _unresolved_concrete_path_mapping_patterns(
        manifest,
        ["tracked.txt"],
        {},
    )

    assert unresolved_patterns == ["missing.txt"]


def test_downstream_marker_concrete_integrity_skips_excluded_and_overridden_patterns(
    tmp_path: Path,
) -> None:
    """Downstream marker mode checks only retained, non-overridden concrete paths."""
    _run_git(tmp_path, "init")
    manifest = _synthetic_manifest_document(
        [
            {"pattern": "README.md", "requires_all": ["baseline"]},
            {
                "pattern": ".github/workflows/data-ci.yml",
                "requires_all": ["github-actions"],
                "requires_any": ["yaml", "schema", "template-sync-support"],
            },
            {
                "pattern": "tests/fixtures/dependabot/auto-assignment.yml",
                "requires_all": ["github-platform", "schema"],
            },
            {"pattern": "modules/main.tf", "requires_all": ["terraform"]},
            {
                "pattern": "GETTING_STARTED_NEW_REPO.md",
                "requires_all": ["template-onboarding"],
            },
        ]
    )
    marker = _marker_document(
        ["baseline", "github-actions", "github-platform", "schema", "yaml"],
        local_overrides=[
            {
                "path": "tests/fixtures/dependabot/auto-assignment.yml",
                "reason": "Downstream uses live Dependabot fields outside the fixture policy.",
                "default_decision": "SKIP",
            }
        ],
    )
    _write_yaml(tmp_path, ".template-sync/manifest.yml", manifest)
    _write_yaml(tmp_path, ".template-sync/marker.yml", marker)
    _write_text(tmp_path, "README.md")
    _write_text(tmp_path, ".github/workflows/data-ci.yml")

    unresolved_patterns = _concrete_pattern_integrity_failures(
        tmp_path,
        manifest,
        CONCRETE_PATTERN_ALLOWLIST,
    )

    assert unresolved_patterns == []


def test_downstream_marker_concrete_integrity_flags_missing_retained_patterns(
    tmp_path: Path,
) -> None:
    """Downstream marker mode still fails retained concrete paths that are absent."""
    _run_git(tmp_path, "init")
    manifest = _synthetic_manifest_document(
        [
            {"pattern": "README.md", "requires_all": ["baseline"]},
            {
                "pattern": ".github/workflows/data-ci.yml",
                "requires_all": ["github-actions"],
                "requires_any": ["yaml", "schema", "template-sync-support"],
            },
        ]
    )
    marker = _marker_document(["baseline", "github-actions", "yaml"])
    _write_yaml(tmp_path, ".template-sync/manifest.yml", manifest)
    _write_yaml(tmp_path, ".template-sync/marker.yml", marker)
    _write_text(tmp_path, "README.md")

    unresolved_patterns = _concrete_pattern_integrity_failures(
        tmp_path,
        manifest,
        CONCRETE_PATTERN_ALLOWLIST,
    )

    assert unresolved_patterns == [".github/workflows/data-ci.yml"]


def test_downstream_marker_concrete_integrity_ignores_ignored_retained_files(
    tmp_path: Path,
) -> None:
    """Ignored scratch files do not satisfy retained concrete manifest mappings."""
    _run_git(tmp_path, "init")
    manifest = _synthetic_manifest_document(
        [
            {"pattern": "README.md", "requires_all": ["baseline"]},
            {"pattern": ".cache/generated.txt", "requires_all": ["baseline"]},
        ]
    )
    marker = _marker_document(["baseline"])
    _write_yaml(tmp_path, ".template-sync/manifest.yml", manifest)
    _write_yaml(tmp_path, ".template-sync/marker.yml", marker)
    _write_text(tmp_path, ".gitignore", ".cache/\n")
    _write_text(tmp_path, "README.md")
    _write_text(tmp_path, ".cache/generated.txt")

    unresolved_patterns = _concrete_pattern_integrity_failures(
        tmp_path,
        manifest,
        CONCRETE_PATTERN_ALLOWLIST,
    )

    assert unresolved_patterns == [".cache/generated.txt"]


def test_downstream_marker_concrete_integrity_agrees_with_validate_marker(
    tmp_path: Path,
) -> None:
    """The manifest helper and validator agree for the same downstream marker."""
    _run_git(tmp_path, "init")
    _copy_marker_validation_schemas(tmp_path)
    manifest = _synthetic_manifest_document(
        [
            {"pattern": "README.md", "requires_all": ["baseline"]},
            {"pattern": "tests/test_schema_examples.py", "requires_all": ["schema"]},
        ]
    )
    marker = _marker_document(["baseline", "schema"])
    _write_yaml(tmp_path, ".template-sync/manifest.yml", manifest)
    _write_yaml(tmp_path, ".template-sync/marker.yml", marker)
    _write_text(tmp_path, "README.md")

    unresolved_patterns = _concrete_pattern_integrity_failures(
        tmp_path,
        manifest,
        CONCRETE_PATTERN_ALLOWLIST,
    )
    failing_result = _run_marker_validator(tmp_path)

    assert unresolved_patterns == ["tests/test_schema_examples.py"]
    assert failing_result.returncode == 1
    assert "tests/test_schema_examples.py" in failing_result.stdout

    _write_text(tmp_path, "tests/test_schema_examples.py")

    unresolved_patterns = _concrete_pattern_integrity_failures(
        tmp_path,
        manifest,
        CONCRETE_PATTERN_ALLOWLIST,
    )
    passing_result = _run_marker_validator(tmp_path)

    assert unresolved_patterns == []
    assert passing_result.returncode == 0, passing_result.stderr


def test_template_manifest_maps_every_tracked_file() -> None:
    """Every git-tracked path must resolve through manifest matching semantics."""
    unmapped_paths = _unmapped_tracked_paths(
        _git_tracked_paths(REPO_ROOT),
        _path_mapping_rows_from_manifest(),
    )
    failure_message = (
        "Git-tracked files must resolve to a template sync manifest mapping:\n"
        + "\n".join(unmapped_paths)
    )

    assert not unmapped_paths, failure_message


def test_template_manifest_flags_unmapped_tracked_files(tmp_path: Path) -> None:
    """A tracked file with no synthetic manifest mapping must fail integrity checks."""
    _run_git(tmp_path, "init")
    (tmp_path / "mapped.txt").write_text("mapped\n", encoding="utf-8")
    (tmp_path / "unmapped.txt").write_text("unmapped\n", encoding="utf-8")
    _run_git(tmp_path, "add", "--", "mapped.txt", "unmapped.txt")
    manifest = _minimal_manifest_document(
        2,
        {
            "pattern": "mapped.txt",
            "requires_all": ["baseline"],
        },
    )

    unmapped_paths = _unmapped_tracked_paths(
        _git_tracked_paths(tmp_path),
        _path_mapping_rows_from_manifest_document(manifest),
    )

    assert unmapped_paths == ["unmapped.txt"]


def test_template_sync_helper_tests_map_to_support_module() -> None:
    """Tracked tests matching template-sync helpers must map to support."""
    expected_modules = ("template-sync-support",)
    tracked_paths = set(_git_tracked_paths(REPO_ROOT))
    helper_test_paths = sorted(
        test_path
        for helper_path in tracked_paths
        if helper_path.startswith(".template-sync/scripts/") and helper_path.endswith(".py")
        for test_path in (f"tests/test_{Path(helper_path).stem}.py",)
        if test_path in tracked_paths
    )

    assert helper_test_paths
    for helper_test_path in helper_test_paths:
        assert _manifest_modules_for_path(helper_test_path) == expected_modules


def test_schema_example_tests_map_to_schema_or_template_sync_support() -> None:
    """Schema example tests must survive either owned example-fixture surface."""
    mapping = _path_mapping_by_pattern().get("tests/test_schema_examples.py")

    assert mapping is not None
    assert _relation_modules(mapping, "requires_all") == ()
    assert _relation_modules(mapping, "requires_any") == ("schema", "template-sync-support")


def test_dependabot_schema_regression_surface_maps_to_github_platform_and_schema() -> None:
    """Dependabot schema regression files must be kept in the same manifest surface."""
    expected_modules = ("github-platform", "schema")

    assert _manifest_modules_for_path("tests/test_dependabot_schema.py") == expected_modules
    assert (
        _manifest_modules_for_path("tests/fixtures/dependabot/auto-assignment.yml")
        == expected_modules
    )


def test_template_sync_inline_markers_are_known_and_paired() -> None:
    """Both inline marker families must use known, non-nested begin/end pairs."""
    known_marker_names = {
        "terraform-only",
        "markdown-only",
        "python-only",
        "yaml-only",
        "schema-only",
        "template-sync-support-only",
        "github-platform-only",
        *REFERENCE_ONLY_MARKER_MODULES,
    }
    inline_block_paths = sorted(
        {
            *TERRAFORM_INLINE_BLOCK_PATHS,
            *MARKDOWN_INLINE_BLOCK_PATHS,
            *PYTHON_INLINE_BLOCK_PATHS,
            *YAML_INLINE_BLOCK_COUNTS,
            *SCHEMA_INLINE_BLOCK_COUNTS,
            *TEMPLATE_SYNC_SUPPORT_INLINE_BLOCK_COUNTS,
            *GITHUB_PLATFORM_INLINE_BLOCK_COUNTS,
            *(
                relative_path
                for path_counts in REFERENCE_ONLY_INLINE_BLOCK_COUNTS.values()
                for relative_path in path_counts
            ),
        }
    )

    for relative_path in inline_block_paths:
        stack: list[tuple[str, int]] = []
        text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), 1):
            match = INLINE_BLOCK_MARKER_RE.match(line)
            if match is None:
                continue
            marker_name = match.group("name")
            assert marker_name in known_marker_names, f"{relative_path}:{line_number}"
            if match.group("kind") == "begin":
                assert not stack, f"{relative_path}:{line_number}: nested inline marker"
                stack.append((marker_name, line_number))
            else:
                assert stack, f"{relative_path}:{line_number}: unmatched inline marker end"
                begin_name, begin_line = stack.pop()
                assert marker_name == begin_name, (
                    f"{relative_path}:{line_number}: end marker {marker_name!r} "
                    f"does not match begin marker {begin_name!r} from line {begin_line}"
                )
        assert not stack, f"{relative_path}: unclosed inline marker {stack[-1][0]!r}"


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


def test_template_sync_support_inline_blocks_are_declared() -> None:
    """Template-sync-support-only blocks must be paired with manifest notes."""
    mappings = _path_mapping_by_pattern()

    for relative_path, expected_count in TEMPLATE_SYNC_SUPPORT_INLINE_BLOCK_COUNTS.items():
        text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        assert text.count(TEMPLATE_SYNC_SUPPORT_INLINE_MARKER_BEGIN) == expected_count
        assert text.count(TEMPLATE_SYNC_SUPPORT_INLINE_MARKER_END) == expected_count
        _strip_template_sync_support_only_inline_blocks(relative_path)

        mapping = mappings.get(relative_path)
        assert mapping is not None, f"{relative_path} must have a manifest mapping"
        notes = mapping.get("notes")
        assert isinstance(notes, str), f"{relative_path} mapping must describe inline blocks"
        assert "Template-sync-support-only inline block" in notes
        assert "template-sync-support module is excluded" in notes


def test_sync_missing_template_sync_support_strips_support_tooling() -> None:
    """Template sync support blocks must be removed when support is absent."""
    module_sets_missing_support = (
        {"schema"},
        set(),
    )

    for (
        relative_path,
        forbidden_tokens,
    ) in TEMPLATE_SYNC_SUPPORT_SHARED_SURFACE_TOKENS.items():
        for included_modules in module_sets_missing_support:
            stripped_text = _strip_template_sync_support_blocks_for_modules(
                relative_path,
                included_modules,
            )
            for forbidden_token in forbidden_tokens:
                assert (
                    forbidden_token not in stripped_text
                ), f"{relative_path}: {sorted(included_modules)}: {forbidden_token}"


def test_sync_missing_template_sync_support_leaves_valid_yaml() -> None:
    """Stripping template sync support blocks must not corrupt the host YAML document."""
    module_sets_missing_support = (
        {"schema"},
        set(),
    )

    for relative_path in TEMPLATE_SYNC_SUPPORT_SHARED_SURFACE_TOKENS:
        for included_modules in module_sets_missing_support:
            stripped_text = _strip_template_sync_support_blocks_for_modules(
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


def test_template_sync_support_sync_retains_support_tooling() -> None:
    """A sync with template sync support must keep support validation blocks."""
    included_modules = {"template-sync-support"}

    for (
        relative_path,
        required_tokens,
    ) in TEMPLATE_SYNC_SUPPORT_SHARED_SURFACE_TOKENS.items():
        text = _strip_template_sync_support_blocks_for_modules(
            relative_path,
            included_modules,
        )
        assert text == (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        for required_token in required_tokens:
            assert required_token in text, f"{relative_path}: {required_token}"


def test_github_platform_inline_blocks_are_declared_for_template_sync() -> None:
    """GitHub-platform-only inline blocks must be paired with manifest notes."""
    mappings = _path_mapping_by_pattern()

    for relative_path, expected_count in GITHUB_PLATFORM_INLINE_BLOCK_COUNTS.items():
        text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        assert text.count(GITHUB_PLATFORM_INLINE_MARKER_BEGIN) == expected_count
        assert text.count(GITHUB_PLATFORM_INLINE_MARKER_END) == expected_count
        _strip_github_platform_only_inline_blocks(relative_path)

        mapping = mappings.get(relative_path)
        assert mapping is not None, f"{relative_path} must have a manifest mapping"
        notes = mapping.get("notes")
        assert isinstance(notes, str), f"{relative_path} mapping must describe inline blocks"
        assert "github-platform-only inline block" in notes
        assert "github-platform module is excluded" in notes


def test_non_github_platform_sync_strips_dependabot_tooling_from_shared_surfaces() -> None:
    """A simulated sync without GitHub platform must remove Dependabot validation."""
    for relative_path, forbidden_tokens in GITHUB_PLATFORM_SHARED_SURFACE_TOKENS.items():
        stripped_text = _strip_github_platform_only_inline_blocks(relative_path)
        for forbidden_token in forbidden_tokens:
            assert forbidden_token not in stripped_text, f"{relative_path}: {forbidden_token}"


def test_non_github_platform_sync_leaves_shared_surfaces_as_valid_yaml() -> None:
    """Stripping GitHub-platform-only blocks must not corrupt host YAML."""
    for relative_path in GITHUB_PLATFORM_SHARED_SURFACE_TOKENS:
        stripped_text = _strip_github_platform_only_inline_blocks(relative_path)
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


def test_github_platform_sync_retains_dependabot_tooling_in_shared_surfaces() -> None:
    """A sync that includes GitHub platform must keep Dependabot validation."""
    for relative_path, required_tokens in GITHUB_PLATFORM_SHARED_SURFACE_TOKENS.items():
        text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        for required_token in required_tokens:
            assert required_token in text, f"{relative_path}: {required_token}"


def test_reference_only_inline_blocks_are_declared_for_template_sync() -> None:
    """Reference-only inline blocks must be paired with manifest notes."""
    mappings = _path_mapping_by_pattern()

    for marker_name, path_counts in REFERENCE_ONLY_INLINE_BLOCK_COUNTS.items():
        marker_begin = _reference_only_marker_begin(marker_name)
        marker_end = _reference_only_marker_end(marker_name)
        for relative_path, expected_count in path_counts.items():
            text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
            assert text.count(marker_begin) == expected_count
            assert text.count(marker_end) == expected_count
            _strip_reference_only_inline_blocks(relative_path, marker_name)

            manifest_pattern = PROTECTED_REFERENCE_MANIFEST_PATTERNS[relative_path]
            mapping = mappings.get(manifest_pattern)
            assert mapping is not None, f"{manifest_pattern} must have a manifest mapping"
            notes = mapping.get("notes")
            assert isinstance(
                notes,
                str,
            ), f"{manifest_pattern} mapping must describe reference-only inline blocks"
            assert "*-reference-only inline blocks" in notes
            assert "when its module is excluded" in notes


def test_procedure_registers_reference_only_marker_family() -> None:
    """The sync procedure must catalog every introduced reference-only marker."""
    procedure_text = PROCEDURE_PATH.read_text(encoding="utf-8")

    assert "`*-reference-only` family" in procedure_text
    assert "same strip semantics" in procedure_text
    for marker_name in REFERENCE_ONLY_MARKER_MODULES:
        assert marker_name in procedure_text
    for relative_path in PROTECTED_REFERENCE_MANIFEST_PATTERNS:
        assert relative_path in procedure_text


def test_reference_only_pruning_removes_entry_point_optional_stack_references() -> None:
    """Simulated module exclusion must strip optional references from agent entries."""
    for marker_name, forbidden_tokens in REFERENCE_ONLY_FORBIDDEN_ENTRY_POINT_TOKENS.items():
        for relative_path in PROTECTED_ENTRY_POINT_REFERENCE_PATHS:
            stripped_text = _strip_reference_only_inline_blocks(relative_path, marker_name)
            for forbidden_token in forbidden_tokens:
                assert forbidden_token not in stripped_text, f"{relative_path}: {forbidden_token}"


def test_reference_only_pruning_preserves_platform_protocol_headings() -> None:
    """Removing all optional references must preserve retained protocol headings."""
    included_modules = {"agent-instructions"}

    for (
        relative_path,
        required_headings,
    ) in PROTECTED_PROTOCOL_HEADINGS_AFTER_REFERENCE_STRIP.items():
        stripped_text = _strip_reference_only_blocks_for_modules(relative_path, included_modules)
        for required_heading in required_headings:
            assert required_heading in stripped_text, f"{relative_path}: {required_heading}"


def test_aggregate_precommit_workflow_is_not_python_scoped() -> None:
    """The aggregate pre-commit gate must survive excluding the Python module."""
    mappings = _path_mapping_by_pattern()
    precommit_mapping = mappings.get(".github/workflows/precommit-ci.yml")
    assert precommit_mapping is not None, "precommit-ci.yml must have a manifest mapping"
    assert precommit_mapping.get("requires_all") == ["baseline", "github-actions"]


def test_repeated_precommit_repos_share_rev() -> None:
    """Repeated pre-commit ``repo:`` entries must share the same ``rev`` to avoid drift.

    ``.pre-commit-config.yaml`` declares the same external repository more than
    once when its hooks are split across template-sync modules (for example,
    ``python-jsonschema/check-jsonschema`` appears under the schema-only,
    template-sync-support-only, and GitHub-platform blocks). Dependabot's
    ``pre-commit`` ecosystem and manual edits both target each ``rev:`` line
    independently, so this test asserts that every entry for the same repository
    remains pinned to the same revision and surfaces any drift between them.
    """
    precommit_path = REPO_ROOT / ".pre-commit-config.yaml"
    precommit_config = yaml.safe_load(precommit_path.read_text(encoding="utf-8"))
    repos = precommit_config.get("repos")
    assert isinstance(repos, list), ".pre-commit-config.yaml must declare repos as a list"

    revs_by_repo: dict[str, set[str]] = {}
    for repo in repos:
        assert isinstance(repo, dict), "each pre-commit repo entry must be a mapping"
        repo_url = repo.get("repo")
        assert isinstance(repo_url, str), f"each pre-commit repo entry must define repo: {repo!r}"
        if repo_url == "local":
            continue
        rev = repo.get("rev")
        assert isinstance(rev, str), f"{repo_url}: each non-local repo entry must define rev"
        revs_by_repo.setdefault(repo_url, set()).add(rev)

    drifted = {repo_url: sorted(revs) for repo_url, revs in revs_by_repo.items() if len(revs) > 1}
    assert not drifted, (
        "Pre-commit repos declared more than once must share the same rev to "
        "avoid version drift from independent Dependabot or manual bumps:\n"
        + "\n".join(f"  {repo_url}: {revs}" for repo_url, revs in sorted(drifted.items()))
    )


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


def test_retained_markdown_files_do_not_link_relatively_to_skippable_files() -> None:
    """Retained Markdown files must not link relatively to skippable files."""
    failures: list[str] = []

    for path in _retained_markdown_files():
        source_relative_path = path.relative_to(REPO_ROOT).as_posix()
        for line_number, target in _markdown_link_targets_outside_fences(path):
            resolved_target = _resolve_relative_markdown_target(path, target)
            if resolved_target is None:
                continue
            target_modules = _manifest_modules_for_path(resolved_target)
            if resolved_target not in SKIPPABLE_OPTIONAL_REFERENCE_PATHS and (
                target_modules is None or "template-onboarding" not in target_modules
            ):
                continue
            failures.append(f"{source_relative_path}:{line_number}: {target} -> {resolved_target}")

    assert not failures, (
        "Retained Markdown files must use neutral wording or absolute upstream URLs "
        "when linking to template-onboarding-owned files or explicitly skippable "
        "optional files:\n" + "\n".join(failures)
    )


def test_template_sync_marker_schema_module_enum_matches_manifest() -> None:
    """The marker schema's baked module enum must mirror the manifest."""
    manifest_modules = [name for name, _description in _module_rows_from_manifest()]
    assert _module_enum_from_marker_schema() == manifest_modules


def test_template_manifest_filtering_semantics_are_valid() -> None:
    """The manifest must keep the version 2 filtering semantics explicit."""
    filtering = _template_manifest().get("filtering")
    assert filtering == {
        "default_semantics": "AND",
        "requires_any_semantics": "OR",
        "path_matching": "most_specific_match_wins",
        "same_specificity_action": "union_modules",
        "unmapped_action": "surface_for_owner",
    }


def test_procedure_module_definitions_match_manifest() -> None:
    """The procedure's module table must mirror the manifest exactly."""
    assert _module_rows_from_procedure() == _module_rows_from_manifest()


def test_procedure_path_mapping_matches_manifest() -> None:
    """The procedure's path mapping table must mirror the manifest exactly."""
    assert _path_mapping_relations_from_procedure() == _path_mapping_relations_from_manifest()
