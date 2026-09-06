#!/usr/bin/env python3
# by white wolf : t.me/j49_c | t.me/bshshshkk
import json as _wolf_js
import os as _wolf_os
import re as _wolf_re
import sys as _wolf_sys
import time as _wolf_tim
import urllib.request as _wolf_req
import urllib.error as _wolf_err

_wolf_base = "https://arena.ai"
_wolf_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
_wolf_site_key = "6LeTGMcsAAAAALuIlkVwIxaAuZA8VledA6d3Nnb0"
_wolf_tmo = (8 * 5) + 10
_wolf_cf = "__cf_bm"
_wolf_mark = 0x7F4A290C

if hasattr(_wolf_sys.stdout, "reconfigure"):
    _wolf_sys.stdout.reconfigure(encoding="utf-8")
    _wolf_sys.stderr.reconfigure(encoding="utf-8")


def _wolf_hush(_wolf_p):
    _wolf_rot = (_wolf_mark * 3 + _wolf_p) % 7
    return _wolf_rot < 3


def _wolf_call(_path, _m="GET", _body=None, _jar=None, _accept="application/json"):
    _h = {
        "User-Agent": _wolf_ua,
        "Accept": _accept,
        "Origin": _wolf_base,
        "Referer": _wolf_base + "/",
        "Content-Type": "application/json" if _body is not None else "text/plain",
    }
    if _jar:
        _h["Cookie"] = _jar
    _r = _wolf_req.Request(
        _wolf_base + _path,
        method=_m,
        headers=_h,
        data=_wolf_js.dumps(_body).encode("utf-8") if _body is not None else None,
    )
    try:
        with _wolf_req.urlopen(_r, timeout=_wolf_tmo) as _res:
            _raw = _res.read()
            _text = _raw.decode("utf-8", "replace")
            _setc = _res.headers.get_all("Set-Cookie") or []
            _code = _res.status
    except _wolf_err.HTTPError as _e:
        _raw = _e.read()
        _text = _raw.decode("utf-8", "replace")
        _setc = _e.headers.get_all("Set-Cookie") or []
        _code = _e.code
    except Exception as _e:
        raise RuntimeError("تعذّر الاتصال بمنصة arena.ai: " + str(_e)[:180])
    _parsed = None
    try:
        _parsed = _wolf_js.loads(_text) if _text else None
    except Exception:
        _parsed = None
    return _code, _parsed if _parsed is not None else _text, _setc


def _wolf_jar(_setc):
    _m = {}
    for _c in _setc:
        _pair = _c.split(";")[0]
        if "=" not in _pair:
            continue
        _k, _, _v = _pair.partition("=")
        if _wolf_cf in _k:
            continue
        _m[_k.strip()] = _v.strip()
    return "; ".join(f"{k}={v}" for k, v in _m.items())


def _wolf_uuid():
    _ts = int(_wolf_tim.time() * 1000)
    _b = bytearray(16)
    for _i in range(5, -1, -1):
        _b[_i] = _ts & 0xFF
        _ts >>= 8
    _b[6:10] = _wolf_os.urandom(4)
    _b[10:16] = _wolf_os.urandom(6)
    _b[6] = (_b[6] & 0x0F) | 0x70
    _b[8] = (_b[8] & 0x3F) | 0x80
    _h = _b.hex()
    if _wolf_hush(2):
        _h = _h.upper() if False else _h
    return f"{_h[0:8]}-{_h[8:12]}-{_h[12:16]}-{_h[16:20]}-{_h[20:32]}"


def _wolf_parse_stream(_text):
    _parts = {"a": "", "b": ""}
    for _line in _text.splitlines():
        _line = _line.strip()
        if not _line:
            continue
        _pos = _line[0]
        if _pos not in ("a", "b"):
            continue
        _rest = _line[1:]
        if "hasArenaError" in _rest:
            continue
        _ci = _rest.find(":")
        if _ci < 0:
            continue
        _code = _rest[:_ci]
        _val = _rest[_ci + 1:]
        try:
            _v = _wolf_js.loads(_val)
        except Exception:
            continue
        if _code == "0" and isinstance(_v, str):
            _parts[_pos] += _v
    return _parts
