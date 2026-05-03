"""Validate schema example files with ``check-jsonschema``.

This is the **active, canonical** schema-example test for this
repository. It auto-discovers schema/example pairs under ``schemas/``
and verifies that:

- Every file under ``schemas/examples/<schema-name>/valid/`` validates
  successfully against ``schemas/<schema-name>.schema.json``
  (``check-jsonschema`` exits ``0``).
- Every file under ``schemas/examples/<schema-name>/invalid/`` is
  rejected (``check-jsonschema`` exits non-zero).

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

import os
import shutil
import subprocess
from pathlib import Path

import pytest

CHECK_JSONSCHEMA = shutil.which("check-jsonschema")

# Repository root, relative to this file: ``<repo>/tests/test_schema_examples.py``.
REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = REPO_ROOT / "schemas"
EXAMPLES_DIR = SCHEMAS_DIR / "examples"
SCHEMA_SUFFIX = ".schema.json"


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
    CHECK_JSONSCHEMA is None,
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
def test_schema_example(
    schema_path: Path,
    example_path: Path,
    expected_to_pass: bool,
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

    Raises:
        AssertionError: If a valid example is rejected, or an invalid
            example is accepted, by ``check-jsonschema``.
    """
    # CHECK_JSONSCHEMA is non-None here because of the skipif guard
    # above; assert for type-checkers and as a defensive runtime check.
    assert CHECK_JSONSCHEMA is not None

    result = subprocess.run(
        [
            CHECK_JSONSCHEMA,
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
            f"{schema_path}.\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    else:
        assert result.returncode != 0, (
            f"Invalid example {example_path} was unexpectedly accepted by "
            f"{schema_path}; the schema may be too permissive or the example "
            f"is no longer invalid.\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
