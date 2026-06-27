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
from datetime import datetime, timezone
from pathlib import Path
from typing import NoReturn, TextIO

DEFAULT_MAX_COMMAND_LENGTH = 30000 if os.name == "nt" else 100000
DEFAULT_PROBE_TIMEOUT_SECONDS = 10.0
DEFAULT_DIAGNOSTIC_MAX_BYTES = 4096
DEFAULT_DIAGNOSTIC_MAX_LINES = 40
GIT_FILE_LIST_COMMAND = (
    "git",
    "ls-files",
    "-z",
    "--cached",
    "--others",
    "--exclude-standard",
)
GIT_STATUS_COMMAND = (
    "git",
    "status",
    "--porcelain=v1",
    "--untracked-files=all",
)
PRE_COMMIT_EXECUTABLE_PREFIX = ("pre-commit", "run", "--files")
PRE_COMMIT_CONFIG_PATH = ".pre-commit-config.yaml"
PLACEHOLDER_SCRIPT = ".github/scripts/replace-template-placeholders.py"
MARKER_PATH = ".template-sync/marker.yml"
MARKER_VALIDATOR_SCRIPT = ".template-sync/scripts/validate_marker.py"
QUALITY_REPORT_SCRIPT = ".template-sync/scripts/first_adoption_quality_reports.py"
MARKDOWN_PACKAGE_SCRIPTS = ("lint:md", "lint:md:links", "lint:md:nested")
AZURE_DEVOPS_MODULES = frozenset(
    ("azure-devops-platform", "azure-pipelines", "azure-devops-collaboration")
)
MARKER_MODULE_PATTERN = re.compile(r"(?m)^\s*-\s*['\"]?(?P<module>[a-z0-9-]+)['\"]?\s*(?:#.*)?$")
INCLUDED_MODULES_KEY_PATTERN = re.compile(r"^(?P<indent>\s*)included_modules\s*:\s*(?:#.*)?$")
MARKER_KEY_PATTERN = re.compile(
    r"^(?P<indent> *)(?P<key>[A-Za-z_][A-Za-z0-9_-]*):(?P<suffix>(?:[ \t].*)?)$"
)
MARKDOWN_MODULE_ITEM_PATTERN = re.compile(
    r"^ *-\s+(?:markdown|'markdown'|\"markdown\")(?:[ \t]+#.*)?[ \t]*$"
)
PRE_COMMIT_GROUP = "pre-commit"
PLACEHOLDER_SCAN_GROUP = "placeholder-scan"
MARKER_VALIDATION_GROUP = "marker-validation"
QUALITY_REPORT_GROUP = "quality-report"
MARKDOWN_FIXER_GROUP = "markdown-fixer"
MARKDOWN_SCRIPT_GROUP = "markdown-script"
CHECK_MODE = "check"
FIX_MODE = "fix"
DOCTOR_MODE = "doctor"
CHANGED_FILES_EXIT_CODE = 2
PROBE_AVAILABLE = "available"
PROBE_UNAVAILABLE = "unavailable"
PROBE_FAILED = "failed"
PROBE_TIMED_OUT = "timed-out"
PYTHON_DOCTOR_MODULE = "platform"
POWERSHELL_PROBE_FLAGS = ("-NoProfile", "-NonInteractive", "-Command")
PSSCRIPTANALYZER_PROBE = (
    "$module = Get-Module -ListAvailable PSScriptAnalyzer | "
    "Sort-Object Version -Descending | Select-Object -First 1; "
    "if ($null -eq $module) { "
    "Write-Error 'PSScriptAnalyzer module not available'; exit 1 }; "
    "$module.Version.ToString()"
)
POWERSHELL_VERSION_PROBE = "$PSVersionTable.PSVersion.ToString()"
PRE_COMMIT_HOOK_ID_PATTERN = re.compile(r"^\s*-\s+id:\s*['\"]?(?P<id>[^'\"\s#]+)")
CREDENTIAL_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)\b(?P<key>token|secret|password|passwd|api[_-]?key|access[_-]?token)"
    r"(?P<separator>\s*[:=]\s*)"
    r"(?P<value>[^\s,;]+)"
)
AUTHORIZATION_HEADER_PATTERN = re.compile(
    r"(?i)\b(?P<prefix>authorization\s*:\s*(?:bearer|basic)\s+)(?P<value>[^\s]+)"
)
URL_USERINFO_PATTERN = re.compile(r"(?i)(?P<scheme>[a-z][a-z0-9+.-]*://)(?P<userinfo>[^/\s@]+@)")
SCHEME_RELATIVE_USERINFO_PATTERN = re.compile(r"(?P<prefix>^|[^\w:])//(?P<userinfo>[^/\s@]+@)")

CommandRunner = Callable[[Sequence[str], Path], int]
GitStatusReader = Callable[[Path], tuple[str, ...]]
TimeSource = Callable[[], datetime]
ProbeExecutor = Callable[[Sequence[str], Path, float], "ProbeExecution"]


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

    commands: tuple["PlannedCommand", ...]
    notes: tuple[str, ...]


@dataclass(frozen=True)
class PlannedCommand:
    """One labeled validation command in the first-adoption plan."""

    group_label: str
    command: tuple[str, ...]


@dataclass(frozen=True)
class ProbeExecution:
    """Raw subprocess result for a small doctor probe command."""

    return_code: int | None
    stdout: str
    stderr: str
    timed_out: bool = False


@dataclass(frozen=True)
class DoctorProbe:
    """One non-mutating first-adoption doctor probe."""

    group_label: str
    name: str
    command: tuple[str, ...]
    note: str = ""


