# Concept Book / Revision Notes Production Pipeline

**Owner / teaching voice:** CA Pranav Pratik Tulshyan — Newton of Accounts  
**Course:** CA Inter Advanced Accounting (VC Gurukul)  
**Repository:** `EFFICIENTCORPORATES/cap-online`  
**Purpose:** make the complete note-generation method reproducible for any future human or AI agent.

> Read this file before creating chapter summary notes, handwritten-style revision PDFs, HTML notes, or full Concept Book chapters. This is the operating runbook that connects the original handwritten notes, ICAI Study Material, annotations, lecture transcripts, Excalidraw/vector recovery, HTML rendering, PDF generation, and eventual full-book assembly.

---

## 1. What we are actually building

There are two related products, and agents must not confuse them:

1. **15-minute / last-day revision notes** — very compressed, visual, teacher-facing/student-facing recall sheets. They should preserve Pranav's flowcharts, shortcuts, examples, warnings, colours and classroom sequence. They are not a mini Study Material.
2. **Full Concept Book** — chapter-by-chapter teaching book. It reconstructs the class journey in a durable editable form, then renders that content into HTML/PDF editions and ultimately into one complete book, using the Question Bank Book pipeline as the engineering model for reproducibility and QA.

The final chain is:

```text
SOURCE EVIDENCE
  ↓
source inventory + page/timestamp evidence
  ↓
official topic map + classroom teaching-beat map
  ↓
canonical structured content / Markdown
  ↓
visual blocks + registered assets / diagrams
  ↓
handwritten-style HTML + clean-print HTML
  ↓
chapter PDFs
  ↓
whole-book front matter + TOC + chapters + back matter
  ↓
merged HTML / print PDF
  ↓
coverage / source / visual QA
```

**PDF is never the source of truth.** Keep an editable text/structured master and regenerate HTML/PDF from it.

---

## 2. Source hierarchy — what each input is allowed to decide

Different sources answer different questions. Do not collapse them into one undifferentiated pile.

| Source | What it decides | What it must NOT decide |
|---|---|---|
| **Unannotated ICAI Study Material** | Accounting correctness, official wording meaning, chapter coverage, section/page references, official examples/illustrations | Classroom order or Pranav's preferred explanation |
| **Teacher-annotated ICAI Study Material** | What Pranav underlined, prioritised, cross-referenced, skipped, circled, connected or emphasised | It does not replace the clean official source; annotations can be incomplete |
| **NB01 Class Annotated Notes** | Main classroom concept order, Pranav's explanations, arrows, flowcharts, analogies, examples, memory logic | Exact official wording / numerical authority when handwriting is unclear |
| **NB02 Class Annotated Notes** | Question placement, in-class practice sequence, solution method, illustration refs | It should not be treated as a complete concept outline |
| **Lecture / revision-video transcript** | Spoken explanation, Hinglish phrasing, examples, stories, repeated emphasis, transitions, teaching sequence clues | It is not accounting authority; ASR can mishear numbers/terms |
| **Teacher revision notes** | Compression style, last-day priority, memory diagrams, what is worth retaining in a 10–20 min recap | They are not a replacement for the full chapter source set |
| **Question Bank / practice tracker** | Exam relevance, repetition, practice coverage and selected questions | Not authority for ICAI concept wording |
| **Existing Concept Book stories / characters** | Continuity of the teaching universe and reusable story devices | Do not force a story into a concept where it adds no teaching value |

### Authority rule

When sources disagree:

- **Accounting rule / definition / recognition / measurement:** ICAI source wins until a corrigendum or later edition is verified.
- **How Pranav teaches it:** NB01 + annotated SMAT + transcript win.
- **Which question was taught there:** NB02 + annotated SMAT + transcript corroboration.
- **What goes into a 15-minute revision:** revision-note style + Pranav's recurring class emphasis, while keeping ICAI coverage safe.
- **Unclear handwriting / unclear ASR:** mark it `needs_teacher_review`; never invent a clean-looking answer.

---

## 3. Where the original sources are

### 3.1 Google Drive — current CA Inter chapter source folders

