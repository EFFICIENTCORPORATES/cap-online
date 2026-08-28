#!/usr/bin/env python3
"""
compress_pdf.py -- shrink an image-heavy PDF (e.g. the 400-DPI/PNG output
of watermark_for_print.py) by re-rendering every page at a lower DPI and
re-encoding as high-quality JPEG instead of lossless PNG. Those are the two
real levers for a PDF that's already pure images -- plain
fitz.save(garbage=4, deflate=True) barely helps here, since there's no
redundant font/text-stream data left to strip once a page IS an image.

WHY RE-RENDER RATHER THAN JUST RE-ENCODE THE EXISTING EMBEDDED IMAGES
------------------------------------------------------------------------
PyMuPDF can re-render each PAGE at any DPI directly from the PDF (not just
re-save whatever raw bytes are already embedded) -- that's what
page.get_pixmap(matrix=...) does. Downsampling this way (400 DPI source ->
200 DPI output, say) produces a clean, properly-antialiased resize, exactly
as if the page had been rasterized at the lower DPI in the first place.

NOTE: this tool flattens every page to an image, same trade-off as
watermark_for_print.py. Don't point it at a PDF whose real, selectable text
layer you want to KEEP -- that text layer will be destroyed. If the input
is already an image-only PDF (e.g. a protected/watermarked book), nothing
new is lost that wasn't already lost.

USAGE
-----
    python compress_pdf.py INPUT.pdf
        Writes INPUT_compressed.pdf next to it. Defaults: DPI=200, JPEG
        quality=82 -- sharp on screen, clean on a home/office printer, and
        typically 8-15x smaller than a 400-DPI PNG source.

    python compress_pdf.py INPUT.pdf -o OUTPUT.pdf --dpi 180 --quality 78
        Custom output path / DPI / quality.

GUIDANCE ON THE TWO KNOBS
----------------------------
  --dpi      300+  print-shop sharp, large files.
             200-220  sharp on any screen, fine for real printing (default 200).
             150  noticeably softer, screen-only.
  --quality  85-95  visually lossless for this kind of flat-colour/text content.
             75-84  still very clean, meaningfully smaller (default 82).
             below 65  JPEG blockiness starts showing around text edges.
"""
import argparse
import io
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image


def compress_pdf(input_path: Path, output_path: Path, dpi: int, quality: int, image_format: str = "JPEG") -> None:
    src = fitz.open(str(input_path))
    out = fitz.open()
    try:
        scale = dpi / 72.0
        matrix = fitz.Matrix(scale, scale)
        total = len(src)
        for i, page in enumerate(src, start=1):
            pix = page.get_pixmap(matrix=matrix, alpha=False, colorspace=fitz.csRGB)
            img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")

            bio = io.BytesIO()
            if image_format.upper() == "JPEG":
                img.save(bio, format="JPEG", quality=quality, optimize=True, progressive=True)
            else:
                img.save(bio, format="PNG", optimize=True)
            img_bytes = bio.getvalue()

            rect = page.rect
            new_page = out.new_page(width=rect.width, height=rect.height)
            new_page.insert_image(rect, stream=img_bytes)

            if i % 25 == 0 or i == total:
                print(f"  {i}/{total} pages processed...")

        out.set_metadata(src.metadata)
        out.save(str(output_path), garbage=4, clean=True, deflate=True)
    finally:
        out.close()
        src.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="Path to the PDF to compress.")
    ap.add_argument("-o", "--output", default=None,
                     help="Output path (default: INPUT_compressed.pdf next to input).")
    ap.add_argument("--dpi", type=int, default=200, help="Render DPI for each page (default 200).")
    ap.add_argument("--quality", type=int, default=82, help="JPEG quality 1-95 (default 82).")
    ap.add_argument("--format", choices=["JPEG", "PNG"], default="JPEG",
                     help="Embedded image format (default JPEG; PNG stays lossless but much larger).")
    args = ap.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"ERROR: {input_path} not found.")

    output_path = (
        Path(args.output) if args.output
        else input_path.with_name(f"{input_path.stem}_compressed{input_path.suffix}")
    )

    print(f"Compressing {input_path.name} -> {output_path.name}  "
          f"(DPI={args.dpi}, quality={args.quality}, format={args.format})")
    compress_pdf(input_path, output_path, args.dpi, args.quality, args.format)

    before = input_path.stat().st_size
    after = output_path.stat().st_size
    print(f"\nDone: {before/1024/1024:.1f} MB -> {after/1024/1024:.1f} MB  "
          f"({100*(1-after/before):.0f}% smaller)")
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
