# SKILL — Question Bank: Verbatim Extraction Discipline

> **What this is:** the rules that exist specifically because the first real pilot run of
> this pipeline failed them — an external AI was given a clear schema and clear
> instructions, and still produced a sitting HTML file with placeholder text standing in
> for real answers, zero topic tagging despite an explicit requirement, and one entire
> 14-mark question silently missing. This skill documents what went wrong and the concrete
> checks that catch it, so the next AI (or human) running this pipeline doesn't have to
> rediscover the failure mode from scratch.
>
> This is a mindset/verification skill, not a structural one — read
> `SKILL-question-bank-html-schema.md` for the shape, this file for how to make sure the
> content poured into that shape is actually trustworthy.

---

## 1. Read the PDF. Not the MD conversion.

Source PDFs get converted to `.md` earlier in the pipeline for other purposes (see
`CLAUDE.md` §6), but when authoring or **reviewing** a sitting HTML file, go back to the
original PDF, not the MD. The MD conversion is a lossy intermediate (plain-text
extraction, no table structure, OCR artifacts baked in) — verifying against it just
confirms the HTML matches another lossy copy, not the source. Pranav's explicit
instruction on the first review of this pipeline was exactly this: *"Please use the MTP
May 26 PDF file as source and not the MD file."*

## 2. Verbatim means verbatim — not "verbatim in spirit"

The first pilot's Part II answers contained text like:

> "Eligible borrowing cost calculation and working notes as in source answers (verbatim,
> OCR-normalized)."

This is a **description of content**, not the content — and it claims to be "verbatim"
while containing none of the actual numbers. This is the single most dangerous failure
mode in this pipeline, because it's easy to skim past: the sentence reads fluently, cites
"verbatim," and gives no visual signal (unlike an obviously blank field) that anything is
wrong. **Every `.question` and `.answer-block` must contain the actual transcribed
content** — every number, every working note, every table row — never a meta-description
of where the content "would be" or a claim that it exists "in the source."

**How to catch this in review:** don't just read the HTML fluently top to bottom. For
every descriptive (non-MCQ) answer, spot-check at least one specific number against the
source PDF. A file can read as complete and professional while being substantively empty.

## 3. Count questions against the source before trusting the output

The first pilot's Part II was supposed to contain 6 printed questions (Q1 compulsory +
Q2–Q6, of which a student answers any 4) — the generated HTML only had 5. This was not
caught by reading the HTML in isolation; it was only caught by counting question numbers
against the source PDF's own instructions ("Answer any four questions from the remaining
five questions" implies 1 + 5 = 6 printed questions, not 5). **Always reconcile the
question count and the marks total against the paper's own stated structure**, not just
against what the AI happened to produce.

## 4. Marks arithmetic is a cheap, high-value check — always run it

The first pilot also had two individually wrong mark values (a sub-part total of 12
where the source said 14, another showing 16 where the source said 14) that happened to
cancel out in the file's grand total, making the file look internally consistent at a
glance. **Check marks at every level**, not just the paper grand total:
- Each Part I MCQ's marks against the paper's stated per-MCQ value.
- Each Part II question's marks against the sum of its own sub-parts.
- The Part I total + Part II compulsory question + best-N-of-M optional questions against
  the paper's stated total marks — understanding that a paper printing more optional
  questions than a student actually answers (e.g. 6 printed, 5 required) means the sum of
  *all printed* Part II marks will legitimately exceed the paper's stated total. That's
  expected, not an error — the error is a Part II question's own marks not matching the
  sum of what it's split into.

## 5. Flag, never silently fix, a source inconsistency

