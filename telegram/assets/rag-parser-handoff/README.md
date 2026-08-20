# CA / CS / CMA Knowledge Base — Parser Developer Brief

**Read this first, then read `CA_CS_CMA_Knowledge_Base_RAG_Master_Spec.md`
(one level up, in `telegram/assets/`) for full depth.** This README is the
onboarding brief — what to build first, what rules are non-negotiable, and
what's in this sample package. The master spec is the complete engineering
contract (57 sections) — every rule below is a distillation of it, not a
replacement for it. If the two ever disagree, the master spec wins; tell us
and we'll fix this README.

---

## 1. What we're actually building

Not a PDF search tool. The end goal is:

1. **A hybrid RAG system** students (and, later, an AI tutor / MCP tools) can
   ask real syllabus questions against, with every answer traceable back to
   an exact document, page, and heading.
2. **An MCQ / question-recommendation engine** that generates and selects
   practice questions from *validated, source-linked* content — never a bare
   "generate 100 MCQs from this PDF" prompt.
3. **A descriptive-answer evaluator** — a student uploads a handwritten
   answer, and the system OCRs it, retrieves the model answer + marking
   scheme + authoritative source, and returns marks + feedback + citations.

All three consume the **same underlying knowledge base** — one parsing and
structuring pipeline feeds all of them. That's why the parser is the
foundation of this whole project, not a side task: if the structure/page/
source linkage is wrong here, every downstream feature (recommendations,
grading, citations) inherits that error.

## 2. Non-negotiable ground rules

These come directly from the master spec and have already been decided —
please build to them rather than proposing alternatives, unless you hit a
real technical blocker:

- **The PDF is immutable evidence, never the database.** Keep three
  distinct layers: raw PDF → processed representation (Markdown + parsed
  JSON) → knowledge database. The whole database must be rebuildable from
  the PDFs if parsing logic changes.
- **Page numbers are mandatory, not optional.** Every heading/content block
  must carry its page range. If the PDF's own page count and the printed
  textbook page number differ, capture both (`PDF_PAGE` vs `PRINTED_PAGE`).
- **Never invent structure that isn't in the source.** If a chapter has no
  numbered subsections, do not manufacture `4.1`, `4.2`, etc. Every
  heading/topic gets a `source_type`: `explicit` (numbered in the source),
  `inferred` (a real heading, just unnumbered), `generated` (created by your
  system for organization — must never be presented as if it were an
  official textbook heading), or `unknown`.
- **One parsing engine, not one parser per course.** See §5 below — this is
  a specific, already-made architecture decision, not a suggestion.
- **CA, CS and CMA do NOT share one native structure.** Don't force CMA or
  CS content into CA's Chapter→Topic→Subtopic shape if the source itself
  doesn't have it. Detect the native hierarchy first (Module/Lesson/Section/
  whatever the publisher actually used), preserve it, *then* map it into the
  common canonical model — keeping the native label alongside the canonical
  one, always.
- **Human-in-the-loop is a feature, not a failure.** When confidence is low
  on something that materially affects the hierarchy, the pipeline should
  produce a review item (document, page, extracted text, the parser's
  interpretation, confidence score) instead of guessing. It should keep
  going on the rest of the batch — one ambiguous page never blocks the
  other 999 documents.
- **Content typing matters.** Examples, illustrations, practice questions,
  summary boxes, "Test Your Knowledge" sections, case studies, notes — these
  must be classified as their own content type, never flattened into
  generic paragraphs. They're what the MCQ engine and answer evaluator
  actually retrieve from.

## 3. Architecture, condensed

```
Original PDFs (immutable)
    → PDF metadata / registration (hash, page count, course/level/subject)
    → PDF → Markdown (page-marker-preserving)
    → Structure-aware parser (deterministic rules + AI for ambiguous cases)
    → Canonical JSON (native structure preserved + mapped to common model)
    → Semantic content chunks (heading/paragraph-boundary aware, not fixed-size)
    → Embeddings → PostgreSQL + pgvector
    → Hybrid retrieval (metadata filter + keyword + vector)
    → RAG answers / MCQ generation / descriptive answer checking
```

Deterministic code (Python/SQL) owns: document IDs, metadata, page numbers,
hashing, duplicate detection, storage, retrieval filtering. AI is used only
for: ambiguous structure interpretation, semantic classification, answer
quality assessment, explanation/feedback generation. Keep that split — it's
what keeps this affordable and auditable at ~1,100 documents.

