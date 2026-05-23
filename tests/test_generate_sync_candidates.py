"""Exercise the marker-aware sync candidate table generator."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / ".template-sync" / "scripts" / "generate_sync_candidates.py"
MARKER_SCHEMA_PATH = REPO_ROOT / "schemas" / "template-sync-marker.schema.json"
MANIFEST_SCHEMA_PATH = REPO_ROOT / "schemas" / "template-sync-manifest.schema.json"
SOURCE_REPO = "https://github.com/franklesniak/copilot-repo-template.git"
MODULE_DEFINITIONS = {
    "baseline": "Baseline files.",
    "agent-instructions": "Agent instruction files.",
    "github-actions": "GitHub Actions workflows.",
    "template-sync-support": "Template sync support files.",
    "markdown": "Markdown files.",
    "python": "Python files.",
    "json": "JSON files.",
    "yaml": "YAML files.",
    "schema": "Schema files.",
}


def _run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run a test command and capture text output."""
    return subprocess.run(
        command,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )


def _git(repo_root: Path, *args: str) -> str:
    """Run a Git command in a fixture repository and return stdout."""
    result = _run(["git", *args], repo_root)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


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


def _manifest(
    *,
    version: int = 2,
    extra_mappings: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a small schema-valid manifest fixture."""
    path_mappings: list[dict[str, Any]] = [
        {"pattern": "README.md", "requires_all": ["baseline"]},
        {
            "pattern": ".github/copilot-instructions.md",
            "requires_all": ["agent-instructions"],
        },
        {
            "pattern": ".pre-commit-config.yaml",
            "requires_all": ["baseline"],
            "notes": "Contains a Python-only inline block for the python module.",
        },
        {"pattern": ".template-sync/scripts/**", "requires_all": ["template-sync-support"]},
        {"pattern": "templates/markdown/**", "requires_all": ["markdown"]},
        {"pattern": "templates/python/**", "requires_all": ["python"]},
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
        path_mappings.append(
            {
                "pattern": ".github/workflows/data-ci.yml",
                "requires_all": ["github-actions", "yaml"],
            }
        )
        notes["known_limitations"] = [
            {
                "path": ".github/workflows/data-ci.yml",
                "description": "Version 1 cannot model alternative module relations.",
                "future_work": "Migrate to manifest version 2 relation semantics.",
            }
        ]
    elif version == 2:
        path_mappings.append(
            {
                "pattern": ".github/workflows/data-ci.yml",
                "requires_all": ["github-actions"],
                "requires_any": ["json", "yaml", "schema"],
            }
        )
        filtering["requires_any_semantics"] = "OR"
    else:
        raise ValueError(f"Unsupported manifest version: {version}")

    if extra_mappings is not None:
        path_mappings.extend(extra_mappings)

    return {
        "template_manifest": {
            "version": version,
            "modules": [
                {"name": name, "description": description}
                for name, description in MODULE_DEFINITIONS.items()
            ],
            "path_mappings": path_mappings,
            "filtering": filtering,
            "notes": notes,
        }
    }


def _marker(
    included_modules: list[str],
    *,
    last_reviewed_template_commit: str | None,
    local_overrides: list[dict[str, str]] | None = None,
    deferred_candidates: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Build a small schema-valid marker fixture."""
    template_sync: dict[str, Any] = {
        "source_repo": SOURCE_REPO,
        "included_modules": included_modules,
    }
    if last_reviewed_template_commit is not None:
        template_sync["last_reviewed_template_commit"] = last_reviewed_template_commit
    if local_overrides is not None:
        template_sync["local_overrides"] = local_overrides
    if deferred_candidates is not None:
        template_sync["deferred_protected_candidates"] = deferred_candidates
    return {"template_sync": template_sync}


def _init_repo(
    repo_root: Path,
    *,
    manifest_version: int = 2,
    extra_mappings: list[dict[str, Any]] | None = None,
) -> None:
    """Create a fixture Git repository with schemas and a manifest."""
    _git(repo_root, "init")
    _git(repo_root, "config", "user.name", "Template Sync Tests")
    _git(repo_root, "config", "user.email", "template-sync-tests@example.invalid")
    _copy_schemas(repo_root)
    _write_yaml(
        repo_root,
        ".template-sync/manifest.yml",
        _manifest(version=manifest_version, extra_mappings=extra_mappings),
    )


def _commit_all(repo_root: Path, message: str) -> str:
    """Commit all fixture repository changes and return the commit SHA."""
    _git(repo_root, "add", ".")
    _git(repo_root, "commit", "-m", message)
    return _git(repo_root, "rev-parse", "HEAD")


def _run_generator(repo_root: Path, *extra_args: str) -> subprocess.CompletedProcess[str]:
    """Run the candidate generator against a fixture repository."""
    return _run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--repo-root",
            str(repo_root),
            *extra_args,
        ],
        repo_root,
    )


