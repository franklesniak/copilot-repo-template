"""Exercise instruction-contract validation for protected agent protocols."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml  # type: ignore[import-untyped]

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / ".template-sync" / "scripts" / "validate_instruction_contracts.py"
CONTRACTS_SCHEMA_PATH = REPO_ROOT / "schemas" / "template-sync-instruction-contracts.schema.json"
MARKER_SCHEMA_PATH = REPO_ROOT / "schemas" / "template-sync-marker.schema.json"
MANIFEST_SCHEMA_PATH = REPO_ROOT / "schemas" / "template-sync-manifest.schema.json"
SOURCE_REPO = "https://github.com/franklesniak/copilot-repo-template.git"
FULL_SHA = "0123456789abcdef0123456789abcdef01234567"


def _write_text(repo_root: Path, relative_path: str, text: str) -> None:
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
    """Copy the real validator schemas into a fixture repository."""
    schemas_dir = repo_root / "schemas"
    schemas_dir.mkdir(parents=True, exist_ok=True)
    for source_path in (CONTRACTS_SCHEMA_PATH, MARKER_SCHEMA_PATH, MANIFEST_SCHEMA_PATH):
        shutil.copyfile(source_path, schemas_dir / source_path.name)


def _manifest() -> dict[str, Any]:
    """Build a small schema-valid manifest fixture."""
    return {
        "template_manifest": {
            "version": 2,
            "modules": [
                {
                    "name": "agent-instructions",
                    "description": "Agent instruction files.",
                },
                {
                    "name": "template-sync-support",
                    "description": "Template sync support files.",
                },
                {
                    "name": "azure-devops-collaboration",
                    "description": "Azure DevOps collaboration files.",
                },
                {
                    "name": "schema",
                    "description": "Schema files.",
                },
            ],
            "path_mappings": [
                {
                    "pattern": "CLAUDE.md",
                    "requires_all": ["agent-instructions"],
                },
                {
                    "pattern": ".template-sync/instruction-contracts.yml",
                    "requires_all": ["template-sync-support"],
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


def _contracts(
    *,
    required_headings: list[str] | None = None,
    required_phrases: list[str] | None = None,
) -> dict[str, Any]:
    """Build a small instruction-contract fixture."""
    contract: dict[str, Any] = {
        "path": "CLAUDE.md",
        "requires_modules": ["agent-instructions"],
    }
    if required_headings is not None:
        contract["required_headings"] = required_headings
    if required_phrases is not None:
        contract["required_phrases"] = required_phrases
    return {"instruction_contracts": [contract]}


def _host_specific_contracts() -> dict[str, Any]:
    """Build contract fixtures for default GitHub and optional Azure DevOps protocols."""
    return {
        "instruction_contracts": [
            {
                "path": "CLAUDE.md",
                "requires_modules": ["agent-instructions"],
                "required_headings": ["## Handling Code Review Comments"],
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
    included_modules: list[str],
    *,
    protected_decisions: list[dict[str, str]] | None = None,
    waivers: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Build a small schema-valid marker fixture."""
    template_sync: dict[str, Any] = {
        "source_repo": SOURCE_REPO,
        "last_reviewed_template_commit": FULL_SHA,
        "included_modules": included_modules,
    }
    if protected_decisions is not None:
        template_sync["protected_file_decisions"] = protected_decisions
    if waivers is not None:
        template_sync["instruction_contract_waivers"] = waivers
    return {"template_sync": template_sync}


def _write_common_contract_repo(repo_root: Path, contracts: dict[str, Any]) -> None:
    """Write schemas, manifest, and instruction contracts to a fixture repository."""
    _copy_schemas(repo_root)
    _write_yaml(repo_root, ".template-sync/manifest.yml", _manifest())
    _write_yaml(repo_root, ".template-sync/instruction-contracts.yml", contracts)


def _run_validator(repo_root: Path, *extra_args: str) -> subprocess.CompletedProcess[str]:
    """Run the instruction-contract validator against a fixture repository."""
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


def test_mode_is_required(tmp_path: Path) -> None:
    """The validator must not fall back to implicit mode detection."""
    result = _run_validator(tmp_path)

    assert result.returncode == 2
    assert "--mode" in result.stderr


@pytest.mark.upstream_template_only
def test_intact_upstream_claude_contract_passes() -> None:
    """The committed upstream Claude protocol satisfies the default contract."""
    result = _run_validator(REPO_ROOT, "--mode", "upstream-template")

    assert result.returncode == 0, result.stderr
    assert "Instruction-contract validation passed." in result.stdout
    assert "Contracts checked: 1" in result.stdout


