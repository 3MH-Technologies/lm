# أدوات أتمتة Arena AI — white wolf

حزمة أدوات سطر الأوامر، أداة واحدة لكل واجهة REST في منظومة الأتمتة، مع أداتي «إنشاء الحسابات» و«الأداة الشاملة».

## الأداة الشاملة (نقطة الدخول)

```bash
python tools/all_in_one.py help
python tools/all_in_one.py health                     # فحص جميع المكونات
python tools/all_in_one.py session                    # جلسة مؤقتة جديدة على arena.ai
python tools/all_in_one.py me [--force]               # بيانات المستخدم الحالي
python tools/all_in_one.py account [--name اسم]      # إنشاء حساب كامل (بريد مؤقت + ماجك لينك)
python tools/all_in_one.py chat "نص الرسالة" [--mode battle|direct] [--via agent|hub|raw]
python tools/all_in_one.py mail create                # صندوق بريد مؤقت
python tools/all_in_one.py solve                      # حلّ كابتشا وعرض الرمز
```

## الأدوات المفردة

| الأداة | الواجهة | الوظيفة |
|---|---|---|
| `mail_api.py` | mail.tm | بريد مؤقت: إنشاء صندوق، قراءة الرسائل، استخراج الروابط، حذف الصندوق |
| `account_creator.py` | mail.tm + arena.ai | إنشاء حساب كامل: بريد مؤقت ← ماجك لينك ← تعيين كلمة المرور ← حفظ الجلسة |
| `arena_api.py` | arena.ai (خام) | جلسات، whoami، تصنيف السؤال، السجل، محادثة عبر البث |
| `hub_api.py` | محور Cloudflare Worker | فحص المحور، إدراج المهام، استطلاع النتائج |
| `agent_api.py` | الوكيل المحلي (`:8765`) | محادثة متزامنة وغير متزامنة، الحساب الحالي |
| `captcha_api.py` | 2captcha / capsolver / yescaptcha | حلّ reCAPTCHA Enterprise وعرض الرمز |

## المتغيرات البيئية

- `ARENA_HUB_URL` / `ARENA_HUB_SECRET` — محور Cloudflare Worker.
- `ARENA_API_URL` — عنوان الوكيل المحلي (الافتراضي `http://127.0.0.1:8765`).
- `TWOCAPTCHA_KEY` / `CAPSOLVER_KEY` / `YESCAPTCHA_KEY` — مفاتيح مزوّدي حلّ الكابتشا.

## ملاحظات أمان

- كلمات مرور الحسابات تُولَّد عشوائيًا (`secrets`) ولا تُحفظ في الكود.
- ملفات الجلسات: `.arena_api_cookies.json` داخل `tools/`، و`arena_account.json` في جذر المشروع.
- لا تشارك مفاتيحك أو ملفات الجلسات مع أي جهة.

## مثال شامل

```bash
python tools/all_in_one.py health
python tools/all_in_one.py account
python tools/all_in_one.py chat "اشرح لي الحوسبة الكمومية" --via agent
```

---

## الحقوق

- **التطوير والهندسة:** white wolf
- **المنظومة والاستضافة:** [3MH TECHNOLOGIES](https://3mh.pages.dev/)