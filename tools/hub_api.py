#!/usr/bin/env python3
# by white wolf : t.me/j49_c | t.me/bshshshkk
import json as _wolf_js
import os as _wolf_os
import sys as _wolf_sys
import time as _wolf_tim
import urllib.request as _wolf_req
import urllib.error as _wolf_err

_wolf_hub = _wolf_os.environ.get("ARENA_HUB_URL", "https://arena-hub.contact-3mh.workers.dev")
_wolf_secret = _wolf_os.environ.get("ARENA_HUB_SECRET", "")
_wolf_ua = "Mozilla/5.0"
_wolf_tmo = (7 * 4) + 2
_wolf_wait = 5 * 60
_wolf_mark = 0x0F2B3C4D

if hasattr(_wolf_sys.stdout, "reconfigure"):
    _wolf_sys.stdout.reconfigure(encoding="utf-8")
    _wolf_sys.stderr.reconfigure(encoding="utf-8")


def _wolf_pad(_wolf_x):
    _wolf_mix = (_wolf_mark + _wolf_x * 7) % 31
    return _wolf_mix < 7


def _wolf_call(_path, _m="GET", _body=None, _timeout=None):
    _h = {"Content-Type": "application/json", "User-Agent": _wolf_ua}
    if _wolf_secret:
        _h["X-Auth"] = _wolf_secret
    _r = _wolf_req.Request(
        _wolf_hub + _path,
        method=_m,
        headers=_h,
        data=_wolf_js.dumps(_body).encode("utf-8") if _body is not None else None,
    )
    try:
        with _wolf_req.urlopen(_r, timeout=_timeout or _wolf_tmo) as _res:
            return _wolf_js.loads(_res.read().decode("utf-8", "replace") or "{}"), _res.status
    except _wolf_err.HTTPError as _e:
        try:
            return _wolf_js.loads(_e.read().decode("utf-8", "replace")), _e.code
        except Exception:
            return {"error": str(_e)}, _e.code
    except Exception as _e:
        return {"error": str(_e)}, 0


def _wolf_health():
    _d, _c = _wolf_call("/health")
    if _c == 200:
        print(f"المحور يعمل بنجاح ✅ — {_wolf_hub}")
        return True
    print(f"المحور غير متاح حالياً ({_c}): {_d}")
    return False


def _wolf_queue(_prompt, _mode="battle"):
    if not _prompt.strip():
        raise RuntimeError("لا يمكن إرسال رسالة فارغة")
    _job, _code = _wolf_call("/jobs", "POST", {"prompt": _prompt, "mode": _mode})
    if _code != 201:
        raise RuntimeError(f"فشل إدراج المهمة في المحور ({_code}): {_job}")
    _jid = _job["id"]
    print(f"أُدرجت المهمة {_jid} — بانتظار عامل المتصفح...", file=_wolf_sys.stderr)
    _t0 = _wolf_tim.time()
    while _wolf_tim.time() - _t0 < _wolf_wait:
        _wolf_tim.sleep(2)
        _j, _c2 = _wolf_call(f"/jobs/{_jid}")
        _st = _j.get("status")
        if _st == "done":
            _res = _j.get("result") or {}
            if not _res.get("ok"):
                raise RuntimeError("خطأ من الوكيل: " + str(_res.get("error")))
            _a = _res.get("answerA")
            _b = _res.get("answerB")
            if _a:
                print("\n=== النموذج أ ===\n" + _a.strip())
            if _b:
                print("\n=== النموذج ب ===\n" + _b.strip())
            if not _a and not _b:
                print("تعذّر استخراج نص — البيانات الخام:", _wolf_js.dumps(_res, ensure_ascii=False)[:400])
            print(f"\n[الجلسة] https://arena.ai/c/{_res.get('sessionId') or _jid}", file=_wolf_sys.stderr)
            return _res
        if _j.get("error"):
            raise RuntimeError("خطأ في المحور: " + str(_j["error"]))
        if _c2 == 404:
            raise RuntimeError("المهمة غير موجودة في المحور")
    raise RuntimeError("انتهت المهلة — تأكد من فتح تبويب arena.ai وتفعيل سكربت Tampermonkey")


def _wolf_job_info(_jid):
    _d, _c = _wolf_call(f"/jobs/{_jid}")
    if _c != 200:
        raise RuntimeError(f"المهمة غير متاحة ({_c}): {_d}")
    print(_wolf_js.dumps(_d, ensure_ascii=False, indent=2))
    return _d


def _wolf_recent(_limit=10):
    _d, _c = _wolf_call(f"/recent?limit={_limit}")
    _jobs = _d.get("jobs", [])
    if not _jobs:
        print("لا توجد مهام مكتملة في المحور حتى الآن")
        return
    for _j in _jobs:
        _res = _j.get("result") or {}
        _prev = (_res.get("answerA") or _res.get("error") or "")[:80].replace("\n", " ")
        _when = _wolf_tim.strftime("%Y-%m-%d %H:%M", _wolf_tim.localtime(_j.get("doneAt", 0) / 1000))
        print(f"[{_when}] {_j.get('id','')[:8]}  {_j.get('prompt','')[:50]}  ->  {_prev}")
def _wolf_help():
    print("أداة محور Cloudflare Worker — إدارة المهام عن بُعد")
    print("  health                       فحص حالة المحور")
    print("  chat <نص الرسالة>            إرسال رسالة وانتظار نتيجة عامل المتصفح")
    print("  job <معرف المهمة>            عرض تفاصيل مهمة محددة")
    print("  recent [عدد]                 آخر المهام المكتملة")
    print("المتغيرات البيئية: ARENA_HUB_URL / ARENA_HUB_SECRET")


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
                    print("الاستخدام: chat \"نص الرسالة\" [--mode battle|direct]")
                    return 1
                _mode = "battle"
                if "--mode" in _prompt:
                    _parts = _prompt.split(" --mode ")
                    _prompt = _parts[0]
                    _mode = _parts[1].split()[0] if len(_parts) > 1 and _parts[1].split() else "battle"
                _wolf_queue(_prompt, _mode)
            case "job":
                if len(_args) < 2:
                    print("الاستخدام: job <معرف المهمة>")
                    return 1
                _wolf_job_info(_args[1])
            case "recent":
                _n = int(_args[1]) if len(_args) > 1 else 10
                _wolf_recent(_n)
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