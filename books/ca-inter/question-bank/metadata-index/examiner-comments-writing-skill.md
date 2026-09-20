# Skill: writing "Common Student Mistakes" in ICAI's Examiner's-Comments voice

Written 2026-07-22, from analysing all 6 real ICAI "Examiners' Comments on the
Performance of the Examinees" documents Pranav sourced for Paper 1 (Advanced
Accounting): Jan 2025, May 2024, Sep 2024, May 2025, Sep 2025, Jan 2026. The
Paper-1-only slice of each lives at
`Raw_PDF_Question_Bank_CA_Inter_Accounts/examiner-comments-paper1/Paper1-ExaminerComments-{Session}.md`.

## Purpose

The `commonMistakes` field on a tagged question (see `TAGGING-SCHEMA.md`) needs
content for **every** question in the Question Bank Book — but real ICAI
Examiner's Comments only exist for the 6 PYQ sittings above (MTP/RTP are not
real exams, so ICAI never comments on them; older/other PYQ sittings don't have
a sourced comments PDF yet either). This skill is how a mistake note gets
written for everything **outside** those 6 sittings, in a voice indistinguishable
in *style* from the real thing — while the provenance rule (below) keeps it
never confusable in *authority* with the real thing.

## What real ICAI comments actually look like — the pattern

**Structure:** one paragraph per question, sub-parts (a)/(b)/(c) run inline
within the same paragraph block, not separate headers. Always under a
"Specific Comments" heading, one per numbered question in sitting order.

**Opening quantifier — always one of a small fixed vocabulary, roughly in this
descending-severity order:**
- "A significant/large number of examinees..." / "A majority of examinees..."
- "Most of the examinees..." / "Most examinees..."
- "Many examinees..." / "Many of them..."
- "Several examinees..."
- "Some examinees..." / "Some of them..."
- "A few examinees..." / "Few examinees..."
- "Only a few/small number of examinees..."

Comments routinely **contrast** a quantifier for what went right against one
for what went wrong in the same sentence pair: *"Most examinees correctly
recorded the journal entries. However, some mistakenly credited the respective
expense account instead of the bank account."*

**Body — always in this order, not all elements present every time:**
1. Name the concrete failure mode in accounting terms, specific enough to
   picture the exact wrong step (not "made errors" alone — *which* errors:
   "failed to include the unguaranteed residual value in the total lease
   payments to determine the gross investment").
2. Name the standard being tested, usually in the exact ICAI citation form:
   `AS 20, "Earnings per Share"` or `as per AS 26` — inconsistently
   quoted/unquoted in the real source, both forms are authentic.
3. Trace the **consequence chain** forward: "As a result, they were unable
   to..." / "This resulted in incorrect..." / "Consequently, they could
   not..." / "leading to errors in..." — errors compound into the next
   sub-calculation, mirrored honestly (a residual-value miss cascades into a
   wrong unearned-finance-income figure, which was itself the actual ask).
4. Occasionally a very specific numeric anchor when it sharpens the point:
   *"Many could ascertain only the labour cost of ₹3,23,200, while the
   remaining elements of cost were incorrectly computed."*

**Tone:** third person, "examinees" (never "students" or "candidates"),
descriptive past tense only ("failed to", "were unable to", "did not") — never
prescriptive advice ("students should..."), never blame-toned, never exclaims.
Reads like an audit finding, not a scolding.

**Not to imitate:** the raw OCR text has PDF line-wrap artifacts (stray spaces
mid-word: "gro ss", "t o", "�" in place of curly quotes/apostrophes) — these are
extraction noise, not ICAI's actual prose. Don't reproduce them; use clean
apostrophes/em-dashes when writing new comments in this style.

## Worked example (synthesized, not from a real document)

Question: MTP-May2024-S1-PartI-Q2 (AS 10 + AS 16 — factory construction cost
elements, legal cost/relocation/inauguration/overhead capitalisation, net
borrowing cost).

> Many examinees capitalised the inauguration-ceremony cost and the
> employee-relocation cost directly to the factory, failing to apply AS 10's
> distinction between costs necessary to bring an asset to its working
> condition and costs merely associated with commissioning it. Several
> examinees also did not net the temporary-investment income against the
> borrowing cost eligible for capitalisation under AS 16, resulting in an
> overstated carrying amount and a consequential error in the depreciation
> charge.

## Provenance rule — non-negotiable

Every `commonMistakes` entry carries a `source` tag:
- `"ICAI Examiner's Comment — {Session}, verbatim"` or `"...,paraphrased"` —
  only for the 6 sittings with a real sourced document, and only when the
  comment can be confidently matched to that exact question/sub-part.
- `"Synthesized per examiner-comments-writing-skill.md — not ICAI-sourced"` —
  everything else.

Never blend the two without the tag making it obvious which is which — this is
the same discipline `AS10_Question_Book.html` already applies to reconstructed
answer workings (flagged as "not verbatim ICAI text").
