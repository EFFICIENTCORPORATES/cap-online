---
name: 1lavya-faculty-onboarding-model
description: "1LAVYA's faculty roster, the flat ₹5,000 onboarding fee, and the real content-heterogeneity problem across faculty (each brings wildly different material)"
metadata: 
  node_type: memory
  type: project
  originSessionId: eff70d38-31a6-4cc7-baf2-a93b1aa25479
  modified: 2026-08-09T12:41:18.598Z
---

**Faculty onboarded so far** (as of 2026-08-09), see [[1lavya-platform-entity-structure]]
for the entity context:
1. **CA Pranav Pratik Tulshyan** — faculty #1. Teaches Advanced Accounts, CA Inter
   (may expand to CA Foundation/Final later).
2. **CS Arun Chouhan** — faculty #2. Teaches Law to CMA Foundation and CMA
   Intermediate.

**Commercial terms:** every faculty pays a **flat one-time ₹5,000** to 1LAVYA. This
buys them two things: (a) their students get free access to a **limited slice** of
1LAVYA's shared exclusive content (not full/unrestricted), and (b) the right to
**publish their own content** through their branded bot. This is distinct from the
separate **student-side MCQ usage billing** (100 free MCQs/month per student, then
₹1/100 MCQs to recharge — likely sold as prepaid credit packs, not literal ₹1
transactions, since gateway fees alone would exceed that) — the ₹5,000 is a faculty
onboarding fee, not related to MCQ metering.

**Real, confirmed content-heterogeneity problem** — the catalog/schema work has to
tolerate this, not assume every faculty supplies all 3 categories (Study/Exam/
Revision):
- **CA Pranav** gave only **2 Study Resources**, both Revision-Material-style
  handwritten-notes PDFs (AS02 Inventory, AS10 PPE) — no Study Materials, no Exam
  Materials of his own. For exam content his students rely **entirely on 1LAVYA's
  shared exclusive content**.
- **CS Arun Chouhan** gave **zero Study Hub materials** at all. He supplied only Exam
  Materials: MCQs as separate topic-wise **Word (.docx) files** (e.g.
  `Factories_Act_50_MCQs_June2026.docx`), plus **one descriptive Q&A PDF**
  (`descp-companies-act.pdf`, Companies Act, CMA Inter only — CMA Foundation has no
  descriptive content from him, MCQs only).

**On-disk convention** (established this session, 3 folders exist today):
`telegram/assets/faculty/{facultyslug}-{course}-{level}-{subjectslug}/`, e.g.
`capranav-ca-inter-advacc`, `csarunchouhan-cma-found-law`,
`csarunchouhan-cma-inter-law` — raw faculty-supplied source files land here
unprocessed (PDFs, .docx), before any extraction/catalog pipeline touches them. A
`exam-mcq/` subfolder is the pattern seen so far for MCQ-only Word-doc submissions.

**Implication for the catalog/build work**: the "standard catalog" being planned must
be schema-flexible per faculty (any category can be legitimately empty for a given
faculty) and needs new extraction tooling for **.docx-sourced MCQs** — the existing
`tools/*.py` pipeline (icai_pdf_to_md_converter.py, etc.) is PDF-only; nothing yet
parses Word docs into structured MCQ records.
