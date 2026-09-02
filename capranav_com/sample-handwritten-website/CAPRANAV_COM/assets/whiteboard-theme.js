(() => {
  const path = (location.pathname.split('/').pop() || 'index.html').toLowerCase();
  const pageClass = 'wb-page-' + path.replace(/\.html$/,'').replace(/[^a-z0-9]+/g,'-');
  document.body.classList.add('wb-whiteboard', pageClass);

  // Add marker underline treatment to a small, deterministic set of emphasized words.
  document.querySelectorAll('h1 em, h2 em').forEach((el) => el.classList.add('wb-marker-underline'));

  // Whiteboard annotations: explanatory rather than decorative clutter.
  const annotations = {
    'index.html': [
      ['.hero.hero-learning','Start here ↘','wb-note-blue','top:95px;right:41%;'],
      ['.quick-start-section','Pick the problem you have today','wb-note-green','top:54px;right:7%;'],
      ['.teaching-section','Story → concept → practice','wb-note-purple','top:58px;right:6%;']
    ],
    'student-learning.html': [
      ['.hub-hero','One guide. One action.','wb-note-blue','top:66px;right:7%;'],
      ['.accounts-library','Start with the standards below ↘','wb-note-green','top:40px;right:5%;']
    ],
    'knowledge.html': [
      ['.knowledge-hero','4 answers → 5 resources','wb-note-blue','top:65px;right:7%;'],
      ['.path-finder-section','No long form. Just choose.','wb-note-green','top:55px;right:6%;']
    ],
    'notes.html': [
      ['.notes-hero','Search. Preview. Download.','wb-note-blue','top:60px;right:7%;']
    ],
    'strategy-book.html': [
      ['.book-hero','Your chapter-by-chapter route','wb-note-blue','top:65px;right:7%;'],
      ['.chapters','Open only what solves today’s problem','wb-note-green','top:48px;right:5%;']
    ],
    'policies.html': [
      ['.policy-hero','Clear rules, written plainly','wb-note-blue','top:55px;right:7%;']
    ]
  };

  (annotations[path] || []).forEach(([selector,text,kind,styleText]) => {
    const host = document.querySelector(selector);
    if (!host || getComputedStyle(host).position === 'static') return;
    const note = document.createElement('span');
    note.className = `wb-board-note ${kind}`;
    note.setAttribute('aria-hidden','true');
    note.textContent = text;
    note.style.cssText = styleText;
    host.appendChild(note);
  });

  // Add a hand-drawn underline below selected lead headings that do not use <em>.
  document.querySelectorAll('.quick-start-head h2,.updates-heading h2,.journey-heading h2,.library-top h2,.accounts-heading h2,.chapters-head h2').forEach((h) => {
    if (h.querySelector('.wb-squiggle')) return;
    const line = document.createElement('span');
    line.className = 'wb-squiggle';
    line.setAttribute('aria-hidden','true');
    h.appendChild(line);
  });
})();
