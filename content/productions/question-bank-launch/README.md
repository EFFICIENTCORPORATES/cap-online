# Question Bank Book — Launch Promo

Production folder for the one-pager promoting `books/question-bank/`'s Question Bank
Book (built end-to-end in `first_run/`, see `CLAUDE.md` section 6) — the piece Pranav
is building a promotional video around.

## What's here
- `deck/question-bank-onepager.html` — the exact shipped one-page promo/landing page.
  Self-contained (fonts embedded as base64 data URIs, no external requests), so it can
  be opened directly in a browser or sent as a single file.

## Origin and design intent
Built 2026-08-08, after Pranav reviewed the actual book (`first_run/output/
QUESTION-BANK-BOOK.html`) and drafted his own feature list. The page's visual language
is deliberately **reused from the book's own CSS** (the tan/pink/green Examiner's
Comment vs. Author's Note colour code, the `Marks · Approx Time · Topic` question-meta
line, the dotted-line Error Register) — it's meant to read as a page out of the book
itself, not a generic separate marketing wrapper. The two facsimile "exhibits" on the
page (the AS 10 Preet Ltd. PPE question, its real Author's Note) are genuine excerpts
from the actual book, not invented examples.

Hero line (verbatim, Pranav's instruction): **"Most Friendly Question Bank for Self
Study Students."** MCQ-platform mention is placed deliberately last and low-key
(Pranav's instruction — promote the book first) and names `1Lavya.com` only as one
neutral example among "any other MCQ practice platform of your choice" — explicitly
not an endorsement or partnership, per Pranav's instruction not to be seen as
associated with 1Lavya.

## Still needed before this goes live
The "Get Your Copy" buttons and the footer currently have **no purchase link, no
price, and no contact address** — left as visible placeholders rather than invented.
Fill these in (same file, same Artifact URL below) before sharing publicly.

## Where it's published
Claude Artifact (private until shared): `https://claude.ai/code/artifact/de2d9aa7-ab4b-4b91-9bf4-08a6cf729ab5`
— redeploy by re-publishing `deck/question-bank-onepager.html` with that URL to keep
the same link.

## publish.md
Not yet posted anywhere public — update this README (or add a `publish.md`, per the
`productions/` convention) with dates/links once it ships.
