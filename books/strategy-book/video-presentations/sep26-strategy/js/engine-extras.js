/* ============================================================
   ENGINE EXTRAS — Phase 2-4 interactivity (loads after engine.js)

   1. Subject Slider Board — draggable markers, B4 goal line,
      LEVEL UP state when all 6 subjects reach Bucket 4. R = reset.
   2. Booti tracker — 3 gold slots in the footer of Booti slides
      (slide meta `bootis: 0–3` = how many are collected).
   3. Mock deadline — fills [data-mock-deadline] with the date
      10 days before EXAM_DATE (e.g. "22 AUG").
   ============================================================ */

(function () {
  'use strict';

  /* ---------- 1. subject slider boards ---------- */

  /* cumulative bucket boundaries in % — must match the
     8/34/22/16/7/13 widths used everywhere in this deck */
  var CUM = [8, 42, 64, 80, 87, 100];
  var B4_LINE = 64;   /* % where Bucket 4 starts = the 15 July line */

  function bucketOf(pct) {
    for (var i = 0; i < CUM.length; i++) {
      if (pct <= CUM[i]) return i + 1;
    }
    return 6;
  }

  function initBoard(board) {
    var rows = Array.prototype.slice.call(board.querySelectorAll('.sb-row'));

    function update(row, pct) {
      pct = Math.max(2, Math.min(98, pct));
      row.dataset.pct = pct;
      var m = row.querySelector('.sb-marker');
      m.style.left = pct + '%';
      m.textContent = 'B' + bucketOf(pct);
      m.classList.toggle('ok', pct >= B4_LINE);
      check();
    }

    function check() {
      var win = rows.every(function (r) { return (+r.dataset.pct) >= B4_LINE; });
      board.classList.toggle('win', win);
    }

    rows.forEach(function (row) {
      var track = row.querySelector('.sb-track');
      var m = row.querySelector('.sb-marker');
      var dragging = false;

      update(row, +row.dataset.start || 30);

      function pctFrom(e) {
        var r = track.getBoundingClientRect();
        return (e.clientX - r.left) / r.width * 100;
      }

      m.addEventListener('pointerdown', function (e) {
        dragging = true;
        m.setPointerCapture(e.pointerId);
        e.preventDefault();
      });
      m.addEventListener('pointermove', function (e) {
        if (dragging) update(row, pctFrom(e));
      });
      m.addEventListener('pointerup', function () { dragging = false; });
      m.addEventListener('pointercancel', function () { dragging = false; });

      /* tap anywhere on the track to jump the marker there */
      track.addEventListener('pointerdown', function (e) {
        if (e.target === m) return;
        update(row, pctFrom(e));
      });
    });

    board.resetBoard = function () {
      rows.forEach(function (row) { update(row, +row.dataset.start || 30); });
    };

    /* visible reset button on the slide */
    var btn = board.querySelector('.sb-reset');
    if (btn) {
      btn.addEventListener('click', function (e) {
        e.stopPropagation();      /* don't advance the slide */
        board.resetBoard();
      });
    }
  }

  document.querySelectorAll('[data-slider-board]').forEach(initBoard);

  /* R = reset all slider boards to start positions */
  document.addEventListener('keydown', function (e) {
    if (e.key === 'r' || e.key === 'R') {
      document.querySelectorAll('[data-slider-board]').forEach(function (b) {
        if (b.resetBoard) b.resetBoard();
      });
    }
  });

  /* ---------- 2. booti tracker in footer ---------- */

  var sections = document.querySelectorAll('#stage .slide');
  SLIDES.forEach(function (s, i) {
    if (s.bootis === undefined) return;
    var footer = sections[i] && sections[i].querySelector('.sl-footer');
    if (!footer) return;
    var div = document.createElement('div');
    div.className = 'booti-slots';
    var marks = ['①', '②', '③'];   /* ① ② ③ */
    for (var k = 0; k < 3; k++) {
      div.innerHTML += '<span class="bs' + (k < s.bootis ? ' on' : '') + '">' + marks[k] + '</span>';
    }
    var wm = footer.querySelector('.wm');
    footer.insertBefore(div, wm);
  });

  /* ---------- 3. mock deadline = EXAM_DATE - 10 days ---------- */

  var MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];
  var md = new Date(EXAM_DATE + 'T00:00:00');
  md.setDate(md.getDate() - 10);
  var txt = md.getDate() + ' ' + MONTHS[md.getMonth()];
  document.querySelectorAll('[data-mock-deadline]').forEach(function (el) {
    el.textContent = txt;
  });

})();
