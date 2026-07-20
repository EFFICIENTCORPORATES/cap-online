# Phase 1 — ICAI-Practice Extraction Prompts (for any Tier 2 tool)

Extracts every question + answer from the 8 Model Test Papers inside the ICAI-Practice
compilation (`CAInter-AdvAcc-MTP-ICAI-Practice-Q.pdf` / `-Ans.pdf`, a scanned document).
Both PDFs have already been OCR'd (Tesseract) — **do not re-OCR or read the PDFs
directly; read the plain-text OCR output files below.**

Source files (in `books/question-bank/metadata-index/icai-practice-extraction/`):
- `icai_practice_Q_ocr.txt` — full OCR of the Q PDF (101 physical pages). Each page is
  delimited by a line like `===== PHYSICAL PAGE N =====`. Physical page N = printed
  page (N-5) for this file (e.g. physical page 6 = printed page 1).
- `icai_practice_Ans_ocr.txt` — full OCR of the Ans PDF (111 physical pages), same
  page-delimiter format. **The Q-to-Ans printed-page offset is NOT fixed/reliable for
  this file — locate each answer by matching its content to the question, never assume
  a fixed page offset.**
- `icai_practice_MTP1_Q_extracted.json` through `icai_practice_MTP4_Q_extracted.json` —
  Model Test Papers 1-4's questions have ALREADY been extracted (by Claude, reading the
  OCR text directly) and don't need re-extraction. These are given to you as **the exact
  format/detail level to match** for Papers 5-8, and so you can locate/attach their
  answers without re-deriving the question text.

**OCR quality note:** the OCR is generally clean but has known artifacts: currency
symbols (₹) sometimes render as `=`, `%`, `2`, or are dropped; tables (trial balances,
balance sheets) often lose column alignment and need reconstruction from context; roman
numeral sub-parts like "(iii)" sometimes get split oddly across lines. Where you
reconstruct a garbled number/table, note what you did in a `"notes"` field on that
question — do not silently guess and present it as certain. If a question's per-marks
label is genuinely not printed (common for Part I MCQ case-scenario sub-parts, where
only the block total like "4 MCQs of 2 Marks each: Total 8 Marks" is printed, not each
sub-part), set `printedMarks` to `null` rather than dividing/guessing — I will decide
default handling for these in a later phase.

**Output schema** (same as the MTP1-4 files given to you — match it exactly):
```json
{
  "sourceFile_Q": "CAInter-AdvAcc-MTP-ICAI-Practice-Q.pdf",
  "modelTestPaper": 5,
  "physicalPageRange": "52-64",
  "questions": [
    {
      "qNoInPaper": "1(i)",
      "type": "MCQ-Direct | MCQ-Scenario | Descriptive",
      "printedMarks": 2,
      "pageQ": 52,
      "pageAns": 214,
      "caseScenario": "one-line description of the shared case-scenario context, only for MCQ-Scenario questions",
      "questionTextHtml": "...",
      "answerTextHtml": "...",
      "notes": "any OCR reconstruction caveats or uncertainties"
    }
  ]
}
```
Set `answerTextHtml`/`pageAns` to `null` and add `"answerNotFound": true` if a question's
answer genuinely cannot be located in the Ans OCR text — do not invent one.

---

## Prompt 1 of 2 — Extract Model Test Papers 5-8 (Q-side)

> Read `books/question-bank/metadata-index/icai-practice-extraction/icai_practice_Q_ocr.txt`
> from the line containing `MODEL TEST PAPER 5` through the end of the file (Model Test
> Papers 5, 6, 7, and 8 — this file contains only these 4 remaining papers; there is no
> Paper 9). Also open `icai_practice_MTP4_Q_extracted.json` first as a reference for the
> exact level of detail and JSON structure expected (case scenario descriptions, full
> option text, sub-part numbering, notes field usage for OCR ambiguities). Extract every
> question, sub-part, and case-scenario context from Papers 5-8 following the schema and
> instructions above this prompt in `books/question-bank/metadata-index/phase1-icai-practice-prompts.md`.
> Output 4 JSON objects (one per Model Test Paper), matching the MTP1-4 files' structure.
> Do not extract answers yet — that's Prompt 2. Read the entire remainder of the file;
> don't stop partway (Paper 8 is the last one, near the end of a 101-page OCR file).

---

## Prompt 2 of 2 — Locate and attach answers for all 8 Model Test Papers

> Read `books/question-bank/metadata-index/icai-practice-extraction/icai_practice_Ans_ocr.txt`
> in full (111 physical pages). For every question in `icai_practice_MTP1_Q_extracted.json`,
> `icai_practice_MTP2_Q_extracted.json`, `icai_practice_MTP3_Q_extracted.json`,
> `icai_practice_MTP4_Q_extracted.json`, and the 4 new JSON objects you produced in
> Prompt 1 for Papers 5-8, locate that question's official answer/solution in the Ans OCR
> text by matching content (each Model Test Paper's answers are grouped together in the
> Ans file, in the same paper order as the Q file, but the internal page offset is not
> fixed — search by matching question number and subject matter within each paper's
> answer block). Add `answerTextHtml` (full HTML-formatted solution text, numbers exactly
> as printed, `₹` for rupee symbol) and `pageAns` (physical page in the Ans OCR file) to
> every question object. Follow the schema and instructions above this prompt in
> `books/question-bank/metadata-index/phase1-icai-practice-prompts.md`, including the
> `answerNotFound` rule for any question whose answer genuinely cannot be located.
> Output all 8 complete JSON objects (Papers 1-8, each now with both questions and
> answers).

---

## After running both

Bring back all 8 complete JSON paper-objects and I'll validate them (spot-checking
answers against the Ans OCR text directly, particularly checking that nothing was
invented for the `answerNotFound` cases) before merging into the master
extracted-questions dataset alongside MTP/RTP/PYQ.
