<!-- markdownlint-disable MD013 -->

# Schemas

## Metadata

- **Status:** Active
- **Owner:** Repository Maintainers
- **Last Updated:** 2026-06-22
- **Scope:** Conventions for JSON Schemas that describe load-bearing JSON and YAML files in this repository, the template sync manifest, marker, instruction-contract, and first-adoption quality suppression schemas, plus a clearly removable worked example (`example-config.schema.json` with valid and invalid example data) wired into pre-commit and data CI to demonstrate the schema-validation pipeline end to end.
- **Related:** [JSON Authoring Standards](../.github/instructions/json.instructions.md), [YAML Authoring Standards](../.github/instructions/yaml.instructions.md), [Repository Copilot Instructions](../.github/copilot-instructions.md), [Template Design Decisions — Schema Location at Repository Root](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/.github/TEMPLATE_DESIGN_DECISIONS.md#design-decision-schema-location-at-repository-root), [Template Design Decisions — Schema Validation Tiers](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/.github/TEMPLATE_DESIGN_DECISIONS.md#design-decision-schema-validation-tiers), [Template Design Decisions — Built-in Schema Validation for Real Load-Bearing Configuration Files](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/.github/TEMPLATE_DESIGN_DECISIONS.md#design-decision-built-in-schema-validation-for-real-load-bearing-configuration-files), [Template Design Decisions — `additionalProperties` Policy](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/.github/TEMPLATE_DESIGN_DECISIONS.md#design-decision-additionalproperties-policy), [Template Design Decisions — Testing Beyond Linting for JSON/YAML](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/.github/TEMPLATE_DESIGN_DECISIONS.md#design-decision-testing-beyond-linting-for-jsonyaml)

## Purpose

This directory contains JSON Schemas for load-bearing JSON and YAML files in this repository. A "load-bearing" file is one whose shape is depended on by build, deploy, runtime, release automation, or downstream consumers, such that a malformed value would cause incorrect behavior.

Schemas live at the repository root (under `schemas/`, not `.github/schemas/`) so they are discoverable to IDEs, schema validators, and downstream consumers, and so projects that do not use schema-backed data files can opt out by deleting this directory.

## Template Portability

This template provides `schemas/` as a convention for repositories that adopt schema-backed JSON or YAML contracts. Downstream repositories MAY delete `schemas/` (including this `README.md`) if they do not use schema-backed data files or the template sync support scripts.

## Repository-Specific Validation Inventory

The portable JSON and YAML style guides describe validation rules generically so they can be reused by repositories with different schema, test, and CI layouts. This README is the repository-specific home for this template's concrete schema inventory, worked-example fixtures, built-in schema validation choices, regression tests, and data-file CI wiring.

The authoritative active hook list remains [`.pre-commit-config.yaml`](../.pre-commit-config.yaml). The dedicated data-file workflow, [`.github/workflows/data-ci.yml`](../.github/workflows/data-ci.yml), re-runs the retained data-file hooks so branch protection can require JSON, YAML, GitHub Actions, and schema validation independently of language-specific CI jobs.

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

Schema-backed files are validated by pre-commit and the dedicated data-file CI workflow ([`.github/workflows/data-ci.yml`](../.github/workflows/data-ci.yml)). This template ships a worked example (see [Worked Example](#worked-example) below) so the validation pipeline is exercised end to end out of the box, and it ships production schemas for the template sync manifest, marker, instruction contracts, and first-adoption quality suppressions (see [Template Sync Manifest Schema](#template-sync-manifest-schema), [Template Sync Marker Schema](#template-sync-marker-schema), [Template Sync Instruction Contracts Schema](#template-sync-instruction-contracts-schema), and [First-Adoption Quality Suppressions Schema](#first-adoption-quality-suppressions-schema)). Downstream repositories that do not use general schema-backed data files SHOULD remove the worked example using the [Downstream Removal Checklist](#downstream-removal-checklist). Repositories that keep `template-sync-support` SHOULD retain the template-sync production schemas and their template-sync example fixtures even when they remove the general `schema` module. See the JSON authoring standards for the schema-validation policy and tier guidance.

### Schema Categories

This repository distinguishes two schema categories. The distinction matters for where schemas live, how they are tested, and how they are wired into pre-commit and CI.

1. **Project-owned schemas.**
   - Stored under `schemas/` in this repository.
   - MAY include valid and invalid example fixtures under `schemas/examples/<schema-name>/{valid,invalid}/`.
   - Tested by [`tests/test_schema_examples.py`](../tests/test_schema_examples.py), which auto-discovers schema/example pairs and asserts that valid examples pass and invalid examples fail.
   - Wired into pre-commit by adding a `check-jsonschema` hook that points at the schema with `--schemafile schemas/<name>.schema.json` and an anchored `files:` pattern matching the file family the schema covers.
   - The [Worked Example](#worked-example) below is the canonical illustration of the general `schema` module. The [Template Sync Manifest Schema](#template-sync-manifest-schema), [Template Sync Marker Schema](#template-sync-marker-schema), [Template Sync Instruction Contracts Schema](#template-sync-instruction-contracts-schema), and [First-Adoption Quality Suppressions Schema](#first-adoption-quality-suppressions-schema) are production schema-backed contracts owned by `template-sync-support` because the support scripts load them at runtime or validate downstream-created retained state.

2. **External built-in schemas.**
   - Referenced through `check-jsonschema --builtin-schema vendor.<name>` against schemas that ship inside the pinned `check-jsonschema` release.
   - **Not vendored** into this repository. Schema content tracks `check-jsonschema` upstream releases and is updated through the Dependabot `pre-commit` ecosystem.
   - Used for selected real, load-bearing repository configuration files where the external schema is mature and validation is low-noise.
   - See the [Built-in Schema Validation for Real Load-Bearing Configuration Files](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/.github/TEMPLATE_DESIGN_DECISIONS.md#design-decision-built-in-schema-validation-for-real-load-bearing-configuration-files) ADR for the policy, the full list of selected files, and the explicit "Evaluated but deferred" negative-space record.

The two categories are complementary. A downstream repository MAY use either, both, or neither.

<!-- template-sync: begin github-platform-reference-only -->

### Real Repository Configuration Files Validated Through Built-in Schemas

The following real, load-bearing repository configuration files are validated by default through `check-jsonschema --builtin-schema ...` hooks in [`.pre-commit-config.yaml`](../.pre-commit-config.yaml):

| File | Built-in schema identifier | Regression coverage |
| --- | --- | --- |
| [`.github/dependabot.yml`](../.github/dependabot.yml) | `vendor.dependabot` | GitHub-platform-only validation; when retained, `tests/test_dependabot_schema.py` validates the documented `tests/fixtures/dependabot/auto-assignment.yml` fixture |

If a downstream repository deletes one of these files, it **MUST** also remove the corresponding `check-jsonschema` hook (and any matching `data-ci.yml` step) per the [downstream removal guidance in the ADR](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/.github/TEMPLATE_DESIGN_DECISIONS.md#design-decision-built-in-schema-validation-for-real-load-bearing-configuration-files). Azure DevOps-only adoptions do not retain `.github/dependabot.yml`, `validate-dependabot-config`, or `tests/test_dependabot_schema.py`; Azure DevOps security scanning and routine dependency version updates are documented as service-side/adopter-selected choices rather than as Dependabot schema validation.

<!-- template-sync: end github-platform-reference-only -->

<!-- template-sync: begin azure-devops-guide-reference-only -->
For Azure DevOps-only adoptions, see the [Azure DevOps Services Support Guide](../docs/azure-devops-support.md) for host-specific service boundaries.
<!-- template-sync: end azure-devops-guide-reference-only -->

### Project-Owned Schema-Backed Files

The following project-owned file families are validated by default through `check-jsonschema --schemafile ...` hooks in [`.pre-commit-config.yaml`](../.pre-commit-config.yaml):

| File | Schema |
| --- | --- |
| [`.template-sync/manifest.yml`](../.template-sync/manifest.yml) | [`template-sync-manifest.schema.json`](./template-sync-manifest.schema.json) |
| `.template-sync/marker.yml` when present | [`template-sync-marker.schema.json`](./template-sync-marker.schema.json) |
| [`.template-sync/instruction-contracts.yml`](../.template-sync/instruction-contracts.yml) | [`template-sync-instruction-contracts.schema.json`](./template-sync-instruction-contracts.schema.json) |
| `.template-sync/first-adoption/quality-suppressions.json` when present | [`first-adoption-quality-suppressions.schema.json`](./first-adoption-quality-suppressions.schema.json) |

### File-Family Hooks

When real schemas exist, validation SHOULD be wired in per **file family**:

- Add **one `check-jsonschema` hook per real schema-backed file family**, scoped to the files that family covers (for example, `^config/.*\.json$`).
- **Do not add placeholder hooks** for schemas that do not yet exist. An empty or speculative hook adds noise without enforcing anything.
- **Do not validate every JSON or YAML file by default.** Generic `check-jsonschema --check-metaschema` style sweeps are out of scope; pre-commit already runs `check-json` and `check-yaml` for syntax. Schema validation is a contract check for specific file families, not a global sweep.

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

A starter version of this pattern lives at [`templates/python/tests/test_schema_examples.py`](../templates/python/tests/test_schema_examples.py); the active, canonical version that this repository runs in CI lives at [`tests/test_schema_examples.py`](../tests/test_schema_examples.py). Both auto-discover schema/example pairs under `schemas/`, prefer the console script, and fall back to `python -m check_jsonschema` when the package is importable. The starter retains a `skipif` guard so it remains safe to copy into downstream projects that have not yet added `check-jsonschema` to their dev/test dependencies.

## Worked Example

This template ships a worked example so the schema-validation pipeline works out of the box. The worked example is **template starter content**, not a production contract for downstream repositories.

- Schema: [`example-config.schema.json`](./example-config.schema.json)
- Valid example data: [`examples/example-config/valid/`](./examples/example-config/valid/)
  - [`minimal.json`](./examples/example-config/valid/minimal.json) — only the required properties.
  - [`full.json`](./examples/example-config/valid/full.json) — every optional property exercised.
- Invalid example data: [`examples/example-config/invalid/`](./examples/example-config/invalid/)
  - [`missing-required.json`](./examples/example-config/invalid/missing-required.json) — required property omitted.
  - [`wrong-type.json`](./examples/example-config/invalid/wrong-type.json) — required property has the wrong JSON type.
  - [`extra-property.json`](./examples/example-config/invalid/extra-property.json) — unknown property rejected by `additionalProperties: false`.

How the worked example is validated:

- The `valid/` example data files are validated by the `Validate example-config valid examples` `check-jsonschema` hook in [`.pre-commit-config.yaml`](../.pre-commit-config.yaml) and by [`.github/workflows/data-ci.yml`](../.github/workflows/data-ci.yml).
- The schema itself is self-validated against its declared JSON Schema Draft 2020-12 metaschema by the `Self-validate example-config schema` `check-metaschema` hook in [`.pre-commit-config.yaml`](../.pre-commit-config.yaml), also executed by [`.github/workflows/data-ci.yml`](../.github/workflows/data-ci.yml).
- The `invalid/` example data files are exercised by [`tests/test_schema_examples.py`](../tests/test_schema_examples.py), which uses `check-jsonschema` to assert that each invalid example causes a non-zero exit code (and that each valid example exits cleanly). A starter version of this pattern, with the same discovery and assertion logic but with project-root resolution suitable for downstream repositories, is also available at [`templates/python/tests/test_schema_examples.py`](../templates/python/tests/test_schema_examples.py).
- Invalid example data files MUST NOT be wired into a normal pre-commit hook because `check-jsonschema` would treat their (expected) failure as a hook failure.

## Template Sync Manifest Schema

[`template-sync-manifest.schema.json`](./template-sync-manifest.schema.json) defines the shape of [`.template-sync/manifest.yml`](../.template-sync/manifest.yml), which is the source of truth for the downstream sync module taxonomy.

The schema accepts manifest version 1, version 2, and version 3 documents. Version 1 preserves the original `requires_all`-only path mapping contract for downstream compatibility. Version 2 adds `requires_any` so a path can require all `requires_all` modules plus at least one `requires_any` module, such as `.github/workflows/data-ci.yml` requiring `github-actions` plus at least one of `json`, `yaml`, `schema`, or `template-sync-support`. Version 3 adds `compatibility_groups` for host-family module metadata; the checked-in groups preserve GitHub defaults while allowing Azure DevOps-only selections and explicit mixed-host selections.

How the template sync manifest contract is validated:

- The manifest file is validated by the `Validate template sync manifest` `check-jsonschema` hook in [`.pre-commit-config.yaml`](../.pre-commit-config.yaml) and by [`.github/workflows/data-ci.yml`](../.github/workflows/data-ci.yml).
- The schema itself is self-validated against its declared JSON Schema Draft 2020-12 metaschema by the `Self-validate template-sync-manifest schema` `check-metaschema` hook in [`.pre-commit-config.yaml`](../.pre-commit-config.yaml), also executed by [`.github/workflows/data-ci.yml`](../.github/workflows/data-ci.yml).
- [`tests/test_template_manifest.py`](../tests/test_template_manifest.py) validates manifest semantics that JSON Schema cannot express cleanly, including module-reference integrity, uniqueness rules, version 1 compatibility, version 2 relation semantics, version 3 compatibility grouping, filtering semantics, and drift between the manifest and the rendered taxonomy tables in [`TEMPLATE_UPDATE_PROCEDURE.md`](../TEMPLATE_UPDATE_PROCEDURE.md).

Downstream repositories that intentionally do not retain machine-assisted future sync metadata MAY remove `.template-sync/manifest.yml`, `schemas/template-sync-manifest.schema.json`, the matching pre-commit hooks, and `tests/test_template_manifest.py`. Downstream repositories that use this sync procedure SHOULD still keep `.template-sync/marker.yml` and the template-sync support schemas required by the retained scripts.

## Template Sync Marker Schema

[`template-sync-marker.schema.json`](./template-sync-marker.schema.json) defines the shape of the downstream sync marker at `.template-sync/marker.yml`. The schema validates marker contents only; marker placement is enforced by the `Validate template sync marker` hook's `files:` pattern in [`.pre-commit-config.yaml`](../.pre-commit-config.yaml).

The marker schema includes `template_sync.instruction_contract_waivers` for explicit waivers of missing required instruction-contract anchors. Each waiver requires `path`, `anchor`, `reason`, and `authorization_basis`; the instruction-contract validator reports applied waivers as `passed with waivers` rather than ordinary success.

The marker schema includes `template_sync.local_path_ownership` for downstream-owned project paths that are not upstream template-managed manifest rows. Each record requires `path` and `reason`, with optional `overlap_exception_reason` only when semantic validation confirms the record is near a broad manifest-owned area. Exact paths such as `docs` cover only that normalized path; directory-prefix paths such as `docs/` cover the directory path and descendants. Glob-style paths such as `docs/**` are intentionally rejected. Local ownership records may name future paths, but validators reject unsafe lexical forms, existing symlink ancestors, exact collisions with concrete manifest-owned files, and exception reasons that do not correspond to broad manifest-area proximity.

The marker schema also records collaboration-template policy inputs used by first-adoption materialization. `template_sync.issue_label_policy` accepts `existing`, `create-manual-follow-up`, `omit`, or `custom`; `custom` requires `template_sync.issue_labels`. `template_sync.discussions_policy` accepts `enabled`, `disabled`, `deferred-planned-render`, or `deferred-not-rendered`. Deferred or future-state policies that leave manual setup open require `template_sync.collaboration_policy_follow_up_status`, which MUST reflect the matching `_TODO-repo-init.md` dependent-file status.

For Azure DevOps Services adoptions, `template_sync.host_provider` values of `azure-devops-services` or `dual` enable Azure DevOps project identity fields and service setup policy fields. The Azure collaboration fields record Azure Boards intake policy, Azure Repos PR template policy, branch-policy reviewer guidance, security intake policy, security product enablement, and dependency update policy so first-adoption reporting can distinguish service-backed setup decisions from Git-file materialization.

How the template sync marker contract is validated:

- The marker file is validated by the `Validate template sync marker` `check-jsonschema` hook when `.template-sync/marker.yml` is present. Repositories without a marker are unaffected because no file matches the hook's anchored pattern.
- Valid marker fixtures under [`examples/template-sync-marker/valid/`](./examples/template-sync-marker/valid/) are validated by the `Validate template sync marker valid examples` `check-jsonschema` hook and by [`.github/workflows/data-ci.yml`](../.github/workflows/data-ci.yml).
- Invalid marker fixtures under [`examples/template-sync-marker/invalid/`](./examples/template-sync-marker/invalid/) are exercised by [`tests/test_schema_examples.py`](../tests/test_schema_examples.py), which asserts that each invalid example is rejected.
- The schema itself is self-validated against its declared JSON Schema Draft 2020-12 metaschema by the `Self-validate template-sync-marker schema` `check-metaschema` hook in [`.pre-commit-config.yaml`](../.pre-commit-config.yaml), also executed by [`.github/workflows/data-ci.yml`](../.github/workflows/data-ci.yml).
- [`tests/test_template_manifest.py`](../tests/test_template_manifest.py) checks that the baked `included_modules` enum in the marker schema matches the module names in [`.template-sync/manifest.yml`](../.template-sync/manifest.yml).

Marker changes MUST be rejected when they fail this schema. Downstream repositories that use the sync procedure SHOULD keep `.template-sync/marker.yml`, `schemas/template-sync-marker.schema.json`, the matching pre-commit hooks, and the marker examples or an equivalent validation path. These files are retained with `template-sync-support`; they do not require retaining the general worked-example `schema` module.

## Template Sync Instruction Contracts Schema

[`template-sync-instruction-contracts.schema.json`](./template-sync-instruction-contracts.schema.json) defines the shape of [`.template-sync/instruction-contracts.yml`](../.template-sync/instruction-contracts.yml), which records required headings and phrases for protected instruction files. The contract file lets the upstream template and downstream repositories detect accidental removal of platform-specific agent protocols that would otherwise still pass file-presence validation.

How the instruction-contract contract is validated:

- The contract file is validated by the `Validate template sync instruction contracts` `check-jsonschema` hook in [`.pre-commit-config.yaml`](../.pre-commit-config.yaml) and by [`.github/workflows/data-ci.yml`](../.github/workflows/data-ci.yml).
- Valid instruction-contract fixtures under [`examples/template-sync-instruction-contracts/valid/`](./examples/template-sync-instruction-contracts/valid/) are validated by the `Validate template sync instruction contract valid examples` `check-jsonschema` hook and by [`.github/workflows/data-ci.yml`](../.github/workflows/data-ci.yml).
- Invalid instruction-contract fixtures under [`examples/template-sync-instruction-contracts/invalid/`](./examples/template-sync-instruction-contracts/invalid/) are exercised by [`tests/test_schema_examples.py`](../tests/test_schema_examples.py), which asserts that each invalid example is rejected.
- The schema itself is self-validated against its declared JSON Schema Draft 2020-12 metaschema by the `Self-validate template-sync-instruction-contracts schema` `check-metaschema` hook in [`.pre-commit-config.yaml`](../.pre-commit-config.yaml), also executed by [`.github/workflows/data-ci.yml`](../.github/workflows/data-ci.yml).
- Required anchors are enforced by [`validate_instruction_contracts.py`](../.template-sync/scripts/validate_instruction_contracts.py). Upstream template CI invokes `--mode upstream-template`; downstream repositories SHOULD invoke `--mode downstream`, with `--require-marker` when the marker is required in CI.

Downstream repositories that use the sync procedure SHOULD keep `.template-sync/instruction-contracts.yml`, `schemas/template-sync-instruction-contracts.schema.json`, the matching pre-commit hooks, and the instruction-contract examples or an equivalent validation path. These files are retained with `template-sync-support`; they do not require retaining the general worked-example `schema` module.

## First-Adoption Quality Suppressions Schema

[`first-adoption-quality-suppressions.schema.json`](./first-adoption-quality-suppressions.schema.json) defines the shape of the optional downstream-created `.template-sync/first-adoption/quality-suppressions.json` file used by first-adoption quality reports. The upstream template does not ship a concrete suppression file. Downstream repositories create it only when they intentionally suppress report findings.

The current schema defines a report-scoped `path-reference` section. Each suppression entry can be scoped by `ruleId`, `category`, exact source `path`, source `pathGlob`, exact `literal`, and `literalPattern`; populated selector fields are combined, so every populated selector must match before the finding is suppressed. The schema reserves the top-level structure for future `line-ending`, `powershell`, or `markdown` sections without relocating the file.

How the first-adoption quality suppression contract is validated:

- The suppression file is validated by the `Validate first-adoption quality suppressions` `check-jsonschema` hook when `.template-sync/first-adoption/quality-suppressions.json` is present. Repositories without that file are unaffected because no file matches the hook's anchored pattern.
- Valid suppression fixtures under [`examples/first-adoption-quality-suppressions/valid/`](./examples/first-adoption-quality-suppressions/valid/) are validated by the `Validate first-adoption quality suppression valid examples` `check-jsonschema` hook and by [`.github/workflows/data-ci.yml`](../.github/workflows/data-ci.yml).
- Invalid suppression fixtures under [`examples/first-adoption-quality-suppressions/invalid/`](./examples/first-adoption-quality-suppressions/invalid/) are exercised by [`tests/test_schema_examples.py`](../tests/test_schema_examples.py), which asserts that each invalid example is rejected.
- The schema itself is self-validated against its declared JSON Schema Draft 2020-12 metaschema by the `Self-validate first-adoption quality suppressions schema` `check-metaschema` hook in [`.pre-commit-config.yaml`](../.pre-commit-config.yaml), also executed by [`.github/workflows/data-ci.yml`](../.github/workflows/data-ci.yml).

Downstream repositories that use the first-adoption quality reports SHOULD keep `schemas/first-adoption-quality-suppressions.schema.json`, the matching pre-commit hooks, and the suppression examples or an equivalent validation path. These files are retained with `template-sync-support`; they do not require retaining the general worked-example `schema` module.

### Downstream Removal Checklist

The worked example is intentionally easy to remove. This checklist removes only the general `schema` module's `example-config` surface; it does not remove the template-sync production schemas or their example fixtures when `template-sync-support` is retained. To take the worked example out of a downstream repository:

1. Delete [`schemas/example-config.schema.json`](./example-config.schema.json).
2. Delete the [`schemas/examples/example-config/`](./examples/example-config/) directory and all of its contents.
3. Remove the `Validate example-config valid examples` and `Self-validate example-config schema` hooks (and the surrounding `python-jsonschema/check-jsonschema` repo block, if no other hooks from that repo remain) from [`.pre-commit-config.yaml`](../.pre-commit-config.yaml). Keep the template-sync support hooks when the repository retains `template-sync-support`.
4. If you adopted the optional schema-example tests (for example, by copying [`templates/python/tests/test_schema_examples.py`](../templates/python/tests/test_schema_examples.py) into your repository's `tests/` directory), remove or adjust the corresponding test cases there if no schemas remain in the downstream repository.
5. Update any documentation that mentions the example schema, including this `README.md` and any references in [`.github/workflows/data-ci.yml`](../.github/workflows/data-ci.yml).

## Future Work

Candidate load-bearing repository configuration files that could later be schema-validated against [SchemaStore](https://www.schemastore.org/)-published schemas, `check-jsonschema` built-in schemas, or other stable schema sources include:

- `package.json` — schema available on SchemaStore. Not currently shipped as a `check-jsonschema` `--builtin-schema`; would require pinning an external schema URL or a future builtin.
- Generated package-manager lockfiles — only if a stable schema-backed validation path is useful and does not conflict with the package manager's own validation.
- `pyproject.toml` — TOML rather than JSON, but conceptually parallel; would require a TOML-aware validator rather than `check-jsonschema`.
- `.pre-commit-config.yaml` — not currently shipped as a `check-jsonschema` `--builtin-schema`. pre-commit itself validates the file's structure when it loads its configuration.
- `.markdownlint.jsonc` — intentionally JSONC (contains comments). MUST NOT be converted to strict JSON merely to satisfy a validator. markdownlint's own config loader remains the enforcement mechanism for this file.
- `.yamllint.yml` — not currently shipped as a `check-jsonschema` `--builtin-schema`. MUST NOT be weakened to satisfy an incomplete external schema; yamllint itself enforces its configuration shape when it loads `.yamllint.yml`.
- GitHub Actions workflow files — already covered by `actionlint`, so an additional schema check would primarily be redundant.

`.github/dependabot.yml` is already validated by default; see the [Real Repository Configuration Files Validated Through Built-in Schemas](#real-repository-configuration-files-validated-through-built-in-schemas) section above. The candidates above remain out of scope until a verified, mature builtin schema (or an explicitly pinned stable schema source) becomes available; downstream repositories MAY adopt them as additional `check-jsonschema` hooks at their discretion. See the [Built-in Schema Validation for Real Load-Bearing Configuration Files](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/.github/TEMPLATE_DESIGN_DECISIONS.md#design-decision-built-in-schema-validation-for-real-load-bearing-configuration-files) ADR for the durable "Evaluated but deferred" record covering each candidate.

## Out of Scope for This Worked Example

This directory ships one worked example schema and production schemas for the template sync manifest, marker, and instruction contracts. It does not introduce:

- Additional SchemaStore-backed validation hooks beyond the wired `vendor.dependabot` validation of `.github/dependabot.yml` (which lives in `.pre-commit-config.yaml`, not in this directory).
- Any JSONC, JSON5, or TOML schema validation tooling.

Additional schema-backed file families will be added in follow-up changes when concrete contracts are introduced or when downstream consumers decide to adopt them.
