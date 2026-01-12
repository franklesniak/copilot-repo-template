# Project Name

> **Note:** This repository was created from [`franklesniak/copilot-repo-template`](https://github.com/franklesniak/copilot-repo-template).

## Description

[Add your project description here]

---

## Readme for the Copilot Repository Template

This is a template repository providing best-practice GitHub Copilot instructions and linting configurations for new projects.

### What This Template Provides

This template includes:

- **GitHub Copilot Instructions:** Comprehensive coding standards that guide AI-assisted development
- **Language-Specific Guidelines:** Modular instruction files for Markdown, PowerShell, and Python
- **Linting Configurations:** Pre-configured settings for markdownlint and PSScriptAnalyzer
- **Pre-commit Hooks:** Automated code quality checks before commits

### Repository Structure

```text
.github/
├── copilot-instructions.md          # Repo-wide constitution for all changes
├── instructions/                    # Language-specific coding standards
│   ├── docs.instructions.md         # Markdown/documentation standards
│   ├── powershell.instructions.md   # PowerShell coding standards
│   └── python.instructions.md       # Python coding standards
├── linting/                         # Linting tool configurations
│   └── PSScriptAnalyzerSettings.psd1  # PowerShell linting settings
├── scripts/                         # Helper scripts for CI/tooling
└── workflows/                       # GitHub Actions workflows
    └── powershell-ci.yml            # PowerShell linting and testing CI (optional)

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

pyproject.toml                       # Python project configuration
.markdownlint.jsonc                  # Markdown linting configuration
.pre-commit-config.yaml              # Pre-commit hooks (Python focused)
```

#### Key Files Explained

| File | Purpose |
| --- | --- |
| `.github/copilot-instructions.md` | The "constitution" for all code changes - defines safety rules, pre-commit discipline, and references language-specific instructions |
| `.github/instructions/*.md` | Language-specific coding standards applied based on file patterns |
| `.github/linting/PSScriptAnalyzerSettings.psd1` | PSScriptAnalyzer settings enforcing OTBS formatting for PowerShell |
| `.github/workflows/powershell-ci.yml` | PowerShell linting and Pester testing CI workflow (optional - remove if not using PowerShell) |
| `.markdownlint.jsonc` | Markdown linting rules prioritizing auto-fixable checks |
| `.pre-commit-config.yaml` | Pre-commit hooks for Python projects (remove if not using Python) |
| `pyproject.toml` | Python project configuration with dev dependencies |
| `src/copilot_repo_template/` | Example Python package - rename for your project |
| `tests/` | Test directory with pytest tests (Python) and Pester tests (PowerShell) |
| `templates/powershell/Example.Tests.ps1` | Comprehensive Pester test template with examples |

### How to Use This Template

#### 1. Create a New Repository

Click **"Use this template"** on GitHub to create a new repository based on this template.

#### 2. Install Dependencies

```bash
# Install root dependencies (enables pre-commit hooks via Husky)
npm install

# Install CI workflow dependencies
cd .github/workflows
npm install
cd ../..
```

#### 3. (Optional) Install Python Pre-commit Hooks

If your project uses Python:

```bash
pip install pre-commit
pre-commit install
```

#### 4. Customize for Your Project

##### Customize Python Package (if using Python)

The template includes a working Python project structure. To customize it for your project:

1. **Rename the package directory:**

   ```bash
   # Replace 'your_package_name' with your project's package name
   mv src/copilot_repo_template src/your_package_name
   ```

2. **Update `pyproject.toml`:**
   - Change `name = "copilot-repo-template"` to your project name
   - Update `description`, `authors`, and `keywords`
   - Add your runtime dependencies to the `dependencies` list
   - See `templates/python/pyproject.toml` for additional tooling configuration (Black, Ruff)

3. **Replace example code:**
   - Replace `src/your_package_name/example.py` with your actual modules
   - Replace `tests/test_example.py` with your actual tests
   - Update imports in test files to match your package name

4. **Update CI workflow paths (if needed):**
   - The workflow expects `src/` and `tests/` directories
   - If using a different layout, update `MYPY_PATHS` in `.github/workflows/ci.yml`

##### Remove Python (if not using Python)

If your project doesn't use Python:

```bash
rm -rf src/ tests/ pyproject.toml .pre-commit-config.yaml
rm .github/workflows/ci.yml
rm .github/instructions/python.instructions.md
rm -rf templates/python/
```

##### Remove PowerShell (if not using PowerShell)

If your project doesn't use PowerShell:

```bash
rm .github/workflows/powershell-ci.yml
rm .github/instructions/powershell.instructions.md
rm -rf .github/linting/
rm -rf tests/PowerShell/
rm -rf templates/powershell/
```

##### Update Copilot Instructions

Edit `.github/copilot-instructions.md`:

- Add your project-specific "Source of Truth" section
- Update the language-specific instructions table to reflect your project's languages

#### 5. Update This README

Replace this content with your actual project documentation.

### Validating Your New Repository

After creating a repository from this template, validate your setup before adding custom code.

#### Testing CI on First Clone

Before making changes, run CI checks locally to ensure the template is working correctly:

```bash
# Run pre-commit hooks (requires pre-commit to be installed globally)
pre-commit run --all-files
```

For Python projects:

```bash
# Run pytest
pytest tests/ -v
```

For PowerShell projects:

```powershell
# Run Pester tests
Invoke-Pester -Path tests/ -Output Detailed
```

CI workflows will also run automatically when you push to GitHub.

#### Common CI Failures on Fresh Clone

##### Python: ModuleNotFoundError or Import Errors

**Cause:** The template's `pyproject.toml` references the `copilot_repo_template` package in `src/`.

**Fix:** Either rename `src/copilot_repo_template/` to match your project name and update `pyproject.toml`, OR delete the example package and create your own structure.

**Alternative:** If not using Python, remove the `src/` directory and Python-related CI steps (see "Remove Python" instructions above).

##### Python: mypy Path Errors

**Cause:** The `MYPY_PATHS` environment variable in `.github/workflows/ci.yml` defaults to `src/ tests/`.

**Fix:** Update `MYPY_PATHS` to match your project structure. See `templates/python/README.md` for configuration examples.

##### PowerShell: PSScriptAnalyzer Warnings on Empty Test Files

**Cause:** The placeholder test file has minimal content.

**Fix:** Replace `tests/PowerShell/Placeholder.Tests.ps1` with actual tests or add real functions to test.

##### Pre-commit: Black/Ruff Not Installed

**Cause:** The root `pyproject.toml` has minimal dev dependencies; full tooling configuration is in `templates/python/pyproject.toml`.

**Fix:** Either install pre-commit globally (`pip install pre-commit`) which manages its own tool environments, OR copy the fuller dependencies from `templates/python/pyproject.toml`.

#### Recommended First Steps After Clone

- [ ] Update `pyproject.toml` with your project name, description, and authors
- [ ] Rename or replace `src/copilot_repo_template/` with your package
- [ ] Replace placeholder tests in `tests/` with your actual tests
- [ ] Update `README.md` with your project's documentation
- [ ] Run `pre-commit run --all-files` to verify setup
- [ ] Commit and push to trigger CI validation

### Language Support

| Language | Instruction File | File Pattern | CI Workflow | Description |
| --- | --- | --- | --- | --- |
| Markdown/Docs | `.github/instructions/docs.instructions.md` | `**/*.md` | `markdownlint.yml` | Documentation writing standards |
| PowerShell | `.github/instructions/powershell.instructions.md` | `**/*.ps1` | `powershell-ci.yml` | PowerShell coding standards (OTBS, v1.0-v7.x) |
| Python | `.github/instructions/python.instructions.md` | `**/*.py` | `ci.yml` | Python coding standards (PEP 8, typing) |

### Linting Tools

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
pre-commit run ruff --all-files
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

### Code Quality

This repository enforces code quality through:

- **Markdown Linting:** Runs on pre-commit and in CI
- **GitHub Copilot Instructions:** Guides AI-assisted development
- **Pre-commit Hooks:** Catches issues before they reach CI
- **PSScriptAnalyzer:** PowerShell static analysis with OTBS formatting
- **Auto-fix Workflow:** Automatically commits pre-commit fixes on PRs (optional)

#### Auto-fix Pre-commit Workflow

The repository includes an optional workflow (`.github/workflows/auto-fix-precommit.yml`)
that automatically commits pre-commit fixes when they occur on pull requests. This is
particularly useful for:

- **AI-assisted development:** When using GitHub Copilot Coding Agent or similar tools,
  formatting fixes are automatically committed without manual intervention
- **Streamlined PRs:** Contributors don't need to manually run pre-commit and commit fixes

If you prefer to manually commit pre-commit fixes, you can safely delete the
`auto-fix-precommit.yml` workflow file. The standard `ci.yml` workflow will
still run pre-commit checks and report any issues.

### Template Maintenance

When using this template, periodically perform the following maintenance tasks:

#### Update Pre-commit Hooks

Pre-commit hooks should be kept up-to-date for security and compatibility:

```bash
# Check for and apply updates to pre-commit hooks
pre-commit autoupdate

# Test that updated hooks work correctly
pre-commit run --all-files
```

#### Review Python Version Requirements

This template requires Python versions that are currently receiving bugfix updates. Check the [Python Developer's Guide - Versions](https://devguide.python.org/versions/) page annually (typically around October when new Python versions are released) to ensure your minimum Python version is still supported.

#### Review Instruction File Versions

The instruction files in `.github/instructions/` include version numbers in the format `Major.Minor.YYYYMMDD.Revision`. Periodically review these to ensure they remain current with your project's coding standards.

### License

MIT License - See [LICENSE](LICENSE) for details.
