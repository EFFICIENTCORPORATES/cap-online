const box = document.getElementById("admin-box");

async function getAdminMe() {
  const res = await fetch("/api/admin/me", { credentials: "include" });
  return res.json();
}

function renderLogin(errorMsg) {
  box.innerHTML = `
    <h2>Admin login</h2>
    <p class="note">This area is for processing privacy-policy data-deletion requests only.</p>
    <form id="admin-login-form" class="modal-form">
      <label>Username<input type="text" name="username" required autocomplete="username"></label>
      <label>Password<input type="password" name="password" required autocomplete="current-password"></label>
      <button type="submit" class="button button-primary">Log in</button>
    </form>
    <p class="status-line" id="admin-login-status">${errorMsg || ""}</p>
  `;
  TS.mount(document.getElementById("admin-login-form"));
  document.getElementById("admin-login-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.target).entries());
    data.turnstileToken = TS.token(e.target);
    TS.reset(e.target);
    const status = document.getElementById("admin-login-status");
    status.textContent = "Logging in…";
    try {
      const res = await fetch("/api/admin/login", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      const result = await res.json();
      if (!res.ok) throw new Error(result.error || "Login failed.");
      boot();
    } catch (err) {
      status.textContent = err.message;
    }
  });
}

function renderTool(username) {
  box.innerHTML = `
    <h2>Delete a student's data</h2>
    <p class="note">Logged in as ${username}</p>
    <div class="admin-warning">This is a real, mostly irreversible action. Look up the email first, review what it would affect, then confirm.</div>
    <form id="lookup-form" class="modal-form">
      <label>Student email<input type="email" name="email" required></label>
      <button type="submit" class="button button-primary">Look up</button>
    </form>
    <div id="lookup-result"></div>
    <p style="margin-top:24px;"><button type="button" class="button" id="admin-logout-btn" style="background:transparent;border:1.5px solid var(--ink);">Log out</button></p>
  `;

  document.getElementById("lookup-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = new FormData(e.target).get("email");
    const resultEl = document.getElementById("lookup-result");
    resultEl.innerHTML = `<p class="status-line">Looking up…</p>`;
    try {
      const res = await fetch("/api/admin/lookup", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Lookup failed.");
      renderLookupResult(data);
    } catch (err) {
      resultEl.innerHTML = `<p class="status-line">${err.message}</p>`;
    }
  });

  document.getElementById("admin-logout-btn").addEventListener("click", async () => {
    await fetch("/api/admin/logout", { method: "POST", credentials: "include" });
    boot();
  });
}

function renderLookupResult(data) {
  const resultEl = document.getElementById("lookup-result");
  const nothingFound =
    !data.orders && !data.hasProfile && !data.entitlements && !data.sessions && !data.contactMessages && !data.otpCodes;

  if (nothingFound) {
    resultEl.innerHTML = `<div class="admin-lookup-result">No data found for <strong>${data.email}</strong>.</div>`;
    return;
  }

  resultEl.innerHTML = `
    <div class="admin-lookup-result">
      <p><strong>${data.email}</strong> — deleting will:</p>
      <ul>
        <li>${data.orders} order(s) — name/email/phone/shipping anonymized, amount/product/date/status kept for accounting</li>
        <li>Profile: ${data.hasProfile ? "deleted" : "none saved"}</li>
        <li>${data.entitlements} PDF entitlement(s) — deleted (reader access is lost)</li>
        <li>${data.sessions} login session(s) — deleted (logs them out everywhere)</li>
        <li>${data.contactMessages} contact-form message(s) — deleted</li>
        <li>${data.otpCodes} login code record(s) — deleted</li>
      </ul>
      <button type="button" class="button button-primary" id="confirm-delete-btn" style="margin-top:10px;background:#b42318;">Confirm delete</button>
      <p class="admin-note">This is logged with your username and the time, for your own records.</p>
    </div>
  `;
  document.getElementById("confirm-delete-btn").addEventListener("click", async () => {
    if (!confirm(`Really delete/anonymize all data for ${data.email}? This cannot be undone.`)) return;
    const btn = document.getElementById("confirm-delete-btn");
    btn.disabled = true;
    btn.textContent = "Deleting…";
    try {
      const res = await fetch("/api/admin/delete-student", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: data.email }),
      });
      const result = await res.json();
      if (!res.ok) throw new Error(result.error || "Delete failed.");
      document.getElementById("lookup-result").innerHTML = `<div class="admin-lookup-result">Done. ${result.ordersAnonymized} order(s) anonymized, ${result.profileDeleted} profile row(s), ${result.entitlementsDeleted} entitlement(s), ${result.sessionsDeleted} session(s), ${result.contactMessagesDeleted} contact message(s), ${result.otpCodesDeleted} login code record(s) removed.</div>`;
    } catch (err) {
      alert(err.message);
      btn.disabled = false;
      btn.textContent = "Confirm delete";
    }
  });
}

async function boot() {
  const me = await getAdminMe();
  if (!me.loggedIn) {
    renderLogin();
    return;
  }
  renderTool(me.username);
}

boot();
