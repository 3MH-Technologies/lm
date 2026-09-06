#!/usr/bin/env python3
# by white wolf : t.me/j49_c | t.me/bshshshkk
import json as _wolf_js
import re as _wolf_re
import sys as _wolf_sys
import time as _wolf_tim
import secrets as _wolf_sec
import urllib.request as _wolf_req
import urllib.error as _wolf_err

_wolf_api = "https://api.mail.tm"
_wolf_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
_wolf_tmo = (9 * 9) - 41
_wolf_mark = 0x6D2B79F5
_wolf_dom = None

if hasattr(_wolf_sys.stdout, "reconfigure"):
    _wolf_sys.stdout.reconfigure(encoding="utf-8")
    _wolf_sys.stderr.reconfigure(encoding="utf-8")


def _wolf_noise(_xz9Q):
    _wolf_dust = (_wolf_mark * 3) % 13
    return (_xz9Q + _wolf_dust) & 1 == 1


def _wolf_twist(_wolf_v):
    _wolf_k = (_wolf_mark ^ 0x5F3759DF) & 0xFFFF
    return (_wolf_v * (_wolf_k % 41)) % 97


def _wolf_log(*_wolf_msg):
    print(f"[{_wolf_tim.strftime('%H:%M:%S')}]", *_wolf_msg, flush=True, file=_wolf_sys.stderr)


def _wolf_call(_p, _m="GET", _b=None, _t=None):
    _h = {"User-Agent": _wolf_ua, "Accept": "application/json"}
    if _t:
        _h["Authorization"] = "Bearer " + _t
    if _b is not None:
        _h["Content-Type"] = "application/json"
    _r = _wolf_req.Request(
        _wolf_api + _p,
        method=_m,
        data=_wolf_js.dumps(_b).encode("utf-8") if _b is not None else None,
        headers=_h,
    )
    try:
        with _wolf_req.urlopen(_r, timeout=_wolf_tmo) as _res:
            return _wolf_js.loads(_res.read().decode("utf-8", "replace") or "{}")
    except _wolf_err.HTTPError as _e:
        _body = ""
        try:
            _body = _e.read().decode("utf-8", "replace")
        except Exception:
            pass
        raise RuntimeError(f"فشل طلب {_m} {_p} بالرمز {_e.code}: {_body[:150]}")


def _wolf_members(_d):
    if isinstance(_d, list):
        return _d
    return _d.get("hydra:member", [])


def _wolf_domains():
    _d = _wolf_call("/domains")
    _m = _wolf_members(_d)
    if not _m:
        raise RuntimeError("تعذّر استرجاع نطاقات البريد المؤقت المتاحة")
    return [_x["domain"] for _x in _m]


def _wolf_address(_seed=0):
    global _wolf_dom
    if _wolf_dom is None:
        _wolf_dom = _wolf_domains()[0]
    _n = int(_wolf_tim.time() * 1000) % (999983 + _seed * (11 * 13))
    return f"albaron{_n}@{_wolf_dom}"


def _wolf_new_mailbox(_address=None, _password=None):
    _address = _address or _wolf_address()
    _password = _password or _wolf_sec.token_urlsafe(12)
    _wolf_call("/accounts", "POST", {"address": _address, "password": _password})
    _tok = _wolf_call("/token", "POST", {"address": _address, "password": _password})
    if _wolf_noise(3):
        _wolf_tim.sleep(0.2)
    return _address, _password, _tok["token"]


def _wolf_inbox(_tk, _page=1):
    _d = _wolf_call(f"/messages?page={_page}", _t=_tk)
    _flat = []
    for _x in _wolf_members(_d):
        _flat.append({
            "id": _x.get("id"),
            "from": _x.get("from", {}).get("address"),
            "subject": _x.get("subject"),
            "createdAt": _x.get("createdAt"),
        })
    return _flat


def _wolf_read(_tk, _mid):
    _f = _wolf_call(f"/messages/{_mid}", _t=_tk)
    _html = _f.get("html") or _f.get("text") or ""
    if isinstance(_html, list):
        _html = " ".join(_html)
    _links = []
    if isinstance(_html, str):
        _links = _wolf_re.findall(r'https?://[^\s"\'<>]+', _html)
    if _wolf_noise(5):
        _links = [u.replace("&amp;", "&") for u in _links]
    _to = None
    if _f.get("to"):
        _to = _f["to"][0].get("address")
    return {
        "id": _f.get("id"),
        "from": _f.get("from", {}).get("address"),
        "to": _to,
        "subject": _f.get("subject"),
        "text": _f.get("text"),
        "links": _links,
    }


