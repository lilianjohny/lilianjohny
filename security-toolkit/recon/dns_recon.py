#!/usr/bin/env python3
"""Passive DNS reconnaissance for a domain you own or are assessing.

Resolves common record types and probes a small wordlist of subdomains via
standard DNS (no zone transfers, no brute-force floods). Read-only.

Usage:
    python dns_recon.py example.com
    python dns_recon.py example.com --wordlist hosts.txt
"""
from __future__ import annotations

import argparse
import socket
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.common import Report, emit, Level  # noqa: E402

DEFAULT_SUBS = ["www", "mail", "smtp", "webmail", "ns1", "ns2", "api", "dev",
                "staging", "test", "vpn", "portal", "admin", "app", "cdn",
                "blog", "shop", "git", "ci", "docs"]


def resolve(name: str) -> list[str]:
    try:
        infos = socket.getaddrinfo(name, None)
        return sorted({info[4][0] for info in infos})
    except socket.gaierror:
        return []


def main() -> int:
    ap = argparse.ArgumentParser(description="Passive DNS recon")
    ap.add_argument("domain")
    ap.add_argument("--wordlist", type=Path, default=None,
                    help="File with one subdomain label per line")
    args = ap.parse_args()

    rep = Report()
    apex_ips = resolve(args.domain)
    if apex_ips:
        rep.info(f"{args.domain} -> {', '.join(apex_ips)}")
    else:
        rep.warn(f"{args.domain} did not resolve.")

    labels = DEFAULT_SUBS
    if args.wordlist and args.wordlist.exists():
        labels = [l.strip() for l in args.wordlist.read_text().splitlines() if l.strip()]

    emit(Level.INFO, f"Probing {len(labels)} subdomain labels…")
    found = 0
    for label in labels:
        fqdn = f"{label}.{args.domain}"
        ips = resolve(fqdn)
        if ips:
            found += 1
            rep.ok(f"{fqdn} -> {', '.join(ips)}")

    if not found:
        rep.info("No subdomains from the list resolved.")
    rep.summary()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