The currently verified Drive source roots are:

- **Teacher-annotated ICAI Study Material**  
  `https://drive.google.com/drive/folders/1xmSOYMmtv8HehJNOwtQ6_WYO2WIKlHxH`
- **Class Annotated Notes (NB01 / NB02 chapter PDFs)**  
  `https://drive.google.com/drive/folders/1fHgz8ktYI8_kF5oQaUKVHcP43KE9bTNb`
- **Unannotated ICAI Study Material — May 2027 edition root**  
  `https://drive.google.com/drive/folders/13huHzTSMJ97-a-5EsNRejzEVG1b3jxIc`

The broader Drive folder previously used to group Advanced Accounts materials is:

- `https://drive.google.com/drive/folders/1vkXftVomfQtkdoLoc25Emde64RcSTEWh`

That grouping contains folders such as `ICAI-SMAT Annotated`, `Class Annotated Notes`, `ICAI-SMAT` and `QuestionBank`.

**Never assume a chapter match from folder access alone.** Match the actual chapter/AS name and inspect content. For example, AS 26 was matched as:

- NB01: `P01 NB 01 AS 26 Intangible Assets`
- NB02: `P01 NB 02 AS 26 Intangible Assets.pdf`
- annotated ICAI: `M2_C5_U6_ Accounting Standard 26 Intangible Assets.pdf`

### 3.2 Original CollaNote concept notebook

A recovered original CollaNote package exists at:

`books/ca-inter/concept-book/notes_making/source/P01-NB-01B CONCEPT BOOK.cnote`

It is also indexed in private R2 through `R2_MANIFEST.md`.

The detailed conversion history is:

`books/ca-inter/concept-book/notes_making/README.md`

### 3.3 Large/binary storage

Do not commit large videos, PDFs, audio or other binaries just to make an agent see them.

- Repo large-file policy: `AGENTS.md`
- R2 inventory: `R2_MANIFEST.md`
- Private bucket currently documented there: `ec-cap-online-assets`
- Restore/sync tooling lives in `EFFICIENTCORPORATES/ec-asset-index`

Text manifests, Markdown, HTML, JSON and scripts belong in Git. Large media belongs in the approved external store/R2.

---

## 4. Where lecture videos, audio and transcripts live

> **Transcription agents:** before changing models, language settings, Romanization, GPU setup, or bulk-processing logic, read `_claude/skills/SKILL-ca-lecture-transcription.md`. It contains the tested settings, failed experiments, QA method, Roman Hinglish policy, local RTX 3050/CUDA learnings, and the current no-bulk-before-approval gate.

There are three distinct layers.

### 4.1 Source video archive

The archive workflow copies Google Drive lecture videos to R2 under:

`source-videos/<lecture-folder>/<video>.mp4`

The archive workflow is documented/implemented in the repository's GitHub Actions history and related workflow files.

### 4.2 Audio derivatives

Audio is generated from the R2-backed video and stored under:

`audio/<lecture-folder>/<lecture>.mp3`

For QA, the current 5-minute test workflow accepts paths such as:

`audio/3. AS-10/Lecture 4-AS 10 Property Plant and Equipment.mp3`

Workflow:

`.github/workflows/test-transcription-5min.yml`

### 4.3 Transcript text outputs

The verified intro end-to-end workflow writes transcript text into:

`books/ca-inter/concept-book/notes_making/lecture_transcripts/01-intro/<lecture>/`

Files produced by the workflow include:

- `transcript.md`
- `transcript.txt`
- `transcript.json`
- `transcript.srt`
- `transcript.vtt`
- `manifest.json`

Workflow:

`.github/workflows/intro-videos-e2e.yml`

The intended production convention is to extend the same shape chapter-by-chapter, e.g.:

```text
books/ca-inter/concept-book/notes_making/lecture_transcripts/
  03-as10/
    lecture-01/
      transcript.md
      transcript.json
      manifest.json
    lecture-02/
      ...
```

If a chapter transcript has not yet been committed there, search R2 / workflow artifacts before saying it does not exist.

### Transcript language policy

For Pranav's classes:

