"""Build the Must Practice question JSON served at /practice-with-pranav-bhaiya/must-practice/.

Sources (all already reviewed and canonical, nothing is re-typed here):

* ``books/ca-inter/smat-may-27-edition/practice-with-pranav-bhaiya/data/mcq-library/``
  holds one descriptive-question file per unit, carrying the verbatim question
  and answer HTML from the Question Bank Book pipeline.
* ``.../data/descriptive_topic_priority.json`` holds the 400-topic ranking, the
  Top-100 priority bands and the per-question topic mapping.
* ``first_run/output/final_deliverable/CA Inter Advanced Accounts_ The Complete
  Question Bank_V1.pdf`` is the distributed book. Page numbers are read out of
  its own text layer by matching each question's printed header line, so a page
  number is never guessed or hand-maintained.

Run after any change to the sources, then deploy::

    python tools/build_must_practice_data.py
    npx wrangler deploy
"""

from __future__ import annotations

import json
import re
import unicodedata
from datetime import date
from pathlib import Path

import pypdf

ROOT = Path(__file__).resolve().parents[2]
PRACTICE = ROOT / "books/ca-inter/smat-may-27-edition/practice-with-pranav-bhaiya/data"
LIBRARY = PRACTICE / "mcq-library"
PRIORITY = PRACTICE / "descriptive_topic_priority.json"
BOOK_PDF = (
    ROOT
    / "first_run/output/final_deliverable"
    / "CA Inter Advanced Accounts_ The Complete Question Bank_V1.pdf"
)
OUTPUT = (
    ROOT
    / "capranav_com_revamped/public/practice-with-pranav-bhaiya/must-practice/data"
)

BOOK_EDITION = "CA Inter Advanced Accounts — The Complete Question Bank, First Edition (V1)"

# One entry per unit that is switched on. ``selection`` is the ordered shortlist;
# ``why`` is the reason that question earns its place, shown on the card.
UNITS = {
    "M2-C5-U1": {
        "library_file": "CA_Inter_AdvAcc_AS_2_Valuation_of_Inventories_17_Descriptive.json",
        "standard": "AS 2",
        "unit_title": "Valuation of Inventories",
        "module": "MODULE 2",
        "chapter": "Assets Based Accounting Standards",
        "selection": [
            ("M2C5U1-008", "Highest-ranked AS 2 topic (rank 40) and a 90% match to an ICAI Study Material question."),
            ("M2C5U1-002", "Newest MTP in the corpus and a Category A question — 93% identical to a Study Material question."),
            ("M2C5U1-015", "An RTP that carries three mapped topics at once, including the rank-40 NRV topic."),
            ("M2C5U1-006", "Normal versus abnormal loss, the most repeated AS 2 idea, at an 80% Study Material match."),
            ("M2C5U1-004", "Category A: 93.5% identical to a Study Material question on excluded costs."),
            ("M2C5U1-012", "ICAI lifted this one from the Study Material verbatim (100% match) once already."),
            ("M2C5U1-005", "The abnormal-waste computation in its most examined form, 80% Study Material match."),
            ("M2C5U1-013", "The most recent AS 2 question actually set in a PYQ, on the rank-40 topic."),
            ("M2C5U1-010", "The only question covering Joint and By-Products, and the largest at 7 marks."),
            ("M2C5U1-007", "Latest MTP, and the only recent hit on the retail method and NRV estimation."),
        ],
    }
}


def normalise(text: str) -> str:
    text = unicodedata.normalize("NFKD", re.sub(r"<[^>]+>", " ", text))
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def book_page_index() -> list[str]:
    reader = pypdf.PdfReader(str(BOOK_PDF))
    return [normalise(page.extract_text() or "") for page in reader.pages]


def resolve_page(pages: list[str], question: dict) -> int | None:
    """Locate a question by its printed header line, e.g.

    ``MTP May 2024 Set 2 · Q1(b) · Marks: 5``. Returns None rather than a guess
    when the header does not resolve to exactly one page.
    """
    anchor = normalise(question["src_text"] + question["qno_text"] + question["marks_text"])
    hits = [i + 1 for i, page in enumerate(pages) if anchor in page]
    return hits[0] if len(hits) == 1 else None


def topic_lookup(priority: dict) -> tuple[dict, dict]:
    ranks = {t["topic_id"]: t for t in priority["topic_rankings"]}
    by_question: dict[str, list[dict]] = {}
    for row in priority["question_topic_rows"]:
        by_question.setdefault(row["question_id"], []).append(row)
    return ranks, by_question


def question_key(question: dict) -> tuple[str, str, str | None]:
    match = re.match(r"Q(\d+)\(?([a-z])?\)?", question["qno_text"])
    return question["src_text"], match.group(1), match.group(2)


