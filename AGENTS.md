<!-- markdownlint-disable MD013 -->
# Agent Instructions for OpenAI Codex CLI

**Version:** 1.5.20260629.0

## Metadata

- **Status:** Active
- **Owner:** Repository Maintainers
- **Last Updated:** 2026-06-29
- **Scope:** Agent-specific entry point for OpenAI Codex CLI and compatible AI coding agents operating in this repository. Mirrors a minimal inline summary of the highest-priority shared rules; `.github/copilot-instructions.md` remains the canonical source of truth.
<!-- template-sync: begin markdown-reference-only -->
- **Related:** [Repository Copilot Instructions](.github/copilot-instructions.md), [Documentation Writing Style](.github/instructions/docs.instructions.md)
<!-- template-sync: end markdown-reference-only -->

This file provides project-specific instructions for OpenAI Codex CLI and compatible AI coding agents operating in this repository. These instructions ensure that agents follow the same coding standards, safety rules, and workflows that apply to all contributors.

## Canonical Instructions

The authoritative source of truth for all repository rules is **`.github/copilot-instructions.md`** (the repo-wide constitution). All rules defined there apply without exception. **Read that file before making any changes.**

This file intentionally keeps only a minimal inline summary of the highest-priority shared rules so that agents receive critical guidance immediately. The full shared rule set remains in the canonical file above.

**Thin entry point classification:** A thin entry point keeps shared repository rules brief; it does not mean platform-specific or required protocol sections may be discarded. Sections explicitly labeled as platform protocol or required protocol must be preserved unless the repository owner explicitly waives that protocol for the retained agent platform.

## Protected Instruction Files

Instruction files and style guides are protected governance files. Do not create, edit, delete, rename, or otherwise change `.github/copilot-instructions.md`, files under `.github/instructions/`, files under `.cursor/rules/`, or root agent instruction files (`.hermes.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`) unless the repository owner or maintainer has directly and explicitly authorized that specific instruction-file change in the current task. Implied consent is not enough; do not infer authorization from a plan you generated, review feedback, a general request to update docs, cleanup/validation work, or a "keep files in sync" instruction.

If a style-guide update appears warranted but has not been explicitly authorized, propose it separately and wait for approval before editing protected instruction files.

During downstream template adoption and stack selection, perform non-protected cleanup first, record the protected instruction-file edits needed to remove references to deleted tools or stacks, obtain explicit maintainer authorization, then update `.github/copilot-instructions.md`, remaining root agent files, and relevant `.github/instructions/*.instructions.md` files. Bump `Last Updated` and `Version` metadata where present, and avoid temporary migration wording in durable governance docs.

## Essential Repository Summary

- **Safety and security**
  - No secrets in code or repo; never hardcode API keys, tokens, credentials, or connection strings.
  - Treat all external input as untrusted.
  - Respect allowlisted file access boundaries; reject path traversal and symlink escapes.

