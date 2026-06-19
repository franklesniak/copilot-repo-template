"""Report first-adoption quality debt without mutating repository files."""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import NoReturn, Protocol, TextIO

import yaml  # type: ignore[import-untyped]

DEFAULT_SUPPRESSION_PATH = ".template-sync/first-adoption/quality-suppressions.json"
MARKER_PATH = ".template-sync/marker.yml"
GIT_VISIBLE_FILES_COMMAND = (
    "git",
    "ls-files",
    "-z",
    "--cached",
    "--others",
    "--exclude-standard",
)
GIT_TRACKED_FILES_COMMAND = ("git", "ls-files", "-z", "--cached")
GIT_IGNORED_FILES_COMMAND = (
    "git",
    "ls-files",
    "-z",
    "--others",
    "--ignored",
    "--exclude-standard",
)
PATH_REFERENCE_CATEGORY = "path-reference"
PATH_REFERENCE_CASE_MISMATCH_RULE = "path-reference.case-mismatch"
PATH_REFERENCE_MISSING_TARGET_RULE = "path-reference.missing-target"
KNOWN_PATH_REFERENCE_RULE_IDS = frozenset(
    (PATH_REFERENCE_CASE_MISMATCH_RULE, PATH_REFERENCE_MISSING_TARGET_RULE)
)
KNOWN_PATH_REFERENCE_CATEGORIES = frozenset((PATH_REFERENCE_CATEGORY,))
MARKDOWN_FILE_SUFFIXES = frozenset((".md", ".mdc"))
ISSUE_TEMPLATE_SUFFIXES = frozenset((".md", ".yml", ".yaml"))
CONFIG_SURFACES = frozenset(
    (
        ".gitattributes",
        ".pre-commit-config.yaml",
        ".vscode/settings.json",
        "package.json",
        "pyproject.toml",
    )
)
WORKFLOW_SURFACE_PATTERNS = (".github/workflows/*.yml", ".github/workflows/*.yaml")
IGNORED_SCAN_DIRECTORIES = frozenset(
    (".cache", ".git", ".pytest_cache", ".ruff_cache", "node_modules")
)
MARKDOWN_PACKAGE_SCRIPT = "lint:md"
LINE_ENDING_RISK_STATES = frozenset(("cr", "crlf", "mixed"))
AZURE_DEVOPS_MODULES = frozenset(
    ("azure-devops-platform", "azure-pipelines", "azure-devops-collaboration")
)
AZURE_HOST_SETUP_FIELDS = (
    ("azure_boards_policy", "Azure Boards intake policy"),
    ("azure_repos_pr_template_policy", "Azure Repos pull request template policy"),
    ("azure_branch_policy_reviewer_guidance", "Branch policy reviewer guidance"),
    ("azure_security_intake_policy", "Security intake policy"),
    ("azure_security_product_enablement", "Security product enablement"),
    ("azure_dependency_update_policy", "Dependency update policy"),
)
PATH_TOKEN_PATTERN = re.compile(
    r"(?P<literal>(?:[A-Za-z0-9_.-]+[\\/])+[A-Za-z0-9_.%+~#?=&,-]+|"
    r"(?:\./|\../)?[A-Za-z0-9_.-]+\."
    r"(?:md|mdc|py|ps1|json|jsonc|ya?ml|toml|hcl|tf|tfvars|tftpl|tfbackend|mjs|js|txt))"
)
MARKDOWN_LINK_TARGET_PATTERN = re.compile(r"!?\[[^\]]*]\((?P<target>[^)\s]+)(?:\s+[^)]*)?\)")
MARKDOWNLINT_FINDING_PATTERN = re.compile(
    r"^(?P<path>.*?):\d+(?::\d+)?\s+(?P<rule>MD\d{3}(?:/[A-Za-z0-9_-]+)?)\b"
)
GIT_EOL_PATTERN = re.compile(
    r"^i/(?P<index>\S+)\s+w/(?P<worktree>\S+)\s+attr/(?P<attr>.*?)\t(?P<path>.*)$"
)