@pytest.mark.parametrize(
    "missing_heading",
    [
        "## Handling Code Review Comments",
        "## Automated Review Loop",
    ],
)
def test_upstream_missing_required_heading_fails(
    tmp_path: Path,
    missing_heading: str,
) -> None:
    """Required Claude protocol headings are enforced in upstream-template mode."""
    _write_common_contract_repo(
        tmp_path,
        _contracts(required_headings=[missing_heading]),
    )
    _write_text(
        tmp_path,
        "CLAUDE.md",
        "# Agent Instructions\n\n## Different Heading\n\nProtected-file authorization checkpoint\n",
    )

    result = _run_validator(tmp_path, "--mode", "upstream-template")

    assert result.returncode == 1
    assert "Instruction-contract validation failed." in result.stdout
    assert f"CLAUDE.md: missing required heading: {missing_heading}" in result.stdout


def test_upstream_missing_required_phrase_fails(tmp_path: Path) -> None:
    """Required protocol phrases are reported with exact missing text."""
    _write_common_contract_repo(
        tmp_path,
        _contracts(required_phrases=["Protected-file authorization checkpoint"]),
    )
    _write_text(tmp_path, "CLAUDE.md", "# Agent Instructions\n")

    result = _run_validator(tmp_path, "--mode", "upstream-template")

    assert result.returncode == 1
    assert (
        "CLAUDE.md: missing required phrase: Protected-file authorization checkpoint"
        in result.stdout
    )


def test_downstream_missing_marker_skips_by_default_and_fails_when_required(
    tmp_path: Path,
) -> None:
    """Downstream mode preserves the marker validator's require-marker semantics."""
    default_result = _run_validator(tmp_path, "--mode", "downstream")
    required_result = _run_validator(tmp_path, "--mode", "downstream", "--require-marker")

    assert default_result.returncode == 0, default_result.stderr
    assert "No marker found at .template-sync/marker.yml" in default_result.stdout
    assert "instruction-contract validation skipped" in default_result.stdout
    assert required_result.returncode == 1
    assert "Marker is required but was not found" in required_result.stderr


def test_upstream_mode_with_marker_present_warns_without_failing(tmp_path: Path) -> None:
    """A present marker is a non-blocking warning in upstream-template mode."""
    _write_common_contract_repo(
        tmp_path,
        _contracts(required_headings=["## Handling Code Review Comments"]),
    )
    _write_yaml(tmp_path, ".template-sync/marker.yml", {"not_template_sync": True})
    _write_text(tmp_path, "CLAUDE.md", "# Agent Instructions\n\n## Handling Code Review Comments\n")

    result = _run_validator(tmp_path, "--mode", "upstream-template")

    assert result.returncode == 0, result.stderr
    assert "WARNING: --mode upstream-template was invoked while .template-sync/marker.yml" in (
        result.stdout
    )
    assert "Instruction-contract validation passed." in result.stdout


def test_valid_downstream_waiver_is_reported_loudly(tmp_path: Path) -> None:
    """A valid marker waiver can pass validation but is not ordinary success."""
    _write_common_contract_repo(
        tmp_path,
        _contracts(required_headings=["## Handling Code Review Comments"]),
    )
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        _marker(
            ["agent-instructions"],
            waivers=[
                {
                    "path": "CLAUDE.md",
                    "anchor": "## Handling Code Review Comments",
                    "reason": "Downstream owner uses a different review protocol.",
                    "authorization_basis": "Owner authorized this waiver on 2026-05-27.",
                }
            ],
        ),
    )
    _write_text(tmp_path, "CLAUDE.md", "# Agent Instructions\n")

    result = _run_validator(tmp_path, "--mode", "downstream", "--require-marker")

    assert result.returncode == 0, result.stderr
    assert "Instruction-contract validation passed with waivers." in result.stdout
    assert "Instruction contract waivers applied:" in result.stdout
    assert "CLAUDE.md: ## Handling Code Review Comments" in result.stdout
    assert "Owner authorized this waiver on 2026-05-27." in result.stdout


def test_required_heading_inside_indented_code_block_is_not_satisfied(
    tmp_path: Path,
) -> None:
    """A heading inside an indented code block (4+ leading spaces) must not satisfy."""
    _write_common_contract_repo(
        tmp_path,
        _contracts(required_headings=["## Handling Code Review Comments"]),
    )
    _write_text(
        tmp_path,
        "CLAUDE.md",
        "# Agent Instructions\n\nSee example:\n\n    ## Handling Code Review Comments\n",
    )

    result = _run_validator(tmp_path, "--mode", "upstream-template")

    assert result.returncode == 1
    assert "CLAUDE.md: missing required heading: ## Handling Code Review Comments" in result.stdout


