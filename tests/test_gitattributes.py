"""Regression tests for repository Git attribute defaults."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
ATTRIBUTES_TO_CHECK = ("text", "eol", "diff")
LF_PINNED_TEXT_PATHS = (
    "README.md",
    ".cursor/rules/repository-instructions.mdc",
    "templates/powershell/Example.Tests.ps1",
    ".github/linting/PSScriptAnalyzerSettings.psd1",
    "src/example/module.psm1",
    "package.json",
    ".markdownlint.jsonc",
    "pyproject.toml",
    ".github/scripts/lint-nested-markdown.js",
    ".remarkrc.mjs",
    "src/copilot_repo_template/example.py",
    ".github/workflows/precommit-ci.yml",
)
BINARY_OVERRIDE_PATHS = (
    "tests/fixtures/screenshot.png",
    "tests/snapshots/archive.zip",
    "testdata/font.ttf",
)


def git_check_attributes(paths: tuple[str, ...]) -> dict[str, dict[str, str]]:
    """Return selected Git attributes for repository-relative paths."""
    result = subprocess.run(
        ["git", "check-attr", *ATTRIBUTES_TO_CHECK, "--", *paths],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr

    attributes_by_path: dict[str, dict[str, str]] = {path: {} for path in paths}
    for line in result.stdout.splitlines():
        path, attribute, value = line.split(": ", 2)
        attributes_by_path[path][attribute] = value
    return attributes_by_path


@pytest.mark.parametrize("path", LF_PINNED_TEXT_PATHS)
def test_template_text_paths_are_pinned_to_lf(path: str) -> None:
    """Template-managed text formats must use LF across platforms."""
    attributes = git_check_attributes((path,))

    assert attributes[path]["text"] == "set"
    assert attributes[path]["eol"] == "lf"


@pytest.mark.parametrize("path", BINARY_OVERRIDE_PATHS)
def test_binary_overrides_disable_text_conversion(path: str) -> None:
    """Binary overrides must win over broad text and fixture pins."""
    attributes = git_check_attributes((path,))

    assert attributes[path]["text"] == "unset"
    assert attributes[path]["diff"] == "unset"
