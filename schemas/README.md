<!-- markdownlint-disable MD013 -->

# Schemas

## Metadata

- **Status:** Active
- **Owner:** Repository Maintainers
- **Last Updated:** 2026-09-18
- **Scope:** Conventions for JSON Schemas that describe load-bearing JSON and YAML files in this repository, the baseline placeholder manifest schema, the template sync manifest, marker, instruction-contract, and first-adoption quality suppression schemas, plus a clearly removable worked example (`example-config.schema.json` with valid and invalid example data) wired into pre-commit and data CI to demonstrate the schema-validation pipeline end to end.
- **Related:** [Repository Copilot Instructions](../.github/copilot-instructions.md), [Template Design Decisions — Schema Location at Repository Root](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/.github/TEMPLATE_DESIGN_DECISIONS.md#design-decision-schema-location-at-repository-root), [Template Design Decisions — Schema Validation Tiers](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/.github/TEMPLATE_DESIGN_DECISIONS.md#design-decision-schema-validation-tiers), [Template Design Decisions — Built-in Schema Validation for Real Load-Bearing Configuration Files](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/.github/TEMPLATE_DESIGN_DECISIONS.md#design-decision-built-in-schema-validation-for-real-load-bearing-configuration-files), [Template Design Decisions — `additionalProperties` Policy](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/.github/TEMPLATE_DESIGN_DECISIONS.md#design-decision-additionalproperties-policy), [Template Design Decisions — Testing Beyond Linting for JSON/YAML](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/.github/TEMPLATE_DESIGN_DECISIONS.md#design-decision-testing-beyond-linting-for-jsonyaml)
<!-- template-sync: begin json-reference-only -->
- **Related JSON guidance:** [JSON Authoring Standards](../.github/instructions/json.instructions.md)
<!-- template-sync: end json-reference-only -->
<!-- template-sync: begin yaml-reference-only -->
- **Related YAML guidance:** [YAML Authoring Standards](../.github/instructions/yaml.instructions.md)
<!-- template-sync: end yaml-reference-only -->

## Purpose

This directory contains JSON Schemas for load-bearing JSON and YAML files in this repository. A "load-bearing" file is one whose shape is depended on by build, deploy, runtime, release automation, or downstream consumers, such that a malformed value would cause incorrect behavior.

Schemas live at the repository root (under `schemas/`, not `.github/schemas/`) so they are discoverable to IDEs, schema validators, and downstream consumers, and so projects that do not use schema-backed data files can opt out by deleting this directory.

## Template Portability

This template provides `schemas/` as a convention for repositories that adopt schema-backed JSON or YAML contracts. Downstream repositories MAY delete `schemas/` (including this `README.md`) if they do not use schema-backed data files or the template sync support scripts.

## Repository-Specific Validation Inventory

The inventory below describes the upstream template. Downstream pre-commit configuration and its runner requirement are retained only with `baseline`; data CI also requires the matching host module. A data-module selection without baseline retains content but does not supply this pre-commit enforcement. Upstream workflow links remain useful when the downstream workflow is absent.

The portable JSON and YAML style guides describe validation rules generically so they can be reused by repositories with different schema, test, and CI layouts. This README is the repository-specific home for this template's concrete schema inventory, worked-example fixtures, built-in schema validation choices, regression tests, and data-file CI wiring.

<!-- template-sync: begin baseline-reference-only -->
The authoritative active hook list remains [`.pre-commit-config.yaml`](../.pre-commit-config.yaml). When GitHub Actions is also retained, the dedicated data-file workflow, [`.github/workflows/data-ci.yml`](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/.github/workflows/data-ci.yml), re-runs the retained data-file hooks so branch protection can require JSON, YAML, GitHub Actions, and schema validation independently of language-specific CI jobs.
<!-- template-sync: end baseline-reference-only -->

## Conventions

### Draft

- Schemas SHOULD use [JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12/schema) unless a specific consumer requires another draft (for example, an OpenAPI version pinned to Draft-07).
- The chosen draft SHOULD be stated in the schema's `$schema` field, and any deviation from Draft 2020-12 SHOULD be called out in the schema's `description` or in this `README.md`.

### File Naming

- Schema files SHOULD use the suffix `.schema.json` (for example, `schemas/feature-flags.schema.json`).
- Filenames SHOULD use lowercase `kebab-case`.

### Required Schema Metadata

Every schema SHOULD include the following top-level keywords:

- `$schema` — the JSON Schema draft URI.
- `$id` — a stable, absolute URI that identifies the schema. See [`$id` URL Convention](#id-url-convention) for the two URL forms used in this directory.
- `title` — a short, human-readable name for the contract.
- `description` — a concise explanation of what the schema describes and which files it applies to.

### `$id` URL Convention

Two `$id` URL forms are used in this directory, depending on whether the schema is a worked example or a production contract. The distinction is intentional and is documented here so that future contributors do not "normalize" the two forms to a single value.

- **Production schemas** (such as [`template-sync-manifest.schema.json`](./template-sync-manifest.schema.json) and [`template-sync-marker.schema.json`](./template-sync-marker.schema.json)) use a stable, real URL that resolves to the schema's canonical content. Use the `raw.githubusercontent.com` form anchored at the default branch, for example, `https://raw.githubusercontent.com/franklesniak/copilot-repo-template/HEAD/schemas/<schema-name>.schema.json`. JSON Schema treats `$id` primarily as an identifier rather than a fetch URI, but a URL that actually dereferences to the schema JSON lets tooling that does try to follow `$id` succeed and avoids 404s when a reader clicks the URL. `HEAD` tracks the repository's default branch, so the identifier remains stable across default-branch renames.
- **Worked example schemas** (such as [`example-config.schema.json`](./example-config.schema.json)) use the reserved `https://example.invalid/schemas/<schema-name>.schema.json` form. Per [RFC 6761](https://www.rfc-editor.org/rfc/rfc6761.html#section-6.4), the `.invalid` TLD is reserved for non-resolving identifiers, which appropriately signals that the schema is template starter content rather than a production contract and reinforces that downstream consumers SHOULD replace or remove it (see the [Downstream Removal Checklist](#downstream-removal-checklist)).

Downstream repositories that adopt this template **MAY** retain a production schema's `$id` pointing to the upstream URL (treating it as a "this is the contract version I am using" indicator), **MAY** rewrite it to their own canonical URL when forking or customizing the schema, or **MAY** remove the schema entirely if they do not use the corresponding template feature (such as the template sync procedure).

### Object Schemas

Schemas whose root type is `object` SHOULD define:

- `type: "object"`
- `required` — the list of properties that MUST be present.
- `properties` — the typed shape of each known property.

### Open vs. Closed Contracts

- Project-owned closed contracts SHOULD set `"additionalProperties": false` so that unknown keys are caught early.
- Ecosystem-mirroring schemas (schemas that describe an external format the project does not own, for example a third-party config) MAY leave additional properties open and SHOULD document why in the schema's `description` or in this `README.md`.

## Validation

This template ships a [Worked Example](#worked-example) and production schemas for the [Template Sync Manifest](#template-sync-manifest-schema), [Template Sync Marker](#template-sync-marker-schema), [Template Sync Instruction Contracts](#template-sync-instruction-contracts-schema), and [First-Adoption Quality Suppressions](#first-adoption-quality-suppressions-schema). Downstream repositories that do not use general schema-backed data files SHOULD remove the worked example using the [Downstream Removal Checklist](#downstream-removal-checklist). Repositories that keep `template-sync-support` SHOULD retain the template-sync production schemas and their template-sync example fixtures even when they remove the general `schema` module. See the JSON authoring standards for the schema-validation policy and tier guidance when that guide is retained.

<!-- template-sync: begin baseline-reference-only -->
Schema-backed files are validated by pre-commit and, when the matching host module is retained, data CI. Baseline also supplies the [Template Placeholder Manifest Schema](#template-placeholder-manifest-schema). Repositories that keep the baseline placeholder helper SHOULD retain the placeholder manifest schema, manifest file, and placeholder-specific invalid-example validator.
<!-- template-sync: end baseline-reference-only -->

### Schema Categories

This repository distinguishes two schema categories. The distinction matters for where schemas live, how they are tested, and how they are wired into pre-commit and CI.

1. **Project-owned schemas.**
   - Stored under `schemas/` in this repository.
   - MAY include valid and invalid example fixtures under `schemas/examples/<schema-name>/{valid,invalid}/`.
   - Tested by [`tests/test_schema_examples.py`](../tests/test_schema_examples.py), which auto-discovers schema/example pairs and asserts that valid examples pass and invalid examples fail.
   - When pre-commit is retained, wired into it by adding a `check-jsonschema` hook that points at the schema with `--schemafile schemas/<name>.schema.json` and an anchored `files:` pattern matching the file family the schema covers.
   - The [Worked Example](#worked-example) below is the canonical illustration of the general `schema` module. The [Template Sync Manifest Schema](#template-sync-manifest-schema), [Template Sync Marker Schema](#template-sync-marker-schema), [Template Sync Instruction Contracts Schema](#template-sync-instruction-contracts-schema), and [First-Adoption Quality Suppressions Schema](#first-adoption-quality-suppressions-schema) are production schema-backed contracts owned by `template-sync-support` because the support scripts load them at runtime or validate downstream-created retained state.

2. **External built-in schemas.**
   - Referenced through `check-jsonschema --builtin-schema vendor.<name>` against schemas that ship inside the pinned `check-jsonschema` release.
   - **Not vendored** into this repository. Schema content tracks `check-jsonschema` upstream releases. When baseline and GitHub platform support are retained, Dependabot's `pre-commit` ecosystem updates the hook dependency.
   - Used for selected real, load-bearing repository configuration files where the external schema is mature and validation is low-noise.
   - See the [Built-in Schema Validation for Real Load-Bearing Configuration Files](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/.github/TEMPLATE_DESIGN_DECISIONS.md#design-decision-built-in-schema-validation-for-real-load-bearing-configuration-files) ADR for the policy, the full list of selected files, and the explicit "Evaluated but deferred" negative-space record.

The two categories are complementary. A downstream repository MAY use either, both, or neither.

<!-- template-sync: begin github-platform-reference-only -->

### Real Repository Configuration Files Validated Through Built-in Schemas

When baseline is retained, the following real, load-bearing repository configuration files are validated by default through `check-jsonschema --builtin-schema ...` hooks in `.pre-commit-config.yaml`:

| File | Built-in schema identifier | Regression coverage |
| --- | --- | --- |
| [`.github/dependabot.yml`](../.github/dependabot.yml) | `vendor.dependabot` | GitHub-platform-only validation; when retained, the `validate-dependabot-config-valid-examples` hook validates the documented `tests/fixtures/dependabot/auto-assignment.yml` fixture at the same pinned `rev`, and `tests/test_dependabot_schema.py` re-validates it under pytest |

If a downstream repository deletes one of these files, it **MUST** also remove the corresponding `check-jsonschema` hook (and any matching `data-ci.yml` step) per the [downstream removal guidance in the ADR](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/.github/TEMPLATE_DESIGN_DECISIONS.md#design-decision-built-in-schema-validation-for-real-load-bearing-configuration-files). Azure DevOps-only adoptions do not retain `.github/dependabot.yml`, `validate-dependabot-config`, or `tests/test_dependabot_schema.py`; Azure DevOps security scanning and routine dependency version updates are documented as service-side/adopter-selected choices rather than as Dependabot schema validation.

<!-- template-sync: end github-platform-reference-only -->

<!-- template-sync: begin azure-devops-guide-reference-only -->
For Azure DevOps-only adoptions, see the [Azure DevOps Services Support Guide](../docs/azure-devops-support.md) for host-specific service boundaries.
<!-- template-sync: end azure-devops-guide-reference-only -->

### Project-Owned Schema-Backed Files

The following project-owned file families have retained schema contracts:

| File | Schema |
| --- | --- |
| [`.template-sync/manifest.yml`](../.template-sync/manifest.yml) | [`template-sync-manifest.schema.json`](./template-sync-manifest.schema.json) |
| `.template-sync/marker.yml` when present | [`template-sync-marker.schema.json`](./template-sync-marker.schema.json) |
| [`.template-sync/instruction-contracts.yml`](../.template-sync/instruction-contracts.yml) | [`template-sync-instruction-contracts.schema.json`](./template-sync-instruction-contracts.schema.json) |
| `.template-sync/first-adoption/quality-suppressions.json` when present | [`first-adoption-quality-suppressions.schema.json`](./first-adoption-quality-suppressions.schema.json) |

<!-- template-sync: begin baseline-reference-only -->
Baseline additionally supplies [`.github/template-placeholders.json`](../.github/template-placeholders.json), governed by [`template-placeholders.schema.json`](./template-placeholders.schema.json). These file families are validated by default through `check-jsonschema --schemafile ...` hooks in [`.pre-commit-config.yaml`](../.pre-commit-config.yaml).
<!-- template-sync: end baseline-reference-only -->

### File-Family Hooks

When real schemas and a pre-commit toolchain are retained, validation SHOULD be wired in per **file family**:

- Add **one `check-jsonschema` hook per real schema-backed file family**, scoped to the files that family covers (for example, `^config/.*\.json$`).
- **Do not add placeholder hooks** for schemas that do not yet exist. An empty or speculative hook adds noise without enforcing anything.
- **Do not validate every JSON or YAML file by default.** Generic `check-jsonschema --check-metaschema` style sweeps are out of scope; the retained syntax validators cover syntax. Schema validation is a contract check for specific file families, not a global sweep.

Example hook pattern (illustrative — do not copy verbatim without re-verifying the version):

```yaml
- repo: https://github.com/python-jsonschema/check-jsonschema
  rev: 0.33.3
  hooks:
    - id: check-jsonschema
      name: Validate project JSON config
      files: ^config/.*\.json$
      args:
        - --schemafile
        - schemas/project-config.schema.json
```

> **Version pinning.** Implementers MUST verify and pin a current upstream version of `check-jsonschema` when enabling the hook, rather than copying the example `rev:` value above. Look up the latest tagged release at the upstream repository ([python-jsonschema/check-jsonschema](https://github.com/python-jsonschema/check-jsonschema)) before adoption, and update the pin via your normal dependency-update process.

## Examples

Example pairs (a sample data file plus the schema it validates against) MAY live under:

```text
schemas/examples/
```

Examples MUST NOT contain real secrets or credentials. Example values MUST be obviously fake (for example, `"REPLACE_ME"`, `"example-token-not-real"`).

### Testing Valid Examples

Valid examples can be validated directly with `check-jsonschema` from the command line or from a pre-commit hook:

```bash
check-jsonschema \
  --schemafile schemas/project-config.schema.json \
  schemas/examples/project-config/valid/minimal.json
```

A valid example MUST produce exit code `0`. A non-zero exit indicates either a broken example or a schema regression and MUST be fixed before merging.

### Testing Invalid Examples

Invalid examples (intentionally malformed fixtures used to prove the schema rejects bad input) MUST NOT be wired directly into a normal pre-commit hook, because `check-jsonschema` would treat their failure as a hook failure.

Instead, invalid examples SHOULD be exercised by a test or script that asserts validation **fails**. For example, using `pytest` and a subprocess invocation:

```python
import shutil
import subprocess
import sys
from importlib.util import find_spec

import pytest


def check_jsonschema_command():
    executable = shutil.which("check-jsonschema")
    if executable is not None:
        return [executable]
    if find_spec("check_jsonschema") is not None:
        return [sys.executable, "-m", "check_jsonschema"]
    return None


CHECK_JSONSCHEMA_COMMAND = check_jsonschema_command()


@pytest.mark.skipif(
    CHECK_JSONSCHEMA_COMMAND is None,
    reason="check-jsonschema is not installed in this environment",
)
def test_invalid_example_is_rejected():
    assert CHECK_JSONSCHEMA_COMMAND is not None
    result = subprocess.run(
        [
            *CHECK_JSONSCHEMA_COMMAND,
            "--schemafile",
            "schemas/project-config.schema.json",
            "schemas/examples/project-config/invalid/missing-required.json",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0, (
        "Invalid example was unexpectedly accepted by the schema; "
        "either the schema is too permissive or the example is no longer invalid."
    )
```

The command resolver prefers the `check-jsonschema` console script when it is on `PATH`, falls back to `python -m check_jsonschema` when the package is importable in the pytest environment, and skips only when neither invocation is available. The same shape applies in PowerShell, Bash, or any CI step: invoke the validator on the invalid fixture and assert a non-zero exit.

The upstream template's Python starter version of this pattern lives at [`templates/python/tests/test_schema_examples.py`](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/templates/python/tests/test_schema_examples.py); the active, canonical version that this repository runs in CI lives at [`tests/test_schema_examples.py`](../tests/test_schema_examples.py). Both auto-discover schema/example pairs under `schemas/`, prefer the console script, and fall back to `python -m check_jsonschema` when the package is importable. The starter retains a `skipif` guard so it remains safe to copy into downstream projects that have not yet added `check-jsonschema` to their dev/test dependencies.

## Worked Example

This template ships a worked example with direct tests and optional pre-commit integration. The worked example is **template starter content**, not a production contract for downstream repositories.

- Schema: [`example-config.schema.json`](./example-config.schema.json)
- Valid example data: [`examples/example-config/valid/`](./examples/example-config/valid/)
  - [`minimal.json`](./examples/example-config/valid/minimal.json) — only the required properties.
  - [`full.json`](./examples/example-config/valid/full.json) — every optional property exercised.
- Invalid example data: [`examples/example-config/invalid/`](./examples/example-config/invalid/)
  - [`missing-required.json`](./examples/example-config/invalid/missing-required.json) — required property omitted.
  - [`wrong-type.json`](./examples/example-config/invalid/wrong-type.json) — required property has the wrong JSON type.
  - [`extra-property.json`](./examples/example-config/invalid/extra-property.json) — unknown property rejected by `additionalProperties: false`.

How the worked example is validated:

<!-- template-sync: begin baseline-reference-only -->
- The `valid/` example data files are validated by the `Validate example-config valid examples` `check-jsonschema` hook in [`.pre-commit-config.yaml`](../.pre-commit-config.yaml) and by [`.github/workflows/data-ci.yml`](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/.github/workflows/data-ci.yml).
- The schema itself is self-validated against its declared JSON Schema Draft 2020-12 metaschema by the `Self-validate example-config schema` `check-metaschema` hook in [`.pre-commit-config.yaml`](../.pre-commit-config.yaml), also executed by [`.github/workflows/data-ci.yml`](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/.github/workflows/data-ci.yml).
<!-- template-sync: end baseline-reference-only -->
- The `invalid/` example data files are exercised by [`tests/test_schema_examples.py`](../tests/test_schema_examples.py), which uses `check-jsonschema` to assert that each invalid example causes a non-zero exit code (and that each valid example exits cleanly). An upstream Python starter version of this pattern, with the same discovery and assertion logic but with project-root resolution suitable for downstream repositories, is also available at [`templates/python/tests/test_schema_examples.py`](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/templates/python/tests/test_schema_examples.py).
- Invalid example data files MUST NOT be wired into a normal pre-commit hook because `check-jsonschema` would treat their (expected) failure as a hook failure.

<!-- template-sync: begin baseline-reference-only -->

## Template Placeholder Manifest Schema

[`template-placeholders.schema.json`](./template-placeholders.schema.json) defines the baseline JSON manifest consumed by [`.github/scripts/replace-template-placeholders.py`](../.github/scripts/replace-template-placeholders.py). The manifest is the source of truth for placeholder tokens, replacement sources, approved path scopes, scan finding kinds, finding contexts, and failure dispositions. It does not declare module ownership; the placeholder helper resolves path ownership through [`.template-sync/manifest.yml`](../.template-sync/manifest.yml) when classified scans are requested.

How the placeholder manifest contract is validated:

- The live manifest file is validated by the `Validate template placeholder manifest` `check-jsonschema` hook in [`.pre-commit-config.yaml`](../.pre-commit-config.yaml) and by [`.github/workflows/data-ci.yml`](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/.github/workflows/data-ci.yml).
- Valid placeholder manifest fixtures under [`examples/template-placeholders/valid/`](./examples/template-placeholders/valid/) are validated by the `Validate template placeholder valid examples` hook and by the data-file CI workflow.
- Invalid placeholder manifest fixtures under [`examples/template-placeholders/invalid/`](./examples/template-placeholders/invalid/) are exercised by [`.github/scripts/validate-placeholder-schema-examples.py`](../.github/scripts/validate-placeholder-schema-examples.py), which asserts they are rejected. That retained hook declares its own `jsonschema` dependency in pre-commit.
- The schema itself is self-validated against its declared JSON Schema Draft 2020-12 metaschema by the `Self-validate template placeholder schema` hook.

<!-- template-sync: end baseline-reference-only -->

## Template Sync Manifest Schema

[`template-sync-manifest.schema.json`](./template-sync-manifest.schema.json) defines the shape of [`.template-sync/manifest.yml`](../.template-sync/manifest.yml), which is the source of truth for the downstream sync module taxonomy.

The schema accepts manifest version 1, version 2, and version 3 documents. Version 1 preserves the original `requires_all`-only path mapping contract for downstream compatibility. Version 2 adds `requires_any` so a path can require all `requires_all` modules plus at least one `requires_any` module; for example, `tests/test_schema_examples.py` uses `requires_any: [schema, template-sync-support]`. Version 3 adds `compatibility_groups` for host-family module metadata; the checked-in groups preserve GitHub defaults while allowing Azure DevOps-only selections and explicit mixed-host selections.

How the template sync manifest contract is validated:

<!-- template-sync: begin baseline-reference-only -->
- The manifest file is validated by the `Validate template sync manifest` `check-jsonschema` hook in [`.pre-commit-config.yaml`](../.pre-commit-config.yaml) and by [`.github/workflows/data-ci.yml`](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/.github/workflows/data-ci.yml).
- The schema itself is self-validated against its declared JSON Schema Draft 2020-12 metaschema by the `Self-validate template-sync-manifest schema` `check-metaschema` hook in [`.pre-commit-config.yaml`](../.pre-commit-config.yaml), also executed by [`.github/workflows/data-ci.yml`](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/.github/workflows/data-ci.yml).
<!-- template-sync: end baseline-reference-only -->
- [`tests/test_template_manifest.py`](../tests/test_template_manifest.py) validates manifest semantics that JSON Schema cannot express cleanly, including module-reference integrity, uniqueness rules, version 1 compatibility, version 2 relation semantics, version 3 compatibility grouping, filtering semantics, and drift between the manifest and the rendered taxonomy tables in [`TEMPLATE_UPDATE_PROCEDURE.md`](../TEMPLATE_UPDATE_PROCEDURE.md).

Downstream repositories that intentionally do not retain machine-assisted future sync metadata MAY remove `.template-sync/manifest.yml`, `schemas/template-sync-manifest.schema.json`, the matching pre-commit hooks when baseline is retained, and `tests/test_template_manifest.py`. Downstream repositories that use this sync procedure SHOULD still keep `.template-sync/marker.yml` and the template-sync support schemas required by the retained scripts.

## Template Sync Marker Schema

[`template-sync-marker.schema.json`](./template-sync-marker.schema.json) defines the shape of the downstream sync marker at `.template-sync/marker.yml`. The schema validates marker contents only.

<!-- template-sync: begin baseline-reference-only -->
Marker placement is enforced by the `Validate template sync marker` hook's `files:` pattern in [`.pre-commit-config.yaml`](../.pre-commit-config.yaml).
<!-- template-sync: end baseline-reference-only -->

The marker schema includes `template_sync.instruction_contract_waivers` for explicit waivers of missing required instruction-contract anchors. Each waiver requires `path`, `anchor`, `reason`, and `authorization_basis`; the instruction-contract validator reports applied waivers as `passed with waivers` rather than ordinary success.

The marker schema also includes `template_sync.protected_guide_contract_waivers` for explicit waivers of protected-guide section and reference obligations declared in `.template-sync/instruction-contracts.yml`. Each waiver requires `path`, `contract_key`, `reason`, and `authorization_basis`, plus at least one of `target_path` or `target_module`. Optional `linked_local_override_path` records the local override that made the protected-guide remnant intentional, but local overrides alone do not waive protected-guide obligations.

The marker schema includes `template_sync.placeholder_waivers` for explicit waivers of reviewed unresolved placeholder findings. Each waiver requires `path` or `path_pattern`, `token` or `finding_kind`, `reason`, `authorization_basis`, and `reviewed_scope`. Local overrides alone are not placeholder waivers; the placeholder helper reports local-override context but only a matching structured placeholder waiver changes the finding disposition to `waived-informational`.

The marker schema includes `template_sync.local_path_ownership` for downstream-owned project paths that are not upstream template-managed manifest rows. Each record requires `path` and `reason`, with optional `overlap_exception_reason` only when semantic validation confirms the record is near a broad manifest-owned area. Exact paths such as `docs` cover only that normalized path; directory-prefix paths such as `docs/` cover the directory path and descendants. Glob-style paths such as `docs/**` are intentionally rejected. Local ownership records may name future paths, but validators reject unsafe lexical forms, existing symlink ancestors, exact collisions with concrete manifest-owned files, and exception reasons that do not correspond to broad manifest-area proximity.

The marker schema also records collaboration-template policy inputs used by first-adoption materialization. `template_sync.issue_label_policy` accepts `existing`, `create-manual-follow-up`, `omit`, or `custom`; `custom` requires `template_sync.issue_labels`. `template_sync.discussions_policy` accepts `enabled`, `disabled`, `deferred-planned-render`, or `deferred-not-rendered`. Deferred or future-state policies that leave manual setup open require `template_sync.collaboration_policy_follow_up_status`, which MUST reflect the matching `_TODO-repo-init.md` dependent-file status.

For Azure DevOps Services adoptions, `template_sync.host_provider` values of `azure-devops-services` or `dual` enable Azure DevOps project identity fields and service setup policy fields. The Azure collaboration fields record Azure Boards intake policy, Azure Repos PR template policy, branch-policy reviewer guidance, security intake policy, security product enablement, and dependency update policy so first-adoption reporting can distinguish service-backed setup decisions from Git-file materialization.

How the template sync marker contract is validated:

<!-- template-sync: begin baseline-reference-only -->
- The marker file is validated by the `Validate template sync marker` `check-jsonschema` hook when `.template-sync/marker.yml` is present. Repositories without a marker are unaffected because no file matches the hook's anchored pattern.
- Valid marker fixtures under [`examples/template-sync-marker/valid/`](./examples/template-sync-marker/valid/) are validated by the `Validate template sync marker valid examples` `check-jsonschema` hook and by [`.github/workflows/data-ci.yml`](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/.github/workflows/data-ci.yml).
<!-- template-sync: end baseline-reference-only -->
- Invalid marker fixtures under [`examples/template-sync-marker/invalid/`](./examples/template-sync-marker/invalid/) are exercised by [`tests/test_schema_examples.py`](../tests/test_schema_examples.py), which asserts that each invalid example is rejected.
<!-- template-sync: begin baseline-reference-only -->
- The schema itself is self-validated against its declared JSON Schema Draft 2020-12 metaschema by the `Self-validate template-sync-marker schema` `check-metaschema` hook in [`.pre-commit-config.yaml`](../.pre-commit-config.yaml), also executed by [`.github/workflows/data-ci.yml`](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/.github/workflows/data-ci.yml).
<!-- template-sync: end baseline-reference-only -->
- [`tests/test_template_manifest.py`](../tests/test_template_manifest.py) checks that the baked `included_modules` enum in the marker schema matches the module names in [`.template-sync/manifest.yml`](../.template-sync/manifest.yml).

Marker changes MUST be rejected when they fail this schema. Downstream repositories that use the sync procedure SHOULD keep `.template-sync/marker.yml`, `schemas/template-sync-marker.schema.json`, the matching pre-commit hooks when baseline is retained, and the marker examples or an equivalent validation path. These files are retained with `template-sync-support`; they do not require retaining the general worked-example `schema` module.

## Template Sync Instruction Contracts Schema

[`template-sync-instruction-contracts.schema.json`](./template-sync-instruction-contracts.schema.json) defines the shape of [`.template-sync/instruction-contracts.yml`](../.template-sync/instruction-contracts.yml), which records required headings and phrases for protected instruction files plus protected-guide obligations that become stale when downstream repositories exclude optional module families. The contract file lets the upstream template and downstream repositories detect accidental removal of platform-specific agent protocols that would otherwise still pass file-presence validation, and it lets downstream validation surface protected-guide references that cannot be silently removed without owner authorization.

Protected-guide section obligations use `protected_guide_section_obligations` records with a stable `key`, protected guide `path`, `target_modules`, and one or more `stale_headings` or `stale_phrases`. They are downstream-only checks: upstream template validation does not fail merely because a listed stale heading or phrase is absent. Downstream validation applies a section obligation when the protected guide is retained and none of the target modules are retained; if the stale heading or phrase is still present, the validator requires either owner action on the protected guide or a matching `template_sync.protected_guide_contract_waivers` record.

An instruction contract can also declare `required_sections`. Each section names one unique live ATX `heading` and its exact unique immediate `next_heading` (or `null` for EOF), with ordered `required_paragraphs`, exact `required_tables`, or both. Its direct body ends before the next heading of any level; child sections have separate contracts. An added child, sibling, or higher-level heading, or a missing, duplicate, or misplaced declared successor, fails the boundary contract. The explicit successor and content after it are outside that section's scope; this is structural enforcement, not a global contradiction classifier. Extra, duplicate, or reordered paragraphs fail. Complete paragraphs and list items with zero to three leading spaces are compared with only ASCII space, horizontal tab, CR and LF wrapping normalized; other Unicode and control characters remain literal in catalog matching and waiver identities; words, punctuation, case, list markers, and Markdown markup remain significant. Fenced code, block quotes (including lazy continuation), indented code, and raw HTML blocks (including comments) cannot supply a clause. Comment delimiters inside code examples and matched inline code spans remain literal; wrapped spans must stay within a direct paragraph block. The deliberately narrow table subset uses unescaped pipe-delimited cells, at least two unique headers, a delimiter row, and full ordered data rows of matching width with unique first-column conditions. Extra, duplicate, malformed, reordered, or changed tables fail. These static checks preserve the operative policy; they do not prove that an agent follows it.

A section may add `requires_modules`, a nonempty list of unique known manifest modules. Downstream enforcement requires all parent and section modules; upstream enforces every section. Omit the section field to use only parent applicability. The GitHub plugin protocol applies with the Codex entry point, while the Azure Repos protocol also requires `azure-devops-collaboration`. When an optional successor section is both absent and inapplicable, the validator follows only its declared acyclic successor chain to the next present, applicable, or uncontracted boundary, or EOF. A present optional heading remains the exact boundary, and the separate stale-section checks still require a waiver when applicable. The body and internal boundaries of an inapplicable section are outside its required-section contract, even when the section remains present; this is not a global policy or contradiction check. Unknown inserted headings, duplicate or misplaced successors, and successor cycles fail. For example, authorized Azure protocol removal in a GitHub-only profile makes the plugin section end at the Codex review workflow; the same removal fails when Azure collaboration is retained.

For example, a retained section requiring `Agents MUST reject stale results.` fails when that sentence becomes `Agents MAY reject stale results.` or exists only in a fenced example. A table that maps a failed review to `Not clean` fails if that cell becomes `Clean`. Section failures use deterministic waiver anchors: `section:<heading>`, `section:<heading>:paragraph:<sha256>`, `section:<heading>:paragraphs:<sha256>` for an extra or reordered inventory, and `section:<heading>:tables:<sha256>`. Individual paragraph digests bind normalized expected text. Aggregate paragraph and table digests bind both expected and observed inventories; malformed tables bind exact operative table rows without whitespace normalization. Boundary failures use `section:<heading>:boundary:<sha256>` and bind the expected successor plus the observed region through that successor or EOF. A changed local deviation therefore needs a new explicit waiver; restoring canonical content does not use the old waiver. Missing headings still report every unsatisfied content contract, and a malformed table cannot suppress paragraph checks. Existing explicit marker authorization and loud waiver reporting apply; a waiver is not an ordinary pass. A missing retained file still requires an authorized `REMOVE-LOCAL` decision. All `requires_modules` must be retained: the YAML security contract therefore requires both `yaml` and `agent-instructions`. Removed agent platforms do not become mandatory merely because the catalog still declares them.

Protected-guide reference obligations use `protected_guide_reference_obligations` records with a stable `key`, protected guide `path`, `reference_kind`, and `target_modules`. `markdown-relative-link` obligations require `target_path` and are enforced through the same retained Markdown relative-link scanner used for ordinary excluded-module link checks. `absolute-url` and `prose-reference` obligations require explicit `tokens`; the validator scans only those declared tokens outside fenced code blocks, so absolute links and prose references are not treated as an open-ended text search.

Contract and observed table cells must use canonical nonempty spelling: non-whitespace words separated by one ASCII space, without leading/trailing whitespace or pipes. The schema and semantic loader use an explicit shared whitespace grammar to give Python and ECMAScript consumers the same result, including control separators and U+FEFF; catalog loading rejects invalid expectations, and document parsing applies the same grammar after trimming only ASCII space/tab syntax padding at cell edges. Internal repeated spaces, tabs and other forbidden whitespace are not rewritten. Invalid observed cells cause a table failure with the original operative rows retained in its waiver identity. Unicode text and Markdown markup remain supported. Inline-code delimiter runs are indexed once within the supported block boundaries; unmatched runs stay literal without repeated paragraph-tail searches.

Raw HTML uses the shared block boundaries in [CommonMark 0.31.2](https://spec.commonmark.org/0.31.2/#html-blocks) and [GitHub Flavored Markdown 0.29](https://github.github.com/gfm/#html-blocks). Literal-tag blocks, processing instructions, declarations and CDATA end at their specified terminators or EOF. Block-tag and standalone complete-tag blocks end at a blank line. Standalone complete tags cannot interrupt a live paragraph. Code and comment examples do not open HTML blocks, and inline spans cannot cross an interrupting block boundary. A hidden required heading or clause fails; live policy after a terminated block remains subject to its normal contract. Nested or ambiguous container syntax retains the existing conservative unsupported-content behavior.

The two dialects differ on `textarea`, `search`, `source`, lowercase declarations and textarea terminators inside literal HTML blocks. Active occurrences of these ambiguous boundaries fail all applicable section contracts in the document, including when the boundary is outside a governed section. Such a boundary can hide later headings or clauses. The scanner retains the ambiguous source lines and reports `section:<heading>:html-grammar:<sha256>`, bound to the expected section and complete original document. A changed deviation needs a new explicit waiver. Use fenced examples for these forms. Escaped text, inline code and content already inside an unambiguous inert block retain their normal behavior. A standalone closing textarea tag is a shared complete-tag form; it is ambiguous only when it can terminate an active literal block. This conservative restriction is not a general Markdown renderer or HTML sanitizer.

Lazy quote continuation is supported for ordinary paragraph and simple list-paragraph leaves. Quoted headings, fences, blank lines, and other recognized structural leaves do not hide later live text. Ambiguous quoted HTML, pipe-table text, or mixed nested containers fail closed within a governed section: the scanner preserves their original text in an explicit unsupported-region inventory, and following lines cannot supply required clauses until a clear blank separator or live heading. Use fenced examples for those unsupported quoted forms. This bounded scanner is not a general CommonMark parser.

Indented text is inert code only when no live paragraph or list container can own it. A no-blank indented paragraph continuation and potential nested list content are retained as explicit unsupported original-text inventory, so an added rule cannot disappear or become a section heading. List context can survive blank lines and lazy continuation; a proven outside block or dedented new paragraph ends it. Ordinary paragraphs and list items with zero to three leading spaces retain their existing normalized inventory, including the template's nested clauses. Nonempty list content after more than four visual padding columns is an indented code block, not an operative clause. The scanner expands tabs to four-column stops and preserves such lines as unsupported policy before normalization. One-to-four-column padding and empty items retain their existing behavior. Potential nested headings, quotes, HTML blocks, comments, fences, and four-column content fail closed. Use unindented direct paragraphs and top-level list items for new governed policy, and top-level fences for nested examples. Short complete HTML block comments (`<!-->` and `<!--->`) close on their own line and cannot suppress later policy. Inline comments require a same-line close and the shared CommonMark/GFM grammar: content cannot start with `>` or `->`, end with `-`, or contain `--`. Short, unclosed, wrapped, or otherwise ambiguous inline forms remain explicit unsupported text. Use a standalone comment block, with its opener preceded only by zero to three spaces, for multiline comments.

Paragraph expectations must remain nonempty and unique after the same whitespace normalization used for matching. The semantic loader rejects whitespace-only clauses and normalized duplicates before checking documents; the schema alone does not establish these semantic properties. Valid wrapped clauses retain their original catalog spelling and order. Hash-prefixed text is ordinary paragraph content unless it meets the supported ATX heading grammar (one to six hashes followed by ASCII space, tab, or the end of the line).

Removing an inline comment preserves its actual surrounding text and does not insert a space. For example, `Agents<!-- note -->MUST` cannot satisfy `Agents MUST`, while `Agents <!-- note -->MUST` retains the existing space. Quoted list content with more than four padding columns starts item code and cannot establish lazy paragraph continuation. Tabs in quoted container or list structural prefixes are unsupported and remain visible in failure inventories; tabs after ordinary text begins remain supported. Comment removal cannot create a heading or list marker absent from the source. Comment-bearing table rows and nonblank HTML-comment-block closing tails are unsupported original-text inventory. Distinct tables can share column headers; duplicate table identity includes the complete headers and ordered rows, and the document must retain the full ordered table inventory.

The catalog remains protected for authorization and materialization, but it is structured policy data rather than a human-facing prose document. The excluded-module prose scan therefore omits the catalog's intentional module-gated obligation records. Root agent documents and protected instruction/Cursor directories retain their existing prose checks, including when the report runs before marker creation with explicit included modules.

Ordered list markers use ASCII digits. A non-1 ordered start cannot interrupt a direct live paragraph; the scanner keeps that continuation as unsupported original text before it can become a false list-contained fence. Blank-separated lists and existing list siblings keep their supported behavior. Closing fences may end in ASCII spaces or tabs; other trailing characters do not close them. New quoted leaves that start with `[` are ambiguous with potentially wrapped reference definitions and fail closed as unsupported regions. An established ordinary quoted paragraph can still continue with bracket-leading text. Put reference-definition examples inside fences instead.

The retained instruction-contract catalog is protected governance. Its creation, replacement, or obligation changes need explicit current-task owner or maintainer authorization. Adoption and sync use the existing path-scoped `protected_file_decisions`; an authorized `TAKE` copies the pinned reviewed catalog intact. Support-retaining profiles keep the same catalog, including profiles with no agent platform; `requires_modules` determines applicability. Candidate-local schema and content checks detect drift against the supplied catalog and do not independently prove authorization or resist coordinated changes to candidate code, expectations, and tests.

Markdown structure uses only CR, LF, or CRLF physical line endings and ASCII space/tab structural whitespace. Other Unicode/control characters remain source content and cannot create a fence close, heading, blank separator, or template-sync pruning marker. Paragraph matching still uses its documented whitespace normalization. The same physical-line helper is used by shared fence, marker, blank-hygiene, and excluded-reference scans.

The instruction-contract validator limits each file it reads to **1 MiB (1,048,576 bytes)** before decoding or parsing. This applies to governed instruction and protected-guide files, the catalog, manifest, downstream marker, and their JSON schemas. The limit leaves room for substantial policy files while bounding local input allocation; it is independent of any agent's document-context limit. JSON and instructions use strict UTF-8; YAML keeps its optional UTF-8 BOM support. Existing newline normalization and repository containment remain unchanged. Oversized input and invalid UTF-8 fail with a controlled path-specific diagnostic; input is never silently truncated or repaired. For example, an otherwise valid 1,048,576-byte instruction file passes this size check, while one extra byte produces an input-limit error and exit 1. Invalid UTF-8 below the limit also produces exit 1. Split an unusually large document or review an intentional change to the validator's limit. This local check does not establish a trusted security boundary; other callers of the shared text loaders do not acquire this size limit automatically.

How the instruction-contract contract is validated:

<!-- template-sync: begin baseline-reference-only -->
- The contract file is validated by the `Validate template sync instruction contracts` `check-jsonschema` hook in [`.pre-commit-config.yaml`](../.pre-commit-config.yaml) and by [`.github/workflows/data-ci.yml`](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/.github/workflows/data-ci.yml).
- Valid instruction-contract fixtures under [`examples/template-sync-instruction-contracts/valid/`](./examples/template-sync-instruction-contracts/valid/) are validated by the `Validate template sync instruction contract valid examples` `check-jsonschema` hook and by [`.github/workflows/data-ci.yml`](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/.github/workflows/data-ci.yml).
<!-- template-sync: end baseline-reference-only -->
- Invalid instruction-contract fixtures under [`examples/template-sync-instruction-contracts/invalid/`](./examples/template-sync-instruction-contracts/invalid/) are exercised by [`tests/test_schema_examples.py`](../tests/test_schema_examples.py), which asserts that each invalid example is rejected.
<!-- template-sync: begin baseline-reference-only -->
- The schema itself is self-validated against its declared JSON Schema Draft 2020-12 metaschema by the `Self-validate template-sync-instruction-contracts schema` `check-metaschema` hook in [`.pre-commit-config.yaml`](../.pre-commit-config.yaml), also executed by [`.github/workflows/data-ci.yml`](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/.github/workflows/data-ci.yml).
<!-- template-sync: end baseline-reference-only -->
- Required anchors are enforced by [`validate_instruction_contracts.py`](../.template-sync/scripts/validate_instruction_contracts.py). Upstream template CI invokes `--mode upstream-template`; downstream repositories SHOULD invoke `--mode downstream`, with `--require-marker` when the marker is required in CI.
- Protected-guide reference obligations are composed by [`validate_downstream_adoption.py`](../.template-sync/scripts/validate_downstream_adoption.py), which keeps broad relative-link validation separate from declared absolute URL and prose-token obligations.

Downstream repositories that use the sync procedure SHOULD keep `.template-sync/instruction-contracts.yml`, `schemas/template-sync-instruction-contracts.schema.json`, the matching pre-commit hooks when baseline is retained, and the instruction-contract examples or an equivalent validation path. These files are retained with `template-sync-support`; they do not require retaining the general worked-example `schema` module.

## First-Adoption Quality Suppressions Schema

[`first-adoption-quality-suppressions.schema.json`](./first-adoption-quality-suppressions.schema.json) defines the shape of the optional downstream-created `.template-sync/first-adoption/quality-suppressions.json` file used by first-adoption quality reports. The upstream template does not ship a concrete suppression file. Downstream repositories create it only when they intentionally suppress report findings.

The current schema defines a report-scoped `path-reference` section. Each suppression entry can be scoped by `ruleId`, `category`, exact source `path`, source `pathGlob`, exact `literal`, and `literalPattern`; populated selector fields are combined, so every populated selector must match before the finding is suppressed. The schema reserves the top-level structure for future `line-ending`, `powershell`, or `markdown` sections without relocating the file.

How the first-adoption quality suppression contract is validated:

<!-- template-sync: begin baseline-reference-only -->
- The suppression file is validated by the `Validate first-adoption quality suppressions` `check-jsonschema` hook when `.template-sync/first-adoption/quality-suppressions.json` is present. Repositories without that file are unaffected because no file matches the hook's anchored pattern.
- Valid suppression fixtures under [`examples/first-adoption-quality-suppressions/valid/`](./examples/first-adoption-quality-suppressions/valid/) are validated by the `Validate first-adoption quality suppression valid examples` `check-jsonschema` hook and by [`.github/workflows/data-ci.yml`](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/.github/workflows/data-ci.yml).
<!-- template-sync: end baseline-reference-only -->
- Invalid suppression fixtures under [`examples/first-adoption-quality-suppressions/invalid/`](./examples/first-adoption-quality-suppressions/invalid/) are exercised by [`tests/test_schema_examples.py`](../tests/test_schema_examples.py), which asserts that each invalid example is rejected.
<!-- template-sync: begin baseline-reference-only -->
- The schema itself is self-validated against its declared JSON Schema Draft 2020-12 metaschema by the `Self-validate first-adoption quality suppressions schema` `check-metaschema` hook in [`.pre-commit-config.yaml`](../.pre-commit-config.yaml), also executed by [`.github/workflows/data-ci.yml`](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/.github/workflows/data-ci.yml).
<!-- template-sync: end baseline-reference-only -->

Downstream repositories that use the first-adoption quality reports SHOULD keep `schemas/first-adoption-quality-suppressions.schema.json`, the matching pre-commit hooks when baseline is retained, and the suppression examples or an equivalent validation path. These files are retained with `template-sync-support`; they do not require retaining the general worked-example `schema` module.

### Downstream Removal Checklist

The worked example is intentionally easy to remove. This checklist removes only the general `schema` module's `example-config` surface; it does not remove the template-sync production schemas or their example fixtures when `template-sync-support` is retained. To take the worked example out of a downstream repository:

1. Delete [`schemas/example-config.schema.json`](./example-config.schema.json).
2. Delete the [`schemas/examples/example-config/`](./examples/example-config/) directory and all of its contents.
3. When pre-commit is retained, remove the `Validate example-config valid examples` and `Self-validate example-config schema` hooks (and the surrounding `python-jsonschema/check-jsonschema` repo block, if no other hooks from that repo remain) from `.pre-commit-config.yaml`. Keep the template-sync support hooks when the repository retains both `baseline` and `template-sync-support`.
4. If you adopted the optional schema-example tests (for example, by copying the upstream [`templates/python/tests/test_schema_examples.py`](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/templates/python/tests/test_schema_examples.py) into your repository's `tests/` directory), remove or adjust the corresponding test cases there if no schemas remain in the downstream repository.
5. Update any documentation that mentions the example schema, including this `README.md` and the data-CI definitions when retained.

## Future Work

Candidate load-bearing repository configuration files that could later be schema-validated against [SchemaStore](https://www.schemastore.org/)-published schemas, `check-jsonschema` built-in schemas, or other stable schema sources include:

- `package.json` — schema available on SchemaStore. Not currently shipped as a `check-jsonschema` `--builtin-schema`; would require pinning an external schema URL or a future builtin.
- Generated package-manager lockfiles — only if a stable schema-backed validation path is useful and does not conflict with the package manager's own validation.
- `pyproject.toml` — TOML rather than JSON, but conceptually parallel; would require a TOML-aware validator rather than `check-jsonschema`.
- `.pre-commit-config.yaml` — not currently shipped as a `check-jsonschema` `--builtin-schema`. pre-commit itself validates the file's structure when it loads its configuration.
- `.markdownlint.jsonc` — intentionally JSONC (contains comments). MUST NOT be converted to strict JSON merely to satisfy a validator. markdownlint's own config loader remains the enforcement mechanism for this file.
- `.yamllint.yml` — not currently shipped as a `check-jsonschema` `--builtin-schema`. MUST NOT be weakened to satisfy an incomplete external schema; yamllint itself enforces its configuration shape when it loads `.yamllint.yml`.
- GitHub Actions workflow files — already covered by `actionlint`, so an additional schema check would primarily be redundant.

When baseline and GitHub platform support are retained, `.github/dependabot.yml` is validated by default. The candidates above remain out of scope until a verified, mature builtin schema (or an explicitly pinned stable schema source) becomes available; downstream repositories MAY adopt them as additional `check-jsonschema` hooks at their discretion. See the [Built-in Schema Validation for Real Load-Bearing Configuration Files](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/.github/TEMPLATE_DESIGN_DECISIONS.md#design-decision-built-in-schema-validation-for-real-load-bearing-configuration-files) ADR for the durable "Evaluated but deferred" record covering each candidate.

## Out of Scope for This Worked Example

This directory ships one worked example schema and production schemas for the template sync manifest, marker, and instruction contracts. It does not introduce:

- Additional SchemaStore-backed validation hooks beyond the wired `vendor.dependabot` validation of `.github/dependabot.yml` (which lives in `.pre-commit-config.yaml`, not in this directory).
- Any JSONC, JSON5, or TOML schema validation tooling.

Additional schema-backed file families will be added in follow-up changes when concrete contracts are introduced or when downstream consumers decide to adopt them.
