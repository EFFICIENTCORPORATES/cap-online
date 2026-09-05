const PDF_PRODUCTS = [
  { id: "book-qb-pdf", title: "The Question Bank Book — PDF access", price: 199 },
  { id: "book-sb-pdf", title: "The Exam Strategy Book — PDF access", price: 99 },
];

const STATUS_LABELS = { paid: "Paid", pending: "Pending", failed: "Failed" };

const params = new URLSearchParams(location.search);
const pendingBuy = params.get("buy");

const box = document.getElementById("dash-box");

async function getMe() {
  const res = await fetch("/api/me", { credentials: "include" });
  return res.json();
}

async function getProfile() {
  const res = await fetch("/api/profile", { credentials: "include" });
  if (!res.ok) return { name: "", phone: "" };
  return res.json();
}

async function getMyOrders() {
  const res = await fetch("/api/orders/mine", { credentials: "include" });
  if (!res.ok) return [];
  const data = await res.json();
  return data.orders || [];
}

function renderLogin(prefillEmail) {
  box.innerHTML = `
    <h2>Log in</h2>
    <p class="note">Enter your email — we'll send a 6-digit code, no password needed.</p>
    <form id="email-form" class="modal-form">
      <label>Email<input type="email" name="email" required value="${prefillEmail || ""}"></label>
      <button type="submit" class="button button-primary">Send code</button>
    </form>
    <div id="code-area" style="display:none;margin-top:16px;">
      <form id="code-form" class="modal-form">
        <label>6-digit code<input type="text" name="code" inputmode="numeric" pattern="[0-9]{6}" maxlength="6" required></label>
        <button type="submit" class="button button-primary">Verify &amp; continue</button>
      </form>
    </div>
    <p id="login-status" class="status-line"></p>
  `;

  let emailSent = "";
  document.getElementById("email-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = new FormData(e.target).get("email");
    const status = document.getElementById("login-status");
    status.textContent = "Sending code…";
    try {
      const res = await fetch("/api/otp/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Could not send the code.");
      emailSent = email;
      document.getElementById("code-area").style.display = "block";
      status.textContent = "Code sent — check your inbox.";
    } catch (err) {
      status.textContent = err.message;
    }
  });

  document.getElementById("code-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const code = new FormData(e.target).get("code");
    const status = document.getElementById("login-status");
    status.textContent = "Verifying…";
    try {
      const res = await fetch("/api/otp/verify", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: emailSent, code }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "That code didn't work.");
      await boot();
    } catch (err) {
      status.textContent = err.message;
    }
  });
}

function askNamePhoneThenBuy(product, profile) {
  window.openModal(`
    <h3>${product.title}</h3>
    <p class="note">₹${product.price}</p>
    <form class="modal-form" id="pdf-buy-form">
      <label>Full name<input name="name" required value="${(profile && profile.name) || ""}"></label>
      <label>Phone / WhatsApp<input type="tel" name="phone" required value="${(profile && profile.phone) || ""}"></label>
      <button type="submit" class="button button-primary">Proceed to pay</button>
    </form>
  `);
  document.getElementById("pdf-buy-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.target).entries());
    window.closeModal();
    window.buyProduct(product.id, {
      buyer: { name: data.name, phone: data.phone, email: "" }, // email is fixed server-side to the logged-in session
      onSuccess: () => boot(),
      onError: (err) => alert(err.message),
    });
  });
}

function formatDate(iso) {
  if (!iso) return "";
  // D1 stores UTC "YYYY-MM-DD HH:MM:SS" — make it parseable, then show a
  // plain readable date (no need for exact time-of-day here).
  const d = new Date(iso.replace(" ", "T") + "Z");
  if (isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("en-IN", { year: "numeric", month: "short", day: "numeric" });
}

function renderOrderHistory(orders) {
  if (!orders.length) {
    return `<p class="note">No orders yet.</p>`;
  }
  return `<ul class="order-list">${orders
    .map((o) => {
      const badgeClass = `status-${o.status}`;
      const label = STATUS_LABELS[o.status] || o.status;
      return `<li class="order-item">
        <div class="order-top">
          <span class="order-title">${o.productTitle}</span>
          <span class="order-badge ${badgeClass}">${label}</span>
        </div>
        <div class="order-meta">₹${o.amountRupees} · Ordered ${formatDate(o.createdAt)}${o.paidAt ? " · Paid " + formatDate(o.paidAt) : ""}</div>
      </li>`;
    })
    .join("")}</ul>`;
}

function wireProfileForm(profile) {
  const form = document.getElementById("profile-form");
  const note = document.getElementById("profile-saved-note");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.target).entries());
    note.textContent = "Saving…";
    try {
      const res = await fetch("/api/profile/update", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: data.name, phone: data.phone }),
      });
      const result = await res.json();
      if (!res.ok) throw new Error(result.error || "Could not save.");
      note.textContent = "Saved.";
    } catch (err) {
      note.textContent = err.message;
    }
  });
}

async function renderDashboard(me) {
  const [profile, orders] = await Promise.all([getProfile(), getMyOrders()]);

  const owned = new Set(me.entitlements || []);
  const libraryRows = PDF_PRODUCTS.map((p) => {
    if (owned.has(p.id)) {
      return `<li class="entitlement-item"><span>${p.title}</span>
        <a class="button button-primary" href="reader.html?product=${encodeURIComponent(p.id)}">Read now</a></li>`;
    }
    return `<li class="entitlement-item"><span>${p.title} — ₹${p.price}</span>
      <button type="button" class="button button-primary" data-buy="${p.id}">Buy PDF access</button></li>`;
  }).join("");

  box.innerHTML = `
    <h2>Your dashboard</h2>
    <p class="note">Logged in as ${me.email}</p>

    <div class="dash-section">
      <h3>Profile</h3>
      <form class="profile-form" id="profile-form">
        <label>Full name<input name="name" required value="${profile.name || ""}"></label>
        <label>Phone / WhatsApp<input type="tel" name="phone" required value="${profile.phone || ""}"></label>
        <button type="submit" class="button button-primary">Save</button>
      </form>
      <p class="profile-saved-note" id="profile-saved-note"></p>
    </div>

    <div class="dash-section">
      <h3>Your library</h3>
      <ul class="entitlement-list">${libraryRows}</ul>
    </div>

    <div class="dash-section">
      <h3>Order history</h3>
      ${renderOrderHistory(orders)}
    </div>

    <div class="dash-section">
      <button type="button" class="button" id="logout-btn" style="background:transparent;border:1.5px solid var(--ink);">Log out</button>
    </div>
  `;

  wireProfileForm(profile);

  box.querySelectorAll("[data-buy]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const product = PDF_PRODUCTS.find((p) => p.id === btn.dataset.buy);
      askNamePhoneThenBuy(product, profile);
    });
  });
  document.getElementById("logout-btn").addEventListener("click", async () => {
    await fetch("/api/logout", { method: "POST", credentials: "include" });
    boot();
  });

  return profile;
}

async function boot() {
  const me = await getMe();
  if (!me.loggedIn) {
    renderLogin();
    return;
  }
  const profile = await renderDashboard(me);
  if (pendingBuy) {
    const product = PDF_PRODUCTS.find((p) => p.id === pendingBuy);
    if (product && !(me.entitlements || []).includes(product.id)) {
      askNamePhoneThenBuy(product, profile);
    }
    history.replaceState(null, "", "dashboard.html");
  }
}

boot();