class CaptureRunner(Protocol):
    """Run a command in a repository root and capture its text output."""

    def __call__(
        self,
        command: Sequence[str],
        repo_root: Path,
        *,
        env: Mapping[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]: ...


class FirstAdoptionQualityError(RuntimeError):
    """Raised when a first-adoption report cannot be generated safely."""


@dataclass(frozen=True)
class GitFileCollection:
    """Repository file discovery result."""

    files: tuple[str, ...]
    skipped_non_regular_paths: tuple[str, ...]


@dataclass(frozen=True)
class GitEolRecord:
    """One parsed ``git ls-files --eol`` record."""

    index_eol: str
    worktree_eol: str
    raw_attributes: str


@dataclass(frozen=True)
class LineEndingRecord:
    """Line-ending state for one discovered file."""

    path: str
    index_eol: str
    git_worktree_eol: str
    detected_worktree_eol: str
    attr_text: str
    attr_eol: str
    normalization_risk: bool


@dataclass(frozen=True)
class LineEndingReport:
    """Line-ending inventory and normalization-risk data."""

    records: tuple[LineEndingRecord, ...]
    counts: Counter[str]
    normalization_risk_paths: tuple[str, ...]


@dataclass(frozen=True)
class PathReferenceFinding:
    """One path-reference quality finding."""

    rule_id: str
    category: str
    source_path: str
    line_number: int
    literal: str
    normalized_path: str
    matched_path: str | None
    message: str


@dataclass(frozen=True)
class PathReferenceSuppression:
    """One configured suppression for a path-reference finding."""

    rule_id: str | None
    category: str | None
    path: str | None
    path_glob: str | None
    literal: str | None
    literal_pattern: re.Pattern[str] | None
    reason: str

    def matches(self, finding: PathReferenceFinding) -> bool:
        """Return whether this suppression applies to ``finding``."""
        if self.rule_id is not None and self.rule_id != finding.rule_id:
            return False
        if self.category is not None and self.category != finding.category:
            return False
        if self.path is not None and self.path != finding.source_path:
            return False
        if self.path_glob is not None and not fnmatch.fnmatchcase(
            finding.source_path,
            self.path_glob,
        ):
            return False
        if self.literal is not None and self.literal != finding.literal:
            return False
        if self.literal_pattern is not None and not self.literal_pattern.search(finding.literal):
            return False
        return True


@dataclass(frozen=True)
class QualitySuppressions:
    """Parsed quality report suppression configuration."""

    path_reference: tuple[PathReferenceSuppression, ...]


@dataclass(frozen=True)
class PathReferenceReport:
    """Path-reference report result."""

    scanned_paths: tuple[str, ...]
    findings: tuple[PathReferenceFinding, ...]
    suppressed_count: int


@dataclass(frozen=True)
class MarkdownlintFinding:
    """One parsed markdownlint finding."""

    path: str
    rule: str


@dataclass(frozen=True)
class MarkdownlintReport:
    """Markdownlint report or fixer result."""

    available: bool
    message: str
    return_code: int
    findings: tuple[MarkdownlintFinding, ...]
    changed_files: tuple[str, ...]


@dataclass(frozen=True)
class PowerShellAnalyzerReport:
    """PowerShell analyzer report result."""

    available: bool
    message: str
    summary_lines: tuple[str, ...]
    issue_ready_markdown: tuple[str, ...]


@dataclass(frozen=True)
class HostSetupReport:
    """Azure DevOps Services first-adoption setup status."""

    marker_available: bool
    azure_modules_retained: bool
    host_provider: str | None
    setup_items: tuple[tuple[str, str], ...]
    message: str


def default_repo_root() -> Path:
    """Return the repository root implied by this script's committed location."""
    return Path(__file__).resolve().parents[2]


def resolve_repo_root(raw_repo_root: str | None) -> Path:
    """Resolve and validate the repository root argument."""
    repo_root = Path(raw_repo_root).expanduser() if raw_repo_root else default_repo_root()
    resolved = repo_root.resolve()
    if not resolved.is_dir():
        raise FirstAdoptionQualityError("Repository root does not exist or is not a directory.")
    return resolved


def resolve_repo_path(repo_root: Path, relative_path: str) -> Path:
    """Resolve a Git-relative path inside the repository root."""
    if "\\" in relative_path or Path(relative_path).is_absolute():
        raise FirstAdoptionQualityError(f"Git path must be repository-relative: {relative_path}")
    parts = PurePosixPath(relative_path).parts
    if any(part in ("", ".", "..") for part in parts):
        raise FirstAdoptionQualityError(f"Git path must not contain traversal: {relative_path}")
    resolved_path = (repo_root / relative_path).resolve()
    try:
        resolved_path.relative_to(repo_root)
    except ValueError as error:
        raise FirstAdoptionQualityError(
            f"Git path escapes repository root: {relative_path}"
        ) from error
    return resolved_path


def is_present_regular_file(path: Path) -> bool:
    """Return whether ``path`` is a present regular file, excluding symlinks."""
    return not path.is_symlink() and path.is_file()


def load_marker_template_sync(repo_root: Path) -> dict[str, object] | None:
    """Load the marker's template_sync mapping when a marker is present."""
    marker_path = resolve_repo_path(repo_root, MARKER_PATH)
    # resolve_repo_path() collapses a leaf symlink, so check the lexical path for
    # symlink/regular-file status the way the rest of this file's discovery does.
    marker_link = repo_root / MARKER_PATH
    if not marker_path.exists() and not marker_link.is_symlink():
        return None
    if not is_present_regular_file(marker_link):
        raise FirstAdoptionQualityError(f"Expected a regular file: {MARKER_PATH}")
    try:
        marker_document = yaml.safe_load(marker_path.read_text(encoding="utf-8-sig"))
    except yaml.YAMLError as error:
        raise FirstAdoptionQualityError(f"{MARKER_PATH} is not valid YAML: {error}") from error
    except OSError as error:
        error_summary = f"{type(error).__name__}: {error.strerror or 'I/O error'}"
        raise FirstAdoptionQualityError(
            f"Unable to read {MARKER_PATH} ({error_summary})."
        ) from error
    if not isinstance(marker_document, dict):
        raise FirstAdoptionQualityError(f"{MARKER_PATH} must contain a YAML mapping.")
    template_sync = marker_document.get("template_sync")
    if not isinstance(template_sync, dict):
        raise FirstAdoptionQualityError(f"{MARKER_PATH} must contain template_sync mapping.")
    return template_sync


def marker_modules(template_sync: Mapping[str, object]) -> frozenset[str]:
    """Return marker-listed modules from a parsed template_sync mapping."""
    raw_modules = template_sync.get("included_modules")
    if not isinstance(raw_modules, list):
        return frozenset()
    return frozenset(item for item in raw_modules if isinstance(item, str))


def build_host_setup_report(repo_root: Path) -> HostSetupReport:
    """Build an Azure DevOps Services first-adoption service setup report."""
    template_sync = load_marker_template_sync(repo_root)
    if template_sync is None:
        return HostSetupReport(
            marker_available=False,
            azure_modules_retained=False,
            host_provider=None,
            setup_items=(),
            message=f"{MARKER_PATH} not found; no host setup marker decisions are available.",
        )

    modules = marker_modules(template_sync)
    azure_modules_retained = bool(modules & AZURE_DEVOPS_MODULES)
    host_provider = template_sync.get("host_provider")
    host_provider_text = host_provider if isinstance(host_provider, str) else None
    if not azure_modules_retained:
        return HostSetupReport(
            marker_available=True,
            azure_modules_retained=False,
            host_provider=host_provider_text,
            setup_items=(),
            message="No Azure DevOps Services host setup tasks are recorded.",
        )

    setup_items = tuple(
        (label, str(template_sync.get(field_name, "not recorded")))
        for field_name, label in AZURE_HOST_SETUP_FIELDS
    )
    return HostSetupReport(
        marker_available=True,
        azure_modules_retained=True,
        host_provider=host_provider_text,
        setup_items=setup_items,
        message=(
            "These are Azure DevOps Services setup follow-ups, not local file "
            "materialization failures or GitHub issue-template findings."
        ),
    )


def print_host_setup_report(report: HostSetupReport, *, stdout: TextIO) -> None:
    """Print a stable Azure DevOps Services setup report."""
    print("First-adoption host setup report:", file=stdout)
    if not report.marker_available or not report.azure_modules_retained:
        print(f"  {report.message}", file=stdout)
        return
    print("  Azure DevOps Services service setup tasks:", file=stdout)
    print(f"    - Host provider: {report.host_provider or 'not recorded'}", file=stdout)
    for label, value in report.setup_items:
        print(f"    - {label}: {value}", file=stdout)
    print(f"  {report.message}", file=stdout)


def format_command(command: Sequence[str]) -> str:
    """Return a shell-like representation of the exact argument vector."""
    command_parts = list(command)
    if os.name == "nt":
        return subprocess.list2cmdline(command_parts)
    return shlex.join(command_parts)


def run_capture(
    command: Sequence[str],
    repo_root: Path,
    *,
    env: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run ``command`` in ``repo_root`` and capture text output."""
    try:
        return subprocess.run(
            list(command),
            cwd=repo_root,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
    except OSError as error:
        error_summary = f"{type(error).__name__}: {error.strerror or 'I/O error'}"
        raise FirstAdoptionQualityError(f"Unable to run {command[0]} ({error_summary}).") from error


def git_capture(repo_root: Path, args: Sequence[str]) -> str:
    """Run a Git command and return stdout, raising on failure."""
    result = run_capture(("git", *args), repo_root)
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise FirstAdoptionQualityError(f"Unable to inspect repository with git: {message}")
    return result.stdout


def collect_git_files(
    repo_root: Path,
    *,
    tracked_only: bool = False,
    include_ignored: bool = False,
    stdout: TextIO | None = None,
) -> GitFileCollection:
    """Collect tracked and adoption-visible files for quality reports."""
    commands = [GIT_TRACKED_FILES_COMMAND if tracked_only else GIT_VISIBLE_FILES_COMMAND]
    if include_ignored and not tracked_only:
        commands.append(GIT_IGNORED_FILES_COMMAND)

    files: list[str] = []
    skipped_non_regular_paths: list[str] = []
    seen_paths: set[str] = set()
    for command in commands:
        if stdout is not None:
            print(f"$ {format_command(command)}", file=stdout, flush=True)
        output = git_capture(repo_root, command[1:])
        for relative_path in output.split("\0"):
            if not relative_path or relative_path in seen_paths:
                continue
            seen_paths.add(relative_path)
            path = resolve_repo_path(repo_root, relative_path)
            if is_present_regular_file(path):
                files.append(relative_path)
            elif path.exists() or path.is_symlink():
                skipped_non_regular_paths.append(relative_path)

    return GitFileCollection(
        files=tuple(sorted(files)),
        skipped_non_regular_paths=tuple(sorted(skipped_non_regular_paths)),
    )


def git_eol_records(
    repo_root: Path,
    *,
    tracked_only: bool = False,
    include_ignored: bool = False,
) -> dict[str, GitEolRecord]:
    """Return parsed ``git ls-files --eol`` records keyed by repository path."""
    commands: list[tuple[str, ...]] = [
        (
            ("git", "ls-files", "--eol", "--cached")
            if tracked_only
            else ("git", "ls-files", "--eol", "--cached", "--others", "--exclude-standard")
        )
    ]
    if include_ignored and not tracked_only:
        commands.append(("git", "ls-files", "--eol", "--others", "--ignored", "--exclude-standard"))

    records: dict[str, GitEolRecord] = {}
    for command in commands:
        output = git_capture(repo_root, command[1:])
        for line in output.splitlines():
            match = GIT_EOL_PATTERN.match(line)
            if match is None:
                continue
            path = match.group("path")
            records[path] = GitEolRecord(
                index_eol=match.group("index"),
                worktree_eol=match.group("worktree"),
                raw_attributes=match.group("attr"),
            )
    return records


def git_attributes(repo_root: Path, files: Sequence[str]) -> dict[str, dict[str, str]]:
    """Return selected Git attributes for ``files``."""
    attributes_by_path: dict[str, dict[str, str]] = {relative_path: {} for relative_path in files}
    if not files:
        return attributes_by_path

    chunk_size = 100
    for index in range(0, len(files), chunk_size):
        chunk = files[index : index + chunk_size]
        output = git_capture(repo_root, ("check-attr", "text", "eol", "--", *chunk))
        for line in output.splitlines():
            try:
                path, attribute, value = line.split(": ", 2)
            except ValueError:
                continue
            attributes_by_path.setdefault(path, {})[attribute] = value
    return attributes_by_path


def detect_file_line_endings(path: Path) -> str:
    """Return a stable line-ending category for ``path``."""
    try:
        data = path.read_bytes()
    except OSError as error:
        error_summary = f"{type(error).__name__}: {error.strerror or 'I/O error'}"
        raise FirstAdoptionQualityError(
            f"Unable to read repository file ({error_summary})."
        ) from error

    if b"\0" in data:
        return "binary"

    crlf_count = data.count(b"\r\n")
    lf_count = data.count(b"\n") - crlf_count
    cr_count = data.count(b"\r") - crlf_count

    populated_kinds = sum(1 for count in (crlf_count, lf_count, cr_count) if count > 0)
    if populated_kinds > 1:
        return "mixed"
    if crlf_count > 0:
        return "crlf"
    if lf_count > 0:
        return "lf"
    if cr_count > 0:
        return "cr"
    return "no-newline"


def build_line_ending_report(
    repo_root: Path,
    *,
    tracked_only: bool = False,
    include_ignored: bool = False,
) -> LineEndingReport:
    """Build a line-ending inventory for adoption-visible files."""
    collection = collect_git_files(
        repo_root,
        tracked_only=tracked_only,
        include_ignored=include_ignored,
    )
    eol_records = git_eol_records(
        repo_root,
        tracked_only=tracked_only,
        include_ignored=include_ignored,
    )
    attributes = git_attributes(repo_root, collection.files)

    records: list[LineEndingRecord] = []
    counts: Counter[str] = Counter()
    risk_paths: list[str] = []
    for relative_path in collection.files:
        detected_eol = detect_file_line_endings(resolve_repo_path(repo_root, relative_path))
        counts[detected_eol] += 1
        git_record = eol_records.get(relative_path)
        attr_values = attributes.get(relative_path, {})
        attr_text = attr_values.get("text", "unspecified")
        attr_eol = attr_values.get("eol", "unspecified")
        normalization_risk = (
            attr_eol == "lf" and detected_eol in LINE_ENDING_RISK_STATES and attr_text != "unset"
        )
        if normalization_risk:
            risk_paths.append(relative_path)
        records.append(
            LineEndingRecord(
                path=relative_path,
                index_eol=git_record.index_eol if git_record else "unknown",
                git_worktree_eol=git_record.worktree_eol if git_record else "unknown",
                detected_worktree_eol=detected_eol,
                attr_text=attr_text,
                attr_eol=attr_eol,
                normalization_risk=normalization_risk,
            )
        )

    return LineEndingReport(
        records=tuple(records),
        counts=counts,
        normalization_risk_paths=tuple(sorted(risk_paths)),
    )


def print_line_ending_report(report: LineEndingReport, *, stdout: TextIO) -> None:
    """Print a stable line-ending report."""
    print("First-adoption line-ending report:", file=stdout)
    print(f"  Files inventoried: {len(report.records)}", file=stdout)
    for kind in ("lf", "crlf", "mixed", "cr", "no-newline", "binary"):
        print(f"  {kind}: {report.counts.get(kind, 0)}", file=stdout)
    if report.normalization_risk_paths:
        print(
            "  Normalization risk: files below are matched by Git attributes "
            "that pin LF and currently contain CRLF, CR, or mixed endings.",
            file=stdout,
        )
        print(
            "  Running broad fixers or touching these files may cause reviewable "
            "line-ending normalization; do not run broad renormalization "
            "automatically.",
            file=stdout,
        )
        for path in report.normalization_risk_paths:
            print(f"    - {path}", file=stdout)
    else:
        print("  Normalization risk: none detected.", file=stdout)


def is_excluded_scan_path(relative_path: str) -> bool:
    """Return whether ``relative_path`` lives under a generated or dependency directory."""
    parts = PurePosixPath(relative_path).parts
    return any(part in IGNORED_SCAN_DIRECTORIES for part in parts)


def is_path_reference_surface(relative_path: str) -> bool:
    """Return whether ``relative_path`` belongs to the documented scan surface set."""
    if is_excluded_scan_path(relative_path):
        return False
    path = PurePosixPath(relative_path)
    suffix = path.suffix.lower()
    if suffix in MARKDOWN_FILE_SUFFIXES:
        return True
    if relative_path.startswith(".github/ISSUE_TEMPLATE/") and suffix in ISSUE_TEMPLATE_SUFFIXES:
        return True
    if relative_path in CONFIG_SURFACES:
        return True
    return any(fnmatch.fnmatchcase(relative_path, pattern) for pattern in WORKFLOW_SURFACE_PATTERNS)


def repo_directories(files: Sequence[str]) -> set[str]:
    """Return repository-relative directories implied by ``files``."""
    directories: set[str] = set()
    for file_path in files:
        path = PurePosixPath(file_path)
        for parent in path.parents:
            parent_text = parent.as_posix()
            if parent_text == ".":
                continue
            directories.add(parent_text)
    return directories


def case_index(paths: Sequence[str] | set[str]) -> dict[str, str]:
    """Return a case-folded path index with deterministic canonical values."""
    index: dict[str, str] = {}
    for path in sorted(paths):
        index.setdefault(path.casefold(), path)
    return index


def normalize_reference_literal(
    literal: str,
    *,
    source_path: str,
) -> tuple[str, bool]:
    """Normalize a scanned literal into a repository-relative candidate path."""
    cleaned = literal.strip().strip("`'\"()[]{}<>,;:")
    if not cleaned:
        return "", False
    if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", cleaned) or cleaned.startswith("//"):
        return "", False
    if cleaned.startswith("#") or cleaned.startswith("mailto:"):
        return "", False
    if "@" in cleaned or "$" in cleaned or "*" in cleaned:
        return "", False
    if any(char in cleaned for char in ("{", "}", "<", ">")):
        return "", False
    if re.match(r"^[A-Za-z]:[\\/]", cleaned):
        return "", False

    path_part = cleaned.split("#", maxsplit=1)[0].split("?", maxsplit=1)[0]
    path_part = path_part.replace("\\", "/")
    if not path_part or path_part.startswith("/"):
        return "", False

    source_parent = PurePosixPath(source_path).parent
    try:
        if path_part.startswith("./") or path_part.startswith("../"):
            parts: list[str] = []
            for part in (source_parent / path_part).parts:
                if part in ("", "."):
                    continue
                if part == "..":
                    if not parts:
                        return "", False
                    parts.pop()
                else:
                    parts.append(part)
            normalized = PurePosixPath(*parts).as_posix() if parts else ""
        else:
            normalized = PurePosixPath(path_part).as_posix()
    except ValueError:
        return "", False

    if not normalized or normalized == ".":
        return "", False
    return normalized.removesuffix("/"), cleaned.endswith("/")


def is_strong_repo_path(candidate_path: str, known_root_components: set[str]) -> bool:
    """Return whether a missing candidate is strong enough to report."""
    first_part = PurePosixPath(candidate_path).parts[0]
    if first_part in known_root_components:
        return True
    return first_part.startswith(".") and len(PurePosixPath(candidate_path).parts) > 1


def extract_reference_literals(text: str) -> list[tuple[int, str]]:
    """Extract path-like literals from text with source line numbers."""
    literals: list[tuple[int, str]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for match in MARKDOWN_LINK_TARGET_PATTERN.finditer(line):
            literals.append((line_number, match.group("target")))
        for match in PATH_TOKEN_PATTERN.finditer(line):
            literals.append((line_number, match.group("literal")))
    return literals


def _string_property(
    value: object,
    *,
    key: str,
    required: bool = False,
) -> str | None:
    """Validate and return an optional string property from a suppression entry."""
    if value is None:
        if required:
            raise FirstAdoptionQualityError(f"Suppression entry is missing required '{key}'.")
        return None
    if not isinstance(value, str) or not value.strip():
        raise FirstAdoptionQualityError(f"Suppression entry '{key}' must be a non-empty string.")
    return value


def parse_path_reference_suppression(raw_entry: object, *, index: int) -> PathReferenceSuppression:
    """Parse one path-reference suppression entry."""
    if not isinstance(raw_entry, dict):
        raise FirstAdoptionQualityError(
            f"path-reference suppression {index} must be a JSON object."
        )

    allowed_keys = {
        "category",
        "literal",
        "literalPattern",
        "path",
        "pathGlob",
        "reason",
        "ruleId",
    }
    unknown_keys = sorted(set(raw_entry) - allowed_keys)
    if unknown_keys:
        raise FirstAdoptionQualityError(
            f"path-reference suppression {index} has unknown key(s): {', '.join(unknown_keys)}"
        )
    selector_keys = allowed_keys - {"reason"}
    if not selector_keys.intersection(raw_entry):
        raise FirstAdoptionQualityError(
            f"path-reference suppression {index} must include at least one selector."
        )

    rule_id = _string_property(raw_entry.get("ruleId"), key="ruleId")
    if rule_id is not None and rule_id not in KNOWN_PATH_REFERENCE_RULE_IDS:
        raise FirstAdoptionQualityError(
            f"path-reference suppression {index} references unknown ruleId: {rule_id}"
        )

    category = _string_property(raw_entry.get("category"), key="category")
    if category is not None and category not in KNOWN_PATH_REFERENCE_CATEGORIES:
        raise FirstAdoptionQualityError(
            f"path-reference suppression {index} references unknown category: {category}"
        )

    literal_pattern_text = _string_property(raw_entry.get("literalPattern"), key="literalPattern")
    literal_pattern = None
    if literal_pattern_text is not None:
        try:
            literal_pattern = re.compile(literal_pattern_text)
        except re.error as error:
            raise FirstAdoptionQualityError(
                f"path-reference suppression {index} has invalid literalPattern: {error}"
            ) from error

    return PathReferenceSuppression(
        rule_id=rule_id,
        category=category,
        path=_string_property(raw_entry.get("path"), key="path"),
        path_glob=_string_property(raw_entry.get("pathGlob"), key="pathGlob"),
        literal=_string_property(raw_entry.get("literal"), key="literal"),
        literal_pattern=literal_pattern,
        reason=_string_property(raw_entry.get("reason"), key="reason", required=True) or "",
    )


def load_quality_suppressions(repo_root: Path, suppression_path: str) -> QualitySuppressions:
    """Load and validate quality-report suppressions."""
    full_path = resolve_repo_path(repo_root, suppression_path)
    if not full_path.exists():
        return QualitySuppressions(path_reference=())
    if not is_present_regular_file(full_path):
        raise FirstAdoptionQualityError(
            f"Suppression path is not a regular file: {suppression_path}"
        )
    try:
        raw_data = json.loads(full_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as error:
        raise FirstAdoptionQualityError(
            f"{suppression_path} is not valid JSON: {error.msg}"
        ) from error
    except OSError as error:
        error_summary = f"{type(error).__name__}: {error.strerror or 'I/O error'}"
        raise FirstAdoptionQualityError(
            f"Unable to read suppression file ({error_summary})."
        ) from error

    if not isinstance(raw_data, dict):
        raise FirstAdoptionQualityError(f"{suppression_path} must contain a JSON object.")
    allowed_sections = {"path-reference"}
    unknown_sections = sorted(set(raw_data) - allowed_sections)
    if unknown_sections:
        raise FirstAdoptionQualityError(
            f"{suppression_path} has unknown top-level section(s): {', '.join(unknown_sections)}"
        )
    if "path-reference" not in raw_data:
        raise FirstAdoptionQualityError(
            f"{suppression_path} is missing required 'path-reference' section."
        )

    path_reference_section = raw_data["path-reference"]
    if not isinstance(path_reference_section, dict):
        raise FirstAdoptionQualityError("'path-reference' must be a JSON object.")
    section_unknown_keys = sorted(set(path_reference_section) - {"suppressions"})
    if section_unknown_keys:
        raise FirstAdoptionQualityError(
            "'path-reference' has unknown key(s): " + ", ".join(section_unknown_keys)
        )
    raw_suppressions = path_reference_section.get("suppressions", [])
    if not isinstance(raw_suppressions, list):
        raise FirstAdoptionQualityError("'path-reference.suppressions' must be an array.")

    suppressions = tuple(
        parse_path_reference_suppression(raw_entry, index=index)
        for index, raw_entry in enumerate(raw_suppressions, start=1)
    )
    return QualitySuppressions(path_reference=suppressions)


def is_suppressed(
    finding: PathReferenceFinding,
    suppressions: Sequence[PathReferenceSuppression],
) -> bool:
    """Return whether ``finding`` is suppressed."""
    return any(suppression.matches(finding) for suppression in suppressions)


def build_path_reference_report(
    repo_root: Path,
    *,
    tracked_only: bool = False,
    include_ignored: bool = False,
    suppression_path: str = DEFAULT_SUPPRESSION_PATH,
    include_missing_targets: bool = False,
) -> PathReferenceReport:
    """Build a path-reference casing and existence report."""
    collection = collect_git_files(
        repo_root,
        tracked_only=tracked_only,
        include_ignored=include_ignored,
    )
    suppressions = load_quality_suppressions(repo_root, suppression_path)
    file_paths = set(collection.files)
    directory_paths = repo_directories(collection.files)
    all_known_paths = file_paths | directory_paths
    exact_paths = all_known_paths
    folded_paths = case_index(all_known_paths)
    known_root_components = {PurePosixPath(path).parts[0] for path in all_known_paths}

    scanned_paths = tuple(path for path in collection.files if is_path_reference_surface(path))
    findings: list[PathReferenceFinding] = []
    suppressed_count = 0
    seen_findings: set[tuple[str, str, int, str]] = set()
    for source_path in scanned_paths:
        full_path = resolve_repo_path(repo_root, source_path)
        try:
            text = full_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        except OSError as error:
            error_summary = f"{type(error).__name__}: {error.strerror or 'I/O error'}"
            raise FirstAdoptionQualityError(
                f"Unable to read scanned surface {source_path} ({error_summary})."
            ) from error

        for line_number, literal in extract_reference_literals(text):
            candidate_path, _had_trailing_slash = normalize_reference_literal(
                literal,
                source_path=source_path,
            )
            if not candidate_path:
                continue
            if candidate_path in exact_paths:
                continue

            folded_match = folded_paths.get(candidate_path.casefold())
            if folded_match is not None and folded_match != candidate_path:
                finding = PathReferenceFinding(
                    rule_id=PATH_REFERENCE_CASE_MISMATCH_RULE,
                    category=PATH_REFERENCE_CATEGORY,
                    source_path=source_path,
                    line_number=line_number,
                    literal=literal,
                    normalized_path=candidate_path,
                    matched_path=folded_match,
                    message=(
                        "Path reference casing differs from the discovered "
                        f"repository path '{folded_match}'."
                    ),
                )
            elif include_missing_targets and is_strong_repo_path(
                candidate_path,
                known_root_components,
            ):
                finding = PathReferenceFinding(
                    rule_id=PATH_REFERENCE_MISSING_TARGET_RULE,
                    category=PATH_REFERENCE_CATEGORY,
                    source_path=source_path,
                    line_number=line_number,
                    literal=literal,
                    normalized_path=candidate_path,
                    matched_path=None,
                    message="Path reference does not match a discovered repository file or directory.",
                )
            else:
                continue

            dedupe_key = (
                finding.rule_id,
                finding.source_path,
                finding.line_number,
                finding.literal,
            )
            if dedupe_key in seen_findings:
                continue
            seen_findings.add(dedupe_key)
            if is_suppressed(finding, suppressions.path_reference):
                suppressed_count += 1
                continue
            findings.append(finding)

    return PathReferenceReport(
        scanned_paths=scanned_paths,
        findings=tuple(findings),
        suppressed_count=suppressed_count,
    )


def print_path_reference_report(report: PathReferenceReport, *, stdout: TextIO) -> None:
    """Print a stable path-reference report."""
    print("First-adoption path-reference report:", file=stdout)
    print("  Scan surfaces:", file=stdout)
    print("    - Markdown files (*.md, *.mdc)", file=stdout)
    print("    - Issue and pull request templates", file=stdout)
    print(
        "    - .vscode/settings.json, pyproject.toml, package.json, "
        ".pre-commit-config.yaml, .github/workflows/*.yml/*.yaml, and .gitattributes",
        file=stdout,
    )
    print(f"  Files scanned: {len(report.scanned_paths)}", file=stdout)
    print(f"  Findings: {len(report.findings)}", file=stdout)
    print(f"  Suppressed findings: {report.suppressed_count}", file=stdout)
    if not report.findings:
        return
    for finding in report.findings:
        print(
            f"  - {finding.rule_id} {finding.source_path}:{finding.line_number} "
            f"`{finding.literal}`",
            file=stdout,
        )
        print(f"    {finding.message}", file=stdout)


def load_package_scripts(repo_root: Path) -> dict[str, object]:
    """Return the root package.json scripts mapping when package.json exists."""
    package_path = repo_root / "package.json"
    if not package_path.exists():
        return {}
    if not is_present_regular_file(package_path):
        raise FirstAdoptionQualityError("Expected a regular file: package.json")
    try:
        package_data = json.loads(package_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as error:
        raise FirstAdoptionQualityError(f"package.json is not valid JSON: {error.msg}") from error
    except OSError as error:
        error_summary = f"{type(error).__name__}: {error.strerror or 'I/O error'}"
        raise FirstAdoptionQualityError(
            f"Unable to read package.json ({error_summary})."
        ) from error

    scripts = package_data.get("scripts") if isinstance(package_data, dict) else None
    return scripts if isinstance(scripts, dict) else {}


def npm_executable() -> str | None:
    """Return an npm executable when one is available."""
    return shutil.which("npm") or shutil.which("npm.cmd")


def parse_markdownlint_findings(output: str) -> tuple[MarkdownlintFinding, ...]:
    """Parse markdownlint-cli2 text findings into stable counters."""
    findings: list[MarkdownlintFinding] = []
    for line in output.splitlines():
        match = MARKDOWNLINT_FINDING_PATTERN.match(line)
        if match is None:
            continue
        findings.append(MarkdownlintFinding(path=match.group("path"), rule=match.group("rule")))
    return tuple(findings)


def git_status_files(repo_root: Path) -> tuple[str, ...]:
    """Return changed Git status paths for fixer summaries."""
    output = git_capture(repo_root, ("status", "--porcelain=v1", "--untracked-files=all"))
    paths: list[str] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        paths.append(line[3:] if len(line) > 3 else line.strip())
    return tuple(sorted(paths))


def build_markdownlint_report(
    repo_root: Path,
    *,
    fix: bool = False,
    runner: CaptureRunner = run_capture,
) -> MarkdownlintReport:
    """Run Markdownlint in report or explicit fixer mode."""
    package_scripts = load_package_scripts(repo_root)
    if MARKDOWN_PACKAGE_SCRIPT not in package_scripts:
        return MarkdownlintReport(
            available=False,
            message="Markdownlint report unavailable: package.json has no lint:md script.",
            return_code=0,
            findings=(),
            changed_files=(),
        )
    npm = npm_executable()
    if npm is None:
        return MarkdownlintReport(
            available=False,
            message="Markdownlint report unavailable: npm was not found on PATH.",
            return_code=0,
            findings=(),
            changed_files=(),
        )

    before_status = git_status_files(repo_root) if fix else ()
    command = (
        (npm, "run", MARKDOWN_PACKAGE_SCRIPT, "--", "--fix")
        if fix
        else (
            npm,
            "run",
            MARKDOWN_PACKAGE_SCRIPT,
        )
    )
    result = runner(command, repo_root)
    combined_output = "\n".join(part for part in (result.stdout, result.stderr) if part)
    findings = parse_markdownlint_findings(combined_output)
    changed_files: tuple[str, ...] = ()
    if fix:
        after_status = git_status_files(repo_root)
        changed_files = tuple(path for path in after_status if path not in before_status)
    return MarkdownlintReport(
        available=True,
        message="Markdownlint fixer completed." if fix else "Markdownlint report completed.",
        return_code=result.returncode,
        findings=findings,
        changed_files=changed_files,
    )


def print_markdownlint_report(
    report: MarkdownlintReport,
    *,
    fix: bool,
    stdout: TextIO,
) -> None:
    """Print Markdownlint report output."""
    heading = (
        "First-adoption Markdownlint fixer report"
        if fix
        else "First-adoption Markdownlint debt report"
    )
    print(f"{heading}:", file=stdout)
    if not report.available:
        print(f"  {report.message}", file=stdout)
        print(
            "  Install npm dependencies intentionally; this helper never installs tools.",
            file=stdout,
        )
        return

    print(f"  Exit code: {report.return_code}", file=stdout)
    print(f"  Findings parsed: {len(report.findings)}", file=stdout)
    rule_counts = Counter(finding.rule for finding in report.findings)
    file_counts = Counter(finding.path for finding in report.findings)
    if rule_counts:
        print("  Rule counts:", file=stdout)
        for rule, count in sorted(rule_counts.items(), key=lambda item: (-item[1], item[0])):
            print(f"    - {rule}: {count}", file=stdout)
    if file_counts:
        print("  File counts:", file=stdout)
        for path, count in sorted(file_counts.items(), key=lambda item: (-item[1], item[0])):
            print(f"    - {path}: {count}", file=stdout)
    if fix:
        print(
            "  Fix mode can touch files that Git attributes normalize to LF; "
            "review the line-ending report before accepting fixer edits.",
            file=stdout,
        )
        if report.changed_files:
            print("  Files changed after Markdown fixer:", file=stdout)
            for path in report.changed_files:
                print(f"    - {path}", file=stdout)
        else:
            print("  Files changed after Markdown fixer: none detected.", file=stdout)


def powershell_executable() -> str | None:
    """Return a PowerShell executable when one is available."""
    return shutil.which("pwsh") or shutil.which("powershell")


def powershell_files(files: Sequence[str]) -> tuple[str, ...]:
    """Return discovered PowerShell script paths."""
    return tuple(path for path in files if path.lower().endswith(".ps1"))


def build_powershell_report(
    repo_root: Path,
    *,
    tracked_only: bool = False,
    include_ignored: bool = False,
    runner: CaptureRunner = run_capture,
) -> PowerShellAnalyzerReport:
    """Run an optional PSScriptAnalyzer debt report when tooling is available."""
    collection = collect_git_files(
        repo_root,
        tracked_only=tracked_only,
        include_ignored=include_ignored,
    )
    script_paths = powershell_files(collection.files)
    if not script_paths:
        return PowerShellAnalyzerReport(
            available=True,
            message="No PowerShell files were discovered.",
            summary_lines=("No PowerShell files were discovered.",),
            issue_ready_markdown=(),
        )

    settings_path = repo_root / ".github/linting/PSScriptAnalyzerSettings.psd1"
    gate_helper_path = repo_root / "src/tools/Resolve-PSScriptAnalyzerGate.ps1"
    if not is_present_regular_file(settings_path) or not is_present_regular_file(gate_helper_path):
        return PowerShellAnalyzerReport(
            available=False,
            message=(
                "PSScriptAnalyzer report unavailable: retained PowerShell settings "
                "or gate helper files are missing."
            ),
            summary_lines=(),
            issue_ready_markdown=(),
        )

    executable = powershell_executable()
    if executable is None:
        return PowerShellAnalyzerReport(
            available=False,
            message=(
                "PSScriptAnalyzer report unavailable: neither pwsh nor powershell "
                "was found on PATH."
            ),
            summary_lines=(),
            issue_ready_markdown=(),
        )

    command_script = r"""
$ErrorActionPreference = 'Stop'
Import-Module PSScriptAnalyzer -ErrorAction Stop
. (Join-Path -Path (Get-Location) -ChildPath 'src/tools/Resolve-PSScriptAnalyzerGate.ps1')
$settingsPath = Join-Path -Path (Get-Location) -ChildPath '.github/linting/PSScriptAnalyzerSettings.psd1'
$relativeFiles = ConvertFrom-Json -InputObject $env:FIRST_ADOPTION_PS1_FILES_JSON
$findings = [System.Collections.Generic.List[object]]::new()
foreach ($relativeFile in $relativeFiles) {
    $fullPath = Join-Path -Path (Get-Location) -ChildPath $relativeFile
    $findings.AddRange(@(Invoke-ScriptAnalyzer -Path $fullPath -Settings $settingsPath))
}
$result = Resolve-PSScriptAnalyzerGate -Mode 'first-adoption' -AnalyzerFinding $findings -RepositoryRoot (Get-Location)
$result | ConvertTo-Json -Depth 8
"""
    environment = os.environ.copy()
    environment["FIRST_ADOPTION_PS1_FILES_JSON"] = json.dumps(script_paths)
    result = runner(
        (executable, "-NoProfile", "-Command", command_script),
        repo_root,
        env=environment,
    )

    if result.returncode != 0:
        diagnostic = result.stderr.strip() or result.stdout.strip() or "PowerShell command failed"
        return PowerShellAnalyzerReport(
            available=False,
            message=(
                "PSScriptAnalyzer report unavailable: run "
                "`Install-Module PSScriptAnalyzer` intentionally if the PowerShell "
                f"module is retained. Diagnostic: {diagnostic}"
            ),
            summary_lines=(),
            issue_ready_markdown=(),
        )

    try:
        result_data = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise FirstAdoptionQualityError(
            "PSScriptAnalyzer report returned non-JSON output."
        ) from error

    summary_lines = tuple(str(line) for line in result_data.get("SummaryLines", ()))
    issue_ready = result_data.get("IssueReadyMarkdown", ())
    if isinstance(issue_ready, str):
        issue_ready_lines = tuple(issue_ready.splitlines())
    else:
        issue_ready_lines = tuple(str(line) for line in issue_ready)
    return PowerShellAnalyzerReport(
        available=True,
        message="PSScriptAnalyzer report completed.",
        summary_lines=summary_lines,
        issue_ready_markdown=issue_ready_lines,
    )


def print_powershell_report(report: PowerShellAnalyzerReport, *, stdout: TextIO) -> None:
    """Print a stable PowerShell analyzer report."""
    print("First-adoption PSScriptAnalyzer debt report:", file=stdout)
    if not report.available:
        print(f"  {report.message}", file=stdout)
        print("  This helper never installs optional tools automatically.", file=stdout)
        return
    print(f"  {report.message}", file=stdout)
    for line in report.summary_lines:
        print(f"  {line}", file=stdout)
    if report.issue_ready_markdown:
        print("  Issue-ready Markdown:", file=stdout)
        for line in report.issue_ready_markdown:
            print(f"    {line}", file=stdout)


def add_common_scope_args(parser: argparse.ArgumentParser) -> None:
    """Add common file-discovery scope arguments to ``parser``."""
    parser.add_argument(
        "--tracked-only",
        action="store_true",
        help="Scan only tracked files instead of tracked plus untracked non-ignored files.",
    )
    parser.add_argument(
        "--include-ignored",
        action="store_true",
        help="Also include ignored untracked files. Ignored files are excluded by default.",
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Emit first-adoption quality debt reports without installing tools."
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Repository root. Defaults to the repository root containing this script.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    line_endings_parser = subparsers.add_parser(
        "line-endings",
        help="Inventory line endings and Git-attribute normalization risk.",
    )
    add_common_scope_args(line_endings_parser)

    path_references_parser = subparsers.add_parser(
        "path-references",
        help="Check documented path-reference surfaces for casing and missing targets.",
    )
    add_common_scope_args(path_references_parser)
    path_references_parser.add_argument(
        "--suppressions",
        default=DEFAULT_SUPPRESSION_PATH,
        help=f"Suppression file path. Default: {DEFAULT_SUPPRESSION_PATH}.",
    )
    path_references_parser.add_argument(
        "--fail-on-findings",
        action="store_true",
        help="Exit non-zero when unsuppressed path-reference findings are present.",
    )
    path_references_parser.add_argument(
        "--include-missing-targets",
        action="store_true",
        help=(
            "Also report path-like literals that do not match a discovered file "
            "or directory. By default, only casing mismatches are reported."
        ),
    )

    subparsers.add_parser(
        "host-setup",
        help="Report Azure DevOps Services first-adoption service setup follow-ups.",
    )

    markdown_parser = subparsers.add_parser(
        "markdown",
        help="Report Markdownlint debt or run the explicit Markdown fixer.",
    )
    markdown_parser.add_argument(
        "--fix",
        action="store_true",
        help="Run the lint:md fixer command and report changed files afterward.",
    )

    powershell_parser = subparsers.add_parser(
        "powershell",
        help="Report optional PSScriptAnalyzer debt when PowerShell tooling is available.",
    )
    add_common_scope_args(powershell_parser)

    return parser.parse_args(argv)


def run_report(args: argparse.Namespace, *, stdout: TextIO = sys.stdout) -> int:
    """Run the selected report and return a process exit code."""
    repo_root = resolve_repo_root(args.repo_root)

    if args.command == "line-endings":
        line_ending_report = build_line_ending_report(
            repo_root,
            tracked_only=args.tracked_only,
            include_ignored=args.include_ignored,
        )
        print_line_ending_report(line_ending_report, stdout=stdout)
        return 0

    if args.command == "path-references":
        path_reference_report = build_path_reference_report(
            repo_root,
            tracked_only=args.tracked_only,
            include_ignored=args.include_ignored,
            suppression_path=args.suppressions,
            include_missing_targets=args.include_missing_targets,
        )
        print_path_reference_report(path_reference_report, stdout=stdout)
        if args.fail_on_findings and path_reference_report.findings:
            return 1
        return 0

    if args.command == "host-setup":
        host_setup_report = build_host_setup_report(repo_root)
        print_host_setup_report(host_setup_report, stdout=stdout)
        return 0

    if args.command == "markdown":
        markdown_report = build_markdownlint_report(repo_root, fix=args.fix)
        print_markdownlint_report(markdown_report, fix=args.fix, stdout=stdout)
        return markdown_report.return_code if args.fix and markdown_report.return_code != 0 else 0

    if args.command == "powershell":
        powershell_report = build_powershell_report(
            repo_root,
            tracked_only=args.tracked_only,
            include_ignored=args.include_ignored,
        )
        print_powershell_report(powershell_report, stdout=stdout)
        return 0

    raise FirstAdoptionQualityError(f"Unsupported report command: {args.command}")


def fail(message: str) -> NoReturn:
    """Print an error and exit non-zero."""
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the first-adoption quality report CLI."""
    args = parse_args(argv)
    try:
        return run_report(args)
    except FirstAdoptionQualityError as error:
        fail(str(error))


if __name__ == "__main__":
    raise SystemExit(main())