- preserve **Roman Hinglish / English-script speech**;
- preserve technical accounting terms in English;
- do not translate the class into formal textbook English before extraction;
- do not convert normal Hinglish to Devanagari unless explicitly requested;
- retain timestamps in the machine-readable transcript;
- unclear words/numbers must be flagged, not guessed.

Use transcripts as **teaching evidence**, not as the authority for an Accounting Standard.

---

## 5. How the original handwriting was recovered

The CollaNote `.cnote` file is a structured ZIP-like package, not a PDF.

The recovery process already documented in `notes_making/README.md` discovered:

1. page records `.cpage`;
2. drawing data in `_dkDrawing`;
3. Base64/protobuf-like stroke records;
4. recoverable stroke coordinates, widths and colours;
5. embedded audio and timestamps.

The important design decision was **not to rasterise first**.

### Existing Excalidraw-compatible outputs

The notebook was reconstructed into editable vector-style JSON:

- `notes_making/excalidraw/notebook_all_pages.excalidraw.json`
- `notes_making/excalidraw/page-XX.excalidraw.json`
- `notes_making/excalidraw/notebook_editable_source.json`
- `notes_making/excalidraw/font_and_ocr_settings.json`

The large all-pages JSON and editable source are indexed in `R2_MANIFEST.md`.

### What Excalidraw is for

Use Excalidraw/vector recovery for:

- preserving **actual handwritten strokes**;
- retaining original table lines, arrows, circles and page geometry;
- editing/reusing a teacher-created flowchart without redrawing it from memory;
- animation/whiteboard work where the repository explicitly uses Excalidraw.

### What Excalidraw is NOT for

Do not force the entire Concept Book to be authored as thousands of freehand elements.

For the book itself:

- canonical content stays in Markdown/structured data;
- normal text remains real searchable/selectable text;
- tables stay semantic HTML where practical;
- registered original drawings can be inserted as visual assets or reconstructed diagrams;
- the renderer creates HTML;
- PDF is printed from HTML.

This gives us editable content **and** the handwritten visual identity without sacrificing searchability, accessibility or reproducibility.

---

## 6. OCR policy

OCR is **assistive only** for handwritten notes.

Do not use OCR as the sole authority for:

- accounting numbers;
- journal entries;
- T-accounts;
- arrows / branch logic;
- table row/column placement;
- handwritten abbreviations;
- circled exceptions.

Correct sequence:

1. inspect page visually;
2. use OCR only to accelerate text discovery;
3. compare critical facts against the original image/vector page;
4. mark uncertainty;
5. preserve the original visual source reference.

A wrong number in the correct sentence is worse than an explicit `unclear` marker.

---

## 7. Chapter intake — exact process for every new chapter

Create a source-inventory record before writing.

Minimum sources to locate:

- [ ] clean ICAI SMAT for the same edition;
- [ ] annotated ICAI SMAT;
- [ ] NB01;
- [ ] NB02;
- [ ] teacher revision notes, if available;
- [ ] lecture transcripts / revision-video transcripts, if available;
- [ ] relevant practice tracker / question mappings;
- [ ] existing Concept Book chapter, story, asset or prior prototype.

For each source capture:

```yaml
source_id:
source_type:
title:
chapter:
edition:
drive_or_repo_locator:
printed_pages:
pdf_pages:
checksum_if_downloaded:
verified_date:
status:
notes:
```

Do not draft until the agent can state which sources are present and which are missing.

---

## 8. Build the official topic map first

The clean ICAI Study Material gives the full official skeleton.

Create a topic tree containing:

- chapter / AS;
- section heading;
- definition/rule;
- sub-rule / exception;
- printed page;
- PDF page;
- official examples;
- official illustrations;
- Test Your Knowledge / exercise references.

This is the **coverage map**, not the teaching sequence.

The point is to prevent a beautiful set of notes from silently omitting an examinable ICAI concept.

---

## 9. Reconstruct Pranav's classroom sequence

This is the most important intellectual step.

### Evidence order

1. NB01 — main teaching path.
2. Teacher-annotated ICAI SMAT — emphasis and cross-reference.
3. Transcript — spoken transition, example, story, reason for a diagram.
4. NB02 — selected question inserted after the concept.
5. Revision notes — final compression / memory device.

