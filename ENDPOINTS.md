# Arena AI (arena.ai) — API Endpoints

> مستخرجة من تحليل حزم JavaScript الخاصة بالموقع (Next.js + Vercel + Supabase + Cloudflare).

> **الاستخدام العملي:** هذه النقاط مجرّبة فنيًا، ويمكن تنفيذها مباشرة عبر أدوات `tools/` — خاصة `tools/arena_api.py` للواجهة الخام و `tools/agent_api.py` لمسار الوكيل المحلي.

## المعمارية
- الواجهة: Next.js (App Router) على Vercel
- المصادقة: Supabase Auth (JWT HS256 عبر كوكي `arena-auth-prod-v1`)
- بادئة الـ API: `/nextjs-api/*` (تواجه Vercel) و `/api/*` (oRPC/Hono مباشر)
- الحماية: Cloudflare (`__cf_bm`) + reCAPTCHA Enterprise v3 على إرسال الرسائل

## نقاط الاتصال

### المصادقة والمستخدم
| Method | Endpoint | الوصف |
|---|---|---|
| GET | `/api/me` | بيانات المستخدم الحالي |
| POST | `/nextjs-api/sign-up` | تسجيل ضيف/مجهول. body: `{recaptchaToken, provisionalUserId}` (يُقبل توكن فارغ) |
| POST | `/nextjs-api/sign-in/email` | دخول بالإيميل |
| POST | `/nextjs-api/sign-in/google` | دخول بجوجل |
| POST | `/nextjs-api/sign-up/magic-link` | رابط سحري |
| POST | `/nextjs-api/sign-out` | خروج |
| POST | `/api/me/update-tou-consent` | قبول شروط الاستخدام (**مطلوب قبل أي محادثة**) — body: `{}` |
| GET | `/api/me/pulse` | إشعارات/نشاط المستخدم |

### المحادثة والتقييم (SSE streaming)
| Method | Endpoint | الوصف |
|---|---|---|
| POST | `/nextjs-api/stream/create-evaluation` | **إنشاء جلسة + إرسال أول رسالة** — البث يبدأ من نفس الاستجابة |
| POST | `/nextjs-api/stream/post-to-evaluation/{sessionId}` | رسالة إضافية لجلسة قائمة |
| PUT | `/nextjs-api/stream/retry-evaluation-session-message/{sid}/messages/{mid}` | إعادة محاولة رسالة |
| POST | `/nextjs-api/stream/stop/{sid}/messages/{mid}` | إيقاف التوليد |
| POST | `/nextjs-api/stream/skip-direct-battle/{id}` | تخطي مقارنة. body: `{messageAId, messageBId, modelAMessageId}` |
| POST | `/nextjs-api/stream/resample/{sessionId}` | إعادة توليد |
| POST | `/nextjs-api/stream/rerun/{sessionId}` | إعادة تشغيل |
| POST | `/nextjs-api/stream/resume-video-workflow/{sessionId}` | استئناف فيديو |
| POST | `/nextjs-api/stream/resume-webdev/{sessionId}` | استئناف ويب ديف |
| POST | `/nextjs-api/stream/create-evaluation` body يدعم `webhook: {url, data}` | استدعاء خارجي عند انتهاء التوليد |

#### جسم طلب `create-evaluation`
```json
{
  "id": "UUIDv7 (يجب أن يكون طابعه الزمني قريب من الآن)",
  "mode": "direct | direct-battle | side-by-side | battle",
  "modality": "chat | webdev | search | image | video | audio",
  "modelAId": "UUID (اختياري — يثبت موديل معين في direct)",
  "modelBId": "UUID (لـ side-by-side)",
  "userMessageId": "UUIDv7",
  "modelAMessageId": "UUIDv7",
  "modelBMessageId": "UUIDv7 (battle فقط)",
  "recaptchaV3Token": "توكن reCAPTCHA Enterprise v3 — مطلوب للـ chat/webdev",
  "userMessage": {
    "content": "النص",
    "experimental_attachments": [],
    "metadata": {}
  },
  "webhook": { "url": "https://...", "data": "..." }
}
```

**حدود التحقق من الـ IDs:** السيرفر يرفض (`400`) أي UUIDv7 طابعه الزمني أبعد من ساعة عن وقت السيرفر (`"Evaluation session ID seems spoofed, offset too big"`).

### أدوات مساعدة
| Method | Endpoint | الوصف |
|---|---|---|
| POST | `/nextjs-api/auto-modality` | تصنيف تلقائي للسؤال. body: `{user_prompt, has_image}` → `{predicted_modality, probabilities}` — **بدون حماية** |
| POST | `/nextjs-api/factuality/verify` | تحقق من صحة المعلومات |
| GET | `/api/history/unified` | سجل المحادثات — `{"entries":[],...}` |
| GET | `/api/history/search?q=` | بحث في السجل |
| GET | `/api/evaluation/{id}` | تفاصيل جلسة |
| GET | `/api/evaluation/{id}/cost` | تكلفة جلسة |
| GET | `/api/evaluation/webdev/{messageId}/stream-credentials` | بيانات بث الويب ديف → `{runId, publicAccessToken}` |
| DELETE | `/api/chat/{id}` | حذف محادثة |
| POST | `/api/chat/{id}/archive` / `unarchive` | أرشفة |
| GET | `/api/chat/{id}/cost` | تكلفة محادثة |

