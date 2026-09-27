"""Build /faq: the questions CA Inter students most often ask about Advanced Accounting and about CA Pranav,
answered in plain HTML that search and AI crawlers can read, with matching FAQPage structured data.

Numbers (top chapters, top topics, how many papers, how often ICAI follows its Study Material) are computed from
the same data as /topics/, so the page cannot drift from the analysis. Career and rank facts are the ones
confirmed by Pranav (see PROJECT-LOG.md). Nothing here names a client.

Run after the data or the facts change::

    python tools/build_faq.py
    python tools/apply_seo_meta.py      # head block + sitemap (the FAQ page is in its PAGES table)
    python tools/build_discovery_files.py
    npx wrangler deploy
"""

from __future__ import annotations

import collections
import html
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_notices import COPY_NOTICE, DATA_CONTACT, DATA_NOTICE, SITE_CONTACT  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "capranav_com_revamped"
PRIORITY = ROOT / "books/ca-inter/smat-may-27-edition/practice-with-pranav-bhaiya/data/descriptive_topic_priority.json"
OUT = SITE / "public/faq/index.html"
BASE = "https://capranav.com"

e = lambda s: html.escape(str(s), quote=True)


def stats() -> dict:
    d = json.loads(PRIORITY.read_text(encoding="utf-8"))
    ranks = sorted(d["topic_rankings"], key=lambda t: t["overall_rank"])
    chapters = collections.Counter()
    for t in d["topic_rankings"]:
        chapters[t["chapter_name"]] += t["pyq_allocated_marks"]
    cls = collections.Counter(c["category"] for c in d["question_classifications"])
    n = len(d["question_classifications"])
    labels = {r["paper_label"]: r["paper_type"] for r in d["question_topic_rows"]}
    kinds = collections.Counter(labels.values())
    return {
        "top_topics": [(t["topic_name"], round(t["pyq_allocated_marks"]), t["chapter_name"]) for t in ranks[:10]],
        "top_chapters": [(c, round(m)) for c, m in chapters.most_common(5)],
        "total_marks": round(sum(chapters.values())),
        "questions": n,
        "cat_a": cls["A"], "cat_b": cls["B"],
        "pct_ab": round(100 * (cls["A"] + cls["B"]) / n),
        "pyq": len(d["metadata"]["ranking_scope"]),
        "mtp": kinds["MTP"], "rtp": kinds["RTP"],
        "topics": d["metadata"]["study_topic_count"],
    }


