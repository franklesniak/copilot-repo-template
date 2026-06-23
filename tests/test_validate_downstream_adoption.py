"""Exercise aggregate downstream partial-adoption validation."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / ".template-sync" / "scripts" / "validate_downstream_adoption.py"
CONTRACTS_SCHEMA_PATH = REPO_ROOT / "schemas" / "template-sync-instruction-contracts.schema.json"
MARKER_SCHEMA_PATH = REPO_ROOT / "schemas" / "template-sync-marker.schema.json"
MANIFEST_SCHEMA_PATH = REPO_ROOT / "schemas" / "template-sync-manifest.schema.json"
SOURCE_REPO = "https://github.com/franklesniak/copilot-repo-template.git"
FULL_SHA = "0123456789abcdef0123456789abcdef01234567"
PARTIAL_MODULES = [
    "baseline",
    "agent-instructions",
    "github-actions",
    "github-platform",
    "github-templates",
    "markdown",
    "powershell",
    "schema",
    "template-sync-support",
    "yaml",
]
MODULE_DEFINITIONS = {
    "baseline": "Baseline files.",
    "agent-instructions": "Agent instruction files.",
    "github-platform": "GitHub platform files.",
    "github-actions": "GitHub Actions workflows.",
    "github-templates": "GitHub collaboration surfaces.",
    "azure-devops-platform": "Azure DevOps platform files.",
    "azure-pipelines": "Azure Pipelines files.",
    "azure-devops-collaboration": "Azure DevOps collaboration surfaces.",
    "template-onboarding": "Template onboarding files.",
    "template-sync-support": "Template sync support files.",
    "markdown": "Markdown files.",
    "powershell": "PowerShell files.",
    "json": "JSON files.",
    "yaml": "YAML files.",
    "schema": "Schema files.",
    "python": "Python project files.",
    "terraform": "Terraform files.",
}


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


def _copy_schemas(repo_root: Path) -> None:
    """Copy real template-sync schemas into a fixture repository."""
    schemas_dir = repo_root / "schemas"
    schemas_dir.mkdir(parents=True, exist_ok=True)
    for source_path in (CONTRACTS_SCHEMA_PATH, MARKER_SCHEMA_PATH, MANIFEST_SCHEMA_PATH):
        shutil.copyfile(source_path, schemas_dir / source_path.name)


def _run_git(repo_root: Path, *args: str) -> None:
    """Run a git command in ``repo_root`` for validator fixtures."""
    subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _run_validator(repo_root: Path, *extra_args: str) -> subprocess.CompletedProcess[str]:
    """Run the aggregate downstream adoption validator."""
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


def _section_entries(output: str, heading: str) -> set[str]:
    """Return bullet entries rendered under a named output section."""
    entries: set[str] = set()
    in_section = False

    for line in output.splitlines():
        if line and not line.startswith(" ") and line.endswith(":"):
            in_section = line == f"{heading}:"
            continue
        if in_section and line.startswith("  - "):
            entries.add(line.removeprefix("  - ").strip())
    return entries


def _manifest() -> dict[str, Any]:
    """Build a schema-valid manifest fixture with retained and excluded modules."""
    return {
        "template_manifest": {
            "version": 2,
            "modules": [
                {"name": name, "description": description}
                for name, description in MODULE_DEFINITIONS.items()
            ],
            "path_mappings": [
                {"pattern": ".template-sync/marker.yml", "requires_all": ["template-sync-support"]},
                {
                    "pattern": ".template-sync/manifest.yml",
                    "requires_all": ["template-sync-support"],
                },
                {
                    "pattern": ".template-sync/instruction-contracts.yml",
                    "requires_all": ["template-sync-support"],
                },
                {
                    "pattern": ".template-sync/scripts/**",
                    "requires_all": ["template-sync-support"],
                },
                {"pattern": "AGENTS.md", "requires_all": ["agent-instructions"]},
                {"pattern": "README.md", "requires_all": ["baseline"]},
                {"pattern": ".pre-commit-config.yaml", "requires_all": ["baseline"]},
                {"pattern": ".github/dependabot.yml", "requires_all": ["github-platform"]},
                {
                    "pattern": ".github/workflows/data-ci.yml",
                    "requires_all": ["github-actions"],
                    "requires_any": ["yaml", "schema", "template-sync-support"],
                },
                {"pattern": ".github/ISSUE_TEMPLATE/**", "requires_all": ["github-templates"]},
                {
                    "pattern": ".azuredevops/pull_request_template.md",
                    "requires_all": ["azure-devops-collaboration"],
                },
                {
                    "pattern": "docs/azure-devops-support.md",
                    "requires_any": [
                        "azure-devops-platform",
                        "azure-pipelines",
                        "azure-devops-collaboration",
                    ],
                },
                {"pattern": ".yamllint.yml", "requires_all": ["yaml"]},
                {
                    "pattern": "schemas/template-sync-manifest.schema.json",
                    "requires_all": ["template-sync-support"],
                },
                {
                    "pattern": "schemas/template-sync-marker.schema.json",
                    "requires_all": ["template-sync-support"],
                },
                {
                    "pattern": "schemas/template-sync-instruction-contracts.schema.json",
                    "requires_all": ["template-sync-support"],
                },
                {"pattern": "schemas/**", "requires_all": ["schema"]},
                {"pattern": "templates/powershell/**", "requires_all": ["powershell"]},
                {"pattern": "templates/json/**", "requires_all": ["json"]},
                {"pattern": "pyproject.toml", "requires_all": ["python"]},
                {"pattern": "src/copilot_repo_template/**", "requires_all": ["python"]},
                {"pattern": ".github/workflows/python-ci.yml", "requires_all": ["python"]},
                {"pattern": "modules/**", "requires_all": ["terraform"]},
                {
                    "pattern": "GETTING_STARTED_NEW_REPO.md",
                    "requires_all": ["template-onboarding"],
                },
            ],
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


def _contracts() -> dict[str, Any]:
    """Build a schema-valid instruction-contract fixture."""
    return {
        "instruction_contracts": [
            {
                "path": "AGENTS.md",
                "requires_modules": ["agent-instructions"],
                "required_headings": ["## GitHub Plugin Usage"],
                "required_phrases": ["Protected Instruction Files"],
            },
            {
                "path": "GEMINI.md",
                "requires_modules": [
                    "agent-instructions",
                    "azure-devops-collaboration",
                ],
                "required_headings": ["## Azure DevOps PR Review Protocol"],
            },
        ]
    }


def _marker(
    included_modules: list[str] | None = None,
    *,
    local_overrides: list[dict[str, str]] | None = None,
    deferred_candidates: list[dict[str, str]] | None = None,
    protected_decisions: list[dict[str, str]] | None = None,
    waivers: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Build a schema-valid downstream marker fixture."""
    template_sync: dict[str, Any] = {
        "source_repo": SOURCE_REPO,
        "last_reviewed_template_commit": FULL_SHA,
        "included_modules": included_modules or PARTIAL_MODULES,
    }
    if local_overrides is not None:
        template_sync["local_overrides"] = local_overrides
    if deferred_candidates is not None:
        template_sync["deferred_protected_candidates"] = deferred_candidates
    if protected_decisions is not None:
        template_sync["protected_file_decisions"] = protected_decisions
    if waivers is not None:
        template_sync["instruction_contract_waivers"] = waivers
    return {"template_sync": template_sync}


