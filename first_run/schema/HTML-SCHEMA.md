# Sitting-level HTML schema — first_run pilot

Written 2026-07-23, **revised 2026-07-24** after the first real pilot file
(`MTP_May2026_Set1.html`) was reviewed against its source PDF and found to violate this
schema in several ways invisible on a casual read (missing case-scenario narratives,
placeholder text presented as verbatim, an entire missing question, unparseable marks
strings, zero topic tagging). This is the exact, strict structure every sitting HTML file
in `first_run/output/` must follow. It exists so that (a) a human can visually review the
file in a browser against the source PDF, and (b) a later Python script (BeautifulSoup)
can mechanically extract a flexible JSON from it — no ambiguity, no guessing at structure.

**For the reasoning behind every rule below, see the `_claude/skills/SKILL-question-bank-*.md`
files** — this document is the terse "exactly what to emit" spec; those are the durable
"why," including worked examples and the failure modes each rule exists to prevent.

**Styling comes from exactly one place**: every sitting HTML file links to
`../schema/book-style.css` (generated from `book-style.json` by
`generate_style_css.py`) via `<link rel="stylesheet" href="../schema/book-style.css">`
in its `<head>`. **No inline `<style>` block, no hardcoded font-size/margin/colour
anywhere in a sitting HTML file.** Every visual property must come from a CSS
class already defined in `book-style.css` (`.qblock`, `.qmeta`, `.answer-block`,
etc.) or a CSS custom property (`var(--body-font-size)` etc.) — never a literal
value written directly into the sitting HTML.

## Document-level structure (once per file)

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
  <!-- verbatim any "Part I is compulsory..." style instructions printed on the paper,
       including the numbered general instructions and both Part I / Part II notes -->
</div>

<h2>Questions</h2>

<!-- .case-scenario nodes and .qblock nodes, see below -->

</body>
</html>
```

### Paper-level facets (on `<body>`, once per file — never repeated per question)

| Attribute | Values | Notes |
|---|---|---|
| `data-course` | `CA-Inter` | |
| `data-group` | `1` | |
| `data-paper-code` | `P1` | |
| `data-subject` | `advanced-accounting` | |
| `data-paper-type` | `MTP` \| `RTP` \| `PYQ` \| `SM` \| `Other` | |
| `data-exam-month` | `01`–`12` | Numeric, zero-padded. Never `"May"`. |
| `data-exam-year` | 4-digit year | |
| `data-set` | `1`, `2`, ... | **Omit entirely** if the paper has no set. Never `data-set=""`. |
| `data-session-key` | `YYYY-MM` | Derived from month+year. |
| `data-total-marks` | integer | |

The display string (`MTP May 2026 Set 1` in `<h1>` and each qblock's `.qmeta`) is
**display text only** — never parsed by any script.

## Case scenarios — mandatory, own node (§ new)

Case-scenario MCQs share a narrative that the questions depend on. It must be its own
node, never dropped:

```html
<div class="case-scenario" id="CS-1" data-case-no="1" data-part="I" data-question-count="4">
  <div class="case-facts">
    <p>...the full shared narrative as printed in the source paper, verbatim...</p>
  </div>
</div>
```

Every dependent question carries `data-case-ref="CS-1"`. Standalone MCQs omit it.
**Checks:** every `data-case-ref` must resolve to a `.case-scenario` in the same file;
every `.case-scenario`'s `data-question-count` must match the number of questions
referencing it.

## MCQ qblock structure (Part I)

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
    <!-- ICAI-voice synthesized comment, or real comment for PYQ Jan 2026 with
         data-comment-source="icai" and the matching data-source citation -->
  </div>

  <div class="author-comment" data-author="Pranav" data-status="empty"></div>

  <div class="extraction-note">...</div>
</div>
```

