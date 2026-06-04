"""Exercise the first-adoption working-tree validation runner."""

from __future__ import annotations

import importlib.util
import io
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / ".template-sync"
    / "scripts"
    / "run_first_adoption_checks.py"
)
SCRIPT_SPEC = importlib.util.spec_from_file_location("run_first_adoption_checks", SCRIPT_PATH)
if SCRIPT_SPEC is None or SCRIPT_SPEC.loader is None:
    raise RuntimeError(f"Unable to load first-adoption helper module from {SCRIPT_PATH}")
first_adoption = importlib.util.module_from_spec(SCRIPT_SPEC)
sys.modules[SCRIPT_SPEC.name] = first_adoption
SCRIPT_SPEC.loader.exec_module(first_adoption)


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


def _recording_runner(records: list[tuple[str, ...]]):
    """Return a fake command runner that records commands."""

    def run(command: list[str] | tuple[str, ...], _repo_root: Path) -> int:
        records.append(tuple(command))
        return 0

    return run


def _utc_time(second: int) -> datetime:
    """Return a deterministic UTC timestamp for timing assertions."""
    return datetime(2026, 6, 3, 12, 0, second, tzinfo=timezone.utc)


def _queued_time_source(*timestamps: datetime):
    """Return a time source that consumes a fixed sequence of timestamps."""
    remaining_timestamps = list(timestamps)

    def now() -> datetime:
        assert remaining_timestamps, "No queued timestamp remains."
        return remaining_timestamps.pop(0)

    return now


def _incrementing_time_source():
    """Return a deterministic time source that advances one second per read."""
    current_timestamp = [_utc_time(0)]

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
    assert "No tracked or untracked non-ignored regular files found" in stdout.getvalue()
    assert "No first-adoption checks were available to run." in stdout.getvalue()


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
    _write_text(tmp_path, ".template-sync/marker.yml", "included_modules:\n  - markdown\n")
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
    _write_text(tmp_path, ".template-sync/marker.yml", "included_modules:\n  - markdown\n")
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
    assert "Total elapsed time: 2.000s" in output
    assert "Command 1/2 [pre-commit] start time" not in output


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
    assert "Total elapsed time: 20.000s" in output


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

    def run(command: list[str] | tuple[str, ...], _repo_root: Path) -> int:
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
