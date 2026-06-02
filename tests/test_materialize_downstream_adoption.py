"""Exercise deterministic first-adoption materialization."""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml  # type: ignore[import-untyped]

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / ".template-sync" / "scripts" / "materialize_downstream_adoption.py"
SCRIPT_DIR = SCRIPT_PATH.parent
SOURCE_REPO = "https://github.com/franklesniak/copilot-repo-template.git"
FULL_SHA = "0123456789abcdef0123456789abcdef01234567"

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
_MODULE_SPEC = importlib.util.spec_from_file_location(
    "materialize_downstream_adoption", SCRIPT_PATH
)
if _MODULE_SPEC is None or _MODULE_SPEC.loader is None:
    raise RuntimeError(f"Unable to load materializer module from {SCRIPT_PATH}")
materializer = importlib.util.module_from_spec(_MODULE_SPEC)
sys.modules[_MODULE_SPEC.name] = materializer
_MODULE_SPEC.loader.exec_module(materializer)


def write_file(path: Path, content: str) -> None:
    """Write a UTF-8 fixture file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    """Write a YAML fixture file."""
    write_file(path, yaml.safe_dump(data, sort_keys=False))


def read_file(path: Path) -> str:
    """Read a UTF-8 fixture file."""
    return path.read_text(encoding="utf-8")


def prepare_template(
    template_root: Path,
    path_mappings: list[dict[str, Any]],
    *,
    include_placeholder_helper: bool = False,
) -> None:
    """Create the minimal template-side contract files for a fixture run."""
    manifest = {
        "template_manifest": {
            "version": 2,
            "modules": [
                {"name": "baseline", "description": "Baseline files."},
                {
                    "name": "agent-instructions",
                    "description": "Agent instruction files.",
                },
                {
                    "name": "template-sync-support",
                    "description": "Template sync support files.",
                },
                {"name": "python", "description": "Python files."},
                {"name": "markdown", "description": "Markdown files."},
            ],
            "path_mappings": path_mappings,
            "filtering": {
                "default_semantics": "AND",
                "requires_any_semantics": "OR",
                "path_matching": "most_specific_match_wins",
                "same_specificity_action": "union_modules",
                "unmapped_action": "surface_for_owner",
            },
            "notes": {
                "downstream_retention": "Downstream repositories keep marker data.",
            },
        }
    }
    write_yaml(template_root / ".template-sync" / "manifest.yml", manifest)
    schema_root = template_root / "schemas"
    schema_root.mkdir(parents=True)
    shutil.copyfile(
        REPO_ROOT / "schemas" / "template-sync-manifest.schema.json",
        schema_root / "template-sync-manifest.schema.json",
    )
    shutil.copyfile(
        REPO_ROOT / "schemas" / "template-sync-marker.schema.json",
        schema_root / "template-sync-marker.schema.json",
    )
    if include_placeholder_helper:
        helper_path = template_root / ".github" / "scripts" / "replace-template-placeholders.py"
        helper_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(
            REPO_ROOT / ".github" / "scripts" / "replace-template-placeholders.py",
            helper_path,
        )


def run_materialize(
    template_root: Path,
    target_root: Path,
    *args: str,
) -> subprocess.CompletedProcess[str]:
    """Run the materialization helper against fixture repositories."""
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--template-root",
            str(template_root),
            "--target-root",
            str(target_root),
            *args,
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def marker_document(
    included_modules: list[str],
    **template_sync_fields: Any,
) -> dict[str, Any]:
    """Build marker-shaped decisions for fixture runs."""
    template_sync: dict[str, Any] = {
        "source_repo": SOURCE_REPO,
        "last_reviewed_template_commit": FULL_SHA,
        "included_modules": included_modules,
    }
    template_sync.update(template_sync_fields)
    return {"template_sync": template_sync}


def test_retained_files_excluded_files_inline_blocks_and_unmapped_paths(
    tmp_path: Path,
) -> None:
    """Retained module files are copied, excluded modules are absent, and blocks prune."""
    template_root = tmp_path / "template"
    target_root = tmp_path / "target"
    target_root.mkdir()
    prepare_template(
        template_root,
        [
            {"pattern": "README.md", "requires_all": ["baseline"]},
            {"pattern": "CONTRIBUTING.md", "requires_all": ["baseline"]},
            {"pattern": "templates/python/**", "requires_all": ["python"]},
        ],
    )
    write_file(
        template_root / "README.md",
        "top\n# template-sync: begin python-only\npython\n# template-sync: end python-only\nbottom\n",
    )
    write_file(template_root / "CONTRIBUTING.md", "contributing\n")
    write_file(template_root / "templates" / "python" / "app.py", "print('hi')\n")
    write_file(template_root / "UNMAPPED.txt", "unmapped\n")

    result = run_materialize(
        template_root,
        target_root,
        "--source-repo",
        SOURCE_REPO,
        "--included-module",
        "baseline",
    )

    assert result.returncode == 0, result.stderr
    assert read_file(target_root / "README.md") == "top\nbottom\n"
    assert read_file(target_root / "CONTRIBUTING.md") == "contributing\n"
    assert not (target_root / "templates" / "python" / "app.py").exists()
    assert "templates/python/app.py" in result.stdout
    assert "UNMAPPED.txt" in result.stdout


def test_unrecorded_conflict_exits_two_and_allow_conflicts_does_not_advance_marker(
    tmp_path: Path,
) -> None:
    """Unrecorded conflicts are nonzero by default and preview-only with support."""
    template_root = tmp_path / "template"
    target_root = tmp_path / "target"
    target_root.mkdir()
    prepare_template(
        template_root,
        [
            {"pattern": ".template-sync/marker.yml", "requires_all": ["template-sync-support"]},
            {"pattern": "README.md", "requires_all": ["baseline"]},
            {"pattern": "CONTRIBUTING.md", "requires_all": ["baseline"]},
        ],
    )
    write_file(template_root / "README.md", "template readme\n")
    write_file(template_root / "CONTRIBUTING.md", "template contributing\n")
    write_file(target_root / "README.md", "downstream readme\n")

    result = run_materialize(
        template_root,
        target_root,
        "--source-repo",
        SOURCE_REPO,
        "--included-modules",
        "baseline,template-sync-support",
    )

    assert result.returncode == 2, result.stdout
    assert read_file(target_root / "README.md") == "downstream readme\n"
    assert read_file(target_root / "CONTRIBUTING.md") == "template contributing\n"
    assert "README.md: unrecorded" in result.stdout
    assert "preview-only: unrecorded conflicts remain" in result.stdout
    assert not (target_root / ".template-sync" / "marker.yml").exists()

    allow_result = run_materialize(
        template_root,
        target_root,
        "--source-repo",
        SOURCE_REPO,
        "--included-modules",
        "baseline,template-sync-support",
        "--allow-conflicts",
    )

    assert allow_result.returncode == 0, allow_result.stderr
    assert "preview-only: unrecorded conflicts remain" in allow_result.stdout
    assert not (target_root / ".template-sync" / "marker.yml").exists()


def test_decisions_file_take_skip_and_cli_overlap_conflict(tmp_path: Path) -> None:
    """TAKE and SKIP are applied, while conflicting CLI scalar inputs are rejected."""
    template_root = tmp_path / "template"
    target_root = tmp_path / "target"
    target_root.mkdir()
    prepare_template(
        template_root,
        [
            {"pattern": "README.md", "requires_all": ["baseline"]},
            {"pattern": "CONTRIBUTING.md", "requires_all": ["baseline"]},
        ],
    )
    write_file(template_root / "README.md", "template readme\n")
    write_file(template_root / "CONTRIBUTING.md", "template contributing\n")
    write_file(target_root / "README.md", "downstream readme\n")
    write_file(target_root / "CONTRIBUTING.md", "downstream contributing\n")
    write_yaml(
        target_root / "decisions.yml",
        marker_document(
            ["baseline"],
            local_overrides=[
                {
                    "path": "README.md",
                    "default_decision": "TAKE",
                    "reason": "Adopt template README.",
                },
                {
                    "path": "CONTRIBUTING.md",
                    "default_decision": "SKIP",
                    "reason": "Keep downstream contributing guide.",
                },
            ],
        ),
    )

    result = run_materialize(template_root, target_root, "--decisions-file", "decisions.yml")

    assert result.returncode == 0, result.stderr
    assert read_file(target_root / "README.md") == "template readme\n"
    assert read_file(target_root / "CONTRIBUTING.md") == "downstream contributing\n"
    assert "README.md" in result.stdout
    assert "CONTRIBUTING.md" in result.stdout

    conflict_result = run_materialize(
        template_root,
        target_root,
        "--decisions-file",
        "decisions.yml",
        "--source-repo",
        "https://example.com/other.git",
    )

    assert conflict_result.returncode == 1
    assert "Conflicting source repo" in conflict_result.stderr


def test_recorded_deferral_exits_zero_and_marker_updates_then_stays_unchanged(
    tmp_path: Path,
) -> None:
    """Recorded unresolved decisions do not block marker advancement."""
    template_root = tmp_path / "template"
    target_root = tmp_path / "target"
    target_root.mkdir()
    prepare_template(
        template_root,
        [
            {"pattern": ".template-sync/marker.yml", "requires_all": ["template-sync-support"]},
            {"pattern": "README.md", "requires_all": ["baseline"]},
        ],
    )
    write_file(template_root / "README.md", "template readme\n")
    write_file(target_root / "README.md", "downstream readme\n")
    write_yaml(
        target_root / "decisions.yml",
        marker_document(
            ["baseline", "template-sync-support"],
            local_overrides=[
                {
                    "path": "README.md",
                    "default_decision": "DEFER",
                    "reason": "Review README later.",
                }
            ],
        ),
    )

    result = run_materialize(template_root, target_root, "--decisions-file", "decisions.yml")

    assert result.returncode == 0, result.stderr
    assert "Recorded unresolved decisions remain:" in result.stdout
    assert "updated: computed marker written" in result.stdout
    assert read_file(target_root / "README.md") == "downstream readme\n"
    marker_text = read_file(target_root / ".template-sync" / "marker.yml")
    assert "default_decision: DEFER" in marker_text

    unchanged_result = run_materialize(
        template_root,
        target_root,
        "--decisions-file",
        "decisions.yml",
    )

    assert unchanged_result.returncode == 0, unchanged_result.stderr
    assert "unchanged: existing marker already equals computed marker" in unchanged_result.stdout


def test_remove_local_is_recorded_but_not_applied(tmp_path: Path) -> None:
    """REMOVE-LOCAL records an unresolved removal without deleting the target file."""
    template_root = tmp_path / "template"
    target_root = tmp_path / "target"
    target_root.mkdir()
    prepare_template(
        template_root,
        [
            {"pattern": ".template-sync/marker.yml", "requires_all": ["template-sync-support"]},
            {"pattern": "README.md", "requires_all": ["baseline"]},
        ],
    )
    write_file(template_root / "README.md", "template readme\n")
    write_file(target_root / "README.md", "downstream readme\n")
    write_yaml(
        target_root / "decisions.yml",
        marker_document(
            ["baseline", "template-sync-support"],
            local_overrides=[
                {
                    "path": "README.md",
                    "default_decision": "REMOVE-LOCAL",
                    "reason": "Remove after owner review.",
                }
            ],
        ),
    )

    result = run_materialize(template_root, target_root, "--decisions-file", "decisions.yml")

    assert result.returncode == 0, result.stderr
    assert read_file(target_root / "README.md") == "downstream readme\n"
    assert "Recorded but not applied removals:" in result.stdout
    assert "README.md" in result.stdout


def test_placeholder_replacement_reuses_helper_and_missing_helper_fails(
    tmp_path: Path,
) -> None:
    """Placeholder inputs trigger the template-root helper and require it to exist."""
    template_root = tmp_path / "template"
    target_root = tmp_path / "target"
    target_root.mkdir()
    prepare_template(
        template_root,
        [{"pattern": "SECURITY.md", "requires_all": ["baseline"]}],
        include_placeholder_helper=True,
    )
    write_file(
        template_root / "SECURITY.md",
        "Report at https://github.com/OWNER/REPO/security\nEmail [security contact email]\n",
    )

    result = run_materialize(
        template_root,
        target_root,
        "--source-repo",
        SOURCE_REPO,
        "--included-module",
        "baseline",
        "--repository",
        "octo/widget",
        "--security-contact",
        "security@example.com",
    )

    assert result.returncode == 0, result.stderr
    security_text = read_file(target_root / "SECURITY.md")
    assert "https://github.com/octo/widget/security" in security_text
    assert "security@example.com" in security_text
    assert "SECURITY.md" in result.stdout

    missing_helper_template = tmp_path / "missing-helper-template"
    missing_helper_target = tmp_path / "missing-helper-target"
    missing_helper_target.mkdir()
    prepare_template(
        missing_helper_template,
        [{"pattern": "SECURITY.md", "requires_all": ["baseline"]}],
    )
    write_file(missing_helper_template / "SECURITY.md", "Email [security contact email]\n")

    missing_result = run_materialize(
        missing_helper_template,
        missing_helper_target,
        "--source-repo",
        SOURCE_REPO,
        "--included-module",
        "baseline",
        "--repository",
        "octo/widget",
        "--security-contact",
        "security@example.com",
    )

    assert missing_result.returncode == 1
    assert "placeholder helper is unavailable" in missing_result.stderr


def test_byte_only_files_are_not_sent_to_placeholder_helper(tmp_path: Path) -> None:
    """Byte-only retained files stay byte-for-byte even when placeholders run."""
    template_root = tmp_path / "template"
    target_root = tmp_path / "target"
    target_root.mkdir()
    prepare_template(
        template_root,
        [{"pattern": "SECURITY.md", "requires_all": ["baseline"]}],
        include_placeholder_helper=True,
    )
    byte_content = b"\xff\x00OWNER/REPO"
    security_path = template_root / "SECURITY.md"
    security_path.parent.mkdir(parents=True, exist_ok=True)
    security_path.write_bytes(byte_content)

    result = run_materialize(
        template_root,
        target_root,
        "--source-repo",
        SOURCE_REPO,
        "--included-module",
        "baseline",
        "--repository",
        "octo/widget",
        "--security-contact",
        "security@example.com",
    )

    assert result.returncode == 0, result.stderr
    assert (target_root / "SECURITY.md").read_bytes() == byte_content
    assert "Byte-only paths:" in result.stdout
    assert "SECURITY.md" in result.stdout


def test_protected_files_require_concrete_decisions_before_write(tmp_path: Path) -> None:
    """Protected files are conflicts until a path-scoped TAKE decision exists."""
    template_root = tmp_path / "template"
    target_root = tmp_path / "target"
    target_root.mkdir()
    prepare_template(
        template_root,
        [{"pattern": "AGENTS.md", "requires_all": ["agent-instructions"]}],
    )
    write_file(template_root / "AGENTS.md", "agent instructions\n")

    result = run_materialize(
        template_root,
        target_root,
        "--source-repo",
        SOURCE_REPO,
        "--included-module",
        "agent-instructions",
    )

    assert result.returncode == 2, result.stdout
    assert not (target_root / "AGENTS.md").exists()
    assert "unrecorded protected-file decision required" in result.stdout

    write_yaml(
        target_root / "decisions.yml",
        marker_document(
            ["agent-instructions"],
            protected_file_decisions=[
                {
                    "path": "AGENTS.md",
                    "decision": "TAKE",
                    "adoption_mode": "minimal-preservation",
                    "authorization_basis": "Owner authorized AGENTS.md adoption.",
                    "authorized_scope": "AGENTS.md only.",
                }
            ],
        ),
    )

    take_result = run_materialize(template_root, target_root, "--decisions-file", "decisions.yml")

    assert take_result.returncode == 0, take_result.stderr
    assert read_file(target_root / "AGENTS.md") == "agent instructions\n"


def test_decisions_file_path_traversal_is_rejected(tmp_path: Path) -> None:
    """The decisions file must be repository-relative and stay inside the target."""
    template_root = tmp_path / "template"
    target_root = tmp_path / "target"
    target_root.mkdir()
    prepare_template(template_root, [{"pattern": "README.md", "requires_all": ["baseline"]}])
    write_file(template_root / "README.md", "template readme\n")

    result = run_materialize(
        template_root,
        target_root,
        "--decisions-file",
        "../outside.yml",
    )

    assert result.returncode == 1
    assert "--decisions-file must not contain traversal segments" in result.stderr


def test_format_cli_error_summarizes_oserror_without_path() -> None:
    """OSError output is summarized via os_error_summary and omits the path."""
    secret_path = "/home/secret-user/private/secret.key"
    error = FileNotFoundError(2, "No such file or directory", secret_path)

    message = materializer.format_cli_error(error)

    assert message == "FileNotFoundError: No such file or directory"
    assert secret_path not in message


def test_format_cli_error_summarizes_shutil_error_without_paths() -> None:
    """shutil.Error (an OSError subclass) is summarized without its path tuples."""
    secret_path = "/home/secret-user/private"
    error = shutil.Error([(f"{secret_path}/a", f"{secret_path}/b", "boom")])

    message = materializer.format_cli_error(error)

    assert secret_path not in message
    assert message == "Error: I/O error"


def test_format_cli_error_preserves_domain_error_message() -> None:
    """Domain errors already carry path-safe messages and are returned verbatim."""
    error = materializer.MaterializationError("safe domain message")

    assert materializer.format_cli_error(error) == "safe domain message"


def test_summarize_helper_failure_includes_exit_code_and_output() -> None:
    """The failure summary surfaces the exit code and the helper's findings."""
    summary = materializer.summarize_helper_failure(
        returncode=1,
        stdout="Placeholder scan found issues:\n  - README.md:12: forbidden: x (bad)",
        stderr="ERROR: boom",
    )

    assert "exit code 1" in summary
    assert "README.md:12: forbidden: x (bad)" in summary
    assert "ERROR: boom" in summary