def _write_common_downstream_repo(
    repo_root: Path,
    *,
    marker: dict[str, Any] | None = None,
    readme_text: str = "# Downstream\n",
    precommit_text: str = "repos: []\n",
    agents_text: str = (
        "# Agent Instructions\n\n" "## Protected Instruction Files\n\n" "## GitHub Plugin Usage\n"
    ),
) -> None:
    """Write the common retained partial-adoption fixture files."""
    _run_git(repo_root, "init")
    _copy_schemas(repo_root)
    _write_yaml(repo_root, ".template-sync/manifest.yml", _manifest())
    _write_yaml(repo_root, ".template-sync/instruction-contracts.yml", _contracts())
    _write_yaml(repo_root, ".template-sync/marker.yml", marker or _marker())
    _write_text(repo_root, ".template-sync/scripts/validate_marker.py")
    _write_text(repo_root, ".template-sync/scripts/validate_instruction_contracts.py")
    _write_text(repo_root, ".template-sync/scripts/validate_downstream_adoption.py")
    _write_text(repo_root, "AGENTS.md", agents_text)
    _write_text(repo_root, "README.md", readme_text)
    _write_text(repo_root, ".pre-commit-config.yaml", precommit_text)
    _write_text(repo_root, ".github/dependabot.yml", "version: 2\nupdates: []\n")
    _write_text(
        repo_root,
        ".github/workflows/data-ci.yml",
        "name: Data CI\n'on': pull_request\npermissions: {}\njobs: {}\n",
    )
    _write_text(repo_root, ".yamllint.yml", "extends: default\n")
    _write_text(repo_root, "templates/powershell/Example.Tests.ps1")


