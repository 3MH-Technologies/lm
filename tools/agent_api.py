#!/usr/bin/env python3
# by white wolf : t.me/j49_c | t.me/bshshshkk
import json as _wolf_js
import os as _wolf_os
import sys as _wolf_sys
import time as _wolf_tim
import urllib.request as _wolf_req
import urllib.error as _wolf_err

_wolf_base = _wolf_os.environ.get("ARENA_API_URL", "http://127.0.0.1:8765")
_wolf_ua = "Mozilla/5.0"
_wolf_tmo = 30
_wolf_wait = 5 * 60
_wolf_mark = 0x1A2B3C4D

if hasattr(_wolf_sys.stdout, "reconfigure"):
    _wolf_sys.stdout.reconfigure(encoding="utf-8")
    _wolf_sys.stderr.reconfigure(encoding="utf-8")


def _wolf_flip(_wolf_z):
    _wolf_q = (_wolf_mark % (_wolf_z + 5)) == 0
    return _wolf_q


def _wolf_call(_path, _m="GET", _body=None, _timeout=None):
    _h = {"Content-Type": "application/json", "User-Agent": _wolf_ua}
    _r = _wolf_req.Request(
        _wolf_base + _path,
        method=_m,
        headers=_h,
        data=_wolf_js.dumps(_body).encode("utf-8") if _body is not None else None,
    )
    try:
        with _wolf_req.urlopen(_r, timeout=_timeout or _wolf_tmo) as _res:
            return _wolf_js.loads(_res.read().decode("utf-8", "replace") or "{}"), _res.status
    except _wolf_err.HTTPError as _e:
        try:
            return _wolf_js.loads(_e.read().decode("utf-8", "replace") or "{}"), _e.code
        except Exception:
            return {"error": str(_e)}, _e.code
    except Exception as _e:
        return {"error": str(_e)}, 0


def _wolf_health():
    _d, _c = _wolf_call("/health")
    if _c == 200:
        print(f"الوكيل المحلي يعمل ✅ — {_wolf_base}")
        return True
    print(f"الوكيل المحلي غير متاح ({_c}) — تأكد من تشغيل browser_agent.py")
    return False


def _wolf_show(_d):
    _a = _d.get("answerA")
    _b = _d.get("answerB")
    if _a:
        print("\n=== النموذج أ ===\n" + _a.strip())
    if _b:
        print("\n=== النموذج ب ===\n" + _b.strip())
    if not _a and not _b:
        print("تعذّر استخراج نص — البيانات الخام:", _wolf_js.dumps(_d, ensure_ascii=False)[:400])
    return _d


def _wolf_chat(_prompt, _mode="battle", _model=None, _sid=None, _sync=True):
    if not _prompt.strip():
        raise RuntimeError("لا يمكن إرسال رسالة فارغة")
    _body = {"prompt": _prompt, "mode": _mode}
    if _model:
        _body["modelAId"] = _model
    if _sid:
        _body["sessionId"] = _sid
    _path = "/chat/sync" if _sync else "/chat"
    _d, _c = _wolf_call(_path, "POST", _body, timeout=240 if _sync else _wolf_tmo)
    if _c == 202 and not _sync:
        _jid = _d.get("id")
        print(f"أُدرجت المهمة {_jid} — استخدم 'poll {_jid}' لاستطلاع النتيجة", file=_wolf_sys.stderr)
        return _d
    if _c != 200:
        raise RuntimeError(f"فشل طلب المحادثة ({_c}): {_d}")
    if not _d.get("ok"):
        raise RuntimeError("خطأ من الوكيل: " + str(_d.get("error")))
    return _wolf_show(_d)


def _wolf_poll(_jid):
    _t0 = _wolf_tim.time()
    while _wolf_tim.time() - _t0 < _wolf_wait:
        _wolf_tim.sleep(2)
        _d, _c = _wolf_call(f"/chat/{_jid}")
        if _c == 404:
            raise RuntimeError("المهمة غير موجودة لدى الوكيل المحلي")
        if _d.get("status") == "done":
            _res = _d.get("result") or {}
            if not _res.get("ok"):
                raise RuntimeError("خطأ من الوكيل: " + str(_res.get("error")))
            return _wolf_show(_res)
        if _wolf_flip(_wolf_tim.time()):
            _wolf_tim.sleep(1)
    raise RuntimeError("انتهت مهلة انتظار نتيجة المحادثة")
def _wolf_me():
    _d, _c = _wolf_call("/me")
    if _c != 200:
        raise RuntimeError("لا يوجد حساب محفوظ لدى الوكيل المحلي")
    print(_wolf_js.dumps(_d, ensure_ascii=False, indent=2))
    return _d


def _wolf_create_account():
    _d, _c = _wolf_call("/account/create", "GET", timeout=300)
    if _c != 200:
        raise RuntimeError(f"فشل إنشاء الحساب عبر الوكيل ({_c}): {_d}")
    print(_wolf_js.dumps(_d, ensure_ascii=False, indent=2))
    return _d


def _wolf_help():
    print("أداة الوكيل المحلي (browser_agent.py) — المحادثة والتحكم بالحساب")
    print("  health                       فحص حالة الوكيل")
    print("  chat <نص الرسالة>            محادثة متزامنة (Sync) تنتظر النتيجة")
    print("  async <نص الرسالة>           محادثة غير متزامنة وتستلم معرّف مهمة")
    print("  poll <معرف المهمة>           استطلاع نتيجة مهمة غير متزامنة")
    print("  me                           عرض بيانات الحساب الحالي")
    print("  account-create               إنشاء حساب جديد عبر الوكيل")
    print("المتغير البيئي: ARENA_API_URL (الافتراضي http://127.0.0.1:8765)")


def _wolf_main(_args=None):
    _args = list(_args) if _args is not None else _wolf_sys.argv[1:]
    if not _args or _args[0] in ("help", "-h", "--help"):
        _wolf_help()
        return 0
    _cmd = _args[0]
    try:
        match _cmd:
            case "health":
                return 0 if _wolf_health() else 1
            case "chat":
                _prompt = " ".join(_args[1:]).strip()
                if not _prompt:
                    print("الاستخدام: chat \"نص الرسالة\"")
                    return 1
                _wolf_chat(_prompt)
            case "async":
                _prompt = " ".join(_args[1:]).strip()
                if not _prompt:
                    print("الاستخدام: async \"نص الرسالة\"")
                    return 1
                _wolf_chat(_prompt, _sync=False)
            case "poll":
                if len(_args) < 2:
                    print("الاستخدام: poll <معرف المهمة>")
                    return 1
                _wolf_poll(_args[1])
            case "me":
                _wolf_me()
            case "account-create":
                _wolf_create_account()
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