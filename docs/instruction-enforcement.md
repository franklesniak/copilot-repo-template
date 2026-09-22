<!-- markdownlint-disable MD013 -->
# Static Instruction Enforcement

## Metadata

- **Status:** Active
- **Owner:** Repository Maintainers
- **Last Updated:** 2026-09-22
- **Scope:** Optional static instruction checks, applicability, local declarations, and migration.
- **Related:** [Repository instructions](../.github/copilot-instructions.md)

Select `agent-instructions` and `instruction-enforcement` to retain the checker, protected local profile and reviewed catalog. Select each desired agent module explicitly: `agent-copilot`, `agent-codex`, `agent-claude`, `agent-cursor`, `agent-gemini`, or `agent-hermes`. The language modules independently control their instruction contracts. Selecting only `agent-instructions` retains shared guidance; omitting enforcement is an explicit **policy-only** choice without the standalone validation runtime.

| Selected modules | Execution route |
| --- | --- |
| Instructions, enforcement, baseline | `pre-commit run validate-instruction-profile --all-files` |
| Instructions, enforcement, GitHub Actions | Dedicated Instruction Contracts workflow |
| Instructions, enforcement, Azure Pipelines | Dedicated instruction-contracts pipeline, registered through Azure DevOps Services |
| Instructions, enforcement, both hosts | Both dedicated routes |
| Instructions, enforcement, no baseline or host | Invalid; select a runner or choose policy-only |
| Enforcement without instructions | Invalid |

The optional Python **project** module is never required. Baseline reuses pre-commit's Python environment; each dedicated host route installs Python, PyYAML and jsonschema. GitHub is the default host, and Azure is optional additive support. Azure YAML parsing locally does not establish service-backed pipeline or branch-policy validation.

## Explicit modes

Run `python .github/scripts/validate_instruction_profile.py` after installing its declared PyYAML and jsonschema dependencies. Missing, malformed or contradictory applicability data fails with a nonzero exit.

The shared loaders reject repeated explicit YAML mapping keys and JSON object names before schema validation, including nested mappings and objects. For example, two `modules` keys fail instead of silently retaining the second selection. Supported safe YAML aliases and merge overrides remain valid: an explicit key may override a value inherited from a merge. The same parsers check YAML and JSON argument files supplied to the materializer before adoption.

- **Marker mode:** `.github/instruction-profile.yml` contains `version: 1`, `mode: marker` and an explicit `context`: `upstream-template` in the source template, or `downstream` after adoption. The downstream context requires its marker; absence never falls back to upstream applicability. The marker-aware adapter remains authoritative for retained modules, protected decisions, local ownership and waivers. The upstream template validates every catalog obligation; a downstream marker uses its explicit selection.
- **Standalone mode:** the protected profile contains `version: 1`, `mode: standalone`, explicit `modules` and `exceptions` lists. It reads the protected `.github/instruction-contracts.yml` catalog and its standalone schema. Its validation engine and bounded helpers live under `.github/scripts/`; the standalone check runs after sync-support files have been physically removed.

Do not activate both modes. Standalone performs only an existence check for a conflicting marker; it never reads or requires that marker, and removing all support files does not prevent validation. The marker adapter rejects a standalone profile, and a standalone profile cannot select sync support. When changing modes, use reviewed materialization and resolve protected-file decisions before applying the resulting candidate.

Relative-link checks recognize multiline labels and titles, including reference definitions whose destination starts on the next line. An escaped exclamation mark before a link does not turn it into an image: `\![Guide](target.md)` checks the link, while `![Image](target.md)` remains an image. They preserve the opening line number and do not combine fragments across fenced examples or blank lines. This is bounded target extraction for static checks, not a complete Markdown renderer.

Relative links in indented code blocks are literal examples. Code indentation is measured within quote and list containers; indentation that continues an open paragraph remains live. Tabs use structural column stops without changing the reported destination. For embedded Markdown in YAML, structural YAML indentation keeps its existing live-link behavior.

Matched code spans inside an inline link label do not supply label brackets. For example, ``[a `]`](target.md)`` still checks `target.md`; the bracket inside code does not end the label. Link-shaped text wholly inside a code span is literal and produces no target. Unmatched backticks remain literal. Destinations, titles and reference-definition labels retain their own syntax, so a backtick in those components does not hide a later link.

Before comparing a destination with a catalog path, the checker decodes Markdown punctuation escapes and valid character references in one pass. For example, `target\.md` and `target&#46;md` both compare as `target.md`. Replacements are not decoded again, and ordinary URL percent decoding follows afterward. Reports and exception anchors keep the exact original destination spelling; equivalent rendered paths do not share an exception automatically.

## Local exceptions and migration

Each standalone exception names one exact `path`, one exact reported `anchor`, the file's `content_sha256`, a `reason`, and an `authorization_basis` declaration. The content digest is SHA-256 over strict UTF-8 text with CRLF/CR normalized to LF. `file:absent` uses the literal digest `absent`. Paths cannot name directories or traversal. An unrelated content edit invalidates the declaration; one exception cannot excuse another file or anchor. Active Claude imports and tracked local memory remain failures and cannot be excepted.

Every applied exception is reported. A schema-valid declaration is auditable local data, **not independent proof of owner authorization**. Owner approval remains an external repository process. Candidate-owned static checks cannot establish human permission, arbitrary natural-language compliance, future agent behavior, or resistance to an attacker editing the checker and its catalog together.

Initial materialization renders the explicit selected profile. Removing sync support translates relevant anchor/removal declarations to exact local exceptions and scopes stale-section waivers to observed content. It preserves source decisions as migration evidence without treating their historical authority as a new grant. Review the protected profile candidate and any reported failure before removing the old support paths. Reintroducing sync with local declarations requires explicitly translating them back to reviewed marker decisions first; the tool refuses an implicit loss of declarations.

Newly migrated waivers follow the file selection: protected files use their explicit protected decisions, and other files use the most specific matching local override. `TAKE` uses the staged candidate when present, and `SKIP` uses the preserved local content. Section or reference waivers produce exceptions only for failures in that selected content. If a direct instruction waiver accompanies `TAKE` but its anchor no longer fails, migration rejects the conflicting waiver before writing the profile. Review that waiver against the selected candidate.

Existing standalone exceptions retain their original content hashes; changing the selected content does not silently renew them. Migration rejects an applicable retained exception before writing the profile when its original hash or failure anchor does not match the selected content. For example, `TAKE` of a changed guide requires review of its old exception even when the same anchor still fails. Review or remove the incompatible declaration explicitly, then rerun materialization. Declarations for excluded module scopes still retire into the recorded source decisions.

Repeated materialization preserves identical content and surfaces changed protected local profiles through ordinary protected-file reconciliation. Later module removal uses the same reviewed cleanup: remove the owned runtime, schemas, hooks, host routes and references together. A legacy selection that predates per-agent modules must explicitly select the agents to retain before cleanup; no agent deletion should be inferred from the new taxonomy.

The standalone catalog is seeded from the reviewed template obligations. Template maintainers update that seed with the marker catalog and test their equality. Downstream owners control their retained protected profile/catalog; weakening that catalog is a governance change requiring explicit authorization.
