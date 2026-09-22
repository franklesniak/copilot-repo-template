"""Native standalone reference checks, exact exceptions, and independent controls."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from tests._pytest_compat import pytest
from tests.test_instruction_profile import ROOT, profile, run, write
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
