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

if command -v terraform >/dev/null 2>&1; then
  current="$(terraform version -json 2>/dev/null \
    | python3 -c "import json, sys; print(json.load(sys.stdin)['terraform_version'])" 2>/dev/null \
    || true)"
  if [ "$current" = "$TERRAFORM_VERSION" ]; then
    echo "Terraform ${TERRAFORM_VERSION} already installed at $(command -v terraform)"
    exit 0
  fi
fi

case "$(uname -m)" in
  x86_64) tf_arch="amd64" ;;
  aarch64|arm64) tf_arch="arm64" ;;
  *) echo "Unsupported architecture: $(uname -m)" >&2; exit 1 ;;
esac

tf_os="$(uname -s | tr '[:upper:]' '[:lower:]')"
url="https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_${tf_os}_${tf_arch}.zip"

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

echo "Downloading Terraform ${TERRAFORM_VERSION} (${tf_os}/${tf_arch}) from ${url}"
curl -fsSL --retry 3 --retry-delay 2 "$url" -o "$tmpdir/terraform.zip"
unzip -q "$tmpdir/terraform.zip" -d "$tmpdir"
install -m 0755 "$tmpdir/terraform" "$INSTALL_DIR/terraform"
echo "Installed $(terraform version | head -n1) to $INSTALL_DIR/terraform"
