# Syllabus Intelligence Engine — Complete Architecture Document
### CA Inter Advanced Accounting | efficientcorporates.in
### Author: Pranav Sir | Version: 1.0 | Date: May 2026

---

## 1. Project Overview

The **Syllabus Intelligence Engine** is a structured, AI-assisted pipeline that converts ICAI CA Inter Advanced Accounting Study Material (Modules 1, 2, 3) into a semantically tagged, queryable, multi-view digital knowledge base.

The final output is a rendered HTML book available in three views:
- **Student View** — clean study material
- **Teacher View** — includes production notes, internal flags, teaching cues
- **Master View** — everything visible, used for authoring and review

The system is built on a layered JSON architecture derived from AI-assisted HTML extraction, with teacher customisations applied via a migration-style instruction layer.

---

## 2. Core Design Principles

1. **HTML is the human-verifiable source of truth** — never edit JSON manually
2. **JSON is always machine-generated** from HTML via Python scripts
3. **ICAI Base JSON is locked** after human verification — never modified thereafter
4. **Teacher customisations are a separate layer** — never pollute the base
5. **Extraction is AI-assisted** — not purely deterministic, human review is mandatory
6. **Versioning is non-negotiable** — every base file carries ICAI version and exam applicability
7. **Pilot on Chapter 1 first** — validate full pipeline before scaling

---

## 3. Scope of Material

| Module | Chapters | Key Content |
|--------|----------|-------------|
| Module 1 | Ch 1–4 (Ch 4 has 7 units) | Intro to AS, Framework, Applicability, Presentation Standards |
| Module 2 | Ch 5–10 | Assets, Liabilities, Revenue, Other, Consolidated AS |
| Module 3 | Ch 11–15 | Company Accounts, Buyback, Amalgamation, Reconstruction, Branches |

**Additional Sources:**
- ICAI RTPs (Revision Test Papers)
- ICAI MTPs (Mock Test Papers)
- Teacher's own custom content

---

## 4. Complete Pipeline — Step by Step

```
STEP 1: AI-Assisted PDF → HTML Extraction
STEP 2: Human Verification (Twin Check)
STEP 3: HTML → JSON (Python)
STEP 4: RTP/MTP Same Pipeline + Placement Keys
STEP 5: Teacher Customisation JSON
STEP 6: Merge Engine (Python)
STEP 7: CSS Class Registry Validation
STEP 8: Rendering Engine → Final HTML
```

---

## 5. Step 1 — AI-Assisted PDF to HTML Extraction

### Who Does This
**AI (Claude / GPT-4o with vision)** — primary extraction agent  
**Python (pdfplumber)** — pre-processing, page segmentation, text layer extraction  
**Human** — correction and verification post AI output

### Why AI and Not Pure Python
ICAI PDFs contain:
- Image-embedded diagrams and flowcharts
- Image-embedded tables (especially in older modules)
- Mathematical formulas rendered as images
- Multi-column layouts that merge incorrectly in raw text extraction
- Footnotes appearing in wrong positions

Pure pdfplumber extraction will miss all image-based content. AI with vision capability can read the PDF visually and reconstruct the HTML semantically.

### Process

```
ICAI PDF
  → pdfplumber: extract raw text layer, identify page structure
  → Page images generated (one PNG per page) for AI vision
  → AI prompt sent with: raw text + page image + schema instructions
  → AI outputs: structured HTML per page/section
  → Pages assembled into chapter-level HTML file
  → extraction-flag placeholders inserted where AI is uncertain
```

### Extraction Flag Placeholder
Wherever AI cannot confidently extract (image-only diagrams, complex merged tables), it inserts:

```html
<div class="extraction-flag"
     data-reason="image-based-diagram"
     data-page="47"
     data-description="Standards Setting Process Flowchart">
  [MANUAL ENTRY REQUIRED — See PDF Page 47]
</div>
```

Human reviewer then fills these in during Step 2.

---

### AI Extraction Prompt

The following prompt is to be used when sending each chapter section to the AI for HTML conversion.

---

