# 10. fejezet · Többügynökös együttműködés

> Azt vizsgálja, mikor múlja felül a kollektív intelligencia az egyetlen ágenst: koordinációs minták, kontextusmegosztás és -elszigetelés, hibamódok és ágenstársadalmak.

← [Vissza a magyar főoldalhoz](../docs/hu/README.md) · 📖 [A fejezet olvasása](../book-hu/chapter10.md)

## Hogyan olvassuk a kísérleteket?

A törzsszöveg rövid mechanizmus-skeletonokkal magyarázza a vezérlési folyamatot; a kísérleti könyvtárakban találhatók a teljes SDK-adapterek, naplók, tesztek és átvételi bizonyítékok. Nem kell minden fájlt sorról sorra elolvasni.

- **Starter:** Kezdje a céllal, a minimális paranccsal és az átvételi feltételekkel; induljon innen: [parallel-web-research](parallel-web-research/);
- **Builder:** Kövesse a belépési pontot, a fő ciklust, az állapot-/üzenetsémát, az eszközöket és az ellenőrzőt.
- **Maintainer:** Végül olvassa el a teszteket, a bizonyíték-manifeszteket, a hibakezelést, a visszaállítási útvonalakat és a provider-adaptereket.

Első olvasáskor átugorható a hitelesítő adatok betöltése, a megjelenítési réteg és a provider-kompatibilitás; a számok reprodukálásakor térjen vissza.

## Kapcsolódó projektek

| Kísérlet | Projekt | Típus | Leírás |
| :--: | --- | :--: | --- |
| 10-1 | [multi-role-transfer](multi-role-transfer/) | ✅ | Közös párbeszédelőzmények mellett mutat be egymásba láncolt szerepátadást. |
| 10-2 | [book-translation](book-translation/) | 🚧 | Könyvfordításban hasonlít össze egy négyszereplős menedzsert és egyetlen ágenst. |
| 10-3 | `use-computer-while-calling/` + [autonomous-phone-registration](autonomous-phone-registration/) | 📖 / 🚧 | A TalkAct gyors és lassú ágensekből, megosztott állapotból és kétirányú sorokból álló architektúrája. Űrlapmegfigyelést, LLM-döntést, telefonhívást és párhuzamos kitöltést kapcsol össze. |
| 10-4 | [parallel-web-research](parallel-web-research/) | ✅ | Párhuzamos böngészőmunkameneteket futtat hibaelszigeteléssel, erőforrás-tisztítással és hivatkozott bizonyítékokkal. |
| 10-5 | `generative_agents/` | 📖 | A Stanford AI Town reprodukciója a külső generative agents repository-ból. |
| 10-6 | [voice-werewolf](voice-werewolf/) | 🚧 | Valódi LLM-felhasználószimulátort ad hozzá, amely csak saját helyének kontextusát látja, eszközt hív, és szintetizált hangon plusz valódi OpenRouter ASR-en át lép a játékba. A szigorú ellenőrzés két hibás korai futást elutasított; a v2 E2E, izoláció, győztes és három ciklus kapui átmentek, de a Falusi tévesen száműzte a Látót, ezért a stratégia megbukott. |

## Projekttípusok

| Ikon | Típus | Jelentés |
| :--: | --- | --- |
| ✅ | **Önálló** | A teljes kód a repository-ban található, és az API-kulcsok beállítása után futtatható. |
| 📖 | **Reprodukciós útmutató** | Külső repository szükséges, amelyet külön kell `git clone` paranccsal letölteni. |
| 🚧 | **Folyamatban** | Az implementáció vagy az elfogadási bizonyíték még nem teljes. |
