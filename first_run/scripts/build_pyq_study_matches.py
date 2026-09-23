"""Rank study-material questions for PYQ concept review.

The output is a candidate list, not an automatic assertion of a 100% concept
match. Names, dates, years and monetary amounts are removed before ranking.
Illustrations are extracted as source items independent of their position after
the final topic; they are never assigned to the preceding topic by page order.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STUDY = ROOT / "books/ca-inter/concept-book/raw_icai_study_materials"
INDEX = ROOT / "first_run/output/generated-from-script/questions_index.json"
TYK = ROOT / "first_run/output/generated-from-script/study_material_tyk.json"
OUTPUT = ROOT / "first_run/output/generated-from-script/pyq_study_candidates.json"
MATCHES = ROOT / "first_run/output/generated-from-script/pyq_study_matches.json"

# Manually reviewed same-concept source questions. The accounting operation is
# the same even where names, amounts or financial years differ. This list is
# intentionally conservative; a lexical candidate is not a verified match.
SAME_CONCEPT = {
    "CAI-P1-PYQ-2025-01-PII-Q3-a": ("Test Your Knowledge", 8),
    "CAI-P1-PYQ-2026-01-PII-Q1-b": ("Illustration", 7),
    "CAI-P1-PYQ-2025-05-PII-Q6-a-alt2": ("Illustration", 3),
    "CAI-P1-PYQ-2025-05-PII-Q6-b": ("Illustration", 1),
    "CAI-P1-PYQ-2026-05-PII-Q1-a": ("Illustration", 9),
    "CAI-P1-PYQ-2026-05-PII-Q1-b": ("Test Your Knowledge", 19),
    "CAI-P1-PYQ-2026-05-PII-Q6-a-alt2": ("Illustration", 9),
    "CAI-P1-PYQ-2023-11-PII-Q1-d": ("Illustration", 8),
    "CAI-P1-PYQ-2023-11-PII-Q3-a": ("Test Your Knowledge", 11),
    "CAI-P1-PYQ-2024-09-PII-Q1-b": ("Test Your Knowledge", 9),
    "CAI-P1-PYQ-2024-09-PII-Q1-c": ("Illustration", 4),
    "CAI-P1-PYQ-2024-09-PII-Q6-a-alt1": ("Illustration", 8),
    "CAI-P1-PYQ-2024-09-PII-Q6-a-alt2": ("Test Your Knowledge", 5),
    "CAI-P1-PYQ-2025-09-PII-Q1-c-ii": ("Illustration", 4),
    "CAI-P1-PYQ-2026-01-PII-Q1-c": ("Illustration", 4),
    "CAI-P1-PYQ-2026-01-PII-Q3-b": ("Test Your Knowledge", 10),
    "CAI-P1-PYQ-2026-01-PII-Q6-a-alt2": ("Illustration", 1),
    "CAI-P1-PYQ-2026-01-PII-Q6-b": ("Illustration", 1),
    "CAI-P1-PYQ-2024-05-PII-Q3-a": ("Test Your Knowledge", 11),
}

# Related but not identical tasks: the PYQ adds or omits a material accounting
# operation, so changed company names/amounts are not the reason for <100%.
PARTIAL_CONCEPT = {
    "CAI-P1-PYQ-2025-01-PII-Q1-a": ("Illustration", 6, 75, "PYQ also tests bonus shares and convertible debentures."),
    "CAI-P1-PYQ-2023-05-PII-Q1-c": ("Illustration", 2, 75, "PYQ also tests grant refund and both presentation methods."),
    "CAI-P1-PYQ-2024-05-PII-Q6-a-alt1": ("Illustration", 2, 75, "PYQ also asks for lease classification and lessor treatment."),
    "CAI-P1-PYQ-2024-05-PII-Q6-a-alt2": ("Illustration", 5, 75, "PYQ includes basic EPS and partly paid shares, beyond convertible debentures."),
}

ILLUSTRATION = re.compile(r"(?im)^\s*Illustration\s+(\d+)\b")
SOLUTION = re.compile(r"(?im)^\s*Solution\b")
END = re.compile(r"(?im)^\s*(?:TEST YOUR KNOWLEDGE|Answers to the|Answer to the)\b")
TAG = re.compile(r"<[^>]+>")
PAGE = re.compile(r"(?im)^\s*(?:©.*|ADVANCED ACCOUNTING|[A-Z][A-Z\s&-]{7,}|\d+(?:\.\d+){1,4}\s+\d+)\s*$")
NAME = re.compile(r"\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\s+(?:Ltd\.?|Limited|Co\.?|Corporation|Company|Firm)\b")
NUMBER = re.compile(r"(?<![A-Za-z])(?:₹|Rs\.?|`)?\s*\d[\d,]*(?:\.\d+)?\s*(?:%|percent|lakhs?|crores?|years?|months?|days?)?", re.I)
STOP = set("a an the and or to of in on for from by with at as is are was were be been being this that those these it its their his her we you your company limited ltd co firm entity accounting standard per under provision provisions comment explain state calculate compute prepare find determine what whether how why given following information required question answer based during year amount amounts rupees rs total".split())


def plain(text: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(TAG.sub(" ", text or ""))).strip()


def concept_text(text: str) -> str:
    text = NAME.sub(" entity ", plain(text))
    text = NUMBER.sub(" value ", text)
    tokens = re.findall(r"[a-z][a-z'-]+", text.lower())
    return " ".join(w for w in tokens if w not in STOP and w not in {"value", "entity"})


def study_items() -> list[dict]:
    items = []
    unit_to_path = {}
    for path in sorted(STUDY.glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        unitcode = "-".join(path.name.split("_")[:3])
        unit_to_path.setdefault(unitcode, str(path.relative_to(ROOT)).replace("\\", "/"))
        matches = list(ILLUSTRATION.finditer(text))
        for i, match in enumerate(matches):
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            cutoff = END.search(text, match.end(), end)
            if cutoff:
                end = cutoff.start()
            solution = SOLUTION.search(text, match.end(), end)
            if solution:
                end = solution.start()
            question = PAGE.sub(" ", text[match.end():end]).strip()
            if len(question) < 35:
                continue
            items.append({
                "unitcode": unitcode,
                "item_type": "Illustration",
                "item_no": int(match.group(1)),
                "source_file": str(path.relative_to(ROOT)).replace("\\", "/"),
                "question": plain(question)[:5000],
            })
    for chapter in json.loads(TYK.read_text(encoding="utf-8")):
        for item in chapter.get("descriptive", []):
            items.append({
                "unitcode": chapter["unitcode"],
                "item_type": "Test Your Knowledge",
                "item_no": item["source_num"],
                "source_file": unit_to_path.get(chapter["unitcode"], chapter["name"]),
                "question": plain(item.get("question_html", "")),
            })
    return items


def main() -> None:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    questions = [q for q in json.loads(INDEX.read_text(encoding="utf-8"))
                 if q["paper_type"] == "PYQ" and q["part"] == "II"]
    items = study_items()
    corpus = [concept_text(q["question_html"]) for q in questions]
    corpus += [concept_text(item["question"]) for item in items]
    word = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=1)
    char = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True, min_df=1)
    word_matrix = word.fit_transform(corpus)
    char_matrix = char.fit_transform(corpus)
    n = len(questions)
    scores = 0.7 * cosine_similarity(word_matrix[:n], word_matrix[n:])
    scores += 0.3 * cosine_similarity(char_matrix[:n], char_matrix[n:])
    output = []
    for qi, q in enumerate(questions):
        units = {x.get("unitcode") for x in q.get("topics", []) if x.get("unitcode")}
        units.add(q.get("final_chapter"))
        candidate_indices = [i for i, item in enumerate(items) if item["unitcode"] in units]
        ranked = sorted(candidate_indices, key=lambda i: scores[qi, i], reverse=True)[:5]
        output.append({
            "question_id": q["id"],
            "paper_label": f'{q["paper_type"]} {q["exam_month"]} {q["exam_year"]}',
            "question": plain(q["question_html"])[:700],
            "candidates": [
                {**{k: item[k] for k in ("unitcode", "item_type", "item_no", "source_file")},
                 "lexical_candidate_score": round(float(scores[qi, i]), 4),
                 "study_question": item["question"][:1000]}
                for i in ranked for item in [items[i]]
            ],
        })
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    matches = []
    for row in output:
        question_id = row["question_id"]
        verified = SAME_CONCEPT.get(question_id)
        partial = PARTIAL_CONCEPT.get(question_id)
        candidate = next((c for c in row["candidates"]
                          if (verified and (c["item_type"], c["item_no"]) == verified)
                          or (partial and (c["item_type"], c["item_no"]) == partial[:2])), None)
        if verified and not candidate:
            raise ValueError(f"Verified source item missing from candidates: {question_id}")
        if partial and not candidate:
            raise ValueError(f"Related source item missing from candidates: {question_id}")
        if candidate:
            matches.append({
                "question_id": question_id,
                "match_status": "Verified same concept" if verified else "Reviewed partial concept",
                "similarity_percent": 100 if verified else partial[2],
                "study_item_type": candidate["item_type"],
                "study_item_no": candidate["item_no"],
                "study_source_file": candidate["source_file"],
                "study_question_excerpt": candidate["study_question"][:350],
                "match_note": "Same accounting task; names, years and amounts ignored." if verified else partial[3],
            })
        else:
            candidate = row["candidates"][0] if row["candidates"] else None
            matches.append({
                "question_id": question_id,
                "match_status": "Candidate needs concept review" if candidate else "No study question in mapped unit",
                "similarity_percent": None,
                "study_item_type": candidate["item_type"] if candidate else None,
                "study_item_no": candidate["item_no"] if candidate else None,
                "study_source_file": candidate["source_file"] if candidate else None,
                "study_question_excerpt": candidate["study_question"][:350] if candidate else None,
                "match_note": "Candidate only; percentage withheld until concept is reviewed." if candidate else "No study-material question found in the mapped unit; topic link may still exist.",
            })
    MATCHES.write_text(json.dumps(matches, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Ranked {len(questions)} PYQs against {len(items)} study-material questions; wrote {OUTPUT}")
    print(f"No in-unit candidates: {sum(not x['candidates'] for x in output)}")
    print(f"Verified same-concept matches: {sum(x['similarity_percent'] == 100 for x in matches)}; reviewed partial matches: {sum(x['match_status'] == 'Reviewed partial concept' for x in matches)}; wrote {MATCHES}")


if __name__ == "__main__":
    main()