A classroom sequence may deliberately differ from ICAI order. Preserve it if the evidence supports it.

### Teaching-beat record

Use stable IDs, e.g.:

```yaml
beat_id: AS26-T007
order: 7
heading: Research vs Development
official_refs:
  - AS26-6.13
  - AS26-6.14
  - AS26-6.15
nb01_pages: [..]
nb02_pages: [..]
annotated_smat_pages: [..]
transcript_refs:
  - lecture: ...
    start: ...
    end: ...
teacher_explanation:
teacher_example:
diagram_asset:
exam_trap:
selected_question:
verification: verified|needs_teacher_review
```

This teaching-beat layer is the bridge between raw evidence and book writing.

---

## 10. How to think when making a 15-minute revision note

The revision note is **not** made by summarising every paragraph.

Ask, in order:

1. What is the chapter's first decision/question in class?
2. What flowchart lets a student classify the issue fastest?
3. What are the 3–7 definitions/rules they must recall exactly enough for the exam?
4. What is the biggest conceptual fork?
5. Which exceptions cause marks to be lost?
6. Which tiny example makes the rule memorable?
7. Which timeline / table / journal entry / formula is worth one visual block?
8. What can safely be left to the full Concept Book?

### Target content

A 15-minute revision file should usually contain:

- one opening chapter map;
- definitions in compressed form;
- key recognition/measurement flow;
- one or two decisive comparison tables;
- research/development or similar timelines where relevant;
- mini examples, not full illustrations;
- red exam traps;
- final 30–60 second recall flowchart.

### Example: AS 26 prototype logic

The AS 26 revision prototype used the classroom decision logic:

```text
Expenditure
  ↓
Future economic benefit?
  ├─ no → expense
  └─ yes
       ↓
asset / benefit beyond current period?
       ↓
held for sale?
       ├─ yes → relevant inventory/other standard
       └─ no
            ↓
physical/tangible element predominant?
            ├─ yes → AS 10 / PPE
            └─ no → AS 26 / Intangible
```

Then the note compressed:

- identifiable + non-monetary + no physical substance;
- identifiability / control / future economic benefit;
- recognition criteria;
- acquisition routes;
- Research vs Development;
- the recognition-point timeline;
- amortisation;
- impairment;
- disposal/disclosures;
- six exam traps.

This is the desired pattern: **Pranav's thinking compressed, not ICAI paragraphs compressed**.

---

## 11. Visual grammar for handwritten-style HTML notes

The 2026-10 AS 26 revision prototype established a practical HTML approach that should be reused and refined.

### Page look

- A4 portrait.
- White/cream page.
- Light blue ruled notebook lines.
- Red vertical margin line.
- Handwriting-style typography where licensed/available.
- Real text, not a page screenshot.

### Colour roles

Use colour semantically and consistently:

- **Blue:** main concept, headings, arrows, normal teaching logic.
- **Red:** exception, warning, expense, prohibited treatment, exam trap.
- **Green:** allowed treatment, recognition, capitalisation, positive branch.
- **Black:** calculations, labels, ordinary supporting example.

Do not colour randomly for decoration.

### Block types

Prefer a small reusable vocabulary:

- `flowchart`
- `decision-tree`
- `definition`
- `mini-example`
- `comparison-table`
- `timeline`
- `exam-trap`
- `journal-entry`
- `formula`
- `memory-line`
- `source-ref`

A future renderer should receive these block types from structured content rather than infer layout from paragraphs.

### Handwritten feel without losing editability

Use:

- slightly rotated boxes sparingly;
- underline / wavy underline;
- arrows and circles;
- irregular rounded borders;
- ruled-paper background;
- short phrases rather than dense prose.

Avoid:

- flattening whole pages to PNG;
- illegible fake-handwriting fonts;
- excessive decorative stickers;
- making every concept a coloured box;
- copying a scanned page as the final note.

---

## 12. Clean-print HTML and handwritten HTML come from the same content

One chapter should not have two separately written content files that drift.

