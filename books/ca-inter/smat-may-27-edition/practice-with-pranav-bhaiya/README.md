# Practice with Pranav Bhaiya — Working Hub

This folder is the single working hub for the YouTube live question-practice series for CA Intermediate Advanced Accounting.

The series is **not** a marathon, one-shot, revision lecture, or substitute for concept classes. It trains examination execution: question decoding, concept-and-data selection, answer format, conclusion, error detection, and time management.

## Current structure

| Folder/file | What it contains | Current status |
|---|---|---|
| `data/ca_inter_practice_index_v3_sep2026.xlsx` | Main practice index: Summary, descriptive Questions, and Study Material topics | September 2026 PYQ added at chapter level |
| `data/question_bank_descriptive_flat_through_may2026.json` | Machine-readable descriptive index used for the earlier workbook | 496 records; does not yet include September 2026 |
| `data/study_material_topics_flat.json` | Machine-readable Study Material topic index | 400 topic rows |
| `data/pyq_study_matches_through_may2026.json` | Reviewed PYQ-to-Study-Material question matches | Through May 2026 |
| `data/last-six-pyq-marks-split.json` | Six-PYQ chapter averages with separate MCQ and descriptive splits | January 2025 to September 2026 |
| `data/descriptive_topic_priority.json` | Question-level A/B/C/D evidence, long topic map, and ten-PYQ topic rankings | 509 descriptive questions through September 2026 |
| `data/ca_inter_descriptive_topic_priority_v1.xlsx` | Pivot-ready descriptive topic-priority workbook | Top 50, next 50, chapter ranks, attempts, and classifications |
| `data/mcq-library/` | Main1Lavya chapter-wise MCQ and descriptive practice JSON files | Copied working snapshot; Main1Lavya remains the upstream source |
| `sources/pyq-september-2026-question-paper.html` | Supplied September 2026 ICAI question paper | Source for the newly added workbook rows |
| `sources/study-material-validation-summary.md` | Corpus completeness and block-count validation | May 2027 Study Material corpus |
| `google-drive-links.md` | Shareable Drive-link register for files mentioned during live classes | Awaiting links from Pranav |
| `MUST-PRACTICE-RULES.md` | The formula that picks the ten Must Practice questions per unit, with every hand exclusion | AS 2, AS 10, AS 16 published on capranav.com |
| `slides/day-01-opening.html` | Opening sequence for Day 1 | Interactive HTML presentation |
| `slides/day-01-syllabus-flow.html` | Four-part syllabus build and consolidation animation | Interactive HTML presentation |
| `slides/day-01-marks-split.html` | Four-part and 15-chapter PYQ footprint, followed by the AS 2 transition | Interactive HTML presentation |

## How this data reaches capranav.com

`descriptive_topic_priority.json` and `mcq-library/` here are the inputs to `capranav_com_revamped/tools/build_must_practice_data.py`, which writes the static JSON behind the live Must Practice page. The whole chain, how to add a unit and how to verify it live: `capranav_com_revamped/MUST-PRACTICE.md`. Do not edit the generated JSON under `capranav_com_revamped/public/`; edit the inputs here or the generator, and re-run.

## September 2026 status

The workbook now includes **13 descriptive records** for the September 2026 PYQ:

- MCQ marks: **30**
- Descriptive marks listed before OR de-duplication: **88**
- OR overlap: **4**
- Descriptive marks offered after OR de-duplication: **84**
- Answerable paper total: **100**

Chapter mapping has been added. Detailed topic IDs, official-answer verification, and Study Material illustration/TYK matching remain deliberately marked pending. The supplied file is the question paper, not the official suggested answer.

## Source-of-truth rules

1. The original files remain the upstream sources; this folder is a working snapshot for the series.
2. Do not add counts from the workbook, Study Material corpus, and Main1Lavya library together without de-duplicating overlapping questions.
3. Topic mapping does not prove that a PYQ is copied from a Study Material question.
4. Use `study_match_status` and the supporting source fields before making an exact-match claim on a slide.
5. A new paper is not fully integrated until its question text, marks, OR structure, chapter/topic mapping, official answer, and Study Material match review are complete.

## Next integration work

1. Map September 2026 questions to detailed topic IDs.
2. Add the September 2026 official suggested answers when available.
3. Run the independent Study Material match review.
4. Complete the question-level review for the one unmapped January 2025 MCQ.
5. Create the Live Full Solve / Live Summary / PP / Skim-Duplicate classification for AS 2.
