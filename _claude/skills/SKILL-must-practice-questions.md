# SKILL: Must Practice questions — how they are chosen, where every input comes from

Read this before adding, changing or explaining anything on
`https://capranav.com/practice-with-pranav-bhaiya/must-practice/`. It is written so a new
agent with no memory of earlier sessions can follow the same method and trust the same data.
Commands, file paths and the add-a-unit steps live in `capranav_com_revamped/MUST-PRACTICE.md`;
the scoring formula and every hand exclusion live in
`books/ca-inter/smat-may-27-edition/practice-with-pranav-bhaiya/MUST-PRACTICE-RULES.md`.
This file is the "why", the data provenance, and the rule for units that have too few questions.

## 1. What a Must Practice list is

For each syllabus unit (for example AS 2), up to **ten descriptive questions** that ICAI is most
likely to set again, each with its answer. The test is "most likely to be set again", not
"hardest" and not "most interesting to teach". MCQs are never on this page: the question
bank's MCQs and case-MCQs are for drilling on a practice platform, and they carry no written
answer to show.

## 2. Status (update this table when something changes)

| Piece | State (2026-10-18) |
|---|---|
| Standard units (10 or more usable questions) | Published for AS 2, AS 10, AS 16. AS 2 and AS 10 hand-reviewed for same-idea repeats; AS 16 formula-only, review outstanding. |
| Short-unit rule (section 6) | **Decided by Pranav 2026-10-18; analysis script built; not yet applied to any live unit.** |
| `first_run/scripts/build_study_material_pool.py` | Built. Finds Study Material items not already covered by the Question Bank. Output is an upper bound, see section 6.4. |
| Extracting Study Material **answers** from the ICAI PDFs | **Not built.** The markdown copy has scrambled tables, so answers cannot be copied from it. |
| Topic ranking for Study Material items | **Not built.** The ranking only maps Question Bank questions. |
| Page/source label for Study Material items on the site | **Not built.** The page currently shows only a Question Bank page number. `must-practice.js` and the unit JSON need a source-kind field first. |
| Units AS 3 (`M1-C4-U2`) and AS 14 (`M2-C9-U2`) | **Open decision.** The question bank files this content under `M3-C11-U2` (Cash Flow) and `M3-C13-U0` (Amalgamation); the Module 1/2 units have no bank questions at all. |
| Gating answers behind login | **Open decision** (see `capranav_com_revamped/AGENT-HANDOFF.md`). Today every answer is public static JSON. |

## 3. Inputs: what each is, who made it, how, and how to remake it

Nothing below is hand-typed on the live site. Pages are generated; fix the source or the
generator, never the output.

