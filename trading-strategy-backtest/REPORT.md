# تقرير اختبار استراتيجية افتتاح السوق الأمريكية على الذهب
# Backtest Report: US-Open Box Breakout Strategy on Gold

**التاريخ / Date:** 2026-07-09
**البيانات / Data:** عقود الذهب الآجلة GC=F (كومكس) — بيانات دقيقة واحدة، من 9 يونيو إلى 8 يوليو 2026 (20 يوم تداول)
**ملاحظة:** لم نتمكن من تحميل الفيديو (محجوب في بيئة العمل)، لكن القواعد المكتوبة + لقطات الشاشة كانت كافية لبرمجة الاستراتيجية بدقة.

---

## 🇸🇦 الملخص بالعربية

### القواعد التي تم اختبارها (كما وصفتها بالضبط)

1. شمعة 5 دقائق عند افتتاح السوق الأمريكية (14:30 بتوقيت المغرب = 9:30 نيويورك) — نرسم صندوقاً على أعلاها وأدناها (بالذيول).
2. ننتظر أول شمعة 5 دقائق تغلق بجسمها خارج الصندوق (فوقه = شراء، تحته = بيع). حددنا مهلة ساعة واحدة.
3. ننزل لفريم الدقيقة وننتظر شمعة مطرقة (ذيل سفلي ≥ ضعف الجسم للشراء، والعكس للبيع) خلال 30 دقيقة من الاختراق. الدخول عند إغلاق المطرقة.
4. وقف الخسارة تحت أقرب قاع (أدنى سعر في آخر 5 شموع دقيقة − 0.5$).
5. الهدف: السيولة كاملة = قمة/قاع جلسة ما قبل الافتتاح (من 3:30 حتى 13:30 UTC).
6. إذا لم يتحقق الهدف أو الوقف: خروج عند إغلاق الجلسة 16:00.

### النتائج (19 صفقة في 20 يوماً)

| المتغير | الصفقات | الرابحة | نسبة النجاح | مجموع R | الناتج بالدولار |
|---|---|---|---|---|---|
| **الاستراتيجية كما هي** (هدف السيولة) | 17 | 5 | **29%** | +7.3R | +7.5$ |
| نفسها **مع تكاليف واقعية** (سبريد 0.5$) | 17 | 5 | 29% | +5.1R | **−1.0$** |
| قراءة صارمة (السعر ما زال خارج الصندوق) | 9 | 2 | 22% | −0.1R | −15.6$ |
| هدف ثابت 1:1 | 19 | 11 | 58% | +3.0R | +33.8$ |
| هدف 1:1 مع التكاليف | 19 | 11 | 58% | **+0.6R** | +24.3$ |
| هدف ثابت 1:2 مع التكاليف | 19 | 7 | 37% | −0.4R | +19.0$ |
| هدف ثابت 1:3 مع التكاليف | 19 | 6 | 32% | +1.1R | −9.3$ |

### الخلاصة الصريحة: **الاستراتيجية لا تُظهر أفضلية (Edge) مثبتة**

1. **نسبة النجاح منخفضة جداً (29%)**: خسرت 12 صفقة من 17. كامل الربح جاء من 4 صفقات فقط (+6.6R، +5.0R، +3.8R، +3.7R). صفقة الفيديو الناجحة يوم 8 يوليو حقيقية، لكنها واحدة من القلة الرابحة — المثال في الفيديو هو "انتقاء للناجح" وليس دليلاً على النظام.
2. **بعد التكاليف الحقيقية** (سبريد الذهب + انزلاق ≈ 0.5$ للصفقة): الناتج الدولاري سلبي (−1$)، والناتج بالـ R يعتمد كلياً على الصفقات الشاذة.
3. **حساسة جداً لتفسير القواعد**: القراءة الصارمة (أن يبقى السعر خارج الصندوق عند الدخول) تحولها إلى خاسرة صريحة. وقواعد "المطرقة" و"أقرب قاع" غير محددة رياضياً في الوصف — أي تغيير بسيط يقلب النتيجة.
4. **حساسة لمصدر البيانات**: يوم 8 يوليو نفسه، بيانات كومكس أعطت إشارة **بيع** (وربحت!) بينما تشارت OANDA الذي استخدمه أخوك أعطى إشارة **شراء** (وربحت أيضاً) — نفس اليوم، اتجاهان متعاكسان حسب المنصة! هذا وحده إنذار كبير: الصندوق يُبنى على 5 دقائق فقط وفروقات الأسعار بين المنصات تقلب الإشارة.
5. **العينة صغيرة** (19 صفقة، شهر واحد): لا يمكن إثبات أو نفي الربحية إحصائياً بهذا الحجم. ما نستطيع قوله: في آخر شهر، النظام لم يتفوق على العشوائية.

