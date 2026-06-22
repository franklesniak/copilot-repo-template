<!-- markdownlint-disable MD013 -->

# Azure DevOps Services Support Guide

## Metadata

- **Status:** Active
- **Owner:** Repository Maintainers
- **Last Updated:** 2026-06-22
- **Scope:** Durable adoption guidance for optional Azure DevOps Services host modules in this template. Covers Azure Repos, Azure Pipelines, Azure Boards, Azure DevOps security scanning, dependency-update choices, Copilot code review constraints, and local versus service-backed validation boundaries. Azure DevOps Server is out of scope unless a future change verifies and documents server-specific behavior.
- **Related:** [Issue #758](https://github.com/franklesniak/copilot-repo-template/issues/758), [Optional Configurations](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/OPTIONAL_CONFIGURATIONS.md), [Template Update Procedure](https://github.com/franklesniak/copilot-repo-template/blob/HEAD/TEMPLATE_UPDATE_PROCEDURE.md)

## Purpose

GitHub remains this template's default and primary hosting target. Azure DevOps Services support is additive and module-driven: downstream repositories retain Azure DevOps guidance only when they adopt one or more Azure host modules.

This guide is intentionally service-specific. Treat "Azure DevOps" references here as Azure DevOps Services unless a section explicitly says otherwise. Do not copy these claims to Azure DevOps Server guidance without rechecking Microsoft Learn for server-specific support, feature availability, task support, authentication, and URL behavior.

## Module Ownership

The Azure DevOps host modules split service responsibilities so GitHub-only adopters can remove Azure-only surfaces cleanly:

- `azure-devops-platform` owns Azure DevOps Services project, security, dependency-scanning, service-configuration, and platform-policy guidance that is not itself a pipeline or Azure Repos collaboration template.
- `azure-devops-collaboration` owns Azure Repos PR templates, Azure Boards intake guidance, reviewer-policy guidance, and Azure DevOps security-intake guidance.
- `azure-pipelines` owns Azure Pipelines CI assets and setup guidance.

The durable guide at `docs/azure-devops-support.md` is retained when any one of those Azure modules is adopted. Inline links to this guide from retained shared docs use the `azure-devops-guide-reference-only` marker so GitHub-only materializations strip the link instead of retaining a path to an excluded file.

## Host And URL Boundaries

Azure DevOps Services organizations can use either `https://dev.azure.com/{organization}` or `https://{organization}.visualstudio.com` URL forms. Microsoft Learn documents both as valid organization URL forms and notes that a primary URL can be either form. Preserve the configured organization, project, and repository URL form recorded by the adopter rather than normalizing every reference to one spelling.

When collecting Azure DevOps Services identity during adoption, record:

- Organization root URL or organization name.
- Project name and project URL.
- Azure Repos repository name and repository URL or clone URL.
- Default branch used for PR-template discovery and branch-policy targeting.
- Whether the adoption is Azure-only, GitHub-only, or an explicit mixed-host selection.

Do not invent Azure DevOps organization, project, repository, service-connection, billing, Copilot preview, branch-policy, or security-product state. If connector or API tooling cannot safely verify a setting, record it as an owner decision or manual follow-up.

## Git Import Boundaries

Azure Repos can import or mirror Git repository history, but Git history is only one part of a hosting move. Service configuration must be recreated or deliberately skipped. Treat these as service-backed setup work, not files that arrive automatically with the Git import:

- Azure Pipelines definitions, pipeline registration, variable groups, environments, service connections, and queued validation runs.
- Azure Repos branch policies, build-validation policies, required reviewers, status checks, permissions, and default branch settings.
- Azure Repos PR template placement and branch-specific template rules.
- Azure Boards processes, area paths, iteration paths, work item fields, and work item linking policy.
- Azure DevOps security products, Advanced Security or standalone security-product enablement, repository scanning configuration, and alert ownership.
- Service hooks, notifications, dashboards, wiki content, and repository settings outside the Git tree.

If a downstream adoption imports Git history into Azure Repos, keep the sync report explicit about which service configuration was verified, which was owner-selected, and which remains manual follow-up.

## Azure Pipelines And PR Validation

Azure Repos pull request validation is branch-policy driven. Configure the Azure Pipeline in Azure DevOps Services first, then attach it to the target branch through a build-validation branch policy. Do not treat GitHub Actions `pull_request` triggers or GitHub-only `actionlint` validation as Azure Repos PR validation.

For Azure Pipelines files retained from this template:

- Keep local deterministic validation through `pre-commit run --all-files` for repository files and hooks that are host-neutral.
- Validate Azure Pipelines YAML through Azure DevOps Services pipeline creation, queued runs, or Azure Repos branch-policy build validation.
- Keep GitHub Actions-only hooks such as `actionlint` out of Azure-only validation expectations.
- Treat service connections, pipeline permissions, variable groups, environments, and protected resources as owner-managed Azure DevOps settings.

When a pipeline cannot be validated against Azure DevOps Services in the current task, document the missing service-backed check in the PR or sync report instead of claiming complete Azure validation.

## Azure Repos Collaboration

Azure Repos PR templates are discovered from the default branch. Microsoft Learn documents default-template search locations such as `.azuredevops`, `.vsts`, `docs`, and the repository root, with additional support for branch-specific and additional templates. Prefer host-specific Azure Repos templates under `.azuredevops/` so GitHub and Azure collaboration surfaces do not blur together.

Branch policies are the Azure Repos equivalent for requirements that GitHub repositories often express through rulesets, branch protection, CODEOWNERS, or required checks. Review and configure:

- Minimum reviewer counts and reviewer reset behavior.
- Automatically included reviewers or path-scoped required reviewers.
- Build validation policies for Azure Pipelines PR validation.
- Linked work item policy when Azure Boards linkage is required.
- Comment-resolution, merge-strategy, and status policies where the project uses them.

Azure Boards intake is a service setup decision. Record whether the downstream project uses Azure Boards, how work items should be created, which fields are required, and whether PRs must link work items. Do not infer a Boards process or work item type from the Git tree alone.

## Security Scanning

Keep Azure DevOps security scanning separate from dependency-update automation.

Microsoft Learn documents three current product surfaces for Azure Repos security scanning:

- GitHub Advanced Security for Azure DevOps, which bundles secret scanning push protection, repository secret scanning, dependency scanning, and code scanning.
- GitHub Secret Protection for Azure DevOps, which covers push protection and secret scanning.
- GitHub Code Security for Azure DevOps, which covers dependency alerts and scanning, CodeQL code scanning, third-party findings, and security overview.

Dependency scanning requires configuration. Microsoft Learn documents either dependency scanning default setup or a pipeline using the `AdvancedSecurity-Dependency-Scanning@1` task. Enabling an eligible product alone is not the same as proving that dependency scanning has run on the repository and target branches.

When adopting Azure DevOps security guidance:

- Record the selected product, licensing or billing owner, repositories in scope, alert ownership, and required branch-policy behavior.
- Decide whether dependency scanning uses default setup, an explicit pipeline task, or is intentionally deferred.
- Treat secret handling as service-managed; do not commit PATs, bearer tokens, service connection details, or credential-bearing clone URLs.
- If Advanced Security status checks or branch policies block pull requests on high or critical findings, document that policy as an Azure DevOps service setting.

## Dependency Updates

GitHub Dependabot configuration in `.github/dependabot.yml` is a GitHub platform surface. Azure DevOps-only adoptions do not retain that file, the `validate-dependabot-config` hook, or the Dependabot schema regression fixture.

Azure DevOps dependency scanning alerts and routine dependency version update PRs are different capabilities:

- Azure DevOps security products can identify dependency risk when scanning is configured.
- Routine dependency update PRs require an adopter-selected update tool or service.
- Microsoft still lists automatic Dependabot security-update PRs for Azure DevOps dependency scanning alerts as a future roadmap item, so do not document them as generally available without rechecking the roadmap and feature documentation.

Renovate is the primary documented candidate to evaluate for Azure DevOps routine dependency update automation because Renovate documents Azure DevOps platform support. Keep that separate from Azure Pipelines YAML update support: Renovate's Azure Pipelines manager is opt-in and disabled by default in current Renovate docs. Recheck the manager page for its current stability label before enabling it, because historical guidance has changed over time.

Self-hosted Dependabot on Azure Pipelines is only an optional pattern when maintainers intentionally choose it. Scope any adoption to the source being followed, review the required Azure DevOps permissions, and store tokens or credentials only in the service's secret-management mechanism.

## Copilot Code Review In Azure Repos

Azure Repos Copilot code review is a limited public preview for Azure DevOps Services. Microsoft Learn documents organization-level enablement, repository enablement, individual preview opt-in unless enabled organization-wide, linked Azure subscription billing, and manual review request through the Azure Repos PR reviewers list.

For this template's workflows:

- Do not assume GitHub-hosted Copilot review entitlements cover Azure Repos review usage.
- Do not claim an API-triggered Copilot review path unless available tooling explicitly verifies it.
- Treat Copilot's Azure Repos output as a Comment review only; it does not approve, request changes, satisfy required-reviewer policies, read replies, follow up, or automatically re-review new commits.
- Keep GitHub plugin and GitHub PR workflow guidance scoped to GitHub-hosted repositories.
- Use Azure DevOps connector or REST tooling for reviewers, threads, comments, thread status, and PR statuses only when safely authenticated and available.

## Local And Service Validation

Local validation catches repository-file problems. Service validation catches Azure DevOps configuration and execution problems. Use both where the adopted modules require both.

Run local checks that apply to retained modules, such as:

```bash
pre-commit run --all-files
npm run lint:md
npm run lint:md:links
pytest tests/test_template_manifest.py -v
pytest tests/test_template_sync_materialization_helpers.py -v
pytest tests/test_validate_downstream_adoption.py -v
```

Then validate Azure DevOps service state where relevant:

- Create or update retained Azure Pipelines in Azure DevOps Services.
- Queue representative pipeline runs.
- Attach build-validation branch policies to protected branches.
- Confirm Azure Repos PR template discovery from the default branch.
- Confirm required reviewer, linked work item, comment-resolution, status, and merge policies.
- Confirm security scanning setup, initial scan results, alert routing, and any blocking policies.

If service validation is unavailable in the coding-agent runtime, state the manual owner action and the precise service surface that still needs verification.

## Source References

This guide was verified against these public sources on 2026-06-22:

- Microsoft Learn: [Use Azure DevOps URLs](https://learn.microsoft.com/azure/devops/extend/develop/work-with-urls?view=azure-devops).
- Microsoft Learn: [Import a Git repository](https://learn.microsoft.com/azure/devops/repos/git/import-git-repository?view=azure-devops).
- Microsoft Learn: [Build Azure Repos Git repositories](https://learn.microsoft.com/azure/devops/pipelines/repos/azure-repos-git?view=azure-devops).
- Microsoft Learn: [Branch policies and settings](https://learn.microsoft.com/azure/devops/repos/git/branch-policies?view=azure-devops).
- Microsoft Learn: [Pull request templates](https://learn.microsoft.com/azure/devops/repos/git/pull-request-templates?view=azure-devops).
- Microsoft Learn: [GitHub Copilot code review in Azure Repos](https://learn.microsoft.com/azure/devops/repos/git/copilot-code-reviews?view=azure-devops).
- Microsoft Learn: [Configure GitHub Advanced Security features](https://learn.microsoft.com/azure/devops/repos/security/configure-github-advanced-security-features?view=azure-devops).
- Microsoft Learn: [GitHub Advanced Security dependency scanning](https://learn.microsoft.com/azure/devops/repos/security/github-advanced-security-dependency-scanning?view=azure-devops).
- Microsoft Learn: [Advanced Security Dependency Scanning task](https://learn.microsoft.com/azure/devops/pipelines/tasks/reference/advanced-security-dependency-scanning-v1?view=azure-pipelines).
- Microsoft Learn: [Azure DevOps features timeline](https://learn.microsoft.com/azure/devops/release-notes/features-timeline).
- Renovate docs: [Azure platform support](https://docs.renovatebot.com/modules/platform/azure/).
- Renovate docs: [Azure Pipelines manager](https://docs.renovatebot.com/modules/manager/azure-pipelines/).

## Adoption Checklist

Use this checklist when a downstream repository adopts any Azure DevOps module:

- Select Azure-only, GitHub-only, or mixed-host mode explicitly.
- Record Azure DevOps Services organization, project, repository, and default branch.
- Decide which Azure modules are retained: platform, collaboration, pipelines, or more than one.
- Verify URL form and preserve the adopter's configured primary form.
- Configure Azure Repos branch policies separately from Git file materialization.
- Configure Azure Pipelines registration and service-backed validation separately from local hook validation.
- Configure Azure Repos PR templates under `.azuredevops/` when the collaboration module is retained.
- Decide Azure Boards intake and linked work item policy.
- Decide security product, dependency scanning setup, and alert ownership.
- Decide routine dependency update automation separately from dependency scanning.
- Document any manual service setup that could not be verified during the adoption task.