Preferred architecture:

```text
chapter-content.md / chapter-content.json
            ↓
      validated blocks
       ↙           ↘
handwritten theme   clean-print theme
       ↓                 ↓
handwritten.html     clean.html
       ↓                 ↓
handwritten.pdf      clean.pdf
```

Theme changes should alter appearance, not accounting content.

---

## 13. PDF generation

Read:

`_claude/skills/SKILL-html-to-pdf.md`

Key rules:

- HTML remains the visual master.
- Define `@page` size/margins explicitly.
- Use `print-color-adjust: exact`.
- Keep assets local/resolved at build time.
- Chrome/Edge headless can render static page-based HTML.
- For paged.js continuous-flow books, follow the paged.js-specific instructions; plain `--print-to-pdf` may capture a blank/hidden print state.
- Visually inspect every PDF page after generation.

A PDF existing is not evidence that the page is correct.

---

## 14. Full Concept Book chapter writing

The full chapter must expand the revision note into the complete teaching journey.

Recommended per-beat pattern:

```text
CONCEPT
  ↓
Pranav's explanation / analogy / story
  ↓
precise ICAI rule reference
  ↓
diagram / flow / table
  ↓
selected immediately relevant NB02 / ICAI question
  ↓
stepwise verified solution
  ↓
exam trap
  ↓
next concept
```

Do not put every question inline. Only essential teaching questions belong immediately after the concept. Reinforcement/homework lives in the practice layer.

Existing writing guidance:

- `_claude/skills/concept-book-chapter-writing.md`
- `_claude/skills/SKILL-concept-book-voice-and-craft.md`
- `_claude/skills/SKILL-concept-book-thinking-and-reader.md`
- `books/ca-inter/concept-book/NEWTON_CONCEPT_BOOK_PRODUCTION_GUIDE.md`

---

## 15. How the Question Bank Book teaches us to engineer the Concept Book

Do not copy the Question Bank's content model, but copy its **production discipline**.

Master runbook:

`first_run/HOW-TO-BUILD-THE-BOOK.md`

The Question Bank succeeded because it separates:

1. extracted source data;
2. normalized index;
3. chapter generation;
4. front/back matter;
5. TOC;
6. merge;
7. page-number resolution;
8. reverse extraction / diff QA;
9. final deliverables.

The Concept Book should evolve toward the same shape:

```text
concept-book/
  sources / manifests
  evidence / page extracts
  chapters / canonical content
  renderer / themes
  output / chapter-html
  output / chapter-pdf
  output / qa
  front-matter
  toc
  merged-book
  final-deliverable
```

Do not create these folders mechanically if an existing repo location already serves the purpose. The production guide requires inspecting before reorganising.

### Required Concept Book QA equivalents

Eventually implement automated checks for:

- every official topic linked to at least one teaching beat or explicit exclusion;
- every teaching beat linked to source evidence;
- no broken NB/SMAT/transcript references;
- no selected question orphaned from a concept;
- no duplicate IDs;
- no missing registered visual assets;
- no unresolved `needs_teacher_review` in a release;
- no broken HTML;
- page count sanity;
- no overflow / clipped pages;
- chapter-level and book-level TOC consistency.

A strong future goal is a **round-trip audit** similar to Question Bank QA: parse the finished book back into a machine-readable concept/question index and compare it with the canonical chapter manifests.

---

## 16. Recommended chapter file contract

For a new chapter, prefer a compact text-first set such as:

```text
chapters/as26-intangible-assets/
  source-manifest.yaml
  official-topic-map.yaml
  teaching-beats.yaml
  OPEN_REVIEW.md
  chapter.md
  assets-manifest.yaml
  output/
    revision-handwritten.html
    revision-clean.html
    chapter-handwritten.html
    chapter-clean.html
```

Generated PDFs stay outside Git when binary policy requires it and are indexed in R2.

This is a target contract. Before creating it, check whether the chapter already has an established path/file that should be reused.

---

## 17. Provenance rules inside generated notes

Every agent must be able to answer:

