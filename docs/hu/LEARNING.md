# Tanulási javaslatok

← [Vissza a magyar főoldalhoz](README.md)

## Alapgondolat: Ágens = LLM + Kontextus + Eszközök

A könyv központi képlete az **Ágens = LLM + Kontextus + Eszközök**. Az 1. fejezet ugyanazt az ágenst három szinten magyarázza: a megvalósítás szintjén ez a képlet, az intuitív szinten „agy + szem + kéz és láb", az akadémiai szinten pedig a stratégia (Policy), a megfigyelési tér (Observation Space) és a cselekvési tér (Action Space) felel meg neki.

| Összetevő | Hasonlat | Feladat |
| :--: | :--: | --- |
| 🧠 **LLM** | Agy | Megértési, következtetési és döntéshozatali képességet biztosít |
| 👁️ **Kontextus** | Szem | Minden információ, amit az ágens az egyes döntési pontokon lát: rendszerprompt, eszközdefiníciók, felhasználói üzenetek, modellválaszok, eszközfuttatási eredmények |
| 🤲 **Eszközök** | Kéz és láb | Érzékelik a környezetet, műveleteket hajtanak végre, és kapcsolatot teremtenek a külvilággal |

Éles környezetben az 1. fejezet ugyanezt a rendszert **Ágens = Model + Harness** formában írja át, ahol a **Harness = kontextuskezelés + eszközinterfészek + korlátok + ellenőrzés + korrekció**. Az utóbbi három pontosan az a különbség, ami egy futó demót elválaszt egy megbízható terméktől.

## Tanulási útvonal

A Bevezetés az alábbi ívet rajzolja fel: **az 1–6. fejezet felépíti az ágensépítés teljes módszertanát, a 7–10. fejezet pedig négy irányból — értékelés, utótanítás, folyamatos evolúció és többágenses együttműködés — tárgyalja a képességek növelését.** Minden fejezethez tartozik egy kulcsfelismerés:

| Rész | Fej. | Témakör | Legfontosabb felismerés |
| --- | :--: | --- | --- |
| **Építés** | 1. | A három összetevő, a ReAct ciklus, orkesztrációs minták (munkafolyamat és autonómia), Harness-mérnökség | A futó demó és a megbízható termék közötti különbség a Harnessben rejlik, nem a modellben |
| | 2. | API-üzenetstruktúra, KV Cache, prompttervezés és prompt injection elleni védekezés, Agent Skills, ágens állapotsor, kontextustömörítés | A könyv legfontosabb fejezete; a kontextus szabja meg a képességek felső határát, és minél stabilabb az előtag, annál nagyobb a gyorsítótár-találat |
| | 3. | A felhasználói memória négy fokozatos stratégiája, a RAG technológiai készlete, a tudás szervezése és keresése, Agentic RAG, multimodális memória | A kontextust egyetlen munkamenetről a munkamenetek között felhalmozódó tudásra terjeszti ki |
| | 4. | Öt eszközkategória (érzékelés / végrehajtás / együttműködés / eseményindítás / felhasználói kommunikáció), MCP, általános tervezési elvek, aktív eszközfelderítés | Az érzékelő eszközök az információmennyiséget, a végrehajtó eszközök a kockázatot szabályozzák; az eszközöket általánosra kell tervezni |
| | 5. | Kódoló ágens és fájlrendszer, az OpenClaw architektúra, a kód mint metaképesség hat iránya | A kód nem pusztán programírás, hanem metaképesség új eszközök futásidejű létrehozására |
| | 6. | Két tengely, modalitás × időzítés: aszinkron és eseményvezérelt működés, beszéd, Computer Use, robotmanipuláció | Mind a négy interakciótípus ugyanazokat a rendszerprimitíveket használja: ébresztés, biztonságos pontok, megszakítás, kiszorítás, gyors/lassú útvonal szétválasztása |
| **Fejlesztés** | 7. | Értékelési környezetek, metrikarendszer, adathalmaz-tervezés, LLM-as-a-Judge, statisztikai szignifikancia, megfigyelhetőség, szimulációs környezetek | Értékelés nélkül nem különíthető el a „tervezésből fakadó javulás" a „véletlen ingadozástól" |
| | 8. | A négy szakasz panorámája, mid-training / SFT / RL, jutalomtervezés, többkörös kreditkiosztás, desztilláció | Az SFT memorizál, az RL általánosít; az adat és a környezet fontosabb az algoritmusnál |
| | 9. | Tanulási jelek (környezeti eredmény / folyamatszabály / LLM Rubric), négy frissítési hordozó — tudás, utasítás, program, paraméter —, valamint fokozatos bevezetés és visszaállítás | A frissítés hordozója attól függ, hogyan fejeződik ki és hogyan ellenőrizhető a képesség |
| | 10. | Osztályozási keret (megosztott vagy elkülönített kontextus × egyenrangú / menedzser / decentralizált), A2A protokoll, hat hibamód, ágenstársadalom | Minden többágenses tervezési döntésnek van egyágenses megfelelője |

