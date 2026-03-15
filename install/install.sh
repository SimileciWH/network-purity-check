#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

INSTALL_PREFIX="${NPC_INSTALL_PREFIX:-$HOME/.local/share/network-purity-check}"
BIN_DIR="${NPC_BIN_DIR:-$HOME/.local/bin}"
SHELL_RC_OVERRIDE="${NPC_SHELL_RC:-}"

log() {
  echo "[install] $*"
}

warn() {
  echo "[install][warn] $*" >&2
}

err() {
  echo "[install][error] $*" >&2
}

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

version_ge_311() {
  local py="$1"
  "$py" - <<'PY' >/dev/null
import sys
raise SystemExit(0 if sys.version_info >= (3, 11) else 1)
PY
}

install_python_311() {
  local os_name
  os_name="$(uname -s)"

  if [[ "$os_name" == "Darwin" ]]; then
    if ! command_exists brew; then
      err "Homebrew is required to auto-install Python 3.11 on macOS."
      err "Please install Homebrew first: https://brew.sh"
      return 1
    fi
    log "Installing python@3.11 via Homebrew..."
    brew install python@3.11
    return 0
  fi

  if command_exists apt-get; then
    log "Installing python3.11 via apt-get..."
    if command_exists sudo; then
      sudo apt-get update
      sudo apt-get install -y python3.11
    else
      apt-get update
      apt-get install -y python3.11
    fi
    return 0
  fi

  if command_exists dnf; then
    log "Installing python3.11 via dnf..."
    if command_exists sudo; then
      sudo dnf install -y python3.11
    else
      dnf install -y python3.11
    fi
    return 0
  fi

  err "Unsupported package manager. Please install Python 3.11 manually."
  return 1
}

choose_python() {
  if command_exists python3.11 && version_ge_311 python3.11; then
    echo "python3.11"
    return 0
  fi

  if command_exists python3 && version_ge_311 python3; then
    echo "python3"
    return 0
  fi

  log "Python 3.11+ not found. Attempting installation..."
  install_python_311

  if command_exists python3.11 && version_ge_311 python3.11; then
    echo "python3.11"
    return 0
  fi

  if command_exists python3 && version_ge_311 python3; then
    echo "python3"
    return 0
  fi

  err "Python 3.11+ is still unavailable after installation attempt."
  return 1
}

pick_shell_rc() {
  if [[ -n "$SHELL_RC_OVERRIDE" ]]; then
    echo "$SHELL_RC_OVERRIDE"
    return 0
  fi

  local shell_name
  shell_name="$(basename "${SHELL:-}")"

  case "$shell_name" in
    zsh) echo "$HOME/.zshrc" ;;
    bash) echo "$HOME/.bashrc" ;;
    *)
      if [[ -f "$HOME/.zshrc" ]]; then
        echo "$HOME/.zshrc"
      else
        echo "$HOME/.bashrc"
      fi
      ;;
  esac
}

ensure_path() {
  local target_bin="$1"
  local shell_rc
  shell_rc="$(pick_shell_rc)"
  local marker="# network-purity-check PATH"
  local line="export PATH=\"${target_bin}:\$PATH\""

  if [[ ":$PATH:" == *":${target_bin}:"* ]]; then
    log "PATH already contains ${target_bin}"
    return 0
  fi

  mkdir -p "$(dirname "$shell_rc")"
  touch "$shell_rc"

  if grep -Fq "$marker" "$shell_rc"; then
    log "PATH marker already exists in ${shell_rc}"
    return 0
  fi

  {
    echo ""
    echo "$marker"
    echo "$line"
  } >>"$shell_rc"

  log "Updated ${shell_rc} to include ${target_bin}"
  warn "Run 'source ${shell_rc}' or open a new terminal to apply PATH changes."
}

main() {
  log "Checking Python dependency..."
  local python_bin
  python_bin="$(choose_python)"
  log "Using Python interpreter: $python_bin"

  local commit
  commit="$(git -C "$PROJECT_ROOT" rev-parse --short HEAD 2>/dev/null || echo "manual")"
  local install_dir="${INSTALL_PREFIX}/${commit}"
  local current_link="${INSTALL_PREFIX}/current"

  log "Preparing install directory: ${install_dir}"
  mkdir -p "$install_dir"
  rm -rf "${install_dir:?}"/*

  cp -R "$PROJECT_ROOT/network_purity_check" "$install_dir/"
  cp "$PROJECT_ROOT/pyproject.toml" "$install_dir/"
  cp "$PROJECT_ROOT/LICENSE" "$install_dir/"
  cp "$PROJECT_ROOT/README.md" "$install_dir/"

  ln -sfn "$install_dir" "$current_link"

  mkdir -p "$BIN_DIR"
  cat >"$BIN_DIR/network-purity-check" <<SCRIPT
#!/usr/bin/env bash
set -euo pipefail
PYTHON_BIN="${python_bin}"
PROJECT_DIR="${current_link}"
export PYTHONPATH="\${PROJECT_DIR}:\${PYTHONPATH:-}"
exec "\${PYTHON_BIN}" -m network_purity_check.cli "\$@"
SCRIPT
  chmod +x "$BIN_DIR/network-purity-check"

  ensure_path "$BIN_DIR"

  log "Running post-install checks (--help / -h)..."
  "$BIN_DIR/network-purity-check" --help >/dev/null
  "$BIN_DIR/network-purity-check" -h >/dev/null

  log "Installation completed."
  log "Command: $BIN_DIR/network-purity-check"
}

main "$@"
