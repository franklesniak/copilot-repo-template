"""Exercise excluded-module cleanup reporting."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / ".template-sync" / "scripts" / "report_excluded_module_references.py"
MARKER_SCHEMA_PATH = REPO_ROOT / "schemas" / "template-sync-marker.schema.json"
MANIFEST_SCHEMA_PATH = REPO_ROOT / "schemas" / "template-sync-manifest.schema.json"
SOURCE_REPO = "https://github.com/franklesniak/copilot-repo-template.git"
FULL_SHA = "0123456789abcdef0123456789abcdef01234567"
INCLUDED_MODULES = [
    "baseline",
    "agent-instructions",
    "github-actions",
    "github-platform",
    "github-templates",
    "markdown",
    "template-sync-support",
    "yaml",
]
MODULE_DEFINITIONS = {
    "baseline": "Baseline files.",
    "agent-instructions": "Agent instruction files.",
    "github-platform": "GitHub platform files.",
    "github-actions": "GitHub Actions workflows.",
    "github-templates": "GitHub collaboration surfaces.",
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
    """Write a UTF-8 text file below a fixture repository root."""
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> None:
    """Write a YAML file below a fixture repository root."""
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _copy_schemas(repo_root: Path) -> None:
    """Copy real template-sync schemas into a fixture repository."""
    schemas_dir = repo_root / "schemas"
    schemas_dir.mkdir(parents=True, exist_ok=True)
    for source_path in (MARKER_SCHEMA_PATH, MANIFEST_SCHEMA_PATH):
        shutil.copyfile(source_path, schemas_dir / source_path.name)


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


def _run_report(repo_root: Path, *extra_args: str) -> subprocess.CompletedProcess[str]:
    """Run the excluded-module cleanup reporter."""
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


def _manifest() -> dict[str, Any]:
    """Build a schema-valid manifest fixture with cross-module cleanup surfaces."""
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
                    "pattern": ".template-sync/scripts/**",
                    "requires_all": ["template-sync-support"],
                },
                {"pattern": "README.md", "requires_all": ["baseline"]},
                {
                    "pattern": "AGENTS.md",
                    "requires_all": ["agent-instructions"],
                    "notes": "Contains Markdown-safe *-reference-only inline blocks.",
                },
                {"pattern": ".pre-commit-config.yaml", "requires_all": ["baseline"]},
                {"pattern": ".github/dependabot.yml", "requires_all": ["github-platform"]},
                {"pattern": ".github/ISSUE_TEMPLATE/**", "requires_all": ["github-templates"]},
                {
                    "pattern": ".github/workflows/data-ci.yml",
                    "requires_all": ["github-actions"],
                    "requires_any": ["yaml", "schema", "template-sync-support"],
                },
                {"pattern": "package.json", "requires_all": ["markdown"]},
                {"pattern": "templates/json/**", "requires_all": ["json"]},
                {"pattern": "schemas/**", "requires_all": ["schema"]},
                {"pattern": "pyproject.toml", "requires_all": ["python"]},
                {"pattern": "src/copilot_repo_template/**", "requires_all": ["python"]},
                {"pattern": ".github/workflows/python-ci.yml", "requires_all": ["python"]},
                {"pattern": "modules/**", "requires_all": ["terraform"]},
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


def _marker(
    *,
    local_overrides: list[dict[str, str]] | None = None,
    deferred_candidates: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Build a schema-valid marker fixture."""
    template_sync: dict[str, Any] = {
        "source_repo": SOURCE_REPO,
        "last_reviewed_template_commit": FULL_SHA,
        "included_modules": INCLUDED_MODULES,
    }
    if local_overrides is not None:
        template_sync["local_overrides"] = local_overrides
    if deferred_candidates is not None:
        template_sync["deferred_protected_candidates"] = deferred_candidates
    return {"template_sync": template_sync}


