# Phase 1 — PYQ Extraction Prompts (for Tool C, e.g. Blackbox AI)

Extracts every question + answer from all 7 PYQ attempts. **This is the trickiest of the
three extraction tasks** — unlike MTP/RTP, every PYQ attempt is structurally different.
Confirmed current state (2026-07-20) of every attempt, in the folder
`books/question-bank/Raw_PDF_Question_Bank_CA_Inter_Accounts/`:

| Attempt | Q document | Ans document |
|---|---|---|
| Jan 2025 | `PYQ-Jan2025-Q.pdf` exists, but its `.md` conversion is BLANK (2 bytes) — must read the PDF directly | `PYQ-Jan2025-Ans.md` has full content |
| Jan 2026 | `PYQ-Jan2026-Q.pdf` exists, `.md` BLANK — read PDF directly | `PYQ-Jan2026-Ans.md` has full content |
| May 2024 | `PYQ-May2024-Q.pdf` exists, `.md` BLANK — read PDF directly | `PYQ-May2024-Ans.md` has full content |
| May 2025 | **No Q document exists at all** for this attempt | `PYQ-May2025-Ans.md` has full content |
| May 2026 | `PYQ-May2026-Q.pdf` exists, `.md` BLANK — read PDF directly | **No Ans document exists at all** for this attempt |
| Sep 2024 | **No Q document exists at all** | `PYQ-Sep2024-Ans.md` has full content |
| Sep 2025 | **No Q document exists at all** | `PYQ-Sep2025-Ans.md` has full content |

**Do not assume this table is still accurate by the time you run this** — the source
folder is authoritative. If a `.md` file that this table says is blank turns out to have
content, or vice versa, trust what you actually see and note the discrepancy in your reply.

**Output schema:**
```json
{
  "sourceFile_Q": "CAInter-AdvAcc-PYQ-Jan2025-Q.pdf",
  "sourceFile_Ans": "CAInter-AdvAcc-PYQ-Jan2025-Ans.pdf",
  "attempt": "Jan 2025",
  "paperType": "PYQ",
  "set": null,
  "questions": [
    {
      "qNoInPaper": "5",
      "type": "MCQ-Direct | MCQ-Scenario | Descriptive",
      "printedMarks": 14,
      "pageQ": 3,
      "pageAns": 12,
      "questionTextHtml": "...",
      "answerTextHtml": "..."
    }
  ]
}
```
Where no Q document exists at all for an attempt, set `sourceFile_Q` to `null` and
`pageQ` to `null` for every question in that attempt — do NOT copy the Ans document's
filename/page into the Q fields, and do NOT skip extracting the questions just because
there's no separate Q document (the Ans document usually restates each question before
its solution — extract `questionTextHtml` from that restatement). Same logic in reverse
for the one attempt (May 2026) with no Ans document — set `sourceFile_Ans`/`pageAns`/
`answerTextHtml` to `null`, add `"answerNotFound": true`, but still extract the question.

**Instructions common to every prompt below:**
1. For blank-`.md` Q PDFs, read the PDF directly (the Read tool's `pages` parameter, chunks of ≤20 pages) — these are normal 20-40 page exam papers, fully readable.
2. `pageQ`/`pageAns` for PDF-read files: use the actual printed page number if visible on the page; for `.md`-read files, estimate via the `© The Institute of Chartered Accountants of India` footer count. Use `null` if genuinely uncertain rather than guessing.
3. `questionTextHtml`/`answerTextHtml`: full text, HTML-formatted, numbers exactly as printed, `₹` for rupee symbol.
4. Every question and sub-part must appear — don't skip or summarize.

---

## Prompt 1 of 3 — Jan 2025, Jan 2026 (blank-MD Q, working Ans)

Files: `CAInter-AdvAcc-PYQ-Jan2025-Q.pdf` (read directly, MD blank), `CAInter-AdvAcc-PYQ-Jan2025-Ans.md`, `CAInter-AdvAcc-PYQ-Jan2026-Q.pdf` (read directly, MD blank), `CAInter-AdvAcc-PYQ-Jan2026-Ans.md`

> Extract every question and its answer from the Jan 2025 and Jan 2026 PYQ attempts in `books/question-bank/Raw_PDF_Question_Bank_CA_Inter_Accounts/`, following the schema and instructions above this prompt in `books/question-bank/metadata-index/phase1-pyq-prompts.md`. Both Q documents have blank `.md` conversions — read the `.pdf` files directly in ≤20-page chunks. Output 2 JSON objects.

---

## Prompt 2 of 3 — May 2024 (blank-MD Q), May 2025 (no Q at all)

Files: `CAInter-AdvAcc-PYQ-May2024-Q.pdf` (read directly, MD blank), `CAInter-AdvAcc-PYQ-May2024-Ans.md`, `CAInter-AdvAcc-PYQ-May2025-Ans.md` (no separate Q document exists for this attempt)

> Extract every question and its answer from the May 2024 and May 2025 PYQ attempts in `books/question-bank/Raw_PDF_Question_Bank_CA_Inter_Accounts/`, following the schema and instructions above this prompt in `books/question-bank/metadata-index/phase1-pyq-prompts.md`. May 2024's Q document has a blank `.md` — read the `.pdf` directly. May 2025 has no Q document at all — extract questions from the restated question text inside the Ans document, and set `sourceFile_Q`/`pageQ` to `null` for all of them. Output 2 JSON objects.

---

## Prompt 3 of 3 — May 2026 (Q only, no Ans), Sep 2024 and Sep 2025 (no Q at all)

Files: `CAInter-AdvAcc-PYQ-May2026-Q.pdf` (read directly, MD blank; no Ans document exists for this attempt at all), `CAInter-AdvAcc-PYQ-Sep2024-Ans.md` (no separate Q document exists), `CAInter-AdvAcc-PYQ-Sep2025-Ans.md` (no separate Q document exists)

> Extract every question (and answer, where available) from the May 2026, Sep 2024, and Sep 2025 PYQ attempts in `books/question-bank/Raw_PDF_Question_Bank_CA_Inter_Accounts/`, following the schema and instructions above this prompt in `books/question-bank/metadata-index/phase1-pyq-prompts.md`. May 2026 has a blank-`.md` Q PDF (read directly) but genuinely no Ans document anywhere — extract the questions with `sourceFile_Ans`/`pageAns`/`answerTextHtml` all `null` and `"answerNotFound": true`, do not search for or invent an answer. Sep 2024 and Sep 2025 have no separate Q document — extract questions from the restated question text inside each Ans document, with `sourceFile_Q`/`pageQ` set to `null`. Output 3 JSON objects.

---

## After running all 3

Bring back all 7 JSON attempt-objects and I'll validate them (paying particular attention to the no-Q and no-Ans attempts, to confirm nothing was silently invented) before merging into the master extracted-questions dataset.
