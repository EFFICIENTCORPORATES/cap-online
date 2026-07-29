#!/usr/bin/env python3
"""
clean_pending_md.py -- deterministic post-processing for first_run/output/
pending-pdf-parsed/*.md (produced by a separate, fixed-behavior external AI
tool that cannot be re-prompted or given skills/instructions -- Pranav's
explicit constraint, 2026-07-27).

WHY THIS EXISTS
---------------
Read and byte-inspected the tool's first real output
(CAInter-AdvAcc-MTP-Jan2025-Set1-{Q,Ans}.md) directly. Found several
confirmed, systematic artifacts -- since the tool itself can't be steered,
the fix has to live here instead, applied identically to every file it ever
produces:

1. Every table cell repeats ` style='text-align: center; word-wrap: break-word;'`
   -- confirmed to account for 32.5% of the Q file's characters and 57.1% of
   the Ans file's. Pure bulk: the eventual schema-HTML build step re-authors
   table markup from scratch anyway (this repo's own table styling, not the
   source tool's), so this attribute is never read for its value, only paid
   for in tokens every time the file is read.
2. Literal two-character `\n` sequences embedded as TEXT inside table cells
   -- confirmed via char-code inspection (byte 92 then 110, not a real
   newline byte) -- renders as literal backslash-n in a browser instead of a
   line break.
3. The rupee symbol (U+20B9) sometimes corrupted into the LaTeX macro
   `\bar{x}` -- confirmed 6 occurrences in one file's EPS section, always in
   a "prefixing a number" position (i.e. standing in for "Rs./₹"). This is
   the one fix in this script with real accuracy stakes, so it's never
   silent: every occurrence is logged with surrounding context so a human/AI
   can spot-check it against the source PDF before trusting it.
4. Ordinal-suffix superscripts written as LaTeX math (`$ ^{st} $`,
   `$ ^{{th}} $` -- both single- and double-brace variants seen) instead of
   plain text.
5. Redundant doubly-nested `<div style="text-align: center;">` wrappers.
6. 3+ consecutive blank lines (harmless bulk).

Every fix here is FORMATTING/NOISE only -- no accounting figure, question
number, or English word is ever altered. This is not a substitute for
reading the source PDF when something looks genuinely wrong; it only removes
noise this specific tool is known to introduce every time, deterministically.

RULE: never build a sitting's schema HTML from the raw (unprocessed) file in
pending-pdf-parsed/ -- always run it through this script first and read the
output in pending-pdf-parsed-clean/ instead.

USAGE
-----
    python clean_pending_md.py                 # process every .md in pending-pdf-parsed/
                                                # not yet in pending-pdf-parsed-clean/
    python clean_pending_md.py --all            # reprocess everything (e.g. after
                                                 # editing this script's rules)
    python clean_pending_md.py <file.md>        # process one specific file by path
"""
import argparse
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIRST_RUN = HERE.parent
RAW_DIR = FIRST_RUN / "output" / "pending-pdf-parsed"
CLEAN_DIR = FIRST_RUN / "output" / "pending-pdf-parsed-clean"

_TD_STYLE_RE = re.compile(r" style=(['\"])text-align: center; word-wrap: break-word;\1")
_TABLE_WRAPPER_RE = re.compile(
    r'<table border=([\'"]?)1\1 style=([\'"])margin: auto; word-wrap: break-word;\2>'
)
_LITERAL_NEWLINE_RE = re.compile(r"\\n")
_ORDINAL_RE = re.compile(r"\$\s*\^\{+(st|nd|rd|th)\}+\s*\$")
_NESTED_DIV_RE = re.compile(
    r'<div style="text-align: center;"><div style="text-align: center;">(.*?)</div>\s*</div>',
    re.DOTALL,
)
_RUPEE_CORRUPT_RE = re.compile(r"\\bar\{x\}")
_BLANK_LINES_RE = re.compile(r"\n{3,}")


def clean_text(text: str, report: dict) -> str:
    # Log rupee-corruption context BEFORE replacing, so the report shows what
    # was actually there, not a self-referential "after" snapshot.
    rupee_contexts = []
    for m in _RUPEE_CORRUPT_RE.finditer(text):
        start = max(0, m.start() - 25)
        end = min(len(text), m.end() + 15)
        rupee_contexts.append(text[start:end].replace("\n", " "))
    report["rupee_fix_contexts"] = rupee_contexts

    text, n = _TD_STYLE_RE.subn("", text)
    report["style_attrs_stripped"] = n

    text, n = _TABLE_WRAPPER_RE.subn('<table border="1">', text)
    report["table_wrappers_normalized"] = n

    text, n = _LITERAL_NEWLINE_RE.subn("<br>", text)
    report["literal_newlines_fixed"] = n

    text, n = _ORDINAL_RE.subn(lambda m: m.group(1), text)
    report["ordinal_superscripts_fixed"] = n

    text, n = _NESTED_DIV_RE.subn(r'<div style="text-align: center;">\1</div>', text)
    report["nested_divs_collapsed"] = n

    text, n = _RUPEE_CORRUPT_RE.subn("₹", text)
    report["rupee_corruptions_fixed"] = n

    text, n = _BLANK_LINES_RE.subn("\n\n", text)
    report["excess_blank_lines_collapsed"] = n

    return text


def process_file(src: Path, dst_dir: Path) -> None:
    text = src.read_text(encoding="utf-8")
    orig_len = len(text)
    report = {}
    cleaned = clean_text(text, report)
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / src.name
    dst.write_text(cleaned, encoding="utf-8")
    new_len = len(cleaned)

    pct = (orig_len - new_len) / orig_len if orig_len else 0
    print(f"{src.name}: {orig_len:,} -> {new_len:,} chars ({pct:.1%} smaller)")
    for key in (
        "style_attrs_stripped", "table_wrappers_normalized",
        "literal_newlines_fixed", "ordinal_superscripts_fixed",
        "nested_divs_collapsed", "excess_blank_lines_collapsed",
    ):
        if report.get(key):
            print(f"    {key}: {report[key]}")
    if report["rupee_corruptions_fixed"]:
        print(f"    !! RUPEE-SYMBOL FIX APPLIED {report['rupee_corruptions_fixed']}x -- spot-check against source PDF:")
        for ctx in report["rupee_fix_contexts"]:
            print(f"       ...{ctx}...")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("file", nargs="?", help="Process one specific file instead of the whole folder.")
    ap.add_argument("--all", action="store_true", help="Reprocess every file, even if already cleaned.")
    args = ap.parse_args()

    if args.file:
        process_file(Path(args.file), CLEAN_DIR)
        return

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    found = False
    for src in sorted(RAW_DIR.glob("*.md")):
        dst = CLEAN_DIR / src.name
        if dst.exists() and not args.all:
            continue
        process_file(src, CLEAN_DIR)
        found = True
    if not found:
        print(f"Nothing new to clean in {RAW_DIR} (use --all to reprocess everything).")


if __name__ == "__main__":
    main()
