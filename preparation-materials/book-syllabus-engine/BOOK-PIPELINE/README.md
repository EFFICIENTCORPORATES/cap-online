# BOOK-PIPELINE — How to Run `extract_json_from_html.py`

## What This Script Does

Converts a verified ICAI Base HTML chapter file into a structured JSON file.  
Block IDs are automatically derived from the **Base Syllabus JSON** (not invented by AI).  
Each block gets a sequence ID like `M2-C5-U1-T1.1.B2`, plus teaching sequence, marks history, and other syllabus context pulled directly from the base JSON.

---

## Prerequisites

Python 3.10 or higher. Install the one dependency:

```
pip install beautifulsoup4
```

---

## Files You Need

| File | Description |
|---|---|
| `0-ca-inter-adv-accounts-subtopics-marks-weightage.json` | Base Syllabus JSON — locked, never edit |
| `1-AS2_Inventories.html` (or any chapter HTML) | Verified ICAI Base HTML — no `data-sequence-id` in it |
| `extract_json_from_html.py` | This script |

---

## Basic Command

```
python extract_json_from_html.py <input.html> <output.json> --base-json <base.json> --chapter-id <chapter-id>
```

---

## Full Command with All Options

```
python extract_json_from_html.py "1-AS2_Inventories.html" "2-m1_c5_u1_as2_by_ai.json" ^
  --base-json "0-ca-inter-adv-accounts-subtopics-marks-weightage.json" ^
  --chapter-id "M2-C5-U1" ^
  --verified-by "Reviewer Name" ^
  --verified-on "2026-05-20"
```

> **Windows note:** Use `^` for line continuation in Command Prompt. In PowerShell use a backtick `` ` `` instead.

---

## Chapter ID Reference

Use the `unique_chapter_id` from the Base Syllabus JSON. Common ones:

| Chapter | `--chapter-id` |
|---|---|
| AS 2 — Valuation of Inventory | `M2-C5-U1` |
| AS 10 — Property, Plant and Equipment | `M2-C5-U2` |
| AS 16 — Borrowing Costs | `M2-C5-U4` |
| AS 19 — Leases | `M2-C5-U5` |
| AS 26 — Intangible Assets | `M2-C5-U6` |
| AS 28 — Impairment of Assets | `M2-C5-U7` |
| Introduction to AS | `M1-C1-U0` |
| Framework | `M1-C2-U0` |
| Applicability of AS | `M1-C3-U0` |

For any other chapter, open the Base Syllabus JSON and look up the `unique_chapter_id` field.

---

## What Gets Generated

### Sequence IDs per block

| Block location | Sequence ID format | Example |
|---|---|---|
| Chapter header area | `{chapter_id}-T.B{n}` | `M2-C5-U1-T.B1` |
| Topic section | `{chapter_id}-T{topic_no}.B{n}` | `M2-C5-U1-T1.3.B2` |
| Illustration solution | `{parent_id}.SOL` | `M2-C5-U1-T1.15.B4.SOL` |

Block counter resets to 1 at the start of each new topic.

### Per-block syllabus fields stamped on every block

```json
"syllabus_topic_id": "M2-C5-U1-T1.3",
"syllabus_topics_id_name": "M2-C5-U1-T1.3-Measurement-of-Inventories",
"syllabus_topic_sequence": 3,
"syllabus_page_ref": "5.4",
"syllabus_icai_unit_label": "Unit 1"
```

### Top-level `syllabus_meta` in the output JSON

```json
"syllabus_meta": {
  "unique_chapter_id": "M2-C5-U1",
  "teaching_sequence": "4",
  "icai_chapter_ref": "5.1",
  "chapter_name_icai": "Accounting Standard 2 Valuation of Inventory",
  "chapter_name_short": "AS-2",
  "marks_distinct_attempt_count": 9,
  "sn_alternate_order": 4,
  "marks_by_attempt": { "May-2019": "5+1", "Nov-2019": 5, ... }
}
```

---

## How the Script Matches Topics

When it encounters a `section-heading` block, it reads the heading text and extracts the leading number:

| Heading text in HTML | Extracted `topic_no` | Matched base JSON entry |
|---|---|---|
| `1.1 INTRODUCTION` | `1.1` | `M2-C5-U1-T1.1` |
| `1.10 COST FORMULA` | `1.10` | `M2-C5-U1-T1.10` |
| `TEST YOUR KNOWLEDGE` | *(no number)* | stays under last matched topic |
| `ANSWERS/SOLUTION` | *(no number)* | stays under last matched topic |

Headings with no topic number (like "TEST Your Knowledge", "MCQ", "Answers") stay under the last matched topic without raising an error.

---

## Warnings to Watch For

After the script runs, check stderr output for:

```
WARNING — N heading(s) had topic numbers not found in the base JSON
```

This means a heading like `2.16 SOME NEW TOPIC` appeared in the HTML but `2.16` is not in the base JSON for that chapter. You need to either:
- Add the missing topic to the base JSON, or
- Correct the heading number in the HTML

---

## Backward Compatibility

If you run the script **without** `--base-json` and `--chapter-id`, it falls back to reading `data-sequence-id` attributes from the HTML (the old behaviour). This means old HTML files with sequence IDs still work.

```
python extract_json_from_html.py "old_chapter.html" "output.json"
```

---

## Step-by-Step for Each New Chapter

1. AI generates the HTML from the PDF (no `data-sequence-id` in the output)
2. Human reviewer verifies HTML against the PDF (twin check)
3. Run this script with the correct `--chapter-id`
4. Check stderr — zero duplicates, zero unmatched headings = clean
5. Output JSON is ready for the merge engine

---

## Arguments Reference

| Argument | Required | Description |
|---|---|---|
| `input.html` | Yes | Path to the verified ICAI Base HTML file |
| `output.json` | Yes | Path to write the generated JSON |
| `--base-json` | Recommended | Path to the Base Syllabus JSON |
| `--chapter-id` | Recommended | `unique_chapter_id` for this chapter (e.g. `M2-C5-U1`) |
| `--verified-by` | Optional | Name of the human reviewer |
| `--verified-on` | Optional | Date of verification (YYYY-MM-DD) |
| `--generated-on` | Optional | Override the `generated_on` date in output |
| `--indent` | Optional | JSON indentation spaces (default: 2) |
