# 3 prompts: generate sitting-level HTML for the first_run pilot

Written 2026-07-23, **revised 2026-07-24** after the first real run (MTP May 2026 Set 1)
was reviewed against its source PDF and found to violate the schema in several ways an
earlier draft of this prompt didn't guard against clearly enough: a missing case-scenario
narrative, placeholder text presented as verbatim answer content, an entire missing
question, and unparseable marks strings. This revision adds explicit instructions for all
of those, plus the new independent-question-splitting and topic-tagging rules Pranav
locked in afterward. **If you already ran the pre-revision version of this prompt for any
sitting, that output needs to be re-reviewed against this revised schema, not assumed
still correct.**

Three separate, self-contained prompts — one per paper type (MTP, RTP, PYQ) — each
reusable across sittings of that type by only changing the filenames named inside it. Give
each prompt, as a whole, to an external AI model that has read access to this repo.
**This is the only time these source PDFs will ever be read — the HTML this produces
becomes the permanent primary record.** Get it complete and correct now.

All three target the schema at `first_run/schema/HTML-SCHEMA.md` — read that file in full
for the exact per-question HTML structure. They also point at six `_claude/skills/
SKILL-question-bank-*.md` files — read every one of them; they carry the reasoning and
worked examples behind the rules, and several of the rules below only make sense with that
context.

---

## Prompt 1 of 3 — MTP (Mock Test Paper)