| Input | What it is | How it was made |
|---|---|---|
| **Source papers** `first_run/source/*.pdf` | ICAI's MTP, RTP and PYQ papers plus answers (2023 onward), and the six real Examiner's Comments documents | Downloaded from ICAI by Pranav. PDFs only, never markdown (see `SKILL-question-bank-verbatim-extraction.md`). Gitignored. |
| **Sitting HTML** `first_run/output/parsed-from-pdf/*.html` | One self-contained HTML file per paper: every question and answer verbatim, tagged to syllabus topics | An AI reads the PDF with a strict schema (`first_run/schema/HTML-SCHEMA.md`, prompts in `first_run/prompts/`), then Pranav and Claude review. 34 sittings. Full method: `SKILL-question-bank-pipeline-overview.md`. |
| **`questions_index.json`** | One row per question across all sittings, MCQs included | `first_run/scripts/extract_questions.py` reads the sitting HTML. No AI involved. |
| **Printed book** `first_run/output/final_deliverable/..._V1.pdf` | The distributed Question Bank, first edition | Built by the chapter-book and merge scripts (`first_run/HOW-TO-BUILD-THE-BOOK.md`). Never overwrite. Must Practice reads it only to find each question's printed page number. |
| **Syllabus index** `books/ca-inter/concept-book/syllabus-engine/data/1-ca-inter-adv-accounts-topic-page-index.json` | Canonical list of 36 units and 400 topics with page numbers | Built from Pranav's spreadsheet `CA INTER ADV ACCOUNTS - For Adarsh.csv`, cross-checked 1:1 against the locked master syllabus file. Topic ids look like `M2-C5-U1-T1.3`. Details in `CLAUDE.md` section 6. |
| **`mcq-library/*_Descriptive.json`** (the pool Must Practice picks from) | The Question Bank's descriptive questions, one file per unit, with verbatim question and answer HTML, marks, source label, Examiner's Comment or Author's Note | A snapshot copied from the Main1Lavya repo (`data/README.md` calls it that). Its field layout matches the printed book's chapter questions, so it appears to be derived from the book; **the script that produced it is not in this repo.** Counts per unit match the book's descriptive questions. |
| **`study_material_topics_flat.json`**, **`question_bank_descriptive_flat_through_may2026.json`** | Flat copies of the 400 topics and of every descriptive question | `first_run/scripts/build_sheet_jsons.py` from the syllabus index and `questions_index.json`. |
| **`raw_icai_study_materials/*.md`** | ICAI Study Material text for each unit | Converted from ICAI's PDFs. The converter is not recorded in this repo. **Tables and solutions are scrambled** (rows displaced, numbers detached), so use it to read questions and find Illustration or Test Your Knowledge numbers, never to copy answers. |
| **`study_material_tyk.json`** | Test Your Knowledge questions with answers for 14 chapters only | `first_run/scripts/extract_study_material_tyk.py`. |
| **`pyq_study_matches.json`** | Each past-paper question matched to the Study Material question it came from | `first_run/scripts/build_pyq_study_matches.py`: a lexical candidate list plus **manually reviewed** `SAME_CONCEPT` and partial-concept tables. A lexical candidate is not a verified match. |
| **`descriptive_topic_priority.json`** | The ranking: 400 topics ranked by PYQ marks over the ten latest PYQs (May 2023 to Sep 2026), Top 50 and Next 50 bands, every question mapped to topics, and the A/B/C/D Study Material category | `first_run/scripts/build_descriptive_topic_priority.py`. Categories: **A** 90% or more similar to a Study Material question; **B** 50% to under 90%; **C** no 50% match but the topic exists in the Study Material; **D** no Study Material topic. **Hand input inside it:** `SEP_MAP` (September 2026 PYQ mapped by hand, because its official answers are not yet integrated) and `CURRENT_TOPIC_OVERRIDES` (reviewed topic fixes). |

To rebuild the chain: `build_sheet_jsons.py`, then `build_pyq_study_matches.py` (needs
scikit-learn), then `build_descriptive_topic_priority.py`, then
`capranav_com_revamped/tools/build_must_practice_data.py`. Do not rerun the earlier stages unless
the corpus or ranking changed; they contain reviewed hand tables.

## 4. How the ten are chosen (summary, full reasoning in MUST-PRACTICE-RULES.md)

Score out of 1.0: topic weight 40%, Study Material match 25%, source and recency 20%
(MTP 1.0, RTP 0.95, PYQ 0.6, because an MTP or RTP signals the coming paper better than a past
PYQ), marks 15%. Then drop repeats (text 90% alike, or 5 or more shared figures covering 60% of
the smaller question), allow at most two per topic, make sure every Top-100 topic of the
chapter is covered, and fill to ten. Weights live only in `SCORING` in
`build_must_practice_data.py`.

## 5. Standard unit: the steps

1. Add the unit to `UNITS` in `build_must_practice_data.py` and build.
2. Read the printed ranking and the "repeat dropped" lines.
3. **Review by hand for repeats the formula cannot see**: parts of one question reissued alone,
   and the same idea under unrelated topic tags. Add `force_exclude` entries with a written
   reason; record them in the table in MUST-PRACTICE-RULES.md.
4. `build_seo_static.py`, deploy, then `tools/verify_must_practice_live.py <unit>`.
5. Log it (`capranav_com_revamped/PROJECT-LOG.md`, `_claude/memory/project_log.md`) and update the
   published-unit lists in the docs.

