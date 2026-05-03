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
- **Multi-Agent Support:** Instruction files for Claude Code, OpenAI Codex CLI, and Gemini Code Assist (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`)
- **Language-Specific Guidelines:** Modular instruction files for Markdown, PowerShell, Python, Terraform, JSON/JSONC, and YAML
- **Linting Configurations:** Pre-configured settings for markdownlint, PSScriptAnalyzer, TFLint, and yamllint
- **Data-File Validation:** Pre-commit hooks for `check-json`, `check-yaml`, `yamllint`, and `actionlint` (GitHub Actions workflows)
- **JSON Schemas:** Root-level `schemas/` directory convention for schema-backed JSON and YAML files
- **Pre-commit Hooks:** Automated code quality checks before commits

### Getting Started

Choose the guide that matches your situation:

- **[Creating a New Repository](GETTING_STARTED_NEW_REPO.md)**: Step-by-step guide for creating a new repository from this template
- **[Adding to an Existing Repository](GETTING_STARTED_EXISTING_REPO.md)**: Guide for adopting template features into an existing repository
- **[Optional Configurations](OPTIONAL_CONFIGURATIONS.md)**: Advanced customization options after initial setup

For template maintainers, see [TEMPLATE_MAINTENANCE.md](TEMPLATE_MAINTENANCE.md).

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
    ├── check-placeholders.yml       # Verifies OWNER/REPO placeholders are replaced
    ├── data-ci.yml                   # JSON/YAML/Actions data-file linting CI
    ├── markdownlint.yml              # Markdown linting CI (markdownlint)
    ├── powershell-ci.yml             # PowerShell linting and testing CI (optional)
    ├── python-ci.yml                 # Python linting and testing CI (optional)
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
├── python/                          # Python project templates
└── powershell/                      # PowerShell test templates
    └── Example.Tests.ps1            # Comprehensive Pester test example

schemas/                             # JSON Schemas for load-bearing JSON/YAML files (Draft 2020-12)

pyproject.toml                       # Python project configuration
.markdownlint.jsonc                  # Markdown linting configuration
.yamllint.yml                        # YAML linting configuration
.pre-commit-config.yaml              # Pre-commit hooks (multi-language)
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
| `.github/workflows/check-placeholders.yml` | CI workflow to verify OWNER/REPO and @OWNER placeholders are replaced after cloning |
| `.github/workflows/data-ci.yml` | Data-file (JSON/YAML/GitHub Actions) linting CI workflow — runs `check-json`, `check-yaml`, `yamllint`, and `actionlint` as a dedicated check that can be required via branch protection |
| `.github/workflows/markdownlint.yml` | Markdown linting CI workflow (uses [markdownlint](https://github.com/DavidAnson/markdownlint)) |
| `.github/workflows/powershell-ci.yml` | PowerShell linting and Pester testing CI workflow (optional - remove if not using PowerShell) |
| `.github/workflows/python-ci.yml` | Python linting and testing CI workflow (optional - remove if not using Python) |
| `.github/workflows/terraform-ci.yml` | Terraform format, validate, lint, test, and security CI workflow (optional - remove if not using Terraform) |
| `.markdownlint.jsonc` | Markdown linting rules prioritizing auto-fixable checks |
| `.yamllint.yml` | YAML linting configuration (2-space indentation, max line length 120 as warning, unquoted GitHub Actions `on:` allowed) |
| `.pre-commit-config.yaml` | Pre-commit hooks for all projects (multi-language) |
| `schemas/` | Root-level JSON Schemas (Draft 2020-12) describing load-bearing JSON and YAML files |
| `AGENTS.md` | Minimal agent entry point instructions for OpenAI Codex CLI and GitHub Copilot coding agent |
| `CLAUDE.md` | Minimal agent entry point instructions plus Claude-specific workflow guidance |
| `GEMINI.md` | Minimal agent entry point instructions for Gemini Code Assist and GitHub Copilot coding agent |
| `pyproject.toml` | Python project configuration with dev dependencies |
| `src/copilot_repo_template/` | Example Python package - rename for your project |
| `tests/` | Test directory with pytest tests (Python) and Pester tests (PowerShell) |
| `templates/powershell/Example.Tests.ps1` | Comprehensive Pester test template with examples |

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

```bash
# Check markdown files
npm run lint:md

# Auto-fix issues
npx markdownlint-cli2 "**/*.md" "#node_modules" --fix
```

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
- **`check-jsonschema`** — JSON Schema validation, scoped to the worked-example schema's valid example data under `schemas/examples/example-config/valid/`. Downstream repositories MAY add additional `check-jsonschema` hook entries for their own schema-backed file families.
- **`check-metaschema`** — self-validates the worked-example schema (`schemas/example-config.schema.json`) against its declared JSON Schema Draft 2020-12 metaschema.

Prettier is **opt-in** and is not part of the default data-file toolchain.

> **Schema validation (worked example shipped).** `check-jsonschema` is wired into `.pre-commit-config.yaml` to validate the template's worked-example schema (`schemas/example-config.schema.json`) and its valid example data under `schemas/examples/example-config/valid/`, plus a `check-metaschema` self-validation hook for the schema itself. See [`schemas/README.md`](schemas/README.md) for the worked example, the canonical downstream removal checklist, and future-work candidates. Downstream repositories MAY add additional `check-jsonschema` hook entries for their own schema-backed file families.

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
terraform fmt -check -recursive

# Format fix
terraform fmt -recursive

# Validate (requires init)
terraform init -backend=false && terraform validate

# Lint
tflint --init && tflint --recursive
```

### Testing

#### Python Tests

Python tests use pytest with coverage reporting.

```bash
# Run all Python tests
pytest tests/ -v --cov --cov-report=term-missing

# Run a specific test file
pytest tests/test_example.py -v

# Run the schema-example contract test (validates schemas/examples/<schema>/{valid,invalid}/ fixtures)
pytest tests/test_schema_examples.py -v
```

The schema-example contract test ([`tests/test_schema_examples.py`](tests/test_schema_examples.py)) auto-discovers `schemas/*.schema.json` and the matching `schemas/examples/<name>/{valid,invalid}/` fixtures and asserts that valid fixtures pass and invalid fixtures fail. A starter version is also available at [`templates/python/tests/test_schema_examples.py`](templates/python/tests/test_schema_examples.py) for downstream adoption.

> **Prerequisite — `check-jsonschema` must be on PATH.** This test shells out to the `check-jsonschema` CLI and uses `@pytest.mark.skipif(shutil.which("check-jsonschema") is None, ...)` to skip every parametrized case when the binary is not available. **A skipped test is not a passing test:** if `check-jsonschema` is missing, pytest still exits `0`, but no schema validation actually ran. Install it via `pip install -e ".[dev]"` (which pulls in `check-jsonschema` along with the other dev dependencies — see the `[project.optional-dependencies] dev` table in [`pyproject.toml`](pyproject.toml)) or `pip install check-jsonschema` if you only need this one tool; either path puts the binary on PATH so `shutil.which` finds it. **`pre-commit install --install-hooks` does NOT** add `check-jsonschema` to PATH — pre-commit installs hook dependencies into its own isolated per-hook environments under `~/.cache/pre-commit/`, which satisfies the pre-commit hook but not the `shutil.which` lookup this pytest test performs. To validate schemas through the pre-commit toolchain instead of through this pytest test, run `pre-commit run check-jsonschema --all-files`. Confirm the test reports collected cases (e.g., `N passed`) rather than `N skipped` to know it actually ran.

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

- **Markdown Linting:** Runs on pre-commit and in CI
- **JSON/YAML Validation:** `check-json` (strict `.json`), `check-yaml`, and `yamllint` run on pre-commit
- **GitHub Actions Linting:** `actionlint` runs on pre-commit
- **JSON Schemas:** Root-level `schemas/` convention for schema-backed JSON/YAML files
- **GitHub Copilot Instructions:** Guides AI-assisted development
- **Pre-commit Hooks:** Catches issues before they reach CI
- **PSScriptAnalyzer:** PowerShell static analysis with OTBS formatting
- **TFLint:** Terraform linting with configurable rules and cloud provider plugins

### License

MIT License - See [LICENSE](LICENSE) for details.
