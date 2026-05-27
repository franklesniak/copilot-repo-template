"""Exercise the first-adoption working-tree validation runner."""

from __future__ import annotations

import importlib.util
import io
import subprocess
import sys
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
    assert not any("validate_marker.py" in command for command in commands for command in command)


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
