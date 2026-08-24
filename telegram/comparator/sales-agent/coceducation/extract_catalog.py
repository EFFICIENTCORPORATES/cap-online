"""
Parses the coceducation.com site mirror (site-mirror/course_details/*.html) into one
structured JSON catalog the sales-agent bot can actually query.

Why this exists: the mirrored HTML is a full page dump (inline CSS/JS, a "related
products" carousel repeated on every page) — nothing in this repo could answer a
student's question directly against 421 x ~900KB HTML files. This script extracts just
the real, per-course facts (title, faculty, price, discount, purchase attributes,
highlights table, real course URL) into one small JSON file that IS the bot's knowledge
base going forward. Re-run this any time the client's course_details mirror is refreshed
— never hand-edit catalog.json, it will drift from the source HTML.

Source of truth for fields: verified by hand against
`site-mirror/course_details/accounting-by-ca-cma-santosh-kumar.html` before writing the
parser (see the conversation this was built in) — the <div class="detail-info"> block
is the per-course record; everything before/after it in the file is shared page chrome
(header/footer/related-products carousel) and is deliberately ignored.

Usage:
    .venv/Scripts/python extract_catalog.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from bs4 import BeautifulSoup

HERE = Path(__file__).resolve().parent
COURSE_DIR = HERE / "site-mirror" / "course_details"
ABOUT_HTML = HERE / "site-mirror" / "home" / "about.html"
CONTACT_HTML = HERE / "site-mirror" / "home" / "contact.html"
PRODUCT_DIR = HERE / "site-mirror" / "product"
OUT_PATH = HERE / "catalog.json"

BASE_URL = "https://coceducation.com"

# Exam-group listing pages under site-mirror/product/ — each links to the
# course_details slugs that belong to that exam. Used to tag each course with which
# exam it's for (the course pages themselves don't state this anywhere else).
EXAM_GROUP_PAGES = {
    "CA": PRODUCT_DIR / "CA.html",
    "CMA": PRODUCT_DIR / "cma.html",
    "CFM": PRODUCT_DIR / "cfm.html",
    "Other": PRODUCT_DIR / "other-course.html",
}

SLUG_RE = re.compile(r'href="[^"]*course_details/([^".]+)\.html"')

EXAM_GROUP_MAP: dict[str, str] = {}  # populated by main() before any file is parsed

TITLE_RE = re.compile(r'class="title-detail"[^>]*>(.*?)</h[0-9]>', re.DOTALL)


def build_exam_group_map() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for group, page in EXAM_GROUP_PAGES.items():
        if not page.exists():
            continue
        text = page.read_text(encoding="utf-8", errors="replace")
        for slug in SLUG_RE.findall(text):
            # first group a slug appears under wins; listing pages don't overlap
            # in practice, but this keeps behavior deterministic if they ever do
            mapping.setdefault(slug, group)
    return mapping


def clean(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def parse_course_file(path: Path) -> dict | None:
    html = path.read_text(encoding="utf-8", errors="replace")
    # Only the <body> is needed (title/price/highlights all live there) — the <head>
    # carries hundreds of KB of inlined CSS that lxml would otherwise still have to
    # walk. Slicing it out is what makes parsing 421 files finish in seconds, not
    # minutes (measured: html.parser over the full document was the bottleneck).
    body_start = html.find("<body")
    soup = BeautifulSoup(html[body_start:] if body_start != -1 else html, "lxml")

    detail = soup.select_one("div.detail-info")
    if detail is None:
        return None  # page didn't render a product record (broken/placeholder page)

    # Regex, not the parsed tree: the source markup has a real bug — every course page
    # opens this element as <h4 class="title-detail" ...> but closes it as </h3>. lxml
    # (unlike a browser's lenient HTML5 tree-builder) treats the mismatched </h3> as
    # not closing the h4 at all, so h4.get_text() silently swallows everything that
    # follows in the document (price, buttons, even the unrelated "related products"
    # carousel) instead of just the title. A tag-agnostic regex sidesteps the bug
    # entirely rather than trying to out-guess the parser's recovery behavior.
    title_match = TITLE_RE.search(html)
    title = clean(title_match.group(1)) if title_match else ""
    if not title:
        return None

    category_el = detail.select_one(".product-category a")
    category_tag = clean(category_el.get_text()) if category_el else ""

    price_el = detail.select_one("#product_price_value")
    mrp_el = detail.select_one("#product_regular_value")
    discount_el = detail.select_one("#percentage_offer")

    def to_int(el, strip_chars="₹, "):
        if el is None:
            return None
        raw = clean(el.get_text()).strip(strip_chars).replace(",", "")
        try:
            return int(float(raw))
        except ValueError:
            return None

    price = to_int(price_el)
    mrp = to_int(mrp_el)
    discount_pct = to_int(discount_el, strip_chars=" %")

    # Purchase attributes (Mode of Distribution, Attempt, etc.) — each is one
    # <select> with a data-attribute-name and a list of <option> choices.
    attributes = {}
    for row in detail.select(".attribute-row"):
        label_el = row.select_one("strong")
        select_el = row.select_one("select")
        if label_el is None or select_el is None:
            continue
        label = clean(label_el.get_text()).rstrip(":")
        options = [clean(o.get_text()) for o in select_el.select("option") if clean(o.get_text())]
        if label and options:
            attributes[label] = options

    # Highlights table: repeating (h6 label, value text) pairs inside tab-1-highlights.
    highlights = {}
    highlights_pane = soup.select_one("#tab-1-highlights")
    if highlights_pane:
        for container in highlights_pane.find_all("div", class_="MuiGrid-container", recursive=True):
            label_el = container.select_one("h6")
            if label_el is None:
                continue
            label = clean(label_el.get_text())
            if not label:
                continue
            # value = every text-bearing leaf div AFTER the label's own grid item
            value_parts = []
            for value_div in container.select(".MuiGrid-item"):
                if value_div.select_one("h6") is not None:
                    continue  # this is the label's own grid item, skip it
                text = clean(value_div.get_text(separator=" | "))
                if text:
                    value_parts.append(text)
            value = " ".join(value_parts)
            if value:
                highlights[label] = value

    # Faculty name: highlights table has no explicit "Faculty" row on this theme —
    # it's always embedded in the title as "... By <Faculty Name>". Extract it that
    # way (case-insensitive " by "), falling back to "" (unknown) rather than guessing.
    faculty = ""
    m = re.search(r"\bby\b\s+(.+)$", title, flags=re.IGNORECASE)
    if m:
        faculty = clean(m.group(1))

    slug = path.stem  # filename without .html — matches the real site's URL slug
    return {
        "slug": slug,
        "title": title,
        "faculty": faculty,
        "exam_group": EXAM_GROUP_MAP.get(slug, "Other"),
        "category_tag": category_tag,
        "price_inr": price,
        "mrp_inr": mrp,
        "discount_pct": discount_pct,
        "attributes": attributes,
        "highlights": highlights,
        "url": f"{BASE_URL}/course_details/{slug}",
    }


def parse_org_info() -> dict:
    info = {
        "name": "COC Education Pvt. Ltd.",
        "domain": BASE_URL,
        "about": "",
        "contact": {
            "call_sales": ["+91-9999631597", "+91-7303445575", "+91-9217265617", "+91-7011668629"],
            "purchase_enquiry": "+91-8448322142",
            "tech_login_support": "+91-9811455109",
            "whatsapp": "+91-9999631597",
        },
    }
    if ABOUT_HTML.exists():
        soup = BeautifulSoup(ABOUT_HTML.read_text(encoding="utf-8", errors="replace"), "html.parser")
        for p in soup.find_all("p"):
            text = clean(p.get_text())
            if "COC Education provides" in text:
                info["about"] = text
                break
    return info


def main() -> None:
    if not COURSE_DIR.exists():
        raise SystemExit(f"course_details folder not found: {COURSE_DIR}")

    global EXAM_GROUP_MAP
    EXAM_GROUP_MAP = build_exam_group_map()

    courses = []
    skipped = []
    for path in sorted(COURSE_DIR.glob("*.html")):
        record = parse_course_file(path)
        if record is None:
            skipped.append(path.name)
        else:
            courses.append(record)

    catalog = {
        "client_slug": "coceducation",
        "generated_from": str(COURSE_DIR.relative_to(HERE.parent.parent.parent.parent)),
        "org": parse_org_info(),
        "course_count": len(courses),
        "courses": courses,
    }

    OUT_PATH.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(courses)} courses to {OUT_PATH}")
    if skipped:
        print(f"Skipped {len(skipped)} file(s) with no parseable product record:")
        for name in skipped[:20]:
            print(f"  - {name}")
        if len(skipped) > 20:
            print(f"  ... and {len(skipped) - 20} more")


if __name__ == "__main__":
    main()
