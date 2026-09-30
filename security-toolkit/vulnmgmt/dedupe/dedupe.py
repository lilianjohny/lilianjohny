#!/usr/bin/env python3
"""Deduplicate normalized findings across scanners and runs.

The same vulnerability is often reported by multiple scanners (e.g., Trivy and
Grype both flag CVE-X on package Y). This collapses duplicates by
(vuln_id, asset, component), keeping the highest-severity/CVSS record and
recording which sources reported it.

Usage:
  python dedupe.py findings.jsonl > deduped.jsonl
  cat a.jsonl b.jsonl | python dedupe.py - > deduped.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SEV_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}


def key(f: dict) -> tuple:
    comp = (f.get("component") or "").split(":")[0]
    return (str(f.get("vuln_id", "")).upper(), f.get("asset", ""), comp)


def better(a: dict, b: dict) -> dict:
    """Keep the record with higher severity, then higher CVSS."""
    ra, rb = SEV_RANK.get(a.get("severity"), 0), SEV_RANK.get(b.get("severity"), 0)
    if rb > ra:
        a, b = b, a
    elif rb == ra and (b.get("cvss") or 0) > (a.get("cvss") or 0):
        a, b = b, a
    # merge source provenance
    srcs = set(str(a.get("sources", a.get("source", ""))).split(",")) | {b.get("source", "")}
    a["sources"] = ",".join(sorted(s for s in srcs if s))
    return a


def main() -> int:
    ap = argparse.ArgumentParser(description="Deduplicate findings")
    ap.add_argument("findings", help="JSONL file or - for stdin")
    args = ap.parse_args()

    src = sys.stdin if args.findings == "-" else open(args.findings)
    merged: dict[tuple, dict] = {}
    n_in = 0
    with src:
        for line in src:
            line = line.strip()
            if not line:
                continue
            f = json.loads(line)
            n_in += 1
            k = key(f)
            merged[k] = better(dict(merged[k]), f) if k in merged else f

    for f in merged.values():
        f.setdefault("sources", f.get("source", ""))
        print(json.dumps(f))
    print(f"[INFO] {n_in} in -> {len(merged)} unique ({n_in - len(merged)} duplicates merged)",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
