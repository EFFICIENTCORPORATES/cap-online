#!/usr/bin/env python3
"""
export_amritras_pdf.py -- headless-Chrome PDF export of
AMRITRAS-QUESTION-BANK.html.

Deliberately NOT html_to_pdf.py's plain `subprocess --print-to-pdf`: that
has no way to know paged.js (an async, JS-driven polyfill) has actually
finished restructuring the DOM into .pagedjs_page containers before the
print snapshot is taken -- fine for the simple, static test-paper HTML
that script was built for, not safe for a 277-page paged.js document.
This script instead reuses the exact wait-for-stable-pagination mechanism
already proven in resolve_qb_toc_pages.py (imported, not reimplemented),
THEN calls Page.printToPDF directly over the DevTools Protocol -- the same
underlying action as Ctrl+P -> Save as PDF -- with preferCSSPageSize so
paged.js's own @page size (from book-style.json) is honoured rather than a
default Letter/A4 guess, and printBackground so the colour-coded boxes
(Examiner's Comment / Author's Note / etc.) survive into the PDF.

Usage: python export_amritras_pdf.py [source.html] [output.pdf]
       Defaults: first_run/output/AMRITRAS-QUESTION-BANK.html ->
                 first_run/output/AMRITRAS-QUESTION-BANK.pdf
"""
import base64
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import resolve_qb_toc_pages as rtp  # noqa: E402
import qb_common as qc  # noqa: E402

DEFAULT_SOURCE = qc.OUTPUT_DIR / "AMRITRAS-QUESTION-BANK.html"
DEFAULT_OUT = qc.OUTPUT_DIR / "AMRITRAS-QUESTION-BANK.pdf"


def print_to_pdf(cdp) -> bytes:
    cdp._id += 1
    mid = cdp._id
    cdp.ws.send(json.dumps({
        "id": mid,
        "method": "Page.printToPDF",
        "params": {
            "printBackground": True,
            "preferCSSPageSize": True,
            "marginTop": 0, "marginBottom": 0, "marginLeft": 0, "marginRight": 0,
            "displayHeaderFooter": False,
        },
    }))
    while True:
        msg = json.loads(cdp.ws.recv())
        if msg.get("id") == mid:
            if "error" in msg:
                raise SystemExit(f"Page.printToPDF failed: {msg['error']}")
            return base64.b64decode(msg["result"]["data"])


def main():
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SOURCE
    out_pdf = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUT

    if not source.exists():
        raise SystemExit(f"ERROR: {source} not found.")

    chrome_path = rtp.find_chrome()
    user_data_dir = Path(r"C:\temp\export-amritras-pdf-chrome-profile")
    proc = rtp.launch_chrome(chrome_path, user_data_dir)
    try:
        file_url = "file:///" + str(source.resolve()).replace("\\", "/")
        cdp = rtp.CDP(file_url)
        try:
            n_pages = rtp.wait_for_stable_pagination(cdp)
            print(f"Pagination stable at {n_pages} pages. Printing to PDF...")
            # Page.printToPDF on a 277-page, image/font-heavy document can
            # take well past the CDP class's default 10s recv timeout --
            # widen it just for this one blocking call.
            cdp.ws.settimeout(240)
            pdf_bytes = print_to_pdf(cdp)
        finally:
            cdp.close()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except Exception:
            proc.kill()

    out_pdf.write_bytes(pdf_bytes)
    print(f"Wrote {out_pdf} ({len(pdf_bytes):,} bytes)")


if __name__ == "__main__":
    main()