def test_no_changes_reports_empty_range(tmp_path: Path) -> None:
    """A clean reviewed range produces a clear empty report."""
    _init_repo(tmp_path)
    _write_text(tmp_path, "README.md", "base\n")
    base_sha = _commit_all(tmp_path, "base")
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        _marker(["baseline"], last_reviewed_template_commit=base_sha),
    )

    result = _run_generator(tmp_path, "--range-head", base_sha)

    assert result.returncode == 0, result.stderr
    assert "# Template Sync Candidate Table" in result.stdout
    assert "No changed paths found in the reviewed range." in result.stdout


def test_normal_mixed_change_set_reports_marker_and_manifest_decisions(tmp_path: Path) -> None:
    """Retained, excluded, cross-module, and inline-note rows appear together."""
    _init_repo(tmp_path)
    _write_text(tmp_path, "README.md", "base\n")
    _write_text(tmp_path, ".github/workflows/data-ci.yml", "name: data\n")
    _write_text(tmp_path, ".pre-commit-config.yaml", "repos: []\n")
    _write_text(tmp_path, "templates/python/app.py", "print('base')\n")
    base_sha = _commit_all(tmp_path, "base")

    _write_text(tmp_path, "README.md", "head\n")
    _write_text(tmp_path, ".github/workflows/data-ci.yml", "name: data updated\n")
    _write_text(tmp_path, ".pre-commit-config.yaml", "repos:\n  - repo: local\n")
    _write_text(tmp_path, "templates/python/app.py", "print('head')\n")
    head_sha = _commit_all(tmp_path, "head")
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        _marker(
            ["baseline", "github-actions", "yaml", "template-sync-support"],
            last_reviewed_template_commit=base_sha,
        ),
    )

    result = _run_generator(tmp_path, "--range-head", head_sha)

    assert result.returncode == 0, result.stderr
    assert f"git diff --name-status -M {base_sha}..{head_sha} --" in result.stdout
    assert "| README.md | Modified | requires all: baseline | Retained |" in result.stdout
    assert "requires all: github-actions; requires any: json, schema, yaml" in result.stdout
    assert "Cross-module manifest relation matched." in result.stdout
    assert (
        "| templates/python/app.py | Modified | requires all: python | Excluded |" in result.stdout
    )
    assert "Manifest note: Contains a Python-only inline block" in result.stdout


def test_manifest_v1_requires_all_rows_are_supported(tmp_path: Path) -> None:
    """Version 1 manifests retain requires_all-only relation semantics."""
    _init_repo(tmp_path, manifest_version=1)
    _write_text(tmp_path, ".github/workflows/data-ci.yml", "name: data\n")
    base_sha = _commit_all(tmp_path, "base")
    _write_text(tmp_path, ".github/workflows/data-ci.yml", "name: data updated\n")
    head_sha = _commit_all(tmp_path, "head")
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        _marker(["github-actions", "yaml"], last_reviewed_template_commit=base_sha),
    )

    result = _run_generator(tmp_path, "--range-head", head_sha)

    assert result.returncode == 0, result.stderr
    assert (
        "| .github/workflows/data-ci.yml | Modified | "
        "requires all: github-actions, yaml | Retained |"
    ) in result.stdout


