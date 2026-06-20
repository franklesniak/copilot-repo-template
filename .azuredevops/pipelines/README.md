# Azure Pipelines CI

This optional module provides Azure Pipelines YAML for repositories hosted in
Azure DevOps Services with Azure Repos Git. GitHub Actions remains the
template's primary and default CI host; these files are additive for downstream
repositories that select the `azure-pipelines` module.

## Pipeline Files

| File | Purpose | Module requirements |
| --- | --- | --- |
| `precommit.yml` | Aggregate `pre-commit run --all-files` gate | `baseline`, `azure-pipelines` |
| `check-placeholders.yml` | Post-adoption placeholder scan | `baseline`, `azure-pipelines` |
| `markdownlint.yml` | Markdown lint, nested Markdown lint, and link checks | `markdown`, `azure-pipelines` |
| `powershell-ci.yml` | PSScriptAnalyzer and Pester checks | `powershell`, `azure-pipelines` |
| `python-ci.yml` | mypy and pytest checks | `python`, `azure-pipelines` |
| `terraform-ci.yml` | Terraform fmt, validate, TFLint, and test checks | `terraform`, `azure-pipelines` |
| `data-ci.yml` | JSON, YAML, schema, and template-sync validation hooks | `azure-pipelines` plus one retained data or template-sync module |

## Pull Request Validation

For Azure Repos Git, configure pull request validation with an Azure Repos
branch policy build validation rule that points at the desired pipeline. Do not depend on YAML `pr` triggers for Azure Repos pull requests; Azure Pipelines
documents YAML PR triggers as a GitHub and Bitbucket Cloud feature, while Azure
Repos PR validation is driven by branch policies.

Recommended branch policy setup:

1. Create each required pipeline from the YAML file under `.azuredevops/pipelines/`.
2. In Azure Repos branch policies for the protected branch, add build validation
   policies for the checks you want to require.
3. Mark the aggregate `precommit.yml` pipeline required when pre-commit remains
   part of the adopted repository.
4. Mark stack-specific pipelines required only when their matching modules are
   retained downstream.

## Validation Boundary

Local YAML tools such as `check-yaml` and `yamllint` verify syntax and style for
these files. Azure Pipelines service-schema validation is service-backed: create
or update the pipeline in Azure DevOps, then use a queued pipeline run or branch
policy build validation to verify Azure DevOps task availability and runtime
schema behavior.

## References

- [YAML `pr` trigger schema](https://learn.microsoft.com/azure/devops/pipelines/yaml-schema/pr?view=azure-pipelines)
- [Azure Repos build validation branch policy](https://learn.microsoft.com/azure/devops/repos/git/branch-policies?view=azure-devops#build-validation)
- [Azure Repos Git pull request triggers](https://learn.microsoft.com/azure/devops/pipelines/repos/azure-repos-git?view=azure-devops#pr-triggers)