def test_upstream_template_without_marker_skips_by_default_and_fails_when_required(
    tmp_path: Path,
) -> None:
    """A missing downstream marker is a no-op unless explicitly required."""
    default_result = _run_validator(tmp_path)
    required_result = _run_validator(tmp_path, "--require-marker")

    assert default_result.returncode == 0, default_result.stderr
    assert "No marker found at .template-sync/marker.yml" in default_result.stdout
    assert "downstream adoption validation skipped" in default_result.stdout
    assert required_result.returncode == 1
    assert "Marker is required but was not found at .template-sync/marker.yml." in (
        required_result.stderr
    )


def test_partial_downstream_adoption_without_python_project_files_passes(
    tmp_path: Path,
) -> None:
    """The downstream command does not require excluded Python project surfaces."""
    _write_common_downstream_repo(tmp_path)

    result = _run_validator(tmp_path, "--require-marker")

    assert result.returncode == 0, result.stderr
    assert "Downstream adoption validation passed." in result.stdout
    assert "Retained modules:" in result.stdout
    assert "Excluded modules:" in result.stdout

    retained_modules = _section_entries(result.stdout, "Retained modules")
    excluded_modules = _section_entries(result.stdout, "Excluded modules")

    assert "template-sync-support" in retained_modules
    assert "template-sync-support" not in excluded_modules
    assert "python" in excluded_modules
    assert "python" not in retained_modules
    assert not (tmp_path / "pyproject.toml").exists()
    assert not (tmp_path / "src" / "copilot_repo_template").exists()


def test_github_only_downstream_adoption_skips_azure_devops_contract(
    tmp_path: Path,
) -> None:
    """GitHub-only adopters do not need Azure DevOps protocol anchors or files."""
    _write_common_downstream_repo(tmp_path)

    result = _run_validator(tmp_path, "--require-marker")

    assert result.returncode == 0, result.stderr
    assert "Downstream adoption validation passed." in result.stdout
    assert not (tmp_path / "GEMINI.md").exists()
    assert not (tmp_path / ".azuredevops").exists()

    retained_modules = _section_entries(result.stdout, "Retained modules")
    excluded_modules = _section_entries(result.stdout, "Excluded modules")

    assert "azure-devops-collaboration" in excluded_modules
    assert "azure-devops-collaboration" not in retained_modules


def test_excluded_module_leftover_is_reported(tmp_path: Path) -> None:
    """Files from excluded modules still fail aggregate validation."""
    _write_common_downstream_repo(tmp_path)
    _write_text(tmp_path, "src/copilot_repo_template/example.py")

    result = _run_validator(tmp_path, "--require-marker")

    assert result.returncode == 1
    assert "Excluded-module leftover is present" in result.stdout
    assert "src/copilot_repo_template/example.py" in result.stdout


def test_unrecorded_local_path_is_warning_not_failure(tmp_path: Path) -> None:
    """Aggregate adoption validation surfaces local ownership gaps without failing."""
    _write_common_downstream_repo(tmp_path)
    _write_text(tmp_path, "docs/local.md")

    result = _run_validator(tmp_path, "--require-marker")

    assert result.returncode == 0, result.stderr
    assert "Downstream adoption validation passed." in result.stdout
    assert "Warnings:" in result.stdout
    assert (
        "Git-visible path is neither template-managed nor recorded in "
        "template_sync.local_path_ownership: docs/local.md"
    ) in result.stdout


def test_unrecorded_local_path_warnings_are_bounded(tmp_path: Path) -> None:
    """A large unrecorded local path set is capped with a summary remainder line.

    This mirrors the bounded sample validate_marker.py prints
    (``UNRECORDED_LOCAL_PATH_LIMIT`` = 20) so the aggregate adoption report cannot
    flood CI logs in real downstream repositories.
    """
    _write_common_downstream_repo(tmp_path)
    expected_limit = 20
    for index in range(expected_limit + 5):
        _write_text(tmp_path, f"docs/local-{index:02d}.md")

    result = _run_validator(tmp_path, "--require-marker")

    assert result.returncode == 0, result.stderr
    detailed_warnings = result.stdout.count(
        "Git-visible path is neither template-managed nor recorded in "
        "template_sync.local_path_ownership:"
    )
    assert detailed_warnings == expected_limit
    assert "more unrecorded Git-visible local path(s) not shown." in result.stdout


