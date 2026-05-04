<!-- markdownlint-disable MD013 -->
# Repository Copilot Instructions (Repo-Wide Constitution)

**Version:** 1.4.20260504.0

## Metadata

- **Status:** Active
- **Owner:** Repository Maintainers
- **Last Updated:** 2026-05-04
- **Scope:** Repo-wide canonical instructions ("constitution") that govern all changes in this repository. This file is the authoritative source of truth for repository rules; all language-specific instruction files and agent entry points defer to it.
- **Related:** [Documentation Writing Style](instructions/docs.instructions.md)

These instructions are authoritative for all changes in this repository.

## Source of Truth

> **Customize this section** for your project. Point to your authoritative specification or design document. Example:
>
> - Read **`docs/spec/requirements.md`** before making changes.
> - If any instruction here conflicts with the spec, **the spec wins**.

## Protected Instruction Files

Instruction files and style guides are protected governance files. This rule applies to:

- The repo-wide constitution: `.github/copilot-instructions.md`
- Root agent entry points: `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md`
- Modular instruction files under `.github/instructions/`

Agents **MUST NOT** create, edit, delete, rename, or otherwise change protected instruction files unless the repository owner or maintainer has directly and explicitly authorized the specific instruction-file change in the current task. Implied consent is insufficient.

Authorization **MUST NOT** be inferred from:

- An agent-generated plan, rubric, option analysis, or implementation strategy.
- A request to fix code, resolve review feedback, update documentation as needed, or keep files in sync.
- Pre-commit, formatting, linting, validation, or other cleanup work.
- An automated review loop, reusable prompt, or generic permission to make repository changes.

When an agent identifies a warranted instruction or style-guide update without explicit authorization, it **MUST** propose the change separately (for example, as a prompt or Open Question) and wait for explicit approval before editing protected files.

When explicit authorization is granted, keep protected instruction-file edits narrowly scoped, preserve the canonical source-of-truth hierarchy, and update related metadata and version fields according to [Documentation Writing Style](instructions/docs.instructions.md).

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

In addition to formatting, linting, trailing-whitespace, and end-of-file fixes, pre-commit also enforces validation for structured data files. Run `pre-commit run --all-files` to execute the full hook set. The data-file checks currently include:

- `check-json` — validates strict `.json` syntax. **Note:** `check-json` does **not** validate `.jsonc`; JSONC (JSON with comments) is allowed only when supported by the consuming tool, and stricter enforcement requires JSONC-aware tooling.
- `check-yaml` — parse-checks `.yml` / `.yaml` files.
- `yamllint` — enforces YAML style per `.yamllint.yml`.
- `actionlint` — lints GitHub Actions workflow files.
- `check-jsonschema` — JSON Schema validation. Validates: (a) the worked-example schema's valid example data under `schemas/examples/example-config/valid/` against `schemas/example-config.schema.json`; (b) selected real load-bearing repository configuration files (for example, `.github/dependabot.yml`) against built-in vendor schemas shipped with `check-jsonschema`; and (c) any future project-owned schema-backed file families that downstream maintainers wire up in `.pre-commit-config.yaml`.
- `check-metaschema` — self-validates project-owned schemas (currently `schemas/example-config.schema.json`) against their declared JSON Schema metaschema, where configured in `.pre-commit-config.yaml`.

`.pre-commit-config.yaml` is the authoritative list of active hooks. Do **not** rely on a hardcoded total hook count when describing the validation model; consult `.pre-commit-config.yaml` directly to see which hooks are wired up. For the policy and rationale behind which real load-bearing configuration files receive built-in schema validation, see the **Built-in Schema Validation for Real Load-Bearing Configuration Files** ADR in [`.github/TEMPLATE_DESIGN_DECISIONS.md`](TEMPLATE_DESIGN_DECISIONS.md).

Prettier is **opt-in** and is **not** part of the default data-file toolchain. (This framing has been re-verified against the built-in schema validation ADR and remains correct.)

