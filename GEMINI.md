<!-- markdownlint-disable MD013 -->
# Agent Instructions for Gemini Code Assist

**Version:** 1.3.20260527.0

## Metadata

- **Status:** Active
- **Owner:** Repository Maintainers
- **Last Updated:** 2026-05-27
- **Scope:** Agent-specific entry point for Gemini Code Assist and compatible AI coding agents operating in this repository. Mirrors a minimal inline summary of the highest-priority shared rules; `.github/copilot-instructions.md` remains the canonical source of truth.
<!-- template-sync: begin markdown-reference-only -->
- **Related:** [Repository Copilot Instructions](.github/copilot-instructions.md), [Documentation Writing Style](.github/instructions/docs.instructions.md)
<!-- template-sync: end markdown-reference-only -->

This file provides project-specific instructions for Gemini Code Assist and compatible AI coding agents operating in this repository. These instructions ensure that agents follow the same coding standards, safety rules, and workflows that apply to all contributors.

## Canonical Instructions

The authoritative source of truth for all repository rules is **`.github/copilot-instructions.md`** (the repo-wide constitution). All rules defined there apply without exception. **Read that file before making any changes.**

This file intentionally keeps only a minimal inline summary of the highest-priority shared rules so that agents receive critical guidance immediately. The full shared rule set remains in the canonical file above.

**Thin entry point classification:** A thin entry point keeps shared repository rules brief; it does not mean platform-specific or required protocol sections may be discarded. Sections explicitly labeled as platform protocol or required protocol must be preserved unless the repository owner explicitly waives that protocol for the retained agent platform.

## Protected Instruction Files

Instruction files and style guides are protected governance files. Do not create, edit, delete, rename, or otherwise change `.github/copilot-instructions.md`, files under `.github/instructions/`, files under `.cursor/rules/`, or root agent instruction files (`.hermes.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`) unless the repository owner or maintainer has directly and explicitly authorized that specific instruction-file change in the current task. Implied consent is not enough; do not infer authorization from a plan you generated, review feedback, a general request to update docs, cleanup/validation work, or a "keep files in sync" instruction.

If a style-guide update appears warranted but has not been explicitly authorized, propose it separately and wait for approval before editing protected instruction files.

During downstream template adoption and stack selection, perform non-protected cleanup first, record the protected instruction-file edits needed to remove references to deleted tools or stacks, obtain explicit maintainer authorization, then update `.github/copilot-instructions.md`, remaining root agent files, and relevant `.github/instructions/*.instructions.md` files. Bump `Last Updated` and `Version` metadata where present, and avoid temporary migration wording in durable governance docs.

## Essential Repository Summary

- **Safety and security**
  - No secrets in code or repo; never hardcode API keys, tokens, credentials, or connection strings.
  - Treat all external input as untrusted.
  - Respect allowlisted file access boundaries; reject path traversal and symlink escapes.