## 4. The corpus, one level deeper

~1,100 PDFs across CA, CS, CMA, each with 3 levels:

| Course | Levels | Institute |
|---|---|---|
| CA | Foundation, Intermediate, Final | ICAI |
| CS | CSEET, Executive, Professional | ICSI |
| CMA | Foundation, Intermediate, Final | ICMAI |

Four document *types*, each behaving differently and needing separate
handling:

- **Study Material** (~1,070 files) — the actual teaching content, one PDF
  per chapter/unit. This is the bulk of the corpus and where native
  structure differs most between courses (see §5).
- **Exam Material** (~58 files, currently CA Inter Advanced Accounting only)
  — real past exam papers: MTP (Mock Test Paper), PYQ (Past Year Question),
  RTP (Revision Test Paper). A completely different genre from Study
  Material — no chapter/topic hierarchy to speak of, instead: paper →
  question number → marks → (for MTP) a separate `-Q`/`-Ans` file pair, or
  (for PYQ) one combined file with both question and suggested answer.
- **Revision Material** — category exists, currently empty (0 files). Don't
  build special-case logic for it yet; there's nothing to test against.
- **Faculty content** — individually authored material outside the official
  ICAI/ICSI/ICMAI publications: handwritten notes (scanned images, no
  reliable text layer — heavy OCR dependency), and faculty-authored
  descriptive question banks (often scanned with irregular column layouts —
  see the real example in the sample package, §7).

## 5. Parser configuration model — build ONE engine, not N parsers

This was explicitly decided (see master spec §56) after looking at real
files: **do not build a separate parser per course.** Build one parsing
engine, plus a config profile per `(course, level, document_type)` resolved
at runtime. A profile is pure data (regex patterns, heading keywords,
confidence thresholds) — never new code. Example profile shape:

```yaml
profile_id: CA_INTERMEDIATE_STUDY_MATERIAL

identity:
  course: CA
  institute: ICAI
  level: Intermediate
  document_type: Study Material

native_levels: [Module, Chapter, Unit, Topic, Subtopic]

structure_patterns:
  chapter:
    - "^CHAPTER\\s+\\d+"
    - "^Module\\s+\\d+"
  unit:
    - "^UNIT\\s+[IVX]+"
  topic:
    - "^\\d+\\.\\d+\\s"
  subtopic:
    - "^\\d+\\.\\d+\\.\\d+\\s"

strip_patterns:
  - "^ICAI\\s*-\\s*Study Material$"
  - "^\\d+$"

content_labels:
  example: ["Example", "Illustration"]
  summary: ["Summary", "Let Us Recapitulate"]
  practice_question: ["Test Your Knowledge", "Exercise"]
  note: ["Note:", "Important:"]

toc_authority: supporting_evidence

confidence_thresholds:
  explicit: 0.95
  inferred: 0.80
  human_review_below: 0.70

canonical_mapping:
  Module: chapter_group
  Chapter: chapter
  Unit: chapter
  Topic: topic
  Subtopic: subtopic
```

**These regex patterns are a starting example, not a locked spec** — the
master spec is explicit that the *real* number of profiles needed, and the
exact patterns each one needs, is an empirical question your 9-document
pilot (§7 below) should answer, not something we guess upfront. What we
*have* locked in: the profile-per-`(course, level, document_type)` model
itself, and that a new course/level/type becomes a new config file, never a
parser rewrite.

A few real patterns already known from the actual corpus, worth building
your regex against directly:

- Study Material filenames already encode structure:
  `{COURSE}_L{level}_P{paper}_C{chapter}_U{unit}_{Title}.pdf` — e.g.
  `CA_L2_P01_C10_U1_AccountingStandard21Consolidated.pdf`. **Do not rely on
  this for content structure** (per master-spec rule: metadata must be
  authoritative, not filenames) — but it's a very useful *hint*/cross-check
  while you're building and debugging the real in-document parser.
- Some single logical chapters are split across **two physical PDFs**
  (e.g. `..._C10_U0-1_...pdf` + `..._C10_U0-2_...pdf`) — your document
  registration layer needs to know these are one unit, two files, not two
  unrelated units.
