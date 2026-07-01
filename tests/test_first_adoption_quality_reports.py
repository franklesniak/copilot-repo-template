"""Exercise first-adoption quality-debt report helpers."""

from __future__ import annotations

import importlib
import io
import json
import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, cast

from tests._pytest_compat import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / ".template-sync" / "scripts" / "first_adoption_quality_reports.py"
SCRIPT_DIR = SCRIPT_PATH.parent

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

quality_reports = cast(Any, importlib.import_module("first_adoption_quality_reports"))


def _run_git(repo_root: Path, *args: str) -> str:
    """Run a Git command in a fixture repository and return stdout."""
    result = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def _write_text(repo_root: Path, relative_path: str, text: str = "content\n") -> None:
    """Write a UTF-8 fixture file."""
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_bytes(repo_root: Path, relative_path: str, data: bytes) -> None:
    """Write a binary fixture file."""
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _init_repo(repo_root: Path) -> None:
    """Initialize a fixture Git repository."""
    _run_git(repo_root, "init")
    _run_git(repo_root, "config", "user.email", "test@example.invalid")
    _run_git(repo_root, "config", "user.name", "Test User")


def test_quality_file_discovery_supports_tracked_only_and_ignored_controls(
    tmp_path: Path,
) -> None:
    """Report discovery defaults to tracked plus untracked non-ignored files."""
    _init_repo(tmp_path)
    _write_text(tmp_path, ".gitignore", "ignored.txt\n")
    _write_text(tmp_path, "tracked.txt")
    _write_text(tmp_path, "untracked.txt")
    _write_text(tmp_path, "ignored.txt")
    _run_git(tmp_path, "add", ".gitignore", "tracked.txt")

    default_collection = quality_reports.collect_git_files(tmp_path)
    tracked_collection = quality_reports.collect_git_files(tmp_path, tracked_only=True)
    ignored_collection = quality_reports.collect_git_files(tmp_path, include_ignored=True)

    assert default_collection.files == (".gitignore", "tracked.txt", "untracked.txt")
    assert tracked_collection.files == (".gitignore", "tracked.txt")
    assert ignored_collection.files == (
        ".gitignore",
        "ignored.txt",
        "tracked.txt",
        "untracked.txt",
    )


def test_line_ending_report_inventories_endings_and_normalization_risk(
    tmp_path: Path,
) -> None:
    """Line-ending reports detect CRLF/LF/mixed files and LF-normalization risk."""
    _init_repo(tmp_path)
    _write_bytes(tmp_path, ".gitattributes", b"*.md text eol=lf\n")
    _write_bytes(tmp_path, "tracked-crlf.md", b"one\r\ntwo\r\n")
    _write_bytes(tmp_path, "untracked-lf.md", b"one\ntwo\n")
    _write_bytes(tmp_path, "mixed.md", b"one\r\ntwo\n")
    _run_git(tmp_path, "add", ".gitattributes", "tracked-crlf.md")

    report = quality_reports.build_line_ending_report(tmp_path)

    assert report.counts["crlf"] == 1
    assert report.counts["lf"] == 2
    assert report.counts["mixed"] == 1
    assert report.normalization_risk_paths == ("mixed.md", "tracked-crlf.md")


def test_path_reference_report_catches_case_mismatch(tmp_path: Path) -> None:
    """Path-reference reports catch mismatches hidden on case-insensitive file systems."""
    _init_repo(tmp_path)
    _write_text(tmp_path, "CSV/data.csv")
    _write_text(tmp_path, "README.md", "See [data](Csv/data.csv).\n")

    report = quality_reports.build_path_reference_report(tmp_path)

    assert len(report.findings) == 1
    finding = report.findings[0]
    assert finding.rule_id == quality_reports.PATH_REFERENCE_CASE_MISMATCH_RULE
    assert finding.literal == "Csv/data.csv"
    assert finding.matched_path == "CSV/data.csv"


def test_path_reference_report_scans_only_documented_surfaces(tmp_path: Path) -> None:
    """Files outside the documented surface set are not scanned."""
    _init_repo(tmp_path)
    _write_text(tmp_path, "CSV/data.csv")
    _write_text(tmp_path, "notes.txt", "See Csv/data.csv.\n")

    report = quality_reports.build_path_reference_report(tmp_path)

    assert report.scanned_paths == ()
    assert report.findings == ()


