# 🤖 أتمتة Arena AI — white wolf

منظومة أتمتة لمنصة [arena.ai](https://arena.ai): إنشاء حسابات تلقائي، محادثة مباشرة مع النماذج، بريد مؤقت، وحلّ كابتشا — عبر مجموعة أدوات سطر أوامر بيثون بدون مكتبات خارجية.

---

## 🧭 نظرة عامة

```
حاسوبك (سطر أوامر) ──▶ tools/*.py
        │
        ├─ [المسار المحلي]  browser_agent.py  ──▶ نافذة Chrome حقيقية على arena.ai
        ├─ [مسار المحور]   arena-agent.user.js ──▶ تبويب arena.ai يرصد مهام المحور
        └─ [المسار الخام]   arena.ai API مباشرة + مزوّد حلّ كابتشا
```

توكن reCAPTCHA Enterprise الصحيح يتطلب تنفيذًا داخل صفحة arena.ai الحقيقية، لذا:
- **الوكيل المحلي** (`browser_agent.py`) يفتح متصفحًا حقيقيًا وينفّذ المهام داخله ويوفّر API على المنفذ `8765`.
- **سكربت Tampermonkey** (`arena-agent.user.js`) يلتقط مهام محور Cloudflare وينفّذها في تبويب مفتوح.

---

## 📦 البنية الحالية

| المكوّن | الوظيفة |
|---|---|
| `browser_agent.py` | محرك الأتمتة: متصفح حقيقي + خادم API محلي على `:8765` |
| `arena-agent.user.js` | سكربت Tampermonkey لتنفيذ مهام المحور |
| `tools/` | حزمة الأدوات — أداة لكل واجهة API (التفاصيل أدناه) |
| `ENDPOINTS.md` | توثيق نقاط اتصال منصة arena.ai |
| `STREAM_PROTOCOL.md` | بروتوكول البث (Stream) المستخدم في المنصة |

> ملاحظة: الملفات القديمة (`arena.py`, `vibe.py`, `arena.mjs`, `arena-remote.mjs`, `j49_c.py`, `account_creator.py`) أُزيلت لأن وظائفها انتقلت بالكامل إلى أدوات `tools/`.

---

## 🧰 أدوات `tools/` — أداة لكل API

| الأداة | الواجهة | الوظيفة |
|---|---|---|
| `all_in_one.py` | جميعها | **الأداة الشاملة**: نقطة دخول موحّدة لكل الخدمات |
| `account_creator.py` | mail.tm + arena.ai | **إنشاء الحسابات**: بريد مؤقت ← ماجك لينك ← كلمة مرور ← حفظ الجلسة |
| `mail_api.py` | mail.tm | البريد المؤقت: إنشاء صندوق، قراءة الرسائل، استخراج روابط التحقق |
| `arena_api.py` | arena.ai (خام) | جلسة، بيانات المستخدم، تصنيف السؤال، السجل، محادثة بالبث |
| `hub_api.py` | محور Cloudflare Worker | فحص المحور، إدراج المهام، استطلاع النتائج |
| `agent_api.py` | الوكيل المحلي `:8765` | محادثة متزامنة/غير متزامنة، بيانات الحساب |
| `captcha_api.py` | 2captcha / capsolver / yescaptcha | حلّ reCAPTCHA Enterprise وعرض الرمز |

التفاصيل الكاملة في [`tools/README.md`](tools/README.md).

---

## 🚀 الاستخدام السريع

### تشغيل المحرك المحلي
```bash
pip install playwright playwright-stealth
python -m playwright install chrome
python browser_agent.py
```

### الأداة الشاملة
```bash
python tools/all_in_one.py help                          # جميع الأوامر
python tools/all_in_one.py health                        # فحص سلامة المكوّنات
python tools/all_in_one.py session                       # جلسة مؤقتة على arena.ai
python tools/all_in_one.py me                            # بيانات المستخدم الحالي
python tools/all_in_one.py account --name "الاسم الكامل" # إنشاء حساب جديد كاملًا
python tools/all_in_one.py chat "اشرح لي الكوانتم" --via agent
```

### الأدوات المفردة
```bash
python tools/mail_api.py create            # صندوق بريد مؤقت (كلمة مرور مولّدة)
python tools/arena_api.py classify "سؤال"  # تصنيف نوع السؤال تلقائيًا
python tools/hub_api.py health             # فحص المحور (يتطلب تبويبًا + userscript)
python tools/captcha_api.py solve --help   # خيارات حلّ الكابتشا
```

---

## 🔐 المتغيرات البيئية

| المتغير | الاستخدام |
|---|---|
| `ARENA_API_URL` | عنوان الوكيل المحلي (الافتراضي `http://127.0.0.1:8765`) |
| `ARENA_HUB_URL` | عنوان محور Cloudflare Worker |
| `ARENA_HUB_SECRET` | سرّ المصادقة مع المحور |
| `TWOCAPTCHA_KEY` | مفتاح مزوّد حلّ الكابتشا 2captcha |
| `CAPSOLVER_KEY` | مفتاح مزوّد CapSolver |
| `YESCAPTCHA_KEY` | مفتاح مزوّد YesCaptcha |

> ⚠️ لا تُضمَّن الأسرار في الكود أو التوثيق. إذا سبق أن شاركتَ سرًّا لمرة واحدة، استخدم متغيرات البيئة أو غيّره من لوحة تحكم Cloudflare.

> 💡 لضبط المحور داخل سكربت المتصفح (`arena-agent.user.js`): افتح Console على تبويب arena.ai وشغّل:
> `localStorage.setItem("arena_hub_url", "https://..."); localStorage.setItem("arena_hub_secret", "...")`

---

## 🛡️ أمان

- كلمات مرور الحسابات تُولَّد عشوائيًا عبر `secrets` ولا تُحفظ في الكود.
- ملفات الجلسات (`arena_account.json` و `.arena_api_cookies.json`) تُعتبر أسرارًا — لا تشاركها.
- الأدوات خالية من الثغرات الشائعة (لا حقن أوامر، لا كشف أسرار، لا ثغرات SQLi/XSS).

---

## ❓ استكشاف الأخطاء

| المشكلة | الحل |
|---|---|
| «الوكيل المحلي غير متاح» | شغّل `browser_agent.py` أولًا |
| «انتهت المهلة» عبر المحور | افتح تبويب arena.ai وفعّل سكربت Tampermonkey |
| `403 recaptcha` | حدّث الصفحة وانتظر 10 ثوانٍ ثم أعد المحاولة |
| `429` من mail.tm | انتظر دقيقة واحدة (حد معدّل الطلبات) ثم أعد التجربة |

## 📢 الحقوق

- **التطوير والهندسة:** white wolf
- **المنظومة والاستضافة:** [3MH TECHNOLOGIES](https://3mh.pages.dev/)

---

*white wolf • أدوات أتمتة Arena AI — [3MH TECHNOLOGIES](https://3mh.pages.dev/)*
