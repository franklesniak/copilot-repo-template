"""Tests for the exact template placeholder replacement helper."""

from __future__ import annotations

import importlib.util
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


def build_context(**overrides: object) -> object:
    """Build a replacement context with test defaults."""
    values = {
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
    assert isinstance(config, dict)
    contact_links = config["contact_links"]
    assert isinstance(contact_links, list)
    for contact_link in contact_links:
        assert isinstance(contact_link, dict)
        if contact_link.get("name") == "Security Vulnerabilities":
            return contact_link
    raise AssertionError("Security Vulnerabilities contact link not found")


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