def test_path_reference_suppression_can_match_rule_path_glob_and_literal_pattern(
    tmp_path: Path,
) -> None:
    """Suppressions can target a rule, source-path glob, and literal regex."""
    _init_repo(tmp_path)
    _write_text(tmp_path, "CSV/data.csv")
    _write_text(tmp_path, "README.md", "See [data](Csv/data.csv).\n")
    _write_text(
        tmp_path,
        ".template-sync/first-adoption/quality-suppressions.json",
        json.dumps(
            {
                "path-reference": {
                    "suppressions": [
                        {
                            "ruleId": "path-reference.case-mismatch",
                            "pathGlob": "*.md",
                            "literalPattern": "^Csv/",
                            "reason": "Fixture intentionally exercises suppression matching.",
                        }
                    ]
                }
            },
            indent=2,
        )
        + "\n",
    )

    report = quality_reports.build_path_reference_report(tmp_path)

    assert report.findings == ()
    assert report.suppressed_count == 1


def test_quality_suppressions_tolerate_leading_utf8_bom(tmp_path: Path) -> None:
    """Downstream-authored suppression files load even with a leading UTF-8 BOM."""
    _init_repo(tmp_path)
    _write_text(tmp_path, "CSV/data.csv")
    _write_text(tmp_path, "README.md", "See [data](Csv/data.csv).\n")
    suppression_document = json.dumps(
        {
            "path-reference": {
                "suppressions": [
                    {
                        "ruleId": "path-reference.case-mismatch",
                        "pathGlob": "*.md",
                        "literalPattern": "^Csv/",
                        "reason": "Fixture exercises BOM-tolerant suppression loading.",
                    }
                ]
            }
        },
        indent=2,
    )
    _write_bytes(
        tmp_path,
        ".template-sync/first-adoption/quality-suppressions.json",
        b"\xef\xbb\xbf" + (suppression_document + "\n").encode("utf-8"),
    )

    report = quality_reports.build_path_reference_report(tmp_path)

    assert report.findings == ()
    assert report.suppressed_count == 1


def test_path_reference_suppression_rejects_unknown_rule_identifier(tmp_path: Path) -> None:
    """Malformed suppression files fail with actionable errors."""
    _init_repo(tmp_path)
    _write_text(
        tmp_path,
        ".template-sync/first-adoption/quality-suppressions.json",
        json.dumps(
            {
                "path-reference": {
                    "suppressions": [
                        {
                            "ruleId": "path-reference.not-real",
                            "reason": "Unknown rule must fail.",
                        }
                    ]
                }
            }
        )
        + "\n",
    )

    with pytest.raises(quality_reports.FirstAdoptionQualityError) as excinfo:
        quality_reports.load_quality_suppressions(
            tmp_path,
            ".template-sync/first-adoption/quality-suppressions.json",
        )

    assert "unknown ruleId" in str(excinfo.value)


def test_quality_suppressions_require_path_reference_section(tmp_path: Path) -> None:
    """Suppression files follow the same required sections as their schema."""
    _init_repo(tmp_path)
    _write_text(
        tmp_path,
        ".template-sync/first-adoption/quality-suppressions.json",
        "{}\n",
    )

    with pytest.raises(quality_reports.FirstAdoptionQualityError) as excinfo:
        quality_reports.load_quality_suppressions(
            tmp_path,
            ".template-sync/first-adoption/quality-suppressions.json",
        )

    assert "path-reference" in str(excinfo.value)


def test_path_reference_suppression_requires_a_selector(tmp_path: Path) -> None:
    """Suppressions cannot accidentally match every path-reference finding."""
    _init_repo(tmp_path)
    _write_text(
        tmp_path,
        ".template-sync/first-adoption/quality-suppressions.json",
        json.dumps(
            {
                "path-reference": {
                    "suppressions": [
                        {
                            "reason": "Reason-only suppressions are too broad.",
                        }
                    ]
                }
            }
        )
        + "\n",
    )

    with pytest.raises(quality_reports.FirstAdoptionQualityError) as excinfo:
        quality_reports.load_quality_suppressions(
            tmp_path,
            ".template-sync/first-adoption/quality-suppressions.json",
        )

    assert "at least one selector" in str(excinfo.value)


