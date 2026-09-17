"""Exercise instruction-contract validation for protected agent protocols."""

from __future__ import annotations

import copy
import hashlib
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from tests._pytest_compat import pytest

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
    protected_guide_waivers: list[dict[str, str]] | None = None,
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
    if protected_guide_waivers is not None:
        template_sync["protected_guide_contract_waivers"] = protected_guide_waivers
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
    assert "Contracts checked: 5" in result.stdout


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


def test_blockquote_fence_closure_allows_later_required_heading(
    tmp_path: Path,
) -> None:
    """Instruction contracts use the shared GFM containing-block fence boundary."""
    _write_common_contract_repo(
        tmp_path,
        _contracts(required_headings=["## Handling Code Review Comments"]),
    )
    _write_text(
        tmp_path,
        "CLAUDE.md",
        (
            "# Agent Instructions\n\n"
            "> ```\n"
            "> ## Handling Code Review Comments\n"
            "\n"
            "## Handling Code Review Comments\n"
        ),
    )

    result = _run_validator(tmp_path, "--mode", "upstream-template")

    assert result.returncode == 0, result.stderr
    assert "Instruction-contract validation passed." in result.stdout


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


def test_downstream_stale_protected_guide_section_fails_when_module_excluded(
    tmp_path: Path,
) -> None:
    """Protected-guide sections for excluded modules need owner review or a waiver."""
    contracts = _contracts(required_headings=["## Handling Code Review Comments"])
    contracts["protected_guide_section_obligations"] = [
        {
            "key": "agents-azure-devops-pr-review-protocol",
            "path": "AGENTS.md",
            "target_modules": ["azure-devops-collaboration"],
            "stale_headings": ["## Azure DevOps PR Review Protocol"],
        }
    ]
    _write_common_contract_repo(tmp_path, contracts)
    _write_yaml(tmp_path, ".template-sync/marker.yml", _marker(["agent-instructions"]))
    _write_text(tmp_path, "CLAUDE.md", "## Handling Code Review Comments\n")
    _write_text(tmp_path, "AGENTS.md", "## Azure DevOps PR Review Protocol\n")

    result = _run_validator(tmp_path, "--mode", "downstream", "--require-marker")

    assert result.returncode == 1
    assert "Stale protected-guide sections requiring owner review:" in result.stdout
    assert "AGENTS.md: agents-azure-devops-pr-review-protocol: stale heading" in result.stdout


def test_downstream_stale_protected_guide_section_waiver_passes_loudly(
    tmp_path: Path,
) -> None:
    """A protected-guide section waiver passes validation but remains visible."""
    contracts = _contracts(required_headings=["## Handling Code Review Comments"])
    contracts["protected_guide_section_obligations"] = [
        {
            "key": "agents-azure-devops-pr-review-protocol",
            "path": "AGENTS.md",
            "target_modules": ["azure-devops-collaboration"],
            "stale_headings": ["## Azure DevOps PR Review Protocol"],
        }
    ]
    _write_common_contract_repo(tmp_path, contracts)
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        _marker(
            ["agent-instructions"],
            protected_guide_waivers=[
                {
                    "path": "AGENTS.md",
                    "contract_key": "agents-azure-devops-pr-review-protocol",
                    "target_module": "azure-devops-collaboration",
                    "reason": "GitHub-only fixture retains the protected Azure protocol.",
                    "authorization_basis": "Owner authorized this protected-guide waiver.",
                }
            ],
        ),
    )
    _write_text(tmp_path, "CLAUDE.md", "## Handling Code Review Comments\n")
    _write_text(tmp_path, "AGENTS.md", "## Azure DevOps PR Review Protocol\n")

    result = _run_validator(tmp_path, "--mode", "downstream", "--require-marker")

    assert result.returncode == 0, result.stderr
    assert "Instruction-contract validation passed with waivers." in result.stdout
    assert "Protected guide contract waivers applied:" in result.stdout
    assert "AGENTS.md: agents-azure-devops-pr-review-protocol" in result.stdout


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


@pytest.mark.parametrize("mode", ["upstream-template", "downstream"])
@pytest.mark.parametrize("marker", ["0.", "2.", "2)", "0002.", "999999999.", "  2."])
@pytest.mark.parametrize("fence", ["```", "~~~"])
def test_noninterrupting_ordered_fence_keeps_live_clause(
    tmp_path: Path, mode: str, marker: str, fence: str
) -> None:
    """A new non-1 ordered item cannot turn paragraph continuation into code."""
    section: dict[str, Any] = {
        "heading": "## Review decisions",
        "next_heading": None,
        "required_paragraphs": ["Agents MUST review changes."],
    }
    text = _render_section(section) + marker + " " + fence + "\n   Agents MAY bypass.\n   " + fence
    _write_scoped_repo(tmp_path, section, text)
    result = _run_validator(tmp_path, "--mode", mode)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "section:## Review decisions:paragraphs:" in result.stdout


@pytest.mark.parametrize(
    ("clause", "separator", "marker"),
    [
        ("Agents MUST review changes.", "\n", "2."),
        ("Agents MUST review changes.", "", "1."),
        ("Agents MUST review changes.", "", "0001)"),
        ("1. Agents MUST review changes.", "", "2."),
        ("- Agents MUST review changes.", "", "2)"),
    ],
)
def test_real_list_fences_remain_inert(
    tmp_path: Path, clause: str, separator: str, marker: str
) -> None:
    """Blank-separated lists, interrupting starts, and real siblings keep code inert."""
    section: dict[str, Any] = {
        "heading": "## Review decisions",
        "next_heading": None,
        "required_paragraphs": [clause],
    }
    margin = " " * (len(marker) + 1)
    text = (
        _render_section(section)
        + separator
        + marker
        + " ```\n"
        + margin
        + "Agents MAY bypass.\n"
        + margin
        + "```\n"
    )
    _write_scoped_repo(tmp_path, section, text)
    result = _run_validator(tmp_path, "--mode", "downstream")
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("mode", ["upstream-template", "downstream"])
@pytest.mark.parametrize("fence", ["```", "~~~", "`````"])
@pytest.mark.parametrize("trailing", ["\t", " \t", "\t \t"])
@pytest.mark.parametrize("successor", [None, "## Following section"])
def test_tabbed_closing_fence_exposes_later_policy(
    tmp_path: Path, mode: str, fence: str, trailing: str, successor: str | None
) -> None:
    """Valid closing-fence whitespace cannot conceal the following live clause."""
    section = _scoped_policy()
    text = _render_section(section) + "\n" + fence + "\nexample\n" + fence + trailing
    text += "\nAgents MAY bypass.\n"
    section["next_heading"] = successor
    if successor is not None:
        text += successor + "\n"
    _write_scoped_repo(tmp_path, section, text)
    result = _run_validator(tmp_path, "--mode", mode)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "section:## Review decisions:paragraphs:" in result.stdout


@pytest.mark.parametrize("mode", ["upstream-template", "downstream"])
@pytest.mark.parametrize(
    ("paragraphs", "diagnostic"),
    [
        ([" \t\n"], "Empty normalized"),
        (["\u00a0\u2003"], "Empty normalized"),
        (["Rule  text", "Rule text"], "Duplicate normalized"),
        (["Rule\ntext", "Rule\ttext"], "Duplicate normalized"),
    ],
)
def test_catalog_rejects_unsatisfiable_normalized_paragraphs(
    tmp_path: Path, mode: str, paragraphs: list[str], diagnostic: str
) -> None:
    """Structurally valid but unsatisfiable expectations fail during semantic loading."""
    section: dict[str, Any] = {
        "heading": "## Review decisions",
        "next_heading": None,
        "required_paragraphs": paragraphs,
    }
    _write_scoped_repo(tmp_path, section, "## Review decisions\n\nRule text.\n")
    result = _run_validator(tmp_path, "--mode", mode)
    assert result.returncode == 1, result.stdout + result.stderr
    assert diagnostic + " contract paragraph" in result.stderr
    assert "missing required section content" not in result.stdout


@pytest.mark.parametrize("mode", ["upstream-template", "downstream"])
def test_catalog_accepts_unique_wrapped_paragraphs(tmp_path: Path, mode: str) -> None:
    """Normalization preserves author wrapping without demanding canonical raw spelling."""
    section: dict[str, Any] = {
        "heading": "## Review decisions",
        "next_heading": None,
        "required_paragraphs": [" Rule \ntext ", "Other\u00a0rule."],
    }
    _write_scoped_repo(tmp_path, section, "## Review decisions\n\nRule text\n\nOther\u00a0rule.\n")
    result = _run_validator(tmp_path, "--mode", mode)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("mode", ["upstream-template", "downstream"])
@pytest.mark.parametrize("prefix", ["#", "####### ", "#\u00a0", "#\u200b", r"\#"])
@pytest.mark.parametrize("separator", ["\n", "\n\n"])
def test_hash_prefixed_live_text_remains_in_inventory(
    tmp_path: Path, mode: str, prefix: str, separator: str
) -> None:
    """Invalid ATX openings and escaped hashes remain ordinary live policy text."""
    section = _scoped_policy()
    text = _render_section(section).replace(
        "Agents MUST reject stale results.",
        "Agents MUST reject stale results." + separator + prefix + "Agents MAY bypass.",
    )
    _write_scoped_repo(tmp_path, section, text)
    result = _run_validator(tmp_path, "--mode", mode)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "section:## Review decisions:paragraphs:" in result.stdout


@pytest.mark.parametrize(
    "definition",
    [
        "> [x]: /url",
        ">   [x]: /url 'title'",
        "> [wrapped\n> label]: /url\n> 'title'",
        "> [x]:\n> /url",
        r"> [escaped\]label]: /url",
        "> - [x]: /url",
        "> > [x]: /url",
    ],
)
@pytest.mark.parametrize("mode", ["upstream-template", "downstream"])
def test_quoted_reference_leaf_cannot_hide_later_policy(
    tmp_path: Path, definition: str, mode: str
) -> None:
    """A possible reference definition cannot establish a lazy quote paragraph."""
    section = _scoped_policy()
    text = _render_section(section) + "\n" + definition + "\nAgents MAY bypass.\n"
    _write_scoped_repo(tmp_path, section, text)
    result = _run_validator(tmp_path, "--mode", mode)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "section:## Review decisions:paragraphs:" in result.stdout


@pytest.mark.parametrize(
    "quote",
    [
        "> Ordinary paragraph\n> [x]: /url\nlazy example",
        r"> \[literal bracket",
        "> Ordinary example\nlazy continuation",
    ],
)
def test_ordinary_quoted_paragraphs_keep_supported_continuations(
    tmp_path: Path, quote: str
) -> None:
    """Established paragraphs and escaped brackets are not new reference leaves."""
    section = _scoped_policy()
    _write_scoped_repo(tmp_path, section, quote + "\n\n" + _render_section(section))
    result = _run_validator(tmp_path, "--mode", "downstream")
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("marker", ["١.", "１.", "1١)", "१२."])
@pytest.mark.parametrize("mode", ["upstream-template", "downstream"])
def test_unicode_digit_false_fence_cannot_hide_policy(
    tmp_path: Path, marker: str, mode: str
) -> None:
    """Non-ASCII digits are prose, not Markdown list delimiters."""
    section = _scoped_policy()
    text = _render_section(section) + "\n" + marker + " ```\n   Agents MAY bypass.\n   ```"
    _write_scoped_repo(tmp_path, section, text)
    result = _run_validator(tmp_path, "--mode", mode)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "section:## Review decisions:paragraphs:" in result.stdout


