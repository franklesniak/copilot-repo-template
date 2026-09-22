"""Native standalone reference checks, exact exceptions, and independent controls."""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from tests._pytest_compat import pytest
from tests.test_instruction_profile import (
    ROOT,
    profile,
    run,
    run_migration_schema_control,
    write,
)
from tests.test_instruction_profile import (
    test_standalone_runs_after_sync_owned_files_are_physically_deleted as deploy_without_sync,
)

pytestmark = pytest.mark.upstream_template_only

KINDS = ("prose-reference", "absolute-url", "markdown-relative-link")
TOKENS = {
    "prose-reference": "docs/azure-devops-support.md",
    "absolute-url": "https://example.invalid/azure-guide",
    "markdown-relative-link": "docs/azure-devops-support.md#setup",
}


def reference_fixture(root: Path, kind: str) -> tuple[dict[str, Any], str]:
    """Declare one excluded-module obligation in a minimal deployed runtime."""
    document = profile(root)
    path = root / ".github/instruction-contracts.yml"
    catalog = yaml.safe_load(path.read_text(encoding="utf-8"))
    obligation: dict[str, Any] = {
        "key": "azure-reference",
        "path": "AGENTS.md",
        "reference_kind": kind,
        "target_modules": ["azure-devops-platform"],
        "target_path": "docs/azure-devops-support.md",
    }
    if kind != "markdown-relative-link":
        obligation["tokens"] = [TOKENS[kind]]
    catalog["protected_guide_reference_obligations"] = [obligation]
    write(root, ".github/instruction-contracts.yml", yaml.safe_dump(catalog))
    prose = TOKENS[kind]
    if kind == "markdown-relative-link":
        prose = f"[Azure guide]({prose})"
    return document, prose


def append_reference(root: Path, prose: str) -> None:
    """Add fixture prose without changing the required anchor controls."""
    path = root / "AGENTS.md"
    write(root, "AGENTS.md", path.read_text(encoding="utf-8") + f"See {prose}.\n")


def require_reference_failure(root: Path) -> None:
    """Keep the native failure oracle independent of the validator implementation."""
    result = run(root)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "Stale protected-guide references" in result.stdout
    assert "azure-reference" in result.stdout


@pytest.mark.parametrize("kind", KINDS)
def test_standalone_rejects_each_declared_reference_kind(tmp_path: Path, kind: str) -> None:
    """A clean positive control passes before excluded target prose is restored."""
    _, prose = reference_fixture(tmp_path, kind)
    clean = run(tmp_path)
    assert clean.returncode == 0, clean.stdout + clean.stderr
    append_reference(tmp_path, prose)
    require_reference_failure(tmp_path)
    assert not (tmp_path / ".template-sync").exists()


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("control", ["fence", "retained-target", "excluded-source"])
def test_standalone_reference_applicability_controls(
    tmp_path: Path, kind: str, control: str
) -> None:
    """Examples and module exclusions retain their existing scoped semantics."""
    document, prose = reference_fixture(tmp_path, kind)
    if control == "fence":
        append_reference(tmp_path, f"\n```markdown\n{prose}\n```\n")
    else:
        append_reference(tmp_path, prose)
    if control == "retained-target":
        document["modules"].append("azure-devops-platform")
        write(tmp_path, ".github/instruction-profile.yml", yaml.safe_dump(document))
    if control == "excluded-source":
        path = tmp_path / ".github/instruction-contracts.yml"
        catalog = yaml.safe_load(path.read_text(encoding="utf-8"))
        catalog["instruction_contracts"][0]["requires_modules"] = ["agent-codex"]
        write(tmp_path, ".github/instruction-contracts.yml", yaml.safe_dump(catalog))
        (tmp_path / "AGENTS.md").unlink()
    result = run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("change", ["none", "content", "path", "key", "kind", "target"])
