# SKILL — Question Bank: Topic Tagging & Final Chapter Placement

> **What this is:** how to tag a Question Bank question against the syllabus taxonomy —
> which file is the join-key source of truth (there are three competing candidates in this
> repo; only one is correct to use), how to record a topic tag in the sitting HTML, and
> how to compute the new `data-final-chapter` attribute that decides which chapter's book
> a question physically lands in.
>
> Read `SKILL-question-bank-html-schema.md` first for where a `.topic-tag` span sits in
> the document. Read `SKILL-question-bank-question-splitting.md` alongside this one —
> whether a question gets split changes whether it needs one topic tag or several.

---

## 1. Three taxonomy files exist in this repo. Use only one as the join key.

This repo went through a real migration fight to reconcile competing ID schemes (U0 vs
U1, hyphens vs underscores — see `books/question-bank/metadata-index/TAGGING-SCHEMA.md`
and `CLAUDE.md` §6 for the full history). **Do not reopen it by inventing a fourth
scheme.** The three files and their roles:

| File | Role |
|---|---|
| `books/concept-book/syllabus-engine/data/0-ca-inter-adv-accounts-subtopics-marks-weightage.json` | The master syllabus index. "Locked, never edit." Source of `unique_chapter_id` / `unique_topic_id` and marks-by-attempt history. |
| `books/concept-book/syllabus-engine/data/1-ca-inter-adv-accounts-topic-page-index.json` | **The canonical topic-number + page-number + `teaching_sequence` source.** Cross-joined 1:1 against file 0. This is where `teaching_sequence` (used for Final Chapter placement, §3 below) comes from. |
| `books/question-bank/metadata-index/topic-index.json` | **The operative tagging index** — the one you actually tag questions against. Gives `unitCode` + raw ICAI paragraph `sections[].ref` (e.g. `"2.8"`) + a prose `description` legible enough to point a student at "go read para 2.7–2.8." |

**The join keys for a `.topic-tag` span are `data-unitcode` (from `topic-index.json`) and
`data-subtopicref`** (the `sections[].ref` value from the same file). These are the
*only* IDs a topic tag should carry as machine-readable identity. A human-readable label
(`AS 9 — Revenue Recognition (2.8)`) is display text and can be edited freely without
touching the join key.

**Do not add a parallel ID like `AS-9` or `AS-9.2.8`.** An earlier external-AI review of
this pipeline suggested exactly that, and it was rejected for this reason: it recreates
the multi-scheme problem this repo already spent real effort fixing.

## 2. Tagging a question — the mechanics

1. Read the question, identify which standard(s)/chapter(s) it tests.
2. Look up the matching unit in `topic-index.json` by its `standard` field (e.g. `"AS 9"`)
   or `title`.
3. Find the specific `sections[]` entry whose `description` best matches what the question
   actually tests — not just the chapter, the *paragraph*.
4. Write the tag:
   ```html
   <span class="topic-tag" data-unitcode="M2-C8-U2" data-subtopicref="2.8"
         data-standard="AS 9" data-title="Revenue Recognition"
         data-topic-rank="primary">AS 9 &mdash; Revenue Recognition (2.8)</span>
   ```
5. If the question tests a unit not yet in `topic-index.json` at all (currently: AS 1 and
   AS 27 are the two genuinely untouched chapters, plus several units that exist only as
   heading-list stubs) — **tag it anyway**, using the `unitCode` you can derive from the
   chapter/unit numbering convention (`M{module}-C{chapter}-U{unit}`, `U0` for
   single-unit chapters), and add `data-issue="topic-unindexed"` on the parent qblock
   (see the HTML schema skill §7). Never fabricate section-level detail that isn't in the
   index to make the tag look more complete than it is.

## 3. `data-topic-rank` — primary vs secondary

When a question (or, after splitting, a question fragment — see the splitting skill)
tests more than one standard within the same connected content, rank each tag:

- `primary` — the standard the question is fundamentally testing.
- `secondary` — an incidental or supporting mention that doesn't carry independent marks
  weight.

After the 2026-07-24 schema revision, most multi-topic *descriptive* questions get
**split into independent single-topic records** (see the splitting skill), so most tags
in practice are `primary` by default with nothing to rank against. `data-topic-rank`
matters specifically for the *connected* multi-topic case that splitting explicitly does
not apply to — without a rank, a topic filter would surface a question where the tagged
topic is a footnote, not the point.

## 4. `data-final-chapter` — where a question physically lives in the assembled book

