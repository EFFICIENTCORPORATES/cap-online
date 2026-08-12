"""Generate shareable MCQ and descriptive input-format artifacts.

Reads the live Exam Hub JSON files only to copy one representative record and
confirm the current keys. It writes compact examples, one Excel workbook, and
one combined PDF guide into this folder. It never modifies the production
question banks.
"""

from __future__ import annotations

import json
from datetime import date
from html import escape
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
MCQ_SOURCE = REPO_ROOT / "telegram/assets/exam_bot/mcq_questions_extracted.json"
DESC_SOURCE = REPO_ROOT / "telegram/assets/exam_bot/book_questions_extracted.json"

MCQ_EXAMPLE = HERE / "mcq_input_example.json"
DESC_EXAMPLE = HERE / "descriptive_input_example.json"
XLSX_OUTPUT = HERE / "question_input_formats.xlsx"
PDF_OUTPUT = HERE / "question_input_formats.pdf"

MCQ_FIELDS = [
    ("mcq_id", "string", "Required", "Unique ID. Example: CMAI-P5-M12-FACULTY-2026-Q01"),
    ("course", "string", "Required", "CA, CS or CMA."),
    ("level", "string", "Required", "Course-specific level: Foundation, Intermediate, Final, CSEET, Executive or Professional."),
    ("exam_type", "string", "Required", "MTP, RTP, PYQ, PRACTICE or FACULTY_PRACTICE."),
    ("year", "string", "Required", "Exam/content year, or null when genuinely unknown."),
    ("set", "string", "Required", "Set label or empty string."),
    ("qno_text", "string", "Required", "Display question number, e.g. Q1 or Practice Q1."),
    ("marks", "integer", "Required", "Marks assigned to the question."),
    ("difficulty", "string/null", "Required", "Easy, Medium, Hard, or null if not reviewed."),
    ("qtype", "string", "Required", "mcq or case-mcq."),
    ("case_ref", "string/null", "Required", "Shared case identifier, otherwise null."),
    ("case_facts_html", "HTML string/null", "Required", "Shared case narrative, otherwise null."),
    ("question_html", "HTML string", "Required", "Question stem only; options remain in options."),
    ("options", "object", "Required", "Letter-to-text map. Usually A-D; never assume four if the source differs."),
    ("correct_option", "string", "Required", "Must be one of the option keys."),
    ("answer_html", "HTML string", "Required", "Answer and explanation, preferably source/faculty-authored."),
    ("chapter_slug", "string", "Required", "Stable machine chapter identifier."),
    ("chapter_label", "string", "Required", "Exact catalog chapter/module title."),
    ("unitcode", "string", "Required", "Exact catalog unit/module code."),
    ("topic_text", "string", "Required", "Topic label from the authoritative taxonomy or source document."),
]

DESC_FIELDS = [
    ("book_id", "string", "Required", "Unique descriptive-question ID."),
    ("flagged", "boolean", "Required", "True when a source/content issue needs review."),
    ("src_text", "string", "Required", "Human-readable source label."),
    ("qno_text", "string", "Required", "Question number or faculty practice label."),
    ("marks_text", "string", "Required", "Display text, e.g. Marks: 14 or Practice Question."),
    ("approx_time_text", "string", "Required", "Display time estimate."),
    ("topic_text", "string/null", "Required", "Topic label from the authoritative taxonomy or source."),
    ("badges", "array", "Required", "Display badges such as Compulsory; use [] when none."),
    ("question_html", "HTML string", "Required", "Full question, including tables and sub-parts."),
    ("answer_html", "HTML string", "Required", "Full model answer, including workings/tables."),
    ("answer_letter", "string/null", "Required", "Usually null for descriptive questions."),
    ("mistake_type", "string/null", "Required", "icai, synth, faculty, or null when not supplied."),
    ("mistake_text", "string/null", "Required", "Examiner comment or clearly labelled author note."),
    ("chapter_slug", "string", "Required", "Stable machine chapter identifier."),
    ("unitcode", "string", "Required", "Exact catalog unit/module code."),
    ("chapter_label", "string", "Required", "Exact catalog chapter/module title."),
    ("section", "string", "Required", "descriptive."),
]

PROVENANCE_FIELDS = [
    ("source_kind", "string", "Recommended", "official, faculty_created, extracted, or ai_generated."),
    ("faculty_id", "string/null", "Recommended", "Tenant/faculty owner when applicable."),
    ("faculty_name", "string/null", "Recommended", "Human-readable faculty name."),
    ("source_file", "string", "Recommended", "Original DOCX/PDF filename."),
    ("source_document_hash", "string", "Recommended", "SHA-256 of the source document."),
    ("publication_status", "string", "Recommended", "draft, reviewed or published."),
    ("validation_status", "string", "Recommended", "Machine/human validation state."),
]