def _write_common_repo(
    repo_root: Path,
    *,
    marker: dict[str, Any] | None = None,
    include_marker: bool = True,
    include_reference_content: bool = True,
) -> None:
    """Write a partial-adoption fixture repository."""
    _run_git(repo_root, "init")
    _copy_schemas(repo_root)
    _write_yaml(repo_root, ".template-sync/manifest.yml", _manifest())
    if include_marker:
        _write_yaml(repo_root, ".template-sync/marker.yml", marker or _marker())
    _write_text(repo_root, ".template-sync/scripts/report_excluded_module_references.py")
    _write_text(
        repo_root,
        ".pre-commit-config.yaml",
        (
            "repos:\n"
            "  - repo: https://github.com/pre-commit/pre-commit-hooks\n"
            "    rev: v6.0.0\n"
            "    hooks:\n"
            "      - id: check-json\n"
            "# template-sync: begin python-only\n"
            "  - repo: https://github.com/psf/black\n"
            "    rev: 26.5.1\n"
            "    hooks:\n"
            "      - id: black\n"
            "  - repo: https://github.com/astral-sh/ruff-pre-commit\n"
            "    rev: v0.15.15\n"
            "    hooks:\n"
            "      - id: ruff-check\n"
            "# template-sync: end python-only\n"
            "# template-sync: begin terraform-only\n"
            "  - repo: local\n"
            "    hooks:\n"
            "      - id: terraform-fmt\n"
            "        entry: python .github/scripts/terraform_hooks.py fmt\n"
            "# template-sync: end terraform-only\n"
        ),
    )
    _write_text(
        repo_root,
        ".github/workflows/data-ci.yml",
        (
            "name: Data file linting\n"
            "on: pull_request\n"
            "permissions: {}\n"
            "jobs:\n"
            "  data-file-linting:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - name: Run check-json\n"
            "        run: pre-commit run check-json --all-files\n"
            "      # template-sync: begin schema-only\n"
            "      - name: Run validate-example-config-schema\n"
            "        run: pre-commit run validate-example-config-schema --all-files\n"
            "      # template-sync: end schema-only\n"
        ),
    )
    _write_text(
        repo_root,
        ".github/dependabot.yml",
        (
            "version: 2\n"
            "updates:\n"
            '  - package-ecosystem: "pip"\n'
            '    directory: "/"\n'
            "    schedule:\n"
            '      interval: "weekly"\n'
            '  - package-ecosystem: "github-actions"\n'
            '    directory: "/"\n'
            "    schedule:\n"
            '      interval: "weekly"\n'
            '  - package-ecosystem: "pre-commit"\n'
            '    directory: "/"\n'
            "    schedule:\n"
            '      interval: "weekly"\n'
        ),
    )
    _write_text(
        repo_root,
        "AGENTS.md",
        (
            "# Agent Instructions\n\n"
            "<!-- template-sync: begin python-reference-only -->\n"
            "Python validation command: `pytest tests/ -v`.\n"
            "<!-- template-sync: end python-reference-only -->\n"
        ),
    )
    _write_text(
        repo_root,
        ".github/ISSUE_TEMPLATE/bug_report.yml",
        (
            "name: Bug Report\n"
            "description: Report a bug\n"
            "body:\n"
            "  - type: markdown\n"
            "    attributes:\n"
            "      value: |\n"
            "        See [schema](../../schemas/example-config.schema.json).\n"
        ),
    )
    _write_text(repo_root, "templates/json/example.json", "{}\n")
    if include_reference_content:
        _write_text(
            repo_root,
            "README.md",
            (
                "# Downstream\n\n"
                "See [JSON starter](templates/json/example.json).\n\n"
                "See [upstream JSON]"
                "(https://github.com/franklesniak/copilot-repo-template/blob/HEAD/"
                "templates/json/example.json).\n\n"
                "<!-- template-sync: begin json-reference-only -->\n"
                "JSON is mentioned as reference-only documentation.\n"
                "<!-- template-sync: end json-reference-only -->\n"
            ),
        )
    else:
        _write_text(repo_root, "README.md", "# Downstream\n")


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


def _finding_lines(output: str) -> set[str]:
    """Return rendered finding lines without their bullet marker."""
    return _section_entries(output, "Findings")


