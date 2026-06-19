<!-- markdownlint-disable MD013 -->

# Azure DevOps Services Adoption Guidance

## Project Identity

- Host provider: Azure DevOps Services
- Organization: AZURE_DEVOPS_ORGANIZATION
- Organization URL: AZURE_DEVOPS_ORGANIZATION_URL
- Project: AZURE_DEVOPS_PROJECT
- Project URL: AZURE_DEVOPS_PROJECT_URL
- Repository: AZURE_DEVOPS_REPOSITORY
- Repository URL: AZURE_DEVOPS_REPOSITORY_WEB_URL
- HTTPS clone URL: AZURE_DEVOPS_CLONE_URL
- Default branch: AZURE_DEVOPS_DEFAULT_BRANCH

## First-Adoption Service Setup

Some Azure DevOps Services behavior is configured in the service rather than materialized from repository files. Track these items during first adoption so they are not mistaken for local file failures.

- Azure Boards intake policy: AZURE_BOARDS_INTAKE_POLICY
- Azure Repos pull request template policy: AZURE_REPOS_PR_TEMPLATE_POLICY
- Branch policy reviewer guidance: AZURE_BRANCH_POLICY_REVIEWER_GUIDANCE
- Security intake policy: AZURE_SECURITY_INTAKE_POLICY
- Security product enablement: AZURE_SECURITY_PRODUCT_ENABLEMENT
- Dependency update policy: AZURE_DEPENDENCY_UPDATE_POLICY

## Azure Boards Intake

Azure Boards replaces GitHub issue forms only as an intake destination; copying `.github/ISSUE_TEMPLATE/**` does not configure Azure Boards. Use the Azure Boards intake policy above to decide how this repository records:

- Bugs: create or link an Azure Boards work item that captures reproduction steps, observed behavior, and expected behavior.
- Documentation work: create or link an Azure Boards work item that names the affected document, audience, and validation needed.
- Feature requests: create or link an Azure Boards work item that states the user need, acceptance criteria, and priority signal.
- Security-sensitive reports: do not create public Azure Boards work items. Route vulnerabilities through the private security intake policy before adding any public tracking item.

## Security Intake

Do not route vulnerabilities through public Azure Boards work items, Azure Repos pull request comments, or other public project surfaces. Use the private intake path recorded by the security intake policy before publishing the repository for broad use.

## Pull Request Template Placement and Links

Azure Repos reads pull request templates from repository files, but the templates are advisory. Enforce reviewer requirements, build validation, linked work-item checks, and status checks through [Azure Repos branch policies](https://learn.microsoft.com/azure/devops/repos/git/branch-policies?view=azure-devops).

The default Azure Repos PR template for this module is `.azuredevops/pull_request_template.md`. Microsoft documents in [Azure Repos pull request templates](https://learn.microsoft.com/azure/devops/repos/git/pull-request-templates?view=azure-devops) that default PR templates named `pull_request_template.md` or `pull_request_template.txt` can live in `.azuredevops/`, `.vsts/`, `docs/`, or the repository root, and Azure Repos searches those locations in that order. All PR template files must be located on the repository default branch, and Azure Repos uses PR template files from the default branch only.

Use Azure DevOps web URLs materialized from provider inputs for service destinations such as the project and repository. The checked-in template keeps `AZURE_DEVOPS_PROJECT_URL` and `AZURE_DEVOPS_REPOSITORY_WEB_URL` out of Markdown link destinations so offline link validation stays meaningful; the placeholder helper renders those project and repository lines as Markdown links during materialization. Add repository-relative links only after verifying Azure Repos renders them correctly for the intended target.

## Branch-Policy Reviewer Guidance

`.github/CODEOWNERS` configures GitHub review ownership; it does not configure Azure Repos. For Azure Repos, use branch policies to automatically include reviewers, require reviewer approval, and scope reviewer requirements by path when needed. Record the chosen setup in `AZURE_BRANCH_POLICY_REVIEWER_GUIDANCE` and keep the PR template aligned with that service-side policy.
