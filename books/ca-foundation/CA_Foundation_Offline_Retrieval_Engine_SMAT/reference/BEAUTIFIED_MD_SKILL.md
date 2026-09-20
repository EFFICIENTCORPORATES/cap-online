---
name: ca-foundation-beautified-markdown
version: "1.0"
status: "locked-reference-standard"
description: >-
  Source-faithful processing standard for converting ICAI CA Foundation raw Markdown,
  with the original ICAI PDF as authority, into verified, machine-readable Beautified
  Markdown suitable for deterministic offline retrieval. This skill forbids invented
  structure, requires page-level provenance, preserves accounting geometry, separates
  questions from answers/solutions, and requires explicit validation before a file can
  be marked Verified.
gold_standard_role: "GOLD_STANDARD_BEAUTIFIED_MD"
gold_standard_file: "references/GOLD_STANDARD_BEAUTIFIED_MD.md"
gold_standard_source_revision: "validated-v6"
project_baseline: "post-V1-V4-corrections"
---

# CA Foundation Beautified Markdown Processing Skill

## 1. Purpose

This skill defines the **mandatory processing and validation standard** for converting ICAI CA Foundation study-material Units from:

**Original ICAI PDF + existing Raw Markdown → Verified Beautified Markdown**

The output is not a summary, redesign, teaching note, or visually improved interpretation. It is a **source-faithful structured representation of the ICAI material**, designed so that a later Python retrieval engine can deterministically retrieve MCQs, theoretical questions, practical questions, examples, illustrations, solutions, topics, working notes, tables, and other content without asking an AI model to reinterpret the source.

The governing principle is:

> **The PDF decides the content and the structure. Markdown only represents it.**

If there is a conflict between the PDF and Raw Markdown, the PDF wins. If the Raw Markdown is cleaner but disagrees with the PDF, the PDF still wins. If a structure looks attractive but is not supported by the PDF, it must not be created.

---

## 2. Gold Standard / Reference Standard

The master reference output for this skill is:

`references/GOLD_STANDARD_BEAUTIFIED_MD.md`

This reference is the validated **Admission of a New Partner** Unit and is the structural benchmark for future Units. Its internal source revision is retained as `validated-v6`; it is not renamed internally merely to force a project version number. For project governance, its role is **GOLD_STANDARD_BEAUTIFIED_MD**.

Future processors must study both:

1. this `SKILL.md`; and
2. `references/GOLD_STANDARD_BEAUTIFIED_MD.md`

before processing any new Unit.

The Gold Standard demonstrates the following required patterns:

- source-first metadata;
- Paper → Module → Chapter → Unit hierarchy;
- physical PDF page and ICAI printed-page provenance;
- machine-readable `ICAI_BLOCK` markers;
- explicit Topic/Sub-topic boundaries;
- separate Example Question and Example Solution blocks;
- separate Illustration Question and Illustration Solution blocks;
- `pair_key` links between paired content;
- source-emphasis metadata where relevant;
- Markdown tables only for genuine, unambiguous source tables;
- fixed-width blocks for accounting layouts whose geometry matters;
- diagram transcription without inventing a list/table hierarchy;
- TYK categories and answers as independently retrievable blocks;
- explicit handling of reconstructed boundaries when a PDF page break disrupts extraction.

---

## 3. Non-Negotiable Principles

The following rules override every aesthetic or convenience preference.

### 3.1 PDF is authoritative

The original ICAI PDF is the final authority for:

- wording;
- figures;
- symbols;
- headings;
- numbering;
- row/column placement;
- question boundaries;
- solution boundaries;
- tables;
- journal/ledger geometry;
- highlighted/boxed content;
- page provenance.

Raw Markdown is only an extraction aid.

### 3.2 Never invent structure

Do not create any structure merely because it would be easier to read or retrieve.

**Forbidden examples:**

- turning a prose list into a table because it “fits” columns;
- adding a heading that is not present or semantically required by the source;
- inventing Illustration numbers for unnumbered examples;
- inventing totals, subtotal labels, Dr./Cr. labels, account names, column headings, or working-note labels;
- splitting one source block into new academic categories without evidence;
- merging separate source blocks because they discuss the same idea.

### 3.3 Accuracy first, formatting second

If an ordinary Markdown table distorts an accounting layout, use a fixed-width fenced block instead.

A visually plain but source-faithful representation is superior to an attractive but structurally incorrect table.

### 3.4 Do not rewrite ICAI content

Do not summarise, paraphrase, simplify, modernise, “correct English,” or rewrite the educational content unless the task explicitly requests a derivative version.

Beautification means:

**clean + classify + structure + tag + trace**

It does not mean:

**rewrite + summarise + interpret + improve wording**

### 3.5 Preserve source errors separately from extraction errors

If the PDF itself contains an apparent typo, preserve it in the source-faithful text unless there is explicit evidence that the extraction caused the error.

Distinguish:

- **source typo** — present in PDF; preserve it;
- **extraction artifact** — introduced by PDF-to-text/MD conversion; correct it;
- **uncertain discrepancy** — do not guess; flag for review.

---

## 4. Required Inputs

Each Unit must have, at minimum:

1. **Original ICAI PDF** — mandatory and authoritative.
2. **Raw Markdown** — existing PDF-to-MD extraction used as a text aid.
3. **Filename/hierarchy information** — used to derive Paper, Module, Chapter, Unit only when supported by the project inventory.

Optional but useful inputs:

- previous validation logs;
- page screenshots/renders for difficult pages;
- extraction diagnostics;
- known module/chapter mapping.

### 4.1 Preflight requirement

Do not process a Unit if the PDF and Raw MD pairing is uncertain.

Before conversion, confirm:

- PDF filename;
- raw-MD filename;
- Paper;
- Module;
- Chapter;
- Unit;
- expected page count;
- whether the file is truly a Unit, whole Chapter, or another scope.

