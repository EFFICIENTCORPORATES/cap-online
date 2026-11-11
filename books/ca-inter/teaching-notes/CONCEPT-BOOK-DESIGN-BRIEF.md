# Concept Book (Advanced Accounting): design brief for the agent that builds it

_Written 2026-11-10 from Pranav's instructions in the session that produced `ch09u2-ch13-amalgamation-traps.md`. Read this first when starting any concept-book chapter. These are Pranav's decisions, not my suggestions; where I added something it is marked "(added)". Read with `CONTEXT.md`, `books/ca-inter/concept-book/NEWTON_CONCEPT_BOOK_PRODUCTION_GUIDE.md` and `books/ca-inter/concept-book/CONCEPT_BOOK_NOTES_PIPELINE.md`; if those conflict with this brief on content design, ask Pranav._

## 1. What the book is, and is not

- It is a **complementary** book. It **does not replace the ICAI study material**. Students still read ICAI; this book answers the small doubts ICAI leaves open and builds a holistic understanding so that they **do not rote-learn**.
- It carries **no solved questions and no answers** (no copying of ICAI's illustrations and solutions). It carries only the **relevant question reference placed right after the concept it tests**, followed by what the student learns from it and what is new in it.
- The use case: **one day before the exam**, a student flips through the questions listed against each concept and recalls the traps in minutes.
- Pranav decides scope and wording. Where a doubt, a number or a page is uncertain, ask or mark it; never smooth it over.

## 2. The building block for every concept

Use this order inside each topic (added: names for the blocks, so every chapter looks the same):

1. **The concept in plain words.** What it is, why it exists, in 3-6 lines.
2. **"Why" boxes.** The small doubt a student actually raises, answered with the underlying identity or principle (examples in section 4 below). If ICAI does not explain the logic, say so: "ICAI does not explain this; here is the reasoning."
3. **Step-by-step algorithm.** A numbered flow a student can follow in the exam (see section 5).
4. **Question reference, right after the concept.** For each relevant ICAI illustration or TYK question: chapter, number and printed page, no question text and no solution. Then two lines:
   - **What we learnt:** the main point it teaches.
   - **What is new here:** only if it adds something earlier questions did not (this is the output of the `chapter-illustration-traps` skill).
5. **Error Register Points.** See section 3.
6. **Linkages.** See section 6.

## 3. "Error Register Points"

- The label is fixed: **Error Register Points**. Each one is a short, specific mistake students make in exams, written so a student can copy it into their own error register.
- Give **special emphasis** to the points where the maximum number of students slip. Mark the ones you consider the most common (added: a flag such as "most common").
- Write each as: the **wrong move** → the **right move** → **why**, in one or two lines. Example from Buy-back: "Wrong: buy back the whole room (₹24 lakh ÷ price). Right: share the room between cash and CRR, because CRR is not a free reserve and also reduces equity (Chapter 12 Illustrations 5 and 6; `ch11-12-dividend-vs-buyback.md` section 7)."
- Source them from the teaching notes in this folder (the "trap" bullets). Do not invent a trap without a page or a figure behind it.
- Honesty rule: a point that ICAI's own book handles inconsistently is still an error-register point, labelled "ICAI is inconsistent here; follow the method in the question". Never present an inconsistency as a rule.

## 4. Worked "Why" answers already agreed (use as the model for tone and depth)

Each of these is written up in full in the notes named; the concept book should carry a short form.

- **Why is CRR = cash paid × (face value ÷ offer price)?** Shares bought back = cash ÷ price; CRR = shares × face value (`ch11-12-dividend-vs-buyback.md` section 6).
- **Why must the debt-equity "room" be split between cash and CRR?** The CRR transfer also reduces equity (`ch11-12-dividend-vs-buyback.md` section 7). The gap Pranav named: "when we say ₹150 can be bought back, that is not true, because some has to go to CRR."
- **Why is the net-assets method different under merger and purchase?** Because assets − liabilities = share capital + reserves, so in a merger "− reserves" simply gets back to share capital; in a purchase reserves are not carried, so nothing is deducted (`concept-clarifications.md` section 6).
- **Why is the statutory reserve not deducted in a purchase?** Because it is carried with an equal debit (Amalgamation Adjustment Reserve), so net equity is unchanged (`concept-clarifications.md` section 7).
- **Why is the Amalgamation Adjustment Reserve smaller than the statutory reserves on the balance sheet?** It matches only the statutory reserves brought in from the transferor, not the transferee's own (`concept-clarifications.md` section 8).

## 5. Visual and presentation rules

- **Visually appealing:** charts, arrows, flow diagrams and colour-coded steps. Pranav wants an **algorithmic, step-wise approach** so it is easy to remember. Examples already built: `diagrams/crr-formula-explained.html` and `diagrams/buyback-simple-ltd-example.html` (nine numbered steps, a bar showing equity "must stay" vs "cash paid" vs "CRR", a "what goes wrong without the split" box).
- **Repo rules still apply:** HTML for the book, Markdown for notes, no binary files in git, **no SVG diagrams unless Pranav asks** (`CLAUDE.md` section 2; the capranav.com look and the T-format conventions are in `docs/sessions/2026-11-09-teaching-material-handover.md` section 3). If a diagram would need an SVG, ask first.
- **Standing preferences:** balance sheet in T-format with Equity & Liabilities on the LEFT and Assets on the RIGHT; timing examples always 9 : 3 months; intro lectures are concept-level with no journal entries.
- **Keep a small example next to any new method** with round numbers chosen so each test gives a different answer (as in the Simple Ltd example).

## 6. Linkages: the main focus of the book

- **Every concept must say where else the student has met it or will meet it.** The goal is that the student sees the syllabus as connected, not as 36 separate chapters.
- Write each link as: **"You will also see this in <chapter / standard>, <topic>, p<page>: <one line on how it connects>."** Verify every page in the converted ICAI file before you write it.
- Links already verified (use them, add more only after reading both places):
  - **AS 14 ↔ AS 26 (Intangible Assets), topic 6.9, p5.203:** an intangible acquired in an amalgamation in the nature of purchase is recognised even if the transferor never recorded it, and if its fair value cannot be measured reliably it is not recognised separately and goes into goodwill. Its cost is capped so that it does not create or increase a capital reserve.
  - **AS 14 ↔ AS 26 scope, topic 6.2, p5.197:** goodwill arising on an amalgamation (AS 14) and goodwill arising on consolidation (AS 21) is **outside AS 26**. This is why AS 14 has its own goodwill amortisation rule (five years unless longer is justified, AS 14 topic 2.11, p9.31) while AS 26 has a 10-year presumption for other intangibles (AS 26, "rebuttable presumption", p5.213).
  - **AS 14 pooling vs purchase ↔ AS 21 purchase of a subsidiary:** goodwill/capital reserve on amalgamation and cost of control on consolidation are the same arithmetic (consideration vs net assets). Written in `concept-clarifications.md` sections 1 and 2 and in the Kahaani deck notes (`content/productions/restructuring-lecture-1/outline/`).
  - **Buy-back ↔ dividend:** both are about free reserves; see the side-by-side table in `ch11-12-dividend-vs-buyback.md` section 2.
  - **Chapter 13 Illustration 11 ↔ Chapter 14 (internal reconstruction):** an amalgamation after a capital reduction; the overdraft is netted in Chapter 14 Illustration 3 but not in Chapter 13 Illustration 11 (see the traps notes).
  - **Amalgamation illustrations ↔ Chapter 12 CRR:** the premium and reserve usage mirror the buy-back premium treatment (added; check before use).
- Linkages to propose and verify when you reach the chapter (not yet checked): AS 14 ↔ AS 4 (events after the balance sheet date, used in AS 14 topic 2.14); AS 14 ↔ AS 5 (change in accounting policy); AS 14 ↔ AS 10 (revaluation); AS 14 ↔ Internal Reconstruction.

## 7. Source and process rules for the agent

- **Sources:** ICAI July 2026 edition (May 2027 attempt) as Markdown in `books/ca-inter/smat-may-27-edition/all-modules/`. Page numbers are printed pages from the converted files and are **not checked against the PDFs**; say so in the chapter's header or ask Pranav to confirm.
- **Per-illustration and per-TYK content:** take it from the teaching notes in this folder (`README.md` lists them). Re-check any number you quote.
- **Recompute every figure** with a throwaway script (scratchpad, not the repo). If a printed answer does not reconcile, report it; do not "correct" ICAI silently.
- **Mark every inference:** "my reconstruction", "ICAI does not say". Do not invent what Pranav said in class; the scanned class notes (NB01/NB02) are unreadable.
- **Ask, do not assume.** One concise question when unclear. Do not deploy or open a pull request unless Pranav asks.
- **Chapters covered so far by the teaching notes:** Ch 14 (Internal Reconstruction), Ch 11 topic 1.6 and Ch 12 (Dividend vs Buy-back; Chapter 12 TYK done, Chapter 11 dividend TYK pending), AS 14 and Ch 13 (Amalgamation). Everything else still needs the `chapter-illustration-traps` skill run first.

## 8. Chapter section template (added)

```
# <Chapter / standard>
## <Topic number and name>
**In plain words:** ...
**Why:** <the doubt> → <the identity or principle>
**Algorithm:** 1 → 2 → 3 ...
**Questions to revisit (no text, no answers)**
- ICAI Ill. n (p..): learnt: ...  | new: ...
**Error Register Points**
- (most common) Wrong → Right → Why
**Linkages**
- Also see <standard / chapter, topic, p..>: how it connects
```
