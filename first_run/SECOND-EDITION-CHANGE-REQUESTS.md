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

---

*Add new entries at the bottom, numbered in sequence. Never renumber or delete an
entry — a `WONTFIX` with its reasoning is more useful to the next reader than a
gap in the sequence.*
