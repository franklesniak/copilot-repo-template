# PR and Code Review Prompts

- **Status:** Active
- **Owner:** Repository Maintainers
- **Last Updated:** 2026-04-18
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

Then, determine whether the style guide should be updated based on your
evaluation. If so, please write a prompt in a Markdown code fence that I can
send to GitHub Copilot's coding agent separately to update and clarify the
style guide to match the style you determined was best. Don't update the style
guide; just give me a prompt.
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
