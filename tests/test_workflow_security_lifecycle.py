"""Accept workflow governance through actual module adoption and synchronization."""

from __future__ import annotations

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


def test_template_update_requires_review_and_preserves_adopter_workflow(tmp_path: Path) -> None:
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
    workflow.write_text(
        workflow.read_text(encoding="utf-8").replace(
            "run: python .github/scripts/validate_workflow_security.py",
            "run: python .github/scripts/validate_workflow_security.py --strict",
        ),
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
                "reason": "Fixture owner reviewed the stricter workflow.",
            }
        ],
    )
    updated = lifecycle.run_materialize(source, target, "--decisions-file", "decisions.yml")
    assert updated.returncode == 0, updated.stdout + updated.stderr
    assert " --strict" in (target / workflow_path).read_text(encoding="utf-8")
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
    assert not (target / policy.SCHEMA).exists()
    for relative in [
        ".github/scripts/validate_workflow_security.py",
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
