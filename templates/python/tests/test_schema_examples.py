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
        start: A path inside the downstream project (typically this
            test file's location).

    Returns:
        The first ancestor directory containing ``pyproject.toml``,
        ``setup.cfg``, or ``pytest.ini``. Falls back to ``start``'s
        parent directory when no marker is found, which keeps the
        starter usable in unusual layouts without raising at import
        time.
    """
    for candidate in (start, *start.parents):
        if any((candidate / marker).is_file() for marker in _ROOT_MARKERS):
            return candidate
    return start.parent


PROJECT_ROOT = _find_project_root(Path(__file__).resolve())
SCHEMAS_DIR = PROJECT_ROOT / "schemas"
EXAMPLES_DIR = SCHEMAS_DIR / "examples"


def _discover_cases() -> list[tuple[Path, Path, bool]]:
    """Discover ``(schema, example, expected_to_pass)`` triples.

    Returns:
        A list of ``(schema_path, example_path, expected_to_pass)``
        tuples for every regular file under
        ``schemas/examples/<name>/valid/`` (expected to pass) and
        ``schemas/examples/<name>/invalid/`` (expected to fail).
        Returns an empty list when no schemas or examples are present
        so the test suite degrades gracefully rather than hard-failing
        on a count assertion.
    """
    cases: list[tuple[Path, Path, bool]] = []
    if not SCHEMAS_DIR.is_dir():
        return cases
    for schema_path in sorted(SCHEMAS_DIR.glob(f"*{SCHEMA_SUFFIX}")):
        schema_name = schema_path.name[: -len(SCHEMA_SUFFIX)]
        schema_examples_dir = EXAMPLES_DIR / schema_name
        for kind, expected_to_pass in (("valid", True), ("invalid", False)):
            kind_dir = schema_examples_dir / kind
            if not kind_dir.is_dir():
                continue
            for example_path in sorted(kind_dir.rglob("*")):
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
