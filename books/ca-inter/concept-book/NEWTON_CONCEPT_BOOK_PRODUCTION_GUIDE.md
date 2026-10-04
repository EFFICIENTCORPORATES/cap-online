# Newton of Accounts — Concept Book Production Guide

**Owner / credited author:** CA Pranav Pratik Tulsian  
**Brand:** Newton of Accounts  
**Scope:** CA Inter concept books, starting with AS 10 and AS 2; extend to other standards/chapters after both pilots are approved.  
**Status:** Production operating specification (initial version); source links verified at folder level on 2026-10-04; individual chapters, transcripts, solutions and the full source inventory require per-chapter verification.  
**Repository:** https://github.com/EFFICIENTCORPORATES/cap-online  
**Home:** `books/ca-inter/concept-book/`

> **Start here for every new concept-book assignment.** Also read the repository's root `AGENTS.md`, `README.md`, the relevant existing concept-book skills, and chapter files. This guide describes the requested Newton of Accounts production workflow. Never assume an older draft or an AI-produced PDF has been academically approved. If conflicting instructions exist, pause and raise the conflict rather than silently overriding repository rules.

## 1. Product and non-negotiable teaching method

The deliverable is **not a condensed reprint of ICAI text**. Reconstruct the teacher's actual classroom journey: **concept → teacher's explanation/story/diagram → precise ICAI section → the selected immediately relevant in-class illustration or question and stepwise solution → examination trap → next concept**. Longer unselected exercises form a separate practice assignment. Preserve the order actually taught as evidenced by notebooks and annotations, not ICAI chapter order alone.

The materials must combine clarity and visual memory: short concept blocks, hand-drawn-style arrows and branching maps, comparative tables, scene-based story panels, color-coded rules/exceptions, calculations, journal entries and revision walls. Do not turn the entire chapter into consecutive text boxes. The approved target has **one canonical editable Markdown/content model → two styled HTML editions (handwritten-style and clean print) → two PDFs**. HTML and Markdown remain editable; PDF is an output artifact, never the source of truth. Handwritten style can use appropriately licensed handwriting-style typography and vector illustrations while retaining searchable/selectable text; use embedded original strokes only when legally and technically available.

Credit all student-facing outputs to **CA Pranav Pratik Tulsian — Newton of Accounts**. Avoid legacy branding in newly authored material, page headers, file naming, alt text and generated covers; when reading existing repository material, historical branding or author-spelling discrepancies are input metadata, not authority for future output. Do not rewrite unrelated historical content unless specifically assigned.

## 2. Input-source register and each source's job

| Source | Verified location / identifier | Use | Authority / cautions |
|---|---|---|---|
| **Unannotated ICAI study material (May 2027)** | https://drive.google.com/drive/folders/13huHzTSMJ97-a-5EsNRejzEVG1b3jxIc | Official learning outcomes, concepts, section/page numbers, worked examples, illustrations, exercises and exact question numbering for the relevant edition | **Accounting-text authority for the supplied edition.** Confirm edition, page and corrigenda before publication. The linked root has Modules 1–3; inspect child folders per chapter. |
| **Teacher-annotated ICAI study material** | https://drive.google.com/drive/folders/1xmSOYMmtv8HehJNOwtQ6_WYO2WIKlHxH | Underlines, margin notes, teacher priority, cross-references to notebooks, question selection and class delivery clues | Overlay against its matching unannotated edition; do not separately duplicate the same printed content. Folder listed successfully; PDFs are present. |
| **Classroom notebooks NB01 and NB02** | https://drive.google.com/drive/folders/1fHgz8ktYI8_kF5oQaUKVHcP43KE9bTNb | **NB01**: teacher's actual concept order, informal explanations, stories and drawings. **NB02**: selected in-class questions, solution method, exercise/illustration references and placement in the lesson | These establish the pedagogical timeline. Scanned handwriting needs visual inspection. Do not trust OCR for numbers, arrows, tables or unclear words. Folder listed successfully; chapter files must be matched by name/content. |
| **Practice topic tracker** | `Master_Tracker_Practice_With_Pranav_Bhaiya.xlsx` (supplied project workbook; original Drive source managed separately) | Topic IDs, practice coverage, exam-question associations, classroom/practice planning and progress | Match workbook sheet and column semantics before importing. Tracker is indexing/planning evidence, not authority over ICAI solutions. Do not invent a public Drive URL. |
| **Teacher revision notes** | Per-chapter revision-note source; AS 10 16-page handwritten summary supplied for pilot | Desired visual grammar, compact arrows/tables, memory diagrams, existing illustrative images and last-day revision selection | Inspiration and cross-check, not a substitute for detailed lesson explanations or official accounting references. Register each image as an asset. |
| **Video lessons + revision videos** | **Pending: user to provide the two library URLs or confirm repository/media index paths** | Optional transcript-based clarification of actual spoken teaching order, extra examples, timestamps and recurring stories | Large binary MP4/audio stays outside Git. Extract timestamps and transcript only if accessible; mark unverified transcription and never invent dialogue. |
| **Existing repository material** | `books/ca-inter/concept-book/`, `_claude/skills/`, `AGENTS.md` | Shared characters and stories, existing AS 2 draft, conversion tooling, skills and repo conventions | Reuse, reconcile and improve; never overwrite proven work without diff/review. |