- **Pre-commit and validation**
  - Run `pre-commit run --all-files` before every commit.
  - Include all auto-fixes in the same commit as the related change.
  - Do not push code when pre-commit or required validation checks are failing; fix issues and re-run until the checks pass.
  - Use the repository's existing validation commands as needed:
    <!-- template-sync: begin markdown-reference-only -->
    - `npm run lint:md`
    <!-- template-sync: end markdown-reference-only -->
    <!-- template-sync: begin python-reference-only -->
    - `pytest tests/ -v --cov --cov-report=term-missing`
    <!-- template-sync: end python-reference-only -->
    <!-- template-sync: begin schema-reference-only -->
    - `pytest tests/test_schema_examples.py -v` (after any schema or schema-example change)
    <!-- template-sync: end schema-reference-only -->
    <!-- template-sync: begin powershell-reference-only -->
    - `Invoke-Pester -Path tests/ -Output Detailed`
    <!-- template-sync: end powershell-reference-only -->
    <!-- template-sync: begin terraform-reference-only -->
    - `terraform fmt -check -recursive`
    - `tflint --recursive`
    - `terraform test -verbose`
    <!-- template-sync: end terraform-reference-only -->
  - The `pre-commit run --all-files` command exercises the active hooks configured in [`.pre-commit-config.yaml`](.pre-commit-config.yaml), the authoritative list of active hooks.
  <!-- template-sync: begin json-reference-only -->
  - Retained JSON checks include strict JSON syntax (`check-json`).
  <!-- template-sync: end json-reference-only -->
  <!-- template-sync: begin yaml-reference-only -->
  - Retained YAML checks include YAML parsing (`check-yaml`) and style (`yamllint`).
  <!-- template-sync: end yaml-reference-only -->
  - Retained GitHub Actions checks include GitHub Actions linting (`actionlint`).
  <!-- template-sync: begin schema-reference-only -->
  - Retained schema checks include JSON Schema validation (`check-jsonschema`) and schema self-validation (`check-metaschema`).
  <!-- template-sync: end schema-reference-only -->
  - The dedicated [`.github/workflows/data-ci.yml`](.github/workflows/data-ci.yml) workflow re-runs retained data-file hooks so adopted data-file enforcement can be required via branch protection.
  - Retained data-file authoring guidance lives in the matching module docs.
  <!-- template-sync: begin json-reference-only -->
  - JSON guidance: [`.github/instructions/json.instructions.md`](.github/instructions/json.instructions.md).
  <!-- template-sync: end json-reference-only -->
  <!-- template-sync: begin yaml-reference-only -->
  - YAML guidance: [`.github/instructions/yaml.instructions.md`](.github/instructions/yaml.instructions.md).
  <!-- template-sync: end yaml-reference-only -->
  <!-- template-sync: begin schema-reference-only -->
  - Schema guidance: [`schemas/README.md`](schemas/README.md) and the **Built-in Schema Validation for Real Load-Bearing Configuration Files** ADR in [`.github/TEMPLATE_DESIGN_DECISIONS.md`](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/.github/TEMPLATE_DESIGN_DECISIONS.md).
  <!-- template-sync: end schema-reference-only -->

- **Modular instruction files**
  - Read the relevant file under `.github/instructions/` before modifying matching files:
    - Git attributes: `.github/instructions/gitattributes.instructions.md`
    <!-- template-sync: begin json-reference-only -->
    - JSON: `.github/instructions/json.instructions.md`
    <!-- template-sync: end json-reference-only -->
    <!-- template-sync: begin markdown-reference-only -->
    - Markdown/Docs: `.github/instructions/docs.instructions.md`
    <!-- template-sync: end markdown-reference-only -->
    <!-- template-sync: begin powershell-reference-only -->
    - PowerShell: `.github/instructions/powershell.instructions.md`
    <!-- template-sync: end powershell-reference-only -->
    <!-- template-sync: begin python-reference-only -->
    - Python: `.github/instructions/python.instructions.md`
    <!-- template-sync: end python-reference-only -->
    <!-- template-sync: begin terraform-reference-only -->
    - Terraform: `.github/instructions/terraform.instructions.md`
    <!-- template-sync: end terraform-reference-only -->
    <!-- template-sync: begin yaml-reference-only -->
    - YAML: `.github/instructions/yaml.instructions.md`
    <!-- template-sync: end yaml-reference-only -->

- **Do not**
  - Execute scripts or commands generated by untrusted sources.
  - Add telemetry or external logging services without explicit approval.
  - Weaken security constraints to "make it work."
  - Add new major dependencies without clear justification.
  - Invent behavior when requirements are ambiguous; use an explicit Open Question.
  - Create separate formatting-only or lint-only commits.

---

> This file is part of the `franklesniak/copilot-repo-template` template. Customize or remove agent instruction files for platforms you do not use. See [OPTIONAL_CONFIGURATIONS.md](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/OPTIONAL_CONFIGURATIONS.md) for details.