```
You are converting one CA Inter Advanced Accounting Mock Test Paper (MTP) sitting into a
single, self-contained, permanent HTML record. This is the ONLY time this source will ever
be read - the HTML you write becomes the primary record from now on, not the source files.
Get every number, every table, every tag correct. A prior run of this same task on a
different sitting produced a file with placeholder text standing in for real answers, zero
topic tagging, and one entire question silently missing - read the rules below carefully
enough to not repeat any of that.

READ THESE TWO SOURCE FILES - THE PDFs, NOT ANY .MD CONVERSION OF THEM (in
books/question-bank/Raw_PDF_Question_Bank_CA_Inter_Accounts/):
- CAInter-AdvAcc-MTP-May2026-Set1-Q.pdf   (the questions)
- CAInter-AdvAcc-MTP-May2026-Set1-Ans.pdf (the official answers - this file does NOT
  repeat the questions, you need BOTH files, always)
A .md conversion of these may also exist in first_run/source/ - do not use it. It is a
lossy intermediate extraction with table structure and OCR artifacts baked in; verifying
against it only confirms your output matches another lossy copy, not the real source.

WRITE YOUR OUTPUT TO EXACTLY THIS PATH (create the file, do not just display HTML in your
response):
first_run/output/MTP_May2026_Set1.html

BEFORE YOU START, READ THESE FILES IN FULL (all in this repo):
1. `_claude/skills/SKILL-question-bank-html-schema.md` and
   `first_run/schema/HTML-SCHEMA.md` - the exact HTML structure you must produce, document-
   level and per-question, including paper-level facets on `<body>`, mandatory
   `.case-scenario` nodes, structured MCQ options, and deterministic IDs. Follow it exactly
   - a script will later parse your output mechanically by these class names and data
   attributes, so deviation breaks everything downstream.
2. `_claude/skills/SKILL-question-bank-question-splitting.md` - before writing any multi-
   part descriptive question, classify whether its sub-parts are INDEPENDENT (different
   companies/facts, just bundled under one question number) or CONNECTED (one continuous
   fact pattern). Independent sub-parts each become their OWN separate qblock record with
   their own ID, marks, and topic tag - do not bundle three unrelated 5/5/4-mark problems
   into one 14-mark qblock with three topic tags. This is the common case for MTP
   descriptive questions - check each sub-part's actual facts, don't assume.
3. `_claude/skills/SKILL-question-bank-topic-tagging.md` - which taxonomy file is the join-
   key source of truth (`topic-index.json`'s `unitCode`+`sections[].ref`, never a new ID
   scheme), and how to compute `data-final-chapter` (the chapter this question/fragment
   physically lives under in the assembled Question Bank Book - trivial for single-topic
   questions/fragments, computed from `teaching_sequence` for the rare connected multi-
   topic case).
4. `_claude/skills/SKILL-question-bank-verbatim-extraction.md` - read this one especially
   carefully. It documents exactly what went wrong the first time this pipeline ran:
   placeholder text presented as verbatim content, a missing question caught only by
   counting against the paper's own stated structure, and mark totals that were
   individually wrong but happened to cancel out in the grand total. Do the same checks it
   describes before you finish.
5. `first_run/schema/book-style.css` - every visual property already has a CSS
   class/variable defined for it. You must NEVER write an inline style or hardcode a
   font-size/colour/margin - reference the existing classes and let the linked stylesheet
   handle appearance. Link to it as `<link rel="stylesheet" href="../schema/book-style.css">`.
6. `books/concept-book/syllabus-engine/data/1-ca-inter-adv-accounts-topic-page-index.json`
   - the canonical list of all 36 chapters and 400 topics with exact topic numbers/names/
   page numbers and `teaching_sequence` (needed for `data-final-chapter`). Use this file's
   `unique_chapter_id` (format `M{module}-C{chapter}-U{unit}`, e.g. `M2-C5-U2`) for every
   `data-unitcode` you write. Never invent a chapter ID that isn't in this file.
7. `books/question-bank/metadata-index/topic-index.json` - richer per-topic descriptions
   for chapters already documented there; use its `sections[].ref` values for
   `data-subtopicref` where it has finer paragraph-level detail than file 6 above.

CASE SCENARIOS ARE MANDATORY - THIS IS THE #1 THING A PRIOR RUN GOT WRONG:
If a Case Scenario introduces shared facts that multiple MCQs depend on (e.g. "Suman Ltd.
sold 5 ACs to Beach Resort for Rs.45,000 each..."), that narrative MUST become its own
`<div class="case-scenario" id="CS-1" data-case-no="1" data-part="I"
data-question-count="N">` node with the full verbatim narrative, placed before the first
question that depends on it. Every dependent question then carries `data-case-ref="CS-1"`.
Do not drop the narrative and only keep the questions - a question referencing "the
Company" or a dollar figure with no visible source is broken output.

MARKS: `data-marks` on every qblock is ALWAYS a plain integer. Never write "14 (7+7)" or
any other arithmetic string - if a question has sub-parts with different marks, that means
it needs to be SPLIT per the question-splitting skill (#2 above), with each split fragment
carrying its own plain-integer `data-marks`.

COUNT QUESTIONS AGAINST THE PAPER'S OWN STATED STRUCTURE BEFORE YOU FINISH: MTP Part II
typically says "Question No.1 is compulsory. Answer any four questions from the remaining
five questions" - that means SIX questions are printed with model answers (Q1 plus five
optional Q2-Q6), even though a student only answers five of them. If you only find five
questions in your draft, you are almost certainly missing one - go back and check the
source PDF's question numbering directly, do not trust a count that "feels complete."

MTP sittings never receive real ICAI Examiner's Comments (they aren't real exams) - so
EVERY question/fragment in this sitting gets a SYNTHESIZED mistake note, never a real one.
Write it using this skill (condensed from
`books/question-bank/metadata-index/examiner-comments-writing-skill.md` and
`_claude/skills/SKILL-question-bank-examiner-comments.md` - read both in full too):

- Structure: one note per question/fragment, in the same paragraph style ICAI itself uses
  - not a bullet list.
- Open with a quantifier from this vocabulary, roughly by how common the mistake would
  realistically be: "A significant/large number of examinees...", "Most of the
  examinees...", "Many examinees...", "Several examinees...", "Some examinees...", "A few
  examinees...". Real ICAI comments often contrast two quantifiers in one note: "Most
  examinees correctly X. However, some mistakenly Y."
- Name the CONCRETE failure mode in accounting terms specific enough to picture the exact
  wrong step - never just "made errors."
- Name the standard: `AS 20, "Earnings per Share"` or `as per AS 26` (both citation styles
  are authentic, vary them).
- Trace the consequence forward: "As a result, they were unable to..." / "This resulted in
  incorrect..." / "Consequently..."
- Tone: third person, "examinees" (never "students"/"candidates"), descriptive past tense
  only, never prescriptive ("students should..."), never a scolding tone - reads like an
  audit finding. Write in this exact voice even though this is an MTP with no real
  examinees - the voice fidelity is intentional (see the examiner-comments skill file for
  why), the honesty comes from the data-source tag below, not a diluted voice.
- Every synthesized note's `.examiner-comment` div MUST have class="synthesized",
  `data-comment-source="synthesized"`, AND `data-source="Synthesized per
  examiner-comments-writing-skill.md — not ICAI-sourced"` - all three, exactly.