**Access is not completeness.** Folder listing confirms access, not that every standard, notebook, session or revision set is present. For each chapter create a source-inventory record: source ID, original locator, edition/version, filename, page count, checksum (when downloaded), status, verified date and any missing counterpart. Do not place access tokens or private share credentials in Git.

## 3. Existing repository assets — reuse these first

- `books/ca-inter/concept-book/chapters/seq04-as02-valuation-of-inventories.md` and `.html`: existing AS 2 chapter draft; review before creating another.
- `books/ca-inter/concept-book/characters/character_bible_ca_inter_adv_accounts.md`: established shared fictional-character universe.
- `books/ca-inter/concept-book/story-vignettes/story_bank_characters_ca_inter_adv_accounts.md` and `stories-gap-tracker.md`: story registry and identified gaps.
- `books/ca-inter/concept-book/notes_making/README.md`: previous notebook and vector-handwriting recovery; investigate its Excalidraw-compatible approach before rasterizing drawings.
- `books/ca-inter/concept-book/revision-material/`: shared revision assets/index.
- `_claude/skills/concept-book-chapter-writing.md`, `SKILL-concept-book-voice-and-craft.md`, `SKILL-concept-book-thinking-and-reader.md`, `SKILL-html-to-pdf.md`: review and reconcile with the present brief, especially the request to interleave *selected* questions directly after each concept.
- Root `AGENTS.md` and `tools/health_check.py`, `tools/file_index.py`: repo structural checks. Root guidance currently restricts committing binary assets; keep media in the approved external store and commit text-based references/manifests only until the policy is explicitly changed.

## 4. Standard source → book mapping

Establish three linked but distinct sets of records:

1. **Official-topic record**: immutable canonical ID (e.g. `AS10-2.7` only where the supplied edition actually has that numbering), actual title, edition, module/unit, printed page, PDF page, source locator, exact rule/exception summary and linked official illustrations/questions. Never silently apply numbering from another edition.
2. **Teaching-beat record**: stable `AS10-T001` etc., NB01 page(s), annotated ICAI marks, optional timestamped video evidence, lesson position, explanation, story IDs, key diagram/asset IDs, and linked official-topic IDs. A teacher may revisit the same official concept in different lessons.
3. **Question record**: stable `AS10-Q001` etc., original ICAI/other source type and question number, printed/PDF page, NB02 page and teacher solution, topic IDs, teaching-beat insertion point, `in_class_essential | reinforcement | homework`, solution verification status and any open discrepancy. Keep originally stated question numbers and cross-chapter duplicates traceable.

Each final book must provide both directions: **teaching-beat → ICAI topic/question** and **ICAI topic/question → teaching-beat**. Maintain a coverage report for missing ICAI concepts, unclear notebook items, orphaned questions and unlinked media.

### Recommended record shape (illustrative YAML, not a claim that files already exist)

```yaml
chapter: AS10
beat_id: AS10-T012
order: 12
heading: "Directly attributable costs"
icai:
  edition: "May-2027"
  refs: [{section: "2.7", printed_page: "5.28", pdf_page: 8}]
classroom:
  nb01_pages: [6, 8, 9]
  nb02_pages: [1, 2]
  annotated_icai_pages: [8, 9, 10, 11]
stories: [STORY-AS10-IPAD]
assets: [IMG-AS10-READY-TO-USE]
questions: [{id: AS10-Q002, placement: in_class_essential}]
verification: needs_teacher_review
```

The example above demonstrates schema only; independently verify the exact page associations before declaring a record final.

## 5. Repeatable chapter workflow — exact order

