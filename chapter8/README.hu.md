# 8. fejezet · Modell-utóképzés

> Négy rész—pre-tréning, Mid-training, SFT és RL: hosszúkontextus-tanterv és adatépítés, SFT-protokoll, RL-környezet és jutalom, mintahatékonyság egy- és többmenetes ágenseknél.

← [Vissza a magyar főoldalhoz](../docs/hu/README.md) · 📖 [A fejezet olvasása](../book-hu/chapter8.md)

## Hogyan olvassuk a kísérleteket?

A törzsszöveg rövid mechanizmus-skeletonokkal magyarázza a vezérlési folyamatot; a kísérleti könyvtárakban találhatók a teljes SDK-adapterek, naplók, tesztek és átvételi bizonyítékok. Nem kell minden fájlt sorról sorra elolvasni.

- **Starter:** Kezdje a céllal, a minimális paranccsal és az átvételi feltételekkel; induljon innen: [cot-distillation](cot-distillation/);
- **Builder:** Kövesse a belépési pontot, a fő ciklust, az állapot-/üzenetsémát, az eszközöket és az ellenőrzőt.
- **Maintainer:** Végül olvassa el a teszteket, a bizonyíték-manifeszteket, a hibakezelést, a visszaállítási útvonalakat és a provider-adaptereket.

Első olvasáskor átugorható a hitelesítő adatok betöltése, a megjelenítési réteg és a provider-kompatibilitás; a számok reprodukálásakor térjen vissza.

## Kapcsolódó projektek

| Kísérlet | Projekt | Típus | Leírás |
| :--: | --- | :--: | --- |
| 8-1, 8-2 | [learning-from-experience](../chapter1/learning-from-experience/) | ✅ | Azonos kincskereső környezetben hasonlítja össze a Q-learninget és az LLM-alapú tanulást. |
| 8-3 | [MiniMind-pretrain](MiniMind-pretrain/) · `MiniMind-pretrain/minimind/` | 📖 | Egy kis LLM nulláról történő előképzésének folyamatát mutatja be. |
| 8-4 | [MiniMind-pretrain](MiniMind-pretrain/) · `MiniMind-pretrain/minimind-v/` | 📖 | Egy kis látás-nyelvi modell előképzését és SFT-jét ismerteti. |
| 8-5 | [continued-pretraining](continued-pretraining/) | ✅ | Tartományspecifikus adatokon folytatja az előképzést. |
| 8-6 | [sesame](sesame/) · [orpheus](orpheus/) | 🚧 | Két beszéd-SFT útvonalat vizsgál paralingvisztikai címkékhez és mondatok közötti hangszínkonzisztenciához. |
| 8-7 | [MultilingualReasoning](MultilingualReasoning/) | 🚧 | Több nyelven tanítja a modell következtetési képességét. |
| 8-8 | [prompt-distillation](../chapter8/prompt-distillation/) | ✅ | Tanáradatot készít, diákmodellt képez, majd minőséget és költséget hasonlít össze. |
| 8-9 | [cot-distillation](cot-distillation/) | 🚧 | Helyes CoT-nyomvonalakat szűr, és SFT-adattá alakítja őket. |
| 8-10 | [AdaptThink](AdaptThink/) · `AdaptThink-original/` | 📖 | A feladat nehézsége alapján tanítja meg a modellt a Thinking és NoThinking mód közötti választásra. |
| 8-11 | `SFTvsRL/` | 📖 | Azonos költségkeret mellett hasonlítja össze az SFT memorizálását és az RL általánosítását. |
| 8-12 | [SpatialReasoning](SpatialReasoning/) · `SFTvsRL/` | 📖 | Belső és eloszláson kívüli térbeli következtetést tanít és értékel. |
| 8-13 | [SimpleVLA-RL](SimpleVLA-RL/) · `SimpleVLA-RL/SimpleVLA-RL/` | 📖 | A látást, nyelvet és cselekvést megerősítéses tanulásban kapcsolja össze. |
| 8-14 | [retool](retool/) · `verl/` · `SandboxFusion/` | 📖 | Kódértelmező használatára tanít veRL háttérrendszerrel és végrehajtási sandboxszal. |
| 8-15 | [AWorld-train](AWorld-train/) · `AWorld/` | 📖 | AWorld-alapú GAIA-környezetben tanít eszközhasználó ágenst. |
| 8-16 | [RLVP](RLVP/) · `RLVP/rlvp/` | 📖 | Az RLVP-kutatást reprodukálja: jutalmazza az eredményt, és bünteti az útvonalat. |
| 8-17 | [premature-completion-dpo](premature-completion-dpo/) | ✅ | Korai befejezési bad case DPO-javítása GPU-n. |
| 8-18 | [curly-quote-sft](curly-quote-sft/) | ✅ | Auditált, hatókörérzékeny kínai görbe idézőjel-SFT: 1024/256/256 tanító/holdout/perem eset 10 műfajban és 9 programnyelven; a Qwen3-8B 96,9%/97,7% exact és 100% védett-rész megőrzést ért el GPU-n. |
| 8-19 | [exact-copy-sft](exact-copy-sft/) | ✅ | Auditált bájt-pontos speciális karakterlánc-SFT: 1024/256/256 eset; a Qwen3-8B holdout 78,9%, perem 80,1%, Qwen3/Qwen2.5/Mistral tokenizer-audittal. |
| — | `verl/` | 📖 | Hatékony RLHF-keretrendszer PPO, GRPO, DAPO és további algoritmusok számára. |
| — | [Intuitor](Intuitor/) | ✅ | Hosszú gondolatmenet nélkül tanít intuitív következtetést. |
| — | `tinker-cookbook/` | 📖 | Modellképzési receptek és bevált gyakorlatok gyűjteménye. |

## Projekttípusok

| Ikon | Típus | Jelentés |
| :--: | --- | --- |
| ✅ | **Önálló** | A teljes kód a repository-ban található, és az API-kulcsok beállítása után futtatható. |
| 📖 | **Reprodukciós útmutató** | Külső repository szükséges, amelyet külön kell `git clone` paranccsal letölteni. |
| 🚧 | **Folyamatban** | Az implementáció, a tanítás vagy az elfogadási bizonyíték még nem teljes. |
