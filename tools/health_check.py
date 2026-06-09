#!/usr/bin/env python3
"""health_check.py - validate cap-online folder structure and README links."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_DIRS = [
    "_claude/memory", "_claude/artifacts", "_claude/skills",
    "books/strategy-book/drafts", "books/strategy-book/working", "books/strategy-book/final",
    "books/concept-book/chapter-zero", "books/concept-book/characters",
    "books/concept-book/chapters", "books/concept-book/story-vignettes",
    "books/concept-book/revision-material",
    "books/about-author",
    "syllabus-engine/data", "syllabus-engine/scripts", "syllabus-engine/html-source",
    "question-bank/pyq", "question-bank/mtp", "question-bank/rtp", "question-bank/solutions",
    "mcq-platform/question-generation", "mcq-platform/database", "mcq-platform/cloudflare-app",
    "vc-gurukul/management-discussions", "vc-gurukul/events", "vc-gurukul/batch-july-2025",
    "vc-gurukul/contracts",
    "content/reels", "content/motivation", "content/competitor-analysis",
    "content/ai-content-pipeline",
    "telegram/bots", "telegram/source-docs",
    "obs-setup", "obs-setup/assets", "obs-setup/recordings",
    "photo-gallery/originals",
    "materials/icai-source", "materials/reference",
    "planning", "preparations", "tools",
]

REVIEW_DIRS = {"book", "preparation-materials", "recording"}


def check_dirs():
    return ["MISSING folder: " + d for d in EXPECTED_DIRS if not (ROOT / d).is_dir()]


def check_readme_links():
    readme = ROOT / "README.md"
    if not readme.exists():
        return ["MISSING README.md"]
    text = readme.read_text(encoding="utf-8", errors="ignore")
    problems = []
    for m in re.finditer(r"\]\(([^)]+)\)", text):
        target = m.group(1).split("#")[0].strip()
        if not target or target.startswith(("http://", "https://", "mailto:")):
            continue
        if not (ROOT / target).exists():
            problems.append("README link broken: " + target)
    return problems


def list_review():
    out = []
    for child in sorted(ROOT.iterdir()):
        if child.is_dir() and child.name in REVIEW_DIRS:
            out.append("REVIEW (pending migration): " + child.name + "/")
    return out


def main():
    dp = check_dirs()
    lp = check_readme_links()
    review = list_review()
    print("=== cap-online health check ===\n")
    print("Expected folders present: %d/%d" % (len(EXPECTED_DIRS) - len(dp), len(EXPECTED_DIRS)))
    for p in dp + lp:
        print("  [FAIL] " + p)
    for r in review:
        print("  [warn] " + r)
    if not dp and not lp:
        print("\nOK - structure valid and README links resolve.")
        return 0
    print("\n%d problem(s) found." % (len(dp) + len(lp)))
    return 1


if __name__ == "__main__":
    sys.exit(main())
