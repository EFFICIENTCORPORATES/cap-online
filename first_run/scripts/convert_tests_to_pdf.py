"""
convert_tests_to_pdf.py
========================
Converts the student-facing chapter test Markdown files (Questions-only and
Questions+Answers, one pair per AS) into watermarked PDF files ready to
circulate to students.

Usage:
    python convert_tests_to_pdf.py [input_dir] [output_dir]

    input_dir   defaults to  first_run/TESTS/second phase/student-edition
    output_dir  defaults to  <input_dir>/pdf

Every .md file in input_dir is converted to a same-named .pdf in output_dir,
stamped on every page with a diagonal "CA Pranav | VC Gurukul" watermark.

Requires (install once):
    pip install markdown xhtml2pdf reportlab pypdf

How it works:
    1. Markdown -> HTML (python-markdown, tables extension on - the source
       .md files also embed raw HTML directly, e.g. <table> blocks for
       accounting workings; python-markdown passes raw HTML through
       untouched, so that renders correctly too).
    2. HTML -> PDF via xhtml2pdf (already used elsewhere in this codebase,
       e.g. telegram/bots/exam_hub_bot.py's send_pdf) - kept to plain,
       well-supported CSS since xhtml2pdf's CSS3 support is limited.
    3. A one-page watermark PDF is generated with reportlab (diagonal,
       semi-transparent) and merged onto every page of the step-2 PDF with
       pypdf - watermarking this way (stamp-and-merge) is more reliable
       than trying to get a repeating CSS background through xhtml2pdf.

Note on the vendored font (fonts/DejaVuSans.ttf, fonts/DejaVuSans-Bold.ttf):
    The base-14 PDF fonts (Helvetica etc.) have no glyph for the rupee sign
    (U+20B9) - it silently renders as a black missing-glyph box, a real
    problem given these papers use Rs sums constantly. DejaVu Sans does
    have it (confirmed) and is freely redistributable, so it ships
    alongside this script - keep the fonts/ folder next to this file.
    Getting xhtml2pdf to actually load it needed two fixes, both applied
    below: (1) reference the font by a plain OS path, not a file:// URI -
    xhtml2pdf's file:// handler expects a path-only string and silently
    fails to find the file otherwise; (2) monkeypatch its temp-file step -
    on Windows, tempfile.NamedTemporaryFile() keeps a lock that prevents
    reportlab from reopening the same file by name, so font loading throws
    PermissionError. Both were confirmed as the actual root cause by
    tracing through xhtml2pdf's source, not guessed.
"""
import io
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import markdown
from xhtml2pdf import pisa
import xhtml2pdf.files as _x2p_files
from reportlab.pdfgen import canvas
from pypdf import PdfReader, PdfWriter


def _patched_get_named_tmp_file(self):
    """Replaces xhtml2pdf.files.BaseFile.get_named_tmp_file - see the
    module docstring's "Note on the vendored font" for why this is needed
    on Windows. Only .name is ever read off the return value by callers."""
    data = self.get_data()
    tmp = tempfile.NamedTemporaryFile(suffix=self.suffix, delete=False)
    if data:
        tmp.write(data)
    tmp.close()
    if self.path is None:
        self.path = tmp.name
    return SimpleNamespace(name=tmp.name)


_x2p_files.BaseFile.get_named_tmp_file = _patched_get_named_tmp_file

# --- Watermark text - edit these two lines to change the branding ---------
WATERMARK_LINE_1 = "CA Pranav"
WATERMARK_LINE_2 = "VC Gurukul"

DEFAULT_INPUT_DIR = Path(__file__).resolve().parents[1] / "TESTS" / "second phase" / "student-edition"

# The base-14 PDF fonts (Helvetica etc.) have no glyph for the rupee sign
# (U+20B9) - it silently renders as a black missing-glyph box, which is a
# real problem given these accounting papers use ₹ constantly. Fixed by
# embedding DejaVu Sans (vendored locally in fonts/, SIL/Bitstream-Vera-
# licensed, freely redistributable, confirmed via fontTools to include the
# rupee glyph) instead of relying on the system's Helvetica/Arial mapping.
FONTS_DIR = Path(__file__).resolve().parent / "fonts"
FONT_REGULAR = FONTS_DIR / "DejaVuSans.ttf"
FONT_BOLD = FONTS_DIR / "DejaVuSans-Bold.ttf"


def _font_face_css():
    if not (FONT_REGULAR.exists() and FONT_BOLD.exists()):
        return ""  # falls back to Helvetica - rupee signs will show as boxes
    # A plain OS path, not a file:// URI and no quotes around the font name -
    # both confirmed necessary (see module docstring) for xhtml2pdf to
    # actually find the file and register the font under this name.
    reg_path = str(FONT_REGULAR.resolve()).replace("\\", "/")
    bold_path = str(FONT_BOLD.resolve()).replace("\\", "/")
    return f"""
    @font-face {{
        font-family: DejaVuSans;
        src: url({reg_path});
    }}
    @font-face {{
        font-family: DejaVuSans;
        font-weight: bold;
        src: url({bold_path});
    }}
    """


