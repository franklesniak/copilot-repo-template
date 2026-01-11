---
applyTo: "**/*.py"
description: "Python coding standards:  portability-first by default, modern-advanced when the stack requires it."
---

# Python Writing Style

**Version:** 1.0.20260111.0

## Metadata

- **Status:** Active
- **Owner:** Repository Maintainers
- **Last Updated:** 2026-01-11
- **Scope:** Defines Python coding standards for all Python files in this repository, including modules, scripts, tests, and tooling. Covers style, structure, error handling, testing, and documentation requirements.
- **Related:** [Repository Copilot Instructions](../copilot-instructions.md)

## Purpose and Scope

This guide establishes the Python coding standards for the repository.  Code must be maintainable, deterministic, and security-conscious.  The style adapts to project constraints:  **stdlib-first, portability-first** by default, shifting to **modern-advanced** when required by the technology stack (async frameworks, type-heavy APIs, etc.).

## Executive Summary:  Author Profile

The default style is a highly disciplined **stdlib-first, portability-first** approach.  When code can reasonably run on a minimal, widely available Python baseline, it should:  minimize dependencies, avoid unnecessary metaprogramming, and prefer clarity over cleverness.

This baseline is not dogma.  When external constraints require modern Python (e.g., `typing`-heavy APIs, async I/O, Pydantic models, FastAPI), the style intentionally shifts to a **modern-advanced** posture.

## Quick Reference Checklist

### Layout and Formatting

- **[All]** Use 4 spaces; never tabs.
- **[All]** Follow PEP 8/PEP 257; line length target **<= 100** (may exceed for URLs/long strings when readability wins).
- **[All]** Keep formatting tool-friendly: do not hand-align with extra whitespace.
- **[All]** Prefer f-strings for interpolation; avoid `%` formatting except when required.
- **[All]** Avoid trailing whitespace; files end with a single newline.

### Naming and Structure

- **[All]** `snake_case` for functions/variables; `PascalCase` for classes; `UPPER_SNAKE_CASE` for constants.
- **[All]** Modules are nouns; functions are verbs.
- **[All]** Avoid abbreviations; names should be explicit and descriptive.
- **[All]** Keep functions small and single-purpose; avoid deep nesting.

### Documentation

- **[All]** Every public module/class/function has a docstring.
- **[All]** Docstrings emphasize contract:  inputs, outputs, errors, edge cases, examples.
- **[All]** Inline comments explain "why," not "what."

### Error Handling

- **[All]** Prefer exceptions over sentinel values unless explicitly modeling "no result."
- **[All]** Catch narrowly; never use bare `except:` unless re-raising immediately.
- **[All]** Errors must be actionable: include context, preserve original exceptions (`raise ...  from e`).

### Types, Testing, and Tooling

- **[Baseline]** Use type hints opportunistically for public APIs and complex structures.
- **[Modern]** Type hints are expected broadly; run static checking (e.g., mypy/pyright) in CI.
- **[All]** Tests required for non-trivial logic; prefer `pytest` unless repo standard differs.

## Baseline vs Modern-Advanced Mode

### Baseline Mode (Default)

Use this mode unless the project's constraints clearly require modern-only features.

**Goals:**

- Minimal dependencies (stdlib-first).
- Deterministic behavior; explicit control flow.
- Easy to read without specialized tooling.

**Rules:**

- Avoid metaprogramming, magic decorators, and clever one-liners.
- Prefer explicit loops over heavily nested comprehensions when clarity improves.
- Prefer plain datatypes (`dict`, `list`, `tuple`) over heavy frameworks for simple tasks.
- Keep I/O boundaries obvious (pure functions where possible; isolate side effects).

### Modern-Advanced Mode (When Required)

Use when:

- The repo depends on modern frameworks (FastAPI, Pydantic, async stacks, etc.).
- The domain benefits from stronger contracts (rich types, schemas, validation).
- Performance or concurrency requirements demand modern primitives.

