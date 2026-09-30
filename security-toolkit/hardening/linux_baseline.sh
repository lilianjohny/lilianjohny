#!/usr/bin/env bash
# Quick Linux hardening baseline check (CIS-inspired, non-exhaustive).
# Read-only. Run as root for complete results: sudo bash linux_baseline.sh
set -uo pipefail

warn=0; fail=0
ok()   { echo "[OK]   $*"; }
warnf(){ echo "[WARN] $*"; warn=$((warn+1)); }
failf(){ echo "[FAIL] $*"; fail=$((fail+1)); }

echo "[INFO] Linux baseline check on $(hostname) — $(date -u +%FT%TZ)"

# 1. Accounts with UID 0 other than root
extra_root="$(awk -F: '($3==0 && $1!="root"){print $1}' /etc/passwd)"
[[ -z "$extra_root" ]] && ok "Only root has UID 0" || failf "Extra UID-0 accounts: $extra_root"

# 2. World-writable files in sensitive dirs (sample)
ww="$(find /etc /usr/bin /usr/sbin -xdev -type f -perm -0002 2>/dev/null | head -n5)"
[[ -z "$ww" ]] && ok "No world-writable files in /etc,/usr/bin,/usr/sbin (sampled)" \
  || warnf "World-writable files found (first 5): $ww"

# 3. Empty-password accounts
empty="$(awk -F: '($2==""){print $1}' /etc/shadow 2>/dev/null)"
if [[ -n "${empty:-}" ]]; then failf "Accounts with empty password: $empty"
elif [[ ! -r /etc/shadow ]]; then warnf "/etc/shadow unreadable — run as root for password checks"
else ok "No empty-password accounts"; fi

# 4. SSH root login (delegates detail to ssh_audit.sh)
if command -v sshd >/dev/null 2>&1; then
  prl="$(sshd -T 2>/dev/null | awk '/^permitrootlogin/{print $2}')"
  [[ "$prl" == "no" || "$prl" == "prohibit-password" ]] && ok "SSH PermitRootLogin=$prl" \
    || warnf "SSH PermitRootLogin=${prl:-unknown} (run hardening/ssh_audit.sh)"
fi

# 5. Firewall present & active
if command -v ufw >/dev/null 2>&1 && ufw status 2>/dev/null | grep -qi active; then
  ok "ufw firewall active"
elif command -v firewall-cmd >/dev/null 2>&1 && firewall-cmd --state 2>/dev/null | grep -qi running; then
  ok "firewalld active"
elif command -v nft >/dev/null 2>&1 && [[ -n "$(nft list ruleset 2>/dev/null)" ]]; then
  ok "nftables ruleset present"
else
  warnf "No active host firewall detected (ufw/firewalld/nftables)"
fi

# 6. Automatic updates hint
if [[ -f /etc/apt/apt.conf.d/20auto-upgrades ]] || systemctl is-enabled --quiet dnf-automatic.timer 2>/dev/null; then
  ok "Unattended/automatic updates appear configured"
else
  warnf "No unattended-upgrades / dnf-automatic detected"
fi

# 7. Core dumps restricted
if sysctl -n fs.suid_dumpable 2>/dev/null | grep -q '^0$'; then
  ok "fs.suid_dumpable = 0"
else
  warnf "fs.suid_dumpable != 0 — SUID core dumps allowed"
fi

echo "[INFO] Summary: $warn warning(s), $fail failure(s)."
[[ $fail -gt 0 ]] && exit 2
[[ $warn -gt 0 ]] && exit 1
exit 0
