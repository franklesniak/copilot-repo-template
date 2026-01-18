# Template Guide: Pull Request Template Customization

<!--
FILE PLACEMENT RATIONALE:
This file is placed in .github/ because it is GitHub-specific configuration guidance
that relates directly to other files in this directory (pull_request_template.md,
ISSUE_TEMPLATE/, workflows/, etc.). Keeping it here makes it discoverable alongside
the files it documents and ensures template users encounter it when exploring GitHub
configuration. This is preferable to docs/ (general project documentation) or the
repo root (which should remain clean for end users).
-->

## Overview

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
