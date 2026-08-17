"""
telegram/admin_portal/charts_pdf.py -- native PDF chart rendering
(2026-08-13, Overview rebuild)
--------------------------------------------------------------------------------
charts.py draws on-screen/HTML-export charts as inline SVG -- but
xhtml2pdf (the HTML->PDF engine every other export in this app already
uses, via exporters.py) has no reliable inline-<svg> support, so running
that SVG through xhtml2pdf would silently produce a blank or broken chart
in the PDF. Found and worked around here rather than shipped broken:
PDF chart export uses reportlab's OWN native chart flowables
(reportlab.graphics.charts) instead -- reportlab is already a hard
dependency of this project (xhtml2pdf itself is built on it; also used
directly by telegram/base_formats/generate_base_formats.py), so this adds
no new dependency, just a different reportlab API for this one case.
Genuine vector charts in the PDF, not a rasterized screenshot of the SVG.
"""

from __future__ import annotations

import io

from reportlab.lib import colors as rl_colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.graphics.shapes import Drawing, String
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.legends import Legend


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="ChartTitle", parent=styles["Title"], alignment=TA_CENTER, fontSize=16))
    styles.add(ParagraphStyle(name="ChartMeta", parent=styles["BodyText"], alignment=TA_CENTER, fontSize=9, textColor=rl_colors.grey))
    return styles


def _doc_bytes(title: str, brand_colors: dict, drawing: Drawing, subtitle: str = "") -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=20 * mm, bottomMargin=20 * mm,
                             leftMargin=18 * mm, rightMargin=18 * mm)
    styles = _styles()
    navy = rl_colors.HexColor(brand_colors.get("navy", "#09284b"))
    story = [
        Paragraph("1LAVYA Admin Portal", ParagraphStyle(name="Brand", parent=styles["Title"], alignment=TA_CENTER, fontSize=13, textColor=navy)),
        Spacer(1, 2 * mm),
        Paragraph(title, styles["ChartTitle"]),
    ]
    if subtitle:
        story.append(Paragraph(subtitle, styles["ChartMeta"]))
    story.append(Spacer(1, 8 * mm))
    story.append(drawing)
    doc.build(story)
    return buf.getvalue()


def bar_chart_pdf_bytes(title: str, data: list, brand_colors: dict, subtitle: str = "",
                          value_suffix: str = "") -> bytes:
    """`data` is a list of (label, value) pairs."""
    width, height = 480, 300
    drawing = Drawing(width, height)
    chart = VerticalBarChart()
    chart.x, chart.y = 50, 50
    chart.width, chart.height = width - 90, height - 90
    chart.data = [[v for _, v in data]]
    chart.categoryAxis.categoryNames = [str(l)[:16] for l, _ in data]
    chart.categoryAxis.labels.angle = 30
    chart.categoryAxis.labels.dx = -6
    chart.categoryAxis.labels.fontSize = 7.5
    chart.valueAxis.valueMin = 0
    chart.bars[0].fillColor = rl_colors.HexColor(brand_colors.get("navy", "#09284b"))
    chart.barLabels.fontSize = 7.5
    chart.barLabelFormat = f"%s{value_suffix}"
    chart.barLabels.nudge = 8
    drawing.add(chart)
    return _doc_bytes(title, brand_colors, drawing, subtitle)


def donut_chart_pdf_bytes(title: str, segments: list, brand_colors: dict, subtitle: str = "") -> bytes:
    """`segments` is a list of (label, value, color_hex) triples -- same
    shape charts.donut_chart_svg() takes, rendered here as a reportlab Pie
    (a true ring "donut" isn't a built-in reportlab chart type; a labeled
    pie carries the same information without a custom shape subclass)."""
    width, height = 420, 320
    drawing = Drawing(width, height)
    pie = Pie()
    pie.x, pie.y = 70, 60
    pie.width = pie.height = 200
    pie.data = [v for _, v, _ in segments]
    pie.labels = [f"{l} ({v})" for l, v, _ in segments]
    pie.slices.strokeWidth = 1
    pie.slices.strokeColor = rl_colors.white
    for i, (_, _, color_hex) in enumerate(segments):
        pie.slices[i].fillColor = rl_colors.HexColor(color_hex)
    drawing.add(pie)
    return _doc_bytes(title, brand_colors, drawing, subtitle)