def test_retained_template_sync_helper_scripts_are_required(tmp_path: Path) -> None:
    """Retained template-sync support requires its helper scripts."""
    _write_common_downstream_repo(tmp_path)
    (tmp_path / ".template-sync" / "scripts" / "validate_marker.py").unlink()

    result = _run_validator(tmp_path, "--require-marker")

    assert result.returncode == 1
    assert "Retained template-sync support file is missing" in result.stdout
    assert ".template-sync/scripts/validate_marker.py" in result.stdout


def test_retained_template_sync_schema_contracts_are_required(tmp_path: Path) -> None:
    """Retained template-sync support requires its runtime schema contracts."""
    _write_common_downstream_repo(tmp_path)
    (tmp_path / "schemas" / "template-sync-instruction-contracts.schema.json").unlink()

    result = _run_validator(tmp_path, "--require-marker")

    assert result.returncode == 1
    assert "Retained template-sync support file is missing" in result.stdout
    assert "schemas/template-sync-instruction-contracts.schema.json" in result.stdout


def test_template_sync_support_without_schema_keeps_runtime_schemas(tmp_path: Path) -> None:
    """Template sync support does not require the general schema module."""
    retained_modules = [module for module in PARTIAL_MODULES if module != "schema"]
    _write_common_downstream_repo(tmp_path, marker=_marker(retained_modules))

    result = _run_validator(tmp_path, "--require-marker")

    assert result.returncode == 0, result.stderr
    assert "Downstream adoption validation passed." in result.stdout
    retained = _section_entries(result.stdout, "Retained modules")
    excluded = _section_entries(result.stdout, "Excluded modules")
    assert "template-sync-support" in retained
    assert "schema" in excluded
    assert "schema" not in retained


def test_excluded_inline_block_leftover_is_reported(tmp_path: Path) -> None:
    """Retained shared files cannot keep inline blocks for excluded modules."""
    _write_common_downstream_repo(
        tmp_path,
        precommit_text=(
            "repos: []\n"
            "# template-sync: begin python-only\n"
            "# Python hooks were not stripped.\n"
            "# template-sync: end python-only\n"
        ),
    )

    result = _run_validator(tmp_path, "--require-marker")

    assert result.returncode == 1
    assert "Inline-block consistency" in result.stdout
    assert "python-only remains but requires excluded module(s): python" in result.stdout


def test_or_group_inline_block_is_valid_when_any_member_module_retained(
    tmp_path: Path,
) -> None:
    """An OR-retention (ANY) inline block is not flagged while any member is retained.

    ``PARTIAL_MODULES`` excludes ``json`` but keeps ``yaml``, ``schema``, and
    ``template-sync-support``, so the ``data-ci-reference-only`` OR-group block is
    correctly retained. A naive AND check would flag it as requiring the excluded
    ``json`` module.
    """
    _write_common_downstream_repo(
        tmp_path,
        readme_text=(
            "# Downstream\n\n"
            "<!-- template-sync: begin data-ci-reference-only -->\n"
            "Data CI guidance.\n"
            "<!-- template-sync: end data-ci-reference-only -->\n"
        ),
    )

    result = _run_validator(tmp_path, "--require-marker")

    assert result.returncode == 0, result.stdout
    assert "data-ci-reference-only" not in result.stdout


def test_azure_guide_or_group_inline_block_is_reported_without_azure_modules(
    tmp_path: Path,
) -> None:
    """GitHub-only adopters must not retain Azure guide reference blocks."""
    _write_common_downstream_repo(
        tmp_path,
        readme_text=(
            "# Downstream\n\n"
            "<!-- template-sync: begin azure-devops-guide-reference-only -->\n"
            "See [Azure guide](docs/azure-devops-support.md).\n"
            "<!-- template-sync: end azure-devops-guide-reference-only -->\n"
        ),
    )

    result = _run_validator(tmp_path, "--require-marker")

    assert result.returncode == 1
    assert "azure-devops-guide-reference-only remains" in result.stdout
    assert "at least one of the excluded module(s)" in result.stdout


