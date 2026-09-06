#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Arena Browser Agent — Python replacement for the Tampermonkey userscript.
Opens a REAL (visible) Chromium window via Playwright with stealth patches,
loads arena.ai, then polls the Cloudflare Worker hub for jobs and executes
them inside the arena.ai page context (same-origin => valid reCAPTCHA v3
tokens, same IP for token + request, real browser fingerprint).

Run:  python browser_agent.py
Keep this window open — it IS the automation engine.
"""

import json
import os
import random
import sys
import time
import urllib.request

from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

HUB = os.environ.get("ARENA_HUB_URL", "")  # legacy, unused
SECRET = os.environ.get("ARENA_HUB_SECRET", "")  # legacy, unused
POLL_MIN, POLL_MAX = 2.0, 5.0   # human-like jitter
ACCOUNT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "arena_account.json")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def log(*a):
    print(f"[{time.strftime('%H:%M:%S')}]", *a, flush=True)

def hub(path, payload=None, method="GET"):
    req = urllib.request.Request(
        HUB + path, method=method,
        headers={"Content-Type": "application/json", "X-Auth": SECRET,
                 "User-Agent": "Mozilla/5.0"},
        data=json.dumps(payload).encode() if payload else None)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode() or "{}")

# Executed INSIDE the arena.ai page (same origin). Everything in one shot:
# TOU consent -> reCAPTCHA token -> create/post evaluation -> parse stream.
PAGE_JS = r"""
async ([job]) => {
  const uuidv7 = () => {
    let ts = Date.now(); const b = new Uint8Array(16);
    for (let i = 5; i >= 0; i--) { b[i] = ts % 256; ts = Math.floor(ts / 256); }
    crypto.getRandomValues(b.subarray(6));
    b[6] = (b[6] & 0x0f) | 0x70; b[8] = (b[8] & 0x3f) | 0x80;
    const h = [...b].map(x => x.toString(16).padStart(2, "0")).join("");
    return `${h.slice(0,8)}-${h.slice(8,12)}-${h.slice(12,16)}-${h.slice(16,20)}-${h.slice(20)}`;
  };
  const SITE_KEY = "6LeTGMcsAAAAALuIlkVwIxaAuZA8VledA6d3Nnb0";
  const token = await window.grecaptcha.enterprise.execute(SITE_KEY, {action: "chat_submit"});

  const isContinue = !!job.sessionId;
  let url, body;
  if (isContinue) {
    url = `/nextjs-api/stream/post-to-evaluation/${job.sessionId}`;
    body = { id: job.sessionId, userMessageId: uuidv7(), modelAMessageId: uuidv7(),
             modelBMessageId: uuidv7(), recaptchaV3Token: token,
             userMessage: { content: job.prompt, experimental_attachments: [], metadata: {} } };
  } else {
    const sid = uuidv7();
    url = "/nextjs-api/stream/create-evaluation";
    body = { id: sid, mode: job.mode || "battle", modality: "chat",
             ...(job.mode === "direct" && job.modelAId ? { modelAId: job.modelAId } : {}),
             userMessageId: uuidv7(), modelAMessageId: uuidv7(), modelBMessageId: uuidv7(),
             recaptchaV3Token: token,
             userMessage: { content: job.prompt, experimental_attachments: [], metadata: {} } };
  }
  const res = await fetch(url, { method: "POST", credentials: "include",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify(body) });
  if (!res.ok) return { ok: false, error: `arena ${res.status}: ${(await res.text()).slice(0,150)}` };

  const reader = res.body.getReader(); const dec = new TextDecoder();
  let buf = "", text = { a: "", b: "" };
  const line = (l) => {
    if (!l) return;
    const pos = l.charAt(0), rest = l.slice(1);
    if (rest.includes("hasArenaError")) return;
    const c = rest.indexOf(":"); if (c < 0) return;
    const code = rest.slice(0, c);
    let v; try { v = JSON.parse(rest.slice(c + 1)); } catch { return; }
    if (code === "0" && typeof v === "string") { if (pos === "b") text.b += v; else text.a += v; }
  };
  while (true) {
    const { done, value } = await reader.read(); if (done) break;
    buf += dec.decode(value, { stream: true });
    let i; while ((i = buf.indexOf("\n")) >= 0) { line(buf.slice(0, i).replace(/\r$/, "")); buf = buf.slice(i + 1); }
  }
  if (buf) line(buf);
  return { ok: true, answerA: text.a, answerB: text.b, sessionId: body.id };
}
"""

ENSURE_JS = r"""
async ([account]) => {
  const me = await fetch("/api/me", { credentials: "include" }).then(r => r.json()).catch(() => null);
  if (me?.user?.touConsentTimestamp) return "ready";
  // if we have a saved email account, log in from THIS browser (fresh session)
  if (account && account.email && account.password) {
    const si = await fetch("/nextjs-api/sign-in/email", { method: "POST", credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: account.email, password: account.password, shouldLinkHistory: false }) });
    if (si.ok) {
      await fetch("/api/me/update-tou-consent", { method: "POST", credentials: "include",
        headers: { "Content-Type": "application/json" }, body: "{}" }).catch(() => {});
      const me2 = await fetch("/api/me", { credentials: "include" }).then(r => r.json()).catch(() => null);
      return "logged-in: " + (me2?.user?.email ?? "unknown");
    }
    return "sign-in failed: " + si.status;
  }
  await fetch("/", { credentials: "include" }).then(r => r.text()).catch(() => {});
  const puid = document.cookie.match(/provisional_user_id=([0-9a-f-]+)/)?.[1];
  if (puid) {
    await fetch("/nextjs-api/sign-up", { method: "POST", credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ recaptchaToken: "", provisionalUserId: puid }) });
    await fetch("/api/me/update-tou-consent", { method: "POST", credentials: "include",
      headers: { "Content-Type": "application/json" }, body: "{}" });
  }
  return "ensured-anonymous";
}
"""

def human_pause():
    time.sleep(random.uniform(POLL_MIN, POLL_MAX))

def main():
    log("starting Chrome (real browser + persistent profile = higher v3 score)...")
    stealth = Stealth(navigator_webdriver=True)
    profile = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".chrome_profile")
    with stealth.use_sync(sync_playwright()) as p:
        ctx = p.chromium.launch_persistent_context(
            profile,
            channel="chrome",                    # real installed Chrome, not Chromium
            headless=False,                      # never headless for v3
            viewport={"width": 1280, "height": 800},
            locale="en-US",
            args=["--disable-blink-features=AutomationControlled", "--start-minimized"],
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        # inject saved account cookies (if any) BEFORE navigation — logged-in
        # sessions get higher reCAPTCHA scores + direct mode access
        if os.path.exists(ACCOUNT_FILE):
            try:
                acc = json.load(open(ACCOUNT_FILE, encoding="utf-8"))
                cookies = []
                for pair in acc.get("cookies", "").split("; "):
                    if "=" in pair:
                        k, _, v = pair.partition("=")
                        k = k.strip()
                        if k in ("__cf_bm", "provisional_user_id", "user_country_code"):
                            continue  # stale session-bound cookies — skip
                        cookies.append({"name": k, "value": v, "domain": "arena.ai", "path": "/"})
                if cookies:
                    ctx.add_cookies(cookies)
                    log(f"injected {len(cookies)} account cookies ({acc.get('email')})")
            except Exception as e:
                log("cookie injection warning:", str(e)[:120])
        page.goto("https://arena.ai/", wait_until="domcontentloaded")
        page.wait_for_function("() => !!window.grecaptcha?.enterprise?.execute", timeout=60000)
        log("arena.ai loaded — warming up like a human (25s)...")
        for _ in range(10):  # build behavioral score before first token
            page.mouse.move(random.randint(100, 1100), random.randint(80, 700))
            page.mouse.wheel(0, random.choice([120, -80, 200]))
            time.sleep(random.uniform(1.0, 2.5))
        log("warm-up done")
        page.goto("https://arena.ai/", wait_until="domcontentloaded") if page.url == "about:blank" else None
        page.wait_for_function("() => !!window.grecaptcha?.enterprise?.execute", timeout=60000)
        log("grecaptcha ready")
        _acc = json.load(open(ACCOUNT_FILE, encoding="utf-8")) if os.path.exists(ACCOUNT_FILE) else None
        state = page.evaluate(ENSURE_JS, [_acc])
        log("user state:", state)

        # API server thread (stdlib http.server) — jobs are queued to the MAIN
        # thread because Playwright sync objects are single-threaded (greenlet).
        import threading, queue as _q
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        job_q = _q.Queue()
        chat_jobs = {}  # id -> {status, result} for async /chat API

        class Handler(BaseHTTPRequestHandler):
            def _cors(self):
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")
            def _json(self, obj, status=200):
                body = json.dumps(obj, ensure_ascii=False).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self._cors()
                self.end_headers()
                self.wfile.write(body)
            def do_OPTIONS(self):
                self.send_response(204); self._cors(); self.end_headers()
            def do_GET(self):
                if self.path == "/health":
                    self._json({"ok": True, "agent": "browser", "time": int(time.time())})
                elif self.path.startswith("/chat/"):
                    jid = self.path.split("/chat/")[1]
                    job = chat_jobs.get(jid)
                    self._json(job or {"error": "unknown job"}, 200 if job else 404)
                elif self.path == "/me":
                    acc = json.load(open(ACCOUNT_FILE, encoding="utf-8")) if os.path.exists(ACCOUNT_FILE) else None
                    self._json(acc or {"error": "no account"})
                elif self.path == "/account/create":
                    import subprocess, sys as _s
                    creator = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools", "account_creator.py")
                    r = subprocess.run([_s.executable, creator],
                                       capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__)))
                    acc = json.load(open(ACCOUNT_FILE, encoding="utf-8")) if os.path.exists(ACCOUNT_FILE) else None
                    self._json({"ok": r.returncode == 0, "log": (r.stdout + r.stderr)[-800:], "account": acc})
                else:
                    self._json({"error": "not found"}, 404)
            def do_POST(self):
                if self.path == "/chat":
                    # async mode: return jobId instantly (avoids tunnel timeouts),
                    # caller polls GET /chat/{id}
                    ln = int(self.headers.get("Content-Length", 0))
                    req = json.loads(self.rfile.read(ln) or "{}")
                    prompt = str(req.get("prompt", "")).strip()
                    if not prompt: return self._json({"error": "prompt required"}, 400)
                    jid = os.urandom(8).hex()
                    job = {"prompt": prompt, "mode": req.get("mode", "battle"),
                           "modelAId": req.get("modelAId"), "sessionId": req.get("sessionId")}
                    chat_jobs[jid] = {"status": "pending"}
                    job_q.put((job, jid, None))
                    return self._json({"id": jid, "status": "pending"}, 202)
                # legacy sync mode
                if self.path != "/chat/sync":
                    return self._json({"error": "not found"}, 404)
                try:
                    ln = int(self.headers.get("Content-Length", 0))
                    req = json.loads(self.rfile.read(ln) or "{}")
                    prompt = str(req.get("prompt", "")).strip()
                    if not prompt: return self._json({"error": "prompt required"}, 400)
                    job = {"prompt": prompt, "mode": req.get("mode", "battle"),
                           "modelAId": req.get("modelAId"), "sessionId": req.get("sessionId")}
                    ev = threading.Event(); box = {}
                    job_q.put((job, None, (box, ev)))
                    ev.wait(timeout=240)
                    if "result" not in box: return self._json({"ok": False, "error": "timeout"}, 504)
                    res = box["result"]
                    self._json(res, 200 if res.get("ok") else 502)
                except Exception as e:
                    self._json({"ok": False, "error": str(e)[:300]}, 500)
            def log_message(self, *a): pass

        srv = ThreadingHTTPServer(("0.0.0.0", 8765), Handler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        log("API server on http://0.0.0.0:8765  (GET /health | POST /chat)")

        # Cloudflare quick tunnel -> public HTTPS URL reachable from anywhere
        import subprocess as _sp
        cf_exe = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cloudflared.exe")
        if os.path.exists(cf_exe):
            try:
                cf_log = os.path.join(os.path.dirname(cf_exe), "cf_tunnel.log")
                cf = _sp.Popen([cf_exe, "tunnel", "--url", "http://localhost:8765",
                                "--no-autoupdate", "--logfile", cf_log],
                               stdout=_sp.DEVNULL, stderr=_sp.DEVNULL)
                def _cf_reader():
                    url = None
                    for _ in range(120):
                        time.sleep(1)
                        try:
                            txt = open(cf_log, encoding="utf-8", errors="replace").read()
                        except Exception:
                            continue
                        m = re.search(r"https://[a-z0-9\-]+\.trycloudflare\.com", txt)
                        if m:
                            url = m.group(0)
                            log("PUBLIC URL:", url)
                            with open(os.path.join(os.path.dirname(cf_exe), "public_url.txt"), "w") as f:
                                f.write(url)
                            break
                threading.Thread(target=_cf_reader, daemon=True).start()
                log("cloudflared tunnel starting...")
            except Exception as e:
                log("tunnel failed:", str(e)[:150])

        # keep the page "alive" like a human + drain queued chat jobs on THIS thread
        while True:
            try:
                try:
                    item = job_q.get(timeout=5)
                    if len(item) == 3:
                        job, jid, sync = item
                    else:
                        job, sync = item[0], None
                        jid = None
                    log("chat job:", repr(job["prompt"][:50]))
                    result = {"ok": False, "error": "untried"}
                    for attempt in range(3):
                        try:
                            result = page.evaluate(PAGE_JS, [job])
                        except Exception as e:
                            result = {"ok": False, "error": str(e)[:300]}
                        if result.get("ok"):
                            break
                        err = result.get("error", "")
                        log(f"attempt {attempt+1} failed: {err[:120]}")
                        if "recaptcha" in err.lower():
                            for _ in range(6):
                                page.mouse.move(random.randint(100, 1100), random.randint(80, 700))
                                page.mouse.wheel(0, random.choice([150, -100, 250]))
                                time.sleep(random.uniform(1.5, 3.0))
                        else:
                            break
                    if jid is not None:
                        chat_jobs[jid].update(status="done", result=result)
                    else:
                        box, ev = sync
                        box["result"] = result
                        ev.set()
                    log("done:", "OK" if result.get("ok") else result.get("error"))
                    continue
                except _q.Empty:
                    pass
                if random.random() < 0.25:
                    page.mouse.move(random.randint(100, 1100), random.randint(100, 700))
            except Exception as e:
                log("loop error:", str(e)[:200])
                time.sleep(5)

if __name__ == "__main__":
    main()
