/*
  Server-side check of a Cloudflare Turnstile token (widget "capranav.com", secret in the
  TURNSTILE_SECRET Worker secret). Returns null when the request may proceed, or an
  error Response. If the secret is not configured the check is skipped, so local dev works.
*/
export async function checkTurnstile(request, env, token, json) {
  if (!env.TURNSTILE_SECRET) return null;
  if (!token) {
    return json({ error: "Please complete the security check and try again." }, { status: 400 });
  }
  const form = new FormData();
  form.append("secret", env.TURNSTILE_SECRET);
  form.append("response", token);
  const ip = request.headers.get("CF-Connecting-IP");
  if (ip) form.append("remoteip", ip);
  try {
    const res = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", { method: "POST", body: form });
    const data = await res.json();
    if (data.success) return null;
  } catch (e) {
    // Fall through to the error below: never let a failed check pass.
  }
  return json({ error: "The security check failed. Please refresh the page and try again." }, { status: 403 });
}
