/*
  Cloudflare Turnstile for the login-code, contact and admin-login forms.
  TS.mount(form) adds the widget at the end of the form; TS.token(form) returns the
  one-time token to send as `turnstileToken`; TS.reset(form) gets a fresh one after a submit.
  The Worker checks the token with TURNSTILE_SECRET (worker/lib/turnstile.js).
*/
(function () {
  const SITEKEY = "0x4AAAAAAFFFJsKBEWIqBbA_";
  const queue = [];
  const ids = new WeakMap();

  function render(form) {
    if (ids.has(form)) return;
    const box = document.createElement("div");
    box.className = "ts-box";
    box.style.margin = "10px 0";
    box.style.maxWidth = "100%";
    const submit = form.querySelector('button[type="submit"], button:not([type])');
    if (submit && submit.parentNode === form) form.insertBefore(box, submit);
    else form.appendChild(box);
    ids.set(form, window.turnstile.render(box, { sitekey: SITEKEY, theme: "light", size: form.clientWidth && form.clientWidth < 310 ? "compact" : "flexible" }));
  }

  window.__tsReady = function () {
    while (queue.length) render(queue.shift());
  };

  const s = document.createElement("script");
  s.src = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit&onload=__tsReady";
  s.async = true;
  s.defer = true;
  document.head.appendChild(s);

  window.TS = {
    mount(form) {
      if (!form) return;
      if (window.turnstile) render(form);
      else queue.push(form);
    },
    token(form) {
      const id = ids.get(form);
      return (id !== undefined && window.turnstile && window.turnstile.getResponse(id)) || "";
    },
    reset(form) {
      const id = ids.get(form);
      if (id !== undefined && window.turnstile) window.turnstile.reset(id);
    },
  };
})();
