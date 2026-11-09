# CA Foundation Accounting — agent handoff

Updated: 2026-10-20. Start here before continuing the concept book. This records the work and decisions from Pranav's planning conversation; it does not claim a completed book or completed exam-question mapping.

## 1. User requirements and scope

- Pranav is an ICAI faculty member moving from CA Inter Advanced Accounts into Foundation Paper 1 Accounting teaching.
- Build a concise concept book that includes **all chapters and all applicable concepts**. Compression must not become selective syllabus coverage.
- The first requested deliverable was a chapter/unit/topic list with page references, modeled on his CA Inter topic tracker. That list is completed at detailed-contents-heading level only.
- Primary content/provenance: ICAI sources only. Historical CPT/Foundation Accounting material can be retained, with an original 15-year archive cutoff of 2011-10-04. Never mix old-scheme content into the current book without an applicability check.
- Preferred filename prefix: `CA_L1_P01_M1_C1_U5`; use U0 when there is no numbered unit. Keep names short; Acc = Accounting, Reco = Reconciliation, Stat = Statement.
- Preferred local archive root: `D:\Local_CACSCMA_RAG_Master`, configurable by the downloader. Study material, Question bank and Reference are direct child folders. Manual upload to Drive remains the requested workflow.

## 2. Sources: keep these three spreadsheets distinct