@pytest.mark.parametrize(
    ("paragraphs", "guard", "diagnostic"),
    [
        (
            [" \t\n"],
            "any(not value or value.isspace() for value in normalized_paragraphs)",
            "Empty normalized",
        ),
        (
            ["Rule  text", "Rule text"],
            "len(set(normalized_paragraphs)) != len(normalized_paragraphs)",
            "Duplicate normalized",
        ),
    ],
)
def test_paragraph_loading_oracle_detects_removed_guard(
    tmp_path: Path, paragraphs: list[str], guard: str, diagnostic: str
) -> None:
    """An independent malformed catalog must fail at loading, before document drift."""
    fixture = tmp_path / "fixture"
    section: dict[str, Any] = {
        "heading": "## Review decisions",
        "next_heading": None,
        "required_paragraphs": paragraphs,
    }
    _write_scoped_repo(fixture, section, "## Review decisions\n\nRule text\n")
    baseline = _run_validator(fixture, "--mode", "downstream")
    assert baseline.returncode == 1, baseline.stdout + baseline.stderr
    assert diagnostic + " contract paragraph" in baseline.stderr
    mutant_dir = tmp_path / "mutant"
    mutant_dir.mkdir()
    for source in SCRIPT_PATH.parent.glob("*.py"):
        shutil.copyfile(source, mutant_dir / source.name)
    mutant = mutant_dir / SCRIPT_PATH.name
    source_text = mutant.read_text(encoding="utf-8")
    assert source_text.count(guard) == 1
    mutant.write_text(source_text.replace(guard, "False"), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(mutant), "--repo-root", str(fixture), "--mode", "downstream"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert diagnostic + " contract paragraph" not in result.stderr
    assert "missing required section content" in result.stdout
    assert baseline.stderr != result.stderr, "The early-error oracle must kill this mutant."


@pytest.mark.parametrize("mode", ["upstream-template", "downstream"])
@pytest.mark.parametrize(
    "literal", ["\v", "\f", "\x1c", "\x1d", "\x1e", "\x85", "\u2028", "\u2029"]
)
@pytest.mark.parametrize("fence", ["```", "~~~"])
def test_nonphysical_separator_cannot_expose_a_required_clause(
    tmp_path: Path, mode: str, literal: str, fence: str
) -> None:
    """A non-CR/LF suffix leaves the sole obligation inside literal fenced code."""
    section: dict[str, Any] = {
        "heading": "## Review decisions",
        "next_heading": None,
        "required_paragraphs": ["Agents MUST reject stale results."],
    }
    text = section["heading"] + "\n\n" + fence + "\nexample\n" + fence + literal
    text += "\n" + section["required_paragraphs"][0] + "\n"
    _write_scoped_repo(tmp_path, section, text)
    result = _run_validator(tmp_path, "--mode", mode)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "section:## Review decisions:paragraph:" in result.stdout


@pytest.mark.parametrize("mode", ["upstream-template", "downstream"])
@pytest.mark.parametrize(
    "literal",
    ["\v", "\f", "\x1c", "\x1d", "\x1e", "\x85", "\u2028", "\u2029", "\u00a0", "\u2003", "\x1f"],
)
@pytest.mark.parametrize("position", ["prefix", "suffix"])
def test_non_ascii_whitespace_cannot_supply_required_headings(
    tmp_path: Path, mode: str, literal: str, position: str
) -> None:
    """Neither loose nor section headings discard literal Unicode/control characters."""
    section = _scoped_policy()
    heading = section["heading"]
    fake = literal + heading if position == "prefix" else heading + literal
    text = _render_section(section).replace(heading, fake, 1)
    _write_scoped_repo(tmp_path, section, text)
    contracts = _contracts(required_headings=[heading])
    contracts["instruction_contracts"][0]["required_sections"] = [section]
    _write_yaml(tmp_path, ".template-sync/instruction-contracts.yml", contracts)
    result = _run_validator(tmp_path, "--mode", mode)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "missing required heading: ## Review decisions" in result.stdout
    assert "missing required section content: section:## Review decisions" in result.stdout


@pytest.mark.parametrize("kind", ["splitlines", "strip"])
def test_physical_line_and_heading_oracle_detects_removed_guard(tmp_path: Path, kind: str) -> None:
    """Restoring Python's broader semantics falsely accepts independently invalid input."""
    section: dict[str, Any] = {
        "heading": "## Review decisions",
        "next_heading": None,
        "required_paragraphs": ["Agents MUST reject stale results."],
    }
    if kind == "splitlines":
        text = section["heading"] + "\n\n```\nexample\n```\v\n"
        text += section["required_paragraphs"][0]
        original, replacement = "lines = markdown_lines(text)", "lines = text.splitlines()"
    else:
        text = "\u00a0" + _render_section(section)
        original = 'observed = "".join(visible).strip(" \\t")'
        replacement = 'observed = "".join(visible).strip()'
    fixture = tmp_path / "fixture"
    _write_scoped_repo(fixture, section, text)
    baseline = _run_validator(fixture, "--mode", "downstream")
    assert baseline.returncode == 1, baseline.stdout + baseline.stderr
    mutant_dir = tmp_path / "mutant"
    mutant_dir.mkdir()
    for source in SCRIPT_PATH.parent.glob("*.py"):
        shutil.copyfile(source, mutant_dir / source.name)
    mutant = mutant_dir / SCRIPT_PATH.name
    source_text = mutant.read_text(encoding="utf-8")
    assert source_text.count(original) == 1
    mutant.write_text(source_text.replace(original, replacement), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(mutant), "--repo-root", str(fixture), "--mode", "downstream"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_non_ascii_blank_lines_preserve_quote_and_code_span_state() -> None:
    """Literal whitespace cannot reset unsupported quotes or inline span boundaries."""
    program = r"""
import sys
sys.path.insert(0, sys.argv[1])
import validate_instruction_contracts as validator
for literal in ("\v", "\f", "\x1c", "\x1d", "\x1e", "\x85", "\u2028", "\u2029", "\u00a0", "\u2003", "\x1f"):
    lines = ["`start", literal, "end`"]
    assert validator.policy_code_span_ends(lines)[(0, 0)] == (2, 4)
    observed = validator.operative_markdown_lines("> <unsupported>\n" + literal + "\nAgents MUST act.")
    assert observed[-1] == "[unsupported quoted policy] Agents MUST act."
for blank in ("", " ", "\t", " \t"):
    assert validator.policy_code_span_ends(["`start", blank, "end`"]) == {}
    observed = validator.operative_markdown_lines("> <unsupported>\n" + blank + "\nAgents MUST act.")
    assert observed[-1] == "Agents MUST act."
"""
    result = subprocess.run(
        [sys.executable, "-c", program, str(SCRIPT_PATH.parent)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("mode", ["upstream-template", "downstream"])
def test_physical_lines_preserve_literal_boundaries_and_ascii_headings(
    tmp_path: Path, mode: str
) -> None:
    """Unicode inside a fence stays inert; supported ASCII headings remain operative."""
    section = _scoped_policy()
    for indent in range(4):
        text = _render_section(section).replace(
            section["heading"], " " * indent + section["heading"] + " \t", 1
        )
        for literal in ("\v", "\f", "\x1c", "\x1d", "\x1e", "\x85", "\u2028", "\u2029"):
            text += "\n~~~\nexample\n~~~" + literal + "\n## Inert example heading\n~~~\n"
        _write_scoped_repo(tmp_path, section, text)
        result = _run_validator(tmp_path, "--mode", mode)
        assert result.returncode == 0, result.stdout + result.stderr


def _scoped_policy() -> dict[str, Any]:
    """Provide an independent security/failure-truth oracle for parser tests."""
    return {
        "heading": "## Review decisions",
        "next_heading": None,
        "required_paragraphs": [
            "Agents MUST reject stale results.",
            "Retry delivery after 120 seconds, at most twice.",
        ],
        "required_tables": [
            {
                "headers": ["State", "Action", "Gate"],
                "rows": [
                    ["Failed", "Retry only failed service, at most three attempts", "Not clean"],
                    ["Stale", "Count toward ten complete pending observations", "Unknown"],
                    ["One clean service", "Continue the other service", "Incomplete"],
                    ["Both clean", "Reconcile all findings and CI", "Review complete"],
                ],
            }
        ],
    }


def _render_section(section: dict[str, Any]) -> str:
    """Render fixture input independently of the production Markdown parser."""
    blocks = [section["heading"], *section.get("required_paragraphs", [])]
    for table in section.get("required_tables", []):
        lines = ["| " + " | ".join(table["headers"]) + " |"]
        lines.append("| " + " | ".join("---" for _ in table["headers"]) + " |")
        lines.extend("| " + " | ".join(row) + " |" for row in table["rows"])
        blocks.append("\n".join(lines))
    if section.get("next_heading") is not None:
        blocks.append(section["next_heading"])
    return "\n\n".join(blocks) + "\n"


def _write_scoped_repo(tmp_path: Path, section: dict[str, Any], text: str) -> None:
    """Use a portable retained-agent fixture, never optional upstream files."""
    contracts = _contracts()
    contracts["instruction_contracts"][0]["required_sections"] = [section]
    _write_common_contract_repo(tmp_path, contracts)
    _write_text(tmp_path, "CLAUDE.md", text)
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        _marker(sorted({"agent-instructions", *section.get("requires_modules", [])})),
    )


@pytest.mark.parametrize("mode", ["upstream-template", "downstream"])
def test_scoped_policy_cli_accepts_complete_live_content(tmp_path: Path, mode: str) -> None:
    """Full clauses and decision rows are accepted in both supported modes."""
    section = _scoped_policy()
    _write_scoped_repo(tmp_path, section, _render_section(section))
    result = _run_validator(tmp_path, "--mode", mode)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    ("original", "replacement"),
    [
        ("MUST reject", "MAY reject"),
        ("120 seconds", "121 seconds"),
        ("at most twice", "without a bound"),
        ("at most three attempts", "at most four attempts"),
        ("Not clean", "Clean"),
        ("Count toward ten complete pending observations", "Reset the wait counter"),
        ("Continue the other service", "Finish the pair"),
        ("Reconcile all findings and CI", "Ignore earlier findings"),
        ("| --- | --- | --- |", "| not a delimiter | --- | --- |"),
        ("| Failed |", "| Failed | extra |"),
    ],
)
def test_scoped_policy_cli_rejects_semantic_mutations(
    tmp_path: Path, original: str, replacement: str
) -> None:
    """Independent expected failures guard retry, attribution, and completion truth."""
    section = _scoped_policy()
    _write_scoped_repo(tmp_path, section, _render_section(section).replace(original, replacement))
    result = _run_validator(tmp_path, "--mode", "downstream", "--require-marker")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "missing required section content" in result.stdout


@pytest.mark.parametrize("decoy", ["fence", "quote", "lazy-quote", "indent", "comment", "sibling"])
def test_scoped_policy_cli_rejects_inert_or_relocated_decoys(tmp_path: Path, decoy: str) -> None:
    """A complete-looking example cannot replace the operative section."""
    section = _scoped_policy()
    content = _render_section(section)
    if decoy == "fence":
        content = "```markdown\n" + content + "```\n"
    elif decoy == "quote":
        content = "\n".join("> " + line for line in content.splitlines())
    elif decoy == "lazy-quote":
        content = (
            section["heading"]
            + "\n\n> Example only\n"
            + "\n".join(section["required_paragraphs"])
            + "\n"
        )
    elif decoy == "indent":
        content = "\n".join("    " + line for line in content.splitlines())
    elif decoy == "comment":
        content = "<!--\n" + content + "-->\n"
    else:
        content = section["heading"] + "\n\n## Unrelated\n" + content.split("\n", 1)[1]
    _write_scoped_repo(tmp_path, section, content)
    result = _run_validator(tmp_path, "--mode", "downstream", "--require-marker")
    assert result.returncode == 1, result.stdout + result.stderr


@pytest.mark.parametrize(
    "mutation", ["heading", "table", "row", "extra", "order", "paragraph-order"]
)
def test_scoped_policy_cli_rejects_duplicates_and_reordering(tmp_path: Path, mutation: str) -> None:
    """Ambiguous sections, extra decisions, and changed execution order fail closed."""
    section = _scoped_policy()
    content = _render_section(section)
    changed = copy.deepcopy(section)
    if mutation == "heading":
        content += content
    elif mutation == "table":
        changed["required_tables"] *= 2
        content = _render_section(changed)
    elif mutation == "row":
        changed["required_tables"][0]["rows"] *= 2
        content = _render_section(changed)
    elif mutation == "extra":
        changed["required_tables"][0]["rows"].append(["Expired", "Declare success", "Clean"])
        content = _render_section(changed)
    elif mutation == "order":
        changed["required_tables"][0]["rows"].reverse()
        content = _render_section(changed)
    else:
        changed["required_paragraphs"].reverse()
        content = _render_section(changed)
    _write_scoped_repo(tmp_path, section, content)
    result = _run_validator(tmp_path, "--mode", "downstream", "--require-marker")
    assert result.returncode == 1, result.stdout + result.stderr


def _catalog_sections() -> list[Any]:
    """Collect catalog data retained by template-sync support in downstream trees."""
    catalog = yaml.safe_load(
        (REPO_ROOT / ".template-sync/instruction-contracts.yml").read_text(encoding="utf-8")
    )
    return [
        pytest.param(
            section,
            sorted(set(contract["requires_modules"]) | set(section.get("requires_modules", []))),
            id=f"{contract['path']}:{section['heading']}",
        )
        for contract in catalog["instruction_contracts"]
        for section in contract.get("required_sections", [])
    ]


@pytest.mark.parametrize(("section", "modules"), _catalog_sections())
def test_every_catalog_invariant_has_downstream_cli_mutation_coverage(
    tmp_path: Path, section: dict[str, Any], modules: list[str]
) -> None:
    """Every retained contract clause/row is enforced without optional source files.

    The fixture is contract data; the expected native failure is independent of
    the production predicates. Disabling either validation loop makes this test
    fail. This suite deliberately remains enabled under downstream selection.
    """
    content = _render_section(section)
    _write_scoped_repo(tmp_path, section, content)
    shutil.copyfile(
        REPO_ROOT / ".template-sync/manifest.yml", tmp_path / ".template-sync/manifest.yml"
    )
    _write_yaml(tmp_path, ".template-sync/marker.yml", _marker(modules))
    result = _run_validator(tmp_path, "--mode", "downstream", "--require-marker")
    assert result.returncode == 0, result.stdout + result.stderr
    mutations: list[str] = []
    for paragraph in section.get("required_paragraphs", []):
        mutations.append(content.replace(paragraph, "Removed obligation.", 1))
    for table in section.get("required_tables", []):
        for row in table["rows"]:
            original = "| " + " | ".join(row) + " |"
            mutations.append(
                content.replace(original, original.replace(row[-1], "Changed gate"), 1)
            )
    assert mutations, "Every scoped contract must enforce actual content."
    for index, mutated in enumerate(mutations):
        _write_text(tmp_path, "CLAUDE.md", mutated)
        result = _run_validator(tmp_path, "--mode", "downstream", "--require-marker")
        assert result.returncode == 1, f"mutation {index}: {result.stdout}{result.stderr}"
        assert "missing required section content" in result.stdout


def test_scoped_waiver_is_specific_and_reported(tmp_path: Path) -> None:
    """An explicit clause waiver cannot silently waive the whole policy."""
    section = _scoped_policy()
    text = _render_section(section).replace("Agents MUST reject stale results.", "")
    _write_scoped_repo(tmp_path, section, text)
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        _marker(
            ["agent-instructions"],
            waivers=[
                {
                    "path": "CLAUDE.md",
                    "anchor": "section:## Review decisions:paragraph:"
                    + hashlib.sha256(b"Agents MUST reject stale results.").hexdigest(),
                    "reason": "Owner selected a different local review policy.",
                    "authorization_basis": "Explicit fixture owner authorization for this clause only.",
                }
            ],
        ),
    )
    result = _run_validator(tmp_path, "--mode", "downstream", "--require-marker")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "passed with waivers" in result.stdout
    _write_text(tmp_path, "CLAUDE.md", text.replace("Not clean", "Clean"))
    result = _run_validator(tmp_path, "--mode", "downstream", "--require-marker")
    assert result.returncode == 1
    assert "section:## Review decisions:tables" in result.stdout


def test_malformed_table_waiver_cannot_hide_a_weakened_clause(tmp_path: Path) -> None:
    """A waived table failure leaves independently violated paragraphs failing."""
    section = _scoped_policy()
    text = _render_section(section).replace("MUST reject", "MAY reject")
    text = text.replace("| --- | --- | --- |", "| broken | --- | --- |")
    _write_scoped_repo(tmp_path, section, text)
    initial = _run_validator(tmp_path, "--mode", "downstream", "--require-marker")
    assert initial.returncode == 1
    anchor = re.search(r"section:## Review decisions:tables:[0-9a-f]{64}", initial.stdout)
    assert anchor is not None
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        _marker(
            ["agent-instructions"],
            waivers=[
                {
                    "path": "CLAUDE.md",
                    "anchor": anchor.group(),
                    "reason": "Fixture owner permits a different table format.",
                    "authorization_basis": "Explicit authorization for this table inventory only.",
                }
            ],
        ),
    )
    result = _run_validator(tmp_path, "--mode", "downstream", "--require-marker")
    assert result.returncode == 1, result.stdout + result.stderr
    assert (
        "missing required section content: section:## Review decisions:paragraph:" in result.stdout
    )
    assert "Instruction contract waivers applied:" in result.stdout


