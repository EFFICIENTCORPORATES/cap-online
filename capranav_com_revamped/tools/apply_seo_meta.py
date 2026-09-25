"""Write the SEO / AI-readability <head> block on every public page.

One table (PAGES) is the source of truth for each page's title, description and
canonical URL. Running this replaces the page's <title>, <meta name="description">
and any earlier block between the ``seo:start`` / ``seo:end`` markers with:

* the title and description
* a canonical link (clean URL, no .html)
* Open Graph and Twitter share tags
* JSON-LD (structured data) where the page states facts about a real entity
* ``robots noindex`` for private pages (admin, dashboard, reader)

Idempotent: safe to re-run after editing PAGES. Claims in the JSON-LD are limited to
facts already stated on the live site or confirmed by Pranav (career dates confirmed 2026-09-25).
Clients are never named, only described (Fortune 500, a top metals and mining group).

Run from capranav_com_revamped::

    python tools/apply_seo_meta.py        # also rewrites public/sitemap.xml from the same table
    npx wrangler deploy
"""

from __future__ import annotations

import html
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
SITE = "https://capranav.com"
OG_IMAGE = f"{SITE}/assets/ca-pranav-professional.png"
PERSON_NAME = "CA Pranav Pratik Tulshyan"

START, END = "<!-- seo:start -->", "<!-- seo:end -->"

SAME_AS = [
    "https://www.linkedin.com/in/capranavptulshyan/",
    "https://www.instagram.com/capranavptulshyan/",
]

# (file relative to public/, canonical path, title, description, extra)
# extra: "noindex" for private pages, "home" for the homepage's structured data.
PAGES = [
    ("index.html", "/",
     "CA Pranav Tulshyan | Accounts Faculty for CA Inter | AIR 1 CA",
     "Advanced Accounting faculty for CA Inter: CA Pranav Tulshyan, AIR 1 (Foundation, Inter), AIR 5 (Final). "
     "Courses, books, important topics, must-practice questions, videos.", "home"),
    ("faq/index.html", "/faq/",
     "CA Inter Advanced Accounting FAQs: Exam Pattern, Important Topics, Faculty | CA Pranav",
     "Answers to what CA Inter students ask: Advanced Accounting exam pattern, most important chapters and topics, how to prepare, "
     "and who CA Pranav Tulshyan is. Figures from 35 ICAI papers.", ""),
    ("about-us.html", "/about-us",
     "About CA Pranav Pratik Tulshyan | EY, Indian Oil, Ministry of Petroleum | AIR 1 CA",
     "CA Pranav Pratik Tulshyan: AIR 1 in CA Foundation and Intermediate, AIR 5 in CA Final. Audit at EY, 5 years at Indian Oil "
     "(SAP, Ind AS 115 and 116), a year at the Ministry of Petroleum and Natural Gas, and 4+ years teaching Advanced Accounting.", ""),
    ("pricing-details.html", "/pricing-details",
     "Courses and Books: Pricing | CA Pranav Tulshyan",
     "Prices for CA Inter Advanced Accounting courses for the upcoming attempts, and books by CA Pranav Tulshyan, "
     "including the Question Bank and the Exam Strategy Book.", ""),
    ("contact-us.html", "/contact-us",
     "Contact CA Pranav Tulshyan | CA Inter Advanced Accounting",
     "Get in touch with CA Pranav Tulshyan about CA Inter Advanced Accounting courses, books and practice material.", ""),
    ("policies.html", "/policies",
     "Policies | CA Pranav Tulshyan",
     "Privacy, terms of service, refund and cancellation, and shipping policies for capranav.com.", ""),
    ("privacy.html", "/privacy",
     "Privacy Policy | CA Pranav Tulshyan",
     "How capranav.com collects, uses and protects your information.", ""),
    ("terms.html", "/terms",
     "Terms of Service | CA Pranav Tulshyan",
     "The terms that apply when you use capranav.com and buy its courses and books.", ""),
    ("cancellation-and-refund.html", "/cancellation-and-refund",
     "Cancellation and Refund Policy | CA Pranav Tulshyan",
     "Cancellation and refund rules for courses and books bought on capranav.com.", ""),
    ("shipping-and-exchange.html", "/shipping-and-exchange",
     "Shipping and Exchange Policy | CA Pranav Tulshyan",
     "Shipping timelines and exchange rules for printed books ordered on capranav.com.", ""),
    ("anatomy/index.html", "/anatomy/",
     "The Anatomy of CA Inter Advanced Accounting: Modules, Chapters, Topics | CA Pranav",
     "Explore the complete CA Inter Advanced Accounting syllabus and descriptive question bank by module, chapter, unit and topic.", ""),
    ("practice-with-pranav-bhaiya/index.html", "/practice-with-pranav-bhaiya/",
     "Practice with Pranav Bhaiya | CA Inter Advanced Accounting Class Slides",
     "Interactive class slides from the Practice with Pranav Bhaiya series for CA Inter Advanced Accounting, "
     "with links to must-practice questions and important topics.", ""),
    ("practice-with-pranav-bhaiya/must-practice/index.html", "/practice-with-pranav-bhaiya/must-practice/",
     "Must Practice Questions: CA Inter Advanced Accounting (AS 2, AS 10) | CA Pranav",
     "The must-practice descriptive questions for CA Inter Advanced Accounting, chosen from every MTP, RTP and PYQ "
     "and ranked by how likely the topic is to be set again.", ""),
    ("topics/index.html", "/topics/",
     "Important Topics in CA Inter Advanced Accounting, Ranked by Exam Marks | CA Pranav",
     "The most important CA Inter Advanced Accounting topics, ranked by marks in PYQs, MTPs and RTPs. "
     "Filter by year, module, chapter and unit, and download as Excel.", ""),
    ("videos/index.html", "/videos/",
     "CA Inter Advanced Accounting Videos and Shorts | CA Pranav Tulshyan",
     "Watch CA Pranav Tulshyan's study-plan videos, Advanced Accounting chapter revision (AS 2, AS 10, AS 13, AS 16) "
     "and exam-technique Shorts.", ""),
    ("practice-with-pranav-bhaiya/slides/day-01-marks-split.html", "/practice-with-pranav-bhaiya/slides/day-01-marks-split",
     "Day 1: How Marks Split in Advanced Accounting | Practice with Pranav Bhaiya",
     "Class slide from Practice with Pranav Bhaiya, Day 1: how the Advanced Accounting paper's marks are split.", ""),
    ("practice-with-pranav-bhaiya/slides/day-01-opening.html", "/practice-with-pranav-bhaiya/slides/day-01-opening",
     "Day 1: Opening | Practice with Pranav Bhaiya",
     "Opening slide of Practice with Pranav Bhaiya, Day 1, for CA Inter Advanced Accounting.", ""),
    ("practice-with-pranav-bhaiya/slides/day-01-syllabus-flow.html", "/practice-with-pranav-bhaiya/slides/day-01-syllabus-flow",
     "Day 1: Syllabus Flow | Practice with Pranav Bhaiya",
     "Class slide from Practice with Pranav Bhaiya, Day 1: how the Advanced Accounting syllabus flows.", ""),
    ("admin.html", "/admin", "Admin | CA Pranav", "Private.", "noindex"),
    ("dashboard.html", "/dashboard", "My Dashboard | CA Pranav", "Private.", "noindex"),
    ("reader.html", "/reader", "Reader | CA Pranav", "Private.", "noindex"),
]

