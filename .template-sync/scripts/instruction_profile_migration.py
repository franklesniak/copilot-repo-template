"""Render an explicit local profile while preserving reviewed marker decisions."""

# ruff: noqa: E402

from __future__ import annotations

import re
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


def catalog_path_applicability(
    contracts: tuple[core.InstructionContract, ...],
    section_obligations: tuple[core.ProtectedGuideSectionObligation, ...],
    reference_obligations: tuple[core.ProtectedGuideReferenceObligation, ...],
    modules: set[str],
) -> dict[str, bool]:
    """Classify known catalog paths, including obligation-only source files."""
    applicability: dict[str, bool] = {}
    for section_obligation in section_obligations:
        path = section_obligation.path
        applicability[path] = applicability.get(
            path, False
        ) or core.protected_guide_obligation_applies(section_obligation.target_modules, modules)
    for reference_obligation in reference_obligations:
        path = reference_obligation.path
        applicability[path] = applicability.get(
            path, False
        ) or core.protected_guide_obligation_applies(reference_obligation.target_modules, modules)
    # Core skips all obligations attached to an excluded instruction-contract path.
    for contract in contracts:
        applicability[contract.path] = set(contract.requires_modules) <= modules
    return applicability


def declaration_applies(
    declaration: dict[str, str],
    contracts: tuple[core.InstructionContract, ...],
    section_obligations: tuple[core.ProtectedGuideSectionObligation, ...],
    modules: set[str],
    reference_obligations: tuple[core.ProtectedGuideReferenceObligation, ...] = (),
) -> bool:
    """Retire known excluded obligations, while leaving unknown anchors to fail.

    Applicability comes from catalog scope, never from a failure disappearing
    after a content edit. Direct anchors may themselves resemble section IDs.
    """
    path, anchor = declaration["path"], declaration["anchor"]
    if anchor == "file:absent":
        return catalog_path_applicability(
            contracts, section_obligations, reference_obligations, modules
        ).get(path, True)
    for contract in contracts:
        if contract.path != path:
            continue
        if not set(contract.requires_modules) <= modules:
            return False
        if (
            anchor == "file:absent"
            or anchor in contract.required_headings
            or anchor in contract.required_phrases
        ):
            return True
        # Longest headings distinguish names containing colons from prefixes.
        for section in sorted(
            contract.required_sections, key=lambda item: len(item.heading), reverse=True
        ):
            prefix = f"section:{section.heading}"
            if anchor == prefix or (
                anchor.startswith(prefix + ":")
                and re.fullmatch(
                    r"(?:boundary|html-grammar|hard-break|paragraph|paragraphs|tables|blocks):[0-9a-f]{64}",
                    anchor[len(prefix) + 1 :],
                )
            ):
                return core.section_applies(section, modules)
    for obligation in section_obligations:
        if obligation.path != path:
            continue
        anchors = {
            *(f"stale:{obligation.key}:heading:{heading}" for heading in obligation.stale_headings),
            *(f"stale:{obligation.key}:phrase:{phrase}" for phrase in obligation.stale_phrases),
        }
        if anchor in anchors:
            return core.protected_guide_obligation_applies(obligation.target_modules, modules)
    for reference_obligation in reference_obligations:
        prefix = f"reference:{reference_obligation.key}:{reference_obligation.reference_kind}:"
        if reference_obligation.path != path or not anchor.startswith(prefix):
            continue
        target = anchor[len(prefix) :]
        matches = (
            core.resolve_relative_markdown_target(path, target) == reference_obligation.target_path
            if reference_obligation.reference_kind == "markdown-relative-link"
            else target in reference_obligation.tokens
        )
        if matches:
            return core.protected_guide_obligation_applies(
                reference_obligation.target_modules, modules
            )
    return True


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
    if "instruction-enforcement" not in modules:
        return
    # Temporary roots can use OS aliases such as macOS /var -> /private/var.
    # Normalize the caller's roots, while keeping candidate containment checks.
    staging_root = staging_root.resolve()
    target_root = target_root.resolve()
    destination = staging_root / PROFILE_PATH
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
        known_modules = set(schema["$defs"]["moduleName"]["enum"])
        contracts = core.parse_contracts(catalog, known_modules)
        section_obligations = core.parse_protected_guide_section_obligations(catalog, known_modules)
        reference_obligations = core.parse_protected_guide_reference_obligations(
            catalog, known_modules
        )
        guide_waivers = tuple(
            core.support.ProtectedGuideContractWaiver(
                path=waiver["path"],
                contract_key=waiver["contract_key"],
                target_path=waiver.get("target_path"),
                target_module=waiver.get("target_module"),
                linked_local_override_path=waiver.get("linked_local_override_path"),
                reason=waiver["reason"],
                authorization_basis=waiver["authorization_basis"],
            )
            for waiver in marker.get("protected_guide_contract_waivers", [])
        )
        path_applicability = catalog_path_applicability(
            contracts, section_obligations, reference_obligations, modules
        )
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
                exceptions.extend(local.get("exceptions", []))
        for waiver in marker.get("instruction_contract_waivers", []):
            content_root = target_root if (target_root / waiver["path"]).exists() else staging_root
            exceptions.append(
                {**waiver, "content_sha256": core.file_digest(content_root, waiver["path"])}
            )
        for decision in marker.get("protected_file_decisions", []):
            if decision["decision"] == "REMOVE-LOCAL" and path_applicability.get(
                decision["path"], False
            ):
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
                protected_guide_section_obligations=section_obligations,
                protected_guide_reference_obligations=reference_obligations,
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
            for reference in report.stale_protected_guide_references:
                if content_root == staging_root and (target_root / reference.path).exists():
                    continue
                waiver = core.find_protected_guide_waiver(
                    guide_waivers,
                    path=reference.path,
                    contract_key=reference.contract_key,
                    target_modules=reference.target_modules,
                    target_path=reference.target_path,
                )
                if waiver is not None:
                    exceptions.append(
                        {
                            "path": reference.path,
                            "anchor": f"reference:{reference.contract_key}:{reference.reference_kind}:{reference.target}",
                            "content_sha256": core.file_digest(content_root, reference.path),
                            "reason": waiver.reason,
                            "authorization_basis": waiver.authorization_basis,
                        }
                    )
        unique: dict[tuple[str, str], dict[str, str]] = {}
        for exception in exceptions:
            if not declaration_applies(
                exception, contracts, section_obligations, modules, reference_obligations
            ):
                if exception not in retired_exceptions:
                    retired_exceptions.append(exception)
                continue
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
    core.support.validate_schema(
        document,
        load_reviewed_schema("schemas/instruction-profile.schema.json"),
        destination,
        staging_root,
    )
    rendered = yaml.safe_dump(document, sort_keys=False)
    if len(rendered.encode("utf-8")) > core.MAXIMUM_INPUT_BYTES:
        raise TemplateSyncMaterializationError(
            f"Rendered {PROFILE_PATH} exceeds the {core.MAXIMUM_INPUT_BYTES}-byte input limit."
        )
    destination.write_text(rendered, encoding="utf-8", newline="\n")