If the source file does not carry an explicit Unit number, do **not** invent one. Use a neutral internal scope indicator only if required by the repository design.

---

## 5. Required Output

Each output must be a single **Verified Beautified Markdown** file with:

1. YAML/frontmatter metadata;
2. visible academic hierarchy;
3. machine-readable block markers;
4. page-source markers;
5. source-faithful content;
6. retrievable content-type classification;
7. deterministic question-answer pair links where applicable;
8. validation status.

Recommended filename:

`<SOURCE_BASENAME>_PARSED.md`

During testing/review, a suffix such as `_VALIDATED_VX` may be used, but production filenames should eventually stabilise once the schema is locked.

---

## 6. Authority Order During Comparison

When deciding what is correct, use this order:

1. **Visual PDF page**
2. **PDF text layer / positional extraction**
3. **Raw Markdown**
4. **Previous Beautified Markdown**
5. **Parser inference**

The lower source may help interpret the higher source, but may never override it without evidence.

---

## 7. Academic Hierarchy

Preserve the hierarchy:

`Paper → Module → Chapter → Unit → Topic → Sub-topic → Content Block`

Do not force every file to contain every level. If a source has no sub-topic, do not invent one.

### 7.1 Heading levels

Recommended Markdown hierarchy:

- `#` Chapter
- `##` Unit / major source section
- `###` numbered Topic
- `####` Illustration / TYK item / major child block
- `#####` source Sub-topic or case
- `######` Example Question/Solution when nested beneath a sub-topic

Heading depth may be adjusted only when necessary to preserve the source hierarchy, not to make the document look symmetrical.

---

## 8. Core Metadata Schema

The Gold Standard uses document-level metadata similar to:

```yaml
schema: "icai-foundation-knowledge-v2.0-validation"
content_fidelity: "source-preserving-structure-normalised"
qa_status: "verified"
level: "CA Foundation"
paper: <integer>
paper_title: "<source title>"
module: <integer>
chapter: <integer>
chapter_title: "<source title>"
unit: <integer or null>
unit_scope: "unit|chapter|other"
unit_title: "<source title>"
source_pdf: "<filename>.pdf"
source_raw_md: "<filename>.md"
source_pdf_pages: <integer>
page_number_basis: "1-indexed physical PDF page"
printed_page_basis: "ICAI printed page label retained in page markers and block metadata"
validation_role: "production|representative-unit-golden-sample"
no_invented_structure: true
```

### 8.1 Required block metadata

Every independently retrievable block should contain an `ICAI_BLOCK` marker.

Minimum fields:

```json
{
  "id": "P01-M02-C10-U03-<TYPE>-<NUMBER>",
  "type": "<content_type>",
  "number": "<source number or null>",
  "paper": 1,
  "module": 2,
  "chapter": 10,
  "unit": 3,
  "source_pdf": "<source>.pdf",
  "page_start": 1,
  "page_end": 1,
  "printed_page_start": "<ICAI label>",
  "printed_page_end": "<ICAI label>",
  "retrieval_type": "<content_type>"
}
```

### 8.2 Conditional block metadata

Add only when supported:

- `topic_number`
- `topic_title`
- `subtopic_title`
- `category`
- `pair_key`
- `sequence`
- `source_number`
- `source_emphasis`
- `source_structure`
- `representation`
- `table_spans_pages`
- `boundary_reconstructed`
- `boundary_method`
- `layout_method`

Do not populate optional metadata with guesses merely for completeness.

---

## 9. Block ID Standard

IDs must be deterministic, unique inside the repository, and stable across re-runs unless the source classification itself changes.

Recommended pattern:

`P{paper:02d}-M{module:02d}-C{chapter:02d}-U{unit:02d}-{TYPE}-{NUMBER}`

Examples of TYPE tokens:

- `LEARNING-OUTCOMES`
- `OVERVIEW`
- `TOPIC-3-2`
- `SUBTOPIC-...`
- `EXAMPLE-QUESTION-01`
- `EXAMPLE-SOLUTION-01`
- `ILLUSTRATION-QUESTION-3`
- `ILLUSTRATION-SOLUTION-3`
- `TYK-MCQ-QUESTION-7`
- `ANSWER-MCQ-7`
- `TYK-THEORY-QUESTION-2`
- `ANSWER-THEORY-2`
- `TYK-PRACTICAL-QUESTION-1`
- `ANSWER-PRACTICAL-1`

Never reuse one ID for two blocks.

---

## 10. Recognised Content Types

The parser must recognise the following categories when they actually exist in the source.

### 10.1 Structural content

- `learning_outcomes`
- `overview`
- `topic`
- `subtopic`
- `summary`
- `tyk_section`
- `tyk_category`
- `answers_section`
- `answers_category`

### 10.2 Explanatory/teaching content

- `concept`
- `explanation`
- `definition`
- `note`
- `example_question`
- `example_solution`
- `working_note`

Use these additional types only if they are clearly distinguishable in the source and the project schema has been updated consistently. Do not retroactively over-classify ordinary prose.

### 10.3 Illustration content

- `illustration_question`
- `illustration_solution`

### 10.4 Assessment content

- `tyk_mcq_question`
- `answer_mcq`
- `tyk_true_false_question`
- `answer_true_false`
- `tyk_theory_question`
- `answer_theory`
- `tyk_practical_question`
- `answer_practical`
- `tyk_scenario_question`
- `answer_scenario`

### 10.5 Layout descriptors

These are usually metadata/representation descriptors rather than academic content types:

- `table`
- `accounting_table`
- `journal_entry`
- `ledger`
- `trial_balance`
- `trading_account`
- `profit_and_loss_account`
- `balance_sheet`
- `calculation`
- `diagram`

---

## 11. Page Provenance Standard

Page traceability is mandatory.

### 11.1 Two page systems must be retained

For each block preserve:

1. **Physical PDF page** — 1-indexed page position in the PDF file.
2. **ICAI printed page** — printed label such as `10.84`, if present.

