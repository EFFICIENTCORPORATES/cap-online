# SKILL — MCQ Bank: Chapter/Unit/Topic Tagging (`Questions_Accounts.csv`)

> **What this is:** how `books/question-bank/mcq_bank/Questions_Accounts.csv` (477
> standalone MCQs, a separate track from the MTP/RTP/PYQ sitting-HTML pipeline) got
> mapped to the syllabus taxonomy at chapter/unit/topic granularity (e.g. `M2-C5-U1`,
> topic `1.7`), what was found along the way, and how to extend or re-run the tagging.
>
> This is a sibling of the sitting-HTML pipeline's skills, not a replacement — read
> `SKILL-question-bank-topic-tagging.md` (in `_claude/skills/`) first for the taxonomy
> join-key rules (which file is authoritative, the U0/U1 history, `data-topic-rank`); this
> skill only covers what's specific to tagging a flat MCQ CSV instead of sitting HTML:
> the coarse-bucket problem, the batch-tagging workflow, and findings new to this pass.

---

## 1. The starting problem: `chapter_id` in the CSV is not a real chapter

`Questions_Accounts.csv` ships with a `chapter_id` column, but it is a **coarse grouping
label**, not a `unitCode`. Comparing its 15 distinct values against
`books/concept-book/syllabus-engine/data/1-ca-inter-adv-accounts-topic-page-index.json`
(the canonical file — see the sibling skill for why) showed `chapter_id` is literally
that file's `chapter_name` field, which several `unitCode`s can share — e.g. "Assets
Based Accounting Standards" spans 7 units (AS2, 10, 13, 16, 19, 26, 28). Roughly 270 of
477 rows needed real chapter-level disambiguation before any topic-level tagging was
possible; the other ~205 (Buy-back, Framework, Introduction, Applicability, Amalgamation,
Reconstruction, Branches) were already at the correct chapter (single- or near-single-unit
groups) and only needed topic-level resolution.

**Consequence: `chapter_id` was treated as a weak prior, never ground truth.** Every row
was tagged by reading its actual `question_html` + `explanation_html`, not by trusting
the bucket label. Confirmed mismatches were found and tagged per content, not per label
(e.g. row 69: CSV says "Other Accounting Standards", content is AS 20, which canonically
belongs to the Presentation & Disclosures chapter group).

## 2. Taxonomy source and column schema

Per `SKILL-question-bank-topic-tagging.md`: `unitCode` + numbered topic come from file 1
(canonical, all 36 chapters, has the dotted `topic_no` format the CSV's own reference
spreadsheet uses, e.g. `2.7`); `topic-index.json`'s prose descriptions were used
opportunistically to disambiguate content, not as the numbering authority.

Nine columns were appended to a **copy** of the CSV (original untouched):

| Column | Content |
|---|---|
| `topic_scope` | `single` (one chapter/unit) or `multiple` (genuinely connected content spanning >1 unit — 7 of 477 rows) |
| `unique_chapter_ids` | comma-separated `unitCode`(s), e.g. `M2-C5-U4` |
| `standards` | comma-separated AS number(s), blank for Companies-Act chapters |
| `topic_nos` | comma-separated dotted topic numbers from file 1, e.g. `4.6, 4.7` |
| `unique_topic_ids` | comma-separated `{unitCode}-T{topic_no}`, the precise machine key |
| `topic_names` | comma-separated topic names, for human readability |
| `page_numbers` | comma-separated page refs from file 1 |
| `tagging_confidence` | `confident` \| `inferred` \| `flagged` — see §4 |
| `tagging_notes` | free text: why inferred, cross-chapter cluster membership, data-quality flags |

`topic_scope` answers "does this MCQ test one chapter or genuinely several", per
Pranav's instruction — it is not about how many `topic_no`s are listed (a single chapter
can still list 2 adjacent topic numbers, e.g. `4.6, 4.7`, and stay `single`).

## 3. Workflow used (reproducible)

1. Dumped the CSV in HTML-stripped, UTF-8 condensed batches of 50 rows to a scratch
   `.txt` file (question, options, correct answer, explanation truncated to 500 chars),
   read via the `Read` tool — full explanation wasn't needed for tagging in the vast
   majority of rows, the question stem + correct option were usually sufficient.
2. Classified each row by hand (chapter → topic), writing the decision as a Python dict
   literal into `tag_batchNN.py` (`N` = 1–10, 50 rows each) — one `TAGS = {row_index:
   dict(chapters=[...], scope=..., confidence=..., notes=...), ...}` per file.
