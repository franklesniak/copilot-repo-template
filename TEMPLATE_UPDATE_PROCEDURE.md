<!-- markdownlint-disable MD013 -->
# Downstream Template Update Procedure

**Version:** 1.1.20260517.5

## Metadata

- **Status:** Active
- **Owner:** Repository Maintainers
- **Last Updated:** 2026-05-17
- **Scope:** Defines the selective review procedure for downstream repositories that were created from, or adopted files from, this template repository. Covers manual and agent-assisted syncs from later upstream template changes. Does not define automation contracts for a future manifest or sync tool.
- **Related:** [Optional Configurations](OPTIONAL_CONFIGURATIONS.md), [Getting Started for New Repositories](GETTING_STARTED_NEW_REPO.md), [Getting Started for Existing Repositories](GETTING_STARTED_EXISTING_REPO.md), [Repository Copilot Instructions](.github/copilot-instructions.md)

## Purpose

Downstream template updates are a selective review process, not a raw merge. A downstream repository may have removed optional modules, customized project identity, changed workflows, or retained only part of the language/tooling guidance from this template. The goal of this procedure is to review later upstream template changes deterministically, adopt only relevant improvements, and preserve downstream ownership decisions.

Use this procedure when a downstream repository wants to review new changes from `franklesniak/copilot-repo-template` after initial adoption. The procedure is suitable for a repository owner or for a coding agent operating under owner direction.

## Terminology

- **Module:** A unit in the taxonomy defined by this procedure, such as `markdown`, `powershell`, or `terraform`. Procedure logic operates on modules.
- **Stack:** Informal shorthand for a related grouping of modules. For example, a "PowerShell stack" may mean `powershell`, `markdown`, `yaml`, and `agent-instructions`, depending on what the downstream repository adopted. Stack is acceptable in prose, but sync decisions MUST be recorded in module terms.
- **Downstream sync marker:** The `.template-sync/marker.yml` file in the downstream repository. Under `template_sync`, it records the upstream template repository, the newest upstream template commit that has been reviewed, the modules the downstream repository has adopted, local override rules, and deferred protected-file candidates.
- **Reviewed range:** The upstream template commit range inspected during a delta sync. It is recorded as `RANGE_BASE_SHA..RANGE_HEAD_SHA`, where both endpoints are resolved upstream template commit SHAs. Full reconciliation does not use a delta range; it compares a committed downstream snapshot against the resolved upstream range head.
- **Included module:** A module listed in the downstream sync marker under `template_sync.included_modules`.
- **Unadopted-module activity:** Upstream activity in a known taxonomy module that is not listed in `included_modules`.
- **Unknown module:** A module name introduced by a newer upstream procedure or future manifest that the downstream marker does not recognize. Unknown modules MUST be surfaced for explicit owner decision.
- **Protected file:** A governance or instruction file that requires explicit owner authorization before editing.
- **Sync working notes:** Temporary notes maintained while applying this procedure. They MAY be a scratch document, a draft PR body, or another local checklist, but they are not the final sync PR summary. They MUST capture the range mode, range endpoints or reconciliation command, range-base rationale, unmapped paths, per-file decisions, protected-file dispositions, validation results, and open questions as those facts are discovered. Step 14 turns these working notes into the final sync PR summary.
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
5. Initialize or update `.template-sync/marker.yml`.
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

This step decides which upstream template changes need review during this sync. It does **not** decide which changes will be adopted. Later steps filter the changed paths by module, review each file, and record which upstream changes were taken, merged, skipped, or deferred.

### Terms Used in This Step

