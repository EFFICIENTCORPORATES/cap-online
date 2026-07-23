#!/usr/bin/env python3
"""
resolve_toc_pages.py — bake real page numbers into the Table of Contents
============================================================================

WHY THIS SCRIPT EXISTS
------------------------
tools/generate_toc.py builds build/toc.html with each page-number cell left
empty (`<span class="toc-page" data-target-id="bucket-3"></span>`). Nobody
can fill those in at generation time -- what page Bucket 3 starts on depends
on paged.js actually laying out the entire merged book (font metrics, line
wrapping, everything that came before it), which only happens in a browser,
after the book has been merged.

The obvious "correct" answer -- CSS `target-counter()` -- was tried first and
is confirmed BROKEN in the vendored paged.js version: it parses without
error and allocates an internal counter placeholder, but never actually
resolves to a rendered value. This matches a real, still-open upstream bug
(pagedjs/pagedjs#145, "TOC page number always zero"). Full investigation
in Claude_V2.md -- don't re-attempt target-counter() without reading that
first.

What DOES work, verified directly: paged.js stamps a real, reliable
`data-page-number` attribute on every `.pagedjs_page` container div it
creates. This script:

  1. Launches its own headless Chrome with remote debugging enabled (no
     manual setup needed -- it manages the whole browser process itself).
  2. Loads the ALREADY-MERGED build/FULL-BOOK.html.
  3. Polls .pagedjs_page count over REAL wall-clock time until it stops
     changing -- NOT a fixed --virtual-time-budget guess. This book is large
     enough that a fixed timer previously produced a different (wrong) page
     count on almost every run; see Claude_V2.md section 15 for why that
     happened and why polling for real-time stability is the only reliable
     signal for a document this size.
  4. For every element with a `data-target-id` in toc.html, finds the real
     section element with that id, walks up to its nearest `.pagedjs_page`
     ancestor, and reads that container's `data-page-number`.
  5. Rewrites build/toc.html, replacing each empty
     `<span class="toc-page" data-target-id="...">` with the real number as
     plain static text.

You MUST re-run tools/strategy_book_merge.py after this script to bake the
corrected toc.html into a fresh FULL-BOOK.html -- this script only fixes
toc.html; pass --remerge to have it do that final merge automatically.

USAGE
-----
    python tools/strategy_book_merge.py --force   # first pass: merge with
                                                    # blank ToC page numbers
    python tools/resolve_toc_pages.py --remerge   # resolve + re-merge in
                                                    # one step
"""

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

try:
    import websocket  # from the `websocket-client` package
except ImportError:
    raise SystemExit(
        "ERROR: the 'websocket-client' package is required "
        "(pip install websocket-client) -- this script drives Chrome "
        "directly over the DevTools Protocol to read real page numbers."
    )

BUILD_DIR = (
    Path(__file__).resolve().parent.parent
    / "books" / "strategy-book" / "design" / "templates" / "build"
)
FULL_BOOK = BUILD_DIR / "FULL-BOOK.html"
TOC_FILE = BUILD_DIR / "toc.html"

DEBUG_PORT = 9222
# How long .pagedjs_page count must stop changing before we trust it as the
# real, final layout -- not a virtual-time guess, genuine repeated checks
# over real time (see module docstring point 3).
STABLE_CHECKS_REQUIRED = 5
POLL_INTERVAL_SECONDS = 2
MAX_WAIT_SECONDS = 120

CHROME_CANDIDATES = [
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]


def find_chrome() -> str:
    for path in CHROME_CANDIDATES:
        if Path(path).exists():
            return path
    raise SystemExit(
        "ERROR: could not find chrome.exe or msedge.exe in any known "
        "location. Edit CHROME_CANDIDATES in this script if it's "
        "installed somewhere else."
    )


def launch_chrome(chrome_path: str, user_data_dir: Path) -> subprocess.Popen:
    proc = subprocess.Popen([
        chrome_path,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--no-first-run",
        "--disable-extensions",
        f"--remote-debugging-port={DEBUG_PORT}",
        "--remote-allow-origins=*",
        f"--user-data-dir={user_data_dir}",
        "about:blank",
    ])
    # Wait for the DevTools HTTP endpoint to actually come up.
    for _ in range(30):
        try:
            urllib.request.urlopen(f"http://localhost:{DEBUG_PORT}/json/version", timeout=1)
            return proc
        except Exception:
            time.sleep(0.5)
    proc.kill()
    raise SystemExit("ERROR: Chrome's remote debugging port never came up.")