PAGE_CSS_TEMPLATE = """
<style>
  __FONT_FACE__
  @page {
    size: A4;
    margin: 2.3cm 1.8cm 2.3cm 1.8cm;
  }
  body {
    font-family: DejaVuSans, Helvetica, Arial, sans-serif;
    font-size: 10.5pt;
    line-height: 1.5;
    color: #202020;
  }
  h1 {
    font-size: 19pt;
    color: #17324d;
    margin-bottom: 2px;
  }
  h2 {
    font-size: 13.5pt;
    color: #17324d;
    margin-top: 20px;
    padding-bottom: 4px;
    border-bottom: 1px solid #cccccc;
  }
  h3 {
    font-size: 11.5pt;
    color: #17324d;
    margin-top: 14px;
  }
  p { margin: 6px 0; }
  ul, ol { margin: 4px 0 8px 22px; padding: 0; }
  li { margin: 2px 0; }
  table {
    border-collapse: collapse;
    width: 100%;
    margin: 8px 0 12px 0;
    font-size: 9.5pt;
  }
  th, td {
    border: 1px solid #999999;
    padding: 4px 6px;
    text-align: left;
    vertical-align: top;
  }
  th { background-color: #eef2f7; }
  strong { color: #17324d; }
  blockquote {
    background-color: #fdf6e3;
    border-left: 3px solid #d9a441;
    margin: 8px 0;
    padding: 6px 12px;
    font-size: 9.5pt;
  }
  hr {
    border: none;
    border-top: 1px solid #cccccc;
    margin: 16px 0;
  }
</style>
"""

PAGE_CSS = PAGE_CSS_TEMPLATE.replace("__FONT_FACE__", _font_face_css())


def md_to_html(md_path: Path) -> str:
    md_text = md_path.read_text(encoding="utf-8")
    body_html = markdown.markdown(md_text, extensions=["tables", "sane_lists"])
    return f"<html><head><meta charset='utf-8'>{PAGE_CSS}</head><body>{body_html}</body></html>"


def html_to_pdf_bytes(html: str) -> bytes:
    buf = io.BytesIO()
    result = pisa.CreatePDF(html, dest=buf)
    if result.err:
        raise RuntimeError(f"PDF generation failed with {result.err} error(s)")
    return buf.getvalue()


def make_watermark_page(width: float, height: float) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(width, height))
    c.saveState()
    c.translate(width / 2, height / 2)
    c.rotate(40)
    c.setFillColorRGB(0.55, 0.55, 0.55)
    try:
        c.setFillAlpha(0.16)
    except AttributeError:
        pass  # older reportlab without alpha support - watermark still shows, just fully opaque
    c.setFont("Helvetica-Bold", 42)
    c.drawCentredString(0, 14, WATERMARK_LINE_1)
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(0, -32, WATERMARK_LINE_2)
    c.restoreState()
    c.save()
    return buf.getvalue()


def apply_watermark(pdf_bytes: bytes) -> bytes:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()
    watermark_cache = {}
    for page in reader.pages:
        w, h = float(page.mediabox.width), float(page.mediabox.height)
        key = (round(w), round(h))
        if key not in watermark_cache:
            watermark_cache[key] = PdfReader(io.BytesIO(make_watermark_page(w, h))).pages[0]
        page.merge_page(watermark_cache[key])
        writer.add_page(page)
    out_buf = io.BytesIO()
    writer.write(out_buf)
    return out_buf.getvalue()


def convert_one(md_path: Path, output_dir: Path) -> Path:
    html = md_to_html(md_path)
    pdf_bytes = html_to_pdf_bytes(html)
    watermarked = apply_watermark(pdf_bytes)
    out_path = output_dir / (md_path.stem + ".pdf")
    out_path.write_bytes(watermarked)
    return out_path


def convert_all(input_dir: Path, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    md_files = sorted(input_dir.glob("*.md"))
    if not md_files:
        print(f"No .md files found in: {input_dir}")
        return
    print(f"Found {len(md_files)} Markdown file(s) in {input_dir}\n")
    ok, failed = 0, []
    for md_path in md_files:
        print(f"  {md_path.name} ...", end=" ")
        try:
            out_path = convert_one(md_path, output_dir)
            print(f"-> {out_path.name}")
            ok += 1
        except Exception as exc:
            print(f"FAILED: {exc}")
            failed.append(md_path.name)
    print(f"\nDone: {ok} PDF(s) written to {output_dir}")
    if failed:
        print(f"Failed ({len(failed)}): {', '.join(failed)}")


def main():
    input_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_INPUT_DIR
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else input_dir / "pdf"
    convert_all(input_dir, output_dir)


if __name__ == "__main__":
    main()
