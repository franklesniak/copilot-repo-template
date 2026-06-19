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

## Security Intake

Do not route vulnerabilities through public Azure Boards work items, Azure Repos pull request comments, or other public project surfaces. Use the private intake path recorded by the security intake policy before publishing the repository for broad use.

## Pull Request Template Placement

Azure Repos reads pull request templates from repository files. Keep the materialized `.azuredevops/pull_request_template.md` aligned with the project's branch policy and reviewer workflow.