3. `generate_tagged_csv.py` merges all 10 batch files, joins them back onto the original
   CSV by row position, and writes `Questions_Accounts_topic_tagged.csv`.
4. Same script also runs the QA checks in §5 and prints a report.

**To extend or fix a tag:** edit the relevant row's entry in its `tag_batchNN.py`, then
re-run `python generate_tagged_csv.py` — it's fully regenerable, nothing is hand-edited
in the output CSV directly (same discipline as the sitting-HTML pipeline's Layer
1→Layer 2 split).

## 4. Confidence levels — what each means

- **`confident`** (374 rows): both chapter and topic-number match are solid.
- **`inferred`** (96 rows): chapter is solid but the topic-number match is coarser than
  ideal, almost always because file 1 gives very few topics for that whole chapter —
  Buy-back (`M3-C12-U0`, 2 topics for 40 questions), Applicability (`M1-C3-U0`, 2 topics),
  or a genuine gap where file 1 doesn't separately number a well-known sub-concept (e.g.
  AS10 depreciation mechanics, AS10 Revaluation Model — both real, heavily-tested topics
  with no distinct `topic_no` in file 1's 10-entry list for that unit).
- **`flagged`** (7 rows): something beyond normal tagging judgment — see §6.

## 5. Validation run (see `qa_report.txt`, regenerated by the script each run)

1. **Regex AS-mention cross-check**: every row's text was scanned for explicit `AS n`
   citations and compared against the assigned standard; **0 mismatches** — no row was
   tagged to a standard that contradicts an explicit citation in its own text.
2. **Case-study cluster consistency**: rows sharing a `case_study_id` were grouped and
   checked for chapter agreement. **14 of 26 clusters span more than one chapter** — see
   §6.
3. **Coverage summary**: per-`unitCode` question counts, cross-checked against the
   original `chapter_id` distribution as a sanity table.

## 6. Findings worth carrying forward (not silently resolved)

- **Cross-chapter case-scenario clusters are common in this bank, more than in the
  sitting-HTML pilot.** This is the same open issue logged in
  `SKILL-question-bank-topic-tagging.md` §4 (and `SKILL-question-bank-chapter-book-rendering.md`
  §3) for sitting HTML — each MCQ was tagged individually with the cluster flagged in
  `tagging_notes`, never resolved unilaterally. Largest clusters found: `5c708acd` and
  `3b2dee7b`/`c2aa648f` each span **4 different chapters** under one shared narrative.
- **A second duplicate-chapter pair, structurally like the known AS3/Cash-Flow one**
  (`M1-C4-U2` vs `M3-C11-U2`, see the sibling skill): Amalgamation content exists in both
  `M2-C9-U2` (AS 14, conceptual — 14 topics) and `M3-C13-U0` (Amalgamation of Companies,
  Companies-Act procedural — 7 topics), with real overlap (both have a "Types of
  Amalgamation" and a "Purchase Consideration" topic). Rule applied for this pass: prefer
  `M2-C9-U2` whenever a matching AS14 topic exists; fall back to `M3-C13-U0` only for pure
  bookkeeping mechanics AS14's topic list doesn't cover (vendor-book-closing entries,
  purchaser's entries, unrealised-profit elimination). Flagged in the notes of every
  affected row (e.g. rows 106, 304, 447, 452) for Pranav's review — same kind of decision
  he's already made once for Cash-Flow, not re-litigated here.
- **3 rows are placeholder/test data**, not real questions (rows 224, 291, 454 — literal
  text "Q1 for case study N" / "Option A" / "Question" / "Explanation"). Tagged loosely
  and flagged rather than skipped, since every row needed an entry in the output CSV.
- **Row 382 is a strong candidate for a mechanical OP/PP duplicate** of row 151 per
  `SKILL-question-bank-duplicate-detection.md`'s rule (same structure, same numbers ×100)
  — flagged, not resolved, since that skill's detection pass hasn't been run against this
  bank yet.
- **AS19 (Leases) has no lessor-side topic** in file 1's list for `M2-C5-U2` — only
  `5.8 Accounting for Finance Leases (Books of lessee)` — yet the bank has lessor
  questions (Gross Investment, Unearned Finance Income, lease-rent computation). Mapped
  to `5.3 Definitions` as the least-wrong fit; a real content gap, not a tagging error.

## 7. Non-negotiable rules carried over unchanged from the sitting-HTML pipeline

Same as `SKILL-question-bank-topic-tagging.md` §6 (via `SKILL-question-bank-pipeline-overview.md`):
never invent a new ID scheme, never silently guess on ambiguity (flag it in
`tagging_notes` instead), original source data is never edited in place.