- CS material is much less numbered than CA/CMA — expect ALL-CAPS run-on
  headings with no `x.y` numbering at all in many chapters. Don't force a
  `4.1`/`4.2` pattern match where none exists; that's exactly the
  "inferred vs. invented" distinction in the rules above.

## 6. What "done" looks like for Phase 1 (the pilot — start here, not on all 1,100 files)

Per the master spec, **do not process the full corpus before a small pilot
proves the pipeline.** Concretely, for each sample PDF in this package we
want to see:

1. **Markdown conversion** with page markers preserved
   (`<!-- PDF_PAGE: 43 | PRINTED_PAGE: 41 -->` style — see master spec §8),
   headings/numbering/tables/formulas/examples/notes kept intact.
2. **Native structure JSON** — what hierarchy your parser actually detected
   in *that specific* document (Module/Chapter/Unit for CA, Lesson/Section
   for CS, etc.), with `source_type` + `confidence` on every node.
3. **A review-queue record** for anything below your confidence threshold —
   we want to see this mechanism working on real ambiguous headings from
   the sample set, not just the confident cases.
4. Confirmation that content types (example / illustration / summary /
   practice question / note) are being classified, not flattened into plain
   paragraphs.

Once that's working end-to-end on this sample set, we scale to the CA/CS/CMA
syllabus taxonomy mapping (only CA currently has a governed topic index to
map against), then chunking + embeddings, then the MCQ/answer-evaluator
services. Full phase-by-phase detail: master spec §54.9.

## 7. Sample PDF package — what's in here and why

**We are not sending all ~1,100 PDFs yet.** This package (19 real files) is
chosen to show every *structurally distinct* situation your parser will
need to handle — not one PDF per subject, which would mostly be redundant
copies of the same CA-style numbering. If your pilot handles all 19 of
these correctly, you've almost certainly covered the real variation in the
full corpus; anything genuinely new that turns up at full scale is the
exception, not the rule.

```
sample-pdfs/
├── 01-CA-study-material/         7 files — the strongest-numbered corpus
├── 02-CS-study-material/         3 files — least-numbered, ALL-CAPS headings
├── 03-CMA-study-material/        3 files — Module/Section, mixed numbering
├── 04-exam-material-MTP-PYQ-RTP/ 4 files — a different genre entirely: exam papers
└── 05-faculty-content-OCR-cases/ 2 files — scanned/handwritten, real OCR problems
```

