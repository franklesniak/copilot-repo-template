"""Exercise deterministic first-adoption materialization."""

from __future__ import annotations

import importlib.util
import json
import os
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
    "git-lfs",
    "agent-instructions",
    "github-platform",
    "azure-devops-platform",
    "github-actions",
    "azure-pipelines",
    "github-templates",
    "azure-devops-collaboration",
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
AZURE_TEMPLATE_MODULES = frozenset(
    ("azure-devops-platform", "azure-pipelines", "azure-devops-collaboration")
)
GITHUB_HOST_TEMPLATE_MODULES = frozenset(("github-platform", "github-actions", "github-templates"))
DOWNSTREAM_PYTEST_MODULES = tuple(
    module_name
    for module_name in FULL_TEMPLATE_MODULES
    if module_name not in {"agent-instructions", "git-lfs", "powershell", "terraform"}
)
OPTIONAL_PRUNING_FIXTURES = (
    pytest.param(
        ("baseline", "python", "schema", "template-sync-support"),
        False,
        id="python-schema-template-sync-without-terraform",
    ),
    pytest.param(
        ("baseline", "template-sync-support"),
        False,
        id="template-sync-support-without-powershell",
    ),
    pytest.param(
        FULL_TEMPLATE_MODULES,
        True,
        id="full-upstream-module-set",
    ),
)
AZURE_PROVIDER_BASE_FIELDS: dict[str, str] = {
    "azure_devops_organization": "contoso",
    "azure_devops_project": "Template Adoption",
    "azure_devops_repository": "downstream-template",
    "azure_boards_policy": "manual-follow-up",
    "azure_repos_pr_template_policy": "materialize",
    "azure_branch_policy_reviewer_guidance": "manual-follow-up",
    "azure_security_intake_policy": "manual-follow-up",
    "azure_security_product_enablement": "none",
    "azure_dependency_update_policy": "manual-follow-up",
}
BASELINE_GITATTRIBUTES_LF_PIN_PATHS = (
    "example.ps1",
    "settings.psd1",
    "module.psm1",
    "main.tf",
    "terraform.tfvars",
    "example.tftpl",
    "backend.tfbackend",
)
GIT_ATTRIBUTES_TO_CHECK = ("text", "eol", "filter", "diff", "merge")
GIT_LFS_ATTRIBUTES_TO_CHECK = ("filter", "diff", "merge", "text")
GIT_LFS_MANAGED_ATTRIBUTE_PATHS = (
    "assets/source/poster.psd",
    "assets/source/poster.psb",
    "assets/source/identity.ai",
    "assets/source/layout.indd",
    "assets/source/wireframe.sketch",
    "assets/source/mockup.fig",
    "assets/source/scene.blend",
    "assets/source/model.fbx",
    "assets/source/plan.dwg",
)
OPTIONAL_STACK_OWNED_PATHS = {
    "powershell": (
        ".github/instructions/powershell.instructions.md",
        ".github/linting/PSScriptAnalyzerSettings.psd1",
        ".github/workflows/powershell-ci.yml",
        "src/tools/Resolve-PSScriptAnalyzerGate.ps1",
        "templates/powershell/Example.Tests.ps1",
    ),
    "terraform": (
        ".github/instructions/terraform.instructions.md",
        ".github/workflows/terraform-ci.yml",
        ".tflint.hcl",
        "docs/terraform/TERRAFORM_LINTING_GUIDE.md",
        "docs/terraform/TERRAFORM_TESTING_GUIDE.md",
        "templates/terraform/Example.tftest.hcl",
    ),
}
OPTIONAL_STACK_INLINE_MARKERS = {
    "powershell": ("powershell-reference-only",),
    "terraform": ("terraform-only", "terraform-reference-only"),
}
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
        "docs/azure-devops-support.md",
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
        "docs/azure-devops-support.md",
        "pytest tests/ -v --cov --cov-report=term-missing",
        "mypy src tests",
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

import materialize_downstream_adoption as materializer  # noqa: E402