def _wolf_ensure_user(_jar_cookies=None):
    _jar = _jar_cookies
    _code, _me, _setc = _wolf_call("/api/me", "GET", _jar=_jar)
    if _code == 200 and isinstance(_me, dict) and _me.get("user"):
        _j = _wolf_jar(_setc) or _jar
        return _j, _me, False
    _code2, _home, _setc2 = _wolf_call("/", "GET", _jar=_jar)
    _jar = _wolf_jar(_setc + _setc2) or _jar
    _puid = ""
    if _jar:
        for _seg in _jar.split("; "):
            if _seg.startswith("provisional_user_id="):
                _puid = _seg.split("=", 1)[1]
    if not _puid and isinstance(_home, str):
        _m = _wolf_re.search(r"provisional_user_id=([0-9a-f-]+)", _home or "")
        if _m:
            _puid = _m.group(1)
    if not _puid:
        _m2 = _wolf_re.search(r"provisional_user_id=([0-9a-f-]+)", "; ".join(_setc + _setc2))
        if _m2:
            _puid = _m2.group(1)
    if not _puid:
        raise RuntimeError("تعذّر الحصول على معرّف المستخدم المؤقت من المنصة")
    _code3, _su, _setc3 = _wolf_call(
        "/nextjs-api/sign-up", "POST",
        {"recaptchaToken": "", "provisionalUserId": _puid},
        _jar=_jar,
    )
    if _code3 not in (200, 201):
        raise RuntimeError(f"فشل تسجيل المستخدم المؤقت ({_code3}): {str(_su)[:150]}")
    _jar = _wolf_jar(_setc + _setc2 + _setc3) or _jar
    _code4, _tou, _setc4 = _wolf_call("/api/me/update-tou-consent", "POST", {}, _jar=_jar)
    _jar = _wolf_jar(_setc4) or _jar
    if _code4 not in (200, 201):
        raise RuntimeError(f"تعذّر قبول شروط الاستخدام ({_code4})")
    _code5, _me5, _setc5 = _wolf_call("/api/me", "GET", _jar=_jar)
    _jar = _wolf_jar(_setc5) or _jar
    _user = _me5.get("user") if isinstance(_me5, dict) else None
    return _jar, {"user": _user, "fresh": True}, True


def _wolf_solver_token():
    _here = _wolf_os.path.dirname(_wolf_os.path.abspath(__file__))
    _mod_path = _here + "/captcha_api.py"
    if not _wolf_os.path.exists(_mod_path):
        raise RuntimeError("أداة الكابتشا غير موجودة — captcha_api.py مطلوبة في مجلد tools")
    import importlib.util
    _spec = importlib.util.spec_from_file_location("captcha_api", _mod_path)
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    return _mod._wolf_solve("chat_submit")


def _wolf_chat(_jar, _prompt, _mode="battle", _model_a=None, _sid=None):
    _token = _wolf_solver_token()
    _body = {
        "id": _wolf_uuid(),
        "mode": _mode,
        "modality": "chat",
        "userMessageId": _wolf_uuid(),
        "modelAMessageId": _wolf_uuid(),
        "modelBMessageId": _wolf_uuid(),
        "recaptchaV3Token": _token,
        "userMessage": {"content": _prompt, "experimental_attachments": [], "metadata": {}},
    }
    if _model_a and _mode == "direct":
        _body["modelAId"] = _model_a
    if _mode == "side-by-side" and _model_a:
        _body["modelAId"] = _model_a
        _body["modelBId"] = _model_a
    if _sid:
        _body["id"] = _sid
    _path = f"/nextjs-api/stream/post-to-evaluation/{_sid}" if _sid else "/nextjs-api/stream/create-evaluation"
    _code, _raw, _ = _wolf_call(_path, "POST", _body, _jar=_jar, _accept="text/event-stream")
    _text = _raw if isinstance(_raw, str) else _wolf_js.dumps(_raw)
    if _code != 200:
        raise RuntimeError(f"رفضت المنصة الطلب ({_code}): {_text[:200]}")
    return _wolf_parse_stream(_text), _body["id"]


def _wolf_sesh_file():
    return _wolf_os.path.join(_wolf_os.path.dirname(_wolf_os.path.abspath(__file__)), ".arena_api_cookies.json")


def _wolf_load_sesh():
    if _wolf_os.path.exists(_wolf_sesh_file()):
        try:
            with open(_wolf_sesh_file(), encoding="utf-8") as _f:
                return _wolf_js.load(_f)
        except Exception:
            pass
    return {}


def _wolf_save_sesh(_d):
    with open(_wolf_sesh_file(), "w", encoding="utf-8") as _f:
        _wolf_js.dump(_d, _f, ensure_ascii=False, indent=2)


class _wolf_NoRedirect(_wolf_req.HTTPRedirectHandler):
    def redirect_request(self, *_a, **_k):
        return None
def _wolf_whoami(_jar=None):
    _jar = _jar or _wolf_load_sesh().get("cookies")
    _code, _me, _setc = _wolf_call("/api/me", "GET", _jar=_jar)
    if _code != 200:
        raise RuntimeError(f"تعذّر جلب بيانات المستخدم ({_code})")
    _user = _me.get("user") if isinstance(_me, dict) else None
    _jar2 = _wolf_jar(_setc) or _jar
    _wolf_save_sesh({"cookies": _jar2, "user": _user})
    return _user


