"""
telegram/bots/smoke_test_sales_agent_bot.py -- permanent regression checks for
sales_agent_bot.py (2026-08-24), same discipline as this platform's other
smoke_test_*.py scripts: no mocked Telegram network calls, but every other layer
(catalog loading, search ranking, card rendering, callback_data safety, the
per-client sqlite log) is exercised for real, against the real coceducation
catalog, with any DB rows this script inserts cleaned up even on failure.

Run: .venv/Scripts/python telegram/bots/smoke_test_sales_agent_bot.py
"""

from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

os.environ.setdefault("SALES_AGENT_CLIENT", "coceducation")
sys.path.insert(0, str(Path(__file__).resolve().parent))

import sales_agent_bot as m  # noqa: E402

CHECKS_PASSED = 0
CHECKS_FAILED = 0


def check(label: str, condition: bool) -> None:
    global CHECKS_PASSED, CHECKS_FAILED
    if condition:
        CHECKS_PASSED += 1
        print(f"  OK   {label}")
    else:
        CHECKS_FAILED += 1
        print(f"  FAIL {label}")


def main() -> int:
    print(f"=== smoke_test_sales_agent_bot (client={m.CLIENT_SLUG}) ===")

    # 1. Catalog loaded with real content, not an empty/broken parse.
    check("catalog has courses", len(m.COURSES) > 100)
    check("every course has a title", all(c["title"] for c in m.COURSES))
    check("every course has a real coceducation.com URL", all(c["url"].startswith(m.ORG["domain"]) for c in m.COURSES))
    check("every course has a non-negative price", all((c["price_inr"] or 0) >= 0 for c in m.COURSES))
    check("exam_group is always one of the known groups", all(c["exam_group"] in {"CA", "CMA", "CFM", "Other"} for c in m.COURSES))

    # 2. callback_data never exceeds Telegram's 64-byte limit, across every
    #    course index and every browse page -- this exact bug class has broken
    #    other bots on this platform before (see CLAUDE.md's callback-data
    #    history), so this is a permanent regression guard, not a one-off check.
    max_course_cb = max(len(f"course:{i}".encode()) for i in range(len(m.COURSES)))
    check("course: callback_data max 64 bytes", max_course_cb <= 64)

    for group in {"CA", "CMA", "CFM", "Other"}:
        count = sum(1 for c in m.COURSES if c["exam_group"] == group)
        max_page = max(0, (count - 1) // m.PAGE_SIZE)
        max_list_cb = len(f"list:{group}:{max_page}".encode())
        check(f"list:{group}:<page> callback_data max 64 bytes", max_list_cb <= 64)

    # 3. Search returns real, relevant results.
    results = m.search_courses("Santosh Kumar accounting")
    check("search returns results for a known faculty+subject", len(results) > 0)
    check("top search result mentions the faculty or subject", any(
        "santosh" in c["title"].lower() or "accounting" in c["title"].lower()
        for _idx, c, _score in results[:3]
    ))

    empty_results = m.search_courses("zzzzzznonexistentcoursequery9999")
    check("nonsense query returns no results (score floor works)", len(empty_results) == 0)

    # 4. Course card rendering never crashes and includes the price + a buy link.
    sample = m.COURSES[0]
    card_text = m.format_course_card(sample)
    check("card includes course title", sample["title"] in card_text)
    keyboard = m.course_detail_keyboard(sample)
    buy_button = keyboard.inline_keyboard[0][0]
    check("card has a real Buy Now URL button", buy_button.url == sample["url"])

    # 5. DB logging works and is this client's OWN file, not the shared platform.db.
    check("DB path is inside this client's own folder", m.DB_PATH.parent.name == m.CLIENT_SLUG)
    m.init_db()
    test_user_id = -999999  # negative, out of Telegram's real user-id range -- unambiguous test marker
    try:
        m.log_event(test_user_id, "start")
        m.log_event(test_user_id, "search", query_text="smoke test query")
        m.log_event(test_user_id, "course_view", course_slug=sample["slug"])

        conn = sqlite3.connect(m.DB_PATH)
        try:
            rows = conn.execute(
                "SELECT event_type, query_text, course_slug FROM sales_agent_events WHERE telegram_user_id = ?",
                (test_user_id,),
            ).fetchall()
        finally:
            conn.close()
        check("all 3 logged events round-tripped", len(rows) == 3)
        check("course_view row recorded the right slug", any(r[2] == sample["slug"] for r in rows))
    finally:
        conn = sqlite3.connect(m.DB_PATH)
        try:
            conn.execute("DELETE FROM sales_agent_events WHERE telegram_user_id = ?", (test_user_id,))
            conn.commit()
        finally:
            conn.close()

    conn = sqlite3.connect(m.DB_PATH)
    try:
        leftover = conn.execute(
            "SELECT COUNT(*) FROM sales_agent_events WHERE telegram_user_id = ?", (test_user_id,)
        ).fetchone()[0]
    finally:
        conn.close()
    check("no residue left in the DB after cleanup", leftover == 0)

    print(f"\n{CHECKS_PASSED} passed, {CHECKS_FAILED} failed")
    return 1 if CHECKS_FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
