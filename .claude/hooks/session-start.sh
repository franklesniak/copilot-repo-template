#!/bin/bash
# SessionStart hook: install the tools used by the authoritative local gate in
# Claude Code web sessions. Web-only by design; developer workstations manage
# their own toolchain.
#
# Keep TERRAFORM_VERSION in sync with every `terraform_version:` input passed
# to `hashicorp/setup-terraform@v4` in .github/workflows/. Those pins currently
# live in precommit-ci.yml, auto-fix-precommit.yml, and terraform-ci.yml.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

TERRAFORM_VERSION="1.14.4"
INSTALL_DIR="/usr/local/bin"

persist_path_prepend() {
  local path_entry="$1"

  case ":${PATH}:" in
    *":${path_entry}:"*) ;;
    *) export PATH="${path_entry}:${PATH}" ;;
  esac

  # CLAUDE_ENV_FILE persists exports across hook invocations and subsequent
  # shells; guard against duplicate entries on re-runs.
  if [ -n "${CLAUDE_ENV_FILE:-}" ] \
    && ! grep -Fq "export PATH=\"${path_entry}:" "$CLAUDE_ENV_FILE" 2>/dev/null; then
    echo "export PATH=\"${path_entry}:\$PATH\"" >> "$CLAUDE_ENV_FILE"
  fi
}

python_executable() {
  if command -v python >/dev/null 2>&1; then
    command -v python
  elif command -v python3 >/dev/null 2>&1; then
    command -v python3
  else
    return 1
  fi
}

python_user_bin_dir() {
  local python_bin="$1"
  local user_base

  user_base="$("$python_bin" -m site --user-base)"
  printf '%s/bin\n' "$user_base"
}

ensure_pre_commit() {
  local pre_commit_bin_dir
  local python_bin

  if command -v pre-commit >/dev/null 2>&1; then
    echo "pre-commit already available at $(command -v pre-commit)"
    return 0
  fi

  if command -v uv >/dev/null 2>&1; then
    pre_commit_bin_dir="${UV_TOOL_BIN_DIR:-${HOME:?HOME or UV_TOOL_BIN_DIR must be set}/.local/bin}"
    persist_path_prepend "$pre_commit_bin_dir"
    if ! command -v pre-commit >/dev/null 2>&1; then
      echo "Installing pre-commit with uv tool"
      uv tool install pre-commit
    fi
  elif command -v pipx >/dev/null 2>&1; then
    pre_commit_bin_dir="${PIPX_BIN_DIR:-${HOME:?HOME or PIPX_BIN_DIR must be set}/.local/bin}"
    persist_path_prepend "$pre_commit_bin_dir"
    if ! command -v pre-commit >/dev/null 2>&1; then
      echo "Installing pre-commit with pipx"
      pipx install pre-commit
    fi
  else
    python_bin="$(python_executable)" || {
      echo "No supported pre-commit installer found; need uv, pipx, python, or python3" >&2
      exit 1
    }
    pre_commit_bin_dir="$(python_user_bin_dir "$python_bin")"
    persist_path_prepend "$pre_commit_bin_dir"
    if ! command -v pre-commit >/dev/null 2>&1; then
      echo "Installing pre-commit with ${python_bin} -m pip --user"
      "$python_bin" -m pip install --user pre-commit
    fi
  fi

  if ! command -v pre-commit >/dev/null 2>&1; then
    echo "pre-commit installation completed, but pre-commit is not on PATH" >&2
    exit 1
  fi

  echo "$(pre-commit --version) available at $(command -v pre-commit)"
}

ensure_pre_commit

# Ensure the binary we install below resolves first for the rest of the
# session, even if a different `terraform` exists earlier on the base
# image's PATH. Reuse persist_path_prepend so PATH handling matches the
# pre-commit bootstrap above: update PATH for this hook run and persist it
# via CLAUDE_ENV_FILE for subsequent shells.
persist_path_prepend "$INSTALL_DIR"

# Idempotency: check the install location specifically so a stale or
# differently-versioned terraform earlier on PATH cannot mask us. Parse
# the plain-text first line of `terraform version` (e.g. "Terraform
# v1.14.4") with awk so the check does not depend on python3, jq, or
# any other interpreter that may be absent from the base image.
if [ -x "$INSTALL_DIR/terraform" ]; then
  current="$("$INSTALL_DIR/terraform" version 2>/dev/null \
    | awk 'NR==1 {sub(/^v/, "", $2); print $2; exit}' \
    || true)"
  if [ "$current" = "$TERRAFORM_VERSION" ]; then
    echo "Terraform ${TERRAFORM_VERSION} already installed at ${INSTALL_DIR}/terraform"
    exit 0
  fi
fi

case "$(uname -m)" in
  x86_64) tf_arch="amd64" ;;
  aarch64|arm64) tf_arch="arm64" ;;
  *) echo "Unsupported architecture: $(uname -m)" >&2; exit 1 ;;
esac

tf_os="$(uname -s | tr '[:upper:]' '[:lower:]')"
case "$tf_os" in
  linux|darwin) ;;
  *) echo "Unsupported OS: ${tf_os} (supported: linux, darwin)" >&2; exit 1 ;;
esac

archive="terraform_${TERRAFORM_VERSION}_${tf_os}_${tf_arch}.zip"
base="https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}"

# Portable SHA-256 digest helper. Prefers GNU coreutils `sha256sum`
# (default on Linux), falls back to BSD-style `shasum -a 256` (default on
# macOS) and finally `openssl dgst -sha256` so verification works across
# every uname -s value the OS allowlist above accepts.
compute_sha256() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
  elif command -v openssl >/dev/null 2>&1; then
    openssl dgst -sha256 "$1" | awk '{print $NF}'
  else
    echo "No SHA-256 utility available (need sha256sum, shasum, or openssl)" >&2
    return 1
  fi
}

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

echo "Downloading ${archive} from ${base}"
curl -fsSL --retry 3 --retry-delay 2 "${base}/${archive}" -o "$tmpdir/${archive}"
curl -fsSL --retry 3 --retry-delay 2 \
  "${base}/terraform_${TERRAFORM_VERSION}_SHA256SUMS" -o "$tmpdir/SHA256SUMS"

# Verify the downloaded archive against the official SHA256SUMS file
# before placing the binary on PATH. This catches corrupted downloads
# and partial tampering (e.g. a proxy that rewrites only the archive
# but leaves the SHA256SUMS file alone), but does not by itself defend
# against a full CDN compromise that serves matching tampered archive
# + SHA256SUMS; full tamper resistance would require GPG-verifying
# SHA256SUMS.sig with HashiCorp's public key.
expected_hash="$(awk -v f="${archive}" '$2 == f {print $1}' "$tmpdir/SHA256SUMS")"
if [ -z "$expected_hash" ]; then
  echo "No SHA256 entry for ${archive} in SHA256SUMS; refusing to install" >&2
  exit 1
fi
actual_hash="$(compute_sha256 "$tmpdir/${archive}")"
if [ "$expected_hash" != "$actual_hash" ]; then
  echo "SHA256 mismatch for ${archive}: expected ${expected_hash}, got ${actual_hash}" >&2
  exit 1
fi
echo "SHA256 verified for ${archive}"

unzip -q "$tmpdir/${archive}" -d "$tmpdir"
install -m 0755 "$tmpdir/terraform" "$INSTALL_DIR/terraform"
echo "Installed $("$INSTALL_DIR/terraform" version | head -n1) to ${INSTALL_DIR}/terraform"
