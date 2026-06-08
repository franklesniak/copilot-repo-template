"""Replace and audit template placeholders through an explicit allowlist.

The helper intentionally avoids broad ``REPO`` or ``github.com`` replacement.
Only the placeholder tokens and GitHub URL shapes defined in this file are
eligible for substitution.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

OWNER_REPO_TOKEN_PATHS = (
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/pull_request_template.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
)
GITHUB_URL_TOKEN_PATHS = (
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/pull_request_template.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
)
APPROVED_GITHUB_URL_SUFFIXES = (
    "/security/advisories/new",
    "/blob/HEAD/CONTRIBUTING.md",
    "/blob/HEAD/SECURITY.md",
    "/discussions",
    "/security",
    "/issues",
    ".git",
    "#support",
    "",
)
SECURITY_REPORTING_MODES = ("github-private-only", "contact-only", "both")
SECURITY_CONTACT_REQUIRED_MODES = frozenset({"contact-only", "both"})
TOKEN_REPLACEMENT_SPECS = (
    ("owner-repo token", "OWNER/REPO", OWNER_REPO_TOKEN_PATHS, "repository"),
    ("codeowners owner", "@OWNER", (".github/CODEOWNERS",), "codeowners_owner"),
    (
        "code of conduct contact",
        "[INSERT CONTACT METHOD]",
        ("CODE_OF_CONDUCT.md",),
        "conduct_contact",
    ),
    ("security contact", "[security contact email]", ("SECURITY.md",), "security_contact"),
    (
        "security contact todo",
        "<!-- TODO: Replace with your security contact email -->",
        ("SECURITY.md",),
        "security_todo_replacement",
    ),
    (
        "VS Code window title",
        "Go to .vscode/settings.json and make this the name of the repo",
        (".vscode/settings.json",),
        "vscode_title",
    ),
)
SKIPPED_DISCOVERY_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "build",
    "dist",
    "node_modules",
    "__pycache__",
}
# Structural validation only; does not enforce GitHub's user/org/repo naming
# rules. Callers must supply a real GitHub identifier.
REPOSITORY_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
HOST_PATTERN = re.compile(r"^[A-Za-z0-9.-]+(?::[0-9]+)?$")
OWNER_REPO_NON_PATH_SEGMENT_PATTERN = re.compile(r"(?<!/)OWNER/REPO(?![A-Za-z0-9_-])")
URL_BOUNDARY_PATTERN = r"(?=$|[^A-Za-z0-9._~:/?#@!$&'*+,;=%-])"


class PlaceholderError(RuntimeError):
    """Raised when placeholder substitution or scanning cannot complete."""


@dataclass(frozen=True)
class ReplacementContext:
    """Concrete downstream values used during placeholder substitution."""

    repository: str
    github_host: str
    codeowners_owner: str
    conduct_contact: str | None
    security_contact: str | None
    security_reporting_mode: str
    vscode_title: str

    @property
    def security_todo_replacement(self) -> str | None:
        """Return the replacement for the security-contact TODO marker."""
        if self.security_contact is None:
            return "<!-- Security contact intentionally omitted by reporting mode -->"
        return "<!-- Security contact configured -->"


@dataclass(frozen=True)
class ReplacementRule:
    """One exact placeholder or approved URL replacement rule."""

    name: str
    placeholder: str
    replacement: str
    paths: tuple[str, ...]
    replace: Callable[[str], tuple[str, int]]


@dataclass(frozen=True)
class ReplacementRecord:
    """A replacement performed in one file."""

    path: str
    rule_name: str
    count: int


@dataclass(frozen=True)
class ScanFinding:
    """An unresolved placeholder or corruption pattern found after substitution."""

    kind: str
    path: str
    line_number: int
    matched_text: str
    message: str

    def format_message(self) -> str:
        """Return a human-readable finding message."""
        return (
            f"{self.path}:{self.line_number}: {self.kind}: " f"{self.matched_text} ({self.message})"
        )


def parse_repository(repository: str) -> tuple[str, str]:
    """Validate the structural shape of an ``OWNER/REPO`` identifier and split it.

    Performs character-class validation only; does not enforce GitHub's
    actual user, organization, or repository naming rules. Callers must
    supply a real GitHub identifier.
    """
    if not REPOSITORY_PATTERN.fullmatch(repository):
        raise PlaceholderError(
            "Repository must use the OWNER/REPO form with URL-safe characters "
            "(letters, digits, underscore, dot, hyphen) in each segment. The "
            "helper performs structural validation only; the caller is "
            "responsible for ensuring the value matches a real GitHub identifier."
        )
    owner, repo = repository.split("/", 1)
    return owner, repo


def validate_github_host(github_host: str) -> str:
    """Validate a GitHub host override without accepting schemes or paths."""
    if not HOST_PATTERN.fullmatch(github_host):
        raise PlaceholderError(
            "GitHub host must be a host name, optionally with a port, and must not "
            "include a URL scheme or path."
        )
    return github_host


def validate_codeowners_owner(codeowners_owner: str) -> str:
    """Validate a CODEOWNERS owner placeholder replacement."""
    if not codeowners_owner.startswith("@") or any(
        character.isspace() for character in codeowners_owner
    ):
        raise PlaceholderError(
            "CODEOWNERS owner must start with @ and must not contain whitespace."
        )
    return codeowners_owner


def validate_non_empty(value: str, field_name: str) -> str:
    """Validate a required non-empty CLI value."""
    if not value.strip():
        raise PlaceholderError(f"{field_name} must not be empty.")
    return value


def validate_security_reporting_mode(security_reporting_mode: str) -> str:
    """Validate a security-reporting mode name."""
    if security_reporting_mode not in SECURITY_REPORTING_MODES:
        quoted_modes = ", ".join(SECURITY_REPORTING_MODES)
        raise PlaceholderError(f"--security-reporting-mode must be one of: {quoted_modes}.")
    return security_reporting_mode


def resolve_security_reporting_mode(
    *,
    security_reporting_mode: str | None,
    security_contact: str | None,
) -> str:
    """Resolve explicit and backward-compatible security-reporting mode input."""
    if security_reporting_mode is None:
        if security_contact is None:
            raise PlaceholderError(
                "Either --security-reporting-mode or --security-contact is required."
            )
        return "both"
    return validate_security_reporting_mode(security_reporting_mode)


def resolve_repo_root(raw_repo_root: str | None) -> Path:
    """Resolve the repository root used for replacement and scanning."""
    repo_root = Path(raw_repo_root).expanduser() if raw_repo_root else REPO_ROOT
    resolved = repo_root.resolve()
    if not resolved.is_dir():
        raise PlaceholderError("Repository root does not exist or is not a directory.")
    return resolved


def resolve_repo_path(repo_root: Path, relative_path: str) -> Path:
    """Resolve a committed relative path inside ``repo_root`` without following symlinks."""
    if "\\" in relative_path or Path(relative_path).is_absolute():
        raise PlaceholderError(f"Allowlisted path must be repository-relative: {relative_path}")
    candidate = repo_root / relative_path
    current = repo_root
    for part in Path(relative_path).parts:
        current = current / part
        if current.is_symlink():
            raise PlaceholderError(f"Allowlisted path must not traverse a symlink: {relative_path}")
    resolved = candidate.resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as error:
        raise PlaceholderError(
            f"Allowlisted path escapes repository root: {relative_path}"
        ) from error
    return resolved


def read_text(path: Path, display_path: str) -> str:
    """Read UTF-8 text without newline translation."""
    try:
        return path.read_bytes().decode("utf-8")
    except UnicodeDecodeError as error:
        raise PlaceholderError(f"{display_path}: file is not valid UTF-8.") from error
    except OSError as error:
        error_summary = f"{type(error).__name__}: {error.strerror or 'I/O error'}"
        raise PlaceholderError(f"{display_path}: unable to read file ({error_summary}).") from error


def write_text(path: Path, display_path: str, text: str) -> None:
    """Write UTF-8 text without newline translation."""
    try:
        path.write_bytes(text.encode("utf-8"))
    except OSError as error:
        error_summary = f"{type(error).__name__}: {error.strerror or 'I/O error'}"
        raise PlaceholderError(
            f"{display_path}: unable to write file ({error_summary})."
        ) from error


def replace_literal(placeholder: str, replacement: str) -> Callable[[str], tuple[str, int]]:
    """Build an exact literal replacement callable."""

    def replace(text: str) -> tuple[str, int]:
        count = text.count(placeholder)
        return text.replace(placeholder, replacement), count

    return replace


def replace_owner_repo_token(repository: str) -> Callable[[str], tuple[str, int]]:
    """Build the non-URL ``OWNER/REPO`` token replacement callable."""

    def replace(text: str) -> tuple[str, int]:
        return OWNER_REPO_NON_PATH_SEGMENT_PATTERN.subn(repository, text)

    return replace


def replace_url_pattern(placeholder: str, replacement: str) -> Callable[[str], tuple[str, int]]:
    """Build a URL replacement callable that requires a URL boundary after the placeholder."""
    pattern = re.compile(re.escape(placeholder) + URL_BOUNDARY_PATTERN)

    def replace(text: str) -> tuple[str, int]:
        return pattern.subn(lambda _match: replacement, text)

    return replace


def build_replacement_context(
    repository: str,
    github_host: str = "github.com",
    codeowners_owner: str | None = None,
    conduct_contact: str | None = None,
    security_contact: str | None = None,
    security_reporting_mode: str | None = None,
    vscode_title: str | None = None,
) -> ReplacementContext:
    """Return validated replacement values for the helper."""
    owner, repo = parse_repository(repository)
    validated_security_contact = (
        validate_non_empty(security_contact, "--security-contact")
        if security_contact is not None
        else None
    )
    resolved_security_reporting_mode = resolve_security_reporting_mode(
        security_reporting_mode=security_reporting_mode,
        security_contact=validated_security_contact,
    )
    if (
        resolved_security_reporting_mode in SECURITY_CONTACT_REQUIRED_MODES
        and validated_security_contact is None
    ):
        raise PlaceholderError(
            "--security-contact is required when --security-reporting-mode is "
            f"{resolved_security_reporting_mode}."
        )
    validated_conduct_contact = (
        validate_non_empty(conduct_contact, "--conduct-contact")
        if conduct_contact is not None
        else validated_security_contact
    )
    return ReplacementContext(
        repository=repository,
        github_host=validate_github_host(github_host),
        codeowners_owner=validate_codeowners_owner(codeowners_owner or f"@{owner}"),
        conduct_contact=validated_conduct_contact,
        security_contact=validated_security_contact,
        security_reporting_mode=resolved_security_reporting_mode,
        vscode_title=validate_non_empty(vscode_title or repo, "--vscode-title"),
    )


def build_security_reporting_section(context: ReplacementContext) -> str:
    """Build the rendered SECURITY.md reporting section for the selected mode."""
    direct_url = "https://github.com/OWNER/REPO/security/advisories/new"
    contact_lines = (
        "### Security Contact\n\n"
        "Contact the maintainers directly at:\n\n"
        "<!-- TODO: Replace with your security contact email -->\n"
        "<!-- Do not use a users.noreply.github.com address as a security intake channel. -->\n"
        "- Contact: [security contact email]\n"
    )
    private_lines = (
        "### GitHub Private Vulnerability Reporting\n\n"
        "> **Maintainers:** Enable private vulnerability reporting in GitHub settings "
        f"before relying on the direct reporting link: `{direct_url}`.\n\n"
        "Use GitHub Security Advisories through the "
        f"[private vulnerability reporting form]({direct_url}) after maintainers have "
        "enabled private vulnerability reporting for this repository.\n"
    )

    if context.security_reporting_mode == "github-private-only":
        return (
            "## Reporting a Vulnerability\n\n"
            "**Please do NOT report security vulnerabilities through public GitHub issues.**\n\n"
            "If you discover a security vulnerability in this project, report it privately "
            "using GitHub private vulnerability reporting.\n\n"
            f"{private_lines}"
        )
    if context.security_reporting_mode == "contact-only":
        return (
            "## Reporting a Vulnerability\n\n"
            "**Please do NOT report security vulnerabilities through public GitHub issues.**\n\n"
            "If you discover a security vulnerability in this project, report it privately "
            "using the contact method below.\n\n"
            f"{contact_lines}"
        )
    return (
        "## Reporting a Vulnerability\n\n"
        "**Please do NOT report security vulnerabilities through public GitHub issues.**\n\n"
        "If you discover a security vulnerability in this project, report it privately "
        "using one of the following methods:\n\n"
        "### Option 1: GitHub Private Vulnerability Reporting\n\n"
        "> **Maintainers:** Enable private vulnerability reporting in GitHub settings "
        f"before relying on the direct reporting link: `{direct_url}`.\n\n"
        "Use GitHub Security Advisories through the "
        f"[private vulnerability reporting form]({direct_url}) after maintainers have "
        "enabled private vulnerability reporting for this repository. If that form is "
        "unavailable, use the security contact option below.\n\n"
        "### Option 2: Security Contact\n\n"
        "Contact the maintainers directly at:\n\n"
        "<!-- TODO: Replace with your security contact email -->\n"
        "<!-- Do not use a users.noreply.github.com address as a security intake channel. -->\n"
        "- Contact: [security contact email]\n"
    )


def replace_security_reporting_section(
    text: str,
    context: ReplacementContext,
) -> tuple[str, int]:
    """Replace the SECURITY.md reporting section when the template shape is present."""
    start_marker = "## Reporting a Vulnerability"
    end_marker = "\n### What to Include"
    start = text.find(start_marker)
    end = text.find(end_marker, start)
    if start == -1 or end == -1:
        return text, 0
    replacement = build_security_reporting_section(context).rstrip("\n")
    return f"{text[:start]}{replacement}{text[end:]}", 1


def build_config_security_block(context: ReplacementContext) -> str:
    """Build the rendered issue-template contact link security block."""
    if context.security_reporting_mode == "contact-only":
        url = "https://github.com/OWNER/REPO/blob/HEAD/SECURITY.md"
        about = (
            "Report security issues using the private contact instructions in "
            "SECURITY.md. Do not open a public issue."
        )
        details = (
            "  # Security reports are handled through SECURITY.md in this mode.\n"
            "  # Keep this link pointed at the policy file unless you intentionally\n"
            "  # replace it with a validated external contact URL.\n"
        )
    else:
        url = "https://github.com/OWNER/REPO/security/advisories/new"
        about = (
            "Report security issues privately. Maintainers must enable private "
            "vulnerability reporting before relying on this link."
        )
        details = (
            "  # Private vulnerability reporting must be enabled in GitHub settings\n"
            "  # before this direct advisory-reporting URL can receive reports.\n"
        )
    return (
        "  # =============================================================================\n"
        "  # SECURITY LINK CONFIGURATION\n"
        "  # =============================================================================\n"
        "  # CUSTOMIZE: Replace `OWNER/REPO` with your org/repo name.\n"
        "  # GHES users must also replace github.com with their GHES host.\n"
        f"{details}"
        "  - name: Security Vulnerabilities\n"
        f"    url: {url}\n"
        f"    about: {about}\n\n"
    )


def replace_config_security_block(
    text: str,
    context: ReplacementContext,
) -> tuple[str, int]:
    """Replace the issue-template config security contact-link block."""
    heading = "  # SECURITY LINK CONFIGURATION\n"
    next_heading = "  # DISCUSSIONS LINK (OPTIONAL)\n"
    heading_index = text.find(heading)
    next_heading_index = text.find(next_heading, heading_index)
    if heading_index == -1 or next_heading_index == -1:
        return text, 0
    start = text.rfind(
        "  # =============================================================================",
        0,
        heading_index,
    )
    end = text.rfind(
        "  # =============================================================================",
        0,
        next_heading_index,
    )
    if start == -1 or end == -1:
        return text, 0
    return f"{text[:start]}{build_config_security_block(context)}{text[end:]}", 1


def bug_security_notice(context: ReplacementContext) -> str:
    """Return the bug-report top-of-form security notice for the selected mode."""
    if context.security_reporting_mode == "contact-only":
        return (
            "        **Security Notice:** If you are reporting a security vulnerability, "
            "do NOT use this form.\n"
            "        Report it using the private contact instructions in\n"
            "        [SECURITY.md](https://github.com/OWNER/REPO/blob/HEAD/SECURITY.md)."
        )
    return (
        "        **Security Notice:** If you are reporting a security vulnerability, "
        "do NOT use this form.\n"
        "        Report it through the repository's\n"
        "        [private vulnerability reporting form](https://github.com/OWNER/REPO/security/advisories/new)\n"
        "        after maintainers have enabled private vulnerability reporting in GitHub settings.\n"
        "        If that form is unavailable, review\n"
        "        [SECURITY.md](https://github.com/OWNER/REPO/blob/HEAD/SECURITY.md)."
    )


def bug_security_checkbox_label(context: ReplacementContext) -> str:
    """Return the bug-report security pre-flight checkbox label."""
    if context.security_reporting_mode == "contact-only":
        return (
            "        - label: This is NOT a security vulnerability "
            "(report those using SECURITY.md)"
        )
    return (
        "        - label: This is NOT a security vulnerability "
        "(report those using SECURITY.md or the private reporting form)"
    )


def bug_severity_security_notice(context: ReplacementContext) -> str:
    """Return the bug-report severity-field security notice."""
    if context.security_reporting_mode == "contact-only":
        return (
            "        For security vulnerabilities, do NOT use this form. Report privately\n"
            "        using the contact instructions in SECURITY.md."
        )
    return (
        "        For security vulnerabilities, do NOT use this form. Report privately\n"
        "        via the private vulnerability reporting form after maintainers enable it\n"
        "        in GitHub settings, or review SECURITY.md."
    )


def find_line_start(text: str, needle: str) -> int:
    """Return the start offset of the line containing ``needle``, or ``-1``."""
    index = text.find(needle)
    if index == -1:
        return -1
    return text.rfind("\n", 0, index) + 1


def replace_bug_report_security_notice(
    text: str,
    context: ReplacementContext,
) -> tuple[str, int]:
    """Replace the bug-report top security warning."""
    start = find_line_start(text, "**Security Notice:**")
    end = text.find("\n\n  - type: checkboxes", start)
    if start == -1 or end == -1:
        return text, 0
    return f"{text[:start]}{bug_security_notice(context)}{text[end:]}", 1


def replace_bug_report_checkbox_label(
    text: str,
    context: ReplacementContext,
) -> tuple[str, int]:
    """Replace the bug-report security checkbox label."""
    pattern = re.compile(
        r"        - label: This is NOT a security vulnerability \(report those .+\)"
    )
    updated, count = pattern.subn(bug_security_checkbox_label(context), text)
    return updated, count


def replace_bug_report_severity_notice(
    text: str,
    context: ReplacementContext,
) -> tuple[str, int]:
    """Replace the bug-report severity-field security warning."""
    start = find_line_start(text, "For security vulnerabilities, do NOT use this form.")
    end = text.find("\n      options:", start)
    if start == -1 or end == -1:
        return text, 0
    return f"{text[:start]}{bug_severity_security_notice(context)}{text[end:]}", 1


def render_security_reporting_mode(
    file_texts: dict[str, str],
    context: ReplacementContext,
) -> tuple[ReplacementRecord, ...]:
    """Render known security-reporting surfaces for the selected mode."""
    renderers = {
        "SECURITY.md": (replace_security_reporting_section,),
        ".github/ISSUE_TEMPLATE/config.yml": (replace_config_security_block,),
        ".github/ISSUE_TEMPLATE/bug_report.yml": (
            replace_bug_report_security_notice,
            replace_bug_report_checkbox_label,
            replace_bug_report_severity_notice,
        ),
    }
    records: list[ReplacementRecord] = []
    for relative_path, path_renderers in renderers.items():
        if relative_path not in file_texts:
            continue
        text = file_texts[relative_path]
        replacement_count = 0
        for renderer in path_renderers:
            text, count = renderer(text, context)
            replacement_count += count
        if replacement_count:
            file_texts[relative_path] = text
            records.append(
                ReplacementRecord(
                    path=relative_path,
                    rule_name=f"security reporting mode {context.security_reporting_mode}",
                    count=replacement_count,
                )
            )
    return tuple(records)


def validate_context_against_retained_files(
    file_texts: dict[str, str],
    context: ReplacementContext,
) -> None:
    """Validate placeholder values that depend on retained file presence."""
    code_of_conduct = file_texts.get("CODE_OF_CONDUCT.md")
    if (
        code_of_conduct is not None
        and "[INSERT CONTACT METHOD]" in code_of_conduct
        and context.conduct_contact is None
    ):
        raise PlaceholderError(
            "CODE_OF_CONDUCT.md contains [INSERT CONTACT METHOD]; provide "
            "--conduct-contact when --security-contact is omitted."
        )


def build_replacement_rules(context: ReplacementContext) -> tuple[ReplacementRule, ...]:
    """Build the concrete allowlist of approved replacements."""
    rules: list[ReplacementRule] = []
    for suffix in sorted(APPROVED_GITHUB_URL_SUFFIXES, key=len, reverse=True):
        placeholder = f"https://github.com/OWNER/REPO{suffix}"
        replacement = f"https://{context.github_host}/{context.repository}{suffix}"
        rules.append(
            ReplacementRule(
                name=f"github url {suffix or '/'}",
                placeholder=placeholder,
                replacement=replacement,
                paths=GITHUB_URL_TOKEN_PATHS,
                replace=replace_url_pattern(placeholder, replacement),
            )
        )

    for name, placeholder, paths, attribute_name in TOKEN_REPLACEMENT_SPECS:
        replacement = getattr(context, attribute_name)
        if replacement is None:
            continue
        replace = (
            replace_owner_repo_token(context.repository)
            if placeholder == "OWNER/REPO"
            else replace_literal(placeholder, replacement)
        )
        rules.append(
            ReplacementRule(
                name=name,
                placeholder=placeholder,
                replacement=replacement,
                paths=paths,
                replace=replace,
            )
        )
    return tuple(rules)


def replace_placeholders(
    repo_root: Path,
    context: ReplacementContext,
    dry_run: bool = False,
) -> tuple[ReplacementRecord, ...]:
    """Replace approved placeholders in allowlisted files."""
    records: list[ReplacementRecord] = []
    rules = build_replacement_rules(context)
    files_by_path: dict[str, tuple[Path, str]] = {}
    for relative_path in GITHUB_URL_TOKEN_PATHS:
        files_by_path[relative_path] = (
            resolve_repo_path(repo_root, relative_path),
            relative_path,
        )
    for _name, _placeholder, paths, _attribute_name in TOKEN_REPLACEMENT_SPECS:
        for relative_path in paths:
            files_by_path[relative_path] = (
                resolve_repo_path(repo_root, relative_path),
                relative_path,
            )
    for rule in rules:
        for relative_path in rule.paths:
            files_by_path[relative_path] = (
                resolve_repo_path(repo_root, relative_path),
                relative_path,
            )

    file_texts: dict[str, str] = {}
    for relative_path, (path, display_path) in files_by_path.items():
        if not path.exists():
            continue
        if not path.is_file():
            raise PlaceholderError(f"{display_path}: expected a regular file.")
        file_texts[relative_path] = read_text(path, display_path)

    validate_context_against_retained_files(file_texts, context)
    records.extend(render_security_reporting_mode(file_texts, context))

    for rule in rules:
        for relative_path in rule.paths:
            if relative_path not in file_texts:
                continue
            updated_text, count = rule.replace(file_texts[relative_path])
            if count > 0:
                records.append(
                    ReplacementRecord(path=relative_path, rule_name=rule.name, count=count)
                )
                file_texts[relative_path] = updated_text

    if not dry_run:
        modified_paths = {record.path for record in records}
        for relative_path, text in file_texts.items():
            if relative_path not in modified_paths:
                continue
            path, display_path = files_by_path[relative_path]
            write_text(path, display_path, text)

    return tuple(records)


def build_unresolved_scan_patterns() -> (
    tuple[tuple[str, str, re.Pattern[str], tuple[str, ...]], ...]
):
    """Return unresolved placeholder scan patterns from the replacement allowlist."""
    patterns: list[tuple[str, str, re.Pattern[str], tuple[str, ...]]] = []
    for suffix in APPROVED_GITHUB_URL_SUFFIXES:
        placeholder = f"https://github.com/OWNER/REPO{suffix}"
        pattern = re.compile(rf"{re.escape(placeholder)}{URL_BOUNDARY_PATTERN}")
        patterns.append(
            (f"github url {suffix or '/'}", placeholder, pattern, GITHUB_URL_TOKEN_PATHS)
        )
    for name, placeholder, paths, _attribute_name in TOKEN_REPLACEMENT_SPECS:
        pattern = (
            OWNER_REPO_NON_PATH_SEGMENT_PATTERN
            if placeholder == "OWNER/REPO"
            else re.compile(re.escape(placeholder))
        )
        patterns.append((name, placeholder, pattern, paths))
    return tuple(patterns)


def iter_regex_matches(text: str, pattern: re.Pattern[str]) -> Iterable[tuple[int, str]]:
    """Yield ``(line_number, matched_text)`` for every regex match."""
    for line_number, line in enumerate(text.splitlines(), start=1):
        for match in pattern.finditer(line):
            yield line_number, match.group(0)


def scan_unresolved_placeholders(repo_root: Path) -> tuple[ScanFinding, ...]:
    """Scan allowlisted files for unresolved approved placeholders."""
    findings: list[ScanFinding] = []
    for name, placeholder, pattern, paths in build_unresolved_scan_patterns():
        for relative_path in paths:
            path = resolve_repo_path(repo_root, relative_path)
            if not path.exists():
                continue
            if not path.is_file():
                raise PlaceholderError(f"{relative_path}: expected a regular file.")
            text = read_text(path, relative_path)
            for line_number, matched_text in iter_regex_matches(text, pattern):
                findings.append(
                    ScanFinding(
                        kind="unresolved-placeholder",
                        path=relative_path,
                        line_number=line_number,
                        matched_text=matched_text,
                        message=f"replace approved placeholder '{name}'",
                    )
                )
    return tuple(findings)


def repository_relative_path(path: Path, repo_root: Path) -> str:
    """Return a POSIX-style path relative to the repository root."""
    return path.relative_to(repo_root).as_posix()


def iter_safe_repository_files(repo_root: Path) -> Iterable[tuple[str, Path]]:
    """Yield regular repository files without following symlinks."""
    root = repo_root.resolve()
    for current_root, dir_names, file_names in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current_root)
        retained_dir_names: list[str] = []
        for dir_name in dir_names:
            candidate = current_path / dir_name
            if dir_name in SKIPPED_DISCOVERY_DIRS or candidate.is_symlink():
                continue
            retained_dir_names.append(dir_name)
        dir_names[:] = retained_dir_names

        for file_name in file_names:
            file_path = current_path / file_name
            if file_path.is_symlink() or not file_path.is_file():
                continue
            resolved_file_path = file_path.resolve()
            try:
                resolved_file_path.relative_to(root)
            except ValueError:
                continue
            yield repository_relative_path(resolved_file_path, root), resolved_file_path


def build_corruption_patterns(repository: str) -> tuple[tuple[re.Pattern[str], str], ...]:
    """Return common broad-replacement corruption patterns for ``repository``."""
    _owner, repo = parse_repository(repository)
    escaped_repository = re.escape(repository)
    escaped_repo = re.escape(repo)
    return (
        (
            re.compile(f"{escaped_repository}RT"),
            "REPORT appears to have been changed by OWNER/REPO replacement",
        ),
        (
            re.compile(f"{escaped_repository}SITORY"),
            "REPOSITORY appears to have been changed by OWNER/REPO replacement",
        ),
        (
            re.compile(f"{escaped_repository}SITORIES"),
            "REPOSITORIES appears to have been changed by OWNER/REPO replacement",
        ),
        (
            re.compile(rf"(?<!/){escaped_repo}RT"),
            "REPORT appears to have been changed by broad REPO replacement",
        ),
        (
            re.compile(rf"(?<!/){escaped_repo}SITORY"),
            "REPOSITORY appears to have been changed by broad REPO replacement",
        ),
        (
            re.compile(rf"(?<!/){escaped_repo}SITORIES"),
            "REPOSITORIES appears to have been changed by broad REPO replacement",
        ),
    )


def scan_corruption_patterns(repo_root: Path, repository: str | None) -> tuple[ScanFinding, ...]:
    """Scan repository text files for common broad-replacement corruption."""
    if repository is None:
        return ()

    findings: list[ScanFinding] = []
    patterns = build_corruption_patterns(repository)
    for relative_path, path in iter_safe_repository_files(repo_root):
        try:
            text = path.read_bytes().decode("utf-8")
        except UnicodeDecodeError:
            continue
        except OSError as error:
            error_summary = f"{type(error).__name__}: {error.strerror or 'I/O error'}"
            raise PlaceholderError(
                f"{relative_path}: unable to read file ({error_summary})."
            ) from error

        for pattern, message in patterns:
            for line_number, matched_text in iter_regex_matches(text, pattern):
                findings.append(
                    ScanFinding(
                        kind="possible-corruption",
                        path=relative_path,
                        line_number=line_number,
                        matched_text=matched_text,
                        message=message,
                    )
                )
    return tuple(findings)


def scan_repository(repo_root: Path, repository: str | None = None) -> tuple[ScanFinding, ...]:
    """Scan for unresolved placeholders and common substitution corruption."""
    if repository is not None:
        parse_repository(repository)
    return scan_unresolved_placeholders(repo_root) + scan_corruption_patterns(repo_root, repository)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Replace and audit exact template placeholders.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    replace_parser = subparsers.add_parser("replace", help="replace approved placeholders")
    replace_parser.add_argument("--repo-root", default=None, help="repository root")
    replace_parser.add_argument("--repository", required=True, help="replacement OWNER/REPO value")
    replace_parser.add_argument(
        "--github-host",
        default="github.com",
        help="GitHub or GHES host for approved template URL contexts",
    )
    replace_parser.add_argument(
        "--codeowners-owner",
        default=None,
        help="replacement CODEOWNERS owner, e.g. @octocat or @org/team",
    )
    replace_parser.add_argument(
        "--conduct-contact",
        default=None,
        help=(
            "replacement Code of Conduct contact method; defaults to "
            "--security-contact when supplied"
        ),
    )
    replace_parser.add_argument(
        "--security-contact",
        default=None,
        help=(
            "replacement security contact method; required for contact-only and "
            "both security reporting modes"
        ),
    )
    replace_parser.add_argument(
        "--security-reporting-mode",
        choices=SECURITY_REPORTING_MODES,
        default=None,
        help=(
            "security reporting mode: github-private-only, contact-only, or both; "
            "omitting this while supplying --security-contact preserves the "
            "backward-compatible both mode"
        ),
    )
    replace_parser.add_argument(
        "--vscode-title",
        default=None,
        help="replacement VS Code window title; defaults to the repository name",
    )
    replace_parser.add_argument("--dry-run", action="store_true", help="report without writing")

    scan_parser = subparsers.add_parser("scan", help="scan for unresolved placeholders")
    scan_parser.add_argument("--repo-root", default=None, help="repository root")
    scan_parser.add_argument(
        "--repository",
        default=None,
        help="optional OWNER/REPO value used to detect common corruption patterns",
    )
    return parser.parse_args(argv)


def print_replacement_records(records: Iterable[ReplacementRecord]) -> None:
    """Print a replacement summary."""
    records = tuple(records)
    if not records:
        print("No approved placeholders were replaced.")
        return
    print("Approved placeholder replacements:")
    for record in records:
        print(f"  - {record.path}: {record.rule_name} ({record.count})")


def print_scan_findings(findings: Iterable[ScanFinding]) -> None:
    """Print scan findings."""
    findings = tuple(findings)
    if not findings:
        print("Placeholder scan passed.")
        return
    print("Placeholder scan found issues:")
    for finding in findings:
        print(f"  - {finding.format_message()}")


def run_replace(args: argparse.Namespace) -> int:
    """Run the replacement command."""
    repo_root = resolve_repo_root(args.repo_root)
    context = build_replacement_context(
        repository=args.repository,
        github_host=args.github_host,
        codeowners_owner=args.codeowners_owner,
        conduct_contact=args.conduct_contact,
        security_contact=args.security_contact,
        security_reporting_mode=args.security_reporting_mode,
        vscode_title=args.vscode_title,
    )
    records = replace_placeholders(repo_root=repo_root, context=context, dry_run=args.dry_run)
    print_replacement_records(records)

    if args.dry_run:
        return 0

    findings = scan_repository(repo_root=repo_root, repository=context.repository)
    print_scan_findings(findings)
    return 1 if findings else 0


def run_scan(args: argparse.Namespace) -> int:
    """Run the scan command."""
    repo_root = resolve_repo_root(args.repo_root)
    findings = scan_repository(repo_root=repo_root, repository=args.repository)
    print_scan_findings(findings)
    return 1 if findings else 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the placeholder helper CLI."""
    args = parse_args(argv)
    try:
        if args.command == "replace":
            return run_replace(args)
        if args.command == "scan":
            return run_scan(args)
    except PlaceholderError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
