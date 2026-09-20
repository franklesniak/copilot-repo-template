"""Exercise each workflow invariant and independent failure-injection oracles."""

from __future__ import annotations

import copy
import importlib.util
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

import yaml  # type: ignore[import-untyped]

from tests._pytest_compat import pytest

pytestmark = pytest.mark.upstream_template_only
ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "workflow_security_tests", ROOT / ".github/scripts/validate_workflow_security.py"
)
assert SPEC is not None and SPEC.loader is not None
policy = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(policy)


def copy_policy(root: Path) -> dict[str, Any]:
    """Copy the real policy surface, including copyable documentation examples."""
    contract = policy.load_contract(ROOT)
    for relative in [policy.CONTRACT, policy.SCHEMA, *contract["workflows"], *contract["examples"]]:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    return cast(dict[str, Any], contract)


@pytest.mark.parametrize("path", sorted(policy.load_contract(ROOT)["workflows"]))
def test_each_owned_workflow_passes(path: str) -> None:
    """Every declared workflow passes universal and required-control validation."""
    expected = policy.load_contract(ROOT)["workflows"][path]
    assert policy.validate_workflow(policy.read_text(ROOT, path)) == expected


@pytest.mark.parametrize(
    ("before", "after", "message"),
    [
        (
            "{checkout}",
            "actions/checkout@v7",
            "full SHA",
        ),
        ("{sha}", "abcdef0", "full SHA"),
        ("{annotation}", "", "annotation"),
        ("{annotation}", " # v7", "annotation"),
        ("contents: read", "contents: write", "permissions"),
        ("persist-credentials: false", "persist-credentials: true", "persist-credentials"),
        ("  pull_request:", "  pull_request_target:", "privileged"),
        ("  pull_request:", "  workflow_run:", "privileged"),
        ("name: Workflow Security", "name: first\nname: second", "Duplicate"),
        ("name: Workflow Security", "name: [", "Invalid YAML"),
        ("name: Workflow Security", "name: &name Workflow Security", "anchors"),
        (
            "{checkout}",
            "./.github/actions/local",
            "external",
        ),
        (
            "{checkout}",
            "docker://image:latest",
            "external",
        ),
    ],
)
def test_universal_rule_mutations(before: str, after: str, message: str) -> None:
    """Each isolated unsafe input must fail before contract comparison."""
    source = policy.read_text(ROOT, ".github/workflows/workflow-security.yml")
    checkout_line = next(line for line in source.splitlines() if "uses: actions/checkout@" in line)
    reference = checkout_line.strip().split()[1]
    before = (
        before.replace("{checkout}", reference)
        .replace("{sha}", reference.split("@", 1)[1])
        .replace("{annotation}", " # " + checkout_line.split("#", 1)[1].strip())
    )
    assert before in source
    with pytest.raises(policy.PolicyError, match=message):
        policy.validate_workflow(source.replace(before, after, 1))


def test_job_permission_and_inline_reference_bypass() -> None:
    """Missing job permissions and flow-style unannotated uses are rejected."""
    text = policy.read_text(ROOT, ".github/workflows/workflow-security.yml")
    for source in [
        text.replace("    permissions:\n      contents: read\n", ""),
        text.replace(
            "    permissions:\n      contents: read\n", "    permissions:\n      contents: write\n"
        ),
        text.replace(
            "        uses: actions/checkout@", "        uses: >-\n          actions/checkout@"
        ),
    ]:
        with pytest.raises(policy.PolicyError):
            policy.validate_workflow(source)


@pytest.mark.parametrize("mutation", ["delete", "advisory", "skip", "mask", "aggregate"])
def test_required_execution_controls(tmp_path: Path, mutation: str) -> None:
    """Deleted gates, advisory conditions, and masked aggregate failures fail closed."""
    copy_policy(tmp_path)
    path = tmp_path / ".github/workflows/markdownlint.yml"
    text = path.read_text(encoding="utf-8")
    if mutation == "delete":
        text = text.replace("      - name: Check validation results", "      - name: Deleted check")
    elif mutation == "advisory":
        text = text.replace(
            "      - name: Check validation results",
            "      - name: Check validation results\n        continue-on-error: true",
        )
    elif mutation == "skip":
        text = text.replace("steps.lint-outer.outcome == 'failure'", "false")
    elif mutation == "mask":
        text = text.replace("run: npm run lint:md\n", "run: npm run lint:md || true\n")
    else:
        text = text.replace("          exit 1", "          exit 0")
    path.write_text(text, encoding="utf-8")
    with pytest.raises(policy.PolicyError, match="execution controls"):
        policy.validate_repository(tmp_path)


