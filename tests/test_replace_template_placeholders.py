"""Tests for the exact template placeholder replacement helper."""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest
import yaml  # type: ignore[import-untyped]

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / ".github" / "scripts" / "replace-template-placeholders.py"
SCRIPT_SPEC = importlib.util.spec_from_file_location("replace_template_placeholders", SCRIPT_PATH)
if SCRIPT_SPEC is None or SCRIPT_SPEC.loader is None:
    raise RuntimeError(f"Unable to load placeholder helper module from {SCRIPT_PATH}")
placeholder_helper = importlib.util.module_from_spec(SCRIPT_SPEC)
sys.modules[SCRIPT_SPEC.name] = placeholder_helper
SCRIPT_SPEC.loader.exec_module(placeholder_helper)


def write_file(path: Path, content: str) -> Path:
    """Create a UTF-8 test file and its parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def read_file(path: Path) -> str:
    """Read a UTF-8 test file."""
    return path.read_text(encoding="utf-8")


def write_json(path: Path, content: object) -> Path:
    """Write a strict JSON fixture file."""
    return write_file(path, json.dumps(content, indent=2) + "\n")


def build_context(**overrides: object) -> object:
    """Build a replacement context with test defaults."""
    values: dict[str, object] = {
        "repository": "octo/widget",
        "github_host": "github.com",
        "codeowners_owner": "@octo",
        "conduct_contact": "conduct@example.com",
        "security_contact": "security@example.com",
        "vscode_title": "widget",
    }
    values.update(overrides)
    return placeholder_helper.build_replacement_context(**values)


def copy_security_reporting_fixture(repo_root: Path) -> None:
    """Copy the repository's security-reporting template surfaces into a fixture."""
    for relative_path in (
        "SECURITY.md",
        "CODE_OF_CONDUCT.md",
        ".github/ISSUE_TEMPLATE/config.yml",
        ".github/ISSUE_TEMPLATE/bug_report.yml",
    ):
        destination = repo_root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO_ROOT / relative_path, destination)


def load_yaml(path: Path) -> object:
    """Load a YAML fixture after asserting it parses."""
    return yaml.safe_load(read_file(path))


def security_contact_link(config: object) -> dict[str, object]:
    """Return the security contact link from parsed issue-template config."""
    return contact_link_by_name(config, "Security Vulnerabilities")


def contact_link_by_name(config: object, name: str) -> dict[str, object]:
    """Return a named contact link from parsed issue-template config."""
    assert isinstance(config, dict)
    contact_links = config["contact_links"]
    assert isinstance(contact_links, list)
    for contact_link in contact_links:
        assert isinstance(contact_link, dict)
        if contact_link.get("name") == name:
            return contact_link
    raise AssertionError(f"{name} contact link not found")


def assert_issue_form_shape(bug_report: object) -> None:
    """Assert the rendered bug-report issue form has the expected structure."""
    assert isinstance(bug_report, dict)
    body = bug_report["body"]
    assert isinstance(body, list)
    assert body
    for item in body:
        assert isinstance(item, dict)
        assert isinstance(item.get("type"), str)
        assert isinstance(item.get("attributes"), dict)


def test_approved_placeholder_replacement_does_not_mutate_normal_words(tmp_path: Path) -> None:
    """Exact placeholder replacement leaves REPORT, REPOSITORY, and REPOSITORIES unchanged."""
    write_file(
        tmp_path / ".github" / "ISSUE_TEMPLATE" / "config.yml",
        "url: https://github.com/OWNER/REPO/blob/HEAD/CONTRIBUTING.md\n",
    )
    write_file(
        tmp_path / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml",
        "\n".join(
            [
                "url: https://github.com/OWNER/REPO/security/advisories/new",
                "url: https://github.com/OWNER/REPO/security",
                "url: https://github.com/OWNER/REPO/blob/HEAD/SECURITY.md",
            ]
        )
        + "\n",
    )
    write_file(
        tmp_path / ".github" / "pull_request_template.md",
        "See https://github.com/OWNER/REPO/blob/HEAD/CONTRIBUTING.md and OWNER/REPO.\n",
    )
    write_file(tmp_path / ".github" / "CODEOWNERS", "* @OWNER\n")
    write_file(tmp_path / "CODE_OF_CONDUCT.md", "Contact: [INSERT CONTACT METHOD]\n")
    write_file(
        tmp_path / "CONTRIBUTING.md",
        "\n".join(
            [
                "REPORT REPOSITORY REPOSITORIES",
                "git clone https://github.com/OWNER/REPO.git",
                "Issues: https://github.com/OWNER/REPO/issues",
                "cd REPO",
            ]
        )
        + "\n",
    )
    write_file(
        tmp_path / "SECURITY.md",
        "\n".join(
            [
                "See https://github.com/OWNER/REPO/security/advisories/new",
                "<!-- TODO: Replace with your security contact email -->",
                "Email: [security contact email]",
            ]
        )
        + "\n",
    )
    write_file(
        tmp_path / ".vscode" / "settings.json",
        '{"window.title": "Go to .vscode/settings.json and make this the name of the repo"}\n',
    )

    records = placeholder_helper.replace_placeholders(
        repo_root=tmp_path,
        context=build_context(),
    )
    findings = placeholder_helper.scan_repository(tmp_path, repository="octo/widget")

    assert records
    assert findings == ()
    contributing = read_file(tmp_path / "CONTRIBUTING.md")
    assert "REPORT REPOSITORY REPOSITORIES" in contributing
    assert "git clone https://github.com/octo/widget.git" in contributing
    assert "https://github.com/octo/widget/issues" in contributing
    assert "cd REPO" in contributing
    assert "@OWNER" not in read_file(tmp_path / ".github" / "CODEOWNERS")
    assert "conduct@example.com" in read_file(tmp_path / "CODE_OF_CONDUCT.md")
    security_text = read_file(tmp_path / "SECURITY.md")
    assert "security@example.com" in security_text
    assert "TODO: Replace" not in security_text
    assert "<!-- Security contact configured -->" in security_text
    assert "with your security contact email" not in security_text
    assert "widget" in read_file(tmp_path / ".vscode" / "settings.json")


def test_security_todo_marker_preserved_when_no_security_decision(tmp_path: Path) -> None:
    """A run that makes no security decision leaves the SECURITY.md TODO marker intact."""
    write_file(
        tmp_path / "SECURITY.md",
        "<!-- TODO: Replace with your security contact email -->\n",
    )
    context = placeholder_helper.build_replacement_context()
    assert context.security_reporting_mode is None
    assert context.security_todo_replacement is None

    placeholder_helper.replace_placeholders(repo_root=tmp_path, context=context)

    security_text = read_file(tmp_path / "SECURITY.md")
    assert "<!-- TODO: Replace with your security contact email -->" in security_text
    assert "intentionally omitted by reporting mode" not in security_text


