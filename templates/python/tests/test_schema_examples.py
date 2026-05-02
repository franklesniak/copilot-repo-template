"""Optional template: validate schema example files with check-jsonschema.

This file is a **template**. It is intentionally placed under
``templates/python/tests/`` rather than the repository root ``tests/``
directory because it depends on the ``check-jsonschema`` command being
available on ``PATH``, which is not a default dev/test dependency in this
template.

How to use:

1. Copy this file into your project's real ``tests/`` directory.
2. Either:

   - add ``check-jsonschema`` to your project's dev/test dependencies so
     the test always runs, or
   - keep the ``skipif`` guard below so the test safely no-ops when
     ``check-jsonschema`` is not installed.

3. Update ``SCHEMA_CASES`` to point at your real ``(schema, example,
   expected_to_pass)`` triples under ``schemas/examples/``.

Both valid and invalid examples are exercised here:

- Valid examples MUST validate cleanly (exit code ``0``).
- Invalid examples MUST be rejected (non-zero exit code).

Invalid examples are intentionally NOT wired into a normal
``check-jsonschema`` pre-commit hook, because a failing exit code from
the validator would be reported as a hook failure. Use this test (or an
equivalent script) to prove that the schema actually rejects them.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

CHECK_JSONSCHEMA = shutil.which("check-jsonschema")

# Each entry is (schema_path, example_path, expected_to_pass).
# Replace these placeholder paths with real schema/example pairs from
# your project's ``schemas/`` directory.
SCHEMA_CASES: list[tuple[str, str, bool]] = [
    # ("schemas/project-config.schema.json",
    #  "schemas/examples/project-config.valid.json",
    #  True),
    # ("schemas/project-config.schema.json",
    #  "schemas/examples/project-config.invalid.json",
    #  False),
]


@pytest.mark.skipif(
    CHECK_JSONSCHEMA is None,
    reason="check-jsonschema is not installed in this environment",
)
@pytest.mark.skipif(
    not SCHEMA_CASES,
    reason="No schema example cases are configured in SCHEMA_CASES",
)
@pytest.mark.parametrize(("schema", "example", "expected_to_pass"), SCHEMA_CASES)
def test_schema_example(schema: str, example: str, expected_to_pass: bool) -> None:
    """Validate one (schema, example) pair against the documented expectation."""
    schema_path = Path(schema)
    example_path = Path(example)
    assert schema_path.is_file(), f"Schema file not found: {schema_path}"
    assert example_path.is_file(), f"Example file not found: {example_path}"

    # CHECK_JSONSCHEMA is non-None here because of the skipif guard above;
    # assert for type-checkers and as a defensive runtime check.
    assert CHECK_JSONSCHEMA is not None

    result = subprocess.run(
        [
            CHECK_JSONSCHEMA,
            "--schemafile",
            str(schema_path),
            str(example_path),
        ],
        capture_output=True,
        text=True,
        check=False,
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
            f"is no longer invalid."
        )
