/* Tiny shared modal used for guest-checkout forms and simple messages. */
let modalRoot = null;
function ensureModal() {
  if (modalRoot) return modalRoot;
  modalRoot = document.createElement("div");
  modalRoot.className = "modal";
  modalRoot.innerHTML =
    '<div class="modal-card" role="dialog" aria-modal="true">' +
    '<button type="button" class="modal-close" aria-label="Close">&times;</button>' +
    '<div class="modal-body"></div></div>';
  document.body.appendChild(modalRoot);
  modalRoot.addEventListener("click", (e) => { if (e.target === modalRoot) window.closeModal(); });
  modalRoot.querySelector(".modal-close").addEventListener("click", () => window.closeModal());
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") window.closeModal(); });
  return modalRoot;
}
window.openModal = function openModal(html) {
  const root = ensureModal();
  root.querySelector(".modal-body").innerHTML = html;
  root.classList.add("is-open");
  document.body.classList.add("modal-lock");
  return root;
};
window.closeModal = function closeModal() {
  if (!modalRoot) return;
  modalRoot.classList.remove("is-open");
  document.body.classList.remove("modal-lock");
};
