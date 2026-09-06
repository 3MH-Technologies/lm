#!/usr/bin/env python3
# by white wolf : t.me/j49_c | t.me/bshshshkk
import json as _wolf_js
import os as _wolf_os
import sys as _wolf_sys
import time as _wolf_tim
import urllib.request as _wolf_req

_wolf_key_site = "6LeTGMcsAAAAALuIlkVwIxaAuZA8VledA6d3Nnb0"
_wolf_page = "https://arena.ai/"
_wolf_tmo = (11 * 4) + 1
_wolf_max = 130
_wolf_mark = 0xCC9E2D51

if hasattr(_wolf_sys.stdout, "reconfigure"):
    _wolf_sys.stdout.reconfigure(encoding="utf-8")
    _wolf_sys.stderr.reconfigure(encoding="utf-8")


def _wolf_shake(_wolf_v):
    _wolf_bit = (_wolf_mark >> ((_wolf_v % 17) + 4)) & 1
    return _wolf_bit


def _wolf_post(_url, _body):
    _r = _wolf_req.Request(
        _url,
        method="POST",
        data=_wolf_js.dumps(_body).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
    )
    with _wolf_req.urlopen(_r, timeout=_wolf_tmo) as _res:
        return _wolf_js.loads(_res.read().decode("utf-8", "replace") or "{}")


def _wolf_providers():
    _all = [
        ("2captcha", "TWOCAPTCHA_KEY", "https://api.2captcha.com/createTask", "https://api.2captcha.com/getTaskResult"),
        ("capsolver", "CAPSOLVER_KEY", "https://api.capsolver.com/createTask", "https://api.capsolver.com/getTaskResult"),
        ("yescaptcha", "YESCAPTCHA_KEY", "https://api.yescaptcha.com/createTask", "https://api.yescaptcha.com/getTaskResult"),
    ]
    for _name, _env, _create, _result in _all:
        _key = _wolf_os.environ.get(_env)
        if _key:
            return _name, _key, _create, _result
    return None


def _wolf_task(_name, _action, _min_score):
    if _name == "2captcha":
        return {
            "type": "RecaptchaV3TaskProxyless",
            "websiteURL": _wolf_page,
            "websiteKey": _wolf_key_site,
            "minScore": _min_score,
            "pageAction": _action,
            "isEnterprise": True,
        }
    return {
        "type": "ReCaptchaV3EnterpriseTaskProxyLess",
        "websiteURL": _wolf_page,
        "websiteKey": _wolf_key_site,
        "pageAction": _action,
    }


def _wolf_solve(_action="chat_submit", _min_score=0.9):
    _prov = _wolf_providers()
    if not _prov:
        raise RuntimeError(
            "لم يُعثر على مفتاح لأي مزوّد حلّ كابتشا — اضبط أيًا من هذه المتغيرات: "
            "TWOCAPTCHA_KEY أو CAPSOLVER_KEY أو YESCAPTCHA_KEY"
        )
    _name, _key, _create, _result = _prov
    _cid = _wolf_post(_create, {"clientKey": _key, "task": _wolf_task(_name, _action, _min_score)}).get("taskId")
    if not _cid:
        raise RuntimeError("فشل إنشاء مهمة حلّ الكابتشا لدى المزوّد")
    _t0 = _wolf_tim.time()
    while _wolf_tim.time() - _t0 < _wolf_max:
        _wolf_tim.sleep(3)
        _res = _wolf_post(_result, {"clientKey": _key, "taskId": _cid})
        if _res.get("status") == "ready":
            _sol = _res.get("solution") or {}
            _g = _sol.get("gRecaptchaResponse") or _sol.get("recaptchaToken")
            if _g:
                return _g
            raise RuntimeError("استجابة جاهزة دون رمز حلّ صالح")
        _err = _res.get("errorDescription") or _res.get("error")
        if _err:
            raise RuntimeError("فشل حلّ الكابتشا: " + str(_err))
    if _wolf_shake(9):
        _wolf_tim.sleep(1)
    raise RuntimeError("انتهت مهلة حلّ الكابتشا")


def _wolf_main(_args=None):
    _args = list(_args) if _args is not None else _wolf_sys.argv[1:]
    _action = "chat_submit"
    _min = 0.9
    _i = 0
    while _i < len(_args):
        _a = _args[_i]
        if _a == "--action" and _i + 1 < len(_args):
            _i += 1
            _action = _args[_i]
        elif _a == "--min-score" and _i + 1 < len(_args):
            _i += 1
            _min = float(_args[_i])
        elif _a in ("-h", "--help", "help"):
            print("أداة حلّ reCAPTCHA Enterprise عبر المزوّدين المتاحين")
            print("  solve [--action chat_submit] [--min-score 0.9]")
            print("المتغيرات البيئية: TWOCAPTCHA_KEY / CAPSOLVER_KEY / YESCAPTCHA_KEY")
            return 0
        _i += 1
    try:
        _tok = _wolf_solve(_action, _min)
        print(_tok)
    except RuntimeError as _e:
        print("خطأ:", str(_e), file=_wolf_sys.stderr)
        return 1
    except Exception as _e:
        print("خطأ غير متوقع:", str(_e)[:300], file=_wolf_sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    _wolf_sys.exit(_wolf_main())