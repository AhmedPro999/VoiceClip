# 🎙 VoiceClip

**Talk ⇒ Write ⇒ Trans** · Windows

**اضغط، اتكلم عربي، سيب.. والنص في الحافظة.**

أداة ويندوز صغيرة بتشتغل في الـ tray جنب الساعة. تضغط اختصار وتتكلم عربي (فصحى أو مصري)،
وأول ما تسيب الزرار النص بيتحوّل وبيتنسخ في الحافظة جاهز للّصق في أي مكان: واتساب، شات،
ملف، إيميل. وفيها اختصار تاني بيترجم كلامك العربي لإنجليزي طبيعي ومحترف على طول.

*English summary at the bottom of this file.*

---

## المميزات

| | |
|---|---|
| 🎙 **اضغط واستمر، سيب يوقف** | مفيش زرار تاني للإيقاف. طول ما إنت ضاغط بيسجل، سيبت إيدك يبدأ يحوّل. |
| 🇪🇬 **بيفهم المصري** | مش فصحى بس. "إزيك عامل إيه النهارده" بتتكتب زي ما قلتها. |
| 🌍 **ترجمة احترافية** | `Alt+E` يحوّل كلامك العربي لإنجليزي طبيعي بالمعنى، مش كلمة بكلمة. |
| 📋 **في الحافظة على طول** | النص بيتنسخ تلقائياً. وفي اختيار يلصقه مكان المؤشر من غير `Ctrl+V`. |
| 💊 **شريط حالة عصري** | كبسولة صغيرة تحت الشاشة: أحمر بيسجل، أصفر بيحوّل، أخضر خلص. بتظهر وتختفي بنعومة ومبتسرقش التركيز من اللي إنت فيه. |
| 🧠 **Gemini** | بيستخدم Google Gemini، بمفتاح مجاني. بيسمع الصوت بنفسه فالتعريب والترجمة في طلب واحد. |
| 🔁 **بيتصرف لوحده** | لو الموديل مشغول أو خلّص حصته أو النت وقع في الطلب، بيجرب موديل تاني تلقائياً. |
| 🔇 **كشف الصمت** | لو مفيش صوت أصلاً، يقولك فوراً من غير ما يبعت حاجة ويوفر حصتك. |
| 📜 **سجل آخر 20 نص** | من قائمة الأيقونة، تدوس على أي نص قديم ينسخه تاني. |
| 🔌 **أوفلاين (اختياري)** | Whisper + موديل ترجمة على جهازك من غير نت، لو عندك كارت شاشة NVIDIA وتنزيل كبير مش مشكلة. |

---

## التسطيب (مرة واحدة، 5 دقايق)

