r"""Validate schema example files with ``check-jsonschema``.

This is the **active, canonical** schema-example test for this
repository. It auto-discovers schema/example pairs under ``schemas/``
and verifies that:

- Every file under ``schemas/examples/<schema-name>/valid/`` validates
  successfully against ``schemas/<schema-name>.schema.json``
  (``check-jsonschema`` exits ``0``).
- Every file under ``schemas/examples/<schema-name>/invalid/`` is
  rejected (``check-jsonschema`` exits non-zero).

Each example runs in two regex dialects. JSON Schema reads ``pattern``
in the ECMA-262 dialect, which ``check-jsonschema`` uses by default.
python-jsonschema, which the repository's scripts use, reads it in
Python's ``re`` dialect, which ``--regex-variant python`` selects. In
Python's dialect ``$`` also matches before a final line break, so a
whole-value pattern ends with ``$(?![\s\S])``. The
``invalid/trailing-newline-*`` examples hold one value that ends in a
line break. A second test removes that end guard from a copy of the
schema and checks that Python's dialect then accepts each of these
examples, which proves that the examples detect a missing guard.

Discovery rules:

- Schemas are found via the glob ``schemas/*.schema.json``.
- For each schema, the example directory name is derived by removing
  the trailing ``.schema.json`` from the file name. For example,
  ``schemas/example-config.schema.json`` maps to
  ``schemas/examples/example-config/``.
- Only regular files under ``valid/`` and ``invalid/`` are exercised;
  directories and other non-file entries are ignored.

Paths are resolved from the repository root, which is derived from
this file's known location at ``<repo>/tests/test_schema_examples.py``
(via ``Path(__file__).resolve().parent.parent``) rather than the
process current working directory, so the test behaves the same
regardless of where ``pytest`` is invoked from.

Invalid examples are intentionally NOT wired into a normal
``check-jsonschema`` pre-commit hook, because a failing exit code from
the validator would be reported as a hook failure. This test exists in
part to prove that the schema actually rejects them.

A starter version of this test is available at
``templates/python/tests/test_schema_examples.py`` for downstream
consumers of the template; the two files share the same essential
validation pattern.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from importlib.util import find_spec
from pathlib import Path

from tests._pytest_compat import pytest


def _check_jsonschema_command() -> list[str] | None:
    """Resolve the preferred ``check-jsonschema`` invocation for this environment."""
    executable = shutil.which("check-jsonschema")
    if executable is not None:
        return [executable]
    if find_spec("check_jsonschema") is not None:
        return [sys.executable, "-m", "check_jsonschema"]
    return None


CHECK_JSONSCHEMA_COMMAND = _check_jsonschema_command()

# Repository root, relative to this file: ``<repo>/tests/test_schema_examples.py``.
REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = REPO_ROOT / "schemas"
EXAMPLES_DIR = SCHEMAS_DIR / "examples"
SCHEMA_SUFFIX = ".schema.json"
# ``default`` is ECMA-262 (the JSON Schema dialect); ``python`` is Python's ``re`` dialect.
REGEX_VARIANTS = ("default", "python")
END_GUARD = r"(?![\s\S])"
FINAL_LINE_BREAK_PREFIX = "trailing-newline-"


def _is_within_root(candidate: Path, root: Path) -> bool:
    """Return ``True`` iff ``candidate`` is reachable from ``root`` with no symlink ancestors.

    Walks upward from ``candidate`` to ``root`` (inclusive), checking
    ``Path.is_symlink()`` at each step. Any symlink found on that path
    causes a refusal, which closes the symlink-rooted-discovery
    escape: a malicious symlink at, for example,
    ``schemas/examples/<schema-name>``, ``schemas/examples/``,
    ``schemas/``, or even ``schemas/<schema-name>.schema.json`` itself
    would otherwise survive a downstream ``os.walk(followlinks=False)``
    or a yielded-path-only ``Path.resolve().relative_to(base)`` check,
    because those checks examine paths *under* ``candidate`` rather
    than the symlink chain *to* ``candidate``.

    Also returns ``False`` if ``candidate.resolve()`` does not stay
    inside ``root.resolve()``, or if any ``OSError`` / ``ValueError``
    is raised while resolving (callers should treat such errors as a
    hard refusal rather than a recoverable condition, which is why
    they are caught here and surfaced as a boolean).

    This helper does **not** enforce a mount-point or device boundary
    (``Path.is_symlink()`` does not detect bind mounts). Callers that
    require that level of isolation should layer an explicit
    ``os.stat().st_dev`` (or mount-table) check on top of this helper.

    Args:
        candidate: Path that the caller wants to use as a discovery
            root or as a discovered fixture. May be a file or a
            directory; need not exist (``is_symlink`` is well-defined
            on dangling symlinks).
        root: Trusted ancestor that ``candidate`` must live inside.
            Typically a constant such as ``REPO_ROOT`` or
            ``SCHEMAS_DIR`` derived from ``Path(__file__)`` and
            therefore not user-controlled.

    Returns:
        ``True`` only when ``candidate`` resolves under ``root`` *and*
        every path component from ``candidate`` up to and including
        ``root`` is a regular (non-symlink) entry; ``False`` otherwise.
    """
    try:
        candidate.resolve().relative_to(root.resolve())
        cur = candidate
        while True:
            if cur.is_symlink():
                return False
            if cur == root:
                return True
            parent = cur.parent
            if parent == cur:
                return False
            cur = parent
    except (OSError, ValueError):
        return False


def _iter_safe_files(directory: Path, root: Path) -> list[Path]:
    """List regular files under ``directory``, refusing symlink escapes.

    Caller's contract: ``directory`` must be intended to live inside
    ``root``. This helper enforces that contract before walking by
    calling :func:`_is_within_root`, which rejects discovery if
    ``directory`` (or any ancestor up to ``root``) is itself a
    symlink, or if ``directory.resolve()`` escapes ``root.resolve()``.
    Without this pre-walk check, an attacker who controls a path
    component (e.g., a symlink at ``schemas/examples/<schema-name>``
    pointing outside the repository) could coerce the test suite into
    walking and validating files outside ``root`` even though
    ``os.walk(followlinks=False)`` and the per-yielded-path
    boundary check would each, in isolation, appear to "succeed".

    Once the discovery root is accepted, walks ``directory`` with
    ``os.walk(followlinks=False)`` so that symlinked subdirectories
    are never traversed, drops any yielded entry that is itself a
    symlink, and re-checks each remaining path with
    ``Path.resolve()`` and ``Path.relative_to`` to guarantee its
    fully-resolved path string still lives inside ``directory``'s
    resolved location, which catches symlink and ``..``-style
    traversals that survive the initial walk-time skip.

    The repository constitution requires that file-discovery callers
    "reject path traversal and symlink escapes"; this helper
    centralizes that policy for example-fixture discovery so the test
    suite cannot be coerced into validating files outside the
    schemas/examples tree by a malicious or accidentally-introduced
    symlink at any level.

    This helper does **not** enforce a mount-point or device boundary.
    A bind mount (or any other mount) located *under* ``directory``
    will still expose its target content because ``Path.resolve()``
    returns a path that, from the filesystem's perspective, remains
    inside ``directory``. Callers that require mount-boundary
    isolation should layer an explicit ``os.stat().st_dev`` (or
    mount-table) check on top of this helper.

    Args:
        directory: Directory whose regular-file descendants should be
            returned. May not exist; if absent, an empty list is
            returned.
        root: Trusted ancestor of ``directory`` (typically
            ``REPO_ROOT``). Discovery is refused if ``directory`` or
            any ancestor up to ``root`` is a symlink, or if
            ``directory`` resolves outside ``root``.

    Returns:
        A list of regular-file ``Path`` objects below ``directory``,
        in the order produced by ``os.walk`` (callers that need a
        deterministic order should sort the result). Returns ``[]``
        when ``directory`` is missing, fails the symlink-ancestor /
        containment check against ``root``, or contains no eligible
        regular files.
    """
    if not directory.is_dir():
        return []
    if not _is_within_root(directory, root):
        return []
    base = directory.resolve()
    discovered: list[Path] = []
    for current_root, _dir_names, file_names in os.walk(directory, followlinks=False):
        for file_name in file_names:
            file_path = Path(current_root) / file_name
            if file_path.is_symlink():
                continue
            try:
                file_path.resolve().relative_to(base)
            except (OSError, ValueError):
                continue
            discovered.append(file_path)
    return discovered


def _discover_cases() -> list[tuple[Path, Path, bool]]:
    """Discover ``(schema, example, expected_to_pass)`` triples.

    Returns:
        A list of ``(schema_path, example_path, expected_to_pass)``
        tuples covering every regular file under
        ``schemas/examples/<schema-name>/valid/`` (expected to pass)
        and ``schemas/examples/<schema-name>/invalid/`` (expected to
        fail). Schema files and example directories whose path chain
        from ``REPO_ROOT`` includes a symlink (or that resolve outside
        ``REPO_ROOT``) are rejected via :func:`_is_within_root` so a
        malicious or accidentally-introduced symlink at any level
        cannot coerce the suite into validating files outside the
        repository. Returns an empty list if no schemas or examples
        are present, so the test suite degrades gracefully rather
        than hard-failing on a count assertion.
    """
    cases: list[tuple[Path, Path, bool]] = []
    if not SCHEMAS_DIR.is_dir():
        return cases
    for schema_path in sorted(SCHEMAS_DIR.glob(f"*{SCHEMA_SUFFIX}")):
        if not _is_within_root(schema_path, REPO_ROOT):
            continue
        schema_name = schema_path.name[: -len(SCHEMA_SUFFIX)]
        schema_examples_dir = EXAMPLES_DIR / schema_name
        for kind, expected_to_pass in (("valid", True), ("invalid", False)):
            kind_dir = schema_examples_dir / kind
            if not kind_dir.is_dir():
                continue
            for example_path in sorted(_iter_safe_files(kind_dir, REPO_ROOT)):
                if not example_path.is_file():
                    continue
                cases.append((schema_path, example_path, expected_to_pass))
    return cases


def _case_id(case: tuple[Path, Path, bool]) -> str:
    """Build a readable parametrize ID for a discovered case.

    The ID identifies both the schema and the example path relative to
    the repository root, plus the expected outcome, so failing cases
    are easy to locate from pytest output.
    """
    schema_path, example_path, expected_to_pass = case
    schema_rel = schema_path.relative_to(REPO_ROOT).as_posix()
    example_rel = example_path.relative_to(REPO_ROOT).as_posix()
    outcome = "valid" if expected_to_pass else "invalid"
    return f"{schema_rel}::{outcome}::{example_rel}"


_CASES = _discover_cases()


@pytest.mark.skipif(
    CHECK_JSONSCHEMA_COMMAND is None,
    reason="check-jsonschema is not installed in this environment",
)
@pytest.mark.skipif(
    not _CASES,
    reason="No schema example files found under schemas/examples/",
)
@pytest.mark.parametrize(
    ("schema_path", "example_path", "expected_to_pass"),
    _CASES,
    ids=[_case_id(c) for c in _CASES],
)
@pytest.mark.parametrize("regex_variant", REGEX_VARIANTS)
def test_schema_example(
    schema_path: Path,
    example_path: Path,
    expected_to_pass: bool,
    regex_variant: str,
) -> None:
    """Validate one ``(schema, example)`` pair against its labeled outcome.

    Args:
        schema_path: Absolute path to a ``*.schema.json`` file under
            ``schemas/``.
        example_path: Absolute path to an example file under either
            ``schemas/examples/<schema-name>/valid/`` or
            ``schemas/examples/<schema-name>/invalid/``.
        expected_to_pass: ``True`` when the example lives under
            ``valid/`` (must validate cleanly), ``False`` when it
            lives under ``invalid/`` (must be rejected).
        regex_variant: The ``check-jsonschema`` ``--regex-variant``
            value: ``default`` for ECMA-262 or ``python`` for Python's
            ``re`` dialect. Both dialects must give the labeled outcome.

    Raises:
        AssertionError: If a valid example is rejected, or an invalid
            example is accepted, by ``check-jsonschema`` in either
            regex dialect.
    """
    validator_command = CHECK_JSONSCHEMA_COMMAND
    # The command is non-None here because of the skipif guard above;
    # assert for type-checkers and as a defensive runtime check.
    assert validator_command is not None

    result = subprocess.run(
        [
            *validator_command,
            "--regex-variant",
            regex_variant,
            "--schemafile",
            str(schema_path),
            str(example_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    if expected_to_pass:
        assert result.returncode == 0, (
            f"Valid example {example_path} was unexpectedly rejected by "
            f"{schema_path} in the {regex_variant} regex dialect."
            f"\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    else:
        assert result.returncode != 0, (
            f"Invalid example {example_path} was unexpectedly accepted by "
            f"{schema_path} in the {regex_variant} regex dialect; the schema may be "
            f"too permissive or the example is no longer invalid."
            f"\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


def _without_end_guard(node: object) -> object:
    r"""Return a copy of a schema node with each ``$(?![\s\S])`` cut back to ``$``.

    Args:
        node: A parsed JSON Schema value.

    Returns:
        A copy of ``node`` in which every ``pattern`` value and every
        ``patternProperties`` key that ends with ``$(?![\s\S])`` ends
        with a bare ``$`` instead. Other values are unchanged.
    """

    def cut(pattern: str) -> str:
        if pattern.endswith("$" + END_GUARD):
            return pattern[: -len(END_GUARD)]
        return pattern

    if isinstance(node, dict):
        copied: dict[str, object] = {}
        for key, value in node.items():
            if key == "pattern" and isinstance(value, str):
                copied[key] = cut(value)
            elif key == "patternProperties" and isinstance(value, dict):
                copied[key] = {cut(name): _without_end_guard(sub) for name, sub in value.items()}
            else:
                copied[key] = _without_end_guard(value)
        return copied
    if isinstance(node, list):
        return [_without_end_guard(item) for item in node]
    return node


def _discover_final_line_break_cases() -> list[tuple[Path, tuple[Path, ...]]]:
    """Group the ``invalid/trailing-newline-*`` examples by schema.

    Returns:
        A list of ``(schema_path, example_paths)`` tuples, one for each
        schema that has at least one invalid example whose file name
        starts with ``trailing-newline-``. Discovery reuses
        :func:`_discover_cases`, so the same symlink and containment
        checks apply.
    """
    grouped: dict[Path, list[Path]] = {}
    for schema_path, example_path, expected_to_pass in _CASES:
        if not expected_to_pass and example_path.name.startswith(FINAL_LINE_BREAK_PREFIX):
            grouped.setdefault(schema_path, []).append(example_path)
    return [(schema, tuple(examples)) for schema, examples in sorted(grouped.items())]


def _rejected_examples(
    schema_path: Path, example_paths: tuple[Path, ...], regex_variant: str
) -> set[Path]:
    """Return the examples that ``check-jsonschema`` rejects in one regex dialect.

    Args:
        schema_path: The schema file to validate against.
        example_paths: The instance files to validate in one run.
        regex_variant: The ``--regex-variant`` value.

    Returns:
        The subset of ``example_paths`` that have at least one
        validation error.

    Raises:
        AssertionError: If the validator output is not the expected JSON
            report, or if an example cannot be parsed.
    """
    assert CHECK_JSONSCHEMA_COMMAND is not None
    result = subprocess.run(
        [
            *CHECK_JSONSCHEMA_COMMAND,
            "--output-format",
            "JSON",
            "--regex-variant",
            regex_variant,
            "--schemafile",
            str(schema_path),
            *[str(path) for path in example_paths],
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise AssertionError(
            f"check-jsonschema did not print a JSON report.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        ) from error
    assert not report.get("parse_errors"), report
    return {Path(error["filename"]) for error in report["errors"]}


_FINAL_LINE_BREAK_CASES = _discover_final_line_break_cases()


@pytest.mark.skipif(
    CHECK_JSONSCHEMA_COMMAND is None,
    reason="check-jsonschema is not installed in this environment",
)
@pytest.mark.skipif(
    not _FINAL_LINE_BREAK_CASES,
    reason="No invalid/trailing-newline-* schema examples found under schemas/examples/",
)
@pytest.mark.parametrize(
    ("schema_path", "example_paths"),
    _FINAL_LINE_BREAK_CASES,
    ids=[schema.relative_to(REPO_ROOT).as_posix() for schema, _ in _FINAL_LINE_BREAK_CASES],
)
def test_final_line_break_examples_depend_on_end_guard(
    schema_path: Path,
    example_paths: tuple[Path, ...],
    tmp_path: Path,
) -> None:
    r"""Remove the end guard and check that only Python's dialect then accepts the examples.

    This is the failure-injection control for :func:`test_schema_example`.
    A copy of the schema has each ``$(?![\s\S])`` cut back to ``$``.
    ECMA-262 must still reject each ``trailing-newline-*`` example,
    because its ``$`` matches only at the end of the text. Python's
    dialect must accept each one, because its ``$`` also matches before a
    final line break. The examples therefore detect a missing guard.

    Args:
        schema_path: A schema with ``invalid/trailing-newline-*`` examples.
        example_paths: Those examples.
        tmp_path: Pytest's per-test temporary directory.

    Raises:
        AssertionError: If the schema has no end guard, if ECMA-262
            accepts an example without the guard, or if Python's dialect
            rejects an example without the guard.
    """
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    unguarded = _without_end_guard(schema)
    assert unguarded != schema, f"{schema_path} has no pattern that ends with $(?![\\s\\S])"
    unguarded_path = tmp_path / schema_path.name
    unguarded_path.write_text(json.dumps(unguarded, indent=2), encoding="utf-8")

    rejected_by_ecma = _rejected_examples(unguarded_path, example_paths, "default")
    rejected_by_python = _rejected_examples(unguarded_path, example_paths, "python")

    assert rejected_by_ecma == set(example_paths), (
        f"Without the end guard, ECMA-262 accepted "
        f"{sorted(str(p) for p in set(example_paths) - rejected_by_ecma)}; "
        f"these examples do not isolate a final line break."
    )
    assert not rejected_by_python, (
        f"Without the end guard, Python's dialect still rejected "
        f"{sorted(str(p) for p in rejected_by_python)}; each "
        f"trailing-newline-* example must differ from a valid document only "
        f"by a final line break in one guarded value."
    )
