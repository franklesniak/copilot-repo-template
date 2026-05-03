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
- [Code of Conduct Configuration](#code-of-conduct-configuration)
- [Pull Request Template Customization](#pull-request-template-customization)
- [Dependabot Configuration](#dependabot-configuration)
- [Pre-commit Configuration](#pre-commit-configuration)
- [Schema Validation Configuration](#schema-validation-configuration)
- [Prettier for JSON/JSONC (Opt-in)](#prettier-for-jsonjsonc-opt-in)
- [JSONC Validation (Opt-in)](#jsonc-validation-opt-in)
- [JSON5 Support (Opt-in)](#json5-support-opt-in)
- [Ecosystem-Specific YAML Validators (Opt-in)](#ecosystem-specific-yaml-validators-opt-in)
- [Future SchemaStore Validation for Repository Configuration Files](#future-schemastore-validation-for-repository-configuration-files)
- [Removing the Worked Example Schema](#removing-the-worked-example-schema)
- [Markdown Linting Configuration](#markdown-linting-configuration)
  - [Using the cli2-Specific Configuration Format](#using-the-cli2-specific-configuration-format)
- [Nested Markdown Linting Configuration](#nested-markdown-linting-configuration)
- [Markdown Lint Workflow Configuration](#markdown-lint-workflow-configuration)
- [Copilot Documentation Instructions Configuration](#copilot-documentation-instructions-configuration)
- [Copilot Python Instructions Configuration](#copilot-python-instructions-configuration)
- [Copilot PowerShell Instructions Configuration](#copilot-powershell-instructions-configuration)
- [Copilot Terraform Instructions Configuration](#copilot-terraform-instructions-configuration)
- [Copilot Main Instructions Configuration](#copilot-main-instructions-configuration)
- [Customizing Agent Instruction Files](#customizing-agent-instruction-files)
- [CI Workflow Configuration](#ci-workflow-configuration)
- [Auto-fix Pre-commit Workflow Configuration](#auto-fix-pre-commit-workflow-configuration)
- [Placeholder Check Workflow Configuration](#placeholder-check-workflow-configuration)
- [PowerShell CI Workflow Configuration](#powershell-ci-workflow-configuration)
- [Using the Python Template Files](#using-the-python-template-files)
- [Using the Pester Test Template](#using-the-pester-test-template)
- [PSScriptAnalyzer Configuration](#psscriptanalyzer-configuration)
- [CODEOWNERS Configuration](#codeowners-configuration)
- [Node.js Package Configuration](#nodejs-package-configuration)
- [Gitignore Configuration](#gitignore-configuration)
- [License Customization](#license-customization)
- [VS Code PowerShell File Encoding for Non-ASCII Characters](#vs-code-powershell-file-encoding-for-non-ascii-characters)
- [Ongoing Maintenance](#ongoing-maintenance)
  - [Updating Pre-commit Hooks](#updating-pre-commit-hooks)
  - [Reviewing Python Version Requirements](#reviewing-python-version-requirements)

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

## Code of Conduct Configuration

**File:** `CODE_OF_CONDUCT.md`

The template includes the Contributor Covenant v3.0, a widely-adopted code of conduct for open source projects. This section covers customization options and alternatives.

### Alternative Code of Conduct Templates

While the Contributor Covenant is the most widely used code of conduct for open source, you may choose a different template based on your project's needs:

| Template | Description | Best For |
| --- | --- | --- |
| [Contributor Covenant v3.0](https://www.contributor-covenant.org/version/3/0/code_of_conduct/) | Comprehensive, widely recognized | Most open source projects (template default) |
| [Citizen Code of Conduct](https://github.com/stumpsyn/policies/blob/master/citizen_code_of_conduct.md) | Community-focused, detailed examples | Projects emphasizing community building |
| Organization-specific | Custom policies matching org standards | Enterprise or organizational projects |

**To use a different template:**

1. Replace the contents of `CODE_OF_CONDUCT.md` with your chosen template
2. Update any contact information or placeholders
3. Review enforcement procedures and adjust as needed

### Customizing Enforcement Procedures

The default enforcement section includes a four-tier ladder (Warning → Temporarily Limited Activities → Temporary Suspension → Permanent Ban). You may customize this based on your project's needs:

#### Enforcement Contact Information

Replace `[INSERT CONTACT METHOD]` with your preferred reporting method:

```markdown
To report a possible violation, contact us via: conduct@your-project.org
```

**Contact method options:**

- **Email address:** Simple, widely understood, but requires email monitoring
- **Web form:** Provides structured reporting, can integrate with issue tracking
- **Multiple channels:** List several options (email, form, direct message to maintainers)

#### Response Timeline Commitments

Consider adding explicit timeline commitments to the enforcement section:

```markdown
Community Moderators will acknowledge receipt of reports within 48 hours and
aim to provide a resolution within 7 days for straightforward cases. Complex
cases may require additional time, and reporters will be updated on progress.
```

#### Scope Customization

The default scope section covers community spaces and official representation. Customize based on your project's context:

```markdown
## Scope

This Code of Conduct applies within:

- All repository spaces (issues, pull requests, discussions)
- Project communication channels (Slack, Discord, mailing lists)
- Project events (meetups, conferences, online gatherings)
- When representing the project in public spaces
```

### Removing the Code of Conduct

Small personal projects or projects that don't accept external contributions may not need a code of conduct file.

**To remove:**

1. Delete `CODE_OF_CONDUCT.md` from your repository
2. The placeholder check workflow will continue to pass—`CODE_OF_CONDUCT.md` is treated as optional

**Considerations before removing:**

- Projects that grow to accept contributions later may want to add one
- Some organizations require a code of conduct for all projects
- Having a code of conduct signals that your project welcomes diverse contributors

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

### Contributing Guidelines Link for GHES or External Contexts

The default PR template uses a relative link for the contributing guidelines:

```markdown
[contributing guidelines](../blob/HEAD/CONTRIBUTING.md)
```

This relative link works correctly in GitHub.com PR views but may not resolve correctly in:

- PR preview/draft mode before the branch is pushed
- GitHub Enterprise Server (GHES) — compatibility varies by version
- External contexts (local Markdown preview, email notifications, etc.)

**If you need the link to work in GHES or external contexts**, replace it with an absolute URL:

```markdown
[contributing guidelines](https://github.com/OWNER/REPO/blob/HEAD/CONTRIBUTING.md)
```

Replace `OWNER/REPO` in the URL above with your actual organization and repository name.

**If your CONTRIBUTING.md is in a different location** (e.g., `docs/CONTRIBUTING.md`), update the path accordingly:

```markdown
[contributing guidelines](../blob/HEAD/docs/CONTRIBUTING.md)
```

### Customizing Additional Notes Section

The "Additional Notes" section provides PR authors a place to add context for reviewers that doesn't fit elsewhere. Consider adding prompts for common needs:

```markdown
## Additional Notes

<!-- Add any additional context, such as: -->
<!-- - Migration steps (for breaking changes) -->
<!-- - Deployment considerations -->
<!-- - Rollback instructions -->
```

### Customizing Related Issues Section

The template uses `Closes #` for linking to issues. Update the syntax if your project uses different keywords:

| Keyword | Effect |
| --- | --- |
| `Closes OWNER/REPO#123` | Closes the issue when PR is merged (default) |
| `Fixes OWNER/REPO#123` | Alternative keyword, same effect |
| `Resolves OWNER/REPO#123` | Alternative keyword, same effect |

Choose one keyword and use it consistently across your project.

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
  rev: 26.1.0
  hooks:
    - id: black
      args: [--line-length=100]

- repo: https://github.com/astral-sh/ruff-pre-commit
  rev: v0.14.14
  hooks:
    - id: ruff-check
      args: [--fix, --line-length=100]
```

**To use Black's default (88 characters):**

```yaml
args: [--line-length=88]
```

> **Note:** Ensure both Black and Ruff use the same line length to avoid conflicts.

### Adding Hooks for Other Languages

**Prettier (JavaScript/TypeScript/CSS):**

```yaml
- repo: https://github.com/pre-commit/mirrors-prettier
  rev: v3.1.0
  hooks:
    - id: prettier
      types_or: [javascript, jsx, ts, tsx, css, markdown]
```

> **JSON/JSONC and YAML are intentionally omitted from `types_or` above.** For JSON/JSONC, see [Prettier for JSON/JSONC (Opt-in)](#prettier-for-jsonjsonc-opt-in), which recommends a `repo: local` hook over `pre-commit/mirrors-prettier` to avoid pinning the Prettier version in two places. Prettier for YAML is discouraged by default in this template; see the YAML subsection of that same section for the reconciliation requirements if a project chooses to adopt it anyway.

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

## Schema Validation Configuration

**Files:** `.pre-commit-config.yaml`, `schemas/`, project test directory (for example, `tests/`)

This template ships `schemas/` with one clearly removable worked example (see [`schemas/README.md`](schemas/README.md)). **The worked example is the only `check-jsonschema` configuration enabled by default.** Beyond that, schema validation is opt-in and SHOULD be added per real schema-backed file family. If your downstream project does not need the worked example, follow the canonical [downstream removal checklist](schemas/README.md#downstream-removal-checklist) in `schemas/README.md` to remove it.

### When to Add `check-jsonschema`

Add a [`check-jsonschema`](https://github.com/python-jsonschema/check-jsonschema) hook when you have:

1. A real schema under `schemas/` (for example, `schemas/project-config.schema.json`), and
2. A real, identifiable file family that the schema validates (for example, every `config/*.json` in your project).

Do **not** add `check-jsonschema` hooks for schemas that do not yet exist, and do not configure a generic "validate every JSON/YAML file" hook. Pre-commit already runs `check-json` and `check-yaml` for syntax; `check-jsonschema` is for contract validation against a specific schema.

### Adding a Hook for One File Family

Add one hook per `(schema, file family)` pair to `.pre-commit-config.yaml`:

```yaml
- repo: https://github.com/python-jsonschema/check-jsonschema
  rev: 0.33.3
  hooks:
    - id: check-jsonschema
      name: Validate project JSON config
      files: ^config/.*\.json$
      args:
        - --schemafile
        - schemas/project-config.schema.json
```

> **Version pinning.** Implementers MUST verify and pin a current upstream version of `check-jsonschema` when enabling the hook, rather than copying the example `rev:` value above. Look up the latest tagged release at the upstream repository before adoption and update the pin via your normal dependency-update process (for example, Dependabot's `pre-commit` ecosystem).

If you have multiple schema-backed file families, add one hook **per family**, each scoped with its own `files:` pattern. Do not combine unrelated families into a single hook.

### Testing Valid Examples

Sample data files that should validate cleanly can be placed in either of two locations, with different validation consequences:

- **Inside the file family path covered by the family hook** (for example, `config/example.valid.json` for the hook above). The family hook will validate these automatically because they match its `files:` pattern.
- **Under `schemas/examples/<schema-name>/{valid,invalid}/`** (for example, `schemas/examples/project-config/valid/minimal.json`). This `schemas/examples/<schema-name>/{valid,invalid}/` layout is the convention used by `schemas/README.md` and the pytest tests referenced below, but it does **not** match the family hook's `files:` pattern, so these examples need a separate validation path. Choose one of:

  - Add a dedicated `check-jsonschema` hook scoped to **valid** fixtures under `schemas/examples/` only (for example, `files: ^schemas/examples/project-config/valid/.*\.json$`). Anchor the pattern under the `valid/` directory so the hook does not pick up `invalid/` fixtures (which MUST NOT be wired into a normal `check-jsonschema` hook — see the next subsection). This aligns with the `schemas/examples/<schema-name>/{valid,invalid}/` layout used in `schemas/README.md` § Examples and exercised by both [`tests/test_schema_examples.py`](tests/test_schema_examples.py) and [`templates/python/tests/test_schema_examples.py`](templates/python/tests/test_schema_examples.py).
  - Run `check-jsonschema` directly from a CI step or local script:

    ```bash
    check-jsonschema \
      --schemafile schemas/project-config.schema.json \
      schemas/examples/project-config/valid/minimal.json
    ```

  - Wire the example into the opt-in pytest template described under [Testing Invalid Examples](#testing-invalid-examples) (it exercises both valid and invalid cases).

Whichever placement you choose, valid examples MUST exit with code `0`; a non-zero exit indicates a broken example or a schema regression and MUST be fixed before merging.

### Testing Invalid Examples

Invalid examples (intentionally malformed fixtures used to prove that the schema rejects bad input) MUST NOT be wired into a normal `check-jsonschema` pre-commit hook, because the validator's non-zero exit would be reported as a hook failure on every run. Instead, write a test or script that **asserts validation fails**.

A starter pytest template lives at [`templates/python/tests/test_schema_examples.py`](templates/python/tests/test_schema_examples.py); the active, canonical version that this repository runs in CI lives at [`tests/test_schema_examples.py`](tests/test_schema_examples.py). Both auto-discover `(schema, example, expected_to_pass)` triples from `schemas/*.schema.json` and `schemas/examples/<schema-name>/{valid,invalid}/`. To use the starter:

1. Copy the file into your project's real `tests/` directory.
2. Place schemas under `schemas/<name>.schema.json` and examples under `schemas/examples/<name>/{valid,invalid}/`. Discovery is automatic — no per-case configuration is required.
3. Choose how to make `check-jsonschema` available to the test environment (see below).

### Making `check-jsonschema` Available to Tests

The active root test [`tests/test_schema_examples.py`](tests/test_schema_examples.py) requires `check-jsonschema`, which is declared in the root `pyproject.toml` `dev` dependency group and installed by `.github/workflows/python-ci.yml` via `pip install -e ".[dev]"`. The starter under `templates/python/tests/test_schema_examples.py` retains a `skipif` guard so that downstream projects can copy it before adding the dependency. If you want the starter to run unconditionally in your repository, do one of the following:

- **Add it as a dev/test dependency.** For example, in `pyproject.toml`:

  ```toml
  [project.optional-dependencies]
  dev = [
      "pytest",
      "check-jsonschema",
  ]
  ```

  Then install with `pip install -e ".[dev]"` (or your preferred dev-install command) so `check-jsonschema` is on `PATH` for tests.

- **Install it in CI only.** Add an explicit install step (for example, `pip install check-jsonschema`) in the relevant CI workflow before the test step. Local developers without the tool installed will see the test skip rather than fail.

If you remove the `skipif` guard, you MUST ensure `check-jsonschema` is installed in every environment where the test runs; otherwise the test will fail with a `FileNotFoundError`-style error rather than a clear "tool missing" message.

### Defaults Recap

- The template ships **one** active `check-jsonschema` configuration by default: the worked-example schema (`schemas/example-config.schema.json`) and its valid example data files. A companion `check-metaschema` hook self-validates the schema against its declared JSON Schema Draft 2020-12 metaschema. Downstream repositories MAY add additional `check-jsonschema` hook entries for their own schema-backed file families, and MAY remove the worked example via the canonical [downstream removal checklist](schemas/README.md#downstream-removal-checklist).
- The template ships an active root test, [`tests/test_schema_examples.py`](tests/test_schema_examples.py), that depends on `check-jsonschema` (declared in the root `pyproject.toml` `dev` group). A starter version with the same essential pattern is provided at `templates/python/tests/test_schema_examples.py` for downstream adoption.
- Beyond the worked example, schema validation is opt-in; downstream repositories add real hooks and tests when they introduce additional real schemas.

---

## Prettier for JSON/JSONC (Opt-in)

**Files:** `package.json`, `.prettierrc.json`, `.prettierignore`, `.pre-commit-config.yaml`

[Prettier](https://prettier.io/) is **not** part of the default JSON/YAML toolchain in this template. Prettier MAY be adopted on a per-repository basis to enforce JSON and JSONC formatting beyond what `check-json` validates. **No Prettier configuration, dependency, or hook is added to the repo root by default.** Adoption is an explicit project decision.

> **Background.** The default pre-commit stack uses `check-json` (strict `.json` syntax only), `check-yaml`, `yamllint`, and `actionlint`. See [Schema Validation Configuration](#schema-validation-configuration) for the schema-validation path, and the [Prettier deferral ADR in `.github/TEMPLATE_DESIGN_DECISIONS.md`](.github/TEMPLATE_DESIGN_DECISIONS.md#design-decision-prettier-deferral-for-data-files) for the rationale behind keeping Prettier opt-in.

### When to Adopt Prettier for JSON/JSONC

Adopt Prettier for JSON/JSONC when **at least one** of the following is true:

- The project already uses Node tooling for other purposes (for example, `markdownlint-cli2`, JavaScript/TypeScript builds), so adding Prettier does not introduce a new ecosystem.
- The team wants editor format-on-save consistency across contributors.
- Many JSON/JSONC files in the project benefit from formatter enforcement (consistent indentation, trailing newline, key spacing) that `check-json` does not provide.
- The project has many `.jsonc` files and wants formatting enforcement, since `check-json` does not validate `.jsonc`. Prettier is **one option among several pieces of JSONC-aware tooling** that can fill this gap (other options include dedicated JSONC parsers and schema validators that understand JSONC).

### When Not to Adopt Prettier for JSON/JSONC

Do **not** adopt Prettier when:

- Adding Node tooling would create friction (for example, the project is otherwise pure Python, PowerShell, or Terraform with no existing Node dependency).
- `check-json` syntax validation alone is sufficient for the project's JSON files.
- The project does not want formatter-controlled diffs on data files (Prettier rewrites files in-place; downstream consumers MUST be comfortable with formatter-driven churn).

### Important Caveat: Prettier Does Not Sort JSON Keys

Prettier formats JSON whitespace, indentation, and line endings, but it **does not** sort object keys. Stable key ordering — often the highest-value JSON-stability property — must still be enforced by hand or by a separate tool. Adopters who care about deterministic key order MUST treat Prettier as a formatting tool only and add a separate key-ordering process if needed.

### Recommended `package.json` Scripts

If Prettier is adopted, add `format:json` and `lint:json:format` scripts to `package.json` so that contributors and CI use the same commands:

```json
{
  "scripts": {
    "format:json": "prettier --write \"**/*.{json,jsonc}\" \"!node_modules/**\"",
    "lint:json:format": "prettier --check \"**/*.{json,jsonc}\" \"!node_modules/**\""
  }
}
```

The `--check` variant is suitable for CI; the `--write` variant rewrites files in place locally.

### Recommended `.prettierrc.json`

A minimal Prettier configuration that aligns with the template's other formatting defaults (LF line endings, 2-space indent):

```json
{
  "printWidth": 120,
  "tabWidth": 2,
  "useTabs": false,
  "endOfLine": "lf",
  "trailingComma": "none"
}
```

`trailingComma: "none"` is required for strict `.json`; for `.jsonc` consumers that accept trailing commas, this setting is still safe (Prettier will simply omit them).

### Recommended `.prettierignore`

Add a `.prettierignore` file that excludes generated files, dependencies, and any directories that should not be reformatted. A typical baseline:

```text
node_modules/
package-lock.json
dist/
build/
coverage/
.venv/
```

Adopters SHOULD review their repository for additional generated or vendored content (for example, lockfiles, cached schema bundles, fixtures whose formatting is asserted by tests) and add those paths as well.

### Optional Local Pre-commit Hook

If the project already runs Prettier from `package.json` scripts, a `repo: local` pre-commit hook keeps the version under project control rather than pinning a separate Prettier mirror:

```yaml
- repo: local
  hooks:
    - id: prettier-json-check
      name: Check JSON and JSONC formatting with Prettier
      entry: npx --no-install prettier --check "**/*.{json,jsonc}" "!node_modules/**"
      language: system
      files: '\.(json|jsonc)$'
      pass_filenames: false
```

The `files:` regex scopes the hook so pre-commit only invokes it on commits that touch `.json` or `.jsonc` files; without that filter, `pass_filenames: false` would cause the hook to run (and re-scan the repo's JSON/JSONC globs) on every commit. `pass_filenames: false` lets the glob in `entry:` decide which files Prettier inspects, which keeps the hook consistent with the `lint:json:format` script. The `--no-install` flag tells `npx` to fail rather than fetch an unpinned Prettier on demand, so the hook always uses the version recorded in `package.json` / `package-lock.json`.

> **Node availability requirement.** Because this hook shells out to `npx`, every environment that runs `pre-commit` MUST have Node.js installed and the project's npm dependencies installed (typically via `npm ci`). The template's default CI workflows do not install Node, so adopters who add this hook MUST also add a Node setup step (for example, `actions/setup-node` followed by `npm ci`) to any workflow that runs `pre-commit run --all-files`, and ensure the same is true on contributor workstations.

<!-- -->

> **`pre-commit/mirrors-prettier` is not the recommended path.** The `pre-commit/mirrors-prettier` repository pins a Prettier version separately from the project's `package.json`, which creates two sources of truth for the Prettier version. Prefer the `repo: local` hook above so that `package.json`, CI scripts, and the pre-commit hook all use the same Prettier version.

### YAML

Prettier for YAML is **discouraged by default** in this template. Prettier's YAML output diverges from idiomatic `yamllint` defaults (line wrapping, flow vs. block style, quoting), and running both without explicit reconciliation produces churn-only diffs.

If a project chooses to adopt Prettier for YAML anyway, it MUST reconcile `yamllint` and Prettier so they do not fight. At minimum:

- Pin both tools.
- Adjust `.yamllint.yml` rules (for example, `line-length`, `quoted-strings`, `indentation`) to match Prettier's output, or configure Prettier to match `.yamllint.yml`.
- Run both tools on a representative sample and confirm a clean pass before enabling either in CI.

### Docker Alternative

Projects that do not want a local Node.js installation MAY run Prettier from a Docker image in CI (for example, the official `node:` images or community-maintained Prettier images). The `package.json` scripts and the `.prettierrc.json` configuration above remain unchanged; only the invocation differs. Local developers can still use `npx prettier` if they have Node available, or rely on CI to enforce formatting.

### Editor Formatter Guidance

The template's `.vscode/settings.json` only prescribes the PowerShell file encoding (see [VS Code PowerShell File Encoding for Non-ASCII Characters](#vs-code-powershell-file-encoding-for-non-ascii-characters)) and does **not** prescribe editor formatters for any language. Editor-formatter guidance for JSON, JSONC, and YAML is therefore intentionally omitted here; downstream consumers who adopt Prettier MAY add `[json]`, `[jsonc]`, and `[yaml]` formatter sections to their own `.vscode/settings.json` at their discretion.

---

## JSONC Validation (Opt-in)

**Files:** `.pre-commit-config.yaml`, JSONC-aware tooling of your choice

The default `check-json` pre-commit hook is anchored with `files: \.json$`, so it deliberately does **not** validate `.jsonc` files. JSONC (JSON with comments) is a superset that strict JSON parsers reject, so `check-json` would mis-flag every JSONC file with comments or trailing commas as a syntax error.

**Recommendation:** Repositories with load-bearing JSONC files (for example, configuration that downstream tools read with a JSONC-aware parser) SHOULD adopt **JSONC-aware tooling** rather than retrofitting `check-json` to accept JSONC. Candidate approaches include:

- A JSONC-aware parser invoked from a `repo: local` pre-commit hook (for example, a small Python or Node.js script that uses a JSONC parser library).
- A JSONC-aware schema validator if the JSONC files are also schema-backed.
- Prettier with a JSONC parser (see [Prettier for JSON/JSONC (Opt-in)](#prettier-for-jsonjsonc-opt-in)) for formatting only — Prettier does not enforce strict syntax in the same way `check-json` does.

**Why the default `check-json` regex is anchored.** The anchored regex is intentional and reflects an explicit design decision: `.json` and `.jsonc` are different dialects with different parsers, and validating both with the same strict-JSON tool would produce false positives on every JSONC comment or trailing comma. Retrofitting `check-json` is therefore **not** the recommended path; add separate JSONC-aware tooling instead.

---

## JSON5 Support (Opt-in)

**Files:** `.pre-commit-config.yaml`, JSON5-aware tooling of your choice

JSON5 is **not** enabled by default in this template. The JSON authoring guide ([`.github/instructions/json.instructions.md`](.github/instructions/json.instructions.md)) intentionally omits `.json5`, and no pre-commit hook validates JSON5 syntax out of the box.

**Recommendation:** Adopting JSON5 SHOULD be an explicit, documented project decision rather than an implicit drift from JSON. If a downstream project adopts JSON5:

- Document the decision (which directories, which consumers, why JSON5 over strict JSON or JSONC).
- Add a JSON5-aware parser or validator (for example, a `repo: local` hook that uses a JSON5 parser library).
- Confirm that all consumers of the JSON5 files actually support JSON5 syntax — many tools that accept "loose JSON" only accept JSONC, not full JSON5.

See the [JSON5 exclusion ADR in `.github/TEMPLATE_DESIGN_DECISIONS.md`](.github/TEMPLATE_DESIGN_DECISIONS.md#design-decision-json5-exclusion-by-default) for the rationale behind keeping JSON5 out of the default toolchain.

---

## Ecosystem-Specific YAML Validators (Opt-in)

**Files:** `.pre-commit-config.yaml`, `.github/workflows/*.yml`, ecosystem-specific configuration files

The default YAML toolchain (`check-yaml`, `yamllint`, `actionlint`) covers syntax, style, and GitHub Actions workflow correctness. Ecosystem-specific validators add semantic checks for particular YAML dialects and SHOULD be adopted **only when the repository actually uses those ecosystems** — adding a validator for a stack the project does not use creates noise without enforcing anything useful.

| Ecosystem | Recommended Validator | Notes |
| --- | --- | --- |
| Kubernetes manifests | [`kubeconform`](https://github.com/yannh/kubeconform) (or equivalent, e.g. `kubeval`, `kubectl --dry-run`) | Validates manifest schemas against the relevant Kubernetes API version. |
| OpenAPI / AsyncAPI | [`spectral`](https://github.com/stoplightio/spectral) | Lints API contracts against built-in or custom rulesets. |
| AWS CloudFormation | [`cfn-lint`](https://github.com/aws-cloudformation/cfn-lint) | Validates CloudFormation templates against AWS resource specifications. |
| Ansible playbooks/roles | [`ansible-lint`](https://github.com/ansible/ansible-lint) | Enforces Ansible best practices and detects common errors. |
| Helm charts | [`helm lint`](https://helm.sh/docs/helm/helm_lint/) (and optionally `kubeconform` post-render) | Validates chart structure and renders templates for further validation. |

Adopters MAY add these as additional pre-commit hooks (or as separate CI jobs) when their repository contains the relevant file types. Do **not** add them speculatively.

---

## Future SchemaStore Validation for Repository Configuration Files

**Status:** Future work — not enabled by default.

Several common repository configuration files have public schemas published on [SchemaStore](https://www.schemastore.org/) or maintained by their respective ecosystems. Wiring schema validation for any of them is **explicitly out of scope** for the worked example shipped under `schemas/`; it requires an explicit downstream project decision.

Candidate files (cross-referenced from the [Future Work section in `schemas/README.md`](schemas/README.md#future-work)):

- **`package.json`** — schema available on SchemaStore. A downstream project MAY add a `check-jsonschema` hook scoped to `^package\.json$` that points at the SchemaStore-published schema (for example, via `check-jsonschema`'s built-in `vendor.package-json` schema selector if available). Useful when `package.json` carries non-trivial metadata that should be validated beyond basic JSON syntax.
- **Generated package-manager lockfiles** (for example, `package-lock.json`, `yarn.lock` in JSON form, `composer.lock`) — schema validation MAY be useful, but only if it does **not** conflict with the package manager's own validation. Most package managers already validate their lockfiles internally; an additional schema check is justified only when a stable schema-backed validation path adds value the package manager does not already provide.
- **`.github/dependabot.yml`** — schema available on SchemaStore. A downstream project MAY add a `check-jsonschema` hook scoped to `^\.github/dependabot\.yml$` that points at the SchemaStore-published Dependabot schema. Note that Dependabot itself enforces its schema at evaluation time, so this is primarily a fast local feedback loop.
- **GitHub Actions workflow files** — already covered by `actionlint`. An additional `check-jsonschema` hook against the SchemaStore Actions schema would be **redundant** with `actionlint` and is **not recommended**.

For all of the above, follow the schema-validation guidance in [Schema Validation Configuration](#schema-validation-configuration): add **one `check-jsonschema` hook per real schema-backed file family**, scoped to the files that family covers, and keep the default toolchain free of placeholder hooks. See the [Future Work section in `schemas/README.md`](schemas/README.md#future-work) for additional context and avoid restating that future-work note here.

---

## Removing the Worked Example Schema

**Files:** `schemas/`, `.pre-commit-config.yaml`, `tests/test_schema_examples.py`, `.github/workflows/data-ci.yml`, related documentation

The template ships a worked-example schema (`schemas/example-config.schema.json`), valid and invalid example fixtures under `schemas/examples/example-config/`, two pre-commit hooks (`check-jsonschema` for valid examples, `check-metaschema` for the schema itself), and the schema-example pytest contract at [`tests/test_schema_examples.py`](tests/test_schema_examples.py). The worked example is intentionally easy to remove for downstream repositories that do not use schema-backed validation.

**To remove the worked example, follow the canonical [Downstream Removal Checklist](schemas/README.md#downstream-removal-checklist) in `schemas/README.md`.** That checklist is the single source of truth for the exact files, hooks, and references to remove; do not improvise the steps from memory and do not duplicate the checklist here.

---

## Markdown Linting Configuration

**File:** `.markdownlint.jsonc`

### Customizing Style Rules

The following rules can be configured to match your project's documentation style:

| Rule | Description | Default | Options |
| --- | --- | --- | --- |
| MD003 | Heading style | `atx` | `atx`, `setext`, `consistent` |
| MD004 | Unordered list marker | `dash` | `dash`, `asterisk`, `plus`, `consistent` |
| MD012 | Maximum consecutive blank lines | `2` | Any positive integer |
| MD024 | Multiple headings with same content | `siblings_only: true` | `true`, `false`, or object with `siblings_only` |
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

**Example: Allowing up to 3 consecutive blank lines:**

```jsonc
{
  "MD012": {
    "maximum": 3
  }
}
```

**Example: Disallowing duplicate headings entirely:**

```jsonc
{
  "MD024": {
    "siblings_only": false
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

### Using the cli2-Specific Configuration Format

The repository includes an alternative configuration template at `templates/markdown/.markdownlint-cli2.jsonc` that uses the `markdownlint-cli2` specific format where rules are nested under a `"config"` key.

#### When to Use Each Format

| File | Format | Use Case |
| --- | --- | --- |
| `.markdownlint.jsonc` | Standard (rules at root) | Default choice; works with both `markdownlint-cli` and `markdownlint-cli2` |
| `.markdownlint-cli2.jsonc` | cli2-specific (rules under `"config"`) | When you need cli2-specific features like `globs`, `ignores`, `customRules`, or `frontMatter` parser options |

Both files contain **identical linting rules**; only the structure differs.

#### Switching to the cli2-Specific Format

If you want to use the cli2-specific format, copy the template to your repository root and remove the original configuration file.

**Windows (PowerShell):**

```powershell
Copy-Item -Path "templates/markdown/.markdownlint-cli2.jsonc" -Destination ".markdownlint-cli2.jsonc"
Remove-Item -Path ".markdownlint.jsonc" -Force
```

**macOS/Linux/FreeBSD:**

```bash
cp templates/markdown/.markdownlint-cli2.jsonc .markdownlint-cli2.jsonc
rm .markdownlint.jsonc
```

> **Note:** When using `.markdownlint-cli2.jsonc`, any rule customizations must be made inside the `"config"` block, not at the root level of the JSON.

**See also:** [markdownlint-cli2 documentation](https://github.com/DavidAnson/markdownlint-cli2) for additional cli2-specific configuration options.

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
    - id: ruff-check
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

> **Note:** If requiring strict type checking, ensure your CI workflow (`.github/workflows/python-ci.yml`) runs mypy without `continue-on-error: true`. See [CI Workflow Configuration](#ci-workflow-configuration) for details.

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

## Copilot Terraform Instructions Configuration

**File:** `.github/instructions/terraform.instructions.md`

The `terraform.instructions.md` file provides Terraform coding standards that GitHub Copilot applies when generating or editing `.tf`, `.tfvars`, `.tftest.hcl`, `.tf.json`, `.tftpl`, and `.tfbackend` files in your repository. These standards cover style, formatting, naming conventions, file organization, variable and output design, resource configuration, module design, state management, security best practices, provider management, testing, and documentation requirements.

### Adopting for Terraform Projects

When adopting this template for a Terraform project, complete the following tasks:

1. **Update the metadata** at the top of the file to reflect your project's ownership and versioning
2. **Review and adjust backend configuration** guidance for your project needs (S3, Azure Storage, GCS, Terraform Cloud, etc.)
3. **Verify required provider versions** and update the version constraint examples as needed
4. **Add organization-specific required tags** to the Required Tags section if your organization mandates specific tags
5. **Document any justified deviations** in the "Scope Exceptions & Deviations from Standards" section at the end of the file
6. **Remove non-relevant provider examples** — The file includes parallel examples for AWS, Azure, and GCP. Delete examples for providers your project does not use to reduce noise and confusion. Search for "AWS Example", "Azure Example", "GCP Example", and combined labels like "AWS/Azure Example" to identify provider-specific blocks.
7. **Replace all `REPLACE_ME_*` placeholders** with your organization's actual values. Run `grep -r "REPLACE_ME"` to find all placeholders requiring customization.

### Customizing Provider Examples

The file now includes parallel examples for AWS, Azure, and GCP throughout. Each example group is clearly labeled with "AWS Example", "Azure Example", "GCP Example", or combined labels like "AWS/Azure Example" (used when providers share the same pattern). To customize for your cloud provider:

1. **For single-provider projects:** Remove examples for providers you don't use. Search for the provider labels (e.g., "Azure Example", "GCP Example") and delete those code blocks and their headers.

2. **For multi-cloud projects:** Keep all examples or remove only those that don't apply to your specific environments.

3. **For all projects:** Replace `REPLACE_ME_*` placeholders with your organization's actual values. See the "Placeholder Convention (`REPLACE_ME_*`)" section in `.github/instructions/terraform.instructions.md` for the complete list of standard placeholders.

### Customizing for Terraform Cloud/Enterprise

If your organization uses Terraform Cloud, Terraform Enterprise, Spacelift, or similar tools:

1. **Update the State Management section** to reflect your workflow. The `backend.tf` file may not be applicable.

2. **Add cloud block configuration** guidance as the primary example:

   ```hcl
   terraform {
     cloud {
       organization = "REPLACE_ME_ORG"
       workspaces {
         name = "REPLACE_ME_WORKSPACE"
       }
     }
   }
   ```

3. **Document which sections do not apply** in the Scope Exceptions section. For example:
   - Manual `backend.tf` configuration
   - DynamoDB lock table configuration
   - S3/GCS/Azure Storage bucket configuration for state

### Customizing Required Tags

The Required Tags section lists mandatory tags for all taggable resources. To customize for your organization:

1. **Add organization-specific tags:**

   ```markdown
   | Tag | Description | Example |
   | --- | --- | --- |
   | `CostCenter` | Budget/billing code | `CC-12345` |
   | `Department` | Owning department | `Engineering` |
   | `Compliance` | Compliance framework | `SOC2`, `HIPAA` |
   ```

2. **Remove tags that don't apply** to your organization

3. **Update the Default Tags Configuration** example to reflect your required tags

### Scope Exceptions Section

The file includes a "Scope Exceptions & Deviations from Standards" section at the end for documenting justified deviations. Use this section to record:

- **Alternative backend workflows:** Using Terraform Cloud instead of `backend.tf`
- **Provider-specific requirements:** Organization policies that mandate specific provider configurations
- **Legacy compatibility:** Maintaining compatibility with older Terraform versions or modules
- **Organizational naming conventions:** Pre-existing naming conventions that differ from the template
- **Security policy overrides:** Stricter security requirements that go beyond the template defaults

---

## Copilot Main Instructions Configuration

**File:** `.github/copilot-instructions.md`

The main `.github/copilot-instructions.md` file provides repository-wide instructions that GitHub Copilot applies when generating or editing code. It includes sections on pre-commit discipline, testing tools, and other project-wide standards. These sections should be customized to match your project's actual tools and workflows.

### Customizing the Pre-commit Discipline Section

The Pre-commit Discipline section (near the top of `.github/copilot-instructions.md`) tells Copilot how to run pre-commit checks, what commands to use, and how to handle CI failures. This ensures Copilot generates code that follows your project's code quality workflow.

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

The Testing Tools section (near the bottom of `.github/copilot-instructions.md`) tells Copilot what test frameworks your project uses, where tests are located, and how to run them. This ensures Copilot generates tests that match your project's conventions.

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

When customizing the Pre-commit or Testing sections, you may also need to update these related sections in `.github/copilot-instructions.md`:

- **How to Work (Definition of Done):** Update test location references (e.g., `tests/` to `spec/`)
- **Modular Instructions table:** Ensure it matches your instruction files
- **Linting Configurations:** Update linting tool references if you use different linters

---

## Customizing Agent Instruction Files

**Files:** `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`

The template includes three agent instruction files at the repository root. `.github/copilot-instructions.md` remains the canonical source of truth, while these files act as thin entry points that keep a minimal inline summary of the highest-priority shared rules plus any platform-specific guidance. Each file targets a specific AI coding platform:

| File | Target Agent(s) |
| --- | --- |
| `CLAUDE.md` | Claude Code, GitHub Copilot coding agent |
| `AGENTS.md` | OpenAI Codex CLI, GitHub Copilot coding agent |
| `GEMINI.md` | Gemini Code Assist, GitHub Copilot coding agent |

### Removing Unneeded Files

Delete agent files for platforms you do not use. For example, if your team does not use Claude Code, delete `CLAUDE.md`. If your team does not use OpenAI Codex CLI, delete `AGENTS.md`. Removing unused files reduces maintenance burden without affecting other platforms.

### Keeping Minimal Summaries Aligned

When high-priority shared guidance changes in `.github/copilot-instructions.md`, update the minimal summaries in any remaining agent files as needed. Common changes that require alignment include:

- **Language table updates** — Adding or removing languages
- **Linting tool changes** — Different linting commands or configurations
- **Test command changes** — Different test frameworks or commands
- **Build and test commands** — Updated pre-commit or CI commands
- **Canonical-file guidance** — Changes to how agents should locate or interpret the canonical instructions

> **Note:** No CI enforcement exists for agent-file alignment. Review the remaining agent files whenever you update `.github/copilot-instructions.md` so their minimal summaries stay accurate without regrowing into full duplicates.

### Adding Platform-Specific Notes

If an agent has unique behavioral requirements (e.g., different command syntax, specific tool limitations, or platform-specific workarounds), add agent-specific sections to the appropriate file. Platform-specific notes should supplement, not contradict, the canonical rules in `.github/copilot-instructions.md`.

---

## CI Workflow Configuration

**File:** `.github/workflows/python-ci.yml`

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

> **Note:** Removing this workflow is safe—the standard `python-ci.yml` workflow will still run pre-commit checks and report any issues that need to be fixed.

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

1. **powershell-lint** (display name: "Lint (PSScriptAnalyzer)"): Runs PSScriptAnalyzer on all `.ps1` files (skips if no files found)
2. **test** (display name: "PowerShell Tests (Pester)"): Runs Pester tests on Windows, macOS, and Linux (skips if no `*.Tests.ps1` files found)

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

## Using the Python Template Files

**Directory:** `templates/python/`

This template repository includes reference Python configuration files and scaffolding for projects adopting Python tooling. These files demonstrate how to configure Python tooling to align with the coding standards defined in [`.github/instructions/python.instructions.md`](.github/instructions/python.instructions.md).

### Files Included

- **`pyproject.toml`**: Sample configuration for Python project metadata, dependencies, and tooling (Black, Ruff, mypy, pytest)
- **`tests/__init__.py`**: Package marker for the test directory
- **`tests/test_placeholder.py`**: Placeholder test file that demonstrates pytest test structure
- **`tests/test_schema_examples.py`**: Starter pytest module that auto-discovers and validates schema example fixtures under `schemas/examples/<name>/{valid,invalid}/` with `check-jsonschema`. Skips cleanly when the tool is not installed or when no examples are present. Mirrors the active, canonical test at `tests/test_schema_examples.py` in the template repository root. See [Schema Validation Configuration](#schema-validation-configuration) for setup.
- **`README.md`**: Brief overview of the template files with links to external resources

### How to Use the Template

1. **Copy files to your project root** (or appropriate location based on your layout):

   **Windows (PowerShell):**

   ```powershell
   Copy-Item -Path "templates/python/pyproject.toml" -Destination "pyproject.toml"
   Copy-Item -Path "templates/python/tests" -Destination "tests" -Recurse
   ```

   **macOS/Linux/FreeBSD:**

   ```bash
   cp templates/python/pyproject.toml pyproject.toml
   cp -r templates/python/tests tests
   ```

2. **Customize `pyproject.toml`**:
   - Update the `[project]` section with your project's name, version, description, and authors
   - Add your runtime dependencies to the `dependencies = []` list
   - Adjust development dependencies as needed
   - Update the `classifiers` list to reflect your project's maturity and supported Python versions (see below)

3. **Create your source code** in either a flat layout (modules in project root) or `src/` layout (modules in `src/your_package/`). See the [Project Layout Options](#project-layout-options) section below for detailed layout options and directory structure examples.

4. **Replace or delete `tests/test_placeholder.py`** once you have actual tests in place.

### About the Placeholder File

The file `templates/python/tests/test_placeholder.py` is a minimal placeholder that demonstrates pytest test structure. It contains a single test that always passes:

```python
"""Placeholder test file for template demonstration.

This is a template file. Delete or overwrite this with your actual tests.
"""


def test_placeholder():
    """Simple placeholder test that always passes.

    Replace this with your actual test cases.
    """
    assert True
```

When you add real tests for your project:

1. Create test files following the `test_*.py` naming convention
2. Delete `test_placeholder.py` once you have real tests in place
3. See the [Python Version Configuration](#python-version-configuration) and [mypy Path Configuration](#mypy-path-configuration) sections below for additional configuration details

### Customizing Classifiers

The `classifiers` field in `pyproject.toml` provides metadata for PyPI and other tools. Update these values to match your project:

**Development Status:** Change based on project maturity:

```toml
# Alpha - early development, unstable API
"Development Status :: 3 - Alpha"

# Beta - feature complete, may have bugs
"Development Status :: 4 - Beta"

# Production/Stable - ready for production use
"Development Status :: 5 - Production/Stable"
```

**Python Version Classifiers:** Update when your minimum Python version changes:

```toml
classifiers = [
    "Development Status :: 4 - Beta",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
]
```

> **Note:** The Python version classifiers should match the versions specified in `requires-python` and your CI test matrix. See [PyPI Classifiers](https://pypi.org/classifiers/) for the full list of available classifiers.

### When to Use These Templates

Use the Python template files when:

- **Starting a new Python project from scratch**: These templates provide clean configuration files that you can customize for your project
- **Adding Python to an existing repository**: If your repository doesn't have Python tooling configured, these templates provide a complete starting point

### Project Layout Options

#### Option 1: Flat Layout

Place your Python modules directly in the project root:

```text
your-project/
├── pyproject.toml
├── your_module.py
├── another_module.py
└── tests/
    └── test_your_module.py
```

For mypy in CI, use:

```yaml
env:
  MYPY_PATHS: "."
```

#### Option 2: src/ Layout (Recommended)

Place your Python package(s) in a `src/` directory:

```text
your-project/
├── pyproject.toml
├── src/
│   └── your_package/
│       ├── __init__.py
│       └── module.py
└── tests/
    └── test_module.py
```

For mypy in CI, use:

```yaml
env:
  MYPY_PATHS: "src/ tests/"
```

The `src/` layout is recommended because it:

- Prevents accidental imports of uninstalled code during development
- Makes it clear what code is part of the package vs. project tooling
- Aligns with modern Python packaging best practices

### Python Version Configuration

Different Python tools require different version format specifications. When updating the minimum Python version, you must update **all three** of these settings:

#### 1. Project Metadata: `requires-python`

```toml
[project]
requires-python = ">=3.13"  # PEP 621 standard: ">=" operator with dotted version
```

#### 2. Black Configuration: `target-version`

```toml
[tool.black]
target-version = ["py313"]  # List of strings in "pyXYZ" format
```

#### 3. mypy Configuration: `python_version`

```toml
[tool.mypy]
python_version = "3.13"  # Dotted version string (no ">=" operator)
```

#### 4. Ruff Configuration: `target-version` (Optional)

```toml
[tool.ruff]
# Ruff automatically infers target-version from [project].requires-python
# Only set this if you need to override:
# target-version = "py313"  # Single string in "pyXYZ" format (not a list)
```

**Important:** If you set `[project].requires-python`, Ruff will automatically use that value. Setting `[tool.ruff].target-version` explicitly will override the inferred value.

### Python Version Support Policy

**Always use a Python version that is currently receiving bugfixes.**

- Python versions in "security fix only" phase are **not publicly installable** with security updates—they require building from source with manually applied patches.
- Check the [Python Developer's Guide - Versions](https://devguide.python.org/versions/) page for current version status.

> **Template adopters:** The template defaults to Python 3.13+. Customize the `requires-python` field in `pyproject.toml` based on your project's specific requirements.

**When to update:**

- Check the [Python Developer's Guide - Versions](https://devguide.python.org/versions/) page annually (typically around October when new Python versions are released)
- Update all version references in `pyproject.toml` when the minimum supported version changes
- Update the CI workflow's Python version matrix in `.github/workflows/python-ci.yml`

### mypy Path Configuration

The CI workflow (`.github/workflows/python-ci.yml`) uses the `MYPY_PATHS` environment variable to specify which directories/files mypy should check.

**Default (for src/ layout):**

```yaml
env:
  MYPY_PATHS: "src/ tests/"
```

**For flat layout:**

```yaml
env:
  MYPY_PATHS: "."
```

**For custom directories:**

```yaml
env:
  MYPY_PATHS: "foo/ bar/ baz.py"
```

The command-line paths override any `files` or `exclude` settings in `pyproject.toml` or `mypy.ini` in terms of directory scope. However, per-file configuration options in those files still apply to the files that mypy discovers.

---

## Using the Pester Test Template

**File:** `templates/powershell/Example.Tests.ps1`

This template repository includes a comprehensive Pester 5.x test template that demonstrates common testing patterns. Use this template as a starting point when creating tests for your PowerShell functions.

### What the Template Demonstrates

The template file includes working examples of:

- **BeforeAll/BeforeEach** for test setup and dot-sourcing functions
- **Describe/Context/It** block structure for organizing tests
- **Arrange-Act-Assert (AAA)** pattern for clear test organization
- **Testing integer return codes** (0=success, -1=failure) for v1.0-style functions
- **Testing reference parameters** (`[ref]`) for functions that return data via references
- **Testing boolean returns** for `Test-*` functions
- **Basic mocking** with the `Mock` command to isolate tests from external dependencies

### How to Use the Template

1. **Copy the template file** to your tests directory:

   **Windows (PowerShell):**

   ```powershell
   Copy-Item "templates/powershell/Example.Tests.ps1" "tests/PowerShell/MyFunction.Tests.ps1"
   ```

   **macOS/Linux/FreeBSD:**

   ```bash
   cp templates/powershell/Example.Tests.ps1 tests/PowerShell/MyFunction.Tests.ps1
   ```

2. **Remove the inline example functions** from the `BeforeAll` block. These are demonstration functions (`Get-ExampleGreeting`, `Test-IsValidEmail`, `Get-ProcessedData`) that exist only to make the template runnable as-is.

3. **Uncomment and update the dot-source line** to import your actual function file:

   ```powershell
   BeforeAll {
       # Update this path to your actual function file
       . $PSScriptRoot/../../src/MyFunction.ps1
   }
   ```

4. **Replace the example `Describe` blocks** with tests for your actual functions, following the patterns demonstrated for your specific return types.

### Running the Template Tests

You can run the template file directly to see the test patterns in action:

```powershell
Invoke-Pester -Path templates/powershell/Example.Tests.ps1 -Output Detailed
```

### About the Placeholder File

The file `tests/PowerShell/Placeholder.Tests.ps1` is a minimal placeholder that exists to ensure the PowerShell CI workflow passes with a valid test file. When you add real tests for your project:

1. Copy the template file as described above
2. Customize it for your functions
3. Delete `Placeholder.Tests.ps1` once you have real tests in place

The template file provides much more comprehensive examples than the placeholder and should be your primary reference when writing Pester tests.

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

## Gitignore Configuration

**File:** `.gitignore`

The default `.gitignore` file includes standard exclusion patterns for Node.js, Python, pre-commit, OS-generated files, and IDE configurations. Most projects can use it without modification.

### Excluding Lock Files

The `.gitignore` includes a commented-out option to exclude `package-lock.json`:

```text
# Lock files (optional - uncomment to exclude)
# package-lock.json
```

**To exclude lock files from version control:**

Uncomment the `package-lock.json` line:

```text
# Lock files (optional - uncomment to exclude)
package-lock.json
```

> **Note:** Most projects should keep `package-lock.json` committed to ensure reproducible builds. Only exclude it if you have a specific reason, such as always wanting fresh dependency resolution during installs.

### Adding Project-Specific Exclusions

To add custom exclusion patterns for your project:

1. Open `.gitignore` in your editor
2. Add your patterns at the end of the file
3. Use comments to explain non-obvious exclusions

**Example:**

```text
# Project-specific exclusions
data/
*.log
secrets/
```

---

## License Customization

**File:** `LICENSE` (and related files)

This template uses the MIT License by default. If your project requires different license terms, you will need to update multiple files to ensure consistency.

### Files That Reference the License

When changing your project's license, update all of the following files:

| File | What to Update |
| --- | --- |
| `LICENSE` | Replace entire file with your license text |
| `CONTRIBUTING.md` | Update the "License" section |
| `README.md` | Update the "License" section (near bottom of file) |
| `pyproject.toml` | Update `license = "MIT"` in `[project]` section |
| `package.json` | Update `"license": "MIT"` field |
| `templates/python/pyproject.toml` | Update `license = "MIT"` (only if keeping the templates directory) |

> **Note:** The `package-lock.json` file contains `"license": "MIT"` entries, but these refer to the licenses of npm dependencies (not your project). These do NOT need to be changed when updating your project's license.

### Keeping MIT License (Default)

No changes required. The MIT License is suitable for most open source projects where you want to allow maximum reuse with minimal restrictions.

### Changing to Apache 2.0

Replace MIT with Apache 2.0 if you need explicit patent protection.

**Step 1:** Replace the `LICENSE` file content with the Apache 2.0 license text from [apache.org](https://www.apache.org/licenses/LICENSE-2.0.txt).

**Step 2:** Update all references:

```markdown
<!-- In CONTRIBUTING.md -->
By contributing to this project, you agree that your contributions will be licensed
under the same license as the project (Apache License 2.0).
```

```markdown
<!-- In README.md -->
Apache License 2.0 - See [LICENSE](LICENSE) for details.
```

```toml
# In pyproject.toml and templates/python/pyproject.toml
license = "Apache-2.0"
```

```json
// In package.json
"license": "Apache-2.0"
```

### Changing to a Proprietary License

For closed-source or commercial projects, replace the MIT License with appropriate proprietary terms.

**Step 1:** Replace the `LICENSE` file with your proprietary license text.

**Step 2:** Update `CONTRIBUTING.md` to reflect contribution terms (replace `{{COMPANY}}` with your company name):

```markdown
## License

This project is proprietary software. By contributing to this project, you agree that:

1. Your contributions become the property of {{COMPANY}}
2. You have the right to make the contribution
3. You grant {{COMPANY}} all rights to use your contribution

Contributors may be required to sign a Contributor License Agreement (CLA) before
contributions can be accepted.
```

**Step 3:** Update `README.md` (replace `{{YEAR}}` with the copyright year or range, e.g., `2024` or `2020-2024`):

```markdown
## License

Proprietary - Copyright {{YEAR}} {{COMPANY}}. All rights reserved.
See [LICENSE](LICENSE) for details.
```

**Step 4:** Update package manifests:

```toml
# In pyproject.toml
license = "Proprietary"
```

```json
// In package.json - choose based on your situation:
// Use "UNLICENSED" for internal/private projects with no license granted:
"license": "UNLICENSED"
// Use "SEE LICENSE IN LICENSE" when you have a custom license file:
"license": "SEE LICENSE IN LICENSE"
```

**Additional considerations:**

- Consider requiring Contributor License Agreements (CLAs) for external contributions
- Ensure employment contracts or contributor agreements assign intellectual property rights appropriately
- Review all open source dependencies to ensure their licenses are compatible with proprietary use
- Have legal counsel review your license terms before public or customer distribution

### Other Open Source Licenses

For licenses not covered above (BSD, GPL, LGPL, MPL, etc.), follow the same pattern:

1. Replace `LICENSE` file with the full license text
2. Update `CONTRIBUTING.md` contributor agreement
3. Update `README.md` license section
4. Update `pyproject.toml` with the appropriate SPDX identifier
5. Update `package.json` with the appropriate SPDX identifier

**Common SPDX identifiers:**

| License | SPDX Identifier |
| --- | --- |
| MIT | `MIT` |
| Apache 2.0 | `Apache-2.0` |
| BSD 2-Clause | `BSD-2-Clause` |
| BSD 3-Clause | `BSD-3-Clause` |
| GPL 3.0 | `GPL-3.0-only` |
| LGPL 3.0 | `LGPL-3.0-only` |
| MPL 2.0 | `MPL-2.0` |
| ISC | `ISC` |

For the complete list of SPDX identifiers, see [spdx.org/licenses](https://spdx.org/licenses/).

### Dual Licensing

Some projects offer multiple license options (e.g., GPL for open source use, commercial license for proprietary use). If dual licensing:

1. Include both license texts in `LICENSE` (or separate files like `LICENSE-MIT` and `LICENSE-APACHE`)
2. Clearly explain the licensing options in `README.md`
3. Document which license applies under which conditions

---

## VS Code PowerShell File Encoding for Non-ASCII Characters

**File:** `.vscode/settings.json`

The template ships with this default encoding for PowerShell files:

```json
{
    "[powershell]": {
        "files.encoding": "utf8"
    }
}
```

This is the correct default for the common case and should be kept when:

- Your `.ps1` files contain **only ASCII characters**, or
- Your repository targets **PowerShell 7+ only** (which defaults to UTF-8).

### When to Change the Encoding

If your repository's PowerShell `.ps1` files:

- contain **non-ASCII characters** (for example, accented characters, CJK text, or special symbols in strings or comments), **and**
- must run on **Windows PowerShell** (v5.1 or earlier),

then you should change the VS Code workspace encoding setting for PowerShell files to UTF-8 **with** BOM.

### What to Change

In `.vscode/settings.json`, replace the `files.encoding` value for PowerShell files:

```json
{
    "[powershell]": {
        "files.encoding": "utf8bom"
    }
}
```

`utf8bom` is VS Code's identifier for UTF-8 with BOM (Byte Order Mark, `U+FEFF`).

### Why This May Be Necessary

When a `.ps1` file is saved as UTF-8 **without** a BOM, older Windows PowerShell versions may not detect the encoding correctly. Instead, they may interpret the file using the system's ANSI code page, which can cause non-ASCII characters in strings, comments, or variable content to be read incorrectly.

Adding a BOM lets Windows PowerShell detect that the file is UTF-8 and interpret it correctly. PowerShell 7+ defaults to UTF-8 regardless of BOM, so the BOM is unnecessary (but harmless) on modern PowerShell.

### Down-Level Compatibility Note

For very old Windows PowerShell compatibility scenarios, the safest portable strategy is often to **avoid non-ASCII source text entirely** when practical. If all characters in the script are ASCII, the file is interpreted identically regardless of whether the system reads it as UTF-8 or as ANSI, making the BOM question moot.

Relying on "ANSI" or locale-specific encodings (for example, Windows-1252 or Shift_JIS) is generally **not recommended** because those encodings are non-portable and brittle across systems with different locale settings.

> **Reference:** The full encoding rules are defined in the `### File Encoding` subsection of `.github/instructions/powershell.instructions.md`.

---

## Ongoing Maintenance

These are periodic maintenance tasks for repositories created from the template.

### Updating Pre-commit Hooks

Pre-commit hooks should be kept up-to-date for security and compatibility:

```bash
# Check for and apply updates to pre-commit hooks
pre-commit autoupdate

# Test that updated hooks work correctly
pre-commit run --all-files

# Commit the updated configuration
git add .pre-commit-config.yaml
git commit -m "chore: update pre-commit hooks"
```

**Frequency:** Monthly or when security advisories are published for hook dependencies (Black, Ruff, etc.).

### Reviewing Python Version Requirements

If your project uses Python, periodically review your minimum Python version requirement:

1. Visit the [Python Developer's Guide - Versions](https://devguide.python.org/versions/) page
2. Check which versions are in "bugfix" status
3. Update `pyproject.toml` `requires-python` field if needed
4. Update CI workflow Python version matrix if needed

---

## Additional Resources

- **[Creating a New Repository](GETTING_STARTED_NEW_REPO.md)**: Complete setup guide for new repositories
- **[Adding Template Features to an Existing Repository](GETTING_STARTED_EXISTING_REPO.md)**: Adoption guide for existing repositories
- **[Design Decisions](.github/TEMPLATE_DESIGN_DECISIONS.md)**: Rationale behind template design choices (for maintainers and code reviewers)

> **Note:** The Design Decisions document (`.github/TEMPLATE_DESIGN_DECISIONS.md`) is internal documentation for understanding WHY the template was designed a certain way. It is NOT an instruction guide—use the getting started guides above for setup instructions.