def test_reference_exception_is_exact(tmp_path: Path, kind: str, change: str) -> None:
    """Only the declared path, reference identity and unchanged content can pass."""
    document, prose = reference_fixture(tmp_path, kind)
    append_reference(tmp_path, prose)
    require_reference_failure(tmp_path)
    digest = hashlib.sha256((tmp_path / "AGENTS.md").read_bytes()).hexdigest()
    declaration = {
        "path": "AGENTS.md",
        "anchor": f"reference:azure-reference:{kind}:{TOKENS[kind]}",
        "content_sha256": digest,
        "reason": "Fixture retains this exact local reference.",
        "authorization_basis": "Explicit fixture decision.",
    }
    if change == "content":
        append_reference(tmp_path, "a changed local policy")
    elif change == "path":
        declaration["path"] = "OTHER.md"
    elif change == "key":
        declaration["anchor"] = declaration["anchor"].replace("azure-reference", "other-key")
    elif change == "kind":
        other = "absolute-url" if kind != "absolute-url" else "prose-reference"
        declaration["anchor"] = declaration["anchor"].replace(kind, other)
    elif change == "target":
        declaration["anchor"] += "-different"
    document["exceptions"] = [declaration]
    write(tmp_path, ".github/instruction-profile.yml", yaml.safe_dump(document))
    result = run(tmp_path)
    assert result.returncode == (0 if change == "none" else 1), result.stdout + result.stderr
    if change == "none":
        assert "Applied local exception: AGENTS.md: reference:" in result.stdout
        # The exception cannot hide a separate mandatory anchor failure.
        write(tmp_path, "AGENTS.md", f"See {prose}.\n")
        declaration["content_sha256"] = hashlib.sha256(
            (tmp_path / "AGENTS.md").read_bytes()
        ).hexdigest()
        write(tmp_path, ".github/instruction-profile.yml", yaml.safe_dump(document))
        unrelated = run(tmp_path)
        assert unrelated.returncode == 1, unrelated.stdout + unrelated.stderr
        assert "missing required phrase" in unrelated.stdout
    else:
        assert "Exception does not match a current failure and exact content" in result.stderr


@pytest.mark.parametrize("kind", KINDS)
def test_reference_oracle_detects_removed_adapter_guard(tmp_path: Path, kind: str) -> None:
    """Removing the real reference call defeats the unchanged native failure oracle."""
    _, prose = reference_fixture(tmp_path, kind)
    append_reference(tmp_path, prose)
    require_reference_failure(tmp_path)
    path = tmp_path / ".github/scripts/validate_instruction_profile.py"
    source = path.read_text(encoding="utf-8")
    guard = (
        "        protected_guide_reference_obligations=core.parse_protected_guide_reference_obligations(\n"
        "            catalog, known_modules\n"
        "        ),\n"
    )
    assert source.count(guard) == 1
    write(tmp_path, path.relative_to(tmp_path).as_posix(), source.replace(guard, ""))
    mutant = run(tmp_path)
    assert mutant.returncode == 0, mutant.stdout + mutant.stderr
    with pytest.raises(AssertionError):
        require_reference_failure(tmp_path)


