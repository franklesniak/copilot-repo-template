# Getting Started: Creating a New Repository from This Template

This guide walks you through creating a brand-new repository using `franklesniak/copilot-repo-template`. It is designed for beginners who may not be familiar with Git, Python, Node.js, or pre-commit. If you are looking to merge this template into an existing repository, refer to the README.md instead.

**Estimated time to complete:** 30-60 minutes (depending on your system and internet speed)

---

## Table of Contents

- [What This Template Provides](#what-this-template-provides)
- [Prerequisites](#prerequisites)
  - [Windows Setup](#windows-setup)
  - [macOS Setup](#macos-setup)
  - [Linux/FreeBSD Setup](#linuxfreebsd-setup)
- [Creating Your Repository on GitHub](#creating-your-repository-on-github)
- [Cloning Your New Repository](#cloning-your-new-repository)
- [Installing Dependencies](#installing-dependencies)
- [Initial Placeholder Replacement](#initial-placeholder-replacement)
- [Next Steps](#next-steps)

---

## What This Template Provides

This template repository includes:

- **GitHub Copilot Instructions:** Comprehensive coding standards that guide AI-assisted development
- **Language-Specific Guidelines:** Modular instruction files for Markdown, PowerShell, and Python
- **Linting Configurations:** Pre-configured settings for markdownlint and PSScriptAnalyzer
- **Pre-commit Hooks:** Automated code quality checks before commits
- **Issue Templates:** Structured templates for bug reports, feature requests, and documentation issues
- **Pull Request Template:** Checklist-based template for consistent PR reviews
- **CI Workflows:** GitHub Actions workflows for linting, testing, and validation

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

#### 4. Verify Your Installations

Open **PowerShell** (search for "PowerShell" in the Start menu) and run these commands:

```powershell
# Check Git version
git --version

# Check Python version
python --version

# Check Node.js version
node --version

# Check npm version (comes with Node.js)
npm --version
```

You should see version numbers for each command. If any command shows an error, revisit the installation steps for that tool.

**Example output:**

```text
git version 2.43.0.windows.1
Python 3.12.1
v20.10.0
10.2.3
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

#### 5. Verify Your Installations

Open **Terminal** and run these commands:

```bash
# Check Git version
git --version

# Check Python version
python3 --version

# Check Node.js version
node --version

# Check npm version
npm --version
```

You should see version numbers for each command.

**Example output:**

```text
git version 2.39.3 (Apple Git-145)
Python 3.12.1
v20.10.0
10.2.3
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

---

## Initial Placeholder Replacement

This template uses placeholder values that you **must** replace with your actual repository information. The CI workflow (`check-placeholders.yml`) will fail until you complete these replacements.

### Files That Need Placeholders Replaced

| File | Placeholders to Replace |
| --- | --- |
| `.github/ISSUE_TEMPLATE/config.yml` | `OWNER/REPO` (appears in URLs twice) |
| `.github/CODEOWNERS` | `@OWNER` (appears four times) |
| `CONTRIBUTING.md` | `OWNER/REPO` (appears in clone URL and issues URL) |
| `SECURITY.md` | `[security contact email]` |

### What the Placeholders Mean

- **`OWNER`:** Your GitHub username or organization name (e.g., `franklesniak`)
- **`REPO`:** Your repository name (e.g., `my-new-project`)
- **`OWNER/REPO`:** Combined format used in GitHub URLs (e.g., `franklesniak/my-new-project`)
- **`@OWNER`:** GitHub username with @ prefix for CODEOWNERS file (e.g., `@franklesniak`)
- **`[security contact email]`:** An email address for receiving security vulnerability reports

### Option A: Find and Replace Commands

#### Windows (PowerShell)

Open PowerShell in your repository directory and run these commands. Replace the placeholder values with your actual information:

```powershell
# Define your values (replace these with your actual username/org, repo name, and email)
$Owner = "your-username"
$Repo = "your-repo-name"
$SecurityEmail = "security@example.com"

# Replace OWNER/REPO in config.yml
(Get-Content ".github/ISSUE_TEMPLATE/config.yml") -replace 'OWNER/REPO', "$Owner/$Repo" | Set-Content ".github/ISSUE_TEMPLATE/config.yml"

# Replace OWNER/REPO in CONTRIBUTING.md
(Get-Content "CONTRIBUTING.md") -replace 'OWNER/REPO', "$Owner/$Repo" | Set-Content "CONTRIBUTING.md"

# Replace @OWNER in CODEOWNERS (note the @ prefix)
(Get-Content ".github/CODEOWNERS") -replace '@OWNER', "@$Owner" | Set-Content ".github/CODEOWNERS"

# Replace security email placeholder in SECURITY.md
(Get-Content "SECURITY.md") -replace '\[security contact email\]', $SecurityEmail | Set-Content "SECURITY.md"
```

#### macOS/Linux/FreeBSD (Bash)

Open Terminal in your repository directory and run these commands. Replace the placeholder values with your actual information:

```bash
# Define your values (replace these with your actual username/org, repo name, and email)
OWNER="your-username"
REPO="your-repo-name"
SECURITY_EMAIL="security@example.com"

# Replace OWNER/REPO in config.yml
sed -i.bak "s|OWNER/REPO|$OWNER/$REPO|g" .github/ISSUE_TEMPLATE/config.yml && rm .github/ISSUE_TEMPLATE/config.yml.bak

# Replace OWNER/REPO in CONTRIBUTING.md
sed -i.bak "s|OWNER/REPO|$OWNER/$REPO|g" CONTRIBUTING.md && rm CONTRIBUTING.md.bak

# Replace @OWNER in CODEOWNERS
sed -i.bak "s|@OWNER|@$OWNER|g" .github/CODEOWNERS && rm .github/CODEOWNERS.bak

# Replace security email placeholder in SECURITY.md
sed -i.bak 's|\[security contact email\]|'"$SECURITY_EMAIL"'|g' SECURITY.md && rm SECURITY.md.bak
```

> **Note for macOS users:** The `sed -i.bak` syntax creates a backup file before modifying. The `&& rm *.bak` part removes the backup. If you're using GNU sed (Linux), you can use `sed -i` without the `.bak` extension.

### Option B: Manual Replacement

If you prefer, you can open each file in a text editor and manually find and replace the placeholders:

1. **`.github/ISSUE_TEMPLATE/config.yml`:**
   - Find: `OWNER/REPO`
   - Replace with: `your-username/your-repo-name` (appears in two URLs)

2. **`.github/CODEOWNERS`:**
   - Find: `@OWNER`
   - Replace with: `@your-username` (appears four times)

3. **`CONTRIBUTING.md`:**
   - Find: `OWNER/REPO`
   - Replace with: `your-username/your-repo-name` (appears in clone URL and issues link)

4. **`SECURITY.md`:**
   - Find: `[security contact email]`
   - Replace with: your actual security contact email address

### Understanding the CODEOWNERS File

The `.github/CODEOWNERS` file defines who is automatically requested to review pull requests. The `@OWNER` placeholder should be replaced with:

- Your GitHub username (e.g., `@octocat`) for personal repositories
- A team reference (e.g., `@my-org/maintainers`) for organization repositories

For example, if your GitHub username is `janedoe`, replace `@OWNER` with `@janedoe`.

### Understanding the Security Email Placeholder

The `[security contact email]` placeholder in `SECURITY.md` should be replaced with an email address that:

- Is actively monitored
- Can receive sensitive security reports
- Is not publicly visible (unlike GitHub issues)

If you prefer not to use email, you can:

1. Remove the email section entirely from `SECURITY.md`
2. Keep only the GitHub Security Advisories option (see [`.github/TEMPLATE_GUIDE.md`](.github/TEMPLATE_GUIDE.md) for details)

---

## Next Steps

Congratulations! You've completed Part 1 of the setup process. Your repository now has:

- All prerequisites installed on your computer
- A new repository created from the template
- The repository cloned to your local machine
- Node.js dependencies installed
- Placeholder values replaced with your actual information

**Part 2 of this guide** (continuing below in this same document) will cover:

- Installing and configuring pre-commit hooks
- Customizing the template for your project (removing unused languages, updating configurations)
- Validating your setup by running linting and tests
- Making your first commit and pushing changes
- Understanding the CI workflows and what happens when you push

For detailed customization options beyond the basics, see [`.github/TEMPLATE_GUIDE.md`](.github/TEMPLATE_GUIDE.md).

---

*Continue to Part 2 below for pre-commit setup and project customization...*
