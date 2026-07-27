# Question Bank — chapter/topic tagging schema

Written 2026-07-22. Answers one question: when a new PYQ/MTP/RTP sitting gets tagged
(as `metadata-index/{PaperType}_{Session}[_SetN].json`), which taxonomy and field
names should it use?

## Three taxonomy sources in this repo — which one wins (revised 2026-07-23)

1. **`books/concept-book/syllabus-engine/data/0-ca-inter-adv-accounts-subtopics-marks-weightage.json`**
   — the master syllabus index. All 36 chapters, 436 topics, marked "locked, never
   edit." Uses `unique_chapter_id` = `M{module}-C{chapter}-U{unit}` and
   `unique_topic_id` = `{unique_chapter_id}-T{topic_no}`. Also carries
   `teaching_sequence` and `marks_by_attempt` (back to May-2018) per chapter — not
   duplicated elsewhere.
2. **`books/concept-book/syllabus-engine/data/1-ca-inter-adv-accounts-topic-page-index.json`**
   (new, 2026-07-23) — **the canonical topic-number + page-number authority**,
   converted from Pranav's `CA INTER ADV ACCOUNTS - For Adarsh.csv` (400 topics, all
   36 chapters — including AS 1 and AS 27, which nothing else in this repo had).
   Cross-joined against file 0 by `unique_chapter_id` (100% match, zero unmatched
   either direction) to also carry `teaching_sequence`, `chapter_name_short`, and
   `marks_distinct_attempt_count`; adds `standard`/`standard_title` (parsed from the
   unit name) and `is_single_unit_chapter`. **This is the file to read for exact
   topic numbering/naming and real page numbers** — more complete and better
   validated than `topic-index.json`'s hand-built entries (which still only cover
   32/36 chapters and mark 10 of those as page-number stubs).
3. **`topic-index.json`** (this folder) — the index actually being used to tag
   questions today (see `MTP_Jan2025.json`). Uses `unitCode` = same
   `M{module}-C{chapter}-U{unit}` shape, plus `sections[].ref` = raw ICAI paragraph
   numbers (e.g. `"5.6-5.8"`, no `T` prefix) and prose `description`s for the
   chapters it's gotten to.

**Decision: keep tagging questions with `unitCode` + `subtopicRef` (`topic-index.json`'s
shape)** — its `sections[].ref` values map directly onto the actual ICAI paragraph
numbers students see in the study material, more legible for a question bank than
`unique_topic_id`. But **pull the `unitCode` itself, the topic numbering, and page
numbers from file 1 (canonical) going forward** — `topic-index.json`'s own
per-chapter entries should be treated as supplementary prose description, not the
numbering authority anymore.

## The U0/U1 decision — reversed 2026-07-23

Originally this doc said use `U1` for the 7 single-unit chapters, to match
`topic-index.json` + the raw ICAI filenames. **Reversed: use `U0`** — Pranav's
reasoning: `U0` correctly signals "this chapter has no further units," and it's now
backed by *two* independent sources (file 0 and file 1) against one.

**Migrated 2026-07-23 — `U0` is now used everywhere, no stale `U1` references remain.**
`topic-index.json` (7 `unitCode` fields + their `"unit": 1`→`0` companions) and all 4
already-tagged sitting JSONs (`MTP_Jan2025.json`, `MTP_May2024_Set1.json`,
`PYQ_Jan2026.json`, `RTP_May2026.json` — 10+7+5+6 = 28 `unitCode` occurrences) were
migrated in one pass and re-validated as parseable JSON afterward. The `sourceFile`
fields in `topic-index.json` (e.g. `"M1_C1_U1_ Introduction....pdf"`) were deliberately
**left untouched** — those are real filenames on disk under
`books/concept-book/raw_icai_study_materials/`, which genuinely use `U1` in their
names; that's a filename fact, not our tagging convention, and isn't part of this
migration.

| Chapter | `unique_chapter_id` (canonical, everywhere now) |
|---|---|
| Introduction to Accounting Standards | `M1-C1-U0` |
| Framework for Preparation & Presentation of FS | `M1-C2-U0` |
| Applicability of Accounting Standards | `M1-C3-U0` |
| Buyback of Securities | `M3-C12-U0` |
| Amalgamation of Companies | `M3-C13-U0` |
| Internal Reconstruction | `M3-C14-U0` |
| Accounting for Branches incl. Foreign Branches | `M3-C15-U0` |

All other chapters already agree across all three files (e.g. `M2-C5-U1` = AS 2
everywhere) — no translation needed there.

## Per-question tagging JSON schema — LEAN INDEX (revised 2026-07-22)

`MTP_Jan2025.json` (the pilot) embeds full `questionHtml`/`answerHtml` per question.
That's fine for a one-off proof of format, but doubles storage and requires
hand-retranscribing content that already lives, cleanly, in
`Parsed_PDF_Question_Bank_CA_Inter_Accounts/`. **Going forward, tagging files are a
lean index only** — they point at the parsed `.md` file's question, they don't copy
its content. `MTP_Jan2025.json` is left as-is (not worth reprocessing); everything
tagged from here on uses this leaner shape.