def test_marker_excluding_optional_modules_reports_cleanup_scope(tmp_path: Path) -> None:
    """A marker-derived report explains retained references to excluded modules."""
    _write_common_repo(tmp_path)

    result = _run_report(tmp_path)

    assert result.returncode == 0, result.stderr
    assert "State source: marker (.template-sync/marker.yml)" in result.stdout

    retained_modules = _section_entries(result.stdout, "Retained modules")
    excluded_modules = _section_entries(result.stdout, "Excluded modules")
    findings = _finding_lines(result.stdout)

    assert "template-sync-support" in retained_modules
    assert "python" in excluded_modules
    assert "terraform" in excluded_modules
    assert "json" in excluded_modules
    assert "schema" in excluded_modules
    assert "Excluded module scopes:" in result.stdout
    assert "python | manifest-owned paths:" in result.stdout
    assert "workflow files/jobs: .github/workflows/python-ci.yml" in result.stdout

    # Inline-block markers live on their own lines, so the scope scan must match
    # per line; a whole-file regex match would miss every retained cross-module
    # reference and inline-block family below.
    excluded_scopes = _section_entries(result.stdout, "Excluded module scopes")
    python_scope = next(
        (line for line in excluded_scopes if line.startswith("python | ")),
        "",
    )
    assert (
        "retained cross-module paths: .pre-commit-config.yaml; AGENTS.md" in python_scope
    ), python_scope
    assert "inline block families: python-only; python-reference-only" in python_scope, python_scope

    assert any(
        line.startswith(
            "manifest-owned-path | required_cleanup | json | " "templates/json/example.json |"
        )
        for line in findings
    )
    assert any(
        line.startswith(
            "inline-block.stale | required_cleanup | python | " ".pre-commit-config.yaml:6 |"
        )
        for line in findings
    )
    assert any(
        "pre-commit-hook-group.stale | required_cleanup | python | "
        ".pre-commit-config.yaml:6 | Hooks: black, ruff-check." in line
        for line in findings
    )
    assert any(
        "workflow-validation-command.stale | required_cleanup | schema | "
        ".github/workflows/data-ci.yml:10 | "
        "Command: pre-commit run validate-example-config-schema --all-files." in line
        for line in findings
    )
    assert any(
        line.startswith(
            "dependabot-ecosystem.stale | required_cleanup | python | "
            ".github/dependabot.yml | pip scans"
        )
        for line in findings
    )
    assert any(
        line.startswith("markdown-link.excluded-target | required_cleanup | json | README.md:3 |")
        for line in findings
    )
    assert any(
        line.startswith(
            "markdown-link.excluded-target | required_cleanup | schema | "
            ".github/ISSUE_TEMPLATE/bug_report.yml:7 |"
        )
        for line in findings
    )
    assert any(
        line.startswith(
            "markdown-link.upstream-reference | likely_false_positive_documented_reference | "
            "json | README.md:5 |"
        )
        for line in findings
    )
    assert any(
        line.startswith(
            "inline-block.reference-only | optional_reference_only_cleanup | "
            "json | README.md:7 |"
        )
        for line in findings
    )
    assert any(
        line.startswith(
            "inline-block.reference-only | protected_file_authorization_needed | "
            "python | AGENTS.md:3 |"
        )
        for line in findings
    )
    assert any(
        line.startswith(
            "manifest.reference-only-note | documented_reference_only_retention | "
            "python | AGENTS.md:3 |"
        )
        for line in findings
    )
    assert any(
        "validation-command.documented-reference | "
        "likely_false_positive_documented_reference | json | "
        ".pre-commit-config.yaml | check-json remains" in line
        for line in findings
    )


def test_explicit_included_modules_without_marker_matches_marker_findings(
    tmp_path: Path,
) -> None:
    """Pre-marker explicit module input produces the same deterministic findings."""
    marker_repo = tmp_path / "marker"
    explicit_repo = tmp_path / "explicit"
    marker_repo.mkdir()
    explicit_repo.mkdir()
    _write_common_repo(marker_repo)
    _write_common_repo(explicit_repo, include_marker=False)

    marker_result = _run_report(marker_repo)
    explicit_result = _run_report(
        explicit_repo,
        *(argument for module in INCLUDED_MODULES for argument in ("--included-module", module)),
    )

    assert marker_result.returncode == 0, marker_result.stderr
    assert explicit_result.returncode == 0, explicit_result.stderr
    assert "State source: explicit --included-module input" in explicit_result.stdout
    assert _finding_lines(explicit_result.stdout) == _finding_lines(marker_result.stdout)


def test_ambiguous_marker_and_explicit_included_modules_fail(tmp_path: Path) -> None:
    """Marker-derived and explicit module state cannot both be supplied."""
    _write_common_repo(tmp_path)

    result = _run_report(tmp_path, "--included-module", "baseline")

    assert result.returncode == 1
    assert "Ambiguous included-module state" in result.stderr


def test_local_overrides_and_deferred_decisions_are_report_categories(
    tmp_path: Path,
) -> None:
    """Marker waivers and deferred protected decisions are reported separately."""
    _write_common_repo(
        tmp_path,
        marker=_marker(
            local_overrides=[
                {
                    "path": "templates/json/",
                    "reason": "Downstream keeps JSON examples as local documentation.",
                    "default_decision": "SKIP",
                }
            ],
            deferred_candidates=[
                {
                    "path": "AGENTS.md",
                    "source_commit": FULL_SHA,
                    "reason": "Owner review pending for protected reference-only guidance.",
                }
            ],
        ),
        include_reference_content=False,
    )

    result = _run_report(tmp_path)

    assert result.returncode == 0, result.stderr
    findings = _finding_lines(result.stdout)
    assert any(
        line.startswith(
            "marker.local-override | local_override_recorded | json | "
            "templates/json/ | SKIP; reason:"
        )
        for line in findings
    )
    assert any(
        line.startswith(
            "marker.deferred-protected-decision | deferred_decision_recorded | "
            "unknown | AGENTS.md |"
        )
        for line in findings
    )
    assert not any(
        line.startswith(
            "manifest-owned-path | required_cleanup | json | " "templates/json/example.json |"
        )
        for line in findings
    )


