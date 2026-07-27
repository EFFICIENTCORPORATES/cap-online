#!/usr/bin/env python3
"""
resolve_qb_toc_pages.py — bake real page numbers into the Question Bank
Book's Table of Contents
============================================================================

Same job as tools/resolve_toc_pages.py, adapted for this book's shape: the
ToC lives inside front-matter.html (as `.qb-toc-page` spans, written by
generate_qb_toc.py), not in a standalone toc.html.

target-counter() is confirmed broken in this vendored paged.js version
(matches open upstream bugs, e.g. pagedjs/pagedjs#145) -- the verified
working mechanism is reading the real `data-page-number` attribute paged.js
stamps on every `.pagedjs_page` container, via a real headless Chrome pass.
See tools/resolve_toc_pages.py's docstring for the full investigation; not
repeated here.

USAGE
-----
    python qb_merge.py                       # first pass: blank ToC pages
    python resolve_qb_toc_pages.py --remerge  # resolve + re-merge in one step
"""

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import qb_common as qc  # noqa: E402

try:
    import websocket  # from the `websocket-client` package
except ImportError:
    raise SystemExit(
        "ERROR: the 'websocket-client' package is required "
        "(pip install websocket-client) -- this script drives Chrome "
        "directly over the DevTools Protocol to read real page numbers."
    )

OUTPUT_DIR = qc.OUTPUT_DIR
MERGED_BOOK = OUTPUT_DIR / "QUESTION-BANK-BOOK.html"
FRONT_MATTER_FILE = OUTPUT_DIR / "front-matter.html"

DEBUG_PORT = 9223  # different port than the strategy book's resolver, in
                    # case both are ever run in the same session
STABLE_CHECKS_REQUIRED = 5
POLL_INTERVAL_SECONDS = 2
MAX_WAIT_SECONDS = 180  # this book is larger than any single strategy-book
                        # section -- give pagination more real time before
                        # giving up

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
    for _ in range(30):
        try:
            urllib.request.urlopen(f"http://localhost:{DEBUG_PORT}/json/version", timeout=1)
            return proc
        except Exception:
            time.sleep(0.5)
    proc.kill()
    raise SystemExit("ERROR: Chrome's remote debugging port never came up.")


class CDP:
    """Minimal Chrome DevTools Protocol client -- same shape as the
    strategy book's resolver, just enough to open a tab, run
    Runtime.evaluate, and read the result."""

    def __init__(self, file_url: str):
        req = urllib.request.Request(
            f"http://localhost:{DEBUG_PORT}/json/new?{file_url}", method="PUT"
        )
        r = urllib.request.urlopen(req, timeout=10)
        tab = json.loads(r.read())
        self.ws = websocket.create_connection(tab["webSocketDebuggerUrl"], timeout=10)
        self._id = 0
        self.eval("void 0")

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
        f"(last count seen: {last}). This book is large -- try increasing "
        "MAX_WAIT_SECONDS before assuming something is genuinely broken."
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
            " -- check these ids actually exist in QUESTION-BANK-BOOK.html "
            "(qb_merge.py's page_shell() must have run on the corresponding "
            "chapter)."
        )
    return {tid: num for tid, num in pairs}


def patch_front_matter(page_numbers: dict) -> None:
    text = FRONT_MATTER_FILE.read_text(encoding="utf-8")

    def repl(m):
        slug = m.group("slug")
        num = page_numbers.get(slug)
        if num is None:
            return m.group(0)
        return m.group("open") + num + "</span>"

    pattern = re.compile(
        r'(?P<open><span class="qb-toc-page" data-target-id="(?P<slug>[a-z0-9-]+)"[^>]*>)'
        r'(?:\s*)</span>'
    )
    new_text, count = pattern.subn(repl, text)
    if count != len(page_numbers):
        raise SystemExit(
            f"ERROR: expected to patch {len(page_numbers)} .qb-toc-page "
            f"spans in front-matter.html, only matched {count}. It may be "
            "stale -- re-run generate_qb_toc.py and merge again before "
            "retrying."
        )
    FRONT_MATTER_FILE.write_text(new_text, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--remerge", action="store_true",
        help="Automatically re-run qb_merge.py --force after patching "
             "front-matter.html, so QUESTION-BANK-BOOK.html ends up with "
             "the correct numbers baked in without a separate manual step."
    )
    args = ap.parse_args()

    if not MERGED_BOOK.exists():
        raise SystemExit(
            f"ERROR: {MERGED_BOOK} not found -- run qb_merge.py first (a "
            "first pass with blank ToC page numbers is expected and fine)."
        )
    if not FRONT_MATTER_FILE.exists():
        raise SystemExit(f"ERROR: {FRONT_MATTER_FILE} not found -- run "
                          "generate_qb_front_back_matter.py first.")

    target_ids = sorted(set(
        re.findall(r'data-target-id="([a-z0-9-]+)"',
                   FRONT_MATTER_FILE.read_text(encoding="utf-8"))
    ))
    if not target_ids:
        raise SystemExit(
            "ERROR: no data-target-id spans found in front-matter.html -- "
            "run generate_qb_toc.py first."
        )

    chrome_path = find_chrome()
    user_data_dir = Path(r"C:\temp\resolve-qb-toc-chrome-profile")
    proc = launch_chrome(chrome_path, user_data_dir)
    try:
        file_url = "file:///" + str(MERGED_BOOK.resolve()).replace("\\", "/")
        cdp = CDP(file_url)
        try:
            n_pages = wait_for_stable_pagination(cdp)
            print(f"Pagination stable at {n_pages} pages.")
            page_numbers = resolve_page_numbers(cdp, target_ids)
            for slug in target_ids:
                print(f"  {slug:28s} -> page {page_numbers[slug]}")
        finally:
            cdp.close()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()

    patch_front_matter(page_numbers)
    print(f"Patched: {FRONT_MATTER_FILE}")

    if args.remerge:
        merge_script = Path(__file__).resolve().parent / "qb_merge.py"
        print("Re-merging with corrected page numbers...")
        subprocess.run([sys.executable, str(merge_script), "--force"], check=True)


if __name__ == "__main__":
    main()
