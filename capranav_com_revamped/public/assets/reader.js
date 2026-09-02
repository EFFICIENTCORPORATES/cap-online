import * as pdfjsLib from "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/6.3.289/pdf.min.mjs";
pdfjsLib.GlobalWorkerOptions.workerSrc = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/6.3.289/pdf.worker.min.mjs";

const params = new URLSearchParams(location.search);
const productId = params.get("product");

const titleEl = document.getElementById("reader-title");
const wrap = document.getElementById("reader-wrap");
const pageNumEl = document.getElementById("page-num");
const prevBtn = document.getElementById("prev-page");
const nextBtn = document.getElementById("next-page");

const TITLES = {
  "book-qb-pdf": "The Question Bank Book",
  "book-sb-pdf": "The Exam Strategy Book",
};

// Deterrents (not guarantees — no method makes a screen unphotographable).
document.addEventListener("contextmenu", (e) => e.preventDefault());
document.addEventListener("keydown", (e) => {
  const blocked = (e.ctrlKey || e.metaKey) && ["s", "p", "u"].includes(e.key.toLowerCase());
  if (blocked) e.preventDefault();
});

function showMessage(html) {
  wrap.innerHTML = `<div class="reader-msg">${html}</div>`;
}

if (!productId || !TITLES[productId]) {
  showMessage("Book not found.");
} else {
  titleEl.textContent = TITLES[productId];
  boot();
}

async function boot() {
  const me = await fetch("/api/me", { credentials: "include" }).then((r) => r.json());
  if (!me.loggedIn) {
    location.href = "dashboard.html?buy=" + encodeURIComponent(productId);
    return;
  }
  if (!(me.entitlements || []).includes(productId)) {
    showMessage(`You don't have access to this book yet.<br><br><a class="button button-primary" href="dashboard.html?buy=${encodeURIComponent(productId)}">Buy PDF access</a>`);
    return;
  }

  showMessage("Loading your book…");
  let bytes;
  try {
    const res = await fetch("/api/read?product=" + encodeURIComponent(productId), { credentials: "include" });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.error || "Could not load the book.");
    }
    bytes = await res.arrayBuffer();
  } catch (err) {
    showMessage(err.message);
    return;
  }

  const pdf = await pdfjsLib.getDocument({ data: bytes }).promise;
  let current = 1;

  async function renderPage(num) {
    const page = await pdf.getPage(num);
    const viewport = page.getViewport({ scale: Math.min(2, (window.innerWidth - 40) / page.getViewport({ scale: 1 }).width) });
    const canvas = document.createElement("canvas");
    canvas.width = viewport.width;
    canvas.height = viewport.height;
    wrap.innerHTML = "";
    wrap.appendChild(canvas);
    await page.render({ canvasContext: canvas.getContext("2d"), viewport }).promise;
    pageNumEl.textContent = `Page ${num} of ${pdf.numPages}`;
    prevBtn.disabled = num <= 1;
    nextBtn.disabled = num >= pdf.numPages;
  }

  prevBtn.addEventListener("click", () => { if (current > 1) renderPage((current -= 1)); });
  nextBtn.addEventListener("click", () => { if (current < pdf.numPages) renderPage((current += 1)); });
  document.addEventListener("keydown", (e) => {
    if (e.key === "ArrowRight" && current < pdf.numPages) renderPage((current += 1));
    if (e.key === "ArrowLeft" && current > 1) renderPage((current -= 1));
  });

  renderPage(current);
}