def test_required_heading_inside_tab_indented_line_is_not_satisfied(
    tmp_path: Path,
) -> None:
    """A heading with a leading tab is treated as indented code per CommonMark."""
    _write_common_contract_repo(
        tmp_path,
        _contracts(required_headings=["## Handling Code Review Comments"]),
    )
    _write_text(
        tmp_path,
        "CLAUDE.md",
        "# Agent Instructions\n\n\t## Handling Code Review Comments\n",
    )

    result = _run_validator(tmp_path, "--mode", "upstream-template")

    assert result.returncode == 1
    assert "CLAUDE.md: missing required heading: ## Handling Code Review Comments" in result.stdout


def test_required_heading_with_three_leading_spaces_is_satisfied(tmp_path: Path) -> None:
    """CommonMark allows up to 3 leading spaces for an ATX heading."""
    _write_common_contract_repo(
        tmp_path,
        _contracts(required_headings=["## Handling Code Review Comments"]),
    )
    _write_text(
        tmp_path,
        "CLAUDE.md",
        "# Agent Instructions\n\n   ## Handling Code Review Comments\n",
    )

    result = _run_validator(tmp_path, "--mode", "upstream-template")

    assert result.returncode == 0, result.stderr
    assert "Instruction-contract validation passed." in result.stdout


def test_required_heading_inside_fenced_code_block_is_not_satisfied(tmp_path: Path) -> None:
    """A heading nested inside a fenced code block must not satisfy the contract."""
    _write_common_contract_repo(
        tmp_path,
        _contracts(required_headings=["## Handling Code Review Comments"]),
    )
    _write_text(
        tmp_path,
        "CLAUDE.md",
        "# Agent Instructions\n\n```markdown\n## Handling Code Review Comments\n```\n",
    )

    result = _run_validator(tmp_path, "--mode", "upstream-template")

    assert result.returncode == 1
    assert "CLAUDE.md: missing required heading: ## Handling Code Review Comments" in result.stdout


def test_required_phrase_inside_fenced_code_block_is_not_satisfied(tmp_path: Path) -> None:
    """A phrase nested inside a fenced code block must not satisfy the contract."""
    _write_common_contract_repo(
        tmp_path,
        _contracts(required_phrases=["Protected-file authorization checkpoint"]),
    )
    _write_text(
        tmp_path,
        "CLAUDE.md",
        "# Agent Instructions\n\n~~~text\nProtected-file authorization checkpoint\n~~~\n",
    )

    result = _run_validator(tmp_path, "--mode", "upstream-template")

    assert result.returncode == 1
    assert (
        "CLAUDE.md: missing required phrase: Protected-file authorization checkpoint"
        in result.stdout
    )


def test_upstream_mode_skip_if_marker_present_exits_zero_without_validating(
    tmp_path: Path,
) -> None:
    """--skip-if-marker-present makes upstream-template mode a no-op downstream."""
    _write_common_contract_repo(
        tmp_path,
        _contracts(required_headings=["## Handling Code Review Comments"]),
    )
    _write_yaml(tmp_path, ".template-sync/marker.yml", _marker(["agent-instructions"]))
    _write_text(tmp_path, "CLAUDE.md", "# Agent Instructions\n")

    result = _run_validator(
        tmp_path,
        "--mode",
        "upstream-template",
        "--skip-if-marker-present",
    )

    assert result.returncode == 0, result.stderr
    assert "--mode upstream-template skipped" in result.stdout
    assert ".template-sync/marker.yml" in result.stdout
    assert "Instruction-contract validation failed." not in result.stdout


def test_upstream_mode_skip_if_marker_present_runs_when_marker_absent(
    tmp_path: Path,
) -> None:
    """--skip-if-marker-present has no effect when the marker is absent."""
    _write_common_contract_repo(
        tmp_path,
        _contracts(required_headings=["## Handling Code Review Comments"]),
    )
    _write_text(tmp_path, "CLAUDE.md", "# Agent Instructions\n")

    result = _run_validator(
        tmp_path,
        "--mode",
        "upstream-template",
        "--skip-if-marker-present",
    )

    assert result.returncode == 1
    assert "CLAUDE.md: missing required heading: ## Handling Code Review Comments" in result.stdout