def test_misleading_annotation_uses_upstream_resolution() -> None:
    """A valid-looking release comment must match the independently resolved commit."""
    ref = "owner/action@" + "a" * 40
    policy.check_reference(ref, ref + " # v1.2.3", lambda _repo, _tag: "a" * 40)
    with pytest.raises(policy.PolicyError, match="Misleading"):
        policy.check_reference(ref, ref + " # v9.9.9", lambda _repo, _tag: "b" * 40)


def test_reusable_and_subpath_references() -> None:
    """The external grammar includes reusable workflows and action subdirectories."""
    for ref in ["owner/repo/.github/workflows/build.yml@", "owner/repo/action/path@"]:
        ref += "a" * 40
        policy.check_reference(ref, ref + " # v1.0.0")


@pytest.mark.parametrize("path", ["../escape.yml", "/outside", "C:/outside", "a/../b", "a\\b"])
def test_unsafe_input_paths(tmp_path: Path, path: str) -> None:
    """Reject lexical escapes independently of existence."""
    with pytest.raises(policy.PolicyError, match="Unsafe"):
        policy.read_text(tmp_path, path)


def test_bounds_and_yaml_shape(tmp_path: Path) -> None:
    """Input size, nesting, multi-document YAML, and custom tags fail safely."""
    path = tmp_path / "large.yml"
    path.write_bytes(b"x" * (policy.LIMIT + 1))
    with pytest.raises(policy.PolicyError, match="1 MiB"):
        policy.read_text(tmp_path, path.name)
    for text in [
        "x" * (policy.LIMIT + 1),
        "x: " + "[" * 65 + "]" * 65,
        "x: 1\n---\nx: 2",
        "x: !!python/object:builtins.object {}",
    ]:
        with pytest.raises(policy.PolicyError):
            policy.parse_yaml(text)
    assert "on" in policy.parse_yaml("on: [push]")


def test_symlink_is_rejected(tmp_path: Path) -> None:
    """A symlink must not provide a policy input even inside the repository."""
    source = tmp_path / "real.yml"
    source.write_text("name: test", encoding="utf-8")
    link = tmp_path / "link.yml"
    try:
        link.symlink_to(source)
    except OSError:
        pytest.skip("Host does not permit symlink creation")
    with pytest.raises(policy.PolicyError, match="Symlink"):
        policy.read_text(tmp_path, link.name)


def test_owned_scope_and_strict_opt_in(tmp_path: Path) -> None:
    """Adopter workflows are untouched and ignored until strict checking is requested."""
    copy_policy(tmp_path)
    local = tmp_path / ".github/workflows/adopter.yml"
    local.write_text("on: pull_request_target\njobs: {}\n", encoding="utf-8")
    before = local.read_bytes()
    assert policy.validate_repository(tmp_path) == 10
    with pytest.raises(policy.PolicyError, match="privileged"):
        policy.validate_repository(tmp_path, strict=True)
    assert local.read_bytes() == before


def test_contract_schema_and_inventory(tmp_path: Path) -> None:
    """Schema bounds policy paths and an independent inventory detects dropped owners."""
    contract = copy_policy(tmp_path)
    assert set(contract["workflows"]) == {
        path.relative_to(ROOT).as_posix() for path in (ROOT / ".github/workflows").glob("*.yml")
    }
    malformed = copy.deepcopy(contract)
    malformed["workflows"]["../escape.yml"] = malformed["workflows"].pop(
        next(iter(malformed["workflows"]))
    )
    (tmp_path / policy.CONTRACT).write_text(yaml.safe_dump(malformed), encoding="utf-8")
    assert policy.main(["--repo-root", str(tmp_path)]) == 1


