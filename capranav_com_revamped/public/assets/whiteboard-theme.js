(() => {
  const path = (location.pathname.split("/").pop() || "index.html").toLowerCase();
  const pageClass = "wb-page-" + path.replace(/\.html$/, "").replace(/[^a-z0-9]+/g, "-");
  document.body.classList.add("wb-whiteboard", pageClass);
  document.querySelectorAll("h1 em, h2 em").forEach((el) => el.classList.add("wb-marker-underline"));
})();
