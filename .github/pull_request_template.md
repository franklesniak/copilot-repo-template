<!--
Template users: see OPTIONAL_CONFIGURATIONS.md for guidance on tailoring this PR
template. Delete this comment once the PR template is tailored for your needs.

LINK STYLE: Markdown links to repo-internal files in this template MUST use
absolute `https://github.com/<OWNER>/<REPO>/blob/HEAD/<path>` URLs (with the
angle-bracket placeholders replaced by your actual values). Relative forms
(e.g., `../blob/HEAD/<file>`) are unreliable across non-GitHub.com
renderers, GitHub Mobile, and email notifications. See the
"Issue and PR templates" carve-out in `.github/instructions/docs.instructions.md`.

CUSTOMIZE: Replace `OWNER/REPO` below with your actual org/repo
(enforced by `.github/workflows/check-placeholders.yml`).
GHES users: Replace `github.com` with your GHES host (e.g., `github.company.com`).

KNOWN LIMITATION (template repo only): The contributing-guidelines link
below resolves to a non-existent
`https://github.com/<OWNER>/<REPO>/blob/HEAD/CONTRIBUTING.md` URL (with
`<OWNER>/<REPO>` left literal) when rendered on PRs against the template
repository (`franklesniak/copilot-repo-template`), because the `OWNER/REPO`
placeholder on the checklist link is intentionally not substituted in the
template repo — that substitution is the responsibility of downstream adopters
cloning this template. The reason the unsubstituted placeholder is allowed to
persist there (rather than being rejected by CI) is that
`.github/workflows/check-placeholders.yml` is gated off in the template repo
itself (`if: github.repository != 'franklesniak/copilot-repo-template'`);
downstream adopters do not have that gate and so have their substitution
enforced by CI before merge. This is an accepted trade-off: downstream
adopters get a working absolute link after running the placeholder
substitution, which is the dominant audience. Contributors to the template
repo itself can navigate to `CONTRIBUTING.md` via the file tree.

The illustrative URL in this comment uses the angle-bracket placeholder form
`<OWNER>/<REPO>` so that the only absolute `github.com` URL in this file
that contains the literal `OWNER/REPO` placeholder is the live
contributing-guidelines link below — matching the single substitution target
described in the placeholder table in `GETTING_STARTED_NEW_REPO.md` and
reported by section [6] of `.github/workflows/check-placeholders.yml`.
(The literal `OWNER/REPO` placeholder also appears as plain text in the
`CUSTOMIZE` and `KNOWN LIMITATION` paragraphs above. Those occurrences are
not part of an absolute `github.com` URL and so are not matched by section
[6]'s URL-prefix grep; they are descriptive references to the placeholder
itself, not live template URLs.) See the "Issue and PR templates" carve-out
in `.github/instructions/docs.instructions.md` for the broader rule against
shipping live placeholder URLs disguised as comments. That rule and section
[6]'s grep both target the literal `OWNER/REPO`-bearing URL form (which is
why the live checklist link below is detected and customized); the
angle-bracket documentation form used in this comment block is intentionally
outside the scope of that rule and CI check.
-->

## Description

<!-- Provide a brief description of the changes in this PR -->

## Type of Change

<!-- Check all that apply -->

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Dependencies update
- [ ] Configuration/tooling change

## Checklist

<!-- Review and check all items before submitting -->

### General

- [ ] I have read the [contributing guidelines](https://github.com/OWNER/REPO/blob/HEAD/CONTRIBUTING.md)
- [ ] My code follows the coding standards in `.github/instructions/`
- [ ] My changes follow `.github/copilot-instructions.md` and any applicable `.github/instructions/*`
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code where necessary, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added or updated tests where appropriate
- [ ] New and existing tests pass locally (where applicable)

### Pre-commit Verification (if configured)

- [ ] If this repository uses pre-commit, I ran `pre-commit run --all-files` and all checks pass
- [ ] If pre-commit made auto-fixes, I reviewed and committed them

### Python-Specific (if applicable)

<!-- Delete this section if your project does not use Python -->

- [ ] Minimum Python version complies with the bugfix support policy (see [Python Developer's Guide - Versions](https://devguide.python.org/versions/))
- [ ] I have not defaulted to or required unsupported Python versions
- [ ] Type hints are included for public APIs (if using type checking)
- [ ] Tests have been added/updated for Python changes
- [ ] `pytest` passes locally
- [ ] `mypy` type checking passes (if applicable)

### PowerShell-Specific (if applicable)

<!-- Delete this section if your project does not use PowerShell -->

- [ ] PSScriptAnalyzer passes locally (`Invoke-ScriptAnalyzer -Path . -Settings .github/linting/PSScriptAnalyzerSettings.psd1`)
- [ ] Pester tests pass locally (`Invoke-Pester -Path tests/ -Output Detailed`)
- [ ] PowerShell formatting follows repository standards (OTBS, consistent line endings)

## Additional Notes

<!-- Add any additional information that reviewers should know -->

## Related Issues

<!-- Link any related issues using #issue_number -->

Closes #
