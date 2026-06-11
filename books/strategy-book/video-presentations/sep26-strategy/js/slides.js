/* ============================================================
   SLIDES — content only. Edit text here; engine.js never changes.

   Meta per slide: id, theme ('dark'|'light'), title + hindi
   (bilingual header — omit title for full-drama slides),
   bucket (0–6 → highlighted on footer journey strip), html.

   data-step="n"            reveals in order on → / Space / click
   data-fx="scale|flash"    entrance variants
   [data-days-to-exam]      live days to EXAM_DATE
   [data-days-to="date"]    live days to any date

   KEY DATES:
     EXAM_DATE   2026-09-01  (exams run 1–12 Sep)
     B4_DATE     2026-07-15  (Bucket 4 starts — "45+ days before exam",
                              3-day buffer over the exact 45 = 18 Jul)
   ============================================================ */

const EXAM_DATE = '2026-09-01';
const B4_DATE   = '2026-07-15';

const SLIDES = [

  /* ---------- SLIDE 0 — GITA SHLOK (brand opening) ---------- */
  {
    id: 'shlok',
    theme: 'dark',
    html: `
      <div class="s-shlok">
        <div class="shlok-text dev step" data-step="1" data-fx="scale">
          कर्मण्येवाधिकारस्ते मा फलेषु कदाचन।
        </div>
        <div class="shlok-src dev step" data-step="2">— भगवद्गीता २.४७</div>
      </div>
    `
  },

  /* ---------- SLIDE 1 — THE HOOK ---------- */
  {
    id: 'hook',
    theme: 'dark',
    html: `
      <div class="s-hook">
        <div class="hook-number step" data-step="1" data-fx="scale" data-days-to-exam>83</div>
        <div class="hook-days step" data-step="2">days</div>
        <div class="hook-line step" data-step="3">
          September 2026. <strong>The clock is running.</strong>
        </div>
      </div>
    `
  },

  /* ---------- SLIDE 2 — PAIN MIRROR ---------- */
  {
    id: 'pain-mirror',
    theme: 'dark',
    title: 'The Mirror',
    hindi: 'क्या ये आप हैं?',
    html: `
      <div class="s-pain">
        <div class="pain-list">
          <div class="pain-line step" data-step="1">Revision chal raha hai — par yaad nahi reh raha.</div>
          <div class="pain-line step" data-step="2">Sab kuch pending lag raha hai.</div>
          <div class="pain-line step" data-step="3">Mock dene se darr lag raha hai.</div>
          <div class="pain-line step" data-step="4">Videos saare dekh liye — phir bhi clarity nahi.</div>
        </div>
        <div class="pain-closer step" data-step="5">…toh yeh video aapke liye hai.</div>
      </div>
    `
  },

  /* ---------- SLIDE 3 — POSITIONING ---------- */
  {
    id: 'positioning',
    theme: 'dark',
    title: 'What This Video Is NOT',
    hindi: 'ये वीडियो क्या नहीं है',
    html: `
      <div class="s-not">
        <div class="not-list">
          <div class="not-line step" data-step="1"><span class="x">✕</span> Not a planner.</div>
          <div class="not-line step" data-step="2"><span class="x">✕</span> Not motivation.</div>
          <div class="not-line step" data-step="3"><span class="x">✕</span> Not subject-specific.</div>
        </div>
        <div class="not-final step" data-step="4">
          ON GROUND Strategies.
          <span>For exactly where you are right now.</span>
        </div>
      </div>
    `
  },

  /* ---------- SLIDE 4 — REALITY CHECK (section title) ---------- */
  {
    id: 'reality-check',
    theme: 'dark',
    html: `
      <div class="s-reality">
        <div class="reality-en step" data-step="1" data-fx="scale">REALITY CHECK</div>
        <div class="reality-hi dev step" data-step="2">अभी आप कहाँ हो?</div>
        <div class="reality-sub step" data-step="3">6 buckets · 6 subjects · ek sach</div>
      </div>
    `
  },

  /* ---------- SLIDE 5 — BUCKET ANALYSIS TIMELINE ---------- */
  {
    id: 'bucket-analysis',
    theme: 'light',
    title: 'Bucket Analysis — CA Inter Sep 26 Student',
    hindi: 'आपके सफ़र के 6 पड़ाव',
    bucket: 3,
    html: `
      <div class="s-buckets">

        <div class="bt-bar">
          <div class="bt-seg step" data-step="1" style="width:8%;  --c:var(--b1)">
            <span class="bt-n">B1</span><span class="bt-l">Before<br>Classes</span></div>
          <div class="bt-seg step" data-step="2" style="width:34%; --c:var(--b2)">
            <span class="bt-n">B2</span><span class="bt-l">During the Classes</span></div>
          <div class="bt-seg step" data-step="3" style="width:22%; --c:var(--b3)">
            <span class="bt-n">B3</span><span class="bt-l">Revision Time</span></div>
          <div class="bt-seg step" data-step="4" style="width:16%; --c:var(--b4)">
            <span class="bt-n">B4</span><span class="bt-l">45 Days<br>Before</span></div>
          <div class="bt-seg step" data-step="5" style="width:7%;  --c:var(--b5)">
            <span class="bt-n">B5</span><span class="bt-l">Exam<br>Days</span></div>
          <div class="bt-seg step" data-step="6" style="width:13%; --c:var(--b6)">
            <span class="bt-n">B6</span><span class="bt-l">After the<br>Exams</span></div>
        </div>

        <!-- date markers under the bar -->
        <div class="bt-dates step" data-step="7">
          <div class="bt-mark" style="left:52%"><i></i>AAJ<br><span>aap yahin kahin ho</span></div>
          <div class="bt-mark bt-key pulse" style="left:64%"><i></i>15 JULY<br><span>Level-Up Date</span></div>
          <div class="bt-mark" style="left:80%"><i></i>1 SEP</div>
          <div class="bt-mark" style="left:87%"><i></i>12 SEP</div>
        </div>

        <!-- Bucket 0 foundation band -->
        <div class="bt-b0 step" data-step="8">
          <span class="bt-b0-tag">BUCKET 0</span> Your Daily Self — <span class="dev">हर एक दिन, B1 से B6 तक</span>
        </div>

        <div class="bt-note step" data-step="9">
          Har bucket ka apna kaam hai. Aapko har subject ko
          <b>15 July tak Bucket 4 ki line par</b> lana hai.
        </div>

      </div>
    `
  }

];
