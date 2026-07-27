# SKILL — Question Bank: Sitting-HTML Schema

> **What this is:** the exact, strict HTML structure every Question Bank sitting file
> (one MTP/RTP/PYQ paper) must follow. It exists so a human can visually review a file in
> a browser against the source PDF, and a Python script (BeautifulSoup) can mechanically
> extract a reliable JSON index from it — no ambiguity, no regex-guessing at structure.
>
> **Start here** if you are authoring or reviewing a sitting HTML file. Read
> `SKILL-question-bank-pipeline-overview.md` first if you don't yet know what a "sitting
> HTML file" is or where it fits. Read `SKILL-question-bank-topic-tagging.md` and
> `SKILL-question-bank-question-splitting.md` before filling in `.topics` or deciding
> whether a multi-part question needs splitting — this file tells you the *shape*, those
> two tell you the *content* that goes in that shape.
>
> **History:** this schema replaced an earlier version (`first_run/schema/HTML-SCHEMA.md`,
> 2026-07-23) after the very first real pilot output built against it turned out to have
> multiple structural defects invisible to a first read — missing case-scenario narratives,
> unparseable marks strings, an entire missing question. The live, generation-ready spec
> for prompting an external AI still lives at `first_run/schema/HTML-SCHEMA.md` and must be
> kept in sync with this skill; this file is the durable "why," that file is the
> current "exactly what to emit."

---

## 1. Styling — one source of truth, unchanged

Every sitting HTML file links to `../schema/book-style.css` (generated from
`first_run/schema/book-style.json` by `generate_style_css.py`) via
`<link rel="stylesheet" href="../schema/book-style.css">` in `<head>`. No inline
`<style>`, no hardcoded font-size/margin/colour anywhere in a sitting file. This part of
the schema has not changed and is not up for revision per-file — a styling change is one
JSON edit + one script re-run, never a per-file edit.

## 2. Document-level structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>MTP May 2026 Set 1 — Question &amp; Answer Record</title>
  <link rel="stylesheet" href="../schema/book-style.css">
</head>
<body data-course="CA-Inter" data-group="1" data-paper-code="P1"
      data-subject="advanced-accounting" data-paper-type="MTP"
      data-exam-month="05" data-exam-year="2026" data-set="1"
      data-session-key="2026-05" data-total-marks="100">

<h1>MTP May 2026 Set 1 — Advanced Accounting</h1>
<div class="qmeta">
  <strong>Source files read:</strong> CAInter-AdvAcc-MTP-May2026-Set1-Q.pdf,
  CAInter-AdvAcc-MTP-May2026-Set1-Ans.pdf
</div>
<div class="qmeta"><strong>Printed paper instructions:</strong>
  <!-- verbatim, including numbered instructions, "Part I is compulsory" etc. -->
</div>

<h2>Questions</h2>
<!-- .case-scenario nodes and .qblock nodes, see below -->

