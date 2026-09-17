"""Protect the semantic review-governance contract from instruction drift."""

from __future__ import annotations

from pathlib import Path

from tests._pytest_compat import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
pytestmark = pytest.mark.upstream_template_only

REQUIREMENTS = {
    "AGENTS.md": (
        "reviewThreads",
        "isResolved == false",
        "review:<review-id>:<section-label>:<ordinal>",
        "Balanced",
        "Lite",
        "@codex review",
        "chatgpt-codex-connector[bot]",
        "request-time head",
        "pagination-complete",
        "not clean",
        "both co-equal sources",
        "Failed cycles do not consume",
        "Deferring Work",
        "base branch",
        "diagnostic instrumentation",
        "cookies",
    ),
    "CLAUDE.md": (
        "reviewThreads",
        "isResolved == false",
        "review:<review-id>:<section-label>:<ordinal>",
        "Balanced",
        "Lite",
        "@codex review",
        "chatgpt-codex-connector[bot]",
        "request-time PR head SHA",
        "pagination",
        "not clean",
        "Failed cycles do not consume",
        "Deferring Work",
        "base branch",
        "diagnostic instrumentation",
        "cookies",
    ),
    ".github/instructions/yaml.instructions.md": (
        "on.push.paths",
        "tag pushes",
        "pull_request_target",
        "trust root",
        "inert data",
        "MUST NOT",
        "unconditional or required companion gate",
        "tree entry mode",
        "symlinks",
        "gitlinks",
        "unexpected executable-bit",
    ),
}


def _missing(path: str, text: str) -> list[str]:
    """Return semantic contract markers absent from one instruction file."""
    return [phrase for phrase in REQUIREMENTS[path] if phrase not in text]


def test_current_review_governance_contract_is_complete() -> None:
    """The shipped protocol contains all review and trust-root markers."""
    for relative_path in REQUIREMENTS:
        path = REPO_ROOT / relative_path
        assert _missing(relative_path, path.read_text(encoding="utf-8")) == []


@pytest.mark.parametrize(
    ("relative_path", "removed_marker"),
    [
        ("AGENTS.md", "reviewThreads"),
        ("CLAUDE.md", "@codex review"),
        (".github/instructions/yaml.instructions.md", "pull_request_target"),
    ],
)
def test_missing_semantic_marker_fails(
    relative_path: str,
    removed_marker: str,
) -> None:
    """A missing high-risk protocol marker is observable as a failed contract."""
    text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
    mutated = text.replace(removed_marker, "")

    assert removed_marker in REQUIREMENTS[relative_path]
    assert removed_marker in _missing(relative_path, mutated)


@pytest.mark.parametrize(
    ("relative_path", "original", "replacement"),
    [
        ("AGENTS.md", "Failed cycles do not consume", "Failed cycles consume"),
        ("AGENTS.md", "both co-equal sources", "one co-equal source"),
        ("CLAUDE.md", "Balanced", "Standard"),
        ("CLAUDE.md", "chatgpt-codex-connector[bot]", "codex-reviewer"),
        (
            ".github/instructions/yaml.instructions.md",
            "inert data",
            "executable data",
        ),
        (
            ".github/instructions/yaml.instructions.md",
            "unconditional or required companion gate",
            "optional companion gate",
        ),
    ],
)
def test_semantic_mutation_is_rejected(
    relative_path: str,
    original: str,
    replacement: str,
) -> None:
    """Mutation testing catches weakened retry, effort, or trust-root rules."""
    text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
    mutated = text.replace(original, replacement)

    assert original in text
    assert _missing(relative_path, mutated)