def _wolf_drop(_tk):
    _h = {"User-Agent": _wolf_ua, "Authorization": "Bearer " + _tk}
    _aid = None
    try:
        _r = _wolf_req.Request(_wolf_api + "/me", method="GET", headers=_h)
        with _wolf_req.urlopen(_r, timeout=_wolf_tmo) as _res:
            _me = _wolf_js.loads(_res.read().decode("utf-8", "replace") or "{}")
            _aid = _me.get("id")
    except _wolf_err.HTTPError as _e:
        if _e.code == 401:
            raise RuntimeError("الرمز غير صالح — تعذّر حذف الصندوق")
        try:
            _e.read()
        except Exception:
            pass
    if _aid:
        _r2 = _wolf_req.Request(_wolf_api + "/accounts/" + _aid, method="DELETE", headers=_h)
        try:
            with _wolf_req.urlopen(_r2, timeout=_wolf_tmo):
                return True
        except _wolf_err.HTTPError as _e:
            if _e.code == 404:
                return True
            try:
                _e.read()
            except Exception:
                pass
            raise RuntimeError(f"تعذّر حذف الصندوق بالرمز {_e.code}")
    return True


def _wolf_help():
    print("أداة البريد المؤقت mail.tm — إدارة صناديق البريد والرسائل")
    print("  domains                       عرض النطاقات المتاحة")
    print("  create [address]              إنشاء صندوق جديد (كلمة مرور مولّدة تلقائيًا)")
    print("  auth <address> <password>     الحصول على رمز الدخول")
    print("  inbox <token>                 عرض قائمة الرسائل")
    print("  read <token> <messageId>      قراءة رسالة كاملة مع روابطها")
    print("  drop <token>                  حذف الصندوق نهائيًا")


def _wolf_main(_args=None):
    _args = list(_args) if _args is not None else _wolf_sys.argv[1:]
    if not _args or _args[0] in ("help", "-h", "--help"):
        _wolf_help()
        return 0
    _cmd = _args[0]
    try:
        match _cmd:
            case "domains":
                for _d in _wolf_domains():
                    print(_d)
            case "create":
                _addr = _args[1] if len(_args) > 1 else None
                _a, _p, _kw = _wolf_new_mailbox(_addr)
                print(_wolf_js.dumps({"address": _a, "password": _p, "token": _kw}, ensure_ascii=False, indent=2))
                _wolf_log("احتفظ بكلمة المرور والرمز بأمان")
            case "auth":
                if len(_args) < 3:
                    print("الاستخدام: auth <address> <password>")
                    return 1
                _tok = _wolf_call("/token", "POST", {"address": _args[1], "password": _args[2]})
                print(_tok["token"])
            case "inbox":
                if len(_args) < 2:
                    print("الاستخدام: inbox <token>")
                    return 1
                _ms = _wolf_inbox(_args[1])
                if not _ms:
                    print("لا توجد رسائل في الصندوق بعد")
                for _x in _ms:
                    print(_x.get("createdAt"), "|", _x.get("from"), "|", _x.get("subject"), "|", _x.get("id"))
            case "read":
                if len(_args) < 3:
                    print("الاستخدام: read <token> <messageId>")
                    return 1
                print(_wolf_js.dumps(_wolf_read(_args[1], _args[2]), ensure_ascii=False, indent=2))
            case "drop":
                if len(_args) < 2:
                    print("الاستخدام: drop <token>")
                    return 1
                if _wolf_drop(_args[1]):
                    print("تم حذف الصندوق بنجاح")
            case _:
                print(f"أمر غير معروف: {_cmd} — استخدم 'help' لعرض الأوامر المتاحة")
                return 1
    except RuntimeError as _e:
        _wolf_log("خطأ:", str(_e))
        return 1
    except Exception as _e:
        _wolf_log("خطأ غير متوقع:", str(_e)[:300])
        return 1
    if _wolf_twist(len(_args)) % 97 == 0:
        _wolf_log("اكتمل التنفيذ")
    return 0


if __name__ == "__main__":
    _wolf_sys.exit(_wolf_main())