- **Marker path:** Downstream repositories use `.template-sync/marker.yml` as the sync marker path. The marker lives inside `.template-sync/` so the directory can hold committed template-sync support files, such as the sync marker, future manifest files, and review artifacts only if a later issue explicitly defines them as committed outputs.
- **Marker:** Short name for `.template-sync/marker.yml`.
- **Marker authority:** The marker file is authoritative regardless of whether the downstream repository adopts `template-sync-support`. Module adoption controls only whether sync-procedure and marker-related upstream updates are reviewed in future syncs.
- **`template_sync.last_reviewed_template_commit`:** The marker field that stores the newest upstream template commit already reviewed in a prior sync. The durable marker value MUST be a resolved upstream template commit SHA, not a branch name, tag name, or other moving ref. Always store the full 40-character SHA; short SHAs are ambiguous and are not durable marker values. See the [Step 5 example marker](#step-5-initialize-or-update-the-sync-marker) for the field in context.
- **Range mode:** The review path for this sync: normal delta sync, first sync from known lineage, timestamp-proxy delta sync, or full reconciliation.
- **Range base SHA:** The older endpoint of a delta reviewed range. Changes after this commit are candidates for review.
- **Marker-supplied range base:** The present, non-empty `template_sync.last_reviewed_template_commit` value from the marker.
- **Initial range base:** The upstream template commit where a first sync review starts. Upstream changes after that commit are candidates for review.
- **Exact initial range base:** An initial range base that is known to be the upstream template commit used to create or copy the downstream template content.
- **Timestamp-proxy delta sync:** A first-sync delta mode that uses the latest upstream template commit at or before a known copy or import timestamp as an approximate initial range base. It is useful for over-reviewing likely upstream changes, but it is not proof of lineage.
- **Range head ref:** The upstream branch, tag, or commit the owner chooses as the newer endpoint. By default, this is `template/main`.
- **Range head SHA:** The resolved upstream template commit SHA printed from the range head ref.
- **Full reconciliation:** A first-sync mode that compares the committed downstream snapshot against the resolved upstream range head instead of trusting a delta range. It does not require shared Git history between the downstream repository and the template repository.

### Discover the Marker

Before reading any marker contents, choosing a range mode, or filtering by module, check for `.template-sync/marker.yml`.

- If `.template-sync/marker.yml` is present, read it as the downstream sync marker.
- If `.template-sync/marker.yml` is absent, proceed without a marker. The maintainer then chooses one of the first-sync paths below.

### Choose the Range Mode

| Mode | Definition | When to use | Example |
| --- | --- | --- | --- |
| Normal delta sync | Review upstream changes after the marker-supplied range base through the resolved range head. | `.template-sync/marker.yml` exists and `template_sync.last_reviewed_template_commit` is present and non-empty. | Review `1111111111111111111111111111111111111111..2222222222222222222222222222222222222222`. |
| First sync from known lineage | Review upstream changes after the exact upstream commit used to create or copy the downstream template content. | The marker does not supply a range base, but a trustworthy upstream origin commit is known. | Review `dddddddddddddddddddddddddddddddddddddddd..2222222222222222222222222222222222222222`. |
| Timestamp-proxy delta sync | Review upstream changes after an approximate date-based upstream commit chosen from the downstream copy or import timestamp. | The marker does not supply a range base, the exact source commit is unknown, and the owner accepts over-review risk from an approximate base. | Review `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa..2222222222222222222222222222222222222222` and record the timestamp rationale. |
| Full reconciliation | Compare the committed downstream snapshot against the resolved upstream range head instead of trusting a delta range. | The marker does not supply a range base and no trustworthy exact or timestamp-proxy base should be used. | Compare `HEAD` to `2222222222222222222222222222222222222222`. |

Read `.template-sync/marker.yml`, when present, before running any diff. A marker supplies a range base only when `template_sync.last_reviewed_template_commit` is present and non-empty. If the marker is absent, or if the field is missing or empty, the marker does not supply a range base; the maintainer chooses one of the first-sync paths.

When an agent runs this procedure, the repository owner confirms any initial range base or timestamp-proxy choice before the agent trusts it.

| Situation | Mode | What to do |
| --- | --- | --- |
| Marker supplies a range base | Normal delta sync | Use the marker value as the marker-supplied range base, resolve the range head, run the reachability check, then diff the reviewed range. |
| No range base from the marker, but a trustworthy upstream origin commit is known | First sync from known lineage | Use that upstream template commit as the exact initial range base, resolve the range head, run the reachability check, then diff the reviewed range. |
| No range base from the marker, no exact upstream origin commit is known, and the owner accepts a date-based proxy | Timestamp-proxy delta sync | Use the latest upstream template commit at or before the known copy or import timestamp as the initial range base, resolve the range head, run the reachability check, then diff the reviewed range. |
| No range base from the marker, and no trustworthy upstream origin commit is known | Full reconciliation | Compare the downstream tree against the resolved upstream range head, apply the pre-filter below, adjudicate candidate files through Steps 6-7, then set the marker to the resolved upstream range head only after review is complete. |

A present, non-empty marker value that later fails the reachability check is handled by **Check That the Base Is Reachable** below. Do not run a separate routing-time reachability check, and do not silently replace the marker value with the range head.

Full reconciliation is the recommended path for downstream repositories that adopted this template by manual copy, ZIP download, GitHub web UI copy, cherry-picking selected files, heavily editing template files, or using the copy-based paths in [Getting Started for Existing Repositories](GETTING_STARTED_EXISTING_REPO.md).

### Find an Initial Range Base

Use this recipe only when the marker does not supply a range base and the owner wants a delta range instead of full reconciliation:

1. Check adoption records first: the PR or commit that created the downstream repository, local sync notes, release tags, or any recorded upstream template commit.
2. If the exact upstream source commit is known, resolve that commit and record it as an exact initial range base.
3. If the exact source commit is unknown but the template was copied as a snapshot on a known date, the owner MAY choose a timestamp-proxy delta sync: the latest upstream template commit at or before the copy or import timestamp.
4. Verify any proxy by spot-diffing several copied template files against the candidate upstream commit.
5. If the proxy remains uncertain, choose an older commit or use full reconciliation. Over-review is safer than under-review because under-review can silently skip upstream changes.

Record the range base type, the rationale, and any uncertainty in the sync working notes. A stale local checkout, partial copy, cherry-pick, or later manual edit can make a timestamp-proxy delta sync wrong. Record the timestamp-proxy base as date-based and approximate, not as a known source commit.

### Choose the Range Head

Use `template/main` as the range head ref unless the owner explicitly chooses a different upstream branch, tag, or commit. Resolve the ref to a commit SHA and record the printed SHA in the sync working notes as the range head SHA.

Get the range head SHA explicitly:

```bash
git rev-parse 'RANGE_HEAD_REF^{commit}'
```

For example, if the owner is using the default upstream branch, replace `RANGE_HEAD_REF` with `template/main`:

```bash
git rev-parse 'template/main^{commit}'
```

`template/main` can move after each `git fetch`, while the resolved SHA records exactly what was reviewed and is the value Step 13 later writes to `template_sync.last_reviewed_template_commit`. Typing `template/main` directly is acceptable shorthand during interactive inspection when upstream is not changing under the maintainer, but the sync working notes, reachability check, diff command, and marker update use the resolved SHA.

The `^{commit}` suffix peels the reference to its underlying commit. This matters when the range head is an annotated tag: a plain `git rev-parse` on an annotated tag prints the tag object's SHA instead of the commit SHA. For branches and lightweight tags the suffix is harmless and still prints the commit SHA. The single quotes keep the `^{commit}` suffix as literal text, so the shell does not interpret `^`, `{`, or `}`.

If the chosen range base is a ref or tag rather than a commit SHA, resolve it the same way before recording or using it:

```bash
git rev-parse 'RANGE_BASE_REF^{commit}'
```

`RANGE_BASE_REF`, `RANGE_HEAD_REF`, `RANGE_BASE_SHA`, and `RANGE_HEAD_SHA` are placeholders for values recorded in the sync working notes. They are not shell variables that the snippets set.

### Check That the Base Is Reachable

Run this check only for delta range modes. After choosing the range base SHA and range head SHA, confirm that the range base is still in the history that leads to the range head. In beginner terms, "reachable from the range head" means Git can start at `RANGE_HEAD_SHA`, walk backward through parent commits, and eventually find `RANGE_BASE_SHA`. If Git cannot find the base this way, the two endpoints do not describe a normal forward span of upstream template history.

Check reachability with the recorded SHAs:

```bash
git merge-base --is-ancestor RANGE_BASE_SHA RANGE_HEAD_SHA
```

For example:

```bash
git merge-base --is-ancestor 1111111111111111111111111111111111111111 2222222222222222222222222222222222222222
```

Git may print no output when this command succeeds. A successful exit, exit code `0`, means the range base is reachable from the range head and the reviewed range is coherent. A non-zero exit means the base is not reachable from the head. In that case, stop and ask the owner to choose a new range base before running or trusting the diff.

Reasonable replacement bases include the exact upstream origin commit, a conservative timestamp-proxy base, or an older upstream commit chosen after inspecting repository history. Do not silently reset the marker to the range head.

### Run the Delta Diff

After choosing both endpoints and confirming the base is reachable, replace `RANGE_BASE_SHA` and `RANGE_HEAD_SHA` with the recorded values and list the upstream paths changed in that range:

```bash
git diff --name-status -M RANGE_BASE_SHA..RANGE_HEAD_SHA
```

The `-M` flag is required so upstream renames appear as renames, such as `R100 old/path new/path`, instead of unrelated add/delete pairs.

Example where the marker says the last reviewed upstream commit was `1111111111111111111111111111111111111111` and the resolved range head SHA is `2222222222222222222222222222222222222222`:

```bash
git diff --name-status -M 1111111111111111111111111111111111111111..2222222222222222222222222222222222222222
```

Example first-time sync where upstream commit `dddddddddddddddddddddddddddddddddddddddd` is the exact initial range base and the resolved range head SHA is `2222222222222222222222222222222222222222`:

```bash
git diff --name-status -M dddddddddddddddddddddddddddddddddddddddd..2222222222222222222222222222222222222222
```

Do not use the range head as an initial range base just to make the diff empty. That would mark upstream changes as reviewed without reviewing them and would erase the distinction between reviewed upstream changes and adopted upstream changes.

### Run Full Reconciliation

Use this path when the marker does not supply a range base and there is no trustworthy upstream origin commit. Full reconciliation works even when the downstream repository and the template repository share no Git history, because `git diff` can compare two trees directly.

Before running the comparison, confirm that the downstream working tree is clean or that any local edits that should be part of the reconciliation have been committed. In this command, `HEAD` means the committed downstream snapshot being reconciled. If a different local commit or branch is the downstream snapshot under review, use that ref instead of `HEAD`.

```bash
git diff --name-status -M HEAD RANGE_HEAD_SHA
```

Concrete example after substituting the resolved range head SHA:

```bash
git diff --name-status -M HEAD 2222222222222222222222222222222222222222
```

Hypothetical full-reconciliation output:

```text
A       .github/workflows/markdownlint.yml
D       src/app/legacy_service.py
M       README.md
R075    docs/old-template-guide.md   docs/template-sync-guide.md
```

When the downstream repository and the template repository share no Git history, read the status letters this way:

| Status | Meaning |
| --- | --- |
| `A` | Present in the upstream template only. |
| `D` | Present in the downstream repository only. |
| `M` | Present in both trees, but different. |
| `R` | Pairs a downstream-only path, shown first, with a similar upstream-only path, shown second. With no shared Git history, this is a content-similarity match, not a tracked rename; review each path on its merits. |

A cross-tree `R` row is advisory unless shared lineage is confirmed. For example, `R075 docs/old-template-guide.md docs/template-sync-guide.md` might mean the downstream file was renamed from an earlier template guide, or it might only mean the two files happen to share similar content. Without confirmed shared lineage, treat `docs/old-template-guide.md` as a `D` candidate and `docs/template-sync-guide.md` as an `A` candidate, then decide each through the same taxonomy and per-file review process.

Apply a Step 4 pre-filter before per-file review: when a downstream-only path matches no template-managed path or module mapping and is not template-derived, summarize it as local-only noise and exclude it from Steps 6-7. This keeps the downstream repository's own project files out of per-file adjudication.

The pre-filter does not require listing every downstream-only project file. A count plus one-line categorization is enough, such as `247 application source files under src/app/** excluded as local-only noise`.

Do not exclude paths that appear template-derived or require owner attention. Template-derived paths include a copied template file that was later moved, renamed, or locally edited; a workflow copied from the template and renamed for the downstream project; a Markdown guide that still carries template placeholder conventions; or a protected instruction file whose content is based on this template. Send those paths through the Steps 6-7 taxonomy and per-file decision process unchanged.

### Step 4 Completion Checklist

Before moving to Step 5, the sync working notes MUST contain:

- Range mode: normal delta sync, first sync from known lineage, full reconciliation, or timestamp-proxy delta sync when that optional sub-path was used
- Range base SHA, when using a delta range, plus the ref or tag it resolved from if the base was not already a commit SHA
- Range base type: marker-supplied range base, exact initial range base, or timestamp-proxy base
- Range base rationale
- Range head ref
- Range head SHA
- Reachability check result, when using a delta range
- Diff command or full-reconciliation enumeration command used
- Local-only noise excluded by the full-reconciliation pre-filter, when applicable
- Any uncertainty that should be carried into the sync PR summary

Example sync working-notes block:

```markdown
## Template Sync Working Notes

- Marker discovery: `.template-sync/marker.yml` present
- Range mode: normal delta sync
- Range base SHA: `1111111111111111111111111111111111111111`
- Range base type: marker-supplied range base
- Range base rationale: read from `template_sync.last_reviewed_template_commit`
- Range head ref: `template/main`
- Range head SHA: `2222222222222222222222222222222222222222`
- Reachability check: passed
- Enumeration command: `git diff --name-status -M 1111111111111111111111111111111111111111..2222222222222222222222222222222222222222`
- Local-only noise: not applicable
- Uncertainty: none
```

Step 5 initializes or updates `.template-sync/marker.yml` after the range mode is chosen. Step 13 later advances `template_sync.last_reviewed_template_commit` to the resolved upstream range head SHA only after the relevant range or reconciliation has actually been reviewed.

## Step 5: Initialize or Update the Sync Marker

Downstream repositories SHOULD keep the sync marker at `.template-sync/marker.yml`, matching the marker path rule in Step 4. The marker distinguishes reviewed upstream changes from adopted upstream changes. Selective syncs may intentionally skip upstream files, so the preferred field under `template_sync` is `last_reviewed_template_commit`, not `last_adopted_template_commit`.

For example, suppose upstream changed `README.md` and `.github/workflows/terraform-ci.yml`, and the downstream repository reviewed both but adopted neither because `README.md` is locally owned and Terraform is not adopted. The sync still advances `last_reviewed_template_commit` to the resolved range head after review, because those upstream changes were inspected and intentionally skipped. A `last_adopted_template_commit` field would incorrectly imply that skipped-but-reviewed changes need to be reviewed again during the next sync.

If Step 4 used a first-sync delta range because the marker was missing or incomplete, initialize `.template-sync/marker.yml` in this step. Set `template_sync.last_reviewed_template_commit` to the resolved Step 4 range base SHA until Step 13 advances it to the resolved upstream range head SHA. Carry the range-base rationale from the sync working notes into the final sync PR summary.

If Step 4 selected full reconciliation, the marker still has no reviewed upstream commit at this step. You MAY initialize or update other marker fields, such as `source_repo`, `included_modules`, and local overrides chosen by the owner, but do not set `template_sync.last_reviewed_template_commit` until Step 13 records the resolved upstream range head SHA after review is complete.

`local_overrides` and `deferred_protected_candidates` are explained immediately after the example.

Example marker:

```yaml
template_sync:
  source_repo: https://github.com/franklesniak/copilot-repo-template.git
  last_reviewed_template_commit: 1111111111111111111111111111111111111111
  included_modules:
    - baseline
    - agent-instructions
    - github-actions
    - github-platform
    - github-templates
    - markdown
    - powershell
    - json
    - yaml
    - template-sync-support
  local_overrides:
    - path: README.md
      reason: "Project-specific; use template only as reference."
      default_decision: SKIP
    - path: .github/ISSUE_TEMPLATE/config.yml
      reason: "Repository-specific contact links."
      default_decision: MERGE
  deferred_protected_candidates:
    - path: .github/copilot-instructions.md
      source_commit: dddddddddddddddddddddddddddddddddddddddd
      reason: "Adds a stack-selection clause; pending owner authorization."
```

### Marker Semantics

- `source_repo` is the upstream template repository under review.
- `last_reviewed_template_commit` is the resolved upstream template commit SHA whose changes were most recently reviewed, regardless of how many were adopted. It MUST NOT be a branch name, tag name, or other moving ref.
- `included_modules` is the adoption state. Anything not listed is not adopted.
- `local_overrides` changes the starting recommendation for a path, but it MUST NOT hide upstream activity from the sync.
- `deferred_protected_candidates` records protected-file updates that were reviewed but not applied because path-scoped owner authorization was absent.

### Local Overrides

When a changed upstream path appears in `local_overrides` and every mapped module is in `included_modules`, start the per-file decision at the override's `default_decision`. Each applied override MUST still appear in the sync PR summary with a brief description of the upstream change.

The agent or maintainer does not decide that an upstream change is too minor to mention under an override. Listing every applied override is the mechanism that lets the owner notice stale overrides, security-sensitive changes, validation changes, or governance changes that should override the override.

Worked local-overrides mini scenario:

1. The marker has a `README.md` override with `default_decision: SKIP` because the downstream README is project-specific.
2. The reviewed upstream range changes `README.md` to add a security reporting note.
3. The per-file row starts with `SKIP` from the override, but the maintainer upgrades the decision to `MERGE` because the security note is relevant.
4. The sync PR summary still lists the applied override and the upstream change, for example: `README.md` defaulted to `SKIP`; upstream added security reporting guidance; final decision `MERGE`.

### Deferred Protected Candidates

Protected-file candidates remain in `deferred_protected_candidates` until the owner applies them through an authorized PR or explicitly dismisses them. Each entry includes:

- `path`
- `source_commit`
- `reason`

If the same protected path changes again upstream before the candidate is resolved, update the existing entry to the latest relevant source commit and preserve the prior rationale. Add a short refresh note to `reason` when the newer upstream change materially changes what is deferred. Add a separate entry only when the same path has distinct deferred candidates that cannot be represented clearly by one entry.

To explicitly dismiss a deferred protected candidate:

1. Remove that candidate from `.template-sync/marker.yml`.
2. Record the dismissed candidate's `path`, `source_commit`, and dismissal rationale in the sync PR description or a linked owner comment.
3. Allow later upstream changes to the same protected path to surface a new candidate during a future sync.

## Step 6: Use the Authoritative Module Taxonomy

The table in this section is authoritative for this manual procedure. If future automation moves the mapping into a machine-readable manifest, the manifest should preserve these semantics unless a later procedure explicitly changes them.

### Module Definitions

| Module | Scope |
| --- | --- |
| `baseline` | Core repository scaffolding, community files, starter identity files, and repository-level configuration not owned by a narrower module. |
| `agent-instructions` | Agent entry points, Copilot instructions, Cursor rules, reusable prompt guidance, and modular instruction docs. |
| `github-platform` | Repository-level GitHub platform configuration that is not itself an issue template, PR template, CODEOWNERS file, or workflow. Includes Dependabot configuration, repository funding metadata, security-advisory configuration, code-scanning configuration outside of workflows, and similar repository-scope GitHub-only settings. Current example: `.github/dependabot.yml`. Likely future inhabitants include `.github/FUNDING.yml`, `.github/security/*`, and other repository-scope GitHub configuration files. |
| `github-actions` | GitHub Actions workflow files under `.github/workflows/**`. |
| `github-templates` | GitHub issue templates, PR templates, CODEOWNERS, and GitHub collaboration surfaces. |
| `template-onboarding` | Template adoption and template maintainer guidance that downstream repositories typically remove after adoption. |
| `template-sync-support` | Committed files used to perform future template syncs, such as the sync procedure, sync marker, future manifest references, and future sync validation docs. |
| `markdown` | Markdown linting, Markdown templates, docs guidance, and Markdown-only documentation assets. |
| `powershell` | PowerShell scripts, Pester tests, PSScriptAnalyzer configuration, and PowerShell CI. |
| `json` | JSON and JSONC guidance, examples, validation commands, and JSON-oriented template files. |
| `yaml` | YAML guidance, YAML template files, and YAML validation not owned by a narrower module. |
| `schema` | JSON Schema contracts, schema examples, schema validation docs, and schema-specific tests. |
| `python` | Python package scaffolding, Python tests, Python CI, and Python tooling configuration. |
| `terraform` | Terraform modules, tests, linting, documentation, and template files. |

### Path Mapping

Apply the most specific matching row. The most-specific match wins: when an exact path or a narrower glob row covers a path, broader catch-all rows do not contribute additional modules to that path. If two rows match at the same specificity level, use the de-duplicated union of their modules. A path mapped to multiple modules is included in the per-file review only when every mapped module appears in `included_modules`.

A future manifest representation may model richer semantics, such as `requires_all` plus `requires_any`, for platform-spanning files. Until that exists, this human procedure uses the AND-style rule above.

| Path pattern | Module(s) |
| --- | --- |
| `.template-sync/marker.yml` | `template-sync-support` |
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
| `COPILOT_CHAT_PROMPTS.md`, `docs/PR_REVIEW_PROMPTS.md` | `agent-instructions` |
| `.codex/**` | `agent-instructions` |
| `.claude/**` | `agent-instructions` |
| `.github/ISSUE_TEMPLATE/**` | `github-templates` |
| `.github/pull_request_template.md` | `github-templates` |
| `.github/CODEOWNERS` | `github-templates` |
| `.github/dependabot.yml` | `github-platform` |
| `.github/workflows/markdownlint.yml` | `markdown`, `github-actions` |
| `.github/workflows/powershell-ci.yml` | `powershell`, `github-actions` |
| `.github/workflows/python-ci.yml` | `python`, `github-actions` |
| `.github/workflows/terraform-ci.yml` | `terraform`, `github-actions` |
| `.github/workflows/data-ci.yml` | `github-actions` |
| `.github/workflows/check-placeholders.yml` | `baseline`, `github-actions` |
| `.github/workflows/auto-fix-precommit.yml` | `baseline`, `github-actions` |
| `.yamllint.yml` | `yaml` |
| `.pre-commit-config.yaml` | `baseline` |
| `.markdownlint.jsonc`, `package.json`, `package-lock.json`, `.github/scripts/lint-nested-markdown.js` | `markdown` |
| `templates/markdown/**` | `markdown` |
| `templates/powershell/**`, `tests/PowerShell/**`, `.github/linting/PSScriptAnalyzerSettings.psd1`, `src/tools/*.ps1` | `powershell` |
| `templates/json/**` | `json` |
| `templates/yaml/**` | `yaml` |
| `schemas/**` | `schema` |
| `tests/test_schema_examples.py` | `schema` |
| `.github/scripts/terraform_hooks.py`, `tests/test_terraform_hooks.py` | `terraform` |
| `templates/python/**`, `pyproject.toml`, `src/copilot_repo_template/**`, `tests/**/*.py` | `python` |
| `templates/terraform/**`, `docs/terraform/**`, `modules/**`, `tests/**/*.tftest.hcl`, `.tflint.hcl`, `*.tf`, `*.tfvars`, `*.tftpl`, `*.tfbackend` | `terraform` |
| `README.md` | `baseline` |
| `OPTIONAL_CONFIGURATIONS.md` | `baseline` |
| `TEMPLATE_UPDATE_PROCEDURE.md` | `template-sync-support` |
| `GETTING_STARTED_NEW_REPO.md`, `GETTING_STARTED_EXISTING_REPO.md`, `TEMPLATE_MAINTENANCE.md`, `.github/TEMPLATE_DESIGN_DECISIONS.md` | `template-onboarding` |
| `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `LICENSE` | `baseline` |
| `.gitignore`, `.gitattributes`, `.editorconfig`, `.vscode/**` | `baseline` |

`.github/workflows/data-ci.yml` is platform-level under this AND-style human procedure, so it maps to `github-actions`. A later machine-readable manifest may refine this row to require `github-actions` plus at least one of `json`, `yaml`, or `schema`.

If a changed upstream path does not match the table, classify it as `UNMAPPED` in the sync working notes and ask the owner to assign a module before deciding whether to include it.

### Filtering Rules

For each path from `git diff --name-status -M`:

1. Map the path to module(s).
2. Include the path in the per-file review table only if every mapped module is present in `included_modules`.
3. Exclude the path from the per-file review table if any mapped module is absent from `included_modules`.
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
| `.github/workflows/powershell-ci.yml` | `powershell`, `github-actions` | Updated validation steps | Local runner change | `MERGE` | Preserve local runner. |
| `.github/workflows/terraform-ci.yml` | `terraform`, `github-actions` | Updated TFLint setup | Repo excludes Terraform | `SKIP` | Summarize as unadopted-module activity. |
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

If authorization is absent, leave the protected file unchanged and record the candidate in `.template-sync/marker.yml` under `deferred_protected_candidates`.

Example:

```yaml
template_sync:
  deferred_protected_candidates:
    - path: .github/copilot-instructions.md
      source_commit: 2222222222222222222222222222222222222222
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

References to the upstream template repository itself (for example, `franklesniak/copilot-repo-template` in `.template-sync/marker.yml` under `source_repo`, in the Step 2 `git remote add template` example, or in adopted documentation that intentionally links to the upstream template) are not template placeholders and are out of scope for Step 11. Review and decide on those references under Step 10 (Preserve Local Identity) so that legitimate retentions are not rewritten and any deliberate rebranding remains an explicit decision.

Do not replace didactic examples that intentionally explain the placeholder convention unless the downstream repository has removed the associated placeholder-check workflow and no longer wants the convention documented.

## Step 12: Validate by Adopted Module

Run validation appropriate to the included modules and files changed. Full template-like validation remains the safest default when the downstream repository keeps the relevant tooling.

| Module | Example validation |
| --- | --- |
| `baseline` | `pre-commit run --all-files` |
| `agent-instructions` | `npm run lint:md`, `npm run lint:md:nested`, `pre-commit run check-json --all-files`, `pre-commit run check-toml --all-files`, and any repo-specific instruction checks |
| `github-platform` | `pre-commit run check-yaml --all-files`, `pre-commit run yamllint --all-files`, `pre-commit run check-jsonschema --all-files` where configured, and repository-settings review |
| `github-actions` | `pre-commit run check-yaml --all-files`, `pre-commit run yamllint --all-files`, `pre-commit run actionlint --all-files` |
| `github-templates` | `pre-commit run check-yaml --all-files`, `pre-commit run yamllint --all-files`, `npm run lint:md`, and issue or PR template rendering review |
| `template-onboarding` | `npm run lint:md`, `npm run lint:md:nested`, and walkthrough review for kept onboarding paths |
| `template-sync-support` | `npm run lint:md`, `npm run lint:md:nested`, `pre-commit run check-yaml --all-files`, `pre-commit run yamllint --all-files`, and a dry-run review of the sync procedure examples |
| `markdown` | `npm run lint:md`, `npm run lint:md:nested`, `pre-commit run check-json --all-files` |
| `powershell` | `Invoke-Pester -Path tests/ -Output Detailed` |
| `json` | `pre-commit run check-json --all-files` |
| `yaml` | `pre-commit run check-yaml --all-files`, `pre-commit run yamllint --all-files` |
| `schema` | `pre-commit run check-jsonschema --all-files`, `pre-commit run check-metaschema --all-files`, `pytest tests/test_schema_examples.py -v` after schema or schema-example changes |
| `python` | `pytest tests/ -v --cov --cov-report=term-missing`, `pre-commit run check-toml --all-files` |
| `terraform` | `terraform fmt -check -recursive`, `tflint --recursive`, `terraform test -verbose`, `pytest tests/test_terraform_hooks.py -v` after terraform-hook script changes |

Run `pre-commit run --all-files` before committing when the downstream repository uses pre-commit. If a repository intentionally removed a module and its validation tooling, record that in the PR summary rather than reintroducing validation commands blindly.

## Step 13: Record the Reviewed Commit

After all decisions are recorded and validation is complete, update `.template-sync/marker.yml`:

- Set `template_sync.last_reviewed_template_commit` to the resolved upstream range head SHA that was reviewed.
- Keep `included_modules` current.
- Add, update, or remove `local_overrides` only when the owner made that adoption decision.
- Add or refresh `deferred_protected_candidates` for unresolved protected-file changes.

Do not set `template_sync.last_reviewed_template_commit` to a commit that was not actually reviewed through the taxonomy and per-file process. Do not store a branch name, tag name, short SHA, or other moving ref in this marker field; store the full 40-character resolved upstream template commit SHA that was reviewed.

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

**Upstream range reviewed:** `1111111111111111111111111111111111111111..2222222222222222222222222222222222222222`
**Included modules:** baseline, agent-instructions, github-actions, github-templates, markdown, powershell, template-sync-support
**Unadopted-module activity:** terraform (`.github/workflows/terraform-ci.yml`)
**Unknown modules or unmapped paths:** none
**Files adopted unchanged:** `templates/markdown/README.md`
**Files manually merged:** `.github/workflows/powershell-ci.yml`, `.github/pull_request_template.md`
**Files skipped:** none
**Files removed locally:** none
**Protected files applied:** none
**Protected files deferred:** `.github/copilot-instructions.md` at `2222222222222222222222222222222222222222`
**Local overrides applied:** `README.md` defaulted to `SKIP`; upstream changed setup prose.
**Local customizations preserved:** self-hosted runner block; project-specific PR checklist.
**Validation:** `pre-commit run --all-files` (passed), `npm run lint:md` (passed), `Invoke-Pester -Path tests/ -Output Detailed` (passed)

## Open Questions

- Should the downstream repository opt into the `schema` module in a follow-up PR?
```

## Worked Example

This example is illustrative. A downstream repository adopts `baseline`, `agent-instructions`, `github-actions`, `github-templates`, `markdown`, `powershell`, and `template-sync-support`. It does not use `terraform`, `python`, `json`, `yaml`, `schema`, or `github-platform` as independent modules.

### Scenario State

- Downstream sync marker at `.template-sync/marker.yml`: `template_sync.last_reviewed_template_commit` is `1111111111111111111111111111111111111111`
- Upstream range head ref: `template/main`
- Resolved upstream range head SHA: `2222222222222222222222222222222222222222`
- Included modules: `baseline`, `agent-instructions`, `github-actions`, `github-templates`, `markdown`, `powershell`, and `template-sync-support`
- Local customization: `.github/workflows/powershell-ci.yml` uses a self-hosted runner block.
- Local customization: `.github/pull_request_template.md` includes project-specific checklist items.
- Removed at adoption time: Terraform and Python workflows and template directories.

### Fetch and Enumerate

Marker discovery happens before range selection: `.template-sync/marker.yml` is present, so read it as the marker. The marker supplies `1111111111111111111111111111111111111111` as the range base, so this sync uses normal delta sync.

```bash
git fetch template
git rev-parse 'template/main^{commit}'
git merge-base --is-ancestor 1111111111111111111111111111111111111111 2222222222222222222222222222222222222222
git diff --name-status -M 1111111111111111111111111111111111111111..2222222222222222222222222222222222222222
```

The sync working notes start with the reviewed range endpoints:

- **Marker discovery:** `.template-sync/marker.yml` present
- **Range mode:** normal delta sync
- **Range base:** `1111111111111111111111111111111111111111`
- **Range head:** `2222222222222222222222222222222222222222`

Hypothetical output:

```text
M       .github/copilot-instructions.md
M       .github/workflows/powershell-ci.yml
M       .github/instructions/powershell.instructions.md
M       .github/pull_request_template.md
M       TEMPLATE_UPDATE_PROCEDURE.md
M       templates/markdown/README.md
M       .github/workflows/terraform-ci.yml
R100    templates/markdown/intro.md   templates/markdown/getting-started.md
```

### Filter by Modules

| Path | Module(s) | In scope? |
| --- | --- | --- |
| `.github/copilot-instructions.md` | `agent-instructions` | yes |
| `.github/workflows/powershell-ci.yml` | `powershell`, `github-actions` | yes |
| `.github/instructions/powershell.instructions.md` | `powershell`, `agent-instructions` | yes |
| `.github/pull_request_template.md` | `github-templates` | yes |
| `TEMPLATE_UPDATE_PROCEDURE.md` | `template-sync-support` | yes |
| `templates/markdown/README.md` | `markdown` | yes |
| `.github/workflows/terraform-ci.yml` | `terraform`, `github-actions` | no; `terraform` is absent, so AND-style matching excludes the row even though `github-actions` is present |
| `templates/markdown/intro.md` to `templates/markdown/getting-started.md` | `markdown` | yes |

There are no unknown modules or unmapped paths in this example.

### Decide Per File

| Path | Decision | Notes |
| --- | --- | --- |
| `.github/copilot-instructions.md` | `PROTECTED-REVIEW` | Owner authorization is absent; defer and record under `deferred_protected_candidates`. |
| `.github/workflows/powershell-ci.yml` | `MERGE` | Preserve self-hosted runner block; adopt upstream validation step changes. |
| `.github/instructions/powershell.instructions.md` | `PROTECTED-REVIEW` | Defer and record under `deferred_protected_candidates`. |
| `.github/pull_request_template.md` | `MERGE` | Preserve project checklist; adopt upstream checklist additions. |
| `TEMPLATE_UPDATE_PROCEDURE.md` | `TAKE` | Retain the sync procedure and adopt upstream clarification. |
| `templates/markdown/README.md` | `TAKE` | No local customization. |
| `templates/markdown/intro.md` to `templates/markdown/getting-started.md` | `TAKE` | Adopt upstream rename. |

Unadopted-module activity:

| Module | Upstream activity | Disposition |
| --- | --- | --- |
| `terraform` | `.github/workflows/terraform-ci.yml` changed | Not adopted; summarize in PR. |

### Merge With Scratch Copies

```bash
mkdir -p .cache/template-sync
git show 2222222222222222222222222222222222222222:.github/workflows/powershell-ci.yml > .cache/template-sync/powershell-ci.upstream.yml
git show 2222222222222222222222222222222222222222:.github/pull_request_template.md > .cache/template-sync/pr-template.upstream.md
```

Manually reconcile each scratch file against the downstream file. The PowerShell workflow keeps its self-hosted runner block and adopts the upstream validation step changes. The PR template keeps project-specific checklist items and adopts the upstream checklist additions.

### Update the Marker

```yaml
template_sync:
  source_repo: https://github.com/franklesniak/copilot-repo-template.git
  last_reviewed_template_commit: 2222222222222222222222222222222222222222
  included_modules:
    - baseline
    - agent-instructions
    - github-actions
    - github-templates
    - markdown
    - powershell
    - template-sync-support
  local_overrides:
    - path: README.md
      reason: "Project-specific; use template only as reference."
      default_decision: SKIP
  deferred_protected_candidates:
    - path: .github/copilot-instructions.md
      source_commit: 2222222222222222222222222222222222222222
      reason: "Updated stack-selection clause; awaiting owner authorization."
    - path: .github/instructions/powershell.instructions.md
      source_commit: 2222222222222222222222222222222222222222
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
**Upstream range reviewed:** `1111111111111111111111111111111111111111..2222222222222222222222222222222222222222`
**Included modules:** baseline, agent-instructions, github-actions, github-templates, markdown, powershell, template-sync-support
**Unadopted-module activity:** terraform (`.github/workflows/terraform-ci.yml`)
**Unknown modules or unmapped paths:** none
**Files adopted unchanged:** `TEMPLATE_UPDATE_PROCEDURE.md`, `templates/markdown/README.md`, `templates/markdown/getting-started.md` renamed from `templates/markdown/intro.md`
**Files manually merged:** `.github/workflows/powershell-ci.yml`, `.github/pull_request_template.md`
**Protected files deferred:** `.github/copilot-instructions.md` at `2222222222222222222222222222222222222222`, `.github/instructions/powershell.instructions.md` at `2222222222222222222222222222222222222222`
**Local overrides applied:** none in scope this sync
**Local customizations preserved:** self-hosted runner block; project-specific PR checklist
**Validation:** `pre-commit run --all-files` (passed), `npm run lint:md` (passed), `Invoke-Pester -Path tests/ -Output Detailed` (passed)
```

## Future Automation

Future automation MAY add:

- a `.template-sync/manifest.yml` path-to-module manifest
- a schema for `.template-sync/marker.yml`
- valid and invalid marker fixtures
- a pre-commit hook that checks manifest coverage for managed paths
- a helper script that generates the candidate review table
- richer manifest semantics for platform-spanning files, such as representing `.github/workflows/data-ci.yml` as `github-actions` plus at least one of `json`, `yaml`, or `schema`

Tracked follow-up issues are [Issue #530](../../issues/530) for extracting the taxonomy to a machine-readable manifest and [Issue #531](../../issues/531) for marker schema validation.

Until that automation exists, this document is the authoritative procedure.
