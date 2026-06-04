---
applyTo: "**/*.py"
description: "Python coding standards:  portability-first by default, modern-advanced when the stack requires it."
---

<!-- markdownlint-disable MD013 -->

# Python Writing Style

**Version:** 1.6.20260604.0

## Metadata

- **Status:** Active
- **Owner:** Repository Maintainers
- **Last Updated:** 2026-06-04
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

- **[Baseline]** **MAY** use type hints opportunistically for public APIs and complex structures.
- **[Modern]** Type hints are expected broadly; **MUST** run static checking (e.g., mypy/pyright) in CI.
- **[All]** Tests **MUST** exist for non-trivial logic; **SHOULD** use `pytest` unless repo standard differs.
- **[All]** Tests **SHOULD** prefer public seams over monkeypatching private internals.
- **[All]** **SHOULD** use Black for formatting and Ruff for linting.
- **[This repo]** `pre-commit run --all-files` is the authoritative local gate because it runs the pinned hook versions from `.pre-commit-config.yaml`.
- **[This repo]** Targeted pre-commit hook runs, such as `pre-commit run black --all-files` when Python formatting is the only concern, are useful fast checks but **MUST NOT** replace the aggregate `pre-commit run --all-files` gate.
- **[This repo]** Running hook tools directly outside pre-commit, for example `ruff` or `npm run lint:md`, **MAY** help during iteration but **MUST NOT** replace the aggregate gate; type checking (`mypy`) and tests (`pytest`) are enforced separately by [`.github/workflows/python-ci.yml`](../workflows/python-ci.yml).
- **[This repo]** In the active root configuration, Black is the Python formatter enforced by the pinned `psf/black` pre-commit hook, and Ruff is lint-only through `ruff-check`; there is no active `ruff-format` hook and no root `[tool.ruff]` table.
- **[This repo]** The root `[tool.black]` `target-version` list **MUST** stay aligned with the active Python support window to prevent formatter/runtime mismatches and stale syntax allowances, and **MUST** remain explicit so Black does not fall back to inferring unsupported or prerelease Python grammar targets from `[project].requires-python`.
- **[This repo]** `ruff format` **MUST NOT** be used to apply or validate Python formatting unless a future toolchain change explicitly adopts Ruff formatting.
- **[Downstream]** [`templates/python/pyproject.toml`](../../templates/python/pyproject.toml) shows starter `pyproject.toml` configuration for downstream adopters and is distinct from this repository's active root configuration.

### Package Versioning

- **[All]** Packages and applications that expose a version **MUST** maintain a single source of truth for that version and **MUST NOT** duplicate hard-coded version literals across multiple files (for example, repeating the same `"X.Y.Z"` string in `pyproject.toml`, `__init__.py`, and runtime code).
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

### Secrets in User-Facing Output

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

## Data Modeling

### Baseline

- **SHOULD** use `dataclasses` for lightweight models.
- **SHOULD** avoid "magic" model behavior unless it clearly reduces complexity.

### Modern

- If using Pydantic or similar, **SHOULD** enforce schema boundaries at the edges (I/O) and keep the core logic mostly framework-agnostic.

## Filesystem and Paths

