"""
telegram/admin_portal/exporters.py -- shared export/pagination/filter
primitives (2026-08-11)
--------------------------------------------------------------------------------
Every analytics view AND the generic "Data Export" (any DB table) page
both build on these same few functions -- Pranav's ask: "pagination and
all filter criteria and capacity to download any tabular data to excel...
any analytics dashboard should be able to be downloaded as csv... and
also should be able to download as html or pdf on demand." One set of
primitives now, so every future module (Masters, Content, Leaderboards)
reuses them instead of rebuilding pagination/export per page.

Filtering/pagination here operate IN-MEMORY over already-fetched Python
lists (not a second SQL query with LIMIT/OFFSET/WHERE) -- deliberate:
every existing analytics.py function already returns its full result set
cheaply (this platform's real data volumes are dozens to low hundreds of
rows, not millions), and reusing those already-tested functions unchanged
is lower-risk than rewriting each one's query. Re-evaluate this choice if
a table ever grows large enough for it to matter.
"""

import csv
import io
import json
import sqlite3
from datetime import datetime, timezone

from flask import Response
from openpyxl import Workbook
from xhtml2pdf import pisa


# ---------------------------------------------------------------------------
# Pagination + free-text filtering over a list of dicts
# ---------------------------------------------------------------------------
def filter_rows(rows: list, query: str, fields: list) -> list:
    """Case-insensitive substring match across `fields` (dict keys) --
    same "one text box searches everything relevant" shape the old
    dashboard's Student Master filter already used, just factored out so
    every table can have one."""
    if not query:
        return rows
    q = query.strip().lower()
    if not q:
        return rows
    out = []
    for r in rows:
        haystack_parts = []
        for f in fields:
            v = r.get(f)
            if isinstance(v, (list, tuple)):
                haystack_parts.append(" ".join(str(x) for x in v))
            elif v is not None:
                haystack_parts.append(str(v))
        if q in " ".join(haystack_parts).lower():
            out.append(r)
    return out


def paginate(items: list, page: int, per_page: int = 25) -> dict:
    total = len(items)
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    end = start + per_page
    return {
        "items": items[start:end],
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages,
    }


# ---------------------------------------------------------------------------
# Tabular export -- CSV / XLSX / JSON, from either a raw sqlite3 cursor
# (whole-table export) or a plain list of dicts (a curated analytics view,
# already filtered).
# ---------------------------------------------------------------------------
def _safe_filename(name: str) -> str:
    return "".join(c if (c.isalnum() or c in "-_") else "_" for c in name)


def rows_from_cursor(cursor: sqlite3.Cursor) -> tuple:
    columns = [d[0] for d in cursor.description]
    rows = [list(r) for r in cursor.fetchall()]
    return columns, rows


def rows_from_dicts(dict_rows: list, columns: list = None) -> tuple:
    if not columns:
        columns = list(dict_rows[0].keys()) if dict_rows else []
    rows = [[r.get(c) for c in columns] for r in dict_rows]
    return columns, rows


def csv_response(columns: list, rows: list, filename: str) -> Response:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(columns)
    for row in rows:
        writer.writerow(["" if v is None else v for v in row])
    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{_safe_filename(filename)}.csv"'},
    )


def xlsx_response(columns: list, rows: list, filename: str) -> Response:
    wb = Workbook()
    ws = wb.active
    ws.title = filename[:31] or "Sheet1"   # Excel's own 31-char sheet-name limit
    ws.append(columns)
    for row in rows:
        ws.append(["" if v is None else v for v in row])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return Response(
        buf.getvalue(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{_safe_filename(filename)}.xlsx"'},
    )


def json_response(columns: list, rows: list, filename: str) -> Response:
    data = [dict(zip(columns, row)) for row in rows]
    return Response(
        json.dumps(data, indent=2, default=str, ensure_ascii=False),
        mimetype="application/json",
        headers={"Content-Disposition": f'attachment; filename="{_safe_filename(filename)}.json"'},
    )


# ---------------------------------------------------------------------------
# Printable snapshot -- shared HTML used for BOTH the "download as HTML"
# button (served as-is) and the "download as PDF" button (the SAME html
# run through xhtml2pdf) -- one content source, never two copies that
# could drift apart.
# ---------------------------------------------------------------------------
def render_printable_table(title: str, columns: list, rows: list, brand_colors: dict) -> str:
    """Table/inline-style markup only (no flexbox/grid) -- same xhtml2pdf-
    compatibility constraint documented in brand_kit.py/
    exam_hub_bot.py's html_to_pdf_bytes()."""
    navy, gold = brand_colors["navy"], brand_colors["gold"]
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    header_cells = "".join(f'<th style="text-align:left; padding:6px 8px; border-bottom:2px solid {navy}; font-size:11px;">{c}</th>' for c in columns)
    body_rows = ""
    for row in rows:
        cells = "".join(
            f'<td style="padding:5px 8px; border-bottom:1px solid #e2e2e2; font-size:11px;">{"" if v is None else v}</td>'
            for v in row
        )
        body_rows += f"<tr>{cells}</tr>"

    return f"""
<html><head><meta charset="utf-8"><title>{title}</title></head>
<body style="font-family:Arial,Helvetica,sans-serif; color:#222; margin:24px;">
  <div style="font-family:Georgia,'Times New Roman',serif; font-size:18px; font-weight:bold; color:{navy};">1LAVYA Admin Portal</div>
  <div style="font-size:10px; color:{gold}; text-transform:uppercase; margin-bottom:14px;">{title}</div>
  <div style="font-size:10px; color:#888; margin-bottom:14px;">Generated {generated_at} &middot; {len(rows)} row(s)</div>
  <table style="width:100%; border-collapse:collapse;">
    <thead><tr>{header_cells}</tr></thead>
    <tbody>{body_rows}</tbody>
  </table>
</body></html>
"""


def html_export_response(title: str, columns: list, rows: list, brand_colors: dict, filename: str) -> Response:
    html = render_printable_table(title, columns, rows, brand_colors)
    return Response(
        html, mimetype="text/html",
        headers={"Content-Disposition": f'attachment; filename="{_safe_filename(filename)}.html"'},
    )


def pdf_export_response(title: str, columns: list, rows: list, brand_colors: dict, filename: str) -> Response:
    html = render_printable_table(title, columns, rows, brand_colors)
    buf = io.BytesIO()
    pisa.CreatePDF(html, dest=buf)
    return Response(
        buf.getvalue(), mimetype="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{_safe_filename(filename)}.pdf"'},
    )
