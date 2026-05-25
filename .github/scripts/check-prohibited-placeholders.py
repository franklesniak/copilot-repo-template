"""Check Markdown docs for prohibited placeholder markers.

The pre-commit hook calls this script with candidate Markdown paths. The
checker intentionally stays dependency-free so it can run in the repo-local
hook environment on Windows, macOS, Linux, and WSL.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PLACEHOLDER_PATTERN = re.compile(
    r"\(default[^)]*to\s+be\s+determined[^)]*\)"
    r"|\bTODO\b\s*:"
    r"|\bTBD\b"
    r"|\bFIXME\b"
    r"|\bXXX\b"
    r"|\bto\s+be\s+determined\b",
    re.IGNORECASE,
)
ALLOW_TBD_PATTERN = re.compile(r"<!--\s*ALLOW-TBD:\s*\S.*?-->", re.IGNORECASE)
ALLOWED_LABEL_PATTERN = re.compile(
    r"^\s*(?:(?:[-*+]|\d+\.)\s+)?\*\*(?:Open Questions?|Assumption):\*\*",
    re.IGNORECASE,
)
FENCE_OPEN_PATTERN = re.compile(r"^ {0,3}(?P<marker>`{3,}|~{3,})")
BLOCK_QUOTE_PREFIX_PATTERN = re.compile(r"^ {0,3}> ?")
LIST_ITEM_PATTERN = re.compile(r"^(?P<indent> {0,3})(?P<marker>[-*+]|\d{1,9}[.)])(?P<spacing> +)")

REMEDIATION_HINT = (
    "replace with a measurable value, an **Open Question:** entry, an "
    "**Assumption:** entry, or a cross-reference to another requirement. "
    "To suppress with explicit justification, add <!-- ALLOW-TBD: <reason> --> "
    'on the same line. See .github/instructions/docs.instructions.md "Prohibited Patterns".'
)


@dataclass(frozen=True)
class Violation:
    """A prohibited placeholder match in a Markdown file."""

    display_path: str
    line_number: int
    matched_text: str

    def format_message(self) -> str:
        """Return the hook failure message for this placeholder match."""
        return (
            f"{self.display_path}:{self.line_number}: prohibited placeholder "
            f"{json.dumps(self.matched_text)}; {REMEDIATION_HINT}"
        )


@dataclass(frozen=True)
class FenceLine:
    """A Markdown line normalized for fenced code block detection."""

    content: str
    list_indent: int | None
    block_quote_depth: int
    inner_block_quote_depth: int = 0


@dataclass(frozen=True)
class ActiveFence:
    """The active fenced code block marker and containing Markdown context."""

    character: str
    minimum_length: int
    list_indent: int | None
    block_quote_depth: int
    inner_block_quote_depth: int = 0


@dataclass(frozen=True)
class ListContext:
    """An active Markdown list context with its containing block-quote depth."""

    content_indent: int
    block_quote_depth: int


class FileReadError(RuntimeError):
    """Raised when a candidate Markdown file cannot be read."""

    def __init__(self, display_path: str, error: OSError) -> None:
        error_summary = f"{type(error).__name__}: {error.strerror or 'I/O error'}"
        super().__init__(f"{display_path}: unable to read file ({error_summary})")


def is_changelog_file(path: Path) -> bool:
    """Return whether the file name matches the hook's changelog exemption."""
    name = path.name.lower()
    return name.startswith("changelog") and name.endswith(".md")


def is_scan_target(relative_path: Path) -> bool:
    """Return whether a repo-relative path is a docs Markdown scan target."""
    return (
        len(relative_path.parts) >= 2
        and relative_path.parts[0] == "docs"
        and relative_path.suffix.lower() == ".md"
        and not is_changelog_file(relative_path)
    )


def resolve_candidate_path(path_argument: str | Path, root: Path) -> tuple[Path, str] | None:
    """Resolve a pre-commit path argument to a contained scan target."""
    root = root.resolve()
    path = Path(path_argument)
    candidate = path if path.is_absolute() else root / path

    if candidate.is_symlink() or not candidate.is_file():
        return None

    resolved_candidate = candidate.resolve()
    try:
        relative_path = resolved_candidate.relative_to(root)
    except ValueError:
        return None

    if not is_scan_target(relative_path):
        return None

    return resolved_candidate, relative_path.as_posix()


