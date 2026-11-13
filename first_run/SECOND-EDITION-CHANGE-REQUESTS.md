# Question Bank Book — Second Edition change register

**Every defect, gap or improvement found in the Question Bank Book gets logged
here the moment it is found — before fixing anything, and whether or not it is
fixed now.** The first edition is printed and distributed; nothing in it can be
quietly corrected any more, so the record of what needs correcting is the thing
that has to survive.

The rule that keeps this file honest, and what counts as a change request, is in
`_claude/skills/SKILL-question-bank-change-log.md`. Read that before adding an
entry.

Scope: the book itself — `first_run/output/QUESTION-BANK-BOOK.html`, its chapter
books, and the distributed PDFs in `first_run/output/final_deliverable/`. Bugs in
the *pipeline* that never reached a reader belong in `HOW-TO-BUILD-THE-BOOK.md`
instead; a pipeline bug that did reach the printed page belongs in both.

## Status values

| Status | Meaning |
|---|---|
| `OPEN` | Logged, not yet addressed |
| `FIXED-IN-SOURCE` | Corrected in the pipeline/data, but the distributed PDF still carries the defect |
| `DONE-E2` | Present and correct in the second edition |
| `WONTFIX` | Deliberately not changing — with the reason written down |

## Severity

| Severity | Meaning |
|---|---|
| `S1` | Wrong content a student would learn incorrectly — a wrong figure, wrong answer, wrong standard |
| `S2` | Right content, wrong presentation — mis-tagged chapter, wrong page reference, broken table |
| `S3` | Missing feature or coverage gap the book itself acknowledges |
| `S4` | Cosmetic, print-cost, or editorial polish |

---

## CR-001 — OP / PP recurring-question tags not built

- **Severity** S3 · **Status** OPEN · **Logged** 2026-07-28 · **Source** Design decision
- **Where** Whole book; the front matter and `How-to-Read-this-Book.md` §7 both
  name this as "coming in a future edition".
- **What** Every recurring question should be marked as the Original (earliest
  sitting) or a later Practice repeat, so a student can see at a glance which
  problems ICAI keeps returning to.
- **Why deferred** The ≥90% text-similarity comparison is O(n²) over the whole
  corpus; running it against a partial corpus would mean redoing it. The full
  34-sitting corpus now exists, so the blocker is gone.
- **Design already written** `_claude/skills/SKILL-question-bank-duplicate-detection.md`
- **Second edition** Build it. This is the single largest promised-but-absent feature.

## CR-002 — Short chapter/unit names not drafted

- **Severity** S4 · **Status** OPEN · **Logged** 2026-07-28 · **Source** Design decision
- **Where** Every per-question topic tag; also acknowledged in `How-to-Read-this-Book.md` §7.
- **What** Some chapter titles are long enough to crowd the topic line (AS 5's
  full title is the usual example).
- **Blocked on** Pranav drafting the ~36 short names. `chapter_name_short` and
  `topic_name_abbvtd` already exist in the canonical topic-page-index for the
  coverage matrix — the second edition should extend that convention to the
  per-question tag rather than inventing a third field.

## CR-003 — Distributed V1 PDFs predate the Cash Flow chapter fix

- **Severity** S2 · **Status** FIXED-IN-SOURCE · **Logged** 2026-08-07
- **Where** `first_run/output/final_deliverable/CA Inter Advanced Accounts_ The
  Complete Question Bank_V1.pdf` and its `_protect` watermarked twin, both dated
  2026-07-28/30.
- **What** The Cash Flow Statement chapter carried `study_ref = "M1-C4-U2"`
  where every one of its 27 tagged questions uses `M3-C11-U2`. In the printed
  book this made the chapter's Study Material Reference banner, its ToC
  cross-reference **and** its row in the Chapter-wise Sitting Summary wrong — the
  coverage matrix showed **zero marks in every sitting** for Cash Flow Statement
  despite 27 real questions existing.
- **Fixed** in `qb_merge.py`'s `CHAPTERS` tuple on 2026-08-07; the rebuilt HTML is
  correct and the QA round-trip is clean at 455/455.
- **Still open for E2** The PDFs students actually hold were built before that
  fix and still carry it. Regenerating them is an explicit, separate decision —
  that folder is treated as distributed and never overwritten without asking.

## CR-004 — Legacy pre-syllabus-change topics excluded with no appendix

