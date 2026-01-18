# Template Guide

<!--
FILE PLACEMENT RATIONALE:
This file is placed in .github/ because it is GitHub-specific configuration guidance
that relates directly to other files in this directory (pull_request_template.md,
ISSUE_TEMPLATE/, workflows/, etc.). Keeping it here makes it discoverable alongside
the files it documents and ensures template users encounter it when exploring GitHub
configuration. This is preferable to docs/ (general project documentation) or the
repo root (which should remain clean for end users).
-->

## About This Guide

This file provides detailed customization instructions for GitHub-specific files
included in this repository template. It is placed in `.github/` because it
relates directly to other files in this directory (templates, workflows, etc.).

**This file should be DELETED after completing template adoption.**

### Documentation Strategy

This template uses a dual-documentation approach:

1. **`README.md`**: High-level adoption checklist (what to do)
2. **`.github/TEMPLATE_GUIDE.md`**: Detailed customization instructions (how and why)

This separation ensures:

- Template adopters find detailed guidance alongside the files being customized
- Downstream repos can cleanly remove meta-content after adoption
- End-user documentation (README) stays focused on the project, not the template

---

## Final Steps

After completing all customizations described in this guide:

- [ ] Review detailed customization guidance in each section below
- [ ] **Delete `.github/TEMPLATE_GUIDE.md`** after completing all customizations
- [ ] Update `README.md` with your project-specific documentation

---

## Pull Request Template Customization

### Overview

This guide provides detailed customization instructions for the pull request template
(`.github/pull_request_template.md`) included in this repository template.

The PR template is designed for maximum portability with minimal required customization.
Most downstream repositories can use it immediately after cloning, with optional
enhancements based on project needs.

---

## Sections to Keep

The following sections are universally applicable and should be kept for all project types:

- **Description** - Every PR needs a description
- **Type of Change** - Helps reviewers understand the scope
- **Related Issues** - Links PRs to issue tracking

---

## General Checklist Customization

Review each item and modify based on your project:

### Items to Keep

- Self-review checkbox
- Documentation updates checkbox
- No new warnings checkbox
- Copilot instructions reference

### Items to Modify

**Contributing Guidelines Link:**

The template uses a relative link:

```md
[contributing guidelines](../blob/HEAD/CONTRIBUTING.md)
```

<!--
DESIGN DECISION: Contributing Guidelines Link
=============================================
This relative link has been tested and confirmed to work correctly in rendered PR views
on GitHub.com. It resolves to the repository's CONTRIBUTING.md file regardless of the
default branch name (main, master, develop, etc.) due to the use of HEAD.

We intentionally use this relative link pattern instead of an absolute URL with
OWNER/REPO placeholders for the following reasons:

1. **Clone works with minimal setup**: Template users don't need to find-and-replace
   OWNER/REPO placeholders—the link works immediately after cloning.

2. **Reduces forgotten placeholder risk**: Absolute URLs with placeholders can lead to
   broken links if users forget to replace them. The relative link pattern eliminates
   this failure mode.

3. **Tested and verified**: This link pattern is confirmed to work in GitHub.com PR views.

TRADE-OFFS:
- The relative link may not resolve correctly in PR preview/draft mode before the branch
  is pushed, or in non-GitHub contexts (local Markdown preview, email notifications, etc.).
- GitHub Enterprise Server (GHES) compatibility varies by version.

If you need the link to work in PR drafts, GHES, or external contexts, replace with:
https://github.com/OWNER/REPO/blob/HEAD/CONTRIBUTING.md
(remembering to replace OWNER/REPO with your actual org/repo name)
-->

If your `CONTRIBUTING.md` is renamed or moved (e.g., `docs/CONTRIBUTING.md`), update
the path accordingly: `../blob/HEAD/docs/CONTRIBUTING.md`

**For GitHub Enterprise Server (GHES) or external contexts**, you MAY replace with an
absolute URL:

```md
[contributing guidelines](https://github.com/OWNER/REPO/blob/HEAD/CONTRIBUTING.md)
```

Replace `OWNER/REPO` with your actual organization and repository name.

### Items to Remove

Remove items that don't apply to your project (e.g., test-related items if your
project doesn't have automated tests yet).

---

## Pre-commit Verification Section

<!--
DESIGN DECISION: Conditional Pre-commit Section
===============================================
The pre-commit section uses conditional language ("if this repository uses pre-commit")
to maintain template portability. This is intentional:

