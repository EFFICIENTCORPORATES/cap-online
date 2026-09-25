"""Put the copying notice and the data-source notice on every page that shows the site's analysis or data,
and add the intellectual-property clause to the Terms page.

Idempotent: replaces its own block between ``legal:start`` / ``legal:end`` markers. The FAQ page gets the same
notice from build_faq.py. Wording lives in tools/site_notices.py.

    python tools/apply_legal_notice.py
"""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_notices import COPY_NOTICE, DATA_CONTACT, DATA_NOTICE, TERMS_TEXT  # noqa: E402

PUBLIC = Path(__file__).resolve().parents[1] / "public"
START, END = "<!-- legal:start -->", "<!-- legal:end -->"
PAGES = [
    "topics/index.html",
    "anatomy/index.html",
    "videos/index.html",
    "practice-with-pranav-bhaiya/index.html",
    "practice-with-pranav-bhaiya/must-practice/index.html",
]


def notice_html() -> str:
    data = html.escape(DATA_NOTICE).replace(
        DATA_CONTACT, f'<a href="mailto:{DATA_CONTACT}">{DATA_CONTACT}</a>'
    )
    return f'{START}<p class="legal">{html.escape(COPY_NOTICE)} <a href="/terms">Terms</a></p><p class="legal">{data}</p>{END}'


def apply_footer(rel: str) -> None:
    p = PUBLIC / rel
    s = p.read_text(encoding="utf-8")
    s = re.sub(re.escape(START) + r".*?" + re.escape(END), "", s, flags=re.S)
    m = re.search(r"</footer>", s)
    assert m, f"{rel}: no footer"
    s = s[: m.start()] + notice_html() + s[m.start():]
    p.write_text(s, encoding="utf-8")
    print(f"  {rel}")


def apply_terms() -> None:
    p = PUBLIC / "terms.html"
    s = p.read_text(encoding="utf-8")
    block = (
        f"{START}<h3>Intellectual property and permitted use</h3>"
        f"<p>{html.escape(TERMS_TEXT)}</p>"
        f'<p>{html.escape(DATA_NOTICE).replace(DATA_CONTACT, f"<a href=\'mailto:{DATA_CONTACT}\'>{DATA_CONTACT}</a>")}</p>{END}\n\n        '
    )
    s = re.sub(re.escape(START) + r".*?" + re.escape(END) + r"\s*", "", s, flags=re.S)
    anchor = "<h3>No guaranteed outcome</h3>"
    assert anchor in s
    s = s.replace(anchor, block + anchor, 1)
    s = re.sub(r"Last updated: [A-Za-z]+ \d+, \d{4}\.", "Last updated: September 25, 2026.", s, count=1)
    p.write_text(s, encoding="utf-8")
    print("  terms.html")


def main() -> None:
    for rel in PAGES:
        apply_footer(rel)
    apply_terms()
    print("Legal notices applied")


if __name__ == "__main__":
    main()
