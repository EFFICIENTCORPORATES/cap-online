# SKILL — Question Bank Summary Making

> **Scope:** Building an accuracy-first, topic-tagged reference of every question in the
> CA Inter Advanced Accounting question bank (`books/question-bank/Raw_PDF_Question_Bank_CA_Inter_Accounts/`)
> that tests a given Accounting Standard / chapter topic. Use this skill whenever asked to
> "find all questions on [topic]", "make a topic-wise summary", "which topic is most asked",
> or to extend/refresh the reusable `books/question-bank/metadata-index/topic-index.json`.
> Built from the AS 2 (Valuation of Inventories) audit — see
> `books/question-bank/metadata-index/AS2_Question_Reference.html` as the worked example
> of the expected final deliverable shape.

---

## 0. The one rule that overrides all others

**No hallucination.** Every page reference, mark value, and topic-number citation in the
final output must trace back to text you actually read in this session — never inferred,
never copied from a prior AI-generated list without re-verification, never guessed because
"it's probably right." If you didn't verify it, say so explicitly in the output rather than
presenting a guess as fact. A student will study from this — a wrong page reference wastes
their time; a fabricated mark value misleads their prioritization.

---

## 1. Where the study material topic structure lives

- Base ICAI study material: `books/concept-book/raw_icai_study_materials/`
- File naming: `M{module}_C{chapter}_U{unit}_ {Title}.pdf` and its `.md` sibling
  (e.g. `M2_C5_U1_ Accounting Standard 2 Valuation of Inventory.md`).
