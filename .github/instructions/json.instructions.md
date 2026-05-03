---
applyTo: "**/*.json,**/*.jsonc"
description: "JSON authoring standards: strict-by-default, schema-backed, deterministic, and secure."
---

<!-- markdownlint-disable MD013 -->

# JSON Writing Style

**Version:** 1.2.20260503.3

## Metadata

- **Status:** Active
- **Owner:** Repository Maintainers
- **Last Updated:** 2026-05-03
- **Scope:** Defines authoring standards for JSON and JSONC files in this repository, including configuration, schemas, fixtures, generated metadata, and machine-readable contracts. Covers dialect policy, formatting, key ordering, naming, data modeling, schema usage, comments, security, and generated output.
- **Related:** [Repository Copilot Instructions](../copilot-instructions.md), [`.gitattributes` Rules](./gitattributes.instructions.md), [YAML Writing Style](./yaml.instructions.md), [Schemas README](../../schemas/README.md), [Schema Example Tests (`tests/test_schema_examples.py`)](../../tests/test_schema_examples.py), [Data-File CI Workflow (`data-ci.yml`)](../workflows/data-ci.yml), [Template Design Decision — Dedicated JSON and YAML Instruction Files](../TEMPLATE_DESIGN_DECISIONS.md#design-decision-dedicated-json-and-yaml-instruction-files), [Template Design Decision — Baseline JSON/YAML Linting Stack](../TEMPLATE_DESIGN_DECISIONS.md#design-decision-baseline-jsonyaml-linting-stack), [Template Design Decision — Dedicated Data-File CI Workflow (`data-ci.yml`)](../TEMPLATE_DESIGN_DECISIONS.md#design-decision-dedicated-data-file-ci-workflow-data-ciyml), [Template Design Decision — JSON5 Exclusion by Default](../TEMPLATE_DESIGN_DECISIONS.md#design-decision-json5-exclusion-by-default), [Template Design Decision — `additionalProperties` Policy](../TEMPLATE_DESIGN_DECISIONS.md#design-decision-additionalproperties-policy), [Template Design Decision — Built-in Schema Validation for Real Load-Bearing Configuration Files](../TEMPLATE_DESIGN_DECISIONS.md#design-decision-built-in-schema-validation-for-real-load-bearing-configuration-files)

## Purpose and Scope

This guide establishes how JSON and JSONC files are authored in this repository. JSON is treated as a **machine-readable contract**: it MUST be unambiguous, deterministic, and safe to consume by tools and downstream automation.

The guide applies to every `.json` and `.jsonc` file in the repository, including configuration, schemas, fixtures, examples, policy documents, generated metadata, and any other JSON-shaped artifact, regardless of programming language or surrounding stack.

> **Note:** This document uses [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) keywords (**MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, **MAY**) to indicate requirement levels.

Line-ending pinning, BOM behavior, end-of-file newline, and trailing whitespace policy for JSON files are governed by [`.gitattributes` Rules](./gitattributes.instructions.md); this guide does not duplicate or override those rules.

## Quick Reference Checklist

- **[All]** `.json` files **MUST** be strict JSON; `.jsonc` **MAY** be used only when the consuming tool explicitly supports JSONC.
- **[All]** **MUST** use 2-space indentation; **MUST NOT** use tabs.
- **[All]** **MUST NOT** include trailing commas in strict JSON.
- **[All]** Keys and string values **MUST** be double-quoted.
- **[All]** **MUST NOT** blindly sort keys; **MUST** preserve intentional grouping and tool-managed ordering (for example, `package.json`, JSON/JSONC lockfiles, and other generated files).
- **[All]** Strict JSON **MUST NOT** contain comments.
- **[All]** Production or load-bearing JSON files **MUST** have schema validation; durable fixtures, examples, policy documents, and config contracts **SHOULD** have schema validation.
- **[All]** **MUST NOT** commit secrets; example values **MUST** be obviously fake.
- **[All]** Untrusted JSON **MUST** be validated before use and **MUST NOT** be evaluated as executable code.
- **[All]** Generated JSON **MUST** be reproducible and **SHOULD** identify its source or generation command.

## Dialect Policy

This repository recognizes two JSON dialects: strict JSON and JSONC. Other dialects are out of scope by default.

- Files with the `.json` extension **MUST** be strict JSON as defined by [RFC 8259](https://www.rfc-editor.org/rfc/rfc8259). Strict JSON **MUST NOT** contain comments, trailing commas, unquoted keys, single-quoted strings, or any other non-RFC 8259 syntax.
- Files with the `.jsonc` extension **MAY** be used **only** when the consuming tool explicitly documents support for JSONC (for example, the TypeScript compiler reading `tsconfig.json`, and some VS Code settings files). When in doubt, prefer `.json`.
- The repository's `check-json` pre-commit hook validates `.json` files only. JSONC is **not** validated by `check-json`. Downstream repositories that need stronger enforcement for `.jsonc` files **SHOULD** add JSONC-aware tooling (for example, a JSONC-aware parser, linter, or schema validator) rather than retrofitting `check-json`.
- JSON5 is **not** included in this repository's defaults and **MUST NOT** be introduced without an explicit, documented project decision. The `applyTo` glob for this guide intentionally omits `.json5`.

## Formatting

- Indentation **MUST** be 2 spaces per level. Tabs **MUST NOT** be used.
- Keys and string values **MUST** be double-quoted. Single quotes and unquoted keys **MUST NOT** be used (this is required by strict JSON and is also the recommended style for JSONC).
- Trailing commas **MUST NOT** appear in strict JSON. In JSONC files, trailing commas **MAY** be used only when the consuming tool documents support for them; otherwise they **SHOULD** be avoided to ease later conversion to strict JSON.
- Objects with more than one entry **SHOULD** use one key-value pair per line to keep diffs reviewable.
- Files **MUST** end with a single newline (enforced by the repository's `end-of-file-fixer` pre-commit hook). Line-ending and trailing-whitespace policy is governed by [`.gitattributes` Rules](./gitattributes.instructions.md).

**Example (strict JSON):**

```json
{
  "name": "example",
  "version": "1.0.0",
  "isEnabled": true
}
```

## Key Ordering

JSON does not assign semantic meaning to key order, but tools, humans, and diffs do. Treat key order as part of the file's contract.

- Most formatters, including Prettier, do not sort JSON keys by default. Do not assume any formatter will reorder keys for you.
- Keys **MUST NOT** be blindly sorted alphabetically across an entire file. Intentional grouping (for example, `name` before `version` in `package.json`, or `$schema` first in a schema-bearing file) **MUST** be preserved.
- Tool-managed and generated files **MUST NOT** be reordered by hand. This includes, but is not limited to:
  - `package.json` (npm/Yarn/pnpm reorder fields on install per their own rules)
  - `package-lock.json` and other JSON/JSONC lockfiles or generated manifests
  - Compiler/build tool JSON/JSONC manifests where the tool documents an ordering convention
- Generated files **SHOULD** preserve their generator's ordering exactly. If you need a different order, change the generator, not the output.
- Within a hand-authored object, related keys **SHOULD** be grouped (for example, all identity fields, then all behavior fields, then all metadata fields). New keys **SHOULD** be added next to related keys, not appended at the end "because diffs are smaller."

## Naming Conventions

- Object keys in project-owned JSON **SHOULD** use `camelCase` by default. Downstream repositories **MAY** adopt a different convention (for example, `snake_case` to match a Python-heavy stack) provided the choice is documented and applied consistently within that repository.
- JSON file names **SHOULD** use lowercase `kebab-case` (for example, `release-notes.json`, `feature-flags.json`). Ecosystem-mandated names (for example, `package.json`, `tsconfig.json`) **MUST** be used as-is.
- Boolean keys **SHOULD** use a clear affirmative prefix such as `is`, `has`, `can`, `should`, or `enable` (for example, `isEnabled`, `hasOwner`, `canRetry`, `shouldFail`, `enableTelemetry`). Negated booleans (for example, `isNotReady`) **SHOULD** be avoided to prevent double-negation in consumers.

## Data Modeling

- Prefer **explicit objects** over positional arrays for records. Use `{ "first": "...", "last": "..." }` rather than `["...", "..."]` so that field meaning is self-describing.
- Identifiers (IDs, account numbers, version numbers used as identifiers, ZIP codes) **MUST** be encoded as strings, not numbers. JSON numbers are IEEE 754 doubles and silently lose precision beyond 2^53; identifier-shaped numbers can also acquire leading-zero or formatting issues when round-tripped.
- Timestamps **MUST** be RFC 3339-compatible strings (for example, `"2026-05-01T12:34:56Z"`). Epoch integers **MAY** be used only when explicitly required by the consuming system and **SHOULD** be documented.
- Money and other exact-quantity values **SHOULD NOT** be encoded as JSON floats. Prefer either an integer in the smallest unit (for example, cents) or a decimal-as-string with a documented format and currency.
- Arrays **SHOULD** be homogeneous. Heterogeneous arrays **SHOULD** be replaced with arrays of tagged objects (for example, `[{ "kind": "...", ... }, ...]`).
- `null` **SHOULD** be used only when "absent or unknown" is a meaningful, documented state. Otherwise, omit the key.

## Schema Policy

JSON schemas make JSON contracts checkable. The amount of schema rigor SHOULD scale with the file's importance.

- **Production or load-bearing JSON files MUST have schema validation.** This includes any JSON consumed by build, deploy, runtime configuration, or release automation where a malformed value would cause incorrect behavior.
- **Durable fixtures, examples, policy documents, and config contracts SHOULD have schema validation.** A "durable" artifact is one that other code or other repositories depend on remaining shaped a certain way.
- **Simple tool-owned configs MAY rely on the owning tool's validator** (for example, `tsconfig.json` is validated by the TypeScript compiler; `.eslintrc.json` is validated by ESLint). A separate schema **SHOULD NOT** be added when it would only duplicate the tool's own validation.

Schema location and shape:

- Schemas **SHOULD** live under a root-level `schemas/` directory, not under `.github/schemas/`. Keeping schemas at the repository root makes them discoverable to downstream consumers and to non-Git tooling.
- Schema files **SHOULD** use the `.schema.json` suffix (for example, `schemas/feature-flags.schema.json`).
- [JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12/schema) **SHOULD** be the default `$schema`, unless a specific consumer requires an earlier draft (for example, an OpenAPI version pinned to Draft-07). The chosen draft **SHOULD** be stated in the schema's `$schema` field and called out in the schema's accompanying documentation when it is not Draft 2020-12.
- Project-owned **closed** schemas **SHOULD** set `"additionalProperties": false` so that unknown keys are caught early.
- Ecosystem-mirroring schemas (schemas that describe an external format the project does not own, for example, a third-party config) **MAY** leave additional properties open and **SHOULD** document why in the schema's `description` or in a sibling `README.md`.

Shipped JSON validation tooling in this repository:

- **`check-json`** — strict `.json` syntax validation, wired into [`.pre-commit-config.yaml`](../../.pre-commit-config.yaml) with an anchored `\.json$` pattern. JSONC files are intentionally excluded from `check-json`; downstream repositories that need stronger JSONC enforcement **SHOULD** add JSONC-aware tooling rather than retrofitting `check-json`.
- **`check-jsonschema`** — JSON Schema validation. Wired in today for (a) the worked-example schema (`schemas/example-config.schema.json`) and its valid example data files under `schemas/examples/example-config/valid/`, and (b) selected real load-bearing repository configuration files (for example, `.github/dependabot.yml`) validated against built-in vendor schemas shipped with `check-jsonschema`. See [`.pre-commit-config.yaml`](../../.pre-commit-config.yaml) for the authoritative list of active hooks. Add additional file-family-scoped hooks (project-owned `--schemafile` hooks for new schema-backed JSON families, or additional `--builtin-schema` hooks for tool-owned configuration files) as they are introduced.
- **`check-metaschema`** — self-validates the worked-example schema against its declared JSON Schema Draft 2020-12 metaschema.
- **Schema example tests** — [`tests/test_schema_examples.py`](../../tests/test_schema_examples.py) auto-discovers schema/example pairs under `schemas/` and asserts that valid examples pass and invalid examples fail. Invalid example fixtures are intentionally **not** wired into a `check-jsonschema` pre-commit hook (the hook would treat their expected failure as a hook failure); they are exercised exclusively through this test module.
- **Data-file CI** — [`.github/workflows/data-ci.yml`](../workflows/data-ci.yml) re-runs `check-json`, `check-yaml`, `yamllint`, `actionlint`, `check-jsonschema`, and `check-metaschema` so JSON and YAML enforcement can be made a required check via branch protection independent of the Python CI job.

See [Schemas README](../../schemas/README.md) for the worked example, the canonical downstream-removal checklist, and the future-work candidates that downstream repositories may opt into.

## Comments and Documentation

- Strict JSON **MUST NOT** contain comments of any kind, including `//` line comments, `/* ... */` block comments, dummy `"_comment"` keys used as a comment workaround, or trailing-string hacks. JSONC **MAY** contain comments only when the consuming tool documents support for them.
- Documentation about a JSON file's shape and meaning **SHOULD** live in the schema's `description` and `title` fields and in a sibling `README.md`, not in the JSON file itself.
- Inline rationale for individual fields **SHOULD** be expressed in the schema's `description` for that property, so it is discoverable by anyone who reads the schema or uses a schema-aware editor.

## Security

- Secrets (API keys, tokens, connection strings, passwords, signing keys) **MUST NOT** be committed in any JSON file, including examples, fixtures, and tests.
- Example values **MUST** be obviously fake (for example, `"REPLACE_ME"`, `"example-token-not-real"`, `"example-api-key-not-real"`). Fake values **SHOULD NOT** resemble real credentials closely enough to trigger secret scanners or to mislead a reader into thinking they are real.
- Untrusted JSON (input from network, user, or other untrusted source) **MUST** be parsed using a safe parser and **MUST** be validated against a schema or explicit type checks before its values are used.
- JSON input **MUST NOT** be evaluated as executable code. In particular, `eval`, `Function`, `exec`, `Invoke-Expression`, and equivalent constructs in any language **MUST NOT** be used to "parse" JSON.
- JSON consumers **SHOULD** apply size and depth limits to defend against pathological inputs (deeply nested objects, very large arrays, very long strings).

## Generated JSON

- Generation **MUST** be reproducible: re-running the generator on the same inputs **MUST** produce byte-identical output. This is what makes diffs meaningful and what allows generated JSON to be safely committed.
- Generated files **MUST** use stable formatting (consistent indentation, consistent quoting, consistent line endings). The producer **SHOULD** write files with LF line endings explicitly to interoperate with the repository's `.gitattributes` policy.
- Where ordering is non-semantic (for example, the order of keys in an object), the generator **MUST** apply a stable, documented ordering (for example, sorted by key, or grouped in a documented order). Where ordering **is** semantic (for example, an array of pipeline steps), the generator **MUST** preserve input order.
- Generated files **SHOULD** identify their source or generation command, either via a sibling `README.md` that names the generator, a top-level `"$generatedBy"` or similar property when the schema permits it, or a comment in the generator's own README. The identification **MUST NOT** violate the strict-JSON-no-comments rule: if the file is `.json`, use a property allowed by the schema or a sibling document, not an inline comment.

## Definition of Done for JSON Changes

A JSON change is considered done when **all** of the following hold:

- The file's dialect (strict JSON vs. JSONC) is correct for its extension and consumer.
- Formatting matches this guide (2-space indentation, no tabs, no trailing commas in strict JSON, double-quoted keys and strings).
- Key order is intentional: tool-managed and generated files have not been reordered by hand, and hand-authored objects preserve documented grouping.
- Naming follows the project's chosen convention (default `camelCase` for project-owned JSON; lowercase `kebab-case` filenames; affirmative boolean prefixes).
- Data modeling rules are followed: explicit objects over positional arrays, identifiers as strings, RFC 3339 timestamps, no floats for money or exact quantities.
- Schema validation is in place at the level required by the [Schema Policy](#schema-policy) tier.
- Strict JSON contains no comments; documentation lives in schemas and sibling docs.
- No secrets are committed; example values are obviously fake.
- Generated JSON is reproducible, stably formatted, stably ordered when ordering is non-semantic, and identifies its source or generation command.
- `check-json` and any project-specific JSON or JSONC validators pass; `check-jsonschema` and `check-metaschema` pass for any schema-backed file family wired into pre-commit (see [`.pre-commit-config.yaml`](../../.pre-commit-config.yaml) for the authoritative active-hook list); [`tests/test_schema_examples.py`](../../tests/test_schema_examples.py) passes after any schema or schema-example change; pre-commit and Markdown checks pass for any associated documentation changes.
