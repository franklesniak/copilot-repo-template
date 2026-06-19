<!-- markdownlint-disable MD013 -->

<!--
Azure Repos default PR template.

Microsoft documents that default PR templates named pull_request_template.md
or pull_request_template.txt can live in .azuredevops/, .vsts/, docs/, or the
repository root. This template intentionally uses .azuredevops/ so it stays in
the Azure DevOps collaboration module.

Keep every Azure Repos PR template file on the repository default branch.
Azure Repos uses PR template files from the default branch only.

Link policy: use materialized Azure DevOps web URLs for service destinations
such as the project and repository. Add repository-relative links only after
verifying Azure Repos renders the target correctly in PR descriptions.
-->

# Pull Request

## Summary

Describe the change and the reason for it.

## Azure Boards Intake

- [ ] Linked Azure Boards work item(s) cover bugs, documentation work, or feature requests when applicable.
- [ ] Security-sensitive reports are handled through private security intake, not public Azure Boards work items or PR comments.
- Azure Boards intake policy: `AZURE_BOARDS_INTAKE_POLICY`.

## Validation

- [ ] Local validation completed.
- [ ] Required Azure Pipelines checks are passing or queued.
- [ ] Target branch follows the configured Azure Repos branch policy.

## Azure Repos Review

- Project: AZURE_DEVOPS_PROJECT (AZURE_DEVOPS_PROJECT_URL)
- Repository: AZURE_DEVOPS_REPOSITORY (AZURE_DEVOPS_REPOSITORY_WEB_URL)
- Default branch used for PR template discovery: `AZURE_DEVOPS_DEFAULT_BRANCH`.
- Branch policy reviewer guidance: `AZURE_BRANCH_POLICY_REVIEWER_GUIDANCE`.
- Pull request template policy: `AZURE_REPOS_PR_TEMPLATE_POLICY`.
- Reviewer requirements, minimum approver counts, build validation, and path-scoped reviewer rules are enforced by Azure Repos branch policies, not by this Markdown template.

## Security

- [ ] This change does not expose secrets, credentials, or connection strings.
- [ ] Security-sensitive findings use the private intake policy: `AZURE_SECURITY_INTAKE_POLICY`.
