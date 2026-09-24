/* /videos/ — Videos tab (grid + one player) and Shorts tab (vertical feed with
   auto-scroll). Data: /videos/videos.json. Plays through the official YouTube
   IFrame Player API from youtube-nocookie.com, so visitors never leave the site. */
(function () {
  "use strict";

  var PREFS_KEY = "capranav.videos.prefs";
  var $ = function (id) { return document.getElementById(id); };
  var reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // ---- preferences (per-viewer convenience only; the page works without storage) ----
  var prefs = { auto: true, loop: false, mute: true, speed: "1", size: "comfort" };
  try {
    var saved = JSON.parse(localStorage.getItem(PREFS_KEY) || "null");
    if (saved && typeof saved === "object") Object.keys(prefs).forEach(function (k) { if (k in saved) prefs[k] = saved[k]; });
  } catch (e) { /* storage blocked: keep defaults */ }
  function savePrefs() { try { localStorage.setItem(PREFS_KEY, JSON.stringify(prefs)); } catch (e) { /* ignore */ } }

  // ---- YouTube IFrame API, loaded on first use ----
  var apiPromise = null;
  function loadApi() {
    if (apiPromise) return apiPromise;
    apiPromise = new Promise(function (resolve, reject) {
      if (window.YT && window.YT.Player) return resolve(window.YT);
      var previous = window.onYouTubeIframeAPIReady;
      window.onYouTubeIframeAPIReady = function () { if (previous) previous(); resolve(window.YT); };
      var s = document.createElement("script");
      s.src = "https://www.youtube.com/iframe_api";
      s.onerror = function () { apiPromise = null; reject(new Error("YouTube player could not be loaded")); };
      document.head.appendChild(s);
    });
    return apiPromise;
  }

  function thumb(id) { return "https://i.ytimg.com/vi/" + id + "/hqdefault.jpg"; }
  function ytUrl(id) { return "https://www.youtube.com/watch?v=" + id; }
  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  var data = { groups: [], videos: [] };
  var groupById = {};
  var tab = "video";

  // =====================================================================
  // Videos tab
  // =====================================================================
  var videoFilter = "all";
  var vPlayer = null;
  var vCurrent = null;

  function videosOfType(type) { return data.videos.filter(function (v) { return v.type === type; }); }

  function renderChips(type, filterValue, onPick) {
    var box = $("chips-" + type);
    box.textContent = "";
    var items = [{ id: "all", title: "All" }, { id: "important", title: "★ Important" }]
      .concat(data.groups.filter(function (g) { return g.type === type; }));
    items.forEach(function (g) {
      var b = el("button", null, g.title);
      b.type = "button";
      b.setAttribute("aria-pressed", String(g.id === filterValue));
      b.addEventListener("click", function () { onPick(g.id); });
      box.appendChild(b);
    });
  }

  function matches(v, filter) {
    if (filter === "all") return true;
    if (filter === "important") return !!v.important;
    return v.group === filter;
  }

  function renderVideos() {
    renderChips("video", videoFilter, function (f) { videoFilter = f; renderVideos(); });
    var host = $("cards");
    host.textContent = "";
    var list = videosOfType("video").filter(function (v) { return matches(v, videoFilter); });
    var shown = 0;
    data.groups.filter(function (g) { return g.type === "video"; }).forEach(function (g) {
      var inGroup = list.filter(function (v) { return v.group === g.id; });
      if (!inGroup.length) return;
      var head = el("div", "group-head");
      head.appendChild(el("h3", null, g.title));
      if (g.blurb) head.appendChild(el("p", null, g.blurb));
      host.appendChild(head);
      inGroup.forEach(function (v) { host.appendChild(videoCard(v)); shown++; });
    });
    $("empty").hidden = shown > 0 || tab !== "video";
  }

  function videoCard(v) {
    var c = el("button", "card");
    c.type = "button";
    c.dataset.id = v.id;
    if (vCurrent === v.id) c.setAttribute("aria-current", "true");
    var t = el("span", "thumb");
    var img = el("img");
    img.src = thumb(v.id); img.alt = ""; img.loading = "lazy"; img.decoding = "async";
    t.appendChild(img);
    var p = el("span", "play"); p.appendChild(el("span", null, "▶")); t.appendChild(p);
    if (v.important) t.appendChild(el("span", "badge-imp", "★ Important"));
    c.appendChild(t);
    c.appendChild(el("span", "card-body", v.title));
    c.addEventListener("click", function () { playVideo(v.id, true); });
    return c;
  }

  function playVideo(id, autoplay) {
    var v = data.videos.filter(function (x) { return x.id === id && x.type === "video"; })[0];
    if (!v) return;
    vCurrent = id;
    $("player-wrap").hidden = false;
    $("player-title").textContent = v.title;
    $("player-yt").href = ytUrl(id);
    Array.prototype.forEach.call(document.querySelectorAll(".card"), function (c) {
      if (c.dataset.id === id) c.setAttribute("aria-current", "true"); else c.removeAttribute("aria-current");
    });
    setHash("v=" + id);
    if (autoplay) $("player-wrap").scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "start" });
    loadApi().then(function (YT) {
      if (vPlayer && vPlayer.loadVideoById) {
        if (autoplay) vPlayer.loadVideoById(id); else vPlayer.cueVideoById(id);
        return;
      }
      vPlayer = new YT.Player("player-host", {
        host: "https://www.youtube-nocookie.com",
        videoId: id,
        playerVars: { rel: 0, playsinline: 1, modestbranding: 1, autoplay: autoplay ? 1 : 0 },
        events: { onError: function () { $("player-title").textContent = v.title + " — can't be played here. Use “Watch on YouTube”."; } }
      });
    }).catch(function () {
      $("player-title").textContent = "The player could not be loaded. Use “Watch on YouTube”.";
    });
  }

  // =====================================================================
  // Shorts tab
  // =====================================================================
  var shortFilter = "all";
  var shorts = [];       // current filtered list
  var slides = [];       // slide elements, same order
  var sPlayer = null;    // the one live Player, in slides[activeIndex]
  var activeIndex = -1;
  var observer = null;
  var startTimer = null;
  var skipTimer = null;
  var suppressHash = false;

  function renderShorts(startId) {
    renderChips("short", shortFilter, function (f) { shortFilter = f; renderShorts(); });
    destroyShortPlayer();
    var reel = $("reel");
    reel.textContent = "";
    if (observer) observer.disconnect();
    shorts = videosOfType("short").filter(function (v) { return matches(v, shortFilter); });
    slides = shorts.map(function (v) {
      var s = el("div", "slide");
      s.dataset.id = v.id;
      var img = el("img", "poster");
      img.src = thumb(v.id); img.alt = ""; img.loading = "lazy"; img.decoding = "async";
      s.appendChild(img);
      var cap = el("div", "slide-title", v.title);
      var g = groupById[v.group];
      if (g) cap.appendChild(el("small", null, g.title));
      s.appendChild(cap);
      var fb = el("div", "fallback");
      fb.appendChild(el("span", null, "This Short can't be played here."));
      var a = el("a", null, "Watch on YouTube ↗");
      a.href = "https://www.youtube.com/shorts/" + v.id; a.target = "_blank"; a.rel = "noopener";
      fb.appendChild(a);
      s.appendChild(fb);
      reel.appendChild(s);
      return s;
    });
    $("empty").hidden = shorts.length > 0 || tab !== "short";
    activeIndex = -1;
    updateNav(0);
    if (!shorts.length) return;

    var idx = 0;
    if (startId) {
      var found = shorts.findIndex(function (v) { return v.id === startId; });
      if (found >= 0) idx = found;
    }
    reel.scrollTo({ top: idx * reel.clientHeight, behavior: "auto" });

    observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting && e.intersectionRatio >= 0.6) {
          var i = slides.indexOf(e.target);
          if (i >= 0 && i !== activeIndex && tab === "short") activate(i);
        }
      });
    }, { root: reel, threshold: [0.6, 0.9] });
    slides.forEach(function (s) { observer.observe(s); });
    if (tab === "short") activate(idx);
  }

  function updateNav(i) {
    $("reel-up").disabled = i <= 0;
    $("reel-down").disabled = i >= shorts.length - 1;
  }

  function setStatus(msg) { $("reel-status").textContent = msg || ""; }

  function destroyShortPlayer() {
    clearTimeout(startTimer); clearTimeout(skipTimer);
    if (sPlayer) { try { sPlayer.destroy(); } catch (e) { /* already gone */ } sPlayer = null; }
    Array.prototype.forEach.call(document.querySelectorAll(".unmute"), function (n) { n.remove(); });
    slides.forEach(function (s) {
      s.classList.remove("live");
      var fb = s.querySelector(".fallback"); if (fb) fb.classList.remove("on");
    });
  }

  function goTo(i, instant) {
    if (i < 0 || i >= slides.length) return false;
    var reel = $("reel");
    reel.scrollTo({ top: i * reel.clientHeight, behavior: instant || reduceMotion ? "auto" : "smooth" });
    return true;
  }

  function currentIndex() {
    var reel = $("reel");
    return reel.clientHeight ? Math.round(reel.scrollTop / reel.clientHeight) : 0;
  }

  function applyMute() {
    if (!sPlayer || !sPlayer.mute) return;
    if (prefs.mute) sPlayer.mute(); else sPlayer.unMute();
    var btn = document.querySelector(".unmute");
    if (btn) btn.classList.toggle("on", prefs.mute);
  }

  function activate(i) {
    activeIndex = i;
    updateNav(i);
    var v = shorts[i];
    setHash("s=" + v.id);
    destroyShortPlayer();
    setStatus("");
    loadApi().then(function (YT) {
      if (activeIndex !== i || tab !== "short") return; // scrolled on while the API loaded
      var slide = slides[i];
      slide.classList.add("live");
      var host = el("div");
      slide.insertBefore(host, slide.firstChild.nextSibling);
      var unmute = el("button", "unmute", "🔇 Tap for sound");
      unmute.type = "button";
      unmute.addEventListener("click", function () {
        prefs.mute = false; $("opt-mute").checked = false; savePrefs(); applyMute();
      });
      slide.appendChild(unmute);
      sPlayer = new YT.Player(host, {
        host: "https://www.youtube-nocookie.com",
        videoId: v.id,
        playerVars: { rel: 0, playsinline: 1, modestbranding: 1, autoplay: 1, mute: prefs.mute ? 1 : 0 },
        events: {
          onReady: function (ev) {
            ev.target.setPlaybackRate(parseFloat(prefs.speed));
            applyMute();
            ev.target.playVideo();
            // Autoplay with sound can be refused; fall back to muted instead of a dead frame.
            startTimer = setTimeout(function () {
              if (sPlayer !== ev.target || activeIndex !== i) return;
              var st = ev.target.getPlayerState();
              if (st !== 1 && st !== 3) {
                prefs.mute = true; $("opt-mute").checked = true;
                applyMute(); ev.target.playVideo();
                setStatus("Your browser blocked sound on autoplay, so this Short started muted. Tap for sound.");
              }
            }, 2500);
          },
          onStateChange: function (ev) {
            if (ev.data === 1) { ev.target.setPlaybackRate(parseFloat(prefs.speed)); }
            if (ev.data === 0) onEnded(i, ev.target);
          },
          onError: function () {
            var fb = slide.querySelector(".fallback"); if (fb) fb.classList.add("on");
            if (prefs.auto) skipTimer = setTimeout(function () { goTo(i + 1); }, 1800);
          }
        }
      });
    }).catch(function () { setStatus("The player could not be loaded. Check your connection and reload."); });
  }

  function onEnded(i, player) {
    if (prefs.loop) { player.seekTo(0, true); player.playVideo(); return; }
    if (prefs.auto) {
      if (!goTo(i + 1)) setStatus("That was the last Short in this list.");
    }
  }

  function togglePlay() {
    if (!sPlayer || !sPlayer.getPlayerState) return;
    if (sPlayer.getPlayerState() === 1) sPlayer.pauseVideo(); else sPlayer.playVideo();
  }

  // =====================================================================
  // Tabs, hash, settings wiring
  // =====================================================================
  function setHash(h) {
    try { history.replaceState(null, "", "#" + h); } catch (e) { /* ignore */ }
  }

  function showTab(next, opts) {
    opts = opts || {};
    tab = next;
    ["video", "short"].forEach(function (t) {
      $("tab-" + t).setAttribute("aria-selected", String(t === next));
      $("pane-" + t).hidden = t !== next;
    });
    if (next === "short") {
      if (vPlayer && vPlayer.pauseVideo) try { vPlayer.pauseVideo(); } catch (e) { /* ignore */ }
      if (!opts.keepHash) setHash("shorts");
      renderShorts(opts.shortId);
      // Bring the whole frame into view when the visitor switches to Shorts.
      if (!opts.keepHash) $("reel-layout").scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "start" });
    } else {
      destroyShortPlayer(); activeIndex = -1;
      renderVideos();
      if (!opts.keepHash) setHash("videos");
    }
  }

  function wireSettings() {
    $("opt-auto").checked = !!prefs.auto;
    $("opt-loop").checked = !!prefs.loop;
    $("opt-mute").checked = !!prefs.mute;
    $("opt-speed").value = String(prefs.speed);
    $("opt-size").value = prefs.size;
    $("reel-layout").dataset.size = prefs.size;
    $("opt-auto").addEventListener("change", function (e) { prefs.auto = e.target.checked; savePrefs(); });
    $("opt-loop").addEventListener("change", function (e) { prefs.loop = e.target.checked; savePrefs(); });
    $("opt-mute").addEventListener("change", function (e) { prefs.mute = e.target.checked; savePrefs(); applyMute(); });
    $("opt-speed").addEventListener("change", function (e) {
      prefs.speed = e.target.value; savePrefs();
      if (sPlayer && sPlayer.setPlaybackRate) sPlayer.setPlaybackRate(parseFloat(prefs.speed));
    });
    $("opt-size").addEventListener("change", function (e) {
      prefs.size = e.target.value; savePrefs();
      $("reel-layout").dataset.size = prefs.size;
      var i = Math.max(activeIndex, 0);
      requestAnimationFrame(function () { goTo(i, true); });
    });
    $("reel-up").addEventListener("click", function () { goTo(currentIndex() - 1); });
    $("reel-down").addEventListener("click", function () { goTo(currentIndex() + 1); });
    window.addEventListener("resize", function () { if (tab === "short" && activeIndex >= 0) goTo(activeIndex, true); });
    document.addEventListener("keydown", function (e) {
      if (tab !== "short") return;
      var t = e.target && e.target.tagName;
      if (t === "INPUT" || t === "SELECT" || t === "TEXTAREA" || e.metaKey || e.ctrlKey || e.altKey) return;
      if (e.key === "ArrowDown" || e.key === "j") { e.preventDefault(); goTo(currentIndex() + 1); }
      else if (e.key === "ArrowUp" || e.key === "k") { e.preventDefault(); goTo(currentIndex() - 1); }
      else if (e.key === " " && t !== "BUTTON") { e.preventDefault(); togglePlay(); }
    });
    document.addEventListener("visibilitychange", function () {
      if (document.hidden && sPlayer && sPlayer.pauseVideo) try { sPlayer.pauseVideo(); } catch (e) { /* ignore */ }
    });
  }

  function init() {
    $("tab-video").addEventListener("click", function () { showTab("video"); });
    $("tab-short").addEventListener("click", function () { showTab("short"); });
    wireSettings();

    fetch("/videos/videos.json", { cache: "no-cache" })
      .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
      .then(function (json) {
        data = { groups: json.groups || [], videos: json.videos || [] };
        data.groups.forEach(function (g) { groupById[g.id] = g; });
        var h = (location.hash || "").replace(/^#/, "");
        var m;
        if ((m = /^s=([\w-]{6,20})$/.exec(h))) { showTab("short", { shortId: m[1], keepHash: true }); }
        else if (h === "shorts") { showTab("short"); }
        else if ((m = /^v=([\w-]{6,20})$/.exec(h))) { showTab("video", { keepHash: true }); playVideo(m[1], false); }
        else { showTab("video", { keepHash: true }); }
      })
      .catch(function () {
        $("empty").textContent = "The video list could not be loaded. Please refresh.";
        $("empty").hidden = false;
      });
  }

  init();
})();
