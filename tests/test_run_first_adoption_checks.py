"""Exercise the first-adoption working-tree validation runner."""

from __future__ import annotations

import io
import shutil
import subprocess
import sys
from collections.abc import Callable, Sequence
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / ".template-sync" / "scripts" / "run_first_adoption_checks.py"
SCRIPT_DIR = SCRIPT_PATH.parent

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_first_adoption_checks as first_adoption  # noqa: E402


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


def _write_text(repo_root: Path, relative_path: str, text: str = "placeholder\n") -> None:
    """Write a UTF-8 fixture file."""
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_marker(repo_root: Path, text: str) -> None:
    """Write a downstream marker fixture."""
    _write_text(repo_root, ".template-sync/marker.yml", text)


def _write_pytest_profile_root(tmp_path: Path) -> Path:
    """Create a temporary pytest root with the committed pytest configuration."""
    pytest_root = tmp_path / "pytest-root"
    pytest_root.mkdir()
    shutil.copyfile(REPO_ROOT / "pyproject.toml", pytest_root / "pyproject.toml")
    return pytest_root


def _recording_runner(records: list[tuple[str, ...]]) -> Callable[[Sequence[str], Path], int]:
    """Return a fake command runner that records commands."""

    def run(command: Sequence[str], _repo_root: Path) -> int:
        records.append(tuple(command))
        return 0

    return run


def _queued_status_reader(*snapshots: tuple[str, ...]) -> Callable[[Path], tuple[str, ...]]:
    """Return a Git status reader that consumes a fixed sequence of snapshots."""
    remaining_snapshots = list(snapshots)

    def read_status(_repo_root: Path) -> tuple[str, ...]:
        assert remaining_snapshots, "No queued Git status snapshot remains."
        return remaining_snapshots.pop(0)

    return read_status


def _utc_time(second: int) -> datetime:
    """Return a deterministic UTC timestamp for timing assertions."""
    return datetime(2026, 6, 3, 12, 0, second, tzinfo=timezone.utc)


def _queued_time_source(*timestamps: datetime) -> Callable[[], datetime]:
    """Return a time source that consumes a fixed sequence of timestamps."""
    remaining_timestamps = list(timestamps)

    def now() -> datetime:
        assert remaining_timestamps, "No queued timestamp remains."
        return remaining_timestamps.pop(0)

    return now


def _incrementing_time_source() -> Callable[[], datetime]:
    """Return a deterministic time source that advances one second per read."""
    current_timestamp: list[datetime] = [_utc_time(0)]

    def now() -> datetime:
        timestamp = current_timestamp[0]
        current_timestamp[0] = timestamp + timedelta(seconds=1)
        return timestamp

    return now


def test_no_file_repository_exits_without_validation_commands(tmp_path: Path) -> None:
    """An empty Git repository exits cleanly with a useful no-file message."""
    _run_git(tmp_path, "init")
    commands: list[tuple[str, ...]] = []
    stdout = io.StringIO()

    result = first_adoption.run_first_adoption_checks(
        tmp_path,
        command_runner=_recording_runner(commands),
        stdout=stdout,
    )

    assert result == 0
    assert commands == []
    assert "Run mode: check" in stdout.getvalue()
    assert "No tracked or untracked non-ignored regular files found" in stdout.getvalue()
    assert "No first-adoption checks were available to run." in stdout.getvalue()
    assert "No Git status changes were detected" in stdout.getvalue()


def test_default_mode_is_explicit_check() -> None:
    """The CLI defaults to explicit check mode."""
    args = first_adoption.parse_args([])

    assert args.run_mode == first_adoption.CHECK_MODE


def test_fix_mode_is_explicit() -> None:
    """The CLI exposes an explicit fix mode for mutating hook/fixer runs."""
    args = first_adoption.parse_args(["--fix"])

    assert args.run_mode == first_adoption.FIX_MODE