def faqs(s: dict) -> list[tuple[str, list[tuple[str, str]]]]:
    tt = "; ".join(f"{n} ({m} marks)" for n, m, _ in s["top_topics"][:6])
    tc = "; ".join(f"{c} ({m} marks)" for c, m in s["top_chapters"])
    return [
        ("About CA Pranav", [
            ("Who is CA Pranav Pratik Tulshyan?",
             "CA Pranav Pratik Tulshyan is a practising Chartered Accountant and a CA Inter Advanced Accounting faculty. He secured All India Rank 1 in CA Foundation (CPT), All India Rank 1 in CA Intermediate (IPC) and All India Rank 5 in CA Final, cleared all three levels in the first attempt, and scored 91 marks in Advanced Accounting at CA Intermediate. He teaches through VC Gurukul, Noida."),
            ("Is CA Pranav a good Accounts faculty for CA Inter?",
             "There is no official ranking of faculty, so the honest answer is to judge by record and by teaching. His record: AIR 1 in CA Foundation, AIR 1 in CA Intermediate, AIR 5 in CA Final, 91 in Advanced Accounting, all levels cleared in the first attempt, plus real work in audit and corporate accounting (see the next answers). To judge his teaching, use the free material on this site first: the important-topics ranking, the must-practice questions and the revision videos."),
            ("What are CA Pranav's ranks and results?",
             "All India Rank 1 in CA Foundation (CPT); All India Rank 1 in CA Intermediate (IPC); All India Rank 5 in CA Final (qualified in the November 2018 attempt); all three CA levels cleared in the first attempt; 91 marks in Advanced Accounting at CA Intermediate; All India Rank 3 in B.Com (Hons.) at DU-SOL."),
            ("Where has CA Pranav worked?",
             "Three years of audit at EY (articleship, March 2016 to March 2019); five years at Indian Oil (May 2019 to May 2024) working on SAP accounting, quarterly books closing and the implementation of Ind AS 115 and Ind AS 116; and one year at the Ministry of Petroleum and Natural Gas as Assistant Director (Finance) at PPAC (May 2024 to May 2025). Since mid-2025 he has worked as a virtual CFO for D2C startups and on AI implementations."),
            ("Is CA Pranav a practising Chartered Accountant?",
             "Yes. He has held a Certificate of Practice and has run his own CA firm since June 2026."),
            ("How and where does CA Pranav teach?",
             "He teaches CA Inter Advanced Accounting through VC Gurukul, Noida, and offers a Live + Recorded course on this site for the upcoming CA Inter attempts. He also teaches accounting and GST to working professionals through Newton of Accounts. Current batches and prices are on the pricing page."),
        ]),
        ("CA Inter Advanced Accounting: the exam", [
            ("What is the exam pattern of CA Inter Advanced Accounting?",
             "Advanced Accounting is a 100-mark paper. Part I carries 30 marks of case-scenario based multiple-choice questions and is compulsory. Part II carries 70 marks of descriptive questions, and the paper offers a choice of questions so a student attempts the required number. Recent papers have used 14-mark descriptive questions."),
            ("What is the syllabus of CA Inter Advanced Accounting?",
             f"The ICAI Study Material is organised in 3 modules and 36 chapters and units (each Accounting Standard is a unit), with {s['topics']} topics in all. It covers the Framework for Financial Statements, Accounting Standards (for example AS 2 Valuation of Inventories, AS 10 Property, Plant and Equipment, AS 13 Investments, AS 16 Borrowing Costs), financial statements of companies, cash flow statements, consolidation, amalgamation, buy-back, reconstruction and branch accounting, with an introduction to Ind AS."),
            ("Which chapters carry the most marks in Advanced Accounting?",
             f"Across the {s['pyq']} past papers analysed (May 2023 to September 2026), marks by chapter were: {tc}. Marks are allocated to topics by splitting each question's marks equally across the topics it tests."),
            ("Which topics are the most important in Advanced Accounting?",
             f"By marks in ICAI's past papers, the top topics are: {tt}. The full ranked list of all {s['topics']} topics, which you can filter by year, paper type, module, chapter and unit and download as Excel, is on the Important Topics page."),
            ("What are PYQ, MTP and RTP?",
             "PYQ means Past Year Question: a question from an actual ICAI exam. MTP is a Mock Test Paper and RTP is a Revision Test Paper; both are published by ICAI before each attempt and signal what ICAI is thinking about for the coming exam. RTP questions carry no printed marks."),
            ("How many past papers has CA Pranav analysed?",
             f"{s['pyq']} PYQ papers (May 2023 to September 2026), {s['mtp']} MTP sets and {s['rtp']} RTP papers: {s['questions']} descriptive questions, each mapped to its exact chapter, unit and topic in the ICAI Study Material."),
            ("How often does ICAI follow its own Study Material in the exam?",
             f"In this analysis, {s['cat_a']} of {s['questions']} descriptive questions are at least 90 percent similar to a question in ICAI's Study Material (category A) and a further {s['cat_b']} are 50 to 90 percent similar (category B). Together that is about {s['pct_ab']} percent, roughly three in ten. Practising the Study Material's illustrations and questions therefore matters."),
            ("What is the difference between AS and Ind AS in CA Inter?",
             "CA Inter Advanced Accounting is built mainly on the Accounting Standards (AS) issued in India. Ind AS, the Indian Accounting Standards aligned with IFRS, appear as an introduction in the first chapter (for example carve-outs and carve-ins). Ind AS is studied in depth at CA Final."),
        ]),
        ("Preparing and practising", [
            ("How should I prepare for CA Inter Advanced Accounting?",
             "CA Pranav's method is concept first, then application: understand each topic from the Study Material, solve the ICAI illustrations, practise the questions that ICAI has actually set (PYQs, MTPs, RTPs) starting with the highest-ranked topics, and revise regularly. His 90-day preparation strategy and daily study routine videos are on the Videos page."),
            ("Where can I find the most important questions to practise?",
             "The Must Practice page lists, for each chapter, the ten descriptive questions most likely to be set again, with the reason each was chosen. AS 2 (Valuation of Inventories) and AS 10 (Property, Plant and Equipment) are live; other chapters are being added."),
            ("Where can I get the list of important topics as Excel?",
             "On the Important Topics page. Choose the papers, years, modules, chapters and units you want and download the list, or download ready-made lists: Top 100 topics, MTP-wise, RTP-wise and PYQ-wise topic lists, and the full workbook sheets."),
            ("How do I read a topic ID such as M2-C5-U2-T2.6?",
             "It reads like an address: Module 2, Chapter 5, Unit 2, topic 6 of Unit 2. That topic is Measurement of PPE in AS 10, on page 5.27 of the ICAI Study Material (chapter 5, page 27). A U0 means the chapter has only one unit. Hyphens and underscores mean the same thing."),
            ("Which chapters have revision videos?",
             "AS 2 Inventories, AS 10 Property, Plant and Equipment, AS 13 Accounting for Investments and AS 16 Borrowing Costs, plus study-plan videos and exam-technique Shorts, all playable on the Videos page."),
            ("Is there free practice available?",
             "Yes. The important-topics explorer, the must-practice questions and the videos are free, and free MCQ and descriptive practice is available on Telegram through @CAPranavExamBot."),
        ]),
        ("Books and using this site", [
            ("Which books has CA Pranav written?",
             "The Question Bank Book (every CA Inter Advanced Accounting question from MTPs, RTPs and PYQs, organised chapter by chapter with topic tags) and the Exam Strategy Book. Printed copies are on the pricing page; the Question Bank e-book is sold through VC Gurukul's store."),
            ("How can I contact CA Pranav?",
             f"Email {SITE_CONTACT} or use the contact form on the Contact Us page, for anything about this site, the CA Inter Advanced Accounting syllabus or the courses."),
            ("Who provides the data and analysis on this site?",
             "The data and analysis are sourced from the 1LAVYA data repository (1lavya.com) and published here by CA Pranav Tulshyan."),
            ("Is copying content from this website allowed?",
             "No. Copying, scraping, mirroring, bulk downloading or republishing any content on this site (pages, questions, answers, analysis, datasets, books, slides) is not permitted without written permission. You may read it, use it for your own study, and quote short excerpts with a link to capranav.com. Search engines and AI search and answer systems may read the site and show short excerpts to their users with attribution. The full wording is in the Terms of Service."),
            ("Can faculty or institutes use these lists and mappings on their own website?",
             f"The data behind this site's analysis comes from the 1LAVYA data repository. Faculty or institutes who want these important-question lists and syllabus mappings white-labelled on their own website can contact 1LAVYA at {DATA_CONTACT}."),
        ]),
    ]


