/* ============================================================
   PART 2 — Reality Check tools: Subject Slider Board · Mission · Roadmap
   (appended to SLIDES — loaded after slides.js, before engine.js)
   ============================================================ */

SLIDES.push(

  /* ---------- SLIDE 6 — SUBJECT SLIDER BOARD (interactive) ---------- */
  {
    id: 'subject-sliders',
    theme: 'light',
    title: 'Same Student — 6 Different Truths',
    hindi: 'हर subject की अपनी कहानी',
    bucket: 3,
    html: `
      <div class="sb" data-interactive data-slider-board>
        <div class="sb-goalrow"><span class="sb-goallabel">15 JULY — B4 LINE</span></div>

        <div class="sb-row step" data-step="1" data-start="50"><div class="sb-sub">Adv Accounts</div><div class="sb-track"><div class="sb-marker"></div></div></div>
        <div class="sb-row step" data-step="2" data-start="38"><div class="sb-sub">Corp &amp; Other Laws</div><div class="sb-track"><div class="sb-marker"></div></div></div>
        <div class="sb-row step" data-step="3" data-start="55"><div class="sb-sub">Taxation</div><div class="sb-track"><div class="sb-marker"></div></div></div>
        <div class="sb-row step" data-step="4" data-start="30"><div class="sb-sub">Costing</div><div class="sb-track"><div class="sb-marker"></div></div></div>
        <div class="sb-row step" data-step="5" data-start="45"><div class="sb-sub">Audit &amp; Ethics</div><div class="sb-track"><div class="sb-marker"></div></div></div>
        <div class="sb-row step" data-step="6" data-start="20"><div class="sb-sub">FM-SM</div><div class="sb-track"><div class="sb-marker"></div></div></div>

        <div class="sb-win">&#9733; LEVEL 1 CLEARED — SAB SUBJECTS B4 PAR &#9733;</div>

        <div class="sb-hint step" data-step="7">
          Yeh bilkul normal hai — aap har subject mein alag bucket mein ho.
          Goal: <b>15 July tak har marker B4 line ke paar.</b>
        </div>

        <button class="sb-reset" type="button" title="Markers ko shuruaati position par wapas le jao (ya R dabao)">&#8634; RESET</button>
      </div>
    `
  },

  /* ---------- SLIDE 7 — THE MISSION ---------- */
  {
    id: 'mission',
    theme: 'dark',
    html: `
      <div class="s-mission">
        <div class="mi-days step" data-step="1" data-fx="scale"><span data-days-to="2026-07-15">34</span></div>
        <div class="mi-label step" data-step="2">din — 15 July tak</div>
        <div class="mi-line step" data-step="3">Har subject ko <b>Bucket 4 ki line</b> par lana hai.</div>
        <div class="mi-sub step" data-step="4">Yeh hai aapka Level 1. Ab dekhte hain — karna kaise hai.</div>
      </div>
    `
  },

  /* ---------- SLIDE 8 — THE ROADMAP (Bucket 3 TOC) ---------- */
  {
    id: 'roadmap',
    theme: 'light',
    title: 'The Roadmap — Before 15 July',
    hindi: 'अब आगे क्या?',
    bucket: 3,
    html: `
      <div class="s-roadmap">
        <div class="rm-list">
          <div class="rm-item step" data-step="1"><span class="rm-n">1</span>
            <div class="rm-t">The North Star Question<span>roz ek baar — har din</span></div></div>
          <div class="rm-item step" data-step="2"><span class="rm-n">2</span>
            <div class="rm-t">Fix Your Boundary<span>pehle 4 din — non-negotiable</span></div></div>
          <div class="rm-item step" data-step="3"><span class="rm-n">3</span>
            <div class="rm-t">The 3-Layer Architecture<span>samajh lo — phir kabhi confusion nahi</span></div></div>
          <div class="rm-item step" data-step="4"><span class="rm-n">4</span>
            <div class="rm-t">The 3 Sanjeevani Bootis<span>har chapter ke liye — core of this video</span></div></div>
          <div class="rm-item step" data-step="5"><span class="rm-n">5</span>
            <div class="rm-t">AI — Your Memory Machine<span>sahi kaam ke liye, sahi tarike se</span></div></div>
        </div>
        <div class="rm-note step" data-step="6">
          Inme se kuch already kar chuke ho? <b>Congratulations — bas document karo.</b> &#10003;
        </div>
      </div>
    `
  }

);