def test_schema_cannot_trigger_external_resolution(tmp_path: Path) -> None:
    """Offline validation rejects remote and filesystem refs before schema evaluation."""
    copy_policy(tmp_path)
    schema = tmp_path / policy.SCHEMA
    original = schema.read_text(encoding="utf-8")
    for reference in [
        "https://example.invalid/schema.json",
        "file:///outside.json",
        "../outside.json",
    ]:
        schema.write_text(
            original.replace('"$ref": "#/$defs/workflow"', f'"$ref": "{reference}"'),
            encoding="utf-8",
        )
        with pytest.raises(policy.PolicyError, match="Only local"):
            policy.validate_repository(tmp_path)


def test_guard_removal_is_detected_by_negative_oracle(tmp_path: Path) -> None:
    """Removing the credential guard resurrects the unsafe fixture independently."""
    source_path = ROOT / ".github/scripts/validate_workflow_security.py"
    source = source_path.read_text(encoding="utf-8")
    guard = 'step.get("with", {}).get("persist-credentials") is not False'
    assert source.count(guard) == 1
    mutant_path = tmp_path / "mutant.py"
    mutant_path.write_text(source.replace(guard, "False"), encoding="utf-8")
    spec = importlib.util.spec_from_file_location("credential_guard_mutant", mutant_path)
    assert spec is not None and spec.loader is not None
    mutant = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mutant)
    bad = policy.read_text(ROOT, ".github/workflows/workflow-security.yml").replace(
        "persist-credentials: false", "persist-credentials: true"
    )
    with pytest.raises(policy.PolicyError, match="persist-credentials"):
        policy.validate_workflow(bad)
    assert mutant.validate_workflow(bad)


@pytest.mark.parametrize(
    ("before", "after"),
    [
        ("runs-on: ubuntu-latest", "runs-on: self-hosted"),
        ("runs-on: ubuntu-latest", "runs-on: ubuntu-latest\n    container: attacker/image"),
        ("actions/checkout@", "attacker/checkout@"),
        ("python-version: '3.13'", "python-version: '2.7'"),
    ],
)
def test_execution_surface_substitution_fails(tmp_path: Path, before: str, after: str) -> None:
    """Reviewed runner, action coordinate, and inputs cannot be replaced silently."""
    copy_policy(tmp_path)
    path = tmp_path / ".github/workflows/workflow-security.yml"
    text = path.read_text(encoding="utf-8")
    assert before in text
    path.write_text(text.replace(before, after), encoding="utf-8")
    with pytest.raises(policy.PolicyError, match="execution controls"):
        policy.validate_repository(tmp_path)


def test_comment_cannot_authorize_flow_style_executable_pin() -> None:
    """A descriptive comment on another line cannot annotate an executable scalar."""
    text = policy.read_text(ROOT, ".github/workflows/workflow-security.yml")
    checkout_line = next(line for line in text.splitlines() if "uses: actions/checkout@" in line)
    reference = checkout_line.strip().split()[1]
    annotation = checkout_line.split("#", 1)[1].strip()
    original = (
        "      - name: Checkout repository\n" + checkout_line + "\n"
        "        with:\n          persist-credentials: false"
    )
    changed = (
        f"      # uses: {reference} # {annotation}\n"
        f"      - {{name: Checkout repository, uses: {reference}, with: {{persist-credentials: false}}}}"
    )
    assert original in text
    with pytest.raises(policy.PolicyError, match="own literal"):
        policy.validate_workflow(text.replace(original, changed))


def test_configured_workflow_hook_native_failure(tmp_path: Path) -> None:
    """The actual configured hook propagates a real unsafe checkout's native exit."""
    copy_policy(tmp_path)
    config = policy.parse_yaml(policy.read_text(ROOT, ".pre-commit-config.yaml"))
    hook = next(
        h
        for repo in config["repos"]
        for h in repo["hooks"]
        if h["id"] == "validate-workflow-security"
    )
    command = shlex.split(hook["entry"])
    path = tmp_path / ".github/workflows/workflow-security.yml"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "persist-credentials: false", "persist-credentials: true"
        ),
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(ROOT / command[1]), *command[2:], "--repo-root", str(tmp_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "persist-credentials" in result.stderr
