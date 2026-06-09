#!/usr/bin/env python3
"""gitignore_audit.py — flag large or binary files that git would track.

Scans the working tree for binary-type files or files above a size threshold
that are NOT ignored by .gitignore, so nothing heavy slips into history.

Usage:  python tools/gitignore_audit.py [--max-mb 5]
Exit code 0 = clean, 1 = offenders found.
"""
from __future__ import annotations
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BINARY_EXT = {
    ".pdf", ".docx", ".doc", ".pptx", ".ppt", ".xlsx", ".xls",
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif", ".webp", ".psd", ".ico",
    ".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg",
    ".mp4", ".mov", ".mkv", ".avi", ".webm", ".wmv",
    ".zip", ".rar", ".7z", ".tar", ".gz", ".exe", ".dll", ".msi", ".bin", ".iso",
}


def is_ignored(path: Path) -> bool:
    """True if git ignores this path."""
    try:
        r = subprocess.run(
            ["git", "check-ignore", "-q", str(path)],
            cwd=ROOT, capture_output=True,
        )
        return r.returncode == 0
    except FileNotFoundError:
        return False  # git not available; treat as not ignored


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-mb", type=float, default=5.0,
                    help="flag non-ignored files larger than this (MB)")
    args = ap.parse_args()
    limit = args.max_mb * 1024 * 1024

    offenders: list[str] = []
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        if any(part in {".git", ".venv", "__pycache__"} for part in p.parts):
            continue
        rel = p.relative_to(ROOT)
        binary = p.suffix.lower() in BINARY_EXT
        try:
            size = p.stat().st_size
        except OSError:
            continue
        large = size > limit
        if (binary or large) and not is_ignored(p):
            why = "binary" if binary else f"{size / 1e6:.1f}MB"
            offenders.append(f"  [{why}] {rel}")

    print("=== .gitignore audit ===\n")
    if offenders:
        print("Files git WOULD track but probably shouldn't:")
        print("\n".join(sorted(offenders)))
        print(f"\n{len(offenders)} offender(s). Add patterns to .gitignore.")
        return 1
    print(f"Clean — no binary or >{args.max_mb}MB files outside .gitignore.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