def _wolf_classify(_jar, _prompt):
    _code, _d, _ = _wolf_call("/nextjs-api/auto-modality", "POST", {"user_prompt": _prompt, "has_image": False}, _jar=_jar)
    if _code != 200:
        raise RuntimeError(f"فشل تصنيف السؤال ({_code})")
    return _d


def _wolf_history(_jar=None):
    _jar = _jar or _wolf_load_sesh().get("cookies")
    _code, _d, _ = _wolf_call("/api/history/unified", "GET", _jar=_jar)
    if _code != 200:
        raise RuntimeError(f"فشل جلب السجل ({_code})")
    return _d


def _wolf_show_stream(_parts, _sid):
    _a = _parts.get("a", "")
    _b = _parts.get("b", "")
    if _a:
        print("\n=== النموذج أ ===\n" + _a.strip())
    if _b:
        print("\n=== النموذج ب ===\n" + _b.strip())
    if not _a and not _b:
        print("تعذّر استخراج نص من البث")
    print(f"\n[الجلسة] https://arena.ai/c/{_sid}", file=_wolf_sys.stderr)


def _wolf_help():
    print("أداة الواجهة الخام لمنصة arena.ai — محادثة وجلسات مباشرة")
    print("  session                      إنشاء جلسة مؤقتة والقبول بشروط الاستخدام")
    print("  whoami                       عرض بيانات المستخدم الحالي")
    print("  classify <النص>              تصنيف نوع السؤال تلقائيًا")
    print("  history                      عرض سجل المحادثات")
    print("  chat <النص> [--mode battle|direct] [--model <المعرف>] [--session <المعرف>]")
    print("ملاحظة: محادثة chat تتطلب مفتاح حلّ كابتشا عبر المتغيرات البيئية المتاحة")
    print("         المعرّفات المدعومة: sonnet5 / sonnet5-search")


def _wolf_main(_args=None):
    _args = list(_args) if _args is not None else _wolf_sys.argv[1:]
    if not _args or _args[0] in ("help", "-h", "--help"):
        _wolf_help()
        return 0
    _cmd = _args[0]
    try:
        match _cmd:
            case "session":
                _jar, _me, _fresh = _wolf_ensure_user()
                _wolf_save_sesh({"cookies": _jar, "user": _me.get("user")})
                print("تم إنشاء جلسة مؤقتة بنجاح ✅")
                print(_wolf_js.dumps(_me.get("user") or {}, ensure_ascii=False, indent=2))
            case "whoami":
                _u = _wolf_whoami()
                print(_wolf_js.dumps(_u or {}, ensure_ascii=False, indent=2))
            case "classify":
                _p = " ".join(_args[1:]).strip()
                if not _p:
                    print("الاستخدام: classify <نص السؤال>")
                    return 1
                _jar, _me, _ = _wolf_ensure_user()
                print(_wolf_js.dumps(_wolf_classify(_jar, _p), ensure_ascii=False, indent=2))
            case "history":
                _jar, _me, _ = _wolf_ensure_user()
                print(_wolf_js.dumps(_wolf_history(_jar), ensure_ascii=False, indent=2))
            case "chat":
                _rest = _args[1:]
                _mode = "battle"
                _model = None
                _sid = None
                _p = []
                _i = 0
                while _i < len(_rest):
                    _a = _rest[_i]
                    if _a == "--mode" and _i + 1 < len(_rest):
                        _i += 1
                        _mode = _rest[_i]
                    elif _a == "--model" and _i + 1 < len(_rest):
                        _i += 1
                        _model = _rest[_i]
                    elif _a == "--session" and _i + 1 < len(_rest):
                        _i += 1
                        _sid = _rest[_i]
                    else:
                        _p.append(_a)
                    _i += 1
                _prompt = " ".join(_p).strip()
                if not _prompt:
                    print("الاستخدام: chat \"نص الرسالة\" [--mode battle|direct] [--model sonnet5] [--session <المعرف>]")
                    return 1
                _jar, _me, _fresh = _wolf_ensure_user()
                _parts, _sid = _wolf_chat(_jar, _prompt, _mode, _model, _sid)
                _wolf_show_stream(_parts, _sid)
            case _:
                print(f"أمر غير معروف: {_cmd} — استخدم 'help' لعرض الأوامر المتاحة")
                return 1
    except RuntimeError as _e:
        print("خطأ:", str(_e), file=_wolf_sys.stderr)
        return 1
    except Exception as _e:
        print("خطأ غير متوقع:", str(_e)[:300], file=_wolf_sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    _wolf_sys.exit(_wolf_main())