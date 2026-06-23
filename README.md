# Project Name

> **Note:** This repository was created from [`franklesniak/copilot-repo-template`](https://github.com/franklesniak/copilot-repo-template).

## Description

[Add your project description here]

---

## Table of Contents

- [Readme for the Copilot Repository Template](#readme-for-the-copilot-repository-template)
  - [What This Template Provides](#what-this-template-provides)
  - [Getting Started](#getting-started)
  - [Repository Structure](#repository-structure)
  - [Language Support](#language-support)
  - [Linting Tools](#linting-tools)
  - [Testing](#testing)
  - [Code Quality](#code-quality)
  - [License](#license)

---

## Readme for the Copilot Repository Template

This is a template repository providing GitHub Copilot instructions, AI-agent entry points, validation tooling, and modular starter content for new and existing projects.

### What This Template Provides

This template includes:

- **GitHub Copilot Instructions:** Repository-wide safety, validation, and workflow standards for AI-assisted development.
- **Multi-Agent Support:** Instruction files for Cursor Agent, Hermes Agent, Claude Code, OpenAI Codex CLI, and Gemini Code Assist.
- **Modular Guidelines:** Instruction files for adopted language and file-type stacks.
- **Linting Configurations:** Retained linting and link-checking configuration for Markdown and PowerShell.
- **Data-File Validation:** Baseline hooks for `check-json` and `check-yaml`. Retained modules add `check-jsonschema` (schema, template-sync support, or GitHub platform) and `check-metaschema` (schema or template-sync support) for their JSON Schema contracts.
<!-- template-sync: begin github-actions-reference-only -->
- **GitHub Actions Validation:** Retained GitHub Actions workflows add `actionlint` validation.
<!-- template-sync: end github-actions-reference-only -->
<!-- template-sync: begin yaml-reference-only -->
- **YAML Style Validation:** `yamllint` configuration and CI wiring for repositories that adopt the YAML module.
<!-- template-sync: end yaml-reference-only -->
<!-- template-sync: begin schema-reference-only -->
- **Worked-Example Schemas:** A JSON Schema worked example, example fixtures, and schema contract tests for adopters that keep the schema module.
<!-- template-sync: end schema-reference-only -->
- **Pre-commit Hooks:** Automated quality checks before commits.

### Getting Started

Choose the guide that matches your situation:

- **[Creating a New Repository](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/GETTING_STARTED_NEW_REPO.md):** Step-by-step guide for creating a new repository from this template.
- **[Adding to an Existing Repository](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/GETTING_STARTED_EXISTING_REPO.md):** Guide for adopting template features into an existing repository.
- **[Optional Configurations](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/OPTIONAL_CONFIGURATIONS.md):** Advanced customization options after initial setup.

For template maintainers, see [TEMPLATE_MAINTENANCE.md](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/TEMPLATE_MAINTENANCE.md).

### Repository Structure

Core retained surfaces include:

- `.github/copilot-instructions.md` - repo-wide constitution for all changes.
- `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md`, and `.github/CODEOWNERS` - GitHub collaboration surfaces.
<!-- template-sync: begin github-platform-reference-only -->
- `.github/dependabot.yml` - GitHub Dependabot configuration for GitHub-hosted dependency update automation.
<!-- template-sync: end github-platform-reference-only -->
- `.github/instructions/` - retained modular instruction files.
- `.github/linting/PSScriptAnalyzerSettings.psd1` - PowerShell lint settings.
- `.github/scripts/` - helper scripts for placeholder replacement, Markdown linting, and retained validation.
- `.github/workflows/` - retained GitHub Actions workflows.
- `.markdownlint.jsonc`, `.remarkrc.mjs`, and `.remarkignore` - Markdown linting and link-check configuration.
- `.pre-commit-config.yaml` - aggregate pre-commit hook configuration.
- `templates/markdown/` - Markdown linting starter configuration.
- `templates/powershell/` - PowerShell starter test content.
- `tests/` - retained helper tests and PowerShell tests.
- Root community and contributor files such as `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, and `LICENSE`.

Optional module-owned surfaces include:

<!-- template-sync: begin json-reference-only -->
- `templates/json/` - JSON starter schema content and example fixtures.
<!-- template-sync: end json-reference-only -->
<!-- template-sync: begin yaml-reference-only -->
- `.yamllint.yml` and `templates/yaml/` - YAML style configuration and starter YAML content.
<!-- template-sync: end yaml-reference-only -->
<!-- template-sync: begin schema-reference-only -->
- `schemas/example-config.schema.json`, `schemas/examples/example-config/`, and `schemas/README.md` - worked-example schema contracts and documentation.
<!-- template-sync: end schema-reference-only -->
<!-- template-sync: begin python-reference-only -->
- `pyproject.toml`, `src/copilot_repo_template/`, `templates/python/`, `.github/workflows/python-ci.yml`, and Python tests - Python package starter content and CI.
<!-- template-sync: end python-reference-only -->
<!-- template-sync: begin terraform-reference-only -->
- `.tflint.hcl`, `.github/workflows/terraform-ci.yml`, `.github/scripts/terraform_hooks.py`, `docs/terraform/`, and `templates/terraform/` - Terraform validation, docs, and starter tests.
<!-- template-sync: end terraform-reference-only -->
<!-- template-sync: begin template-sync-support-reference-only -->
- `.template-sync/` - template-sync marker, manifest, and helper scripts.
- `schemas/template-sync-*.schema.json` - template-sync schema contracts, with matching `schemas/examples/template-sync-*` fixtures where provided.
<!-- template-sync: end template-sync-support-reference-only -->
<!-- template-sync: begin azure-devops-guide-reference-only -->
- `docs/azure-devops-support.md` - Durable Azure DevOps Services hosting, security, dependency-update, and validation guidance for optional Azure host modules.
<!-- template-sync: end azure-devops-guide-reference-only -->

#### Key Files Explained

- `.github/CODEOWNERS` - Defines code ownership for automatic PR review requests; replace the `@OWNER` placeholder.
- `.github/copilot-instructions.md` - The repo-wide constitution for all code changes, including safety rules, pre-commit discipline, and instruction-file references.
<!-- template-sync: begin github-platform-reference-only -->
- `.github/dependabot.yml` - GitHub Dependabot configuration for GitHub-hosted dependency update automation.
<!-- template-sync: end github-platform-reference-only -->
- `.github/instructions/*.md` - Retained coding standards applied based on file patterns.
- `.github/linting/PSScriptAnalyzerSettings.psd1` - PSScriptAnalyzer settings enforcing OTBS formatting for PowerShell.
- `.github/workflows/auto-fix-precommit.yml` - Optional auto-fix workflow for pre-commit fixes on Copilot-agent branches.
- `.github/workflows/check-placeholders.yml` - Transitional OWNER/REPO and `@OWNER` placeholder check.
<!-- template-sync: begin data-ci-reference-only -->
- `.github/workflows/data-ci.yml` - Data-file and template-sync validation workflow, present when a data-file or template-sync module is retained.
<!-- template-sync: end data-ci-reference-only -->
- `.github/workflows/markdownlint.yml` - Markdown linting and offline link-validation workflow.
- `.github/workflows/powershell-ci.yml` - PowerShell linting and Pester testing workflow.
- `.github/workflows/precommit-ci.yml` - Aggregate `pre-commit run --all-files` gate.
<!-- template-sync: begin python-reference-only -->
- `.github/workflows/python-ci.yml` - Python type-check and pytest workflow.
<!-- template-sync: end python-reference-only -->
<!-- template-sync: begin terraform-reference-only -->
- `.github/workflows/terraform-ci.yml` - Terraform format, validate, lint, test, and security workflow.
<!-- template-sync: end terraform-reference-only -->
- `.markdownlint.jsonc` - Markdown linting rules prioritizing auto-fixable checks.
- `.remarkignore` - Exclusions for offline Markdown link validation.
- `.remarkrc.mjs` - Remark configuration for offline Markdown link validation.
<!-- template-sync: begin yaml-reference-only -->
- `.yamllint.yml` - YAML linting configuration.
<!-- template-sync: end yaml-reference-only -->
- `.pre-commit-config.yaml` - Pre-commit hooks for retained project surfaces.
- `schemas/` - JSON Schema contracts present when the schema or template-sync support module is adopted (the worked-example schema and/or the template-sync schemas).
<!-- template-sync: begin python-reference-only -->
- `pyproject.toml` - Python project configuration with development dependencies.
- `src/copilot_repo_template/` - Example Python package to rename for your project.
<!-- template-sync: end python-reference-only -->
- `tests/` - Retained automated tests for template tooling and adopted stacks.
<!-- template-sync: begin json-reference-only -->
- `templates/json/` - JSON Schema starter content for downstream consumers to copy and adapt.
<!-- template-sync: end json-reference-only -->
- `templates/powershell/Example.Tests.ps1` - Comprehensive Pester test template with examples.
<!-- template-sync: begin yaml-reference-only -->
- `templates/yaml/` - YAML starter configurations and examples for downstream consumers to copy and adapt.
<!-- template-sync: end yaml-reference-only -->

### Language Support

- **Markdown/Docs:** [`.github/instructions/docs.instructions.md`](.github/instructions/docs.instructions.md), `**/*.md`, and `.github/workflows/markdownlint.yml`.
- **PowerShell:** [`.github/instructions/powershell.instructions.md`](.github/instructions/powershell.instructions.md), `**/*.ps1`, and `.github/workflows/powershell-ci.yml`.
<!-- template-sync: begin json-reference-only -->
- **JSON/JSONC:** [`.github/instructions/json.instructions.md`](.github/instructions/json.instructions.md), `**/*.json`, and `**/*.jsonc`.
<!-- template-sync: end json-reference-only -->
<!-- template-sync: begin yaml-reference-only -->
- **YAML:** [`.github/instructions/yaml.instructions.md`](.github/instructions/yaml.instructions.md), `**/*.yml`, and `**/*.yaml`.
<!-- template-sync: end yaml-reference-only -->
<!-- template-sync: begin python-reference-only -->
- **Python:** [`.github/instructions/python.instructions.md`](.github/instructions/python.instructions.md), `**/*.py`, and `.github/workflows/python-ci.yml`.
<!-- template-sync: end python-reference-only -->
<!-- template-sync: begin terraform-reference-only -->
- **Terraform:** [`.github/instructions/terraform.instructions.md`](.github/instructions/terraform.instructions.md), Terraform files, and `.github/workflows/terraform-ci.yml`.
<!-- template-sync: end terraform-reference-only -->
<!-- template-sync: begin azure-devops-guide-reference-only -->
- **Azure DevOps Services:** [Azure DevOps Services Support Guide](docs/azure-devops-support.md), retained only when an Azure DevOps host module is adopted.
<!-- template-sync: end azure-devops-guide-reference-only -->

> **JSON note:** `check-json` validates strict `.json` files only; it does **not** validate `.jsonc`. JSONC is allowed where the consuming tool supports it, and stricter enforcement requires JSONC-aware tooling.

### Linting Tools

This template organizes linting configurations in `.github/linting/` for PSScriptAnalyzer and in the repository root for Markdown tooling. Projects MAY reorganize retained configurations if they also update every reference to the moved paths so contributor guidance does not drift, including the corresponding workflow, pre-commit, and `.github/copilot-instructions.md` (plus any `.github/instructions/` files) references.

#### Markdown Linting

Configuration: `.markdownlint.jsonc`

Link-check configuration: `.remarkrc.mjs` and `.remarkignore`

```bash
npm run lint:md
npm run lint:md:links
npx markdownlint-cli2 "**/*.md" "#node_modules" "#.pytest_cache" --fix
```

`npm run lint:md:links` validates repository-local file links and Markdown heading fragments without checking external URLs, keeping the default command deterministic for CI.

#### PowerShell Linting

Configuration: `.github/linting/PSScriptAnalyzerSettings.psd1`

```powershell
Invoke-ScriptAnalyzer -Path .\script.ps1 -Settings .\.github\linting\PSScriptAnalyzerSettings.psd1
Invoke-ScriptAnalyzer -Path .\script.ps1 -Settings .\.github\linting\PSScriptAnalyzerSettings.psd1 -Fix
```

<!-- template-sync: begin python-reference-only -->
#### Python Linting

Configuration: `.pre-commit-config.yaml`

```bash
pre-commit run --all-files
pre-commit run black --all-files
pre-commit run ruff-check --all-files
```
<!-- template-sync: end python-reference-only -->

#### Data-File Validation

Data-file and retained schema validation run through `.pre-commit-config.yaml`.

<!-- template-sync: begin github-actions-reference-only -->
GitHub Actions validation also runs through `.pre-commit-config.yaml`.
<!-- template-sync: end github-actions-reference-only -->

- **`check-json`** - strict `.json` syntax validation. It does **not** validate `.jsonc`.
- **`check-yaml`** - `.yml` and `.yaml` parse checks.
<!-- template-sync: begin yaml-reference-only -->
- **`yamllint`** - YAML style enforcement per `.yamllint.yml`.
<!-- template-sync: end yaml-reference-only -->
<!-- template-sync: begin github-actions-reference-only -->
- **`actionlint`** - GitHub Actions workflow linting.
<!-- template-sync: end github-actions-reference-only -->
- **`check-jsonschema`** - present when schema-backed modules (the schema, template-sync support, or GitHub platform module) are retained; validates retained JSON Schema-backed files and selected load-bearing configuration against built-in vendor schemas.
- **`check-metaschema`** - present when the schema or template-sync support module is retained; self-validates retained project-owned schemas.

Prettier is **opt-in** and is not part of the default data-file toolchain.

```bash
pre-commit run --all-files
pre-commit run check-json --all-files
pre-commit run check-yaml --all-files
```

<!-- template-sync: begin github-actions-reference-only -->
```bash
pre-commit run actionlint --all-files
```
<!-- template-sync: end github-actions-reference-only -->

<!-- template-sync: begin yaml-reference-only -->
```bash
pre-commit run yamllint --all-files
```
<!-- template-sync: end yaml-reference-only -->

<!-- template-sync: begin schema-reference-only -->
> **Schema validation (worked example shipped):** `check-jsonschema` validates the worked-example schema fixtures, and `check-metaschema` validates `schemas/example-config.schema.json`. See [`schemas/README.md`](schemas/README.md) for the worked example, the canonical downstream removal checklist, and future-work candidates.
<!-- template-sync: end schema-reference-only -->

<!-- template-sync: begin terraform-reference-only -->
#### Terraform Linting

Configuration: `.tflint.hcl`

```bash
terraform fmt -check -recursive -diff
terraform fmt -recursive
terraform init -backend=false && terraform validate
tflint --init
tflint --recursive --config "$(pwd)/.tflint.hcl"
```
<!-- template-sync: end terraform-reference-only -->

### Testing

<!-- template-sync: begin template-sync-support-reference-only -->
#### Downstream Partial-Adoption Validation

Downstream repositories that keep `.template-sync/marker.yml` after removing optional modules SHOULD validate the retained template surface with:

```bash
python .template-sync/scripts/validate_downstream_adoption.py --require-marker
```

Use the downstream adoption command when `.template-sync/marker.yml` is the source of truth for retained modules and excluded modules are intentionally absent. Run the full upstream test suite when maintaining this template or when a downstream repository intentionally keeps the corresponding test/tool stack.

Downstream repositories that retain pytest-based template support SHOULD use the official downstream pytest gate:

```bash
python -m pytest -m "not upstream_template_only"
```

The gate excludes only tests marked `upstream_template_only`, so new unmarked tests remain included by default. The committed pytest configuration uses strict marker validation.

For cleanup planning, generate a read-only excluded-module report:

```bash
python .template-sync/scripts/report_excluded_module_references.py
```

The report uses a schema-valid `.template-sync/marker.yml` by default. During pre-marker planning, provide the retained modules explicitly and repeat the flag for each retained module:

```bash
python .template-sync/scripts/report_excluded_module_references.py --included-module baseline --included-module agent-instructions
```

Findings are informational and do not make the command fail. The command exits nonzero only for runtime or input failures such as invalid manifest data, unsafe paths, unreadable required files, or unknown explicit modules.
<!-- template-sync: end template-sync-support-reference-only -->

<!-- template-sync: begin python-reference-only -->
#### Python Tests

Python tests use pytest with coverage reporting.

```bash
pytest tests/ -v --cov --cov-report=term-missing
pytest tests/test_example.py -v
```
<!-- template-sync: end python-reference-only -->

<!-- template-sync: begin schema-reference-only -->
#### JSON Schema Example Tests

```bash
pytest tests/test_schema_examples.py -v
```

The schema-example contract test ([`tests/test_schema_examples.py`](tests/test_schema_examples.py)) auto-discovers `schemas/*.schema.json` and the matching `schemas/examples/<name>/{valid,invalid}/` fixtures and asserts that valid fixtures pass and invalid fixtures fail.
<!-- template-sync: end schema-reference-only -->

#### PowerShell Tests

PowerShell tests use Pester 5.x.

```powershell
Install-Module -Name Pester -MinimumVersion 5.0 -Force -Scope CurrentUser
Invoke-Pester -Path tests/ -Output Detailed
Invoke-Pester -Path tests/PowerShell/Placeholder.Tests.ps1
```

CI runs PowerShell tests on Windows, macOS, and Linux to ensure cross-platform compatibility. See `templates/powershell/Example.Tests.ps1` for a comprehensive Pester test template.

<!-- template-sync: begin terraform-reference-only -->
#### Terraform Tests

Terraform tests use the native Terraform test framework.

```bash
terraform test -verbose
terraform test -filter=tests/unit.tftest.hcl
```

See `templates/terraform/Example.tftest.hcl` for a comprehensive Terraform test template.
<!-- template-sync: end terraform-reference-only -->

### Code Quality

This repository enforces code quality through retained validation surfaces:

- **Markdown Linting and Link Checking:** markdownlint runs on pre-commit and in CI; offline Markdown link validation runs in CI.
- **Data-File Validation:** `check-json` and `check-yaml` run through pre-commit.
<!-- template-sync: begin github-actions-reference-only -->
- **GitHub Actions Validation:** `actionlint` runs through pre-commit.
<!-- template-sync: end github-actions-reference-only -->
<!-- template-sync: begin yaml-reference-only -->
- **YAML Style Validation:** `yamllint` runs through pre-commit when the YAML module is retained.
<!-- template-sync: end yaml-reference-only -->
- **Schema Validation:** When schema-backed modules are retained, `check-jsonschema` validates retained schema-backed files and `check-metaschema` self-validates retained project-owned schemas. See [`.github/TEMPLATE_DESIGN_DECISIONS.md`](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/.github/TEMPLATE_DESIGN_DECISIONS.md) for the built-in schema validation policy.
- **Template-Sync Validation:** Template-sync manifest, marker, instruction-contract, and example fixtures are schema-backed when template-sync support is retained.
- **GitHub Copilot Instructions:** Guides AI-assisted development.
- **Pre-commit Hooks:** Catches issues before they reach CI.
- **PSScriptAnalyzer:** PowerShell static analysis with OTBS formatting.
<!-- template-sync: begin terraform-reference-only -->
- **TFLint:** Terraform linting with configurable rules and cloud provider plugins.
<!-- template-sync: end terraform-reference-only -->

### License

MIT License - See [LICENSE](LICENSE) for details.
