"""Tests for repo-local Terraform pre-commit hook wrappers."""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

HOOK_PATH = Path(__file__).resolve().parents[1] / ".github" / "scripts" / "terraform_hooks.py"
HOOK_SPEC = importlib.util.spec_from_file_location("terraform_hooks", HOOK_PATH)
if HOOK_SPEC is None or HOOK_SPEC.loader is None:
    raise RuntimeError(f"Unable to load Terraform hook module from {HOOK_PATH}")
terraform_hooks = importlib.util.module_from_spec(HOOK_SPEC)
HOOK_SPEC.loader.exec_module(terraform_hooks)


class CommandRecorder:
    """Record commands passed to a hook runner."""

    def __init__(self) -> None:
        self.calls: list[tuple[list[str], Path]] = []

    def __call__(self, command: list[str], cwd: Path) -> int:
        self.calls.append((command, cwd))
        return 0


def write_file(path: Path, content: str = "") -> None:
    """Create a test file and its parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_terraform_format_uses_ci_command(tmp_path: Path) -> None:
    """Terraform format mirrors the repository CI format command."""
    write_file(tmp_path / "templates" / "terraform" / "Example.tftest.hcl")
    recorder = CommandRecorder()

    result = terraform_hooks.run_terraform_format(
        root=tmp_path,
        resolve=lambda name: f"{name}-bin",
        runner=recorder,
    )

    assert result == 0
    assert recorder.calls == [
        (
            ["terraform-bin", "fmt", "-check", "-recursive", "-diff"],
            tmp_path.resolve(),
        )
    ]


def test_terraform_validate_discovers_only_tf_directories(tmp_path: Path) -> None:
    """Terraform validate ignores lone `.tftest.hcl` directories."""
    module_dir = tmp_path / "modules" / "example"
    write_file(module_dir / "main.tf", 'resource "terraform_data" "example" {}\n')
    write_file(tmp_path / "templates" / "terraform" / "Example.tftest.hcl")
    recorder = CommandRecorder()

    result = terraform_hooks.run_terraform_validate(
        root=tmp_path,
        resolve=lambda name: f"{name}-bin",
        runner=recorder,
    )

    assert result == 0
    assert recorder.calls == [
        (["terraform-bin", "init", "-backend=false"], module_dir.resolve()),
        (["terraform-bin", "validate"], module_dir.resolve()),
    ]


def test_tflint_uses_absolute_repo_config_path(tmp_path: Path) -> None:
    """TFLint mirrors CI and passes an absolute `.tflint.hcl` path."""
    write_file(tmp_path / ".tflint.hcl", 'plugin "terraform" { enabled = true }\n')
    write_file(tmp_path / "main.tf", 'resource "terraform_data" "example" {}\n')
    recorder = CommandRecorder()

    result = terraform_hooks.run_tflint(
        root=tmp_path,
        resolve=lambda name: f"{name}-bin",
        runner=recorder,
    )

    assert result == 0
    assert recorder.calls == [
        (["tflint-bin", "--init"], tmp_path.resolve()),
        (
            ["tflint-bin", "--recursive", "--config", str(tmp_path.resolve() / ".tflint.hcl")],
            tmp_path.resolve(),
        ),
    ]


def test_validate_skips_without_resolving_when_only_tftest_exists(tmp_path: Path) -> None:
    """A lone Terraform test file is not a validation target."""
    write_file(tmp_path / "templates" / "terraform" / "Example.tftest.hcl")

    def fail_resolve(name: str) -> str:
        raise AssertionError(f"Unexpected executable resolution for {name}")

    result = terraform_hooks.run_terraform_validate(root=tmp_path, resolve=fail_resolve)

    assert result == 0


def test_missing_terraform_message_is_actionable(tmp_path: Path) -> None:
    """Missing Terraform failures name the binary and official install guidance."""
    write_file(tmp_path / "main.tf", 'resource "terraform_data" "example" {}\n')

    with pytest.raises(terraform_hooks.MissingExecutableError) as error:
        terraform_hooks.run_terraform_validate(root=tmp_path, resolve=lambda name: None)

    message = str(error.value)
    assert "`terraform`" in message
    assert "Install HashiCorp Terraform" in message
    assert terraform_hooks.TERRAFORM_INSTALL_URL in message


def test_missing_tflint_message_is_actionable_when_tf_files_exist(tmp_path: Path) -> None:
    """Missing TFLint failures name the binary and official install guidance."""
    write_file(tmp_path / "main.tf", 'resource "terraform_data" "example" {}\n')

    with pytest.raises(terraform_hooks.MissingExecutableError) as error:
        terraform_hooks.run_tflint(root=tmp_path, resolve=lambda name: None)

    message = str(error.value)
    assert "`tflint`" in message
    assert "Install TFLint" in message
    assert terraform_hooks.TFLINT_INSTALL_URL in message


def test_find_terraform_directories_discovers_tf_json_only_modules(tmp_path: Path) -> None:
    """Directories containing only `.tf.json` configuration are discovered."""
    json_only_dir = tmp_path / "modules" / "json_only"
    write_file(json_only_dir / "main.tf.json", '{"resource": {}}\n')

    discovered = terraform_hooks.find_terraform_directories(tmp_path)

    assert discovered == [json_only_dir.resolve()]


def test_find_files_skips_python_tool_cache_directories(tmp_path: Path) -> None:
    """Python tool caches (.pytest_cache, .mypy_cache, .ruff_cache) must not be traversed."""
    write_file(
        tmp_path / "modules" / "example" / "main.tf", 'resource "terraform_data" "example" {}\n'
    )
    write_file(tmp_path / ".pytest_cache" / "should-not-discover.tf", "// pytest cache\n")
    write_file(tmp_path / ".mypy_cache" / "should-not-discover.tf", "// mypy cache\n")
    write_file(tmp_path / ".ruff_cache" / "should-not-discover.tf", "// ruff cache\n")

    discovered = terraform_hooks.find_terraform_directories(tmp_path)

    assert discovered == [(tmp_path / "modules" / "example").resolve()]


def test_missing_tflint_config_raises_actionable_error(tmp_path: Path) -> None:
    """A missing `.tflint.hcl` raises MissingConfigurationError with actionable guidance."""
    write_file(tmp_path / "main.tf", 'resource "terraform_data" "example" {}\n')

    def fail_runner(command: list[str], cwd: Path) -> int:
        raise AssertionError(f"TFLint should not be invoked when config is missing: {command!r}")

    with pytest.raises(terraform_hooks.MissingConfigurationError) as error:
        terraform_hooks.run_tflint(
            root=tmp_path,
            resolve=lambda name: f"{name}-bin",
            runner=fail_runner,
        )

    message = str(error.value)
    assert ".tflint.hcl" in message
    assert "remove the `terraform-tflint` hook" in message
    assert terraform_hooks.TFLINT_CONFIG_REFERENCE_URL in message


def test_subprocess_runner_disables_shell(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The subprocess boundary must not invoke a shell."""
    recorded: dict[str, Any] = {}

    def fake_run(
        command: list[str],
        cwd: Path,
        shell: bool,
        check: bool,
    ) -> SimpleNamespace:
        recorded.update(command=command, cwd=cwd, shell=shell, check=check)
        return SimpleNamespace(returncode=17)

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = terraform_hooks.run_subprocess(["terraform", "fmt"], tmp_path)

    assert result == 17
    assert recorded == {
        "command": ["terraform", "fmt"],
        "cwd": tmp_path,
        "shell": False,
        "check": False,
    }
