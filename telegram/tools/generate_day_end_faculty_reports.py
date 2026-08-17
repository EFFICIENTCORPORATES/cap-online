#!/usr/bin/env python3
"""
telegram/tools/generate_day_end_faculty_reports.py -- nightly Day End
Faculty Report PDFs (2026-08-17)
--------------------------------------------------------------------------------
Pranav's ask: "make sure that these report can be obtained as 'DAY END
REPORT' everyday through my admin dashboard... since these are initial
report, please also additionally save pdf in a suitable folder... later on
we might not need this, but now we need a separate pdf as well."

Two halves to that ask:
  1. On-demand, via the dashboard: a "Day End (Today)" button on
     http://127.0.0.1:8788/reports/faculty (admin_portal/app.py) -- click
     it any time, get today's report fresh. No script needed for that half.
  2. THIS script -- the "also save a PDF to a folder" half. Run once daily
     (see SCHEDULING below), it generates every real faculty's Day End
     Report (today's UTC calendar day, level-wise, username-rolled-up --
     the exact same telegram/admin_portal/faculty_report.build_report()
     the dashboard button calls) and writes the PDF to disk under
     telegram/reports/day_end/{tenant_id}/{tenant_id}_{date}.pdf.

WHY A SEPARATE FOLDER ARCHIVE, NOT JUST THE DASHBOARD BUTTON: the dashboard
button is generate-on-click, nothing persists between clicks. Pranav
explicitly wants a standing, dated local record accumulating day by day
while the platform is new -- named "initial"/"later on we might not need
this" in his own words, so this is deliberately a plain folder of dated
PDFs, not a new database table or retention policy. Revisit/simplify once
Pranav confirms the archive is no longer needed.

ONLY REAL FACULTY TENANTS (kind=="faculty" -- capranav, csarunchouhan
today), via faculty_report.list_faculty_tenant_ids() -- "we have 2
faculties as of now" (Pranav's own framing). The platform-wide tenants
(1lavya-studyhub/1lavya-examhub) are deliberately NOT included here; a
report against the flagship shared pool is available on-demand from the
same dashboard page if ever wanted, just not part of this nightly archive.

SCHEDULING: a Windows Task Scheduler job, "1LAVYA Day End Faculty
Reports", daily at 23:50 local time -- 20 minutes after the leaderboard
broadcaster's 23:11 IST slot (telegram/bots/leaderboard_broadcaster.py),
comfortably before midnight so "today" (this script's own
faculty_report.today_utc_date(), a UTC calendar day) still means the same
day locally -- same reasoning leaderboard_broadcaster.py's own docstring
already gives for its 23:11 slot. Deliberately NOT registered in
bots.json/manage_bots.py -- a run-to-completion batch job, not a
long-running heartbeat process, same precedent as
telegram/tools/backup_to_cloudflare.py.

FAILURE HANDLING: one tenant's report failing (e.g. a transient PDF-
render error) is logged and does NOT stop the run for other tenants --
each tenant is wrapped in its own try/except. No DM-alerting is wired up
for this script (unlike backup_to_cloudflare.py) -- deliberately kept
simple, matching Pranav's own "initial, may not be needed later" framing;
add alerting later if this archive turns out to be load-bearing.

IDEMPOTENT: re-running on the same UTC day overwrites that day's PDF with
a freshly-generated one (more activity may have been logged since the
last run) -- never creates a second file for the same day.

USAGE:
    python telegram/tools/generate_day_end_faculty_reports.py
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parents[2]
TELEGRAM_ROOT = REPO_ROOT / "telegram"

sys.path.insert(0, str(TELEGRAM_ROOT / "database"))
sys.path.insert(0, str(TELEGRAM_ROOT / "tools"))  # document_catalog.py (admin_portal/) needs populate_course_catalog from here -- same sys.path shape as admin_portal/app.py
sys.path.insert(0, str(TELEGRAM_ROOT / "branding"))
sys.path.insert(0, str(TELEGRAM_ROOT / "admin_portal"))

import db  # noqa: E402
import faculty_report  # noqa: E402

BOTS_PATH = TELEGRAM_ROOT / "config" / "bots.json"
REPORTS_DIR = TELEGRAM_ROOT / "reports" / "day_end"

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger("generate_day_end_faculty_reports")


def load_bots() -> list:
    return json.loads(BOTS_PATH.read_text(encoding="utf-8"))["bots"]


def run_once():
    conn = db.get_connection()
    db.init_schema(conn)
    bots = load_bots()

    today = faculty_report.today_utc_date()
    tenant_ids = faculty_report.list_faculty_tenant_ids(conn, bots)
    logger.info(f"Day End Report run for {today} -- {len(tenant_ids)} faculty tenant(s): {tenant_ids}")

    saved, failed = [], []
    for tenant_id in tenant_ids:
        try:
            data = faculty_report.build_report(conn, tenant_id, bots, start_date=today, end_date=today)
            pdf_bytes = faculty_report.build_report_pdf(data)

            out_dir = REPORTS_DIR / tenant_id
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / f"{tenant_id}_{today}.pdf"
            out_path.write_bytes(pdf_bytes)

            rel_path = out_path.relative_to(REPO_ROOT)
            # faculty_report_deliveries.status is CHECK-constrained to
            # ('sent', 'failed', 'downloaded') (schema.sql) -- no 'saved'
            # value exists (found by this script's own first real run
            # failing loudly on the constraint, not assumed). 'downloaded'
            # is the closest correct fit: a PDF was produced and written
            # to disk, same as a manual "Download PDF" click, just
            # automatic -- delivered_to's own "local_file:{path}" prefix
            # is what actually distinguishes this from a real download.
            faculty_report.log_report_delivery(
                conn, tenant_id, data["range_label"], delivered_to=f"local_file:{rel_path}", status="downloaded",
            )
            saved.append(str(rel_path))
            logger.info(f"[{tenant_id}] saved -> {rel_path} ({len(pdf_bytes)} bytes, {len(data['levels'])} level(s))")
        except Exception as e:
            logger.exception(f"[{tenant_id}] Day End Report generation FAILED: {e}")
            try:
                faculty_report.log_report_delivery(conn, tenant_id, today, delivered_to="local_file", status="failed", error_detail=str(e))
            except Exception:
                pass  # logging the failure itself failing shouldn't crash the run for other tenants
            failed.append(tenant_id)

    logger.info(f"Day End Report run complete: {len(saved)} saved, {len(failed)} failed.")
    return saved, failed


def main():
    run_once()


if __name__ == "__main__":
    main()
