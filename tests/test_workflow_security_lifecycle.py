"""Accept workflow governance through actual module adoption and synchronization."""

from __future__ import annotations

import importlib.util
import json
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from tests import test_materialize_downstream_adoption as lifecycle
from tests._pytest_compat import pytest
from tests.test_contract_wiring import assert_ci, assert_hook
from tests.test_workflow_security_contract import ROOT, policy

pytestmark = pytest.mark.upstream_template_only


@pytest.mark.parametrize(
    "modules",
    [
        ("github-actions",),
        ("baseline", "github-actions", "github-platform"),
        ("baseline", "github-actions", "markdown"),
        ("github-actions", "python"),
        ("github-actions", "powershell", "terraform"),
        ("baseline", "github-actions", "template-sync-support", "agent-instructions", "yaml"),
    ],
)
def test_retained_profiles_pass_without_unrelated_stacks(
    tmp_path: Path, modules: tuple[str, ...]
) -> None:
    """Selected language workflows and policy runtime survive real materialization."""
    target = lifecycle.materialize_module_fixture(tmp_path, modules, authorize_protected_files=True)
    assert policy.validate_repository(target) >= 1
    contract = policy.load_contract(target)
    _, _, mappings = lifecycle.materializer.load_validated_manifest_context(ROOT)
    expected = {
        path
        for path in policy.load_contract(ROOT)["workflows"]
        if lifecycle.materializer.selected_relation_for_path(path, mappings).is_retained_by(modules)
    }
    assert set(contract["workflows"]) == expected
    for module, filename in [
        ("markdown", "markdownlint"),
        ("python", "python-ci"),
        ("powershell", "powershell-ci"),
        ("terraform", "terraform-ci"),
    ]:
        assert (target / f".github/workflows/{filename}.yml").exists() == (module in modules)
    assert (target / "package.json").exists() == ("markdown" in modules)
    if "baseline" in modules:
        config = yaml.safe_load((target / ".pre-commit-config.yaml").read_text(encoding="utf-8"))
        assert_hook(config, "validate-workflow-security")
        data_ci = yaml.safe_load(
            (target / ".github/workflows/data-ci.yml").read_text(encoding="utf-8")
        )
        assert_ci(data_ci, "validate-workflow-security")
        if "template-sync-support" in modules:
            for mode in ("upstream", "downstream"):
                assert_hook(config, f"validate-instruction-contracts-{mode}")
                assert_ci(data_ci, f"validate-instruction-contracts-{mode}")
    if "github-platform" in modules:
        assert "github-actions" in lifecycle.dependabot_update_ecosystems(
            target / ".github/dependabot.yml"
        )


def snapshot(root: Path) -> dict[str, bytes]:
    """Capture downstream files without transient caches."""
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and ".git" not in p.parts
    }


def test_selected_validator_is_inert_and_trust_anchor_failure_is_detected(
    tmp_path: Path, monkeypatch: Any
) -> None:
    """Selected Python bytes never execute; restoring that trust boundary trips a marker."""
    from tests.test_workflow_security_contract import copy_policy

    source = tmp_path / "source"
    copy_policy(source)
    sentinel = source / "candidate-executed.txt"
    selected_script = source / ".github/scripts/validate_workflow_security.py"
    selected_script.parent.mkdir(parents=True, exist_ok=True)
    selected_script.write_text(
        "from pathlib import Path\n"
        "Path(__file__).parents[2].joinpath('candidate-executed.txt').write_text('executed')\n"
        "raise RuntimeError('candidate execution sentinel')\n",
        encoding="utf-8",
    )
    _, _, mappings = lifecycle.materializer.load_validated_manifest_context(ROOT)
    rendered = lifecycle.materializer.render_workflow_contract(
        source, mappings, ("github-actions",)
    )
    assert ".github/workflows/workflow-security.yml" in rendered
    assert not sentinel.exists()
    monkeypatch.setattr(lifecycle.materializer, "TRUSTED_TOOL_ROOT", source)
    with pytest.raises(RuntimeError, match="candidate execution sentinel"):
        lifecycle.materializer.render_workflow_contract(source, mappings, ("github-actions",))
    assert sentinel.read_text(encoding="utf-8") == "executed"


