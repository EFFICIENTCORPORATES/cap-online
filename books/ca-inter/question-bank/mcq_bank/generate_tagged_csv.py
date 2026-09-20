# Merges tag_batch01.py..tag_batch10.py (the per-row chapter/unit/topic tagging
# decisions, one dict per 50-row batch of Questions_Accounts.csv) into
# Questions_Accounts_topic_tagged.csv, and prints a QA report (regex AS-mention
# cross-check, case_study_id cross-chapter cluster list, per-chapter coverage).
# Re-run this after editing any tag_batchNN.py file to regenerate the CSV.
import importlib.util, csv, re, html as ihtml, json
from collections import Counter, defaultdict

# 1. Load all batch tag dicts
ALL = {}
for i in range(1, 11):
    fname = f'tag_batch{i:02d}.py'
    spec = importlib.util.spec_from_file_location(f'batch{i}', fname)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    ALL.update(mod.TAGS)

assert len(ALL) == 477, len(ALL)

# 2. Load original CSV
with open('Questions_Accounts.csv', encoding='utf-8', errors='replace') as f:
    r = csv.DictReader(f)
    fieldnames = r.fieldnames
    rows = list(r)
idcol = fieldnames[0]

def strip(t):
    t = re.sub(r'<[^>]+>', ' ', t or '')
    t = ihtml.unescape(t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t

as_pat = re.compile(r'AS[\s-]?(\d{1,2})\b')

# 3. Build enriched rows + run cross-checks
new_fieldnames = fieldnames + [
    'topic_scope', 'unique_chapter_ids', 'standards', 'topic_nos',
    'unique_topic_ids', 'topic_names', 'page_numbers',
    'tagging_confidence', 'tagging_notes'
]

out_rows = []
mismatch_flags = []
chapter_counter = Counter()
case_chapters = defaultdict(set)
case_rows = defaultdict(list)

for idx, row in enumerate(rows, start=1):
    tag = ALL[idx]
    chapters = tag['chapters']  # list of (unitCode, standard, [(topic_no, topic_name, page)])
    unitCodes = [c[0] for c in chapters]
    standards = [c[1] if c[1] else '' for c in chapters]
    topic_nos = []
    topic_names = []
    pages = []
    unique_topic_ids = []
    for unitCode, standard, topics in chapters:
        for tno, tname, page in topics:
            topic_nos.append(tno)
            topic_names.append(tname)
            pages.append(page)
            unique_topic_ids.append(f"{unitCode}-T{tno}")
        chapter_counter[unitCode] += 1

    case_id = row['case_study_id']
    if case_id:
        for uc in unitCodes:
            case_chapters[case_id].add(uc)
        case_rows[case_id].append(idx)

    new_row = dict(row)
    new_row['topic_scope'] = tag['scope']
    new_row['unique_chapter_ids'] = ', '.join(unitCodes)
    new_row['standards'] = ', '.join(s for s in standards if s) if any(standards) else ''
    new_row['topic_nos'] = ', '.join(topic_nos)
    new_row['unique_topic_ids'] = ', '.join(unique_topic_ids)
    new_row['topic_names'] = ', '.join(topic_names)
    new_row['page_numbers'] = ', '.join(pages)
    new_row['tagging_confidence'] = tag['confidence']
    new_row['tagging_notes'] = tag['notes']
    out_rows.append(new_row)

    # Cross-check: regex AS-mentions in question+explanation vs assigned standards
    text = strip(row['question_html']) + ' ' + strip(row['explanation_html'])
    mentioned = set(as_pat.findall(text))
    assigned = set(s.replace('AS ', '').strip() for s in standards if s)
    if mentioned and assigned and not (mentioned & assigned):
        mismatch_flags.append((idx, sorted(mentioned), sorted(assigned), tag['confidence']))

# 4. Write final CSV
with open('Questions_Accounts_topic_tagged.csv', 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=new_fieldnames)
    w.writeheader()
    for row in out_rows:
        w.writerow(row)

print('=== Final CSV written:', len(out_rows), 'rows ===')

# 5. Report regex mismatches
print()
print(f'=== AS-mention cross-check: {len(mismatch_flags)} rows where assigned standard(s) do not appear among regex-detected AS-numbers in text ===')
for idx, mentioned, assigned, conf in mismatch_flags:
    print(f'  row {idx}: text mentions AS{mentioned}, assigned={assigned} (confidence={conf})')

# 6. Case cluster consistency report
print()
print(f'=== Case-study clusters spanning multiple chapters: {sum(1 for v in case_chapters.values() if len(v)>1)} of {len(case_chapters)} clusters ===')
for cid, chaps in sorted(case_chapters.items(), key=lambda x: -len(x[1])):
    if len(chaps) > 1:
        print(f'  case {cid[:8]}: {len(case_rows[cid])} rows, chapters={sorted(chaps)}')

# 7. Coverage summary
print()
print('=== Coverage by unitCode (question count) ===')
for uc, cnt in sorted(chapter_counter.items()):
    print(f'  {uc}: {cnt}')

print()
print('=== Confidence distribution ===')
conf_counter = Counter(ALL[i]['confidence'] for i in range(1,478))
print(dict(conf_counter))

print()
print('=== Scope distribution ===')
scope_counter = Counter(ALL[i]['scope'] for i in range(1,478))
print(dict(scope_counter))