def test_summarize_helper_failure_bounds_output_lines() -> None:
    """Long helper streams are truncated to the most recent lines."""
    stdout = "\n".join(f"line {index}" for index in range(50))

    summary = materializer.summarize_helper_failure(
        returncode=2,
        stdout=stdout,
        stderr="",
        line_limit=10,
    )

    assert "line 49" in summary
    assert "line 39" not in summary
    assert "showing last 10 of 50 lines" in summary


def test_summarize_helper_failure_handles_empty_output() -> None:
    """With no captured output, only the exit-code line is returned."""
    assert (
        materializer.summarize_helper_failure(returncode=3, stdout="", stderr="")
        == "Placeholder helper failed with exit code 3."
    )


def test_non_regular_target_path_is_reported_with_repo_relative_path(tmp_path: Path) -> None:
    """A directory where a staged file would land aborts with an actionable, path-named error."""
    template_root = tmp_path / "template"
    target_root = tmp_path / "target"
    target_root.mkdir()
    prepare_template(template_root, [{"pattern": "README.md", "requires_all": ["baseline"]}])
    write_file(template_root / "README.md", "template readme\n")
    # The downstream repository has a directory where the staged file would land.
    (target_root / "README.md").mkdir()

    result = run_materialize(
        template_root,
        target_root,
        "--source-repo",
        SOURCE_REPO,
        "--included-module",
        "baseline",
    )

    assert result.returncode == 1, result.stdout
    assert "README.md" in result.stderr
    assert "not a regular file" in result.stderr


