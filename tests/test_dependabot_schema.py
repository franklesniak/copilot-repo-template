"""Validate documented Dependabot optional configuration snippets."""

from __future__ import annotations

import importlib.metadata
import shutil
import subprocess
import sys
from importlib.util import find_spec
from pathlib import Path

import pytest
import yaml  # type: ignore[import-untyped]


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
PRE_COMMIT_CONFIG = REPO_ROOT / ".pre-commit-config.yaml"
DEPENDABOT_AUTO_ASSIGNMENT_FIXTURE = (
    REPO_ROOT / "tests" / "fixtures" / "dependabot" / "auto-assignment.yml"
)


def pinned_check_jsonschema_rev() -> str:
    """Return the ``check-jsonschema`` rev pinned in ``.pre-commit-config.yaml``."""
    config = yaml.safe_load(PRE_COMMIT_CONFIG.read_text(encoding="utf-8"))
    revs = {
        str(repo["rev"]).strip().lstrip("v")
        for repo in config.get("repos", [])
        if str(repo.get("repo", "")).rstrip("/").endswith("/check-jsonschema") and "rev" in repo
    }
    assert revs, "No pinned check-jsonschema repo found in .pre-commit-config.yaml"
    assert len(revs) == 1, (
        "check-jsonschema is pinned to multiple revs in .pre-commit-config.yaml: " f"{sorted(revs)}"
    )
    return next(iter(revs))


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


@pytest.mark.skipif(
    find_spec("check_jsonschema") is None,
    reason="check-jsonschema is not installed in this environment",
)
def test_regression_check_jsonschema_matches_pinned_pre_commit_rev() -> None:
    """Pytest's ``check-jsonschema`` must match the pinned pre-commit hook rev so it validates against the same bundled ``vendor.dependabot`` schema."""
    installed = importlib.metadata.version("check-jsonschema")
    pinned = pinned_check_jsonschema_rev()

    assert installed == pinned, (
        f"Installed check-jsonschema {installed!r} does not match the pinned "
        f".pre-commit-config.yaml rev {pinned!r}. The Dependabot regression test "
        "would validate against a different bundled vendor.dependabot schema than "
        "the default validate-dependabot-config hook. Bump the check-jsonschema "
        "pin in pyproject.toml and the pre-commit `rev` together."
    )
