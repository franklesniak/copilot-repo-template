"""Regression tests for repository Git attribute defaults."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
ATTRIBUTES_TO_CHECK = ("text", "eol", "filter", "diff", "merge")
LFS_ATTRIBUTES_TO_CHECK = ("filter", "diff", "merge", "text")
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
    ".claude/hooks/session-start.sh",
    ".gitattributes",
    "nested/.gitattributes",
    ".github/CODEOWNERS",
    "CODEOWNERS",
    "docs/CODEOWNERS",
    "nested/CODEOWNERS",
    ".gitignore",
    ".remarkignore",
    ".dockerignore",
    "nested/.gitignore",
    ".tflint.hcl",
    "LICENSE",
    "templates/terraform/Example.tftest.hcl",
    "main.tf",
    "terraform.tfvars",
    "example.tftpl",
    "backend.tfbackend",
)
BINARY_OVERRIDE_PATHS = (
    "tests/fixtures/screenshot.png",
    "tests/snapshots/archive.zip",
    "testdata/font.ttf",
)
GIT_LFS_MARKER_BEGIN = "# template-sync: begin git-lfs-only"
GIT_LFS_MARKER_END = "# template-sync: end git-lfs-only"
GIT_LFS_ATTRIBUTE_LINES = (
    "*.psd                         filter=lfs diff=lfs merge=lfs -text",
    "*.psb                         filter=lfs diff=lfs merge=lfs -text",
    "*.ai                          filter=lfs diff=lfs merge=lfs -text",
    "*.indd                        filter=lfs diff=lfs merge=lfs -text",
    "*.sketch                      filter=lfs diff=lfs merge=lfs -text",
    "*.fig                         filter=lfs diff=lfs merge=lfs -text",
    "*.blend                       filter=lfs diff=lfs merge=lfs -text",
    "*.fbx                         filter=lfs diff=lfs merge=lfs -text",
    "*.dwg                         filter=lfs diff=lfs merge=lfs -text",
)
GIT_LFS_MANAGED_PATHS = (
    "assets/source/poster.psd",
    "assets/source/poster.psb",
    "assets/source/identity.ai",
    "assets/source/layout.indd",
    "assets/source/wireframe.sketch",
    "assets/source/mockup.fig",
    "assets/source/scene.blend",
    "assets/source/model.fbx",
    "assets/source/plan.dwg",
)
NESTED_LICENSE_PATHS = ("nested/LICENSE", "docs/LICENSE")


def git_check_attributes(
    paths: tuple[str, ...],
    attributes: tuple[str, ...] = ATTRIBUTES_TO_CHECK,
) -> dict[str, dict[str, str]]:
    """Return repository-controlled Git attributes for repository-relative paths."""
    with tempfile.TemporaryDirectory(prefix="gitattributes-test-") as temp_directory:
        repo_root = Path(temp_directory)
        subprocess.run(
            ["git", "init", "-q"],
            cwd=repo_root,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        (repo_root / ".gitattributes").write_text(
            (REPO_ROOT / ".gitattributes").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        info_attributes = repo_root / ".git" / "info" / "attributes"
        info_attributes.write_text("", encoding="utf-8")
        global_attributes = repo_root / "empty-global-attributes"
        global_attributes.write_text("", encoding="utf-8")

        env = os.environ.copy()
        env["GIT_ATTR_NOSYSTEM"] = "1"
        result = subprocess.run(
            [
                "git",
                "-c",
                f"core.attributesFile={global_attributes.as_posix()}",
                "check-attr",
                *attributes,
                "--",
                *paths,
            ],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )
    assert result.returncode == 0, result.stderr

    attributes_by_path: dict[str, dict[str, str]] = {path: {} for path in paths}
    for line in result.stdout.splitlines():
        path, attribute, value = line.split(": ", 2)
        attributes_by_path[path][attribute] = value
    return attributes_by_path


def git_tracked_paths() -> tuple[str, ...]:
    """Return tracked repository paths using Git's own index view."""
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return tuple(path for path in result.stdout.splitlines() if path)


def git_lfs_block_lines() -> tuple[str, ...]:
    """Return the checked-in Git LFS attribute lines."""
    lines = (REPO_ROOT / ".gitattributes").read_text(encoding="utf-8").splitlines()
    begin_index = lines.index(GIT_LFS_MARKER_BEGIN)
    end_index = lines.index(GIT_LFS_MARKER_END)
    return tuple(lines[begin_index + 1 : end_index])


@pytest.mark.parametrize("path", LF_PINNED_TEXT_PATHS)
def test_template_text_paths_are_pinned_to_lf(path: str) -> None:
    """Template-managed text formats must use LF across platforms."""
    attributes = git_check_attributes((path,))

    assert attributes[path]["text"] == "set"
    assert attributes[path]["eol"] == "lf"


@pytest.mark.parametrize("path", NESTED_LICENSE_PATHS)
def test_license_pin_is_root_anchored(path: str) -> None:
    """The root LICENSE pin must not pin nested license files."""
    attributes = git_check_attributes((path,))

    assert attributes[path]["eol"] != "lf"


@pytest.mark.parametrize("path", BINARY_OVERRIDE_PATHS)
def test_binary_overrides_disable_text_conversion(path: str) -> None:
    """Binary overrides must win over broad text and fixture pins."""
    attributes = git_check_attributes((path,))

    assert attributes[path]["text"] == "unset"
    assert attributes[path]["diff"] == "unset"
    assert attributes[path]["filter"] == "unspecified"


@pytest.mark.parametrize("path", BINARY_OVERRIDE_PATHS)
def test_binary_overrides_disable_text_merges(path: str) -> None:
    """Ordinary binary overrides must unset Git text merge handling."""
    attributes = git_check_attributes((path,))

    assert attributes[path]["merge"] == "unset"


@pytest.mark.upstream_template_only
def test_git_lfs_block_uses_curated_patterns() -> None:
    """The opt-in LFS block must stay limited to the curated opaque formats."""
    assert git_lfs_block_lines() == GIT_LFS_ATTRIBUTE_LINES


@pytest.mark.upstream_template_only
@pytest.mark.parametrize("line", GIT_LFS_ATTRIBUTE_LINES)
def test_git_lfs_patterns_do_not_use_binary_macro(line: str) -> None:
    """LFS-managed patterns must not also use Git's ordinary binary macro."""
    assert not line.endswith(" binary")


@pytest.mark.upstream_template_only
@pytest.mark.parametrize("path", GIT_LFS_MANAGED_PATHS)
def test_git_lfs_patterns_set_lfs_attributes(path: str) -> None:
    """Opt-in LFS patterns must set filter, diff, merge, and text explicitly."""
    attributes = git_check_attributes((path,), LFS_ATTRIBUTES_TO_CHECK)

    assert attributes[path]["filter"] == "lfs"
    assert attributes[path]["diff"] == "lfs"
    assert attributes[path]["merge"] == "lfs"
    assert attributes[path]["text"] == "unset"


def test_git_lfs_patterns_do_not_match_tracked_template_paths() -> None:
    """The all-modules template tree must not assign LFS filters to tracked files."""
    tracked_paths = git_tracked_paths()
    attributes_by_path = git_check_attributes(tracked_paths, ("filter",))
    paths_with_lfs_filter = sorted(
        path for path, attributes in attributes_by_path.items() if attributes["filter"] == "lfs"
    )

    assert not paths_with_lfs_filter
