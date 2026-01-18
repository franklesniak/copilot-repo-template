<!--
=============================================================================
TEMPLATE CUSTOMIZATION GUIDE
=============================================================================
This is a pull request template for the repository. When cloning this template
repository, customize the following sections:

1. SECTIONS TO KEEP - The Description, Type of Change, and Related Issues
   sections are universally applicable. Keep these for all project types.

2. GENERAL CHECKLIST - Review each item and modify based on your project:
   - Keep: self-review, documentation updates, no new warnings, Copilot instructions
   - Modify: Update the contributing guidelines link if your CONTRIBUTING.md
     is renamed or moved to a different location (e.g., docs/CONTRIBUTING.md)
   - Remove: Items that don't apply to your project (e.g., remove test-related
     items if your project doesn't have automated tests yet)

3. PRE-COMMIT VERIFICATION - Keep this section if using pre-commit hooks;
   remove if your project doesn't use pre-commit.

4. PYTHON-SPECIFIC SECTION - This section is specific to Python projects:
   - For Python projects: Keep and customize as needed
   - For non-Python projects: Remove this entire section
   - For multi-language projects: Keep Python section if applicable, and add
     additional language-specific sections as needed

5. POWERSHELL-SPECIFIC SECTION - This section is specific to PowerShell projects:
   - For PowerShell projects: Keep and customize as needed
   - For non-PowerShell projects: Remove this entire section
   - For multi-language projects: Keep PowerShell section if applicable

6. ADDING LANGUAGE-SPECIFIC SECTIONS - Add sections for your project's stack:
   - Node.js: npm/yarn test passes, ESLint passes, TypeScript compiles
   - .NET: dotnet test passes, no compiler warnings
   - Go: go test passes, go vet passes, golint passes
   - Rust: cargo test passes, clippy passes
   - Java: Maven/Gradle tests pass, checkstyle passes

7. TYPE OF CHANGE OPTIONS - Add or remove options based on your workflow:
   - Add: "Refactoring (no functional changes)" if you track refactors separately
   - Add: "Security fix" if security changes need special review
   - Add: "Performance improvement" for performance-focused projects
   - Remove: Options that don't apply to your project

8. ADDITIONAL NOTES SECTION - Keep this for reviewers to provide context that
   doesn't fit elsewhere. Consider adding prompts for common needs like
   "migration steps" or "deployment considerations" if applicable.

9. RELATED ISSUES SECTION - Keep this section. Update the "Closes #" syntax
   if your project uses different keywords (e.g., "Fixes #", "Resolves #").

10. TEST REQUIREMENTS - The test-related checklist items use "where appropriate"
    language for template portability. This acknowledges that:
    - Not all projects have test infrastructure set up initially
    - Not all changes require new tests (e.g., documentation-only changes)
    - Downstream repos can strengthen this language (e.g., "I have added tests")
      once they have mature test infrastructure
=============================================================================
-->

## Description

<!-- Provide a brief description of the changes in this PR -->

## Type of Change

<!-- Check all that apply -->

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Configuration/tooling change

## Checklist

<!-- Review and check all items before submitting -->

### General

- [ ] I have read the [contributing guidelines](../blob/HEAD/CONTRIBUTING.md)
- [ ] My code follows the coding standards in `.github/instructions/`
- [ ] My changes follow `.github/copilot-instructions.md` and any applicable `.github/instructions/*`
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code where necessary, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added or updated tests where appropriate
- [ ] New and existing tests pass locally (where applicable)

### Pre-commit Verification

- [ ] I have run `pre-commit run --all-files` locally and all checks pass
- [ ] I have reviewed and committed all auto-fixes made by pre-commit hooks

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
