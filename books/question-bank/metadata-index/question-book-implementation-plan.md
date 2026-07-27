# Question Bank Book — Implementation Plan

Goal: a single book per chapter (starting with AS 2, AS 10) covering every question + answer in the MTP/RTP/PYQ/ICAI-Practice question bank, topic-tagged against the ICAI syllabus's own numbering, with marks, estimated time, OP/PP duplicate linking, comprehensive-question flagging, a rubric ("Important Computational Steps"), and "Common Student Mistakes" — built cost-effectively by splitting work across three tiers instead of running everything through a premium model.

**Roles, as agreed:**
- **Tier 1 (deterministic → Python)**: spec written by Claude, code written by GitHub Copilot / Gemini in VS Code (not Claude).
- **Tier 2 (40–90% deterministic → cheap/free model)**: prompt written by Claude, run by the user via Blackbox / Copilot / Gemini in VS Code, output brought back to Claude.
- **Tier 3 (creative/high-stakes/review → Claude)**: done directly by Claude.
- **OCR (scanned PDFs)**: a dedicated OCR tool, not an LLM at all — cheaper and more accurate for pure transcription.

---

## Phase 0 — Master Topic Keyword Index (all 36 units, built first, in 3 batches by ICAI chapter number)

**Why first:** every downstream tagging step (including cross-chapter tagging for comprehensive/integrated questions) depends on this existing and being accurate. Doing it once, up front, for all 36 units avoids re-deriving keywords chapter-by-chapter later.

**Batching (rebalanced 2026-07-20 — supersedes the original 1-5/6-10/11-15 split):** ICAI has 15 numbered chapters, but several chapters contain multiple units (one per Accounting Standard), so splitting by raw chapter number is uneven. The rebalanced split below is more even (10/17/9 vs. the original 17/13/6) but Batch 2 remains the largest since Chapter 5 alone (7 units, incl. AS 2 and AS 10) sits there:

| Batch | ICAI Chapters | Units in batch | Units |
|---|---|---|---|
| **Batch 1** | 1–4 | **10** | M1-C1-U0 (Intro to AS), M1-C2-U0 (Framework), M1-C3-U0 (Applicability), M1-C4-U1 (AS1 Disclosure of Accounting Policies), M1-C4-U2 (AS3 Cash Flow Statement), M1-C4-U3 (AS17 Segment Reporting), M1-C4-U4 (AS18 Related Party), M1-C4-U5 (AS20 EPS), M1-C4-U6 (AS24 Discontinuing Ops), M1-C4-U7 (AS25 Interim Reporting) |
| **Batch 2** | 5–9 | **17** | M2-C5-U1 (AS2 Inventory — *audited*), M2-C5-U2 (AS10 PPE — *audited*), M2-C5-U3 (AS13 Investments), M2-C5-U4 (AS16 Borrowing Costs), M2-C5-U5 (AS19 Leases), M2-C5-U6 (AS26 Intangibles), M2-C5-U7 (AS28 Impairment), M2-C6-U1 (AS15 Employee Benefits), M2-C6-U2 (AS29 Provisions), M2-C7-U1 (AS4 Contingencies), M2-C7-U2 (AS5 Prior Period Items), M2-C7-U3 (AS11 Forex), M2-C7-U4 (AS22 Taxes on Income), M2-C8-U1 (AS7 Construction Contracts), M2-C8-U2 (AS9 Revenue Recognition), M2-C9-U1 (AS12 Govt Grants), M2-C9-U2 (AS14 Amalgamations) |
| **Batch 3** | 10–15 | **9** | M2-C10-U1 (AS21 Consolidated FS), M2-C10-U2 (AS23 Associates), M2-C10-U3 (AS27 Joint Ventures), M3-C11-U1 (FS Preparation), M3-C11-U2 (Cash Flow Statement — company), M3-C12-U0 (Buyback), M3-C13-U0 (Amalgamation of Companies), M3-C14-U0 (Internal Reconstruction), M3-C15-U0 (Branches incl. Foreign) |

**Sequencing note:** AS 2 and AS 10 now fall in Batch 2, not Batch 1 (they moved when the split was rebalanced). Decision (2026-07-20): don't fast-track Phase 1 for AS 2/AS 10 ahead of the rest of Batch 2 — wait until all 17 Batch 2 units finish Phase 0, then run Phase 1 for the whole batch together, so lessons learned across the batch (keyword-quality calibration, prompt refinements) get applied uniformly rather than AS 2/AS 10 being processed under an earlier, less-refined version of the pipeline.