CRITICAL RULES:
1. Question and answer content must be VERBATIM - every number, every rupee sign
   (use `&#8377;`, never a literal backtick or other stray character), every table cell
   exactly as printed in the source. You are reformatting messy OCR layout into clean
   semantic HTML (tables get `<thead>`/`<tbody>`; MCQ options become
   `<ol class="options"><li data-opt="A">`), never changing what it says, and never
   substituting a description of the content ("as in source, verbatim") for the content
   itself.
2. Classify every multi-part descriptive question as independent or connected (see #2
   above) BEFORE tagging - independent sub-parts split into separate qblocks, each single-
   topic. A question testing multiple chapters that is genuinely connected keeps multiple
   `<span class="topic-tag">` entries in one qblock, each with its own `data-marks` share
   and a `data-topic-rank`.
3. Every qblock carries `data-final-chapter`, `data-confidence`
   ("high"/"medium"/"low"), and `data-review-status`
   ("verified"/"needs-visual-check"/"flagged"/"unreviewed"). If you are uncertain which
   chapter a question tests, or an answer-key entry looks wrong/inconsistent with the
   question, SAY SO explicitly via `data-issue` (vocabulary in the HTML schema skill) plus
   a prose `.extraction-note` - never silently guess, and never silently "correct" a
   source inconsistency, just flag it.
4. The `.author-comment` div is ALWAYS present, ALWAYS EMPTY, with `data-status="empty"`,
   for every single question - this is Pranav's own future annotation slot, not yours to
   fill.
5. Do not skip any question, including short standalone MCQs with no case scenario - every
   question in both source PDFs must appear in your output. Every MCQ answer key value
   must match the source PDF, not be guessed.
6. Write the actual file to `first_run/output/MTP_May2026_Set1.html` using your file-write
   capability - a chat response with HTML in it is not sufficient, this must be a real
   file on disk at that exact path.