def test_section_heading_waiver_cannot_hide_its_content(tmp_path: Path) -> None:
    """A missing-heading exception does not authorize removal of the whole policy."""
    _write_scoped_repo(tmp_path, _scoped_policy(), "# No policy\n")
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        _marker(
            ["agent-instructions"],
            waivers=[
                {
                    "path": "CLAUDE.md",
                    "anchor": "section:## Review decisions",
                    "reason": "Fixture uses a different heading.",
                    "authorization_basis": "Owner authorized the heading only.",
                }
            ],
        ),
    )
    result = _run_validator(tmp_path, "--mode", "downstream", "--require-marker")
    assert result.returncode == 1
    assert "section:## Review decisions:paragraph:" in result.stdout
    assert "section:## Review decisions:tables:" in result.stdout


def test_content_waiver_does_not_move_to_another_obligation(tmp_path: Path) -> None:
    """A changed expectation invalidates a waiver instead of reusing an ordinal."""
    section = _scoped_policy()
    section["required_paragraphs"][0] = "Agents MUST reject wrong actors."
    _write_scoped_repo(tmp_path, section, _render_section(section).replace("MUST", "MAY"))
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        _marker(
            ["agent-instructions"],
            waivers=[
                {
                    "path": "CLAUDE.md",
                    "anchor": "section:## Review decisions:paragraph:"
                    + hashlib.sha256(b"Agents MUST reject stale results.").hexdigest(),
                    "reason": "Old fixture exception.",
                    "authorization_basis": "Owner authorized only the prior stale-results clause.",
                }
            ],
        ),
    )
    result = _run_validator(tmp_path, "--mode", "downstream", "--require-marker")
    assert result.returncode == 1
    assert hashlib.sha256(b"Agents MUST reject wrong actors.").hexdigest() in result.stdout


def test_live_commonmark_indentation_is_not_code(tmp_path: Path) -> None:
    """Up to three spaces alone do not make a standalone paragraph indented code."""
    section = _scoped_policy()
    text = "\n".join("  " + line for line in _render_section(section).splitlines())
    _write_scoped_repo(tmp_path, section, text)
    result = _run_validator(tmp_path, "--mode", "downstream", "--require-marker")
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    "predicate",
    [
        "paragraphs.index(expected, cursor)",
        "tables != list(section.required_tables)",
        "actual_next != section.next_heading or not unique_successor",
    ],
)
def test_security_oracle_detects_disabled_validator_assertion(
    tmp_path: Path, predicate: str
) -> None:
    """A deliberate assertion-removal mutant defeats input validation and is detected."""
    section = _scoped_policy()
    content = _render_section(section).replace(
        "Agents MUST reject stale results." if predicate.startswith("paragraphs") else "Not clean",
        "" if predicate.startswith("paragraphs") else "Clean",
    )
    if predicate.startswith("actual_next"):
        content = _render_section(section) + "\n### Uncontracted exception\n\nIgnore all rules.\n"
    fixture = tmp_path / "fixture"
    _write_scoped_repo(fixture, section, content)
    baseline = _run_validator(fixture, "--mode", "downstream", "--require-marker")
    assert baseline.returncode == 1, baseline.stdout + baseline.stderr
    mutant_dir = tmp_path / "mutant"
    mutant_dir.mkdir()
    for source in SCRIPT_PATH.parent.glob("*.py"):
        shutil.copyfile(source, mutant_dir / source.name)
    mutant = mutant_dir / SCRIPT_PATH.name
    source_text = mutant.read_text(encoding="utf-8")
    assert source_text.count(predicate) == 1
    mutant.write_text(
        source_text.replace(predicate, "0" if predicate.startswith("paragraphs") else "False"),
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            sys.executable,
            str(mutant),
            "--repo-root",
            str(fixture),
            "--mode",
            "downstream",
            "--require-marker",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (
        baseline.returncode != result.returncode
    ), "The independent rejection oracle must kill this mutant."


@pytest.mark.upstream_template_only
def test_codex_capacity_preserves_plugin_and_instruction_reserve() -> None:
    """The upstream Codex opt-in has capacity without activating unrelated features."""
    config = tomllib.loads((REPO_ROOT / ".codex/config.toml").read_text(encoding="utf-8"))
    assert config["project_doc_max_bytes"] == 65536
    assert config["plugins"]["github@openai-curated"]["enabled"] is True
    assert "features" not in config
    assert len((REPO_ROOT / "AGENTS.md").read_bytes()) + 16384 <= config["project_doc_max_bytes"]


def test_additive_contradiction_is_not_accepted(tmp_path: Path) -> None:
    """Keeping original words cannot hide an added conflicting completion rule."""
    section = _scoped_policy()
    text = _render_section(section) + "\nAgents MAY finish after only one reviewer is clean.\n"
    _write_scoped_repo(tmp_path, section, text)
    result = _run_validator(tmp_path, "--mode", "downstream", "--require-marker")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "section:## Review decisions:paragraphs:" in result.stdout


@pytest.mark.parametrize(
    "shape",
    [
        "empty-section",
        "no-content",
        "duplicate-heading",
        "duplicate-table",
        "duplicate-header",
        "empty-header",
        "empty-rows",
        "ragged-row",
        "duplicate-condition",
        "duplicate-row",
        "unexpected-property",
        "missing-boundary",
        "self-boundary",
    ],
)
def test_scoped_contract_cli_rejects_invalid_catalog_shapes(tmp_path: Path, shape: str) -> None:
    """Both schema and semantic shape failures stop the real CLI before evaluation."""
    section = _scoped_policy()
    content = _render_section(section)
    table = section["required_tables"][0]
    sections = [section]
    if shape == "empty-section":
        sections = []
    elif shape == "no-content":
        sections = [{"heading": section["heading"]}]
    elif shape == "duplicate-heading":
        sections.append({"heading": section["heading"], "required_paragraphs": ["Other rule."]})
    elif shape == "duplicate-table":
        duplicate = copy.deepcopy(table)
        section["required_tables"].append(duplicate)
    elif shape == "duplicate-header":
        table["headers"][1] = table["headers"][0]
    elif shape == "empty-header":
        table["headers"] = []
    elif shape == "empty-rows":
        table["rows"] = []
    elif shape == "ragged-row":
        table["rows"][0].pop()
    elif shape == "duplicate-condition":
        table["rows"][1][0] = table["rows"][0][0]
    elif shape == "duplicate-row":
        table["rows"].append(table["rows"][0][:])
    elif shape == "missing-boundary":
        del section["next_heading"]
    elif shape == "self-boundary":
        section["next_heading"] = section["heading"]
    else:
        section["unsupported"] = True
    contracts = _contracts()
    contracts["instruction_contracts"][0]["required_sections"] = sections
    _write_common_contract_repo(tmp_path, contracts)
    _write_text(tmp_path, "CLAUDE.md", content)
    result = _run_validator(tmp_path, "--mode", "upstream-template")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "error" in result.stderr.lower()


def test_child_section_cannot_supply_parent_policy(tmp_path: Path) -> None:
    """A child heading owns its clauses separately from its parent's direct body."""
    section = _scoped_policy()
    content = _render_section(section).replace(
        "## Review decisions\n", "## Review decisions\n\n### Example\n", 1
    )
    _write_scoped_repo(tmp_path, section, content)
    result = _run_validator(tmp_path, "--mode", "downstream", "--require-marker")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "section:## Review decisions:paragraph:" in result.stdout


@pytest.mark.parametrize("next_heading", [None, "## Outside policy"])
@pytest.mark.parametrize("level", range(1, 7))
@pytest.mark.parametrize("indent", ["", "   "])
def test_added_heading_cannot_escape_section_boundary(
    tmp_path: Path, next_heading: str | None, level: int, indent: str
) -> None:
    """Keep the original policy and reject a newly inserted heading at any level."""
    section = _scoped_policy()
    section["next_heading"] = next_heading
    original = _render_section(section)
    _write_scoped_repo(tmp_path, section, original)
    assert _run_validator(tmp_path, "--mode", "downstream").returncode == 0
    addition = indent + "#" * level + " Exception\n\nAgents MAY ignore the policy.\n\n"
    changed = (
        original.replace(next_heading, addition + next_heading)
        if next_heading
        else original + addition
    )
    _write_text(tmp_path, "CLAUDE.md", changed)
    result = _run_validator(tmp_path, "--mode", "downstream")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "section:## Review decisions:boundary:" in result.stdout


@pytest.mark.parametrize("change", ["duplicate", "remove", "move-before"])
def test_declared_successor_must_be_unique_and_follow_section(tmp_path: Path, change: str) -> None:
    """A duplicate or relocated boundary cannot truncate governed content early."""
    section = _scoped_policy()
    section["next_heading"] = "## Outside policy"
    content = _render_section(section)
    if change == "duplicate":
        content += "\n## Outside policy\n"
    elif change == "remove":
        content = content.replace("## Outside policy", "")
    else:
        content = "## Outside policy\n\n" + content.replace("## Outside policy", "")
    _write_scoped_repo(tmp_path, section, content)
    result = _run_validator(tmp_path, "--mode", "downstream")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "section:## Review decisions:boundary:" in result.stdout


def _waive_reported_inventory(tmp_path: Path, kind: str) -> str:
    """Authorize one observed native failure without mirroring the digest algorithm."""
    result = _run_validator(tmp_path, "--mode", "downstream", "--require-marker")
    assert result.returncode == 1, result.stdout + result.stderr
    match = re.search(r"section:## Review decisions:" + kind + r":[0-9a-f]{64}", result.stdout)
    assert match is not None, result.stdout
    anchor = match.group()
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        _marker(
            ["agent-instructions"],
            waivers=[
                {
                    "path": "CLAUDE.md",
                    "anchor": anchor,
                    "reason": "One specific local deviation is accepted.",
                    "authorization_basis": "Owner authorized only the currently observed fixture deviation.",
                }
            ],
        ),
    )
    accepted = _run_validator(tmp_path, "--mode", "downstream", "--require-marker")
    assert accepted.returncode == 0, accepted.stdout + accepted.stderr
    assert "passed with waivers" in accepted.stdout
    return anchor