- **Severity** S3 · **Status** OPEN · **Logged** 2026-07-28 · **Source** Design decision
- **Where** Questions tagged `LEGACY-{TOPIC-SLUG}` across `PYQ_May2023.html`,
  `MTP_May2023_Set1.html`, `MTP_May2023_Set2.html`.
- **What** Several 2023 sittings test topics that no longer exist anywhere in the
  current 36-chapter taxonomy — Hire Purchase, Departmental Accounts, Incomplete
  Records, Insurance Claims for Loss of Stock, Redemption of Debentures and
  Preference Shares, Profit Prior to Incorporation, Bonus Shares, Managerial
  Remuneration. The sitting HTML records them accurately; the book excludes them
  because no current chapter exists to file them under.
- **Second edition** Decide whether an appendix is worth the pages. Students
  sitting the current syllabus will not be examined on these, so the honest
  default is to keep excluding them — but the decision should be recorded rather
  than inherited by silence.

## CR-005 — Descriptive answers were not independently re-derived

- **Severity** S1 (risk, not a confirmed defect) · **Status** OPEN · **Logged** 2026-07-26
- **Where** Every descriptive answer in the book.
- **What** MCQ arithmetic got a full independent re-derivation pass, which found
  and fixed 6 real errors across 67 rows. Descriptive answers deliberately got a
  lighter transcription-fidelity check only — Pranav's explicit relaxation for a
  first edition. The book says so plainly in its own accuracy disclaimer.
- **Second edition** Either run the full re-derivation on descriptive answers, or
  keep the disclaimer and say so again. What must not happen is dropping the
  disclaimer without doing the work.

## CR-006 — Reader-reported errors have no intake path into this register

- **Severity** S2 · **Status** OPEN · **Logged** 2026-09-24
- **Where** Every chapter's accuracy disclaimer prints
  `capranavpratiktulshyan@gmail.com` and promises the error "will be corrected in
  the next edition".
- **What** That promise is live in a distributed book, and until this file existed
  there was nothing behind it — a reported error had nowhere to land.
- **Second edition** Every reader email that reports a real defect becomes a CR
  here, with the reporter noted so they can be told it was fixed.

## CR-007 — Some questions are printed twice in the book

- **Severity** S4 · **Status** OPEN · **Logged** 2026-09-24 · **Source** Found while
  resolving Must Practice page numbers
- **What** A question tagged to two chapters is printed in full in both — its
  home chapter and the other chapter's Integrated section. Two AS 10 questions
  (`M2C5U2-015`, `-016`) matched two pages each for exactly this reason; the same
  will be true wherever an Integrated entry exists.
- **Assessment** This is by design and arguably right for a student working one
  chapter at a time. Logged because it costs printed pages and because a reader
  meeting the same question twice may think it is a mistake.
- **Second edition** Consider printing the Integrated occurrence as a
  cross-reference ("see page N") instead of the full question, and measure the
  page saving before deciding.

## CR-008 — PYQ November 2023 Q4 prints as "QNone"

- **Severity** S2 · **Status** OPEN · **Logged** 2026-10-18 · **Source** Found while
  building Must Practice units from the chapter-book library
- **What** The Financial Statements of Companies chapter (`M3C11U1-024`) prints its
  header as "PYQ November 2023 QNone Marks: 20". The question is PYQ November 2023
  Q4 (the Falgun Ltd. trial-balance-to-Schedule III question, 20 marks). Its record
  in `questions_index.json` (`CAI-P1-PYQ-2023-11-PII-Q4`) has `qno: null`, `parent_qno:
  null` and `subpart: null`, so the generator printed the Python `None`. The sitting
  HTML for that paper evidently lacks a question-number attribute on this one record.
- **Why it matters** Cosmetic for the student (the question and answer are intact),
  but the question cannot be cited by number, and anything that parses the header
  (the Must Practice build did) fails on it.
- **Second edition** Add the missing `data-qno` to the November 2023 sitting HTML,
  re-extract, and make the generator refuse to print a header whose number is
  `None`. The Must Practice build carries a documented `qno_overrides` entry for this
  question until then.

## CR-009 — Chapter order should follow Pranav's real teaching sequence

