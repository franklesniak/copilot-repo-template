---
applyTo: "**/*.md"
description: "Documentation standards:  contract-first, traceable, drift-resistant Markdown."
---

<!-- markdownlint-disable MD013 -->

# Documentation Writing Style

**Version:** 1.4.20260502.1

## Metadata

- **Status:** Active
- **Owner:** Repository Maintainers
- **Last Updated:** 2026-05-02
- **Scope:** Defines documentation standards for all Markdown files in this repository, including specs, design docs, runbooks, ADRs, and developer documentation. Does not cover code comments or inline documentation in source files.
- **Related:** [Repository Copilot Instructions](../copilot-instructions.md)

## Purpose and Scope

Documentation in this repository is treated as a **first-class engineering artifact**, not an afterthought.  Docs are expected to function as:

- A **contract** (what the system does, does not do, and why)
- A **design record** (how it works, constraints, trade-offs, failure modes)
- A **maintenance tool** (how to safely change and operate it without regressions)

This file governs all Markdown documentation (including `README.md`, `docs/**`, ADRs, runbooks, and release notes).

## Core Principles

- **Contract-first:** State behavior precisely.  Prefer normative language:  **MUST**, **SHOULD**, **MAY**, **MUST NOT**, **SHOULD NOT**.
- **Deterministic and explicit:** Avoid vague words like "simple," "fast," "robust," "soon," "etc." Replace with measurable claims or concrete boundaries.
- **Traceable:** Requirements, design decisions, and implementation details must connect via stable identifiers and links.
- **Drift-resistant:** Docs evolve with code; no "document later" in canonical docs.
- **Explain "why," not just "what":** Capture rationale and trade-offs so future changes can be made safely.

## Documentation Taxonomy

- **Product spec:** `docs/spec/` (requirements + design; the source of truth)
- **Developer docs:** `docs/` (how to build, test, extend)
- **Operational docs / runbooks:** `docs/runbooks/` (diagnosis, remediation, safe operations)
- **Architecture Decision Records (ADRs):** `docs/adr/` (durable decisions)

If you introduce a new **top-level documentation category** (a bucket that represents a distinct kind of doc, such as specs vs. runbooks vs. ADRs), it MUST be added to this taxonomy section. Purely **organizational subdirectories under an existing category** (for example, grouping related developer docs under `docs/<topic>/`) are a filing convention, MUST NOT be treated as new top-level categories, and MUST NOT trigger an update to this section. When in doubt, prefer treating a new directory as a subdirectory of an existing category unless it represents a fundamentally different kind of document.

> **Customize for your project:** The taxonomy categories shown above are recommendations, not requirements. Projects SHOULD update this taxonomy to reflect their actual documentation structure. Categories MAY be added, removed, or renamed as appropriate for the project's needs.

## Canonical Source of Truth

Projects SHOULD define a canonical specification document (e.g., `docs/spec/requirements.md`) that serves as the authoritative reference for system behavior and requirements. If a canonical spec is defined, all other documentation (design docs, runbooks, README, etc.) MUST align with it.

> **Customize for your project:** The location and structure of your canonical specification is project-specific. Common patterns include `docs/spec/requirements.md`, `docs/SPEC.md`, or similar. Choose a location that fits your project's documentation organization and update this guidance accordingly.

## Required Header Block for Non-Trivial Docs

For any document longer than ~30 lines or intended as a durable reference (specs, designs, runbooks, ADRs), include this header near the top:

- **Status:** Draft | Active | Deprecated
- **Owner:** Person or team
- **Last Updated:** YYYY-MM-DD
- **Scope:** What this doc covers (and does not cover)
- **Related:** Links to related docs and relevant requirement IDs / ADR IDs

Placement rules for the metadata header block:

- The block MUST appear at the document level. It MUST NOT be placed inside fenced code blocks, quoted excerpts, block quotes, or examples.
- "Top of body" means the first line after any YAML front matter, or line 1 if there is no front matter. "First 30 lines" means lines 1-30 of the body, counting every line (including blank lines and HTML comment directives such as `<!-- markdownlint-disable ... -->`).
- If a top-level `#` heading appears within the first 30 lines of the body, the block MUST be placed immediately after that heading. A single optional `**Version:** ...` line (with surrounding blank lines) MAY appear between the heading and the block; no other intervening content is permitted.
- Otherwise, the block MUST be placed immediately after any leading `<!-- markdownlint-disable ... -->` directive at the top of the body, or at the top of the body if no such directive is present.
- For documents that already use a top-level `## Metadata` section to host the bullet list, that section MUST be the first `##` section after the H1 (and the optional `**Version:** ...` line, if present), and the bullet list MUST appear inside it.
- This placement is compatible with the convention (see **Markdown Conventions** below) that Markdown files SHOULD include `<!-- markdownlint-disable MD013 -->` immediately after any YAML front matter, or at the very top of the file if there is no front matter.

### Synchronizing `Last Updated` and `Version` on Content Changes

The fields referenced in this subsection (`Last Updated`, and the optional `Version` line) are defined in the bullet list above; this subsection adds normative synchronization rules for those fields and does not redefine their semantics.

