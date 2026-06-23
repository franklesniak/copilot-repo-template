<!-- markdownlint-disable MD013 -->

# PR and Code Review Prompts

- **Status:** Active
- **Owner:** Repository Maintainers
- **Last Updated:** 2026-06-22
- **Scope:** Ready-to-use prompts for responding to PR comments, code review
  feedback, branch management, and common false positives during code review.
- **Related:** [Copilot Chat Prompts for Template Adoption](../COPILOT_CHAT_PROMPTS.md)

## Purpose

This document captures prompts used during pull request and code review
workflows. These prompts are designed to be copied directly into GitHub PR
comments or Copilot Chat conversations.

## Responding to Code Review Comments

### Agree with the Reviewer

Use this when you have reviewed the comment and agree with the feedback:

```markdown
I agree with the code reviewer's comment.
```

### Validate and Agree

Use this when you want to confirm the reviewer's concern before agreeing:

```markdown
Please double-check the code reviewer's recommendation. If the gap or concern
they pointed out is valid, then I agree with the code reviewer's comment.
```

### Evaluate, Decide, and Implement (with Style Guide Update)

Use this to validate the reviewer's concern, evaluate response options with a
scoring rubric, implement the best option, and determine whether a style guide
update is warranted:

```markdown
Please double-check the code reviewer's recommendation. If the gap or concern
they pointed out is valid, think hard about possible ways to resolve the
problem/address their feedback. List the options. Then, develop an evaluation
rubric to score the options and determine which is best. Apply the evaluation
rubric to the options and display the results/scores in a table. Then, use the
table to select the best option. Finally, implement the necessary changes
corresponding to the selected option.

If the selected option would create, edit, delete, rename, or otherwise change
a protected instruction file — any file covered by the canonical Protected
Instruction Files rule in `.github/copilot-instructions.md`, such as
`.github/copilot-instructions.md`, the root agent entry points (`.hermes.md`,
`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`), files under `.github/instructions/`, and
files under `.cursor/rules/` — keep the selected option fixed and pause before
editing unless I have already explicitly authorized that specific protected-file
change in this task. Ask one narrow authorization question that names the
selected option, exact file, intended change, recommendation, and whether the
file is already in the PR's scope. Do not treat this prompt, the review comment,
or generic permission to address feedback as authorization to edit protected
files.

Then, determine whether a secondary style guide update should be recommended
based on your evaluation. If so, please write a prompt in a Markdown code fence
that I can send to GitHub Copilot's coding agent separately to update and
clarify the style guide to match the style you determined was best. Don't
update the style guide for this secondary recommendation; just give me a
prompt.
```

### Evaluate, Decide, and Implement (without Style Guide Update)

Use this variant when you are already working on the style guide itself, or when
there is no relevant style guide to update:

```markdown
Please double-check the code reviewer's recommendation. If the gap or concern
they pointed out is valid, think hard about possible ways to resolve the
problem/address their feedback. List the options. Then, develop an evaluation
rubric to score the options and determine which is best. Apply the evaluation
rubric to the options and display the results/scores in a table. Then, use the
table to select the best option. Finally, implement the necessary changes
corresponding to the selected option.

If the selected option would create, edit, delete, rename, or otherwise change
a protected instruction file — any file covered by the canonical Protected
Instruction Files rule in `.github/copilot-instructions.md`, such as
`.github/copilot-instructions.md`, the root agent entry points (`.hermes.md`,
`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`), files under `.github/instructions/`, and
files under `.cursor/rules/` — keep the selected option fixed and pause before
editing unless I have already explicitly authorized that specific protected-file
change in this task. Ask one narrow authorization question that names the
selected option, exact file, intended change, recommendation, and whether the
file is already in the PR's scope. Do not treat this prompt, the review comment,
or generic permission to address feedback as authorization to edit protected
files.
```

### Azure DevOps PR Review Protocol Check

