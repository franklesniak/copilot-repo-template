"""Exercise the marker-aware downstream sync validation helper."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml  # type: ignore[import-untyped]

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / ".template-sync" / "scripts" / "validate_marker.py"
MARKER_SCHEMA_PATH = REPO_ROOT / "schemas" / "template-sync-marker.schema.json"
MANIFEST_SCHEMA_PATH = REPO_ROOT / "schemas" / "template-sync-manifest.schema.json"
SOURCE_REPO = "https://github.com/franklesniak/copilot-repo-template.git"
FULL_SHA = "0123456789abcdef0123456789abcdef01234567"
MODULE_DEFINITIONS = {
    "baseline": "Baseline files.",
    "agent-instructions": "Agent instruction files.",
    "template-sync-support": "Template sync support files.",
    "python": "Python files.",
    "schema": "Schema files.",
    "github-actions": "GitHub Actions files.",
    "yaml": "YAML files.",
}


def _write_text(repo_root: Path, relative_path: str, text: str = "placeholder\n") -> None:
    """Write a text file below a fixture repository root."""
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> None:
    """Write a YAML fixture below a fixture repository root."""
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _copy_schemas(repo_root: Path) -> None:
    """Copy the real marker and manifest schemas into a fixture repository."""
    schemas_dir = repo_root / "schemas"
    schemas_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(MARKER_SCHEMA_PATH, schemas_dir / MARKER_SCHEMA_PATH.name)
    shutil.copyfile(MANIFEST_SCHEMA_PATH, schemas_dir / MANIFEST_SCHEMA_PATH.name)


def _manifest(version: int = 2) -> dict[str, Any]:
    """Build a small schema-valid manifest fixture."""
    modules = [
        {"name": name, "description": description}
        for name, description in MODULE_DEFINITIONS.items()
    ]
    path_mappings: list[dict[str, Any]] = [
        {"pattern": "README.md", "requires_all": ["baseline"]},
        {"pattern": "CLAUDE.md", "requires_all": ["agent-instructions"]},
        {"pattern": "GEMINI.md", "requires_all": ["agent-instructions"]},
        {
            "pattern": ".github/copilot-instructions.md",
            "requires_all": ["agent-instructions"],
        },
        {
            "pattern": ".template-sync/marker.yml",
            "requires_all": ["template-sync-support"],
        },
        {
            "pattern": ".template-sync/manifest.yml",
            "requires_all": ["template-sync-support"],
        },
        {
            "pattern": ".template-sync/scripts/**",
            "requires_all": ["template-sync-support"],
        },
        {"pattern": "templates/python/**", "requires_all": ["python"]},
        {"pattern": "tests/test_schema_examples.py", "requires_all": ["schema"]},
    ]
    filtering: dict[str, str] = {
        "default_semantics": "AND",
        "path_matching": "most_specific_match_wins",
        "same_specificity_action": "union_modules",
        "unmapped_action": "surface_for_owner",
    }
    notes: dict[str, Any] = {
        "downstream_retention": "Downstream repositories keep marker data for syncs.",
    }

    if version == 1:
        notes["known_limitations"] = [
            {
                "path": ".github/workflows/data-ci.yml",
                "description": "Version 1 cannot model alternative module relations.",
                "future_work": "Migrate to manifest version 2 relation semantics.",
            }
        ]
    else:
        path_mappings.append(
            {
                "pattern": ".github/workflows/data-ci.yml",
                "requires_all": ["github-actions"],
                "requires_any": ["yaml", "schema", "template-sync-support"],
            }
        )
        filtering["requires_any_semantics"] = "OR"

    return {
        "template_manifest": {
            "version": version,
            "modules": modules,
            "path_mappings": path_mappings,
            "filtering": filtering,
            "notes": notes,
        }
    }


def _marker(
    included_modules: list[str],
    *,
    local_overrides: list[dict[str, str]] | None = None,
    deferred_candidates: list[dict[str, str]] | None = None,
    protected_decisions: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Build a small schema-valid marker fixture."""
    template_sync: dict[str, Any] = {
        "source_repo": SOURCE_REPO,
        "last_reviewed_template_commit": FULL_SHA,
        "included_modules": included_modules,
    }
    if local_overrides is not None:
        template_sync["local_overrides"] = local_overrides
    if deferred_candidates is not None:
        template_sync["deferred_protected_candidates"] = deferred_candidates
    if protected_decisions is not None:
        template_sync["protected_file_decisions"] = protected_decisions
    return {"template_sync": template_sync}


