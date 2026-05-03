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
- [Agent Instruction Files](#agent-instruction-files)
  - [Multi-Agent Instruction Files at Repository Root](#design-decision-multi-agent-instruction-files-at-repository-root)
  - [Agent Files as Minimal Entry-Point Summaries (Not Canonical)](#design-decision-agent-files-as-minimal-entry-point-summaries-not-canonical)
- [Data File Standards (JSON/YAML)](#data-file-standards-jsonyaml)
  - [Dedicated JSON and YAML Instruction Files](#design-decision-dedicated-json-and-yaml-instruction-files)
  - [Baseline JSON/YAML Linting Stack](#design-decision-baseline-jsonyaml-linting-stack)
  - [yamllint truthy.check-keys Default](#design-decision-yamllint-truthycheck-keys-default)
  - [yamllint line-length Warning Level Default](#design-decision-yamllint-line-length-warning-level-default)
  - [Prettier Deferral for Data Files](#design-decision-prettier-deferral-for-data-files)
  - [Schema Location at Repository Root](#design-decision-schema-location-at-repository-root)
  - [Schema Validation Tiers](#design-decision-schema-validation-tiers)
  - [JSON5 Exclusion by Default](#design-decision-json5-exclusion-by-default)
  - [`additionalProperties` Policy](#design-decision-additionalproperties-policy)
  - [Testing Beyond Linting for JSON/YAML](#design-decision-testing-beyond-linting-for-jsonyaml)
  - [.gitattributes JSON/YAML LF Pinning](#design-decision-gitattributes-jsonyaml-lf-pinning)
- [Node.js Package Configuration](#nodejs-package-configuration)
- [CI Workflow Configuration](#ci-workflow-configuration)
- [Python Configuration](#python-configuration)
- [Security and Vulnerability Reporting](#security-and-vulnerability-reporting)
- [License Configuration](#license-configuration)
- [Dependabot Configuration](#dependabot-configuration)
- [CODEOWNERS Configuration](#codeowners-configuration)
- [Issue Template Design Decisions](#issue-template-design-decisions)
- [Branch Ruleset Setup](#branch-ruleset-setup)

---

## File Placement

### Design Decision: TEMPLATE_DESIGN_DECISIONS.md Location

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
`https://github.com/<owner>/<repo>/blob/HEAD/CONTRIBUTING.md` (remembering to replace `<owner>/<repo>` with your actual org/repo name).

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
- `.github/TEMPLATE_DESIGN_DECISIONS.md` — The "CI Workflow Configuration" section documents CI/CD design decisions
- `README.md` — High-level overview of available workflows and their purposes

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

---

## Data File Standards (JSON/YAML)

These ten ADRs record the design decisions behind the JSON and YAML authoring guides, the baseline linting stack for data files, the schema-validation policy, and the surrounding tooling and portability trade-offs. They are policy-only prose; the implementations live in `.github/instructions/json.instructions.md`, `.github/instructions/yaml.instructions.md`, `.pre-commit-config.yaml`, `.yamllint.yml`, `.gitattributes`, and (for downstream adopters) the optional `schemas/` directory.

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

The default pre-commit stack for JSON and YAML uses `check-json`, `check-yaml`, `yamllint`, `actionlint`, and — as of the worked-example schema rollout — `check-jsonschema` plus `check-metaschema` scoped to the worked-example schema (`schemas/example-config.schema.json`).

**Selected hooks and their roles:**

1. **`check-json` (pre-commit-hooks)** — Validates strict JSON syntax. Fast, dependency-free, fails on duplicate keys, trailing commas, and other strict-JSON violations.
2. **`check-yaml` (pre-commit-hooks)** — Fast YAML parse check. Catches structural errors before slower linters run.
3. **`yamllint`** — YAML style enforcement (indentation, line length, truthy values). Configured via `.yamllint.yml`.
4. **`actionlint`** — GitHub Actions workflow validation, including expression syntax, runner labels, and `shellcheck` integration over `run:` blocks.
5. **`check-jsonschema`** — JSON Schema validation. As of the worked-example schema rollout, this hook is wired by default with two scoped entries: one validates the valid example data files under `schemas/examples/example-config/valid/` against the worked-example schema, and one (`check-metaschema`) self-validates the schema against its declared JSON Schema Draft 2020-12 metaschema. Downstream repositories MAY add additional `check-jsonschema` hook entries for their own schema-backed file families. The "Avoid placeholder schema hooks" rule under the Schema Validation Tiers ADR is still in force: the wiring exists because a real schema and real example data ship in the template, not as a placeholder.

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

### Design Decision: .gitattributes JSON/YAML LF Pinning

`.gitattributes` is **left unchanged** when adding JSON/YAML support. The existing policy — pinning LF line endings only inside byte-exact text fixture locations (`tests/**/golden/**`, `tests/**/goldens/**`, `tests/**/snapshots/**`, `tests/**/__snapshots__/**`, `tests/**/fixtures/**`, `testdata/**`) — is retained. There is no blanket `*.json` / `*.yaml` / `*.yml` LF pin.

This decision was recorded in the Issue 3 PR description (PR #423, "Add `.yamllint.yml` and extend pre-commit JSON/YAML hooks") and is transcribed here.

**Rationale:**

1. **Existing policy is intentionally narrow.** The current `.gitattributes` rules target locations where byte-exact comparison (hash equality, signature verification, snapshot diffing) is the actual correctness contract. JSON and YAML files outside those locations do not have a byte-exact contract — their consumers parse them, not hash them.
2. **Tooling already produces parse-equivalent output across line endings.** `check-json`, `check-yaml`, `yamllint`, `actionlint`, and downstream parsers do not depend on LF endings; CRLF-converted JSON/YAML still validates and still parses identically.
3. **Avoid forcing CRLF rewrites on Windows checkouts that do not need them.** A blanket `*.json text eol=lf` rule would override `core.autocrlf=true` on Windows hosts even for files that are not part of any byte-exact comparison. The cost would land on every Windows contributor for no contract benefit.
4. **Byte-exact JSON/YAML fixtures are already covered.** Any JSON or YAML file living under the existing fixture-location patterns is already pinned to LF by directory rule; no extra extension-level rule is required.

**Downstream opt-in guidance:**

Repos that genuinely need blanket LF pinning for JSON/YAML — for example, projects whose release pipeline hashes JSON manifests, projects publishing YAML policy documents whose checksums are signed, or projects with a strict cross-platform diff-noise policy — can opt in by adding lines such as:

```gitattributes
*.json   text eol=lf
*.jsonc  text eol=lf
*.yaml   text eol=lf
*.yml    text eol=lf
```

These should be added in the project's own `.gitattributes`, with a brief comment explaining the byte-exact contract that motivates them. The template does not ship these rules so that adopters who do not need them are not silently opted in.

**Trade-offs:**

- Pro: Windows contributors are not forced into LF for JSON/YAML files that have no byte-exact contract.
- Pro: Existing byte-exact fixture protection is preserved unchanged.
- Pro: Adopters that need blanket LF can add it deliberately, with rationale documented locally.
- Con: Cross-repo diffs of JSON/YAML files may include CRLF↔LF noise on heterogeneous platforms; this is mitigated by `core.autocrlf` configuration and by editors that preserve the on-disk EOL.

**Alternatives considered:**

- **Blanket `*.json` / `*.yaml` / `*.yml` LF pin in the template `.gitattributes`:** Rejected because it imposes a byte-exact contract on every adopter regardless of whether they have one. The byte-exact-fixture-focused policy is preserved.
- **Conditional per-language opt-in via a commented-out block in the template `.gitattributes`:** Rejected for this iteration to avoid adding code that is dormant by default; the downstream-opt-in snippet above plus this ADR provides the same guidance without dormant rules in the file.

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

### Design Decision: Dedicated Data-File CI Workflow (`data-ci.yml`)

The repository ships a dedicated `.github/workflows/data-ci.yml` workflow that runs JSON, YAML, and GitHub Actions workflow validation as a first-class CI gate, alongside `python-ci.yml`, `powershell-ci.yml`, `terraform-ci.yml`, and `markdownlint.yml`.

**Why a dedicated workflow even though `python-ci.yml` already runs every pre-commit hook:**

- `python-ci.yml` runs `pre-commit run --all-files`, which transitively enforces the JSON/YAML/actionlint hooks. That works functionally but makes data-file validation appear incidental to Python CI.
- A dedicated workflow gives JSON/YAML/Actions validation a distinct required-check identity, clearer ownership, and parity with other per-language workflows. Branch protection rules can require data-file validation independently from Python validation.
- Template adopters who do not use Python should still see data-file validation as a first-class concern; surfacing it only under Python CI would obscure that.

**CI ownership decision:** `python-ci.yml` continues to run the full `pre-commit run --all-files` pipeline as the single canonical aggregate pre-commit gate. `data-ci.yml` runs the data-file hooks (`check-json`, `check-yaml`, `yamllint`, `actionlint`, `check-jsonschema`, and `check-metaschema`) explicitly. The hooks therefore execute in both workflows.

**Trade-off accepted:** The duplication between `python-ci.yml` and `data-ci.yml` is intentional. Splitting responsibility — narrowing `python-ci.yml` to Python-only checks — was rejected because it would change existing CI topology and complicate downstream branch protection migrations for marginal benefit. Visibility and ownership were prioritized over avoiding the duplicated hook execution.

**Distinction from `auto-fix-precommit.yml`:** `data-ci.yml` is a contract enforcement gate that runs on all PRs and pushes. `.github/workflows/auto-fix-precommit.yml` is intentionally NOT a peer of `data-ci.yml`: it is a fix-up workflow scoped to `copilot/**` branches that auto-applies pre-commit fixes and does not enforce results. The two workflows serve different purposes and must not be conflated.

**Schema validation steps:** As of the worked-example schema rollout, `data-ci.yml` runs dedicated `Run check-jsonschema` and `Run check-metaschema` steps that validate the template's worked-example schema (`schemas/example-config.schema.json`), its valid example data files, and the schema itself against its declared Draft 2020-12 metaschema. The dedicated steps are kept alongside the standard data-file hooks so the schema-validation surface is independently visible in CI logs; `pre-commit run check-jsonschema --all-files` covers any additional `check-jsonschema` hooks downstream consumers add to `.pre-commit-config.yaml`.

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
| `python-ci.yml` | **Pre-commit** | ✅ Yes | Foundational check—catches formatting and linting issues |
| `python-ci.yml` | **Type Check (mypy)** | Optional | Set to `continue-on-error: true` by default; make strict when ready |
| `python-ci.yml` | **Test** | ✅ Yes | Ensures tests pass on all platforms |
| `markdownlint.yml` | **Markdown Lint** | ✅ Yes | Ensures documentation quality |
| `powershell-ci.yml` | **Lint (PSScriptAnalyzer)** | Optional | Only if using PowerShell |
| `powershell-ci.yml` | **PowerShell Tests (Pester)** | Optional | Only if using PowerShell with tests |
| `check-placeholders.yml` | **Check for OWNER/REPO Placeholders** | Optional | Only runs in repos created from this template (skipped in template repo itself) |

> **Note:** In the GitHub Actions UI and branch ruleset status-check picker,
> checks appear in the format **`Workflow name / Job name`** (for example,
> `Python CI / Pre-commit`). The **Job Name** column above lists only the
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

### Understanding `needs:` vs Branch Rulesets

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

**How branch rulesets work (external gate):**

- Branch rulesets are configured in repository settings, not in workflows
- They prevent PR merges until selected status checks pass
- They are an external enforcement mechanism that operates at the PR level

**These are complementary:**

- `needs:` optimizes CI execution (skip downstream jobs on early failure)
- Branch rulesets enforce quality gates (block merges until checks pass)
- Using both provides defense in depth

**Recommendation:** Require **both** the `Pre-commit` job AND downstream jobs like `Test` in the branch ruleset. Even though `Test` won't run if `Pre-commit` fails (due to `needs:`), requiring both ensures that:

1. Format/lint issues block the PR (Pre-commit requirement)
2. Test failures block the PR (Test requirement)
3. Skipped jobs (due to upstream failure) also block the PR

### Example Branch Ruleset Configuration

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
- Lint (PSScriptAnalyzer)
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
