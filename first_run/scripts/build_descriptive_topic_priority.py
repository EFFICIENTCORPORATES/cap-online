"""Build question-level A/B/C/D evidence and topic-priority JSON for CA Inter AA.

Ranking scope: the latest ten available PYQs, May 2023 to September 2026.
Master scope: every indexed descriptive PYQ, MTP and RTP question, plus Sep 2026.
"""
from __future__ import annotations

import html, json, re
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HUB = ROOT / "books/ca-inter/smat-may-27-edition/practice-with-pranav-bhaiya"
FLAT = HUB / "data/question_bank_descriptive_flat_through_may2026.json"
TOPICS = HUB / "data/study_material_topics_flat.json"
INDEX = ROOT / "first_run/output/generated-from-script/questions_index.json"
SEP_HTML = HUB / "sources/pyq-september-2026-question-paper.html"
OUT = HUB / "data/descriptive_topic_priority.json"

PYQ_ORDER = ["PYQ May 2023", "PYQ November 2023", "PYQ May 2024", "PYQ September 2024",
             "PYQ January 2025", "PYQ May 2025", "PYQ September 2025", "PYQ January 2026",
             "PYQ May 2026", "PYQ September 2026"]
MONTH = {"01":"January", "05":"May", "09":"September", "11":"November"}

SEP_MAP = [
    ("CAI-P1-PYQ-2026-09-PII-Q1-a", "1", "a", None, None, 5,
     ["M2-C5-U2-T2.5", "M2-C5-U4-T4.3", "M2-C5-U4-T4.6"], "AS 10 and AS 16: building cost, specific borrowing and exchange difference"),
    ("CAI-P1-PYQ-2026-09-PII-Q1-b", "1", "b", None, None, 5,
     ["M2-C5-U5-T5.9"], "AS 19: operating lease rent, income recognition and lessor entries"),
    ("CAI-P1-PYQ-2026-09-PII-Q1-c", "1", "c", None, None, 4,
     ["M1-C4-U5-T5.3", "M1-C4-U5-T5.6", "M1-C4-U5-T5.9", "M1-C4-U5-T5.10"], "AS 20: basic EPS, diluted EPS, ESOP and bonus restatement"),
    ("CAI-P1-PYQ-2026-09-PII-Q2-a", "2", "a", None, None, 10,
     ["M3-C11-U1-T1.5"], "Schedule III company balance sheet with notes"),
    ("CAI-P1-PYQ-2026-09-PII-Q2-b", "2", "b", None, None, 4,
     ["M3-C13-U0-T4"], "Amalgamation: purchase consideration"),
    ("CAI-P1-PYQ-2026-09-PII-Q3", "3", None, None, None, 14,
     ["M3-C13-U0-T4", "M3-C13-U0-T6", "M3-C13-U0-T7"], "Amalgamation: purchase consideration and entries in vendor and purchasing company"),
    ("CAI-P1-PYQ-2026-09-PII-Q4-a", "4", "a", None, None, 10,
     ["M3-C11-U2-T2.4", "M3-C11-U2-T2.5", "M3-C11-U2-T2.6"], "Cash flow statement: operating, investing and financing activities"),
    ("CAI-P1-PYQ-2026-09-PII-Q4-b", "4", "b", None, None, 4,
     ["M2-C5-U7-T7.7"], "AS 28: impairment loss, revaluation reserve treatment and depreciation"),
    ("CAI-P1-PYQ-2026-09-PII-Q5", "5", None, None, None, 14,
     ["M2-C10-U1-T1.10", "M2-C10-U1-T1.11", "M2-C10-U1-T1.12", "M2-C10-U1-T1.14"], "AS 21: consolidated balance sheet with cost of control, NCI and adjustments"),
    ("CAI-P1-PYQ-2026-09-PII-Q6-a-alt1", "6", "a", "alt1", "Q6a", 4,
     ["M1-C4-U4-T4.3", "M1-C4-U4-T4.7"], "AS 18: related parties and disclosure requirements"),
    ("CAI-P1-PYQ-2026-09-PII-Q6-a-alt2", "6", "a", "alt2", "Q6a", 4,
     ["M2-C8-U2-T2.4", "M2-C8-U2-T2.5", "M2-C8-U2-T2.8"], "AS 9: consignment and bill-and-hold sale recognition"),
    ("CAI-P1-PYQ-2026-09-PII-Q6-b", "6", "b", None, None, 4,
     ["M3-C14-U0-T8"], "Internal reconstruction: journal entries and capital reduction account"),
    ("CAI-P1-PYQ-2026-09-PII-Q6-c", "6", "c", None, None, 6,
     ["M3-C15-U0-T4", "M3-C15-U0-T5"], "Dependent branch accounts under debtors method with goods invoiced above cost"),
]