- When a commit modifies the rendered content or documentation meaning of a document that carries the metadata header block, the `Last Updated` field in that document MUST be bumped to the current UTC date in `YYYY-MM-DD` form as part of the same commit.
- If the document also carries a `**Version:** <major>.<minor>.<YYYYMMDD>.<revision>` line, the embedded `<YYYYMMDD>` segment MUST be updated in the same commit so that it matches the new `Last Updated` value.
- Revision convention for the `<revision>` segment of `**Version:**`:
  - When `<YYYYMMDD>` changes in a commit, `<revision>` MUST reset to `0`.
  - When a further same-day commit modifies the document, `<revision>` MUST increment by `1` (for example, `...20260502.0` → `...20260502.1`).
  - `<major>` and `<minor>` are out of scope for this synchronization rule and follow the document's own semantic-versioning conventions.
- Exemption for trivial mechanical changes. The bump MAY be omitted for commits that do not alter rendered content or documentation meaning, including pure file-mode changes, line-ending normalization, end-of-file newline fixes, or trailing-whitespace-only fixes produced by pre-commit hooks. The trailing-whitespace exemption MUST NOT be applied when the change removes or alters a Markdown hard line break (two or more trailing spaces, or a trailing backslash, immediately before a newline), because such whitespace is rendering-significant; in that case the change alters rendered content and the bump is required. Automated commits made by the auto-fix workflow (`.github/workflows/auto-fix-precommit.yml`) MAY omit the bump when they only apply those mechanical fixes, subject to the same hard-line-break carve-out.
- This rule applies to all documents in the repository that carry the metadata header block, including but not limited to `.github/copilot-instructions.md`, `.github/instructions/*.instructions.md`, `CLAUDE.md`, `AGENTS.md`, and `GEMINI.md`.

## Writing Rules

### Clarity and Structure

- Use informative headings that allow skimming.
- Prefer short paragraphs and bullet lists.
- Use tables only when they increase clarity (avoid tables for "pretty formatting").
- Every list of "things" should be complete or explicitly labeled as partial.

### Normative Language

- Use **MUST/SHOULD/MAY** for requirements and guarantees.
- Use **CAN** only for capability, not obligation.
- Label assumptions explicitly as **Assumption:** and keep them testable.
- **Cross-instruction-file normative-level alignment.** When a document restates a normative requirement that is also defined in an applicable file under `.github/instructions/*`, the document's requirement level (`MUST`, `SHOULD`, `MAY`, and their negations) MUST match the level used in the instruction file when the scope and context are the same, unless the document explicitly justifies a stricter or weaker level in prose immediately adjacent to the restatement. If the scope or context differs from the instruction file, the document SHOULD note that scope/context difference at the restatement. Implicit divergence (silently using a different level when the scope and context are the same as in the instruction file, with no adjacent justification) MUST NOT occur.
- **Intra-document normative-level consistency.** Within a single document, the normative requirement level for the same keyword, field, rule, and scope MUST be consistent across sections. If two sections appear to attach different levels to the same item, reconcile the wording or explicitly explain why the scopes differ.

### Examples

- When documenting behavior, include at least one example that shows:
  - Input
  - Output
  - Explanation (why that output is correct)
- For edge cases, include at least one "failure or ambiguous input" example and the expected handling.

### Markdown Conventions

- Use fenced code blocks with language tags.
- Avoid trailing whitespace; keep blank lines truly blank.
- Prefer relative links within the repo (e.g., `docs/spec/requirements.md`).
- Avoid raw URLs in prose; use descriptive link text when possible.
- Markdown files in this repository SHOULD include `<!-- markdownlint-disable MD013 -->` immediately after any YAML front matter (or at the very top of the file if there is no front matter), and **before any other content**, including badges, links, the H1 heading, and any prose. A single optional blank line MAY appear between the front matter terminator (`---`) and the directive for readability; blank lines are not "content" for this rule.
  - Placement matters: markdownlint's inline `<!-- markdownlint-disable RULE -->` directive only suppresses the rule for content that follows it. Placing the directive after badges or other long lines leaves those lines unprotected when the file is processed with default markdownlint settings outside this repo.
  - This intentionally duplicates the repo-wide `"MD013": false` setting in `.markdownlint.jsonc`.
  - This is a deliberate **portability convention** for cases where a file is read or processed outside this repository, for example:
    - sent to an external LLM for analysis or editing
    - viewed by a tool that applies default markdownlint settings
    - imported into another project
  - The per-file directive helps ensure the file is interpreted with the same expectation that long lines (URLs, code samples, single-line paragraphs, tables) are acceptable.
  - Per-file `<!-- markdownlint-disable RULE -->` directives MUST NOT contradict the configuration in `.markdownlint.jsonc`; their purpose is portability, not local override.
  - When a contributor wants an additional rule disabled, update `.markdownlint.jsonc` first. Per-file directives are only for mirroring repo-wide configuration where default enforcement would harm portability.
