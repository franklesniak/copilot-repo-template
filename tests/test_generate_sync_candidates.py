"""Exercise the marker-aware sync candidate table generator."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml  # type: ignore[import-untyped]

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / ".template-sync" / "scripts" / "generate_sync_candidates.py"
SCRIPT_DIR = SCRIPT_PATH.parent
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

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
SCRIPT_SPEC = importlib.util.spec_from_file_location("generate_sync_candidates", SCRIPT_PATH)
if SCRIPT_SPEC is None or SCRIPT_SPEC.loader is None:
    raise RuntimeError(f"Unable to load sync candidate helper module from {SCRIPT_PATH}")
sync_candidates = importlib.util.module_from_spec(SCRIPT_SPEC)
sys.modules[SCRIPT_SPEC.name] = sync_candidates
SCRIPT_SPEC.loader.exec_module(sync_candidates)


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


def _symlink_or_skip(link_path: Path, target_path: Path) -> None:
    """Create a directory symlink, or skip when the platform refuses it."""
    try:
        link_path.symlink_to(target_path, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"Symlink creation unavailable in this environment: {error}")


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
                "requires_any": ["json", "yaml", "schema", "template-sync-support"],
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
    protected_decisions: list[dict[str, str]] | None = None,
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
    if protected_decisions is not None:
        template_sync["protected_file_decisions"] = protected_decisions
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


def _summary_section_modules(output: str, heading: str) -> set[str]:
    """Return the backtick-quoted module names rendered under a `## <heading>` section."""
    modules: set[str] = set()
    in_section = False
    for line in output.splitlines():
        if line.startswith("## "):
            in_section = line == f"## {heading}"
            continue
        if in_section:
            stripped = line.strip()
            if stripped.startswith("- `") and stripped.endswith("`"):
                modules.add(stripped.removeprefix("- `").removesuffix("`"))
    return modules


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
    assert (
        "requires all: github-actions; requires any: json, schema, template-sync-support, yaml"
        in result.stdout
    )
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

    assert result.returncode == 0, result.stderr
    assert "# Template Sync Candidate Table" in result.stdout
    assert "- Saved candidate table: `.cache/template-sync/candidates.md`" in result.stdout
    assert "| README.md | Modified | requires all: baseline | Retained |" in result.stdout

    written_table = (tmp_path / ".cache/template-sync/candidates.md").read_text(encoding="utf-8")
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


def test_ledger_only_reports_manifest_marker_and_todo_decisions(tmp_path: Path) -> None:
    """The adoption ledger can be generated without a git comparison range."""
    _init_repo(tmp_path)
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        _marker(
            ["baseline"],
            last_reviewed_template_commit=None,
            local_overrides=[
                {
                    "path": "README.md",
                    "reason": "Project-specific README.",
                    "default_decision": "SKIP",
                }
            ],
        ),
    )
    _write_text(
        tmp_path,
        "_TODO-repo-init.md",
        (
            "- [ ] Confirm private vulnerability reporting.\n"
            "- [x] Record adoption mode for protected files.\n"
        ),
    )

    result = _run_generator(
        tmp_path,
        "--ledger-only",
        "--write-ledger",
        ".cache/template-sync/adoption-ledger.md",
    )

    assert result.returncode == 0, result.stderr
    assert "Saved adoption ledger: `.cache/template-sync/adoption-ledger.md`" in result.stdout
    assert "# Template Adoption Ledger" in result.stdout
    assert "Generated snapshot; review artifact only." in result.stdout
    assert (
        "| README.md | all: baseline | local override | "
        "Marker local override defaults to `SKIP`: Project-specific README."
    ) in result.stdout
    assert "| .pre-commit-config.yaml | all: baseline | trim |" in result.stdout
    assert "module-scoped inline blocks" in result.stdout
    assert (
        "| .github/copilot-instructions.md | all: agent-instructions | "
        "needs maintainer decision | Protected path is not retained by included modules"
    ) in result.stdout
    assert (
        "| templates/python/** | all: python | skip | Required module(s) not included: python."
        in (result.stdout)
    )
    assert "| _TODO-repo-init.md | manual setup | manual TODO | open:" in result.stdout
    assert "[line 1](../../_TODO-repo-init.md#L1)" in result.stdout
    assert "pre-commit run --all-files" in result.stdout
    assert "manual first-adoption review" in result.stdout
    assert "No range base was provided" not in result.stderr

    written_ledger = (tmp_path / ".cache/template-sync/adoption-ledger.md").read_text(
        encoding="utf-8"
    )
    assert written_ledger.startswith("# Template Adoption Ledger")
    assert (
        ".template-sync/manifest.yml` and `.template-sync/marker.yml` remain the authoritative"
        in written_ledger
    )
    assert "| `_TODO-repo-init.md` link |" in written_ledger


def test_ledger_only_without_marker_uses_empty_marker_data(tmp_path: Path) -> None:
    """The upstream template can render a ledger before a marker exists."""
    _init_repo(tmp_path)

    result = _run_generator(tmp_path, "--ledger-only")

    assert result.returncode == 0, result.stderr
    assert "# Template Adoption Ledger" in result.stdout
    assert "- Marker: `.template-sync/marker.yml`" in result.stdout
    assert "- Included modules: none" in result.stdout
    assert "No range base was provided" not in result.stderr


def test_write_ledger_rejects_paths_outside_repository(tmp_path: Path) -> None:
    """The ledger snapshot path uses the existing repo-root traversal guard."""
    _init_repo(tmp_path)
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        _marker(["baseline"], last_reviewed_template_commit=None),
    )

    result = _run_generator(
        tmp_path,
        "--ledger-only",
        "--write-ledger",
        "../adoption-ledger.md",
    )

    assert result.returncode == 1
    assert "Path escapes the repository root: ../adoption-ledger.md" in result.stderr


def test_ledger_only_rejects_write_candidates_flag(tmp_path: Path) -> None:
    """`--ledger-only` cannot be combined with `--write-candidates`."""
    _init_repo(tmp_path)
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        _marker(["baseline"], last_reviewed_template_commit=None),
    )

    result = _run_generator(
        tmp_path,
        "--ledger-only",
        "--write-candidates",
        ".cache/template-sync/candidates.md",
    )

    assert result.returncode == 1
    assert "--write-candidates cannot be used with --ledger-only." in result.stderr


def test_ledger_flag_appends_ledger_after_candidate_table(tmp_path: Path) -> None:
    """`--ledger` (non-only) prints the candidate table followed by the adoption ledger."""
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
        "--ledger",
    )

    assert result.returncode == 0, result.stderr
    assert "# Template Sync Candidate Table" in result.stdout
    assert "| README.md | Modified | requires all: baseline | Retained |" in result.stdout
    assert "# Template Adoption Ledger" in result.stdout
    assert result.stdout.index("# Template Sync Candidate Table") < result.stdout.index(
        "# Template Adoption Ledger"
    )


def test_summary_reports_clean_adoption_without_unresolved_decisions(tmp_path: Path) -> None:
    """A clean marker produces a concise PR-description-ready summary."""
    _init_repo(tmp_path)
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        _marker(
            ["agent-instructions", "baseline"],
            last_reviewed_template_commit=None,
            protected_decisions=[
                {
                    "path": ".github/copilot-instructions.md",
                    "decision": "MERGE",
                    "adoption_mode": "minimal-preservation",
                    "authorization_basis": "Owner authorized protected edits on 2026-06-04.",
                    "authorized_scope": ".github/copilot-instructions.md only.",
                }
            ],
        ),
    )
    _write_text(
        tmp_path,
        "_TODO-repo-init.md",
        (
            "# Repository Initialization Checklist\n"
            "\n"
            "## Manual GitHub Settings\n"
            "\n"
            "- [x] Private vulnerability reporting decision recorded.\n"
            "\n"
            "## Maintainer Policy Decisions\n"
            "\n"
            "- [x] Adoption mode recorded.\n"
            "\n"
            "## Protected-File Adoption Decisions\n"
            "\n"
            "- [x] Protected-file edits authorized by maintainer.\n"
            "\n"
            "## Unresolved Settings\n"
            "\n"
            "- [x] No unresolved settings remain.\n"
        ),
    )

    result = _run_generator(tmp_path, "--summary")

    assert result.returncode == 0, result.stderr
    assert "# Template Adoption Summary" in result.stdout
    assert "# Template Adoption Ledger" not in result.stdout
    assert "## Included Modules" in result.stdout
    assert "## Excluded Modules" in result.stdout
    included_modules = _summary_section_modules(result.stdout, "Included Modules")
    excluded_modules = _summary_section_modules(result.stdout, "Excluded Modules")
    assert "agent-instructions" in included_modules
    assert "baseline" in included_modules
    assert "agent-instructions" not in excluded_modules
    assert "python" in excluded_modules
    assert "python" not in included_modules
    assert (
        "| .github/copilot-instructions.md | MERGE | minimal-preservation | authorized |"
        in result.stdout
    )
    assert (
        "- Unresolved maintainer decisions remain in available machine-readable state: No."
        in result.stdout
    )
    assert "No unchecked items in machine-interpretable checklist sections." in result.stdout
    assert "python .template-sync/scripts/run_first_adoption_checks.py" in result.stdout
    assert "pytest tests/ -v --cov --cov-report=term-missing" not in result.stdout


def test_summary_reports_deferred_overrides_and_documented_todo_items(
    tmp_path: Path,
) -> None:
    """Deferred marker records and documented unchecked TODOs remain visible."""
    _init_repo(tmp_path)
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        _marker(
            ["baseline"],
            last_reviewed_template_commit=None,
            local_overrides=[
                {
                    "path": "README.md",
                    "reason": "Owner has not chosen the downstream README treatment.",
                    "default_decision": "DEFER",
                }
            ],
            deferred_candidates=[
                {
                    "path": ".github/copilot-instructions.md",
                    "source_commit": "a" * 40,
                    "reason": "Awaiting protected-file authorization.",
                }
            ],
        ),
    )
    _write_text(
        tmp_path,
        "_TODO-repo-init.md",
        (
            "# Repository Initialization Checklist\n"
            "\n"
            "## Discoverable Repository State\n"
            "\n"
            "- [ ] Repository owner/name recorded from Git remote.\n"
            "\n"
            "## Maintainer Policy Decisions\n"
            "\n"
            "- [ ] Security vulnerability reporting channel selected.\n"
            "\n"
            "## Resolution Evidence\n"
            "\n"
            "- [ ] Evidence captured for resolved settings.\n"
        ),
    )

    result = _run_generator(tmp_path, "--summary")

    assert result.returncode == 0, result.stderr
    assert "| README.md | DEFER | Owner has not chosen the downstream README treatment. |" in (
        result.stdout
    )
    assert (
        "`README.md`: local override; Marker local override defaults to `DEFER`: "
        "Owner has not chosen the downstream README treatment."
    ) in result.stdout
    assert "Deferred protected candidate: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" in result.stdout
    assert (
        "- Unresolved maintainer decisions remain in available machine-readable state: Yes."
        in result.stdout
    )
    assert (
        "- Maintainer Policy Decisions: Security vulnerability reporting channel selected. "
        "(`_TODO-repo-init.md` line 9)"
    ) in result.stdout
    assert (
        "- Discoverable Repository State: Repository owner/name recorded from Git remote. "
        "(`_TODO-repo-init.md` line 5)"
    ) in result.stdout


def test_summary_surfaces_deferred_candidate_unmatched_by_manifest_rows(
    tmp_path: Path,
) -> None:
    """Deferred candidates sharing a templated reason are deduplicated by path, not text."""
    _init_repo(tmp_path)
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        _marker(
            ["agent-instructions", "baseline"],
            last_reviewed_template_commit=None,
            deferred_candidates=[
                {
                    "path": ".github/copilot-instructions.md",
                    "source_commit": "a" * 40,
                    "reason": "Awaiting protected-file authorization.",
                },
                {
                    "path": "AGENTS.md",
                    "source_commit": "b" * 40,
                    "reason": "Awaiting protected-file authorization.",
                },
            ],
        ),
    )

    result = _run_generator(tmp_path, "--summary")

    assert result.returncode == 0, result.stderr
    # The manifest-matched candidate is surfaced via its ledger row.
    assert "Deferred protected candidate: " + "a" * 40 in result.stdout
    # The candidate whose path matches no deferred-candidate ledger row must still be
    # surfaced even though it shares the templated reason text of the matched one.
    assert (
        "`AGENTS.md`: deferred protected candidate from `" + "b" * 40 + "`; "
        "Awaiting protected-file authorization."
    ) in result.stdout


def test_summary_reports_protected_file_removal_authorization(tmp_path: Path) -> None:
    """REMOVE-LOCAL protected decisions keep authorization fields in the summary."""
    _init_repo(tmp_path)
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        _marker(
            ["agent-instructions"],
            last_reviewed_template_commit=None,
            protected_decisions=[
                {
                    "path": "GEMINI.md",
                    "decision": "REMOVE-LOCAL",
                    "authorization_basis": "Owner explicitly authorized removing GEMINI.md.",
                    "authorized_scope": "GEMINI.md only.",
                    "reason": "Gemini agent not used by this repository.",
                }
            ],
        ),
    )

    result = _run_generator(tmp_path, "--summary")

    assert result.returncode == 0, result.stderr
    assert (
        "| GEMINI.md | REMOVE-LOCAL | not recorded | authorized | "
        "Owner explicitly authorized removing GEMINI.md. | GEMINI.md only. | "
        "not recorded | Gemini agent not used by this repository. |"
    ) in result.stdout


def test_summary_reports_non_interpretable_todo_without_inferring_tasks(
    tmp_path: Path,
) -> None:
    """A non-document-shaped TODO file is reported but not parsed as policy state."""
    _init_repo(tmp_path)
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        _marker(["baseline"], last_reviewed_template_commit=None),
    )
    _write_text(tmp_path, "_TODO-repo-init.md", "- [ ] Random local cleanup task\n")

    result = _run_generator(tmp_path, "--summary")

    assert result.returncode == 0, result.stderr
    assert "found; not machine-interpretable" in result.stdout
    assert (
        "`_TODO-repo-init.md` is present but not machine-interpretable; "
        "unchecked items were not parsed."
    ) in result.stdout
    assert "manual review is required" in result.stdout
    assert "Random local cleanup task" not in result.stdout


def test_summary_rejects_todo_when_title_is_not_first_content_line(
    tmp_path: Path,
) -> None:
    """A documented H1 that appears after preamble is not treated as interpretable."""
    _init_repo(tmp_path)
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        _marker(["baseline"], last_reviewed_template_commit=None),
    )
    _write_text(
        tmp_path,
        "_TODO-repo-init.md",
        (
            "Downstream preamble that is not the documented title.\n"
            "\n"
            "# Repository Initialization Checklist\n"
            "\n"
            "## Maintainer Policy Decisions\n"
            "\n"
            "- [ ] Security vulnerability reporting channel selected.\n"
        ),
    )

    result = _run_generator(tmp_path, "--summary")

    assert result.returncode == 0, result.stderr
    assert "found; not machine-interpretable" in result.stdout
    assert (
        "`_TODO-repo-init.md` is present but not machine-interpretable; "
        "unchecked items were not parsed."
    ) in result.stdout
    assert "manual review is required" in result.stdout
    assert "Security vulnerability reporting channel selected." not in result.stdout


@pytest.mark.parametrize("mode_flag", ["--ledger", "--ledger-only", "--preflight"])
def test_summary_is_mutually_exclusive_with_other_review_modes(
    tmp_path: Path,
    mode_flag: str,
) -> None:
    """`--summary` is part of the existing mutually-exclusive mode group."""
    _init_repo(tmp_path)

    result = _run_generator(tmp_path, "--summary", mode_flag)

    assert result.returncode == 2
    assert "not allowed with argument" in result.stderr


def test_preflight_without_marker_reports_questionnaire_and_reused_ledger(
    tmp_path: Path,
) -> None:
    """The read-only preflight mode works before a marker is created."""
    _init_repo(tmp_path)

    result = _run_generator(tmp_path, "--preflight")

    assert result.returncode == 0, result.stderr
    assert "# First-Adoption Preflight Report" in result.stdout
    assert "Read-only planning artifact." in result.stdout
    assert "Marker: `.template-sync/marker.yml` (not found;" in result.stdout
    assert "GitHub metadata: not requested" in result.stdout
    assert "Which vulnerability reporting channel should `SECURITY.md` publish?" in result.stdout
    assert "## `_TODO-repo-init.md` Starter" in result.stdout
    assert "state: `[not yet asked, asked and deferred, or unavailable" in result.stdout
    assert "## Reused Adoption Ledger" in result.stdout
    assert "# Template Adoption Ledger" in result.stdout
    assert (
        "| .github/copilot-instructions.md | all: agent-instructions | "
        "needs maintainer decision | Protected path is not retained by included modules"
    ) in result.stdout
    assert "No range base was provided" not in result.stderr


def test_questionnaire_alias_with_marker_reports_protected_questions(
    tmp_path: Path,
) -> None:
    """`--questionnaire` aliases preflight and reuses protected ledger decisions."""
    _init_repo(tmp_path)
    _git(tmp_path, "remote", "add", "origin", "https://github.com/example/project.git")
    _write_text(tmp_path, ".github/copilot-instructions.md", "instructions\n")
    _write_text(tmp_path, "_TODO-repo-init.md", "- [ ] Existing adoption note\n")
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        _marker(["agent-instructions", "baseline"], last_reviewed_template_commit=None),
    )

    result = _run_generator(tmp_path, "--questionnaire")

    assert result.returncode == 0, result.stderr
    assert "Repository owner/name: `example/project`" in result.stdout
    assert (
        "Marker: `.template-sync/marker.yml` (found; included modules: "
        "`agent-instructions`, `baseline`;"
    ) in result.stdout
    assert "First-adoption checklist: `_TODO-repo-init.md` (found)" in result.stdout
    assert "Agent instruction files: `.github/copilot-instructions.md`" in result.stdout
    assert (
        "Does the maintainer authorize the selected action for "
        "`.github/copilot-instructions.md`?"
    ) in result.stdout
    assert (
        "| .github/copilot-instructions.md | all: agent-instructions | "
        "needs maintainer decision | Protected retained path requires explicit owner "
        "authorization."
    ) in result.stdout


def test_preflight_rejects_write_flags(tmp_path: Path) -> None:
    """Preflight remains read-only even though ledger mode can write snapshots."""
    _init_repo(tmp_path)

    result = _run_generator(tmp_path, "--preflight", "--write-ledger", "ledger.md")

    assert result.returncode == 1
    assert "--write-ledger cannot be used with --preflight." in result.stderr


def test_github_metadata_not_requested_skips_provider(tmp_path: Path) -> None:
    """GitHub-only metadata lookup is not attempted without explicit opt-in."""
    calls: list[list[str]] = []

    def runner(repo_root: Path, command: list[str]) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="{}", stderr="")

    metadata = sync_candidates.discover_github_metadata(
        tmp_path,
        "example/project",
        include_metadata=False,
        command_runner=runner,
    )

    assert calls == []
    assert metadata.requested is False
    assert metadata.available is False
    assert metadata.source == "not requested"


def test_github_metadata_provider_reports_visible_values(tmp_path: Path) -> None:
    """The optional GitHub metadata provider can be mocked without network access."""
    calls: list[list[str]] = []

    def runner(repo_root: Path, command: list[str]) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        if command[:3] == ["gh", "repo", "view"]:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=json.dumps(
                    {
                        "nameWithOwner": "example/project",
                        "visibility": "PUBLIC",
                        "defaultBranchRef": {"name": "main"},
                        "hasDiscussionsEnabled": True,
                    }
                ),
                stderr="",
            )
        if command[:3] == ["gh", "label", "list"]:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=json.dumps([{"name": "triage"}, {"name": "bug"}]),
                stderr="",
            )
        raise AssertionError(f"Unexpected command: {command}")

    metadata = sync_candidates.discover_github_metadata(
        tmp_path,
        "example/project",
        include_metadata=True,
        command_runner=runner,
    )

    assert [command[:3] for command in calls] == [
        ["gh", "repo", "view"],
        ["gh", "label", "list"],
    ]
    assert metadata.requested is True
    assert metadata.available is True
    assert metadata.repository == "example/project"
    assert metadata.visibility == "PUBLIC"
    assert metadata.default_branch == "main"
    assert metadata.discussions_enabled == "enabled"
    assert metadata.labels == ("bug", "triage")


def test_format_remotes_redacts_embedded_credentials() -> None:
    """Remote URLs with embedded user-info are redacted in the report."""
    remotes = (
        sync_candidates.RemoteInfo(
            name="origin",
            url="https://maintainer:ghp_secrettoken@github.com/example/project.git",
            purpose="fetch",
        ),
        sync_candidates.RemoteInfo(
            name="bare-token",
            url="https://ghp_anothersecret@github.com/example/project.git",
            purpose="push",
        ),
        sync_candidates.RemoteInfo(
            name="scheme-relative",
            url="//ghp_schemerelative@github.com/example/project.git",
            purpose="fetch",
        ),
        sync_candidates.RemoteInfo(
            name="ssh",
            url="git@github.com:example/project.git",
            purpose="push",
        ),
    )

    rendered = sync_candidates.format_remotes(remotes)

    assert "ghp_secrettoken" not in rendered
    assert "ghp_anothersecret" not in rendered
    assert "ghp_schemerelative" not in rendered
    assert "maintainer:" not in rendered
    assert "https://***@github.com/example/project.git" in rendered
    # Scheme-relative authorities must also be redacted, not just scheme:// URLs.
    assert "//***@github.com/example/project.git" in rendered
    # SCP-style SSH URLs cannot embed a password and are preserved verbatim.
    assert "git@github.com:example/project.git" in rendered


def test_redact_url_userinfo_handles_url_forms() -> None:
    """The canonical redactor covers scheme, scheme-relative, SCP, and malformed forms."""
    redact = sync_candidates.redact_url_userinfo

    assert (
        redact("https://maintainer:token@github.com/org/repo.git")
        == "https://***@github.com/org/repo.git"
    )
    assert (
        redact("https://ghp_token@github.com/org/repo.git") == "https://***@github.com/org/repo.git"
    )
    # Scheme-relative authority must also be redacted.
    assert redact("//user:token@host/path") == "//***@host/path"
    # SCP-style SSH remotes have no URL authority and are preserved.
    assert redact("git@github.com:org/repo.git") == "git@github.com:org/repo.git"
    # No user-info: unchanged.
    assert redact("https://github.com/org/repo.git") == "https://github.com/org/repo.git"
    # Unparseable authority (malformed IPv6): fail-safe redaction that drops the scheme.
    assert redact("https://user:secret@[::1/path") == "***@[::1/path"


def test_infer_repository_name_anchors_github_host() -> None:
    """Owner/name inference matches the URL authority, not any github substring."""

    def infer(url: str) -> str | None:
        return sync_candidates.infer_repository_name(
            (sync_candidates.RemoteInfo(name="origin", url=url, purpose="fetch"),)
        )

    # Genuine GitHub remotes (scheme, SCP, user-info, and subdomain) resolve.
    assert infer("https://github.com/example/project.git") == "example/project"
    assert infer("git@github.com:example/project.git") == "example/project"
    assert infer("https://user:token@github.com/example/project") == "example/project"
    assert infer("https://team.github.com/example/project.git") == "example/project"
    # Look-alike or unrelated hosts MUST NOT be misclassified as GitHub.
    assert infer("https://notgithub.com/example/project.git") is None
    assert infer("https://github.com.evil.com/example/project.git") is None
    assert infer("git@gitlab.com:example/project.git") is None

    # The first genuine GitHub remote wins even if a look-alike precedes it.
    remotes = (
        sync_candidates.RemoteInfo(
            name="decoy", url="https://notgithub.com/decoy/repo.git", purpose="fetch"
        ),
        sync_candidates.RemoteInfo(
            name="origin", url="https://github.com/example/project.git", purpose="fetch"
        ),
    )
    assert sync_candidates.infer_repository_name(remotes) == "example/project"


def test_github_metadata_handles_non_object_json(tmp_path: Path) -> None:
    """Non-object JSON from gh repo view is reported as unavailable, not a crash."""

    def runner(repo_root: Path, command: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 0, stdout="null", stderr="")

    metadata = sync_candidates.discover_github_metadata(
        tmp_path,
        "example/project",
        include_metadata=True,
        command_runner=runner,
    )

    assert metadata.requested is True
    assert metadata.available is False
    assert metadata.error is not None
    assert "non-object" in metadata.error


def test_list_directory_files_skips_symlinked_ancestor(tmp_path: Path, monkeypatch: Any) -> None:
    """A symlinked ancestor directory is not iterated outside the repo root."""
    outside = tmp_path / "outside" / "workflows"
    outside.mkdir(parents=True)
    (outside / "leak.yml").write_text("name: leak\n", encoding="utf-8")

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    # `.github` is a symlink whose target lives outside the repo root.
    _symlink_or_skip(repo_root / ".github", tmp_path / "outside")

    escaping_dir = (repo_root / ".github" / "workflows").resolve()
    original_iterdir = Path.iterdir

    def guarded_iterdir(self: Path) -> Any:
        if self.resolve() == escaping_dir:
            raise AssertionError(f"iterated outside repo root: {self}")
        return original_iterdir(self)

    monkeypatch.setattr(Path, "iterdir", guarded_iterdir)

    result = sync_candidates.list_directory_files(repo_root, ".github/workflows", (".yml", ".yaml"))

    assert result == ()


def test_path_has_symlink_component_detects_symlinked_ancestor(tmp_path: Path) -> None:
    """A symlinked ancestor (or leaf) is detected; fully real paths pass."""
    repo_root = tmp_path / "repo"
    (repo_root / "real" / "nested").mkdir(parents=True)
    (repo_root / "real" / "nested" / "file.txt").write_text("x\n", encoding="utf-8")
    outside = tmp_path / "outside"
    outside.mkdir()
    # `.github` is a symlink whose target lives outside the repo root.
    _symlink_or_skip(repo_root / ".github", outside)

    # A symlinked ancestor and a symlinked leaf are both rejected.
    assert sync_candidates.path_has_symlink_component(repo_root, ".github/workflows") is True
    assert sync_candidates.path_has_symlink_component(repo_root, ".github") is True
    # Fully real paths are accepted whether or not they exist.
    assert sync_candidates.path_has_symlink_component(repo_root, "real/nested") is False
    assert sync_candidates.path_has_symlink_component(repo_root, "real/nested/file.txt") is False
    assert sync_candidates.path_has_symlink_component(repo_root, "does/not/exist") is False


def test_repository_path_exists_rejects_symlinked_ancestor(tmp_path: Path) -> None:
    """A path reached through a symlinked ancestor is not treated as a repo path."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "config.yml").write_text("name: leak\n", encoding="utf-8")
    # `.github` is a symlink whose target lives outside the repo root.
    _symlink_or_skip(repo_root / ".github", outside)

    # The file exists *through* the symlink, but must be rejected as out-of-boundary.
    assert sync_candidates.repository_path_exists(repo_root, ".github/config.yml") is False

    # A genuine in-repo file is accepted.
    (repo_root / "real").mkdir()
    (repo_root / "real" / "in_repo.yml").write_text("ok\n", encoding="utf-8")
    assert sync_candidates.repository_path_exists(repo_root, "real/in_repo.yml") is True


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


