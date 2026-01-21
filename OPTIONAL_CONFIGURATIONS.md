# Optional Configurations

This guide covers optional customizations you can make after completing the initial setup from either of the two getting started guides:

- **[Creating a New Repository](GETTING_STARTED_NEW_REPO.md)**: For users creating new repositories from this template
- **[Adding Template Features to an Existing Repository](GETTING_STARTED_EXISTING_REPO.md)**: For users adopting template features into existing repositories

> **Note:** None of these configurations are required. Your repository will work correctly with the default settings. These options allow you to fine-tune your setup based on your project's specific needs.

---

## Table of Contents

- [Issue Template Configuration](#issue-template-configuration)
  - [Bug Report Template Customization](#bug-report-template-customization)
  - [Feature Request Template Customization](#feature-request-template-customization)
  - [Documentation Issue Template Customization](#documentation-issue-template-customization)
- [Security Configuration](#security-configuration)
- [Pull Request Template Customization](#pull-request-template-customization)
- [Dependabot Configuration](#dependabot-configuration)
- [Pre-commit Configuration](#pre-commit-configuration)
- [Markdown Linting Configuration](#markdown-linting-configuration)
- [Nested Markdown Linting Configuration](#nested-markdown-linting-configuration)
- [Markdown Lint Workflow Configuration](#markdown-lint-workflow-configuration)
- [Copilot Documentation Instructions Configuration](#copilot-documentation-instructions-configuration)
- [Copilot Python Instructions Configuration](#copilot-python-instructions-configuration)
- [Copilot PowerShell Instructions Configuration](#copilot-powershell-instructions-configuration)
- [Copilot Main Instructions Configuration](#copilot-main-instructions-configuration)
- [CI Workflow Configuration](#ci-workflow-configuration)
- [Auto-fix Pre-commit Workflow Configuration](#auto-fix-pre-commit-workflow-configuration)
- [Placeholder Check Workflow Configuration](#placeholder-check-workflow-configuration)
- [PowerShell CI Workflow Configuration](#powershell-ci-workflow-configuration)
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

### Security Link URL Customization

The `config.yml` file includes a security contact link that points to `/security` by default:

```yaml
- name: 🔒 Security Vulnerabilities
  url: https://github.com/OWNER/REPO/security
  about: Report security issues privately (do not open a public issue). Private vulnerability reporting is only available for public repositories.
```

After enabling private vulnerability reporting in your repository, you can optionally update this URL to provide a more direct path to the vulnerability reporting form.

> **Important:** Private vulnerability reporting is only available for **public repositories**. If your repository is private, security reporters must use email contact as specified in your `SECURITY.md` file.
>
> **See:** [Security Configuration](#security-configuration) for instructions on enabling private vulnerability reporting and updating this URL.

### Bug Report Template Customization

**File:** `.github/ISSUE_TEMPLATE/bug_report.yml`

The bug report template includes numerous `# CUSTOMIZE:` comments indicating optional configuration points. This section documents each customization option.

#### Top-Level Metadata

##### Title Prefix

Adjust the issue title prefix to match your project's conventions:

```yaml
# Default:
title: "[Bug] "

# Example alternatives:
title: "bug: "
title: "[BUG] "
title: ""  # No prefix
```

##### Labels

Update the labels to match your repository's label taxonomy. Ensure labels exist before using them:

```yaml
labels:
  - bug
  # Add your project-specific labels:
  # - priority:high
  # - area:api
```

> **Note:** Labels must exist in your repository before they can be applied. Create them via **Settings** > **Labels** or use the GitHub CLI.

##### Triage Label

Uncomment the `triage` label after creating it in your repository:

```yaml
labels:
  - bug
  - triage  # Uncomment after creating the label
```

> **Cross-reference:** The [Getting Started Guides](GETTING_STARTED_NEW_REPO.md) provide instructions for creating labels in your repository.

##### Issue Type (Organization-Level)

For organizations using [GitHub issue types](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms#top-level-syntax), uncomment and configure the `type` field:

```yaml
# Uncomment to enable:
type: Bug
```

##### Assignees

Pre-populate the assignees field for bug reports:

```yaml
# Uncomment and update:
assignees:
  - maintainer-username
  - your-github-handle
```

##### Projects

Auto-add bug reports to a GitHub Project (uses project number):

```yaml
# Uncomment and update with your org and project number:
projects:
  - org/1
```

#### Pre-flight Checklist Customization

##### Making Documentation Check Required

For projects with comprehensive documentation that users should consult before filing bugs:

```yaml
# Change from:
- label: I have read the project documentation
  required: false

# To:
- label: I have read the project documentation
  required: true
```

##### Removing PR Contribution Checkbox

For projects that don't accept community contributions, remove this checkbox:

```yaml
# Remove this block entirely:
- label: I am willing to submit a pull request to fix this issue
  required: false
```

#### Environment Fields Customization

##### Area Dropdown

The Area dropdown is optional by default for template portability. Update the options to match your project's components:

```yaml
options:
  - Backend / API
  - Frontend / UI
  - CLI
  - Documentation
  - Other (describe/specify in Additional Context)
```

**Making it required:** For repos that rely on area-based routing, change `required: false` to `required: true`.

##### Minimal Reproduction URL

For library or framework projects, consider making this field required:

```yaml
# Change from:
validations:
  required: false

# To:
validations:
  required: true
```

Projects that don't accept external reproductions can remove this field entirely.

##### Architecture Dropdown

For cross-platform projects, consider making this required:

```yaml
# Change from:
validations:
  required: false

# To:
validations:
  required: true
```

Single-platform projects can remove this field entirely.

##### Runtime Version Placeholders

Update the placeholder examples to match your project's supported runtimes:

```yaml
# Default (Python-focused):
placeholder: |
  Python 3.13.1 (or your installed version)
  PowerShell 7.4.6 or Windows PowerShell 5.1
  Markdown tooling/renderer (if relevant): e.g., Pandoc 3.1.2

# Node.js project example:
placeholder: |
  Node.js 20.10.0
  npm 10.2.3

# .NET project example:
placeholder: |
  .NET 8.0.1
  C# 12
```

##### Shell/Terminal Field

For non-CLI projects where shell environment isn't relevant, remove this field entirely.

##### How Did You Run It? Placeholders

Update the placeholder examples to match your project's dependency management approach:

```yaml
# Default (Python-focused):
placeholder: |
  # Python (using pyproject.toml)
  python -m venv .venv
  source .venv/bin/activate
  pip install -e .
  python -m your_package

# Node.js example:
placeholder: |
  npm install
  npm run build
  npm start

# Docker example:
placeholder: |
  docker build -t myapp .
  docker run myapp
```

#### Bug Characteristics Customization

##### Regression Fields

For projects where version history or regression tracking is not relevant, remove these fields:

- Remove the "Regression?" dropdown (`id: regression`)
- Remove the "Last Working Version" input (`id: last_working_version`)

##### Severity Options

Adjust the severity levels to match your project's triage workflow:

```yaml
# Default:
options:
  - Critical (system crash, data loss)
  - High (major feature broken, no workaround)
  - Medium (feature impaired, workaround exists)
  - Low (minor inconvenience, cosmetic issue)

# Alternative with P-levels:
options:
  - P0 (production down)
  - P1 (critical impact)
  - P2 (moderate impact)
  - P3 (low impact)
```

#### Additional Information Customization

##### Related Issues Placeholder

Update the cross-repo example to reference related projects in your ecosystem:

```yaml
# Default:
placeholder: |
  #123
  owner/repo-name#456

# Example for a monorepo or related projects:
placeholder: |
  #123
  my-org/frontend#456
  my-org/backend#789
```

### Feature Request Template Customization

**File:** `.github/ISSUE_TEMPLATE/feature_request.yml`

The feature request template shares many customization points with the bug report template. This section documents the unique or different options.

#### Top-Level Metadata

The same customizations apply as for the bug report template:

- **Title Prefix:** Default is `"[Feature] "`
- **Labels:** Default is `enhancement`
- **Triage Label:** Uncomment after creating the label
- **Issue Type:** Use `type: Feature` for organization-level issue types
- **Assignees and Projects:** Same configuration as bug reports

#### Shared Customizations with Bug Report

The feature request template shares several customization points with the bug report template. See the [Bug Report Template Customization](#bug-report-template-customization) section for detailed instructions on:

- **Making Documentation Check Required:** Change `required: false` to `required: true` for the "I have read the project documentation" checkbox
- **Area Dropdown Options:** Update the options to match your project's languages/components (e.g., Backend / API, Frontend / UI, CLI, etc.)

> **Tip:** Keep the Area dropdown options consistent between bug report and feature request templates to maintain a unified user experience.

#### Pre-flight Checklist

##### Removing PR Contribution Checkbox

Same as the bug report template—remove if your project doesn't accept community contributions:

```yaml
# Remove this block:
- label: I am willing to submit a pull request to implement this feature
  required: false
```

#### Feature Classification

##### Priority Options

Adjust priority levels to match your project's triage workflow:

```yaml
# Default:
options:
  - Critical (blocking my adoption/usage)
  - High (significant impact on my workflow)
  - Medium (would improve my experience)
  - Low (nice to have)
```

##### Scope Options

Adjust feature scope categories as needed:

```yaml
# Default:
options:
  - Major feature (new capability, significant change)
  - Minor enhancement (improvement to existing feature)
  - Quality of life (small improvement, polish)
```

### Documentation Issue Template Customization

**File:** `.github/ISSUE_TEMPLATE/documentation_issue.yml`

The documentation issue template is simpler than the other templates but still has customization points.

#### Top-Level Metadata

- **Title Prefix:** Default is `"[Docs] "`
- **Labels:** Default is `documentation` (a GitHub default label)
- **Triage Label:** Uncomment after creating the label

> **Note:** The `documentation` label is a GitHub default label that exists in all new repositories. If your organization has renamed or deleted it, update accordingly.

#### Location Placeholder URL

The "Where is it?" field includes a generic placeholder that uses relative file paths:

```yaml
placeholder: e.g., README.md#usage or docs/guide.md
```

For a more helpful user experience, you can update this placeholder to include a full URL example specific to your repository:

```yaml
placeholder: e.g., https://github.com/your-org/your-repo/blob/HEAD/README.md#usage or docs/guide.md
```

Replace `your-org/your-repo` with your actual organization and repository name.

> **Note:** The default uses simple file paths rather than full URLs to avoid reporters pasting literal placeholders. Updating this is optional and depends on your preference for guiding reporters.

#### Documentation Version Field

For projects that don't maintain versioned documentation, remove this field:

```yaml
# Remove this entire block:
- type: input
  id: doc_version
  attributes:
    label: Documentation Version (optional)
    description: >-
      If the documentation is versioned, which version are you viewing?
    placeholder: e.g., v1.2.3, latest, main branch
  validations:
    required: false
```

#### Issue Type Dropdown

Adjust the documentation issue type options to match your documentation structure:

```yaml
# Default:
options:
  - Typo / Grammar
  - Unclear / Confusing
  - Missing Information
  - Broken Link
  - Outdated Information
  - Code Example Issue
  - Formatting / Rendering
  - Other

# Simplified example:
options:
  - Typo / Grammar
  - Missing or Outdated Content
  - Broken Link
  - Other
```

To make this field required for structured documentation triage, change `required: false` to `required: true`.

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

## Nested Markdown Linting Configuration

**File:** `.github/scripts/lint-nested-markdown.js`

This optional script lints Markdown content embedded within code fences (` ```markdown ` or ` ```md `) in Markdown files. This is useful for documentation-heavy projects that include Markdown examples, ensuring that nested Markdown content follows the same linting rules as the outer Markdown files.

### How to Run

**Scan all Markdown files in the repository:**

```bash
npm run lint:md:nested
```

**Lint specific files:**

```bash
node .github/scripts/lint-nested-markdown.js file1.md file2.md
```

When file arguments are provided, only those files are linted (useful for pre-commit hooks). When no arguments are provided, all `.md` files are scanned via glob (excluding `node_modules`).

### Automatic Rule Adjustments

The script automatically disables two rules for nested Markdown content:

| Rule | Description | Why Disabled |
| --- | --- | --- |
| MD041 | First line in a file should be a top-level heading | Nested Markdown snippets may not start with a top-level heading |
| MD051 | Link fragments should be valid | Nested Markdown often contains example/placeholder links that reference anchors in other documents |

### Pre-commit Integration (Optional)

If you want to run this script as a pre-commit hook, you can add the following to your `.pre-commit-config.yaml`:

```yaml
- repo: local
  hooks:
    - id: lint-nested-markdown
      name: Lint nested Markdown
      entry: node .github/scripts/lint-nested-markdown.js
      language: node
      files: \.md$
      pass_filenames: true
```

### When to Use This Feature

This feature is most useful for:

- **Documentation-heavy projects** with Markdown examples in code blocks
- **Template repositories** that include example Markdown snippets
- **Projects with contributing guides** that show Markdown formatting examples

### Removing This Feature

If you decide you don't need nested markdown linting, you can remove this optional feature to reduce your dependency footprint. The script and its dependencies are not required for the core functionality of this template.

> **Note:** Removing this feature is optional. The script doesn't cause any problems if left in place—it simply won't be used if you don't invoke it.

**Steps to remove:**

1. **Delete the script file:**

   **Windows (PowerShell):**

   ```powershell
   Remove-Item -Path ".github/scripts/lint-nested-markdown.js" -Force
   ```

   **macOS/Linux/FreeBSD:**

   ```bash
   rm .github/scripts/lint-nested-markdown.js
   ```

2. **Remove the npm script from `package.json`:**

   Open `package.json` and delete the `lint:md:nested` line from the `scripts` section. For example:

   ```json
   {
     "scripts": {
       "lint:md": "markdownlint-cli2 \"**/*.md\" \"#node_modules\"",
       "lint:md:nested": "node .github/scripts/lint-nested-markdown.js",  ← Delete this line
       ...
     }
   }
   ```

   > **Note:** Keep all other scripts in the section; only remove the `lint:md:nested` line.

3. **Remove the npm dependencies only used by this script:**

   **Windows (PowerShell):**

   ```powershell
   npm uninstall glob jsonc-parser markdown-it
   ```

   **macOS/Linux/FreeBSD:**

   ```bash
   npm uninstall glob jsonc-parser markdown-it
   ```

4. **Update the lock file:**

   Run npm install to update `package-lock.json` to reflect the removed dependencies:

   ```bash
   npm install
   ```

5. **If you added pre-commit integration, remove the hook:**

   Open `.pre-commit-config.yaml` and remove the `lint-nested-markdown` hook section:

   ```yaml
   # Remove this entire block if present:
   - repo: local
     hooks:
       - id: lint-nested-markdown
         name: Lint nested Markdown
         entry: node .github/scripts/lint-nested-markdown.js
         language: node
         files: \.md$
         pass_filenames: true
   ```

---

## Markdown Lint Workflow Configuration

**File:** `.github/workflows/markdownlint.yml`

The Markdown Lint workflow enforces consistent Markdown formatting across your repository by running markdownlint on every push and pull request. While it works out-of-the-box, you can customize it to match your project's needs.

### Restricting Branch Triggers

The default configuration runs on all branches:

```yaml
on:
  push:
    branches: ["**"]
  pull_request:
    branches: ["**"]
```

**To run only on the default branch:**

```yaml
on:
  push:
    branches: ["main"]
  pull_request:
    branches: ["main"]
```

**To run on multiple specific branches:**

```yaml
on:
  push:
    branches: ["main", "develop"]
  pull_request:
    branches: ["main", "develop"]
```

### Adding Path Filters

By default, the workflow runs on every push and pull request regardless of which files changed. To only run the workflow when Markdown files or linting configuration changes:

```yaml
on:
  push:
    branches: ["main"]
    paths:
      - '**/*.md'
      - '.markdownlint.jsonc'
      - 'package.json'
      - 'package-lock.json'
  pull_request:
    branches: ["main"]
    paths:
      - '**/*.md'
      - '.markdownlint.jsonc'
      - 'package.json'
      - 'package-lock.json'
```

> **Note:** Include configuration files in the path filter to ensure the workflow runs when linting rules change.

### Changing Node.js Version

The workflow uses Node.js 20 by default:

```yaml
- name: Setup Node.js
  uses: actions/setup-node@v6
  with:
    node-version: '20'
```

**To use a different Node.js version:**

```yaml
- name: Setup Node.js
  uses: actions/setup-node@v6
  with:
    node-version: '22'
```

> **Note:** Ensure the Node.js version you choose is compatible with your project's dependencies. Check the markdownlint-cli2 documentation for supported Node.js versions.

### Disabling Nested Markdown Linting in CI

The workflow runs two linting steps: one for outer Markdown files and one for nested Markdown code fences. If you want to keep the outer linting but disable the nested linting step in CI:

**Option 1: Remove the step entirely**

Delete or comment out the nested linting step:

```yaml
# Remove or comment out this step:
# - name: Run markdownlint on nested Markdown code fences
#   id: lint-nested
#   continue-on-error: true
#   run: npm run lint:md:nested
```

And update the final check step to only check the outer linting result:

```yaml
- name: Check linting results
  if: steps.lint-outer.outcome == 'failure'
  run: |
    echo "::error::Markdown linting failed. Check the logs above for details."
    exit 1
```

**Option 2: Skip the step conditionally**

Add a condition to skip the nested linting step:

```yaml
- name: Run markdownlint on nested Markdown code fences
  id: lint-nested
  if: false  # Disabled - remove this line to re-enable
  continue-on-error: true
  run: npm run lint:md:nested
```

> **Note:** If you disable nested linting in CI, you may still want to run it locally using `npm run lint:md:nested` to catch issues before pushing.

### Removing the Workflow

If your project doesn't need Markdown linting in CI (for example, if you only use pre-commit hooks locally), you can remove the workflow file entirely.

**Windows (PowerShell):**

```powershell
Remove-Item -Path ".github/workflows/markdownlint.yml" -Force
```

**macOS/Linux/FreeBSD:**

```bash
rm -f .github/workflows/markdownlint.yml
```

> **Note:** Removing the CI workflow does not affect local linting. You can still run `npm run lint:md` locally or use pre-commit hooks to lint Markdown files before committing.

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

## Copilot Python Instructions Configuration

**File:** `.github/instructions/python.instructions.md`

The `python.instructions.md` file provides Python coding standards that GitHub Copilot applies when generating or editing `.py` files in your repository. These standards define style, structure, error handling, testing, and documentation requirements for Python code. The file supports two modes: **Baseline** (stdlib-first, portability-first) and **Modern-Advanced** (for projects using FastAPI, Pydantic, async frameworks, etc.).

Teams may want to customize these standards to match their project's specific requirements and preferences.

### Choosing Between Baseline and Modern-Advanced Mode

The file defines two distinct coding modes:

**Baseline Mode (Default):**

- Minimal dependencies (stdlib-first)
- Type hints are optional/opportunistic
- Explicit control flow; avoids metaprogramming
- Uses plain datatypes (`dict`, `list`, `tuple`) for simple tasks
- Prioritizes portability and clarity

**Modern-Advanced Mode:**

- Type hints required pervasively
- Uses `pathlib.Path` over `os.path`
- Supports async/await patterns
- Uses structured logging
- Suited for FastAPI, Pydantic, and type-heavy APIs

**To customize for your project:**

1. **For modern-only projects (FastAPI, Pydantic, async stacks):** Update the "Executive Summary: Author Profile" section to indicate that Modern-Advanced mode is the default. You may also simplify or remove Baseline-specific guidance from sections like "Baseline vs Modern-Advanced Mode" and the Quick Reference Checklist items tagged `[Baseline]`.

2. **For stdlib-first projects:** Keep Baseline mode as the default. Consider removing or de-emphasizing Modern-Advanced sections if your project never uses async frameworks or type-heavy APIs.

3. **For mixed projects:** Keep both modes documented but add project-specific guidance on when each applies (e.g., "Use Baseline mode for CLI utilities, Modern-Advanced mode for API services").

> **Note:** The mode primarily affects type hint requirements and framework usage patterns. Core style rules (naming, formatting, error handling) apply to both modes.

### Adjusting Line Length

The Python instructions reference a line length target of **<= 100** characters:

```markdown
- **[All]** **MUST** follow PEP 8/PEP 257; line length target **<= 100**
```

This setting should be consistent with your formatting tools in `.pre-commit-config.yaml`:

```yaml
# .pre-commit-config.yaml
- repo: https://github.com/psf/black
  hooks:
    - id: black
      args: [--line-length=100]

- repo: https://github.com/astral-sh/ruff-pre-commit
  hooks:
    - id: ruff
      args: [--fix, --line-length=100]
```

**To use Black's default of 88 characters:**

1. Update `.pre-commit-config.yaml` to use `--line-length=88` for both Black and Ruff
2. Update the line length reference in `python.instructions.md`:

   ```markdown
   - **[All]** **MUST** follow PEP 8/PEP 257; line length target **<= 88**
   ```

> **Note:** Ensure Black, Ruff, and the instruction file all use the same line length to avoid conflicts between Copilot-generated code and formatting tools.

### Customizing Type Hint Requirements

The file has different type hint expectations based on mode:

**Baseline Mode:**

```markdown
- **[Baseline]** **MAY** use type hints opportunistically for public APIs and complex structures.
```

**Modern-Advanced Mode:**

```markdown
- **[Modern]** Type hints are expected broadly; **MUST** run static checking (e.g., mypy/pyright) in CI.
```

**To customize for your project:**

1. **To require type hints everywhere:** Update the Baseline guidance to match Modern-Advanced requirements. Change `MAY` to `MUST` and add static checking requirements:

   ```markdown
   - **[All]** **MUST** use type hints for all function signatures and complex variables.
   - **[All]** **MUST** run static checking (mypy/pyright) in CI.
   ```

2. **To relax type hint requirements:** For projects where type hints are not a priority, update both mode sections to use `MAY` or `SHOULD`:

   ```markdown
   - **[All]** **SHOULD** use type hints for public APIs.
   - **[All]** **MAY** omit type hints for internal/private functions.
   ```

3. **For gradual adoption:** Document a migration path based on project maturity:

   ```markdown
   - New modules **MUST** include type hints for all public APIs.
   - Legacy modules **SHOULD** add type hints when modified.
   ```

> **Note:** If requiring strict type checking, ensure your CI workflow (`.github/workflows/ci.yml`) runs mypy without `continue-on-error: true`. See [CI Workflow Configuration](#ci-workflow-configuration) for details.

### Adjusting Documentation Standards

The file requires docstrings for all public modules, classes, and functions:

```markdown
- **[All]** Every public module/class/function **MUST** have a docstring.
- **[All]** Docstrings **MUST** emphasize contract: inputs, outputs, errors, edge cases, examples.
```

The default docstring format includes:

- Short summary line
- Longer description if needed
- Args, Returns, Raises sections
- Examples for tricky behavior

**To customize for your project:**

1. **To relax requirements for internal/private functions:** Add guidance that distinguishes between public and private documentation needs:

   ```markdown
   - **[All]** Every public module/class/function **MUST** have a docstring.
   - **[All]** Private functions (prefixed with `_`) **SHOULD** have a docstring but **MAY** use a brief one-line summary.
   - **[All]** Internal helper functions **MAY** omit docstrings if their purpose is obvious from context.
   ```

2. **To enforce a specific docstring style:** Add explicit style guidance such as Google style, NumPy style, or reStructuredText:

   ```markdown
   - **[All]** Docstrings **MUST** use Google style format.
   ```

3. **To require examples for all public functions:** Strengthen the example requirement:

   ```markdown
   - **[All]** Public functions **MUST** include at least one example in the docstring.
   ```

> **Note:** The instruction file uses a Google-style format (Args, Returns, Raises). If your project uses a different convention, update the example in the "Docstrings" section accordingly.

### Customizing Testing Requirements

The file specifies testing requirements for Python code:

```markdown
- **[All]** Tests **MUST** exist for non-trivial logic; **SHOULD** use `pytest` unless repo standard differs.
```

**To customize for your project:**

1. **To specify a different test framework:** If your project uses `unittest` or another framework, update the guidance:

   ```markdown
   - **[All]** Tests **MUST** exist for non-trivial logic; **SHOULD** use `unittest`.
   ```

2. **To add coverage requirements:** Specify minimum coverage thresholds:

   ```markdown
   - **[All]** Tests **MUST** exist for non-trivial logic; **SHOULD** use `pytest`.
   - **[All]** Test coverage **SHOULD** be >= 80% for new code.
   ```

3. **To require specific test patterns:** Add guidance for test organization:

   ```markdown
   - **[All]** Tests **SHOULD** be placed in `tests/` directory mirroring the `src/` structure.
   - **[All]** Test files **MUST** use `test_*.py` naming convention.
   - **[All]** **SHOULD** use table-driven tests for parsing/validation logic.
   ```

4. **To relax testing requirements for prototypes:** Add context-dependent guidance:

   ```markdown
   - **[All]** Production code **MUST** have tests for non-trivial logic.
   - **[All]** Prototype/experimental code **SHOULD** have tests but **MAY** defer coverage.
   ```

> **Note:** Testing configuration (pytest settings, coverage thresholds) is typically managed in `pyproject.toml`. See the "Testing" section in that file for related settings.

---

## Copilot PowerShell Instructions Configuration

**File:** `.github/instructions/powershell.instructions.md`

The `powershell.instructions.md` file provides comprehensive PowerShell coding standards that GitHub Copilot applies when generating or editing `.ps1` files in your repository. These standards define naming conventions, documentation requirements, error handling patterns, and compatibility guidelines for both legacy (v1.0) and modern (v5.1+/v7.x+) PowerShell environments.

Teams may want to customize these standards to match their project's specific requirements and preferences.

### Customizing Variable Naming Conventions

The file defaults to Hungarian-style type-prefixed variable naming for local variables, particularly in v1.0-targeted code:

```powershell
$strMessage    # String
$intCount      # Integer
$boolResult    # Boolean
$arrElements   # Array
$objInstance   # Object
```

Teams with modern codebases that have strong IDE support (IntelliSense, type inference) may prefer plain camelCase:

```powershell
$message
$count
$result
$elements
$instance
```

**To change this preference, update the following sections:**

1. **"Local Variable Naming: Type-Prefixed camelCase"** section - Modify the naming rules and examples
2. **"Options for Local Variable Prefixes: Analysis"** table - Update the recommendation based on your choice
3. **Quick Reference Checklist** - Update the item referencing variable naming conventions (the `[v1.0]` scoped item about local variables)

> **Note:** If your project exclusively targets modern PowerShell (5.1+, 7.x), plain camelCase is generally preferred as IDEs provide type information. Type prefixes are most valuable in v1.0 environments or when editing without IDE support.

### Choosing Between v1.0 and Modern Patterns

The file distinguishes between two function architecture styles:

**v1.0-targeted:**

- Uses `trap` for error handling
- No `[CmdletBinding()]` attribute
- Explicit integer return codes (0=success, -1=failure)
- Reference parameters (`[ref]`) for outputs
- No pipeline input support

**Modern (v2.0+):**

- Uses `try/catch` for error handling
- Requires `[CmdletBinding()]` attribute
- Streaming output to pipeline
- `Write-Verbose` and `Write-Debug` for diagnostics
- Full pipeline support

**To customize for your environment:**

- **Modern-only projects (PowerShell 5.1+, 7.x):** Remove or de-emphasize the v1.0 sections. Update the Quick Reference Checklist to remove items tagged `[v1.0]` and make `[Modern]` items the default.

- **Legacy compatibility projects:** Keep the v1.0 sections as primary guidance. Update the "Executive Summary: Author Profile" to emphasize v1.0 compatibility as the default.

- **Mixed environments:** Keep both patterns but clarify when each applies based on your specific criteria (e.g., "Use v1.0 patterns for standalone utilities, Modern patterns for module functions").

### Adjusting Documentation Requirements

The file requires comprehensive comment-based help for all functions, including:

- `.SYNOPSIS`, `.DESCRIPTION`, `.PARAMETER`, `.EXAMPLE`, `.INPUTS`, `.OUTPUTS`, `.NOTES`
- Version number in `.NOTES` (format: `Major.Minor.YYYYMMDD.Revision`)
- Multiple examples with input, output, and explanation

**Teams may want to customize these requirements:**

1. **For internal/private helper functions:** Relax requirements in the "Comment-Based Help: Structure and Format" section to allow minimal documentation (e.g., `.SYNOPSIS` only) for private helper functions.

2. **For versioning format:** Update the "Function and Script Versioning" section if your project uses a different versioning scheme (e.g., SemVer without date component):

   ```powershell
   # Alternative format
   # .NOTES
   # Version: 1.2.3
   ```

3. **For example requirements:** Reduce the requirement for multiple examples in the "Help Content Quality: High Standards" section if this is too burdensome for your team.

> **Note:** Even with relaxed requirements, maintaining at least `.SYNOPSIS` for all functions is strongly recommended for discoverability with `Get-Help`.

### Customizing Brace Style Preference

The file enforces OTBS (One True Brace Style) where opening braces are placed on the same line as the statement:

```powershell
# OTBS (default)
if ($condition) {
    # code
} else {
    # code
}
```

Some teams prefer Allman style (braces on new lines):

```powershell
# Allman style
if ($condition)
{
    # code
}
else
{
    # code
}
```

**To change brace style:**

1. Update the "Brace Placement (OTBS)" section in this file to reflect your preferred style
2. Update `.github/linting/PSScriptAnalyzerSettings.psd1` to match (see [PSScriptAnalyzer Configuration](#psscriptanalyzer-configuration) for details)

> **Note:** Brace style must be consistent between the instruction file and PSScriptAnalyzer settings. Inconsistent settings will cause conflicts between Copilot-generated code and linting rules.

### Adjusting Error Handling Patterns

The file documents specific return code conventions for v1.0-targeted functions:

| Code | Meaning |
| --- | --- |
| `0` | Full success |
| `1-5` | Partial success with additional data |
| `-1` | Complete failure |

**To customize for your project:**

1. **Different return codes:** Update the "Return Semantics: Explicit Status Codes" section with your project's conventions. For example, some projects use positive integers for all error codes:

   ```powershell
   # Alternative convention
   # 0 = Success
   # 1 = General error
   # 2 = File not found
   # 3 = Permission denied
   ```

2. **Exception-based patterns:** For modern-only projects, you may prefer to rely entirely on exceptions rather than return codes. Update the "Modern catch Block Requirements" section to document your exception handling patterns.

3. **Custom exception types:** If your project defines custom exception types, document them and update the error handling sections accordingly.

---

## Copilot Main Instructions Configuration

**File:** `.github/copilot-instructions.md`

The main `copilot-instructions.md` file provides repository-wide instructions that GitHub Copilot applies when generating or editing code. It includes sections on pre-commit discipline, testing tools, and other project-wide standards. These sections should be customized to match your project's actual tools and workflows.

### Customizing the Pre-commit Discipline Section

The Pre-commit Discipline section (near the top of `copilot-instructions.md`) tells Copilot how to run pre-commit checks, what commands to use, and how to handle CI failures. This ensures Copilot generates code that follows your project's code quality workflow.

The default configuration assumes:

- The [pre-commit](https://pre-commit.com/) framework with `pre-commit run --all-files`
- npm-based markdown linting with `npm run lint:md`
- A `copilot/**` branch pattern for automated fixes

**To customize for your project:**

1. **Different pre-commit tools:** If you use a different tool (e.g., Husky, lefthook, or custom scripts), update the workflow section:

   ```markdown
   **Workflow:**

   1. Make your code changes
   2. Run pre-commit checks locally (e.g., `npx husky run` or `make lint`)
   3. Review and commit ALL auto-fixes as part of your change
   4. Push to GitHub
   ```

2. **Different linting commands:** Update command examples to match your project:

   ```markdown
   **Workflow:**

   1. Make your code changes
   2. Run pre-commit checks locally (e.g., `make lint` or `./scripts/lint.sh`)
   3. Review and commit ALL auto-fixes as part of your change
   4. Push to GitHub
   ```

3. **No pre-commit framework:** If your project uses only CI-based checks without local pre-commit hooks, simplify the section:

   ```markdown
   ## Pre-commit Discipline (CRITICAL)

   **⚠️ ALWAYS run linting checks before committing code.**

   **Workflow:**

   1. Make your code changes
   2. Run linting locally: `npm run lint` (or your project's lint command)
   3. Review and fix all issues before committing
   4. Push to GitHub

   **If CI fails:**

   1. Pull the latest branch
   2. Run linting locally and fix issues
   3. Commit fixes
   4. Push again
   ```

4. **Different branch patterns for automated fixes:** If you use a different branch naming convention for AI-generated PRs, update the Auto-Fix Workflow section to match (and update the corresponding workflow file).

> **Note:** The pre-commit section should accurately reflect your project's tooling. Incorrect instructions will cause Copilot to suggest wrong commands or skip necessary checks.

### Customizing the Testing Tools Section

The Testing Tools section (near the bottom of `copilot-instructions.md`) tells Copilot what test frameworks your project uses, where tests are located, and how to run them. This ensures Copilot generates tests that match your project's conventions.

The default configuration includes:

| Language | Framework | Configuration | Test Location |
| --- | --- | --- | --- |
| Python | pytest | `pyproject.toml` (`[tool.pytest.ini_options]`) | `tests/` |
| PowerShell | Pester 5.x | Inline in `.github/workflows/powershell-ci.yml` | `tests/PowerShell/` |

**To customize for your project:**

1. **Different test frameworks:** Update the table to reflect your actual frameworks:

   ```markdown
   ## Testing Tools

   This repository includes testing infrastructure for the following languages:

   | Language | Framework | Configuration | Test Location |
   | --- | --- | --- | --- |
   | Python | unittest | `setup.cfg` | `tests/` |
   | JavaScript | Jest | `jest.config.js` | `__tests__/` |
   | TypeScript | Vitest | `vitest.config.ts` | `src/**/*.test.ts` |
   ```

2. **Different test locations:** Update the table and running instructions to match your directory structure:

   ```markdown
   | Language | Framework | Configuration | Test Location |
   | --- | --- | --- | --- |
   | Python | pytest | `pytest.ini` | `spec/` |
   | Ruby | RSpec | `.rspec` | `spec/` |
   ```

3. **Update the "Running Tests" section:** Ensure the commands match your setup (this example shows commands for Jest and unittest, matching the frameworks in example 1):

   ````markdown
   ### Running Tests

   **JavaScript:**

   ```bash
   npm test
   ```

   **Python:**

   ```bash
   python -m unittest discover -s tests
   ```
   ````

4. **Single-language projects:** Remove rows for languages you don't use:

   ````markdown
   ## Testing Tools

   This repository uses pytest for testing:

   | Language | Framework | Configuration | Test Location |
   | --- | --- | --- | --- |
   | Python | pytest | `pyproject.toml` | `tests/` |

   ### Running Tests

   ```bash
   pytest tests/ -v
   ```
   ````

5. **Additional test types:** If your project includes integration tests, end-to-end tests, or other test types, document them:

   ```markdown
   ## Testing Tools

   | Test Type | Framework | Configuration | Location |
   | --- | --- | --- | --- |
   | Unit tests | pytest | `pyproject.toml` | `tests/unit/` |
   | Integration tests | pytest | `pyproject.toml` | `tests/integration/` |
   | E2E tests | Playwright | `playwright.config.ts` | `tests/e2e/` |
   ```

> **Note:** Keep the Testing Tools section synchronized with your actual test configuration. Incorrect information will cause Copilot to generate tests in wrong locations or using wrong frameworks.

### Updating Related Sections

When customizing the Pre-commit or Testing sections, you may also need to update these related sections in `copilot-instructions.md`:

- **How to Work (Definition of Done):** Update test location references (e.g., `tests/` to `spec/`)
- **Language-Specific Instructions table:** Ensure it matches your language instruction files
- **Linting Configurations:** Update linting tool references if you use different linters

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

### Customizing Dependency Installation

The CI workflow installs the project with development dependencies using:

```yaml
pip install -e ".[dev]"
```

This command appears in both the `type-check` and `test` jobs.

**To use different dependency groups:**

If your `pyproject.toml` uses a different optional dependency group name:

```yaml
# For a [project.optional-dependencies] section named "test"
pip install -e ".[test]"

# For multiple groups
pip install -e ".[dev,test]"
```

**To use requirements.txt instead:**

If your project uses `requirements.txt` files instead of `pyproject.toml` optional dependencies:

```yaml
- name: Install dependencies
  run: |
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    pip install -r requirements-dev.txt  # If you have separate dev requirements
```

> **Note:** Update both the `type-check` job (line ~131) and the `test` job (line ~183) to keep them consistent.

---

## Auto-fix Pre-commit Workflow Configuration

**File:** `.github/workflows/auto-fix-precommit.yml`

The template includes an optional workflow that automatically runs pre-commit hooks and commits any auto-fixes (such as formatting corrections and trailing whitespace removal) for branches created by the GitHub Copilot Coding Agent.

### Understanding the Workflow

This workflow:

- Triggers only on `copilot/**` branches when pushed by `copilot-swe-agent[bot]`
- Runs pre-commit hooks with auto-fix enabled
- Commits any changes back to the branch automatically
- Helps AI-assisted development pass pre-commit checks without manual intervention

> **Recommendation:** Keep this workflow enabled if you use GitHub Copilot Coding Agent. The safety net significantly reduces the need for manual pre-commit fix commits.

### When to Keep This Workflow

Keep this workflow if:

- You plan to use GitHub Copilot Coding Agent for automated PRs
- You want a safety net that auto-fixes pre-commit issues on `copilot/**` branches
- You prefer automated fixes over manual intervention

### Removing This Workflow

If you don't use GitHub Copilot Coding Agent or prefer to manually commit pre-commit fixes, you can safely remove this workflow.

> **Note:** Removing this workflow is safe—the standard `ci.yml` workflow will still run pre-commit checks and report any issues that need to be fixed.

**Steps to remove:**

**Windows (PowerShell):**

```powershell
Remove-Item -Path ".github/workflows/auto-fix-precommit.yml" -Force
```

**macOS/Linux/FreeBSD:**

```bash
rm -f .github/workflows/auto-fix-precommit.yml
```

---

## Placeholder Check Workflow Configuration

**File:** `.github/workflows/check-placeholders.yml`

The placeholder check workflow verifies that template placeholders (`OWNER/REPO`, `@OWNER`, `[security contact email]`) have been replaced. It runs automatically in all repositories created from the template.

### Understanding the Workflow

The workflow uses automatic detection to determine whether to run:

```yaml
if: github.repository != 'franklesniak/copilot-repo-template'
```

This means the workflow:

- **Runs automatically** in your repository (no configuration needed)
- **Is disabled** only in the original template repository

### When to Keep This Workflow

Keep this workflow if you:

- Plan to make future updates from the template that might introduce new placeholder files
- Want a safety net to catch accidental placeholder remnants
- Have contributors who might add files with placeholder patterns

### Removing This Workflow

If you have replaced all placeholders and don't anticipate needing this check:

**Windows (PowerShell):**

```powershell
Remove-Item -Force ".github\workflows\check-placeholders.yml"
```

**macOS/Linux/FreeBSD:**

```bash
rm -f .github/workflows/check-placeholders.yml
```

### Adding Custom Placeholder Patterns

If your project uses additional placeholder patterns that should be checked, edit `.github/workflows/check-placeholders.yml` and locate the "Additional placeholder patterns check" step. Find the `PATTERNS` array and add your custom patterns:

```yaml
- name: Additional placeholder patterns check
  run: |
    # ... existing code ...
    PATTERNS=(
      "your-org"
      "your-repo"
      "YOUR_ORG"
      "YOUR_REPO"
      "YOUR_CUSTOM_PLACEHOLDER"  # Add your custom patterns here
    )
```

### Converting Warnings to Hard Failures

By default, some checks in the "Additional placeholder patterns check" step produce warnings rather than failures (e.g., `Project Name` in README.md, patterns in PR templates). To make these hard failures, edit `.github/workflows/check-placeholders.yml` and change the warning-only sections to set `FOUND_PLACEHOLDERS=true`:

```yaml
# Before (warning only):
if grep -n "^# Project Name$" README.md; then
  echo "::warning file=README.md::Found 'Project Name' placeholder..."
  FOUND_WARNINGS=true
fi

# After (hard failure):
if grep -n "^# Project Name$" README.md; then
  echo "::error file=README.md::Found 'Project Name' placeholder..."
  FOUND_PLACEHOLDERS=true  # Changed from FOUND_WARNINGS
fi
```

---

## PowerShell CI Workflow Configuration

**File:** `.github/workflows/powershell-ci.yml`

The PowerShell CI workflow runs PSScriptAnalyzer linting and Pester tests for PowerShell scripts. It runs automatically on every push and pull request and automatically skips if no PowerShell files are found in the repository.

### Understanding the Workflow

The workflow consists of two jobs:

1. **lint**: Runs PSScriptAnalyzer on all `.ps1` files (skips if no files found)
2. **test**: Runs Pester tests on Windows, macOS, and Linux (skips if no `*.Tests.ps1` files found)

The workflow uses automatic detection, so you don't need to configure anything if you have PowerShell files—it just works.

### Customizing Pester Test Paths

By default, Pester tests are run from the `tests/` directory. To use a different directory, modify the `$config.Run.Path` setting in the "Run Pester tests" step:

```powershell
$config.Run.Path = "your_tests_directory/"  # Change from default "tests/"
```

### Customizing Test Output Format

The default test output format is `NUnitXml`. To use a different format:

```powershell
$config.TestResult.OutputFormat = "JUnitXml"  # Default is "NUnitXml"
```

Available formats include `NUnitXml`, `JUnitXml`, and `NUnit2.5`.

### Customizing the OS Matrix

By default, Pester tests run on Ubuntu, Windows, and macOS:

```yaml
strategy:
  matrix:
    os: [ubuntu-latest, windows-latest, macos-latest]
```

**To run on fewer operating systems:**

```yaml
strategy:
  matrix:
    os: [windows-latest]  # Windows only
```

**To run on Windows and Linux only:**

```yaml
strategy:
  matrix:
    os: [ubuntu-latest, windows-latest]
```

### Adding Path-Based Filtering

The template deliberately does not use path-based filtering because this is a template repository where all workflows should run on all changes for testing purposes. However, consumers of the template can add path filtering for efficiency:

```yaml
on:
  push:
    branches: ["**"]
    paths:
      - "**/*.ps1"
      - ".github/workflows/powershell-ci.yml"
      - ".github/linting/PSScriptAnalyzerSettings.psd1"
  pull_request:
    branches: ["**"]
    paths:
      - "**/*.ps1"
      - ".github/workflows/powershell-ci.yml"
      - ".github/linting/PSScriptAnalyzerSettings.psd1"
```

> **Note:** Include configuration files in the path filter to ensure the workflow runs when linting rules or the workflow itself changes.

### Removing the Workflow

If your project doesn't use PowerShell, you can remove the workflow:

**Windows (PowerShell):**

```powershell
Remove-Item -Path ".github/workflows/powershell-ci.yml" -Force
```

**macOS/Linux/FreeBSD:**

```bash
rm -f .github/workflows/powershell-ci.yml
```

> **Note:** If you want to remove all PowerShell-related files from the repository (not just the workflow), see the "If NOT Using PowerShell" section in [GETTING_STARTED_NEW_REPO.md](GETTING_STARTED_NEW_REPO.md) for comprehensive removal instructions.

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
