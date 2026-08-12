# Exam Hub Base Formats

Share these files with faculty or content partners when requesting question data:

- `question_input_formats.pdf` — compact human-readable format guide.
- `question_input_formats.xlsx` — field-by-field MCQ and descriptive templates.
- `mcq_input_example.json` — one valid MCQ record in the bot input shape.
- `descriptive_input_example.json` — one valid descriptive record in the bot input shape.

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
