# Template Maintenance Guide

This guide is for **maintainers of the `franklesniak/copilot-repo-template` repository**. It documents periodic maintenance tasks to keep the template current and functional.

> **Note:** If you created a repository FROM this template, see [OPTIONAL_CONFIGURATIONS.md](OPTIONAL_CONFIGURATIONS.md#ongoing-maintenance) for maintenance guidance relevant to your repository.

---

## Table of Contents

- [Recommended Review Cadence](#recommended-review-cadence)
- [Updating Pre-commit Hook Versions](#updating-pre-commit-hook-versions)
- [Reviewing the Worked-Example Schema and Data CI Workflow](#reviewing-the-worked-example-schema-and-data-ci-workflow)
- [Reviewing Python Version Requirements](#reviewing-python-version-requirements)
- [Reviewing Terraform Version Requirements](#reviewing-terraform-version-requirements)
- [Reviewing Terraform Provider Versions](#reviewing-terraform-provider-versions)
- [Reviewing Instruction File Versions](#reviewing-instruction-file-versions)
- [Reviewing Agent Instruction Files](#reviewing-agent-instruction-files)
- [Testing Template Changes](#testing-template-changes)

---

## Recommended Review Cadence

To keep the template current and functional, maintainers **SHOULD** review template documentation and workflows on a **quarterly basis**.

**Quarterly Review Checklist:**

- [ ] Review and update pre-commit hook versions
- [ ] Check for updates to GitHub Actions used in workflows
- [ ] Review and update Terraform version in CI workflows
- [ ] Review instruction files for accuracy and relevance
- [ ] Verify all CI workflows still pass with latest dependency versions
- [ ] Verify agent instruction files (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`) remain aligned with `.github/copilot-instructions.md`
- [ ] Review and address any open issues or feedback

**Annual Review:**

- [ ] Review Python version requirements (typically October)
- [ ] Review major version updates for key dependencies (Node.js, Terraform providers, etc.)
- [ ] Evaluate new GitHub features that could enhance the template

> **Tip:** Set a calendar reminder for quarterly reviews to ensure consistent maintenance.

---

## Updating Pre-commit Hook Versions

Pre-commit hooks **SHOULD** be kept up-to-date for security and compatibility.

### Maintenance Cadence

This template uses a layered cadence for pre-commit hook maintenance:

- **Routine (weekly, automated).** [Dependabot](.github/dependabot.yml)'s `pre-commit` ecosystem opens grouped pull requests for minor and patch updates to hooks pinned in `.pre-commit-config.yaml`. These PRs SHOULD be reviewed and merged routinely; CI exercises the updated hooks via `pre-commit run --all-files` in `.github/workflows/python-ci.yml`.
- **Major-version refreshes (manual).** Maintainers MAY run `pre-commit autoupdate` manually to refresh major versions, or for an explicit quarterly maintenance pass. Major version bumps are not handled by the grouped Dependabot configuration and require an intentional review.
- **Changelog review.** Before accepting any major hook update (whether from `pre-commit autoupdate` or a Dependabot PR), maintainers MUST review the upstream changelog or release notes for breaking changes. See [Breaking Change Considerations](#breaking-change-considerations) for tool-specific notes.
- **Validation.** After any update — Dependabot-driven or manual — maintainers MUST run `pre-commit run --all-files` locally and confirm a clean pass.
- **Commit hygiene.** Hook version bumps and any auto-fixes produced by the updated hooks MUST be committed together in the same change. Do not split formatting churn caused by an updated hook into a separate "fix formatting" commit.

### Quick Update

```bash
# Check for and apply updates to pre-commit hooks
pre-commit autoupdate

# Test that updated hooks work correctly
pre-commit run --all-files
```

**Frequency:** Quarterly (or as needed for major-version refreshes), or sooner when security advisories are published for hook dependencies. Routine minor and patch updates are handled automatically by Dependabot — see [Maintenance Cadence](#maintenance-cadence) above for the full layered cadence.

### Tools to Track

The following pre-commit hooks are configured in this template. Check their repositories for the latest releases:

| Tool | Repository | Purpose |
| --- | --- | --- |
| pre-commit-hooks | <https://github.com/pre-commit/pre-commit-hooks> | General file checks (trailing whitespace, JSON validation via `check-json`, YAML parsing via `check-yaml`, etc.) |
| Black | <https://github.com/psf/black> | Python code formatting |
| Ruff | <https://github.com/astral-sh/ruff-pre-commit> | Python linting and formatting |
| markdownlint-cli2 | <https://github.com/DavidAnson/markdownlint-cli2> | Markdown linting |
| pre-commit-terraform | <https://github.com/antonbabenko/pre-commit-terraform> | Terraform formatting, validation, and linting |
| yamllint | <https://github.com/adrienverge/yamllint> | YAML style enforcement (driven by `.yamllint.yml`) |
| actionlint | <https://github.com/rhysd/actionlint> | GitHub Actions workflow linting |
| check-jsonschema | <https://github.com/python-jsonschema/check-jsonschema> | JSON Schema validation (worked-example schema and any downstream-added schema-backed file families); also provides the `check-metaschema` hook |

### Files Requiring Manual Updates

After running `pre-commit autoupdate`, manually update version references in documentation files. The `pre-commit autoupdate` command only updates `.pre-commit-config.yaml`—version references in documentation examples require manual updates.

#### Black (Python formatter)

- `.pre-commit-config.yaml` (updated by `pre-commit autoupdate`)
- `OPTIONAL_CONFIGURATIONS.md` (Python pre-commit examples)
- `GETTING_STARTED_NEW_REPO.md` (commented example in pre-commit config)
- `GETTING_STARTED_EXISTING_REPO.md` (Python pre-commit examples)

#### Ruff (Python linter)

- `.pre-commit-config.yaml` (updated by `pre-commit autoupdate`)
- `OPTIONAL_CONFIGURATIONS.md` (Python pre-commit examples)
- `GETTING_STARTED_NEW_REPO.md` (commented example in pre-commit config)
- `GETTING_STARTED_EXISTING_REPO.md` (Python pre-commit examples)

#### pre-commit-terraform (Terraform hooks)

- `.pre-commit-config.yaml` (updated by `pre-commit autoupdate`)
- `.github/instructions/terraform.instructions.md` (pre-commit configuration examples)
- `docs/terraform/TERRAFORM_LINTING_GUIDE.md` (pre-commit configuration examples)
- `docs/terraform/TERRAFORM_COPILOT_INSTRUCTIONS_GUIDE.md` (pre-commit configuration examples)
- `docs/terraform/TERRAFORM_TESTING_GUIDE.md` (pre-commit configuration examples)

#### Other Hooks (no documentation references)

The following hooks are only referenced in `.pre-commit-config.yaml` and do not require manual documentation updates:

- pre-commit-hooks
- markdownlint-cli2

### Verification

After updating versions, use these commands to search for potentially stale version references:

```bash
# Check for Black version references (update the version number as appropriate)
grep -rn "rev:.*26\.1\.0" --include="*.md" --include="*.yaml" .

# Check for Ruff version references (update the version number as appropriate)
grep -rn "rev:.*v0\.14\.14" --include="*.md" --include="*.yaml" .

# Check for pre-commit-terraform version references (update the version number as appropriate)
grep -rn "rev:.*v1\.105\.0" --include="*.md" --include="*.yaml" .

# Generic search for any rev: patterns with version numbers
grep -rn "rev:.*v\?[0-9]\+\.[0-9]\+\.[0-9]\+" --include="*.md" --include="*.yaml" .
```

### Breaking Change Considerations

When updating to new major versions, check the release notes for breaking changes:

- **pre-commit-hooks:** May remove deprecated hooks or change Python version requirements. Review [pre-commit-hooks releases](https://github.com/pre-commit/pre-commit-hooks/releases).

- **Black:** Major releases may introduce style changes that reformat existing code differently. Review [Black changelog](https://github.com/psf/black/blob/main/CHANGES.md). Consider running `black --check` on a representative codebase before upgrading.

- **Ruff:** Frequently adds new rules that may flag previously-passing code. Review [Ruff changelog](https://github.com/astral-sh/ruff/blob/main/CHANGELOG.md). New rules are typically disabled by default, but rule behavior changes can affect existing configurations.

- **pre-commit-terraform:** May change hook IDs, arguments, or tool dependencies. Review [pre-commit-terraform releases](https://github.com/antonbabenko/pre-commit-terraform/releases). Ensure any referenced external tools (terraform, tflint, etc.) remain compatible.

- **yamllint:** New rules or default tightening can flag previously-passing YAML. Review [yamllint releases](https://github.com/adrienverge/yamllint/releases). The repository's `.yamllint.yml` carries a documented `truthy.check-keys: false` exception; verify that exception still applies after major updates.

- **actionlint:** Adds new checks as GitHub Actions evolves. Review [actionlint releases](https://github.com/rhysd/actionlint/releases). The hook builds the binary from a Go toolchain on first run; major version bumps may change ShellCheck integration or runner-label awareness.

- **check-jsonschema:** Validator behavior, JSON Schema draft support, and bundled schema catalog versions can change. Review [check-jsonschema releases](https://github.com/python-jsonschema/check-jsonschema/releases). After bumping, re-run `pytest tests/test_schema_examples.py -v` to confirm the worked-example `valid/` and `invalid/` fixtures still produce the expected pass/fail outcomes.

---

## Reviewing the Worked-Example Schema and Data CI Workflow

The template ships a worked-example JSON Schema (`schemas/example-config.schema.json`), valid and invalid example fixtures under `schemas/examples/example-config/`, the schema-example pytest contract at `tests/test_schema_examples.py`, and the dedicated [`.github/workflows/data-ci.yml`](.github/workflows/data-ci.yml) workflow. These need periodic review to stay aligned with current JSON Schema and pre-commit hook versions.

**When to review:** Quarterly, or whenever `check-jsonschema`, `pre-commit-hooks`, `yamllint`, or `actionlint` have a major version bump.

**What to check:**

1. The worked-example schema's declared `$schema` draft URI is still appropriate (the template uses JSON Schema Draft 2020-12).
2. The worked-example fixtures still demonstrate the contract clearly — at minimum, `valid/minimal.json`, `valid/full.json`, `invalid/missing-required.json`, `invalid/wrong-type.json`, and `invalid/extra-property.json` should each still illustrate a distinct schema behavior.
3. `pytest tests/test_schema_examples.py -v` still passes (every `valid/` fixture exits `0`; every `invalid/` fixture exits non-zero).
4. The `.github/workflows/data-ci.yml` workflow continues to invoke `check-json`, `check-yaml`, `yamllint`, `actionlint`, `check-jsonschema`, and `check-metaschema`, and its top-of-file comment still accurately describes how it differs from `auto-fix-precommit.yml`.
5. The canonical [downstream removal checklist](schemas/README.md#downstream-removal-checklist) in `schemas/README.md` still matches the actual files and hook IDs that ship with the worked example.

**When to update:**

- If a hook ID, hook scope, or schema file moves, update the schema, the fixtures, the pre-commit config, the data CI workflow, and the canonical removal checklist together in the same change.
- Do not duplicate the removal-checklist steps elsewhere; keep `schemas/README.md` as the single source of truth and link to it from any other documentation that mentions removal.

---

## Reviewing Python Version Requirements

This template requires Python versions that are currently receiving bugfix updates from the Python core team.

**When to review:** Annually, typically around October when new Python versions are released.

**What to check:**

1. Visit the [Python Developer's Guide - Versions](https://devguide.python.org/versions/) page
2. Identify which versions are in "bugfix" status (not "security" or "end-of-life")
3. Update the following files if the minimum supported version changes:
   - `.github/workflows/python-ci.yml` (Python version matrix)
   - `pyproject.toml` (requires-python field)
   - `templates/python/pyproject.toml` (requires-python field)
   - `.github/instructions/python.instructions.md` (version references)

---

## Reviewing Terraform Version Requirements

This template uses a pinned Terraform version in CI workflows for reproducibility and pre-commit hook execution.

**When to review:** Quarterly, or when a new stable Terraform release is available.

**What to check:**

1. Visit the [Terraform Releases](https://releases.hashicorp.com/terraform/) page or the [Terraform GitHub Releases](https://github.com/hashicorp/terraform/releases)
2. Identify the latest stable release (avoid alpha, beta, or RC versions)
3. Update the Terraform version in the following workflow files:
   - `.github/workflows/terraform-ci.yml` (format, validate, and test jobs)
   - `.github/workflows/python-ci.yml` (pre-commit job)
   - `.github/workflows/auto-fix-precommit.yml` (auto-fix job)

**Version considerations:**

- **Pre-commit workflows:** Use the latest stable version for pre-commit hooks (terraform_fmt, terraform_validate, terraform_tflint)
- **Terraform CI tests:** The test framework requires Terraform 1.6.0+ and mock_provider requires 1.7.0+. The latest stable version satisfies both requirements.
- **Documentation:** After updating, verify that examples in documentation under `docs/terraform/` remain accurate. Note that these are illustrative examples and do not need to be updated unless the version syntax changes.

---

## Reviewing Terraform Provider Versions

The Terraform instructions file uses the newest stable major versions in provider version constraint examples. These should be reviewed periodically to ensure examples reflect current best practices.

**When to review:** Quarterly, or when a new major version of a provider becomes the recommended stable release.

**What to check:**

1. Visit the provider registries:
   - [AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest)
   - [Azure Provider](https://registry.terraform.io/providers/hashicorp/azurerm/latest)
   - [GCP Provider](https://registry.terraform.io/providers/hashicorp/google/latest)
2. Identify current stable major versions for each provider
3. If a new major version is now the recommended stable release, update the following files:
   - `.github/instructions/terraform.instructions.md` (version constraint examples throughout)
   - `.github/TEMPLATE_DESIGN_DECISIONS.md` (current versions table in "Current Provider Versions in Terraform Examples" section)

**Current versions (as of last update):**

| Provider | Example Constraint | Current Stable |
| --- | --- | --- |
| AWS | `~> 6.0` | 6.31.0 |
| Azure | `~> 4.0` | 4.58.0 |
| GCP | `~> 7.0` | 7.18.0 |

**How to update:**

When updating provider versions in terraform.instructions.md, search for the version constraint patterns:

```bash
# Search for AWS provider version references
grep -n "~> 5\.0\|~> 6\.0" .github/instructions/terraform.instructions.md

# Search for Azure provider version references
grep -n "~> 3\.0\|~> 4\.0" .github/instructions/terraform.instructions.md

# Search for GCP provider version references
grep -n "~> 6\.0\|~> 7\.0" .github/instructions/terraform.instructions.md
```

Update all occurrences to the new major version constraint (e.g., `~> 6.0` to `~> 7.0`).

---

## Reviewing Instruction File Versions

The instruction files in `.github/instructions/` include version numbers in the format `Major.Minor.YYYYMMDD.Revision`.

**When to update:**

- Major version: Breaking changes to coding standards
- Minor version: New guidance or significant clarifications
- Date/Revision: Bug fixes or minor wording changes

**Files to review:**

- `.github/instructions/docs.instructions.md`
- `.github/instructions/python.instructions.md`
- `.github/instructions/powershell.instructions.md`
- `.github/instructions/terraform.instructions.md`

---

## Reviewing Agent Instruction Files

Agent instruction files (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`) are thin entry points that **MUST** stay aligned with `.github/copilot-instructions.md`. The canonical file holds the full shared rule set; the root agent files keep only a minimal inline summary of the highest-priority shared rules plus any platform-specific guidance.

**What to check during review:**

- Canonical-source wording is accurate in `.github/copilot-instructions.md` and the root agent files
- Minimal shared guidance in the agent files still matches the canonical file for safety, pre-commit, validation commands, and language-instruction references
- Platform-specific sections still apply and do not contradict the canonical file
- Removed duplication does not creep back into the agent entry points unnecessarily

**Verification command:**

```bash
# Compare recent commit history to identify changes that may require alignment review
# If copilot-instructions.md was modified more recently than agent files,
# manually verify the minimal summaries and any platform-specific sections
git log --oneline -5 .github/copilot-instructions.md
git log --oneline -5 CLAUDE.md AGENTS.md GEMINI.md
```

**When to update:** Whenever high-priority shared guidance in `.github/copilot-instructions.md` changes, whenever platform-specific guidance changes, or when new agent platforms emerge that require their own convention files.

---

## Testing Template Changes

Before merging significant template changes:

1. Create a test repository from the template
2. Complete the setup process following `GETTING_STARTED_NEW_REPO.md`
3. Verify all CI workflows pass
4. Test the placeholder check workflow triggers and passes after placeholder replacement
5. Verify issue templates render correctly
6. Open and close a test PR to verify the PR template

Delete the test repository after verification.
