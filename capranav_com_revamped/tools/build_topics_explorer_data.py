"""Build the data behind /topics/ (the Important Topics explorer).

Sources (already reviewed and canonical; nothing is re-typed here):

* ``books/ca-inter/smat-may-27-edition/practice-with-pranav-bhaiya/data/descriptive_topic_priority.json``
  holds the 400-topic ranking and the per-question topic mapping (one row per
  question x topic, with the marks allocated to that topic).
* ``books/ca-inter/concept-book/syllabus-engine/data/1-ca-inter-adv-accounts-topic-page-index.json``
  is the canonical topic list: names, Study Material page numbers, teaching order.
* ``.../data/ca_inter_descriptive_topic_priority_v1.xlsx`` is Pranav's workbook. Its
  six sheets are copied verbatim into ``sheets/*.json`` so the page can offer each
  one as an Excel download exactly as he made it.

Writes into ``public/topics/data/``::

    topics.json        units, topics, sittings and one row per question x topic
    sheets/<slug>.json one per workbook sheet: {title, header, rows}
    sheets/index.json  the list of sheets, in workbook order

Run after any change to those sources, then deploy::

    python tools/build_topics_explorer_data.py
    npx wrangler deploy

The xlsx itself is gitignored (binary); only these JSON files are committed.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import date
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "books/ca-inter/smat-may-27-edition/practice-with-pranav-bhaiya/data"
PRIORITY = DATA / "descriptive_topic_priority.json"
WORKBOOK = DATA / "ca_inter_descriptive_topic_priority_v1.xlsx"
CANON = ROOT / "books/ca-inter/concept-book/syllabus-engine/data/1-ca-inter-adv-accounts-topic-page-index.json"
OUT = ROOT / "capranav_com_revamped/public/topics/data"

# Workbook sheets offered as downloads: (sheet name, file slug, what it is for).
# The plain-English "use" lines are the workbook's own Guide sheet, lightly reworded.
SHEETS = [
    ("Top 100 PYQ", "top-100-pyq", "The Top 50 plus next 50 topics, ranked by marks in Past Year Questions."),
    ("Chapter Priority", "chapter-priority", "All 400 topics with an overall rank and a rank within their chapter."),
    ("Topic Attempts", "topic-attempts", "One row per topic: PYQ, MTP and RTP marks and the list of papers it appeared in."),
    ("Question Topic Map", "question-topic-map", "One row per question and topic it tests, ready for pivot tables."),
    ("A-B-C-D Questions", "abcd-questions", "Every question classed A/B/C/D by how closely it matches an ICAI Study Material question."),
    ("Study Topics", "study-topics", "The full topic catalogue with ranking fields."),
]

MONTH_NO = {"January": 1, "May": 5, "September": 9, "November": 11}


def teach_order(seq: str) -> float:
    """Teaching sequence as a sortable number: "23" -> 23, "23B" -> 23.2 (the file uses
    a trailing letter for chapters taught as a pair)."""
    digits = "".join(ch for ch in seq if ch.isdigit())
    letters = [ch for ch in seq if ch.isalpha()]
    return int(digits) + (0.1 * (ord(letters[0].upper()) - 64) if letters else 0)


def cell(value):
    """A JSON-safe workbook cell: dates and odd types become strings, whole floats ints."""
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return int(value) if value.is_integer() else round(value, 4)
    return str(value)


def build_sheets() -> list[dict]:
    wb = openpyxl.load_workbook(WORKBOOK, read_only=True, data_only=True)
    (OUT / "sheets").mkdir(parents=True, exist_ok=True)
    index = []
    for name, slug, use in SHEETS:
        rows = [[cell(c) for c in r] for r in wb[name].iter_rows(values_only=True)]
        # Drop trailing empty columns (the workbook has a stray "Column1").
        width = max((max((i for i, c in enumerate(r) if c not in (None, "")), default=-1) for r in rows), default=-1) + 1
        rows = [r[:width] for r in rows]
        header, body = rows[0], [r for r in rows[1:] if any(c not in (None, "") for c in r)]
        (OUT / "sheets" / f"{slug}.json").write_text(
            json.dumps({"title": name, "header": header, "rows": body}, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        index.append({"slug": slug, "title": name, "use": use, "rows": len(body), "columns": len(header)})
        print(f"  sheet {name}: {len(body)} rows x {len(header)} columns")
    (OUT / "sheets" / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    return index


def build_topics() -> dict:
    priority = json.loads(PRIORITY.read_text(encoding="utf-8"))
    canon = json.loads(CANON.read_text(encoding="utf-8"))
    ranks = {t["topic_id"]: t for t in priority["topic_rankings"]}

    units, unit_index, topics, topic_index = [], {}, [], {}
    for chapter in canon["chapters"]:
        uid = chapter["unique_chapter_id"]
        unit_index[uid] = len(units)
        units.append({
            "id": uid,
            "module": int(uid.split("-")[0][1:]),
            "chapterNo": int(chapter["chapter_no"]),
            "chapter": chapter["chapter_name"],
            "unit": chapter["unit_name"],
            "standard": chapter.get("standard") or "",
            "short": chapter.get("chapter_name_short") or "",
            "teach": teach_order(chapter["teaching_sequence"]),
            "single": bool(chapter.get("is_single_unit_chapter")),
        })
        for t in chapter["topics"]:
            tid = t["unique_topic_id"]
            r = ranks.get(tid)
            topic_index[tid] = len(topics)
            topics.append({
                "id": tid,
                "no": t["topic_no"],
                "name": t["topic_name"],
                "short": t.get("topic_name_abbvtd") or t["topic_name"],
                "page": t["page_number"],
                "unit": unit_index[uid],
                "officialRank": r["overall_rank"] if r else None,
                "band": r["priority_band"] if r else None,
            })
    assert len(topics) == 400, len(topics)
    missing = [t for t in ranks if t not in topic_index]
    assert not missing, f"ranked topics not in the canonical index: {missing[:5]}"

    sittings, sitting_index = [], {}
    rows, skipped = [], 0
    for r in priority["question_topic_rows"]:
        if not r["topic_id"]:      # category D: no Study Material topic mapped
            skipped += 1
            continue
        label = r["paper_label"]
        if label not in sitting_index:
            sitting_index[label] = len(sittings)
            sittings.append({
                "label": label,
                "type": r["paper_type"],
                "year": r["exam_year"],
                "month": r["attempt_month"],
                "monthNo": MONTH_NO[r["attempt_month"]],
                "set": r["set"],
            })
        q = f"Q{r['question_no']}" + (f"({r['sub_part']})" if r["sub_part"] else "")
        if r["or_alternative"]:
            q += f" OR-{r['or_alternative']}"
        rows.append([topic_index[r["topic_id"]], sitting_index[label], r["allocated_marks"] or 0, q])

    # The page recomputes rankings in the browser, so it must reproduce the workbook's
    # own PYQ ranking. Refuse to publish if it does not.
    pyq = defaultdict(float)
    for ti, si, marks, _ in rows:
        if sittings[si]["type"] == "PYQ":
            pyq[topics[ti]["id"]] += marks
    for tid, r in ranks.items():
        assert abs(pyq.get(tid, 0) - r["pyq_allocated_marks"]) < 0.01, (tid, pyq.get(tid), r["pyq_allocated_marks"])
    print(f"  topics {len(topics)}, units {len(units)}, sittings {len(sittings)}, rows {len(rows)} "
          f"({skipped} unmapped rows skipped); PYQ marks reproduce the workbook for all {len(ranks)} ranked topics")

    return {
        "generated": date.today().isoformat(),
        "note": "marks = allocated marks: a question's marks are split equally across the topics it tests. "
                "RTP questions carry no stated marks, so RTP is counted in questions, not marks.",
        "units": units,
        "topics": topics,
        "sittings": sittings,
        "rows": rows,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("Building topics explorer data")
    data = build_topics()
    (OUT / "topics.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    build_sheets()
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
