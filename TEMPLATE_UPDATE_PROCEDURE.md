<!-- markdownlint-disable MD013 -->
# Downstream Template Update Procedure

**Version:** 1.0.20260513.3

## Metadata

- **Status:** Active
- **Owner:** Repository Maintainers
- **Last Updated:** 2026-05-13
- **Scope:** Defines the selective review procedure for downstream repositories that were created from, or adopted files from, this template repository. Covers manual and agent-assisted syncs from later upstream template changes. Does not define automation contracts for a future manifest or sync tool.
- **Related:** [Optional Configurations](OPTIONAL_CONFIGURATIONS.md), [Getting Started for New Repositories](GETTING_STARTED_NEW_REPO.md), [Getting Started for Existing Repositories](GETTING_STARTED_EXISTING_REPO.md), [Repository Copilot Instructions](.github/copilot-instructions.md)

## Purpose

Downstream template updates are a selective review process, not a raw merge. A downstream repository may have removed optional modules, customized project identity, changed workflows, or retained only part of the language/tooling guidance from this template. The goal of this procedure is to review later upstream template changes deterministically, adopt only relevant improvements, and preserve downstream ownership decisions.

Use this procedure when a downstream repository wants to review new changes from `franklesniak/copilot-repo-template` after initial adoption. The procedure is suitable for a repository owner or for a coding agent operating under owner direction.

## Terminology

- **Module:** A unit in the taxonomy defined by this procedure, such as `markdown`, `powershell`, or `terraform`. Procedure logic operates on modules.
- **Stack:** Informal shorthand for a related grouping of modules. For example, a "PowerShell stack" may mean `powershell`, `markdown`, `yaml`, and `agent-instructions`, depending on what the downstream repository adopted. Stack is acceptable in prose, but sync decisions MUST be recorded in module terms.
- **Downstream sync marker:** The `.template-sync.yml` file at the downstream repository root. Under `template_sync`, it records the upstream template repository, the newest upstream template commit that has been reviewed, the modules the downstream repository has adopted, local override rules, and deferred protected-file candidates.
- **Reviewed range:** The upstream template commit range being inspected for one sync. The range base is `template_sync.last_reviewed_template_commit` from the downstream sync marker when the marker exists and that field is present and non-empty, or an owner-chosen first-time seed when the marker is absent or when the marker exists but that field is missing or empty. The range head is `template/main` unless the owner explicitly chooses a different upstream branch or tag.
- **Included module:** A module listed in the downstream sync marker under `template_sync.included_modules`.
- **Unadopted-module activity:** Upstream activity in a known taxonomy module that is not listed in `included_modules`.
- **Unknown module:** A module name introduced by a newer upstream procedure or future manifest that the downstream marker does not recognize. Unknown modules MUST be surfaced for explicit owner decision.
- **Protected file:** A governance or instruction file that requires explicit owner authorization before editing.
- **Sync working notes:** Temporary notes maintained while applying this procedure. They MAY be a scratch document, a draft PR body, or another local checklist, but they are not the final sync PR summary. They MUST capture range endpoints, owner-chosen seeds, unmapped paths, per-file decisions, protected-file dispositions, validation results, and open questions as those facts are discovered. Step 14 turns these working notes into the final sync PR summary.
- **Sync PR summary:** The final owner-facing PR description created in Step 14 from the sync working notes. It is the durable review artifact for the sync PR.

## Safety Rules

- Do not run `git pull template main`, `git merge template/main`, or `git rebase template/main` as the update mechanism. Fetch first, inspect the range, and make explicit per-file decisions.
- Do not overwrite downstream project identity, repository URLs, issue templates, PR templates, workflow runner choices, validation commands, README content, package metadata, or local policy without a recorded decision.
- Do not edit protected files unless the owner gives explicit, path-scoped authorization in the current task.
- Do not weaken existing security, validation, or pre-commit expectations to make a sync easier.
- Do not silently include or exclude unknown modules.

## Procedure Overview

