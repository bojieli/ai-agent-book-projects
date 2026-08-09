# 8. fejezet · Az ágensek folyamatos evolúciója

> Tapasztalatból fejleszti az ágenst: nyomvonalakat ellenőriz, tudást desztillál, promptokat javít, munkafolyamatokat készít, és ellenőrzött módon módosítja önmagát.

← [Vissza a magyar főoldalhoz](../docs/hu/README.md) · 📖 [A fejezet olvasása](../book-hu/chapter8.md)

## Kapcsolódó projektek

| Kísérlet | Projekt | Típus | Leírás |
| :--: | --- | :--: | --- |
| 8-1 | [trajectory-verifier](trajectory-verifier/) | ✅ | A környezeti eredményeket, folyamatszabályokat és rubrikákat bizonyítékalapú diagnózissá egyesíti. |
| 8-2 | [gaia-experience](gaia-experience/) | ✅ | Sikeres, részben sikeres és sikertelen nyomvonalakból tapasztalati dokumentumot készít. |
| 8-3 | [prompt-auto-optimization](prompt-auto-optimization/) | ✅ | Minimális promptjavítást készít, és határ- valamint megtartási készlettel vezérli a kiadást. |
| 8-4 | Szöveges kísérlet | 🚧 | 8-4. kísérlet: követelménytisztázó Skillt fejleszt a felhasználói visszajelzésekből |
| 8-5 | [browser-use-rpa](browser-use-rpa/) | ✅ | 8-5. kísérlet: böngészőnyomvonalakat fordít reset és visszajátszás segítségével ellenőrzött munkafolyamattá |
| 8-6 | [self-modifying-agent](self-modifying-agent/) | ✅ | 8-6. kísérlet: ismételt hibák után kódjavítást indít, majd regressziót és kiadást végez |
| 8-7 | [harness-safety-gate](harness-safety-gate/) | ✅ | 8-7. kísérlet: magas kockázatú műveletek megerősítési kapuja |
| 8-8 | [hermes-self-evolution](hermes-self-evolution/) | 📖 | 8-8. kísérlet: Hermes megkapja a teljes könyvet és saját forrását, módosítja önmagát |
| 8-9 | [self-evolution-eval](self-evolution-eval/) | ✅ | 8-9. kísérlet: hosszú távon értékeli a tanulást, átvitelt, szabályváltozást és megtartást |

Minden kísérlet kínál offline belépési pontot és API-kulcs nélküli egységtesztet; a valódi modellt vagy böngészőt igénylő útvonalakat az egyes projektek README-je ismerteti.
## Kiegészítő esetek

| Kísérlet | Projekt | Kapcsolat |
| :--: | --- | --- |
| 7-8 | [prompt-distillation](prompt-distillation/) | Prompt蒸馏与参数化学习的跨章项目 |
| — | [self-evolving-tools](self-evolving-tools/) | Alita-style eszköz-felfedezés és újrafelhasználás |
| — | [ai-style-skill](ai-style-skill/) | Kiegészítő írási Skill kísérlet; a fő példa a 2. fejezetben található |


## Projekttípusok

| Ikon | Típus | Jelentés |
| :--: | --- | --- |
| ✅ | **Önálló** | A teljes kód a repository-ban található, és az API-kulcsok beállítása után futtatható. |
| 📖 | **Reprodukciós útmutató** | Külső repository szükséges, amelyet külön kell `git clone` paranccsal letölteni. |
| 🚧 | **Folyamatban** | Az implementáció vagy az elfogadási bizonyíték még nem teljes. |