### 1. Python
لو مش متسطب: نزّله من [python.org/downloads](https://www.python.org/downloads/) (نسخة 3.11 أو أحدث).
**وإنت بتسطّب علّم على "Add Python to PATH"**، من غيرها `install.bat` مش هيلاقيه.

### 2. شغّل `install.bat`
دبل كليك واستنى دقيقة أو اتنين (بينزّل حوالي 150 ميجا مرة واحدة). لو النت قطع، شغّله تاني وهيكمل من مكانه.

### 3. مفتاح Gemini (مجاني)
1. افتح [aistudio.google.com/apikey](https://aistudio.google.com/apikey) بحساب جوجل.
2. اضغط **Create API key** وانسخ المفتاح.
3. افتح `config.json` (اتعمل تلقائي جنب `install.bat`) بالـ Notepad وحط المفتاح في السطر ده بين علامتي التنصيص:
   ```json
   "api_key": "AIza...."
   ```
   واحفظ. (بديل: متغير بيئة اسمه `VOICECLIP_API_KEY`.)

### 4. شغّل `run.bat`
هتلاقي أيقونة ميكروفون زرقا جنب الساعة (لو مش ظاهرة دوس على السهم الصغير `^`).

### 5. (اختياري) يفتح مع ويندوز
دبل كليك على `add_to_startup.bat` مرة واحدة. للإلغاء امسح:
`%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\VoiceClip.lnk`

> **ويندوز Defender وقّف الملف؟** بيحصل مع ملفات `.bat` جديدة. اضغط **More info** ثم **Run anyway**.

---

## الاستخدام

| اعمل إيه | النتيجة |
|---|---|
| اضغط **`Alt + A`** واستمر، اتكلم عربي، سيب | نص **عربي** في الحافظة |
| اضغط **`Alt + E`** واستمر، اتكلم عربي، سيب | ترجمة **إنجليزية** في الحافظة |
| `Ctrl + V` في أي مكان | يلصق النص |

- بيب قصير = بدأ التسجيل. بيب أعلى = النص اتنسخ. بيب منخفض = فشل.
- الشريط تحت الشاشة بيقولك إنت في أي مرحلة وبأي لغة.
- الاختصارات بتشتغل حتى لو لوحة المفاتيح على العربي.
- الحرف `A` أو `E` مش بيتكتب في البرنامج اللي إنت فيه وإنت بتسجل.

### قائمة الأيقونة (كليك يمين على الأيقونة)

| العنصر | الوظيفة |
|---|---|
| الحالة والاختصارات | للعرض بس |
| **شريط الحالة على الشاشة** | تشغيل/إيقاف الكبسولة اللي بتظهر تحت الشاشة |
| **لصق تلقائي مكان المؤشر** | لو شغال، النص بينزل مكان ما إنت واقف فوراً من غير `Ctrl+V` |
| **إشعارات ويندوز** | إشعار ويندوز العادي بالنص (مقفول افتراضياً مش مشكلة، الحافظة بتتعبي في الحالتين) |
| **الأصوات (بيب)** | تشغيل/إيقاف البيب |
| **الوضع** | أونلاين (Gemini) أو أوفلاين (على الجهاز) |
| **نسخ آخر نص تاني** / **نسخ آخر نص عربي** | لو لصقت حاجة تانية فوقه |
| **سجل النصوص** | آخر 20 نص، اضغط على أي واحد ينسخه |
| **فتح ملف الإعدادات** / **فتح ملف اللوج** | |
| **إغلاق** | |

### لما حاجة تفشل

الشريط يطلع أحمر مكتوب فيه **"فشل التسجيل · عربي/إنجليزي"** والسبب:

| الرسالة | المعنى |
|---|---|
| التسجيل قصير جداً | ضغطت وسبت بسرعة. استمر ضاغط وإنت بتتكلم. |
| مفيش صوت مسموع | الميك مكتوم أو بعيد. مبيتبعتش حاجة لجوجل. |
| مسمعتش كلام واضح | في صوت بس الموديل مفهمش. قرّب من الميك. |
| خلصت حصة Gemini المجانية | وصلت لحد الدقيقة أو اليوم. استنى شوية. |
| مفتاح Gemini غلط أو اتلغى | راجع `api_key` في `config.json`. |
| النت مش واصل لجوجل | اتأكد من الاتصال. |

---

## الإعدادات (`config.json`)

| المفتاح | الافتراضي | المعنى |
|---|---|---|
| `hotkeys.arabic` / `hotkeys.english` | `alt+a` / `alt+e` | الاختصارات. أمثلة: `ctrl+shift+r`، `alt+f9`، `win+space` |
| `mode` | `online` | `online` (Gemini/API) أو `offline` (على الجهاز) |
| `overlay` | `true` | شريط الحالة |
| `auto_paste` | `false` | لصق تلقائي مكان المؤشر |
| `notifications` | `true` | إشعارات ويندوز |
| `sounds` | `true` | البيب |
| `online.provider` | `gemini` | `gemini` أو `openai` أو `groq` |
| `online.api_key` | | مفتاحك (أو متغير البيئة `VOICECLIP_API_KEY`) |
| `online.gemini.model` | `gemini-3.5-flash` | موديل الترجمة (الأدق) |
| `online.gemini.fast_model` | `gemini-3.5-flash-lite` | موديل التعريب (الأسرع) |
| `online.gemini.fallback_models` | `["gemini-3.8-flash"]` | يتجربوا تلقائياً لو الأساسي فشل |
| `online.gemini.reasoning_effort` | `low` | `low` أسرع. `medium` لو عاوز ترجمة أدق لجمل طويلة ومعقدة |
| `online.gemini.timeout_seconds` | `40` | مهلة كل طلب |
| `online.gemini.total_budget_seconds` | `100` | أقصى وقت كلي قبل ما يستسلم |
| `audio.min_seconds` | `0.4` | أقصر تسجيل يتقبل |
| `audio.silence_peak` | `0.01` | أقل مستوى صوت يتقبل. لو ميكك ضعيف جداً وبيقولك "مفيش صوت" وإنت بتتكلم، قلّله لـ `0.005` |
| `offline.whisper_model` | `large-v3-turbo` | أو `medium` / `small` لجهاز أضعف |
| `offline.device` | `auto` | `cuda` / `cpu` |

الأداة بتقرأ الملف مع كل تسجيل، فأي تعديل بيشتغل من غير إعادة تشغيل (ما عدا الاختصارات).

---

## الموديلات والحصة المجانية

- الأداة بتكلم Gemini عن طريق **الـ API** بمفتاحك. ده مسار مختلف عن تطبيق Gemini للدردشة، بحصة منفصلة.
- الحصة المجانية ليها **حد في الدقيقة وحد في اليوم** لكل موديل، وبتتجدد كل يوم. المفتاح نفسه مبينتهيش.
- كل ضغطة اختصار = طلب واحد. الاستخدام العادي طول اليوم غالباً مش بيوصل للحد.
- التعريب على `flash-lite` (أسرع وحصته أكبر)، والترجمة على `flash` (أدق). لو واحد فيهم وصل حده، الأداة بتنط للتاني لوحدها.
- الصوت بيتبعت MP3 مضغوط (12 ثانية ≈ 47 كيلو) علشان يبقى سريع على النت البطيء.
- لو جوجل غيّرت أسماء الموديلات، عدّل `model` و`fast_model` في الإعدادات.

### مزوّدين تانيين
غيّر `online.provider` لـ `openai` أو `groq` وحط مفتاحهم في `api_key`. دول بيستخدموا Whisper للصوت وموديل لغوي للترجمة (طلبين بدل واحد).

---

## الوضع الأوفلاين (اختياري)

لو عاوزها تشتغل من غير نت أو من غير أي API:

1. شغّل `install_offline.bat` (حوالي 4 جيجا حزم: Whisper وCUDA وPyTorch وموديل الترجمة). لو النت قطع، شغّله تاني وهيكمل.
2. غيّر الوضع لـ **أوفلاين** من قائمة الأيقونة.
3. أول استخدام هينزّل موديل Whisper (1.6 جيجا) وموديل الترجمة NLLB (2.4 جيجا) مرة واحدة.

- بيشتغل على كارت NVIDIA لو موجود (4 جيجا VRAM كفاية)، ولو مفيش بيشتغل على المعالج أبطأ.
- التعريب جودته ممتازة. الترجمة الأوفلاين أقل من Gemini في اللهجة المصرية.
- الأداة بترفض التحويل للأوفلاين لو الحزم مش متسطبة وبتقولك.

---

## الخصوصية

- في الوضع الأونلاين، الصوت بيتبعت لجوجل (Gemini API) علشان يتحول لنص. مفيش أي سيرفر تاني في النص.
- في الوضع الأوفلاين، مفيش حاجة بتخرج من جهازك.
- `voiceclip.log` على جهازك بيسجل النصوص اللي اتحولت علشان لو حصلت مشكلة. امسحه وقت ما تحب، ومتشاركوش.
- `config.json` فيه مفتاحك. متشاركوش ومترفعوش على GitHub (موجود في `.gitignore`).

---

## لو في مشكلة

| | |
|---|---|
| مفيش أيقونة جنب الساعة | شغّل `run_debug.bat` علشان تشوف رسالة الخطأ في نافذة. |
| الاختصار مش بيشتغل في برنامج معين | البرامج اللي شغالة كـ Administrator مبتسمعش اختصارات من برنامج عادي. شغّل `run.bat` كـ Administrator. |
| "محتاج API key" | المفتاح مش في `config.json` أو اتحط غلط. |
| بطيئة | أغلب الوقت النت. جرّب `fast_model` لكل حاجة، أو الوضع الأوفلاين. |
| اللصق التلقائي مش بيلصق | البرنامج اللي إنت فيه ممكن يكون Administrator (شوف فوق). |
| "مفيش صوت مسموع" وإنت بتتكلم | قلّل `audio.silence_peak` لـ `0.005`. |
| تفاصيل أكتر | افتح `voiceclip.log` من قائمة الأيقونة، فيه كل خطوة بالوقت. |

---

## هيكل المشروع

```
VoiceClip/
├── app.py                   # نقطة البداية: أيقونة الـ tray والقائمة (Qt)
├── voiceclip/
│   ├── hotkeys.py           # الاختصارات: اضغط واستمر / سيب يوقف (pynput، بتشتغل مع أي لغة لوحة مفاتيح)
│   ├── recorder.py          # تسجيل الميكروفون 16 kHz
│   ├── pipeline.py          # الدورة: تسجيل → تحويل → ترجمة → حافظة → لصق → شريط
│   ├── gemini.py            # Gemini: الصوت بيتبعت مباشرة، JSON فيه العربي والإنجليزي، احتياطي تلقائي
│   ├── transcriber.py       # Whisper أوفلاين / Whisper عبر OpenAI أو Groq
│   ├── translator.py        # ترجمة أوفلاين (NLLB) / عبر موديل لغوي
│   ├── overlay.py           # الكبسولة (Qt): حواف ناعمة، ظل، ظهور واختفاء، نقطة بتنبض
│   ├── notifier.py          # إشعارات ويندوز والبيب
│   ├── settings.py          # قراءة وحفظ config.json
│   └── log.py               # voiceclip.log
├── config.example.json      # انسخه لـ config.json وحط مفتاحك
├── requirements.txt         # الحزم الأساسية (أونلاين)
├── requirements-offline.txt # حزم الأوفلاين (اختياري)
├── install.bat / install_offline.bat / run.bat / run_debug.bat / add_to_startup.bat
└── LICENSE                  # MIT
```

**إزاي بتشتغل:** هوك منخفض المستوى للكيبورد بيمسك ضغط وسيب الاختصار (بالـ scan code علشان يشتغل مع لوحة المفاتيح العربية)، الصوت بيتسجل في الذاكرة، يتضغط MP3، يتبعت لـ Gemini مع تعليمات تطلب JSON فيه النص العربي والترجمة، النتيجة تتنسخ في الحافظة وتظهر في الكبسولة.

---

## للمطورين

```bash
git clone https://github.com/AhmedPro999/VoiceClip.git
cd VoiceClip
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
copy config.example.json config.json   # ثم حط المفتاح
.venv\Scripts\python app.py
```

- Python 3.11+ على ويندوز. الحزم: `pynput`, `sounddevice`, `numpy`, `pyperclip`, `PySide6-Essentials`, `winotify`, `openai`, `lameenc`.
- لإضافة مزوّد جديد: اعمل كلاس شبه `GeminiProcessor` في `gemini.py` واربطه في `pipeline.py`.
- لتغيير شكل الكبسولة: كل حاجة في `overlay.py` (الألوان في `COLORS`، الحجم في `RADIUS` و`row.setContentsMargins`).

## الرخصة

MIT. استخدمها وعدّلها وشاركها براحتك.

---

## English

**VoiceClip** is a tiny Windows tray app for push-to-talk Arabic dictation.
Hold **`Alt+A`**, speak Arabic (MSA or Egyptian), release: the Arabic text is in your clipboard.
Hold **`Alt+E`**, speak Arabic, release: a natural, professional **English translation** is in your clipboard.
Optional auto-paste drops the text at the cursor. A small rounded status pill at the bottom of the
screen shows recording / converting / done and never steals focus.

**Setup:** install Python 3.11+ (tick *Add to PATH*), run `install.bat`, get a free key at
[aistudio.google.com/apikey](https://aistudio.google.com/apikey), paste it into `config.json` → `online.api_key`,
run `run.bat`. `add_to_startup.bat` makes it start with Windows.

**How it works:** a low-level keyboard hook (pynput, matched by scan code so it works under an Arabic layout)
records the mic while the hotkey is held, the audio is compressed to MP3 and sent to Google Gemini through its
OpenAI-compatible endpoint with a prompt asking for JSON `{arabic, english}`; the result is copied to the clipboard.
Transcription uses `gemini-3.5-flash-lite` (fast), translation `gemini-3.5-flash` (accurate), with automatic
fallback on quota / overload / timeout. Silence and too-short recordings are rejected locally without an API call.
An optional offline mode uses faster-whisper + NLLB on an NVIDIA GPU (`install_offline.bat`, ~4 GB).

**Privacy:** online mode sends audio to Google only. `config.json` (your key) and `voiceclip.log`
(your transcripts) stay local and are git-ignored.

MIT licensed.
