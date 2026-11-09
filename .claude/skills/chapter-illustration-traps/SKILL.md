---
name: chapter-illustration-traps
description: For one CA Inter chapter, read every ICAI illustration (and, on request, the Test Your Knowledge section) and write down the main tricky point of each one, for a teacher about to solve them in class. For TYK, list only the questions and adjustments that are NEW (not already in any illustration). Use when asked for "the tricky point in each illustration", "what is new in TYK", "traps in this chapter", or when Pranav starts teaching a chapter and wants a solving guide.
argument-hint: <chapter name, e.g. "Internal Reconstruction"> [illustrations | tyk | both]
---

# Chapter illustration traps and TYK new-adjustments

**What this produces.** For a chapter Pranav is about to teach: (1) one short note per ICAI **illustration** naming the main trap(s), with the printed page; (2) for **Test Your Knowledge**, only the questions and adjustments that are **new**, ignoring anything that repeats an illustration.

**What it is not.** It does not re-solve the illustration, restate the solution or reprint the question. It answers one question for each: *what would a student get wrong, or not see?*

Worked example of the exact output style (Chapter 14, Internal Reconstruction): see the conversation of 2026-11-08, or `_claude/skills/SKILL-chapter-review-skills.md` section 2 for the format.

## 0. Argument handling
- Chapter name given -> do it. No name -> ask which chapter (one question).
- Default scope is **illustrations**. Do TYK only if asked, or offer it in the last line.

## 1. Find the chapter and its text
Source of truth: ICAI study material, **July 2026 edition (May 2027 attempt)**, converted to Markdown with per-page markers.

```bash
python3 .claude/skills/chapter-illustration-traps/scripts/list_headings.py --find "<part of chapter name>"
python3 .claude/skills/chapter-illustration-traps/scripts/list_headings.py "<path printed above>"
```
- Files live in `books/ca-inter/smat-may-27-edition/all-modules/` (`M<module>_C<chapter>_U<unit>_ <name>_BEAUTIFIED.md`).
- The listing shows `ILL-n` (illustrations), `EX-n` (ICAI's short worked examples), `NOTE-n`, `TYK-MCQ-n`, `TYK-TQ-n`, `TYK-SBQ-n`, each with its **printed page**. Use those pages when you cite.
- A rawer second conversion exists in `books/ca-inter/concept-book/raw_icai_study_materials/`. Use it to cross-check any figure that looks odd. The converted files are machine-structured and not visually validated: if a number looks wrong, say so rather than silently "fixing" it.

## 2. Read every illustration, question and solution
Print the lines between one `ILL-n` heading and the next, stripping marker lines:
```bash
sed -n 'START,ENDp' "<file>" | grep -v "^<!--" | grep -v "^\s*$" | cut -c1-175
```
Read the **question and the full solution**, including notes under the solution. A trap often lives in a footnote or in a figure the solution produces but never explains.

## 3. Decide the main tricky point of each illustration
Ask, for each one: *what is the one thing that is easy to miss or get wrong?* Typical classes (use the ones that actually occur; do not force them):
- **Direction of a gain or loss.** An asset handed over for MORE than the claim is a loss; for LESS, a sacrifice. A liability settled at more than its book value is a loss.
- **Something not in the books.** An arrear (e.g. preference dividend), a contingent liability, a commitment penalty: no ledger balance exists, so the entry covers only the part actually settled.
- **Which figure the entry uses.** Valuation vs book value; paid-up vs authorised; original capital vs reduced capital.
- **A balancing figure.** One write-off the question never states; compute it, do not look for it.
- **Order of steps.** Revalue first, then transfer; write down assets before a cash payment reduces them.
- **Counts.** Number of shares after consolidation, issue, conversion; check the total.
- **Cash and overdraft.** Whether an overdraft is netted into cash or stays a liability. If the solution is silent, say so.
- **Which account takes the debit or credit.** Reconstruction/Capital Reduction vs P&L vs reserve vs share capital.
- **Anything the question says to ignore** (tax, cost of the scheme).
For theory-heavy chapters the traps are different (a threshold, an exception, who may do what): name the one a student most often misstates.

## 4. Verify before you write
Never state a figure you have not reconciled. Put a throwaway script in the **scratchpad** (not the repo) that recomputes the key figures: the balancing figure, share counts, closing cash, totals of a reconstruction account. If the solution does not reconcile, report that instead of explaining it away.

## 5. TYK: only what is NEW
1. Read the whole TYK section and the **answers/hints** (usually the last pages of the chapter).
2. Keep a running **ledger of adjustment types already seen** in the illustrations (and in ICAI's `EX-n` examples). It is the test for "new".
3. For every TYK scenario question ask: *does it introduce an adjustment type, a twist in an old one, or a requirement (a ledger account to prepare, a balance sheet item) that no illustration has?*
   - Yes -> list it, with the new point and the numbers that prove it.
   - No -> do **not** list it; name it once at the end as "same as Illustration n".
4. MCQs and theory questions: say so in one line. Mention only a genuinely new rule or a place where ICAI's answer disagrees with its own text.
5. A reworded old idea is not new. A changed direction (loss instead of sacrifice), a different payment form (cash instead of shares) or an added requirement counts as new.

## 6. Output format
- One block per illustration: bold heading `Illustration n, <company> (p<page>): <theme in a few words>`, then 1-4 short bullets. Lead each bullet with the point, in bold where it helps.
- Numbers only where they prove the point. No restating the solution.
- Add a cross-illustration inconsistency note when two solutions treat the same item differently (that is itself a classroom trap), and say whether ICAI explains it.
- TYK: block per new question `Q<n> <company> (p<page>)`, bullets marked **New:**, then a final "Same as an illustration, so skipped" list.
- End with one line offering the part not done (TYK or illustrations).

## 7. Honesty rules
- If you infer how ICAI reached a figure and the solution does not say, write "this is my reconstruction" or "ICAI's solution does not say".
- If a figure in the converted text looks wrong, say it looks wrong and give the raw-copy reading.
- Do not invent teaching advice about what Pranav said in class; you have not seen his notes.
- Page numbers are printed pages from the converted file's markers.
