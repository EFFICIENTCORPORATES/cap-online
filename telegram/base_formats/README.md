# Exam Hub Base Formats

Share these files with faculty or content partners when requesting question data:

- `question_input_formats.pdf` — compact human-readable format guide.
- `question_input_formats.xlsx` — field-by-field MCQ and descriptive templates.
- `mcq_input_example.json` — one valid MCQ record in the bot input shape.
- `descriptive_input_example.json` — one valid descriptive record in the bot input shape.
- **`MCQ_PROMPT.md`** (added 2026-08-12) — a paste-ready system prompt for an AI model
  generating MCQ JSON directly from a source PDF. Built from real defects found and fixed
  in the CA Foundation Accounting/Business Economics batches (invalid JSON escaping,
  inconsistent answer-key formats, a copy-pasted chapter_slug left over from an unrelated
  example). Give it to the AI model alongside the source PDF and a real chapter list from
  `course_catalog` — see the file's own "What you must also give the AI" section. Every
  batch it produces still needs ingestion-script preflight checks before going live (see
  `telegram/tools/ingest_ca_foundation_accounting_economics_mcqs.py` for the pattern) —
  this prompt reduces how many of those checks fire, it doesn't replace them.

The production banks are not duplicated here. The examples are generated from:

- `telegram/assets/exam_bot/mcq_questions_extracted.json`
- `telegram/assets/exam_bot/book_questions_extracted.json`

Important rules:

- JSON root must be an array of records.
- Every MCQ `mcq_id` and descriptive `book_id` must be unique.
- Use exact catalog `unitcode` and `chapter_label` values.
- Keep question and answer tables as HTML inside the relevant HTML fields.
- Do not silently correct legal, accounting, tax or numeric source content; flag it for review.
- Faculty-owned content should include provenance and publication status fields.

Regenerate the artifacts after a source-schema change:

```text
python telegram/base_formats/generate_base_formats.py
```
