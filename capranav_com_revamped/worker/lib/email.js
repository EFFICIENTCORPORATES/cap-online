/*
  Thin wrapper around Cloudflare's Email Sending REST API.
  https://api.cloudflare.com/client/v4/accounts/{account_id}/email/sending/send
  Same product already verified working for capranav.com's domain.
*/
export async function sendEmail(env, { to, subject, html, fromLocal = "noreply", fromName = "CA Pranav" }) {
  const url = `https://api.cloudflare.com/client/v4/accounts/${env.CF_EMAIL_ACCOUNT_ID}/email/sending/send`;
  const res = await fetch(url, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.CF_EMAIL_API_TOKEN}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      from: `${fromName} <${fromLocal}@capranav.com>`,
      to,
      subject,
      html,
    }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok || !data.success) {
    throw new Error("Email send failed: " + JSON.stringify(data));
  }
  return data;
}

export function otpEmailHtml(code) {
  return `
    <div style="font-family:sans-serif;max-width:420px;margin:0 auto;padding:24px;">
      <p style="font-size:13px;color:#667085;text-transform:uppercase;letter-spacing:.08em;">CA Pranav — login code</p>
      <p style="font-size:36px;font-weight:800;letter-spacing:.06em;margin:12px 0;">${code}</p>
      <p style="font-size:14px;color:#475467;">This code expires in 10 minutes. If you didn't request this, ignore this email.</p>
    </div>`;
}
