# 10. fejezet · Többügynökös együttműködés

> Azt vizsgálja, mikor múlja felül a kollektív intelligencia az egyetlen ágenst: koordinációs minták, kontextusmegosztás és -elszigetelés, hibamódok és ágenstársadalmak.

← [Vissza a magyar főoldalhoz](../docs/hu/README.md) · 📖 [A fejezet olvasása](../book-hu/chapter10.md)

## Kapcsolódó projektek

| Kísérlet | Projekt | Típus | Leírás |
| :--: | --- | :--: | --- |
| 10-1 | [staged-system-prompt](staged-system-prompt/) | ✅ | Egy közös kontextuson belül a feladat szakasza szerint cseréli a rendszerpromptot és az eszközkészletet. |
| 10-2 | [multi-role-transfer](multi-role-transfer/) | ✅ | Közös párbeszédelőzmények mellett mutat be egymásba láncolt szerepátadást. |
| 10-3 | [book-translation](book-translation/) | 🚧 | Könyvfordításban hasonlít össze egy négyszereplős menedzsert és egyetlen ágenst. |
| 10-4 | `use-computer-while-calling/` | 📖 | A TalkAct gyors és lassú ágensekből, megosztott állapotból és kétirányú sorokból álló architektúrája. |
| 10-5 | [autonomous-phone-registration](autonomous-phone-registration/) | 🚧 | Űrlapmegfigyelést, LLM-döntést, telefonhívást és párhuzamos kitöltést kapcsol össze. |
| 10-6 | [parallel-web-research](parallel-web-research/) | ✅ | Párhuzamos böngészőmunkameneteket futtat hibaelszigeteléssel, erőforrás-tisztítással és hivatkozott bizonyítékokkal. |
| 10-7 | `generative_agents/` | 📖 | A Stanford AI Town reprodukciója a külső generative agents repository-ból. |
| 10-8 | [voice-werewolf](voice-werewolf/) | 🚧 | Valódi LLM-felhasználószimulátort ad hozzá, amely csak saját helyének kontextusát látja, eszközt hív, és szintetizált hangon plusz valódi OpenRouter ASR-en át lép a játékba. A szigorú ellenőrzés két hibás korai futást elutasított; a v2 E2E, izoláció, győztes és három ciklus kapui átmentek, de a Falusi tévesen száműzte a Látót, ezért a stratégia megbukott. |

## Projekttípusok

| Ikon | Típus | Jelentés |
| :--: | --- | --- |
| ✅ | **Önálló** | A teljes kód a repository-ban található, és az API-kulcsok beállítása után futtatható. |
| 📖 | **Reprodukciós útmutató** | Külső repository szükséges, amelyet külön kell `git clone` paranccsal letölteni. |
| 🚧 | **Folyamatban** | Az implementáció vagy az elfogadási bizonyíték még nem teljes. |