def test_security_todo_replacement_reflects_security_decision() -> None:
    """The TODO replacement marks omission only when a security decision was actually made."""
    # Repository-less / package-metadata-only run with no security inputs -> leave the marker.
    assert (
        placeholder_helper.build_replacement_context(
            package_name="downstream-tools",
        ).security_todo_replacement
        is None
    )
    # An explicit reporting-mode decision that omits the contact -> intentional omission.
    omitted = placeholder_helper.build_replacement_context(
        security_reporting_mode="github-private-only",
    )
    assert omitted.security_todo_replacement == (
        "<!-- Security contact intentionally omitted by reporting mode -->"
    )
    # A configured security contact -> configured.
    configured = placeholder_helper.build_replacement_context(
        repository="octo/widget",
        security_contact="security@example.com",
    )
    assert configured.security_todo_replacement == "<!-- Security contact configured -->"


def test_ghes_host_substitution_is_limited_to_approved_template_urls(
    tmp_path: Path,
) -> None:
    """GHES replacement touches approved placeholder URLs, not arbitrary github.com URLs."""
    write_file(
        tmp_path / ".github" / "ISSUE_TEMPLATE" / "config.yml",
        "\n".join(
            [
                "url: https://github.com/OWNER/REPO/security",
                "example: https://github.com/example/other/security",
            ]
        )
        + "\n",
    )

    placeholder_helper.replace_placeholders(
        repo_root=tmp_path,
        context=build_context(github_host="github.company.com"),
    )

    text = read_file(tmp_path / ".github" / "ISSUE_TEMPLATE" / "config.yml")
    assert "https://github.company.com/octo/widget/security" in text
    assert "https://github.com/example/other/security" in text


def test_azure_devops_url_generation_encodes_paths_and_preserves_host_forms(
    tmp_path: Path,
) -> None:
    """Azure DevOps Services URLs are generated for both supported organization URL forms."""
    write_file(
        tmp_path / ".azuredevops" / "platform" / "adoption-guidance.md",
        "\n".join(
            [
                "AZURE_DEVOPS_ORGANIZATION_URL",
                "AZURE_DEVOPS_PROJECT_URL",
                "AZURE_DEVOPS_REPOSITORY_WEB_URL",
                "AZURE_DEVOPS_CLONE_URL",
            ]
        )
        + "\n",
    )
    context = placeholder_helper.build_replacement_context(
        host_provider="azure-devops-services",
        azure_devops_organization="contoso",
        azure_devops_project="Microsoft 365",
        azure_devops_repository="repo tools",
    )

    placeholder_helper.replace_placeholders(repo_root=tmp_path, context=context)

    text = read_file(tmp_path / ".azuredevops" / "platform" / "adoption-guidance.md")
    assert "https://dev.azure.com/contoso" in text
    assert "https://dev.azure.com/contoso/Microsoft%20365" in text
    assert "https://dev.azure.com/contoso/Microsoft%20365/_git/repo%20tools" in text

    visualstudio_context = placeholder_helper.build_replacement_context(
        host_provider="azure-devops-services",
        azure_devops_organization="contoso",
        azure_devops_organization_url="https://contoso.visualstudio.com",
        azure_devops_project="Microsoft 365",
        azure_devops_repository="repo tools",
    )

    assert visualstudio_context.azure_devops.project_url == (
        "https://contoso.visualstudio.com/Microsoft%20365"
    )
    assert visualstudio_context.azure_devops.repository_web_url == (
        "https://contoso.visualstudio.com/Microsoft%20365/_git/repo%20tools"
    )


def test_azure_devops_url_overrides_validate_without_double_encoding() -> None:
    """Azure DevOps URL overrides preserve supplied encoding and reject credentials."""
    context = placeholder_helper.build_replacement_context(
        host_provider="azure-devops-services",
        azure_devops_organization="contoso",
        azure_devops_project="Microsoft 365",
        azure_devops_project_url="https://dev.azure.com/contoso/Microsoft%20365",
        azure_devops_repository="repo tools",
        azure_devops_repository_url=(
            "https://dev.azure.com/contoso/Microsoft%20365/_git/repo%20tools"
        ),
    )

    assert context.azure_devops.project_url == "https://dev.azure.com/contoso/Microsoft%20365"
    assert "%2520" not in context.azure_devops.repository_web_url

    with pytest.raises(placeholder_helper.PlaceholderError, match="embedded credentials"):
        placeholder_helper.build_replacement_context(
            host_provider="azure-devops-services",
            azure_devops_organization="contoso",
            azure_devops_project="Platform",
            azure_devops_repository="downstream-template",
            azure_devops_clone_url=(
                "https://user:token@dev.azure.com/contoso/Platform/_git/downstream-template"
            ),
        )

    with pytest.raises(placeholder_helper.PlaceholderError, match="whitespace"):
        placeholder_helper.build_replacement_context(
            host_provider="azure-devops-services",
            azure_devops_organization="contoso",
            azure_devops_project="Microsoft 365",
            azure_devops_project_url="https://dev.azure.com/contoso/Microsoft 365",
            azure_devops_repository="downstream-template",
        )


def test_azure_provider_rejects_github_only_inputs_unless_dual() -> None:
    """Azure-only adoption rejects GitHub-only surfaces such as CODEOWNERS ownership."""
    with pytest.raises(placeholder_helper.PlaceholderError, match="codeowners-owner"):
        placeholder_helper.build_replacement_context(
            host_provider="azure-devops-services",
            azure_devops_organization="contoso",
            azure_devops_project="Platform",
            azure_devops_repository="downstream-template",
            codeowners_owner="@octo",
        )

    context = placeholder_helper.build_replacement_context(
        host_provider="dual",
        repository="octo/widget",
        codeowners_owner="@octo",
        security_contact="security@example.com",
        azure_devops_organization="contoso",
        azure_devops_project="Platform",
        azure_devops_repository="downstream-template",
    )

    assert context.host_provider == "dual"
    assert context.codeowners_owner == "@octo"
    assert context.azure_devops.repository_web_url == (
        "https://dev.azure.com/contoso/Platform/_git/downstream-template"
    )


@pytest.mark.parametrize(
    "security_reporting_mode",
    ["contact-only", "github-private-only", "both"],
)
def test_azure_only_rejects_security_reporting_mode(security_reporting_mode: str) -> None:
    """Azure-only adoption rejects --security-reporting-mode (a no-op for this provider)."""
    with pytest.raises(placeholder_helper.PlaceholderError, match="security-reporting-mode"):
        placeholder_helper.build_replacement_context(
            host_provider="azure-devops-services",
            azure_devops_organization="contoso",
            azure_devops_project="Platform",
            azure_devops_repository="downstream-template",
            security_contact="security@example.com",
            security_reporting_mode=security_reporting_mode,
        )