def test_protected_file_decision_is_reported_in_candidate_table(tmp_path: Path) -> None:
    """Changed protected paths show matching protected decision records."""
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
            protected_decisions=[
                {
                    "path": ".github/copilot-instructions.md",
                    "decision": "MERGE",
                    "adoption_mode": "minimal-preservation",
                    "authorization_basis": "Owner authorized protected edits on 2026-05-27.",
                    "authorized_scope": ".github/copilot-instructions.md only.",
                }
            ],
        ),
    )

    result = _run_generator(tmp_path, "--range-head", head_sha)

    assert result.returncode == 0, result.stderr
    assert "Protected file decision" in result.stdout
    assert "decision=MERGE; adoption_mode=minimal-preservation" in result.stdout
    assert "Protected file decision record present in marker." in result.stdout


def test_ledger_reports_protected_decision_modes_and_remove_local_section(
    tmp_path: Path,
) -> None:
    """The adoption ledger distinguishes tailored decisions and removals."""
    _init_repo(tmp_path)
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        _marker(
            ["agent-instructions"],
            last_reviewed_template_commit=None,
            protected_decisions=[
                {
                    "path": ".github/copilot-instructions.md",
                    "decision": "TAKE",
                    "adoption_mode": "tailored",
                    "authorization_basis": "Owner authorized protected edits on 2026-05-27.",
                    "authorized_scope": ".github/copilot-instructions.md only.",
                    "tailored_authorization_basis": "Owner authorized a tailored rewrite.",
                },
                {
                    "path": "GEMINI.md",
                    "decision": "REMOVE-LOCAL",
                    "authorization_basis": "Owner explicitly authorized removing GEMINI.md.",
                    "authorized_scope": "GEMINI.md only.",
                    "reason": "Gemini agent not used by this repository.",
                },
            ],
        ),
    )

    result = _run_generator(tmp_path, "--ledger-only")

    assert result.returncode == 0, result.stderr
    assert (
        "| .github/copilot-instructions.md | all: agent-instructions | protected decision: TAKE |"
        in (result.stdout)
    )
    assert "tailored (authorized protected-file decision)" in result.stdout
    assert "tailored_authorization_basis: Owner authorized a tailored rewrite." in result.stdout
    assert "| GEMINI.md | unmapped | protected decision: REMOVE-LOCAL |" in result.stdout
    assert "## REMOVE-LOCAL Authorizations" in result.stdout
    assert "authorization_basis: Owner explicitly authorized removing GEMINI.md." in result.stdout
    assert "authorized_scope: GEMINI.md only." in result.stdout
    assert "reason: Gemini agent not used by this repository." in result.stdout


