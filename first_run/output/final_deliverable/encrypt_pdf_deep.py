import os
import sys
import io
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont

# -----------------------------
# CONFIG
# -----------------------------
DEFAULT_INPUT_PDF = r"H:\Other computers\Office_Desktop\EffCorp_Projects\cap-online\first_run\output\final_deliverable\CA Inter Advanced Accounts_ The Complete Question Bank_V1.pdf"
PASSWORD = "PranavBhaiya@777"
WATERMARK_TEXT = "CA Pranav Pratik Tulshyan"
DPI = 300                  # Increase to 400 or 600 if you want sharper output
WATERMARK_OPACITY = 42     # 0 to 255 (lower = lighter)
WATERMARK_ANGLE = 35       # diagonal angle
FONT_COLOR = (110, 110, 110, WATERMARK_OPACITY)

# Pillow compatibility for resampling constants
if hasattr(Image, "Resampling"):
    BICUBIC = Image.Resampling.BICUBIC
else:
    BICUBIC = Image.BICUBIC


def get_output_path(input_pdf_path: str) -> str:
    p = Path(input_pdf_path)
    return str(p.with_name(f"{p.stem}_pro{p.suffix}"))


def find_font(font_size: int):
    """
    Tries common system fonts. Falls back safely if none found.
    """
    candidates = [
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\calibri.ttf",
        r"C:\Windows\Fonts\arialbd.ttf",
        r"/System/Library/Fonts/Supplemental/Arial.ttf",
        r"/Library/Fonts/Arial.ttf",
        r"/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]

    for font_path in candidates:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, font_size)
            except Exception:
                pass

    return ImageFont.load_default()


def add_diagonal_watermark(base_image: Image.Image, text: str) -> Image.Image:
    """
    Adds one centered diagonal watermark with low opacity.
    """
    base = base_image.convert("RGBA")
    width, height = base.size

    # Font size based on page dimensions
    font_size = max(28, int(min(width, height) * 0.055))
    font = find_font(font_size)

    # Measure text
    dummy = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
    draw_dummy = ImageDraw.Draw(dummy)
    bbox = draw_dummy.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    pad_x = max(20, font_size // 2)
    pad_y = max(20, font_size // 3)

    text_layer = Image.new("RGBA", (text_w + 2 * pad_x, text_h + 2 * pad_y), (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_layer)
    draw.text((pad_x, pad_y), text, font=font, fill=FONT_COLOR)

    rotated = text_layer.rotate(WATERMARK_ANGLE, expand=True, resample=BICUBIC)

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    x = (width - rotated.width) // 2
    y = (height - rotated.height) // 2
    overlay.paste(rotated, (x, y), rotated)

    combined = Image.alpha_composite(base, overlay)
    return combined.convert("RGB")


def protect_pdf(input_pdf_path: str, password: str = PASSWORD):
    input_pdf = Path(input_pdf_path)

    if not input_pdf.exists():
        raise FileNotFoundError(f"Input PDF not found:\n{input_pdf}")

    if input_pdf.suffix.lower() != ".pdf":
        raise ValueError("The input file must be a PDF.")

    output_pdf_path = get_output_path(str(input_pdf))

    src = fitz.open(str(input_pdf))
    out = fitz.open()

    try:
        zoom = DPI / 72.0
        matrix = fitz.Matrix(zoom, zoom)

        for page_number in range(len(src)):
            page = src[page_number]

            # Rasterize the page so text is no longer directly extractable
            pix = page.get_pixmap(matrix=matrix, alpha=False)

            img_bytes = pix.tobytes("png")
            pil_img = Image.open(io.BytesIO(img_bytes)).convert("RGB")

            # Add watermark
            watermarked_img = add_diagonal_watermark(pil_img, WATERMARK_TEXT)

            # Convert back to PNG bytes
            page_img_stream = io.BytesIO()
            watermarked_img.save(page_img_stream, format="PNG", optimize=True)
            page_img_stream.seek(0)

            # Preserve original page size in points
            rect = page.rect
            new_page = out.new_page(width=rect.width, height=rect.height)
            new_page.insert_image(rect, stream=page_img_stream.getvalue())

        # Minimal metadata
        out.set_metadata({
            "title": input_pdf.stem + "_pro",
            "author": "",
            "subject": "",
            "keywords": "",
            "creator": "",
            "producer": "",
        })

        # Allow printing if viewer respects permissions, but restrict copy/extract.
        permissions = 0
        permissions |= int(getattr(fitz, "PDF_PERM_PRINT", 0))
        permissions |= int(getattr(fitz, "PDF_PERM_PRINT_HQ", 0))

        out.save(
            output_pdf_path,
            garbage=4,
            clean=True,
            deflate=True,
            encryption=fitz.PDF_ENCRYPT_AES_256,
            owner_pw=password,
            user_pw=password,
            permissions=permissions,
        )

    finally:
        out.close()
        src.close()

    return output_pdf_path


if __name__ == "__main__":
    try:
        input_path = sys.argv[1].strip() if len(sys.argv) > 1 else DEFAULT_INPUT_PDF
        result = protect_pdf(input_path, PASSWORD)
        print(f"Protected PDF created successfully:\n{result}")
        print(f"Password: {PASSWORD}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

