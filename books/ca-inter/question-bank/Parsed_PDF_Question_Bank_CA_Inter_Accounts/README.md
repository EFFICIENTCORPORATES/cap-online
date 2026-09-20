# Parsed PDF Question Bank - CA Inter Advanced Accounting

Pilot parsed outputs from `../Raw_PDF_Question_Bank_CA_Inter_Accounts/`.

## Files

| Parsed File | Source Type | Source Files | Notes |
| --- | --- | --- | --- |
| `parsed-MTP-May2024-Set1.md` | MTP | `CAInter-AdvAcc-MTP-May2024-Set1-Q.md`, `CAInter-AdvAcc-MTP-May2024-Set1-Ans.md` | Combines question paper and answer paper. |
| `parsed-RTP-May2026.md` | RTP | `CAInter-AdvAcc-RTP-May2026-Q.md` | Splits announcements, questions, and suggested answers/hints from one source file. |
| `parsed-PYQ-Jan2026.md` | PYQ | `CAInter-AdvAcc-PYQ-Jan2026-Ans.md` | Uses suggested-answer file because the corresponding question markdown is blank. |

## Format Rule

The source remains Markdown. Complex accounting tables are represented as HTML `<table>` blocks inside Markdown so Balance Sheets, ledgers, journals, and working notes can keep ruled columns and stable alignment.

## Current Parser Limits

- Existing Markdown pipe-table blocks are converted to HTML tables.
- Standalone page-number lines are removed.
- Original wording is preserved as far as possible.
- Tables that were already broken into plain text by OCR may still need manual or smarter table reconstruction.
- Encoding artifacts from PDF conversion are lightly normalized but may need a deeper cleanup pass.