These are not interchangeable.

### 11.2 Visible source markers

Use markers such as:

```html
<!-- ICAI_SOURCE_PAGE pdf_page=10 printed_page="10.84" -->
```

For a multi-page block:

```html
<!-- ICAI_SOURCE_PAGE_RANGE pdf_pages=34-35 printed_pages="10.108-10.109" -->
```

### 11.3 Page-boundary rule

When content continues onto another physical page, insert the next page marker at the actual continuation point. Do not place all page references only at the block beginning.

### 11.4 Page-range integrity

For every block:

- `page_start <= every source page marker <= page_end`
- first marker must not predate `page_start`;
- last marker must not exceed `page_end`;
- printed-page span must correspond to the same source span.

---

## 12. Source-Structure Decision Tree

For every meaningful source block, answer the following questions in order.

### Step 1 — Is it ordinary prose?

If yes, keep it as prose.

Do not convert prose to a table merely because it contains labels and amounts.

### Step 2 — Is it a source list?

If yes, preserve it as an ordered or unordered list, matching the source numbering/bullets where practical.

### Step 3 — Is it genuinely tabular?

A Markdown table is allowed only when:

- the PDF visually contains a table or unquestionably tabular grid;
- row boundaries are clear;
- column meanings are clear;
- merged headings can be represented without changing meaning;
- values can be assigned to columns with high confidence;
- Markdown will not destroy the accounting geometry.

### Step 4 — Is it accounting geometry?

If the meaning depends on horizontal placement, inner/outer amount columns, Dr./Cr. sides, account halves, nested totals, or merged headings, use a fixed-width fenced block.

### Step 5 — Is it a diagram?

If yes, transcribe the diagram structure conservatively using labelled ASCII/fixed-width representation or a neutral textual transcription. Do not silently convert a radial/flow diagram into a list hierarchy unless that hierarchy is explicit.

### Step 6 — Is the layout uncertain?

Do not guess. Mark the block for manual visual verification and keep the least destructive representation until resolved.

---

## 13. Table Rules

### 13.1 When a Markdown table is allowed

Use a Markdown table when the PDF contains a simple source table with clear independent columns.

Example structural annotation:

```html
<!-- SOURCE_STRUCTURE type="table" representation="markdown" note="Direct source table; no columns invented." -->
```

### 13.2 When a Markdown table is forbidden

Do not use an ordinary Markdown table when the source contains:

- nested amount columns;
- inner/outer totals;
- multiple Dr./Cr. sections;
- account T-format geometry;
- ledger sides;
- a page-spanning table whose columns shift at the page break;
- merged headers whose meaning would be lost;
- prose with occasional amounts;
- working calculations written as normal lines.

### 13.3 No invented columns

Never create columns such as:

- `Particulars`
- `Amount`
- `Dr.`
- `Cr.`
- `Total`

unless those columns are visually/semantically present in the source.

### 13.4 Table completeness check

For every source table verify:

- title;
- column headings;
- every row;
- every amount;
- blank cells where meaningful;
- subtotal/total;
- debit/credit side;
- continuation across pages;
- parentheses/minus signs;
- ₹ symbols or source currency notation;
- footnotes/notes attached to table.

---

## 14. Accounting Layout Rules

Accounting material requires a different fidelity standard from ordinary prose.

### 14.1 Fixed-width representation is preferred when geometry matters

Use fenced `text` blocks for:

- Journal Entries with separate debit and credit amount columns;
- Ledger Accounts;
- Revaluation Accounts;
- Memorandum Revaluation Accounts;
- Partners’ Capital Accounts;
- Trial Balance;
- Trading Account;
- Profit & Loss Account;
- Balance Sheet with nested totals;
- Cash/Bank accounts;
- complex working-note fraction layouts;
- page-spanning statements.

### 14.2 Preserve semantic column position

A figure is not “verified” merely because the amount exists somewhere in the block. It must be attached to the correct:

- account;
- side;
- row;
- debit/credit column;
- inner/outer amount column;
- subtotal/total context.

### 14.3 Never infer a missing debit/credit location from arithmetic alone

Arithmetic consistency is a validation aid, not permission to reconstruct unobserved geometry.

### 14.4 Positional extraction procedure

For difficult accounting pages:

1. inspect the actual PDF page;
2. inspect positional PDF text if available;
3. identify horizontal column zones;
4. reconstruct the fixed-width block preserving order and indentation;
5. compare each amount back to the visual page;
6. verify totals independently;
7. verify source page marker.

### 14.5 Cross-page accounting blocks

If a statement continues on the next page:

- keep it one semantic question/solution block if the source does;
- place page markers at the continuation;
- preserve repeated headings only if they carry meaning;
- remove running page headers/footers that are not content;
- do not merge a following unrelated section into the same block.

---

## 15. Illustrations

Every Illustration must be independently retrievable.

### 15.1 Required structure

```text
Illustration N
  ├── illustration_question
  └── illustration_solution
```

Use the same `pair_key`, e.g.:

`illustration:3`

### 15.2 Question block

The Illustration Question must contain only the source question, including:

- opening facts;
- source balance sheet/table;
- all conditions;
- all numbered requirements;
- any page-spanning continuation;
- the final “prepare/show/calculate” instruction.

### 15.3 Solution block

The Illustration Solution must contain only the corresponding source solution, including:

- journal/ledger/statements;
- working notes;
- calculations;
- explanatory notes;
- final balances/conclusions.

### 15.4 Boundary check

Do not assume the word `SOLUTION` is always printed. Determine the boundary from the PDF’s visual/semantic layout. If the boundary had to be reconstructed, record:

```json
"boundary_reconstructed": true,
"boundary_method": "verified_pdf_layout"
```

### 15.5 Illustration numbering

Preserve source numbering exactly. Never renumber to make sequences continuous.

---

## 16. Worked Examples