def strip_html_comments(line: str, is_in_html_comment: bool) -> tuple[str, bool]:
    """Remove HTML comment spans from a Markdown line."""
    uncommented_parts: list[str] = []
    index = 0

    while index < len(line):
        if is_in_html_comment:
            comment_end = line.find("-->", index)
            if comment_end == -1:
                return "".join(uncommented_parts), True
            index = comment_end + len("-->")
            is_in_html_comment = False
            continue

        comment_start = line.find("<!--", index)
        if comment_start == -1:
            uncommented_parts.append(line[index:])
            break

        uncommented_parts.append(line[index:comment_start])
        comment_end = line.find("-->", comment_start + len("<!--"))
        if comment_end == -1:
            is_in_html_comment = True
            break
        index = comment_end + len("-->")

    return "".join(uncommented_parts), is_in_html_comment


def strip_block_quote_prefixes(line: str) -> tuple[str, int]:
    """Return a Markdown line with leading block quote container markers removed."""
    block_quote_depth = 0
    while True:
        match = BLOCK_QUOTE_PREFIX_PATTERN.match(line)
        if match is None:
            return line, block_quote_depth
        line = line[match.end() :]
        block_quote_depth += 1


def count_leading_spaces(line: str) -> int:
    """Return the number of leading space characters in a line."""
    return len(line) - len(line.lstrip(" "))


def prune_inactive_list_contexts(line: str, list_contexts: list[ListContext]) -> None:
    """Drop active list contexts that a nonblank Markdown line has outdented past."""
    if not line.strip():
        return

    while list_contexts:
        top = list_contexts[-1]
        stripped = line
        sufficient_block_quote_depth = True
        for _quote_level in range(top.block_quote_depth):
            match = BLOCK_QUOTE_PREFIX_PATTERN.match(stripped)
            if match is None:
                sufficient_block_quote_depth = False
                break
            stripped = stripped[match.end() :]

        if not sufficient_block_quote_depth:
            list_contexts.pop()
            continue

        # A line with more block-quote prefixes than the list's recorded depth is
        # inside a blockquote nested in the list. Preserve the list — its
        # content_indent is not meaningful in this deeper coordinate system.
        if BLOCK_QUOTE_PREFIX_PATTERN.match(stripped) is not None:
            return

        if not stripped.strip():
            return

        if count_leading_spaces(stripped) >= top.content_indent:
            return

        list_contexts.pop()


def list_content_indent(match: re.Match[str], parent_indent: int) -> int:
    """Return the content indent column for a Markdown list-item marker."""
    marker_end_column = parent_indent + match.end("marker")
    spacing_width = len(match.group("spacing"))
    content_padding = spacing_width if spacing_width <= 4 else 1
    return marker_end_column + content_padding


def strip_active_list_prefix(line: str, list_contexts: list[ListContext]) -> tuple[str, int]:
    """Return a line relative to the innermost active list context."""
    if not list_contexts:
        return line, 0

    parent_indent = list_contexts[-1].content_indent
    if count_leading_spaces(line) < parent_indent:
        return line, 0

    return line[parent_indent:], parent_indent


def normalize_for_fence_opening(line: str, list_contexts: list[ListContext]) -> FenceLine:
    """Return a line normalized to its current Markdown container content column."""
    prune_inactive_list_contexts(line, list_contexts)
    line, block_quote_depth = strip_block_quote_prefixes(line)

    relative_line, parent_indent = strip_active_list_prefix(line, list_contexts)
    list_match = LIST_ITEM_PATTERN.match(relative_line)
    if list_match is None:
        # A blockquote nested inside the list item lives at the list-content
        # column, so its ">" is past the 0-3 column rule that
        # BLOCK_QUOTE_PREFIX_PATTERN enforces on the raw line.
        #
        # LIST_ITEM_PATTERN is intentionally not re-run after this inner strip:
        # tracking a list item that lives inside a blockquote that lives inside
        # another list item would require a multi-level container path on
        # ListContext (essentially the CommonMark container-stack model).
        # That deeper pattern is unsupported here; fence detection inside such
        # a triply-nested context may produce false positives until the hook
        # is rewritten around an ordered container stack.
        relative_line, inner_block_quote_depth = strip_block_quote_prefixes(relative_line)
        list_indent = parent_indent if parent_indent != 0 else None
        return FenceLine(
            content=relative_line,
            list_indent=list_indent,
            block_quote_depth=block_quote_depth,
            inner_block_quote_depth=inner_block_quote_depth,
        )

    content_indent = list_content_indent(list_match, parent_indent)
    list_contexts.append(
        ListContext(content_indent=content_indent, block_quote_depth=block_quote_depth)
    )
    return FenceLine(
        content=line[content_indent:] if len(line) >= content_indent else "",
        list_indent=content_indent,
        block_quote_depth=block_quote_depth,
    )


