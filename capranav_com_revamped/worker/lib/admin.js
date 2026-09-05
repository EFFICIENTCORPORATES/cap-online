/*
  Single-admin login, entirely separate from the student OTP-login system
  (session.js) — different cookie name, different table, gates only the
  narrow data-deletion tool in worker/index.js. Password is checked as
  PLAIN TEXT on purpose — see schema.sql's own comment on admin_users for
  why (a deliberate, informed choice by Pranav, not an oversight).
*/

const ADMIN_COOKIE_NAME = "cp_admin_session";
const ADMIN_SESSION_HOURS = 8;
const LOGIN_RATE_WINDOW_MINUTES = 15;
const LOGIN_MAX_FAILURES_PER_WINDOW = 5;

function randomToken(bytes = 32) {
  const arr = new Uint8Array(bytes);
  crypto.getRandomValues(arr);
  return Array.from(arr, (b) => b.toString(16).padStart(2, "0")).join("");
}

function readCookie(request, name) {
  const header = request.headers.get("Cookie") || "";
  for (const part of header.split(";")) {
    const [k, ...rest] = part.trim().split("=");
    if (k === name) return rest.join("=");
  }
  return null;
}

export function adminCookieHeader(token, expiresIso) {
  const expires = new Date(expiresIso).toUTCString();
  return `${ADMIN_COOKIE_NAME}=${token}; Path=/; Expires=${expires}; HttpOnly; Secure; SameSite=Strict`;
}

export function clearAdminCookieHeader() {
  return `${ADMIN_COOKIE_NAME}=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT; HttpOnly; Secure; SameSite=Strict`;
}

/*
  Returns true only if a genuine failed-attempt limit hasn't been hit for
  this IP — checked BEFORE the password comparison, so a brute-force run
  against an unhashed password is at least bounded to a handful of
  guesses per window, not unlimited.
*/
export async function isLoginRateLimited(db, ip) {
  const row = await db
    .prepare(
      `SELECT COUNT(*) AS c FROM admin_login_attempts WHERE ip = ? AND created_at > datetime('now', '-${LOGIN_RATE_WINDOW_MINUTES} minutes')`
    )
    .bind(ip)
    .first();
  return !!row && row.c >= LOGIN_MAX_FAILURES_PER_WINDOW;
}

export async function recordFailedLogin(db, ip) {
  await db.prepare("INSERT INTO admin_login_attempts (ip) VALUES (?)").bind(ip).run();
}

export async function verifyAdminLogin(db, username, password) {
  if (!username || !password) return false;
  const row = await db.prepare("SELECT password FROM admin_users WHERE username = ?").bind(username).first();
  if (!row) return false;
  return row.password === password;
}

export async function createAdminSession(db, username) {
  const token = randomToken();
  const expires = new Date(Date.now() + ADMIN_SESSION_HOURS * 3600 * 1000).toISOString();
  await db.prepare("INSERT INTO admin_sessions (token, username, expires_at) VALUES (?, ?, ?)").bind(token, username, expires).run();
  return { token, expires };
}

/** Returns the logged-in admin's username, or null. Expired sessions are lazily deleted. */
export async function getAdminUsername(db, request) {
  const token = readCookie(request, ADMIN_COOKIE_NAME);
  if (!token) return null;
  const row = await db.prepare("SELECT username, expires_at FROM admin_sessions WHERE token = ?").bind(token).first();
  if (!row) return null;
  if (new Date(row.expires_at).getTime() < Date.now()) {
    await db.prepare("DELETE FROM admin_sessions WHERE token = ?").bind(token).run();
    return null;
  }
  return row.username;
}