def _write_manifest(repo_root: Path, version: int = 2) -> None:
    """Write the manifest fixture."""
    _write_yaml(repo_root, ".template-sync/manifest.yml", _manifest(version))


def _write_marker(
    repo_root: Path,
    included_modules: list[str],
    *,
    local_overrides: list[dict[str, str]] | None = None,
    deferred_candidates: list[dict[str, str]] | None = None,
    protected_decisions: list[dict[str, str]] | None = None,
) -> None:
    """Write the marker fixture."""
    _write_yaml(
        repo_root,
        ".template-sync/marker.yml",
        _marker(
            included_modules,
            local_overrides=local_overrides,
            deferred_candidates=deferred_candidates,
            protected_decisions=protected_decisions,
        ),
    )


def _run_validator(repo_root: Path, *extra_args: str) -> subprocess.CompletedProcess[str]:
    """Run the helper against a fixture repository."""
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--repo-root",
            str(repo_root),
            *extra_args,
        ],
        check=False,
        capture_output=True,
        text=True,
    )


def _run_git(repo_root: Path, *args: str) -> None:
    """Run a git command in a fixture repository."""
    subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


@pytest.fixture()
def marker_repo(tmp_path: Path) -> Path:
    """Create a fixture repository with schemas and a manifest."""
    _run_git(tmp_path, "init")
    _copy_schemas(tmp_path)
    _write_manifest(tmp_path)
    return tmp_path


def test_fully_included_template_state_passes(marker_repo: Path) -> None:
    """All retained concrete paths and present glob files are accepted."""
    _write_marker(
        marker_repo,
        ["baseline", "template-sync-support", "python", "schema", "github-actions"],
    )
    _write_text(marker_repo, "README.md")
    _write_text(marker_repo, ".template-sync/scripts/validate_marker.py")
    _write_text(marker_repo, "templates/python/app.py")
    _write_text(marker_repo, "tests/test_schema_examples.py")
    _write_text(marker_repo, ".github/workflows/data-ci.yml")

    result = _run_validator(marker_repo)

    assert result.returncode == 0, result.stderr
    assert "Marker-aware template sync validation passed." in result.stdout
    assert "No retained-template inconsistencies found." in result.stdout


def test_partial_module_exclusion_without_leftovers_passes(marker_repo: Path) -> None:
    """Excluded glob modules do not imply every possible glob match must exist."""
    _write_marker(marker_repo, ["baseline", "template-sync-support"])
    _write_text(marker_repo, "README.md")

    result = _run_validator(marker_repo)

    assert result.returncode == 0, result.stderr
    assert "Marker-aware template sync validation passed." in result.stdout


def test_absent_marker_skips_by_default_and_fails_when_required(tmp_path: Path) -> None:
    """A missing marker is a no-op unless CI explicitly requires one."""
    result = _run_validator(tmp_path)
    required_result = _run_validator(tmp_path, "--require-marker")

    assert result.returncode == 0, result.stderr
    assert "No marker found at .template-sync/marker.yml" in result.stdout
    assert required_result.returncode == 1
    assert "Marker is required but was not found" in required_result.stderr


def test_malformed_marker_data_is_rejected(marker_repo: Path) -> None:
    """Present marker files must pass the existing marker schema."""
    _write_yaml(
        marker_repo,
        ".template-sync/marker.yml",
        _marker(["not-a-real-module"]),
    )

    result = _run_validator(marker_repo)

    assert result.returncode == 1
    assert "Schema validation failed for .template-sync/marker.yml" in result.stderr


