"""Run first-adoption checks against tracked and untracked repository files."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import shlex
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn, TextIO

DEFAULT_MAX_COMMAND_LENGTH = 30000 if os.name == "nt" else 100000
GIT_FILE_LIST_COMMAND = (
    "git",
    "ls-files",
    "-z",
    "--cached",
    "--others",
    "--exclude-standard",
)
PRE_COMMIT_EXECUTABLE_PREFIX = ("pre-commit", "run", "--files")
PLACEHOLDER_SCRIPT = ".github/scripts/replace-template-placeholders.py"
MARKER_PATH = ".template-sync/marker.yml"
MARKER_VALIDATOR_SCRIPT = ".template-sync/scripts/validate_marker.py"
MARKDOWN_PACKAGE_SCRIPTS = ("lint:md", "lint:md:links", "lint:md:nested")
MARKDOWN_MODULE_PATTERN = re.compile(r"(?m)^\s*-\s*['\"]?markdown['\"]?\s*(?:#.*)?$")

CommandRunner = Callable[[Sequence[str], Path], int]


class FirstAdoptionCheckError(RuntimeError):
    """Raised when first-adoption checks cannot be planned or run."""


@dataclass(frozen=True)
class FileCollection:
    """Git-visible file discovery results."""

    files: tuple[str, ...]
    skipped_non_regular_paths: tuple[str, ...]


@dataclass(frozen=True)
class CheckPlan:
    """Commands and notes for a first-adoption validation run."""

    commands: tuple[tuple[str, ...], ...]
    notes: tuple[str, ...]


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Validate tracked and untracked non-ignored files before the first "
            "template adoption commit."
        )
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Repository root. Defaults to the repository root containing this script.",
    )
    parser.add_argument(
        "--max-command-length",
        type=int,
        default=DEFAULT_MAX_COMMAND_LENGTH,
        help=(
            "Maximum formatted command length before splitting pre-commit --files "
            f"invocations. Default: {DEFAULT_MAX_COMMAND_LENGTH}."
        ),
    )
    return parser.parse_args(argv)


def default_repo_root() -> Path:
    """Return the repository root implied by this script's committed location."""
    return Path(__file__).resolve().parents[2]


def resolve_repo_root(raw_repo_root: str | None) -> Path:
    """Resolve and validate the repository root argument."""
    repo_root = Path(raw_repo_root).expanduser() if raw_repo_root else default_repo_root()
    resolved = repo_root.resolve()
    if not resolved.is_dir():
        raise FirstAdoptionCheckError("Repository root does not exist or is not a directory.")
    return resolved


def resolve_repo_path(repo_root: Path, relative_path: str) -> Path:
    """Resolve a Git-relative path inside the repository root."""
    if "\\" in relative_path or Path(relative_path).is_absolute():
        raise FirstAdoptionCheckError(f"Git path must be repository-relative: {relative_path}")
    parts = Path(relative_path).parts
    if any(part in ("", ".", "..") for part in parts):
        raise FirstAdoptionCheckError(f"Git path must not contain traversal: {relative_path}")
    resolved_path = (repo_root / relative_path).resolve()
    try:
        resolved_path.relative_to(repo_root)
    except ValueError as error:
        raise FirstAdoptionCheckError(
            f"Git path escapes repository root: {relative_path}"
        ) from error
    return resolved_path


def is_present_regular_file(path: Path) -> bool:
    """Return whether ``path`` is a present regular file, excluding symlinks."""
    return not path.is_symlink() and path.is_file()


def format_command(command: Sequence[str]) -> str:
    """Return a shell-like representation of the exact argument vector."""
    command_parts = list(command)
    if os.name == "nt":
        return subprocess.list2cmdline(command_parts)
    return shlex.join(command_parts)


def run_external_command(command: Sequence[str], repo_root: Path) -> int:
    """Run one external command in the repository root."""
    try:
        result = subprocess.run(list(command), cwd=repo_root, check=False)
    except OSError as error:
        error_summary = f"{type(error).__name__}: {error.strerror or 'I/O error'}"
        raise FirstAdoptionCheckError(f"Unable to run {command[0]} ({error_summary}).") from error
    return result.returncode