Worked Examples must not be buried inside a Topic when the source visually identifies them as examples.

### 16.1 Pair structure

Use:

- `example_question`
- `example_solution`

with a common `pair_key`, e.g. `example:seq-04`.

### 16.2 Unnumbered examples

If ICAI does not assign a source number:

- `number: null`
- `source_number: null`
- assign an **internal** `sequence` only for deterministic retrieval.

Never present the internal sequence as if ICAI numbered the example.

### 16.3 Highlighted/boxed examples

If the source visually highlights or boxes an Example, retain this as metadata when useful:

```json
"source_emphasis": "highlighted_example_box"
```

This is descriptive metadata, not a new academic category.

---

## 17. Test Your Knowledge (TYK)

TYK must never remain one large undifferentiated text block.

### 17.1 Section hierarchy

Recommended structure:

```text
tyk_section
  ├── tyk_category: true_false
  ├── tyk_category: mcq
  ├── tyk_category: theory
  ├── tyk_category: practical
  └── tyk_category: scenario   [only if present]
```

### 17.2 Individual questions

Every question must be a separate block with source number and page range.

### 17.3 MCQ options

Verify:

- option labels;
- option order;
- amounts;
- punctuation where relevant;
- continuation across page breaks;
- that an option has not migrated into the next question due to extraction order.

### 17.4 Answers

Answers must be independently retrievable and paired with their question using `pair_key`.

Examples:

- `tyk:mcq:7`
- `tyk:true_false:3`
- `tyk:theory:2`
- `tyk:practical:1`

### 17.5 Answer-boundary rule

The answer to one category must not absorb the heading or answer text of the next category. Page breaks are a common failure point and require visual confirmation.

---

## 18. Diagrams, Boxes, Colour and Visual Emphasis

Text extraction often loses colour, boxes, arrows, radial relationships, and shaded tables.

### 18.1 Visual audit required

For every page with:

- red tables;
- shaded boxes;
- coloured examples;
- diagrams;
- arrows;
- callouts;
- multi-column layouts;

inspect the visual PDF page, not only its text layer.

### 18.2 Preserve meaning, not decorative colour

The Markdown does not need to reproduce colour itself unless colour carries meaning. It must preserve the **content and structural role** that the colour/box conveyed.

### 18.3 Diagrams

Use conservative transcription such as:

```html
<!-- SOURCE_STRUCTURE type="diagram" representation="ascii-transcription" -->
```

Do not infer an ordered hierarchy from a radial diagram unless the PDF indicates one.

---

## 19. Numerical Fidelity Rules

Numerical accuracy is a separate QA gate.

### 19.1 Every material numeric token must be checked

Verify especially:

- opening balances;
- Trade Payables/Receivables;
- capital balances;
- reserves;
- inventory;
- assets/liabilities;
- revaluation amounts;
- goodwill;
- ratios;
- percentages;
- journal amounts;
- totals/subtotals;
- final balance-sheet totals.

### 19.2 Numeric presence is not enough

The validator must check both:

1. **value correctness**; and
2. **structural attachment** — the value belongs to the correct row/side/account.

### 19.3 Number-format preservation

Preserve source-style Indian grouping where present (`1,00,000`, not automatically `100,000`).

Do not silently normalise source figures unless the repository explicitly adopts a separate canonical numeric field.

### 19.4 Arithmetic checks are secondary

Totals and calculations may be recomputed as a validation check, but the recomputed value must not replace the source without confirming the PDF.

---

## 20. Source Typos vs Extraction Artifacts

This distinction must be made explicitly.

### 20.1 Extraction artifacts — correct

Examples:

- broken word joins caused by page extraction;
- running header inserted in middle of a sentence;
- currency symbol read as another character;
- MCQ number displaced from its question;
- table row order scrambled by extraction;
- duplicated page header/footer;
- literal `\\n` artifacts;
- orphan Markdown separators.

### 20.2 Source typos — preserve

If the visual PDF itself contains the wording/error, retain it in the source-faithful Markdown. Do not “correct” ICAI silently.

If useful, record a non-invasive QA note outside the educational text, but never mutate the source wording merely because it appears wrong.

### 20.3 Uncertain cases — flag

If visual evidence is insufficient:

- retain the closest source-faithful representation;
- set QA status to `needs_manual_verification` for that file/block;
- document the uncertainty;
- do not mark the file Verified.

---

## 21. Raw MD Comparison Method

Raw Markdown is useful for text coverage but unreliable for layout.

For each page:

1. identify the PDF page number and printed page label;
2. locate corresponding raw-MD text;
3. compare headings and body text;
4. compare every visible table/account/box/diagram;
5. check the raw extraction order;
6. identify missing or duplicated lines;
7. detect header/footer contamination;
8. detect page-break sentence splits;
9. detect displaced question/option numbers;
10. reconstruct only what the PDF supports.

Never trust raw-MD table syntax as proof that the source contained a table.

Never trust absence of a raw-MD table as proof that the PDF did not contain one.

---

## 22. Detailed Processing Workflow

### Phase 0 — Preflight

- confirm PDF/raw-MD pair;
- derive hierarchy;
- count physical PDF pages;
- identify printed-page numbering pattern;
- note whether pages contain scans/graphics/complex tables.

**Gate:** Do not continue if the pair is wrong or scope is uncertain.

### Phase 1 — Build page map

Create an internal map:

`physical_pdf_page → printed_page → raw_MD region → visible source sections`

Record where Topics, Illustrations, TYK and Answers begin/end.

### Phase 2 — Segment academic structure

Identify only source-supported:

- Learning Outcomes;
- Overview;
- Topics;
- Sub-topics;
- Examples;
- Illustrations;
- Summary;
- TYK;
- Answers.

### Phase 3 — Insert block metadata

Assign deterministic `ICAI_BLOCK` markers and page metadata.

### Phase 4 — Reconstruct source format

For each block choose exactly one primary representation:

- prose;
- list;
- Markdown table;
- fixed-width accounting layout;
- ASCII/labelled diagram transcription.

### Phase 5 — Separate paired content

Create paired blocks for:

- Example Q/S;
- Illustration Q/S;
- TYK question/answer.

Validate unique and matching `pair_key` values.

### Phase 6 — Numerical reconciliation

Compare every material figure against the visual PDF page.

### Phase 7 — Page-boundary audit

Check every page transition for:

- missing continuation;
- duplicate continuation;
- answer contamination;
- table continuation errors;
- misplaced list/question numbers.

### Phase 8 — Visual-layout audit

Reinspect every page containing tables, red/highlighted boxes, accounts, diagrams or multiple columns.

### Phase 9 — Machine validation

Run structural validators for:

- JSON validity of block markers;
- unique IDs;
- page-range validity;
- pair-key completeness;
- balanced fenced blocks;
- malformed Markdown tables;
- forbidden residual headers/footers;
- literal extraction artifacts;
- source-page-marker range integrity.

### Phase 10 — Final manual verification

A human/AI visual pass must still review the accounting-heavy and visually complex pages. Passing machine checks alone does not make a file Verified.

### Phase 11 — Status assignment

Only after all gates pass set:

`qa_status: verified`

Otherwise use a non-final status such as:

- `draft`
- `needs_manual_verification`
- `validation_failed`

---

## 23. Validation Checklist — Mandatory

A Unit is not Verified until all applicable checks are PASS.

### 23.1 Content completeness

- [ ] Every source page was inspected.
- [ ] All educational text is present.
- [ ] No source block is duplicated.
- [ ] No source block is silently omitted.
- [ ] Page-break continuation text is complete.

### 23.2 Heading and hierarchy

- [ ] Chapter is correct.
- [ ] Unit is correct.
- [ ] Topic numbering matches source.
- [ ] Sub-topic headings match source.
- [ ] Illustration numbering matches source.
- [ ] Question numbering matches source.
- [ ] No heading was invented for appearance.

### 23.3 Tables/layouts

- [ ] Every source table is represented.
- [ ] No non-table source block was converted into an artificial table.
- [ ] Every row is present.
- [ ] Every column is present.
- [ ] Every heading is present.
- [ ] Totals/subtotals are present.
- [ ] Debit/credit placement is preserved.
- [ ] Inner/outer amount placement is preserved.
- [ ] Page-spanning layouts are preserved.

### 23.4 Illustrations/examples

- [ ] Every Illustration question is separate.
- [ ] Every Illustration solution is separate.
- [ ] Q/S `pair_key` matches.
- [ ] Working Notes remain with the correct solution.
- [ ] Every explicitly highlighted Example is independently classified.
- [ ] Unnumbered Examples were not assigned fake source numbers.

### 23.5 TYK

- [ ] TYK section is identified.
- [ ] Categories are separated.
- [ ] Every MCQ is independent.
- [ ] All options are present and correctly attached.
- [ ] True/False questions are separate.
- [ ] Theory questions are separate.
- [ ] Practical questions are separate.
- [ ] Scenario questions are separate if present.
- [ ] Answers are separately retrievable and paired.

### 23.6 Numerical checks

- [ ] All ₹ amounts match source.
- [ ] Ratios match source.
- [ ] Percentages match source.
- [ ] Totals match source.
- [ ] Values are attached to the correct row/account/side.

### 23.7 Provenance

- [ ] Every major/retrievable block has `source_pdf`.
- [ ] Every block has physical page range.
- [ ] Printed page range is retained where available.
- [ ] Continuation markers are inserted at actual page transitions.
- [ ] No source marker falls outside block range.

### 23.8 Cleanliness

- [ ] No running ICAI page header inside content.
- [ ] No footer/page-number contamination.
- [ ] No orphan table separators.
- [ ] No literal extraction escape artifacts.
- [ ] No accidental duplicate headings.
- [ ] No unbalanced code fences.

---

## 24. Acceptance Gates

A file may be marked **Verified** only when all five gates pass.

### Gate A — Source Coverage

All physical pages accounted for and all source content captured.

### Gate B — Structural Fidelity

No invented table/heading/category and no missed source table/box/diagram.

### Gate C — Accounting Fidelity

All accounting layouts preserve semantic geometry and amounts.

### Gate D — Retrieval Integrity

Block IDs, types, numbers, page spans and pair keys are deterministic and valid.

### Gate E — Human/Visual QA

Representative difficult pages have been compared directly against the PDF, not merely against extracted text.

**If any gate fails, the file is not Verified.**

---

## 25. Failure / Uncertainty Policy

When uncertain, the processor must fail conservatively.

### 25.1 Never guess a number

If a figure is unclear, mark it for verification rather than inferring from totals.

### 25.2 Never guess table geometry

If column placement is unclear, preserve a minimally transformed fixed-width extraction and flag it.

### 25.3 Never guess boundaries

If a solution boundary is ambiguous, inspect adjacent PDF pages. If still ambiguous, mark `boundary_reconstructed` and require manual QA.

### 25.4 Never silently repair source wording

If a sentence appears grammatically wrong but the PDF shows the same text, preserve it.

### 25.5 Do not approve partially verified files

A file can be structurally parseable yet still fail source fidelity. Machine-valid is not the same as source-verified.

---

# Part II — Version 1–4 Post-Mortem and Permanent Rules

## 26. Why the Earlier Versions Were Not Sufficient

The earlier attempts improved progressively, but they exposed a central design problem: **the process was initially treating beautification as a formatting task instead of a source-reconstruction task**.

The Gold Standard was reached only after shifting to:

- PDF-authoritative comparison;
- page-by-page visual audit;
- source-structure decisions;
- positional preservation for accounts;
- deterministic block metadata;
- explicit numerical reconciliation;
- regression-style validation.

The following failures must be treated as permanent regression cases.