**OCR pipeline — finalized and verified working (2026-07-20):** Tesseract 5.5.0 confirmed installed (`C:\Program Files\Tesseract-OCR\tesseract.exe`; needs a fresh terminal to pick up PATH — this session's shells predate the PATH update). Using **PyMuPDF (`fitz`) + `pytesseract`** instead of the originally-planned `pdf2image` + Poppler route — `fitz` renders PDF pages to images natively (already installed and working from the AS 10 audit), so no separate Poppler binary is needed at all. Verified end-to-end on page 1 of the ICAI-Practice compilation — output matched the known front-matter text exactly. Reference snippet:
```python
import fitz, pytesseract
from PIL import Image
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
doc = fitz.open(pdf_path)
mat = fitz.Matrix(3, 3)  # 3x scale for OCR accuracy
pix = doc[page_num].get_pixmap(matrix=mat)
img = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
text = pytesseract.image_to_string(img)
```

**Tier split:**
- **Tier 2 (Gemini/Copilot, prompt below):** first-draft keyword extraction, one run per chapter (36 runs), using the chapter's already-known topic list from `0-ca-inter-adv-accounts-subtopics-marks-weightage.json` as the topic scaffold.
- **Tier 3 (Claude):** review pass across all 36 chapters' drafts — spot-check against the two chapters already audited in depth (AS 2, AS 10) as calibration, fix any topic where keywords are too generic/wrong, and add the "unnumbered sections" (like AS 10's post-2.10 content) that the taxonomy JSON doesn't capture.

**Output:** ONE single JSON file (not per-chapter), e.g. `books/question-bank/metadata-index/topic-keyword-index.json`, schema:

```json
{
  "meta": {
    "source": "Built from 0-ca-inter-adv-accounts-subtopics-marks-weightage.json + direct reading of each unit's source material",
    "generated_on": "YYYY-MM-DD",
    "coverage_chapters": "0/36",
    "unnumbered_topic_convention": "Sections with no ICAI-assigned number get sequential IDs continuing from the last real number, suffixed with an asterisk, e.g. M2-C5-U2-T2.11* — flagged as author-assigned, not ICAI-numbered."
  },
  "topics": {
    "M2-C5-U1-T1.7": {
      "chapter_id": "M2-C5-U1",
      "chapter_name": "AS 2 Valuation of Inventory",
      "topic_name": "Joint or By-Products",
      "keywords": ["joint product", "by-product", "split-off point", "NRV of by-product", "scrap value", "joint cost allocation"],
      "typical_question_signals": [
        "by-product X is sold at ₹Y per unit",
        "two/three products emerge from a common process",
        "closing inventory of [main product A] and [main product B]"
      ],
      "notes": ""
    }
  }
}
```

**Phase 0 prompt (run once per chapter in Gemini/Copilot, 36 times total):**

> You are extracting a keyword/concept index from one unit of the ICAI CA-Inter Advanced Accounting study material, to help a later automated step match real exam questions to this specific unit/topic.
>
> Read the attached file: `[path to the unit's source .md/.pdf]`
>
> This unit's known topic breakdown (topic ID → topic name → page) is:
> `[paste the relevant "topics" array for this chapter from 0-ca-inter-adv-accounts-subtopics-marks-weightage.json]`
>
> For EACH topic ID listed above, extract:
> 1. 5–12 keywords/technical terms that a question testing *specifically this topic* would likely use. Be specific — avoid generic accounting terms that could apply to any chapter (e.g. "cost", "value" alone are too generic; "fixed overhead absorption at normal capacity" is specific).
> 2. 2–4 "typical question signal" phrasings — short example phrasings showing how a real exam question testing this topic tends to be worded.
> 3. If the unit's actual content extends beyond the last numbered topic listed above (i.e. there are unnumbered sections in the ICAI source text after the last numbered one), list these as additional topics with sequential IDs continuing from the last number, each suffixed with an asterisk (e.g. if topics stop at T2.10, use T2.11*, T2.12*...), and note `"unnumbered in ICAI source"`.
>
> Do NOT invent concepts not actually present in the attached file — only extract what's genuinely there. If a topic is purely theoretical/definitional with no computational angle, say so explicitly rather than forcing a fake "typical question" example.
>
> Output as JSON matching this exact schema: `[paste schema above]`

