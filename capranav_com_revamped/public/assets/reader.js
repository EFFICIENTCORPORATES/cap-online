import * as pdfjsLib from "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/6.3.289/pdf.min.mjs";
import { BOOK_TOC } from "./book-toc.js";
pdfjsLib.GlobalWorkerOptions.workerSrc = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/6.3.289/pdf.worker.min.mjs";

const params = new URLSearchParams(location.search);
const productId = params.get("product");

const titleEl = document.getElementById("reader-title");
const wrap = document.getElementById("reader-wrap");
const pageNumEl = document.getElementById("page-num");
const prevBtn = document.getElementById("prev-page");
const nextBtn = document.getElementById("next-page");
const jumpForm = document.getElementById("jump-form");
const jumpInput = document.getElementById("jump-input");
const jumpGoBtn = document.getElementById("jump-go");
const tocToggle = document.getElementById("toc-toggle");
const tocPanel = document.getElementById("toc-panel");
const tocBackdrop = document.getElementById("toc-backdrop");
const tocClose = document.getElementById("toc-close");
const tocListEl = document.getElementById("toc-list");

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

function openToc() {
  tocPanel.classList.add("is-open");
  tocBackdrop.classList.add("is-open");
}
function closeToc() {
  tocPanel.classList.remove("is-open");
  tocBackdrop.classList.remove("is-open");
}
tocClose.addEventListener("click", closeToc);
tocBackdrop.addEventListener("click", closeToc);

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

  let pdf;
  try {
    // Streamed via HTTP Range requests (PDF.js fetches only the byte ranges
    // it needs for the page being viewed, not the whole file up front) —
    // /api/read supports Range/206 responses specifically for this.
    // rangeChunkSize is set above PDF.js's own 64KB default: this book's
    // pages can carry large embedded images, and a bigger chunk means fewer
    // round trips per page without going back to "download everything".
    pdf = await pdfjsLib.getDocument({
      url: "/api/read?product=" + encodeURIComponent(productId),
      withCredentials: true,
      rangeChunkSize: 512 * 1024,
    }).promise;
  } catch (err) {
    showMessage(err && err.message ? err.message : "Could not load the book.");
    return;
  }

  let current = 1;
  jumpInput.max = String(pdf.numPages);
  jumpInput.disabled = false;
  jumpGoBtn.disabled = false;

  buildToc();

  async function renderPage(num) {
    num = Math.min(Math.max(1, num), pdf.numPages);
    current = num;
    showMessage("Loading page…");
    const page = await pdf.getPage(num);
    const viewport = page.getViewport({ scale: Math.min(2, (window.innerWidth - 40) / page.getViewport({ scale: 1 }).width) });
    const canvas = document.createElement("canvas");
    canvas.width = viewport.width;
    canvas.height = viewport.height;
    wrap.innerHTML = "";
    wrap.appendChild(canvas);
    await page.render({ canvasContext: canvas.getContext("2d"), viewport }).promise;
    pageNumEl.textContent = `Page ${num} of ${pdf.numPages}`;
    jumpInput.value = "";
    jumpInput.placeholder = String(num);
    prevBtn.disabled = num <= 1;
    nextBtn.disabled = num >= pdf.numPages;
  }

  function buildToc() {
    const chapters = BOOK_TOC[productId];
    if (!chapters || !chapters.length) {
      tocToggle.disabled = true;
      tocToggle.title = "No table of contents for this book yet.";
      tocListEl.innerHTML = `<div class="toc-empty">No table of contents available for this book yet — use Prev/Next or the page-jump box above to navigate.</div>`;
      return;
    }
    tocToggle.disabled = false;
    tocListEl.innerHTML = chapters
      .map(
        (c) => `<li><button type="button" data-page="${c.page}"><span class="toc-num">${c.n}.</span><span>${c.title}</span><span class="toc-page">p.${c.page}</span></button></li>`
      )
      .join("");
    tocListEl.querySelectorAll("button[data-page]").forEach((btn) => {
      btn.addEventListener("click", () => {
        renderPage(Number(btn.dataset.page));
        closeToc();
      });
    });
  }

  tocToggle.addEventListener("click", openToc);

  prevBtn.addEventListener("click", () => { if (current > 1) renderPage(current - 1); });
  nextBtn.addEventListener("click", () => { if (current < pdf.numPages) renderPage(current + 1); });
  document.addEventListener("keydown", (e) => {
    if (e.key === "ArrowRight" && current < pdf.numPages) renderPage(current + 1);
    if (e.key === "ArrowLeft" && current > 1) renderPage(current - 1);
  });

  jumpForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const target = parseInt(jumpInput.value, 10);
    if (!target || target < 1 || target > pdf.numPages) return;
    renderPage(target);
  });

  renderPage(current);
}