- Code-fence info strings MUST contain only a single language tag (e.g., `powershell`, `text`, `json`, `bash`). Do NOT embed file paths, URLs, or other metadata in the info string (for example, `powershell name=src/Foo.ps1 url=https://...#L1-L9` is not allowed). To cite the source of a code excerpt, place a line of the form ``Source: [`relative/path` (lines <start>-<end>)](relative/path#L<start>-L<end>).`` in prose immediately above the fence (for example, ``Source: [`src/Foo.ps1` (lines 1-9)](src/Foo.ps1#L1-L9).``). This keeps the language tag standard, preserves syntax highlighting across Markdown renderers, and reinforces the existing rule to avoid raw URLs in prose.

## ADR Standards

ADRs exist to prevent re-litigating decisions.

- File naming pattern: `docs/adr/ADR-0001-short-title.md`
- ADRs MUST include:
  - **Status:** Proposed | Accepted | Superseded | Deprecated
  - **Context**
  - **Decision**
  - **Consequences:** positive and negative
  - **Alternatives Considered**
  - **Date:** YYYY-MM-DD

ADRs MUST be short and specific. If an ADR grows into a design doc, split it.

## Requirements Documentation Standards

> **Customize this section** for your project. The patterns below are recommendations for projects that track formal requirements.

When writing or updating requirements in specification documents:

- Each requirement SHOULD have a stable identifier (example pattern):
  - `PROJ-REQ-001`, `PROJ-REQ-002`, ...
- Each requirement MUST be phrased as a testable statement:
  - "The system MUST …"
- Each requirement entry SHOULD include:
  - **Rationale:** why it exists
  - **Acceptance Criteria:** objective checks (bullets)
  - **Priority:** P0/P1/P2 (or repo standard)
  - **Verification:** how it will be tested (unit/integration/e2e/manual)

Avoid "implementation leakage" in requirements unless the constraint is truly required (e.g., "MUST NOT store secrets at rest").

### Traceability to Implementation

For each non-trivial requirement, maintain a "Traceability" note that points to:

- An ADR (if it drove a durable decision)
- The implementation module/package path
- The primary test file(s)

This can be minimal, but it SHOULD exist for high-priority requirements.

## Design Documentation Standards

Design docs SHOULD be written to survive refactors. They describe architecture and invariants, not incidental code structure.

A design section SHOULD include:

- **Context:** problem statement and why now
- **Goals / Non-Goals:** explicit boundaries
- **Key Constraints:** security, privacy, performance, portability, cost, toolchain
- **System Overview:** components and responsibilities
- **Data Flow:** what moves where, in what format, and why
- **Interfaces and Contracts:** inputs/outputs, error semantics, validation rules
- **Failure Modes:** what can fail, detection, recovery, and user-visible behavior
- **Alternatives Considered:** at least 2 credible alternatives and why rejected
- **Open Questions:** enumerated, each with an owner or next step

Design sections SHOULD reference requirement IDs they satisfy when applicable.

## Runbook Standards

Runbooks MUST optimize for "2 a.m. usability."

- **Symptoms:** what the operator sees
- **Immediate Triage:** safe checks first
- **Diagnostics:** commands/steps with expected output patterns
- **Mitigations:** reversible actions first; call out risks explicitly
- **Escalation:** when to stop and who to contact
- **Postmortem Notes:** what to capture for later analysis

All commands in runbooks MUST be copy/paste safe and must not destroy data without an explicit warning.

Placeholder text embedded **inside a fenced shell example** MUST NOT contain shell metacharacters that the target shell would interpret. In fenced `bash` examples, runbook authors MUST NOT embed backticks or `$()` command-substitution syntax inside placeholder text, including inside double-quoted strings, because a user who pastes the command before substituting the placeholder may cause the shell to attempt command substitution instead of producing a clean unresolved-placeholder error. When a placeholder needs to refer to a command name, command output, or another identifier that benefits from monospace formatting, the inline-code reference MUST be kept in the surrounding prose, not inside the placeholder string in the code fence. When practical, runbook authors SHOULD validate shell examples in a safe context with the placeholder still present and confirm they fail as literal unresolved-placeholder errors rather than attempting unintended substitution, expansion, redirection, or command execution.

## Change Hygiene and "Definition of Done" for Docs

A change is not complete unless docs remain correct.

For any PR/commit that changes externally observable behavior, at least one of the following MUST be updated:

- spec docs (if any contract/behavior/design constraints changed)
- a design doc section (if architecture/invariants changed)
- an ADR (if a durable decision changed)
- a runbook (if operational behavior changed)
- README / developer docs (if onboarding/build/test steps changed)

Before merging, verify:

- No contradictions across docs
- Examples still match actual behavior
- Open questions are either resolved or explicitly tracked

## Prohibited Patterns

- "TODO:  document later" in spec docs (use "Open Question" instead)
- Contradictory statements between the spec and other docs
- Vague guarantees without measurable definitions
- Unowned open questions ("someone should figure out…")

## AI Authorship Expectations

When generating or editing docs:

- Prefer correctness over eloquence.
- Do not invent requirements, interfaces, or behavior.  If unknown, label as **Open Question**.
- Keep language neutral and engineering-focused; avoid marketing tone.