---

## Phase 1 — Extract every question + answer as clean, structured text

**Tier split:**
- **OCR tool (not LLM), confirmed choice: Tesseract.** Convert the scanned/image-only PDFs (ICAI-Practice compilation Q+Ans, blank-MD PYQ-Q files) to text first.
- **Tier 2 (Gemini/Copilot, prompt below):** split each paper's raw text into individual question objects (question text, answer text, printed marks if any, page markers), for both OCR output and the already-clean `.md` files.
- **Tier 1 (Python, Copilot-written):** normalize the JSON output across all source files into one consistent schema; flag any file where question/answer counts look mismatched (e.g. 6 questions in Q but 5 in Ans) for Tier 3 review rather than silently guessing.

**Tesseract install (Windows 11, this machine):**
1. Download the installer from the official UB-Mannheim build (the maintained Windows build of Tesseract): `https://github.com/UB-Mannheim/tesseract/wiki` — grab the latest `tesseract-ocr-w64-setup-*.exe`.
2. Run the installer. Default install path is `C:\Program Files\Tesseract-OCR`. During setup, make sure the **English** language data is selected (default) — CA study material is English-only, no extra language packs needed.
3. Add Tesseract to PATH: either check "Add to PATH" during install, or manually add `C:\Program Files\Tesseract-OCR` to the system PATH afterward (Settings → System → About → Advanced system settings → Environment Variables).
4. Verify from a fresh terminal: `tesseract --version` should print the version (5.x) — open a new shell first, PATH changes don't apply to already-open terminals.
5. Since the inputs are PDFs, not raw images, Tesseract alone isn't enough — it needs page images first. Two options:
   - **`pytesseract` + `pdf2image`** (Python wrapper route — recommended, ties in with the Python tooling already used for PyMuPDF rendering in this project): `pip install pytesseract pdf2image`. `pdf2image` needs Poppler for the PDF→image step — same family of tool that was missing earlier in this session (`pdftoppm`); install via the same UB-Mannheim-style approach or `conda install poppler`, and add its `bin` folder to PATH too.
   - **Direct CLI route**: render pages to PNG first (already have a working PyMuPDF-based script pattern from this session), then run `tesseract page1.png out1 --psm 6` per page and concatenate.
6. Quick smoke test before running it across the whole question bank: OCR just page 1 of `CAInter-AdvAcc-MTP-ICAI-Practice-Q.pdf` and visually compare against the known front-matter table of contents (already read once in this session) to confirm output quality before committing to the full run.

**Output:** one JSON per source paper, e.g. `extracted/CAInter-AdvAcc-MTP-Jan2025-Set1.json`, schema:

```json
{
  "sourceFile_Q": "CAInter-AdvAcc-MTP-Jan2025-Set1-Q.pdf",
  "sourceFile_Ans": "CAInter-AdvAcc-MTP-Jan2025-Set1-Ans.pdf",
  "attempt": "Jan 2025",
  "paperType": "MTP",
  "set": "Set 1",
  "questions": [
    {
      "qNoInPaper": "1(b)",
      "type": "Descriptive",
      "printedMarks": 5,
      "pageQ": 3,
      "pageAns": 2,
      "questionTextHtml": "...",
      "answerTextHtml": "..."
    }
  ]
}
```

**Phase 1 prompt (run per source paper):**

> You are extracting individual questions and their official answers from one CA Inter Advanced Accounting exam paper (ICAI MTP/RTP/PYQ format), for a structured question bank.
>
> Question source: `[Q file text/OCR output]`
> Answer source: `[Ans file text/OCR output, or the later "solutions" section if this is a self-contained RTP]`
>
> For every question in the Question source, produce one JSON object with: `qNoInPaper` (exactly as printed, including sub-parts like "1(b)"), `type` (MCQ-Direct / MCQ-Scenario / Descriptive — infer from structure: 4 lettered options = MCQ; a "Case Scenario"/"based on the following" heading grouping several questions = MCQ-Scenario; otherwise Descriptive), `printedMarks` (the exact number if stated, else `null` — do not guess), `pageQ` (the physical page this question is on), `questionTextHtml` (the full question text, HTML-formatted with `<table>`/`<tr>`/`<td>` for any tabular data, preserving all numbers exactly as printed).
>
> Then find that SAME question's answer independently in the Answer source (never assume it's on a predictable page — actually locate the matching solution by content), and add `pageAns` and `answerTextHtml` to the same object.
>
> If a question's answer cannot be found at all in the Answer source, set `answerTextHtml` to `null` and add `"answerNotFound": true` rather than leaving a guess.
>
> Output the full paper as one JSON array matching this schema: `[paste schema above]`

