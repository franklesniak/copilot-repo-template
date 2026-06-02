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

This is a template repository providing best-practice GitHub Copilot instructions and linting configurations for new projects.

### What This Template Provides

This template includes:

- **GitHub Copilot Instructions:** Comprehensive coding standards that guide AI-assisted development
- **Multi-Agent Support:** Instruction files for Cursor Agent, Hermes Agent, Claude Code, OpenAI Codex CLI, and Gemini Code Assist (`.cursor/rules/repository-instructions.mdc`, `.hermes.md`, `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`)
- **Language-Specific Guidelines:** Modular instruction files for Markdown, PowerShell, Python, Terraform, JSON/JSONC, and YAML
- **Linting Configurations:** Pre-configured settings for markdownlint, offline Markdown link validation, PSScriptAnalyzer, TFLint, and yamllint
- **Data-File Validation:** Pre-commit hooks for `check-json`, `check-yaml`, `yamllint`, `actionlint` (GitHub Actions workflows), `check-jsonschema` (validates schema valid examples, `.template-sync/manifest.yml`, `.template-sync/marker.yml` when present, plus selected real load-bearing configuration files against built-in vendor schemas), and `check-metaschema` (project-owned schema self-validation)
- **JSON Schemas:** Root-level `schemas/` directory convention for schema-backed JSON and YAML files
- **Pre-commit Hooks:** Automated code quality checks before commits

### Getting Started

Choose the guide that matches your situation:

- **[Creating a New Repository](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/GETTING_STARTED_NEW_REPO.md)**: Step-by-step guide for creating a new repository from this template
- **[Adding to an Existing Repository](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/GETTING_STARTED_EXISTING_REPO.md)**: Guide for adopting template features into an existing repository
- **[Optional Configurations](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/OPTIONAL_CONFIGURATIONS.md)**: Advanced customization options after initial setup

For template maintainers, see [TEMPLATE_MAINTENANCE.md](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/TEMPLATE_MAINTENANCE.md).

### Repository Structure

```text
.github/
├── CODEOWNERS                       # Code ownership for automatic PR review requests
├── copilot-instructions.md          # Repo-wide constitution for all changes
├── dependabot.yml                   # Automated dependency updates configuration
├── instructions/                    # Language-specific coding standards
│   ├── docs.instructions.md         # Markdown/documentation standards
│   ├── gitattributes.instructions.md # .gitattributes authoring standards
│   ├── json.instructions.md         # JSON/JSONC authoring standards
│   ├── powershell.instructions.md   # PowerShell coding standards
│   ├── python.instructions.md       # Python coding standards
│   ├── terraform.instructions.md    # Terraform coding standards
│   └── yaml.instructions.md         # YAML authoring standards
├── linting/                         # Linting tool configurations
│   └── PSScriptAnalyzerSettings.psd1  # PowerShell linting settings
├── scripts/                         # Helper scripts for CI/tooling
└── workflows/                       # GitHub Actions workflows
    ├── auto-fix-precommit.yml        # Auto-fix pre-commit on copilot/** pushes (optional)
    ├── check-placeholders.yml       # Transitional OWNER/REPO placeholder check
    ├── data-ci.yml                   # JSON/YAML/Actions data-file linting CI
    ├── markdownlint.yml              # Markdown linting CI (markdownlint + link checks)
    ├── powershell-ci.yml             # PowerShell linting and testing CI (optional)
    ├── precommit-ci.yml              # Aggregate `pre-commit run --all-files` gate
    ├── python-ci.yml                 # Python type-check (mypy) and test (pytest) CI (optional)
    └── terraform-ci.yml              # Terraform format, validate, lint, test, security CI (optional)

src/
└── copilot_repo_template/           # Example Python package (rename for your project)
    ├── __init__.py
    └── example.py

tests/                               # Test directory
├── __init__.py
├── test_example.py                  # Python pytest tests
└── PowerShell/                      # PowerShell Pester tests
    └── Placeholder.Tests.ps1

templates/                           # Reference templates for project setup
├── json/                            # JSON Schema starter content (Draft 2020-12)
├── markdown/                        # Markdown linting configuration variants
├── powershell/                      # PowerShell test templates
│   └── Example.Tests.ps1            # Comprehensive Pester test example
├── python/                          # Python project templates
├── terraform/                       # Terraform test templates
└── yaml/                            # yamllint starter configurations and starter YAML

schemas/                             # JSON Schemas for load-bearing JSON/YAML files (Draft 2020-12)

pyproject.toml                       # Python project configuration
.markdownlint.jsonc                  # Markdown linting configuration
.remarkignore                        # Markdown link-check scan exclusions
.remarkrc.mjs                        # Markdown link-check configuration
.yamllint.yml                        # YAML linting configuration
.pre-commit-config.yaml              # Pre-commit hooks (multi-language)
.cursor/rules/repository-instructions.mdc  # Agent instructions for Cursor Agent
.hermes.md                           # Agent instructions for Hermes Agent
AGENTS.md                            # Agent instructions for OpenAI Codex CLI
CLAUDE.md                            # Agent instructions for Claude Code
GEMINI.md                            # Agent instructions for Gemini Code Assist
```

