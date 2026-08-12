#!/usr/bin/env python3
"""
telegram/tools/dashboard_server.py -- LIVE analytics dashboard (2026-08-10)
--------------------------------------------------------------------------------
Pranav's ask, verbatim: "The dashboard should have a refresh button which
will make the necessary query and get the latest Bot Progress and the
Analytics part as well." A static file (telegram/tools/generate_dashboard.py)
can't do that -- there's nothing for a browser to fetch from once the file
is on disk. This is the same dashboard (same page template, same query
layer -- see telegram/database/dashboard_html.py / analytics.py, the two
modules both this script and the static generator share), served by a tiny
local HTTP server instead of written to a file, so the page's Refresh
button has something to call.

Local only, by design -- matches the platform's existing "stay on local
server for now" decision (memory: 1lavya-bot-infra-plan). Nothing here is
exposed to the internet; binds to 127.0.0.1.

ENDPOINTS:
    GET /            -- the dashboard page (live=True: has the Refresh button)
    GET /api/data    -- the same JSON analytics.fetch_all() returns, fresh
                         on every call (no caching -- SQLite reads are cheap
                         enough locally that there's no reason to)

USAGE:
    python telegram/tools/dashboard_server.py
    (then open http://127.0.0.1:8787/  -- Ctrl+C to stop)

    Set DASHBOARD_PORT to use a different port.

This can also run as a managed, always-on process alongside every bot --
see telegram/config/bots.json's "1lavya-dashboard" entry (kind: "dashboard")
and telegram/tools/manage_bots.py, which starts/stops it the same way as
every other bot (it just doesn't hold a Telegram token, since it never
talks to Telegram).
"""

import os
import sys
import json
import logging
import threading
import time
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "telegram" / "database"))
import db as platform_db  # noqa: E402
import analytics  # noqa: E402
from dashboard_html import render_page  # noqa: E402

BOTS_PATH = REPO_ROOT / "telegram" / "config" / "bots.json"
PORT = int(os.environ.get("DASHBOARD_PORT", "8787"))
HOST = "127.0.0.1"   # local only -- see module docstring

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger("dashboard_server")


def load_bots():
    return json.loads(BOTS_PATH.read_text(encoding="utf-8"))["bots"]


class Handler(BaseHTTPRequestHandler):
    # One connection per request/response cycle -- see db.get_connection()'s
    # own docstring on why bot scripts open one connection at startup and
    # reuse it; this server does the same instead of opening a fresh
    # sqlite3.connect() per request, since ThreadingHTTPServer serves
    # concurrent requests on separate threads and sqlite3 connections aren't
    # meant to be shared across threads without check_same_thread=False
    # (which get_connection() already sets).
    def _conn(self):
        conn = platform_db.get_connection()
        platform_db.init_schema(conn)
        return conn

    def _send_json(self, obj: dict, status: int = 200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")   # always fresh -- see module docstring
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html: str):
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        try:
            if self.path == "/" or self.path == "":
                conn = self._conn()
                bots = load_bots()
                data = analytics.fetch_all(conn, bots)
                self._send_html(render_page(data, live=True))
            elif self.path == "/api/data":
                conn = self._conn()
                bots = load_bots()
                data = analytics.fetch_all(conn, bots)
                self._send_json(data)
            else:
                self._send_json({"error": "not found"}, status=404)
        except Exception as e:
            logger.exception("Request failed")
            self._send_json({"error": str(e)}, status=500)

    def log_message(self, fmt, *args):
        logger.info("%s - %s", self.address_string(), fmt % args)


DASHBOARD_BOT_ID = "1lavya-dashboard"   # must match telegram/config/bots.json's own entry


def _heartbeat_loop(interval_seconds: int = 120):
    """This process has no python-telegram-bot Application/JobQueue (it's a
    plain HTTP server, not a Telegram bot) -- db.py's schedule_heartbeat()
    needs one, so this is the same idea on a plain background thread
    instead. Without this, the dashboard would show every other bot's
    online/offline status but never its own -- and telegram/bots/
    watcher_bot.py couldn't tell if the dashboard itself ever goes down."""
    conn = platform_db.get_connection()
    platform_db.init_schema(conn)
    pid = os.getpid()
    started_at = platform_db.now()
    while True:
        platform_db.send_heartbeat(conn, DASHBOARD_BOT_ID, pid, started_at)
        time.sleep(interval_seconds)


def main():
    threading.Thread(target=_heartbeat_loop, daemon=True).start()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    logger.info(f"Dashboard live at http://{HOST}:{PORT}/  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Stopping.")
        server.shutdown()


if __name__ == "__main__":
    main()
