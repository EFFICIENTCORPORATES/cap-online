---
name: concept-material-review
description: Review a concept-book chapter, revision sheet or similar teaching HTML/Markdown for one CA Inter chapter. Checks (1) coverage against the ICAI study-material chapter topic by topic, (2) factual accuracy, including Ind AS or other-standard contamination, (3) sequence against ICAI order and the teacher's class notes, and (4) how it was built (layout, fonts, phone view, provenance). Use when asked "is this file complete / correct / in the right sequence", "check the AS 26 file", "review this concept book", or "does it need improvement".
argument-hint: <path to the HTML or MD file> [chapter name if not obvious from the file]
---

# Concept material review

**What this produces.** A review of one teaching artefact against (a) the ICAI chapter it teaches and (b) what the repo says that kind of artefact should be. **Report only. Do not edit the file unless Pranav asks.**

## 0. Know what kind of artefact it is
Judging a revision sheet as if it were the full concept book (or the reverse) gives a wrong review. Read, before anything else:
- `books/ca-inter/concept-book/NEWTON_CONCEPT_BOOK_PRODUCTION_GUIDE.md` sections 1, 5, 8 and 16: the concept book is **not** a condensed ICAI reprint; it follows the classroom journey (concept -> teacher's story/diagram -> precise ICAI section -> the in-class illustration with solution -> exam trap -> next concept). A **revision wall** is a separate, shorter asset.
- `books/ca-inter/concept-book/CONCEPT_BOOK_NOTES_PIPELINE.md` for the source register (unannotated ICAI, annotated ICAI, NB01, NB02) and the planned chapter file contract.
State in the review which kind it is and which standard you applied.

## 1. Get the artefact's content in reading order
```bash
python3 -I .claude/skills/concept-material-review/scripts/extract_text.py "<file.html or file.md>"
```
Read the **whole** text, tables included.

## 2. Coverage: artefact vs ICAI chapter
1. List the ICAI topics with printed pages (shared helper):
   ```bash
   python3 .claude/skills/chapter-illustration-traps/scripts/list_headings.py --find "<chapter>"
   python3 .claude/skills/chapter-illustration-traps/scripts/list_headings.py "<path>"
   ```
2. Read the ICAI text for **every** topic. Build a matrix: topic -> **covered / partial / missing / wrong**. Check not just topics but the details inside: definitions, scope and exclusions, thresholds and numbers, exceptions, examples, disclosures, and ICAI's own `EX-n` and `ILL-n`.
3. Rank the gaps by **exam relevance**, highest first. A gap is most serious when an ICAI illustration or TYK question turns on it. Use the `chapter-illustration-traps` skill to see what the illustrations test.
4. Also list what the artefact adds that ICAI does not say. Mark each as "classroom heuristic" (fine if labelled) or "not in the standard" (a risk).

## 3. Accuracy
- Check every factual claim against the ICAI text. Quote the paragraph and page for each error.
- **Ind AS / international contamination is the commonest real error.** Example from 2026-11: an AS 26 sheet allowed a *revaluation model* for intangibles; the study material's AS 26 allows cost less amortisation and impairment only. Whenever the artefact states an option, a threshold or a permission, confirm it exists in **this** standard and this edition.
- Check numbers and worked examples by recomputing them in a scratchpad script.
- Wording that is looser than the standard ("periodically" where ICAI says "at least at each financial year end") is a finding, not a nitpick: exams reward the exact rule.

## 4. Sequence
- Compare the artefact's order with **ICAI's order** (the topic list from step 2).
- The teaching order is set by Pranav's **class notes**: NB01 (concept order) and NB02 (where questions are placed), kept in Google Drive. They are usually **scanned handwriting with no text layer**; reading NB01 through the Drive connector returned an empty string (2026-11-08). So:
  - Do not claim to have verified the teaching order unless you actually read the notes.
  - Say what you could and could not check, and ask Pranav for the chapter order as a short list if the order matters.
- Drive connector: `search_files` with `title contains '<chapter>'` finds other versions of the artefact. Report duplicates and which is newer. Scratch results never go in the repo.

## 5. Build quality
Run the render check (Playwright is pre-installed; the output folder must exist; use the **scratchpad**):
```bash
mkdir -p "$SCRATCH/rc" && node .claude/skills/concept-material-review/scripts/render_check.js "<file.html>" "$SCRATCH/rc" ".page"
```
It reports per page: height, **how much of the page the content fills**, overflow; the font stack and whether the first-choice font is **shipped inside the file**; and whether the page **scrolls sideways at a 390 px phone width**. Then **look at the screenshots** (open the PNGs): collisions, tiny text, misaligned arrows or flowcharts, empty areas. Never judge layout from the code alone.

Checklist:
- Pages filled sensibly (large empty areas are waste; content hitting the edge is overflow).
- Text size readable on video / print (about 16 px equivalent or more for anything read aloud).
- Fonts: shipped with the file, or a deliberate system fallback. A web font that is named but not loaded falls back unpredictably.
- Phone width: a fixed-width page that scrolls sideways is a finding if the page is meant for the website.
- Print: `@page` set, `break-inside` on boxes, colours survive greyscale (colour is not the only signal).
- Provenance: does it cite ICAI paragraph/page, name its sources, tie to a manifest? Per the guide, one canonical source should feed both the clean and the handwritten edition.
- Brand: matches the site/book style (`capranav_com_revamped/public/assets/site.css`, the slide pages) if it is meant for the site.
- Hand-authored one-off vs generated from a content model: say which, and what that costs when the chapter changes.

## 6. Report format (fixed order)
1. **Bottom line** (2-3 sentences): fit for purpose or not, the one error, the main gaps. State plainly that nothing was changed.
2. **What it is vs what the guide asks for.**
3. **Coverage**: *Correct and well done* (short) / *Factual errors* (quote, ICAI para and page) / *Missing*, numbered, most exam-relevant first, each with ICAI topic and printed page.
4. **Sequence**: vs ICAI order, and what could not be checked and why.
5. **How it was made**: what works, what to improve (concrete: numbers from the render check).
6. **Suggested next steps** in order, ending with a question about which to start.

## 7. Honesty rules
- Say what you read and what you could not read. An empty Drive result is not evidence of anything.
- Mark inferences as inferences.
- Do not praise to soften findings, and do not pad findings to look thorough: list what is actually wrong or missing.
- Do not edit the artefact, the ICAI conversions or Drive files during a review.
