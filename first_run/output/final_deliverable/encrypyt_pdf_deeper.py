import os
import sys
import io
import argparse
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont

# ============================================================
# DEFAULT CONFIG
# ============================================================

DEFAULT_INPUT = r"H:\Other computers\Office_Desktop\EffCorp_Projects\cap-online\first_run\output\final_deliverable\CA Inter Advanced Accounts_ The Complete Question Bank_V1.pdf"
DEFAULT_PASSWORD = "PranavBhaiya@777"
DEFAULT_WATERMARK_TEXT = "CA Pranav Pratik Tulshyan"

# Quality / size balance
DEFAULT_DPI = 240
DEFAULT_JPEG_QUALITY = 82  # Lower = smaller file, higher = better quality

# Watermark styling
DEFAULT_WATERMARK_OPACITY = 34  # 0 to 255, lower = lighter
DEFAULT_WATERMARK_ANGLE = 32

# ============================================================
# WATERMARK PAGE RANGE
# Leave blank ("") to apply from first page to last page
# Page numbering is 1-based
# Example:
#   DEFAULT_WATERMARK_START_PAGE = 3
#   DEFAULT_WATERMARK_END_PAGE = 25
# ============================================================

DEFAULT_WATERMARK_START_PAGE = 10
DEFAULT_WATERMARK_END_PAGE = ""

# Folder processing
DEFAULT_RECURSIVE = False

# Skip already processed files
SKIP_SUFFIX = "_pro.pdf"

if hasattr(Image, "Resampling"):
    RESAMPLE_BICUBIC = Image.Resampling.BICUBIC
else:
    RESAMPLE_BICUBIC = Image.BICUBIC


# ============================================================
# HELPERS
# ============================================================

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


def output_path_for(pdf_path: Path) -> Path:
    return pdf_path.with_name(f"{pdf_path.stem}_pro{pdf_path.suffix}")


def iter_pdf_files(target: Path, recursive: bool = False):
    if target.is_file():
        if target.suffix.lower() == ".pdf":
            yield target
        return

    if target.is_dir():
        pattern = "**/*.pdf" if recursive else "*.pdf"
        for pdf in sorted(target.glob(pattern)):
            if pdf.is_file():
                yield pdf
        return

    raise FileNotFoundError(f"Path not found: {target}")


def strip_metadata(doc: fitz.Document):
    try:
        doc.set_metadata({
            "title": "",
            "author": "",
            "subject": "",
            "keywords": "",
            "creator": "",
            "producer": "",
        })
    except Exception:
        pass


def parse_optional_page_number(value, field_name: str):
    """
    Accepts:
      - None
      - ""
      - integer
      - numeric string
    Returns:
      - None if blank
      - int otherwise
    """
    if value is None:
        return None

    if isinstance(value, str):
        value = value.strip()
        if value == "":
            return None

    try:
        page_num = int(value)
    except Exception:
        raise ValueError(f"{field_name} must be blank or a valid integer.")

    if page_num < 1:
        raise ValueError(f"{field_name} must be 1 or greater.")

    return page_num


def resolve_watermark_range(total_pages: int, start_page, end_page):
    """
    Page numbering is 1-based and inclusive.
    Blank start => 1
    Blank end   => total_pages
    """
    start = parse_optional_page_number(start_page, "Watermark start page")
    end = parse_optional_page_number(end_page, "Watermark end page")

    if start is None:
        start = 1
    if end is None:
        end = total_pages

    if start > total_pages:
        raise ValueError(
            f"Watermark start page ({start}) exceeds total pages ({total_pages})."
        )
    if end > total_pages:
        raise ValueError(
            f"Watermark end page ({end}) exceeds total pages ({total_pages})."
        )
    if start > end:
        raise ValueError(
            f"Watermark start page ({start}) cannot be greater than end page ({end})."
        )

    return start, end


def make_tiled_watermark_overlay(
    width: int,
    height: int,
    text: str,
    angle: int,
    opacity: int
) -> Image.Image:
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


def add_repeated_watermark(
    base_image: Image.Image,
    text: str,
    angle: int,
    opacity: int
) -> Image.Image:
    base = base_image.convert("RGBA")
    overlay = make_tiled_watermark_overlay(
        base.width,
        base.height,
        text=text,
        angle=angle,
        opacity=opacity
    )
    combined = Image.alpha_composite(base, overlay)
    return combined.convert("RGB")


def pil_to_jpeg_bytes(img: Image.Image, quality: int) -> bytes:
    bio = io.BytesIO()
    img.save(
        bio,
        format="JPEG",
        quality=quality,
        optimize=True,
        progressive=True
    )
    return bio.getvalue()


# ============================================================
# CORE PDF PROTECTION LOGIC
# ============================================================

