# Must Practice — end-to-end runbook (question corpus → live page)

Read this if the task is "publish / fix / explain a Must Practice list". It is the one place that follows the
whole chain from raw exam papers to the page at
`https://capranav.com/practice-with-pranav-bhaiya/must-practice/`.

**Published units (2026-10-06):** AS 2 (`M2-C5-U1`), AS 10 (`M2-C5-U2`), AS 16 (`M2-C5-U4`). The picker lists
every syllabus unit from the 400-topic ranking; unpublished ones show "coming soon". AS 2 and AS 10 were
hand-reviewed for same-idea repeats; AS 16 is formula-only (review still outstanding, see `PROJECT-LOG.md`).

## What the page is

For each unit, **ten descriptive questions** (never fewer, never more) that ICAI is most likely to set again,
each with source, marks, topic rank tags, a "Why this one" line, the verbatim question, a reveal-on-click
answer, an Examiner's Comment / Author's Note, and its page number in the printed Question Bank book.
MCQs are not part of this page. The ten are **computed by a formula, not hand-picked**; hand overrides exist but
must carry a written reason.

## The chain, stage by stage

| # | Stage | Script / file | Output |
|---|---|---|---|
| 1 | Past-paper questions are extracted from the ICAI PDFs into sitting HTML, then `extract_questions.py` | `first_run/scripts/extract_questions.py` (full runbook: `first_run/HOW-TO-BUILD-THE-BOOK.md`) | `first_run/output/generated-from-script/questions_index.json` |
| 2 | Per-unit descriptive libraries (verbatim question + answer HTML, badges, Author's Note) | `books/ca-inter/smat-may-27-edition/practice-with-pranav-bhaiya/data/mcq-library/CA_Inter_AdvAcc_<unit>_<n>_Descriptive.json`. That folder's README calls it a copied snapshot of the Main1Lavya library (upstream). The exact copy step is not scripted in this repo. | one file per unit |
| 3 | 400-topic list with pages | `first_run/scripts/build_sheet_jsons.py` | `study_material_topics_flat.json`, `question_bank_descriptive_flat_through_may2026.json` |
| 4 | Each PYQ matched to ICAI Study Material questions (category A/B/C/D + similarity %). A lexical candidate list plus a manually reviewed `SAME_CONCEPT` table; **a candidate is not a verified match** | `first_run/scripts/build_pyq_study_matches.py` | `pyq_study_matches_through_may2026.json` |
| 5 | Topic ranking over the last ten PYQs (May 2023 → Sep 2026), Top 50 / Next 50 bands, question→topic mapping. September 2026 is hand-mapped in `SEP_MAP` because its official answers are not yet integrated | `first_run/scripts/build_descriptive_topic_priority.py` | `…/practice-with-pranav-bhaiya/data/descriptive_topic_priority.json` |
| 6 | **Choose the ten** (score → drop repeats → per-topic cap → Top-100 coverage → pad to ten). Reads the V1 book PDF to find each question's printed page | `capranav_com_revamped/tools/build_must_practice_data.py` | `public/practice-with-pranav-bhaiya/must-practice/data/index.json` and `<unit_id>.json` |
| 7 | Crawler-readable HTML copy of the lists (answers deliberately omitted) | `capranav_com_revamped/tools/build_seo_static.py` | edits `must-practice/index.html`, `topics/index.html`, `videos/index.html` |
| 8 | Deploy | `cd capranav_com_revamped && npx wrangler deploy` | live site |
| 9 | Verify in a real browser | `tools/verify_must_practice_live.py` | pass/fail |

Stages 1 to 5 normally do not need re-running to add a unit whose library file and topic mapping already exist
(AS 16 needed none). Re-run them only if the corpus, the topic ranking or a new sitting changes.

**Front end:** `public/assets/must-practice.js` (picker, table, expand row, "Show answer") with the shared
`public/assets/anatomy.css`. It fetches `…/must-practice/data/index.json` then `<unit_id>.json`. The data folder is
served through the Worker (`run_worker_first` in `wrangler.toml`) with bot protection.

## How the ten are chosen (summary)

Full reasoning, weights and every hand exclusion: `books/ca-inter/smat-may-27-edition/practice-with-pranav-bhaiya/MUST-PRACTICE-RULES.md`.
Score out of 1.0 = topic weight 40% + Study Material match 25% + source/recency 20% (MTP 1.0, RTP 0.95, PYQ 0.6) +
marks 15%. Then: drop repeats (text ≥ 90% alike, or ≥ 5 shared figures covering ≥ 60% of the smaller question),
at most two per topic, make sure every Top-100 topic of the chapter is covered, pad to ten. Weights live only in
`SCORING` in the build script; change them there and update the rules file in the same commit.

## Add a unit (the procedure that was used for AS 16)

1. Find the unit id (`M<module>-C<chapter>-U<unit>`) in `public/…/must-practice/data/index.json`, and its library
   file in `…/data/mcq-library/` (names end `_Descriptive.json`).
2. Add one entry to `UNITS` in `tools/build_must_practice_data.py`: `library_file`, `standard`, `unit_title`,
   `module`, `chapter`, `published: True`. No overrides to start with.
3. `python tools/build_must_practice_data.py`. Read the printed ranking and the "repeat dropped" lines.
   A question with no topic mapping is skipped silently and shown only as a lower "scored" count than the library size.
4. **Manual review (do not skip):** look for parts of one question reissued alone, and the same idea under
   different topic tags (the formula cannot see these). Add `force_exclude` entries with a written reason in
   `UNITS`, re-run, and add rows to the table at the bottom of `MUST-PRACTICE-RULES.md`.
5. `python tools/build_seo_static.py`, then `npx wrangler deploy`.
6. `python tools/verify_must_practice_live.py <unit_id>` must print `ALL PASSED`.
7. Add an entry to the top of `PROJECT-LOG.md`, update the published-unit lists in `AGENT-HANDOFF.md`,
   `PENDING.md` and `MUST-PRACTICE-RULES.md`, and append a note to `_claude/memory/project_log.md`.

## Gotchas

- **Do not test with curl/wget.** Data files return 403 to non-browsers by design (`BOT-PROTECTION.md`). Use the
  verify script (Playwright + Microsoft Edge: `pip install playwright`).
- **Answers are only visible after clicking a row, then "Show answer".** A test that clicks the button directly
  fails because the detail row is hidden.
- **Page numbers come from `first_run/output/final_deliverable/CA Inter Advanced Accounts_ The Complete Question Bank_V1.pdf`**
  (distributed and gitignored; never regenerate or overwrite it). Missing file = build fails; unmatched question =
  shows "not traced".
- **Running the build rewrites `generated_on` in every published unit's JSON**, so unchanged units show a one-line
  diff. Harmless.
- **`build_seo_static.py` also touches Topics and Videos pages** (a blank line). Harmless.
- **Edit generators, never the output** (`public/…/data/*.json`, the `ssr` blocks): the next run overwrites them.
- **Duplicate-chapter codes exist** in the syllabus (for example Cash Flow Statement is `M1-C4-U2` and `M3-C11-U2`);
  Must Practice uses the unit ids in the topic ranking. See `CLAUDE.md` §6 (2026-08-07).
- The repo has a background job that commits changes locally as "auto: N file(s) updated"; it does not push.
  Pushing is separate (see `CLAUDE.md` §2 "Pushing").
- **PYQs score lower than MTP/RTP on purpose** and can be absent from a list entirely (AS 16 has none).

## Related docs

`AGENT-HANDOFF.md` (site-wide handoff, task B3 = more units) · `PROJECT-LOG.md` (history) · `SEO.md` ·
`BOT-PROTECTION.md` · `ANATOMY.md` (the topic explorer, same data) ·
`books/ca-inter/smat-may-27-edition/practice-with-pranav-bhaiya/README.md` (data hub) and `MUST-PRACTICE-RULES.md` (formula).
