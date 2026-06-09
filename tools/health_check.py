#!/usr/bin/env python3
"""health_check.py — validate cap-online folder structure and README links.

Checks:
  1. All expected folders from the agreed structure exist.
  2. Every relative link/path referenced in README.md actually exists.
  3. Reports any top-level folders not in the agreed structure (review items).

Usage:  python tools/health_check.py
Exit code 0 = all good, 1 = problems found.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_DIRS = [
    "_claude/memory", "_claude/artifacts", "_claude/skills",
    "books/strategy-book/drafts", "books/strategy-book/working", "books/strategy-book/final",
    "books/concept-book/chapter-zero", "books/concept-book/characters",
    "books/adv-accounts-book/chapters", "books/adv-accounts-book/story-vignettes",
    "books/adv-accounts-book/revision-material",
    "syllabus-engine/data", "syllabus-engine/scripts", "syllabus-engine/html-source",
    "vc-gurukul/management-discussions", "vc-gurukul/events", "vc-gurukul/batch-july-2025",
    "content/reels", "content/motivation", "content/competitor-analysis",
    "telegram/bots", "telegram/source-docs",
    "obs-setup", "photo-gallery/originals",
    "materials/icai-source", "materials/reference",
    "preparations", "tools",
]

# Top-level folders that are allowed but flagged as "pending review"
REVIEW_DIRS = {"book", "preparation-materials", "recording"}


def check_dirs() -> list[str]:
    problems = []
    for d in EXPECTED_DIRS:
        if not (ROOT / d).is_dir():
            problems.append(f"MISSING folder: {d}")
    return problems


def check_readme_links() -> list[str]:
    readme = ROOT / "README.md"
    if not readme.exists():
        return ["MISSING README.md"]
    text = readme.read_text(encoding="utf-8", errors="ignore")
    problems = []
    # markdown links [text](path) with non-URL targets
    for m in re.finditer(r"\]\(([^)]+)\)", text):
        target = m.group(1).split("#")[0].strip()
        if not target or target.startswith(("http://", "https://", "mailto:")):
            continue
        if not (ROOT / target).exists():
            problems.append(f"README link broken: {target}")
    return problems


def list_review() -> list[str]:
    found = []
    for child in sorted(ROOT.iterdir()):
        if child.is_dir() and child.name in REVIEW_DIRS:
            found.append(f"REVIEW (pending migration): {child.name}/")
    return found


def main() -> int:
    dir_problems = check_dirs()
    link_problems = check_readme_links()
    review = list_review()

    print("=== cap-online health check ===\n")
    print(f"Expected folders present: {len(EXPECTED_DIRS) - len(dir_problems)}/{len(EXPECTED_DIRS)}")

    for p in dir_problems + link_problems:
        print("  [FAIL]", p)
    for r in review:
        print("  [warn]", r)

    if not dir_problems and not link_problems:
        print("\nOK — structure valid and README links resolve.")
        return 0
    print(f"\n{len(dir_problems) + len(link_problems)} problem(s) found.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
