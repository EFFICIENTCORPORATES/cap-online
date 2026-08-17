"""
telegram/admin_portal/charts.py -- self-built, dependency-free inline SVG
chart generation for the Admin Portal (2026-08-13, Overview rebuild)
--------------------------------------------------------------------------------
Pranav's ask included "best display and analytics" with downloadable
graphs. Confirmed with him before building (AskUserQuestion, 2026-08-13):
self-built inline SVG, no new JS charting library -- consistent with this
repo's existing "self-contained, no external dependency, no CDN calls"
practice (see the Artifact-publishing rules this session already follows,
and CLAUDE.md section 7's "vendor fonts locally, never @import a network
CDN" principle applied to charts instead of fonts).

Every function here returns a plain SVG markup STRING (no <html> wrapper),
meant to be embedded directly into a Jinja template via `{{ svg | safe }}`.
SVG renders natively in every browser -- both on-screen and in the
"download as HTML" export (see exporters.py's chart_html_response()).

PDF export is a SEPARATE code path (charts_pdf.py, reportlab-native
drawing) rather than trying to rasterize this SVG -- xhtml2pdf/reportlab
(the PDF engine every other export in this app already uses) has no
reliable inline-<svg> support, a real gap found and worked around here
rather than discovered as a bug later (same "check the actual rendered
output" discipline CLAUDE.md's branding-kit entry already learned once
this session, on a different rendering gap).
"""

from __future__ import annotations

from html import escape


def _fmt(v) -> str:
    if isinstance(v, float):
        return f"{v:.1f}".rstrip("0").rstrip(".")
    return str(v)


def bar_chart_svg(data: list, width: int = 640, height: int = 260, color: str = "#09284b",
                    value_suffix: str = "", empty_message: str = "No data in this range.") -> str:
    """`data` is a list of (label, value) pairs, in the order to display
    (left to right). Simple vertical bars with a value label on top and a
    rotated x-axis label underneath -- deliberately plain (no gridlines,
    no animation) so it stays legible on a print/PDF export too, not just
    on screen."""
    if not data:
        return f'<div style="padding:32px; text-align:center; color:#999; font-size:13px;">{escape(empty_message)}</div>'

    pad_left, pad_right, pad_top, pad_bottom = 36, 16, 26, 56
    plot_w = width - pad_left - pad_right
    plot_h = height - pad_top - pad_bottom
    max_val = max((v for _, v in data), default=0) or 1
    n = len(data)
    slot_w = plot_w / n
    bar_w = min(slot_w * 0.6, 56)

    bars, labels, values = [], [], []
    for i, (label, value) in enumerate(data):
        slot_x = pad_left + i * slot_w
        bar_h = (value / max_val) * plot_h if max_val else 0
        x = slot_x + (slot_w - bar_w) / 2
        y = pad_top + plot_h - bar_h
        bars.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" rx="3" fill="{color}"></rect>')
        values.append(
            f'<text x="{x + bar_w/2:.1f}" y="{y - 6:.1f}" font-size="11" text-anchor="middle" fill="#333" font-family="Arial,sans-serif">{escape(_fmt(value))}{escape(value_suffix)}</text>'
        )
        label_text = str(label)
        if len(label_text) > 14:
            label_text = label_text[:13] + "…"
        ty = pad_top + plot_h + 16
        labels.append(
            f'<text x="{slot_x + slot_w/2:.1f}" y="{ty:.1f}" font-size="10.5" text-anchor="end" fill="#666" '
            f'font-family="Arial,sans-serif" transform="rotate(-40 {slot_x + slot_w/2:.1f} {ty:.1f})">{escape(label_text)}</text>'
        )

    baseline_y = pad_top + plot_h
    return (
        f'<svg viewBox="0 0 {width} {height}" width="100%" style="max-width:{width}px; height:auto; display:block;" '
        f'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Bar chart">'
        f'<line x1="{pad_left}" y1="{baseline_y}" x2="{width - pad_right}" y2="{baseline_y}" stroke="#e2e4e8" stroke-width="1"></line>'
        + "".join(bars) + "".join(values) + "".join(labels) +
        "</svg>"
    )


def donut_chart_svg(segments: list, width: int = 240, height: int = 240,
                      empty_message: str = "No data in this range.") -> str:
    """`segments` is a list of (label, value, color) triples. Drawn as a
    ring of stacked `<circle>` strokes (the standard stroke-dasharray
    donut technique) -- no path/arc trigonometry needed, and it degrades
    gracefully (just doesn't render) in any SVG-capable viewer without a
    dependency on a JS chart runtime."""
    total = sum(v for _, v, _ in segments)
    if not segments or not total:
        return f'<div style="padding:32px; text-align:center; color:#999; font-size:13px;">{escape(empty_message)}</div>'

    cx, cy = width / 2, height / 2
    r = min(width, height) / 2 - 14
    circumference = 2 * 3.14159265 * r
    offset = 0.0
    rings = []
    for label, value, color in segments:
        frac = value / total
        seg_len = frac * circumference
        rings.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="26" '
            f'stroke-dasharray="{seg_len:.2f} {circumference - seg_len:.2f}" '
            f'stroke-dashoffset="{-offset:.2f}" transform="rotate(-90 {cx} {cy})"></circle>'
        )
        offset += seg_len

    legend_rows = []
    for i, (label, value, color) in enumerate(segments):
        pct = round(100 * value / total, 1)
        y = cy - (len(segments) - 1) * 9 + i * 18
        legend_rows.append(
            f'<rect x="{width + 14}" y="{y - 9}" width="10" height="10" fill="{color}" rx="2"></rect>'
            f'<text x="{width + 30}" y="{y}" font-size="11.5" fill="#333" font-family="Arial,sans-serif">{escape(str(label))} ({escape(_fmt(value))}, {pct}%)</text>'
        )

    total_w = width + 190
    return (
        f'<svg viewBox="0 0 {total_w} {height}" width="100%" style="max-width:{total_w}px; height:auto; display:block;" '
        f'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Donut chart">'
        + "".join(rings) +
        f'<text x="{cx}" y="{cy + 5}" font-size="20" font-weight="700" text-anchor="middle" fill="#09284b" font-family="Arial,sans-serif">{escape(_fmt(total))}</text>'
        + "".join(legend_rows) +
        "</svg>"
    )


def chart_card(title: str, subtitle: str, svg_markup: str, download_urls: dict = None) -> str:
    """Wraps a chart in the same `.card` shell every other page uses, plus
    a small HTML/PDF download row when `download_urls` ({'html': url,
    'pdf': url}) is given -- consistent with the table export buttons
    (_export_toolbar.html), just for a chart instead of a table."""
    dl = ""
    if download_urls:
        dl = (
            '<div style="margin-top:10px; display:flex; gap:6px;">'
            f'<a class="btn btn-secondary btn-sm" href="{download_urls.get("html", "#")}">Download HTML</a>'
            f'<a class="btn btn-secondary btn-sm" href="{download_urls.get("pdf", "#")}">Download PDF</a>'
            "</div>"
        )
    subtitle_html = f'<p class="card-note" style="margin-top:-4px;">{escape(subtitle)}</p>' if subtitle else ""
    return (
        '<div class="card">'
        f"<h2>{escape(title)}</h2>"
        f"{subtitle_html}"
        f'<div style="overflow-x:auto;">{svg_markup}</div>'
        f"{dl}"
        "</div>"
    )