**01-CA-study-material/** (Foundation, Intermediate, Final all represented):
- `CA_L1_P01_C0_U1_InitialPages.pdf` — front-matter/table-of-contents pages.
  Real edge case: this has no chapter content at all; confirm your parser
  classifies it as front matter, not as an empty/failed chapter.
- `CA_L1_P01_C0_U9_Corrigendum.pdf` — an official corrigendum notice, not
  teaching content. Another "don't force this into the chapter hierarchy"
  case.
- `CA_L1_P01_C1_U1_MeaningAndScopeOfAccounting.pdf` — a clean, well-numbered
  Foundation-level unit. Your baseline "this should just work" case.
- `CA_L2_P01_C10_U1_AccountingStandard21Consolidated.pdf` — Intermediate,
  an Accounting-Standard-numbered chapter (a naming convention on top of the
  chapter numbering).
- `CA_L2_P02_C10_U0-1_AuditAndAuditors.pdf` +
  `CA_L2_P02_C10_U0-2_AuditAndAuditors.pdf` — **one logical chapter split
  across two physical files.** Confirm your document-registration layer
  links these, rather than treating them as two independent chapters.
- `CA_L3_P01_C0_U1-1_InitialPages.pdf` — Final-level front matter.

**02-CS-study-material/** (CSEET, Executive, Professional):
- `CS_L1_P01_C1_U0_ESSENTIALSOFGOODENGLISH.pdf`,
  `CS_L2_P01_C10_U0_LAWRELATINGTOLIMITATION.pdf`,
  `CS_L3_P01_C10_U0_STAKEHOLDERSRIGHTS.pdf` — all three genuinely have far
  less internal numbering than CA. Expect to lean on heading detection
  (font size/bold/position) more than regex-on-numbers here.

**03-CMA-study-material/** (Foundation, Intermediate, Final):
- `CMA_L1_P01_C1_U0_Introduction.pdf`,
  `CMA_L2_P05_C12_U0_CompaniesAct2013.pdf`,
  `CMA_L3_P13_C1_U0_TheCompaniesAct2013.pdf` — note `CMA_L2_...CompaniesAct2013`
  and `CMA_L3_...CompaniesAct2013` are **the same Act taught at two
  different levels, in two different papers** — a real case of the same
  legal subject matter appearing in more than one place in the taxonomy;
  don't assume a subject/topic name is unique across the whole corpus.

**04-exam-material-MTP-PYQ-RTP/** — an entirely different genre from Study
Material (no chapter/topic hierarchy — paper → question number → marks):
- `CAInter-AdvAcc-MTP-May2024-Set1-Q.pdf` +
  `CAInter-AdvAcc-MTP-May2024-Set1-Ans.pdf` — an MTP question paper and its
  answer paper as **two separate files** that need to be linked
  question-by-question.
- `CAInter-AdvAcc-PYQ-May2024-Ans.pdf` — a real past exam paper where
  question **and** suggested answer are in **one combined file** (a
  different convention from MTP's split Q/Ans files — don't assume PYQ and
  MTP share one parsing rule).
- `CAInter-AdvAcc-RTP-May2024-Q.pdf` — revision test paper, question-only
  (RTP questions in this corpus don't reliably carry marks — a real,
  already-known limitation, not something to "fix" by inventing marks).

**05-faculty-content-OCR-cases/** — deliberately the hardest two files in
this package:
- `AS02 Inventory Handwritten Notes.pdf` — genuinely handwritten, scanned
  pages. No reliable extractable text layer — this is your real
  handwriting-OCR test case, directly relevant to the descriptive-answer
  evaluator's own OCR pipeline (student-uploaded handwritten answers will
  look like this).
- `descp-companies-act.pdf` — a real, already-documented problem file: an
  irregular scanned/column layout where a naive extractor previously found
  47 question prompts but only 46 of the expected answer markers. We want
  to see how your parser handles (and flags) exactly this kind of
  discrepancy — silently dropping the mismatched item is the wrong
  behavior; flagging it for review is correct.

## 8. Deliverable JSON shapes (summary — full detail in master spec §18, §54.6)

Three JSON layers per document, in order:

1. **Document manifest record** — one per physical PDF: `document_id`,
   course/institute/level/subject, `native_structure`, `native_code`,
   `original_filename`, `file_hash` (SHA-256), `page_count`,
   `processing_status`.
2. **Native structure JSON** — what the parser found: a `native_structure`
   description (top-level type + full level list) and a flat `nodes[]` list,
   each with `native_type`, `native_number`, `native_title`,
   `parent_node_id`, `source_type`, `confidence`, `page_start`/`page_end`.
3. **Content blocks JSON** — the actual chunked, retrievable text: each
   block tagged with `content_type` (paragraph/definition/rule/formula/
   example/illustration/table/note/practice_question/summary/...),
   `page_start`/`page_end`, `sequence`, and the chapter/topic node(s) it
   belongs to.

Never skip straight to embeddings without these — the whole point of this
design is that every future answer can cite an exact document + page +
heading, and that citation chain only exists if these layers are built and
kept.

## 9. What we're deliberately NOT asking for yet

- Don't build CS/CMA syllabus taxonomy mapping yet — only CA currently has
  a governed topic index to map against (CS/CMA don't have one built yet on
  our side).
- Don't build the amendment/edition-applicability system (master spec §57)
  yet — that's a real, designed-but-not-built feature for law/tax content,
  out of scope for the parser pilot.
- Don't process the full ~1,100-document corpus yet, even if the pilot
  works perfectly — we want to review real output on this sample set first.

## 10. Questions during the pilot

If you hit a document that doesn't fit any pattern above, or a structural
ambiguity you're not sure how to classify — that's expected and welcome,
not a sign something's wrong. Send it back with the page, the extracted
text, and your best-guess interpretation + confidence, the same shape the
master spec's own review-queue record uses (§15). We'll decide together
rather than have it guessed silently either way.

---

*Companion file: `CA_CS_CMA_Knowledge_Base_RAG_Master_Spec.md` (same
folder) — the full 57-section spec this brief was distilled from. Sample
PDFs: `sample-pdfs/` (this folder), 19 files, real production content.*
