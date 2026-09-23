"""Test instruction-validator byte limits and controlled native input failures."""

from __future__ import annotations

import io
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from tests._pytest_compat import pytest
from tests.test_validate_instruction_contracts import (
    SCRIPT_PATH,
    _contracts,
    _marker,
    _write_common_contract_repo,
    _write_yaml,
)

SCRIPT_DIR = SCRIPT_PATH.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import validate_instruction_contracts as validator  # noqa: E402
from template_sync_materialization_helpers import (  # noqa: E402
    TemplateSyncMaterializationError,
    load_json_mapping,
    load_yaml_mapping,
    read_repository_text,
)

# This acceptance boundary is intentionally independent of the production value.
ACCEPTED_LIMIT = 1_048_576
INPUT_PATHS = (
    "CLAUDE.md",
    ".template-sync/instruction-contracts.yml",
    ".template-sync/manifest.yml",
    ".template-sync/marker.yml",
    "schemas/template-sync-instruction-contracts.schema.json",
    "schemas/template-sync-manifest.schema.json",
    "schemas/template-sync-marker.schema.json",
)


def _write_input_fixture(root: Path) -> None:
    """Create actual validator inputs with a minimal independent policy."""
    _write_common_contract_repo(root, _contracts(required_headings=["# Required"]))
    (root / "CLAUDE.md").write_bytes(b"# Required\n")
    _write_yaml(root, ".template-sync/marker.yml", _marker(["agent-instructions"]))