def write_file(path: Path, content: str) -> None:
    """Write a UTF-8 fixture file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    """Write a YAML fixture file."""
    write_file(path, yaml.safe_dump(data, sort_keys=False))


def write_json(path: Path, data: dict[str, Any]) -> None:
    """Write a strict JSON fixture file."""
    write_file(path, json.dumps(data, indent=2) + "\n")


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
                {
                    "name": "azure-devops-platform",
                    "description": "Azure DevOps platform files.",
                },
                {
                    "name": "azure-pipelines",
                    "description": "Azure Pipelines files.",
                },
                {
                    "name": "azure-devops-collaboration",
                    "description": "Azure DevOps collaboration files.",
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
    return contact_link_by_name(config, "Security Vulnerabilities")


def contact_link_by_name(config: object, name: str) -> dict[str, object]:
    """Return a named contact link from parsed issue-template config."""
    assert isinstance(config, dict)
    contact_links = config["contact_links"]
    assert isinstance(contact_links, list)
    for contact_link in contact_links:
        assert isinstance(contact_link, dict)
        if contact_link.get("name") == name:
            return contact_link
    raise AssertionError(f"{name} contact link not found")


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


def retained_protected_paths_for_modules(included_modules: tuple[str, ...]) -> tuple[str, ...]:
    """Return protected instruction files retained by a materialized module set."""
    _manifest, _module_order, mappings = materializer.load_validated_manifest_context(REPO_ROOT)
    template_paths, skipped_symlinks = materializer.iter_safe_repository_files(REPO_ROOT)
    assert not skipped_symlinks, f"fixture source has skipped symlink(s): {skipped_symlinks}"

    protected_paths: list[str] = []
    for relative_path in template_paths:
        relation = materializer.selected_relation_for_path(relative_path, mappings)
        if relation is None or not relation.is_retained_by(included_modules):
            continue
        if materializer.is_protected_instruction_path(relative_path):
            protected_paths.append(relative_path)
    return tuple(sorted(protected_paths))


def protected_take_decisions_for_modules(
    included_modules: tuple[str, ...],
) -> list[dict[str, str]]:
    """Return marker decisions that allow a full protected-file fixture."""
    return [
        {
            "path": relative_path,
            "decision": "TAKE",
            "adoption_mode": "minimal-preservation",
            "authorization_basis": f"Regression fixture authorizes taking {relative_path}.",
            "authorized_scope": f"{relative_path} only.",
        }
        for relative_path in retained_protected_paths_for_modules(included_modules)
    ]


def materialize_module_fixture(
    tmp_path: Path,
    included_modules: tuple[str, ...],
    *,
    authorize_protected_files: bool = False,
) -> Path:
    """Materialize a real downstream fixture from the requested module set."""
    target_root = tmp_path / "downstream"
    target_root.mkdir()
    marker_fields: dict[str, Any] = {}
    marker_fields.update(azure_provider_fields_for_modules(included_modules))
    if authorize_protected_files:
        marker_fields["protected_file_decisions"] = protected_take_decisions_for_modules(
            included_modules
        )
    write_yaml(
        target_root / "decisions.yml",
        marker_document(list(included_modules), **marker_fields),
    )
    placeholder_args = azure_provider_cli_args_for_modules(included_modules)

    result = run_materialize(
        REPO_ROOT,
        target_root,
        "--decisions-file",
        "decisions.yml",
        *placeholder_args,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    return target_root


def git_check_attributes_in_repo(
    repo_root: Path,
    paths: tuple[str, ...],
    attributes: tuple[str, ...] = GIT_ATTRIBUTES_TO_CHECK,
) -> dict[str, dict[str, str]]:
    """Return Git attributes for paths in a materialized fixture."""
    info_attributes = repo_root / ".git" / "info" / "attributes"
    info_attributes.write_text("", encoding="utf-8")
    global_attributes = repo_root / ".git" / "info" / "empty-global-attributes"
    global_attributes.write_text("", encoding="utf-8")
    env = os.environ.copy()
    env["GIT_ATTR_NOSYSTEM"] = "1"

    result = subprocess.run(
        [
            "git",
            "-C",
            str(repo_root),
            "-c",
            f"core.attributesFile={global_attributes.as_posix()}",
            "check-attr",
            *attributes,
            "--",
            *paths,
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    assert result.returncode == 0, result.stderr

    attributes_by_path: dict[str, dict[str, str]] = {path: {} for path in paths}
    for line in result.stdout.splitlines():
        path, attribute, value = line.split(": ", 2)
        attributes_by_path[path][attribute] = value
    return attributes_by_path


def retained_test_files(target_root: Path) -> tuple[Path, ...]:
    """Return retained pytest files in a materialized fixture."""
    tests_root = target_root / "tests"
    if not tests_root.is_dir():
        return ()
    return tuple(sorted(tests_root.rglob("test_*.py")))


def materialize_downstream_pytest_fixture(tmp_path: Path) -> Path:
    """Materialize a pytest-capable tree that excludes Terraform and PowerShell."""
    target_root = tmp_path / "downstream-pytest"
    target_root.mkdir()
    module_args = [
        argument
        for module_name in DOWNSTREAM_PYTEST_MODULES
        for argument in ("--included-module", module_name)
    ]
    placeholder_args = azure_provider_cli_args_for_modules(DOWNSTREAM_PYTEST_MODULES)

    # placeholder_args already supplies --repository and --security-contact for
    # this fixture's module set (Azure modules resolve host_provider to "dual"),
    # so they are not repeated here.
    result = run_materialize(
        REPO_ROOT,
        target_root,
        "--source-repo",
        SOURCE_REPO,
        "--last-reviewed-template-commit",
        FULL_SHA,
        *module_args,
        *placeholder_args,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    run_git(target_root, "init", "-q")
    run_git(target_root, "add", ".")
    return target_root


def run_downstream_pytest_gate(
    target_root: Path,
    *pytest_args: str,
) -> subprocess.CompletedProcess[str]:
    """Run the official downstream pytest gate in a materialized tree."""
    env = os.environ.copy()
    src_path = str(target_root / "src")
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        src_path if not existing_pythonpath else os.pathsep.join((src_path, existing_pythonpath))
    )
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            *pytest_args,
            "-m",
            "not upstream_template_only",
        ],
        cwd=target_root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
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
    marker_path = repo_root / ".template-sync" / "marker.yml"
    module_args: list[str]
    if marker_path.is_file():
        # The reporter reads the retained module set from the marker, so the
        # caller's included_modules would otherwise be silently ignored. Assert
        # the marker records the same module set so drift between the test's
        # intent and the materialized marker is caught rather than hidden.
        marker_data = load_yaml(marker_path)
        assert isinstance(marker_data, dict), marker_path
        recorded_modules = marker_data["template_sync"]["included_modules"]
        assert set(recorded_modules) == set(included_modules), (
            f"marker included_modules {sorted(recorded_modules)!r} do not match "
            f"requested {sorted(included_modules)!r}"
        )
        module_args = []
    else:
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


def azure_provider_fields_for_modules(included_modules: tuple[str, ...]) -> dict[str, str]:
    """Return marker-shaped Azure provider fields for retained Azure modules."""
    module_set = set(included_modules)
    if not module_set & AZURE_TEMPLATE_MODULES:
        return {}
    host_provider = "dual" if module_set & GITHUB_HOST_TEMPLATE_MODULES else "azure-devops-services"
    return {"host_provider": host_provider, **AZURE_PROVIDER_BASE_FIELDS}


def azure_provider_cli_args_for_modules(included_modules: tuple[str, ...]) -> tuple[str, ...]:
    """Return CLI placeholder args needed by Azure-aware materialization fixtures."""
    provider_fields = azure_provider_fields_for_modules(included_modules)
    if not provider_fields:
        return ()
    args = [
        "--host-provider",
        provider_fields["host_provider"],
        "--security-contact",
        "security@example.com",
        "--vscode-title",
        provider_fields["azure_devops_repository"],
    ]
    if provider_fields["host_provider"] == "dual":
        args.extend(["--repository", "octocat/hello-world"])
    for field_name, value in AZURE_PROVIDER_BASE_FIELDS.items():
        flag = "--" + field_name.replace("_", "-")
        args.extend([flag, value])
    return tuple(args)


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


def test_materializer_help_documents_license_preservation(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The materializer help output documents license-preservation inputs."""
    with pytest.raises(SystemExit) as error:
        materializer.parse_args(["--help"])

    captured = capsys.readouterr()
    assert error.value.code == 0
    assert "--preserve-existing-license" in captured.out
    assert "--license-source-path" in captured.out


