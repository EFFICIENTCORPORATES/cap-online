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

# Scoring weights. The reasoning behind each is in the rules document:
# books/ca-inter/smat-may-27-edition/practice-with-pranav-bhaiya/MUST-PRACTICE-RULES.md
# Change them here and nowhere else, then update that file in the same commit.
SCORING = {
    "topic_weight": 0.40,     # how heavily the question's topic is actually examined
    "study_match": 0.25,      # closeness to an ICAI Study Material question
    "source_recency": 0.20,   # MTP/RTP signal the coming paper better than a past PYQ
    "marks": 0.15,
}

# Paper type: an MTP/RTP predicts the NEXT paper better than a question already
# set in a past exam. See the rules document's "why a PYQ scores lower" note.
PAPER_TYPE_SCORE = {"MTP": 1.0, "RTP": 0.95, "PYQ": 0.6}

# The ten-sitting window the topic ranking itself is built over, oldest first;
# a question's recency is its position in this list.
SITTING_ORDER = [
    "May 2023", "November 2023", "May 2024", "September 2024", "January 2025",
    "May 2025", "September 2025", "January 2026", "May 2026", "September 2026",
]

SHORTLIST_SIZE = 10

# One entry per unit. The shortlist is COMPUTED from SCORING above — never typed
# by hand. ``published`` false keeps a unit out of the live page while it is
# being reviewed. ``force_include``/``force_exclude`` and ``why_overrides`` are
# the documented escape hatches; each force entry carries its reason.
UNITS = {
    "M2-C5-U1": {
        "library_file": "CA_Inter_AdvAcc_AS_2_Valuation_of_Inventories_17_Descriptive.json",
        "standard": "AS 2",
        "unit_title": "Valuation of Inventories",
        "module": "MODULE 2",
        "chapter": "Assets Based Accounting Standards",
        "published": True,
        # Hand-written card wording, kept so all ten read in one voice rather
        # than mixing reviewed prose with generated lines.
        "why_overrides": {
            "M2C5U1-008": "Highest-ranked AS 2 topic (rank 40) and a 90% match to an ICAI Study Material question.",
            "M2C5U1-002": "Newest MTP in the corpus and a Category A question — 93% identical to a Study Material question.",
            "M2C5U1-015": "An RTP that carries three mapped topics at once, including the rank-40 NRV topic.",
            "M2C5U1-006": "Normal versus abnormal loss, the most repeated AS 2 idea, at an 80% Study Material match.",
            "M2C5U1-004": "Category A: 93.5% identical to a Study Material question on excluded costs.",
            "M2C5U1-012": "ICAI lifted this one from the Study Material verbatim (100% match) once already.",
            "M2C5U1-005": "The abnormal-waste computation in its most examined form, 80% Study Material match.",
            "M2C5U1-009": "Costs excluded from inventory cost, at an 80% match to an ICAI Study Material question.",
            "M2C5U1-010": "The only question covering Joint and By-Products, and the largest at 7 marks.",
            "M2C5U1-007": "Latest MTP, and the only recent hit on the retail method and NRV estimation.",
        },
    },
    "M2-C5-U2": {
        "library_file": "CA_Inter_AdvAcc_AS_10_Property_Plant_and_Equipment_16_Descriptive.json",
        "standard": "AS 10",
        "unit_title": "Property, Plant and Equipment",
        "module": "MODULE 2",
        "chapter": "Assets Based Accounting Standards",
        "published": False,   # local-only until reviewed
    },
}


def recency_score(paper_label: str) -> float:
    for i, sitting in enumerate(SITTING_ORDER):
        if sitting in paper_label:
            return i / (len(SITTING_ORDER) - 1)
    return 0.0


def study_match_score(category: str | None, similarity: float | None) -> float:
    if category == "A":
        return 1.0
    if category == "B":
        return (similarity if similarity is not None else 60.0) / 100.0
    if category == "C":
        return 0.30
    return 0.0