```
SYSTEM PROMPT — ICAI PDF TO HTML EXTRACTION

You are converting a section of the ICAI CA Inter Advanced Accounting Study 
Material from PDF to structured semantic HTML.

You will receive:
1. Raw extracted text from pdfplumber for this section
2. A page image (PNG) of the same section from the original PDF

Your task is to produce a clean, structured HTML file that is an EXACT REPLICA 
of the original PDF content. The HTML and the PDF must be twins — identical in 
content, sequence, and structure.

STRICT RULES:
- Do NOT paraphrase, summarise, or reword any content
- Do NOT add any content not present in the original PDF
- Do NOT remove any content present in the original PDF
- Preserve ALL numbering — section numbers, illustration numbers, example 
  numbers, MCQ numbers, answer numbers
- Preserve ALL formatting cues — bold terms, italics, underlines where visible
- Every block of content must carry a class attribute identifying its type

HTML CLASSES TO USE:
- class="learning-outcomes" — the learning outcomes block at chapter/unit start
- class="chapter-overview" — the overview diagram or table at chapter start
- class="theory" — narrative explanation paragraphs
- class="definition" — formally defined terms (e.g. "Control means...")
- class="concept-note" — shorter clarifying inserts, notes within theory
- class="standard-provision" — direct provision text from the AS
- class="exception" — negative conditions, what is excluded
- class="comparison" — side by side comparisons
- class="formula" — mathematical expressions, ratio formulas
- class="flowchart-text" — text description of a flowchart or diagram
- class="illustration" — named Illustration blocks with solutions
- class="example" — shorter Example blocks
- class="solution" — solution block inside illustration or example
- class="working-note" — working note inside a solution
- class="journal-entry" — journal entry inside a solution
- class="accounting-statement" — P&L, Balance Sheet, Cash Flow inside solution
- class="mcq" — each MCQ block
- class="mcq-option" — individual option (a, b, c, d)
- class="mcq-answer" — correct answer line
- class="theoretical-question" — descriptive question in Test Your Knowledge
- class="scenario-question" — scenario based question
- class="case-scenario" — longer case based question
- class="answer-hint" — answer or hint block

DATA ATTRIBUTES TO ADD ON EVERY BLOCK:
- data-sequence-id — use format M[x].C[x].U[x].S[x].B[x] 
  (Module.Chapter.Unit.Section.Block — increment Block for each block in sequence)
- data-block-type — same as class name
- data-visibility — set to "both" for all blocks (teacher will change later)

FOR TABLES:
- Use standard HTML <table>, <thead>, <tbody>, <tr>, <th>, <td> tags
- Add class="data-table" for reference/data tables
- Add class="accounting-statement-table" for P&L, Balance Sheet, Cash Flow tables
- Preserve all column headers exactly
- Preserve all row data exactly

FOR DIAGRAMS AND FLOWCHARTS:
- If the diagram is image-only and you cannot reconstruct it as text/HTML:
  Insert: <div class="extraction-flag" data-reason="image-based-diagram" 
  data-page="[page number]" data-description="[brief description of diagram]">
  [MANUAL ENTRY REQUIRED — See PDF Page [x]]</div>
- If the diagram has text labels you can read, reconstruct it using nested 
  divs with class="flowchart-text" and describe the flow in structured text

FOR MATHEMATICAL FORMULAS:
- If formula is image-only: use extraction-flag as above
- If formula text is readable: wrap in <div class="formula"> and use 
  plain text or simple HTML to represent it

SEQUENCE ID FORMAT:
M1 = Module 1, M2 = Module 2, M3 = Module 3
C1 = Chapter 1, C2 = Chapter 2 etc.
U0 = no unit (chapter level), U1 = Unit 1 etc.
S1 = Section 1 etc.
B1 = Block 1, B2 = Block 2 (increment for every distinct content block)

Example: data-sequence-id="M1.C4.U2.S3.B5"

OUTPUT FORMAT:
- Pure HTML only
- No CSS, no inline styles, no JavaScript
- No markdown formatting
- Begin with: <div class="chapter" data-module="1" data-chapter="4" 
  data-unit="2" data-icai-version="July-2024" data-exam="May-2026">
- End with: </div>
- Every content block on its own clearly tagged element
- No wrapping everything in a single <p> tag

VERIFICATION CHECKLIST (add as HTML comment at end of file):
<!-- EXTRACTION CHECKLIST
  Section headings: [YES/PARTIAL/NO]
  Definitions: [YES/PARTIAL/NO]  
  Illustrations: [YES/PARTIAL/NO]
  Tables: [YES/PARTIAL/NO]
  MCQs with options and answers: [YES/PARTIAL/NO]
  Diagrams flagged for manual entry: [YES/NO/NONE PRESENT]
  Extraction flags inserted: [count]
-->
```