def test_downstream_skips_azure_devops_contract_when_module_excluded(
    tmp_path: Path,
) -> None:
    """Azure-specific contracts are not mandatory for GitHub-only adopters."""
    _write_common_contract_repo(tmp_path, _host_specific_contracts())
    _write_yaml(tmp_path, ".template-sync/marker.yml", _marker(["agent-instructions"]))
    _write_text(tmp_path, "CLAUDE.md", "# Agent Instructions\n\n## Handling Code Review Comments\n")

    result = _run_validator(tmp_path, "--mode", "downstream", "--require-marker")

    assert result.returncode == 0, result.stderr
    assert "Instruction-contract validation passed." in result.stdout
    # CLAUDE.md is checked while the Azure-only GEMINI.md contract is skipped
    # because azure-devops-collaboration is not retained. Assert on these stable
    # signals rather than the exact skipped-contract line, whose module ordering
    # and phrasing are incidental formatting details.
    assert "Contracts checked: 1" in result.stdout
    skipped_entries = _section_entries(
        result.stdout, "Contracts skipped by downstream module selection"
    )
    assert len(skipped_entries) == 1
    (skipped_entry,) = skipped_entries
    assert skipped_entry.startswith("GEMINI.md ")
    assert "azure-devops-collaboration" in skipped_entry


def test_downstream_checks_azure_devops_contract_when_module_retained(
    tmp_path: Path,
) -> None:
    """Azure-specific contracts are enforced only when their Azure module is retained."""
    _write_common_contract_repo(tmp_path, _host_specific_contracts())
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        _marker(["agent-instructions", "azure-devops-collaboration"]),
    )
    _write_text(tmp_path, "CLAUDE.md", "# Agent Instructions\n\n## Handling Code Review Comments\n")
    _write_text(tmp_path, "GEMINI.md", "# Agent Instructions\n")

    result = _run_validator(tmp_path, "--mode", "downstream", "--require-marker")

    assert result.returncode == 1
    assert "Instruction-contract validation failed." in result.stdout
    assert (
        "GEMINI.md: missing required heading: ## Azure DevOps PR Review Protocol" in result.stdout
    )


def test_downstream_duplicate_waiver_pairs_fail(tmp_path: Path) -> None:
    """Duplicate (path, anchor) waivers fail fast instead of silently de-duplicating."""
    _write_common_contract_repo(
        tmp_path,
        _contracts(required_headings=["## Handling Code Review Comments"]),
    )
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        _marker(
            ["agent-instructions"],
            waivers=[
                {
                    "path": "CLAUDE.md",
                    "anchor": "## Handling Code Review Comments",
                    "reason": "First waiver.",
                    "authorization_basis": "Owner authorized this waiver on 2026-05-27.",
                },
                {
                    "path": "CLAUDE.md",
                    "anchor": "## Handling Code Review Comments",
                    "reason": "Conflicting second waiver for the same anchor.",
                    "authorization_basis": "Owner re-authorized on 2026-05-27.",
                },
            ],
        ),
    )
    _write_text(tmp_path, "CLAUDE.md", "# Agent Instructions\n")

    result = _run_validator(tmp_path, "--mode", "downstream", "--require-marker")

    assert result.returncode == 1
    assert (
        "Duplicate template_sync.instruction_contract_waivers (path, anchor) pair(s):"
        in result.stderr
    )
    assert "(CLAUDE.md, ## Handling Code Review Comments)" in result.stderr


def test_file_absent_without_authorized_remove_local_fails(tmp_path: Path) -> None:
    """A retained contract file cannot disappear without protected-file authorization."""
    _write_common_contract_repo(
        tmp_path,
        _contracts(required_headings=["## Handling Code Review Comments"]),
    )
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        _marker(["agent-instructions"]),
    )

    result = _run_validator(tmp_path, "--mode", "downstream", "--require-marker")

    assert result.returncode == 1
    assert "Required instruction files absent without authorized removal:" in result.stdout
    assert "CLAUDE.md" in result.stdout


def test_file_absent_with_authorized_remove_local_is_visible_skip(tmp_path: Path) -> None:
    """An authorized protected-file removal skips anchors visibly."""
    _write_common_contract_repo(
        tmp_path,
        _contracts(required_headings=["## Handling Code Review Comments"]),
    )
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        _marker(
            ["agent-instructions"],
            protected_decisions=[
                {
                    "path": "CLAUDE.md",
                    "decision": "REMOVE-LOCAL",
                    "authorization_basis": "Owner explicitly authorized removing CLAUDE.md.",
                    "authorized_scope": "CLAUDE.md only.",
                    "reason": "Claude agent is not used by this downstream repository.",
                }
            ],
        ),
    )

    result = _run_validator(tmp_path, "--mode", "downstream", "--require-marker")

    assert result.returncode == 0, result.stderr
    assert "Authorized removals skipped:" in result.stdout
    assert "CLAUDE.md" in result.stdout
    assert "Owner explicitly authorized removing CLAUDE.md." in result.stdout
