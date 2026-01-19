# Project Name

> **Note:** This repository was created from [`franklesniak/copilot-repo-template`](https://github.com/franklesniak/copilot-repo-template).

## Description

[Add your project description here]

---

## Table of Contents

- [Readme for the Copilot Repository Template](#readme-for-the-copilot-repository-template)
  - [What This Template Provides](#what-this-template-provides)
  - [Repository Structure](#repository-structure)
  - [How to Use This Template](#how-to-use-this-template)
  - [Validating Your New Repository](#validating-your-new-repository)
  - [Language Support](#language-support)
  - [Linting Tools](#linting-tools)
  - [Testing](#testing)
  - [Code Quality](#code-quality)
  - [Template Maintenance](#template-maintenance)
  - [License](#license)

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
├── CODEOWNERS                       # Code ownership for automatic PR review requests
├── copilot-instructions.md          # Repo-wide constitution for all changes
├── dependabot.yml                   # Automated dependency updates configuration
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
| `.github/CODEOWNERS` | Defines code ownership for automatic PR review requests - replace `@OWNER` placeholder |
| `.github/copilot-instructions.md` | The "constitution" for all code changes - defines safety rules, pre-commit discipline, and references language-specific instructions |
| `.github/dependabot.yml` | Dependabot configuration for automated dependency updates - enabled by default |
| `.github/instructions/*.md` | Language-specific coding standards applied based on file patterns |
| `.github/linting/PSScriptAnalyzerSettings.psd1` | PSScriptAnalyzer settings enforcing OTBS formatting for PowerShell |
| `.github/workflows/check-placeholders.yml` | CI workflow to verify OWNER/REPO and @OWNER placeholders are replaced after cloning |
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

##### Customize Node.js Package (if applicable)

If your project uses Node.js/npm beyond the template's dev tooling:

1. **Update `package.json` metadata:**
   - Change `name` to your project name
   - Update `description`, `author`, and `keywords`
   - Set `version` appropriately (keep `1.0.0` or start at `0.1.0`)

2. **Add repository information:**

   ```json
   "repository": {
     "type": "git",
     "url": "https://github.com/YOUR_ORG/YOUR_REPO.git"
   }
   ```

3. **Specify Node.js requirements (if needed):**

   ```json
   "engines": {
     "node": ">=18.0.0"
   }
   ```

   Note: Husky (used for pre-commit hooks) requires Node.js 18 or later.

4. **Add your runtime dependencies** to the `dependencies` section (keep dev tooling in `devDependencies`)

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

**After completing steps 1-4 above:**

1. Delete everything from "Readme for the Copilot Repository Template" section down (including all subsections)
2. Delete `.github/TEMPLATE_GUIDE.md`
3. Write your project's actual documentation above this section
4. Keep the initial note about template origin for reference

**Your final README should contain:**

- Project name and description
- Installation/usage instructions
- Contributing guidelines (or link to CONTRIBUTING.md)
- License information
- Any project-specific documentation

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

**Cause:** The root `pyproject.toml` includes dev dependencies for CI but not all tools configured for pre-commit hooks (like Black).

**Fix:** Install pre-commit globally (`pip install pre-commit`) which manages its own tool environments. Pre-commit downloads and manages its own isolated tool versions, so your `pyproject.toml` dev dependencies don't need to include every linting tool.

#### Recommended First Steps After Clone

##### Template Setup Checklist

After creating a repository from this template, complete the following setup steps.
For detailed customization guidance, see [`.github/TEMPLATE_GUIDE.md`](.github/TEMPLATE_GUIDE.md).

**Required Setup:**

- [ ] Replace `OWNER/REPO` placeholders in `.github/ISSUE_TEMPLATE/config.yml` with your actual org/repo name
- [ ] Replace `@OWNER` in `.github/CODEOWNERS` with your GitHub username or team (or delete the file if not needed)
- [ ] Update `SECURITY.md`: Choose reporting method (email, advisories, or both)
- [ ] Replace `[security contact email]` placeholder if keeping email option
- [ ] If using direct advisories URL (Option C), replace `OWNER/REPO` with actual repository details
- [ ] Confirm required labels exist in your repository: `bug`, `enhancement`, `documentation` (see [Issue Template Labels](#issue-template-labels) below)
- [ ] Update `pyproject.toml` with your project name, description, and authors (if using Python)
- [ ] Rename or replace `src/copilot_repo_template/` with your package (if using Python)
- [ ] Replace placeholder tests in `tests/` with your actual tests
- [ ] Update `README.md` with your project's documentation

**Optional but Recommended:**

- [ ] **Create the `triage` label** for consistent issue routing and automation. Once created, uncomment `# - triage` in each issue template where you want it applied. See [Issue Template Labels](#issue-template-labels) for creation instructions.
- [ ] Configure branch protection rules for your default branch (see [Branch Protection Setup](.github/TEMPLATE_GUIDE.md#branch-protection-setup-recommended) in `.github/TEMPLATE_GUIDE.md`)
- [ ] Test security reporting path (visit URL or send test email)
- [ ] Enable private vulnerability reporting in repository settings if using GitHub Advisories

**Optional Setup:**

- [ ] Review Dependabot configuration (`.github/dependabot.yml`) - disable or customize if needed (see [Disabling Dependabot](#disabling-dependabot-optional) below)
- [ ] Decide whether to enable [GitHub Discussions](https://docs.github.com/en/discussions) and uncomment the Discussions link in `config.yml`
- [ ] If not enabling Discussions, consider adding a Support section to README and uncommenting the Support/FAQ link in `config.yml`
- [ ] Enable [private vulnerability reporting](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/configuring-private-vulnerability-reporting-for-a-repository) in repository settings
- [ ] Decide whether to keep `blank_issues_enabled: true` in `config.yml` (set to `false` once you have comprehensive templates)

**Validation:**

- [ ] Run `pre-commit run --all-files` to verify linting setup
- [ ] Commit and push to trigger CI validation
- [ ] Verify the placeholder check workflow runs successfully (happens automatically on first push)

**Final Steps:**

- [ ] Review detailed customization guidance in `.github/TEMPLATE_GUIDE.md`
- [ ] **Delete `.github/TEMPLATE_GUIDE.md`** after completing all customizations

##### Post-clone Verification Plan

After completing the setup checklist, perform the following quick verification:

1. **Verify template functionality** in your newly created repository (template maintainers can create a separate test repository to verify template changes)
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
- `OWNER/REPO` placeholders in `CONTRIBUTING.md`:
  - Repository clone URL: `https://github.com/OWNER/REPO.git`
  - Issue links: `https://github.com/OWNER/REPO/issues`
- Security contact email placeholders in `SECURITY.md`: `[security contact email]`
- `OWNER/REPO` URLs in any `.github/` files
- `@OWNER` placeholder in `.github/CODEOWNERS`

**If the workflow fails:**

Review the error messages for specific placeholders that need replacement. Replace:

- `OWNER` with your GitHub organization or username
- `REPO` with your repository name
- `@OWNER` with your GitHub username or team (e.g., `@octocat` or `@my-org/maintainers`)
- `[security contact email]` with your actual security contact email (or remove if using GitHub Advisories only)

Refer to the Template Setup Checklist above for complete customization guidance.

#### Disabling Dependabot (Optional)

Dependabot is enabled by default for security monitoring. It automatically creates pull
requests when dependency updates or security vulnerabilities are detected.

**To disable Dependabot:**

Delete `.github/dependabot.yml` from your repository. Dependabot will stop monitoring
immediately.

**To customize Dependabot:**

Edit `.github/dependabot.yml` to adjust update frequency, add/remove ecosystems, or
modify grouping rules. See [GitHub Dependabot documentation](https://docs.github.com/en/code-security/dependabot)
for configuration options.

**Why it's enabled by default:**

- Automated detection of security vulnerabilities in dependencies
- Reduces maintenance burden for keeping dependencies current
- Template repositories should model security best practices
- Weekly schedule with grouped updates minimizes PR noise

#### Code Owners Configuration

The template includes a `.github/CODEOWNERS` file that enables automatic review requests
for pull requests. Code owners are automatically requested to review PRs that modify
files they own.

**To customize CODEOWNERS:**

Replace `@OWNER` with your GitHub username (e.g., `@octocat`) or team name
(e.g., `@my-org/maintainers`).

**To disable CODEOWNERS:**

Delete `.github/CODEOWNERS` if automatic review assignment is not needed.

**What CODEOWNERS provides:**

- Automatic review requests for PRs affecting specific paths
- Works with branch protection "required reviews from code owners" setting
- Documents code ownership explicitly in the repository

See [GitHub CODEOWNERS documentation](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
for additional configuration options.

### Language Support

| Language | Instruction File | File Pattern | CI Workflow | Description |
| --- | --- | --- | --- | --- |
| Markdown/Docs | `.github/instructions/docs.instructions.md` | `**/*.md` | `.github/workflows/markdownlint.yml` | Documentation writing standards |
| PowerShell | `.github/instructions/powershell.instructions.md` | `**/*.ps1` | `.github/workflows/powershell-ci.yml` | PowerShell coding standards (OTBS, v1.0-v7.x) |
| Python | `.github/instructions/python.instructions.md` | `**/*.py` | `.github/workflows/ci.yml` | Python coding standards (PEP 8, typing) |

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