- **Always read the actual unit `.md` (or `.pdf` if `.md` is missing/blank) in full before
  writing down its numbered sub-topic structure.** Do not infer sub-topic numbering from a
  chapter's table of contents, from memory of the standard, or from a previous incomplete
  pass — ICAI's own numbering (e.g. `1.1`, `1.2`, ... `1.15`) must be read off the actual
  document headings verbatim.
  - Past mistake to avoid: an earlier pass bundled sections `1.4` through `1.8` into one
    fake combined entry ("Costs of Inventory / Purchase / Conversion / Joint-By-products /
    Other Costs") because a background agent summarized rather than enumerated. This was
    caught only when the user asked for a topic-wise table and the bundling became visibly
    wrong. Always enumerate every numbered heading separately.
- Page numbers in these unit documents follow the `chapter.page` convention printed in the
  book itself (e.g. `5.6`, `5.7`) — these ARE reliable printed page numbers (unlike the
  question-bank PDFs, see §3) because the ICAI textbook page footer/header survives OCR
  conversion cleanly. Cite them as printed.
- The reusable index file `books/question-bank/metadata-index/topic-index.json` stores this
  once per unit (`unitCode`, `sections[]` with `ref`/`heading`/`page`/`description`) so it
  doesn't need re-reading every time. **Before trusting an existing entry, sanity-check that
  every `ref` looks like a single atomic sub-topic number, not a bundled range** — if you see
  a range like `"1.4-1.8"` in an existing entry, treat it as unverified and re-read the
  source to split it properly, updating the file via `Edit` (see `_readme` field for edit
  history convention — keep it current when you add/fix units).

## 2. Where the question bank lives, and its structural landmines

- Folder: `books/question-bank/Raw_PDF_Question_Bank_CA_Inter_Accounts/`
- Manifest: `books/question-bank/question_bank_index.csv` — **read this first**, every
  time. It tells you which `.md` conversions are blank/corrupted (2-byte files) and must be
  read directly from the source `.pdf` instead, and it is the fastest way to see the full
  file inventory without listing the directory blind.
- File families and their structural differences (do not assume uniformity):
  - **MTP** (Mock Test Papers): separate `-Set1-Q` / `-Set1-Ans` / `-Set2-Q` / `-Set2-Ans`
    files per attempt.
  - **RTP** (Revision Test Papers): a single `-Q` file containing BOTH the questions and
    their solutions in one document (solutions appear later in the same file). There is no
    separate `-Ans` file for RTPs — don't go looking for one.
  - **PYQ** (Past Year Questions): inconsistent across attempts — some have both Q and Ans,
    some have Ans only (no Q paper was ever scanned for that attempt), at least one observed
    attempt has Q only with no Ans at all. **Check the manifest per attempt; do not assume
    symmetry.** Where a Q or Ans document genuinely does not exist, say so explicitly in the
    output ("N/A — no separate Question paper for this attempt") rather than citing the
    other document's page for both, and never silently substitute one for the other.
  - **Compiled/mega-PDFs** (e.g. an "ICAI-Practice" bundle containing multiple mock papers
    in one file): often the largest files by byte size specifically *because* they are
    scanned image PDFs with no text layer (that's usually *why* the `.md` conversion came
    out blank — large file size + blank text extraction together are a strong signal of a
    scanned/image-only PDF, not a hint that it's simply a long document). These need either
    OCR-by-screenshot (render page images and read them visually — install PyMuPDF if
    `pdftoppm`/poppler isn't available) or, if the compiled PDF has a table of contents page,
    read that first — it usually gives exact printed-page start-points for each embedded
    paper, which is far cheaper than a blind page-by-page sweep.
- **Page-number reliability differs by source type** — be explicit in the final output about
  which convention was used for which row:
  - Individual MTP/PYQ/RTP PDFs are generally small enough to page through directly with
    `Read(pages=...)` if precision is required — this gives an authoritative printed page
    number (or physical page count if unprinted).
  - Where full PDF paging is skipped for speed (see §6), fall back to citing the `.md` line
    number instead, and say so plainly in a methodology note rather than presenting a line
    number as if it were a PDF page.
  - Never estimate a page number by "footer counting" (counting recurring boilerplate lines
    like a copyright footer) as a substitute for real verification unless you have already
    spot-checked that the footer reliably marks one-page-per-occurrence in that specific
    file — it's a weak heuristic, not a citation-grade method.

## 3. Search methodology — don't trust a single keyword sweep

1. Start with a broad `Grep` sweep across all `-Q.md` (and self-contained RTP) files using
   every synonym/phrasing you can think of for the topic (formula names, defined terms,
   common scenario nouns) — this produces a **candidate file list only**, not a final answer.
2. **Do a full read-through of each candidate file**, not just the matched lines — exam
   questions frequently test a concept inside a sub-part of a larger multi-part question
   without using the standard's jargon at all (e.g. a question about "provision for
   non-moving inventory" tests AS 2/AS 1 without ever saying "NRV" or "FIFO"; a keyword
   sweep tuned to standard vocabulary will silently miss it).
3. **Actively hunt for files that returned zero matches but which context suggests should
   have content** (e.g. a paper from an attempt where every sibling paper tested the topic).
   A zero-match file is not proof of absence — broaden the search terms and/or read the file
   directly before concluding the topic wasn't tested there.
4. When re-verifying a user-supplied lead list, do not assume the vocabulary used in their
   notes matches the source document's vocabulary — search for the underlying concept/
   scenario details (names, numbers, amounts mentioned) instead of just the phrase they wrote.

## 4. False-positive traps — check context, don't pattern-match blindly

The same words appear in unrelated topics constantly. Confirmed traps from the AS 2 pass
(generalize this pattern to any topic you're auditing):
- "FIFO" / "Weighted Average" applied to an **investment account / securities** ≠ inventory
  cost formula.
- "Weighted average number of shares" ≠ inventory — that's EPS (AS 20).
- "NRV" / "replacement cost" applied to a **building or other PPE** ≠ inventory — that's
  impairment / AS 10.
- A **borrowing-cost interest rate** calculation step ≠ automatically an inventory question —
  only counts if that interest is being specifically capitalised into inventory value.
- A coincidental number (e.g. an annuity factor like "2.28") that superficially resembles a
  standard-number citation ("AS 2") is not a real reference — always verify actual textual
  context around a regex hit, never trust the match alone.

Before including any candidate, ask: *is this actually testing the target standard's own
recognition/measurement/disclosure rule, or is it just using a similar-sounding term in
service of a different standard's question?*

## 5. Q-page vs Ans-page: always independent, never inferred

This is a standing instruction from the project owner, not a one-off preference: **never
infer the answer's location from the question's location, or vice versa.** For every
finding:
- Locate the question in its own document (or its own section, for self-contained RTPs).
- Separately locate the matching solution in the Ans document (or the later Solution section
  of the same RTP) by searching for matching content — not by assuming proximity or a fixed
  offset.
- If only one of the two exists for a given attempt (see §2), say so explicitly rather than
  citing the existing document's page for both roles.

## 6. Handling user-supplied reference lists

If the user provides their own compiled list of questions/pages (e.g. from a prior AI tool
or manual notes):
- Treat every field in it as an unverified **lead**, not as ground truth — even (especially)
  page numbers, which have been confirmed in this project to sometimes be AI-hallucinated
  by a previous tool. A quick sanity check: if a cited page number exceeds the total page
  count the source PDF could plausibly have (cross-check file size / `.md` line count against
  the claimed page), treat the whole list's page numbers as suspect and ask the user directly
  about their provenance before trying to reconcile — don't silently guess at what numbering
  scheme they used.
- Re-derive the PDF name, page, question number, marks, and concept independently from the
  source documents. Only keep a lead's *topic pointer* (which paper, roughly which concept)
  as a starting hint for where to search.
- Explicitly report, per lead, whether you confirmed it, corrected it, or could not verify it
  — don't silently merge corrected data into the output without flagging that a correction
  happened.

## 7. Speed vs accuracy — an explicit, revisitable tradeoff

Full exhaustive verification (independent PDF-page confirmation for every single question,
across every file, including large scanned compilations) is expensive and slow. If the user
signals time pressure, it is legitimate to trade precision for speed — but only *explicitly*:
- State plainly in the deliverable which parts were fully verified (exact PDF page, both Q
  and Ans independently) vs which used a cheaper proxy (`.md` line position, single-pass
  read without secondary confirmation).
- Keep a visible "what was not fully covered" section listing skipped verification, unread
  files, and unconfirmed marks/question-numbers — this is what makes an ~90%-accuracy pass
  trustworthy: the student can see exactly where the remaining 10% risk sits, instead of it
  being silently baked into confident-looking numbers.
- Background subagents are a good way to parallelize this kind of search (split the question
  bank into batches: MTP-batch-1, MTP-batch-2, RTP, PYQ, any compiled mega-PDF as its own
  agent since it's usually the slowest). But background agent state can be lost across long
  gaps in a session (observed: agents dispatched, then "no task found" after several hours) —
  if a background search goes stale/unrecoverable, don't re-dispatch identical expensive
  agents; pivot to direct sequential tool calls using whatever partial context you already
  have, and be transparent with the user about the pivot.

## 8. Building the topic-wise weightage summary (marks × topic × attempt)

Once individual questions are found and verified (§§1-6), aggregate by the study material's
own numbered sub-topics:
- **Assign each question to its single dominant/primary topic**, not to every topic it
  touches. Composite numerical questions routinely blend 2-3 sub-topics (e.g. one scenario
  testing both fixed-overhead absorption AND by-product NRV AND raw-material replacement
  cost in one go) — double-counting its marks under every touched topic would inflate the
  table and mislead the "which topic matters most" signal. Note secondary/shared topics in
  the row's description instead of splitting marks.
- Where a question's marks aren't visible in the extracted text, say "not stated on page" or
  "not confirmed" rather than guessing a plausible-looking number.
- Include **zero-hit topics explicitly** in the summary table (don't just omit them) — a
  topic that has never appeared is itself useful information for a student (either
  low-priority, or "due" to appear), and silently dropping it from the table would look like
  an oversight rather than a finding.
- Create a small number of clearly-labeled **cross-topic buckets** for content that
  genuinely doesn't map to one sub-topic number (e.g. an AS 1-interface "estimate vs policy
  change" question, or an AS 21-interface consolidation question) — forcing these into a
  single ill-fitting sub-topic number is its own kind of inaccuracy.
- Sort the final table by marks descending and add a one-paragraph plain-English "reading
  this table" note calling out the clear high-yield and zero-yield topics — that's the whole
  point of the deliverable ("which topic is most necessary," in the project owner's words).

## 9. Final deliverable shape

A single self-contained HTML file (UTF-8, no external assets — this repo requires no binary
files and no NUL/UTF-16 encoding, see root `CLAUDE.md`) saved under
`books/question-bank/metadata-index/`, containing, in this order:
1. Title + one-line scope statement.
2. A **methodology note** (styled distinctly, e.g. a highlighted box) stating exactly what
   was verified vs approximated, and how user-supplied reference data was (or wasn't) reused.
3. The **topic-wise weightage summary** table (§8) — placed first/near-top, since it's the
   highest-value "at a glance" view for a student.
4. Detailed question tables, bifurcated by question type (MCQ / Descriptive-Scenario /
   Integrated-with-other-standards or however the user has asked for it split), each row
   carrying: source PDF (Q), question no., page (Q), source PDF (Ans), page (Ans), marks,
   type, concepts tested, and a **specific, non-generic** "common student mistakes" note
   (a concrete numeric or conceptual trap in that exact question — never generic filler like
   "students may make calculation errors").
5. A closing **"what was not fully covered"** honesty section (§7) if any speed/accuracy
   tradeoff was made.

After writing/editing the file, run `python tools/health_check.py` (per root `CLAUDE.md`) —
new top-level structural changes need documenting there and in `README.md`, though a new
file inside an already-documented folder (like `question-bank/metadata-index/`) typically
needs no further action beyond the health check passing.

## 10. Keep the reusable index current

Whenever you read a study-material unit's numbered structure precisely enough to write it
into `topic-index.json`, add/correct that unit's entry in the same pass — don't let the
one-off question-bank summary be the only place the correct numbering lives. Future summaries
(for other chapters/standards) should be able to skip re-reading a unit already indexed
correctly here. Bump `topic-index.json`'s `_readme`/`generated` fields when you touch it, and
validate the file is still well-formed JSON with the expected unit count before moving on.