## A törzsszöveg és a kísérletek felosztása

A könyv nem egyetlen SDK lépésről lépésre követhető oktatóanyaga. A szövegben szereplő rövid pseudocode és skeleton csak arra válaszol, hogy „hogyan áramlik az állapot, hol lehet megállni, mely jelek vesznek részt az ellenőrzésben"; a fejezetek kísérletei teljes megvalósítást, modell- és környezetadaptereket, teszteket, naplókat és bizonyítékot adnak. Egy kísérlet olvasásakor nem kell minden fájl minden sorát megérteni, és egyetlen kísérlet konkrét API-használatát sem szabad általános architektúrának tekinteni.

Az alábbi három rétegben érdemes olvasni; összetett fejezetnél inkább válassz több mechanizmuskísérletet ugyanabból a rétegből, mintsem hogy egyetlen projektet futtass:

| Réteg | Először olvasd | Egyelőre hagyd ki | Milyen kérdésre válaszol? |
| :--: | --- | --- | --- |
| **Starter** | A projekt README-je: cél, minimális parancs, elfogadási feltételek és a hozzá tartozó szöveges skeleton | hitelesítő adatok, UI, szolgáltatói adapterek és hosszú nyers naplók | Melyik mechanizmust hivatott bemutatni ez a kísérlet? |
| **Builder** | belépési pont, magciklus, állapot-/üzenetséma, eszközök és ellenőrző | a mechanizmustól független kompatibilitási/deploy rétegek | Melyik változó változtatta meg a viselkedést? |
| **Maintainer** | tesztek, hibakezelés, bizonyítékformátum, manifest/hash és visszaállítási útvonal | csak a kísérlet módosításakor szükséges külső részletek | Reprodukálható az eredmény, és őszintén vannak rögzítve a hibák? |

Minden fejezet README-je megjelöli a saját Starter belépési pontját. Az ajánlott első kör: 1. fej. `context`, 2. fej. `context-compression`, 3. fej. `user-memory`, 4. fej. `execution-tools`, 5. fej. `coding-agent`, 6. fej. `live-audio`, 7. fej. `tau2-bench-eval`, 8. fej. `cot-distillation`, 9. fej. `trajectory-verifier`, 10. fej. `parallel-web-research`. Az egyes könyvtárak Code mapje jelöli a Run first, Core behavior és Verifier részeket, valamint azt, amit első olvasásra ki lehet hagyni.

## Nehézségi szintek

| Szint | Fej. | Kinek ajánlott? |
| --- | :--: | --- |
| 🟢 Kezdő | 1–2. | Kezdőknek; elég hozzá a Python alapszintű ismerete és némi LLM-használati tapasztalat |
| 🔵 Középhaladó | 3–4. | Programozási alapokkal rendelkezőknek; keresőrendszerek és eszközintegráció |
| 🟣 Haladó | 5–6. | Erős programozási készség és összetett rendszertervezés; a 6. fejezethez ajánlott a HTTP/WebSocket ismerete |
| 🟡 Mérnöki | 7. | Értékelési infrastruktúra és statisztikai módszerek — sok mérnöki munka, kevés matematika |
| 🔴 Szakértő | 8. | A könyv egyetlen fejezete, amelyhez gépi tanulási és modellképzési tapasztalat kell |
| 🟠 Alkalmazott | 9–10. | Az előzőeket összeépítve folyamatos evolúciós hurkot és többágenses rendszert épít |

A törzsszöveg kísérletei és kérdései külön csillagos nehézségi jelölést kapnak: ★ bevezető szint, minden olvasónak; ★★ közepes, némi mérnöki gyakorlatot igényel; ★★★ haladó kihívás, jellemzően nyitott kérdés vagy összetett rendszertervezés.

## Gyakorlati tanácsok

| # | Tanács | Magyarázat |
| :--: | --- | --- |
| 1 | 🛠️ **Gyakorolj közvetlenül** | Minden projekt önállóan futtatható; futtasd és módosítsd magad a kódot |
| 2 | 📚 **Olvasd együtt a kézirattal** | A projektek kipróbálása közben olvasd el a megfelelő fejezetet a [`book-hu/`](../../book-hu/) könyvtárban |
| 3 | 🔬 **Hasonlítsd össze a kísérleteket** | Ablációs és összehasonlító vizsgálatokkal értsd meg az egyes összetevők hatását |
| 4 | 🪜 **Haladj fokozatosan** | Kezdd az egyszerű projektekkel, majd lépj tovább az összetettebb rendszerekre |
| 5 | 🔌 **Figyelj a protokollokra** | A 4. fejezet MCP-eszközprojektjei megmutatják, miért fontos a szabványosított eszközprotokoll a bővíthető ágensekhez |
