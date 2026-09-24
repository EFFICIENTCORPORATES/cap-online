# Videos & Shorts (`/videos/`)

Public page (no login) that plays Pranav's YouTube videos and Shorts on the site.
Built 2026-09-24. Files:

| File | Role |
|---|---|
| `public/videos/index.html` | Page shell (tabs, chips, player, Shorts feed, settings) |
| `public/videos/videos.json` | **The data.** Edit this to add or change videos |
| `public/assets/videos.js` | Behaviour (YouTube IFrame API, feed, auto-scroll, settings) |
| `public/assets/videos.css` | Layout; colours and fonts come from `anatomy.css` |

## How it plays

Official YouTube embed via the IFrame Player API, served from
`youtube-nocookie.com`. Visitors stay on capranav.com. YouTube's own logo and
"Watch on YouTube" link remain on the player (a YouTube requirement — do not hide
them). A Short is an ordinary video with a vertical shape, so the same `id` plays
in the embed; YouTube's own swipe-up Shorts feed cannot be embedded, so the feed
here is built by hand.

**Videos tab:** grouped thumbnail cards; clicking one loads it in the player above.
**Shorts tab:** one full-height vertical player at a time (scroll-snap). Only the
active Short is loaded; the previous player is destroyed when you move on.
Swipe/scroll, ▲▼ buttons, ↑ ↓ or J / K, Space to play/pause.

Settings (remembered in the browser's localStorage; the page works without it):
auto-scroll to next on end (default on), loop this Short, sound off (default on),
speed 0.75–2×, size Compact / Comfortable / Large.

**Autoplay and sound.** Browsers only allow autoplay with sound after the visitor
has interacted with the page, so the first Short starts muted with a "Tap for
sound" button. If a browser refuses autoplay anyway, the page falls back to muted
playback and says so.

**Unplayable videos.** If a video has embedding switched off or is removed, a
Short shows a "Watch on YouTube" fallback and (if auto-scroll is on) moves on
after ~2 s. Videos must be **Public or Unlisted** with **Allow embedding** on.

Deep links: `/videos/#v=<id>` (a video), `/videos/#s=<id>` (a Short), `/videos/#shorts`.

## `videos.json`

```json
{ "id": "nNrcAZEIk_k",          // 11-char YouTube id (from watch?v=..., youtu.be/..., or /shorts/...)
  "type": "video",               // "video" | "short"
  "group": "study-plan",         // must match a group id; groups have their own "type"
  "important": true,             // shows the ★ Important badge + the Important filter
  "title": "Daily Study Routine",// what the site shows
  "youtube_title": "..." }       // reference only, not displayed
```

Array order is display order within a group. To add a video: find its id, add a
line, run `npx wrangler deploy`. Groups are chosen by the *nature* of the video
(strategy, chapter revision, exam technique, mindset). Only Pranav's own content
is listed — the channel also carries other faculty's lectures, deliberately not included.

Notes on the first list: the 90-days video link Pranav sent carried `&t=1064s`
(a share timestamp); it is ignored, the video starts from 0. The four Shorts
were chosen from titles and hashtags without watching them — review them.

## Planned: move to D1

When the list outgrows a hand-edited file, or someone other than a developer
needs to add videos, move it to D1 and give the admin page a "Videos" form:

```sql
-- migrations/000N_videos.sql
CREATE TABLE IF NOT EXISTS video_groups (
  group_id   TEXT PRIMARY KEY,
  type       TEXT NOT NULL CHECK (type IN ('video','short')),
  title      TEXT NOT NULL,
  blurb      TEXT,
  sort_order INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS videos (
  video_id      TEXT PRIMARY KEY,           -- YouTube id
  type          TEXT NOT NULL CHECK (type IN ('video','short')),
  group_id      TEXT NOT NULL REFERENCES video_groups(group_id),
  title         TEXT NOT NULL,
  youtube_title TEXT,
  important     INTEGER NOT NULL DEFAULT 0 CHECK (important IN (0,1)),
  published     INTEGER NOT NULL DEFAULT 1 CHECK (published IN (0,1)),
  sort_order    INTEGER NOT NULL DEFAULT 0,
  created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_videos_type_group ON videos(type, group_id, sort_order);
```

Migration steps: (1) apply the migration to remote D1; (2) one-off script loads
`videos.json` into the tables; (3) add `GET /api/videos` in `worker/index.js`
returning `{groups, videos}` in the same shape as `videos.json` (published only,
ordered); (4) change the one `fetch("/videos/videos.json")` in `videos.js` to
`/api/videos` — nothing else in the page changes; (5) add admin create/edit/
reorder/hide routes behind `role`-checked admin session, audit-logged like the
other admin actions; (6) keep `videos.json` as a fallback for a release, then delete it.
If videos are ever restricted to logged-in or paying students, YouTube embeds are
not a safe gate (anyone can copy an Unlisted link) — use a private host such as
Cloudflare Stream instead.
