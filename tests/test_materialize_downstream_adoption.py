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
REPORT_SCRIPT_PATH = (
    REPO_ROOT / ".template-sync" / "scripts" / "report_excluded_module_references.py"
)
SCRIPT_DIR = SCRIPT_PATH.parent
NESTED_MARKDOWN_LINT_PATH = REPO_ROOT / ".github" / "scripts" / "lint-nested-markdown.js"
SOURCE_REPO = "https://github.com/franklesniak/copilot-repo-template.git"
FULL_SHA = "0123456789abcdef0123456789abcdef01234567"
ISSUE_692_NO_PYTHON_MODULES = (
    "baseline",
    "agent-instructions",
    "github-platform",
    "github-actions",
    "github-templates",
    "template-sync-support",
    "markdown",
    "powershell",
)
ISSUE_693_PARTIAL_DOC_MODULES = ISSUE_692_NO_PYTHON_MODULES
FULL_TEMPLATE_MODULES = (
    "baseline",
    "agent-instructions",
    "github-platform",
    "github-actions",
    "github-templates",
    "template-onboarding",
    "template-sync-support",
    "markdown",
    "powershell",
    "json",
    "yaml",
    "schema",
    "python",
    "terraform",
)
DEPENDABOT_NO_PYTHON_ECOSYSTEMS = {"github-actions", "npm", "pre-commit"}
DEPENDABOT_FULL_ECOSYSTEMS = DEPENDABOT_NO_PYTHON_ECOSYSTEMS | {"pip"}
ISSUE_693_BASELINE_DOCS = ("README.md", "CONTRIBUTING.md")
# Base module set with no data-file modules (json, yaml, schema) and no
# template-sync-support, used to exercise the OR-group data-ci-reference-only and
# the single-module template-sync-support-reference-only blocks.
NO_DATA_NO_TEMPLATE_SYNC_MODULES = (
    "baseline",
    "agent-instructions",
    "github-platform",
    "github-actions",
    "github-templates",
    "markdown",
    "powershell",
)
# References that exist only inside the template-sync-support-reference-only block
# in README.md.
TEMPLATE_SYNC_SUPPORT_README_REFERENCES = (
    "`.template-sync/`",
    "schemas/template-sync-",
    "validate_downstream_adoption.py",
)
ISSUE_693_EXCLUDED_DOC_REFERENCES = {
    "README.md": (
        "pyproject.toml",
        ".github/workflows/python-ci.yml",
        ".github/workflows/terraform-ci.yml",
        ".github/instructions/python.instructions.md",
        ".github/instructions/terraform.instructions.md",
        ".github/instructions/json.instructions.md",
        ".github/instructions/yaml.instructions.md",
        ".tflint.hcl",
        ".yamllint.yml",
        "templates/python/",
        "templates/terraform/",
        "templates/json/",
        "templates/yaml/",
        "schemas/README.md",
        "schemas/example-config",
        "pre-commit run yamllint --all-files",
        "terraform test -verbose",
        "TFLint",
    ),
    "CONTRIBUTING.md": (
        "Python Version Requirements",
        "pyproject.toml",
        ".github/workflows/python-ci.yml",
        ".github/workflows/terraform-ci.yml",
        ".github/instructions/python.instructions.md",
        ".github/instructions/terraform.instructions.md",
        ".github/instructions/json.instructions.md",
        ".github/instructions/yaml.instructions.md",
        ".tflint.hcl",
        ".yamllint.yml",
        "schemas/README.md",
        "schemas/example-config",
        "pytest tests/ -v --cov --cov-report=term-missing",
        "mypy src/ tests/",
        "terraform-fmt",
        "terraform-validate",
        "terraform-tflint",
        "terraform_version",
        "tflint_version",
        "TFLint",
    ),
}
ISSUE_693_RETAINED_DOC_REFERENCES = {
    "README.md": (
        "npm run lint:md",
        "Invoke-Pester -Path tests/ -Output Detailed",
        "python .template-sync/scripts/validate_downstream_adoption.py --require-marker",
        "`check-json`",
        "`check-yaml`",
        "`actionlint`",
        "`check-jsonschema`",
        "`check-metaschema`",
    ),
    "CONTRIBUTING.md": (
        "pre-commit run --all-files",
        "a working Python 3 interpreter is required",
        "npm run lint:md",
        "Invoke-Pester -Path tests/ -Output Detailed",
        "python .template-sync/scripts/validate_downstream_adoption.py --require-marker",
        "`check-json`",
        "`check-yaml`",
        "`actionlint`",
        "`check-jsonschema`",
        "`check-metaschema`",
        "secrets",
    ),
}
NESTED_MARKDOWN_LINT_NODE_MODULES = (
    "glob",
    "jsonc-parser",
    "markdown-it",
    "markdownlint",
)

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


def copy_template_file(template_root: Path, relative_path: str) -> None:
    """Copy a repository template file into a fixture template root."""
    destination = template_root / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(REPO_ROOT / relative_path, destination)


