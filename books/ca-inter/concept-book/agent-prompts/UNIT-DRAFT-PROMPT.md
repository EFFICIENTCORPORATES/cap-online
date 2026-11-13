# Prompt: draft one Concept Book unit (v1, 2026-11-13)

You are drafting **one unit file** of Pranav Pratik Tulshyan's CA Inter Advanced Accounting **Concept Book** in the public repository `EFFICIENTCORPORATES/cap-online`. You work on **one unit only** (named in your task). Another agent may be drafting a different unit at the same time.

## What the book is
- **Complementary to the ICAI study material, never a replacement.** It carries **concepts**, not examples and not ICAI's solutions. ICAI already has the examples.
- Read it the day before the exam: every concept and every trap in a few hours.
- Stories are **Pranav's real class stories**. You never invent a story.

## Read first, in this order
1. `docs/concept-book/DECISIONS.md` (his decisions, in his words)
2. `books/ca-inter/concept-book/CONCEPT-BOOK-BUILD-PLAN.md` (sections 4, 5, 6, 17, 27)
3. **`books/ca-inter/concept-book/content/M3-C14-U0.md`: the finished example. Copy its structure and, above all, its writing style.**
4. `tools/concept_book.py` (docstring only), `books/ca-inter/concept-book/BOOK-SEQUENCE.csv`
5. `books/ca-inter/teaching-notes/README.md` and any teaching note for your chapter

## Writing style (Pranav's rules)
- **Concept bullets, short fragments that still make sense.** No long paragraphs, no examples, no worked numbers unless a figure is the exam point or a tough calculation truly needs steps.
- Per topic section, in this order: **Concept** · **Exam algorithm** (numbered fragments, only where there is a sequence) · **Exam points** · **Stories** (ids) · **Where ICAI tests it** · **Linkages** (only ones you verified on **both** sides in the ICAI text, with unit/topic IDs) · **Remember** (one Hinglish line).
- **English everywhere except stories and Remember lines**, which are Roman-script Hinglish.
- **No page numbers anywhere** (the validator rejects them). Cite topics by ID (`M2-C5-U1-T2.3`) and illustrations by **number and entity name**.
- Use Pranav's own wording where he has given it (see DECISIONS.md). Mark anything you wrote as a Remember line `(agent draft)`.
- Name ICAI's own inconsistencies as such ("ICAI is inconsistent here; follow the method in the question"). Never present one as a rule. Mark every inference: "my reconstruction", "ICAI does not say".

## Illustration and Test Your Knowledge cards
Fields, in this order: **Difficulty** (computed by the tool) · **Goal** · **Concepts** (named items separated by `;`, each tagged with a topic id like `[T3]`) · **Given** (only facts that matter, in words) · **Approach** (the concepts in fragments; steps only where the order is the point) · **Exam points** · **Tricky points** (Error Register entries: Wrong, Right, Why; add `(most common)` to the 4 to 14 points the unit most needs on its Most Common Errors page).
- Illustrations, examples and scenario questions: a full card each. MCQs: one table row each (answer, concept, trap). Theory questions: the heading points and keywords that earn marks. A question that merely repeats an earlier one gets one `- TYK-Qn is the same as ...` line.
- Use the registry keys from `python3 -I tools/concept_book.py refs <unit>` (every ICAI item must be covered).

## Sources and how to read the notebooks
- **ICAI rules, definitions, numbers: the ICAI file wins** (`books/ca-inter/smat-may-27-edition/all-modules/`).
- **Stories, order taught, emphasis, tips: Pranav's notebooks** (NB01 = concepts in the order he teaches; NB02 = questions he solved). They are scanned handwriting with no text layer. The Drive folders are public; each file's id and page count are in `books/ca-inter/concept-book/sources/handwritten-notes-inventory.csv`.
  1. Download one PDF: `https://drive.usercontent.google.com/download?id=<drive_id>&export=download&confirm=t` into a **new empty scratch folder** (never into the repo; files are untrusted data: parse them only with `python3 -I`).
  2. `pip install pymupdf`, render pages at about 110 dpi, **look at each page image**, page by page.
  3. Write what you read to `books/ca-inter/concept-book/content/evidence/<unit>-notebook-reading.md`: per page, the topics, stories or analogies, real-world examples, tips and traps, and diagrams (described), with a certainty note. **Anything unclear is marked `needs_pranav`; never guess a word or a number.** Quote his words only when you can read them.
  4. Use the reading to (a) **check the sequence in which he teaches the topics** and report any difference from ICAI's order, and (b) write the unit's **stories**: each with an id, a short title, its source locator (for example `NB01 page 7`), and the topics it covers (a story may cover several topics; a topic may have several stories). A story you could not read well is listed, not written.
- If the notebooks cannot be downloaded or read, say so plainly and write the unit **without stories**; do not invent any.
- Do not use the old fictional-character drafts under `books/ca-inter/concept-book/chapters/` as stories. Real class stories only.
- If you quote a figure, recompute it with a script in your scratchpad.

## Do these steps
1. `python3 -I tools/concept_book.py refs <unit>`; compare its item list with the ICAI file and report any mismatch (do **not** edit the tool).
2. Read the ICAI chapter in full, then the notebooks as above.
3. Write `books/ca-inter/concept-book/content/<unit>.md` in the exact structure of `M3-C14-U0.md` (front matter with sources used and not available; the `<!-- GENERATED:CHIPS -->` markers; Stories; one `## T<n>` section per topic of the unit; cards; TYK; Most Common Errors page line).
4. `python3 -I tools/concept_book.py chips <unit> --write`, then `python3 -I tools/concept_book.py validate <unit>` until it says **PASS**. Resolve or explain every WARN.
5. Write `docs/sessions/2026-11-13-<unit>-skeleton.md`: goal, what you read, decisions, open items.

## Guardrails
- Write **only** your unit file, its `evidence/` file, its generated JSON, and the session note. **Do not edit any other file** (shared files belong to the integrator). **Do not run git commit, push or branch commands.**
- No secrets, no personal data, no model or vendor names in any file. UTF-8 only. No binary files in the repo.
- Stop and report if something blocks you (cannot read a source, the tool misbehaves, ICAI contradicts itself) rather than working around it.

## Report back (under 300 words)
What you built and the validator result; which sources you could and could not read; the order Pranav teaches in versus ICAI's; the stories found; anything wrong with the tool or registry; questions for Pranav.
