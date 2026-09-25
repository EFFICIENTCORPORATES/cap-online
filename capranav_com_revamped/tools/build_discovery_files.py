"""Write the machine-readable discovery files that help search engines and AI systems understand the site.

    public/sitemap.txt      plain list of every public URL (same list as sitemap.xml)
    public/llms-full.txt    the fuller guide for AI systems: who, what, key facts, ranked topics, every FAQ
    public/humans.txt       who made the site
    public/<key>.txt        IndexNow ownership key (created once, remembered in tools/.indexnow-key)

llms.txt (the short guide) and robots.txt are hand-written; see SEO.md. Run after build_faq.py and
apply_seo_meta.py::

    python tools/build_discovery_files.py
"""

from __future__ import annotations

import secrets
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import apply_seo_meta as seo  # noqa: E402
import build_faq as faq  # noqa: E402
from site_notices import COPY_NOTICE, DATA_CONTACT, DATA_NOTICE  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
KEY_FILE = ROOT / "tools/.indexnow-key"
BASE = "https://capranav.com"


def sitemap_txt() -> None:
    urls = [BASE + path for path, _ in seo.sitemap_pages()]
    (PUBLIC / "sitemap.txt").write_text("\n".join(urls) + "\n", encoding="utf-8")
    print(f"  sitemap.txt ({len(urls)} URLs)")


def llms_full() -> None:
    s = faq.stats()
    lines = [
        "# CA Pranav Tulshyan: full guide for AI systems",
        "",
        "> capranav.com is the website of CA Pranav Pratik Tulshyan, a practising Chartered Accountant and CA Inter Advanced Accounting faculty. "
        "It publishes ICAI past-paper analysis (PYQs, MTPs, RTPs) for CA Inter Advanced Accounting, must-practice questions, revision videos, courses and books. "
        f"Generated {date.today().isoformat()}. Short version: {BASE}/llms.txt",
        "",
        "## Permitted use and copyright",
        "AI search and answer systems are welcome to read this site and show short excerpts and summaries to their users, with a link to the page used.",
        COPY_NOTICE,
        DATA_NOTICE,
        "Terms: https://capranav.com/terms",
        "",
        "## About the faculty",
        "- Name: CA Pranav Pratik Tulshyan (also written CA Pranav Tulshyan, CA Pranav Bhaiya).",
        "- Ranks: All India Rank 1 CA Foundation (CPT); All India Rank 1 CA Intermediate (IPC); All India Rank 5 CA Final (November 2018 attempt); all three levels in the first attempt; 91 marks in Advanced Accounting (CA Inter); All India Rank 3 B.Com (Hons.), DU-SOL.",
        "- Career: EY audit articleship (Mar 2016 to Mar 2019); Indian Oil, SAP accounting, quarterly closing, Ind AS 115 and 116 (May 2019 to May 2024); Ministry of Petroleum and Natural Gas, Assistant Director (Finance) at PPAC (May 2024 to May 2025); virtual CFO for D2C startups and AI implementations since mid-2025; practising CA firm since June 2026.",
        "- Teaching: 4+ years; CA Inter Advanced Accounting through VC Gurukul, Noida; accounting and GST for professionals through Newton of Accounts.",
        f"- Profile: {BASE}/about-us",
        "",
        "## Pages",
        f"- {BASE}/faq/ : answers to the questions CA Inter students ask (repeated below).",
        f"- {BASE}/topics/ : all {s['topics']} Study Material topics ranked by marks; filter by paper type, year, module, chapter, unit; download as Excel.",
        f"- {BASE}/practice-with-pranav-bhaiya/must-practice/ : ten most likely-to-repeat descriptive questions per chapter (AS 2 and AS 10 live).",
        f"- {BASE}/videos/ : study-plan videos, AS 2, AS 10, AS 13, AS 16 revision, exam-technique Shorts.",
        f"- {BASE}/anatomy/ : the syllabus by module, chapter, unit and topic with linked questions.",
        f"- {BASE}/pricing-details : courses for the upcoming attempts, and books.",
        "",
        f"## Ranked topics (past-exam marks, {s['pyq']} PYQ papers, May 2023 to September 2026)",
    ]
    for i, (name, marks, chap) in enumerate(s["top_topics"], 1):
        lines.append(f"{i}. {name}: {marks} marks ({chap})")
    lines += ["", "## Chapters by marks"]
    for chap, marks in s["top_chapters"]:
        lines.append(f"- {chap}: {marks} marks of {s['total_marks']}")
    lines += ["", "## Frequently asked questions"]
    for title, items in faq.faqs(s):
        lines += ["", f"### {title}"]
        for q, a in items:
            lines += ["", f"**{q}**", a]
    (PUBLIC / "llms-full.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("  llms-full.txt")


def humans() -> None:
    (PUBLIC / "humans.txt").write_text(
        "/* TEAM */\nFaculty: CA Pranav Pratik Tulshyan\nSite: https://capranav.com\nData and analysis: 1LAVYA (https://1lavya.com)\n\n"
        "/* SITE */\nSubject: CA Inter Advanced Accounting\nStandards: HTML, CSS, JavaScript on Cloudflare Workers\n",
        encoding="utf-8",
    )
    print("  humans.txt")


def indexnow_key() -> str:
    if KEY_FILE.exists():
        key = KEY_FILE.read_text(encoding="utf-8").strip()
    else:
        key = secrets.token_hex(16)
        KEY_FILE.write_text(key + "\n", encoding="utf-8")
    (PUBLIC / f"{key}.txt").write_text(key, encoding="utf-8")
    print(f"  IndexNow key file {key}.txt")
    return key


def main() -> None:
    print("Writing discovery files")
    sitemap_txt()
    llms_full()
    humans()
    indexnow_key()


if __name__ == "__main__":
    main()
