# 4. fejezet · Eszközök

> Az eszközök az ágens kezei: eszközosztályozás és -tervezés, MCP-protokoll, érzékelési, végrehajtási és együttműködési eszközök, valamint eseményvezérelt aszinkron ágensek.

← [Vissza a magyar főoldalhoz](../docs/hu/README.md) · 📖 [A fejezet olvasása](../book-hu/chapter4.md)

## Kapcsolódó projektek

| Kísérlet | Projekt | Típus | Leírás |
| :--: | --- | :--: | --- |
| 4-1 | [perception-tools](perception-tools/) | ✅ | Webes keresési, multimodális, fájlrendszer- és nyilvánosadat-eszközöket biztosít. |
| 4-2 | [multimodal-agent](multimodal-agent/) | ✅ | Multimodal processing: compare native multimodal, extract-to-text, and tool-based analysis. |
| 4-3 | [execution-tools](execution-tools/) | ✅ | Fájlműveleteket, kódértelmezőt, virtuális terminált és biztonságos végrehajtási mechanizmusokat valósít meg. |
| 4-4 | [collaboration-tools](collaboration-tools/) | ✅ | Böngésző-automatizálást, emberi közreműködést, értesítéseket és időzítőket kínál. |
| 4-5 | [agent-with-event-trigger](agent-with-event-trigger/) | ✅ | Több eseményforrást kezelő, FastAPI-alapú eseményvezérelt ágenst épít. |
| 4-6 | [async-agent](async-agent/) | ✅ | Eseménysort, prioritásokat, párhuzamos eszközöket, megszakítást, törlést és feladatállapotot valósít meg. |
| 4-7 | [active-tool-discovery](active-tool-discovery/) | ✅ | Az összes eszközséma betöltését hasonlítja össze az igény szerinti aktív eszközfelderítéssel. |
| — | [active-tool-selection](active-tool-selection/) | ✅ | A feladat követelményei alapján kiválasztja a legmegfelelőbb eszközkombinációt. |

> A `chapter4/docker-compose.yml` és `chapter4/DOCKER_DEPLOYMENT.md` konténeres telepítési referenciát biztosít az MCP-szerverekhez.

## Projekttípusok

| Ikon | Típus | Jelentés |
| :--: | --- | --- |
| ✅ | **Önálló** | A teljes kód a repository-ban található, és az API-kulcsok beállítása után futtatható. |
| 📖 | **Reprodukciós útmutató** | Külső repository szükséges, amelyet külön kell `git clone` paranccsal letölteni. |
| 🚧 | **Folyamatban** | Az implementáció vagy az elfogadási bizonyíték még nem teljes. |
