<!-- markdownlint-disable MD013 -->

# Schemas

## Metadata

- **Status:** Active
- **Owner:** Repository Maintainers
- **Last Updated:** 2026-05-03
- **Scope:** Conventions for JSON Schemas that describe load-bearing JSON and YAML files in this repository, plus a clearly removable worked example (`example-config.schema.json` with valid and invalid example data) wired into pre-commit and data CI to demonstrate the schema-validation pipeline end to end.
- **Related:** [JSON Authoring Standards](../.github/instructions/json.instructions.md), [YAML Authoring Standards](../.github/instructions/yaml.instructions.md), [Repository Copilot Instructions](../.github/copilot-instructions.md), [Template Design Decisions — Schema Location at Repository Root](../.github/TEMPLATE_DESIGN_DECISIONS.md#design-decision-schema-location-at-repository-root), [Template Design Decisions — Schema Validation Tiers](../.github/TEMPLATE_DESIGN_DECISIONS.md#design-decision-schema-validation-tiers), [Template Design Decisions — Built-in Schema Validation for Real Load-Bearing Configuration Files](../.github/TEMPLATE_DESIGN_DECISIONS.md#design-decision-built-in-schema-validation-for-real-load-bearing-configuration-files), [Template Design Decisions — `additionalProperties` Policy](../.github/TEMPLATE_DESIGN_DECISIONS.md#design-decision-additionalproperties-policy), [Template Design Decisions — Testing Beyond Linting for JSON/YAML](../.github/TEMPLATE_DESIGN_DECISIONS.md#design-decision-testing-beyond-linting-for-jsonyaml)

## Purpose

This directory contains JSON Schemas for load-bearing JSON and YAML files in this repository. A "load-bearing" file is one whose shape is depended on by build, deploy, runtime, release automation, or downstream consumers, such that a malformed value would cause incorrect behavior.

Schemas live at the repository root (under `schemas/`, not `.github/schemas/`) so they are discoverable to IDEs, schema validators, and downstream consumers, and so projects that do not use schema-backed data files can opt out by deleting this directory.

## Template Portability

This template provides `schemas/` as a convention for repositories that adopt schema-backed JSON or YAML contracts. Downstream repositories MAY delete `schemas/` (including this `README.md`) if they do not use schema-backed data files.

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
- `$id` — a stable, absolute URI that identifies the schema.
- `title` — a short, human-readable name for the contract.
- `description` — a concise explanation of what the schema describes and which files it applies to.

### Object Schemas

Schemas whose root type is `object` SHOULD define:

- `type: "object"`
- `required` — the list of properties that MUST be present.
- `properties` — the typed shape of each known property.

### Open vs. Closed Contracts

- Project-owned closed contracts SHOULD set `"additionalProperties": false` so that unknown keys are caught early.
- Ecosystem-mirroring schemas (schemas that describe an external format the project does not own, for example a third-party config) MAY leave additional properties open and SHOULD document why in the schema's `description` or in this `README.md`.

## Validation

Schema-backed files are validated by pre-commit and the dedicated data-file CI workflow ([`.github/workflows/data-ci.yml`](../.github/workflows/data-ci.yml)). This template ships a worked example (see [Worked Example](#worked-example) below) so the validation pipeline is exercised end to end out of the box. Downstream repositories that do not use schema-backed data files SHOULD remove the worked example using the [Downstream Removal Checklist](#downstream-removal-checklist). See the JSON authoring standards for the schema-validation policy and tier guidance.

### Schema Categories

This repository distinguishes two schema categories. The distinction matters for where schemas live, how they are tested, and how they are wired into pre-commit and CI.

1. **Project-owned schemas.**
   - Stored under `schemas/` in this repository.
   - MAY include valid and invalid example fixtures under `schemas/examples/<schema-name>/{valid,invalid}/`.
   - Tested by [`tests/test_schema_examples.py`](../tests/test_schema_examples.py), which auto-discovers schema/example pairs and asserts that valid examples pass and invalid examples fail.
   - Wired into pre-commit by adding a `check-jsonschema` hook that points at the schema with `--schemafile schemas/<name>.schema.json` and an anchored `files:` pattern matching the file family the schema covers.
   - The [Worked Example](#worked-example) below is the canonical illustration of this category.

2. **External built-in schemas.**
   - Referenced through `check-jsonschema --builtin-schema vendor.<name>` against schemas that ship inside the pinned `check-jsonschema` release.
   - **Not vendored** into this repository. Schema content tracks `check-jsonschema` upstream releases and is updated through the Dependabot `pre-commit` ecosystem.
   - Used for selected real, load-bearing repository configuration files where the external schema is mature and validation is low-noise.
   - See the [Built-in Schema Validation for Real Load-Bearing Configuration Files](../.github/TEMPLATE_DESIGN_DECISIONS.md#design-decision-built-in-schema-validation-for-real-load-bearing-configuration-files) ADR for the policy, the full list of selected files, and the explicit "Evaluated but deferred" negative-space record.

The two categories are complementary. A downstream repository MAY use either, both, or neither.

### Real Repository Configuration Files Validated Through Built-in Schemas

The following real, load-bearing repository configuration files are validated by default through `check-jsonschema --builtin-schema ...` hooks in [`.pre-commit-config.yaml`](../.pre-commit-config.yaml):

| File | Built-in schema identifier |
| --- | --- |
| [`.github/dependabot.yml`](../.github/dependabot.yml) | `vendor.dependabot` |

If a downstream repository deletes one of these files, it **MUST** also remove the corresponding `check-jsonschema` hook (and any matching `data-ci.yml` step) per the [downstream removal guidance in the ADR](../.github/TEMPLATE_DESIGN_DECISIONS.md#design-decision-built-in-schema-validation-for-real-load-bearing-configuration-files).

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
import pytest

CHECK_JSONSCHEMA = shutil.which("check-jsonschema")


@pytest.mark.skipif(
    CHECK_JSONSCHEMA is None,
    reason="check-jsonschema is not installed in this environment",
)
def test_invalid_example_is_rejected():
    result = subprocess.run(
        [
            CHECK_JSONSCHEMA,
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

The same shape applies in PowerShell, Bash, or any CI step: invoke the validator on the invalid fixture and assert a non-zero exit.

A starter version of this pattern lives at [`templates/python/tests/test_schema_examples.py`](../templates/python/tests/test_schema_examples.py); the active, canonical version that this repository runs in CI lives at [`tests/test_schema_examples.py`](../tests/test_schema_examples.py). Both auto-discover schema/example pairs under `schemas/`. The starter retains a `skipif` guard so it remains safe to copy into downstream projects that have not yet added `check-jsonschema` to their dev/test dependencies.

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

### Downstream Removal Checklist

The worked example is intentionally easy to remove. To take it out of a downstream repository:

1. Delete [`schemas/example-config.schema.json`](./example-config.schema.json).
2. Delete the [`schemas/examples/example-config/`](./examples/example-config/) directory and all of its contents.
3. Remove the `Validate example-config valid examples` and `Self-validate example-config schema` hooks (and the surrounding `python-jsonschema/check-jsonschema` repo block, if no other hooks from that repo remain) from [`.pre-commit-config.yaml`](../.pre-commit-config.yaml).
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

`.github/dependabot.yml` is already validated by default; see the [Real Repository Configuration Files Validated Through Built-in Schemas](#real-repository-configuration-files-validated-through-built-in-schemas) section above. The candidates above remain out of scope until a verified, mature builtin schema (or an explicitly pinned stable schema source) becomes available; downstream repositories MAY adopt them as additional `check-jsonschema` hooks at their discretion. See the [Built-in Schema Validation for Real Load-Bearing Configuration Files](../.github/TEMPLATE_DESIGN_DECISIONS.md#design-decision-built-in-schema-validation-for-real-load-bearing-configuration-files) ADR for the durable "Evaluated but deferred" record covering each candidate.

## Out of Scope for This Worked Example

This directory ships exactly one worked example schema and its example data so the validation pipeline is observable end to end. It does not introduce:

- Any production schema for this repository's own load-bearing files.
- Additional SchemaStore-backed validation hooks beyond the wired `vendor.dependabot` validation of `.github/dependabot.yml` (which lives in `.pre-commit-config.yaml`, not in this directory).
- Any JSONC, JSON5, or TOML schema validation tooling.

Those will be added in follow-up changes when concrete schema-backed file families are introduced or when downstream consumers decide to adopt them.