def test_validate_computed_marker_error_names_marker_document_not_schema() -> None:
    """A computed-marker schema failure is reported against the marker document path."""
    with pytest.raises(materializer.TemplateSyncMaterializationError) as excinfo:
        materializer.validate_computed_marker({"template_sync": {}}, template_root=REPO_ROOT)

    message = str(excinfo.value)
    assert ".template-sync/marker.yml" in message
    assert "schema.json" not in message


def test_ensure_regular_target_rejects_non_regular_path_with_repo_relative_path(
    tmp_path: Path,
) -> None:
    """A directory where a regular file is expected raises naming the repo-relative path."""
    conflict = tmp_path / ".template-sync" / "marker.yml"
    conflict.mkdir(parents=True)

    with pytest.raises(materializer.MaterializationError) as excinfo:
        materializer.ensure_regular_target(conflict, ".template-sync/marker.yml")

    message = str(excinfo.value)
    assert ".template-sync/marker.yml" in message
    assert "not a regular file" in message


def test_ensure_regular_target_allows_regular_file_and_missing_path(tmp_path: Path) -> None:
    """Regular files and missing paths pass the guard without raising."""
    regular = tmp_path / "file.txt"
    regular.write_text("content", encoding="utf-8")

    materializer.ensure_regular_target(regular, "file.txt")
    materializer.ensure_regular_target(tmp_path / "missing.txt", "missing.txt")