def test_ledger_reports_protected_decision_overlap_side_by_side(tmp_path: Path) -> None:
    """Ledger protected decision context shows compatible local override overlap."""
    _init_repo(tmp_path)
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        _marker(
            ["agent-instructions"],
            last_reviewed_template_commit=None,
            local_overrides=[
                {
                    "path": ".github/copilot-instructions.md",
                    "reason": "Use minimal-preservation with a local policy note.",
                    "default_decision": "MERGE",
                }
            ],
            protected_decisions=[
                {
                    "path": ".github/copilot-instructions.md",
                    "decision": "MERGE",
                    "adoption_mode": "minimal-preservation",
                    "authorization_basis": "Owner authorized protected edits on 2026-05-27.",
                    "authorized_scope": ".github/copilot-instructions.md only.",
                }
            ],
        ),
    )

    result = _run_generator(tmp_path, "--ledger-only")

    assert result.returncode == 0, result.stderr
    assert "## Protected File Decision Records" in result.stdout
    assert (
        "protected_file_decisions: decision=MERGE; adoption_mode=minimal-preservation"
        in result.stdout
    )
    assert (
        "local_overrides: path=.github/copilot-instructions.md; default_decision=MERGE; "
        "reason=Use minimal-preservation with a local policy note."
    ) in result.stdout