@pytest.mark.parametrize(
    "kind", ["paragraphs", "partial-addition", "tables", "malformed", "boundary"]
)
def test_aggregate_waiver_cannot_authorize_a_different_deviation(tmp_path: Path, kind: str) -> None:
    """A previously authorized local difference cannot silently expand or change."""
    section = _scoped_policy()
    original = _render_section(section)
    if kind in {"paragraphs", "partial-addition"}:
        first = original + "\nAccepted local A.\n\nAccepted local B.\n"
        second = first.replace(
            "Accepted local A.", "Changed local rule." if kind == "paragraphs" else ""
        )
        anchor_kind = "paragraphs"
    elif kind == "boundary":
        first = original + "\n### Exception\n\nAccepted local A.\n"
        second = first.replace("Accepted local A.", "A different unauthorized exception.")
        anchor_kind = "boundary"
    else:
        first = original.replace("Not clean", "Accepted gate")
        if kind == "malformed":
            first = first.replace("| --- | --- | --- |", "| malformed | --- | --- |")
        second = first.replace("Accepted gate", "Different gate")
        anchor_kind = "tables"
    _write_scoped_repo(tmp_path, section, first)
    old_anchor = _waive_reported_inventory(tmp_path, anchor_kind)
    _write_text(tmp_path, "CLAUDE.md", second)
    rejected = _run_validator(tmp_path, "--mode", "downstream", "--require-marker")
    assert rejected.returncode == 1, rejected.stdout + rejected.stderr
    assert "missing required section content: " + old_anchor not in rejected.stdout
    assert (
        "missing required section content: section:## Review decisions:" + anchor_kind
        in rejected.stdout
    )
    _write_text(tmp_path, "CLAUDE.md", original)
    restored = _run_validator(tmp_path, "--mode", "downstream", "--require-marker")
    assert restored.returncode == 0, restored.stdout + restored.stderr
    assert "passed with waivers" not in restored.stdout


@pytest.mark.parametrize(
    "example",
    [
        "```html\n<!--\n```\n\n",
        "~~~html\n<!-- literal -->\n~~~\n\n",
        "<!--\n```markdown\n-->\n\n",
        "> <!-- example only\n\n",
        "    <!-- example only\n\n",
    ],
)
def test_code_or_comment_example_cannot_corrupt_following_policy(
    tmp_path: Path, example: str
) -> None:
    """Literal examples stay inert and a fence in a real comment stays commented."""
    section = _scoped_policy()
    _write_scoped_repo(tmp_path, section, example + _render_section(section))
    result = _run_validator(tmp_path, "--mode", "downstream")
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    "literal", ["`<!--`", "`<!-- example -->`", "``literal ` <!-- -->``", "\\<!--"]
)
def test_inline_code_and_escaped_comment_delimiters_remain_literal(
    tmp_path: Path, literal: str
) -> None:
    """A comment delimiter in a matched code span or after an escape is visible text."""
    section = _scoped_policy()
    section["required_paragraphs"][0] = "Agents MUST preserve " + literal + " in examples."
    _write_scoped_repo(tmp_path, section, _render_section(section))
    result = _run_validator(tmp_path, "--mode", "downstream")
    assert result.returncode == 0, result.stdout + result.stderr


def test_wrapped_inline_code_span_preserves_comment_literal(tmp_path: Path) -> None:
    """Inline code can wrap within one paragraph without turning into an HTML comment."""
    section = _scoped_policy()
    section["required_paragraphs"][
        0
    ] = "Agents MUST preserve `literal continued <!-- example -->` text."
    text = _render_section(section).replace("literal continued", "literal\ncontinued")
    _write_scoped_repo(tmp_path, section, text)
    result = _run_validator(tmp_path, "--mode", "downstream")
    assert result.returncode == 0, result.stdout + result.stderr


def test_unmatched_backtick_does_not_hide_a_live_comment(tmp_path: Path) -> None:
    """Unmatched literal backticks cannot make commented obligations operative."""
    section = _scoped_policy()
    clause = section["required_paragraphs"][0]
    text = _render_section(section).replace(clause, "Unmatched ` <!-- " + clause + " -->", 1)
    _write_scoped_repo(tmp_path, section, text)
    result = _run_validator(tmp_path, "--mode", "downstream")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "section:## Review decisions:paragraph:" in result.stdout


@pytest.mark.parametrize(
    "example",
    [
        "```markdown\n### Example heading\n```",
        "> ### Example heading",
        "    ### Example heading",
        "<!--\n### Example heading\n-->",
    ],
)
def test_inert_headings_do_not_change_a_declared_boundary(tmp_path: Path, example: str) -> None:
    """Only live headings can interrupt a section's declared successor relation."""
    section = _scoped_policy()
    section["next_heading"] = "## Outside policy"
    text = _render_section(section).replace("## Outside policy", example + "\n\n## Outside policy")
    text += "\nThis unrelated section can have its own uncontracted content.\n"
    _write_scoped_repo(tmp_path, section, text)
    result = _run_validator(tmp_path, "--mode", "downstream")
    assert result.returncode == 0, result.stdout + result.stderr


def test_indented_pseudoheading_cannot_end_a_lazy_quote(tmp_path: Path) -> None:
    """Four-space pseudo-headings cannot promote quoted clauses into live policy."""
    section = _scoped_policy()
    clause = section["required_paragraphs"][0]
    text = _render_section(section).replace(
        clause, "> Example paragraph\n    ### Inert pseudo-heading\n" + clause, 1
    )
    _write_scoped_repo(tmp_path, section, text)
    result = _run_validator(tmp_path, "--mode", "downstream")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "section:## Review decisions:paragraph:" in result.stdout


@pytest.mark.parametrize("indent", range(4))
def test_live_heading_ends_a_lazy_quote(tmp_path: Path, indent: int) -> None:
    """Zero-to-three-space ATX headings can start a live policy after a quote."""
    section = _scoped_policy()
    text = "> Example paragraph\n" + " " * indent + _render_section(section)
    _write_scoped_repo(tmp_path, section, text)
    result = _run_validator(tmp_path, "--mode", "downstream")
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    "quote_end",
    [
        "> note\n- Extra rule.",
        "> note\n2. Extra rule.",
        "> note\n123456789) Extra rule.",
        "> note\n-",
        "> note\n2.",
        "> note\n***",
        "> note\n---",
        "> note\n```\nliteral example\n```",
        "> note\n~~~\nliteral example\n~~~",
        "> note\n<!-- example -->",
        "> ### Example heading",
        "> > ### Nested heading",
        "> - ### List heading",
        "> ```\n> literal example\n> ```",
        "> - ```\n>   literal example\n>   ```",
        "> ~~~\n> literal example\n> ~~~",
        ">     indented example",
        "> text\n> ===",
        "> text\n> ---",
        "> text\n>",
        "> ***",
    ],
)
def test_live_policy_after_quote_blocks_cannot_disappear(tmp_path: Path, quote_end: str) -> None:
    """An outside extra clause must fail even when no blank ends the preceding quote."""
    section = _scoped_policy()
    text = _render_section(section) + "\n" + quote_end + "\nAgents MAY bypass review.\n"
    _write_scoped_repo(tmp_path, section, text)
    result = _run_validator(tmp_path, "--mode", "downstream")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "section:## Review decisions:paragraphs:" in result.stdout


@pytest.mark.parametrize(
    "quoted_paragraph",
    [
        "> Example paragraph",
        "> - Example paragraph",
        "> 2. Example paragraph",
        "> > Example paragraph",
        "> Example paragraph\n>     indented continuation",
        "> Example paragraph\n    - indented continuation",
        "> Example paragraph\n\t### indented continuation",
        "> ===",
    ],
)
def test_true_lazy_quote_cannot_supply_required_clause(
    tmp_path: Path, quoted_paragraph: str
) -> None:
    """Actual paragraph continuations remain inert, including nested/list paragraphs."""
    section = _scoped_policy()
    clause = section["required_paragraphs"][0]
    text = _render_section(section).replace(clause, quoted_paragraph + "\n" + clause, 1)
    _write_scoped_repo(tmp_path, section, text)
    result = _run_validator(tmp_path, "--mode", "downstream")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "section:## Review decisions:paragraph:" in result.stdout


@pytest.mark.parametrize(
    "example",
    [
        "> note\n```\nliteral example\n```",
        "> note\n~~~\nliteral example\n~~~",
        "> ### Example heading",
        "> ```\n> literal example\n> ```",
    ],
)
def test_known_quote_block_before_live_clause_is_accepted(tmp_path: Path, example: str) -> None:
    """Harmless supported quote/fence leaves do not hide the following required clause."""
    section = _scoped_policy()
    clause = section["required_paragraphs"][0]
    text = _render_section(section).replace(clause, example + "\n" + clause, 1)
    _write_scoped_repo(tmp_path, section, text)
    result = _run_validator(tmp_path, "--mode", "downstream")
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    "example",
    [
        "> <custom>",
        "> <!-- example -->",
        "> | example | table |\n> | --- | --- |\n> | text | text |",
        "> - > mixed nested container",
        "> paragraph\n<custom>",
    ],
)
def test_ambiguous_quote_syntax_fails_closed(tmp_path: Path, example: str) -> None:
    """Unsupported regions neither hide added policy nor supply expected live clauses."""
    section = _scoped_policy()
    original = _render_section(section)
    _write_scoped_repo(tmp_path, section, original + "\n" + example + "\nAn extra rule.\n")
    added = _run_validator(tmp_path, "--mode", "downstream")
    assert added.returncode == 1, added.stdout + added.stderr
    clause = section["required_paragraphs"][0]
    _write_text(tmp_path, "CLAUDE.md", original.replace(clause, example + "\n" + clause, 1))
    quoted = _run_validator(tmp_path, "--mode", "downstream")
    assert quoted.returncode == 1, quoted.stdout + quoted.stderr
    assert "section:## Review decisions:paragraph:" in quoted.stdout