# Pages that belong in sitemap.xml (everything public, i.e. not noindex).
def sitemap_pages():
    return [(path, extra) for _, path, _, _, extra in PAGES if extra != "noindex"]


def person_ld() -> dict:
    return {
        "@type": "Person",
        "@id": f"{SITE}/#pranav",
        "name": PERSON_NAME,
        "alternateName": ["CA Pranav Tulshyan", "CA Pranav Bhaiya"],
        "url": f"{SITE}/",
        "image": OG_IMAGE,
        "jobTitle": "Chartered Accountant and CA Inter Advanced Accounting faculty",
        "description": (
            "Practising Chartered Accountant and CA Inter Advanced Accounting faculty. All India Rank 1 in CA Foundation (CPT) and "
            "CA Intermediate (IPC), All India Rank 5 in CA Final, all three levels cleared in the first attempt, 91 marks in Advanced "
            "Accounting. Three years of audit at EY, five years at Indian Oil (SAP accounting, quarterly closing, Ind AS 115 and 116), "
            "one year at the Ministry of Petroleum and Natural Gas (PPAC), then virtual CFO work for D2C startups and AI implementations."
        ),
        "hasCredential": {"@type": "EducationalOccupationalCredential", "name": "Chartered Accountant (ICAI), qualified November 2018 attempt"},
        "memberOf": {"@type": "Organization", "name": "The Institute of Chartered Accountants of India (ICAI)"},
        "alumniOf": {"@type": "CollegeOrUniversity", "name": "University of Delhi, School of Open Learning (B.Com Hons.)"},
        "affiliation": {"@type": "Organization", "name": "VC Gurukul, Noida"},
        "award": [
            "All India Rank 1, CA Foundation (CPT)",
            "All India Rank 1, CA Intermediate (IPC)",
            "All India Rank 5, CA Final",
            "All India Rank 3, B.Com (Hons.), DU-SOL",
        ],
        "knowsAbout": ["Advanced Accounting", "CA Intermediate", "Accounting Standards", "Ind AS", "Ind AS 115", "Ind AS 116",
                       "Financial Reporting", "Consolidation of accounts", "Audit", "SAP accounting", "GST", "Virtual CFO services",
                       "CA exam preparation"],
        "sameAs": SAME_AS,
    }