def score_question(rows: list[dict], ranks: dict, marks: int) -> tuple[float, dict]:
    """Score one question out of 1.0. ``rows`` are its question_topic_rows."""
    first = rows[0]
    topic_marks = max(ranks[r["topic_id"]]["pyq_allocated_marks"] for r in rows)
    parts = {
        "topic_weight": min(topic_marks / 5.0, 1.0),
        "study_match": study_match_score(first.get("category"), first.get("similarity_percent")),
        "source_recency": (
            0.45 * PAPER_TYPE_SCORE.get(first.get("paper_type"), 0.6)
            + 0.55 * recency_score(first.get("paper_label", ""))
        ),
        "marks": min((marks or 5) / 7.0, 1.0),
    }
    total = sum(SCORING[k] * v for k, v in parts.items())
    return total, parts


def apply_coverage(ranked: list[dict], top100: set[str], size: int) -> list[dict]:
    """Take the best `size` by score, then make sure every Top-100 topic of the
    chapter is represented — swapping only redundant questions out. See the
    rules document's "coverage pass"."""
    chosen = ranked[:size]
    rest = ranked[size:]

    def covered(sel):
        return {t for q in sel for t in q["topic_ids"] if t in top100}

    for topic in sorted(top100 - covered(chosen)):
        candidate = next((q for q in rest if topic in q["topic_ids"]), None)
        if candidate is None:
            continue
        # Drop the lowest-scoring question that is not the sole carrier of any topic.
        counts = {}
        for q in chosen:
            for t in q["topic_ids"]:
                if t in top100:
                    counts[t] = counts.get(t, 0) + 1
        redundant = [
            q for q in chosen
            if all(counts.get(t, 0) > 1 for t in q["topic_ids"] if t in top100)
        ]
        if not redundant:
            continue
        drop = min(redundant, key=lambda q: q["score"])
        chosen = [q for q in chosen if q is not drop] + [candidate]
        rest = [q for q in rest if q is not candidate] + [drop]
        chosen.sort(key=lambda q: -q["score"])
    return chosen


def auto_why(q: dict, ranks: dict) -> str:
    """The card's "Why this one" line, generated from the same signals that
    scored it, so the stated reason always matches the real one."""
    bits = []
    best = min(q["topics"], key=lambda t: t["overall_rank"]) if q["topics"] else None
    if best:
        bits.append(f"Rank {best['overall_rank']} topic ({best['topic_name']})")
    cat, pct = q["study_match_category"], q["study_match_percent"]
    if cat == "A":
        bits.append(f"Category A — {round(pct)}% identical to an ICAI Study Material question"
                    if pct else "Category A — lifted from an ICAI Study Material question")
    elif cat == "B" and pct:
        bits.append(f"{round(pct)}% match to an ICAI Study Material question")
    bits.append(f"{q['source_label']}")
    if len(q["topics"]) > 1:
        bits.append(f"covers {len(q['topics'])} mapped topics")
    return "; ".join(bits) + "."


def normalise(text: str) -> str:
    text = unicodedata.normalize("NFKD", re.sub(r"<[^>]+>", " ", text))
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def book_page_index() -> list[str]:
    reader = pypdf.PdfReader(str(BOOK_PDF))
    return [normalise(page.extract_text() or "") for page in reader.pages]


def page_hits(pages: list[str], question: dict) -> list[int]:
    """Every page whose text carries this question's printed header line, e.g.
    ``MTP May 2024 Set 2 · Q1(b) · Marks: 5``."""
    anchor = normalise(question["src_text"] + question["qno_text"] + question["marks_text"])
    return [i + 1 for i, page in enumerate(pages) if anchor in page]


