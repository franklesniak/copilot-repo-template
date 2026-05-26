"""Tests for the exact template placeholder replacement helper."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / ".github" / "scripts" / "replace-template-placeholders.py"
)
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


def test_cli_rejects_missing_security_contact(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """argparse rejects a missing required security contact."""
    with pytest.raises(SystemExit) as error:
        placeholder_helper.main(
            ["replace", "--repository", "octo/widget", "--repo-root", str(tmp_path)]
        )

    captured = capsys.readouterr()
    assert error.value.code == 2
    assert "security-contact" in captured.err


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
