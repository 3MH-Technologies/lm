// ==UserScript==
// @name         Arena Agent (Cloudflare Hub)
// @namespace    arena-agent
// @version      1.0
// @description  Polls a Cloudflare Worker for prompts, executes them inside arena.ai (same-origin = valid reCAPTCHA tokens), posts results back.
// @match        https://arena.ai/*
// @match        https://*.arena.ai/*
// @run-at       document-idle
// @grant        none
// ==/UserScript==

(function () {
  "use strict";

  const HUB = localStorage.getItem("arena_hub_url") || "https://arena-hub.contact-3mh.workers.dev";
  const SECRET = localStorage.getItem("arena_hub_secret") || "";
  const SITE_KEY = "6LeTGMcsAAAAALuIlkVwIxaAuZA8VledA6d3Nnb0";
  const POLL_MS = 4000;

  const log = (...a) => console.log("%c[arena-agent]", "color:#f80", ...a);

  function uuidv7() {
    let ts = Date.now();
    const b = new Uint8Array(16);
    for (let i = 5; i >= 0; i--) { b[i] = ts % 256; ts = Math.floor(ts / 256); }
    crypto.getRandomValues(b.subarray(6));
    b[6] = (b[6] & 0x0f) | 0x70;
    b[8] = (b[8] & 0x3f) | 0x80;
    const h = [...b].map(x => x.toString(16).padStart(2, "0")).join("");
    return `${h.slice(0,8)}-${h.slice(8,12)}-${h.slice(12,16)}-${h.slice(16,20)}-${h.slice(20)}`;
  }

  async function getRecaptchaToken(action = "chat_submit") {
    if (!window.grecaptcha?.enterprise) throw new Error("grecaptcha not loaded yet");
    return window.grecaptcha.enterprise.execute(SITE_KEY, { action });
  }

  async function readStream(res, onEvent) {
    // arena.ai stream protocol (NOT standard SSE):
    //   line = <position><code>:<json>   e.g.  a0:"hello"  or  b0:"world"
    //   position: "a" | "b"  (model participant)
    //   code "0" = text delta (JSON string), code "g" = reasoning,
    //   code "d" = finish, code "3" = error, JSON containing hasArenaError = error
    const reader = res.body.getReader();
    const dec = new TextDecoder();
    let buf = "", text = { a: "", b: "" };
    const handleLine = (line) => {
      if (!line) return;
      const pos = line.charAt(0);            // "a" or "b"
      const rest = line.slice(1);
      if (rest.includes("hasArenaError")) return; // server-side error marker
      const colon = rest.indexOf(":");
      if (colon < 0) return;
      const code = rest.slice(0, colon);
      const raw = rest.slice(colon + 1);
      let val;
      try { val = JSON.parse(raw); } catch { return; }
      onEvent?.(pos + code, val);
      if (code === "0" && typeof val === "string") {
        if (pos === "b") text.b += val; else text.a += val;
      }
    };
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      let i;
      while ((i = buf.indexOf("\n")) >= 0) {
        handleLine(buf.slice(0, i).replace(/\r$/, ""));
        buf = buf.slice(i + 1);
      }
    }
    if (buf) handleLine(buf);
    return text;
  }

  async function runJob(job) {
    log("running job", job.id, JSON.stringify(job.prompt), "mode:", job.mode, "model:", job.modelAId, "session:", job.sessionId);
    const token = await getRecaptchaToken("chat_submit");
    log("recaptcha token acquired, len:", token?.length);

    const isContinue = !!job.sessionId;
    // Server rule: all message IDs must be generated AFTER the evaluation/session ID.
    // So: sessionId first, then userMessageId, then model message IDs.
    let url, body;
    if (isContinue) {
      url = `/nextjs-api/stream/post-to-evaluation/${job.sessionId}`;
      body = {
        id: job.sessionId,
        userMessageId: uuidv7(),
        modelAMessageId: uuidv7(),
        modelBMessageId: uuidv7(),
        recaptchaV3Token: token,
        userMessage: { content: job.prompt, experimental_attachments: [], metadata: {} },
      };
    } else {
      const sessionId = uuidv7();
      url = "/nextjs-api/stream/create-evaluation";
      body = {
        id: sessionId,
        mode: job.mode ?? "battle",
        modality: "chat",
        ...(job.mode === "direct" && job.modelAId ? { modelAId: job.modelAId } : {}),
        userMessageId: uuidv7(),
        modelAMessageId: uuidv7(),
        modelBMessageId: uuidv7(),
        recaptchaV3Token: token,
        userMessage: { content: job.prompt, experimental_attachments: [], metadata: {} },
      };
    }

    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
      credentials: "include",
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      const err = await res.text().catch(() => "");
      throw new Error(`arena api ${res.status}: ${err.slice(0, 200)}`);
    }

    const result = await readStream(res);
    log("done:", result);
    await fetch(`${HUB}/jobs/${job.id}/result`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Auth": SECRET },
      body: JSON.stringify({
        ok: true,
        answerA: result.a,
        answerB: result.b,
        sessionId: body.id,
        mode: body.mode ?? (isContinue ? "continue" : "battle"),
      }),
    });
    log("result posted to hub");
  }

  async function ensureUser() {
    // quick check: if /api/me says user exists and TOU accepted, we're good
    const me = await fetch("/api/me", { credentials: "include" }).then(r => r.json()).catch(() => null);
    if (me?.user?.touConsentTimestamp) return;
    // otherwise create anonymous user + accept TOU (same flow as the site)
    const home = await fetch("/", { credentials: "include" });
    await home.text();
    const puid = document.cookie.match(/provisional_user_id=([0-9a-f-]+)/)?.[1];
    if (!puid) throw new Error("no provisional_user_id");
    const su = await fetch("/nextjs-api/sign-up", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ recaptchaToken: "", provisionalUserId: puid }),
    });
    if (!su.ok) throw new Error("sign-up failed " + su.status);
    await fetch("/api/me/update-tou-consent", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: "{}",
    });
    log("anonymous user ready");
  }

  async function poll() {
    try {
      const r = await fetch(`${HUB}/next-job`, { headers: { "X-Auth": SECRET } });
      const data = await r.json();
      if (data.job) {
        try {
          await ensureUser();
          await runJob(data.job);
        } catch (e) {
          log("job failed:", e.message);
          await fetch(`${HUB}/jobs/${data.job.id}/result`, {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-Auth": SECRET },
            body: JSON.stringify({ ok: false, error: String(e.message).slice(0, 500) }),
          }).catch(() => {});
        }
      }
    } catch (e) {
      log("poll error:", e.message);
    }
    setTimeout(poll, POLL_MS);
  }

  // wait for grecaptcha then start
  const t0 = Date.now();
  (function waitReady() {
    if (window.grecaptcha?.enterprise?.execute) {
      log("started — polling hub every", POLL_MS, "ms");
      poll();
    } else if (Date.now() - t0 < 30000) {
      setTimeout(waitReady, 500);
    } else {
      log("grecaptcha never loaded — retrying in 60s");
      setTimeout(waitReady, 60000);
    }
  })();
})();
