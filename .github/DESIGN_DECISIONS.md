# Template Design Decisions

This document records design decisions made during the creation and maintenance of `franklesniak/copilot-repo-template`. It serves as institutional memory to prevent re-litigation of settled decisions during code review.

> **For consumers of this template:** This document is NOT an instruction guide. See [GETTING_STARTED_NEW_REPO.md](../GETTING_STARTED_NEW_REPO.md) or [GETTING_STARTED_EXISTING_REPO.md](../GETTING_STARTED_EXISTING_REPO.md) for setup instructions, and [OPTIONAL_CONFIGURATIONS.md](../OPTIONAL_CONFIGURATIONS.md) for customization options.

---

## Table of Contents

- [File Placement](#file-placement)
- [Pull Request Template](#pull-request-template)
- [Pre-commit and Git Hooks](#pre-commit-and-git-hooks)
- [Coding Standards and Instructions](#coding-standards-and-instructions)
  - [Current Provider Versions in Terraform Examples](#design-decision-current-provider-versions-in-terraform-examples)
  - [Terraform Instructions Document Length Strategy](#design-decision-terraform-instructions-document-length-strategy)
  - [Instruction Files Scope (Code Authoring, Not CI/CD)](#design-decision-instruction-files-scope-code-authoring-not-cicd)
- [Node.js Package Configuration](#nodejs-package-configuration)
- [CI Workflow Configuration](#ci-workflow-configuration)
- [Python Configuration](#python-configuration)
- [Security and Vulnerability Reporting](#security-and-vulnerability-reporting)
- [License Configuration](#license-configuration)
- [Dependabot Configuration](#dependabot-configuration)
- [CODEOWNERS Configuration](#codeowners-configuration)
- [Issue Template Design Decisions](#issue-template-design-decisions)
- [Branch Protection Setup](#branch-protection-setup)

---

## File Placement

### Design Decision: DESIGN_DECISIONS.md Location

This file is placed in `.github/` because it is GitHub-specific configuration guidance that relates directly to other files in this directory (pull_request_template.md, ISSUE_TEMPLATE/, workflows/, etc.). Keeping it here makes it discoverable alongside the files it documents and ensures template maintainers encounter it when exploring GitHub configuration. This is preferable to `docs/` (general project documentation) or the repo root (which should remain clean for end users).

---

## Pull Request Template

### Design Decision: Contributing Guidelines Link

The PR template uses a relative link for contributing guidelines:

```md
[contributing guidelines](../blob/HEAD/CONTRIBUTING.md)
```

This relative link has been tested and confirmed to work correctly in rendered PR views on GitHub.com. It resolves to the repository's CONTRIBUTING.md file regardless of the default branch name (main, master, develop, etc.) due to the use of HEAD.

**Why this approach:**

1. **Clone works with minimal setup**: Template users don't need to find-and-replace OWNER/REPO placeholders—the link works immediately after cloning.

2. **Reduces forgotten placeholder risk**: Absolute URLs with placeholders can lead to broken links if users forget to replace them. The relative link pattern eliminates this failure mode.

3. **Tested and verified**: This link pattern is confirmed to work in GitHub.com PR views.

**Trade-offs:**

- The relative link may not resolve correctly in PR preview/draft mode before the branch is pushed, or in non-GitHub contexts (local Markdown preview, email notifications, etc.).
- GitHub Enterprise Server (GHES) compatibility varies by version.

If you need the link to work in PR drafts, GHES, or external contexts, replace with:
`https://github.com/OWNER/REPO/blob/HEAD/CONTRIBUTING.md` (remembering to replace OWNER/REPO with your actual org/repo name).

### Design Decision: Link Strategy in PR Template

The PR template uses relative links for repository files (e.g., `../blob/HEAD/CONTRIBUTING.md`) rather than absolute URLs with `OWNER/REPO` placeholders.

**Rationale:**

- Template works immediately upon cloning (no placeholder replacement needed)
- Reduces forgotten placeholder risk (common failure mode)
- Proven to work for primary use case (GitHub.com PR body)
- Absolute links remain available as documented opt-in for GHES/email notifications

**Alternative considered:** Use absolute `OWNER/REPO` placeholders as default

**Rejected because:** Requires find-and-replace for all adopters, even when relative links work for their use case. Template portability prioritizes zero-friction adoption.

### Design Decision: Type of Change Options

The PR template includes "Dependencies update" as a standard change type.

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

### Design Decision: Checklist Item Links

Checklist items that reference files/directories use inline code formatting (e.g., `.github/instructions/`) rather than hyperlinks.

**Rationale:**

- Checklists are reference documentation, not primary navigation
- Adding links to every path creates visual clutter
- Path references are unambiguous without links
- Maintains consistency across checklist items

**Alternative considered:** Make all file/directory references clickable

**Rejected because:** Minimal value for added noise. Contributors can navigate to commonly-referenced directories without hyperlinks.

---

## Pre-commit and Git Hooks

### Design Decision: Conditional Pre-commit Section

The pre-commit section uses conditional language ("if this repository uses pre-commit") to maintain template portability. This is intentional:

1. **Not all downstream repos use pre-commit**: Many projects use different linting/formatting approaches (IDE settings, CI-only checks, language-specific tools).

2. **Reduces friction**: Contributors to repos without pre-commit won't be confused by irrelevant instructions.

3. **Self-documenting**: The conditional phrasing makes it clear when the section applies.

**Recommendation for repos using pre-commit:**

If your repository uses pre-commit hooks, replace the conditional section with the more direct version for clearer contributor guidance.

### Design Decision: Pre-commit as Sole Git Hook Manager

This template uses pre-commit as the sole git hook manager. All hooks are configured in `.pre-commit-config.yaml`.

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

## Coding Standards and Instructions

### Design Decision: .github/instructions/ Reference

The PR template reference to `.github/instructions/` assumes the directory structure will remain as provided in this template. The assumption is that downstream repos will:

1. Keep the directory structure but ADD/REMOVE instruction files as appropriate for their project's languages/frameworks.

2. NOT reorganize the directory to a different location.

This allows the generic reference to work across all downstream repos without requiring customization. If you need to reorganize this directory, update this reference in the PR template accordingly.

### Design Decision: Python Version Policy Reference Pattern

CONTRIBUTING.md uses policy-based language ("Python version currently receiving bugfixes") rather than hardcoded version numbers throughout the document for consistency and maintainability.

**Rationale:**

1. **Reduces maintenance burden**: Version numbers don't need updates when Python releases new versions—the policy link is the single source of truth.

2. **Consistency**: Aligning references with the established Python Version Requirements section prevents contradictory guidance.

3. **Clear reference**: The anchor link (#python-version-requirements) helps contributors find the authoritative policy statement.

**Trade-offs:**

- Slightly more verbose than "Python 3.13+", but eliminates drift risk between sections.
- Template adopters who want specific version requirements can still customize the Python Version Requirements section as instructed.

### Design Decision: Realistic Examples in Terraform Instructions (No REPLACE_ME_* Placeholders)

The `.github/instructions/terraform.instructions.md` file uses realistic example values (e.g., `acme-corp-terraform-state`, `us-east-1`) instead of `REPLACE_ME_*` placeholder patterns.

**Rationale:**

1. **No adoption burden**: Consumers don't need to find-replace `REPLACE_ME_*` patterns throughout examples before the documentation is useful.

2. **Cleaner examples**: Code looks like real Terraform, improving readability and comprehension for both humans and LLMs.

3. **Consistency with other instructions**: PowerShell and Python instruction files in this repository use realistic examples without placeholders—Terraform instructions now follow the same pattern.

4. **Reduced document length**: No need for a lengthy "Placeholder Convention" section with placeholder tables and usage rules.

5. **Better LLM comprehension**: LLMs are trained on realistic code patterns, not `REPLACE_ME_*` conventions, making realistic examples more effective for AI-assisted coding.

**What ensures examples aren't mistaken for prescriptive values:**

- **"About Examples in This Document" section**: A clear statement at the beginning of the document explains that all code examples are illustrative.

- **Inline comments on key examples**: Backend configuration blocks include comments like `# Use your state bucket name` to reinforce that values require customization.

- **Self-documenting names**: Example names like `acme-corp-terraform-state` are obviously placeholder-like through their fictional organization prefix.

**Alternative considered:** Use `REPLACE_ME_*` placeholder markers for all values requiring customization.

**Rejected because:**

- Adds friction for consumers who must do find-replace before examples are useful
- Looks unusual compared to typical Terraform documentation in the ecosystem
- Creates inconsistency with how PowerShell and Python instructions handle examples
- The only scenario where `REPLACE_ME_*` provides unique value is when someone might literally copy-paste a backend block into production without reading—but that's a user error, not a documentation problem, and the same risk exists with any example code in any documentation
- A clear "About Examples" note addresses the "examples are illustrative" concern sufficiently

### Design Decision: Current Provider Versions in Terraform Examples

The `.github/instructions/terraform.instructions.md` file uses the newest stable major versions in all provider version constraint examples.

**Current versions as of 2026-02-04:**

| Provider | Example Constraint | Current Stable |
| --- | --- | --- |
| AWS | `~> 6.0` | 6.31.0 |
| Azure | `~> 4.0` | 4.58.0 |
| GCP | `~> 7.0` | 7.18.0 |

**Rationale:**

1. **Best practice demonstration**: Examples should show current recommended practices, not outdated patterns.

2. **Reduces adopter confusion**: Using current versions prevents questions like "why does the template use AWS provider 5.x when 6.x is current?"

3. **Forward-compatible constraints**: The pessimistic constraint operator (`~>`) allows minor/patch updates within the major version, so examples remain valid until the next major version release.

**Trade-offs:**

- Requires periodic review to update when new major versions become the recommended stable release
- Examples may reference features not available in older provider versions (mitigated by the pessimistic constraint allowing updates)

**When to update:**

- When a new major version becomes the recommended stable release (not just released, but recommended for production use)
- When significant new features change best practices (e.g., a new authentication pattern becomes standard)
- As part of quarterly maintenance reviews

### Design Decision: Terraform Instructions Document Length Strategy

The `.github/instructions/terraform.instructions.md` file is intentionally comprehensive (~195KB) rather than split into multiple smaller files.

**Rationale:**

1. **Single source of truth**: All Terraform coding standards in one location eliminates questions about which file to consult.

2. **LLM optimization**: The file is designed to be consumed by GitHub Copilot and similar LLMs. A single comprehensive file provides complete context without requiring the LLM to navigate between files or potentially miss relevant guidance.

3. **Consistency with Terraform ecosystem**: HashiCorp's own Terraform documentation and style guides tend toward comprehensive single documents rather than fragmented collections.

**Discoverability mitigations already in place:**

- **Quick Reference Checklist**: A complete checklist near the top provides a scannable summary of all requirements
- **Scope tags**: Each checklist item is tagged with `[All]`, `[Module]`, `[Root]`, or `[Test]` for quick filtering
- **Comprehensive Table of Contents**: Full ToC with anchor links for navigation
- **Consistent heading structure**: Three-level hierarchy (section → topic → detail) for predictable navigation

**Alternative considered:** Split into multiple files (e.g., `terraform-formatting.md`, `terraform-modules.md`, `terraform-testing.md`)

**Rejected because:**

- Creates navigation burden for both humans and LLMs
- Increases maintenance burden (cross-file consistency, duplicate content, broken links)
- The Quick Reference Checklist already provides the "summary view" that splitting would attempt to create
- No evidence that document length impairs usability given existing navigation aids

### Design Decision: Instruction Files Scope (Code Authoring, Not CI/CD)

Instruction files in `.github/instructions/` are scoped to **code authoring standards**, not CI/CD pipeline design or deployment workflows.

**Rationale:**

1. **Clear purpose**: Instruction files are for GitHub Copilot and developers writing code, not for DevOps engineers designing pipelines.

2. **Separation of concerns**: CI/CD configuration lives in `.github/workflows/` where it can be versioned, tested, and maintained independently of coding standards.

3. **Consistency across languages**: All instruction files (Python, PowerShell, Terraform, Markdown) follow this scope boundary, making the pattern predictable.

4. **LLM context optimization**: Keeping instruction files focused on code authoring prevents context pollution with operational details that would distract from the primary task of writing code.

**What instruction files cover:**

- Syntax, formatting, and style rules
- Naming conventions
- File organization and structure
- Testing patterns (unit tests, integration tests, test file conventions)
- Security patterns in code (input validation, secret handling in code)
- Documentation standards (docstrings, comments, README patterns)

**What instruction files do NOT cover:**

- CI/CD pipeline design (workflow triggers, job dependencies, runner selection)
- Deployment workflows (approval gates, environment promotion, rollback procedures)
- Drift detection and remediation procedures
- Operational runbooks

**Where CI/CD guidance lives:**

- `.github/workflows/` — Workflow files with inline comments explaining design choices
- `DESIGN_DECISIONS.md` — The "CI Workflow Configuration" section documents CI/CD design decisions
- `README.md` — High-level overview of available workflows and their purposes

---

## Node.js Package Configuration

### Design Decision: package.json Minimal Configuration

The template ships with minimal package.json configuration (no repository field, no engines field, generic metadata) to reduce template adoption friction.

**Rationale:**

1. **Reduces friction**: Most users only need dev tooling (markdownlint scripts) without Node.js runtime dependencies.

2. **Prevents placeholder sprawl**: Unlike OWNER/REPO placeholders that break functionality if not replaced, missing optional fields don't affect usage.

3. **Clear separation**: Dev tooling (present) vs. application code (user adds).

4. **Private by default**: The `"private": true` flag means omitted fields like repository don't affect npm publishing.

**Trade-offs:**

- Users creating Node.js applications must manually add metadata fields
- No validation for Node.js version requirements
- Users must consult README for customization guidance

---

## CI Workflow Configuration

### Design Decision: Non-Blocking Type Checking by Default

The template uses `continue-on-error: true` for the mypy type checking job. This is a deliberate choice for template portability.

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

1. No type checking at all: Rejected because mypy provides value even when non-blocking (developers can see errors and fix them opportunistically)

2. Strict by default with documentation to make it lenient: Rejected because this inverts the adoption experience—failing CI on first push is a poor template UX

3. Conditional based on repository variable: Rejected as over-engineering for a simple toggle that adopters can easily change

**When downstream repos should make this strict:**

- After achieving reasonable type coverage (70%+ of public APIs)
- Before releasing stable versions (1.0+)
- When the team has committed to maintaining type annotations
- For libraries where type hints are part of the API contract

### Design Decision: Placeholder Check Workflow Behavior

The placeholder check workflow (`.github/workflows/check-placeholders.yml`) runs automatically in all repositories created from this template. It does NOT run in the template repository itself.

**Implementation:**

```yaml
if: github.repository != 'franklesniak/copilot-repo-template'
```

**This means:**

- ✅ Zero configuration required for adopters
- ✅ Workflow activates automatically on first push/PR
- ✅ Template maintainers don't get spurious failures

**Historical Context:**

Previous versions of this template required setting a `TEMPLATE_INITIALIZED` repository variable to enable the workflow. This was changed because automatic behavior reduces adoption friction and eliminates the "forgot to configure" failure mode. The repository-name-based skip gate provides the same protection without requiring user action.

### Design Decision: Documentation Strategy for Issue Templates

Issue template design rationale is documented in this guide, not in extensive inline YAML comments.

**Rationale:**

- **Reduces duplication**: Design decisions apply across multiple templates; documenting once prevents inconsistency
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

## Python Configuration

### Design Decision: Python Dependency Version Alignment

The root `pyproject.toml` uses the same pytest version (>=8.0.0) as the template file (`templates/python/pyproject.toml`). This is a deliberate choice for template clarity and consistency.

**Rationale:**

1. **Single source of truth**: The root `pyproject.toml` serves both as CI configuration AND as a working example for template users. Using current best-practice versions demonstrates the intended configuration.

2. **Reduces confusion**: When template consumers compare the root `pyproject.toml` to `templates/python/pyproject.toml`, consistent versions eliminate questions about which version to use.

3. **Current stable version**: pytest 8.0+ is the current stable version as of January 2026, with significant improvements over pytest 7.x including better assertion introspection, improved output formatting, and enhanced plugin support.

4. **Template portability**: Template adopters can use either file as reference without needing to reconcile version differences.

**Trade-offs:**

- Slightly higher minimum version requirement than strictly necessary for CI to pass
- May require newer Python environments (pytest 8.0 requires Python 3.8+)

**Alternatives considered:**

- Using pytest>=7.0 in root for minimal CI requirements: Rejected because it creates inconsistency between root and template files, leading to adopter confusion.

---

## Security and Vulnerability Reporting

### Design Decision: Private Vulnerability Reporting Availability

Private vulnerability reporting via GitHub Security Advisories is ONLY available for PUBLIC repositories on GitHub.com. This is a GitHub platform limitation, not a template configuration choice.

**Rationale:**

- GitHub's private vulnerability reporting feature requires the repository to be publicly accessible so that external security researchers can submit reports
- Private repositories cannot receive external vulnerability reports because external users cannot access the Security tab
- This affects all GitHub.com repositories; GitHub Enterprise Server (GHES) may have different availability depending on version and licensing

**Implications for template adopters:**

1. If repository will remain private permanently: Remove GitHub Advisories option, use email-only approach
2. If repository is private now but will become public later: Keep both options, document that Advisories will work once public
3. If repository is already public: All options work as documented

**Trade-offs:**

- Pro: Template provides guidance for all repository visibility scenarios
- Pro: Prevents confusion when "Report a vulnerability" link doesn't work
- Con: Additional complexity in adoption documentation
- Con: Adopters must make visibility-dependent decisions during setup

---

## License Configuration

### Design Decision: MIT License as Template Default

This template uses the MIT License as its default because:

1. **Minimal friction**: MIT is one of the most permissive and widely-understood licenses
2. **Template portability**: Works for both open source and commercial projects (with modification)
3. **Simplicity**: Short, clear terms that don't require legal expertise to understand
4. **Compatibility**: Compatible with most other open source licenses

**Trade-offs:**

- Pro: Maximum adoption potential due to permissive terms
- Pro: Simple contributor agreement (no CLA needed for most cases)
- Pro: Widely recognized in enterprise and open source communities
- Con: Provides no patent protection (unlike Apache 2.0)
- Con: No copyleft protection (unlike GPL)
- Con: Proprietary projects must replace with appropriate license

**Alternatives considered:**

1. Apache 2.0 as default: Rejected because patent grant clause can be unfamiliar to some adopters and adds complexity for simple projects
2. No default license: Rejected because unlicensed code is legally unusable; providing a permissive default is better than no default
3. Dual licensing (MIT + Apache 2.0): Rejected as over-engineering for a template

**Recommendation:**

Most open source projects can keep MIT. Consider Apache 2.0 for projects involving patents. Proprietary projects MUST replace the license entirely.

---

## Dependabot Configuration

### Design Decision: Dependabot Enabled by Default

Dependabot is enabled by default in this template repository to provide automated dependency security monitoring and update management. This configuration represents security-conscious defaults that align with best practices for modern software projects.

**Rationale:**

- Security vulnerabilities in dependencies are automatically detected and PRs created
- Reduces maintenance burden for keeping dependencies current with security patches
- Template repositories should model best practices; security-conscious defaults are appropriate
- Monitors all three dependency ecosystems used by this template: npm, pip, and GitHub Actions
- Weekly schedule with grouped minor/patch updates balances security with reduced PR noise

**Trade-offs:**

- Pro: Automated security vulnerability detection and remediation
- Pro: Keeps dependencies current without manual monitoring
- Pro: Reduces risk of using outdated, vulnerable packages
- Pro: Grouped updates reduce PR noise for minor/patch versions
- Con: Creates PR noise for minor updates that adopters may not want
- Con: Adopters who prefer manual dependency management must disable it
- Con: May suggest updates that require testing/validation before merging

**Recommendation:**

Keep Dependabot enabled unless you have a specific reason to manage dependencies manually or use an alternative tool (e.g., Renovate). If the PR volume is too high, consider adjusting the schedule from weekly to monthly, or customizing the grouping configuration. Delete `.github/dependabot.yml` to disable entirely.

---

## CODEOWNERS Configuration

### Design Decision: CODEOWNERS with Placeholder

The template includes a CODEOWNERS file with `@OWNER` placeholders that template adopters must replace. This file enables automatic review request assignment for pull requests and documents code ownership.

**Rationale:**

- CODEOWNERS enables automatic review requests for PRs affecting specific paths
- Works well with branch protection rules requiring code owner approval
- Using `@OWNER` placeholder follows the existing `OWNER/REPO` pattern in this template
- Placeholder check workflow ensures adopters don't forget to customize
- Default rules cover repository root, workflows, and Copilot instructions

**Trade-offs:**

- Pro: Automatic PR review assignment reduces manual reviewer selection
- Pro: Documents code ownership explicitly in the repository
- Pro: Works with branch protection "required reviews from code owners" setting
- Pro: Placeholder check workflow ensures customization before use
- Con: Requires placeholder replacement during template adoption
- Con: Solo maintainers may not benefit from CODEOWNERS
- Con: Adds another file to the template adoption checklist

**Recommendation:**

Replace `@OWNER` with your GitHub username or team name (e.g., `@octocat` or `@my-org/maintainers`). For solo projects, you may delete the file if automatic review assignment is not needed. For team projects, CODEOWNERS is highly recommended to ensure consistent review practices.

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

**ACTION ITEM:** If you want to use a `triage` label, you must first create it in your repository (it doesn't exist by default). The `triage` label cannot be auto-created when cloning a template repository—GitHub does not support this.

#### Field IDs

Templates use `snake_case` for all field IDs (e.g., `steps_to_reproduce`, `operating_system`). Maintain this convention when adding new fields for consistency.

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

The placeholder shows multiple runtime examples rather than a single language example, using currently-supported version numbers.

**Rationale:**

- Template supports Python, PowerShell, and Markdown-focused projects
- Multi-line examples help reporters provide complete information
- **Placeholder examples should use currently-supported versions** for consistency with project policy (e.g., Python 3.13+ aligns with template's Python version policy)
- Using exact version format (not vague `.x`) demonstrates correct format
- Downstream repos should customize to match their supported runtimes

#### how_ran Placeholder Format

The placeholder shows detailed, multi-step installation examples rather than brief one-liners, including both `pyproject.toml` and `requirements.txt` workflows.

**Rationale:**

- Shows both `pyproject.toml` and `requirements.txt` workflows (template portability)
- Demonstrates best practices (venv creation, activation)
- Helps reporters provide complete reproduction steps
- Supports diverse downstream adopter workflows
- Doesn't lock adopters into a single dependency management approach

**Alternative considered:** Brief form with multiple options on same line

**Rejected because:**

- Compressed form is harder to parse visually
- Doesn't demonstrate best practices (venv setup, activation)
- Less helpful for users unfamiliar with Python dependency management

#### Area Dropdown - No "I don't know" Option

The Area dropdown does NOT include an "I don't know / not sure" option.

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

This template intentionally includes multiple security warnings (top-of-form notice, required checkbox, severity dropdown warning).

**Why keep all three:**

- **Different interaction patterns:** Some users skim headers (→ checkbox catches them), some focus on dropdowns (→ severity warning catches them). Multiple touchpoints maximize chance of catching accidental public disclosure.
- **High stakes, low cost:** Cost of redundancy is slightly longer form. Cost of failure is public disclosure of security vulnerability. Risk/reward strongly favors redundancy.
- **Template portability:** Downstream adopters can easily remove warnings if desired. Harder to add them back if not provided. Template should err on side of caution.
- **Audit trail:** Required checkbox provides explicit acknowledgment.

**Alternative considered:** Remove severity dropdown warning text, keep top warning + checkbox.

**Rejected because:**

- Severity dropdown is where users actively interact (making selection)
- Warning at point of interaction provides contextual reminder
- Consistency with documented design decision (no compelling reason to change)

### feature_request.yml

#### Area Dropdown Consistency

The Area dropdown options match `bug_report.yml` for consistency. Update both templates when modifying area categories.

#### Priority vs Scope

The template separates priority (urgency from reporter's perspective) and scope (size of the feature). Both are optional and self-assessed by reporters; maintainers may adjust during triage.

### documentation_issue.yml

#### No Area Dropdown by Default

This template intentionally does NOT include an `area` dropdown field.

**Rationale:**

- Most consumers have simple documentation sets that don't require area routing
- Keeping the template lean encourages drive-by documentation reports
- Documentation issues are typically easy to locate via the `location` field

#### Location Field Optional

**Trade-off:**

- Optional (current): Encourages drive-by typo reports with lower friction
- Required: More actionable for maintainers; may reduce submissions

Recommendation: Keep optional but encourage providing location via description text.

### config.yml

#### blank_issues_enabled

Set to `true` for flexibility (allows any issue format), or `false` to enforce template usage. Most projects benefit from `true` initially; consider `false` once you have comprehensive templates.

#### contact_links URL Requirement

**Critical:** Unlike issue-form markdown blocks (where relative links work), `contact_links` URLs MUST be absolute URLs. There is no way to use relative links here.

- You MUST replace `OWNER/REPO` with your actual org/repo
- Use `blob/HEAD` instead of `blob/main` to support non-main default branches

#### GitHub Enterprise Server (GHES) Portability

GHES host replacement is documented in comments, not enforced via placeholders.

**Rationale:**

- GHES users universally know their host (appears in every URL)
- One-line note in "MUST READ" section is sufficient
- Avoids placeholder proliferation (simpler adoption)
- No CI validation needed for host placeholder

#### Security Link Documentation

Detailed setup instructions remain in comments, not in user-facing `about` text.

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

## Branch Protection Setup

This section documents how to configure branch protection using the CI workflows provided by this template.

### Design Decision: Branch Protection Documentation

This template includes documentation for branch protection setup rather than attempting to configure it automatically. Branch protection is a repository setting that cannot be included in template repositories, so documentation is the appropriate way to guide adopters.

**Rationale:**

- Helps adopters set up proper CI gates for their default branch
- Explains the intended use of CI workflows and how they relate to branch protection
- Documents which CI jobs are good candidates for required status checks
- Clarifies the relationship between `needs:` dependencies and branch protection

**Trade-offs:**

- Pro: Helps adopters set up proper CI gates quickly
- Pro: Explains intended use of CI workflows from this template
- Pro: Clarifies complementary nature of CI dependencies vs branch protection
- Con: GitHub UI may change over time, requiring documentation updates
- Con: Cannot be enforced via template (requires manual setup in each repository)
- Con: Adopters must manually configure settings in GitHub UI

**Recommendation:**

Configure branch protection for your default branch after initial repository setup. At minimum, require the pre-commit check to pass before merging. For additional protection, also require downstream checks like tests and type checking.

### CI Jobs Available as Required Status Checks

The template provides these CI jobs that can be configured as required status checks:

| Workflow | Job Name | Recommended as Required | Notes |
| --- | --- | --- | --- |
| `python-ci.yml` | **Pre-commit** | ✅ Yes | Foundational check—catches formatting and linting issues |
| `python-ci.yml` | **Type Check (mypy)** | Optional | Set to `continue-on-error: true` by default; make strict when ready |
| `python-ci.yml` | **Test** | ✅ Yes | Ensures tests pass on all platforms |
| `markdownlint.yml` | **Markdown Lint** | ✅ Yes | Ensures documentation quality |
| `powershell-ci.yml` | **lint** | Optional | Only if using PowerShell |
| `powershell-ci.yml` | **PowerShell Tests (Pester)** | Optional | Only if using PowerShell with tests |

**Note:** Job names must match exactly as they appear in the GitHub Actions UI. The names listed above are the exact job names from the template workflows.

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

**Recommendation:** Require **both** the `Pre-commit` job AND downstream jobs like `Test` in branch protection. Even though `Test` won't run if `Pre-commit` fails (due to `needs:`), requiring both ensures that:

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

---

## Document Maintenance

This document should be updated when:

- New design decisions are made that affect template structure or behavior
- Existing design decisions are revised based on new information or feedback
- Design decisions are superseded by new approaches

When adding new design decisions, follow the established format:

1. Add a heading with the pattern `### Design Decision: [Topic]`
2. Explain the rationale and trade-offs
3. Document alternatives considered and why they were rejected
4. Include recommendations where appropriate
