# Getting Started: Adding Template Features to an Existing Repository

This guide walks you through adopting features from `franklesniak/copilot-repo-template` into your **existing repository**. Unlike creating a new repository from a template, integrating template features into an existing project requires careful planning to avoid conflicts with your current configuration.

> **Looking to create a new repository?** See [GETTING_STARTED_NEW_REPO.md](GETTING_STARTED_NEW_REPO.md) instead.

**Recommendation:** Read through this entire guide before starting. This helps you plan which features to adopt and in what order.

**Estimated time to complete:** 15-60 minutes (varies based on scope of adoption)

---

## Table of Contents

- [What This Template Provides](#what-this-template-provides)
- [Prerequisites](#prerequisites)
  - [Existing Repository Requirements](#existing-repository-requirements)
  - [Tools Needed](#tools-needed)
- [Planning Your Adoption](#planning-your-adoption)
  - [Feature Decision Matrix](#feature-decision-matrix)
  - [Recommended Adoption Order](#recommended-adoption-order)
- [Getting the Template Files](#getting-the-template-files)
  - [Files to Skip (Example/Demonstration Code)](#files-to-skip-exampledemonstration-code)
- [Adopting Simple Standalone Files](#adopting-simple-standalone-files)
  - [CODEOWNERS](#codeowners)
  - [Dependabot](#dependabot)
  - [Security Policy](#security-policy)
- [Adopting Issue Templates](#adopting-issue-templates)
  - [Full Adoption](#full-adoption-recommended-if-you-have-none)
  - [Partial Adoption](#partial-adoption-if-you-have-existing-templates)
  - [Customizing Area Dropdowns](#customizing-area-dropdowns)
  - [Creating Required Labels](#creating-required-labels)
- [Adopting PR Template](#adopting-pr-template)
  - [Simple Adoption](#simple-adoption)
  - [Customization Needed](#customization-needed)
  - [Merging with Existing PR Template](#merging-with-existing-pr-template)
- [Adopting GitHub Copilot Instructions](#adopting-github-copilot-instructions)
  - [Main Instructions File](#main-instructions-file)
  - [Language-Specific Instructions](#language-specific-instructions)
  - [Merging with Existing Copilot Instructions](#merging-with-existing-copilot-instructions)
  - [Creating Instructions for Other Languages](#creating-instructions-for-other-languages)
- [Adopting Markdown Linting](#adopting-markdown-linting)
  - [If You Don't Have package.json](#if-you-dont-have-packagejson)
  - [If You Already Have package.json](#if-you-already-have-packagejson)
  - [Copying the Configuration](#copying-the-configuration)
  - [Testing Markdown Linting](#testing-markdown-linting)
- [Adopting Pre-commit Hooks](#adopting-pre-commit-hooks)
  - [If You Don't Have Pre-commit Configured](#if-you-dont-have-pre-commit-configured)
  - [If You Already Have Pre-commit Configured](#if-you-already-have-pre-commit-configured)
  - [Customizing Hooks](#customizing-hooks)
- [Adopting CI Workflows](#adopting-ci-workflows)
  - [Understanding Workflow Dependencies](#understanding-workflow-dependencies)
  - [Markdown Lint Workflow](#markdown-lint-workflow)
  - [Auto-fix Pre-commit Workflow](#auto-fix-pre-commit-workflow)
  - [Placeholder Check Workflow](#placeholder-check-workflow)
  - [Python CI Workflow](#python-ci-workflow)
  - [PowerShell CI Workflow](#powershell-ci-workflow)
  - [Merging with Existing CI](#merging-with-existing-ci)
- [Adopting PSScriptAnalyzer Configuration](#adopting-psscriptanalyzer-configuration)
  - [Copying the Configuration](#copying-the-configuration-1)
  - [Using the Configuration](#using-the-configuration)
  - [Customizing Rules](#customizing-rules)
- [Validation and Testing](#validation-and-testing)
  - [Verify All Configurations Work](#verify-all-configurations-work)
  - [Troubleshooting Common Issues](#troubleshooting-common-issues)
- [Cleanup and Documentation](#cleanup-and-documentation)
  - [Files to Review After Adoption](#files-to-review-after-adoption)
  - [Updating Your Project Documentation](#updating-your-project-documentation)
- [Next Steps](#next-steps)
- [Summary Checklist](#summary-checklist)

---

## What This Template Provides

This template repository includes several features you can adopt individually or together:

| Feature | Description |
| --- | --- |
| **GitHub Copilot Instructions** | Comprehensive coding standards that guide AI-assisted development |
| **Issue Templates** | Structured templates for bug reports, feature requests, and documentation issues |
| **PR Template** | Checklist-based template for consistent pull request reviews |
| **CI Workflows** | GitHub Actions workflows for linting, testing, and validation |
| **Pre-commit Hooks** | Automated code quality checks before commits |
| **Linting Configurations** | Pre-configured settings for markdownlint and PSScriptAnalyzer |
| **Dependabot** | Automated dependency update monitoring |
| **CODEOWNERS** | Automatic reviewer assignment for pull requests |

---

## Prerequisites

### Existing Repository Requirements

Before adopting template features, ensure your repository meets these requirements:

- [ ] **GitHub remote configured:** Your repository must be hosted on GitHub
- [ ] **Clean working tree:** All changes should be committed (`git status` shows no pending changes)
- [ ] **Working on a feature branch:** Recommended to avoid issues with your main branch

**Create a feature branch for this work:**

```bash
# Navigate to your repository
cd /path/to/your/repository

# Ensure you're on your main branch and up to date
git checkout main
git pull origin main

# Create a feature branch for template adoption
git checkout -b feature/adopt-template-features
```

### Tools Needed

The tools you need depend on which features you plan to adopt:

| Feature | Required Tools |
| --- | --- |
| Issue Templates, PR Template, CODEOWNERS, Dependabot | None (GitHub web interface only) |
| Copilot Instructions | None |
| Markdown Linting | Node.js |
| Pre-commit Hooks | Python, pre-commit |
| Python CI Workflow | Python |
| PowerShell CI Workflow | PowerShell |

**Verify your installations:**

**Windows (PowerShell):**

```powershell
# Check Git version
git --version

# Check Python version (if adopting Python features or pre-commit)
# Python 3.9+ is required for pre-commit hooks and CI workflows
python --version

# Check Node.js version (if adopting markdown linting)
node --version
```

**macOS/Linux/FreeBSD:**

```bash
# Check Git version
git --version

# Check Python version (if adopting Python features or pre-commit)
# Python 3.9+ is required for pre-commit hooks and CI workflows
python3 --version

# Check Node.js version (if adopting markdown linting)
node --version
```

> **Need to install these tools?** See the [Prerequisites section in GETTING_STARTED_NEW_REPO.md](GETTING_STARTED_NEW_REPO.md#prerequisites) for detailed installation instructions.

---

## Planning Your Adoption

### Feature Decision Matrix

Use this matrix to decide which features to adopt based on complexity and dependencies:

| Feature | Files Involved | Dependencies | Complexity |
| --- | --- | --- | --- |
| Issue Templates | `.github/ISSUE_TEMPLATE/` | None | Low |
| PR Template | `.github/pull_request_template.md` | None | Low |
| Copilot Instructions | `.github/copilot-instructions.md`, `.github/instructions/` | None | Low |
| CODEOWNERS | `.github/CODEOWNERS` | None | Low |
| Dependabot | `.github/dependabot.yml` | None | Low |
| Security Policy | `SECURITY.md` | None | Low |
| VS Code Settings | `.vscode/settings.json` | None | Low |
| Markdown Linting | `.markdownlint.jsonc`, `package.json`, npm scripts | Node.js | Medium |
| Pre-commit Hooks | `.pre-commit-config.yaml` | Python, pre-commit | Medium |
| PowerShell CI Workflow | `.github/workflows/powershell-ci.yml` | PowerShell, Pester | Medium |
| PSScriptAnalyzer Config | `.github/linting/PSScriptAnalyzerSettings.psd1` | PowerShell | Low |
| Python CI Workflow | `.github/workflows/ci.yml` | Python project structure | High |

### Recommended Adoption Order

For the smoothest experience, adopt features in this order:

1. **Simple standalone files first** — CODEOWNERS, Dependabot, Security Policy
2. **Issue/PR templates** — Low complexity, immediate usability improvements
3. **Copilot instructions** — Enhances AI-assisted development
4. **Linting configurations** — Establishes code quality standards
5. **CI workflows** — Most complex, most dependencies; adopt last

> **Tip:** You don't need to adopt everything. Pick the features that provide the most value for your project.

---

## Getting the Template Files

Choose the method that works best for your situation:

### Option A: Clone Template Separately (Recommended)

This method gives you easy access to all template files for reference and copying.

**Windows (PowerShell):**

```powershell
# Create a temporary directory
mkdir $env:USERPROFILE\template-source
cd $env:USERPROFILE\template-source

# Clone the template repository
git clone https://github.com/franklesniak/copilot-repo-template.git
```

**macOS/Linux/FreeBSD:**

```bash
# Create a temporary directory
mkdir ~/template-source
cd ~/template-source

# Clone the template repository
git clone https://github.com/franklesniak/copilot-repo-template.git
```

### Option B: Download as ZIP

1. Navigate to <https://github.com/franklesniak/copilot-repo-template>
2. Click the green **Code** button
3. Select **Download ZIP**
4. Extract to a known location (e.g., `~/template-source/` or `C:\template-source\`)

### Option C: Use GitHub's Web Interface

Best for adopting just one or two files:

1. Navigate to the file you want in the template repository
2. Click the file to view its contents
3. Click the **Raw** button to see the raw content
4. Copy the content and paste into a new file in your repository

### Files to Skip (Example/Demonstration Code)

The template repository includes example Python source code and tests that demonstrate coding standards. These files are intended for new repositories created from the template and should **NOT** be copied to existing repositories:

| File/Directory | Purpose | Action |
| --- | --- | --- |
| `src/copilot_repo_template/` | Example Python package demonstrating coding standards | Do not copy |
| `tests/test_example.py` | Example pytest tests for the demo package | Do not copy |
| `tests/__init__.py` | Package marker with template-specific docstring | Do not copy |
| `pyproject.toml` | Configured for the template's example package | Copy only if you need a starting point, then heavily customize |

If you already have Python tests in your existing repository, these template example files would conflict with your existing setup.

**What you SHOULD copy:**

- `.github/` directory contents (workflows, instructions, templates)
- Configuration files (`.markdownlint.jsonc`, `.pre-commit-config.yaml`)
- Community health files (`CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`)
- `templates/` directory (reference templates for starting new test files)

If your existing repository lacks Python project structure and you want to adopt the template's Python CI workflow, see the [Python CI Workflow](#python-ci-workflow) section below for guidance on setting up your own `pyproject.toml` and test structure.

---

## Adopting Simple Standalone Files

These files can be copied directly with minimal modifications.

### CODEOWNERS

The CODEOWNERS file automatically assigns reviewers to pull requests based on file paths.

**Location:** `.github/CODEOWNERS`

**Steps:**

1. **If you don't have a CODEOWNERS file:**
   - Copy `.github/CODEOWNERS` from the template to your `.github/` directory
   - Replace `@OWNER` with your GitHub username or team name

2. **If you already have a CODEOWNERS file:**
   - Review the template's file for patterns you may want to add
   - Merge entries manually, keeping your existing ownership rules

**Example customization:**

```text
# Default owners for everything in the repo
* @your-username

# Workflow files require maintainer review
.github/workflows/ @your-username

# Copilot instructions require maintainer review
.github/copilot-instructions.md @your-username
.github/instructions/ @your-username
```

### Dependabot

Dependabot automatically creates pull requests to update your dependencies.

**Location:** `.github/dependabot.yml`

**Steps:**

1. **If you don't have a dependabot.yml file:**
   - Copy `.github/dependabot.yml` from the template
   - Remove ecosystems you don't use:
     - Remove the `npm` section if you don't use Node.js
     - Remove the `pip` section if you don't use Python
     - Keep the `github-actions` section (recommended for all repositories)

2. **If you already have a dependabot.yml file:**
   - Review the template's grouping strategy (groups minor/patch updates)
   - Consider adopting the commit message prefix convention (`chore(deps)`)
   - Merge any ecosystems you want to add

**Example: Dependabot for a Python-only project:**

```yaml
version: 2
updates:
  # Python dependencies (pyproject.toml)
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    groups:
      pip-minor-patch:
        patterns:
          - "*"
        update-types:
          - "minor"
          - "patch"
    commit-message:
      prefix: "chore(deps)"
    open-pull-requests-limit: 10

  # GitHub Actions (workflows)
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    groups:
      actions-minor-patch:
        patterns:
          - "*"
        update-types:
          - "minor"
          - "patch"
    commit-message:
      prefix: "chore(deps)"
    open-pull-requests-limit: 10
```

### Security Policy

The security policy tells users how to report security vulnerabilities.

**Location:** `SECURITY.md` (repository root)

**Steps:**

1. **If you don't have a SECURITY.md file:**
   - Copy `SECURITY.md` from the template to your repository root
   - Replace `[security contact email]` with your email address
   - Or remove the email option and use only GitHub Security Advisories (for public repositories)

2. **If you already have a SECURITY.md file:**
   - Review the template's structure for ideas
   - Consider adding sections you may be missing (response timeline, disclosure policy)

> **Note:** Private vulnerability reporting via GitHub Security Advisories is only available for **public repositories**. If your repository is private, you must provide an email contact in SECURITY.md. Use a dedicated security email (e.g., `security@your-domain.com`) rather than a personal email when possible.

### VS Code Settings

The `.vscode/settings.json` file customizes VS Code behavior for your repository. The template includes a placeholder window title.

**Location:** `.vscode/settings.json`

**Steps:**

1. **If you don't have a `.vscode/settings.json` file:**
   - Copy `.vscode/settings.json` from the template to your `.vscode/` directory
   - Replace the `window.title` value with your repository name

2. **If you already have a `.vscode/settings.json` file:**
   - Review the template's file for settings you may want to add
   - Consider adding the `window.title` setting for easier workspace identification

**Example customization:**

```json
{
    "window.title": "my-awesome-project"
}
```

---

## Adopting Issue Templates

The template includes three issue templates: bug reports, feature requests, and documentation issues.

### Full Adoption (Recommended if You Have None)

If your repository doesn't have issue templates, adopt the full set:

1. Copy the entire `.github/ISSUE_TEMPLATE/` directory to your repository's `.github/` directory

2. **Update `config.yml`:** Replace `OWNER/REPO` placeholders with your actual organization/username and repository name:

   ```yaml
   # Before
   url: https://github.com/OWNER/REPO/blob/HEAD/CONTRIBUTING.md

   # After
   url: https://github.com/your-username/your-repo/blob/HEAD/CONTRIBUTING.md
   ```

3. **Review and customize each template** (see [Customizing Area Dropdowns](#customizing-area-dropdowns))

### Partial Adoption (If You Have Existing Templates)

If you already have issue templates:

1. Compare the template files with your existing templates
2. Copy specific templates you want to add (e.g., just `documentation_issue.yml`)
3. If you have a `config.yml`, merge the `contact_links` sections

### Customizing Area Dropdowns

The issue templates include an "Area" dropdown with default options. Customize for your project:

**In `bug_report.yml` and `feature_request.yml`:**

```yaml
# Default options - modify for your project
options:
  - Python
  - PowerShell
  - Markdown / Documentation
  - GitHub Actions / CI
  - Cross-language / Integration
  - Cross-cutting / Repo-wide
  - Other (describe/specify in Additional Context)
```

**Example for a JavaScript/TypeScript project:**

```yaml
options:
  - Frontend (React)
  - Backend (Node.js)
  - API
  - Documentation
  - CI/CD
  - Other (describe in Additional Context)
```

> **Tip:** Update the Area dropdown in both template files to keep them consistent.

### Creating Required Labels

The issue templates use labels that should exist in your repository:

**Default GitHub labels (already exist in most repositories):**

- `bug` — Used by bug_report.yml
- `enhancement` — Used by feature_request.yml
- `documentation` — Used by documentation_issue.yml

**Optional label to create:**

The templates include a commented-out `triage` label. To use it:

**Windows (PowerShell) / macOS / Linux:**

```bash
# Using GitHub CLI
gh label create triage --description "Needs triage" --color "d4c5f9"
```

**Or via GitHub web UI:**

1. Go to your repository
2. Click **Issues** or **Pull requests**
3. Above the list, click **Labels**
4. Click **New label**
5. Under "Label name", type `triage`
6. Under "Description", type `Needs triage`
7. Edit the color hexadecimal number to `d4c5f9` (light purple)
8. Click **Create label**

After creating the label, uncomment the `- triage` line in each issue template.

---

## Adopting PR Template

The pull request template provides a checklist for contributors.

### Simple Adoption

If you don't have a PR template:

1. Copy `.github/pull_request_template.md` to your `.github/` directory
2. Review the sections and remove any that don't apply to your project

### Customization Needed

Review these sections and modify as needed:

**Language-specific sections:**

- **Python-Specific:** Remove if your project doesn't use Python
- **PowerShell-Specific:** Remove if your project doesn't use PowerShell

**Pre-commit section:**

- Remove the "Pre-commit Verification" section if you're not adopting pre-commit hooks

**Contributing guidelines link:**

The template uses a relative link that works for most repositories:

```markdown
[contributing guidelines](../blob/HEAD/CONTRIBUTING.md)
```

If your CONTRIBUTING.md is in a different location, update this link.

### Merging with Existing PR Template

If you already have a PR template:

1. **Keep your existing structure** — Don't replace what's working
2. **Add relevant checklist items** from the template that you're missing
3. **Consider adopting:**
   - The "Type of Change" section (if you don't have one)
   - Language-specific checklists
   - The pre-commit verification checkbox (if adopting pre-commit)

**Example: Adding a "Type of Change" section to your existing template:**

```markdown
## Type of Change

<!-- Check all that apply -->

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Dependencies update
- [ ] Configuration/tooling change
```

---

## Adopting GitHub Copilot Instructions

GitHub Copilot Instructions guide AI-assisted development by providing project-specific coding standards and rules. The template includes both a main instructions file and language-specific instruction files.

### Main Instructions File

**Location:** `.github/copilot-instructions.md`

This file serves as the "constitution" for all Copilot suggestions in your repository. It contains:

- Safety and security rules (non-negotiable)
- Pre-commit discipline requirements
- Language-specific guideline references
- Linting and testing configurations

**Steps:**

1. Copy `.github/copilot-instructions.md` to your `.github/` directory

2. **Customize the "Source of Truth" section** — Point to your project's authoritative documentation:

   ```markdown
   ## Source of Truth

   > **Customize this section** for your project. Point to your authoritative specification or design document. Example:
   >
   > - Read **`docs/spec/requirements.md`** before making changes.
   > - If any instruction here conflicts with the spec, **the spec wins**.
   ```

3. **Update the language table** — Modify to reflect your project's languages:

   ```markdown
   | Language | Instruction File | Applies To |
   | --- | --- | --- |
   | Markdown/Docs | `.github/instructions/docs.instructions.md` | `**/*.md` |
   | Python | `.github/instructions/python.instructions.md` | `**/*.py` |
   | PowerShell | `.github/instructions/powershell.instructions.md` | `**/*.ps1` |
   ```

4. **Review and modify:**
   - **Pre-commit section** — Update if using different tools or workflows
   - **Testing section** — Update for your test frameworks and locations

5. **Update linting and testing tables** — Modify to reflect your project's languages:
   - **Linting Configurations table** — Remove the PSScriptAnalyzer row if not using PowerShell
   - **Testing Tools table** — Remove rows for languages you're not using (Python row if not using Python, PowerShell row if not using PowerShell)

### Language-Specific Instructions

**Location:** `.github/instructions/`

These files use `applyTo` front matter to automatically apply to matching file patterns:

```yaml
---
applyTo: "**/*.py"
description: "Python coding standards for this repository"
---
```

**Available instruction files:**

| File | Purpose | Recommended For |
| --- | --- | --- |
| `docs.instructions.md` | Markdown/documentation standards | All projects |
| `python.instructions.md` | Python coding standards | Python projects |
| `powershell.instructions.md` | PowerShell coding standards | PowerShell projects |

**Adoption options:**

1. **Full adoption:** Copy the entire `.github/instructions/` directory
2. **Selective adoption:** Copy only the files relevant to your project's languages

### Merging with Existing Copilot Instructions

If you already have a `.github/copilot-instructions.md` file:

1. **Review both files** — Compare your existing instructions with the template

2. **Merge safety rules** — The template's non-negotiable safety rules are security-focused:
   - No secrets in code or repo
   - Treat all external input as untrusted
   - Allowlisted file access only

   Consider adopting these if not already present.

3. **Merge language guidelines** — Add references to language instruction files

4. **Keep your project-specific guidance** — Preserve any custom rules specific to your project

### Creating Instructions for Other Languages

If your project uses languages not covered by the template (JavaScript, TypeScript, Go, Rust, etc.):

1. Use an existing instruction file as a template

2. Create a new file following the naming pattern: `{language}.instructions.md`

3. Add the `applyTo` front matter:

   ```yaml
   ---
   applyTo: "**/*.ts"
   description: "TypeScript coding standards for this repository"
   ---
   ```

4. Define your project's coding standards for that language

5. Update the language table in `.github/copilot-instructions.md`

---

## Adopting Markdown Linting

Markdown linting enforces consistent formatting across your documentation. The template uses markdownlint-cli2 with a configuration optimized for auto-fixable rules.

**Required files:**

- `.markdownlint.jsonc` — Linting rules configuration
- `package.json` — npm scripts and dependencies

**Optional files:**

- `.github/workflows/markdownlint.yml` — CI workflow
- `.github/scripts/lint-nested-markdown.js` — Lints markdown in code blocks

### If You Don't Have package.json

If your project doesn't have a `package.json`:

1. Copy `package.json` from the template

2. Update the metadata for your project:

   ```json
   {
     "name": "your-project-name",
     "description": "Your project description",
     "author": "Your Name"
   }
   ```

3. Install dependencies:

   **Windows (PowerShell) / macOS / Linux:**

   ```bash
   npm install
   ```

### If You Already Have package.json

If your project already has a `package.json`:

1. **Merge the scripts section** — Add these scripts:

   ```json
   {
     "scripts": {
       "lint:md": "markdownlint-cli2 \"**/*.md\" \"#node_modules\"",
       "lint:md:nested": "node .github/scripts/lint-nested-markdown.js"
     }
   }
   ```

2. **Merge devDependencies** — Add these packages (check template for current versions):

   ```json
   {
     "devDependencies": {
       "markdownlint": "^0.40.0",
       "markdownlint-cli2": "^0.20.0"
     }
   }
   ```

   > **Note:** If adopting the nested markdown linting script, also add `glob`, `jsonc-parser`, and `markdown-it`.

3. Run `npm install` to install the new dependencies

### Copying the Configuration

1. Copy `.markdownlint.jsonc` to your repository root

2. Review the rules and adjust for your project's preferences. Key configurable rules:

   | Rule | Default | Purpose |
   | --- | --- | --- |
   | `MD003` | ATX style (`#`) | Heading style |
   | `MD004` | Dashes | Unordered list marker |
   | `MD029` | Ordered (1. 2. 3.) | Ordered list prefix |
   | `MD035` | `---` | Horizontal rule style |

3. **Optional:** Copy `.github/scripts/lint-nested-markdown.js` if you have markdown embedded in code blocks (common in documentation-heavy projects)

   > **Tip:** See [Nested Markdown Linting Configuration](OPTIONAL_CONFIGURATIONS.md#nested-markdown-linting-configuration) for details on using this script.

### Testing Markdown Linting

Run the linter to verify configuration:

**Windows (PowerShell) / macOS / Linux:**

```bash
npm run lint:md
```

If many errors appear, you have three options:

1. **Fix the files** — Run with `--fix` to auto-correct:

   ```bash
   npx markdownlint-cli2 "**/*.md" "#node_modules" --fix
   ```

2. **Adjust rules** — Modify `.markdownlint.jsonc` to match your project's existing style

3. **Disable specific rules** — Set rules to `false` in the configuration

---

## Adopting Pre-commit Hooks

Pre-commit hooks run automated checks before each commit, catching issues early in the development process.

**Prerequisites:**

- Python installed (3.9+)
- pre-commit installed globally

**Install pre-commit:**

**Windows (PowerShell):**

```powershell
pip install pre-commit
```

**macOS/Linux:**

```bash
pip3 install pre-commit
```

### If You Don't Have Pre-commit Configured

If your project doesn't have a `.pre-commit-config.yaml`:

1. Copy `.pre-commit-config.yaml` to your repository root

2. Review the hooks and remove those for languages you don't use:

   ```yaml
   # Remove this section if not using Python
   - repo: https://github.com/psf/black
     rev: 25.12.0
     hooks:
       - id: black
         args: [--line-length=100]

   # Remove this section if not using Python
   - repo: https://github.com/astral-sh/ruff-pre-commit
     rev: v0.14.11
     hooks:
       - id: ruff
         args: [--fix, --line-length=100]
   ```

3. Install the hooks:

   ```bash
   pre-commit install
   ```

4. Run all hooks to verify:

   ```bash
   pre-commit run --all-files
   ```

### If You Already Have Pre-commit Configured

If your project already uses pre-commit:

1. Compare your `.pre-commit-config.yaml` with the template

2. Consider adding hooks you may be missing:

   **General hooks (recommended for all projects):**
   - `trailing-whitespace`
   - `end-of-file-fixer`
   - `check-yaml`
   - `check-added-large-files`

   **Python hooks:**
   - `black` (formatting)
   - `ruff` (linting)

   **Markdown hooks:**
   - `markdownlint-cli2`

3. Update hook versions if the template has newer ones

4. Run all hooks to verify:

   ```bash
   pre-commit run --all-files
   ```

### Customizing Hooks

**Adjust line length for Black/Ruff:**

```yaml
- repo: https://github.com/psf/black
  rev: 25.12.0
  hooks:
    - id: black
      args: [--line-length=88]  # Change from 100 to 88 (Black's default)
```

**Add hooks for other languages:**

```yaml
# Example: Prettier for JavaScript/TypeScript
- repo: https://github.com/pre-commit/mirrors-prettier
  rev: v3.1.0
  hooks:
    - id: prettier
      types_or: [javascript, typescript, json, yaml]
```

**Handling hook environment issues:**

| Issue | Platform | Solution |
| --- | --- | --- |
| Python not found | Windows | Add Python to PATH |
| pip not found | macOS/Linux | Use `pip3` instead of `pip` |
| Hooks fail to initialize | All | Run `pre-commit clean && pre-commit install` |

---

## Adopting CI Workflows

The template includes several GitHub Actions workflows. Adopt only the ones relevant to your project.

### Understanding Workflow Dependencies

Before adopting workflows, understand their requirements:

| Workflow | Dependencies | Prerequisites |
| --- | --- | --- |
| `markdownlint.yml` | `package.json` with markdownlint-cli2 | Node.js |
| `auto-fix-precommit.yml` | `.pre-commit-config.yaml` | Python |
| `check-placeholders.yml` | None | Template placeholders in files |
| `ci.yml` | Python project structure, `pyproject.toml` | Python |
| `powershell-ci.yml` | PowerShell scripts, Pester tests | PowerShell |

### Markdown Lint Workflow

**Location:** `.github/workflows/markdownlint.yml`

**Purpose:** Enforces consistent Markdown formatting in CI.

**Prerequisites:**

- `markdownlint-cli2` in `package.json`
- `.markdownlint.jsonc` configuration file

**Steps:**

1. Copy `.github/workflows/markdownlint.yml` to your `.github/workflows/` directory
2. The workflow runs automatically on push and pull requests

### Auto-fix Pre-commit Workflow

**Location:** `.github/workflows/auto-fix-precommit.yml`

**Purpose:** Automatically fixes pre-commit issues on `copilot/**` branches. This is useful for AI-assisted development where the Copilot Coding Agent may push code that doesn't pass pre-commit checks.

**Prerequisites:**

- `.pre-commit-config.yaml` configured

**Steps:**

1. Copy `.github/workflows/auto-fix-precommit.yml` to your `.github/workflows/` directory
2. The workflow triggers only on `copilot/**` branches when pushed by `copilot-swe-agent[bot]`

> **Note:** This workflow is optional but recommended if you use GitHub Copilot Coding Agent. If you don't use the Copilot Coding Agent, you can skip adopting this workflow. If you've already adopted it but later decide to remove it, see [Auto-fix Pre-commit Workflow Configuration](OPTIONAL_CONFIGURATIONS.md#auto-fix-pre-commit-workflow-configuration) for removal instructions.

### Placeholder Check Workflow

**Location:** `.github/workflows/check-placeholders.yml`

**Purpose:** Verifies that `OWNER/REPO` placeholders have been replaced after copying from the template.

**No configuration required.** The workflow:

- Runs automatically on push, pull request, and manual dispatch
- Is already configured to exclude only the original template repository (`franklesniak/copilot-repo-template`)
- Will check your repository for unreplaced placeholders

**Adoption considerations:**

1. **If you copied templates with placeholders:** The workflow will catch any unreplaced placeholders and fail CI until you fix them

2. **After all placeholders are replaced:** You have two options:
   - **Keep the workflow** — It serves as a safety net for any future template updates or additions
   - **Remove the workflow** — Delete `.github/workflows/check-placeholders.yml` if you no longer need placeholder checking

**What the workflow checks:**

- `OWNER/REPO` in `.github/ISSUE_TEMPLATE/config.yml` (contact links URLs)
- `OWNER/REPO` in `CONTRIBUTING.md` (clone URL and issues link)
- `@OWNER` in `.github/CODEOWNERS`
- `[security contact email]` and `TODO: Replace` in `SECURITY.md`
- `https://github.com/OWNER/REPO` URLs in any file under `.github/`

### Python CI Workflow

**Location:** `.github/workflows/ci.yml`

**Purpose:** Runs pre-commit hooks, type checking (mypy), and tests (pytest) for Python code.

**Prerequisites:**

- Python code in `src/` directory (or update `MYPY_PATHS`)
- Tests in `tests/` directory
- `pyproject.toml` with `[project.optional-dependencies] dev` section containing test dependencies

**Steps:**

1. Copy `.github/workflows/ci.yml` to your `.github/workflows/` directory

2. **Update paths if needed:**

   If your Python code is in a different location, update the `MYPY_PATHS` environment variable:

   ```yaml
   env:
     MYPY_PATHS: "your_package/ tests/"  # Change from "src/ tests/"
   ```

3. **Update pytest path if needed:**

   ```yaml
   run: pytest your_tests_directory/ -v --cov --cov-report=term-missing
   ```

**If you have existing Python CI:**

- Compare your workflow with the template
- Consider adding specific checks from the template as additional jobs
- The template's job dependency pattern (`needs: pre-commit`) ensures tests don't run on poorly-formatted code

### PowerShell CI Workflow

**Location:** `.github/workflows/powershell-ci.yml`

**Purpose:** Runs PSScriptAnalyzer linting and Pester tests for PowerShell scripts.

**Prerequisites:**

- PowerShell scripts (`.ps1` files)
- Pester tests (`.Tests.ps1` files) for the test job

**Steps:**

1. Copy `.github/workflows/powershell-ci.yml` to your `.github/workflows/` directory

2. Copy `.github/linting/PSScriptAnalyzerSettings.psd1` for consistent linting

3. **Update paths if needed:**

   If your PowerShell files are in different locations, update the find commands in the workflow.

   If your Pester tests aren't in `tests/`, update the configuration:

   ```powershell
   $config.Run.Path = "your_tests_directory/"
   ```

### Merging with Existing CI

If you already have CI workflows:

1. **Don't blindly overwrite** — Review what your current CI does

2. **Add template checks as additional jobs:**

   ```yaml
   jobs:
     existing-job:
       # Your existing job
       runs-on: ubuntu-latest
       steps: [...]

     # Add this from the template
     pre-commit:
       runs-on: ubuntu-latest
       steps: [...]
   ```

3. **Consider matrix builds** — The template uses matrix builds for cross-platform testing. If not already doing this, consider adopting the pattern:

   ```yaml
   strategy:
     matrix:
       os: [ubuntu-latest, windows-latest, macos-latest]
   ```

---

## Adopting PSScriptAnalyzer Configuration

PSScriptAnalyzer is a static code checker for PowerShell. The template includes a configuration file that enforces OTBS (One True Brace Style) formatting.

### Copying the Configuration

1. Create the directory if it doesn't exist:

   **Windows (PowerShell):**

   ```powershell
   New-Item -ItemType Directory -Path .github\linting -Force
   ```

   **macOS/Linux:**

   ```bash
   mkdir -p .github/linting
   ```

2. Copy `PSScriptAnalyzerSettings.psd1` to `.github/linting/`

### Using the Configuration

**Check PowerShell files:**

```powershell
Invoke-ScriptAnalyzer -Path .\your-script.ps1 -Settings .\.github\linting\PSScriptAnalyzerSettings.psd1
```

**Auto-fix formatting issues:**

```powershell
Invoke-ScriptAnalyzer -Path .\your-script.ps1 -Settings .\.github\linting\PSScriptAnalyzerSettings.psd1 -Fix
```

**Check all PowerShell files in a directory:**

```powershell
Get-ChildItem -Path . -Filter "*.ps1" -Recurse | ForEach-Object {
    Invoke-ScriptAnalyzer -Path $_.FullName -Settings .\.github\linting\PSScriptAnalyzerSettings.psd1
}
```

### Customizing Rules

Review the rules in `PSScriptAnalyzerSettings.psd1` and adjust as needed:

**Key configurable rules:**

| Rule | Default | Purpose |
| --- | --- | --- |
| `PSPlaceOpenBrace` | Same line | OTBS brace placement |
| `PSUseConsistentIndentation` | 4 spaces | Indentation style |
| `PSAvoidUsingPositionalParameters` | Enabled | Enforce named parameters |
| `PSProvideCommentHelp` | Enabled | Require help comments |

**To disable a rule:**

```powershell
PSAvoidUsingPositionalParameters = @{
    Enable = $false
}
```

---

## Validation and Testing

Before considering adoption complete, verify that all configurations work correctly.

### Verify All Configurations Work

**1. Pre-commit (if adopted):**

```bash
pre-commit run --all-files
```

Expected result: All hooks should pass, or you should understand and have addressed any failures.

**2. Markdown linting (if adopted):**

```bash
npm run lint:md
```

Expected result: No errors, or only warnings you've chosen to accept.

**3. Push to feature branch:**

```bash
git add .
git commit -m "feat: adopt template configurations from copilot-repo-template"
git push origin feature/adopt-template-features
```

**4. Verify CI workflows:**

- Navigate to your repository's **Actions** tab
- Check that all adopted workflows run
- Fix any failures before merging

**5. Test issue templates (if adopted):**

- Navigate to **Issues** → **New Issue**
- Verify all templates appear correctly
- Open a test issue with each template to verify form fields work
- Verify links in the template chooser (`config.yml`) work
- Close test issues without saving (or delete after testing)

**6. Test PR template (if adopted):**

- Open a test pull request (can be against your feature branch)
- Verify the template renders correctly with all sections
- Close without merging

### Troubleshooting Common Issues

| Issue | Cause | Solution |
| --- | --- | --- |
| Workflow fails with "file not found" | Different project structure | Update paths in workflow file |
| Pre-commit downloads every time | Environment cache issue | Run `pre-commit clean && pre-commit install` |
| Markdown lint finds many errors | Stricter rules than before | Adjust `.markdownlint.jsonc` or fix files |
| Python CI fails on imports | Different package structure | Update `MYPY_PATHS` in workflow |
| PSScriptAnalyzer fails | Code doesn't match OTBS style | Run with `-Fix` or adjust settings |
| npm install fails | Node.js version mismatch | Update Node.js to v20+ (see `engines` in package.json) |
| Placeholder check fails | OWNER/REPO not replaced | Search and replace all placeholders |

---

## Cleanup and Documentation

### Files to Review After Adoption

**Files you may want to delete after adoption:**

- If you cloned the template separately, delete the clone directory
- `.github/TEMPLATE_GUIDE.md` — Template adoption guidance (only useful during adoption)
- `templates/` directory — Only useful if your project is also a template

**Files you should keep:**

- All configuration files you adopted (`.markdownlint.jsonc`, `.pre-commit-config.yaml`, etc.)
- All workflow files in `.github/workflows/`
- Copilot instructions (`.github/copilot-instructions.md` and `.github/instructions/`)

### Updating Your Project Documentation

**Update CONTRIBUTING.md:**

If you adopted the template's `CONTRIBUTING.md`, you should:

1. **Remove the "For Template Users" section** — This section (starting with `## For Template Users`) contains meta-instructions about the template itself. Delete it along with the HTML comment above it for non-template projects.

2. **Replace `OWNER/REPO` placeholders** — Update with your actual organization and repository name in clone instructions and issue links.

3. **Add pre-commit setup instructions** (if you adopted pre-commit):

````markdown
## Development Setup

Before making changes, install pre-commit hooks:

```bash
pip install pre-commit
pre-commit install
```

Pre-commit hooks will automatically run on each commit. You can also run them manually:

```bash
pre-commit run --all-files
```
````

See `.github/TEMPLATE_GUIDE.md` for additional `CONTRIBUTING.md` customization guidance.

**Update README.md:**

Add any new development setup steps:

````markdown
## Development

### Prerequisites

- Node.js 20+ (for markdown linting)
- Python 3.9+ (for pre-commit hooks)
- PowerShell (for PSScriptAnalyzer)

### Setup

```bash
npm install          # Install markdown linting tools
pip install pre-commit
pre-commit install   # Set up git hooks
```
````

**Notify your team:**

Consider informing collaborators about:

- New pre-commit requirements
- CI workflow changes
- New issue/PR templates

---

## Next Steps

After adopting template features, you may want to explore additional customization options:

- **[Optional Configurations](OPTIONAL_CONFIGURATIONS.md)**: Fine-tune your repository with optional settings like enabling GitHub Discussions, adjusting Dependabot frequency, customizing linting rules, and more.

---

## Summary Checklist

Before considering adoption complete, verify:

### Files

- [ ] All copied files have placeholders replaced (OWNER/REPO, @OWNER, `window.title` in `.vscode/settings.json`, etc.)
- [ ] Conflicting configurations have been merged, not overwritten
- [ ] Unused language files have been removed (e.g., PowerShell instructions if not using PowerShell)
- [ ] `.github/TEMPLATE_GUIDE.md` deleted (if not needed)

### Functionality

- [ ] Pre-commit runs successfully (`pre-commit run --all-files`)
- [ ] Markdown linting passes (`npm run lint:md`)
- [ ] All CI workflows pass in GitHub Actions
- [ ] Issue templates display correctly in GitHub
- [ ] PR template renders correctly when opening a PR
- [ ] PSScriptAnalyzer runs without unexpected errors (if using PowerShell)

### Documentation

- [ ] CONTRIBUTING.md updated with new development requirements
- [ ] README.md updated if setup steps changed
- [ ] Team notified of new tooling/workflows

---

**Commit all your changes:**

```bash
git add .
git commit -m "feat: adopt template configurations from copilot-repo-template"
git push origin feature/adopt-template-features
```

**Create a pull request:**

1. Navigate to your repository on GitHub
2. Click **Compare & pull request**
3. Review the changes
4. Merge after CI passes

Congratulations! You've successfully adopted features from the copilot-repo-template into your existing repository.
