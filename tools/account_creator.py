#!/usr/bin/env python3
# by white wolf : t.me/j49_c | t.me/bshshshkk
import json as _wolf_js
import os as _wolf_os
import re as _wolf_re
import sys as _wolf_sys
import time as _wolf_tim
import secrets as _wolf_sec
import http.cookiejar as _wolf_cjar
import urllib.request as _wolf_req
import urllib.error as _wolf_err
import urllib.parse as _wolf_parse

_wolf_ms = "https://api.mail.tm"
_wolf_tar = "https://arena.ai"
_wolf_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
_wolf_out = _wolf_os.path.join(_wolf_os.path.dirname(_wolf_os.path.abspath(__file__)), "..", "arena_account.json")
_wolf_out = _wolf_os.path.normpath(_wolf_out)
_wolf_tmo = 45
_wolf_rounds = 24
_wolf_mark = 0xA5F0C21B

if hasattr(_wolf_sys.stdout, "reconfigure"):
    _wolf_sys.stdout.reconfigure(encoding="utf-8")
    _wolf_sys.stderr.reconfigure(encoding="utf-8")


def _wolf_churn(_wolf_o):
    _wolf_t = (_wolf_mark ^ (_wolf_o * 31)) % 17
    return _wolf_t < 4


def _wolf_log(*_wolf_rest):
    print(f"[{_wolf_tim.strftime('%H:%M:%S')}]", *_wolf_rest, flush=True)


def _wolf_fetch(_url, _m="GET", _data=None, _headers=None, _jar=None):
    _h = {"User-Agent": _wolf_ua}
    if _jar:
        _h["Cookie"] = _jar
    if _headers:
        _h.update(_headers)
    _r = _wolf_req.Request(_url, method=_m, data=_data, headers=_h)
    try:
        with _wolf_req.urlopen(_r, timeout=_wolf_tmo) as _res:
            return _res.status, _res.read().decode("utf-8", "replace"), (_res.headers.get_all("Set-Cookie") or [])
    except _wolf_err.HTTPError as _e:
        return _e.code, _e.read().decode("utf-8", "replace"), (_e.headers.get_all("Set-Cookie") or [])


def _wolf_mail(_m, _path, _body=None, _tk=None):
    _h = {"Content-Type": "application/json", "Accept": "application/json"}
    if _tk:
        _h["Authorization"] = "Bearer " + _tk
    _data = _wolf_js.dumps(_body).encode("utf-8") if _body is not None else None
    _code, _raw, _ = _wolf_fetch(_wolf_ms + _path, _m, _data, _h)
    try:
        return _code, _wolf_js.loads(_raw or "{}")
    except Exception:
        return _code, {}


def _wolf_hydra(_d):
    if isinstance(_d, list):
        return _d
    return _d.get("hydra:member", [])


def _wolf_gen_password():
    return _wolf_sec.token_urlsafe(18)


def _wolf_jarpack(_setc):
    _j = {}
    for _c in _setc:
        _pair = _c.split(";")[0]
        if "=" not in _pair:
            continue
        _k, _, _v = _pair.partition("=")
        if _k.strip() == "__cf_bm":
            continue
        _j[_k.strip()] = _v.strip()
    return "; ".join(f"{k}={v}" for k, v in _j.items())


def _wolf_warm(_n):
    _wolf_tim.sleep(1 + _n % 3)
    if _wolf_churn(_n):
        _wolf_tim.sleep(0.3)


def _wolf_make_mailbox(_n):
    _code, _doms = _wolf_mail("GET", "/domains")
    _list = _wolf_hydra(_doms)
    if not _list:
        raise RuntimeError("تعذّر استرجاع نطاقات البريد المؤقت المتاحة")
    _dom = _list[0]["domain"]
    _addr = f"albaron{int(_wolf_tim.time()*1000)%999983}@{_dom}"
    _passw = _wolf_gen_password()
    _code, _acc = _wolf_mail("POST", "/accounts", {"address": _addr, "password": _passw})
    if _code not in (200, 201):
        raise RuntimeError("فشل إنشاء صندوق البريد المؤقت: " + str(_acc)[:200])
    _code, _tok = _wolf_mail("POST", "/token", {"address": _addr, "password": _passw})
    if _code != 200 or "token" not in _tok:
        raise RuntimeError("تعذّر الحصول على رمز صندوق البريد")
    return _addr, _passw, _tok["token"]