def test_explicit_range_base_allows_marker_without_last_reviewed(tmp_path: Path) -> None:
    """First-sync delta reviews can pass an explicit base when the marker lacks one."""
    _init_repo(tmp_path)
    _write_text(tmp_path, "README.md", "base\n")
    base_sha = _commit_all(tmp_path, "base")
    _write_text(tmp_path, "README.md", "head\n")
    head_sha = _commit_all(tmp_path, "head")
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        _marker(["baseline"], last_reviewed_template_commit=None),
    )

    result = _run_generator(tmp_path, "--range-base", base_sha, "--range-head", head_sha)

    assert result.returncode == 0, result.stderr
    assert f"- Range base: `{base_sha}` from `{base_sha}` (--range-base)" in result.stdout
    assert f"git diff --name-status -M {base_sha}..{head_sha} --" in result.stdout
    assert "| README.md | Modified | requires all: baseline | Retained |" in result.stdout


def test_matching_local_procedure_does_not_warn(tmp_path: Path) -> None:
    """The procedure warning is quiet when local text matches range-head upstream."""
    _init_repo(tmp_path)
    _write_text(tmp_path, "README.md", "base\n")
    _write_text(tmp_path, "TEMPLATE_UPDATE_PROCEDURE.md", "procedure v1\n")
    base_sha = _commit_all(tmp_path, "base")
    _write_text(tmp_path, "README.md", "head\n")
    head_sha = _commit_all(tmp_path, "head")
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        _marker(["baseline"], last_reviewed_template_commit=base_sha),
    )

    result = _run_generator(tmp_path, "--range-head", head_sha)

    assert result.returncode == 0, result.stderr
    assert "WARNING: Local `TEMPLATE_UPDATE_PROCEDURE.md` may be stale" not in result.stdout
    assert f"git show {head_sha}:TEMPLATE_UPDATE_PROCEDURE.md" not in result.stdout


def test_stale_local_procedure_warns_with_upstream_show_command(tmp_path: Path) -> None:
    """A stale local procedure produces a non-fatal warning with a copyable command."""
    _init_repo(tmp_path)
    _write_text(tmp_path, "README.md", "base\n")
    _write_text(tmp_path, "TEMPLATE_UPDATE_PROCEDURE.md", "procedure v1\n")
    base_sha = _commit_all(tmp_path, "base")
    _write_text(tmp_path, "README.md", "head\n")
    _write_text(tmp_path, "TEMPLATE_UPDATE_PROCEDURE.md", "procedure v2\n")
    head_sha = _commit_all(tmp_path, "head")
    _write_text(tmp_path, "TEMPLATE_UPDATE_PROCEDURE.md", "procedure v1\n")
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        _marker(["baseline"], last_reviewed_template_commit=base_sha),
    )

    result = _run_generator(tmp_path, "--range-head", head_sha)

    assert result.returncode == 0, result.stderr
    assert "WARNING: Local `TEMPLATE_UPDATE_PROCEDURE.md` may be stale" in result.stdout
    assert f"git show {head_sha}:TEMPLATE_UPDATE_PROCEDURE.md" in result.stdout
    assert "| README.md | Modified | requires all: baseline | Retained |" in result.stdout


def test_missing_range_base_errors_when_marker_has_no_last_reviewed(tmp_path: Path) -> None:
    """The generator refuses to guess a baseline."""
    _init_repo(tmp_path)
    _write_text(tmp_path, "README.md", "base\n")
    _commit_all(tmp_path, "base")
    _write_text(tmp_path, "README.md", "head\n")
    head_sha = _commit_all(tmp_path, "head")
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        _marker(["baseline"], last_reviewed_template_commit=None),
    )

    result = _run_generator(tmp_path, "--range-head", head_sha)

    assert result.returncode == 1
    assert "No range base was provided" in result.stderr
    assert "will not guess a baseline" in result.stderr


def test_default_range_head_uses_local_template_main_ref(tmp_path: Path) -> None:
    """When no head is supplied, the local template/main ref is used without fetching."""
    _init_repo(tmp_path)
    _write_text(tmp_path, "README.md", "base\n")
    base_sha = _commit_all(tmp_path, "base")
    _write_text(tmp_path, "README.md", "head\n")
    head_sha = _commit_all(tmp_path, "head")
    _git(tmp_path, "update-ref", "refs/remotes/template/main", head_sha)
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        _marker(["baseline"], last_reviewed_template_commit=base_sha),
    )

    result = _run_generator(tmp_path)

    assert result.returncode == 0, result.stderr
    assert f"- Range head: `{head_sha}` from `template/main`" in result.stdout


