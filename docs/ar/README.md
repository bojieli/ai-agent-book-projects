# فهم وكلاء الذكاء الاصطناعي بعمق: مبادئ التصميم والممارسة الهندسية

[![PDF](https://img.shields.io/badge/PDF-تنزيل-success.svg)](#-الكتاب-الإلكتروني) [![القراءة عبر الإنترنت](https://img.shields.io/badge/🌐_قراءة_عبر_الإنترنت-bojieli.github.io-success?style=flat-square)](https://bojieli.github.io/ai-agent-book/) [![النجوم](https://img.shields.io/github/stars/bojieli/ai-agent-book?style=social)](https://github.com/bojieli/ai-agent-book) [![الترخيص](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](../../LICENSE) [![اللغات](https://img.shields.io/badge/الترجمات-10%20لغات-informational.svg)](#-الكتاب-الإلكتروني)
[![Trending GitHub Project of the Day](https://img.shields.io/badge/GitHub%20Trending-Project%20of%20the%20Day-orange?logo=github)](https://github.com/trending)

**[中文](../../README.md) · [English](../en/README.md) · [Español](../es/README.md) · العربية ← الحالية · [繁體中文（台灣）](../zh-TW/README.md) · [Русский](../ru/README.md) · [Tiếng Việt](../vi/README.md) · [தமிழ்](../ta/README.md) · [日本語](../ja/README.md) · [Türkçe](../tr/README.md)**

> **ملاحظة حول الترجمة:** هذه ترجمة عربية كاملة، خضعت لمراجعة تحريرية وتقنية شملت سلامة المعنى، وطبيعية الأسلوب، واتساق المصطلحات، وبنية النص والرسوم.
>
> 📥 **[تنزيل PDF / EPUB](#-الكتاب-الإلكتروني)** (موصى به) — توفر نسختا PDF وEPUB أفضل تجربة قراءة؛ ويمكنك أيضًا [القراءة عبر الإنترنت](https://bojieli.github.io/ai-agent-book/) مع تبديل اللغات وشجرة الفصول والبحث في النص الكامل.

**الوكيل = LLM + السياق + الأدوات** — تنظم هذه المعادلة فصول الكتاب العشرة، التي تنتقل من المبادئ إلى الممارسة الهندسية. والنص الكامل والرسوم و**93 تجربة مصاحبة** كلها مفتوحة المصدر، ويمكنك تشغيل التجارب بنفسك.

| 📚 **10 فصول** من الأساسيات إلى الإنتاج | 📂 **93** مشروعًا مصاحبًا (أكثر من 70 مستقلاً) | 🌐 **10 لغات**: CN / EN / ES / AR / zh-TW / RU / TA / VI / JA / TR |
| :---: | :---: | :---: |

## 📖 الكتاب الإلكتروني

> 📥 **تنزيل** (موصى به؛ نص كامل، مجاني ومفتوح المصدر). تشير هذه الروابط دائمًا إلى أحدث إصدار لفرع `main`؛ الإصدارات الثابتة موجودة في صفحة [الإصدارات](https://github.com/bojieli/ai-agent-book/releases):
> - **الصينية (الأصل)**: [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-CN.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-CN.epub)
> - **الإنجليزية** (ترجمة المجتمع، بواسطة [@nsdevaraj](https://github.com/nsdevaraj) و[@whanyu1212](https://github.com/whanyu1212)): [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-en.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-en.epub)
> - **الإسبانية** (ترجمة المجتمع): [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-es.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-es.epub)
> - **الصينية التقليدية (تايوان)** (ترجمة المجتمع، بواسطة [@tigercosmos](https://github.com/tigercosmos)): [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-TW.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-TW.epub)
> - **الروسية** (ترجمة المجتمع، بواسطة [@ui99ru](https://github.com/ui99ru)): [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ru.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ru.epub)
> - **التاميلية** (ترجمة المجتمع، بواسطة [@nsdevaraj](https://github.com/nsdevaraj)): [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ta.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ta.epub)
> - **الفيتنامية** (ترجمة المجتمع، بواسطة [@toanalien](https://github.com/toanalien)): [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-vi.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-vi.epub)
> - **اليابانية** (ترجمة المجتمع، بواسطة [@eltociear](https://github.com/eltociear)): [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ja.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ja.epub)
> - **العربية** (ترجمة مجتمعية بواسطة [@TheSyBuilder](https://github.com/TheSyBuilder) — النسخة الحالية): [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ar.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ar.epub)
> - **التركية** (ترجمة المجتمع، بواسطة [@memisemre](https://github.com/memisemre)): [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-tr.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-tr.epub)
>
> 🌐 يمكنك أيضًا [القراءة عبر الإنترنت](https://bojieli.github.io/ai-agent-book/) عبر واجهة متعددة اللغات، وشجرة فصول قابلة للطي، وبحث في النص الكامل، وروابط مباشرة للتجارب المصاحبة. ويُعاد بناء الموقع تلقائيًا عند كل دفع إلى الفرع `main`.

يوجد المصدر الصيني في [`book/`](../../book/)، وتوجد النسخة العربية الحالية في [`book-ar/`](../../book-ar/). أما النسخ الإنجليزية والإسبانية والصينية التقليدية والروسية والتاميلية والفيتنامية واليابانية والتركية فهي مساهمات مجتمعية قد تتأخر عن الأصل الصيني، وتوجد النسخة الإسبانية في [`book-es/`](../../book-es/).

ينتج سكربت البناء الموحّد كتب EPUB 3 باللغات العشر، ومنها العربية ذات اتجاه القراءة من اليمين إلى اليسار. راجع [تعليمات إنشاء EPUB](../../EPUB.md).

<details>
<summary><b>🔧 بناء ملف PDF محليًا</b> (يتطلب pandoc وxelatex وElegantBook)</summary>

- **مصدر النص العربي**: `book-ar/introduction.ar.md`، و`book-ar/chapter1.ar.md` إلى `book-ar/chapter10.ar.md`، و`book-ar/afterword.ar.md`
- **البناء**: ثبّت pandoc وxelatex وفئة ElegantBook والخطوط المطلوبة، ثم شغّل:

  ```bash
  cd book-ar && bash build_pdf.sh
  ```

  توجد الرسوم العربية في `book-ar/images/`؛ راجع `book-ar/preamble.tex` و`book-ar/*.lua` لتفاصيل التنضيد واتجاه RTL.

</details>

## 📑 نظرة عامة على المحتوى (الفصول 1-10)

يدور الكتاب حول المعادلة الأساسية **الوكيل = LLM + السياق + الأدوات**، وتتدرج موضوعاته عبر عشرة فصول:

| الفصل | الموضوع | ملخص من سطر واحد | نص | الكود |
| :--: | --- | --- | :--: | :--: |
| 1 | 🚀 **أساسيات الوكيل** | **الوكيل = LLM + السياق + الأدوات**; هندسة منظومة التشغيل هي الميزة التنافسية الحقيقية | [اقرأ](../../book-ar/chapter1.ar.md) | [4](../../chapter1/README.ar.md) |
| 2 | 🎯 **هندسة السياق** | يحدد السياق سقف قدرة الوكيل: KV Cache، وهندسة الموجّهات، ومهارات الوكيل، وضغط السياق | [اقرأ](../../book-ar/chapter2.ar.md) | [9](../../chapter2/README.ar.md) |
| 3 | 📚 **ذاكرة المستخدم وقواعد المعرفة** | ذاكرة المستخدم عبر الجلسات + المعرفة الخارجية: ذاكرة المستخدم، RAG، الفهارس المنظمة، الرسوم البيانية المعرفية | [اقرأ](../../book-ar/chapter3.ar.md) | [13](../../chapter3/README.ar.md) |
| 4 | 🛠️ **الأدوات** | الأدوات هي أيدي الوكيل: بروتوكول MCP، وأدوات الإدراك/التنفيذ/التعاون، والوكلاء غير المتزامنين القائمين على الأحداث، والاكتشاف الاستباقي للأدوات | [اقرأ](../../book-ar/chapter4.ar.md) | [7](../../chapter4/README.ar.md) |
| 5 | 💻 **وكيل البرمجة وتوليد الشفرة** | الشفرة «أداة تنشئ أدوات جديدة»؛ من وكيل البرمجة الأساسي إلى منظومة جاهزة للإنتاج | [اقرأ](../../book-ar/chapter5.ar.md) | [12](../../chapter5/README.ar.md) |
| 6 | 🎯 **تقييم الوكيل** | تحويل الأداء إلى إشارات قابلة للمقارنة: البيئات، والمقاييس، والأهمية الإحصائية، والاختيار القائم على التقييم | [اقرأ](../../book-ar/chapter6.ar.md) | [11](../../chapter6/README.ar.md) |
| 7 | 🧠 **مرحلة ما بعد تدريب النموذج** | التدريب المسبق وSFT وRL في ثلاث مراحل: متى نختار كل مسار، وكيف يستبطن النموذج استدعاء الأدوات، وكيف نحسن كفاءة العينات | [اقرأ](../../book-ar/chapter7.ar.md) | [16](../../chapter7/README.ar.md) |
| 8 | 🔄 **التطور الذاتي للوكيل** | النمو دون تغيير الأوزان: التعلم من الخبرة، من مستخدم الأداة إلى منشئ الأداة | [اقرأ](../../book-ar/chapter8.ar.md) | [6](../../chapter8/README.ar.md) |
| 9 | 🎙️ **تعدد الوسائط والتفاعل الآني** | من النص إلى الصوت والواجهات الرسومية والعالم المادي: ثلاثة نماذج صوتية، واستخدام الحاسوب، والتحكم في الروبوت | [اقرأ](../../book-ar/chapter9.ar.md) | [7](../../chapter9/README.ar.md) |
| 10 | 🤝 **التعاون متعدد الوكلاء** | الذكاء الجماعي أكبر من الفردي: أطر التعاون، ومشاركة السياق أو عزله، ومجتمعات الوكلاء الناشئة | [اقرأ](../../book-ar/chapter10.ar.md) | [7](../../chapter10/README.ar.md) |

> 💡 **اقرأ** = افتح نص الفصل بصيغة Markdown على GitHub؛ و**N** = عدد المشاريع المصاحبة، ويمكن النقر عليه للوصول إلى الشفرة. تُشرح أنواع المشاريع (✅ مستقل / 📖 إعادة إنتاج / 🚧 تصميم) في ملف README الخاص بكل فصل.
>
> 📚 كيف تقرأ هذا الكتاب بكفاءة؟ راجع **[اقتراحات التعلم](LEARNING.md)** (الأفكار الأساسية، ومسار التعلم، ومستويات الصعوبة، ونصائح التدريب).

## 🔑 مفاتيح API

يُستحسن الحصول على مفاتيح API من أكثر من منصة لتيسير التجربة. راجع [هذا الدليل](https://01.me/2025/07/llm-api-setup/) لاختيار النموذج المناسب.

| منصة | رابط | ملاحظات | الوصول إلى نقاط النهاية |
| --- | --- | --- | --- |
| **Kimi** (Moonshot) | <https://platform.moonshot.cn/> | سلسلة Kimi قوية في السياق الطويل وقدرات الوكلاء | البر الرئيسي للصين |
| **Zhipu GLM** | <https://open.bigmodel.cn/> | نماذج GLM، ومنها GLM-4.6، قوية في الصينية ومنافسة من حيث الكلفة | البر الرئيسي للصين |
| **SiliconFlow** | <https://siliconflow.cn/> | مجموعة واسعة من النماذج المفتوحة، مثل DeepSeek وQwen، مع وصول سريع من الصين | البر الرئيسي للصين |
| **DeepSeek** | <https://platform.deepseek.com/> | واجهة DeepSeek الرسمية | عالمي + البر الرئيسي للصين |
| **Krill AI** | [www.krill-ai.com](https://www.krill-ai.com/register?invite=Q8D3L35725) | وصول موحد إلى نماذج عالمية وصينية، منها OpenAI وClaude وGemini وKimi وGLM وDeepSeek وQwen | عالمي + البر الرئيسي للصين |
| **OpenRouter** | <https://openrouter.ai/> | وصول موحد إلى عدد كبير من النماذج العالمية والمفتوحة | عالمي |

## 💎 الرعاة

شكرًا لـ **Krill AI** على رعاية المشروع. توفر المنصة بوابة API مستقرة وسريعة لنماذج GPT وClaude وGemini وعدد من النماذج الصينية، إلى جانب خيارات للمؤسسات والفوترة والدعم الفني واتصال WebSocket محسّن لخفض زمن وصول الرمز الأول.

تقدم Krill عرضًا لقراء الكتاب: سجّل عبر [هذا الرابط](https://www.krill-ai.com/register?invite=Q8D3L35725)، ثم أدخل الرمز الترويجي `ai-agent-book` عند إضافة الرصيد للحصول على خصم 23% على أول خطة Codex.

## 📦 الملحق · جلب المستودعات الخارجية

لا يتضمن هذا المستودع المستودعات الخارجية التسعة عشر الخاصة بالمعايير وأطر التدريب ومنصات الروبوتات في الفصول 6 و7 و9 و10، وذلك بسبب الحجم وشروط الترخيص. لذا يجب استنساخها في الأدلة المقابلة.

### سكربت للاستنساخ دفعة واحدة

<details>
<summary><b>🔧 عرض أوامر الاستنساخ</b> (19 مستودعًا خارجيًا)</summary>

```bash
# Chapter 6 · Evaluation Benchmarks
git clone https://github.com/google-research/android_world.git         chapter6/android_world
git clone https://huggingface.co/datasets/gaia-benchmark/GAIA          chapter6/GAIA
git clone https://github.com/xlang-ai/OSWorld.git                      chapter6/OSWorld
git clone https://github.com/SWE-bench/SWE-bench.git                   chapter6/SWE-bench
git clone https://github.com/sierra-research/tau2-bench.git            chapter6/tau2-bench
git clone https://github.com/laude-institute/terminal-bench.git        chapter6/terminal-bench

# Chapter 7 · Training Frameworks (bojieli/* are book-adapted forks)
git clone https://github.com/bojieli/minimind.git                      chapter7/MiniMind-pretrain/minimind      # Exp 7-3 train LLM from scratch
git clone https://github.com/bojieli/minimind-v.git                    chapter7/MiniMind-pretrain/minimind-v    # Exp 7-4 train VLM from scratch (projection layer)
git clone https://github.com/bojieli/AdaptThink.git                    chapter7/AdaptThink-original
git clone https://github.com/bojieli/AWorld.git                        chapter7/AWorld
git clone https://github.com/bojieli/SFTvsRL.git                       chapter7/SFTvsRL
git clone https://github.com/bojieli/verl.git                          chapter7/verl
git clone https://github.com/thinking-machines-lab/tinker-cookbook.git chapter7/tinker-cookbook
git clone https://github.com/19PINE-AI/rlvp.git                        chapter7/RLVP/rlvp                       # Exp 7-14 RLVP paper code
git clone https://github.com/PRIME-RL/SimpleVLA-RL.git                 chapter7/SimpleVLA-RL/SimpleVLA-RL       # Exp 7-13 vision-language-action RL

# Chapter 9 · Browser Automation & Claude Examples
git clone https://github.com/browser-use/browser-use.git               chapter9/browser-use
git clone https://github.com/anthropics/claude-quickstarts.git         chapter9/claude-quickstarts

# Chapter 10 · Dual-Agent Architecture (now independent TalkAct project) + Stanford AI Town
git clone https://github.com/19PINE-AI/TalkAct.git                     chapter10/use-computer-while-calling
git clone https://github.com/joonspk-research/generative_agents.git    chapter10/generative_agents             # Exp 10-7 Stanford AI Town
```

> إذا حدد ملف README لمشروع ما معرّف commit بعينه، فنفّذ `git checkout` لذلك الإصدار لضمان قابلية إعادة النتائج. وقد تطور مشروع الفصل العاشر `use-computer-while-calling` إلى [19PINE-AI/TalkAct](https://github.com/19PINE-AI/TalkAct)، وهو يُصان بصورة مستقلة ولا يُضمَّن في هذا المستودع؛ استخدم أمر الاستنساخ أعلاه لجلبه.

</details>

### طرق أخرى لإعادة إنتاج التجارب

التجارب أدناه لا تحتوي على أمر استنساخ مخصص ولكن لديها طرق استنساخ محددة:

| التجربة | النوع | ملاحظات |
| --- | :--: | --- |
| 6-2 / 6-3 / 6-4 / 6-9 | 📝 تمرين القارئ | المعيار البشري، تقييم الذاكرة، بطاقات JSON مقابل RAG، اختيار الذاكرة - تكييف `user-memory` / `user-memory-evaluation` / `contextual-retrieval` للفصل الثالث |
| 5-12 | 📝 تمرين القارئ | الوكيل الذي يقوم بإنشاء الوكلاء — التمهيد من `chapter5/coding-agent` |
| 7-8 | 📝 تمرين القارئ | تقطير الموجّهات — راجع `chapter8/prompt-distillation` (إعادة استخدام بين الفصول) |
| 7-9 | 📝 تمرين القارئ | تقطير CoT `[Extension]` — التنفيذ المصاحب في `chapter7/cot-distillation` (بما في ذلك إنشاء بيانات SFT ومتحقق القاعدة) |
| 6-11 | 🤖 تقييم المحاكاة | OpenVLA + RoboTwin2 — راجع الملف التمهيدي `chapter7/SimpleVLA-RL` للتعرف على تدريب VLA/عمليات البيئة |
| 9-8 / 9-9 | 🔧 أجهزة حقيقية | التشغيل عن بعد بواسطة XleRobot والتحكم في الوكيل LLM — يتطلب ذراع SO-100، [Teleop](https://xlerobot.readthedocs.io/en/latest/software/getting_started/XLeRobot_teleop.html) · [LLM Agent](https://xlerobot.readthedocs.io/en/latest/software/getting_started/LLM_agent.html) |
| 9-10 | 🔧 أجهزة حقيقية | نقل Sim2Real من دون أمثلة باستخدام صور RGB — [`StoneT2000/lerobot-sim2real`](https://github.com/StoneT2000/lerobot-sim2real) (تعمل المحاكاة على وحدة معالجة الرسومات؛ ويتطلب النشر ذراع SO-100) |

## 🤝 المساهمة

الكتاب والكود المصاحب له مفتوح المصدر بالكامل. طلبات السحب موضع ترحيب كبير:

| النوع | ملاحظات |
| --- | --- |
| 📝 **محتوى الكتاب** | الأخطاء أو الإضافات أو تحسين الصياغة أو التطورات الجديدة (النص العربي في `book-ar/chapter*.ar.md`) |
| 🐛 **تحسينات على الكود وإصلاحات للأخطاء** | اجعل المشاريع المصاحبة أكثر قوة وقابلة للاستخدام وجاهزة للإنتاج |
| 🧪 **مشاريع تدريبية جديدة** | إضافة/استبدال تطبيقات أفضل للتجارب، أو المساهمة بأمثلة جديدة |
| 🎨 **تصميم الشكل** | تحسين مخططات SVG المحفوظة في المستودع ضمن `book/images/` مباشرةً |
| 🌐 **ترجمات جديدة** | نرحب بالترجمات إلى المزيد من اللغات؛ انظر العربية (`book-ar/`)، والإنجليزية (`book-en/`)، والصينية التقليدية/تايوان (`book-zhtw/`)، والروسية (`book-ru/`)، والتاميلية (`book-ta/`)، والفيتنامية (`book-vi/`)، واليابانية (`book-ja/`)، والتركية (`book-tr/`) كمرجع |

قبل إرسال مساهمتك، شغّل التجارب ذات الصلة للتأكد من قابلية إعادة النتائج. ويمكنك فتح issue لمناقشة الفكرة أولًا.

## 📄 الترخيص

هذا المشروع مرخص بموجب [Apache License 2.0](../../LICENSE). راجع ملف [`LICENSE`](../../LICENSE) للتفاصيل. وقد تتضمن بعض المشاريع الفرعية تراخيص مستقلة؛ ارجع إلى كل مشروع لمعرفة شروطه.

## ⭐ تاريخ النجوم

<a href="https://star-history.com/#bojieli/ai-agent-book&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="../../assets/star-history-dark.png" />
    <source media="(prefers-color-scheme: light)" srcset="../../assets/star-history-light.png" />
    <img alt="Star History Chart" src="../../assets/star-history-light.png" width="100%" />
  </picture>
</a>

<sub>أنشأه السكربت [`scripts/gen_star_history.py`](../../scripts/gen_star_history.py)، ويُحدَّث يوميًا عبر [GitHub Actions](../../.github/workflows/star-history.yml) · انقر على الصورة لعرض البيانات الحية.</sub>
