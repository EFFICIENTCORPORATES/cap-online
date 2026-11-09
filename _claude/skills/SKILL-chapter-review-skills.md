# SKILL index: chapter illustration traps and concept-material review

Two Claude Code skills, written 2026-11-09 from work done on Chapter 14 (Internal Reconstruction) and the AS 26 revision sheet. Both are **repeatable for any CA Inter chapter**.

| Skill | Call it | What it does |
|---|---|---|
| `chapter-illustration-traps` | `/chapter-illustration-traps Internal Reconstruction` | One note per ICAI illustration naming the main trap; with `tyk`, only the Test Your Knowledge questions and adjustments that are new. |
| `concept-material-review` | `/concept-material-review books/ca-inter/concept-book/revision-material/as26/AS26_Intangible_Assets_15min_Revision_Handwritten.html` | Reviews a concept-book/revision file for coverage, accuracy, sequence and build quality. Report only; it never edits. |

**Where they live:** `.claude/skills/<name>/SKILL.md`, with helper scripts in `scripts/`. They are available in any Claude Code session that has these files in its checkout (a session on `main` once they are merged). Skills are read at session start, so open a new session after they land.

**Helper scripts (both tested):**
- `.claude/skills/chapter-illustration-traps/scripts/list_headings.py`: finds a chapter file and lists its headings (illustrations, TYK items) with printed pages.
- `.claude/skills/concept-material-review/scripts/render_check.js`: renders an HTML file and reports page fill, overflow, font shipping, phone-width scroll, and writes screenshots.

---

## 1. Why these exist
Pranav teaches a chapter by solving its illustrations, and builds concept books and revision sheets from his class notes. Two recurring needs:
1. **"What is the tricky point in each illustration?"** and **"which TYK items are genuinely new?"**, so class time goes to what is new.
2. **"Is this file complete, correct and in the right order, and is it built well?"**

## 2. Output format example (illustrations)
This is the shape to produce. It is condensed from the Chapter 14 answer of 2026-11-08.

> **Illustration 3, A & Co. (p14.13): the full scheme with many items**
> - **Preference dividend arrears** are 4 × 6% × ₹4,00,000 = ₹96,000. They are not a liability in the books. Three-fourths is simply waived with no entry; only the ₹24,000 settled in shares is entered, debited to Capital Reduction A/c.
> - **Property** is revalued before it goes to the debenture holders. The debentures are reduced by the **valuation** (₹1,20,000), not the book value.
> - The **bank overdraft** is netted against the new cash, so the balance sheet shows cash ₹35,000 and no overdraft. *(ICAI's solution does not say this; it is the only reading that reconciles. Say so.)*
>
> **Illustration 4, Rebuilt Ltd (p14.20): reduction plus fresh capital**
> - **Preference shareholders receive more than they give up**: ₹55 per ₹50 share (4 × ₹10 + 6 × ₹2.50). The extra ₹60,000 is **debited** to Capital Reduction A/c.
> - The write-off of Trademarks and Goodwill is the **balancing figure** (₹1,66,500).

TYK entry shape: `Q14 Green Ltd (p14.50)`, bullets starting **New:**, then a final line "Same as an illustration, so skipped: Q15 (= Illustration 5), Q18 (= Q12)".

## 3. Lessons these skills encode (so they are not rediscovered)
- **Reconcile every figure** with a throwaway script before stating it (reconstruction account balance, share counts, closing cash).
- **"New" means new adjustment type, direction, payment form or requirement.** Reworded repeats are skipped.
- **Two solutions in one chapter may treat the same item differently** (overdraft netted in one, separate in another). That is a classroom trap; flag it and say whether ICAI explains it.
- **Say when you inferred.** "ICAI's solution does not say" is a valid, useful sentence.
- **Ind AS contamination** (e.g. a revaluation model in AS 26) is the commonest factual error in homemade notes.
- **Class notes (NB01/NB02) are scanned and unreadable by the Drive connector**: never claim the teaching order was verified; ask for it.
- **Judge an artefact by the right standard**: revision sheet vs concept book vs question sheet.
- **Layout is judged from screenshots**, not code. Content fill, text size, shipped fonts and phone width are measurable (`render_check.js`).

## 4. Reference findings (AS 26 revision sheet, 2026-11-08)
`books/ca-inter/concept-book/revision-material/as26/AS26_Intangible_Assets_15min_Revision_Handwritten.html`: correct on definition, recognition, cost table, research/development, amortisation basics; **one factual error** (revaluation permitted: not in this edition's AS 26); main gaps: ICAI Illustration 1 (prior-period catch-up amortisation), cost components of internally generated assets (6.16), subsequent expenditure (6.18), useful life above ten years and the legal-period rule (6.20), the annual impairment test for assets not yet in use or amortised over more than ten years (6.24), the "at least each financial year end" review (6.23). Build: pages 58-74% filled, 794 px fixed width (sideways scroll on phones), Comic Neue named but not shipped, no source references. Nothing was changed in that file.
