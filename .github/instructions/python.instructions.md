---
applyTo: "**/*.py"
description: "Python coding standards:  portability-first by default, modern-advanced when the stack requires it."
---

<!-- markdownlint-disable MD013 -->

# Python Writing Style

**Version:** 1.10.20260727.0

## Metadata

- **Status:** Active
- **Owner:** Repository Maintainers
- **Last Updated:** 2026-07-27
- **Scope:** Defines Python coding standards for all Python files in this repository, including modules, scripts, tests, and tooling. Covers style, structure, error handling, testing, and documentation requirements.
- **Related:** [Repository Copilot Instructions](../copilot-instructions.md)

## Purpose and Scope

This guide establishes the Python coding standards for the repository.  Code **MUST** be maintainable, deterministic, and security-conscious.  The style adapts to project constraints:  **stdlib-first, portability-first** by default, shifting to **modern-advanced** when required by the technology stack (async frameworks, type-heavy APIs, etc.).

> **Note:** This document uses [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) keywords (**MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, **MAY**) to indicate requirement levels.

## Executive Summary:  Author Profile

The default style is a highly disciplined **stdlib-first, portability-first** approach.  When code can reasonably run on a minimal, widely available Python baseline, it **SHOULD**:  minimize dependencies, avoid unnecessary metaprogramming, and prefer clarity over cleverness.

This baseline is not dogma.  When external constraints require modern Python (e.g., `typing`-heavy APIs, async I/O, Pydantic models, FastAPI), the style intentionally shifts to a **modern-advanced** posture.

## Quick Reference Checklist

### Layout and Formatting

- **[All]** **MUST** use 4 spaces; never tabs.
- **[All]** **MUST** follow PEP 8/PEP 257; line length target **<= 100** (**MAY** exceed for URLs/long strings when readability wins).
- **[All]** **MUST** keep formatting tool-friendly: **MUST NOT** hand-align with extra whitespace.
- **[All]** **SHOULD** use f-strings for interpolation; **SHOULD NOT** use `%` or `.format()` formatting except when required.
- **[All]** **SHOULD NOT** rely on same-line implicit concatenation of adjacent string literals such as `f"a " "b"` or `"a" "b"`, and **SHOULD NOT** mix an f-string with an adjacent plain literal on the same line; a missing comma silently concatenates instead of erroring. Prefer one f-string or plain literal, and reserve adjacency for intentional multi-line wrapping described below.
- **[All]** **MUST NOT** include trailing whitespace; files **MUST** end with a single newline.

### Naming and Structure

- **[All]** **MUST** use `snake_case` for functions/variables; `PascalCase` for classes; `UPPER_SNAKE_CASE` for constants.
- **[All]** Modules **SHOULD** be nouns; functions **SHOULD** be verbs.
- **[All]** **SHOULD NOT** use abbreviations; names **SHOULD** be explicit and descriptive.
- **[All]** **SHOULD** keep functions small and single-purpose; **SHOULD** avoid deep nesting.

### Documentation

- **[All]** Every public module/class/function **MUST** have a docstring.
- **[All]** Docstrings **MUST** emphasize contract:  inputs, outputs, errors, edge cases, examples.
- **[All]** Inline comments **SHOULD** explain "why," not "what."

### Error Handling

- **[All]** **SHOULD** use exceptions over sentinel values unless explicitly modeling "no result."
- **[All]** **MUST** catch narrowly; **MUST NOT** use bare `except:` unless re-raising immediately.
- **[All]** Errors **MUST** be actionable: **MUST** include context, **MUST** preserve original exceptions (`raise ... from e`).

### Types, Testing, and Tooling