---

## 27. Post-Mortem Matrix

### PM-01 — Artificial tables created from non-table source

**What went wrong:** Normal prose, question details or working information was sometimes converted into a Markdown table because it could be arranged neatly into columns.

**Why it happened:** The parser optimised for readability/structure instead of reproducing the PDF.

**How detected:** Visual PDF comparison showed no actual source table even though the Beautified MD had one.

**How corrected:** Reverted the block to prose/list/calculation representation.

**Permanent rule:** **No table without source evidence.** A Markdown table requires a genuine source table or unquestionably tabular structure.

**Regression test:** For every Markdown table, record/confirm the PDF page where the source table exists.

---

### PM-02 — Genuine source tables missed

**What went wrong:** Some actual tables, including visually emphasised/red/highlighted layouts, were absent or flattened into text.

**Why it happened:** Text extraction does not reliably preserve colour, borders, shaded boxes or visual grids.

**How detected:** Visual page audit showed tabular content not represented in MD.

**How corrected:** Reconstructed the table/layout from the PDF page.

**Permanent rule:** **Every visually complex/accounting page requires visual PDF inspection.** Text-layer coverage alone is insufficient.

**Regression test:** Page inventory must flag any page containing a table/box/account and confirm a corresponding MD representation.

---

### PM-03 — Accounting geometry broken

**What went wrong:** Debit/credit positioning, nested amount columns, capital-account geometry, ledgers and balance sheets became distorted in ordinary Markdown tables.

**Why it happened:** Markdown tables are one-dimensional row/column structures and cannot safely represent every accounting layout.

**How detected:** Figures were present but attached to the wrong side/column or the source geometry was lost.

**How corrected:** Rebuilt difficult layouts as fixed-width fenced text using PDF positional layout.

**Permanent rule:** **When geometry carries accounting meaning, preserve geometry rather than forcing a Markdown table.**

**Regression test:** For every accounting block, verify each amount’s account, side and amount column against the PDF.

---

### PM-04 — Numerical values looked plausible but were structurally wrong

**What went wrong:** Values such as Trade Payables could appear in the MD but be vulnerable to wrong row/column interpretation.

**Why it happened:** Numeric token presence was being treated as sufficient validation.

**How detected:** Direct PDF comparison of the Illustration balance sheet exposed the need to verify exact row and geometry, not only the value.

**How corrected:** Reconstructed accounting tables from the source and reconciled values in context.

**Permanent rule:** **Every material figure must be verified as value + structural attachment.**

**Regression test:** Numeric reconciliation must identify the label/account/side associated with each high-risk figure.

---

### PM-05 — Illustration question/solution boundaries incorrect

**What went wrong:** A question line could leak into the solution, or solution material could be merged with surrounding content.

**Why it happened:** Raw extraction boundaries do not always align with printed headings; some solutions do not begin with a clean machine-detectable marker.

**How detected:** Page-by-page visual review of Illustration transitions.

**How corrected:** Reconstructed the boundary using verified PDF layout and explicit paired blocks.

**Permanent rule:** **Every Illustration has separate Question and Solution blocks connected by one pair key.**

**Regression test:** Each `illustration:n` must have exactly one question and one solution unless the source genuinely omits one.

---

### PM-06 — Explicit worked Examples buried in Topic prose

**What went wrong:** Worked Examples were initially left inside Topic text and therefore could not be independently retrieved.

**Why it happened:** The parser recognised conceptual topic flow but missed visual Example emphasis/boxing.

**How detected:** Visual PDF review revealed highlighted Example blocks not represented as separate semantic blocks.

**How corrected:** Created `example_question` and `example_solution` pairs with internal sequence numbers only where source numbers were absent.

**Permanent rule:** **An explicitly identified/highlighted source Example must be independently retrievable.**

**Regression test:** Compare every visually marked Example in the PDF against the Example block count.

---

### PM-07 — Fake source numbering risk for unnumbered Examples

**What went wrong:** Internal ordering can be mistaken for ICAI numbering.

**Why it happened:** Deterministic retrieval requires an identifier, but source Examples may be unnumbered.

**How detected:** Review of the source showed Example labels without source numbers.

**How corrected:** `number: null`, `source_number: null`, plus internal `sequence`.

**Permanent rule:** **Internal sequence is metadata, never presented as source numbering.**

---

### PM-08 — Page-break artifacts displaced question/list numbers

**What went wrong:** MCQ numbers, option labels, list items or sentence continuations moved to the wrong location after extraction.

**Why it happened:** PDF reading order and page breaks can reorder tokens.

**How detected:** Visual comparison and numbering continuity checks.

**How corrected:** Reattached numbers/options to the correct source content using the PDF page.

**Permanent rule:** **Numbering must be validated visually at every page boundary.**

**Regression test:** Detect missing/duplicate sequence numbers and inspect every sequence discontinuity.

---

### PM-09 — MCQ option displacement

**What went wrong:** An MCQ option could be attached to the previous/next question or appear out of order.

**Why it happened:** Multi-column/page-break extraction did not preserve visual reading order.

**How detected:** Comparing each MCQ and options against the source PDF.

**How corrected:** Reassembled MCQ blocks from the PDF.

**Permanent rule:** **Every MCQ must be validated as question stem + complete ordered option set.**

---

### PM-10 — Practical answer absorbed unrelated answer text

**What went wrong:** A Practical Answer block accidentally included preceding MCQ/theory answer material.

**Why it happened:** Category boundaries on the answer pages were inferred from text order instead of visually verified headings/layout.

**How detected:** Cross-category answer review against the PDF.

**How corrected:** Rebuilt the answer boundary directly from the relevant PDF pages.

**Permanent rule:** **Answer-category transitions are hard boundaries and must be visually checked.**

**Regression test:** The first line of each answer block must belong to its declared category/question.

---

### PM-11 — Long worked Example/solution truncated at a page boundary