def normalize_for_fence_closing(line: str, active_fence: ActiveFence) -> str:
    """Return a fenced-block line normalized to the opening fence's container."""
    normalized_line = line
    for _quote_level in range(active_fence.block_quote_depth):
        match = BLOCK_QUOTE_PREFIX_PATTERN.match(normalized_line)
        if match is None:
            return line
        normalized_line = normalized_line[match.end() :]

    if active_fence.list_indent is not None:
        if count_leading_spaces(normalized_line) < active_fence.list_indent:
            return line
        normalized_line = normalized_line[active_fence.list_indent :]

    for _quote_level in range(active_fence.inner_block_quote_depth):
        match = BLOCK_QUOTE_PREFIX_PATTERN.match(normalized_line)
        if match is None:
            return line
        normalized_line = normalized_line[match.end() :]

    return normalized_line


def build_active_fence(
    opening_fence: tuple[str, int],
    fence_line: FenceLine,
) -> ActiveFence:
    """Return active fenced code block state for a detected opening fence."""
    fence_character, minimum_length = opening_fence
    return ActiveFence(
        character=fence_character,
        minimum_length=minimum_length,
        list_indent=fence_line.list_indent,
        block_quote_depth=fence_line.block_quote_depth,
        inner_block_quote_depth=fence_line.inner_block_quote_depth,
    )


def parse_opening_fence(line: str) -> tuple[str, int] | None:
    """Return the opening fence marker character and length, if present."""
    match = FENCE_OPEN_PATTERN.match(line)
    if match is None:
        return None

    marker = match.group("marker")
    return marker[0], len(marker)


def is_closing_fence(line: str, fence_character: str, minimum_length: int) -> bool:
    """Return whether a line closes the active fenced code block."""
    closing_pattern = re.compile(rf"^ {{0,3}}{re.escape(fence_character)}{{{minimum_length},}}\s*$")
    return closing_pattern.match(line) is not None


def is_allowed_label_line(line: str) -> bool:
    """Return whether the line is an explicit Open Question or Assumption entry."""
    return ALLOWED_LABEL_PATTERN.match(line) is not None


def find_violations_in_text(text: str, display_path: str) -> list[Violation]:
    """Find prohibited placeholder markers in Markdown text."""
    violations: list[Violation] = []
    is_in_html_comment = False
    active_fence: ActiveFence | None = None
    list_contexts: list[ListContext] = []

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        if active_fence is not None:
            fence_line = normalize_for_fence_closing(raw_line, active_fence)
            if is_closing_fence(
                fence_line,
                active_fence.character,
                active_fence.minimum_length,
            ):
                active_fence = None
            continue

        commentless_line, is_in_html_comment = strip_html_comments(raw_line, is_in_html_comment)

        fence_line = normalize_for_fence_opening(commentless_line, list_contexts)
        opening_fence = parse_opening_fence(fence_line.content)
        if opening_fence is not None:
            active_fence = build_active_fence(opening_fence, fence_line)
            continue

        if ALLOW_TBD_PATTERN.search(raw_line):
            continue

        if is_allowed_label_line(commentless_line):
            continue

        for match in PLACEHOLDER_PATTERN.finditer(commentless_line):
            violations.append(
                Violation(
                    display_path=display_path,
                    line_number=line_number,
                    matched_text=match.group(0),
                )
            )

    return violations


def scan_files(path_arguments: Iterable[str | Path], root: Path = REPO_ROOT) -> list[Violation]:
    """Find prohibited placeholder markers in candidate Markdown docs."""
    violations: list[Violation] = []
    for path_argument in path_arguments:
        candidate = resolve_candidate_path(path_argument, root)
        if candidate is None:
            continue

        path, display_path = candidate
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as error:
            raise FileReadError(display_path, error) from error

        violations.extend(find_violations_in_text(text, display_path))

    return violations


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Check docs Markdown for prohibited placeholder markers."
    )
    parser.add_argument("paths", nargs="*", help="Markdown files passed by pre-commit.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None, root: Path = REPO_ROOT) -> int:
    """Run the placeholder check."""
    args = parse_args(argv)

    try:
        violations = scan_files(args.paths, root=root)
    except FileReadError as error:
        print(error, file=sys.stderr)
        return 1

    for violation in violations:
        print(violation.format_message())

    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
