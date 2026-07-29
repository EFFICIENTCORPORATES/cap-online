"""
Batch driver: generate a chapter book for every unique data-final-chapter value
found in questions_index.json. Reuses generate_chapter_book.build_book() for each.

Usage: python generate_all_chapter_books.py
"""
import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_chapter_book import build_book, load_index

HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.normpath(os.path.join(HERE, "..", "output"))

# Chapter title overrides for the few chapters whose topic-tag "standard" field is n/a
# (not an AS-numbered standard) or where the raw title needs shortening for a filename/label.
TITLE_OVERRIDES = {
    "M3-C11-U1": ("Financial Statements", "Preparation of Financial Statements (Schedule III)"),
    "M3-C11-U2": ("Cash Flow Statement", "Cash Flow Statement"),
    "M3-C12-U0": ("Buy-back", "Buy-back of Securities"),
    "M3-C14-U0": ("Internal Reconstruction", "Internal Reconstruction"),
    "M3-C15-U0": ("Branch Accounting", "Accounting for Branches including Foreign Branches"),
    "M1-C1-U0": ("Intro to AS", "Introduction to Accounting Standards"),
    "M1-C2-U0": ("Framework", "Framework for Preparation and Presentation of Financial Statements"),
    "M1-C3-U0": ("Applicability of AS", "Applicability of Accounting Standards"),
}


NON_AS_SLUGS = {
    "M3-C11-U1": "FinancialStatements",
    "M3-C11-U2": "CashFlowStatement",
    "M3-C12-U0": "Buyback",
    "M3-C14-U0": "InternalReconstruction",
    "M3-C15-U0": "BranchAccounting",
    "M1-C1-U0": "IntroToAS",
    "M1-C2-U0": "Framework",
    "M1-C3-U0": "ApplicabilityOfAS",
}


def slug(unitcode, standard):
    if unitcode in NON_AS_SLUGS:
        return NON_AS_SLUGS[unitcode]
    if standard and standard.upper().startswith("AS "):
        num = standard.split()[1]
        return f"AS{int(num):02d}"
    return unitcode.replace("-", "")


def main():
    data = load_index()
    chapter_info = {}
    counts = Counter()
    legacy_skipped = Counter()
    for r in data:
        fc = r["final_chapter"]
        # LEGACY-* codes mark pre-syllabus-change topics (e.g. Hire Purchase,
        # Departmental Accounts) that don't exist in the current 36-chapter
        # taxonomy at all -- Pranav's decision (2026-07-28, see CLAUDE.md §6):
        # keep them in the sitting HTML/questions_index.json for a complete
        # record, but never generate a chapter book for one. No real chapter
        # exists for them to belong to.
        if fc and fc.startswith("LEGACY-"):
            legacy_skipped[fc] += 1
            continue
        counts[fc] += 1
        for t in r["topics"]:
            if t["unitcode"] == fc:
                chapter_info[fc] = (t.get("standard"), t.get("title"))

    if legacy_skipped:
        print(f"Skipped {sum(legacy_skipped.values())} LEGACY (pre-syllabus-change) "
              f"records across {len(legacy_skipped)} topics -- excluded from chapter "
              f"books by design, not an error:")
        for fc, n in sorted(legacy_skipped.items()):
            print(f"    {fc}: {n} record(s)")

    print(f"Generating {len(counts)} chapter books...")
    results = []
    for fc in sorted(counts):
        std, title = chapter_info.get(fc, (None, "Unknown"))
        if fc in TITLE_OVERRIDES:
            label, chapter_title = TITLE_OVERRIDES[fc]
        else:
            label = std or fc
            chapter_title = title

        out_filename = f"{slug(fc, std)}_Question_Book.html"
        build_book(fc, label, chapter_title, out_filename)
        results.append((fc, label, chapter_title, out_filename, counts[fc]))

    print(f"\nDone. {len(results)} chapter books written to {OUTPUT_DIR}")
    return results


if __name__ == "__main__":
    main()