### التصويت
- زوجي (Pairwise): `model_a | model_b | tie | both_bad | skip` — يتطلب reCAPTCHA v3
- فردي (Pointwise): `upvote | downvote`
- Meta: `{modelsRevealed, didInspectBothMobileHorizontalResponses}`

## حماية إرسال الرسائل (reCAPTCHA Enterprise) — والحلول

- **مفتاح الموقع:** `6LeTGMcsAAAAALuIlkVwIxaAuZA8VledA6d3Nnb0`
- **يُحمَّل عبر:** `https://www.google.com/recaptcha/enterprise.js?render=...` → نسخة Enterprise من v3
- **الأكشن:** `chat_submit` / `chat_retry` / `sign_up` / `pairwise_feedback`
- السيرفر يتحقق عبر Google Enterprise siteverify ويرفض (`403 {"error":"recaptcha validation failed"}`)
- `sign-up` **يُقبل** بدون توكن، لكن `stream/*` **يتطلب** توكنًا صالحًا لموديلات `chat` و `webdev`
- ⏱️ **عمر التوكن ~120 ثانية فقط** (استخدام واحد) — ولّده واستعمله فورًا

### الحل 1: مجاني — متصفحك أنت (الأكثر موثوقية)
افتح https://arena.ai ثم DevTools Console والصق:
```js
grecaptcha.enterprise.execute(
  '6LeTGMcsAAAAALuIlkVwIxaAuZA8VledA6d3Nnb0',
  {action: 'chat_submit'}
).then(t => console.log(t))
```
انسخ التوكن ومرّره فورًا — المسار الخام يقرأ مفاتيح المزوّدين تلقائيًا (انظر الحلول التالية):
```powershell
python tools/arena_api.py chat "مرحبا"
```

### الحل 2: 2captcha (~$3 لكل 1000 توكن)
التوثيق: https://2captcha.com/api-docs/recaptcha-v3
- نوع المهمة: `RecaptchaV3TaskProxyless` + `isEnterprise: true` + `minScore: 0.9` + `pageAction: chat_submit`
```powershell
$env:TWOCAPTCHA_KEY = "YOUR_API_KEY"
python tools/arena_api.py chat "مرحبا"
```

### الحل 3: CapSolver
التوثيق: https://docs.capsolver.com/guide/captcha/ReCaptchaV3/
- نوع المهمة: `ReCaptchaV3EnterpriseTaskProxyLess` + `pageAction: chat_submit`
```powershell
$env:CAPSOLVER_KEY = "CAP-..."
python tools/arena_api.py chat "مرحبا"
```

### الحل 4: YesCaptcha
- نوع المهمة: `ReCaptchaV3EnterpriseTaskProxyLess`
```powershell
$env:YESCAPTCHA_KEY = "..."
python tools/arena_api.py chat "مرحبا"
```

### الحل 5: متصفح آلي (بدون خدمات مدفوعة)
Playwright/Puppeteer headless يفتح arena.ai وينفّذ `grecaptcha.enterprise.execute` لسحب التوكن ثم يمرّره للـ API الخام — وسط بين "متصفح كامل" و"API خام". ملاحظة: جوجل يعطي سكور أقل للترويسات غير الحقيقية، لذا استخدم `playwright-extra` + `stealth plugin`.

### ملاحظات مهمة
- التوكن مرتبط بـ `pageAction` الصحيح: `chat_submit` لإرسال الرسائل (وليس أي أكشن آخر)
- إن فشل التوكن برفض السيرفر رغم صلاحيته: ارفع `minScore` إلى 0.9، وجرّب بروكسي سكني مع `ReCaptchaV3EnterpriseTask` (نوع البروكسي في 2captcha/capsolver)
- بعض الخدمات تعيد `recaptcha-ca-t` ككوكي إضافي (وضع الجلسة `isSession`) — الموقع لا يستخدمه حتى الآن

## مصفوفة الاستجابات (مُختبَرة فعليًا)
| الطلب | بدون مصادقة | ضيف بدون توكن reCAPTCHA |
|---|---|---|
| `sign-up` | — | 200 ✅ |
| `update-tou-consent` | 401 | 200 ✅ |
| `auto-modality` | 200 ✅ | 200 ✅ |
| `battle + chat` | 401 | **403 recaptcha** |
| `direct + chat` | 401 | 401 LOGIN_GATE |
| `battle + webdev` | 401 | 403 recaptcha |
| `battle + search/image/audio/video` | — | 401 LOGIN_GATE (تتطلب حسابًا مسجّلًا) |

## الأنماط والقيم
```
EChatMode:          direct | direct-battle | side-by-side | battle
EEvaluationModality: auto | chat | webdev | search | image | p2l | video | audio
EMessageRole:       system | user | assistant | data
EMessageStatus:     pending | success | failed | flagged | resampling | stopped
PairwiseFeedback:   model_a | model_b | tie | both_bad | skip
Visibility:         public | private
```

## حدود المعدل
- `ratelimit: limit=1800, remaining=..., reset=300` (لكل 5 دقائق، في الهيدرز)
- هيدر خاص: `x-arena-request-caller: web-ssr-public`
