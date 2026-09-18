"""Verify the baseline-owned pre-commit runner consumers."""

from __future__ import annotations

import os
import re
import shlex
import shutil
import subprocess
import sys
import textwrap
from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal

import yaml  # type: ignore[import-untyped]

from tests._pytest_compat import pytest

pytestmark = pytest.mark.upstream_template_only

REPO_ROOT = Path(__file__).resolve().parent.parent
RUNNER_REQUIREMENT_PATH = REPO_ROOT / "requirements-pre-commit.txt"
PYTHON_INSTALLER_PATHS = (
    ".github/workflows/precommit-ci.yml",
    ".github/workflows/data-ci.yml",
    ".github/workflows/auto-fix-precommit.yml",
    ".azuredevops/pipelines/precommit.yml",
    ".azuredevops/pipelines/data-ci.yml",
)
GITHUB_CACHE_WORKFLOWS = (
    ".github/workflows/precommit-ci.yml",
    ".github/workflows/data-ci.yml",
)
HOOK_PATH = REPO_ROOT / ".claude/hooks/session-start.sh"
EXACT_REQUIREMENT_RE = re.compile(r"pre-commit==(?P<version>[0-9]+\.[0-9]+\.[0-9]+)\Z")


def runner_requirement() -> str:
    """Return the repository pin after independently validating its public shape."""
    requirement = RUNNER_REQUIREMENT_PATH.read_text(encoding="utf-8").strip()
    assert EXACT_REQUIREMENT_RE.fullmatch(requirement)
    return requirement


def assert_immutable_action_references(workflow: str) -> None:
    """Require full upstream-style references and same-line release annotations."""
    uses_lines = [
        line.strip() for line in workflow.splitlines() if line.strip().startswith("uses:")
    ]
    assert uses_lines
    for line in uses_lines:
        assert re.fullmatch(
            r"uses: [A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40} # v[0-9]+\.[0-9]+\.[0-9]+",
            line,
        ), line


def assert_candidate_hook_checkout(workflow_text: str) -> None:
    """Require credential-free checkout before actual candidate pre-commit steps."""
    workflow = yaml.safe_load(workflow_text)
    hook_jobs = 0
    for job in workflow["jobs"].values():
        steps = job.get("steps", [])
        hook_indexes = [
            index
            for index, step in enumerate(steps)
            if re.search(r"\bpre-commit\s+run\b", step.get("run", ""))
        ]
        if not hook_indexes:
            continue
        hook_jobs += 1
        assert job.get("permissions", workflow.get("permissions")) == {"contents": "read"}
        for hook_index in hook_indexes:
            checkouts = [
                step
                for step in steps[:hook_index]
                if step.get("uses", "").startswith("actions/checkout@")
            ]
            assert checkouts, "candidate hooks require a preceding checkout"
            for checkout in checkouts:
                assert checkout.get("with", {}).get("persist-credentials") is False
    assert hook_jobs, "the fixture must exercise an actual candidate-hook job"


@pytest.mark.parametrize("relative_path", PYTHON_INSTALLER_PATHS[:3])
def test_candidate_hook_workflows_do_not_persist_checkout_credentials(relative_path: str) -> None:
    """All three real hook entry points retain read-only, credential-free checkout."""
    assert_candidate_hook_checkout((REPO_ROOT / relative_path).read_text(encoding="utf-8"))


@pytest.mark.parametrize("relative_path", PYTHON_INSTALLER_PATHS[:3])
@pytest.mark.parametrize("mutation", ["omitted", "true", "string-false", "write-permission"])
def test_candidate_hook_workflow_rejects_weakened_checkout(
    relative_path: str, mutation: str
) -> None:
    """Mutations of actual workflows must fail the independent structural oracle."""
    workflow = yaml.safe_load((REPO_ROOT / relative_path).read_text(encoding="utf-8"))
    checkout = next(
        step
        for job in workflow["jobs"].values()
        for step in job["steps"]
        if step.get("uses", "").startswith("actions/checkout@")
    )
    if mutation == "omitted":
        del checkout["with"]["persist-credentials"]
    elif mutation == "true":
        checkout["with"]["persist-credentials"] = True
    elif mutation == "string-false":
        checkout["with"]["persist-credentials"] = "false"
    else:
        workflow["permissions"]["contents"] = "write"
    with pytest.raises(AssertionError):
        assert_candidate_hook_checkout(yaml.safe_dump(workflow))