**The rule (Pranav, 2026-07-24):** a student practices the Question Bank Book
sequentially, chapter by chapter, in teaching order. For a question/fragment that only
ever tests one topic (the normal case after independent-question splitting), its home
chapter is trivially that topic. For a genuinely **connected** multi-topic question — one
continuous fact pattern that happens to test, say, AS 2, AS 10, and AS 29 in one flowing
problem — its home chapter is whichever tested topic comes **latest in teaching
sequence**. Reasoning: by the time a student sequentially reaches the latest of the
standards a question touches, every earlier standard it also touches has already been
taught — so that's both the pedagogically correct place to encounter it and the place a
student would intuitively guess to search for it.

**Source of `teaching_sequence`:**
`books/concept-book/syllabus-engine/data/1-ca-inter-adv-accounts-topic-page-index.json`,
field `teaching_sequence` on each chapter entry (keyed by `unique_chapter_id`, which is
the same value as `unitCode`). Values are mostly plain integers as strings (`"7"`,
`"15"`) but a few carry a letter suffix for insertions between two sequence numbers
(`"23B"`, `"30A"`) — sort by the numeric part first, letter suffix as a tiebreak after the
base number.

**Worked example** (from `first_run/output/parsed-from-pdf/MTP_May2026_Set1.html`, Q1 before it was split
into independent fragments): the un-split question tested AS 16 (`teaching_sequence: 7`),
AS 11 (`teaching_sequence: 15`), and AS 2 (`teaching_sequence: 4`). If this had been a
*connected* question, its `data-final-chapter` would be AS 11's `unitCode` (`M2-C7-U3`),
being the latest of the three. In the actual file, all three sub-parts turned out to be
**independent** (three unrelated companies bundled under one question number), so each
became its own single-topic record and `data-final-chapter` is trivially each one's own
topic — the "latest teaching sequence" computation never actually had to run. Don't skip
recording the attribute just because it's trivial in the common case; a future connected
question will need it to already be part of the schema, not bolted on ad hoc.

**Open issue (2026-07-25, not yet resolved):** this rule was written for one connected
question testing multiple standards within a single continuous fact pattern. Pranav's
first real-data review of the rendered chapter book (`AS02_Question_Book.html`) surfaced a
related but distinct case this rule doesn't yet cover: a **case-scenario MCQ cluster**
where each individual MCQ is validly single-topic on its own, but its sibling MCQs (under
the same shared case scenario) test a *different* standard — e.g. `PYQ_Jan2026.html`'s
"P Limited" cluster, where Q1–Q3 individually test AS 11 and Q4 individually tests AS 2.
Whether the same "latest teaching sequence wins" logic should apply **at the cluster
level** (homing the whole cluster, including Q4, under AS 11) — and what that means for
whether AS 2's chapter book shows Q4 at all — is undecided. See
`SKILL-question-bank-chapter-book-rendering.md` §3.2 for the full open question; don't
resolve this unilaterally, it's part of a review Pranav is running holistically.

**Reference table of `teaching_sequence` values used so far** (pull fresh values from
file 1 for anything not listed — this table is a convenience snapshot, not the source of
truth):

| Standard/Topic | `unitCode` | `teaching_sequence` |
|---|---|---|
| AS 2 — Valuation of Inventories | `M2-C5-U1` | 4 |
| AS 10 — Property, Plant and Equipment | `M2-C5-U2` | 5 |
| AS 13 — Accounting for Investments | `M2-C5-U3` | 10 |
| AS 16 — Borrowing Costs | `M2-C5-U4` | 7 |
| AS 19 — Leases | `M2-C5-U5` | 8 |
| AS 29 — Provisions, Contingent Liabilities and Contingent Assets | `M2-C6-U2` | 11 |
| AS 11 — Effects of Changes in Foreign Exchange Rates | `M2-C7-U3` | 15 |
| AS 9 — Revenue Recognition | `M2-C8-U2` | 16 |
| AS 21 — Consolidated Financial Statements | `M2-C10-U1` | 27 |
| AS 1 — Disclosure of Accounting Policies | `M1-C4-U1` | 21 |
| AS 17 — Segment Reporting | `M1-C4-U3` | 24 |
| AS 18 — Related Party Disclosures | `M1-C4-U4` | 25 |
| AS 24 — Discontinuing Operations | `M1-C4-U6` | 26 |
| Preparation of Financial Statements (Schedule III) | `M3-C11-U1` | 22 |
| Buy-back of Securities | `M3-C12-U0` | 32 |
| Amalgamation of Companies | `M3-C13-U0` | 30A |
| Internal Reconstruction | `M3-C14-U0` | 33 |
| Accounting for Branches | `M3-C15-U0` | 34 |