WHEN YOU FINISH, report back: how many questions/fragments you captured (and how that
reconciles against the paper's own stated question count), how many total topic tags you
assigned, how many questions you split and why, and a list of anything you flagged as
uncertain.
```

**To reuse this same prompt for MTP Set 2**: change every occurrence of `Set1`/`Set 1` to
`Set2`/`Set 2` (both source filenames and the output path becomes
`first_run/output/MTP_May2026_Set2.html`). Nothing else changes.

---

## Prompt 2 of 3 — RTP (Revision Test Paper)

```
You are converting one CA Inter Advanced Accounting Revision Test Paper (RTP) sitting into
a single, self-contained, permanent HTML record. This is the ONLY time this source will
ever be read - the HTML you write becomes the primary record from now on, not the source
file. Get every number, every table, every tag correct. A prior run of this same task on a
different sitting produced a file with placeholder text standing in for real answers, zero
topic tagging, and one entire question silently missing - read the rules below carefully
enough to not repeat any of that.

READ THIS SOURCE FILE - THE PDF, NOT ANY .MD CONVERSION OF IT (in
books/question-bank/Raw_PDF_Question_Bank_CA_Inter_Accounts/):
- CAInter-AdvAcc-RTP-May2026-Q.pdf
  (RTPs are single combined files - announcements, questions, AND suggested answers are
  all in this one file, despite the "-Q" in its name. There is no separate answer file to
  look for.)
A .md conversion of this may also exist in first_run/source/ - do not use it. It is a
lossy intermediate extraction; verifying against it only confirms your output matches
another lossy copy, not the real source.

WRITE YOUR OUTPUT TO EXACTLY THIS PATH (create the file, do not just display HTML in your
response):
first_run/output/RTP_May2026.html

BEFORE YOU START, READ THESE FILES IN FULL (all in this repo):
1. `_claude/skills/SKILL-question-bank-html-schema.md` and
   `first_run/schema/HTML-SCHEMA.md` - the exact HTML structure you must produce, document-
   level and per-question, including paper-level facets on `<body>`, mandatory
   `.case-scenario` nodes, structured MCQ options, and deterministic IDs. Follow it exactly
   - a script will later parse your output mechanically by these class names and data
   attributes, so deviation breaks everything downstream.
2. `_claude/skills/SKILL-question-bank-question-splitting.md` - before writing any multi-
   part descriptive question, classify whether its sub-parts are INDEPENDENT (different
   companies/facts, just bundled under one question number) or CONNECTED (one continuous
   fact pattern). Independent sub-parts each become their OWN separate qblock record with
   their own ID, marks, and topic tag. Check each sub-part's actual facts, don't assume.
3. `_claude/skills/SKILL-question-bank-topic-tagging.md` - which taxonomy file is the join-
   key source of truth (`topic-index.json`'s `unitCode`+`sections[].ref`, never a new ID
   scheme), and how to compute `data-final-chapter`.
4. `_claude/skills/SKILL-question-bank-verbatim-extraction.md` - read this one especially
   carefully. It documents exactly what went wrong the first time this pipeline ran:
   placeholder text presented as verbatim content, a missing question caught only by
   counting against the paper's own stated structure, and mark totals that were
   individually wrong but happened to cancel out in the grand total. Do the same checks it
   describes before you finish.
5. `first_run/schema/book-style.css` - every visual property already has a CSS
   class/variable defined for it. Never write an inline style or hardcode a
   font-size/colour/margin - use the existing classes and link to the stylesheet as
   `<link rel="stylesheet" href="../schema/book-style.css">`.
6. `books/concept-book/syllabus-engine/data/1-ca-inter-adv-accounts-topic-page-index.json`
   - the canonical list of all 36 chapters and 400 topics with exact topic numbers/names/
   page numbers and `teaching_sequence` (needed for `data-final-chapter`). Use this file's
   `unique_chapter_id` (format `M{module}-C{chapter}-U{unit}`, e.g. `M2-C5-U2`) for every
   `data-unitcode` you write. Never invent a chapter ID that isn't in this file.
7. `books/question-bank/metadata-index/topic-index.json` - richer per-topic descriptions
   for chapters already documented there; use its `sections[].ref` values for
   `data-subtopicref` where it has finer paragraph-level detail than file 6 above.

CASE SCENARIOS ARE MANDATORY - THIS IS THE #1 THING A PRIOR RUN GOT WRONG: if a Case
Scenario introduces shared facts multiple MCQs depend on, that narrative MUST become its
own `<div class="case-scenario">` node (see the HTML schema skill), referenced by each
dependent question via `data-case-ref`. Do not drop the narrative and only keep the
questions.

MARKS: `data-marks` on every qblock is ALWAYS a plain integer - never an arithmetic
string. A question with differently-marked sub-parts needs to be SPLIT (see #2 above).

RTP sittings never receive real ICAI Examiner's Comments (they aren't real exams) - so
EVERY question/fragment in this sitting gets a SYNTHESIZED mistake note, never a real one.
Write it using this skill (condensed from
`books/question-bank/metadata-index/examiner-comments-writing-skill.md` and
`_claude/skills/SKILL-question-bank-examiner-comments.md` - read both in full too):

- Structure: one note per question/fragment, in the same paragraph style ICAI itself uses
  - not a bullet list.
- Open with a quantifier from this vocabulary, roughly by how common the mistake would
  realistically be: "A significant/large number of examinees...", "Most of the
  examinees...", "Many examinees...", "Several examinees...", "Some examinees...", "A few
  examinees...". Real ICAI comments often contrast two quantifiers in one note: "Most
  examinees correctly X. However, some mistakenly Y."
- Name the CONCRETE failure mode in accounting terms specific enough to picture the exact
  wrong step - never just "made errors."
- Name the standard: `AS 20, "Earnings per Share"` or `as per AS 26` (both citation styles
  are authentic, vary them).
- Trace the consequence forward: "As a result, they were unable to..." / "This resulted in
  incorrect..." / "Consequently..."
- Tone: third person, "examinees" (never "students"/"candidates"), descriptive past tense
  only, never prescriptive, never scolding - reads like an audit finding. Write in this
  exact voice even though this is an RTP with no real examinees - the voice fidelity is
  intentional, the honesty comes from the data-source tag, not a diluted voice.
- Every synthesized note's `.examiner-comment` div MUST have class="synthesized",
  `data-comment-source="synthesized"`, AND `data-source="Synthesized per
  examiner-comments-writing-skill.md — not ICAI-sourced"` - all three, exactly.

IMPORTANT RTP-SPECIFIC NOTES:
- RTPs often print announcements/applicability notes before the actual questions (e.g.
  MSME classification criteria updates) - these are NOT questions, do not create a
  `.qblock` for them, but you may include a brief plain-paragraph summary in the document
  header area if it seems useful context.
- RTPs sometimes don't print marks for every question - if marks aren't stated, omit
  `data-marks` entirely and say so in that question's `.extraction-note` rather than
  guessing a number.
- Watch for section headers in the source that mislabel the actual content being tested
  (this has happened before - a question printed under an "AS 7 Construction Contracts"
  header turned out to be pure AS 10 + AS 16 content). Tag from what the question actually
  asks, never from the paper's own header alone - and note the mismatch in the
  `.extraction-note` if you catch one.

CRITICAL RULES:
1. Question and answer content must be VERBATIM - every number, every rupee sign (use
   `&#8377;`, never a literal backtick), every table cell exactly as printed in the
   source. Reformat messy OCR layout into clean semantic HTML, never change what it says,
   never substitute a description of the content for the content itself.
2. Classify every multi-part descriptive question as independent or connected BEFORE
   tagging - independent sub-parts split into separate qblocks, each single-topic.
3. Every qblock carries `data-final-chapter`, `data-confidence`, `data-review-status`, and
   (if uncertain) `data-issue` plus a prose `.extraction-note` - never silently guess or
   silently "correct" a source inconsistency.
4. The `.author-comment` div is ALWAYS present, ALWAYS EMPTY, with `data-status="empty"`,
   for every single question.
5. Do not skip any question - every question in the source file must appear in your
   output.
6. Write the actual file to `first_run/output/RTP_May2026.html` using your file-write
   capability - a chat response with HTML in it is not sufficient, this must be a real
   file on disk at that exact path.

WHEN YOU FINISH, report back: how many questions/fragments you captured, how many total
topic tags you assigned, how many questions you split and why, and a list of anything you
flagged as uncertain.
```

---

## Prompt 3 of 3 — PYQ (Past Year Question)

**This one needs care, as Pranav specifically flagged: one of its two runs (Jan 2026) has
a REAL ICAI Examiner's Comments document to use; the other (May 2026) does not. Read the
conditional instruction inside this prompt carefully before running it for each.**

```
You are converting one CA Inter Advanced Accounting Past Year Question (PYQ) sitting into
a single, self-contained, permanent HTML record. This is the ONLY time this source will
ever be read - the HTML you write becomes the primary record from now on, not the source
file. Get every number, every table, every tag correct. A prior run of this same task on a
different sitting produced a file with placeholder text standing in for real answers, zero
topic tagging, and one entire question silently missing - read the rules below carefully
enough to not repeat any of that.

READ THIS SOURCE FILE - THE PDF, NOT ANY .MD CONVERSION OF IT (in
books/question-bank/Raw_PDF_Question_Bank_CA_Inter_Accounts/):
- CAInter-AdvAcc-PYQ-May2026-Ans.pdf
  (Despite "-Ans" in the name, this single file already contains both the full question
  text AND the answer for each question - PYQ Question-only PDFs were deprecated because
  they always converted blank/scanned; this Answers document embeds the question text
  before each answer. There is no separate question file to look for.)
A .md conversion of this may also exist in first_run/source/ - do not use it. It is a
lossy intermediate extraction; verifying against it only confirms your output matches
another lossy copy, not the real source.

CHECK FOR A MATCHING EXAMINER'S COMMENTS FILE - THIS DETERMINES HOW YOU WRITE MISTAKE
NOTES FOR THIS SITTING:
Look in `books/question-bank/Raw_PDF_Question_Bank_CA_Inter_Accounts/
examiner-comments-paper1/` for a file named `Paper1-ExaminerComments-May2026.md`. If it
does NOT exist (as is the case for May 2026 - ICAI has not yet published comments for this
recent sitting), every question/fragment in this sitting gets a SYNTHESIZED mistake note
(see the skill instructions below). If it DOES exist for whichever session you were
actually given, read it in full and match each of its comments to its exact corresponding
question - use the REAL comment for that question instead of synthesizing one, and mark it
accordingly (see the two `data-source`/`data-comment-source` variants below - use the
correct one for each question individually, don't assume the whole sitting is one or the
other if the comments document only covers some questions).

WRITE YOUR OUTPUT TO EXACTLY THIS PATH (create the file, do not just display HTML in your
response):
first_run/output/PYQ_May2026.html

BEFORE YOU START, READ THESE FILES IN FULL (all in this repo):
1. `_claude/skills/SKILL-question-bank-html-schema.md` and
   `first_run/schema/HTML-SCHEMA.md` - the exact HTML structure you must produce, document-
   level and per-question, including paper-level facets on `<body>`, mandatory
   `.case-scenario` nodes, structured MCQ options, and deterministic IDs. Follow it exactly
   - a script will later parse your output mechanically by these class names and data
   attributes, so deviation breaks everything downstream.
2. `_claude/skills/SKILL-question-bank-question-splitting.md` - before writing any multi-
   part descriptive question, classify whether its sub-parts are INDEPENDENT (different
   companies/facts, just bundled under one question number) or CONNECTED (one continuous
   fact pattern). Independent sub-parts each become their OWN separate qblock record.
3. `_claude/skills/SKILL-question-bank-topic-tagging.md` - which taxonomy file is the join-
   key source of truth, and how to compute `data-final-chapter`.
4. `_claude/skills/SKILL-question-bank-verbatim-extraction.md` - read this one especially
   carefully; it documents exactly what went wrong the first time this pipeline ran.
5. `_claude/skills/SKILL-question-bank-examiner-comments.md` and
   `books/question-bank/metadata-index/examiner-comments-writing-skill.md` - read both IN
   FULL regardless of whether this sitting has real comments, since you will very likely
   need them for at least some questions.
6. `first_run/schema/book-style.css` - every visual property already has a CSS
   class/variable defined for it. Never write an inline style or hardcode a
   font-size/colour/margin - use the existing classes and link to the stylesheet as
   `<link rel="stylesheet" href="../schema/book-style.css">`.
7. `books/concept-book/syllabus-engine/data/1-ca-inter-adv-accounts-topic-page-index.json`
   - the canonical list of all 36 chapters and 400 topics with exact topic numbers/names/
   page numbers and `teaching_sequence`. Use this file's `unique_chapter_id` (format
   `M{module}-C{chapter}-U{unit}`, e.g. `M2-C5-U2`) for every `data-unitcode` you write.
   Never invent a chapter ID that isn't in this file.
