"""Render an explicit local profile while preserving reviewed marker decisions."""

# ruff: noqa: E402

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

_SHARED_SCRIPTS = Path(__file__).resolve().parents[2] / ".github" / "scripts"
if str(_SHARED_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SHARED_SCRIPTS))

import instruction_contract_core as core
from template_sync_materialization_helpers import (
    TemplateSyncMaterializationError,
)

PROFILE_PATH = ".github/instruction-profile.yml"
TRUSTED_TOOL_ROOT = Path(__file__).resolve().parents[2]
SOURCE_FIELDS = (
    "local_overrides",
    "local_path_ownership",
    "protected_file_decisions",
    "instruction_contract_waivers",
    "protected_guide_contract_waivers",
)


def load_reviewed_schema(relative_path: str) -> dict[str, Any]:
    """Load schemas from the installed tool bundle, never selected source data."""
    return core.support.load_json_mapping(
        core.support.resolve_repo_path(TRUSTED_TOOL_ROOT, relative_path),
        TRUSTED_TOOL_ROOT,
        maximum_bytes=core.MAXIMUM_INPUT_BYTES,
    )


def load_existing_profile(target_root: Path) -> dict[str, Any]:
    """Read bounded local data against the installed tool's reviewed schema."""
    path = core.support.resolve_repo_path(target_root, PROFILE_PATH)
    document = core.support.load_yaml_mapping(
        path, target_root, maximum_bytes=core.MAXIMUM_INPUT_BYTES
    )
    schema = load_reviewed_schema("schemas/instruction-profile.schema.json")
    core.support.validate_schema(document, schema, path, target_root)
    return document


def render_instruction_profile(
    *,
    staging_root: Path,
    target_root: Path,
    marker_document: dict[str, Any],
) -> None:
    """Render a protected candidate; ordinary reconciliation still controls writes.

    Preserve source decisions as evidence, not authority. Convert only exact
    currently applicable failures; bind each declaration to the local file
    content so a later unrelated edit cannot reuse it silently.
    """
    marker = marker_document["template_sync"]
    modules = set(marker["included_modules"])
    destination = staging_root / PROFILE_PATH
    if "instruction-enforcement" not in modules:
        return
    if not destination.is_file():
        raise TemplateSyncMaterializationError("Selected enforcement profile candidate is missing.")
    previous = target_root / PROFILE_PATH
    if "template-sync-support" in modules:
        if previous.is_file():
            local = load_existing_profile(target_root)
            if local.get("mode") == "standalone" and (
                local.get("exceptions") or local.get("source_decisions")
            ):
                raise TemplateSyncMaterializationError(
                    "Reintroducing sync requires explicitly translating local declarations into "
                    "marker decisions and clearing the reviewed standalone declarations first."
                )
        document: dict[str, Any] = {"version": 1, "mode": "marker", "context": "downstream"}
    else:
        schema = load_reviewed_schema("schemas/instruction-profile.schema.json")
        catalog_path = core.support.resolve_repo_path(
            staging_root, ".github/instruction-contracts.yml"
        )
        catalog = core.support.load_yaml_mapping(
            catalog_path,
            staging_root,
            maximum_bytes=core.MAXIMUM_INPUT_BYTES,
        )
        core.support.validate_schema(
            catalog,
            load_reviewed_schema("schemas/instruction-contracts.schema.json"),
            catalog_path,
            staging_root,
        )
        contracts = core.parse_contracts(catalog, set(schema["$defs"]["moduleName"]["enum"]))
        active_paths = {item.path for item in contracts if set(item.requires_modules) <= modules}
        exceptions: list[dict[str, str]] = []
        source_decisions = {key: marker[key] for key in SOURCE_FIELDS if marker.get(key)}
        retired_exceptions: list[dict[str, str]] = []
        # Retain declarations from an existing local standalone profile. Protected
        # reconciliation refuses to replace locally changed profile content.
        if previous.is_file():
            local = load_existing_profile(target_root)
            if local.get("mode") == "standalone":
                source_decisions = {**local.get("source_decisions", {}), **source_decisions}
                retired_exceptions.extend(source_decisions.get("retired_exceptions", []))
                for declaration in local.get("exceptions", []):
                    if declaration["path"] in active_paths:
                        exceptions.append(declaration)
                    else:
                        retired_exceptions.append(declaration)
        for waiver in marker.get("instruction_contract_waivers", []):
            if waiver["path"] in active_paths:
                content_root = (
                    target_root if (target_root / waiver["path"]).exists() else staging_root
                )
                exceptions.append(
                    {**waiver, "content_sha256": core.file_digest(content_root, waiver["path"])}
                )
        for decision in marker.get("protected_file_decisions", []):
            if decision["decision"] == "REMOVE-LOCAL" and decision["path"] in active_paths:
                exceptions.append(
                    {
                        "path": decision["path"],
                        "anchor": "file:absent",
                        "content_sha256": "absent",
                        "reason": decision.get("reason") or "Reviewed marker removal declaration",
                        "authorization_basis": decision["authorization_basis"],
                    }
                )
        for content_root in (target_root, staging_root):
            report = core.validate_contracts(
                mode="migration",
                repo_root=content_root,
                contracts=contracts,
                included_modules=modules,
                protected_guide_section_obligations=core.parse_protected_guide_section_obligations(
                    catalog, set(schema["$defs"]["moduleName"]["enum"])
                ),
            )
            for stale in report.stale_protected_guide_sections:
                if content_root == staging_root and (target_root / stale.path).exists():
                    continue
                for waiver in marker.get("protected_guide_contract_waivers", []):
                    if waiver["path"] != stale.path or waiver["contract_key"] != stale.contract_key:
                        continue
                    if waiver.get("target_module") not in stale.target_modules:
                        continue
                    exceptions.append(
                        {
                            "path": stale.path,
                            "anchor": f"stale:{stale.contract_key}:{stale.anchor_type}:{stale.anchor}",
                            "content_sha256": core.file_digest(content_root, stale.path),
                            "reason": waiver["reason"],
                            "authorization_basis": waiver["authorization_basis"],
                        }
                    )
        unique: dict[tuple[str, str], dict[str, str]] = {}
        for exception in exceptions:
            key = (exception["path"], exception["anchor"])
            if key in unique and unique[key] != exception:
                raise TemplateSyncMaterializationError(
                    f"Conflicting migrated declarations require protected profile review: {key}"
                )
            unique[key] = exception
        document = {
            "version": 1,
            "mode": "standalone",
            "modules": sorted(modules),
            "exceptions": list(unique.values()),
            "source_decisions": source_decisions,
        }
        if retired_exceptions:
            source_decisions["retired_exceptions"] = retired_exceptions
    destination.write_text(
        yaml.safe_dump(document, sort_keys=False), encoding="utf-8", newline="\n"
    )
