"""
Converts every .html file in a folder to a same-named .pdf, in the same folder.

Uses headless Microsoft Edge / Google Chrome's own --print-to-pdf, NOT
xhtml2pdf. This was a deliberate choice after actually testing both: this
repo's test-paper HTML (first_run/TESTS/) uses ordinary CSS (a bordered
cover box, flex/inline-block layout, border-bottom "fill in" lines) that
xhtml2pdf (reportlab-based, a real CSS subset -- see CLAUDE.md's brand-kit
`em`-unit finding for a prior instance of this same class of gap) renders
incorrectly: it duplicates a bordered container's border onto every nested
block child, and silently drops border-bottom on inline-block spans, with
zero error reported either way. Headless-browser printing uses the exact
same rendering engine already verified via screenshot for this HTML, so
what you see in the browser is what prints -- consistent with this repo's
own established discipline (CLAUDE.md section 7, point 7: never trust a
layout by reading code alone, verify with a real render) applied to PDF
export too. If a future use of this script needs xhtml2pdf specifically
(e.g. matching the bot's existing on-demand PDF style), write a separate
script -- don't silently swap the engine here.

Usage:
    python html_to_pdf.py                      # converts first_run/TESTS/
    python html_to_pdf.py <folder>              # converts any folder
    python html_to_pdf.py <folder> --pattern "AS*_Test_Paper_*.html"
"""
import argparse
import os
import shutil
import subprocess
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DIR = os.path.normpath(os.path.join(HERE, "..", "TESTS"))

CANDIDATE_BROWSERS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]


def find_browser():
    for name in ("msedge", "msedge.exe", "chrome", "chrome.exe", "google-chrome"):
        found = shutil.which(name)
        if found:
            return found
    for path in CANDIDATE_BROWSERS:
        if os.path.isfile(path):
            return path
    raise SystemExit(
        "Could not find msedge.exe or chrome.exe on this machine. "
        "Install Microsoft Edge or Google Chrome, or edit CANDIDATE_BROWSERS "
        "in this script to point at your browser's .exe."
    )


def convert_one(browser, html_path, pdf_path):
    file_url = "file:///" + urllib.parse.quote(html_path.replace("\\", "/"))
    cmd = [
        browser,
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path}",
        "--print-to-pdf-no-header",
        file_url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return result.returncode == 0 and os.path.isfile(pdf_path) and os.path.getsize(pdf_path) > 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", nargs="?", default=DEFAULT_DIR,
                         help=f"Folder to scan for .html files (default: {DEFAULT_DIR})")
    parser.add_argument("--pattern", default=None,
                         help="Only convert files whose name contains this substring")
    args = parser.parse_args()

    folder = os.path.abspath(args.folder)
    if not os.path.isdir(folder):
        raise SystemExit(f"Not a folder: {folder}")

    html_files = sorted(f for f in os.listdir(folder) if f.lower().endswith(".html"))
    if args.pattern:
        html_files = [f for f in html_files if args.pattern in f]

    if not html_files:
        print(f"No .html files found in {folder}")
        return

    browser = find_browser()
    print(f"Using browser: {browser}\n")

    ok, failed = [], []
    for fname in html_files:
        html_path = os.path.join(folder, fname)
        pdf_path = os.path.join(folder, os.path.splitext(fname)[0] + ".pdf")
        print(f"Converting {fname} -> {os.path.basename(pdf_path)} ...", end=" ")
        try:
            success = convert_one(browser, html_path, pdf_path)
        except Exception as exc:
            print(f"ERROR: {exc}")
            failed.append((fname, str(exc)))
            continue
        if success:
            size_kb = os.path.getsize(pdf_path) / 1024
            print(f"OK ({size_kb:.0f} KB)")
            ok.append(fname)
        else:
            print("FAILED")
            failed.append((fname, "browser print-to-pdf did not produce a file"))

    print(f"\n{len(ok)} converted, {len(failed)} failed.")
    if failed:
        print("Failed files:")
        for fname, reason in failed:
            print(f"  {fname}: {reason}")
        sys.exit(1)


if __name__ == "__main__":
    main()