def _wolf_ask_magic(_addr, _name, _jar):
    _body = _wolf_js.dumps({
        "email": _addr,
        "fullName": _name,
        "shouldLinkHistory": False,
        "recaptchaToken": "",
    }).encode("utf-8")
    _code, _raw, _ = _wolf_fetch(
        _wolf_tar + "/nextjs-api/sign-up/magic-link",
        "POST", _body,
        {"Content-Type": "application/json", "Origin": _wolf_tar, "Referer": _wolf_tar + "/"},
        _jar,
    )
    if '"success":true' not in _raw:
        raise RuntimeError("فشل إرسال رابط التحقق من المنصة: " + _raw[:200])
    return True


def _wolf_hunt_link(_tk, _prev_jar=None):
    for _i in range(_wolf_rounds):
        _wolf_tim.sleep(5)
        _code, _msgs = _wolf_mail("GET", "/messages?page=1", _tk=_tk)
        for _m in _wolf_hydra(_msgs):
            _c2, _full = _wolf_mail("GET", "/messages/" + _m["id"], _tk=_tk)
            _html = _full.get("html") or _full.get("text") or ""
            if isinstance(_html, list):
                _html = " ".join(_html)
            if isinstance(_html, str):
                for _u in _wolf_re.findall(r"https?://[^\s'\"<>]+", _html):
                    _u = _u.replace("&amp;", "&")
                    if "/callback/email" in _u:
                        return _u
        _wolf_log(f"جارٍ انتظار رسالة التحقق... ({(_i + 1) * 5} ثانية)")
    raise RuntimeError("لم تصل رسالة التحقق خلال المدة المحددة")
class _wolf_NoFollow(_wolf_req.HTTPRedirectHandler):
    def redirect_request(self, *_a, **_k):
        return None


def _wolf_visit_magic(_link, _jar_cookies):
    _cj = _wolf_cjar.CookieJar()
    _opener = _wolf_req.build_opener(_wolf_req.HTTPCookieProcessor(_cj), _wolf_NoFollow())
    _opener.addheaders = [("User-Agent", _wolf_ua)]
    _final = _link
    try:
        with _opener.open(
            _wolf_req.Request(_link, headers={"User-Agent": _wolf_ua, "Cookie": _jar_cookies}),
            timeout=60,
        ) as _res:
            _final = _res.url
    except _wolf_err.HTTPError as _e:
        if _e.code in (301, 302, 303, 307, 308):
            _final = _wolf_parse.urljoin(_link, _e.headers.get("Location", ""))
        else:
            raise
    _m = _wolf_re.search(r"token=([^&]+)", _final)
    if not _m:
        raise RuntimeError("رابط التحقق غير صالح أو منتهي الصلاحية")
    _token = _m.group(1)
    _body = _wolf_js.dumps({"password": _wolf_pw, "token": _token}).encode("utf-8")
    try:
        with _opener.open(
            _wolf_req.Request(
                _wolf_tar + "/nextjs-api/auth/set-password",
                method="POST",
                data=_body,
                headers={"Content-Type": "application/json", "Origin": _wolf_tar,
                         "Referer": _wolf_tar + "/auth/set-password"},
            ),
            timeout=60,
        ):
            pass
    except _wolf_err.HTTPError as _e:
        if _e.code in (301, 302, 303, 307, 308):
            _loc = _e.headers.get("Location", "")
            if "error=" in _loc:
                raise RuntimeError("انتهت صلاحية رابط التحقق قبل استخدامه")
        else:
            try:
                _e.read()
            except Exception:
                pass
    return "; ".join(c.name + "=" + c.value for c in _cj)


