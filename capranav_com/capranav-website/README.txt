CAPRANAV.COM — CLOUDFLARE UPLOAD PACKAGE

Upload the complete contents of this folder to Cloudflare Pages.
The root file must remain index.html.

Main files:
- index.html: student-first CA Inter Advanced Accounting homepage with CA Pranav's journey
- courses.html: the full CA Inter Gr.1 Advanced Accounting course + all 36 chapters sold individually
- books.html: the Question Bank Book and Exam Strategy Book, ordered for physical delivery
- strategy-book.html: interactive chapter-wise Strategy Book with routing, the 5×5 framework, completion progress and saved chapters
- viewer.html: preserves the original interactive sites inside a common navigation frame
- notes.html: searchable Advanced Accounting resource library with individual PDF preview/download buttons
- student-learning.html: compact learning-hub index
- guide.html: focused individual guide reader with progress, bookmarks, print and action-sheet download
- knowledge.html: four-question path finder plus the secondary full resource catalogue
- policies.html: about, contact, privacy, terms, refund, course-access, shipping, copyright and grievance information
- assets/: homepage styles, JavaScript, the professional CA Pranav portrait, and the store (catalogue-data.js, checkout.js, store-config.js, store.css)
- public/experiences/: exact mirrored source files from the supplied capranav.com links
- _headers: security and caching headers for Cloudflare Pages
- .env.example / .env: Razorpay Key ID goes in .env (gitignored, never committed) — see tools/apply_store_config.py

The Karma card opens the live 1LAVYA exam-practice platform.
The notes page currently uses public Google Drive preview/download links. Those URLs can be replaced with Cloudflare R2 public URLs later without changing the page structure.
Run tools/build_notes_catalog.py against refreshed shared-folder HTML files when the Google Drive catalogue changes.
Run tools/build_knowledge_library.py after the notes catalogue changes to rebuild the connected student knowledge library.

Store / payments (added 2026-09-02):
- All prices, chapters and books live in one place: assets/catalogue-data.js. Edit a price there and it
  updates everywhere (homepage, courses.html, books.html) — nothing else needs touching.
- Checkout is client-side only for now (no backend): assets/checkout.js opens Razorpay's own Checkout
  widget using the public Key ID from assets/store-config.js, after collecting the buyer's details
  (and, for books, their delivery address) in a short form. Every field rides along as Razorpay "notes"
  so it's visible against the payment in the Razorpay Dashboard for manual fulfilment — see
  VAULT-BLUEPRINT.html for the later phase that adds automatic, backend-verified access unlock.
- To go live: copy .env.example to .env, paste your real Razorpay Key ID into RAZORPAY_KEY_ID, then run
  `python tools/apply_store_config.py` from this folder. Until that's done, every Buy button shows a
  friendly "payment isn't switched on yet" message instead of failing.
- Book prices and the flat shipping fee are still blank in catalogue-data.js (price: null) — fill those
  in, and the full course / ready chapters, to make everything purchasable.
