#!/usr/bin/env python3
"""Application security-headers check (AppSec entry point).

Thin delegator to the toolkit's vuln/header_check.py so AppSec workflows have a
local command without duplicating logic.

Usage:
    python security_headers.py https://app.example.com
"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

TARGET = Path(__file__).resolve().parents[2] / "vuln" / "header_check.py"

if __name__ == "__main__":
    if not TARGET.exists():
        print(f"[FAIL] Expected {TARGET} not found.", file=sys.stderr)
        raise SystemExit(3)
    # Re-exec header_check.py with the same argv.
    sys.argv[0] = str(TARGET)
    runpy.run_path(str(TARGET), run_name="__main__")
