#!/usr/bin/env python3
# by white wolf : t.me/j49_c | t.me/bshshshkk
import json as _wolf_js
import os as _wolf_os
import sys as _wolf_sys
import time as _wolf_tim

_wolf_root = _wolf_os.path.dirname(_wolf_os.path.dirname(_wolf_os.path.abspath(__file__)))
_tools_dir = _wolf_os.path.join(_wolf_root, "tools")
_wolf_sys.path.insert(0, _tools_dir)

import mail_api as _wm
import hub_api as _wh
import agent_api as _wa
import captcha_api as _wc

_wolf_mark = 0x0DDB1A3E
_WOLF_VERSION = "1.0.0"

if hasattr(_wolf_sys.stdout, "reconfigure"):
    _wolf_sys.stdout.reconfigure(encoding="utf-8")
    _wolf_sys.stderr.reconfigure(encoding="utf-8")


def _wolf_mix(_wolf_g):
    _wolf_s = (_wolf_mark * (_wolf_g + 3)) % 29
    return _wolf_s < 9


def _wolf_import_tool(_name):
    _path = _wolf_os.path.join(_tools_dir, _name + ".py")
    if not _wolf_os.path.exists(_path):
        raise RuntimeError(f"الأداة {_name} غير موجودة في مجلد tools")
    import importlib.util
    _spec = importlib.util.spec_from_file_location(_name, _path)
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    return _mod


def _cmd_health():
    print("🔍 فحص سلامة جميع مكونات النظام...")
    _ok = True
    print("\n[1] الوكيل المحلي:")
    _ok = _wa._wolf_health() and _ok
    print("\n[2] محور Cloudflare:")
    _ok = _wh._wolf_health() and _ok
    print("\n[3] جاهزية أدوات البريد المؤقت:")
    try:
        _d = _wm._wolf_domains()
        print(f"    مستعد ✅ — النطاقات المتاحة: {len(_d)}")
    except Exception as _e:
        print("    غير متاح:", str(_e)[:120])
        _ok = False
    print("\n[4] مزوّدو حلّ الكابتشا:")
    try:
        _mc = _wc._wolf_providers()
        if _mc:
            print(f"    مستعد ✅ — المزوّد النشط: {_mc[0]}")
        else:
            print("    غير مُعدّ — اضبط أحد مفاتيح التزويد للتفعيل")
    except Exception as _e:
        print("    غير متاح:", str(_e)[:120])
    print("\n" + ("✅ جميع المكونات تعمل بشكل سليم" if _ok else "⚠️  توجد مكونات تحتاج إلى ضبط"))
    return 0 if _ok else 1


def _cmd_chat(_args):
    import arena_api as _ara
    _rest = _args
    _mode = "battle"
    _model = None
    _sid = None
    _via = "agent"
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
        elif _a == "--via" and _i + 1 < len(_rest):
            _i += 1
            _via = _rest[_i]
        else:
            _p.append(_a)
        _i += 1
    _prompt = " ".join(_p).strip()
    if not _prompt:
        print("الاستخدام: chat <نص الرسالة> [--mode battle|direct] [--model sonnet5] [--via agent|hub|raw]")
        return 1
    if _via == "agent":
        return _wa._wolf_main(["chat", _prompt])
    if _via == "hub":
        return _wh._wolf_main(["chat", _prompt])
    if _via == "raw":
        (_jar, _me, _fr) = _ara._wolf_ensure_user()
        _parts, _sid = _ara._wolf_chat(_jar, _prompt, _mode, _model, _sid)
        _ara._wolf_show_stream(_parts, _sid)
        return 0
    raise RuntimeError("نقل غير معروف — استخدم agent أو hub أو raw")


def _cmd_account(_args):
    _tool = _wolf_import_tool("account_creator")
    _name = "Al Baron"
    if "--name" in _args:
        _i = _args.index("--name")
        if _i + 1 < len(_args):
            _name = _args[_i + 1]
    return _tool._wolf_main(["-n", _name])
