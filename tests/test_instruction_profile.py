"""Independent downstream deployment and failure controls for instruction profiles."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from tests._pytest_compat import pytest

pytestmark = pytest.mark.upstream_template_only

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = (
    ".github/scripts/instruction_contract_core.py",
    ".github/scripts/instruction_contract_support.py",
    ".github/scripts/validate_instruction_profile.py",
    "schemas/instruction-profile.schema.json",
    "schemas/instruction-contracts.schema.json",
)


def write(root: Path, path: str, value: str) -> None:
    """Write one bounded fixture input."""
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(value, encoding="utf-8", newline="\n")


def profile(root: Path, modules: list[str] | None = None) -> dict[str, Any]:
    """Create a standalone deployment containing no sync files or Python project."""
    for path in RUNTIME:
        write(root, path, (ROOT / path).read_text(encoding="utf-8"))
    document: dict[str, Any] = {
        "version": 1,
        "mode": "standalone",
        "modules": modules or ["agent-instructions", "instruction-enforcement", "baseline"],
        "exceptions": [],
    }
    write(root, ".github/instruction-profile.yml", yaml.safe_dump(document))
    write(
        root,
        ".github/instruction-contracts.yml",
        yaml.safe_dump(
            {
                "instruction_contracts": [
                    {
                        "path": "AGENTS.md",
                        "requires_modules": ["agent-instructions"],
                        "required_phrases": [
                            "Agents MUST validate.",
                            "Agents MUST preserve authority.",
                        ],
                    }
                ],
            }
        ),
    )
    write(root, "AGENTS.md", "Agents MUST validate.\nAgents MUST preserve authority.\n")
    return document


def run(root: Path) -> subprocess.CompletedProcess[str]:
    """Execute the deployed CLI so missing imports and native failures are visible."""
    return subprocess.run(
        [sys.executable, str(root / RUNTIME[2]), "--repo-root", str(root)],
        check=False,
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize(
    "excluded",
    [
        {"template-sync-support", "python"},
        {"template-sync-support", "python", "baseline", "azure-pipelines"},
        {"template-sync-support", "python", "baseline", "github-actions"},
        {"template-sync-support", "python", "powershell"},
        {"template-sync-support", "python", "terraform"},
        {
            "template-sync-support",
            "python",
            "powershell",
            "terraform",
            "agent-claude",
            "agent-cursor",
            "agent-gemini",
            "agent-hermes",
            "agent-copilot",
        },
    ],
)
def test_standalone_runs_after_sync_owned_files_are_physically_deleted(
    tmp_path: Path, excluded: set[str]
) -> None:
    """A real selected tree survives deletion of every support-owned path."""
    sys.path.insert(0, str(ROOT / ".template-sync/scripts"))
    import materialize_downstream_adoption as adoption
    from instruction_profile_migration import render_instruction_profile
    from template_sync_materialization_helpers import (
        iter_safe_repository_files,
        parse_manifest_mappings,
        selected_relation_for_path,
    )

    manifest = yaml.safe_load((ROOT / ".template-sync/manifest.yml").read_text(encoding="utf-8"))
    modules, mappings = parse_manifest_mappings(manifest)
    selected = set(modules) - excluded
    summary = adoption.Summary(
        retained_modules=sorted(selected),
        excluded_modules=["template-sync-support", "python"],
        default_adoption_mode="minimal-preservation",
    )
    adoption.write_staged_candidate(
        template_root=ROOT,
        staging_root=tmp_path,
        mappings=mappings,
        included_modules=selected,
        summary=summary,
    )
    render_instruction_profile(
        staging_root=tmp_path,
        target_root=tmp_path / "empty-target",
        marker_document={"template_sync": {"included_modules": sorted(selected)}},
    )
    # Independently copy and then physically remove all concrete support-owned
    # files, so success cannot be explained by a retained hidden dependency.
    support_paths: list[str] = []
    for relative in iter_safe_repository_files(ROOT)[0]:
        relation = selected_relation_for_path(relative, mappings)
        if (
            relation is not None
            and not relation.is_retained_by(selected)
            and relation.is_retained_by(selected | {"template-sync-support"})
        ):
            destination = tmp_path / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, destination)
            support_paths.append(relative)
    assert "schemas/template-sync-marker.schema.json" in support_paths
    assert "tests/test_validate_instruction_contracts.py" in support_paths
    for relative in support_paths:
        (tmp_path / relative).unlink()
    shutil.rmtree(tmp_path / ".template-sync")
    assert not (tmp_path / ".template-sync").exists()
    assert not any((tmp_path / relative).exists() for relative in support_paths)
    for path in tmp_path.rglob("*"):
        if path.is_file():
            relation = selected_relation_for_path(path.relative_to(tmp_path).as_posix(), mappings)
            assert relation is None or relation.is_retained_by(selected)
    result = run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert not (tmp_path / "pyproject.toml").exists()
    assert "Mode: standalone" in result.stdout
    agents_path = tmp_path / "AGENTS.md"
    if agents_path.exists():
        intact = agents_path.read_text(encoding="utf-8")
        anchor = "## PR Review Workflow (Codex-adapted)"
        assert intact.count(anchor) == 1
        agents_path.write_text(intact.replace(anchor, "## Removed protocol"), encoding="utf-8")
        weakened = run(tmp_path)
        assert weakened.returncode == 1, weakened.stdout + weakened.stderr
        assert anchor in weakened.stdout


@pytest.mark.parametrize(
    "bad",
    [
        "missing",
        "malformed",
        "no-modules",
        "unknown-module",
        "conflicting-modules",
        "conflicting-marker",
        "no-runner",
    ],
)
def test_invalid_applicability_is_native_failure(tmp_path: Path, bad: str) -> None:
    """No missing applicability input silently chooses all or no obligations."""
    document = profile(tmp_path)
    path = tmp_path / ".github/instruction-profile.yml"
    if bad == "missing":
        path.unlink()
    elif bad == "malformed":
        path.write_text("[", encoding="utf-8")
    else:
        if bad == "no-modules":
            del document["modules"]
        elif bad == "unknown-module":
            document["modules"].append("unknown")
        elif bad == "conflicting-modules":
            document["modules"].append("template-sync-support")
        elif bad == "conflicting-marker":
            write(tmp_path, ".template-sync/marker.yml", "invalid but conflicting\n")
        elif bad == "no-runner":
            document["modules"].remove("baseline")
        path.write_text(yaml.safe_dump(document), encoding="utf-8")
    result = run(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr


def test_marker_context_requires_missing_marker(tmp_path: Path) -> None:
    """An explicit downstream context never falls back to upstream-template."""
    profile(tmp_path)
    for source in (ROOT / ".template-sync/scripts").glob("*.py"):
        write(tmp_path, ".template-sync/scripts/" + source.name, source.read_text(encoding="utf-8"))
    write(
        tmp_path,
        ".github/instruction-profile.yml",
        "version: 1\nmode: marker\ncontext: downstream\n",
    )
    result = run(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "Marker is required" in result.stderr


@pytest.mark.parametrize("change", ["delete", "weaken", "unrelated", "unsafe", "oversized"])
def test_scoped_exception_cannot_hide_unrelated_failures(tmp_path: Path, change: str) -> None:
    """Fixed required clauses and a content-bound waiver have independent outcomes."""
    document = profile(tmp_path)
    text = "Agents MAY validate.\nAgents MUST preserve authority.\n"
    write(tmp_path, "AGENTS.md", text)
    assert run(tmp_path).returncode == 1
    document["exceptions"] = [
        {
            "path": "AGENTS.md",
            "anchor": "Agents MUST validate.",
            "content_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "reason": "Owner-reviewed fixture",
            "authorization_basis": "Fixture declaration",
        }
    ]
    write(tmp_path, ".github/instruction-profile.yml", yaml.safe_dump(document))
    accepted = run(tmp_path)
    assert accepted.returncode == 0, accepted.stdout + accepted.stderr
    assert "Applied local exception" in accepted.stdout
    assert "not independent proof" in accepted.stdout
    if change == "delete":
        (tmp_path / "AGENTS.md").unlink()
    elif change == "weaken":
        write(tmp_path, "AGENTS.md", text.replace("MUST preserve", "MAY preserve"))
    elif change == "unrelated":
        write(tmp_path, "AGENTS.md", text + "Unrelated new content.\n")
    elif change == "unsafe":
        document["exceptions"][0]["path"] = "../outside.md"
        write(tmp_path, ".github/instruction-profile.yml", yaml.safe_dump(document))
    else:
        write(tmp_path, ".github/instruction-profile.yml", " " * (1024 * 1024 + 1))
    assert run(tmp_path).returncode == 1


def test_content_scope_guard_removal_is_detected_by_fixed_oracle(tmp_path: Path) -> None:
    """A guard mutant must recreate false acceptance of an unrelated file edit."""
    document = profile(tmp_path)
    text = "Agents MAY validate.\nAgents MUST preserve authority.\n"
    document["exceptions"] = [
        {
            "path": "AGENTS.md",
            "anchor": "Agents MUST validate.",
            "content_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "reason": "Fixture",
            "authorization_basis": "Fixture declaration",
        }
    ]
    write(tmp_path, ".github/instruction-profile.yml", yaml.safe_dump(document))
    write(tmp_path, "AGENTS.md", text + "Unrelated content.\n")
    assert run(tmp_path).returncode == 1
    script = tmp_path / RUNTIME[2]
    source = script.read_text(encoding="utf-8")
    guard = 'declaration["content_sha256"] != file_digest(root, path)'
    assert source.count(guard) == 1
    script.write_text(source.replace(guard, "False"), encoding="utf-8")
    assert run(tmp_path).returncode == 0


def test_reviewed_seed_and_module_taxonomy_do_not_drift() -> None:
    """The seed is reviewed source data, never a standalone runtime dependency."""
    assert (ROOT / ".github/instruction-contracts.yml").read_bytes() == (
        ROOT / ".template-sync/instruction-contracts.yml"
    ).read_bytes()
    schema = json.loads((ROOT / "schemas/instruction-profile.schema.json").read_text())
    manifest = yaml.safe_load((ROOT / ".template-sync/manifest.yml").read_text(encoding="utf-8"))
    assert set(schema["$defs"]["moduleName"]["enum"]) == {
        item["name"] for item in manifest["template_manifest"]["modules"]
    }


def test_migration_preserves_scoped_declarations_and_repeated_noop(tmp_path: Path) -> None:
    """Migrated decisions bind local content and do not duplicate on repeat adoption."""
    sys.path.insert(0, str(ROOT / ".template-sync/scripts"))
    from instruction_profile_migration import render_instruction_profile

    target, stage = tmp_path / "target", tmp_path / "stage"
    document = profile(target)
    profile(stage)
    text = "Agents MAY validate.\nAgents MUST preserve authority.\n"
    write(target, "AGENTS.md", text)
    marker = {
        "template_sync": {
            "included_modules": document["modules"],
            "instruction_contract_waivers": [
                {
                    "path": "AGENTS.md",
                    "anchor": "Agents MUST validate.",
                    "reason": "Fixture",
                    "authorization_basis": "Reviewed fixture declaration",
                }
            ],
        }
    }
    render_instruction_profile(staging_root=stage, target_root=target, marker_document=marker)
    first = (stage / ".github/instruction-profile.yml").read_bytes()
    (target / ".github/instruction-profile.yml").write_bytes(first)
    assert run(target).returncode == 0
    render_instruction_profile(staging_root=stage, target_root=target, marker_document=marker)
    assert first == (stage / ".github/instruction-profile.yml").read_bytes()
    migrated = yaml.safe_load(first)
    assert len(migrated["exceptions"]) == 1
    assert (
        migrated["source_decisions"]["instruction_contract_waivers"]
        == marker["template_sync"]["instruction_contract_waivers"]
    )


def test_later_agent_removal_retires_exception_as_nonoperative_evidence(tmp_path: Path) -> None:
    """Reviewed module removal preserves history without retaining active waivers."""
    sys.path.insert(0, str(ROOT / ".template-sync/scripts"))
    from instruction_profile_migration import render_instruction_profile

    target, stage = tmp_path / "target", tmp_path / "stage"
    document = profile(target)
    profile(stage)
    text = "Agents MAY validate.\nAgents MUST preserve authority.\n"
    write(target, "AGENTS.md", text)
    document["exceptions"] = [
        {
            "path": "AGENTS.md",
            "anchor": "Agents MUST validate.",
            "content_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "reason": "Fixture",
            "authorization_basis": "Reviewed fixture declaration",
        }
    ]
    write(target, ".github/instruction-profile.yml", yaml.safe_dump(document))
    for root in (target, stage):
        catalog = yaml.safe_load((root / ".github/instruction-contracts.yml").read_text())
        catalog["instruction_contracts"][0]["requires_modules"].append("agent-codex")
        write(root, ".github/instruction-contracts.yml", yaml.safe_dump(catalog))
    render_instruction_profile(
        staging_root=stage,
        target_root=target,
        marker_document={"template_sync": {"included_modules": document["modules"]}},
    )
    result = yaml.safe_load((stage / ".github/instruction-profile.yml").read_text())
    assert result["exceptions"] == []
    assert result["source_decisions"]["retired_exceptions"] == document["exceptions"]
    assert run(stage).returncode == 0


@pytest.mark.parametrize(
    "modules",
    [
        {"instruction-enforcement", "baseline"},
        {"instruction-enforcement", "agent-instructions"},
        {"agent-codex", "baseline"},
    ],
)
def test_materializer_rejects_contradictory_selections(modules: set[str]) -> None:
    """Selection validity is enforced before any candidate file is written."""
    sys.path.insert(0, str(ROOT / ".template-sync/scripts"))
    from template_sync_materialization_helpers import validate_module_compatibility

    assert validate_module_compatibility(modules, ())


def test_legacy_agent_selection_requires_deliberate_migration(tmp_path: Path) -> None:
    """Old all-agent markers cannot silently delete existing agent entry points."""
    sys.path.insert(0, str(ROOT / ".template-sync/scripts"))
    from materialize_downstream_adoption import (
        MaterializationError,
        validate_agent_selection_migration,
    )
    from template_sync_materialization_helpers import parse_marker_decision_data

    write(tmp_path, "AGENTS.md", "Existing local instructions.\n")
    marker = parse_marker_decision_data(
        {"template_sync": {"included_modules": ["agent-instructions"]}}
    )
    with pytest.raises(MaterializationError, match="Legacy agent selection"):
        validate_agent_selection_migration(tmp_path, {"agent-instructions"}, marker)
    validate_agent_selection_migration(tmp_path, {"agent-instructions", "agent-codex"}, marker)


@pytest.mark.parametrize(
    "path",
    [
        ".github/instruction-contracts.yml",
        "schemas/instruction-contracts.schema.json",
        "schemas/instruction-profile.schema.json",
    ],
)
@pytest.mark.parametrize("change", ["missing", "malformed"])
def test_standalone_missing_or_malformed_companion_inputs_fail(
    tmp_path: Path, path: str, change: str
) -> None:
    """Every required local input fails visibly, independently of profile selection."""
    profile(tmp_path)
    if change == "missing":
        (tmp_path / path).unlink()
    else:
        (tmp_path / path).write_text("[", encoding="utf-8")
    result = run(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr


@pytest.mark.parametrize("modules", [set(), {"baseline"}, {"agent-instructions", "baseline"}])
def test_policy_only_selection_has_no_enforcement_runtime_or_routes(modules: set[str]) -> None:
    """Instruction retention never silently makes optional enforcement mandatory."""
    sys.path.insert(0, str(ROOT / ".template-sync/scripts"))
    from template_sync_materialization_helpers import (
        parse_manifest_mappings,
        selected_relation_for_path,
    )

    manifest = yaml.safe_load((ROOT / ".template-sync/manifest.yml").read_text(encoding="utf-8"))
    _known, mappings = parse_manifest_mappings(manifest)
    for path in (
        *RUNTIME,
        ".github/instruction-profile.yml",
        ".github/instruction-contracts.yml",
        ".github/workflows/instruction-contracts.yml",
        ".azuredevops/pipelines/instruction-contracts.yml",
    ):
        relation = selected_relation_for_path(path, mappings)
        assert relation is not None and not relation.is_retained_by(modules)


def test_current_decision_authorizes_legacy_agent_removal(tmp_path: Path) -> None:
    """An explicit current protected removal is accepted without inferring retention."""
    sys.path.insert(0, str(ROOT / ".template-sync/scripts"))
    from materialize_downstream_adoption import validate_agent_selection_migration
    from template_sync_materialization_helpers import parse_marker_decision_data

    write(tmp_path, "AGENTS.md", "Existing local instructions.\n")
    marker = parse_marker_decision_data(
        {
            "template_sync": {
                "included_modules": ["agent-instructions"],
                "protected_file_decisions": [
                    {
                        "path": "AGENTS.md",
                        "decision": "REMOVE-LOCAL",
                        "authorization_basis": "Fixture owner approved removing AGENTS.md",
                        "authorized_scope": "Remove AGENTS.md",
                        "reason": "Codex omitted",
                    }
                ],
            }
        }
    )
    validate_agent_selection_migration(tmp_path, {"agent-instructions"}, marker)


def run_migration_schema_control(
    stage: Path, target: Path, *, redirect_trust: bool = False
) -> subprocess.CompletedProcess[str]:
    """Run the real migration or an exact schema-provenance mutant natively."""
    source_path = ROOT / ".template-sync/scripts/instruction_profile_migration.py"
    source = source_path.read_text(encoding="utf-8")
    if redirect_trust:
        guard = "TRUSTED_TOOL_ROOT = Path(__file__).resolve().parents[2]"
        assert source.count(guard) == 1
        source = source.replace(guard, "TRUSTED_TOOL_ROOT = Path(sys.argv[1])")
    program = (
        "import sys\n"
        "from pathlib import Path\n"
        f"sys.path.insert(0, {str(ROOT / '.template-sync/scripts')!r})\n"
        f"namespace = {{'__file__': {str(source_path)!r}, '__name__': 'schema_control'}}\n"
        f"exec(compile({source!r}, {str(source_path)!r}, 'exec'), namespace)\n"
        "namespace['render_instruction_profile'](\n"
        "    staging_root=Path(sys.argv[1]), target_root=Path(sys.argv[2]),\n"
        "    marker_document={'template_sync': {'included_modules': [\n"
        "        'agent-instructions', 'instruction-enforcement', 'baseline']}})\n"
    )
    return subprocess.run(
        [sys.executable, "-c", program, str(stage), str(target)],
        check=False,
        capture_output=True,
        text=True,
    )


def test_migration_ignores_rejecting_candidate_schemas_and_detects_trust_mutant(
    tmp_path: Path,
) -> None:
    """Valid local data uses the installed tool schema even if candidates reject all."""
    stage, target = tmp_path / "stage", tmp_path / "target"
    profile(stage)
    profile(target)
    for path in RUNTIME[3:]:
        write(stage, path, json.dumps({"type": "object", "not": {}}))
    accepted = run_migration_schema_control(stage, target)
    assert accepted.returncode == 0, accepted.stdout + accepted.stderr
    mutant = run_migration_schema_control(stage, target, redirect_trust=True)
    assert mutant.returncode == 1, mutant.stdout + mutant.stderr
    assert "Schema validation failed" in mutant.stderr


@pytest.mark.parametrize("invalid_input", ["prior-profile", "candidate-catalog"])
def test_permissive_candidate_schema_cannot_excuse_invalid_data(
    tmp_path: Path, invalid_input: str
) -> None:
    """Fixed forbidden fields remain errors unless trusted schema provenance is removed."""
    stage, target = tmp_path / "stage", tmp_path / "target"
    profile(stage)
    profile(target)
    # Preserve the module definition needed by the renderer while removing all
    # candidate validation constraints. The reviewed installed schemas stay intact.
    reviewed = json.loads((ROOT / RUNTIME[3]).read_text(encoding="utf-8"))
    write(stage, RUNTIME[3], json.dumps({"$defs": reviewed["$defs"]}))
    write(stage, RUNTIME[4], "{}")
    root, path = (
        (target, ".github/instruction-profile.yml")
        if invalid_input == "prior-profile"
        else (stage, ".github/instruction-contracts.yml")
    )
    document = yaml.safe_load((root / path).read_text(encoding="utf-8"))
    document["unreviewed_schema_bypass"] = True
    write(root, path, yaml.safe_dump(document))
    rejected = run_migration_schema_control(stage, target)
    assert rejected.returncode == 1, rejected.stdout + rejected.stderr
    assert "unreviewed_schema_bypass" in rejected.stderr
    mutant = run_migration_schema_control(stage, target, redirect_trust=True)
    assert mutant.returncode == 0, mutant.stdout + mutant.stderr


def test_installed_support_only_tool_later_enables_standalone_enforcement(tmp_path: Path) -> None:
    """Exercise installed dependency closure through the native adoption pipeline."""
    sys.path.insert(0, str(ROOT / ".template-sync/scripts"))
    from template_sync_materialization_helpers import (
        is_protected_instruction_path,
        iter_safe_repository_files,
        parse_manifest_mappings,
        selected_relation_for_path,
    )

    target = tmp_path / "installed"
    target.mkdir()
    manifest = yaml.safe_load((ROOT / ".template-sync/manifest.yml").read_text(encoding="utf-8"))
    _known, mappings = parse_manifest_mappings(manifest)
    source_paths = iter_safe_repository_files(ROOT)[0]
    script_relative = ".template-sync/scripts/materialize_downstream_adoption.py"

    def adopt(
        script_root: Path, modules: set[str], *, source_root: Path = ROOT
    ) -> subprocess.CompletedProcess[str]:
        decisions = []
        for relative in source_paths:
            relation = selected_relation_for_path(relative, mappings)
            if (
                relation is not None
                and relation.is_retained_by(modules)
                and is_protected_instruction_path(relative)
            ):
                decisions.append(
                    {
                        "path": relative,
                        "decision": (
                            "SKIP" if source_root != ROOT and relative in RUNTIME[3:] else "TAKE"
                        ),
                        "adoption_mode": "minimal-preservation",
                        "authorization_basis": "Fixture owner authorizes this exact file",
                        "authorized_scope": relative,
                        "reason": "Fixture keeps reviewed schemas and selects retained files",
                    }
                )
        write(
            target,
            "decisions.yml",
            yaml.safe_dump(
                {
                    "template_sync": {
                        "source_repo": "https://github.com/franklesniak/copilot-repo-template",
                        "included_modules": sorted(modules),
                        "protected_file_decisions": decisions,
                    }
                }
            ),
        )
        return subprocess.run(
            [
                sys.executable,
                str(script_root / script_relative),
                "--template-root",
                str(source_root),
                "--target-root",
                str(target),
                "--decisions-file",
                "decisions.yml",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

    initial = adopt(ROOT, {"template-sync-support"})
    assert initial.returncode == 0, initial.stdout + initial.stderr
    assert not (target / RUNTIME[2]).exists()
    assert not (target / ".github/instruction-profile.yml").exists()
    assert all((target / path).is_file() for path in RUNTIME[3:])
    help_result = subprocess.run(
        [sys.executable, str(target / script_relative), "--help"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert help_result.returncode == 0, help_result.stdout + help_result.stderr
    assert "--included-modules" in help_result.stdout
    installed_migration = target / ".template-sync/scripts/instruction_profile_migration.py"
    intact_migration = installed_migration.read_bytes()
    installed_migration.write_bytes(
        intact_migration + b"\nfrom validate_instruction_profile import file_digest\n"
    )
    missing_cli = subprocess.run(
        [sys.executable, str(target / script_relative), "--help"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert missing_cli.returncode == 1, missing_cli.stdout + missing_cli.stderr
    assert "ModuleNotFoundError" in missing_cli.stderr
    installed_migration.write_bytes(intact_migration)
    selected = {"baseline", "agent-instructions", "instruction-enforcement"}
    installed_schema = target / RUNTIME[3]
    reviewed_schema = installed_schema.read_bytes()
    installed_schema.unlink()
    missing_schema = adopt(target, selected)
    assert missing_schema.returncode == 1, missing_schema.stdout + missing_schema.stderr
    installed_schema.write_bytes(reviewed_schema)
    enabled = adopt(target, selected)
    assert enabled.returncode == 0, enabled.stdout + enabled.stderr
    generated = yaml.safe_load((target / ".github/instruction-profile.yml").read_text())
    assert generated["mode"] == "standalone"
    assert set(generated["modules"]) == selected
    candidate = tmp_path / "candidate"
    for relative in source_paths:
        destination = candidate / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, destination)
    for relative in RUNTIME[3:]:
        write(candidate, relative, json.dumps({"type": "object", "not": {}}))
    # Explicit SKIP declarations preserve installed reviewed schemas while the
    # selected source carries rejecting candidates. Migration must not execute them.
    poisoned = adopt(target, selected, source_root=candidate)
    assert poisoned.returncode == 0, poisoned.stdout + poisoned.stderr
    assert all((target / path).read_bytes() == (ROOT / path).read_bytes() for path in RUNTIME[3:])
    before = {
        path.relative_to(target).as_posix(): path.read_bytes()
        for path in target.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    }
    repeated = adopt(target, selected, source_root=candidate)
    assert repeated.returncode == 0, repeated.stdout + repeated.stderr
    after = {
        path.relative_to(target).as_posix(): path.read_bytes()
        for path in target.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    }
    assert before == after
    # Materialization reports excluded surfaces; cleanup is an explicit owner
    # step. Remove support-only files after its installed tool has finished.
    for path in tuple(target.rglob("*")):
        if not path.is_file():
            continue
        relation = selected_relation_for_path(path.relative_to(target).as_posix(), mappings)
        if relation is not None and not relation.is_retained_by(selected):
            path.unlink()
    shutil.rmtree(target / ".template-sync")
    assert not (target / ".template-sync").exists()
    validated = run(target)
    assert validated.returncode == 0, validated.stdout + validated.stderr
