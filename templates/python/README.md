# Python Template Files

This directory contains template Python configuration files and scaffolding for projects using Python in this repository template.

## Purpose

These template files demonstrate how to configure Python tooling to align with the coding standards defined in `.github/instructions/python.instructions.md`.

## Files Included

- **`pyproject.toml`**: Sample configuration for Python project metadata, dependencies, and tooling (Black, Ruff, mypy, pytest)
- **`tests/`**: Sample test directory structure with placeholder test file
- **`README.md`**: This file

## How to Use

1. **Copy files to your project root** (or appropriate location based on your layout)
2. **Customize `pyproject.toml`**:
   - Update `[project]` section with your project's name, version, description, authors
   - Add your runtime dependencies to `dependencies = []`
   - Adjust dev dependencies as needed
3. **Create your source code** in either a flat layout or `src/` layout (see below)
4. **Replace placeholder tests** in `tests/` with your actual test files
5. **Update Python version references** when upstream support changes (see below)

## Project Layout Options

### Option 1: Flat Layout

Place your Python modules directly in the project root:

```text
your-project/
├── pyproject.toml
├── your_module.py
├── another_module.py
└── tests/
    └── test_your_module.py
```

For mypy in CI, use:

```yaml
env:
  MYPY_PATHS: "."
```

### Option 2: src/ Layout (Recommended)

Place your Python package(s) in a `src/` directory:

```text
your-project/
├── pyproject.toml
├── src/
│   └── your_package/
│       ├── __init__.py
│       └── module.py
└── tests/
    └── test_module.py
```

For mypy in CI, use:

```yaml
env:
  MYPY_PATHS: "src/ tests/"
```

The `src/` layout is recommended because it:

- Prevents accidental imports of uninstalled code during development
- Makes it clear what code is part of the package vs. project tooling
- Aligns with modern Python packaging best practices

## Python Version Configuration

Different Python tools require different version format specifications. When updating the minimum Python version, you must update **all three** of these settings:

### 1. Project Metadata: `requires-python`

```toml
[project]
requires-python = ">=3.13"  # PEP 621 standard: ">=" operator with dotted version
```

### 2. Black Configuration: `target-version`

```toml
[tool.black]
target-version = ["py313"]  # List of strings in "pyXYZ" format
```

### 3. mypy Configuration: `python_version`

```toml
[tool.mypy]
python_version = "3.13"  # Dotted version string (no ">=" operator)
```

### 4. Ruff Configuration: `target-version` (Optional)

```toml
[tool.ruff]
# Ruff automatically infers target-version from [project].requires-python
# Only set this if you need to override:
# target-version = "py313"  # Single string in "pyXYZ" format (not a list)
```

**Important:** If you set `[project].requires-python`, Ruff will automatically use that value. Setting `[tool.ruff].target-version` explicitly will override the inferred value.

## Python Version Support Policy

**Always use a Python version that is currently receiving bugfixes.**

- Python versions in "security fix only" phase are **not publicly installable** with security updates—they require building from source with manually applied patches.
- As of January 2026, **Python 3.13** is the latest bugfix-supported version (receiving bugfixes and security updates until approximately October 2026 per [PEP 719](https://peps.python.org/pep-0719/)).
- Python 3.12 stopped receiving bugfixes in April 2025 per [PEP 693](https://peps.python.org/pep-0693/) and is now security-fix only.

**When to update:**

- Check the [Python Developer's Guide - Versions](https://devguide.python.org/versions/) page annually (typically around October when new Python versions are released)
- Update all version references in `pyproject.toml` when the minimum supported version changes
- Update the CI workflow's Python version matrix in `.github/workflows/python-ci.yml`

## mypy Path Configuration

The CI workflow (`.github/workflows/python-ci.yml`) uses the `MYPY_PATHS` environment variable to specify which directories/files mypy should check.

**Default:**

```yaml
env:
  MYPY_PATHS: "src/ tests/"
```

**For flat layout:**

```yaml
env:
  MYPY_PATHS: "."
```

**For custom directories:**

```yaml
env:
  MYPY_PATHS: "foo/ bar/ baz.py"
```

The command-line paths override any `files` or `exclude` settings in `pyproject.toml` or `mypy.ini` in terms of directory scope. However, per-file configuration options in those files still apply to the files that mypy discovers.

## Additional Resources

- [Python Developer's Guide - Versions](https://devguide.python.org/versions/)
- [PEP 621 - Python Project Metadata](https://peps.python.org/pep-0621/)
- [Black Documentation](https://black.readthedocs.io/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [mypy Documentation](https://mypy.readthedocs.io/)
- [pytest Documentation](https://docs.pytest.org/)