**Phase 0 — assignment and isolation.** Integration agent assigns one chapter and one Git branch/PR per worker. Read repo instructions; inspect existing chapter and shared records; check for concurrent work before editing. Prepare acceptance checklist. Never run several agents against the same source file.

**Phase 1 — inventory.** Locate the chapter's four core inputs (unannotated official PDF, annotated official PDF, NB01, NB02), revision notes if available, tracker entries and optional recordings. Record exact source identity, edition and availability. Compare annotated/unannotated versions for mismatched editions. Flag missing materials; do not silently proceed as if complete.

**Phase 2 — one-time extraction and evidence.** Extract printed PDF text/tables once to machine-readable page-tagged text. Visually inspect scanned notebooks, annotated pages and drawings; human/AI transcription must label uncertainties. For optional video, produce time-coded transcript and confidence/unclear spans. Cache extracted artifacts by source checksum; do not repeatedly process unmodified binary files or paste entire PDFs into every agent's context.

**Phase 3 — official topic/question index.** Make the official-edition concept tree, page refs, worked-example/illustration and exercise registry. Reconcile relevant tracker IDs without changing source identifiers.

**Phase 4 — reconstruct classroom order.** NB01 is the primary lesson timeline, NB02 places selected questions at the exact teaching moment, and annotated ICAI notes provide corroboration. The teacher may move back and forth between topics; preserve that intentionally. Produce a reviewable beat-by-beat mapping **before** drafting layouts.

**Phase 5 — stories, characters and assets.** Inspect the shared character bible and story registry for relevant existing scenes, preserve continuity and avoid repetitive plots across standards. Separate teacher-documented classroom stories from newly proposed AI analogies; label proposals as such. Create stable IDs for story scenes and individual visual assets. For an existing image use a manifest record with `asset_id`, filename, external-storage source, licensing/permission, alt text and preferred placement. Use deterministic filename/ID in Markdown; renderer must show a conspicuous missing-asset placeholder rather than silently dropping an illustration.

**Phase 6 — write the teaching beats.** For each beat, write a concise explanation in the teacher's classroom voice, link to the official rule, reproduce the *reasoning* (not unnecessarily copied source pages), add diagram/story/table as needed, insert the selected NB02/ICAI question **immediately after that concept**, show a verified stepwise solution and one examination trap. Put all other questions in after-lesson practice. Mark numerical or source conflicts `needs_teacher_review`; never fabricate the missing answer. Respect third-party material attribution and redistribution permissions.

**Phase 7 — assemble editable source.** Maintain one canonical Markdown/structured content version and one chapter manifest with explicit block types: `concept`, `story-scene`, `decision-tree`, `comparison-table`, `arrow-flow`, `asset`, `worked-question`, `exam-alert`, `revision-wall`. Python parser validates IDs, references and assets before rendering. Avoid designing individual pages manually as the only source.

**Phase 8 — render both editions.** The same validated content feeds (a) clean, accessible, print-friendly HTML and (b) handwritten-style HTML with controlled page geometry, arrows, vector visuals, story backgrounds and readable type. All image paths must resolve through the manifest at build time; keep a local/cache or explicitly approved media-fetch process for offline reproducibility. Print each HTML to PDF using the repository's existing HTML-to-PDF skill. Do not call a flattened raster-image PDF "editable": the HTML/MD and vector source are the editable masters.

**Phase 9 — automated and visual QA.** Validate schema, provenance, cross-reference coverage, question placement and calculations; assert no broken assets, dead links or unresolved template directives. Render every page and inspect thumbnails for collisions, overflow, empty pages, tiny text, poor contrast, detached headings and inconsistent story images. Sample-check official rules/illustrations and independently recalculate numerical answers. Keep an `OPEN_REVIEW.md` of unresolved handwritten ambiguities and teaching decisions.

**Phase 10 — teacher review and release.** Present both editions with a concept/question coverage report and a short change log. Teacher approves content, visual treatment and source decisions. Only then label a release `approved`. Keep draft/approved states explicit; avoid claiming publication-quality completion merely because a PDF rendered.

## 6. Multi-agent boundaries and deliverables