| Source | What it owns | What it does not establish |
|---|---|---|
| [Foundation topic master](https://docs.google.com/spreadsheets/d/1a_faP38UZan5QSHDiZeRUnB4TxngHuPdwsAnGCbBMtE/edit) | 229 numbered TOC headings, IDs, pages and source links | Complete body-level concepts, importance ranking or exam frequency |
| [Original download inventory](https://docs.google.com/spreadsheets/d/1FxNpBF5_CI2FVw2lQ7a3w8r8AchIFzcJdlVOB7Gjy7A/edit) | 331 document URLs, 330 enabled at original checks; four-column Downloader Master | A finished local archive or a topic inventory |
| [CA Inter reference tracker](https://docs.google.com/spreadsheets/d/1sPM8QUsTr7wf2btEsUiX5v00l_BSqOfvWRiXNokM_84/edit) | Reference structure for topic IDs, pages and later importance/question mapping | Foundation importance, marks or topic evidence |

Read the current exact source before making new claims or refreshing snapshots. This handoff does not authorize an agent to edit the live Sheets without a user instruction to do so.

## 3. What has actually been completed

1. Official-document download inventory and shallow naming plan; runnable [download_icai_pdfs.py](download_icai_pdfs.py), [requirements](requirements-downloader.txt) and [download specification](DOWNLOADER-SPEC.md) already exist.
2. Existing shared [PDF-to-Markdown converter](../../tools/icai_pdf_to_md_converter.py) is documented; it writes Markdown beside each PDF with the same basename. Raw extraction still needs table/formula/OCR review.
3. The Foundation topic master was created on 2026-10-18 using the English **May 2026-onward** listing, August 2024 edition / August 2025 reprint. The separate May 2027 edition was not used.
4. All five live tabs were re-read on 2026-10-20 and preserved in [topic-master/](topic-master/README.md): 229 topic rows, 33 source sections (27 numbered units plus six U0 chapters), 11 chapter rows, 132 learning/overview/summary/test entries and 25 README records.
5. A teaching sequence, official grouped-weightage explanation, illustrative 200-hour allocation, and compressed date-wise plan were proposed in the conversation. See [TEACHING-PLAN.md](TEACHING-PLAN.md) and [teaching-plan.csv](teaching-plan.csv).

The topic master contains the first seven columns of the reference structure, then Foundation identifiers, source/evidence links, edition and assessment status. Topic/page values are text: `1.10` must never become `1.1`.

## 4. Limits that every agent must preserve

- **229 is a count of numbered detailed-TOC headings, not a count of every individual concept.** Broad headings hide sub-concepts, methods, exceptions and treatments that must be extracted from the body.
- Importance is **Not assessed** throughout the current snapshot; blank evidence is unknown, not zero marks or evidence that a topic is unimportant.
- No Foundation PYQ/MTP/RTP question-to-topic mapping or historical chapter-wise marks analysis has been completed here.
- Official weightages apply to grouped sections. Do not label Chapters 2–6 individually as 30–35 marks each, or Chapters 7–9 as 20–25 marks each.
- No Foundation concept-book chapter has been drafted in this conversation. No final layout, page target, character cast or example policy has been approved for this book.
- Arjun's stationery business, linked side cases and the teaching sequence are assistant proposals, not user-approved fictional facts or a locked design.
- The 41-lecture timetable is a fast-track proposal; it is not proof that a beginner can master the full syllabus in 61.5 hours.
- A complete local download/manual Drive upload of the 331-row plan has not been confirmed. Existing curated Markdown/retrieval files do not prove full inventory coverage.
- Existing `icai-smaterials-md/` and `CA_Foundation_Offline_Retrieval_Engine_SMAT/` contain separate curated downstream work. Read their own instructions, inspect edition/provenance, and do not overwrite them with raw extraction or this snapshot.

## 5. Next work: inputs, output fields and acceptance criteria

### A. Expand headings into body-level sub-concepts

**Inputs:** `topic-master/topics.csv`, `units.csv`, official unit PDFs from their source URLs, the chosen exam attempt/edition and applicable corrigenda. The source Initial Pages PDFs are linked in the Sheet README and each row's TOC evidence link. Do not infer concepts from a title alone.

**Proposed output:** a separate `concepts.csv` (not created/populated yet) with `concept_id`, `parent_topic_id`, `module_no`, `chapter_no`, `unit_no`, `concept_title`, `rule_or_treatment`, `conditions_exceptions`, `printed_page_start`, `printed_page_end`, `source_pdf_url`, `example_refs`, `review_status`, `review_notes`.

Preserve all 229 parent IDs; do not renumber them when splitting a topic. A child can use `<parent_topic_id>_S01`. Keep page strings literal. Record unnumbered body concepts explicitly and explain their chosen parent. Every parent needs either verified child coverage or a documented reviewed reason why no split is necessary. A verified statement must be traceable to the chosen edition, not generated solely from model memory.

### B. Link importance to exam evidence

**Inputs:** official Foundation PYQ/MTP/RTP papers and solutions, topic master and expanded concepts.

**Proposed output:** a separate question-to-topic mapping with `paper_label`, `attempt`, `paper_type`, `question_no`, `sub_part`, `or_alternative`, `question_marks`, `topic_id`, `allocated_marks`, `allocation_method`, `source_url`, `review_status`.

One question can span multiple topics. Define allocation and optional-question counting rules before calculating ranks; avoid double counting. Preserve unknown marks as blank. Any faculty-priority judgment must be labeled separately from exam-derived evidence. This is pending work, not completed analysis.

### C. Draft and audit the concept book

After the coverage expansion, draft concise explanations of all applicable concepts with treatment logic, required formats/formulas, exceptions and carefully chosen short examples. This is a suggested chapter pattern, pending Pranav's editorial direction. Retain original ICAI chapter/unit numbering for navigation even if the teaching order differs. Maintain a coverage map from every concept ID to the draft section so summarization cannot silently remove concepts.

Do not invent a fixed page cap or delete topics to fit the timetable. Confirm the target exam attempt and resolve edition changes before locking the manuscript. Question-bank importance may guide emphasis, not omission.

## 6. Continuation prompt for another agent

Read root AGENTS.md and books/ca-foundation/AGENT-HANDOFF.md, topic-master/README.md and TEACHING-PLAN.md. Inspect existing curated Foundation work before changing anything. Use the 2026-10-20 topic snapshots as the versioned starting point; re-read the exact live Sheet if freshness affects your task. Begin by auditing one chapter's source PDF against its TOC rows and creating a traceable body-level concept expansion, preserving all parent IDs. Do not claim 229 headings are full micro-concept coverage or invent Foundation exam ranks. Keep edits within the assigned chapter, state remaining gaps, run required checks, and open a PR under current repo rules.

## 7. Other inputs still needed before final book design

Pranav's exact target exam attempt; whether this is the primary classroom book or revision companion; final language/tone/layout; permissible length; treatment of illustrations versus short examples; and how the classroom writing/annotation space should work. Until specified, preserve coverage and avoid silently locking these choices.
