<!-- markdownlint-disable MD013 -->

# Cross-platform Terraform pre-commit guidance for native Windows users

## Metadata

- **Status:** Draft
- **Owner:** Repository Maintainers
- **Last Updated:** 2026-05-11
- **Scope:** Draft of an upstream issue body to be filed at `franklesniak/TerraformStyleGuide` proposing generalized guidance for cross-platform Terraform pre-commit hook execution on native Windows / PowerShell, Git Bash, WSL/Linux, macOS, and Linux. This file is a transient artifact intended to be removed from this repository once the upstream issue is filed; it does not document active repository policy.
- **Related:** [Template Design Decisions](.github/TEMPLATE_DESIGN_DECISIONS.md), [Documentation Writing Style](.github/instructions/docs.instructions.md)

## Summary

Downstream repository `franklesniak/copilot-repo-template` replaced its active Terraform pre-commit hooks with repo-local Python wrappers so local Terraform validation works from native Windows / PowerShell, Git Bash, WSL/Linux, macOS, and Linux without relying on POSIX shell hook scripts.

Please consider adding generalized guidance to `franklesniak/TerraformStyleGuide` for cross-platform Terraform pre-commit execution.

## Observed failure mode

On native Windows, `pre-commit run terraform_fmt --all-files` failed before Terraform was invoked when `bash` resolved to the WSL launcher instead of Git Bash:

```text
/bin/bash: C:Usersflesniak.cachepre-commit...hooksterraform_fmt.sh: No such file or directory
```

The path had lost every backslash. Moving Git Bash earlier on PATH allowed the upstream shell hook to start, but then the hook failed later because Terraform was not installed. That showed two separate local-developer concerns:

- POSIX shell hook execution can be fragile for native Windows / PowerShell users when multiple Bash implementations are present.
- Terraform and TFLint still need to be installed and discoverable on PATH for local validation.

## Why POSIX shell hooks are fragile here

The active `antonbabenko/pre-commit-terraform` hooks are shell scripts. They work well in POSIX-oriented environments, but native Windows users can run pre-commit from PowerShell where `bash` may resolve to WSL, Git Bash, or another shim depending on PATH. When the wrong Bash receives a Windows path, hook startup can fail before any Terraform command runs.

That failure can look like a missing hook script or path-loss problem rather than an actionable missing-`terraform` or formatting error.

## Repo-local decision made downstream

`franklesniak/copilot-repo-template` implemented repo-local Python wrappers for active Terraform pre-commit hooks:

- `terraform-fmt` runs `terraform fmt -check -recursive -diff` from the repository root.
- `terraform-validate` finds directories containing `.tf` files and runs `terraform init -backend=false` followed by `terraform validate`.
- `terraform-tflint` runs `tflint --init` and `tflint --recursive --config <repo-root>/.tflint.hcl`.
- The wrappers use `subprocess.run(..., shell=False)`.
- Executable discovery uses `shutil.which`.
- Missing `terraform` or `tflint` produces actionable install guidance instead of Bash/path-loss-looking errors.
- The downstream repository intentionally requires HashiCorp Terraform (`terraform`) only and does not add an OpenTofu fallback for this change.

## Recommended generalized style-guide wording

Consider adding guidance along these lines:

```markdown
For Terraform pre-commit validation that must support native Windows / PowerShell, avoid assuming POSIX shell hook execution. Prefer repo-local wrappers in a runtime already required by the repository's validation stack, such as Python when pre-commit is already in use. Wrappers SHOULD invoke Terraform and related tools with shell execution disabled, SHOULD resolve executables through PATH, and SHOULD fail with clear installation guidance when required tools such as `terraform` or `tflint` are missing.

When using third-party Terraform pre-commit hook collections that rely on shell scripts, document the supported Windows shell environment explicitly, including any Git Bash or WSL assumptions. Do not let native Windows users receive path-translation failures that obscure whether Terraform itself is installed or whether the Terraform configuration failed validation.
```

## Downstream handling

The downstream repository did **not** modify its copied `.github/instructions/terraform.instructions.md` directly because that file is sourced from `franklesniak/TerraformStyleGuide`. This issue draft exists so the style-guide source can decide whether and how to generalize the guidance.