- **Pre-commit and validation**
  - Run `pre-commit run --all-files` before every commit.
  - Include all auto-fixes in the same commit as the related change.
  - Do not push code when pre-commit or required validation checks are failing; fix issues and re-run until the checks pass.
  - Use the repository's existing validation commands as needed:
    <!-- template-sync: begin markdown-reference-only -->
    - `npm run lint:md`
    <!-- template-sync: end markdown-reference-only -->
    <!-- template-sync: begin python-reference-only -->
    - `python -m pyright --project pyrightconfig.json`
    - `pytest tests/ -m "not slow" -v --cov --cov-report=term-missing`
    - `pytest tests/ -m slow -v --no-cov`
    <!-- template-sync: end python-reference-only -->
    <!-- template-sync: begin schema-reference-only -->
    - `pytest tests/test_schema_examples.py -v` (after any schema or schema-example change)
    <!-- template-sync: end schema-reference-only -->
    <!-- template-sync: begin powershell-reference-only -->
    - `Invoke-Pester -Path tests/ -Output Detailed`
    <!-- template-sync: end powershell-reference-only -->
    <!-- template-sync: begin terraform-reference-only -->
    - `terraform fmt -check -recursive`
    - `tflint --recursive`
    - `terraform test -verbose`
    <!-- template-sync: end terraform-reference-only -->
  - The `pre-commit run --all-files` command exercises the active hooks configured in [`.pre-commit-config.yaml`](.pre-commit-config.yaml), the authoritative list of active hooks.
  <!-- template-sync: begin json-reference-only -->
  - Retained JSON checks include strict JSON syntax (`check-json`).
  <!-- template-sync: end json-reference-only -->
  <!-- template-sync: begin yaml-reference-only -->
  - Retained YAML checks include YAML parsing (`check-yaml`) and style (`yamllint`).
  <!-- template-sync: end yaml-reference-only -->
  - Retained GitHub Actions checks include GitHub Actions linting (`actionlint`).
  - Retained Azure Pipelines assets require host-neutral local hooks plus Azure DevOps Services pipeline creation, queued runs, or branch-policy build validation; `actionlint` does not validate Azure Pipelines YAML.
  <!-- template-sync: begin schema-reference-only -->
  - Retained schema checks include JSON Schema validation (`check-jsonschema`) and schema self-validation (`check-metaschema`).
  <!-- template-sync: end schema-reference-only -->
  - When the `github-actions` module is retained, the dedicated [`.github/workflows/data-ci.yml`](.github/workflows/data-ci.yml) workflow re-runs retained data-file hooks so adopted data-file enforcement can be required via branch protection.
  <!-- template-sync: begin azure-devops-guide-reference-only -->
  - When the `azure-pipelines` module is retained, `.azuredevops/pipelines/data-ci.yml` re-runs retained data-file hooks; pipeline YAML and branch-policy validation remain Azure DevOps Services-backed.
  <!-- template-sync: end azure-devops-guide-reference-only -->
  - Retained data-file authoring guidance lives in the matching module docs.
  <!-- template-sync: begin json-reference-only -->
  - JSON guidance: [`.github/instructions/json.instructions.md`](.github/instructions/json.instructions.md).
  <!-- template-sync: end json-reference-only -->
  <!-- template-sync: begin yaml-reference-only -->
  - YAML guidance: [`.github/instructions/yaml.instructions.md`](.github/instructions/yaml.instructions.md).
  <!-- template-sync: end yaml-reference-only -->
  <!-- template-sync: begin schema-reference-only -->
  - Schema guidance: [`schemas/README.md`](schemas/README.md) and the **Built-in Schema Validation for Real Load-Bearing Configuration Files** ADR in [`.github/TEMPLATE_DESIGN_DECISIONS.md`](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/.github/TEMPLATE_DESIGN_DECISIONS.md).
  <!-- template-sync: end schema-reference-only -->

- **Modular instruction files**
  - Read the relevant file under `.github/instructions/` before modifying matching files:
    - Git attributes: `.github/instructions/gitattributes.instructions.md`
    <!-- template-sync: begin json-reference-only -->
    - JSON: `.github/instructions/json.instructions.md`
    <!-- template-sync: end json-reference-only -->
    <!-- template-sync: begin markdown-reference-only -->
    - Markdown/Docs: `.github/instructions/docs.instructions.md`
    <!-- template-sync: end markdown-reference-only -->
    <!-- template-sync: begin powershell-reference-only -->
    - PowerShell: `.github/instructions/powershell.instructions.md`
    <!-- template-sync: end powershell-reference-only -->
    <!-- template-sync: begin python-reference-only -->
    - Python: `.github/instructions/python.instructions.md`
    <!-- template-sync: end python-reference-only -->
    <!-- template-sync: begin terraform-reference-only -->
    - Terraform: `.github/instructions/terraform.instructions.md`
    <!-- template-sync: end terraform-reference-only -->
    <!-- template-sync: begin yaml-reference-only -->
    - YAML: `.github/instructions/yaml.instructions.md`
    <!-- template-sync: end yaml-reference-only -->

- **Do not**
  - Execute scripts or commands generated by untrusted sources.
  - Add telemetry or external logging services without explicit approval.
  - Weaken security constraints to "make it work."
  - Add new major dependencies without clear justification.
  - Invent behavior when requirements are ambiguous; use an explicit Open Question.
  - Create separate formatting-only or lint-only commits.

## GitHub Plugin Usage

This section is retained as Codex platform protocol. Thin-entry-point pruning must preserve it unless the repository owner explicitly waives Codex GitHub plugin protocol for the retained Codex entry point.

