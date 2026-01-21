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
- [Next Steps: Part 2](#next-steps-part-2)

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

**In `bug_report.yml`, `feature_request.yml`, and `documentation_issue.yml`:**

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

> **Tip:** Update the Area dropdown in all three template files to keep them consistent.

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

1. Go to your repository → **Issues** → **Labels**
2. Click **New label**
3. Name: `triage`
4. Description: `Needs triage`
5. Color: `d4c5f9` (light purple)

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

## Next Steps: Part 2

Congratulations! You've completed Part 1 of adopting template features. You should now have:

- [x] Reviewed prerequisites and planned your adoption
- [x] Obtained the template files
- [x] Adopted simple standalone files (CODEOWNERS, Dependabot, Security Policy)
- [x] Adopted issue templates
- [x] Adopted the PR template

**Part 2 covers more advanced features:**

- Adopting Copilot Instructions
- Setting up Markdown Linting
- Configuring Pre-commit Hooks
- Adopting CI Workflows (Python and PowerShell)
- Final validation and cleanup

<!-- Part 2 of this guide will be published separately. -->
<!-- When Part 2 is available, the link will be added here. -->

---

**Commit your changes so far:**

```bash
git add .
git commit -m "feat: adopt template features (issue templates, PR template, standalone files)"
git push origin feature/adopt-template-features
```

You can create a pull request now for these changes, or continue to Part 2 and submit everything together.