---

## 6. Step 2 — Human Verification (Twin Check)

### Who Does This
**Independent reviewer** (not the AI, not Pranav Sir)  
Ideally a CA student or junior who knows the material well enough to spot errors

### Objective
ICAI PDF and the HTML file must be **exact twins** in content, sequence, and structure.

### Verification Checklist Per Chapter

```
CHAPTER VERIFICATION CHECKLIST

Chapter: _______________  Module: ___  Verified by: _______________  Date: ___

STRUCTURE
[ ] All section headings present and correctly numbered
[ ] All unit headings present (for Chapter 4 type multi-unit chapters)
[ ] Learning outcomes block present at chapter/unit start
[ ] Chapter overview block present

CONTENT BLOCKS
[ ] All theory paragraphs present — no lines missing, no lines added
[ ] All definitions present and worded exactly as per ICAI
[ ] All concept notes and standard provisions present
[ ] All exceptions and negative conditions present
[ ] All formulas present (or flagged for manual entry)

WORKED EXAMPLES
[ ] All Illustrations present with correct numbers (Illustration 1, 2, 3...)
[ ] All Examples present with correct numbers (Example 1, 2, 3...)
[ ] All solutions present and complete
[ ] All working notes present
[ ] All journal entries present
[ ] All accounting statements (P&L, BS, CFS) present with correct figures

TABLES
[ ] All tables present
[ ] All column headers correct
[ ] All row data correct — spot check at minimum 20% of rows

ASSESSMENT BLOCKS
[ ] All MCQs present with correct question text
[ ] All MCQ options (a, b, c, d) present and correct
[ ] All MCQ answers present
[ ] All theoretical questions present
[ ] All scenario questions present
[ ] All answer hints present

EXTRACTION FLAGS
[ ] All extraction-flag placeholders reviewed
[ ] Manual content entered for all flags
[ ] All flags removed after content entry

FINAL
[ ] HTML renders correctly in browser — no broken tags
[ ] Sequence IDs are in correct order — no gaps, no duplicates
[ ] data-icai-version and data-exam attributes present on root div
[ ] Extraction checklist comment at end of file updated to all YES
```

### What Reviewer Can Edit
- Fix typos in extracted text
- Fill in extraction-flag placeholders with correct content
- Fix broken table structures
- Correct sequence IDs if out of order
- **Cannot** add new content not in ICAI PDF
- **Cannot** remove content present in ICAI PDF

Once verified — the HTML file is **locked** as the ICAI Base HTML.

---

## 7. Step 3 — HTML to JSON (Python)

### Who Does This
**Python script — `extract_json_from_html.py`**

### What It Does
Parses the verified ICAI Base HTML using BeautifulSoup and generates a structured JSON file following the defined schema.

### No Manual JSON Editing — Ever
Once the Python script generates the JSON, it is never manually edited. If a correction is needed, it goes back to the HTML file, correction is made there, and JSON is regenerated.

### JSON Schema — ICAI Base JSON

