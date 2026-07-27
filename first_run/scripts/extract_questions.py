"""
Layer 1 -> Layer 2 extraction script for the Question Bank pipeline.

Walks every sitting HTML file in first_run/output/parsed-from-pdf/*.html (schema
defined in first_run/schema/HTML-SCHEMA.md and
_claude/skills/SKILL-question-bank-html-schema.md), and emits one combined JSON file
(first_run/output/generated-from-script/questions_index.json) with one row per qblock
(question or independent-split question-fragment).

This is a mechanical extraction only (BeautifulSoup) - no AI judgment. It reads what
the sitting HTML already says; it does not re-tag or re-interpret anything.

Usage:  python extract_questions.py
"""
import json
import os
import re
from bs4 import BeautifulSoup

HERE = os.path.dirname(os.path.abspath(__file__))
SITTINGS_DIR = os.path.normpath(os.path.join(HERE, "..", "output", "parsed-from-pdf"))
GENERATED_DIR = os.path.normpath(os.path.join(HERE, "..", "output", "generated-from-script"))
INDEX_PATH = os.path.join(GENERATED_DIR, "questions_index.json")

DIFFICULTY_LABELS = {"easy": "Easy", "medium": "Medium", "hard": "Hard"}


def difficulty_for(topic_count):
    """Pranav's rule: <=2 distinct topics = Easy, 3-5 = Medium, >5 = Hard."""
    if topic_count <= 2:
        return "Easy"
    if topic_count <= 5:
        return "Medium"
    return "Hard"


def inner_html(tag):
    if tag is None:
        return ""
    return "".join(str(c) for c in tag.contents).strip()


def extract_topics(qblock):
    topics = []
    topics_div = qblock.find("div", class_="topics")
    if not topics_div:
        return topics
    for span in topics_div.find_all("span", class_="topic-tag"):
        topics.append({
            "unitcode": span.get("data-unitcode"),
            "subtopicref": span.get("data-subtopicref"),
            "standard": span.get("data-standard"),
            "title": span.get("data-title"),
            "rank": span.get("data-topic-rank"),
            "label": span.get_text(strip=True),
            "flag": span.get("data-flag"),
        })
    return topics


def extract_case_scenarios(soup):
    scenarios = {}
    for cs in soup.find_all("div", class_="case-scenario"):
        cs_id = cs.get("id")
        facts = cs.find("div", class_="case-facts")
        scenarios[cs_id] = {
            "id": cs_id,
            "case_no": cs.get("data-case-no"),
            "question_count": cs.get("data-question-count"),
            "facts_html": inner_html(facts),
        }
    return scenarios


def parse_marks(qblock):
    raw = qblock.get("data-marks")
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError:
        return raw  # shouldn't happen post-schema-revision, but don't crash if it does


def extract_examiner_comment(qblock):
    # class is "examiner-comment" or "examiner-comment synthesized"
    div = qblock.find("div", class_=re.compile(r"\bexaminer-comment\b"))
    if div is None:
        return None
    return {
        "comment_source": div.get("data-comment-source"),
        "source_citation": div.get("data-source"),
        "text": div.get_text(strip=True),
    }


def extract_one_file(path, filename):
    with open(path, encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    body = soup.find("body")
    paper = {
        "source_file": filename,
        "course": body.get("data-course"),
        "group": body.get("data-group"),
        "paper_code": body.get("data-paper-code"),
        "subject": body.get("data-subject"),
        "paper_type": body.get("data-paper-type"),
        "exam_month": body.get("data-exam-month"),
        "exam_year": body.get("data-exam-year"),
        "set": body.get("data-set"),  # None if the paper has no set
        "session_key": body.get("data-session-key"),
        "total_marks": body.get("data-total-marks"),
    }

    case_scenarios = extract_case_scenarios(soup)

    rows = []
    for qblock in soup.find_all("div", class_="qblock"):
        topics = extract_topics(qblock)
        question_div = qblock.find("div", class_="question")
        question_html = inner_html(question_div)

        case_ref = qblock.get("data-case-ref")
        case_facts_html = None
        if case_ref and case_ref in case_scenarios:
            case_facts_html = case_scenarios[case_ref]["facts_html"]

        answer_div = qblock.find("div", class_="answer-block")
        author_div = qblock.find("div", class_="author-comment")
        extraction_note = qblock.find("div", class_="extraction-note")

        row = {
            "id": qblock.get("id"),
            **paper,
            "part": qblock.get("data-part"),
            "qno": qblock.get("data-qno"),
            "parent_qno": qblock.get("data-parent-qno"),
            "subpart": qblock.get("data-subpart"),
            "alt_group": qblock.get("data-alt-group"),
            "alt": qblock.get("data-alt"),
            "marks": parse_marks(qblock),
            "compulsory": qblock.get("data-compulsory") == "true",
            "qtype": qblock.get("data-qtype"),
            "answer_letter": qblock.get("data-answer"),
            "final_chapter": qblock.get("data-final-chapter"),
            "confidence": qblock.get("data-confidence"),
            "review_status": qblock.get("data-review-status"),
            "issue": qblock.get("data-issue"),
            "case_ref": case_ref,
            "case_facts_html": case_facts_html,
            "question_html": question_html,
            "answer_html": inner_html(answer_div),
            "topics": topics,
            "topic_count": len(topics),
            "difficulty": difficulty_for(len(topics)),
            "examiner_comment": extract_examiner_comment(qblock),
            "author_comment_empty": (author_div is not None and not author_div.get_text(strip=True)),
            "extraction_note": extraction_note.get_text(strip=True) if extraction_note else None,
        }
        rows.append(row)

    return rows


def main():
    all_rows = []
    files = sorted(
        f for f in os.listdir(SITTINGS_DIR)
        if f.endswith(".html") and not f.endswith("_Question_Book.html")
    )
    per_file_counts = {}
    for fn in files:
        path = os.path.join(SITTINGS_DIR, fn)
        rows = extract_one_file(path, fn)
        per_file_counts[fn] = len(rows)
        all_rows.extend(rows)

    os.makedirs(GENERATED_DIR, exist_ok=True)
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(all_rows, f, ensure_ascii=False, indent=2)

    print(f"Extracted {len(all_rows)} question rows from {len(files)} files:")
    for fn, n in per_file_counts.items():
        print(f"  {fn}: {n}")
    print(f"Wrote {INDEX_PATH}")

    # Quick sanity check: alt-group-deduped marks total, per source file
    from collections import defaultdict
    totals = defaultdict(lambda: {"part1": 0, "part2_raw": 0, "alt_seen": set(), "part2_dedup": 0})
    for row in all_rows:
        sf = row["source_file"]
        marks = row["marks"] or 0
        if row["part"] and row["part"].strip().upper().startswith("I") and "II" not in (row["part"] or ""):
            # crude Part I detection: data-part == "I" for MCQs in the new files
            pass
        if row["part"] == "I":
            totals[sf]["part1"] += marks
        else:
            totals[sf]["part2_raw"] += marks
            ag = row["alt_group"]
            if ag:
                key = (sf, ag)
                if key not in totals[sf]["alt_seen"]:
                    totals[sf]["alt_seen"].add(key)
                    totals[sf]["part2_dedup"] += marks
            else:
                totals[sf]["part2_dedup"] += marks
    print("\nPer-file marks check (Part I / Part II raw / Part II deduped):")
    for sf, t in totals.items():
        print(f"  {sf}: {t['part1']} / {t['part2_raw']} / {t['part2_dedup']}")


if __name__ == "__main__":
    main()
