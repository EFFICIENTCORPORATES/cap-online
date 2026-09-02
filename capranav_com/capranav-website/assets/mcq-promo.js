/*
  Shared "Free MCQ Practice Bot" promo block — used on index.html, courses.html
  and books.html so the pitch and QR code render identically everywhere.
  Renders a live QR code client-side (via qrcodejs, loaded from cdnjs) pointing
  at the bot's real Telegram link — no static image file needed.
*/
window.renderMcqPromo = function (bot) {
  const statsHtml = bot.stats.map((s) =>
    `<div class="mcq-stat"><strong>${s.value}</strong><span>${s.label}</span></div>`
  ).join("");
  const featuresHtml = bot.features.map((f) => `<li>${f}</li>`).join("");

  return `
    <div class="mcq-promo">
      <div class="mcq-promo-copy">
        <p class="eyebrow">Free · Telegram</p>
        <h2>Practise free, right now.</h2>
        <p>@${bot.username} — CA Pranav's free MCQ and descriptive-question practice bot. No login, no payment, just open it and start.</p>
        <div class="mcq-stats">${statsHtml}</div>
        <ul class="mcq-features">${featuresHtml}</ul>
        <a class="button button-primary" href="${bot.url}" target="_blank" rel="noopener">Open @${bot.username} ↗</a>
      </div>
      <div class="mcq-promo-qr">
        <div class="mcq-qr-box" data-mcq-qr="${bot.url}"></div>
        <span>Scan to open on your phone</span>
      </div>
    </div>`;
};

window.initMcqPromoQrCodes = function () {
  document.querySelectorAll("[data-mcq-qr]").forEach((el) => {
    if (el.dataset.rendered) return;
    if (window.QRCode) {
      // eslint-disable-next-line no-new
      new window.QRCode(el, {
        text: el.dataset.mcqQr,
        width: 148,
        height: 148,
        colorDark: "#111827",
        colorLight: "#ffffff",
      });
      el.dataset.rendered = "true";
    }
  });
};
