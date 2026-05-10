#!/bin/bash
# SessionStart hook: install the Terraform binary used by CI so that
# pre-commit hooks (terraform_fmt, terraform_validate, terraform_tflint) and
# manual `terraform fmt -check -recursive` invocations work in Claude Code on
# the web sessions. Web-only by design; developer workstations manage their
# own toolchain.
#
# Keep TERRAFORM_VERSION in sync with the `terraform_version:` pin used in
# .github/workflows/python-ci.yml, .github/workflows/auto-fix-precommit.yml,
# and .github/workflows/terraform-ci.yml.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

TERRAFORM_VERSION="1.14.4"
INSTALL_DIR="/usr/local/bin"

# Ensure the binary we install below resolves first for the rest of the
# session, even if a different `terraform` exists earlier on the base
# image's PATH. CLAUDE_ENV_FILE persists exports across hook invocations
# and subsequent shells; guard against duplicate entries on re-runs.
if [ -n "${CLAUDE_ENV_FILE:-}" ] \
  && ! grep -Fq "export PATH=\"${INSTALL_DIR}:" "$CLAUDE_ENV_FILE" 2>/dev/null; then
  echo "export PATH=\"${INSTALL_DIR}:\$PATH\"" >> "$CLAUDE_ENV_FILE"
fi

# Idempotency: check the install location specifically so a stale or
# differently-versioned terraform earlier on PATH cannot mask us.
if [ -x "$INSTALL_DIR/terraform" ]; then
  current="$("$INSTALL_DIR/terraform" version -json 2>/dev/null \
    | python3 -c "import json, sys; print(json.load(sys.stdin)['terraform_version'])" 2>/dev/null \
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
archive="terraform_${TERRAFORM_VERSION}_${tf_os}_${tf_arch}.zip"
base="https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}"

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

echo "Downloading ${archive} from ${base}"
curl -fsSL --retry 3 --retry-delay 2 "${base}/${archive}" -o "$tmpdir/${archive}"
curl -fsSL --retry 3 --retry-delay 2 \
  "${base}/terraform_${TERRAFORM_VERSION}_SHA256SUMS" -o "$tmpdir/SHA256SUMS"

# Verify the downloaded archive against the official SHA256SUMS file before
# placing the binary on PATH, to catch corrupted downloads and reduce
# supply-chain risk from a tampered CDN/proxy path.
expected_hash="$(awk -v f="${archive}" '$2 == f {print $1}' "$tmpdir/SHA256SUMS")"
if [ -z "$expected_hash" ]; then
  echo "No SHA256 entry for ${archive} in SHA256SUMS; refusing to install" >&2
  exit 1
fi
actual_hash="$(sha256sum "$tmpdir/${archive}" | awk '{print $1}')"
if [ "$expected_hash" != "$actual_hash" ]; then
  echo "SHA256 mismatch for ${archive}: expected ${expected_hash}, got ${actual_hash}" >&2
  exit 1
fi
echo "SHA256 verified for ${archive}"

unzip -q "$tmpdir/${archive}" -d "$tmpdir"
install -m 0755 "$tmpdir/terraform" "$INSTALL_DIR/terraform"
echo "Installed $("$INSTALL_DIR/terraform" version | head -n1) to ${INSTALL_DIR}/terraform"