def test_authorized_protected_decision_does_not_require_maintainer_decision(
    tmp_path: Path,
) -> None:
    """Authorized TAKE/MERGE protected decisions do not re-flag maintainer review."""
    _init_repo(tmp_path)
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        _marker(
            ["agent-instructions"],
            last_reviewed_template_commit=None,
            protected_decisions=[
                {
                    "path": ".github/copilot-instructions.md",
                    "decision": "MERGE",
                    "adoption_mode": "minimal-preservation",
                    "authorization_basis": "Owner authorized protected edits on 2026-05-27.",
                    "authorized_scope": ".github/copilot-instructions.md only.",
                }
            ],
        ),
    )

    result = _run_generator(tmp_path, "--ledger-only")

    assert result.returncode == 0, result.stderr
    assert (
        "| .github/copilot-instructions.md | all: agent-instructions "
        "| protected decision: MERGE | Authorized minimal-preservation protected-file edit."
    ) in result.stdout
    assert (
        "authorization_basis: Owner authorized protected edits on 2026-05-27. "
        "authorized_scope: .github/copilot-instructions.md only. | Yes | No |"
    ) in result.stdout


def test_unmatched_protected_decision_for_non_protected_path_reports_no(
    tmp_path: Path,
) -> None:
    """Non-protected paths in protected_file_decisions report protected_file=No."""
    _init_repo(tmp_path)
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        _marker(
            ["agent-instructions"],
            last_reviewed_template_commit=None,
            protected_decisions=[
                {
                    "path": "docs/non-protected-note.md",
                    "decision": "SKIP",
                    "reason": "Owner has decided not to adopt this file.",
                }
            ],
        ),
    )

    result = _run_generator(tmp_path, "--ledger-only")

    assert result.returncode == 0, result.stderr
    assert (
        "| docs/non-protected-note.md | unmapped | protected decision: SKIP "
        "| Protected decision `SKIP`: Owner has decided not to adopt this file. | No |"
    ) in result.stdout


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