- **Severity** S3 · **Status** OPEN · **Logged** 2026-11-13 · **Source** Pranav's request
- **Where** Whole book: chapter order, the Table of Contents, the Chapter-wise Sitting Summary
  rows. The order is set by the `CHAPTERS` tuple in `first_run/scripts/qb_merge.py`, which follows file 1's
  `teaching_sequence`.
- **What** The book is ordered by an index sequence that is not the order Pranav teaches in class and
  recommends to students for reading and revision.
- **Second edition** Re-order by `books/ca-inter/concept-book/BOOK-SEQUENCE.csv` (Part A, B, C; 38 rows, 36
  units). Two units are taught in two parts (Intro to AS; Ch 11 Unit 1): **decide whether the Question
  Bank keeps one chapter at the first slot or the second, or splits** (open). Do not edit file 1's
  `teaching_sequence`: "Final Chapter" placement depends on it. Add the order as a separate input read by
  `qb_merge.py`, then rebuild the ToC and coverage matrix.

## CR-010 — Must Practice questions should be highlighted separately

- **Severity** S3 · **Status** OPEN · **Logged** 2026-11-13 · **Source** Pranav's request
- **Where** Every chapter book.
- **What** The ten Must Practice questions per unit (live on capranav.com) are not marked in the book,
  so a student cannot see which questions in a chapter are the priority ones.
- **Second edition** Mark those questions distinctly in each chapter (a badge or box, listed in the
  legend), and list them together at the start of the chapter. The join already exists: the Must
  Practice topic map (`books/ca-inter/smat-may-27-edition/practice-with-pranav-bhaiya/data/must_practice_topic_map.csv`)
  carries `book_id` and `human_id` per question. Study-Material-sourced Must Practice items are not in
  the book and need a separate pointer.

## CR-011 — Add MTP and RTP for September 2026 and January 2027

- **Severity** S3 · **Status** OPEN · **Logged** 2026-11-13 · **Source** Pranav's request
- **Where** Question corpus, every chapter book, coverage matrix, front matter statistics.
- **What** The book's latest MTP and RTP sittings are Sep 2025 / Jan 2026 (plus May 2026 where present).
  Sep 2026 and Jan 2027 MTP and RTP are to be added. **Not verified:** whether the Jan 2027 papers are
  published yet as of 2026-11-13; the sources are not in the repo.
- **Second edition** Source the PDFs (PDF only, never a converted copy: `SKILL-question-bank-verbatim-extraction.md`),
  build the sitting HTML, tag, extract, rebuild. Related, **ask Pranav**: PYQ September 2026 is not in the
  book either (the Must Practice build hand-maps it in `SEP_MAP` because its official answers are not
  integrated).

## CR-012 — Typos and trial balances are not rendered correctly

- **Severity** S2 · **Status** OPEN · **Logged** 2026-11-13 · **Source** Pranav's request
- **Where** Questions whose text contains a trial balance, and typos elsewhere. A count of
  `questions_index.json` (2026-11-13): **26** questions mention a trial balance (12 in
  `M3-C11-U1` Financial Statements of Companies, 8 in `M3-C15-U0` Branches, 4 elsewhere), of which
  **18** carry an HTML table in the question and **8 do not**, so their figures may have been flattened
  into running text (for example `CAI-P1-MTP-2026-01-S1-PII-Q5`, `CAI-P1-MTP-2026-01-S1-PII-Q6-c`,
  `CAI-P1-MTP-2024-09-S1-PII-Q6-c`). **This count is a lead, not a finding: no question has been compared
  against its source PDF yet.** The specific typos Pranav saw were not itemised.
- **Second edition** Audit every trial-balance question against its source PDF (debits and credits agree,
  columns aligned, no flattened figures), fix the sitting HTML, and re-extract. Pranav to list the typos
  he has seen; each gets its own entry or a line here. Related: CR-008.

## CR-013 — Repeated disclaimers in every chapter should be removed

- **Severity** S4 · **Status** OPEN · **Logged** 2026-11-13 · **Source** Pranav's request
- **Where** The opening notes of every chapter book: the "A note on accuracy" box, the "Scope of this book"
  box, and the "How this book is organised" box.
- **What** The same three notes are printed at the start of all 34 chapters (the scope note even lists every
  sitting each time), costing pages and diluting the one place they belong.
- **Second edition** Remove them from the chapter books (`generate_chapter_book.py`). Keep one accuracy
  note, one scope note and the how-to-read guide **once** in the front matter.

