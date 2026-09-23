"""Build two flat, Google-Sheets-ready JSON files.
1) study_material_topics_flat.json  - one row per study-material topic (file 1 of syllabus-engine)
2) question_bank_descriptive_flat.json - one row per descriptive question record (MCQs excluded)
Read-only over existing data; safe to re-run."""
import json, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
T = ROOT/"books/ca-inter/concept-book/syllabus-engine/data/1-ca-inter-adv-accounts-topic-page-index.json"
Q = ROOT/"first_run/output/generated-from-script/questions_index.json"
OUT = ROOT/"first_run/output/sheet-ready-json"
OUT.mkdir(exist_ok=True)

idx = json.load(open(T, encoding="utf-8"))
topics, lookup, chap_name = [], {}, {}
for c in idx["chapters"]:
    chap_name[c["unique_chapter_id"]] = c
    for t in c["topics"]:
        row = {
            "unique_topic_id": t["unique_topic_id"],
            "topic_no": t["topic_no"],
            "topic_name": t["topic_name"],
            "topic_name_short": t.get("topic_name_abbvtd"),
            "page_number": t["page_number"],
            "unique_unit_id": c["unique_chapter_id"],
            "unit_no": c["unit_no"],
            "unit_name": c["unit_name"],
            "standard": c["standard"],
            "chapter_no": c["chapter_no"],
            "chapter_name": c["chapter_name"],
            "chapter_name_short": c.get("chapter_name_short"),
            "module": c["module"],
            "module_acronym": c["module_acronym"],
            "teaching_sequence": c["teaching_sequence"],
            "topic_id_name": t["topics_id_name"],
        }
        topics.append(row)
        lookup[(c["unique_chapter_id"], str(t["topic_no"]))] = row
json.dump(topics, open(OUT/"study_material_topics_flat.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)


order = {}
for row in topics: order.setdefault(row["unique_unit_id"], []).append(row["topic_no"])
def resolve(uc, ref):
    """subtopicref may be '1.5', '6/7', '2.6-2.7', '2.4.2' or 'n/a' -> list of matching topic rows."""
    if not ref or ref == "n/a": return []
    found = []
    for part in str(ref).split("/"):
        part = part.strip()
        if "-" in part:
            a, b = [x.strip() for x in part.split("-", 1)]
            seq = order.get(uc, [])
            if a in seq and b in seq:
                found += [lookup[(uc, n)] for n in seq[seq.index(a):seq.index(b)+1]]
                continue
        cand = part
        while cand:
            if (uc, cand) in lookup: found.append(lookup[(uc, cand)]); break
            cand = cand.rsplit(".", 1)[0] if "." in cand else ""
    return found
unresolved = []
MORD = {"01":1,"05":5,"09":9,"11":11}
TYPE_ORD = {"RTP":0,"MTP":1,"PYQ":2}
MON = {"01":"January","05":"May","09":"September","11":"November"}
rows = [r for r in json.load(open(Q, encoding="utf-8")) if r["part"] == "II"]
match_path = ROOT/"first_run/output/generated-from-script/pyq_study_matches.json"
matches = {m["question_id"]: m for m in json.load(open(match_path, encoding="utf-8"))} if match_path.exists() else {}
def key(r):
    return (int(r["exam_year"]), TYPE_ORD[r["paper_type"]], int(r["exam_month"]), int(r.get("set") or 0),
            int(re.sub(r"\D","",str(r["qno"] or r["parent_qno"])) or 0), str(r.get("subpart") or ""), str(r.get("alt") or ""))
rows.sort(key=key)
out = []
seen_or_groups = set()
for r in rows:
    ids, names, chs = [], [], []
    for tp in r["topics"]:
        uc, ref = tp.get("unitcode"), tp.get("subtopicref")
        if uc not in chs: chs.append(uc)
        hits = resolve(uc, ref)
        if hits:
            for h in hits:
                if h["unique_topic_id"] not in ids:
                    ids.append(h["unique_topic_id"]); names.append(h["topic_name"])
        else:
            unresolved.append((uc, ref))
    fc = r["final_chapter"]
    or_key = (r["source_file"], r.get("alt_group")) if r.get("alt_group") else None
    count_in_offered_total = 0 if or_key and or_key in seen_or_groups else 1
    if or_key: seen_or_groups.add(or_key)
    match = matches.get(r["id"], {}) if r["paper_type"] == "PYQ" else {}
    last_topic_only = len(ids) == 1 and any(
        ids[0] == lookup[(uc, order[uc][-1])]["unique_topic_id"]
        and "disclosure" in lookup[(uc, order[uc][-1])]["topic_name"].lower()
        for uc in chs if uc in order and order[uc] and (uc, order[uc][-1]) in lookup
    )
    out.append({
        "exam_year": int(r["exam_year"]),
        "paper_type": r["paper_type"],
        "attempt_month": MON[r["exam_month"]],
        "set": r.get("set"),
        "paper_label": f'{r["paper_type"]} {MON[r["exam_month"]]} {r["exam_year"]}' + (f' Set {r["set"]}' if r.get("set") else ""),
        "question_no": str(r["qno"] or r["parent_qno"]),
        "sub_part": r.get("subpart"),
        "or_alternative": r.get("alt"),
        "or_group": r.get("alt_group"),
        "marks": r["marks"],
        "count_in_offered_total": count_in_offered_total,
        "marks_issue": r.get("issue"),
        "question_type": r["qtype"],
        "final_chapter_id": fc,
        "final_chapter_name": chap_name[fc]["chapter_name"] if fc in chap_name else None,
        "final_unit_name": chap_name[fc]["unit_name"] if fc in chap_name else None,
        "topic_ids": ids,
        "topic_names": names,
        "chapter_ids": chs,
        "source_file": r["source_file"],
        "question_id": r["id"],
        "topic_mapping_review": "Last disclosure topic only; verify by concept, not page position" if last_topic_only else None,
        "study_match_status": match.get("match_status"),
        "concept_similarity_percent": match.get("similarity_percent"),
        "study_item_type": match.get("study_item_type"),
        "study_item_no": match.get("study_item_no"),
        "study_source_file": match.get("study_source_file"),
        "study_question_excerpt": match.get("study_question_excerpt"),
        "study_match_note": match.get("match_note"),
    })
json.dump(out, open(OUT/"question_bank_descriptive_flat.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("topics:", len(topics), "| questions:", len(out), "| unresolved topic refs:", len(unresolved))
import collections
print("unresolved detail:", collections.Counter(("LEGACY" if str(u).startswith("LEGACY") else "n/a-in-syllabus" if r=="n/a" else "other") for u,r in unresolved), [x for x in unresolved if not str(x[0]).startswith("LEGACY") and x[1]!="n/a"][:10])
print("years:", sorted({o["exam_year"] for o in out}))
print("not in syllabus:", sum(1 for o in out if o["final_chapter_name"] is None), {o["final_chapter_id"] for o in out if o["final_chapter_name"] is None})
