#!/usr/bin/env bash
# Audit local OpenSSH server configuration against common hardening guidance.
# Read-only: parses sshd effective config, changes nothing.
#
# Usage: bash ssh_audit.sh [/path/to/sshd_config]
set -uo pipefail

CONF="${1:-/etc/ssh/sshd_config}"
warn=0; fail=0
ok()   { echo "[OK]   $*"; }
warnf(){ echo "[WARN] $*"; warn=$((warn+1)); }
failf(){ echo "[FAIL] $*"; fail=$((fail+1)); }

# Prefer the effective config from sshd -T (resolves includes/defaults).
if command -v sshd >/dev/null 2>&1 && sshd -T >/dev/null 2>&1; then
  echo "[INFO] Using effective config from 'sshd -T'"
  CFG="$(sshd -T 2>/dev/null)"
  get() { echo "$CFG" | awk -v k="$1" 'tolower($1)==tolower(k){print $2; exit}'; }
elif [[ -r "$CONF" ]]; then
  echo "[INFO] Reading $CONF (may not reflect Include/defaults)"
  get() { grep -iE "^[[:space:]]*$1[[:space:]]" "$CONF" | tail -n1 | awk '{print $2}'; }
else
  echo "[FAIL] Cannot read sshd config and 'sshd -T' unavailable (try sudo)."
  exit 3
fi

check() { # key expected_regex message_if_bad
  local val; val="$(get "$1")"
  if [[ -z "$val" ]]; then warnf "$1 not set explicitly — $3"; return; fi
  if [[ "$val" =~ $2 ]]; then ok "$1 = $val"; else failf "$1 = $val — $3"; fi
}

check permitrootlogin '^(no|prohibit-password)$' "should be 'no' or 'prohibit-password'"
check passwordauthentication '^no$' "prefer key-based auth (set 'no')"
check permitemptypasswords '^no$' "must be 'no'"
check x11forwarding '^no$' "disable unless required"
check maxauthtries '^([1-4])$' "lower (<=4) to slow brute force"
check protocol '^2$' "must be 2 (1 is insecure/obsolete)"

lg="$(get loglevel)"
[[ "$lg" =~ ^(VERBOSE|INFO)$ ]] && ok "loglevel = $lg" || warnf "loglevel = ${lg:-unset} — prefer VERBOSE for key fingerprints"

echo "[INFO] Summary: $warn warning(s), $fail failure(s)."
[[ $fail -gt 0 ]] && exit 2
[[ $warn -gt 0 ]] && exit 1
exit 0
