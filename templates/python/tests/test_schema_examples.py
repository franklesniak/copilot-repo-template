"""Starter template: validate schema example files with ``check-jsonschema``.

This file is **starter content** that downstream Python projects copy
into their own ``tests/`` directory. The active, canonical version
that this starter is derived from lives at
``tests/test_schema_examples.py`` in the ``copilot-repo-template``
repository — see that file for the source of truth on discovery,
invocation, and assertion logic.

The starter and the active test share the same essential pattern:

- Auto-discover schemas via ``schemas/*.schema.json``.
- For each schema, derive the example directory by stripping
  ``.schema.json`` from the file name (``schemas/<name>.schema.json``
  maps to ``schemas/examples/<name>/``).
- Recursively walk ``schemas/examples/<name>/valid/`` (must validate)
  and ``schemas/examples/<name>/invalid/`` (must be rejected).
- Invoke ``check-jsonschema`` via ``subprocess.run`` with
  ``check=False``, ``capture_output=True``, ``text=True``.

Intentional differences from the active test:

- Path resolution: this starter resolves the project root by walking
  up from this file's location until it finds a ``pyproject.toml``,
  ``setup.cfg``, or ``pytest.ini`` marker. The active test in the
  template repository hardcodes its location as
  ``<repo>/tests/test_schema_examples.py``; downstream projects may
  place this file at a different depth, so root discovery is dynamic
  here. See ``.github/instructions/python.instructions.md``
  (Filesystem and Paths): paths SHOULD be resolved from a clear root
  rather than the process CWD.
- The ``check-jsonschema`` skipif guard is retained so the starter
  remains safe to copy even into projects that have not yet added
  ``check-jsonschema`` to their dev/test dependencies. Downstream
  projects SHOULD add ``check-jsonschema`` to their dev/test
  dependency group (see ``templates/python/pyproject.toml``) so the
  test always runs.

How to use:

1. Copy this file into your project's real ``tests/`` directory.
2. Add ``check-jsonschema`` to your project's dev/test dependencies
   (already declared in ``templates/python/pyproject.toml``).
3. Place schemas under ``schemas/<name>.schema.json`` and matching
   examples under ``schemas/examples/<name>/{valid,invalid}/``. No
   per-case configuration is required — discovery is automatic.

Both valid and invalid examples are exercised here:

- Valid examples MUST validate cleanly (exit code ``0``).
- Invalid examples MUST be rejected (non-zero exit code).

Invalid examples are intentionally NOT wired into a normal
``check-jsonschema`` pre-commit hook, because a failing exit code from
the validator would be reported as a hook failure. Use this test (or
an equivalent script) to prove that the schema actually rejects them.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

CHECK_JSONSCHEMA = shutil.which("check-jsonschema")

SCHEMA_SUFFIX = ".schema.json"
_ROOT_MARKERS = ("pyproject.toml", "setup.cfg", "pytest.ini")


def _find_project_root(start: Path) -> Path:
    """Walk up from ``start`` until a project-root marker is found.

    Args:
        start: A directory inside the downstream project (typically
            the directory containing this test file). Callers MUST
            pass a directory; file paths should be normalized at the
            call site (e.g., ``Path(__file__).resolve().parent``) so
            the first iteration does not check a nonexistent
            ``<file>/<marker>`` path.

    Returns:
        The first ancestor directory containing ``pyproject.toml``,
        ``setup.cfg``, or ``pytest.ini``. Falls back to ``start``
        itself when no marker is found, which keeps the starter
        usable in unusual layouts without raising at import time.
    """
    for candidate in (start, *start.parents):
        if any((candidate / marker).is_file() for marker in _ROOT_MARKERS):
            return candidate
    return start


PROJECT_ROOT = _find_project_root(Path(__file__).resolve().parent)
SCHEMAS_DIR = PROJECT_ROOT / "schemas"
EXAMPLES_DIR = SCHEMAS_DIR / "examples"


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
    (``Path.is_symlink()`` does not detect bind mounts). Downstream
    projects that require that level of isolation should layer an
    explicit ``os.stat().st_dev`` (or mount-table) check on top of
    this helper.

    Args:
        candidate: Path that the caller wants to use as a discovery
            root or as a discovered fixture. May be a file or a
            directory; need not exist (``is_symlink`` is well-defined
            on dangling symlinks).
        root: Trusted ancestor that ``candidate`` must live inside.
            Typically the downstream-derived ``PROJECT_ROOT`` or
            ``SCHEMAS_DIR``.

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
    pointing outside the project) could coerce the test suite into
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

    Downstream projects that copy this starter inherit the same
    policy: example-fixture discovery refuses any symlink-rooted
    escape (a symlink at any level from ``root`` down to the discovery
    directory), never follows symlinks during traversal, and never
    returns files outside the resolved fixture tree, so a malicious
    or accidentally-introduced symlink at any level of the
    ``schemas/`` tree cannot coerce the test into validating files
    outside the project.

    This helper does **not** enforce a mount-point or device boundary.
    A bind mount (or any other mount) located *under* ``directory``
    will still expose its target content because ``Path.resolve()``
    returns a path that, from the filesystem's perspective, remains
    inside ``directory``. Downstream projects that require mount-
    boundary isolation should layer an explicit
    ``os.stat().st_dev`` (or mount-table) check on top of this
    helper.

    Args:
        directory: Directory whose regular-file descendants should be
            returned. May not exist; if absent, an empty list is
            returned.
        root: Trusted ancestor of ``directory`` (typically
            ``PROJECT_ROOT``). Discovery is refused if ``directory``
            or any ancestor up to ``root`` is a symlink, or if
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
        tuples for every regular file under
        ``schemas/examples/<name>/valid/`` (expected to pass) and
        ``schemas/examples/<name>/invalid/`` (expected to fail).
        Schema files and example directories whose path chain from
        ``PROJECT_ROOT`` includes a symlink (or that resolve outside
        ``PROJECT_ROOT``) are rejected via :func:`_is_within_root` so
        a malicious or accidentally-introduced symlink at any level
        cannot coerce the suite into validating files outside the
        project. Returns an empty list when no schemas or examples
        are present so the test suite degrades gracefully rather
        than hard-failing on a count assertion.
    """
    cases: list[tuple[Path, Path, bool]] = []
    if not SCHEMAS_DIR.is_dir():
        return cases
    for schema_path in sorted(SCHEMAS_DIR.glob(f"*{SCHEMA_SUFFIX}")):
        if not _is_within_root(schema_path, PROJECT_ROOT):
            continue
        schema_name = schema_path.name[: -len(SCHEMA_SUFFIX)]
        schema_examples_dir = EXAMPLES_DIR / schema_name
        for kind, expected_to_pass in (("valid", True), ("invalid", False)):
            kind_dir = schema_examples_dir / kind
            if not kind_dir.is_dir():
                continue
            for example_path in sorted(_iter_safe_files(kind_dir, PROJECT_ROOT)):
                if not example_path.is_file():
                    continue
                cases.append((schema_path, example_path, expected_to_pass))
    return cases


def _case_id(case: tuple[Path, Path, bool]) -> str:
    """Build a readable parametrize ID for a discovered case."""
    schema_path, example_path, expected_to_pass = case
    try:
        schema_rel = schema_path.relative_to(PROJECT_ROOT).as_posix()
        example_rel = example_path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        schema_rel = schema_path.as_posix()
        example_rel = example_path.as_posix()
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
        expected_to_pass: ``True`` for ``valid/`` examples (must
            validate cleanly), ``False`` for ``invalid/`` examples
            (must be rejected).

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