def test_missing_concrete_mapped_file_fails(marker_repo: Path) -> None:
    """Concrete retained mappings must exist on disk."""
    _write_marker(marker_repo, ["baseline", "template-sync-support", "schema"])
    _write_text(marker_repo, "README.md")

    result = _run_validator(marker_repo)

    assert result.returncode == 1
    assert "Concrete mapped files expected for included modules but missing" in result.stdout
    assert "tests/test_schema_examples.py" in result.stdout


def test_untracked_nonignored_concrete_file_counts_as_present(marker_repo: Path) -> None:
    """Untracked retained files are accepted when Git does not ignore them."""
    _write_marker(marker_repo, ["baseline", "template-sync-support", "schema"])
    _write_text(marker_repo, "README.md")
    _write_text(marker_repo, "tests/test_schema_examples.py")

    result = _run_validator(marker_repo)

    assert result.returncode == 0, result.stderr
    assert "Marker-aware template sync validation passed." in result.stdout


def test_ignored_retained_concrete_file_is_reported_missing(marker_repo: Path) -> None:
    """Ignored files do not satisfy retained concrete manifest mappings."""
    _write_marker(marker_repo, ["baseline", "template-sync-support", "schema"])
    _write_text(marker_repo, ".gitignore", "tests/test_schema_examples.py\n")
    _write_text(marker_repo, "README.md")
    _write_text(marker_repo, "tests/test_schema_examples.py")

    result = _run_validator(marker_repo)

    assert result.returncode == 1
    assert "Concrete mapped files expected for included modules but missing" in result.stdout
    assert "tests/test_schema_examples.py" in result.stdout


def test_leftover_file_from_excluded_module_fails(marker_repo: Path) -> None:
    """Existing files mapped only to excluded modules are reported."""
    _write_marker(marker_repo, ["baseline", "template-sync-support"])
    _write_text(marker_repo, "README.md")
    _write_text(marker_repo, "templates/python/app.py")

    result = _run_validator(marker_repo)

    assert result.returncode == 1
    assert "Files present on disk but not retained by included modules" in result.stdout
    assert "templates/python/app.py" in result.stdout


def test_local_overrides_skip_matching_paths(marker_repo: Path) -> None:
    """Local override paths are omitted from retained-template consistency checks."""
    _write_marker(
        marker_repo,
        ["baseline", "template-sync-support"],
        local_overrides=[
            {
                "path": "templates/python/",
                "reason": "Local project owns this directory.",
                "default_decision": "SKIP",
            }
        ],
    )
    _write_text(marker_repo, "README.md")
    _write_text(marker_repo, "templates/python/app.py")

    result = _run_validator(marker_repo)

    assert result.returncode == 0, result.stderr
    assert "Local overrides skipped:" in result.stdout
    assert "templates/python/ (SKIP): Local project owns this directory." in result.stdout


def test_deferred_protected_candidates_are_reported_without_failure(marker_repo: Path) -> None:
    """Deferred protected candidates are visible but do not create failures."""
    _write_marker(
        marker_repo,
        ["baseline", "template-sync-support"],
        deferred_candidates=[
            {
                "path": ".github/copilot-instructions.md",
                "source_commit": "89abcdef0123456789abcdef0123456789abcdef",
                "reason": "Owner authorization is still pending.",
            }
        ],
    )
    _write_text(marker_repo, "README.md")

    result = _run_validator(marker_repo)

    assert result.returncode == 0, result.stderr
    assert "Deferred protected candidates:" in result.stdout
    assert ".github/copilot-instructions.md" in result.stdout


def test_manifest_v2_requires_any_relation_is_consumed(marker_repo: Path) -> None:
    """Version 2 mappings retain a file when one requires_any module is included."""
    _write_marker(marker_repo, ["baseline", "template-sync-support", "github-actions", "yaml"])
    _write_text(marker_repo, "README.md")
    _write_text(marker_repo, ".github/workflows/data-ci.yml")

    result = _run_validator(marker_repo)

    assert result.returncode == 0, result.stderr
    assert "Marker-aware template sync validation passed." in result.stdout


