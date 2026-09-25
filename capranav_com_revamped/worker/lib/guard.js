/*
  Bot and scraping guards for the data the site publishes.

  Static data files (topic data, the Excel sheets, Must Practice questions) are served through the Worker
  (wrangler.toml [assets] run_worker_first) so they can be checked before being returned:

    1. Same-site only. A page on capranav.com that fetches a file sends Sec-Fetch-Site: same-origin (or a
       Referer from this site). A bare wget/curl/python request sends neither and is refused. This is a speed
       bump, not a wall: a determined scraper can add the header. It stops mirror tools and naive scripts.
    2. Per-IP rate limit through the Workers Rate Limiting binding.

  Search and AI crawlers read the HTML pages, which are not affected: robots.txt disallows /api/ and none of
  the SEO text needs these data files.
*/

const SITE_HOSTS = ["capranav.com", "www.capranav.com"];

export const DATA_PATHS = [/^\/topics\/data\//, /^\/practice-with-pranav-bhaiya\/must-practice\/data\//];

export function isDataPath(pathname) {
  return DATA_PATHS.some((re) => re.test(pathname));
}

function refererIsSite(request) {
  const ref = request.headers.get("Referer");
  if (!ref) return false;
  try {
    return SITE_HOSTS.includes(new URL(ref).hostname) || new URL(ref).hostname.endsWith(".workers.dev") || new URL(ref).hostname === "localhost";
  } catch { return false; }
}

export function isSameSiteRequest(request) {
  const site = request.headers.get("Sec-Fetch-Site");
  if (site) return site === "same-origin" || site === "same-site";
  return refererIsSite(request); // older browsers send Referer but not Sec-Fetch-Site
}

export function clientIp(request) {
  return request.headers.get("CF-Connecting-IP") || "unknown";
}

export async function limited(limiter, request, keyPrefix) {
  if (!limiter) return false; // binding absent (e.g. some local setups): fail open
  try {
    const { success } = await limiter.limit({ key: `${keyPrefix}:${clientIp(request)}` });
    return !success;
  } catch { return false; }
}

export function deny(status, message, extra = {}) {
  return new Response(JSON.stringify({ error: message }), {
    status,
    headers: { "Content-Type": "application/json", "Cache-Control": "no-store", ...extra },
  });
}
