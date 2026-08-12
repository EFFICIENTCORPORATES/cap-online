#!/usr/bin/env python3
"""
telegram/tools/generate_student_report.py -- branded student performance
report, HTML->PDF (2026-08-11, Phase 2 of the branding-kit -> report-
pipeline -> leaderboard -> admin-portal roadmap)
--------------------------------------------------------------------------------
Takes a telegram_user_id (chat_id), queries telegram/database/
student_analytics.py for that student's platform-wide practice data, and
renders a branded (telegram/branding/brand_kit.py) PDF report -- the exact
"python script that takes a CHAT ID and queries the DB for a report" from
Pranav's original ask.

Importable (telegram/bots/report_flow.py calls build_report_pdf() directly
to attach the PDF to a Telegram message) AND a standalone CLI for manual/
admin use:

    python telegram/tools/generate_student_report.py 5777734732
    python telegram/tools/generate_student_report.py 5777734732 --last-n 100
    python telegram/tools/generate_student_report.py 5777734732 --since 2026-08-01
    python telegram/tools/generate_student_report.py 5777734732 --out my_report.pdf

Same cross-engine-safe markup discipline as brand_kit.py (table/inline-
style only, no flexbox/grid/gradients/em-units) -- this renders through
xhtml2pdf/reportlab, the same real-world-proven engine
exam_hub_bot.py's html_to_pdf_bytes() already uses.
"""

import io
import sys
import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "telegram" / "database"))
sys.path.insert(0, str(REPO_ROOT / "telegram" / "branding"))
import db as platform_db  # noqa: E402
import student_analytics  # noqa: E402
import brand_kit  # noqa: E402

from xhtml2pdf import pisa  # noqa: E402


def format_duration(total_seconds) -> str:
    if total_seconds is None:
        return "N/A"
    total_seconds = int(total_seconds)
    h, rem = divmod(total_seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m}m"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


def format_pct(pct) -> str:
    return "N/A" if pct is None else f"{pct}%"


def display_name_for_student(data: dict) -> str:
    name = " ".join(p for p in (data.get("first_name"), data.get("last_name")) if p).strip()
    return name or data.get("username") or f"Student {data['telegram_user_id']}"


def _stat_tile_row(c: dict, cells: list) -> str:
    """One row of simple bordered stat cells -- xhtml2pdf-safe (a table,
    not the dashboard's CSS-grid stat-tiles, which don't have to survive a
    PDF engine)."""
    tds = "".join(
        f'<td style="width:{100//len(cells)}%; padding:12px; border:1px solid {c["navy_tint"]}; text-align:center;">'
        f'<div style="font-size:10px; color:{c["ink"]}; text-transform:uppercase; opacity:0.65;">{label}</div>'
        f'<div style="font-size:20px; font-weight:bold; color:{c["navy"]}; margin-top:4px;">{value}</div>'
        f'</td>'
        for label, value in cells
    )
    return f'<table style="width:100%; border-collapse:collapse; margin-bottom:20px;"><tr>{tds}</tr></table>'


