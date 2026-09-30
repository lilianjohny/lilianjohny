"""05 Cybersecurity (defensive): detect brute-force logins and hash files for integrity.

- `logscan`: parse an SSH auth log and flag IPs with repeated failed logins.
- `hash`   : record SHA-256 hashes of a folder, then re-run with --verify to spot changes.

Only run security tooling against systems you own or are authorized to test.
"""
import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

FAILED_LOGIN = re.compile(r"Failed password for (?:invalid user )?(\S+) from (\d{1,3}(?:\.\d{1,3}){3})")


def failed_logins(lines) -> Counter:
    """Count failed login attempts per source IP."""
    counts: Counter = Counter()
    for line in lines:
        m = FAILED_LOGIN.search(line)
        if m:
            counts[m.group(2)] += 1
    return counts


def suspicious_ips(counts: Counter, threshold: int) -> list[tuple[str, int]]:
    return [(ip, n) for ip, n in counts.most_common() if n >= threshold]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def hash_tree(folder: Path) -> dict[str, str]:
    return {str(p.relative_to(folder)): sha256(p) for p in sorted(folder.rglob("*")) if p.is_file()}


def compare(old: dict[str, str], new: dict[str, str]) -> dict[str, list[str]]:
    return {
        "added": sorted(new.keys() - old.keys()),
        "removed": sorted(old.keys() - new.keys()),
        "modified": sorted(k for k in old.keys() & new.keys() if old[k] != new[k]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("logscan", help="find brute-force attempts in an auth log")
    p.add_argument("logfile", type=Path)
    p.add_argument("--threshold", type=int, default=5)
    p = sub.add_parser("hash", help="create or verify a file-integrity baseline")
    p.add_argument("folder", type=Path)
    p.add_argument("--baseline", type=Path, default=Path("baseline.json"))
    p.add_argument("--verify", action="store_true")
    args = parser.parse_args()

    if args.cmd == "logscan":
        with args.logfile.open(errors="ignore") as f:
            counts = failed_logins(f)
        flagged = suspicious_ips(counts, args.threshold)
        print(f"{sum(counts.values())} failed logins from {len(counts)} IPs")
        for ip, n in flagged:
            print(f"  ALERT {ip}: {n} failed attempts")
    elif args.verify:
        changes = compare(json.loads(args.baseline.read_text()), hash_tree(args.folder))
        for kind, files in changes.items():
            for name in files:
                print(f"  {kind.upper():9} {name}")
        print("No changes detected." if not any(changes.values()) else "Integrity changes found!")
    else:
        args.baseline.write_text(json.dumps(hash_tree(args.folder), indent=2))
        print(f"Baseline saved to {args.baseline}")


if __name__ == "__main__":
    main()
