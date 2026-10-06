"""Verify a Must Practice unit on the LIVE site, the way a student uses it.

    python tools/verify_must_practice_live.py M2-C5-U4          # one unit
    python tools/verify_must_practice_live.py                   # every published unit
    python tools/verify_must_practice_live.py --base http://127.0.0.1:8787   # local `wrangler dev`

Needs ``pip install playwright`` and Microsoft Edge (same as ``qa_smoke.py --browser``).
A real browser is required: bulk data files go through the Worker's bot protection
(BOT-PROTECTION.md), so bare curl/wget get 403 by design and prove nothing.

Per unit it checks: the unit is in the picker and not marked "coming soon"; it has exactly
ten question rows; every row expands and its "Show answer" reveals a non-empty answer;
every row has a traced Question Bank page; no console errors, no 4xx/5xx responses; no
horizontal overflow at 1280 px or 390 px. Exits 1 on any failure.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "public/practice-with-pranav-bhaiya/must-practice/data"
PAGE = "/practice-with-pranav-bhaiya/must-practice/"
EXPECTED = 10


def published_units() -> list[str]:
    index = json.loads((DATA / "index.json").read_text(encoding="utf-8"))
    return [
        u["unit_id"]
        for m in index["modules"] for c in m["chapters"] for u in c["units"] if u["published"]
    ]


def locate(index: dict, unit_id: str) -> tuple[str, str]:
    for m in index["modules"]:
        for c in m["chapters"]:
            if any(u["unit_id"] == unit_id for u in c["units"]):
                return m["module"], c["chapter"]
    raise SystemExit(f"{unit_id} is not in index.json")


def check_unit(pg, base: str, unit_id: str, errors: list, bad: list) -> list[str]:
    problems: list[str] = []
    index = json.loads((DATA / "index.json").read_text(encoding="utf-8"))
    module, chapter = locate(index, unit_id)
    pg.set_viewport_size({"width": 1280, "height": 900})
    pg.goto(base + PAGE, wait_until="networkidle")
    pg.select_option("#module-select", module)
    pg.select_option("#chapter-select", chapter)
    label = pg.eval_on_selector(f'#unit-select option[value="{unit_id}"]', "o => o.textContent")
    if "coming soon" in label.lower():
        problems.append(f"picker still says coming soon: {label!r}")
    pg.select_option("#unit-select", unit_id)
    pg.wait_for_selector("#q-body tr.q-row", timeout=15000)
    pg.wait_for_timeout(800)

    rows = pg.locator("#q-body tr.q-row")
    n = rows.count()
    if n != EXPECTED:
        problems.append(f"{n} question rows, expected {EXPECTED}")
    for i in range(n):
        rows.nth(i).click()  # the answer button lives in a detail row hidden until the row is clicked
        detail = pg.locator("#q-body tr.detail-row").nth(i)
        detail.locator("button.show-answer").click()
        question = detail.locator(".qtext").inner_text().strip()
        answer = detail.locator(".atext").inner_text().strip()
        page_cell = rows.nth(i).locator(".col-page").inner_text()
        if not detail.locator(".answer").is_visible() or len(answer) < 100:
            problems.append(f"row {i + 1}: answer missing or too short ({len(answer)} chars)")
        if len(question) < 20:
            problems.append(f"row {i + 1}: question missing or too short ({len(question)} chars)")
        if "not traced" in page_cell:
            problems.append(f"row {i + 1}: no Question Bank page number")
    for width in (1280, 390):
        pg.set_viewport_size({"width": width, "height": 800})
        pg.wait_for_timeout(300)
        if not pg.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth"):
            problems.append(f"horizontal overflow at {width}px")
    print(f"{unit_id}: {n} rows, {len(problems)} problem(s)")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("unit", nargs="?", help="unit id such as M2-C5-U4; default = every published unit")
    ap.add_argument("--base", default="https://capranav.com")
    args = ap.parse_args()
    units = [args.unit] if args.unit else published_units()

    failed = False
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge")
        pg = browser.new_page()
        errors: list[str] = []
        bad: list[tuple[int, str]] = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.on("response", lambda r: bad.append((r.status, r.url)) if r.status >= 400 else None)
        for unit_id in units:
            for problem in check_unit(pg, args.base, unit_id, errors, bad):
                failed = True
                print(f"  FAIL {problem}")
        if errors:
            failed = True
            print("  FAIL console errors:", errors)
        if bad:
            failed = True
            print("  FAIL http errors:", bad)
        browser.close()
    print("ALL PASSED" if not failed else "FAILED")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
