#!/usr/bin/env python3
"""Watch an auth log for brute-force / suspicious authentication patterns.

Parses SSH-style auth log lines and flags source IPs that exceed a failed-
login threshold in a sliding time window. Read-only; useful for detection
and for feeding a blocklist you apply separately.

Usage:
    sudo python log_watch.py /var/log/auth.log
    sudo python log_watch.py /var/log/auth.log --follow --threshold 5
"""
from __future__ import annotations

import argparse
import re
import sys
import time
from collections import defaultdict, deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.common import emit, Level  # noqa: E402

# Matches "Failed password for [invalid user] X from 1.2.3.4 port ..."
FAIL_RE = re.compile(
    r"Failed password for (?:invalid user )?(?P<user>\S+) from (?P<ip>\d{1,3}(?:\.\d{1,3}){3})"
)
ACCEPT_RE = re.compile(
    r"Accepted \S+ for (?P<user>\S+) from (?P<ip>\d{1,3}(?:\.\d{1,3}){3})"
)


class Detector:
    def __init__(self, threshold: int, window: int):
        self.threshold = threshold
        self.window = window
        self.events: dict[str, deque[float]] = defaultdict(deque)
        self.alerted: set[str] = set()

    def record(self, ip: str, now: float) -> None:
        dq = self.events[ip]
        dq.append(now)
        while dq and now - dq[0] > self.window:
            dq.popleft()
        if len(dq) >= self.threshold and ip not in self.alerted:
            self.alerted.add(ip)
            emit(Level.FAIL,
                 f"Brute-force suspected from {ip}: "
                 f"{len(dq)} failures within {self.window}s")


def process_line(line: str, det: Detector, now: float) -> None:
    m = FAIL_RE.search(line)
    if m:
        det.record(m.group("ip"), now)
        return
    a = ACCEPT_RE.search(line)
    if a and a.group("ip") in det.alerted:
        emit(Level.WARN,
             f"Successful login from previously-flagged IP {a.group('ip')} "
             f"(user {a.group('user')}) — investigate.")


def follow(path: Path, det: Detector) -> None:
    with path.open("r", errors="replace") as fh:
        fh.seek(0, 2)  # end of file
        while True:
            line = fh.readline()
            if not line:
                time.sleep(0.5)
                continue
            process_line(line, det, time.time())


def scan(path: Path, det: Detector) -> None:
    with path.open("r", errors="replace") as fh:
        for line in fh:
            # In batch mode we treat all lines as "now" for windowing.
            process_line(line, det, time.time())


def main() -> int:
    ap = argparse.ArgumentParser(description="Auth-log brute-force watcher")
    ap.add_argument("logfile", type=Path)
    ap.add_argument("--threshold", type=int, default=8,
                    help="Failed logins per window to alert on")
    ap.add_argument("--window", type=int, default=60, help="Window in seconds")
    ap.add_argument("--follow", action="store_true", help="Tail the file live")
    args = ap.parse_args()

    if not args.logfile.exists():
        emit(Level.FAIL, f"Log file not found: {args.logfile}")
        return 3

    det = Detector(args.threshold, args.window)
    emit(Level.INFO,
         f"Watching {args.logfile} (threshold {args.threshold}/{args.window}s)")
    try:
        if args.follow:
            follow(args.logfile, det)
        else:
            scan(args.logfile, det)
    except PermissionError:
        emit(Level.FAIL, "Permission denied — try running with sudo.")
        return 3
    except KeyboardInterrupt:
        emit(Level.INFO, "Stopped.")

    if not args.follow:
        emit(Level.INFO, f"Flagged {len(det.alerted)} source IP(s).")
    return 2 if det.alerted else 0


if __name__ == "__main__":
    raise SystemExit(main())