def test_write_candidates_writes_table_and_preserves_stdout(tmp_path: Path) -> None:
    """The optional output path receives the table while stdout keeps the full report."""
    _init_repo(tmp_path)
    _write_text(tmp_path, "README.md", "base\n")
    base_sha = _commit_all(tmp_path, "base")
    _write_text(tmp_path, "README.md", "head\n")
    head_sha = _commit_all(tmp_path, "head")
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        _marker(["baseline"], last_reviewed_template_commit=base_sha),
    )

    result = _run_generator(
        tmp_path,
        "--range-head",
        head_sha,
        "--write-candidates",
        ".cache/template-sync/candidates.md",
    )
    written_table = (tmp_path / ".cache/template-sync/candidates.md").read_text(encoding="utf-8")

    assert result.returncode == 0, result.stderr
    assert "# Template Sync Candidate Table" in result.stdout
    assert "- Saved candidate table: `.cache/template-sync/candidates.md`" in result.stdout
    assert "| README.md | Modified | requires all: baseline | Retained |" in result.stdout
    assert written_table.startswith("| Path | Change | Matched module relation |")
    assert "| README.md | Modified | requires all: baseline | Retained |" in written_table
    assert "# Template Sync Candidate Table" not in written_table


def test_write_candidates_rejects_paths_outside_repository(tmp_path: Path) -> None:
    """The optional output path uses the existing repo-root traversal guard."""
    _init_repo(tmp_path)
    _write_text(tmp_path, "README.md", "base\n")
    base_sha = _commit_all(tmp_path, "base")
    _write_text(tmp_path, "README.md", "head\n")
    head_sha = _commit_all(tmp_path, "head")
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        _marker(["baseline"], last_reviewed_template_commit=base_sha),
    )

    result = _run_generator(
        tmp_path,
        "--range-head",
        head_sha,
        "--write-candidates",
        "../candidates.md",
    )

    assert result.returncode == 1
    assert "Path escapes the repository root: ../candidates.md" in result.stderr


def test_unmapped_paths_are_flagged(tmp_path: Path) -> None:
    """Changed paths outside the manifest surface as owner-review items."""
    _init_repo(tmp_path)
    _write_text(tmp_path, "README.md", "base\n")
    base_sha = _commit_all(tmp_path, "base")
    _write_text(tmp_path, "docs/unmapped.md", "new\n")
    head_sha = _commit_all(tmp_path, "head")
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        _marker(["baseline"], last_reviewed_template_commit=base_sha),
    )

    result = _run_generator(tmp_path, "--range-head", head_sha)

    assert result.returncode == 0, result.stderr
    assert "| docs/unmapped.md | Added | UNMAPPED | Unmapped |" in result.stdout
    assert "owner must assign or confirm a module" in result.stdout


def test_unknown_manifest_modules_are_flagged(tmp_path: Path) -> None:
    """Mappings that reference modules absent from the manifest are surfaced."""
    _init_repo(
        tmp_path,
        extra_mappings=[
            {"pattern": "future.md", "requires_all": ["future-module"]},
        ],
    )
    _write_text(tmp_path, "README.md", "base\n")
    base_sha = _commit_all(tmp_path, "base")
    _write_text(tmp_path, "future.md", "new\n")
    head_sha = _commit_all(tmp_path, "head")
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        _marker(["baseline"], last_reviewed_template_commit=base_sha),
    )

    result = _run_generator(tmp_path, "--range-head", head_sha)

    assert result.returncode == 0, result.stderr
    assert "| future.md | Added | requires all: future-module | Excluded |" in result.stdout
    assert "Unknown module(s): future-module." in result.stdout


def test_local_overrides_are_reported(tmp_path: Path) -> None:
    """Marker local overrides appear as defaults, not automatic decisions."""
    _init_repo(tmp_path)
    _write_text(tmp_path, "README.md", "base\n")
    base_sha = _commit_all(tmp_path, "base")
    _write_text(tmp_path, "README.md", "head\n")
    head_sha = _commit_all(tmp_path, "head")
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        _marker(
            ["baseline"],
            last_reviewed_template_commit=base_sha,
            local_overrides=[
                {
                    "path": "README.md",
                    "reason": "Project-specific README.",
                    "default_decision": "SKIP",
                }
            ],
        ),
    )

    result = _run_generator(tmp_path, "--range-head", head_sha)

    assert result.returncode == 0, result.stderr
    assert "SKIP: Project-specific README." in result.stdout
    assert "Local override present; use it as a default" in result.stdout


