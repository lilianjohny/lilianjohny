#!/usr/bin/env bash
# Incident-response triage collector for a Linux host you administer.
# Gathers volatile & system state into a timestamped directory for analysis.
# Read-only with respect to the system; only writes into the output dir.
#
# Run as root for complete results:  sudo bash triage_collect.sh
set -uo pipefail

OUT="${1:-ir_triage_$(hostname)_$(date -u +%Y%m%dT%H%M%SZ)}"
mkdir -p "$OUT" || { echo "[FAIL] cannot create $OUT"; exit 3; }
echo "[INFO] Collecting triage data into: $OUT"

cap() { # <filename> <command...>
  local f="$OUT/$1"; shift
  echo "[INFO] $*"
  { echo "# \$ $*"; "$@"; } >"$f" 2>&1 || echo "[WARN] '$*' returned non-zero (see $f)"
}

# --- Host & time ----------------------------------------------------------
cap host.txt uname -a
cap uptime.txt uptime
cap date.txt date -u +%FT%TZ

# --- Users & auth ---------------------------------------------------------
cap who.txt who -a
cap last.txt last -n 50
cap lastb.txt lastb -n 50          # failed logins (root)
cap passwd.txt cat /etc/passwd
cap sudoers.txt cat /etc/sudoers

# --- Processes ------------------------------------------------------------
cap ps.txt ps auxww
cap pstree.txt bash -c "command -v pstree >/dev/null && pstree -ap || echo 'pstree not installed'"

# --- Network --------------------------------------------------------------
cap netstat.txt bash -c "ss -tulpane 2>/dev/null || netstat -tulpane"
cap connections.txt bash -c "ss -tanp 2>/dev/null || netstat -tanp"
cap routes.txt ip route
cap arp.txt bash -c "ip neigh || arp -a"
cap dns.txt cat /etc/resolv.conf

# --- Persistence surfaces -------------------------------------------------
cap crontab_root.txt bash -c "crontab -l 2>/dev/null || echo 'no root crontab'"
cap cron_dirs.txt bash -c "ls -laR /etc/cron* 2>/dev/null"
cap systemd_units.txt bash -c "systemctl list-unit-files --type=service 2>/dev/null | head -n 200"
cap startup_timers.txt bash -c "systemctl list-timers --all 2>/dev/null"

# --- Recently modified files (last 2 days in common dirs) -----------------
cap recent_files.txt bash -c "find /etc /root /home /tmp /var/tmp -xdev -mtime -2 -type f 2>/dev/null | head -n 500"

# --- Logs (copies) --------------------------------------------------------
mkdir -p "$OUT/logs"
for lg in /var/log/auth.log /var/log/secure /var/log/syslog /var/log/messages; do
  [[ -r "$lg" ]] && cp -p "$lg" "$OUT/logs/" 2>/dev/null && echo "[INFO] copied $lg"
done

# --- Hashes of collected files (chain of custody) -------------------------
( cd "$OUT" && find . -type f ! -name manifest.sha256 -exec sha256sum {} \; > manifest.sha256 )
echo "[OK] Triage complete. Review $OUT/ and manifest.sha256"
echo "[INFO] Tip: collect from a live-response context and preserve timestamps."