8. `books/question-bank/metadata-index/topic-index.json` - richer per-topic descriptions
   for chapters already documented there; use its `sections[].ref` values for
   `data-subtopicref` where it has finer paragraph-level detail than file 7 above.

CASE SCENARIOS ARE MANDATORY - THIS IS THE #1 THING A PRIOR RUN GOT WRONG: if a Case
Scenario introduces shared facts multiple MCQs depend on, that narrative MUST become its
own `<div class="case-scenario">` node, referenced by each dependent question via
`data-case-ref`. Do not drop the narrative and only keep the questions.

MARKS: `data-marks` on every qblock is ALWAYS a plain integer - never an arithmetic
string. A question with differently-marked sub-parts needs to be SPLIT per the
question-splitting skill.

FOR ANY QUESTION USING A REAL ICAI COMMENT (only possible if the matching
Paper1-ExaminerComments-{session}.md file exists and covers that question):
- Transcribe the comment faithfully - verbatim if you're quoting it directly, or clearly
  paraphrased if condensing, but never alter its substance.
- Set `data-comment-source="icai"` and `data-source="ICAI Examiner's Comment — {Session},
  verbatim"` (or `...,paraphrased`) on that `.examiner-comment` div - no `synthesized`
  class.
- If a comment in the source document covers multiple sub-parts or questions together,
  it's fine to reuse/split it across those specific questions, but don't force-fit a
  comment onto a question it doesn't actually address.