`data-marks` is **always a plain integer** — never `"2 Marks"` or an arithmetic string.
`data-answer` must match one of the child `data-opt` values (build-time check). Options
are structured (`<ol class="options"><li data-opt="A">`), never `<br>`-separated text.

## Descriptive qblocks (Part II) — independent sub-parts are separate records (§ new)

**Before authoring a multi-part question, classify it**: do the sub-parts share one
continuous fact pattern (**connected**), or are they unrelated problems bundled under one
question number for paper-length convenience (**independent**)? See
`_claude/skills/SKILL-question-bank-question-splitting.md` for the full rule and edge
cases. Independent is the common case for this exam's descriptive questions — check each
sub-part's actual facts before assuming otherwise.

**Independent** → each sub-part becomes its own qblock:

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

**Connected** → stays one qblock, multiple `.topic-tag` spans each carrying its own
`data-marks` share (summing to the qblock's total) and a `data-topic-rank`;
`data-final-chapter` = the tagged topic with the latest `teaching_sequence`
(`_claude/skills/SKILL-question-bank-topic-tagging.md` §4).

**OR-alternatives** ("(a) theory OR (a) numerical problem") → each alternative is its own
independent record (per above), sharing `data-alt-group` with a distinguishing
`data-alt="1"`/`"2"`. Do not sum both toward the parent question's marks — only one was
ever answerable.

## Rules, non-negotiable

1. **Every visual property comes from `book-style.css`** — no inline styles, no
   hardcoded font-size/colour/margin.
2. **Question and answer content is verbatim** — every number, every rupee sign
   (`&#8377;`, never a stray backtick), every table cell, exactly as printed in the
   source. Reformatting messy OCR text into clean HTML is expected and required;
   changing what it *says*, or substituting a description of the content for the content
   itself, is never allowed — see
   `_claude/skills/SKILL-question-bank-verbatim-extraction.md` for exactly what went
   wrong the first time this was tried.
3. **`data-marks` is always a plain integer**, at every level. No `"14 (7+7)"`. The
   breakdown lives in separate sub-part records (independent) or per-topic-tag marks
   shares (connected).
4. **Every multi-part question is explicitly classified independent/connected before
   authoring** — see the splitting skill.
5. **Every question/fragment carries `data-final-chapter`** — the chapter it physically
   lives under in the assembled Question Bank Book. Trivial (= its own topic) for
   single-topic questions/fragments; computed from `teaching_sequence` for connected
   multi-topic questions.
6. **`.examiner-comment`'s `data-comment-source` (enum) and `data-source` (citation) are
   both mandatory and must be accurate** — real ICAI comment (PYQ sittings only, and only
   where confidently matched) vs. synthesized. Never omit, never guess. Voice stays
   ICAI-authentic even when synthesized — see
   `_claude/skills/SKILL-question-bank-examiner-comments.md` §3 for why this was decided
   and should not be silently revisited.
7. **`.author-comment` is always present, always empty, always hidden**, with
   `data-status="empty"`.
8. **Flag uncertainty explicitly** via `data-confidence`, `data-review-status`,
   `data-issue` (comma-separated; vocabulary in
   `_claude/skills/SKILL-question-bank-html-schema.md` §7) plus a prose
   `.extraction-note` — never silently guess and present something as confident when it
   isn't.
9. **Tables use `<thead>`/`<tbody>`**; never put a `→` inside a cell for a before/after
   value — split into separate columns.
10. **IDs are deterministic and derivable** from the paper-level facets + question
    numbering (`CAI-P1-MTP-2026-05-S1-PII-Q1-a`) — never hand-invented.
11. **Write an actual `.html` file to disk** at the path given in the task, inside
    `first_run/output/` — do not just display the HTML in a chat response.

## Reference

See `books/question-bank/metadata-index/AS10_Question_Book.html` for the tone/quality
bar this is drawing from, and `first_run/output/MTP_May2026_Set1.html` for the current
concrete worked example of this schema applied to a real sitting.
