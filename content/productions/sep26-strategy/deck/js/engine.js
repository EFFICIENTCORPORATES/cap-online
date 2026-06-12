/* ============================================================
   ENGINE — generic slide engine. Content lives in slides.js.

   Slide meta (slides.js):
     id      slug (HUD)
     theme   'dark' | 'light'
     title   header title (English). Omit → no header (dramatic slides)
     hindi   header subtitle in Devanagari
     bucket  0–6 → highlights that bucket on the footer journey strip
     chip    false → hide the live days-to-exam chip (default shown w/ header)
     html    slide body. data-step="n" elements reveal in order.

   Live dates:
     [data-days-to-exam]          → days from today to EXAM_DATE
     [data-days-to="YYYY-MM-DD"]  → days from today to that date

   Controls:
     → / Space / PageDown / click   next reveal step (then next slide)
     ← / PageUp                     undo step (then previous slide)
     Home / End                     first / last slide
     F fullscreen · H toggle HUD
   ============================================================ */

(function () {
  'use strict';

  const stage = document.getElementById('stage');
  const hud   = document.getElementById('hud');

  /* journey strip: 6 buckets, widths proportional to a Sep-26
     student's real timeline (B2 longest, B5 = 12 exam days) */
  const BUCKETS = [
    { n: 1, w: 8,  c: 'var(--b1)' },
    { n: 2, w: 34, c: 'var(--b2)' },
    { n: 3, w: 22, c: 'var(--b3)' },
    { n: 4, w: 16, c: 'var(--b4)' },
    { n: 5, w: 7,  c: 'var(--b5)' },
    { n: 6, w: 13, c: 'var(--b6)' }
  ];

  function daysTo(dateStr) {
    const target = new Date(dateStr + 'T00:00:00');
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return Math.max(0, Math.round((target - today) / 86400000));
  }
  window.DECK = { daysTo: daysTo };   /* available to slide scripts */

  /* ---------- chrome builders ---------- */

  function headerHTML(s) {
    if (!s.title) return '';
    const chip = (s.chip === false) ? '' :
      '<div class="sl-chip"><b><span data-days-to-exam></span></b>&nbsp;DIN — EXAM</div>';
    return '<header class="sl-header"><div class="sl-title">' +
      '<h1>' + s.title + '</h1>' +
      (s.hindi ? '<div class="h-dev">' + s.hindi + '</div>' : '') +
      '</div>' + chip + '</header>';
  }

  function footerHTML(s) {
    const segs = BUCKETS.map(function (b) {
      const on = (s.bucket === b.n) ? ' on' : '';
      return '<div class="j-seg' + on + '" style="width:' + b.w + '%;background:' + b.c + '"></div>';
    }).join('');
    const b0on = (s.bucket === 0) ? ' on' : '';
    return '<footer class="sl-footer">' +
      '<div class="journey"><div class="j-row">' + segs + '</div>' +
      '<div class="j-b0' + b0on + '"></div>' +
      '<div class="j-label">Bucket 0 — Your Daily Self · B1→B6</div></div>' +
      '<div class="wm">CA&nbsp;<b>Pranav P Tulshyan</b></div>' +
      '</footer>';
  }

  /* ---------- build DOM from SLIDES ---------- */

  SLIDES.forEach(function (s) {
    const sec = document.createElement('section');
    sec.className = 'slide';
    sec.dataset.id = s.id;
    sec.dataset.theme = s.theme || 'dark';
    sec.innerHTML =
      headerHTML(s) +
      '<div class="slide-body">' + s.html + '</div>' +
      footerHTML(s);
    stage.appendChild(sec);
  });

  const sections = Array.from(stage.querySelectorAll('.slide'));
  const steps = sections.map(function (sec) {
    return Array.from(sec.querySelectorAll('[data-step]'))
      .sort(function (a, b) { return (+a.dataset.step) - (+b.dataset.step); });
  });
  const revealed = sections.map(function () { return 0; });
  let slideIndex = 0;

  /* ---------- live dates ---------- */

  stage.querySelectorAll('[data-days-to-exam]').forEach(function (el) {
    el.textContent = daysTo(EXAM_DATE);
  });
  stage.querySelectorAll('[data-days-to]').forEach(function (el) {
    el.textContent = daysTo(el.dataset.daysTo);
  });

  /* ---------- rendering ---------- */

  function applyStepStates(i) {
    steps[i].forEach(function (el, k) {
      el.classList.toggle('on', k < revealed[i]);
    });
  }

  function show(i) {
    slideIndex = Math.max(0, Math.min(SLIDES.length - 1, i));
    sections.forEach(function (sec, k) {
      sec.classList.toggle('active', k === slideIndex);
    });
    const theme = sections[slideIndex].dataset.theme;
    document.body.classList.toggle('theme-dark',  theme === 'dark');
    document.body.classList.toggle('theme-light', theme === 'light');
    applyStepStates(slideIndex);
    updateHud();
  }

  function next() {
    if (revealed[slideIndex] < steps[slideIndex].length) {
      revealed[slideIndex]++;
      applyStepStates(slideIndex);
      updateHud();
    } else if (slideIndex < SLIDES.length - 1) {
      show(slideIndex + 1);
    }
  }

  function prev() {
    if (revealed[slideIndex] > 0) {
      revealed[slideIndex]--;
      applyStepStates(slideIndex);
      updateHud();
    } else if (slideIndex > 0) {
      revealed[slideIndex - 1] = steps[slideIndex - 1].length;
      show(slideIndex - 1);
    }
  }

  function updateHud() {
    hud.textContent =
      (slideIndex + 1) + '/' + SLIDES.length +
      ' · ' + SLIDES[slideIndex].id +
      ' · step ' + revealed[slideIndex] + '/' + steps[slideIndex].length;
  }

  /* ---------- scale 1920x1080 stage to window ---------- */

  function fit() {
    const s = Math.min(window.innerWidth / 1920, window.innerHeight / 1080);
    stage.style.transform = 'scale(' + s + ')';
  }
  window.addEventListener('resize', fit);
  fit();

  /* ---------- input ---------- */

  document.addEventListener('keydown', function (e) {
    switch (e.key) {
      case 'ArrowRight':
      case ' ':
      case 'PageDown':
        e.preventDefault(); next(); break;
      case 'ArrowLeft':
      case 'PageUp':
        e.preventDefault(); prev(); break;
      case 'Home':
        e.preventDefault(); revealed[0] = 0; show(0); break;
      case 'End':
        e.preventDefault();
        revealed[SLIDES.length - 1] = steps[SLIDES.length - 1].length;
        show(SLIDES.length - 1);
        break;
      case 'f': case 'F':
        if (document.fullscreenElement) document.exitFullscreen();
        else document.documentElement.requestFullscreen();
        break;
      case 'h': case 'H':
        hud.classList.toggle('hidden');
        break;
    }
  });

  /* clicks advance — unless the click is on an interactive element
     (e.g. the draggable subject sliders, coming in Phase 2) */
  document.addEventListener('click', function (e) {
    if (e.target.closest('[data-interactive]')) return;
    next();
  });

  show(0);
})();