**Rules:**

- Use type hints pervasively (inputs/outputs, key variables in complex logic).
- Prefer `pathlib. Path` over `os.path` for paths.
- Use `logging` (structured if available) instead of `print`.
- For async:  prefer `async`/`await`, `anyio`/`asyncio` patterns; keep sync/async boundaries explicit.
- Raise domain-specific exceptions where helpful.

## Code Layout and Formatting

- Indentation: 4 spaces, no tabs.
- Imports:
  - Group as:  standard library, third-party, local.
  - Within each group: alphabetical, one import per line when reasonable.
  - Avoid wildcard imports.

Example:

```python
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

import requests

from myproject.core.models import Requirement
```

## Naming Conventions

- Functions: `verb_noun` (e.g., `parse_markdown`, `build_index`, `validate_input`).
- Classes: `NounPhrase` (e.g., `RequirementGraph`, `DesignAnalyzer`).
- Variables: explicit, non-abbreviated (e.g., `requirements_text`, not `req_txt`).
- Boolean variables: `is_`, `has_`, `should_` prefixes (e.g., `is_valid`, `has_errors`).

## Documentation and Comments

### Docstrings

Use docstrings for all public interfaces.  Prefer a consistent, readable style:

- Short summary line.
- Longer description if needed.
- Arguments, returns, raises.
- Examples for tricky behavior.

Example:

```python
def parse_requirements_markdown(markdown_text: str) -> list[str]:
    """
    Parse requirements from a markdown document.

    Args:
        markdown_text: Raw markdown content.

    Returns:
        A list of normalized requirement strings.

    Raises:
        ValueError:  If the markdown is empty or cannot be parsed.
    """
```

### Inline Comments

- Explain rationale and invariants.
- Avoid narrating obvious code.

## Error Handling

- Raise specific exceptions (`ValueError`, `KeyError`, `TypeError`, or custom domain exceptions).
- Always add context.  Preserve the original exception when wrapping:

```python
try:
    parsed = json.loads(text)
except json.JSONDecodeError as error:
    raise ValueError(f"Invalid JSON in requirements file: {path}") from error
```

- Never swallow errors silently.  If you must continue, log at `debug` or `warning` with rationale.

## Logging and Output

- Use `logging` for non-test code.  Do not use `print` except in CLI entrypoints.
- Logging messages must be human-actionable and include identifiers/paths when relevant.

## Data Modeling

### Baseline

- Prefer `dataclasses` for lightweight models.
- Avoid "magic" model behavior unless it clearly reduces complexity.

### Modern

- If using Pydantic or similar, enforce schema boundaries at the edges (I/O) and keep the core logic mostly framework-agnostic.

## Filesystem and Paths

- Prefer `pathlib.Path`.
- Avoid relying on current working directory; resolve paths from a clear root (e.g., repo root or config).

## Tests

- Non-trivial logic must have tests.
- Tests should be deterministic and not depend on network unless explicitly marked/integration-only.
- Prefer table-driven tests for parsing/validation logic.

## Performance and Safety

- Prefer clarity first; optimize only when needed and measured.
- Avoid quadratic algorithms in obvious hot paths (parsers, matchers, large loops).
- Validate untrusted input at boundaries; never `eval`.

## "Done" Definition for Python Changes

A PR/commit is considered complete when:

- **All pre-commit hooks pass** (Black formatting, Ruff linting, trailing whitespace, etc.).
  - Run `pre-commit run --all-files` locally before pushing.
  - Pre-commit hooks may modify files (auto-fix formatting/linting). Always review and commit these changes before pushing.
  - **If pre-commit CI fails:** Pull the branch, run `pre-commit run --all-files`, commit fixes, and push again.
- Code conforms to this style guide.
- Public APIs have docstrings.
- Errors are explicit and actionable.
- Tests exist for core logic and pass locally/CI.
- No debug prints; logging is appropriate for runtime visibility.
- All CI checks must pass.
