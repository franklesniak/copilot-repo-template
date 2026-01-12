# Copilot Repository Template

A template repository providing best-practice GitHub Copilot instructions and linting configurations for new projects.

## What This Template Provides

This template includes:

- **GitHub Copilot Instructions:** Comprehensive coding standards that guide AI-assisted development
- **Language-Specific Guidelines:** Modular instruction files for Markdown, PowerShell, and Python
- **Linting Configurations:** Pre-configured settings for markdownlint and PSScriptAnalyzer
- **Pre-commit Hooks:** Automated code quality checks before commits

## Repository Structure

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

.markdownlint.jsonc                  # Markdown linting configuration
.pre-commit-config.yaml              # Pre-commit hooks (Python focused)
```

### Key Files Explained

| File | Purpose |
| --- | --- |
| `.github/copilot-instructions.md` | The "constitution" for all code changes - defines safety rules, pre-commit discipline, and references language-specific instructions |
| `.github/instructions/*.md` | Language-specific coding standards applied based on file patterns |
| `.github/linting/PSScriptAnalyzerSettings.psd1` | PSScriptAnalyzer settings enforcing OTBS formatting for PowerShell |
| `.markdownlint.jsonc` | Markdown linting rules prioritizing auto-fixable checks |
| `.pre-commit-config.yaml` | Pre-commit hooks for Python projects (remove if not using Python) |

## How to Use This Template

### 1. Create a New Repository

Click **"Use this template"** on GitHub to create a new repository based on this template.

### 2. Install Dependencies

```bash
# Install root dependencies (enables pre-commit hooks via Husky)
npm install

# Install CI workflow dependencies
cd .github/workflows
npm install
cd ../..
```

### 3. (Optional) Install Python Pre-commit Hooks

If your project uses Python:

```bash
pip install pre-commit
pre-commit install
```

### 4. Customize for Your Project

#### Update Copilot Instructions

Edit `.github/copilot-instructions.md`:

- Add your project-specific "Source of Truth" section
- Update the language-specific instructions table

#### Remove Unused Language Instructions

Remove instruction files for languages you don't use:

```bash
# Example: Remove Python instructions for a PowerShell-only project
rm .github/instructions/python.instructions.md
rm .pre-commit-config.yaml
```

#### Update the Instructions Table

Edit the table in `.github/copilot-instructions.md` to reflect your project's languages.

### 5. Update This README

Replace this content with your actual project documentation.

## Language Support

| Language | Instruction File | File Pattern | Description |
| --- | --- | --- | --- |
| Markdown/Docs | `.github/instructions/docs.instructions.md` | `**/*.md` | Documentation writing standards |
| PowerShell | `.github/instructions/powershell.instructions.md` | `**/*.ps1` | PowerShell coding standards (OTBS, v1.0-v7.x) |
| Python | `.github/instructions/python.instructions.md` | `**/*.py` | Python coding standards (PEP 8, typing) |

## Linting Tools

### Markdown Linting

Configuration: `.markdownlint.jsonc`

```bash
# Check markdown files
npm run lint:md

# Auto-fix issues
npx markdownlint-cli2 "**/*.md" "#node_modules" --fix
```

### PowerShell Linting (PSScriptAnalyzer)

Configuration: `.github/linting/PSScriptAnalyzerSettings.psd1`

```powershell
# Check PowerShell files
Invoke-ScriptAnalyzer -Path .\script.ps1 -Settings .\.github\linting\PSScriptAnalyzerSettings.psd1

# Auto-fix formatting issues
Invoke-ScriptAnalyzer -Path .\script.ps1 -Settings .\.github\linting\PSScriptAnalyzerSettings.psd1 -Fix
```

### Python Linting

Configuration: `.pre-commit-config.yaml`

```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Run specific hooks
pre-commit run black --all-files
pre-commit run ruff --all-files
```

## Code Quality

This repository enforces code quality through:

- **Markdown Linting:** Runs on pre-commit and in CI
- **GitHub Copilot Instructions:** Guides AI-assisted development
- **Pre-commit Hooks:** Catches issues before they reach CI
- **PSScriptAnalyzer:** PowerShell static analysis with OTBS formatting

## License

MIT License - See [LICENSE](LICENSE) for details.