@pytest.mark.parametrize(
    "source_path",
    [
        pytest.param("LICENSE.txt", id="txt"),
        pytest.param("LICENSE.md", id="markdown"),
        pytest.param("docs/OWNER-LICENSE", id="owner-approved-custom-path"),
    ],
)
def test_preserve_existing_license_source_to_root_license_and_records_override(
    tmp_path: Path,
    source_path: str,
) -> None:
    """A downstream license source is copied byte-for-byte to root LICENSE."""
    template_root = tmp_path / "template"
    target_root = tmp_path / "target"
    target_root.mkdir()
    prepare_template(
        template_root,
        [
            {"pattern": ".template-sync/marker.yml", "requires_all": ["template-sync-support"]},
            {"pattern": "LICENSE", "requires_all": ["baseline"]},
        ],
    )
    write_file(template_root / "LICENSE", "template license text\n")
    license_bytes = b"Downstream License\r\n\r\nPreserve this exact text.\r\n"
    source_file = target_root / source_path
    source_file.parent.mkdir(parents=True, exist_ok=True)
    source_file.write_bytes(license_bytes)

    result = run_materialize(
        template_root,
        target_root,
        "--source-repo",
        SOURCE_REPO,
        "--included-module",
        "baseline",
        "--included-module",
        "template-sync-support",
        "--preserve-existing-license",
        "--license-source-path",
        source_path,
    )

    assert result.returncode == 0, result.stderr
    assert (target_root / "LICENSE").read_bytes() == license_bytes
    assert source_file.read_bytes() == license_bytes
    assert b"template license text" not in (target_root / "LICENSE").read_bytes()
    assert "License preservation notes:" in result.stdout
    assert f"preserved downstream license text from {source_path} to LICENSE" in result.stdout
    assert "Residual manual-cleanup paths:" in result.stdout
    assert source_path in result.stdout

    marker = load_yaml(target_root / ".template-sync" / "marker.yml")
    assert isinstance(marker, dict)
    template_sync = marker["template_sync"]
    assert isinstance(template_sync, dict)
    local_overrides = template_sync["local_overrides"]
    assert isinstance(local_overrides, list)
    license_override = next(
        override
        for override in local_overrides
        if isinstance(override, dict) and override.get("path") == "LICENSE"
    )
    assert license_override["default_decision"] == "SKIP"
    assert source_path in license_override["reason"]


def test_preserve_existing_license_auto_selects_single_alternate_candidate(
    tmp_path: Path,
) -> None:
    """The preservation flag can auto-select one unambiguous root candidate."""
    template_root = tmp_path / "template"
    target_root = tmp_path / "target"
    target_root.mkdir()
    prepare_template(
        template_root,
        [{"pattern": "LICENSE", "requires_all": ["baseline"]}],
    )
    write_file(template_root / "LICENSE", "template license text\n")
    license_bytes = b"Downstream license from markdown.\n"
    (target_root / "LICENSE.md").write_bytes(license_bytes)

    result = run_materialize(
        template_root,
        target_root,
        "--source-repo",
        SOURCE_REPO,
        "--included-module",
        "baseline",
        "--preserve-existing-license",
    )

    assert result.returncode == 0, result.stderr
    assert (target_root / "LICENSE").read_bytes() == license_bytes
    assert (target_root / "LICENSE.md").read_bytes() == license_bytes


def test_preserve_existing_license_rejects_same_path_source(
    tmp_path: Path,
) -> None:
    """Root LICENSE preservation stays on the existing local-overrides SKIP path."""
    template_root = tmp_path / "template"
    target_root = tmp_path / "target"
    target_root.mkdir()
    prepare_template(template_root, [{"pattern": "LICENSE", "requires_all": ["baseline"]}])
    write_file(template_root / "LICENSE", "template license text\n")
    write_file(target_root / "LICENSE", "downstream license text\n")

    result = run_materialize(
        template_root,
        target_root,
        "--source-repo",
        SOURCE_REPO,
        "--included-module",
        "baseline",
        "--preserve-existing-license",
        "--license-source-path",
        "LICENSE",
    )

    assert result.returncode == 1
    assert "same-path license preservation" in result.stderr
    assert "local_overrides" in result.stderr
    assert read_file(target_root / "LICENSE") == "downstream license text\n"


def test_same_path_license_preservation_still_uses_local_override_skip(
    tmp_path: Path,
) -> None:
    """A downstream root LICENSE is preserved by the existing SKIP mechanism."""
    template_root = tmp_path / "template"
    target_root = tmp_path / "target"
    target_root.mkdir()
    prepare_template(
        template_root,
        [
            {"pattern": ".template-sync/marker.yml", "requires_all": ["template-sync-support"]},
            {"pattern": "LICENSE", "requires_all": ["baseline"]},
        ],
    )
    write_file(template_root / "LICENSE", "template license text\n")
    write_file(target_root / "LICENSE", "downstream license text\n")
    write_yaml(
        target_root / "decisions.yml",
        marker_document(
            ["baseline", "template-sync-support"],
            local_overrides=[
                {
                    "path": "LICENSE",
                    "default_decision": "SKIP",
                    "reason": "Keep downstream root license text.",
                }
            ],
        ),
    )

    result = run_materialize(
        template_root,
        target_root,
        "--decisions-file",
        "decisions.yml",
    )

    assert result.returncode == 0, result.stderr
    assert read_file(target_root / "LICENSE") == "downstream license text\n"
    assert "Skipped paths:" in result.stdout
    assert "LICENSE" in result.stdout