def collect_present_regular_files(
    repo_root: Path,
    *,
    stdout: TextIO | None = None,
) -> FileCollection:
    """Collect tracked and untracked non-ignored regular files from Git."""
    if stdout is not None:
        print(f"$ {format_command(GIT_FILE_LIST_COMMAND)}", file=stdout, flush=True)

    result = subprocess.run(
        list(GIT_FILE_LIST_COMMAND),
        cwd=repo_root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "git ls-files failed"
        raise FirstAdoptionCheckError(f"Unable to inspect Git-visible files: {message}")

    files: list[str] = []
    skipped_non_regular_paths: list[str] = []
    seen_paths: set[str] = set()
    for relative_path in result.stdout.split("\0"):
        if not relative_path or relative_path in seen_paths:
            continue
        seen_paths.add(relative_path)
        path = resolve_repo_path(repo_root, relative_path)
        if is_present_regular_file(path):
            files.append(relative_path)
        elif path.exists() or path.is_symlink():
            skipped_non_regular_paths.append(relative_path)

    return FileCollection(
        files=tuple(sorted(files)),
        skipped_non_regular_paths=tuple(sorted(skipped_non_regular_paths)),
    )


def default_pre_commit_prefix() -> tuple[str, ...]:
    """Return the preferred pre-commit command prefix for this environment."""
    if shutil.which("pre-commit") is not None:
        return PRE_COMMIT_EXECUTABLE_PREFIX
    return (sys.executable, "-m", "pre_commit", "run", "--files")


def default_npm_executable() -> str:
    """Return an npm executable name or path suitable for direct subprocess use."""
    return shutil.which("npm") or shutil.which("npm.cmd") or "npm"


def pre_commit_commands(
    files: Sequence[str],
    *,
    max_command_length: int = DEFAULT_MAX_COMMAND_LENGTH,
    command_prefix: Sequence[str] | None = None,
) -> tuple[tuple[str, ...], ...]:
    """Build chunked ``pre-commit run --files`` commands for ``files``."""
    prefix = tuple(command_prefix or default_pre_commit_prefix())
    if max_command_length <= len(format_command(prefix)):
        raise FirstAdoptionCheckError("--max-command-length is too small for pre-commit.")

    commands: list[tuple[str, ...]] = []
    current_files: list[str] = []
    for relative_path in files:
        candidate = (*prefix, *current_files, relative_path)
        if current_files and len(format_command(candidate)) > max_command_length:
            commands.append((*prefix, *current_files))
            current_files = [relative_path]
        else:
            current_files.append(relative_path)

    if current_files:
        commands.append((*prefix, *current_files))
    return tuple(commands)


def require_regular_script(repo_root: Path, relative_path: str) -> None:
    """Raise if a required helper script is missing or unsafe to execute."""
    path = repo_root / relative_path
    if not path.exists():
        raise FirstAdoptionCheckError(f"Required helper script is missing: {relative_path}")
    if not is_present_regular_file(path):
        raise FirstAdoptionCheckError(
            f"Required helper script is not a regular file: {relative_path}"
        )


def optional_regular_file_exists(repo_root: Path, relative_path: str) -> bool:
    """Return whether an optional repository file exists as a regular file."""
    path = repo_root / relative_path
    if not path.exists():
        return False
    if not is_present_regular_file(path):
        raise FirstAdoptionCheckError(f"Expected a regular file: {relative_path}")
    return True


def load_package_scripts(repo_root: Path) -> dict[str, object]:
    """Return the root package.json scripts mapping when package.json exists."""
    package_path = repo_root / "package.json"
    if not package_path.exists():
        return {}
    if not is_present_regular_file(package_path):
        raise FirstAdoptionCheckError("Expected a regular file: package.json")
    try:
        package_data = json.loads(package_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise FirstAdoptionCheckError(f"package.json is not valid JSON: {error}") from error
    except OSError as error:
        error_summary = f"{type(error).__name__}: {error.strerror or 'I/O error'}"
        raise FirstAdoptionCheckError(f"Unable to read package.json ({error_summary}).") from error

    scripts = package_data.get("scripts") if isinstance(package_data, dict) else None
    return scripts if isinstance(scripts, dict) else {}


def marker_includes_markdown_module(repo_root: Path) -> bool:
    """Return whether the downstream marker appears to retain the markdown module."""
    marker_path = repo_root / MARKER_PATH
    if not marker_path.exists():
        return False
    if not is_present_regular_file(marker_path):
        raise FirstAdoptionCheckError(f"Expected a regular file: {MARKER_PATH}")
    try:
        marker_text = marker_path.read_text(encoding="utf-8")
    except OSError as error:
        error_summary = f"{type(error).__name__}: {error.strerror or 'I/O error'}"
        raise FirstAdoptionCheckError(f"Unable to read {MARKER_PATH} ({error_summary}).") from error
    return bool(MARKDOWN_MODULE_PATTERN.search(marker_text))


def markdown_commands_and_notes(repo_root: Path) -> CheckPlan:
    """Build optional Markdown npm commands and any explanatory notes."""
    package_scripts = load_package_scripts(repo_root)
    commands = tuple(
        (default_npm_executable(), "run", script_name)
        for script_name in MARKDOWN_PACKAGE_SCRIPTS
        if script_name in package_scripts
    )
    if commands:
        return CheckPlan(commands=commands, notes=())

    if marker_includes_markdown_module(repo_root):
        return CheckPlan(
            commands=(),
            notes=(
                "Markdown module appears retained, but no supported Markdown npm "
                "scripts were found in package.json.",
            ),
        )
    return CheckPlan(commands=(), notes=())


def build_check_plan(
    repo_root: Path,
    files: Sequence[str],
    *,
    max_command_length: int = DEFAULT_MAX_COMMAND_LENGTH,
) -> CheckPlan:
    """Build the first-adoption check command plan."""
    commands: list[tuple[str, ...]] = []
    notes: list[str] = []

    if files:
        commands.extend(pre_commit_commands(files, max_command_length=max_command_length))
    else:
        notes.append(
            "No tracked or untracked non-ignored regular files found; "
            "skipping pre-commit --files."
        )

    if optional_regular_file_exists(repo_root, PLACEHOLDER_SCRIPT):
        commands.append((sys.executable, PLACEHOLDER_SCRIPT, "scan"))

    if (repo_root / MARKER_PATH).exists():
        if not optional_regular_file_exists(repo_root, MARKER_PATH):
            raise FirstAdoptionCheckError(f"Expected a regular file: {MARKER_PATH}")
        require_regular_script(repo_root, MARKER_VALIDATOR_SCRIPT)
        commands.append((sys.executable, MARKER_VALIDATOR_SCRIPT, "--require-marker"))

    markdown_plan = markdown_commands_and_notes(repo_root)
    commands.extend(markdown_plan.commands)
    notes.extend(markdown_plan.notes)

    return CheckPlan(commands=tuple(commands), notes=tuple(notes))


def run_first_adoption_checks(
    repo_root: Path,
    *,
    max_command_length: int = DEFAULT_MAX_COMMAND_LENGTH,
    command_runner: CommandRunner = run_external_command,
    stdout: TextIO = sys.stdout,
) -> int:
    """Run first-adoption checks and return a process exit code."""
    collection = collect_present_regular_files(repo_root, stdout=stdout)
    if collection.files:
        print(
            f"Collected {len(collection.files)} tracked or untracked non-ignored "
            "regular file(s).",
            file=stdout,
            flush=True,
        )
    if collection.skipped_non_regular_paths:
        print("Skipped non-regular Git-visible path(s):", file=stdout, flush=True)
        for relative_path in collection.skipped_non_regular_paths:
            print(f"  - {relative_path}", file=stdout, flush=True)

    plan = build_check_plan(
        repo_root=repo_root,
        files=collection.files,
        max_command_length=max_command_length,
    )
    for note in plan.notes:
        print(note, file=stdout, flush=True)

    if not plan.commands:
        print("No first-adoption checks were available to run.", file=stdout, flush=True)
        return 0

    failures: list[str] = []
    for command in plan.commands:
        print(f"$ {format_command(command)}", file=stdout, flush=True)
        return_code = command_runner(command, repo_root)
        if return_code != 0:
            failures.append(f"{format_command(command)} exited with {return_code}")

    if failures:
        print("First-adoption checks failed:", file=stdout, flush=True)
        for failure in failures:
            print(f"  - {failure}", file=stdout, flush=True)
        return 1

    print("First-adoption checks passed.", file=stdout, flush=True)
    return 0


def fail(message: str) -> NoReturn:
    """Print an error and exit non-zero."""
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the first-adoption check CLI."""
    args = parse_args(argv)
    try:
        repo_root = resolve_repo_root(args.repo_root)
        return run_first_adoption_checks(
            repo_root,
            max_command_length=args.max_command_length,
        )
    except FirstAdoptionCheckError as error:
        fail(str(error))


if __name__ == "__main__":
    raise SystemExit(main())
