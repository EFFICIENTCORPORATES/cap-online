CAPRANAV.COM — CLOUDFLARE UPLOAD PACKAGE

Upload the complete contents of this folder to Cloudflare Pages.
The root file must remain index.html.

Main files:
- index.html: student-first CA Inter Advanced Accounting homepage with CA Pranav's journey
- strategy-book.html: interactive chapter-wise Strategy Book with routing, the 5×5 framework, completion progress and saved chapters
- viewer.html: preserves the original interactive sites inside a common navigation frame
- notes.html: searchable Advanced Accounting resource library with individual PDF preview/download buttons
- student-learning.html: compact learning-hub index
- guide.html: focused individual guide reader with progress, bookmarks, print and action-sheet download
- knowledge.html: four-question path finder plus the secondary full resource catalogue
- policies.html: about, contact, privacy, terms, refund, course-access, copyright and grievance information
- assets/: homepage styles, JavaScript and the professional CA Pranav portrait
- public/experiences/: exact mirrored source files from the supplied capranav.com links
- _headers: security and caching headers for Cloudflare Pages

The Karma card opens the live 1LAVYA exam-practice platform.
The notes page currently uses public Google Drive preview/download links. Those URLs can be replaced with Cloudflare R2 public URLs later without changing the page structure.
Run tools/build_notes_catalog.py against refreshed shared-folder HTML files when the Google Drive catalogue changes.
Run tools/build_knowledge_library.py after the notes catalogue changes to rebuild the connected student knowledge library.

WHITEBOARD DESIGN UPDATE — 12 AUGUST 2026
- The full primary CAPRANAV.COM portal now loads assets/whiteboard-theme.css and assets/whiteboard-theme.js.
- The supplied My Whiteboard design language is applied site-wide: handwritten/marker hierarchy, whiteboard grid texture, rough marker borders, sticky-note cards, highlights, annotations and controlled irregularity.
- Existing JavaScript/data behaviour and the embedded learning experiences are preserved.
- viewer.html provides the handwritten whiteboard frame around the original embedded interactive experiences so those applications are not broken by global restyling.
