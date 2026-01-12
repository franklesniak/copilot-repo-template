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

src/
└── copilot_repo_template/           # Example Python package (rename for your project)
    ├── __init__.py
    └── example.py

tests/                               # Example test directory
├── __init__.py
└── test_example.py

templates/                           # Reference templates for project setup
└── python/                          # Python project templates

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
| `.markdownlint.jsonc` | Markdown linting rules prioritizing auto-fixable checks |
| `.pre-commit-config.yaml` | Pre-commit hooks for Python projects (remove if not using Python) |
| `pyproject.toml` | Python project configuration with dev dependencies |
| `src/copilot_repo_template/` | Example Python package - rename for your project |
| `tests/` | Example test directory with pytest tests |

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
   - If using a different layout, update `MYPY_PATHS` in `.github/workflows/python-ci.yml`

##### Remove Python (if not using Python)

If your project doesn't use Python:

```bash
rm -rf src/ tests/ pyproject.toml .pre-commit-config.yaml
rm .github/workflows/python-ci.yml
rm .github/instructions/python.instructions.md
rm -rf templates/python/
```

##### Update Copilot Instructions

Edit `.github/copilot-instructions.md`:

- Add your project-specific "Source of Truth" section
- Update the language-specific instructions table

##### Remove Unused Language Instructions

Remove instruction files for languages you don't use (beyond Python, which is covered above):

```bash
# Example: Remove PowerShell instructions for a Python-only project
rm .github/instructions/powershell.instructions.md
rm -rf .github/linting/
```

##### Update the Instructions Table

Edit the table in `.github/copilot-instructions.md` to reflect your project's languages.

#### 5. Update This README

Replace this content with your actual project documentation.

### Language Support

| Language | Instruction File | File Pattern | Description |
| --- | --- | --- | --- |
| Markdown/Docs | `.github/instructions/docs.instructions.md` | `**/*.md` | Documentation writing standards |
| PowerShell | `.github/instructions/powershell.instructions.md` | `**/*.ps1` | PowerShell coding standards (OTBS, v1.0-v7.x) |
| Python | `.github/instructions/python.instructions.md` | `**/*.py` | Python coding standards (PEP 8, typing) |

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

### Code Quality

This repository enforces code quality through:

- **Markdown Linting:** Runs on pre-commit and in CI
- **GitHub Copilot Instructions:** Guides AI-assisted development
- **Pre-commit Hooks:** Catches issues before they reach CI
- **PSScriptAnalyzer:** PowerShell static analysis with OTBS formatting

### License

MIT License - See [LICENSE](LICENSE) for details.
