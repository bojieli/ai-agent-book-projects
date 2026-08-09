# 8. fejezet · Az ágensek folyamatos evolúciója

> Tapasztalatból fejleszti az ágenst: nyomvonalakat ellenőriz, tudást desztillál, promptokat javít, munkafolyamatokat készít, és ellenőrzött módon módosítja önmagát.

← [Vissza a magyar főoldalhoz](../docs/hu/README.md) · 📖 [A fejezet olvasása](../book-hu/chapter8.md)

## Kapcsolódó projektek

| Kísérlet | Projekt | Típus | Leírás |
| :--: | --- | :--: | --- |
| 8-1 | [trajectory-verifier](trajectory-verifier/) | ✅ | A környezeti eredményeket, folyamatszabályokat és rubrikákat bizonyítékalapú diagnózissá egyesíti. |
| 8-2 | [gaia-experience](gaia-experience/) | ✅ | Sikeres, részben sikeres és sikertelen nyomvonalakból tapasztalati dokumentumot készít. |
| 8-3 | [prompt-auto-optimization](prompt-auto-optimization/) | ✅ | Minimális promptjavítást készít, és határ- valamint megtartási készlettel vezérli a kiadást. |
| 8-4 | [browser-use-rpa](browser-use-rpa/) | ✅ | Böngészőnyomvonalakat fordít reset és visszajátszás segítségével ellenőrzött munkafolyamattá. |
| 8-5 | [self-modifying-agent](self-modifying-agent/) | ✅ | Ismételt hibák után kódjavítást indít, majd regressziót, canary kiadást és visszaállítást végez. |
| 8-6 | [hermes-self-evolution](hermes-self-evolution/) | 📖 | Hermes megkapja a teljes könyvet és saját forrását, választ egy javítást, módosítja önmagát, és minden Reviewer-elutasításból új tanulási kört indít az elfogadásig. |
| 8-7 | [self-evolution-eval](self-evolution-eval/) | ✅ | A 8-7. kísérlet hosszú távon értékeli a tanulást, átvitelt, szabályváltozást és megtartást. |
| 8-8 | [harness-safety-gate](harness-safety-gate/) | ✅ | Magas kockázatú műveletek megerősítési kapuja |
| 8-9 | [ai-style-skill](ai-style-skill/) | ✅ | Az írási visszajelzést ellenőrizhető Skill-lé alakítja; a fejezet a görbe idézőjeles Skillt auditált szintetikus adattal és utóhangolással kapcsolja össze, a pontos másolás tokenizer/Harness hibáit pedig külön kezeli |

Minden kísérlet kínál offline belépési pontot és API-kulcs nélküli egységtesztet; a valódi modellt vagy böngészőt igénylő útvonalakat az egyes projektek README-je ismerteti.

## Projekttípusok

| Ikon | Típus | Jelentés |
| :--: | --- | --- |
| ✅ | **Önálló** | A teljes kód a repository-ban található, és az API-kulcsok beállítása után futtatható. |
| 📖 | **Reprodukciós útmutató** | Külső repository szükséges, amelyet külön kell `git clone` paranccsal letölteni. |
| 🚧 | **Folyamatban** | Az implementáció vagy az elfogadási bizonyíték még nem teljes. |