1. Create a dedicated sync branch.
2. Add this template repository as a `template` remote if it is not already present.
3. Fetch upstream template changes without merging.
4. Identify the upstream commit range under review with rename detection.
5. Initialize or update `.template-sync.yml`.
6. Filter upstream changes through the authoritative module taxonomy.
7. Review every candidate file with an explicit decision.
8. Perform manual merges using an ignored scratch location when needed.
9. Handle protected files through authorization or deferral.
10. Preserve local customizations and downstream project identity.
11. Re-substitute template placeholders such as `OWNER/REPO`.
12. Run validation for the adopted modules.
13. Record the latest reviewed template commit.
14. Open a PR with a clear sync summary.

Independent substeps, such as inspecting unrelated candidate files or collecting validation commands for separate modules, MAY be performed in parallel. The final recorded decisions and marker update MUST remain deterministic.

## Step 1: Create a Sync Branch

Start from the downstream repository's normal integration branch, then create a branch dedicated to the sync.

```bash
git checkout main
git pull --ff-only origin main
git checkout -b template-sync/YYYYMMDD
```

Use the downstream repository's actual default branch name if it is not `main`.

## Step 2: Add the Template Remote

Add this template repository as a remote named `template` if it is not already configured.

```bash
git remote add template https://github.com/franklesniak/copilot-repo-template.git
```

If the remote already exists, verify it points to the template repository.

```bash
git remote get-url template
```

## Step 3: Fetch Without Merging

Fetch upstream template refs without changing the working tree.

```bash
git fetch template
```

Do not merge, rebase, or pull from `template/main` at this step.

## Step 4: Identify the Reviewed Range

Read `.template-sync.yml` at the downstream repository root before calculating the reviewed range. When the marker exists, use `template_sync.last_reviewed_template_commit` as the range base. Use `template/main` as the range head unless the owner explicitly chooses a different upstream branch or tag.

For first-time syncs where `.template-sync.yml` does not exist yet, choose the range base before running the diff. If the marker exists but `template_sync.last_reviewed_template_commit` is missing or empty, treat the range base as unset and use the same owner-chosen seed process.

- Use the upstream template commit the downstream repository was originally created from when known.
- If the original commit is unknown, ask the owner to choose a reasonable proxy, such as a tagged template release before the downstream repository's first commit or another owner-approved commit chosen after inspecting repository history.
- Record the chosen seed and rationale in the sync working notes, then initialize the marker in Step 5 and include the rationale in the final sync PR summary.

```bash
git diff --name-status -M RANGE_BASE..template/main
```

The `-M` flag is required so upstream renames appear as renames, such as `R100 old/path new/path`, instead of unrelated add/delete pairs.

Record both endpoints in the sync working notes:

- **Range base:** `template_sync.last_reviewed_template_commit` from `.template-sync.yml` when the marker exists and that field is present and non-empty, or the owner-chosen first-time seed when the marker is absent or when that field is missing or empty.
- **Range head:** the current `template/main` commit SHA

Get the range head explicitly:

```bash
git rev-parse template/main
```

If the range base is no longer reachable from `template/main`, stop and ask the owner to choose a new seed. Reasonable re-seed choices include the original template adoption commit, a tagged template release that predates the downstream repository's first commit, or an owner-approved commit chosen after inspecting repository history. Do not silently reset the marker to `template/main`.

## Step 5: Initialize or Update the Sync Marker

Downstream repositories SHOULD keep a `.template-sync.yml` marker at the repository root. The marker distinguishes reviewed upstream changes from adopted upstream changes. Selective syncs may intentionally skip upstream files, so the preferred field is `last_reviewed_template_commit`, not `last_adopted_template_commit`.

If Step 4 used a first-time seed because the marker was missing or incomplete, initialize `.template-sync.yml` in this step. Set `last_reviewed_template_commit` to the Step 4 range base until Step 13 advances it to the reviewed range head. Carry the seed rationale from the sync working notes into the final sync PR summary.

Example marker:

