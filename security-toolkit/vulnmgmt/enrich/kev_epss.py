#!/usr/bin/env python3
"""Load CISA KEV and FIRST EPSS threat-intel for enrichment.

KEV  = CISA Known Exploited Vulnerabilities catalog (CVEs actively exploited).
EPSS = FIRST Exploit Prediction Scoring System (probability of exploitation).

Fetches the public feeds if --allow-fetch is set and the network permits;
otherwise (and by default) loads from local files you supply. Designed to
degrade gracefully in restricted networks.

Local file formats:
  --kev-file   CISA KEV JSON, or a plain text/CSV with one CVE id per line.
  --epss-file  EPSS CSV with header rows; columns: cve,epss,percentile.

Importable: load_intel(kev_file, epss_file, allow_fetch) -> (kev_set, epss_dict)
CLI: prints how many KEV/EPSS entries were loaded and looks up a CVE.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from pathlib import Path

KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
EPSS_URL = "https://epss.empiricalsecurity.com/epss_scores-current.csv.gz"


def _fetch(url: str, timeout: float = 30):
    import urllib.request
    with urllib.request.urlopen(url, timeout=timeout) as r:  # noqa: S310
        return r.read()


def load_kev(path: str | None, allow_fetch: bool) -> set[str]:
    raw = None
    if path and Path(path).exists():
        raw = Path(path).read_bytes()
    elif allow_fetch:
        try:
            raw = _fetch(KEV_URL)
        except Exception as exc:  # noqa: BLE001
            print(f"[WARN] KEV fetch failed: {exc}", file=sys.stderr)
    if not raw:
        return set()
    text = raw.decode("utf-8", "replace").strip()
    if text.startswith("{"):
        try:
            data = json.loads(text)
            return {v["cveID"].upper() for v in data.get("vulnerabilities", []) if v.get("cveID")}
        except (json.JSONDecodeError, KeyError):
            pass
    # plain list / csv: take any CVE-looking token per line
    out = set()
    for line in text.splitlines():
        tok = line.strip().split(",")[0].strip().upper()
        if tok.startswith("CVE-"):
            out.add(tok)
    return out


def load_epss(path: str | None, allow_fetch: bool) -> dict[str, float]:
    raw = None
    if path and Path(path).exists():
        raw = Path(path).read_bytes()
    elif allow_fetch:
        try:
            raw = _fetch(EPSS_URL)
        except Exception as exc:  # noqa: BLE001
            print(f"[WARN] EPSS fetch failed: {exc}", file=sys.stderr)
    if not raw:
        return {}
    # gzip?
    if raw[:2] == b"\x1f\x8b":
        import gzip
        raw = gzip.decompress(raw)
    text = raw.decode("utf-8", "replace")
    out: dict[str, float] = {}
    for row in csv.reader(io.StringIO(text)):
        if not row or row[0].startswith("#"):
            continue
        cve = row[0].strip().upper()
        if not cve.startswith("CVE-"):
            continue  # skips header
        try:
            out[cve] = float(row[1])
        except (ValueError, IndexError):
            continue
    return out


def load_intel(kev_file=None, epss_file=None, allow_fetch=False):
    return load_kev(kev_file, allow_fetch), load_epss(epss_file, allow_fetch)


def main() -> int:
    ap = argparse.ArgumentParser(description="Load KEV + EPSS intel")
    ap.add_argument("--kev-file")
    ap.add_argument("--epss-file")
    ap.add_argument("--allow-fetch", action="store_true")
    ap.add_argument("--lookup", help="CVE id to look up")
    args = ap.parse_args()
    kev, epss = load_intel(args.kev_file, args.epss_file, args.allow_fetch)
    print(f"[INFO] KEV entries: {len(kev)}  EPSS entries: {len(epss)}", file=sys.stderr)
    if args.lookup:
        c = args.lookup.upper()
        print(f"{c}: KEV={c in kev} EPSS={epss.get(c)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