> **Schema example tests.** The contract that valid example fixtures pass and invalid example fixtures fail is exercised by [`tests/test_schema_examples.py`](../tests/test_schema_examples.py). Run `pytest tests/test_schema_examples.py -v` after any schema or schema-example change. The dedicated [`.github/workflows/data-ci.yml`](workflows/data-ci.yml) workflow re-runs the data-file hooks (`check-json`, `check-yaml`, `yamllint`, `actionlint`, `check-jsonschema`, `check-metaschema`) so JSON/YAML/Actions enforcement can be made a required check via branch protection independent of the Python CI job. See [`schemas/README.md`](../schemas/README.md) for the worked example, the canonical downstream removal checklist, and future-work candidates. Downstream repositories MAY add additional `check-jsonschema` hook entries for their own schema-backed file families.
>
> **When schema contracts change**, agents updating any schema **MUST** keep the following in sync in the same change:
>
> - The schema file under `schemas/<name>.schema.json`.
> - Valid example fixtures under `schemas/examples/<name>/valid/`.
> - Invalid example fixtures under `schemas/examples/<name>/invalid/`.
> - The pre-commit hook scope in `.pre-commit-config.yaml`.
> - `.github/workflows/data-ci.yml` only when **adding or removing a hook ID** (for example, introducing a new `check-yaml-custom` hook), or when adding, removing, or renaming an explicit CI step or hook alias that the workflow invokes by name. Changes to an **existing** hook's `files:` regex (including `check-jsonschema` scope changes) are picked up automatically, because each `data-ci.yml` step invokes hooks by ID via `pre-commit run <hook-id> --all-files`.
> - The **Built-in Schema Validation for Real Load-Bearing Configuration Files** ADR in [`.github/TEMPLATE_DESIGN_DECISIONS.md`](TEMPLATE_DESIGN_DECISIONS.md) when **adding or removing** a default validated real load-bearing configuration file (for example, when wiring or unwiring a new built-in vendor schema).
> - Any documentation that references the schema or the validation policy (for example, `schemas/README.md`, `README.md`, `CONTRIBUTING.md`, and `OPTIONAL_CONFIGURATIONS.md`).

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

## Workflow Version Pinning

GitHub Actions workflow files in this repository (`.github/workflows/*.yml`) reference both **action versions** (in `uses:` lines) and **tool versions** (passed to actions or shell commands as inputs or arguments). The two categories have different update mechanisms and different rules. Conflating them — or mirroring an action version into a secondary location that Dependabot does not rewrite — produces partial updates where the declared action version moves but related literals silently drift to the old version. The rules below prevent that drift.

For the rationale, see the **Workflow Version Pinning and Dependabot Coherence** ADR in [`.github/TEMPLATE_DESIGN_DECISIONS.md`](TEMPLATE_DESIGN_DECISIONS.md).

### Action versions in `uses:` references