</body>
</html>
```

### 2a. Paper-level facets (§ new — replaces the free-text `"MTP May 2026 Set 1"` string)

Declared **once**, as `data-*` attributes on `<body>` — never repeated per-question, and
never parsed out of a display string by downstream code.

| Attribute | Values | Notes |
|---|---|---|
| `data-course` | `CA-Inter` | Fixed for this repo's scope. |
| `data-group` | `1` | Group I (Paper 1, Advanced Accounting). |
| `data-paper-code` | `P1` | |
| `data-subject` | `advanced-accounting` | |
| `data-paper-type` | `MTP` \| `RTP` \| `PYQ` \| `SM` \| `Other` | |
| `data-exam-month` | `01`–`12` | **Numeric, zero-padded.** Never `"May"` — a string month breaks chronological sorting. |
| `data-exam-year` | 4-digit year | |
| `data-set` | `1`, `2`, ... | **Omit the attribute entirely** if the paper has no set. Never `data-set=""` or `data-set="none"` — absence of the attribute *is* the null. |
| `data-session-key` | `YYYY-MM` | Derived from month+year; exists purely so range queries (`session_key >= "2025-05"`) work without parsing anything. |
| `data-total-marks` | integer | |

The human-readable label (`MTP May 2026 Set 1`) still appears in `<h1>` and in each
qblock's `.qmeta` display line — but it is **display text only**, never a join key, never
parsed by any script. All filtering/sorting code reads the `data-*` attributes above.

## 3. Case scenarios — mandatory, own node

**This is the defect that prompted this schema revision.** Case-scenario-based MCQs share
a narrative ("Suman Ltd. sold 5 ACs to Beach Resort for ₹45,000 each...") that the
questions themselves depend on but don't repeat. The first pilot run captured the
questions and silently dropped the shared narrative, leaving them unanswerable standalone.

```html
<div class="case-scenario" id="CS-1" data-case-no="1" data-part="I" data-question-count="4">
  <div class="case-facts">
    <p>...the full shared narrative, verbatim, exactly as printed in the source paper,
       reformatted into paragraphs/tables as needed but never summarised...</p>
  </div>
</div>
```

Every MCQ that depends on a case scenario carries `data-case-ref="CS-1"` (see §4). A
standalone MCQ (not tied to any case) simply omits `data-case-ref`.

**Non-negotiable checks, every sitting, every time:**
- Every `data-case-ref` on a qblock must resolve to a `.case-scenario` with a matching
  `id` in the same file.
- Every `.case-scenario`'s `data-question-count` must equal the number of qblocks that
  actually reference it.
- **Audit for this specifically** when reviewing any newly-generated sitting file — it is
  the single easiest thing for an AI extracting from a messy OCR'd PDF to drop, because
  the narrative reads like scene-setting rather than "the answer," and nothing about a
  quick read of just the questions makes its absence obvious.

## 4. MCQ qblocks (Part I, case-scenario or standalone)

```html
<div class="qblock" id="CAI-P1-MTP-2026-05-S1-PI-Q1"
     data-part="I" data-case-ref="CS-1" data-qno="1" data-marks="2"
     data-qtype="case-mcq" data-answer="B"
     data-final-chapter="M2-C8-U2"
     data-confidence="high" data-review-status="verified">

  <div class="qmeta">
    <span class="src">MTP May 2026 Set 1</span> &middot;
    <span class="part">Part I &ndash; Case Scenario I</span> &middot;
    <span class="qno">Q1</span> &middot;
    <span class="marks">Marks: 2</span>
  </div>

  <div class="question">
    <p class="stem">How much revenue should be recognised by the Company as on
       March 31, 2024?</p>
    <ol class="options" type="A">
      <li data-opt="A">&#8377;2,25,000</li>
      <li data-opt="B">&#8377;2,17,500</li>
      <li data-opt="C">&#8377;2,00,000</li>
      <li data-opt="D">&#8377;2,30,000</li>
    </ol>
  </div>

  <div class="answer-block" data-answer="B">
    <p><strong>Answer:</strong> (B)</p>
  </div>

  <div class="topics">
    <span class="topic-tag" data-unitcode="M2-C8-U2" data-subtopicref="2.8"
          data-standard="AS 9" data-title="Revenue Recognition"
          data-topic-rank="primary">AS 9 &mdash; Revenue Recognition (2.8)</span>
  </div>

  <div class="examiner-comment synthesized" data-comment-source="synthesized"
       data-source="Synthesized per examiner-comments-writing-skill.md — not ICAI-sourced">
    ...
  </div>

  <div class="author-comment" data-author="Pranav" data-status="empty"></div>

  <div class="extraction-note">...</div>
