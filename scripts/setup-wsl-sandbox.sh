#!/usr/bin/env bash
# Prepare a WSL2 Ubuntu host to run TrueForge with a working local sandbox.
#
# Run as root inside WSL:  wsl -d Ubuntu -u root -- bash scripts/setup-wsl-sandbox.sh
# (or `sudo bash scripts/setup-wsl-sandbox.sh` from inside the WSL shell)
#
# TrueForge's local sandbox provider (bubblewrap-jailed, no external
# service) is Linux/macOS only, so on Windows the harness has to run inside
# WSL2 to use it -- see difficulties.md for how this was diagnosed. Three
# things have to be true before the sandbox can run a single line of
# agent-written code:
#
#   1. bwrap, socat, rg on PATH -- the sandbox runtime shells out to them.
#   2. python3-venv installed -- Ubuntu ships python3 without ensurepip, so
#      the sandbox fails at "virtual environment was not created
#      successfully" before it ever reaches any actual code.
#   3. pip has to install pydantic into that venv WITHOUT reaching the
#      network. TrueForge's own internal Code Mode shim needs pydantic on
#      every first sandbox use, and the sandbox routes all egress through a
#      filtering proxy (a Unix-domain-socket bridge into host-side HTTP/
#      SOCKS5 proxies -- see @anthropic-ai/sandbox-runtime's README) that
#      does not work under WSL2. Every pip install attempt dies with
#      ProxyError. Fix: stage the one pinned wheel in a path the sandbox's
#      filesystem policy is already allowed to read, and point pip at it
#      with --no-index so the install resolves locally and never touches
#      the proxy.
#
# Step 3 has to be a host-wide pip config: the sandboxed pip does not
# inherit environment variables, so PIP_CONFIG_FILE/PIP_NO_INDEX have no
# effect on it. The script backs up whatever pip.conf existed and
# `--revert` restores it.
#
#     wsl -d Ubuntu -u root -- bash scripts/setup-wsl-sandbox.sh --revert
#
# Also needs networkingMode=mirrored in %USERPROFILE%\.wslconfig (+
# `wsl --shutdown` to apply) so WSL2 can reach the wallet server on the
# Windows host's 127.0.0.1 -- it's bound to localhost only, deliberately
# (see mcp-server/app/config.py), so the default WSL2 NAT mode can't reach
# it without either mirrored networking or reopening the bind, which we
# don't want to do.
set -euo pipefail

WHEELS=/usr/local/share/tf-wheels
PYDANTIC_PIN="pydantic>=2.0.0,<3.0.0"
PIP_CONF=/etc/pip.conf
BACKUP="$PIP_CONF.before-treasuryforge"

if [[ "${1:-}" == "--revert" ]]; then
  if [[ -f "$BACKUP" ]]; then
    mv "$BACKUP" "$PIP_CONF"
    echo "Restored the previous $PIP_CONF."
  else
    rm -f "$PIP_CONF"
    echo "Removed $PIP_CONF; there was no earlier config to restore."
  fi
  rm -rf "$WHEELS"
  echo "Removed $WHEELS. Host pip can reach the package index again."
  exit 0
fi

echo "==> Installing sandbox host dependencies"
apt-get update -qq
apt-get install -y -qq bubblewrap socat ripgrep python3-venv python3-pip

echo "==> Staging $PYDANTIC_PIN wheels in $WHEELS"
mkdir -p "$WHEELS"
pip3 download "$PYDANTIC_PIN" -d "$WHEELS" -q

echo "==> Pointing pip at the local wheels (bypasses the sandbox egress proxy)"
if [[ -f "$PIP_CONF" && ! -f "$BACKUP" ]]; then
  cp "$PIP_CONF" "$BACKUP"
  echo "    Saved your existing $PIP_CONF to $BACKUP"
fi
cat > "$PIP_CONF" <<EOF
[global]
no-index = true
find-links = $WHEELS
disable-pip-version-check = true
EOF

echo "==> Verifying a sandbox-style venv can be built offline"
rm -rf /tmp/tf-venv-check
python3 -m venv /tmp/tf-venv-check
/tmp/tf-venv-check/bin/pip install --quiet "$PYDANTIC_PIN"
/tmp/tf-venv-check/bin/python -c "import pydantic; print('pydantic', pydantic.VERSION, 'installed offline OK')"
rm -rf /tmp/tf-venv-check

cat <<'EOF'

Done.

NOTE: pip on this host now installs only from the staged wheel directory,
so other Python work in this WSL instance won't reach the package index
until you run this script with --revert.

Install Node (native, not the Windows one leaking in via PATH interop) and
TrueForge itself separately, e.g.:

    curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
    apt-get install -y nodejs
    npm install @truefoundry/trueforge@0.1.4

Then run scripts/setup_trueforge.py with TRUEFORGE_URL pointed at whatever
port you start it on inside WSL.
EOF