- Third-party action versions **MUST** remain directly visible in `uses:` references (for example, `actions/checkout@v6`, `hashicorp/setup-terraform@v4`) so Dependabot's `github-actions` ecosystem can update them.
- Repeated `uses:` references to the same action across jobs and steps are acceptable when each occurrence is a normal Dependabot-managed `uses:` reference. Dependabot updates each `uses:` line directly.
- Do **NOT** store an action version in a workflow-level `env:` variable, comment, cache key, file path, shell literal, manually constructed image tag, or any other secondary location as a mirror of a `uses:` version. The `uses:` line **MUST** be the only authoritative source for the action version because Dependabot rewrites `uses:` references and will leave unrelated literals stale.
- Do **NOT** copy a Dependabot-managed action version into secondary workflow locations that Dependabot will not reliably rewrite (for example, cache keys, file paths, shell commands, manually constructed image tags, or comments presented as authoritative version state).
- If secondary workflow behavior needs to change when a `uses:` version changes, derive that behavior from a stable source that naturally changes with the workflow or tool configuration. Prefer cache keys scoped to the specific configuration file that governs the cached artifact — for example, `hashFiles('.pre-commit-config.yaml')` for pre-commit caches, `hashFiles('.tflint.hcl')` for TFLint plugin caches, or `hashFiles('**/.terraform.lock.hcl')` for Terraform provider caches, mirroring the pattern already used in this repository's workflows. Avoid broad wildcard patterns such as `hashFiles('.github/workflows/*.yml')` for cache keys: any unrelated workflow edit would invalidate every job's cache. The goal is to track the configuration that actually drives the cached content, not the workflow definition that consumes it.

### Tool versions passed as action inputs or shell arguments

Tool versions that are not managed by Dependabot — for example, `terraform_version: "1.14.4"` passed to `hashicorp/setup-terraform@v4`, or `tflint_version: v0.51.1` passed to `terraform-linters/setup-tflint@v6` — **SHOULD** still avoid unnecessary duplication. If the same tool version is required in multiple workflow jobs or steps, prefer a single source of truth where GitHub Actions supports one, such as a workflow-level `env:` value for the CLI/tool version.

### Asymmetry: workflow-level `env:` for action versions vs. tool versions

The two categories are **not** symmetric, and the difference is the entire point of this rule:

- **Action versions** (`uses:`): a workflow-level `env:` mirror is **forbidden**. Dependabot will not rewrite the `env:` value, so it would silently desynchronize from the actual `uses:` reference. The `uses:` line is the only authoritative source.
- **Tool versions** (action inputs, shell args): a workflow-level `env:` value is **encouraged** as the single source of truth. Dependabot does not manage these versions, so there is no desync risk; one `env:` value can serve as the source of truth across multiple steps.

### Distinguishing wrapper actions from the tools they install

Action wrapper versions and the tool versions they install are **separate pins** that travel through different channels:

- `hashicorp/setup-terraform@v4` is the setup action version (managed by Dependabot via `uses:`).
- `terraform_version: "1.14.4"` is the Terraform CLI version installed by that setup action (not managed by Dependabot; manually maintained).

Both pins exist in the same workflow step, but they update on different cadences and through different mechanisms. Do not conflate them.

### When a Dependabot-managed dependency cannot be expressed without duplication

If a Dependabot-managed dependency genuinely cannot be represented only through Dependabot-managed declarations, and Dependabot would otherwise produce partial updates, add an appropriate `.github/dependabot.yml` `ignore:` entry with a YAML comment explaining why the dependency is intentionally not auto-updated. Use this escape hatch sparingly: it disables automation for that dependency, so it should be applied only when the partial-update problem cannot be solved by removing the duplication or by deriving secondary behavior from a stable source.

### Concrete examples in this repository

- Pinned action majors such as `actions/checkout@v6`, `actions/setup-python@v6`, `actions/cache@v5`, and `actions/setup-node@v6` appear repeatedly in workflow `uses:` lines. These are acceptable because each occurrence is a normal Dependabot-managed `uses:` reference.
- `terraform_version: "1.14.4"` appears in multiple jobs in [`.github/workflows/terraform-ci.yml`](workflows/terraform-ci.yml). This is a Terraform CLI version (not the `hashicorp/setup-terraform` action version), so it is **not** a Dependabot `uses:` desynchronization case. It is a useful candidate for a future single source of truth (such as a workflow-level `env:` value) if duplication grows; refactoring existing workflows to that shape is out of scope for this rule.
- `tflint_version: v0.51.1` is passed to `terraform-linters/setup-tflint@v6`. This is a tool-version pin distinct from the setup action version; the same dual-pin model applies.

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

When explicitly authorized to modify high-priority shared guidance in `.github/copilot-instructions.md` (for example, canonical file location, safety rules, pre-commit expectations, validation commands, or language-instruction references), update the minimal summaries in any remaining agent files as needed. Avoid copying large shared sections into the entry point files.

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