CSS = """
.faq-wrap{max-width:820px;margin:0 auto;padding:0 clamp(16px,4vw,32px) 60px}
.faq-wrap h2{margin:42px 0 6px;font-size:1.5rem;letter-spacing:-.02em}
.faq-wrap h3{margin:26px 0 6px;font-size:1.08rem}
.faq-wrap p{margin:0 0 6px;color:var(--ink);line-height:1.65}
.faq-toc{display:flex;flex-wrap:wrap;gap:8px 16px;margin:16px 0 8px;padding:0;list-style:none}
.faq-toc a{font-weight:700;color:var(--green)}
.faq-meta{color:var(--muted);font-size:.86rem}
.faq-links{margin:34px 0 0;padding:18px 20px;background:var(--lime);border-radius:14px}
.faq-links a{font-weight:700;color:var(--green)}
"""


def build() -> None:
    s = stats()
    groups = faqs(s)
    today = date.today().isoformat()
    body, entities = [], []
    toc = []
    for gi, (title, items) in enumerate(groups):
        anchor = f"g{gi}"
        toc.append(f'<li><a href="#{anchor}">{e(title)}</a></li>')
        body.append(f'<h2 id="{anchor}">{e(title)}</h2>')
        for q, a in items:
            body.append(f"<h3>{e(q)}</h3><p>{e(a)}</p>")
            entities.append({"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}})
    ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": entities}
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Caveat:wght@600;700&family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/anatomy.css">
<style>{CSS}</style>
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
</head>
<body>
  <header class="topbar">
    <a class="brand" href="/"><span>P</span> CA PRANAV</a>
    <a class="back" href="/">Home</a>
  </header>
  <main class="faq-wrap">
    <section class="hero" style="padding:44px 0 6px">
      <p class="kicker">CA Inter &middot; Advanced Accounting</p>
      <h1>Questions students ask <em>about CA Inter Accounts</em></h1>
      <p class="intro">Straight answers about the Advanced Accounting paper, the most important topics, how to practise, and about CA Pranav Tulshyan, the faculty behind this site. Figures come from the analysis of {s['pyq']} PYQ papers, {s['mtp']} MTP sets and {s['rtp']} RTP papers.</p>
      <p class="faq-meta">Last updated {today}.</p>
      <p class="faq-meta">{e(COPY_NOTICE)} <a href="/terms">Terms</a></p>
    </section>
    <ul class="faq-toc">{"".join(toc)}</ul>
    {"".join(body)}
    <div class="faq-links">
      <p><a href="/topics/">Important Topics (filter and download)</a> &middot; <a href="/practice-with-pranav-bhaiya/must-practice/">Must Practice Questions</a> &middot; <a href="/videos/">Videos and Shorts</a> &middot; <a href="/about-us">About CA Pranav</a> &middot; <a href="/pricing-details">Courses and books</a> &middot; <a href="/contact-us">Contact</a></p>
    </div>
  </main>
  <footer>CA Pranav Pratik Tulshyan &middot; CA Inter Advanced Accounting<p class="powered">Powered by <a href="https://1lavya.com/?utm_source=capranav&amp;utm_medium=referral&amp;utm_campaign=powered_by&amp;utm_content=faq" target="_blank" rel="noopener">1LAVYA</a> &middot; this analysis is built from the 1LAVYA data repository</p><p class="legal">{e(DATA_NOTICE)}</p></footer>
</body>
</html>
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(page, encoding="utf-8")
    n = sum(len(i) for _, i in groups)
    print(f"Wrote {OUT} with {n} questions")


if __name__ == "__main__":
    build()
