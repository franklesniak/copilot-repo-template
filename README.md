# Project Name

> **Note:** This repository was created from [`franklesniak/copilot-repo-template`](https://github.com/franklesniak/copilot-repo-template).

## Description

[Add your project description here]

---

## Setup (After Creating from Template)

### 1. Install Dependencies

```bash
# Install root dependencies (enables pre-commit hooks)
npm install

# Install CI workflow dependencies
cd .github/workflows
npm install
cd ../..
```

### 2. Initialize Husky

```bash
npx husky install
```

### 3. (Optional) Install Python Pre-commit Hooks

If your project uses Python:

```bash
pip install pre-commit
pre-commit install
```

### 4. Customize Copilot Instructions

Edit `.github/copilot-instructions.md` to:

- Add your project-specific "Source of Truth" section at the top
- Update the language-specific instructions table

Review and customize `.github/instructions/` files:

- Remove instruction files for languages you don't use
- Modify standards to match your project's requirements

### 5. Update This README

Replace this setup content with your actual project documentation.

---

## Code Quality

This repository enforces code quality through:

- **Markdown Linting:** Runs on pre-commit and in CI
- **GitHub Copilot Instructions:** Guides AI-assisted development
- **Pre-commit Hooks:** Catches issues before they reach CI

### Running Linters Manually

```bash
# Markdown
npm run lint:md

# Python (if applicable)
pre-commit run --all-files
```

---

## License

[Add your license here]
