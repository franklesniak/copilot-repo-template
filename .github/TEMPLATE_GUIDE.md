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

<!--
DESIGN DECISION: Python Version Policy Reference Pattern
========================================================
CONTRIBUTING.md uses policy-based language ("Python version currently receiving bugfixes")
rather than hardcoded version numbers throughout the document for consistency and
maintainability.

RATIONALE:
1. **Reduces maintenance burden**: Version numbers don't need updates when Python
   releases new versions—the policy link is the single source of truth.

2. **Consistency**: Aligning line 91 with the established Python Version Requirements
   section (lines 22-46) prevents contradictory guidance.

3. **Clear reference**: The anchor link (#python-version-requirements) helps contributors
   find the authoritative policy statement.

TRADE-OFFS:
- Slightly more verbose than "Python 3.13+", but eliminates drift risk between sections.
- Template adopters who want specific version requirements can still customize the
  Python Version Requirements section as instructed.
-->

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

## Node.js Package Configuration

<!--
DESIGN DECISION: package.json Minimal Configuration
===================================================
The template ships with minimal package.json configuration (no repository field,
no engines field, generic metadata) to reduce template adoption friction.

RATIONALE:
1. **Reduces friction**: Most users only need dev tooling (markdownlint scripts)
   without Node.js runtime dependencies.

2. **Prevents placeholder sprawl**: Unlike OWNER/REPO placeholders that break
   functionality if not replaced, missing optional fields don't affect usage.

3. **Clear separation**: Dev tooling (present) vs. application code (user adds).

4. **Private by default**: The "private": true flag means omitted fields like
   repository don't affect npm publishing.

TRADE-OFFS:
- Users creating Node.js applications must manually add metadata fields
- No validation for Node.js version requirements
- Users must consult README for customization guidance

See README.md "Customize Node.js Package" section for user-facing instructions.
-->

If your project uses Node.js/npm as a runtime (not just for dev tooling), update
`package.json` with appropriate metadata. See the README for detailed instructions.

---

## Git Hook Management

<!--
DESIGN DECISION: Pre-commit as Sole Git Hook Manager
=====================================================
This template uses pre-commit as the sole git hook manager. All hooks are configured
in `.pre-commit-config.yaml`.

**Why pre-commit only:**

- **Single tool**:  Unified configuration in one file
- **No conflicts**: Uses standard `.git/hooks/` location, no `core.hooksPath` issues
- **Python standard**: Pre-commit is the de facto standard in Python projects
- **Multi-language**: Also supports Markdown, YAML, JSON, and other file types
- **Isolated environments**: Manages its own tool installations per hook

**For projects preferring Husky:**

If you prefer Husky for git hooks:

1. Remove `.pre-commit-config.yaml`
2. Run `npm install husky --save-dev`
3. Add `"prepare": "husky"` to `package.json` scripts
4. Create `.husky/pre-commit` with your hook commands
5. Do NOT run `pre-commit install` (the two tools conflict)
-->

This template uses pre-commit as the sole git hook manager. All hooks are configured
in `.pre-commit-config.yaml`.

**Why pre-commit only:**

- **Single tool**: Unified configuration in one file
- **No conflicts**: Uses standard `.git/hooks/` location, no `core.hooksPath` issues
- **Python standard**: Pre-commit is the de facto standard in Python projects
- **Multi-language**: Also supports Markdown, YAML, JSON, and other file types
- **Isolated environments**: Manages its own tool installations per hook

**For projects preferring Husky:**

If you prefer Husky for git hooks:

1. Remove `.pre-commit-config.yaml`
2. Run `npm install husky --save-dev`
3. Add `"prepare": "husky"` to `package.json` scripts
4. Create `.husky/pre-commit` with your hook commands
5. Do NOT run `pre-commit install` (the two tools conflict)

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

## License Customization

<!--
DESIGN DECISION: MIT License as Template Default
=================================================
This template uses the MIT License as its default because:

1. **Minimal friction**: MIT is one of the most permissive and widely-understood licenses
2. **Template portability**: Works for both open source and commercial projects (with modification)
3. **Simplicity**: Short, clear terms that don't require legal expertise to understand
4. **Compatibility**: Compatible with most other open source licenses

TRADE-OFFS:

- Pro: Maximum adoption potential due to permissive terms
- Pro: Simple contributor agreement (no CLA needed for most cases)
- Pro: Widely recognized in enterprise and open source communities
- Con: Provides no patent protection (unlike Apache 2.0)
- Con: No copyleft protection (unlike GPL)
- Con: Proprietary projects must replace with appropriate license

ALTERNATIVES CONSIDERED:

1. Apache 2.0 as default: Rejected because patent grant clause can be unfamiliar to
   some adopters and adds complexity for simple projects
2. No default license: Rejected because unlicensed code is legally unusable;
   providing a permissive default is better than no default
3. Dual licensing (MIT + Apache 2.0): Rejected as over-engineering for a template

RECOMMENDATION:

Most open source projects can keep MIT. Consider Apache 2.0 for projects involving
patents. Proprietary projects MUST replace the license entirely.
-->

This template uses the MIT License by default. **You MUST review and update the license
if your project requires different terms.**

### Files That Reference the License

When changing your project's license, you MUST update all of the following files:

| File | What to Update |
| --- | --- |
| `LICENSE` | Replace entire file with your license text |
| `CONTRIBUTING.md` | Update the "License" section |
| `README.md` | Update the "License" section (near bottom of file) |
| `pyproject.toml` | Update `license = { text = "MIT" }` in `[project]` section |
| `package.json` | Update `"license": "MIT"` field |
| `templates/python/pyproject.toml` | Update `license = { text = "MIT" }` in `[project]` section |

**Note:** The `package-lock.json` file also contains `"license": "MIT"` entries, but these
refer to the licenses of npm dependencies (not your project). These do not need to be
changed when updating your project's license.

### Option A: Keep MIT License (Default)

No changes required. The MIT License is suitable for most open source projects where you
want to allow maximum reuse with minimal restrictions.

**Best for:**

- Open source projects prioritizing adoption
- Libraries intended for broad reuse
- Projects without patent concerns
- Simple utilities and tools

---

### Option B: Apache License 2.0

Replace MIT with Apache 2.0 if you need explicit patent protection.

**Step 1:** Replace the `LICENSE` file content with the Apache 2.0 license text from
[https://www.apache.org/licenses/LICENSE-2.0.txt](https://www.apache.org/licenses/LICENSE-2.0.txt).

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
license = { text = "Apache-2.0" }
```

```json
// In package.json
"license": "Apache-2.0"
```

**Pros:**

- Explicit patent grant protects users and contributors
- Well-understood in enterprise environments
- Compatible with GPL v3 (unlike MIT alone in some interpretations)

**Cons:**

- Longer, more complex license text
- Requires including NOTICE file for attributions
- Some developers unfamiliar with patent clauses

**Best for:**

- Projects with potential patent implications
- Enterprise-backed open source projects
- Projects that may be incorporated into GPL v3 works

---

### Option C: Proprietary License

For closed-source or commercial projects, you MUST replace the MIT License with
appropriate proprietary terms.

**Step 1:** Replace the `LICENSE` file with your proprietary license text.

Example proprietary license header:

```text
PROPRIETARY AND CONFIDENTIAL

This software and associated documentation files are proprietary and confidential.

Copyright [YEAR] [YOUR COMPANY NAME]. All rights reserved.

This software is protected under the copyright laws of the United States and other
countries as an unpublished work. This software contains information that is
proprietary and confidential to [YOUR COMPANY NAME], which shall not be disclosed
outside the company or duplicated, used, or disclosed in whole or in part for any
purpose other than authorized internal use.

Any use or disclosure in whole or in part of this information without the express
written permission of [YOUR COMPANY NAME] is prohibited.

Unauthorized copying of this software, via any medium, is strictly prohibited.

Some dependencies may be subject to their own license terms. See the respective
dependency documentation for details.
```

**Step 2:** Update `CONTRIBUTING.md` to reflect contribution terms:

```markdown
## License

This project is proprietary software. By contributing to this project, you agree that:

1. Your contributions become the property of [YOUR COMPANY NAME]
2. You have the right to make the contribution
3. You grant [YOUR COMPANY NAME] all rights to use your contribution

Contributors may be required to sign a Contributor License Agreement (CLA) before
contributions can be accepted. Contact [EMAIL] for CLA details.
```

**Step 3:** Update `README.md`:

```markdown
## License

Proprietary - Copyright [YEAR] [YOUR COMPANY NAME]. All rights reserved.
See [LICENSE](LICENSE) for details.
```

**Step 4:** Update package manifests:

```toml
# In pyproject.toml
license = { text = "Proprietary" }
# Or remove the license field entirely and add:
# classifiers = ["License :: Other/Proprietary License"]
```

```json
// In package.json
"license": "UNLICENSED"
// Or for explicit proprietary:
"license": "SEE LICENSE IN LICENSE"
```

**Additional Considerations for Proprietary Projects:**

- [ ] **Contributor License Agreement (CLA):** Consider requiring CLAs for any external
      contributions. Tools like [CLA Assistant](https://cla-assistant.io/) can automate this.
- [ ] **IP Assignment:** Ensure employment contracts or contributor agreements assign
      intellectual property rights appropriately.
- [ ] **Dependency Audit:** Review all open source dependencies to ensure their licenses
      are compatible with proprietary use (avoid GPL dependencies if you cannot comply
      with copyleft terms).
- [ ] **NOTICE file:** If using Apache-licensed dependencies, you MUST include required
      attribution notices.
- [ ] **Legal Review:** Have legal counsel review your license terms before public or
      customer distribution.

**Best for:**

- Commercial software products
- Internal enterprise tools
- Proprietary SaaS backends
- Projects with trade secrets

---

### Option D: Other Open Source Licenses

For licenses not covered above (BSD, GPL, LGPL, MPL, etc.), follow the same pattern:

1. Replace `LICENSE` file with the full license text
2. Update `CONTRIBUTING.md` contributor agreement
3. Update `README.md` license section
4. Update `pyproject.toml` with the appropriate [SPDX identifier](https://spdx.org/licenses/)
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

---

### Dual Licensing

Some projects offer multiple license options (e.g., GPL for open source use, commercial
license for proprietary use). If dual licensing:

1. Include both license texts in `LICENSE` (or separate files like `LICENSE-MIT` and
   `LICENSE-APACHE`)
2. Clearly explain the licensing options in README.md
3. Document which license applies under which conditions

---

## CI Workflow Customization

### Overview

The CI workflow (`.github/workflows/ci.yml`) includes optional configurations that
adopters should review and adjust based on their project's maturity and requirements.
This section documents the key customization points.

### Type Checking Strictness

<!--
DESIGN DECISION: Non-Blocking Type Checking by Default
=======================================================
The template uses `continue-on-error: true` for the mypy type checking job. This is
a deliberate choice for template portability.

**Why this is the right default for a template:**
- Template adopters start with varying levels of type coverage (often zero)
- Blocking type errors on day one creates adoption friction
- Gradual type adoption is a well-established Python best practice
- Allows adopters to see type errors without blocking their workflow

**Trade-offs:**

Blocking type checking (strict):
- Pros: Enforces type safety, prevents type debt accumulation
- Cons: High friction for new adopters, requires upfront investment

Non-blocking type checking (current):
- Pros: Zero friction adoption, gradual improvement path, visibility without blocking
- Cons: Type errors can accumulate if not addressed, requires discipline

**Alternatives considered:**

1. No type checking at all: Rejected because mypy provides value even when non-blocking
   (developers can see errors and fix them opportunistically)

2. Strict by default with documentation to make it lenient: Rejected because this
   inverts the adoption experience—failing CI on first push is a poor template UX

3. Conditional based on repository variable: Rejected as over-engineering for a
   simple toggle that adopters can easily change

**When downstream repos should make this strict:**
- After achieving reasonable type coverage (70%+ of public APIs)
- Before releasing stable versions (1.0+)
- When the team has committed to maintaining type annotations
- For libraries where type hints are part of the API contract
-->

The mypy step in `.github/workflows/ci.yml` (lines 114-116) includes:

```yaml
run: mypy $MYPY_PATHS
continue-on-error: true
```

**What `continue-on-error: true` does:**

- Mypy runs and reports all type errors in the workflow log
- The job is marked as successful even if mypy finds errors
- Type errors are visible but do not block PR merges or deployments
- The overall CI workflow continues to subsequent jobs

**Why the template uses this setting:**

- **Gradual adoption:** New projects rarely have complete type coverage on day one
- **Template portability:** Works for any project without requiring initial type work
- **Visibility without friction:** Developers see type errors without being blocked

#### When to Make Type Checking Strict

**Make it strict when:**

- You have added type hints to your public APIs (functions, classes, methods)
- Your team has agreed to maintain type annotations going forward
- You want to prevent type regressions in PRs
- Before releasing stable versions (1.0.0+)
- For libraries where type hints are part of the public API contract

**Keep it non-blocking when:**

- You just created the repository from this template (day 1)
- You are in rapid prototyping phase
- Your project has minimal or no type coverage
- You want to incrementally add types without blocking work

#### How to Make Type Checking Strict

**Step 1:** Remove `continue-on-error: true` from the mypy step in `.github/workflows/ci.yml`:

```yaml
# Before (non-blocking):
- name: Run mypy
  env:
    MYPY_PATHS: "src/ tests/"
  run: mypy $MYPY_PATHS
  continue-on-error: true

# After (strict):
- name: Run mypy
  env:
    MYPY_PATHS: "src/ tests/"
  run: mypy $MYPY_PATHS
```

**Step 2:** Ensure your code has sufficient type coverage. Run mypy locally first:

```bash
mypy src/ tests/
```

**Step 3:** Fix any type errors before pushing, or add them to a tracking issue.

#### Optional: Tighten mypy Configuration

For stricter type enforcement, update the `[tool.mypy]` section in `pyproject.toml`:

```toml
[tool.mypy]
python_version = "3.13"
warn_return_any = true
warn_unused_configs = true
# Template default is false; change to true for stricter checking:
disallow_untyped_defs = true
```

The `disallow_untyped_defs = true` setting requires type annotations on all function
definitions. This is recommended for mature projects with comprehensive type coverage.

See the [mypy configuration documentation](https://mypy.readthedocs.io/en/stable/config_file.html)
for additional strictness options.

---

## Python Dependency Versions

<!--
DESIGN DECISION: Python Dependency Version Alignment
=====================================================
The root `pyproject.toml` uses the same pytest version (>=8.0.0) as the template
file (`templates/python/pyproject.toml`). This is a deliberate choice for template
clarity and consistency.

RATIONALE:
1. **Single source of truth**: The root `pyproject.toml` serves both as CI configuration
   AND as a working example for template users. Using current best-practice versions
   demonstrates the intended configuration.

2. **Reduces confusion**: When template consumers compare the root `pyproject.toml`
   to `templates/python/pyproject.toml`, consistent versions eliminate questions about
   which version to use.

3. **Current stable version**: pytest 8.0+ is the current stable version as of
   January 2026, with significant improvements over pytest 7.x including better
   assertion introspection, improved output formatting, and enhanced plugin support.

4. **Template portability**: Template adopters can use either file as reference
   without needing to reconcile version differences.

TRADE-OFFS:
- Slightly higher minimum version requirement than strictly necessary for CI to pass
- May require newer Python environments (pytest 8.0 requires Python 3.8+)

ALTERNATIVES CONSIDERED:
- Using pytest>=7.0 in root for minimal CI requirements: Rejected because it creates
  inconsistency between root and template files, leading to adopter confusion.
-->

The root `pyproject.toml` and `templates/python/pyproject.toml` use aligned dependency
versions. This ensures template adopters have a consistent reference regardless of which
file they examine.

**Key principle:** The root `pyproject.toml` is both functional CI configuration AND
a reference example. It should reflect current best practices, not minimal requirements.

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

### Cross-Template Customization Patterns

This section documents customization points that apply across all issue templates.

#### Labels

Update labels to match your repository's label taxonomy. Common patterns:

- **Type labels**: `bug`, `enhancement`, `documentation`
- **Status labels**: `triage`, `confirmed`, `in-progress`
- **Priority labels**: `priority:critical`, `priority:high`, `priority:medium`, `priority:low`
- **Area labels**: `area:api`, `area:cli`, `area:docs`

**ACTION ITEM:** If you want to use a `triage` label, you must first create it in your
repository (it doesn't exist by default). The `triage` label cannot be auto-created when
cloning a template repository—GitHub does not support this.

#### Assignees and Projects

Both can be optionally added to auto-route issues:

```yaml
# Auto-assign issues to specific users
assignees:
  - maintainer-username

# Auto-add issues to a GitHub Project (uses project number)
projects:
  - org/1
```

See [GitHub docs](https://docs.github.com/en/issues/planning-and-tracking-with-projects)
for project configuration.

#### Required Fields

Mark fields required only when information is essential for triage. Over-requiring fields
discourages issue submissions. Recommended required: description, steps to reproduce (bugs),
expected/actual behavior (bugs), version, OS, severity.

#### Field IDs

Templates use `snake_case` for all field IDs (e.g., `steps_to_reproduce`, `operating_system`).
Maintain this convention when adding new fields for consistency.

#### Issue Types

Optionally add `type` top-level field for issue categorization (defined at org level):

```yaml
type: Bug
```

---

### bug_report.yml

#### Security Notice URL Strategy

The security notice uses relative links that work automatically after cloning:

- `[Security tab](security)` - links to repository's Security tab
- `[SECURITY.md](blob/HEAD/SECURITY.md)` - links to security policy file

**Tested and confirmed** to work in GitHub issue forms on GitHub.com.

**Trade-offs:**

- Relative links work immediately without OWNER/REPO replacement
- For GHES or external contexts, replace with absolute URLs

#### runtime_version Placeholder Format

**Design Decision:** The placeholder shows multiple runtime examples rather than
a single language example, using currently-supported version numbers.

**Rationale:**

- Template supports Python, PowerShell, and Markdown-focused projects
- Multi-line examples help reporters provide complete information
- **Placeholder examples should use currently-supported versions** for consistency
  with project policy (e.g., Python 3.13+ aligns with template's Python version policy)
- Using exact version format (not vague `.x`) demonstrates correct format
- Downstream repos should customize to match their supported runtimes

**Customization note:** Adopters should update version examples to match their
project's supported runtimes and version policies.

#### how_ran Placeholder Format

**Design Decision:** The placeholder shows detailed, multi-step installation examples
rather than brief one-liners, including both `pyproject.toml` and `requirements.txt` workflows.

**Rationale:**

- Shows both `pyproject.toml` and `requirements.txt` workflows (template portability)
- Demonstrates best practices (venv creation, activation)
- Helps reporters provide complete reproduction steps
- Supports diverse downstream adopter workflows
- Doesn't lock adopters into a single dependency management approach

**Customization note for adopters:** Simplify this placeholder to show only your project's
dependency management approach (e.g., remove `pyproject.toml` section if you only use
`requirements.txt`, or vice versa).

**Alternative considered:** Brief form with multiple options on same line

```yaml
placeholder: |
  # Python
  pip install -e .  # or: pip install -r requirements.txt
  python -m your_package  # or: python script.py
```

**Rejected because:**

- Compressed form is harder to parse visually
- Doesn't demonstrate best practices (venv setup, activation)
- Less helpful for users unfamiliar with Python dependency management

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

**Why keep all three:**

- **Different interaction patterns:** Some users skim headers (→ checkbox catches them),
  some focus on dropdowns (→ severity warning catches them). Multiple touchpoints maximize
  chance of catching accidental public disclosure.
- **High stakes, low cost:** Cost of redundancy is slightly longer form. Cost of failure
  is public disclosure of security vulnerability. Risk/reward strongly favors redundancy.
- **Template portability:** Downstream adopters can easily remove warnings if desired.
  Harder to add them back if not provided. Template should err on side of caution.
- **Audit trail:** Required checkbox provides explicit acknowledgment.

**Alternative considered:** Remove severity dropdown warning text, keep top warning + checkbox.

**Rejected because:**

- Severity dropdown is where users actively interact (making selection)
- Warning at point of interaction provides contextual reminder
- Consistency with documented design decision (no compelling reason to change)

**If you prefer less redundancy**, remove the warning from severity dropdown by changing:

```yaml
description: >-
  Select the severity level that best describes the impact from your perspective.
  Note: This is your self-assessment; maintainers may adjust during triage.
```

---

### feature_request.yml

#### Area Dropdown Consistency

The Area dropdown options match `bug_report.yml` for consistency. Update both
templates when modifying area categories.

#### Priority vs Scope

The template separates priority (urgency from reporter's perspective) and scope
(size of the feature). Both are optional and self-assessed by reporters; maintainers
may adjust during triage.

---

### documentation_issue.yml

#### No Area Dropdown by Default

**Design Decision:** This template intentionally does NOT include an `area` dropdown field.

**Rationale:**

- Most consumers have simple documentation sets that don't require area routing
- Keeping the template lean encourages drive-by documentation reports
- Documentation issues are typically easy to locate via the `location` field

**For large documentation sets**, you may add an optional area dropdown:

```yaml
- type: dropdown
  id: area
  attributes:
    label: Documentation Area (optional)
    description: What part of the documentation does this affect?
    options:
      - Getting Started / Installation
      - API Reference
      - Tutorials / Guides
      - FAQ / Troubleshooting
      - Other
  validations:
    required: false
```

#### Location Field Optional

**Trade-off:**

- Optional (current): Encourages drive-by typo reports with lower friction
- Required: More actionable for maintainers; may reduce submissions

Recommendation: Keep optional but encourage providing location via description text.

---

### config.yml

#### blank_issues_enabled

Set to `true` for flexibility (allows any issue format), or `false` to enforce
template usage. Most projects benefit from `true` initially; consider `false`
once you have comprehensive templates.

#### contact_links URL Requirement

**Critical:** Unlike issue-form markdown blocks (where relative links work),
`contact_links` URLs MUST be absolute URLs. There is no way to use relative links here.

- You MUST replace `OWNER/REPO` with your actual org/repo
- Use `blob/HEAD` instead of `blob/main` to support non-main default branches

#### GitHub Enterprise Server (GHES) Portability

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

#### Discussions Link

Kept commented out by default because many downstream repos don't enable Discussions.
To enable:

1. Go to repository Settings > General > Features
2. Check "Discussions" checkbox
3. Uncomment the discussions contact link block
4. Replace `OWNER/REPO` with your actual org/repo

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

---

## Dependabot Configuration

<!--
DESIGN DECISION: Dependabot Enabled by Default

===============================================

Dependabot is enabled by default in this template repository to provide automated
dependency security monitoring and update management. This configuration represents
security-conscious defaults that align with best practices for modern software projects.

Rationale:
- Security vulnerabilities in dependencies are automatically detected and PRs created
- Reduces maintenance burden for keeping dependencies current with security patches
- Template repositories should model best practices; security-conscious defaults are appropriate
- Monitors all three dependency ecosystems used by this template: npm, pip, and GitHub Actions
- Weekly schedule with grouped minor/patch updates balances security with reduced PR noise

TRADE-OFFS:

- Pro: Automated security vulnerability detection and remediation
- Pro: Keeps dependencies current without manual monitoring
- Pro: Reduces risk of using outdated, vulnerable packages
- Pro: Grouped updates reduce PR noise for minor/patch versions
- Con: Creates PR noise for minor updates that adopters may not want
- Con: Adopters who prefer manual dependency management must disable it
- Con: May suggest updates that require testing/validation before merging

RECOMMENDATION:

Keep Dependabot enabled unless you have a specific reason to manage dependencies
manually or use an alternative tool (e.g., Renovate). If the PR volume is too high,
consider adjusting the schedule from weekly to monthly, or customizing the grouping
configuration. Delete `.github/dependabot.yml` to disable entirely.
-->

### What Dependabot Does

Dependabot automatically monitors your repository's dependencies and creates pull
requests when updates are available. The template configuration monitors:

- **npm** dependencies (from `package.json`)
- **pip** dependencies (from `pyproject.toml`)
- **GitHub Actions** (from workflow files)

### Customization Options

**Adjust update frequency:**

```yaml
schedule:
  interval: "monthly"  # Options: daily, weekly, monthly
```

**Disable specific ecosystems:**

Remove the corresponding `package-ecosystem` block from `.github/dependabot.yml`.

**Change grouping strategy:**

The default configuration groups minor and patch updates. To receive individual
PRs for all updates, remove the `groups:` section.

### Disabling Dependabot

To completely disable Dependabot, delete `.github/dependabot.yml`. Dependabot
will stop monitoring your repository immediately.

See [GitHub Dependabot documentation](https://docs.github.com/en/code-security/dependabot)
for additional configuration options.

---

## CODEOWNERS Configuration

<!--
DESIGN DECISION: CODEOWNERS with Placeholder

=============================================

The template includes a CODEOWNERS file with @OWNER placeholders that template
adopters must replace. This file enables automatic review request assignment for
pull requests and documents code ownership.

Rationale:
- CODEOWNERS enables automatic review requests for PRs affecting specific paths
- Works well with branch protection rules requiring code owner approval
- Using @OWNER placeholder follows the existing OWNER/REPO pattern in this template
- Placeholder check workflow ensures adopters don't forget to customize
- Default rules cover repository root, workflows, and Copilot instructions

TRADE-OFFS:

- Pro: Automatic PR review assignment reduces manual reviewer selection
- Pro: Documents code ownership explicitly in the repository
- Pro: Works with branch protection "required reviews from code owners" setting
- Pro: Placeholder check workflow ensures customization before use
- Con: Requires placeholder replacement during template adoption
- Con: Solo maintainers may not benefit from CODEOWNERS
- Con: Adds another file to the template adoption checklist

RECOMMENDATION:

Replace @OWNER with your GitHub username or team name (e.g., @octocat or
@my-org/maintainers). For solo projects, you may delete the file if automatic
review assignment is not needed. For team projects, CODEOWNERS is highly
recommended to ensure consistent review practices.
-->

### What CODEOWNERS Does

The CODEOWNERS file defines who is automatically requested to review pull requests
that modify specific files or directories. When a PR is opened, GitHub checks the
CODEOWNERS file and requests reviews from the specified users or teams.

### Template Configuration

The template includes these default ownership rules:

```text
# Default owners for everything in the repo
* @OWNER

# Workflow files require maintainer review
.github/workflows/ @OWNER

# Copilot instructions require maintainer review
.github/copilot-instructions.md @OWNER
.github/instructions/ @OWNER
```

### Customization

**Replace the placeholder:**

Replace `@OWNER` with your GitHub username (e.g., `@octocat`) or team
(e.g., `@my-org/maintainers`).

**Add path-specific owners:**

```text
# Documentation team owns docs
docs/ @my-org/docs-team

# Security team must review security-related files
SECURITY.md @my-org/security-team
```

**Multiple owners:**

```text
# Both teams are requested for API changes
src/api/ @my-org/backend-team @my-org/api-reviewers
```

### Disabling CODEOWNERS

To disable automatic review assignment, delete `.github/CODEOWNERS`.

See [GitHub CODEOWNERS documentation](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
for additional patterns and configuration options.

---

## Branch Protection Setup (Recommended)

<!--
DESIGN DECISION: Branch Protection Documentation

================================================

This template includes documentation for branch protection setup rather than
attempting to configure it automatically. Branch protection is a repository
setting that cannot be included in template repositories, so documentation
is the appropriate way to guide adopters.

Rationale:
- Helps adopters set up proper CI gates for their default branch
- Explains the intended use of CI workflows and how they relate to branch protection
- Documents which CI jobs are good candidates for required status checks
- Clarifies the relationship between `needs:` dependencies and branch protection

TRADE-OFFS:

- Pro: Helps adopters set up proper CI gates quickly
- Pro: Explains intended use of CI workflows from this template
- Pro: Clarifies complementary nature of CI dependencies vs branch protection
- Con: GitHub UI may change over time, requiring documentation updates
- Con: Cannot be enforced via template (requires manual setup in each repository)
- Con: Adopters must manually configure settings in GitHub UI

RECOMMENDATION:

Configure branch protection for your default branch after initial repository setup.
At minimum, require the pre-commit check to pass before merging. For additional
protection, also require downstream checks like tests and type checking.
-->

Branch protection rules prevent direct pushes to important branches and require
certain conditions (like passing CI checks) before pull requests can be merged.
This section documents how to configure branch protection using the CI workflows
provided by this template.

### CI Jobs Available as Required Status Checks

The template provides these CI jobs that can be configured as required status checks:

| Workflow | Job Name | Recommended as Required | Notes |
| --- | --- | --- | --- |
| `ci.yml` | **Pre-commit** | ✅ Yes | Foundational check—catches formatting and linting issues |
| `ci.yml` | **Type Check (mypy)** | Optional | Set to `continue-on-error: true` by default; make strict when ready |
| `ci.yml` | **Test** | ✅ Yes | Ensures tests pass on all platforms |
| `markdownlint.yml` | **Markdown Lint** | ✅ Yes | Ensures documentation quality |
| `powershell-ci.yml` | **lint** | Optional | Only if using PowerShell |
| `powershell-ci.yml` | **PowerShell Tests (Pester)** | Optional | Only if using PowerShell with tests |

**Note:** Job names must match exactly as they appear in the GitHub Actions UI. The names
listed above are the exact job names from the template workflows.

### How to Configure Branch Protection

1. Go to your repository on GitHub
2. Navigate to **Settings** > **Branches**
3. Click **Add branch protection rule** (or edit existing rule)
4. Enter your branch name pattern (e.g., `main` or `master`)
5. Configure the following settings:

**Recommended settings:**

- ✅ **Require a pull request before merging**
  - ✅ Require approvals (set to 1 or more)
  - ✅ Dismiss stale pull request approvals when new commits are pushed
- ✅ **Require status checks to pass before merging**
  - ✅ Require branches to be up to date before merging
  - Search for and select the job names you want to require (e.g., "Pre-commit", "Test")
- ✅ **Require conversation resolution before merging** (optional but recommended)
- ✅ **Do not allow bypassing the above settings** (for strict enforcement)

### Understanding `needs:` vs Branch Protection

The template CI workflows use `needs:` to create internal job dependencies:

```yaml
test:
  name: Test
  needs: pre-commit  # Test job waits for pre-commit to pass
```

**How `needs:` works (internal CI dependency):**

- If `pre-commit` fails, the `test` job is automatically skipped
- This saves CI minutes by not running tests on poorly-formatted code
- The dependency is internal to the workflow—GitHub Actions manages it

**How branch protection works (external gate):**

- Branch protection is configured in repository settings, not in workflows
- It prevents PR merges until selected status checks pass
- It's an external enforcement mechanism that operates at the PR level

**These are complementary:**

- `needs:` optimizes CI execution (skip downstream jobs on early failure)
- Branch protection enforces quality gates (block merges until checks pass)
- Using both provides defense in depth

**Recommendation:** Require **both** the `Pre-commit` job AND downstream jobs like
`Test` in branch protection. Even though `Test` won't run if `Pre-commit` fails
(due to `needs:`), requiring both ensures that:

1. Format/lint issues block the PR (Pre-commit requirement)
2. Test failures block the PR (Test requirement)
3. Skipped jobs (due to upstream failure) also block the PR

### Example Branch Protection Configuration

For a Python project using this template:

**Required status checks:**

- Pre-commit
- Test
- Markdown Lint

**Optional but recommended:**

- Type Check (mypy) — after making it strict by removing `continue-on-error: true`

For a multi-language project (Python + PowerShell):

**Required status checks:**

- Pre-commit
- Test
- Markdown Lint
- lint (PowerShell)
- PowerShell Tests (Pester)