def resolve_pages(pages: list[str], sources: list[dict]) -> dict[str, int | None]:
    """Resolve the Question Bank page for every question in one unit.

    A question tagged to two chapters is printed twice — once in its home
    chapter and once in another chapter's Integrated section — so its header
    matches two pages. Unambiguous questions are resolved first; their pages
    locate this chapter in the book, and an ambiguous question then takes
    whichever of its hits sits nearest that cluster. A question with no hit at
    all, or one that stays ambiguous because nothing anchors the chapter, is
    left as None and renders as "not traced" rather than a guess.
    """
    hits = {q["book_id"]: page_hits(pages, q) for q in sources}
    resolved = {bid: h[0] for bid, h in hits.items() if len(h) == 1}

    if resolved:
        anchor = sorted(resolved.values())[len(resolved) // 2]  # median home page
        for bid, h in hits.items():
            if bid not in resolved and h:
                resolved[bid] = min(h, key=lambda page: abs(page - anchor))

    return {q["book_id"]: resolved.get(q["book_id"]) for q in sources}


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
    ranks, _ = topic_lookup(priority)

    unit_rows = [r for r in priority["question_topic_rows"] if r["unit_id"] == unit_id]
    rows_by_key: dict = {}
    for row in unit_rows:
        rows_by_key.setdefault((row["paper_label"], row["question_no"], row["sub_part"]), []).append(row)

    # The chapter's Top-100 topics — what the coverage pass must satisfy.
    top100 = {
        t["topic_id"]
        for t in priority["topic_rankings"]
        if t["topic_id"].rsplit("-T", 1)[0] == unit_id
        and t["priority_band"] in ("Top 50", "Next 50")
    }

    page_by_id = resolve_pages(pages, library)

    # Score every question in the unit's library.
    scored = []
    for source in library:
        mapped = rows_by_key.get(question_key(source), [])
        if not mapped:
            continue  # no topic mapping -> cannot be scored or justified
        topics = sorted(
            (
                {
                    "topic_id": row["topic_id"],
                    "topic_name": row["topic_name"],
                    "overall_rank": ranks[row["topic_id"]]["overall_rank"],
                    "priority_band": ranks[row["topic_id"]]["priority_band"],
                }
                for row in mapped
            ),
            key=lambda t: t["overall_rank"],
        )
        first = mapped[0]
        marks = first.get("question_marks") or 0
        score, parts = score_question(mapped, ranks, marks)
        scored.append(
            {
                "book_id": source["book_id"],
                "source": source,
                "topics": topics,
                "topic_ids": [t["topic_id"] for t in topics],
                "score": score,
                "score_parts": parts,
                "source_label": source["src_text"],
                "paper_type": first.get("paper_type") or source["src_text"].split()[0],
                "study_match_category": first.get("category"),
                "study_match_percent": first.get("similarity_percent"),
            }
        )

    scored.sort(key=lambda q: -q["score"])

    forced_out = set(spec.get("force_exclude", {}))
    ranked = [q for q in scored if q["book_id"] not in forced_out]
    forced_in = [q for q in ranked if q["book_id"] in spec.get("force_include", {})]
    remaining = [q for q in ranked if q["book_id"] not in spec.get("force_include", {})]

    chosen = forced_in + apply_coverage(
        remaining, top100, max(SHORTLIST_SIZE - len(forced_in), 0)
    )
    chosen.sort(key=lambda q: -q["score"])

    print()
    print(f"{spec['standard']} ({unit_id}) — {len(scored)} scored, {len(top100)} Top-100 topics")
    for i, q in enumerate(scored, start=1):
        mark = "*" if q in chosen else " "
        print(f"  {mark} {i:>2}. {q['score']:.3f}  {q['book_id']:<12} {q['source_label']:<24} "
              f"cat {str(q['study_match_category']):<4} rank {q['topics'][0]['overall_rank'] if q['topics'] else '-'}")

    questions = []
    for position, q in enumerate(chosen, start=1):
        source = q["source"]
        why = spec.get("why_overrides", {}).get(q["book_id"]) or auto_why(q, ranks)
        questions.append(
            {
                "position": position,
                "book_id": q["book_id"],
                "source_label": q["source_label"],
                "paper_type": q["paper_type"],
                "question_no": source["qno_text"],
                "marks_text": source["marks_text"],
                "approx_time_text": source["approx_time_text"],
                "topic_text": source["topic_text"],
                "topics": q["topics"],
                "badges": source["badges"],
                "study_match_category": q["study_match_category"],
                "study_match_percent": q["study_match_percent"],
                "why": why,
                "score": round(q["score"], 4),
                "book_page": page_by_id.get(q["book_id"]),
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
        "published": spec.get("published", True),
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
                "published": bool(UNITS.get(unit_id, {}).get("published", False)),
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
    default_unit = next((u for u, sp in UNITS.items() if sp.get("published", True)), next(iter(UNITS)))
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