def _run_input_validator(
    root: Path, script: Path = SCRIPT_PATH, mode: str = "downstream"
) -> subprocess.CompletedProcess[str]:
    """Run the real CLI, including the downstream-only marker reader."""
    return subprocess.run(
        [sys.executable, str(script), "--repo-root", str(root), "--mode", mode],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


@pytest.mark.parametrize("relative_path", INPUT_PATHS)
@pytest.mark.parametrize("size_delta", [-1, 0, 1])
def test_cli_byte_boundary_for_each_input_family(
    tmp_path: Path, relative_path: str, size_delta: int
) -> None:
    """Every file family accepts the exact limit and rejects one excess byte."""
    _write_input_fixture(tmp_path)
    target = tmp_path / relative_path
    original = target.read_bytes()
    target_size = ACCEPTED_LIMIT + size_delta
    assert len(original) <= target_size, (
        f"{relative_path}: original fixture has {len(original)} bytes; "
        f"requested boundary is {target_size} bytes"
    )
    target.write_bytes(original + b" " * (target_size - len(original)))
    assert target.stat().st_size == target_size

    result = _run_input_validator(tmp_path)
    if size_delta <= 0:
        assert result.returncode == 0, result.stdout + result.stderr
        assert "Instruction-contract validation passed." in result.stdout
    else:
        assert result.returncode == 1, result.stdout + result.stderr
        assert relative_path in result.stderr
        assert "exceeds the 1048576-byte input limit" in result.stderr
        assert "Traceback" not in result.stderr
        assert "validation passed" not in result.stdout


@pytest.mark.parametrize("relative_path", INPUT_PATHS)
def test_cli_malformed_utf8_has_a_controlled_failure(tmp_path: Path, relative_path: str) -> None:
    """Malformed instructions, control documents and schemas fail without a traceback."""
    _write_input_fixture(tmp_path)
    (tmp_path / relative_path).write_bytes(b"# \xc3(\n")
    result = _run_input_validator(tmp_path)

    assert result.returncode == 1, result.stdout + result.stderr
    assert relative_path in result.stderr
    assert "Invalid utf-8" in result.stderr
    assert "Traceback" not in result.stderr
    assert str(tmp_path) not in result.stderr


@pytest.mark.parametrize(
    "payload",
    [b"# Required\n" + b" " * ACCEPTED_LIMIT, b"# \xc3(\n"],
    ids=["oversized", "malformed-utf8"],
)
def test_upstream_mode_uses_the_same_input_guards(tmp_path: Path, payload: bytes) -> None:
    """Upstream validation cannot bypass the downstream-tested byte/decoding checks."""
    _write_input_fixture(tmp_path)
    (tmp_path / ".template-sync/marker.yml").unlink()
    (tmp_path / "CLAUDE.md").write_bytes(payload)
    result = _run_input_validator(tmp_path, mode="upstream-template")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "CLAUDE.md" in result.stderr
    assert "Traceback" not in result.stderr


def test_multibyte_limit_measures_bytes_before_decode(tmp_path: Path) -> None:
    """A complete multibyte character fits at the limit; one excess byte does not."""
    target = tmp_path / "policy.md"
    prefix = b"a" * (ACCEPTED_LIMIT - 2)
    target.write_bytes(prefix + "é".encode())
    assert read_repository_text(target, tmp_path, maximum_bytes=ACCEPTED_LIMIT) == (
        "a" * (ACCEPTED_LIMIT - 2) + "é"
    )
    target.write_bytes(prefix + "€".encode())
    with pytest.raises(TemplateSyncMaterializationError, match="exceeds"):
        read_repository_text(target, tmp_path, maximum_bytes=ACCEPTED_LIMIT)


@pytest.mark.parametrize("limit", [None, 128])
def test_reader_preserves_encoding_newlines_and_parser_failures(
    tmp_path: Path, limit: int | None
) -> None:
    """The optional cap does not change BOM, newline, mapping or syntax contracts."""
    target = tmp_path / "data.txt"
    target.write_bytes(b"one\r\ntwo\rthree\n")
    assert read_repository_text(target, tmp_path, maximum_bytes=limit) == "one\ntwo\nthree\n"
    target.write_bytes(b"\xef\xbb\xbfkey: value\r\n")
    assert load_yaml_mapping(target, tmp_path, maximum_bytes=limit) == {"key": "value"}
    target.write_bytes(b'\xef\xbb\xbf{"key": "value"}')
    with pytest.raises(TemplateSyncMaterializationError, match="Invalid JSON"):
        load_json_mapping(target, tmp_path, maximum_bytes=limit)
    target.write_bytes(b'{"key": "value"}')
    assert load_json_mapping(target, tmp_path, maximum_bytes=limit) == {"key": "value"}
    target.write_bytes(b"key: [")
    with pytest.raises(TemplateSyncMaterializationError, match="Invalid YAML"):
        load_yaml_mapping(target, tmp_path, maximum_bytes=limit)
    for loader in (load_json_mapping, load_yaml_mapping):
        target.write_bytes(b"[]")
        with pytest.raises(TemplateSyncMaterializationError, match="must contain"):
            loader(target, tmp_path, maximum_bytes=limit)
        target.write_bytes(b"\xc3(")
        with pytest.raises(TemplateSyncMaterializationError, match="Invalid utf-8") as caught:
            loader(target, tmp_path, maximum_bytes=limit)
        assert isinstance(caught.value.__cause__, UnicodeDecodeError)


def test_reader_preserves_absence_kind_containment_and_io_error(tmp_path: Path) -> None:
    """The new reader changes neither optional absence nor existing containment."""
    assert validator.read_instruction_file(tmp_path, "absent.md") is None
    (tmp_path / "directory.md").mkdir()
    with pytest.raises(validator.InstructionContractValidationError, match="not a regular file"):
        validator.read_instruction_file(tmp_path, "directory.md")
    with pytest.raises(TemplateSyncMaterializationError, match="escapes"):
        validator.read_instruction_file(tmp_path, "../outside.md")
    with pytest.raises(
        TemplateSyncMaterializationError, match="Unable to read absent.md"
    ) as caught:
        read_repository_text(tmp_path / "absent.md", tmp_path, maximum_bytes=128)
    assert isinstance(caught.value.__cause__, OSError)
    assert str(tmp_path) not in str(caught.value)


def test_reader_bounds_the_actual_stream_request(tmp_path: Path, monkeypatch: Any) -> None:
    """A finite spy rejects an unbounded read even when its returned text is tiny."""
    requests: list[int] = []

    class BoundedStream(io.BytesIO):
        """Fail on any request that exceeds the independent read allowance."""

        def read(self, size: int | None = -1) -> bytes:
            assert size is not None and 0 <= size <= 129, "unbounded stream request"
            requests.append(size)
            return super().read(size)

    def open_stream(path: Path, *args: Any, **kwargs: Any) -> BoundedStream:
        assert path == tmp_path / "policy.md"
        assert args == ("rb",)
        return BoundedStream(b"small\r\n")

    monkeypatch.setattr(Path, "open", open_stream)
    assert read_repository_text(tmp_path / "policy.md", tmp_path, maximum_bytes=128) == "small\n"
    assert requests


@pytest.mark.parametrize("guard", ["size", "decode", "read"])
def test_independent_input_oracles_kill_removed_guards(tmp_path: Path, guard: str) -> None:
    """Each actual guard is necessary for an independently stated acceptance check."""
    fixture = tmp_path / "fixture"
    _write_input_fixture(fixture)
    mutant_dir = tmp_path / "mutant"
    mutant_dir.mkdir()
    for source in SCRIPT_DIR.iterdir():
        if source.suffix == ".py" and source.is_file() and not source.is_symlink():
            shutil.copyfile(source, mutant_dir / source.name)
    shared = SCRIPT_DIR.parents[1] / ".github" / "scripts"
    for name in ("instruction_contract_core.py", "instruction_contract_support.py"):
        shutil.copyfile(shared / name, mutant_dir / name)
    helper = mutant_dir / "instruction_contract_support.py"
    source_text = helper.read_text(encoding="utf-8")
    substitutions = {
        "size": ("if len(data) > maximum_bytes:", "if False:"),
        "decode": ("except UnicodeDecodeError as error:", "except UnicodeEncodeError as error:"),
        "read": ("stream.read(maximum_bytes + 1)", "stream.read()"),
    }
    old, new = substitutions[guard]
    assert source_text.count(old) == 1
    helper.write_text(source_text.replace(old, new), encoding="utf-8")

    if guard == "read":
        # The spy oracle is separate from the predicate being removed.
        probe = """import io
from pathlib import Path
from template_sync_materialization_helpers import read_repository_text
class FiniteStream(io.BytesIO):
    def read(self, size=-1):
        assert 0 <= size <= 129, "unbounded stream request"
        return super().read(size)
Path.open = lambda *args, **kwargs: FiniteStream(b"valid")
assert read_repository_text(Path("policy.md"), Path("."), maximum_bytes=128) == "valid"
"""
        baseline = subprocess.run(
            [sys.executable, "-c", probe],
            cwd=SCRIPT_DIR,
            capture_output=True,
            text=True,
            check=False,
        )
        changed = subprocess.run(
            [sys.executable, "-c", probe],
            cwd=mutant_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        assert baseline.returncode == 0, baseline.stderr
        assert changed.returncode != 0
        assert "unbounded stream request" in changed.stderr
    else:
        payload = b"# Required\n" + b" " * ACCEPTED_LIMIT if guard == "size" else b"# \xc3(\n"
        (fixture / "CLAUDE.md").write_bytes(payload)
        baseline = _run_input_validator(fixture)
        changed = _run_input_validator(fixture, mutant_dir / SCRIPT_PATH.name)
        assert baseline.returncode == 1 and "Traceback" not in baseline.stderr
        if guard == "size":
            assert changed.returncode == 0, changed.stdout + changed.stderr
        else:
            assert changed.returncode == 1
            assert "UnicodeDecodeError" in changed.stderr and "Traceback" in changed.stderr
