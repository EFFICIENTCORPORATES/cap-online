#!/usr/bin/env python3
"""
telegram/tools/generate_dashboard.py -- static analytics snapshot (2026-08-10,
refactored same day dashboard_server.py was added)
--------------------------------------------------------------------------------
Queries the shared platform database (telegram/database/platform.db) and
telegram/config/bots.json via telegram/database/analytics.py (the ONE query
layer both this script and dashboard_server.py use -- see that module's own
docstring), and writes a single self-contained HTML file
(telegram/database/dashboard.html) via telegram/database/dashboard_html.py
(the ONE page template both surfaces render). Not a live server: re-run
this script to refresh the snapshot (it's cheap -- a few queries over a
local SQLite file).

Use this when you want an offline snapshot (e.g. to email/share a file) --
for a dashboard you leave open and click Refresh on, use
telegram/tools/dashboard_server.py instead (same look, same data, but live).

USAGE:
    python telegram/tools/generate_dashboard.py
    (then open telegram/database/dashboard.html)
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "telegram" / "database"))
import db as platform_db  # noqa: E402
import analytics  # noqa: E402
from dashboard_html import render_page  # noqa: E402

BOTS_PATH = REPO_ROOT / "telegram" / "config" / "bots.json"
OUT_PATH = REPO_ROOT / "telegram" / "database" / "dashboard.html"


def load_bots():
    import json
    return json.loads(BOTS_PATH.read_text(encoding="utf-8"))["bots"]


def main():
    conn = platform_db.get_connection()
    platform_db.init_schema(conn)

    bots = load_bots()
    data = analytics.fetch_all(conn, bots)

    html = render_page(data, live=False)
    OUT_PATH.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT_PATH} ({len(html):,} bytes)")
    print(f"Bots: {len(bots)} | Heartbeats recorded: {len(data['heartbeats'])} | "
          f"Days with activity: {len(data['daily'])} | Bots with usage: {len(data['summary'])}")


if __name__ == "__main__":
    main()
