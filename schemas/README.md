<!-- markdownlint-disable MD013 -->

# Schemas

## Metadata

- **Status:** Active
- **Owner:** Repository Maintainers
- **Last Updated:** 2026-05-01
- **Scope:** Conventions for JSON Schemas that describe load-bearing JSON and YAML files in this repository. Does not define any specific schema; this directory is a scaffold.
- **Related:** [JSON Authoring Standards](../.github/instructions/json.instructions.md), [YAML Authoring Standards](../.github/instructions/yaml.instructions.md), [Repository Copilot Instructions](../.github/copilot-instructions.md)

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

Schema-backed files SHOULD be validated by pre-commit and CI once real schemas and matching file families exist in this repository. Until then, this directory is a scaffold only and no schema validation hook is wired into pre-commit by default. See the JSON authoring standards for the schema-validation policy and tier guidance.

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
  schemas/examples/project-config.valid.json
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
            "schemas/examples/project-config.invalid.json",
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

A reusable, opt-in template version of this pattern lives at [`templates/python/tests/test_schema_examples.py`](../templates/python/tests/test_schema_examples.py). It safely skips when `check-jsonschema` is unavailable so that it does not break environments that have not opted in to schema validation.

## Out of Scope for This Scaffold

This `README.md` documents conventions only. It does not introduce:

- Any actual schema files.
- Any example data files under `schemas/examples/`.
- Any pre-commit or CI validation hooks for schema-backed files.

Those will be added in follow-up changes when concrete schema-backed file families are introduced.