@dataclass(frozen=True)
class DoctorProbeResult:
    """Rendered result for one first-adoption doctor probe."""

    group_label: str
    name: str
    command: tuple[str, ...]
    availability_state: str
    exit_code: int | None
    elapsed_time: str
    timed_out: bool
    stdout: str
    stderr: str
    note: str = ""


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
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--check",
        dest="run_mode",
        action="store_const",
        const=CHECK_MODE,
        default=CHECK_MODE,
        help=(
            "Run validation in explicit check mode (default). Any Git status "
            "change during the invocation exits nonzero and must be inspected."
        ),
    )
    mode_group.add_argument(
        "--fix",
        dest="run_mode",
        action="store_const",
        const=FIX_MODE,
        help=(
            "Run validation in explicit fix mode so mutating hooks or fixers may "
            "update files without failing the run. The same validation commands "
            "run as in check mode; inspect the changed-file summary, keep or "
            "discard the edits intentionally, then rerun with --check."
        ),
    )
    mode_group.add_argument(
        "--doctor",
        dest="run_mode",
        action="store_const",
        const=DOCTOR_MODE,
        help=(
            "Run non-mutating environment/tool probes with per-command timeouts "
            "and bounded diagnostics. Doctor mode does not run validation hooks "
            "or fixers."
        ),
    )
    parser.add_argument(
        "--plan-only",
        action="store_true",
        help=(
            "Print Git-visible file collection results, notes, and the planned "
            "validation commands without running those validation commands."
        ),
    )
    parser.add_argument(
        "--doctor-timeout",
        type=float,
        default=DEFAULT_PROBE_TIMEOUT_SECONDS,
        help=(
            "Per-probe timeout in seconds for --doctor. "
            f"Default: {DEFAULT_PROBE_TIMEOUT_SECONDS:.1f}."
        ),
    )
    parser.add_argument(
        "--doctor-max-bytes",
        type=int,
        default=DEFAULT_DIAGNOSTIC_MAX_BYTES,
        help=(
            "Maximum captured diagnostic bytes per stdout/stderr stream in --doctor. "
            f"Default: {DEFAULT_DIAGNOSTIC_MAX_BYTES}."
        ),
    )
    parser.add_argument(
        "--doctor-max-lines",
        type=int,
        default=DEFAULT_DIAGNOSTIC_MAX_LINES,
        help=(
            "Maximum captured diagnostic lines per stdout/stderr stream in --doctor. "
            f"Default: {DEFAULT_DIAGNOSTIC_MAX_LINES}."
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


def default_time_source() -> datetime:
    """Return the current UTC wall-clock time."""
    return datetime.now(timezone.utc)


def normalize_utc(timestamp: datetime) -> datetime:
    """Return ``timestamp`` as a timezone-aware UTC datetime."""
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return timestamp.astimezone(timezone.utc)


def format_utc_timestamp(timestamp: datetime) -> str:
    """Return a stable UTC ISO 8601 timestamp string."""
    return normalize_utc(timestamp).isoformat(timespec="seconds").replace("+00:00", "Z")


def elapsed_seconds(started_at: datetime, ended_at: datetime) -> float:
    """Return elapsed seconds between two readings from the injected time source."""
    return (normalize_utc(ended_at) - normalize_utc(started_at)).total_seconds()


def format_elapsed_time(started_at: datetime, ended_at: datetime) -> str:
    """Return a stable elapsed-time string."""
    return f"{elapsed_seconds(started_at, ended_at):.3f}s"


def redact_diagnostic_text(value: str) -> str:
    """Redact obvious credentials from doctor diagnostic text."""
    redacted = URL_USERINFO_PATTERN.sub(r"\g<scheme>***@", value)
    redacted = SCHEME_RELATIVE_USERINFO_PATTERN.sub(
        lambda match: f"{match.group('prefix')}//***@",
        redacted,
    )
    redacted = AUTHORIZATION_HEADER_PATTERN.sub(r"\g<prefix>***", redacted)
    return CREDENTIAL_ASSIGNMENT_PATTERN.sub(
        r"\g<key>\g<separator>***",
        redacted,
    )


def bound_diagnostic_text(
    value: str,
    *,
    max_bytes: int = DEFAULT_DIAGNOSTIC_MAX_BYTES,
    max_lines: int = DEFAULT_DIAGNOSTIC_MAX_LINES,
) -> str:
    """Return redacted diagnostic text capped by bytes and lines."""
    if max_bytes <= 0:
        raise FirstAdoptionCheckError("--doctor-max-bytes must be greater than zero.")
    if max_lines <= 0:
        raise FirstAdoptionCheckError("--doctor-max-lines must be greater than zero.")

    bounded = redact_diagnostic_text(value)
    markers: list[str] = []
    encoded = bounded.encode("utf-8")
    if len(encoded) > max_bytes:
        bounded = encoded[:max_bytes].decode("utf-8", errors="ignore")
        markers.append(f"[truncated: byte limit {max_bytes} bytes]")

    lines = bounded.splitlines()
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        markers.append(f"[truncated: line limit {max_lines} lines]")

    rendered = "\n".join(lines)
    if markers:
        rendered = "\n".join(part for part in (rendered, *markers) if part)
    return rendered


def command_succeeds(
    command: Sequence[str],
    *,
    timeout_seconds: float = 5.0,
) -> bool:
    """Return whether a small command executes successfully."""
    try:
        result = subprocess.run(
            list(command),
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout_seconds,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def decode_timeout_stream(value: bytes | str | None) -> str:
    """Decode optional timeout output captured by ``subprocess``."""
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def execute_probe_command(
    command: Sequence[str],
    repo_root: Path,
    timeout_seconds: float,
) -> ProbeExecution:
    """Run one non-mutating doctor probe command and capture its diagnostics."""
    result = subprocess.run(
        list(command),
        cwd=repo_root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_seconds,
    )
    return ProbeExecution(
        return_code=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )


def python_module_invocation_forms() -> tuple[tuple[str, ...], ...]:
    """Return candidate Python module invocation prefixes."""
    forms = (
        (sys.executable, "-m"),
        ("python", "-m"),
        ("python3", "-m"),
        ("py", "-m"),
    )
    unique_forms: list[tuple[str, ...]] = []
    for form in forms:
        if form not in unique_forms:
            unique_forms.append(form)
    return tuple(unique_forms)


def python_form_display_name(form: Sequence[str]) -> str:
    """Return a stable display name for a Python module invocation prefix."""
    executable = form[0]
    if executable == sys.executable:
        return "sys.executable -m"
    return f"{executable} -m"


def probe_availability_state(execution: ProbeExecution) -> str:
    """Return the doctor availability state represented by a raw execution."""
    if execution.timed_out:
        return PROBE_TIMED_OUT
    if execution.return_code == 0:
        return PROBE_AVAILABLE
    return PROBE_FAILED


def run_doctor_probe(
    probe: DoctorProbe,
    *,
    repo_root: Path,
    timeout_seconds: float,
    max_output_bytes: int,
    max_output_lines: int,
    probe_executor: ProbeExecutor,
    time_source: TimeSource,
) -> DoctorProbeResult:
    """Run one doctor probe and return a bounded diagnostic result."""
    if timeout_seconds <= 0:
        raise FirstAdoptionCheckError("--doctor-timeout must be greater than zero.")

    started_at = time_source()
    try:
        execution = probe_executor(probe.command, repo_root, timeout_seconds)
    except subprocess.TimeoutExpired as error:
        stdout = decode_timeout_stream(error.stdout)
        stderr = decode_timeout_stream(error.stderr)
        timeout_message = f"Timed out after {timeout_seconds:.3f}s."
        stderr = "\n".join(part for part in (stderr, timeout_message) if part)
        execution = ProbeExecution(
            return_code=None,
            stdout=stdout,
            stderr=stderr,
            timed_out=True,
        )
        availability_state = PROBE_TIMED_OUT
    except OSError as error:
        error_summary = f"{type(error).__name__}: {error.strerror or 'I/O error'}"
        execution = ProbeExecution(
            return_code=None,
            stdout="",
            stderr=error_summary,
        )
        availability_state = PROBE_UNAVAILABLE
    else:
        availability_state = probe_availability_state(execution)
    ended_at = time_source()

    return DoctorProbeResult(
        group_label=probe.group_label,
        name=probe.name,
        command=tuple(probe.command),
        availability_state=availability_state,
        exit_code=execution.return_code,
        elapsed_time=format_elapsed_time(started_at, ended_at),
        timed_out=execution.timed_out,
        stdout=bound_diagnostic_text(
            execution.stdout,
            max_bytes=max_output_bytes,
            max_lines=max_output_lines,
        ),
        stderr=bound_diagnostic_text(
            execution.stderr,
            max_bytes=max_output_bytes,
            max_lines=max_output_lines,
        ),
        note=probe.note,
    )


def run_external_command(command: Sequence[str], repo_root: Path) -> int:
    """Run one external command in the repository root."""
    try:
        result = subprocess.run(list(command), cwd=repo_root, check=False)
    except OSError as error:
        error_summary = f"{type(error).__name__}: {error.strerror or 'I/O error'}"
        raise FirstAdoptionCheckError(f"Unable to run {command[0]} ({error_summary}).") from error
    return result.returncode


def git_status_lines(repo_root: Path) -> tuple[str, ...]:
    """Return a deterministic Git status snapshot for changed-file reporting."""
    try:
        result = subprocess.run(
            list(GIT_STATUS_COMMAND),
            cwd=repo_root,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except OSError as error:
        error_summary = f"{type(error).__name__}: {error.strerror or 'I/O error'}"
        raise FirstAdoptionCheckError(
            f"Unable to inspect Git changed files ({error_summary})."
        ) from error
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "git status failed"
        raise FirstAdoptionCheckError(f"Unable to inspect Git changed files: {message}")
    return tuple(sorted(line for line in result.stdout.splitlines() if line.strip()))


def collect_present_regular_files(
    repo_root: Path,
    *,
    stdout: TextIO | None = None,
) -> FileCollection:
    """Collect tracked and untracked non-ignored regular files from Git."""
    if stdout is not None:
        print(f"$ {format_command(GIT_FILE_LIST_COMMAND)}", file=stdout, flush=True)

    try:
        result = subprocess.run(
            list(GIT_FILE_LIST_COMMAND),
            cwd=repo_root,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except OSError as error:
        error_summary = f"{type(error).__name__}: {error.strerror or 'I/O error'}"
        raise FirstAdoptionCheckError(
            f"Unable to inspect Git-visible files ({error_summary})."
        ) from error
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
    if shutil.which("pre-commit") is not None and command_succeeds(("pre-commit", "--version")):
        return PRE_COMMIT_EXECUTABLE_PREFIX
    for python_form in python_module_invocation_forms():
        if command_succeeds((*python_form, "pre_commit", "--version")):
            return (*python_form, "pre_commit", "run", "--files")
    return (sys.executable, "-m", "pre_commit", "run", "--files")


def default_npm_executable() -> str:
    """Return an npm executable name or path suitable for direct subprocess use."""
    return shutil.which("npm") or shutil.which("npm.cmd") or "npm"


def build_doctor_probes(repo_root: Path) -> tuple[DoctorProbe, ...]:
    """Build the first-adoption doctor probe inventory."""
    del repo_root
    probes: list[DoctorProbe] = [
        DoctorProbe(
            group_label="git",
            name="Git executable",
            command=("git", "--version"),
        ),
    ]

    for python_form in python_module_invocation_forms():
        probes.append(
            DoctorProbe(
                group_label="python",
                name=f"Python module invocation ({python_form_display_name(python_form)})",
                command=(*python_form, PYTHON_DOCTOR_MODULE),
            )
        )

    probes.append(
        DoctorProbe(
            group_label=PRE_COMMIT_GROUP,
            name="pre-commit console",
            command=("pre-commit", "--version"),
        )
    )
    for python_form in python_module_invocation_forms():
        probes.append(
            DoctorProbe(
                group_label=PRE_COMMIT_GROUP,
                name=f"pre_commit module ({python_form_display_name(python_form)})",
                command=(*python_form, "pre_commit", "--version"),
            )
        )

    probes.append(
        DoctorProbe(
            group_label="pytest",
            name="pytest console",
            command=("pytest", "--version"),
        )
    )
    for python_form in python_module_invocation_forms():
        probes.append(
            DoctorProbe(
                group_label="pytest",
                name=f"pytest module ({python_form_display_name(python_form)})",
                command=(*python_form, "pytest", "--version"),
            )
        )

    probes.extend(
        (
            DoctorProbe(
                group_label="node",
                name="Node.js executable",
                command=("node", "--version"),
            ),
            DoctorProbe(
                group_label="npm",
                name="npm executable",
                command=(default_npm_executable(), "--version"),
            ),
        )
    )

    probes.append(
        DoctorProbe(
            group_label="yamllint",
            name="yamllint console",
            command=("yamllint", "--version"),
        )
    )
    for python_form in python_module_invocation_forms():
        probes.append(
            DoctorProbe(
                group_label="yamllint",
                name=f"yamllint module ({python_form_display_name(python_form)})",
                command=(*python_form, "yamllint", "--version"),
            )
        )

    for powershell_host in ("pwsh", "powershell"):
        probes.extend(
            (
                DoctorProbe(
                    group_label="powershell",
                    name=f"PowerShell host ({powershell_host})",
                    command=(
                        powershell_host,
                        *POWERSHELL_PROBE_FLAGS,
                        POWERSHELL_VERSION_PROBE,
                    ),
                ),
                DoctorProbe(
                    group_label="PSScriptAnalyzer",
                    name=f"PSScriptAnalyzer module ({powershell_host})",
                    command=(
                        powershell_host,
                        *POWERSHELL_PROBE_FLAGS,
                        PSSCRIPTANALYZER_PROBE,
                    ),
                    note=(
                        "PSScriptAnalyzer is checked inside this PowerShell host; "
                        "module availability is not shared across hosts."
                    ),
                ),
            )
        )

    return tuple(probes)


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
        package_data = json.loads(package_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as error:
        raise FirstAdoptionCheckError(f"package.json is not valid JSON: {error}") from error
    except OSError as error:
        error_summary = f"{type(error).__name__}: {error.strerror or 'I/O error'}"
        raise FirstAdoptionCheckError(f"Unable to read package.json ({error_summary}).") from error

    scripts = package_data.get("scripts") if isinstance(package_data, dict) else None
    return scripts if isinstance(scripts, dict) else {}


def included_modules_from_marker_text(marker_text: str) -> frozenset[str]:
    """Return modules listed under the marker's ``included_modules`` block.

    Only the ``included_modules`` block is scanned. The block is located by its
    key line and bounded by indentation so sibling marker string lists (for
    example ``issue_labels``) are never read as retained modules, even when a
    downstream label happens to match a module name. Block sequence items are
    accepted both when indented beneath the key and when rendered at the key's
    own indentation, matching PyYAML's default ``safe_dump`` block style. Blank
    lines and full-line comments inside the block are skipped rather than
    treated as block terminators, so hand-edited markers parse correctly.
    """
    modules: set[str] = set()
    in_block = False
    block_indent = 0
    for line in marker_text.splitlines():
        if not in_block:
            key_match = INCLUDED_MODULES_KEY_PATTERN.match(line)
            if key_match is not None:
                in_block = True
                block_indent = len(key_match.group("indent"))
            continue
        if is_marker_blank_or_comment_line(line):
            # Blank lines and full-line comments are structurally transparent in
            # YAML; skip them so a comment at the block indentation does not
            # prematurely terminate the included_modules block.
            continue
        item_match = MARKER_MODULE_PATTERN.match(line)
        if item_match is None and len(line) - len(line.lstrip()) <= block_indent:
            break
        if item_match is not None:
            modules.add(item_match.group("module"))
    return frozenset(modules)


def marker_line_indent(line: str) -> int:
    """Return the number of leading spaces on ``line``."""
    return len(line) - len(line.lstrip(" "))


def is_marker_blank_or_comment_line(line: str) -> bool:
    """Return whether ``line`` is blank or a full-line marker comment."""
    stripped_line = line.strip()
    return not stripped_line or stripped_line.startswith("#")


def parse_marker_key_line(line: str) -> tuple[int, str, str] | None:
    """Return a simple marker key line as ``(indent, key, suffix)``."""
    match = MARKER_KEY_PATTERN.fullmatch(line)
    if match is None:
        return None
    return len(match.group("indent")), match.group("key"), match.group("suffix")


def is_empty_or_comment_key_suffix(suffix: str) -> bool:
    """Return whether a key suffix is empty or only a whitespace-separated comment."""
    if suffix.strip() == "":
        return True
    return suffix[0] in " \t" and suffix.lstrip(" \t").startswith("#")


def is_exact_empty_list_key_suffix(suffix: str) -> bool:
    """Return whether a key suffix is exactly ``[]`` with an optional comment."""
    if not suffix or suffix[0] not in " \t":
        return False
    value = suffix.lstrip(" \t")
    if not value.startswith("[]"):
        return False
    tail = value[2:]
    return tail.strip() == "" or (tail[0] in " \t" and tail.lstrip(" \t").startswith("#"))


def is_marker_block_key(line: str, key: str, *, indent: int | None = None) -> bool:
    """Return whether ``line`` is a simple block-style marker key."""
    parsed_line = parse_marker_key_line(line)
    if parsed_line is None:
        return False
    line_indent, line_key, suffix = parsed_line
    if indent is not None and line_indent != indent:
        return False
    return line_key == key and is_empty_or_comment_key_suffix(suffix)


def included_modules_key_kind(line: str, child_indent: int) -> str | None:
    """Return the recognized direct-child ``included_modules`` key shape."""
    parsed_line = parse_marker_key_line(line)
    if parsed_line is None:
        return None
    line_indent, key, suffix = parsed_line
    if line_indent != child_indent or key != "included_modules":
        return None
    if is_empty_or_comment_key_suffix(suffix):
        return "block"
    if is_exact_empty_list_key_suffix(suffix):
        return "empty"
    return None


def template_sync_child_indent(marker_lines: Sequence[str], start_index: int) -> int | None:
    """Return the direct-child indentation under top-level ``template_sync``."""
    for line in marker_lines[start_index:]:
        if is_marker_blank_or_comment_line(line):
            continue
        line_indent = marker_line_indent(line)
        if line_indent == 0:
            return None
        parsed_line = parse_marker_key_line(line)
        if parsed_line is not None:
            return parsed_line[0]
    return None


def included_modules_block_includes_markdown(
    marker_lines: Sequence[str],
    start_index: int,
    included_modules_indent: int,
) -> bool:
    """Return whether a scoped ``included_modules`` block contains ``markdown``."""
    sequence_indent: int | None = None
    sequence_blocked = False
    for line in marker_lines[start_index:]:
        if is_marker_blank_or_comment_line(line):
            continue

        line_indent = marker_line_indent(line)
        stripped_line = line[line_indent:]
        if line_indent < included_modules_indent:
            break
        if line_indent == included_modules_indent and parse_marker_key_line(line):
            break
        if stripped_line.startswith("-"):
            if sequence_blocked:
                continue
            if sequence_indent is None:
                sequence_indent = line_indent
            if line_indent == sequence_indent and MARKDOWN_MODULE_ITEM_PATTERN.fullmatch(line):
                return True
            continue
        if sequence_indent is None:
            sequence_blocked = True
    return False


def template_sync_block_includes_markdown(
    marker_lines: Sequence[str],
    start_index: int,
) -> bool:
    """Return whether top-level ``template_sync.included_modules`` has ``markdown``."""
    child_indent = template_sync_child_indent(marker_lines, start_index)
    if child_indent is None:
        return False

    for line_index, line in enumerate(marker_lines[start_index:], start=start_index):
        if is_marker_blank_or_comment_line(line):
            continue
        line_indent = marker_line_indent(line)
        if line_indent == 0:
            break
        if line_indent != child_indent:
            continue

        key_kind = included_modules_key_kind(line, child_indent)
        if key_kind == "empty":
            return False
        if key_kind == "block":
            return included_modules_block_includes_markdown(
                marker_lines,
                line_index + 1,
                child_indent,
            )
    return False


def marker_text_includes_markdown_module(marker_text: str) -> bool:
    """Return whether marker text retains ``template_sync.included_modules`` markdown."""
    marker_lines = marker_text.splitlines()
    for line_index, line in enumerate(marker_lines):
        if is_marker_block_key(line, "template_sync", indent=0) and (
            template_sync_block_includes_markdown(marker_lines, line_index + 1)
        ):
            return True
    return False


def marker_included_modules(repo_root: Path) -> frozenset[str] | None:
    """Return marker-listed modules, or ``None`` when no marker is present."""
    marker_path = repo_root / MARKER_PATH
    if not marker_path.exists():
        return None
    if not is_present_regular_file(marker_path):
        raise FirstAdoptionCheckError(f"Expected a regular file: {MARKER_PATH}")
    try:
        marker_text = marker_path.read_text(encoding="utf-8-sig")
    except OSError as error:
        error_summary = f"{type(error).__name__}: {error.strerror or 'I/O error'}"
        raise FirstAdoptionCheckError(f"Unable to read {MARKER_PATH} ({error_summary}).") from error
    return included_modules_from_marker_text(marker_text)


def marker_includes_markdown_module(repo_root: Path) -> bool:
    """Return whether the downstream marker appears to retain the markdown module."""
    marker_path = repo_root / MARKER_PATH
    if not marker_path.exists():
        return False
    if not is_present_regular_file(marker_path):
        raise FirstAdoptionCheckError(f"Expected a regular file: {MARKER_PATH}")
    try:
        marker_text = marker_path.read_text(encoding="utf-8-sig")
    except OSError as error:
        error_summary = f"{type(error).__name__}: {error.strerror or 'I/O error'}"
        raise FirstAdoptionCheckError(f"Unable to read {MARKER_PATH} ({error_summary}).") from error
    return marker_text_includes_markdown_module(marker_text)


def has_powershell_files(files: Sequence[str]) -> bool:
    """Return whether collected files include PowerShell-owned extensions."""
    return any(
        Path(relative_path).suffix.casefold() in {".ps1", ".psd1", ".psm1"}
        for relative_path in files
    )


def markdown_commands_and_notes(repo_root: Path) -> CheckPlan:
    """Build optional Markdown npm commands and any explanatory notes."""
    package_scripts = load_package_scripts(repo_root)
    commands = tuple(
        PlannedCommand(
            group_label=MARKDOWN_SCRIPT_GROUP,
            command=(default_npm_executable(), "run", script_name),
        )
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


def quality_report_commands(
    repo_root: Path,
    files: Sequence[str],
    *,
    run_mode: str = CHECK_MODE,
) -> tuple[PlannedCommand, ...]:
    """Build first-adoption quality report commands when the helper is available."""
    if not optional_regular_file_exists(repo_root, QUALITY_REPORT_SCRIPT):
        return ()

    marker_modules = marker_included_modules(repo_root)
    commands = [
        PlannedCommand(
            group_label=QUALITY_REPORT_GROUP,
            command=(sys.executable, QUALITY_REPORT_SCRIPT, "line-endings"),
        ),
        PlannedCommand(
            group_label=QUALITY_REPORT_GROUP,
            command=(sys.executable, QUALITY_REPORT_SCRIPT, "path-references"),
        ),
    ]
    if marker_modules is not None and marker_modules & AZURE_DEVOPS_MODULES:
        commands.append(
            PlannedCommand(
                group_label=QUALITY_REPORT_GROUP,
                command=(sys.executable, QUALITY_REPORT_SCRIPT, "host-setup"),
            )
        )
    if marker_modules is None or "powershell" in marker_modules or has_powershell_files(files):
        commands.append(
            PlannedCommand(
                group_label=QUALITY_REPORT_GROUP,
                command=(sys.executable, QUALITY_REPORT_SCRIPT, "powershell"),
            )
        )

    markdown_command = [sys.executable, QUALITY_REPORT_SCRIPT, "markdown"]
    group_label = QUALITY_REPORT_GROUP
    if run_mode == FIX_MODE:
        markdown_command.append("--fix")
        group_label = MARKDOWN_FIXER_GROUP

    commands.append(
        PlannedCommand(
            group_label=group_label,
            command=tuple(markdown_command),
        )
    )
    return tuple(commands)


def build_check_plan(
    repo_root: Path,
    files: Sequence[str],
    *,
    max_command_length: int = DEFAULT_MAX_COMMAND_LENGTH,
    run_mode: str = CHECK_MODE,
) -> CheckPlan:
    """Build the first-adoption check command plan."""
    commands: list[PlannedCommand] = []
    notes: list[str] = []

    commands.extend(quality_report_commands(repo_root, files, run_mode=run_mode))

    if files:
        commands.extend(
            PlannedCommand(group_label=PRE_COMMIT_GROUP, command=command)
            for command in pre_commit_commands(
                files,
                max_command_length=max_command_length,
            )
        )
    else:
        notes.append(
            "No tracked or untracked non-ignored regular files found; "
            "skipping pre-commit --files."
        )

    if optional_regular_file_exists(repo_root, PLACEHOLDER_SCRIPT):
        commands.append(
            PlannedCommand(
                group_label=PLACEHOLDER_SCAN_GROUP,
                command=(sys.executable, PLACEHOLDER_SCRIPT, "scan"),
            )
        )

    if optional_regular_file_exists(repo_root, MARKER_PATH):
        require_regular_script(repo_root, MARKER_VALIDATOR_SCRIPT)
        commands.append(
            PlannedCommand(
                group_label=MARKER_VALIDATION_GROUP,
                command=(sys.executable, MARKER_VALIDATOR_SCRIPT, "--require-marker"),
            )
        )

    markdown_plan = markdown_commands_and_notes(repo_root)
    commands.extend(markdown_plan.commands)
    notes.extend(markdown_plan.notes)

    return CheckPlan(commands=tuple(commands), notes=tuple(notes))


def print_file_collection(
    collection: FileCollection,
    *,
    stdout: TextIO,
    include_files: bool,
) -> None:
    """Print a deterministic summary of Git-visible file discovery."""
    print(
        f"Collected {len(collection.files)} tracked or untracked non-ignored regular file(s).",
        file=stdout,
        flush=True,
    )
    if include_files and collection.files:
        print("Git-visible regular file(s):", file=stdout, flush=True)
        for relative_path in collection.files:
            print(f"  - {relative_path}", file=stdout, flush=True)

    if collection.skipped_non_regular_paths:
        print("Skipped non-regular Git-visible path(s):", file=stdout, flush=True)
        for relative_path in collection.skipped_non_regular_paths:
            print(f"  - {relative_path}", file=stdout, flush=True)


def print_check_plan(plan: CheckPlan, *, stdout: TextIO) -> None:
    """Print the numbered command plan before validation starts."""
    print(
        f"Planned validation commands ({len(plan.commands)}):",
        file=stdout,
        flush=True,
    )
    for index, planned_command in enumerate(plan.commands, start=1):
        print(
            f"  {index}. [{planned_command.group_label}] "
            f"{format_command(planned_command.command)}",
            file=stdout,
            flush=True,
        )


def print_total_elapsed_time(
    started_at: datetime,
    ended_at: datetime,
    *,
    stdout: TextIO,
) -> None:
    """Print total elapsed time for this run."""
    print(
        f"Total elapsed time: {format_elapsed_time(started_at, ended_at)}",
        file=stdout,
        flush=True,
    )


def print_indented_diagnostic(value: str, *, stdout: TextIO) -> None:
    """Print a bounded stdout/stderr diagnostic block."""
    if not value:
        print("    <empty>", file=stdout, flush=True)
        return
    for line in value.splitlines():
        print(f"    {line}", file=stdout, flush=True)


def print_doctor_probe_results(
    results: Sequence[DoctorProbeResult],
    *,
    stdout: TextIO,
) -> None:
    """Print doctor probe results with stable fields."""
    print(f"Doctor probes executed ({len(results)}):", file=stdout, flush=True)
    for index, result in enumerate(results, start=1):
        exit_code = "<none>" if result.exit_code is None else str(result.exit_code)
        timed_out = "yes" if result.timed_out else "no"
        print(f"  {index}. [{result.group_label}] {result.name}", file=stdout, flush=True)
        print(f"     Command: {format_command(result.command)}", file=stdout, flush=True)
        print(f"     Availability: {result.availability_state}", file=stdout, flush=True)
        print(f"     Exit code: {exit_code}", file=stdout, flush=True)
        print(f"     Timed out: {timed_out}", file=stdout, flush=True)
        print(f"     Elapsed time: {result.elapsed_time}", file=stdout, flush=True)
        if result.note:
            print(f"     Note: {result.note}", file=stdout, flush=True)
        print("     stdout:", file=stdout, flush=True)
        print_indented_diagnostic(result.stdout, stdout=stdout)
        print("     stderr:", file=stdout, flush=True)
        print_indented_diagnostic(result.stderr, stdout=stdout)


def pre_commit_managed_hook_ids(repo_root: Path) -> tuple[str, ...]:
    """Return hook IDs declared in the pre-commit config, best effort."""
    config_path = repo_root / PRE_COMMIT_CONFIG_PATH
    if not config_path.exists():
        return ()
    if not is_present_regular_file(config_path):
        raise FirstAdoptionCheckError(f"Expected a regular file: {PRE_COMMIT_CONFIG_PATH}")
    try:
        config_text = config_path.read_text(encoding="utf-8-sig")
    except OSError as error:
        error_summary = f"{type(error).__name__}: {error.strerror or 'I/O error'}"
        raise FirstAdoptionCheckError(
            f"Unable to read {PRE_COMMIT_CONFIG_PATH} ({error_summary})."
        ) from error

    hook_ids: list[str] = []
    for line in config_text.splitlines():
        match = PRE_COMMIT_HOOK_ID_PATTERN.match(line)
        if match is not None:
            hook_ids.append(match.group("id"))
    return tuple(hook_ids)


def print_pre_commit_managed_hook_notes(repo_root: Path, *, stdout: TextIO) -> None:
    """Print doctor notes for hooks intentionally left to pre-commit."""
    hook_ids = pre_commit_managed_hook_ids(repo_root)
    print("Pre-commit-managed hook note:", file=stdout, flush=True)
    print(
        "  Doctor mode does not run pre-commit hooks or direct-probe every hook "
        "entrypoint. pre-commit creates language-specific hook environments; "
        "--check and --fix remain the surfaces for actual hook execution.",
        file=stdout,
        flush=True,
    )
    if not hook_ids:
        print(f"  No hook IDs were detected in {PRE_COMMIT_CONFIG_PATH}.", file=stdout, flush=True)
        return
    print(f"  Hook IDs detected in {PRE_COMMIT_CONFIG_PATH}:", file=stdout, flush=True)
    for hook_id in hook_ids:
        print(f"    - {hook_id}", file=stdout, flush=True)


def result_command_ends_with(result: DoctorProbeResult, suffix: Sequence[str]) -> bool:
    """Return whether a probe command ends with ``suffix``."""
    return len(result.command) >= len(suffix) and tuple(result.command[-len(suffix) :]) == tuple(
        suffix
    )


def first_available_result(
    results: Sequence[DoctorProbeResult],
    group_label: str,
    *,
    command_suffix: Sequence[str] | None = None,
) -> DoctorProbeResult | None:
    """Return the first available result in a group, optionally by command suffix."""
    for result in results:
        if result.group_label != group_label or result.availability_state != PROBE_AVAILABLE:
            continue
        if command_suffix is not None and not result_command_ends_with(result, command_suffix):
            continue
        return result
    return None


def doctor_recommendations(results: Sequence[DoctorProbeResult]) -> tuple[str, ...]:
    """Return concise recommendations from doctor probe results."""
    recommendations: list[str] = []

    pre_commit_console = first_available_result(
        results,
        PRE_COMMIT_GROUP,
        command_suffix=("--version",),
    )
    if pre_commit_console is not None and pre_commit_console.command[0] == "pre-commit":
        recommendations.append(
            "Use pre-commit validation prefix: " f"{format_command(PRE_COMMIT_EXECUTABLE_PREFIX)}"
        )
    else:
        pre_commit_module = first_available_result(
            results,
            PRE_COMMIT_GROUP,
            command_suffix=("pre_commit", "--version"),
        )
        if pre_commit_module is None:
            recommendations.append(
                "No working pre-commit invocation was detected; install pre-commit "
                "in an available Python environment before --check or --fix."
            )
        else:
            prefix = (*pre_commit_module.command[:-2], "pre_commit", "run", "--files")
            recommendations.append(f"Use pre-commit validation prefix: {format_command(prefix)}")

    pytest_console = first_available_result(results, "pytest", command_suffix=("--version",))
    if pytest_console is not None and pytest_console.command[0] == "pytest":
        recommendations.append("Use pytest invocation: pytest")
    else:
        pytest_module = first_available_result(
            results,
            "pytest",
            command_suffix=("pytest", "--version"),
        )
        if pytest_module is not None:
            recommendations.append(
                f"Use pytest invocation: {format_command((*pytest_module.command[:-1],))}"
            )

    yamllint_console = first_available_result(results, "yamllint", command_suffix=("--version",))
    if yamllint_console is not None and yamllint_console.command[0] == "yamllint":
        recommendations.append("Use yamllint invocation: yamllint")
    else:
        yamllint_module = first_available_result(
            results,
            "yamllint",
            command_suffix=("yamllint", "--version"),
        )
        if yamllint_module is None:
            recommendations.append(
                "yamllint was not directly available; if the YAML module is retained, "
                "let pre-commit manage the yamllint hook environment or install "
                "yamllint locally for direct use."
            )
        else:
            recommendations.append(
                "Use yamllint invocation: " f"{format_command((*yamllint_module.command[:-1],))}"
            )

    pssa_result = first_available_result(results, "PSScriptAnalyzer")
    if pssa_result is None:
        recommendations.append(
            "No PowerShell host with PSScriptAnalyzer was detected; install the "
            "module in the intended host before running PowerShell analyzer checks."
        )
    else:
        recommendations.append(f"Use PSScriptAnalyzer host: {pssa_result.command[0]}")

    return tuple(recommendations)


def print_doctor_recommendations(
    results: Sequence[DoctorProbeResult],
    *,
    stdout: TextIO,
) -> None:
    """Print recommended invocation forms from successful doctor probes."""
    print("Doctor recommendations:", file=stdout, flush=True)
    for recommendation in doctor_recommendations(results):
        print(f"  - {recommendation}", file=stdout, flush=True)


def print_status_entries(status_lines: Sequence[str], *, stdout: TextIO) -> None:
    """Print one Git status snapshot as a deterministic bullet list."""
    if not status_lines:
        print("    - <none>", file=stdout, flush=True)
        return
    for status_line in status_lines:
        print(f"    - {status_line}", file=stdout, flush=True)


def print_changed_file_summary(
    before_status: Sequence[str],
    after_status: Sequence[str],
    *,
    run_mode: str = CHECK_MODE,
    stdout: TextIO,
) -> bool:
    """Print changed-file status before/after the invocation and return if it changed."""
    print("Git changed-file summary:", file=stdout, flush=True)
    if tuple(before_status) == tuple(after_status):
        print(
            "  No Git status changes were detected during this invocation.",
            file=stdout,
            flush=True,
        )
        return False

    print("  Before invocation:", file=stdout, flush=True)
    print_status_entries(before_status, stdout=stdout)
    print("  After invocation:", file=stdout, flush=True)
    print_status_entries(after_status, stdout=stdout)
    if run_mode == FIX_MODE:
        print(
            "Files changed during this invocation as intended by fix mode. Inspect "
            "the changes, keep or discard them intentionally, then rerun with --check.",
            file=stdout,
            flush=True,
        )
    else:
        print(
            "Files changed during this invocation. Inspect the changes and keep or "
            "discard them intentionally. To intentionally allow mutating hooks or "
            "fixers to apply these edits, rerun with --fix, then rerun with --check.",
            file=stdout,
            flush=True,
        )
    return True


def run_planned_command(
    planned_command: PlannedCommand,
    *,
    index: int,
    total: int,
    repo_root: Path,
    command_runner: CommandRunner,
    time_source: TimeSource,
    stdout: TextIO,
) -> int:
    """Run one planned validation command with deterministic timing output."""
    started_at = time_source()
    print(
        f"Command {index}/{total} [{planned_command.group_label}] "
        f"start time (UTC): {format_utc_timestamp(started_at)}",
        file=stdout,
        flush=True,
    )
    print(f"$ {format_command(planned_command.command)}", file=stdout, flush=True)
    return_code = command_runner(planned_command.command, repo_root)
    ended_at = time_source()
    print(
        f"Command {index}/{total} [{planned_command.group_label}] "
        f"completed with exit code {return_code}",
        file=stdout,
        flush=True,
    )
    print(
        f"Command {index}/{total} [{planned_command.group_label}] "
        f"end time (UTC): {format_utc_timestamp(ended_at)}",
        file=stdout,
        flush=True,
    )
    print(
        f"Command {index}/{total} [{planned_command.group_label}] "
        f"elapsed time: {format_elapsed_time(started_at, ended_at)}",
        file=stdout,
        flush=True,
    )
    return return_code


def run_first_adoption_doctor(
    repo_root: Path,
    *,
    probe_timeout_seconds: float = DEFAULT_PROBE_TIMEOUT_SECONDS,
    max_output_bytes: int = DEFAULT_DIAGNOSTIC_MAX_BYTES,
    max_output_lines: int = DEFAULT_DIAGNOSTIC_MAX_LINES,
    probe_executor: ProbeExecutor = execute_probe_command,
    time_source: TimeSource = default_time_source,
    stdout: TextIO = sys.stdout,
) -> int:
    """Run non-mutating first-adoption environment probes."""
    run_started_at = time_source()
    print("Run mode: doctor", file=stdout, flush=True)
    print(
        "Doctor mode runs small non-mutating environment/tool probes only. It does "
        "not run validation hooks, fixers, generated validation commands, or "
        "repository-setting changes.",
        file=stdout,
        flush=True,
    )
    print(
        f"Probe timeout: {probe_timeout_seconds:.3f}s; diagnostic caps: "
        f"{max_output_bytes} bytes and {max_output_lines} lines per stream.",
        file=stdout,
        flush=True,
    )

    results = tuple(
        run_doctor_probe(
            probe,
            repo_root=repo_root,
            timeout_seconds=probe_timeout_seconds,
            max_output_bytes=max_output_bytes,
            max_output_lines=max_output_lines,
            probe_executor=probe_executor,
            time_source=time_source,
        )
        for probe in build_doctor_probes(repo_root)
    )
    print_doctor_probe_results(results, stdout=stdout)
    print_pre_commit_managed_hook_notes(repo_root, stdout=stdout)
    print_doctor_recommendations(results, stdout=stdout)
    print_total_elapsed_time(run_started_at, time_source(), stdout=stdout)
    return 0


def run_first_adoption_checks(
    repo_root: Path,
    *,
    max_command_length: int = DEFAULT_MAX_COMMAND_LENGTH,
    run_mode: str = CHECK_MODE,
    plan_only: bool = False,
    command_runner: CommandRunner = run_external_command,
    git_status_reader: GitStatusReader = git_status_lines,
    time_source: TimeSource = default_time_source,
    stdout: TextIO = sys.stdout,
) -> int:
    """Run first-adoption checks and return a process exit code."""
    if run_mode not in (CHECK_MODE, FIX_MODE):
        raise FirstAdoptionCheckError(f"Unsupported run mode: {run_mode}")

    run_started_at = time_source()
    print(f"Run mode: {run_mode}", file=stdout, flush=True)
    before_status = git_status_reader(repo_root)
    collection = collect_present_regular_files(repo_root, stdout=stdout)
    print_file_collection(collection, stdout=stdout, include_files=plan_only)

    plan = build_check_plan(
        repo_root=repo_root,
        files=collection.files,
        max_command_length=max_command_length,
        run_mode=run_mode,
    )
    for note in plan.notes:
        print(note, file=stdout, flush=True)
    print_check_plan(plan, stdout=stdout)

    if not plan.commands:
        print("No first-adoption checks were available to run.", file=stdout, flush=True)
        after_status = git_status_reader(repo_root)
        status_changed = print_changed_file_summary(
            before_status,
            after_status,
            run_mode=run_mode,
            stdout=stdout,
        )
        print_total_elapsed_time(run_started_at, time_source(), stdout=stdout)
        return CHANGED_FILES_EXIT_CODE if status_changed and run_mode == CHECK_MODE else 0

    if plan_only:
        print("Plan-only mode: validation commands were not run.", file=stdout, flush=True)
        after_status = git_status_reader(repo_root)
        status_changed = print_changed_file_summary(
            before_status,
            after_status,
            run_mode=run_mode,
            stdout=stdout,
        )
        print_total_elapsed_time(run_started_at, time_source(), stdout=stdout)
        return CHANGED_FILES_EXIT_CODE if status_changed and run_mode == CHECK_MODE else 0

    failures: list[str] = []
    total_commands = len(plan.commands)
    cold_start_guidance_printed = False
    for index, planned_command in enumerate(plan.commands, start=1):
        if planned_command.group_label == PRE_COMMIT_GROUP and not cold_start_guidance_printed:
            print(
                "Cold pre-commit hook environment bootstrapping may take several "
                "minutes on a fresh checkout; the helper will keep reporting "
                "command timing as each planned command completes.",
                file=stdout,
                flush=True,
            )
            cold_start_guidance_printed = True
        return_code = run_planned_command(
            planned_command,
            index=index,
            total=total_commands,
            repo_root=repo_root,
            command_runner=command_runner,
            time_source=time_source,
            stdout=stdout,
        )
        if return_code != 0:
            failures.append(
                f"{planned_command.group_label}: "
                f"{format_command(planned_command.command)} exited with {return_code}"
            )

    after_status = git_status_reader(repo_root)
    status_changed = print_changed_file_summary(
        before_status,
        after_status,
        run_mode=run_mode,
        stdout=stdout,
    )
    if failures:
        print("First-adoption checks failed:", file=stdout, flush=True)
        for failure in failures:
            print(f"  - {failure}", file=stdout, flush=True)
        print_total_elapsed_time(run_started_at, time_source(), stdout=stdout)
        return 1

    if status_changed and run_mode == CHECK_MODE:
        print_total_elapsed_time(run_started_at, time_source(), stdout=stdout)
        return CHANGED_FILES_EXIT_CODE

    print_total_elapsed_time(run_started_at, time_source(), stdout=stdout)
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
        if args.run_mode == DOCTOR_MODE:
            if args.plan_only:
                raise FirstAdoptionCheckError("--plan-only cannot be combined with --doctor.")
            return run_first_adoption_doctor(
                repo_root,
                probe_timeout_seconds=args.doctor_timeout,
                max_output_bytes=args.doctor_max_bytes,
                max_output_lines=args.doctor_max_lines,
            )
        return run_first_adoption_checks(
            repo_root,
            max_command_length=args.max_command_length,
            run_mode=args.run_mode,
            plan_only=args.plan_only,
        )
    except FirstAdoptionCheckError as error:
        fail(str(error))


if __name__ == "__main__":
    raise SystemExit(main())
