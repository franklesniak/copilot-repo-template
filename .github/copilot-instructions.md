<!-- markdownlint-disable MD013 -->
# Repository Copilot Instructions (Repo-Wide Constitution)

**Version:** 1.4.20260503.1

## Metadata

- **Status:** Active
- **Owner:** Repository Maintainers
- **Last Updated:** 2026-05-03
- **Scope:** Repo-wide canonical instructions ("constitution") that govern all changes in this repository. This file is the authoritative source of truth for repository rules; all language-specific instruction files and agent entry points defer to it.
- **Related:** [Documentation Writing Style](instructions/docs.instructions.md)

These instructions are authoritative for all changes in this repository.

## Source of Truth

> **Customize this section** for your project. Point to your authoritative specification or design document. Example:
>
> - Read **`docs/spec/requirements.md`** before making changes.
> - If any instruction here conflicts with the spec, **the spec wins**.

## Non-negotiable Safety and Security Rules

1. **No secrets in code or repo**
   - Never hardcode API keys, tokens, connection strings, or credentials.
   - Do not introduce `.env` files or secret placeholders that look like real keys.
   - Never print secrets to stdout/stderr or logs.

2. **Treat all external input as untrusted**
   - Never execute untrusted outputs or commands.
   - Validate and sanitize all inputs at boundaries.
   - Never allow external input to influence file/network access beyond explicitly implemented adapters.

3. **Allowlisted file access only**
   - Read only explicitly allowed inputs/config/rules files and tool-owned runtime dependencies.
   - Refuse path traversal and symlink escapes.

## Pre-commit Discipline (CRITICAL)

**⚠️ ALWAYS run pre-commit checks before committing code.**

Pre-commit hooks are NOT optional. They enforce:

- Code formatting
- Linting
- Trailing whitespace removal
- End-of-file fixes

**Workflow:**

1. Make your code changes
2. Run pre-commit checks locally (e.g., `pre-commit run --all-files` or `npm run lint:md`)
3. Review and commit ALL auto-fixes as part of your change
4. Push to GitHub

**If pre-commit CI fails after a push:**

1. Pull the latest branch
2. Run pre-commit checks locally and review the fixes
3. Add the fixes to commit history before pushing again: prefer amending the commit(s) that introduced the failures, or include the fixes in your next substantive commit on the same branch, rather than landing a standalone formatting-only or lint-only commit (see "What Not to Do" below). For `copilot/**` branches, the auto-fix workflow described under "Auto-Fix Workflow (Safety Net for Copilot Branches)" will normally apply these fixes automatically.
4. Push again (force-push if you amended or rebased earlier commits)

**CI is a safety net, not a substitute for local checks.**

### Data-File Validation

In addition to formatting, linting, trailing-whitespace, and end-of-file fixes, pre-commit also enforces validation for structured data files. Run `pre-commit run --all-files` to execute the full hook set, which includes:

- `check-json` — validates strict `.json` syntax. **Note:** `check-json` does **not** validate `.jsonc`; JSONC (JSON with comments) is allowed only when supported by the consuming tool, and stricter enforcement requires JSONC-aware tooling.
- `check-yaml` — parse-checks `.yml` / `.yaml` files.
- `yamllint` — enforces YAML style per `.yamllint.yml`.
- `actionlint` — lints GitHub Actions workflow files.

Prettier is **opt-in** and is **not** part of the default data-file toolchain.

> **Schema validation (worked example only).** `check-jsonschema` is wired into `.pre-commit-config.yaml` to validate the worked-example schema shipped at `schemas/example-config.schema.json` and its valid example data under `schemas/examples/example-config/valid/`, plus a self-validation hook (`check-metaschema`) for the schema itself. The dedicated [`.github/workflows/data-ci.yml`](workflows/data-ci.yml) workflow re-runs the same data-file hooks (`check-json`, `check-yaml`, `yamllint`, `actionlint`, `check-jsonschema`, `check-metaschema`) so JSON/YAML/Actions enforcement can be made a required check via branch protection independent of the Python CI job. The contract that valid examples pass and invalid examples fail is exercised by [`tests/test_schema_examples.py`](../tests/test_schema_examples.py); run `pytest tests/test_schema_examples.py -v` after any schema or fixture change. See [`schemas/README.md`](../schemas/README.md) for the worked example, the canonical downstream removal checklist, and future-work candidates. Downstream repositories MAY add additional `check-jsonschema` hook entries for their own schema-backed file families.
>
> **When schema contracts change**, agents updating any schema **MUST** keep the following in sync in the same change:
>
> - The schema file under `schemas/<name>.schema.json`.
> - Valid example fixtures under `schemas/examples/<name>/valid/`.
> - Invalid example fixtures under `schemas/examples/<name>/invalid/`.
> - The pre-commit hook scope in `.pre-commit-config.yaml`.
> - `.github/workflows/data-ci.yml` only when **adding or removing a hook ID** (for example, introducing a new `check-yaml-custom` hook). Changes to an **existing** hook's `files:` regex (including `check-jsonschema` scope changes) are picked up automatically, because each `data-ci.yml` step invokes hooks by ID via `pre-commit run <hook-id> --all-files`.
> - Any documentation that references the schema (for example, `schemas/README.md`, `README.md`, `OPTIONAL_CONFIGURATIONS.md`).