def build_unit(unit_id: str, spec: dict, pages: list[str], priority: dict) -> dict:
    library = json.loads((LIBRARY / spec["library_file"]).read_text(encoding="utf-8"))
    by_book_id = {q["book_id"]: q for q in library}
    ranks, rows_by_question = topic_lookup(priority)

    unit_rows = [r for r in priority["question_topic_rows"] if r["unit_id"] == unit_id]
    rows_by_key = {}
    for row in unit_rows:
        rows_by_key.setdefault((row["paper_label"], row["question_no"], row["sub_part"]), []).append(row)

    questions = []
    for position, (book_id, why) in enumerate(spec["selection"], start=1):
        source = by_book_id.get(book_id)
        if source is None:
            raise KeyError(f"{book_id} is not in {spec['library_file']}")

        mapped = rows_by_key.get(question_key(source), [])
        topics = [
            {
                "topic_id": row["topic_id"],
                "topic_name": row["topic_name"],
                "overall_rank": ranks[row["topic_id"]]["overall_rank"],
                "priority_band": ranks[row["topic_id"]]["priority_band"],
            }
            for row in mapped
        ]
        topics.sort(key=lambda t: t["overall_rank"])

        page = resolve_page(pages, source)
        first_row = mapped[0] if mapped else {}

        questions.append(
            {
                "position": position,
                "book_id": book_id,
                "source_label": source["src_text"],
                "paper_type": first_row.get("paper_type") or source["src_text"].split()[0],
                "question_no": source["qno_text"],
                "marks_text": source["marks_text"],
                "approx_time_text": source["approx_time_text"],
                "topic_text": source["topic_text"],
                "topics": topics,
                "badges": source["badges"],
                "study_match_category": first_row.get("category"),
                "study_match_percent": first_row.get("similarity_percent"),
                "why": why,
                "book_page": page,
                "question_html": source["question_html"],
                "answer_html": source["answer_html"],
                "mistake_type": source["mistake_type"],
                "mistake_text": source["mistake_text"],
            }
        )

    return {
        "unit_id": unit_id,
        "standard": spec["standard"],
        "unit_title": spec["unit_title"],
        "module": spec["module"],
        "chapter": spec["chapter"],
        "book_edition": BOOK_EDITION,
        "generated_on": date.today().isoformat(),
        "library_total": len(library),
        "questions": questions,
    }


def build_catalogue(priority: dict) -> list[dict]:
    """Derive the Module -> Chapter -> Unit tree from the canonical topic ranking,
    so the picker can never drift from the real syllabus. Units without a
    published shortlist are still listed, marked as not published."""
    seen: dict[str, dict] = {}
    for topic in priority["topic_rankings"]:
        unit_id = topic["topic_id"].rsplit("-T", 1)[0]
        if unit_id not in seen:
            seen[unit_id] = {
                "unit_id": unit_id,
                "label": topic["unit_name"],
                "module": topic["module"],
                "chapter": topic["chapter_name"],
                "published": unit_id in UNITS,
            }

    tree: list[dict] = []
    for unit in sorted(seen.values(), key=lambda u: u["unit_id"]):
        module = next((m for m in tree if m["module"] == unit["module"]), None)
        if module is None:
            module = {"module": unit["module"], "chapters": []}
            tree.append(module)
        chapter = next((c for c in module["chapters"] if c["chapter"] == unit["chapter"]), None)
        if chapter is None:
            chapter = {"chapter": unit["chapter"], "units": []}
            module["chapters"].append(chapter)
        chapter["units"].append(
            {"unit_id": unit["unit_id"], "label": unit["label"], "published": unit["published"]}
        )
    return tree


def main() -> None:
    priority = json.loads(PRIORITY.read_text(encoding="utf-8"))
    pages = book_page_index()
    OUTPUT.mkdir(parents=True, exist_ok=True)

    catalogue = build_catalogue(priority)
    default_unit = next(iter(UNITS))
    (OUTPUT / "index.json").write_text(
        json.dumps(
            {"generated_on": date.today().isoformat(), "default_unit": default_unit, "modules": catalogue},
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )
    units_total = sum(len(c["units"]) for m in catalogue for c in m["chapters"])
    print(f"Wrote index.json: {len(catalogue)} modules, {units_total} units")

    for unit_id, spec in UNITS.items():
        payload = build_unit(unit_id, spec, pages, priority)
        target = OUTPUT / f"{unit_id}.json"
        target.write_text(
            json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        unresolved = [q["book_id"] for q in payload["questions"] if q["book_page"] is None]
        print(f"Wrote {target.name}: {len(payload['questions'])} questions")
        if unresolved:
            print(f"  Page number unresolved for: {', '.join(unresolved)}")


if __name__ == "__main__":
    main()