def test_invalid_explicit_module_is_runtime_failure(tmp_path: Path) -> None:
    """Invalid input exits nonzero because no deterministic module source exists."""
    _write_common_repo(tmp_path, include_marker=False)

    result = _run_report(tmp_path, "--included-module", "not-a-module")

    assert result.returncode == 1
    assert "not defined by the manifest" in result.stderr


def test_dependabot_local_override_keeps_ecosystem_from_stale(tmp_path: Path) -> None:
    """A locally overridden scanned file keeps its Dependabot ecosystem non-stale."""
    _write_common_repo(
        tmp_path,
        marker=_marker(
            local_overrides=[
                {
                    "path": "pyproject.toml",
                    "reason": "Downstream keeps Python packaging metadata as a local file.",
                    "default_decision": "SKIP",
                }
            ],
        ),
    )
    _write_text(tmp_path, "pyproject.toml", '[project]\nname = "downstream"\n')

    result = _run_report(tmp_path)

    assert result.returncode == 0, result.stderr
    findings = _finding_lines(result.stdout)
    # The pip ecosystem maps to the excluded ``python`` module, but the retained
    # pyproject.toml is an intentional local override, so the ecosystem entry is
    # still justified and must not be reported as stale.
    assert not any(
        line.startswith("dependabot-ecosystem.stale | required_cleanup | python |")
        for line in findings
    )


def test_dependabot_github_actions_directory_surface_is_detected(tmp_path: Path) -> None:
    """A retained workflow keeps the github-actions ecosystem from being stale."""
    marker = {
        "template_sync": {
            "source_repo": SOURCE_REPO,
            "last_reviewed_template_commit": FULL_SHA,
            "included_modules": [
                "baseline",
                "agent-instructions",
                "github-platform",
                "github-templates",
                "markdown",
                "template-sync-support",
                "yaml",
            ],
            "local_overrides": [
                {
                    "path": ".github/workflows/data-ci.yml",
                    "reason": "Downstream keeps the data-file CI workflow.",
                    "default_decision": "SKIP",
                }
            ],
        }
    }
    _write_common_repo(tmp_path, marker=marker)

    result = _run_report(tmp_path)

    assert result.returncode == 0, result.stderr
    findings = _finding_lines(result.stdout)
    # github-actions is excluded, but a workflow under the ".github/workflows/"
    # directory surface is retained (here via override), so the ecosystem entry
    # is still justified. The scanned surface must be matched as a directory
    # prefix, not as a literal file path that is never present.
    assert not any(
        line.startswith("dependabot-ecosystem.stale | required_cleanup | github-actions |")
        for line in findings
    )


def test_yaml_embedded_fenced_links_are_skipped(tmp_path: Path) -> None:
    """Links inside fenced code blocks in YAML-embedded Markdown are ignored."""
    _write_common_repo(tmp_path)
    _write_text(
        tmp_path,
        ".github/ISSUE_TEMPLATE/fenced_example.yml",
        (
            "name: Fenced Example\n"
            "description: Example with fenced Markdown\n"
            "body:\n"
            "  - type: markdown\n"
            "    attributes:\n"
            "      value: |\n"
            "        Outside fence: [schema](../../schemas/example-config.schema.json).\n"
            "        ```\n"
            "        Inside fence: [json](../../templates/json/example.json).\n"
            "        ```\n"
        ),
    )

    result = _run_report(tmp_path)

    assert result.returncode == 0, result.stderr
    findings = _finding_lines(result.stdout)
    # The link outside the (indented) fenced block is still reported.
    assert any(
        line.startswith(
            "markdown-link.excluded-target | required_cleanup | schema | "
            ".github/ISSUE_TEMPLATE/fenced_example.yml:7 |"
        )
        for line in findings
    )
    # The link inside the fenced block must be ignored even though the file is
    # YAML and the fence is indented inside a ``value: |`` block.
    assert not any(".github/ISSUE_TEMPLATE/fenced_example.yml:9" in line for line in findings)