def load_first(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    return data[0] if isinstance(data, list) else data["questions"][0]


def compact_example(source: Path, fields):
    source_record = load_first(source)
    example = {}
    for name, _, _, _ in fields + PROVENANCE_FIELDS:
        if name in source_record:
            example[name] = source_record[name]
        else:
            example[name] = None
    return example


def write_json_examples():
    mcq = compact_example(MCQ_SOURCE, MCQ_FIELDS)
    desc = compact_example(DESC_SOURCE, DESC_FIELDS)
    MCQ_EXAMPLE.write_text(json.dumps([mcq], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    DESC_EXAMPLE.write_text(json.dumps([desc], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def style_sheet(ws, widths):
    fill = PatternFill("solid", fgColor="D9EAF7")
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1F4E78")
        cell.alignment = Alignment(wrap_text=True, vertical="top")
    for col, width in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(col)].width = width
    ws.freeze_panes = "A2"
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")


def write_workbook():
    wb = Workbook()
    intro = wb.active
    intro.title = "Read Me First"
    intro.append(["Question Input Formats"])
    intro.append(["Use this workbook to prepare MCQ and descriptive JSON for the Exam Hub."])
    intro.append(["The JSON files must be arrays of records. Do not wrap them in an outer object unless the bot contract is changed."])
    intro.append(["HTML fields are allowed for tables, bold text, lists and structured answers."])
    intro.append(["Keep exact catalog unitcode and chapter_label values; do not invent taxonomy IDs."])
    intro.append(["Generated from the live schemas on " + date.today().isoformat()])
    intro.column_dimensions["A"].width = 115
    intro["A1"].font = Font(bold=True, size=16, color="1F4E78")
    intro["A1"].alignment = Alignment(wrap_text=True)

    for title, fields in [("MCQ Format", MCQ_FIELDS), ("Descriptive Format", DESC_FIELDS), ("Provenance", PROVENANCE_FIELDS)]:
        ws = wb.create_sheet(title)
        ws.append(["Field", "Type", "Requirement", "Meaning / rule"])
        for row in fields:
            ws.append(list(row))
        style_sheet(ws, [26, 20, 16, 105])
        ws.auto_filter.ref = ws.dimensions

    rules = wb.create_sheet("Validation Rules")
    rules.append(["Rule", "MCQ", "Descriptive"])
    rules.append(["JSON root", "Array of records", "Array of records"])
    rules.append(["Identity", "mcq_id unique", "book_id unique"])
    rules.append(["Taxonomy", "unitcode/chapter_label must match catalog", "unitcode/chapter_label must match catalog"])
    rules.append(["Answer", "correct_option must exist in options", "answer_html required"])
    rules.append(["Source", "Preserve source/faculty provenance", "Preserve source/faculty provenance"])
    rules.append(["Review", "Numeric/legal figures require review when currentness matters", "flagged/mistake fields must distinguish source comments from author notes"])
    style_sheet(rules, [24, 65, 65])
    rules.auto_filter.ref = rules.dimensions
    wb.save(XLSX_OUTPUT)


def pdf_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TitleCenter", parent=styles["Title"], alignment=TA_CENTER, textColor=colors.HexColor("#1F4E78")))
    styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontSize=8.5, leading=11))
    styles.add(ParagraphStyle(name="HeadingBlue", parent=styles["Heading2"], textColor=colors.HexColor("#1F4E78")))
    return styles


def table_for_fields(fields):
    rows = [["Field", "Type", "Requirement", "Rule"]] + [list(row) for row in fields]
    table = Table(rows, colWidths=[33 * mm, 28 * mm, 25 * mm, 94 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E78")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("LEADING", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EEF5FA")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table


def write_pdf():
    styles = pdf_styles()
    doc = SimpleDocTemplate(str(PDF_OUTPUT), pagesize=A4, rightMargin=12 * mm, leftMargin=12 * mm, topMargin=12 * mm, bottomMargin=12 * mm)
    story = [Paragraph("Exam Hub Question Input Formats", styles["TitleCenter"]), Spacer(1, 5 * mm)]
    story.append(Paragraph("Purpose", styles["HeadingBlue"]))
    story.append(Paragraph("This guide defines the JSON contract for faculty or content partners supplying MCQ and descriptive questions to the Telegram Exam Hub. Submit a JSON array, preserve HTML in question/answer fields, and use exact catalog module codes and titles.", styles["BodyText"]))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph("MCQ record", styles["HeadingBlue"]))
    story.append(table_for_fields(MCQ_FIELDS))
    story.append(PageBreak())
    story.append(Paragraph("Descriptive record", styles["HeadingBlue"]))
    story.append(table_for_fields(DESC_FIELDS))
    story.append(PageBreak())
    story.append(Paragraph("Provenance and validation", styles["HeadingBlue"]))
    story.append(table_for_fields(PROVENANCE_FIELDS))
    story.append(Spacer(1, 4 * mm))
    rules = [
        ["Validation rule", "Requirement"],
        ["Root shape", "A JSON array of records."],
        ["IDs", "Every MCQ mcq_id and descriptive book_id must be unique."],
        ["Taxonomy", "unitcode and chapter_label must come from the authoritative course catalog."],
        ["MCQ answers", "correct_option must match an option key; preserve all four options when the source has A-D."],
        ["Descriptive answers", "answer_html must contain the complete model answer, workings and tables."],
        ["Review", "Do not silently correct source law, amounts or dates. Flag them for review."],
    ]
    table = Table(rules, colWidths=[38 * mm, 142 * mm], repeatRows=1)
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E78")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -1), 0.25, colors.grey), ("FONTSIZE", (0, 0), (-1, -1), 8), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(table)
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("See mcq_input_example.json and descriptive_input_example.json in this folder for compact valid examples. The full production banks are not duplicated here.", styles["Small"]))
    doc.build(story)


def main():
    write_json_examples()
    write_workbook()
    write_pdf()
    print(f"Wrote {MCQ_EXAMPLE}")
    print(f"Wrote {DESC_EXAMPLE}")
    print(f"Wrote {XLSX_OUTPUT}")
    print(f"Wrote {PDF_OUTPUT}")


if __name__ == "__main__":
    main()