def test_installed_support_tools_can_add_actions_and_require_shared_helpers(tmp_path: Path) -> None:
    """A support-only installation carries its trusted executable and data closure."""
    target = lifecycle.materialize_module_fixture(
        tmp_path, ("template-sync-support",), authorize_protected_files=True
    )
    shared = [
        ".github/scripts/validate_workflow_security.py",
        ".github/scripts/replace-template-placeholders.py",
        ".github/template-placeholders.json",
        "schemas/template-placeholders.schema.json",
        policy.SCHEMA,
    ]
    for relative in shared:
        assert (target / relative).is_file(), relative
    assert not (target / policy.CONTRACT).exists()
    assert (target / policy.SCHEMA).is_file()
    modules = ("template-sync-support", "github-actions")
    write_decisions(
        target,
        modules,
        protected_file_decisions=lifecycle.protected_take_decisions_for_modules(modules),
        local_overrides=[
            {
                "path": path,
                "default_decision": "TAKE",
                "reason": "Fixture owner approves added Actions wiring.",
            }
            for path in ("TEMPLATE_UPDATE_PROCEDURE.md", "tests/test_contract_wiring.py")
        ],
    )
    command = [
        sys.executable,
        str(target / ".template-sync/scripts/materialize_downstream_adoption.py"),
        "--template-root",
        str(ROOT),
        "--target-root",
        str(target),
        "--decisions-file",
        "decisions.yml",
        "--repository",
        "octo/widget",
        "--security-contact",
        "security@example.com",
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    assert policy.validate_repository(target) == 1
    installed = subprocess.run(
        [sys.executable, str(target / shared[0]), "--repo-root", str(target)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert installed.returncode == 0, installed.stdout + installed.stderr
    for relative in [*shared[:2], policy.SCHEMA]:
        helper = target / relative
        original = helper.read_bytes()
        helper.unlink()
        try:
            failed = subprocess.run(command, capture_output=True, text=True, check=False)
            assert failed.returncode == 1, failed.stdout + failed.stderr
            assert "trusted helper is unavailable" in failed.stderr
            assert relative in failed.stderr
        finally:
            helper.write_bytes(original)


@pytest.mark.parametrize("candidate_schema", ["sentinel", "malformed", "missing"])
def test_candidate_workflow_schema_is_inert(tmp_path: Path, candidate_schema: str) -> None:
    """Selected schema bytes cannot change the running renderer's validation authority."""
    from tests.test_workflow_security_contract import copy_policy

    source = tmp_path / "source"
    copy_policy(source)
    _, _, mappings = lifecycle.materializer.load_validated_manifest_context(ROOT)
    expected = lifecycle.materializer.render_workflow_contract(
        source, mappings, ("github-actions",)
    )
    path = source / policy.SCHEMA
    if candidate_schema == "sentinel":
        schema = json.loads(path.read_text(encoding="utf-8"))
        schema["required"].append("candidate_schema_sentinel")
        path.write_text(json.dumps(schema), encoding="utf-8")
    elif candidate_schema == "malformed":
        path.write_text("not a schema", encoding="utf-8")
    else:
        path.unlink()
    assert (
        lifecycle.materializer.render_workflow_contract(source, mappings, ("github-actions",))
        == expected
    )


def test_installed_workflow_schema_is_authoritative(tmp_path: Path, monkeypatch: Any) -> None:
    """The same harmless schema sentinel is enforced when installed in the trusted bundle."""
    trusted = tmp_path / "trusted"
    for relative in [".github/scripts/validate_workflow_security.py", policy.SCHEMA]:
        path = trusted / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, path)
    path = trusted / policy.SCHEMA
    schema = json.loads(path.read_text(encoding="utf-8"))
    schema["required"].append("trusted_schema_sentinel")
    path.write_text(json.dumps(schema), encoding="utf-8")
    monkeypatch.setattr(lifecycle.materializer, "TRUSTED_TOOL_ROOT", trusted)
    _, _, mappings = lifecycle.materializer.load_validated_manifest_context(ROOT)
    with pytest.raises(
        lifecycle.materializer.MaterializationError, match="trusted_schema_sentinel"
    ):
        lifecycle.materializer.render_workflow_contract(ROOT, mappings, ("github-actions",))


@pytest.mark.parametrize("call", ["validate_repository", "load_contract"])
def test_workflow_schema_authority_guard_removal(
    tmp_path: Path, monkeypatch: Any, call: str
) -> None:
    """Removing either trusted-schema argument restores candidate control independently."""
    from tests.test_workflow_security_contract import copy_policy

    source = tmp_path / "source"
    copy_policy(source)
    schema_path = source / policy.SCHEMA
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    schema["required"].append("candidate_schema_sentinel")
    schema_path.write_text(json.dumps(schema), encoding="utf-8")
    _, _, mappings = lifecycle.materializer.load_validated_manifest_context(ROOT)
    assert lifecycle.materializer.render_workflow_contract(source, mappings, ("github-actions",))
    script = ROOT / ".template-sync/scripts/materialize_downstream_adoption.py"
    code = script.read_text(encoding="utf-8")
    before = f"validator.{call}(template_root, schema_root=TRUSTED_TOOL_ROOT)"
    assert code.count(before) == 1
    mutant_path = tmp_path / "materializer_schema_mutant.py"
    mutant_path.write_text(
        code.replace(before, f"validator.{call}(template_root)"), encoding="utf-8"
    )
    spec = importlib.util.spec_from_file_location("materializer_schema_mutant", mutant_path)
    assert spec is not None and spec.loader is not None
    mutant = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, mutant.__name__, mutant)
    spec.loader.exec_module(mutant)
    monkeypatch.setattr(mutant, "TRUSTED_TOOL_ROOT", ROOT)
    with pytest.raises(mutant.MaterializationError, match="candidate_schema_sentinel"):
        mutant.render_workflow_contract(source, mappings, ("github-actions",))


@pytest.mark.parametrize("mode", ["help", "materialize", "render", "eager-import-mutant"])
def test_installed_support_schema_dependency_is_lazy(tmp_path: Path, mode: str) -> None:
    """Help needs no schema runtime, while actual validation fails with a clear diagnostic."""
    target = lifecycle.materialize_module_fixture(
        tmp_path, ("template-sync-support",), authorize_protected_files=True
    )
    assert not (target / "pyproject.toml").exists()
    assert not (target / policy.CONTRACT).exists()
    script = target / ".template-sync/scripts/materialize_downstream_adoption.py"
    if mode == "eager-import-mutant":
        source = script.read_text(encoding="utf-8")
        anchor = "import yaml  # type: ignore[import-untyped]"
        assert source.count(anchor) == 1
        script.write_text(source.replace(anchor, "import jsonschema\n" + anchor), encoding="utf-8")
    runner = (
        "import runpy, sys\n"
        "from pathlib import Path\n"
        "sys.modules['jsonschema'] = None\n"
        "script = sys.argv.pop(1)\n"
    )
    if mode == "render":
        runner += (
            "namespace = runpy.run_path(script)\n"
            "try:\n"
            "    namespace['render_workflow_contract'](Path(sys.argv[1]), (), ('github-actions',))\n"
            "except namespace['MaterializationError'] as error:\n"
            "    print(error, file=sys.stderr)\n"
            "    sys.exit(1)\n"
        )
        arguments = [str(ROOT)]
    else:
        runner += "runpy.run_path(script, run_name='__main__')\n"
        arguments = ["--help"]
        if mode == "materialize":
            output = tmp_path / "output"
            output.mkdir()
            arguments = [
                "--template-root",
                str(ROOT),
                "--target-root",
                str(output),
                "--included-module",
                "template-sync-support",
            ]
    result = subprocess.run(
        [sys.executable, "-c", runner, str(script), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )
    if mode == "help":
        assert result.returncode == 0, result.stderr
        assert "--template-root" in result.stdout
    elif mode == "eager-import-mutant":
        assert result.returncode == 1
        assert "ModuleNotFoundError" in result.stderr
    else:
        assert result.returncode == 1
        expected = (
            "jsonschema is unavailable"
            if mode == "materialize"
            else "Workflow contract rendering requires jsonschema"
        )
        assert expected in result.stderr
        assert "Traceback" not in result.stderr


def write_decisions(target: Path, modules: tuple[str, ...], **fields: Any) -> None:
    """Record explicit fixture authorization using the normal marker schema."""
    reviewed = fields.pop("reviewed_commit", None)
    document = lifecycle.marker_document(list(modules), **fields)
    if reviewed:
        document["template_sync"]["last_reviewed_template_commit"] = reviewed
    lifecycle.write_yaml(target / "decisions.yml", document)


def test_existing_adoption_noop_customization_and_protection(tmp_path: Path) -> None:
    """First adoption, repeat sync, and protected conflicts preserve adopter content."""
    target = tmp_path / "existing"
    local = target / ".github/workflows/custom.yml"
    local.parent.mkdir(parents=True)
    local.write_text("# Adopter content\non: pull_request_target\njobs: {}\n", encoding="utf-8")
    modules = ("github-actions",)
    write_decisions(target, modules)
    blocked = lifecycle.run_materialize(ROOT, target, "--decisions-file", "decisions.yml")
    assert blocked.returncode == 2, blocked.stdout + blocked.stderr
    assert not (target / policy.CONTRACT).exists()
    write_decisions(
        target,
        modules,
        protected_file_decisions=lifecycle.protected_take_decisions_for_modules(modules),
    )
    adopted = lifecycle.run_materialize(ROOT, target, "--decisions-file", "decisions.yml")
    assert adopted.returncode == 0, adopted.stdout + adopted.stderr
    assert policy.validate_repository(target) == 1
    before = snapshot(target)
    repeated = lifecycle.run_materialize(ROOT, target, "--decisions-file", "decisions.yml")
    assert repeated.returncode == 0, repeated.stdout + repeated.stderr
    assert snapshot(target) == before
    contract = target / policy.CONTRACT
    contract.write_text(
        contract.read_text(encoding="utf-8") + "# Local policy customization\n", encoding="utf-8"
    )
    write_decisions(target, modules)
    tampered = contract.read_bytes()
    blocked = lifecycle.run_materialize(ROOT, target, "--decisions-file", "decisions.yml")
    assert blocked.returncode == 2, blocked.stdout + blocked.stderr
    assert contract.read_bytes() == tampered
    assert local.read_bytes() == before[local.relative_to(target).as_posix()]
    contract.unlink()
    assert policy.main(["--repo-root", str(target)]) == 1


@pytest.mark.parametrize("change", ["command", "job-name"])
def test_template_update_requires_review_and_preserves_adopter_workflow(
    tmp_path: Path, change: str
) -> None:
    """A reviewed template revision updates required behavior only with path decisions."""
    source = tmp_path / "source"
    source.mkdir()
    # Copy only manifest-owned files, excluding dependencies, scratch, and Git internals.
    _, _, mappings = lifecycle.materializer.load_validated_manifest_context(ROOT)
    paths, _ = lifecycle.materializer.iter_safe_repository_files(ROOT)
    for relative in paths:
        if lifecycle.materializer.selected_relation_for_path(relative, mappings) is not None:
            destination = source / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, destination)
    target = tmp_path / "target"
    target.mkdir()
    modules = ("github-actions", "template-sync-support")
    revision_a = lifecycle.commit_fixture_template(source)
    decisions = lifecycle.protected_take_decisions_for_modules(modules)
    write_decisions(target, modules, protected_file_decisions=decisions, reviewed_commit=revision_a)
    assert (
        lifecycle.run_materialize(source, target, "--decisions-file", "decisions.yml").returncode
        == 0
    )
    marker_path = target / ".template-sync/marker.yml"
    assert (
        yaml.safe_load(marker_path.read_text(encoding="utf-8"))["template_sync"][
            "last_reviewed_template_commit"
        ]
        == revision_a
    )
    local = target / ".github/workflows/local.yml"
    local_content = "on: push\npermissions: {}\njobs:\n  local:\n    permissions: {}\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo local\n"
    local.write_text(local_content, encoding="utf-8")
    workflow_path = ".github/workflows/workflow-security.yml"
    workflow = source / workflow_path
    original_control, updated_control = (
        (
            "run: python .github/scripts/validate_workflow_security.py",
            "run: python .github/scripts/validate_workflow_security.py --strict",
        )
        if change == "command"
        else ("  validate:\n", "  validate:\n    name: Reviewed workflow check\n")
    )
    workflow.write_text(
        workflow.read_text(encoding="utf-8").replace(original_control, updated_control),
        encoding="utf-8",
    )
    # Unreviewed source drift must not be blessed by rendering new fingerprints.
    rejected = lifecycle.run_materialize(source, target, "--decisions-file", "decisions.yml")
    assert rejected.returncode == 1, rejected.stdout + rejected.stderr
    contract = policy.load_contract(source)
    contract["workflows"][workflow_path] = policy.validate_workflow(
        workflow.read_text(encoding="utf-8")
    )
    (source / policy.CONTRACT).write_text(
        yaml.safe_dump(contract, sort_keys=False), encoding="utf-8"
    )
    lifecycle.run_git(source, "add", ".")
    lifecycle.run_git(
        source,
        "-c",
        "user.name=Template Tester",
        "-c",
        "user.email=template@example.com",
        "commit",
        "-q",
        "-m",
        "Reviewed workflow policy update",
    )
    revision_b = lifecycle.run_git(source, "rev-parse", "HEAD").stdout.strip()
    assert revision_b != revision_a
    write_decisions(target, modules, reviewed_commit=revision_b)
    blocked = lifecycle.run_materialize(source, target, "--decisions-file", "decisions.yml")
    assert blocked.returncode == 2, blocked.stdout + blocked.stderr
    assert (
        yaml.safe_load(marker_path.read_text(encoding="utf-8"))["template_sync"][
            "last_reviewed_template_commit"
        ]
        == revision_a
    )
    write_decisions(
        target,
        modules,
        protected_file_decisions=decisions,
        reviewed_commit=revision_b,
        local_overrides=[
            {
                "path": workflow_path,
                "default_decision": "TAKE",
                "reason": "Fixture owner reviewed the workflow control change.",
            }
        ],
    )
    updated = lifecycle.run_materialize(source, target, "--decisions-file", "decisions.yml")
    assert updated.returncode == 0, updated.stdout + updated.stderr
    assert updated_control in (target / workflow_path).read_text(encoding="utf-8")
    assert policy.validate_repository(target, strict=True) == 1
    installed = policy.parse_yaml((target / workflow_path).read_text(encoding="utf-8"))
    gate = installed["jobs"]["validate"]["steps"][-1]["run"]
    command = shlex.split(gate)
    executed = subprocess.run(
        [sys.executable, *command[1:]], cwd=target, capture_output=True, text=True, check=False
    )
    assert executed.returncode == 0, executed.stdout + executed.stderr
    assert local.read_text(encoding="utf-8") == local_content
    marker = yaml.safe_load(marker_path.read_text(encoding="utf-8"))["template_sync"]
    assert marker["last_reviewed_template_commit"] == revision_b
    assert any(item["path"] == policy.CONTRACT for item in marker["protected_file_decisions"])
    before = snapshot(target)
    repeated = lifecycle.run_materialize(source, target, "--decisions-file", "decisions.yml")
    assert repeated.returncode == 0, repeated.stdout + repeated.stderr
    assert snapshot(target) == before


def test_omission_and_reviewed_removal_leave_no_policy_orphans(tmp_path: Path) -> None:
    """Removal preserves old files pending explicit cleanup, then matches clean omission."""
    retained = ("baseline", "github-actions", "github-platform", "template-sync-support")
    omitted = ("baseline", "github-platform", "template-sync-support")
    (tmp_path / "retained").mkdir()
    (tmp_path / "omitted").mkdir()
    target = lifecycle.materialize_module_fixture(
        tmp_path / "retained", retained, authorize_protected_files=True
    )
    clean = lifecycle.materialize_module_fixture(
        tmp_path / "omitted", omitted, authorize_protected_files=True
    )
    _, _, mappings = lifecycle.materializer.load_validated_manifest_context(ROOT)
    original = snapshot(target)
    overrides = []
    removals = []
    for relative in original:
        relation = lifecycle.materializer.selected_relation_for_path(relative, mappings)
        if relation is None:
            continue
        if relation.is_retained_by(omitted):
            overrides.append(
                {
                    "path": relative,
                    "default_decision": "TAKE",
                    "reason": "Fixture owner approved module removal cleanup.",
                }
            )
        else:
            removals.append(relative)
    write_decisions(
        target,
        omitted,
        local_overrides=overrides,
        protected_file_decisions=lifecycle.protected_take_decisions_for_modules(omitted),
    )
    result = lifecycle.run_materialize(ROOT, target, "--decisions-file", "decisions.yml")
    assert result.returncode == 0, result.stdout + result.stderr
    assert (
        target / policy.CONTRACT
    ).exists(), "Materialization must not silently delete excluded files"
    lifecycle.run_git(target, "init", "-q")
    lifecycle.run_git(target, "add", ".")
    before_cleanup = lifecycle.run_downstream_adoption_validator(target)
    assert before_cleanup.returncode == 1, before_cleanup.stdout + before_cleanup.stderr
    assert policy.CONTRACT in before_cleanup.stdout
    for relative in removals:
        (target / relative).unlink()
    lifecycle.run_git(target, "add", "-A")
    lifecycle.run_git(clean, "init", "-q")
    lifecycle.run_git(clean, "add", ".")
    for tree in (target, clean):
        lifecycle.finish_review_profile_link_cleanup(tree, "neither")
    after_cleanup = lifecycle.run_downstream_adoption_validator(target)
    assert after_cleanup.returncode == 0, after_cleanup.stdout + after_cleanup.stderr
    ignored = {"decisions.yml", ".template-sync/marker.yml"}
    assert {p: b for p, b in snapshot(target).items() if p not in ignored} == {
        p: b for p, b in snapshot(clean).items() if p not in ignored
    }
    assert not (target / policy.CONTRACT).exists()
    assert (target / policy.SCHEMA).is_file()
    assert (target / ".github/scripts/validate_workflow_security.py").is_file()
    for relative in [
        ".github/workflows/workflow-security.yml",
        "docs/workflow-security.md",
        "schemas/examples/workflow-security-contract/valid/contract.yml",
        "schemas/examples/workflow-security-contract/invalid/contract.yml",
        "tests/test_workflow_security_contract.py",
        "tests/test_workflow_security_lifecycle.py",
        ".github/workflows/data-ci.yml",
    ]:
        assert not (target / relative).exists(), relative
    assert "validate-workflow-security" not in (target / ".pre-commit-config.yaml").read_text(
        encoding="utf-8"
    )
    assert "github-actions" not in lifecycle.dependabot_update_ecosystems(
        target / ".github/dependabot.yml"
    )
    assert "workflow-security" not in (target / "tests/test_contract_wiring.py").read_text(
        encoding="utf-8"
    )