def test_preserve_existing_license_rejects_existing_root_license_conflict(
    tmp_path: Path,
) -> None:
    """Normalization refuses to choose between an existing root and alternate license."""
    template_root = tmp_path / "template"
    target_root = tmp_path / "target"
    target_root.mkdir()
    prepare_template(template_root, [{"pattern": "LICENSE", "requires_all": ["baseline"]}])
    write_file(template_root / "LICENSE", "template license text\n")
    write_file(target_root / "LICENSE", "existing root license\n")
    write_file(target_root / "LICENSE.txt", "alternate license text\n")

    result = run_materialize(
        template_root,
        target_root,
        "--source-repo",
        SOURCE_REPO,
        "--included-module",
        "baseline",
        "--preserve-existing-license",
        "--license-source-path",
        "LICENSE.txt",
    )

    assert result.returncode == 1
    assert "root LICENSE already exists" in result.stderr
    assert "same-path local_overrides SKIP" in result.stderr
    assert read_file(target_root / "LICENSE") == "existing root license\n"


def test_preserve_existing_license_rejects_multiple_auto_candidates(
    tmp_path: Path,
) -> None:
    """Ambiguous license candidates require an explicit owner-approved source."""
    template_root = tmp_path / "template"
    target_root = tmp_path / "target"
    target_root.mkdir()
    prepare_template(template_root, [{"pattern": "LICENSE", "requires_all": ["baseline"]}])
    write_file(template_root / "LICENSE", "template license text\n")
    write_file(target_root / "LICENSE.txt", "first candidate\n")
    write_file(target_root / "LICENSE.md", "second candidate\n")

    result = run_materialize(
        template_root,
        target_root,
        "--source-repo",
        SOURCE_REPO,
        "--included-module",
        "baseline",
        "--preserve-existing-license",
    )

    assert result.returncode == 1
    assert "Multiple candidate license source paths found" in result.stderr
    assert "LICENSE.md" in result.stderr
    assert "LICENSE.txt" in result.stderr
    assert "owner-approved source path" in result.stderr
    assert not (target_root / "LICENSE").exists()


def test_preserve_existing_license_rejects_missing_source_path(
    tmp_path: Path,
) -> None:
    """A requested license source path must already exist."""
    template_root = tmp_path / "template"
    target_root = tmp_path / "target"
    target_root.mkdir()
    prepare_template(template_root, [{"pattern": "LICENSE", "requires_all": ["baseline"]}])
    write_file(template_root / "LICENSE", "template license text\n")

    result = run_materialize(
        template_root,
        target_root,
        "--source-repo",
        SOURCE_REPO,
        "--included-module",
        "baseline",
        "--preserve-existing-license",
        "--license-source-path",
        "LICENSE.txt",
    )

    assert result.returncode == 1
    assert "License source path does not exist: LICENSE.txt" in result.stderr


def test_preserve_existing_license_rejects_directory_source_path(
    tmp_path: Path,
) -> None:
    """A license source path must be a regular text file."""
    template_root = tmp_path / "template"
    target_root = tmp_path / "target"
    target_root.mkdir()
    prepare_template(template_root, [{"pattern": "LICENSE", "requires_all": ["baseline"]}])
    write_file(template_root / "LICENSE", "template license text\n")
    (target_root / "LICENSE.txt").mkdir()

    result = run_materialize(
        template_root,
        target_root,
        "--source-repo",
        SOURCE_REPO,
        "--included-module",
        "baseline",
        "--preserve-existing-license",
        "--license-source-path",
        "LICENSE.txt",
    )

    assert result.returncode == 1
    assert "License source path must reference a regular text file" in result.stderr
    assert "LICENSE.txt" in result.stderr


def test_preserve_existing_license_rejects_symlink_source_path(
    tmp_path: Path,
) -> None:
    """A license source path must not traverse or be a symlink."""
    template_root = tmp_path / "template"
    target_root = tmp_path / "target"
    target_root.mkdir()
    prepare_template(template_root, [{"pattern": "LICENSE", "requires_all": ["baseline"]}])
    write_file(template_root / "LICENSE", "template license text\n")
    outside_license = tmp_path / "outside-license.txt"
    outside_license.write_text("outside license\n", encoding="utf-8")
    try:
        (target_root / "LICENSE.txt").symlink_to(outside_license)
    except OSError as error:
        pytest.skip(f"Symlink creation unavailable in this environment: {error}")

    result = run_materialize(
        template_root,
        target_root,
        "--source-repo",
        SOURCE_REPO,
        "--included-module",
        "baseline",
        "--preserve-existing-license",
        "--license-source-path",
        "LICENSE.txt",
    )

    assert result.returncode == 1
    assert "--license-source-path must not traverse a symlink" in result.stderr
    assert not (target_root / "LICENSE").exists()


@pytest.mark.parametrize(
    ("license_bytes", "expected_message"),
    [
        pytest.param(b"license\x00text\n", "NUL bytes were found", id="nul-byte"),
        pytest.param(b"\xff\xfeinvalid utf-8\n", "must be UTF-8 text", id="invalid-utf8"),
    ],
)
def test_preserve_existing_license_rejects_non_text_source(
    tmp_path: Path,
    license_bytes: bytes,
    expected_message: str,
) -> None:
    """License preservation rejects non-text source files before writing LICENSE."""
    template_root = tmp_path / "template"
    target_root = tmp_path / "target"
    target_root.mkdir()
    prepare_template(template_root, [{"pattern": "LICENSE", "requires_all": ["baseline"]}])
    write_file(template_root / "LICENSE", "template license text\n")
    (target_root / "LICENSE.txt").write_bytes(license_bytes)

    result = run_materialize(
        template_root,
        target_root,
        "--source-repo",
        SOURCE_REPO,
        "--included-module",
        "baseline",
        "--preserve-existing-license",
        "--license-source-path",
        "LICENSE.txt",
    )

    assert result.returncode == 1
    assert expected_message in result.stderr
    assert not (target_root / "LICENSE").exists()


