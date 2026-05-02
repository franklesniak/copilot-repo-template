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

Paths are resolved from the repository root (pytest's ``rootpath``)
rather than the process current working directory, so the test behaves
the same regardless of where ``pytest`` is invoked from.

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


def _discover_cases() -> list[tuple[Path, Path, bool]]:
    """Discover ``(schema, example, expected_to_pass)`` triples.

    Returns:
        A list of ``(schema_path, example_path, expected_to_pass)``
        tuples covering every regular file under
        ``schemas/examples/<schema-name>/valid/`` (expected to pass)
        and ``schemas/examples/<schema-name>/invalid/`` (expected to
        fail). Returns an empty list if no schemas or examples are
        present, so the test suite degrades gracefully rather than
        hard-failing on a count assertion.
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
