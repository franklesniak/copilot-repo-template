---
applyTo: "**/*.md"
description: "Documentation standards:  contract-first, traceable, drift-resistant Markdown."
---

# Documentation Writing Style

**Version:** 1.0.20260111.0

## Metadata

- **Status:** Active
- **Owner:** Repository Maintainers
- **Last Updated:** 2026-01-11
- **Scope:** Defines documentation standards for all Markdown files in this repository, including specs, design docs, runbooks, ADRs, and developer documentation. Does not cover code comments or inline documentation.
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

If you introduce new doc categories, they MUST be added to this taxonomy section.

## Required Header Block for Non-Trivial Docs

For any document longer than ~30 lines or intended as a durable reference (specs, designs, runbooks, ADRs), include this header near the top:

- **Status:** Draft | Active | Deprecated
- **Owner:** Person or team
- **Last Updated:** YYYY-MM-DD
- **Scope:** What this doc covers (and does not cover)
- **Related:** Links to related docs and relevant requirement IDs / ADR IDs

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

## Runbook Standards

Runbooks MUST optimize for "2 a.m. usability."

- **Symptoms:** what the operator sees
- **Immediate Triage:** safe checks first
- **Diagnostics:** commands/steps with expected output patterns
- **Mitigations:** reversible actions first; call out risks explicitly
- **Escalation:** when to stop and who to contact
- **Postmortem Notes:** what to capture for later analysis

All commands in runbooks MUST be copy/paste safe and must not destroy data without an explicit warning.

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