def _cmd_me(_args):
    _tool = _wolf_import_tool("arena_api")
    _jar = None
    _stored = _tool._wolf_load_sesh()
    if _stored.get("cookies"):
        _jar = _stored["cookies"]
    if _args and _args[0] == "--force":
        _jar = None
    if _jar:
        try:
            return _tool._wolf_main(["whoami"])
        except Exception as _e:
            print("انتهت صلاحية الجلسة المحفوظة — سيتم إنشاء جلسة جديدة")
    _jar, _me, _fresh = _tool._wolf_ensure_user()
    _tool._wolf_save_sesh({"cookies": _jar, "user": _me.get("user")})
    print(_tool._wolf_js.dumps(_me.get("user") or {}, ensure_ascii=False, indent=2))
    return 0


def _cmd_mail(_args):
    return _wm._wolf_main(_args)


def _cmd_solve(_args):
    _action = "chat_submit"
    _min = 0.9
    if "--action" in _args:
        _i = _args.index("--action")
        if _i + 1 < len(_args):
            _action = _args[_i + 1]
    if "--min-score" in _args:
        _i = _args.index("--min-score")
        if _i + 1 < len(_args):
            _min = float(_args[_i + 1])
    try:
        _tok = _wc._wolf_solve(_action, _min)
        print(_tok)
        return 0
    except RuntimeError as _e:
        print("خطأ:", str(_e), file=_wolf_sys.stderr)
        return 1


def _cmd_session(_args):
    _tool = _wolf_import_tool("arena_api")
    return _tool._wolf_main(["session"])


def _cmd_version():
    print(f"lm — أدوات أتمتة Arena AI (white wolf / 3MH TECHNOLOGIES)  الإصدار {_WOLF_VERSION}")
    return 0


def _cmd_prompt_help():
    print("الأداة الشاملة لإدارة أتمتة منصة arena.ai — white wolf")
    print("")
    print("  version               عرض الإصدار")
    print("  health                فحص سلامة جميع المكونات")
    print("  chat <نص>             إرسال رسالة (عبر الوكيل المحلي افتراضيًا)")
    print("                        [--mode battle|direct] [--model sonnet5|sonnet5-search]")
    print("                        [--session <المعرف>] [--via agent|hub|raw]")
    print("  session               إنشاء جلسة مؤقتة جديدة والقبول بشروط الاستخدام")
    print("  me [--force]          عرض بيانات المستخدم الحالي")
    print("  account [--name اسم]  إنشاء حساب جديد بالكامل (بريد مؤقت + تفعيل)")
    print("  mail <subcommands>    أدوات البريد المؤقت (انظر: mail help)")
    print("  solve [--action chat_submit] [--min-score 0.9]")
    print("                        حلّ كابتشا وعرض الرمز")
    print("")
    print("أمثلة:")
    print("  python all_in_one.py health")
    print("  python all_in_one.py chat \"اشرح لي نظرية النسبية\" --via hub")
    print("  python all_in_one.py account --name \"عبدالله\"")
    print("  python all_in_one.py mail create")


def _wolf_main():
    _args = _wolf_sys.argv[1:]
    if not _args or _args[0] in ("-h", "--help", "help"):
        _cmd_prompt_help()
        return 0
    _cmd = _args[0]
    _rest = _args[1:]
    try:
        match _cmd:
            case "version":
                return _cmd_version()
            case "health":
                return _cmd_health()
            case "chat":
                return _cmd_chat(_rest)
            case "account":
                return _cmd_account(_rest)
            case "me":
                return _cmd_me(_rest)
            case "mail":
                return _cmd_mail(_rest)
            case "solve":
                return _cmd_solve(_rest)
            case "session":
                return _cmd_session(_rest)
            case _:
                print(f"أمر غير معروف: {_cmd} — استخدم 'help' لعرض الأوامر المتاحة")
                return 1
    except RuntimeError as _e:
        print("خطأ:", str(_e), file=_wolf_sys.stderr)
        return 1
    except Exception as _e:
        print("خطأ غير متوقع:", str(_e)[:300], file=_wolf_sys.stderr)
        return 1
    if _wolf_mix(len(_args)):
        _wolf_tim.sleep(0.2)
    return 0


if __name__ == "__main__":
    _wolf_sys.exit(_wolf_main())