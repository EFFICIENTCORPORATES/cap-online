"""Candidate pool of ICAI Study Material descriptive items, de-duplicated against the Question Bank.

Why this exists: the Must Practice page picks ten descriptive questions per unit from the
Question Bank (PYQ/MTP/RTP). Some units have fewer than ten, or none that are distinct. For
those, the Study Material's own Illustrations and Test Your Knowledge (TYK) descriptive
questions are a second source. This script finds which of them are NOT already covered by a
Question Bank question in the same unit. It is read-only analysis: it writes one JSON file
and changes nothing else. Method and status: _claude/skills/SKILL-must-practice-questions.md

Inputs (all produced by earlier, documented steps):
  .../practice-with-pranav-bhaiya/data/mcq-library/*_Descriptive.json   the Question Bank's descriptive
        questions per unit, i.e. exactly the pool the Must Practice build chooses from (a snapshot
        copied from the Main1Lavya repo; the underlying questions come from the sitting HTML files)
  books/ca-inter/concept-book/raw_icai_study_materials/*.md     Study Material text, converted from
        ICAI's PDFs (tables are scrambled; this script reads QUESTION text only, never answers)
  first_run/output/generated-from-script/study_material_tyk.json   Test Your Knowledge items
        (made by first_run/scripts/extract_study_material_tyk.py)
  .../practice-with-pranav-bhaiya/data/descriptive_topic_priority.json   the 36 unit ids
  first_run/output/generated-from-script/pyq_study_matches.json   human-reviewed PYQ -> Study Material
        same-concept matches (made by build_pyq_study_matches.py: a lexical candidate list plus its
        manually reviewed SAME_CONCEPT / PARTIAL tables). A study item named there is already
        "covered" by a PYQ and is never reported as unique.

Output: .../practice-with-pranav-bhaiya/data/study_material_descriptive_pool.json

Run:  python first_run/scripts/build_study_material_pool.py
Needs: nothing beyond the standard library (TF-IDF is implemented below).

Thresholds are PROVISIONAL (calibrated on nothing but eyeballing); the report prints every
borderline pair so a human can judge. Do not treat "unique" as verified until reviewed.
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_pyq_study_matches as bsm  # noqa: E402  (reuses its extraction + normalisation)

HUB = ROOT / "books/ca-inter/smat-may-27-edition/practice-with-pranav-bhaiya/data"
PRIORITY = HUB / "descriptive_topic_priority.json"
LIBRARY = HUB / "mcq-library"
OUT = HUB / "study_material_descriptive_pool.json"
REVIEWED = ROOT / "first_run/output/generated-from-script/pyq_study_matches.json"

# Provisional thresholds (see module docstring).
COSINE_DUPLICATE = 0.75     # concept-text TF-IDF cosine at or above this = same question
COSINE_REVIEW = 0.25        # between REVIEW and DUPLICATE = a human must look. Calibrated on the human-
                            # reviewed same-concept pairs in pyq_study_matches.json, whose lexical scores
                            # here are as low as ~0.28: wording and figures change between a Study Material
                            # illustration and the exam question built on it, so lexical similarity alone
                            # UNDERSTATES overlap. Hence the reviewed matches below are authoritative.
FIGURES_MIN = 5             # same shared-figures test the Must Practice build uses
FIGURES_RATIO = 0.60

HTML_TAG = re.compile(r"<[^>]+>")


def figures(text: str) -> set[str]:
    return {n.replace(",", "") for n in re.findall(r"\d[\d,]*\.?\d*", text) if len(n.replace(",", "")) >= 3}


def shared_figures(a: set[str], b: set[str]) -> float:
    """1.0 when the two share enough distinct figures to be the same problem, else 0.0."""
    smaller = min(len(a), len(b))
    shared = a & b
    return 1.0 if smaller and len(shared) >= FIGURES_MIN and len(shared) / smaller >= FIGURES_RATIO else 0.0


def tfidf_vectors(docs: list[str]) -> list[dict[str, float]]:
    """Unigram+bigram sublinear TF-IDF, L2-normalised. Small corpora only (one unit at a time)."""
    import math
    from collections import Counter

    grams = []
    for doc in docs:
        words = doc.split()
        grams.append(Counter(words + [f"{a} {b}" for a, b in zip(words, words[1:])]))
    df = Counter(g for c in grams for g in c)
    n = len(docs)
    vectors = []
    for c in grams:
        vec = {g: (1 + math.log(tf)) * (math.log((1 + n) / (1 + df[g])) + 1) for g, tf in c.items()}
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        vectors.append({g: v / norm for g, v in vec.items()})
    return vectors


def cosine(a: dict[str, float], b: dict[str, float]) -> float:
    if len(a) > len(b):
        a, b = b, a
    return sum(v * b.get(g, 0.0) for g, v in a.items())


def ranking_units() -> set[str]:
    priority = json.loads(PRIORITY.read_text(encoding="utf-8"))
    return {t["topic_id"].rsplit("-T", 1)[0] for t in priority["topic_rankings"]}


def canonical_unit(code: str, units: set[str]) -> str | None:
    """Study Material filenames say U1 for single-unit chapters; the canonical id is U0."""
    if code in units:
        return code
    alt = re.sub(r"-U\d+$", "-U0", code)
    return alt if alt in units else None


def reviewed_matches(units: set[str]) -> dict[tuple[str, str, int], dict]:
    """(unit, item_type, item_no) -> the human-reviewed PYQ match that already covers it."""
    out: dict[tuple[str, str, int], dict] = {}
    for m in json.loads(REVIEWED.read_text(encoding="utf-8")):
        if not m.get("study_item_no") or not m.get("study_source_file"):
            continue
        code = "-".join(Path(m["study_source_file"]).name.split("_")[:3])
        unit = canonical_unit(code, units)
        if unit:
            out[(unit, m["study_item_type"], int(m["study_item_no"]))] = {
                "pyq_question_id": m["question_id"], "similarity_percent": m.get("similarity_percent"),
                "match_status": m.get("match_status"),
            }
    return out


def main() -> None:
    units = ranking_units()
    reviewed = reviewed_matches(units)

    bank = defaultdict(list)
    for path in sorted(LIBRARY.glob("*_Descriptive.json")):
        for row in json.loads(path.read_text(encoding="utf-8")):
            unit = canonical_unit(row["unitcode"], units)
            if unit is None:
                continue
            text = bsm.plain(row["question_html"])
            bank[unit].append({
                "id": row["book_id"], "text": text, "concept": bsm.concept_text(text), "figs": figures(text),
            })

    study = defaultdict(list)
    for item in bsm.study_items():
        unit = canonical_unit(item["unitcode"], units)
        if unit is None:
            continue
        text = item["question"]
        study[unit].append({
            "item_type": item["item_type"], "item_no": item["item_no"], "source_file": item["source_file"],
            "text": text, "concept": bsm.concept_text(text), "figs": figures(text),
        })

    report = []
    for unit in sorted(units):
        b, s = bank.get(unit, []), study.get(unit, [])
        entry = {"unit_id": unit, "bank_questions": len(b), "study_items": len(s), "items": []}
        if s:
            corpus = [x["concept"] or "-" for x in b + s]
            vecs = tfidf_vectors(corpus)
            bank_vecs, study_vecs = vecs[:len(b)], vecs[len(b):]
            for i, item in enumerate(s):
                nearest, best = None, 0.0
                for j, q in enumerate(b):
                    cos = cosine(study_vecs[i], bank_vecs[j])
                    score = max(cos, shared_figures(item["figs"], q["figs"]))
                    if score > best:
                        best, nearest = score, q["id"]
                dup_of_study = next(
                    (f'{s[k]["item_type"]} {s[k]["item_no"]}' for k in range(i)
                     if max(cosine(study_vecs[i], study_vecs[k]), shared_figures(item["figs"], s[k]["figs"])) >= COSINE_DUPLICATE),
                    None,
                )
                covered = reviewed.get((unit, item["item_type"], item["item_no"]))
                verdict = ("duplicate_of_bank" if best >= COSINE_DUPLICATE
                           else "covered_by_reviewed_match" if covered
                           else "duplicate_of_study_item" if dup_of_study
                           else "review" if best >= COSINE_REVIEW else "unique")
                entry["items"].append({
                    "item_type": item["item_type"], "item_no": item["item_no"],
                    "source_file": item["source_file"], "verdict": verdict,
                    "nearest_bank_id": nearest, "nearest_similarity": round(best, 3),
                    "duplicate_of_study_item": dup_of_study, "reviewed_match": covered, "question_text": item["text"][:600],
                })
        entry["unique"] = sum(1 for x in entry["items"] if x["verdict"] == "unique")
        entry["review"] = sum(1 for x in entry["items"] if x["verdict"] == "review")
        report.append(entry)

    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{'unit':10} {'bank':>4} {'study':>5} {'unique':>6} {'review':>6}   potential list size")
    for e in report:
        if e["bank_questions"] >= 10 and not e["study_items"]:
            continue
        potential = e["bank_questions"] + e["unique"]
        print(f"{e['unit_id']:10} {e['bank_questions']:>4} {e['study_items']:>5} {e['unique']:>6} {e['review']:>6}   "
              f"{min(potential, 10)} (max {potential})")
    print(f"\nWrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
