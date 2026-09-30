#!/usr/bin/env python3
"""Lightweight TCP connect scanner for hosts you are authorized to test.

Uses plain TCP connects (no raw sockets, no root needed). Intended for
verifying your own exposed services / firewall rules, not stealth scanning.
For richer scans, use nmap directly.

Usage:
    python port_scan.py 192.168.1.10
    python port_scan.py host.internal --ports 22,80,443,8080-8090 --workers 200
"""
from __future__ import annotations

import argparse
import socket
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.common import Report, confirm_authorized, emit, Level  # noqa: E402

COMMON_PORTS = [21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 587, 993, 995,
                3306, 3389, 5432, 5900, 6379, 8080, 8443, 9200, 27017]

# Best-effort service labels for common ports.
SERVICES = {
    21: "ftp", 22: "ssh", 23: "telnet", 25: "smtp", 53: "dns", 80: "http",
    110: "pop3", 143: "imap", 443: "https", 445: "smb", 587: "submission",
    993: "imaps", 995: "pop3s", 3306: "mysql", 3389: "rdp", 5432: "postgres",
    5900: "vnc", 6379: "redis", 8080: "http-alt", 8443: "https-alt",
    9200: "elasticsearch", 27017: "mongodb",
}


def parse_ports(spec: str) -> list[int]:
    ports: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            lo, hi = part.split("-", 1)
            ports.update(range(int(lo), int(hi) + 1))
        elif part:
            ports.add(int(part))
    return sorted(p for p in ports if 0 < p <= 65535)


def probe(host: str, port: int, timeout: float) -> tuple[int, bool]:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return port, True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return port, False


def main() -> int:
    ap = argparse.ArgumentParser(description="Authorized TCP connect scanner")
    ap.add_argument("host")
    ap.add_argument("--ports", default=None,
                    help="e.g. 22,80,443,8000-8100 (default: common ports)")
    ap.add_argument("--timeout", type=float, default=1.0)
    ap.add_argument("--workers", type=int, default=100)
    args = ap.parse_args()

    confirm_authorized(args.host)
    ports = parse_ports(args.ports) if args.ports else COMMON_PORTS

    try:
        ip = socket.gethostbyname(args.host)
    except socket.gaierror as exc:
        emit(Level.FAIL, f"Cannot resolve {args.host}: {exc}")
        return 3

    emit(Level.INFO, f"Scanning {args.host} ({ip}) — {len(ports)} ports")
    rep = Report()
    open_ports: list[int] = []

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(probe, args.host, p, args.timeout) for p in ports]
        for fut in as_completed(futures):
            port, is_open = fut.result()
            if is_open:
                open_ports.append(port)

    for port in sorted(open_ports):
        rep.warn(f"OPEN {port}/tcp ({SERVICES.get(port, 'unknown')})")
    if not open_ports:
        rep.ok("No open ports found in the scanned range.")

    rep.summary()
    return rep.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
