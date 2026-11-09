// Render an HTML page and report layout facts that matter for a teaching sheet or book.
// Usage: node render_check.js <file.html> <outdir> [pageSelector=.page]
// Reports per page: height, how much of it the content actually fills, any overflow;
// the font stack and whether the first-choice font actually loaded; sideways scroll at 390 px (phone);
// and writes one PNG per page into <outdir> (the folder must already exist).
// Needs Playwright (pre-installed in the cloud sessions: require('playwright') works).
const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const [file, out, sel = '.page'] = process.argv.slice(2);
  if (!file || !out) {
    console.log('Usage: node render_check.js <file.html> <outdir> [pageSelector]');
    process.exit(1);
  }
  const url = 'file://' + path.resolve(file);
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1000, height: 1300 } });
  await p.goto(url);
  await p.waitForTimeout(500);

  const pages = await p.evaluate((selector) => [...document.querySelectorAll(selector)].map((el, i) => {
    const r = el.getBoundingClientRect();
    // content only: ignore absolutely/fixed positioned children (page-number footers, watermarks)
    const kids = [...el.children].filter((k) => k.getBoundingClientRect().height > 0
      && !['absolute', 'fixed'].includes(getComputedStyle(k).position));
    const bottom = kids.length ? Math.max(...kids.map((k) => k.getBoundingClientRect().bottom)) : r.top;
    return {
      page: i + 1,
      height: Math.round(r.height),
      filledPct: Math.round(((bottom - r.top) / r.height) * 100),
      overflow: el.scrollHeight > el.clientHeight + 2,
    };
  }), sel);
  console.log('pages matching "' + sel + '":', pages.length);
  pages.forEach((x) => console.log(' ', JSON.stringify(x)));

  const font = await p.evaluate(() => {
    const stack = getComputedStyle(document.body).fontFamily;
    const first = stack.split(',')[0].replace(/["']/g, '').trim();
    const faces = [...document.fonts].map((f) => ({ family: f.family.replace(/["']/g, ''), status: f.status }));
    // document.fonts.check() is true for a family with no @font-face at all, so it proves nothing here:
    // what matters is whether the FILE ships/loads the first-choice font itself.
    return {
      stack,
      firstChoice: first,
      firstChoiceShippedWithFile: faces.some((f) => f.family === first && f.status === 'loaded'),
      fontFaces: faces,
    };
  });
  console.log('fonts:', JSON.stringify(font));

  const q = await b.newPage({ viewport: { width: 390, height: 800 } });
  await q.goto(url);
  const sw = await q.evaluate(() => [document.documentElement.scrollWidth, document.documentElement.clientWidth]);
  console.log('phone 390px: scrollWidth', sw[0], 'vs', sw[1], sw[0] > sw[1] ? '-> SCROLLS SIDEWAYS' : '-> ok');

  const els = await p.$$(sel);
  for (let i = 0; i < els.length; i++) await els[i].screenshot({ path: path.join(out, 'page' + (i + 1) + '.png') });
  await b.close();
})();