| Role | Owns | Must hand off |
|---|---|---|
| Source curator | Source inventory, edition identity, page-aware extractions, transcript evidence | Source manifest + missing-material report |
| Topic mapper | Official topic and illustration IDs, tracker reconciliation | Official concept/question index + coverage gaps |
| Classroom-sequence agent | NB01 teaching order, NB02 interleaving, annotated corroboration | Sequenced teaching beats + reference map |
| Story/asset agent | Existing cross-chapter story continuity, scene briefs, asset registry, drawing layouts | Scene/asset manifests + flagged proposals |
| Content/solution agent | Explanations and verified immediate questions/solutions | Canonical Markdown + verification issues |
| Renderer/QA agent | Markdown parser, both HTML themes, PDFs, tests and visual QA | Reproducible outputs + reports |
| Integrator | Resolves PR conflicts, checks policy, secures teacher approval | Reviewed merge, release checklist and progress log |

Separate source facts from interpretations and generated additions. Use deterministic IDs and small per-beat inputs to minimize tokens. Run independent agents in separate branches or isolated chapter subdirectories; integration must serialize modifications to shared registries.

## 7. Media/asset resolution contract

Suggested chapter and shared text files, added incrementally and only after inspecting what already exists:

```text
books/ca-inter/concept-book/
  NEWTON_CONCEPT_BOOK_PRODUCTION_GUIDE.md
  chapters/                                # existing chapter MD/HTML; add AS10 only after checking collision
  characters/                              # existing canonical universe
  story-vignettes/                         # existing shared stories and gap tracker
  revision-material/                       # existing shared revision area
  [future] manifests/                      # text-only source, story, question, asset registries if approved
  [future] renderer/                       # Python, templates, CSS and reproducible tests if approved
```

Use source-controlled manifest entries such as:

```yaml
asset_id: IMG-AS10-READY-TO-USE
filename: as10-ready-to-use-scene.png
storage: external_media
source_locator: "TO_BE_REGISTERED"
alt: "Timeline showing when expenditure stops being capitalised"
placement: AS10-T012
rights: needs_check
status: missing
```

HTML must render by resolved asset path, not by an arbitrary image search each run. Do not embed private Google Drive session URLs or binary media directly in source control. Test with a clean checkout and a documented asset-sync/cache step.

## 8. Pilot acceptance gates

Complete **AS 10** and **AS 2** independently end-to-end before generalizing to other chapters. AS 2 has an existing chapter draft; AS 10 has prior standalone prototypes that are **not automatically the repo's authoritative release**. For each pilot require:

- Four-core-source inventory, version reconciliation and complete topic-to-lesson and lesson-to-topic maps.
- Verified NB02 classroom question placement and selected worked solutions; a clearly separate practice set.
- Shared-story/character continuity review and chapter-specific story/image manifests, with no silent repetition.
- Canonical editable Markdown → both HTML editions → corresponding PDFs, reproducible from a clean environment.
- Revision-wall content informed by the teacher's summary, not used as a replacement for concept lessons.
- Automated tests, human review of every rendered page and no unflagged source/number ambiguities.
- Instructor sign-off and a documented list of improvements to freeze for other chapters.

## 9. Git policy and required end-of-task checks

Commit text documentation, templates, manifest and code; follow root `AGENTS.md` restrictions on binary files and credentials. Prefer PR review for substantial changes. After **structural** changes, run `python tools/health_check.py`, then `python tools/file_index.py`, as instructed in the repo, and record the outcome; do not claim a local CI run if working only via remote connector. Record decisions, new blockers and approved amendments in the repository's existing progress log. This document is an initial guide, not permission to reorganize existing folders or edit the connected Drive originals.

## 10. Known open inputs / decisions

1. User to supply or confirm exact **revision-video** and **full lecture-video** library links or existing repository media-index paths; only then start timestamped transcription.
2. For each chapter, locate and validate the matching revision-note PDF and the matching four core source files; Drive folder listing alone is insufficient.
3. Decide whether shared manifest and renderer directories should be added under this concept-book tree or reuse existing broader pipeline code; first inspect and test existing scripts.
4. Reconcile legacy branding/author metadata in existing files **before** reusing that wording in newly rendered notes, without silently altering unrelated historical files.
5. Resolve any discrepancy between existing story-first chapter templates and the required interleaved **concept → selected in-class question** sequence. A chapter may keep an opening hook, but in-class worked questions must still appear at their teaching beats.
6. Establish how media is stored/synced and its redistribution rights, particularly official text excerpts and third-party images.

**Operating rule:** when a source reference, handwritten figure, video claim, image permission or existing repository instruction is unclear, flag the exact item and ask; accuracy, reproducibility and the teacher's actual classroom sequence take priority over filling every page.