def test_check_plan_assigns_stable_group_labels(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Planned validation commands carry stable group labels."""
    monkeypatch.setattr(
        first_adoption,
        "default_pre_commit_prefix",
        lambda: ("pre-commit", "run", "--files"),
    )
    monkeypatch.setattr(first_adoption, "default_npm_executable", lambda: "npm")
    _write_text(tmp_path, "README.md")
    _write_text(tmp_path, ".github/scripts/replace-template-placeholders.py")
    _write_marker(tmp_path, "template_sync:\n  included_modules:\n  - markdown\n")
    _write_text(tmp_path, ".template-sync/scripts/validate_marker.py")
    _write_text(
        tmp_path,
        "package.json",
        '{"scripts":{"lint:md":"markdownlint .","lint:md:nested":"markdownlint ."}}\n',
    )

    plan = first_adoption.build_check_plan(tmp_path, ("README.md",))

    assert [command.group_label for command in plan.commands] == [
        "pre-commit",
        "placeholder-scan",
        "marker-validation",
        "markdown-script",
        "markdown-script",
    ]
    assert plan.commands[0].command == ("pre-commit", "run", "--files", "README.md")
    assert plan.commands[-2].command == ("npm", "run", "lint:md")
    assert plan.commands[-1].command == ("npm", "run", "lint:md:nested")


def test_quality_reports_are_planned_before_fixers_when_helper_exists(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The first-adoption runner inventories quality debt before fix-mode commands."""
    monkeypatch.setattr(
        first_adoption,
        "default_pre_commit_prefix",
        lambda: ("pre-commit", "run", "--files"),
    )
    _write_text(tmp_path, ".template-sync/scripts/first_adoption_quality_reports.py")

    plan = first_adoption.build_check_plan(
        tmp_path,
        ("README.md",),
        run_mode=first_adoption.FIX_MODE,
    )

    assert [command.group_label for command in plan.commands[:5]] == [
        "quality-report",
        "quality-report",
        "quality-report",
        "markdown-fixer",
        "pre-commit",
    ]
    assert plan.commands[0].command[-1] == "line-endings"
    assert plan.commands[1].command[-1] == "path-references"
    assert plan.commands[2].command[-1] == "powershell"
    assert plan.commands[3].command[-2:] == ("markdown", "--fix")


def test_powershell_quality_report_is_skipped_when_marker_excludes_powershell(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Marker-derived module state suppresses stale PowerShell report commands."""
    monkeypatch.setattr(
        first_adoption,
        "default_pre_commit_prefix",
        lambda: ("pre-commit", "run", "--files"),
    )
    _write_text(tmp_path, ".template-sync/scripts/first_adoption_quality_reports.py")
    _write_text(tmp_path, ".template-sync/scripts/validate_marker.py")
    _write_text(
        tmp_path,
        ".template-sync/marker.yml",
        "template_sync:\n  included_modules:\n    - baseline\n    - template-sync-support\n",
    )

    plan = first_adoption.build_check_plan(
        tmp_path,
        ("README.md",),
        run_mode=first_adoption.FIX_MODE,
    )

    quality_modes = [
        command.command[-1]
        for command in plan.commands
        if command.group_label == first_adoption.QUALITY_REPORT_GROUP
    ]
    assert quality_modes == ["line-endings", "path-references"]
    assert all("powershell" not in command.command for command in plan.commands)


def test_azure_marker_plans_host_setup_quality_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Azure DevOps module retention schedules the host setup report."""
    monkeypatch.setattr(
        first_adoption,
        "default_pre_commit_prefix",
        lambda: ("pre-commit", "run", "--files"),
    )
    _write_text(tmp_path, ".template-sync/scripts/first_adoption_quality_reports.py")
    _write_text(tmp_path, ".template-sync/scripts/validate_marker.py")
    _write_text(
        tmp_path,
        ".template-sync/marker.yml",
        "template_sync:\n  included_modules:\n    - baseline\n    - azure-devops-platform\n",
    )

    plan = first_adoption.build_check_plan(
        tmp_path,
        ("README.md",),
        run_mode=first_adoption.FIX_MODE,
    )

    quality_modes = [
        command.command[-1]
        for command in plan.commands
        if command.group_label == first_adoption.QUALITY_REPORT_GROUP
    ]
    assert quality_modes == ["line-endings", "path-references", "host-setup"]


def test_marker_module_detection_ignores_sibling_string_lists(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sibling marker lists like issue_labels are not read as retained modules."""
    monkeypatch.setattr(
        first_adoption,
        "default_pre_commit_prefix",
        lambda: ("pre-commit", "run", "--files"),
    )
    _write_text(tmp_path, ".template-sync/scripts/first_adoption_quality_reports.py")
    _write_text(tmp_path, ".template-sync/scripts/validate_marker.py")
    # Block sequence items render at the key's own indentation under PyYAML's
    # default safe_dump style, and issue_labels can reuse module-like names.
    _write_text(
        tmp_path,
        ".template-sync/marker.yml",
        (
            "template_sync:\n"
            "  source_repo: https://github.com/franklesniak/copilot-repo-template\n"
            "  included_modules:\n"
            "  - baseline\n"
            "  - template-sync-support\n"
            "  issue_label_policy: custom\n"
            "  issue_labels:\n"
            "  - powershell\n"
            "  - markdown\n"
        ),
    )

    assert first_adoption.marker_included_modules(tmp_path) == frozenset(
        {"baseline", "template-sync-support"}
    )
    assert not first_adoption.marker_includes_markdown_module(tmp_path)

    plan = first_adoption.build_check_plan(
        tmp_path,
        ("README.md",),
        run_mode=first_adoption.FIX_MODE,
    )

    assert all("powershell" not in command.command for command in plan.commands)


def test_marker_module_detection_skips_comment_lines_inside_block(
    tmp_path: Path,
) -> None:
    """Full-line comments inside included_modules do not end the module scan."""
    # A hand-added comment at the block indentation must be skipped, not treated
    # as an end-of-block marker that drops the modules listed after it.
    _write_marker(
        tmp_path,
        (
            "template_sync:\n"
            "  included_modules:\n"
            "  - baseline\n"
            "  # downstream note kept after editing\n"
            "  - powershell\n"
            "  - template-sync-support\n"
            "  issue_labels:\n"
            "  - markdown\n"
        ),
    )

    assert first_adoption.marker_included_modules(tmp_path) == frozenset(
        {"baseline", "powershell", "template-sync-support"}
    )


def test_tracked_only_files_are_collected(tmp_path: Path) -> None:
    """Tracked files staged in the index are included in the pre-commit file list."""
    _run_git(tmp_path, "init")
    _write_text(tmp_path, "tracked.txt")
    _run_git(tmp_path, "add", "tracked.txt")

    collection = first_adoption.collect_present_regular_files(tmp_path)

    assert collection.files == ("tracked.txt",)
    assert collection.skipped_non_regular_paths == ()


def test_untracked_only_files_are_collected(tmp_path: Path) -> None:
    """Untracked non-ignored files are included before the first adoption commit."""
    _run_git(tmp_path, "init")
    _write_text(tmp_path, "untracked.txt")

    collection = first_adoption.collect_present_regular_files(tmp_path)

    assert collection.files == ("untracked.txt",)


def test_ignored_files_are_not_collected(tmp_path: Path) -> None:
    """Ignored files are excluded by the Git-visible working-tree query."""
    _run_git(tmp_path, "init")
    _write_text(tmp_path, ".gitignore", "ignored.txt\n")
    _write_text(tmp_path, "ignored.txt")

    collection = first_adoption.collect_present_regular_files(tmp_path)

    assert "ignored.txt" not in collection.files
    assert collection.files == (".gitignore",)


def test_plan_only_prints_collection_notes_and_plan_without_running(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Plan-only mode prints discovery and plan details without validation commands."""
    monkeypatch.setattr(
        first_adoption,
        "default_pre_commit_prefix",
        lambda: ("pre-commit", "run", "--files"),
    )
    _run_git(tmp_path, "init")
    _write_text(tmp_path, "README.md")
    _write_marker(tmp_path, "template_sync:\n  included_modules:\n  - markdown\n")
    _write_text(tmp_path, ".template-sync/scripts/validate_marker.py")
    commands: list[tuple[str, ...]] = []
    stdout = io.StringIO()

    result = first_adoption.run_first_adoption_checks(
        tmp_path,
        plan_only=True,
        command_runner=_recording_runner(commands),
        time_source=_queued_time_source(_utc_time(0), _utc_time(2)),
        stdout=stdout,
    )

    output = stdout.getvalue()
    assert result == 0
    assert commands == []
    assert "Run mode: check" in output
    assert "Collected 3 tracked or untracked non-ignored regular file(s)." in output
    assert "Git-visible regular file(s):" in output
    assert "  - .template-sync/marker.yml" in output
    assert "  - .template-sync/scripts/validate_marker.py" in output
    assert "  - README.md" in output
    assert "Markdown module appears retained" in output
    assert "Planned validation commands (2):" in output
    assert "  1. [pre-commit] pre-commit run --files" in output
    assert "  2. [marker-validation]" in output
    assert "Plan-only mode: validation commands were not run." in output
    assert "No Git status changes were detected" in output
    assert "Total elapsed time: 2.000s" in output
    assert "Command 1/2 [pre-commit] start time" not in output


def test_fix_mode_plan_only_prints_fix_mode_without_running(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Plan-only mode can preview the explicit fix-mode command plan."""
    monkeypatch.setattr(
        first_adoption,
        "default_pre_commit_prefix",
        lambda: ("pre-commit", "run", "--files"),
    )
    _run_git(tmp_path, "init")
    _write_text(tmp_path, "README.md")
    commands: list[tuple[str, ...]] = []
    stdout = io.StringIO()

    result = first_adoption.run_first_adoption_checks(
        tmp_path,
        run_mode=first_adoption.FIX_MODE,
        plan_only=True,
        command_runner=_recording_runner(commands),
        stdout=stdout,
    )

    output = stdout.getvalue()
    assert result == 0
    assert commands == []
    assert "Run mode: fix" in output
    assert "Plan-only mode: validation commands were not run." in output


def test_marker_absent_does_not_run_marker_validator(tmp_path: Path) -> None:
    """Marker validation is skipped when no downstream marker exists."""
    _run_git(tmp_path, "init")
    _write_text(tmp_path, "README.md")
    commands: list[tuple[str, ...]] = []

    result = first_adoption.run_first_adoption_checks(
        tmp_path,
        command_runner=_recording_runner(commands),
        stdout=io.StringIO(),
    )

    assert result == 0
    assert commands[0][-3:] == ("run", "--files", "README.md")
    assert not any("validate_marker.py" in arg for cmd in commands for arg in cmd)


def test_timing_output_uses_injected_time_source_and_prints_cold_start_guidance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Command timing and total elapsed output are deterministic in tests."""
    monkeypatch.setattr(
        first_adoption,
        "default_pre_commit_prefix",
        lambda: ("pre-commit", "run", "--files"),
    )
    _run_git(tmp_path, "init")
    _write_text(tmp_path, "README.md")
    _write_text(tmp_path, ".github/scripts/replace-template-placeholders.py")
    commands: list[tuple[str, ...]] = []
    stdout = io.StringIO()

    result = first_adoption.run_first_adoption_checks(
        tmp_path,
        command_runner=_recording_runner(commands),
        time_source=_queued_time_source(
            _utc_time(0),
            _utc_time(5),
            _utc_time(9),
            _utc_time(10),
            _utc_time(13),
            _utc_time(20),
        ),
        stdout=stdout,
    )

    output = stdout.getvalue()
    assert result == 0
    assert len(commands) == 2
    assert "Planned validation commands (2):" in output
    assert "Cold pre-commit hook environment bootstrapping may take several minutes" in output
    assert "Command 1/2 [pre-commit] start time (UTC): 2026-06-03T12:00:05Z" in output
    assert "Command 1/2 [pre-commit] completed with exit code 0" in output
    assert "Command 1/2 [pre-commit] end time (UTC): 2026-06-03T12:00:09Z" in output
    assert "Command 1/2 [pre-commit] elapsed time: 4.000s" in output
    assert "Command 2/2 [placeholder-scan] start time (UTC): 2026-06-03T12:00:10Z" in output
    assert "Command 2/2 [placeholder-scan] elapsed time: 3.000s" in output
    assert "No Git status changes were detected" in output
    assert "Total elapsed time: 20.000s" in output


def test_unchanged_git_status_passes_after_validation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A stable dirty status from before the run is not treated as a new mutation."""
    monkeypatch.setattr(
        first_adoption,
        "default_pre_commit_prefix",
        lambda: ("pre-commit", "run", "--files"),
    )
    _run_git(tmp_path, "init")
    _write_text(tmp_path, "README.md")
    commands: list[tuple[str, ...]] = []
    stdout = io.StringIO()

    result = first_adoption.run_first_adoption_checks(
        tmp_path,
        command_runner=_recording_runner(commands),
        git_status_reader=_queued_status_reader(("?? README.md",), ("?? README.md",)),
        stdout=stdout,
    )

    assert result == 0
    assert commands == [("pre-commit", "run", "--files", "README.md")]
    assert "No Git status changes were detected" in stdout.getvalue()


def test_changed_git_status_exits_distinctly_after_validation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A command-induced Git status change is reported and exits distinctly."""
    monkeypatch.setattr(
        first_adoption,
        "default_pre_commit_prefix",
        lambda: ("pre-commit", "run", "--files"),
    )
    _run_git(tmp_path, "init")
    _write_text(tmp_path, "README.md")
    commands: list[tuple[str, ...]] = []
    stdout = io.StringIO()

    result = first_adoption.run_first_adoption_checks(
        tmp_path,
        command_runner=_recording_runner(commands),
        git_status_reader=_queued_status_reader((), (" M README.md", "?? generated.txt")),
        stdout=stdout,
    )

    output = stdout.getvalue()
    assert result == first_adoption.CHANGED_FILES_EXIT_CODE
    assert commands == [("pre-commit", "run", "--files", "README.md")]
    assert "Git changed-file summary:" in output
    assert "  Before invocation:" in output
    assert "    - <none>" in output
    assert "  After invocation:" in output
    assert "    -  M README.md" in output
    assert "    - ?? generated.txt" in output
    assert "Inspect the changes" in output
    assert "rerun with --fix" in output


def test_fix_mode_tolerates_mutations_without_failing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fix mode reports command-induced mutations but exits zero."""
    monkeypatch.setattr(
        first_adoption,
        "default_pre_commit_prefix",
        lambda: ("pre-commit", "run", "--files"),
    )
    _run_git(tmp_path, "init")
    _write_text(tmp_path, "README.md")
    commands: list[tuple[str, ...]] = []
    stdout = io.StringIO()

    result = first_adoption.run_first_adoption_checks(
        tmp_path,
        run_mode=first_adoption.FIX_MODE,
        command_runner=_recording_runner(commands),
        git_status_reader=_queued_status_reader((), (" M README.md",)),
        stdout=stdout,
    )

    output = stdout.getvalue()
    assert result == 0
    assert commands == [("pre-commit", "run", "--files", "README.md")]
    assert "Run mode: fix" in output
    assert "Git changed-file summary:" in output
    assert "    -  M README.md" in output
    assert "as intended by fix mode" in output
    assert "rerun with --check" in output


def test_check_mode_reports_command_failure_before_changed_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failing command takes exit-code precedence over a mutated work tree."""
    monkeypatch.setattr(
        first_adoption,
        "default_pre_commit_prefix",
        lambda: ("pre-commit", "run", "--files"),
    )
    _run_git(tmp_path, "init")
    _write_text(tmp_path, "README.md")
    stdout = io.StringIO()

    def failing_runner(command: Sequence[str], _repo_root: Path) -> int:
        del command
        return 1

    result = first_adoption.run_first_adoption_checks(
        tmp_path,
        command_runner=failing_runner,
        git_status_reader=_queued_status_reader((), (" M README.md",)),
        stdout=stdout,
    )

    output = stdout.getvalue()
    assert result == 1
    assert "Git changed-file summary:" in output
    assert "    -  M README.md" in output
    assert "First-adoption checks failed:" in output
    assert "exited with 1" in output


def test_git_status_lines_reports_oserror_as_check_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A missing git executable surfaces as FirstAdoptionCheckError, not a raw OSError."""

    def raise_oserror(*_args: object, **_kwargs: object) -> object:
        raise FileNotFoundError(2, "No such file or directory")

    monkeypatch.setattr(first_adoption.subprocess, "run", raise_oserror)

    with pytest.raises(first_adoption.FirstAdoptionCheckError) as excinfo:
        first_adoption.git_status_lines(tmp_path)

    assert "Unable to inspect Git changed files" in str(excinfo.value)


def test_collect_present_regular_files_reports_oserror_as_check_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A missing git executable surfaces as FirstAdoptionCheckError, not a raw OSError."""

    def raise_oserror(*_args: object, **_kwargs: object) -> object:
        raise FileNotFoundError(2, "No such file or directory")

    monkeypatch.setattr(first_adoption.subprocess, "run", raise_oserror)

    with pytest.raises(first_adoption.FirstAdoptionCheckError) as excinfo:
        first_adoption.collect_present_regular_files(tmp_path)

    assert "Unable to inspect Git-visible files" in str(excinfo.value)


def test_marker_present_runs_marker_validator(tmp_path: Path) -> None:
    """A present marker adds the marker validator after the pre-commit file check."""
    _run_git(tmp_path, "init")
    _write_text(tmp_path, "README.md")
    _write_text(tmp_path, ".template-sync/marker.yml", "template_sync:\n")
    _write_text(tmp_path, ".template-sync/scripts/validate_marker.py", "print('ok')\n")
    commands: list[tuple[str, ...]] = []

    result = first_adoption.run_first_adoption_checks(
        tmp_path,
        command_runner=_recording_runner(commands),
        stdout=io.StringIO(),
    )

    assert result == 0
    assert commands[-1] == (
        sys.executable,
        ".template-sync/scripts/validate_marker.py",
        "--require-marker",
    )
    assert ".template-sync/marker.yml" in commands[0]


def test_multiple_failures_are_reported_by_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The runner continues through the plan and reports every failing command."""
    monkeypatch.setattr(
        first_adoption,
        "default_pre_commit_prefix",
        lambda: ("pre-commit", "run", "--files"),
    )
    _run_git(tmp_path, "init")
    _write_text(tmp_path, "README.md")
    _write_text(tmp_path, ".github/scripts/replace-template-placeholders.py")
    return_codes = [7, 3]
    records: list[tuple[str, ...]] = []

    def run(command: Sequence[str], _repo_root: Path) -> int:
        records.append(tuple(command))
        return return_codes.pop(0)

    stdout = io.StringIO()

    result = first_adoption.run_first_adoption_checks(
        tmp_path,
        command_runner=run,
        time_source=_incrementing_time_source(),
        stdout=stdout,
    )

    output = stdout.getvalue()
    assert result == 1
    assert len(records) == 2
    assert "Command 1/2 [pre-commit] completed with exit code 7" in output
    assert "Command 2/2 [placeholder-scan] completed with exit code 3" in output
    assert "First-adoption checks failed:" in output
    assert "  - pre-commit: pre-commit run --files" in output
    assert "exited with 7" in output
    assert "  - placeholder-scan:" in output
    assert "exited with 3" in output


def test_placeholder_script_runs_when_present(tmp_path: Path) -> None:
    """A present placeholder helper adds the scan command."""
    _run_git(tmp_path, "init")
    _write_text(tmp_path, "README.md")
    _write_text(tmp_path, ".github/scripts/replace-template-placeholders.py", "print('ok')\n")
    commands: list[tuple[str, ...]] = []

    result = first_adoption.run_first_adoption_checks(
        tmp_path,
        command_runner=_recording_runner(commands),
        stdout=io.StringIO(),
    )

    assert result == 0
    assert (
        sys.executable,
        ".github/scripts/replace-template-placeholders.py",
        "scan",
    ) in commands


@pytest.mark.parametrize(
    "marker_text",
    [
        pytest.param(
            "\n".join(
                [
                    "template_sync:",
                    "  included_modules:",
                    "  - baseline",
                    "  - markdown",
                    "  issue_labels:",
                    "  - triage",
                    "",
                ]
            ),
            id="indentless-sequence",
        ),
        pytest.param(
            "\n".join(
                [
                    "template_sync:",
                    "  included_modules:",
                    "    - baseline",
                    "    - markdown",
                    "  issue_labels:",
                    "    - triage",
                    "",
                ]
            ),
            id="visually-indented-sequence",
        ),
        pytest.param(
            "\n".join(
                [
                    "template_sync:",
                    "    included_modules:",
                    "    - baseline",
                    "    - markdown",
                    "    issue_labels:",
                    "    - triage",
                    "",
                ]
            ),
            id="four-space-child-indent",
        ),
        pytest.param(
            "\n".join(
                [
                    "template_sync: # downstream marker",
                    "  included_modules: # retained modules",
                    "  - baseline",
                    '  - "markdown" # exact module',
                    "",
                ]
            ),
            id="key-comments",
        ),
    ],
)
def test_marker_includes_markdown_module_detects_scoped_module(
    tmp_path: Path,
    marker_text: str,
) -> None:
    """The marker scan detects markdown only in top-level retained modules."""
    _write_marker(tmp_path, marker_text)

    assert first_adoption.marker_includes_markdown_module(tmp_path) is True


@pytest.mark.parametrize(
    "item_line",
    [
        "- markdown",
        "- 'markdown'",
        '- "markdown"',
        "- markdown # note",
        "- 'markdown' # note",
        '- "markdown" # note',
    ],
)
def test_marker_includes_markdown_module_accepts_exact_scalar_items(
    tmp_path: Path,
    item_line: str,
) -> None:
    """Exact unquoted and matching-quoted markdown items are recognized."""
    _write_marker(tmp_path, f"template_sync:\n  included_modules:\n  {item_line}\n")

    assert first_adoption.marker_includes_markdown_module(tmp_path) is True


@pytest.mark.parametrize(
    "marker_text",
    [
        pytest.param(
            "\n".join(
                [
                    "template_sync:",
                    "  included_modules:",
                    "  - baseline",
                    "  issue_labels:",
                    "  - markdown",
                    "",
                ]
            ),
            id="issue-label-markdown",
        ),
        pytest.param(
            "template_sync:\n    included_modules:\n    - baseline\n",
            id="four-space-child-indent-without-markdown",
        ),
        pytest.param(
            "included_modules:\n- markdown\ntemplate_sync:\n  source_repo: example\n",
            id="top-level-included-modules",
        ),
        pytest.param(
            "root:\n  template_sync:\n    included_modules:\n    - markdown\n",
            id="nested-template-sync",
        ),
        pytest.param(
            "# template_sync:\n#   included_modules:\n#   - markdown\n",
            id="commented-template-sync",
        ),
        pytest.param(
            'notes: "template_sync:"\nincluded_modules:\n- markdown\n',
            id="scalar-template-sync",
        ),
        pytest.param(
            "template_sync:\n  source_repo: example\nother:\n  included_modules:\n  - markdown\n",
            id="included-modules-outside-template-sync",
        ),
        pytest.param(
            "template_sync:\n  some_nested_mapping:\n    included_modules:\n    - markdown\n",
            id="nested-included-modules",
        ),
        pytest.param(
            "template_sync:\n  # included_modules:\n  # - markdown\n",
            id="commented-included-modules",
        ),
        pytest.param(
            'template_sync:\n  notes: "included_modules:"\n  issue_labels:\n  - markdown\n',
            id="scalar-included-modules",
        ),
        pytest.param(
            "\n".join(
                [
                    "template_sync:",
                    "  included_modules:",
                    "  - markdown-extra",
                    "  - not-markdown",
                    "  - markdown#note",
                    "",
                ]
            ),
            id="substring-values",
        ),
        pytest.param(
            "template_sync:\n  included_modules:\n  - 'markdown\"\n  - \"markdown'\n",
            id="malformed-quotes",
        ),
        pytest.param(
            "source_repo: example\n",
            id="missing-template-sync",
        ),
        pytest.param(
            "template_sync:\n  source_repo: example\n",
            id="missing-included-modules",
        ),
        pytest.param(
            "template_sync:\n  included_modules: []\n  issue_labels:\n  - markdown\n",
            id="empty-list",
        ),
        pytest.param(
            "template_sync:\n  included_modules:\n  issue_labels:\n  - markdown\n",
            id="block-with-no-items",
        ),
    ],
)
def test_marker_includes_markdown_module_rejects_unscoped_or_inexact_matches(
    tmp_path: Path,
    marker_text: str,
) -> None:
    """Look-alike markdown tokens outside the module block are ignored."""
    _write_marker(tmp_path, marker_text)

    assert first_adoption.marker_includes_markdown_module(tmp_path) is False


def test_marker_includes_markdown_module_skips_blank_and_comment_lines(
    tmp_path: Path,
) -> None:
    """Blank and comment lines do not terminate the retained-module sequence."""
    _write_marker(
        tmp_path,
        "\n".join(
            [
                "template_sync:",
                "  included_modules:",
                "  # retained baseline module",
                "",
                "  - baseline",
                "",
                "  # retained markdown module",
                "  - markdown",
                "  issue_labels:",
                "  - triage",
                "",
            ]
        ),
    )

    assert first_adoption.marker_includes_markdown_module(tmp_path) is True


def test_markdown_note_ignores_markdown_issue_label(tmp_path: Path) -> None:
    """An issue label named markdown does not imply the Markdown module is retained."""
    _write_marker(
        tmp_path,
        "\n".join(
            [
                "template_sync:",
                "  included_modules:",
                "  - baseline",
                "  issue_labels:",
                "  - markdown",
                "",
            ]
        ),
    )

    plan = first_adoption.markdown_commands_and_notes(tmp_path)

    assert plan == first_adoption.CheckPlan(commands=(), notes=())


def test_package_markdown_scripts_run_when_present(tmp_path: Path) -> None:
    """Supported package scripts add optional Markdown validation commands."""
    _run_git(tmp_path, "init")
    _write_text(tmp_path, "README.md")
    _write_text(
        tmp_path,
        "package.json",
        '{"scripts":{"lint:md":"markdownlint .","lint:md:links":"remark ."}}\n',
    )
    commands: list[tuple[str, ...]] = []

    result = first_adoption.run_first_adoption_checks(
        tmp_path,
        command_runner=_recording_runner(commands),
        stdout=io.StringIO(),
    )

    assert result == 0
    assert any(command[-2:] == ("run", "lint:md") for command in commands)
    assert any(command[-2:] == ("run", "lint:md:links") for command in commands)


def test_pre_commit_prefix_falls_back_to_python_module(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The runner works when the pre-commit console script is not on PATH."""
    monkeypatch.setattr(first_adoption.shutil, "which", lambda _name: None)

    prefix = first_adoption.default_pre_commit_prefix()

    assert prefix == (sys.executable, "-m", "pre_commit", "run", "--files")


def test_npm_executable_prefers_cmd_shim_on_windows_style_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The runner can use npm.cmd when bare npm is not directly executable."""

    def fake_which(name: str) -> str | None:
        if name == "npm.cmd":
            return "C:\\tools\\npm.cmd"
        return None

    monkeypatch.setattr(first_adoption.shutil, "which", fake_which)

    assert first_adoption.default_npm_executable() == "C:\\tools\\npm.cmd"


def test_downstream_pytest_selection_includes_unmarked_and_excludes_upstream_only(
    tmp_path: Path,
) -> None:
    """Negative marker selection keeps new unmarked tests in the downstream gate."""
    pytest_root = _write_pytest_profile_root(tmp_path)
    test_file = pytest_root / "test_profile_selection.py"
    test_file.write_text(
        "\n".join(
            [
                "import pytest",
                "",
                "def test_unmarked_is_selected():",
                "    pass",
                "",
                "@pytest.mark.upstream_template_only",
                "def test_upstream_only_is_excluded():",
                "    pass",
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--collect-only",
            "-q",
            "-m",
            "not upstream_template_only",
            test_file.name,
        ],
        cwd=pytest_root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "test_unmarked_is_selected" in result.stdout
    assert "test_upstream_only_is_excluded" not in result.stdout


def test_unregistered_pytest_marker_fails_collection(tmp_path: Path) -> None:
    """Committed strict marker configuration rejects marker typos during collection."""
    pytest_root = _write_pytest_profile_root(tmp_path)
    test_file = pytest_root / "test_bad_marker.py"
    test_file.write_text(
        "\n".join(
            [
                "import pytest",
                "",
                "@pytest.mark.not_registered_here",
                "def test_bad_marker():",
                "    pass",
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--collect-only",
            test_file.name,
        ],
        cwd=pytest_root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert result.returncode != 0
    assert "not_registered_here" in result.stdout + result.stderr