```yaml
template_sync:
  source_repo: https://github.com/franklesniak/copilot-repo-template.git
  last_reviewed_template_commit: abc1234
  included_modules:
    - baseline
    - agent-instructions
    - github-templates
    - markdown
    - powershell
    - json
    - yaml
  local_overrides:
    - path: README.md
      reason: "Project-specific; use template only as reference."
      default_decision: SKIP
    - path: .github/ISSUE_TEMPLATE/config.yml
      reason: "Repository-specific contact links."
      default_decision: MERGE
  deferred_protected_candidates:
    - path: .github/copilot-instructions.md
      source_commit: def5678
      reason: "Adds a stack-selection clause; pending owner authorization."
```

### Marker Semantics

- `source_repo` is the upstream template repository under review.
- `last_reviewed_template_commit` is the newest upstream commit whose changes were reviewed, regardless of how many were adopted.
- `included_modules` is the adoption state. Anything not listed is not adopted.
- `local_overrides` changes the starting recommendation for a path, but it MUST NOT hide upstream activity from the sync.
- `deferred_protected_candidates` records protected-file updates that were reviewed but not applied because path-scoped owner authorization was absent.

### Local Overrides

When a changed upstream path appears in `local_overrides` and at least one of its mapped modules is in `included_modules`, start the per-file decision at the override's `default_decision`. Each applied override MUST still appear in the sync PR summary with a brief description of the upstream change.

The agent or maintainer does not decide that an upstream change is too minor to mention under an override. Listing every applied override is the mechanism that lets the owner notice stale overrides, security-sensitive changes, validation changes, or governance changes that should override the override.

### Deferred Protected Candidates

Protected-file candidates remain in `deferred_protected_candidates` until the owner applies them through an authorized PR or explicitly dismisses them. Each entry includes:

- `path`
- `source_commit`
- `reason`

If the same protected path changes again upstream before the candidate is resolved, update the existing entry to the latest relevant source commit and preserve the prior rationale. Add a short refresh note to `reason` when the newer upstream change materially changes what is deferred. Add a separate entry only when the same path has distinct deferred candidates that cannot be represented clearly by one entry.

## Step 6: Use the Authoritative Module Taxonomy

The table in this section is authoritative for this manual procedure. If future automation moves the mapping into a machine-readable manifest, the manifest should preserve these semantics unless a later procedure explicitly changes them.

### Module Definitions

| Module | Scope |
| --- | --- |
| `baseline` | Core repository scaffolding, community files, starter identity files, template maintenance docs, and repository-level configuration not owned by a narrower module. |
| `agent-instructions` | Agent entry points, Copilot instructions, Cursor rules, reusable prompt guidance, and modular instruction docs. |
| `github-templates` | GitHub issue templates, PR templates, CODEOWNERS, and GitHub-facing community workflow surfaces. |
| `markdown` | Markdown linting, Markdown templates, docs guidance, and Markdown-only documentation assets. |
| `powershell` | PowerShell scripts, Pester tests, PSScriptAnalyzer configuration, and PowerShell CI. |
| `json` | JSON and JSONC guidance, examples, validation commands, and JSON-oriented template files. |
| `yaml` | YAML guidance, YAML template files, YAML validation, and GitHub Actions syntax guidance not owned by a narrower workflow module. |
| `schema` | JSON Schema contracts, schema examples, schema validation docs, and schema-specific tests. |
| `python` | Python package scaffolding, Python tests, Python CI, and Python tooling configuration. |
| `terraform` | Terraform modules, tests, linting, documentation, workflows, and template files. |

### Path Mapping

Apply the most specific matching row. If multiple rows match, use the union of their modules. A path mapped to multiple modules is included in the review set if any mapped module appears in `included_modules`.