Codex can use the OpenAI-curated GitHub plugin (`github@openai-curated`) in this repository when the user has installed and authorized it. The plugin is the preferred mechanism for any operation that touches remote GitHub state.

- **Prefer the GitHub plugin** for GitHub Issues, pull requests, PR comments, review comments, labels, reactions, PR creation, branch management on GitHub, and any other read or write against remote GitHub state.
- **`gh` is an optional fallback**, not a prerequisite. Codex MUST NOT treat the absence of the `gh` CLI as a blocker when the GitHub plugin can satisfy the same operation. If both are available, use the GitHub plugin first and fall back to `gh` only when the plugin lacks a needed capability.
- **Local `git` remains appropriate** for local working-tree operations: inspecting diffs (`git diff`, `git log`, `git status`), creating branches, staging, committing, and pushing. Use the GitHub plugin for the corresponding remote-side actions (creating PRs, posting comments, reading review state).
- **Before declaring any GitHub operation impossible**, Codex MUST first check whether the GitHub plugin exposes a tool that can perform it. Only after the plugin and any documented fallback have both been ruled out should Codex report the operation as unavailable.

The `.codex/config.toml` file at the repository root declares `[plugins."github@openai-curated"] enabled = true` so that trusted Codex checkouts can opt the plugin in by default. Enabling the plugin in this file does not, by itself, grant GitHub authorization: actual access still depends on the GitHub app/connector installation, the Codex account performing the operation, and the repository's permissions.

## Azure DevOps PR Review Protocol

This section is retained as Codex host-specific protocol. Thin-entry-point pruning must preserve it unless the repository owner explicitly waives Azure DevOps PR review protocol for the retained Codex entry point.

Use this protocol only for Azure DevOps Services pull requests hosted in Azure Repos. The GitHub plugin protocol and GitHub Copilot workflow above remain primary/default for GitHub-hosted repositories; do not substitute GitHub plugin, `gh`, or GitHub GraphQL operations for Azure Repos state.

<!-- template-sync: begin azure-devops-guide-reference-only -->
For broader Azure DevOps Services module setup, validation, security scanning, dependency-update, and URL-form guidance, use the durable Azure DevOps Services support guide at `docs/azure-devops-support.md` when that guide is retained.
<!-- template-sync: end azure-devops-guide-reference-only -->

- Azure Repos Copilot code review is a limited public preview for Azure DevOps Services. It requires sign-up, organization-level enablement by a Project Collection Administrator, repository-level enablement by a repository owner or administrator, and individual-user opt-in through Preview features unless the administrator enables it for the organization. It requires Azure billing through a subscription linked to the Azure DevOps organization; Azure DevOps review usage does not draw down GitHub Copilot plan AI credits. Treat licensing and pricing details as preview-specific and documentation-driven, and do not assume GitHub-hosted Copilot review entitlements cover Azure Repos review usage.
- Copilot review is requested manually from the Azure Repos PR Reviewers list by selecting **Request** next to **GitHub Copilot**. If Azure DevOps tooling supports reviewer operations, Codex MAY inspect or add ordinary reviewers through Azure DevOps Pull Request Reviewers APIs, but MUST NOT claim API-triggered Copilot preview review unless the available tooling explicitly verifies that behavior.
- Copilot always leaves a **Comment** review, never approves or requests changes, does not satisfy required-reviewer policies, and does not block merging. Copilot does not read replies, does not follow up, and does not automatically re-review after new commits; a fresh review requires another manual request.
- Codex has no autonomous Azure DevOps wake-up. Mentions such as `@codex` route Azure DevOps comments only when the user's runtime explicitly forwards them into the active Codex session.
- When Azure DevOps connector/API tooling is available and safely authenticated, Codex MAY inspect PR reviewers, threads, comments, thread status, and PR statuses through Azure DevOps REST APIs, and MAY post replies/comments, update thread status, or create PR statuses. When tooling is missing or insufficient, state the needed manual owner action instead.
- Authentication guidance must stay high-level and secure: prefer Microsoft Entra authentication, service principals or managed identities for automation, Azure DevOps service connections for pipeline scenarios, secure local tool configuration, or environment variables. Treat tokens as opaque values, do not decode claims, and never embed PATs, bearer tokens, service connections, credential-bearing clone URLs, or secret-like placeholders in repository files, commands, logs, or comments.