def test_azure_security_reporting_renders_security_md_without_github_urls(
    tmp_path: Path,
) -> None:
    """Azure-only SECURITY.md rendering does not use GitHub private advisory language."""
    shutil.copyfile(REPO_ROOT / "SECURITY.md", tmp_path / "SECURITY.md")
    context = placeholder_helper.build_replacement_context(
        host_provider="azure-devops-services",
        azure_devops_organization="contoso",
        azure_devops_project="Platform",
        azure_devops_repository="downstream-template",
        azure_security_intake_policy="security-contact",
        security_contact="security@example.com",
    )

    placeholder_helper.replace_placeholders(repo_root=tmp_path, context=context)

    security_text = read_file(tmp_path / "SECURITY.md")
    assert "Azure DevOps Services project" in security_text
    assert "Azure Boards work items" in security_text
    assert "security@example.com" in security_text
    assert "github.com/OWNER/REPO" not in security_text
    assert "private vulnerability reporting" not in security_text
    assert "[security contact email]" not in security_text


def test_azure_only_baseline_docs_do_not_leave_github_placeholders(tmp_path: Path) -> None:
    """Azure-only rendering removes GitHub OWNER/REPO placeholders from baseline docs."""
    for relative_path in ("CONTRIBUTING.md", "SECURITY.md", "CODE_OF_CONDUCT.md"):
        shutil.copyfile(REPO_ROOT / relative_path, tmp_path / relative_path)
    context = placeholder_helper.build_replacement_context(
        host_provider="azure-devops-services",
        azure_devops_organization="contoso",
        azure_devops_project="Platform",
        azure_devops_repository="downstream-template",
        azure_boards_policy="work-items",
        security_contact="security@example.com",
    )

    placeholder_helper.replace_placeholders(repo_root=tmp_path, context=context)

    contributing_text = read_file(tmp_path / "CONTRIBUTING.md")
    assert "OWNER/REPO" not in contributing_text
    assert "git clone https://dev.azure.com/contoso/Platform/_git/downstream-template" in (
        contributing_text
    )
    assert "[Platform](https://dev.azure.com/contoso/Platform)" in contributing_text
    assert "Azure Boards intake policy: work-items" in contributing_text
    assert placeholder_helper.scan_repository(tmp_path) == ()


def test_azure_pr_template_materializes_service_links_and_policy_guidance(
    tmp_path: Path,
) -> None:
    """Azure PR template rendering uses service URLs and names service-backed policies."""
    destination = tmp_path / ".azuredevops" / "pull_request_template.md"
    write_file(
        destination,
        "\n".join(
            [
                "- Project: AZURE_DEVOPS_PROJECT (AZURE_DEVOPS_PROJECT_URL)",
                "- Repository: AZURE_DEVOPS_REPOSITORY (AZURE_DEVOPS_REPOSITORY_WEB_URL)",
                "- Default branch used for PR template discovery: `AZURE_DEVOPS_DEFAULT_BRANCH`.",
                "- Azure Boards intake policy: `AZURE_BOARDS_INTAKE_POLICY`.",
                "- Branch policy reviewer guidance: `AZURE_BRANCH_POLICY_REVIEWER_GUIDANCE`.",
                "- Pull request template policy: `AZURE_REPOS_PR_TEMPLATE_POLICY`.",
                "- Reviewer requirements are enforced by Azure Repos branch policies, "
                "not by this Markdown template.",
                "- Security-sensitive reports are handled through private security intake, "
                "not public Azure Boards work items or PR comments.",
                "- Security-sensitive findings use the private intake policy: "
                "`AZURE_SECURITY_INTAKE_POLICY`.",
            ]
        )
        + "\n",
    )
    context = placeholder_helper.build_replacement_context(
        host_provider="azure-devops-services",
        azure_devops_organization="contoso",
        azure_devops_project="Template Adoption",
        azure_devops_repository="downstream-template",
        azure_boards_policy="work-items",
        azure_branch_policy_reviewer_guidance="required-reviewers",
        azure_security_intake_policy="manual-follow-up",
    )

    records = placeholder_helper.replace_placeholders(repo_root=tmp_path, context=context)

    template_text = read_file(destination)
    assert any(record.path == ".azuredevops/pull_request_template.md" for record in records)
    assert "[Template Adoption](https://dev.azure.com/contoso/Template%20Adoption)" in (
        template_text
    )
    assert (
        "[downstream-template]"
        "(https://dev.azure.com/contoso/Template%20Adoption/_git/downstream-template)"
    ) in template_text
    assert "Default branch used for PR template discovery: `main`." in template_text
    assert "Azure Boards intake policy: `work-items`." in template_text
    assert "Branch policy reviewer guidance: `required-reviewers`." in template_text
    assert "not by this Markdown template" in template_text
    assert "public Azure Boards work items or PR comments" in template_text
    assert "AZURE_" not in template_text
    assert "github.com/OWNER/REPO" not in template_text
    assert placeholder_helper.scan_repository(tmp_path) == ()


def test_default_host_leaves_unrelated_github_com_occurrences_untouched(
    tmp_path: Path,
) -> None:
    """Default substitution does not rewrite unrelated github.com occurrences."""
    write_file(
        tmp_path / "CONTRIBUTING.md",
        "\n".join(
            [
                "git clone https://github.com/OWNER/REPO.git",
                "Upstream: https://github.com/actions/checkout",
            ]
        )
        + "\n",
    )

    placeholder_helper.replace_placeholders(repo_root=tmp_path, context=build_context())

    text = read_file(tmp_path / "CONTRIBUTING.md")
    assert "https://github.com/octo/widget.git" in text
    assert "https://github.com/actions/checkout" in text


def test_scan_reports_unresolved_placeholders(tmp_path: Path) -> None:
    """The audit reports unresolved allowlisted placeholders."""
    write_file(
        tmp_path / ".github" / "ISSUE_TEMPLATE" / "config.yml",
        "url: https://github.com/OWNER/REPO/security\n",
    )
    write_file(tmp_path / ".github" / "CODEOWNERS", "* @OWNER\n")

    findings = placeholder_helper.scan_repository(tmp_path)

    assert {finding.matched_text for finding in findings} == {
        "https://github.com/OWNER/REPO/security",
        "@OWNER",
    }


def test_scan_reports_unresolved_url_placeholders_inside_markdown_delimiters(
    tmp_path: Path,
) -> None:
    """Approved placeholder URLs followed by ) or ] are still reported as unresolved."""
    write_file(
        tmp_path / ".github" / "pull_request_template.md",
        "\n".join(
            [
                "[contrib](https://github.com/OWNER/REPO/blob/HEAD/CONTRIBUTING.md)",
                "[issues](https://github.com/OWNER/REPO/issues)",
                "ref [advisories](https://github.com/OWNER/REPO/security/advisories/new)",
                "bracketed [https://github.com/OWNER/REPO/security]",
            ]
        )
        + "\n",
    )

    findings = placeholder_helper.scan_repository(tmp_path)
    matched = {finding.matched_text for finding in findings}

    assert "https://github.com/OWNER/REPO/blob/HEAD/CONTRIBUTING.md" in matched
    assert "https://github.com/OWNER/REPO/issues" in matched
    assert "https://github.com/OWNER/REPO/security/advisories/new" in matched
    assert "https://github.com/OWNER/REPO/security" in matched