def test_azure_guide_or_group_inline_block_is_valid_when_one_azure_module_retained(
    tmp_path: Path,
) -> None:
    """The Azure guide marker is valid while any Azure host module is retained."""
    retained_modules = [*PARTIAL_MODULES, "azure-pipelines"]
    _write_common_downstream_repo(
        tmp_path,
        marker=_marker(retained_modules),
        readme_text=(
            "# Downstream\n\n"
            "<!-- template-sync: begin azure-devops-guide-reference-only -->\n"
            "See [Azure guide](docs/azure-devops-support.md).\n"
            "<!-- template-sync: end azure-devops-guide-reference-only -->\n"
        ),
    )
    _write_text(tmp_path, "docs/azure-devops-support.md", "# Azure DevOps Services Support\n")

    result = _run_validator(tmp_path, "--require-marker")

    assert result.returncode == 0, result.stdout
    assert "azure-devops-guide-reference-only" not in result.stdout


def test_github_only_downstream_adoption_reports_unguarded_azure_guide_link(
    tmp_path: Path,
) -> None:
    """GitHub-only adopters cannot keep unguarded relative links to the Azure guide."""
    _write_common_downstream_repo(
        tmp_path,
        readme_text="# Downstream\n\nSee [Azure guide](docs/azure-devops-support.md).\n",
    )

    result = _run_validator(tmp_path, "--require-marker")

    assert result.returncode == 1
    assert "Retained Markdown relative link targets excluded module(s)" in result.stdout
    assert "README.md:3: docs/azure-devops-support.md -> docs/azure-devops-support.md" in (
        result.stdout
    )


def test_retained_markdown_relative_link_to_excluded_module_is_reported(
    tmp_path: Path,
) -> None:
    """Retained Markdown files cannot link relatively to excluded template modules."""
    _write_common_downstream_repo(
        tmp_path,
        readme_text="# Downstream\n\nSee [JSON starter](templates/json/example.json).\n",
    )

    result = _run_validator(tmp_path, "--require-marker")

    assert result.returncode == 1
    assert "Retained Markdown relative link targets excluded module(s)" in result.stdout
    assert "README.md:3: templates/json/example.json -> templates/json/example.json" in (
        result.stdout
    )


def test_instruction_contract_failures_are_composed(tmp_path: Path) -> None:
    """Downstream instruction-contract checks run through the aggregate command."""
    _write_common_downstream_repo(
        tmp_path,
        agents_text="# Agent Instructions\n\n## Different Heading\n",
    )

    result = _run_validator(tmp_path, "--require-marker")

    assert result.returncode == 1
    assert "Required downstream instruction contract anchor is missing" in result.stdout
    assert "AGENTS.md: heading: ## GitHub Plugin Usage" in result.stdout


def test_waivers_deferred_items_and_commands_are_reported(tmp_path: Path) -> None:
    """Aggregate output distinguishes waivers, deferred items, and commands."""
    _write_common_downstream_repo(
        tmp_path,
        marker=_marker(
            local_overrides=[
                {
                    "path": "templates/json/",
                    "reason": "Downstream owns JSON examples.",
                    "default_decision": "SKIP",
                }
            ],
            deferred_candidates=[
                {
                    "path": "AGENTS.md",
                    "source_commit": FULL_SHA,
                    "reason": "Owner review pending for platform protocol changes.",
                }
            ],
            protected_decisions=[
                {
                    "path": "CLAUDE.md",
                    "decision": "REMOVE-LOCAL",
                    "authorization_basis": "Owner explicitly authorized removing CLAUDE.md.",
                    "authorized_scope": "CLAUDE.md only.",
                    "reason": "Claude agent is not retained downstream.",
                }
            ],
        ),
    )

    result = _run_validator(tmp_path, "--require-marker")

    assert result.returncode == 0, result.stderr
    assert "Waivers:" in result.stdout
    assert "Local override: templates/json/ (SKIP; reason: Downstream owns JSON examples.)" in (
        result.stdout
    )
    assert "Deferred items:" in result.stdout
    assert "Owner review pending for platform protocol changes." in result.stdout
    assert "Protected file decisions:" in result.stdout
    assert "CLAUDE.md: REMOVE-LOCAL" in result.stdout
    assert "Validation commands considered:" in result.stdout
    assert "validate_marker.py --require-marker" in result.stdout
    assert "validate_instruction_contracts.py --mode downstream --require-marker" in (result.stdout)