def render_report_html(data: dict) -> str:
    c = brand_kit.colors()
    display_name = display_name_for_student(data)
    t = data["totals"]

    stat_row_1 = _stat_tile_row(c, [
        ("MCQs Answered", f"{t['mcq_answered']} / {t['mcq_shown']}"),
        ("Accuracy", format_pct(t["mcq_accuracy_pct"])),
        ("Avg Time / Question", format_duration(t["avg_seconds_per_mcq"])),
        ("Time on Bot", format_duration(t["total_time_on_bot_seconds"])),
    ])
    stat_row_2 = _stat_tile_row(c, [
        ("Descriptive Questions Viewed", t["descriptive_shown"]),
        ("Practice Sessions", f"{t['sessions_with_activity']} / {t['total_sessions']}"),
    ])

    chapter_rows = "".join(
        f'<tr>'
        f'<td style="padding:6px 8px; border-bottom:1px solid {c["navy_tint"]};">{ch["chapter_label"]}</td>'
        f'<td style="padding:6px 8px; border-bottom:1px solid {c["navy_tint"]}; text-align:center;">{ch["mcq_shown"]}</td>'
        f'<td style="padding:6px 8px; border-bottom:1px solid {c["navy_tint"]}; text-align:center;">{ch["mcq_answered"]}</td>'
        f'<td style="padding:6px 8px; border-bottom:1px solid {c["navy_tint"]}; text-align:center;">{ch["mcq_correct"]}</td>'
        f'<td style="padding:6px 8px; border-bottom:1px solid {c["navy_tint"]}; text-align:center;">{format_pct(ch["accuracy_pct"])}</td>'
        f'<td style="padding:6px 8px; border-bottom:1px solid {c["navy_tint"]}; text-align:center;">{ch["descriptive_shown"]}</td>'
        f'</tr>'
        for ch in data["by_chapter"]
    ) or f'<tr><td colspan="6" style="padding:12px; color:#888; text-align:center;">No questions practiced in this period.</td></tr>'

    date_range = data["date_range"]
    date_range_line = (
        f"{date_range['first_activity'][:10]} to {date_range['last_activity'][:10]}"
        if date_range["first_activity"] else "No activity recorded yet"
    )

    return f"""<html><head><meta charset="utf-8"><style>
body {{ font-family: Helvetica, Arial, sans-serif; font-size: 12px; color: {c['ink']}; }}
h2 {{ color: {c['navy']}; font-size: 16px; margin: 24px 0 8px; }}
table.chapter-table th {{ text-align: left; color: {c['ink']}; opacity: 0.65; font-size: 10px; text-transform: uppercase; padding: 6px 8px; border-bottom: 2px solid {c['navy']}; }}
</style></head><body>
{brand_kit.render_header_html("Performance Report", data["criteria_label"])}

<p style="font-size:14px; font-weight:bold; color:{c['navy']};">{display_name}</p>
<p style="font-size:11px; color:#666;">Activity period covered: {date_range_line} &nbsp;|&nbsp; Report generated: {data['generated_at'][:19].replace('T', ' ')} UTC</p>

<h2>Overview</h2>
{stat_row_1}
{stat_row_2}

<h2>Chapter-wise Breakdown</h2>
<table class="chapter-table" style="width:100%; border-collapse:collapse;">
<thead><tr>
<th>Chapter</th><th style="text-align:center;">MCQs Shown</th><th style="text-align:center;">Answered</th>
<th style="text-align:center;">Correct</th><th style="text-align:center;">Accuracy</th><th style="text-align:center;">Descriptive Viewed</th>
</tr></thead>
<tbody>{chapter_rows}</tbody>
</table>

<p style="font-size:10px; color:#999; margin-top:24px;">
"Time on Bot" reflects actual recorded practice activity per session, not wall-clock time between your first and last message --
idle gaps between sessions are never counted as practice time. "Avg Time / Question" is capped per-question at 30 minutes so a
single abandoned-then-resumed question doesn't skew your average.
</p>

{brand_kit.render_footer_html()}
</body></html>"""


def build_report_pdf(conn, telegram_user_id: int, since: str = None, last_n: int = None) -> bytes:
    """The one function both the CLI below and telegram/bots/report_flow.py
    call. Returns raw PDF bytes -- never writes a file itself, callers
    decide where the bytes go (disk, an email attachment, a Telegram
    document upload)."""
    data = student_analytics.fetch_student_report_data(conn, telegram_user_id, since=since, last_n=last_n)
    html = render_report_html(data)
    buffer = io.BytesIO()
    result = pisa.CreatePDF(html, dest=buffer)
    if result.err:
        raise RuntimeError(f"PDF generation failed with {result.err} error(s) for telegram_user_id={telegram_user_id}")
    return buffer.getvalue()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("telegram_user_id", type=int)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--since", type=str, help="ISO date, e.g. 2026-08-01")
    group.add_argument("--last-n", type=int, help="Scope to the most recent N MCQ questions")
    parser.add_argument("--out", type=Path, default=None, help="Output PDF path (default: report_<chat_id>.pdf)")
    args = parser.parse_args()

    conn = platform_db.get_connection()
    platform_db.init_schema(conn)

    pdf_bytes = build_report_pdf(conn, args.telegram_user_id, since=args.since, last_n=args.last_n)
    out_path = args.out or Path(f"report_{args.telegram_user_id}.pdf")
    out_path.write_bytes(pdf_bytes)
    print(f"Wrote {out_path} ({len(pdf_bytes):,} bytes)")


if __name__ == "__main__":
    main()