FOR ANY QUESTION WITHOUT A MATCHING REAL COMMENT (write a synthesized one, condensed from
the skill files you read in full above):
- Structure: one note per question/fragment, in the same paragraph style ICAI itself uses
  - not a bullet list.
- Open with a quantifier from this vocabulary, roughly by how common the mistake would
  realistically be: "A significant/large number of examinees...", "Most of the
  examinees...", "Many examinees...", "Several examinees...", "Some examinees...", "A few
  examinees...". Real ICAI comments often contrast two quantifiers in one note.
- Name the CONCRETE failure mode in accounting terms specific enough to picture the exact
  wrong step - never just "made errors."
- Name the standard: `AS 20, "Earnings per Share"` or `as per AS 26` (both citation styles
  are authentic, vary them).
- Trace the consequence forward: "As a result, they were unable to..." / "This resulted in
  incorrect..." / "Consequently..."
- Tone: third person, "examinees", descriptive past tense only, never prescriptive, never
  scolding - reads like an audit finding.
- Set class="synthesized", `data-comment-source="synthesized"`, AND `data-source=
  "Synthesized per examiner-comments-writing-skill.md — not ICAI-sourced"` - all three,
  exactly.

CRITICAL RULES:
1. Question and answer content must be VERBATIM - every number, every rupee sign (use
   `&#8377;`, never a literal backtick), every table cell exactly as printed in the
   source. Reformat messy OCR layout into clean semantic HTML, never change what it says,
   never substitute a description of the content for the content itself.
