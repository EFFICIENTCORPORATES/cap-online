#!/usr/bin/env python3
"""Print an HTML (or Markdown) teaching file as plain text, in reading order.

Usage: python3 -I extract_text.py <file.html|file.md>

Scripts and styles are dropped; block elements become line breaks; tables keep their cells on one line.
Read the WHOLE output when reviewing: coverage gaps hide in boxes, tables and footers.
"""
import html
import re
import sys


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    text = open(sys.argv[1], encoding="utf-8").read()
    if sys.argv[1].lower().endswith((".html", ".htm")):
        text = re.sub(r"<(script|style).*?</\1>", "", text, flags=re.S | re.I)
        text = re.sub(r"</t[dh]>", " | ", text, flags=re.I)
        text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
        text = re.sub(r"</(p|div|li|h\d|tr|section|article|table)>", "\n", text, flags=re.I)
        text = html.unescape(re.sub(r"<[^>]+>", "", text))
    print(re.sub(r"\n\s*\n+", "\n", text))


if __name__ == "__main__":
    main()
