# 5. fejezet · Kódoló ágens és kódgenerálás

> A kód „olyan eszköz, amely új eszközöket hozhat létre”, ezért az általános célú ágensek egyik legfontosabb metaképessége.

← [Vissza a magyar főoldalhoz](../docs/hu/README.md) · 📖 [A fejezet olvasása](../book-hu/chapter5.md)

## Hogyan olvassuk a kísérleteket?

A törzsszöveg rövid mechanizmus-skeletonokkal magyarázza a vezérlési folyamatot; a kísérleti könyvtárakban találhatók a teljes SDK-adapterek, naplók, tesztek és átvételi bizonyítékok. Nem kell minden fájlt sorról sorra elolvasni.

- **Starter:** Kezdje a céllal, a minimális paranccsal és az átvételi feltételekkel; induljon innen: [coding-agent](coding-agent/);
- **Builder:** Kövesse a belépési pontot, a fő ciklust, az állapot-/üzenetsémát, az eszközöket és az ellenőrzőt.
- **Maintainer:** Végül olvassa el a teszteket, a bizonyíték-manifeszteket, a hibakezelést, a visszaállítási útvonalakat és a provider-adaptereket.

Első olvasáskor átugorható a hitelesítő adatok betöltése, a megjelenítési réteg és a provider-kompatibilitás; a számok reprodukálásakor térjen vissza.

## Kapcsolódó projektek

| Kísérlet | Projekt | Típus | Leírás |
| :--: | --- | :--: | --- |
| 5-1 | [provider-failover](provider-failover/) | ✅ | Félbehagyott trajektória átadása másik szolgáltatónak, hat párosítás × három megközelítés: a semleges formátum 6/6 arányban váltott át és mindig helyes végösszeget adott, a szó szerinti átemelés 3/6, a teljes gondolatmenet eltávolítása 4/6; minden hiba a szolgáltató valódi hibaüzenetét őrzi |
| 5-2 | [provider-failover](provider-failover/) | ✅ | Gondolatmenet, szöveg vagy argumentum közben elvágott folyam helyreállítása: a folytatás szövegnél 15–66% kimeneti tokent spórol, csonka argumentumnál viszont érvényes, de jelentésében hibás JSON-t told hozzá; a meta-utasítás minden cellában drágább volt a teljes újraküldésnél |
| 5-3 | [code-for-math](code-for-math/) | ✅ | A tisztán gondolatmenet-alapú megoldást hasonlítja össze a kóddal támogatott számítással. |
| 5-4 | [code-for-logic](code-for-logic/) | ✅ | Logikai feladványokat alakít át korlátkielégítési problémává. |
| 5-5 | [small-model-codified-rules](small-model-codified-rules/) | ✅ | Üzleti szabályokat helyez át kódalapú ellenőrzésbe, hogy a kis modell megbízhatóbban kövesse őket. |
| 5-6 | [paper-to-ppt](paper-to-ppt/) | ✅ | Slidev-prezentációt készít javaslattevő és vizuális felülvizsgáló iteratív együttműködésével. |
| 5-7 | [paper-to-video](paper-to-video/) | ✅ | TTS és ffmpeg segítségével narrált videóvá alakítja a prezentációt. |
| 5-8 | [video-edit](video-edit/) | ✅ | Természetes nyelvű kérés alapján megkeresi és kivágja a megfelelő videójelenetet. |
| 5-9 | [cad-vs-diffusion](cad-vs-diffusion/) | ✅ | Ugyanazon karimaspecifikáció kétútvonalas mérése: a Kimi által írt 17 soros CadQuery minden méretben nulla eltérésű; a Hunyuan3D-2.1 (HF nyilvános Space) mind a 4 átmenő furatot elhagyta, a külső átmérő eltérése −99,4%. M5→M6 módosítás: a kódútvonalon egy paramétersor átírása, 0 LLM-hívás, a többi méret nulla driftje; a generatív útvonal teljes újrafuttatása mellett a külső átmérő +283%-kal sodródott el, és axiálisan átfordult. A zöldnövény-kontrollcsoport természetességi pontszáma 3 vs 8, az alkalmazhatósági határ megfordul. |
| 5-10 | [adaptive-log-parser](adaptive-log-parser/) | ✅ | Ismeretlen naplóformátum esetén automatikusan új elemzőfüggvényt készít és regisztrál. |
| 5-11 | [log-diagnosis](log-diagnosis/) | ✅ | HTTP-nyomvonalakat diagnosztizál, regressziót játszik vissza, és ellenőrizhető Issue-t hoz létre. |
| 5-12 | [dynamic-form](dynamic-form/) | ✅ | Dinamikus HTML-űrlapot készít a hiányos kérés összes szükséges adatának egyszeri tisztázására. |
| 5-13 | [erp-agent](erp-agent/) | ✅ | SQL-artefaktumot készít ERP-lekérdezésekhez anélkül, hogy a teljes adathalmazt átvezetné az LLM-en. |
| 5-14 | [conversational-ui](conversational-ui/) | ✅ | Természetes nyelv alapján módosít React-felületet, és HMR-rel azonnal alkalmazza a változásokat. |
| 5-15 | [permission-embedded-data-objects](permission-embedded-data-objects/) | ✅ | PostgreSQL-alapú objektumtár, amely a dinamikusan generált alkalmazáskód alatt kényszeríti ki a jogosultságot, az ellenőrzést és a referenciális integritást. |
| 5-16 | [agent-creator](agent-creator/) | ✅ | Egy ellenőrzött referencia alapján, illetve nulláról létrehozott ágenseket hasonlít össze. |

## Projekttípusok

| Ikon | Típus | Jelentés |
| :--: | --- | --- |
| ✅ | **Önálló** | A teljes kód a repository-ban található, és az API-kulcsok beállítása után futtatható. |
| 📖 | **Reprodukciós útmutató** | Külső repository szükséges, amelyet külön kell `git clone` paranccsal letölteni. |
| 🚧 | **Folyamatban** | Az implementáció vagy az elfogadási bizonyíték még nem teljes. |