def test_scan_ignores_didactic_owner_repo_text_outside_allowlisted_files(
    tmp_path: Path,
) -> None:
    """Didactic OWNER/REPO prose outside replacement targets is not a failure."""
    write_file(tmp_path / "GETTING_STARTED_NEW_REPO.md", "Replace OWNER/REPO during setup.\n")

    findings = placeholder_helper.scan_repository(tmp_path)

    assert findings == ()


def test_scan_reports_common_corruption_patterns(tmp_path: Path) -> None:
    """The audit catches common REPORT/REPOSITORY/REPOSITORIES corruption."""
    write_file(
        tmp_path / "README.md",
        "\n".join(
            [
                "This octo/widgetRT should have been REPORT.",
                "This widgetSITORY should have been REPOSITORY.",
                "This widgetSITORIES should have been REPOSITORIES.",
            ]
        )
        + "\n",
    )

    findings = placeholder_helper.scan_repository(tmp_path, repository="octo/widget")

    assert {finding.matched_text for finding in findings} == {
        "octo/widgetRT",
        "widgetSITORY",
        "widgetSITORIES",
    }


def test_helper_defines_expected_allowlist_without_standalone_repo_token() -> None:
    """The concrete allowlist covers approved URL shapes and omits broad REPO replacement."""
    assert ".git" in placeholder_helper.APPROVED_GITHUB_URL_SUFFIXES
    assert "/blob/HEAD/CONTRIBUTING.md" in placeholder_helper.APPROVED_GITHUB_URL_SUFFIXES
    assert "/blob/HEAD/SECURITY.md" in placeholder_helper.APPROVED_GITHUB_URL_SUFFIXES
    assert "/security/advisories/new" in placeholder_helper.APPROVED_GITHUB_URL_SUFFIXES
    assert "#support" in placeholder_helper.APPROVED_GITHUB_URL_SUFFIXES
    token_placeholders = {
        placeholder
        for _name, placeholder, _paths, _attribute in placeholder_helper.TOKEN_REPLACEMENT_SPECS
    }
    assert "OWNER/REPO" in token_placeholders
    assert "REPO" not in token_placeholders