- Which ICAI edition?
- Which official pages?
- Which NB01 pages?
- Which NB02 pages?
- Which annotated pages?
- Which video/timestamp?
- Is this a real Pranav example or a generated analogy?
- Was the question/solution verified?

Student-facing pages need not show every internal locator, but the canonical source/manifest must retain them.

Generated analogies must never be silently presented as something Pranav actually said.

---

## 18. Examples — how to preserve Pranav's notes instead of replacing them

### Bad

> “An intangible asset is recognised when probable future economic benefits will flow and cost is reliably measurable.”

Correct but generic. It loses the class.

### Better

Start with the class decision tree, then place the definition and recognition rule at the exact point where the student needs it. Add the class example (e.g. staff training → benefit exists but control fails), the red exception, and the research/development timeline.

The book should let a student mentally hear the class again.

### Diagram rule

If a distinctive Pranav-created flowchart exists:

1. locate the original notebook page;
2. preserve/recover the original strokes if useful;
3. register it with a stable asset ID;
4. optionally reconstruct a clean HTML/Excalidraw version while retaining the source reference;
5. do not redraw from memory after reading only the ICAI text.

---

## 19. Quality gates before calling a chapter “done”

### Source gate

- [ ] All four core sources found or missing ones explicitly reported.
- [ ] Edition matched.
- [ ] Transcript status known.
- [ ] Source manifest complete.

### Content gate

- [ ] Official topic coverage complete.
- [ ] Classroom sequence reconstructed.
- [ ] Teacher examples separated from generated additions.
- [ ] Selected questions placed correctly.
- [ ] Accounting rules and calculations verified.

### Visual gate

- [ ] Handwritten HTML readable at 100%.
- [ ] No clipped text.
- [ ] No orphan heading at page bottom.
- [ ] Tables remain readable.
- [ ] Colours preserve semantic roles.
- [ ] Original flowcharts/examples feel recognisably like Pranav's notes.

### Release gate

- [ ] HTML is editable and self-contained enough to rebuild.
- [ ] PDF has been visually reviewed page-by-page.
- [ ] Binary output is stored/indexed according to R2 policy.
- [ ] No unresolved teacher-review markers.
- [ ] Coverage / QA report saved.
- [ ] Teacher approval recorded before calling it approved/final.

---

## 20. Agent start checklist

A new agent assigned “Make notes for Chapter X” should do this before drafting:

1. Read `AGENTS.md`.
2. Read repo `README.md`.
3. Read `NEWTON_CONCEPT_BOOK_PRODUCTION_GUIDE.md`.
4. Read this runbook.
5. Read `notes_making/README.md` if handwriting/Excalidraw is involved.
6. Read the concept-book writing skills.
7. Locate clean ICAI + annotated ICAI + NB01 + NB02.
8. Search for existing revision notes.
9. Search transcript folder + R2/workflow artifacts.
10. Inspect existing chapter/story/assets.
11. Build source inventory.
12. Build official topic map.
13. Reconstruct teaching beats.
14. Only then write revision/full-book content.
15. Render HTML.
16. Render PDF.
17. Run automated checks where available.
18. Visually inspect.
19. Record open questions and teacher decisions.
20. Update project/session log.

---

## 21. Current gaps / work still to automate

The architecture is established, but the following are not yet fully automated for every chapter:

- chapter-wide transcript production and canonical transcript index;
- automatic NB01/NB02 chapter matching with confidence;
- structured teaching-beat manifest generator;
- reusable handwritten-note HTML renderer;
- concept-book front matter / TOC / merge scripts;
- concept coverage matrix;
- round-trip finished-book QA;
- automatic asset resolver from R2 for original handwriting visuals;
- teacher-review dashboard.

Do not pretend these exist. Build them incrementally and document each addition.

---

## 22. One-sentence mental model

> **ICAI gives us the truth; annotations tell us what matters; NB01 tells us how Pranav teaches it; NB02 tells us where practice enters; transcripts recover the voice; Excalidraw preserves the original handwriting; structured Markdown/JSON preserves the knowledge; HTML preserves the design; PDF distributes it; the Question Bank pipeline teaches us how to make the entire book reproducible and auditable.**