```json
{
  "meta": {
    "module": 1,
    "chapter": 4,
    "unit": 2,
    "title": "Accounting Standard 3 — Cash Flow Statement",
    "icai_version": "July-2024",
    "exam_applicable": "May-2026",
    "generated_on": "2026-05-28",
    "source_html": "m1_c4_u2_as3.html",
    "verified_by": "reviewer_name",
    "verified_on": "2026-05-20"
  },
  "blocks": [
    {
      "sequence_id": "M1.C4.U2.S1.B1",
      "block_type": "learning-outcomes",
      "visibility": "both",
      "content": [
        "What are Cash and Cash Equivalents",
        "Presentation of a Cash Flow Statement"
      ]
    },
    {
      "sequence_id": "M1.C4.U2.S2.B1",
      "block_type": "theory",
      "visibility": "both",
      "heading": "Introduction",
      "content": "This Standard is mandatory for Non-SMCs..."
    },
    {
      "sequence_id": "M1.C4.U2.S3.B1",
      "block_type": "definition",
      "visibility": "both",
      "term": "Cash and Cash Equivalents",
      "as_reference": "AS-3",
      "content": "Cash in hand and deposits repayable on demand..."
    },
    {
      "sequence_id": "M1.C4.U2.S4.B1",
      "block_type": "table",
      "visibility": "both",
      "table_class": "data-table",
      "caption": "List of Accounting Standards",
      "headers": ["AS No.", "AS Title", "Date of Applicability"],
      "rows": [
        ["1", "Disclosure of Accounting Policies", "01/04/1993"],
        ["2", "Valuation of Inventories (Revised)", "01/04/1999"]
      ]
    },
    {
      "sequence_id": "M1.C4.U2.S5.B1",
      "block_type": "illustration",
      "visibility": "both",
      "illustration_number": "Illustration 1",
      "question_text": "Classify the following activities...",
      "given_directly": [],
      "given_indirectly": [],
      "asked": [],
      "solution": {
        "sequence_id": "M1.C4.U2.S5.B1.SOL",
        "block_type": "solution",
        "content": "Operating Activities: c, e, f...",
        "accounting_statements": [],
        "working_notes": [],
        "journal_entries": []
      },
      "practical_solution_summary": {
        "given_directly": [],
        "given_indirectly": [],
        "what_was_asked": "",
        "approach_used": "",
        "formula_used": "",
        "common_mistakes": [],
        "exam_watchout": ""
      }
    },
    {
      "sequence_id": "M1.C4.U2.S6.B1",
      "block_type": "mcq",
      "visibility": "both",
      "mcq_number": 1,
      "question_text": "Crown Ltd. wants to prepare its cash flow statement...",
      "options": {
        "a": "Nil",
        "b": "8,000",
        "c": "68,000",
        "d": "60,000"
      },
      "correct_answer": "a",
      "mcq_solution_explanation": "",
      "one_day_revision": false
    }
  ]
}
```

### Table Representation — Accounting Statements

```json
{
  "sequence_id": "M1.C2.ILL1.SOL.T1",
  "block_type": "accounting-statement",
  "statement_type": "profit_and_loss",
  "entity": "Trader",
  "period": "Year ended 31st March 20X2",
  "columns": [
    "Particulars",
    "Case (i) Going Concern ₹",
    "Case (ii) Not Going Concern ₹"
  ],
  "rows": [
    ["To Opening Stock", "30,000", "30,000"],
    ["To Purchases", "4,00,000", "4,00,000"],
    ["By Sales", "4,50,000", "4,50,000"]
  ]
}
```

---

## 8. Step 4 — RTP / MTP Pipeline

### Same Pipeline as ICAI Base

```
RTP/MTP PDF
  → AI-assisted extraction (same prompt, same rules)
  → Human verification (twin check)
  → Locked RTP/MTP HTML
  → Python → RTP/MTP JSON
```

### Additional Keys in RTP/MTP JSON

Each question block in the RTP/MTP JSON gets two additional keys:

```json
{
  "sequence_id": "RTP.Nov2025.Q3",
  "block_type": "mcq",
  "question_text": "...",
  "include_in_teachers_book": true,
  "placement_sequence_id": "M1.C4.U2.S6",
  "placement_position": "after",
  "source": "RTP_Nov_2025",
  "visibility": "both"
}
```

- `include_in_teachers_book` — true or false
- `placement_sequence_id` — exact block in ICAI JSON after/before which this goes
- `placement_position` — "after" or "before"
- `source` — identifies which RTP/MTP this came from

---

## 9. Step 5 — Teacher Customisation JSON

### Who Authors This
**Pranav Sir** — directly

### What This Is
A migration-style instruction file. Every entry references a sequence ID from the ICAI Base JSON and specifies what operation to perform.

### Supported Operations

```json
"operation": "keep_as_is"
"operation": "replace"
"operation": "remove"
"operation": "add_new"
"operation": "flag_revision"
"operation": "set_visibility"
```

### Teacher JSON Schema