def test_read_license_source_bytes_reports_unreadable_source_without_absolute_path(
    tmp_path: Path,
) -> None:
    """Unreadable license source diagnostics include the safe relative path only."""
    secret_path = tmp_path / "private" / "LICENSE.txt"

    def unreadable() -> bytes:
        raise PermissionError(13, "Permission denied", str(secret_path))

    with pytest.raises(materializer.MaterializationError) as excinfo:
        materializer.read_license_source_bytes(
            secret_path,
            "LICENSE.txt",
            read_bytes=unreadable,
        )

    message = str(excinfo.value)
    assert "Unable to read license source LICENSE.txt" in message
    assert "PermissionError: Permission denied" in message
    assert str(secret_path) not in message


@pytest.mark.upstream_template_only
def test_materialized_downstream_pytest_gate_collects(
    tmp_path: Path,
) -> None:
    """A Terraform/PowerShell-excluded downstream collects the pytest gate."""
    target_root = materialize_downstream_pytest_fixture(tmp_path)

    result = run_downstream_pytest_gate(target_root, "--collect-only", "-q")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "test_run_first_adoption_checks.py" in result.stdout
    assert "test_template_manifest.py" not in result.stdout


@pytest.mark.slow
@pytest.mark.upstream_template_only
def test_materialized_downstream_pytest_gate_passes(
    tmp_path: Path,
) -> None:
    """A Terraform/PowerShell-excluded downstream passes the pytest gate."""
    target_root = materialize_downstream_pytest_fixture(tmp_path)

    result = run_downstream_pytest_gate(target_root, "-q")

    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    ("included_modules", "authorize_protected_files"),
    OPTIONAL_PRUNING_FIXTURES,
)
def test_materialized_optional_pruning_retained_tests_have_no_stale_markers(
    tmp_path: Path,
    included_modules: tuple[str, ...],
    authorize_protected_files: bool,
) -> None:
    """Materialized optional-pruning fixtures carry no stale retained-test markers."""
    target_root = materialize_module_fixture(
        tmp_path,
        included_modules,
        authorize_protected_files=authorize_protected_files,
    )
    run_git(target_root, "init", "-q")
    run_git(target_root, "add", ".")

    report_result = run_excluded_module_report(target_root, included_modules)
    marker = load_yaml(target_root / ".template-sync" / "marker.yml")
    assert isinstance(marker, dict)
    recorded_modules = marker["template_sync"]["included_modules"]
    assert set(recorded_modules) == set(included_modules)

    assert report_result.returncode == 0, report_result.stderr
    assert "State source: marker (.template-sync/marker.yml)" in report_result.stdout

    excluded_modules = set(FULL_TEMPLATE_MODULES) - set(included_modules)
    for module_name, relative_paths in OPTIONAL_STACK_OWNED_PATHS.items():
        if module_name not in excluded_modules:
            continue
        for relative_path in relative_paths:
            assert not (target_root / relative_path).exists(), relative_path

    test_files = retained_test_files(target_root)
    assert test_files, "fixture must retain template-support pytest files"
    for test_file in test_files:
        relative_path = test_file.relative_to(target_root).as_posix()
        text = read_file(test_file)
        for module_name, marker_names in OPTIONAL_STACK_INLINE_MARKERS.items():
            if module_name not in excluded_modules:
                continue
            for marker_name in marker_names:
                for line in text.splitlines():
                    stripped_line = line.lstrip()
                    assert not stripped_line.startswith(
                        f"# template-sync: begin {marker_name}"
                    ), f"{relative_path}: {marker_name}"
                    assert not stripped_line.startswith(
                        f"# template-sync: end {marker_name}"
                    ), f"{relative_path}: {marker_name}"
                    assert not stripped_line.startswith(
                        f"<!-- template-sync: begin {marker_name}"
                    ), f"{relative_path}: {marker_name}"
                    assert not stripped_line.startswith(
                        f"<!-- template-sync: end {marker_name}"
                    ), f"{relative_path}: {marker_name}"


def test_materialized_azure_pipelines_without_github_actions_omits_actionlint(
    tmp_path: Path,
) -> None:
    """Azure-only CI adoption must not retain GitHub Actions-only validation."""
    target_root = materialize_module_fixture(
        tmp_path,
        ("baseline", "azure-pipelines", "yaml"),
    )

    assert (target_root / ".azuredevops" / "pipelines" / "README.md").is_file()
    assert (target_root / ".azuredevops" / "pipelines" / "precommit.yml").is_file()
    assert (target_root / ".azuredevops" / "pipelines" / "check-placeholders.yml").is_file()
    assert (target_root / ".azuredevops" / "pipelines" / "data-ci.yml").is_file()
    assert not (target_root / ".github" / "workflows").exists()
    assert not (target_root / ".azuredevops" / "pipelines" / "markdownlint.yml").exists()

    precommit_text = read_file(target_root / ".pre-commit-config.yaml")
    data_pipeline_text = read_file(target_root / ".azuredevops" / "pipelines" / "data-ci.yml")

    assert "github-actions-only" not in precommit_text
    assert "actionlint" not in precommit_text
    assert "actionlint" not in data_pipeline_text
    assert "pre-commit run yamllint --all-files" in data_pipeline_text