## PR Review Workflow (Codex-adapted)

This section is retained as Codex platform protocol. Thin-entry-point pruning must preserve it unless the repository owner explicitly waives Codex PR review protocol for the retained Codex entry point.

This workflow adapts the Claude-targeted process documented in `CLAUDE.md` for Codex's capabilities and runtime limitations. Use it when responding to review feedback on a pull request. All GitHub-side reads and writes in the steps below SHOULD go through the GitHub plugin first; fall back to `gh`, GraphQL, or manual owner action only when the plugin does not expose the needed capability (see **Fallbacks for unsupported plugin capabilities** below).

### Runtime limitations to keep in mind

- **No autonomous wake-up.** Codex has no equivalent of `subscribe_pr_activity`. Codex MUST NOT promise webhook-driven wake-up, background polling, or scheduled review responses. The workflow runs only when the user explicitly starts or resumes it inside an active Codex session.
- **`@codex` mention convention.** A PR comment beginning with `@codex` MAY be used as a convention to signal that a comment is intended for Codex, but this works **only** when the user's runtime is configured to route the comment into an active Codex session (for example, when the user pastes the comment into Codex). It is not an autonomous trigger and Codex MUST NOT promise that posting `@codex` will, by itself, cause Codex to act.
- **Tooling-dependent steps.** Where the GitHub plugin (and any documented fallback) does not expose the capability used by a step, document the absence in the relevant reply and continue. Do not block the workflow on missing tooling.

### Handling each review comment

For each code review comment received from GitHub Copilot, a human reviewer, or any other reviewer, follow these steps:

#### Protected-file authorization terms

These terms apply to the review-comment workflow below and defer to the canonical **Protected Instruction Files** rule in [`.github/copilot-instructions.md`](.github/copilot-instructions.md):

- **Protected instruction file:** Any file covered by the canonical Protected Instruction Files rule, including `.github/copilot-instructions.md`, the root agent entry points (`.hermes.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`), files under `.github/instructions/`, and files under `.cursor/rules/`.
- **Explicit protected-file authorization:** A direct maintainer or owner instruction in the current task authorizing the specific protected instruction-file change, either by naming the file or by clearly bounding the protected-file change set. The following are not sufficient on their own: a PR existing, a review comment existing, a generic "address the feedback" request, a reusable prompt, an automated review loop or active review workflow, or generic branch-placement authorization.
- **Already in the PR's scope:** The protected file appears in the PR's changed-files list or diff against its base branch before the review-driven edit under consideration. This is relevant context, not authorization.
- **Newly introduced protected file:** A protected file the PR did not modify before the review-driven edit. Introducing one exceeds any authorization scoped to the PR's existing changes and requires the narrow authorization question in step 7.
- **Within the already-authorized scope:** An edit that resolves the reviewer's comment without expanding the protected file's changes beyond the specific protected-file change the maintainer already explicitly authorized for this task. A larger or more structural change, or one that newly introduces a protected file, exceeds the already-authorized scope.
- **Secondary style-guide recommendation:** A step-8 recommendation to update a style guide to prevent similar issues in the future, distinct from the selected step-7 fix for the current review comment.

1. **Signal processing (conditional).** If the GitHub plugin (or a documented fallback) supports adding emoji reactions to review comments, add an `eyes` (👀) reaction when work begins on the comment and remove it when the comment is fully processed (after step 9, or after the early-exit path in step 2). The reaction's `content` value is the literal string `eyes` as used by the GitHub Reactions API, not the Markdown shortcode `:eyes:`. If reaction tooling is not available in the current runtime, skip this step silently.

2. **Validate the concern.** Determine whether the reviewer's feedback identifies a genuine gap, bug, style violation, or improvement opportunity. If the concern is not valid, post a reply explaining why through the GitHub plugin (or fallback), skip steps 3-8, and continue to step 9.

3. **List options.** Enumerate all reasonable ways to resolve the problem or address the feedback.

4. **Build an evaluation rubric.** Define 4-6 scoring criteria relevant to the concern (for example: style guide compliance, performance, code simplicity, PII safety, PowerShell 5.1 compatibility). Score each criterion on a 1-5 scale.