CURRENT_TOPIC_OVERRIDES = {
    "CAI-P1-RTP-2025-01-PII-Q3": ["M2-C7-U2-T2.4"],
    "CAI-P1-RTP-2025-05-PII-Q4": ["M1-C4-U1-T1.2"],
    "CAI-P1-RTP-2025-05-PII-Q17": ["M1-C4-U4-T4.3"],
    "CAI-P1-RTP-2025-09-PII-Q10": ["M2-C8-U1-T1.5"],
    "CAI-P1-RTP-2025-09-PII-Q11-i": ["M2-C8-U2-T2.4", "M2-C8-U2-T2.5", "M2-C8-U2-T2.8"],
    "CAI-P1-RTP-2025-09-PII-Q11-ii": ["M2-C8-U2-T2.4", "M2-C8-U2-T2.5", "M2-C8-U2-T2.8"],
    "CAI-P1-RTP-2025-09-PII-Q11-iii": ["M2-C8-U2-T2.4", "M2-C8-U2-T2.5", "M2-C8-U2-T2.8"],
    "CAI-P1-MTP-2025-09-S2-PII-Q6-c": ["M3-C11-U1-T1.5"],
    "CAI-P1-PYQ-2025-01-PII-Q6-a-alt2": ["M1-C4-U1-T1.2"],
    "CAI-P1-PYQ-2025-09-PII-Q1-c-i": ["M2-C8-U2-T2.4", "M2-C8-U2-T2.5", "M2-C8-U2-T2.8"],
    "CAI-P1-PYQ-2025-09-PII-Q1-c-iii": ["M2-C8-U2-T2.4", "M2-C8-U2-T2.5", "M2-C8-U2-T2.8"],
    "CAI-P1-PYQ-2025-09-PII-Q1-c-iv": ["M2-C8-U2-T2.4", "M2-C8-U2-T2.5", "M2-C8-U2-T2.8"],
    "CAI-P1-RTP-2026-01-PII-Q7": ["M2-C8-U1-T1.5", "M2-C8-U1-T1.10"],
    "CAI-P1-RTP-2026-01-PII-Q8": ["M2-C8-U2-T2.4", "M2-C8-U2-T2.5", "M2-C8-U2-T2.8"],
    "CAI-P1-RTP-2026-01-PII-Q18": ["M2-C10-U3-T3.2", "M2-C10-U3-T3.5"],
    "CAI-P1-MTP-2026-01-S2-PII-Q3": ["M2-C10-U3-T3.7"],
    "CAI-P1-MTP-2026-01-S2-PII-Q6-a-alt1": ["M2-C8-U2-T2.4", "M2-C8-U2-T2.5", "M2-C8-U2-T2.8"],
    "CAI-P1-MTP-2026-05-S1-PII-Q6-b": ["M1-C4-U1-T1.2", "M1-C4-U1-T1.5", "M1-C4-U1-T1.6"],
}
TAG = re.compile(r"<[^>]+>")
NUM = re.compile(r"(?<![A-Za-z])(?:₹|Rs\.?|`)?\s*\d[\d,]*(?:\.\d+)?\s*(?:%|lakhs?|crores?|years?|months?|days?)?", re.I)
STOP = set("a an the and or to of in on for from by with at as is are was were be been being this that those these it its their company limited ltd accounting standard per under calculate compute prepare find determine required following information amount amounts total".split())

def plain(s): return re.sub(r"\s+", " ", html.unescape(TAG.sub(" ", s or ""))).strip()
def concept(s):
    toks = re.findall(r"[a-z][a-z'-]+", NUM.sub(" value ", plain(s)).lower())
    return " ".join(x for x in toks if x not in STOP and x != "value")
def unit_of(topic_id):
    m = re.match(r"(M\d+-C\d+-U\d+)", topic_id or "")
    return m.group(1) if m else None

def similarity(a, b):
    if not a or not b: return 0.0
    aset, bset = set(a.split()), set(b.split())
    overlap = len(aset & bset)
    jaccard = overlap / max(1, len(aset | bset))
    containment = overlap / max(1, min(len(aset), len(bset)))
    sequence = SequenceMatcher(None, a, b).ratio()
    return max(sequence, .65 * containment + .35 * jaccard)
def extract_study_items():
    from build_pyq_study_matches import study_items
    return study_items()

