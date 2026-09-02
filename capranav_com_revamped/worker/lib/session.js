const COOKIE_NAME = "cp_session";
const SESSION_HOURS = 24 * 30; // 30 days
const OTP_MINUTES = 10;

function randomToken(bytes = 32) {
  const arr = new Uint8Array(bytes);
  crypto.getRandomValues(arr);
  return Array.from(arr, (b) => b.toString(16).padStart(2, "0")).join("");
}

export function randomOtpCode() {
  const n = crypto.getRandomValues(new Uint32Array(1))[0] % 1000000;
  return String(n).padStart(6, "0");
}

export function otpExpiry() {
  return new Date(Date.now() + OTP_MINUTES * 60 * 1000).toISOString();
}

export async function createSession(db, email) {
  const token = randomToken();
  const expires = new Date(Date.now() + SESSION_HOURS * 3600 * 1000).toISOString();
  await db
    .prepare("INSERT INTO sessions (token, user_email, expires_at) VALUES (?, ?, ?)")
    .bind(token, email, expires)
    .run();
  return { token, expires };
}

export function sessionCookieHeader(token, expiresIso) {
  const expires = new Date(expiresIso).toUTCString();
  return `${COOKIE_NAME}=${token}; Path=/; Expires=${expires}; HttpOnly; Secure; SameSite=Lax`;
}

export function clearCookieHeader() {
  return `${COOKIE_NAME}=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT; HttpOnly; Secure; SameSite=Lax`;
}

function readCookie(request, name) {
  const header = request.headers.get("Cookie") || "";
  for (const part of header.split(";")) {
    const [k, ...rest] = part.trim().split("=");
    if (k === name) return rest.join("=");
  }
  return null;
}

/** Returns the logged-in user's email, or null. Expired sessions are lazily deleted. */
export async function getSessionEmail(db, request) {
  const token = readCookie(request, COOKIE_NAME);
  if (!token) return null;
  const row = await db
    .prepare("SELECT user_email, expires_at FROM sessions WHERE token = ?")
    .bind(token)
    .first();
  if (!row) return null;
  if (new Date(row.expires_at).getTime() < Date.now()) {
    await db.prepare("DELETE FROM sessions WHERE token = ?").bind(token).run();
    return null;
  }
  return row.user_email;
}

export function isValidEmail(email) {
  return typeof email === "string" && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());
}