## CR-014 — Every page needs a header naming the chapter and the unit

- **Severity** S2 · **Status** OPEN · **Logged** 2026-11-13 · **Source** Pranav's request
- **Where** The distributed PDFs. Pranav reports the chapter/unit identification appears only on the first
  page of a chapter, not on the pages that follow.
- **What** The merged HTML does define a running header (`.qb-running-header`, `@top-center`, in
  `first_run/scripts/qb_common.py`) and one per chapter (36 in `QUESTION-BANK-BOOK.html`), so the intended
  design exists. **Why it does not reach every printed page is not yet determined.** It currently shows
  the book title and the chapter, not the unit.
- **Second edition** Find the cause on a real rendered PDF (not from the code: `CLAUDE.md` §7), fix it, and
  make the header show the chapter name and its unit ID on every page.

## CR-015 — Footer missing: "#Newton of Accounts, AIR-1-1-5, Pranav Bhaiya"

- **Severity** S4 · **Status** OPEN · **Logged** 2026-11-13 · **Source** Pranav's request
- **Where** The distributed PDFs. A running footer is defined in `qb_common.py` (`.qb-running-footer`,
  `@bottom-center`; 35 in the merged HTML) but, per Pranav, it is not present in the book.
- **Second edition** Every page carries the footer **#Newton of Accounts · AIR 1-1-5 · Pranav Bhaiya**
  (wording as Pranav gave it), plus the page number. Same root-cause check as CR-014; fix both together.

## CR-016 — OP / PP tags confirmed for the second edition

- **Severity** S3 · **Status** OPEN · **Logged** 2026-11-13 · **Source** Pranav's decision
- **What** Pranav confirmed OP / PP recurring-question tagging is to be done **in the second edition**.
  This is the decision CR-001 was waiting for; CR-001 stays as the design record. The earlier scope
  decision that kept OP/PP out of the first edition is unchanged.
- **Second edition** Build it as CR-001 describes (`SKILL-question-bank-duplicate-detection.md`), run once
  on the full corpus **after** CR-011 adds the new sittings, so it is not run twice.

## CR-017 — Question Bank topic numbers collide with the canonical topic numbers (marks land on the wrong topic)

- **Severity** S2 · **Status** OPEN · **Logged** 2026-11-13 · **Source** Pranav noticed the skewed marks in the
  topic table while the Concept Book unit for Internal Reconstruction was being built
- **Where** The "Topic-wise Marks Mapping" table at the start of each chapter book (seen in
  `InternalReconstruction_Question_Book.html`), and the Must Practice topic map
  (`must_practice_topic_map.csv`) that the website uses.
- **What** The Question Bank tags questions with its own older numbering (`topic-index.json`:
  `subtopicref` such as 1, 2, 2.1, 2.3/3, 3, 4). The canonical topic index (file 1) numbers the same chapter's topics
  differently. In Internal Reconstruction, **20 of the 25 records (143 marks)** carry the Question Bank tag "3",
  whose own title is "Full internal reconstruction scheme: capital reduction, preference conversion, loan-to-equity
  conversion, write-off of accumulated losses". File 1's topic 3 is **Alteration of Share Capital**. The topic table
  therefore prints those full-scheme questions under "3: Alteration of Share Capital", and Reduction of Share Capital,
  Compromise/Arrangements and Surrender of Shares (file 1 topics 5 to 7) show **zero marks**.
- **Cause (read in the code, not re-run)** `first_run/scripts/build_sheet_jsons.py` resolves a Question Bank
  `subtopicref` by matching it against file 1's `topic_no`, so equal numbers with different meanings collide
  (`CLAUDE.md` §6 already warns the two taxonomies must not be mixed).
- **Not checked** Whether the same collision affects other chapters (likely wherever the two numberings differ) and
  the website's topic-level importance tables.
- **Second edition** Map Question Bank tags to file 1's `unique_topic_id` by topic title and paragraph, not by number;
  re-run for all 36 chapters, check the topic tables, then rebuild the Must Practice map (Pranav deploys). Related:
  CR-010 (Must Practice highlighting) and the Concept Book's topic-level importance chips, which read the same map.

---

*Add new entries at the bottom, numbered in sequence. Never renumber or delete an
entry — a `WONTFIX` with its reasoning is more useful to the next reader than a
gap in the sequence.*
