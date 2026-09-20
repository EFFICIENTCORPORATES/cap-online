# Phase 1 — RTP Extraction Prompts (for Tool B, e.g. GitHub Copilot)

Extracts every question + solution from all 7 RTP files into structured JSON.

**Important structural difference from MTP:** each RTP file is a SINGLE document
containing BOTH the questions AND their solutions bundled together — solutions appear
later in the same document, often after a "SUGGESTED ANSWERS / HINTS" heading. There is
no separate Ans file. RTPs also typically include a Part I MCQ/case-scenario section
before the Part II descriptive questions — don't skip Part I.

**Output schema:**
```json
{
  "sourceFile_Q": "CAInter-AdvAcc-RTP-Jan2025-Q.pdf",
  "sourceFile_Ans": "CAInter-AdvAcc-RTP-Jan2025-Q.pdf",
  "attempt": "Jan 2025",
  "paperType": "RTP",
  "set": null,
  "questions": [
    {
      "qNoInPaper": "5",
      "type": "MCQ-Direct | MCQ-Scenario | Descriptive",
      "printedMarks": null,
      "pageQ": 4,
      "pageAns": 12,
      "questionTextHtml": "...",
      "answerTextHtml": "..."
    }
  ]
}
```
Note `sourceFile_Q` and `sourceFile_Ans` are the SAME filename for RTPs (self-contained) —
only `pageQ` and `pageAns` differ. RTPs frequently print NO marks at all for descriptive
questions — if genuinely absent, use `null`, don't guess.

**Instructions common to every prompt below:**
1. Read the full `.md` file named — folder: `books/question-bank/Raw_PDF_Question_Bank_CA_Inter_Accounts/`. Read start to finish; don't stop partway through (a known issue in a prior phase of this project was a tool stopping at an arbitrary line count and missing the back half of long RTP files).
2. Extract questions from BOTH the Part I MCQ/case-scenario section and the Part II descriptive section.
3. For each question, locate its solution independently by matching content later in the same document — never assume a fixed offset.
4. `pageQ` / `pageAns`: count physical page breaks using the repeating `© The Institute of Chartered Accountants of India` footer line (each occurrence = end of one page). If uncertain, use `null` rather than guessing.
5. `questionTextHtml` / `answerTextHtml`: full text, HTML-formatted (`<table>`/`<tr>`/`<td>` for tabular content), numbers exactly as printed, `₹` for rupee symbol.
6. Every question and sub-part must appear — don't skip or summarize.

---

## Prompt 1 of 3 — Jan 2025, Jan 2026, May 2024

Files: `CAInter-AdvAcc-RTP-Jan2025-Q.md`, `CAInter-AdvAcc-RTP-Jan2026-Q.md`, `CAInter-AdvAcc-RTP-May2024-Q.md`

> Extract every question and its solution from these 3 RTP files in `books/question-bank/Raw_PDF_Question_Bank_CA_Inter_Accounts/`, following the schema and instructions above this prompt in `books/question-bank/metadata-index/phase1-rtp-prompts.md`. Read each file completely from start to end before extracting. Output 3 JSON objects (one per file).

---

## Prompt 2 of 3 — May 2025, May 2026

Files: `CAInter-AdvAcc-RTP-May2025-Q.md`, `CAInter-AdvAcc-RTP-May2026-Q.md`

> Extract every question and its solution from these 2 RTP files in `books/question-bank/Raw_PDF_Question_Bank_CA_Inter_Accounts/`, following the schema and instructions above this prompt in `books/question-bank/metadata-index/phase1-rtp-prompts.md`. Read each file completely from start to end before extracting — `RTP-May2026-Q.md` is long (~1990 lines); make sure you reach the Test Your Knowledge section at the end, not just the main descriptive questions. Output 2 JSON objects (one per file).

---

## Prompt 3 of 3 — Sep 2024, Sep 2025

Files: `CAInter-AdvAcc-RTP-Sep2024-Q.md`, `CAInter-AdvAcc-RTP-Sep2025-Q.md`

> Extract every question and its solution from these 2 RTP files in `books/question-bank/Raw_PDF_Question_Bank_CA_Inter_Accounts/`, following the schema and instructions above this prompt in `books/question-bank/metadata-index/phase1-rtp-prompts.md`. Read each file completely from start to end before extracting — `RTP-Sep2025-Q.md` is long (~1530 lines); make sure you reach the full Test Your Knowledge section at the end. Output 2 JSON objects (one per file).

---

## After running all 3

Bring back all 7 JSON file-objects and I'll validate them before merging into the master extracted-questions dataset.
