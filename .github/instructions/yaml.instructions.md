---
applyTo: "**/*.yml,**/*.yaml"
description: "YAML authoring standards: explicit, conservative, schema-backed, and safe."
---

<!-- markdownlint-disable MD013 -->

# YAML Writing Style

**Version:** 1.2.20260503.2

## Metadata

- **Status:** Active
- **Owner:** Repository Maintainers
- **Last Updated:** 2026-05-03
- **Scope:** Defines authoring standards for all YAML files in this repository, including GitHub Actions workflows, pre-commit configuration, linter configuration, and any other human-authored YAML configuration. Does not cover JSON files (covered by [JSON Writing Style](./json.instructions.md)) or generated YAML artifacts that are owned by another tool's serializer.
- **Related:** [Repository Copilot Instructions](../copilot-instructions.md), [`.gitattributes` Rules](./gitattributes.instructions.md), [JSON Writing Style](./json.instructions.md), [`.yamllint.yml`](../../.yamllint.yml), [Data-File CI Workflow (`data-ci.yml`)](../workflows/data-ci.yml), [Schemas README](../../schemas/README.md), [Schema Example Tests (`tests/test_schema_examples.py`)](../../tests/test_schema_examples.py), [Template Design Decision — Dedicated JSON and YAML Instruction Files](../TEMPLATE_DESIGN_DECISIONS.md#design-decision-dedicated-json-and-yaml-instruction-files), [Template Design Decision — Baseline JSON/YAML Linting Stack](../TEMPLATE_DESIGN_DECISIONS.md#design-decision-baseline-jsonyaml-linting-stack), [Template Design Decision — yamllint truthy.check-keys Default](../TEMPLATE_DESIGN_DECISIONS.md#design-decision-yamllint-truthycheck-keys-default), [Template Design Decision — yamllint line-length Warning Level Default](../TEMPLATE_DESIGN_DECISIONS.md#design-decision-yamllint-line-length-warning-level-default), [Template Design Decision — Dedicated Data-File CI Workflow (`data-ci.yml`)](../TEMPLATE_DESIGN_DECISIONS.md#design-decision-dedicated-data-file-ci-workflow-data-ciyml), [Template Design Decision — Prettier Deferral for Data Files](../TEMPLATE_DESIGN_DECISIONS.md#design-decision-prettier-deferral-for-data-files)

## Purpose and Scope

YAML in this repository is the preferred format for **human-authored configuration** that benefits from comments, multi-line strings, and a forgiving syntax for editors (workflow files, pre-commit configs, linter configs, application config files committed to source control). JSON is preferred for **strict machine interchange** and for **generated artifacts** (lock files, schema documents, tool outputs, structured data exchanged between systems).

To keep YAML safe to edit, easy to diff, and portable across parsers, this repository adopts a **conservative, tool-friendly subset** of YAML 1.2. Authors **MUST** prefer explicit, unambiguous constructs over clever or compact YAML features that vary by parser.

> **Note:** This document uses [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) keywords (**MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, **MAY**) to indicate requirement levels.

## Quick Reference Checklist

- **[All]** **MUST** use 2-space indentation; **MUST NOT** use tabs.
- **[All]** **MUST** use block style by default; **SHOULD NOT** use flow style for non-trivial structures.
- **[All]** **MUST** use lowercase `true`, `false`, and `null`; **MUST NOT** use `yes`/`no`/`on`/`off` (or capitalized variants) as booleans.
- **[All]** **MUST** quote values that could be misparsed as booleans, nulls, numbers, dates, or YAML 1.1 truthy tokens.
- **[All]** **MUST** quote version pins (for example, `"3.13"`, `"1.0"`) so they cannot be coerced to numbers.
- **[All]** **SHOULD** use double quotes only when escape sequences are needed; **SHOULD** use single quotes for literal regexes and Windows paths.
- **[All]** **SHOULD** use block scalars (`|`, `>`, `|-`, `>-`) for multi-line strings.
- **[All]** **SHOULD NOT** use anchors, aliases, merge keys, custom tags, or multi-document files unless required and supported by the consumer.
- **[All]** **MUST NOT** commit secrets in YAML.
- **[Actions]** **MUST** apply least-privilege `permissions:` on GitHub Actions workflows.
- **[Schemas]** Schema-backed YAML **MUST** pass any schema validator wired into pre-commit or CI; where no validator is wired up for a particular file family, authors **SHOULD** run the appropriate validator locally before committing.
- **[Naming]** YAML filenames **SHOULD** be lowercase kebab-case; GitHub Actions workflows **MUST** use the `.yml` extension; project-owned YAML **MUST** choose `.yml` or `.yaml` and use it consistently.

## Dialect and Consumer Policy

- Authors **SHOULD** target **YAML 1.2-compatible** values and avoid relying on parser-specific extensions.
- Authors **MUST** avoid the YAML 1.1 *non-lowercase-`true`/`false`* truthy tokens that this guide does not permit as booleans (`y`, `Y`, `yes`, `Yes`, `YES`, `n`, `N`, `no`, `No`, `NO`, `on`, `On`, `ON`, `off`, `Off`, `OFF`, `True`, `TRUE`, `False`, `FALSE`); only lowercase `true` and `false` are allowed as booleans (see "Booleans, Nulls, and Numbers"). Many widely-deployed parsers (including those used by GitHub Actions, `js-yaml` defaults, and some legacy PyYAML configurations) still resolve some or all of these YAML 1.1 tokens as booleans, so any string value that would otherwise match one of them **MUST** be quoted.
- Ecosystem-specific validators (for example, Kubernetes manifest validators, OpenAPI validators, Helm validators, Ansible validators) **SHOULD** be adopted only when the repository actually uses those ecosystems. Generic YAML guidance **MUST NOT** require validators that are irrelevant to the repository's stack. The shipped baseline (`check-yaml`, `yamllint`, `actionlint`, and `check-jsonschema` for the worked-example schema) is described in [Schema-backed YAML](#schema-backed-yaml).

## Formatting Rules

- Indentation **MUST** be exactly **2 spaces** per level. Tabs **MUST NOT** appear in YAML files.
- Block style **MUST** be the default for mappings and sequences. Flow style (`{key: value}`, `[a, b, c]`) **MAY** be used only for short, obviously-bounded inline values where block style would be visually disruptive.
- Document separators (`---`, `...`) **SHOULD NOT** appear in single-document files. Multi-document YAML files **MAY** use `---` separators when the consumer requires multi-document input (for example, Kubernetes manifest bundles) or when the file format mandates a leading `---`.
- Files **SHOULD NOT** contain trailing whitespace and **SHOULD** end with a single newline. Line-ending, BOM, EOF newline, and trailing-whitespace policy at the Git layer is owned by [`.gitattributes` Rules](./gitattributes.instructions.md); this guide does not duplicate or contradict it.

## Quoting Rules

Authors **MUST** quote any scalar that a YAML 1.2 (or YAML 1.1) parser could resolve as a non-string type when a string is intended. In particular:

- Values that match boolean, null, integer, float, hex, octal, binary, or sexagesimal patterns when a string is intended.
- Values that match RFC 3339 / ISO 8601 timestamp patterns when intended as strings, **unless** the specific parser's behavior is known and tested for that value.
- Values that match any YAML 1.1 truthy token (see "Dialect and Consumer Policy" above) when a string is intended.
- Values that begin with YAML special syntax characters (`&`, `*`, `!`, `|`, `>`, `%`, `@`, the backtick character, `#`, `,`, `[`, `]`, `{`, `}`, `?`, `:` followed by space) where the parser would otherwise interpret them.

Version pins **MUST** be quoted. Common examples:

```yaml
python-version: "3.13"
api-version: "1.0"
node-version: "20"
```

Without quotes, `3.13` is parsed as the float `3.13` (which compares equal to `3.130`), `1.0` is parsed as the float `1.0` (which loses the trailing zero), and `20` is parsed as the integer `20`.

Quote style guidance:

- Use **double quotes** when escape sequences are required (for example, `"line1\nline2"`, `"tab\there"`).
- Use **single quotes** for literal regular expressions, Windows paths, and other strings that contain backslashes intended literally (for example, `'C:\Users\runner'`, `'^v\d+\.\d+\.\d+$'`).
- Use **block scalars** (`|`, `>`, `|-`, `>-`) for multi-line strings instead of long quoted scalars with embedded `\n` sequences.

## Booleans, Nulls, and Numbers

- The only booleans that **MUST** appear in YAML are lowercase `true` and `false`.
- The only null literal that **MUST** appear is lowercase `null`. Authors **MAY** omit a value entirely when the consumer treats absent and null identically; otherwise, write `null` explicitly.
- Authors **MUST NOT** use `yes`, `no`, `on`, `off`, `True`, `False`, `TRUE`, or `FALSE` as booleans.
- Numbers intended as numbers **SHOULD** be written without quotes. Numbers intended as **strings** (version pins, ZIP codes, account IDs, leading-zero identifiers) **MUST** be quoted.

## GitHub Actions `on:` Key

The GitHub Actions workflow trigger key `on:` is a well-known YAML 1.1 truthy hazard. Under YAML 1.1 resolution rules, the unquoted bare key `on` is parsed as the boolean `true`. GitHub Actions itself parses workflows correctly because it does not rely on YAML 1.1 truthy resolution for keys, but **lint tooling** that is YAML 1.1-aware (notably `yamllint`'s `truthy` rule) will flag the `on:` key as a truthy violation by default.

This repository ships a [`yamllint` configuration at `.yamllint.yml`](../../.yamllint.yml) that intentionally sets `truthy.check-keys: false` so that the idiomatic GitHub Actions `on:` key is preserved without per-file exception comments:

```yaml
rules:
  truthy:
    check-keys: false
```

This configuration preserves the idiomatic GitHub Actions `on:` key while still flagging YAML 1.1 truthy hazards in **values**. Authors **MAY** alternatively quote the key as `"on":` to satisfy a stricter `truthy.check-keys: true` configuration, but this form is **non-idiomatic** in the GitHub Actions ecosystem and **SHOULD NOT** be adopted unless a downstream policy requires it.

## Conservative YAML Subset

To maximize portability across parsers and to keep diffs reviewable, authors **SHOULD NOT** use the following YAML features unless the consumer documents support for them and a reviewer has confirmed the construct is necessary:

- Anchors (`&name`) and aliases (`*name`)
- Merge keys (`<<: *name`)
- Custom or explicit tags (`!!str`, `!CustomTag`, `!!python/object`)
- Flow style for non-trivial mappings or sequences
- Multi-document files with multiple `---` separators
- Directives other than the implicit `%YAML 1.2`

When these features are necessary (for example, a tool's configuration format genuinely requires anchors), the YAML file **SHOULD** include a brief comment explaining why the feature is used.

## Multi-line Strings

For multi-line string values, authors **SHOULD** use YAML block scalars rather than embedding `\n` in quoted strings:

- `|` — literal block scalar; preserves newlines, keeps a single trailing newline.
- `>` — folded block scalar; folds line breaks within paragraphs into spaces, keeps a single trailing newline.
- `|-` — literal block scalar with strip chomping; preserves newlines, removes the trailing newline.
- `>-` — folded block scalar with strip chomping; folds and strips the trailing newline.

Choose the indicator that matches the consumer's expectations. When passing a multi-line string to a shell (for example, a workflow `run:` step), `|` is almost always the correct choice.

## Naming Conventions

- YAML filenames **SHOULD** use **lowercase kebab-case** (for example, `release-please.yml`, `pre-commit-config.yaml`).
- GitHub Actions workflow files in `.github/workflows/` **MUST** use the `.yml` extension. GitHub Actions accepts both `.yml` and `.yaml`, but this repository standardizes on `.yml` for workflows for consistency with the existing tree.
- Project-owned YAML files outside `.github/workflows/` **MUST** pick **one** of `.yml` or `.yaml` and use it consistently within a project. Tool-owned configuration files **MUST** use whatever extension the tool requires (for example, `.pre-commit-config.yaml`).

## Comments

- YAML comments (lines beginning with `#` after optional whitespace) are **allowed and encouraged** for non-obvious configuration choices.
- Comments **SHOULD** explain **why** a value is set the way it is, not **what** the value is. Restating the literal value adds noise without information.
- Comments **MUST NOT** be the only place where behavior is described. If a configuration value's correctness depends on context, that context **MUST** also be captured somewhere a reader will see (in linked documentation, in the surrounding configuration block, or in the consuming code).

## Schema-backed YAML

YAML files that have a published schema **SHOULD** be validated against that schema, using the same MUST/SHOULD/MAY tiers applied to JSON in [JSON Writing Style](./json.instructions.md). This repository wires schema and ecosystem validators into pre-commit and re-runs them in [`.github/workflows/data-ci.yml`](../workflows/data-ci.yml); files covered by those hooks **MUST** pass them. For file families that do not yet have a hook configured, authors **SHOULD** run the appropriate validator locally before committing. The shipped pipeline is described below; CI/pre-commit integration is owned by the repository's tooling configuration rather than by this guide.

Validation tiers:

- **MUST tier** (files whose schema validator is wired into pre-commit or CI **MUST** pass it; where the validator is not wired up, authors **SHOULD** run it locally before committing): GitHub Actions workflows (`.github/workflows/*.yml`); pre-commit configuration (`.pre-commit-config.yaml`); any YAML file whose schema is published and stable and whose consumer requires structural correctness.
- **SHOULD tier**: linter configuration files (for example, `.yamllint.yml`) when a schema is available and a validator is convenient to run.
- **MAY tier**: optional or experimental configuration formats whose schema may change.

Shipped validators in this repository (extend as needed for new ecosystems):

- **`yamllint`** — YAML style enforcement, configured in [`.yamllint.yml`](../../.yamllint.yml) and run through [`.pre-commit-config.yaml`](../../.pre-commit-config.yaml) and [`.github/workflows/data-ci.yml`](../workflows/data-ci.yml).
- **`check-yaml`** (from `pre-commit/pre-commit-hooks`) — parse-checks YAML files; runs through pre-commit and `data-ci.yml`.
- **`actionlint`** — GitHub Actions workflow linter; runs through pre-commit and `data-ci.yml` for any workflow file under `.github/workflows/`.
- **`check-jsonschema`** — generic JSON Schema validation for YAML and JSON files. Used today for the worked-example schema (`schemas/example-config.schema.json`); add file-family-scoped hooks for additional schema-backed YAML as needed.

Additional ecosystem-specific validators (for example, `kubeval`/`kubeconform` for Kubernetes, `helm lint` for Helm charts, `ansible-lint` for Ansible) **SHOULD** be adopted **only** when the repository actually uses the ecosystem. Generic YAML guidance **MUST NOT** mandate validators for ecosystems the repository does not use.

## Security

- YAML files **MUST NOT** contain committed secrets (API keys, tokens, passwords, connection strings, private keys). Reference secrets through the consumer's secret-management mechanism (for example, GitHub Actions `secrets.*`, environment variables, external secret stores).
- GitHub Actions workflows **MUST** declare **least-privilege** `permissions:` blocks at the workflow or job level. Workflows **SHOULD** start from `permissions: {}` (or `contents: read`) and grant additional scopes only where required.
- YAML loaded by application code **MUST** use a **safe loader**. In Python, this means `yaml.safe_load` (or `yaml.load(..., Loader=yaml.SafeLoader)`); authors **MUST NOT** call `yaml.load` with `Loader=yaml.FullLoader` or `Loader=yaml.UnsafeLoader` on untrusted input, and **MUST NOT** call `yaml.load` without an explicit safe `Loader=` argument (calling `yaml.load` without `Loader=` raises a warning in modern PyYAML and historically defaulted to the unsafe full loader). Equivalent safe-loading APIs **MUST** be used in other languages.
- Custom or unsafe deserialization tags (for example, `!!python/object`, `!!python/object/apply`, `!ruby/object`) **MUST NOT** appear in YAML files in this repository, and the loaders that read those files **MUST NOT** be configured to honor such tags.

## Definition of Done for YAML Changes

A YAML change is "done" when **all** of the following are true:

- The file follows the formatting rules above (2-space indentation, no tabs, block style by default, no trailing whitespace, single trailing newline).
- All scalars that need quoting per "Quoting Rules" are quoted; all version pins are quoted.
- All booleans are lowercase `true` / `false`; no `yes`/`no`/`on`/`off` as boolean values.
- The conservative subset is respected (no anchors, aliases, merge keys, custom tags, multi-document files, or flow style except where necessary and justified).
- Comments explain **why**, not **what**; behavior is not documented only in comments.
- `yamllint` (configured in [`.yamllint.yml`](../../.yamllint.yml)) and `check-yaml` pass under the repository's pre-commit configuration.
- Any schema or ecosystem validator wired into pre-commit or CI passes for the affected files (for example, `actionlint` for workflow files, `check-jsonschema` for schema-backed YAML covered by an active hook). When no such validator is wired up for the file family being changed, authors **SHOULD** run the applicable validator locally before committing.
- Pre-commit hooks pass locally (`pre-commit run --all-files`) and in CI, including the dedicated [`.github/workflows/data-ci.yml`](../workflows/data-ci.yml) data-file workflow.
- No secrets are committed; GitHub Actions workflows declare least-privilege `permissions:`.