5. **Score and select.** Apply the rubric to every option and present the results in a Markdown table. Select the option with the highest total score. When the rubric produces a clear highest-scoring option, the agent **MUST** select that option and carry it forward to step 7. A topic touching owner preferences, governance, or policy is not, by itself, an escalation trigger when the rubric produces a clear winner; this clarification stands independently of the protected-file authorization checkpoint in step 7.

    **Escalation path.** If the scores are tied or too close to differentiate objectively, or if the deciding question genuinely cannot be scored, escalate to the PR owner instead of selecting an option. Post a **standalone PR comment** (not a reply to the review thread) through the GitHub plugin containing:

    - A brief summary of the reviewer's concern and which file/line it applies to
    - The options and scoring tables
    - The specific question the owner needs to answer
    - Instructions: *"Reply to this PR comment with your chosen option or direction, then bring the reply back to your active Codex session so Codex can act on it. Posting `@codex` in the reply only routes the comment to Codex when the user's runtime is configured to forward it."*

    **PAUSE** processing of this comment until the owner responds. Continue processing other independent review comments in the meantime.

6. **Post the evaluation.** Reply to the review comment thread with the options table, the scoring table, the selected option, and either a note that implementation will follow in step 7 or, if the fix was already applied, the commit SHA that implements it. Post the reply through the GitHub plugin; fall back to `gh` only if the plugin reply tool is unavailable.

