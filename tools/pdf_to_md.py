#!/usr/bin/env python3
"""
pdf_to_md.py — Bulk PDF to Markdown converter (markitdown wrapper with cleanup).

Post-processes markitdown output to produce clean, Unix-compatible UTF-8 Markdown:
  - Removes NUL bytes (\\x00)
  - Normalises Windows line endings (CRLF) to Unix LF
  - Fixes character-spaced OCR text  (e.g. "A D V A N C E D" -> "ADVANCED")
  - Writes output .md alongside each source PDF (same folder, same name)
  - Appends to conversion_log.txt and conversion_log.xlsx one level above input folder

Usage:
  python tools/pdf_to_md.py <folder>             # convert all PDFs recursively
  python tools/pdf_to_md.py <file.pdf>           # convert a single file
  python tools/pdf_to_md.py <folder> --overwrite # re-convert even if .md exists
  python tools/pdf_to_md.py <folder> --dry-run   # preview without writing files

Requirements:
  pip install markitdown openpyxl
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Dependency checks
# ---------------------------------------------------------------------------

try:
    from markitdown import MarkItDown
except ImportError:
    sys.exit(
        "ERROR: markitdown not found.\n"
        "Install via: pip install markitdown\n"
        "Or clone: https://github.com/microsoft/markitdown.git and pip install -e ."
    )

try:
    import openpyxl
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
except ImportError:
    sys.exit("ERROR: openpyxl not found.  Install via: pip install openpyxl")


# ---------------------------------------------------------------------------
# Post-processing helpers
# ---------------------------------------------------------------------------

def _remove_nul_bytes(text: str) -> tuple:
    """Remove NUL (\\x00) bytes. Returns (cleaned_text, was_modified)."""
    cleaned = text.replace("\x00", "")
    return cleaned, cleaned != text


def _normalise_line_endings(text: str) -> tuple:
    """Replace CRLF and bare CR with LF. Returns (cleaned_text, was_modified)."""
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
    return cleaned, cleaned != text


def _fix_char_spacing(text: str) -> tuple:
    """
    Fix character-spaced OCR text produced by some PDF encodings.

    Pattern: each letter is separated by a single space; words are separated
    by two or more spaces.  e.g.  "A D V A N C E D   A C C O U N T I N G"
    becomes "ADVANCED ACCOUNTING".

    Detection heuristic: if >60% of the whitespace-split tokens on a line
    are single alphanumeric characters and there are more than 4 such tokens,
    the line is treated as character-spaced.

    Markdown structural lines (headings, table rows, horizontal rules,
    bullet points) are left untouched.
    """
    lines = text.split("\n")
    fixed_lines = []
    modified = False

    for line in lines:
        stripped = line.strip()

        # Leave structural Markdown lines as-is
        if (
            not stripped
            or stripped.startswith("#")
            or stripped.startswith("|")
            or stripped.startswith("-")
            or stripped.startswith("*")
            or stripped.startswith(">")
            or stripped.startswith("```")
        ):
            fixed_lines.append(line)
            continue

        tokens = line.split(" ")
        non_empty = [t for t in tokens if t]
        single_char = [t for t in non_empty if len(t) == 1 and t.isalnum()]

        if len(non_empty) > 4 and len(single_char) / len(non_empty) > 0.60:
            # Split on 2+ consecutive spaces (word boundaries), collapse each word
            words = re.split(r" {2,}", line)
            fixed_words = ["".join(w.split(" ")) for w in words]
            fixed_lines.append(" ".join(w for w in fixed_words if w))
            modified = True
        else:
            fixed_lines.append(line)

    return "\n".join(fixed_lines), modified


def post_process(raw_text: str) -> dict:
    """
    Run all cleanup passes on raw markitdown output.
    Returns dict with cleaned text and boolean flags for each pass.
    """
    text, nul_removed = _remove_nul_bytes(raw_text)
    text, crlf_fixed = _normalise_line_endings(text)
    text, char_spacing_fixed = _fix_char_spacing(text)
    text = text.rstrip("\n") + "\n"   # single trailing newline
    return {
        "text": text,
        "nul_removed": nul_removed,
        "crlf_fixed": crlf_fixed,
        "char_spacing_fixed": char_spacing_fixed,
    }


# ---------------------------------------------------------------------------
# Single-file conversion
# ---------------------------------------------------------------------------

def convert_one(pdf_path: Path, converter: MarkItDown, overwrite: bool, dry_run: bool) -> dict:
    """
    Convert one PDF file.  Returns a result record (dict) for logging.
    """
    md_path = pdf_path.with_suffix(".md")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    record: dict = {
        "timestamp":          timestamp,
        "status":             None,
        "pdf_name":           pdf_path.name,
        "pdf_path":           str(pdf_path),
        "pdf_size_bytes":     pdf_path.stat().st_size,
        "md_name":            md_path.name,
        "md_path":            str(md_path),
        "md_size_bytes":      None,
        "md_line_count":      None,
        "nul_removed":        False,
        "crlf_fixed":         False,
        "char_spacing_fixed": False,
        "skipped":            False,
        "notes":              "",
    }

    if md_path.exists() and not overwrite:
        record["status"]  = "SKIPPED"
        record["skipped"] = True
        record["notes"]   = ".md already exists — pass --overwrite to re-convert"
        return record

    if dry_run:
        record["status"] = "DRY-RUN"
        return record

    try:
        result   = converter.convert(str(pdf_path))
        raw_text = result.text_content
        processed = post_process(raw_text)

        md_path.write_text(processed["text"], encoding="utf-8")

        record.update({
            "status":             "SUCCESS",
            "md_size_bytes":      md_path.stat().st_size,
            "md_line_count":      processed["text"].count("\n"),
            "nul_removed":        processed["nul_removed"],
            "crlf_fixed":         processed["crlf_fixed"],
            "char_spacing_fixed": processed["char_spacing_fixed"],
        })

    except Exception as exc:
        record["status"] = "FAILED"
        record["notes"]  = str(exc)

    return record


# ---------------------------------------------------------------------------
# Log writers
# ---------------------------------------------------------------------------

def write_txt_log(log_path: Path, records: list) -> None:
    """Append a run summary block to conversion_log.txt."""
    success = sum(1 for r in records if r["status"] == "SUCCESS")
    failed  = sum(1 for r in records if r["status"] == "FAILED")
    skipped = sum(1 for r in records if r["status"] == "SKIPPED")
    dry_run = sum(1 for r in records if r["status"] == "DRY-RUN")

    lines = [
        "",
        "=" * 72,
        f"Run timestamp : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Total files   : {len(records)}  |  "
        f"Success: {success}  |  Failed: {failed}  |  "
        f"Skipped: {skipped}  |  Dry-run: {dry_run}",
        "=" * 72,
    ]

    for r in records:
        flags = (
            (" [NUL-REMOVED]"  if r["nul_removed"]        else "") +
            (" [CRLF-FIXED]"   if r["crlf_fixed"]         else "") +
            (" [CHARFIX]"      if r["char_spacing_fixed"]  else "")
        )
        note = f"  -> {r['notes']}" if r["notes"] else ""
        lines.append(f"  [{r['status']:8s}]  {r['pdf_name']}  ->  {r['md_name']}{flags}{note}")

    with log_path.open("a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


# Excel column definitions: (header label, record key, column width)
_EXCEL_COLUMNS = [
    ("Timestamp",           "timestamp",          19),
    ("Status",              "status",             10),
    ("PDF Filename",        "pdf_name",           38),
    ("PDF Full Path",       "pdf_path",           65),
    ("PDF Size (bytes)",    "pdf_size_bytes",     17),
    ("MD Filename",         "md_name",            38),
    ("MD Full Path",        "md_path",            65),
    ("MD Size (bytes)",     "md_size_bytes",      16),
    ("MD Line Count",       "md_line_count",      14),
    ("NUL Removed",         "nul_removed",        13),
    ("CRLF Fixed",          "crlf_fixed",         12),
    ("Char Spacing Fixed",  "char_spacing_fixed", 19),
    ("Skipped",             "skipped",            10),
    ("Notes",               "notes",              45),
]

_STATUS_FILL = {
    "SUCCESS": "E2EFDA",  # soft green
    "FAILED":  "FCE4D6",  # soft red/orange
    "SKIPPED": "FFF2CC",  # soft yellow
    "DRY-RUN": "DDEBF7",  # soft blue
}


def write_excel_log(excel_path: Path, records: list) -> None:
    """Append records to conversion_log.xlsx. Creates file with header if absent."""
    if excel_path.exists():
        wb = openpyxl.load_workbook(excel_path)
        ws = wb.active
    else:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Conversion Log"

        # Header row
        header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True)
        for col_idx, (label, _, width) in enumerate(_EXCEL_COLUMNS, 1):
            cell = ws.cell(row=1, column=col_idx, value=label)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", wrap_text=False)
            ws.column_dimensions[get_column_letter(col_idx)].width = width

        ws.freeze_panes = "A2"  # keep header visible when scrolling

    for r in records:
        row_vals = []
        for _, key, _ in _EXCEL_COLUMNS:
            val = r[key]
            if isinstance(val, bool):
                val = "Yes" if val else "No"
            row_vals.append(val)
        ws.append(row_vals)

        fill_colour = _STATUS_FILL.get(r["status"], "FFFFFF")
        fill = PatternFill(start_color=fill_colour, end_color=fill_colour, fill_type="solid")
        for col_idx in range(1, len(_EXCEL_COLUMNS) + 1):
            ws.cell(row=ws.max_row, column=col_idx).fill = fill

    wb.save(excel_path)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bulk PDF -> Markdown converter using markitdown with UTF-8/Unix cleanup.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python tools/pdf_to_md.py materials/icai-source/\n"
            "  python tools/pdf_to_md.py materials/icai-source/ch1.pdf --overwrite\n"
            "  python tools/pdf_to_md.py materials/icai-source/ --dry-run\n"
        ),
    )
    parser.add_argument("path", help="PDF file or folder to process (folder = recursive)")
    parser.add_argument(
        "--overwrite", action="store_true",
        help="Re-convert even if the .md output already exists",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be converted without writing any files",
    )
    args = parser.parse_args()

    input_path = Path(args.path).resolve()
    if not input_path.exists():
        sys.exit(f"ERROR: path does not exist: {input_path}")

    # Collect PDFs and decide where logs go
    if input_path.is_file():
        if input_path.suffix.lower() != ".pdf":
            sys.exit(f"ERROR: not a PDF file: {input_path}")
        pdf_files = [input_path]
        log_dir = input_path.parent.parent   # one level above the containing folder
    else:
        pdf_files = sorted(input_path.rglob("*.pdf"))
        log_dir = input_path.parent          # one level above the input folder

    if not pdf_files:
        print(f"No PDF files found under: {input_path}")
        return

    log_dir.mkdir(parents=True, exist_ok=True)
    log_txt  = log_dir / "conversion_log.txt"
    log_xlsx = log_dir / "conversion_log.xlsx"

    print(f"Input  : {input_path}")
    print(f"PDFs   : {len(pdf_files)} file(s)")
    print(f"Logs   : {log_dir}")
    if args.dry_run:
        print("Mode   : DRY-RUN (nothing will be written)")
    print()

    converter = MarkItDown()
    records   = []

    for pdf_path in pdf_files:
        record = convert_one(pdf_path, converter, args.overwrite, args.dry_run)
        records.append(record)

        flags = (
            (" [NUL]"     if record["nul_removed"]        else "") +
            (" [CRLF]"    if record["crlf_fixed"]         else "") +
            (" [CHARFIX]" if record["char_spacing_fixed"]  else "")
        )
        print(f"  [{record['status']:8s}]  {record['pdf_name']}{flags}")
        if record["notes"]:
            print(f"             -> {record['notes']}")

    if not args.dry_run:
        write_txt_log(log_txt,  records)
        write_excel_log(log_xlsx, records)
        print(f"\nconversion_log.txt  -> {log_txt}")
        print(f"conversion_log.xlsx -> {log_xlsx}")

    success = sum(1 for r in records if r["status"] == "SUCCESS")
    failed  = sum(1 for r in records if r["status"] == "FAILED")
    skipped = sum(1 for r in records if r["status"] == "SKIPPED")
    print(f"\nDone.  Success: {success}  |  Failed: {failed}  |  Skipped: {skipped}")


if __name__ == "__main__":
    main()
