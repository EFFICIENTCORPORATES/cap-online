#!/usr/bin/env python3
"""
telegram/admin_portal/smoke_test_admin_portal.py -- Phase 4 foundation tier
smoke test (2026-08-11)
--------------------------------------------------------------------------------
Uses Flask's own test_client() (no real network socket, no real port) --
safe to re-run any time. The one place this WOULD touch a real system
(bot restart) is mocked (manage_bots.restart_bot patched to a no-op) so
this test never actually stops/starts a real bot process -- the real
restart path was already verified manually against real bots (see
telegram/admin_portal/README.md's "Verified" section); this test instead
proves the ROUTE logic (auth gating, audit logging, flash messages,
unknown-bot handling) is wired correctly, safely, repeatably.

USAGE:
    python telegram/admin_portal/smoke_test_admin_portal.py
"""

import sys
import re
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "database"))

import db as platform_db  # noqa: E402
import app as portal_app  # noqa: E402
import manage_bots  # noqa: E402
import analytics  # noqa: E402

REAL_USERNAME = "pranav"   # must match telegram/.env's ADMIN_PORTAL_USERNAME for the positive-login test to pass
FAKE_BOT_ID = "smoketest-nonexistent-bot"
SYNTHETIC_MARKER = "smoketest-admin-portal-marker"   # tags every DB row this test writes, for guaranteed cleanup

failures = []


def check(label: str, condition: bool, detail: str = ""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}" + (f" -- {detail}" if detail and not condition else ""))
    if not condition:
        failures.append(label)


def _cleanup_audit(conn):
    conn.execute("DELETE FROM admin_actions WHERE target=? OR target LIKE ?", (FAKE_BOT_ID, f"%{SYNTHETIC_MARKER}%"))
    conn.execute("DELETE FROM report_deliveries WHERE criteria LIKE ?", (f"%{SYNTHETIC_MARKER}%",))
    conn.execute("DELETE FROM mcq_issue_reports WHERE mcq_id LIKE ?", (f"%{SYNTHETIC_MARKER}%",))
    conn.execute("DELETE FROM faculty_report_deliveries WHERE delivered_to LIKE ?", (f"%{SYNTHETIC_MARKER}%",))
    conn.execute("DELETE FROM faculty_master WHERE notes LIKE ?", (f"%{SYNTHETIC_MARKER}%",))
    conn.commit()


