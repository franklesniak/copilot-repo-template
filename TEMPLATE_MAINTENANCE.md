# Template Maintenance Guide

This guide is for **maintainers of the `franklesniak/copilot-repo-template` repository**. It documents periodic maintenance tasks to keep the template current and functional.

> **Note:** If you created a repository FROM this template, see [OPTIONAL_CONFIGURATIONS.md](OPTIONAL_CONFIGURATIONS.md#ongoing-maintenance) for maintenance guidance relevant to your repository.

---

## Table of Contents

- [Recommended Review Cadence](#recommended-review-cadence)
- [Updating Pre-commit Hook Versions](#updating-pre-commit-hook-versions)
- [Reviewing Python Version Requirements](#reviewing-python-version-requirements)
- [Reviewing Instruction File Versions](#reviewing-instruction-file-versions)
- [Testing Template Changes](#testing-template-changes)

---

## Recommended Review Cadence

To keep the template current and functional, maintainers should review template documentation and workflows on a **quarterly basis**.

**Quarterly Review Checklist:**

- [ ] Review and update pre-commit hook versions
- [ ] Check for updates to GitHub Actions used in workflows
- [ ] Review instruction files for accuracy and relevance
- [ ] Verify all CI workflows still pass with latest dependency versions
- [ ] Review and address any open issues or feedback

**Annual Review:**

- [ ] Review Python version requirements (typically October)
- [ ] Review major version updates for key dependencies (Node.js, Terraform providers, etc.)
- [ ] Evaluate new GitHub features that could enhance the template

> **Tip:** Set a calendar reminder for quarterly reviews to ensure consistent maintenance.

---

## Updating Pre-commit Hook Versions

Pre-commit hooks should be kept up-to-date for security and compatibility:

```bash
# Check for and apply updates to pre-commit hooks
pre-commit autoupdate

# Test that updated hooks work correctly
pre-commit run --all-files
```

**Frequency:** Monthly or when security advisories are published for hook dependencies.

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
