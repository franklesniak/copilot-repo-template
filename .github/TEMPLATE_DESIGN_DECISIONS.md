<!-- markdownlint-disable MD013 -->

# Template Design Decisions

## Metadata

- **Status:** Active
- **Owner:** Repository Maintainers
- **Last Updated:** 2026-06-21
- **Scope:** Durable design-decision record for this repository template, including rationale for GitHub configuration, instruction files, validation policy, template structure, maintenance conventions, and the documentation-tier inventory below.
- **Related:** [Repository Copilot Instructions](copilot-instructions.md), [Documentation Writing Style](instructions/docs.instructions.md)

This document records design decisions made during the creation and maintenance of `franklesniak/copilot-repo-template`. It serves as institutional memory to prevent re-litigation of settled decisions during code review.

> **For consumers of this template:** This document is NOT an instruction guide. See [GETTING_STARTED_NEW_REPO.md](../GETTING_STARTED_NEW_REPO.md) or [GETTING_STARTED_EXISTING_REPO.md](../GETTING_STARTED_EXISTING_REPO.md) for setup instructions, and [OPTIONAL_CONFIGURATIONS.md](../OPTIONAL_CONFIGURATIONS.md) for customization options.

---

## Table of Contents

- [File Placement](#file-placement)
- [Pull Request Template](#pull-request-template)
- [Pre-commit and Git Hooks](#pre-commit-and-git-hooks)
  - [Cross-Platform Local Terraform Pre-Commit Wrappers](#design-decision-cross-platform-local-terraform-pre-commit-wrappers)
- [Coding Standards and Instructions](#coding-standards-and-instructions)
  - [Current Provider Versions in Terraform Examples](#design-decision-current-provider-versions-in-terraform-examples)
  - [Terraform Instructions Document Length Strategy](#design-decision-terraform-instructions-document-length-strategy)
  - [Instruction Files Scope (Code Authoring, Not CI/CD)](#design-decision-instruction-files-scope-code-authoring-not-cicd)
  - [Terraform Registry Reference URLs Use /latest/](#design-decision-terraform-registry-reference-urls-use-latest)
- [Agent Instruction Files](#agent-instruction-files)
  - [Multi-Agent Instruction Files at Repository Root](#design-decision-multi-agent-instruction-files-at-repository-root)
  - [Agent Files as Minimal Entry-Point Summaries (Not Canonical)](#design-decision-agent-files-as-minimal-entry-point-summaries-not-canonical)
  - [Reference-Only Template-Sync Blocks for Retained Shared Documents](#design-decision-reference-only-template-sync-blocks-for-retained-shared-documents)
- [Data File Standards (JSON/YAML)](#data-file-standards-jsonyaml)
  - [Parity Status](#parity-status)
  - [Dedicated JSON and YAML Instruction Files](#design-decision-dedicated-json-and-yaml-instruction-files)
  - [Baseline JSON/YAML Linting Stack](#design-decision-baseline-jsonyaml-linting-stack)
  - [yamllint truthy.check-keys Default](#design-decision-yamllint-truthycheck-keys-default)
  - [yamllint line-length Warning Level Default](#design-decision-yamllint-line-length-warning-level-default)
  - [Prettier Deferral for Data Files](#design-decision-prettier-deferral-for-data-files)
  - [Schema Location at Repository Root](#design-decision-schema-location-at-repository-root)
  - [Schema Validation Tiers](#design-decision-schema-validation-tiers)
  - [Built-in Schema Validation for Real Load-Bearing Configuration Files](#design-decision-built-in-schema-validation-for-real-load-bearing-configuration-files)
  - [JSON5 Exclusion by Default](#design-decision-json5-exclusion-by-default)
  - [`additionalProperties` Policy](#design-decision-additionalproperties-policy)
  - [Testing Beyond Linting for JSON/YAML](#design-decision-testing-beyond-linting-for-jsonyaml)
  - [.gitattributes LF Pinning for Template-Managed Text](#design-decision-gitattributes-lf-pinning-for-template-managed-text)
- [Template Sync](#template-sync)
  - [Manifest v2 Path-Mapping Relations](#design-decision-manifest-v2-path-mapping-relations)
- [Node.js Package Configuration](#nodejs-package-configuration)
- [CI Workflow Configuration](#ci-workflow-configuration)
- [Python Configuration](#python-configuration)
- [Security and Vulnerability Reporting](#security-and-vulnerability-reporting)
- [License Configuration](#license-configuration)
- [Dependabot Configuration](#dependabot-configuration)
  - [Workflow Version Pinning and Dependabot Coherence](#design-decision-workflow-version-pinning-and-dependabot-coherence)
  - [Dependabot Enabled by Default](#design-decision-dependabot-enabled-by-default)
- [CODEOWNERS Configuration](#codeowners-configuration)
- [Issue Template Design Decisions](#issue-template-design-decisions)
- [Branch Ruleset Setup](#branch-ruleset-setup)
- [Documentation Tier Inventory](#documentation-tier-inventory)

---

## File Placement

### Design Decision: TEMPLATE_DESIGN_DECISIONS.md Location

This file is placed in `.github/` because it is GitHub-specific configuration guidance that relates directly to other files in this directory (pull_request_template.md, ISSUE_TEMPLATE/, workflows/, etc.). Keeping it here makes it discoverable alongside the files it documents and ensures template maintainers encounter it when exploring GitHub configuration. This is preferable to `docs/` (general project documentation) or the repo root (which should remain clean for end users).

---

## Pull Request Template

### Design Decision: Contributing Guidelines Link

> **Status: Superseded** (2026-05-03). This decision has been replaced by the **Issue and PR templates** carve-out in [`.github/instructions/docs.instructions.md`](instructions/docs.instructions.md), which requires absolute `https://github.com/OWNER/REPO/...` URLs in `.github/ISSUE_TEMPLATE/*.yml` and `.github/pull_request_template.md` — `https://github.com/OWNER/REPO/blob/HEAD/<path>` for repo-internal **file** targets and `https://github.com/OWNER/REPO/<other-path>` for non-file targets such as `/security`, `/discussions`, or `/issues`. The original rationale (zero-friction adoption via relative links) was weakened once `.github/workflows/check-placeholders.yml` began enforcing `OWNER/REPO` replacement automatically, and the relative-link pattern is fragile across non-GitHub.com renderers, GitHub Mobile, and email notifications. The historical content is preserved below for context.

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
`https://github.com/<owner>/<repo>/blob/HEAD/CONTRIBUTING.md` (remembering to replace `<owner>/<repo>` with your actual org/repo name).

### Design Decision: Link Strategy in PR Template

> **Status: Superseded** (2026-05-03). This decision has been replaced by the **Issue and PR templates** carve-out in [`.github/instructions/docs.instructions.md`](instructions/docs.instructions.md). The current rule is that Markdown links to repo-internal files inside `.github/ISSUE_TEMPLATE/*.yml` and `.github/pull_request_template.md` MUST use absolute `https://github.com/OWNER/REPO/blob/HEAD/<path>` URLs; relative forms such as `../blob/HEAD/<file>` and `blob/HEAD/<file>` MUST NOT be used in those files. The historical content is preserved below for context.

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

### Design Decision: Cross-Platform Local Terraform Pre-Commit Wrappers

The template uses repo-local Python wrappers for active Terraform pre-commit hooks instead of `antonbabenko/pre-commit-terraform` shell hooks.

**Decision:**

- `.pre-commit-config.yaml` defines `repo: local` hooks named `terraform-fmt`, `terraform-validate`, and `terraform-tflint`.
- The hooks call `.github/scripts/terraform_hooks.py`, which invokes Terraform and TFLint through `subprocess.run(..., shell=False)`.
- Executable discovery uses `shutil.which` and fails with actionable installation guidance when required tools are missing.
- HashiCorp Terraform (`terraform`) is required; the template does not add an OpenTofu fallback.
- TFLint (`tflint`) is required when Terraform lint targets are present.

**Rationale:**

1. **Native Windows support is required.** POSIX shell hook scripts can fail before Terraform runs when native Windows paths are routed through the wrong Bash implementation. Python avoids that path-translation layer and works from PowerShell, Git Bash, WSL/Linux, macOS, and Linux.

2. **Python is already in the local validation path.** Pre-commit itself and multiple existing hooks already require Python. A small stdlib-only wrapper reuses that dependency class rather than adding PowerShell, container, or additional runtime requirements.

3. **Local behavior mirrors CI.** The format hook runs `terraform fmt -check -recursive -diff` from the repository root. Validation discovers directories containing `.tf` files and runs `terraform init -backend=false` followed by `terraform validate`. TFLint runs `tflint --init` and `tflint --recursive --config <repo-root>/.tflint.hcl`.

4. **Missing tools fail clearly.** When matching Terraform targets exist and `terraform` or `tflint` is absent from PATH, the wrapper reports the missing executable and points to installation guidance instead of surfacing Bash/path-loss errors.

**Alternatives considered:**

- **Continue using `pre-commit-terraform`.** Rejected because its active hooks are POSIX shell scripts and do not provide reliable native Windows / PowerShell execution in this repository's observed environment.
- **PowerShell wrappers.** Rejected because PowerShell is not a universal dependency for macOS/Linux contributors and would create a second shell-specific path.
- **Container-based hooks.** Rejected because requiring Docker or another container runtime would add substantial local setup burden for a template repository.
- **Documentation-only workaround.** Rejected because asking Windows users to reorder Bash implementations does not provide deterministic local validation.

**Consequences:**

- `pre-commit autoupdate` no longer updates Terraform hook behavior because the hooks are local. Maintainers must review `.github/scripts/terraform_hooks.py`, `tests/test_terraform_hooks.py`, `.pre-commit-config.yaml`, and aggregate pre-commit workflows together when Terraform validation behavior changes.
- CI workflows that run aggregate pre-commit must install both Terraform and TFLint so downstream repositories with `.tf` files can run the same hooks.
- The downstream copy of `.github/instructions/terraform.instructions.md` remains sourced from `franklesniak/TerraformStyleGuide` and is not modified directly for this policy. If generalized style-guide wording is desired, file it upstream.

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
- `.github/TEMPLATE_DESIGN_DECISIONS.md` — The "CI Workflow Configuration" section documents CI/CD design decisions
- `README.md` — High-level overview of available workflows and their purposes

### Design Decision: Terraform Registry Reference URLs Use /latest/

Terraform Registry reference URLs that appear in **comments** in `.tf`, `.tftest.hcl`, `.tfvars`, `.tfbackend`, `.tftpl`, and other Terraform-related files **MUST** use the `latest` path segment instead of a pinned provider or module version. The same `/latest/` requirement applies to any Terraform Registry navigation links in instructional Markdown under this template (currently those in [`TEMPLATE_MAINTENANCE.md`](../TEMPLATE_MAINTENANCE.md); the same convention would apply to any future Registry links in other Markdown documentation under this template, including under `docs/`). The Markdown half of the rule is binding via this ADR rather than via an `applyTo`-scoped instruction file: the canonical instruction file [`terraform.instructions.md`](instructions/terraform.instructions.md) is scoped to Terraform extensions only, and the convention has not yet been mirrored into `docs.instructions.md` (which governs `**/*.md`). Because the repository's auto-apply mechanism is limited to `.github/instructions/*.instructions.md` files with `applyTo` front matter, the rule is *not* auto-surfaced to an agent editing a pure Markdown file; until the convention is codified into a Markdown-scoped instruction file, a maintainer or task description has to point at this ADR for the agent to apply it.

The shape of the rule is:

- Provider URLs use `latest` immediately after `/providers/<namespace>/<name>/`, with any trailing path, query string, or fragment, or none — for example, `https://registry.terraform.io/providers/hashicorp/aws/latest` or `.../latest/docs/resources/...`.
- Module URLs use `latest` immediately after `/modules/<namespace>/<name>/<provider>/`, with any trailing path, query string, or fragment, or none — for example, `https://registry.terraform.io/modules/terraform-aws-modules/vpc/aws/latest` or `.../latest/submodules/...`.
- Pinned examples such as `/azurerm/4.67.0/` or `/random/3.8.1/` **MUST NOT** appear in either Terraform-file documentation comments or instructional Markdown under this template, except as clearly labeled non-compliant examples that exist to document this rule.

For Terraform-file comments, the full normative rule (with compliant and non-compliant examples) lives in [`.github/instructions/terraform.instructions.md`](instructions/terraform.instructions.md) under "Terraform Registry Documentation URLs"; that file is loaded automatically when an agent edits a Terraform file. For instructional Markdown, this ADR is the binding statement until the convention is mirrored into `docs.instructions.md` or a separate `applyTo`-scoped instruction file. This ADR records *why* the template adopts the rule and how it spans Terraform comments and Markdown today; the Terraform instruction file remains the single source of truth for *what* the rule says inside Terraform files.

**Rationale:**

1. **Registry URLs in comments are navigation aids, not version pins.** The provider and module versions that actually drive `terraform init`, `terraform plan`, and `terraform apply` are governed by `required_providers` blocks in `terraform.tf` / `versions.tf` and by `.terraform.lock.hcl` for *providers*, and by module `source` and `version` arguments for *modules* (`.terraform.lock.hcl` does not record module versions). Those files are the authoritative version sources. Comment URLs only help a reader (or an AI assistant) jump to relevant Registry documentation while reading the code.

2. **Version updates do not rewrite arbitrary comment text.** When provider versions advance, maintainers (or, when configured, dependency automation such as Dependabot or Renovate) update `required_providers` constraints and `.terraform.lock.hcl`; when module versions advance, maintainers update the module `version` argument. None of these update paths parses Markdown prose or arbitrary `.tf` comments to find embedded Registry URLs, so a pinned URL such as `/providers/<namespace>/<name>/<pinned-version>/docs/...` stays at `<pinned-version>` in the comment even after the underlying constraint, lockfile entry, or `version` argument has moved on. (At the time this ADR was recorded, this template's [`.github/dependabot.yml`](dependabot.yml) does not configure Terraform-ecosystem updates, so the entire update path here is currently manual; the rationale still applies if Terraform automation is added later.)

3. **Pinned URLs in comments drift silently.** Once the executable configuration moves past the version embedded in a comment URL, the comment points at outdated documentation. Readers can be sent to deprecated argument descriptions, removed resources, or release-note pages that no longer reflect the configuration's actual behavior. Because nothing in CI mechanically reconciles comment URLs against the underlying version sources (`.terraform.lock.hcl` for providers, module `version` arguments for modules), the drift is invisible until a human notices it.

4. **`latest` matches the navigation-aid intent.** Linking to `/providers/<namespace>/<name>/latest/docs/...` (or `/modules/<namespace>/<name>/<provider>/latest` for modules) always resolves to the current Registry documentation, which is what a reader navigating from a comment generally wants. If a reader needs documentation that matches a specific pinned version, they can look up the version in `.terraform.lock.hcl` (for providers) or in the module `source` / `version` arguments (for modules) and adjust the URL by hand; comment URLs do not need to duplicate that capability.

**Trade-offs:**

- Readers who want documentation pinned to the exact version recorded in `.terraform.lock.hcl` (for providers) or in module `source` / `version` arguments (for modules) need to take an extra step (look up the lockfile or module block entry and adjust the URL by hand). The alternative — pinning every comment URL — was rejected because the silent-drift cost outweighs the convenience for that minority case.
- Clearly labeled non-compliant examples in the Terraform instruction file intentionally include pinned URLs so the rule itself can be illustrated. Tooling that enforces this rule in the future must distinguish those documentation examples from real violations.

**Scope boundary:**

This ADR governs only documentation-comment URLs and Markdown navigation links to the Terraform Registry. It does **not** change:

- Provider version constraints in `required_providers` blocks.
- Module `source` addresses or `version` arguments.
- Entries in `.terraform.lock.hcl`.
- Any other intentionally pinned executable configuration.

Those remain governed by their existing rules and by the relevant maintenance guidance in [`TEMPLATE_MAINTENANCE.md`](../TEMPLATE_MAINTENANCE.md).

**Enforcement:**

This template intentionally does not ship a pre-commit hook or custom lint rule for this convention at the time the decision was recorded. Adding mechanical enforcement would require carefully distinguishing real violations from the clearly labeled non-compliant examples in the Terraform instruction file (and any future similar examples in Markdown), and would need to handle both provider and module URL shapes. If enforcement is added later, it will be designed in a separate, dedicated change rather than rolled into the documentation/design-decision update that introduced this ADR.

---

## Agent Instruction Files

### Design Decision: Multi-Agent Instruction Files at Repository Root

The template includes three agent-specific instruction files at the repository root: `CLAUDE.md` (for Claude Code), `AGENTS.md` (for OpenAI Codex CLI), and `GEMINI.md` (for Gemini Code Assist).

**Rationale:**

1. **Multi-agent coverage**: AI coding agents other than GitHub Copilot (Claude Code, OpenAI Codex CLI, Gemini Code Assist) use their own convention files and do not read `.github/copilot-instructions.md` or `.github/instructions/*.instructions.md`.

2. **Enriches GitHub Copilot**: GitHub Copilot's coding agent reads `CLAUDE.md`, `AGENTS.md`, and `GEMINI.md` as supplemental agent instructions, so adding these files enriches Copilot as well.

3. **Template mission alignment**: The template's mission is to provide coding standards for AI-assisted development—limiting to a single AI platform contradicts this mission.

4. **Minimal entry-point summaries**: Agent files keep only a minimal inline summary of the highest-priority shared rules from `.github/copilot-instructions.md`, rather than restating the full canonical document. This avoids multiple sources of truth while preserving reliable first-read guidance.

**Trade-offs:**

- Pro: All major coding agents receive project-specific guidance
- Pro: GitHub Copilot coding agent receives enriched context from additional files
- Pro: Template adopters can delete files for platforms they don't use
- Con: Three additional files at the repository root
- Con: Manual alignment burden when high-priority shared guidance changes in `.github/copilot-instructions.md`
- Con: No CI enforcement for alignment between the canonical file and the agent entry points

**Alternatives considered:**

1. **Single `AGENTS.md` only:** Rejected because Claude Code reads only `CLAUDE.md` and Gemini reads only `GEMINI.md`—a single file does not cover all agents.

2. **Symlinks from agent files to `.github/copilot-instructions.md`:** Rejected because agent files need a small amount of inline guidance for reliability, and symlinks may not work correctly on all platforms or in all agent runtimes.

3. **No agent files (Copilot-only):** Rejected because it contradicts the template's mission of supporting AI-assisted development broadly.

**Recommendation:** Keep all three files unless your project exclusively uses one AI coding agent. Delete files for platforms you do not use. When modifying high-priority shared guidance in `.github/copilot-instructions.md`, update the remaining agent files so their minimal summaries stay accurate.

### Design Decision: Agent Files as Minimal Entry-Point Summaries (Not Canonical)

Agent instruction files (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`) are minimal entry-point summaries of `.github/copilot-instructions.md`, not independent canonical sources.

**Rationale:**

1. **Single source of truth**: `.github/copilot-instructions.md` is the established single source of truth for repository coding standards.

2. **Avoids divergence**: Making agent files canonical would create multiple sources of truth that could diverge.

3. **Agent discoverability**: Agent files contain a minimal inline summary of key rules (safety, pre-commit, validation commands, language-instruction pointers) because some agents may only auto-read their convention file and may not reliably follow references to other files without explicit instruction.

4. **DRY vs. discoverability trade-off**: The trade-off between DRY (Don't Repeat Yourself) and agent discoverability favors a small, intentional amount of duplication to ensure agents actually receive the rules.

**Trade-offs:**

- Pro: Single source of truth remains `.github/copilot-instructions.md`
- Pro: Agents that don't follow file references still receive critical rules
- Con: Rule changes require updating multiple files
- Con: No automated enforcement that alignment reviews happen after shared-rule changes

### Design Decision: Reference-Only Template-Sync Blocks for Retained Shared Documents

Retained shared documents may contain `*-reference-only` template-sync blocks around optional-stack references. These blocks coexist with the older `*-only` family instead of replacing it.

**Rationale:**

1. **Different ownership shape**: `*-only` blocks wrap owned configuration or workflow content, such as hooks and CI steps. `*-reference-only` blocks wrap prose, table rows, list items, and links that merely mention optional stacks inside retained protected files or shared baseline docs.

2. **Safer stack pruning**: Downstream adopters can remove Python, Terraform, PowerShell, JSON, YAML, schema, or Markdown references without deleting unrelated required or platform-specific protocol text.

3. **Protocol and baseline preservation**: Agent entry points can remain thin summaries while retaining platform protocol sections, such as Claude review-loop rules and Codex GitHub-plugin/PR-review rules. Baseline docs such as `README.md` and `CONTRIBUTING.md` can keep pre-commit, Markdown, PowerShell, GitHub, no-secrets, PR-readiness, and template-sync guidance while removing references to excluded optional stacks.

**Decision:** Use `*-reference-only` only for textual optional-stack references in retained documents. Continue to use `*-only` for module-owned configuration, workflow, or validation blocks. Both families strip when the corresponding module is absent, but tests must prove protected-file pruning removes only the reference blocks and preserves required protocol headings, and shared baseline doc pruning removes excluded-stack prose without dropping retained contributor-facing guidance.

**Alternatives considered:**

1. **Reuse `*-only` for prose references:** Rejected because it hides the difference between owned module configuration and incidental textual references, making downstream review less precise.

2. **Do not mark protected-file or baseline-doc references:** Rejected because downstream repositories that exclude optional stacks would need broad protected-file and contributor-doc rewrites, increasing the risk of deleting retained platform protocol or baseline contributor guidance.

---

## Data File Standards (JSON/YAML)

These ten ADRs record the design decisions behind the JSON and YAML authoring guides, the baseline linting stack for data files, the schema-validation policy, and the surrounding tooling and portability trade-offs. They are policy-only prose; the implementations live in `.github/instructions/json.instructions.md`, `.github/instructions/yaml.instructions.md`, `.pre-commit-config.yaml`, `.yamllint.yml`, `.gitattributes`, and (for downstream adopters) the optional `schemas/` directory.

### Parity Status

JSON and YAML are treated as equal citizens with the other first-class supported file types in this template (see the **Last Updated** date in the metadata block above for when this status was last reviewed). Parity is enforced across these cross-cutting surfaces:

- Canonical instructions.
- Template starter content.
- PR checklist.
- Getting-started guidance.
- README references.
- Pre-commit and CI validation.
- Schema-example testing.

### Design Decision: Dedicated JSON and YAML Instruction Files

The template ships dedicated instruction files for JSON (`.github/instructions/json.instructions.md`) and YAML (`.github/instructions/yaml.instructions.md`) alongside the existing language instruction files for Python, PowerShell, Terraform, and Markdown.

**Rationale:**

1. **Data files are potentially load-bearing contracts.** JSON and YAML are commonly used as configuration files, lockfiles, fixtures, schemas, CI/CD definitions, and policy documents. Even when a project does not currently rely on a given JSON or YAML file as a contract, downstream consumers (CI, release tooling, deployment automation, schema validators) frequently turn data files into de facto contracts over time. Treating them as potentially load-bearing by default is safer than retrofitting rigor after a silent format break.

2. **Authoring rules differ from prose rules.** Markdown, Python, PowerShell, and Terraform guides cover human-authored or executable content. JSON and YAML guides cover structured data where ordering, key naming, comment policy, schema discipline, and quoting rules matter independently of any host language.

3. **Per-format guidance is non-trivial.** JSON forbids comments and trailing commas while JSONC permits both; YAML has a substantially larger surface area (anchors, tags, the YAML 1.1/1.2 truthy delta, multi-document streams). A single combined guide would either bloat or paper over these differences.

4. **Consistency with the existing modular pattern.** The repo-wide constitution already mandates a modular instruction-file layout under `.github/instructions/`. Adding JSON and YAML files extends — rather than reshapes — the established pattern.

**Trade-offs:**

- Pro: Authors and AI agents get format-specific rules without scanning unrelated guides.
- Pro: Downstream repos can delete either file independently if they truly do not use that format.
- Con: Two more files to keep aligned when shared rules (e.g., schema policy) change.

**Alternatives considered:**

- **Combined `data.instructions.md`:** Rejected. JSON and YAML differ enough on comments, quoting, and truthy semantics that combining them obscured per-format rules in early drafts.
- **No dedicated guides; inline rules in language guides:** Rejected. Most JSON/YAML in this template is not co-located with a single host language (workflows, lockfiles, instruction front matter), so language-specific guides cannot carry the rules.

### Design Decision: Baseline JSON/YAML Linting Stack

The default pre-commit stack for JSON and YAML uses `check-json`, `check-yaml`, `yamllint`, `actionlint`, and `check-jsonschema` plus `check-metaschema` entries scoped to concrete schema-backed file families.

**Selected hooks and their roles:**

1. **`check-json` (pre-commit-hooks)** — Validates strict JSON syntax. Fast, dependency-free, fails on duplicate keys, trailing commas, and other strict-JSON violations.
2. **`check-yaml` (pre-commit-hooks)** — Fast YAML parse check. Catches structural errors before slower linters run.
3. **`yamllint`** — YAML style enforcement (indentation, line length, truthy values). Configured via `.yamllint.yml`.
4. **`actionlint`** — GitHub Actions workflow validation, including expression syntax, runner labels, and `shellcheck` integration over `run:` blocks.
5. **`check-jsonschema` and `check-metaschema`** — JSON Schema validation. These hooks are wired by default with explicit aliases for schema example validation, project-owned schema self-validation, template-sync manifest and marker validation, and Dependabot configuration validation against the built-in `vendor.dependabot` schema. The `.pre-commit-config.yaml` entries are split into schema-owned, joint schema plus template-sync-support, and GitHub-platform-owned repo blocks so downstream repositories can strip module-owned validation without removing unrelated schema checks. Downstream repositories MAY add additional `check-jsonschema` hook entries for their own schema-backed file families. The "Avoid placeholder schema hooks" rule under the Schema Validation Tiers ADR is still in force: the wiring exists because real schemas, examples, and load-bearing configuration files ship in the template, not as placeholders.

**Notable scoping:**

- **`check-json` validates `.json`, not `.jsonc`.** The hook is anchored with `files: \.json$` so JSONC files (which permit comments and trailing commas) are intentionally skipped. Strict-JSON syntax checks would reject any valid JSONC file, producing false positives. Repos that need strict JSONC enforcement should add **JSONC-aware tooling** (e.g., a JSONC parser or a schema validator that understands JSONC) rather than retrofitting `check-json` for files it cannot correctly parse.

**Why `jsonlint` is not added by default:**

- `jsonlint` overlaps with `check-json` for strict JSON syntax and adds a Node-only dependency.
- `check-json` already catches the high-value failure modes (parse errors, duplicate keys) and is part of the broader `pre-commit-hooks` repo already in use.
- Adding `jsonlint` would expand the toolchain for marginal benefit and would not validate JSONC either.

**`actionlint` first-run-on-restricted-networks caveat:**

The `actionlint` pre-commit hook builds the `actionlint` binary from source on first install. On networks that block Go module downloads (corporate proxies, air-gapped environments), the first-run install can fail. CI is the shared enforcement environment, so contributors who hit a network restriction locally can rely on CI to enforce the hook. The same caveat is surfaced in `.pre-commit-config.yaml` (inline comment on the `actionlint` repo block) and `CONTRIBUTING.md` so contributors encounter it where they look first. Keep these cross-references in sync if the hook is repinned, replaced, or removed.

**Trade-offs:**

- Pro: Coverage spans strict syntax, style, and Actions-specific semantics with widely-used, well-maintained hooks.
- Pro: Each hook is independent — downstream repos can disable any one without disturbing the rest.
- Con: First-run network requirements for `actionlint` can confuse new contributors; mitigated by inline comments and CI as the source of truth.

**Alternatives considered:**

- **`jsonlint` instead of `check-json`:** Rejected for the dependency and overlap reasons above.
- **`prettier` for JSON/YAML format enforcement:** Rejected as a default; see the Prettier deferral ADR below.
- **A single mega-linter image:** Rejected. Mega-linter aggregations obscure version pinning, slow first-run installs, and complicate per-hook overrides.

### Design Decision: yamllint truthy.check-keys Default

`yamllint` is configured with `truthy.check-keys: false` in `.yamllint.yml`.

**Rationale:**

- The most common GitHub Actions workflow idiom is the unquoted `on:` key (`on: push`). With `truthy.check-keys: true`, `yamllint` flags `on` as a truthy value, producing false positives on every workflow file.
- Disabling key checking preserves the idiomatic Actions style without weakening the value-side `truthy` rule, which still flags ambiguous values like `yes`, `no`, `on`, `off` outside of keys.

**Stricter alternative:**

Repos that prefer maximum YAML 1.2 hygiene can:

1. Quote `"on":` (and any other reserved truthy keys) in workflow files, and
2. Set `truthy.check-keys: true` in `.yamllint.yml`.

This is a deliberate opt-in because it requires editing every workflow file at adoption time. The default favors zero-friction Actions authoring.

**Trade-offs:**

- Pro: Default works out-of-the-box for GitHub Actions, the most common YAML use case in this template.
- Con: A small class of truly-ambiguous truthy keys (e.g., a literal `yes:` map key) would not be flagged. The risk is low and stylistic — quoting is still recommended in the YAML guide.

### Design Decision: yamllint line-length Warning Level Default

`yamllint` is configured with `line-length.level: warning` in `.yamllint.yml`, even though the rest of the rule baseline aligned with the full template recommendation uses default (error) severity.

**Rationale:**

- A large fraction of long YAML lines in this template are **non-breakable user-facing content**: URLs in `.github/ISSUE_TEMPLATE/config.yml`, descriptive prose in issue-form `body:` blocks, and `echo`/`gh` shell commands inside workflow `run:` blocks that print PR comments or summary lines. Forcing these into multi-line continuations either harms readability (URLs, single sentences of UI copy) or changes the literal output that downstream users see (PR comment bodies).
- `yamllint`'s `line-length` rule already enables `allow-non-breakable-words` and `allow-non-breakable-inline-mappings`, but these only suppress lines whose overflow is a single non-breakable token. Comment-prefixed URLs and prose with embedded spaces still trip the rule.
- Treating line length as a warning preserves the signal (long lines still surface in `yamllint` output and CI annotations) without blocking PRs on cosmetic wraps that would not improve the underlying file.
- All other style violations (indentation, trailing whitespace, end-of-file newline, truthy values, brace/bracket spacing, comment formatting, empty-line counts) remain at default severity and **do** fail CI. Line length is the single intentional softening.

**Stricter alternative:**

Repos that want every long line to fail can either:

1. Remove the `level: warning` line from `.yamllint.yml` to inherit `yamllint`'s default error severity, and reformat any offending YAML files; or
2. Raise `line-length.max` if 120 columns is the friction point rather than the severity.

Adopting alternative 1 requires reformatting issue templates and workflow `run:` blocks at adoption time, which is the friction this default is meant to avoid.

**Trade-offs:**

- Pro: Default keeps idiomatic GitHub Actions workflows and issue-form prose readable without per-file `# yamllint disable-line: line-length` exceptions.
- Pro: Keeps line-length signal visible in CI annotations without blocking PRs on cosmetic wraps.
- Con: Long lines do not gate merges; reviewers must rely on the warning surface to notice problematic cases. Mitigated by the fact that every other style rule still fails the build.

### Design Decision: Prettier Deferral for Data Files

Prettier is **not** part of the default JSON/YAML toolchain.

**Rationale:**

1. **Tooling sprawl.** Adopting Prettier for data files expands Node tooling from "Markdown linting only" into "data-file formatting policy." That is a scope increase several adopters will not want, especially non-Node projects.
2. **Limited semantic value for JSON.** Prettier formats JSON but does not sort keys, which is the highest-value JSON-stability transformation a formatter could provide. Stable key ordering still has to be enforced by hand or via a separate tool.
3. **Conflicts with `yamllint` for YAML.** Prettier's YAML output differs from idiomatic `yamllint` defaults (line wrapping, flow vs. block style, quoting). Running both without explicit reconciliation produces churn-only diffs.
4. **JSONC support is partial across tools.** Adopting Prettier as the JSONC formatter forces additional decisions about which tools in the chain understand JSONC.

**Policy:**

- **JSON/JSONC:** Prettier remains **opt-in**. Repos that already use Prettier for Markdown or JavaScript may extend it to JSON/JSONC at their discretion; the JSON instruction guide is compatible with that choice.
- **YAML:** Prettier is **discouraged-by-default** unless the project explicitly reconciles Prettier's output with `yamllint` rules and pins both tools. Otherwise the two will fight.

**Trade-offs:**

- Pro: Smaller default toolchain; no Node dependency required for non-Node projects.
- Pro: No `yamllint` ↔ Prettier conflict surface in the default configuration.
- Con: No automatic data-file reformatting; authors lean on `check-json`/`yamllint` to flag issues rather than auto-fix them.

### Design Decision: Schema Location at Repository Root

Project-owned JSON Schemas live under a top-level `schemas/` directory, not under `.github/schemas/`.

**Rationale:**

1. **Schemas are project assets, not GitHub configuration.** `.github/` is reserved for GitHub-specific configuration (workflows, issue templates, CODEOWNERS, instructions). Schemas describe project data contracts that are consumed by application code, CI tooling, IDEs, and external tools. They belong alongside other project assets at the repository root.
2. **Discoverability.** A root-level `schemas/` directory is the conventional location IDEs and schema validators look for project schemas.
3. **Easy opt-out.** Downstream repos that do not use schema-backed data files can delete the entire `schemas/` directory without touching `.github/`.

**Trade-offs:**

- Pro: Clear separation between GitHub configuration and project data contracts.
- Pro: Aligns with widespread community convention.
- Con: One more top-level directory in repos that adopt schemas.

**Recommendation:** Repos adopting schema-backed validation should keep `schemas/` at the repository root and reference schemas by relative path from data files (`$schema`) or by configuring `check-jsonschema` in pre-commit.

### Design Decision: Schema Validation Tiers

Schema validation is required (RFC 2119 MUST/SHOULD/MAY) at three tiers based on the role each data file plays.

1. **MUST — Production / load-bearing contracts.** Data files whose shape is consumed by production code, deployment pipelines, public APIs, or release tooling MUST be validated against an explicit schema. Examples: published API request/response payloads, release manifests, policy bundles consumed by enforcement tools, IaC variable contracts.
2. **SHOULD — Durable fixtures, examples, policy documents, and config contracts.** Data files that survive across releases and are referenced by humans or by non-production tooling SHOULD be schema-validated. Examples: long-lived test fixtures, documented example payloads, governance policy documents, internal config files with a stable shape.
3. **MAY — Tool-owned simple config.** Files whose shape is owned and validated by the consuming tool itself (e.g., `.markdownlint.jsonc`, `pyproject.toml` sections, `.yamllint.yml` itself) MAY rely on the owning tool's own validation rather than a separately-maintained schema.

**Avoid placeholder schema hooks.** Do not wire `check-jsonschema` (or any other schema validator) into pre-commit until at least one schema actually exists and is referenced. Placeholder hooks produce no-op runs, drift silently, and obscure when real schema enforcement has been adopted.

**Trade-offs:**

- Pro: Tiered policy concentrates rigor where breakage is expensive and avoids over-engineering tool-owned config.
- Pro: Avoiding placeholder hooks keeps the pre-commit surface honest.
- Con: Authors must classify each new contract; the JSON/YAML guides provide the rubric.

### Design Decision: Built-in Schema Validation for Real Load-Bearing Configuration Files

This template wires `check-jsonschema --builtin-schema ...` validation for selected real, load-bearing repository configuration files, in addition to the worked-example schema-validation pattern under `schemas/`.

**Context:**

- The repository already ships a worked-example schema under `schemas/` ([`example-config.schema.json`](../schemas/example-config.schema.json)) whose primary purpose is to prove the schema-validation pipeline end to end.
- Real repository configuration files such as Dependabot, pre-commit, package metadata, markdownlint, and yamllint can also be load-bearing: they drive automation, dependency updates, formatting, or hook execution, and a malformed value can silently break those tools.
- The [Schema Validation Tiers](#design-decision-schema-validation-tiers) ADR requires (MUST) or recommends (SHOULD) schema validation for automation-driving files when validation is practical and low-noise.
- `check-jsonschema` ships a curated set of built-in vendor schemas (`--builtin-schema vendor.<name>`) that do not require network access at hook runtime and that track upstream schema changes through pinned `check-jsonschema` releases (kept current via the Dependabot `pre-commit` ecosystem).

**Decision:**

1. **Use `check-jsonschema --builtin-schema ...` for selected real load-bearing configuration files** when a mature, low-noise built-in schema exists in the pinned `check-jsonschema` release.
2. **Keep project-owned schemas under root-level `schemas/`.** Built-in schemas are not vendored into `schemas/`.
3. **Do not vendor third-party schemas into `schemas/`** unless a strong reason emerges (for example, an upstream schema that is unmaintained but still needed). The default path is "use the built-in schema" or "rely on the owning tool's own validation."
4. **Keep GitHub Actions workflow validation with [`actionlint`](https://github.com/rhysd/actionlint), not a redundant generic schema hook.** `actionlint` understands Actions-specific semantics (expression syntax, runner labels, shell-script linting via shellcheck) that a generic JSON Schema check would miss.

**Selected files (currently wired):**

| File | Built-in schema identifier | Hook in `.pre-commit-config.yaml` | Regression coverage |
| --- | --- | --- | --- |
| `.github/dependabot.yml` | `vendor.dependabot` | `validate-dependabot-config` alias on the `check-jsonschema` hook | [`tests/test_dependabot_schema.py`](../tests/test_dependabot_schema.py) validates the documented auto-assignment fixture |

The currently pinned `check-jsonschema` 0.37.2 `vendor.dependabot` schema has been verified against the documented Dependabot auto-assignment snippet in [`OPTIONAL_CONFIGURATIONS.md`](../OPTIONAL_CONFIGURATIONS.md): it accepts `assignees` and rejects `reviewers` as an additional property. The template therefore keeps `validate-dependabot-config` default-wired, limits the documented auto-assignment guidance to the accepted `assignees` field, and regression-tests that fixture in [`tests/test_dependabot_schema.py`](../tests/test_dependabot_schema.py).

**Evaluated but deferred:**

The following candidates were evaluated and intentionally **not** wired in this iteration. This subsection is the durable negative-space record: each entry exists so future authors do not re-litigate the same decision without new evidence.

- **GitHub Actions workflow files (`.github/workflows/*.yml`).** Already validated by `actionlint` (pinned in [`.pre-commit-config.yaml`](../.pre-commit-config.yaml) and re-run by [`.github/workflows/data-ci.yml`](./workflows/data-ci.yml)). Adding a generic JSON Schema hook against the SchemaStore Actions schema would be **redundant** with `actionlint` and would not catch the Actions-specific issues `actionlint` is designed for. Decision: rely on `actionlint`.
- **`.pre-commit-config.yaml`.** The pinned `check-jsonschema` release does not ship a `vendor.pre-commit-config` (or equivalent) built-in schema. pre-commit itself validates the file's structure when it loads its configuration, so a separate schema check would have minimal marginal value even if one became available. Decision: rely on pre-commit's own configuration loader.
- **`package.json`.** The pinned `check-jsonschema` release does not ship a `vendor.package` (or equivalent) built-in schema. npm validates this file when it parses dependency manifests, so it is not unguarded. Decision: rely on the package manager's own validation; revisit if a stable built-in schema is added upstream.
- **`.markdownlint.jsonc`.** The pinned `check-jsonschema` release does not ship a `vendor.markdownlint` built-in schema. The file is intentionally JSONC (it contains comments) and **MUST NOT** be converted to strict JSON merely to satisfy a validator. markdownlint's own configuration loader remains the enforcement mechanism for this file. Decision: rely on markdownlint's own validation.
- **`.yamllint.yml`.** The pinned `check-jsonschema` release does not ship a `vendor.yamllint` built-in schema. The file **MUST NOT** be weakened to satisfy an incomplete external schema; yamllint itself enforces its configuration shape when it loads `.yamllint.yml`. Decision: rely on yamllint's own validation.

If a future `check-jsonschema` release adds a mature built-in schema for any of the deferred candidates, add a narrowly scoped hook with an anchored `files:` pattern at that time. Do not vendor third-party schemas into this repository to fill the gap.

**Alternatives considered:**

- **Vendor external schemas under `schemas/external/`.** Rejected as the default. Vendoring couples the repository to a specific snapshot of an external contract and shifts maintenance burden onto template maintainers (re-syncing on every upstream change). Built-in schemas shipped with a pinned `check-jsonschema` release achieve the same effect with a single dependency-update touchpoint.
- **Leave real load-bearing repository configuration files without schema validation.** Rejected for files where a mature built-in schema exists and validation is low-noise. The Schema Validation Tiers ADR already classifies these as SHOULD-validate when practical; not wiring an available, low-cost validator would be inconsistent with that policy.
- **Validate every JSON/YAML file generically.** Rejected. The [Schema Validation Tiers](#design-decision-schema-validation-tiers) ADR explicitly forbids generic "validate every JSON/YAML file" sweeps. Schema validation is a contract check for specific file families, not a global sweep; `check-json` and `check-yaml` already cover syntax.
- **Add redundant schema validation for GitHub Actions workflows on top of `actionlint`.** Rejected. `actionlint` is the authoritative validator for Actions workflow files; adding a generic JSON Schema check would duplicate effort, increase noise, and miss Actions-specific issues.

**Consequences:**

- Stronger parity between JSON/YAML and other first-class file types: load-bearing configuration is checked by a real validator, not just by syntax-only `check-json` / `check-yaml`.
- Built-in schema names and the schemas they reference track `check-jsonschema` releases. Schema updates arrive through the normal `check-jsonschema` release cycle rather than through hand-vendored snapshots.
- Dependabot `pre-commit` ecosystem updates help keep schema support current; reviewers SHOULD treat `check-jsonschema` bumps as schema-content changes, not just dependency hygiene.
- Documentation that recommends optional keys for a default-validated vendor configuration MUST stay within the surface accepted by the pinned built-in schema, or the hook must move to an opt-in path with clear downstream wiring instructions.
- Downstream adopters who delete a validated file family **MUST** also remove the corresponding `check-jsonschema` hook (and any matching `data-ci.yml` step), per the removal guidance below.
- External schemas can be stricter, looser, or differently timed than the consuming tool's actual behavior. Hooks that produce noisy or misleading failures **SHOULD** be evaluated carefully and either narrowed in scope or removed.

**Downstream removal guidance:**

To remove built-in schema validation for a single file family in a downstream repository:

1. Delete or stop using the validated file (for example, remove `.github/dependabot.yml`).
2. Remove the corresponding `check-jsonschema` hook entry (or its `alias:`) from [`.pre-commit-config.yaml`](../.pre-commit-config.yaml).
3. If the granular `data-ci.yml` step list explicitly invokes the hook by ID or alias, remove the corresponding step from [`.github/workflows/data-ci.yml`](./workflows/data-ci.yml). Steps that invoke a hook by ID continue to work for any remaining files; only remove the step if the entire hook is being retired.
4. Update documentation that lists the active schema-validated files, including the table in this ADR, [`schemas/README.md`](../schemas/README.md), and [`OPTIONAL_CONFIGURATIONS.md`](../OPTIONAL_CONFIGURATIONS.md).

**Trade-offs:**

- Pro: Real load-bearing configuration files get cheap, fast schema feedback locally and in CI.
- Pro: Built-in schemas avoid vendoring and avoid runtime network access.
- Pro: The "Evaluated but deferred" subsection makes the negative space durable, so future authors do not silently re-add or re-evaluate already-rejected candidates without new evidence.
- Con: Built-in schema coverage tracks `check-jsonschema` release cadence rather than upstream-vendor cadence; new vendor schema fields may take a release cycle to be reflected.
- Con: External schemas can disagree with the consuming tool's actual behavior; noisy hooks must be evaluated carefully.

### Design Decision: JSON5 Exclusion by Default

JSON5 is **not** included in the default toolchain or instruction guidance.

**Rationale:**

1. **Limited ecosystem support.** Many common JSON consumers (the Go standard library `encoding/json`, .NET `System.Text.Json` in default mode, `jq` without flags, `check-json`) do not parse JSON5.
2. **JSONC already covers the most common use case.** The primary motivation for JSON5 in this codebase's context (comments and trailing commas) is satisfied by JSONC for tool-owned configuration files.
3. **Avoid format proliferation.** Three tiers of JSON-shaped formats (JSON, JSONC, JSON5) increase author confusion, expand the validator matrix, and create more places where strict-JSON tooling silently skips files.

**Adoption requires an explicit project decision.** A downstream repo that intentionally adopts JSON5 should record that decision in its own design-decisions document, add a JSON5-capable parser and validator, and update the JSON instruction guide accordingly. The default template stays on JSON + JSONC.

**Trade-offs:**

- Pro: Smaller, more interoperable default surface.
- Con: Repos that already use JSON5 must opt in explicitly rather than inheriting it from the template.

### Design Decision: `additionalProperties` Policy

JSON Schemas owned by this template (and recommended for downstream adopters) use `additionalProperties: false` for closed contracts, with documented exceptions for ecosystem-mirroring schemas.

**Rules:**

1. **Project-owned closed contracts:** Use `additionalProperties: false`. Closing the schema makes typos and drift fail loudly rather than silently being accepted.
2. **Ecosystem-mirroring schemas:** Open schemas (`additionalProperties: true` or omitted) are allowed when the schema mirrors an external ecosystem that itself permits unknown keys (e.g., extension fields in OpenAPI `x-*`, vendor-specific keys in tool config that the upstream tool intentionally allows). Each open schema MUST include an inline rationale comment or `description` explaining why the schema is open.
3. **Mixed schemas:** Use `additionalProperties: false` at the closed level and a typed `patternProperties` entry (or a typed sub-object) for the controlled extension surface.

**Rationale:**

- Closed-by-default catches the highest-frequency real-world failure mode: a typoed key silently being ignored.
- A documented escape hatch prevents the closed-default from misrepresenting genuinely open ecosystems.

**Trade-offs:**

- Pro: Schema becomes a useful drift detector.
- Con: Authors must update the schema when intentionally adding new keys; this is the intended behavior.

### Design Decision: Testing Beyond Linting for JSON/YAML

Schema validation is the primary correctness strategy for static JSON and YAML. A separate JSON/YAML test framework is **not** added by default.

**Rationale:**

1. **Static data shape is best validated statically.** Schemas catch shape errors deterministically across every file in scope without authoring per-file tests.
2. **Behavioral correctness belongs to the consumer.** If a JSON or YAML file influences runtime behavior, the test that proves the behavior belongs in the **consuming language's** test framework (pytest for Python, Pester for PowerShell, Terraform Test for Terraform). That keeps the data file under test alongside the code that consumes it.
3. **Avoid orphan test infrastructure.** A standalone "JSON/YAML test framework" without consumers tends to either duplicate schema validation or drift into ad-hoc behavioral tests in the wrong layer.

**Policy:**

- Use schemas (with the tiered MUST/SHOULD/MAY policy above) for static shape correctness.
- Use the consumer's existing test framework for behavioral assertions about data files.
- Do not add a new top-level data-file test framework as part of this template.

**Trade-offs:**

- Pro: Single mental model — schemas for shape, language tests for behavior.
- Pro: No additional CI surface to maintain.
- Con: Authors must remember to write consumer-side tests for behaviorally-significant data; the language instruction guides reinforce this.

### Design Decision: .gitattributes LF Pinning for Template-Managed Text

`.gitattributes` pins byte-exact text fixture locations, linter-enforced YAML files (`*.yml` and `*.yaml`), and template-managed text/control file families to LF. The shipped template-managed pins cover Markdown, Cursor MDC, PowerShell, JSON, JSONC, TOML, JavaScript (`*.js`), JavaScript module (`*.mjs`), Python, shell scripts (`*.sh`), HCL (`*.hcl`), Terraform (`*.tf`, `*.tfvars`, `*.tftpl`, `*.tfbackend`), `.gitattributes`, dot-prefixed ignore files (`.*ignore`), CODEOWNERS files, and the root `LICENSE`.

This decision records the current shipped defaults. It supersedes the earlier narrow framing that left JSON outside the shipped extension-level pins and described only YAML extension-level LF rules outside byte-exact fixture paths.

**Rationale:**

1. **YAML has a linter-enforced LF contract.** `.yamllint.yml` extends `default`, which enables `new-lines: type: unix`. On Windows checkouts where `core.autocrlf=true` rewrites repository YAML files to CRLF, `yamllint` fails with `wrong new line character: expected \n (new-lines)`. Standard validation therefore depends on LF working-tree bytes for YAML.
2. **Template-managed text/control files need stable checkout bytes.** Markdown, PowerShell, JSON, JSONC, TOML, JavaScript, Python, HCL/Terraform, ignore files, CODEOWNERS files, `.gitattributes`, and the root `LICENSE` are repository-managed files that downstream adopters commonly edit, prune, or review across platforms. LF pins prevent broad non-semantic CRLF churn from obscuring the intended template change.
3. **Shell scripts have a direct-execution correctness requirement.** The template ships `.claude/hooks/session-start.sh` as a directly invoked hook. On Unix-like hosts, a CRLF shebang can make the script loader search for an interpreter path containing a carriage return, so `*.sh text eol=lf` prevents a checkout mode from breaking the hook.
4. **Git attributes are the durable checkout-level fix.** Explicit `text eol=lf` rules override host-level checkout conversion and make `pre-commit run --all-files` behave the same on Windows as on LF-native checkouts for the pinned families.
5. **Byte-exact fixture protection is unchanged.** Any text artifact under the existing fixture-location patterns remains pinned to LF by directory rule, independent of extension. The extension and basename rules cover linter contracts, direct-execution correctness, and CRLF-churn prevention for template-managed files.
6. **Binary overrides still win.** The LF rules are placed before the existing binary override block so later `binary` patterns continue to declassify binary files per attribute.

**Trade-offs:**

- Pro: `yamllint` and `pre-commit run --all-files` no longer fail on Windows checkouts solely because YAML files materialized as CRLF.
- Pro: Existing byte-exact fixture protection is preserved unchanged.
- Pro: Shell hooks and template-managed control files remain usable and reviewable in mixed-EOL environments.
- Con: Windows contributors now get LF working-tree bytes for a broader set of template-managed text/control files even when their global Git configuration would otherwise materialize CRLF.

**Alternatives considered:**

- **Leave the remaining text/control files unpinned:** Rejected because the repository already observed non-semantic CRLF churn for these tracked LF files, and shell-script CRLF conversion can break direct execution.
- **Add a blanket `* text=auto` rule:** Rejected because `text=auto` does not guarantee LF working-tree bytes on hosts with CRLF checkout conversion; explicit `eol=lf` is required for the pinned families.
- **Use a pre-commit mixed-line-ending hook as the primary fix:** Rejected because it would catch or repair the symptom after checkout rather than distributing stable checkout behavior through `.gitattributes`.
- **Relax or disable `yamllint`'s `new-lines` rule:** Rejected because the repository already standardizes YAML formatting through `yamllint`; aligning checkout behavior with the configured rule is less surprising than weakening the rule.

---

## Template Sync

### Design Decision: Manifest v2 Path-Mapping Relations

The template sync manifest uses version 2 semantics for path mappings. Version 2 keeps `requires_all` from version 1 and adds `requires_any` as the only new relation field.

**Decision:**

- `requires_all` remains an AND relation. Every listed module must be present in the downstream marker's `included_modules`.
- `requires_any` is an OR relation. When present, at least one listed module must be present in `included_modules`.
- When a mapping contains both fields, both conditions must pass. The practical reading is "all required modules, plus at least one alternative module."
- Version 1 manifests remain valid and continue to mean `requires_all` only.
- `known_limitations` is no longer used for cross-module mappings that version 2 can express natively.

**Rationale:**

1. **Smallest sufficient contract change:** The known gap was platform-spanning shared files, especially `.github/workflows/data-ci.yml`, which needs `github-actions` plus at least one data-file module. One OR group alongside the existing AND list expresses that without introducing an expression language.
2. **Backward compatibility:** Keeping version 1 valid lets downstream repositories validate existing manifests while migrating on their own schedule.
3. **Reviewability:** `requires_all` plus `requires_any` remains easy to render in human sync documentation and easy to validate with JSON Schema plus focused pytest coverage.
4. **Migration clarity:** Existing rows can remain unchanged during a v1-to-v2 migration unless they truly need alternative-module semantics.

**Alternatives considered:**

- **Full boolean expression tree:** Rejected for now because nested `allOf` / `anyOf` / `not` style structures would be harder to read, harder to render in the manual procedure, and unnecessary for the current manifest.
- **Duplicate path mappings for each accepted module combination:** Rejected because it would obscure the single ownership rule for a path and make most-specific matching harder to audit.
- **Keep prose-only notes:** Rejected because downstream sync filtering needs machine-readable semantics; notes are useful for human context but should not be the only source of logical requirements.

---

## Node.js Package Configuration

### Design Decision: package.json Minimal Configuration

The template ships with minimal package.json configuration (no repository field, an explicit Node.js support floor through `engines.node`, and generic metadata) to reduce template adoption friction.

**Rationale:**

1. **Reduces friction**: Most users only need dev tooling (markdownlint scripts) without Node.js runtime dependencies.

2. **Prevents placeholder sprawl**: Unlike OWNER/REPO placeholders that break functionality if not replaced, missing optional fields don't affect usage.

3. **Clear separation**: Dev tooling (present) vs. application code (user adds).

4. **Private by default**: The `"private": true` flag means omitted fields like repository don't affect npm publishing.

**Trade-offs:**

- Users creating Node.js applications must manually add metadata fields
- Node.js version requirements are advisory by default in npm: `engines.node` declares the support floor and npm warns on mismatch unless `engine-strict` is enabled, where it becomes an install error
- Users must consult README for customization guidance

---

## CI Workflow Configuration

### Design Decision: Dedicated Data-File CI Workflow (`data-ci.yml`)

The repository ships a dedicated `.github/workflows/data-ci.yml` workflow that runs JSON, YAML, and GitHub Actions workflow validation as a first-class CI gate, alongside the aggregate pre-commit gate (`precommit-ci.yml`) and the per-language workflows (`python-ci.yml`, `powershell-ci.yml`, `terraform-ci.yml`, and `markdownlint.yml`).

**Why a dedicated workflow even though `precommit-ci.yml` already runs every pre-commit hook:**

- `precommit-ci.yml` runs `pre-commit run --all-files`, which transitively enforces the JSON/YAML/actionlint hooks. That works functionally but makes data-file validation appear incidental to the broader repository hygiene gate.
- A dedicated workflow gives JSON/YAML/Actions validation a distinct required-check identity, clearer ownership, and parity with per-language workflows. Branch protection rules can require data-file validation independently from aggregate pre-commit validation.
- Template adopters who do not use Python should still see data-file validation as a first-class concern; surfacing it only under Python CI would obscure that.

**CI ownership decision:** `precommit-ci.yml` runs the full `pre-commit run --all-files` pipeline as the single canonical aggregate pre-commit gate. `data-ci.yml` runs the shared data-file hooks (`check-json`, `check-toml`, `check-yaml`, `yamllint`, and `actionlint`) by hook ID and runs schema-backed checks by explicit pre-commit aliases such as `validate-example-config-valid-examples`, `validate-template-sync-manifest`, and `validate-dependabot-config`. The hooks therefore execute in both workflows, but the dedicated workflow keeps module-owned schema and template-sync validation visible as separate CI steps.

**Trade-off accepted:** The duplication between `precommit-ci.yml` and `data-ci.yml` is intentional. The previous decision to keep aggregate pre-commit enforcement in `python-ci.yml` was reversed because excluding the `python` module deleted the aggregate gate for downstream repositories with no Python project source. The accepted topology keeps data-file visibility while moving shared hook enforcement to a baseline workflow.

**Distinction from `auto-fix-precommit.yml`:** `data-ci.yml` is a contract enforcement gate that runs on all PRs and pushes. `.github/workflows/auto-fix-precommit.yml` is intentionally NOT a peer of `data-ci.yml`: it is a fix-up workflow scoped to `copilot/**` branches that auto-applies pre-commit fixes and does not enforce results. The two workflows serve different purposes and must not be conflated.

**Schema validation steps:** `data-ci.yml` invokes schema-backed validation by alias rather than by the aggregate `check-jsonschema` or `check-metaschema` hook IDs. Schema-owned aliases validate the worked-example schema fixtures, template-sync marker fixtures, and project-owned schemas against their declared Draft 2020-12 metaschemas inside `schema-only` inline blocks. Joint schema plus template-sync-support aliases validate `.template-sync/manifest.yml` and `.template-sync/marker.yml` inside `schema-template-sync-support-only` inline blocks. The GitHub-platform-owned `validate-dependabot-config` alias validates `.github/dependabot.yml` against `vendor.dependabot` in its own standalone step. This alias-based model preserves current validation when modules are retained while allowing downstream repositories to strip `schema` or `template-sync-support` blocks without leaving CI steps that invoke missing hooks or unrelated module-owned validation.

### Design Decision: Aggregate Pre-commit CI Workflow (`precommit-ci.yml`)

The repository ships `.github/workflows/precommit-ci.yml` as the canonical aggregate pre-commit CI gate. It is mapped to the `baseline` and `github-actions` modules so downstream repositories can keep `pre-commit run --all-files` enforcement even when they exclude the `python` module.

**Decision:** Aggregate pre-commit enforcement belongs in `precommit-ci.yml`, not in `python-ci.yml`. The Python workflow is limited to Python-specific checks such as mypy and pytest. The aggregate workflow still installs Python because pre-commit itself and several hooks are Python tools, but that runner dependency is distinct from shipping Python project source.

**Rationale:**

- Downstream repositories may exclude `python` while retaining `.pre-commit-config.yaml`; aggregate hook enforcement must survive that module choice.
- `.pre-commit-config.yaml` is baseline-scoped and can contain inline module blocks for hooks that belong to optional modules.
- Branch rulesets need a stable required-check identity for repository hygiene that is not tied to Python source ownership.

**Alternatives considered:**

1. Keep the aggregate `Pre-commit` job in `python-ci.yml` and document a manual downstream workaround. Rejected because excluding the `python` module removes `python-ci.yml` and therefore removes the recommended required check.
2. Treat `data-ci.yml` as the aggregate replacement. Rejected because `data-ci.yml` intentionally runs selected data-file hooks for visibility and does not exercise every active hook in `.pre-commit-config.yaml`.
3. Make `python-ci.yml` baseline-scoped. Rejected because it would force downstream repositories without Python source to retain mypy and pytest CI scaffolding.

**Consequences:**

- Repositories that exclude Python source can retain `precommit-ci.yml` and the shared pre-commit gate.
- Python project hooks such as Black and Ruff must be inside `python-only` inline blocks in `.pre-commit-config.yaml`.
- Terraform/TFLint setup for aggregate pre-commit runs moves with the aggregate workflow and remains inside a `terraform-only` inline block.

### Design Decision: Non-Blocking Type Checking by Default

The template keeps mypy advisory by default for repositories created from this template. In the upstream `franklesniak/copilot-repo-template` repository, the mypy step is blocking so the shipped template cannot accumulate type-check failures.

**Implementation:**

```yaml
continue-on-error: ${{ github.repository != 'franklesniak/copilot-repo-template' }}
```

The expression evaluates to `false` in the upstream template repository, so mypy failures block upstream pushes and pull requests. It evaluates to `true` in adopter repositories because their `github.repository` value is different, preserving the template's non-blocking default without any adopter edit.

**Why this is the right default for a template:**

- Template adopters start with varying levels of type coverage (often zero)
- Blocking type errors on day one creates adoption friction
- Gradual type adoption is a well-established Python best practice
- Allows adopters to see type errors without blocking their workflow

**Trade-offs:**

Blocking type checking (strict):

- Pros: Enforces type safety, prevents type debt accumulation
- Cons: High friction for new adopters, requires upfront investment

Non-blocking type checking (adopter default):

- Pros: Zero friction adoption, gradual improvement path, visibility without blocking
- Cons: Type errors can accumulate if not addressed, requires discipline

**Alternatives considered:**

1. No type checking at all: Rejected because mypy provides value even when non-blocking (developers can see errors and fix them opportunistically)

2. Strict by default with documentation to make it lenient: Rejected because this inverts the adoption experience—failing CI on first push is a poor template UX

3. Conditional based on repository variable: Rejected as over-engineering for a simple toggle that adopters can easily change

4. Repository-slug gate for upstream enforcement only: Accepted because the literal upstream slug is stable, pull requests into this repository evaluate in the upstream repository context, and adopters automatically receive the advisory behavior when their repository slug differs.

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

### Design Decision: Workflow Version Pinning and Dependabot Coherence

The repository-wide rule for how third-party action versions and tool versions are referenced inside `.github/workflows/*.yml` lives in the **Workflow Version Pinning** section of [`.github/copilot-instructions.md`](copilot-instructions.md#workflow-version-pinning). This ADR records the rationale and the alternatives that were considered.

**Context:**

- Dependabot's `github-actions` ecosystem rewrites GitHub Actions `uses:` references when an action publishes a new version. It does **not** generally rewrite unrelated `with:` inputs, workflow-level `env:` values, cache keys, file paths, shell-script literals, manually constructed image tags, or comments — even when those locations contain a literal copy of the same action version string.
- Workflow files in this repository today contain repeated `uses:` references to the same action (for example, `actions/checkout@v6` and `actions/setup-python@v6` appear in multiple workflows and jobs). Each occurrence is a normal Dependabot-managed `uses:` reference, which is fine.
- Workflow files also contain manually maintained tool-version inputs that are **not** Dependabot-managed: `terraform_version: "1.14.4"` (passed to `hashicorp/setup-terraform@v4`) appears in multiple jobs in [`.github/workflows/terraform-ci.yml`](workflows/terraform-ci.yml), and `tflint_version: v0.51.1` is passed to `terraform-linters/setup-tflint@v6`. These are CLI versions installed by the setup actions, distinct from the setup action versions themselves.
- Without a written rule, future authors could reasonably assume that lifting an action version into a workflow-level `env:` variable is "DRY" or that a cache key embedding the action version is a useful invalidation hint. Both patterns silently break Dependabot coherence: Dependabot bumps the `uses:` line, the mirror remains stale, and the workflow runs with a mismatched literal until someone notices.

**Decision:**

1. **Action versions in `uses:` lines are the only authoritative source for the action version.** Repeated `uses:` references are acceptable; Dependabot updates each line.
2. **Action versions MUST NOT be mirrored** into workflow-level `env:` variables, comments-presented-as-authoritative-state, cache keys, file paths, shell literals, manually constructed image tags, or any other secondary location that Dependabot will not reliably rewrite.
3. **Secondary workflow behavior that needs to track a `uses:` change** must be derived from a stable source that naturally changes with the workflow or tool configuration — for example, cache keys scoped to the specific configuration file that governs the cached artifact (`hashFiles('.pre-commit-config.yaml')` for pre-commit caches, `hashFiles('.tflint.hcl')` for TFLint plugin caches, `hashFiles('**/.terraform.lock.hcl')` for Terraform provider caches, mirroring the pattern already used in this repository's workflows) — rather than embedding a duplicated literal version string. Avoid broad wildcard patterns like `hashFiles('.github/workflows/*.yml')` for cache keys: any unrelated workflow edit would invalidate every job's cache, and the goal is to track the configuration that drives the cached content, not the workflow definition that consumes it.
4. **Tool versions that are not Dependabot-managed** (for example, `terraform_version`, `tflint_version`) **SHOULD** still avoid unnecessary duplication. A workflow-level `env:` value is the encouraged single source of truth for these, precisely because Dependabot does not manage them and there is no desync risk.
5. **Wrapper actions and the tools they install are separate pins.** `hashicorp/setup-terraform@v4` is the setup action version (Dependabot-managed via `uses:`); `terraform_version: "1.14.4"` is the CLI version installed by that setup action (manually maintained). Both pins coexist in the same step; do not conflate them.
6. **The `.github/dependabot.yml` `ignore:` escape hatch** is appropriate only when a Dependabot-managed dependency genuinely cannot be represented without duplication and Dependabot would otherwise produce partial updates. When used, the `ignore:` entry **MUST** carry a YAML comment explaining why the dependency is intentionally not auto-updated.

**Asymmetry around workflow-level `env:`:**

- For **action versions**, a workflow-level `env:` mirror is forbidden because Dependabot will not rewrite the mirror.
- For **tool versions**, a workflow-level `env:` value is encouraged because Dependabot does not manage the value, so there is no desync risk and the `env:` value can serve as the source of truth across multiple steps.

This asymmetry is the entire point of the rule: the choice of where a version literal lives depends on whether Dependabot owns updates for that literal, not on a generic preference for "DRY" or "single source of truth."

**Alternatives considered:**

- **Allow workflow-level `env:` mirrors of action versions, on the theory that a human reviewer will catch the desync.** Rejected. The whole purpose of Dependabot is to remove the human reviewer from routine version bumps; relying on review to catch silent drift defeats the automation.
- **Forbid repeated `uses:` references and require a single composite action wrapper.** Rejected. Repeated `uses:` references are explicitly compatible with Dependabot; introducing composite-action indirection trades a non-problem for new template complexity.
- **Bulk-refactor existing workflows now to centralize `terraform_version` and `tflint_version` under workflow-level `env:`.** Out of scope for this documentation-only change. The rule documents the preferred pattern; existing duplication is accepted until a separate refactor lands.
- **Add `.github/dependabot.yml` `ignore:` entries pre-emptively for the duplicated tool-version literals.** Rejected. Tool-version literals are not Dependabot-managed in the first place, so `ignore:` would be a no-op. `ignore:` is reserved for genuine partial-update problems on Dependabot-managed dependencies.

**Trade-offs:**

- Pro: Eliminates a class of silent partial-update bugs where a `uses:` line moves but a mirrored literal stays on the old version.
- Pro: Documents the wrapper-action vs. installed-tool distinction so future authors do not collapse them into a single "version" concept.
- Pro: Makes the `dependabot.yml` `ignore:` escape hatch a documented, narrow tool rather than a folk remedy.
- Con: Authors who reach for "DRY" instinctively when they see a repeated `uses:` value must learn the rule before refactoring. The asymmetry table in [`.github/copilot-instructions.md`](copilot-instructions.md#workflow-version-pinning) is the primary mitigation.
- Con: Existing duplicated tool-version literals (`terraform_version: "1.14.4"` in three places) remain; the rule documents the preferred pattern but does not by itself eliminate them. A follow-up refactor is the appropriate vehicle for that cleanup.

**Consequences:**

- New workflow code authored after this ADR **MUST** keep action versions only in `uses:` references and **SHOULD** keep tool versions in a single workflow-level `env:` value when the same tool version is needed in multiple steps.
- Reviewers **SHOULD** flag any new workflow change that introduces a mirrored action version (in `env:`, cache keys, comments, file paths, shell literals, or image tags) and request that it be removed in favor of relying on the `uses:` line plus a stable derivation source for any dependent behavior.
- Adding an `.github/dependabot.yml` `ignore:` entry **MUST** be justified inline with a YAML comment that explains the partial-update risk being mitigated; an `ignore:` without that comment is treated as incomplete.

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
- Works well with branch rulesets requiring code owner approval
- Using `@OWNER` placeholder follows the existing `OWNER/REPO` pattern in this template
- Placeholder check workflow ensures adopters don't forget to customize
- Default rules cover repository root, workflows, and Copilot instructions

**Trade-offs:**

- Pro: Automatic PR review assignment reduces manual reviewer selection
- Pro: Documents code ownership explicitly in the repository
- Pro: Works with branch ruleset "required reviews from code owners" setting
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

> **Status: Superseded** (2026-05-03). This decision has been replaced by the **Issue and PR templates** carve-out in [`.github/instructions/docs.instructions.md`](instructions/docs.instructions.md). The relative links described below were not actually working: `[Security tab](security)` resolved to `/{owner}/{repo}/issues/security` (404), and `[SECURITY.md](blob/HEAD/SECURITY.md)` resolved to `/{owner}/{repo}/issues/blob/HEAD/SECURITY.md` (404), because issue-form `value:` blocks render at `/{owner}/{repo}/issues/new?...`. The current `bug_report.yml` uses absolute `https://github.com/OWNER/REPO/security` and `https://github.com/OWNER/REPO/blob/HEAD/SECURITY.md` URLs; the `OWNER/REPO` substitution is enforced by `.github/workflows/check-placeholders.yml` **only when that workflow is adopted and kept** (it is an optional adoption step that downstream repositories MAY skip or remove after initial setup, in which case no CI guardrail catches a missed substitution and adopters must verify it manually). The historical content is preserved below for context.

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

## Branch Ruleset Setup

This section documents how to configure a branch ruleset using the CI workflows provided by this template. Repository rulesets are the recommended approach for protecting branches, replacing classic branch protection rules. They offer more granular control and can be applied across multiple branches or repositories.

### Design Decision: Branch Ruleset Documentation

This template includes documentation for branch ruleset setup rather than attempting to configure it automatically. Branch rulesets are repository settings that cannot be included in template repositories, so documentation is the appropriate way to guide adopters.

**Rationale:**

- Helps adopters set up proper CI gates for their default branch
- Explains the intended use of CI workflows and how they relate to branch rulesets
- Documents which CI jobs are good candidates for required status checks
- Clarifies the relationship between `needs:` dependencies and branch rulesets

**Trade-offs:**

- Pro: Helps adopters set up proper CI gates quickly
- Pro: Explains intended use of CI workflows from this template
- Pro: Clarifies complementary nature of CI dependencies vs branch rulesets
- Con: GitHub UI may change over time, requiring documentation updates
- Con: Cannot be enforced via template (requires manual setup in each repository)
- Con: Adopters must manually configure settings in GitHub UI

**Recommendation:**

Configure a branch ruleset for your default branch after initial repository setup. At minimum, require the pre-commit check to pass before merging. For additional protection, also require downstream checks like tests and type checking.

### CI Jobs Available as Required Status Checks

The template provides these CI jobs that can be configured as required status checks:

| Workflow | Job Name | Recommended as Required | Notes |
| --- | --- | --- | --- |
| `precommit-ci.yml` | **Pre-commit** | ✅ Yes | Foundational check—catches formatting and linting issues |
| `data-ci.yml` | **Data file linting** | ✅ Yes | Gives JSON/YAML/Actions validation a distinct required-check identity |
| `python-ci.yml` | **Type Check (mypy)** | Optional | Set to `continue-on-error: true` by default; make strict when ready |
| `python-ci.yml` | **Test** | ✅ Yes | Ensures tests pass on all platforms |
| `markdownlint.yml` | **Markdown Lint** | ✅ Yes | Ensures documentation quality |
| `powershell-ci.yml` | **Lint (PSScriptAnalyzer)** | Optional | Only if using PowerShell |
| `powershell-ci.yml` | **PowerShell Tests (Pester)** | Optional | Only if using PowerShell with tests |
| `check-placeholders.yml` | **Check for OWNER/REPO Placeholders** | Optional | Only runs in repos created from this template (skipped in template repo itself) |

> **Note:** In the GitHub Actions UI and branch ruleset status-check picker,
> checks appear in the format **`Workflow name / Job name`** (for example,
> `Pre-commit CI / Pre-commit`). The **Job Name** column above lists only the
> job-level name; prepend the workflow name when searching for checks in the
> ruleset configuration. Status checks only appear for selection after the
> corresponding workflow has run at least once.
>
> The `auto-fix-precommit.yml` workflow is intentionally **not listed** above
> because it only triggers on pushes to `copilot/**` branches by the Copilot
> bot. Making it a required status check would block PRs from all other
> branches where the check never runs.

### How to Configure a Branch Ruleset

Complete this step **after** your CI workflows have run at least once so that status checks are available to select.

1. Go to your repository on GitHub
2. Navigate to **Settings** > **Rules** > **Rulesets**
3. Click **New ruleset** → **New branch ruleset**
4. Configure the ruleset:
   - **Ruleset name:** `main branch ruleset`
   - **Enforcement status:** **Active**
5. Under **Target branches**, click **Add target** → **Include default branch**
6. Under **Branch rules**, enable the following:
   - ✅ **Restrict deletions**
   - ✅ **Require a pull request before merging**
     - Required approvals: **1**
     - ✅ Dismiss stale pull request approvals when new commits are pushed
   - ✅ **Require status checks to pass**
     - ✅ Require branches to be up to date before merging
     - Click **Add checks** and search for the status checks you want to require (see the [CI Jobs table](#ci-jobs-available-as-required-status-checks) above for recommended checks)
   - ✅ **Require conversation resolution before merging** (optional)
   - ✅ **Block force pushes**
7. Under **Bypass list** (at the top of the ruleset):
   - Leave empty if you want no one to bypass the rules
   - Optionally click **Add bypass** → **Repository admin** if you want the ability to force-merge as an admin
8. Click **Create**

> **Note:** Repository rulesets offer more granular control than classic
> branch protection rules and can be applied across multiple branches or
> repositories. See GitHub's
> [rulesets documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)
> for more details.

### Understanding Workflow Dependencies vs Branch Rulesets

Some template CI workflows use `needs:` to create internal job dependencies:

```yaml
lint:
  name: Lint
  needs: validate  # Lint waits for validation to pass
```

**How `needs:` works (internal CI dependency):**

- If the dependency job fails, the dependent job is automatically skipped
- This saves CI minutes by not running later checks after earlier failures
- The dependency is internal to the workflow—GitHub Actions manages it

**How branch rulesets work (external gate):**

- Branch rulesets are configured in repository settings, not in workflows
- They prevent PR merges until selected status checks pass
- They are an external enforcement mechanism that operates at the PR level

**These are complementary:**

- `needs:` optimizes CI execution (skip downstream jobs on early failure)
- Branch rulesets enforce quality gates (block merges until checks pass)
- Using both provides defense in depth

**Recommendation:** Require **both** the aggregate `Pre-commit` job and downstream jobs like `Test` in the branch ruleset. Requiring independent checks ensures that:

1. Format/lint issues block the PR (Pre-commit requirement)
2. Test failures block the PR (Test requirement)
3. Skipped jobs (due to an internal workflow dependency) also block the PR

### Example Branch Ruleset Configuration

For a Python project using this template:

**Required status checks:**

- Pre-commit
- Data file linting
- Test
- Markdown Lint

**Optional but recommended:**

- Type Check (mypy) — after making it strict by removing `continue-on-error: true`

For a multi-language project (Python + PowerShell):

**Required status checks:**

- Pre-commit
- Data file linting
- Test
- Markdown Lint
- Lint (PSScriptAnalyzer)
- PowerShell Tests (Pester)

---

## Documentation Tier Inventory

The documentation-tier policy itself lives in [`.github/instructions/docs.instructions.md`](instructions/docs.instructions.md) and is intentionally expressed in categorical, content-based terms with path patterns rather than as a list of specific shipped filenames. This section captures **this template repository's current file-by-file classification** under that policy. Downstream consumers of this template should treat this section as template-state to maintain, prune, replace, or extend as their own file set diverges from the template.

### Tier 1 (Metadata Block Present)

The following files currently shipped by this template are Tier 1 under the policy:

- `.github/copilot-instructions.md`
- Files matching `.github/instructions/*.instructions.md`
- Root agent entry-point files: `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.hermes.md`
- `.cursor/rules/repository-instructions.mdc`
- `.github/TEMPLATE_DESIGN_DECISIONS.md` (newly added in this PR)
- `docs/PR_REVIEW_PROMPTS.md`
- `docs/terraform/TERRAFORM_LINTING_GUIDE.md`
- `docs/terraform/TERRAFORM_TESTING_GUIDE.md`
- `docs/terraform/TERRAFORM_COPILOT_INSTRUCTIONS_GUIDE.md`
- `schemas/README.md`

### Tier 2 (No Metadata Block)

The following files currently shipped by this template are Tier 2 under the policy:

- `README.md`
- `CONTRIBUTING.md`
- `CODE_OF_CONDUCT.md`
- `SECURITY.md`
- `OPTIONAL_CONFIGURATIONS.md`
- `GETTING_STARTED_NEW_REPO.md`
- `GETTING_STARTED_EXISTING_REPO.md`
- `TEMPLATE_MAINTENANCE.md`
- `COPILOT_CHAT_PROMPTS.md`
- `.github/pull_request_template.md`
- `templates/json/README.md` (metadata removed in this PR)
- `templates/yaml/README.md` (metadata removed in this PR)

### Rationale for In-PR Mismatch Fixes

Two categories of files were updated in the same PR that introduced the tiered policy, to align this template's shipped state with the policy's content-based classification:

- **`.github/TEMPLATE_DESIGN_DECISIONS.md` gains a metadata block.** This file is a durable ADR-style design-decision record. Its content meets the Tier 1 content criteria (governance and durable design rationale), so it carries the Tier 1 metadata header block.
- **`templates/json/README.md` and `templates/yaml/README.md` lose their metadata blocks.** These files are starter-content READMEs intended for downstream copy/paste. Their content is end-user-oriented (adoption guidance, copy/adapt instructions), so under the precedence rule and the starter-content clarification in the policy they are Tier 2 by default and do not carry a metadata header block without a concrete consumer for the metadata.

### Maintenance Note

Future files added to this template should be classified by the categorical policy in [`.github/instructions/docs.instructions.md`](instructions/docs.instructions.md). Record an entry in this inventory only when it remains useful to maintainers; the inventory is template-state to maintain, prune, replace, or extend, not a registry that has to track every file in the repository.

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