Where the `[This repo]` bullets below state which local command is the authoritative gate, they apply the canonical [Pre-commit Discipline (CRITICAL)](../copilot-instructions.md#pre-commit-discipline-critical) section to Python work; they are interpretations of that section and create no exception to it.

- **[Baseline]** **MAY** use type hints opportunistically for public APIs and complex structures.
- **[Modern]** Type hints are expected broadly; **MUST** run static checking (e.g., mypy/pyright) in CI.
- **[All]** Tests **MUST** exist for non-trivial logic; **SHOULD** use `pytest` unless repo standard differs.
- **[All]** Tests **SHOULD** prefer public seams over monkeypatching private internals.
- **[All]** **SHOULD** use Black for formatting and Ruff for linting.
- **[This repo]** `pre-commit run --all-files` is the authoritative local gate because it runs the pinned hook versions from `.pre-commit-config.yaml`.
- **[This repo]** Targeted pre-commit hook runs, such as `pre-commit run black --all-files` when Python formatting is the only concern, are useful fast checks but **MUST NOT** replace the aggregate `pre-commit run --all-files` gate.
- **[This repo]** Running hook tools directly outside pre-commit, for example `ruff` or `npm run lint:md`, **MAY** help during iteration but **MUST NOT** replace the aggregate gate; type checking (`mypy`) and tests (`pytest`) are enforced separately by the retained Python CI surface for the selected host, such as `.github/workflows/python-ci.yml` for GitHub Actions or `.azuredevops/pipelines/python-ci.yml` for Azure Pipelines.
- **[This repo]** In the active root configuration, Black is the Python formatter enforced by the pinned `psf/black` pre-commit hook, and Ruff is lint-only through `ruff-check`; there is no active `ruff-format` hook and no root `[tool.ruff]` table.
- **[This repo]** The root `[tool.black]` `target-version` list **MUST** stay aligned with the active Python support window to prevent formatter/runtime mismatches and stale syntax allowances, and **MUST** remain explicit so Black does not fall back to inferring unsupported or prerelease Python grammar targets from `[project].requires-python`.
- **[This repo]** `ruff format` **MUST NOT** be used to apply or validate Python formatting unless a future toolchain change explicitly adopts Ruff formatting.
- **[Downstream]** [`templates/python/pyproject.toml`](../../templates/python/pyproject.toml) shows starter `pyproject.toml` configuration for downstream adopters and is distinct from this repository's active root configuration.

### CLI Flag Integrity

- **[All]** CLI flags and meaningful option modes/values **MUST** have a user- or test-verifiable runtime effect; a flag's help text **MUST** match its actual behavior. See [CLI and Argument Handling](#cli-and-argument-handling).

### Single-Source Versioning

- **[All]** Packages and applications that expose a version **MUST** maintain a single source of truth for that version and **MUST NOT** duplicate hard-coded version literals across multiple files (for example, repeating the same `"X.Y.Z"` string in `pyproject.toml`, `__init__.py`, and runtime code). See [Package Versioning](#package-versioning).
- **[All]** For setuptools-based packages in this template, the preferred pattern is to declare the version once in `src/<package>/__init__.py` as `__version__ = "X.Y.Z"` and **SHOULD** reference it from:
  - `pyproject.toml` via dynamic versioning (`dynamic = ["version"]` plus `[tool.setuptools.dynamic] version = { attr = "<package>.__version__" }`).
  - application/runtime metadata by importing `__version__` rather than hard-coding a literal (for example, FastAPI version metadata, a CLI `--version` flag, or HTTP response headers).
- **[All]** If a different build backend or project structure is used, the same single-source-of-truth principle **MUST** still apply, using the backend's equivalent mechanism.
- **[All]** Tests or CI **SHOULD** verify that the packaged/resolved version and the runtime `__version__` remain aligned to prevent drift.

## Baseline vs Modern-Advanced Mode

### Baseline Mode (Default)

Use this mode unless the project's constraints clearly require modern-only features.

**Goals:**

- Minimal dependencies (stdlib-first).
- Deterministic behavior; explicit control flow.
- Easy to read without specialized tooling.

**Rules:**

- **SHOULD** avoid metaprogramming, magic decorators, and clever one-liners.
- **SHOULD** use explicit loops over heavily nested comprehensions when clarity improves.
- **SHOULD** use plain datatypes (`dict`, `list`, `tuple`) over heavy frameworks for simple tasks.
- **SHOULD** keep I/O boundaries obvious (pure functions where possible; isolate side effects).

### Modern-Advanced Mode (When Required)

Use when:

- The repo depends on modern frameworks (FastAPI, Pydantic, async stacks, etc.).
- The domain benefits from stronger contracts (rich types, schemas, validation).
- Performance or concurrency requirements demand modern primitives.

**Rules:**

- **MUST** use type hints pervasively (inputs/outputs, key variables in complex logic).
- **SHOULD** use `pathlib.Path` over `os.path` for paths.
- **SHOULD** use structured logging when available.
- For async:  **SHOULD** use `async`/`await`, `anyio`/`asyncio` patterns; **MUST** keep sync/async boundaries explicit.
- **MAY** raise domain-specific exceptions where helpful.

## Code Layout and Formatting

- Indentation: **MUST** use 4 spaces, no tabs.
- Imports:
  - **MUST** group as:  standard library, third-party, local.
  - Within each group: **SHOULD** sort alphabetically, one import per line when reasonable.
  - **MUST NOT** use wildcard imports.

Example:

```python
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

# import third_party_package  # Third-party imports go here

from myproject.core.models import Requirement
```

### String Literal Concatenation

Code **SHOULD** prefer a single f-string or plain string literal when readable. Same-line adjacency that can hide a likely missing comma **SHOULD NOT** be used, including adjacent f-string and plain-literal fragments on the same line.

When a string exceeds the 100-character line target or readability requires splitting, code **MAY** wrap intentional implicit concatenation in explicit parentheses with each fragment on its own line and clearly delimited. When interpolation is involved, keep wrapped fragments homogeneous, such as all f-strings. Code **MAY** also use explicit construction such as `"".join(...)` when that is clearer. Intentional, clearly delimited multi-line implicit concatenation purely for line length is acceptable; wrapping is an option, not a requirement, and long strings **MAY** remain on one line when readability wins.

Compliant example:

```python
message = f"Collected {n} items found."
```

Non-compliant counter-example:

```python
message = f"Collected {n} items " "found."
```

## Naming Conventions

- Functions: **SHOULD** use `verb_noun` (e.g., `parse_markdown`, `build_index`, `validate_input`).
- Classes: **SHOULD** use `NounPhrase` (e.g., `RequirementGraph`, `DesignAnalyzer`).
- Variables: **MUST** be explicit, non-abbreviated (e.g., `requirements_text`, not `req_txt`).
- Boolean variables: **SHOULD** use `is_`, `has_`, `should_` prefixes (e.g., `is_valid`, `has_errors`).

## Documentation and Comments

### Docstrings

**MUST** use docstrings for all public interfaces.  **SHOULD** use a consistent, readable style:

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

- **SHOULD** explain rationale and invariants.
- **SHOULD NOT** narrate obvious code.

## Error Handling

- **MUST** raise specific exceptions (`ValueError`, `KeyError`, `TypeError`, or custom domain exceptions).
- **MUST** always add context.  **MUST** preserve the original exception when wrapping:

```python
try:
    parsed = json.loads(text)
except json.JSONDecodeError as error:
    raise ValueError(f"Invalid JSON in requirements file: {path}") from error
```

- **MUST NOT** swallow errors silently.  If you must continue, **MUST** log at `debug` or `warning` with rationale.
- **SHOULD NOT** interpolate an `OSError`-derived exception directly into user-facing output. User-facing output includes CLI output written to stdout/stderr, generated reports, warnings emitted to a user-visible terminal, and any log line intended to be pasted, shared, or quoted verbatim into bug reports, GitHub issues, or chat. For `OSError` and subclasses such as `FileNotFoundError`, `PermissionError`, `IsADirectoryError`, and `NotADirectoryError`, **SHOULD NOT** use `str(error)`, `f"{error}"`, `error.filename`, or `error.filename2` directly in those surfaces, because the default string form and filename attributes can expose absolute local filesystem paths.
- **SHOULD** report `OSError`-derived failures in user-facing output with the exception class name plus a short human-readable cause derived from `error.strerror`, using a non-`None` fallback because `strerror` may be `None` for some `OSError` instances:

  ```python
  error_summary = f"{type(error).__name__}: {error.strerror or 'I/O error'}"
  ```

  Callers **MAY** include a deliberately chosen safe path representation in the surrounding message, such as a repo-relative path, configured display name, or otherwise sanitized path. This rule only forbids deriving that path from the exception's default string form or from `filename` / `filename2`. Internal-only diagnostics, such as `DEBUG`-level logs that never reach end users, **MAY** continue to log the full exception via `logger.exception(...)` or `str(error)`.

## Logging and Output

- **MUST** use `logging` for non-test code.  **MUST NOT** use `print` except in CLI entrypoints.
- Logging messages **MUST** be human-actionable and **SHOULD** include identifiers/paths when relevant.

### Rendering Commands for Humans

When rendering a command line that a human is expected to read, copy, or paste, including CLI output, generated reports, and suggested manual remediation commands, code **SHOULD** quote for the intended command-line surface. The intended surface is usually the current host, but code that renders commands for a different shell or platform **SHOULD** declare that target explicitly and quote for that target. This guidance covers human-facing rendering only; constructing a command the program will execute is out of scope.

- For POSIX / Unix-shell-facing full command strings built from an argument vector, use `shlex.join()` (added in Python 3.8).
- On Windows, when rendering the argv-style command line that matches Python's `subprocess` behavior, use `subprocess.list2cmdline()` behind an `os.name == "nt"` branch. This gives display parity with Python's Windows argument conversion.
- Code **SHOULD NOT** use `subprocess.list2cmdline()` unconditionally for POSIX-facing command strings, because it applies Windows / MS C runtime quoting rules.
- Code **SHOULD NOT** present `subprocess.list2cmdline()` output as paste-safe for a Windows shell. If output must target PowerShell, `cmd.exe`, or another specific Windows shell, quote per that shell's own rules or do not label the rendered string paste-safe.
- For POSIX-facing single-token rendering, use `shlex.quote()` rather than adding quotes manually. This is not Windows-shell guidance.

Compliant example:

```python
import os
import shlex
import subprocess
from collections.abc import Sequence


def format_command(command: Sequence[str]) -> str:
    """Return a platform-appropriate display string for an argument vector."""
    command_parts = list(command)
    if os.name == "nt":
        return subprocess.list2cmdline(command_parts)
    return shlex.join(command_parts)
```

Non-compliant counter-example:

```python
import subprocess
from collections.abc import Sequence


def format_command(command: Sequence[str]) -> str:
    """Return a command string."""
    return subprocess.list2cmdline(command)
```

### Secrets in User-Facing Output

The bullets below state how the canonical [Non-negotiable Safety and Security Rules](../copilot-instructions.md#non-negotiable-safety-and-security-rules), item 1 "No secrets in code or repo", applies to Python output surfaces. That rule requires "Never print secrets to stdout/stderr or logs"; where the bullets scope a requirement to the URL user-info component, or permit leaving an SCP-style remote intact, they are interpretations of that rule and create no exception to it.

- When rendering Git remote URLs, URL-form connection strings, or other `scheme://userinfo@host/path` (or scheme-relative `//userinfo@host/path`) values into user-facing output, using the same surfaces described for the `OSError` guidance above (CLI output written to stdout/stderr, generated reports, warnings emitted to a user-visible terminal, or text intended to be copied, pasted, shared, or quoted), code **MUST** redact the entire URL user-info component before display. The user-info component can be `user`, `user:password`, or a bare token. Replace `userinfo@` with a redaction marker such as `***@` while preserving the scheme, host, port, path, query string, and fragment unless those other components are independently known to contain secrets. For example, `https://maintainer:token@github.com/org/repo.git` should render as `https://***@github.com/org/repo.git`.
- If a value cannot be parsed safely (for example, a malformed IPv6 authority that raises `ValueError`), prefer fail-safe redaction over returning the raw value — redact the user-info even when that drops non-secret components such as the scheme.
- SCP-style SSH remotes such as `git@github.com:org/repo.git` **MAY** be left intact because they are not URI-authority URLs and cannot embed a password in the same `scheme://userinfo@host` form.
- This rule covers URL user-info redaction only. It does not authorize preserving known secrets elsewhere in a value, such as secret query parameters. Known credentials, tokens, passwords, and secrets **MUST** still be omitted or redacted under the repo-wide no-secrets rule.

Compliant example:

```python
from urllib.parse import urlsplit, urlunsplit


def redact_url_userinfo(value: str) -> str:
    """Redact URL user-info before displaying a URL-like value."""
    try:
        parsed = urlsplit(value)
    except ValueError:
        # Unparseable input (for example, malformed IPv6): redact defensively
        # instead of risking a leak by returning the raw value.
        if "@" not in value:
            return value
        return f"***@{value.rsplit('@', maxsplit=1)[1]}"
    if not parsed.netloc or "@" not in parsed.netloc:
        return value

    safe_netloc = f"***@{parsed.netloc.rsplit('@', maxsplit=1)[1]}"
    return urlunsplit((parsed.scheme, safe_netloc, parsed.path, parsed.query, parsed.fragment))


assert (
    redact_url_userinfo("https://maintainer:token@github.com/org/repo.git")
    == "https://***@github.com/org/repo.git"
)
assert redact_url_userinfo("git@github.com:org/repo.git") == "git@github.com:org/repo.git"
assert redact_url_userinfo("https://user:secret@[::1/path") == "***@[::1/path"
assert redact_url_userinfo("//user:token@host/path") == "//***@host/path"
```

## CLI and Argument Handling

Command-line flags and options are part of the program's user-facing contract. A flag or option **MUST** have a user- or test-verifiable runtime effect under at least one applicable input state. It need not produce a different result for every possible input. For example, `--fix` may have nothing to rewrite when there are no findings, but it **MUST** select behavior that can rewrite files, change output, change an exit code, change validation scope, or otherwise affect the result when fixes are available.

Observable effects include changed output, changed side effects such as filesystem writes, network/API calls, or subprocess calls, changed exit codes, or changed validation scope, such as the set of inputs or rules the command validates. A code branch counts only when it produces one of these effects, whether immediately or through a value recorded at parse time and acted on later. A branch with no externally observable or testable difference does not count, except for a deliberately retained compatibility flag documented under the compatibility rule below.

For options with enumerated values, boolean modes, or named modes, each non-default value or meaningful mode choice **MUST** be reachable in the runtime code path. For free-form value options such as paths, package names, branch names, or URLs, the supplied value **MUST** be used by the behavior the option documents. Explicitly selecting the default value **MAY** behave the same as omitting the option.

A flag that only validates or echoes its own parsed value, such as printing `mode: check` while running the same plan for every mode, is a prohibited no-op unless it is a deliberately retained compatibility flag documented under the compatibility rule below.

A flag's advertised help or usage text **MUST** accurately describe the flag's actual runtime effect and **MUST NOT** imply a different command plan, output, side effect, validation scope, or exit behavior than the code implements. This applies however the help or usage text is produced: an `argparse` `help=` string, the equivalent in `click` or `typer`, generated command help, or any other usage text the program presents.

When mutually exclusive modes, such as `--check` / `--fix` or planning versus writing modes, differ in user-facing meaning, that difference **MUST** be reachable in the runtime code path through output, side effects, exit code, or validation scope, whether produced immediately or through a command plan acted on later. Using `argparse`'s `add_mutually_exclusive_group()`, even when created with `required=True`, enforces only parse-time exclusivity and does not by itself satisfy this runtime-difference requirement. Mode-dependent guidance printed by the tool **SHOULD** reflect the active mode.

Informational and diagnostic flags satisfy the observable-effect rule only when their documented effect is implemented. `--help` and `--version` are compliant when they print the requested information and exit. `--dry-run` is compliant when it reports the plan without performing the normal side effects. `--verbose` is compliant when it changes verbosity or diagnostics. Such a flag is non-compliant if it is parsed but does not produce its documented behavior.

A deliberately retained no-op or deprecated flag **MAY** exist only as a compatibility bridge. This is an exception only to the requirement that the flag change normal command behavior; it is not an exception to truthful documentation. The flag's no-effect or deprecated status **MUST** be disclosed in the help or usage text the flag exposes or, for a flag that intentionally suppresses its help, in release notes or a changelog, consistent with the help-accuracy rule above.

Such a flag **SHOULD** additionally surface its retained-for-compatibility behavior at runtime when that will not break reasonable scripted usage, for example with a clear CLI warning on stderr, or with Python warning categories such as `DeprecationWarning` or `FutureWarning` when those are appropriate for the audience and visible under the tool's warning policy.

This rule applies regardless of parser library. Examples **MAY** use `argparse` because it is the standard-library parser and matches this guide's stdlib-first default. Tests for non-trivial CLI behavior **SHOULD** follow the mode-coverage guidance in [Tests](#tests).

Compliant example:

```python
parser.add_argument(
    "--fix",
    action="store_true",
    help=(
        "Rewrite files in place and exit zero after applying fixes; by default, "
        "only report problems and exit non-zero when problems are found."
    ),
)
args = parser.parse_args()
problems = run_checks(paths)
if args.fix:
    apply_fixes(problems)
    raise SystemExit(0)

raise SystemExit(1 if problems else 0)
```

Non-compliant counter-example:

```python
parser.add_argument(
    "--mode",
    choices=["check", "fix"],
    default="check",
    help="Apply fixes when set to 'fix'.",  # Help promises fixes.
)
args = parser.parse_args()
print(f"Running in {args.mode} mode")
run_checks(paths)  # Identical work regardless of --mode; no fixes are ever applied.
```

## Data Modeling

### Baseline

- **SHOULD** use `dataclasses` for lightweight models.
- **SHOULD** avoid "magic" model behavior unless it clearly reduces complexity.

### Modern

- If using Pydantic or similar, **SHOULD** enforce schema boundaries at the edges (I/O) and keep the core logic mostly framework-agnostic.

## Filesystem and Paths

Where the bullets below state how the repo-wide rule "Refuse path traversal and symlink escapes" in [`.github/copilot-instructions.md`](../copilot-instructions.md) § "Non-negotiable Safety and Security Rules" item 3, "Allowlisted file access only", applies to Python code, they are interpretations of that rule and create no exception to it.

**When the obligations in this section bind.** The canonical rule attaches to *allowlist-governed access* — "Read only explicitly allowed inputs/config/rules files and tool-owned runtime dependencies" — and then states "Refuse path traversal and symlink escapes" without qualification. The obligations below therefore bind on that axis, **not** on whether the path's *name* arrived from untrusted input. They apply whenever **either** of the following holds:

- the access is governed by the allowlist described in the canonical rule, **or**
- any party less privileged than the running process, or any party the process does not fully trust, can create or replace that path or any of its ancestors.

Where a bullet below says "untrusted, repo-supplied, or otherwise externally influenced," read it as that test. The practical question is: *could anyone you do not fully trust place a symlink at this path, or at any directory above it?* A path is **not** exempt because the code classifies it as trusted, local, or developer-supplied. [CWE-59](https://cwe.mitre.org/data/definitions/59.html) is about what a name resolves to, not where the name came from, and [SEI CERT POS01-C](https://wiki.sei.cmu.edu/confluence/x/9NYxBQ) keys the risk to whether the process runs with privileges the link's creator lacks.

**Missing security flags are stop conditions, not zero-defaults.** When a flag whose absence would weaken a security guarantee is not available at runtime — `O_NOFOLLOW` and `O_DIRECTORY` in the trusted-root descent below are the recurring examples — probe for it with `hasattr(os, "FLAG")` and, on absence, route to the platform's equivalent safe primitive or fail the operation. Such a flag **MUST NOT** be supplied through `getattr(os, "FLAG", 0)` or an equivalent `| 0` fallback: a `0` in a bitmask `OR` is a no-op, so the protection silently disappears while the surrounding code continues to assert it holds. This is the general rule that the `O_NOFOLLOW` handling below instantiates; apply it to any future security-required flag as well. It does **not** govern flags that are merely optimizations (for example a performance hint), whose absence changes speed rather than a security property.

- **SHOULD** use `pathlib.Path`.
- *Note on Python version callouts in this section:* the bullets below intentionally cite minimum Python versions for specific APIs (for example `Path.is_relative_to()` on 3.9+ and `Path.walk(...)` on 3.12+) even though this repository's own `pyproject.toml` currently sets `requires-python = ">=3.13"`. These callouts exist for **portability**, consistent with this guide's "portability-first by default" posture (see *Executive Summary*), so that downstream projects which adopt these instructions on a lower Python baseline still receive correct guidance. Projects whose own baseline is 3.13+ **MAY** simplify call sites to the 3.13+ form (for example, always using `is_relative_to(...)` and `Path.walk(follow_symlinks=False)`), but **MUST NOT** weaken the underlying symlink-rejection or containment requirements.
- When checking whether an expected regular file is present, such as before deciding whether the file already exists for create or replacement logic or before reporting it as "present", "found", or "missing", code **SHOULD NOT** use `Path.exists()` as the success criterion. Code **SHOULD** use `Path.is_file()` or an equivalent regular-file check. `Path.exists()` remains acceptable when the intended contract is "any filesystem entry exists at this path" or as a diagnostic after an expected-file check fails.
- When a path exists but is not the expected regular file, code **SHOULD** surface that state explicitly rather than treating the path as the expected file. Create, write, or replacement workflows **SHOULD** raise or block with an actionable error; read-only presence reporting **MAY** report the path as missing or as the wrong kind, but **SHOULD NOT** report it as the expected file.
- In untrusted, repo-supplied, or otherwise externally influenced contexts, individual expected-file checks **MUST** keep the symlink-rejection and containment protections required by this section. Existing candidates **MUST** reject symlinks explicitly, such as `not path.is_symlink() and path.is_file()`, or use an equivalent no-follow regular-file check supported by the active Python baseline, and **MUST** verify resolved-path containment against the trusted root. For create, write, or replacement workflows where the target may not exist yet, a separate check-then-write step is insufficient on its own: callers **MUST** validate the parent and intended target path against the trusted root and perform the write through a symlink-safe, race-resistant pattern, such as an atomic, no-follow write where the platform supports it.
- This individual-path presence guidance is a correctness and robustness idiom separate from the recursive and non-walk filesystem-discovery requirements below. The `Path.is_file()` preference is **SHOULD**-level for general correctness. The symlink-rejection and containment obligations above are **MUST**-level for every access that meets the test at the top of this section, whether or not the code classifies the path as trusted, local, or developer-supplied. Only where that test is not met — no allowlist-governed access, and no less-privileged or untrusted party able to create or replace the path or an ancestor — does this rule stop requiring rejection of symlinked regular files, and even then the path contract may forbid symlinks on its own terms.
- Create, write, replace, and rename workflows **MUST** be symlink-safe regardless of how the target path is classified. The dangerous operation in this class is the rewrite, not the read: [CVE-2026-28684](https://nvd.nist.gov/vuln/detail/CVE-2026-28684) in `python-dotenv` (fixed in 1.2.2) is a local arbitrary-file-overwrite in `set_key()`/`unset_key()` caused by following a symlink while rewriting a `.env` file — a path nearly every project treats as trusted local configuration, and therefore exactly the case a trust-based reading would have exempted. Validate the parent and the intended target against the trusted root before writing, then use the pattern that matches the operation. `O_NOFOLLOW` does not exist on Windows, so probe for it with `hasattr(os, "O_NOFOLLOW")` rather than assuming it is present — and where a workflow in this section depends on no-follow semantics, the flag's absence is a **stop condition** that routes to the platform's equivalent safe primitive or fails the operation, never a silent `getattr(..., 0)` substitution: OR-ing `0` into the flags turns every open into a symlink-following open while the surrounding code continues to claim no-follow behavior.

    **The normative requirement is the threat model, not the choreography.** Whatever implementation performs this workflow **MUST** defeat every threat in the following list, each of which is a real defect this pattern was refined to close: (1) a symlink or ancestor redirect inserted between a containment check and a later open; (2) time-of-check/time-of-use races across validation, metadata capture, and the final rename; (3) substitution of a temporary name or staging directory that a less-privileged principal can reach; (4) poisoning of the destination's captured metadata by replacing the destination entry before it is read; (5) exposure of secret content during the write window through the file's mode or through inherited ACL entries; (6) loss of the set-user-ID/set-group-ID bits, file capabilities, POSIX ACLs, or security labels across the ownership and mode changes; and (7) denial of service when the validation open blocks on an attacker-substituted FIFO. Code **MUST** use an implementation covered by an adversarial test with at least one case per threat above, and **MUST** treat a missing test as a missing defense. Code **MUST NOT** transcribe the walkthrough below into hand-rolled logic and treat that as sufficient: prose cannot be executed, and this walkthrough accumulated defects across more than a dozen review passes precisely because English has no compiler and no test suite. No maintained general-purpose Python library is known to cover this full model — `atomicwrites`, the most maintained option, performs a same-directory temporary write plus `os.replace` with an overwrite guard and does not perform trusted-root descent, metadata preservation, or ACL handling — so "use a library" is not on its own sufficient; the chosen implementation **MUST** be verified against the threat list above. What follows, through the Windows-fallback paragraph, is a **non-normative illustrative walkthrough** of how a correct implementation reasons about each threat. It is reference material for building or reviewing a tested implementation, not a specification to copy by hand.
  - **Create-only.** `os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW` refuses to follow a symlink at the final component and fails if any entry already exists there (probe for `O_NOFOLLOW` per the stop-condition rule above; `O_EXCL` alone already refuses an existing symlink at the final component, but the no-follow guarantee for the rest of this pattern still requires the real flag). Open it **relative to a directory handle descended from the trusted root**, exactly as the replacement case below requires, and pass an explicit restrictive `mode`. Resolving the path by name after a containment check leaves the same ancestor-redirect window, and omitting `mode` starts from `0o777`, yielding `0o755` under a typical `0o022` umask — so a newly created secret would be world-readable. Neither hazard is specific to replacement.
  - **Replacement**, which is what the `.env` case above actually is. The create-only flags **MUST NOT** be adapted for replacement by dropping `O_EXCL`: `O_EXCL` is what makes the open refuse a pre-existing entry, and removing it reintroduces the symlink-following defect the pattern exists to prevent. Instead, anchor the whole operation to a **directory handle descended from the trusted root**, never to a pathname. Opening the parent by pathname does not qualify, even with `O_NOFOLLOW`: that flag constrains only the final component, so a party who redirects an *ancestor* to an external tree whose last component is a real directory still hands you a valid handle outside the trusted root, and every operation relative to that handle inherits the escape. Start from an independently verified handle on the trusted root and descend one component at a time, opening each with `os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW` and `dir_fd=` the previous handle, so no component is ever resolved through a path an attacker can redirect. The descent's guarantee **is** those flags, so enter it only after probing that both exist (`hasattr`); where either is missing, this route is unavailable — use the platform's equivalent safe primitive or fail, per the fallback paragraph below, rather than substituting `0` and descending anyway. Where the platform offers a beneath-root primitive such as `openat2(RESOLVE_BENEATH)`, prefer it and let the kernel enforce containment.

    When using a **named** temporary file (the `O_TMPFILE` route below needs no name until its final `linkat`), create it with `dir_fd=` **the validated staging subdirectory's descriptor described below — never the destination directory's handle**, the create-only flags, **and an explicit restrictive `mode`**. Every temporary name in this pattern lives in the staging subdirectory; the destination directory receives only the final atomic rename. `os.open()` defaults to `mode=0o777`, so under a typical `0o022` umask a rewritten `0o600` secret would land at `0o755` and become world-readable — a silent privilege downgrade on exactly the `.env`-style files this pattern exists to protect. Create it `0o600` or stricter **regardless of what the destination's mode will be**, and do not pass the destination's mode here. Mode bits are interpreted against the *creating* process's owner and group, not the destination's, so a mode that is safe on the destination can be permissive on the temporary file: replacing a `0o640 root:secrets` file from a process running as `alice:users` would create a `0o640 alice:users` inode, letting every member of `users` read partially written secret content for the whole write window. Capture the destination's intended metadata **by descriptor, after validation — never by trusting the name**: open the existing destination read-only through the held directory handle with `O_NOFOLLOW | O_NONBLOCK`, `os.fstat()` that descriptor, and require the expected regular file with the expected ownership and an access contract no wider than the caller expects. `O_NONBLOCK` is there because the entry is unvalidated at open time: a substituted FIFO would otherwise block the open indefinitely before `os.fstat()` ever runs, turning the validation step into a denial of service against the privileged rewrite. The flag is inert on a regular file, so once `fstat` confirms the type nothing needs undoing. A destination entry that a less-privileged principal could have replaced is attack input, not a contract: blindly inheriting whatever owner, mode, or ACL currently sits at the name lets that principal choose the metadata a privileged rewrite will copy onto the secret — and the read-back verification below would then "verify" against the poisoned snapshot. On any mismatch, stop before capturing anything for reuse. Take every later metadata read for the sequence below (`os.fstat()`, `os.getxattr()` — Python exposes no `fgetxattr`; `os.getxattr` and `os.setxattr` accept an open file descriptor as the path argument — and ACL-by-descriptor where available) from this same opened descriptor, so validation and capture are pinned to one inode, and apply the captured mode **at its ordered position in the metadata sequence below**: that sequence, not this sentence, governs the order.

    A restrictive `mode` is necessary and still not a guarantee of privacy during the write. On filesystems that inherit ACL entries from the parent directory, the requested mode does not bound effective access: OpenZFS's [`aclinherit`](https://openzfs.github.io/openzfs-docs/man/master/7/zfsprops.7.html#aclinherit) property documents that under `passthrough`, "files are created with a mode determined by the inheritable ACEs" — so the temporary inode can be born readable by other principals regardless of the mode passed to `os.open()`, and the pre-rename metadata read-back below runs only after the content is written, which is too late for confidentiality. Prefer an **unnamed inode** where the platform offers one: Linux's `O_TMPFILE` (see [`open(2)`](https://man7.org/linux/man-pages/man2/open.2.html)) creates "an unnamed temporary regular file" in the target directory's filesystem with no name for any other principal to open, so content is written and the whole metadata sequence is applied and verified before the file becomes reachable at all. Open it as `os.O_TMPFILE | os.O_WRONLY`. `hasattr(os, "O_TMPFILE")` is a precondition, not the gate: it reports that Python exposes the flag, not that the destination filesystem supports unnamed files, so **attempt the open and fall back** to the named staging route when it fails with the errors `open(2)` documents for unsupported configurations (`EOPNOTSUPP` for the filesystem, `EISDIR` for a kernel without the feature), while propagating any other failure. The create-only flag set above does **not** carry over to this route: `open(2)` requires `O_TMPFILE` "with one of `O_RDWR` or `O_WRONLY` and, optionally, `O_EXCL`", and "specifying `O_EXCL` in conjunction with `O_TMPFILE` prevents a temporary file from being linked into the filesystem" — that is the deliberate never-named form, and carrying the mandatory `O_EXCL` over would make the naming step below fail by construction. Only after content and metadata are finalized and verified, give the inode a name using the `linkat` route the man page itself documents (`/proc/self/fd/<fd>` with `AT_SYMLINK_FOLLOW`) — onto a temporary name **inside the verified-private staging subdirectory described below, never a name in the destination directory** — and rename that name into place as below. Where `O_TMPFILE` is unavailable, read the effective access metadata back from the just-created **empty** temporary file before writing any secret content, and treat any access beyond the owner as a stop condition. Do **not** tighten the ACL and continue: permission checks happen at open time, so a principal who opened the file during the permissive window keeps that descriptor across any later mode or ACL change and reads everything written afterward. Instead, create a fresh subdirectory under the already-held directory handle and validate it **by descriptor before first use**: open it through the held handle with `O_DIRECTORY | O_NOFOLLOW`, `os.fstat()` that descriptor, and require **both** that the owner is the creating process's own effective UID **and** that its effective ACL is owner-only. The ownership check is not optional: a principal who can write the destination directory can rename the empty staging directory away in the window after `mkdir` and substitute their own `0o700` directory — which passes a shape-only "owner-only" check with the *attacker* as the owner, handing them every temporary name created afterward. Ownership is what a substitution cannot forge. Every subsequent staging operation goes through this validated descriptor (`dir_fd=` it), never by re-resolving the staging name. With that established, create the temporary file inside it — inheritance is applied at creation, so a file born under a validated-private parent is born private, there is nothing in the window for another principal to pre-open, and a directory descriptor obtained earlier does not bypass the new file's own access check — then rename through from there, or fail the operation. The metadata sequence and pre-rename read-back below are unchanged; this paragraph governs the window before and during the write, which that later verification cannot reach.

    The temporary **name** is a target of its own. `os.replace()` renames whatever inode the source name refers to *at rename time*, so a temporary name in a directory that any less-privileged principal can write reopens the race the handle descent closed: between naming the verified inode and renaming it, that principal can unlink the name and substitute an arbitrary file or symlink, and the rename installs the substitute under the just-verified identity. Both routes therefore keep the temporary name **inside the verified-private staging subdirectory** — owner-only, so no other principal can touch the name — and move it into place with `os.replace(tmp_name, dest_name, src_dir_fd=staging_dir_fd, dst_dir_fd=dest_dir_fd)`: the **staging** directory's handle for the source, the destination directory's handle for the target. The staging subdirectory sits under the destination directory, so the rename stays within one filesystem and remains atomic. Reject a symlinked destination before replacing. Probe support with `os.open in os.supports_dir_fd` and **`os.rename in os.supports_dir_fd`**: `os.replace` is *not* a member of that set even where its `src_dir_fd`/`dst_dir_fd` parameters work, because it shares the underlying `renameat` with `os.rename`, so probing on `os.replace` itself reports a false negative. Preserving mode is necessary but not sufficient: `os.replace()` installs a **new inode**, so ownership, POSIX ACLs, extended attributes, and any security label on the destination do not survive it. Where the file's access contract depends on those, read them from the destination before the swap and reapply them to the new file before the rename, or fail the operation — and order those steps so that each one runs after whatever would otherwise clobber it, then **verify the result before the rename**.

    Two clobbering relations are documented and set the order. Changing ownership clears the set-user-ID and set-group-ID bits and every file capability set: [`chown(2)`](https://man7.org/linux/man-pages/man2/chown.2.html) specifies that "when the owner or group of an executable file is changed by an unprivileged user, the S_ISUID and S_ISGID mode bits are cleared", that "since Linux 2.2.13, root is treated like other users" so running privileged buys no exemption, and that "when the owner or group of an executable file is changed (by any user), all capability sets for the file are cleared". Changing the mode can destroy ACLs: on OpenZFS the dataset's [`aclmode`](https://openzfs.github.io/openzfs-docs/man/master/7/zfsprops.7.html#aclmode) property makes `chmod(2)` either `discard` "all ACEs except for those representing the mode of the file or directory requested by chmod(2)", `groupmask` every ALLOW entry down to the chmod's group permissions, or — under `restricted` — fail outright on a file carrying a non-trivial ACL. Two of those three lose the ACL silently.

    That gives `os.fchown()` first; then capability and other security extended attributes, which the ownership change would otherwise have cleared; then `os.fchmod()`; then ACLs, which the mode change would otherwise have discarded or masked. **Do not treat that sequence as sufficient on its own.** Mode and ACL semantics interact differently across filesystems, and on POSIX-ACL systems setting an access ACL rewrites the mode's group bits in turn, so the last write can invalidate an earlier one in either direction. Read the metadata back from the new file after the final mutating step, compare it against what was captured from the destination, and **fail the operation rather than renaming** when they do not match. Silently replacing a secret with an inode that a different principal owns, or that has lost its ACL, is the same class of exposure as widening its mode — and a fixed order asserted without verification is how that happens.

    Directory-handle operations are POSIX-only. Where they are unavailable, use the platform's equivalent safe primitive — on Windows, open the destination directory and operate relative to that handle with `FILE_FLAG_OPEN_REPARSE_POINT` semantics, or use an API that refuses reparse points. If no such primitive is available, **fail the operation** and surface an actionable error. Do not fall back to the pathname form and record a residual race: this section requires create, write, replace, and rename workflows to be symlink-safe, and a pathname-based containment check can be invalidated between the check and the write by replacing an ancestor, which is exactly the arbitrary-overwrite this pattern exists to prevent.
- Where a path contract legitimately permits a symlinked component — macOS `/tmp` resolving to `/private/tmp`, container bind-mount layouts, virtual environments, or developer workspaces under a symlinked home directory — code **MAY** accept the symlink, but **MUST** still verify resolved-path containment against the trusted root. A carve-out for symlink *rejection* is never a carve-out for *containment*.
- **MUST NOT** follow symbolic links during recursive directory discovery in code that processes untrusted, repo-supplied, or otherwise externally influenced fixtures, configuration, or input files. Prefer explicit traversal with `os.walk(directory, followlinks=False)` or `base_path.walk(follow_symlinks=False)` on Python 3.12+ (where `base_path` is a concrete `pathlib.Path` instance). Prune or skip entries that are symlinks — for `os.walk` and `pathlib.Path.walk`, which both yield directory and file *names* as strings relative to the per-iteration directory, test by joining `name` to that per-iteration directory: `os.path.islink(os.path.join(dirpath, name))` for `os.walk`, or `(dirpath / name).is_symlink()` for `Path.walk` (where `dirpath` is the `Path` yielded by the current iteration); when using `os.scandir`, test `entry.is_symlink()` on the `os.DirEntry`. Verify each yielded path remains under the declared discovery root by comparing resolved paths on the candidate path instance, e.g. `candidate.resolve().relative_to(base_path.resolve())` (which raises `ValueError` when `candidate` is outside `base_path` — callers **MUST** handle that as a containment failure), or use an equivalent safe boundary check.
- **MUST** validate the discovery root (`base_path`) itself before walking. In addition to the per-yielded-path containment check, callers **MUST** verify that `base_path.resolve()` is contained within `trusted_root.resolve()`, where `trusted_root` is an independently determined allowlisted root, such as `REPO_ROOT`, `PROJECT_ROOT`, or a configured root, and is not derived from `base_path`. Use a concrete, unambiguous containment check on the resolved paths — for example `base_path.resolve().is_relative_to(trusted_root.resolve())` on Python 3.9+, or `base_path.resolve().relative_to(trusted_root.resolve())` (catching `ValueError` and treating it as a containment failure) — and **MUST NOT** fall back to string-prefix comparisons such as `str(base_path).startswith(str(trusted_root))`, which are vulnerable to sibling-directory false positives (for example `/srv/data-evil` vs. `/srv/data`) and to separator/normalization mismatches. This discovery-root validation **MUST NOT** be anchored against `base_path` itself (for example `base_path.resolve().is_relative_to(base_path.resolve())`, which is trivially true), because `base_path.resolve()` follows any symlink at or above the discovery root and a self-anchored check can silently accept a `base_path` that re-anchors to an external target. Note that this prohibition is specifically about the **discovery-root check**: the per-yielded-entry containment check in the previous bullet *is* expressed relative to `base_path` (for example `candidate.resolve().relative_to(base_path.resolve())`), and remains correct **once `base_path` itself has been independently validated against `trusted_root`** as required here. `os.walk(..., followlinks=False)` and `base_path.walk(follow_symlinks=False)` on Python 3.12+ only refuse to descend into symlinked subdirectories; they do not detect the case where `base_path` is itself a symlink, or has a symlinked ancestor, pointing outside the trusted area. Refuse discovery if the resolved-root containment check fails.
- **SHOULD** additionally reject discovery roots whose ancestor chain from `trusted_root` down to `base_path` contains symlinks, as a stricter defense-in-depth posture for high-sensitivity inputs. **SHOULD**, not **MUST**, is used here because legitimate environments can have symlinked ancestors, such as macOS `/tmp` → `/private/tmp`, container bind-mount layouts, or developer workspaces under symlinked home directories.
- **MUST** apply the same symlink and containment guidance to non-walk discovery APIs, not only recursive directory discovery, and to *every* discovered entry regardless of whether it is a file or a directory. Entries returned by `base_path.glob(...)`, `base_path.rglob(...)`, `os.scandir(base_path)`, or `os.listdir(base_path)` in untrusted, repo-supplied, or externally influenced discovery contexts **MUST** be rejected by a per-entry symlink check such as `Path.is_symlink()`, `os.path.islink(...)`, or `os.DirEntry.is_symlink()`, and the resolved candidate **MUST** remain contained within the same `trusted_root` introduced above using the same concrete check (for example `candidate.resolve().is_relative_to(trusted_root.resolve())` on Python 3.9+, or `candidate.resolve().relative_to(trusted_root.resolve())` with `ValueError` handled as a containment failure). Note that `os.listdir(base_path)` yields bare entry *names* and that `os.scandir` yields `os.DirEntry` objects whose `name` attribute is also a bare name; **if you are operating on the bare name** (the result of `os.listdir(...)` or `DirEntry.name`), callers **MUST** join the name back to `base_path` (for example `Path(base_path) / name` or `os.path.join(base_path, name)`) before any `os.path.islink(...)`, `Path.resolve()`, or containment check, mirroring the per-iteration join required for `os.walk` and `pathlib.Path.walk` above. No additional join is required when using `os.DirEntry.is_symlink()` or `os.DirEntry.path` directly, because the `DirEntry` object already carries its full path and those APIs are safe to use as-is.
- **SHOULD NOT** use `base_path.rglob("*")` or `base_path.glob("**/*")` (where `base_path` is a concrete `pathlib.Path` instance) for fixture, config, or input discovery unless the implementation also makes symlink handling and root-containment checks explicit. Prefer the safer `os.walk` / `pathlib.Path.walk` patterns above for untrusted or externally influenced discovery roots.
- This guidance implements the repo-wide rule "Refuse path traversal and symlink escapes" in [`.github/copilot-instructions.md`](../copilot-instructions.md) § "Non-negotiable Safety and Security Rules" item 3, "Allowlisted file access only".
- **SHOULD NOT** rely on current working directory; **SHOULD** resolve paths from a clear root (e.g., repo root or config).

## Text Encoding

- When reading local text files from disk that may be authored outside the repository's own write path, especially operator-provided configuration, data, or argument files produced by external tools, code **SHOULD** use `encoding="utf-8-sig"` when the input contract accepts UTF-8 with an optional leading byte order mark (BOM). This guidance applies to JSON and other structured text formats only when the parser path receives decoded text where a leading `\ufeff` would affect parsing.
- `encoding="utf-8"` remains appropriate for repository-controlled text that the project writes or otherwise guarantees to be BOM-free, and for strict input contracts where a leading BOM should be rejected as invalid.
- This is read-side guidance. Code **MUST NOT** use `encoding="utf-8-sig"` for project-controlled writes unless the output contract explicitly requires a UTF-8 BOM, because `utf-8-sig` prepends a BOM on encoding.
- `encoding="utf-8-sig"` only neutralizes an optional leading UTF-8 BOM. It is not general encoding detection and does not handle UTF-16, UTF-32, locale-specific Windows code pages, or other non-UTF-8 encodings. Inputs that may use those encodings need a separate encoding contract, detection strategy, or conversion step.
- Network and API response decoding is out of scope for this guidance. Code **SHOULD** follow the relevant protocol, content-type, charset, or client-library contract.
- This guidance does not require changing parser calls that already consume bytes or binary file objects and define their own encoding behavior.

The examples below are intentionally minimal and scoped to the encoding decision. The `dict[str, object]` return type assumes each args file's top-level value is a JSON object; production code that cannot guarantee that **SHOULD** validate the parsed result and use an annotation that reflects the validated schema. Production code that wraps `json.loads(...)` **MUST** also follow [Error Handling](#error-handling), including raising a domain error with `raise ... from error`.

Compliant example:

```python
import json
from pathlib import Path


def load_args_file(path: Path) -> dict[str, object]:
    """Load an operator-authored JSON args file (UTF-8, optional leading BOM)."""
    return json.loads(path.read_text(encoding="utf-8-sig"))
```

Non-compliant counter-example:

Reading with `encoding="utf-8"` preserves a leading UTF-8 BOM as `\ufeff`, so `json.loads(...)` can raise `json.JSONDecodeError: Unexpected UTF-8 BOM (decode using utf-8-sig)`. This failure is specific to inputs that begin with a UTF-8 BOM; the same code parses BOM-less UTF-8 correctly, which makes the bug easy to miss until an externally authored file arrives.

```python
import json
from pathlib import Path


def load_args_file(path: Path) -> dict[str, object]:
    """Load an operator-authored JSON args file."""
    # Can raise json.JSONDecodeError on a leading UTF-8 BOM.
    return json.loads(path.read_text(encoding="utf-8"))
```

## Tests

- Non-trivial logic **MUST** have tests.
- Tests **MUST** be deterministic and **MUST NOT** depend on network unless explicitly marked/integration-only.
- **SHOULD** use table-driven tests for parsing/validation logic.
- Tests for non-trivial CLI behavior **SHOULD** exercise at least one observable difference for each meaningful mode or flag family, especially for mutually exclusive modes and for flags that choose between reporting-only and writing behavior.
- A test that calls `pytest.skip()` or uses `@pytest.mark.skipif` because an external, provisionable prerequisite is unavailable, such as a Node toolchain, `node_modules`, a compiled binary, or another language runtime, **MUST** have at least one CI path that provisions that prerequisite and exercises the protected behavior without taking the skip. Otherwise CI can pass while the behavior the test is meant to protect remains unenforced.
- This requirement covers prerequisites that CI can reasonably install, build, or otherwise provision. It does **NOT** apply to skips that gate on local or platform capabilities CI cannot reasonably provide on every runner, such as symlink creation support in a particular OS or filesystem environment. Such skips **SHOULD** still describe the missing capability in the skip reason.
- When the prerequisite belongs to another toolchain already provisioned by an existing workflow or pipeline, such as the Node setup plus `npm ci` in the retained Markdown lint CI surface (`.github/workflows/markdownlint.yml` for GitHub Actions or `.azuredevops/pipelines/markdownlint.yml` for Azure Pipelines), the regression **SHOULD** run in the workflow, pipeline, or job that owns or already provisions that prerequisite rather than adding a redundant install to an unrelated job, as long as that CI path exercises the non-skipped behavior.
- A PR that adds such a conditionally skipped test **SHOULD** identify the CI workflow or job that exercises the non-skipped path so reviewers can confirm the behavior is actually enforced.
- Tests **SHOULD NOT** read from or monkeypatch private (single-underscore-prefixed) attributes or methods of production classes.
- When a test needs to substitute collaborators or inject fixtures that production code would normally build internally, production code **SHOULD** expose a narrow public seam (for example, a keyword-only `__init__` parameter or another explicit injection point) rather than relying on tests to monkeypatch private internals.
- Production call sites **SHOULD** use the default behavior of that seam unless an override is intentionally required.
- When a test invokes an external command, subprocess, child process, or generator and then both asserts the command's success and reads derived artifacts the command or generator was supposed to produce, the test **SHOULD** assert success plus any expected `stdout` / `stderr` contents before reading the derived artifacts. Reading the derived artifact first can cause a regression in the command under test to surface as an unrelated `FileNotFoundError` or similar I/O error on the read, hiding the more informative `result.stderr` message that the success assertion is designed to surface. This rule does not apply when the test intentionally verifies that an artifact is absent or unreadable. In those cases, still assert the external command, subprocess, child process, or generator outcome and diagnostic output before checking artifact absence whenever that ordering gives clearer failure messages.

Compliant example:

```python
result = _run_generator(...)
assert result.returncode == 0, result.stderr
assert "expected stdout line" in result.stdout

output = (tmp_path / "out.txt").read_text(encoding="utf-8")
assert "expected output content" in output
```

Non-compliant counter-example:

```python
result = _run_generator(...)
output = (tmp_path / "out.txt").read_text(encoding="utf-8")  # masks generator failures
assert result.returncode == 0, result.stderr
assert "expected output content" in output
```

- When a test asserts that a token, entry, path, module name, or similar value appears in a specific labeled section of multi-section or otherwise structured command/CLI output, the test **MUST** assert against the parsed or isolated target section, or use an equivalent assertion that disambiguates placement. A bare whole-output substring check, such as `assert "python" in result.stdout`, does not establish that the value appears in the intended section, so it is insufficient to prove section membership: the value may legitimately appear in another section. Whole-output substring checks remain acceptable when the asserted contract is global output presence rather than placement within a specific section.

Compliant example:

```python
def _section_entries(output: str, heading: str) -> set[str]:
    """Return bullet entries rendered under a named output section."""
    entries: set[str] = set()
    in_section = False

    for line in output.splitlines():
        if line and not line.startswith(" ") and line.endswith(":"):
            in_section = line == f"{heading}:"
            continue
        if in_section and line.startswith("  - "):
            entries.add(line.removeprefix("  - ").strip())

    return entries


result = _run_tool(...)
assert result.returncode == 0, result.stderr

excluded_modules = _section_entries(result.stdout, "Excluded modules")
retained_modules = _section_entries(result.stdout, "Retained modules")

assert "python" in excluded_modules
assert "python" not in retained_modules
```

Non-compliant counter-example:

```python
result = _run_tool(...)
assert result.returncode == 0, result.stderr
assert "python" in result.stdout  # Does not prove "python" is under "Excluded modules".
```

### External Tool Configuration Isolation

When a test or test helper isolates an external tool's configuration by setting or overriding environment variables, it **SHOULD** neutralize every ambient, non-fixture-owned, higher-priority, or command- or operation-specific override channel that can affect the fixture, not only the configuration files or file scopes the fixture redirects. This prevents ambient configuration from CI setup, automation or bots, wrapper tooling, or a developer shell from leaking into the fixture and making the test non-deterministic.

- Deliberate fixture-owned configuration remains allowed. For example, a test **MAY** create local repository config inside a temporary Git repository it owns. This rule targets ambient, non-fixture-owned channels, not configuration the fixture deliberately establishes.
- Git illustrates command-scope configuration: isolating global and system file inputs with `GIT_CONFIG_GLOBAL`, `GIT_CONFIG_SYSTEM`, and `GIT_CONFIG_NOSYSTEM` is not sufficient by itself, because Git command-scope configuration from `GIT_CONFIG_PARAMETERS` and the `GIT_CONFIG_COUNT`-bounded `GIT_CONFIG_KEY_<n>` / `GIT_CONFIG_VALUE_<n>` pairs overrides configuration files.
- A Git isolation helper **SHOULD** clear `GIT_CONFIG_PARAMETERS` and `GIT_CONFIG_COUNT`, for example with `for name in ("GIT_CONFIG_PARAMETERS", "GIT_CONFIG_COUNT"): monkeypatch.delenv(name, raising=False)`. Clearing `GIT_CONFIG_COUNT` disables the count-bounded `GIT_CONFIG_KEY_<n>` / `GIT_CONFIG_VALUE_<n>` pairs; deleting individual pairs is only a defensive extra.
- The Git variables above illustrate command-scope configuration, not an exhaustive inventory of every Git-related environment variable. Helpers **SHOULD** also account for command-specific environment variables for the Git commands they invoke; for example, helpers that invoke `git config` **SHOULD** account for `GIT_CONFIG` when no `--file` is provided, because Git documents that variable as affecting `git config` even though it does not affect other Git commands.
- Helpers that cannot use the function-scoped `monkeypatch` fixture **MAY** instead run Git with a sanitized `env=` mapping that includes only variables required for execution plus deliberate fixture configuration. Typical required variables include `PATH`, needed home-directory variables, platform-required variables such as `SystemRoot` on Windows, and deliberate Git isolation variables such as `GIT_CONFIG_GLOBAL`, `GIT_CONFIG_SYSTEM`, and/or `GIT_CONFIG_NOSYSTEM`. A default-deny `env=` mapping also avoids inheriting future, unrelated, or command- or operation-specific tool environment overrides.
- Tests that intentionally exercise Git command scope **MAY** set the command-scope environment variables or pass `git -c` / `--config-env` deliberately after cleanup.

## Performance and Safety

- **SHOULD** prefer clarity first; optimize only when needed and measured.
- **SHOULD** avoid quadratic algorithms in obvious hot paths (parsers, matchers, large loops).
- **MUST** validate untrusted input at boundaries; **MUST NOT** use `eval`.
- **MUST** escape serialized output appropriately for its output context before embedding it into markup, templates, or generated documents. For example, `json.dumps()` output embedded in an inline HTML `<script>` block **MUST** escape `</` sequences (for example, `<\/`) so user-controlled data cannot terminate the script tag and enable XSS. Use framework-provided escaping utilities when available.

### Regular Expressions

When scanning multi-line text for a pattern intended to match each line independently, code **MUST** make line boundaries explicit. Either iterate line by line, such as over `str.splitlines()`, and apply `re.Pattern.match()`, `re.Pattern.search()`, or `re.Pattern.fullmatch()` as appropriate, or use `re.MULTILINE` for the regex operation. When matching whole lines with `fullmatch()`, keep candidate strings free of trailing newlines because `fullmatch()` requires the entire string, including any `\n`, to match; `str.splitlines()` already provides lines without their line terminators.

Code **MUST NOT** use `re.findall()` or `re.finditer()` over a whole multi-line string with `^` or `$` anchors for per-line matching unless `re.MULTILINE` is used for the regex operation. Without `re.MULTILINE`, `^` matches only at the start of the input and `$` matches only at its end, or immediately before a newline at the end of the input. The scan can therefore silently produce a wrong result: typically no matches when the pattern is anchored on both sides (`^...$`), or only the first or last line when it is anchored on just one side. A pattern whose intended match really is the whole string is acceptable.

Code that consumes `re.findall()` results **MUST** account for the pattern's capturing groups: no capturing groups yields a list of full-match strings, one capturing group yields that group's strings, and two or more capturing groups yield a list of tuples. Use non-capturing groups `(?:...)` for grouping that should not change the result shape, or use `re.finditer()` with explicit `match.group(...)` access when match context or a stable result shape matters.

When extracting values from structured text, code **SHOULD** prefer an existing structured parser when one is available in the runtime and dependency posture. When a parser is intentionally unavailable or avoided, such as in a standard-library-only bootstrap script, regex-based extraction of values that belong to a specific key or section **MUST** scope the scan to that key or section's block instead of applying a membership test or per-line item regex to the whole document. A whole-document scan can silently sweep in look-alike tokens from sibling sections, such as a YAML `issue_labels:` item whose value equals a module name.

For YAML-like indentation-bounded extraction, code **MUST** recognize the target key only as a key-shaped line, ignoring the same token when it appears in a comment or single-line scalar value. Code **MUST** derive indentation from the document's actual space indentation rather than assuming a fixed two-space width, support sequence items that appear at the target key's own indentation as well as items indented beneath the key, skip blank and comment lines within the block, treat only whitespace-separated `#` text as an inline comment, and terminate on a non-list sibling key at the target key's indentation or on dedent. A line-based scan cannot reliably parse all YAML features, such as tokens embedded inside multi-line block scalars; that limit is itself a reason to prefer a real parser when one is available.

This rule is the production-code counterpart to the test guidance that section-membership assertions must isolate the target section, and to the [Host Matching](#host-matching) requirement to parse and compare the structured component rather than trusting the raw string.

Compliant example:

```python
line_pattern = re.compile(r"\w+")
word_lines = [line for line in text.splitlines() if line_pattern.fullmatch(line)]
```

Non-compliant counter-example:

```python
word_lines = re.findall(r"^(\w+)$", text)
```

Compliant scoped extraction example, where `extract_key_block(...)` is an illustrative helper that returns the lines of the named nested block and `module_item_pattern` is the compiled per-item pattern:

```python
module_lines = extract_key_block(marker_text, ("template_sync", "included_modules"))
has_markdown = any(module_item_pattern.fullmatch(line) for line in module_lines)
```

Non-compliant counter-example:

```python
has_markdown = module_item_pattern.search(marker_text) is not None
```

### Host Matching

When detecting, allow-listing, routing, selecting credentials, controlling network access, or otherwise making a security-relevant decision based on a host taken from a URL-like value, Git remote string, or explicitly accepted bare host value, code **MUST** compare against a parsed, validated, and normalized host component. Code **MUST NOT** compare against the raw input string.

When a value is expected to already be a bare host, code **MUST** validate that it conforms exactly to the accepted bare-host grammar. Unless that grammar explicitly allows the component, the value must not contain a scheme, user-info, port, path, query string, or fragment. Do not trust a bare-host input merely because it contains the allowed host text.

For URL and scheme-relative input, obtain the host from `urllib.parse.urlsplit(value).hostname`, not from `.netloc` and not from the raw input string. The `.hostname` property excludes user-info and port and returns a lowercased host when a host is present. Code **MUST** treat parse failures, missing hosts, and otherwise unparseable input as non-matches; fail closed.

Code **MUST** use an exact host match by default. Dot-boundary suffix matching, such as `host == allowed or host.endswith("." + allowed)`, **MAY** be used only when subdomains of the allowed DNS name are intentionally trusted, and **MUST NOT** be used for IP literals. IP literals must be parsed and compared exactly, for example with `ipaddress`, before using any DNS suffix-matching helper.

Code **MUST NOT** substring-match or regex-match the raw URL, raw Git remote string, raw `netloc`, or other unparsed host-containing text. Non-compliant patterns include `re.search(r"example\.com", value)`, `"example.com" in value`, and `value.endswith("example.com")`. Using a parser, including a grammar-anchored small regex, `str.split`, or `urllib.parse`, to extract the structured host before comparison is different and acceptable only when that parser recognizes the intended input grammar; extract the host first, then decide trust by exact or dot-boundary comparison of that host.

For SCP-style Git remotes of the form `[user@]host:path`, such as `git@github.com:org/repo.git` or `git@github.com:/srv/org/repo.git`, recognize the SCP shape deliberately and extract the host after the optional `user@` and before the host/path separator colon. Code **MUST NOT** treat a `scheme://` URL, a string with a leading scheme token followed by `:` such as `https:example.com/path`, a local filesystem path, or a Windows drive path such as `C:\repo` as an SCP remote. If an implementation supports bracketed IPv6 SCP remotes, it **MUST** parse that grammar explicitly rather than splitting on the first colon inside the IPv6 literal.

Implementations **SHOULD** normalize both the parsed input host and the allow-listed host before comparison. For DNS names, lowercase both sides and handle trailing-dot absolute DNS names consistently, either by normalizing a trailing absolute-name dot on both sides or by rejecting such inputs. If non-ASCII hostnames are supported, convert both sides to one canonical IDNA form before matching; otherwise reject non-ASCII hostnames before matching.

Host matching does not replace other URL validation. Code that depends on scheme, port, path, query string, user-info, or other URL components **MUST** validate those components separately.

Compliant example:

```python
from urllib.parse import urlsplit

ALLOWED_DNS_HOST = "example.com"


def normalize_dns_host(host: str) -> str:
    """Lowercase a DNS host and normalize one trailing absolute-name dot."""
    return host.lower().removesuffix(".")


def dns_host_matches(
    host: str,
    allowed_host: str,
    *,
    include_subdomains: bool = False,
) -> bool:
    """Match DNS host names: exact by default; opt in before trusting subdomains."""
    normalized_host = normalize_dns_host(host)
    normalized_allowed = normalize_dns_host(allowed_host)

    if normalized_host == normalized_allowed:
        return True
    return include_subdomains and normalized_host.endswith(f".{normalized_allowed}")


def is_allowed_url(value: str) -> bool:
    """Return True only when value's URL authority host is allow-listed."""
    try:
        host = urlsplit(value).hostname
    except ValueError:
        return False
    if host is None:
        return False
    return dns_host_matches(host, ALLOWED_DNS_HOST)


assert is_allowed_url("https://example.com/repo.git") is True
assert is_allowed_url("//example.com/repo.git") is True
assert is_allowed_url("https://notexample.com/repo.git") is False
assert is_allowed_url("https://example.com.evil.com/repo.git") is False
assert is_allowed_url("https://example.com@evil.com/repo.git") is False
assert dns_host_matches("api.example.com", "example.com") is False
assert dns_host_matches("api.example.com", "example.com", include_subdomains=True) is True
```

Non-compliant counter-example:

```python
import re


# WRONG: a substring/regex match against the raw string trusts look-alike and
# user-info-confusion hosts such as notexample.com, example.com.evil.com, and
# https://example.com@evil.com/repo.git.
def is_allowed_url(value: str) -> bool:
    return re.search(r"example\.com", value) is not None
```

## Package Versioning

Packages and applications that expose a version (in package metadata, in CLI `--version` output, in HTTP response headers, in framework metadata such as a FastAPI `version=` field, etc.) **MUST** maintain a **single source of truth** for that version. The same version literal **MUST NOT** be hard-coded independently in `pyproject.toml`, in `__init__.py`, in runtime code, or in any other surface; bumping the version **MUST** require editing exactly one location.

This rule applies regardless of build backend or project structure. When the build backend or layout differs from the preferred pattern below, the same single-source-of-truth principle **MUST** still apply, using the backend's equivalent mechanism.

### Preferred Pattern (Setuptools)

For setuptools-based packages — the default for projects derived from this template — declare the version exactly once in the package's `__init__.py`:

```python
# src/<package>/__init__.py
__version__ = "1.2.3"
```

Reference it from `pyproject.toml` via setuptools' dynamic versioning so the wheel/sdist metadata is derived from the same literal at build time:

```toml
# pyproject.toml
[project]
name = "your-project"
dynamic = ["version"]
# ... other fields ...

[tool.setuptools.dynamic]
version = { attr = "your_project.__version__" }
```

Reference it from runtime/application metadata by importing `__version__` rather than repeating the literal. The same import pattern applies to FastAPI's `version=` metadata, a CLI `--version` flag, HTTP response headers, and any other surface that exposes a version:

```python
# src/your_project/app.py -- FastAPI version metadata
from fastapi import FastAPI

from your_project import __version__

app = FastAPI(title="Your Project", version=__version__)
```

```python
# src/your_project/cli.py -- CLI --version flag
import argparse

from your_project import __version__

parser = argparse.ArgumentParser()
parser.add_argument(
    "--version",
    action="version",
    version=f"%(prog)s {__version__}",
)
```

```python
# src/your_project/middleware.py -- HTTP response header
from your_project import __version__


def add_version_header(response):
    response.headers["X-Service-Version"] = __version__
    return response
```

### Keep the Version Module Side-Effect-Free

The module referenced by `attr = "<package>.__version__"` **SHOULD** be importable without successfully resolving every transitive dependency of the package. Modern setuptools (>= 61) reads simple `__version__ = "X.Y.Z"` assignments via static AST parsing without importing the module, but several real-world conditions still cause the attribute to be resolved by import: older setuptools versions, assignments more complex than a string literal, and tooling other than setuptools that resolves `attr =` references. When that import is required and `__init__.py` performs side-effectful imports — for example, `from .core import Foo` that pulls in an optional or unbuilt dependency — the build fails.

For non-trivial packages, the defensive pattern is to declare `__version__` in a minimal, dependency-free module (commonly `src/<package>/_version.py` or `src/<package>/__about__.py`) and re-export it from `__init__.py`:

```python
# src/your_project/_version.py
__version__ = "1.2.3"
```

```python
# src/your_project/__init__.py
from ._version import __version__
```

```toml
# pyproject.toml
[project]
name = "your-project"
dynamic = ["version"]

[tool.setuptools.dynamic]
version = { attr = "your_project._version.__version__" }
```

This keeps the version literal in a single dependency-free module regardless of what `__init__.py` imports at runtime, and it works identically whether the build resolves `attr =` via static parsing or via import.

### Other Build Backends

If a different build backend is used, the same single-source-of-truth principle **MUST** be preserved using that backend's equivalent mechanism.

> **PEP 621 requirement:** `version` **MUST** be either statically set in `[project]` or explicitly listed in `[project] dynamic`. Backend-specific configuration (such as `[tool.hatch.version]` or `[tool.flit.module]`) is in addition to the `dynamic = ["version"]` declaration in `[project]`, not a replacement for it. Omitting both produces invalid PEP 621 metadata and causes build failures even when the backend would otherwise pick up the literal from the package source.

Common patterns:

- **Hatchling:** Declare `dynamic = ["version"]` in `[project]` and configure `[tool.hatch.version] path = "src/<package>/__init__.py"`. Hatchling then reads `__version__` from the package at build time.
- **Flit:** Declare `dynamic = ["version"]` in `[project]`. Flit then reads `__version__` from the package's top-level module automatically.
- **Poetry:** Use a single source (for example, a `_version.py` module imported by `__init__.py`, combined with a tool such as `poetry-dynamic-versioning`). Under PEP 621-compliant Poetry metadata (Poetry 2.0+), declare `dynamic = ["version"]` in `[project]`. **MUST NOT** maintain a separate hard-coded literal in `pyproject.toml` alongside an independent literal in code.

The specific mechanism is out of scope for this guide; what matters is that exactly one literal exists and that `[project]` declares `version` either statically or as dynamic.

### Drift Detection

Tests or CI **SHOULD** verify that the packaged/resolved version (as reported by `importlib.metadata.version("<distribution-name>")`) and the runtime `__version__` remain aligned, so that a misconfigured build or accidentally re-introduced literal is caught before release:

```python
# tests/test_version.py
from importlib.metadata import version

import your_project


def test_runtime_version_matches_package_metadata() -> None:
    """The runtime __version__ must match the installed package's metadata."""
    assert your_project.__version__ == version("your-project")
```

### Compliant Example

The version literal lives in exactly one place. Every other surface derives from it:

```python
# src/your_project/__init__.py
__version__ = "1.2.3"
```

```toml
# pyproject.toml
[project]
name = "your-project"
dynamic = ["version"]

[tool.setuptools.dynamic]
version = { attr = "your_project.__version__" }
```

```python
# src/your_project/app.py
from fastapi import FastAPI

from your_project import __version__

app = FastAPI(title="Your Project", version=__version__)
```

Bumping `__version__` in `__init__.py` automatically propagates to:

- the wheel/sdist metadata produced by `python -m build`,
- the runtime `your_project.__version__` attribute,
- the FastAPI metadata exposed at `/openapi.json`, and
- any other surface that imports `__version__`.

### Non-compliant Example

The same version literal `"1.2.3"` is duplicated independently across multiple files. Bumping the version requires editing every file, and forgetting any one of them produces silent drift between the wheel metadata, the runtime attribute, and the externally visible surfaces:

```toml
# pyproject.toml -- duplicates the literal
[project]
name = "your-project"
version = "1.2.3"
```

```python
# src/your_project/__init__.py -- duplicates the literal
__version__ = "1.2.3"
```

```python
# src/your_project/app.py -- duplicates the literal
from fastapi import FastAPI

app = FastAPI(title="Your Project", version="1.2.3")
```

```python
# src/your_project/cli.py -- duplicates the literal
import argparse

parser = argparse.ArgumentParser()
parser.add_argument(
    "--version",
    action="version",
    version="%(prog)s 1.2.3",
)
```

This pattern **MUST NOT** be used. Once the version is bumped in one file but missed in another, the package's externally visible version no longer matches its packaged metadata, and the drift typically surfaces only after a release.

## "Done" Definition for Python Changes

This section states what the canonical [Pre-commit Discipline (CRITICAL)](../copilot-instructions.md#pre-commit-discipline-critical) and [How to Work (Definition of Done)](../copilot-instructions.md#how-to-work-definition-of-done) sections require of a completed Python change. Where it selects `pre-commit run --all-files` as the required command, which canonical offers as one example alongside `npm run lint:md`, or fixes the checkpoint at a particular moment, it is an interpretation of those sections and creates no exception to them.

A PR/commit is considered complete when:

- **All pre-commit hooks MUST pass** (Black formatting, Ruff linting, trailing whitespace, etc.).
  - **MUST** run `pre-commit run --all-files` locally before pushing.
  - Pre-commit hooks **MAY** modify files (auto-fix formatting/linting). **MUST** always review and commit these changes before pushing.
  - **If pre-commit CI fails:** **MUST** pull the branch, run `pre-commit run --all-files`, commit fixes, and push again.
- Code **MUST** conform to this style guide.
- Public APIs **MUST** have docstrings.
- Errors **MUST** be explicit and actionable.
- Tests **MUST** exist for core logic and pass locally/CI.
- **MUST NOT** include debug prints; logging **SHOULD** be appropriate for runtime visibility.
- All CI checks **MUST** pass.
