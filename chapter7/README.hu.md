# 7. fejezet · Ügynökök kiértékelése

> A teljesítményt összehasonlítható jellé alakítja értékelési környezetekkel, adathalmazokkal, mérőszámokkal, megfigyelhetőséggel és értékelésvezérelt kiválasztással.

← [Vissza a magyar főoldalhoz](../docs/hu/README.md) · 📖 [A fejezet olvasása](../book-hu/chapter7.md)

## Hogyan olvassuk a kísérleteket?

A törzsszöveg rövid mechanizmus-skeletonokkal magyarázza a vezérlési folyamatot; a kísérleti könyvtárakban találhatók a teljes SDK-adapterek, naplók, tesztek és átvételi bizonyítékok. Nem kell minden fájlt sorról sorra elolvasni.

- **Starter:** Kezdje a céllal, a minimális paranccsal és az átvételi feltételekkel; induljon innen: [tau2-bench-eval](tau2-bench-eval/);
- **Builder:** Kövesse a belépési pontot, a fő ciklust, az állapot-/üzenetsémát, az eszközöket és az ellenőrzőt.
- **Maintainer:** Végül olvassa el a teszteket, a bizonyíték-manifeszteket, a hibakezelést, a visszaállítási útvonalakat és a provider-adaptereket.

Első olvasáskor átugorható a hitelesítő adatok betöltése, a megjelenítési réteg és a provider-kompatibilitás; a számok reprodukálásakor térjen vissza.

## Kapcsolódó projektek

| Kísérlet | Projekt | Típus | Leírás |
| :--: | --- | :--: | --- |
| 7-1 | `tau2-bench/` | 📖 | Többkörös, kettős vezérlésű τ²-bench értékelést futtat, és összeveti a τ-bench-csel. |
| 7-2 | `tau2-bench/` | 📖 | Mintafeladatokat old meg kézzel a τ²-bench-ből, és rögzíti a végrehajtási nyomvonalakat. |
| 7-2 | `terminal-bench/` | 📖 | Valós terminálkörnyezetben tesztel teljes, végponttól végpontig tartó feladatokat. |
| 7-2 | `SWE-bench/` | 📖 | Valós GitHub Issue-k tesztelhető javítással történő megoldását értékeli. |
| 7-2 | `GAIA/` | 📖 | Többszintű feladatokon méri a keresést, eszközhasználatot és autonómiát. |
| 7-2 | `OSWorld/` | 📖 | Teljes operációsrendszer-környezetben értékeli a fájl-, alkalmazás- és konfigurációkezelést. |
| 7-2, 7-12 | `android_world/` | 📖 | Androidon méri az alkalmazásnavigációt és a felhasználói felület kezelését. |
| 7-3 | [user-memory-evaluation](../chapter3/user-memory-evaluation/) | ✅ | Többdimenziós memóriaértékelési rubrikát futtat, minden ítélethez bizonyítékkal. |
| 7-4 | [user-memory-system-evaluation](user-memory-system-evaluation/) | ✅ | Azonos esetkészleten hasonlítja össze a JSON Cards, RAG és hibrid rendszereket. |
| 7-5 | [user-memory-policy-eval](user-memory-policy-eval/) | ✅ | Tizenegy hibás trajektória-előtag esetet futtat JSON, Markdown és Python-szerű memóriareprezentációkon, valós OpenRouter-hívásokkal és determinisztikus szabályzat-ellenőrzésekkel. |
| 7-6 | [tts-quality-eval](tts-quality-eval/) | ✅ | Rubrikaalapú multimodális LLM-bíróval hasonlít össze TTS-konfigurációkat. |
| 7-7 | [elo-leaderboard](elo-leaderboard/) | ✅ | Páronkénti összehasonlítások és ELO-pontszám alapján készít ágensranglistát. |
| 7-8 | [model-action-threshold](model-action-threshold/) | ✅ | Azonos, semleges Coding Harness alatt hasonlítja össze a GPT-5.6-sol és a Claude Sonnet 5 átmenetét a feltárástól az első szerkesztésig; mind a 18/18 cella API-hiba nélkül lefutott, a [manifest](model-action-threshold/results/exp7-8-action-threshold-20260731-v1/manifest.json) pedig ellenőrizhető hash-ekkel köti össze a nyomvonalakat és az összesítéseket. |
| 7-9 | [agent-cost-analysis](agent-cost-analysis/) | ✅ | Felbontja a teljes költséget, és méri a cache-barát tervezés és tömörítés megtakarítását. |
| 7-10 | [model-benchmark](model-benchmark/) | 🚧 | TTFT-t, késleltetést, áteresztőképességet, megbízhatóságot és költséget mér; a hosszú kampány még nem teljes. |
| 7-11 | [user-memory-system-evaluation](user-memory-system-evaluation/) | ✅ | A teljes 4×3×2×60 mátrix 1 440/1 440 valós trajektóriát őriz meg hiba és árazatlan használat nélkül, teljes visszakeresési és feladatmetrikákkal, interakcióelemzéssel és sikeres független ellenőrzéssel. |
| 7-12 | [android-world](android-world/) | 📖 | Repository-n belüli T3A-értékelési jelentés és AndroidWorld-hibaelemzés. |
| 7-13 | [openvla-robotwin2-eval](openvla-robotwin2-eval/) | ✅ | Az egy GPU-s hivatalos futás karonként 256 epizódot teljesített: chunk 1 0/256, chunk 25 26/256; mind az 512 rollout hash-e megmaradt. |
| — | [public-health-reporting-eval](public-health-reporting-eval/) | ✅ | Közegészségügyi jelentések eszközhívásait, számításait, hivatkozásait és állításait értékeli. |

> A kódformázással jelölt benchmarkokat külön kell klónozni. Az `android-world/` helyi elemzési jegyzet, nem az `android_world/` benchmark forrása.

## Projekttípusok

| Ikon | Típus | Jelentés |
| :--: | --- | --- |
| ✅ | **Önálló** | A teljes kód a repository-ban található, és az API-kulcsok beállítása után futtatható. |
| 📖 | **Reprodukciós útmutató** | Külső repository szükséges, amelyet külön kell `git clone` paranccsal letölteni. |
| 🚧 | **Folyamatban** | Az implementáció vagy az elfogadási bizonyíték még nem teljes. |