### For GitHub Copilot Coding Agent (Automated PRs)

**⚠️ CRITICAL: You are an automated agent creating PRs. You MUST follow this workflow:**

When creating automated PRs, you **MUST**:

1. Run all linting/formatting checks as the **FINAL step** before each commit
2. Include **ALL** auto-fixes in the **SAME commit** with your code changes
3. **NEVER** push code that will fail pre-commit CI
4. If pre-commit fails, fix issues and re-run until all checks pass

**The pre-commit step is NON-NEGOTIABLE for automated PRs.**

If you encounter issues:

- Do NOT create a separate "fix formatting" commit
- Do NOT push and wait for CI to fail
- Fix locally, include in your commit, then push

**Failure to follow this will cause CI failures and require manual intervention.**

### Auto-Fix Workflow (Safety Net for Copilot Branches)

This repository includes an auto-fix workflow (`.github/workflows/auto-fix-precommit.yml`) that automatically runs pre-commit hooks and commits fixes for `copilot/**` branches. This serves as a safety net when the Copilot Coding Agent pushes code that fails pre-commit checks.

**How it works:**

- Triggers only on `push` events to `copilot/**` branches
- Only runs when the pusher is `copilot-swe-agent[bot]` (prevents infinite loops)
- Automatically commits any auto-fixes with message `chore: Apply pre-commit auto-fixes [automated]`
- Uses `github-actions[bot]` identity for commits

**Important notes:**

- This is a **safety net**, not a substitute for running pre-commit locally
- Agents should still try to run pre-commit checks before pushing when possible
- The workflow only applies to `copilot/**` branches—human branches are not affected
- Manual intervention may still be required for issues that cannot be auto-fixed

## Repository Self-Containment

All files committed to this repository MUST be interpretable—meaning understandable to a reader without access to private or internal resources—using only the contents of this repository and public references that are clearly linked from it.

This rule governs the meaning of documentation, code comments, and embedded references. It does not require the repository to build or run without standard external dependencies declared in its manifests (for example, package, module, or action dependencies pinned in `requirements.txt`, `package.json`, Terraform `required_providers`, or workflow `uses:` entries).

It applies to, but is not limited to:

- `README.md` and other top-level `*.md` files.
- Files under `.github/`, including workflows, instructions, and design-decision docs.
- Code comments embedded in committed files.

Do not embed references to:

- Work stream identifiers, sprint names, milestone labels, or phase numbers that are not defined inside this repository.
- Ticket, issue, or project IDs that resolve only inside a private or external tracker.
- Internal team, person, or communication-channel names.
- Roadmap, design, or planning documents that are not published in this repository or otherwise publicly resolvable from links in this repository.

Where a future-extension hook needs to be described, phrase the condition in repository-observable terms. For example, prefer "Once concrete schemas are added under `schemas/` and a `check-jsonschema` hook is enabled in `.pre-commit-config.yaml`, ..." rather than referencing the work stream that will introduce those changes.

If a needed reference cannot be expressed in repository-observable terms, follow the existing **What Not to Do** guidance and open an issue or add an explicit "Open Question" in the affected file instead of inventing or importing an external reference.

## Determinism and Correctness Rules

- Prefer deterministic tooling over manual rewriting.
- Sanitation pipelines must be bounded (iteration caps, no-progress detection).
- Preserve formatting, indentation, and ordering when processing structured content.
- Concurrency is allowed, but outputs must be deterministic.

## How to Work (Definition of Done)

For each PR-sized change:

- **Run pre-commit checks locally and fix all issues before committing.**
  - Pre-commit hooks will auto-fix many issues (formatting, linting, whitespace).
  - Always review and commit these auto-fixes as part of your change.
- Add/adjust tests for new behavior.
  - Python: pytest tests in `tests/`
  - PowerShell: Pester tests in `tests/PowerShell/`
- For data-file changes (JSON, JSONC, YAML, YAML-based GitHub Actions workflows), run the applicable validation hooks via `pre-commit run --all-files` so that `check-json`, `check-yaml`, `yamllint`, `actionlint`, and (where configured) `check-jsonschema` all pass before committing.
- Keep changes small and reviewable; avoid "big bang" refactors.
- Update docs/spec only if behavior is intentionally changed (and note why).
- Ensure:
  - unit tests pass
  - linters/formatters pass
  - no secrets appear in logs, artifacts, or test fixtures

