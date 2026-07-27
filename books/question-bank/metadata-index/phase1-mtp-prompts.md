# Phase 1 — MTP Extraction Prompts (for Tool A, e.g. Gemini)

Extracts every question + answer from all 9 MTP attempts (18 Q/Ans file pairs, 36 files total)
into structured JSON. All files have clean, non-blank `.md` conversions — this is the most
mechanical of the three extraction tasks.

**Output schema** (same for every prompt below):
```json
{
  "sourceFile_Q": "CAInter-AdvAcc-MTP-Jan2025-Set1-Q.pdf",
  "sourceFile_Ans": "CAInter-AdvAcc-MTP-Jan2025-Set1-Ans.pdf",
  "attempt": "Jan 2025",
  "paperType": "MTP",
  "set": "Set 1",
  "questions": [
    {
      "qNoInPaper": "1(b)",
      "type": "MCQ-Direct | MCQ-Scenario | Descriptive",
      "printedMarks": 5,
      "pageQ": 3,
      "pageAns": 2,
      "questionTextHtml": "...",
      "answerTextHtml": "..."
    }
  ]
}
```
Return one such object per paper (i.e. one array of 2 objects per prompt: Set 1 and Set 2).

**Instructions common to every prompt below:**
1. Read the `.md` files named (both Q and Ans for each attempt/set) — folder: `books/question-bank/Raw_PDF_Question_Bank_CA_Inter_Accounts/`.
2. Split each Q document into individual question objects, preserving sub-parts (e.g. "1(b)") exactly as printed.
3. `type`: MCQ-Direct = a single standalone question with 4 lettered options. MCQ-Scenario = several MCQs grouped under one "Case Scenario" / "based on the following information" heading. Descriptive = everything else.
4. `printedMarks`: the exact number printed next to the question or sub-part. If genuinely not printed anywhere for that question, set to `null` — do not guess or infer from other questions.
5. `pageQ` / `pageAns`: since these are `.md` files with no reliable printed page markers, count physical page breaks using the repeating `© The Institute of Chartered Accountants of India` footer line (each occurrence marks the end of one page) — report the resulting page number as your best estimate, and if truly uncertain, set to `null` rather than guessing.
6. Find each question's answer by matching content in the Ans document — never assume it's on a fixed offset from the question's own position. If a question's answer cannot be located in the Ans document, set `answerTextHtml` to `null` and add `"answerNotFound": true`.
7. `questionTextHtml` / `answerTextHtml`: full text, HTML-formatted (`<table>`, `<tr>`, `<td>` for any tabular/ledger-style content), preserving all numbers exactly as printed. Use `₹` for the rupee symbol.
8. Do not skip or summarize any question — every question and sub-part in the paper must appear as its own object (or nested within its parent question's sub-parts, your choice, as long as nothing is dropped).

---

## Prompt 1 of 5 — Jan 2025, Jan 2026

Files: `CAInter-AdvAcc-MTP-Jan2025-Set1-Q.md`, `CAInter-AdvAcc-MTP-Jan2025-Set1-Ans.md`, `CAInter-AdvAcc-MTP-Jan2025-Set2-Q.md`, `CAInter-AdvAcc-MTP-Jan2025-Set2-Ans.md`, `CAInter-AdvAcc-MTP-Jan2026-Set1-Q.md`, `CAInter-AdvAcc-MTP-Jan2026-Set1-Ans.md`, `CAInter-AdvAcc-MTP-Jan2026-Set2-Q.md`, `CAInter-AdvAcc-MTP-Jan2026-Set2-Ans.md`

> Extract every question and its answer from these 4 MTP papers (Jan 2025 Set 1, Jan 2025 Set 2, Jan 2026 Set 1, Jan 2026 Set 2) in `books/question-bank/Raw_PDF_Question_Bank_CA_Inter_Accounts/`, following the schema and instructions given above this prompt in `books/question-bank/metadata-index/phase1-mtp-prompts.md`. Output 4 JSON objects (one per paper).

---

## Prompt 2 of 5 — May 2023, May 2024

Files: `CAInter-AdvAcc-MTP-May2023-Set1-Q.md`, `CAInter-AdvAcc-MTP-May2023-Set1-Ans.md`, `CAInter-AdvAcc-MTP-May2023-Set2-Q.md`, `CAInter-AdvAcc-MTP-May2023-Set2-Ans.md`, `CAInter-AdvAcc-MTP-May2024-Set1-Q.md`, `CAInter-AdvAcc-MTP-May2024-Set1-Ans.md`, `CAInter-AdvAcc-MTP-May2024-Set2-Q.md`, `CAInter-AdvAcc-MTP-May2024-Set2-Ans.md`

> Extract every question and its answer from these 4 MTP papers (May 2023 Set 1, May 2023 Set 2, May 2024 Set 1, May 2024 Set 2) in `books/question-bank/Raw_PDF_Question_Bank_CA_Inter_Accounts/`, following the schema and instructions given above this prompt in `books/question-bank/metadata-index/phase1-mtp-prompts.md`. Output 4 JSON objects (one per paper).

---

## Prompt 3 of 5 — May 2025, May 2026

Files: `CAInter-AdvAcc-MTP-May2025-Set1-Q.md`, `CAInter-AdvAcc-MTP-May2025-Set1-Ans.md`, `CAInter-AdvAcc-MTP-May2025-Set2-Q.md`, `CAInter-AdvAcc-MTP-May2025-Set2-Ans.md`, `CAInter-AdvAcc-MTP-May2026-Set1-Q.md`, `CAInter-AdvAcc-MTP-May2026-Set1-Ans.md`, `CAInter-AdvAcc-MTP-May2026-Set2-Q.md`, `CAInter-AdvAcc-MTP-May2026-Set2-Ans.md`

> Extract every question and its answer from these 4 MTP papers (May 2025 Set 1, May 2025 Set 2, May 2026 Set 1, May 2026 Set 2) in `books/question-bank/Raw_PDF_Question_Bank_CA_Inter_Accounts/`, following the schema and instructions given above this prompt in `books/question-bank/metadata-index/phase1-mtp-prompts.md`. Output 4 JSON objects (one per paper).

---

## Prompt 4 of 5 — Nov 2023, Sep 2024

Files: `CAInter-AdvAcc-MTP-Nov2023-Set1-Q.md`, `CAInter-AdvAcc-MTP-Nov2023-Set1-Ans.md`, `CAInter-AdvAcc-MTP-Nov2023-Set2-Q.md`, `CAInter-AdvAcc-MTP-Nov2023-Set2-Ans.md`, `CAInter-AdvAcc-MTP-Sep2024-Set1-Q.md`, `CAInter-AdvAcc-MTP-Sep2024-Set1-Ans.md`, `CAInter-AdvAcc-MTP-Sep2024-Set2-Q.md`, `CAInter-AdvAcc-MTP-Sep2024-Set2-Ans.md`

> Extract every question and its answer from these 4 MTP papers (Nov 2023 Set 1, Nov 2023 Set 2, Sep 2024 Set 1, Sep 2024 Set 2) in `books/question-bank/Raw_PDF_Question_Bank_CA_Inter_Accounts/`, following the schema and instructions given above this prompt in `books/question-bank/metadata-index/phase1-mtp-prompts.md`. Output 4 JSON objects (one per paper).

---

## Prompt 5 of 5 — Sep 2025

Files: `CAInter-AdvAcc-MTP-Sep2025-Set1-Q.md`, `CAInter-AdvAcc-MTP-Sep2025-Set1-Ans.md`, `CAInter-AdvAcc-MTP-Sep2025-Set2-Q.md`, `CAInter-AdvAcc-MTP-Sep2025-Set2-Ans.md`

> Extract every question and its answer from these 2 MTP papers (Sep 2025 Set 1, Sep 2025 Set 2) in `books/question-bank/Raw_PDF_Question_Bank_CA_Inter_Accounts/`, following the schema and instructions given above this prompt in `books/question-bank/metadata-index/phase1-mtp-prompts.md`. Output 2 JSON objects (one per paper).

---

## After running all 5

Bring back all 18 JSON paper-objects (36 source files' worth) and I'll validate them (question-count sanity check against a quick line-count of each source file, spot-check a sample against the actual `.md`/`.pdf`) before merging into the master extracted-questions dataset.