#### Key Files Explained

| File | Purpose |
| --- | --- |
| `.github/CODEOWNERS` | Defines code ownership for automatic PR review requests - replace `@OWNER` placeholder |
| `.github/copilot-instructions.md` | The "constitution" for all code changes - defines safety rules, pre-commit discipline, and references language-specific instructions |
| `.github/dependabot.yml` | Dependabot configuration for automated dependency updates - enabled by default |
| `.github/instructions/*.md` | Language-specific coding standards applied based on file patterns |
| `.github/linting/PSScriptAnalyzerSettings.psd1` | PSScriptAnalyzer settings enforcing OTBS formatting for PowerShell |
| `.github/workflows/auto-fix-precommit.yml` | Automatically commits pre-commit auto-fixes on pushes to `copilot/**` branches by the Copilot coding agent (optional - remove if not using the Copilot coding agent) |
| `.github/workflows/check-placeholders.yml` | Transitional CI workflow to verify OWNER/REPO and @OWNER placeholders are replaced after cloning; remove after initialization if placeholders are fully replaced and you no longer need the guardrail |
| `.github/workflows/data-ci.yml` | Data-file (JSON/YAML/GitHub Actions) linting CI workflow — runs `check-json`, `check-yaml`, `yamllint`, `actionlint`, `check-jsonschema`, and `check-metaschema` as a dedicated check that can be required via branch protection |
| `.github/workflows/markdownlint.yml` | Markdown linting CI workflow (uses [markdownlint](https://github.com/DavidAnson/markdownlint), nested Markdown linting, and offline link validation) |
| `.github/workflows/powershell-ci.yml` | PowerShell linting and Pester testing CI workflow (optional - remove if not using PowerShell) |
| `.github/workflows/precommit-ci.yml` | Aggregate pre-commit CI workflow — runs `pre-commit run --all-files` over every hook in `.pre-commit-config.yaml`; baseline-scoped so it stays even when Python project source is removed |
| `.github/workflows/python-ci.yml` | Python type-check (mypy) and test (pytest) CI workflow (optional - remove if not using Python). The aggregate pre-commit gate lives in `precommit-ci.yml`. |
| `.github/workflows/terraform-ci.yml` | Terraform format, validate, lint, test, and security CI workflow (optional - remove if not using Terraform) |
| `.markdownlint.jsonc` | Markdown linting rules prioritizing auto-fixable checks |
| `.remarkignore` | Exclusions for offline Markdown link validation |
| `.remarkrc.mjs` | Remark configuration for offline Markdown link validation |
| `.yamllint.yml` | YAML linting configuration (2-space indentation, max line length 120 as warning, unquoted GitHub Actions `on:` allowed) |
| `.pre-commit-config.yaml` | Pre-commit hooks for all projects (multi-language) |
| `schemas/` | Root-level JSON Schemas (Draft 2020-12) describing load-bearing JSON and YAML files |
| `.cursor/rules/repository-instructions.mdc` | Minimal Cursor project rule instructions for Cursor Agent |
| `.hermes.md` | Minimal agent entry point instructions for Hermes Agent |
| `AGENTS.md` | Minimal agent entry point instructions for OpenAI Codex CLI and GitHub Copilot coding agent |
| `CLAUDE.md` | Minimal agent entry point instructions plus Claude-specific workflow guidance |
| `GEMINI.md` | Minimal agent entry point instructions for Gemini Code Assist and GitHub Copilot coding agent |
| `pyproject.toml` | Python project configuration with dev dependencies |
| `src/copilot_repo_template/` | Example Python package - rename for your project |
| `tests/` | Test directory with pytest tests (Python) and Pester tests (PowerShell) |
| `templates/json/` | JSON Schema starter content (Draft 2020-12) and example fixtures for downstream consumers to copy into their own `schemas/` directory and adapt — starter content, not active contracts while under `templates/` |
| `templates/powershell/Example.Tests.ps1` | Comprehensive Pester test template with examples |
| `templates/yaml/` | `yamllint` starter configurations (lenient and strict) and a starter YAML config example for downstream consumers to copy into their own repositories — starter content, not active configurations while under `templates/` |

### Language Support

| Language | Instruction File | File Pattern | CI Workflow | Description |
| --- | --- | --- | --- | --- |
| JSON/JSONC | `.github/instructions/json.instructions.md` | `**/*.json`, `**/*.jsonc` | `.github/workflows/data-ci.yml` (`check-json` on `.json`; `.jsonc` not validated) | JSON authoring standards (strict, schema-backed, deterministic) |
| Markdown/Docs | `.github/instructions/docs.instructions.md` | `**/*.md` | `.github/workflows/markdownlint.yml` | Documentation writing standards |
| PowerShell | `.github/instructions/powershell.instructions.md` | `**/*.ps1` | `.github/workflows/powershell-ci.yml` | PowerShell coding standards (OTBS, v1.0-v7.x) |
| Python | `.github/instructions/python.instructions.md` | `**/*.py` | `.github/workflows/python-ci.yml` | Python coding standards (PEP 8, typing) |
| Terraform | `.github/instructions/terraform.instructions.md` | `**/*.tf`, `**/*.tfvars`, `**/*.tftest.hcl`, etc. | `.github/workflows/terraform-ci.yml` | Terraform coding standards (HCL, modules) |
| YAML | `.github/instructions/yaml.instructions.md` | `**/*.yml`, `**/*.yaml` | `.github/workflows/data-ci.yml` (`check-yaml`, `yamllint`; `actionlint` for workflows only) | YAML authoring standards (explicit, conservative, schema-backed) |

> **JSON note:** `check-json` validates strict `.json` only; it does **not** validate `.jsonc`. JSONC is allowed where the consuming tool supports it, and stricter enforcement requires JSONC-aware tooling.
>
> **Schemas:** JSON Schemas for load-bearing JSON and YAML files live at the repository root under `schemas/` (not `.github/schemas/`). See [`schemas/README.md`](schemas/README.md) for conventions.

### Linting Tools

This template organizes linting configurations in `.github/linting/` (for PSScriptAnalyzer) and the repository root (for markdownlint). Projects MAY reorganize these configurations to a different location (e.g., a project-specific `config/` directory) if preferred. If configurations are moved, update the paths referenced in CI workflows and `.github/copilot-instructions.md` accordingly.

#### Markdown Linting

Configuration: `.markdownlint.jsonc`

Link-check configuration: `.remarkrc.mjs` and `.remarkignore`

```bash
# Check markdown files
npm run lint:md

# Validate local markdown links and headings offline
npm run lint:md:links

# Auto-fix issues
npx markdownlint-cli2 "**/*.md" "#node_modules" "#.pytest_cache" --fix
```

`npm run lint:md:links` validates repository-local file links and Markdown heading fragments without checking external URLs, keeping the default command deterministic for CI.

#### PowerShell Linting (PSScriptAnalyzer)

Configuration: `.github/linting/PSScriptAnalyzerSettings.psd1`

```powershell
# Check PowerShell files
Invoke-ScriptAnalyzer -Path .\script.ps1 -Settings .\.github\linting\PSScriptAnalyzerSettings.psd1

# Auto-fix formatting issues
Invoke-ScriptAnalyzer -Path .\script.ps1 -Settings .\.github\linting\PSScriptAnalyzerSettings.psd1 -Fix
```

#### Python Linting

Configuration: `.pre-commit-config.yaml`

```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Run specific hooks
pre-commit run black --all-files
pre-commit run ruff-check --all-files
```

#### JSON, YAML, and GitHub Actions Linting

JSON, YAML, and GitHub Actions workflow validation runs through pre-commit hooks. Configuration: `.pre-commit-config.yaml` (and `.yamllint.yml` for `yamllint`).

- **`check-json`** — strict `.json` syntax validation. Does **not** validate `.jsonc`; use JSONC-aware tooling if you need stricter enforcement for `.jsonc` files.
- **`check-yaml`** — `.yml` / `.yaml` parse check.
- **`yamllint`** — YAML style enforcement per `.yamllint.yml`.
- **`actionlint`** — GitHub Actions workflow linting.
- **`check-jsonschema`** — JSON Schema validation for schema valid examples, the template sync manifest at `.template-sync/manifest.yml`, the template sync marker at `.template-sync/marker.yml` when present, plus selected real load-bearing configuration files validated against built-in vendor schemas. Downstream repositories MAY add additional `check-jsonschema` hook entries for their own schema-backed file families.
- **`check-metaschema`** — self-validates project-owned schemas, including the worked-example schema (`schemas/example-config.schema.json`), template sync manifest schema (`schemas/template-sync-manifest.schema.json`), and template sync marker schema (`schemas/template-sync-marker.schema.json`), against their declared JSON Schema Draft 2020-12 metaschema.

Prettier is **opt-in** and is not part of the default data-file toolchain.

> **Schema validation (worked example shipped).** `check-jsonschema` is wired into `.pre-commit-config.yaml` to validate schema valid examples, the template sync manifest (`.template-sync/manifest.yml`) against `schemas/template-sync-manifest.schema.json`, the template sync marker (`.template-sync/marker.yml`) against `schemas/template-sync-marker.schema.json` when present, plus selected real load-bearing configuration files against built-in vendor schemas. A `check-metaschema` hook self-validates project-owned schemas against their declared JSON Schema Draft 2020-12 metaschemas. See [`schemas/README.md`](schemas/README.md) for the worked example, template sync schemas, the canonical downstream removal checklist, and future-work candidates. Downstream repositories MAY add additional `check-jsonschema` hook entries for their own schema-backed file families.

```bash
# Run all pre-commit hooks (includes data-file validators)
pre-commit run --all-files

# Run a specific hook
pre-commit run check-json --all-files
pre-commit run check-yaml --all-files
pre-commit run yamllint --all-files
pre-commit run actionlint --all-files
pre-commit run check-jsonschema --all-files
pre-commit run check-metaschema --all-files
```

#### Terraform Linting

This repository includes Terraform linting via:

- **terraform fmt:** Format checking and auto-formatting
- **terraform validate:** Configuration validation
- **TFLint:** Best practice linting with cloud provider plugins

Configuration: `.tflint.hcl`

```bash
# Format check
terraform fmt -check -recursive -diff

# Format fix
terraform fmt -recursive

# Validate (requires init)
terraform init -backend=false && terraform validate

# Lint
tflint --init
tflint --recursive --config "$(pwd)/.tflint.hcl"
```

### Testing

#### Python Tests

Python tests use pytest with coverage reporting.

```bash
# Run all Python tests
pytest tests/ -v --cov --cov-report=term-missing

# Run a specific test file
pytest tests/test_example.py -v
```

#### JSON Schema Example Tests

```bash
# Run the schema-example contract test (validates schemas/examples/<schema>/{valid,invalid}/ fixtures)
pytest tests/test_schema_examples.py -v
```

The schema-example contract test ([`tests/test_schema_examples.py`](tests/test_schema_examples.py)) auto-discovers `schemas/*.schema.json` and the matching `schemas/examples/<name>/{valid,invalid}/` fixtures and asserts that valid fixtures pass and invalid fixtures fail. A starter version is also available at [`templates/python/tests/test_schema_examples.py`](templates/python/tests/test_schema_examples.py) for downstream adoption.

> **Prerequisite — `check-jsonschema` must be runnable in the pytest environment.** This test shells out to the `check-jsonschema` validator by first using the `check-jsonschema` console script when it is on `PATH`, then falling back to `python -m check_jsonschema` when the package is importable. **A skipped test is not a passing test:** if neither invocation is available, pytest still exits `0`, but no schema validation actually ran. Install it via `pip install -e ".[dev]"` (which pulls in `check-jsonschema` along with the other dev dependencies — see the `[project.optional-dependencies] dev` table in [`pyproject.toml`](pyproject.toml)) or `pip install check-jsonschema` if you only need this one tool; either path makes the package importable, and many environments also put the console script on `PATH`. **`pre-commit install --install-hooks` does NOT** install `check-jsonschema` into the pytest environment — pre-commit installs hook dependencies into its own isolated per-hook environments under `~/.cache/pre-commit/`, which satisfies the pre-commit hook but not this pytest test. To validate schemas through the pre-commit toolchain instead of through this pytest test, run `pre-commit run check-jsonschema --all-files`. Confirm the test reports collected cases (e.g., `N passed`) rather than `N skipped` to know it actually ran.

#### Downstream Partial-Adoption Validation

Downstream repositories that keep `.template-sync/marker.yml` after removing optional modules SHOULD validate the retained template surface with:

```bash
python .template-sync/scripts/validate_downstream_adoption.py --require-marker
```

Use the full upstream test suite (`pre-commit run --all-files` plus the relevant `pytest`, Pester, Terraform, and schema-example tests) when maintaining this template or when a downstream repository intentionally keeps the corresponding test/tool stack. Use the downstream adoption command when `.template-sync/marker.yml` is the source of truth for retained modules and excluded modules are intentionally absent. Run both when changing template-sync manifest/schema contracts or when a downstream repository keeps the upstream helper tests and wants both contract-level and test-level coverage.

Omit `--require-marker` only during exploratory adoption work; without the flag, the command exits successfully with a no-marker message when `.template-sync/marker.yml` is absent.

For cleanup planning, generate a read-only excluded-module report:

```bash
python .template-sync/scripts/report_excluded_module_references.py
```

The report uses a schema-valid `.template-sync/marker.yml` by default. During pre-marker planning, provide the retained modules explicitly and repeat the flag for each retained module:

```bash
python .template-sync/scripts/report_excluded_module_references.py --included-module baseline --included-module agent-instructions
```

Do not combine marker-derived state with `--included-module`; the command rejects ambiguous module sources. Findings are informational and do not make the command fail. The command exits nonzero only for runtime or input failures, such as an invalid manifest, invalid marker, unsafe path, unreadable required file, or unknown explicit module.

Report categories are deterministic so downstream cleanup notes can be compared across runs:

- `required_cleanup`
- `optional_reference_only_cleanup`
- `protected_file_authorization_needed`
- `local_override_recorded`
- `deferred_decision_recorded`
- `documented_reference_only_retention`
- `likely_false_positive_documented_reference`

The deterministic false-positive category is limited to documented references that do not point at local retained files, such as upstream-template blob links or general validation commands that may still apply to retained configuration files. Use the report to identify cleanup scope across manifest-owned paths, retained cross-module files, template-sync inline blocks, validation commands, workflows, pre-commit hooks, Dependabot ecosystems, Markdown links, and protected instruction paths; continue to use `validate_downstream_adoption.py` as the pass/fail validation gate.

#### PowerShell Tests

PowerShell tests use Pester 5.x.

```powershell
# Install Pester if needed
Install-Module -Name Pester -MinimumVersion 5.0 -Force -Scope CurrentUser

# Run all Pester tests
Invoke-Pester -Path tests/ -Output Detailed

# Run a specific test file
Invoke-Pester -Path tests/PowerShell/Placeholder.Tests.ps1
```

CI runs PowerShell tests on Windows, macOS, and Linux to ensure cross-platform compatibility.

See `templates/powershell/Example.Tests.ps1` for a comprehensive Pester test template.

#### Terraform Tests

Terraform tests use the native Terraform test framework (Terraform 1.6+).

```bash
# Run all Terraform tests
terraform test -verbose

# Run specific test file
terraform test -filter=tests/unit.tftest.hcl
```

Tests are located in `modules/*/tests/` directories.

See `templates/terraform/Example.tftest.hcl` for a comprehensive Terraform test template.

### Code Quality

This repository enforces code quality through:

- **Markdown Linting and Link Checking:** markdownlint runs on pre-commit and in CI; offline Markdown link validation runs in CI
- **JSON/YAML Validation:** `check-json` (strict `.json`), `check-yaml`, and `yamllint` run on pre-commit
- **GitHub Actions Linting:** `actionlint` runs on pre-commit
- **Schema Validation:** `check-jsonschema` validates schema valid examples, `.template-sync/manifest.yml`, `.template-sync/marker.yml` when present, and selected real load-bearing configuration files (e.g., `.github/dependabot.yml`) against built-in vendor schemas; `check-metaschema` self-validates project-owned schemas. See [`.github/TEMPLATE_DESIGN_DECISIONS.md`](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/.github/TEMPLATE_DESIGN_DECISIONS.md) (Built-in Schema Validation ADR) for the policy
- **JSON Schemas:** Root-level `schemas/` convention for schema-backed JSON/YAML files
- **GitHub Copilot Instructions:** Guides AI-assisted development
- **Pre-commit Hooks:** Catches issues before they reach CI
- **PSScriptAnalyzer:** PowerShell static analysis with OTBS formatting
- **TFLint:** Terraform linting with configurable rules and cloud provider plugins

### License

MIT License - See [LICENSE](LICENSE) for details.
