import os
import sys
import io
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont

# ============================================================
# CONFIG
# ============================================================

INPUT_PDF = r"H:\Other computers\Office_Desktop\EffCorp_Projects\cap-online\first_run\output\final_deliverable\CA Inter Advanced Accounts_ The Complete Question Bank_V1.pdf"

WATERMARK_TEXT = "CA PRANAV PRATIK TULSHYAN"

# For sharp text:
# 300 = good
# 400 = sharper
# 600 = very sharp but large file size
DPI = 400

# Watermark styling
WATERMARK_OPACITY = 32   # lower = lighter
WATERMARK_ANGLE = 32

# If True, watermark every page.
# If False, watermark only selected page range below.
APPLY_WATERMARK_ALL_PAGES = True

# 1-based inclusive page range if APPLY_WATERMARK_ALL_PAGES = False
WATERMARK_START_PAGE = ""
WATERMARK_END_PAGE = ""

# Output format for embedded page images:
# "PNG" = sharper text, larger file
# "JPEG" = smaller file, slightly softer text
IMAGE_FORMAT = "PNG"

# Used only if IMAGE_FORMAT = "JPEG"
JPEG_QUALITY = 92

if hasattr(Image, "Resampling"):
    RESAMPLE_BICUBIC = Image.Resampling.BICUBIC
else:
    RESAMPLE_BICUBIC = Image.BICUBIC


# ============================================================
# HELPERS
# ============================================================

def get_output_path(input_pdf_path: str) -> str:
    p = Path(input_pdf_path)
    return str(p.with_name(f"{p.stem}_pro{p.suffix}"))


def get_font(font_size: int):
    candidates = [
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\calibri.ttf",
        r"C:\Windows\Fonts\tahoma.ttf",
        r"/System/Library/Fonts/Supplemental/Arial.ttf",
        r"/Library/Fonts/Arial.ttf",
        r"/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]

    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, font_size)
            except Exception:
                pass

    return ImageFont.load_default()


def parse_optional_page_number(value, field_name: str):
    if value is None:
        return None

    if isinstance(value, str):
        value = value.strip()
        if value == "":
            return None

    try:
        n = int(value)
    except Exception:
        raise ValueError(f"{field_name} must be blank or an integer.")

    if n < 1:
        raise ValueError(f"{field_name} must be 1 or greater.")

    return n


def resolve_watermark_range(total_pages: int, start_page, end_page):
    start = parse_optional_page_number(start_page, "WATERMARK_START_PAGE")
    end = parse_optional_page_number(end_page, "WATERMARK_END_PAGE")

    if start is None:
        start = 1
    if end is None:
        end = total_pages

    if start > total_pages:
        raise ValueError(f"WATERMARK_START_PAGE ({start}) exceeds total pages ({total_pages}).")
    if end > total_pages:
        raise ValueError(f"WATERMARK_END_PAGE ({end}) exceeds total pages ({total_pages}).")
    if start > end:
        raise ValueError("WATERMARK_START_PAGE cannot be greater than WATERMARK_END_PAGE.")

    return start, end


def should_apply_watermark(page_number: int, total_pages: int) -> bool:
    if APPLY_WATERMARK_ALL_PAGES:
        return True

    start, end = resolve_watermark_range(total_pages, WATERMARK_START_PAGE, WATERMARK_END_PAGE)
    return start <= page_number <= end


def make_tiled_watermark_overlay(width: int, height: int, text: str, angle: int, opacity: int) -> Image.Image:
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))

    font_size = max(26, int(min(width, height) * 0.045))
    font = get_font(font_size)

    temp = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
    draw_temp = ImageDraw.Draw(temp)
    bbox = draw_temp.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    pad_x = max(30, font_size // 2)
    pad_y = max(20, font_size // 3)

    text_img = Image.new(
        "RGBA",
        (text_w + 2 * pad_x, text_h + 2 * pad_y),
        (0, 0, 0, 0)
    )

    draw_text = ImageDraw.Draw(text_img)
    draw_text.text(
        (pad_x, pad_y),
        text,
        font=font,
        fill=(110, 110, 110, opacity)
    )

    rotated = text_img.rotate(angle, expand=True, resample=RESAMPLE_BICUBIC)

    step_x = max(int(rotated.width * 1.15), 250)
    step_y = max(int(rotated.height * 1.6), 180)

    start_x = -rotated.width
    start_y = -rotated.height

    for y in range(start_y, height + rotated.height, step_y):
        for x in range(start_x, width + rotated.width, step_x):
            overlay.alpha_composite(rotated, (x, y))

    return overlay


def add_repeated_watermark(base_image: Image.Image, text: str, angle: int, opacity: int) -> Image.Image:
    base = base_image.convert("RGBA")
    overlay = make_tiled_watermark_overlay(
        width=base.width,
        height=base.height,
        text=text,
        angle=angle,
        opacity=opacity
    )
    combined = Image.alpha_composite(base, overlay)
    return combined.convert("RGB")


def image_to_bytes(img: Image.Image, image_format: str) -> bytes:
    bio = io.BytesIO()

    if image_format.upper() == "PNG":
        img.save(bio, format="PNG", optimize=True)
    elif image_format.upper() == "JPEG":
        img.save(
            bio,
            format="JPEG",
            quality=JPEG_QUALITY,
            optimize=True,
            progressive=True
        )
    else:
        raise ValueError("IMAGE_FORMAT must be either 'PNG' or 'JPEG'.")

    return bio.getvalue()


# ============================================================
# CORE
# ============================================================

def protect_pdf_without_password(input_pdf_path: str):
    input_pdf = Path(input_pdf_path)

    if not input_pdf.exists():
        raise FileNotFoundError(f"Input PDF not found:\n{input_pdf}")

    if input_pdf.suffix.lower() != ".pdf":
        raise ValueError("The input file must be a PDF.")

    output_pdf_path = get_output_path(str(input_pdf))

    src = fitz.open(str(input_pdf))
    out = fitz.open()

    try:
        total_pages = len(src)
        scale = DPI / 72.0
        matrix = fitz.Matrix(scale, scale)

        for page_index in range(total_pages):
            page = src[page_index]
            page_number = page_index + 1

            # Rasterize page
            pix = page.get_pixmap(matrix=matrix, alpha=False, colorspace=fitz.csRGB)
            img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")

            # Apply watermark if needed
            if should_apply_watermark(page_number, total_pages):
                img = add_repeated_watermark(
                    img,
                    text=WATERMARK_TEXT,
                    angle=WATERMARK_ANGLE,
                    opacity=WATERMARK_OPACITY
                )

            page_img_bytes = image_to_bytes(img, IMAGE_FORMAT)

            # Keep original page size
            rect = page.rect
            new_page = out.new_page(width=rect.width, height=rect.height)
            new_page.insert_image(rect, stream=page_img_bytes)

        # Strip metadata as much as possible
        out.set_metadata({
            "title": input_pdf.stem + "_pro",
            "author": "",
            "subject": "",
            "keywords": "",
            "creator": "",
            "producer": "",
        })

        # Save WITHOUT password
        out.save(
            output_pdf_path,
            garbage=4,
            clean=True,
            deflate=True
        )

    finally:
        out.close()
        src.close()

    return output_pdf_path


if __name__ == "__main__":
    try:
        input_path = sys.argv[1].strip() if len(sys.argv) > 1 else INPUT_PDF
        result = protect_pdf_without_password(input_path)
        print(f"Protected PDF created successfully:\n{result}")
        print("No password applied.")
        print(f"DPI used: {DPI}")
        print(f"Embedded image format: {IMAGE_FORMAT}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