1. **Not all downstream repos use pre-commit**: Many projects use different linting/
   formatting approaches (IDE settings, CI-only checks, language-specific tools).

2. **Reduces friction**: Contributors to repos without pre-commit won't be confused
   by irrelevant instructions.

3. **Self-documenting**: The conditional phrasing makes it clear when the section
   applies.

RECOMMENDATION FOR REPOS USING PRE-COMMIT:
If your repository uses pre-commit hooks, replace the conditional section with the
more direct version shown below for clearer contributor guidance.
-->

The template includes conditional language for pre-commit:

```md
#### Pre-commit Verification (if configured)

- [ ] If this repository uses pre-commit, I ran `pre-commit run --all-files` and all checks pass
- [ ] If pre-commit made auto-fixes, I reviewed and committed them
```

**If your repository uses pre-commit hooks**, replace with the direct version:

```md
#### Pre-commit Verification

- [ ] I have run `pre-commit run --all-files` locally and all checks pass
- [ ] I have reviewed and committed all auto-fixes made by pre-commit hooks
```

**If your repository does NOT use pre-commit**, remove the section entirely.

---

## Coding Standards Reference

The template includes:

```md
My code follows the coding standards in `.github/instructions/`
```

<!--
DESIGN DECISION: .github/instructions/ Reference
=================================================
This reference assumes the .github/instructions/ directory structure will remain
as provided in this template. The assumption is that downstream repos will:

1. Keep the directory structure but ADD/REMOVE instruction files as appropriate
   for their project's languages/frameworks.

2. NOT reorganize the directory to a different location.

This allows the generic reference to work across all downstream repos without
requiring customization. If you need to reorganize this directory, update this
reference in the PR template accordingly.
-->

