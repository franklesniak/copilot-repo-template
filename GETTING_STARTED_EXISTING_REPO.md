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
  - [First-Adoption Preflight Checklist](#first-adoption-preflight-checklist)
  - [Structural Convention Assessment](#structural-convention-assessment)
  - [Required Structural Alignment Catalog](#required-structural-alignment-catalog)
  - [Post-Adoption Issue Drafting](#post-adoption-issue-drafting)
  - [Stack Selection Cleanup Checklist](#stack-selection-cleanup-checklist)
  - [Recommended Adoption Order](#recommended-adoption-order)
  - [Repo Layout Examples](#repo-layout-examples)
- [Getting the Template Files](#getting-the-template-files)
  - [Files to Skip (Example/Demonstration Code)](#files-to-skip-exampledemonstration-code)
- [Adopting Simple Standalone Files](#adopting-simple-standalone-files)
  - [CODEOWNERS](#codeowners)
  - [Dependabot](#dependabot)
  - [Security Policy](#security-policy)
  - [LICENSE File](#license-file)
  - [Code of Conduct](#code-of-conduct)
  - [VS Code Settings](#vs-code-settings)
- [Adopting Issue Templates](#adopting-issue-templates)
  - [Full Adoption](#full-adoption-recommended-if-you-have-none)
  - [Partial Adoption](#partial-adoption-if-you-have-existing-templates)
  - [Customizing Area Dropdowns](#customizing-area-dropdowns)
  - [Creating Required Labels](#creating-required-labels)
- [Adopting PR Template](#adopting-pr-template)
  - [Simple Adoption](#simple-adoption)
  - [Customization Needed](#customization-needed)
  - [Merging with Existing PR Template](#merging-with-existing-pr-template)
- [Adopting GitHub Copilot Instructions](#adopting-github-copilot-instructions)
  - [Protected-File Adoption Step](#protected-file-adoption-step)
  - [Main Instructions File](#main-instructions-file)
  - [Modular Instructions](#modular-instructions)
  - [Merging with Existing Copilot Instructions](#merging-with-existing-copilot-instructions)
  - [Creating Instructions for Other Languages](#creating-instructions-for-other-languages)
  - [Agent Instruction Files (Multi-Platform Support)](#agent-instruction-files-multi-platform-support)
- [Adopting Markdown Linting](#adopting-markdown-linting)
  - [If You Don't Have package.json](#if-you-dont-have-packagejson)
  - [If You Already Have package.json](#if-you-already-have-packagejson)
  - [Copying the Configuration](#copying-the-configuration)
  - [Testing Markdown Linting](#testing-markdown-linting)
- [Adopting Pre-commit Hooks](#adopting-pre-commit-hooks)
  - [Local Validation Prerequisites](#local-validation-prerequisites)
  - [If You Don't Have Pre-commit Configured](#if-you-dont-have-pre-commit-configured)
  - [If You Already Have Pre-commit Configured](#if-you-already-have-pre-commit-configured)
  - [Customizing Hooks](#customizing-hooks)
- [Adopting JSON/YAML Toolchain](#adopting-jsonyaml-toolchain)
- [Adopting CI Workflows](#adopting-ci-workflows)
  - [Understanding Workflow Dependencies](#understanding-workflow-dependencies)
  - [Pre-commit-Only CI Without Python Project CI](#pre-commit-only-ci-without-python-project-ci)
  - [Markdown Lint Workflow](#markdown-lint-workflow)
  - [Auto-fix Pre-commit Workflow](#auto-fix-pre-commit-workflow)
  - [Placeholder Check Workflow](#placeholder-check-workflow)
  - [Python CI Workflow](#python-ci-workflow)
    - [If You Already Have pyproject.toml](#if-you-already-have-pyprojecttoml)
  - [PowerShell CI Workflow](#powershell-ci-workflow)
  - [Merging with Existing CI](#merging-with-existing-ci)
- [Adopting PSScriptAnalyzer Configuration](#adopting-psscriptanalyzer-configuration)
  - [Copying the Configuration](#copying-the-configuration-1)
  - [Using the Configuration](#using-the-configuration)
  - [Analyzer Debt Triage for Existing Repositories](#analyzer-debt-triage-for-existing-repositories)
  - [Customizing Rules](#customizing-rules)
- [Validation and Testing](#validation-and-testing)
  - [Verify All Configurations Work](#verify-all-configurations-work)
  - [Troubleshooting Common Issues](#troubleshooting-common-issues)
- [Cleanup and Documentation](#cleanup-and-documentation)
  - [Files to Review After Adoption](#files-to-review-after-adoption)
  - [Updating Your Project Documentation](#updating-your-project-documentation)
- [Migration Notes for Existing Terraform Repos](#migration-notes-for-existing-terraform-repos)
- [Next Steps](#next-steps)
- [Summary Checklist](#summary-checklist)

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
| **Linting Configurations** | Pre-configured settings for markdownlint, PSScriptAnalyzer, TFLint, and yamllint |
| **Data-File Validation** | JSON, YAML, GitHub Actions, and JSON Schema example validation through pre-commit and `data-ci.yml` |
| **Template Sync Support** | `.template-sync/marker.yml`, `.template-sync/manifest.yml`, `.template-sync/instruction-contracts.yml`, the first-adoption working-tree runner, the marker-aware retained-state and instruction-contract validation helpers, and the candidate table generator with read-only first-adoption preflight/questionnaire and future-sync ledger modes |
| **Dependabot** | Automated dependency update monitoring |
| **CODEOWNERS** | Automatic reviewer assignment for pull requests |
| **Multi-Agent Support** | Instruction files for Cursor Agent, Hermes Agent, Claude Code, OpenAI Codex CLI, and Gemini Code Assist |

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
| Pre-commit Hooks | Python, pre-commit; Terraform and TFLint if retaining Terraform hooks |
| Template Sync Support | Python plus the schema validation dependencies installed with the template's development or pre-commit tooling |
| Python CI Workflow | Python |
| PowerShell CI Workflow | PowerShell |

> **Python runtime note:** Python can remain a development-tool runtime even when your repository does not contain Python project source. Keep Python available anywhere you run `pre-commit`, `check-jsonschema`, `check-metaschema`, or repo-local Python hooks. Removing `.github/workflows/python-ci.yml`, `src/`, or Python tests does not by itself remove Python from validation tooling.

**Verify your installations:**

**Windows (PowerShell):**

```powershell
# Check Git version
git --version

# Check Python version (if adopting Python features or pre-commit)
# Python 3.13 or 3.14 is required by this template's pre-commit hooks and CI workflows
python --version

# Check pip version (if adopting Python features or pre-commit)
python -m pip --version

# Check Node.js version (if adopting markdown linting)
node --version
```

**macOS/Linux/FreeBSD:**

```bash
# Check Git version
git --version

# Check Python version (if adopting Python features or pre-commit)
# Python 3.13 or 3.14 is required by this template's pre-commit hooks and CI workflows
python3 --version

# Check pip version (if adopting Python features or pre-commit)
pip3 --version

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
| VS Code Settings | `.vscode/settings.json` | None | Low |
| Markdown Linting | `.markdownlint.jsonc`, `package.json`, npm scripts | Node.js | Medium |
| Pre-commit Hooks | `.pre-commit-config.yaml`, `.github/scripts/terraform_hooks.py` if retaining Terraform hooks | Python, pre-commit; Terraform and TFLint for Terraform hooks | Medium |
| Template Sync Support | `.template-sync/marker.yml`, `.template-sync/manifest.yml`, `.template-sync/instruction-contracts.yml`, `.template-sync/scripts/materialize_downstream_adoption.py`, `.template-sync/scripts/run_first_adoption_checks.py`, `.template-sync/scripts/validate_marker.py`, `.template-sync/scripts/validate_instruction_contracts.py`, `.template-sync/scripts/generate_sync_candidates.py` (`--preflight` / `--questionnaire`, `--ledger`, `--ledger-only`), `schemas/template-sync-marker.schema.json`, `schemas/template-sync-manifest.schema.json`, `schemas/template-sync-instruction-contracts.schema.json` | Python and schema validation dependencies | Medium |
| PowerShell CI Workflow | `.github/workflows/powershell-ci.yml` | PowerShell, Pester | Medium |
| PSScriptAnalyzer Config | `.github/linting/PSScriptAnalyzerSettings.psd1` | PowerShell | Low |
| Python CI Workflow | `.github/workflows/python-ci.yml` | Python project structure | High |
| Agent Instruction Files | `.cursor/rules/repository-instructions.mdc`, `.hermes.md`, `CLAUDE.md`, `AGENTS.md`, `GEMINI.md` | Adopt `.github/copilot-instructions.md` first | Low |

### First-Adoption Preflight Checklist

When this is the first import of template content into an existing repository, create or update a root `_TODO-repo-init.md` checklist before adopting template files whose contents depend on unresolved maintainer choices. If the repository already records these answers in `_TODO-repo-init.md`, `.template-sync/marker.yml`, or an equivalent committed adoption note named by a prior adoption procedure, carry those answers forward and do not re-ask resolved questions.

If you want an AI coding agent to help run this discovery step, use [Prompt 0: Existing Repository Adoption Preflight](COPILOT_CHAT_PROMPTS.md#prompt-0-existing-repository-adoption-preflight) in `COPILOT_CHAT_PROMPTS.md`. The prompt is an operator aid for collecting preflight facts and questions; this guide and [TEMPLATE_UPDATE_PROCEDURE.md](TEMPLATE_UPDATE_PROCEDURE.md) remain the authoritative adoption and sync procedures.

After copying `.template-sync/manifest.yml`, `.template-sync/scripts/generate_sync_candidates.py`, `.template-sync/scripts/validate_marker.py`, and the template-sync schemas, run the read-only preflight mode before finalizing `_TODO-repo-init.md` or policy-dependent files:

```bash
python .template-sync/scripts/generate_sync_candidates.py --preflight
```

Use `--include-github-metadata` only when the maintainer explicitly opts in to read-only GitHub metadata lookup through the `gh` CLI. Without that flag, the report labels GitHub-only settings as manual-review items instead of guessing.

After retained modules, source repository, reviewed template commit, and protected-file decisions are known, you may run the one-shot materialization helper against a target working tree:

```bash
python .template-sync/scripts/materialize_downstream_adoption.py --help
```

The helper copies only retained manifest-owned files, removes inline blocks for excluded modules, optionally reuses the approved placeholder replacement helper against a staging tree, and refuses to overwrite non-identical existing target files unless a path-scoped decision authorizes or records the conflict. In a non-empty repository, conflicts for existing files such as `README.md`, `LICENSE`, and `.gitignore` are expected first-adoption decisions. Resolve them per path through `template_sync.local_overrides`, `template_sync.protected_file_decisions`, or `template_sync.deferred_protected_candidates`; they are not runtime/tool failures.

Use the concrete `_TODO-repo-init.md` example in [GETTING_STARTED_NEW_REPO.md](GETTING_STARTED_NEW_REPO.md#first-adoption-preflight-checklist) and keep only the items that are unresolved for this repository. Discovery may inspect files and Git metadata first, but agents and maintainers MUST NOT invent contact emails, reporting channels, branch protection policy, CODEOWNERS identities, GHES hosts, label availability, GitHub repository settings, or adoption modes beyond the documented default.

When governance, security, community, CODEOWNERS, issue-template, PR-template, or other template-derived file content depends on unknown owner policy, ask the owner a concrete question before finalizing that file. The checklist records the answer or deferral state; it does not replace asking, and generated or adopted files MUST NOT ship unresolved placeholders or misleading policy defaults.

The default adoption mode for protected files and template-derived governance, community, process, workflow, and collaboration files is `minimal-preservation`: keep upstream wording and structure, substitute placeholders, trim sections owned by unadopted manifest modules, fix broken links, and record required local overrides in `.template-sync/marker.yml` when template sync support is retained. Select `tailored` only when the maintainer explicitly wants broader downstream rewriting for a specific file or file set. For protected files, record that choice in `template_sync.protected_file_decisions` with the required authorization fields before editing. For non-protected files, record that choice in `_TODO-repo-init.md`, `.template-sync/marker.yml` local overrides, or another committed adoption note before editing.

Separate the checklist into:

- **Discoverable repository state:** owner/name, default branch, existing files, existing `.template-sync/marker.yml`, and any committed adoption notes.
- **Manual GitHub settings:** private vulnerability reporting, Discussions, labels such as `triage`, and default-branch protection or rulesets.
- **Maintainer policy decisions:** Code of Conduct contact method, security reporting channel, CODEOWNERS owner/team identity, adoption mode for protected and template-derived files, explicit `tailored` opt-ins, and any GHES host override.
- **Protected-file adoption decisions:** protected instruction-file identification, edit authorization, removal authorization, and marker updates.
- **Unresolved settings:** concrete owner questions, exactly one deferral state, and dependent file/status impact.
- **Resolution evidence:** proof of resolved settings, intentionally deferred items, and placeholder/default safety.

Maintainers should expect concrete questions before adoption is finalized, especially:

- Which contact path should `CODE_OF_CONDUCT.md` publish?
- Which vulnerability reporting channel should `SECURITY.md` publish?
- Which CODEOWNERS owner or team and label-dependent issue-template behavior should be used?
- Should the recorded default branch be kept or renamed, surfaced neutrally even when it is not `main`?

Use this copyable starting point and remove only items that are already resolved for this repository:

```markdown
# Repository Initialization Checklist

This file records first-adoption decisions for this downstream repository. It is downstream-owned state, not an upstream template file, and is excluded from upstream template sync candidate review.

Keep unresolved items in this file until the maintainer completes them through the GitHub UI, an authorized GitHub connector, a safe API call, or a later maintainer action. Do not create this file in the upstream template repository unless the template manifest and sync procedure are deliberately changed to handle it.

When a template-derived file depends on unknown governance, security, community, CODEOWNERS, issue-template, PR-template, or other owner policy, ask the owner a concrete question before finalizing that file. Record unresolved dependent-file items only after the question and the dependent file/status impact are identified.

## Discoverable Repository State

- [ ] Repository owner/name recorded from the GitHub URL or Git remote: `OWNER/REPO`
- [ ] Repository visibility recorded: `[public, private, or internal]`
- [ ] Repository default branch recorded neutrally from GitHub or `git remote show origin`: `[recorded default branch]`
- [ ] Existing `SECURITY.md`, `CODE_OF_CONDUCT.md`, `.github/CODEOWNERS`, issue templates, PR template, and `.github/dependabot.yml` reviewed before replacement.
- [ ] Existing `.template-sync/marker.yml`, `_TODO-repo-init.md`, or equivalent adoption note checked before asking repeated questions.
- [ ] Existing labels reviewed in GitHub under **Issues** > **Labels**.
- [ ] Existing Discussions state reviewed in GitHub under **Settings** > **General** > **Features**.
- [ ] Existing repository rulesets or branch protection reviewed in GitHub under **Settings** > **Rules**.

## Manual GitHub Settings

These settings may be completed through the GitHub UI even when `gh` is unavailable. If a GitHub connector or approved API call is used instead, record the action and evidence in the item.

- [ ] Private vulnerability reporting decision: `[enable, leave disabled, or not available]`
  - UI path: open **Settings** > **Code security and analysis**, then review **Private vulnerability reporting**.
  - After enabling, verify the **Security** tab and `SECURITY.md` private-reporting links.
  - Docs: [Configuring private vulnerability reporting for a repository](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/configuring-private-vulnerability-reporting-for-a-repository). If this link breaks, search `private vulnerability reporting repository` on `docs.github.com`.
  - Evidence: `[date, actor, screenshot/link, connector result, or maintainer note]`
- [ ] GitHub Discussions decision: `[enable or leave disabled]`
  - UI path: open **Settings** > **General** > **Features**, then review **Discussions**.
  - If enabled, verify the repository **Discussions** tab appears and decide whether issue templates should point users there.
  - Docs: [Enabling or disabling GitHub Discussions for a repository](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/enabling-or-disabling-github-discussions-for-a-repository). If this link breaks, search `enable GitHub Discussions repository` on `docs.github.com`.
  - Evidence: `[date, actor, screenshot/link, connector result, or maintainer note]`
- [ ] Labels decision, including `triage`: `[create, skip, or already present]`
  - UI path: open **Issues** > **Labels**, then create or edit labels required by issue templates and local triage policy.
  - Minimum template label to review: `triage` with description `Needs triage` and color `d4c5f9`, unless the maintainer chooses a different triage label.
  - Docs: [Managing labels](https://docs.github.com/en/issues/using-labels-and-milestones-to-track-work/managing-labels). If this link breaks, search `manage labels GitHub issues` on `docs.github.com`.
  - Evidence: `[date, actor, labels created/skipped, connector result, or maintainer note]`
- [ ] Default branch decision: `[keep recorded default branch, rename, or defer]`
  - UI path: open **Settings** > **Branches**, then review the default branch selector before changing it.
  - If the recorded default branch is not `main`, surface that as repository state and ask whether to keep or rename it without implying it is wrong.
  - If renaming, update local clones, open PR bases, branch protection or rulesets, documentation, and CI references.
  - Docs: [Changing the default branch](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-branches-in-your-repository/changing-the-default-branch). If this link breaks, search `change default branch GitHub repository` on `docs.github.com`.
  - Evidence: `[date, actor, old branch, new branch, connector result, or maintainer note]`
- [ ] Repository ruleset or branch-protection decision for the default branch: `[create ruleset, use classic branch protection, leave unchanged, or defer]`
  - UI path: open **Settings** > **Rules** > **Rulesets**, then create or review rules for branch names such as `main` or the recorded default branch.
  - Review required status checks, pull request review requirements, force-push restrictions, deletion restrictions, bypass roles, and enforcement mode.
  - Docs: [Creating rulesets for a repository](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/creating-rulesets-for-a-repository). If this link breaks, search `create repository ruleset GitHub` on `docs.github.com`.
  - Evidence: `[date, actor, ruleset name/link, connector result, or maintainer note]`

## Maintainer Policy Decisions

- [ ] Code of Conduct reporting contact method: `[explicit contact email/address, repository-maintainer profile contact, another maintainer-approved contact path, or intentionally deferred (dependent file status recorded)]`
- [ ] Security vulnerability reporting channel: `[private vulnerability reporting, monitored email, both, or intentionally deferred (dependent file status recorded)]`
- [ ] CODEOWNERS owner/team identity: `[@user or @org/team]`
- [ ] Label-dependent issue-template behavior: `[use template labels, choose alternate labels, remove label metadata, or intentionally deferred (dependent file status recorded)]`
- [ ] Adoption mode for protected and template-derived governance, community, process, workflow, and collaboration files: `minimal-preservation` by default; list any specific `tailored` opt-ins.
- [ ] GHES host override: `[none or github.company.com]`

## Protected-File Adoption Decisions

- [ ] Protected instruction files identified before editing: `.github/copilot-instructions.md`, `.github/instructions/*.instructions.md`, `.cursor/rules/*.mdc`, `.hermes.md`, `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md`.
- [ ] Protected-file edits authorized by maintainer: `[none, path-scoped authorization, or deferred]`
- [ ] Protected-file removals authorized by maintainer: `[none, path-scoped authorization, or deferred]`
- [ ] Protected-file authorization bundle selected: `[full selected-agent bundle, Copilot + Codex only, Copilot + Claude Code only, defer all protected files, or path-by-path tailored selection]`
- [ ] `.github/instructions/*.instructions.md` scope expanded to concrete retained-module instruction files: `[list concrete paths]`
- [ ] Copy-ready maintainer authorization wording captured for each authorized protected edit or removal and mapped to marker fields (`authorization_basis`, `authorized_scope`, and `tailored_authorization_basis` for `tailored` records).
- [ ] Unselected protected agent files recorded separately as `[SKIP, REMOVE-LOCAL, DEFER, PROTECTED-REVIEW, or left untouched with rationale]`; smaller bundle selection alone does not authorize deletion.
- [ ] `.template-sync/marker.yml` protected-file decisions updated if template sync support is retained.

## Unresolved Settings

Tag each unresolved item with exactly one deferral state:

- `not yet asked`: the concrete owner question is identified but has not been asked.
- `asked and deferred`: the owner was asked and intentionally deferred the answer; dependent-file status is recorded.
- `unavailable through current safe tooling / manual review required`: the answer could not be determined through current safe tooling and requires owner or manual reviewer action.

- [ ] Items that must be completed later:
  - Question: `[concrete owner question]`; state: `[not yet asked, asked and deferred, or unavailable through current safe tooling / manual review required]`; owner: `[person/team]`; target date or trigger: `[date/event]`; dependency: `[file, workflow, or GitHub setting]`; dependent-file status: `[not finalized, blocked, placeholder removed, local default withheld, or other concrete status]`
- [ ] Dependent files that must not be considered finalized until the unresolved items are complete:
  - `[path]` depends on `[concrete owner question]`; state: `[same deferral state used above]`; status: `[dependent-file status]`

## Resolution Evidence

- [ ] Every unresolved dependent-file item was recorded only after the concrete owner question and dependent file/status impact were identified.
- [ ] Dependent files are finalized only after their policy questions are resolved, or after the owner intentionally chooses `asked and deferred` and the dependent-file status avoids placeholders and misleading defaults.
- [ ] No generated or adopted file ships unresolved placeholders or misleading policy defaults.
- [ ] Evidence captured for every resolved GitHub setting or policy decision: `[commit, PR, screenshot/link, connector result, API response note, or maintainer note]`
- [ ] Deferred items copied into the adoption PR description, sync summary, issue, or other maintainer-owned follow-up with their deferral state.
```

Downstream work may assume a checklist item is complete only after it is recorded as resolved, or after the owner intentionally chooses `asked and deferred` with dependent-file status, in `_TODO-repo-init.md`, `.template-sync/marker.yml`, or the equivalent committed adoption note named by the adoption procedure. Items tagged `not yet asked` or `unavailable through current safe tooling / manual review required` keep dependent files unfinalized.

### Structural Convention Assessment

Run this assessment before copying, moving, renaming, or deleting structure during first adoption. The assessment is a scope-control tool: it separates structure that must change for selected template modules to work from modernization that can wait.

Inspect at least these repository surfaces:

- Source layout: package roots, module directories, generated source, and language-specific source conventions.
- Test layout: test roots, naming conventions, fixture adjacency, and paths referenced by CI, coverage, or package metadata.
- Fixture and data layout: schema examples, test fixtures, sample configuration, seed data, and generated data outputs.
- License filename: root license file name and whether the repository platform recognizes it without extra configuration.
- CI layout: `.github/workflows/`, workflow names, workflow roots, action inputs, matrix assumptions, and path filters.
- Package and tooling metadata: `package.json`, `pyproject.toml`, `.pre-commit-config.yaml`, `.yamllint.yml`, `.markdownlint.jsonc`, `.tflint.hcl`, and other retained tool entry points.
- Docs location: README, contributing docs, runbooks, ADRs, generated docs, and command references.
- Generated-output patterns: ignored build outputs, generated reports, lock files, schema examples, and cache directories.
- Language-specific conventions: the repository's established ecosystem norms for test names, module roots, fixture placement, lock files, and config locations.
- Template-module assumptions: retained modules from the [Stack Selection Cleanup Checklist](#stack-selection-cleanup-checklist), the module taxonomy in [TEMPLATE_UPDATE_PROCEDURE.md](TEMPLATE_UPDATE_PROCEDURE.md#step-6-use-the-authoritative-module-taxonomy), and any `.template-sync/marker.yml` local overrides or protected-file decisions.

For each structural question, list the realistic options and score them from 1 to 5 against this lightweight rubric:

| Criterion | Score 1 | Score 5 |
| --- | --- | --- |
| Runtime compatibility | Breaks or risks runtime behavior | Preserves runtime behavior |
| User ergonomics | Makes normal commands harder or surprising | Keeps commands discoverable and familiar |
| Ecosystem-convention alignment | Conflicts with common conventions for the stack | Matches common conventions for the stack |
| Template compatibility | Requires repeated local exceptions or broken retained tooling | Works with retained template modules and validators |
| Validation/test readiness | Leaves CI, tests, or linters ambiguous | Keeps validation paths executable and documented |
| Migration burden | Requires broad moves, rewrites, or user retraining | Is small, reversible, or already mostly true |
| Documentation burden | Requires many docs to change or risks stale commands | Keeps user-facing docs easy to update |
| Blast radius | Touches unrelated ownership or behavior | Stays limited to the adoption boundary |

Classify every convention finding with exactly one classification:

| Classification | Use when | Adoption disposition |
| --- | --- | --- |
| **Required for selected template modules** | A retained module, platform feature, validator, or instruction contract cannot work correctly without the structure. | Include the change in adoption or update the retained tool/workflow to the downstream path before adoption is complete. |
| **Strongly recommended during adoption** | The structure is not strictly required, but changing it now materially reduces confusion, drift, or follow-up churn. | Include only when the migration burden and blast radius are low enough for the adoption change. |
| **Post-adoption follow-up** | The change is modernization, cleanup, or repository improvement that is useful but not required for template adoption. | Draft a follow-up issue using [Post-Adoption Issue Drafting](#post-adoption-issue-drafting). |
| **Intentionally not recommended** | The downstream layout is better for the repository, or the template convention would create churn without enough benefit. | Record the rationale and, when template sync support is retained, capture durable path-specific treatment in `.template-sync/marker.yml` local overrides. |

Post-adoption modernization MUST NOT be bundled into template adoption unless the repository owner explicitly authorizes that modernization in the adoption scope. A high rubric score for modernization does not make it adoption scope by itself.

### Required Structural Alignment Catalog

Required structural alignment means a path, filename, directory, or command shape that must exist, or must be explicitly remapped, for a selected template module, repository platform feature, validator, or retained instruction contract to work. It is different from optional modernization or preference-based cleanup.

Use this catalog with the [Stack Selection Cleanup Checklist](#stack-selection-cleanup-checklist). The checklist tells you which module families remain; this catalog tells you which retained structures must align or be explicitly remapped to keep working, with any intentional deviation additionally recorded.

| Category | Required alignment examples | Required vs. recommended boundary |
| --- | --- | --- |
| Platform-recognized root files | A standard root `LICENSE` filename when relying on repository-platform license detection; community-health files at platform-recognized paths when those files are adopted. | Required when platform detection or template links depend on the standard path. Recommended when the existing alternate path is already linked and platform behavior is not needed. |
| Test roots expected by CI | `tests/`, `tests/PowerShell/`, Terraform test paths, schema example fixtures, or other roots referenced by retained workflows, package metadata, or pre-commit hooks. | Required when retained validation invokes those paths. Deferred when test reorganization is cleanup and every retained command already points at the downstream path. |
| Template sync marker and schema support | `.template-sync/marker.yml`, `.template-sync/manifest.yml`, instruction contracts, schemas, and validation scripts retained by `template-sync-support`. | Required when future template sync support is retained. Not required when the downstream repository deliberately excludes the module and records that choice. |
| Workflow and config locations | `.github/workflows/**`, `.pre-commit-config.yaml`, `.yamllint.yml`, `.markdownlint.jsonc`, `package.json` scripts, schema files, and other locations consumed by retained validators. | Required when the tool or platform only reads the conventional path, or when the retained workflow references that path. Recommended when a tool supports an explicit alternate path and the alternate path is already documented. |
| Instruction-contract files | `.github/copilot-instructions.md`, `.github/instructions/*.instructions.md`, root agent files, and `.cursor/rules/**` retained by the `agent-instructions` module. | Required when retained instruction-contract validation expects the file and no authorized removal or waiver exists. Protected-file authorization is still required before changing protected instruction files. |
| Documentation command references | README, contributing docs, runbooks, issue templates, PR templates, and onboarding docs that name adopted commands or paths. | Required whenever adopted structure changes a user-facing command, workflow name, path, prerequisite, or validation step. |

For any move or rename, record which reason applies:

- **Required for platform/template compatibility:** The retained platform feature, validator, workflow, template-sync support, or instruction contract expects the path. Move or rename during adoption, or update the retained consumer to the downstream path and document the mapping.
- **Recommended by convention:** The ecosystem normally expects the path, but retained tooling already works with the downstream layout. Include only when the change is low-risk and owner-approved for adoption scope.
- **Deferred as post-adoption cleanup:** The change is useful modernization but not needed for the adopted template modules. Draft a follow-up issue instead of bundling it.

When a downstream repository intentionally keeps a different layout, record the deviation through `.template-sync/marker.yml` `local_overrides` if template sync support is retained. Use the existing local-override mechanism described in [TEMPLATE_UPDATE_PROCEDURE.md](TEMPLATE_UPDATE_PROCEDURE.md#local-overrides); do not invent a second override file or hidden exception list. The override reason should name the local layout decision, the affected path, and the default future sync disposition.

Line-ending and `.gitattributes` effects are separate from content moves. If adoption changes `.gitattributes` or introduces new EOL attributes for retained files, follow the Step 8 normalization guidance in [TEMPLATE_UPDATE_PROCEDURE.md](TEMPLATE_UPDATE_PROCEDURE.md#normalize-line-endings-after-gitattributes-changes) and record normalization separately from structural moves or content edits.

Whenever adopted structure changes a user-facing command, update the affected docs and workflows in the same adoption change. Examples include changing a test root referenced by CI, moving schema examples, renaming workflow files, changing package scripts, or replacing a copied template command with the downstream repository's command.

### Post-Adoption Issue Drafting

When a structural finding is classified as **Post-adoption follow-up**, draft one or more GitHub Issue descriptions before finalizing adoption. Each draft should be sized for a sophisticated coding agent: self-contained enough to implement without rediscovering adoption context, but narrow enough to review as a normal PR.

Each drafted issue MUST:

- Assume template adoption is already complete.
- Be self-contained to one repository and require no cloning, inspecting, or accessing another repository.
- Include scope, non-goals, acceptance criteria, validation steps, and notes on preserving downstream behavior.
- Include a step to bump `Last Updated` and synchronize any `**Version:**` line for every touched file that carries that metadata.
- State whether protected instruction files are in scope; if they are, require explicit maintainer authorization before editing them.
- Avoid bundling unrelated modernization. Post-adoption modernization MUST NOT be folded back into template adoption unless the owner explicitly authorizes it.

Use this issue-draft skeleton and replace the bracketed text with repository-specific content:

```markdown
## Context

Template adoption is complete. This issue handles one deferred structural follow-up in this repository only.

## Scope

- [Specific paths, commands, or workflow roots to change]
- [Downstream behavior that must be preserved]
- Protected instruction files in scope: [yes/no]. If yes, obtain explicit maintainer authorization before editing them.

## Non-Goals

- Do not revisit template adoption decisions.
- Do not change unrelated structure or formatting.

## Acceptance Criteria

- [Observable result 1]
- [Observable result 2]
- Any touched file with `Last Updated` or `**Version:**` metadata has `Last Updated` bumped and any `**Version:**` line synchronized.

## Validation

- [Command or manual check 1]
- [Command or manual check 2]

## Preservation Notes

- Preserve [runtime behavior, user command, CI behavior, or local policy].
- If protected instruction files become necessary, stop and obtain explicit maintainer authorization before editing them.
```

#### Worked Examples

The following examples use the same issue-draft skeleton fields above. Copy the example that matches the deferred follow-up, then edit only the repository-specific details that differ.

##### Rename Default Branch to `main`

```markdown
## Context

Template adoption is complete. This issue handles the deferred decision to rename this repository's default branch to `main`, if the maintainer confirms that rename is still intended.

## Scope

- Confirm the repository's current default branch from GitHub settings or `git remote show origin` before proposing or making any branch rename.
- Confirm maintainer intent to rename the default branch to `main` before any GitHub setting, connector, API, or local branch action.
- Use the default-branch decision item in the [First-Adoption Preflight Checklist](#first-adoption-preflight-checklist) as the coordination checklist, including local clones, open PR bases, branch protection or rulesets, documentation, and CI references.
- Update repository-local references to the renamed branch after the GitHub default-branch change is maintainer-authorized and complete.
- Protected instruction files in scope: no. If a branch-name reference in a protected instruction file must change, obtain explicit maintainer authorization before editing it.

## Non-Goals

- Do not rename the default branch before the current branch, maintainer intent, and downstream coordination plan are confirmed.
- Do not change repository rulesets, branch protections, CI behavior, or required checks except where the branch rename requires a target-branch update.
- Do not revisit template adoption decisions.
- Do not change unrelated structure or formatting.

## Acceptance Criteria

- The current default branch and maintainer-approved target branch are recorded in the issue or pull request before any rename occurs.
- Open PR bases, branch protection or rulesets, CI references, documentation links, and local-clone communication have been reviewed using the First-Adoption Preflight Checklist default-branch item as the source of truth.
- The GitHub default branch is renamed to `main` only through a maintainer-authorized GitHub UI, connector, or API action.
- Repository-local references that must follow the rename are updated in the same pull request or explicitly recorded as separate follow-up work.
- Any touched file with `Last Updated` or `**Version:**` metadata has `Last Updated` bumped and any `**Version:**` line synchronized.

## Validation

- Verify the repository default branch in GitHub settings after the maintainer-authorized change.
- Verify open pull requests target the intended base branch or have been intentionally retargeted.
- Run the repository's retained CI, lint, and documentation validation commands affected by the rename.
- Search the repository for stale references to the previous default branch and document any intentionally retained historical references.

## Preservation Notes

- Preserve existing branch history, open pull request content, release references, and contributor access.
- Preserve existing ruleset or branch-protection intent while updating only the branch target needed for the rename.
- If protected instruction files become necessary, stop and obtain explicit maintainer authorization before editing them.
```

##### Configure Repository Rulesets After CI Exists

```markdown
## Context

Template adoption is complete. CI now exists in this repository, so this issue handles the deferred setup of repository rulesets for the default branch.

## Scope

- Review the current GitHub rulesets documentation, including [Creating rulesets for a repository](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/creating-rulesets-for-a-repository), before proposing settings.
- Inventory the repository's current CI workflow names, required status checks, review expectations, force-push policy, deletion policy, bypass roles, and enforcement mode.
- Configure or document a repository ruleset for the current default branch only after the maintainer authorizes the GitHub UI, connector, or API action that changes repository settings.
- Protected instruction files in scope: no. If ruleset policy must be documented in a protected instruction file, obtain explicit maintainer authorization before editing it.

## Non-Goals

- Do not imply that a coding agent may change GitHub settings without maintainer authorization.
- Do not replace classic branch protection unless the maintainer explicitly chooses that migration path.
- Do not add new CI jobs solely to satisfy a ruleset.
- Do not revisit template adoption decisions.
- Do not change unrelated structure or formatting.

## Acceptance Criteria

- The proposed ruleset targets the current default branch and references the repository's actual CI check names.
- The ruleset plan identifies required status checks, pull request review requirements, force-push restrictions, deletion restrictions, bypass roles, and enforcement mode.
- Any GitHub settings change is performed only through a maintainer-authorized GitHub UI, connector, or API action.
- The issue or pull request links to current GitHub rulesets documentation rather than branch-protection-only guidance.
- Any touched file with `Last Updated` or `**Version:**` metadata has `Last Updated` bumped and any `**Version:**` line synchronized.

## Validation

- Verify the ruleset appears under **Settings** > **Rules** > **Rulesets** with the intended target branch and enforcement mode.
- Verify required checks in the ruleset exactly match the current CI check names shown by a pull request or workflow run.
- Open or inspect a pull request targeting the default branch to confirm the expected ruleset checks are visible.

## Preservation Notes

- Preserve existing collaborator access, bypass expectations, and release workflow unless the maintainer explicitly approves a change.
- Preserve existing CI workflow behavior; this issue configures repository policy around CI that already exists.
- If protected instruction files become necessary, stop and obtain explicit maintainer authorization before editing them.
```

##### Reorganize a Script-Heavy Repository After Adoption

```markdown
## Context

Template adoption is complete. This issue handles the deferred cleanup of a script-heavy repository whose root-level or mixed-location scripts should be reorganized after baseline validation is stable.

## Scope

- Move repository-owned utility scripts into a consistent `scripts/` or language-specific subdirectory chosen for this repository.
- Update workflows, package scripts, pre-commit hook entries, documentation commands, and test references that invoke the moved scripts.
- Keep script names, command-line arguments, outputs, exit codes, and working-directory assumptions compatible unless a breaking change is explicitly documented and approved.
- Protected instruction files in scope: no. If a protected instruction file references the old script layout, obtain explicit maintainer authorization before editing it.

## Non-Goals

- Do not rewrite script behavior while moving files.
- Do not introduce a new task runner or major dependency.
- Do not reorganize application source code unrelated to the scripts.
- Do not revisit template adoption decisions.
- Do not change unrelated structure or formatting.

## Acceptance Criteria

- Scripts covered by this issue live in the chosen script directory and no retained workflow or documented command points to the old path.
- Existing script invocations continue to work through updated paths or intentionally retained compatibility wrappers.
- CI, pre-commit hooks, package scripts, and developer documentation reference the same script paths.
- The pull request lists any intentionally retained compatibility wrappers and when they may be removed.
- Any touched file with `Last Updated` or `**Version:**` metadata has `Last Updated` bumped and any `**Version:**` line synchronized.

## Validation

- Run the repository's retained pre-commit checks that invoke or inspect scripts.
- Run each moved script's documented command from the repository root.
- Run the retained CI-equivalent commands for workflows that call the moved scripts.
- Search the repository for stale references to old script paths.

## Preservation Notes

- Preserve existing command behavior for contributors and CI.
- Preserve file permissions, line endings, shell targets, and PowerShell compatibility requirements for moved scripts.
- If protected instruction files become necessary, stop and obtain explicit maintainer authorization before editing them.
```

##### Add Tests After Adopting CI

```markdown
## Context

Template adoption is complete. CI now provides a stable validation surface, so this issue adds tests for existing repository behavior without changing that behavior.

## Scope

- Add focused tests for existing scripts, helpers, schemas, or configuration behavior that the repository already relies on.
- Place tests under the repository's retained test root and use the test framework already adopted by the repository.
- Wire the test command into existing CI only when the adopted CI does not already run that test root.
- Protected instruction files in scope: no. If test guidance in a protected instruction file must change, obtain explicit maintainer authorization before editing it.

## Non-Goals

- Do not change runtime behavior to make tests easier to write.
- Do not add a new test framework when an adopted framework already covers the repository's retained stack.
- Do not broaden CI beyond the behavior covered by these tests.
- Do not revisit template adoption decisions.
- Do not change unrelated structure or formatting.

## Acceptance Criteria

- New tests cover the selected existing behavior with at least one passing case and one failure or edge case where applicable.
- The tests run from the repository root with the documented retained test command.
- CI runs the new tests or the issue records the maintainer-approved reason they remain local-only.
- Test fixtures do not contain secrets, private identifiers, or environment-specific absolute paths.
- Any touched file with `Last Updated` or `**Version:**` metadata has `Last Updated` bumped and any `**Version:**` line synchronized.

## Validation

- Run the retained test command for the affected stack.
- Run pre-commit checks that apply to the added tests and fixtures.
- Confirm CI configuration invokes the same test command when CI integration is in scope.

## Preservation Notes

- Preserve existing behavior; tests should characterize current expectations before any later refactor changes them.
- Preserve existing test-root and fixture conventions unless the maintainer approves a structural change.
- If protected instruction files become necessary, stop and obtain explicit maintainer authorization before editing them.
```

##### Consolidate Duplicated Helper Code After Baseline Validation

```markdown
## Context

Template adoption is complete. Baseline validation is in place, so this issue consolidates duplicated helper code that was intentionally left alone during adoption.

## Scope

- Identify duplicated helper logic within this repository's scripts, tests, workflows, or small support modules.
- Extract a shared helper in the repository's existing language and directory conventions.
- Update each duplicate call site to use the shared helper without changing observable behavior.
- Add or update tests for the shared helper and at least one representative call site.
- Protected instruction files in scope: no. If helper usage guidance in a protected instruction file must change, obtain explicit maintainer authorization before editing it.

## Non-Goals

- Do not redesign the surrounding workflow, command-line interface, or module architecture.
- Do not introduce a new package, build system, or major dependency for the shared helper.
- Do not consolidate code that has intentionally different behavior.
- Do not revisit template adoption decisions.
- Do not change unrelated structure or formatting.

## Acceptance Criteria

- Duplicate helper logic is replaced by one shared implementation in the repository's existing helper location.
- Updated call sites preserve inputs, outputs, errors, logging, and exit codes.
- Tests cover the shared helper and demonstrate that at least one updated call site still follows existing behavior.
- The pull request documents any duplicate code intentionally left separate because its behavior differs.
- Any touched file with `Last Updated` or `**Version:**` metadata has `Last Updated` bumped and any `**Version:**` line synchronized.

## Validation

- Run the retained test command for the affected helper and call sites.
- Run pre-commit checks that apply to the changed language and documentation files.
- Run or inspect the affected scripts, workflow steps, or commands to confirm they call the shared helper.

## Preservation Notes

- Preserve current user-facing commands, CI behavior, validation output, and local policy.
- Preserve compatibility with the repository's supported shells, runtimes, and operating systems.
- If protected instruction files become necessary, stop and obtain explicit maintainer authorization before editing them.
```

### Stack Selection Cleanup Checklist

Use this checklist when adopting only part of the template's language/tooling stack. Remove files as a set so CI, pre-commit hooks, Dependabot, and agent instructions do not keep pointing at deleted tools.

#### Python Project/Source Stack

Keep these only when the repository has Python project source, Python tests, or Python packaging metadata:

- `pyproject.toml`
- `src/` or other Python package/source directories
- Python tests such as `tests/test_example.py` and `tests/__init__.py`
- `templates/python/`
- The `# template-sync: begin python-only` … `# template-sync: end python-only` block in `.pre-commit-config.yaml` (contains the Black and Ruff hooks; template-sync strips it automatically when the `python` module is excluded)
- `.github/workflows/python-ci.yml` (type-check + tests). Note: `.github/workflows/precommit-ci.yml` is baseline-scoped and stays even when Python project source is removed.
- The `pip` ecosystem in `.github/dependabot.yml`
- `.github/instructions/python.instructions.md`
- Python validation references in `.github/copilot-instructions.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `README.md`, `CONTRIBUTING.md`, and PR/issue templates

If you remove Python source but keep `pre-commit`, `check-jsonschema`, `check-metaschema`, or repo-local hook wrappers, keep Python installed as development tooling and make that distinction explicit in your docs and CI names.

#### Terraform/HCL Stack

Keep these only when the repository contains Terraform or HCL infrastructure code:

- `.tflint.hcl`
- Terraform examples, modules, templates, and tests, including `templates/terraform/`
- `.github/workflows/terraform-ci.yml`
- Terraform hooks in `.pre-commit-config.yaml`: `terraform-fmt`, `terraform-validate`, and `terraform-tflint`
- `.github/scripts/terraform_hooks.py` if any remaining hook or workflow uses it
- Terraform docs and validation commands
- Any Terraform Dependabot ecosystem added downstream
- `.github/instructions/terraform.instructions.md`
- Terraform validation references in `.github/copilot-instructions.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `README.md`, and `CONTRIBUTING.md`

#### PowerShell Stack

Keep these only when the repository contains PowerShell scripts or Pester tests:

- `.github/workflows/powershell-ci.yml`
- `.github/linting/PSScriptAnalyzerSettings.psd1`
- `tests/PowerShell/`
- `templates/powershell/`
- `.github/instructions/powershell.instructions.md`
- The "PowerShell-Specific (if applicable)" checklist in `.github/pull_request_template.md`
- PowerShell validation references in `.github/copilot-instructions.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `README.md`, and `CONTRIBUTING.md`

### Recommended Adoption Order

For the smoothest experience, adopt features in this order:

1. **Simple standalone files first** — CODEOWNERS, Dependabot, Security Policy
2. **Issue/PR templates** — Low complexity, immediate usability improvements
3. **Copilot instructions** — Enhances AI-assisted development
4. **Linting configurations** — Establishes code quality standards
5. **CI workflows** — Most complex, most dependencies; adopt last

> **Tip:** You don't need to adopt everything. Pick the features that provide the most value for your project.

### Repo Layout Examples

Before starting adoption, understand how your repository is structured. Here are two common patterns:

**Root-Only Repo (Single Configuration):**

A repository with a single Terraform or application configuration:

```text
my-project/
├── .github/
│   ├── copilot-instructions.md
│   ├── instructions/
│   └── workflows/
├── main.tf              # Primary configuration
├── variables.tf         # Input variables
├── outputs.tf           # Output values
├── versions.tf          # Provider version constraints
├── .terraform.lock.hcl  # Dependency lock file
└── README.md
```

**Module-Based Repo:**

A repository containing reusable modules with examples and tests:

```text
my-modules/
├── .github/
│   ├── copilot-instructions.md
│   ├── instructions/
│   └── workflows/
├── modules/
│   └── vpc/
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       ├── versions.tf
│       └── README.md
├── examples/
│   └── basic-vpc/
│       ├── main.tf
│       └── README.md
├── tests/
│   └── vpc.tftest.hcl
└── README.md
```

Choose your adoption approach based on your repository's structure.

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

### Files to Skip (Example/Demonstration Code)

The template repository includes example Python source code and tests that demonstrate coding standards. These files are intended for new repositories created from the template and should **NOT** be copied to existing repositories:

| File/Directory | Purpose | Action |
| --- | --- | --- |
| `src/copilot_repo_template/` | Example Python package demonstrating coding standards | Do not copy |
| `tests/test_example.py` | Example pytest tests for the demo package | Do not copy |
| `tests/__init__.py` | Package marker with template-specific docstring | Do not copy |
| `pyproject.toml` | Configured for the template's example package | Copy only if you need a starting point, then heavily customize |

If you already have Python tests in your existing repository, these template example files would conflict with your existing setup.

**What you SHOULD copy:**

- `.github/` directory contents (workflows, instructions, templates)
- Configuration files (`.markdownlint.jsonc`, `.pre-commit-config.yaml`)
- Community health files (`CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`)
- `templates/` directory (reference templates for starting new test files)

If your existing repository lacks Python project structure and you want to adopt the template's Python CI workflow, see the [Python CI Workflow](#python-ci-workflow) section below for guidance on setting up your own `pyproject.toml` and test structure.

---

## Adopting Simple Standalone Files

These files can be copied directly with minimal modifications.

After copying any placeholder-bearing template files, prefer the helper in `.github/scripts/replace-template-placeholders.py` over ad hoc global find/replace. It replaces only the approved template placeholders and GitHub URL shapes, supports `--github-host` for GitHub Enterprise Server URL contexts, and scans afterward for unresolved placeholders and common broad-replacement corruption such as mutated `REPORT`, `REPOSITORY`, or `REPOSITORIES` text.

Example after copying the helper and the files you intend to adopt:

```bash
python .github/scripts/replace-template-placeholders.py replace \
    --repository "your-username/your-repo-name" \
    --security-contact "security@example.com" \
    --conduct-contact "conduct@example.com" \
    --codeowners-owner "@your-username" \
    --vscode-title "your-repo-name"
```

Use `python3` instead of `python` on systems where Python 3 is exposed only as `python3`. For GitHub Enterprise Server, add `--github-host "github.company.com"`; the helper limits host substitution to approved template URL placeholders and does not rewrite unrelated `github.com` links.

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

Dependabot automatically creates pull requests to update retained dependency and automation surfaces.

**Location:** `.github/dependabot.yml`

`.github/dependabot.yml` itself is owned by the `github-platform` module in
[`.template-sync/manifest.yml`](.template-sync/manifest.yml). The ecosystem
entries inside it scan files owned by other modules. Use the manifest as the
source of truth for file/module ownership, then keep each ecosystem only when
the scanned manifest, lock file, configuration file, or workflow surface remains
in your adopted repository. Remove any ecosystem whose scanned surface was not
retained.

The [Stack Selection Cleanup Checklist](#stack-selection-cleanup-checklist)
calls out stack-level cleanup for the `pip` ecosystem and any downstream
Terraform ecosystem. Use this matrix for the per-ecosystem keep/remove decision:

| Dependabot ecosystem | Scanned file or surface | Target surface module | Keep by default |
| --- | --- | --- | --- |
| `npm` | `package.json` | `markdown` (Markdown tooling, not a Node application) | When the `markdown` module and `package.json` are retained |
| `pip` | `pyproject.toml` or another Python dependency manifest | `python` | Only when the `python` module or a Python dependency manifest is retained |
| `github-actions` | `.github/workflows/**` | `github-actions` | When any workflows are retained |
| `pre-commit` | `.pre-commit-config.yaml` | `baseline` | When `.pre-commit-config.yaml` is retained |
| `terraform` | Terraform sources | `terraform` | Only when the `terraform` module is retained and a Terraform Dependabot ecosystem is added downstream; this template does not ship one by default |

**Steps:**

1. **If you don't have a dependabot.yml file:**
   - Copy `.github/dependabot.yml` from the template
   - Remove ecosystem entries for scanned surfaces you did not retain
   - Keep the template's grouping strategy for any ecosystem you retain unless
     your repository already has a different update grouping policy

2. **If you already have a dependabot.yml file:**
   - Review the template's grouping strategy (groups minor/patch updates)
   - Consider adopting the commit message prefix convention (`chore(deps)`)
   - Merge only the ecosystem entries whose scanned surfaces you retained

**Example: recommended tailored config for a non-Python repository that retains
Markdown tooling, GitHub Actions workflows, and pre-commit:**

This example removes `pip` because no Python dependency manifest is retained,
keeps `npm` for Markdown tooling, and keeps `pre-commit` because
`.pre-commit-config.yaml` remains present.

```yaml
version: 2
updates:
  # Markdown tooling dependencies (package.json)
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
    groups:
      npm-minor-patch:
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

  # Pre-commit hooks (.pre-commit-config.yaml)
  - package-ecosystem: "pre-commit"
    directory: "/"
    schedule:
      interval: "weekly"
    groups:
      pre-commit-minor-patch:
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
   - Clear the security-contact `TODO: Replace` marker after the contact is configured
   - Replace `OWNER/REPO` in the direct private-reporting URL `https://github.com/OWNER/REPO/security/advisories/new` with your repository's `owner/repo` (so the URL points at your repo, not the template)
     - **GHES only:** also replace `github.com` with your GHES host in that URL
   - Or remove the email option and use only GitHub Security Advisories (for public repositories)
   - If private vulnerability reporting is enabled, prefer the direct reporting URL `https://github.com/OWNER/REPO/security/advisories/new`

2. **If you already have a SECURITY.md file:**
   - Review the template's structure for ideas
   - Consider adding sections you may be missing (response timeline, disclosure policy)

> **Note:** Private vulnerability reporting via GitHub Security Advisories is only available for **public repositories**. If your repository is private, you must provide an email contact in SECURITY.md. Use a dedicated security email (e.g., `security@your-domain.com`) rather than a personal email when possible, and do not use a `users.noreply.github.com` address as a real security intake channel.

### LICENSE File

The template includes an MIT License file with the template author's name as the copyright holder.

**Location:** `LICENSE`

**Steps:**

1. **If you want to use the MIT License:**
   - Copy `LICENSE` from the template to your repository root
   - Replace `Frank Lesniak` with your name or organization name (the copyright holder)
   - Optionally update the copyright year to the current year or your project's start year

2. **If you already have a LICENSE file:**
   - Keep your existing license—no action needed

3. **If you want a different license type:**
   - See the [License Customization](OPTIONAL_CONFIGURATIONS.md#license-customization) section in `OPTIONAL_CONFIGURATIONS.md` for guidance on Apache 2.0, proprietary licenses, and updating all license references across your project

### Code of Conduct

The code of conduct defines community standards and expectations for behavior.

**Location:** `CODE_OF_CONDUCT.md` (repository root)

**Steps:**

1. **If you don't have a CODE_OF_CONDUCT.md file:**
   - Copy `CODE_OF_CONDUCT.md` from the template to your repository root
   - Replace `[INSERT CONTACT METHOD]` with an email address, form URL, or other contact method for reporting violations
   - You may use wording such as "contact the repository owners using the contact links on their GitHub profiles" for general conduct contact, but do not use a `users.noreply.github.com` address as the intake channel

2. **If you already have a CODE_OF_CONDUCT.md file:**
   - Review the template's structure for ideas
   - Consider adding sections you may be missing (enforcement ladder, scope definition)

> **Note:** Small personal projects or projects that don't accept external contributions may choose to delete this file entirely. The placeholder check workflow treats the file as optional.

### VS Code Settings

The `.vscode/settings.json` file customizes VS Code behavior for your repository. The template includes a placeholder window title.

**Location:** `.vscode/settings.json`

**Steps:**

1. **If you don't have a `.vscode/settings.json` file:**
   - Copy `.vscode/settings.json` from the template to your `.vscode/` directory
   - Replace the `window.title` value with your repository name

2. **If you already have a `.vscode/settings.json` file:**
   - Review the template's file for settings you may want to add
   - Consider adding the `window.title` setting for easier workspace identification

**Example customization:**

```json
{
    "window.title": "my-awesome-project"
}
```

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

3. **Update `bug_report.yml`:** Replace `OWNER/REPO` placeholders in the security-notice URLs (the private vulnerability reporting form, Security tab, and `SECURITY.md` links). These URLs use the same `https://github.com/OWNER/REPO/...` form as `config.yml`. If you also adopt and keep `.github/workflows/check-placeholders.yml` (an optional adoption step), CI will fail until this substitution is made; if you do not adopt that workflow or you remove it after initial setup, no CI guardrail catches a missed substitution and you must verify the replacement manually.

   **GHES adopters:** In both `config.yml` and `bug_report.yml`, also replace `github.com` with your GHES host (e.g., `github.company.com`). The host substitution is not validated by `.github/workflows/check-placeholders.yml`, but inline YAML comments above the affected blocks (in both files) note the requirement.

4. **Review and customize each template** (see [Customizing Area Dropdowns](#customizing-area-dropdowns))

### Partial Adoption (If You Have Existing Templates)

If you already have issue templates:

1. Compare the template files with your existing templates
2. Copy specific templates you want to add (e.g., just `documentation_issue.yml`)
3. If you have a `config.yml`, merge the `contact_links` sections
4. **If you adopt `bug_report.yml`** (in whole or in part), remember to replace `OWNER/REPO` in the security-notice URLs — and, on GHES, the `github.com` host as well.

### Customizing Area Dropdowns

The issue templates include an "Area" dropdown with default options. Customize for your project:

**In `bug_report.yml` and `feature_request.yml`:**

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

> **Tip:** Update the Area dropdown in both template files to keep them consistent.

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

1. Go to your repository
2. Click **Issues** or **Pull requests**
3. Above the list, click **Labels**
4. Click **New label**
5. Under "Label name", type `triage`
6. Under "Description", type `Needs triage`
7. Edit the color hexadecimal number to `d4c5f9` (light purple)
8. Click **Create label**

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

The template uses an absolute URL with the `OWNER/REPO` placeholder for the contributing guidelines link in the PR template:

```markdown
[contributing guidelines](https://github.com/OWNER/REPO/blob/HEAD/CONTRIBUTING.md)
```

Replace `OWNER/REPO` with your actual organization and repository name, preferably by running `.github/scripts/replace-template-placeholders.py` after copying the template files you intend to keep. If you also adopt and keep `.github/workflows/check-placeholders.yml` (an optional adoption step), CI will fail until this substitution is made; if you do not adopt that workflow or you remove it after initial setup, no CI guardrail catches a missed substitution and you must verify the replacement manually. If your CONTRIBUTING.md is in a different location, update the path inside the URL accordingly. **GHES adopters** must additionally replace `github.com` with their GHES host (e.g., `github.company.com`); the helper supports this with `--github-host`, but the host substitution is not validated by `.github/workflows/check-placeholders.yml` even when that workflow is kept. Absolute URLs are required in `.github/ISSUE_TEMPLATE/*.yml` and `.github/pull_request_template.md`; see the **Issue and PR templates** carve-out in `.github/instructions/docs.instructions.md` and the [Pull Request Template Customization](OPTIONAL_CONFIGURATIONS.md#contributing-guidelines-link) section in `OPTIONAL_CONFIGURATIONS.md`.

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

## Adopting GitHub Copilot Instructions

GitHub Copilot Instructions guide AI-assisted development by providing project-specific coding standards and rules. The template includes both a main instructions file and language-specific instruction files.

### Protected-File Adoption Step

The template treats `.github/copilot-instructions.md`, `.github/instructions/**`, `.cursor/rules/**`, and root agent instruction files such as `.hermes.md`, `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md` as protected governance files. When adopting into an existing repository:

1. Perform non-protected cleanup first, including unused workflows, source examples, tests, templates, and lint configuration.
2. Record the adoption mode for the protected files that remain. Use `minimal-preservation` by default; choose `tailored` only when the maintainer explicitly approves broader rewriting for named files.
3. Record the protected-file changes still needed after stack selection.
4. Obtain explicit maintainer authorization for those protected-file edits or removals. `minimal-preservation` limits the scope of an authorized edit but does not authorize protected-file changes by itself.
5. Before editing or removing a protected file, add a matching `template_sync.protected_file_decisions` marker record. `TAKE` and `MERGE` records need `adoption_mode`, `authorization_basis`, and `authorized_scope`; `tailored` records also need `tailored_authorization_basis`; `REMOVE-LOCAL` records need explicit removal authorization, `authorized_scope`, and a substantive `reason`.
6. For `REMOVE-LOCAL`, make `authorization_basis` name the removed file and mention removal, deletion, or equivalent wording. Reviewers should verify that wording before approving; maintainers who want an automated brittle check can run `python .template-sync/scripts/validate_marker.py --require-marker --strict-remove-local-phrasing`.
7. If a retained protected instruction file intentionally omits a required anchor from `.template-sync/instruction-contracts.yml`, record a matching `template_sync.instruction_contract_waivers` entry with `path`, `anchor`, `reason`, and `authorization_basis`. A waiver is visible validation state, not protected-file edit or removal authorization.
8. Update `.github/copilot-instructions.md`, remaining root agent files, and relevant `.github/instructions/*.instructions.md` files so they match the stacks and tools actually retained.
9. Remove references to deleted tools, workflows, hooks, and validation commands.
10. Bump `Last Updated` and `Version` metadata where those fields exist.
11. Avoid ephemeral implementation-stage language in durable governance docs.

Use this copy-ready checklist for step 4 before creating marker records. Maintainer wording MAY use globs for readability, but implementation MUST expand every glob to concrete protected paths before editing, removing, skipping, deferring, or sending files through protected review. Do not write a glob such as `.github/instructions/*.instructions.md` into `template_sync.protected_file_decisions[].path`; expand it to the concrete instruction files for retained modules. For example, include `.github/instructions/docs.instructions.md` only when the Markdown module is retained, `.github/instructions/yaml.instructions.md` only when the YAML module is retained, and so on. The bundle scope is the retained-module instruction files, not every optional language instruction file in the template.

`minimal-preservation` is the default protected-file adoption mode, but it still requires explicit maintainer authorization before any protected path is edited. Under `minimal-preservation`, the authorized edit scope is limited to placeholder substitution, removal of unadopted-module sections, link fixes, and recorded local overrides required by the downstream repository. It does not authorize broad rewriting, new policy, or structural redesign.

1. **Full selected-agent bundle (`minimal-preservation`)**

   Use this bundle when the repository is retaining the full selected protected agent set. Copy-ready maintainer wording:

   ```text
   I authorize minimal-preservation TAKE or MERGE edits for this protected instruction-file bundle: .github/copilot-instructions.md; the concrete .github/instructions/*.instructions.md files for retained modules; .cursor/rules/repository-instructions.mdc; .hermes.md; AGENTS.md; CLAUDE.md; and GEMINI.md. Authorized scope: substitute repository placeholders, remove unadopted-module sections, fix links affected by retained stack selection, and record required local overrides; no broad rewriting is authorized.
   ```

   Record one concrete `template_sync.protected_file_decisions` entry per retained path with `decision: TAKE` or `decision: MERGE`, `adoption_mode: minimal-preservation`, the copied sentence as `authorization_basis`, and the "Authorized scope" sentence as `authorized_scope`.

2. **Copilot + Codex only (`minimal-preservation`)**

   Use this bundle when the repository is retaining GitHub Copilot guidance and Codex guidance but not other protected agent entry points. Copy-ready maintainer wording:

   ```text
   I authorize minimal-preservation TAKE or MERGE edits for this Copilot + Codex protected instruction-file bundle: .github/copilot-instructions.md; the concrete .github/instructions/*.instructions.md files for retained modules; and AGENTS.md. Authorized scope: substitute repository placeholders, remove unadopted-module sections, fix links affected by retained stack selection, preserve required Codex platform protocol, and record required local overrides; no broad rewriting is authorized.
   ```

   Record one concrete `template_sync.protected_file_decisions` entry per retained path with the same `TAKE` or `MERGE` fields described above. Excluding `.cursor/rules/repository-instructions.mdc`, `.hermes.md`, `CLAUDE.md`, or `GEMINI.md` from this smaller bundle does not authorize deletion. Removal requires a separate `REMOVE-LOCAL` record with removal-specific maintainer wording, `authorized_scope`, and `reason`; deferral or protected review requires a separate `DEFER` or `PROTECTED-REVIEW` record with `reason`; a deliberate no-action decision requires a separate `SKIP` record with `reason`.

3. **Copilot + Claude Code only (`minimal-preservation`)**

   Use this bundle when the repository is retaining GitHub Copilot guidance and Claude Code guidance but not other protected agent entry points. Copy-ready maintainer wording:

   ```text
   I authorize minimal-preservation TAKE or MERGE edits for this Copilot + Claude Code protected instruction-file bundle: .github/copilot-instructions.md; the concrete .github/instructions/*.instructions.md files for retained modules; and CLAUDE.md. Authorized scope: substitute repository placeholders, remove unadopted-module sections, fix links affected by retained stack selection, preserve required Claude Code platform protocol, and record required local overrides; no broad rewriting is authorized.
   ```

   Record one concrete `template_sync.protected_file_decisions` entry per retained path with the same `TAKE` or `MERGE` fields described above. Excluding `.cursor/rules/repository-instructions.mdc`, `.hermes.md`, `AGENTS.md`, or `GEMINI.md` from this smaller bundle does not authorize deletion. Removal requires a separate `REMOVE-LOCAL` record with removal-specific maintainer wording, `authorized_scope`, and `reason`; deferral or protected review requires a separate `DEFER` or `PROTECTED-REVIEW` record with `reason`; a deliberate no-action decision requires a separate `SKIP` record with `reason`.

4. **Defer all protected files**

   Use this bundle when the maintainer wants the non-protected adoption work to proceed but wants protected files reviewed later. Copy-ready maintainer wording:

   ```text
   I do not authorize protected instruction-file edits or removals for this adoption round. Defer all protected-file candidates for explicit later review.
   ```

   Do not create `TAKE`, `MERGE`, or `REMOVE-LOCAL` records from this wording. If template sync support is retained, record each concrete protected candidate with `decision: DEFER` or `decision: PROTECTED-REVIEW` and a substantive `reason` that cites the maintainer deferral.

5. **Path-by-path tailored selection**

   Use this bundle when the maintainer wants broader rewriting for specific protected files. Copy-ready maintainer wording:

   ```text
   For [concrete protected path], I authorize [TAKE or MERGE] in tailored adoption mode. Authorization basis: [maintainer-approved reason this file may be edited]. Authorized scope: [exact permitted rewrite, bounded to this file]. Tailored authorization basis: [maintainer-approved reason minimal-preservation is insufficient]. This authorization applies only to [concrete protected path] and no other protected file.
   ```

   Record one concrete marker entry per path with `adoption_mode: tailored`, `authorization_basis`, `authorized_scope`, and `tailored_authorization_basis`. Any path not named by a tailored authorization remains outside that authorization and needs its own `TAKE`, `MERGE`, `SKIP`, `REMOVE-LOCAL`, `DEFER`, or `PROTECTED-REVIEW` record before action.

### Main Instructions File

**Location:** `.github/copilot-instructions.md`

This file serves as the "constitution" for all Copilot suggestions in your repository. It contains:

- Safety and security rules (non-negotiable)
- Pre-commit discipline requirements
- Language-specific guideline references
- Linting and testing configurations

**Steps:**

1. Copy `.github/copilot-instructions.md` to your `.github/` directory

2. **Customize the "Source of Truth" section** — Point to your project's authoritative documentation:

   ```markdown
   ## Source of Truth

   > **Customize this section** for your project. Point to your authoritative specification or design document. Example:
   >
   > - Read **`docs/spec/requirements.md`** before making changes.
   > - If any instruction here conflicts with the spec, **the spec wins**.
   ```

3. **Update the modular instructions table** — Modify to reflect your project's languages and cross-cutting rules:

   ```markdown
   | Scope | Instruction File | Applies To |
   | --- | --- | --- |
   | Git attributes | `.github/instructions/gitattributes.instructions.md` | `**/.gitattributes` |
   | Markdown/Docs | `.github/instructions/docs.instructions.md` | `**/*.md` |
   | Python | `.github/instructions/python.instructions.md` | `**/*.py` |
   | PowerShell | `.github/instructions/powershell.instructions.md` | `**/*.ps1` |
   ```

4. **Review and modify:**
   - **Pre-commit section** — Update if using different tools or workflows
   - **Testing section** — Update for your test frameworks and locations

5. **Update linting and testing tables** — Modify to reflect your project's languages:
   - **Linting Configurations table** — Remove the PSScriptAnalyzer row if not using PowerShell
   - **Testing Tools table** — Remove rows for languages you're not using (Python row if not using Python, PowerShell row if not using PowerShell)

### Modular Instructions

**Location:** `.github/instructions/`

These files use `applyTo` front matter to automatically apply to matching file patterns:

```yaml
---
applyTo: "**/*.py"
description: "Python coding standards for this repository"
---
```

**Available instruction files:**

| File | Purpose | Recommended For |
| --- | --- | --- |
| `gitattributes.instructions.md` | `.gitattributes` rules for byte-exact text artifacts | All projects |
| `docs.instructions.md` | Markdown/documentation standards | All projects |
| `python.instructions.md` | Python coding standards | Python projects |
| `powershell.instructions.md` | PowerShell coding standards | PowerShell projects |
| `terraform.instructions.md` | Terraform coding standards | Terraform/IaC projects |

**Adoption options:**

1. **Full adoption:** Copy the entire `.github/instructions/` directory
2. **Selective adoption:** Copy only the files relevant to your project's languages

### Merging with Existing Copilot Instructions

If you already have a `.github/copilot-instructions.md` file:

1. **Review both files** — Compare your existing instructions with the template

2. **Merge safety rules** — The template's non-negotiable safety rules are security-focused:
   - No secrets in code or repo
   - Treat all external input as untrusted
   - Allowlisted file access only

   Consider adopting these if not already present.

3. **Merge language guidelines** — Add references to language instruction files

4. **Keep your project-specific guidance** — Preserve any custom rules specific to your project

### Creating Instructions for Other Languages

If your project uses languages not covered by the template (JavaScript, TypeScript, Go, Rust, etc.):

1. Use an existing instruction file as a template

2. Create a new file following the naming pattern: `{language}.instructions.md`

3. Add the `applyTo` front matter:

   ```yaml
   ---
   applyTo: "**/*.ts"
   description: "TypeScript coding standards for this repository"
   ---
   ```

4. Define your project's coding standards for that language

5. Update the language table in `.github/copilot-instructions.md`

### Agent Instruction Files (Multi-Platform Support)

The template includes agent instruction files to support multi-platform AI coding agents:

| File | Target Agent(s) |
| --- | --- |
| `.cursor/rules/repository-instructions.mdc` | Cursor Agent |
| `.hermes.md` | Hermes Agent |
| `CLAUDE.md` | Claude Code, GitHub Copilot coding agent |
| `AGENTS.md` | OpenAI Codex CLI, GitHub Copilot coding agent |
| `GEMINI.md` | Gemini Code Assist, GitHub Copilot coding agent |

These files are thin entry points for their respective AI coding platforms. `.github/copilot-instructions.md` remains canonical, and the root agent files keep only a minimal inline summary of the highest-priority shared rules plus any platform-specific guidance.

**Adoption steps:**

1. **Copy agent files** — Copy the agent files you want from the template repository to your repository root
2. **Update to match your project** — If you customized `.github/copilot-instructions.md`, keep the copied agent files limited to a minimal inline summary of the highest-priority shared rules plus any platform-specific notes you need
3. **Remove unneeded files** — Delete agent files for platforms you do not use

---

## Adopting Markdown Linting

Markdown linting enforces consistent formatting across your documentation. The template uses markdownlint-cli2 with a configuration optimized for auto-fixable rules.

**Required files:**

- `.markdownlint.jsonc` — Linting rules configuration
- `package.json` — npm scripts and dependencies

**Optional files:**

- `.github/workflows/markdownlint.yml` — CI workflow
- `.github/scripts/lint-nested-markdown.js` — Lints markdown in code blocks

### If You Don't Have package.json

If your project doesn't have a `package.json`:

1. Copy `package.json` from the template

2. Update the metadata for your project:

   ```json
   {
     "name": "your-project-name",
     "description": "Your project description",
     "author": "Your Name"
   }
   ```

3. Install dependencies:

   **Windows (PowerShell) / macOS / Linux:**

   ```bash
   npm install
   ```

### If You Already Have package.json

If your project already has a `package.json`:

1. **Merge the scripts section** — Add these scripts:

   ```json
   {
     "scripts": {
       "lint:md": "markdownlint-cli2 \"**/*.md\" \"#node_modules\" \"#.pytest_cache\"",
       "lint:md:nested": "node .github/scripts/lint-nested-markdown.js"
     }
   }
   ```

2. **Merge devDependencies** — Add these packages (check template for current versions):

   ```json
   {
     "devDependencies": {
       "markdownlint": "^0.40.0",
       "markdownlint-cli2": "^0.22.1"
     }
   }
   ```

   > **Note:** If adopting the nested markdown linting script, also add `glob`, `jsonc-parser`, and `markdown-it`.

3. Run `npm install` to install the new dependencies

### Copying the Configuration

1. Copy `.markdownlint.jsonc` to your repository root

2. Review the rules and adjust for your project's preferences. Key configurable rules:

   | Rule | Default | Purpose |
   | --- | --- | --- |
   | `MD003` | ATX style (`#`) | Heading style |
   | `MD004` | Dashes | Unordered list marker |
   | `MD029` | Ordered (1. 2. 3.) | Ordered list prefix |
   | `MD035` | `---` | Horizontal rule style |

3. **Optional:** Copy `.github/scripts/lint-nested-markdown.js` if you have markdown embedded in code blocks (common in documentation-heavy projects)

   > **Tip:** See [Nested Markdown Linting Configuration](OPTIONAL_CONFIGURATIONS.md#nested-markdown-linting-configuration) for details on using this script.

### Testing Markdown Linting

Run the linter to verify configuration:

**Windows (PowerShell) / macOS / Linux:**

```bash
npm run lint:md
```

If many errors appear, you have three options:

1. **Fix the files** — Run with `--fix` to auto-correct:

   ```bash
   npx markdownlint-cli2 "**/*.md" "#node_modules" "#.pytest_cache" --fix
   ```

2. **Adjust rules** — Modify `.markdownlint.jsonc` to match your project's existing style

3. **Disable specific rules** — Set rules to `false` in the configuration

---

## Adopting Pre-commit Hooks

Pre-commit hooks run automated checks before each commit, catching issues early in the development process.

**Prerequisites:**

- Python installed (3.13 or 3.14)
- pre-commit installed (see installation steps below; pipx/Homebrew installs make `pre-commit` available via PATH, pip installs require module invocation)
- HashiCorp Terraform and TFLint installed if you keep the Terraform hooks

### Local Validation Prerequisites

Before running adopted validation commands:

- Run `npm install` or `npm ci` before npm-backed Markdown checks such as `npm run lint:md:nested`.
- Install `pre-commit` in the active Python environment before running `pre-commit run --all-files`, or use the `python -m pre_commit` / `python3 -m pre_commit` form documented below.
- Treat `pre-commit install` as a local developer action. Automation should usually run `pre-commit run --all-files` directly unless the workflow explicitly needs Git hooks installed.
- Keep Python available for Python-based development tooling such as `pre-commit`, `check-jsonschema`, `check-metaschema`, and repo-local hook wrappers, even if you do not adopt Python project CI.

> **Why pipx is recommended:**
>
> When you install Python packages with CLI tools using `pip`, the executables are placed in a `Scripts` folder (Windows) or `bin` folder (macOS/Linux) that may not be in your system PATH. This can cause "command not found" errors.
>
> `pipx` addresses this by installing Python CLI tools in isolated environments and exposing their executables from a single, well-defined binary directory. To make that directory available on the command line, you must run `pipx ensurepath` once (and restart your shell); after that, new tools installed with `pipx` will typically be usable without additional PATH changes. This is the [official recommendation from the pre-commit project](https://pre-commit.com/#install).
>
> If the `pipx` command itself is not yet on your PATH (for example, just after installation on Windows), you can invoke it via the Python module instead, such as `python -m pipx ensurepath` on Windows or `python3 -m pipx ensurepath` on macOS/Linux/FreeBSD for the initial setup.
>
> If you prefer to use `pip`, you can invoke pre-commit as a Python module using `python -m pre_commit` (Windows) or `python3 -m pre_commit` (macOS/Linux/FreeBSD) instead of the `pre-commit` command directly.

**Install pre-commit:**

**Windows (PowerShell):**

**Option 1: Using pipx (recommended):**

```powershell
# First, upgrade pip to the latest version (recommended)
python -m pip install --upgrade pip

# Install pipx
python -m pip install pipx

# Configure PATH (use module invocation in case pipx isn't on PATH yet)
python -m pipx ensurepath
```

Then install pre-commit:

```powershell
# Use module invocation to ensure it works even if pipx isn't on PATH
python -m pipx install pre-commit
```

> **Note:** You need to restart your PowerShell window (or open a new one) before running `pre-commit` directly by name, because PATH changes only apply to new shells. Using `python -m pipx` avoids needing `pipx` on PATH and lets you install packages in the same session, but `pipx run pre-commit` runs from a temporary environment and should not be used for `pre-commit install` (it can create hooks that reference a non-existent interpreter).

**Option 2: Using pip:**

```powershell
# First, upgrade pip to the latest version (recommended)
python -m pip install --upgrade pip

# Then install pre-commit
python -m pip install pre-commit
```

> **Note:** When using pip, the `pre-commit` command may not be recognized because Python's `Scripts` folder is not always added to PATH. Use `python -m pre_commit` instead of `pre-commit` for all commands.

**macOS/Linux/FreeBSD:**

**Option 1: Using pipx (recommended):**

> **Important (PEP 668 systems):** On newer Linux distributions (Ubuntu 23.04+, Fedora 38+) and some macOS configurations, `python3 -m pip install` commands fail with an `externally-managed-environment` error. If you're on one of these systems, **skip the pip commands below** and install pipx via your OS package manager instead:
>
> - Debian / Ubuntu: `sudo apt install pipx && pipx ensurepath`
> - Fedora: `sudo dnf install pipx && pipx ensurepath`
> - macOS (Homebrew): `brew install pipx && pipx ensurepath`
>
> After running `pipx ensurepath`, restart your terminal, then proceed to the "Then install pre-commit" step below.

If pip works on your system:

```bash
# First, upgrade pip to the latest version (recommended)
python3 -m pip install --upgrade pip

# Install pipx
python3 -m pip install pipx

# Configure PATH (use module invocation in case pipx isn't on PATH yet)
python3 -m pipx ensurepath
```

Then install pre-commit:

```bash
# Use module invocation to ensure it works even if pipx isn't on PATH
python3 -m pipx install pre-commit
```

> **Note:** You need to restart your terminal (or open a new one) before running `pre-commit` directly by name, because PATH changes only apply to new shells. Using `python3 -m pipx` avoids needing `pipx` on PATH and lets you install packages in the same session, but `pipx run pre-commit` runs from a temporary environment and should not be used for `pre-commit install` (it can create hooks that reference a non-existent interpreter).

**Option 2: Using Homebrew (macOS only):**

```bash
brew install pre-commit
```

**Option 3: Using pip:**

> **Important (PEP 668 systems):** On newer Linux distributions (Ubuntu 23.04+, Fedora 38+) and some macOS configurations, `python3 -m pip install` commands fail with an `externally-managed-environment` error. If you're on one of these systems, **do not use pip**—use Option 1 (pipx via OS package manager) instead:
>
> - Debian / Ubuntu: `sudo apt install pipx && pipx ensurepath`
> - Fedora: `sudo dnf install pipx && pipx ensurepath`
> - macOS (Homebrew): `brew install pipx && pipx ensurepath`
>
> After running `pipx ensurepath`, restart your terminal, then run `pipx install pre-commit`.

If pip works on your system:

```bash
# First, upgrade pip to the latest version (recommended)
python3 -m pip install --upgrade pip

# Then install pre-commit
python3 -m pip install pre-commit
```

> **Note:** When using pip, the `pre-commit` command may not be recognized if Python's `bin` folder is not in your PATH. Use `python3 -m pre_commit` instead of `pre-commit` for all commands.

### If You Don't Have Pre-commit Configured

If your project doesn't have a `.pre-commit-config.yaml`:

1. Copy `.pre-commit-config.yaml` to your repository root

2. If you keep the Terraform hooks, also copy `.github/scripts/terraform_hooks.py`

3. Review the hooks and remove those for languages you don't use:

   ```yaml
   # Remove this section if not using Python
   - repo: https://github.com/psf/black
     rev: 26.1.0
     hooks:
       - id: black
         args: [--line-length=100]

   # Remove this section if not using Python
   - repo: https://github.com/astral-sh/ruff-pre-commit
     rev: v0.14.14
     hooks:
       - id: ruff-check
         args: [--fix, --line-length=100]
   ```

4. Install the hooks:

   **If you installed with pipx (Windows):**

   ```powershell
   pre-commit install
   ```

   **If you installed with pipx or Homebrew (macOS/Linux/FreeBSD):**

   ```bash
   pre-commit install
   ```

   **If you installed with pip (Windows):**

   ```powershell
   python -m pre_commit install
   ```

   **If you installed with pip (macOS/Linux/FreeBSD):**

   ```bash
   python3 -m pre_commit install
   ```

5. Run all hooks to verify:

   **If you installed with pipx or Homebrew:**

   ```bash
   pre-commit run --all-files
   ```

   **If you installed with pip (Windows):**

   ```powershell
   python -m pre_commit run --all-files
   ```

   **If you installed with pip (macOS/Linux/FreeBSD):**

   ```bash
   python3 -m pre_commit run --all-files
   ```

### If You Already Have Pre-commit Configured

If your project already uses pre-commit:

1. Compare your `.pre-commit-config.yaml` with the template

2. Consider adding hooks you may be missing:

   **General hooks (recommended for all projects):**
   - `trailing-whitespace`
   - `end-of-file-fixer`
   - `check-yaml`
   - `check-added-large-files`

   **Python hooks:**
   - `black` (formatting)
   - `ruff` (linting)

   **Markdown hooks:**
   - `markdownlint-cli2`

   **Terraform hooks:**
   - `terraform-fmt`
   - `terraform-validate`
   - `terraform-tflint`

   If you add the Terraform hooks, copy `.github/scripts/terraform_hooks.py` too.

3. Update hook versions if the template has newer ones

4. Run all hooks to verify:

   **If you installed with pipx or Homebrew (same command on all platforms/shells):**

   ```bash
   pre-commit run --all-files
   ```

   **If you installed with pip (Windows):**

   ```powershell
   python -m pre_commit run --all-files
   ```

   **If you installed with pip (macOS/Linux/FreeBSD):**

   ```bash
   python3 -m pre_commit run --all-files
   ```

### Customizing Hooks

**Adjust line length for Black/Ruff:**

```yaml
- repo: https://github.com/psf/black
  rev: 26.1.0
  hooks:
    - id: black
      args: [--line-length=88]  # Change from 100 to 88 (Black's default)
```

**Add hooks for other languages:**

```yaml
# Example: Prettier for JavaScript/TypeScript
- repo: https://github.com/pre-commit/mirrors-prettier
  rev: v3.1.0
  hooks:
    - id: prettier
      types_or: [javascript, typescript, json, yaml]
```

**Handling hook environment issues:**

| Issue | Platform | Solution |
| --- | --- | --- |
| `pre-commit` not recognized | Windows | Use `python -m pre_commit` instead of `pre-commit`, or reinstall using `pipx` |
| `pre-commit` command not found | macOS/Linux | Use `python3 -m pre_commit` instead of `pre-commit`, or reinstall using `pipx` or Homebrew |
| `pip` not recognized | Windows | Use `python -m pip` instead of `pip` |
| `pip` not found | macOS/Linux | Use `python3 -m pip` instead of `pip` |
| `externally-managed-environment` error | Linux/macOS | Install pipx via OS package manager (`sudo apt install pipx`, `sudo dnf install pipx`, or `brew install pipx`) then run `pipx ensurepath` and use `pipx install pre-commit` (or `python3 -m pipx install pre-commit`) |
| Python not found | Windows | Reinstall Python and check "Add Python to PATH" |
| Hooks fail to initialize | All | See [Hook initialization troubleshooting](#hook-initialization-troubleshooting) below |

### Hook initialization troubleshooting

If hooks fail to initialize, follow these steps based on your installation method:

**If `pre-commit` is on your PATH:**

Run the following to clear the cache and reinstall hooks:

```bash
pre-commit clean
pre-commit install
```

**If `pre-commit` is NOT on your PATH:**

First, fix your PATH configuration or use module invocation:

- **pipx users:** Run `pipx ensurepath` (or `python -m pipx ensurepath` / `python3 -m pipx ensurepath` if `pipx` is not on your PATH) and restart your terminal, then run the commands above.

  > **Note:** Do not use `pipx run pre-commit install` because it runs from a temporary environment and can create hooks that reference a non-existent interpreter.

- **Homebrew users (macOS):** Ensure your Homebrew `bin` directory (e.g., `/opt/homebrew/bin` or `/usr/local/bin`) is on your PATH, then run the commands above.

- **pip users:** Use module invocation:

  Windows (PowerShell):

  ```powershell
  python -m pre_commit clean
  python -m pre_commit install
  ```

  macOS/Linux:

  ```bash
  python3 -m pre_commit clean
  python3 -m pre_commit install
  ```

---

## Adopting JSON/YAML Toolchain

If you are adopting the template's JSON/YAML support into an existing repository, work through the following steps. Each step is independent — adopt only the pieces you need.

> **Do not duplicate full JSON/YAML policy here.** The authoritative authoring rules live in [`.github/instructions/json.instructions.md`](.github/instructions/json.instructions.md) and [`.github/instructions/yaml.instructions.md`](.github/instructions/yaml.instructions.md). Link to those files from your own documentation rather than copying their contents.

### Default Template Behavior

The template already ships JSON and YAML as first-class supported formats:

- `.github/instructions/json.instructions.md` and `.github/instructions/yaml.instructions.md` define the authoring rules.
- `.yamllint.yml` configures the default YAML style policy.
- `.pre-commit-config.yaml` wires `check-json`, `check-yaml`, `yamllint`, `actionlint`, two `check-jsonschema` hook entries (the worked-example `Validate example-config valid examples` hook plus the `validate-dependabot-config` hook that validates `.github/dependabot.yml` against `vendor.dependabot`), and `check-metaschema`.
- `.github/workflows/data-ci.yml` re-runs those data-file hooks as a dedicated CI check.
- `schemas/` contains a removable worked example (`schemas/example-config.schema.json` and `schemas/examples/example-config/`) plus `schemas/README.md`.
- `tests/test_schema_examples.py` verifies valid and invalid schema-example fixtures when the schema example is retained.
- `templates/json/` and `templates/yaml/` provide starter content for downstream repositories to copy and adapt.

### Optional Downstream Adoption

For an existing repository, adopt only the pieces that match your stack:

- Copy the JSON and YAML instruction files when the repository contains those formats.
- Copy `.yamllint.yml` when you want the template's default YAML style policy.
- Add or merge the data-file pre-commit hooks that apply to your files.
- Optionally copy `schemas/` when you want schema-backed contract examples.
- Alternatively, start from `templates/json/` and `templates/yaml/` when you want starter files without copying the template's worked example verbatim.
- Optionally copy `.github/workflows/data-ci.yml` when you want JSON/YAML/Actions validation as its own CI check.
- Optionally copy `tests/test_schema_examples.py` if you adopt schema-example contract testing.
- Optionally adopt the stricter `templates/yaml/yamllint.strict.yml` configuration if your repository wants a stricter YAML policy than the template default.

### Removal and De-scope Paths

If you already copied the JSON/YAML stack into an existing repository and later decide to remove part of it, keep the removals consistent:

- To remove JSON-specific guidance, delete `.github/instructions/json.instructions.md` and `templates/json/`, then remove the `check-json` hook only after confirming no strict `.json` files remain.
- To remove the worked schema example, delete `schemas/example-config.schema.json`, `schemas/examples/example-config/`, and `tests/test_schema_examples.py` if no schema examples remain; also remove the worked-example `check-jsonschema` hook entry (`Validate example-config valid examples`) and the `check-metaschema` hook from `.pre-commit-config.yaml`. Keep any other `check-jsonschema` hook entries that validate non-example files against built-in vendor schemas (for example, the `validate-dependabot-config` entry that validates `.github/dependabot.yml` against `vendor.dependabot`).
- To remove YAML-specific guidance, delete `.github/instructions/yaml.instructions.md`, `templates/yaml/`, and `.yamllint.yml`; remove `check-yaml`, `yamllint`, and `actionlint` from `.pre-commit-config.yaml` only if no YAML files or GitHub Actions workflows remain.
- To remove dedicated data-file CI, delete `.github/workflows/data-ci.yml` or remove only the steps whose hook IDs no longer exist.
- Keeping `.github/workflows/*.yml` while removing YAML validation is contradictory because GitHub Actions workflows are YAML. Flag and resolve that contradiction during adoption rather than leaving workflows without YAML guidance.

### Downstream-only Ecosystem Validators

Validators for ecosystems such as Kubernetes, OpenAPI, Helm, and Ansible are downstream-only choices. Add them only when the repository actually uses that ecosystem; they are not part of the template's default JSON/YAML toolchain.

### 1. Start with the Instruction Files

Copy the JSON and YAML authoring guides into your repository. They are small, self-contained, and apply repository-wide:

- `.github/instructions/json.instructions.md`
- `.github/instructions/yaml.instructions.md`

If your repository already has equivalents, merge the rules rather than overwriting. Pay particular attention to the dialect policy (strict `.json` vs. `.jsonc`, no JSON5 by default) and the schema-validation tier guidance.

### 2. Add `.yamllint.yml`

Copy `.yamllint.yml` to the repository root. It extends `default`, enforces 2-space indentation, sets the line-length warning at 120 characters, and disables `truthy.check-keys` so unquoted GitHub Actions `on:` keys are accepted.

If you already have a yamllint configuration, reconcile its rules with the YAML authoring guide rather than replacing your file wholesale.

If your repository wants a stricter policy, compare the default file with `templates/yaml/yamllint.strict.yml` and adopt the stricter settings intentionally.

### 3. Add or Merge Pre-commit Hooks

Add the following hooks to your `.pre-commit-config.yaml` (or merge them with your existing configuration) so the JSON/YAML toolchain runs locally and in CI:

- `check-json` — **must** be scoped to strict `.json` files only. Use `files: \.json$` so the hook does **not** run against `.jsonc`.
- `check-yaml` — basic YAML syntax check.
- `yamllint` — style and structural checks driven by `.yamllint.yml` (`args: [-c, .yamllint.yml]`).
- `actionlint` — GitHub Actions workflow linting (only needed if your repository contains workflow files; on networks that block Go module downloads, the hook's first-run install can fail — CI is the shared enforcement environment in that case).
- `check-jsonschema` — JSON Schema validation for the worked example and any real schema-backed file families you adopt.
- `check-metaschema` — schema self-validation for project-owned schemas that declare a supported JSON Schema metaschema.

The repository's `.pre-commit-config.yaml` shows the current pinned versions and exact configuration; copy from there rather than retyping.

### 4. Decide Whether `.jsonc` Needs Stricter Tooling

The default pre-commit stack does **not** validate `.jsonc` syntax — `check-json` is intentionally limited to strict `.json`. Inspect the `.jsonc` files in your repository (for example, `.markdownlint.jsonc` or other tool configurations that ship with a `.jsonc` extension) and decide whether they warrant adding **JSONC-aware tooling** (a JSONC-aware parser, linter, or schema validator). If they are small, well-controlled, and consumed by tools that understand JSONC, no extra tooling is required. If `.jsonc` files are load-bearing, adopt JSONC-aware tooling rather than retrofitting `check-json`. The repository's JSON authoring guide reserves JSONC syntax for files that actually use the `.jsonc` extension; `.json` files **MUST** remain strict JSON, so they are out of scope for this step.

### 5. Add `actionlint` for GitHub Actions

If your repository has any GitHub Actions workflow files (`.github/workflows/*.yml`), keep or add the `actionlint` pre-commit hook. It validates workflow syntax, expression usage, and runner labels, and may also run ShellCheck over `run:` blocks when `shellcheck` is available on the contributor's `PATH`. The default pre-commit hook installs only `actionlint` itself, so ShellCheck coverage of `run:` blocks is conditional on a separate local `shellcheck` install.

### 6. Adopt `schemas/` and `check-jsonschema` Gradually

Schemas are opt-in and **should be added gradually**, only for **load-bearing** files (files whose shape is depended on by build, deploy, runtime, release automation, or downstream consumers).

- Copy the `schemas/` directory (including `schemas/README.md`) only if you intend to define real schemas. The template ships `schemas/` with one clearly removable worked example (`example-config.schema.json` plus example data under `schemas/examples/example-config/`) wired into pre-commit and `data-ci.yml`. If you are not adopting schema-backed validation, follow the [downstream removal checklist](schemas/README.md#downstream-removal-checklist) in `schemas/README.md` to take the worked example out, or skip copying the directory entirely.
- If you want starter content instead of the active worked example, copy from `templates/json/` and adapt the files into your own `schemas/` directory.
- When you add a real schema, add **one `check-jsonschema` hook per real schema-backed file family**, scoped to the files that family covers (for example, `^config/.*\.json$`). See [`schemas/README.md`](schemas/README.md) for an illustrative hook example.
- Do **not** add placeholder hooks for schemas that do not yet exist, and do **not** validate every JSON or YAML file by default. `check-json` and `check-yaml` already cover syntax; `check-jsonschema` is for contract checks against specific file families.

> **No docs should imply that all JSON/YAML files require schemas.** Schemas are reserved for load-bearing contracts; most fixtures, examples, and ad-hoc configs do not need them.

### 7. Avoid Ecosystem Validators Unless You Use Those Ecosystems

Adopt ecosystem-specific validators (Kubernetes manifest validators, OpenAPI validators, Helm validators, Ansible validators, and so on) **only** when the repository actually uses those ecosystems. Generic YAML guidance does not require validators that are irrelevant to your stack, and adding them creates noise without enforcing anything useful.

### Notes on Formatting

- **Prettier is opt-in** and is not part of the default pre-commit toolchain. The default stack does not use Prettier on JSON or YAML, and it does **not** rely on Prettier (or any other tool) to sort JSON keys. The JSON authoring guide preserves intentional grouping and tool-managed key order.
- **JSON5 is not enabled by default.** The JSON authoring guide intentionally omits `.json5`. Do not introduce JSON5 without an explicit, documented project decision.

---

## Adopting CI Workflows

The template includes several GitHub Actions workflows. Adopt only the ones relevant to your project.

### Understanding Workflow Dependencies

Before adopting workflows, understand their requirements:

| Workflow | Dependencies | Prerequisites |
| --- | --- | --- |
| `markdownlint.yml` | `package.json` with markdownlint-cli2 | Node.js |
| `auto-fix-precommit.yml` | `.pre-commit-config.yaml` | Python |
| `check-placeholders.yml` | None | Template placeholders in files |
| `python-ci.yml` | Python project structure, `pyproject.toml` | Python |
| `powershell-ci.yml` | PowerShell scripts, Pester tests | PowerShell |
| `data-ci.yml` | `.pre-commit-config.yaml`, `.yamllint.yml` (and, for schema validation, `schemas/`) | Python (for `pre-commit`) |

### Pre-commit-Only CI Without Python Project CI

If your repository removes Python project source but keeps Python-based pre-commit hooks, do not interpret that as removing Python from CI entirely. Use a narrow hygiene workflow that installs Python only to run `pre-commit`, `check-jsonschema`, `check-metaschema`, or other Python-based hooks.

Name and comment the workflow so it is clearly repository hygiene tooling, not Python application validation. For example, a workflow named "Repository Hygiene" can run `actions/setup-python`, install `pre-commit`, and execute `pre-commit run --all-files` without running pytest, mypy, or package installation for Python source.

### Markdown Lint Workflow

**Location:** `.github/workflows/markdownlint.yml`

**Purpose:** Enforces consistent Markdown formatting in CI.

**Prerequisites:**

- `markdownlint-cli2` in `package.json`
- `.markdownlint.jsonc` configuration file

**Steps:**

1. Copy `.github/workflows/markdownlint.yml` to your `.github/workflows/` directory
2. The workflow runs automatically on push and pull requests

### Auto-fix Pre-commit Workflow

**Location:** `.github/workflows/auto-fix-precommit.yml`

**Purpose:** Automatically fixes pre-commit issues on `copilot/**` branches. This is useful for AI-assisted development where the Copilot Coding Agent may push code that doesn't pass pre-commit checks.

**Prerequisites:**

- `.pre-commit-config.yaml` configured

**Steps:**

1. Copy `.github/workflows/auto-fix-precommit.yml` to your `.github/workflows/` directory
2. The workflow triggers only on `copilot/**` branches when pushed by `copilot-swe-agent[bot]`

> **Note:** This workflow is optional but recommended if you use GitHub Copilot Coding Agent. If you don't use the Copilot Coding Agent, you can skip adopting this workflow. If you've already adopted it but later decide to remove it, see [Auto-fix Pre-commit Workflow Configuration](OPTIONAL_CONFIGURATIONS.md#auto-fix-pre-commit-workflow-configuration) for removal instructions.

### Placeholder Check Workflow

**Location:** `.github/workflows/check-placeholders.yml`

**Purpose:** Verifies that `OWNER/REPO` placeholders have been replaced after copying from the template.

**No configuration required.** The workflow:

- Runs automatically on push, pull request, and manual dispatch
- Is already configured to exclude only the original template repository (`franklesniak/copilot-repo-template`)
- Runs `.github/scripts/replace-template-placeholders.py scan`, so the CI audit uses the same placeholder and URL-shape allowlist as the substitution helper

**Adoption considerations:**

1. **If you copied templates with placeholders:** The workflow will catch any unreplaced placeholders and fail CI until you fix them

2. **If you copy this workflow manually:** Also copy `.github/scripts/replace-template-placeholders.py`; the workflow calls that helper for its hard-fail audit.

3. **After all placeholders are replaced:** Treat the workflow as transitional and choose one valid end state:
   - **Keep the workflow** while `OWNER/REPO`, `@OWNER`, `[security contact email]`, or similar template placeholders are still being replaced, or when future template syncs may add placeholder-bearing files
   - **Remove the workflow** once the repository is initialized and placeholders have been replaced with concrete downstream values

If you remove the workflow, also drop or de-emphasize documentation that implies it still exists, do not reintroduce live `OWNER/REPO` placeholders, and prefer concrete downstream repository URLs in issue templates, PR templates, and community-health docs.

**What the workflow checks:**

- Approved `https://github.com/OWNER/REPO...` URL placeholders in `.github/ISSUE_TEMPLATE/config.yml`, `.github/ISSUE_TEMPLATE/bug_report.yml`, `.github/pull_request_template.md`, `CONTRIBUTING.md`, and `SECURITY.md`
- `OWNER/REPO` in the helper's allowlisted non-URL placeholder contexts
- `@OWNER` in `.github/CODEOWNERS`
- `[security contact email]` and `TODO: Replace` in `SECURITY.md`
- `[INSERT CONTACT METHOD]` in `CODE_OF_CONDUCT.md`
- The template `window.title` value in `.vscode/settings.json`
- Common broad-replacement corruption patterns, such as repository names accidentally injected into `REPORT`, `REPOSITORY`, or `REPOSITORIES`

### Python CI Workflow

**Location:** `.github/workflows/python-ci.yml`

**Purpose:** Runs type checking (mypy) and tests (pytest) for Python code. Aggregate pre-commit enforcement (`pre-commit run --all-files`) lives in `.github/workflows/precommit-ci.yml`, not in this workflow.

**Prerequisites:**

- Python code in `src/` directory (or update `MYPY_PATHS`)
- Tests in `tests/` directory
- `pyproject.toml` with `[project.optional-dependencies] dev` section containing test dependencies

**Steps:**

1. Copy `.github/workflows/python-ci.yml` to your `.github/workflows/` directory

2. **Update paths if needed:**

   If your Python code is in a different location, update the `MYPY_PATHS` environment variable:

   ```yaml
   env:
     MYPY_PATHS: "your_package/ tests/"  # Change from "src/ tests/"
   ```

3. **Update pytest path if needed:**

   ```yaml
   run: pytest your_tests_directory/ -v --cov --cov-report=term-missing
   ```

**If you have existing Python CI:**

- Compare your workflow with the template
- Consider adding specific checks from the template as additional jobs
- Repository hygiene (formatting, linting, JSON/YAML validation, etc.) is enforced separately by `.github/workflows/precommit-ci.yml`, which runs the full `pre-commit run --all-files` pipeline. Adopt that workflow alongside Python CI rather than chaining a `needs: pre-commit` dependency inside `python-ci.yml`.

#### If You Already Have pyproject.toml

If your Python project already has a `pyproject.toml` file, you'll need to ensure it includes the required configuration for the CI workflow to pass successfully.

**Required Development Dependencies:**

The CI workflow expects certain development dependencies to be installed. Add these to your `pyproject.toml` if not already present:

| Dependency | Minimum Version | Purpose |
| --- | --- | --- |
| `pytest` | `>=8.0.0` | Running tests in the CI workflow |
| `pytest-cov` | `>=4.0` | Generating test coverage reports |
| `mypy` | `>=1.0` | Type checking Python code |
| `ruff` | `>=0.9.0` | Code linting and formatting (installed automatically by pre-commit, but useful for local development) |

**Adding Development Dependencies:**

Add or merge the `[project.optional-dependencies]` section in your existing `pyproject.toml`:

```toml
[project.optional-dependencies]
dev = [
    # Required for CI workflow:
    "pytest>=8.0.0",
    "pytest-cov>=4.0",
    "mypy>=1.0",
    # Include your existing dev dependencies as well
    # "your-existing-dependency>=1.0.0",
]
```

> **Note:** If you already have a `dev` extras section, merge these dependencies with your existing ones.

**Adding mypy Configuration:**

The CI workflow runs mypy for type checking. Add the `[tool.mypy]` section if not present:

```toml
[tool.mypy]
python_version = "3.13"  # Use the lowest Python line your project supports
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false  # Start permissive, tighten later as you add type hints
```

> **Tip:** Start with `disallow_untyped_defs = false` to avoid errors on untyped functions. You can tighten this requirement as your project matures and you add more type annotations.

**Adding pytest Configuration:**

Add the `[tool.pytest.ini_options]` section to configure test discovery:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]  # Adjust to match your test directory location
python_files = ["test_*.py"]
python_functions = ["test_*"]
```

> **Note:** See [Using the Python Template Files](OPTIONAL_CONFIGURATIONS.md#using-the-python-template-files) for more comprehensive Python configuration options, including Black and Ruff tool settings.

### PowerShell CI Workflow

**Location:** `.github/workflows/powershell-ci.yml`

**Purpose:** Runs PSScriptAnalyzer linting and Pester tests for PowerShell scripts.

**Prerequisites:**

- PowerShell scripts (`.ps1` files)
- Pester tests (`.Tests.ps1` files) for the test job

**Steps:**

1. Copy `.github/workflows/powershell-ci.yml` to your `.github/workflows/` directory

2. Copy `.github/linting/PSScriptAnalyzerSettings.psd1` for consistent linting

3. **Update paths if needed:**

   If your PowerShell files are in different locations, update the find commands in the workflow.

   If your Pester tests aren't in `tests/`, update the configuration:

   ```powershell
   $config.Run.Path = "your_tests_directory/"
   ```

### Data CI Workflow

**Location:** `.github/workflows/data-ci.yml`

**Purpose:** Runs the data-file pre-commit hooks (`check-json`, `check-yaml`, `yamllint`, `actionlint`, and the worked-example `check-jsonschema` and `check-metaschema` hooks) as a dedicated check that can be required via branch protection independent of the Python CI job.

**Prerequisites:**

- `.pre-commit-config.yaml` with the data-file hooks configured
- `.yamllint.yml` at the repository root
- For schema validation: `schemas/<name>.schema.json` plus matching `schemas/examples/<name>/{valid,invalid}/` fixtures

**Steps:**

1. Copy `.github/workflows/data-ci.yml` to your `.github/workflows/` directory.
2. Read the top-of-file comment in `.github/workflows/data-ci.yml` for how it differs from `.github/workflows/auto-fix-precommit.yml` (the auto-fix workflow only runs on `copilot/**` branches and commits fixes; the data CI workflow enforces the hooks on every push and PR without committing).
3. The workflow runs automatically on push and pull requests; no per-file configuration is required as long as the pre-commit hooks themselves are scoped correctly.

**Caveat — `check-jsonschema` and `check-metaschema` steps run unconditionally.** `data-ci.yml` invokes `pre-commit run check-jsonschema --all-files` and `pre-commit run check-metaschema --all-files` as dedicated steps. If you adopt `data-ci.yml` but do **not** keep both hook IDs configured in `.pre-commit-config.yaml`, those steps will fail with `pre-commit: No hook with id ...`. Two safe paths forward:

1. **Keep schema validation:** retain (or repurpose) the `check-jsonschema` and `check-metaschema` hooks in `.pre-commit-config.yaml`, and provide your own schema(s) and example fixture(s) at `schemas/<name>.schema.json` plus `schemas/examples/<name>/{valid,invalid}/`.
2. **Drop schema validation entirely:** remove the `check-jsonschema` and `check-metaschema` steps from `data-ci.yml` (and the corresponding hooks from `.pre-commit-config.yaml`) so the workflow does not invoke missing hook IDs. See [`schemas/README.md`](schemas/README.md) for the canonical removal checklist for the worked example.

`check-json`, `check-yaml`, `yamllint`, and `actionlint` are repository-agnostic and remain useful even without a worked-example schema, so the corresponding `data-ci.yml` steps can be kept regardless of which path above you take.

### Merging with Existing CI

If you already have CI workflows:

1. **Don't blindly overwrite** — Review what your current CI does

2. **Add template checks as additional jobs:**

   ```yaml
   jobs:
     existing-job:
       # Your existing job
       runs-on: ubuntu-latest
       steps: [...]

     # Add this from the template
     pre-commit:
       runs-on: ubuntu-latest
       steps: [...]
   ```

3. **Consider matrix builds** — The template uses matrix builds for cross-platform testing. If not already doing this, consider adopting the pattern:

   ```yaml
   strategy:
     matrix:
       os: [ubuntu-latest, windows-latest, macos-latest]
   ```

---

## Adopting PSScriptAnalyzer Configuration

PSScriptAnalyzer is a static code checker for PowerShell. The template includes a configuration file that enforces OTBS (One True Brace Style) formatting.

### Copying the Configuration

1. Create the directory if it doesn't exist:

   **Windows (PowerShell):**

   ```powershell
   New-Item -ItemType Directory -Path .github\linting -Force
   ```

   **macOS/Linux:**

   ```bash
   mkdir -p .github/linting
   ```

2. Copy `PSScriptAnalyzerSettings.psd1` to `.github/linting/`

### Using the Configuration

**Check PowerShell files:**

```powershell
Invoke-ScriptAnalyzer -Path .\your-script.ps1 -Settings .\.github\linting\PSScriptAnalyzerSettings.psd1
```

**Auto-fix formatting issues:**

```powershell
Invoke-ScriptAnalyzer -Path .\your-script.ps1 -Settings .\.github\linting\PSScriptAnalyzerSettings.psd1 -Fix
```

**Check all PowerShell files in a directory:**

```powershell
Get-ChildItem -Path . -Filter "*.ps1" -Recurse | ForEach-Object {
    Invoke-ScriptAnalyzer -Path $_.FullName -Settings .\.github\linting\PSScriptAnalyzerSettings.psd1
}
```

### Analyzer Debt Triage for Existing Repositories

Existing PowerShell repositories can have pre-existing analyzer findings before this template's PSScriptAnalyzer settings are adopted. Treat the first analyzer run as a debt-discovery step, not as a reason to weaken `.github/linting/PSScriptAnalyzerSettings.psd1`.

Use this workflow when the initial analyzer run reports failures:

1. **Baseline the findings.** Run PSScriptAnalyzer against the adopted PowerShell scope and group findings by rule and file.
2. **Classify each finding.** Assign one accepted decision to every finding group:
   - **Fix now:** Update the script in the adoption branch when the change is low risk, clearly correct, and covered by existing tests or review.
   - **Suppress narrowly with rationale:** Use the smallest suppression scope available, such as the affected command, function, or file. Include a reason that explains why the rule does not apply for that case.
   - **Defer with owner acceptance:** Record the debt in a visible committed note, issue, or narrow code TODO, and identify the accepting owner or review decision. Deferred debt MUST remain visible; do not hide it with broad configuration changes.
3. **Record the triage decision.** Commit a short report with the adoption work or link to an issue that contains the same information.
4. **Re-run validation.** Re-run PSScriptAnalyzer after fixes or suppressions so remaining findings match the recorded deferrals.

Sample triage report:

```markdown
| Rule | File | Count | Decision | Rationale | Follow-up |
| --- | --- | ---: | --- | --- | --- |
| `PSAvoidUsingPositionalParameters` | `scripts/Build.ps1` | 4 | Fix now | Named parameters improve readability and are safe to update in this script. | Included in adoption branch |
| `PSUseApprovedVerbs` | `scripts/LegacyDeploy.ps1` | 1 | Suppress narrowly | The command name is published in an external runbook and will be renamed in a separate change. | Inline suppression with issue link |
| `PSProvideCommentHelp` | `scripts/internal/Migrate.ps1` | 3 | Defer with owner acceptance | Internal migration helpers need usage notes, but the adopting team accepted this as follow-up debt. | Issue #123 or committed TODO |
```

Rule changes to `.github/linting/PSScriptAnalyzerSettings.psd1` SHOULD be rare. Make them only when the repository intentionally changes its PowerShell quality bar, document the reason in the adoption review, and route the change through normal code review. Do not disable or loosen rules merely to make the first adoption run pass.

### Customizing Rules

Review the rules in `PSScriptAnalyzerSettings.psd1` before changing them. Rule edits change the repository's PowerShell quality bar, so prefer fixing findings, using narrow justified suppressions, or recording accepted deferrals before changing the shared settings.

**Key configurable rules:**

| Rule | Default | Purpose |
| --- | --- | --- |
| `PSPlaceOpenBrace` | Same line | OTBS brace placement |
| `PSUseConsistentIndentation` | 4 spaces | Indentation style |
| `PSAvoidUsingPositionalParameters` | Enabled | Enforce named parameters |
| `PSProvideCommentHelp` | Enabled | Require help comments |

**To disable a rule:**

```powershell
PSAvoidUsingPositionalParameters = @{
    Enable = $false
}
```

---

## Validation and Testing

Before considering adoption complete, verify that all configurations work correctly.

### Verify All Configurations Work

**1. Pre-commit (if adopted):**

```bash
pre-commit run --all-files
```

Expected result: All hooks should pass, or you should understand and have addressed any failures.

**2. First-adoption working-tree check (recommended before the first adoption commit):**

Inspect the planned validation surface first:

```bash
python .template-sync/scripts/run_first_adoption_checks.py --plan-only
```

Then run the planned checks:

```bash
python .template-sync/scripts/run_first_adoption_checks.py
```

Expected result: `--plan-only` prints the Git-visible file collection result, explanatory notes, and the deterministic numbered command plan without running validation commands. The normal run prints the same command plan before the first validation command starts, warns that cold pre-commit hook environment bootstrapping may be slow, then validates tracked plus untracked non-ignored regular files. It differs from `pre-commit run --all-files` because it builds its file list from `git ls-files --cached --others --exclude-standard`, then runs `pre-commit run --files ...` against that list so newly copied adoption files are checked before they are committed. Each planned command reports its group label, index, UTC start and end timestamps, elapsed time, and exit status; the run also reports total elapsed time and continues through the full plan so multiple failures are reported together. If the `pre-commit` console script is not on PATH, it uses the equivalent `python -m pre_commit run --files ...` form. When the supporting files are present, it also runs the placeholder scan, marker validation, and Markdown package scripts such as `npm run lint:md` and `npm run lint:md:links`.

**3. Structural consistency checks:**

Before finalizing adoption, confirm that retained modules agree about test roots, workflow roots, and command paths:

- Every retained workflow under `.github/workflows/` invokes paths that exist in the downstream repository or have been intentionally updated to the downstream layout.
- Every retained test command points at the retained test root, such as `tests/`, `tests/PowerShell/`, Terraform test directories, or schema example fixtures.
- Every retained package, pre-commit, schema, markdown, YAML, or Terraform validator points at config files that still exist after stack cleanup.
- Every adopted command shown in README, CONTRIBUTING, runbooks, issue templates, PR templates, or onboarding docs matches the retained workflow and test-root layout.
- Every required structural change from the [Required Structural Alignment Catalog](#required-structural-alignment-catalog) is implemented or remapped in the relevant workflow/tool config. When the downstream path intentionally deviates and template sync support is retained, that deviation is additionally recorded as an intentional `.template-sync/marker.yml` local override.

Expected result: no retained workflow, validator, package script, or user-facing command points at a removed test root, deleted workflow root, or unadopted module path. Record any remaining modernization as post-adoption issue drafts rather than bundling it into adoption.

**4. Template sync marker check (if `.template-sync/marker.yml` is adopted):**

```bash
python .template-sync/scripts/validate_marker.py --require-marker
```

Expected result: The helper reports no retained-template inconsistencies. It validates `.template-sync/marker.yml` and `.template-sync/manifest.yml` against the checked-in schemas, reports leftover files from excluded modules, reports missing concrete files for included modules, and lists deferred protected-file candidates without failing solely because they exist.

**5. Instruction contract check (if template sync support and agent instruction files are adopted):**

```bash
python .template-sync/scripts/validate_instruction_contracts.py --mode downstream --require-marker
```

Expected result: The helper checks required headings and phrases only for contracts whose `requires_modules` are retained by `.template-sync/marker.yml`. Missing anchors fail with the exact file and anchor unless a visible `template_sync.instruction_contract_waivers` entry applies, and absent protected files are skipped only when `.template-sync/marker.yml` records an authorized `REMOVE-LOCAL` decision for that path.

**6. Template sync candidate table (when performing a future sync):**

After fetching the template remote and resolving the upstream range head, use the generator to create the first-pass Markdown decision aid:

```bash
python .template-sync/scripts/generate_sync_candidates.py --range-head RANGE_HEAD_SHA
```

For a first-sync delta review where `.template-sync/marker.yml` does not yet set `template_sync.last_reviewed_template_commit`, pass the owner-approved base explicitly:

```bash
python .template-sync/scripts/generate_sync_candidates.py --range-base RANGE_BASE_SHA --range-head RANGE_HEAD_SHA
```

Expected result: The helper validates `.template-sync/marker.yml` and `.template-sync/manifest.yml`, evaluates `RANGE_BASE_SHA..RANGE_HEAD_SHA`, and prints a Markdown table that flags retained/excluded paths, local overrides, deferred protected candidates, protected instruction/governance files, unmapped paths, unknown modules, cross-module mappings, inline-block notes, and renames. It is read-only and does not replace the manual review process in [TEMPLATE_UPDATE_PROCEDURE.md](TEMPLATE_UPDATE_PROCEDURE.md).

**7. Markdown linting (if adopted):**

```bash
npm run lint:md
```

Expected result: No errors, or only warnings you've chosen to accept.

**8. Push to feature branch:**

```bash
git add .
git commit -m "feat: adopt template configurations from copilot-repo-template"
git push origin feature/adopt-template-features
```

**9. Verify CI workflows:**

- Navigate to your repository's **Actions** tab
- Check that all adopted workflows run
- Fix any failures before merging

**10. Test issue templates (if adopted):**

- Navigate to **Issues** → **New Issue**
- Verify all templates appear correctly
- Open a test issue with each template to verify form fields work
- Verify links in the template chooser (`config.yml`) work
- Close test issues without saving (or delete after testing)

**11. Test PR template (if adopted):**

- Open a test pull request (can be against your feature branch)
- Verify the template renders correctly with all sections
- Close without merging

### Troubleshooting Common Issues

| Issue | Cause | Solution |
| --- | --- | --- |
| Workflow fails with "file not found" | Different project structure | Update paths in workflow file |
| Pre-commit downloads every time | Environment cache issue | Run `pre-commit clean && pre-commit install` |
| Markdown lint finds many errors | Stricter rules than before | Adjust `.markdownlint.jsonc` or fix files |
| Python CI fails on imports | Different package structure | Update `MYPY_PATHS` in workflow |
| PSScriptAnalyzer fails | Code does not match the adopted analyzer rules | Run with `-Fix`, apply the analyzer debt triage workflow, or add narrow justified suppressions |
| npm install fails | Node.js version mismatch | Update Node.js to v20+ (see `engines` in package.json) |
| Placeholder check fails | OWNER/REPO not replaced | Search and replace all placeholders |

---

## Cleanup and Documentation

### Files to Review After Adoption

**Files you may want to delete after adoption:**

- If you cloned the template separately, delete the clone directory
- `templates/` directory — Only useful if your project is also a template

**Files you should keep:**

- All configuration files you adopted (`.markdownlint.jsonc`, `.pre-commit-config.yaml`, etc.)
- All workflow files in `.github/workflows/`
- Copilot instructions (`.github/copilot-instructions.md` and `.github/instructions/`)
- `.github/TEMPLATE_DESIGN_DECISIONS.md` — Template design rationale (useful during setup to understand why configurations were made; can be deleted after review if not needed)

### Updating Your Project Documentation

**Update CONTRIBUTING.md:**

If you adopted the template's `CONTRIBUTING.md`, you should:

1. **Remove the "For Template Users" section** — This section (starting with `## For Template Users`) contains meta-instructions about the template itself. Delete it along with the HTML comment above it for non-template projects.

2. **Replace `OWNER/REPO` placeholders** — Update with your actual organization and repository name in clone instructions and issue links.

3. **Add pre-commit setup instructions** (if you adopted pre-commit):

````markdown
## Development Setup

Before making changes, install pre-commit hooks:

**Option 1: Using pipx (recommended)**

Windows (PowerShell):

```powershell
python -m pip install pipx
python -m pipx ensurepath
python -m pipx install pre-commit
```

After running the above, restart your terminal, then run:

```powershell
pre-commit install
```

macOS/Linux/FreeBSD:

```bash
python3 -m pip install pipx
# Or use your OS package manager: sudo apt install pipx, brew install pipx, etc.
python3 -m pipx ensurepath
python3 -m pipx install pre-commit
```

After running the above, restart your terminal, then run:

```bash
pre-commit install
```

**Option 2: Using pip (if you can't use pipx)**

Windows (PowerShell):

```powershell
python -m pip install pre-commit
# Use module invocation (avoids PATH issues):
python -m pre_commit install
```

macOS/Linux/FreeBSD:

```bash
python3 -m pip install pre-commit
# Use module invocation (avoids PATH issues):
python3 -m pre_commit install
```

Pre-commit hooks will automatically run on each commit. You can also run them manually:

**Windows (PowerShell):**

```powershell
pre-commit run --all-files
```

Or if `pre-commit` is not on PATH:

```powershell
python -m pre_commit run --all-files
```

**macOS/Linux/FreeBSD:**

```bash
pre-commit run --all-files
```

Or if `pre-commit` is not on PATH:

```bash
python3 -m pre_commit run --all-files
```
````

See [OPTIONAL_CONFIGURATIONS.md](OPTIONAL_CONFIGURATIONS.md) for additional `CONTRIBUTING.md` customization guidance.

**Update README.md:**

> **Note:** Do NOT copy the template's `README.md` to your existing repository. The template's README is designed for new repositories created from the template and contains template-specific documentation that would not apply to your repository. Your existing README should remain intact.

Instead, update your existing README to document any new development requirements you've adopted:

````markdown
## Development

### Prerequisites

- Node.js 20+ (for markdown linting)
- Python 3.13 or 3.14 (for pre-commit hooks)
- PowerShell (for PSScriptAnalyzer)

### Setup

Install markdown linting tools:

```bash
npm install
```

Install pre-commit hooks:

**Option 1: Using pipx (recommended)**

Windows (PowerShell):

```powershell
python -m pip install pipx
python -m pipx ensurepath
python -m pipx install pre-commit
```

After running the above, restart your terminal, then run:

```powershell
pre-commit install
```

macOS/Linux/FreeBSD:

```bash
python3 -m pip install pipx
# Or use your OS package manager: sudo apt install pipx, brew install pipx, etc.
python3 -m pipx ensurepath
python3 -m pipx install pre-commit
```

After running the above, restart your terminal, then run:

```bash
pre-commit install
```

**Option 2: Using pip (if you can't use pipx)**

Windows (PowerShell):

```powershell
python -m pip install pre-commit
# Use module invocation (avoids PATH issues):
python -m pre_commit install
```

macOS/Linux/FreeBSD:

```bash
python3 -m pip install pre-commit
# Use module invocation (avoids PATH issues):
python3 -m pre_commit install
```
````

Consider adding sections for:

- Pre-commit hook requirements (if adopted)
- Linting commands (e.g., `npm run lint:md`)
- CI workflow expectations

**Notify your team:**

Consider informing collaborators about:

- New pre-commit requirements
- CI workflow changes
- New issue/PR templates

---

## Migration Notes for Existing Terraform Repos

If you are adopting this template into an existing Terraform repository, follow this step-by-step checklist to ensure a smooth migration:

### Tooling Prerequisites

Install both HashiCorp Terraform (`terraform`) and TFLint (`tflint`) before running the template's local Terraform hooks. The hooks are repo-local Python wrappers, so native Windows PowerShell, Git Bash, WSL/Linux, and macOS all use the same implementation and do not require POSIX shell hook scripts.

**Windows PowerShell:**

- Terraform: download the Windows binary from [HashiCorp's Terraform install guide](https://developer.hashicorp.com/terraform/install), place `terraform.exe` in a stable tools directory, and add that directory to PATH. If your organization uses Chocolatey, `choco install terraform` is also supported.
- TFLint: download the Windows binary from the [TFLint installation guide](https://github.com/terraform-linters/tflint#installation), place `tflint.exe` in a stable tools directory, and add that directory to PATH. If your organization uses Chocolatey, `choco install tflint` is also supported.
- Restart PowerShell and verify with `terraform version` and `tflint --version`.

**macOS:**

```bash
brew tap hashicorp/tap
brew install hashicorp/tap/terraform
brew install tflint
```

**Linux, FreeBSD, and WSL:**

- Install Terraform using the package or binary instructions for your distribution in [HashiCorp's Terraform install guide](https://developer.hashicorp.com/terraform/install).
- Install TFLint using the Linux install script or release binary from the [TFLint installation guide](https://github.com/terraform-linters/tflint#installation).

### Pre-Migration Checklist

- [ ] **Baseline current state:** Run `terraform plan` and save the output. This gives you a baseline to verify no unintended changes occur after migration.
- [ ] **Commit any pending changes:** Ensure your working tree is clean before starting migration.

### Alignment Checklist

- [ ] **Align `versions.tf`:** Ensure your `versions.tf` follows the template's format with explicit `required_version` and `required_providers` blocks:

  ```hcl
  terraform {
    required_version = ">= 1.6.0"

    required_providers {
      aws = {
        source  = "hashicorp/aws"
        version = "~> 5.0"
      }
    }
  }
  ```

- [ ] **Update `.terraform.lock.hcl`:** Regenerate your lock file to include hashes for all platforms used in CI:

  ```bash
  terraform providers lock \
    -platform=linux_amd64 \
    -platform=darwin_amd64 \
    -platform=darwin_arm64
  ```

- [ ] **Commit `.terraform.lock.hcl`:** Ensure the lock file is tracked in version control.

### Formatting and Validation Checklist

- [ ] **Run `terraform fmt -recursive`:** Format all Terraform files to match the template's style.
- [ ] **Run `terraform validate`:** Ensure all configurations are syntactically valid.
- [ ] **Run `tflint`:** Use the template's `.tflint.hcl` configuration to lint your code:

  ```bash
  tflint --init
  tflint --recursive --config "$(pwd)/.tflint.hcl"
  ```

- [ ] **Fix any issues:** Address formatting, validation, and linting errors before proceeding.

### Local Pre-commit Terraform Hooks

After copying `.pre-commit-config.yaml` and `.github/scripts/terraform_hooks.py`, verify the repo-local Terraform hooks:

**Windows PowerShell:**

```powershell
python -m pre_commit run terraform-fmt --all-files
python -m pre_commit run terraform-validate --all-files
python -m pre_commit run terraform-tflint --all-files
```

**Git Bash, WSL/Linux, macOS, and other POSIX-style shells:**

```bash
pre-commit run terraform-fmt --all-files
pre-commit run terraform-validate --all-files
pre-commit run terraform-tflint --all-files
```

These hooks mirror Terraform CI: format checks run from the repository root, validation runs only in directories containing `.tf` or `.tf.json` files, and TFLint receives an absolute path to the repository-root `.tflint.hcl` file.

### Refactoring Checklist

If you need to rename resources or restructure your configuration:

- [ ] **Use `moved` blocks for renames:** Instead of manual state manipulation, use declarative `moved` blocks:

  ```hcl
  moved {
    from = aws_instance.old_name
    to   = aws_instance.new_name
  }
  ```

- [ ] **Use `import` blocks for existing resources:** Bring unmanaged resources into Terraform using `import` blocks (Terraform 1.5+):

  ```hcl
  import {
    to = aws_instance.example
    id = "i-1234567890abcdef0"
  }
  ```

- [ ] **Use `removed` blocks when appropriate:** Remove resources from state without destroying them using `removed` blocks (Terraform 1.7+):

  ```hcl
  removed {
    from = aws_instance.legacy_server

    lifecycle {
      destroy = false  # Remove from state without destroying
    }
  }
  ```

### Documentation Checklist

- [ ] **Document deviations:** If your repository deviates from the template's Terraform standards, document these in the **Scope Exceptions & Deviations from Standards** section of `.github/instructions/terraform.instructions.md`.
- [ ] **Update README:** Document any Terraform-specific setup requirements for your repository.

### Post-Migration Verification

- [ ] **Run `terraform plan`:** Compare against your pre-migration baseline. There should be no unexpected changes.
- [ ] **Run CI workflows:** Verify all GitHub Actions workflows pass.
- [ ] **Test in a non-production environment:** If possible, apply changes to a test environment before production.

---

## Next Steps

After adopting template features, you may want to explore additional customization options:

- **[Optional Configurations](OPTIONAL_CONFIGURATIONS.md)**: Fine-tune your repository with optional settings like enabling GitHub Discussions, adjusting Dependabot frequency, customizing linting rules, and more.

---

## Summary Checklist

Before considering adoption complete, verify:

### Files

- [ ] All copied files have placeholders replaced (OWNER/REPO, @OWNER, `window.title` in `.vscode/settings.json`, etc.)
- [ ] Conflicting configurations have been merged, not overwritten
- [ ] Unused language files have been removed (e.g., PowerShell instructions if not using PowerShell)
- [ ] `.github/TEMPLATE_DESIGN_DECISIONS.md` reviewed (keep for reference or delete after review)
- [ ] Structural convention findings classified as required, strongly recommended, post-adoption follow-up, or intentionally not recommended
- [ ] Required structural changes implemented or remapped, with intentional `.template-sync/marker.yml` local overrides recorded in addition for deliberate downstream deviations

### Functionality

- [ ] Pre-commit runs successfully (`pre-commit run --all-files`)
- [ ] First-adoption working-tree validation passes (`python .template-sync/scripts/run_first_adoption_checks.py`) before the first adoption commit, so untracked non-ignored files are checked
- [ ] Retained test roots, workflow roots, package scripts, and validator config paths are consistent with the adopted structure
- [ ] Template sync marker validation passes (`python .template-sync/scripts/validate_marker.py --require-marker`) if `.template-sync/marker.yml` is adopted
- [ ] Template sync candidate generation is available for future syncs (`python .template-sync/scripts/generate_sync_candidates.py --range-head RANGE_HEAD_SHA`) after fetching and choosing a reviewed range
- [ ] Markdown linting passes (`npm run lint:md`)
- [ ] All CI workflows pass in GitHub Actions
- [ ] Issue templates display correctly in GitHub
- [ ] PR template renders correctly when opening a PR
- [ ] PSScriptAnalyzer runs without unexpected errors (if using PowerShell)

### Documentation

- [ ] CONTRIBUTING.md updated with new development requirements
- [ ] README.md updated if setup steps changed
- [ ] Post-adoption follow-up issues drafted for deferred modernization and cleanup
- [ ] Team notified of new tooling/workflows

---

**Commit all your changes:**

```bash
git add .
git commit -m "feat: adopt template configurations from copilot-repo-template"
git push origin feature/adopt-template-features
```

**Create a pull request:**

1. Navigate to your repository on GitHub
2. Click **Compare & pull request**
3. Review the changes
4. Merge after CI passes

Congratulations! You've successfully adopted features from the copilot-repo-template into your existing repository.