- **SHOULD** use `pathlib.Path`.
- *Note on Python version callouts in this section:* the bullets below intentionally cite minimum Python versions for specific APIs (for example `Path.is_relative_to()` on 3.9+ and `Path.walk(...)` on 3.12+) even though this repository's own `pyproject.toml` currently sets `requires-python = ">=3.13"`. These callouts exist for **portability**, consistent with this guide's "portability-first by default" posture (see *Executive Summary*), so that downstream projects which adopt these instructions on a lower Python baseline still receive correct guidance. Projects whose own baseline is 3.13+ **MAY** simplify call sites to the 3.13+ form (for example, always using `is_relative_to(...)` and `Path.walk(follow_symlinks=False)`), but **MUST NOT** weaken the underlying symlink-rejection or containment requirements.
- **MUST NOT** follow symbolic links during recursive directory discovery in code that processes untrusted, repo-supplied, or otherwise externally influenced fixtures, configuration, or input files. Prefer explicit traversal with `os.walk(directory, followlinks=False)` or `base_path.walk(follow_symlinks=False)` on Python 3.12+ (where `base_path` is a concrete `pathlib.Path` instance). Prune or skip entries that are symlinks — for `os.walk` and `pathlib.Path.walk`, which both yield directory and file *names* as strings relative to the per-iteration directory, test by joining `name` to that per-iteration directory: `os.path.islink(os.path.join(dirpath, name))` for `os.walk`, or `(dirpath / name).is_symlink()` for `Path.walk` (where `dirpath` is the `Path` yielded by the current iteration); when using `os.scandir`, test `entry.is_symlink()` on the `os.DirEntry`. Verify each yielded path remains under the declared discovery root by comparing resolved paths on the candidate path instance, e.g. `candidate.resolve().relative_to(base_path.resolve())` (which raises `ValueError` when `candidate` is outside `base_path` — callers **MUST** handle that as a containment failure), or use an equivalent safe boundary check.
- **MUST** validate the discovery root (`base_path`) itself before walking. In addition to the per-yielded-path containment check, callers **MUST** verify that `base_path.resolve()` is contained within `trusted_root.resolve()`, where `trusted_root` is an independently determined allowlisted root, such as `REPO_ROOT`, `PROJECT_ROOT`, or a configured root, and is not derived from `base_path`. Use a concrete, unambiguous containment check on the resolved paths — for example `base_path.resolve().is_relative_to(trusted_root.resolve())` on Python 3.9+, or `base_path.resolve().relative_to(trusted_root.resolve())` (catching `ValueError` and treating it as a containment failure) — and **MUST NOT** fall back to string-prefix comparisons such as `str(base_path).startswith(str(trusted_root))`, which are vulnerable to sibling-directory false positives (for example `/srv/data-evil` vs. `/srv/data`) and to separator/normalization mismatches. This discovery-root validation **MUST NOT** be anchored against `base_path` itself (for example `base_path.resolve().is_relative_to(base_path.resolve())`, which is trivially true), because `base_path.resolve()` follows any symlink at or above the discovery root and a self-anchored check can silently accept a `base_path` that re-anchors to an external target. Note that this prohibition is specifically about the **discovery-root check**: the per-yielded-entry containment check in the previous bullet *is* expressed relative to `base_path` (for example `candidate.resolve().relative_to(base_path.resolve())`), and remains correct **once `base_path` itself has been independently validated against `trusted_root`** as required here. `os.walk(..., followlinks=False)` and `base_path.walk(follow_symlinks=False)` on Python 3.12+ only refuse to descend into symlinked subdirectories; they do not detect the case where `base_path` is itself a symlink, or has a symlinked ancestor, pointing outside the trusted area. Refuse discovery if the resolved-root containment check fails.
- **SHOULD** additionally reject discovery roots whose ancestor chain from `trusted_root` down to `base_path` contains symlinks, as a stricter defense-in-depth posture for high-sensitivity inputs. **SHOULD**, not **MUST**, is used here because legitimate environments can have symlinked ancestors, such as macOS `/tmp` → `/private/tmp`, container bind-mount layouts, or developer workspaces under symlinked home directories.
- **MUST** apply the same symlink and containment guidance to non-walk discovery APIs, not only recursive directory discovery, and to *every* discovered entry regardless of whether it is a file or a directory. Entries returned by `base_path.glob(...)`, `base_path.rglob(...)`, `os.scandir(base_path)`, or `os.listdir(base_path)` in untrusted, repo-supplied, or externally influenced discovery contexts **MUST** be rejected by a per-entry symlink check such as `Path.is_symlink()`, `os.path.islink(...)`, or `os.DirEntry.is_symlink()`, and the resolved candidate **MUST** remain contained within the same `trusted_root` introduced above using the same concrete check (for example `candidate.resolve().is_relative_to(trusted_root.resolve())` on Python 3.9+, or `candidate.resolve().relative_to(trusted_root.resolve())` with `ValueError` handled as a containment failure). Note that `os.listdir(base_path)` yields bare entry *names* and that `os.scandir` yields `os.DirEntry` objects whose `name` attribute is also a bare name; **if you are operating on the bare name** (the result of `os.listdir(...)` or `DirEntry.name`), callers **MUST** join the name back to `base_path` (for example `Path(base_path) / name` or `os.path.join(base_path, name)`) before any `os.path.islink(...)`, `Path.resolve()`, or containment check, mirroring the per-iteration join required for `os.walk` and `pathlib.Path.walk` above. No additional join is required when using `os.DirEntry.is_symlink()` or `os.DirEntry.path` directly, because the `DirEntry` object already carries its full path and those APIs are safe to use as-is.
- **SHOULD NOT** use `base_path.rglob("*")` or `base_path.glob("**/*")` (where `base_path` is a concrete `pathlib.Path` instance) for fixture, config, or input discovery unless the implementation also makes symlink handling and root-containment checks explicit. Prefer the safer `os.walk` / `pathlib.Path.walk` patterns above for untrusted or externally influenced discovery roots.
- This guidance implements the repo-wide rule "Refuse path traversal and symlink escapes" in [`.github/copilot-instructions.md`](../copilot-instructions.md) § "Non-negotiable Safety and Security Rules" item 3, "Allowlisted file access only".
- **SHOULD NOT** rely on current working directory; **SHOULD** resolve paths from a clear root (e.g., repo root or config).