---

## Phase 2 — Topic tagging

**Tier split:**
- **Tier 2 (Gemini/Copilot):** first-pass tag suggestion — match each question's text against `topic-keyword-index.json`, output candidate topic ID(s) + a confidence note.
- **Tier 3 (Claude):** review every tag the cheap pass flags as low-confidence, PLUS spot-check a sample of high-confidence tags for the known false-positive traps (FIFO-for-investments ≠ AS 2, depreciation-as-CFS-addback ≠ AS 10, etc. — maintained in a running Trap List, seeded from the AS 2/AS 10 audits).

**Output:** adds a `topicTags: ["M2-C5-U1-T1.7", ...]` array (plus `comprehensiveQuestion: true/false` once ≥3 tags, computed in Tier 1 Python) to each question object from Phase 1.

## Phase 3 — Metadata completion (Tier 1, Python)
- Estimated time = `printedMarks × 1.8` (skip if marks unknown until Phase 4 resolves it).
- MCQ default marks = 2 where `printedMarks` is null and `type` starts with "MCQ" (empirically near-universal across every paper audited so far).

## Phase 4 — OP/PP duplicate detection (Tier 1, Python — fully deterministic, no AI)
- Within each topic-tag cluster, compare `questionTextHtml` pairwise with digits/currency stripped out (`difflib.SequenceMatcher` or token-Jaccard). ≥95% similarity → same cluster.
- Earliest attempt (per `attempt_labels_in_order` from the taxonomy JSON, or by MTP/RTP/PYQ date parsing) = OP; rest = PP with a `opQuestionRef` pointer.
- For any PP question where `printedMarks` was null, inherit the OP's marks and label it `"marksSource": "inherited from OP"`; if the OP also has no marks, label `"marksSource": "author-guessed"` and still apply a value so the time estimate can compute — never leave it silently blank.

## Phase 5 — Rubrics ("Important Computational Steps") — Tier 3 only, not delegated
Given these will later drive AI-based grading of student answers, quality matters more than cost here. Claude reads the question + official answer and produces a step-wise mark allocation, explicitly labeled `"rubricSource": "author-inferred, not ICAI-published"` unless the source answer already shows an official breakdown.

## Phase 6 — Common Student Mistakes
- **Tier 2 draft** for routine/single-topic questions (prompt derived from the same pattern used manually in the AS 2/AS 10 tables — concrete, tied to the specific numbers in that question, never generic filler).
- **Tier 3 authors directly** for every comprehensive-flagged question (≥3 topics) and reviews/edits every Tier 2 draft before it's published.

## Phase 7 — Book assembly (Tier 1, Python/Copilot — pure templating once all fields exist)
One flowing document per chapter: Q.N → metadata block → question → answer → Important Computational Steps → Common Student Mistakes, ordered by topic sequence (1.1 → 1.15, 2.1 → 2.10*, etc.), OP question followed immediately by its linked PP questions.

## Phase 8 — Final QA (Tier 3, Claude)
Spot-check page numbers against actual source PDFs, re-run the false-positive trap list across the finished book, confirm no question was silently dropped between phases (count reconciliation: questions found in Phase 1 = questions present in the final book).

---

## Open items before starting

1. Which of Blackbox / Copilot / Gemini is best suited to which phase? (My guess: Gemini for the large-context reading tasks — Phase 0 keyword extraction, Phase 1 splitting — since it handles long documents well; Copilot for anything that's actually code generation, being IDE-native; unclear where Blackbox fits best — your call once you've tried a phase with each.)
2. Confirm OCR tool choice (Tesseract locally vs. a cloud OCR API) — affects the Phase 1 prompt's input format.
3. Should Phase 0 run all 36 chapters before Phase 1 starts on even one chapter, or can they interleave per-chapter (Phase 0 for AS 2 → Phase 1 for AS 2 → ... while Phase 0 for AS 10 runs separately)? Interleaving would let the AS 2/AS 10 books finish sooner without waiting on all 34 other chapters' keyword indexes.