@pytest.mark.parametrize("change", ["missing", "oversized", "unsafe", "invalid-utf8"])
def test_reference_only_input_fails_closed(tmp_path: Path, change: str) -> None:
    """Reference-only paths receive bounded and contained reads independently of anchors."""
    reference_fixture(tmp_path, "prose-reference")
    path = tmp_path / ".github/instruction-contracts.yml"
    catalog = yaml.safe_load(path.read_text(encoding="utf-8"))
    catalog["protected_guide_reference_obligations"][0]["path"] = "REFERENCE.md"
    if change == "unsafe":
        catalog["protected_guide_reference_obligations"][0]["path"] = "../outside.md"
    write(tmp_path, ".github/instruction-contracts.yml", yaml.safe_dump(catalog))
    if change == "oversized":
        write(tmp_path, "REFERENCE.md", "x" * (1024 * 1024 + 1))
    elif change == "invalid-utf8":
        (tmp_path / "REFERENCE.md").write_bytes(b"\xff")
    result = run(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    if change == "missing":
        assert "Required instruction files absent" in result.stdout
        assert "REFERENCE.md" in result.stdout
    else:
        assert "ERROR:" in result.stderr


def test_azure_reference_fails_after_all_sync_files_are_deleted(tmp_path: Path) -> None:
    """The real selected catalog checks stale Azure prose with physical sync removal."""
    manifest = yaml.safe_load((ROOT / ".template-sync/manifest.yml").read_text(encoding="utf-8"))
    all_modules = {item["name"] for item in manifest["template_manifest"]["modules"]}
    selected = {"agent-instructions", "instruction-enforcement", "baseline"}
    deploy_without_sync(tmp_path, all_modules - selected)
    path = tmp_path / ".github/copilot-instructions.md"
    write(
        tmp_path,
        path.relative_to(tmp_path).as_posix(),
        path.read_text(encoding="utf-8")
        + "\nSee docs/azure-devops-support.md for Azure guidance.\n",
    )
    result = run(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "copilot-instructions-azure-devops-support-guide-path" in result.stdout
    assert "Stale protected-guide references" in result.stdout
    assert not (tmp_path / ".template-sync").exists()


MULTILINE_LINK_CASES = (
    '[Guide](docs/azure-devops-support.md\n "Azure guide")',
    '[Guide](docs/azure-devops-support.md "Azure\nguide")',
    "[Azure\nguide](docs/azure-devops-support.md)",
    '[Guide](\n docs/azure-devops-support.md\n "Azure guide"\n)',
    '[Guide](<docs/azure-devops-support.md>\n "Azure guide")',
    '[Guide]:\n docs/azure-devops-support.md\n "Azure guide"\n\n[Guide]',
    "[Azure\nguide]: docs/azure-devops-support.md\n\n[Azure guide]",
    "[Guide](docs/azure-devops-support.md\n 'Azure\nguide')",
    "[Guide](docs/azure-devops-support.md\n (Azure\nguide))",
    '[Guide](docs/azure-devops-support.md\n "Azure \\"guide\\" title")',
    '> [Guide](docs/azure-devops-support.md\n> "Azure guide")',
    '- [Guide](docs/azure-devops-support.md\n  "Azure guide")',
)
NON_LINK_CASES = (
    '```markdown\n[Guide](docs/azure-devops-support.md\n "Azure guide")\n```',
    '[Guide](docs/azure-devops-support.md\n```text\nexample\n```\n "Azure guide")',
    '[Guide](docs/azure-devops-support.md "Azure\n\nguide")',
    "[Azure\n\nguide](docs/azure-devops-support.md)",
    "[Guide](<docs/azure-devops-\nsupport.md>)",
    '[Guide](docs/azure-devops-support.md "unfinished)',
    "[Guide](docs/azure-devops-support.md \"wrong title')",
    '[Guide](docs/azure-devops-support.md\n# Boundary\n "Azure guide")',
    '- [Guide](docs/azure-devops-support.md\n- "Azure guide")',
    '[Guide](docs/azure-devops-support.md\n> "Azure guide")',
)


@pytest.mark.parametrize("ending", ["\n", "\r\n", "\r"])
@pytest.mark.parametrize("body", MULTILINE_LINK_CASES)
def test_multiline_links_preserve_exact_target_and_physical_line(body: str, ending: str) -> None:
    """Fixed expected tuples independently cover the supported multiline grammar."""
    sys.path.insert(0, str(ROOT / ".github/scripts"))
    import instruction_contract_core as core

    text = "```text\nexample\n```\n\n" + body + "\n"
    assert core.markdown_link_targets_from_text(text.replace("\n", ending)) == (
        (5, "docs/azure-devops-support.md"),
    )


@pytest.mark.parametrize("body", NON_LINK_CASES)
def test_multiline_link_boundaries_do_not_synthesize_targets(body: str) -> None:
    """Removed fences, blank lines and distinct blocks cannot create a live link."""
    sys.path.insert(0, str(ROOT / ".github/scripts"))
    import instruction_contract_core as core

    assert core.markdown_link_targets_from_text(body) == ()


@pytest.mark.parametrize("body", MULTILINE_LINK_CASES[:7])
def test_deployed_multiline_reference_fails_without_sync_and_exact_exception_passes(
    tmp_path: Path, body: str
) -> None:
    """Use the deployed CLI, then preserve existing exact declaration semantics."""
    document, _ = reference_fixture(tmp_path, "markdown-relative-link")
    append_reference(tmp_path, "\n" + body)
    require_reference_failure(tmp_path)
    assert not (tmp_path / ".template-sync").exists()
    declaration = {
        "path": "AGENTS.md",
        "anchor": "reference:azure-reference:markdown-relative-link:docs/azure-devops-support.md",
        "content_sha256": hashlib.sha256((tmp_path / "AGENTS.md").read_bytes()).hexdigest(),
        "reason": "Exact multiline fixture declaration",
        "authorization_basis": "Fixture owner approval",
    }
    document["exceptions"] = [declaration]
    write(tmp_path, ".github/instruction-profile.yml", yaml.safe_dump(document))
    accepted = run(tmp_path)
    assert accepted.returncode == 0, accepted.stdout + accepted.stderr
    assert "Applied local exception" in accepted.stdout
    append_reference(tmp_path, "changed content")
    rejected = run(tmp_path)
    assert rejected.returncode == 1, rejected.stdout + rejected.stderr
    assert "Exception does not match" in rejected.stderr


def test_multiline_link_parser_mutations_have_independent_native_oracles(tmp_path: Path) -> None:
    """Restore the previous parser and remove each boundary separately."""
    reference_fixture(tmp_path, "markdown-relative-link")
    body = MULTILINE_LINK_CASES[0]
    append_reference(tmp_path, body)
    require_reference_failure(tmp_path)
    path = tmp_path / ".github/scripts/instruction_contract_core.py"
    source = path.read_text(encoding="utf-8")
    start = source.index("def markdown_link_targets_from_text(")
    stop = source.index("\ndef normalize_markdown_target(", start)
    old = r"""def markdown_link_targets_from_text(text, *, fence_context=MARKDOWN_FENCE_CONTEXT):
    targets = []
    inline = re.compile(r'(?<!!)\[[^\]\n]+\]\((?P<target><[^>\n]+>|[^)\s\n]+)(?:\s+[^)\n]*)?\)')
    reference = re.compile(r'^ {0,3}\[[^\]\n]+\]:\s+(?P<target><[^>\n]+>|\S+)')
    for number, line in lines_outside_markdown_fences(text, fence_context=fence_context):
        for match in inline.finditer(line):
            targets.append((number, normalize_markdown_target(match.group("target"))))
        match = reference.match(line)
        if match is not None:
            targets.append((number, normalize_markdown_target(match.group("target"))))
    return tuple(targets)

"""
    path.write_text(source[:start] + old + source[stop:], encoding="utf-8", newline="\n")
    missed = run(tmp_path)
    assert missed.returncode == 0, missed.stdout + missed.stderr
    for guard, replacement, fragment in (
        ("line_number != previous_line + 1", "False", NON_LINK_CASES[1]),
        (r'if not content.strip(" \t"):', "if False:", NON_LINK_CASES[2]),
    ):
        boundary_start = source.index("def markdown_link_spans(")
        boundary_stop = source.index("def markdown_delimiter_pairs(", boundary_start)
        boundaries = source[boundary_start:boundary_stop]
        assert boundaries.count(guard) == 1
        write(
            tmp_path,
            "AGENTS.md",
            "Agents MUST validate.\nAgents MUST preserve authority.\n" + fragment,
        )
        path.write_text(source, encoding="utf-8", newline="\n")
        positive = run(tmp_path)
        assert positive.returncode == 0, positive.stdout + positive.stderr
        mutant = (
            source[:boundary_start]
            + boundaries.replace(guard, replacement)
            + source[boundary_stop:]
        )
        path.write_text(mutant, encoding="utf-8", newline="\n")
        synthetic = run(tmp_path)
        assert synthetic.returncode == 1, synthetic.stdout + synthetic.stderr
        assert "Stale protected-guide references" in synthetic.stdout


def test_multiline_reference_migration_keeps_exact_identity_and_noop(tmp_path: Path) -> None:
    """Newly recognized links use the existing exact marker waiver translation."""
    stage, target = tmp_path / "stage", tmp_path / "target"
    for root in (stage, target):
        document, _ = reference_fixture(root, "markdown-relative-link")
        append_reference(root, MULTILINE_LINK_CASES[0])
    waiver = {
        "path": "AGENTS.md",
        "contract_key": "azure-reference",
        "target_path": "docs/azure-devops-support.md",
        "reason": "Exact retained link",
        "authorization_basis": "Fixture owner approval",
    }
    marker = {
        "template_sync": {
            "included_modules": document["modules"],
            "protected_guide_contract_waivers": [waiver],
        }
    }
    migrated = run_migration_schema_control(stage, target, marker_document=marker)
    assert migrated.returncode == 0, migrated.stdout + migrated.stderr
    accepted = run(stage)
    assert accepted.returncode == 0, accepted.stdout + accepted.stderr
    profile_path = stage / ".github/instruction-profile.yml"
    before = profile_path.read_bytes()
    generated = yaml.safe_load(before)
    assert generated["exceptions"][0]["anchor"] == (
        "reference:azure-reference:markdown-relative-link:docs/azure-devops-support.md"
    )
    write(target, ".github/instruction-profile.yml", before.decode())
    repeated = run_migration_schema_control(stage, target, marker_document=marker)
    assert repeated.returncode == 0, repeated.stdout + repeated.stderr
    assert profile_path.read_bytes() == before


def test_multiline_link_parser_near_limit_malformed_input_finishes(tmp_path: Path) -> None:
    """Repeated unmatched delimiters must not rescan a near-limit suffix quadratically."""
    for name, text in {
        "labels": "[" * 1_040_000,
        "destinations": "[x](<" * 170_000 + "tail",
        "parentheses": "[x](" * 200_000 + "tail",
        "titles": '[x](target "' + "x" * 1_039_000,
        "reference-prefixes": "prefix " + "[x]:a " * 170_000,
    }.items():
        candidate = tmp_path / (name + ".md")
        candidate.write_text(text, encoding="utf-8")
        program = (
            "import sys; from pathlib import Path; "
            f"sys.path.insert(0, {str(ROOT / '.github/scripts')!r}); "
            "import instruction_contract_core as c; "
            "assert c.markdown_link_targets_from_text(Path(sys.argv[1]).read_text()) == ()"
        )
        result = subprocess.run(
            [sys.executable, "-c", program, str(candidate)],
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
        assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("[x]([x]([x](target)))", ((1, "[x]([x](target))"),)),
        ('[x](first "[nested](not-a-target)") [y](second)', ((1, "first"), (1, "second"))),
        ('[x]: first "[nested](not-a-target)"\n\n[y](second)', ((1, "first"), (3, "second"))),
        (
            '[x](<docs/azure%2Ddevops-support.md#section>\n "title")',
            ((1, "docs/azure%2Ddevops-support.md#section"),),
        ),
        (r"[x](docs/a\(b\).md)", ((1, r"docs/a\(b\).md"),)),
        ("[x](a(b(c)).md) [y](other.md)", ((1, "a(b(c)).md"), (1, "other.md"))),
    ],
)
def test_multiline_link_destinations_have_independent_fixed_oracles(
    text: str, expected: tuple[tuple[int, str], ...]
) -> None:
    """Accepted destinations and titles cannot be reinterpreted as nested links."""
    sys.path.insert(0, str(ROOT / ".github/scripts"))
    import instruction_contract_core as core

    assert core.markdown_link_targets_from_text(text) == expected


def test_multiline_link_output_is_bounded_and_guard_mutant_is_caught(tmp_path: Path) -> None:
    """Near-limit accepted nesting emits one target; removing consumption breaks it."""
    reference_fixture(tmp_path, "markdown-relative-link")
    script_root = tmp_path / ".github/scripts"
    program = (
        "import sys; "
        f"sys.path.insert(0, {str(script_root)!r}); "
        "import instruction_contract_core as c; "
        "n=int(sys.argv[1]); text='[x]('*n+'target'+')'*n; "
        "targets=c.markdown_link_targets_from_text(text); "
        "assert targets == ((1, text[4:-1]),), (len(targets), len(text)); "
        "assert sum(len(target) for _,target in targets) <= len(text)"
    )
    result = subprocess.run(
        [sys.executable, "-c", program, "200000"],
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    path = script_root / "instruction_contract_core.py"
    source = path.read_text(encoding="utf-8")
    guard = "        if opening < consumed_until:\n            continue\n"
    assert source.count(guard) == 1
    path.write_text(source.replace(guard, ""), encoding="utf-8", newline="\n")
    mutant = subprocess.run(
        [sys.executable, "-c", program, "20"],
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    assert mutant.returncode == 1, mutant.stdout + mutant.stderr
    assert "AssertionError: (20, 106)" in mutant.stderr


@pytest.mark.parametrize(
    "prefix",
    ["", " ", "  ", "   ", "prefix ", " " * 100000],
    ids=["zero", "one", "two", "three", "inline", "long"],
)
def test_multiline_reference_definition_prefix_remains_bounded(prefix: str) -> None:
    """Only zero through three literal spaces qualify as definition indentation."""
    sys.path.insert(0, str(ROOT / ".github/scripts"))
    import instruction_contract_core as core

    expected = ((1, "target.md"),) if len(prefix) <= 3 else ()
    assert core.markdown_link_targets_from_text(prefix + "[x]:\n target.md") == expected


BANG_PARITY_CASES = (
    (0, False),
    (1, True),
    (2, False),
    (3, True),
    (4, False),
    (5, True),
    (6, False),
)


@pytest.mark.parametrize(("backslashes", "is_link"), BANG_PARITY_CASES)
@pytest.mark.parametrize("ending", ["\n", "\r\n", "\r"])
@pytest.mark.parametrize("title", ["", '\n "Azure guide"'])
def test_escaped_bang_parity_preserves_exact_target_and_line(
    backslashes: int, is_link: bool, ending: str, title: str
) -> None:
    """Fixed CommonMark cases distinguish escaped bangs from actual image markers."""
    sys.path.insert(0, str(ROOT / ".github/scripts"))
    import instruction_contract_core as core

    body = "\\" * backslashes + f"![Guide](docs/azure-devops-support.md{title})"
    text = ("Heading\n\n" + body).replace("\n", ending)
    expected = ((3, "docs/azure-devops-support.md"),) if is_link else ()
    assert core.markdown_link_targets_from_text(text) == expected


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        (r"!\[Guide](target.md)", ()),
        (r"\!\[Guide](target.md)", ()),
        ("! [Guide](target.md)", ((1, "target.md"),)),
        (r"![Image](image.md) \![Guide](target.md)", ((1, "target.md"),)),
        (r"\![Guide](target.md) ![Image](image.md)", ((1, "target.md"),)),
        (r"!\![Guide](target.md)", ((1, "target.md"),)),
        ("```markdown\n\\![Guide](target.md)\n```", ()),
    ],
)
def test_escaped_bang_boundaries_keep_independent_expected_targets(
    body: str, expected: tuple[tuple[int, str], ...]
) -> None:
    """Escapes do not activate brackets, examples, or adjacent image destinations."""
    sys.path.insert(0, str(ROOT / ".github/scripts"))
    import instruction_contract_core as core

    assert core.markdown_link_targets_from_text(body) == expected


@pytest.mark.parametrize(("backslashes", "is_link"), BANG_PARITY_CASES)
def test_deployed_escaped_bang_obligation_uses_native_parity(
    tmp_path: Path, backslashes: int, is_link: bool
) -> None:
    """Only rendered links fail after deployment without sync-support files."""
    reference_fixture(tmp_path, "markdown-relative-link")
    append_reference(tmp_path, "\\" * backslashes + "![Guide](docs/azure-devops-support.md)")
    assert not (tmp_path / ".template-sync").exists()
    result = run(tmp_path)
    assert result.returncode == (1 if is_link else 0), result.stdout + result.stderr
    assert ("Stale protected-guide references" in result.stdout) is is_link


def test_deployed_escaped_bang_exact_exception_and_retained_target(tmp_path: Path) -> None:
    """A newly recognized link keeps module applicability and exact declarations."""
    test_deployed_multiline_reference_fails_without_sync_and_exact_exception_passes(
        tmp_path / "excepted", '\\![Guide](docs/azure-devops-support.md\n "Azure guide")'
    )
    retained = tmp_path / "retained"
    document, _ = reference_fixture(retained, "markdown-relative-link")
    document["modules"].append("azure-devops-platform")
    write(retained, ".github/instruction-profile.yml", yaml.safe_dump(document))
    append_reference(retained, r"\![Guide](docs/azure-devops-support.md)")
    result = run(retained)
    assert result.returncode == 0, result.stdout + result.stderr


def test_escaped_bang_native_mutants_have_independent_oracles(tmp_path: Path) -> None:
    """Old skipping, no image exclusion, and one-character escapes each fail controls."""
    reference_fixture(tmp_path, "markdown-relative-link")
    path = tmp_path / ".github/scripts/instruction_contract_core.py"
    source = path.read_text(encoding="utf-8")
    cases = (
        (
            "if markdown_link_opening_is_image(text, opening):",
            'if opening > 0 and text[opening - 1] == "!":',
            r"\![Guide](docs/azure-devops-support.md)",
            1,
            0,
        ),
        (
            "if markdown_link_opening_is_image(text, opening):",
            "if False:",
            "![Image](docs/azure-devops-support.md)",
            0,
            1,
        ),
        (
            "return backslashes % 2 == 0",
            "return backslashes == 0",
            r"\\![Image](docs/azure-devops-support.md)",
            0,
            1,
        ),
    )
    for guard, replacement, body, expected_exit, mutant_exit in cases:
        assert source.count(guard) == 1
        write(
            tmp_path, "AGENTS.md", "Agents MUST validate.\nAgents MUST preserve authority.\n" + body
        )
        path.write_text(source, encoding="utf-8", newline="\n")
        normal = run(tmp_path)
        assert normal.returncode == expected_exit, normal.stdout + normal.stderr
        path.write_text(source.replace(guard, replacement), encoding="utf-8", newline="\n")
        mutant = run(tmp_path)
        assert mutant.returncode == mutant_exit, mutant.stdout + mutant.stderr
        assert ("Stale protected-guide references" in mutant.stdout) is (mutant_exit == 1)


def test_escaped_bang_near_limit_runs_remain_bounded() -> None:
    """Long and repeated parity runs finish without rescanning a growing prefix."""
    program = "\n".join(
        [
            "import sys",
            f"sys.path.insert(0, {str(ROOT / '.github/scripts')!r})",
            "import instruction_contract_core as c",
            "cases=[('\\\\'*1000001+'![x](a)',1),('\\\\'*1000000+'![x](a)',0),",
            "       (('\\\\'*3+'![x](a) ')*80000,80000),",
            "       (('\\\\'*2+'![x](a) ')*80000,0)]",
            "for text, count in cases:",
            "    assert len(text.encode()) <= c.MAXIMUM_INPUT_BYTES",
            "    targets = c.markdown_link_targets_from_text(text)",
            "    assert len(targets) == count",
            "    assert sum(len(target) for _, target in targets) <= len(text)",
        ]
    )
    result = subprocess.run(
        [sys.executable, "-c", program], capture_output=True, text=True, check=False, timeout=15
    )
    assert result.returncode == 0, result.stdout + result.stderr