</div>
```

Key differences from the pre-revision schema:
- **`data-marks` is always a plain integer.** No `"2 Marks"`, no arithmetic embedded in the
  string.
- **`data-answer` on the qblock, mirrored on `.answer-block`.** The `<p>Answer: (B)</p>`
  text is display only; `data-answer` is the join key, and it must match one of the child
  `<li data-opt>` values — this is a build-time assertion, not optional.
- **Options are structured** (`<ol class="options"><li data-opt="A">...`), not
  `<br>`-separated text. This is what makes quiz-mode / option-level analytics possible
  later without a fragile regex parse of free text.
- **`data-final-chapter`** — see `SKILL-question-bank-topic-tagging.md` §3. For a
  single-topic MCQ this is trivially that topic's `unitCode`.
- **`data-confidence` / `data-review-status`** — see §7 below.

## 5. Descriptive qblocks (Part II) — independent sub-parts are separate records

**Read `SKILL-question-bank-question-splitting.md` before authoring any multi-part
descriptive question.** The short version: classify each sub-part as *independent*
(different company, different facts, just bundled under one question number) or
*connected* (one continuous fact pattern). Independent sub-parts become **separate
qblocks**, each with its own ID, marks, topic tag, and answer. Connected sub-parts stay
one qblock.

`data-qtype` enum: `mcq` (standalone MCQ), `case-mcq` (MCQ tied to a `.case-scenario`),
`practical` (numerical/computation question), `theory` (descriptive discussion question,
no computation). The `theory`/`practical` split already exists on every descriptive qblock
across all 5 pilot sittings — **open issue (2026-07-25):** it isn't yet surfaced downstream
(not in `questions_index.json`'s display fields, not in the rendered chapter book's
`qmeta` line), and the existing tags haven't had a dedicated review pass against the
verbose/numeric heuristic Pranav proposed. See
`SKILL-question-bank-chapter-book-rendering.md` §3.4.

**Independent sub-part example** (a 14-mark question whose (a)/(b)/(c) are three
unrelated companies/scenarios):

```html
<div class="qblock" id="CAI-P1-MTP-2026-05-S1-PII-Q1-a"
     data-parent-qno="1" data-subpart="a" data-part="II" data-marks="5"
     data-compulsory="true" data-qtype="practical"
     data-final-chapter="M2-C5-U4"
     data-confidence="high" data-review-status="verified">

  <div class="qmeta">
    <span class="src">MTP May 2026 Set 1</span> &middot;
    <span class="part">Part II</span> &middot;
    <span class="qno">Q1(a)</span> &middot;
    <span class="marks">Marks: 5</span> &middot;
    <span class="compulsory">Compulsory</span>
  </div>

  <div class="question"><!-- verbatim, this sub-part only --></div>
  <div class="answer-block"><!-- verbatim, this sub-part only --></div>

  <div class="topics">
    <span class="topic-tag" data-unitcode="M2-C5-U4" data-subtopicref="4.4/4.6/4.7"
          data-standard="AS 16" data-title="Borrowing Costs"
          data-topic-rank="primary">AS 16 &mdash; Borrowing Costs</span>
  </div>

  <div class="examiner-comment synthesized" data-comment-source="synthesized" ...>...</div>
  <div class="author-comment" data-author="Pranav" data-status="empty"></div>
  <div class="extraction-note">...</div>
