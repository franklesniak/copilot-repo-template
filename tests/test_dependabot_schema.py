"""Validate documented Dependabot optional configuration snippets."""

from __future__ import annotations

import shutil
import subprocess
import sys
from importlib.util import find_spec
from pathlib import Path

import pytest


def check_jsonschema_command() -> list[str] | None:
    """Resolve the preferred ``check-jsonschema`` invocation for this environment."""
    executable = shutil.which("check-jsonschema")
    if executable is not None:
        return [executable]
    if find_spec("check_jsonschema") is not None:
        return [sys.executable, "-m", "check_jsonschema"]
    return None


CHECK_JSONSCHEMA_COMMAND = check_jsonschema_command()
REPO_ROOT = Path(__file__).resolve().parent.parent
DEPENDABOT_AUTO_ASSIGNMENT_FIXTURE = (
    REPO_ROOT / "tests" / "fixtures" / "dependabot" / "auto-assignment.yml"
)


@pytest.mark.skipif(
    CHECK_JSONSCHEMA_COMMAND is None,
    reason="check-jsonschema is not installed in this environment",
)
def test_dependabot_vendor_schema_accepts_documented_auto_assignment_fields() -> None:
    """The default Dependabot hook must accept documented auto-assignment guidance."""
    validator_command = CHECK_JSONSCHEMA_COMMAND
    assert validator_command is not None

    result = subprocess.run(
        [
            *validator_command,
            "--builtin-schema",
            "vendor.dependabot",
            str(DEPENDABOT_AUTO_ASSIGNMENT_FIXTURE),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, (
        "Documented Dependabot auto-assignment fixture was rejected by "
        "vendor.dependabot.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
