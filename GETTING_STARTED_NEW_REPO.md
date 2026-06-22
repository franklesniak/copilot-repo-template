# Getting Started: Creating a New Repository from This Template

This guide walks you through creating a brand-new repository using `franklesniak/copilot-repo-template`. It is designed for beginners who may not be familiar with Git, Python, Node.js, or pre-commit. If you are looking to merge this template into an existing repository, refer to the README.md instead.

**Estimated time to complete:** 30-60 minutes (depending on your system and internet speed)

---

## Table of Contents

- [What This Template Provides](#what-this-template-provides)
  - [Repo Layout Examples](#repo-layout-examples)
- [Prerequisites](#prerequisites)
  - [Windows Setup](#windows-setup)
  - [macOS Setup](#macos-setup)
  - [Linux/FreeBSD Setup](#linuxfreebsd-setup)
- [Creating Your Repository on GitHub](#creating-your-repository-on-github)
- [Cloning Your New Repository](#cloning-your-new-repository)
- [Installing Dependencies](#installing-dependencies)
- [First-Adoption Preflight Checklist](#first-adoption-preflight-checklist)
- [Initial Placeholder Replacement](#initial-placeholder-replacement)
- [Creating Optional Labels](#creating-optional-labels)
- [Installing and Configuring Pre-commit](#installing-and-configuring-pre-commit)
- [Language-Specific Customization](#language-specific-customization)
  - [JSON/YAML-Heavy Repositories](#jsonyaml-heavy-repositories)
- [Updating package.json Metadata](#updating-packagejson-metadata)
- [Customizing the Pull Request Template](#customizing-the-pull-request-template)
- [Updating README.md](#updating-readmemd)
- [Customizing CONTRIBUTING.md](#customizing-contributingmd)
- [Customizing CODE_OF_CONDUCT.md](#customizing-code_of_conductmd)
- [Updating Copilot Instructions](#updating-copilot-instructions)
  - [Protected-File Adoption Step](#protected-file-adoption-step)
- [Additional Configuration (Optional)](#additional-configuration-optional)
- [Validation and Testing](#validation-and-testing)
  - [Confirm Local Validation Prerequisites](#confirm-local-validation-prerequisites)
- [Cleanup](#cleanup)
- [Troubleshooting](#troubleshooting)
- [Development Workflow](#development-workflow)
- [Next Steps](#next-steps)

---

## What This Template Provides

This template repository includes:

- **GitHub Copilot Instructions:** Comprehensive coding standards that guide AI-assisted development
- **Language-Specific Guidelines:** Modular instruction files for Markdown, PowerShell, Python, Terraform, JSON/JSONC, and YAML
- **Linting Configurations:** Pre-configured settings for markdownlint, PSScriptAnalyzer, TFLint, and yamllint
- **Data-File Validation:** Pre-commit and CI coverage for JSON, YAML, GitHub Actions workflows, and the worked JSON Schema example
- **Pre-commit Hooks:** Automated code quality checks before commits
- **Issue Templates:** Structured templates for bug reports, feature requests, and documentation issues
- **Pull Request Template:** Checklist-based template for consistent PR reviews
- **CI Workflows:** GitHub Actions workflows for linting, testing, and validation
- **Multi-Agent Support:** Instruction files for Cursor Agent, Hermes Agent, Claude Code, OpenAI Codex CLI, and Gemini Code Assist

### Repo Layout Examples

Depending on your project's needs, you may organize your repository in different ways. Here are two common patterns:

**Root-Only Repo (Single Configuration):**

A repository with a single Terraform or application configuration:

```text
my-project/
├── .github/
│   ├── copilot-instructions.md
│   ├── instructions/
│   └── workflows/
├── main.tf              # Primary configuration
├── variables.tf         # Input variables
├── outputs.tf           # Output values
├── versions.tf          # Provider version constraints
├── .terraform.lock.hcl  # Dependency lock file
└── README.md
```

**Module-Based Repo:**

A repository containing reusable modules with examples and tests:

```text
my-modules/
├── .github/
│   ├── copilot-instructions.md
│   ├── instructions/
│   └── workflows/
├── modules/
│   └── vpc/
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       ├── versions.tf
│       └── README.md
├── examples/
│   └── basic-vpc/
│       ├── main.tf
│       └── README.md
├── tests/
│   └── vpc.tftest.hcl
└── README.md
```

Choose the structure that best fits your project when customizing the template.

---

## Prerequisites

Before you can use this template, you need to install several tools on your computer. Follow the instructions for your operating system below.

### Windows Setup

#### 1. Install Git for Windows

Git is the version control system used to track changes in your code.

1. Download Git for Windows from [https://git-scm.com/download/win](https://git-scm.com/download/win)
2. Run the installer and use these recommended settings:
   - **Select Components:** Keep defaults, ensure "Git Bash Here" is checked
   - **Default editor:** Choose your preferred editor (VS Code recommended if installed)
   - **Initial branch name:** Select "Let Git decide" (uses `master`) or "Override" and type `main`
   - **PATH environment:** Select "Git from the command line and also from 3rd-party software"
   - **SSH executable:** Select "Use bundled OpenSSH"
   - **HTTPS transport backend:** Select "Use the native Windows Secure Channel library"
   - **Line ending conversions:** Select "Checkout Windows-style, commit Unix-style line endings" (recommended)
   - **Terminal emulator:** Select "Use MinTTY"
   - **Default behavior of `git pull`:** Select "Fast-forward or merge"
   - **Credential helper:** Select "Git Credential Manager"
   - **Extra options:** Keep defaults
3. Click **Install** and wait for completion

#### 2. Install Python

Python is required for pre-commit hooks and Python-based linting tools.

1. Download Python from [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Run the installer
   - **IMPORTANT:** Check the box that says "Add Python to PATH" before clicking Install
   - Click "Install Now" for the default installation

> **Warning:** If you forget to check "Add Python to PATH," you will need to uninstall and reinstall Python, or manually add Python to your PATH environment variable.

#### 3. Install Node.js

Node.js is required for markdown linting scripts.

1. Download the LTS (Long Term Support) version from [https://nodejs.org/](https://nodejs.org/)
2. Run the installer and accept the defaults
3. When prompted about "Automatically install the necessary tools," you can uncheck this option (not required for this template)

#### 4. Install Terraform and TFLint (if keeping Terraform support)

Terraform support is optional, but the template ships Terraform validation by default. If you keep `.github/workflows/terraform-ci.yml`, `.tflint.hcl`, or the Terraform pre-commit hooks, install both HashiCorp Terraform and TFLint on PATH.

**Terraform options for Windows:**

- Download the Windows binary from [HashiCorp's Terraform install guide](https://developer.hashicorp.com/terraform/install), place `terraform.exe` in a stable tools directory, and add that directory to PATH.
- If your organization uses Chocolatey, run `choco install terraform`.

**TFLint options for Windows:**

- Download the Windows binary from the [TFLint installation guide](https://github.com/terraform-linters/tflint#installation), place `tflint.exe` in a stable tools directory, and add that directory to PATH.
- If your organization uses Chocolatey, run `choco install tflint`.

Restart PowerShell after changing PATH.

#### 5. Verify Your Installations

Open **PowerShell** (search for "PowerShell" in the Start menu) and run these commands:

```powershell
# Check Git version
git --version

# Check Python version
python --version

# Check pip version
python -m pip --version

# Check Node.js version
node --version

# Check npm version (comes with Node.js)
npm --version

# Optional Terraform tools, required if keeping Terraform support
terraform version
tflint --version
```

You should see version numbers for each command. If any command shows an error, revisit the installation steps for that tool.

**Example output:**

```text
git version 2.43.0.windows.1
Python 3.12.1
pip 23.3.2 from C:\Users\YourName\AppData\Local\Programs\Python\Python312\Lib\site-packages\pip (python 3.12)
v24.17.0
11.17.0
```

---

### macOS Setup

#### 1. Install Xcode Command Line Tools

The Xcode Command Line Tools provide essential developer tools including Git.

1. Open **Terminal** (press Cmd+Space, type "Terminal," and press Enter)
2. Run the following command:

   ```bash
   xcode-select --install
   ```

3. A dialog will appear asking you to install the tools. Click **Install** and wait for completion.

> **Note:** This may take several minutes depending on your internet connection.

#### 2. Install Homebrew (Recommended)

Homebrew is a package manager that makes it easy to install and manage software on macOS. While optional, it simplifies installation of Python and Node.js.

1. Open Terminal and run:

   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. Follow the on-screen instructions. You may be prompted to enter your password.
3. After installation, follow the instructions shown to add Homebrew to your PATH (the installer will display the exact commands).

#### 3. Install Python

**Option A: Using Homebrew (recommended if you installed Homebrew):**

```bash
brew install python
```

**Option B: Using the official installer:**

1. Download Python from [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Run the installer package
3. Follow the prompts to complete installation

#### 4. Install Node.js

**Option A: Using Homebrew (recommended):**

```bash
brew install node
```

**Option B: Using the official installer:**

1. Download the LTS version from [https://nodejs.org/](https://nodejs.org/)
2. Run the installer package
3. Follow the prompts to complete installation

#### 5. Install Terraform and TFLint (if keeping Terraform support)

Terraform support is optional, but the template ships Terraform validation by default. If you keep `.github/workflows/terraform-ci.yml`, `.tflint.hcl`, or the Terraform pre-commit hooks, install both HashiCorp Terraform and TFLint on PATH.

```bash
brew tap hashicorp/tap
brew install hashicorp/tap/terraform
brew install tflint
```

You can also use the official Terraform and TFLint binary downloads if Homebrew is not available.

#### 6. Verify Your Installations

Open **Terminal** and run these commands:

```bash
# Check Git version
git --version

# Check Python version
python3 --version

# Check pip version
pip3 --version

# Check Node.js version
node --version

# Check npm version
npm --version

# Optional Terraform tools, required if keeping Terraform support
terraform version
tflint --version
```

You should see version numbers for each command.

**Example output:**

```text
git version 2.39.3 (Apple Git-145)
Python 3.12.1
pip 23.3.2 from /opt/homebrew/lib/python3.12/site-packages/pip (python 3.12)
v24.17.0
11.17.0
```

> **Note:** On macOS, use `python3` instead of `python` to ensure you're using Python 3.

---

### Linux/FreeBSD Setup

The commands below vary depending on your Linux distribution. Find your distribution and follow the appropriate instructions.

#### Ubuntu/Debian

```bash
# Update package lists
sudo apt update

# Install Git
sudo apt install git

# Install Python 3 and pip
sudo apt install python3 python3-pip python3-venv

# Install Node.js (using NodeSource for LTS version)
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install nodejs
```

#### Fedora/RHEL/CentOS

```bash
# Install Git
sudo dnf install git

# Install Python 3 and pip
sudo dnf install python3 python3-pip

# Install Node.js
sudo dnf install nodejs npm
```

#### Arch Linux

```bash
# Install Git
sudo pacman -S git

# Install Python 3 and pip
sudo pacman -S python python-pip

# Install Node.js and npm
sudo pacman -S nodejs npm
```

#### FreeBSD

```bash
# Install Git
sudo pkg install git

# Install Python 3 and pip
sudo pkg install python3 py39-pip

# Install Node.js and npm
sudo pkg install node npm
```

#### Alternative: Using nvm for Node.js

If you prefer to manage multiple Node.js versions, you can use nvm (Node Version Manager):

```bash
# Install nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

# Restart your terminal or run:
source ~/.bashrc  # or ~/.zshrc if using zsh

# Install the latest LTS version of Node.js
nvm install --lts

# Verify installation
node --version
npm --version
```

#### Install Terraform and TFLint (if keeping Terraform support)

Terraform support is optional, but the template ships Terraform validation by default. If you keep `.github/workflows/terraform-ci.yml`, `.tflint.hcl`, or the Terraform pre-commit hooks, install both HashiCorp Terraform and TFLint on PATH.

- Install Terraform using the package or binary instructions for your distribution in [HashiCorp's Terraform install guide](https://developer.hashicorp.com/terraform/install).
- Install TFLint using the Linux install script or release binary from the [TFLint installation guide](https://github.com/terraform-linters/tflint#installation).

#### Verify Your Installations

Open a terminal and run these commands:

```bash
# Check Git version
git --version

# Check Python version
python3 --version

# Check pip version
pip3 --version

# Check Node.js version
node --version

# Check npm version
npm --version

# Optional Terraform tools, required if keeping Terraform support
terraform version
tflint --version
```

You should see version numbers for each command.

---

## Creating Your Repository on GitHub

Now that you have all the prerequisites installed, you can create your new repository from this template.

### Step 1: Navigate to the Template Repository

1. Open your web browser and go to [https://github.com/franklesniak/copilot-repo-template](https://github.com/franklesniak/copilot-repo-template)

### Step 2: Create a New Repository from the Template

1. Click the green **"Use this template"** button near the top of the page
2. Select **"Create a new repository"** from the dropdown menu

### Step 3: Configure Your New Repository

On the "Create a new repository" page:

1. **Owner:** Select your GitHub username or an organization you belong to
2. **Repository name:** Enter a name for your new repository (e.g., `my-new-project`)
3. **Description (optional):** Enter a brief description of your project
4. **Visibility:**
   - **Public:** Anyone can see your repository
   - **Private:** Only you and people you invite can see your repository
5. **Include all branches:** Leave this **unchecked** unless you have a specific reason to include other branches. Most users only need the default branch.

### Step 4: Create the Repository

1. Click the green **"Create repository"** button
2. Wait a few seconds for GitHub to create your repository

You will be redirected to your new repository's page. The URL will be something like `https://github.com/YOUR-USERNAME/your-repo-name`.

---

## Cloning Your New Repository

Now you need to download (clone) your new repository to your local computer.

### Understanding SSH vs. HTTPS

There are two main ways to connect to GitHub:

- **HTTPS:** Easier to set up. You authenticate with your GitHub username and a personal access token (or GitHub CLI).
- **SSH:** More secure and convenient for frequent use. Requires setting up SSH keys once.

For beginners, we recommend **HTTPS** because it's simpler to get started. Advanced users may prefer SSH.

### Windows: Cloning with Git Bash or PowerShell

1. Open **Git Bash** (right-click on your desktop or in a folder and select "Git Bash Here") or **PowerShell**
2. Navigate to the folder where you want to store your project:

   ```powershell
   # Example: Navigate to your Documents folder
   cd ~/Documents
   ```

3. Clone your repository (replace `YOUR-USERNAME` and `your-repo-name` with your actual values):

   **Using HTTPS:**

   ```powershell
   git clone https://github.com/YOUR-USERNAME/your-repo-name.git
   ```

   **Using SSH (if you've set up SSH keys):**

   ```powershell
   git clone git@github.com:YOUR-USERNAME/your-repo-name.git
   ```

4. Navigate into your cloned repository:

   ```powershell
   cd your-repo-name
   ```

### macOS/Linux/FreeBSD: Cloning with Terminal

1. Open **Terminal**
2. Navigate to the folder where you want to store your project:

   ```bash
   # Example: Navigate to your home directory's projects folder
   cd ~/projects
   # Or create one if it doesn't exist:
   mkdir -p ~/projects && cd ~/projects
   ```

3. Clone your repository (replace `YOUR-USERNAME` and `your-repo-name` with your actual values):

   **Using HTTPS:**

   ```bash
   git clone https://github.com/YOUR-USERNAME/your-repo-name.git
   ```

   **Using SSH (if you've set up SSH keys):**

   ```bash
   git clone git@github.com:YOUR-USERNAME/your-repo-name.git
   ```

4. Navigate into your cloned repository:

   ```bash
   cd your-repo-name
   ```

> **Tip:** If you haven't set up SSH keys and want to use SSH, see [GitHub's SSH key documentation](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account).

---

## Installing Dependencies

After cloning, you need to install the project dependencies.

### Step 1: Navigate to Your Repository Directory

Make sure you're in your repository's root directory. You should see files like `package.json`, `README.md`, and the `.github` folder.

**Windows (PowerShell):**

```powershell
# If you're not already there:
cd C:\path\to\your-repo-name

# Verify you're in the right place by listing files:
dir
```

**macOS/Linux/FreeBSD (Terminal):**

```bash
# If you're not already there:
cd ~/projects/your-repo-name

# Verify you're in the right place by listing files:
ls -la
```

### Step 2: Install Node.js Dependencies

Run the following command to install the Node.js dependencies defined in `package.json`:

**All platforms:**

```bash
npm install
```

This command:

- Reads the `package.json` file to determine which packages are needed
- Downloads and installs those packages into a `node_modules` folder
- Creates or updates `package-lock.json` to lock dependency versions

**What gets installed:** The Node.js dependencies are primarily for **markdown linting** (markdownlint-cli2). This ensures your documentation follows consistent formatting rules.

> **Note:** The `node_modules` folder is automatically excluded from Git (via `.gitignore`), so these files won't be committed to your repository.
>
> **Tip:** The repository also includes an optional nested markdown linting script that checks Markdown code blocks within your documentation. See [Nested Markdown Linting Configuration](OPTIONAL_CONFIGURATIONS.md#nested-markdown-linting-configuration) in the optional configurations guide for details.

---

## First-Adoption Preflight Checklist

Before editing files whose contents depend on maintainer choices, create a root `_TODO-repo-init.md` checklist in the downstream repository. Discovery and non-content setup may happen before this checklist exists, but agents and maintainers MUST NOT invent contact emails, reporting channels, branch protection policy, or GitHub repository settings to continue setup.

When governance, security, community, CODEOWNERS, issue-template, PR-template, or other template-derived file content depends on unknown owner policy, ask the owner a concrete question before finalizing that file. The checklist records the answer or deferral state; it does not replace asking, and generated or adopted files MUST NOT ship unresolved placeholders or misleading policy defaults.

This preflight is for first-time template adoption only. Do not recreate it or re-ask resolved questions during later template syncs when the answers are already recorded in `_TODO-repo-init.md`, `.template-sync/marker.yml`, or an equivalent committed adoption note named by the adoption procedure.

Use repository files and Git metadata for discoverable facts, such as the repository name, default branch, current placeholder values, and existing files. Use the checklist for manual GitHub settings and maintainer policy decisions that cannot be inferred safely from files, such as private vulnerability reporting, Discussions, branch protection, label availability, conduct reporting, security reporting, CODEOWNERS identity, GHES host override, and any explicit opt-in to broader rewriting of template-derived files. The checklist also tracks protected-file adoption decisions, unresolved settings with deferral states, and resolution evidence.

The default adoption mode for protected files and template-derived governance, community, process, workflow, and collaboration files is `minimal-preservation`: keep upstream wording and structure, substitute placeholders, trim sections owned by unadopted manifest modules, fix broken links, and record required local overrides in `.template-sync/marker.yml` when template sync support is retained. Select `tailored` only when the maintainer explicitly wants broader downstream rewriting for a specific file or file set. Record that choice before editing so agents do not repeatedly prompt when the default applies.

Create `_TODO-repo-init.md` from this example and replace bracketed notes only after the maintainer confirms them:

```markdown
# Repository Initialization Checklist

This file records first-adoption decisions for this downstream repository. It is downstream-owned state, not an upstream template file, and is excluded from upstream template sync candidate review.

Keep unresolved items in this file until the maintainer completes them through the GitHub UI, an authorized GitHub connector, a safe API call, or a later maintainer action. Do not create this file in the upstream template repository unless the template manifest and sync procedure are deliberately changed to handle it.

When a template-derived file depends on unknown governance, security, community, CODEOWNERS, issue-template, PR-template, or other owner policy, ask the owner a concrete question before finalizing that file. Record unresolved dependent-file items only after the question and the dependent file/status impact are identified.

## Discoverable Repository State

- [ ] Repository owner/name recorded from the GitHub URL or Git remote: `OWNER/REPO`
- [ ] Repository visibility recorded: `[public, private, or internal]`
- [ ] Repository default branch recorded neutrally from GitHub or `git remote show origin`: `[recorded default branch]`
- [ ] Existing `SECURITY.md`, `CODE_OF_CONDUCT.md`, `.github/CODEOWNERS`, issue templates, PR template, and `.github/dependabot.yml` reviewed before replacement.
- [ ] Existing `.template-sync/marker.yml`, `_TODO-repo-init.md`, or equivalent adoption note checked before asking repeated questions.
- [ ] Existing labels reviewed in GitHub under **Issues** > **Labels**.
- [ ] Existing Discussions state reviewed in GitHub under **Settings** > **General** > **Features**.
- [ ] Existing repository rulesets or branch protection reviewed in GitHub under **Settings** > **Rules**.

## Manual GitHub Settings

These settings may be completed through the GitHub UI even when `gh` is unavailable. If a GitHub connector or approved API call is used instead, record the action and evidence in the item.

- [ ] Private vulnerability reporting decision: `[enable, leave disabled, or not available]`
  - UI path: open **Settings** > **Code security and analysis**, then review **Private vulnerability reporting**.
  - After enabling, verify the **Security** tab and `SECURITY.md` private-reporting links.
  - Docs: [Configuring private vulnerability reporting for a repository](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/configuring-private-vulnerability-reporting-for-a-repository). If this link breaks, search `private vulnerability reporting repository` on `docs.github.com`.
  - Evidence: `[date, actor, screenshot/link, connector result, or maintainer note]`
- [ ] GitHub Discussions decision: `[enable or leave disabled]`
  - UI path: open **Settings** > **General** > **Features**, then review **Discussions**.
  - If enabled, verify the repository **Discussions** tab appears and decide whether issue templates should point users there.
  - Docs: [Enabling or disabling GitHub Discussions for a repository](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/enabling-or-disabling-github-discussions-for-a-repository). If this link breaks, search `enable GitHub Discussions repository` on `docs.github.com`.
  - Evidence: `[date, actor, screenshot/link, connector result, or maintainer note]`
- [ ] Labels decision, including `triage`: `[create, skip, or already present]`
  - UI path: open **Issues** > **Labels**, then create or edit labels required by issue templates and local triage policy.
  - Minimum template label to review: `triage` with description `Needs triage` and color `d4c5f9`, unless the maintainer chooses a different triage label.
  - Docs: [Managing labels](https://docs.github.com/en/issues/using-labels-and-milestones-to-track-work/managing-labels). If this link breaks, search `manage labels GitHub issues` on `docs.github.com`.
  - Evidence: `[date, actor, labels created/skipped, connector result, or maintainer note]`
- [ ] Default branch decision: `[keep recorded default branch, rename, or defer]`
  - UI path: open **Settings** > **Branches**, then review the default branch selector before changing it.
  - If the recorded default branch is not `main`, surface that as repository state and ask whether to keep or rename it without implying it is wrong.
  - If renaming, update local clones, open PR bases, branch protection or rulesets, documentation, and CI references.
  - Docs: [Changing the default branch](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-branches-in-your-repository/changing-the-default-branch). If this link breaks, search `change default branch GitHub repository` on `docs.github.com`.
  - Evidence: `[date, actor, old branch, new branch, connector result, or maintainer note]`
- [ ] Repository ruleset or branch-protection decision for the default branch: `[create ruleset, use classic branch protection, leave unchanged, or defer]`
  - UI path: open **Settings** > **Rules** > **Rulesets**, then create or review rules for branch names such as `main` or the recorded default branch.
  - Review required status checks, pull request review requirements, force-push restrictions, deletion restrictions, bypass roles, and enforcement mode.
  - Docs: [Creating rulesets for a repository](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/creating-rulesets-for-a-repository). If this link breaks, search `create repository ruleset GitHub` on `docs.github.com`.
  - Evidence: `[date, actor, ruleset name/link, connector result, or maintainer note]`

## Maintainer Policy Decisions

- [ ] Code of Conduct reporting contact method: `[explicit contact email/address, repository-maintainer profile contact, another maintainer-approved contact path, or intentionally deferred (dependent file status recorded)]`
- [ ] Security vulnerability reporting channel: `[private vulnerability reporting, monitored email, both, or intentionally deferred (dependent file status recorded)]`
- [ ] CODEOWNERS owner/team identity: `[@user or @org/team]`
- [ ] Label-dependent issue-template behavior: `[use template labels, choose alternate labels, remove label metadata, or intentionally deferred (dependent file status recorded)]`
- [ ] Adoption mode for protected and template-derived governance, community, process, workflow, and collaboration files: `minimal-preservation` by default; list any specific `tailored` opt-ins.
- [ ] GHES host override: `[none or github.company.com]`

## Protected-File Adoption Decisions

- [ ] Protected instruction files identified before editing: `.github/copilot-instructions.md`, `.github/instructions/*.instructions.md`, `.cursor/rules/*.mdc`, `.hermes.md`, `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md`.
- [ ] Protected-file edits authorized by maintainer: `[none, path-scoped authorization, or deferred]`
- [ ] Protected-file removals authorized by maintainer: `[none, path-scoped authorization, or deferred]`
- [ ] `.template-sync/marker.yml` protected-file decisions updated if template sync support is retained.

## Unresolved Settings

Tag each unresolved item with exactly one deferral state:

- `not yet asked`: the concrete owner question is identified but has not been asked.
- `asked and deferred`: the owner was asked and intentionally deferred the answer; dependent-file status is recorded.
- `unavailable through current safe tooling / manual review required`: the answer could not be determined through current safe tooling and requires owner or manual reviewer action.

- [ ] Items that must be completed later:
  - Question: `[concrete owner question]`; state: `[not yet asked, asked and deferred, or unavailable through current safe tooling / manual review required]`; owner: `[person/team]`; target date or trigger: `[date/event]`; dependency: `[file, workflow, or GitHub setting]`; dependent-file status: `[not finalized, blocked, placeholder removed, local default withheld, or other concrete status]`
- [ ] Dependent files that must not be considered finalized until the unresolved items are complete:
  - `[path]` depends on `[concrete owner question]`; state: `[same deferral state used above]`; status: `[dependent-file status]`

## Resolution Evidence

- [ ] Every unresolved dependent-file item was recorded only after the concrete owner question and dependent file/status impact were identified.
- [ ] Dependent files are finalized only after their policy questions are resolved, or after the owner intentionally chooses `asked and deferred` and the dependent-file status avoids placeholders and misleading defaults.
- [ ] No generated or adopted file ships unresolved placeholders or misleading policy defaults.
- [ ] Evidence captured for every resolved GitHub setting or policy decision: `[commit, PR, screenshot/link, connector result, API response note, or maintainer note]`
- [ ] Deferred items copied into the adoption PR description, sync summary, issue, or other maintainer-owned follow-up with their deferral state.
```

Downstream work may assume a checklist item is complete only after it is recorded as resolved, or after the owner intentionally chooses `asked and deferred` with dependent-file status, in `_TODO-repo-init.md`, `.template-sync/marker.yml`, or the equivalent committed adoption note named by the adoption procedure. Items tagged `not yet asked` or `unavailable through current safe tooling / manual review required` keep dependent files unfinalized.

---

## Initial Placeholder Replacement

This template uses placeholder values that you **must** replace with your actual repository information. If you keep `.github/workflows/check-placeholders.yml` (an optional adoption step — see *Verify Placeholder Check Workflow* below), CI will fail until you complete these replacements; if you do not adopt that workflow or you remove it after initial setup, no CI guardrail catches a missed substitution and you must verify the replacements manually.

### Files That Need Placeholders Replaced

| File | Placeholders to Replace |
| --- | --- |
| `.github/ISSUE_TEMPLATE/config.yml` | `OWNER/REPO` (appears in URLs twice) |
| `.github/ISSUE_TEMPLATE/bug_report.yml` | `OWNER/REPO` (appears in security-notice URLs) |
| `.github/pull_request_template.md` | `OWNER/REPO` (appears in the contributing-guidelines link) |
| `.github/CODEOWNERS` | `@OWNER` (appears five times) |
| `CODE_OF_CONDUCT.md` | `[INSERT CONTACT METHOD]` (enforcement contact for code of conduct violations) |
| `CONTRIBUTING.md` | `OWNER/REPO` (appears in clone URL and issues URL) |
| `LICENSE` | `Frank Lesniak` (copyright holder name — replace with your name or organization) |
| `SECURITY.md` | `[security contact email]` and the security-contact `TODO: Replace` marker when using contact-based reporting, plus the `OWNER/REPO` placeholder in the direct private-reporting URL when using GitHub private vulnerability reporting |
| `.vscode/settings.json` | `window.title` value (replace with your repository name) |

### What the Placeholders Mean

- **`OWNER`:** Your GitHub username or organization name (e.g., `franklesniak`)
- **`REPO`:** Your repository name (e.g., `my-new-project`)
- **`OWNER/REPO`:** Combined format used in GitHub URLs (e.g., `franklesniak/my-new-project`)
- **`@OWNER`:** GitHub username with @ prefix for CODEOWNERS file (e.g., `@franklesniak`)
- **`Frank Lesniak`:** The template author's name in the LICENSE file. Replace with your name or organization name (the copyright holder for your project).
- **`[INSERT CONTACT METHOD]`:** A method for reporting code of conduct violations (e.g., an email address, a form URL, or instructions to contact maintainers). This should be actively monitored and capable of receiving sensitive reports.
- **`[security contact email]`:** A monitored security contact method used when your selected security-reporting mode includes contact-based reporting
- **`window.title` in `.vscode/settings.json`:** The VS Code window title that appears in the title bar when working in this repository. Replace the instruction text with your repository name for easy identification.

> **GHES adopters:** The absolute URLs in `.github/ISSUE_TEMPLATE/config.yml`, `.github/ISSUE_TEMPLATE/bug_report.yml`, `.github/pull_request_template.md`, `CONTRIBUTING.md`, and `SECURITY.md` are all `https://github.com/OWNER/REPO`-prefixed (variants include `https://github.com/OWNER/REPO/blob/HEAD/<path>` for file targets, `https://github.com/OWNER/REPO/security` and `https://github.com/OWNER/REPO/issues` for non-file repo targets, `https://github.com/OWNER/REPO/security/advisories/new` for the private vulnerability reporting form in `bug_report.yml` and `SECURITY.md`, and `https://github.com/OWNER/REPO.git` for the clone URL in `CONTRIBUTING.md`). The `github.com` host is the assumed default and is **not** validated by `.github/workflows/check-placeholders.yml`. If your repository is hosted on GitHub Enterprise Server, you **MUST** replace `github.com` with your GHES host (e.g., `github.company.com`) in all five files in addition to substituting `OWNER/REPO`; otherwise the clone, issues, security, and contributing-guidelines links will point off-instance to GitHub.com. The recommended helper below supports this with `--github-host` and limits host substitution to approved template URL contexts.

### Option A: Recommended Placeholder Helper

Prefer the repository helper over ad hoc global find/replace. It replaces only the exact placeholder tokens and approved `https://github.com/OWNER/REPO...` URL shapes defined in `.github/scripts/replace-template-placeholders.py`, then scans for unresolved placeholders and common corruption patterns such as mutated `REPORT`, `REPOSITORY`, and `REPOSITORIES` text.

Choose a security reporting mode before running the helper:

- `both` keeps GitHub private vulnerability reporting guidance and a contact method. This is also the backward-compatible behavior when `--security-reporting-mode` is omitted and `--security-contact` is supplied.
- `contact-only` keeps the contact method and removes GitHub private vulnerability reporting guidance.
- `github-private-only` keeps GitHub private vulnerability reporting guidance and removes the security contact section. If you keep `CODE_OF_CONDUCT.md`, still pass an explicit `--conduct-contact`.

For values that begin with `@`, contain literal `$`, spaces, commas, or need whole-sentence contact prose, prefer an args file. JSON args files are always supported; `.yaml` and `.yml` args files are supported when the retained YAML parser is available. If YAML support is unavailable, convert the args file to JSON or enable the retained YAML support.

Create an args file and run the helper from the repository root after replacing the example values.

**Windows (PowerShell):**

```powershell
@'
{
  "repository": "your-username/your-repo-name",
  "security_reporting_mode": "both",
  "security_contact": "security@example.com",
  "conduct_contact_sentence": "Report possible Code of Conduct violations using the private conduct form at https://example.com/conduct.",
  "codeowners_owner": "@your-org/maintainers",
  "vscode_title": "your-repo-name",
  "package_name": "your-repo-name",
  "package_description": "Your project description with literal $ text, spaces, and commas.",
  "package_author": "Your Name or Organization",
  "package_keywords": ["your-project", "docs"]
}
'@ | Set-Content -Encoding UTF8 .\adoption-identity.json

python .github/scripts/replace-template-placeholders.py replace `
    --args-file .\adoption-identity.json
```

**macOS/Linux/FreeBSD (Bash):**

```bash
cat > adoption-identity.json <<'JSON'
{
  "repository": "your-username/your-repo-name",
  "security_reporting_mode": "both",
  "security_contact": "security@example.com",
  "conduct_contact_sentence": "Report possible Code of Conduct violations using the private conduct form at https://example.com/conduct.",
  "codeowners_owner": "@your-org/maintainers",
  "vscode_title": "your-repo-name",
  "package_name": "your-repo-name",
  "package_description": "Your project description with literal $ text, spaces, and commas.",
  "package_author": "Your Name or Organization",
  "package_keywords": ["your-project", "docs"]
}
JSON

python3 .github/scripts/replace-template-placeholders.py replace \
    --args-file ./adoption-identity.json
```

For GitHub Enterprise Server, add `"github_host": "github.company.com"` to the args file. The helper changes the host only for approved template URL placeholders; it does not rewrite unrelated `github.com` links.

For simple values, direct flags remain supported. CLI flags take precedence over values from `--args-file`, so you can override one field without editing the file.

The helper does not edit `LICENSE`, because `Frank Lesniak` is not a pattern-based placeholder. Update that file manually with your name or organization name.

### Option B: Exact Find and Replace Fallbacks

The platform-specific commands below remain available as visible fallbacks. Keep them scoped to the exact placeholders shown here; do not run a broad replacement for `REPO`, because that can corrupt normal words such as `REPORT`, `REPOSITORY`, and `REPOSITORIES`. For GHES host substitution, prefer Option A with `--github-host`. If you use Option B on GHES, run the *GHES Host Substitution (GHES Adopters Only)* commands below after the platform-specific commands; they rewrite only the approved `https://github.com/OWNER/REPO...` URLs the template emits, never every `github.com` occurrence in a file. Option B's commands assume contact-based security reporting and use a single contact value for both the `[INSERT CONTACT METHOD]` Code of Conduct placeholder and the `[security contact email]` placeholder; if you want `github-private-only` or a distinct Code of Conduct contact, prefer Option A.

#### Windows (PowerShell)

Open PowerShell in your repository directory and run these commands. Replace the placeholder values with your actual information:

```powershell
# Define your values (replace these with your actual username/org, repo name, and email)
$Owner = "your-username"
$Repo = "your-repo-name"
$SecurityEmail = "security@example.com"

# Replace OWNER/REPO in config.yml
(Get-Content ".github/ISSUE_TEMPLATE/config.yml" -Raw -Encoding UTF8).Replace('OWNER/REPO', "$Owner/$Repo") | Set-Content ".github/ISSUE_TEMPLATE/config.yml" -Encoding UTF8

# Replace OWNER/REPO in bug_report.yml
(Get-Content ".github/ISSUE_TEMPLATE/bug_report.yml" -Raw -Encoding UTF8).Replace('OWNER/REPO', "$Owner/$Repo") | Set-Content ".github/ISSUE_TEMPLATE/bug_report.yml" -Encoding UTF8

# Replace OWNER/REPO in pull_request_template.md
(Get-Content ".github/pull_request_template.md" -Raw -Encoding UTF8).Replace('OWNER/REPO', "$Owner/$Repo") | Set-Content ".github/pull_request_template.md" -Encoding UTF8

# Replace OWNER/REPO in CONTRIBUTING.md
(Get-Content "CONTRIBUTING.md" -Raw -Encoding UTF8).Replace('OWNER/REPO', "$Owner/$Repo") | Set-Content "CONTRIBUTING.md" -Encoding UTF8

# Replace OWNER/REPO in SECURITY.md (the direct private-reporting URL `https://github.com/OWNER/REPO/security/advisories/new`)
(Get-Content "SECURITY.md" -Raw -Encoding UTF8).Replace('OWNER/REPO', "$Owner/$Repo") | Set-Content "SECURITY.md" -Encoding UTF8

# Replace @OWNER in CODEOWNERS (note the @ prefix)
(Get-Content ".github/CODEOWNERS" -Raw -Encoding UTF8).Replace('@OWNER', "@$Owner") | Set-Content ".github/CODEOWNERS" -Encoding UTF8

# Replace contact method placeholder in CODE_OF_CONDUCT.md (uses the security contact; change if different contact preferred)
(Get-Content "CODE_OF_CONDUCT.md" -Raw -Encoding UTF8).Replace('[INSERT CONTACT METHOD]', $SecurityEmail) | Set-Content "CODE_OF_CONDUCT.md" -Encoding UTF8

# Replace security contact placeholder in SECURITY.md
(Get-Content "SECURITY.md" -Raw -Encoding UTF8).Replace('[security contact email]', $SecurityEmail) | Set-Content "SECURITY.md" -Encoding UTF8

# Clear the security-contact TODO marker in SECURITY.md (replaces the whole HTML comment line so SECURITY.md text stays accurate)
(Get-Content "SECURITY.md" -Raw -Encoding UTF8).Replace('<!-- TODO: Replace with your security contact email -->', '<!-- Security contact configured -->') | Set-Content "SECURITY.md" -Encoding UTF8

# Replace window.title placeholder in VS Code settings
(Get-Content ".vscode\settings.json" -Raw -Encoding UTF8).Replace('Go to .vscode/settings.json and make this the name of the repo', $Repo) | Set-Content ".vscode\settings.json" -Encoding UTF8

```

#### macOS/Linux/FreeBSD (Bash)

Open Terminal in your repository directory and run the commands below. Replace the placeholder values with your actual information.

> **Note:** The `LICENSE` file contains the template author's name (`Frank Lesniak`) in the copyright notice. This is not a pattern-based placeholder, so you'll need to manually update it with your own name or organization. Optionally update the copyright year to the current year or your project's start year.

**Step 1: Define your values** (all platforms):

```bash
# Define your values (replace these with your actual username/org, repo name, and email)
OWNER="your-username"
REPO="your-repo-name"
SECURITY_EMAIL="security@example.com"
```

**Step 2: Run the replacement commands** for your platform:

##### Linux (GNU sed)

```bash
# Replace OWNER/REPO in config.yml
sed -i "s|OWNER/REPO|$OWNER/$REPO|g" .github/ISSUE_TEMPLATE/config.yml

# Replace OWNER/REPO in bug_report.yml
sed -i "s|OWNER/REPO|$OWNER/$REPO|g" .github/ISSUE_TEMPLATE/bug_report.yml

# Replace OWNER/REPO in pull_request_template.md
sed -i "s|OWNER/REPO|$OWNER/$REPO|g" .github/pull_request_template.md

# Replace OWNER/REPO in CONTRIBUTING.md
sed -i "s|OWNER/REPO|$OWNER/$REPO|g" CONTRIBUTING.md

# Replace OWNER/REPO in SECURITY.md (the direct private-reporting URL https://github.com/OWNER/REPO/security/advisories/new)
sed -i "s|OWNER/REPO|$OWNER/$REPO|g" SECURITY.md

# Replace @OWNER in CODEOWNERS
sed -i "s|@OWNER|@$OWNER|g" .github/CODEOWNERS

# Replace contact method placeholder in CODE_OF_CONDUCT.md
sed -i "s|\[INSERT CONTACT METHOD\]|$SECURITY_EMAIL|g" CODE_OF_CONDUCT.md

# Replace security contact placeholder in SECURITY.md
sed -i "s|\[security contact email\]|$SECURITY_EMAIL|g" SECURITY.md

# Clear the security-contact TODO marker in SECURITY.md (replaces the whole HTML comment line so SECURITY.md text stays accurate)
sed -i "s|<!-- TODO: Replace with your security contact email -->|<!-- Security contact configured -->|g" SECURITY.md

# Replace window.title placeholder in VS Code settings
sed -i 's|Go to \.vscode/settings\.json and make this the name of the repo|'"$REPO"'|g' .vscode/settings.json

```

##### macOS / FreeBSD (BSD sed)

```bash
# Replace OWNER/REPO in config.yml
sed -i '' "s|OWNER/REPO|$OWNER/$REPO|g" .github/ISSUE_TEMPLATE/config.yml

# Replace OWNER/REPO in bug_report.yml
sed -i '' "s|OWNER/REPO|$OWNER/$REPO|g" .github/ISSUE_TEMPLATE/bug_report.yml

# Replace OWNER/REPO in pull_request_template.md
sed -i '' "s|OWNER/REPO|$OWNER/$REPO|g" .github/pull_request_template.md

# Replace OWNER/REPO in CONTRIBUTING.md
sed -i '' "s|OWNER/REPO|$OWNER/$REPO|g" CONTRIBUTING.md

# Replace OWNER/REPO in SECURITY.md (the direct private-reporting URL https://github.com/OWNER/REPO/security/advisories/new)
sed -i '' "s|OWNER/REPO|$OWNER/$REPO|g" SECURITY.md

# Replace @OWNER in CODEOWNERS
sed -i '' "s|@OWNER|@$OWNER|g" .github/CODEOWNERS

# Replace contact method placeholder in CODE_OF_CONDUCT.md
sed -i '' "s|\[INSERT CONTACT METHOD\]|$SECURITY_EMAIL|g" CODE_OF_CONDUCT.md

# Replace security contact placeholder in SECURITY.md
sed -i '' "s|\[security contact email\]|$SECURITY_EMAIL|g" SECURITY.md

# Clear the security-contact TODO marker in SECURITY.md (replaces the whole HTML comment line so SECURITY.md text stays accurate)
sed -i '' "s|<!-- TODO: Replace with your security contact email -->|<!-- Security contact configured -->|g" SECURITY.md

# Replace window.title placeholder in VS Code settings
sed -i '' 's|Go to \.vscode/settings\.json and make this the name of the repo|'"$REPO"'|g' .vscode/settings.json

```

##### Windows (Git Bash or WSL)

If using **Git Bash**, use the Linux (GNU sed) commands above. If using **WSL (Windows Subsystem for Linux)**, use the Linux commands. Alternatively, use the PowerShell commands in the previous section.

> **Note on special characters:** If your email or contact method contains special `sed` characters (`&`, `\`, or `|`), escape them with a backslash or use the PowerShell commands instead, which handle special characters more reliably.

#### GHES Host Substitution (GHES Adopters Only)

If your repository is hosted on GitHub Enterprise Server, run **one additional command set** after the platform commands above so the approved template URLs point to your GHES host. The commands below rewrite only the `https://github.com/OWNER/REPO...` URLs the template emits — they leave unrelated `github.com` links (for example, `https://github.com/actions/checkout` in workflow files) untouched. They assume the variables defined in the platform commands above (`$Owner`/`$Repo` for PowerShell or `$OWNER`/`$REPO` for Bash) are still in scope; if you started a new shell, redefine them first.

**Windows (PowerShell):**

```powershell
$GhesHost = "github.company.com"  # replace with your GHES host
$GhubPrefix = "https://github.com/$Owner/$Repo"
$GhesPrefix = "https://$GhesHost/$Owner/$Repo"

foreach ($File in @(
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/pull_request_template.md",
    "CONTRIBUTING.md",
    "SECURITY.md"
)) {
    (Get-Content $File -Raw -Encoding UTF8).Replace($GhubPrefix, $GhesPrefix) | Set-Content $File -Encoding UTF8
}
```

**Linux (GNU sed):**

```bash
GHES_HOST="github.company.com"  # replace with your GHES host
for file in .github/ISSUE_TEMPLATE/config.yml .github/ISSUE_TEMPLATE/bug_report.yml .github/pull_request_template.md CONTRIBUTING.md SECURITY.md; do
    sed -i "s|https://github.com/${OWNER}/${REPO}|https://${GHES_HOST}/${OWNER}/${REPO}|g" "$file"
done
```

**macOS / FreeBSD (BSD sed):**

```bash
GHES_HOST="github.company.com"  # replace with your GHES host
for file in .github/ISSUE_TEMPLATE/config.yml .github/ISSUE_TEMPLATE/bug_report.yml .github/pull_request_template.md CONTRIBUTING.md SECURITY.md; do
    sed -i '' "s|https://github.com/${OWNER}/${REPO}|https://${GHES_HOST}/${OWNER}/${REPO}|g" "$file"
done
```

### Option C: Manual Replacement

If you prefer, you can open each file in a text editor and manually find and replace the placeholders:

> **GHES adopters:** In addition to the `OWNER/REPO` substitutions below, also replace `github.com` with your GHES host (e.g., `github.company.com`) in items 1, 2, 3, 6, and 7. The host substitution is not validated by `.github/workflows/check-placeholders.yml`, so it MUST be done manually.

1. **`.github/ISSUE_TEMPLATE/config.yml`:**
   - Find: `OWNER/REPO`
   - Replace with: `your-username/your-repo-name` (appears in two URLs)
   - **GHES only:** also replace `github.com` with your GHES host (in the same two URLs)

2. **`.github/ISSUE_TEMPLATE/bug_report.yml`:**
   - Find: `OWNER/REPO`
   - Replace with: `your-username/your-repo-name` (appears in the security-notice URLs selected by your security reporting mode)
   - **GHES only:** also replace `github.com` with your GHES host (in the same security-notice URLs)

3. **`.github/pull_request_template.md`:**
   - Find: `OWNER/REPO`
   - Replace with: `your-username/your-repo-name` (the live substitution
     target is the contributing-guidelines link in the file body; the file
     may also contain plain-text `OWNER/REPO` references inside the
     top-of-file HTML comment block, which you can replace now or skip
     because the entire HTML comment block is deleted in the
     *Delete Template Comment* step under *Customizing the Pull Request
     Template* later in this guide)
   - **GHES only:** also replace `github.com` with your GHES host (in the same link)

4. **`.github/CODEOWNERS`:**
   - Find: `@OWNER`
   - Replace with: `@your-username` (appears five times)

5. **`CODE_OF_CONDUCT.md`:**
   - Find: `[INSERT CONTACT METHOD]`
   - Replace with: your contact method for code of conduct reports (e.g., email address)

6. **`CONTRIBUTING.md`:**
   - Find: `OWNER/REPO`
   - Replace with: `your-username/your-repo-name` (appears in clone URL and issues link)
   - **GHES only:** also replace `github.com` with your GHES host (in the same clone URL and issues link)

7. **`SECURITY.md`:**
   - Find: `[security contact email]`
   - Replace with: your actual security contact email address
   - Find: `<!-- TODO: Replace with your security contact email -->` (the whole HTML comment line)
   - Replace with: `<!-- Security contact configured -->`
   - Find: `OWNER/REPO` (appears in the direct private-reporting URL `https://github.com/OWNER/REPO/security/advisories/new`)
   - Replace with: `your-username/your-repo-name`
   - **GHES only:** also replace `github.com` with your GHES host (in the same URL)

8. **`.vscode/settings.json`:**
   - Find: `Go to .vscode/settings.json and make this the name of the repo`
   - Replace with: your repository name (e.g., `my-awesome-project`)

9. **`LICENSE`:**
   - Find: `Frank Lesniak`
   - Replace with: your name or organization name (the copyright holder)
   - Optionally update the copyright year to the current year or your project's start year

### Understanding the CODEOWNERS File

The `.github/CODEOWNERS` file defines who is automatically requested to review pull requests. The `@OWNER` placeholder should be replaced with:

- Your GitHub username (e.g., `@octocat`) for personal repositories
- A team reference (e.g., `@my-org/maintainers`) for organization repositories

For example, if your GitHub username is `janedoe`, replace `@OWNER` with `@janedoe`.

### Understanding Security Reporting Modes

The helper's `--security-reporting-mode` option controls how `SECURITY.md`, `.github/ISSUE_TEMPLATE/config.yml`, and `.github/ISSUE_TEMPLATE/bug_report.yml` are rendered:

- `both`: keeps GitHub private vulnerability reporting guidance and a monitored security contact method.
- `contact-only`: keeps the monitored security contact method and removes GitHub private vulnerability reporting guidance.
- `github-private-only`: keeps GitHub private vulnerability reporting guidance and removes the security contact section.

Use `--security-contact` only for `both` or `contact-only`. The contact value should be actively monitored, able to receive sensitive security reports, and must not be a `users.noreply.github.com` address. Before relying on `github-private-only`, enable private vulnerability reporting in GitHub repository settings.

---

## Creating Optional Labels

The issue templates include labels that should exist in your repository.

**Default GitHub labels (already exist in new repositories):**

- `bug` — Used by bug_report.yml
- `enhancement` — Used by feature_request.yml
- `documentation` — Used by documentation_issue.yml

**Optional label to create:**

The templates include a commented-out `triage` label. To use it:

**Using GitHub CLI (Windows PowerShell / macOS / Linux):**

```bash
gh label create triage --description "Needs triage" --color "d4c5f9"
```

**Or via GitHub web UI:**

1. Go to your repository
2. Click **Issues** or **Pull requests**
3. Above the list, click **Labels**
4. Click **New label**
5. Under "Label name", type `triage`
6. Under "Description", type `Needs triage`
7. Edit the color hexadecimal number to `d4c5f9` (light purple)
8. Click **Create label**

After creating the label, uncomment the `- triage` line in each issue template (`bug_report.yml`, `feature_request.yml`, and `documentation_issue.yml`).

---

## Installing and Configuring Pre-commit

### Understanding Pre-commit

[Pre-commit](https://pre-commit.com/) is a framework for managing git hooks. It automatically runs code quality checks (formatting, linting, validation) before each commit, catching issues early and ensuring consistent code quality across your team.

**Why pre-commit is not a project dependency:**

- Pre-commit is a **development tool**, not a runtime or test dependency
- It manages its own isolated environments for each hook (e.g., Black, Ruff)
- Installing it globally or via `pipx` keeps your project dependencies clean
- This is standard practice in the Python community
- CI workflows install pre-commit separately

> **Why pipx is recommended:**
>
> When you install Python packages with CLI tools using `pip`, the executables are placed in a `Scripts` folder (Windows) or `bin` folder (macOS/Linux) that may not be in your system PATH. This can cause "command not found" errors.
>
> `pipx` addresses this by installing Python CLI tools in isolated environments and exposing their executables from a single, well-defined binary directory. To make that directory available on the command line, you must run `pipx ensurepath` once (and restart your shell); after that, new tools installed with `pipx` will typically be usable without additional PATH changes. This is the [official recommendation from the pre-commit project](https://pre-commit.com/#install).
>
> If the `pipx` command itself is not yet on your PATH (for example, just after installation on Windows), you can invoke it via the Python module instead, such as `python -m pipx ensurepath` on Windows or `python3 -m pipx ensurepath` on macOS/Linux/FreeBSD for the initial setup.
>
> If you prefer to use `pip`, you can invoke pre-commit as a Python module using `python -m pre_commit` (Windows) or `python3 -m pre_commit` (macOS/Linux/FreeBSD) instead of the `pre-commit` command directly.

### Installation - Windows

#### Option 1: Using pipx (recommended)

[pipx](https://pipx.pypa.io/) installs Python applications in isolated environments and, after you run `pipx ensurepath` once, adds the pipx binaries directory to your PATH so you can run installed tools from the command line. First install pipx if you don't have it:

```powershell
# First, upgrade pip to the latest version (recommended)
python -m pip install --upgrade pip

# Install pipx
python -m pip install pipx

# Configure PATH (use module invocation in case pipx isn't on PATH yet)
python -m pipx ensurepath
```

Then install pre-commit:

```powershell
# Use module invocation to ensure it works even if pipx isn't on PATH
python -m pipx install pre-commit
```

> **Note:** You need to restart your PowerShell window (or open a new one) before running `pre-commit` directly by name, because PATH changes only apply to new shells. Using `python -m pipx` avoids needing `pipx` on PATH and lets you install packages in the same session, but `pipx run pre-commit` runs from a temporary environment and should not be used for `pre-commit install` (it can create hooks that reference a non-existent interpreter).

#### Option 2: Using pip

Open PowerShell and run:

```powershell
# First, upgrade pip to the latest version (recommended)
python -m pip install --upgrade pip

# Then install pre-commit
python -m pip install pre-commit
```

> **Note:** When using pip, the `pre-commit` command may not be recognized because Python's `Scripts` folder is not always added to PATH. Use `python -m pre_commit` instead of `pre-commit` for all commands. For example, use `python -m pre_commit --version` to verify installation.
>
> **Troubleshooting:** If you see `pip: The term 'pip' is not recognized`, ensure you checked "Add Python to PATH" during Python installation. Using `python -m pip` instead of `pip` directly is more reliable on Windows.

#### Verifying installation

**If you installed with pipx:**

```powershell
pre-commit --version
```

> **Note:** If `pre-commit` is not found, you need to restart your PowerShell window so the PATH changes from `pipx ensurepath` take effect. Alternatively, you can verify pipx installed pre-commit by running `python -m pipx list` to see installed packages.

**If you installed with pip:**

```powershell
python -m pre_commit --version
```

You should see output like `pre-commit 4.0.1`.

### Installation - macOS/Linux/FreeBSD

#### Option 1: Using pipx (recommended)

[pipx](https://pipx.pypa.io/) installs Python applications in isolated environments and, after you run `pipx ensurepath` once, adds the pipx binaries directory to your PATH so you can run installed tools from the command line.

> **Important (PEP 668 systems):** On newer Linux distributions (Ubuntu 23.04+, Fedora 38+) and some macOS configurations, `python3 -m pip install` commands fail with an `externally-managed-environment` error. If you're on one of these systems, **skip the pip commands below** and install pipx via your OS package manager instead:
>
> - Debian / Ubuntu: `sudo apt install pipx && pipx ensurepath`
> - Fedora: `sudo dnf install pipx && pipx ensurepath`
> - macOS (Homebrew): `brew install pipx && pipx ensurepath`
>
> After running `pipx ensurepath`, restart your terminal, then proceed to the "Then install pre-commit" step below.

If pip works on your system, first install pipx:

```bash
# First, upgrade pip to the latest version (recommended)
python3 -m pip install --upgrade pip

# Install pipx
python3 -m pip install pipx

# Configure PATH (use module invocation in case pipx isn't on PATH yet)
python3 -m pipx ensurepath
```

Then install pre-commit:

```bash
pipx install pre-commit
```

> **Note:** If you installed pipx via an OS package manager (Homebrew, apt, dnf), use `pipx install pre-commit` as shown above. If you installed pipx via pip and pipx isn't on your PATH yet, you can use `python3 -m pipx install pre-commit` instead. After installing pre-commit, you'll need to restart your terminal before running `pre-commit` directly by name. Do not use `pipx run pre-commit install`—it runs from a temporary environment and can create hooks referencing a non-existent interpreter.

#### Option 2: Using Homebrew (macOS only)

```bash
brew install pre-commit
```

#### Option 3: Using pip

> **Important (PEP 668 systems):** On newer Linux distributions (Ubuntu 23.04+, Fedora 38+) and some macOS configurations, `python3 -m pip install` commands fail with an `externally-managed-environment` error. If you're on one of these systems, **do not use pip**—use Option 1 (pipx via OS package manager) instead:
>
> - Debian / Ubuntu: `sudo apt install pipx && pipx ensurepath`
> - Fedora: `sudo dnf install pipx && pipx ensurepath`
> - macOS (Homebrew): `brew install pipx && pipx ensurepath`
>
> After running `pipx ensurepath`, restart your terminal, then run `pipx install pre-commit`.

If pip works on your system:

```bash
# First, upgrade pip to the latest version (recommended)
python3 -m pip install --upgrade pip

# Then install pre-commit
python3 -m pip install pre-commit
```

> **Note:** When using pip, the `pre-commit` command may not be recognized if Python's `bin` folder is not in your PATH. Use `python3 -m pre_commit` instead of `pre-commit` for all commands. For example, use `python3 -m pre_commit --version` to verify installation.

#### Verifying installation

**If you installed with pipx:**

```bash
pre-commit --version
```

> **Note:** If `pre-commit` is not found, you need to restart your terminal so the PATH changes from `pipx ensurepath` take effect. Alternatively, you can verify pipx installed pre-commit by running `python3 -m pipx list` to see installed packages.

**If you installed with Homebrew:**

```bash
pre-commit --version
```

> **Note:** If `pre-commit` is not found, ensure Homebrew's `bin` directory (typically `/opt/homebrew/bin` on Apple Silicon or `/usr/local/bin` on Intel Macs) is in your PATH. You can add it by running `eval "$(/opt/homebrew/bin/brew shellenv)"` (Apple Silicon) or `eval "$(/usr/local/bin/brew shellenv)"` (Intel) in your shell configuration file.

**If you installed with pip:**

```bash
python3 -m pre_commit --version
```

You should see output like `pre-commit 4.0.1`.

### Activating Hooks in Your Repository

Navigate to your repository directory and run:

**Windows (PowerShell):**

**If you installed with pipx:**

```powershell
cd C:\path\to\your-repo-name
pre-commit install
```

> **Note:** If `pre-commit` is not found, run `python -m pipx ensurepath` and restart your PowerShell window. Do not use `pipx run pre-commit install` because it runs from a temporary environment and can create hooks that reference a non-existent interpreter.

**If you installed with pip:**

```powershell
cd C:\path\to\your-repo-name
python -m pre_commit install
```

**macOS/Linux/FreeBSD:**

**If you installed with pipx:**

```bash
cd ~/projects/your-repo-name
pre-commit install
```

> **Note:** If `pre-commit` is not found, run `python3 -m pipx ensurepath` (or `pipx ensurepath` if `pipx` is already on your PATH) and restart your terminal. Do not use `pipx run pre-commit install` because it runs from a temporary environment and can create hooks that reference a non-existent interpreter.

**If you installed with Homebrew:**

```bash
cd ~/projects/your-repo-name
pre-commit install
```

> **Note:** If `pre-commit` is not found, ensure Homebrew's `bin` directory is in your PATH (see verification section above).

**If you installed with pip:**

```bash
cd ~/projects/your-repo-name
python3 -m pre_commit install
```

This command modifies `.git/hooks/pre-commit` to run pre-commit automatically before each commit. You only need to run this once per repository clone.

**What happens:** Git will now automatically run all configured hooks every time you run `git commit`. If any hook fails, the commit is blocked until you fix the issues.

### Running Pre-commit Manually

Run pre-commit on all files:

**If you installed with pipx:**

```bash
pre-commit run --all-files
```

> **Note:** If `pre-commit` is not found, you may need to add the pipx binary location to your PATH. On **Windows**, run `python -m pipx ensurepath`. On **macOS/Linux/FreeBSD**, run `python3 -m pipx ensurepath`. In both cases, you can alternatively run `pipx ensurepath` if `pipx` itself is already on your PATH, then restart your terminal. `pipx run pre-commit` can be used for one-off commands but runs from a temporary environment (slower and doesn't validate your installed version).

**If you installed with Homebrew:**

```bash
pre-commit run --all-files
```

**If you installed with pip (Windows):**

```powershell
python -m pre_commit run --all-files
```

**If you installed with pip (macOS/Linux/FreeBSD):**

```bash
python3 -m pre_commit run --all-files
```

**First run behavior:** The first time you run pre-commit, it downloads and installs the hook environments (e.g., Black, Ruff). This may take a minute or two. Subsequent runs are much faster.

**Interpreting output:**

```text
Trim Trailing Whitespace......................................Passed
Fix End of Files..............................................Passed
Check Yaml....................................................Passed
Check for added large files...................................Passed
black.........................................................Passed
ruff..........................................................Passed
markdownlint-cli2.............................................Passed
```

- **Passed:** The check found no issues
- **Failed:** The check found issues (some hooks auto-fix, others require manual fixes)
- **Skipped:** The hook didn't apply to any files in this commit

> **Tip:** If hooks auto-fix files (like trailing whitespace or formatting), review the changes and include them in your commit. Pre-commit will run again and should pass.

---

## Language-Specific Customization

This template includes support for Python, PowerShell, Terraform, JSON/JSONC, YAML, and Markdown/documentation. You should remove support for languages or formats you don't need and configure the ones you do use.

### Decision Point: Which Languages Do You Need?

Review your project requirements and decide which languages you'll be using:

- **Python:** Server-side code, scripts, data processing, APIs
- **PowerShell:** Windows automation, cross-platform scripting, DevOps tasks
- **Terraform:** Infrastructure as Code, modules, cloud resources
- **JSON/JSONC:** Machine-readable configuration, schemas, fixtures, tool settings
- **YAML:** Human-authored configuration, GitHub Actions workflows, pre-commit configuration
- **Markdown:** Documentation (always needed)

> **YAML adoption warning:** Keeping `.github/workflows/*.yml` while deleting the YAML instruction, linting, and validation stack is contradictory. GitHub Actions workflows are YAML files. If you remove YAML support, flag the contradiction during adoption and either keep the YAML stack or remove/replace every YAML-based workflow and configuration file.
>
> **Python runtime note:** Removing Python as project source code does not always remove Python as a development-tool runtime. Keep Python available anywhere you run `pre-commit`, `check-jsonschema`, `check-metaschema`, or repo-local Python hooks, even if you delete `src/`, Python tests, and `.github/workflows/python-ci.yml`.

### Language and Format Checklist

Use this checklist before the detailed Python and PowerShell sections below.

#### Python

Set up Python if you use it:

- Read `.github/instructions/python.instructions.md` before editing `*.py` files.
- Keep `.github/workflows/python-ci.yml` for Python type checking (mypy) and tests (pytest). Aggregate pre-commit enforcement lives in `.github/workflows/precommit-ci.yml`, which is baseline-scoped and stays regardless of Python adoption.
- Keep `src/`, `tests/test_example.py`, `tests/__init__.py`, `pyproject.toml`, and `templates/python/` until you replace the example package and tests with your project code.

Remove Python if you do not use it:

- Delete `src/`.
- Delete `tests/test_example.py` and `tests/__init__.py`.
- Delete `pyproject.toml` if no other tooling in your project depends on it.
- Delete `.github/workflows/python-ci.yml`.
- Delete `.github/instructions/python.instructions.md`.
- Delete `templates/python/`.
- Keep `.github/workflows/precommit-ci.yml`. It is baseline-scoped and runs `pre-commit run --all-files` for repository hygiene; Python is still installed there only as the runtime for `pre-commit` itself and Python-based hooks (e.g., `check-jsonschema`).
- Remove the `# template-sync: begin python-only` … `# template-sync: end python-only` block from `.pre-commit-config.yaml` (which contains the `black` and `ruff-check` hooks). The template-sync framework strips this block automatically when the `python` module is excluded; remove it manually if you are not using template sync.
- Remove the `pip` ecosystem from `.github/dependabot.yml` if `pyproject.toml` is gone and no Python dependency manifest remains.
- Remove Python validation references from `.github/copilot-instructions.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `README.md`, `CONTRIBUTING.md`, and the PR template after the protected-file cleanup step below is authorized.
- Keep Python installed for development tooling if you still run `pre-commit`, `check-jsonschema`, `check-metaschema`, or repo-local hooks.

#### PowerShell

Set up PowerShell if you use it:

- Read `.github/instructions/powershell.instructions.md` before editing `*.ps1` files.
- Keep `.github/workflows/powershell-ci.yml` for PSScriptAnalyzer and Pester CI.
- Keep `.github/linting/PSScriptAnalyzerSettings.psd1`, `tests/PowerShell/`, and `templates/powershell/` if you want the shipped linting and test examples.

Remove PowerShell if you do not use it:

- Delete `.github/workflows/powershell-ci.yml`.
- Delete `.github/instructions/powershell.instructions.md`.
- Delete `.github/linting/`.
- Delete `tests/PowerShell/`.
- Delete `templates/powershell/`.
- Remove the "PowerShell-Specific (if applicable)" checklist from `.github/pull_request_template.md`.
- Remove PowerShell validation references from `.github/copilot-instructions.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `README.md`, and `CONTRIBUTING.md` after the protected-file cleanup step below is authorized.

#### Terraform

Set up Terraform if you use it:

- Read `.github/instructions/terraform.instructions.md` before editing Terraform files.
- Keep `.github/workflows/terraform-ci.yml` for Terraform format, validation, linting, tests, and security checks.
- Keep `.tflint.hcl` and `templates/terraform/` until you replace the starter examples with project-specific Terraform tests or modules.
- Keep the `terraform-fmt`, `terraform-validate`, and `terraform-tflint` repo-local Python hooks in `.pre-commit-config.yaml`.
- Install HashiCorp Terraform (`terraform`) and TFLint (`tflint`) on developer machines and CI runners that execute Terraform validation.

Remove Terraform if you do not use it:

- Delete `.github/workflows/terraform-ci.yml`.
- Delete `.github/instructions/terraform.instructions.md`.
- Delete `.tflint.hcl`.
- Delete `templates/terraform/`.
- Remove the `terraform-fmt`, `terraform-validate`, and `terraform-tflint` hooks from `.pre-commit-config.yaml`.
- Delete `.github/scripts/terraform_hooks.py` if no remaining pre-commit hook or workflow uses it.
- Remove any Terraform Dependabot ecosystem you added downstream.
- Remove Terraform-specific docs, examples, validation commands, and table rows from `.github/copilot-instructions.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `README.md`, `CONTRIBUTING.md`, and any project docs you keep after the protected-file cleanup step below is authorized.

#### JSON/JSONC

Set up JSON/JSONC if you use it:

- Read `.github/instructions/json.instructions.md` before editing `*.json` or `*.jsonc` files.
- Keep `templates/json/` as starter content for downstream JSON Schema examples.
- Keep `schemas/example-config.schema.json` and `schemas/examples/example-config/` if you want the worked schema example.
- Keep the `check-json` hook for strict `.json` syntax validation.
- Keep the worked-example `check-jsonschema` hook and `check-metaschema` hook if the worked schema example remains.
- Keep `tests/test_schema_examples.py` if schema examples remain.
- Keep `.github/workflows/data-ci.yml` if you want dedicated JSON/YAML/Actions validation in CI.

Remove JSON/JSONC if you truly do not use it:

- Delete `.github/instructions/json.instructions.md`.
- Delete `templates/json/`.
- Delete `schemas/example-config.schema.json` and `schemas/examples/example-config/` if no schema examples remain.
- Delete `tests/test_schema_examples.py` if no schema examples remain.
- Remove the `check-json` hook from `.pre-commit-config.yaml` only after confirming no strict `.json` files remain.
- Remove only the worked-example `check-jsonschema` hook entry (`Validate example-config valid examples`) and the `check-metaschema` hook from `.pre-commit-config.yaml` if the worked schema example is removed. Keep any other `check-jsonschema` hook entries that validate non-example files against built-in vendor schemas (for example, the `validate-dependabot-config` entry that validates `.github/dependabot.yml` against `vendor.dependabot`).
- In `.github/workflows/data-ci.yml`, remove the `Run check-metaschema` step when the worked example is removed. Keep the `Run check-jsonschema` step as long as any `check-jsonschema` hook entry remains in `.pre-commit-config.yaml` (a single `pre-commit run check-jsonschema --all-files` invocation runs every remaining hook with that ID, including the Dependabot validation). Remove that step (or delete `data-ci.yml` entirely) only when no `check-jsonschema` hooks remain and no dedicated data-file CI is wanted.

#### YAML

Set up YAML if you use it:

- Read `.github/instructions/yaml.instructions.md` before editing `*.yml` or `*.yaml` files.
- Keep `templates/yaml/` as starter content for yamllint configuration variants and starter YAML.
- Keep `.yamllint.yml` for the repository's `yamllint` configuration.
- Keep the `check-yaml`, `yamllint`, and `actionlint` hooks in `.pre-commit-config.yaml`.
- Keep `.github/workflows/data-ci.yml` if you want dedicated JSON/YAML/Actions validation in CI.

Remove YAML only if you remove every YAML-dependent surface:

- Delete `.github/instructions/yaml.instructions.md`.
- Delete `templates/yaml/`.
- Delete `.yamllint.yml`.
- Delete `.github/workflows/data-ci.yml` if no dedicated data-file CI remains.
- Remove the `check-yaml`, `yamllint`, and `actionlint` hooks from `.pre-commit-config.yaml`.
- Delete or replace `.github/workflows/*.yml` and other YAML configuration files; otherwise keep the YAML stack.

#### Markdown/Docs

Set up Markdown if you use it:

- Read `.github/instructions/docs.instructions.md` before editing Markdown files.
- Keep `.github/workflows/markdownlint.yml` for Markdown linting CI.
- Keep `.markdownlint.jsonc`, the Markdown linting scripts in `package.json`, and `templates/markdown/`.

Remove Markdown only if your repository deliberately has no Markdown docs:

- Delete `.github/instructions/docs.instructions.md`.
- Delete `.github/workflows/markdownlint.yml`.
- Delete `.markdownlint.jsonc`.
- Delete `templates/markdown/`.
- Remove Markdown linting scripts and dependencies from `package.json`.
- Delete or replace Markdown files such as `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, and the getting-started guides if you do not keep them.

### If Using Python

#### 1. Rename the Package Directory

The template includes an example Python package at `src/copilot_repo_template/`. Rename it to match your project name:

**Windows (PowerShell):**

```powershell
# Replace 'your_package_name' with your actual package name
# Use underscores, not hyphens (Python package naming convention)
Move-Item -Path "src\copilot_repo_template" -Destination "src\your_package_name"
```

**macOS/Linux/FreeBSD:**

```bash
# Replace 'your_package_name' with your actual package name
mv src/copilot_repo_template src/your_package_name
```

#### 2. Update pyproject.toml

Open `pyproject.toml` and update the following fields:

```toml
[project]
name = "your-project-name"  # Your project name (can use hyphens)
version = "0.1.0"
description = "Your project description"
authors = [
    { name = "Your Name" }
]
keywords = ["your", "keywords", "here"]

# Add your runtime dependencies
dependencies = [
    # "requests>=2.28.0",
    # "pydantic>=2.0.0",
]
```

#### 3. Update Test Imports

Open `tests/test_example.py` and update the import statements to match your package name:

```python
# Change from:
from copilot_repo_template.example import hello

# To:
from your_package_name.example import hello
```

#### 4. Replace Example Code with Your Project Code

The template includes example files demonstrating Python coding standards. Replace these with your actual project code:

1. **Replace the example module:**
   - Delete or replace `src/your_package_name/example.py` with your actual Python modules
   - The example file contains `greet()` and `add_numbers()` functions for demonstration only

2. **Update `__init__.py`:**
   - Update `src/your_package_name/__init__.py` with your package's docstring and any exports you need
   - Update the `__version__` variable if using versioning

3. **Replace example tests:**
   - Delete or replace `tests/test_example.py` with tests for your actual modules
   - Update the docstring in `tests/__init__.py` to reflect your project name (replace "copilot-repo-template" with your project's name)
   - Follow the pytest conventions demonstrated in the example test file

> **Tip:** The example files demonstrate the coding standards defined in `.github/instructions/python.instructions.md`. Review this file when writing your own code to ensure consistency.

#### 5. Verify Python Setup

Install the package in development mode and run tests:

**Windows (PowerShell):**

```powershell
python -m pip install -e ".[dev]"
pytest tests/ -v
```

**macOS/Linux/FreeBSD:**

```bash
pip3 install -e ".[dev]"
pytest tests/ -v
```

You should see output indicating tests passed. If you haven't yet replaced the example tests with your own, you'll see the template's example tests running.

### If NOT Using Python

Remove Python-related files and configurations:

**Windows (PowerShell):**

```powershell
# Remove Python package and test files
Remove-Item -Recurse -Force "src"
Remove-Item -Force "tests\test_example.py"
Remove-Item -Force "tests\__init__.py"
Remove-Item -Force "pyproject.toml"

# Remove Python CI workflow
Remove-Item -Force ".github\workflows\python-ci.yml"

# Remove Python instructions
Remove-Item -Force ".github\instructions\python.instructions.md"

# Remove Python templates
Remove-Item -Recurse -Force "templates\python"
```

**macOS/Linux/FreeBSD:**

```bash
# Remove Python package and test files
rm -rf src/
rm -f tests/test_example.py tests/__init__.py
rm -f pyproject.toml

# Remove Python CI workflow
rm -f .github/workflows/python-ci.yml

# Remove Python instructions
rm -f .github/instructions/python.instructions.md

# Remove Python templates
rm -rf templates/python/
```

#### Update Pre-commit Configuration

Edit `.pre-commit-config.yaml` to remove Python-specific hooks. Delete or comment out the Black and Ruff sections:

```yaml
# Remove or comment out these sections:
#  - repo: https://github.com/psf/black
#    rev: 26.3.1
#    hooks:
#      - id: black
#        args: [--line-length=100]
#
#  - repo: https://github.com/astral-sh/ruff-pre-commit
#    rev: v0.15.12
#    hooks:
#      - id: ruff-check
#        args: [--fix, --line-length=100]
```

#### Update Issue Templates

Edit `.github/ISSUE_TEMPLATE/bug_report.yml` and `.github/ISSUE_TEMPLATE/feature_request.yml` to remove "Python" from the Area dropdown options.

#### Update Pull Request Template

Edit `.github/pull_request_template.md` to remove the "Python-Specific (if applicable)" section.

### If Using PowerShell

#### 1. Review PSScriptAnalyzer Settings

The template includes PSScriptAnalyzer configuration at `.github/linting/PSScriptAnalyzerSettings.psd1`. This enforces the OTBS (One True Brace Style) formatting style.

Review the settings file to understand the rules being enforced. You can customize these settings based on your team's preferences.

#### 2. Add PowerShell Scripts

Add your PowerShell scripts to appropriate locations in your repository. The CI workflow will automatically lint any `.ps1` files.

#### 3. Run PSScriptAnalyzer Locally

**Install PSScriptAnalyzer (if not already installed):**

```powershell
Install-Module -Name PSScriptAnalyzer -Force -Scope CurrentUser
```

**Run linting on a script:**

```powershell
# Lint a single file
Invoke-ScriptAnalyzer -Path .\your-script.ps1 -Settings .\.github\linting\PSScriptAnalyzerSettings.psd1

# Auto-fix formatting issues
Invoke-ScriptAnalyzer -Path .\your-script.ps1 -Settings .\.github\linting\PSScriptAnalyzerSettings.psd1 -Fix
```

#### 4. Run Pester Tests

**Install Pester 5.x (if not already installed):**

```powershell
Install-Module -Name Pester -MinimumVersion 5.0 -Force -Scope CurrentUser
```

**Run tests:**

```powershell
Invoke-Pester -Path tests/ -Output Detailed
```

### If NOT Using PowerShell

Remove PowerShell-related files and configurations:

**Windows (PowerShell):**

```powershell
# Remove PowerShell CI workflow
Remove-Item -Force ".github\workflows\powershell-ci.yml"

# Remove PowerShell instructions
Remove-Item -Force ".github\instructions\powershell.instructions.md"

# Remove linting configuration
Remove-Item -Recurse -Force ".github\linting"

# Remove PowerShell tests
Remove-Item -Recurse -Force "tests\PowerShell"

# Remove PowerShell templates
Remove-Item -Recurse -Force "templates\powershell"
```

**macOS/Linux/FreeBSD:**

```bash
# Remove PowerShell CI workflow
rm -f .github/workflows/powershell-ci.yml

# Remove PowerShell instructions
rm -f .github/instructions/powershell.instructions.md

# Remove linting configuration
rm -rf .github/linting/

# Remove PowerShell tests
rm -rf tests/PowerShell/

# Remove PowerShell templates
rm -rf templates/powershell/
```

#### Update Issue Templates

Edit `.github/ISSUE_TEMPLATE/bug_report.yml` and `.github/ISSUE_TEMPLATE/feature_request.yml` to remove "PowerShell" from the Area dropdown options.

#### Update Pull Request Template

Edit `.github/pull_request_template.md` to remove the "PowerShell-Specific (if applicable)" section.

### JSON/YAML-Heavy Repositories

The template ships with a default JSON/YAML toolchain that already covers most repositories — including JSON-config-only or YAML-heavy projects (for example, Kubernetes manifests, Helm charts, Ansible playbooks, GitHub Actions-only repos). Unlike the Python and PowerShell sections above, you typically do **not** need to add anything new for JSON/YAML; you mostly need to **keep** what is already there and decide how far to take optional schema validation.

> **Do not duplicate full JSON/YAML policy here.** The authoritative authoring rules live in [`.github/instructions/json.instructions.md`](.github/instructions/json.instructions.md) and [`.github/instructions/yaml.instructions.md`](.github/instructions/yaml.instructions.md). Read those files when authoring JSON or YAML.

#### What to Keep

For any repository that contains JSON or YAML (which is essentially all of them), keep the following:

- `.github/instructions/json.instructions.md` — JSON authoring standards.
- `.github/instructions/yaml.instructions.md` — YAML authoring standards.
- `.yamllint.yml` — YAML lint configuration consumed by the `yamllint` pre-commit hook (extends `default`, enforces 2-space indentation, sets the line-length warning at 120 characters, and disables `truthy.check-keys` so unquoted GitHub Actions `on:` keys are accepted; see the inline comment and the [yamllint truthy.check-keys ADR in `.github/TEMPLATE_DESIGN_DECISIONS.md`](.github/TEMPLATE_DESIGN_DECISIONS.md#design-decision-yamllint-truthycheck-keys-default) for the rationale).
- `.github/workflows/data-ci.yml` — the dedicated data-file CI workflow that re-runs `check-json`, `check-yaml`, `yamllint`, `actionlint`, `check-jsonschema`, and `check-metaschema` so JSON/YAML/Actions enforcement can be required via branch protection independent of the aggregate pre-commit gate. See the top-of-file comment in `.github/workflows/data-ci.yml` for how it differs from `auto-fix-precommit.yml`.
- The default pre-commit hooks for data files in `.pre-commit-config.yaml`:
  - `check-json` (validates **strict `.json` only** — see below)
  - `check-yaml`
  - `yamllint`
  - `actionlint` (GitHub Actions workflow validation)
  - `check-jsonschema` and `check-metaschema` (worked-example schema validation; see [Schemas: Worked Example Plus Opt-In for Load-Bearing Contracts](#schemas-worked-example-plus-opt-in-for-load-bearing-contracts))

If you retain the template's aggregate pre-commit workflow (`.github/workflows/precommit-ci.yml` runs `pre-commit run --all-files`), CI will already enforce these hooks for every push and pull request — you do not need to wire up additional CI for JSON/YAML validation.

#### `check-json` vs. `.jsonc`

- The `check-json` hook validates **strict `.json`** files only. The hook is anchored with `files: \.json$`, so `.jsonc` files are intentionally skipped.
- `.jsonc` is allowed only when the consuming tool explicitly supports JSONC (for example, `markdownlint-cli2` reading `.markdownlint.jsonc`, or other tool configurations that ship with a `.jsonc` extension). `.json` files **MUST** remain strict JSON regardless of whether the consuming tool can also accept JSONC.
- The default pre-commit stack does **not** validate `.jsonc` syntax. Repositories that need stricter enforcement of `.jsonc` files should add **JSONC-aware tooling** (a JSONC-aware parser, linter, or schema validator) rather than retrofitting `check-json`.
- JSON5 is **not** enabled by default and **must not** be introduced without an explicit, documented project decision.

#### Schemas: Worked Example Plus Opt-In for Load-Bearing Contracts

The template ships a `schemas/` directory at the repository root for JSON Schemas that describe **load-bearing** JSON or YAML files (files whose shape is depended on by build, deploy, runtime, release automation, or downstream consumers). It is **not** scaffold-only: a worked example schema (`schemas/example-config.schema.json`), valid and invalid example fixtures under `schemas/examples/example-config/`, two pre-commit hooks (`check-jsonschema` for valid examples, `check-metaschema` for the schema itself), and a pytest contract at [`tests/test_schema_examples.py`](tests/test_schema_examples.py) ship enabled by default so the validation pipeline is exercised end to end out of the box.

How schema-backed validation works in this repo:

- `check-jsonschema` runs against `schemas/examples/example-config/valid/` to confirm valid examples pass.
- `check-metaschema` self-validates `schemas/example-config.schema.json` against its declared JSON Schema Draft 2020-12 metaschema.
- `tests/test_schema_examples.py` auto-discovers `schemas/*.schema.json` and the matching `schemas/examples/<name>/{valid,invalid}/` fixtures and asserts that **valid** fixtures exit with code `0` and **invalid** fixtures exit non-zero. Run it with `pytest tests/test_schema_examples.py -v` after any schema or fixture change.
- The dedicated [`.github/workflows/data-ci.yml`](.github/workflows/data-ci.yml) workflow re-runs the same data-file hooks so JSON/YAML/Actions enforcement can be required via branch protection.

To **adapt the worked example** for your own contract, follow the schema authoring conventions in [`schemas/README.md`](schemas/README.md) (Draft 2020-12, `.schema.json` naming, `additionalProperties: false` for closed contracts, `schemas/examples/<name>/{valid,invalid}/` layout) rather than restating those conventions here.

To **add a new schema-backed file family**, add **one `check-jsonschema` hook per real schema-backed file family**, scoped to the files that family covers (for example, `^config/.*\.json$`). Do not add placeholder hooks for schemas that do not yet exist, and do not validate every JSON or YAML file by default. See [`schemas/README.md`](schemas/README.md) for an illustrative hook configuration.

To **remove the worked example** in a downstream repository (or to remove `schemas/` entirely if no schema-backed files are needed), follow the canonical [downstream removal checklist](schemas/README.md#downstream-removal-checklist) in `schemas/README.md` rather than improvising the steps here.

#### Formatting: Prettier and JSON5 Are Not in the Default Toolchain

- **Prettier is opt-in** and is not part of the default pre-commit toolchain. The default stack does not run Prettier on JSON or YAML, and does **not** rely on Prettier (or any other tool) to sort JSON keys. The JSON authoring guide intentionally preserves intentional grouping and tool-managed key order (for example, in `package.json` and lock files). See the [Prettier deferral ADR in `.github/TEMPLATE_DESIGN_DECISIONS.md`](.github/TEMPLATE_DESIGN_DECISIONS.md#design-decision-prettier-deferral-for-data-files) for the full rationale, and [Prettier for JSON/JSONC (Opt-in)](OPTIONAL_CONFIGURATIONS.md#prettier-for-jsonjsonc-opt-in) in `OPTIONAL_CONFIGURATIONS.md` for adoption guidance.
- **JSON5 is not enabled by default.** The JSON authoring guide does not target `.json5`. See the [JSON5 exclusion ADR in `.github/TEMPLATE_DESIGN_DECISIONS.md`](.github/TEMPLATE_DESIGN_DECISIONS.md#design-decision-json5-exclusion-by-default) for the rationale.
- If your project independently adopts Prettier or JSON5, document the decision and ensure the resulting configuration does not conflict with the JSON/YAML authoring guides linked above.

#### Ecosystem Validators

Adopt ecosystem-specific validators (Kubernetes manifest validators, OpenAPI validators, Helm validators, Ansible validators, etc.) only when the repository actually uses those ecosystems. Do not add validators that are not relevant to your stack.

---

## Updating package.json Metadata

**File:** `package.json`

The `package.json` file contains template-specific values that should be updated to reflect your project. This applies to **all projects** using this template, not just Node.js projects, because `package.json` is used for the markdown linting tooling.

If you used the placeholder helper args-file example in [Initial Placeholder Replacement](#initial-placeholder-replacement), the helper can update the `name`, `description`, `author`, and `keywords` fields for you. When `package_name` changes, it also updates the root package identity fields in `package-lock.json` (`name` and `packages[""].name`) without running `npm install`. It updates lockfile version fields only when `package_version` is explicitly supplied.

### Fields to Update

Open `package.json` and update the following fields:

| Field | Template Value | Update To |
| --- | --- | --- |
| `name` | `"copilot-repo-template"` | Your project name (lowercase, no spaces) |
| `description` | `"Template repository with Copilot instructions and code quality tooling"` | Your project description |
| `author` | `"Frank Lesniak"` | Your name or organization |
| `keywords` | `["template", "copilot", "linting"]` | Keywords relevant to your project |

### Example

After updating, your `package.json` metadata might look like:

```json
{
  "name": "my-awesome-project",
  "version": "1.0.0",
  "description": "A tool for automating cloud infrastructure deployments",
  "private": true,
  "keywords": [
    "automation",
    "cloud",
    "infrastructure"
  ],
  "author": "Jane Developer"
}
```

### Fields to Keep As-Is

The following fields can typically remain unchanged:

- `version` — Start at `1.0.0` unless you have a specific versioning scheme
- `private` — Keep as `true` unless you plan to publish to npm
- `scripts` — These are configured for markdown linting and should be kept
- `engines` — Specifies the minimum Node.js version required
- `devDependencies` — Required packages for markdown linting

> **See Also:** [OPTIONAL_CONFIGURATIONS.md](OPTIONAL_CONFIGURATIONS.md#nodejs-package-configuration) for additional optional configurations like adding `repository`, `homepage`, and `bugs` fields.

---

## Customizing the Pull Request Template

**File:** `.github/pull_request_template.md`

The pull request template provides a contributor checklist for consistent PR reviews.

### Delete Template Comment

Delete the HTML comment block at the top of the file — the entire `<!-- ... -->`
block immediately preceding the `## Description` heading. The block contains
template-user guidance (`LINK STYLE`, `CUSTOMIZE`, GHES host note, and a
`KNOWN LIMITATION` paragraph explaining the template-repo-only behavior of
the contributing-guidelines link) that downstream adopters do not need once
the placeholder substitution has been performed. Identify the block by the
opening `<!--` (currently the first line of the file, before any other
content) and the closing `-->` (immediately preceding the `## Description`
heading) rather than by a fixed line range; both endpoints may shift as the
template comment is updated, or if other content is later added above the
block.

Schematic of the block to delete (paragraph headers shown; full prose elided):

```markdown
<!--
(opening paragraph: brief pointer to OPTIONAL_CONFIGURATIONS.md and a
"delete this comment when tailored" instruction)

LINK STYLE: ...

CUSTOMIZE: ...
GHES users: ...

KNOWN LIMITATION (template repo only): ...

(rationale paragraph explaining angle-bracket placeholder use)
-->
```

### Language-Specific Sections

Remove sections for languages you're not using:

- **If NOT using Python:** Delete the entire "Python-Specific (if applicable)" section
- **If NOT using PowerShell:** Delete the entire "PowerShell-Specific (if applicable)" section

### Pre-commit Verification Section

- **If using pre-commit:** Keep the section. Optionally strengthen the conditional language to direct language (see [Pull Request Template Customization](OPTIONAL_CONFIGURATIONS.md#pull-request-template-customization) for details).
- **If NOT using pre-commit:** Delete the entire "Pre-commit Verification (if configured)" section.

> **See Also:** [OPTIONAL_CONFIGURATIONS.md](OPTIONAL_CONFIGURATIONS.md#pull-request-template-customization) for additional customizations like adding language-specific sections for other languages (Node.js, .NET, Go, Rust, Java), customizing Type of Change options, or strengthening test requirements.

---

## Updating README.md

The template README includes both a project section (for your use) and a template documentation section (for template users). You should customize the project section and remove the template documentation.

### Understanding the Current README Structure

The README has two main parts:

1. **Project section (lines 1-10):** Keep this—add your project name and description
2. **Template section (starting with "Readme for the Copilot Repository Template"):** Delete this

### What to Keep

Keep the top section and customize it:

```markdown
# Your Project Name

> **Note:** This repository was created from [`franklesniak/copilot-repo-template`](https://github.com/franklesniak/copilot-repo-template).

## Description

Your actual project description goes here. Explain what your project does,
why it exists, and who it's for.
```

### What to Delete

Delete everything from the heading `## Readme for the Copilot Repository Template` down to the end of the file, including:

- What This Template Provides
- Repository Structure
- How to Use This Template
- Validating Your New Repository
- Language Support
- Linting Tools
- Testing
- Code Quality
- Template Maintenance
- License (keep this, but update if needed)

### Minimal README Template

Here's a minimal template for your project README:

```markdown
# Your Project Name

> **Note:** This repository was created from [`franklesniak/copilot-repo-template`](https://github.com/franklesniak/copilot-repo-template).

## Description

Brief description of what your project does.

## Installation

Instructions for installing your project.

## Usage

Examples of how to use your project.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

MIT License - See [LICENSE](LICENSE) for details.
```

---

## Customizing CONTRIBUTING.md

**File:** `CONTRIBUTING.md`

The `CONTRIBUTING.md` file includes a "For Template Users" section near the end that contains meta-instructions about the template itself. This section should be removed for most downstream projects.

### Remove "For Template Users" Section

This section (starting with `## For Template Users`) includes:

- Information about understanding instruction files
- Guidance on customizing for your project
- First-time setup validation steps

**For non-template projects (most common):** Delete the entire "For Template Users" section, including the HTML comment above it.

**To delete:**

Locate the section starting with:

````markdown
<!--
TEMPLATE ADOPTERS: This entire section is meta-documentation about the template itself.
...
-->

## For Template Users
````

Delete from the HTML comment through the end of the file.

**To keep (if your project is also a template):** Leave the section as-is and customize it for your template's specific guidance.

### Remove Template Maintenance Pointer

`CONTRIBUTING.md` also includes a `Template Taxonomy Updates` section that points contributors to template-maintenance guidance. If your downstream repository no longer maintains this template itself, remove that section during adoption. Keep and customize it only when your repository remains a template and needs to maintain its own downstream sync path mapping.

### Other Customizations

See [OPTIONAL_CONFIGURATIONS.md](OPTIONAL_CONFIGURATIONS.md) for additional `CONTRIBUTING.md` customization guidance, including:

- Replacing `OWNER/REPO` placeholders with your organization and repository name
- Updating Python version requirements
- Removing language-specific sections you don't use

---

## Customizing CODE_OF_CONDUCT.md

**File:** `CODE_OF_CONDUCT.md`

The `CODE_OF_CONDUCT.md` file defines community standards and expectations for behavior when participating in your project. It also establishes enforcement procedures for handling violations.

### Understanding the Contact Method Placeholder

The `[INSERT CONTACT METHOD]` placeholder in `CODE_OF_CONDUCT.md` should be replaced with a method for reporting code of conduct violations that:

- Is actively monitored
- Can receive sensitive reports privately
- Is appropriate for your project's size and community

**Examples of contact methods:**

- An email address (e.g., `conduct@example.com`)
- A link to a reporting form
- Instructions to contact specific maintainers via direct message
- Instructions to contact the repository owners using the contact links on their GitHub profiles

If you used the same email for both `CODE_OF_CONDUCT.md` and `SECURITY.md` during the [Initial Placeholder Replacement](#initial-placeholder-replacement) step, consider whether you want a separate contact method for code of conduct issues versus security vulnerabilities.

Do not use a `users.noreply.github.com` address as the conduct contact. It is suitable for commit attribution privacy, not for receiving sensitive community reports.

### About the Contributor Covenant

This template includes the [Contributor Covenant v3.0](https://www.contributor-covenant.org/version/3/0/code_of_conduct/), which is:

- **Widely recognized:** Used by over 200,000 open source projects
- **GitHub-supported:** Listed as a recommended code of conduct when creating new repositories
- **Comprehensive:** Covers encouraged behaviors, restricted behaviors, enforcement procedures, and scope

### Whether to Keep or Remove

**Keep the file if your project:**

- Accepts contributions from others
- Has or expects community interaction (issues, discussions, PRs)
- Is part of an organization that requires a code of conduct

**Consider removing the file if your project:**

- Is a personal project that doesn't accept external contributions
- Is internal/private with no external community interaction

> **Note:** The placeholder check workflow treats `CODE_OF_CONDUCT.md` as optional—it will continue to pass if the file is missing.

See [OPTIONAL_CONFIGURATIONS.md](OPTIONAL_CONFIGURATIONS.md#code-of-conduct-configuration) for advanced customization options including alternative code of conduct templates and customizing enforcement procedures.

---

## Updating Copilot Instructions

The `.github/copilot-instructions.md` file contains repository-wide coding standards that guide GitHub Copilot's code generation. You should customize this for your project.

### Protected-File Adoption Step

The template protects `.github/copilot-instructions.md`, files under `.github/instructions/`, `.cursor/rules/`, and root agent files such as `.hermes.md`, `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md`. Stack selection usually requires legitimate updates to those files, but make those updates deliberately:

1. Perform non-protected cleanup first, such as deleting unused workflows, templates, source files, and lint configuration.
2. Record the adoption mode for the protected files that remain. Use `minimal-preservation` by default; choose `tailored` only when the maintainer explicitly approves broader rewriting for named files.
3. Record the protected-file edits that remain, including removed tool references, changed validation commands, and language-table updates.
4. Obtain explicit maintainer authorization for the protected-file cleanup. `minimal-preservation` limits the scope of an authorized edit but does not authorize protected-file changes by itself.
5. Update `.github/copilot-instructions.md`, any remaining root agent files, and relevant `.github/instructions/*.instructions.md` files so they no longer reference deleted tools or stacks.
6. Bump `Last Updated` and `Version` metadata in protected files that carry those fields.
7. Use durable adoption language. Avoid temporary implementation notes such as "for this migration" in governance docs that downstream maintainers will keep.

### Customizing the Source of Truth Section

Edit `.github/copilot-instructions.md` and update the "Source of Truth" section to point to your project's specification or design documents:

```markdown
## Source of Truth

> **Important:** Read **`docs/spec/requirements.md`** before making changes.
> If any instruction here conflicts with the spec, **the spec wins**.
```

If you don't have a specification document yet, you can simplify this section or leave the placeholder guidance.

### Updating the Modular Instructions Table

If you removed language or data-format support, update the modular instructions table to reflect your project's languages, data formats, and cross-cutting rules:

```markdown
## Modular Instructions

This repository uses modular instruction files covering both language-specific standards and cross-cutting repository rules:

| Scope | Instruction File | Applies To |
| --- | --- | --- |
| Git attributes | `.github/instructions/gitattributes.instructions.md` | `**/.gitattributes` |
| Markdown/Docs | `.github/instructions/docs.instructions.md` | `**/*.md` |
```

Remove rows for languages you're not using.

### Updating Linting and Testing Tables

If you removed Python, PowerShell, Terraform, JSON, YAML, or Markdown support, also update the **Linting Configurations** and **Testing Tools** tables in `.github/copilot-instructions.md`.

**Linting Configurations table** — Remove the PSScriptAnalyzer row if you removed PowerShell:

```markdown
## Linting Configurations

| Tool | Configuration File | Purpose |
| --- | --- | --- |
| markdownlint | `.markdownlint.jsonc` | Markdown linting |
```

**Testing Tools table** — Remove rows for languages you're not using:

If you removed Python:

```markdown
## Testing Tools

| Language | Framework | Configuration | Test Location |
| --- | --- | --- | --- |
| PowerShell | Pester 5.x | Inline in `.github/workflows/powershell-ci.yml` | `tests/PowerShell/` |
```

If you removed PowerShell:

```markdown
## Testing Tools

| Language | Framework | Configuration | Test Location |
| --- | --- | --- | --- |
| Python | pytest | `pyproject.toml` (`[tool.pytest.ini_options]`) | `tests/` |
```

If you removed both Python and PowerShell, remove the entire Testing Tools section or update it for your project's languages.

### Reviewing Instruction Files

Review the files in `.github/instructions/` and remove or modify any that don't apply to your project:

- `docs.instructions.md` - Documentation standards (keep for all projects)
- `gitattributes.instructions.md` - `.gitattributes` standards (keep if you retain `.gitattributes`)
- `json.instructions.md` - JSON/JSONC standards (remove only if you truly have no JSON/JSONC files)
- `powershell.instructions.md` - PowerShell standards (remove if not using PowerShell)
- `python.instructions.md` - Python standards (remove if not using Python)
- `terraform.instructions.md` - Terraform/IaC standards (remove if not using Terraform)
- `yaml.instructions.md` - YAML standards (keep if you retain GitHub Actions workflows or other YAML files)

### Reviewing Agent Instruction Files

The template includes agent instruction files for multi-platform AI coding agent support:

- `.cursor/rules/repository-instructions.mdc` — Cursor Agent project rule
- `.hermes.md` — Hermes Agent
- `CLAUDE.md` — Claude Code, GitHub Copilot coding agent
- `AGENTS.md` — OpenAI Codex CLI, GitHub Copilot coding agent
- `GEMINI.md` — Gemini Code Assist, GitHub Copilot coding agent

These files are thin entry points for their respective AI coding platforms. `.github/copilot-instructions.md` remains canonical, and the root agent files keep only a minimal inline summary of the highest-priority shared rules plus any platform-specific guidance.

**To customize for your project:**

1. **Remove unneeded files** — Delete agent files for platforms you do not use (e.g., if not using Cursor Agent, delete `.cursor/rules/repository-instructions.mdc`; if not using Hermes Agent, delete `.hermes.md`; if not using Claude Code, delete `CLAUDE.md`)
2. **Keep remaining files** — Keep all agent files for platforms you want to support, or accept that agents on those platforms receive no project-specific instructions
3. **Keep minimal summaries aligned** — If you modified high-priority shared guidance in `.github/copilot-instructions.md` (for example, safety rules, pre-commit requirements, validation commands, language instruction references, or canonical-file guidance), update any remaining agent files so their minimal summaries stay accurate

---

## Additional Configuration (Optional)

### Installing the GitHub CLI

Several optional configuration steps use the GitHub CLI (`gh`). If you haven't installed it yet:

**Windows:**

Download from [cli.github.com](https://cli.github.com/) or use winget:

```powershell
winget install --id GitHub.cli
```

**macOS:**

```bash
brew install gh
```

**Linux (Debian/Ubuntu):**

```bash
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh
```

After installation, authenticate with GitHub:

```bash
gh auth login
```

### Creating the `triage` Label

The issue templates reference a `triage` label that doesn't exist by default. Creating this label enables better issue organization.

**Why it's not created automatically:** GitHub doesn't support auto-creating labels when a repository is created from a template. This is a platform limitation.

**Using GitHub CLI:**

```bash
gh label create triage --description "Needs triage" --color "d4c5f9"
```

**Using the GitHub web interface:**

1. Go to your repository on GitHub
2. Navigate to **Issues** > **Labels** (or go to Settings > Labels)
3. Click **New label**
4. Enter:
   - **Label name:** `triage`
   - **Description:** `Needs triage`
   - **Color:** `d4c5f9` (lavender)
5. Click **Create label**

**After creating the label:** Uncomment the `# - triage` line in each issue template where you want it applied:

- `.github/ISSUE_TEMPLATE/bug_report.yml`
- `.github/ISSUE_TEMPLATE/documentation_issue.yml`
- `.github/ISSUE_TEMPLATE/feature_request.yml`

### Configuring Dependabot

The template includes Dependabot configuration at `.github/dependabot.yml` for automated dependency updates.

**To customize update frequency:**

Edit `.github/dependabot.yml` and modify the `schedule` section:

```yaml
schedule:
  interval: "weekly"  # Options: daily, weekly, monthly
```

**To disable Dependabot:**

Delete `.github/dependabot.yml` from your repository.

### Branch Ruleset (Recommended)

Repository rulesets help prevent accidental force pushes and ensure code review. Rulesets are the recommended replacement for classic branch protection rules and offer more granular control. See [GitHub's rulesets documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets) for setup instructions.

For detailed guidance on branch ruleset setup, see the "Branch Ruleset Setup" section in [`.github/TEMPLATE_DESIGN_DECISIONS.md`](.github/TEMPLATE_DESIGN_DECISIONS.md).

---

## Validation and Testing

Before committing your changes, validate that everything is configured correctly.

### Confirm Local Validation Prerequisites

Before running validation commands, confirm the tool runtime for each check is installed:

- Run `npm install` or `npm ci` before `npm run lint:md`, `npm run lint:md:nested`, or other npm-backed Markdown lint commands.
- Install `pre-commit` in the active Python environment, or use `python -m pre_commit` / `python3 -m pre_commit` if the `pre-commit` executable is not on `PATH`.
- Treat `pre-commit install` as a local developer setup step. Automation should usually run `pre-commit run --all-files` directly unless your workflow explicitly needs to install Git hooks.
- Keep Python available for Python-based hooks such as `check-jsonschema`, `check-metaschema`, and repo-local hook wrappers, even if your repository has no Python project source.

### Run Pre-commit on All Files

```bash
pre-commit run --all-files
```

**Expected output for a clean run:**

```text
Trim Trailing Whitespace......................................Passed
Fix End of Files..............................................Passed
Check Yaml....................................................Passed
Check JSON....................................................Passed
Check for added large files...................................Passed
yamllint......................................................Passed
actionlint....................................................Passed
black.........................................................Passed
ruff..........................................................Passed
Validate example-config valid examples........................Passed
Validate Dependabot configuration.............................Passed
Self-validate example-config schema...........................Passed
markdownlint-cli2.............................................Passed
Terraform fmt.................................................Passed
Terraform validate........................(no files to check)Skipped
Terraform validate with tflint...............................Passed
```

**Troubleshooting common failures:**

- **Trailing whitespace / End of file:** These are auto-fixed. Re-run pre-commit and it should pass.
- **JSON errors:** Check strict `.json` syntax; `.jsonc` is intentionally outside `check-json`.
- **YAML errors:** Check for syntax errors in `.yml` files.
- **Schema errors:** Run `pytest tests/test_schema_examples.py -v` after schema or schema-example changes, or `pre-commit run check-jsonschema --all-files` and `pre-commit run check-metaschema --all-files` to isolate hook failures.
- **GitHub Actions errors:** `actionlint` reports workflow syntax, expression, and runner-label issues.
- **Markdown errors:** Run `npm run lint:md` to see specific issues.
- **Black/Ruff errors:** These may auto-fix. Re-run pre-commit. For persistent issues, check the specific error messages.
- **Terraform errors:** Install `terraform` and `tflint`, then re-run the Terraform hooks. The hooks are Python wrappers and support native Windows PowerShell, Git Bash, WSL/Linux, and macOS.

### Run Terraform Validation Locally (If Applicable)

Use the pre-commit hooks for the local path that matches CI behavior.

**Windows PowerShell:**

```powershell
python -m pre_commit run terraform-fmt --all-files
python -m pre_commit run terraform-validate --all-files
python -m pre_commit run terraform-tflint --all-files
```

**Git Bash, WSL/Linux, macOS, and other POSIX-style shells:**

```bash
pre-commit run terraform-fmt --all-files
pre-commit run terraform-validate --all-files
pre-commit run terraform-tflint --all-files
```

The hooks run `terraform fmt -check -recursive -diff` from the repository root, validate each directory containing `.tf` or `.tf.json` files with `terraform init -backend=false` followed by `terraform validate`, and run `tflint --init` followed by recursive TFLint with the repository-root `.tflint.hcl` config.

### Run Tests (If Applicable)

**Python:**

```bash
pytest tests/ -v
```

**PowerShell:**

```powershell
Invoke-Pester -Path tests/ -Output Detailed
```

**JSON Schema example fixtures:**

```bash
pytest tests/test_schema_examples.py -v
```

### Commit and Push

**Stage all changes:**

```bash
git add .
```

**Review what will be committed:**

```bash
git status
```

**Create your initial commit:**

```bash
git commit -m "Initial project setup from template"
```

> **Note:** Pre-commit hooks will run automatically. If they modify files, review the changes, stage them (`git add .`), and commit again.

**Push to GitHub:**

```bash
git push origin main
```

### Verify CI Workflows Pass

After pushing, go to your repository on GitHub and:

1. Click the **Actions** tab
2. Verify that all workflows complete successfully (green checkmarks)

### Verify Placeholder Check Workflow

The `check-placeholders.yml` workflow runs `.github/scripts/replace-template-placeholders.py scan` to verify that the same placeholder and URL-shape allowlist used by the helper has been cleared. If this workflow fails:

1. Read the error messages to identify which files still have placeholders or possible corruption
2. Run the helper from [Initial Placeholder Replacement](#initial-placeholder-replacement), or replace the reported exact placeholders manually
3. Commit and push the fixes

**What the workflow checks:**

- Approved `https://github.com/OWNER/REPO...` URL placeholders in `.github/ISSUE_TEMPLATE/config.yml`, `.github/ISSUE_TEMPLATE/bug_report.yml`, `.github/pull_request_template.md`, `CONTRIBUTING.md`, and `SECURITY.md`
- `OWNER/REPO` in the helper's allowlisted non-URL placeholder contexts
- `@OWNER` in `.github/CODEOWNERS`
- `[security contact email]` in `SECURITY.md`
- `TODO: Replace` markers in `SECURITY.md`
- `[INSERT CONTACT METHOD]` in `CODE_OF_CONDUCT.md`
- The template `window.title` value in `.vscode/settings.json`
- Common broad-replacement corruption patterns, such as repository names accidentally injected into `REPORT`, `REPOSITORY`, or `REPOSITORIES`

**After all placeholders are replaced:**

Treat `.github/workflows/check-placeholders.yml` as a transitional adoption workflow. Once you've replaced all placeholders and the workflow passes, you have two valid options:

- **Keep the workflow** while `OWNER/REPO`, `@OWNER`, `[security contact email]`, or similar template placeholders are still being replaced, or if you expect future template syncs to reintroduce placeholder-bearing files.
- **Remove the workflow** after the repository is initialized and all placeholders have been replaced with concrete downstream values.

If you remove the workflow, also drop or de-emphasize docs that imply it still exists, do not reintroduce live `OWNER/REPO` placeholders, and prefer concrete downstream repository URLs in issue templates, PR templates, and community-health docs.

See [Placeholder Check Workflow Configuration](OPTIONAL_CONFIGURATIONS.md#placeholder-check-workflow-configuration) for more details on customizing this workflow.

### Post-clone Verification Plan

After completing the setup checklist, perform the following quick verification:

1. **Verify template functionality** in your newly created repository (template maintainers can create a separate test repository to verify template changes)
2. **Open each issue type** once and ensure required fields behave correctly
3. **Click key links** in the issue template chooser:
   - Contributing Guide link
   - Security Vulnerabilities link
   - (If enabled) Discussions link
4. **Verify issue form rendering:**
   - Open a bug report issue template
   - Paste a Python traceback into the Logs/Error Output field
   - Confirm it renders cleanly as plain text (not mangled by Markdown parsing)
5. **Verify security flow:**
   - From your repository's main page, click the **Security** tab
   - Confirm SECURITY.md is accessible
6. **Open a test PR** to verify the PR workflow:
   - Create a trivial change (e.g., add a comment to a file)
   - Open a pull request and confirm:
     - PR template renders correctly
     - Contributing guidelines link works
     - CI workflows trigger as expected
   - Close the test PR without merging

---

## Cleanup

After completing setup and verification, clean up template-specific files.

### Review TEMPLATE_DESIGN_DECISIONS.md

The template design decisions document (`.github/TEMPLATE_DESIGN_DECISIONS.md`) contains rationale for design choices made in the **template itself**, not your downstream project. Review it during setup to understand why the template is structured the way it is.

**After review, choose one of these options:**

1. **Keep it** if you want to preserve template rationale for future reference (e.g., onboarding new maintainers or understanding why configurations were made)
2. **Delete it** if the template rationale is not useful for your project going forward

> **Note:** This file documents the *template's* design decisions. It is not about your project's design decisions. If you keep it, be aware that its content is template-specific and may reference context that does not apply to your repository.

### Consider This Getting Started Guide

You have three options for `GETTING_STARTED_NEW_REPO.md`:

1. **Delete it** if your project won't be used as a template for others
2. **Keep it** if your project is also a template that others will clone
3. **Modify it** to be specific to your project's setup process

**To delete:**

**Windows (PowerShell):**

```powershell
Remove-Item -Force "GETTING_STARTED_NEW_REPO.md"
```

**macOS/Linux/FreeBSD:**

```bash
rm -f GETTING_STARTED_NEW_REPO.md
```

### Final Cleanup Commit

```bash
git add .
git commit -m "Remove template documentation after initial setup"
git push origin main
```

---

## Troubleshooting

### Pre-commit Hook Failures

**Problem:** Pre-commit hooks fail with "command not found" errors.

**Solution:** Ensure pre-commit is installed globally and in your PATH:

```bash
pip install pre-commit
pre-commit --version
```

**Problem:** Hooks download every time you commit.

**Solution:** This is normal on first run. The environments are cached in `~/.cache/pre-commit/`. If they keep downloading, check disk space and permissions.

### Python ModuleNotFoundError

**Problem:** `ModuleNotFoundError: No module named 'copilot_repo_template'`

**Solution:** You need to either:

1. Rename `src/copilot_repo_template/` to your package name and update imports
2. Install the package in development mode: `pip install -e ".[dev]"`
3. If not using Python, delete the `src/` directory

### Node.js/npm Errors

**Problem:** `npm install` fails with permission errors.

**Solution:**

- **Windows:** Run PowerShell as Administrator
- **macOS/Linux:** Don't use `sudo npm install`. Instead, fix npm permissions or use a version manager like nvm.

**Problem:** `npm run lint:md` fails with "command not found".

**Solution:** Run `npm install` first to install dependencies.

### Placeholder Check CI Failures

**Problem:** The `check-placeholders.yml` workflow fails.

**Solution:** Read the error messages carefully. They tell you exactly which files and lines contain placeholders. Replace:

- `OWNER/REPO` with `your-username/your-repo-name`
- `@OWNER` with `@your-username`
- `[security contact email]` with your monitored security contact, or rerun the helper with `--security-reporting-mode github-private-only` if you intentionally use GitHub private vulnerability reporting only

### Permission Errors

**Windows:**

- Run PowerShell as Administrator for system-wide installations
- Check that Python and Node.js are in your PATH
- Restart PowerShell after installing new tools

**macOS/Linux/FreeBSD:**

- Don't use `sudo` for pip or npm installations in your home directory
- Check file ownership: `ls -la`
- Fix ownership: `sudo chown -R $(whoami) ~/.npm ~/.cache`

### Pre-commit Not Running on Commit

**Problem:** Git commits succeed without running pre-commit hooks.

**Solution:** Re-install the hooks:

**Windows (PowerShell):**

If you installed with pipx:

```powershell
pre-commit install
```

> **Note:** If `pre-commit` is not found, run `python -m pipx ensurepath` and restart your PowerShell window. Do not use `pipx run pre-commit install` because it runs from a temporary environment and can create hooks that reference a non-existent interpreter.

If you installed with pip:

```powershell
python -m pre_commit install
```

**macOS/Linux/FreeBSD:**

If you installed with pipx:

```bash
pre-commit install
```

> **Note:** If `pre-commit` is not found, run `python3 -m pipx ensurepath` (or `pipx ensurepath` if `pipx` is already on your PATH) and restart your terminal. Do not use `pipx run pre-commit install` because it runs from a temporary environment and can create hooks that reference a non-existent interpreter.

If you installed with Homebrew:

```bash
pre-commit install
```

> **Note:** If `pre-commit` is not found, ensure Homebrew's `bin` directory (typically `/opt/homebrew/bin` on Apple Silicon or `/usr/local/bin` on Intel Macs) is in your PATH.

If you installed with pip:

```bash
python3 -m pre_commit install
```

Verify the hook exists:

**Windows:**

```powershell
Get-Content .git\hooks\pre-commit
```

**macOS/Linux/FreeBSD:**

```bash
cat .git/hooks/pre-commit
```

---

## Development Workflow

Now that your repository is set up, you're ready to start development! For the standard development workflow, including:

- Creating branches
- Making changes
- Running tests
- Submitting pull requests
- Code review process

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed instructions.

**Quick reference for daily development:**

**Windows (PowerShell):**

```powershell
# Create a feature branch
git checkout -b feature/your-feature-name

# Make changes and run pre-commit
pre-commit run --all-files

# Stage and commit
git add .
git commit -m "Add your feature"

# Push and open a PR
git push origin feature/your-feature-name
```

If `pre-commit` is not on PATH:

- **pipx users:** Run `python -m pipx ensurepath` (or `pipx ensurepath` if `pipx` is already on your PATH) and restart your PowerShell window, then run `pre-commit run --all-files`.
- **pip users:** Use module invocation:

  ```powershell
  python -m pre_commit run --all-files
  ```

**macOS/Linux/FreeBSD:**

```bash
# Create a feature branch
git checkout -b feature/your-feature-name

# Make changes and run pre-commit
pre-commit run --all-files

# Stage and commit
git add .
git commit -m "Add your feature"

# Push and open a PR
git push origin feature/your-feature-name
```

If `pre-commit` is not on PATH:

- **pipx users:** Run `python3 -m pipx ensurepath` (or `pipx ensurepath` if `pipx` is already on your PATH) and restart your terminal, then run `pre-commit run --all-files`.
- **pip users:** Use module invocation:

  ```bash
  python3 -m pre_commit run --all-files
  ```

---

## Next Steps

After completing the initial setup, you may want to explore additional customization options:

- **[Optional Configurations](OPTIONAL_CONFIGURATIONS.md)**: Fine-tune your repository with optional settings like enabling GitHub Discussions, adjusting Dependabot frequency, customizing linting rules, and more.

---

**Congratulations!** 🎉 Your repository is now fully configured and ready for development. Happy coding!