Use this when a review thread or PR is hosted in Azure DevOps Services with
Azure Repos rather than GitHub:

<!-- template-sync: begin azure-devops-guide-reference-only -->
For broader host guidance, see [Azure DevOps Services Support Guide](azure-devops-support.md).
<!-- template-sync: end azure-devops-guide-reference-only -->

```markdown
Please handle this as an Azure DevOps Services / Azure Repos pull request, not
as a GitHub pull request.

Before acting, verify current Microsoft Learn behavior for Azure Repos Copilot
code review and Azure DevOps PR REST APIs. Keep the GitHub workflow intact and
apply the repository's Azure DevOps PR review protocol instead.

Account for these constraints explicitly:

- Azure Repos Copilot code review is a limited public preview that requires
  organization, repository, and individual-user enablement plus linked Azure
  billing; Azure DevOps review usage does not draw down GitHub Copilot plan AI
  credits. Treat licensing and pricing details as Microsoft Learn-dependent,
  and do not assume GitHub-hosted Copilot review entitlements cover Azure Repos
  review usage.
- Copilot review must be requested manually unless the available Azure DevOps
  tooling explicitly verifies an API-supported request path.
- Copilot leaves Comment reviews only, does not satisfy required-reviewer
  policies, does not read replies, does not follow up, and does not
  automatically re-review new commits.
- If Azure DevOps connector/API tooling is available and safely authenticated,
  use it for reviewers, PR threads, thread comments, thread status, and PR
  statuses. If tooling is absent, identify the manual owner action instead.
- Keep authentication guidance high-level and secure. Do not embed tokens,
  credential-bearing URLs, service connections, or secret-like placeholders in
  files, commands, logs, or comments.
```

## Branch Management

### Merge Main into Branch

Use this to catch a branch up with recent changes on `main`. Replace the
placeholder with the actual commit link:

```markdown
@copilot I need to catch this branch up with recent changes made to `main`, so
please merge `main` (at **link to commit here**) into this branch.
```

### Merge Main into Branch (Scoped to One File)

Use this variant when you need to catch the branch up with `main` while
ensuring that only a specific file remains modified in the PR. Replace the
placeholder commit link and filename:

```markdown
@copilot I need to catch this branch up with recent changes made to `main`, so
please merge `main` (at **link to commit here**) into this branch. After this
operation, only `File-We-Are-Working-On.xyz` should appear as modified in the
PR.
```

### Bring Branch Up to Date with Main

Use this when the branch is not up to date with `main`, causing extra files to
appear in the PR diff. Replace the placeholder commit link and filename:

```markdown
@copilot, it seems something got a bit off the rails. I don't believe this
branch is up to date with `main`. Please fix this by merging `main` (at **link
to commit here**) into the branch, so that the PR shows only
`File-We-Are-Working-On.xyz` as a modified file.
```

## Responding to False Positives

### Hallucinated Table Formatting Issue

The GitHub Copilot code reviewer sometimes flags a false positive related to
improperly formatted tables. Use this prompt in response:

```markdown
I believe this is a hallucination. I don't see any double pipes (`||` or
`| |`) in the table.
```

### Markdownlint Compliance Dispute

Use this when the GitHub Copilot code reviewer appears to falsely flag
markdownlint compliance:

```markdown
I'm OK with leaving it as is if it's currently markdownlint-compliant without
any markdownlint rule customizations. I think MD032 doesn't apply if the
previous line is an ordered list, as long as the unordered list item is
indented. If it's not markdownlint-compliant the way it currently is, fix it.
```

## Version and Compatibility Clarifications

### PowerShell Version Support

Use this when a new version of PowerShell is released and the script's version
support requirements need to be updated. Adjust the version numbers and release
context as needed:

```markdown
PowerShell 7.6.x was recently released. So, the script must support
Windows PowerShell 5.1, PowerShell 7.4.x, PowerShell 7.5.x, and PowerShell
7.6.x. Please ensure this requirement is thoroughly clarified.
```