def sep_texts():
    raw = SEP_HTML.read_text(encoding="utf-8")
    labels = ["1. (a)", "(b) On 1", "(c) Z Technologies", "2. (a)", "(b) B Limited", "3.</strong>", "4. (a)", "(b) Matrix", "5.</strong>", "6. (a)", "OR</p>", "(b) Green", "(c) A firm"]
    starts = [raw.find(x) for x in labels]
    out = []
    for i, start in enumerate(starts):
        end = starts[i+1] if i+1 < len(starts) else raw.find('<div class="rough"', start)
        out.append(plain(raw[start:end]))
    return out

def main():
    topic_catalog = {r["unique_topic_id"]: r for r in json.loads(TOPICS.read_text(encoding="utf-8"))}
    flat = json.loads(FLAT.read_text(encoding="utf-8"))
    source = {q["id"]: q for q in json.loads(INDEX.read_text(encoding="utf-8")) if q.get("part") == "II"}
    questions = []
    for r in flat:
        q = source.get(r["question_id"], {})
        if not r.get("topic_ids") and r["question_id"] in CURRENT_TOPIC_OVERRIDES:
            tids = CURRENT_TOPIC_OVERRIDES[r["question_id"]]
            cats = [topic_catalog[t] for t in tids]
            r = {**r, "topic_ids": tids, "topic_names": [x["topic_name"] for x in cats],
                 "chapter_ids": sorted(set(x["unique_unit_id"] for x in cats)),
                 "final_chapter_id": cats[0]["unique_unit_id"], "final_chapter_name": cats[0]["chapter_name"],
                 "final_unit_name": cats[0]["unit_name"]}
        questions.append({**r, "question_text": plain(q.get("question_html", "")), "answer_text": plain(q.get("answer_html", ""))[:1000]})
    sep_qtexts = sep_texts()
    for n, row in enumerate(SEP_MAP):
        qid, qno, sub, alt, org, marks, tids, summary = row
        cats = [topic_catalog[t] for t in tids]
        questions.append({
            "exam_year": 2026, "paper_type": "PYQ", "attempt_month": "September", "set": None,
            "paper_label": "PYQ September 2026", "question_no": qno, "sub_part": sub,
            "or_alternative": alt, "or_group": org, "marks": marks, "count_in_offered_total": 0 if alt == "alt2" else 1,
            "marks_issue": None, "question_type": "theory" if qid.endswith("alt1") else "practical",
            "final_chapter_id": cats[0]["unique_unit_id"], "final_chapter_name": cats[0]["chapter_name"],
            "final_unit_name": cats[0]["unit_name"], "topic_ids": tids,
            "topic_names": [x["topic_name"] for x in cats], "chapter_ids": sorted(set(x["unique_unit_id"] for x in cats)),
            "source_file": "pyq-september-2026-question-paper.html", "question_id": qid,
            "question_text": sep_qtexts[n] if n < len(sep_qtexts) else summary, "answer_text": "", "mapping_note": summary,
        })

    items = extract_study_items()
    qtexts = [concept(q["question_text"]) for q in questions]
    itexts = [concept(x["question"]) for x in items]

    manual = {x["question_id"]:x for x in json.loads((ROOT/"first_run/output/generated-from-script/pyq_study_matches.json").read_text(encoding="utf-8"))}
    classifications=[]; long=[]
    for i,q in enumerate(questions):
        tids = q.get("topic_ids") or []
        units = {unit_of(t) for t in tids}
        cand = [j for j,x in enumerate(items) if x["unitcode"] in units]
        scored = [(similarity(qtexts[i], itexts[j]), j) for j in cand]
        score, best = max(scored) if scored else (0.0, None)
        override = manual.get(q["question_id"])
        if override and override.get("similarity_percent") is not None:
            pct = float(override["similarity_percent"]); evidence="manually reviewed PYQ match"
            cat = "A" if pct >= 90 else "B" if pct >= 50 else "C"
        elif score >= .90:
            pct=round(score*100,1); cat="A"; evidence="automatic normalized-text match"
        elif score >= .50:
            pct=round(score*100,1); cat="B"; evidence="automatic normalized-text match"
        elif tids:
            pct=None; cat="C"; evidence="topic mapped; no >=50% study-question match"
        else:
            pct=None; cat="D"; evidence="no mapped Study Material topic"
        item = items[best] if best is not None else {}
        cls = {"question_id":q["question_id"],"paper_label":q["paper_label"],"paper_type":q["paper_type"],
               "marks":q.get("marks"),"category":cat,"similarity_percent":pct,"classification_basis":evidence,
               "study_item_type":override.get("study_item_type") if override else item.get("item_type"),
               "study_item_no":override.get("study_item_no") if override else item.get("item_no"),
               "study_source_file":override.get("study_source_file") if override else item.get("source_file"),
               "study_question_excerpt":override.get("study_question_excerpt") if override else (item.get("question","")[:350] or None),
               "question_excerpt":q["question_text"][:500],"topic_ids":tids,"topic_names":q.get("topic_names") or []}
        classifications.append(cls)
        divisor=max(1,len(tids)); or_divisor=2 if q.get("or_group") else 1
        for tid in tids or [None]:
            t=topic_catalog.get(tid,{})
            long.append({
                "question_id":q["question_id"],"paper_type":q["paper_type"],"paper_label":q["paper_label"],
                "exam_year":q["exam_year"],"attempt_month":q["attempt_month"],"set":q.get("set"),
                "question_no":q.get("question_no"),"sub_part":q.get("sub_part"),"or_alternative":q.get("or_alternative"),
                "question_type":q.get("question_type"),"question_marks":q.get("marks") or 0,
                "allocated_marks":(q.get("marks") or 0)/divisor,"or_adjusted_allocated_marks":(q.get("marks") or 0)/divisor/or_divisor,
                "topic_id":tid,"topic_name":t.get("topic_name") or ((q.get("topic_names") or [None])[0]),
                "unit_id":t.get("unique_unit_id"),"unit_name":t.get("unit_name") or q.get("final_unit_name"),
                "chapter_name":t.get("chapter_name") or q.get("final_chapter_name"),"module":t.get("module"),
                "category":cat,"similarity_percent":pct,"classification_basis":evidence,
            })

    # Rank all topics using allocated listed marks across the 10 PYQs. Both OR options count as asked.
    pyq = [r for r in long if r["paper_label"] in PYQ_ORDER and r["topic_id"]]
    agg=defaultdict(lambda:{"marks":0.0,"questions":set(),"attempts":set(),"papers":Counter()})
    for r in pyq:
        a=agg[r["topic_id"]]; a["marks"]+=r["allocated_marks"]; a["questions"].add(r["question_id"]); a["attempts"].add(r["paper_label"]); a["papers"][r["paper_label"]]+=r["allocated_marks"]
    ranks=[]
    for tid,t in topic_catalog.items():
        a=agg[tid]
        ranks.append({"topic_id":tid,"topic_name":t["topic_name"],"unit_name":t["unit_name"],"chapter_name":t["chapter_name"],"module":t["module"],
                      "pyq_allocated_marks":round(a["marks"],2),"pyq_question_count":len(a["questions"]),"pyq_attempt_count":len(a["attempts"]),
                      "attempts_list":", ".join(x for x in PYQ_ORDER if x in a["attempts"]),
                      "marks_by_attempt":{x:round(a["papers"][x],2) for x in PYQ_ORDER}})
    ranks.sort(key=lambda x:(-x["pyq_allocated_marks"],-x["pyq_attempt_count"],-x["pyq_question_count"],x["topic_id"]))
    for pos,r in enumerate(ranks,1):
        r["overall_rank"]=pos; r["priority_band"]="Top 50" if pos<=50 else "Next 50" if pos<=100 else "Beyond Top 100"
    within=defaultdict(int)
    for r in sorted(ranks,key=lambda x:(x["chapter_name"],-x["pyq_allocated_marks"],-x["pyq_attempt_count"],x["topic_id"])):
        within[r["chapter_name"]]+=1; r["chapter_rank"]=within[r["chapter_name"]]

    output={"metadata":{"study_topic_count":len(topic_catalog),"descriptive_question_count":len(questions),"ranking_scope":PYQ_ORDER,
             "ranking_rule":"Sum allocated_marks across ten PYQs; full marks divided equally across mapped topics; both OR alternatives retained as concept exposure.",
             "category_rules":{"A":">=90% similar Study Material question","B":"50% to <90% similar Study Material question","C":"No >=50% question match, but exact Study Material topic mapped","D":"No Study Material topic mapped"}},
            "topic_rankings":ranks,"question_classifications":classifications,"question_topic_rows":long}
    OUT.write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"Wrote {OUT}: {len(questions)} questions, {len(long)} question-topic rows, {len(ranks)} topics")
    print("Categories",dict(Counter(x["category"] for x in classifications)))
    print("Top-100 positive marks",sum(1 for x in ranks[:100] if x["pyq_allocated_marks"]>0),"all positive",sum(1 for x in ranks if x["pyq_allocated_marks"]>0))

if __name__ == "__main__": main()