def website_ld() -> dict:
    return {
        "@type": "WebSite",
        "@id": f"{SITE}/#website",
        "url": f"{SITE}/",
        "name": "CA Pranav Tulshyan: CA Inter Advanced Accounting",
        "inLanguage": "en-IN",
        "publisher": {"@id": f"{SITE}/#pranav"},
    }


def block_for(path: str, title: str, desc: str, extra: str) -> str:
    url = SITE + path
    t, d = html.escape(title, quote=True), html.escape(desc, quote=True)
    lines = [
        START,
        f"<title>{html.escape(title)}</title>",
        f'<meta name="description" content="{d}">',
        f'<link rel="canonical" href="{url}">',
    ]
    if extra == "noindex":
        lines.append('<meta name="robots" content="noindex, nofollow">')
    else:
        lines += [
            '<meta property="og:type" content="website">',
            '<meta property="og:site_name" content="CA Pranav Tulshyan">',
            f'<meta property="og:title" content="{t}">',
            f'<meta property="og:description" content="{d}">',
            f'<meta property="og:url" content="{url}">',
            f'<meta property="og:image" content="{OG_IMAGE}">',
            '<meta property="og:locale" content="en_IN">',
            '<meta name="twitter:card" content="summary_large_image">',
            f'<meta name="twitter:title" content="{t}">',
            f'<meta name="twitter:description" content="{d}">',
            f'<meta name="twitter:image" content="{OG_IMAGE}">',
        ]
    if extra == "home":
        graph = {"@context": "https://schema.org", "@graph": [website_ld(), person_ld()]}
        lines.append('<script type="application/ld+json">' + json.dumps(graph, ensure_ascii=False) + "</script>")
    elif extra != "noindex":
        page = {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "url": url,
            "name": title,
            "description": desc,
            "isPartOf": {"@id": f"{SITE}/#website"},
            "about": {"@type": "Thing", "name": "CA Inter Advanced Accounting"},
            "author": {"@id": f"{SITE}/#pranav"},
            "inLanguage": "en-IN",
            "copyrightHolder": {"@id": f"{SITE}/#pranav"},
            "copyrightYear": 2026,
            "usageInfo": f"{SITE}/terms",
        }
        lines.append('<script type="application/ld+json">' + json.dumps(page, ensure_ascii=False) + "</script>")
    lines.append(END)
    return "\n".join(lines)


def apply(file: str, path: str, title: str, desc: str, extra: str) -> None:
    p = PUBLIC / file
    s = p.read_text(encoding="utf-8")
    s = re.sub(re.escape(START) + r".*?" + re.escape(END) + r"\n?", "", s, flags=re.S)   # previous run
    s = re.sub(r"<title>.*?</title>\s*", "", s, count=1, flags=re.S)
    s = re.sub(r'<meta name="description"[^>]*>\s*', "", s, count=1)
    block = block_for(path, title, desc, extra) + "\n"
    m = re.search(r'<meta name="viewport"[^>]*>\s*', s)
    assert m, f"{file}: no viewport meta to anchor on"
    s = s[: m.end()] + block + s[m.end():]
    if not re.search(r"<html[^>]*\blang=", s):
        s = s.replace("<html", '<html lang="en"', 1)
    p.write_text(s, encoding="utf-8")


PRIORITY = {"/": "1.0", "/faq/": "0.9", "/topics/": "0.9", "/practice-with-pranav-bhaiya/must-practice/": "0.9", "/videos/": "0.8",
            "/about-us": "0.8", "/anatomy/": "0.7", "/pricing-details": "0.6"}


def write_sitemap() -> None:
    today = date.today().isoformat()
    urls = []
    for path, _ in sitemap_pages():
        urls.append(
            f"  <url><loc>{SITE}{path}</loc><lastmod>{today}</lastmod>"
            f"<priority>{PRIORITY.get(path, '0.4')}</priority></url>"
        )
    nl = chr(10)
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>' + nl
        + '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + nl
        + nl.join(urls) + nl
        + "</urlset>" + nl
    )
    (PUBLIC / "sitemap.xml").write_text(xml, encoding="utf-8")


def main() -> None:
    for page in PAGES:
        apply(*page)
        print(f"  {page[0]}")
    write_sitemap()
    print(f"Wrote SEO head blocks on {len(PAGES)} pages and sitemap.xml ({len(sitemap_pages())} URLs)")


if __name__ == "__main__":
    main()
