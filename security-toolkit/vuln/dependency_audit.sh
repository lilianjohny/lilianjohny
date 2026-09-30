#!/usr/bin/env bash
# Audit project dependencies for known vulnerabilities using whatever
# ecosystem tooling is available. Read-only. Exit non-zero if issues found.
#
# Usage: bash dependency_audit.sh [project_dir]
set -uo pipefail

DIR="${1:-.}"
cd "$DIR" || { echo "[FAIL] Cannot cd to $DIR"; exit 3; }
echo "[INFO] Auditing dependencies in: $(pwd)"

status=0

run() { echo "[INFO] \$ $*"; "$@"; }

# --- Python ---------------------------------------------------------------
if [[ -f requirements.txt || -f pyproject.toml || -f Pipfile ]]; then
  if command -v pip-audit >/dev/null 2>&1; then
    echo "[INFO] Python: running pip-audit"
    run pip-audit || status=1
  else
    echo "[WARN] Python project detected but 'pip-audit' not installed (pip install pip-audit)."
  fi
fi

# --- Node.js --------------------------------------------------------------
if [[ -f package.json ]]; then
  if command -v npm >/dev/null 2>&1; then
    echo "[INFO] Node: running npm audit"
    run npm audit --omit=dev || status=1
  else
    echo "[WARN] package.json found but npm not installed."
  fi
fi

# --- Go -------------------------------------------------------------------
if [[ -f go.mod ]]; then
  if command -v govulncheck >/dev/null 2>&1; then
    echo "[INFO] Go: running govulncheck"
    run govulncheck ./... || status=1
  else
    echo "[WARN] go.mod found but govulncheck not installed (go install golang.org/x/vuln/cmd/govulncheck@latest)."
  fi
fi

# --- Rust -----------------------------------------------------------------
if [[ -f Cargo.lock ]]; then
  if command -v cargo-audit >/dev/null 2>&1; then
    echo "[INFO] Rust: running cargo audit"
    run cargo audit || status=1
  else
    echo "[WARN] Cargo.lock found but cargo-audit not installed (cargo install cargo-audit)."
  fi
fi

if [[ $status -eq 0 ]]; then
  echo "[OK] No known vulnerabilities reported by available scanners."
else
  echo "[FAIL] One or more scanners reported vulnerabilities. Review output above."
fi
exit $status
