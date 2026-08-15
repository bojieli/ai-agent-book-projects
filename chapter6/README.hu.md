# 6. fejezet · Interakció: a megfigyelési és a cselekvési tér kiterjesztése

> A szövegtől a beszéd, a grafikus felületek és a fizikai világ felé bővíti az érzékelést és a cselekvést: streamelt beszéd, Computer Use és robotika.

← [Vissza a magyar főoldalhoz](../docs/hu/README.md) · 📖 [A fejezet olvasása](../book-hu/chapter6.md)

## Hogyan olvassuk a kísérleteket?

A törzsszöveg rövid mechanizmus-skeletonokkal magyarázza a vezérlési folyamatot; a kísérleti könyvtárakban találhatók a teljes SDK-adapterek, naplók, tesztek és átvételi bizonyítékok. Nem kell minden fájlt sorról sorra elolvasni.

- **Starter:** Kezdje a céllal, a minimális paranccsal és az átvételi feltételekkel; induljon innen: [live-audio](live-audio/);
- **Builder:** Kövesse a belépési pontot, a fő ciklust, az állapot-/üzenetsémát, az eszközöket és az ellenőrzőt.
- **Maintainer:** Végül olvassa el a teszteket, a bizonyíték-manifeszteket, a hibakezelést, a visszaállítási útvonalakat és a provider-adaptereket.

Első olvasáskor átugorható a hitelesítő adatok betöltése, a megjelenítési réteg és a provider-kompatibilitás; a számok reprodukálásakor térjen vissza.

## Kapcsolódó projektek

| Kísérlet | Projekt | Típus | Leírás |
| :--: | --- | :--: | --- |
| 6-1 | [agent-with-event-trigger](agent-with-event-trigger/) | ✅ | Több eseményforrást kezelő, FastAPI-alapú eseményvezérelt ágenst épít. |
| 6-2 | [async-agent](async-agent/) | ✅ | Eseménysort, prioritásokat, párhuzamos eszközöket, megszakítást, törlést és feladatállapotot valósít meg. |
| 6-3 | [live-audio](live-audio/) | ✅ | Valós idejű hangbeszélgetési demó, amely STT-t, AI-párbeszédet és TTS-t kapcsol össze. |
| Add-on | [phone-agent](phone-agent/) | 🚧 | A Pine Voice útvonalai elkészültek, de engedélyezett PSTN-hívás még nem futott. |
| 6-4 | [streaming-speech](streaming-speech/) | ✅ | Bemutatja a streamelt beszédfelismerés késleltetési és pontossági kompromisszumát. |
| 6-5 | [end-to-end-speech](end-to-end-speech/) | ✅ | A rögzített revisionű MiniCPM-o 4.5 helyben futott egy RTX PRO 6000 GPU-n; az end-to-end és self-cascade egyaránt 3/4 lett, egymást kiegészítő szemantikai/paralingvisztikai hibákkal és valódi 24kHz-es hangbizonyítékkal. |
| 6-6 | [controllable-tts](controllable-tts/) | 🚧 | Fish Audio referencia-könyvtárat és média-összehasonlítást készít; a hallgatási értékelés még hiányos. |
| 6-7 | `claude-quickstarts/computer-use-demo/` | 📖 | Az Anthropic hivatalos Computer Use demója konténerizált Ubuntu asztalon. |
| 6-8 | `browser-use/` | 📖 | Vizuális böngésző-automatizálás művelet- és képernyőkép-nyomvonalakkal. |
| 6-9 | [xlerobot-teleoperation](xlerobot-teleoperation/) | 📖 | Valós XLeRobot távvezérlése ugyanazon asztalrendezési feladathoz: a piros csésze a tálcába, a sárga papír a hulladékgyűjtőbe kerül, majd az állapotot újra megfigyeljük és ellenőrizzük. |
| 6-10 | [gemini-xlerobot-navigation](gemini-xlerobot-navigation/) | 📖 | Ugyanennek a feladatnak az ideális vezérlési felső határa szimulátorban; ez nem jelenti a valódi robot futtatását. |
| 6-11 | [gemini-xlerobot-navigation](gemini-xlerobot-navigation/) | 📖 | A Gemini Robotics-ER 1.5 önállóan vezérli a valós XLeRobotot ugyanazon asztalrendezési feladaton. |
| 6-12 | [gemini-xlerobot-navigation](gemini-xlerobot-navigation/) | 📖 | Nyílt hurkú, lépésenként ellenőrző és prediktív zárt hurkú stratégia összehasonlítása szimulátorban. |
| 6-13 | [rgb-sim2real-grasping](rgb-sim2real-grasping/) | 📖 | RGB-környezetközi teszt ugyanazon feladaton, eltérő háttérrel, tárgymegjelenéssel, megvilágítással és zajjal. |

## Projekttípusok

| Ikon | Típus | Jelentés |
| :--: | --- | --- |
| ✅ | **Önálló** | A teljes kód a repository-ban található, és az API-kulcsok beállítása után futtatható. |
| 📖 | **Reprodukciós útmutató** | Külső repository vagy meghatározott hardver szükséges. |
| 🚧 | **Folyamatban** | Az implementáció vagy az élő elfogadási bizonyíték még nem teljes. |