def nested_markdown_lint_prerequisites_available() -> bool:
    """Return whether the Node-based nested Markdown linter can run locally."""
    if shutil.which("node") is None:
        return False
    return all(
        (REPO_ROOT / "node_modules" / module_name).exists()
        for module_name in NESTED_MARKDOWN_LINT_NODE_MODULES
    )


def check_jsonschema_command() -> list[str] | None:
    """Resolve a ``check-jsonschema`` command for optional generated YAML validation."""
    executable = shutil.which("check-jsonschema")
    if executable is not None:
        return [executable]
    if importlib.util.find_spec("check_jsonschema") is not None:
        return [sys.executable, "-m", "check_jsonschema"]
    return None


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


def prepare_security_reporting_template(template_root: Path) -> None:
    """Create a fixture template with the security-reporting placeholder surfaces."""
    prepare_template(
        template_root,
        [
            {"pattern": "SECURITY.md", "requires_all": ["baseline"]},
            {"pattern": "CODE_OF_CONDUCT.md", "requires_all": ["baseline"]},
            {"pattern": ".github/ISSUE_TEMPLATE/config.yml", "requires_all": ["baseline"]},
            {"pattern": ".github/ISSUE_TEMPLATE/bug_report.yml", "requires_all": ["baseline"]},
        ],
        include_placeholder_helper=True,
    )
    for relative_path in (
        "SECURITY.md",
        "CODE_OF_CONDUCT.md",
        ".github/ISSUE_TEMPLATE/config.yml",
        ".github/ISSUE_TEMPLATE/bug_report.yml",
    ):
        copy_template_file(template_root, relative_path)


def load_yaml(path: Path) -> object:
    """Load generated YAML after asserting it parses."""
    return yaml.safe_load(read_file(path))


def dependabot_update_ecosystems(path: Path) -> set[str]:
    """Return Dependabot package ecosystems from a generated config."""
    document = load_yaml(path)
    assert isinstance(document, dict)
    updates = document.get("updates")
    assert isinstance(updates, list)
    ecosystems: set[str] = set()
    for update in updates:
        assert isinstance(update, dict)
        ecosystem = update.get("package-ecosystem")
        assert isinstance(ecosystem, str)
        ecosystems.add(ecosystem)
    return ecosystems