## What Not to Do

- Do not add any feature that executes scripts or commands generated by untrusted sources.
- Do not add telemetry or external logging services without explicit approval.
- Do not weaken security constraints to "make it work."
- Do not add new major dependencies without clear justification in the PR description.
- Do not implement "Copilot agent fixes" or rely on non-public APIs for lint correction.
- Do not silently invent behavior when specs or requirements are ambiguous—open an issue or add an explicit "Open Question" instead.
- Do not create separate "fix formatting" or "fix linting" commits—include all auto-fixes in the same commit as your changes.

## Modular Instructions

This repository uses modular instruction files covering both language-specific standards and cross-cutting repository rules:

| Scope | Instruction File | Applies To |
| --- | --- | --- |
| Git attributes | `.github/instructions/gitattributes.instructions.md` | `**/.gitattributes` |
| JSON | `.github/instructions/json.instructions.md` | `**/*.json`, `**/*.jsonc` |
| Markdown/Docs | `.github/instructions/docs.instructions.md` | `**/*.md` |
| PowerShell | `.github/instructions/powershell.instructions.md` | `**/*.ps1` |
| Python | `.github/instructions/python.instructions.md` | `**/*.py` |
| Terraform | `.github/instructions/terraform.instructions.md` | `**/*.tf`, `**/*.tfvars`, `**/*.tftest.hcl`, `**/*.tf.json`, `**/*.tftpl`, `**/*.tfbackend` |
| YAML | `.github/instructions/yaml.instructions.md` | `**/*.yml`, `**/*.yaml` |

**Note:** The PowerShell instructions include comprehensive guidance on Pester testing. The Terraform instructions include comprehensive guidance on Terraform Test framework.

**To customize for your project:**

- Remove instruction files for scopes you don't use
- Add new instruction files for additional languages or cross-cutting rules as needed
- Update this table to reflect the instruction files present in your project

> **Terraform note:** If your project does not use Terraform, remove the Terraform instruction file (`.github/instructions/terraform.instructions.md`), remove the Terraform row from the table above, and remove Terraform-related entries from the Linting Configurations and Testing Tools sections below.

## Agent Instruction Files

This repository includes agent instruction files at the repository root to support multi-platform AI coding agents:

| File | Target Agent(s) |
| --- | --- |
| `CLAUDE.md` | Claude Code, GitHub Copilot coding agent |
| `AGENTS.md` | OpenAI Codex CLI, GitHub Copilot coding agent |
| `GEMINI.md` | Gemini Code Assist, GitHub Copilot coding agent |

`.github/copilot-instructions.md` remains the **canonical source of truth** for all repository rules. The root agent instruction files are thin entry points: each keeps a minimal inline summary of the highest-priority shared rules for reliability and may add platform-specific guidance that does not conflict with this file.

When modifying high-priority shared guidance in `.github/copilot-instructions.md` (for example, canonical file location, safety rules, pre-commit expectations, validation commands, or language-instruction references), update the minimal summaries in any remaining agent files as needed. Avoid copying large shared sections into the entry point files.

**To customize for your project:**

- Remove agent files for platforms you do not use
- Keep the remaining agent files limited to minimal inline summaries plus any necessary platform-specific guidance

## Linting Configurations

This repository includes linting tool configurations that align with the coding standards:

| Tool | Configuration File | Purpose |
| --- | --- | --- |
| PSScriptAnalyzer | `.github/linting/PSScriptAnalyzerSettings.psd1` | PowerShell formatting/linting (OTBS style) |
| markdownlint | `.markdownlint.jsonc` | Markdown linting |
| TFLint | `.tflint.hcl` | Terraform linting |

### Running Linters

**Markdown:**

```bash
npm run lint:md
```

**PowerShell:**

```powershell
Invoke-ScriptAnalyzer -Path .\script.ps1 -Settings .\.github\linting\PSScriptAnalyzerSettings.psd1
```

**Terraform:**

```bash
terraform fmt -check -recursive
tflint --recursive
```

## Testing Tools

This repository includes testing infrastructure for Python, PowerShell, and Terraform:

| Language | Framework | Configuration | Test Location |
| --- | --- | --- | --- |
| Python | pytest | `pyproject.toml` (`[tool.pytest.ini_options]`) | `tests/` |
| PowerShell | Pester 5.x | Inline in `.github/workflows/powershell-ci.yml` | `tests/PowerShell/` |
| Terraform | Terraform Test (requires Terraform 1.6+) | Built-in | `modules/*/tests/` or `tests/` |

### Running Tests

**Python:**

```bash
pytest tests/ -v --cov --cov-report=term-missing
```

**PowerShell:**

```powershell
Invoke-Pester -Path tests/ -Output Detailed
```

**Terraform:**

```bash
terraform test -verbose
```