def _wolf_run(_full_name="Al Baron"):
    _wolf_log("الخطوة 1 من 5: إنشاء بريد إلكتروني مؤقت ومعرّفات آمنة...")
    _addr, _passw, _tk = _wolf_make_mailbox(0)
    global _wolf_pw
    _wolf_pw = _passw
    _wolf_log("    البريد المؤقت:", _addr)
    _wolf_warm(1)
    _wolf_log("الخطوة 2 من 5: طلب رابط التسجيل من المنصة...")
    _code, _, _setc = _wolf_fetch(_wolf_tar + "/", _headers={"Accept": "text/html"})
    _jar = _wolf_jarpack(_setc)
    _wolf_tim.sleep(2)
    _wolf_ask_magic(_addr, _full_name, _jar)
    _wolf_log("    أُرسل رابط التحقق إلى البريد المؤقت")
    _wolf_log("الخطوة 3 من 5: انتظار رسالة التحقق في صندوق البريد...")
    _link = _wolf_hunt_link(_tk, _jar)
    _wolf_log("    تم العثور على رابط التحقق")
    _wolf_log("الخطوة 4 من 5: تفعيل الحساب وتعيين كلمة المرور...")
    _cookies = _wolf_visit_magic(_link, _jar)
    _user = _wolf_verify(_cookies)
    _wolf_log("الخطوة 5 من 5: حفظ بيانات الحساب...")
    _data = {"email": _addr, "password": _passw, "cookies": _cookies, "user": _user}
    with open(_wolf_out, "w", encoding="utf-8") as _f:
        _wolf_js.dump(_data, _f, ensure_ascii=False, indent=2)
    if _user:
        _wolf_log("تم إنشاء الحساب وتسجيل الدخول بنجاح ✔")
    else:
        _wolf_log("تم إنشاء الحساب؛ أعد تفعيل الجلسة من الوكيل مرة واحدة لإكمال الربط")
    _wolf_log("حُفظ الحساب في:", _wolf_out)
    return _data


def _wolf_verify(_cookies):
    _code, _raw, _ = _wolf_fetch(_wolf_tar + "/api/me", _jar=_cookies, _headers={"Referer": _wolf_tar + "/"})
    if _code == 200:
        try:
            return _wolf_js.loads(_raw).get("user")
        except Exception:
            return None
    return None


def _wolf_cleanup(_acc):
    try:
        _code, _me = _wolf_mail("GET", "/me", _tk=_acc.get("mailToken"))
        if _me.get("id"):
            _wolf_mail("DELETE", "/me", _tk=_acc.get("mailToken"))
    except Exception:
        pass


def _wolf_help():
    print("أداة إنشاء الحسابات على منصة arena.ai — إنشاء كامل تلقائي")
    print("  python account_creator.py [--name <الاسم الكامل>]")
    print("الخطوات: بريد مؤقت من mail.tm ← طلب ماجك لينك ← انتظار رسالة التحقق ←")
    print("         فتح الرابط وتعيين كلمة مرور ← حفظ الحساب في arena_account.json")
    print("كلمة المرور تُولَّد عشوائيًا ولا تُحفظ في الكود")


def _wolf_main(_args=None):
    _args = list(_args) if _args is not None else _wolf_sys.argv[1:]
    if _args and _args[0] in ("help", "-h", "--help"):
        _wolf_help()
        return 0
    _name = "Al Baron"
    if _args and _args[0] in ("-n", "--name") and len(_args) > 1:
        _name = _args[1]
    try:
        _wolf_run(_name)
    except RuntimeError as _e:
        _wolf_log("خطأ:", str(_e))
        return 1
    except Exception as _e:
        _wolf_log("خطأ غير متوقع:", str(_e)[:300])
        return 1
    return 0


if __name__ == "__main__":
    _wolf_pw = None
    _wolf_sys.exit(_wolf_main())