def test_replace_help_documents_security_reporting_modes(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The replace help output documents every supported reporting mode."""
    with pytest.raises(SystemExit) as error:
        placeholder_helper.main(["replace", "--help"])

    captured = capsys.readouterr()
    assert error.value.code == 0
    assert "github-private-only" in captured.out
    assert "contact-only" in captured.out
    assert "both" in captured.out


def test_cli_rejects_missing_security_mode_and_contact(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The helper rejects ambiguous reporting configuration."""
    result = placeholder_helper.main(
        ["replace", "--repository", "octo/widget", "--repo-root", str(tmp_path)]
    )

    captured = capsys.readouterr()
    assert result == 1
    assert "Either --security-reporting-mode or --security-contact is required" in captured.err


def test_repository_less_security_overrides_without_mode_fail_fast(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Security overrides that cannot render fail fast instead of being silently ignored."""
    # A repository-less section override with no explicit reporting mode is rejected
    # rather than silently dropped (the security reporting section is not rendered).
    with pytest.raises(placeholder_helper.PlaceholderError, match="security-reporting-mode"):
        placeholder_helper.build_replacement_context(
            security_contact_section="### Security Intake\n\nReach us.\n",
        )
    with pytest.raises(placeholder_helper.PlaceholderError):
        placeholder_helper.build_replacement_context(security_contact="security@example.com")

    # The CLI surfaces the actionable error.
    result = placeholder_helper.main(
        [
            "replace",
            "--repo-root",
            str(tmp_path),
            "--security-contact-section",
            "### Security Intake\n\nReach us.\n",
        ]
    )
    captured = capsys.readouterr()
    assert result == 1
    assert "--security-reporting-mode" in captured.err

    # An explicit contact-only mode makes a repository-less override valid, and
    # Code-of-Conduct-only inputs remain valid repository-less (not a security override).
    context = placeholder_helper.build_replacement_context(
        security_contact_section="### Security Intake\n\nReach us.\n",
        security_reporting_mode="contact-only",
    )
    assert context.security_reporting_mode == "contact-only"
    assert (
        placeholder_helper.build_replacement_context(
            conduct_contact="conduct@example.com",
        ).security_reporting_mode
        is None
    )


def test_json_args_file_supplies_shell_sensitive_identity_and_package_metadata(
    tmp_path: Path,
) -> None:
    """JSON args files carry shell-sensitive identity values and package metadata."""
    write_file(tmp_path / ".github" / "CODEOWNERS", "* @OWNER\n")
    write_file(tmp_path / "CODE_OF_CONDUCT.md", "Contact: [INSERT CONTACT METHOD]\n")
    write_file(
        tmp_path / "SECURITY.md",
        "\n".join(
            [
                "## Reporting a Vulnerability",
                "",
                "**Please do NOT report security vulnerabilities through public GitHub issues.**",
                "",
                "If you discover a security vulnerability in this project, report it privately "
                "using the contact method below.",
                "",
                "### Security Contact",
                "",
                "Contact the maintainers directly at:",
                "",
                "<!-- TODO: Replace with your security contact email -->",
                "<!-- Do not use a users.noreply.github.com address as a security "
                "intake channel. -->",
                "- Contact: [security contact email]",
                "",
                "### What to Include",
            ]
        )
        + "\n",
    )
    write_json(
        tmp_path / "package.json",
        {
            "name": "copilot-repo-template",
            "version": "1.0.0",
            "description": "Template repository with Copilot instructions",
            "private": True,
            "keywords": ["template"],
            "author": "Frank Lesniak",
        },
    )
    write_json(
        tmp_path / "package-lock.json",
        {
            "name": "copilot-repo-template",
            "version": "1.0.0",
            "lockfileVersion": 3,
            "packages": {
                "": {
                    "name": "copilot-repo-template",
                    "version": "1.0.0",
                    "dependencies": {"left-pad": "1.3.0"},
                },
                "node_modules/left-pad": {
                    "version": "1.3.0",
                    "resolved": "https://registry.npmjs.org/left-pad/-/left-pad-1.3.0.tgz",
                },
            },
        },
    )
    args_file = write_json(
        tmp_path / "identity.args.json",
        {
            "repository": "octo/widget",
            "security_reporting_mode": "contact-only",
            "security_contact": "sec$ops, hotline@example.com",
            "conduct_contact": "conduct team, $literal inbox",
            "codeowners_owner": "@octo/platform-team",
            "package_name": "widget-docs",
            "package_description": "Docs, tools, and $literal examples",
            "package_author": "Example Org",
            "package_keywords": ["docs", "ops team"],
        },
    )

    result = placeholder_helper.main(
        ["replace", "--repo-root", str(tmp_path), "--args-file", str(args_file)]
    )

    assert result == 0
    assert "* @octo/platform-team" in read_file(tmp_path / ".github" / "CODEOWNERS")
    assert "conduct team, $literal inbox" in read_file(tmp_path / "CODE_OF_CONDUCT.md")
    assert "sec$ops, hotline@example.com" in read_file(tmp_path / "SECURITY.md")

    package_json = json.loads(read_file(tmp_path / "package.json"))
    assert package_json["name"] == "widget-docs"
    assert package_json["version"] == "1.0.0"
    assert package_json["description"] == "Docs, tools, and $literal examples"
    assert package_json["author"] == "Example Org"
    assert package_json["keywords"] == ["docs", "ops team"]

    package_lock = json.loads(read_file(tmp_path / "package-lock.json"))
    assert package_lock["name"] == "widget-docs"
    assert package_lock["version"] == "1.0.0"
    assert package_lock["packages"][""]["name"] == "widget-docs"
    assert package_lock["packages"][""]["version"] == "1.0.0"
    assert package_lock["packages"]["node_modules/left-pad"]["version"] == "1.3.0"


def test_cli_values_take_precedence_over_args_file_values(tmp_path: Path) -> None:
    """Direct CLI flags override lower-priority args-file values."""
    write_file(tmp_path / ".github" / "CODEOWNERS", "* @OWNER\n")
    args_file = write_json(
        tmp_path / "identity.json",
        {
            "repository": "octo/widget",
            "security_contact": "security@example.com",
            "codeowners_owner": "@octo/from-file",
        },
    )

    result = placeholder_helper.main(
        [
            "replace",
            "--repo-root",
            str(tmp_path),
            "--args-file",
            str(args_file),
            "--codeowners-owner",
            "@octo/from-cli",
        ]
    )

    assert result == 0
    assert read_file(tmp_path / ".github" / "CODEOWNERS") == "* @octo/from-cli\n"


def test_values_beginning_with_at_work_without_args_file_magic(tmp_path: Path) -> None:
    """A CODEOWNERS owner beginning with @ is a normal value, not an args-file marker."""
    write_file(tmp_path / ".github" / "CODEOWNERS", "* @OWNER\n")

    result = placeholder_helper.main(
        [
            "replace",
            "--repo-root",
            str(tmp_path),
            "--repository",
            "octo/widget",
            "--security-contact",
            "security@example.com",
            "--codeowners-owner",
            "@octo/platform-team",
        ]
    )

    assert result == 0
    assert read_file(tmp_path / ".github" / "CODEOWNERS") == "* @octo/platform-team\n"


def test_yaml_args_file_is_supported_when_yaml_parser_is_available(tmp_path: Path) -> None:
    """YAML args files parse through the retained YAML parser path."""
    write_file(tmp_path / ".github" / "CODEOWNERS", "* @OWNER\n")
    args_file = tmp_path / "identity.yml"
    write_file(
        args_file,
        yaml.safe_dump(
            {
                "repository": "octo/widget",
                "security_contact": "security@example.com",
                "codeowners_owner": "@octo/yaml-team",
            },
            sort_keys=False,
        ),
    )

    result = placeholder_helper.main(
        ["replace", "--repo-root", str(tmp_path), "--args-file", str(args_file)]
    )

    assert result == 0
    assert read_file(tmp_path / ".github" / "CODEOWNERS") == "* @octo/yaml-team\n"


def test_yaml_args_file_unavailable_message_is_actionable(tmp_path: Path) -> None:
    """Unavailable YAML support tells operators to use JSON or enable YAML support."""
    args_file = write_file(tmp_path / "identity.yml", "repository: octo/widget\n")

    def missing_yaml(_module_name: str) -> object:
        raise ImportError("yaml unavailable")

    with pytest.raises(placeholder_helper.PlaceholderError) as excinfo:
        placeholder_helper.load_args_file_mapping(
            str(args_file),
            "yaml",
            yaml_module_loader=missing_yaml,
        )

    message = str(excinfo.value)
    assert "Convert the args file to JSON" in message
    assert "enable the repository's retained YAML support" in message


def test_args_format_override_and_unknown_extension_diagnostics(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Unknown extensions require --args-format, and explicit format wins."""
    write_file(tmp_path / ".github" / "CODEOWNERS", "* @OWNER\n")
    args_file = write_json(
        tmp_path / "identity.arguments",
        {
            "repository": "octo/widget",
            "security_contact": "security@example.com",
            "codeowners_owner": "@octo/format-team",
        },
    )

    missing_format = placeholder_helper.main(
        ["replace", "--repo-root", str(tmp_path), "--args-file", str(args_file)]
    )
    missing_format_output = capsys.readouterr()
    assert missing_format == 1
    assert "Unable to determine --args-file format" in missing_format_output.err

    explicit_format = placeholder_helper.main(
        [
            "replace",
            "--repo-root",
            str(tmp_path),
            "--args-file",
            str(args_file),
            "--args-format",
            "json",
        ]
    )

    assert explicit_format == 0
    assert read_file(tmp_path / ".github" / "CODEOWNERS") == "* @octo/format-team\n"

    write_file(tmp_path / ".github" / "CODEOWNERS", "* @OWNER\n")
    json_named_yaml = write_json(
        tmp_path / "identity.yaml",
        {
            "repository": "octo/widget",
            "security_contact": "security@example.com",
            "codeowners_owner": "@octo/json-override-team",
        },
    )
    override_recognized_extension = placeholder_helper.main(
        [
            "replace",
            "--repo-root",
            str(tmp_path),
            "--args-file",
            str(json_named_yaml),
            "--args-format",
            "json",
        ]
    )

    assert override_recognized_extension == 0
    assert read_file(tmp_path / ".github" / "CODEOWNERS") == "* @octo/json-override-team\n"


@pytest.mark.parametrize(
    ("args_data", "expected"),
    [
        pytest.param({"unknown": "value"}, "Unknown --args-file field", id="unknown-field"),
        pytest.param({"repository": ["octo/widget"]}, "must be a string", id="invalid-type"),
    ],
)
def test_args_file_schema_errors_are_actionable(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    args_data: dict[str, object],
    expected: str,
) -> None:
    """Unknown fields and type errors name the args-file problem."""
    args_file = write_json(tmp_path / "identity.json", args_data)

    result = placeholder_helper.main(["replace", "--args-file", str(args_file)])

    captured = capsys.readouterr()
    assert result == 1
    assert expected in captured.err


def test_missing_args_file_is_actionable(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Missing args files report an actionable read failure."""
    result = placeholder_helper.main(["replace", "--args-file", str(tmp_path / "missing.json")])

    captured = capsys.readouterr()
    assert result == 1
    assert "--args-file: unable to read file" in captured.err


def test_args_file_with_utf8_bom_is_parsed(tmp_path: Path) -> None:
    """A UTF-8 BOM (e.g. PowerShell Set-Content -Encoding UTF8) in an args file is tolerated."""
    args_file = tmp_path / "adoption-identity.json"
    args_file.write_bytes(
        b"\xef\xbb\xbf" + json.dumps({"repository": "octo/widget"}).encode("utf-8")
    )

    mapping = placeholder_helper.load_args_file_mapping(str(args_file), None)

    assert mapping == {"repository": "octo/widget"}


@pytest.mark.upstream_template_only
def test_contact_sentence_and_security_section_overrides(tmp_path: Path) -> None:
    """Whole-sentence and whole-section contact overrides avoid awkward token grammar."""
    copy_security_reporting_fixture(tmp_path)
    conduct_sentence = (
        "Report possible Code of Conduct violations using the private conduct form "
        "at https://example.com/conduct."
    )
    security_section = (
        "### Security Intake\n\n"
        "Use the monitored security desk at security@example.com; include impact details.\n"
    )

    result = placeholder_helper.main(
        [
            "replace",
            "--repo-root",
            str(tmp_path),
            "--repository",
            "octo/widget",
            "--security-reporting-mode",
            "contact-only",
            "--conduct-contact-sentence",
            conduct_sentence,
            "--security-contact-section",
            security_section,
        ]
    )

    assert result == 0
    code_of_conduct = read_file(tmp_path / "CODE_OF_CONDUCT.md")
    security_text = read_file(tmp_path / "SECURITY.md")
    assert conduct_sentence in code_of_conduct
    assert "[INSERT CONTACT METHOD]" not in code_of_conduct
    assert "### Security Intake" in security_text
    assert "[security contact email]" not in security_text
    assert "TODO: Replace" not in security_text


def test_package_lock_version_changes_only_when_package_version_is_explicit(
    tmp_path: Path,
) -> None:
    """Lockfile root versions stay fixed unless --package-version is supplied."""
    package_json = {
        "name": "copilot-repo-template",
        "version": "1.0.0",
        "description": "Template repository",
        "author": "Frank Lesniak",
    }
    package_lock = {
        "name": "copilot-repo-template",
        "version": "1.0.0",
        "lockfileVersion": 3,
        "packages": {
            "": {
                "name": "copilot-repo-template",
                "version": "1.0.0",
            },
            "node_modules/example": {"version": "9.9.9"},
        },
    }
    write_json(tmp_path / "package.json", package_json)
    write_json(tmp_path / "package-lock.json", package_lock)

    name_only_context = placeholder_helper.build_replacement_context(
        package_name="downstream-package"
    )
    placeholder_helper.replace_placeholders(tmp_path, name_only_context)
    name_only_lock = json.loads(read_file(tmp_path / "package-lock.json"))
    assert name_only_lock["name"] == "downstream-package"
    assert name_only_lock["version"] == "1.0.0"
    assert name_only_lock["packages"][""]["name"] == "downstream-package"
    assert name_only_lock["packages"][""]["version"] == "1.0.0"

    version_context = placeholder_helper.build_replacement_context(package_version="2.0.0")
    placeholder_helper.replace_placeholders(tmp_path, version_context)
    versioned_package = json.loads(read_file(tmp_path / "package.json"))
    versioned_lock = json.loads(read_file(tmp_path / "package-lock.json"))
    assert versioned_package["version"] == "2.0.0"
    assert versioned_lock["version"] == "2.0.0"
    assert versioned_lock["packages"][""]["version"] == "2.0.0"
    assert versioned_lock["packages"]["node_modules/example"]["version"] == "9.9.9"


def test_package_lock_without_packages_object_yields_actionable_error() -> None:
    """A lockfileVersion 1 package-lock.json gives an actionable error for identity updates."""
    file_texts = {
        "package-lock.json": json.dumps(
            {"name": "x", "version": "1.0.0", "lockfileVersion": 1, "dependencies": {}}
        )
        + "\n"
    }
    context = placeholder_helper.build_replacement_context(package_name="downstream-tools")

    with pytest.raises(placeholder_helper.PlaceholderError) as excinfo:
        placeholder_helper.update_package_lock_identity(file_texts, context)

    message = str(excinfo.value)
    assert "lockfileVersion" in message
    assert "npm install --package-lock-only" in message


def test_check_placeholders_workflow_delegates_hard_fail_allowlist_to_helper() -> None:
    """The workflow hard-fail path uses the helper's allowlist-backed scan."""
    workflow = read_file(REPO_ROOT / ".github" / "workflows" / "check-placeholders.yml")

    assert "replace-template-placeholders.py scan" in workflow
    assert "hard-fail allowlist lives" in workflow


@pytest.mark.parametrize(
    ("mode_args", "expected_mode"),
    [
        pytest.param(
            ["--security-contact", "security@example.com"],
            "both",
            id="omitted-mode-backward-compatible-both",
        ),
        pytest.param(
            [
                "--security-reporting-mode",
                "both",
                "--security-contact",
                "security@example.com",
            ],
            "both",
            id="explicit-both",
        ),
        pytest.param(
            [
                "--security-reporting-mode",
                "contact-only",
                "--security-contact",
                "security@example.com",
            ],
            "contact-only",
            id="contact-only",
        ),
        pytest.param(
            ["--security-reporting-mode", "github-private-only"],
            "github-private-only",
            id="github-private-only",
        ),
    ],
)
@pytest.mark.upstream_template_only
def test_security_reporting_modes_render_consistent_surfaces(
    tmp_path: Path,
    mode_args: list[str],
    expected_mode: str,
) -> None:
    """Security reporting modes render SECURITY.md and issue templates consistently."""
    copy_security_reporting_fixture(tmp_path)

    result = placeholder_helper.main(
        [
            "replace",
            "--repo-root",
            str(tmp_path),
            "--repository",
            "octo/widget",
            "--conduct-contact",
            "conduct@example.com",
            *mode_args,
        ]
    )

    assert result == 0
    assert placeholder_helper.scan_repository(tmp_path, repository="octo/widget") == ()
    assert "[INSERT CONTACT METHOD]" not in read_file(tmp_path / "CODE_OF_CONDUCT.md")
    assert "conduct@example.com" in read_file(tmp_path / "CODE_OF_CONDUCT.md")

    config = load_yaml(tmp_path / ".github" / "ISSUE_TEMPLATE" / "config.yml")
    contact_link = security_contact_link(config)
    assert set(contact_link) == {"name", "url", "about"}
    assert_issue_form_shape(load_yaml(tmp_path / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml"))

    security_text = read_file(tmp_path / "SECURITY.md")
    config_text = read_file(tmp_path / ".github" / "ISSUE_TEMPLATE" / "config.yml")
    bug_text = read_file(tmp_path / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml")
    combined_security_surfaces = "\n".join((security_text, config_text, bug_text))

    assert "[security contact email]" not in security_text
    assert "TODO: Replace" not in security_text

    # Regression: the rendered reporting section must keep a blank line before the
    # following heading so downstream markdownlint (MD022/MD032) does not fail.
    assert "\n\n### What to Include" in security_text

    if expected_mode == "contact-only":
        assert "security@example.com" in security_text
        assert contact_link["url"] == "https://github.com/octo/widget/blob/HEAD/SECURITY.md"
        assert "/security/advisories/new" not in combined_security_surfaces
        assert "GitHub Security Advisories" not in combined_security_surfaces
        assert "private vulnerability reporting" not in combined_security_surfaces
        assert "private reporting form" not in combined_security_surfaces
    elif expected_mode == "github-private-only":
        assert "security@example.com" not in security_text
        assert "Security Contact" not in security_text
        assert "Contact:" not in security_text
        # The issue chooser link always points at SECURITY.md (always reachable),
        # even though SECURITY.md itself renders the advisory form for this mode.
        assert contact_link["url"] == "https://github.com/octo/widget/blob/HEAD/SECURITY.md"
        assert "GitHub Security Advisories" in security_text
        assert "private vulnerability reporting" in combined_security_surfaces
    else:
        assert "security@example.com" in security_text
        assert contact_link["url"] == "https://github.com/octo/widget/blob/HEAD/SECURITY.md"
        assert "GitHub Security Advisories" in security_text
        assert "private vulnerability reporting" in combined_security_surfaces


@pytest.mark.upstream_template_only
def test_collaboration_policy_renders_labels_and_discussions(
    tmp_path: Path,
) -> None:
    """Collaboration policy inputs render issue labels and Discussions contact links."""
    copy_security_reporting_fixture(tmp_path)
    follow_up_status = "Enable labels and Discussions before accepting public intake."

    result = placeholder_helper.main(
        [
            "replace",
            "--repo-root",
            str(tmp_path),
            "--repository",
            "octo/widget",
            "--security-contact",
            "security@example.com",
            "--conduct-contact",
            "conduct@example.com",
            "--issue-label-policy",
            "create-manual-follow-up",
            "--discussions-policy",
            "deferred-planned-render",
            "--collaboration-policy-follow-up-status",
            follow_up_status,
        ]
    )

    assert result == 0
    assert placeholder_helper.scan_repository(tmp_path, repository="octo/widget") == ()

    bug_report = load_yaml(tmp_path / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml")
    assert isinstance(bug_report, dict)
    assert bug_report["labels"] == ["bug", "triage"]
    config = load_yaml(tmp_path / ".github" / "ISSUE_TEMPLATE" / "config.yml")
    discussions_link = contact_link_by_name(config, "Questions & Discussions")
    assert discussions_link["url"] == "https://github.com/octo/widget/discussions"

    combined_text = "\n".join(
        (
            read_file(tmp_path / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml"),
            read_file(tmp_path / ".github" / "ISSUE_TEMPLATE" / "config.yml"),
        )
    )
    assert "_TODO-repo-init.md dependent-file status remains open" in combined_text
    assert follow_up_status in combined_text


@pytest.mark.upstream_template_only
def test_collaboration_policy_can_omit_labels_and_disable_discussions(
    tmp_path: Path,
) -> None:
    """Omit/disabled policies remove active label and Discussions output."""
    copy_security_reporting_fixture(tmp_path)

    result = placeholder_helper.main(
        [
            "replace",
            "--repo-root",
            str(tmp_path),
            "--repository",
            "octo/widget",
            "--security-contact",
            "security@example.com",
            "--conduct-contact",
            "conduct@example.com",
            "--issue-label-policy",
            "omit",
            "--discussions-policy",
            "disabled",
        ]
    )

    assert result == 0
    bug_report = load_yaml(tmp_path / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml")
    assert isinstance(bug_report, dict)
    assert "labels" not in bug_report
    config_text = read_file(tmp_path / ".github" / "ISSUE_TEMPLATE" / "config.yml")
    assert "/discussions" not in config_text
    assert "Support / FAQ" not in config_text
    assert_issue_form_shape(bug_report)


def test_replace_config_discussions_block_preserves_trailing_content() -> None:
    """Rendering the Discussions policy keeps contact-link content after Support/FAQ."""
    text = (
        "contact_links:\n"
        "  # =============================================================================\n"
        "  # DISCUSSIONS LINK (OPTIONAL)\n"
        "  # =============================================================================\n"
        "  # CUSTOMIZE: Uncomment to enable Discussions.\n"
        "  # - name: Questions & Discussions\n"
        "  #   url: https://github.com/OWNER/REPO/discussions\n"
        "\n"
        "  # =============================================================================\n"
        "  # SUPPORT / FAQ LINK (OPTIONAL)\n"
        "  # =============================================================================\n"
        "  # - name: Support / FAQ\n"
        "  #   url: https://github.com/OWNER/REPO#support\n"
        "\n"
        "  # =============================================================================\n"
        "  # ENTERPRISE SUPPORT LINK\n"
        "  # =============================================================================\n"
        "  - name: Enterprise Support\n"
        "    url: https://github.com/OWNER/REPO/enterprise\n"
    )
    context = placeholder_helper.build_replacement_context(discussions_policy="disabled")

    rendered, count = placeholder_helper.replace_config_discussions_block(text, context)

    assert count == 1
    assert "SUPPORT / FAQ LINK" not in rendered
    assert "/discussions" not in rendered
    assert "Discussions policy: disabled" in rendered
    # Content after the superseded Support/FAQ section must be preserved verbatim.
    assert "# ENTERPRISE SUPPORT LINK" in rendered
    assert "name: Enterprise Support" in rendered
    assert rendered.endswith(
        "  - name: Enterprise Support\n    url: https://github.com/OWNER/REPO/enterprise\n"
    )


def test_collaboration_policy_validates_custom_labels_and_deferred_status() -> None:
    """Invalid collaboration policy combinations fail before rendering."""
    with pytest.raises(placeholder_helper.PlaceholderError) as custom_exc:
        placeholder_helper.build_replacement_context(issue_label_policy="custom")
    assert "--issue-label-policy custom requires" in str(custom_exc.value)

    with pytest.raises(placeholder_helper.PlaceholderError) as follow_up_exc:
        placeholder_helper.build_replacement_context(
            discussions_policy="deferred-planned-render",
        )
    assert "--collaboration-policy-follow-up-status is required" in str(follow_up_exc.value)


@pytest.mark.parametrize(
    ("mode_args", "expected_fragment"),
    [
        pytest.param(
            ["--security-reporting-mode", "github-private-only"],
            "/blob/HEAD/SECURITY.md",
            id="github-private-only",
        ),
        pytest.param(
            [
                "--security-reporting-mode",
                "contact-only",
                "--security-contact",
                "security@example.com",
            ],
            "/blob/HEAD/SECURITY.md",
            id="contact-only",
        ),
        pytest.param(
            ["--security-reporting-mode", "both", "--security-contact", "security@example.com"],
            "/blob/HEAD/SECURITY.md",
            id="both",
        ),
    ],
)
@pytest.mark.upstream_template_only
def test_security_reporting_modes_preserve_github_host_override(
    tmp_path: Path,
    mode_args: list[str],
    expected_fragment: str,
) -> None:
    """GHES host substitution works for every security reporting mode."""
    copy_security_reporting_fixture(tmp_path)

    result = placeholder_helper.main(
        [
            "replace",
            "--repo-root",
            str(tmp_path),
            "--repository",
            "octo/widget",
            "--github-host",
            "github.company.com",
            "--conduct-contact",
            "conduct@example.com",
            *mode_args,
        ]
    )

    assert result == 0
    config = load_yaml(tmp_path / ".github" / "ISSUE_TEMPLATE" / "config.yml")
    contact_link = security_contact_link(config)
    assert contact_link["url"] == f"https://github.company.com/octo/widget{expected_fragment}"
    for relative_path in (
        "SECURITY.md",
        ".github/ISSUE_TEMPLATE/config.yml",
        ".github/ISSUE_TEMPLATE/bug_report.yml",
    ):
        text = read_file(tmp_path / relative_path)
        assert "https://github.com/octo/widget" not in text
    assert placeholder_helper.scan_repository(tmp_path, repository="octo/widget") == ()


@pytest.mark.upstream_template_only
def test_github_private_only_requires_conduct_contact_when_code_of_conduct_retained(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A missing security contact is not silently reused for Code of Conduct contact."""
    copy_security_reporting_fixture(tmp_path)

    result = placeholder_helper.main(
        [
            "replace",
            "--repo-root",
            str(tmp_path),
            "--repository",
            "octo/widget",
            "--security-reporting-mode",
            "github-private-only",
        ]
    )

    captured = capsys.readouterr()
    assert result == 1
    assert "CODE_OF_CONDUCT.md contains [INSERT CONTACT METHOD]" in captured.err


@pytest.mark.parametrize(
    "argv",
    [
        ["replace", "--repository", "octo/widget", "--security-contact", ""],
        [
            "replace",
            "--repository",
            "octo/widget",
            "--security-contact",
            "security@example.com",
            "--github-host",
            "https://github.company.com",
        ],
    ],
)
def test_cli_rejects_empty_or_unsafe_values(
    tmp_path: Path,
    argv: list[str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The CLI rejects empty required values and unsafe host overrides."""
    result = placeholder_helper.main([*argv, "--repo-root", str(tmp_path)])

    captured = capsys.readouterr()
    assert result == 1
    assert captured.err.startswith("ERROR:")


def test_url_replacement_does_not_rewrite_unapproved_longer_urls(tmp_path: Path) -> None:
    """The bare https://github.com/OWNER/REPO placeholder must not prefix-rewrite longer URLs."""
    write_file(
        tmp_path / "CONTRIBUTING.md",
        "\n".join(
            [
                "Issues: https://github.com/OWNER/REPO/issues",
                "Other: https://github.com/OWNER/REPO/contributions",
                "Stars: https://github.com/OWNER/REPO/stargazers",
            ]
        )
        + "\n",
    )

    placeholder_helper.replace_placeholders(repo_root=tmp_path, context=build_context())

    text = read_file(tmp_path / "CONTRIBUTING.md")
    assert "https://github.com/octo/widget/issues" in text
    assert "https://github.com/OWNER/REPO/contributions" in text
    assert "https://github.com/OWNER/REPO/stargazers" in text


def test_replace_placeholders_does_not_rewrite_unchanged_files(tmp_path: Path) -> None:
    """Files without any approved-placeholder replacements keep their original mtime."""
    unchanged = write_file(
        tmp_path / "CODE_OF_CONDUCT.md",
        "Contact: conduct@already-replaced.example\n",
    )
    changed = write_file(
        tmp_path / "CONTRIBUTING.md",
        "git clone https://github.com/OWNER/REPO.git\n",
    )
    import os

    old_mtime_ns = 1700000000_000000000
    os.utime(unchanged, ns=(old_mtime_ns, old_mtime_ns))
    os.utime(changed, ns=(old_mtime_ns, old_mtime_ns))

    placeholder_helper.replace_placeholders(repo_root=tmp_path, context=build_context())

    assert unchanged.stat().st_mtime_ns == old_mtime_ns
    assert changed.stat().st_mtime_ns != old_mtime_ns
    assert "octo/widget" in read_file(changed)
    assert read_file(unchanged) == "Contact: conduct@already-replaced.example\n"


def test_owner_repo_token_does_not_replace_prefix_of_longer_token(tmp_path: Path) -> None:
    """OWNER/REPO must not match when it is a prefix of a longer repo-name token."""
    write_file(
        tmp_path / "CONTRIBUTING.md",
        "\n".join(
            [
                "Mirror to OWNER/REPOSITORY for archival.",
                "Mirror to OWNER/REPORT for archival.",
                "Mirror to OWNER/REPO_TEST for archival.",
                "Mirror to OWNER/REPO-TEST for archival.",
                "Mirror to OWNER/REPO123 for archival.",
                "Replace OWNER/REPO. End of sentence.",
                "Standalone OWNER/REPO works.",
            ]
        )
        + "\n",
    )

    placeholder_helper.replace_placeholders(repo_root=tmp_path, context=build_context())

    text = read_file(tmp_path / "CONTRIBUTING.md")
    assert "OWNER/REPOSITORY" in text
    assert "OWNER/REPORT" in text
    assert "OWNER/REPO_TEST" in text
    assert "OWNER/REPO-TEST" in text
    assert "OWNER/REPO123" in text
    assert "Replace octo/widget. End of sentence." in text
    assert "Standalone octo/widget works." in text


def test_resolve_repo_path_rejects_symlinked_allowlisted_file(tmp_path: Path) -> None:
    """An allowlisted path that is itself a symlink is rejected before resolution."""
    target = tmp_path / "real_codeowners"
    target.write_text("* @real\n", encoding="utf-8")
    link = tmp_path / ".github" / "CODEOWNERS"
    link.parent.mkdir(parents=True, exist_ok=True)
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError) as error:
        pytest.skip(f"symlink creation not supported in this environment: {error}")

    with pytest.raises(placeholder_helper.PlaceholderError, match="must not traverse a symlink"):
        placeholder_helper.resolve_repo_path(tmp_path, ".github/CODEOWNERS")


def test_resolve_repo_path_rejects_symlinked_parent_directory(tmp_path: Path) -> None:
    """An allowlisted path whose parent is a symlink is rejected before resolution."""
    real_dir = tmp_path / "real_dot_github"
    real_dir.mkdir()
    (real_dir / "CODEOWNERS").write_text("* @real\n", encoding="utf-8")
    try:
        (tmp_path / ".github").symlink_to(real_dir)
    except (OSError, NotImplementedError) as error:
        pytest.skip(f"symlink creation not supported in this environment: {error}")

    with pytest.raises(placeholder_helper.PlaceholderError, match="must not traverse a symlink"):
        placeholder_helper.resolve_repo_path(tmp_path, ".github/CODEOWNERS")