```json
{
  "meta": {
    "module": 1,
    "chapter": 4,
    "unit": 2,
    "authored_by": "Pranav Sir",
    "version": "1.0",
    "date": "2026-05-28",
    "references_icai_version": "July-2024"
  },
  "instructions": [
    {
      "ref_sequence_id": "M1.C4.U2.S2.B1",
      "operation": "keep_as_is"
    },
    {
      "ref_sequence_id": "M1.C4.U2.S3.B1",
      "operation": "replace",
      "new_content": "Pranav Sir's enhanced explanation of Cash and Cash Equivalents..."
    },
    {
      "ref_sequence_id": "M1.C4.U2.S5.B1",
      "operation": "keep_as_is",
      "practical_solution_summary": {
        "given_directly": ["Sales figures", "PPE book values"],
        "given_indirectly": ["Depreciation derived from WDV difference"],
        "what_was_asked": "Prepare Cash Flow Statement using Indirect Method",
        "approach_used": "Indirect Method — start from Net Profit, adjust non-cash items",
        "formula_used": "Operating CF = Net Profit + Depreciation + Working Capital Changes",
        "common_mistakes": [
          "Students forget to add back depreciation",
          "Tax paid treated as financing instead of operating"
        ],
        "exam_watchout": "Dividend paid is always financing — do not put under operating"
      },
      "pranav_sir_production_notes": "Stress the indirect method format — 80% of exam questions use indirect. Do a live board solve for this illustration."
    },
    {
      "ref_sequence_id": "M1.C4.U2.S6.B1",
      "operation": "keep_as_is",
      "mcq_solution_explanation": "Gain on disposal is investing cash flow — it goes under investing, not operating. The operating activities section gets zero from this transaction.",
      "one_day_revision": true
    },
    {
      "ref_sequence_id": "M1.C4.U2.S3",
      "operation": "add_new",
      "position": "after",
      "new_block": {
        "block_type": "concept-note",
        "visibility": "both",
        "content": "Pranav Sir's additional concept note on bank overdraft treatment..."
      }
    },
    {
      "ref_sequence_id": "M1.C4.U2.S4.B1",
      "operation": "set_visibility",
      "visibility": "teacher"
    },
    {
      "ref_sequence_id": "M1.C4.U2.S2.B1",
      "operation": "flag_revision",
      "one_day_revision": true
    }
  ],
  "global_additions": [
    {
      "block_type": "quotation",
      "placement": "header",
      "content": "Success is the sum of small efforts repeated day in and day out.",
      "visibility": "both"
    }
  ]
}
```

---

## 10. Step 6 — Merge Engine

### Who Does This
**Python script — `merge_engine.py`**

### What It Does

```
Inputs:
  - ICAI Base JSON (locked)
  - RTP/MTP JSONs (locked)
  - Teacher JSON

Process:
  1. Load ICAI Base JSON — this is the ordered sequence
  2. For each block in ICAI Base JSON:
     a. Check Teacher JSON for instruction referencing this sequence_id
     b. Apply operation: keep / replace / remove
     c. If keep — add teacher enrichments (summary, notes, explanation, flags)
     d. If replace — substitute block content
     e. If remove — skip block
  3. After each block — check for add_new instructions at this position
  4. After all ICAI blocks — integrate RTP/MTP blocks at their placement positions
  5. Apply global additions (header/footer quotations etc.)
  6. Output: Book JSON

Output:
  Book JSON (versioned, timestamped)
```

### Validation Before Output

Merge engine validates:
- All `ref_sequence_id` in Teacher JSON exist in ICAI Base JSON
- All `placement_sequence_id` in RTP/MTP JSON exist in ICAI Base JSON
- All class names used exist in CSS Class Registry JSON
- No duplicate sequence IDs in output
- All blocks have valid visibility flag (both / teacher / student)

Any validation failure → merge aborts → error log generated → human fixes Teacher JSON

---

## 11. Step 7 — CSS Class Registry & Master CSS

### CSS Class Registry JSON

Single source of truth for all valid class names. Both content JSONs and CSS file reference this.

```json
{
  "registry_version": "1.0",
  "classes": [
    "learning-outcomes",
    "chapter-overview",
    "theory",
    "definition",
    "concept-note",
    "standard-provision",
    "exception",
    "comparison",
    "formula",
    "flowchart-text",
    "illustration",
    "example",
    "solution",
    "working-note",
    "journal-entry",
    "accounting-statement",
    "accounting-statement-table",
    "data-table",
    "mcq",
    "mcq-option",
    "mcq-answer",
    "mcq-solution-explanation",
    "theoretical-question",
    "scenario-question",
    "case-scenario",
    "answer-hint",
    "practical-solution-summary",
    "one-day-revision",
    "pranav-sir-production-notes",
    "quotation",
    "page-header",
    "page-footer",
    "extraction-flag",
    "as-reference",
    "applicability-note",
    "amendment-note",
    "statutory-ref",
    "cross-ref",
    "exam-relevance"
  ]
}
```

