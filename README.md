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
    ├── check-placeholders.yml       # Verifies OWNER/REPO placeholders are replaced
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
| `.github/workflows/check-placeholders.yml` | CI workflow to verify OWNER/REPO placeholders are replaced after cloning |
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

> **Action Item:** Update `.github/ISSUE_TEMPLATE/bug_report.yml` and `.github/ISSUE_TEMPLATE/feature_request.yml` and remove "Python" from the Area dropdown options.

##### Remove PowerShell (if not using PowerShell)

If your project doesn't use PowerShell:

```bash
rm .github/workflows/powershell-ci.yml
rm .github/instructions/powershell.instructions.md
rm -rf .github/linting/
rm -rf tests/PowerShell/
rm -rf templates/powershell/
```

> **Action Item:** Update `.github/ISSUE_TEMPLATE/bug_report.yml` and `.github/ISSUE_TEMPLATE/feature_request.yml` and remove "PowerShell" from the Area dropdown options.

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

##### Template Setup Checklist

After creating a repository from this template, complete the following setup steps:

**Required Setup:**

- [ ] Replace `OWNER/REPO` placeholders in `.github/ISSUE_TEMPLATE/config.yml` with your actual org/repo name
- [ ] Confirm `SECURITY.md` exists and the security reporting path works for your repository
- [ ] Confirm required labels exist in your repository: `bug`, `enhancement`, `documentation` (see [Issue Template Labels](#issue-template-labels) below)
- [ ] Update `pyproject.toml` with your project name, description, and authors (if using Python)
- [ ] Rename or replace `src/copilot_repo_template/` with your package (if using Python)
- [ ] Replace placeholder tests in `tests/` with your actual tests
- [ ] Update `README.md` with your project's documentation

**Optional but Recommended:**

- [ ] **Create the `triage` label** for consistent issue routing and automation. Once created, uncomment `# - triage` in each issue template where you want it applied. See [Issue Template Labels](#issue-template-labels) for creation instructions.

**Optional Setup:**

- [ ] Decide whether to enable [GitHub Discussions](https://docs.github.com/en/discussions) and uncomment the Discussions link in `config.yml`
- [ ] If not enabling Discussions, consider adding a Support section to README and uncommenting the Support/FAQ link in `config.yml`
- [ ] Enable [private vulnerability reporting](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/configuring-private-vulnerability-reporting-for-a-repository) in repository settings
- [ ] Decide whether to keep `blank_issues_enabled: true` in `config.yml` (set to `false` once you have comprehensive templates)

**Validation:**

- [ ] Run `pre-commit run --all-files` to verify linting setup
- [ ] Commit and push to trigger CI validation
- [ ] Verify the placeholder check workflow runs successfully (happens automatically on first push)

##### Post-clone Verification Plan

After completing the setup checklist, perform the following quick verification:

1. **Create a test repository** using GitHub's "Use this template" button to verify template functionality
2. **Open each issue type** once and ensure required fields behave correctly
3. **Click key links** in the issue template chooser:
   - Contributing Guide link
   - Security Vulnerabilities link
   - (If enabled) Discussions link
4. **Verify issue form rendering:**
   - Paste a Python traceback into the Logs/Error Output field
   - Confirm it renders cleanly as plain text (not mangled by Markdown parsing)
5. **Verify security flow:**
   - Navigate to the Security tab
   - Confirm SECURITY.md is accessible
6. **Open a test PR** to verify the PR workflow:
   - Create a trivial change (e.g., add a comment to a file)
   - Open a pull request and confirm:
     - PR template renders correctly
     - Contributing guidelines link works
     - CI workflows trigger as expected
   - Close the test PR without merging

#### Issue Template Labels

The issue templates reference several labels. The default GitHub labels (`bug`, `enhancement`, `documentation`) should already exist in your repository. However, the `triage` label is **not a default GitHub label** and must be created manually if you want to use it.

**Why the `triage` label requires manual setup:**

GitHub does not support auto-creating labels when a repository is created from a template. This is a platform limitation, so the `triage` label is intentionally commented out in the issue templates by default. Once you create the label, you can uncomment it in each template where you want it applied.

**To use the `triage` label:**

1. Create the label in your repository (see instructions below)
2. Uncomment the `# - triage` line in each issue template where you want it:
   - `.github/ISSUE_TEMPLATE/bug_report.yml`
   - `.github/ISSUE_TEMPLATE/documentation_issue.yml`
   - `.github/ISSUE_TEMPLATE/feature_request.yml`

**Create the label using GitHub CLI:**

```bash
gh label create triage --description "Needs triage" --color "d4c5f9"
```

**Or create it manually:**

1. Go to your repository on GitHub
2. Navigate to **Settings** > **Labels**
3. Click **New label**
4. Enter:
   - **Label name:** `triage`
   - **Description:** `Needs triage`
   - **Color:** `d4c5f9` (or choose a purple/lavender color)

> **Note:** The `bug`, `enhancement`, and `documentation` labels are GitHub default labels and should already exist. If any are missing, create them with their standard descriptions and colors.

#### Placeholder Check Workflow

The repository includes a CI workflow (`.github/workflows/check-placeholders.yml`) that verifies `OWNER/REPO` placeholders have been replaced in issue templates and configuration files.

**No configuration required.** The workflow runs automatically on:

- Pull requests to any branch
- Pushes to any branch
- Manual workflow dispatch triggers

The workflow is automatically disabled in the template repository itself (`franklesniak/copilot-repo-template`) and activates when you clone/fork this template.

**What the workflow checks:**

- `OWNER/REPO` placeholders in `.github/ISSUE_TEMPLATE/config.yml` (contact links URLs)
- `OWNER/REPO` placeholders in `CONTRIBUTING.md` (clone instructions, issue links)
- Security contact email placeholders in `SECURITY.md`
- `OWNER/REPO` URLs in any `.github/` files

**If the workflow fails:**

Review the error messages for specific placeholders that need replacement. Refer to the Template Setup Checklist above for customization guidance.

### Language Support

| Language | Instruction File | File Pattern | CI Workflow | Description |
| --- | --- | --- | --- | --- |
| Markdown/Docs | `.github/instructions/docs.instructions.md` | `**/*.md` | `markdownlint.yml` | Documentation writing standards |
| PowerShell | `.github/instructions/powershell.instructions.md` | `**/*.ps1` | `powershell-ci.yml` | PowerShell coding standards (OTBS, v1.0-v7.x) |
| Python | `.github/instructions/python.instructions.md` | `**/*.py` | `ci.yml` | Python coding standards (PEP 8, typing) |

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
