"""Replace and audit template placeholders through an explicit allowlist.

The helper intentionally avoids broad ``REPO`` or ``github.com`` replacement.
Only the placeholder tokens and GitHub URL shapes defined in this file are
eligible for substitution.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import re
import shlex
import sys
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote, urlsplit, urlunsplit

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
ISSUE_LABEL_POLICIES = ("existing", "create-manual-follow-up", "omit", "custom")
DISCUSSIONS_POLICIES = (
    "enabled",
    "disabled",
    "deferred-planned-render",
    "deferred-not-rendered",
)
ISSUE_LABEL_FOLLOW_UP_POLICIES = frozenset({"create-manual-follow-up"})
DISCUSSIONS_FOLLOW_UP_POLICIES = frozenset({"deferred-planned-render", "deferred-not-rendered"})
DEFAULT_ISSUE_LABELS = ("bug", "triage")
HOST_PROVIDERS = (
    "github",
    "github-enterprise-server",
    "azure-devops-services",
    "dual",
)
GITHUB_HOST_PROVIDERS = frozenset({"github", "github-enterprise-server", "dual"})
AZURE_DEVOPS_HOST_PROVIDERS = frozenset({"azure-devops-services", "dual"})
AZURE_DEVOPS_URL_TOKEN_PATHS = (
    ".azuredevops/platform/adoption-guidance.md",
    ".azuredevops/pull_request_template.md",
)
AZURE_DEVOPS_TOKEN_REPLACEMENT_SPECS = (
    ("azure devops organization", "AZURE_DEVOPS_ORGANIZATION", "organization"),
    ("azure devops organization url", "AZURE_DEVOPS_ORGANIZATION_URL", "organization_url"),
    ("azure devops project", "AZURE_DEVOPS_PROJECT", "project"),
    ("azure devops project url", "AZURE_DEVOPS_PROJECT_URL", "project_url"),
    ("azure devops repository", "AZURE_DEVOPS_REPOSITORY", "repository"),
    (
        "azure devops repository url",
        "AZURE_DEVOPS_REPOSITORY_WEB_URL",
        "repository_web_url",
    ),
    ("azure devops clone url", "AZURE_DEVOPS_CLONE_URL", "clone_url"),
    ("azure devops default branch", "AZURE_DEVOPS_DEFAULT_BRANCH", "default_branch"),
    ("azure boards policy", "AZURE_BOARDS_INTAKE_POLICY", "boards_policy"),
    (
        "azure repos pr template policy",
        "AZURE_REPOS_PR_TEMPLATE_POLICY",
        "pr_template_policy",
    ),
    (
        "azure branch policy reviewer guidance",
        "AZURE_BRANCH_POLICY_REVIEWER_GUIDANCE",
        "branch_policy_reviewer_guidance",
    ),
    (
        "azure security intake policy",
        "AZURE_SECURITY_INTAKE_POLICY",
        "security_intake_policy",
    ),
    (
        "azure security product enablement",
        "AZURE_SECURITY_PRODUCT_ENABLEMENT",
        "security_product_enablement",
    ),
    (
        "azure dependency update policy",
        "AZURE_DEPENDENCY_UPDATE_POLICY",
        "dependency_update_policy",
    ),
)
AZURE_DEVOPS_BOARDS_POLICIES = ("work-items", "disabled", "manual-follow-up")
AZURE_DEVOPS_PR_TEMPLATE_POLICIES = ("materialize", "disabled", "manual-follow-up")
AZURE_DEVOPS_BRANCH_POLICY_POLICIES = ("required-reviewers", "manual-follow-up", "none")
AZURE_DEVOPS_SECURITY_INTAKE_POLICIES = ("security-contact", "external-process", "manual-follow-up")
AZURE_DEVOPS_SECURITY_PRODUCT_POLICIES = (
    "none",
    "github-advanced-security",
    "github-secret-protection",
    "github-code-security",
    "github-secret-protection-and-code-security",
)
AZURE_DEVOPS_DEPENDENCY_UPDATE_POLICIES = ("none", "renovate", "manual-follow-up")
AZURE_DEVOPS_ARGS_FILE_FIELDS = frozenset(
    {
        "host_provider",
        "azure_devops_organization",
        "azure_devops_organization_url",
        "azure_devops_project",
        "azure_devops_project_url",
        "azure_devops_repository",
        "azure_devops_repository_url",
        "azure_devops_clone_url",
        "azure_devops_default_branch",
        "azure_boards_policy",
        "azure_repos_pr_template_policy",
        "azure_branch_policy_reviewer_guidance",
        "azure_security_intake_policy",
        "azure_security_product_enablement",
        "azure_dependency_update_policy",
    }
)
ARGS_FILE_FORMATS = ("json", "yaml")
ARGS_FILE_EXTENSION_FORMATS = {
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
}
PACKAGE_METADATA_PATHS = ("package.json", "package-lock.json")
CONDUCT_CONTACT_SENTENCE_PLACEHOLDER = (
    "To report a possible violation, contact us via: [INSERT CONTACT METHOD]"
)
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
REPLACE_ARGS_FILE_FIELDS = (
    frozenset(
        {
            "repo_root",
            "repository",
            "github_host",
            "codeowners_owner",
            "conduct_contact",
            "conduct_contact_sentence",
            "security_contact",
            "security_contact_section",
            "security_reporting_mode",
            "issue_label_policy",
            "issue_labels",
            "discussions_policy",
            "collaboration_policy_follow_up_status",
            "vscode_title",
            "package_name",
            "package_description",
            "package_author",
            "package_version",
            "package_keywords",
            "dry_run",
        }
    )
    | AZURE_DEVOPS_ARGS_FILE_FIELDS
)
SCAN_ARGS_FILE_FIELDS = frozenset({"repo_root", "repository"})
STRING_ARGS_FILE_FIELDS = (
    frozenset(
        {
            "repo_root",
            "repository",
            "github_host",
            "codeowners_owner",
            "conduct_contact",
            "conduct_contact_sentence",
            "security_contact",
            "security_contact_section",
            "security_reporting_mode",
            "issue_label_policy",
            "discussions_policy",
            "collaboration_policy_follow_up_status",
            "vscode_title",
            "package_name",
            "package_description",
            "package_author",
            "package_version",
        }
    )
    | AZURE_DEVOPS_ARGS_FILE_FIELDS
)
LIST_STRING_ARGS_FILE_FIELDS = frozenset({"issue_labels", "package_keywords"})
BOOLEAN_ARGS_FILE_FIELDS = frozenset({"dry_run"})
REPLACE_CLI_FLAGS = {
    "repo_root": ("--repo-root",),
    "host_provider": ("--host-provider",),
    "repository": ("--repository",),
    "github_host": ("--github-host",),
    "codeowners_owner": ("--codeowners-owner",),
    "conduct_contact": ("--conduct-contact",),
    "conduct_contact_sentence": ("--conduct-contact-sentence",),
    "security_contact": ("--security-contact",),
    "security_contact_section": ("--security-contact-section",),
    "security_reporting_mode": ("--security-reporting-mode",),
    "issue_label_policy": ("--issue-label-policy",),
    "issue_labels": ("--issue-label",),
    "discussions_policy": ("--discussions-policy",),
    "collaboration_policy_follow_up_status": ("--collaboration-policy-follow-up-status",),
    "vscode_title": ("--vscode-title",),
    "package_name": ("--package-name",),
    "package_description": ("--package-description",),
    "package_author": ("--package-author",),
    "package_version": ("--package-version",),
    "package_keywords": ("--package-keyword",),
    "dry_run": ("--dry-run",),
    "azure_devops_organization": ("--azure-devops-organization",),
    "azure_devops_organization_url": ("--azure-devops-organization-url",),
    "azure_devops_project": ("--azure-devops-project",),
    "azure_devops_project_url": ("--azure-devops-project-url",),
    "azure_devops_repository": ("--azure-devops-repository",),
    "azure_devops_repository_url": ("--azure-devops-repository-url",),
    "azure_devops_clone_url": ("--azure-devops-clone-url",),
    "azure_devops_default_branch": ("--azure-devops-default-branch",),
    "azure_boards_policy": ("--azure-boards-policy",),
    "azure_repos_pr_template_policy": ("--azure-repos-pr-template-policy",),
    "azure_branch_policy_reviewer_guidance": ("--azure-branch-policy-reviewer-guidance",),
    "azure_security_intake_policy": ("--azure-security-intake-policy",),
    "azure_security_product_enablement": ("--azure-security-product-enablement",),
    "azure_dependency_update_policy": ("--azure-dependency-update-policy",),
}
SCAN_CLI_FLAGS = {
    "repo_root": ("--repo-root",),
    "repository": ("--repository",),
}
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
INVALID_PERCENT_ENCODING_PATTERN = re.compile(r"%(?![0-9A-Fa-f]{2})")


class PlaceholderError(RuntimeError):
    """Raised when placeholder substitution or scanning cannot complete."""


@dataclass(frozen=True)
class AzureDevOpsContext:
    """Concrete Azure DevOps Services values used during substitution."""

    organization: str
    organization_url: str
    project: str
    project_url: str
    repository: str
    repository_web_url: str
    clone_url: str
    default_branch: str
    boards_policy: str
    pr_template_policy: str
    branch_policy_reviewer_guidance: str
    security_intake_policy: str
    security_product_enablement: str
    dependency_update_policy: str


@dataclass(frozen=True)
class ReplacementContext:
    """Concrete downstream values used during placeholder substitution."""

    host_provider: str
    repository: str | None
    github_host: str
    azure_devops: AzureDevOpsContext | None
    codeowners_owner: str | None
    conduct_contact: str | None
    conduct_contact_sentence: str | None
    security_contact: str | None
    security_contact_section: str | None
    security_reporting_mode: str | None
    issue_label_policy: str | None
    issue_labels: tuple[str, ...] | None
    discussions_policy: str | None
    collaboration_policy_follow_up_status: str | None
    vscode_title: str | None
    package_name: str | None
    package_description: str | None
    package_author: str | None
    package_version: str | None
    package_keywords: tuple[str, ...] | None

    @property
    def security_todo_replacement(self) -> str | None:
        """Return the security-contact TODO replacement, or None when no security decision was made.

        Returns None when the run supplied no security inputs at all (no reporting
        mode, security contact, or contact section), so the SECURITY.md TODO marker is
        left intact instead of being rewritten as an intentional omission for a run --
        such as a repository-less or package-metadata-only run -- that made no security
        decision. The marker is only rewritten when the run actually configures a
        security contact or selects a reporting mode that intentionally omits one.
        """
        if (
            self.security_contact is None
            and self.security_contact_section is None
            and self.security_reporting_mode is None
        ):
            return None
        if self.security_contact is None and self.security_contact_section is None:
            return "<!-- Security contact intentionally omitted by reporting mode -->"
        return "<!-- Security contact configured -->"

    @property
    def has_package_metadata(self) -> bool:
        """Return whether package metadata replacement was requested."""
        return any(
            value is not None
            for value in (
                self.package_name,
                self.package_description,
                self.package_author,
                self.package_version,
                self.package_keywords,
            )
        )

    @property
    def has_collaboration_policy(self) -> bool:
        """Return whether issue/PR collaboration policy rendering was requested."""
        return self.issue_label_policy is not None or self.discussions_policy is not None

    @property
    def uses_github_surfaces(self) -> bool:
        """Return whether GitHub-specific repository surfaces are in scope."""
        return self.host_provider in GITHUB_HOST_PROVIDERS


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


def validate_optional_non_empty(value: str | None, field_name: str) -> str | None:
    """Validate an optional non-empty CLI value."""
    if value is None:
        return None
    return validate_non_empty(value, field_name)


def validate_single_line_non_empty(value: str, field_name: str) -> str:
    """Validate a required non-empty CLI value that must fit on one line."""
    validated = validate_non_empty(value, field_name)
    if "\n" in validated or "\r" in validated:
        raise PlaceholderError(f"{field_name} must be a single-line value.")
    return validated


def validate_choice(value: str, field_name: str, choices: Sequence[str]) -> str:
    """Validate a CLI enum value against an explicit list of choices."""
    if value not in choices:
        quoted_choices = ", ".join(choices)
        raise PlaceholderError(f"{field_name} must be one of: {quoted_choices}.")
    return value


def validate_host_provider(host_provider: str) -> str:
    """Validate a host-provider mode name."""
    return validate_choice(host_provider, "--host-provider", HOST_PROVIDERS)


def validate_azure_devops_segment(value: str, field_name: str) -> str:
    """Validate an Azure DevOps path segment before URL generation."""
    validated = validate_single_line_non_empty(value, field_name)
    if validated != validated.strip():
        raise PlaceholderError(f"{field_name} must not include leading or trailing whitespace.")
    if "/" in validated or "\\" in validated:
        raise PlaceholderError(f"{field_name} must be one Azure DevOps path segment.")
    if any(ord(character) < 32 for character in validated):
        raise PlaceholderError(f"{field_name} must not contain control characters.")
    return validated


def quote_azure_devops_segment(value: str) -> str:
    """Percent-encode one Azure DevOps URL path segment."""
    return quote(value, safe="")


def validate_azure_devops_url(raw_url: str, field_name: str) -> Any:
    """Parse and validate a credential-free Azure DevOps Services URL."""
    url = validate_single_line_non_empty(raw_url, field_name)
    if re.search(r"\s", url):
        raise PlaceholderError(
            f"{field_name} must not contain whitespace; percent-encode spaces as %20."
        )
    if INVALID_PERCENT_ENCODING_PATTERN.search(url):
        raise PlaceholderError(f"{field_name} contains malformed percent encoding.")
    parts = urlsplit(url)
    if parts.scheme.lower() != "https":
        raise PlaceholderError(f"{field_name} must use https.")
    if not parts.netloc or parts.hostname is None:
        raise PlaceholderError(f"{field_name} must include a host.")
    try:
        _port = parts.port
    except ValueError as error:
        raise PlaceholderError(f"{field_name} contains an invalid port.") from error
    if parts.username is not None or parts.password is not None or "@" in parts.netloc:
        raise PlaceholderError(f"{field_name} must not contain embedded credentials.")
    if parts.query or parts.fragment:
        raise PlaceholderError(f"{field_name} must not include a query string or fragment.")
    return parts


def azure_devops_host_kind(parts: Any, field_name: str) -> str:
    """Return the recognized Azure DevOps Services host shape."""
    hostname = parts.hostname.lower()
    if hostname == "dev.azure.com":
        return "dev.azure.com"
    if hostname.endswith(".visualstudio.com") and hostname != "visualstudio.com":
        return "visualstudio.com"
    raise PlaceholderError(
        f"{field_name} must use https://dev.azure.com/<organization> or "
        "https://<organization>.visualstudio.com."
    )


def azure_devops_path_segments(parts: Any, field_name: str) -> tuple[str, ...]:
    """Return decoded Azure DevOps URL path segments after structural validation."""
    path = parts.path.strip("/")
    if not path:
        return ()
    segments = tuple(path.split("/"))
    if any(segment == "" for segment in segments):
        raise PlaceholderError(f"{field_name} must not include empty path segments.")
    return tuple(unquote(segment) for segment in segments)


def normalize_azure_devops_url(parts: Any) -> str:
    """Return an Azure DevOps URL without query, fragment, or trailing slash."""
    normalized_path = parts.path.rstrip("/")
    return urlunsplit(("https", parts.netloc, normalized_path, "", ""))


def validate_azure_devops_organization_url(raw_url: str, organization: str) -> str:
    """Validate an Azure DevOps Services organization URL."""
    parts = validate_azure_devops_url(raw_url, "--azure-devops-organization-url")
    host_kind = azure_devops_host_kind(parts, "--azure-devops-organization-url")
    segments = azure_devops_path_segments(parts, "--azure-devops-organization-url")
    if host_kind == "dev.azure.com":
        if len(segments) != 1 or segments[0].casefold() != organization.casefold():
            raise PlaceholderError(
                "--azure-devops-organization-url must use the selected organization "
                "as its only path segment."
            )
    else:
        account_name = parts.hostname[: -len(".visualstudio.com")]
        if segments or account_name.casefold() != organization.casefold():
            raise PlaceholderError(
                "--azure-devops-organization-url must use the selected organization "
                "as the visualstudio.com account name and must not include a path."
            )
    return normalize_azure_devops_url(parts)


def validate_azure_devops_project_url(
    raw_url: str,
    *,
    organization: str,
    project: str,
) -> str:
    """Validate an Azure DevOps Services project URL override."""
    parts = validate_azure_devops_url(raw_url, "--azure-devops-project-url")
    host_kind = azure_devops_host_kind(parts, "--azure-devops-project-url")
    segments = azure_devops_path_segments(parts, "--azure-devops-project-url")
    if host_kind == "dev.azure.com":
        if len(segments) != 2 or (
            segments[0].casefold() != organization.casefold() or segments[1] != project
        ):
            raise PlaceholderError(
                "--azure-devops-project-url must use the selected organization and project path."
            )
    else:
        account_name = parts.hostname[: -len(".visualstudio.com")]
        if (
            len(segments) != 1
            or account_name.casefold() != organization.casefold()
            or segments[0] != project
        ):
            raise PlaceholderError(
                "--azure-devops-project-url must use the selected organization "
                "account and project path."
            )
    return normalize_azure_devops_url(parts)


def validate_azure_devops_repository_url(
    raw_url: str,
    *,
    organization: str,
    project: str,
    repository: str,
    field_name: str,
) -> str:
    """Validate an Azure Repos repository or clone URL override."""
    parts = validate_azure_devops_url(raw_url, field_name)
    host_kind = azure_devops_host_kind(parts, field_name)
    segments = azure_devops_path_segments(parts, field_name)
    if host_kind == "dev.azure.com":
        expected = (organization, project, "_git", repository)
        if len(segments) != 4 or (
            segments[0].casefold() != expected[0].casefold() or segments[1:] != expected[1:]
        ):
            raise PlaceholderError(
                f"{field_name} must use the selected organization, project, "
                "and repository under /_git/."
            )
    else:
        account_name = parts.hostname[: -len(".visualstudio.com")]
        if (
            len(segments) != 3
            or account_name.casefold() != organization.casefold()
            or segments != (project, "_git", repository)
        ):
            raise PlaceholderError(
                f"{field_name} must use the selected organization account, project, "
                "and repository under /_git/."
            )
    return normalize_azure_devops_url(parts)


def build_azure_devops_url(base_url: str, *segments: str) -> str:
    """Build an Azure DevOps Services URL from a validated base and path segments."""
    encoded_segments = "/".join(quote_azure_devops_segment(segment) for segment in segments)
    return f"{base_url.rstrip('/')}/{encoded_segments}"


def validate_azure_policy(
    value: str | None,
    *,
    field_name: str,
    default: str,
    choices: Sequence[str],
) -> str:
    """Validate or default one Azure DevOps policy selector."""
    return default if value is None else validate_choice(value, field_name, choices)


def azure_devops_inputs_supplied(values: dict[str, str | None]) -> bool:
    """Return whether any Azure DevOps provider value was supplied."""
    return any(value is not None for value in values.values())


def github_only_inputs_supplied(
    *,
    repository: str | None,
    github_host: str,
    codeowners_owner: str | None,
    issue_label_policy: str | None,
    issue_labels: Sequence[str] | None,
    discussions_policy: str | None,
) -> bool:
    """Return whether GitHub-specific replacement inputs were supplied."""
    return (
        repository is not None
        or github_host != "github.com"
        or codeowners_owner is not None
        or issue_label_policy is not None
        or issue_labels is not None
        or discussions_policy is not None
    )


def resolve_host_provider(
    host_provider: str | None,
    *,
    azure_inputs: dict[str, str | None],
    repository: str | None,
    github_host: str,
    codeowners_owner: str | None,
    issue_label_policy: str | None,
    issue_labels: Sequence[str] | None,
    discussions_policy: str | None,
) -> str:
    """Resolve the host-provider mode while preserving backward compatibility."""
    if host_provider is not None:
        return validate_host_provider(host_provider)
    if azure_devops_inputs_supplied(azure_inputs):
        if github_only_inputs_supplied(
            repository=repository,
            github_host=github_host,
            codeowners_owner=codeowners_owner,
            issue_label_policy=issue_label_policy,
            issue_labels=issue_labels,
            discussions_policy=discussions_policy,
        ):
            raise PlaceholderError(
                "Azure DevOps and GitHub-specific inputs were both supplied; "
                "set --host-provider dual when both hosts are intentional."
            )
        return "azure-devops-services"
    return "github"


def validate_provider_inputs(
    *,
    host_provider: str,
    azure_inputs: dict[str, str | None],
    repository: str | None,
    github_host: str,
    codeowners_owner: str | None,
    issue_label_policy: str | None,
    issue_labels: Sequence[str] | None,
    discussions_policy: str | None,
    security_reporting_mode: str | None,
) -> None:
    """Reject host-provider combinations that would render incompatible surfaces."""
    if host_provider in {"github", "github-enterprise-server"} and azure_devops_inputs_supplied(
        azure_inputs
    ):
        raise PlaceholderError(
            "Azure DevOps provider fields require --host-provider azure-devops-services "
            "or --host-provider dual."
        )
    if host_provider == "dual" and repository is None:
        raise PlaceholderError("--host-provider dual requires --repository for GitHub surfaces.")
    if host_provider != "azure-devops-services":
        return

    incompatible_inputs: list[str] = []
    if repository is not None:
        incompatible_inputs.append("--repository")
    if github_host != "github.com":
        incompatible_inputs.append("--github-host")
    if codeowners_owner is not None:
        incompatible_inputs.append("--codeowners-owner")
    if issue_label_policy is not None or issue_labels is not None:
        incompatible_inputs.append("--issue-label-policy/--issue-label")
    if discussions_policy is not None:
        incompatible_inputs.append("--discussions-policy")
    if security_reporting_mode is not None:
        # SECURITY.md rendering for Azure-only adoptions is driven by
        # --azure-security-intake-policy/--security-contact, so any
        # --security-reporting-mode value (including contact-only) is a no-op here.
        incompatible_inputs.append("--security-reporting-mode")
    if incompatible_inputs:
        raise PlaceholderError(
            "--host-provider azure-devops-services cannot be combined with "
            "GitHub-specific inputs: "
            + ", ".join(incompatible_inputs)
            + ". Use --host-provider dual when both hosts are intentional."
        )


def build_azure_devops_context(
    *,
    host_provider: str,
    azure_devops_organization: str | None,
    azure_devops_organization_url: str | None,
    azure_devops_project: str | None,
    azure_devops_project_url: str | None,
    azure_devops_repository: str | None,
    azure_devops_repository_url: str | None,
    azure_devops_clone_url: str | None,
    azure_devops_default_branch: str | None,
    azure_boards_policy: str | None,
    azure_repos_pr_template_policy: str | None,
    azure_branch_policy_reviewer_guidance: str | None,
    azure_security_intake_policy: str | None,
    azure_security_product_enablement: str | None,
    azure_dependency_update_policy: str | None,
    security_contact: str | None,
    security_contact_section: str | None,
) -> AzureDevOpsContext | None:
    """Build validated Azure DevOps Services context when the provider requires it."""
    if host_provider not in AZURE_DEVOPS_HOST_PROVIDERS:
        return None
    if azure_devops_organization is None:
        raise PlaceholderError(
            "--azure-devops-organization is required for Azure DevOps Services adoption."
        )
    if azure_devops_project is None:
        raise PlaceholderError("--azure-devops-project is required for Azure DevOps adoption.")
    if azure_devops_repository is None:
        raise PlaceholderError("--azure-devops-repository is required for Azure Repos adoption.")

    organization = validate_azure_devops_segment(
        azure_devops_organization,
        "--azure-devops-organization",
    )
    project = validate_azure_devops_segment(azure_devops_project, "--azure-devops-project")
    repository = validate_azure_devops_segment(
        azure_devops_repository,
        "--azure-devops-repository",
    )
    organization_url = (
        validate_azure_devops_organization_url(azure_devops_organization_url, organization)
        if azure_devops_organization_url is not None
        else build_azure_devops_url("https://dev.azure.com", organization)
    )
    project_url = (
        validate_azure_devops_project_url(
            azure_devops_project_url,
            organization=organization,
            project=project,
        )
        if azure_devops_project_url is not None
        else build_azure_devops_url(organization_url, project)
    )
    repository_web_url = (
        validate_azure_devops_repository_url(
            azure_devops_repository_url,
            organization=organization,
            project=project,
            repository=repository,
            field_name="--azure-devops-repository-url",
        )
        if azure_devops_repository_url is not None
        else build_azure_devops_url(organization_url, project, "_git", repository)
    )
    clone_url = (
        validate_azure_devops_repository_url(
            azure_devops_clone_url,
            organization=organization,
            project=project,
            repository=repository,
            field_name="--azure-devops-clone-url",
        )
        if azure_devops_clone_url is not None
        else repository_web_url
    )
    security_intake_default = (
        "security-contact"
        if security_contact is not None or security_contact_section is not None
        else "manual-follow-up"
    )
    security_intake_policy_value = validate_azure_policy(
        azure_security_intake_policy,
        field_name="--azure-security-intake-policy",
        default=security_intake_default,
        choices=AZURE_DEVOPS_SECURITY_INTAKE_POLICIES,
    )
    return AzureDevOpsContext(
        organization=organization,
        organization_url=organization_url,
        project=project,
        project_url=project_url,
        repository=repository,
        repository_web_url=repository_web_url,
        clone_url=clone_url,
        default_branch=validate_single_line_non_empty(
            azure_devops_default_branch or "main",
            "--azure-devops-default-branch",
        ),
        boards_policy=validate_azure_policy(
            azure_boards_policy,
            field_name="--azure-boards-policy",
            default="manual-follow-up",
            choices=AZURE_DEVOPS_BOARDS_POLICIES,
        ),
        pr_template_policy=validate_azure_policy(
            azure_repos_pr_template_policy,
            field_name="--azure-repos-pr-template-policy",
            default="materialize",
            choices=AZURE_DEVOPS_PR_TEMPLATE_POLICIES,
        ),
        branch_policy_reviewer_guidance=validate_azure_policy(
            azure_branch_policy_reviewer_guidance,
            field_name="--azure-branch-policy-reviewer-guidance",
            default="manual-follow-up",
            choices=AZURE_DEVOPS_BRANCH_POLICY_POLICIES,
        ),
        security_intake_policy=security_intake_policy_value,
        security_product_enablement=validate_azure_policy(
            azure_security_product_enablement,
            field_name="--azure-security-product-enablement",
            default="none",
            choices=AZURE_DEVOPS_SECURITY_PRODUCT_POLICIES,
        ),
        dependency_update_policy=validate_azure_policy(
            azure_dependency_update_policy,
            field_name="--azure-dependency-update-policy",
            default="none",
            choices=AZURE_DEVOPS_DEPENDENCY_UPDATE_POLICIES,
        ),
    )


def validate_package_keywords(package_keywords: Sequence[str] | None) -> tuple[str, ...] | None:
    """Validate optional package keyword metadata."""
    if package_keywords is None:
        return None
    validated_keywords = tuple(
        validate_non_empty(keyword, "--package-keyword") for keyword in package_keywords
    )
    if not validated_keywords:
        raise PlaceholderError("--package-keyword must be supplied at least once when present.")
    return validated_keywords


def validate_security_reporting_mode(security_reporting_mode: str) -> str:
    """Validate a security-reporting mode name."""
    if security_reporting_mode not in SECURITY_REPORTING_MODES:
        quoted_modes = ", ".join(SECURITY_REPORTING_MODES)
        raise PlaceholderError(f"--security-reporting-mode must be one of: {quoted_modes}.")
    return security_reporting_mode


def validate_issue_label_policy(issue_label_policy: str) -> str:
    """Validate an issue-label policy name."""
    if issue_label_policy not in ISSUE_LABEL_POLICIES:
        quoted_policies = ", ".join(ISSUE_LABEL_POLICIES)
        raise PlaceholderError(f"--issue-label-policy must be one of: {quoted_policies}.")
    return issue_label_policy


def validate_discussions_policy(discussions_policy: str) -> str:
    """Validate a Discussions contact-link policy name."""
    if discussions_policy not in DISCUSSIONS_POLICIES:
        quoted_policies = ", ".join(DISCUSSIONS_POLICIES)
        raise PlaceholderError(f"--discussions-policy must be one of: {quoted_policies}.")
    return discussions_policy


def validate_issue_labels(issue_labels: Sequence[str] | None) -> tuple[str, ...] | None:
    """Validate optional issue labels for the custom issue-label policy."""
    if issue_labels is None:
        return None
    validated_labels = tuple(validate_non_empty(label, "--issue-label") for label in issue_labels)
    if not validated_labels:
        raise PlaceholderError("--issue-label must be supplied at least once when present.")
    invalid_labels = [label for label in validated_labels if "\n" in label or "\r" in label]
    if invalid_labels:
        raise PlaceholderError("--issue-label values must be single-line labels.")
    return validated_labels


def resolve_issue_label_policy(
    *,
    issue_label_policy: str | None,
    issue_labels: tuple[str, ...] | None,
) -> str | None:
    """Resolve the label policy, inferring custom when labels are supplied."""
    if issue_label_policy is None:
        return "custom" if issue_labels is not None else None
    resolved_policy = validate_issue_label_policy(issue_label_policy)
    if resolved_policy == "custom" and issue_labels is None:
        raise PlaceholderError("--issue-label-policy custom requires at least one --issue-label.")
    if resolved_policy != "custom" and issue_labels is not None:
        raise PlaceholderError("--issue-label can only be used with --issue-label-policy custom.")
    return resolved_policy


def validate_collaboration_policy_follow_up(
    *,
    issue_label_policy: str | None,
    discussions_policy: str | None,
    collaboration_policy_follow_up_status: str | None,
) -> str | None:
    """Validate follow-up status for policies that leave manual setup open."""
    follow_up_status = validate_optional_non_empty(
        collaboration_policy_follow_up_status,
        "--collaboration-policy-follow-up-status",
    )
    needs_follow_up = (
        issue_label_policy in ISSUE_LABEL_FOLLOW_UP_POLICIES
        or discussions_policy in DISCUSSIONS_FOLLOW_UP_POLICIES
    )
    if needs_follow_up and follow_up_status is None:
        raise PlaceholderError(
            "--collaboration-policy-follow-up-status is required when "
            "--issue-label-policy is create-manual-follow-up or "
            "--discussions-policy is deferred-planned-render/deferred-not-rendered; "
            "record the matching _TODO-repo-init.md dependent-file status."
        )
    return follow_up_status


def resolve_security_reporting_mode(
    *,
    security_reporting_mode: str | None,
    security_contact: str | None,
    security_contact_section: str | None,
    require_security_decision: bool,
) -> str:
    """Resolve explicit and backward-compatible security-reporting mode input."""
    if security_reporting_mode is None:
        if not require_security_decision:
            return "both"
        if security_contact is None and security_contact_section is None:
            raise PlaceholderError(
                "Either --security-reporting-mode or --security-contact is required; "
                "--security-contact-section may be used instead of --security-contact."
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
    host_provider: str | None = None,
    repository: str | None = None,
    github_host: str = "github.com",
    azure_devops_organization: str | None = None,
    azure_devops_organization_url: str | None = None,
    azure_devops_project: str | None = None,
    azure_devops_project_url: str | None = None,
    azure_devops_repository: str | None = None,
    azure_devops_repository_url: str | None = None,
    azure_devops_clone_url: str | None = None,
    azure_devops_default_branch: str | None = None,
    azure_boards_policy: str | None = None,
    azure_repos_pr_template_policy: str | None = None,
    azure_branch_policy_reviewer_guidance: str | None = None,
    azure_security_intake_policy: str | None = None,
    azure_security_product_enablement: str | None = None,
    azure_dependency_update_policy: str | None = None,
    codeowners_owner: str | None = None,
    conduct_contact: str | None = None,
    conduct_contact_sentence: str | None = None,
    security_contact: str | None = None,
    security_contact_section: str | None = None,
    security_reporting_mode: str | None = None,
    issue_label_policy: str | None = None,
    issue_labels: Sequence[str] | None = None,
    discussions_policy: str | None = None,
    collaboration_policy_follow_up_status: str | None = None,
    vscode_title: str | None = None,
    package_name: str | None = None,
    package_description: str | None = None,
    package_author: str | None = None,
    package_version: str | None = None,
    package_keywords: Sequence[str] | None = None,
) -> ReplacementContext:
    """Return validated replacement values for the helper."""
    owner: str | None = None
    repo: str | None = None
    if repository is not None:
        owner, repo = parse_repository(repository)
    azure_inputs = {
        "azure_devops_organization": azure_devops_organization,
        "azure_devops_organization_url": azure_devops_organization_url,
        "azure_devops_project": azure_devops_project,
        "azure_devops_project_url": azure_devops_project_url,
        "azure_devops_repository": azure_devops_repository,
        "azure_devops_repository_url": azure_devops_repository_url,
        "azure_devops_clone_url": azure_devops_clone_url,
        "azure_devops_default_branch": azure_devops_default_branch,
        "azure_boards_policy": azure_boards_policy,
        "azure_repos_pr_template_policy": azure_repos_pr_template_policy,
        "azure_branch_policy_reviewer_guidance": azure_branch_policy_reviewer_guidance,
        "azure_security_intake_policy": azure_security_intake_policy,
        "azure_security_product_enablement": azure_security_product_enablement,
        "azure_dependency_update_policy": azure_dependency_update_policy,
    }
    resolved_host_provider = resolve_host_provider(
        host_provider,
        azure_inputs=azure_inputs,
        repository=repository,
        github_host=github_host,
        codeowners_owner=codeowners_owner,
        issue_label_policy=issue_label_policy,
        issue_labels=issue_labels,
        discussions_policy=discussions_policy,
    )
    validate_provider_inputs(
        host_provider=resolved_host_provider,
        azure_inputs=azure_inputs,
        repository=repository,
        github_host=github_host,
        codeowners_owner=codeowners_owner,
        issue_label_policy=issue_label_policy,
        issue_labels=issue_labels,
        discussions_policy=discussions_policy,
        security_reporting_mode=security_reporting_mode,
    )
    validated_security_contact = (
        validate_non_empty(security_contact, "--security-contact")
        if security_contact is not None
        else None
    )
    validated_security_contact_section = validate_optional_non_empty(
        security_contact_section,
        "--security-contact-section",
    )
    azure_context = build_azure_devops_context(
        host_provider=resolved_host_provider,
        azure_devops_organization=azure_devops_organization,
        azure_devops_organization_url=azure_devops_organization_url,
        azure_devops_project=azure_devops_project,
        azure_devops_project_url=azure_devops_project_url,
        azure_devops_repository=azure_devops_repository,
        azure_devops_repository_url=azure_devops_repository_url,
        azure_devops_clone_url=azure_devops_clone_url,
        azure_devops_default_branch=azure_devops_default_branch,
        azure_boards_policy=azure_boards_policy,
        azure_repos_pr_template_policy=azure_repos_pr_template_policy,
        azure_branch_policy_reviewer_guidance=azure_branch_policy_reviewer_guidance,
        azure_security_intake_policy=azure_security_intake_policy,
        azure_security_product_enablement=azure_security_product_enablement,
        azure_dependency_update_policy=azure_dependency_update_policy,
        security_contact=validated_security_contact,
        security_contact_section=validated_security_contact_section,
    )
    require_security_decision = repository is not None
    resolved_security_reporting_mode = resolve_security_reporting_mode(
        security_reporting_mode=security_reporting_mode,
        security_contact=validated_security_contact,
        security_contact_section=validated_security_contact_section,
        require_security_decision=require_security_decision,
    )
    if not require_security_decision and security_reporting_mode is None:
        if validated_security_contact is not None or validated_security_contact_section is not None:
            if azure_context is None:
                raise PlaceholderError(
                    "--security-contact and --security-contact-section configure the "
                    "SECURITY.md reporting section, which is only rendered when a "
                    "reporting mode is selected. Supply --repository, or set "
                    "--security-reporting-mode explicitly (for example, "
                    "--security-reporting-mode contact-only), so the override is "
                    "applied instead of silently ignored; use --conduct-contact to set "
                    "the Code of Conduct contact independently."
                )
        resolved_security_reporting_mode = None
    if (
        resolved_security_reporting_mode in SECURITY_CONTACT_REQUIRED_MODES
        and validated_security_contact is None
        and validated_security_contact_section is None
    ):
        raise PlaceholderError(
            "--security-contact or --security-contact-section is required when "
            f"--security-reporting-mode is {resolved_security_reporting_mode}."
        )
    validated_issue_labels = validate_issue_labels(issue_labels)
    resolved_issue_label_policy = resolve_issue_label_policy(
        issue_label_policy=issue_label_policy,
        issue_labels=validated_issue_labels,
    )
    resolved_discussions_policy = (
        validate_discussions_policy(discussions_policy) if discussions_policy is not None else None
    )
    validated_follow_up_status = validate_collaboration_policy_follow_up(
        issue_label_policy=resolved_issue_label_policy,
        discussions_policy=resolved_discussions_policy,
        collaboration_policy_follow_up_status=collaboration_policy_follow_up_status,
    )
    validated_conduct_contact = (
        validate_non_empty(conduct_contact, "--conduct-contact")
        if conduct_contact is not None
        else validated_security_contact if conduct_contact_sentence is None else None
    )
    validated_conduct_contact_sentence = validate_optional_non_empty(
        conduct_contact_sentence,
        "--conduct-contact-sentence",
    )
    return ReplacementContext(
        host_provider=resolved_host_provider,
        repository=repository,
        github_host=validate_github_host(github_host),
        azure_devops=azure_context,
        codeowners_owner=(
            validate_codeowners_owner(codeowners_owner)
            if codeowners_owner is not None
            else validate_codeowners_owner(f"@{owner}") if owner is not None else None
        ),
        conduct_contact=validated_conduct_contact,
        conduct_contact_sentence=validated_conduct_contact_sentence,
        security_contact=validated_security_contact,
        security_contact_section=validated_security_contact_section,
        security_reporting_mode=resolved_security_reporting_mode,
        issue_label_policy=resolved_issue_label_policy,
        issue_labels=validated_issue_labels,
        discussions_policy=resolved_discussions_policy,
        collaboration_policy_follow_up_status=validated_follow_up_status,
        vscode_title=(
            validate_non_empty(vscode_title, "--vscode-title")
            if vscode_title is not None
            else validate_non_empty(repo, "--vscode-title") if repo is not None else None
        ),
        package_name=validate_optional_non_empty(package_name, "--package-name"),
        package_description=validate_optional_non_empty(
            package_description,
            "--package-description",
        ),
        package_author=validate_optional_non_empty(package_author, "--package-author"),
        package_version=validate_optional_non_empty(package_version, "--package-version"),
        package_keywords=validate_package_keywords(package_keywords),
    )


def azure_security_contact_section(context: ReplacementContext, *, default_heading: str) -> str:
    """Return an Azure-oriented SECURITY.md private contact section."""
    if context.security_contact_section is not None:
        return context.security_contact_section.rstrip("\n") + "\n"
    if context.security_contact is not None:
        return (
            f"{default_heading}\n\n"
            "Contact the maintainers directly at:\n\n"
            f"- Contact: {context.security_contact}\n"
        )
    return (
        f"{default_heading}\n\n"
        "Maintainers must publish the private security intake route before relying on "
        "this policy.\n"
    )


def azure_security_product_note(azure_context: AzureDevOpsContext) -> str:
    """Return optional Azure DevOps Services security-product setup guidance."""
    notes = {
        "none": "",
        "github-advanced-security": (
            "Maintainers should enable and review GitHub Advanced Security for "
            "Azure DevOps Services before treating service-side scanning as complete."
        ),
        "github-secret-protection": (
            "Maintainers should enable and review GitHub Secret Protection for the "
            "Azure Repos project before treating secret scanning as complete."
        ),
        "github-code-security": (
            "Maintainers should enable and review GitHub Code Security for the Azure "
            "Repos project before treating code scanning as complete."
        ),
        "github-secret-protection-and-code-security": (
            "Maintainers should enable and review GitHub Secret Protection and GitHub "
            "Code Security for the Azure Repos project before treating security "
            "scanning as complete."
        ),
    }
    note = notes[azure_context.security_product_enablement]
    return f"\n{note}\n" if note else ""


def build_azure_devops_security_reporting_section(context: ReplacementContext) -> str:
    """Build SECURITY.md reporting guidance for Azure DevOps Services adoption."""
    assert context.azure_devops is not None
    azure_context = context.azure_devops
    if azure_context.security_intake_policy == "security-contact":
        intake_text = (
            "Report vulnerabilities privately using the security contact below.\n\n"
            f"{azure_security_contact_section(context, default_heading='### Security Contact')}"
        )
    elif azure_context.security_intake_policy == "external-process":
        intake_text = (
            "Report vulnerabilities through the maintainers' private external "
            "security intake process. Do not create public Azure Boards work items, "
            "pull request comments, or discussion posts for vulnerabilities.\n"
        )
    elif azure_context.security_intake_policy == "manual-follow-up":
        intake_text = (
            "> **Maintainers:** Finalize the private security intake route before "
            "publishing this repository for broad use. Until that route is ready, "
            "treat vulnerability intake as a first-adoption service setup task.\n"
        )
    else:
        raise AssertionError(
            f"Unhandled Azure security intake policy: {azure_context.security_intake_policy}"
        )
    return (
        f"## Reporting a Vulnerability\n\n"
        f"**Please do NOT report security vulnerabilities through public Azure Boards "
        f"work items, Azure Repos pull request comments, or other public project "
        f"surfaces.**\n\n"
        f"Azure DevOps Services project: "
        f"[{azure_context.project}]({azure_context.project_url})\n\n"
        f"{intake_text}"
        f"{azure_security_product_note(azure_context)}"
    )


def replace_contributing_placeholder_strategy_comment(
    text: str,
    _context: ReplacementContext,
) -> tuple[str, int]:
    """Remove the GitHub placeholder design note from Azure-only contributing docs."""
    start_marker = "<!--\nTEMPLATE DESIGN DECISION: Placeholder Strategy"
    start = text.find(start_marker)
    if start == -1:
        return text, 0
    end = text.find("-->\n\n", start)
    if end == -1:
        return text, 0
    end += len("-->\n\n")
    return f"{text[:start]}{text[end:]}", 1


def replace_contributing_clone_block(
    text: str,
    context: ReplacementContext,
) -> tuple[str, int]:
    """Render the Azure Repos clone block in CONTRIBUTING.md."""
    assert context.azure_devops is not None
    start_marker = "### 1. Clone the Repository"
    end_marker = "\n### 2. Install Node.js Dependencies"
    start = text.find(start_marker)
    end = text.find(end_marker, start)
    if start == -1 or end == -1:
        return text, 0
    azure_context = context.azure_devops
    replacement = (
        "### 1. Clone the Repository\n\n"
        "```bash\n"
        f"git clone {azure_context.clone_url}\n"
        f"cd {shlex.quote(azure_context.repository)}\n"
        "```\n"
    )
    return f"{text[:start]}{replacement}{text[end:]}", 1


def replace_contributing_questions_block(
    text: str,
    context: ReplacementContext,
) -> tuple[str, int]:
    """Render Azure DevOps Services issue-intake guidance in CONTRIBUTING.md."""
    assert context.azure_devops is not None
    start_marker = "## Questions or Issues?"
    end_marker = "\n## License"
    start = text.find(start_marker)
    end = text.find(end_marker, start)
    if start == -1 or end == -1:
        return text, 0
    azure_context = context.azure_devops
    replacement = (
        "## Questions or Issues?\n\n"
        "If you have questions or encounter issues:\n\n"
        f"1. Review the Azure DevOps Services project: "
        f"[{azure_context.project}]({azure_context.project_url}).\n"
        "2. Review the retained documentation in `.github/instructions/`.\n"
        f"3. Follow the Azure Boards intake policy: {azure_context.boards_policy}.\n"
    )
    return f"{text[:start]}{replacement}{text[end:]}", 1


def build_security_reporting_section(context: ReplacementContext) -> str:
    """Build the rendered SECURITY.md reporting section for the selected mode."""
    if context.host_provider == "azure-devops-services":
        return build_azure_devops_security_reporting_section(context)
    if context.security_reporting_mode is None:
        return ""
    direct_url = "https://github.com/OWNER/REPO/security/advisories/new"
    contact_lines = security_contact_section(
        context,
        default_heading="### Security Contact",
    )
    private_lines = (
        f"### GitHub Private Vulnerability Reporting\n\n"
        f"> **Maintainers:** Enable private vulnerability reporting in GitHub settings "
        f"before relying on the direct reporting link: `{direct_url}`.\n\n"
        f"Use GitHub Security Advisories through the "
        f"[private vulnerability reporting form]({direct_url}) after maintainers have "
        f"enabled private vulnerability reporting for this repository.\n"
    )

    if context.security_reporting_mode == "github-private-only":
        return (
            f"## Reporting a Vulnerability\n\n"
            f"**Please do NOT report security vulnerabilities through public GitHub issues.**\n\n"
            f"If you discover a security vulnerability in this project, report it privately "
            f"using GitHub private vulnerability reporting.\n\n"
            f"{private_lines}"
        )
    if context.security_reporting_mode == "contact-only":
        return (
            f"## Reporting a Vulnerability\n\n"
            f"**Please do NOT report security vulnerabilities through public GitHub issues.**\n\n"
            f"If you discover a security vulnerability in this project, report it privately "
            f"using the contact method below.\n\n"
            f"{contact_lines}"
        )
    return (
        f"## Reporting a Vulnerability\n\n"
        f"**Please do NOT report security vulnerabilities through public GitHub issues.**\n\n"
        f"If you discover a security vulnerability in this project, report it privately "
        f"using one of the following methods:\n\n"
        f"### Option 1: GitHub Private Vulnerability Reporting\n\n"
        f"> **Maintainers:** Enable private vulnerability reporting in GitHub settings "
        f"before relying on the direct reporting link: `{direct_url}`.\n\n"
        f"Use GitHub Security Advisories through the "
        f"[private vulnerability reporting form]({direct_url}) after maintainers have "
        f"enabled private vulnerability reporting for this repository. If that form is "
        f"unavailable, use the security contact option below.\n\n"
        f"{security_contact_section(context, default_heading='### Option 2: Security Contact')}"
    )


def security_contact_section(context: ReplacementContext, *, default_heading: str) -> str:
    """Return the SECURITY.md contact section, honoring a whole-section override."""
    if context.security_contact_section is not None:
        return context.security_contact_section.rstrip("\n") + "\n"
    return (
        f"{default_heading}\n\n"
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
    # Keep a single trailing newline so the rendered section is separated from the
    # following `### What to Include` heading by a blank line (the end_marker begins
    # with "\n"). Without it, downstream markdownlint fails MD022/MD032.
    replacement = build_security_reporting_section(context).rstrip("\n") + "\n"
    return f"{text[:start]}{replacement}{text[end:]}", 1


def build_config_security_block(context: ReplacementContext) -> str:
    """Build the rendered issue-template contact link security block.

    The issue chooser link always points to ``SECURITY.md`` regardless of the
    selected reporting mode. ``SECURITY.md`` is always reachable and is itself
    rendered per mode, so it documents the appropriate reporting path. Linking
    the chooser directly at the GitHub advisory form would send reporters to a
    page that cannot receive reports until a maintainer enables private
    vulnerability reporting; ``SECURITY.md`` avoids that dead end.
    """
    del context  # Mode controls SECURITY.md content, not the chooser link target.
    url = "https://github.com/OWNER/REPO/blob/HEAD/SECURITY.md"
    about = (
        "Report security issues privately using the instructions in "
        "SECURITY.md. Do not open a public issue."
    )
    return (
        "  # =============================================================================\n"
        "  # SECURITY LINK CONFIGURATION\n"
        "  # =============================================================================\n"
        "  # CUSTOMIZE: Replace `OWNER/REPO` with your org/repo name.\n"
        "  # GHES users must also replace github.com with their GHES host.\n"
        "  # The issue chooser links to SECURITY.md, which is always reachable and\n"
        "  # documents the reporting path for the configured security reporting mode.\n"
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


def find_comment_block_end(text: str, index: int) -> int:
    """Return the offset just past the contiguous comment block at ``index``.

    Starting from the line containing ``index``, consume consecutive comment
    lines (whose first non-space character is ``#``) and stop at the first
    blank or non-comment line, or end of file. This locates the end of an
    issue-template contact-link section so any content after it is preserved.
    """
    end = text.rfind("\n", 0, index) + 1
    length = len(text)
    while end < length:
        newline = text.find("\n", end)
        line_end = length if newline == -1 else newline + 1
        line = text[end:line_end]
        if not line.strip() or not line.lstrip().startswith("#"):
            break
        end = line_end
    return end


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
    if context.security_reporting_mode is None and context.azure_devops is None:
        return ()
    renderers = {
        "SECURITY.md": (replace_security_reporting_section,),
    }
    if context.uses_github_surfaces and context.security_reporting_mode is not None:
        renderers[".github/ISSUE_TEMPLATE/config.yml"] = (replace_config_security_block,)
        renderers[".github/ISSUE_TEMPLATE/bug_report.yml"] = (
            replace_bug_report_security_notice,
            replace_bug_report_checkbox_label,
            replace_bug_report_severity_notice,
        )
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
                    rule_name=(
                        f"security reporting mode {context.security_reporting_mode}"
                        if context.security_reporting_mode is not None
                        else f"{context.host_provider} security reporting"
                    ),
                    count=replacement_count,
                )
            )
    return tuple(records)


def render_azure_devops_provider_neutral_docs(
    file_texts: dict[str, str],
    context: ReplacementContext,
) -> tuple[ReplacementRecord, ...]:
    """Render provider-neutral baseline docs for Azure-only adoption."""
    if context.host_provider != "azure-devops-services" or context.azure_devops is None:
        return ()
    renderers: dict[str, tuple[Callable[[str, ReplacementContext], tuple[str, int]], ...]] = {
        "CONTRIBUTING.md": (
            replace_contributing_placeholder_strategy_comment,
            replace_contributing_clone_block,
            replace_contributing_questions_block,
        )
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
                    rule_name="azure devops provider-neutral docs",
                    count=replacement_count,
                )
            )
    return tuple(records)


def markdown_link_text(value: str) -> str:
    """Escape Markdown link text delimiters in a generated link label."""
    return value.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")


def replace_azure_pr_template_service_links(
    text: str,
    context: ReplacementContext,
) -> tuple[str, int]:
    """Render Azure Repos PR template service destinations as Markdown links."""
    if context.azure_devops is None:
        return text, 0
    replacements = (
        (
            "- Project: AZURE_DEVOPS_PROJECT (AZURE_DEVOPS_PROJECT_URL)",
            (
                "- Project: "
                f"[{markdown_link_text(context.azure_devops.project)}]"
                f"({context.azure_devops.project_url})"
            ),
        ),
        (
            "- Repository: AZURE_DEVOPS_REPOSITORY (AZURE_DEVOPS_REPOSITORY_WEB_URL)",
            (
                "- Repository: "
                f"[{markdown_link_text(context.azure_devops.repository)}]"
                f"({context.azure_devops.repository_web_url})"
            ),
        ),
    )
    replacement_count = 0
    for placeholder, replacement in replacements:
        count = text.count(placeholder)
        if count:
            text = text.replace(placeholder, replacement)
            replacement_count += count
    return text, replacement_count


def render_azure_devops_pr_template(
    file_texts: dict[str, str],
    context: ReplacementContext,
) -> tuple[ReplacementRecord, ...]:
    """Render Azure Repos PR-template lines that need generated Markdown."""
    relative_path = ".azuredevops/pull_request_template.md"
    if context.azure_devops is None or relative_path not in file_texts:
        return ()
    text, count = replace_azure_pr_template_service_links(file_texts[relative_path], context)
    if count == 0:
        return ()
    file_texts[relative_path] = text
    return (
        ReplacementRecord(
            path=relative_path,
            rule_name="azure devops pr template links",
            count=count,
        ),
    )


def yaml_string(value: str) -> str:
    """Return a YAML-safe quoted scalar using JSON string syntax."""
    return json.dumps(value)


def collaboration_follow_up_comments(
    status: str,
    *,
    prefix: str = "",
) -> str:
    """Return comment lines describing an open _TODO-repo-init.md action."""
    comment_lines = [f"{prefix}# Follow-up: _TODO-repo-init.md dependent-file status remains open:"]
    comment_lines.extend(f"{prefix}#   {line}" for line in status.splitlines())
    return "\n".join(comment_lines) + "\n"


def issue_labels_for_policy(context: ReplacementContext) -> tuple[str, ...]:
    """Return the labels rendered for the selected issue-label policy."""
    if context.issue_label_policy in {"existing", "create-manual-follow-up"}:
        return DEFAULT_ISSUE_LABELS
    if context.issue_label_policy == "custom":
        assert context.issue_labels is not None
        return context.issue_labels
    return ()


def build_bug_report_label_block(context: ReplacementContext) -> str:
    """Build the top-level bug-report labels block for the selected policy."""
    policy = context.issue_label_policy
    if policy is None:
        return ""

    lines = [
        "# CUSTOMIZE: Update these labels to match your repository's label taxonomy.",
        "# Template-sync issue-label policy: " + policy,
    ]
    if policy == "existing":
        lines.append("# These labels are expected to exist before this template is used.")
    elif policy == "create-manual-follow-up":
        assert context.collaboration_policy_follow_up_status is not None
        lines.append("# These labels are rendered before repository setup is complete.")
        lines.append(
            collaboration_follow_up_comments(context.collaboration_policy_follow_up_status).rstrip(
                "\n"
            )
        )
    elif policy == "omit":
        lines.append("# Labels intentionally omitted for downstream policy.")
        return "\n".join(lines) + "\n"
    elif policy == "custom":
        lines.append("# Custom labels were supplied by the downstream adoption policy.")
    else:
        raise AssertionError(f"Unhandled issue label policy: {policy}")

    lines.append("labels:")
    lines.extend(f"  - {yaml_string(label)}" for label in issue_labels_for_policy(context))
    return "\n".join(lines) + "\n"


def replace_bug_report_label_block(
    text: str,
    context: ReplacementContext,
) -> tuple[str, int]:
    """Replace the top-level bug-report label block for the selected policy."""
    start = find_line_start(text, "# CUSTOMIZE: Update these labels")
    end = find_line_start(text, "# CUSTOMIZE: Uncomment and update to specify an issue type")
    if start == -1 or end == -1:
        return text, 0
    return f"{text[:start]}{build_bug_report_label_block(context)}{text[end:]}", 1


def build_config_discussions_block(context: ReplacementContext) -> str:
    """Build the issue-template contact-link Discussions block for the selected policy."""
    policy = context.discussions_policy
    if policy is None:
        return ""

    lines = [
        "  # =============================================================================",
        "  # DISCUSSIONS LINK (OPTIONAL)",
        "  # =============================================================================",
        f"  # Template-sync Discussions policy: {policy}.",
    ]
    renders_link = policy in {"enabled", "deferred-planned-render"}
    if policy in DISCUSSIONS_FOLLOW_UP_POLICIES:
        assert context.collaboration_policy_follow_up_status is not None
        lines.append(
            collaboration_follow_up_comments(
                context.collaboration_policy_follow_up_status,
                prefix="  ",
            ).rstrip("\n")
        )
    if policy == "disabled":
        lines.append("  # GitHub Discussions contact link intentionally omitted.")
    elif policy == "deferred-not-rendered":
        lines.append("  # GitHub Discussions contact link deferred and not rendered.")
    elif policy not in {"enabled", "deferred-planned-render"}:
        raise AssertionError(f"Unhandled Discussions policy: {policy}")
    if renders_link:
        lines.extend(
            [
                "  - name: Questions & Discussions",
                "    url: https://github.com/OWNER/REPO/discussions",
                "    about: Ask questions and discuss ideas (not for bug reports)",
            ]
        )
    return "\n".join(lines) + "\n"


def replace_config_discussions_block(
    text: str,
    context: ReplacementContext,
) -> tuple[str, int]:
    """Replace the issue-template config Discussions contact-link block."""
    heading_candidates = (
        "  # DISCUSSIONS LINK (OPTIONAL)\n",
        "  # DISCUSSIONS LINK CONFIGURATION\n",
    )
    heading_index = -1
    for heading in heading_candidates:
        heading_index = text.find(heading)
        if heading_index != -1:
            break
    if heading_index == -1:
        return text, 0
    start = text.rfind(
        "  # =============================================================================",
        0,
        heading_index,
    )
    if start == -1:
        return text, 0
    # The Discussions policy block supersedes both the Discussions section and
    # the optional Support/FAQ section that follows it. Extend the removed span
    # to the end of the Support/FAQ section when present so it is dropped, while
    # splicing the rest of the file back in instead of truncating at ``start``.
    support_index = text.find("  # SUPPORT / FAQ LINK", heading_index)
    block_anchor = support_index if support_index != -1 else heading_index
    end = find_comment_block_end(text, block_anchor)
    return f"{text[:start]}{build_config_discussions_block(context)}{text[end:]}", 1


def render_collaboration_policy(
    file_texts: dict[str, str],
    context: ReplacementContext,
) -> tuple[ReplacementRecord, ...]:
    """Render issue-template collaboration policies."""
    if not context.has_collaboration_policy:
        return ()
    renderers: dict[str, tuple[Callable[[str, ReplacementContext], tuple[str, int]], ...]] = {}
    if context.issue_label_policy is not None:
        renderers[".github/ISSUE_TEMPLATE/bug_report.yml"] = (replace_bug_report_label_block,)
    if context.discussions_policy is not None:
        renderers[".github/ISSUE_TEMPLATE/config.yml"] = (replace_config_discussions_block,)

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
                    rule_name="collaboration policy",
                    count=replacement_count,
                )
            )
    return tuple(records)


def render_conduct_contact_sentence(
    file_texts: dict[str, str],
    context: ReplacementContext,
) -> tuple[ReplacementRecord, ...]:
    """Replace the Code of Conduct contact sentence when a sentence override is supplied."""
    if context.conduct_contact_sentence is None or "CODE_OF_CONDUCT.md" not in file_texts:
        return ()
    text = file_texts["CODE_OF_CONDUCT.md"]
    updated_text, count = replace_literal(
        CONDUCT_CONTACT_SENTENCE_PLACEHOLDER,
        context.conduct_contact_sentence,
    )(text)
    if count == 0:
        return ()
    file_texts["CODE_OF_CONDUCT.md"] = updated_text
    return (
        ReplacementRecord(
            path="CODE_OF_CONDUCT.md",
            rule_name="code of conduct contact sentence",
            count=count,
        ),
    )


def load_json_object_from_text(text: str, display_path: str) -> dict[str, Any]:
    """Parse a JSON object from an already-read UTF-8 file body."""
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as error:
        raise PlaceholderError(f"{display_path}: invalid JSON ({error}).") from error
    if not isinstance(parsed, dict):
        raise PlaceholderError(f"{display_path}: expected a JSON object.")
    return parsed


def dump_json_object(document: dict[str, Any]) -> str:
    """Serialize a JSON object with stable repository formatting."""
    return json.dumps(document, indent=2) + "\n"


def set_json_field(
    document: dict[str, Any],
    field_name: str,
    value: Any,
) -> int:
    """Set a JSON field and return whether it changed."""
    if document.get(field_name) == value:
        return 0
    document[field_name] = value
    return 1


def package_json_updates(context: ReplacementContext) -> dict[str, Any]:
    """Return requested package.json metadata field updates."""
    updates: dict[str, Any] = {}
    if context.package_name is not None:
        updates["name"] = context.package_name
    if context.package_version is not None:
        updates["version"] = context.package_version
    if context.package_description is not None:
        updates["description"] = context.package_description
    if context.package_keywords is not None:
        updates["keywords"] = list(context.package_keywords)
    if context.package_author is not None:
        updates["author"] = context.package_author
    return updates


def update_package_json_metadata(
    file_texts: dict[str, str],
    context: ReplacementContext,
) -> tuple[ReplacementRecord, ...]:
    """Apply requested package metadata to package.json."""
    if "package.json" not in file_texts:
        return ()
    updates = package_json_updates(context)
    if not updates:
        return ()
    document = load_json_object_from_text(file_texts["package.json"], "package.json")
    change_count = 0
    for field_name, value in updates.items():
        change_count += set_json_field(document, field_name, value)
    if change_count == 0:
        return ()
    file_texts["package.json"] = dump_json_object(document)
    return (
        ReplacementRecord(
            path="package.json",
            rule_name="package metadata",
            count=change_count,
        ),
    )


def root_package_lock_mapping(document: dict[str, Any]) -> dict[str, Any]:
    """Return the root package-lock packages[''] object."""
    packages = document.get("packages")
    if not isinstance(packages, dict):
        lockfile_version = document.get("lockfileVersion")
        version_note = (
            f" (found lockfileVersion {lockfile_version!r})" if lockfile_version is not None else ""
        )
        raise PlaceholderError(
            f'package-lock.json has no top-level "packages" object{version_note}. '
            "Deterministic root-identity updates require an npm lockfileVersion 2 or 3 "
            "lockfile. Regenerate it with a modern npm (for example, "
            "`npm install --package-lock-only`), or omit package-lock.json from the "
            "adopted files so only package.json receives the identity update."
        )
    root_package = packages.get("")
    if not isinstance(root_package, dict):
        raise PlaceholderError(
            'package-lock.json has no root packages[""] entry, so its root identity '
            "cannot be updated deterministically. Regenerate the lockfile with "
            "`npm install --package-lock-only`, or omit package-lock.json from the "
            "adopted files so only package.json receives the identity update."
        )
    return root_package


def update_package_lock_identity(
    file_texts: dict[str, str],
    context: ReplacementContext,
) -> tuple[ReplacementRecord, ...]:
    """Apply requested root identity metadata to package-lock.json."""
    if "package-lock.json" not in file_texts:
        return ()
    if context.package_name is None and context.package_version is None:
        return ()
    document = load_json_object_from_text(file_texts["package-lock.json"], "package-lock.json")
    root_package = root_package_lock_mapping(document)
    change_count = 0
    if context.package_name is not None:
        change_count += set_json_field(document, "name", context.package_name)
        change_count += set_json_field(root_package, "name", context.package_name)
    if context.package_version is not None:
        change_count += set_json_field(document, "version", context.package_version)
        change_count += set_json_field(root_package, "version", context.package_version)
    if change_count == 0:
        return ()
    file_texts["package-lock.json"] = dump_json_object(document)
    return (
        ReplacementRecord(
            path="package-lock.json",
            rule_name="package-lock root identity",
            count=change_count,
        ),
    )


def render_package_metadata(
    file_texts: dict[str, str],
    context: ReplacementContext,
) -> tuple[ReplacementRecord, ...]:
    """Render package metadata and deterministic root package-lock identity fields."""
    records: list[ReplacementRecord] = []
    if not context.has_package_metadata:
        return ()
    records.extend(update_package_json_metadata(file_texts, context))
    records.extend(update_package_lock_identity(file_texts, context))
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
        and context.conduct_contact_sentence is None
    ):
        raise PlaceholderError(
            "CODE_OF_CONDUCT.md contains [INSERT CONTACT METHOD]; provide "
            "--conduct-contact or --conduct-contact-sentence when --security-contact "
            "is omitted."
        )


def build_replacement_rules(context: ReplacementContext) -> tuple[ReplacementRule, ...]:
    """Build the concrete allowlist of approved replacements."""
    rules: list[ReplacementRule] = []
    if context.uses_github_surfaces and context.repository is not None:
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

    if context.azure_devops is not None:
        for name, placeholder, attribute_name in sorted(
            AZURE_DEVOPS_TOKEN_REPLACEMENT_SPECS,
            key=lambda spec: len(spec[1]),
            reverse=True,
        ):
            replacement = getattr(context.azure_devops, attribute_name)
            rules.append(
                ReplacementRule(
                    name=name,
                    placeholder=placeholder,
                    replacement=replacement,
                    paths=AZURE_DEVOPS_URL_TOKEN_PATHS,
                    replace=replace_literal(placeholder, replacement),
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
    if context.has_package_metadata:
        for relative_path in PACKAGE_METADATA_PATHS:
            files_by_path[relative_path] = (
                resolve_repo_path(repo_root, relative_path),
                relative_path,
            )
    if context.has_collaboration_policy:
        for relative_path in (
            ".github/ISSUE_TEMPLATE/config.yml",
            ".github/ISSUE_TEMPLATE/bug_report.yml",
        ):
            files_by_path[relative_path] = (
                resolve_repo_path(repo_root, relative_path),
                relative_path,
            )
    if context.azure_devops is not None:
        for relative_path in AZURE_DEVOPS_URL_TOKEN_PATHS:
            files_by_path[relative_path] = (
                resolve_repo_path(repo_root, relative_path),
                relative_path,
            )
    if context.host_provider == "azure-devops-services":
        files_by_path["CONTRIBUTING.md"] = (
            resolve_repo_path(repo_root, "CONTRIBUTING.md"),
            "CONTRIBUTING.md",
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
    records.extend(render_conduct_contact_sentence(file_texts, context))
    records.extend(render_security_reporting_mode(file_texts, context))
    records.extend(render_azure_devops_provider_neutral_docs(file_texts, context))
    records.extend(render_azure_devops_pr_template(file_texts, context))
    records.extend(render_collaboration_policy(file_texts, context))
    records.extend(render_package_metadata(file_texts, context))

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
    for name, placeholder, _attribute_name in AZURE_DEVOPS_TOKEN_REPLACEMENT_SPECS:
        patterns.append(
            (
                name,
                placeholder,
                re.compile(re.escape(placeholder)),
                AZURE_DEVOPS_URL_TOKEN_PATHS,
            )
        )
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


def add_args_file_options(parser: argparse.ArgumentParser) -> None:
    """Add explicit argument-file options to one subcommand parser."""
    parser.add_argument(
        "--args-file",
        default=None,
        help="JSON or YAML file containing shell-safe argument values for this command.",
    )
    parser.add_argument(
        "--args-format",
        choices=ARGS_FILE_FORMATS,
        default=None,
        help="Explicit args-file format; overrides the file extension.",
    )


def args_file_format_for_path(path: Path, args_format: str | None) -> str:
    """Return the parser format selected by override or recognized file extension."""
    if args_format is not None:
        return args_format
    inferred_format = ARGS_FILE_EXTENSION_FORMATS.get(path.suffix.lower())
    if inferred_format is None:
        raise PlaceholderError(
            "Unable to determine --args-file format from extension; use "
            "--args-format json or --args-format yaml, or name the file with "
            "a .json, .yaml, or .yml extension."
        )
    return inferred_format


def read_args_file_text(path: Path) -> str:
    """Read an explicit args file path."""
    try:
        # Tolerate a leading UTF-8 BOM (e.g. PowerShell `Set-Content -Encoding UTF8`).
        return path.read_text(encoding="utf-8-sig")
    except OSError as error:
        error_summary = f"{type(error).__name__}: {error.strerror or 'I/O error'}"
        raise PlaceholderError(f"--args-file: unable to read file ({error_summary}).") from error


def load_json_args_file(path: Path) -> dict[str, Any]:
    """Load a JSON args file that must contain an object."""
    text = read_args_file_text(path)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as error:
        raise PlaceholderError(f"--args-file: invalid JSON ({error}).") from error
    if not isinstance(parsed, dict):
        raise PlaceholderError("--args-file must contain a JSON object.")
    return parsed


def load_yaml_args_file(
    path: Path,
    *,
    yaml_module_loader: Callable[[str], Any] = importlib.import_module,
) -> dict[str, Any]:
    """Load a YAML args file through the retained YAML parser path."""
    try:
        yaml_module = yaml_module_loader("yaml")
    except ImportError as error:
        raise PlaceholderError(
            "YAML --args-file support is unavailable because the retained YAML "
            "parser is not importable. Convert the args file to JSON or enable "
            "the repository's retained YAML support."
        ) from error
    text = read_args_file_text(path)
    try:
        parsed = yaml_module.safe_load(text)
    except yaml_module.YAMLError as error:
        raise PlaceholderError(f"--args-file: invalid YAML ({error}).") from error
    if not isinstance(parsed, dict):
        raise PlaceholderError("--args-file must contain a YAML mapping.")
    return parsed


def load_args_file_mapping(
    raw_path: str,
    args_format: str | None,
    *,
    yaml_module_loader: Callable[[str], Any] = importlib.import_module,
) -> dict[str, Any]:
    """Load an explicit JSON or YAML argument file."""
    path = Path(raw_path).expanduser()
    selected_format = args_file_format_for_path(path, args_format)
    if selected_format == "json":
        return load_json_args_file(path)
    if selected_format == "yaml":
        return load_yaml_args_file(path, yaml_module_loader=yaml_module_loader)
    raise AssertionError(f"Unhandled args-file format: {selected_format}")


def cli_supplied_fields(
    argv: Sequence[str],
    flags_by_field: dict[str, tuple[str, ...]],
) -> set[str]:
    """Return argument destinations supplied directly on the command line."""
    supplied: set[str] = set()
    flag_to_field = {
        flag: field_name for field_name, flags in flags_by_field.items() for flag in flags
    }
    for token in argv:
        flag = token.split("=", 1)[0]
        field_name = flag_to_field.get(flag)
        if field_name is not None:
            supplied.add(field_name)
    return supplied


def validate_args_file_value(field_name: str, value: Any) -> Any:
    """Validate one args-file value and return its normalized representation."""
    if value is None:
        return None
    if field_name in STRING_ARGS_FILE_FIELDS:
        if not isinstance(value, str):
            raise PlaceholderError(f"--args-file field {field_name!r} must be a string.")
        return value
    if field_name in LIST_STRING_ARGS_FILE_FIELDS:
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise PlaceholderError(f"--args-file field {field_name!r} must be a list of strings.")
        return tuple(value)
    if field_name in BOOLEAN_ARGS_FILE_FIELDS:
        if not isinstance(value, bool):
            raise PlaceholderError(f"--args-file field {field_name!r} must be a boolean.")
        return value
    raise AssertionError(f"Unhandled args-file field: {field_name}")


def apply_args_file_values(
    args: argparse.Namespace,
    *,
    argv: Sequence[str],
    allowed_fields: frozenset[str],
    flags_by_field: dict[str, tuple[str, ...]],
) -> argparse.Namespace:
    """Merge args-file values into parsed args, with CLI flags taking precedence."""
    if args.args_file is None:
        return args
    args_file_values = load_args_file_mapping(args.args_file, args.args_format)
    unknown_fields = sorted(set(args_file_values) - allowed_fields)
    if unknown_fields:
        raise PlaceholderError("Unknown --args-file field(s): " + ", ".join(unknown_fields) + ".")
    direct_cli_fields = cli_supplied_fields(argv, flags_by_field)
    for field_name, raw_value in args_file_values.items():
        if field_name in direct_cli_fields:
            continue
        if raw_value is None:
            continue
        setattr(args, field_name, validate_args_file_value(field_name, raw_value))
    return args


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    argv = tuple(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(description="Replace and audit exact template placeholders.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    replace_parser = subparsers.add_parser("replace", help="replace approved placeholders")
    add_args_file_options(replace_parser)
    replace_parser.add_argument("--repo-root", default=None, help="repository root")
    replace_parser.add_argument(
        "--host-provider",
        choices=HOST_PROVIDERS,
        default=None,
        help=(
            "Host-provider mode: github, github-enterprise-server, "
            "azure-devops-services, or dual."
        ),
    )
    replace_parser.add_argument("--repository", default=None, help="replacement OWNER/REPO value")
    replace_parser.add_argument(
        "--github-host",
        default="github.com",
        help="GitHub or GHES host for approved template URL contexts",
    )
    replace_parser.add_argument(
        "--azure-devops-organization",
        default=None,
        help="Azure DevOps Services organization name.",
    )
    replace_parser.add_argument(
        "--azure-devops-organization-url",
        default=None,
        help=(
            "Azure DevOps Services organization URL, either "
            "https://dev.azure.com/<organization> or "
            "https://<organization>.visualstudio.com."
        ),
    )
    replace_parser.add_argument(
        "--azure-devops-project",
        default=None,
        help="Azure DevOps project name.",
    )
    replace_parser.add_argument(
        "--azure-devops-project-url",
        default=None,
        help="Validated Azure DevOps project URL override.",
    )
    replace_parser.add_argument(
        "--azure-devops-repository",
        default=None,
        help="Azure Repos repository name.",
    )
    replace_parser.add_argument(
        "--azure-devops-repository-url",
        default=None,
        help="Validated Azure Repos repository web URL override.",
    )
    replace_parser.add_argument(
        "--azure-devops-clone-url",
        default=None,
        help="Validated Azure Repos HTTPS clone URL override without embedded credentials.",
    )
    replace_parser.add_argument(
        "--azure-devops-default-branch",
        default=None,
        help="Azure Repos default branch name; defaults to main.",
    )
    replace_parser.add_argument(
        "--azure-boards-policy",
        choices=AZURE_DEVOPS_BOARDS_POLICIES,
        default=None,
        help="Azure Boards intake policy for first-adoption reporting.",
    )
    replace_parser.add_argument(
        "--azure-repos-pr-template-policy",
        choices=AZURE_DEVOPS_PR_TEMPLATE_POLICIES,
        default=None,
        help="Azure Repos pull request template policy.",
    )
    replace_parser.add_argument(
        "--azure-branch-policy-reviewer-guidance",
        choices=AZURE_DEVOPS_BRANCH_POLICY_POLICIES,
        default=None,
        help="Azure Repos branch policy reviewer-guidance status.",
    )
    replace_parser.add_argument(
        "--azure-security-intake-policy",
        choices=AZURE_DEVOPS_SECURITY_INTAKE_POLICIES,
        default=None,
        help="Azure security intake policy for SECURITY.md and first-adoption reporting.",
    )
    replace_parser.add_argument(
        "--azure-security-product-enablement",
        choices=AZURE_DEVOPS_SECURITY_PRODUCT_POLICIES,
        default=None,
        help="Azure DevOps Services security product enablement status.",
    )
    replace_parser.add_argument(
        "--azure-dependency-update-policy",
        choices=AZURE_DEVOPS_DEPENDENCY_UPDATE_POLICIES,
        default=None,
        help="Azure Repos dependency update policy status.",
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
        "--conduct-contact-sentence",
        default=None,
        help="replacement full Code of Conduct reporting sentence",
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
        "--security-contact-section",
        default=None,
        help="replacement whole SECURITY.md contact section for contact-based modes",
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
        "--issue-label-policy",
        choices=ISSUE_LABEL_POLICIES,
        default=None,
        help="Issue-template label policy: existing, create-manual-follow-up, omit, or custom.",
    )
    replace_parser.add_argument(
        "--issue-label",
        dest="issue_labels",
        action="append",
        default=None,
        help="Custom issue label for --issue-label-policy custom. May be repeated.",
    )
    replace_parser.add_argument(
        "--discussions-policy",
        choices=DISCUSSIONS_POLICIES,
        default=None,
        help=(
            "Issue-template Discussions contact-link policy: enabled, disabled, "
            "deferred-planned-render, or deferred-not-rendered."
        ),
    )
    replace_parser.add_argument(
        "--collaboration-policy-follow-up-status",
        default=None,
        help=(
            "Single source status text from _TODO-repo-init.md for label or "
            "Discussions policies that leave manual setup open."
        ),
    )
    replace_parser.add_argument(
        "--vscode-title",
        default=None,
        help="replacement VS Code window title; defaults to the repository name",
    )
    replace_parser.add_argument("--package-name", default=None, help="replacement package name")
    replace_parser.add_argument(
        "--package-description",
        default=None,
        help="replacement package description",
    )
    replace_parser.add_argument("--package-author", default=None, help="replacement package author")
    replace_parser.add_argument(
        "--package-version",
        default=None,
        help="replacement package version; updates package-lock root version fields",
    )
    replace_parser.add_argument(
        "--package-keyword",
        dest="package_keywords",
        action="append",
        default=None,
        help="replacement package keyword; may be repeated",
    )
    replace_parser.add_argument("--dry-run", action="store_true", help="report without writing")

    scan_parser = subparsers.add_parser("scan", help="scan for unresolved placeholders")
    add_args_file_options(scan_parser)
    scan_parser.add_argument("--repo-root", default=None, help="repository root")
    scan_parser.add_argument(
        "--repository",
        default=None,
        help="optional OWNER/REPO value used to detect common corruption patterns",
    )
    args = parser.parse_args(argv)
    if args.command == "replace":
        return apply_args_file_values(
            args,
            argv=argv,
            allowed_fields=REPLACE_ARGS_FILE_FIELDS,
            flags_by_field=REPLACE_CLI_FLAGS,
        )
    if args.command == "scan":
        return apply_args_file_values(
            args,
            argv=argv,
            allowed_fields=SCAN_ARGS_FILE_FIELDS,
            flags_by_field=SCAN_CLI_FLAGS,
        )
    raise AssertionError(f"Unhandled command: {args.command}")


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
        host_provider=args.host_provider,
        repository=args.repository,
        github_host=args.github_host,
        azure_devops_organization=args.azure_devops_organization,
        azure_devops_organization_url=args.azure_devops_organization_url,
        azure_devops_project=args.azure_devops_project,
        azure_devops_project_url=args.azure_devops_project_url,
        azure_devops_repository=args.azure_devops_repository,
        azure_devops_repository_url=args.azure_devops_repository_url,
        azure_devops_clone_url=args.azure_devops_clone_url,
        azure_devops_default_branch=args.azure_devops_default_branch,
        azure_boards_policy=args.azure_boards_policy,
        azure_repos_pr_template_policy=args.azure_repos_pr_template_policy,
        azure_branch_policy_reviewer_guidance=args.azure_branch_policy_reviewer_guidance,
        azure_security_intake_policy=args.azure_security_intake_policy,
        azure_security_product_enablement=args.azure_security_product_enablement,
        azure_dependency_update_policy=args.azure_dependency_update_policy,
        codeowners_owner=args.codeowners_owner,
        conduct_contact=args.conduct_contact,
        conduct_contact_sentence=args.conduct_contact_sentence,
        security_contact=args.security_contact,
        security_contact_section=args.security_contact_section,
        security_reporting_mode=args.security_reporting_mode,
        issue_label_policy=args.issue_label_policy,
        issue_labels=args.issue_labels,
        discussions_policy=args.discussions_policy,
        collaboration_policy_follow_up_status=args.collaboration_policy_follow_up_status,
        vscode_title=args.vscode_title,
        package_name=args.package_name,
        package_description=args.package_description,
        package_author=args.package_author,
        package_version=args.package_version,
        package_keywords=args.package_keywords,
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
    try:
        args = parse_args(argv)
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