### Master CSS Defines
- Font family, size, weight per class
- Background colours (one-day-revision gets distinct highlight colour)
- Border styles (illustration gets boxed, theory is plain)
- Spacing and padding per block type
- Print-safe styles for PDF export if needed
- Three view modes via CSS custom properties or body class toggling

---

## 12. Step 8 — Rendering Engine

### Who Does This
**Python script — `render_html.py`** using Jinja2 templating

### Three View Modes

```python
python render_html.py --input book_m1_c4_u2.json --view student
python render_html.py --input book_m1_c4_u2.json --view teacher
python render_html.py --input book_m1_c4_u2.json --view both
```

### Rendering Logic

```python
for block in book_json["blocks"]:
    if view_mode == "student" and block["visibility"] == "teacher":
        skip
    elif view_mode == "teacher" and block["visibility"] == "student":
        skip
    else:
        render block to HTML using Jinja2 template
        apply CSS class from block_type
        wrap in appropriate HTML element
```

### Jinja2 Template Structure

```html
<!DOCTYPE html>
<html>
<head>
  <link rel="stylesheet" href="master.css">
  <title>{{ meta.title }}</title>
</head>
<body class="view-{{ view_mode }}">

  <header class="page-header">
    <div class="quotation">{{ header_quotation }}</div>
    <div class="chapter-title">{{ meta.title }}</div>
    <div class="branding">efficientcorporates.in</div>
  </header>

  {% for block in blocks %}
    {% include "templates/" + block.block_type + ".html" %}
  {% endfor %}

  <footer class="page-footer">
    <div class="quotation">{{ footer_quotation }}</div>
    <div class="page-info">Module {{ meta.module }} | Chapter {{ meta.chapter }}</div>
    <div class="branding">efficientcorporates.in | Pranav Sir</div>
  </footer>

</body>
</html>
```

Each block type has its own Jinja2 sub-template — `templates/theory.html`, `templates/mcq.html`, `templates/illustration.html` etc.

---

## 13. File Structure

```
/syllabus-intelligence-engine
│
├── /source-pdfs
│   ├── /icai
│   │   ├── icai_m1_july2024.pdf
│   │   ├── icai_m2_july2024.pdf
│   │   └── icai_m3_july2024.pdf
│   ├── /rtp
│   │   ├── rtp_nov2025.pdf
│   │   └── rtp_may2026.pdf
│   └── /mtp
│       ├── mtp1_2026.pdf
│       └── mtp2_2026.pdf
│
├── /icai-base-html                    ← AI extracted, human verified, locked
│   ├── /module-1
│   │   ├── m1_c1.html
│   │   ├── m1_c2.html
│   │   ├── m1_c3.html
│   │   ├── m1_c4_u1_as1.html
│   │   ├── m1_c4_u2_as3.html
│   │   └── ...
│   ├── /module-2
│   └── /module-3
│
├── /icai-base-json                    ← Auto-generated from HTML, never touch
│   ├── /module-1
│   │   ├── m1_c1.json
│   │   └── ...
│   └── ...
│
├── /rtp-mtp-html                      ← AI extracted, human verified
│   ├── rtp_nov2025.html
│   └── ...
│
├── /rtp-mtp-json                      ← Auto-generated, with placement keys
│   ├── rtp_nov2025.json
│   └── ...
│
├── /teacher-json                      ← Pranav Sir authors these
│   ├── /module-1
│   │   ├── teacher_m1_c1.json
│   │   └── ...
│   └── ...
│
├── /book-json                         ← Merge engine output, versioned
│   ├── /module-1
│   │   ├── book_m1_c1_v1.0.json
│   │   └── ...
│   └── ...
│
├── /rendered-html                     ← Final output
│   ├── /student
│   ├── /teacher
│   └── /master
│
├── /css
│   ├── master.css
│   └── class_registry.json
│
├── /templates                         ← Jinja2 block templates
│   ├── theory.html
│   ├── mcq.html
│   ├── illustration.html
│   └── ...
│
├── /scripts
│   ├── extract_html_from_pdf.py       ← pdfplumber pre-processing
│   ├── extract_json_from_html.py      ← HTML → JSON
│   ├── merge_engine.py                ← Merge ICAI + RTP/MTP + Teacher
│   ├── render_html.py                 ← JSON + CSS → Final HTML
│   ├── validate_json.py               ← Validate against class registry
│   └── generate_master_index.py       ← Master index across all chapters
│
├── /prompts
│   └── icai_pdf_to_html_prompt.txt    ← The AI extraction prompt (versioned)
│
├── /verification-checklists
│   └── chapter_verification_template.md
│
├── master_index.json                  ← Auto-generated index of entire book
└── README.md
```

