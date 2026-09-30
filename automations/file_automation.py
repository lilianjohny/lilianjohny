"""01 File Automation: organize files by type, bulk-rename them, and back up folders."""
import argparse
import shutil
from datetime import datetime
from pathlib import Path

CATEGORIES = {
    "Images": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"},
    "Documents": {".pdf", ".doc", ".docx", ".txt", ".md", ".xlsx", ".csv", ".pptx"},
    "Archives": {".zip", ".tar", ".gz", ".rar", ".7z"},
    "Audio": {".mp3", ".wav", ".flac", ".aac"},
    "Video": {".mp4", ".mkv", ".mov", ".avi"},
    "Code": {".py", ".js", ".ts", ".html", ".css", ".json", ".sh"},
}


def category_for(path: Path) -> str:
    ext = path.suffix.lower()
    for name, exts in CATEGORIES.items():
        if ext in exts:
            return name
    return "Other"


def _unique(target: Path) -> Path:
    """Avoid overwriting an existing file by appending _1, _2, ..."""
    counter = 1
    candidate = target
    while candidate.exists():
        candidate = target.with_name(f"{target.stem}_{counter}{target.suffix}")
        counter += 1
    return candidate


def organize(folder: Path, dry_run: bool = False) -> list[tuple[Path, Path]]:
    """Move every file in `folder` into a sub-folder named after its category."""
    moves = []
    for item in sorted(folder.iterdir()):
        if not item.is_file():
            continue
        dest = _unique(folder / category_for(item) / item.name)
        moves.append((item, dest))
        if not dry_run:
            dest.parent.mkdir(exist_ok=True)
            shutil.move(item, dest)
    return moves


def bulk_rename(folder: Path, prefix: str, dry_run: bool = False) -> list[tuple[Path, Path]]:
    """Rename files to <prefix>_001.ext, <prefix>_002.ext, ..."""
    renames = []
    files = sorted(p for p in folder.iterdir() if p.is_file())
    for i, item in enumerate(files, start=1):
        dest = _unique(item.with_name(f"{prefix}_{i:03d}{item.suffix.lower()}"))
        renames.append((item, dest))
        if not dry_run:
            item.rename(dest)
    return renames


def backup(folder: Path, dest_dir: Path) -> Path:
    """Create a timestamped .zip backup of `folder` inside `dest_dir`."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = dest_dir / f"{folder.name}_backup_{stamp}"
    return Path(shutil.make_archive(str(base), "zip", root_dir=folder))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("organize", help="sort files into folders by type")
    p.add_argument("folder", type=Path)
    p.add_argument("--dry-run", action="store_true")
    p = sub.add_parser("rename", help="bulk rename files with a prefix")
    p.add_argument("folder", type=Path)
    p.add_argument("prefix")
    p.add_argument("--dry-run", action="store_true")
    p = sub.add_parser("backup", help="zip a folder with a timestamp")
    p.add_argument("folder", type=Path)
    p.add_argument("--dest", type=Path, default=Path("backups"))
    args = parser.parse_args()

    if args.cmd == "organize":
        for src, dst in organize(args.folder, args.dry_run):
            print(f"{src.name} -> {dst.relative_to(args.folder)}")
    elif args.cmd == "rename":
        for src, dst in bulk_rename(args.folder, args.prefix, args.dry_run):
            print(f"{src.name} -> {dst.name}")
    else:
        print(f"Backup created: {backup(args.folder, args.dest)}")


if __name__ == "__main__":
    main()