While rebuilding `MTP_May2026_Set1.html`'s Q3 (Falgun Ltd.), the source *answer key
itself* printed a Share Capital note with figures for a different company size than the
same paper's own trial balance — an inconsistency in the source PDF, not introduced by
extraction. The correct response was to reproduce it exactly as printed and add an
`extraction-note` (and, per the current schema, `data-issue="source-inconsistency"`)
flagging it for Pranav's judgment call — **not** to silently "correct" it to what seemed
more internally consistent. This pipeline's job is faithful transcription plus honest
flagging, never editorial correction of the source, even when the source is visibly wrong.

## 6. MCQ answer keys are routinely bare-letter-only — verify any authored explanation against the stated letter before trusting it

Found 2026-07-26, during an external review of `AS02_Question_Book.html`: ICAI's own
"Suggested Answers" documents for MCQs conventionally give **just the letter** (e.g. a
plain answer-key table reading `4. (B)`, `10 (a)`, `11 (d)` — no working at all). This is
true across PYQ and MTP sittings alike (confirmed in both
`CAInter-AdvAcc-PYQ-Jan2026-Ans.md` and `CAInter-AdvAcc-MTP-May2026-Set2-Ans.md`). Any
explanation accompanying such an MCQ in the sitting HTML is therefore **necessarily
AI-authored**, never transcribed — and two of these authored explanations (PYQ Jan2026 Q4,
PYQ May2026 Q6, both AS 2) turned out to have the underlying AS 2 rule **backward**: each
one's own arithmetic actually computed to the *distractor* option, not the letter the
qblock claimed, while the `extraction-note` on both falsely read "Verbatim... Confidence:
high." The attached synthesized "Common Student Mistakes" note compounded this by
explicitly branding the *correct* method as the student error — exactly backward, and
exactly the kind of mistake a student revising from this book would internalize as fact.

**The rule going forward:**
1. Before marking `data-review-status="verified"` on any MCQ qblock whose answer-block
   contains a computed explanation (not just a letter), **independently redo the
   arithmetic yourself and confirm it lands on the stated `data-answer` letter** — don't
   accept a plausible-reading explanation at face value, even one you wrote yourself
   moments earlier. This is the single check that would have caught both errors above; the
   explanations read fluently and cited the right AS 2 concept, they just had the
   direction of the rule inverted.
2. Tag every qblock built this way with `data-issue="answer-key-letter-only"` (extends the
   `data-issue` vocabulary in `SKILL-question-bank-html-schema.md` §7), and have the
   `extraction-note` say plainly that the letter/options are verbatim but the explanation
   is authored — never claim "verbatim... high confidence" for reasoning that was never in
   the source. This is a metadata-honesty requirement even in cases where the authored
   explanation turns out to be correct (4 sibling AS 2 MCQs in `MTP_May2026_Set2.html` had
   correct math but the same dishonest "verbatim" label, fixed the same day).
3. Given this was found on only 2 of ~13 AS 2 MCQ records checked so far, treat it as a
   **systemic risk across all `mcq`/`case-mcq` qblocks in all 5 pilot sittings** (most
   MCQs in this exam format are answer-key-letter-only), not a two-instance bug. A full
   audit pass — re-deriving the arithmetic for every MCQ explanation against its own
   source figures — is recommended before this pipeline scales past the pilot, flagged to
   Pranav 2026-07-26, not yet scheduled or completed.

## 7. A mechanical verification gate is the long-term fix — not yet built

Everything in §§2–4 above is currently caught by careful human/AI review, which doesn't
scale to ~50 papers. The intended long-term safeguard (proposed, not yet built) is a
Python script run against every generated sitting HTML file that mechanically checks:
- **Arithmetic self-consistency** on every HTML table (row/column totals actually sum).
- **Number-traceability** — every number appearing in the HTML's answer content also
  appears somewhere in the source PDF's extracted text (catches fabricated or garbled
  figures without needing a human to re-derive every working).
- The marks and question-count checks in §§3–4, automated rather than manually run.

Until this exists, the manual discipline in this file is the only gate. Don't skip it
because "the schema was followed" — the first pilot followed the schema's document
structure closely while still failing every one of the checks above.