| Path pattern | Module(s) |
| --- | --- |
| `.template-sync.yml` | `baseline` |
| `.github/copilot-instructions.md` | `agent-instructions` |
| `.github/instructions/docs.instructions.md` | `markdown`, `agent-instructions` |
| `.github/instructions/gitattributes.instructions.md` | `baseline`, `agent-instructions` |
| `.github/instructions/json.instructions.md` | `json`, `agent-instructions` |
| `.github/instructions/powershell.instructions.md` | `powershell`, `agent-instructions` |
| `.github/instructions/python.instructions.md` | `python`, `agent-instructions` |
| `.github/instructions/terraform.instructions.md` | `terraform`, `agent-instructions` |
| `.github/instructions/yaml.instructions.md` | `yaml`, `agent-instructions` |
| `.github/instructions/*.instructions.md` not otherwise listed | `agent-instructions`; surface for owner to confirm or add additional module mappings |
| `.cursor/rules/**` | `agent-instructions` |
| `.hermes.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` | `agent-instructions` |
| `COPILOT_CHAT_PROMPTS.md`, `docs/PR_REVIEW_PROMPTS.md` | `agent-instructions`, `markdown` |
| `.codex/**` | `agent-instructions` |
| `.github/ISSUE_TEMPLATE/**` | `github-templates`, `yaml` |
| `.github/pull_request_template.md` | `github-templates`, `markdown` |
| `.github/CODEOWNERS` | `github-templates` |
| `.github/workflows/markdownlint.yml` | `markdown`, `yaml` |
| `.github/workflows/powershell-ci.yml` | `powershell`, `yaml` |
| `.github/workflows/python-ci.yml` | `python`, `yaml` |
| `.github/workflows/terraform-ci.yml` | `terraform`, `yaml` |
| `.github/workflows/data-ci.yml` | `json`, `yaml`, `schema` |
| `.github/workflows/check-placeholders.yml` | `baseline`, `github-templates`, `markdown`, `yaml` |
| `.github/workflows/auto-fix-precommit.yml` | `baseline`, `yaml` |
| `.github/dependabot.yml`, `.yamllint.yml` | `yaml` |
| `.pre-commit-config.yaml` | `baseline`, `markdown`, `json`, `yaml`, `schema`, `python`, `terraform` |
| `.markdownlint.jsonc`, `package.json`, `package-lock.json` | `markdown`, `json` |
| `templates/markdown/**` | `markdown` |
| `templates/powershell/**`, `tests/PowerShell/**`, `.github/linting/PSScriptAnalyzerSettings.psd1`, `src/tools/*.ps1` | `powershell` |
| `templates/json/**` | `json` |
| `templates/yaml/**` | `yaml` |
| `schemas/**`, `tests/test_schema_examples.py` | `schema`, `json`, `python` |
| `templates/python/**`, `pyproject.toml`, `tests/**/*.py` | `python` |
| `templates/terraform/**`, `docs/terraform/**`, `modules/**`, `tests/**/*.tftest.hcl`, `.tflint.hcl`, `*.tf`, `*.tfvars`, `*.tftpl`, `*.tfbackend` | `terraform` |
| `README.md`, `GETTING_STARTED_NEW_REPO.md`, `GETTING_STARTED_EXISTING_REPO.md`, `OPTIONAL_CONFIGURATIONS.md`, `TEMPLATE_MAINTENANCE.md`, `TEMPLATE_UPDATE_PROCEDURE.md` | `baseline`, `markdown` |
| `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `LICENSE` | `baseline`, `markdown` |
| `.gitignore`, `.gitattributes`, `.editorconfig`, `.vscode/**` | `baseline` |

If a changed upstream path does not match the table, classify it as `UNMAPPED` in the sync working notes and ask the owner to assign a module before deciding whether to include it.

### Filtering Rules

For each path from `git diff --name-status -M`:

1. Map the path to module(s).
2. Include the path in the per-file review table if any mapped module is present in `included_modules`.
3. Exclude the path from the per-file review table if all mapped modules are known taxonomy modules absent from `included_modules`.
4. Summarize excluded paths as unadopted-module activity by module in the PR summary.
5. Surface unknown modules and unmapped paths for explicit owner review before completing the sync.

Unadopted-module activity and unknown modules are different cases:

- **Unadopted-module activity** uses known modules from this taxonomy, such as `terraform`, that the downstream marker intentionally omits. Summarize it by module and path count or path list.
- **Unknown modules** are not known to the downstream marker or procedure. The owner MUST decide whether the module should be added to `included_modules`, mapped to an existing module, or deferred.

If summarized unadopted-module activity appears relevant during review, the owner MAY opt into that module before completing the sync by adding it to `included_modules`, or MAY defer opt-in to a later PR. Record either choice in the sync PR summary.

## Step 7: Review Each Candidate File

Every included candidate requires a row in a per-file decision table.

| Decision | Meaning |
| --- | --- |
| `TAKE` | Adopt the upstream version as-is. |
| `MERGE` | Manually merge relevant upstream changes with local customizations. |
| `SKIP` | Do not adopt because the change is irrelevant, not adopted, or locally superseded. |
| `REMOVE-LOCAL` | Remove a downstream file because the module or feature is intentionally excluded. |
| `DEFER` | Leave unresolved pending owner decision. |
| `PROTECTED-REVIEW` | Protected-file change requiring explicit owner authorization before it can be applied. |

Suggested table:

```markdown
| Path | Module(s) | Template Change | Local Customization | Decision | Notes |
| --- | --- | --- | --- | --- | --- |
| `.github/instructions/docs.instructions.md` | `markdown`, `agent-instructions` | Updated style rules | None | `PROTECTED-REVIEW` | Requires owner authorization. |
| `.github/workflows/powershell-ci.yml` | `powershell`, `yaml` | Updated validation steps | Local runner change | `MERGE` | Preserve local runner. |
| `.github/workflows/terraform-ci.yml` | `terraform`, `yaml` | Updated TFLint setup | Repo excludes Terraform | `SKIP` | Summarize as unadopted-module activity. |
```

Upstream deletions MUST be surfaced for owner decision rather than applied automatically. Valid decisions for deletion rows include `TAKE` when the downstream owner agrees to delete the local file, `SKIP` when the downstream file is intentionally retained, and `MERGE` when only part of the deletion rationale applies.

Upstream renames MUST preserve both old and new paths in the table. If the rename is adopted, apply it as a rename locally rather than recreating the file without history where practical.

## Step 8: Perform Manual Merges

Use `MERGE` when the downstream file contains local customizations that should survive. A merge MUST inspect both the upstream candidate and the local file.

### Scratch Location

This template ignores `.cache/` in `.gitignore`, so `.cache/template-sync/` is the preferred scratch location when the downstream repository still has that ignore rule.

Verify the location is ignored:

```bash
git check-ignore .cache/template-sync/
```

If the command does not report the path as ignored, either add an equivalent downstream-specific ignore rule before using the location or choose another already ignored scratch location. Do not commit scratch copies.

Create the scratch directory:

```bash
mkdir -p .cache/template-sync
```

PowerShell equivalent:

```powershell
New-Item -ItemType Directory -Force -Path .cache/template-sync
```

### Inspect Upstream Content

Inspect an upstream file directly:

```bash
git show TEMPLATE_SHA:.github/workflows/powershell-ci.yml
```

Or restore an upstream copy into scratch for side-by-side reconciliation:

```bash
git show TEMPLATE_SHA:.github/workflows/powershell-ci.yml > .cache/template-sync/powershell-ci.upstream.yml
```

Then manually reconcile the scratch copy with the downstream file. Preserve local customizations unless the per-file decision explicitly replaces them.

## Step 9: Handle Protected Files

Protected governance and instruction files require explicit owner authorization before editing.

Protected files include:

- `.github/copilot-instructions.md`
- `.github/instructions/*.instructions.md`
- `.cursor/rules/*`
- `.hermes.md`
- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`

The default decision for protected-file changes is `PROTECTED-REVIEW`.

### Same-PR Protected Edits

Protected-file changes MAY be included in the same sync PR only when the owner gives explicit, current-task authorization for the specific protected path or paths being changed.

The sync PR summary MUST record the authorization basis in a reviewer-verifiable form, such as:

- a linked owner comment
- a linked authorization issue
- a quoted owner instruction from the current task

The PR summary MUST list each protected path, the authorization basis, and the validation performed.

Protected-file edits MUST be placed in a separate commit from non-protected changes unless the owner's current-task authorization explicitly waives commit isolation. If commit isolation is waived, record the waiver and authorization basis in the PR summary.

### Deferred Protected Edits

If authorization is absent, leave the protected file unchanged and record the candidate in `.template-sync.yml` under `deferred_protected_candidates`.

Example:

```yaml
template_sync:
  deferred_protected_candidates:
    - path: .github/copilot-instructions.md
      source_commit: 2222bbb
      reason: "Updates stack-selection guidance; awaiting owner authorization."
```

Leave the PR thread or sync question open when the owner still needs to act on the protected-file candidate.

## Step 10: Preserve Local Identity

Before taking or merging a file, check whether it contains local project identity or downstream policy. Examples include:

- repository owner/name
- package names
- workflow runner labels
- branch names
- support or security contact details
- issue labels, projects, assignees, and issue types
- PR checklist items
- README product description
- license policy
- validation commands that reflect adopted modules

Use `MERGE`, not `TAKE`, when upstream content is useful but the downstream identity must remain.

## Step 11: Re-Substitute Template Placeholders

After applying upstream content, search for unresolved template placeholders and replace them with downstream values or remove the placeholder-bearing content.

```bash
git grep "OWNER/REPO"
```

Common placeholder shapes include:

- `OWNER/REPO`
- `https://github.com/OWNER/REPO`
- `https://github.com/OWNER/REPO.git`
- `https://github.com/OWNER/REPO/blob/HEAD/PATH`

References to the upstream template repository itself (for example, `franklesniak/copilot-repo-template` in `.template-sync.yml` under `source_repo`, in the Step 2 `git remote add template` example, or in adopted documentation that intentionally links to the upstream template) are not template placeholders and are out of scope for Step 11. Review and decide on those references under Step 10 (Preserve Local Identity) so that legitimate retentions are not rewritten and any deliberate rebranding remains an explicit decision.

Do not replace didactic examples that intentionally explain the placeholder convention unless the downstream repository has removed the associated placeholder-check workflow and no longer wants the convention documented.

## Step 12: Validate by Adopted Module

Run validation appropriate to the included modules and files changed. Full template-like validation remains the safest default when the downstream repository keeps the relevant tooling.

| Module | Example validation |
| --- | --- |
| `baseline` | `pre-commit run --all-files` |
| `agent-instructions` | `npm run lint:md`, `npm run lint:md:nested`, and any repo-specific instruction checks |
| `github-templates` | `pre-commit run check-yaml --all-files`, `pre-commit run actionlint --all-files`, and template rendering review |
| `markdown` | `npm run lint:md`, `npm run lint:md:nested` |
| `powershell` | `Invoke-Pester -Path tests/ -Output Detailed` |
| `json` | `pre-commit run check-json --all-files` |
| `yaml` | `pre-commit run check-yaml --all-files`, `pre-commit run yamllint --all-files`, `pre-commit run actionlint --all-files` |
| `schema` | `pre-commit run check-jsonschema --all-files`, `pre-commit run check-metaschema --all-files`, `pytest tests/test_schema_examples.py -v` after schema or schema-example changes |
| `python` | `pytest tests/ -v --cov --cov-report=term-missing` |
| `terraform` | `terraform fmt -check -recursive`, `tflint --recursive`, `terraform test -verbose` |

Run `pre-commit run --all-files` before committing when the downstream repository uses pre-commit. If a repository intentionally removed a module and its validation tooling, record that in the PR summary rather than reintroducing validation commands blindly.

## Step 13: Record the Reviewed Commit

After all decisions are recorded and validation is complete, update `.template-sync.yml`:

- Set `last_reviewed_template_commit` to the upstream range head that was reviewed.
- Keep `included_modules` current.
- Add, update, or remove `local_overrides` only when the owner made that adoption decision.
- Add or refresh `deferred_protected_candidates` for unresolved protected-file changes.

Do not set `last_reviewed_template_commit` to a commit that was not actually reviewed through the taxonomy and per-file process.

## Step 14: Open the Sync PR

The final sync PR summary is assembled from the sync working notes after decisions and validation are complete. The working notes can remain a scratch artifact; the PR summary is the durable owner-facing record attached to the sync PR.

The sync PR summary SHOULD include:

- upstream template commit range reviewed
- included modules
- unadopted-module activity summarized by module
- unknown modules or unmapped paths surfaced for owner decision
- files adopted unchanged
- files manually merged
- files skipped
- files removed locally because a module was intentionally excluded
- protected files applied with explicit authorization, including authorization basis and any commit-isolation waiver
- protected files deferred for separate authorization
- local overrides applied during this sync, each with a brief upstream change description
- local customizations preserved
- validation commands run
- open questions for the owner

Example summary skeleton:

```markdown
## Template Sync Summary

**Upstream range reviewed:** `1111aaa..2222bbb`
**Included modules:** baseline, agent-instructions, github-templates, markdown, powershell
**Unadopted-module activity:** terraform (`.github/workflows/terraform-ci.yml`)
**Unknown modules or unmapped paths:** none
**Files adopted unchanged:** `templates/markdown/README.md`
**Files manually merged:** `.github/workflows/powershell-ci.yml`, `.github/pull_request_template.md`
**Files skipped:** none
**Files removed locally:** none
**Protected files applied:** none
**Protected files deferred:** `.github/copilot-instructions.md` at `2222bbb`
**Local overrides applied:** `README.md` defaulted to `SKIP`; upstream changed setup prose.
**Local customizations preserved:** self-hosted runner block; project-specific PR checklist.
**Validation:** `pre-commit run --all-files` (passed), `npm run lint:md` (passed), `Invoke-Pester -Path tests/ -Output Detailed` (passed)

## Open Questions

- Should the downstream repository opt into the `schema` module in a follow-up PR?
```

## Worked Example

This example is illustrative. A downstream repository adopts `baseline`, `agent-instructions`, `github-templates`, `markdown`, and `powershell`. It does not use `terraform`, `python`, `json`, `yaml`, or `schema` as independent modules, though YAML files that belong to included modules may still be reviewed through their included module mapping.

### Scenario State

- Downstream sync marker at `.template-sync.yml`: `template_sync.last_reviewed_template_commit` is `1111aaa`
- Upstream `template/main` head: `2222bbb`
- Local customization: `.github/workflows/powershell-ci.yml` uses a self-hosted runner block.
- Local customization: `.github/pull_request_template.md` includes project-specific checklist items.
- Removed at adoption time: Terraform and Python workflows and template directories.

### Fetch and Enumerate

```bash
git fetch template
git diff --name-status -M 1111aaa..template/main
```

The sync working notes start with the reviewed range endpoints:

- **Range base:** `1111aaa`
- **Range head:** `2222bbb`

Hypothetical output:

```text
M       .github/copilot-instructions.md
M       .github/workflows/powershell-ci.yml
M       .github/instructions/powershell.instructions.md
M       .github/pull_request_template.md
M       templates/markdown/README.md
M       .github/workflows/terraform-ci.yml
R100    docs/intro.md   docs/getting-started.md
```

### Filter by Modules

| Path | Module(s) | In scope? |
| --- | --- | --- |
| `.github/copilot-instructions.md` | `agent-instructions` | yes |
| `.github/workflows/powershell-ci.yml` | `powershell`, `yaml` | yes |
| `.github/instructions/powershell.instructions.md` | `powershell`, `agent-instructions` | yes |
| `.github/pull_request_template.md` | `github-templates`, `markdown` | yes |
| `templates/markdown/README.md` | `markdown` | yes |
| `.github/workflows/terraform-ci.yml` | `terraform`, `yaml` | no for `terraform`; summarize as unadopted-module activity because `yaml` is not independently adopted in this scenario |
| `docs/intro.md` to `docs/getting-started.md` | `markdown` | yes |

There are no unknown modules or unmapped paths in this example.

### Decide Per File

| Path | Decision | Notes |
| --- | --- | --- |
| `.github/copilot-instructions.md` | `PROTECTED-REVIEW` | Owner authorization is absent; defer and record under `deferred_protected_candidates`. |
| `.github/workflows/powershell-ci.yml` | `MERGE` | Preserve self-hosted runner block; adopt upstream validation step changes. |
| `.github/instructions/powershell.instructions.md` | `PROTECTED-REVIEW` | Defer and record under `deferred_protected_candidates`. |
| `.github/pull_request_template.md` | `MERGE` | Preserve project checklist; adopt upstream checklist additions. |
| `templates/markdown/README.md` | `TAKE` | No local customization. |
| `docs/intro.md` to `docs/getting-started.md` | `TAKE` | Adopt upstream rename. |

Unadopted-module activity:

| Module | Upstream activity | Disposition |
| --- | --- | --- |
| `terraform` | `.github/workflows/terraform-ci.yml` changed | Not adopted; summarize in PR. |

### Merge With Scratch Copies

```bash
mkdir -p .cache/template-sync
git show 2222bbb:.github/workflows/powershell-ci.yml > .cache/template-sync/powershell-ci.upstream.yml
git show 2222bbb:.github/pull_request_template.md > .cache/template-sync/pr-template.upstream.md
```

Manually reconcile each scratch file against the downstream file. The PowerShell workflow keeps its self-hosted runner block and adopts the upstream validation step changes. The PR template keeps project-specific checklist items and adopts the upstream checklist additions.

### Update the Marker

```yaml
template_sync:
  source_repo: https://github.com/franklesniak/copilot-repo-template.git
  last_reviewed_template_commit: 2222bbb
  included_modules:
    - baseline
    - agent-instructions
    - github-templates
    - markdown
    - powershell
  local_overrides:
    - path: README.md
      reason: "Project-specific; use template only as reference."
      default_decision: SKIP
  deferred_protected_candidates:
    - path: .github/copilot-instructions.md
      source_commit: 2222bbb
      reason: "Updated stack-selection clause; awaiting owner authorization."
    - path: .github/instructions/powershell.instructions.md
      source_commit: 2222bbb
      reason: "Adds parameter-validation guidance; awaiting owner authorization."
```

### Validate

```bash
pre-commit run --all-files
npm run lint:md
```

PowerShell validation:

```powershell
Invoke-Pester -Path tests/ -Output Detailed
```

### PR Summary Fragment

```markdown
**Upstream range reviewed:** `1111aaa..2222bbb`
**Included modules:** baseline, agent-instructions, github-templates, markdown, powershell
**Unadopted-module activity:** terraform (`.github/workflows/terraform-ci.yml`)
**Unknown modules or unmapped paths:** none
**Files adopted unchanged:** `templates/markdown/README.md`, `docs/getting-started.md` renamed from `docs/intro.md`
**Files manually merged:** `.github/workflows/powershell-ci.yml`, `.github/pull_request_template.md`
**Protected files deferred:** `.github/copilot-instructions.md` at `2222bbb`, `.github/instructions/powershell.instructions.md` at `2222bbb`
**Local overrides applied:** none in scope this sync
**Local customizations preserved:** self-hosted runner block; project-specific PR checklist
**Validation:** `pre-commit run --all-files` (passed), `npm run lint:md` (passed), `Invoke-Pester -Path tests/ -Output Detailed` (passed)
```

## Future Automation

Future automation MAY add:

- a `.template-manifest.yml` path-to-module manifest
- a schema for `.template-sync.yml`
- valid and invalid marker fixtures
- a pre-commit hook that checks manifest coverage for managed paths
- a helper script that generates the candidate review table

Until that automation exists, this document is the authoritative procedure.
