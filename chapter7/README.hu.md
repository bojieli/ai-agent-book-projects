# 7. fejezet · Modell-utóképzés

> Az előképzést, SFT-t és RL-t tárgyalja: mikor melyiket érdemes választani, hogyan internalizálhatók az eszközhívások, és hogyan javítható a mintahatékonyság.

← [Vissza a magyar főoldalhoz](../docs/hu/README.md) · 📖 [A fejezet olvasása](../book-hu/chapter7.md)

## Kapcsolódó projektek

| Kísérlet | Projekt | Típus | Leírás |
| :--: | --- | :--: | --- |
| 7-1, 7-2 | [learning-from-experience](../chapter1/learning-from-experience/) | ✅ | Azonos kincskereső környezetben hasonlítja össze a Q-learninget és az LLM-alapú tanulást. |
| 7-3 | [MiniMind-pretrain](MiniMind-pretrain/) · `MiniMind-pretrain/minimind/` | 📖 | Egy kis LLM nulláról történő előképzésének folyamatát mutatja be. |
| 7-4 | [MiniMind-pretrain](MiniMind-pretrain/) · `MiniMind-pretrain/minimind-v/` | 📖 | Egy kis látás-nyelvi modell előképzését és SFT-jét ismerteti. |
| 7-5 | [continued-pretraining](continued-pretraining/) | ✅ | Tartományspecifikus adatokon folytatja az előképzést. |
| 7-6 | [sesame](sesame/) · [orpheus](orpheus/) | 🚧 | Két beszéd-SFT útvonalat vizsgál paralingvisztikai címkékhez és mondatok közötti hangszínkonzisztenciához. |
| 7-7 | [MultilingualReasoning](MultilingualReasoning/) | 🚧 | Több nyelven tanítja a modell következtetési képességét. |
| 7-8 | [prompt-distillation](../chapter8/prompt-distillation/) | ✅ | Tanáradatot készít, diákmodellt képez, majd minőséget és költséget hasonlít össze. |
| 7-9 | [cot-distillation](cot-distillation/) | 🚧 | Helyes CoT-nyomvonalakat szűr, és SFT-adattá alakítja őket. |
| 7-10 | [AdaptThink](AdaptThink/) · `AdaptThink-original/` | 📖 | A feladat nehézsége alapján tanítja meg a modellt a Thinking és NoThinking mód közötti választásra. |
| 7-11 | `SFTvsRL/` | 📖 | Azonos költségkeret mellett hasonlítja össze az SFT memorizálását és az RL általánosítását. |
| 7-12 | [SpatialReasoning](SpatialReasoning/) · `SFTvsRL/` | 📖 | Belső és eloszláson kívüli térbeli következtetést tanít és értékel. |
| 7-13 | [SimpleVLA-RL](SimpleVLA-RL/) · `SimpleVLA-RL/SimpleVLA-RL/` | 📖 | A látást, nyelvet és cselekvést megerősítéses tanulásban kapcsolja össze. |
| 7-14 | [retool](retool/) · `verl/` · `SandboxFusion/` | 📖 | Kódértelmező használatára tanít veRL háttérrendszerrel és végrehajtási sandboxszal. |
| 7-15 | [AWorld-train](AWorld-train/) · `AWorld/` | 📖 | AWorld-alapú GAIA-környezetben tanít eszközhasználó ágenst. |
| 7-16 | [RLVP](RLVP/) · `RLVP/rlvp/` | 📖 | Az RLVP-kutatást reprodukálja: jutalmazza az eredményt, és bünteti az útvonalat. |
| 7-17 | [premature-completion-dpo](premature-completion-dpo/) | ✅ | Korai befejezési bad case DPO-javítása GPU-n. |
| 7-18 | [curly-quote-sft](curly-quote-sft/) | ✅ | Auditált, hatókörérzékeny kínai görbe idézőjel-SFT: 1024/256/256 tanító/holdout/perem eset 10 műfajban és 9 programnyelven; a Qwen3-8B 96,9%/97,7% exact és 100% védett-rész megőrzést ért el GPU-n. |
| 7-19 | [exact-copy-sft](exact-copy-sft/) | ✅ | Auditált bájt-pontos speciális karakterlánc-SFT: 1024/256/256 eset; a Qwen3-8B holdout 78,9%, perem 80,1%, Qwen3/Qwen2.5/Mistral tokenizer-audittal. |
| — | `verl/` | 📖 | Hatékony RLHF-keretrendszer PPO, GRPO, DAPO és további algoritmusok számára. |
| — | [Intuitor](Intuitor/) | ✅ | Hosszú gondolatmenet nélkül tanít intuitív következtetést. |
| — | `tinker-cookbook/` | 📖 | Modellképzési receptek és bevált gyakorlatok gyűjteménye. |

## Projekttípusok

| Ikon | Típus | Jelentés |
| :--: | --- | --- |
| ✅ | **Önálló** | A teljes kód a repository-ban található, és az API-kulcsok beállítása után futtatható. |
| 📖 | **Reprodukciós útmutató** | Külső repository szükséges, amelyet külön kell `git clone` paranccsal letölteni. |
| 🚧 | **Folyamatban** | Az implementáció, a tanítás vagy az elfogadási bizonyíték még nem teljes. |