def test_markdownlint_report_reports_missing_npm_without_silent_skip(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    """Missing optional Markdown tooling produces an unavailable state."""
    _write_text(tmp_path, "package.json", '{"scripts":{"lint:md":"markdownlint-cli2 ."}}\n')

    def missing_executable(_name: str) -> None:
        return None

    monkeypatch.setattr(quality_reports.shutil, "which", missing_executable)

    report = quality_reports.build_markdownlint_report(tmp_path)

    assert report.available is False
    assert "npm was not found" in report.message


def test_markdownlint_output_parser_records_rule_and_file_counts() -> None:
    """Markdownlint text output is parsed into reportable findings."""
    output = "\n".join(
        [
            "README.md:10:81 MD013/line-length Line length [Expected: 80]",
            "docs/guide.md:3 MD032/blanks-around-lists Lists should be surrounded by blank lines",
            "",
        ]
    )

    findings = quality_reports.parse_markdownlint_findings(output)

    assert [finding.rule for finding in findings] == [
        "MD013/line-length",
        "MD032/blanks-around-lists",
    ]
    assert [finding.path for finding in findings] == ["README.md", "docs/guide.md"]


def test_markdownlint_fixer_reports_changed_files(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    """Markdown fixer mode reports files changed after the fixer command."""
    _init_repo(tmp_path)
    _write_text(tmp_path, "package.json", '{"scripts":{"lint:md":"markdownlint-cli2 ."}}\n')
    _write_text(tmp_path, "README.md", "# Title\n")
    _run_git(tmp_path, "add", "package.json", "README.md")
    _run_git(tmp_path, "commit", "-m", "initial")
    monkeypatch.setattr(quality_reports, "npm_executable", lambda: "npm")

    def fake_runner(
        command: Sequence[str],
        repo_root: Path,
        *,
        env: Mapping[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        del env
        (repo_root / "README.md").write_text("# Title\n\nBody\n", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    report = quality_reports.build_markdownlint_report(
        tmp_path,
        fix=True,
        runner=fake_runner,
    )

    assert report.available is True
    assert report.changed_files == ("README.md",)


def test_decode_git_nul_paths_preserves_crlf_inside_record() -> None:
    """Raw Git path decoding preserves valid CR/LF bytes inside path records."""
    output = "src/line\r\nbreak.ps1\0".encode("utf-8")

    paths = quality_reports.decode_git_nul_paths(output)

    assert paths == ("src/line\r\nbreak.ps1",)


def test_decode_git_nul_paths_rejects_undecodable_record() -> None:
    """Undecodable Git path bytes fail with a manual-review diagnostic."""
    with pytest.raises(quality_reports.FirstAdoptionQualityError, match="not valid UTF-8"):
        quality_reports.decode_git_nul_paths(b"src/bad-\xff.ps1\0")


def test_candidate_summary_lines_escape_human_facing_crlf() -> None:
    """Candidate summaries preserve structure but render paths on one line."""
    lines = quality_reports.candidate_summary_lines(
        {
            "Selected": [],
            "PolicyExcluded": [
                {
                    "CandidateFullName": "/repo/node_modules/.bin/tool.ps1",
                    "RepositoryRelativePath": "node_modules/.bin/tool.ps1",
                    "OutcomeCategory": "policy-excluded",
                    "ReasonCode": "NodeModulesSegment",
                }
            ],
            "Unsafe": [
                {
                    "CandidateFullName": "/repo/src/line\r\nbreak.ps1",
                    "RepositoryRelativePath": "src/line\r\nbreak.ps1",
                    "OutcomeCategory": "unsafe",
                    "ReasonCode": "MissingTarget",
                }
            ],
            "SummaryCounts": {
                "Selected": 0,
                "PolicyExcluded": 1,
                "Unsafe": 1,
            },
        }
    )

    assert "node_modules/.bin/tool.ps1" in "\n".join(lines)
    assert "src/line\\r\\nbreak.ps1" in "\n".join(lines)
    assert all("\r" not in line and "\n" not in line for line in lines)


def test_powershell_report_parses_injected_runner_output(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    """The PowerShell report sends stdin candidates and parses composite JSON."""
    _init_repo(tmp_path)
    _write_text(tmp_path, "src/café.ps1", "Write-Output 'sample'\n")
    _write_text(tmp_path, ".github/linting/PSScriptAnalyzerSettings.psd1", "@{}\n")
    _write_text(
        tmp_path,
        "src/tools/Resolve-PSScriptAnalyzerCandidate.ps1",
        "function Resolve-PSScriptAnalyzerCandidate {}\n",
    )
    _write_text(
        tmp_path,
        "src/tools/Resolve-PSScriptAnalyzerGate.ps1",
        "function Resolve-PSScriptAnalyzerGate {}\n",
    )
    monkeypatch.setattr(quality_reports, "powershell_executable", lambda: "pwsh")

    captured_input = ""

    def fake_runner(
        command: Sequence[str],
        repo_root: Path,
        *,
        env: Mapping[str, str] | None = None,
        input: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        nonlocal captured_input
        assert env is None
        captured_input = input or ""
        payload = json.dumps(
            {
                "Gate": {
                    "Status": "ok",
                    "SummaryLines": [
                        "PSScriptAnalyzer gate mode: first-adoption.",
                        "Result: pass.",
                    ],
                    "IssueReadyMarkdown": [
                        "## PSScriptAnalyzer First-Adoption Debt Cleanup",
                        "",
                    ],
                },
                "Candidates": {
                    "Selected": [
                        {
                            "CandidateFullName": str(repo_root / "src" / "café.ps1"),
                            "RepositoryRelativePath": "src/café.ps1",
                            "EscapedAnalyzerPath": str(repo_root / "src" / "café.ps1"),
                            "OutcomeCategory": "selected",
                            "ReasonCode": "Selected",
                        }
                    ],
                    "PolicyExcluded": [],
                    "Unsafe": [],
                    "SummaryCounts": {
                        "Selected": 1,
                        "PolicyExcluded": 0,
                        "Unsafe": 0,
                    },
                },
            }
        )
        return subprocess.CompletedProcess(command, 0, stdout=payload, stderr="")

    report = quality_reports.build_powershell_report(tmp_path, runner=fake_runner)

    assert report.available is True
    assert report.summary_lines == (
        "PSScriptAnalyzer gate mode: first-adoption.",
        "Result: pass.",
    )
    assert report.issue_ready_markdown == (
        "## PSScriptAnalyzer First-Adoption Debt Cleanup",
        "",
    )
    assert report.candidate_summary_lines == (
        "PSScriptAnalyzer candidates: 1 selected; 0 policy-excluded; 0 unsafe.",
    )
    assert "café" in captured_input
    assert "\\u00e9" not in captured_input
    assert {"RepositoryRelativePath": "src/café.ps1"} in json.loads(captured_input)


def test_powershell_report_unsafe_candidates_use_reserved_exit_code(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    """Unsafe analyzer candidates propagate the reserved report exit code."""
    report = quality_reports.PowerShellAnalyzerReport(
        available=True,
        message="Unsafe candidate path(s) were found.",
        candidate_summary_lines=(
            "Unsafe candidate: src/link.ps1; reason: TargetOutsideRepository",
        ),
        unsafe_candidate_count=1,
        summary_lines=(),
        issue_ready_markdown=(),
    )
    monkeypatch.setattr(quality_reports, "build_powershell_report", lambda *args, **kwargs: report)
    stdout = io.StringIO()
    args = quality_reports.parse_args(
        [
            "--repo-root",
            str(tmp_path),
            "powershell",
        ]
    )

    result = quality_reports.run_report(args, stdout=stdout)

    assert result == quality_reports.UNSAFE_CANDIDATE_EXIT_CODE
    assert "Unsafe candidate" in stdout.getvalue()


def test_host_setup_report_distinguishes_azure_service_tasks(tmp_path: Path) -> None:
    """Azure host setup reporting separates service tasks from file materialization."""
    _write_text(
        tmp_path,
        ".template-sync/marker.yml",
        (
            "template_sync:\n"
            "  source_repo: https://github.com/franklesniak/copilot-repo-template.git\n"
            "  included_modules:\n"
            "    - baseline\n"
            "    - azure-devops-platform\n"
            "  host_provider: azure-devops-services\n"
            "  azure_boards_policy: work-items\n"
            "  azure_repos_pr_template_policy: materialize\n"
            "  azure_branch_policy_reviewer_guidance: manual-follow-up\n"
            "  azure_security_intake_policy: manual-follow-up\n"
            "  azure_security_product_enablement: github-advanced-security\n"
            "  azure_dependency_update_policy: manual-follow-up\n"
        ),
    )
    stdout = io.StringIO()

    report = quality_reports.build_host_setup_report(tmp_path)
    quality_reports.print_host_setup_report(report, stdout=stdout)

    output = stdout.getvalue()
    assert report.azure_modules_retained is True
    assert "Azure DevOps Services service setup tasks" in output
    assert "Azure Boards intake policy: work-items" in output
    assert "Azure Repos pull request template policy: materialize" in output
    assert "Branch policy reviewer guidance: manual-follow-up" in output
    assert "not local file materialization failures" in output
    assert "not local file materialization failures or GitHub issue-template findings" in output


def test_load_marker_rejects_symlinked_marker(tmp_path: Path) -> None:
    """A symlinked marker (even a broken one) is rejected, not treated as absent."""
    marker_path = tmp_path / ".template-sync" / "marker.yml"
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        marker_path.symlink_to(tmp_path / "nonexistent-target.yml")
    except (OSError, NotImplementedError):
        pytest.skip("Filesystem does not support symlink creation")

    with pytest.raises(quality_reports.FirstAdoptionQualityError, match="Expected a regular file"):
        quality_reports.load_marker_template_sync(tmp_path)


def test_path_reference_cli_can_fail_on_findings(tmp_path: Path) -> None:
    """The CLI offers an explicit non-zero path-reference gate when selected."""
    _init_repo(tmp_path)
    _write_text(tmp_path, "CSV/data.csv")
    _write_text(tmp_path, "README.md", "See [data](Csv/data.csv).\n")
    stdout = io.StringIO()
    args = quality_reports.parse_args(
        [
            "--repo-root",
            str(tmp_path),
            "path-references",
            "--fail-on-findings",
        ]
    )

    result = quality_reports.run_report(args, stdout=stdout)

    assert result == 1
    assert "path-reference.case-mismatch" in stdout.getvalue()