def validate_dependabot_vendor_schema(path: Path) -> None:
    """Validate generated Dependabot YAML against the built-in schema when available."""
    validator_command = check_jsonschema_command()
    if validator_command is None:
        return

    result = subprocess.run(
        [
            *validator_command,
            "--builtin-schema",
            "vendor.dependabot",
            str(path),
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def security_contact_link(config: object) -> dict[str, object]:
    """Return the security contact link from parsed issue-template config."""
    assert isinstance(config, dict)
    contact_links = config["contact_links"]
    assert isinstance(contact_links, list)
    for contact_link in contact_links:
        assert isinstance(contact_link, dict)
        if contact_link.get("name") == "Security Vulnerabilities":
            return contact_link
    raise AssertionError("Security Vulnerabilities contact link not found")


def assert_issue_form_shape(bug_report: object) -> None:
    """Assert the generated bug-report issue form has the expected structure."""
    assert isinstance(bug_report, dict)
    body = bug_report["body"]
    assert isinstance(body, list)
    assert body
    for item in body:
        assert isinstance(item, dict)
        assert isinstance(item.get("type"), str)
        assert isinstance(item.get("attributes"), dict)


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


def run_materialize_without_template_root(
    target_root: Path,
    *args: str,
) -> subprocess.CompletedProcess[str]:
    """Run the materialization helper using source-selection CLI flags."""
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--target-root",
            str(target_root),
            *args,
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def run_git(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run Git in a fixture repository and assert success."""
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return result


def git_worktree_paths(repo_root: Path) -> set[Path]:
    """Return paths from ``git worktree list --porcelain``."""
    result = run_git(repo_root, "worktree", "list", "--porcelain")
    paths: set[Path] = set()
    for line in result.stdout.splitlines():
        if line.startswith("worktree "):
            paths.add(Path(line.removeprefix("worktree ")).resolve(strict=False))
    return paths


def commit_fixture_template(template_root: Path) -> str:
    """Initialize and commit a fixture template repository."""
    run_git(template_root, "init", "-q")
    run_git(template_root, "add", ".")
    run_git(
        template_root,
        "-c",
        "user.name=Template Tester",
        "-c",
        "user.email=template@example.com",
        "commit",
        "-q",
        "-m",
        "Initial template fixture",
    )
    return run_git(template_root, "rev-parse", "HEAD").stdout.strip()


def prepare_git_template(
    template_root: Path,
    path_mappings: list[dict[str, Any]],
    files: dict[str, str],
) -> str:
    """Create a minimal committed template repository and return its HEAD SHA."""
    prepare_template(template_root, path_mappings)
    for relative_path, content in files.items():
        write_file(template_root / relative_path, content)
    return commit_fixture_template(template_root)


def summary_value(output: str, label: str) -> str:
    """Return the first source-summary value for ``label``."""
    prefix = f"  - {label}: "
    for line in output.splitlines():
        if line.startswith(prefix):
            return line.removeprefix(prefix)
    raise AssertionError(f"summary label not found: {label}")


def run_excluded_module_report(
    repo_root: Path,
    included_modules: tuple[str, ...],
) -> subprocess.CompletedProcess[str]:
    """Run the excluded-module reporter against a fixture repository."""
    module_args = [
        argument
        for module_name in included_modules
        for argument in ("--included-module", module_name)
    ]
    return subprocess.run(
        [
            sys.executable,
            str(REPORT_SCRIPT_PATH),
            "--repo-root",
            str(repo_root),
            *module_args,
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


def test_materializer_help_documents_security_reporting_modes(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The materializer help output documents every supported reporting mode."""
    with pytest.raises(SystemExit) as error:
        materializer.parse_args(["--help"])

    captured = capsys.readouterr()
    assert error.value.code == 0
    assert "github-private-only" in captured.out
    assert "contact-only" in captured.out
    assert "both" in captured.out


def test_materializer_materializes_from_local_template_ref_and_cleans_worktree(
    tmp_path: Path,
) -> None:
    """A locally available template ref is checked out privately and removed."""
    template_repo = tmp_path / "template-repo"
    target_root = tmp_path / "target"
    target_root.mkdir()
    resolved_sha = prepare_git_template(
        template_repo,
        [{"pattern": "README.md", "requires_all": ["baseline"]}],
        {"README.md": "template readme\n"},
    )
    run_git(template_repo, "branch", "template-main", resolved_sha)

    result = run_materialize_without_template_root(
        target_root,
        "--template-ref",
        "template-main",
        "--template-repo",
        str(template_repo),
        "--source-repo",
        SOURCE_REPO,
        "--included-module",
        "baseline",
    )

    assert result.returncode == 0, result.stderr
    assert read_file(target_root / "README.md") == "template readme\n"
    assert summary_value(result.stdout, "source ref") == "template-main"
    assert summary_value(result.stdout, "resolved source SHA") == resolved_sha
    assert summary_value(result.stdout, "source repository") == str(template_repo.resolve())
    temporary_checkout_path = Path(summary_value(result.stdout, "temporary checkout path"))
    assert not temporary_checkout_path.exists()
    assert not materializer.is_same_or_descendant(temporary_checkout_path, target_root)
    assert temporary_checkout_path not in git_worktree_paths(template_repo)
    assert "cleanup status: removed" in result.stdout
    assert "\n  - .git\n" not in result.stdout


def test_materializer_materializes_from_full_template_revision(tmp_path: Path) -> None:
    """A full SHA input is resolved, checked out, and reported as a revision."""
    template_repo = tmp_path / "template-repo"
    target_root = tmp_path / "target"
    target_root.mkdir()
    resolved_sha = prepare_git_template(
        template_repo,
        [{"pattern": "README.md", "requires_all": ["baseline"]}],
        {"README.md": "template readme\n"},
    )

    result = run_materialize_without_template_root(
        target_root,
        "--template-revision",
        resolved_sha,
        "--template-repo",
        str(template_repo),
        "--source-repo",
        SOURCE_REPO,
        "--included-module",
        "baseline",
    )

    assert result.returncode == 0, result.stderr
    assert read_file(target_root / "README.md") == "template readme\n"
    assert summary_value(result.stdout, "source revision") == resolved_sha
    assert summary_value(result.stdout, "resolved source SHA") == resolved_sha
    assert "cleanup status: removed" in result.stdout


def test_materializer_rejects_invalid_template_ref(tmp_path: Path) -> None:
    """The materializer resolves refs locally and fails without fetching."""
    template_repo = tmp_path / "template-repo"
    target_root = tmp_path / "target"
    target_root.mkdir()
    prepare_git_template(
        template_repo,
        [{"pattern": "README.md", "requires_all": ["baseline"]}],
        {"README.md": "template readme\n"},
    )

    result = run_materialize_without_template_root(
        target_root,
        "--template-ref",
        "missing-template-ref",
        "--template-repo",
        str(template_repo),
        "--source-repo",
        SOURCE_REPO,
        "--included-module",
        "baseline",
    )

    assert result.returncode == 1
    assert "Unable to resolve --template-ref 'missing-template-ref'" in result.stderr


def test_materializer_rejects_template_root_with_ref(tmp_path: Path) -> None:
    """Explicit source root and source ref modes are mutually exclusive."""
    template_repo = tmp_path / "template-repo"
    target_root = tmp_path / "target"
    target_root.mkdir()
    prepare_template(template_repo, [{"pattern": "README.md", "requires_all": ["baseline"]}])

    result = run_materialize_without_template_root(
        target_root,
        "--template-root",
        str(template_repo),
        "--template-ref",
        "template-main",
        "--source-repo",
        SOURCE_REPO,
        "--included-module",
        "baseline",
    )

    assert result.returncode == 2
    assert "not allowed with argument" in result.stderr


def test_materializer_rejects_template_temp_root_inside_target(tmp_path: Path) -> None:
    """Operator-supplied temporary checkout roots must stay outside the target."""
    template_repo = tmp_path / "template-repo"
    target_root = tmp_path / "target"
    target_root.mkdir()
    resolved_sha = prepare_git_template(
        template_repo,
        [{"pattern": "README.md", "requires_all": ["baseline"]}],
        {"README.md": "template readme\n"},
    )
    run_git(template_repo, "branch", "template-main", resolved_sha)

    result = run_materialize_without_template_root(
        target_root,
        "--template-ref",
        "template-main",
        "--template-repo",
        str(template_repo),
        "--template-temp-root",
        str(target_root / ".tmp"),
        "--source-repo",
        SOURCE_REPO,
        "--included-module",
        "baseline",
    )

    assert result.returncode == 1
    assert "--template-temp-root must not be inside --target-root" in result.stderr


def test_materializer_rejects_reviewed_sha_mismatch(tmp_path: Path) -> None:
    """Reviewed commits must match the resolved source SHA when both are supplied."""
    template_repo = tmp_path / "template-repo"
    target_root = tmp_path / "target"
    target_root.mkdir()
    resolved_sha = prepare_git_template(
        template_repo,
        [{"pattern": "README.md", "requires_all": ["baseline"]}],
        {"README.md": "template readme\n"},
    )
    run_git(template_repo, "branch", "template-main", resolved_sha)
    mismatched_sha = "f" * 40
    assert mismatched_sha != resolved_sha

    result = run_materialize_without_template_root(
        target_root,
        "--template-ref",
        "template-main",
        "--template-repo",
        str(template_repo),
        "--source-repo",
        SOURCE_REPO,
        "--last-reviewed-template-commit",
        mismatched_sha,
        "--included-module",
        "baseline",
    )

    assert result.returncode == 1
    assert "does not match the resolved source SHA" in result.stderr
    assert "Omit the reviewed value until review is complete" in result.stderr


def test_materializer_failure_cleans_temporary_worktree(tmp_path: Path) -> None:
    """A materialization failure still removes the tool-created source worktree."""
    template_repo = tmp_path / "template-repo"
    target_root = tmp_path / "target"
    target_root.mkdir()
    resolved_sha = prepare_git_template(
        template_repo,
        [{"pattern": "SECURITY.md", "requires_all": ["baseline"]}],
        {"SECURITY.md": "Email [security contact email]\n"},
    )
    run_git(template_repo, "branch", "template-main", resolved_sha)
    before_paths = git_worktree_paths(template_repo)

    result = run_materialize_without_template_root(
        target_root,
        "--template-ref",
        "template-main",
        "--template-repo",
        str(template_repo),
        "--source-repo",
        SOURCE_REPO,
        "--included-module",
        "baseline",
        "--repository",
        "octo/widget",
        "--security-contact",
        "security@example.com",
    )

    assert result.returncode == 1
    assert "placeholder helper is unavailable" in result.stderr
    assert git_worktree_paths(template_repo) == before_paths


def test_cleanup_retries_once_and_verifies_worktree_absence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cleanup retries the remove command once before verifying worktree state."""
    template_repo = tmp_path / "template-repo"
    template_repo.mkdir()
    checkout_path = tmp_path / "source-checkout"
    source_checkout = materializer.SourceCheckout(
        template_root=checkout_path,
        template_repo=template_repo,
        temporary_parent=tmp_path,
        temporary_checkout_path=checkout_path,
        summary=materializer.SourceSummary(
            target_root=str(tmp_path / "target"),
            template_root=str(checkout_path),
            source_mode="template-ref",
            source_value="template-main",
            resolved_source_sha="a" * 40,
            source_repository=str(template_repo),
            temporary_checkout_path=str(checkout_path),
            cleanup_status="pending",
            manual_cleanup_command="git worktree remove --force source-checkout",
        ),
    )
    remove_calls = 0

    def fake_run_git(
        _repo_root: Path,
        args: list[str],
    ) -> subprocess.CompletedProcess[str]:
        nonlocal remove_calls
        if args[:3] == ["worktree", "remove", "--force"]:
            remove_calls += 1
            if remove_calls == 1:
                return subprocess.CompletedProcess(args, 1, "", "locked")
            return subprocess.CompletedProcess(args, 0, "", "")
        if args == ["worktree", "list", "--porcelain"]:
            return subprocess.CompletedProcess(args, 0, "worktree /other/path\n", "")
        raise AssertionError(f"unexpected git args: {args}")

    monkeypatch.setattr(materializer, "run_git", fake_run_git)

    failure = materializer.cleanup_source_checkout(source_checkout)

    assert failure is None
    assert remove_calls == 2
    assert source_checkout.summary.cleanup_status == "removed after retry"


def test_successful_materialization_cleanup_failure_exits_dedicated_code(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Successful materialization plus cleanup failure has a dedicated exit code."""
    template_root = tmp_path / "template"
    target_root = tmp_path / "target"
    target_root.mkdir()
    prepare_template(template_root, [{"pattern": "README.md", "requires_all": ["baseline"]}])
    write_file(template_root / "README.md", "template readme\n")

    def fake_cleanup(source_checkout: materializer.SourceCheckout) -> materializer.CleanupFailure:
        source_checkout.summary.cleanup_status = "failed"
        source_checkout.summary.cleanup_failure = "simulated cleanup failure"
        source_checkout.summary.temporary_checkout_path = str(tmp_path / "stale-worktree")
        source_checkout.summary.source_repository = str(template_root)
        source_checkout.summary.manual_cleanup_command = "git worktree remove --force stale"
        return materializer.CleanupFailure(
            detail="simulated cleanup failure",
            residual_worktree_path=tmp_path / "stale-worktree",
            source_repository=template_root,
            manual_cleanup_command="git worktree remove --force stale",
        )

    monkeypatch.setattr(materializer, "cleanup_source_checkout", fake_cleanup)

    exit_code = materializer.main(
        [
            "--template-root",
            str(template_root),
            "--target-root",
            str(target_root),
            "--source-repo",
            SOURCE_REPO,
            "--included-module",
            "baseline",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == materializer.EXIT_CLEANUP_FAILURE
    assert read_file(target_root / "README.md") == "template readme\n"
    assert "cleanup status: failed" in captured.out
    assert "Target tree was materialized successfully" in captured.err
    assert "Manual cleanup command" in captured.err


def test_materialization_failure_plus_cleanup_failure_preserves_primary_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Cleanup failure diagnostics do not replace the materialization failure."""
    template_root = tmp_path / "template"
    target_root = tmp_path / "target"
    target_root.mkdir()
    prepare_template(template_root, [{"pattern": "SECURITY.md", "requires_all": ["baseline"]}])
    write_file(template_root / "SECURITY.md", "Email [security contact email]\n")

    def fake_cleanup(source_checkout: materializer.SourceCheckout) -> materializer.CleanupFailure:
        source_checkout.summary.cleanup_status = "failed"
        return materializer.CleanupFailure(
            detail="simulated cleanup failure",
            residual_worktree_path=tmp_path / "stale-worktree",
            source_repository=template_root,
            manual_cleanup_command="git worktree remove --force stale",
        )

    monkeypatch.setattr(materializer, "cleanup_source_checkout", fake_cleanup)

    exit_code = materializer.main(
        [
            "--template-root",
            str(template_root),
            "--target-root",
            str(target_root),
            "--source-repo",
            SOURCE_REPO,
            "--included-module",
            "baseline",
            "--repository",
            "octo/widget",
            "--security-contact",
            "security@example.com",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == materializer.EXIT_RUNTIME_FAILURE
    assert "placeholder helper is unavailable" in captured.err
    assert captured.err.index("placeholder helper is unavailable") < captured.err.index(
        "Temporary source checkout cleanup also failed"
    )


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


@pytest.mark.parametrize(
    ("included_modules", "case_name"),
    [
        pytest.param(
            (
                "baseline",
                "agent-instructions",
                "github-platform",
                "github-actions",
                "github-templates",
                "template-sync-support",
                "markdown",
                "powershell",
            ),
            "issue-690-powershell-retained",
            id="issue-690-powershell-retained",
        ),
        pytest.param(
            (
                "baseline",
                "agent-instructions",
                "github-platform",
                "github-actions",
                "github-templates",
                "template-sync-support",
                "markdown",
            ),
            "powershell-reference-stripped",
            id="powershell-reference-stripped",
        ),
    ],
)
def test_materialized_template_update_procedure_passes_nested_markdown_lint(
    tmp_path: Path,
    included_modules: tuple[str, ...],
    case_name: str,
) -> None:
    """Partial materialization produces a nested-lint-clean sync procedure."""
    if not nested_markdown_lint_prerequisites_available():
        pytest.skip("Run npm ci --ignore-scripts before this generated-output lint test.")

    target_root = tmp_path / case_name
    target_root.mkdir()
    module_args = [
        argument
        for module_name in included_modules
        for argument in ("--included-module", module_name)
    ]

    result = run_materialize(
        REPO_ROOT,
        target_root,
        "--source-repo",
        SOURCE_REPO,
        "--last-reviewed-template-commit",
        FULL_SHA,
        "--repository",
        "octocat/hello-world",
        "--security-contact",
        "security@example.com",
        "--allow-conflicts",
        *module_args,
    )

    assert result.returncode == 0, result.stderr
    generated_procedure = target_root / "TEMPLATE_UPDATE_PROCEDURE.md"
    assert generated_procedure.is_file(), result.stdout

    lint_result = subprocess.run(
        ["node", str(NESTED_MARKDOWN_LINT_PATH), str(generated_procedure)],
        cwd=REPO_ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert lint_result.returncode == 0, lint_result.stdout + lint_result.stderr


@pytest.mark.parametrize("relative_path", ISSUE_693_BASELINE_DOCS)
def test_materialized_partial_adoption_strips_shared_baseline_doc_stale_references(
    tmp_path: Path,
    relative_path: str,
) -> None:
    """Partial materialization strips excluded-stack prose from each shared baseline doc."""
    target_root = tmp_path / "partial-docs"
    target_root.mkdir()
    module_args = [
        argument
        for module_name in ISSUE_693_PARTIAL_DOC_MODULES
        for argument in ("--included-module", module_name)
    ]

    result = run_materialize(
        REPO_ROOT,
        target_root,
        "--source-repo",
        SOURCE_REPO,
        "--last-reviewed-template-commit",
        FULL_SHA,
        "--repository",
        "octocat/hello-world",
        "--security-contact",
        "security@example.com",
        "--allow-conflicts",
        *module_args,
    )

    assert result.returncode == 0, result.stderr
    generated_path = target_root / relative_path
    assert generated_path.is_file(), result.stdout
    generated_text = read_file(generated_path)

    for retained_token in ISSUE_693_RETAINED_DOC_REFERENCES[relative_path]:
        assert retained_token in generated_text, f"{relative_path}: {retained_token}"
    for excluded_token in ISSUE_693_EXCLUDED_DOC_REFERENCES[relative_path]:
        assert excluded_token not in generated_text, f"{relative_path}: {excluded_token}"

    subprocess.run(
        ["git", "init", "-q"],
        cwd=target_root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    report_result = run_excluded_module_report(target_root, ISSUE_693_PARTIAL_DOC_MODULES)

    assert report_result.returncode == 0, report_result.stderr
    matched_report_row = False
    for report_line in report_result.stdout.splitlines():
        if f"| {relative_path}" not in report_line:
            continue
        matched_report_row = True
        assert "required_cleanup" not in report_line, report_line
        assert "markdown-link.excluded-target" not in report_line, report_line
    assert matched_report_row, (
        f"excluded-module report produced no row mentioning {relative_path}; "
        "the report format may have changed, leaving the cleanup assertions "
        "above vacuous"
    )


@pytest.mark.parametrize("template_sync_support_included", [False, True])
def test_materialized_readme_template_sync_support_reference_block(
    tmp_path: Path,
    template_sync_support_included: bool,
) -> None:
    """README template-sync surface rows materialize only when support is adopted."""
    target_root = tmp_path / "readme-template-sync"
    target_root.mkdir()
    included_modules = NO_DATA_NO_TEMPLATE_SYNC_MODULES
    if template_sync_support_included:
        included_modules = (*included_modules, "template-sync-support")
    module_args = [
        argument
        for module_name in included_modules
        for argument in ("--included-module", module_name)
    ]

    result = run_materialize(
        REPO_ROOT,
        target_root,
        "--source-repo",
        SOURCE_REPO,
        "--last-reviewed-template-commit",
        FULL_SHA,
        "--repository",
        "octocat/hello-world",
        "--security-contact",
        "security@example.com",
        "--allow-conflicts",
        *module_args,
    )

    assert result.returncode == 0, result.stderr
    generated_path = target_root / "README.md"
    assert generated_path.is_file(), result.stdout
    generated_text = read_file(generated_path)

    for reference in TEMPLATE_SYNC_SUPPORT_README_REFERENCES:
        if template_sync_support_included:
            assert reference in generated_text, reference
        else:
            assert reference not in generated_text, reference


@pytest.mark.parametrize("template_sync_support_included", [False, True])
def test_materialized_contributing_template_sync_support_reference_block(
    tmp_path: Path,
    template_sync_support_included: bool,
) -> None:
    """CONTRIBUTING template-sync surface materializes only when support is adopted."""
    target_root = tmp_path / "contributing-template-sync"
    target_root.mkdir()
    included_modules = NO_DATA_NO_TEMPLATE_SYNC_MODULES
    if template_sync_support_included:
        included_modules = (*included_modules, "template-sync-support")
    module_args = [
        argument
        for module_name in included_modules
        for argument in ("--included-module", module_name)
    ]

    result = run_materialize(
        REPO_ROOT,
        target_root,
        "--source-repo",
        SOURCE_REPO,
        "--last-reviewed-template-commit",
        FULL_SHA,
        "--repository",
        "octocat/hello-world",
        "--security-contact",
        "security@example.com",
        "--allow-conflicts",
        *module_args,
    )

    assert result.returncode == 0, result.stderr
    generated_path = target_root / "CONTRIBUTING.md"
    assert generated_path.is_file(), result.stdout
    generated_text = read_file(generated_path)

    if template_sync_support_included:
        assert "validate_downstream_adoption.py" in generated_text
    else:
        assert "validate_downstream_adoption.py" not in generated_text


@pytest.mark.parametrize(
    ("included_data_module", "expect_data_ci_row"),
    [
        pytest.param(None, False, id="all-data-modules-excluded"),
        pytest.param("json", True, id="json-included"),
    ],
)
def test_materialized_contributing_data_ci_reference_block(
    tmp_path: Path,
    included_data_module: str | None,
    expect_data_ci_row: bool,
) -> None:
    """The Data CI row materializes when any OR-group data module is adopted."""
    target_root = tmp_path / "contributing-data-ci"
    target_root.mkdir()
    included_modules = NO_DATA_NO_TEMPLATE_SYNC_MODULES
    if included_data_module is not None:
        included_modules = (*included_modules, included_data_module)
    module_args = [
        argument
        for module_name in included_modules
        for argument in ("--included-module", module_name)
    ]

    result = run_materialize(
        REPO_ROOT,
        target_root,
        "--source-repo",
        SOURCE_REPO,
        "--last-reviewed-template-commit",
        FULL_SHA,
        "--repository",
        "octocat/hello-world",
        "--security-contact",
        "security@example.com",
        "--allow-conflicts",
        *module_args,
    )

    assert result.returncode == 0, result.stderr
    generated_path = target_root / "CONTRIBUTING.md"
    assert generated_path.is_file(), result.stdout
    generated_text = read_file(generated_path)

    if expect_data_ci_row:
        assert "**Data CI**" in generated_text
        assert ".github/workflows/data-ci.yml" in generated_text
    else:
        assert "**Data CI**" not in generated_text
        assert ".github/workflows/data-ci.yml" not in generated_text


def test_excluded_module_report_retains_or_group_block_without_cleanup(
    tmp_path: Path,
) -> None:
    """An OR-group reference-only block retained via one member is not flagged for cleanup."""
    target_root = tmp_path / "or-group-report"
    target_root.mkdir()
    included_modules = (*NO_DATA_NO_TEMPLATE_SYNC_MODULES, "template-sync-support")
    module_args = [
        argument
        for module_name in included_modules
        for argument in ("--included-module", module_name)
    ]

    result = run_materialize(
        REPO_ROOT,
        target_root,
        "--source-repo",
        SOURCE_REPO,
        "--last-reviewed-template-commit",
        FULL_SHA,
        "--repository",
        "octocat/hello-world",
        "--security-contact",
        "security@example.com",
        "--allow-conflicts",
        *module_args,
    )
    assert result.returncode == 0, result.stderr

    subprocess.run(
        ["git", "init", "-q"],
        cwd=target_root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    report_result = run_excluded_module_report(target_root, included_modules)
    assert report_result.returncode == 0, report_result.stderr
    # data-ci.yml is materialized because template-sync-support is retained, so the
    # OR-group data-ci-reference-only block must not surface anywhere in the report
    # (neither a cleanup finding nor an excluded-module scope row) for the excluded
    # json/yaml/schema members.
    assert "data-ci-reference-only" not in report_result.stdout, report_result.stdout


def test_materialized_no_python_adoption_prunes_dependabot_pip_ecosystem(
    tmp_path: Path,
) -> None:
    """No-Python materialization keeps only ecosystems with retained surfaces."""
    target_root = tmp_path / "no-python"
    target_root.mkdir()
    module_args = [
        argument
        for module_name in ISSUE_692_NO_PYTHON_MODULES
        for argument in ("--included-module", module_name)
    ]

    result = run_materialize(
        REPO_ROOT,
        target_root,
        "--source-repo",
        SOURCE_REPO,
        "--last-reviewed-template-commit",
        FULL_SHA,
        "--allow-conflicts",
        *module_args,
    )

    assert result.returncode == 0, result.stderr
    dependabot_path = target_root / ".github" / "dependabot.yml"
    assert dependabot_path.is_file(), result.stdout

    dependabot_text = read_file(dependabot_path)
    assert "pip (pyproject.toml) - Python dependencies" not in dependabot_text
    assert 'package-ecosystem: "pip"' not in dependabot_text
    assert "pip-minor-patch" not in dependabot_text
    assert "npm (package.json) - Markdown tooling dependencies" in dependabot_text
    assert "GitHub Actions (workflows) - Action version updates" in dependabot_text
    assert "pre-commit (.pre-commit-config.yaml) - Pre-commit hook updates" in dependabot_text
    assert dependabot_update_ecosystems(dependabot_path) == DEPENDABOT_NO_PYTHON_ECOSYSTEMS
    validate_dependabot_vendor_schema(dependabot_path)

    subprocess.run(
        ["git", "init"],
        cwd=target_root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    report_result = run_excluded_module_report(target_root, ISSUE_692_NO_PYTHON_MODULES)

    assert report_result.returncode == 0, report_result.stderr
    assert "dependabot-ecosystem.stale | required_cleanup | python |" not in report_result.stdout


def test_materialized_full_adoption_keeps_all_dependabot_ecosystems(
    tmp_path: Path,
) -> None:
    """Full materialization keeps every default Dependabot ecosystem."""
    target_root = tmp_path / "full"
    target_root.mkdir()
    module_args = [
        argument
        for module_name in FULL_TEMPLATE_MODULES
        for argument in ("--included-module", module_name)
    ]

    result = run_materialize(
        REPO_ROOT,
        target_root,
        "--source-repo",
        SOURCE_REPO,
        "--last-reviewed-template-commit",
        FULL_SHA,
        "--allow-conflicts",
        *module_args,
    )

    assert result.returncode == 0, result.stderr
    dependabot_path = target_root / ".github" / "dependabot.yml"
    assert dependabot_path.is_file(), result.stdout
    assert dependabot_update_ecosystems(dependabot_path) == DEPENDABOT_FULL_ECOSYSTEMS
    validate_dependabot_vendor_schema(dependabot_path)


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


@pytest.mark.parametrize(
    ("mode_args", "expected_mode", "expected_url"),
    [
        pytest.param(
            ["--security-contact", "security@example.com"],
            "both",
            "https://github.com/octo/widget/blob/HEAD/SECURITY.md",
            id="omitted-mode-backward-compatible-both",
        ),
        pytest.param(
            ["--security-reporting-mode", "both", "--security-contact", "security@example.com"],
            "both",
            "https://github.com/octo/widget/blob/HEAD/SECURITY.md",
            id="explicit-both",
        ),
        pytest.param(
            [
                "--security-reporting-mode",
                "contact-only",
                "--security-contact",
                "security@example.com",
            ],
            "contact-only",
            "https://github.com/octo/widget/blob/HEAD/SECURITY.md",
            id="contact-only",
        ),
        pytest.param(
            ["--security-reporting-mode", "github-private-only"],
            "github-private-only",
            "https://github.com/octo/widget/blob/HEAD/SECURITY.md",
            id="github-private-only",
        ),
    ],
)
def test_materializes_security_reporting_modes(
    tmp_path: Path,
    mode_args: list[str],
    expected_mode: str,
    expected_url: str,
) -> None:
    """Materialization passes supported security reporting modes to the helper."""
    template_root = tmp_path / "template"
    target_root = tmp_path / "target"
    target_root.mkdir()
    prepare_security_reporting_template(template_root)

    result = run_materialize(
        template_root,
        target_root,
        "--source-repo",
        SOURCE_REPO,
        "--included-module",
        "baseline",
        "--repository",
        "octo/widget",
        "--conduct-contact",
        "conduct@example.com",
        *mode_args,
    )

    assert result.returncode == 0, result.stderr
    assert "Placeholder scan passed" in result.stdout
    assert "conduct@example.com" in read_file(target_root / "CODE_OF_CONDUCT.md")
    assert "[INSERT CONTACT METHOD]" not in read_file(target_root / "CODE_OF_CONDUCT.md")

    config = load_yaml(target_root / ".github" / "ISSUE_TEMPLATE" / "config.yml")
    contact_link = security_contact_link(config)
    assert contact_link["url"] == expected_url
    assert_issue_form_shape(
        load_yaml(target_root / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml")
    )

    security_text = read_file(target_root / "SECURITY.md")
    combined_security_surfaces = "\n".join(
        (
            security_text,
            read_file(target_root / ".github" / "ISSUE_TEMPLATE" / "config.yml"),
            read_file(target_root / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml"),
        )
    )
    assert "[security contact email]" not in security_text
    assert "TODO: Replace" not in security_text

    if expected_mode == "contact-only":
        assert "security@example.com" in security_text
        assert "/security/advisories/new" not in combined_security_surfaces
        assert "GitHub Security Advisories" not in combined_security_surfaces
        assert "private vulnerability reporting" not in combined_security_surfaces
    elif expected_mode == "github-private-only":
        assert "security@example.com" not in security_text
        assert "Security Contact" not in security_text
        assert "GitHub Security Advisories" in security_text
        assert "private vulnerability reporting" in combined_security_surfaces
    else:
        assert "security@example.com" in security_text
        assert "GitHub Security Advisories" in security_text
        assert "private vulnerability reporting" in combined_security_surfaces


def test_materialized_security_reporting_mode_preserves_github_host(
    tmp_path: Path,
) -> None:
    """Materialized security-mode URLs honor --github-host for GHES adoption."""
    template_root = tmp_path / "template"
    target_root = tmp_path / "target"
    target_root.mkdir()
    prepare_security_reporting_template(template_root)

    result = run_materialize(
        template_root,
        target_root,
        "--source-repo",
        SOURCE_REPO,
        "--included-module",
        "baseline",
        "--repository",
        "octo/widget",
        "--security-reporting-mode",
        "github-private-only",
        "--conduct-contact",
        "conduct@example.com",
        "--github-host",
        "github.company.com",
    )

    assert result.returncode == 0, result.stderr
    config = load_yaml(target_root / ".github" / "ISSUE_TEMPLATE" / "config.yml")
    contact_link = security_contact_link(config)
    assert contact_link["url"] == "https://github.company.com/octo/widget/blob/HEAD/SECURITY.md"
    for relative_path in (
        "SECURITY.md",
        ".github/ISSUE_TEMPLATE/config.yml",
        ".github/ISSUE_TEMPLATE/bug_report.yml",
    ):
        text = read_file(target_root / relative_path)
        assert "https://github.com/octo/widget" not in text


def test_materializer_rejects_missing_security_mode_and_contact_when_placeholders_run(
    tmp_path: Path,
) -> None:
    """Supplying repository replacement without mode or contact fails clearly."""
    template_root = tmp_path / "template"
    target_root = tmp_path / "target"
    target_root.mkdir()
    prepare_security_reporting_template(template_root)

    result = run_materialize(
        template_root,
        target_root,
        "--source-repo",
        SOURCE_REPO,
        "--included-module",
        "baseline",
        "--repository",
        "octo/widget",
    )

    assert result.returncode == 1
    assert "Either --security-reporting-mode or --security-contact is required" in result.stderr


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