**What went wrong:** A later case/table/conclusion in a long Example was omitted.

**Why it happened:** The parser prematurely ended the block when the page/visual section changed.

**How detected:** Page-span reconciliation against the original PDF.

**How corrected:** Extended the block to include the complete source case and conclusion.

**Permanent rule:** **Semantic block end is determined by the source, not by physical page end.**

**Regression test:** Every page-spanning Example/Illustration must have explicit continuation markers and a verified ending.

---

### PM-12 — Running headers and table separators leaked into content

**What went wrong:** Repeated ICAI page headings, footer text or Markdown separator fragments survived extraction and appeared as educational content.

**Why it happened:** PDF-to-MD treated page furniture as ordinary text/table rows.

**How detected:** Artifact scans plus visual comparison.

**How corrected:** Removed only extraction/page-furniture artifacts while preserving real source content.

**Permanent rule:** **Running headers/footers are not academic content and must be excluded.**

---

### PM-13 — Currency/extraction symbol corruption

**What went wrong:** Currency symbols or similar glyphs could be misread by raw extraction.

**Why it happened:** Font/text-layer mapping issues.

**How detected:** Visual PDF verification of amounts.

**How corrected:** Replaced the extraction artifact with the symbol shown in the PDF.

**Permanent rule:** **Symbols attached to material figures must be checked against the visual source.**

---

### PM-14 — Source typo was at risk of being “fixed”

**What went wrong:** Apparent errors in ICAI wording could be silently corrected by the beautification process.

**Why it happened:** Natural-language cleanup tends to normalise grammar/spelling.

**How detected:** Comparing disputed wording directly with the PDF showed that some odd wording was genuinely in the source.

**How corrected:** Retained source wording and separated source fidelity from editorial correction.

**Permanent rule:** **Never silently correct a source typo.** Only extraction errors are corrected automatically.

---

### PM-15 — Page metadata did not fully cover visible source markers

**What went wrong:** Some blocks contained content from a later page while `page_end` stopped earlier.

**Why it happened:** Metadata was assigned before the final page-boundary reconstruction.

**How detected:** Validator found source-page markers outside declared block ranges.

**How corrected:** Expanded/corrected the block page span.

**Permanent rule:** **Page metadata is validated after content reconstruction, not assumed from the initial extraction.**

---

### PM-16 — Diagram flattened into an invented hierarchy

**What went wrong:** A visual overview/diagram risked being represented as a conventional list/tree that the PDF did not actually state.

**Why it happened:** Text-first extraction loses spatial relationships and encourages linearisation.

**How detected:** Visual comparison of the overview page.

**How corrected:** Used a conservative ASCII transcription and explicitly labelled the source structure as a diagram.

**Permanent rule:** **Preserve diagram relationships without inventing hierarchy.**

---

### PM-17 — Nested balance-sheet totals were flattened

**What went wrong:** Capital subtotals/outer totals could be lost when a multi-amount-column balance sheet was converted to a simple table.

**Why it happened:** Raw MD cannot reliably distinguish inner and outer amount columns.

**How detected:** Visual page comparison revealed the nested amount-column structure.

**How corrected:** Fixed-width representation retained inner and outer totals.

**Permanent rule:** **Nested amount columns trigger fixed-width accounting layout unless a Markdown table can preserve them unambiguously.**

---

### PM-18 — Verification relied too heavily on block counts

**What went wrong:** Counts such as “11 illustrations” or “10 MCQs” could reconcile while individual rows, figures, layouts or boundaries were still wrong.

**Why it happened:** Structural counts are easy to automate but do not prove source fidelity.

**How detected:** Manual comparison found errors despite correct aggregate counts.

**How corrected:** Added page-level visual audit, numeric reconciliation and layout validation.

**Permanent rule:** **Correct counts are necessary but never sufficient for verification.**

---

## 28. Regression Test Suite for Every Future Unit

Every future Unit must be tested against the above failure classes.

Minimum regression assertions:

1. No Markdown table exists without a corresponding genuine source table.
2. Every visually obvious source table has a representation.
3. Complex accounting geometry is not forced into a simple table.
4. Every Illustration number in source appears exactly once as Q and once as Solution where applicable.
5. Every explicit Example is independently classified.
6. No internal Example sequence is presented as ICAI numbering.
7. No MCQ number or option is displaced.
8. Every TYK answer belongs to the correct category.
9. No page-spanning block ends prematurely.
10. No page header/footer contamination remains.
11. Every material numeric amount matches source and correct position.
12. No source typo is silently editorialised.
13. Every block page range contains all of its page markers.
14. No duplicate block IDs.
15. No orphan `pair_key`.
16. No unbalanced fenced layout.
17. No malformed Markdown table.
18. All source pages are accounted for.

---

## 29. Definition of “Verified”

**Verified** does not mean:

- Markdown renders without errors;
- all headings exist;
- block counts match;
- Python can parse the file;
- the file looks neat.

**Verified means:**

> Every material content block has been compared against the authoritative ICAI PDF; source structure is preserved; educational wording is not rewritten; numerical figures and accounting placement are source-faithful; page provenance is accurate; questions/solutions/answers are correctly separated; and both machine and visual QA gates pass.

---

## 30. Batch Processing Rule for the Remaining PDFs

Do not simply prompt “make all remaining files like the reference.”

For each PDF, execute the full workflow independently:

1. load this Skill;
2. inspect the Gold Standard;
3. pair PDF + raw MD;
4. build page map;
5. classify source structure page-by-page;
6. create Beautified MD;
7. run validation gates;
8. fix failures;
9. re-run validation;
10. mark Verified only after PASS.

### 30.1 Batch does not remove per-file QA

Automation may accelerate extraction and validation, but every file retains its own verification record. A parser rule that worked in one Unit is not proof that a visually different Unit is correct.

### 30.2 Stop-on-regression rule

If a new Unit reveals a new failure class not covered by this Skill:

1. stop the batch at that Unit;
2. document the failure;
3. correct the Unit;
4. add a permanent rule/regression test to the Skill;
5. re-check already processed Units if the new rule could affect them;
6. then resume.

This prevents repeating a newly discovered mistake across the remaining repository.

---

## 31. Recommended Repository Structure

```text
ca-foundation-knowledge/
├── source_pdf/
│   └── <original PDFs>
├── raw_md/
│   └── <raw PDF-to-MD outputs>
├── parsed_md/
│   └── <verified Beautified MDs>
├── skill/
│   ├── SKILL.md
│   └── references/
│       └── GOLD_STANDARD_BEAUTIFIED_MD.md
├── validation/
│   ├── reports/
│   └── machine_results/
└── retrieval/
    └── <future offline Python retrieval engine>
```

---

## 32. Retrieval Compatibility Requirements

The Beautified MD schema must support deterministic queries such as:

- all MCQs;
- MCQs from a Chapter/Unit;
- all theoretical questions;
- all practical questions;
- all scenario-based questions;
- all Illustrations;
- Illustration questions only;
- Illustration Q + solutions;
- all worked Examples;
- everything from a Unit;
- all content under a Topic;
- question-only teaching compilation;
- source-page lookup.

Therefore, source text must never be the only signal. Retrieval must use explicit block metadata.

---

## 33. Minimum Machine Validation Rules

A validator should fail the file when any of the following occurs:

- invalid `ICAI_BLOCK` JSON;
- duplicate `id`;
- missing required metadata;
- `page_start > page_end`;
- source page marker outside block range;
- duplicate source question number within same category unless source itself duplicates;
- unpaired question/answer `pair_key`;
- unbalanced fenced code blocks;
- malformed Markdown tables;
- residual extraction markers known to be invalid;
- declared `verified` status while unresolved QA flags exist.

Machine validation should also warn, not necessarily fail, for:

- unusual number formatting;
- source typo notes;
- blocks with `boundary_reconstructed: true`;
- diagrams requiring manual layout review;
- complex accounting pages with low extraction confidence.

---

## 34. High-Risk Page Prioritisation

The following pages always receive enhanced manual review:

- first page of a Unit;
- page containing Unit Overview/diagram;
- every Illustration start/end page;
- every page with a Journal/Ledger/Balance Sheet/Trial Balance;
- every page where an accounting table crosses a page break;
- TYK category transition pages;
- answer-category transition pages;
- pages containing red/highlighted/boxed source elements;
- pages with dense multiple columns;
- final page of a Unit.

---

## 35. Processing Notes That Must Never Become Source Content

Internal notes such as these may exist in metadata/comments but must not be inserted into ICAI educational prose:

- “boundary reconstructed”;
- “source table confirmed”;
- “fixed-width chosen due to nested amounts”;
- “source typo retained”;
- “manual verification required.”

Keep QA metadata separate from the study material.

---

## 36. Change-Control Policy

This Skill is a living standard, but changes must be controlled.

A rule may be changed only when a new source pattern demonstrates that the current rule is inadequate.

For every change:

1. state the new failure pattern;
2. add/modify the rule;
3. add a regression test;
4. increment the Skill version;
5. identify which previously processed Units may be affected;
6. revalidate affected Units.

Do not casually change the schema in the middle of processing 35+ files.

---

## 37. Golden-Sample Regression Requirement

Before releasing a new parser/process revision, re-run it against the Gold Standard Unit.

The new process must not degrade:

- block count/identity;
- pair keys;
- page ranges;
- source structure annotations;
- accounting geometry;
- numerical fidelity;
- TYK separation;
- Example/Illustration separation.

If the new process changes the Gold Standard, the change must be explained and reviewed. Silent drift is forbidden.

---

## 38. Final “Do / Do Not” Rules

### DO

- read the PDF visually;
- use raw MD as an extraction aid;
- preserve source wording;
- preserve source numbering;
- preserve physical and printed pages;
- classify explicit Examples and Illustrations;
- pair questions and answers;
- use Markdown tables for genuine simple tables;
- use fixed-width text for complex accounting geometry;
- verify every material figure;
- flag uncertainty;
- run machine validation;
- perform final visual QA.

### DO NOT

- beautify by redesigning;
- invent tables;
- invent source numbering;
- infer a debit/credit column solely from arithmetic;
- flatten complex accounts into unsafe Markdown tables;
- silently fix ICAI wording;
- trust raw MD layout blindly;
- trust text extraction alone for highlighted/boxed material;
- treat correct counts as proof of correctness;
- mark a file Verified with unresolved uncertainty.

---

## 39. Operational Instruction for an AI/Parser

When this Skill is used to process a new Unit, the operative instruction is:

> Read the original ICAI PDF and the corresponding Raw Markdown. Treat the PDF as authoritative. Reproduce the source structure faithfully rather than redesigning it. Preserve Paper/Module/Chapter/Unit/Topic hierarchy, source numbering, physical PDF page and ICAI printed-page provenance. Create independently retrievable blocks for explicit Examples, Illustrations, TYK questions and corresponding answers/solutions. Create a Markdown table only when the PDF genuinely contains an unambiguous table. Preserve complex accounting geometry in fixed-width form when Markdown tables would alter debit/credit, inner/outer amount, ledger, journal, or statement meaning. Correct extraction artifacts but do not silently correct source wording. Verify all material amounts and their structural placement against the PDF. Run structural, numerical, page-range, pairing and layout validation. If uncertain, flag the block and do not mark the file Verified.

---

## 40. Final Standard

The success criterion for the project is not “all PDFs converted.”

The success criterion is:

> **Every Beautified Markdown file is sufficiently source-faithful, structured, traceable and validated that later offline Python retrieval can use it deterministically without requiring an AI model to reinterpret the ICAI source and without the user having to worry that a question, answer, amount, table, illustration or accounting structure was silently changed or missed.**