@pytest.mark.parametrize("relative_path", PYTHON_INSTALLER_PATHS[:3])
def test_review_support_actions_are_immutable_and_release_annotated(relative_path: str) -> None:
    """Each changed GitHub workflow keeps direct immutable, updateable references."""
    workflow = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
    assert_immutable_action_references(workflow)
    without_pin = re.sub(r"@[0-9a-f]{40}", "@v7", workflow, count=1)
    without_release = re.sub(r" # v[0-9]+\.[0-9]+\.[0-9]+", "", workflow, count=1)
    assert without_pin != workflow
    assert without_release != workflow
    for mutant in (without_pin, without_release):
        with pytest.raises(AssertionError):
            assert_immutable_action_references(mutant)


def expected_version_output(requirement: str | None = None) -> str:
    """Return the CLI identity selected by an exact runner requirement."""
    selected = requirement or runner_requirement()
    match = EXACT_REQUIREMENT_RE.fullmatch(selected)
    assert match is not None
    return f"pre-commit {match.group('version')}"


def github_python_block(path: Path) -> str:
    """Extract the one actual ``shell: python`` installer block from a workflow."""
    lines = path.read_text(encoding="utf-8").splitlines()
    shell_index = next(index for index, line in enumerate(lines) if line.strip() == "shell: python")
    run_index = next(
        index for index in range(shell_index + 1, len(lines)) if lines[index].strip() == "run: |"
    )
    run_indent = len(lines[run_index]) - len(lines[run_index].lstrip())
    block_lines: list[str] = []
    for line in lines[run_index + 1 :]:
        indent = len(line) - len(line.lstrip())
        if line.strip() and indent <= run_indent:
            break
        block_lines.append(line)
    return textwrap.dedent("\n".join(block_lines)).strip() + "\n"


def azure_python_block(path: Path) -> str:
    """Extract the actual Python heredoc installer from an Azure pipeline."""
    lines = path.read_text(encoding="utf-8").splitlines()
    start = next(index for index, line in enumerate(lines) if line.strip() == "python - <<'PY'")
    end = next(index for index in range(start + 1, len(lines)) if lines[index].strip() == "PY")
    return textwrap.dedent("\n".join(lines[start + 1 : end])).strip() + "\n"


def installer_source(relative_path: str) -> str:
    """Return one real installer source block without reimplementing it."""
    path = REPO_ROOT / relative_path
    if relative_path.startswith(".github/"):
        return github_python_block(path)
    return azure_python_block(path)


def execute_installer_source(
    source: str,
    tmp_path: Path,
    monkeypatch: Any,
    *,
    requirement_text: str | None,
    run: Callable[..., Any],
    check_output: Callable[..., str],
) -> None:
    """Execute an extracted installer with controlled filesystem and subprocesses."""
    if requirement_text is not None:
        (tmp_path / "requirements-pre-commit.txt").write_text(
            requirement_text,
            encoding="utf-8",
            newline="\n",
        )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(subprocess, "run", run)
    monkeypatch.setattr(subprocess, "check_output", check_output)
    exec(compile(source, "<workflow pre-commit installer>", "exec"), {})  # noqa: S102


