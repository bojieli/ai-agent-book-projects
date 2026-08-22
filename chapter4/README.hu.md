# 4. fejezet · Eszközök

> Az eszközök az ágens kezei: eszközosztályozás és -tervezés, MCP-protokoll, érzékelési, végrehajtási és együttműködési eszközök, valamint eseményvezérelt aszinkron ágensek.

← [Vissza a magyar főoldalhoz](../docs/hu/README.md) · 📖 [A fejezet olvasása](../book-hu/chapter4.md)

## Hogyan olvassuk a kísérleteket?

A törzsszöveg rövid mechanizmus-skeletonokkal magyarázza a vezérlési folyamatot; a kísérleti könyvtárakban találhatók a teljes SDK-adapterek, naplók, tesztek és átvételi bizonyítékok. Nem kell minden fájlt sorról sorra elolvasni.

- **Starter:** Kezdje a céllal, a minimális paranccsal és az átvételi feltételekkel; induljon innen: [execution-tools](execution-tools/);
- **Builder:** Kövesse a belépési pontot, a fő ciklust, az állapot-/üzenetsémát, az eszközöket és az ellenőrzőt.
- **Maintainer:** Végül olvassa el a teszteket, a bizonyíték-manifeszteket, a hibakezelést, a visszaállítási útvonalakat és a provider-adaptereket.

Első olvasáskor átugorható a hitelesítő adatok betöltése, a megjelenítési réteg és a provider-kompatibilitás; a számok reprodukálásakor térjen vissza.

## Kapcsolódó projektek

| Kísérlet | Projekt | Típus | Leírás |
| :--: | --- | :--: | --- |
| 4-1 | [perception-tools](perception-tools/) | ✅ | Webes keresési, multimodális, fájlrendszer- és nyilvánosadat-eszközöket biztosít. |
| 4-2 | [multimodal-agent](multimodal-agent/) | ✅ | Multimodal processing: compare native multimodal, extract-to-text, and tool-based analysis. |
| 4-3 | [execution-tools](execution-tools/) | ✅ | Fájlműveleteket, kódértelmezőt, virtuális terminált és biztonságos végrehajtási mechanizmusokat valósít meg. |
| 4-4 | [collaboration-tools](collaboration-tools/) | ✅ | Böngésző-automatizálást, emberi közreműködést, értesítéseket és időzítőket kínál. |
| 4-5 | [active-tool-discovery](active-tool-discovery/) | ✅ | Az összes eszközséma betöltését hasonlítja össze az igény szerinti aktív eszközfelderítéssel. |
| — | [active-tool-selection](active-tool-selection/) | ✅ | A feladat követelményei alapján kiválasztja a legmegfelelőbb eszközkombinációt. |

> A `chapter4/docker-compose.yml` és `chapter4/DOCKER_DEPLOYMENT.md` konténeres telepítési referenciát biztosít az MCP-szerverekhez.

## Projekttípusok

| Ikon | Típus | Jelentés |
| :--: | --- | --- |
| ✅ | **Önálló** | A teljes kód a repository-ban található, és az API-kulcsok beállítása után futtatható. |
| 📖 | **Reprodukciós útmutató** | Külső repository szükséges, amelyet külön kell `git clone` paranccsal letölteni. |
| 🚧 | **Folyamatban** | Az implementáció vagy az elfogadási bizonyíték még nem teljes. |