This assumes the `.github/instructions/` directory remains in place (though you may
add or remove specific instruction files based on your project's languages).

---

## Language-Specific Sections

### Python-Specific Section

- **For Python projects:** Keep and customize as needed
- **For non-Python projects:** Remove this entire section
- **For multi-language projects:** Keep if applicable; add additional language sections

### PowerShell-Specific Section

- **For PowerShell projects:** Keep and customize as needed
- **For non-PowerShell projects:** Remove this entire section
- **For multi-language projects:** Keep if applicable

### Adding Language-Specific Sections

Add sections for your project's technology stack. Examples:

- **Node.js:** npm/yarn test passes, ESLint passes, TypeScript compiles
- **.NET:** dotnet test passes, no compiler warnings
- **Go:** go test passes, go vet passes, golint passes
- **Rust:** cargo test passes, clippy passes
- **Java:** Maven/Gradle tests pass, checkstyle passes

---

## Type of Change Options

Add or remove options based on your workflow:

**Consider Adding:**

- `Refactoring (no functional changes)` - if you track refactors separately
- `Security fix` - if security changes need special review
- `Performance improvement` - for performance-focused projects

**Consider Removing:**

- Options that don't apply to your project type

---

## Additional Notes Section

Keep this for reviewers to provide context that doesn't fit elsewhere.

Consider adding prompts for common needs:

- Migration steps (for breaking changes)
- Deployment considerations
- Rollback instructions

---

## Related Issues Section

Keep this section. Update the linking syntax if your project uses different keywords:

- `Fixes #` - Used by some projects
- `Resolves #` - Alternative keyword
- `Closes #` - Used by this template (default)

---

## Test Requirements

The template uses "where appropriate" language for test-related checklist items.
This is intentional for template portability:

- Not all projects have test infrastructure initially
- Not all changes require new tests (e.g., documentation-only changes)
- Downstream repos can strengthen language once they have mature test infrastructure

**For mature projects**, consider changing:

```md
- [ ] I have added or updated tests where appropriate
```

To:

```md
- [ ] I have added tests for all new functionality
- [ ] I have updated tests for all modified functionality
```

---

## Quick Reference

| Section | Keep/Modify/Remove |
| ------- | ------------------ |
| Description | Keep |
| Type of Change | Keep, customize options |
| General Checklist | Keep, remove inapplicable items |
| Pre-commit Verification | Keep if using pre-commit, else remove |
| Python-Specific | Keep for Python projects, else remove |
| PowerShell-Specific | Keep for PowerShell projects, else remove |
| Additional Notes | Keep |
| Related Issues | Keep |

---

## Placeholder Check Workflow

### Behavior

The placeholder check workflow (`.github/workflows/check-placeholders.yml`) runs automatically
in all repositories created from this template. It does NOT run in the template repository itself.

**Implementation:**

```yaml
if: github.repository != 'franklesniak/copilot-repo-template'
```

**This means:**

- ✅ Zero configuration required for adopters
- ✅ Workflow activates automatically on first push/PR
- ✅ Template maintainers don't get spurious failures

### What the Workflow Checks

The workflow verifies placeholders are replaced in:

1. **`.github/ISSUE_TEMPLATE/config.yml`** - Contact links URLs containing `OWNER/REPO`
2. **`CONTRIBUTING.md`** - Clone instructions and issue links containing `OWNER/REPO`
3. **`SECURITY.md`** - Security contact email placeholders (`[security contact email]` and `TODO: Replace`)
4. **Issue templates** (`.yml` and `.yaml`) - URLs containing `OWNER/REPO`
5. **`.github/` directory** - Recursive scan for `https://github.com/OWNER/REPO` links

### File-Type-Aware Comment Filtering

The workflow uses intelligent comment filtering:

- **YAML files** (`.yml`, `.yaml`): Lines starting with `#` are treated as comments (ignored)
- **Markdown files** (`.md`): Lines with `<!-- ... -->` are treated as HTML comments (ignored)
- **Markdown `#`**: These are HEADINGS, not comments, so they ARE checked

### Historical Context

**Previous behavior:** Earlier versions of this template required setting a `TEMPLATE_INITIALIZED`
repository variable to enable the workflow.

**Why changed:** Automatic behavior reduces adoption friction and eliminates the "forgot to configure"
failure mode. The repository-name-based skip gate (`github.repository != '...'`) provides the same
protection without requiring user action.

**Documentation impact:** All references to the `TEMPLATE_INITIALIZED` variable have been removed
from README, TEMPLATE_GUIDE, and other adoption documentation.

---

## CONTRIBUTING.md Customization

### Overview

The `CONTRIBUTING.md` file includes template-specific content that should be reviewed
and customized after cloning the template.

### Placeholder Strategy

`CONTRIBUTING.md` uses `OWNER/REPO` placeholders (not generic `<your-repo>` syntax) because:

- Enables bulk find-and-replace for template adopters (single operation)
- CI automation verifies all placeholders are replaced (`.github/workflows/check-placeholders.yml`)
- Results in working, copy-pastable commands after replacement
- Consistent with issue templates and other template files

**Alternative considered:** Generic angle-bracket syntax like `<your-repository-clone-url>`

**Rejected because:** Harder to replace in bulk, produces non-working commands, inconsistent
with other files that require real values.

### Content to Customize

1. **`OWNER/REPO` placeholders:** Replace with your organization/repository name
   - Clone instructions in "Development Setup" section
   - Issue links in "Questions or Issues?" section

2. **Python version policy:** Update when upstream support changes
   - The template uses an evergreen policy linking to Python's official version status page
   - Customize the minimum version based on your project's requirements

3. **Language-specific sections:** Remove sections for languages you don't use
   - PowerShell test instructions
   - Python test instructions

### Content to Review

**"For Template Users" section:**

This section contains meta-instructions about the template itself (understanding instruction
files, customizing for your project, first-time setup validation). After reviewing:

- **Option A:** Keep it if your project is also a template
- **Option B:** Remove it for end-user projects (most common)
- **Option C:** Move relevant content to your own documentation

### Python Version Policy Pattern

The template uses an evergreen policy pattern instead of hard-coded versions:

**Pattern used:**

```markdown
Contributors and maintainers must use a Python version that is **currently receiving
bugfixes** from the Python core team.

See the [Python Developer's Guide - Versions](https://devguide.python.org/versions/)
page for current version status.
```

**Benefits:**

- No dates to become stale
- Single source of truth via external link
- Clear guidance for template adopters on what to customize

---

## SECURITY.md Customization

The template includes a `SECURITY.md` file that offers **two reporting methods**:

1. GitHub Security Advisories (via UI navigation)
2. Email (with placeholder: `[security contact email]`)

**You must update this file before making the repository public.** The CI workflow
will fail if the email placeholder remains.

### Why Multiple Options?

This template intentionally does NOT prescribe a single "correct" security reporting
method because operational constraints vary widely:

- **Enterprise projects**: Must route through organizational security teams (email required)
- **Open source solo projects**: GitHub Advisories reduce operational burden
- **High-profile projects**: Multiple channels increase accessibility

The CI workflow enforces that adopters make a *deliberate choice*, not that they
choose a specific option.

### Current State

The template's `SECURITY.md` describes how to report via:

- **Option 1:** GitHub Security Advisories → Navigate to Security tab → Click "Report a vulnerability"
- **Option 2:** Email → `[security contact email]` (placeholder)

### Option A: Keep Both Methods (Email + Advisories)

Replace the email placeholder with a real, monitored email address:

```markdown
- Email: security@example.com
```

Keep the GitHub Security Advisories section as-is.

**Pros:**

- Multiple reporting channels increase accessibility
- Email fallback works outside GitHub
- Familiar reporting channel for security researchers
- Works even if GitHub features are unavailable

**Cons:**

- Requires operational ownership of mailbox
- Must monitor and respond to reports from multiple channels
- Needs documented incident response process

**Best for:** Projects with established operational teams or organizational security contacts.

**Requirements:**

- Email must be actively monitored
- Team must have incident response process
- Response time expectations should be documented
- Enable Security Advisories in repository settings

---

### Option B: Email Only

Replace the email placeholder and remove the GitHub Security Advisories section.

**Best for:** Projects that need to route security reports through organizational email systems.

---

### Option C: Advisories Only

Remove the email section entirely.

**You have two sub-options:**

**C1: Keep UI navigation instructions (no URL placeholders to replace):**

```markdown
## Reporting a Vulnerability

Please report security vulnerabilities using GitHub Security Advisories:

1. Navigate to the **Security** tab of this repository
2. Click **Report a vulnerability**
3. Fill out the security advisory form with details about the vulnerability
```

This works as-is with no placeholder replacement needed.

**C2: Provide direct link (requires replacing placeholder):**

```markdown
## Reporting a Vulnerability

Please report security vulnerabilities using [GitHub Security Advisories](https://github.com/OWNER/REPO/security/advisories/new).

**We do not accept security reports via email.** All reports must be submitted through GitHub's private reporting mechanism to ensure proper tracking and coordinated disclosure.
```

**If you choose C2**, you **must** replace `OWNER/REPO` with your actual repository details.

**Example:** If your repository is `octocat/hello-world`, the URL should be:

```markdown
https://github.com/octocat/hello-world/security/advisories/new
```

**Pros:**

- No email channel to manage
- Built-in coordinated disclosure workflow
- Automatic CVE assignment (if eligible)
- Direct link (C2) makes reporting easier

**Cons:**

- Relies on GitHub feature availability
- Requires repository security features enabled
- Reporters must have GitHub accounts

**Best for:** Small projects, solo maintainers, or projects without dedicated security response teams.

**Requirements:**

- Enable Security Advisories in repository settings (Settings → Security → Private vulnerability reporting)
- If using C2 (direct link): Replace `OWNER/REPO` with your actual repository details
- If using C2 (direct link): Verify the URL works by visiting it in a browser
- Ensure maintainers have notifications enabled for security advisories

---

### Enforcement

**The CI workflow will fail if:**

- The placeholder `[security contact email]` remains in `SECURITY.md`
- The placeholder `OWNER/REPO` is found in URLs in `SECURITY.md`

**Note:** The workflow checks for `OWNER/REPO` in URLs to catch cases where adopters add
direct links but forget to customize them.

---

## Documentation Strategy for Issue Templates

**Design Decision:** Issue template design rationale is documented in this guide,
not in extensive inline YAML comments.

**Rationale:**

- **Reduces duplication**: Design decisions apply across multiple templates;
  documenting once prevents inconsistency
- **Cleaner templates**: Makes YAML files easier to scan and edit
- **Centralized maintenance**: Updates to rationale don't require editing multiple files
- **Follows established pattern**: Consistent with PR template documentation approach

**Alternative considered:** Keep all design rationale as inline YAML comments

**Rejected because:**

- Creates visual noise (30+ line comment blocks)
- Duplicates explanations across templates
- Makes it harder to find actionable customization markers
- Increases maintenance burden when rationale needs updating

**Implementation:**

- Each `.yml` file includes a brief header comment pointing to this guide
- `# CUSTOMIZE:` and `# ACTION ITEM:` markers remain inline for visibility
- Extended rationale, alternatives, and examples documented here

---

## Issue Template Design Decisions

### bug_report.yml

#### runtime_version Placeholder Format

**Design Decision:** The placeholder shows multiple runtime examples rather than
a single language example.

**Rationale:**

- Template supports Python, PowerShell, and Markdown-focused projects
- Multi-line examples help reporters provide complete information
- Downstream repos should customize to match their supported runtimes

#### how_ran Placeholder Format

**Design Decision:** The placeholder shows detailed, multi-step installation examples
rather than brief one-liners.

**Rationale:**

- Shows both Python and PowerShell workflows (template portability)
- Demonstrates best practices (venv creation, activation)
- Helps reporters provide complete reproduction steps
- More useful for diverse downstream adopters

#### Area Dropdown - No "I don't know" Option

**Design Decision:** The Area dropdown does NOT include an "I don't know / not sure" option.

**Rationale:**

- "Other (describe/specify)" already handles uncertain cases
- Field is `required: false` by default (intentional for template portability)
- Projects needing required area should define clear, actionable categories
- "I don't know" encourages lazy reporting

**Alternative considered:** Add "I don't know / not sure" option to enable making field required.

**Rejected because:**

- Defeats the purpose of requiring area-based routing
- If a project can't confidently categorize bugs, area shouldn't be required
- "Other" option already provides escape hatch for edge cases

#### Redundant Security Warnings

**Design Decision:** This template intentionally includes multiple security warnings
(top-of-form notice, required checkbox, severity dropdown warning).

**Rationale:**

- Defense in depth: Multiple touchpoints reduce accidental public disclosure
- Different contexts: Some users skim forms; redundancy catches attention
- Audit trail: Required checkbox provides explicit acknowledgment

---

### config.yml

#### GHES Portability

**Design Decision:** GHES host replacement is documented in comments, not enforced via placeholders.

**Rationale:**

- GHES users universally know their host (appears in every URL)
- One-line note in "MUST READ" section is sufficient
- Avoids placeholder proliferation (simpler adoption)
- No CI validation needed for host placeholder

#### Security Link Documentation

**Design Decision:** Detailed setup instructions remain in comments, not in user-facing `about` text.

**Rationale:**

- `about` text appears in issue chooser UI (end-user-facing)
- Long docs URLs would clutter the chooser display
- Comment block is appropriate for template adoption guidance
- Quick setup steps (1-2-3) in comments reduce adopter friction

---

## PR Template Design Decisions

### Link Strategy in PR Template

**Design Decision:** The PR template uses relative links for repository files (e.g., `../blob/HEAD/CONTRIBUTING.md`) rather than absolute URLs with `OWNER/REPO` placeholders.

**Rationale:**

- Template works immediately upon cloning (no placeholder replacement needed)
- Reduces forgotten placeholder risk (common failure mode)
- Proven to work for primary use case (GitHub.com PR body)
- Absolute links remain available as documented opt-in for GHES/email notifications

**Alternative considered:** Use absolute `OWNER/REPO` placeholders as default

**Rejected because:** Requires find-and-replace for all adopters, even when relative links work for their use case. Template portability prioritizes zero-friction adoption.

### Type of Change Options

**Design Decision:** The PR template includes "Dependencies update" as a standard change type.

**Rationale:**

- Dependency management is near-universal (npm, pip, cargo, Maven, etc.)
- Common workflow with automation tools (Dependabot, Renovate)
- Often requires different review standards than feature work
- Low cost, high applicability

**Standard options:**

- Bug fix
- New feature
- Breaking change
- Documentation update
- Dependencies update
- Configuration/tooling change

Projects can add/remove options as documented in the "Type of Change Options" section.

### Checklist Item Links

**Design Decision:** Checklist items that reference files/directories use inline code formatting (e.g., `.github/instructions/`) rather than hyperlinks.

**Rationale:**

- Checklists are reference documentation, not primary navigation
- Adding links to every path creates visual clutter
- Path references are unambiguous without links
- Maintains consistency across checklist items

**Alternative considered:** Make all file/directory references clickable

**Rejected because:** Minimal value for added noise. Contributors can navigate to commonly-referenced directories without hyperlinks.