@pytest.mark.parametrize("position", ["header", "data"])
@pytest.mark.parametrize(
    "cell",
    [
        " State",
        "State ",
        "A  B",
        "   ",
        "A\tB",
        "A\nB",
        "State\n",
        "A\u00a0B",
        "A\u001cB",
        "A\u0085B",
        "A\ufeffB",
        "",
    ],
)
def test_noncanonical_policy_cell_is_a_catalog_error(
    tmp_path: Path, position: str, cell: str
) -> None:
    """Invalid catalog spelling fails schema and semantic loading before drift checks."""
    section = _scoped_policy()
    content = _render_section(section)
    table = section["required_tables"][0]
    target = table["headers"] if position == "header" else table["rows"][0]
    target[0] = cell
    _write_scoped_repo(tmp_path, section, content)

    result = _run_validator(tmp_path, "--mode", "downstream", "--require-marker")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "error" in result.stderr.lower()
    assert "missing required section content:" not in result.stdout

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys, pathlib, yaml; sys.path.insert(0, sys.argv[1]); "
                "import validate_instruction_contracts as validator; "
                "document = yaml.safe_load(pathlib.Path(sys.argv[2]).read_text(encoding='utf-8')); "
                "validator.parse_required_sections(document['instruction_contracts'][0])"
            ),
            str(SCRIPT_PATH.parent),
            str(tmp_path / ".template-sync/instruction-contracts.yml"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "Noncanonical contract table cell: ## Review decisions" in result.stderr


@pytest.mark.parametrize("cell", ["State", "State value", "État", "状态", "Gate: `pending`"])
def test_canonical_policy_cells_remain_usable(tmp_path: Path, cell: str) -> None:
    """Single spaces, Unicode text, punctuation, and markup retain exact meaning."""
    section = _scoped_policy()
    section["required_tables"][0]["headers"][0] = cell
    section["required_tables"][0]["rows"][0][0] = cell
    _write_scoped_repo(tmp_path, section, _render_section(section))
    result = _run_validator(tmp_path, "--mode", "downstream", "--require-marker")
    assert result.returncode == 0, result.stdout + result.stderr


def test_unmatched_code_runs_have_bounded_line_visits() -> None:
    """Distinct unmatched widths cannot cause repeated scans of paragraph tails."""
    program = """
import sys
sys.path.insert(0, sys.argv[1])
import validate_instruction_contracts as validator

class BoundedLines(list):
    reads = 0
    def __getitem__(self, key):
        self.reads += len(range(*key.indices(len(self)))) if isinstance(key, slice) else 1
        assert self.reads <= 4 * len(self), "Scanner repeatedly revisited paragraph lines"
        return super().__getitem__(key)
    def __iter__(self):
        for index in range(len(self)):
            yield self[index]

source = ["literal " + chr(96) * width for width in range(1, 1001)]
lines = BoundedLines(source)

assert validator.policy_code_span_ends(lines) == {}
assert lines.reads > 0
observed = validator.operative_markdown_lines("\\n".join(source))
assert observed == source
print("Bounded scan preserved every unmatched delimiter.")
"""
    result = subprocess.run(
        [sys.executable, "-c", program, str(SCRIPT_PATH.parent)],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Bounded scan preserved every unmatched delimiter." in result.stdout


@pytest.mark.parametrize(
    "paragraph",
    [
        "A literal \\`` span <!-- marker` remains visible.",
        "A literal \\``` span <!-- marker`` remains visible.",
        "The ``outer ` inner <!-- marker`` span remains visible.",
        "The `first` and ``second`` spans remain visible.",
    ],
)
def test_indexed_inline_spans_preserve_literal_comments(tmp_path: Path, paragraph: str) -> None:
    """Escaped opener prefixes and mixed delimiter widths retain comment precedence."""
    section = _scoped_policy()
    section["required_paragraphs"][0] = paragraph
    _write_scoped_repo(tmp_path, section, _render_section(section))
    result = _run_validator(tmp_path, "--mode", "downstream", "--require-marker")
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    "parent",
    [
        "- Agents MUST review changes.",
        "+ Agents MUST review changes.",
        "1. Agents MUST review changes.",
        "10) Agents MUST review changes.",
        "-    Agents MUST review changes.",
        "-\tAgents MUST review changes.",
    ],
)
@pytest.mark.parametrize("gap", ["\n", "\n\n"])
def test_nested_list_policy_cannot_disappear(tmp_path: Path, parent: str, gap: str) -> None:
    """A nested exception remains visible across tight and loose list boundaries."""
    section: dict[str, Any] = {
        "heading": "## Review decisions",
        "next_heading": None,
        "required_paragraphs": [" ".join(parent.split())],
    }
    text = section["heading"] + "\n\n" + parent + gap + "     - Agents MAY bypass review.\n"
    _write_scoped_repo(tmp_path, section, text)
    result = _run_validator(tmp_path, "--mode", "downstream")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "section:## Review decisions:paragraphs:" in result.stdout


@pytest.mark.parametrize(
    "nested",
    [
        "    - Agents MAY bypass review.",
        "\tAgents MAY bypass review.",
        "    ### Hidden exception\n    Agents MAY bypass review.",
        "    > Agents MAY bypass review.",
        "    | Exception | Allowed |",
        "    <!-->\n    Agents MAY bypass review.",
        "    ```\n    Agents MAY bypass review.",
        "  <!-- hidden -->\n    Agents MAY bypass review.",
        "lazy continuation\n\n    Agents MAY bypass review.",
    ],
)
def test_nested_list_leaves_fail_closed(tmp_path: Path, nested: str) -> None:
    """Nested structural syntax cannot turn the rest of an item into inert content."""
    parent = "- Agents MUST review changes."
    expected = parent + " lazy continuation" if nested.startswith("lazy") else parent
    section: dict[str, Any] = {
        "heading": "## Review decisions",
        "next_heading": None,
        "required_paragraphs": [expected],
    }
    _write_scoped_repo(tmp_path, section, section["heading"] + "\n\n" + parent + "\n" + nested)
    result = _run_validator(tmp_path, "--mode", "downstream")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "section:## Review decisions:paragraphs:" in result.stdout


@pytest.mark.parametrize("sibling", ["-", "- <!-- hidden -->", "2.", "2. <!-- hidden -->"])
def test_empty_list_sibling_keeps_nested_content_live(tmp_path: Path, sibling: str) -> None:
    """An empty or commented sibling still owns a following indented paragraph."""
    parent = "- Agents MUST review changes."
    section: dict[str, Any] = {
        "heading": "## Review decisions",
        "next_heading": None,
        "required_paragraphs": [parent, sibling.split()[0]],
    }
    text = section["heading"] + "\n\n" + parent + "\n\n" + sibling
    _write_scoped_repo(tmp_path, section, text + "\n    Agents MAY bypass review.\n")
    result = _run_validator(tmp_path, "--mode", "downstream")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "section:## Review decisions:paragraphs:" in result.stdout


@pytest.mark.parametrize(
    "exit_block", ["<!-- list ends -->", "## Outside policy", "A direct paragraph.\n"]
)
def test_proven_list_exit_keeps_standalone_code_inert(tmp_path: Path, exit_block: str) -> None:
    """A dedented new block ends the list before a standalone indented example."""
    parent = "- Agents MUST review changes."
    section: dict[str, Any] = {
        "heading": "## Review decisions",
        "next_heading": None,
        "required_paragraphs": [parent],
    }
    if exit_block.startswith("#"):
        section["next_heading"] = exit_block
    elif exit_block.startswith("A"):
        section["required_paragraphs"].append(exit_block.strip())
    text = section["heading"] + "\n\n" + parent + "\n\n" + exit_block
    _write_scoped_repo(tmp_path, section, text + "\n\n    Agents MAY bypass review.\n")
    result = _run_validator(tmp_path, "--mode", "downstream")
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("indent", ["    ", "\t", "  \t"])
@pytest.mark.parametrize("gap", ["\n", "\n\n", " <!--\nhidden\n-->\n", "\n<!-- hidden -->\n"])
def test_indented_paragraph_context_controls_visibility(
    tmp_path: Path, indent: str, gap: str
) -> None:
    """Only a live paragraph continuation can make otherwise indented text operative."""
    parent = "Agents MUST review changes."
    section: dict[str, Any] = {
        "heading": "## Review decisions",
        "next_heading": None,
        "required_paragraphs": [parent],
    }
    text = section["heading"] + "\n\n" + parent + gap + indent + "Agents MAY bypass review.\n"
    _write_scoped_repo(tmp_path, section, text)
    result = _run_validator(tmp_path, "--mode", "downstream")
    expected = 1 if gap in {"\n", " <!--\nhidden\n-->\n"} else 0
    assert result.returncode == expected, result.stdout + result.stderr
    if expected:
        assert "section:## Review decisions:paragraphs:" in result.stdout


@pytest.mark.parametrize("comment", ["<!-->", "<!--->"])
@pytest.mark.parametrize("prefix", ["", " ", "  ", "   ", "<!-- ordinary -->"])
@pytest.mark.parametrize("suffix", ["\n", "\n-->\n", " <!--> <!--->\n"])
def test_short_comment_cannot_hide_later_policy(
    tmp_path: Path, comment: str, prefix: str, suffix: str
) -> None:
    """An overlapping close ends the comment before a later live extra clause."""
    section = _scoped_policy()
    text = (
        _render_section(section) + "\n" + prefix + comment + suffix + "Agents MAY bypass review.\n"
    )
    _write_scoped_repo(tmp_path, section, text)
    result = _run_validator(tmp_path, "--mode", "downstream")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "section:## Review decisions:paragraphs:" in result.stdout


@pytest.mark.parametrize("comment", ["<!-->", "<!--->", "<!-- ordinary -->", "<!--\nordinary\n-->"])
def test_complete_comments_remain_inert(tmp_path: Path, comment: str) -> None:
    """Short and ordinary comments preserve surrounding required paragraph text."""
    section = _scoped_policy()
    text = _render_section(section).replace(
        "Agents MUST reject", "Agents " + comment + " MUST reject", 1
    )
    if "\n" in comment or comment in {"<!-->", "<!--->"}:
        text = comment + "\n\n" + _render_section(section)
    _write_scoped_repo(tmp_path, section, text)
    result = _run_validator(tmp_path, "--mode", "downstream")
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    "kind",
    [
        "list",
        "paragraph",
        "comment",
        "inline-comment",
        "gfm-comment",
        "ordered",
        "tab-fence",
        "hash",
        "reference",
        "unicode-list",
        "comment-space",
        "quoted-padding",
        "quoted-tab",
    ],
)
def test_security_oracle_detects_removed_scanner_guard(tmp_path: Path, kind: str) -> None:
    """Independent live-clause fixtures detect removal of each scanner safeguard."""
    clause = "- Agents MUST review changes." if kind == "list" else "Agents MUST review changes."
    section: dict[str, Any] = {
        "heading": "## Review decisions",
        "next_heading": None,
        "required_paragraphs": [clause],
    }
    extra = (
        "\n<!-->\nAgents MAY bypass review."
        if kind == "comment"
        else "\n    Agents MAY bypass review."
    )
    if kind == "inline-comment":
        extra = " <!--\nAgents MAY bypass review."
    elif kind == "gfm-comment":
        extra = " <!-- Agents MAY -- bypass review. -->"
    elif kind == "ordered":
        extra = "\n2. ```\n   Agents MAY bypass review.\n   ```"
    elif kind == "tab-fence":
        extra = "\n\n```\nexample\n```\t\nAgents MAY bypass review."
    elif kind == "hash":
        extra = "\n\n#Agents MAY bypass review."
    elif kind == "reference":
        extra = "\n\n> [x]: /url\nAgents MAY bypass review."
    elif kind == "unicode-list":
        extra = "\n\n\u0661. ```\n   Agents MAY bypass review.\n   ```"
    elif kind == "comment-space":
        extra = ""
    elif kind == "quoted-padding":
        extra = "\n\n> -     code\nAgents MAY bypass review."
    elif kind == "quoted-tab":
        extra = "\n\n> > - \tcode\nAgents MAY bypass review."
    fixture = tmp_path / "fixture"
    text = section["heading"] + "\n\n" + clause + extra
    if kind == "comment-space":
        text = text.replace("Agents MUST", "Agents<!--x-->MUST")
    _write_scoped_repo(fixture, section, text)
    baseline = _run_validator(fixture, "--mode", "downstream")
    assert baseline.returncode == 1, baseline.stdout + baseline.stderr
    assert "section:## Review decisions:paragraphs:" in baseline.stdout
    mutant_dir = tmp_path / "mutant"
    mutant_dir.mkdir()
    for source in SCRIPT_PATH.parent.glob("*.py"):
        shutil.copyfile(source, mutant_dir / source.name)
    mutant = mutant_dir / SCRIPT_PATH.name
    target = (
        mutant_dir / "template_sync_materialization_helpers.py"
        if kind in {"tab-fence", "unicode-list"}
        else mutant
    )
    source_text = target.read_text(encoding="utf-8")
    changes = {
        "list": (
            'result.append("[unsupported nested policy] " + line)',
            'result.append("")',
        ),
        "paragraph": (
            '"[unsupported indented policy] " + line if paragraph_can_continue else ""',
            '""',
        ),
        "comment": ('line.find("-->", column + 2)', 'line.find("-->", column + 4)'),
        "inline-comment": ("end == -1 and not block_comment", "False"),
        "gfm-comment": ("not block_comment and ambiguous_inline", "False"),
        "ordered": ("and int(ordered.group(1)) != 1", "and False"),
        "tab-fence": (
            'stripped[fence_length:].strip(" \\t")',
            'stripped[fence_length:].strip(" ")',
        ),
        "hash": (
            "if line and not is_policy_heading(line):",
            'if line and not line.startswith("#"):',
        ),
        "reference": ('not was_paragraph and content.lstrip(" ").startswith("[")', "False"),
        "unicode-list": (r"[0-9]{1,9}[.)]", r"\d{1,9}[.)]"),
        "comment-space": (
            "in_comment = end == -1\n                column =",
            'in_comment = end == -1\n                visible.append(" ")\n                column =',
        ),
        "quoted-padding": ('if item.group("rest").startswith(" "):', "if False:"),
        "quoted-tab": (
            'if "\\t" in prefix.group():',
            "if False:",
        ),
    }
    original, replacement = changes[kind]
    assert source_text.count(original) == (2 if kind == "unicode-list" else 1)
    target.write_text(source_text.replace(original, replacement), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(mutant), "--repo-root", str(fixture), "--mode", "downstream"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert baseline.returncode != result.returncode, "The rejection oracle must kill this mutant."


@pytest.mark.parametrize("prefix", ["", "- "])
@pytest.mark.parametrize(
    ("comment", "accepted"),
    [
        ("<!---->", True),
        ("<!-- ordinary -->", True),
        ("<!-- foo- -->", True),
        ("<!-->Agents MAY bypass -->", False),
        ("<!--->Agents MAY bypass -->", False),
        ("<!-- Agents MAY bypass --->", False),
        ("<!-- Agents MAY -- bypass -->", False),
        ("<!-->", False),
        ("<!--->", False),
    ],
)
def test_inline_comment_grammar_preserves_visible_text(
    tmp_path: Path, prefix: str, comment: str, accepted: bool
) -> None:
    """Only same-line comments shared by CommonMark and GFM can be suppressed."""
    clause = prefix + "Agents MUST review changes."
    section: dict[str, Any] = {
        "heading": "## Review decisions",
        "next_heading": None,
        "required_paragraphs": [clause],
    }
    _write_scoped_repo(tmp_path, section, section["heading"] + "\n\n" + clause + " " + comment)
    result = _run_validator(tmp_path, "--mode", "downstream")
    assert result.returncode == (0 if accepted else 1), result.stdout + result.stderr
    if not accepted:
        assert "section:## Review decisions:paragraphs:" in result.stdout


@pytest.mark.parametrize(
    "comment", ["<!-- Agents MAY -- bypass -->", "<!-- Agents MAY bypass --->"]
)
@pytest.mark.parametrize("indent", ["", " ", "  ", "   "])
def test_block_comments_keep_their_separate_grammar(
    tmp_path: Path, comment: str, indent: str
) -> None:
    """Inline grammar restrictions do not promote standalone block comment text."""
    section = _scoped_policy()
    _write_scoped_repo(tmp_path, section, indent + comment + "\n\n" + _render_section(section))
    result = _run_validator(tmp_path, "--mode", "downstream")
    assert result.returncode == 0, result.stdout + result.stderr


def test_nested_list_dedent_retains_outer_container(tmp_path: Path) -> None:
    """A nested item's larger margin cannot erase a later outer-item child."""
    section: dict[str, Any] = {
        "heading": "## Review decisions",
        "next_heading": None,
        "required_paragraphs": [
            "- Agents MUST review changes.",
            "10) Agents MUST retain evidence.",
        ],
    }
    text = "## Review decisions\n\n- Agents MUST review changes.\n  10) Agents MUST retain evidence.\n\n    Agents MAY bypass review.\n"
    _write_scoped_repo(tmp_path, section, text)
    result = _run_validator(tmp_path, "--mode", "downstream")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "section:## Review decisions:paragraphs:" in result.stdout


@pytest.mark.parametrize("content", ["### False heading", "<!--", "> False quote", "```"])
def test_indented_paragraph_structure_cannot_hide_policy(tmp_path: Path, content: str) -> None:
    """A paragraph's indented literal cannot start a suppressing block."""
    section: dict[str, Any] = {
        "heading": "## Review decisions",
        "next_heading": None,
        "required_paragraphs": ["Agents MUST review changes."],
    }
    text = (
        "## Review decisions\n\nAgents MUST review changes.\n    "
        + content
        + "\nAgents MAY bypass review.\n"
    )
    _write_scoped_repo(tmp_path, section, text)
    result = _run_validator(tmp_path, "--mode", "downstream")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "section:## Review decisions:paragraphs:" in result.stdout


def test_policy_cell_whitespace_grammar_is_portable() -> None:
    """Schema and semantic boundaries agree on explicit Unicode whitespace cases."""
    program = """
import json
import sys
from pathlib import Path
import jsonschema
sys.path.insert(0, sys.argv[1])
import validate_instruction_contracts as validator

schema = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))["$defs"]["policyCell"]
assert schema["pattern"] == validator.POLICY_CELL_PATTERN.pattern
forbidden = [
    *range(0x09, 0x0E), *range(0x1C, 0x21), 0x85, 0xA0, 0x1680,
    *range(0x2000, 0x200B), 0x2028, 0x2029, 0x202F, 0x205F, 0x3000, 0xFEFF,
]
assert len(forbidden) == 30
cases = [("", False), ("A|B", False), ("A  B", False), ("A B", True),
         ("État", True), ("状态", True), ("A" + chr(0x200B) + "B", True)]
for point in forbidden:
    character = chr(point)
    cases.extend([(character + "A", False), ("A" + character, False)])
    if point != 0x20:
        cases.append(("A" + character + "B", False))
checker = jsonschema.Draft202012Validator(schema)
for cell, expected in cases:
    assert checker.is_valid(cell) is expected, (repr(cell), "schema")
    contract = {"required_sections": [{"heading": "## Policy", "next_heading": None,
                "required_tables": [{"headers": [cell, "Gate"], "rows": [["Pending", "Wait"]]}]}]}
    try:
        validator.parse_required_sections(contract)
        accepted = True
    except validator.InstructionContractValidationError:
        accepted = False
    assert accepted is expected, (repr(cell), "semantic")
print("Explicit Unicode cell boundaries agree.")
"""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            program,
            str(SCRIPT_PATH.parent),
            str(REPO_ROOT / "schemas/template-sync-instruction-contracts.schema.json"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Explicit Unicode cell boundaries agree." in result.stdout


@pytest.mark.parametrize("parent", ["Agents MUST review changes.", "- Agents MUST review changes."])
@pytest.mark.parametrize(
    "follow_on",
    [
        "\nAgents MAY bypass review.",
        "\n  continuation\nAgents MAY bypass review.",
        "\n  continuation\n\nAgents MAY bypass review.",
        "\n- Agents MAY bypass review.",
        "\n### Exception\nAgents MAY bypass review.",
        "\n  continuation",
        "\nwrapped comment -->\nAgents MAY bypass review.",
    ],
)
def test_incomplete_inline_comment_cannot_hide_live_policy(
    tmp_path: Path, parent: str, follow_on: str
) -> None:
    """Unclosed and unsupported wrapped inline tokens remain failure inventory."""
    section: dict[str, Any] = {
        "heading": "## Review decisions",
        "next_heading": None,
        "required_paragraphs": [parent],
    }
    text = section["heading"] + "\n\n" + parent + " <!--" + follow_on
    _write_scoped_repo(tmp_path, section, text)
    result = _run_validator(tmp_path, "--mode", "downstream")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "section:## Review decisions:paragraphs:" in result.stdout


@pytest.mark.parametrize("indent", range(4))
@pytest.mark.parametrize("closed", [False, True])
def test_standalone_comment_block_cannot_supply_policy(
    tmp_path: Path, indent: int, closed: bool
) -> None:
    """True line-start HTML comment blocks remain inert even when unclosed."""
    section = _scoped_policy()
    text = " " * indent + "<!--\n" + _render_section(section) + ("-->\n" if closed else "")
    _write_scoped_repo(tmp_path, section, text)
    result = _run_validator(tmp_path, "--mode", "downstream")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "section:## Review decisions:paragraph:" in result.stdout


@pytest.mark.parametrize("mode", ["upstream-template", "downstream"])
@pytest.mark.parametrize("prefix", ["", "- "])
@pytest.mark.parametrize(
    ("visible", "expected"),
    [
        ("Agents<!--x-->MUST act.", 1),
        ("Agents<!--x--><!--y-->MUST act.", 1),
        ("Agents <!--x-->MUST act.", 0),
        ("Agents<!--x--> MUST act.", 0),
        ("Agents <!--x--> MUST act.", 0),
        ("Ag<!--x-->ents MUST act.", 0),
    ],
)
def test_inline_comments_preserve_actual_word_boundaries(
    tmp_path: Path, mode: str, prefix: str, visible: str, expected: int
) -> None:
    """Comments neither supply missing spaces nor split an existing word."""
    section: dict[str, Any] = {
        "heading": "## Review decisions",
        "next_heading": None,
        "required_paragraphs": [prefix + "Agents MUST act."],
    }
    _write_scoped_repo(tmp_path, section, section["heading"] + "\n\n" + prefix + visible)
    result = _run_validator(tmp_path, "--mode", mode)
    assert result.returncode == expected, result.stdout + result.stderr
    if expected:
        assert "section:## Review decisions:paragraphs:" in result.stdout


@pytest.mark.parametrize("mode", ["upstream-template", "downstream"])
@pytest.mark.parametrize(
    ("leaf", "is_code"),
    [
        ("> - code", False),
        ("> -    code", False),
        ("> -     code", True),
        ("> -        code", True),
        ("> 1.     code", True),
        ("> 10)     code", True),
        ("> > +     code", True),
        ("> -\tcode", None),
        ("> - \tcode", None),
        ("> 1. \tcode", None),
        ("> > 1. \tcode", None),
        ("> > - \tcode", None),
        (">\t- code", None),
        ("> \t> - code", None),
        ("> > > 10)\tcode", None),
        (" > -\tcode", None),
        ("  > 1.\tcode", None),
        ("   > > + \tcode", None),
        ("> plain\ttext", False),
        ("> - plain\ttext", False),
        ("> 1. plain\ttext", False),
        ("> prior\n> -     code", True),
    ],
)
def test_quoted_list_padding_preserves_live_and_lazy_policy(
    tmp_path: Path, mode: str, leaf: str, is_code: bool | None
) -> None:
    """Known paragraphs can continue lazily; ambiguous structural tabs fail closed."""
    clause = "Agents MUST act."
    section: dict[str, Any] = {
        "heading": "## Review decisions",
        "next_heading": None,
        "required_paragraphs": [clause],
    }
    for label, text, expected in (
        (
            "required",
            section["heading"] + "\n\n" + leaf + "\n" + clause,
            0 if is_code is True else 1,
        ),
        (
            "extra",
            _render_section(section) + "\n" + leaf + "\nAgents MAY bypass.",
            0 if is_code is False else 1,
        ),
    ):
        root = tmp_path / label
        _write_scoped_repo(root, section, text)
        result = _run_validator(root, "--mode", mode)
        assert result.returncode == expected, result.stdout + result.stderr
        if expected:
            assert "section:## Review decisions:paragraph" in result.stdout


@pytest.mark.parametrize("mode", ["upstream-template", "downstream"])
@pytest.mark.parametrize("change", ["none", "omit", "reorder", "alter", "duplicate"])
def test_distinct_same_header_tables_keep_complete_ordered_identity(
    tmp_path: Path, mode: str, change: str
) -> None:
    """Repeated column names across tables do not weaken full inventory checks."""
    section = _scoped_policy()
    second = copy.deepcopy(section["required_tables"][0])
    second["rows"] = [["Owner decision", "Keep PR open", "Not merged"]]
    section["required_tables"].append(second)
    document = copy.deepcopy(section)
    if change == "omit":
        document["required_tables"].pop()
    elif change == "reorder":
        document["required_tables"].reverse()
    elif change == "alter":
        document["required_tables"][1]["rows"][0][-1] = "Merged"
    elif change == "duplicate":
        document["required_tables"].append(copy.deepcopy(second))
    _write_scoped_repo(tmp_path, section, _render_section(document))
    result = _run_validator(tmp_path, "--mode", mode)
    assert result.returncode == (0 if change == "none" else 1), result.stdout + result.stderr
    if change != "none":
        assert "section:## Review decisions:tables:" in result.stdout


def test_semantic_loader_rejects_complete_duplicate_tables() -> None:
    """Direct semantic loading retains the duplicate guard beyond schema checks."""
    program = """
import sys
sys.path.insert(0, sys.argv[1])
import validate_instruction_contracts as validator
table = {"headers": ["State", "Action"], "rows": [["Pending", "Wait"]]}
raw = {"required_sections": [{"heading": "## Rules", "next_heading": None,
                             "required_tables": [table, table]}]}
try:
    validator.parse_required_sections(raw)
except validator.InstructionContractValidationError as error:
    assert "Duplicate contract table" in str(error), str(error)
else:
    raise AssertionError("Complete duplicate tables must fail semantic loading.")
"""
    result = subprocess.run(
        [sys.executable, "-c", program, str(SCRIPT_PATH.parent)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("mode", ["upstream-template", "downstream"])
@pytest.mark.parametrize(
    "kind",
    ["heading", "list", "ordered", "table-delimiter", "block-tail", "wrapped-block-tail"],
)
def test_comment_elision_cannot_create_policy_structure(
    tmp_path: Path, mode: str, kind: str
) -> None:
    """Inline text removal cannot create a source heading, list, or table."""
    section: dict[str, Any] = {
        "heading": "## Review decisions",
        "next_heading": None,
        "required_paragraphs": ["Agents MUST act."],
    }
    if kind == "list":
        section["required_paragraphs"] = ["- Agents MUST act."]
    elif kind == "ordered":
        section["required_paragraphs"] = ["1. Agents MUST act."]
    elif kind == "table-delimiter":
        section["required_tables"] = [
            {"headers": ["State", "Action"], "rows": [["Pending", "Wait"]]}
        ]
    text = _render_section(section)
    if kind == "heading":
        text = text.replace("## Review", "##<!--x--> Review")
    elif kind == "list":
        text = text.replace("- Agents", "-<!--x--> Agents")
    elif kind == "ordered":
        text = text.replace("1. Agents", "1.<!--x--> Agents")
    elif kind == "table-delimiter":
        text = text.replace("| --- |", "| -<!--x-->-- |", 1)
    elif kind == "block-tail":
        text = text.replace("Agents MUST", "<!--x-->Agents MUST")
    else:
        text = text.replace("Agents MUST", "<!--\nx\n-->Agents MUST")
    _write_scoped_repo(tmp_path, section, text)
    result = _run_validator(tmp_path, "--mode", mode)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "section:## Review decisions:" in result.stdout


@pytest.mark.parametrize("kind", ["heading", "list", "table", "block-tail", "wrapped-tail"])
def test_comment_structure_oracle_detects_removed_guard(tmp_path: Path, kind: str) -> None:
    """Each structural guard rejects a fixture that its removal falsely accepts."""
    section: dict[str, Any] = {
        "heading": "## Review decisions",
        "next_heading": None,
        "required_paragraphs": ["Agents MUST act."],
    }
    if kind == "list":
        section["required_paragraphs"] = ["- Agents MUST act."]
    elif kind == "table":
        section["required_tables"] = [
            {"headers": ["State", "Action"], "rows": [["Pending", "Wait"]]}
        ]
    text = _render_section(section)
    if kind == "heading":
        text = text.replace("## Review", "##<!--x--> Review")
    elif kind == "list":
        text = text.replace("- Agents", "-<!--x--> Agents")
    elif kind == "table":
        text = text.replace("| --- |", "| -<!--x-->-- |", 1)
    elif kind == "block-tail":
        text = text.replace("Agents MUST", "<!--x-->Agents MUST")
    else:
        text = text.replace("Agents MUST", "<!--\nx\n-->Agents MUST")
    root = tmp_path / "fixture"
    _write_scoped_repo(root, section, text)
    baseline = _run_validator(root, "--mode", "downstream")
    assert baseline.returncode == 1, baseline.stdout + baseline.stderr
    assert "section:## Review decisions:" in baseline.stdout

    mutant_dir = tmp_path / "mutant"
    mutant_dir.mkdir()
    for source in SCRIPT_PATH.parent.glob("*.py"):
        shutil.copyfile(source, mutant_dir / source.name)
    mutant = mutant_dir / SCRIPT_PATH.name
    source_text = mutant.read_text(encoding="utf-8")
    if kind == "block-tail":
        original = 'if block_comment and end != -1 and line[end + 3 :].strip(" \\t"):'
        replacement = "if False:"
    elif kind == "wrapped-tail":
        original = 'if line[column:].strip(" \\t"):'
        replacement = "if False:"
    else:
        original = "if elided_comment and ("
        replacement = "if False and ("
    assert source_text.count(original) == 1
    mutant.write_text(source_text.replace(original, replacement), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(mutant), "--repo-root", str(root), "--mode", "downstream"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def _module_section_repo(tmp_path: Path, text: str, modules: list[str]) -> dict[str, Any]:
    """Write an independent three-section fixture with one optional host protocol."""
    sections = [
        {
            "heading": "## Plugin",
            "next_heading": "## Azure",
            "required_paragraphs": ["Use the plugin."],
        },
        {
            "heading": "## Azure",
            "next_heading": "## Review",
            "requires_modules": ["azure-devops-collaboration"],
            "required_paragraphs": ["Keep Azure authentication secure."],
        },
        {
            "heading": "## Review",
            "next_heading": None,
            "required_paragraphs": ["Review all findings."],
        },
    ]
    contracts = _contracts()
    contracts["instruction_contracts"][0]["required_sections"] = sections
    contracts["protected_guide_section_obligations"] = [
        {
            "key": "optional-azure",
            "path": "CLAUDE.md",
            "target_modules": ["azure-devops-collaboration"],
            "stale_headings": ["## Azure"],
        }
    ]
    _write_common_contract_repo(tmp_path, contracts)
    _write_text(tmp_path, "CLAUDE.md", text)
    _write_yaml(tmp_path, ".template-sync/marker.yml", _marker(modules))
    return contracts


@pytest.mark.parametrize("mode", ["upstream-template", "downstream"])
@pytest.mark.parametrize("retained", [False, True])
@pytest.mark.parametrize("present", [False, True])
def test_module_section_applicability_cli(
    tmp_path: Path, mode: str, retained: bool, present: bool
) -> None:
    """Upstream enforces all protocols; downstream checks modules and stale retention."""
    text = "## Plugin\n\nUse the plugin.\n\n"
    if present:
        text += "## Azure\n\nKeep Azure authentication secure.\n\n"
    text += "## Review\n\nReview all findings.\n"
    modules = ["agent-instructions"] + (["azure-devops-collaboration"] if retained else [])
    _module_section_repo(tmp_path, text, modules)
    result = _run_validator(tmp_path, "--mode", mode)
    expected = (
        (0 if present else 1) if mode == "upstream-template" or retained else (1 if present else 0)
    )
    assert result.returncode == expected, result.stdout + result.stderr
    if mode == "downstream" and not retained and present:
        assert "CLAUDE.md: optional-azure: stale heading: ## Azure" in result.stdout
        _write_yaml(
            tmp_path,
            ".template-sync/marker.yml",
            _marker(
                modules,
                protected_guide_waivers=[
                    {
                        "path": "CLAUDE.md",
                        "contract_key": "optional-azure",
                        "target_module": "azure-devops-collaboration",
                        "reason": "The fixture owner retains the optional protocol.",
                        "authorization_basis": "Explicit fixture authorization for this stale section.",
                    }
                ],
            ),
        )
        waived = _run_validator(tmp_path, "--mode", mode)
        assert waived.returncode == 0, waived.stdout + waived.stderr
        assert "passed with waivers" in waived.stdout
        # The excluded host body is outside applicable section contracts. Its
        # intentional retention is governed by the separate stale-section waiver.
        _write_text(
            tmp_path,
            "CLAUDE.md",
            text.replace(
                "Keep Azure authentication secure.",
                "Local inactive host note.\n\n### Local inactive subsection",
            ),
        )
        inactive = _run_validator(tmp_path, "--mode", mode)
        assert inactive.returncode == 0, inactive.stdout + inactive.stderr


@pytest.mark.parametrize(
    "replacement",
    [
        "### Hidden exception\n\nSkip review.\n\n",
        "## Azure\n\n## Azure\n\n",
        "## Unrelated\n\n",
    ],
)
def test_module_section_traversal_rejects_unexpected_boundaries(
    tmp_path: Path, replacement: str
) -> None:
    """Excluding Azure cannot authorize arbitrary, duplicate, or inserted boundaries."""
    text = "## Plugin\n\nUse the plugin.\n\n" + replacement + "## Review\n\nReview all findings.\n"
    _module_section_repo(tmp_path, text, ["agent-instructions"])
    result = _run_validator(tmp_path, "--mode", "downstream")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "section:## Plugin:boundary:" in result.stdout


@pytest.mark.parametrize("end", ["contracted", "uncontracted", "eof"])
def test_module_section_traversal_follows_multiple_absent_successors(
    tmp_path: Path, end: str
) -> None:
    """Traversal skips declared excluded sections and stops at the explicit scope end."""
    text = "## Plugin\n\nUse the plugin.\n"
    if end != "eof":
        text += "\n## Review\n\nReview all findings.\n"
    contracts = _module_section_repo(tmp_path, text, ["agent-instructions"])
    sections = contracts["instruction_contracts"][0]["required_sections"]
    sections[1]["next_heading"] = "## Second optional"
    sections.insert(
        2,
        {
            "heading": "## Second optional",
            "next_heading": None if end == "eof" else "## Review",
            "requires_modules": ["schema"],
            "required_paragraphs": ["Keep the second protocol."],
        },
    )
    if end != "contracted":
        sections.pop()
    _write_yaml(tmp_path, ".template-sync/instruction-contracts.yml", contracts)
    result = _run_validator(tmp_path, "--mode", "downstream")
    assert result.returncode == 0, result.stdout + result.stderr
    _write_text(
        tmp_path, "CLAUDE.md", text.replace("Use the plugin.", "Use the plugin.\n\n## Intruder")
    )
    rejected = _run_validator(tmp_path, "--mode", "downstream")
    assert rejected.returncode == 1, rejected.stdout + rejected.stderr
    assert "section:## Plugin:boundary:" in rejected.stdout


@pytest.mark.parametrize("mode", ["upstream-template", "downstream"])
@pytest.mark.parametrize("value", [[], ["schema", "schema"], [3], "schema", ["unknown-module"]])
def test_section_module_catalog_rejects_invalid_requirements(
    tmp_path: Path, mode: str, value: Any
) -> None:
    """Malformed or unknown section modules are catalog errors, not skipped checks."""
    contracts = _module_section_repo(tmp_path, "", ["agent-instructions"])
    contracts["instruction_contracts"][0]["required_sections"][1]["requires_modules"] = value
    _write_yaml(tmp_path, ".template-sync/instruction-contracts.yml", contracts)
    result = _run_validator(tmp_path, "--mode", mode)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "requires_modules" in result.stderr or "unknown manifest module" in result.stderr


@pytest.mark.parametrize("mode", ["upstream-template", "downstream"])
def test_section_module_catalog_rejects_successor_cycles(tmp_path: Path, mode: str) -> None:
    """An excluded successor cycle fails loading and cannot hang traversal."""
    contracts = _module_section_repo(tmp_path, "", ["agent-instructions"])
    contracts["instruction_contracts"][0]["required_sections"][1]["next_heading"] = "## Plugin"
    _write_yaml(tmp_path, ".template-sync/instruction-contracts.yml", contracts)
    result = _run_validator(tmp_path, "--mode", mode)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "Cyclic section successor chain" in result.stderr


@pytest.mark.upstream_template_only
@pytest.mark.parametrize("mode", ["upstream-template", "downstream"])
@pytest.mark.parametrize(
    ("heading", "successor"),
    [
        ("## GitHub Plugin Usage", "## Azure DevOps PR Review Protocol"),
        ("## Azure DevOps PR Review Protocol", "## PR Review Workflow (Codex-adapted)"),
    ],
)
def test_actual_codex_protocol_removal_is_rejected(
    tmp_path: Path, mode: str, heading: str, successor: str
) -> None:
    """Real catalog coverage cannot disappear with a data-driven fixture expectation."""
    catalog = yaml.safe_load(
        (REPO_ROOT / ".template-sync/instruction-contracts.yml").read_text(encoding="utf-8")
    )
    contract = next(
        item for item in catalog["instruction_contracts"] if item["path"] == "AGENTS.md"
    )
    _write_common_contract_repo(tmp_path, {"instruction_contracts": [contract]})
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        _marker(["agent-instructions", "azure-devops-collaboration"]),
    )
    text = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    _write_text(tmp_path, "AGENTS.md", text)
    intact = _run_validator(tmp_path, "--mode", mode)
    assert intact.returncode == 0, intact.stdout + intact.stderr
    start = text.index(heading + "\n")
    end = text.index(successor + "\n", start)
    _write_text(tmp_path, "AGENTS.md", text[:start] + text[end:])
    result = _run_validator(tmp_path, "--mode", mode)
    assert result.returncode == 1, result.stdout + result.stderr
    assert f"section:{heading}" in result.stdout


@pytest.mark.parametrize("mutation", ["skip-applicable", "disable-traversal"])
def test_section_module_security_mutants_are_detected(tmp_path: Path, mutation: str) -> None:
    """Independent native expectations kill disabled applicability and traversal checks."""
    fixture = tmp_path / "fixture"
    if mutation == "skip-applicable":
        section = {
            "heading": "## Azure",
            "next_heading": None,
            "requires_modules": ["azure-devops-collaboration"],
            "required_paragraphs": ["Keep Azure authentication secure."],
        }
        _write_scoped_repo(fixture, section, "")
        predicate = "if not section_applies(section, included_modules):"
        replacement = "if section.requires_modules:"
        expected, mutant_expected = 1, 0
    else:
        _module_section_repo(
            fixture,
            "## Plugin\n\nUse the plugin.\n\n## Review\n\nReview all findings.\n",
            ["agent-instructions"],
        )
        predicate = "while successor in sections and successor not in live_lines:"
        replacement = "while False:"
        expected, mutant_expected = 0, 1
    baseline = _run_validator(fixture, "--mode", "downstream")
    assert baseline.returncode == expected, baseline.stdout + baseline.stderr
    mutant_dir = tmp_path / "mutant"
    mutant_dir.mkdir()
    for source in SCRIPT_PATH.parent.glob("*.py"):
        shutil.copyfile(source, mutant_dir / source.name)
    mutant = mutant_dir / SCRIPT_PATH.name
    source_text = mutant.read_text(encoding="utf-8")
    assert source_text.count(predicate) == 1
    mutant.write_text(source_text.replace(predicate, replacement), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(mutant), "--repo-root", str(fixture), "--mode", "downstream"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == mutant_expected, result.stdout + result.stderr
    assert result.returncode != baseline.returncode


def test_module_section_boundary_waiver_tracks_effective_successor(tmp_path: Path) -> None:
    """A waiver for excluded Azure cannot authorize a missing required Azure boundary."""
    text = "## Plugin\n\nUse the plugin.\n\n## Intruder\n\n## Review\n\nReview all findings.\n"
    _module_section_repo(tmp_path, text, ["agent-instructions"])
    anchors: list[str] = []
    for modules in (
        ["agent-instructions"],
        ["agent-instructions", "schema"],
        ["agent-instructions", "azure-devops-collaboration"],
    ):
        _write_yaml(tmp_path, ".template-sync/marker.yml", _marker(modules))
        result = _run_validator(tmp_path, "--mode", "downstream")
        assert result.returncode == 1, result.stdout + result.stderr
        match = re.search(r"section:## Plugin:boundary:[0-9a-f]{64}", result.stdout)
        assert match is not None, result.stdout
        anchors.append(match.group())
    assert (
        anchors[0] == anchors[1]
    ), "An unrelated module cannot change the same boundary deviation."
    assert (
        anchors[0] != anchors[2]
    ), "Required Azure changes the expected boundary and waiver identity."


@pytest.mark.parametrize("mode", ["upstream-template", "downstream"])
@pytest.mark.parametrize(
    ("original", "replacement"),
    [
        ("| Review state |", "| Review  state |"),
        ("| Review state |", "| Review\tstate |"),
        ("| Review state |", "| \x1cReview state |"),
        ("Not clean", "Not  clean"),
        ("Not clean", "Not\tclean"),
        ("Not clean", "Not\x1cclean"),
        ("Not clean", "Not\x85clean"),
        ("Not clean", "Not\u00a0clean"),
        ("Not clean", "Not\u2028clean"),
        ("Not clean", "Not\ufeffclean"),
        ("| --- |", "| \x1c---\x1c |"),
        ("| --- |", "| \u00a0---\u00a0 |"),
        ("| --- |", "| --\t- |"),
        ("| --- |", "| -- - |"),
    ],
)
def test_observed_table_cells_reject_noncanonical_whitespace(
    tmp_path: Path, mode: str, original: str, replacement: str
) -> None:
    """Both CLIs retain invalid header, data and delimiter cell spelling."""
    section = _scoped_policy()
    section["required_tables"][0]["headers"][0] = "Review state"
    text = _render_section(section).replace(original, replacement, 1)
    _write_scoped_repo(tmp_path, section, text)
    result = _run_validator(tmp_path, "--mode", mode)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "section:## Review decisions:tables:" in result.stdout


@pytest.mark.parametrize("padding", ["", " ", "   ", "\t", " \t"])
def test_observed_table_ascii_padding_preserves_canonical_cells(
    tmp_path: Path, padding: str
) -> None:
    """Only cell-edge syntax padding changes; Unicode words and alignment stay usable."""
    section = _scoped_policy()
    table = section["required_tables"][0]
    table["headers"][0] = "État 中文"
    text = _render_section(section)
    lines = []
    for line in text.split("\n"):
        if line.startswith("|"):
            cells = [cell.strip(" ") for cell in line[1:-1].split("|")]
            cells = [":---:" if cell == "---" else cell for cell in cells]
            line = "|" + "|".join(padding + cell + padding for cell in cells) + "|"
        lines.append(line)
    _write_scoped_repo(tmp_path, section, "\n".join(lines))
    result = _run_validator(tmp_path, "--mode", "downstream")
    assert result.returncode == 0, result.stdout + result.stderr


def test_observed_whitespace_character_matrix() -> None:
    """Literal oracles cover every explicit cell separator and paragraph character."""
    program = r"""
import sys
sys.path.insert(0, sys.argv[1])
import validate_instruction_contracts as validator
points = [
    *range(0x09, 0x0E), *range(0x1C, 0x21), 0x85, 0xA0, 0x1680,
    *range(0x2000, 0x200B), 0x2028, 0x2029, 0x202F, 0x205F, 0x3000, 0xFEFF,
]
assert len(points) == 30
for point in points:
    character = chr(point)
    variants = [character + "A B", "A" + character + "B", "A B" + character]
    for location in ("header", "data"):
        for position, value in enumerate(variants):
            lines = ["| A B | Gate |", "| --- | --- |", "| A B | Not clean |"]
            row = 0 if location == "header" else 2
            lines[row] = lines[row].replace("A B", value)
            expected = point in (0x09, 0x20) if position != 1 else point == 0x20
            try:
                validator.parse_policy_body(lines)
                accepted = True
            except validator.InstructionContractValidationError:
                accepted = False
            assert accepted is expected, (point, location, position, accepted)
    # Delimiter edges have their own structural check after cell validation.
    lines = ["| A | B |", "|" + character + "---" + character + "| --- |", "| C | D |"]
    try:
        validator.parse_policy_body(lines)
        accepted = True
    except validator.InstructionContractValidationError:
        accepted = False
    assert accepted is (point in (0x09, 0x20)), (point, "delimiter")
section = validator.RequiredSection("## Policy", ("Agents MUST act.",), ())
for point in points:
    if point in (0x09, 0x0A, 0x0D, 0x20):
        continue
    character = chr(point)
    variants = [character + "Agents MUST act.", "Agents" + character + "MUST act.",
                "Agents MUST act." + character]
    for value in variants:
        assert validator.section_failures("## Policy\n\n" + value + "\n", (section,)), point
        literal = validator.RequiredSection("## Policy", (value,), ())
        assert validator.section_failures("## Policy\n\n" + value + "\n", (literal,)) == [], point
print("Explicit observed-cell and literal-paragraph character matrices passed.")
"""
    result = subprocess.run(
        [sys.executable, "-c", program, str(SCRIPT_PATH.parent)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("mode", ["upstream-template", "downstream"])
@pytest.mark.parametrize("character", ["\x1c", "\x85", "\v", "\u00a0"])
@pytest.mark.parametrize("position", ["leading", "internal", "trailing"])
def test_paragraph_whitespace_drift_remains_literal(
    tmp_path: Path, mode: str, character: str, position: str
) -> None:
    """Replacing or adding a non-ASCII wrapping character cannot satisfy a clause."""
    section = _scoped_policy()
    original = section["required_paragraphs"][0]
    value = (
        character + original
        if position == "leading"
        else (
            original + character
            if position == "trailing"
            else original.replace("Agents MUST", "Agents" + character + "MUST")
        )
    )
    _write_scoped_repo(tmp_path, section, _render_section(section).replace(original, value))
    result = _run_validator(tmp_path, "--mode", mode)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "section:## Review decisions:paragraph:" in result.stdout
    assert "section:## Review decisions:paragraphs:" in result.stdout


@pytest.mark.parametrize("mode", ["upstream-template", "downstream"])
@pytest.mark.parametrize("wrapping", ["  ", "\t", "\n", "\r\n", "\r"])
def test_paragraph_ascii_wrapping_preserves_literal_unicode(
    tmp_path: Path, mode: str, wrapping: str
) -> None:
    """ASCII wrapping folds while distinct Unicode-bearing catalog clauses remain distinct."""
    section: dict[str, Any] = {
        "heading": "## Review decisions",
        "next_heading": None,
        "required_paragraphs": ["Agents MUST act.", "Agents\u00a0MUST act.", "État 中文."],
    }
    text = _render_section(section).replace("Agents MUST", "Agents" + wrapping + "MUST")
    _write_scoped_repo(tmp_path, section, text)
    # Preserve literal CR/LF combinations without host text-mode translation.
    (tmp_path / "CLAUDE.md").write_bytes(text.encode("utf-8"))
    result = _run_validator(tmp_path, "--mode", mode)
    assert result.returncode == 0, result.stdout + result.stderr
    (tmp_path / "CLAUDE.md").write_bytes(
        text.replace("Agents\u00a0MUST", "Agents MUST").encode("utf-8")
    )
    changed = _run_validator(tmp_path, "--mode", mode)
    assert changed.returncode == 1, changed.stdout + changed.stderr
    assert "section:## Review decisions:paragraph:" in changed.stdout


@pytest.mark.parametrize("kind", ["table", "paragraph", "boundary"])
def test_whitespace_waiver_cannot_authorize_another_deviation(tmp_path: Path, kind: str) -> None:
    """An authorized control-character deviation cannot waive another or canonical content."""
    section = _scoped_policy()
    if kind == "boundary":
        section["next_heading"] = "## End"
    canonical = _render_section(section)
    if kind == "table":
        first = canonical.replace("Not clean", "Not\x1cclean")
    elif kind == "paragraph":
        first = canonical.replace("Agents MUST", "Agents\x1cMUST")
    else:
        first = canonical.replace("## End", "## Extra\n\nLocal\x1ctext.\n\n## End")
    second = first.replace("\x1c", "\x85")
    _write_scoped_repo(tmp_path, section, first)
    initial = _run_validator(tmp_path, "--mode", "downstream", "--require-marker")
    assert initial.returncode == 1, initial.stdout + initial.stderr
    anchors = set(
        re.findall(
            r"section:## Review decisions:(?:paragraph|paragraphs|tables|boundary):[0-9a-f]{64}",
            initial.stdout,
        )
    )
    assert anchors
    _write_yaml(
        tmp_path,
        ".template-sync/marker.yml",
        _marker(
            ["agent-instructions"],
            waivers=[
                {
                    "path": "CLAUDE.md",
                    "anchor": anchor,
                    "reason": "Fixture owner accepts only this exact observed deviation.",
                    "authorization_basis": "Explicit fixture authorization for the captured text.",
                }
                for anchor in sorted(anchors)
            ],
        ),
    )
    same = _run_validator(tmp_path, "--mode", "downstream", "--require-marker")
    assert same.returncode == 0, same.stdout + same.stderr
    assert "passed with waivers" in same.stdout
    _write_text(tmp_path, "CLAUDE.md", second)
    changed = _run_validator(tmp_path, "--mode", "downstream", "--require-marker")
    assert changed.returncode == 1, changed.stdout + changed.stderr
    _write_text(tmp_path, "CLAUDE.md", canonical)
    restored = _run_validator(tmp_path, "--mode", "downstream", "--require-marker")
    assert restored.returncode == 0, restored.stdout + restored.stderr
    assert "Instruction contract waivers applied:" not in restored.stdout


@pytest.mark.parametrize("kind", ["table", "paragraph"])
def test_whitespace_matching_oracle_detects_broad_normalization(tmp_path: Path, kind: str) -> None:
    """Restoring broad folding falsely accepts an independently invalid literal fixture."""
    section = _scoped_policy()
    if kind == "table":
        text = _render_section(section).replace("Not clean", "Not\x1cclean")
        original = 'cell.strip(" \\t")'
        replacement = '" ".join(cell.split())'
    else:
        text = _render_section(section).replace("Agents MUST", "Agents\x1cMUST")
        original = 'return re.sub(r"[ \\t\\r\\n]+", " ", text).strip(" ")'
        replacement = 'return " ".join(text.split())'
    fixture = tmp_path / "fixture"
    _write_scoped_repo(fixture, section, text)
    baseline = _run_validator(fixture, "--mode", "downstream")
    assert baseline.returncode == 1, baseline.stdout + baseline.stderr
    mutant_dir = tmp_path / "mutant"
    mutant_dir.mkdir()
    for source in SCRIPT_PATH.parent.glob("*.py"):
        shutil.copyfile(source, mutant_dir / source.name)
    mutant = mutant_dir / SCRIPT_PATH.name
    source_text = mutant.read_text(encoding="utf-8")
    assert source_text.count(original) == 1
    mutant.write_text(source_text.replace(original, replacement), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(mutant), "--repo-root", str(fixture), "--mode", "downstream"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("kind", ["malformed-table", "boundary"])
def test_whitespace_identity_oracle_detects_normalized_hashes(tmp_path: Path, kind: str) -> None:
    """Distinct observed controls need distinct anchors even after another defect is waived."""
    program = r"""
import sys
sys.path.insert(0, sys.argv[1])
import validate_instruction_contracts as validator
kind = sys.argv[2]
if kind == "malformed-table":
    section = validator.RequiredSection("## Policy", (), (
        validator.RequiredTable(("State", "Gate"), (("Failed", "Not clean"),)),
    ))
    text = "## Policy\n\n| State | Gate |\n| broken | --- |\n| Failed | Not\x1cclean |\n"
    prefix = "section:## Policy:tables:"
else:
    section = validator.RequiredSection("## Policy", ("Agents MUST act.",), (), "## End")
    text = "## Policy\n\nAgents MUST act.\n\n## Extra\n\nLocal\x1ctext.\n\n## End\n"
    prefix = "section:## Policy:boundary:"
first = next(a for a in validator.section_failures(text, (section,)) if a.startswith(prefix))
second = next(a for a in validator.section_failures(text.replace("\x1c", "\x85"), (section,))
              if a.startswith(prefix))
print("distinct" if first != second else "collision")
"""
    baseline = subprocess.run(
        [sys.executable, "-c", program, str(SCRIPT_PATH.parent), kind],
        check=False,
        capture_output=True,
        text=True,
    )
    assert baseline.returncode == 0, baseline.stdout + baseline.stderr
    assert baseline.stdout.strip() == "distinct"
    mutant_dir = tmp_path / "mutant"
    mutant_dir.mkdir()
    for source in SCRIPT_PATH.parent.glob("*.py"):
        shutil.copyfile(source, mutant_dir / source.name)
    mutant = mutant_dir / SCRIPT_PATH.name
    source_text = mutant.read_text(encoding="utf-8")
    if kind == "malformed-table":
        original = '[line for line in body if line.startswith("|")]'
        replacement = '[" ".join(line.split()) for line in body if line.startswith("|")]'
    else:
        original = "[normalize_policy_paragraph(line) for line in lines[start:end] if line]"
        replacement = '[" ".join(line.split()) for line in lines[start:end] if line]'
    assert source_text.count(original) == 1
    mutant.write_text(source_text.replace(original, replacement), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-c", program, str(mutant_dir), kind],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == "collision"
