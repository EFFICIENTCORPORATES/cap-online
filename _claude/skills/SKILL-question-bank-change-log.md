# SKILL — Question Bank Book: log every defect the moment you find it

**Standing rule, no exceptions: the instant you find anything wrong with, or
missing from, the Question Bank Book, add it to
`first_run/SECOND-EDITION-CHANGE-REQUESTS.md` — before you fix it, and whether or
not you fix it at all.**

## Why this rule exists and is not negotiable

The first edition is **printed and distributed**. Nothing in a student's copy can
be quietly corrected. The only thing that can carry a defect forward to the
second edition is a written record, and the only reliable moment to write it is
the moment it is found — not at the end of the session, not "once it's
confirmed", not after deciding whether it matters.

Every failure mode this rule guards against has already happened in this repo:

- The Cash Flow chapter pointed at the wrong study reference for weeks, printing
  a coverage matrix that showed zero marks for a chapter with 27 real questions.
  It was found only because a QA round-trip tool was built for another reason.
- The Must Practice selection logic was reasoned out carefully, published, and
  the formula behind it was never written down — a later session had to
  reconstruct it from prose and got a different answer on one question.
- OP/PP and short chapter names survived as "future edition" items only because
  someone happened to repeat them in three different documents.

A defect noticed and not written down is a defect that ships again.

## What counts as a change request

Log it if it is any of these, in the **book** — the merged
`QUESTION-BANK-BOOK.html`, any chapter book, or the distributed PDFs:

- A wrong figure, wrong answer, wrong standard, wrong marks
- A question tagged to the wrong chapter, unit or topic
- A wrong page reference, broken table, mangled character, missing question
- A coverage gap the book itself acknowledges or a reader would notice
- A promise the book makes that nothing currently delivers
- An editorial or print-cost improvement worth the pages

Also log it when **you fix it in the pipeline**. The source being correct does not
make the distributed PDF correct — that is exactly what `FIXED-IN-SOURCE` is for.

Do **not** log pipeline bugs that never reached a reader; those belong in
`HOW-TO-BUILD-THE-BOOK.md`'s gotchas. A pipeline bug that *did* reach the printed
page belongs in both.

## How to log one

Append to the bottom of the register, next number in sequence, using the existing
entry shape: severity (`S1`–`S4`), status (`OPEN` / `FIXED-IN-SOURCE` / `DONE-E2`
/ `WONTFIX`), the date, where in the book, what is actually wrong, and what the
second edition should do about it.

Three things that make an entry worth having:

1. **Name the location precisely** — chapter, `book_id`, page. "Some AS 10
   answers look off" is not actionable a year later.
2. **Say what is wrong, not that something is wrong.** If you have not confirmed
   it, say so and mark it a risk — `CR-005` is written that way deliberately.
3. **Never renumber or delete an entry.** A `WONTFIX` with its reasoning is more
   useful than a gap in the sequence.

## When a reader reports an error

Every chapter prints an email address and promises the error will be corrected in
the next edition. That promise is live in a distributed book. A reader's report
becomes a CR like any other, with the reporter noted so they can be told when it
is fixed.

## Where this is referenced

- `first_run/SECOND-EDITION-CHANGE-REQUESTS.md` — the register itself
- `first_run/HOW-TO-BUILD-THE-BOOK.md` — the build runbook points here
- `CLAUDE.md` §6 — so a session sees the rule without having to find this file
