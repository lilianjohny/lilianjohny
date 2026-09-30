#!/usr/bin/env python3
"""Check a host's TLS certificate: validity window, expiry, and basics.

Read-only. Connects to <host>:<port> and inspects the presented certificate.

Usage:
    python tls_cert_check.py example.com
    python tls_cert_check.py example.com --port 8443 --warn-days 30
"""
from __future__ import annotations

import argparse
import datetime as dt
import socket
import ssl
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.common import Report  # noqa: E402


def get_cert(host: str, port: int, timeout: float) -> dict:
    ctx = ssl.create_default_context()
    with socket.create_connection((host, port), timeout=timeout) as sock:
        with ctx.wrap_socket(sock, server_hostname=host) as ssock:
            return ssock.getpeercert()


def parse_date(value: str) -> dt.datetime:
    return dt.datetime.strptime(value, "%b %d %H:%M:%S %Y %Z").replace(
        tzinfo=dt.timezone.utc
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="TLS certificate checker")
    ap.add_argument("host")
    ap.add_argument("--port", type=int, default=443)
    ap.add_argument("--warn-days", type=int, default=21,
                    help="Warn if cert expires within this many days")
    ap.add_argument("--timeout", type=float, default=10.0)
    args = ap.parse_args()

    rep = Report()
    try:
        cert = get_cert(args.host, args.port, args.timeout)
    except (ssl.SSLError, socket.error, OSError) as exc:
        rep.fail(f"Could not retrieve certificate: {exc}")
        return rep.exit_code

    if not cert:
        rep.fail("No certificate returned (verification may have failed).")
        return rep.exit_code

    subject = dict(x[0] for x in cert.get("subject", []))
    issuer = dict(x[0] for x in cert.get("issuer", []))
    rep.info(f"Subject CN : {subject.get('commonName', '?')}")
    rep.info(f"Issuer     : {issuer.get('organizationName', issuer.get('commonName', '?'))}")

    now = dt.datetime.now(dt.timezone.utc)
    not_after = parse_date(cert["notAfter"])
    not_before = parse_date(cert["notBefore"])
    days_left = (not_after - now).days

    if now < not_before:
        rep.fail(f"Certificate not yet valid (starts {not_before:%Y-%m-%d}).")
    elif days_left < 0:
        rep.fail(f"Certificate EXPIRED {abs(days_left)} days ago ({not_after:%Y-%m-%d}).")
    elif days_left <= args.warn_days:
        rep.warn(f"Certificate expires in {days_left} days ({not_after:%Y-%m-%d}).")
    else:
        rep.ok(f"Certificate valid, {days_left} days remaining ({not_after:%Y-%m-%d}).")

    sans = [v for k, v in cert.get("subjectAltName", []) if k == "DNS"]
    if sans:
        rep.info(f"SANs       : {', '.join(sans[:10])}" + (" …" if len(sans) > 10 else ""))

    rep.summary()
    return rep.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
