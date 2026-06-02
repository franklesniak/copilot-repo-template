"""Exercise shared template-sync materialization planning helpers."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest
import yaml  # type: ignore[import-untyped]

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = REPO_ROOT / ".template-sync" / "scripts"
MANIFEST_SCHEMA_PATH = REPO_ROOT / "schemas" / "template-sync-manifest.schema.json"
MARKER_SCHEMA_PATH = REPO_ROOT / "schemas" / "template-sync-marker.schema.json"

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from template_sync_materialization_helpers import (  # noqa: E402
    MissingExpectedInlineBlockError,
    RepositoryPathError,
    classify_repository_file,
    is_excluded_template_path,
    is_protected_instruction_path,
    is_retained_template_path,
    is_template_managed_path,
    load_validated_manifest,
    load_validated_marker_decision_data,
    parse_manifest_mappings,
    remove_inline_block_family,
    resolve_safe_repository_target_path,
    selected_relation_for_path,
)

SOURCE_REPO = "https://github.com/franklesniak/copilot-repo-template.git"
FULL_SHA = "0123456789abcdef0123456789abcdef01234567"


def _manifest(path_mappings: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a small schema-shaped manifest fixture."""
    return {
        "template_manifest": {
            "version": 2,
            "modules": [
                {"name": "baseline", "description": "Baseline files."},
                {"name": "python", "description": "Python files."},
                {"name": "yaml", "description": "YAML files."},
                {"name": "schema", "description": "Schema files."},
                {
                    "name": "template-sync-support",
                    "description": "Template sync support files.",
                },
            ],
            "path_mappings": path_mappings,
            "filtering": {
                "default_semantics": "AND",
                "requires_any_semantics": "OR",
                "path_matching": "most_specific_match_wins",
                "same_specificity_action": "union_modules",
                "unmapped_action": "surface_for_owner",
            },
            "notes": {
                "downstream_retention": "Downstream repositories keep marker data.",
            },
        }
    }


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> None:
    """Write YAML below a fixture repository root."""
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _marker(included_modules: list[str]) -> dict[str, Any]:
    """Build a marker-shaped decision fixture."""
    return {
        "template_sync": {
            "source_repo": SOURCE_REPO,
            "last_reviewed_template_commit": FULL_SHA,
            "included_modules": included_modules,
            "local_overrides": [
                {
                    "path": "local/",
                    "default_decision": "SKIP",
                    "reason": "Local project owns this directory.",
                }
            ],
            "protected_file_decisions": [
                {
                    "path": "AGENTS.md",
                    "decision": "MERGE",
                    "adoption_mode": "minimal-preservation",
                    "authorization_basis": "Owner authorized protected edits.",
                    "authorized_scope": "AGENTS.md only.",
                }
            ],
        }
    }


def test_manifest_relation_selection_uses_specificity_union_and_module_logic() -> None:
    """Path mapping resolution keeps existing manifest filtering semantics."""
    _module_names, mappings = parse_manifest_mappings(
        _manifest(
            [
                {"pattern": "configs/**", "requires_all": ["baseline"]},
                {"pattern": "configs/app.yml", "requires_all": ["yaml"]},
                {"pattern": "configs/app.yml", "requires_all": ["schema"]},
                {"pattern": "shared.yml", "requires_all": ["baseline"]},
                {"pattern": "shared.yml", "requires_any": ["yaml", "schema"]},
            ]
        )
    )

    relation = selected_relation_for_path("configs/app.yml", mappings)
    assert relation is not None
    assert relation.patterns == ("configs/app.yml", "configs/app.yml")
    assert relation.requires_all == frozenset({"yaml", "schema"})
    assert relation.requires_any == frozenset()
    assert relation.is_retained_by({"yaml", "schema"})
    assert not relation.is_retained_by({"yaml"})

    shared_relation = selected_relation_for_path("shared.yml", mappings)
    assert shared_relation is not None
    assert shared_relation.is_retained_by({"baseline", "yaml"})
    assert shared_relation.is_retained_by({"baseline", "schema"})
    assert not shared_relation.is_retained_by({"baseline"})


def test_manifest_loader_schema_validates_real_manifest() -> None:
    """The helper can load and schema-validate the checked-in manifest."""
    modules, mappings = load_validated_manifest(
        REPO_ROOT,
        REPO_ROOT / ".template-sync" / "manifest.yml",
        MANIFEST_SCHEMA_PATH,
    )

    assert "template-sync-support" in modules
    assert selected_relation_for_path(".template-sync/scripts/validate_marker.py", mappings)