## Tests

- Non-trivial logic **MUST** have tests.
- Tests **MUST** be deterministic and **MUST NOT** depend on network unless explicitly marked/integration-only.
- **SHOULD** use table-driven tests for parsing/validation logic.
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

## Performance and Safety

- **SHOULD** prefer clarity first; optimize only when needed and measured.
- **SHOULD** avoid quadratic algorithms in obvious hot paths (parsers, matchers, large loops).
- **MUST** validate untrusted input at boundaries; **MUST NOT** use `eval`.
- **MUST** escape serialized output appropriately for its output context before embedding it into markup, templates, or generated documents. For example, `json.dumps()` output embedded in an inline HTML `<script>` block **MUST** escape `</` sequences (for example, `<\/`) so user-controlled data cannot terminate the script tag and enable XSS. Use framework-provided escaping utilities when available.

### Regular Expressions

When scanning multi-line text for a pattern intended to match each line independently, code **MUST** make line boundaries explicit. Either iterate line by line, such as over `str.splitlines()`, and apply `re.Pattern.match()`, `re.Pattern.search()`, or `re.Pattern.fullmatch()` as appropriate, or use `re.MULTILINE` for the regex operation. When matching whole lines with `fullmatch()`, keep candidate strings free of trailing newlines because `fullmatch()` requires the entire string, including any `\n`, to match; `str.splitlines()` already provides lines without their line terminators.

Code **MUST NOT** use `re.findall()` or `re.finditer()` over a whole multi-line string with `^` or `$` anchors for per-line matching unless `re.MULTILINE` is used for the regex operation. Without `re.MULTILINE`, `^` matches only at the start of the input and `$` matches only at its end, or immediately before a newline at the end of the input. The scan can therefore silently produce a wrong result: typically no matches when the pattern is anchored on both sides (`^...$`), or only the first or last line when it is anchored on just one side. A pattern whose intended match really is the whole string is acceptable.

Code that consumes `re.findall()` results **MUST** account for the pattern's capturing groups: no capturing groups yields a list of full-match strings, one capturing group yields that group's strings, and two or more capturing groups yield a list of tuples. Use non-capturing groups `(?:...)` for grouping that should not change the result shape, or use `re.finditer()` with explicit `match.group(...)` access when match context or a stable result shape matters.

Compliant example:

```python
line_pattern = re.compile(r"\w+")
word_lines = [line for line in text.splitlines() if line_pattern.fullmatch(line)]
```

Non-compliant counter-example:

```python
word_lines = re.findall(r"^(\w+)$", text)
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
