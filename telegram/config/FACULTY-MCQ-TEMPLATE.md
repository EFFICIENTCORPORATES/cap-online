# Faculty MCQ template — the canonical, deterministically-parseable format

Added 2026-08-10, per Pranav's instruction to make faculty content ingestion
**deterministic, not AI-driven**. This is the one format
`telegram/tools/convert_faculty_mcq_docx.py` (the converter script) actually
understands — a faculty's `.docx` filled in exactly this way converts to our
JSON schema with **zero AI involvement**: pure regex + `python-docx` table
parsing. A file that doesn't follow this shape isn't silently guessed at —
the converter reports exactly what it couldn't parse and stops there.

This format is not invented from nothing — it's the same shape CS Arun
Chouhan's own `CMA_Foundation_Module1_40_MCQs.docx` already used
independently (see [[1lavya-csarunchouhan-demo-content]] memory), formalized
as the standard because it already proved itself fully parseable. His
*other* file (`IncorporationOfCompany_50MCQs_June2026.docx`) used a
different shape — an inline "✓ CORRECT ANSWER" marker on the option itself
— and that shape is **exactly what produced 5 real defects** (the checkmark
landing on the wrong option, silently) when it was manually extracted. This
template deliberately avoids that failure mode structurally — see rule 3.

## The rules

1. **One question = one paragraph**, matching exactly:
   `Q<number>. <question text> [optional bracketed topic tag]`
   Example: `Q7.  [Section 109 — Money Bills] A Money Bill CANNOT be introduced in the —`
   The bracketed tag is optional and becomes `topic_text` if present.

2. **Options are separate paragraphs immediately after the question**,
   lowercase, parenthesized, in order:
   ```
   (a) Lok Sabha
   (b) Rajya Sabha
   (c) Either House of Parliament
   (d) Joint sitting of both Houses
   ```
   2 to 4 options are allowed (not every real MCQ has exactly 4) — the
   converter reads however many `(a)`/`(b)`/`(c)`/`(d)` paragraphs appear
   before the next `Q<number>.` or the Answer Key table, in order.

3. **Never mark the correct answer inline.** No "✓", no bold, no
   asterisk on an option — the correct answer lives in exactly ONE place:
   the Answer Key table at the end (rule 4). This is the single most
   important rule — it's what makes a "checkmark on the wrong option"
   error structurally much harder to make (a faculty filling in one
   summary table, once, per question, is far less error-prone than an
   inline marker repeated across every question block) and, if it still
   happens, confines the mistake to one auditable place instead of 50
   scattered ones.

4. **One Answer Key table at the end of the document**, a real Word table
   (Insert → Table), not text -- exactly two columns:

   | Q. No. | Answer |
   |---|---|
   | Q1 | b |
   | Q2 | c |
   | Q3 | a |

   (Arun's original file used a 4-pairs-per-row layout — `Q1 → (b) | Q2 →
   (c) | ...` — that's also accepted; the converter reads whatever table
   cells contain a `Q<n>` / letter pair, in any consistent table shape.)

5. **An "Explanation:" paragraph is optional but strongly preferred**,
   immediately after a question's options:
   ```
   Explanation: Article 109 requires a Money Bill to originate only in
   the Lok Sabha; the Rajya Sabha may only recommend changes within 14
   days, not amend or reject it.
   ```
   If present, this becomes `answer_html` **verbatim** (your own words,
   not rewritten). If absent, the converter still produces the question
   with `answer_html: null` and flags it in the conversion report as
   `"needs_explanation"` — someone has to write one before that question
   can go live (see `_claude/skills` or ask Pranav's session for how that
   review step works) — the converter will never invent one on its own.

6. **One `.docx` = one chapter/topic scope.** Course/Level/Subject/Chapter
   are supplied to the converter as arguments (`--course`, `--level`,
   `--chapter-slug`, `--chapter-label`, `--unitcode`), not read from the
   document — keeps the document itself simple and this rule matches how
   every existing faculty docx has actually been scoped in practice.

## What the converter checks and reports, never silently resolves

- A question with no matching Answer Key entry → flagged, excluded from
  the output, listed in the report.
- An Answer Key entry with no matching question → flagged (a typo'd `Q`
  number is a real, easy mistake).
- A question whose option count doesn't match `(a)`..`(d)` cleanly
  (e.g. a stray `(e)`) → flagged, excluded, never guessed at.
- Any question whose text contains a number followed by "day", "%",
  "crore", "lakh", or "₹"/"Rs." → flagged with a **"verify this figure is
  still current"** reminder (not blocked — these are exactly the class of
  fact most likely to have been amended since the document was written,
  per the real Q6/Q8 findings in [[1lavya-csarunchouhan-demo-content]]).

## Example

See `telegram/config/faculty_mcq_template_example.docx` for a filled-in,
5-question example following every rule above — generate it (or a blank
starting template) with:
```
python telegram/tools/generate_faculty_mcq_template.py
```