@pytest.mark.parametrize("relative_path", PYTHON_INSTALLER_PATHS)
def test_actual_ci_installer_uses_exact_runner_source_and_verifies_command(
    tmp_path: Path,
    monkeypatch: Any,
    relative_path: str,
) -> None:
    """Every real CI installer consumes the shared file and checks the runnable CLI."""
    requirement = runner_requirement()
    run_calls: list[tuple[list[str], dict[str, Any]]] = []
    version_calls: list[tuple[list[str], dict[str, Any]]] = []

    def fake_run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        run_calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0)

    def fake_check_output(command: list[str], **kwargs: Any) -> str:
        version_calls.append((command, kwargs))
        return expected_version_output(requirement)

    execute_installer_source(
        installer_source(relative_path),
        tmp_path,
        monkeypatch,
        requirement_text=requirement + "\n",
        run=fake_run,
        check_output=fake_check_output,
    )

    assert run_calls == [
        (
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--requirement",
                "requirements-pre-commit.txt",
            ],
            {"check": True},
        )
    ]
    assert version_calls == [(["pre-commit", "--version"], {"text": True})]


@pytest.mark.parametrize("relative_path", PYTHON_INSTALLER_PATHS)
@pytest.mark.parametrize(
    "requirement_text",
    [
        None,
        "pre-commit",
        "pre-commit>=4",
        f"{runner_requirement()}\nwheel==1",
    ],
    ids=("missing", "malformed", "range", "extra-requirement"),
)
def test_actual_ci_installer_rejects_missing_or_nonexact_runner_source(
    tmp_path: Path,
    monkeypatch: Any,
    relative_path: str,
    requirement_text: str | None,
) -> None:
    """Missing, ranged, malformed, and multi-requirement sources fail before install."""

    def unexpected(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("invalid input must fail before invoking subprocess")

    with pytest.raises((FileNotFoundError, SystemExit)):
        execute_installer_source(
            installer_source(relative_path),
            tmp_path,
            monkeypatch,
            requirement_text=requirement_text,
            run=unexpected,
            check_output=unexpected,
        )


@pytest.mark.parametrize("relative_path", PYTHON_INSTALLER_PATHS)
def test_actual_ci_installer_propagates_install_failure(
    tmp_path: Path,
    monkeypatch: Any,
    relative_path: str,
) -> None:
    """A failed pip install cannot continue to a version check."""

    def failed_run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if kwargs.get("check"):
            raise subprocess.CalledProcessError(1, command)
        return subprocess.CompletedProcess(command, 1)

    def unexpected_version(*_args: Any, **_kwargs: Any) -> str:
        raise AssertionError("failed install must not reach version verification")

    with pytest.raises(subprocess.CalledProcessError):
        execute_installer_source(
            installer_source(relative_path),
            tmp_path,
            monkeypatch,
            requirement_text=runner_requirement(),
            run=failed_run,
            check_output=unexpected_version,
        )


@pytest.mark.parametrize("relative_path", PYTHON_INSTALLER_PATHS)
@pytest.mark.parametrize("failure", ["mismatch", "broken-command"])
def test_actual_ci_installer_rejects_wrong_or_broken_installed_command(
    tmp_path: Path,
    monkeypatch: Any,
    relative_path: str,
    failure: str,
) -> None:
    """Successful installation is insufficient without the expected executable identity."""

    def successful_run(command: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 0)

    def failed_version(command: list[str], **_kwargs: Any) -> str:
        if failure == "broken-command":
            raise subprocess.CalledProcessError(1, command)
        return "pre-commit 0.0.0"

    expected_error = subprocess.CalledProcessError if failure == "broken-command" else SystemExit
    with pytest.raises(expected_error):
        execute_installer_source(
            installer_source(relative_path),
            tmp_path,
            monkeypatch,
            requirement_text=runner_requirement(),
            run=successful_run,
            check_output=failed_version,
        )


def test_installer_failure_oracle_detects_removed_check_guard(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    """The failure oracle kills a mutant that stops asking pip to raise."""
    source = installer_source(PYTHON_INSTALLER_PATHS[0])
    mutant = source.replace("check=True", "check=False", 1)
    assert mutant != source

    def check_sensitive_run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if kwargs.get("check"):
            raise subprocess.CalledProcessError(1, command)
        return subprocess.CompletedProcess(command, 1)

    def expected_output(*_args: Any, **_kwargs: Any) -> str:
        return expected_version_output()

    execute_installer_source(
        mutant,
        tmp_path,
        monkeypatch,
        requirement_text=runner_requirement(),
        run=check_sensitive_run,
        check_output=expected_output,
    )

    fresh = tmp_path / "production"
    fresh.mkdir()
    with pytest.raises(subprocess.CalledProcessError):
        execute_installer_source(
            source,
            fresh,
            monkeypatch,
            requirement_text=runner_requirement(),
            run=check_sensitive_run,
            check_output=expected_output,
        )


def test_github_runner_caches_follow_both_runner_inputs() -> None:
    """The two cached gates invalidate Python and hook caches on the shared source."""
    expected_hash = "hashFiles('.pre-commit-config.yaml', 'requirements-pre-commit.txt')"
    for relative_path in GITHUB_CACHE_WORKFLOWS:
        text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        assert re.search(r"cache:\s*['\"]pip['\"]", text)
        assert "cache-dependency-path: requirements-pre-commit.txt" in text
        assert expected_hash in text

    auto_fix_text = (REPO_ROOT / ".github/workflows/auto-fix-precommit.yml").read_text(
        encoding="utf-8"
    )
    assert "cache: pip" not in auto_fix_text
    assert "hashFiles(" not in auto_fix_text


def hook_prefix() -> str:
    """Return the actual hook through the end of its baseline-only block."""
    text = HOOK_PATH.read_text(encoding="utf-8")
    end_marker = "# template-sync: end baseline-only"
    end = text.index(end_marker) + len(end_marker)
    return text[:end] + "\n"


def make_executable(path: Path, text: str) -> None:
    """Write an LF shell fixture and make it executable on POSIX hosts."""
    path.write_text(text, encoding="utf-8", newline="\n")
    path.chmod(0o755)


def bash_path(bash: str, path: Path) -> str:
    """Return a path usable by Bash on both native POSIX and Git for Windows."""
    if os.name != "nt":
        return str(path)
    if subprocess.check_output([bash, "-lc", "uname -s"], text=True).strip() == "Linux":
        drive, tail = os.path.splitdrive(str(path.resolve()))
        assert drive and drive.endswith(":")
        normalized_tail = tail.lstrip("\\/").replace("\\", "/")
        return f"/mnt/{drive[0].lower()}/{normalized_tail}"
    return subprocess.check_output(
        [bash, "-lc", 'cygpath -u "$1"', "bash", str(path)],
        text=True,
    ).strip()


def run_hook_fixture(
    tmp_path: Path,
    *,
    installer: str | None,
    initial_version: str | None,
    requirement_text: str | None = None,
    broken_precommit: bool = False,
    installer_exit: int = 0,
    installer_updates: bool = True,
) -> tuple[subprocess.CompletedProcess[str], str]:
    """Run the actual baseline hook block with local executable mocks."""
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("Bash is required to exercise the actual Claude hook")
    assert bash is not None

    repo = tmp_path / "repo"
    hook = repo / ".claude" / "hooks" / "session-start.sh"
    hook.parent.mkdir(parents=True)
    make_executable(hook, hook_prefix())
    if requirement_text is not None:
        (repo / "requirements-pre-commit.txt").write_text(
            requirement_text,
            encoding="utf-8",
            newline="\n",
        )

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    state = tmp_path / "pre-commit.state"
    install_log = tmp_path / "installer.log"
    env_file = tmp_path / "claude.env"
    env_file.write_text("", encoding="utf-8")
    if initial_version is not None:
        state.write_text(initial_version + "\n", encoding="utf-8", newline="\n")

    make_executable(
        fake_bin / "pre-commit",
        """#!/bin/sh
if [ "${BROKEN_PRECOMMIT:-}" = "1" ]; then
  exit 2
fi
if [ -f "$PRE_COMMIT_STATE" ]; then
  cat "$PRE_COMMIT_STATE"
else
  echo "pre-commit 0.0.0"
fi
""",
    )
    installer_script = """#!/bin/sh
printf '%s\n' "$*" >> "$INSTALL_LOG"
if [ "${INSTALLER_EXIT:-0}" -ne 0 ]; then
  exit "$INSTALLER_EXIT"
fi
if [ "${INSTALLER_UPDATES:-1}" = "1" ]; then
  printf '%s\n' "$EXPECTED_PRE_COMMIT" > "$PRE_COMMIT_STATE"
fi
"""
    if installer in {"uv", "pipx"}:
        make_executable(fake_bin / installer, installer_script)
    if installer == "python":
        make_executable(
            fake_bin / "python",
            """#!/bin/sh
if [ "$1" = "-m" ] && [ "$2" = "site" ] && [ "$3" = "--user-base" ]; then
  printf '%s\n' "$FAKE_USER_BASE"
  exit 0
fi
printf '%s\n' "$*" >> "$INSTALL_LOG"
if [ "${INSTALLER_EXIT:-0}" -ne 0 ]; then
  exit "$INSTALLER_EXIT"
fi
if [ "${INSTALLER_UPDATES:-1}" = "1" ]; then
  printf '%s\n' "$EXPECTED_PRE_COMMIT" > "$PRE_COMMIT_STATE"
fi
""",
        )

    requirement = requirement_text if requirement_text is not None else runner_requirement()
    expected = (
        expected_version_output(requirement)
        if EXACT_REQUIREMENT_RE.fullmatch(requirement.strip())
        else "invalid"
    )
    fake_bin_bash = bash_path(bash, fake_bin)
    shell_env = {
        "PATH": f"{fake_bin_bash}:/usr/bin:/bin",
        "CLAUDE_CODE_REMOTE": "true",
        "CLAUDE_ENV_FILE": bash_path(bash, env_file),
        "HOME": bash_path(bash, tmp_path / "home"),
        "UV_TOOL_BIN_DIR": fake_bin_bash,
        "PIPX_BIN_DIR": fake_bin_bash,
        "FAKE_USER_BASE": bash_path(bash, tmp_path),
        "PRE_COMMIT_STATE": bash_path(bash, state),
        "INSTALL_LOG": bash_path(bash, install_log),
        "EXPECTED_PRE_COMMIT": expected,
        "BROKEN_PRECOMMIT": "1" if broken_precommit else "0",
        "INSTALLER_EXIT": str(installer_exit),
        "INSTALLER_UPDATES": "1" if installer_updates else "0",
    }
    wrapper = tmp_path / "run-hook.sh"
    exports = "\n".join(f"export {name}={shlex.quote(value)}" for name, value in shell_env.items())
    make_executable(
        wrapper,
        f"#!/bin/sh\n{exports}\nexec /bin/bash {shlex.quote(bash_path(bash, hook))}\n",
    )
    result = subprocess.run(
        [bash, bash_path(bash, wrapper)],
        check=False,
        capture_output=True,
        text=True,
    )
    log = install_log.read_text(encoding="utf-8") if install_log.exists() else ""
    return result, log


def run_hook_path_precedence_fixture(
    tmp_path: Path,
    *,
    installer: Literal["uv", "pipx", "python"],
    selected_position: Literal["first", "later", "absent"],
    selected_version: str,
    hook_source: str | None = None,
) -> tuple[subprocess.CompletedProcess[str], str, str]:
    """Run the actual hook with separate stale, installer, and selected directories."""
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("Bash is required to exercise the actual Claude hook")
    assert bash is not None

    repo = tmp_path / "repo"
    hook = repo / ".claude" / "hooks" / "session-start.sh"
    hook.parent.mkdir(parents=True)
    make_executable(hook, hook_source or hook_prefix())
    (repo / "requirements-pre-commit.txt").write_text(
        runner_requirement(), encoding="utf-8", newline="\n"
    )

    stale_bin = tmp_path / "stale-bin"
    installer_bin = tmp_path / "installer-bin"
    selected_base = tmp_path / "selected-user" if installer == "python" else tmp_path
    selected_bin = selected_base / "bin" if installer == "python" else tmp_path / "selected-bin"
    for directory in (stale_bin, installer_bin, selected_bin):
        directory.mkdir(parents=True, exist_ok=True)

    selected_state = tmp_path / "selected-pre-commit.state"
    selected_state.write_text(selected_version + "\n", encoding="utf-8", newline="\n")
    install_log = tmp_path / "installer.log"
    env_file = tmp_path / "claude.env"
    env_file.write_text("", encoding="utf-8")

    make_executable(stale_bin / "pre-commit", "#!/bin/sh\necho 'pre-commit 0.0.0'\n")
    make_executable(
        selected_bin / "pre-commit",
        """#!/bin/sh
cat "$SELECTED_PRE_COMMIT_STATE"
""",
    )
    installer_script = """#!/bin/sh
printf '%s\n' "$*" >> "$INSTALL_LOG"
printf '%s\n' "$EXPECTED_PRE_COMMIT" > "$SELECTED_PRE_COMMIT_STATE"
"""
    if installer in {"uv", "pipx"}:
        make_executable(installer_bin / installer, installer_script)
    else:
        make_executable(
            installer_bin / "python",
            """#!/bin/sh
if [ "$1" = "-m" ] && [ "$2" = "site" ] && [ "$3" = "--user-base" ]; then
  printf '%s\n' "$FAKE_USER_BASE"
  exit 0
fi
printf '%s\n' "$*" >> "$INSTALL_LOG"
printf '%s\n' "$EXPECTED_PRE_COMMIT" > "$SELECTED_PRE_COMMIT_STATE"
""",
        )

    stale_bin_bash = bash_path(bash, stale_bin)
    installer_bin_bash = bash_path(bash, installer_bin)
    selected_bin_bash = bash_path(bash, selected_bin)
    if selected_position == "first":
        path_entries = [selected_bin_bash, stale_bin_bash, installer_bin_bash]
    elif selected_position == "later":
        path_entries = [stale_bin_bash, installer_bin_bash, selected_bin_bash]
    else:
        path_entries = [stale_bin_bash, installer_bin_bash]
    initial_path = ":".join([*path_entries, "/usr/bin", "/bin"])

    shell_env = {
        "PATH": initial_path,
        "CLAUDE_CODE_REMOTE": "true",
        "CLAUDE_ENV_FILE": bash_path(bash, env_file),
        "HOME": bash_path(bash, tmp_path / "home"),
        "UV_TOOL_BIN_DIR": selected_bin_bash,
        "PIPX_BIN_DIR": selected_bin_bash,
        "FAKE_USER_BASE": bash_path(bash, selected_base),
        "SELECTED_PRE_COMMIT_STATE": bash_path(bash, selected_state),
        "INSTALL_LOG": bash_path(bash, install_log),
        "EXPECTED_PRE_COMMIT": expected_version_output(),
    }
    exports = "\n".join(f"export {name}={shlex.quote(value)}" for name, value in shell_env.items())
    wrapper = tmp_path / "run-hook-and-probe.sh"
    make_executable(
        wrapper,
        (
            f"#!/bin/bash\n{exports}\n"
            f". {shlex.quote(bash_path(bash, hook))}\n"
            "printf 'FINAL_COMMAND=%s\\n' \"$(command -v pre-commit)\"\n"
            "printf 'FINAL_VERSION=%s\\n' \"$(pre-commit --version)\"\n"
            "printf 'FINAL_PATH=%s\\n' \"$PATH\"\n"
        ),
    )
    result = subprocess.run(
        [bash, bash_path(bash, wrapper)],
        check=False,
        capture_output=True,
        text=True,
    )
    log = install_log.read_text(encoding="utf-8") if install_log.exists() else ""
    return result, log, env_file.read_text(encoding="utf-8")


def assert_selected_runner_is_active(
    result: subprocess.CompletedProcess[str],
    *,
    bash: str,
    selected_bin: Path,
) -> None:
    """Require the ordinary command to resolve the selected exact runner."""
    selected_bin_bash = bash_path(bash, selected_bin)
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"FINAL_COMMAND={selected_bin_bash}/pre-commit" in result.stdout
    assert f"FINAL_VERSION={expected_version_output()}" in result.stdout
    final_path = next(
        line.removeprefix("FINAL_PATH=")
        for line in result.stdout.splitlines()
        if line.startswith("FINAL_PATH=")
    )
    assert final_path.split(":", maxsplit=1)[0] == selected_bin_bash


def selected_runner_bin(tmp_path: Path, installer: str) -> Path:
    """Return the install directory chosen by one fixture installer branch."""
    return (
        tmp_path / "selected-user" / "bin" if installer == "python" else tmp_path / "selected-bin"
    )


def assert_expected_installer_call(installer: str, install_log: str) -> None:
    """Require one installer to receive the exact shared pre-commit pin."""
    requirement = runner_requirement()
    if installer == "uv":
        assert install_log == f"tool install --force {requirement}\n"
    elif installer == "pipx":
        assert install_log == f"install --force {requirement}\n"
    else:
        assert install_log == f"-m pip install --user {requirement}\n"


@pytest.mark.parametrize("installer", ["uv", "pipx", "python"])
def test_claude_hook_activates_selected_runner_ahead_of_stale_command(
    tmp_path: Path, installer: Literal["uv", "pipx", "python"]
) -> None:
    """Every installer branch makes its exact runner win ordinary PATH lookup."""
    result, install_log, env_text = run_hook_path_precedence_fixture(
        tmp_path,
        installer=installer,
        selected_position="later",
        selected_version="pre-commit 1.0.0",
    )
    bash = shutil.which("bash")
    assert bash is not None
    selected_bin = selected_runner_bin(tmp_path, installer)
    assert_selected_runner_is_active(result, bash=bash, selected_bin=selected_bin)
    assert_expected_installer_call(installer, install_log)

    selected_bin_bash = bash_path(bash, selected_bin)
    assert env_text.splitlines() == [f'export PATH="{selected_bin_bash}:$PATH"']
    final_path = next(
        line.removeprefix("FINAL_PATH=")
        for line in result.stdout.splitlines()
        if line.startswith("FINAL_PATH=")
    )
    assert final_path.split(":").count(selected_bin_bash) == 2


@pytest.mark.parametrize("installer", ["uv", "pipx", "python"])
def test_claude_hook_reuses_exact_runner_in_selected_later_directory(
    tmp_path: Path, installer: Literal["uv", "pipx", "python"]
) -> None:
    """Activation avoids reinstalling an exact runner hidden behind a stale command."""
    result, install_log, env_text = run_hook_path_precedence_fixture(
        tmp_path,
        installer=installer,
        selected_position="later",
        selected_version=expected_version_output(),
    )
    bash = shutil.which("bash")
    assert bash is not None
    selected_bin = selected_runner_bin(tmp_path, installer)
    assert_selected_runner_is_active(result, bash=bash, selected_bin=selected_bin)
    assert install_log == ""
    selected_bin_bash = bash_path(bash, selected_bin)
    assert env_text.splitlines() == [f'export PATH="{selected_bin_bash}:$PATH"']


@pytest.mark.parametrize("selected_position", ["first", "absent"])
def test_claude_hook_activation_preserves_first_and_absent_path_controls(
    tmp_path: Path, selected_position: Literal["first", "absent"]
) -> None:
    """Activation remains correct when the selected directory is first or absent."""
    result, install_log, env_text = run_hook_path_precedence_fixture(
        tmp_path,
        installer="uv",
        selected_position=selected_position,
        selected_version="pre-commit 1.0.0",
    )
    bash = shutil.which("bash")
    assert bash is not None
    selected_bin = selected_runner_bin(tmp_path, "uv")
    assert_selected_runner_is_active(result, bash=bash, selected_bin=selected_bin)
    assert_expected_installer_call("uv", install_log)
    selected_bin_bash = bash_path(bash, selected_bin)
    assert env_text.splitlines() == [f'export PATH="{selected_bin_bash}:$PATH"']
    final_path = next(
        line.removeprefix("FINAL_PATH=")
        for line in result.stdout.splitlines()
        if line.startswith("FINAL_PATH=")
    )
    assert final_path.split(":").count(selected_bin_bash) == 1


def test_claude_hook_activation_oracle_rejects_removed_force_front(tmp_path: Path) -> None:
    """The stale-command regression must return when only persistence remains."""
    source = hook_prefix()
    activation_call = 'activate_pre_commit_bin "$pre_commit_bin_dir"'
    assert source.count(activation_call) == 3
    mutant = source.replace(
        activation_call,
        'persist_path_prepend "$pre_commit_bin_dir"',
    )

    original_result, _original_log, _original_env = run_hook_path_precedence_fixture(
        tmp_path / "original",
        installer="uv",
        selected_position="later",
        selected_version="pre-commit 1.0.0",
        hook_source=source,
    )
    mutant_result, mutant_log, _mutant_env = run_hook_path_precedence_fixture(
        tmp_path / "mutant",
        installer="uv",
        selected_position="later",
        selected_version="pre-commit 1.0.0",
        hook_source=mutant,
    )

    assert original_result.returncode == 0, original_result.stdout + original_result.stderr
    assert mutant_result.returncode != 0, mutant_result.stdout + mutant_result.stderr
    assert_expected_installer_call("uv", mutant_log)
    assert "installation did not provide" in mutant_result.stderr


def test_claude_hook_reuses_the_exact_available_runner(tmp_path: Path) -> None:
    """An exact runnable command avoids every installer branch."""
    result, install_log = run_hook_fixture(
        tmp_path,
        installer="uv",
        initial_version=expected_version_output(),
        requirement_text=runner_requirement(),
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "pre-commit already available" in result.stdout
    assert install_log == ""


@pytest.mark.parametrize("installer", ["uv", "pipx", "python"])
def test_claude_hook_installs_exact_runner_through_supported_branch(
    tmp_path: Path,
    installer: str,
) -> None:
    """Each supported installer receives the exact shared requirement."""
    result, install_log = run_hook_fixture(
        tmp_path,
        installer=installer,
        initial_version="pre-commit 0.0.0",
        requirement_text=runner_requirement(),
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert runner_requirement() in install_log
    if installer == "uv":
        assert f"tool install --force {runner_requirement()}" in install_log
    elif installer == "pipx":
        assert f"install --force {runner_requirement()}" in install_log
    else:
        assert f"-m pip install --user {runner_requirement()}" in install_log
    assert expected_version_output() in result.stdout


@pytest.mark.parametrize(
    ("case", "kwargs"),
    [
        pytest.param("missing", {"requirement_text": None}, id="missing-requirement"),
        pytest.param("range", {"requirement_text": "pre-commit>=4"}, id="ranged-requirement"),
        pytest.param("broken", {"broken_precommit": True}, id="broken-command"),
        pytest.param("installer", {"installer_exit": 7}, id="installer-failure"),
        pytest.param("wrong", {"installer_updates": False}, id="wrong-version-after-install"),
    ],
)
def test_claude_hook_fails_closed_for_invalid_or_unfulfilled_runner(
    tmp_path: Path,
    case: str,
    kwargs: dict[str, Any],
) -> None:
    """The hook rejects invalid input and cannot report an unfulfilled install."""
    call_kwargs = dict(kwargs)
    supplied_requirement = call_kwargs.pop("requirement_text", runner_requirement())
    if case == "missing":
        requirement_text = None
    else:
        requirement_text = supplied_requirement
    result, _install_log = run_hook_fixture(
        tmp_path,
        installer="uv",
        initial_version="pre-commit 0.0.0",
        requirement_text=requirement_text,
        **call_kwargs,
    )

    assert result.returncode != 0, result.stdout + result.stderr