def test_materialized_template_sync_support_only_first_adoption_plan_omits_powershell(
    tmp_path: Path,
) -> None:
    """A no-PowerShell support fixture does not plan stale PowerShell checks."""
    target_root = materialize_module_fixture(
        tmp_path,
        ("baseline", "template-sync-support"),
    )
    run_git(target_root, "init", "-q")
    run_git(target_root, "add", ".")

    result = subprocess.run(
        [
            sys.executable,
            ".template-sync/scripts/run_first_adoption_checks.py",
            "--repo-root",
            str(target_root),
            "--plan-only",
        ],
        cwd=target_root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "first_adoption_quality_reports.py line-endings" in result.stdout
    assert "first_adoption_quality_reports.py path-references" in result.stdout
    assert "first_adoption_quality_reports.py powershell" not in result.stdout


def test_materialized_gitattributes_baseline_lf_pins_survive_optional_stack_exclusion(
    tmp_path: Path,
) -> None:
    """Baseline-owned LF pins remain after Terraform and PowerShell are excluded."""
    target_root = materialize_module_fixture(
        tmp_path,
        DOWNSTREAM_PYTEST_MODULES,
    )
    run_git(target_root, "init", "-q")

    attributes_by_path = git_check_attributes_in_repo(
        target_root,
        BASELINE_GITATTRIBUTES_LF_PIN_PATHS,
    )

    for path, attributes in attributes_by_path.items():
        assert attributes["text"] == "set", path
        assert attributes["eol"] == "lf", path


def test_materialized_gitattributes_strips_lfs_when_git_lfs_module_excluded(
    tmp_path: Path,
) -> None:
    """Repositories that do not adopt git-lfs receive no LFS attributes."""
    target_root = materialize_module_fixture(tmp_path, ("baseline",))
    run_git(target_root, "init", "-q")

    gitattributes_text = read_file(target_root / ".gitattributes")
    assert "git-lfs-only" not in gitattributes_text
    assert "filter=lfs" not in gitattributes_text

    attributes_by_path = git_check_attributes_in_repo(
        target_root,
        GIT_LFS_MANAGED_ATTRIBUTE_PATHS,
        GIT_LFS_ATTRIBUTES_TO_CHECK,
    )

    for path, attributes in attributes_by_path.items():
        assert attributes["filter"] == "unspecified", path
        assert attributes["diff"] == "unspecified", path
        assert attributes["merge"] == "unspecified", path
        assert attributes["text"] == "unspecified", path


@pytest.mark.upstream_template_only
def test_materialized_gitattributes_retains_lfs_when_git_lfs_module_included(
    tmp_path: Path,
) -> None:
    """Repositories that adopt git-lfs receive the opt-in LFS attributes."""
    target_root = materialize_module_fixture(tmp_path, ("baseline", "git-lfs"))
    run_git(target_root, "init", "-q")

    gitattributes_text = read_file(target_root / ".gitattributes")
    assert "git-lfs-only" in gitattributes_text
    assert "filter=lfs diff=lfs merge=lfs -text" in gitattributes_text

    attributes_by_path = git_check_attributes_in_repo(
        target_root,
        GIT_LFS_MANAGED_ATTRIBUTE_PATHS,
        GIT_LFS_ATTRIBUTES_TO_CHECK,
    )

    for path, attributes in attributes_by_path.items():
        assert attributes["filter"] == "lfs", path
        assert attributes["diff"] == "lfs", path
        assert attributes["merge"] == "lfs", path
        assert attributes["text"] == "unset", path


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
    included_modules: tuple[str, ...] = NO_DATA_NO_TEMPLATE_SYNC_MODULES
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
    included_modules: tuple[str, ...] = NO_DATA_NO_TEMPLATE_SYNC_MODULES
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
    included_modules: tuple[str, ...] = NO_DATA_NO_TEMPLATE_SYNC_MODULES
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


@pytest.mark.parametrize("module_name", sorted(AZURE_TEMPLATE_MODULES))
def test_materialized_azure_support_guide_retained_by_any_azure_module(
    tmp_path: Path,
    module_name: str,
) -> None:
    """Any Azure host module retains the durable Azure DevOps guide."""
    target_root = materialize_module_fixture(tmp_path, ("baseline", module_name))

    guide_path = target_root / "docs" / "azure-devops-support.md"
    assert guide_path.is_file()
    assert "Azure DevOps Services Support Guide" in read_file(guide_path)


def test_materialized_all_azure_modules_retain_guide_and_reference_links(
    tmp_path: Path,
) -> None:
    """A full Azure host selection keeps the guide and guarded shared-doc links."""
    target_root = materialize_module_fixture(
        tmp_path, ("baseline", *sorted(AZURE_TEMPLATE_MODULES))
    )

    assert (target_root / "docs" / "azure-devops-support.md").is_file()
    readme_text = read_file(target_root / "README.md")
    contributing_text = read_file(target_root / "CONTRIBUTING.md")

    assert "docs/azure-devops-support.md" in readme_text
    assert "docs/azure-devops-support.md" in contributing_text


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

    result = run_materialize(
        template_root,
        target_root,
        "--decisions-file",
        "decisions.yml",
    )

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

    result = run_materialize(
        template_root,
        target_root,
        "--decisions-file",
        "decisions.yml",
    )

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


def test_materializer_json_args_file_supplies_package_metadata(
    tmp_path: Path,
) -> None:
    """The materializer accepts shell-safe JSON args and updates package identity."""
    template_root = tmp_path / "template"
    target_root = tmp_path / "target"
    target_root.mkdir()
    prepare_template(
        template_root,
        [
            {"pattern": "package.json", "requires_all": ["baseline"]},
            {"pattern": "package-lock.json", "requires_all": ["baseline"]},
        ],
        include_placeholder_helper=True,
    )
    write_json(
        template_root / "package.json",
        {
            "name": "copilot-repo-template",
            "version": "1.0.0",
            "description": "Template repository with Copilot instructions",
            "private": True,
            "author": "Frank Lesniak",
        },
    )
    write_json(
        template_root / "package-lock.json",
        {
            "name": "copilot-repo-template",
            "version": "1.0.0",
            "lockfileVersion": 3,
            "packages": {
                "": {
                    "name": "copilot-repo-template",
                    "version": "1.0.0",
                },
                "node_modules/example": {"version": "9.9.9"},
            },
        },
    )
    args_file = tmp_path / "materialize.args.json"
    write_json(
        args_file,
        {
            "target_root": str(target_root),
            "source_repo": SOURCE_REPO,
            "included_modules": ["baseline"],
            "package_name": "downstream-markdown-tools",
            "package_description": "Markdown tooling for downstream docs, with $literal text",
            "package_author": "Example Org",
            "package_version": "2.0.0",
        },
    )

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--template-root",
            str(template_root),
            "--args-file",
            str(args_file),
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    package_json = json.loads(read_file(target_root / "package.json"))
    package_lock = json.loads(read_file(target_root / "package-lock.json"))
    assert package_json["name"] == "downstream-markdown-tools"
    assert package_json["description"] == "Markdown tooling for downstream docs, with $literal text"
    assert package_json["author"] == "Example Org"
    assert package_json["version"] == "2.0.0"
    assert package_lock["name"] == "downstream-markdown-tools"
    assert package_lock["version"] == "2.0.0"
    assert package_lock["packages"][""]["name"] == "downstream-markdown-tools"
    assert package_lock["packages"][""]["version"] == "2.0.0"
    assert package_lock["packages"]["node_modules/example"]["version"] == "9.9.9"


def test_materializer_args_file_cli_values_take_precedence(tmp_path: Path) -> None:
    """Direct CLI values override lower-priority args-file values."""
    args_file = tmp_path / "materialize.args.json"
    write_json(
        args_file,
        {
            "target_root": str(tmp_path / "from-file"),
            "source_repo": "https://example.com/from-file.git",
            "included_modules": ["python"],
            "package_name": "from-file",
        },
    )

    args = materializer.parse_args(
        [
            "--args-file",
            str(args_file),
            "--target-root",
            str(tmp_path / "from-cli"),
            "--source-repo",
            SOURCE_REPO,
            "--included-module",
            "baseline",
            "--package-name",
            "from-cli",
        ]
    )

    assert args.target_root == str(tmp_path / "from-cli")
    assert args.source_repo == SOURCE_REPO
    assert args.included_modules == ["baseline"]
    assert args.package_name == "from-cli"


def test_materializer_args_file_with_utf8_bom_is_parsed(tmp_path: Path) -> None:
    """A UTF-8 BOM (e.g. PowerShell Set-Content -Encoding UTF8) in an args file is tolerated."""
    args_file = tmp_path / "materialize.args.json"
    args_file.write_bytes(
        b"\xef\xbb\xbf"
        + json.dumps({"target_root": str(tmp_path / "target"), "source_repo": SOURCE_REPO}).encode(
            "utf-8"
        )
    )

    mapping = materializer.load_args_file_mapping(str(args_file), None)

    assert mapping["target_root"] == str(tmp_path / "target")
    assert mapping["source_repo"] == SOURCE_REPO


def test_materializer_args_file_cli_selectors_override_family(tmp_path: Path) -> None:
    """A CLI source/module selector overrides its whole args-file family, not just the same flag."""
    args_file = tmp_path / "materialize.args.json"
    write_json(
        args_file,
        {"template_ref": "v1.2.3", "included_modules_csv": "python,yaml"},
    )

    args = materializer.parse_args(
        [
            "--args-file",
            str(args_file),
            "--template-root",
            str(tmp_path / "tmpl"),
            "--target-root",
            str(tmp_path / "tgt"),
            "--source-repo",
            SOURCE_REPO,
            "--included-module",
            "baseline",
        ]
    )

    # CLI --template-root wins; the args-file source selector is skipped (no conflict error).
    assert args.template_root == str(tmp_path / "tmpl")
    assert args.template_ref is None
    # CLI --included-module wins; the args-file module selector is skipped (no merge).
    assert args.included_modules == ["baseline"]
    assert args.included_modules_csv is None


def test_materializer_args_file_decisions_path_traversal_is_rejected(
    tmp_path: Path,
) -> None:
    """Repo-relative path values supplied through args files cannot escape target root."""
    template_root = tmp_path / "template"
    target_root = tmp_path / "target"
    target_root.mkdir()
    prepare_template(template_root, [{"pattern": "README.md", "requires_all": ["baseline"]}])
    write_file(template_root / "README.md", "template readme\n")
    args_file = tmp_path / "materialize.args.json"
    write_json(
        args_file,
        {
            "target_root": str(target_root),
            "source_repo": SOURCE_REPO,
            "included_modules": ["baseline"],
            "decisions_file": "../outside.yml",
        },
    )

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--template-root",
            str(template_root),
            "--args-file",
            str(args_file),
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert result.returncode == 1
    assert "--decisions-file must not contain traversal segments" in result.stderr


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


@pytest.mark.upstream_template_only
def test_materializer_replays_azure_provider_fields_from_marker(
    tmp_path: Path,
) -> None:
    """Marker-recorded Azure provider fields drive placeholder materialization."""
    template_root = tmp_path / "template"
    target_root = tmp_path / "target"
    target_root.mkdir()
    prepare_template(
        template_root,
        [
            {"pattern": "SECURITY.md", "requires_all": ["baseline"]},
            {"pattern": "CONTRIBUTING.md", "requires_all": ["baseline"]},
            {"pattern": "CODE_OF_CONDUCT.md", "requires_all": ["baseline"]},
            {
                "pattern": ".azuredevops/platform/**",
                "requires_all": ["azure-devops-platform"],
            },
            {
                "pattern": ".azuredevops/pull_request_template.md",
                "requires_all": ["azure-devops-collaboration"],
            },
        ],
        include_placeholder_helper=True,
    )
    copy_template_file(template_root, "SECURITY.md")
    copy_template_file(template_root, "CONTRIBUTING.md")
    copy_template_file(template_root, "CODE_OF_CONDUCT.md")
    copy_template_file(template_root, ".azuredevops/platform/adoption-guidance.md")
    copy_template_file(template_root, ".azuredevops/pull_request_template.md")
    write_yaml(
        target_root / "decisions.yml",
        {
            "template_sync": {
                "source_repo": SOURCE_REPO,
                "included_modules": [
                    "baseline",
                    "template-sync-support",
                    "azure-devops-platform",
                    "azure-devops-collaboration",
                ],
                "host_provider": "azure-devops-services",
                "azure_devops_organization": "contoso",
                "azure_devops_project": "Microsoft 365",
                "azure_devops_repository": "downstream-template",
                "azure_boards_policy": "work-items",
                "azure_repos_pr_template_policy": "materialize",
                "azure_branch_policy_reviewer_guidance": "manual-follow-up",
                "azure_security_intake_policy": "manual-follow-up",
                "azure_security_product_enablement": "github-secret-protection",
                "azure_dependency_update_policy": "manual-follow-up",
            }
        },
    )

    result = run_materialize(
        template_root,
        target_root,
        "--decisions-file",
        "decisions.yml",
        "--security-contact",
        "security@example.com",
    )

    assert result.returncode == 0, result.stderr
    guidance_text = read_file(target_root / ".azuredevops" / "platform" / "adoption-guidance.md")
    assert "https://dev.azure.com/contoso/Microsoft%20365" in guidance_text
    assert "https://dev.azure.com/contoso/Microsoft%20365/_git/downstream-template" in guidance_text
    assert "AZURE_DEVOPS_PROJECT_URL" not in guidance_text
    pr_template_text = read_file(target_root / ".azuredevops" / "pull_request_template.md")
    assert "[Microsoft 365](https://dev.azure.com/contoso/Microsoft%20365)" in pr_template_text
    assert (
        "[downstream-template]"
        "(https://dev.azure.com/contoso/Microsoft%20365/_git/downstream-template)"
    ) in pr_template_text
    assert "Default branch used for PR template discovery: `main`." in pr_template_text
    assert "Azure Boards intake policy: `work-items`." in pr_template_text
    assert "not by this Markdown template" in pr_template_text
    assert "AZURE_DEVOPS_PROJECT_URL" not in pr_template_text
    security_text = read_file(target_root / "SECURITY.md")
    assert "Azure DevOps Services project" in security_text
    assert "private vulnerability reporting" not in security_text
    contributing_text = read_file(target_root / "CONTRIBUTING.md")
    assert "OWNER/REPO" not in contributing_text
    assert "https://dev.azure.com/contoso/Microsoft%20365/_git/downstream-template" in (
        contributing_text
    )
    marker = load_yaml(target_root / ".template-sync" / "marker.yml")
    assert isinstance(marker, dict)
    template_sync = marker["template_sync"]
    assert template_sync["host_provider"] == "azure-devops-services"
    assert template_sync["azure_devops_project"] == "Microsoft 365"
    assert template_sync["azure_security_product_enablement"] == "github-secret-protection"


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
@pytest.mark.upstream_template_only
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


@pytest.mark.upstream_template_only
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


@pytest.mark.upstream_template_only
def test_materializes_collaboration_policy_cli_inputs(
    tmp_path: Path,
) -> None:
    """Materialization passes collaboration policy CLI inputs to the helper."""
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
        "--security-contact",
        "security@example.com",
        "--conduct-contact",
        "conduct@example.com",
        "--issue-label-policy",
        "custom",
        "--issue-label",
        "type: bug",
        "--issue-label",
        "needs triage",
        "--discussions-policy",
        "enabled",
    )

    assert result.returncode == 0, result.stderr
    bug_report = load_yaml(target_root / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml")
    assert isinstance(bug_report, dict)
    assert bug_report["labels"] == ["type: bug", "needs triage"]
    config = load_yaml(target_root / ".github" / "ISSUE_TEMPLATE" / "config.yml")
    discussions_link = contact_link_by_name(config, "Questions & Discussions")
    assert discussions_link["url"] == "https://github.com/octo/widget/discussions"


@pytest.mark.upstream_template_only
def test_materializes_collaboration_policy_from_decisions_file(
    tmp_path: Path,
) -> None:
    """Marker-recorded collaboration policy fields feed placeholder rendering."""
    template_root = tmp_path / "template"
    target_root = tmp_path / "target"
    target_root.mkdir()
    prepare_security_reporting_template(template_root)
    follow_up_status = "Discussions enablement is still open in _TODO-repo-init.md."
    write_yaml(
        target_root / "decisions.yml",
        {
            "template_sync": {
                "source_repo": SOURCE_REPO,
                "included_modules": ["baseline"],
                "issue_label_policy": "create-manual-follow-up",
                "discussions_policy": "deferred-not-rendered",
                "collaboration_policy_follow_up_status": follow_up_status,
            }
        },
    )

    result = run_materialize(
        template_root,
        target_root,
        "--decisions-file",
        "decisions.yml",
        "--repository",
        "octo/widget",
        "--security-contact",
        "security@example.com",
        "--conduct-contact",
        "conduct@example.com",
    )

    assert result.returncode == 0, result.stderr
    bug_report = load_yaml(target_root / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml")
    assert isinstance(bug_report, dict)
    assert bug_report["labels"] == ["bug", "triage"]
    config_text = read_file(target_root / ".github" / "ISSUE_TEMPLATE" / "config.yml")
    assert "/discussions" not in config_text
    assert "_TODO-repo-init.md dependent-file status remains open" in config_text
    assert follow_up_status in config_text
    assert "issue_label_policy: create-manual-follow-up" in result.stdout
    assert "discussions_policy: deferred-not-rendered" in result.stdout


@pytest.mark.upstream_template_only
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