def test_manifest_v1_requires_all_semantics_are_consumed(tmp_path: Path) -> None:
    """Version 1 mappings continue to use requires_all-only semantics."""
    _run_git(tmp_path, "init")
    _copy_schemas(tmp_path)
    _write_manifest(tmp_path, version=1)
    _write_marker(tmp_path, ["baseline", "template-sync-support"])
    _write_text(tmp_path, "README.md")

    result = _run_validator(tmp_path)

    assert result.returncode == 0, result.stderr
    assert "Marker-aware template sync validation passed." in result.stdout


def test_protected_file_decisions_and_remove_local_authorizations_are_reported(
    marker_repo: Path,
) -> None:
    """Protected-file decisions and removal authorizations are visible."""
    _write_marker(
        marker_repo,
        ["template-sync-support"],
        protected_decisions=[
            {
                "path": "CLAUDE.md",
                "decision": "MERGE",
                "adoption_mode": "minimal-preservation",
                "authorization_basis": "Owner authorized protected edits on 2026-05-27.",
                "authorized_scope": "CLAUDE.md only.",
            },
            {
                "path": "GEMINI.md",
                "decision": "REMOVE-LOCAL",
                "authorization_basis": "Owner explicitly authorized removing GEMINI.md.",
                "authorized_scope": "GEMINI.md only.",
                "reason": "Gemini agent not used by this repository.",
            },
        ],
    )

    result = _run_validator(marker_repo)

    assert result.returncode == 0, result.stderr
    assert "Protected file decisions:" in result.stdout
    assert "CLAUDE.md: MERGE" in result.stdout
    assert "REMOVE-LOCAL authorizations:" in result.stdout
    assert "authorization_basis: Owner explicitly authorized removing GEMINI.md." in result.stdout
    assert "authorized_scope: GEMINI.md only." in result.stdout
    assert "reason: Gemini agent not used by this repository." in result.stdout


def test_duplicate_protected_decision_paths_fail(marker_repo: Path) -> None:
    """Protected-file decisions must not repeat normalized paths."""
    _write_marker(
        marker_repo,
        ["template-sync-support"],
        protected_decisions=[
            {
                "path": "CLAUDE.md",
                "decision": "SKIP",
                "reason": "Claude agent is not used.",
            },
            {
                "path": "CLAUDE.md",
                "decision": "PROTECTED-REVIEW",
                "reason": "Owner authorization is pending.",
            },
        ],
    )

    result = _run_validator(marker_repo)

    assert result.returncode == 1
    assert "Duplicate protected_file_decisions path(s): CLAUDE.md" in result.stderr


def test_directory_style_protected_decision_path_fails(marker_repo: Path) -> None:
    """Protected-file decisions must reference a file, not a directory."""
    _write_marker(
        marker_repo,
        ["template-sync-support"],
        protected_decisions=[
            {
                "path": ".github/instructions/",
                "decision": "MERGE",
                "adoption_mode": "minimal-preservation",
                "authorization_basis": "Owner authorized protected edits on 2026-05-27.",
                "authorized_scope": ".github/instructions/ only.",
            }
        ],
    )

    result = _run_validator(marker_repo)

    assert result.returncode == 1
    assert "Schema validation failed for .template-sync/marker.yml" in result.stderr
    assert (
        ".template_sync.protected_file_decisions[0].path" in result.stderr
        or "template_sync.protected_file_decisions[0].path" in result.stderr
    )


def test_directory_style_deferred_candidate_path_fails(marker_repo: Path) -> None:
    """Deferred protected candidates must reference a file, not a directory."""
    _write_marker(
        marker_repo,
        ["template-sync-support"],
        deferred_candidates=[
            {
                "path": ".github/instructions/",
                "source_commit": FULL_SHA,
                "reason": "Protected governance directory needs explicit owner authorization.",
            }
        ],
    )

    result = _run_validator(marker_repo)

    assert result.returncode == 1
    assert "Schema validation failed for .template-sync/marker.yml" in result.stderr
    assert (
        ".template_sync.deferred_protected_candidates[0].path" in result.stderr
        or "template_sync.deferred_protected_candidates[0].path" in result.stderr
    )