## 6. Short units (fewer than 10 usable questions): Pranav's rule, 2026-10-18

### 6.1 The rule

Do not pad a short unit with weak or repeated questions, and do not lean on the Study Material
alone. Instead:

1. Take every descriptive question the Question Bank has for the unit.
2. Also take the Study Material's own Illustrations and Test Your Knowledge descriptive
   questions.
3. Remove questions that are the same as another (a Study Material item that a past paper already
   reused counts as covered). Keep only **unique, non-similar** questions.
4. Publish what is left, **even if that is fewer than ten**. The page should say how many
   questions exist ("all N available") rather than pretend.

### 6.2 Why a Study Material item needs more work than a bank question

- Its **answer** exists only in a scrambled markdown copy; it has to be extracted from the ICAI PDF
  and checked, the same standard as the sitting HTML (PDF is the source of truth).
- It has **no topic ranking** until someone maps it to topics in the syllabus index.
- It has **no Question Bank page number**; the site must label it as, for example, "ICAI Study
  Material, Illustration 3".

### 6.3 What is built: the pool script

`python first_run/scripts/build_study_material_pool.py` (standard library only) compares each
Illustration and TYK descriptive item to the unit's Question Bank questions and writes
`.../practice-with-pranav-bhaiya/data/study_material_descriptive_pool.json`. Verdicts:
`duplicate_of_bank`, `covered_by_reviewed_match` (already named in `pyq_study_matches.json`),
`duplicate_of_study_item`, `review` (a human must look), `unique`.

### 6.4 Honest limits of that script

- Similarity is lexical (TF-IDF plus a shared-figures test). On the human-reviewed same-concept
  pairs it scored as low as ~0.28, because wording and figures change between a Study Material
  illustration and the exam question built on it. That is why reviewed matches override it and
  the review threshold is low (0.25). **"Unique" means "not obviously covered", not verified.**
  Every unit still needs a human pass over its `review` and `unique` items.
- The list sizes it prints are **upper bounds**: each unique item still needs a verified answer.
- Study Material illustrations whose solutions are missing, or are tables that cannot be rebuilt
  from the PDF, must be dropped rather than published with a guessed answer.

### 6.5 What it showed on 2026-10-18 (re-run the script for current numbers)

Units where the Study Material adds questions beyond the bank, as an upper bound before review
and answer extraction: AS 25 (bank 2, up to 4), AS 23 (4, up to 6), AS 27 (2, up to 5), AS 22 (4,
up to 6), Applicability, Introduction to AS and AS 24 (no Study Material items, so they stay at
3, 8 and 9). AS 18 reaches ten from the bank plus extras, AS 1 is already ten, and AS 17 reaches nine. AS 3 and AS 14 are
the open duplicate-code decision in section 2.

### 6.6 Steps for a short unit

1. Run the pool script and read that unit's items in the JSON output.
2. Judge every `review` and `unique` item against the bank questions of the unit.
3. For each kept Study Material item, extract question and answer from the ICAI **PDF**, rebuild
   its tables, and check the arithmetic. Tag it to the syllabus topic (from file 1 in section 3).
4. Add a source-kind field to the unit JSON and update `must-practice.js` to label it. Do the
   same for the SEO block in `build_seo_static.py`.
5. Build, deploy, verify; log which items were dropped and why.

## 7. Rules that apply to every unit

- Edit generators, never generated output (`public/.../data/*.json`, the `ssr` blocks).
- PDF is the source of truth for any question or answer text; markdown is a reading aid only.
- Never regenerate or overwrite `first_run/output/final_deliverable/`.
- Any defect found in the first-edition Question Bank goes in
  `first_run/SECOND-EDITION-CHANGE-REQUESTS.md` first (`SKILL-question-bank-change-log.md`).
- Another AI session may be working in this repo; check `git log` and file times before assuming a
  file is yours.
- OP/PP duplicate tagging is out of scope for edition 1. Must Practice's repeat test is a separate,
  local use of the same 90% idea.