def main():
    conn = platform_db.get_connection()
    platform_db.init_schema(conn)
    _cleanup_audit(conn)

    client = portal_app.app.test_client()

    print("\n--- Step 1: unauthenticated access is blocked ---")
    resp = client.get("/", follow_redirects=False)
    check("GET / unauthenticated redirects (not a real page)", resp.status_code == 302)
    check("redirect target is /login", "/login" in resp.headers.get("Location", ""))

    resp = client.get("/bots", follow_redirects=False)
    check("GET /bots unauthenticated redirects too", resp.status_code == 302)

    resp = client.post(f"/bots/{FAKE_BOT_ID}/restart", follow_redirects=False)
    check("POST .../restart unauthenticated redirects, does not execute", resp.status_code == 302)
    row = conn.execute("SELECT 1 FROM admin_actions WHERE target=?", (FAKE_BOT_ID,)).fetchone()
    check("no audit log entry was created for the unauthenticated attempt", row is None)

    print("\n--- Step 2: login rejects wrong credentials ---")
    resp = client.post("/login", data={"username": REAL_USERNAME, "password": "definitely-wrong-password"})
    check("wrong password does not redirect (stays on login page)", resp.status_code == 200)
    check("flashes an 'Invalid' message", b"Invalid" in resp.data)
    with client.session_transaction() as sess:
        check("session has no username after a failed login", "username" not in sess)

    print("\n--- Step 3: login accepts real credentials (from telegram/.env) ---")
    import os
    real_password_configured = bool(os.environ.get("ADMIN_PORTAL_PASSWORD_HASH"))
    if not real_password_configured:
        print("    (ADMIN_PORTAL_PASSWORD_HASH not set in this process's env -- "
              "skipping the real-login check; run via a shell that's loaded telegram/.env to cover this.)")
    else:
        # We don't have the real plaintext password here (only its hash is
        # in .env, by design -- see auth.py's own docstring) -- this step
        # only proves the LOGIN FORM/SESSION WIRING works for a request
        # that verify_credentials() would accept, by patching that one
        # function rather than needing the real plaintext in this script.
        with patch("app.auth.verify_credentials", return_value=True):
            resp = client.post("/login", data={"username": REAL_USERNAME, "password": "whatever"}, follow_redirects=False)
            check("correct credentials redirect away from /login", resp.status_code == 302 and "/login" not in resp.headers.get("Location", ""))
            with client.session_transaction() as sess:
                check("session has username set after successful login", sess.get("username") == REAL_USERNAME)
                check("session role is 'admin'", sess.get("role") == "admin")

    print("\n--- Step 4: authenticated pages render real data ---")
    resp = client.get("/")
    check("GET / (authenticated) returns 200", resp.status_code == 200)
    check("overview page shows the logged-in username", REAL_USERNAME.encode() in resp.data)

    resp = client.get("/bots")
    check("GET /bots (authenticated) returns 200", resp.status_code == 200)
    real_bot_ids = [b["bot_id"] for b in manage_bots.load_bots()]
    check("bots page lists every real configured bot_id",
          all(bid.encode() in resp.data for bid in real_bot_ids),
          f"missing: {[bid for bid in real_bot_ids if bid.encode() not in resp.data]}")

    print("\n--- Step 5: restart route -- unknown bot_id handled without crashing ---")
    resp = client.post(f"/bots/{FAKE_BOT_ID}/restart", follow_redirects=True)
    check("restarting an unknown bot_id does not crash (still 200 after redirect)", resp.status_code == 200)
    check("flashes an error mentioning the unknown bot_id", FAKE_BOT_ID.encode() in resp.data)
    row = conn.execute(
        "SELECT detail FROM admin_actions WHERE target=? ORDER BY action_id DESC LIMIT 1", (FAKE_BOT_ID,)
    ).fetchone()
    check("audit log recorded the failed attempt", row is not None and "unknown bot_id" in (row[0] or ""))

    print("\n--- Step 6: restart route -- real bot_id, restart_bot() MOCKED (no real process touched) ---")
    real_bot_id = real_bot_ids[0]
    with patch("app.manage_bots.restart_bot") as mock_restart:
        resp = client.post(f"/bots/{real_bot_id}/restart", follow_redirects=True)
        check("restart route returns 200 after redirect", resp.status_code == 200)
        check("manage_bots.restart_bot() was called exactly once", mock_restart.call_count == 1)
        called_bot = mock_restart.call_args[0][0]
        check("called with the correct bot dict", called_bot["bot_id"] == real_bot_id)
    row = conn.execute(
        "SELECT username, detail FROM admin_actions WHERE target=? ORDER BY action_id DESC LIMIT 1", (real_bot_id,)
    ).fetchone()
    check("audit log recorded the (mocked) successful restart", row is not None and row[1] == "ok")
    check("audit log recorded the correct username", row is not None and row[0] == REAL_USERNAME)

    print("\n--- Step 7: logs route ---")
    resp = client.get(f"/bots/{real_bot_id}/logs")
    check("GET .../logs (authenticated, real bot) returns 200", resp.status_code == 200)
    resp = client.get(f"/bots/{FAKE_BOT_ID}/logs")
    check("GET .../logs for an unknown bot_id returns 404, not a crash", resp.status_code == 404)

    print("\n--- Step 8: logout clears the session ---")
    client.get("/logout")
    resp = client.get("/", follow_redirects=False)
    check("GET / after logout redirects again (session cleared)", resp.status_code == 302)

    # Re-authenticate for the Analytics/export steps below.
    with patch("app.auth.verify_credentials", return_value=True):
        client.post("/login", data={"username": REAL_USERNAME, "password": "whatever"})

    print("\n--- Step 9: Data Export -- any table, json/csv/xlsx ---")
    resp = client.get("/export")
    check("GET /export (index) returns 200", resp.status_code == 200)
    check("export index lists a real table (students)", b"students" in resp.data)

    for fmt, min_bytes in (("json", 10), ("csv", 10), ("xlsx", 100)):
        resp = client.get(f"/export/students.{fmt}")
        check(f"GET /export/students.{fmt} returns 200", resp.status_code == 200)
        check(f".{fmt} export has real content", len(resp.data) > min_bytes)
        check(f".{fmt} export sets a download filename",
              "attachment" in resp.headers.get("Content-Disposition", ""))

    resp = client.get("/export/students.badformat")
    check("unsupported export format rejected with 400", resp.status_code == 400)
    resp = client.get(f"/export/{FAKE_BOT_ID}.csv")
    check("exporting an unknown table returns 404", resp.status_code == 404)

    print("\n--- Step 10: Analytics > Student Master -- view, filter, paginate, export ---")
    resp = client.get("/analytics/students")
    check("GET /analytics/students returns 200", resp.status_code == 200)
    resp = client.get("/analytics/students?q=zzz_no_such_student_zzz")
    check("filtering to a no-match query returns 200, not an error", resp.status_code == 200)
    check("no-match filter shows the empty-state message", b"No students match" in resp.data)
    resp = client.get("/analytics/students?page=1")
    check("explicit page=1 returns 200", resp.status_code == 200)

    for fmt in ("csv", "xlsx", "html", "pdf"):
        resp = client.get(f"/analytics/students.{fmt}")
        check(f"Student Master .{fmt} export returns 200", resp.status_code == 200)
        check(f"Student Master .{fmt} export has real content", len(resp.data) > 50)

    print("\n--- Step 11: bulk report send -- real DB rows, send_report_email() MOCKED ---")
    conn2 = platform_db.get_connection()
    with_email = conn2.execute("SELECT telegram_user_id FROM students WHERE email IS NOT NULL LIMIT 1").fetchone()
    without_email = conn2.execute("SELECT telegram_user_id FROM students WHERE email IS NULL LIMIT 1").fetchone()
    if not with_email or not without_email:
        print("    (need at least one student WITH and one WITHOUT a confirmed email in the real DB to "
              "fully exercise this step -- skipping, not a failure of the code itself.)")
    else:
        expected_email = conn2.execute("SELECT email FROM students WHERE telegram_user_id=?", (with_email[0],)).fetchone()[0]
        max_delivery_id_before = conn2.execute("SELECT COALESCE(MAX(delivery_id), 0) FROM report_deliveries").fetchone()[0]
        with patch("app.report_delivery.send_report_email") as mock_send:
            resp = client.post("/analytics/students/send-report", data={
                "telegram_user_id": [str(with_email[0]), str(without_email[0])],
            }, follow_redirects=True)
            check("send-report POST returns 200 after redirect", resp.status_code == 200)
            check("send_report_email() called exactly once (only the student WITH an email)", mock_send.call_count == 1)
            check("called with the admin portal's own bot_id (not impersonating a student-facing bot)",
                  mock_send.call_args[0][0] == "1lavya-admin-portal")
            check("called with that exact student's real confirmed email",
                  mock_send.call_args[0][1] == expected_email)
        m = re.search(r'flash flash-\w+">([^<]+)', resp.data.decode("utf-8", errors="replace"))
        check("flash message reports 1 sent, 1 skipped", bool(m) and "1 sent" in m.group(1) and "1 skipped" in m.group(1),
              m.group(1) if m else "no flash found")

        audit_row = conn2.execute(
            "SELECT username, detail FROM admin_actions WHERE action_type='bulk_report_send' ORDER BY action_id DESC LIMIT 1"
        ).fetchone()
        check("audit log recorded the bulk send", audit_row is not None)
        check("audit detail shows sent=1 failed=0 skipped=1", audit_row and audit_row[1] == "sent=1 failed=0 skipped=1")

        # Clean up ONLY the report_deliveries rows this test run just created
        # (identified precisely by delivery_id, not by a criteria string
        # match, since the real route doesn't take a test-only marker).
        conn2.execute("DELETE FROM report_deliveries WHERE delivery_id > ?", (max_delivery_id_before,))
        conn2.execute("DELETE FROM admin_actions WHERE action_type='bulk_report_send'")
        conn2.commit()

    print("\n--- Step 12: Analytics > Bot-wise Usage ---")
    resp = client.get("/analytics/bots")
    check("GET /analytics/bots returns 200", resp.status_code == 200)
    resp = client.get("/analytics/bots.csv")
    check("Bot-wise Usage .csv export returns 200", resp.status_code == 200)

    print("\n--- Step 13: Analytics > Faculty Report + chapter drill-down ---")
    faculty_bot_ids = [b["bot_id"] for b in manage_bots.load_bots() if b["kind"] in ("exam", "unified")]
    resp = client.get("/analytics/faculty-report")
    check("GET /analytics/faculty-report (default bot) returns 200", resp.status_code == 200)
    if faculty_bot_ids:
        target_bot = faculty_bot_ids[0]
        rows = analytics.fetch_faculty_report(conn2, [target_bot]).get(target_bot, [])
        resp = client.get(f"/analytics/faculty-report?bot_id={target_bot}")
        check(f"GET /analytics/faculty-report?bot_id={target_bot} returns 200", resp.status_code == 200)
        resp = client.get(f"/analytics/faculty-report.csv?bot_id={target_bot}")
        check("Faculty Report .csv export returns 200", resp.status_code == 200)
        resp = client.get("/analytics/faculty-report.csv")   # no bot_id
        check("Faculty Report export without bot_id returns 400, not a crash", resp.status_code == 400)
        if rows:
            uid = rows[0]["telegram_user_id"]
            resp = client.get(f"/analytics/faculty-report/{target_bot}/{uid}/chapters")
            check("chapter drill-down for a real student returns 200", resp.status_code == 200)
        resp = client.get(f"/analytics/faculty-report/{target_bot}/999999999999/chapters")
        check("chapter drill-down for an unknown student returns 404", resp.status_code == 404)

    print("\n--- Step 14: Analytics > Content Health + Email Analytics ---")
    resp = client.get("/analytics/content-health")
    check("GET /analytics/content-health returns 200", resp.status_code == 200)
    resp = client.get("/analytics/content-health.csv")
    check("Content Health .csv export returns 200", resp.status_code == 200)

    resp = client.get("/analytics/email")
    check("GET /analytics/email returns 200", resp.status_code == 200)
    resp = client.get("/analytics/email.csv")
    check("Email Analytics .csv export returns 200", resp.status_code == 200)

    print("\n--- Step 14a: Analytics > MCQ Issue Reports (2026-08-13) ---")
    synthetic_mcq_id = f"{SYNTHETIC_MARKER}-mcq-1"
    platform_db.log_mcq_issue_report(
        conn, bot_id="1lavya-examhub", telegram_user_id=999999003, mcq_id=synthetic_mcq_id,
        human_id="CA_L1_P01_C1_U1_00001", course="CA", level="Foundation", subject="Accounting",
        chapter_slug="test-slug", chapter_label="Test Chapter", category="wrong_answer",
        description="Smoke-test synthetic issue report",
    )
    resp = client.get("/analytics/issue-reports")
    check("GET /analytics/issue-reports returns 200", resp.status_code == 200)
    check("shows the synthetic report's human_id", b"CA_L1_P01_C1_U1_00001" in resp.data)
    check("shows the synthetic report's description", b"Smoke-test synthetic issue report" in resp.data)
    check("shows the category", b"wrong_answer" in resp.data)
    resp = client.get("/analytics/issue-reports.csv")
    check("MCQ Issue Reports .csv export returns 200", resp.status_code == 200)
    resp = client.get("/analytics/issue-reports.xlsx")
    check("MCQ Issue Reports .xlsx export returns 200", resp.status_code == 200)
    _cleanup_audit(conn)
    row = conn.execute("SELECT 1 FROM mcq_issue_reports WHERE mcq_id=?", (synthetic_mcq_id,)).fetchone()
    check("synthetic issue report cleaned up", row is None)

    print("\n--- Step 14b: Content > Course Catalog ---")
    resp = client.get("/content/course-catalog")
    check("GET /content/course-catalog (default course/level/subject) returns 200", resp.status_code == 200)
    check("default view is Study Materials", b"Study Materials" in resp.data)
    resp = client.get("/content/course-catalog?course=CMA&level=Intermediate&subject=Business+Laws+and+Ethics")
    check("GET /content/course-catalog with real CMA subject returns 200", resp.status_code == 200)
    resp = client.get("/content/course-catalog?course=CMA&level=Intermediate&subject=Business+Laws+and+Ethics&catalogue=taxonomy")
    check("Chapter Taxonomy tab still works (unchanged legacy view)", resp.status_code == 200)
    check("shows the real Companies Act chapter", b"Companies Act" in resp.data)
    resp = client.get("/content/course-catalog.csv?course=CA&level=Inter&subject=Advanced+Accounting")
    check("Course Catalog .csv export returns 200", resp.status_code == 200)
    resp = client.get("/content/course-catalog.csv")   # missing course/level/subject
    check("Course Catalog export without params returns 400, not a crash", resp.status_code == 400)

    print("\n--- Step 14c: the 4 new document/question catalogue tabs (2026-08-12) ---")
    for view in ("study", "exam", "revision", "questions"):
        resp = client.get(f"/content/course-catalog?course=CA&level=Inter&subject=Advanced+Accounting&catalogue={view}")
        check(f"catalogue={view} tab returns 200", resp.status_code == 200)
        resp = client.get(f"/content/course-catalog.csv?course=CA&level=Inter&subject=Advanced+Accounting&catalogue={view}")
        check(f"catalogue={view} .csv export returns 200", resp.status_code == 200)

    # Real regression case: the 3 "Other Laws" PDFs added 2026-08-12, and the
    # Module-4-chapter-number-restart fix that made them addressable at all
    # (see populate_course_catalog.py's CHAPTER_NO_MODULE_OFFSET).
    resp = client.get("/content/course-catalog?course=CA&level=Inter&subject=Corporate+and+Other+Laws&catalogue=study")
    check("Corporate and Other Laws Study Materials tab returns 200", resp.status_code == 200)
    check("all 15 real chapters present (12 Company Law + 3 Other Laws, no collision)",
          len(re.findall(rb"<td>C\d+</td>", resp.data)) == 15)
    check("Module 4's General Clauses Act chapter shows its real file, not 'missing'",
          b"General Clauses Act" in resp.data and b"Available" in resp.data)

    # Question Bank tab: real, non-zero counts for a subject with tagged content.
    resp = client.get("/content/course-catalog?course=CA&level=Inter&subject=Advanced+Accounting&catalogue=questions")
    check("Question Bank tab shows real (non-zero) MCQ/Descriptive counts, not all-zero placeholders",
          b">0<" in resp.data and any(str(n).encode() in resp.data for n in (146, 111, 257)))

    # Honest-empty states, not a crash or a fabricated row.
    resp = client.get("/content/course-catalog?course=CMA&level=Intermediate&subject=Business+Laws+and+Ethics&catalogue=exam")
    check("Exam Materials tab shows the honest 'not sourced yet' message for a course with no exam papers",
          b"No Exam Material has been sourced" in resp.data)
    resp = client.get("/content/course-catalog?course=CA&level=Inter&subject=Advanced+Accounting&catalogue=revision")
    check("Revision Material tab shows the honest 'not sourced yet' message (folder is genuinely empty)",
          b"No Revision Material has been sourced" in resp.data)

    # A subject name that doesn't exist at the requested level (Pranav's own
    # example URL: level=Inter&subject=Accounting, when the real CA Inter
    # subject is "Advanced Accounting") falls back to a real subject instead
    # of silently rendering an empty "No chapters match" table.
    resp = client.get("/content/course-catalog?course=CA&level=Inter&subject=Accounting&catalogue=study")
    check("An invalid subject falls back to a real one instead of an unexplained empty table",
          b"No chapters match" not in resp.data and b"Advanced Accounting" in resp.data)

    print("\n--- Step 14d: Overview rebuild -- 4 sub-tabs, date ranges, charts, exports (2026-08-13) ---")
    for tab in ("students", "content", "performance", "faculty"):
        resp = client.get(f"/?tab={tab}")
        check(f"Overview tab '{tab}' renders", resp.status_code == 200)
        check(f"Overview tab '{tab}' has no unrendered Jinja", b"{{" not in resp.data and b"{%" not in resp.data)

    resp = client.get("/?tab=students&preset=30d")
    check("Overview Students tab accepts a 30d preset", resp.status_code == 200 and b"Last 30 days" in resp.data)
    resp = client.get("/?tab=students&preset=all")
    check("Overview Students tab accepts the 'all time' preset", resp.status_code == 200 and b"All time" in resp.data)
    resp = client.get("/?tab=performance&perf_course=CA&perf_level=Inter&min_attempts=1")
    check("Overview Performance tab accepts course/level/min-attempts filters", resp.status_code == 200)

    for fmt, ctype_fragment in (("csv", "text/csv"), ("xlsx", "spreadsheetml"), ("html", "text/html"), ("pdf", "application/pdf")):
        for tab_export in ("students", "content", "performance", "faculty"):
            resp = client.get(f"/overview/{tab_export}.{fmt}")
            check(f"Overview {tab_export} export .{fmt} returns 200", resp.status_code == 200)
            check(f"Overview {tab_export} export .{fmt} has the right content-type", ctype_fragment in resp.headers.get("Content-Type", ""),
                  resp.headers.get("Content-Type"))

    for chart_id in ("students_daily", "content_daily", "content_split", "performance_daily", "faculty_interactions"):
        for fmt in ("html", "pdf"):
            resp = client.get(f"/overview/chart/{chart_id}.{fmt}")
            check(f"Chart export {chart_id}.{fmt} returns 200", resp.status_code == 200, f"got {resp.status_code}")
            check(f"Chart export {chart_id}.{fmt} is non-trivially sized", len(resp.data) > 500)
    resp = client.get("/overview/chart/not-a-real-chart.html")
    check("An unknown chart_id 404s instead of crashing", resp.status_code == 404)
    resp = client.get("/overview/chart/students_daily.svg")
    check("An unsupported export format 404s instead of crashing", resp.status_code == 404)

    # Data-correctness spot check: the Content tab's "New Questions Added"
    # stat and its underlying content_ingestion_log rows must agree with
    # what fetch_content_growth() itself reports -- proves the template
    # renders the SAME number the query layer computed, not a second
    # hand-derived one.
    growth = analytics.fetch_content_growth(conn)
    resp = client.get("/?tab=content&preset=all")
    check("Content tab's total-in-range figure matches fetch_content_growth()",
          str(growth["total_in_range"]).encode() in resp.data)

    print("\n--- Step 14e: Faculty Comprehensive Report (2026-08-14) ---")
    import faculty_report  # noqa: E402 -- telegram/admin_portal/faculty_report.py
    reportable = faculty_report.list_reportable_tenants(conn, manage_bots.load_bots())
    check("At least one reportable faculty/tenant exists", len(reportable) > 0)
    if reportable:
        sample_tenant = reportable[0]["tenant_id"]

        resp = client.get("/reports/faculty")
        check("GET /reports/faculty (no tenant selected yet) returns 200", resp.status_code == 200)

        resp = client.get(f"/reports/faculty?tenant_id={sample_tenant}")
        check(f"GET /reports/faculty?tenant_id={sample_tenant} returns 200", resp.status_code == 200)
        check(
            "Report page includes all 6 section headings",
            all(s.encode() in resp.data for s in (
                "Content Availability", "Chapter-wise Practice", "Student Performance",
                "Last 7 Days Activity", "Chapter Matrix", "Question-wise Difficulty",
            )),
        )

        resp = client.get(f"/reports/faculty/{sample_tenant}.pdf")
        check("Full report PDF export returns 200", resp.status_code == 200)
        check("Full report PDF has the right content-type", "application/pdf" in resp.headers.get("Content-Type", ""))
        check("Full report PDF is non-trivially sized", len(resp.data) > 500)

        resp = client.get(f"/reports/faculty/{sample_tenant}.xlsx")
        check("Full report XLSX export returns 200", resp.status_code == 200)
        check("Full report XLSX has the right content-type", "spreadsheetml" in resp.headers.get("Content-Type", ""))

        resp = client.get(f"/reports/faculty/{sample_tenant}.html")
        check("Full report HTML export returns 200", resp.status_code == 200)

        resp = client.get(f"/reports/faculty/{sample_tenant}.svg")
        check("An unsupported export format 400s instead of crashing", resp.status_code == 400)

        resp = client.get(f"/reports/faculty/{FAKE_BOT_ID}.pdf")
        check("An unknown tenant_id in the export route 404s instead of crashing", resp.status_code == 404)

        print("    --- email delivery: invalid address rejected, valid address sends (send_report_email MOCKED, no real network call) ---")
        resp = client.post(f"/reports/faculty/{sample_tenant}/email", data={"email": "not-an-email"}, follow_redirects=True)
        check("Invalid email address is rejected with a flash message, no send attempted", b"valid email" in resp.data)

        marker_email = f"{SYNTHETIC_MARKER}@example.com"
        with patch("app.faculty_report.send_report_email") as mock_send:
            resp = client.post(f"/reports/faculty/{sample_tenant}/email", data={"email": marker_email}, follow_redirects=True)
            check("Valid email triggers a 200 response after redirect", resp.status_code == 200)
            check("send_report_email() was called exactly once", mock_send.call_count == 1)
            check("send_report_email() was called with the typed email address", mock_send.call_args[0][0] == marker_email)
        row = conn.execute(
            "SELECT status FROM faculty_report_deliveries WHERE delivered_to=? ORDER BY delivery_id DESC LIMIT 1", (marker_email,),
        ).fetchone()
        check("A 'sent' delivery row was logged for the (mocked) successful email", row is not None and row[0] == "sent")

        print("    --- email delivery: send_report_email() FAILS (mocked) -> logged as 'failed', flashed, no crash ---")
        with patch("app.faculty_report.send_report_email", side_effect=RuntimeError("smoketest forced failure")):
            resp = client.post(f"/reports/faculty/{sample_tenant}/email", data={"email": marker_email}, follow_redirects=True)
            check("A failed send still returns 200 (flash, not a crash)", resp.status_code == 200)
            check("Failure is flashed to the admin", b"Failed to send report" in resp.data)
        row = conn.execute(
            "SELECT status, error_detail FROM faculty_report_deliveries WHERE delivered_to=? ORDER BY delivery_id DESC LIMIT 1", (marker_email,),
        ).fetchone()
        check("A 'failed' delivery row was logged with the error detail",
              row is not None and row[0] == "failed" and "forced failure" in (row[1] or ""))

    print("\n--- Step 14f: Faculty Master DB table (Masters > Faculty Details, 2026-08-14) ---")
    import faculty_master  # noqa: E402 -- telegram/admin_portal/faculty_master.py
    resp = client.get("/masters/faculty")
    check("GET /masters/faculty returns 200", resp.status_code == 200)
    check("Faculty Details list shows every real tenant",
          all(tid.encode() in resp.data for tid in faculty_master.load_tenants().keys()))

    resp = client.get(f"/masters/faculty/{sample_tenant}")
    check(f"GET /masters/faculty/{sample_tenant} (edit form) returns 200", resp.status_code == 200)

    resp = client.get(f"/masters/faculty/{FAKE_BOT_ID}")
    check("GET /masters/faculty/<unknown tenant_id> returns 404, not a crash", resp.status_code == 404)

    # This route can hold REAL admin-entered data by the time this test runs
    # again -- capture whatever's there now so it can be restored exactly,
    # rather than losing it just because this step exercised the save path.
    original_master_row = faculty_master.get_faculty_master(conn, sample_tenant)

    marker_notes = f"synthetic test row -- {SYNTHETIC_MARKER}"
    resp = client.post(f"/masters/faculty/{sample_tenant}", data={
        "contact_email": "smoketest@example.com", "contact_phone": "+91 90000 00000", "notes": marker_notes,
    }, follow_redirects=True)
    check("POST /masters/faculty/<tenant_id> (save) returns 200 after redirect", resp.status_code == 200)
    check("Save is flashed to the admin", b"Saved details" in resp.data)
    row = faculty_master.get_faculty_master(conn, sample_tenant)
    check("Row reflects the submitted values",
          row is not None and row["contact_email"] == "smoketest@example.com" and row["notes"] == marker_notes)

    resp = client.post(f"/masters/faculty/{sample_tenant}", data={
        "contact_email": "smoketest2@example.com", "contact_phone": "", "notes": marker_notes,
    }, follow_redirects=True)
    check("POST /masters/faculty/<tenant_id> (a second save) returns 200 after redirect", resp.status_code == 200)
    row2 = faculty_master.get_faculty_master(conn, sample_tenant)
    check("A second save UPDATES the same row (email changed), no duplicate (tenant_id is the PK)",
          row2 is not None and row2["contact_email"] == "smoketest2@example.com")
    check("An empty field submitted on save clears that column", row2 is not None and row2["contact_phone"] is None)

    resp = client.get(f"/reports/faculty?tenant_id={sample_tenant}")
    check("Faculty Comprehensive Report's email box now pre-fills from the saved faculty_master row",
          b"smoketest2@example.com" in resp.data)

    # Restore exactly what was there before this step touched it -- delete
    # if nothing existed, or write the original field values back (via the
    # same upsert function the route itself uses) if something real did.
    if original_master_row is None:
        conn.execute("DELETE FROM faculty_master WHERE tenant_id=?", (sample_tenant,))
        conn.commit()
        restored_ok = faculty_master.get_faculty_master(conn, sample_tenant) is None
    else:
        faculty_master.upsert_faculty_master(
            conn, sample_tenant, original_master_row["contact_email"],
            original_master_row["contact_phone"], original_master_row["notes"],
        )
        restored = faculty_master.get_faculty_master(conn, sample_tenant)
        restored_ok = (restored is not None
                       and restored["contact_email"] == original_master_row["contact_email"]
                       and restored["contact_phone"] == original_master_row["contact_phone"]
                       and restored["notes"] == original_master_row["notes"])
    check("faculty_master row for the sample tenant was restored/cleaned up correctly (no test residue, no data loss)", restored_ok)

    print("\n--- Step 15: every new export/analytics route requires auth ---")
    client.get("/logout")
    for path in ("/export", "/export/students.csv", "/analytics/students", "/analytics/students.csv",
                 "/analytics/bots", "/analytics/faculty-report", "/analytics/content-health", "/analytics/email",
                 "/analytics/issue-reports", "/content/course-catalog",
                 "/overview/students.csv", "/overview/content.csv", "/overview/performance.csv", "/overview/faculty.csv",
                 "/overview/chart/students_daily.html", "/overview/chart/students_daily.pdf",
                 "/reports/faculty", f"/reports/faculty/{FAKE_BOT_ID}.pdf",
                 "/masters/faculty", f"/masters/faculty/{FAKE_BOT_ID}"):
        resp = client.get(path, follow_redirects=False)
        check(f"GET {path} unauthenticated redirects (not served directly)", resp.status_code == 302, f"got {resp.status_code}")
    resp = client.post("/analytics/students/send-report", data={"telegram_user_id": ["1"]}, follow_redirects=False)
    check("POST send-report unauthenticated redirects, does not execute", resp.status_code == 302)
    resp = client.post(f"/reports/faculty/{FAKE_BOT_ID}/email", data={"email": "x@example.com"}, follow_redirects=False)
    check("POST .../faculty/<tenant_id>/email unauthenticated redirects, does not execute", resp.status_code == 302)
    resp = client.post(f"/masters/faculty/{FAKE_BOT_ID}", data={"contact_email": "x@example.com"}, follow_redirects=False)
    check("POST /masters/faculty/<tenant_id> unauthenticated redirects, does not execute", resp.status_code == 302)

    print(f"\n{'='*70}")
    if failures:
        print(f"{len(failures)} check(s) FAILED:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("All checks passed.")


if __name__ == "__main__":
    try:
        main()
    finally:
        conn = platform_db.get_connection()
        _cleanup_audit(conn)
        print("(cleanup done -- synthetic audit rows removed)")