### النقطة الإيجابية الوحيدة

فكرة الدخول بعد اختراق صندوق الافتتاح **مع هدف 1:1** أعطت أفضل اتساق (58% نجاح) — لكنها بعد التكاليف تساوي تقريباً الصفر. يعني: الفكرة ليست مجنونة، لكنها بحاجة لفلتر إضافي (مثلاً: التداول فقط مع اتجاه ما قبل الافتتاح، أو تجنب الشراء بعد هبوط ليلي حاد).

### نصائح عملية لأخيك

- **لا تتداول بمال حقيقي بناءً على هذا الفيديو.** جرّبها على حساب تجريبي 3 أشهر على الأقل وسجّل كل صفقة.
- إذا استمررت: خاطر بنسبة ثابتة (مثلاً 0.5-1% من الحساب لكل صفقة) — في اختبارنا تراوح حجم المخاطرة من 1.7$ إلى 17$ للأونصة، وهذا يدمر الحساب بدون تحجيم صحيح.
- انتبه: الوقف "تحت أقرب قاع" كان قريباً جداً في معظم الأيام (2-4$) والذهب يتحرك 1-2$ في ثوانٍ وقت الافتتاح — الوقف يُضرب بسهولة قبل انطلاق السعر (حدث 12 مرة من 17).
- الصفقات الرابحة الكبيرة كلها كانت **بيع** في أيام كان الاتجاه الليلي هابطاً — أي أن "التداول مع سياق ما قبل الافتتاح" يبدو الفلتر الأهم لتحسينها.

---

## 🇬🇧 English Summary

**Strategy tested:** 9:30 ET opening 5-minute candle defines a box (wick-to-wick). First 5m candle whose body closes outside the box arms the direction. Then on the 1-minute chart, the first hammer (in the breakout direction, within 30 min) triggers entry; stop below the nearest low (min of last five 1m lows − $0.5); target = full pre-open liquidity (pre-open session high/low); time-exit at 16:00.

**Data:** COMEX gold futures (GC=F) 1-minute bars, Jun 9 – Jul 8 2026, 20 trading days, fetched from Yahoo Finance (bad ticks repaired). Every day broke its opening box within an hour; 19 days produced a hammer entry.

**Results:** As described: 17 trades, 29% win rate, +7.3R / +$7.5 gross, ≈ $0 after realistic costs; all profit from 4 outlier winners. Strict box-retest reading: 22% win rate, negative. Fixed 1:1 target: 58% win rate but ~break-even after costs. Feed sensitivity is severe: on Jul 8 the COMEX box gave a SHORT while the OANDA spot chart (used in the video) gave a LONG.

**Verdict: no demonstrable edge on this sample.** The video example is a genuine but cherry-picked winner. The concept isn't hopeless — the 1:1 variant and the "trade with the overnight trend" observation are worth forward-testing on demo — but as specified, this is not a system to trade real money on.

**Caveats:** one month of data (Yahoo's 1m limit), futures not spot, mathematically fixed hammer definition (lower wick ≥ 2× body, upper wick ≤ 30% of range), one trade/day, conservative ambiguity handling (none occurred).

## Files

- `backtest.py` — engine (entry detection + simulation + variants). Run: `python3 backtest.py [--cost 0.25]`
- `process_day.py`, `save_tail.py`, `repair_csv.py` — data pipeline (Yahoo v8 chart JSON → clean CSVs)
- `data/1m_*.csv` — 1m bars 9:30–11:00 ET per day; `data/5m_tail_*.csv` — 5m bars 11:00–16:00 ET where needed
- `preopen.json` — pre-open (03:30–13:30 UTC) high/low per day = the "liquidity" targets
- `results_full.txt`, `results_with_costs.txt` — full per-trade output of every variant