---

## 14. Technology Stack Summary

| Task | Tool / Language | Who |
|------|----------------|-----|
| PDF page image generation | Python — pdf2image | Automated |
| Raw text extraction | Python — pdfplumber | Automated |
| PDF to HTML conversion | AI (Claude / GPT-4o with vision) + prompt | AI |
| HTML correction and verification | Human reviewer | Manual |
| HTML to JSON | Python — BeautifulSoup | Automated |
| Teacher JSON authoring | Pranav Sir directly | Manual |
| RTP/MTP placement tagging | Pranav Sir or assistant | Manual |
| Merge engine | Python | Automated |
| CSS class registry validation | Python | Automated |
| HTML rendering | Python — Jinja2 | Automated |
| Version control | Git | Automated |
| Master index generation | Python | Automated |

---

## 15. Versioning Strategy

### ICAI Base HTML and JSON

```
data-icai-version="July-2024"
data-exam="May-2026"
```

When ICAI releases updated material:
- New HTML file created with new version tag
- Old file retained
- Diff script flags all changed blocks
- Teacher JSON checked against diff — instructions referencing changed blocks flagged for review
- New Book JSON generated only after Teacher JSON is updated

### Book JSON Versioning

```
book_m1_c1_v1.0.json     ← initial
book_m1_c1_v1.1.json     ← after teacher additions
book_m1_c1_v2.0.json     ← after ICAI material update
```

---

## 16. Pilot Plan — Chapter 1 First

Before scaling to all 15 chapters, run the complete pipeline on **Chapter 1 — Introduction to Accounting Standards** only.

### Pilot Checklist

```
[ ] Extract Chapter 1 HTML using AI prompt
[ ] Human verification — twin check against ICAI PDF
[ ] Run extract_json_from_html.py → verify JSON structure
[ ] Author teacher_m1_c1.json with sample instructions
[ ] Run merge_engine.py → verify book JSON
[ ] Define master.css for all block types
[ ] Run render_html.py in all three view modes
[ ] Visual check of rendered HTML against ICAI PDF
[ ] Fix any pipeline issues
[ ] Document all edge cases found
[ ] Sign off before scaling
```

---

## 17. Key Risks and Mitigations

| Risk | Mitigation |
|------|-----------|
| AI extraction misses image content | extraction-flag placeholders + human correction |
| Sequence IDs inconsistent across files | Merge engine validates all IDs before output |
| Teacher JSON references wrong sequence ID | Validation script aborts merge with error log |
| ICAI updates material mid-project | Versioning system + diff script + re-verification |
| HTML drift from ICAI original over time | HTML locked after verification, diff log on every edit |
| CSS class name mismatch | Class registry JSON enforced at merge validation |
| Reviewer misses errors in twin check | Structured verification checklist per chapter |

---

## 18. One-Day Revision Strategy

Any block flagged with `"one_day_revision": true` in Book JSON:
- Renders with a distinct visual style in HTML (colour highlight, icon, border)
- Is queryable from master_index.json to generate a standalone revision document
- Can be rendered as a separate `revision_only.html` per chapter using:

```python
python render_html.py --input book_m1_c4_u2.json --view student --filter revision_only
```

This gives students a last-day study sheet per chapter automatically.

---

## 19. Quotations System

Each chapter HTML has header and footer quotation slots. Quotations are maintained in:

```json
/css/quotations.json
```

Structure:
```json
{
  "quotations": [
    {
      "id": "Q001",
      "text": "Success is the sum of small efforts repeated day in and day out.",
      "author": "Robert Collier",
      "tags": ["motivation", "consistency"]
    }
  ]
}
```

Rendering engine randomly assigns or sequences quotations per chapter during render. Both header and footer carry quotations. Styled via `.page-header .quotation` and `.page-footer .quotation` in master CSS.

---

*Document Version: 1.0 | Last Updated: May 2026 | efficientcorporates.in*