def protect_pdf(
    input_pdf: Path,
    password: str,
    watermark_text: str,
    dpi: int,
    jpeg_quality: int,
    watermark_opacity: int,
    watermark_angle: int,
    watermark_start_page,
    watermark_end_page
) -> Path:
    if not input_pdf.exists():
        raise FileNotFoundError(f"Input PDF not found: {input_pdf}")

    if input_pdf.suffix.lower() != ".pdf":
        raise ValueError(f"Not a PDF file: {input_pdf}")

    output_pdf = output_path_for(input_pdf)

    src = fitz.open(str(input_pdf))
    out = fitz.open()

    try:
        total_pages = len(src)
        wm_start, wm_end = resolve_watermark_range(
            total_pages=total_pages,
            start_page=watermark_start_page,
            end_page=watermark_end_page
        )

        scale = dpi / 72.0
        matrix = fitz.Matrix(scale, scale)

        for page_index in range(total_pages):
            page = src[page_index]
            page_number = page_index + 1  # 1-based numbering

            # Rasterize page -> removes live/selectable text in output
            pix = page.get_pixmap(matrix=matrix, alpha=False, colorspace=fitz.csRGB)
            img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")

            # Apply watermark only within configured page range
            if wm_start <= page_number <= wm_end:
                img = add_repeated_watermark(
                    img,
                    text=watermark_text,
                    angle=watermark_angle,
                    opacity=watermark_opacity
                )

            # Compress for smaller file size
            jpeg_bytes = pil_to_jpeg_bytes(img, quality=jpeg_quality)

            # Preserve original page dimensions
            rect = page.rect
            new_page = out.new_page(width=rect.width, height=rect.height)
            new_page.insert_image(rect, stream=jpeg_bytes)

        strip_metadata(out)

        permissions = 0
        permissions |= int(getattr(fitz, "PDF_PERM_PRINT", 0))
        permissions |= int(getattr(fitz, "PDF_PERM_PRINT_HQ", 0))

        out.save(
            str(output_pdf),
            garbage=4,
            clean=True,
            deflate=True,
            encryption=fitz.PDF_ENCRYPT_AES_256,
            owner_pw=password,
            user_pw=password,
            permissions=permissions
        )

    finally:
        out.close()
        src.close()

    return output_pdf


def process_target(
    target_path: str,
    password: str,
    watermark_text: str,
    dpi: int,
    jpeg_quality: int,
    watermark_opacity: int,
    watermark_angle: int,
    watermark_start_page,
    watermark_end_page,
    recursive: bool
):
    target = Path(target_path)

    pdfs = list(iter_pdf_files(target, recursive=recursive))
    if not pdfs:
        print("No PDF files found.")
        return

    success = 0
    failed = 0

    for pdf in pdfs:
        try:
            if pdf.name.lower().endswith(SKIP_SUFFIX):
                print(f"Skipping already processed file: {pdf}")
                continue

            out_path = output_path_for(pdf)
            if out_path.resolve() == pdf.resolve():
                print(f"Skipping invalid output mapping: {pdf}")
                continue

            print(f"Processing: {pdf}")
            result = protect_pdf(
                input_pdf=pdf,
                password=password,
                watermark_text=watermark_text,
                dpi=dpi,
                jpeg_quality=jpeg_quality,
                watermark_opacity=watermark_opacity,
                watermark_angle=watermark_angle,
                watermark_start_page=watermark_start_page,
                watermark_end_page=watermark_end_page
            )
            print(f"Created: {result}\n")
            success += 1

        except Exception as e:
            failed += 1
            print(f"Failed: {pdf}")
            print(f"Reason: {e}\n")

    print("=" * 60)
    print(f"Done. Success: {success}, Failed: {failed}")
    print(f"Password used: {password}")


# ============================================================
# CLI
# ============================================================

def build_arg_parser():
    parser = argparse.ArgumentParser(
        description="Rasterize, watermark selected page range, compress, and encrypt PDF(s) into _pro.pdf output."
    )

    parser.add_argument(
        "path",
        nargs="?",
        default=DEFAULT_INPUT,
        help="Path to a PDF file or a folder containing PDFs."
    )

    parser.add_argument(
        "--password",
        default=DEFAULT_PASSWORD,
        help="Password used for both user and owner encryption."
    )

    parser.add_argument(
        "--watermark",
        default=DEFAULT_WATERMARK_TEXT,
        help="Watermark text."
    )

    parser.add_argument(
        "--dpi",
        type=int,
        default=DEFAULT_DPI,
        help="Rasterization DPI. Recommended 220 to 300."
    )

    parser.add_argument(
        "--jpeg-quality",
        type=int,
        default=DEFAULT_JPEG_QUALITY,
        help="JPEG quality from 1 to 95. Lower = smaller output."
    )

    parser.add_argument(
        "--opacity",
        type=int,
        default=DEFAULT_WATERMARK_OPACITY,
        help="Watermark opacity from 0 to 255. Lower = lighter."
    )

    parser.add_argument(
        "--angle",
        type=int,
        default=DEFAULT_WATERMARK_ANGLE,
        help="Watermark angle in degrees."
    )

    parser.add_argument(
        "--wm-start",
        default=DEFAULT_WATERMARK_START_PAGE,
        help='Watermark start page (1-based). Leave blank to start from page 1.'
    )

    parser.add_argument(
        "--wm-end",
        default=DEFAULT_WATERMARK_END_PAGE,
        help='Watermark end page (1-based). Leave blank to end at last page.'
    )

    parser.add_argument(
        "--recursive",
        action="store_true",
        default=DEFAULT_RECURSIVE,
        help="Recursively scan subfolders when input path is a folder."
    )

    return parser


def main():
    parser = build_arg_parser()
    args = parser.parse_args()

    if not (1 <= args.jpeg_quality <= 95):
        raise ValueError("jpeg-quality must be between 1 and 95.")

    if not (0 <= args.opacity <= 255):
        raise ValueError("opacity must be between 0 and 255.")

    if args.dpi < 100:
        raise ValueError("dpi must be at least 100.")

    process_target(
        target_path=args.path,
        password=args.password,
        watermark_text=args.watermark,
        dpi=args.dpi,
        jpeg_quality=args.jpeg_quality,
        watermark_opacity=args.opacity,
        watermark_angle=args.angle,
        watermark_start_page=args.wm_start,
        watermark_end_page=args.wm_end,
        recursive=args.recursive
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Error: {exc}")
        sys.exit(1)