</div>
```

`data-parent-qno="1"` + `data-subpart="a"` reconstruct "this was Q1(a) as printed on the
paper" — useful for anyone who wants to see the exam in its original shape, without that
shape governing how the Question Bank actually organises the content.

**Connected multi-topic question** (rare; stays one qblock) carries multiple
`<span class="topic-tag">` entries, each with its own `data-marks` share (so
marks-by-topic arithmetic still works without physically fragmenting the verbatim
content), and `data-final-chapter` is computed from whichever topic has the latest
`teaching_sequence` (see the tagging skill).

**OR-alternatives** (a question offering "(a) theory OR (a) numerical problem") — each
alternative is its own record, tagged with a shared `data-alt-group` and a distinguishing
`data-alt="1"|"2"`. Both alternatives are legitimate, separately useful Question Bank
content (a student might want to practice either), but a marks-total validator must not
sum both toward the paper's total — only one was ever actually answerable.

## 6. Tables

- Always use `<thead>`/`<tbody>`, even for simple two-column ledgers. Consistency here is
  what lets a future table-to-data extraction script work without per-table special
  cases.
- **Never put a `→`/`&rarr;` inside a table cell** to show a before/after value (e.g. a
  revaluation adjustment). Split into separate columns instead — an arrow inside a cell
  defeats numeric parsing downstream.
- Reproduce the source table's structure faithfully; do not collapse multi-row workings
  into a single summarised row.

## 7. Review-flag attributes — structured, not just prose

Every qblock carries:

```html
data-confidence="high|medium|low"
data-review-status="verified|needs-visual-check|flagged|unreviewed"
data-issue="source-inconsistency,ocr-garbled"   <!-- comma-separated; omit if none -->
```

`data-issue` vocabulary: `source-inconsistency` (the source PDF's own answer key
contradicts itself), `ocr-garbled` (extraction produced unreliable characters/layout),
`table-reconstructed` (a table's structure was rebuilt from misaligned OCR text and
should get a visual spot-check), `missing-case-narrative`, `topic-unindexed` (tagged
against a syllabus unit not yet detailed in `topic-index.json`), `marks-mismatch`,
`answer-key-letter-only` (the source MCQ answer key gives only the option letter, so the
qblock's explanation is AI-authored rather than transcribed — see
`SKILL-question-bank-verbatim-extraction.md` §6 for why this needs its own arithmetic
re-verification, found necessary after two such explanations turned out to have the
underlying rule backward while still citing the right final letter).

Keep the prose `.extraction-note` too — it's what a human reads. The attributes are what
a script queries ("show me every question awaiting a visual check across all 50 papers"
becomes one query instead of a manual read of 50 files).

## 8. Author comment

```html
<div class="author-comment" data-author="Pranav" data-status="empty"></div>
```

Always present, always empty at extraction time, always hidden by default
(`.author-comment { display: none }` in `book-style.css`). `data-status="empty"` lets an
editorial dashboard later show which questions still await Pranav's own annotation,
without needing to parse "is this div empty."

## 9. Character/entity normalisation

Use `&#8377;` for ₹, consistently, everywhere. The source PDFs' OCR extraction sometimes
renders the rupee sign as a stray backtick (`` ` ``) — **never carry that artifact into
the HTML.** Normalise on sight. Reject any stray backtick in `.question` or
`.answer-block` content as a lint error, not a style nit — it is a transcription defect.

## 10. Deterministic composite IDs

```
CAI-P1-MTP-2026-05-S1-PII-Q1-a
│   │  │   │    │  │  │  └── sub-part letter (omit if the question wasn't split)
│   │  │   │    │  │  └───── part + question number
│   │  │   │    │  └──────── set (omit this whole segment if the paper has no set)
│   │  │   │    └─────────── exam month
│   │  │   └──────────────── exam year
│   │  └──────────────────── paper type
│   └─────────────────────── paper code
└─────────────────────────── course
```

IDs are **derivable from the paper-level facets + the question's own numbering** — never
hand-invented, never stored independently of the facts they're built from. This is what
keeps IDs globally unique the moment 50 papers get merged into one corpus, and lets a
script regenerate an ID rather than a human maintaining a lookup table.

## 11. Golden reference

`first_run/output/parsed-from-pdf/MTP_May2026_Set1.html` is the first file rebuilt against
this revised schema (2026-07-24) — use it as the concrete worked example alongside this
document. All sitting HTML files live in `parsed-from-pdf/`, never at the top level of
`first_run/output/` (that subfolder split was introduced 2026-07-26 to keep Layer 1 source
files visually separated from Layer 2/3 script output).
