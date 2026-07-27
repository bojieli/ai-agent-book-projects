# فهم وكلاء الذكاء الاصطناعي بعمق: مبادئ التصميم والممارسة الهندسية

[![PDF](https://img.shields.io/badge/PDF-تنزيل-success.svg)](#-الكتاب-الإلكتروني) [![القراءة عبر الإنترنت](https://img.shields.io/badge/🌐_قراءة_عبر_الإنترنت-bojieli.github.io-success?style=flat-square)](https://bojieli.github.io/ai-agent-book/) [![النجوم](https://img.shields.io/github/stars/bojieli/ai-agent-book?style=social)](https://github.com/bojieli/ai-agent-book) [![الترخيص](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](../../LICENSE) [![اللغات](https://img.shields.io/badge/الترجمات-8%20لغات-informational.svg)](#-الكتاب-الإلكتروني)

**[中文](../../README.md) · [English](../en/README.md) · العربية ← الحالية · [正體中文](../zh-TW/README.md) · [Русский](../ru/README.md) · [Tiếng Việt](../vi/README.md) · [தமிழ்](../ta/README.md) · [日本語](../ja/README.md)**

> **ملاحظة حول الترجمة:** هذه مسودة عربية كاملة أُنجزت بمساعدة الترجمة الآلية مع مراجعة تقنية وبنيوية. نرحب بمراجعة المتحدثين الأصليين لتحسين الأسلوب والمصطلحات.

> 📥 **[تنزيل PDF / EPUB](#-الكتاب-الإلكتروني)** (موصى به) — توفر نسختا PDF وEPUB أفضل تجربة قراءة؛ ويمكنك أيضًا [القراءة عبر الإنترنت](https://bojieli.github.io/ai-agent-book/) مع تبديل اللغات وشجرة الفصول والبحث في النص الكامل.

**الوكيل = LLM + السياق + الأدوات**— يعتمد هذا الكتاب على هذه الصيغة الأساسية عبر 10 فصول، حيث ينقل وكلاء الذكاء الاصطناعي من المبادئ إلى الممارسة الهندسية. النص الكامل والرسوم التوضيحية و**92 تجربة مصاحبة** كلها مفتوحة المصدر. أنتم مدعوون لإجراء التجارب بنفسك.

| 📚 **10 فصول** من الأساسيات إلى الإنتاج | 📂 **92** مشروعًا مصاحبًا (أكثر من 70 مستقلاً) | 🌐 **8 لغات**: CN / EN / AR / zh-TW / RU / TA / VI / JA |
| :---: | :---: | :---: |

## 📖 الكتاب الإلكتروني

> 📥 **تنزيل** (موصى به؛ نص كامل، مجاني ومفتوح المصدر). تشير هذه الروابط دائمًا إلى أحدث إصدار لفرع `main`؛ الإصدارات الثابتة موجودة في صفحة [الإصدارات](https://github.com/bojieli/ai-agent-book/releases):
> - **الصينية (الأصل)**: [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-CN.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-CN.epub)
> - **الإنجليزية** (ترجمة المجتمع، بواسطة [@nsdevaraj](https://github.com/nsdevaraj) و[@whanyu1212](https://github.com/whanyu1212)): [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-en.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-en.epub)
> - **الصينية التقليدية (تايوان)** (ترجمة المجتمع، بواسطة [@tigercosmos](https://github.com/tigercosmos)): [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-TW.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-TW.epub)
> - **الروسية** (ترجمة المجتمع، بواسطة [@ui99ru](https://github.com/ui99ru)): [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ru.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ru.epub)
> - **التاميلية** (ترجمة المجتمع، بواسطة [@nsdevaraj](https://github.com/nsdevaraj)): [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ta.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ta.epub)
> - **الفيتنامية** (ترجمة المجتمع، بواسطة [@toanalien](https://github.com/toanalien)): [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-vi.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-vi.epub)
> - **اليابانية** (ترجمة المجتمع، بواسطة [@eltociear](https://github.com/eltociear)): [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ja.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ja.epub)
> - **العربية** (ترجمة مجتمعية بواسطة [@TheSyBuilder](https://github.com/TheSyBuilder) — النسخة الحالية): [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ar.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ar.epub)
>
> 🌐 يمكنك أيضًا [القراءة عبر الإنترنت](https://bojieli.github.io/ai-agent-book/) - محوّل متعدد اللغات، وشجرة فصول قابلة للطي، والبحث عن النص الكامل، وروابط مباشرة للتجارب المصاحبة. يتم إعادة بنائها تلقائيًا عند كل ضغطة على المفتاح الرئيسي.

يوجد المصدر الصيني في [`book/`](../../book/)، وتوجد النسخة العربية الحالية في [`book-ar/`](../../book-ar/). أما النسخ الإنجليزية والصينية التقليدية والروسية والتاميلية والفيتنامية واليابانية فهي مساهمات مجتمعية قد تتأخر عن الأصل الصيني.

ينتج سكربت البناء الموحّد كتب EPUB 3 بجميع اللغات الثماني، ومنها العربية ذات اتجاه القراءة من اليمين إلى اليسار. راجع [تعليمات إنشاء EPUB](../../EPUB.md).

<details>
<summary><b>🔧 قم بإنشاء ملف PDF بنفسك؟ </b> (يتطلب pandoc / xelatex / ElegantBook)</summary>

- **مصدر النص العربي**: `book-ar/introduction.ar.md`، و`book-ar/chapter1.ar.md` إلى `book-ar/chapter10.ar.md`، و`book-ar/afterword.ar.md`
- **الإنشاء**: قم بتثبيت فئة المستندات pandoc وxelatex وElegantBook والخطوط المطلوبة، ثم قم بتشغيلها

  ```bash
  cd book-ar && bash build_pdf.sh
  ```

  توجد الرسوم العربية في `book-ar/images/`؛ راجع `book-ar/preamble.tex` و`book-ar/*.lua` لتفاصيل التنضيد واتجاه RTL.

</details>

## 📑 نظرة عامة على المحتوى (الفصول 1-10)

يدور الكتاب حول الصيغة الأساسية **الوكيل = LLM + السياق + الأدوات** ، مع عشرة فصول يتم إنشاؤها بشكل تدريجي:

| الفصل | الموضوع | ملخص من سطر واحد | نص | الكود |
| :--: | --- | --- | :--: | :--: |
| 1 | 🚀 **أساسيات الوكيل** | **الوكيل = LLM + السياق + الأدوات**; هندسة الحزام هي الميزة التنافسية الحقيقية | [اقرأ](../../book-ar/chapter1.ar.md) | [4](../../chapter1/README.ar.md) |
| 2 | 🎯 **هندسة السياق** | حدود السياق قدرة الوكيل: KV Cache، الهندسة السريعة، مهارات الوكيل، ضغط السياق | [اقرأ](../../book-ar/chapter2.ar.md) | [9](../../chapter2/README.ar.md) |
| 3 | 📚 **ذاكرة المستخدم وقواعد المعرفة** | ذاكرة المستخدم عبر الجلسات + المعرفة الخارجية: ذاكرة المستخدم، RAG، الفهارس المنظمة، الرسوم البيانية المعرفية | [اقرأ](../../book-ar/chapter3.ar.md) | [13](../../chapter3/README.ar.md) |
| 4 | 🛠️ **الأدوات** | الأدوات هي أيدي الوكيل: بروتوكول MCP، وأدوات الإدراك/التنفيذ/التعاون، والوكلاء غير المتزامنين القائمين على الأحداث، والاكتشاف الاستباقي للأدوات | [اقرأ](../../book-ar/chapter4.ar.md) | [7](../../chapter4/README.ar.md) |
| 5 | 💻 **وكيل الترميز وإنشاء الأكواد** | الكود هو "أداة تنشئ أدوات جديدة"؛ وكيل الترميز على مستوى الإنتاج بالكامل | [اقرأ](../../book-ar/chapter5.ar.md) | [12](../../chapter5/README.ar.md) |
| 6 | 🎯 **تقييم الوكيل** | تحويل الأداء إلى إشارات قابلة للمقارنة: البيئات، والمقاييس، والأهمية الإحصائية، والاختيار القائم على التقييم | [اقرأ](../../book-ar/chapter6.ar.md) | [11](../../chapter6/README.ar.md) |
| 7 | 🧠 **نموذج ما بعد التدريب** | التدريب المسبق/SFT/RL ثلاث مراحل: متى يتم اختيار SFT مقابل RL، واستيعاب استدعاءات الأداة، وكفاءة العينة | [اقرأ](../../book-ar/chapter7.ar.md) | [16](../../chapter7/README.ar.md) |
| 8 | 🔄 **التطور الذاتي للوكيل** | النمو دون تغيير الأوزان: التعلم من الخبرة، من مستخدم الأداة إلى منشئ الأداة | [اقرأ](../../book-ar/chapter8.ar.md) | [6](../../chapter8/README.ar.md) |
| 9 | 🎙️ **تفاعل متعدد الوسائط وفي الوقت الفعلي** | يمتد من النص إلى الصوت، واجهة المستخدم الرسومية، العالم المادي: ثلاثة نماذج صوتية، استخدام الكمبيوتر، الروبوتات | [اقرأ](../../book-ar/chapter9.ar.md) | [7](../../chapter9/README.ar.md) |
| 10 | 🤝 **تعاون متعدد الوكلاء** | الذكاء الجماعي > الفردي: أطر التعاون، مشاركة/عزل السياق، "مجتمع الوكيل" الناشئ | [اقرأ](../../book-ar/chapter10.ar.md) | [7](../../chapter10/README.ar.md) |

> 💡 **اقرأ**= اقرأ نص الفصل على GitHub (تخفيض السعر)؛ **N**= عدد المشاريع المصاحبة، انقر للحصول على الكود. يتم شرح أنواع المشاريع ( ✅ مستقل / 📖 استنساخ / 🚧 تصميم) في الملف التمهيدي الخاص بكل فصل.
>
> 📚 كيف تقرأ هذا الكتاب بكفاءة؟ راجع **[اقتراحات التعلم](LEARNING.md)** (الأفكار الأساسية، ومسار التعلم، ومستويات الصعوبة، ونصائح التدريب).

## 🔑 مفاتيح API

يوصى بالتقدم بطلب للحصول على مفاتيح API من عدة منصات للتعلم المريح. راجع [هذا الدليل](https://01.me/2025/07/llm-api-setup/) لاختيار الطراز.

| منصة | رابط | ملاحظات | الوصول إلى نقاط النهاية |
| --- | --- | --- | --- |
| **كيمي** (Moonshot) | <https://platform.moonshot.cn/> | سلسلة Kimi قوية في السياق الطويل وقدرات العميل | البر الرئيسى للصين |
| **زيبو جي إل إم** | <https://open.bigmodel.cn/> | GLM-4.6 وما إلى ذلك، قدرة صينية قوية وفعالة من حيث التكلفة | البر الرئيسى للصين |
| **تدفق السيليكون** | <https://siliconflow.cn/> | العديد من النماذج مفتوحة المصدر (DeepSeek، Qwen، وما إلى ذلك)، الوصول السريع من الصين القارية | البر الرئيسى للصين |
| **DeepSeek** | <https://platform.deepseek.com/> | الرسمية DeepSeek API | العالمية + البر الرئيسى للصين |
| **كريل الذكاء الاصطناعي** | [www.krill-ai.com](https://www.krill-ai.com/register?invite=Q8D3L35725) | الوصول الشامل إلى النماذج العالمية والمحلية الكبرى (OpenAI، Claude، Gemini، Grok، Kimi، GLM، DeepSeek، Qwen، Minimax) | العالمية + البر الرئيسى للصين |
| **جهاز التوجيه المفتوح** | <https://openrouter.ai/> | الوصول الشامل إلى النماذج العالمية والمحلية الرئيسية (GPT، Claude، Gemini، Kimi، GLM، DeepSeek، Qwen، إلخ.) | عالمي |

## 💎 الرعاة

شكرًا **Krill AI** لرعاية هذا المشروع! يوفر Krill مرحل API رسمي ومستقر وفائق السرعة لـ GPT / Claude / Gemini والعديد من الطرز الصينية، مع التخصيص على مستوى المؤسسة، والفواتير، والدعم الفني المخصص 7 × 16 ساعة، بالإضافة إلى اتصال WebSocket المكيف حصريًا للحصول على وقت سريع للغاية لأول رمز مميز.

يقدم Krill عرضًا خاصًا لقراء هذا الكتاب: قم بالتسجيل عبر [هذا الرابط](https://www.krill-ai.com/register?invite=Q8D3L35725) وأدخل الرمز الترويجي "ai-agent-book" عند إضافة الرصيد للحصول على خصم 23% على خطة Codex الأولى!

## 📦 الملحق · الحصول على المستودعات الخارجية

إن عمليات إعادة الشراء الخارجية التسعة عشر للمعايير وأطر التدريب ومنصات الروبوتات في الفصول 6 و7 و9 و10 **غير مجمعة** (بسبب الحجم والترخيص) ويجب استنساخها في الدلائل المقابلة.

### لقطة واحدة استنساخ النصي

<details>
<summary><b>🔧 توسيع أوامر الاستنساخ</b> (19 إعادة شراء خارجية)</summary>

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

> إذا حدد مشروع README التزامًا معينًا، فسيتم إرسال `git checkout` إلى هذا الإصدار من أجل إمكانية التكرار. تطورت `use-computer-while-calling` للفصل العاشر إلى [19PINE-AI/TalkAct](https://github.com/19PINE-AI/TalkAct) التي تتم صيانتها بشكل مستقل؛ لا يقوم هذا الريبو بتجميع هذا الدليل - استخدم أمر النسخ أعلاه لجلبه.

</details>

### مسارات التكاثر الأخرى

التجارب أدناه لا تحتوي على أمر استنساخ مخصص ولكن لديها طرق استنساخ محددة:

| تجربة | اكتب | ملاحظات |
| --- | :--: | --- |
| 6-2 / 6-3 / 6-4 / 6-9 | 📝 تمرين القارئ | المعيار البشري، تقييم الذاكرة، بطاقات JSON مقابل RAG، اختيار الذاكرة - تكييف `user-memory` / `user-memory-evaluation` / `contextual-retrieval` للفصل الثالث |
| 5-12 | 📝 تمرين القارئ | الوكيل الذي يقوم بإنشاء الوكلاء — التمهيد من `chapter5/coding-agent` |
| 7-8 | 📝 تمرين القارئ | التقطير الفوري — راجع `chapter8/prompt-distillation` (إعادة الاستخدام عبر الفصول) |
| 7-9 | 📝 تمرين القارئ | تقطير CoT `[Extension]` — التنفيذ المصاحب في `chapter7/cot-distillation` (بما في ذلك إنشاء بيانات SFT ومتحقق القاعدة) |
| 6-11 | 🤖 تقييم المحاكاة | OpenVLA + RoboTwin2 — راجع الملف التمهيدي `chapter7/SimpleVLA-RL` للتعرف على تدريب VLA/عمليات البيئة |
| 9-8 / 9-9 | 🔧 أجهزة حقيقية | التشغيل عن بعد بواسطة XleRobot والتحكم في العميل LLM — يتطلب ذراع SO-100، [Teleop](https://xlerobot.readthedocs.io/en/latest/software/getting_started/XLeRobot_teleop.html) · [LLM Agent](https://xlerobot.readthedocs.io/en/latest/software/getting_started/LLM_agent.html) |
| 9-10 | 🔧 أجهزة حقيقية | استيعاب Sim2Real بدون لقطة RGB - [`StoneT2000/lerobot-sim2real`](https://github.com/StoneT2000/lerobot-sim2real) (تعمل المحاكاة على وحدة معالجة الرسومات النقية؛ يحتاج النشر إلى SO-100) |

## 🤝 المساهمة

الكتاب والكود المصاحب له مفتوح المصدر بالكامل. طلبات السحب موضع ترحيب كبير:

| اكتب | ملاحظات |
| --- | --- |
| 📝 **محتوى الكتاب** | الأخطاء أو الإضافات أو الصياغة الأكثر وضوحًا أو التطورات الجديدة (النص في `book/chapter*.md`) |
| 🐛 **تحسينات على الكود وإصلاحات للأخطاء** | اجعل المشاريع المصاحبة أكثر قوة وقابلة للاستخدام وجاهزة للإنتاج |
| 🧪 **مشاريع تدريبية جديدة** | إضافة/استبدال تطبيقات أفضل للتجارب، أو المساهمة بأمثلة جديدة |
| 🎨 **تصميم الشكل** | جعل مخططات `book/images/` أكثر وضوحًا وصقلًا (تم إنشاؤها بواسطة `book/gen_*_figs.py`) |
| 🌐 **ترجمات جديدة** | نرحب بالترجمات إلى المزيد من اللغات؛ انظر الإنجليزية (`book-en/`)، والصينية التقليدية/تايوان (`book-zhtw/`)، والتاميلية (`book-ta/`)، والفيتنامية (`book-vi/`)، واليابانية (`book-ja/`) كمرجع |

قبل التقديم، يرجى تشغيل التجارب ذات الصلة للتأكد من إمكانية تكرار نتائج؛ لا تتردد في فتح قضية لمناقشة الأفكار أولا.

## 📄 الترخيص

هذا المشروع مرخص بموجب [Apache License 2.0](../../LICENSE). راجع ملف [`LICENSE`](../../LICENSE) للحصول على التفاصيل. قد تتضمن بعض المشاريع الفرعية معلومات الترخيص الخاصة بها؛ الرجوع إلى المشروع الفرعي للحصول على تفاصيل.

## ⭐ تاريخ النجوم

<a href="https://star-history.com/#bojieli/ai-agent-book&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="../../assets/star-history-dark.png" />
    <source media="(prefers-color-scheme: light)" srcset="../../assets/star-history-light.png" />
    <img alt="Star History Chart" src="../../assets/star-history-light.png" width="100%" />
  </picture>
</a>

<sub> تم إنشاؤه بواسطة [`scripts/gen_star_history.py`](../../scripts/gen_star_history.py)، ويتم تحديثه يوميًا بواسطة [GitHub Actions](../../.github/workflows/star-history.yml) · انقر على الصورة للحصول على بيانات حية </sub>