2. Classify every multi-part descriptive question as independent or connected BEFORE
   tagging - independent sub-parts split into separate qblocks, each single-topic.
3. Every qblock carries `data-final-chapter`, `data-confidence`, `data-review-status`, and
   (if uncertain which chapter a question tests, or which comment truly matches) a
   `data-issue` plus a prose `.extraction-note` - never silently guess or force a match.
4. The `.author-comment` div is ALWAYS present, ALWAYS EMPTY, with `data-status="empty"`,
   for every single question.
5. Do not skip any question - every question in the source file must appear in your
   output.
6. Write the actual file to `first_run/output/PYQ_May2026.html` using your file-write
   capability - a chat response with HTML in it is not sufficient, this must be a real
   file on disk at that exact path.

WHEN YOU FINISH, report back: how many questions/fragments you captured, how many used a
REAL examiner comment vs. a synthesized one (this should be a clean count, not a guess),
how many total topic tags you assigned, how many questions you split and why, and a list
of anything you flagged as uncertain.
```

**To reuse this same prompt for PYQ Jan 2026** (the one WITH real comments): change every
occurrence of `May2026`/`May 2026` to `Jan2026`/`Jan 2026` in the source filename and
output path (`first_run/output/PYQ_Jan2026.html`). The conditional-check instruction
inside the prompt itself handles the rest automatically — it will find
`Paper1-ExaminerComments-Jan2026.md` this time and use real comments wherever they match.

---

## Notes for whoever is running these (not part of the prompts above)

- Run Prompt 1 twice (Set 1, Set 2 — swap the one detail noted), Prompt 2 once, Prompt 3
  twice (May 2026, Jan 2026 — swap the one detail noted). **5 runs total, 5 output HTML
  files.**
- Expect the PYQ Jan 2026 run to report a mix of real-vs-synthesized comments — if it
  reports 100% synthesized, double check it actually found and read
  `Paper1-ExaminerComments-Jan2026.md`.
- **Review each output against the source PDF directly** (not the MD conversion), both by
  opening it in a browser (visual check) and by working through the checklist in
  `_claude/skills/SKILL-question-bank-verbatim-extraction.md`: is every question/case-
  scenario narrative present and counted against the paper's own stated structure, is
  every number in every answer actually verbatim (spot-check at least one number per
  descriptive answer against the PDF), does the marks arithmetic reconcile at every level,
  and is every claimed-verbatim table actually populated with real content rather than a
  description of content. This is the checkpoint before the extraction script gets built
  against these 5 files as real data — the first run through this checklist on MTP Set 1
  caught a missing question, a missing case scenario, and two wrong mark totals that a
  purely visual skim had missed.
