"""Repo-local Terraform pre-commit hook entrypoints.

The hooks in this module intentionally avoid shell scripts so that native
Windows / PowerShell, WSL/Linux, and macOS execute the same Python code path.
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TERRAFORM_INSTALL_URL = "https://developer.hashicorp.com/terraform/install"
TFLINT_INSTALL_URL = "https://github.com/terraform-linters/tflint#installation"
TFLINT_CONFIG_REFERENCE_URL = (
    "https://github.com/terraform-linters/tflint/blob/master/docs/user-guide/config.md"
)
TFLINT_CONFIG_FILENAME = ".tflint.hcl"
SKIPPED_DIRECTORY_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".terraform",
    "__pycache__",
    "node_modules",
}

ExecutableResolver = Callable[[str], str | None]
CommandRunner = Callable[[Sequence[str], Path], int]


class MissingExecutableError(RuntimeError):
    """Raised when a required Terraform validation executable is unavailable."""


class MissingConfigurationError(RuntimeError):
    """Raised when a required Terraform validation configuration file is missing."""


def resolve_executable(name: str) -> str:
    """Resolve an executable from PATH or raise an actionable error."""
    executable = shutil.which(name)
    if executable is None:
        raise MissingExecutableError(build_missing_executable_message(name))
    return executable


def require_executable(name: str, resolve: ExecutableResolver) -> str:
    """Resolve an executable through an injected resolver and normalize failures."""
    executable = resolve(name)
    if executable is None:
        raise MissingExecutableError(build_missing_executable_message(name))
    return executable


def build_missing_tflint_config_message(config_path: Path) -> str:
    """Build actionable guidance for a missing TFLint configuration file."""
    return "\n".join(
        [
            f"Required TFLint configuration file `{config_path.name}` was not found at {config_path}.",
            (
                f"Either restore `{TFLINT_CONFIG_FILENAME}` at the repository root, or remove the "
                "`terraform-tflint` hook from `.pre-commit-config.yaml` if TFLint is no longer needed."
            ),
            f"TFLint configuration reference: {TFLINT_CONFIG_REFERENCE_URL}",
        ]
    )


def build_missing_executable_message(name: str) -> str:
    """Build platform-appropriate installation guidance for a missing executable."""
    system = platform.system().lower()
    if name == "terraform":
        install_url = TERRAFORM_INSTALL_URL
        tool_label = "HashiCorp Terraform"
        windows = "Windows: install HashiCorp Terraform from the official download page, or run `choco install terraform` if your organization uses Chocolatey."
        macos = "macOS: run `brew tap hashicorp/tap` and `brew install hashicorp/tap/terraform`, or use the official download page."
        unix = "Linux/FreeBSD: use the HashiCorp package repository or the official binary download for your platform."
    elif name == "tflint":
        install_url = TFLINT_INSTALL_URL
        tool_label = "TFLint"
        windows = "Windows: install TFLint from its GitHub releases, or run `choco install tflint` if your organization uses Chocolatey."
        macos = "macOS: run `brew install tflint`, or use the GitHub releases page."
        unix = "Linux/FreeBSD: use the official install script or download a release binary from GitHub."
    else:
        install_url = ""
        tool_label = name
        windows = f"Windows: install `{name}` and restart PowerShell so PATH is refreshed."
        macos = f"macOS: install `{name}` and restart your terminal so PATH is refreshed."
        unix = f"Linux/FreeBSD: install `{name}` and restart your shell so PATH is refreshed."

    if system == "windows":
        platform_guidance = windows
    elif system == "darwin":
        platform_guidance = macos
    else:
        platform_guidance = unix

    lines = [
        f"Required executable `{name}` was not found on PATH.",
        f"Install {tool_label}, then restart your shell so `{name}` is discoverable.",
        platform_guidance,
    ]
    if install_url:
        lines.append(f"Install guidance: {install_url}")
    return "\n".join(lines)


def run_subprocess(command: Sequence[str], cwd: Path) -> int:
    """Run a validation command without invoking a shell."""
    completed = subprocess.run(command, cwd=cwd, shell=False, check=False)
    return completed.returncode


def find_files(root: Path, predicate: Callable[[Path], bool]) -> list[Path]:
    """Find repo-contained, non-symlink files matching a predicate."""
    root = root.resolve()
    matches: list[Path] = []

    for directory_path, directory_names, file_names in os.walk(root, followlinks=False):
        directory = Path(directory_path)
        directory_names[:] = [
            name
            for name in directory_names
            if name not in SKIPPED_DIRECTORY_NAMES and not (directory / name).is_symlink()
        ]

        for file_name in file_names:
            candidate = directory / file_name
            if candidate.is_symlink():
                continue
            try:
                candidate.resolve().relative_to(root)
            except ValueError:
                continue
            if predicate(candidate):
                matches.append(candidate)

    return sorted(matches)


def is_terraform_format_target(path: Path, root: Path) -> bool:
    """Return whether a file should trigger the repository Terraform fmt check."""
    relative_path = path.relative_to(root)
    relative_parts = relative_path.parts
    if len(relative_parts) >= 2 and relative_parts[:2] == ("templates", "terraform"):
        return True
    return (
        path.name.endswith(".tf")
        or path.name.endswith(".tfvars")
        or path.name.endswith(".tftest.hcl")
        or path.name.endswith(".tf.json")
    )


def find_terraform_directories(root: Path) -> list[Path]:
    """Find directories containing Terraform `.tf` or `.tf.json` configuration files."""
    return sorted(
        {
            path.parent
            for path in find_files(
                root,
                lambda path: path.name.endswith(".tf") or path.name.endswith(".tf.json"),
            )
        }
    )


def run_terraform_format(
    root: Path = REPO_ROOT,
    resolve: ExecutableResolver = resolve_executable,
    runner: CommandRunner = run_subprocess,
) -> int:
    """Run `terraform fmt -check -recursive -diff` from the repository root."""
    root = root.resolve()
    format_targets = find_files(root, lambda path: is_terraform_format_target(path, root))
    if not format_targets:
        print("No Terraform format targets found; skipping terraform fmt.")
        return 0

    terraform = require_executable("terraform", resolve)
    return runner([terraform, "fmt", "-check", "-recursive", "-diff"], root)


def run_terraform_validate(
    root: Path = REPO_ROOT,
    resolve: ExecutableResolver = resolve_executable,
    runner: CommandRunner = run_subprocess,
) -> int:
    """Run `terraform init -backend=false` and `terraform validate` per `.tf` or `.tf.json` directory."""
    root = root.resolve()
    terraform_directories = find_terraform_directories(root)
    if not terraform_directories:
        print(
            "No Terraform directories containing .tf or .tf.json files found; "
            "skipping terraform validate."
        )
        return 0

    terraform = require_executable("terraform", resolve)
    for terraform_directory in terraform_directories:
        print(f"=== Validating {terraform_directory.relative_to(root)} ===")
        init_result = runner([terraform, "init", "-backend=false"], terraform_directory)
        if init_result != 0:
            return init_result
        validate_result = runner([terraform, "validate"], terraform_directory)
        if validate_result != 0:
            return validate_result
    return 0


def run_tflint(
    root: Path = REPO_ROOT,
    resolve: ExecutableResolver = resolve_executable,
    runner: CommandRunner = run_subprocess,
) -> int:
    """Run `tflint --init` and recursive linting with the repo root config."""
    root = root.resolve()
    terraform_directories = find_terraform_directories(root)
    if not terraform_directories:
        print("No Terraform directories containing .tf or .tf.json files found; skipping TFLint.")
        return 0

    tflint = require_executable("tflint", resolve)

    config_path = root / TFLINT_CONFIG_FILENAME
    if not config_path.is_file():
        raise MissingConfigurationError(build_missing_tflint_config_message(config_path))

    init_result = runner([tflint, "--init"], root)
    if init_result != 0:
        return init_result

    return runner([tflint, "--recursive", "--config", str(config_path)], root)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse Terraform hook CLI arguments."""
    parser = argparse.ArgumentParser(description="Run repo-local Terraform pre-commit hooks.")
    parser.add_argument(
        "hook",
        choices=("fmt", "validate", "tflint"),
        help="Terraform hook behavior to run.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the requested Terraform hook."""
    args = parse_args(argv)
    hook_functions = {
        "fmt": run_terraform_format,
        "validate": run_terraform_validate,
        "tflint": run_tflint,
    }

    try:
        return hook_functions[args.hook]()
    except (MissingExecutableError, MissingConfigurationError) as error:
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
