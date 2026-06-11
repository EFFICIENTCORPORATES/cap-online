#!/usr/bin/env python3
"""health_check.py - validate cap-online folder structure, README links, encoding, and CLAUDE.md.

Checks:
  1. All expected folders from the agreed structure exist.
  2. Every relative link/path in README.md resolves.
  3. No tracked text file contains NUL bytes / invalid UTF-8.
  4. CLAUDE.md exists and is not stale (every live top-level folder is documented in it).
  5. Component index MD5 matches current MASTER.md (run generate_component_index.py if stale).
  6. Reports top-level folders not in the agreed structure (review items).

Usage:  python tools/health_check.py
Exit code 0 = all good, 1 = problems found.
"""
import hashlib
from pathlib import Path
import re
import subprocess
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
    "content/motivation", "content/competitor-analysis", "content/ai-content-pipeline",
    "content/assets", "content/assets/raw-footage",
    "content/social/personal", "content/social/vc-gurukul",
    "content/calendar", "content/scripts",
    "telegram/bots", "telegram/source-docs",
    "obs-setup", "obs-setup/assets", "obs-setup/recordings",
    "photo-gallery/originals",
    "materials/icai-source", "materials/reference",
    "planning", "preparations", "tools",
]

REVIEW_DIRS = {"book", "preparation-materials", "recording"}

TEXT_EXT = {".md", ".py", ".html", ".json", ".csv", ".txt",
            ".yml", ".yaml", ".toml", ".cfg", ".ini", ".js", ".css"}
SKIP_PARTS = {".git", ".venv", "__pycache__", "node_modules"}


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


def _git_ignored(path):
    """True if git ignores this path (so we don't flag local-only binaries)."""
    try:
        r = subprocess.run(["git", "check-ignore", "-q", str(path)],
                           cwd=ROOT, capture_output=True)
        return r.returncode == 0
    except FileNotFoundError:
        return False


def _live_top_level_dirs():
    """Top-level folders that should be documented (skip hidden / ignored / build dirs)."""
    out = []
    for child in sorted(ROOT.iterdir()):
        if not child.is_dir():
            continue
        if child.name.startswith(".") or child.name in SKIP_PARTS:
            continue
        if _git_ignored(child):
            continue
        out.append(child.name)
    return out


def check_encoding():
    """Flag tracked text files that contain NUL bytes or aren't valid UTF-8."""
    problems = []
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_PARTS for part in p.parts):
            continue
        if p.suffix.lower() not in TEXT_EXT and p.name != ".gitignore":
            continue
        if _git_ignored(p):
            continue
        data = p.read_bytes()
        rel = str(p.relative_to(ROOT))
        if b"\x00" in data:
            problems.append("NUL bytes in text file: %s (%d)" % (rel, data.count(b"\x00")))
            continue
        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            problems.append("not valid UTF-8: " + rel)
    return problems


def check_claude_md():
    """CLAUDE.md must exist and mention every live top-level folder (staleness guard)."""
    f = ROOT / "CLAUDE.md"
    if not f.exists():
        return ["MISSING CLAUDE.md (the session entry point)"]
    text = f.read_text(encoding="utf-8", errors="ignore")
    problems = []
    for name in _live_top_level_dirs():
        if name not in text:
            problems.append("CLAUDE.md may be stale: top-level '%s/' is not documented" % name)
    return problems


def check_component_index_stale():
    """Component index MD5 must match current MASTER.md; if not, regenerate with generate_component_index.py."""
    master = ROOT / "books/strategy-book/working/CA-Inter-Strategy-Book-MASTER.md"
    index  = ROOT / "books/strategy-book/working/MASTER-component-index.md"
    if not master.exists() or not index.exists():
        return []  # files missing — other checks will catch it
    current_md5 = hashlib.md5(master.read_bytes()).hexdigest()[:8]
    idx_text    = index.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"MD5:\s*`([0-9a-f]{8})`", idx_text)
    if not m:
        return ["component-index has no MD5 stamp — run: python tools/generate_component_index.py"]
    if m.group(1) != current_md5:
        return [
            f"component-index is STALE (stamped {m.group(1)}, current {current_md5})"
            " — run: python tools/generate_component_index.py"
        ]
    return []


def list_review():
    out = []
    for child in sorted(ROOT.iterdir()):
        if child.is_dir() and child.name in REVIEW_DIRS:
            out.append("REVIEW (pending migration): " + child.name + "/")
    return out


def main():
    dp = check_dirs()
    lp = check_readme_links()
    ep = check_encoding()
    cp = check_claude_md()
    ip = check_component_index_stale()
    review = list_review()
    print("=== cap-online health check ===\n")
    print("Expected folders present: %d/%d" % (len(EXPECTED_DIRS) - len(dp), len(EXPECTED_DIRS)))
    print("Text files checked for NUL/UTF-8: %s" % ("FAIL" if ep else "clean"))
    print("CLAUDE.md up to date: %s" % ("FAIL" if cp else "yes"))
    print("Component index in sync: %s" % ("FAIL" if ip else "yes"))
    for prob in dp + lp + ep + cp + ip:
        print("  [FAIL] " + prob)
    for r in review:
        print("  [warn] " + r)
    if not dp and not lp and not ep and not cp and not ip:
        print("\nOK - structure valid, README links resolve, encodings clean, CLAUDE.md current, component index in sync.")
        return 0
    print("\n%d problem(s) found." % (len(dp) + len(lp) + len(ep) + len(cp) + len(ip)))
    return 1


if __name__ == "__main__":
    sys.exit(main())