One file per sitting: `metadata-index/{MTP|PYQ|RTP}_{Session}[_SetN].json`
(e.g. `MTP_May2024_Set1.json`).

```
{
  "_readme": "<one line: source, method, any caveats>",
  "examSession": "<e.g. May 2024>",
  "paperType": "Mock Test Paper (MTP)" | "Past Year Question (PYQ)" | "Revision Test Paper (RTP)",
  "course": "CA Intermediate - Group I - Paper 1",
  "subject": "Advanced Accounting",
  "sourceParsedFile": "../Parsed_PDF_Question_Bank_CA_Inter_Accounts/parsed-....md",
  "totalMarks": <int>,
  "questions": [
    {
      "id": "<PaperType-Session[-SetN]-Part-QN>",
      "mdAnchor": "<the '### Question N' heading text in sourceParsedFile, so the question can be located there>",
      "part": "<section/part label as printed, e.g. 'Part I - Case Scenario MCQs' or 'Part II - Descriptive'>",
      "questionNumber": "<as printed>",
      "marks": <int>,
      "marksNote": "<optional breakdown, e.g. '(a) 4 + (b) 5 + (c) 5'>",
      "topics": [
        {"unitCode": "M{m}-C{c}-U{u}", "standard": "AS n" | null, "title": "<chapter title>",
         "subtopicRef": "<topic-index.json sections[].ref value(s)>",
         "subtopicTitle": "<short description of what's actually being tested>"}
      ],
      "commonMistakes": {
        "text": "<the mistake note itself, in ICAI Examiner's-Comments voice>",
        "source": "ICAI Examiner's Comment — {Session}, verbatim" | "ICAI Examiner's Comment — {Session}, paraphrased" | "Synthesized per examiner-comments-writing-skill.md — not ICAI-sourced"
      },
      "recurringGroup": {
        "groupId": "<short slug for the fact pattern, e.g. 'mars', 'greenltd', 'blackltd' — lowercase, no spaces>",
        "role": "OP" | "PP",
        "note": "<optional: what varies between occurrences, if anything — company name only, or numbers too>"
      }
    }
  ]
}
```

Rules:
- Multi-topic questions (a question with parts testing different chapters) get
  multiple entries in `topics[]`, one per distinct chapter/sub-part tested.
- If a question tests a chapter not yet in `topic-index.json`, add a stub entry
  there first (module/chapter/unit/standard/title/sourceFile, sections list can be
  a plain heading list marked `"_note": "stub - headings only, not yet described"`
  if there's no time to write full descriptions) — don't invent a `unitCode`/`ref`
  that isn't backed by the reference index.
- Flag (in `subtopicTitle`) any tag that required inference beyond verbatim
  standard text (see the existing bonus-share example in `MTP_Jan2025.json` Q2).
- Content (question/answer text) stays exclusively in `Parsed_PDF_.../*.md` — never
  duplicate it into the tagging JSON. `mdAnchor` is the join key.
- `commonMistakes` is omitted entirely (not left as an empty stub) until it's
  actually been written — don't invent placeholder mistake text.
- `recurringGroup` is likewise omitted unless a question has actually been
  compared against others and matched — don't pre-emptively tag every question
  as a singleton group.

## `commonMistakes` — provenance rule (added 2026-07-22)

Real ICAI "Examiners' Comments on the Performance of the Examinees" documents
exist for exactly 6 PYQ sittings so far — Jan 2025, May 2024, Sep 2024, May
2025, Sep 2025, Jan 2026 — sourced PDFs converted and sliced to their Paper 1
section at
`Raw_PDF_Question_Bank_CA_Inter_Accounts/examiner-comments-paper1/Paper1-ExaminerComments-{Session}.md`.
MTP and RTP sittings never get real examiner comments (they aren't real exams),
and PYQ sittings outside those 6 don't have a sourced comments document yet.

**Rule: use the real ICAI comment wherever one exists and can be confidently
matched to the question; everywhere else, write one using the style guide at
`examiner-comments-writing-skill.md`, and mark it as synthesized.** Never
present a synthesized mistake note without that `source` tag making it
obvious it isn't ICAI's own words — this is the same non-negotiable discipline
`AS10_Question_Book.html` already applies to reconstructed answer workings.

## `recurringGroup` — OP/PP duplicate-detection rule (added 2026-07-22)

Per Pranav: compare question text pairwise **with numbers stripped out**; if
similarity is **≥90%**, the questions belong to the same `groupId`. Within a
group, the occurrence from the **chronologically earliest sitting** (by actual
exam date, not filename) is the **OP** ("Original Concept-testing Question");
every later occurrence is a **PP** ("For Practice Question"). Every occurrence
in a group is still shown in full in the eventual chapter book — grouping is
for cross-referencing and confidence (identical answer keys across occurrences
raise confidence in the answer), not for de-duplication/collapsing.

Watch for the two edge cases the exact-90%-on-text rule can miss: (a) same
numbers, renamed company (should still match — the number-bearing content is
identical); (b) same company, different numbers, same trap (may need judgment
beyond the mechanical rule). Flag borderline cases rather than deciding
silently.