def test_deferred_protected_candidates_and_protected_files_are_flagged(tmp_path: Path) -> None:
    """Deferred protected marker entries and protected paths are visible."""
    _init_repo(tmp_path)
    _write_text(tmp_path, ".github/copilot-instructions.md", "base\n")
    base_sha = _commit_all(tmp_path, "base")
    _write_text(tmp_path, ".github/copilot-instructions.md", "head\n")
    head_sha = _commit_all(tmp_path, "head")
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        _marker(
            ["agent-instructions"],
            last_reviewed_template_commit=base_sha,
            deferred_candidates=[
                {
                    "path": ".github/copilot-instructions.md",
                    "source_commit": head_sha,
                    "reason": "Awaiting owner authorization.",
                }
            ],
        ),
    )

    result = _run_generator(tmp_path, "--range-head", head_sha)

    assert result.returncode == 0, result.stderr
    assert "Awaiting owner authorization." in result.stdout
    assert "| .github/copilot-instructions.md | Modified |" in result.stdout
    assert (
        "Protected instruction/governance file; explicit owner authorization is required."
        in result.stdout
    )


def test_renamed_files_preserve_old_and_new_paths(tmp_path: Path) -> None:
    """Rename rows keep both paths and identify the rename status."""
    _init_repo(tmp_path)
    _write_text(tmp_path, "templates/markdown/intro.md", "same content\n")
    base_sha = _commit_all(tmp_path, "base")
    _git(tmp_path, "mv", "templates/markdown/intro.md", "templates/markdown/getting-started.md")
    head_sha = _commit_all(tmp_path, "head")
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        _marker(["markdown"], last_reviewed_template_commit=base_sha),
    )

    result = _run_generator(tmp_path, "--range-head", head_sha)

    assert result.returncode == 0, result.stderr
    assert "templates/markdown/intro.md -> templates/markdown/getting-started.md" in result.stdout
    assert "Renamed (R100)" in result.stdout
    assert "Renamed from templates/markdown/intro.md." in result.stdout


def test_rename_across_module_boundaries_is_flagged(tmp_path: Path) -> None:
    """A rename whose old and new paths map to different modules is surfaced."""
    _init_repo(tmp_path)
    _write_text(tmp_path, "templates/markdown/intro.md", "same content\n")
    base_sha = _commit_all(tmp_path, "base")
    (tmp_path / "templates/markdown/intro.md").unlink()
    _write_text(tmp_path, "templates/python/intro.md", "same content\n")
    head_sha = _commit_all(tmp_path, "head")
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        _marker(["markdown", "python"], last_reviewed_template_commit=base_sha),
    )

    result = _run_generator(tmp_path, "--range-head", head_sha)

    assert result.returncode == 0, result.stderr
    assert "templates/markdown/intro.md -> templates/python/intro.md" in result.stdout
    assert "Renamed from templates/markdown/intro.md." in result.stdout
    assert (
        "Rename crosses module mapping boundaries: old path resolves to "
        "requires all: markdown; new path resolves to requires all: python." in result.stdout
    )


def test_invalid_marker_schema_is_rejected(tmp_path: Path) -> None:
    """Marker and manifest files must pass the checked-in schemas before output."""
    _init_repo(tmp_path)
    _write_text(tmp_path, "README.md", "base\n")
    base_sha = _commit_all(tmp_path, "base")
    _write_text(tmp_path, "README.md", "head\n")
    head_sha = _commit_all(tmp_path, "head")
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        {
            "template_sync": {
                "source_repo": SOURCE_REPO,
                "last_reviewed_template_commit": base_sha,
                "included_modules": ["not-a-real-module"],
            }
        },
    )

    result = _run_generator(tmp_path, "--range-head", head_sha)

    assert result.returncode == 1
    assert "Schema validation failed for .template-sync/marker.yml" in result.stderr
