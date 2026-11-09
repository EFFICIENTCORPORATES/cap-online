#!/usr/bin/env python3
"""List the headings of an ICAI study-material chapter (BEAUTIFIED .md) with printed pages.

Usage:
  python3 list_headings.py "<path to chapter .md>"
  python3 list_headings.py --find "Internal Reconstruction"     # locate the chapter file first

Output: line number, printed page, heading. Illustrations are ILL-n, ICAI's own examples EX-n,
notes NOTE-n, Test Your Knowledge items TYK-MCQ-n / TYK-TQ-n / TYK-SBQ-n.
The printed page is the ICAI_SOURCE_PAGE marker in force at that line (the page the text sits on).
"""
import glob
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
MODULES = os.path.join(ROOT, "books/ca-inter/smat-may-27-edition/all-modules")


def find(term):
    hits = [f for f in glob.glob(os.path.join(MODULES, "*BEAUTIFIED.md")) if term.lower() in os.path.basename(f).lower()]
    if not hits:
        sys.exit(f"No chapter file matching '{term}' in {MODULES}")
    return hits


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    if args[0] == "--find":
        for f in find(" ".join(args[1:])):
            print(f)
        return
    page = None
    for i, line in enumerate(open(args[0], encoding="utf-8").read().split("\n"), 1):
        m = re.search(r'printed_page="([^"]+)"', line)
        if m:
            page = m.group(1)
        if re.match(r"^#{2,5}\s", line):
            print(f"L{i:<5} p{page or '-':<7} {line[:110]}")


if __name__ == "__main__":
    main()
