# Optional Configurations

This guide covers optional customizations you can make after completing the initial setup from either of the two getting started guides:

- **[Creating a New Repository](GETTING_STARTED_NEW_REPO.md)**: For users creating new repositories from this template
- **[Adding Template Features to an Existing Repository](GETTING_STARTED_EXISTING_REPO.md)**: For users adopting template features into existing repositories

> **Note:** None of these configurations are required. Your repository will work correctly with the default settings. These options allow you to fine-tune your setup based on your project's specific needs.

---

## Table of Contents

- [Issue Template Configuration](#issue-template-configuration)
- [Security Configuration](#security-configuration)
- [Pull Request Template Customization](#pull-request-template-customization)
- [Dependabot Configuration](#dependabot-configuration)
- [Pre-commit Configuration](#pre-commit-configuration)
- [Markdown Linting Configuration](#markdown-linting-configuration)
- [Copilot Documentation Instructions Configuration](#copilot-documentation-instructions-configuration)
- [CI Workflow Configuration](#ci-workflow-configuration)
- [PSScriptAnalyzer Configuration](#psscriptanalyzer-configuration)
- [CODEOWNERS Configuration](#codeowners-configuration)
- [Node.js Package Configuration](#nodejs-package-configuration)

---

## Issue Template Configuration

**File:** `.github/ISSUE_TEMPLATE/config.yml`

### Requiring Issue Templates

By default, `blank_issues_enabled` is set to `true`, which allows users to create issues without selecting a template. This provides flexibility for edge cases that don't fit your predefined templates.

**To require template usage:**

```yaml
blank_issues_enabled: false
```

> **Recommendation:** Set this to `false` once you have comprehensive templates covering all issue types and want structured data collection for better triage.

### Enabling GitHub Discussions Link

If your repository uses GitHub Discussions for Q&A and general discussions, you can add a link that redirects users away from the issue tracker.

**Steps:**

1. Enable GitHub Discussions in your repository:
   - Go to **Settings** > **General** > **Features**
   - Check the **Discussions** checkbox
2. Uncomment the Discussions contact link in `config.yml`:

   ```yaml
   - name: 💬 Questions & Discussions
     url: https://github.com/OWNER/REPO/discussions
     about: Ask questions and discuss ideas (not for bug reports)
   ```

3. Replace `OWNER/REPO` with your actual organization and repository name

### Adding a Support/FAQ Link

If you prefer not to enable Discussions but want to redirect support questions away from issues:

**Steps:**

1. Add a `## Support` section to your `README.md` with FAQs and support guidance
2. Uncomment the Support/FAQ contact link in `config.yml`:

   ```yaml
   - name: ❓ Support / FAQ
     url: https://github.com/OWNER/REPO#support
     about: Common questions, FAQs, and support guidance
   ```

3. Replace `OWNER/REPO` with your actual values
4. Update the URL anchor (`#support`) if your section has a different heading

---

## Security Configuration

**Files:** `SECURITY.md` and repository settings

### Enabling Private Vulnerability Reporting

> **Important:** Private vulnerability reporting is **only available for public repositories**.

Private vulnerability reporting allows security researchers to report vulnerabilities directly to maintainers without public disclosure.

**Steps:**

1. Go to **Settings** > **Security** > **Private vulnerability reporting**
2. Click **Enable**

**Optional:** After enabling, you can update the security link in `.github/ISSUE_TEMPLATE/config.yml` for a more direct path:

```yaml
# Change from:
url: https://github.com/OWNER/REPO/security

# To:
url: https://github.com/OWNER/REPO/security/advisories/new
```

### Customizing Supported Versions

The default `SECURITY.md` includes a minimal supported versions table:

```markdown
| Version | Supported          |
| ------- | ------------------ |
| latest  | :white_check_mark: |
```

**To customize for your versioning policy:**

```markdown
| Version | Supported          |
| ------- | ------------------ |
| 2.x     | :white_check_mark: |
| 1.x     | :white_check_mark: |
| < 1.0   | :x:                |
```

Update this table to reflect which versions of your project receive security updates.

---

## Pull Request Template Customization

**File:** `.github/pull_request_template.md`

### Strengthening Pre-commit Language

The default template uses conditional language for pre-commit verification:

```markdown
### Pre-commit Verification (if configured)

- [ ] If this repository uses pre-commit, I ran `pre-commit run --all-files` and all checks pass
- [ ] If pre-commit made auto-fixes, I reviewed and committed them
```

**If your repository uses pre-commit hooks**, replace with direct language:

```markdown
### Pre-commit Verification

- [ ] I have run `pre-commit run --all-files` locally and all checks pass
- [ ] I have reviewed and committed all auto-fixes made by pre-commit hooks
```

### Adding Language-Specific Sections

Add checklist sections for your project's technology stack:

**Node.js/TypeScript:**

```markdown
### Node.js-Specific (if applicable)

- [ ] `npm test` passes locally
- [ ] ESLint passes with no errors
- [ ] TypeScript compiles without errors
```

**.NET:**

```markdown
### .NET-Specific (if applicable)

- [ ] `dotnet test` passes locally
- [ ] No compiler warnings
- [ ] Code analysis passes
```

**Go:**

```markdown
### Go-Specific (if applicable)

- [ ] `go test ./...` passes locally
- [ ] `go vet ./...` passes
- [ ] `golint ./...` passes (if using golint)
```

**Rust:**

```markdown
### Rust-Specific (if applicable)

- [ ] `cargo test` passes locally
- [ ] `clippy` passes with no warnings
- [ ] `cargo fmt --check` shows no formatting issues
```

**Java:**

```markdown
### Java-Specific (if applicable)

- [ ] Maven/Gradle tests pass locally
- [ ] Checkstyle passes
- [ ] No compiler warnings
```

### Customizing Type of Change Options

Add options relevant to your workflow:

```markdown
- [ ] Refactoring (no functional changes)
- [ ] Security fix
- [ ] Performance improvement
```

Remove options that don't apply to your project.

### Strengthening Test Requirements

For mature projects with established test infrastructure, change:

```markdown
- [ ] I have added or updated tests where appropriate
```

To:

```markdown
- [ ] I have added tests for all new functionality
- [ ] I have updated tests for all modified functionality
```

---

## Dependabot Configuration

**File:** `.github/dependabot.yml`

### Adjusting Update Frequency

The default configuration checks for updates weekly:

```yaml
schedule:
  interval: "weekly"
```

**Options:**

- `"daily"`: More frequent updates, useful for security-critical projects
- `"weekly"`: Balanced approach (default)
- `"monthly"`: Less frequent updates, reduces PR volume

### Adjusting PR Limits

The `open-pull-requests-limit` controls how many Dependabot PRs can be open simultaneously:

```yaml
open-pull-requests-limit: 10
```

- **Increase** if you have a large dependency tree and want faster updates
- **Decrease** if Dependabot PRs are overwhelming your team

### Adding Automatic Reviewers

Automatically assign reviewers and assignees to Dependabot PRs:

```yaml
- package-ecosystem: "npm"
  directory: "/"
  schedule:
    interval: "weekly"
  reviewers:
    - "username1"
    - "org/team-name"
  assignees:
    - "username2"
```

### Customizing Commit Message Prefixes

The default prefix is `chore(deps)`:

```yaml
commit-message:
  prefix: "chore(deps)"
```

**To match your project's commit conventions:**

```yaml
commit-message:
  prefix: "deps"           # Simpler prefix
  prefix: "build(deps)"    # For projects using build scope
  prefix: "fix(deps)"      # If you treat dependency updates as fixes
```

---

## Pre-commit Configuration

**File:** `.pre-commit-config.yaml`

### Adjusting Line Length

The default line length is 100 characters for both Black and Ruff:

```yaml
- repo: https://github.com/psf/black
  rev: 25.12.0
  hooks:
    - id: black
      args: [--line-length=100]

- repo: https://github.com/astral-sh/ruff-pre-commit
  rev: v0.14.11
  hooks:
    - id: ruff
      args: [--fix, --line-length=100]
```

**To use Black's default (88 characters):**

```yaml
args: [--line-length=88]
```

> **Note:** Ensure both Black and Ruff use the same line length to avoid conflicts.

### Adding Hooks for Other Languages

**Prettier (JavaScript/TypeScript/CSS/JSON):**

```yaml
- repo: https://github.com/pre-commit/mirrors-prettier
  rev: v3.1.0
  hooks:
    - id: prettier
      types_or: [javascript, jsx, ts, tsx, css, json, yaml, markdown]
```

**ESLint:**

```yaml
- repo: https://github.com/pre-commit/mirrors-eslint
  rev: v8.56.0
  hooks:
    - id: eslint
      files: \.[jt]sx?$
      additional_dependencies:
        - eslint@8.56.0
        - eslint-config-your-config
```

**ShellCheck (Bash/Shell scripts):**

```yaml
- repo: https://github.com/shellcheck-py/shellcheck-py
  rev: v0.9.0.6
  hooks:
    - id: shellcheck
```

### Switching to Husky

If your project prefers Husky for git hooks:

1. Remove `.pre-commit-config.yaml`
2. Install Husky:

   ```bash
   npm install husky --save-dev
   ```

3. Add the prepare script to `package.json`:

   ```json
   {
     "scripts": {
       "prepare": "husky"
     }
   }
   ```

4. Create `.husky/pre-commit`:

   ```bash
   #!/usr/bin/env sh
   . "$(dirname -- "$0")/_/husky.sh"

   npm run lint
   npm test
   ```

> **Warning:** Pre-commit and Husky both manage `.git/hooks/pre-commit`. Do NOT run `pre-commit install` if using Husky, as the two tools conflict.

---

## Markdown Linting Configuration

**File:** `.markdownlint.jsonc`

### Customizing Style Rules

The following rules can be configured to match your project's documentation style:

| Rule | Description | Default | Options |
| --- | --- | --- | --- |
| MD003 | Heading style | `atx` | `atx`, `setext`, `consistent` |
| MD004 | Unordered list marker | `dash` | `dash`, `asterisk`, `plus`, `consistent` |
| MD029 | Ordered list prefix | `ordered` | `ordered`, `one`, `one_or_ordered` |
| MD035 | Horizontal rule style | `---` | `---`, `***`, `___`, `consistent` |
| MD048 | Code fence style | `backtick` | `backtick`, `tilde`, `consistent` |
| MD049 | Emphasis style | `asterisk` | `asterisk`, `underscore`, `consistent` |
| MD050 | Strong style | `asterisk` | `asterisk`, `underscore`, `consistent` |

**Example: Using asterisks for unordered lists:**

```jsonc
{
  "MD004": {
    "style": "asterisk"
  }
}
```

### Re-enabling Disabled Rules

Several rules are disabled by default because they are not auto-fixable:

| Rule | Why Disabled | When to Enable |
| --- | --- | --- |
| MD013 | Line length not auto-fixable | If you want to enforce line length limits |
| MD034 | Bare URLs may be intentional | If you want all URLs to use link syntax |
| MD036 | False positives with bold text | If you want to prevent emphasis as headings |
| MD041 | Prevents badges/metadata at start | If you require first line to be a heading |

**To re-enable a rule:**

```jsonc
{
  "MD013": {
    "line_length": 120
  },
  "MD041": true
}
```

---

## Copilot Documentation Instructions Configuration

**File:** `.github/instructions/docs.instructions.md`

GitHub Copilot instruction files (`.github/instructions/*.md`) provide coding and documentation standards that Copilot applies when generating or editing code in your repository. The `docs.instructions.md` file specifically provides documentation standards that Copilot applies to all Markdown files, defining contract-first, traceable, and drift-resistant documentation practices.

The file contains several customization points that should be updated to match your project's specific needs.

### Customizing Documentation Taxonomy

The default taxonomy suggests a folder structure for documentation:

```markdown
- **Product spec:** `docs/spec/` (requirements + design; the source of truth)
- **Developer docs:** `docs/` (how to build, test, extend)
- **Operational docs / runbooks:** `docs/runbooks/` (diagnosis, remediation, safe operations)
- **Architecture Decision Records (ADRs):** `docs/adr/` (durable decisions)
```

**To customize for your project's structure:**

Update the taxonomy section to reflect your actual documentation organization. For example, if your project uses a different structure:

```markdown
- **API documentation:** `docs/api/` (API reference and usage guides)
- **User guides:** `docs/guides/` (end-user documentation)
- **Developer docs:** `docs/dev/` (how to build, test, extend)
- **Release notes:** `docs/releases/` (version history and changelogs)
```

> **Note:** If your project does not have a formal documentation structure, you can simplify this section to match your needs or remove categories that don't apply.

### Customizing Canonical Source of Truth

The file recommends defining a canonical specification document that serves as the authoritative reference for system behavior:

```markdown
Projects SHOULD define a canonical specification document (e.g., `docs/spec/requirements.md`)
that serves as the authoritative reference for system behavior and requirements.
```

**To customize for your project:**

- If you have a canonical spec, update the example path to match your actual location:

  ```markdown
  Projects SHOULD define a canonical specification document (e.g., `docs/SPEC.md`)
  that serves as the authoritative reference for system behavior and requirements.
  ```

- If your project does not use a formal specification document, you can note this explicitly or remove the section entirely.

### Customizing Requirements Documentation Standards

The file provides a pattern for tracking formal requirements with identifiers:

```markdown
- Each requirement SHOULD have a stable identifier (example pattern):
  - `PROJ-REQ-001`, `PROJ-REQ-002`, ...
```

**To customize for your project:**

1. **Update the requirement ID pattern** to match your project's naming convention:

   ```markdown
   - Each requirement SHOULD have a stable identifier (example pattern):
     - `MYPROJ-REQ-001`, `MYPROJ-REQ-002`, ...
   ```

2. **Adjust the requirement entry format** if your project uses different metadata fields. The default includes Rationale, Acceptance Criteria, Priority, and Verification. You might customize this to:

   ```markdown
   - Each requirement entry SHOULD include:
     - **Rationale:** why it exists
     - **Acceptance Criteria:** objective checks (bullets)
     - **Owner:** responsible team or individual
     - **Target Release:** version when this should be implemented
   ```

3. **If your project does not track formal requirements**, you can simplify or remove this section entirely. Consider replacing it with guidance appropriate for your documentation needs.

---

## CI Workflow Configuration

**File:** `.github/workflows/ci.yml`

### Enabling Codecov Integration

Uncomment the Codecov step to enable code coverage reporting:

```yaml
- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v4
  with:
    token: ${{ secrets.CODECOV_TOKEN }}  # Required for private repos only
    files: ./coverage.xml
    flags: unittests
    name: codecov-umbrella
    fail_ci_if_error: false
```

> **Note:** Public repositories do not require a token. For private repositories, add `CODECOV_TOKEN` to your repository secrets.

### Making Type Checking Strict

The mypy step includes `continue-on-error: true` by default:

```yaml
- name: Run mypy
  run: mypy $MYPY_PATHS
  continue-on-error: true
```

**Once your project has full type coverage**, remove `continue-on-error: true` to make type checking a required check.

### Customizing Python Version Matrix

The test matrix runs on Python 3.13 by default:

```yaml
strategy:
  matrix:
    python-version: ['3.13']
```

**To test multiple versions:**

```yaml
strategy:
  matrix:
    python-version: ['3.11', '3.12', '3.13']
```

> **Note:** Only test Python versions currently receiving bugfix updates. Security-fix-only versions require building from source and are not recommended for CI.

### Customizing Test Paths

The `MYPY_PATHS` environment variable controls which directories mypy checks:

```yaml
env:
  MYPY_PATHS: "src/ tests/"
```

**Common configurations:**

- Flat layout: `MYPY_PATHS: "."`
- src layout: `MYPY_PATHS: "src/ tests/"`
- Custom: `MYPY_PATHS: "mymodule/ tests/ scripts/"`

---

## PSScriptAnalyzer Configuration

**File:** `.github/linting/PSScriptAnalyzerSettings.psd1`

### Adjusting Severity Levels

The default configuration enforces Error and Warning severity:

```powershell
Severity = @('Error', 'Warning')
```

**To include informational messages:**

```powershell
Severity = @('Error', 'Warning', 'Information')
```

**To only enforce errors:**

```powershell
Severity = @('Error')
```

### Customizing Individual Rules

Each rule can be individually enabled or disabled:

```powershell
Rules = @{
    PSAvoidUsingCmdletAliases = @{
        Enable = $true  # or $false to disable
    }
}
```

For a complete list of available rules, see the [PSScriptAnalyzer documentation](https://github.com/PowerShell/PSScriptAnalyzer).

### Relaxing Formatting Rules

For teams preferring different brace styles, modify the `PSPlaceOpenBrace` rule:

**Allman style (braces on new line):**

```powershell
PSPlaceOpenBrace = @{
    Enable = $true
    OnSameLine = $false
    NewLineAfter = $true
}
```

**To disable brace checking entirely:**

```powershell
PSPlaceOpenBrace = @{
    Enable = $false
}
PSPlaceCloseBrace = @{
    Enable = $false
}
```

---

## CODEOWNERS Configuration

**File:** `.github/CODEOWNERS`

### Adding Team-Based Ownership

Use team references for organization repositories:

```text
* @org/maintainers
.github/workflows/ @org/devops-team
docs/ @org/documentation-team
```

### Adding Path-Specific Ownership

Assign different owners for different directories:

```text
# Default owners
* @username

# Documentation
docs/ @docs-team
*.md @docs-team

# Tests
tests/ @qa-team

# Specific modules
src/api/ @api-team
src/frontend/ @frontend-team
```

### Multiple Owners

List multiple owners for the same pattern:

```text
# Both users will be requested for review
src/critical/ @senior-dev @tech-lead

# Team and individual
.github/ @org/maintainers @repo-admin
```

---

## Node.js Package Configuration

**File:** `package.json`

### Adding Application Metadata

For projects using Node.js as a runtime (not just dev tooling), add these fields:

```json
{
  "name": "your-package-name",
  "version": "1.0.0",
  "description": "Your project description",
  "main": "dist/index.js",
  "exports": {
    ".": "./dist/index.js"
  },
  "repository": {
    "type": "git",
    "url": "git+https://github.com/OWNER/REPO.git"
  },
  "homepage": "https://github.com/OWNER/REPO#readme",
  "bugs": {
    "url": "https://github.com/OWNER/REPO/issues"
  }
}
```

### Specifying Node.js Version Requirements

The template includes an `engines` field:

```json
{
  "engines": {
    "node": ">=20.0.0"
  }
}
```

Update this to match your project's Node.js version requirements.

---

## Additional Resources

- **[Creating a New Repository](GETTING_STARTED_NEW_REPO.md)**: Complete setup guide for new repositories
- **[Adding Template Features to an Existing Repository](GETTING_STARTED_EXISTING_REPO.md)**: Adoption guide for existing repositories
- **[Template Guide](.github/TEMPLATE_GUIDE.md)**: Detailed customization guidance for GitHub-specific files

> **Note:** The Template Guide (`.github/TEMPLATE_GUIDE.md`) should be deleted after completing template adoption, as it contains meta-content specific to the template setup process.
