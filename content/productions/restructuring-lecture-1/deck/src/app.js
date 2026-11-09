(() => {
  const deck = document.getElementById('deck');
  const slides = [...document.querySelectorAll('.slide')];
  const counter = document.getElementById('counter');
  const progress = document.getElementById('progress');
  const toc = document.getElementById('toc');
  const toast = document.getElementById('toast');
  let index = 0;
  const steps = slides.map(() => 0);

  // ---- parse step attributes once ----
  const parseMap = s => s.split('|').map(p => { const i = p.indexOf(':'); return [parseInt(p.slice(0, i), 10), p.slice(i + 1)]; });
  const pick = (map, step) => { let v = null; for (const [k, val] of map) if (k <= step) v = val; return v; };
  slides.forEach(sl => {
    sl._els = [...sl.querySelectorAll('[data-at],[data-st],[data-txt]')].map(el => ({
      el,
      at: el.hasAttribute('data-at') ? parseInt(el.dataset.at, 10) : null,
      until: el.hasAttribute('data-until') ? parseInt(el.dataset.until, 10) : null,
      st: el.dataset.st ? parseMap(el.dataset.st) : null,
      txt: el.dataset.txt ? parseMap(el.dataset.txt) : null,
    }));
    let m = 0;
    sl._els.forEach(o => {
      if (o.at !== null) m = Math.max(m, o.at);
      if (o.until !== null) m = Math.max(m, o.until);
      (o.st || []).forEach(([k]) => { m = Math.max(m, k); });
      (o.txt || []).forEach(([k]) => { m = Math.max(m, k); });
    });
    sl._max = m;
  });

  function apply(si, step) {
    slides[si]._els.forEach(o => {
      if (o.at !== null) o.el.classList.toggle('on', step >= o.at && (o.until === null || step < o.until));
      if (o.st) { const v = pick(o.st, step); if (v === null) o.el.removeAttribute('data-state'); else o.el.setAttribute('data-state', v); }
      if (o.txt) { const v = pick(o.txt, step); if (v !== null) o.el.innerHTML = v; }
    });
  }

  function update() {
    slides.forEach((s, i) => s.classList.toggle('active', i === index));
    apply(index, steps[index]);
    counter.textContent = `${index + 1} / ${slides.length}` + (slides[index]._max ? `  ·  step ${steps[index]}/${slides[index]._max}` : '');
    progress.style.width = `${((index + 1) / slides.length) * 100}%`;
    toc.querySelectorAll('a').forEach(a => a.classList.toggle('cur', a.dataset.sec === slides[index].dataset.sec));
    try { history.replaceState(null, '', '#' + (index + 1)); } catch (e) {}
  }
  function forward() {
    if (steps[index] < slides[index]._max) steps[index]++;
    else if (index < slides.length - 1) { index++; steps[index] = 0; }
    update();
  }
  function backward() {
    if (steps[index] > 0) steps[index]--;
    else if (index > 0) { index--; steps[index] = slides[index]._max; }
    update();
  }
  function goto(i, step = 0) { index = Math.max(0, Math.min(slides.length - 1, i)); steps[index] = step; update(); }

  // ---- table of contents ----
  const secs = [];
  slides.forEach((s, i) => { if (!secs.find(x => x.sec === s.dataset.sec)) secs.push({ sec: s.dataset.sec, i }); });
  toc.innerHTML = '<div class="wm"><span>P</span> CA PRANAV</div><div class="tg">AIR 1 · AIR 1 · AIR 5</div>' +
    secs.map(s => `<a data-sec="${s.sec}" data-i="${s.i}">${s.sec}</a>`).join('');
  toc.addEventListener('click', e => { const a = e.target.closest('a'); if (a) { goto(+a.dataset.i); toc.classList.remove('open'); } });
  document.getElementById('tocbtn').addEventListener('click', e => { e.stopPropagation(); toc.classList.toggle('open'); });

  // ---- print / save as PDF ----
  function showToast(msg, ms = 6000) { toast.textContent = msg; toast.classList.add('on'); setTimeout(() => toast.classList.remove('on'), ms); }
  function doPrint() {
    showToast('In the print dialog: Destination "Save as PDF", Layout Landscape, Margins None, tick "Background graphics".');
    setTimeout(() => window.print(), 250);
  }
  const prePrint = () => slides.forEach((s, i) => apply(i, s._max));
  const postPrint = () => { slides.forEach((s, i) => apply(i, steps[i])); update(); };
  window.addEventListener('beforeprint', prePrint);
  window.addEventListener('afterprint', postPrint);
  document.getElementById('printbtn').addEventListener('click', e => { e.stopPropagation(); doPrint(); });

  // ---- controls ----
  document.getElementById('next').addEventListener('click', e => { e.stopPropagation(); forward(); });
  document.getElementById('prev').addEventListener('click', e => { e.stopPropagation(); backward(); });
  document.addEventListener('keydown', e => {
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    const k = e.key;
    if (['ArrowRight', 'PageDown', ' ', 'Enter'].includes(k)) { e.preventDefault(); forward(); }
    else if (['ArrowLeft', 'PageUp', 'Backspace'].includes(k)) { e.preventDefault(); backward(); }
    else if (k === 'Home') goto(0);
    else if (k === 'End') goto(slides.length - 1, slides[slides.length - 1]._max);
    else if (k.toLowerCase() === 't') toc.classList.toggle('open');
    else if (k.toLowerCase() === 'p') doPrint();
    else if (k.toLowerCase() === 'f') document.documentElement.requestFullscreen?.();
    else if (k === 'Escape') toc.classList.remove('open');
  });
  deck.addEventListener('click', e => { if (!e.target.closest('button,#toc')) { toc.classList.remove('open'); forward(); } });

  // ---- start (deep link #n) ----
  const h = parseInt((location.hash || '').slice(1), 10);
  if (h >= 1 && h <= slides.length) index = h - 1;
  window.__deck = { goto, slides, steps, apply, update, max: i => slides[i]._max };
  update();
})();