7. **Implement the fix.** Apply the selected option locally, commit, and push to the agent's working branch using local `git`.

    **Protected-file authorization checkpoint.** Before creating, editing, deleting, renaming, or otherwise changing any protected instruction file, including a style guide under `.github/instructions/`, determine whether explicit protected-file authorization already covers that specific protected-file content change in the current task. Keep the selected option fixed while making this authorization determination; do not reopen option selection or ask the maintainer to choose among the scored options again merely because protected-file authorization is required.

    - If explicit protected-file authorization already covers the change and the edit stays within the already-authorized scope, proceed with the selected option under the placement rules below.
    - Otherwise, including when no explicit authorization exists, when the intended edit exceeds the already-authorized scope, or when the edit would newly introduce a protected file the PR did not previously modify, ask one narrow authorization question before editing. The question states the selected option, the protected file, the intended change, the agent's recommendation, and, when applicable, that the protected file is already in the PR's scope. Ask the question in the active Codex session when the owner is present; if the workflow is mediated through PR comments, post it as a standalone PR comment through the GitHub plugin and wait for the user to bring the maintainer's authorization back to the active Codex session.
    - If authorization is declined, record the decision and resolve or leave the review thread according to step 9.

    This checkpoint governs only authorization to change protected-file content. It does not expand any existing authorization for direct PR-head placement, which continues to govern only where an authorized commit lands. To make the fix visible on the PR (i.e., reachable from the PR's head ref), choose the appropriate placement strategy:

    - **Default — push to the working branch only.** Cross-branch integration onto the PR head is a manual owner action. State in the step-6 reply which branch the commit will be pushed to and whether a merge or cherry-pick will be required to make it visible on the PR head.
    - **Direct PR-head push (only with explicit user authorization).** Codex MAY push directly to the PR head branch only when **all** of the following hold:
        1. The user has **explicitly authorized** direct PR-head pushes for this specific PR within the current Codex session. Implied consent is not enough; do not infer authorization from a general "address the review" instruction.
        2. The PR head branch is in the **same repository** as the agent's working branch (cross-fork PRs are excluded).
        3. The push is **non-destructive**: no force-push and no history rewrite on the PR head branch.
        4. All branch protections, required status checks, signing requirements, and CI/CD validation rules on the PR head branch continue to be satisfied.

      When direct PR-head placement is used, record the resulting PR-head commit SHA(s) and post a follow-up reply confirming the placement and listing those SHA(s). If any of the four conditions above is not met, fall back to the default behavior.

8. **Evaluate style guide impact.** Determine whether the relevant language instruction file(s) under `.github/instructions/` should be updated to prevent the same issue in the future. **Read the full applicable style guide(s) before answering** so the recommendation accounts for what the guide already covers and does not duplicate or contradict existing rules. The protected-file authorization checkpoint in step 7 governs selected fixes that would directly change any protected instruction file, including a style guide under `.github/instructions/`. This step governs secondary style-guide recommendations. If such a secondary update is warranted, write a prompt in a Markdown code fence (suitable for sending to GitHub Copilot's coding agent) that describes the style-guide change, and post it as a reply in the same review thread through the GitHub plugin. In this secondary-recommendation case, do **not** modify the style guide directly; if the maintainer later authorizes that change, handle it through the step-7 protected-file authorization checkpoint.

9. **Resolve or leave open.** If **no** style guide update was recommended in step 8, resolve the review comment thread when tooling permits (for example, the GitHub plugin's thread-resolution capability, a `gh api graphql` call against the `resolveReviewThread` mutation, or manual owner action). If a style guide update **was** recommended, leave the thread **open** so the owner can act on the prompt before it is dismissed. If thread-resolution tooling is not available in the current runtime, leave a brief note in the reply that the thread should be resolved manually and continue.

### Optional user-initiated review cycle

When the PR owner explicitly asks Codex to drive multiple review rounds inside an active session (for example, *"run the review cycle on PR #N"*), Codex MAY iterate on the following loop. The loop runs only while the Codex session is active; it MUST NOT be presented as autonomous.

1. **Request a Copilot code review** through the GitHub plugin if it exposes that capability. If not, fall back to `gh pr edit --add-reviewer github-copilot[bot]` (or the equivalent `gh api` call), or ask the user to request the review manually.
2. **Wait for the review.** Codex cannot wake up on webhooks. Either keep the session active and poll the PR's review state through the GitHub plugin (or `gh pr view --json reviews,comments`) at a reasonable cadence, or ask the user to notify Codex when the review arrives.
3. **Process each comment** using the per-comment workflow above. Skip any comment whose ID was already processed in an earlier round of this cycle.
4. **Re-request review** only after the round's fix commits are reachable from the PR head. If a fix commit lives only on the agent's working branch (not on the PR head), state that in the round's summary reply and pause until the owner integrates it, unless the explicit-authorization conditions in step 7 above for direct PR-head placement are satisfied.

### Safety limits for the optional review cycle

When the optional review cycle is used, retain these finite safety limits:

- **Maximum rounds:** 8 review iterations per cycle invocation. After the eighth round, PAUSE and ask the user to confirm whether to continue.
- **Wall-clock timeout:** 6 hours from cycle start. If the timeout is reached, PAUSE and ask the user to confirm whether to continue.
- **Duplicate-comment skipping:** Track comment IDs already processed in earlier rounds and skip them on subsequent rounds.

### Fallbacks for unsupported plugin capabilities

When a workflow step depends on a capability the GitHub plugin does not currently expose, use the following fallbacks and document the chosen fallback in the relevant reply or PR comment:

| Capability | Primary | Fallback |
| --- | --- | --- |
| Request a Copilot code review | GitHub plugin | `gh pr edit --add-reviewer github-copilot[bot]`, `gh api`, or ask the owner to request the review manually |
| Resolve a review thread | GitHub plugin | `gh api graphql` against the `resolveReviewThread` mutation, or ask the owner to resolve the thread manually |
| Add a reaction on a review comment | GitHub plugin | `gh api -X POST /repos/{owner}/{repo}/pulls/comments/{comment_id}/reactions -f content=eyes`, or skip silently if neither path is available |
| Remove a reaction on a review comment | GitHub plugin | First list the comment's reactions via `gh api /repos/{owner}/{repo}/pulls/comments/{comment_id}/reactions` and find the reaction whose `content` matches the one to remove (e.g. `eyes`) and whose `user.login` is the agent's own identity; then delete by reaction id via `gh api -X DELETE /repos/{owner}/{repo}/pulls/comments/{comment_id}/reactions/{reaction_id}`. Skip silently if neither path is available |
| Post a reply to a review comment thread | GitHub plugin | `gh api` against `/repos/{owner}/{repo}/pulls/{pr}/comments/{comment_id}/replies`, or post a standalone PR comment that quotes the original review comment |

If the primary capability and all listed fallbacks are unavailable in the current runtime, skip the step, note the limitation in the relevant reply, and continue rather than failing the workflow.

---

> This file is part of the `franklesniak/copilot-repo-template` template. Customize or remove agent instruction files for platforms you do not use. See [OPTIONAL_CONFIGURATIONS.md](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/OPTIONAL_CONFIGURATIONS.md) for details.