def test_noncontradictory_protected_decision_local_override_overlap_is_reported(
    marker_repo: Path,
) -> None:
    """Same-decision protected decisions and local overrides are shown together."""
    _write_marker(
        marker_repo,
        ["template-sync-support"],
        local_overrides=[
            {
                "path": "CLAUDE.md",
                "reason": "Claude agent is downstream-owned.",
                "default_decision": "SKIP",
            }
        ],
        protected_decisions=[
            {
                "path": "CLAUDE.md",
                "decision": "SKIP",
                "reason": "Claude agent is not used.",
            }
        ],
    )

    result = _run_validator(marker_repo)

    assert result.returncode == 0, result.stderr
    assert "Protected decision overlaps:" in result.stdout
    assert "protected_file_decisions: decision=SKIP; reason=Claude agent is not used." in (
        result.stdout
    )
    assert (
        "local_overrides: path=CLAUDE.md; default_decision=SKIP; "
        "reason=Claude agent is downstream-owned."
    ) in result.stdout


def test_contradictory_protected_decision_local_override_overlap_fails(
    marker_repo: Path,
) -> None:
    """Different same-path protected and local override decisions are contradictory."""
    _write_marker(
        marker_repo,
        ["template-sync-support"],
        local_overrides=[
            {
                "path": "CLAUDE.md",
                "reason": "Claude agent is downstream-owned.",
                "default_decision": "SKIP",
            }
        ],
        protected_decisions=[
            {
                "path": "CLAUDE.md",
                "decision": "MERGE",
                "adoption_mode": "minimal-preservation",
                "authorization_basis": "Owner authorized protected edits on 2026-05-27.",
                "authorized_scope": "CLAUDE.md only.",
            }
        ],
    )

    result = _run_validator(marker_repo)

    assert result.returncode == 1
    assert "Contradictory protected-file marker entries:" in result.stderr
    assert "protected_file_decisions: decision=MERGE" in result.stderr
    assert "local_overrides: path=CLAUDE.md; default_decision=SKIP" in result.stderr


def test_protected_decision_deferred_candidate_overlap_fails(marker_repo: Path) -> None:
    """A current protected decision cannot also be deferred for the same path."""
    _write_marker(
        marker_repo,
        ["template-sync-support"],
        deferred_candidates=[
            {
                "path": "CLAUDE.md",
                "source_commit": "89abcdef0123456789abcdef0123456789abcdef",
                "reason": "Owner authorization is pending.",
            }
        ],
        protected_decisions=[
            {
                "path": "CLAUDE.md",
                "decision": "PROTECTED-REVIEW",
                "reason": "Owner authorization is pending.",
            }
        ],
    )

    result = _run_validator(marker_repo)

    assert result.returncode == 1
    assert "Contradictory protected-file marker entries:" in result.stderr
    assert "deferred_protected_candidates: source_commit=89abcdef" in result.stderr


def test_strict_remove_local_phrasing_is_opt_in_and_token_configurable(
    marker_repo: Path,
) -> None:
    """Strict removal phrasing fails only when opted in and no token matches."""
    _write_marker(
        marker_repo,
        ["template-sync-support"],
        protected_decisions=[
            {
                "path": "GEMINI.md",
                "decision": "REMOVE-LOCAL",
                "authorization_basis": "Owner approved GEMINI.md retirement.",
                "authorized_scope": "GEMINI.md only.",
                "reason": "Gemini agent not used by this repository.",
            }
        ],
    )

    default_result = _run_validator(marker_repo)
    strict_result = _run_validator(marker_repo, "--strict-remove-local-phrasing")
    custom_result = _run_validator(
        marker_repo,
        "--strict-remove-local-phrasing",
        "--remove-local-authorization-token",
        "retire",
    )

    assert default_result.returncode == 0, default_result.stderr
    assert strict_result.returncode == 1
    assert "GEMINI.md REMOVE-LOCAL authorization_basis must contain" in strict_result.stderr
    assert custom_result.returncode == 0, custom_result.stderr