class CDP:
    """Minimal Chrome DevTools Protocol client -- just enough to open a
    tab, run Runtime.evaluate, and read the result. Not a general-purpose
    library; this repo has no other CDP need beyond this one script."""

    def __init__(self, file_url: str):
        # Chrome's DevTools HTTP endpoint requires PUT for /json/new --
        # plain urlopen() defaults to GET, which it rejects with 405.
        req = urllib.request.Request(
            f"http://localhost:{DEBUG_PORT}/json/new?{file_url}", method="PUT"
        )
        r = urllib.request.urlopen(req, timeout=10)
        tab = json.loads(r.read())
        self.ws = websocket.create_connection(tab["webSocketDebuggerUrl"], timeout=10)
        self._id = 0
        self.eval("void 0")  # Runtime.enable equivalent isn't required for eval-only use

    def eval(self, expression: str):
        self._id += 1
        mid = self._id
        self.ws.send(json.dumps({
            "id": mid, "method": "Runtime.evaluate",
            "params": {"expression": expression, "returnByValue": True},
        }))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == mid:
                result = msg.get("result", {}).get("result", {})
                if "value" in result:
                    return result["value"]
                return None

    def close(self):
        self.ws.close()


def wait_for_stable_pagination(cdp: CDP) -> int:
    start = time.time()
    last = None
    stable = 0
    while time.time() - start < MAX_WAIT_SECONDS:
        n = cdp.eval("document.querySelectorAll('.pagedjs_page').length")
        stable = stable + 1 if n == last else 0
        last = n
        if stable >= STABLE_CHECKS_REQUIRED:
            return n
        time.sleep(POLL_INTERVAL_SECONDS)
    raise SystemExit(
        f"ERROR: pagination never stabilized within {MAX_WAIT_SECONDS}s "
        f"(last count seen: {last}). The book may be larger than usual, or "
        "something is genuinely broken -- try increasing MAX_WAIT_SECONDS "
        "before assuming the latter."
    )


def resolve_page_numbers(cdp: CDP, target_ids: list) -> dict:
    result = cdp.eval(f"""
    JSON.stringify(({json.dumps(target_ids)}).map(id => {{
        const el = document.getElementById(id);
        if (!el) return [id, null];
        const pageEl = el.closest('.pagedjs_page');
        if (!pageEl) return [id, null];
        return [id, pageEl.getAttribute('data-page-number')];
    }}))
    """)
    pairs = json.loads(result)
    missing = [tid for tid, num in pairs if num is None]
    if missing:
        raise SystemExit(
            "ERROR: could not resolve a page number for: " + ", ".join(missing) +
            " -- check these ids actually exist in FULL-BOOK.html "
            "(strategy_book_parser.py's _h1() must have run on the "
            "corresponding section)."
        )
    return {tid: num for tid, num in pairs}


def patch_toc_file(page_numbers: dict) -> None:
    text = TOC_FILE.read_text(encoding="utf-8")

    def repl(m):
        slug = m.group("slug")
        num = page_numbers.get(slug)
        if num is None:
            return m.group(0)
        return m.group("open") + num + "</span>"

    pattern = re.compile(
        r'(?P<open><span class="toc-page" data-target-id="(?P<slug>[a-z0-9-]+)"[^>]*>)'
        r'(?:\s*)</span>'
    )
    new_text, count = pattern.subn(repl, text)
    if count != len(page_numbers):
        raise SystemExit(
            f"ERROR: expected to patch {len(page_numbers)} .toc-page spans "
            f"in toc.html, only matched {count}. toc.html may be stale -- "
            "re-run tools/generate_toc.py and merge again before retrying."
        )
    TOC_FILE.write_text(new_text, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--remerge", action="store_true",
        help="Automatically re-run strategy_book_merge.py --force after "
             "patching toc.html, so FULL-BOOK.html ends up with the "
             "correct numbers baked in without a separate manual step."
    )
    args = ap.parse_args()

    if not FULL_BOOK.exists():
        raise SystemExit(
            f"ERROR: {FULL_BOOK} not found -- run "
            "tools/strategy_book_merge.py first (a first pass with blank "
            "ToC page numbers is expected and fine)."
        )
    if not TOC_FILE.exists():
        raise SystemExit(f"ERROR: {TOC_FILE} not found -- run tools/generate_toc.py first.")

    target_ids = sorted(set(
        re.findall(r'data-target-id="([a-z0-9-]+)"', TOC_FILE.read_text(encoding="utf-8"))
    ))
    if not target_ids:
        raise SystemExit("ERROR: no data-target-id spans found in toc.html.")

    chrome_path = find_chrome()
    user_data_dir = Path(r"C:\temp\resolve-toc-chrome-profile")
    proc = launch_chrome(chrome_path, user_data_dir)
    try:
        file_url = "file:///" + str(FULL_BOOK.resolve()).replace("\\", "/")
        cdp = CDP(file_url)
        try:
            n_pages = wait_for_stable_pagination(cdp)
            print(f"Pagination stable at {n_pages} pages.")
            page_numbers = resolve_page_numbers(cdp, target_ids)
            for slug in target_ids:
                print(f"  {slug:20s} -> page {page_numbers[slug]}")
        finally:
            cdp.close()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()

    patch_toc_file(page_numbers)
    print(f"Patched: {TOC_FILE}")

    if args.remerge:
        merge_script = Path(__file__).resolve().parent / "strategy_book_merge.py"
        print("Re-merging with corrected page numbers...")
        subprocess.run([sys.executable, str(merge_script), "--force"], check=True)


if __name__ == "__main__":
    main()