def test_marker_loader_schema_validates_decision_data(tmp_path: Path) -> None:
    """Marker-shaped decision data is loaded, schema-validated, and parsed."""
    _write_yaml(tmp_path, ".template-sync/marker.yml", _marker(["baseline"]))

    marker_data = load_validated_marker_decision_data(
        tmp_path,
        tmp_path / ".template-sync" / "marker.yml",
        MARKER_SCHEMA_PATH,
        validate_protected_decision_integrity=True,
    )

    assert marker_data.included_modules == frozenset({"baseline"})
    assert marker_data.local_overrides[0].matches("local/file.txt")
    assert marker_data.protected_decisions[0].path == "AGENTS.md"


def test_mapping_classification_identifies_retained_excluded_and_unmapped_paths() -> None:
    """Shared helpers distinguish mapped, retained, excluded, and unmapped paths."""
    _module_names, mappings = parse_manifest_mappings(
        _manifest(
            [
                {"pattern": "README.md", "requires_all": ["baseline"]},
                {"pattern": "templates/python/**", "requires_all": ["python"]},
            ]
        )
    )
    included_modules = {"baseline"}

    assert is_template_managed_path("README.md", mappings)
    assert is_retained_template_path("README.md", mappings, included_modules)
    assert is_excluded_template_path("templates/python/app.py", mappings, included_modules)
    assert not is_template_managed_path("docs/unmapped.md", mappings)


def test_protected_file_classification_uses_shared_rules() -> None:
    """Protected instruction path classification follows repository governance rules."""
    assert is_protected_instruction_path(".github/copilot-instructions.md")
    assert is_protected_instruction_path(".github/instructions/python.instructions.md")
    assert is_protected_instruction_path(".cursor/rules/repository-instructions.mdc")
    assert not is_protected_instruction_path("README.md")


def test_inline_block_removal_preserves_blank_line_hygiene() -> None:
    """Removing an inline block collapses lint-hostile blank-line runs."""
    text = (
        "top\n"
        "\n"
        "# template-sync: begin python-only\n"
        "removed\n"
        "# template-sync: end python-only\n"
        "\n"
        "\n"
        "\n"
        "bottom\n"
    )

    assert (
        remove_inline_block_family(text, "python-only", relative_path="fixture.yml")
        == "top\n\n\nbottom\n"
    )


def test_inline_block_removal_requires_expected_family() -> None:
    """Materialization callers get a typed error when an expected family is absent."""
    with pytest.raises(MissingExpectedInlineBlockError):
        remove_inline_block_family("plain\n", "python-only", relative_path="fixture.yml")


def test_text_versus_byte_only_classification_preserves_bytes(tmp_path: Path) -> None:
    """Only safe UTF-8 files without NUL bytes are transformable text."""
    text_path = tmp_path / "docs" / "note.txt"
    text_path.parent.mkdir(parents=True)
    text_path.write_bytes(b"hello\n")
    invalid_bytes = b"\xff\xfe\x00binary"
    byte_path = tmp_path / "assets" / "blob.bin"
    byte_path.parent.mkdir(parents=True)
    byte_path.write_bytes(invalid_bytes)

    text_classification = classify_repository_file(tmp_path, "docs/note.txt")
    byte_classification = classify_repository_file(tmp_path, "assets/blob.bin")

    assert text_classification.is_transformable_text
    assert text_classification.text == "hello\n"
    assert byte_classification.is_byte_only
    assert byte_classification.bytes_content == invalid_bytes
    assert byte_classification.text is None


def test_path_safety_rejects_traversal_absolute_backslash_and_symlink(
    tmp_path: Path,
) -> None:
    """Safe target resolution rejects paths that can escape the repository."""
    for raw_path in ("../outside.txt", "/absolute.txt", r"dir\file.txt"):
        with pytest.raises(RepositoryPathError):
            resolve_safe_repository_target_path(tmp_path, raw_path)

    outside = tmp_path.parent / "outside-target"
    outside.mkdir(exist_ok=True)
    symlink_path = tmp_path / "linked"
    try:
        symlink_path.symlink_to(outside, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"Symlink creation unavailable in this environment: {error}")

    with pytest.raises(RepositoryPathError):
        resolve_safe_repository_target_path(tmp_path, "linked/file.txt")
