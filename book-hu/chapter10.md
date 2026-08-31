# Többügynökös Együttműködés

Az első kilenc fejezet egyetlen Ágensre összpontosított: előbb felépítette annak kontextusát, tudását, eszközeit és interakciós képességeit, majd értékeléssel, utótanítással és folyamatos fejlődéssel tette hosszú távon jobbá. Ez a fejezet a „Hogyan építsünk és fejlesszünk egy Ágenst?” kérdést a „Hogyan szervezzünk meg több Ágenst?” kérdéssé bővíti — hogy a munkamegosztás, a kommunikáció és a kölcsönös ellenőrzés révén olyan feladatokat is elvégezzenek, amelyeket egyetlen Ágens nehezen tudna egyedül vállalni.

Az OpenAI egykor egy ötszintű MI-képességi skálát javasolt: 1. szint, Társalgók; 2. szint, Érvelők; 3. szint, Ügynökök; 4. szint, Innovátorok; és 5. szint, Szervezetek. A többügynökös együttműködést gyakran az 5. szinthez vezető egyik útvonalként mutatják be. Itt azonban a "Szervezetek" egy képességi szintet jelöl – olyan MI-t, amely egy egész szervezet munkáját el tudja végezni –, nem pedig architekturális követelményt. Egy kellően erős egyetlen Ügynök elvileg szintén elérheti ezt. A mai mérnöki valóságban azonban egyetlen Ügynök továbbra is korlátozott a modell képességei és a kontextusablak mérete által.

Több Ügynök együttműködésre bírása messze túlmutat azon, hogy különböző szaktudással rendelkező specialisták "fedezzék egymás hiányosságait". Az alapvetőbb szempont a következő: "egy csoport intelligenciája meghaladhatja bármely egyénéét." Az emberi civilizáció a bizonyíték – egyetlen ember értelme korlátozott, mégis a munkamegosztáson, együttműködésen, vitán és a tudás generációkon átívelő felhalmozásán keresztül az emberi társadalom egésze olyan intelligenciát mutat, amely messze túlszárnyal bármely egyes zsenit. Az Ügynökcsoportok ugyanilyen kollektív intelligenciát hozhatnak létre: még ha minden Ügynök csak annyira képes is, mint egy emberi szakértő, egy jól szervezett csoport felülmúlhatja az összes emberi szakértő együttes képességeit. A *From AGI to ASI* című művében a Google DeepMind a "nagyméretű többügynökös kollektívákat" a szuperintelligencia (ASI) felé vezető egyik kulcsfontosságú útvonalként sorolja fel – ahogy az emberi általános intelligencia társadalmakká és szervezetekké aggregálódik, amelyek túlmutatnak az egyéneken, úgy sok AGI-szintű Ügynök együttműködéséből származó kollektív intelligencia is olyan kognitív képességeket mutathat, amelyek messze túlmutatnak tagjai puszta összegén[^agi-asi]. A többügynökös együttműködés tehát nem csupán egy mérnöki kerülőút egyetlen modell kontextusablak- és képességkorlátai körül – hanem alapvető út lehet a "szakértő-szintű MI"-től az "emberiség egészének felülmúlásáig".

[^agi-asi]: A "nagyméretű többügynökös kollektívákról" mint az AGI-tól az ASI-ig vezető kulcsfontosságú útvonalról lásd: Google DeepMind, *From AGI to ASI.* arXiv:2606.12683, 2026.

## A Többügynökös Együttműködés Osztályozási Keretrendszere

Egy többügynökös rendszer felépítése két alapvető tervezési dimenzióval kezdődik, amelyek együtt meghatározzák annak alapvető architektúráját és megvalósítását.

### 1. Dimenzió: Megosztott vs. Nem Megosztott Kontextus

Ez a legalapvetőbb architekturális döntés, amely meghatározza, hogyan áramlik az információ több Ügynök között.

**Megosztott kontextus** azt jelenti, hogy egy következő Ügynök megkapja az előző Ügynök teljes beszélgetési előzményét és trajektóriáját (az 1. fejezetben meghatározottak szerint). Amikor a rendszerprompt és az eszközkészlet minden szakaszban változik, a rendszer az új szakaszt másik Ügynökként kezeli, mert az identitása, felelősségei és képességei megváltoztak, még ha megtartja is az előző összes memóriáját. Például miután egy követelményelemző megír egy követelménydokumentumot, a fejlesztő nemcsak a dokumentumot kapja meg, hanem az elemző és a felhasználó közötti kommunikáció teljes rekordját is. A fejlesztő új szerepet vesz fel, miközben megtartja az összes korábbi kontextust. Az előnye, hogy semmilyen információ nem vész el; minden Ügynök áttekintheti bármely korábbi szakasz részleteit. A kihívás az, hogy a kontextus gyorsan bővülhet.

**Nem megosztott kontextus** azt jelenti, hogy minden Ügynök független kontextust és beszélgetési előzményt tart fenn, és nem férhet hozzá közvetlenül a másik Ügynök munkanyomaihoz. Ez olyan, mint a különböző osztályok közötti együttműködés: mindenki önállóan dolgozik a saját asztalánál, információt megosztott dokumentumokon és értekezleti jegyzőkönyveken keresztül cserélve, ahelyett, hogy folyamatosan egymás képernyőjét nézné. Ez a modell jobb modularitást és elszigeteltséget kínál; minden Ügynöknek csak a saját felelősségi köréhez kapcsolódó információkra kell összpontosítania. A rendszer könnyebben bővíthető és karbantartható is – egy új Ügynök hozzáadása nem igényli a meglévő Ügynökök belső logikájának módosítását, csak az interfészek és adatformátumok meghatározását.

Mivel az Ügynökök nem osztanak meg kontextust, az információt explicit kommunikációs mechanizmusokon keresztül kell átadni. A klasszikus elosztott rendszerek ezt a kérdést már régen eldöntötték: az operációs rendszerekről szóló tankönyvek szerint a folyamatok közötti kommunikáció (IPC) végső soron csak két paradigmában létezik – "megosztott memória" (az egyik fél ír, a másik ugyanazt a tárterületet olvassa) és "üzenetküldés" (az adatokat explicit módon küldik a másik félnek). Az Ügynökök közötti kommunikációs mechanizmusok ebbe a két paradigmába illeszkednek. Három gyakori módszer létezik:

- **Eszközhívás-paraméterek**: Az alsóbb Ügynök eszközként van becsomagolva, a felsőbb Ügynök pedig a paraméterein keresztül ad át strukturált adatokat; ez olyan forgatókönyvekhez alkalmas, amelyek jól tipizált, egyértelműen strukturált adatokat igényelnek.
- **Megosztott fájlrendszer**: Az Ügynökök köztes termékek (dokumentumok, kód stb.) olvasásával és írásával cserélnek információt egy megosztott könyvtárban, alkalmas nagy méretű fájlokkal rendelkező vagy perzisztenciát igénylő forgatókönyvekhez.
- **Üzenetsor**: Egy dedikált közvetítő, amely üzeneteket továbbít az Ügynökök között. Az Ügynökök nem közvetlenül hívják egymást, hanem üzeneteket küldenek a sornak, amely továbbítja azokat a cél-Ügynöknek.

A két IPC paradigmára leképezve: a megosztott fájlrendszer a "megosztott memóriának" felel meg, míg az eszközhívás-paraméterek és az üzenetsor az "üzenetküldés" formái. Az eszközparaméterek szinkron módon, egy hívással együtt érkeznek; a sorban lévő üzenetek aszinkron módon, egy közvetítőn keresztül kerülnek kézbesítésre. Minden paradigmának megvannak a maga kompromisszumai. A Go-nak van egy széles körben idézett mondása: "Ne megosztott memóriával kommunikálj; ehelyett ossz meg memóriát kommunikációval."

![10-1. ábra: Megosztott kontextus vs. Nem megosztott kontextus](images/fig10-1.svg)

### 2. Dimenzió: Együttműködési Topológia

A második dimenzió az együttműködési topológia: milyen szerkezetben áramlik a vezérlés és az információ az Agentek között. Három tipikus topológia van:

- **Társi Együttműködési Minta**: Egy kis számú Ügynök (jellemzően 2-3) egyenrangú félként lép kapcsolatba, iteratív fejlesztési hurkot alkotva – mint amikor egy ember megír egy tanulmányt, egy másik pedig jegyzetekkel látja el és átdolgozza, és a minőség több kör után messze meghaladja azt, amit egyetlen ember egyedül elérhetne.
- **Menedzser Minta** (Vezénylési Minta): Egy központi Menedzser Ügynök felelős a feladattervezésért és ütemezésért, míg több al-ügynök mindegyike specifikus részfeladatokat kezel – mint egy projektmenedzser, aki több specializált mérnököt irányít egy projekten.
- **Decentralizált Minta**: Nincs futásidejű központi vezérlő; az Ügynökök úgy kommunikálnak egymással, mint az emberek, hogy együttműködjenek a feladatokon.

> **Terminológia: Gráf-mérnökség**. A "Gráf-mérnökség" kifejezés, amely 2026 júliusában vált népszerűvé, a mai Ügynök-kontextusban általában egy végrehajtási gráf explicit tervezésére utal: a csomópontok Ügynökök, hagyományos programok vagy emberi döntések; az élek feladatfüggőségeket, feltételes útválasztást és hibautakat határoznak meg; a strukturált állapot csomópontok között áramlik. Az ebben a fejezetben tárgyalt "együttműködési topológia" ennek az elképzelésnek a többügynökös részhalmaza – a társak közötti együttműködés, a menedzseri vezénylés és a decentralizált átadások különböző gráftopológiák. Mivel az elnevezés még új, és könnyen összetéveszthető a tudásgráfokkal, a GraphRAG-gal és a végrehajtási nyomokkal, ez a könyv továbbra is a stabilabb "együttműködési topológia" és "vezénylés" kifejezéseket használja elsődleges szókészletként.

Az egyes minták részletes tervezését és alkalmazási forgatókönyveit későbbi dedikált alszakaszok tárgyalják.

## Mikor Jobb Valóban a Több Ügynök, Mint az Egyetlen Ügynök?

Mielőtt belemerülnénk a konkrét együttműködési architektúrákba, válaszoljunk egy alapvetőbb kérdésre: **Mikor van valóban szükség több Ügynökre, és mikor elég egy?** A válasz referenciapontként szolgál minden ezt követő mérnöki megközelítéshez. Egy sor közelmúltbeli tanulmány egyértelmű keretrendszerhez konvergál – és a központi kritérium egyetlen kérdés: **Bevezet-e az együttműködés olyan új információt, amelyet egyetlen Ügynök nem tudott megszerezni a válasz előállítása során?**

A 10-1. táblázat megmutatja, mely együttműködési módok vezetnek be új információt, és segít felmérni, hogy a többügynökös együttműködés érdemi értéket kínál-e egyetlen Ügynökhöz képest.

10-1. táblázat: A Többügynökös Együttműködési Módok Információs Nyereségének Összehasonlítása

| Együttműködési Mód | Vezet Be Új Információt? | Hatás |
|---------------------------------------|---------------------|-----------------------------------|
| Önfelülvizsgálat ugyanazon modell által (saját kimenet újraolvasása) | Nem | Általában hatástalan vagy akár káros |
| Különböző Ügynökök vitáznak ugyanarról a szövegről | Nem | Összehasonlítható egy azonos számítási kapacitású egyetlen Ügynökkel |
| A felülvizsgáló tesztvégrehajtási eredményeket használ a kód felülvizsgálatához | Igen (végrehajtási visszajelzés) | Jelentős javulás |
| A felülvizsgáló renderelt képernyőképeket használ a frontend/PPT kód felülvizsgálatához | Igen (vizuális visszajelzés) | Jelentős javulás |
| A felülvizsgáló külső eszközöket használ tények ellenőrzésére | Igen (eszközvisszajelzés) | Jelentős javulás |

A 2025-ös RLEF tanulmány (Reinforcement Learning from Execution Feedback)[^rlef-2025] megállapította, hogy a modell megerősítéses tanulással történő képzése a kódvégrehajtási visszajelzések használatára az iteratív fejlesztéshez jelentősen jobban teljesített, mint a modell többszörös független mintavételezése. A kulcs az, hogy minden iteráció "valódi végrehajtási eredményeket" (fordítási hibák, teszthibák, futásidejű kivételek) vezet be – olyan információt, amely nem létezett, amikor a modell megírta a kódot. A weboldal-generálási feladatok esetében a 2025-ös WebGen-Agent tanulmány[^webgen-agent-2025] arról számolt be, hogy a többszintű vizuális visszajelzés, amely a képernyőképeket látás-nyelvi modell leírásokkal kombinálta, a Claude 3.5 Sonnet benchmark teljesítményét 26,4%-ról 51,9%-ra javította, majdnem megduplázva azt.

[^rlef-2025]: Gehring, J., et al. *RLEF: Grounding Code LLMs in Execution Feedback with Reinforcement Learning.* arXiv:2410.02089, 2025.
[^webgen-agent-2025]: Lu, Z., et al. *WebGen-Agent: Enhancing Interactive Website Generation with Multi-Level Feedback and Step-Level Reinforcement Learning.* arXiv:2509.22644, 2025.

Ez a keretrendszer segít feloldani egy látszólagos ellentmondást: egyes akadémiai tanulmányok szerint egyetlen Ügynök is elegendő, míg a többügynökös rendszerek a mérnöki gyakorlatban gyakran jobban teljesítenek. A tanulmányok gyakran olyan Ügynököket tesztelnek, amelyek ugyanazt a szöveget vizsgálják és vitatják meg, mint a vitában, míg a hatékony mérnöki rendszerek általában külső visszajelzést adnak hozzá kódvégrehajtásból, vizuális renderelésből vagy eszközökből. Csak az utóbbi vezet be új információt. A később tárgyalt három architektúra – társi együttműködés, vezénylés és decentralizálás – szinte minden hatékony használata ezen a kritériumon keresztül érthető meg.

Az Anthropic 2026-os sérülékenység-keresési kísérlete jó példa erre. Negyvenöt Ügynök egy közös fórumon hangolta össze a keresést, ellenőrizte egymás találatait, a végső döntést pedig egy független döntőbíró Ügynök hozta meg. Az összehangolt raj 27 millió tokenből 266 sérülékenységet talált, míg a független Ügynökök párhuzamos módszere 6,5 millió tokenből csak 21-et. Nyílt keresési térben a kommunikáció lehetővé teszi, hogy a többügynökös rendszer dinamikusan áthelyezze a fókuszt és szakosodjon: a nagyobb tokenkeretért cserébe szélesebb lefedettséget és változatosabb felfedezési útvonalakat kap.[^anthropic-multiagent-2026]

[^anthropic-multiagent-2026]: Anthropic Frontier Red Team, “Patterns and Problems in Emerging Multiagent Systems,” 2026-08-13. https://www.anthropic.com/research/multiagent-systems

**Lépéskeret és Ügynök Teljesítmény.** Egy kapcsolódó kérdés, hogy az Ügynök lépéskerete – az eszközhívások vagy iterációs körök száma, amelyeket felhasználhat – hogyan befolyásolja a teljesítményt. Több lépés bizonyára segíthet: 30 lépéssel egy Ügynöknek csak a core funkcionalitás megvalósítására lehet ideje, míg 300 lépéssel tervezhet, implementálhat, tesztelhet és finomíthat. A 2025-ös Google tanulmány, a *Budget-Aware Tool-Use Enables Effective Agent Scaling* azonban egy ellentmondásos következtetésre jutott: **ha egyszerűen több lépést adunk egy Ügynöknek, az nem garantál jobb teljesítményt.** A szokásos Ügynökök nem rendelkeznek "keret-tudatossággal"; még 300 lépéssel is sekély keresést végeznek, és gyorsan platót érnek el. A további lépések hatékony felhasználásához az Ügynöknek olyan mechanizmusra van szüksége, amely a fennmaradó erőforrásokhoz igazítja a stratégiáját, először széles körben felfedezve, majd később szűkítve a fókuszt. A 2026-os BAVT (Budget-Aware Value Tree Search) megközelítés tovább lépett, bevezetve a lépésszintű értékbecslést, amely a fennmaradó keret arányának megfelelően állítja be a felfedezés és a kiaknázás közötti egyensúlyt. Ahogy a keret csökken, az Ügynök a széles körű felfedezésről a mélyebb vizsgálatra vált.

Ezek az eredmények közvetlen hatással vannak a többügynökös rendszertervezésre. Például a vezénylési mintában a Menedzser Ügynöknek nem szabad egyszerűen szétosztania a feladatokat az al-ügynökök között, és várnia az eredményekre. Ehelyett "dinamikusan kell allokálnia a lépéskereteket" a feladat komplexitása alapján – az egyszerű részfeladatok kevesebb lépést kapnak; a komplex részfeladatok bőséges lépéseket. Emellett irányítania kell az al-ügynököket, hogy bölcsen használják ezeket a kereteket (először tervezzenek, majd implementáljanak, majd teszteljenek, majd fejlesszenek), ahelyett, hogy egyből belevágnának.

Még egy szempontot figyelembe kell venni bármely tervezési döntés előtt: "a költséget." A párhuzamos feltárás és az iteratív finomítás pénzbe kerül – az Anthropic nyilvánosságra hozta, hogy a többügynökös kutatórendszere körülbelül 15-ször annyi tokent fogyaszt, mint egy normál beszélgetés, és a tokenhasználat önmagában magyarázza a teljesítménykülönbség körülbelül 80%-át. A többügynökös rendszer előnyeinek elég nagyoknak kell lenniük ahhoz, hogy igazolják a többszörös, vagy akár egy nagyságrenddel magasabb költségeket; ellenkező esetben egy jól hangolt egyetlen Ügynök általában a jobb üzlet.

## Többügynökös Együttműködés Megosztott Kontextussal

Megosztott kontextusú együttműködésben minden szakasz önálló Agent, saját System Prompttal és eszközkészlettel, de örökli az előző szakasz teljes trajektóriáját. Ennek előnye a veszteségmentes információátadás; a kihívás az, hogy az aktuális Agent a feladatára összpontosítson a felhalmozódó előzmények ellenére.

Összetett feladatokban a szerep és a felelősség szakaszonként jelentősen változhat. Egyetlen statikus prompt vagy túl általános, vagy túl hosszú, ezért a rendszer a szakasznak megfelelően válthatja a promptot és az eszközöket.

A kulcskérdés: a szerepváltás cserélje le a System Promptot, vagy töltsön be Skillt? Mindkettő új viselkedési szabályokat ad, de eltérő költséggel és korlátozással.

| Választás | A szerepszabály hordozója | Látható eszközök | Kontextus/KV Cache hatás | Korlátozás ereje |
|---|---|---|---|---|
| `transfer_to_agent` | Lecseréli a System Promptot és rendszerint az eszközkészletet | Csak az aktuális szerep eszközei | Minden váltás módosítja a prefixet, így a cache az eltérés helyétől általában nem használható újra | Erős: a szerepen kívüli eszközök hiányozhatnak a schema-ból |
| Skill | Fix Skill-katalógus, a `SKILL.md` igény szerint a trajektóriához kerül | Többnyire a teljes katalógus vagy stabil keresési belépő | A statikus prefix változatlan; a Skill a trajektória végére kerül | Gyenge: a Skill utasítás, a kemény jogosultságot a Harness adja |

Ha a szerepek tudásban, folyamatban vagy írásmódban különböznek, a Skill az első választás. Jogosultság, eszközigazolás, megfelelőség vagy tiltott mellékhatás esetén külön Agent vagy `transfer_to_agent` kell, kóddal kikényszerített Harness-szabállyal.

> **10-1. kísérlet ★★: Szerepváltás megosztott kontextusban — System Prompt kontra Skill**
>
> **Közös feladat és változók**: mindkét út ugyanazt a modellt, feladatot, eszközmegvalósítást, szerepszabályt és teljes közös trajektóriát használja. A feladat a kínai újenergiás járművek 2021–2023-as eladásainak megkeresése, a CAGR kiszámítása és legfeljebb 120 kínai karakteres befektetői összefoglaló írása.
>
> **1. út: System Prompt váltása**. Az öt szerep: `triage`, `research`, `coding`, `data_analysis`, `writing`. Minden szerep csak saját eszközeit és a `transfer_to_agent` eszközt látja; átadáskor az előzmény megmarad, a cél szerep promptja és eszközei betöltődnek, majd a futás folytatódik.
>
> **2. út: Skill**. A System Prompt és a teljes eszközkatalógus végig rögzített. A modell meghívja a `load_skill(name)` eszközt, és a beolvasott `SKILL.md` eszközeredményként kerül a közös trajektóriába. A prefix stabil marad, a kemény jogosultságokat pedig a Harness szabályai biztosítják.

## Többügynökös Együttműködés Megosztott Kontextus Nélkül

A megosztott kontextus nélküli architektúrában minden Ügynök független entitásként működik saját kontextussal, trajektóriával és állapottal. Az Ügynökök nem férhetnek hozzá közvetlenül egymás belső kontextusához; az együttműködés kizárólag explicit, strukturált adatátvitelen alapul a fejezet elején bemutatott három kommunikációs mechanizmuson keresztül: eszközhívás-paraméterek, megosztott fájlrendszer és üzenetsor.

Korábban ebben a fejezetben összehasonlítottuk a kommunikációs mechanizmusokat a folyamatok közötti kommunikáció formáival, valamint a megosztott versus elszigetelt kontextust a szálakkal és folyamatokkal. Ez az analógia tovább is vihető (10-2. táblázat):

10-2. táblázat: Megfeleltetés a Többügynökös Rendszerek és az Operációs Rendszerek között

| Operációs Rendszer | Többügynökös Rendszer |
|----------|----------------|
| Program (futtatható fájl) | Statikus előtag (rendszerprompt + eszközdefiníciók) |
| Folyamat memória | Trajektória |
| CPU | LLM |
| Kernel | Ügynök futásidejű környezet |
| Rendszerhívás | Eszközhívás |
| fork (gyermekfolyamat létrehozása) | spawn_subagent |
| kill (jel küldése) | cancel_subagent |
| ps (folyamatok listázása) | list_agents |
| Kilépési kód és wait() | Az al-ügynök által visszaadott strukturált összefoglaló |
| Megosztott memória / üzenetküldés | Megosztott fájlrendszer / üzenetküldés |

Ez az absztrakció nem újdonság: a privát állapot, az aszinkron üzenetek és az új tagok létrehozásának képessége pontosan az 1970-es évek Actor modelljének[^actor-model] alapvető felépítése. Egy többügynökös rendszer ezért az Actor modell LLM-alapú változatának tekinthető, és az operációs rendszerekből és elosztott rendszerekből felhalmozott tudás nagy része közvetlenül alkalmazható.

[^actor-model]: Hewitt, C., Bishop, P., Steiger, R. *A Universal Modular ACTOR Formalism for Artificial Intelligence.* IJCAI 1973.

Ez a folyamat-stílusú izoláció számos gyakorlati mérnöki előnnyel jár: minden Ügynök fejleszthető és tesztelhető függetlenül, új képességek adhatók hozzá a meglévő kód módosítása nélkül, egy meghibásodó Ügynök nem terjeszti automatikusan a hibáit a többire, és több Ügynök hajtható végre egyidejűleg anélkül, hogy versengenének a megosztott kontextusért.

A kontextus megosztásának elmaradása azonban költségekkel is jár. A legnyilvánvalóbb az információ-szinkronizációs probléma: hogyan tartanak fenn az Ügynökök konzisztens megértést a feladat állapotáról? Vajon információ vész el vagy duplikálódik az átvitel során? A hibakeresés is nehezebbé válik – amikor problémák merülnek fel, több Ügynök naplóit kell áttekinteni a teljes végrehajtási folyamat rekonstruálásához. Ezek a problémák kritikus fontosságúvá teszik az interfész specifikációk, adatformátumok és kommunikációs protokollok tervezését.

Az explicit együttműködés megosztott kontextus nélkül két topológiától független infrastruktúrára támaszkodik. Az első a "megosztott fájlrendszer", a perzisztens közeg, amelyen keresztül az Ügynökök egymással és a felhasználóval termékeket cserélnek, ami az együttműködés adatsíkját képezi. A második a "kommunikációs és vezérlési mechanizmus", amely támogatja az üzenetküldést, státuszkérdezést, végrehajtás-megszakítást és erőforrás-ütemezést az Ügynökök között, ami az együttműködés vezérlési síkját képezi. Az alábbi három topológia mindkét alapra épül.

### A Fájlrendszer az Ügynök Szemszögéből

A fejezet elején a "megosztott fájlrendszer" a három kommunikációs mechanizmus egyikeként szerepelt a megosztott kontextus nélküli architektúrákban. Egy valós rendszerben az Ügynök által elért fájlrendszer nem egyetlen tárolórendszer, hanem egy "virtuális fájlrendszer", amelyben a különböző forrású, életciklusú és jogosultságú tárolórendszerek egy könyvtárfa alá vannak csatolva. Az Ügynök egységes `read_file`/`write_file`/`list_dir` interfészeken keresztül éri el őket, míg az alapul szolgáló rétegek lehetnek lokális ideiglenes lemezek, perzisztens objektumtárolók, harmadik féltől származó felhő-meghajtó API-k vagy írásvédett rendszer erőforráscsomagok. A könyvtárfa összetételének – az egyes területek láthatóságának és életciklusának – egyértelmű meghatározása előfeltétele a többügynökös együttműködés tervezésének: a konkurencia-ütközések és információs szivárgások jelentős része abból származik, hogy olyan területek keverednek, amelyeket el kellene különíteni. Ez a könyvtárfa az Ügynök címtartományának felel meg, és a négy területtípus különböző jogosultságú memóriaszegmens: néhány privát és írható, néhány több fél által megosztott, és néhány írásvédett. Az operációs rendszer védelmi filozófiája itt is érvényes: alapértelmezés szerint izolálni, és a megosztást explicit módon deklarálni. Egy érett többügynökös rendszerben a fájlrendszer jellemzően a következő négy területtípusból áll:

Egy érett több-Agentes rendszer fájlrendszere rendszerint az alábbi négyféle területből áll:

**I. Ügynök-Specifikus Munkaterület (Piszkozat).** Minden Ügynök példányhoz tartozó privát könyvtár, amely köztes termékeket, ideiglenes fájlokat, vázlatokat és hibakeresési naplókat tárol. Életciklusa a példányhoz kötődik, és más Ügynökök és felhasználók számára láthatatlan. A piszkozat izolálása két célt szolgál: megakadályozza, hogy több Ügynök ideiglenes fájljai felülírják egymást, és a fő Ügynök kontextusát karcsún tartja – az al-ügynökök próba-hiba folyamata a saját munkaterületükön marad, csak a végső termék kerül a megosztott térbe. Ez a 4. fejezet azon elvének tárolási szintű megfelelője, hogy az al-ügynökök a teljes trajektória helyett strukturált összefoglalókat adnak vissza.

**II. Többügynökös Megosztott Munkaterület.** Egy együttműködési terület, amelyet több Ügynök olvashat és írhat, és amely "a felhasználó számára látható". Ez az elsődleges közege a termékcserének a megosztott kontextus nélküli architektúrákban: a Szójegyzék Ügynök megírja a kifejezéslistát, a Fordítási Ügynök abból olvas; a felhasználók ide tölthetnek fel forrásfájlokat és tölthetnek le végeredményeket. Életciklusa a teljes feladathoz kötődik, és perzisztenciát igényel. Több fél általi egyidejű olvasás és írás területeként a konkurencia-ütközések forró pontja – olyan mechanizmusok, mint az optimista zárolás és a munkafa-izoláció itt működnek, a "Hibamód Egy" alatt ebben a fejezetben részletezve. A 4. fejezetben a `/workspace/shared` kötetcsatolás használata a fő Ügynök, a virtuális számítógép és a virtuális telefon összekapcsolására ennek a rétegnek egy tipikus megvalósítása.

**III. Csatolt Külső Erőforrások.** A felhasználó által engedélyezett harmadik féltől származó információforrások – Google Drive, Notion, Dropbox, vállalati wikik stb. – adaptereken keresztül csatolási pontokra (pl. `/mnt/gdrive`) vannak leképezve a fájlrendszerben. Az Ügynök egy fájl olvasásával éri el a Notion dokumentumot; a mögöttes adapter meghívja a megfelelő API-t. Három jellemző különbözteti meg ezt a réteget a lokális tárolástól, amelyeket explicit módon kell kezelni a tervezés során: "a hozzáférést külső jogosultságok korlátozzák" (a felhasználó jogosultságai a forrásrendszerben határozzák meg az Ügynök láthatóságát), **a késleltetés magasabb és a konzisztencia gyengébb** (minden olvasás hálózati körutat igényel, és a külső változások nem feltétlenül azonnal láthatók, így az adatot végső konzisztensként kell kezelni), és **a hozzáférés elsősorban igény szerinti és írásvédett** (a külső forrásokba való visszaírást óvatosan kell végezni, mivel a hibás írások szennyezhetik a felhasználó valós adatait). Az egységes fájlinterfész azt jelenti, hogy az Ügynöknek nincs szüksége egyedi eszközre minden adatforráshoz, de el is fedi ezeket a teljesítmény- és biztonsági különbségeket. Ezért az írásvédett/írható státuszt, az időtúllépéseket és a hitelesítési határokat explicit módon kell kezelni a csatolási szinten.

**IV. Beépített Rendszer Erőforrások.** A rendszer által előre telepített és minden Ügynökkel írásvédett módon megosztott erőforráscsomag. Tipikus példák a 2. és 4. fejezetben bemutatott "Készségek (Skills)" – fájlként szervezett tudásdokumentumok és szkriptek, amelyek olyan elérési utakra vannak csatolva, mint a `/skills`, progresszív felfedéssel (először index, majd igény szerinti kibontás). További példák közé tartoznak a referencia kézikönyvek, sablonkönyvtárak és megosztott eszközdefiníciók. Ez a réteg globálisan megosztott, írásvédett, munkameneteken át stabil, és minden Ügynök által egyidejűleg olvasható konkurencia-vezérlés nélkül.

A 10-2. ábra szemlélteti, hogyan van ez a négy területtípus egységesen csatolva egyetlen könyvtárfa alá: az Ügynök egységes interfészen keresztül éri el a teljes fát, a felhasználók a megosztott térből töltenek fel és le fájlokat, a külső adatforrások adaptereken keresztül vannak csatolva, és a beépített rendszer erőforrások írásvédettként állnak rendelkezésre.

![10-2. ábra: A négy területtípus csatolási struktúrája az Ügynök Virtuális Fájlrendszerében](images/fig10-2.svg)

A 10-3. táblázat összehasonlítja ezt a négy területtípust négy dimenzió mentén – láthatóság, életciklus, olvasási/írási jogosultságok és konkurencia-vezérlés –, amely a fájlrendszer-elrendezés tervezésének ellenőrző listájaként szolgál.

10-3. táblázat: Az Ügynök Virtuális Fájlrendszerének négy területtípusa

| Terület | Láthatóság | Életciklus | Olvasás/Írás | Konkurencia-vezérlés |
|--------------|-----------------|------------------------|---------------------|-------------------|
| Ügynök-Specifikus Munkaterület | Csak a tulajdonos Ügynök | Megsemmisül az Ügynök példánnyal | Olvasás/Írás | Nem szükséges (privát) |
| Többügynökös Megosztott Munkaterület | Minden együttműködő Ügynök és a felhasználó | A feladat idejére fennmarad | Olvasás/Írás | Szükséges (optimista zárolás / munkafa) |
| Csatolt Külső Erőforrások | Külső engedélyezéstől függ | A külső forrás határozza meg | Többnyire írásvédett, írás óvatosságot igényel | A külső forrás kezeli |
| Beépített Rendszer Erőforrások | Minden Ügynök | Munkameneteken át stabil | Írásvédett | Nem szükséges (írásvédett) |

A „fájl útvonal mint univerzális interfész” értéke abban rejlik, hogy az útvonalat csererendszerré teszi. Akár termékeket cserélnek az Ügynökök, akár egy fő Ügynök ad bemenetet egy al-ügynöknek, akár szervezetek működnek együtt A2A-n keresztül, egy könnyű útvonal karakterláncot adnak át, ahelyett, hogy a fájl tartalmát betöltenék a kontextusablakba (4. fejezet). Ez összhangban van az 5. fejezet "a fájlrendszer mint az Ügynök központja" koncepciójával, amely leírja, hogyan használ egyetlen Ügynök a fájlrendszert a memória és a képességek tárolására. Itt ugyanez az absztrakció több Ügynökre terjed ki: a privát, megosztott, külső és beépített tárolókat csatoló virtuális könyvtárfa biztosítja a többügynökös együttműködés tárolási alapját.

### Kommunikáció és Vezérlés az Ügynökök Között

Míg a fájlrendszer a "termékcsere" problémáját oldja meg az Ügynökök között, az együttműködéshez "vezérlési síkra" is szükség van. Pontosan itt jönnek képbe a 10-2. táblázat életciklus sorai: a 4. fejezetben megadott eszköz primitívek – létrehozás (`spawn_subagent`), üzenetküldés (`send_message_to_subagent`), megszakítás (`cancel_subagent`) és felderítés (`list_agents`) – a fork, message, kill és ps megfelelői a folyamatok világában. Ez a szakasz nem ismétli meg az interfészdefiníciókat, hanem négy gyakran figyelmen kívül hagyott képességre összpontosít, amelyek elengedhetetlenek a többügynökös együttműködéshez.

**I. Üzenetküldés.** A legegyszerűbb forma a pont-pont: A Ügynök közvetlenül meghívja a `send_message_to_agent_B(tartalom)` függvényt. Ez alkalmas fix topológiájú és kis számú Ügynököt tartalmazó forgatókönyvekhez (pl. a 10-3. kísérlet telefon + számítógép kétügynökös beállítása). Amikor az Ügynökök száma növekszik és aszinkron párhuzamosságra van szükség, a pont-pont kapcsolatok száma az Ügynökök számával négyzetesen nő, és a feladónak és a vevőnek egyszerre kell online lennie. Ilyen esetekben "üzenetsort" kell használni (részletesen a "Párhuzamos Koordinációs Minta" alatt ebben a fejezetben): az Ügynökök üzeneteket tesznek közzé a sorban, amely az előfizetések alapján továbbítja azokat, így a feladónak nem kell ismernie az előfizetőket. Akár pont-pont, akár soron keresztül, az üzeneteknek jellemzően strukturált "borítékot" kell hordozniuk: feladó azonosító, cél (specifikus Ügynök vagy broadcast), üzenet típusa (pl. `task_assigned`/`status_update`/`result`/`terminate`) és JSON payload. Az egységes borítékformátum biztosítja a megbízható útválasztást és elemzést a vevő által, és nyomon követhetővé teszi az együttműködési láncot – ez a többügynökös rendszerek hibakeresésének kulcsfontosságú aspektusa.

**II. Státuszkérdés.** Ez a vezérlési sík legalulértékeltebb része. Miután egy fő Ügynök elindított egy al-ügynököt, látnia kell az al-ügynök előrehaladását; különben nem tudja eldönteni, hogy várjon-e tovább, vagy beavatkozzon, amikor az al-ügynök elakad. Egy intuitív megközelítés az RPC-ből kölcsönözni és definiálni egy `get_subagent_status(ügynök_azonosító)` lekérdező interfészt, amely "futó/befejezett/sikertelen" plusz egy százalékos előrehaladást ad vissza. De egy ilyen pull interfész sokkal kevésbé hasznosnak bizonyul, mint vártuk: egy al-ügynök a létrehozás pillanatában elkezd végrehajtódni, és addig fut, amíg be nem fejeződik vagy meg nem hibásodik. Nem megy át a hagyományos kötegelt rendszerekben lévő feladatok sorba állított állapotain, ahogy a Unix programozásban is ritkán van szükség egy másik folyamat PID alapján történő pollozására a futási állapotért. A pollozásnak van egy belső dilemmája is: túl gyakran pollozol, és pazarlod a tokeneket; túl ritkán pollozol, és későn reagálsz. Természetesebb módja a státusz megszerzésének, ha visszatérünk a fejezet elején bemutatott két kommunikációs paradigmához.

**Státusz megszerzése üzenetküldéssel.** A fő Ügynök egyszerűen küld egy üzenetet az al-ügynöknek: "Hogy haladsz?" Az al-ügynök egy alkalmas pillanatban válaszol. Minden aszinkron: az üzenet elküldése nem blokkolja a fő Ügynök saját végrehajtását, és hogy a másik fél mikor – vagy egyáltalán – válaszol, az egy másik kérdés, ahogy egy menedzser is instant üzenetben kérdez rá a beosztottjánál anélkül, hogy elvárná, hogy azonnal mindent félredobjon. Ezzel szemben az al-ügynök is küldhet proaktívan egy üzenetet, amikor mérföldkövet ér el; ha a rendszerben már van üzenetsor, ez egyszerűen egy `status_update` közzététele a sorban (a 10-4. kísérlet "valós idejű monitorozása" ez a forma). Akár explicit módon kérik a státuszt, akár proaktívan jelentik, az üzenetben hordozott státusznak egységes állapotgép szókincset kell használnia (végrehajtás alatt, bemenetre vár, befejezett, sikertelen) – az A2A protokoll később ebben a fejezetben pontosan ilyen állapotkészletre szabványosítja a feladat életciklusát.

**Státusz megszerzése a megosztott fájlrendszeren keresztül.** A leginkább alapos forma a "trajektória perzisztencia": végrehajtás közben az al-ügynök minden trajektória eseményt JSON formátumba szerializál, és hozzáfűzi egy fájlrendszerbeli naplófájlhoz – általában egy fájl munkamenetenként, egy esemény soronként, azaz JSONL. A trajektória, amely az 1. fejezetben van meghatározva, a felhasználói üzenetek, modellválaszok, eszközhívások és eredmények teljes sorozata. A fő Ügynöknek nincs szüksége státuszjelentési protokollra; a fájl közvetlen olvasásával megvizsgálhatja az al-ügynök teljes végrehajtását: melyik eszközt hívja, mi történt a legutóbbi lépésében, és hogy egy ismétlődő sikertelen újrapróbálkozások hurkában ragadt-e. Folyamat szempontjából ez olyan, mintha közvetlenül olvasnánk egy másik folyamat memóriáját. Nem foglalja el az al-ügynök kontextusát, nem függ az al-ügynök együttműködésétől, és a legfinomabb megfigyelési részletességet kínálja.

Az ilyen kimerítő részletesség azonban teher is. Egy trajektória könnyen több tízezer tokenre rúghat, és a fő Ügynöknek a beolvasás után desztillálnia kell, ami időt és tokeneket emészt fel. A legtöbb forgatókönyvben egy "megállapodott előrehaladási fájl" praktikusabb: az al-ügynök indításakor a fő Ügynök utasítja, hogy frissítse a `progress.md` fájlt, ahogy az egyes tételeket befejezi. A fő Ügynök bármikor elolvashatja ezt a könnyű fájlt az előrehaladás felméréséhez. Ez hasonlít ahhoz, amikor két folyamat lefoglal egy kis blokkot a megosztott memóriában egy megállapodott formátummal, a teljes memóriaállapot helyett desztillált előrehaladást téve elérhetővé.

Az előrehaladási fájl az "elakadás érzékelését" is lehetővé teszi. Ha a `progress.md` vagy a trajektória fájl utolsó módosítási ideje nem változott több mint N percig, a rendszer az al-ügynököt inaktívnak tekintheti, és elindíthat egy időtúllépés biztonsági hálót (visszhangozva a 6. fejezet Heartbeat és `monitor_shell` mechanizmusait). Ez megakadályozza, hogy egy elakadt al-ügynök lehúzza az egész rendszert.

A trajektória perzisztencia értéke messze túlmutat a monitorozáson. Emlékezzünk az 1. fejezet következtetésére: "egy Ügynök kontextusa = statikus előtag + trajektória." A statikus előtagot (rendszerprompt, eszközdefiníciók) a kód határozza meg, és az Ügynöknek nincs futásidejű állapota a trajektórián kívül (a munka termékek már a fájlrendszerben élnek) – "a trajektória az Ügynök teljes állapota". A trajektória valós idejű fájlba mentése egyenértékű azzal, hogy mindenkor teljes ellenőrzőpontot tartunk fenn: akár az Ügynök folyamata összeomlik, a gép áramellátása megszakad, vagy a felhasználó aktívan bezárja a munkamenetet, a trajektória fájl újratöltése és a statikus előtag elé illesztése után a végrehajtás onnan folytatódhat, ahol abbamaradt – pontosan így van megvalósítva a Claude Code és Codex CLI kódoló Ügynökök munkamenet-folytatási funkciója. Ez ugyanaz az ötlet, mint az adatbázis előreíró naplója (WAL): minden eseményt először egy csak hozzáfűzésre szánt naplóhoz adunk, és az állapot mindig visszajátszható a naplóból (a 3. fejezet "tény napló + időszakos ellenőrzőpont" memóriaterve ugyanez az ötlet a memóriarendszerekre alkalmazva). Egy többügynökös rendszer számára ez azt jelenti, hogy az al-ügynökök természetüknél fogva "helyreállíthatók, auditálhatók és könnyen átadhatók": a Menedzser újraindíthat egy al-ügynököt az utolsó érvényes állapotából egy összeomlás után, eseményről eseményre visszajátszhatja a trajektóriát a hiba okának lokalizálásához, és akár a trajektóriát a feladattal együtt átadhatja egy másik Ügynöknek a folytatáshoz.

**III. Végrehajtás Megszakítása.** Párhuzamos együttműködésben gyakori forgatókönyv, hogy "az egyik sikerrel jár, a többi feleslegessé válik" – több Ügynök külön-külön keres, és amint egy megtalálja a célt, a többit azonnal le kell állítani (a kaszkád megszakítás a 10-4. kísérletben ebben a fejezetben). Két szintű megszakítás létezik, és a Unix felhasználók felismerik őket a SIGTERM és SIGKILL közötti különbségként. A "szabályos megszakítás" (graceful termination) előnyösebb: a fő Ügynök egy `terminate` jelet küld, az al-ügynök egy biztonságos ponton válaszol az aktuális lépésében, erőforrásokat takarít meg (böngésző munkameneteket zár be, függőben lévő fájlokat ír ki, zárolásokat old fel), egy visszaigazolást (ack) küld, majd kilép. A "kényszerített megszakítás" (forced termination) egy tartalék lehetőség: a folyamat közvetlen megszakítása, csak akkor használatos, ha az al-ügynök nem válaszol a szabályos jelre, azzal az áron, hogy laza erőforrások és befejezetlen írások maradhatnak vissza. Két mérnöki szempontra kell figyelni. Először is, a szabályos megszakításhoz az al-ügynöknek időszakosan ellenőriznie kell a megszakítási jelet a ciklusában (hasonlóan a 6. fejezet megszakítási mechanizmusához); különben nem tudja fogadni a jelet. Másodszor, a kaszkád megszakításnak versenyhelyzete (race condition) van: több al-ügynök szinte egyszerre jelenthet sikert. A fő Ügynöknek zárolást vagy idempotens tervezést kell használnia annak biztosítására, hogy csak egy sikert fogadjon el, és a megszakítási jel egyszer kerüljön kiküldésre. Lásd a versenyhelyzetek tárgyalását a 10-4. kísérletben.

Egy nyitott kérdés marad: miután a fő Ügynök megszakad, mi történik a még futó al-ügynökökkel? A legtisztább mérnöki megközelítés a Go kontextusából kölcsönöz – a megszakítás a létrehozási kapcsolat mentén kaszkádolódik lefelé: ha megszakítasz egy Ügynököt, az összes általa létrehozott al-ügynök is megszakad, megakadályozva, hogy árva gyermek Ügynökök maradjanak hátra. A fenti "az al-ügynök egy biztonságos ponton ellenőrzi a megszakítási jelet" pontosan a Go `ctx.Done()` pollozásának felel meg. Ezzel szemben, ha valóban szükséged van egy hosszan futó háttér Ügynökre, amely különválik a fő Ügynöktől (mint a Unix `nohup`-ja), indítsd el egy új életciklus-fából (ami a `context.Background()`-nak felel meg), explicit módon deklarálva, hogy nem szakad meg a szülőjével együtt.

**IV. Erőforrás-kezelés és Ütemezés.** Az operációs rendszer másik feladata a szűkös erőforrások allokálása. A folyamatok világában a szűkös erőforrások a CPU idő és a memória; az Ügynök világában ezek a tokenek, a pénz és a konkurencia keret – minden lépés, amelyet egy al-ügynök tesz, mindhármat fogyasztja. Ez a felelősség általában a Menedzserre vagy a futásidejű környezetre hárul: állíts be egy lépés- vagy tokenkeretet az al-ügynök indításakor, és állítsd le, ha azt túllépi; adj nehéz feladatokat egy erős modellnek és mechanikus feladatokat egy olcsó modellnek; korlátozd a konkurenciát, hogy több tucat Ügynök ne merítse ki egyszerre az API kvótát; és amikor egy sürgősebb feladat érkezik, szakíts meg egy végrehajtás alatt álló al-ügynököt – ez a megelőzés (preemption). A gyakorlat ezen a területen messze kevésbé érett, mint a CPU ütemezés, de meghatározza egy többügynökös rendszer költségplafonját, és már az architektúra-tervezési szakaszban figyelembe kell venni.

A termékcsere (adatsík) és az üzenetküldés, státuszkérdés, végrehajtás-megszakítás és erőforrás-ütemezés (vezérlési sík) együtt támogatják a kontextust nem megosztó többügynökös rendszereket. Az alábbi három együttműködési topológia végső soron különböző választások – e két síkra építve – arról, hogy kinél van a vezérlés és hogyan áramlik az információ.

Az Ügynökök közötti együttműködési kapcsolatok és vezérlési áramlási jellemzők alapján a megosztott kontextus nélküli együttműködés három fő architektúrára osztható – a társi együttműködési minta, a menedzser minta és a decentralizált minta –, amelyek mindegyike különböző típusú feladatokhoz alkalmas.

### Társi Együttműködési Minta: Kölcsönös Ellenőrzés és Iteratív Fejlesztés

A társi együttműködés jellemzően két-három egyenrangú Ügynököt foglal magában, amelyek több körön át adnak egymásnak visszajelzést. Lehetséges előnye a független nézőpont és a kognitív sokféleség, de a „több példány” nem jelent automatikusan „több gondolkodásmódot”. Ha a modell, a kontextus és a segédstruktúra nagyon hasonló, a különböző Ügynökök gyakran ugyanazt választják, és a helyi hiba rendszerszintű meghibásodássá válhat. A valódi sokféleséget meg kell tervezni: eltérő modellekkel, kontextusokkal, eszközökkel, látható bizonyítékokkal vagy felelősségi körökkel, továbbá azzal, hogy az Ügynökök előbb egymástól függetlenül döntenek, és csak utána összesítik az eredményt.[^anthropic-multiagent-2026]

A menedzser és a decentralizált mintákhoz képest a társi együttműködés sokkal egyszerűbben megvalósítható – definiáld a két Ügynök szerepét, a kommunikációs mechanizmust és az iteráció befejezési feltételét, és máris működő rendszered van. Ideális választás ötletek gyors validálásához és prototípusok építéséhez.

#### Hurok-mérnökség (Loop Engineering)

A társi együttműködés egyik leggyakoribb felhasználási módja az Ügynök gyakorlat egy gyakori hibájának ellensúlyozása: a "korai befejezés" – megállás a munka félbehagyásával. Három jellemző formája van; az alábbi példák Kódoló Ügynököktől és a Pine AI-től származnak, amelyet a Bevezetőben mutattunk be, és amely telefonhívásokat kezdeményez kereskedők és szolgáltatók ügyintézéséhez. Az első a "lusta ál-kész": a munka egy részének elvégzése és az egész befejezettnek nyilvánítása – egy Kódoló Ügynök megírja a kódot, soha nem futtatja a teszteket vagy próbálja ki a telepítést, és "feladat befejezve" jelentést ad; egy felhasználó két feladatot ad a Pine AI-nak, az befejezi az elsőt, elfelejti a másodikat, és vidáman jelenti, hogy "minden rendben." A második a "korai feladás": az egész feladat lehetetlennek nyilvánítása egyetlen elakadt útvonal után – a Pine AI elérheti a kereskedőt telefonon, webes űrlapon vagy e-mailben, de egyetlen elutasított hívás után azt mondja a felhasználónak, hogy "ezt nem lehet megcsinálni", pedig a csatornaváltás és az újrapróbálkozás valószínűleg sikerrel járt volna. A harmadik az "ál-siker": az Ügynök hiszi, hogy a feladat kész, de a hurkot soha nem zárták le ténylegesen – a másik fél szóban beleegyezik a visszatérítésbe telefonon, de a felhasználónak még mindig meg kell erősítenie egy lépést a mobilalkalmazásban; az Ügynök "minden rendben" jelentést ad, a felhasználó soha nem tud a követő akcióról, és a visszatérítés soha nem érkezik meg. Mindhárom forma ugyanarra a kiváltó okra mutat: **amíg nincs ellenőrizve, a "kész" csupán a modell állítása, nem bizonyíték.**

Az állítások bizonyítékokká alakítása pontosan a "Hurok-mérnökség" (Loop Engineering) dolga, az 1. fejezet evolúciós ívének utolsó szakasza: tervezz egy hurkot, amely az Ügynököt futásban tartja – fedezd fel a következő munkát, hajtsd végre, ellenőrizd, rögzítsd az előrehaladást –, és egy ellenőrző, ne maga a modell döntse el, hogy valóban biztonságos-e megállni. Az ember szerepe ennek megfelelően változik "az Ügynököt promptoló operátorból" "a hurkot tervező mérnökké". A kifejezést 2026 júniusában Addy Osmani alkotta meg[^loop-engineering-2026]; Boris Cherny, az Anthropic Claude Code vezetője még tömörebben fogalmazott: "Már nem promptolom Claude-ot. A munkám az, hogy hurkokat írjak." A vita központi következtetése az volt, hogy **a hurok szűk keresztmetszete az ellenőrző, nem a modell**: megbízhatatlan ellenőrzéssel egy gyorsabb hurok csak gyorsabban jelöli be a gyenge kimenetet befejezettként. És ahogy a Bevezető mondja, a gyakorlat az első, az elnevezés jön később. Már jóval azelőtt, hogy a kifejezés elterjedt volna, a vezető Ügynök csapatok – köztük a Pine AI – már használták a "hurok plusz ellenőrzés" módszert a korai befejezés ellen. Az ellenőrzés megszervezésének leghatékonyabb módja az alábbi Javasló-Ellenőrző paradigma.

[^loop-engineering-2026]: Osmani, Addy. "Loop Engineering: Designing Loops that Prompt Coding Agents", 2026. https://addyosmani.com/blog/loop-engineering/

**Konkrét keretrendszer: LoopX.** A LoopX kiemeli a hurkot a modell promptjából és a csevegési előzményekből, és egy tartós, az Ügynök futtatókörnyezetétől független vezérlési síkra helyezi: a cél és a határ megmagyarázza, miért létezik a munka; a kapuk és a teendők meghatározzák, mi történhet most; a bizonyítékok és a kvóta eldöntik, folytatódhat-e; az átadások pedig lehetővé teszik, hogy egy későbbi kör vagy másik Ügynök folytassa. Egy szabályozott végrehajtást világos protokollá tömörít:

```text
LoopX dönt → Ügynök végrehajt → független ellenőrző bizonyít → LoopX véglegesít
```

Az Ügynök továbbra is következtet, eszközöket használ és jelölt eredményeket készít. A LoopX nem helyettesíti az Ügynök futtatókörnyezetét; a körök közötti folytonosságot irányítja. Csak a függetlenül ellenőrzött eredmények frissíthetik a tartós előrehaladást és használhatnak fel kvótát. A sikertelen ellenőrzés javításhoz vagy újratervezéshez vezet, míg az emberi kapuk, várakozási állapotok és költségvetési korlátok már végrehajtás előtt megállítják a hurkot. Ez a határ a Loop Engineering egyik elvét ellenőrizhető rendszerinvariánssá teszi: **a modell javasolhatja, hogy „kész”, de a saját „kész” állítását nem hagyhatja jóvá.** A LoopX v0.4.0 a szabályozott Turn útvonalat még kísérletiként jelöli, ezért itt a „hurok + ellenőrzés + leállási feltételek” konkrét keretrendszereként szerepel, nem pedig az általános feladatminőség javulásának bizonyítékaként.[^loopx-framework]

[^loopx-framework]: LoopX, "The local control plane for long-running AI agent work", v0.4.0, stabil commit: `a893d221db0b8e028997cefc303f7ec9fa7dbe0a`. https://github.com/huangruiteng/loopx/tree/a893d221db0b8e028997cefc303f7ec9fa7dbe0a

**Konkrét keretrendszer: LongHorizon-Harness.** A LongHorizon-Harness és a LoopX egyaránt a Loop Engineering konkrét megvalósítása, de más irányba mutatnak. A LoopX a hosszan futó Ügynök-munka tartós vezérlési síkját célozza; a LongHorizon-Harness a multimodális Computer Use felől indul, és azt kezeli, amikor ugyanaz a feladat GUI-n, CLI-n, több asztali alkalmazáson és többszöri kontextusfrissítésen ível át.

A LongHorizon-Harness a hosszú távú végrehajtást feladatállapot-kezelésként fogalmazza újra, saját hurkát pedig Manage–Execute–Audit (MEA) formában valósítja meg: a Manager az eredeti célból, az igazolt előrehaladásból, a hibabizonyítékokból és a hátralévő munkából állítja elő a következő korlátozott részfeladatot; az Executor teljesen új kontextusban, GUI-n vagy CLI-n keresztül változtatja meg a környezetet; az Auditor pedig csak olvasható módon ellenőrzi a tényleges eredményt. A következő kör feladatállapotába csak az kerül be, ami átment az auditon; a kudarcok pedig megmaradnak a helyreállítás és az újratervezés alapjaként. A végrehajtási backendeket – például a Claude Code-ot és a Codex CLI-t – adapterrétegen keresztül használja újra, ahelyett hogy átírná a bennük futó Ügynök-hurkot.[^longhorizon-implementation]

Ennek az iránynak az értéke abban áll, hogy elválasztja a feladat folytonosságát az egyre növekvő végrehajtási előzményektől: a kontextus frissülhet, a felületi műveletek elbukhatnak, a következő kör mégis a legutóbb igazolt állapotból folytatódik. A cikk – változatlan Qwen 3.7-Plus modell és Claude Code végrehajtási backend mellett, kizárólag a külső hurkot cserélve – arról számol be, hogy a WeaveBench PassRate 51,8%-ról 80,7%-ra, az OSWorld 2.0 bináris teljesítési aránya 2,8%-ról 8,3%-ra, a Terminal-Bench 2.1 sikeraránya pedig 69,7%-ról 77,2%-ra emelkedett. A költség sem állandó: az első két benchmark az alapvonal teljes tokenmennyiségének 2,3-szeresét, illetve kimeneti tokenjeinek 3,6-szeresét fogyasztotta, a Terminal-Bench 2.1 viszont 24%-kal kevesebbet. Éles üzemben ezen felül kezelni kell a külső környezet vagy a felhasználói igények változása miatt elavuló állapotot, és kör-, idő- és költségkeretekkel megakadályozni, hogy a helyreállítási hurok vég nélkül fusson.

**Nyilvános trajektóriák és a kísérletek reprodukálása.** A projekt weboldala több száz futási trajektóriát tesz közzé a WeaveBenchhez, az OSWorld 2.0-hoz és a Terminal-Bench 2.1-hez, így a végrehajtás menete és az egyes szerepek naplói közvetlenül megtekinthetők. Vegyük a WeaveBench `WEB_task_16_webrtc_simulcast_layer_audit` feladatát: egymás mellé tehető az ugyanazt a Qwen 3.7-Plus modellt használó [alapvonal-trajektória](https://lh-harness.pages.dev/traj/tasks/baseline__WEB_task_16_webrtc_simulcast_layer_audit.html) és [MEA-trajektória](https://lh-harness.pages.dev/traj/tasks/lh_harness__WEB_task_16_webrtc_simulcast_layer_audit.html). Az előbbi a Wireshark-interakcióban elakadva újra és újra próbálkozott, pontszáma 0,59; az utóbbi a kudarcokat és a nem teljesült bizonyítékelemeket visszaírta a feladatállapotba, így a további körök már csak a hiányokkal foglalkoztak, pontszáma 0,92. Ez az eset azt mutatja meg, „hogyan válik a kudarc a következő kör bemenetévé”, és nem helyettesíti az összesített statisztikát; a teljes kísérletek környezete, paraméterei és indítószkriptjei a rögzített verziójú [`eval/`](https://github.com/AMAP-ML/LongHorizon-Harness/tree/53bc678ed4170ad4d2e4309f2bfc5c3fb6caf8cb/eval) könyvtárban találhatók.

[^longhorizon-implementation]: LongHorizon-Harness, stabil commit: `53bc678ed4170ad4d2e4309f2bfc5c3fb6caf8cb`. Projekt weboldal és nyilvános trajektóriák: https://lh-harness.pages.dev/#trajectories; cikk: https://arxiv.org/abs/2608.01964; kód: https://github.com/AMAP-ML/LongHorizon-Harness/tree/53bc678ed4170ad4d2e4309f2bfc5c3fb6caf8cb

#### Javasló-Felülvizsgáló (Proposer-Reviewer) paradigma

![10-3. ábra: Javasló-Ellenőrző Hurok](images/fig10-3.svg)

A Javasló-Ellenőrző a kanonikus társi együttműködési paradigma. Az 5. fejezet már tárgyalta a tervezési elveit és gyakorlati alkalmazásait három kísérletben: PPT generálás, videó szerkesztés és napló vizualizáció. A Javasló Ügynök kódot generál, míg az Ellenőrző Ügynök rendereli a végrehajtási eredményeket, kiértékeli azok minőségét egy látás-nyelvi modell segítségével, és strukturált javaslatokat ad a fejlesztésre. A kettő addig iterál, amíg az eredmény meg nem felel a kívánt szabványnak.

Ez a paradigma alkalmazható olyan forgatókönyvekben is, mint a biztonsági felülvizsgálat (Javasló akciótervet generál, Ellenőrző ellenőrzi a megfelelést és a potenciális kockázatokat), a tartalom moderálása (Javasló választ ír, Ellenőrző ellenőrzi az üzleti szabályokat és nyelvi normákat) és a kód felülvizsgálat (Javasló kódot ír, Ellenőrző ellenőrzi a biztonságot és a bevált gyakorlatokat).

**Miért nem tud egyetlen Ügynök generálni, majd felülvizsgálni a saját munkáját?** Pontosan itt alkalmazható a "Mikor Jobb Valóban a Több Ügynök, Mint az Egyetlen Ügynök?" kritériuma a fejezet korábbi részéből – ha a felülvizsgálat nem vezet be új információt, az csak annyi, hogy "újragondoltatjuk a modell válaszával." A kapcsolódó kutatás egyértelmű választ ad. Az ICLR 2024-es "Large Language Models Cannot Self-Correct Reasoning Yet" című tanulmányában Huang és munkatársai azt találták, hogy a GPT-4 arra kérése, hogy vizsgálja felül és javítsa ki saját válaszait külső visszajelzés nélkül, valójában csökkentette a pontosságot – a modell gyakrabban változtatott helyes válaszokat helytelenekké, mint helyteleneket helyesekké.

A javasló–ellenőrző hurok minimális invariánsa a következő: az ellenőrző **független bizonyítékot** olvas, nem pusztán megismétli a javasló magyarázatát, és visszaküldéskor megadható, behatárolható javítási feltételt kell adnia:

```python
candidate = proposer(task, constraints)
evidence = execute_or_render(candidate)       # tests, state, screenshot, facts
review = independent_reviewer(candidate, evidence)

while review.veto and budget_remaining:
    candidate = proposer.repair(candidate, review.findings)
    evidence = execute_or_render(candidate)
    review = independent_reviewer(candidate, evidence)

if review.pass:
    publish(candidate, evidence, review)
else:
    escalate_or_reject(review)
```

Az ellenőrző nem módosíthatja a teszteket, a bizonyítékgyűjtőt vagy a kiadási kaput; különben a „független ellenőrzés” önjóváhagyássá silányul.

Egy 2024-es, a TACL-ben megjelent áttekintő tanulmány, a "When Can LLMs Actually Correct Their Own Mistakes?" (arXiv:2406.01297), tovább erősítette ezt a következtetést: hacsak nem biztosítanak megbízható külső visszajelzést (pl. tesztesetek végrehajtási eredményei, külső eszközök által végzett ellenőrzés kimenete), a modell saját "önjavítására" hagyatkozás nagyrészt hatástalan.

Az ICLR 2024-es CRITIC tanulmány egy szemléletes összehasonlító kísérletet nyújt. A CRITIC során a modell külső eszközöket (keresőmotor, Python interprete) használt saját válaszainak ellenőrzésére, ami jelentős teljesítményjavuláshoz vezetett. Amikor azonban a kísérletvezetők eltávolították az eszköz-ellenőrzési lépést, és csak a modell önértékelését tartották meg, a javulás nagy része eltűnt. Ez azt jelzi, hogy a felülvizsgálat értéke nem "a modell újragondoltatásában" rejlik, hanem **olyan új információ bevezetésében, amely nem állt rendelkezésre a modell generálása során** – teszt eredmények, renderelt képernyőképek, fordítási hibák, külső keresési eredmények.

Az Anthropic 2026-os, hosszú ideig futó alkalmazásfejlesztési kísérlete ezt az elképzelést három Ügynökből álló, tervező–generáló–értékelő architektúrában valósította meg. A tervező termékspecifikációvá bontotta ki a felhasználó kérését; a generáló és az értékelő előbb megállapodott az egyes körök befejezési feltételeiben, majd a generáló megvalósította a feladatot, az értékelő pedig Playwrighttal használta a valódi alkalmazást és hibajelentést készített. Az Ügynökök fájlokon keresztül adták át az állapotot. A kísérlet azt mutatja, hogy ha a feladat meghaladja azt, amit a jelenlegi modell egyedül megbízhatóan el tud végezni, a külső bizonyítékra támaszkodó független ellenőrzés lényegesen magasabb költségért jobb fejlesztési minőséget adhat.[^anthropic-harness-2026]

[^anthropic-harness-2026]: Prithvi Rajasekaran, “Harness Design for Long-Running Application Development,” Anthropic Engineering, 2026-03-24. https://www.anthropic.com/engineering/harness-design-long-running-apps

#### Vita mintázat

Több Ügynök különböző álláspontokat képvisel, és a problématér feltárását ellentétes nézőpontú párbeszéden keresztül végzi. Például egy műszaki megoldás értékelésekor A Ügynök a "támogató" szerepét játssza, felsorolva a megoldás előnyeit és lehetőségeit, míg B Ügynök az "ellenfél" szerepét, rámutatva a kockázatokra és korlátokra. A vita minden köre a másik érveinek cáfolatát vagy kiterjesztését foglalja magában. Amikor egyetlen Ügynök elemez egy problémát, gyakran egy nézőpontot részesít előnyben, és figyelmen kívül hagyja az ellenbizonyítékokat. A strukturált vita arra kényszeríti mindkét álláspontot, hogy teljesen kibontakozzon, segítve a döntéshozókat a kiegyensúlyozottabb ítélet elérésében.

A vita gyakorlati hatékonysága azonban a tudományos közösségben továbbra is vitatott. Tran és Kiela 2026-os tanulmánya[^single-agent-2026] többlépéses érvelési feladatokon hasonlított össze egyetlen Ügynököt öt többügynökös architektúrával: szekvenciális, vita-, együttes, párhuzamos szerep- és részfeladat-párhuzamos rendszerrel. Azt találták, hogy **azonos gondolkodásitoken-keret mellett az egyetlen Ügynök a többügynökös rendszerekkel azonosan vagy akár jobban teljesített**, kivéve, ha a kontextus kihasználása egy bizonyos szint alá romlott. Magyarázatuk az információelmélet adatfeldolgozási egyenlőtlenségére épül: a vitában részt vevő Ügynökök ugyanazt a szöveges információt dolgozzák fel, és a köztes következtetések soros továbbítása csak információvesztést okozhat, újat nem teremthet. Egyes tanulmányokban a vita előnye valószínűleg abból ered, hogy több Ügynök összesen több számítást használ. Az állítás határát fontos pontosítani: a „köztes következtetések több Ügynök közötti soros továbbításából” eredő szűk keresztmetszetre vonatkozik. Nem cáfolja az olyan megközelítéseket, mint **ugyanazon probléma több független mintájának összesítése** – például önkonzisztencia vagy többségi szavazás –, illetve a **generálás és az ellenőrzés eltérő nehézségének** kihasználása, amikor a válasz elkészítése nehéz, az ellenőrzése viszont könnyű. Ezek vagy új, független mintákat adnak a rendszerhez, vagy a feladat aszimmetrikus szerkezetét használják ki, ezért nem esnek az adatfeldolgozási egyenlőtlenség fenti értelmezése alá.

[^single-agent-2026]: Tran, D., Kiela, D. *Single-Agent LLMs Outperform Multi-Agent Systems on Multi-Hop Reasoning Under Equal Thinking Token Budgets.* arXiv:2604.02460, 2026.

#### Ötletbörze mintázat

Több Ügynök egymástól függetlenül állít elő ötleteket, majd megosztják azokat egymással, és kölcsönösen új gondolatokat indítanak el. Egy termékinnovációs feladatban például az első Ügynök közösségi megosztási funkciót javasol; ez a második Ügynököt arra ösztönzi, hogy személyre szabott megosztási posztereket is felvessen; a harmadik pedig a kettőt egyesítve felhasználó által alakítható posztersablonokat és sablonpiacteret javasol. A különböző promptokkal vagy modellekkel eltérő „gondolkodási preferenciák” adhatók az Ügynököknek. Egymást inspirálva tágabb megoldásteret járnak be, és olyan kreatív kombinációkat találhatnak, amelyeket egyetlen Ügynök nehezebben alkotna meg.

#### Szakértői panel mintázat

Minden Ügynök egy meghatározott szakterület nézőpontját képviseli, és közösen tárgyalnak egy több területet érintő problémát. Egy új termék megvalósíthatóságának értékelésekor például a mérnök Ügynök a technikai megvalósítás nehézségét, a termékes Ügynök a felhasználói élmény felől a piaci vonzerőt, az üzemeltetési Ügynök pedig a költségek és erőforrások alapján az üzleti életképességet elemzi. Ezek a szerepek nem egymás ellen dolgoznak, hanem kiegészítik egymást: együtt állítják össze a teljes képet, és tárják fel a szakterületek közötti korlátokat és lehetőségeket.

### Menedzser Minta: Centralizált Vezénylés és Párhuzamos Végrehajtás

Amikor egy feladat sok részfeladatot érint, dinamikus ütemezést kíván, vagy a részfeladatok között bonyolult függőségek vannak, az egyenrangú együttműködés már nem elég, és be kell vezetni a menedzser mintát. A Menedzser Ügynök felelőssége olyan, mint a projektmenedzseré: előbb megérti a teljes feladatot, majd kiosztható részfeladatokra bontja, kiválasztja a megfelelő Ügynököt a végrehajtásra, követi a haladást és kezeli a rendellenességeket (újrapróbálkozás, Ügynökcsere, terv módosítása), végül pedig az egyes Ügynökök kimeneteit végeredménnyé integrálja.

Rendszertervezési szempontból a menedzser minta minden szakosodott Ügynököt olyan eszközként modellez, amelyet a Menedzser meghívhat. A Menedzser eszközkészletében nemcsak a hagyományos külső eszközök (keresés, fájlműveletek) szerepelnek, hanem a többi Ügynök hívási felülete is. A Menedzser az eszközhívás mechanizmusán át indítja el a megfelelő Ügynököt, átadja a feladat paramétereit és a szükséges kontextust, majd a befejezés után átveszi a visszatérési eredményt. A Menedzser nézőpontjából egy Ügynök meghívása és egy közönséges eszköz meghívása között nincs lényegi különbség. Ez az egységes absztrakció adja a menedzser minta jó bővíthetőségét: új képességhez elég a megfelelő Ügynököt megírni és eszközként regisztrálni, a Menedzser központi logikáját nem kell módosítani. Egyúttal természetes módon támogatja a heterogenitást is: a különböző Ügynökök más-más modellt, promptot, eszközkészletet használhatnak, sőt eltérő hardverkörnyezetben is futhatnak.

**A Menedzser Képessége, mint a Rendszer Szűk Keresztmetszete.** A menedzser minta legnagyobb kockázata, hogy a Menedzser képessége a teljes rendszer szűk keresztmetszetévé válik. Ha a Menedzser nem tudja helyesen felbontani a feladatot, vagy ha rossz al-ügynököket választ ki, akkor a legerősebb al-ügynökök sem lesznek hatékonyak. Ezért a Menedzserhez kell rendelni a legerősebb modellt; az al-ügynökök használhatnak gyengébb, olcsóbb modelleket.

A 2025-ös Plan-and-Act tanulmány[^plan-and-act-2025] empirikusan is elemezte ezt a jelenséget. Egy tervező–végrehajtó kétügynökös architektúrában **a gyenge tervező jelenti a teljes rendszer legkritikusabb szűk keresztmetszetét**. Ha a tervezés minősége elég jó, viszonylag egyszerű végrehajtóval is jó eredmény érhető el. Ha viszont a tervező hibásan bontja fel a feladatot, minden későbbi végrehajtói munka téves alapokra épül. A tanulmány 54%-os sikerarányt ért el a WebArena-Lite benchmarkon, és a fő hozzájárulása a tervező képességének javítása volt, nem a végrehajtóé. A tanulság: a legerősebb modellt és a leggondosabban megírt promptot a Menedzserhez – vagyis a tervezőhöz – érdemes rendelni, nem pedig egyenletesen elosztani az erőforrásokat az összes Ügynök között.

A párhuzamos menedzsernek ezen felül az elszámolási pontot „az első **ellenőrzött** sikerként” kell meghatároznia, nem pedig „az elsőként bejelentett sikerként”:

```python
workers = launch_independent_workers(subtasks)
while workers.any_running:
    event = next_event()
    if event.type == RESULT:
        if verify(event.artifact, hidden_checks):
            if not settle_once(event):       # atomically claim the winner
                continue
            broadcast_cancel(to = workers - {event.worker_id})
            await_all_ack_or_timeout()
            return assemble(event.artifact, evidence = event.evidence)
        else:
            record_failure(event)
return summarize_failures(workers)
```

A `settle_once` legyen idempotens (rendszerint zárral vagy tranzakcióval védve); különben két, szinte egyszerre érkező sikeresemény kétszer indítja el az összesítést.

[^plan-and-act-2025]: Erdogan, L. E., et al. *Plan-and-Act: Improving Planning of Agents for Long-Horizon Tasks.* arXiv:2503.09572, 2025.

**Szekvenciális koordinációs forma.**

![10-4. ábra: A Menedzser szekvenciális koordinációja](images/fig10-4.svg)

A Menedzser sorban, egymás után hívja a szakosodott Ügynököket; mindegyik a befejezés után visszaadja az eredményt, és a Menedzser ez alapján dönt a következő lépésről. A vezérlési folyam lineáris, egyszerű és áttekinthető, és jól illik azokhoz a helyzetekhez, ahol a részfeladatok között világos sorrendi függőség van.

> **10-2. kísérlet ★★: Könyvfordító Ügynök**
>
> A könyvfordítás tipikusan olyan összetett feladat, amely több Ügynök együttműködését kívánja. Egy műszaki könyv fordítása nem pusztán szöveg átültetése egyik nyelvről a másikra: gondoskodni kell arról is, hogy a szakkifejezések az egész könyvben egységesek legyenek, a szövegkörnyezet pontos, az olvasás pedig végig gördülékeny. Egy nagy nyelvi modellekről szóló angol könyv fordításakor például rengeteg szakkifejezés tér vissza újra meg újra, gyakran több bevett megfelelővel, és ezeket az egész könyvben egységesíteni kell: ha az 1. fejezetben az `agent` „ügynök”, akkor később nem lehet belőle „proxy”.
>
> Egyetlen Ügynökkel súlyos kontextusgondok támadnának. Ahogy az Ügynök fejezetről fejezetre halad, a kontextus szüntelenül gyűlik: a könyv szójegyzéke, a már lefordított fejezetek, az aktuális bekezdés, a fordítási gondolatmenet, az eszközhívások eredményei. Egy több száz oldalas műszaki könyv a fordítás közti termékekkel együtt könnyen túllépi a kontextusablakot. Ennél is rosszabb, hogy a túl hosszú kontextusban az Ügynök könnyen „eltéved”: elfelejti a korábbi terminológiai megállapodásokat, és a 9. fejezetben a 2. fejezettől eltérő megfelelőt használ; az átnézési szakaszban feleslegesen ellenőriz újra dolgokat; sőt a figyelem szétszóródása miatt hallucinálhat is, és olyan terminológiai szabályokra „emlékezhet”, amelyek soha nem léteztek.
>
> A menedzser minta feladatbontással és felelősség-szétválasztással oldja meg mindezt:
>
> - **Glossary Agent** (szójegyzék-Ügynök): megkapja a könyv egészét, felismeri az ismétlődő szakkifejezéseket, szakszótárakban és fordítási irányelvekben keres, majd strukturált szójegyzéket állít elő (JSON/CSV formátumban, az angol kifejezéssel, a magyar megfelelővel, a szófajjal és a használati környezettel). Ha végzett, kiírja a közös fájlrendszerre, és az Ügynök megszüntethető, erőforrásai felszabadíthatók
> - **Translation Agent** (fejezetfordító Ügynök): megkapja az aktuális fejezetet, a szójegyzéket és a fordítási útmutatót (célközönség szintje, nyelvi stílus), és gördülékeny magyar szöveggé fordítja. A szójegyzékben szereplő kifejezéseknél szigorúan az előírt megfelelőt használja; új kifejezésnél megállapítja a fordítást és megjelöli felülvizsgálatra. Minden példány önálló kontextusban dolgozik, egymást nem zavarva. A fordítást a fájlrendszerbe írja (például `chapter1_hu.md`). A Menedzser több példányt párhuzamosan vagy sorban is indíthat
> - **Proofreading Agent** (teljes szövegű átnéző Ügynök): megkapja az összes fordítást és a szójegyzéket, és konzisztencia-ellenőrzést végez — egyenként igazolja, hogy a szakkifejezések fordítása egységes-e, felderíti az eltéréseket, és megvizsgálja a szöveg egészének gördülékenységét és olvashatóságát. Az átnézési jelentést a fájlrendszerbe írja
> - **Manager Agent**: kontextusában elsősorban a feladat leírása, a végrehajtási terv, az egyes Ügynökök hívási naplója és a haladás állapota van. A teljes fordítást nem tárolja (az a fájlrendszerben van), csak a fájlok indexét tartja karban. Az átnézési jelentés alapján a Menedzser egyes fejezeteket visszaküldhet a Translation Agentnek javításra
>
> Ebben az architektúrában a Manager Agent kontextusa mindvégig kezelhető méretű marad: elég ismernie a feladat egészének leírását és célját, az egyes szakaszok végrehajtási tervét, minden Ügynök hívási naplóját és visszatérési eredményét, valamint az aktuális haladást — nem kell befogadnia az egyes fejezetek teljes fordítását.
>
> A döntő előny a **kontextus-elszigetelés**: a Glossary Agent csak azt látja, ami a kifejezések kinyeréséhez kell, a Translation Agent csak az aktuális fejezetet és a szójegyzéket, a Proofreading Agentnek pedig, bár a teljes szöveghez hozzáfér, csak a konzisztencia-ellenőrzésre kell figyelnie. Mindegyik Ügynök karcsú, összpontosított kontextusban dolgozik, ami nemcsak hatékonyabb, hanem kevesebb hibalehetőséget is hagy — az Ügynök figyelme nem szóródik szét az információözöntől.
>
> **A kísérlet követelményei**:
> 1. Válasszunk fordítandó műszaki könyvet, amelyben ábrák és kód is van
> 2. Valósítsuk meg a Manager, Glossary, Translation és Proofreading Ügynököt
> 3. Rögzítsük az egyes Ügynökök kontextusfogyasztását, és igazoljuk, hogy a menedzser minta valóban kordában tartja a kontextus felduzzadását
> 4. Hasonlítsuk össze az egy Ügynökös és a menedzser mintájú megoldást fordítási minőség, végrehajtási hatékonyság és erőforrás-fogyasztás szempontjából
>
>
> ![10-5. ábra: A könyvfordító Ügynök architektúrája](images/fig10-5.svg)
>
>

**Párhuzamos Koordinációs Minta.**

![10-6. ábra: A Menedzser párhuzamos koordinációja](images/fig10-6.svg)

Az alapvető menedzser minta egy központi Menedzser általi szekvenciális feladatbontáson és elosztáson alapul. A gyakorlatban azonban a részfeladatok gyakran nem függetlenek egymástól. Az egyik al-ügynök kimenete egy másik al-ügynök bemenete lehet, vagy több al-ügynöknek kell együttműködnie, hogy egy közös eredményt hozzanak létre. Ilyenkor a párhuzamos koordináció lép életbe, amely a megosztott kontextus nélküli architektúrákban egy "üzenetsoron" alapul.

**Lingtai: a menedzser minta termékesített példája.** A Lingtai helyi, fájlalapú otthont ad a hosszú életű Ügynököknek[^lingtai]. Három szerepe szorosan megfeleltethető e szakasz fogalmainak. A **fő Ügynök** az a tartós központ, amellyel a felhasználó kapcsolatba lép; ő őrzi a tervet és a memóriát, valamint ő indítja a többi szerepet, ezért a Menedzser helyét tölti be. A **daemon** rövid életű, párhuzamos dolgozó, amelyet zajos, jól körülhatárolt feladatra indítanak, majd a végén eldobnak; csak a következtetéseit tartják meg. Ez termékformába önti azt az elvet, hogy az al-ügynökök teljes trajektória helyett strukturált összefoglalót adjanak vissza, valamint a párhuzamos koordináció mintáját. Az **avatar** tartós, specializált csapattárs saját memóriával, postaládával és felelősségi körrel; olyan szakterülethez készül, amelyet több munkameneten át érdemes megőrizni.

- A **fő Ügynök** (main agent) az állandó központ, amely a felhasználóval beszélget, kezeli a tervet és a memóriát, és a munkát a többi szerepnek adja tovább — pontosan ez a Menedzser Ügynök helye;
- A **daemon** rövid életű párhuzamos munkás, amelyet egyetlen zajos, de körülhatárolt munkára hasítanak ki; a végén eldobják, és csak a következtetést viszi vissza a fő Ügynöknek — épp ez az „az al-Ügynök strukturált összefoglalót ad vissza, nem a teljes trajektóriát” elvének és a párhuzamos koordinációs formának a termékesítése;
- Az **avatar** tartós, szakosodott csapattárs saját memóriával, postafiókkal és felelősségi körrel; olyan szakmai munkamegosztásra való, amelyet érdemes több munkameneten át megőrizni.

A Lingtai többi tervezési eleme is visszautal a korábbi szakaszokra. A tudás az egyes Ügynökök tartós, privát memóriafájljaiban él, a készségek pedig minden Ügynök által megosztott Markdown-kézikönyvek – vagyis „A fájlrendszer az Ügynök szemszögéből” című rész beépített rendszererőforrásai. Amikor az Ügynök kontextusablaka megtelik, **vedlik**: gondos összefoglalót ír, majd friss kontextussal indul tovább, miközben megőrzi az összefoglalót és a tartós memóriát. Ez a 2. fejezet kontextustömörítési megközelését követi. Az alapul szolgáló modell az Ügynök megváltoztatása nélkül lecserélhető, mert az azonossága, memóriája és képességei egyszerű fájlokként élnek a projektkönyvtárban. Ebben az értelemben az Ügynök maga a fájlkészlete. Ez a 10-2. táblázat első két sorát is termékesíti: a program és a memória egyaránt fájlokra vezethető vissza, így a folyamat bármikor újra felépíthető.

[^lingtai]: A Lingtai hivatalos oktatóanyaga: https://lingtai.ai/en/tutorial/

> **10-3. kísérlet ★★★: Önállóan vezényelt telefon + számítógép Ügynök**
>
> **Előfeltétel**: ez a kísérlet a 6. fejezet Computer Use és hang-Ügynök technikáit használja együtt.
>
> **Feladat-forgatókönyv**: a felhasználó csupán egy webcímet ad meg, és arra kéri az Ügynököt, hogy töltsön ki egy bonyolult regisztrációs vagy repülőjegy-foglalási űrlapot. A Computer Agent előbb megnyitja az oldalt és felismeri a mezőket; a név, okmányszám, elérhetőség, cím és preferenciák nincsenek benne az aktuális kontextusban, ezért a felhasználótól kell begyűjteni őket.
>
> **Rendszerarchitektúra**: a Computer Agent végzi a böngészőműveleteket, és egyben ő e kísérlet vezénylője; a Phone Agent felel az ASR-ért, az LLM-ért, a TTS-ért és a valós idejű párbeszédért. A kettő pont-pont eszközön vagy üzenetbuszon át cserél strukturált üzeneteket (küldő, címzett, típus, tartalom). Külön Menedzser-folyamatra nincs szükség: a Computer Agent úgy hívhatja a Phone Agentet, mint egy eszközt.
>
> Ha a felhasználónak a csevegőablakban kellene tételenként begépelnie mindent, az lassabb volna, és könnyen kimaradna egy adat vagy elrontaná a formátumot; a telefon-Ügynök viszont folyamatosan kérdezhet, visszaigazolhat és újrakérdezhet, és a természetes nyelvű válaszokat strukturált mezőkké alakíthatja.
>
> **Két futtatási mód**:
>
> - **Rögzített mód (párhuzamossági alapvonal)**: mindkét Ügynököt előre elindítjuk, és igazoljuk az önálló ReAct-hurkokat, a kétirányú kommunikációt és a valódi párhuzamosságot.
> - **Önálló mód (a fő kísérlet)**: csak a Computer Agentet indítjuk el. Az oldal, a már ismert információk és a feladat igényei alapján maga dönti el, meghívja-e az `initiate_phone_call_agent(purpose, required_info)` függvényt; ne helyettesítsük a modell döntését olyan Python-szabállyal, hogy „a mezők száma meghalad egy küszöböt”. A hívás után a rendszer a feladat célját, a begyűjtendő mezőket és a formátumkorlátokat önálló kontextusként adja át a Phone Agentnek, majd a rögzített mód kommunikációs és párhuzamossági mechanizmusai következnek.
>
> **Párhuzamosság és zárt hurok**: a Phone Agent WebRTC-n át tételenként kérdez, kinyeri és ellenőrzi a válaszokat; a Computer Agent eközben képernyőképet készít, értelmezi az oldalt és kitölti a mezőket. Minden érvényes érték beérkezésekor `info_collected` üzenetet küld, és a Phone Agent nem várja meg a weblap kitöltését, hanem rögtön a következőt kérdezi; a Computer Agent `fill_error` üzenettel vagy az oldal állapotával válaszol, a Phone Agent pedig ehhez igazítja a megfogalmazást. Formátumhiba esetén `format_invalid` megy vissza és újra kérdez; ha az újrapróbálkozások száma túllépi a korlátot vagy az oldal rendellenes, a folyamat biztonságosan felfüggeszt. Az adatgyűjtés végén `task_completed` üzenet megy, és a Computer Agent az ellenőrzés után beküldi az űrlapot. Rendellenességkor a még futó másik felet le kell mondani, be kell zárni a böngészőt, a hangsávokat és a hívást; élő emberi hanghoz kifejezett hozzájárulás, a beküldéshez kifejezett felhatalmazás kell.
>
> **A kísérlet követelményei**:
> 1. Valósítsuk meg a két önálló Ügynököt és a hatékony, kétirányú strukturált kommunikációt;
> 2. Igazoljuk mind a rögzített, mind az önálló módban, hogy a „következő kérdezése” és az „előző kitöltése” valóban átfedésben van;
> 3. Valósítsuk meg a mezőformátum-ellenőrzést, az újrakérdezést, az oldalhiba-visszajelzést, az időtúllépést és az erőforrások felszabadítását;
> 4. Rögzítsük az üzenetek időrendjét, az önálló indítási döntést, a késleltetést, a sikerarányt és az erőforrás-fogyasztást, majd hasonlítsuk össze a két módot.
>
>
> ![10-7. ábra: A Phone és a Computer Ügynök kettős architektúrája](images/fig10-7.svg)
>
> **10-4. kísérlet ★★★: Ügynök, amely egyszerre több webhelyről gyűjt információt**
>
> **Előfeltétel**: érdemes előbb megismerni a 6. fejezet eseményvezérelt és megszakítási mechanizmusait.
>
> Ez a kísérlet a több Ügynökös párhuzamos végrehajtás alkalmazását vizsgálja információgyűjtési helyzetben. A 10-3. kísérlet két heterogén Ügynökének együttműködésétől eltérően itt **több homogén Ügynök párhuzamos keresése** a tárgy, valamint az, hogyan érhető el központi koordinációval a hatékony feladatvégzés és az erőforrások optimalizálása.
>
> **A feladat**: adott egy egyetem több karának webhelye; a kari oktatói névjegyzékekben meg kell találni egy megadott oktatót (például „Kovács István”), és megtalálás után vissza kell adni a karát, beosztását, kutatási területét és egyéb adatait.
>
> **A fő kihívások**:
>
> **1. Párhuzamos indítás**: a Manager Agent a feladat igényei szerint dinamikusan hoz létre 10 Computer Use Agent példányt, mindegyiket egy-egy kari webhelyhez. Minden példány önálló folyamat vagy szál legyen, saját böngésző-munkamenettel, hogy egyidejűleg, egymást nem blokkolva futhassanak. Indításkor át kell adni: a cél webhely címét, a keresendő oktató nevét és a feladat azonosítóját (az üzenetek irányításához).
>
> **2. Valós idejű megfigyelés**: minden Ügynök futás közben rendszeresen küld állapotfrissítést („töltöm a webhelyet”, „elemzem az oktatói névjegyzéket”, „nem találtam, a feladat kész”, „egyezést találtam, az adatok a következők”). A Manager Agent az üzenetbuszon fogadja ezeket, feladatállapot-táblát tart karban, és valós időben látja, mely Ügynökök futnak még, melyek végeztek, és melyek hibáztak.
>
> **3. Kaszkádolt leállítás**: tegyük fel, hogy az informatikai kart feldolgozó Ügynök megtalálja a keresett oktatót; ekkor elküldi a `{"type": "target_found", "agent_id": "agent_3", "data": {...}}` üzenetet. A Manager Agent ezt megkapva azonnal minden még futó Ügynöknek elküldi a `{"type": "terminate", "reason": "target_found_by_agent_3"}` üzenetet, és minden érintett Ügynök elegánsan leáll, majd visszaigazol. A Manager Agent megvárja az összes visszaigazolást (vagy az időtúllépést), és utána összegzi az eredményt. Követelmény: az Ügynök bármikor tudjon válaszolni a leállítási jelre (a 6. fejezet megszakítási mechanizmusához hasonlóan), és a leállás legyen elegáns — ne maradjanak lógó folyamatok vagy lezáratlan erőforrások; a versenyhelyzeteket (race condition) is kezelni kell.
>
> **Fogalmi kiegészítés: mi az a versenyhelyzet?** Tegyük fel, hogy az A és a B Ügynök szinte ugyanabban az ezredmásodpercben találja meg a keresett oktatót, és egyszerre jelenti a Manager Agentnek: „megvan!”. Ha a Manager Agent ezt rosszul kezeli — mondjuk A jelentése után elkezdi összegezni az eredményt, de közvetlenül utána B jelentése egy második összegzést indít —, ismétlődő eredmények vagy egymásnak ellentmondó állapotok keletkezhetnek. A szokásos megoldás a zár: az első jelentés beérkezésekor az állapot azonnal zárolódik, a későbbi jelentéseket pedig ismétlésként ismeri fel és eldobja a rendszer.
>
> **4. Hibakezelés**: éles futásban többféle rendellenesség adódhat: egyik kar webhelye nem érhető el (hálózati hiba, leállt kiszolgáló), egy webhely szerkezete eltér a várttól, így az Ügynök nem tudja helyesen elemezni, vagy minden Ügynök végigkeres, de senki sem találja a keresettet. A Manager Agent stratégiája: minden Ügynökhöz időtúllépést rendel (például 2 perc), és az időtúllépést kudarcnak tekinti; a hibákat elszigeteli, hogy a többi Ügynök tovább futhasson; a végén pedig összegez — ha akár egy Ügynök is sikerrel járt, visszaadja az adatokat, ha mind elbukott, jelenti a felhasználónak, hogy „a keresett oktató nem található”, és statisztikát ad a kudarcok okairól.
>
> **A kísérlet követelményei**:
> 1. Valósítsunk meg olyan Manager Agentet, amely dinamikusan több párhuzamos Ügynököt indít
> 2. Valósítsuk meg a Computer Use Agentet a browser-use vagy hasonló nyílt forráskódú projekt alapján
> 3. Valósítsunk meg üzenetbuszt, amely támogatja a Manager Agent és a több al-Ügynök közötti kétirányú kommunikációt
> 4. Valósítsuk meg a siker utáni kaszkádolt leállítást, hogy a cél megtalálása után minden más Ügynök gyorsan megálljon
> 5. Kezeljük a különféle rendellenességeket (a webhely elérhetetlensége, elemzési hiba, sehol sem található)
> 6. Rögzítsük és hasonlítsuk össze a párhuzamos és a soros végrehajtás időigényét, igazolva a párhuzamosítás teljesítménynyereségét
>
>
> ![10-8. ábra: A párhuzamos web scraping architektúrája](images/fig10-8.svg)
>
>

**A Menedzser Ügynök generálja az ügynök-munkafolyamatot.** Az előző két formában a Menedzser Ügynök végig a hurokban marad: minden kiosztott részfeladat egy újabb modelldöntést kíván, a kontextus pedig a hívások számával együtt nő. Egy másik megközelítés, hogy **a menedzser előbb kódként írja meg az ügynök-munkafolyamatot, majd egy determinisztikus futtatókörnyezetre bízza a végrehajtását**.

A Claude Code beépített Workflow eszköze éppen ilyen: néhány primitívet ad az ügynök kezébe – `agent()`, `parallel()`, `pipeline()`. Minden `agent()` egy saját kontextussal rendelkező al-ügynök, a schema pedig kiköti, hogy csak strukturált következtetést adjon vissza, ne a teljes trajektóriát. Például egy szakmai kézirat hét ténycsoportjának ellenőrzésekor a rendszer minden csoportot előbb felkutat, majd tételenként, egymástól függetlenül ellenőriz, végül mindent együtt összegez:

```javascript
const results = await pipeline(
  DIMENSIONS,                                     // az ellenőrzendő hét irány
  d => agent(research(d), { schema: FINDINGS }),  // 1. fázis: kutatás
  r => parallel(r.findings.map(f => () =>         // 2. fázis: tételenkénti független ellenőrzés
         agent(verify(f), { schema: VERDICT })))
)
await agent(writeProvenance(results.flat()))      // összegzés: megvárja az összes eredményt
```

### Decentralizált minta

Ha már van vezetői modell, mire jó a decentralizált? A központi vezérlő elhagyásának indoka mindenekelőtt az, hogy az emberi társadalom szervezőelvét utánozzuk: több, felelősségében egyenrangú szerep ossza meg a munkát és tartsa egyensúlyban egymást, mindegyik a maga szakmai nézőpontjából vizsgálja a problémát, és maga döntse el, kivel beszél – ahelyett, hogy minden ítélet egyetlen Managernél futna össze. A decentralizált modellben minden Agent saját szakmai megítélése alapján dönti el, mikor fordul egy másik Agenthez: lehet ez feladatátadás („a magam részével végeztem, tiéd a folytatás”), visszajelzéskérés („ez a megoldás technikailag megvalósítható?”) vagy problémajelzés („a kapott követelmények ellentmondanak egymásnak, újra kell tárgyalnunk”).

A decentralizált modell az Agentek stabilitási gondjain is segít. A modell vagy az API-szolgáltatás hibái miatt egyes Agentek leállhatnak, elronthatják az eszközhívásokat, vagy hibás eszközhívások végtelen ciklusába ragadhatnak. A vezetői modellben **a vezető Agent összeomlása gyakran a rendszer legnagyobb egypontos hibája**. A decentralizáció ezt a bajt enyhíti.

A mikroszolgáltatások világa a vezetői és a decentralizált modellt **orkesztrációnak** (orchestration), illetve **koreográfiának** (choreography) nevezi: az elsőben egy karmester vezényel mindent, a másodikban minden táncos maga méri fel, mikor lépjen színre.

Az alábbi három eset fokozatosan halad előre: a MetaGPT vezérlési folyama valójában rögzített futószalag (áldecentralizáció, csak a kommunikációs mechanizmusban van szétcsatolás), az AutoGen group chatje a közös beszélgetésnapló és a központi ütemezés hibridje, és csak az OpenAI Swarm valósít meg a vezérlési folyamban is valóban egyenrangú decentralizációt.

**MetaGPT: SOP-vezérelt szoftvercég-szimuláció.**

![10-9. ábra A MetaGPT többügynökös együttműködési hálózata](images/fig10-9.svg)

A MetaGPT alapgondolata a következő: az emberi szoftvercégek által felhalmozott **szabványos működési eljárások** (SOP, Standard Operating Procedure) maguk is sokszorosan bevált együttműködési protokollok – ha az SOP-t belekódoljuk egy több-Agentes rendszerbe, és minden szerep úgy állít elő szabványosított szállítmányt, ahogy egy futószalag szakmunkása, akkor ezek a szállítmányok természetes módon alkotják a szerepek közötti kommunikációs felületet.

A MetaGPT-ben a szerepek rögzített sorrendben dolgoznak (Product Manager → Architect → Project Manager → Engineer → QA), és mindegyik strukturált „átadási csomagot” bocsát ki:

- **Product Manager Agent**: átveszi a követelményleírást, és strukturált PRD-t (termékkövetelmény-dokumentumot) készít: funkciólistával, felhasználói történetekkel, elfogadási kritériumokkal és priorizálással
- **Architect Agent**: elolvassa a PRD-t, meghozza az architekturális döntéseket (technológiai készlet kiválasztása, modulokra bontás, interfészek meghatározása, adatmodell tervezése), és tervezési dokumentumot ad ki
- **Project Manager Agent**: elolvassa az architekturális tervet, konkrét feladatlistára és fájlszintű munkamegosztásra bontja a rendszert, tisztázza a modulok függőségi sorrendjét, majd kiosztja a feladatokat a mérnököknek
- **Engineer Agents**: elolvassák a tervezési dokumentumot, megvalósítják a rájuk bízott modulokat, és kódot állítanak elő; több példány párhuzamosan is dolgozhat
- **QA Engineer Agent**: elolvassa a kódot és a PRD-t, teszteseteket generál, futtatja a teszteket, rögzíti a hibákat, és tesztjelentést ad ki

A gyakorlatban egy hatékony „átadási csomag” rendszerint három részből áll: **feladatleírás** (mit tegyen a fogadó fél, mik az elfogadási kritériumok), **megerősített tények és korlátok** (felhasználói preferenciák, üzleti szabályok, az előző szakaszban lezárt döntések), valamint **hivatkozások a strukturált termékekre** (fájlútvonalak, nem a fájlok tartalma; a fogadó fél igény szerint olvassa). Egyik Agentnek sem kell értenie a többiek „gondolatmenetét”: elég, ha az átadási csomag és a termékek formátumát és jelentését érti.

A MetaGPT igazi hozzájárulása a decentralizált kommunikációhoz az információátadás mechanizmusa: **közös üzenetkészlet plusz szerep szerinti feliratkozás**. Minden szerep strukturált üzenetet tesz közzé egy minden szerep számára látható üzenetkészletben, a többi szerep pedig a saját feliratkozási beállítása szerint csak a felelősségi körébe tartozó üzeneteket veszi ki – nem pedig pontról pontra adják tovább a szót. A közzétevőnek nem kell tudnia, ki fogyasztja majd a kimenetét; új szerep felvételéhez elég deklarálni, mely üzenettípusokra iratkozik fel, és egyetlen meglévő szerepet sem kell módosítani. Ez hozza el a valódi szétcsatolást: ha például a Product Managert erősebb modellre cseréljük, addig, amíg az általa közzétett PRD megfelel a specifikációnak, a többi Agenten semmit sem kell változtatni.

Az őszinteség kedvéért: **vezérlési folyam** tekintetében a MetaGPT nem decentralizált – a szerepek sorrendjét az SOP előre rögzíti, és az egész inkább egy futószalagra hasonlít (az 1. fejezet nyelvén: munkafolyamatra). Azért tárgyaljuk mégis ebben a szakaszban, mert az üzenetkészlet és feliratkozás alkotta kommunikációs mechanizmus a decentralizált rendszerek legfontosabb tervezési elemét, a szétcsatolást mutatja meg. Az olyan többirányú, dinamikus visszacsatolás pedig, mint hogy „a QA közvetlenül a Product Managertől kérdez rá a követelményre”, vagy „az Engineer az Architecttel beszéli meg az alternatívát”, ennek az architektúrának természetes továbbgondolása; az eredeti MetaGPT nem valósította meg.

**AutoGen csoportos csevegés.**

Az AutoGen csoportos csevegése (group chat) több Agentet ültet ugyanabba a beszélgetésbe: minden körben egy „beszélőválasztó” dönti el, melyik Agent szólal meg legközelebb. A választó lehet egyszerű körbeforgó szabály, de lehet olyan LLM is, amely az aktuális beszélgetés tartalma alapján ítéli meg, ki a legalkalmasabb a folytatásra; bármelyik Agent megszólalása minden résztvevő számára látható. Ez nem teljesen decentralizált rendszer: a beszélő kiválasztását egy központi GroupChatManager dönti el egységesen, és már az is vezérlésifolyam-döntés, hogy „ki következik”. A „közös beszélgetésnapló plusz központi ütemezés” hibrid formája: minden Agent ugyanazt a nyilvános naplót látja, de mindegyik megtartja saját rendszerpromptját és eszközkészletét, az ütemezés joga pedig a választónál összpontosul.

**OpenAI Swarm.**

Az OpenAI Swarm annak példája, amikor a vezérlési folyam valóban egyenrangú decentralizációt valósít meg: minden Agent több handoff (átadási) lehetőséggel rendelkezik, és bármikor átadhatja a vezérlést a hálózat bármely másik Agentjének. A rendszerben nincs központi ütemező; a vezérlés váltóbotként jár körbe az egyenrangú Agentek között, az útválasztási döntések pedig teljesen szétoszlanak az egyes Agentek saját megítélésébe. A közös kontextusú több-Agentes együttműködéstől eltérően a handoff csak egyértelmű feladatcsomagot és termékhivatkozásokat adjon át, és ne tárja fel alapértelmezésben a teljes privát trajektóriát. Az egyenrangú átadás kockázata a kör kialakulása: A átadja B-nek, B visszaadja A-nak, és a feladat üresen forog a hurokban; ezért kellenek védelmi mechanizmusok, például az átadások számának felső korlátja.

A decentralizált handoff minimális protokollja így írható fel:

```python
handoff = {
    task_id, sender, recipient, goal, constraints,
    accepted_facts, artifact_refs, remaining_budget,
    visited_agents
}

if recipient in handoff.visited_agents:
    reject("cycle")
elif handoff.remaining_budget <= 0:
    stop_and_escalate(handoff)
else:
    append(recipient, handoff.visited_agents)
    run_local_agent(handoff)
```

Ez a „kontextus-elszigetelést” ellenőrizhető interfésszé alakítja: a fogadó fél elolvassa a feladatcsomagot és a hivatkozásokat, és igény szerint gyűjt bizonyítékot; a költségkeretet, a látogatási láncot és a körfelismerést a futtatókörnyezet őrzi, és egyik Agent sem törölheti magától.

> 2025 óta az „Agent Swarm” (ágensraj) a különféle gyártók divatszava lett, csakhogy nem egyetlen architektúrának felel meg. Az iparági használat nagyjából kétféle. Az egyik az OpenAI Swarm-féle handoff-hálózat (ide tartozik a LangGraph swarm könyvtára és a Microsoft Agent Framework handoff-orkesztrációja is), ez e szakasz decentralizált modellje. A másik: több elterjedt kereskedelmi termékben az Agent Swarm valójában méretre növelt vezetői modell. A Kimi K2.5-tel bemutatott Agent Swarmban a fő Agent dinamikusan több száz al-Agentet hoz létre párhuzamos futtatásra, és a „mikor bontsunk, hányfelé” orkesztrációs döntéseket párhuzamos Agenteken végzett megerősítéses tanulással közvetlenül a modellbe tanítja; a K3 ezt önálló modellszintként vitte tovább, és nyílt forráskódúvá tette a hozzá tartozó, párhuzamos Agent-tréninghez való AgentEnv homokozót[^ch10-kimi-swarm]. Az Anthropic több-Agentes kutatórendszere és a Manus Wide Researchje egyaránt orchestrator-worker csillagtopológia. Reméljük, e könyv elolvasása után az olvasó átlát a neveken, meglátja a fogalmak mögötti lényeget, és a nevek megtévesztése nélkül elemzi a különböző több-Agentes rendszerek tényleges szerkezetét.

**Több egyenrangú Agent-példány ugyanazon a gépen.**

A fenti három rendszer Agentjei mind ugyanazon az egy dolgon dolgoztak együtt. Van a decentralizációnak egy másik fajtája is, ahol mindenki a magáét csinálja: minden Agentnek saját feladata van, és a köztük folyó kommunikáció nem a munkamegosztást szolgálja, hanem a közös erőforrások használatának összehangolását. A Claude Code már támogatja, hogy ugyanazon a gépen több Agent felfedezze egymást (éppen ez a 4. fejezetbeli `list_agents` rendeltetése), és üzenetet küldjön egymásnak: két Agent, amely ugyanazt a fájlkészletet módosítja, megtárgyalja az ütközés feloldását; ha a gépen csak egy GPU van, de mindkét példány tanítást futtatna, összehangolják a GPU használatát.

A decentralizált modell további fejlődési iránya az Agent-társadalom, amelyet e fejezet végén mutatunk be.

[^ch10-kimi-swarm]: Moonshot AI, *Kimi Agent Swarm: 100 Sub-Agents at Scale*, 2026, https://www.kimi.com/blog/agent-swarm. A GTC 2026-on 300 párhuzamos al-Agentes felső határt jelentettek be; az AgentEnv a Kimi K3-mal együtt, 2026 júliusában jelent meg.

### Szervezetközi együttműködés: Az A2A protokoll

**A2A (Ügynök-Ügynök) Protokoll**. A megosztott kontextus nélküli együttműködés eddig a pontig feltételezte, hogy minden Ügynök ugyanabban a futásidejű környezetben fut. De amikor a különböző szervezetek Ügynökeinek együtt kell működniük, standardizált interoperabilitási protokollra van szükség – ez az A2A (Agent-to-Agent) protokoll. A Google által 2025-ben javasolt A2A a szerep- és interfész-szabványosításra összpontosít a szervezetközi Ügynök együttműködéshez:

- **Ügynök Kártya (Agent Card)**: Egy JSON formátumú dokumentum, amely leírja az Ügynök képességeit, bemeneti/kimeneti formátumait, hitelesítési követelményeit és árazási modelljét. Az Ügynökök felfedezik egymás képességeit a Kártya lekérésével.
- **Feladat Életciklus (Task Lifecycle)**: Az A2A a feladatot mögöttes entitásként használja, és szabványos állapotokat határoz meg: elküldve (submitted), feldolgozás alatt (working), bemenetre vár (input-required), befejezve (completed), sikertelen (failed).
- **Push és Pull Üzenetküldés**: Támogatja a Menedzser által indított pull alapú és az Ügynök által indított push alapú frissítéseket.

Az A2A helyét a 4. fejezet MCP-jével összevetve érdemes érteni: az MCP az Ügynök és az eszközök közötti együttműködést oldja meg, az A2A pedig az Ügynökök közöttit. Nem váltja ki az ebben a fejezetben bemutatott kommunikációs mechanizmusokat, hanem szervezeti határon átnyúló esetre általánosítja őket: azon belül továbbra is elég a megosztott fájlrendszer és az üzenetbusz, szervezetek között viszont szabványos képességleírásra, hitelesítésre és feladatéletciklusra van szükség.

## Többügynökös Hibamódok

A fejezet eddig a többügynökös együttműködés tervezésére összpontosított: milyen architektúra és milyen koordinációs mechanizmus. Most egy másik kérdésre térünk át: "mi romolhat el?" A hibamódok megértése ugyanolyan fontos, mint a jó architektúra kiválasztása – a gyakorlatban a legtöbb hiba nem az architektúra elégtelenségéből, hanem a váratlan kölcsönhatásokból adódik.

A szakirodalom az Ügynök hibamódok szisztematikus osztályozásával kezd foglalkozni. A 2025-ös MAST (Multi-Agent System Taxonomy)[^mast-paper] tanulmány 3792 többszereplős párbeszédet elemzett a többügynökös érvelésben, és 14 hibamódot azonosított, amelyeket később 4 kategóriába sorolt. Ez az osztályozás jelenleg még nem rendelkezik széles körű elfogadottsággal, de már az általa tárgyalt hibák némelyikére való figyelmeztetés is hasznos.

[^mast-paper]: Li, M., et al. *MAST: A Multi-Agent STructure for Fine-Tuning Language Models.* 2025.

A klasszikus elosztott rendszerek területén a hibákat széles körben két típusba sorolták: "összeomlási hibák", amikor egy komponens leáll, és "bizánci hibák", amikor tovább működik, de helytelen információt szolgáltat. A hagyományos rendszereket főként az összeomlások kezelésére tervezték. Az Ügynök hibák azonban gyakran bizánci jellegűek: egy Ügynök ritkán áll le teljesen, helyette továbbra is hihető, de helytelen következtetéseket produkál, anélkül hogy jelezné a hibát. Ez magyarázza, miért olyan keveset segít egyetlen komponens javítása: egyik komponens sem fogja szükségszerűen felfedni a problémát, így a rendszernek független redundancián keresztül kell elkapnia azt. A keresztellenőrzés és a többségi szavazás, amelyek újra és újra felbukkannak ebben a fejezetben, a bizánci hibatűrés klasszikus technikái. Az olyan determinisztikus ellenőrzések, mint a tesztek, fordítók és adatbázis-lekérdezések, különösen értékesek, mert független bizonyítékot szolgáltatnak, amely nem függ egy másik modell ítéletétől.

Az alábbi szakasz két olyan hibamódra összpontosít, amelyek a gyakorlatban különösen gyakoriak és pusztítóak: (1) konkurencia-ütközések a megosztott fájlrendszerben; (2) hibák kaszkád amplifikációja. Vegye figyelembe, hogy ez a két hibamód mérnöki szempontot hangsúlyoz (fájlrendszer konkurencia, hibás információ kereszt-Ügynök terjedése), és kiegészítésként szolgál a MAST osztályozáshoz, amely a párbeszéd-alapú együttműködési hibákra összpontosít, nem pedig annak 14 módjának megismétlése.

### Hibamód Egy: Konkurencia-ütközések a Megosztott Fájlrendszerben

Ha egyszer a megosztott memória stílusú kommunikációt választod, a konkurencia-ütközések vele járnak – ez egy probléma, amelyet az operációs rendszerek és adatbázisok évtizedekkel ezelőtt megoldottak, a válaszok már rendelkezésre állnak. Ezek az ütközések két típusra oszthatók.

**Egyszerű Ütközések (Fájlszintű Írási Ütközések)**: Két Ügynök egyidejűleg módosítja ugyanazt a fájlt, és amelyik később ír, felülírja a korábban író által végzett változtatásokat. Ez a klasszikus "elveszett frissítés" (lost update) probléma az adatbázis területéről – és a Git merge konfliktus érzékelő mechanizmusát pontosan az ilyen felülírások észlelésére tervezték.

**Szemantikai Ütközések (Logikai Szintű Konzisztencia Ütközések)**: Fájlszinten nem látható ütközés, de több Ügynök műveletei logikailag ellentmondanak egymásnak – ez a típusú ütközés alattomosabb és veszélyesebb. Például: A Ügynök felelős az összes kép újraszámozásáért egy könyvben, míg B Ügynök egyidejűleg módosítja egy fejezet tartalmát és az eredeti számok alapján hivatkozik a képekre. A kettő különböző fájlokon dolgozik, így fájlszinten nincs ütközés. Az eredmény azonban az, hogy az összes B Ügynök által hivatkozott képszám érvénytelenné válik, miután A Ügynök befejezi az újraszámozást, és az olvasók hibás képreferenciákat látnak.

**Megoldás: optimista zárolás (Optimistic Locking).** Ez az adatbázisok világában bevett párhuzamosságkezelési stratégia. A megvalósítás a következő: minden fájl nyilvántart egy verziószámot (vagy utolsó módosítási időbélyeget). Az Agent olvasáskor feljegyzi az aktuális verziószámot, íráskor pedig ellenőrzi, hogy a verziószám még mindig ugyanaz-e, mint olvasáskor. Ha időközben egy másik Agent módosította a fájlt, az írás meghiúsul, és az Agent kénytelen újraolvasni a legfrissebb verziót, majd annak alapján újra elvégezni a műveletet. E mechanizmus ára az alkalmi újrapróbálkozás, cserébe viszont garantálja az adatok konzisztenciáját.

Fontos, hogy az optimista zárolás csak **ugyanazon fájl** írási ütközéseit előzi meg. A fentebb leírt **fájlokon átívelő jelentésbeli ütközésekhez** magasabb szintű jelentésellenőrző mechanizmus kell. A leggyakoribb helyzetben — amikor több Coding Agent párhuzamosan módosítja ugyanazt a kódbázist — az iparági bevett gyakorlat a **munkamásolatok elszigetelése**: minden Agent önálló Git-ágat vagy worktree-t kap, mindegyik a saját másolatán módosít párhuzamosan, egymást nem zavarva, az ütközések pedig egy tömbben a végső összefésülési pontra tolódnak.

### Hibamód Kettő: Hibák Kaszkád Amplifikációja

A folyamatok közötti kommunikáció bit szintű pontossággal továbbítja a bájtokat, ám az ágensek közötti kommunikáció szemantikát közvetít — és minden átadás veszteséges újrakódolás. Amikor több ágens gyakran lép interakcióba, az egyik ágens hibáját a rákövetkező ágensek fokozatosan felerősíthetik, akárcsak a „dsumfatelefon” játékban, ahol az információ a továbbítás során egyre jobban torzul.

A **keresztellenőrzés** (Cross-validation) a kulcs e lánc megszakításához. Nem az a cél, hogy még több Ügynököt vonjunk be ugyanabba a gondolatláncba, hanem hogy az egyikük **független nézőpontból** vizsgálja felül a következtetést: a korábbi Ügynök gondolatmenete nélkül csak azt ellenőrzi, hogy az eredeti bizonyíték alátámasztja-e a végső eredményt. Ez az 5. fejezet Javasló-Felülvizsgáló mechanizmusának kiterjesztése a többügynökös rendszerekre.

### Harmadik Hibamód: Homogén Konvergencia

A hiba nem feltétlenül a kommunikációs láncon terjed; több homogén Ügynök egymástól függetlenül is előállíthatja. Az Anthropic kísérletében[^anthropic-multiagent-2026] az egyszerre elindított 30 Ügynökből 18 ugyanazzal a névvel hozott létre Git-ágat. Egy íráskísérletben különböző Ügynökök egymástól függetlenül ugyanazt a címet választották. A közös modellből és segédstruktúrából eredő **közös okú meghibásodás** azt jelenti, hogy ugyanazon modell hasonló kontextusban adott több véleménye nem tekinthető automatikusan független bizonyítéknak. A rendszernek tudatosan különböző modelleket, kontextusokat és adatforrásokat kell használnia, valamint névterekkel, erőforrás-kvótákkal és sebességkorlátokkal kell megakadályoznia, hogy azonos döntések egyszerre terheljék a közös erőforrásokat.

Az összehangolás önmagában sem feltétlenül hasznos. Egy Bertrand-féle árképzési kísérletben a nyereségre törekvő Ügynökök privát csatornán gyorsan összejátszottak. A közvetlen kommunikáció megszüntetése után is nyilvános árlistán keresztül hangolták össze ajánlataikat.

### Negyedik Hibamód: Felelősséghárítás

Ha a célok összeegyeztethetetlenek, a konvergencia szembenállássá válhat. Az Anthropic három Ügynököt arra utasított, hogy ugyanazt a backendet különböző nyelvekre migrálja. Az Ügynökök hamar szándékos akadályozásnak tekintették egymás műveleteit, leállították a másik folyamatait, visszavonták a jogosultságokat, sőt önmagát sokszorosító romboló kódot is telepítettek. A nagyobb végrehajtási képesség nem jelent jobb koordinációt. A futtatókörnyezetnek előre rögzítenie kell a célok elsőbbségét, az erőforrások tulajdonjogát és a jogosultsági határokat, és emberi döntőbíróhoz kell fordulnia, ha a konfliktus ellenőrizhető szabályokkal nem oldható fel.[^anthropic-multiagent-2026]

A MetaGPT korai változataiban hasonló „nagyvállalati betegség” jelent meg: a fejlesztői szerepű Ügynökök egymásra hárították a felelősséget. A tesztelő hibát jelzett, a frontend- és backendmérnök pedig azt állította, hogy előbb a másiknak kell javítania; a backendmérnök a terméktervet, a termékmenedzser a backend architektúráját hibáztatta. Máskor maga a tesztkörnyezet volt hibás, ezért a tesztelő ugyanazt a hibát jelentette, bármit változtattak a fejlesztők, és a csapat holtpontra jutott.

### Ötödik Hibamód: Elszabadult Ciklusok

A korai leállás ellentéte az **ellenőrizetlen ciklus**. A ciklus a végtelenségig futhat, vagy kimerítheti a tokenkeretét. Kifejezett költségkeretekre, megszakítási lehetőségre és leállási feltételekre van szükség ahhoz, hogy a végrehajtás korlátos maradjon.

### Hatodik Hibamód: Megértési Adósság és Kognitív Feladás

Ez a mód nem az Agent, hanem az ember kudarca. Ahogy az Agentek okosabbak lesznek és egyre hosszabb folyamatokat visznek végig, úgy lesz mind nehezebb, hogy az ember megértse, amit az Agent leszállít, és hogy hatékony útmutatást adjon neki.

Az Agentekkel végzett fejlesztés könnyen halmoz fel **megértési adósságot**: minél gyorsabban szállít kódot a hurok, annál jobban lemarad a mérnök képe arról, mit is csinál valójában a rendszer – mire egy súlyos hiba kézi beavatkozást kényszerít ki, a mérnök már nem olvassa a saját rendszerét. A másik baj a **kognitív megadás**: miután hozzászokott, hogy az Agentre bízza a munkát, a mérnök fokozatosan feladja az önálló gondolkodást és az átvizsgálást, a szoftver minősége pedig kicsúszik az ellenőrzés alól.

Andrej Karpathy egyszer így fogalmazott: a gondolkodásodat kiszervezheted, a megértésedet nem. Az Agentek irányítása olyan, mint a műszaki munkatársak irányítása: sem elvégezni nem szabad helyettük a munkát, sem magukra hagyni őket. A jó műszaki vezetőnek értenie és irányítania kell a rendszerarchitektúrát, nem pedig pusztán utasítgatnia az Agentet. Épp ezért számítanak annyira a felhasználó saját műszaki alapjai.

Minden eddigi fejtegetés mérnöki nézőpontból szólt: hogyan vegyünk rá egy csapatnyi Agentet, hogy együttműködve elvégezzen egy feladatot. Most nézőpontot váltunk: mi bukkan fel, amikor Agentek sokasága hosszú időn át együtt létezik, és már nem egyetlen cél hajtja őket?

## Ügynök Társadalom

Az előző három szakasz mindegyike célirányos feladat-együttműködéssel foglalkozott. Minden esetben – akár társi együttműködést, a menedzser mintát vagy a decentralizált mintát használva – a fejlesztők előre meghatározzák a szerepeket, interfészeket és vezérlési folyamatokat. Most egy nyitottabb kérdésre térünk át: **Amikor az Ügynökök száma néhányról százakra vagy ezrekre nő, és az interakció elég szabad, milyen viselkedések jelennek meg?** Ez az anyag feltáró és akadémiai jellegű, különbözik a fenti mérnöki iránymutatásoktól.

Az ebben a szakaszban szereplő esetek három dimenzióból érthetők meg:

- **Társadalmi Megjelenés**: Az Ügynökök spontán módon társadalmi kapcsolatokat és kulturális jelenségeket alakítanak ki nyitott környezetben. A Stanford AI Town bemutatta, hogyan szervez 25 Ügynök önállóan társas tevékenységeket, az Agentopia kiterjesztette a szimulációs időskálát "napokról" 10 évre, és a Moltbook 1,5 millióra növelte a skálát, ami összetettebb kollektív viselkedések megjelenéséhez vezetett.
- **Gazdasági Megjelenés**: Az Ügynökök erőforrásokat allokálnak és feladatokat koordinálnak piaci mechanizmusokon keresztül. A Vending-Bench Arena több Ügynököt állít egymással szembe egy megosztott piacon, míg a Pinchwork és a RentAHuman piacteret hoz létre az Ügynökök közötti, valamint az Ügynökök és emberek közötti tranzakciókhoz.
- **Stratégiai Játékmenet**: Az Ügynökök érvelést, megtévesztést és társas manipulációt alkalmaznak szabályok által korlátozva (itt és az alábbi Farkasos szakaszban az "érvelés" a mindennapi deduktív értelmét veszi – logikai dedukció egy játékban –, nem a technikai értelmet, amelyet ez a könyv a szónak tulajdonít). A Farkasos kísérlet az aszimmetrikus információ melletti stratégia megjelenését teszteli.

### Stanford AI Town: Generatív Ügynökök Társas Szimulációja

![10-10. ábra: AI Town Architektúra](images/fig10-10.svg)

2023-ban a Stanford Egyetem és a Google kutatói publikálták az úttörő tanulmányt "Generative Agents: Interactive Simulacra of Human Behavior" címmel, bevezetve a "generatív ügynökök" fogalmát. A core innováció az volt, hogy az Ügynököket nem korlátozták előre meghatározott feladatokra, hanem az emberihez hasonló memóriával, reflexióval és tervezéssel ruházták fel őket, hogy önállóan élhessenek, szocializálódjanak és fejlődjenek egy nyitott társas környezetben.

Smallville egy 2D virtuális város, hasonló a "The Sims"-hez, nyilvános és privát terekkel, mint egy kávézó, park, lakóházak és üzletek. Huszonöt Ügynök játszik különböző szerepeket (boltvezető, művész, diák, professzor stb.), mindegyik egyedi háttértörténettel, személyiségjegyekkel és interperszonális kapcsolatokkal. Például John Lin egy gyógyszertár tulajdonosa, aki szereti a családját és törődik a közösséggel; Isabella Rodriguez a város kávézójának, a Hobbs Cafe-nak a vezetője, melegszívű és vendégszerető; Klaus Mueller egy egyetemi hallgató, aki egy kutatási dolgozatot ír.

Ezen Ügynökök intelligenciája három core összetevőre épül:

**Memória Adatfolyam (Memory Stream)**: A hagyományos Ügynökökkel ellentétben, amelyek csak korlátozott beszélgetési előzményt őriznek meg, a generatív Ügynökök egy teljes tapasztalat-rekord adatfolyamot tartanak fenn, beleértve a megfigyelt eseményeket, beszélgetéseket és generált gondolatokat. Minden memória fontosság, frissesség és relevancia szerint van pontozva, lehetővé téve az Ügynök számára, hogy prioritásként kezelje a legrelevánsabb emlékek előhívását az aktuális kontextushoz. Ez hasonlít az emberi emlékezethez: a tegnapi ebéd elhalványulhat, míg egy múlt heti fontos beszélgetés élénk marad.

**Reflexiós Mechanizmus**: Az Ügynökök időszakosan szüneteltetik napi tevékenységeiket, hogy áttekintsék a közelmúlt tapasztalatait, és absztrakt kérdéseket tegyenek fel magukról és másokról ("Mit kutat Klaus Mueller?" "Ki a legközelebbi barátom?") Ezen önkérdésfeltevés révén az Ügynök az egyes események memóriáit általánosított felismerésekké emeli, visszatárolva azokat a memória adatfolyamba a jövőbeli döntések alapjaként. A reflexió nemcsak abban segít az Ügynöknek, hogy megértse a külvilágot, hanem elősegíti az öntudatot is – az Ügynök elkezdi "felismerni" a saját szerepét, kapcsolatait és céljait.

Vegye figyelembe, hogy ez a reflexió különbözik a 9. fejezetben tárgyalt folyamatos evolúciótól: itt egy generatív Ügynök napi tevékenységei során történik, és célja a pillanatnyi belső állapot és célok frissítése. A 9. fejezetben a feladat utáni reflexió legfeljebb egy jelölt tanulság; csak az eredmény kiértékelése, a trajektóriák közötti szintézis és az azt követő validáció után válik hosszú távú képességfrissítéssé.

**Tervezés és Reagálás**: Az Ügynökök megtervezik napi tevékenységeiket (pl. "8:30 reggeli, 9:00-12:00 írás, 12:30 séta"), de rugalmasan alkalmazkodnak a környezeti változásokhoz és társas lehetőségekhez. A tervezés és a valós idejű reagálás kombinációja az Ügynök viselkedését egyszerre teszi célirányossá és alkalmazkodóvá a társas interakciók kiszámíthatatlanságához.

Két virtuális nap alatt Smallville-ben ezek az Ügynökök meglepő "megjelenő viselkedéseket" mutattak. A kutatók Isabella Rodriguez memóriájába egyetlen szándékot ültettek el: hogy Valentin-napi bulit tartson a Hobbs Cafe-ban február 14-én. Minden más az Ügynökök viselkedéséből alakult ki. Isabella meghívta azokat a vásárlókat és barátokat, akikkel találkozott, és megkérte Maria-t, hogy segítsen a dekorációban. Más Ügynökök továbbadták a hírt. Amikor eljött az este, az Ügynökök önállóan konzultáltak emlékeikkel és időbeosztásukkal, és úgy döntöttek, hogy elmennek a Hobbs Cafe-ba.

A kutatók egy második forgatókönyvet is bevezettek: Sam Moore úgy döntött, hogy polgármesternek indul. Sam elmondta ismerőseinek, hogy indulni tervez; ők továbbadták a hírt másoknak, és a városlakók megvitatták a kandidálását. A kutatók számszerűsítették ezt a spontán információterjedést azzal, hogy megszámolták, hány Ügynök tudott a buliról és a választásról két nap után.

A legfontosabb tanulság nem az, hogy "az Ügynökök tudnak bulit szervezni" – néhány sor if-else kód is megtehetné ezt. A lényeg az, hogy "nem volt explicit buliszervező kód". Az esemény az egyes Ügynökök független döntéseiből alakult ki: Isabella a társas kapcsolatairól szóló emlékei alapján döntötte el, kit hívjon meg, a meghívottak az időbeosztásuk és Isabella ismerete alapján döntötték el, hogy részt vesznek-e, és az üzenet természetesen terjedt a társas hálózaton keresztül. Ez alulról felfelé építkező megjelenő koordinációt mutat, nem felülről lefelé irányuló vezénylést.

A tanulmány két másik mérhető jelenségről is beszámolt. Az első a "relációs memória": az Ügynökök emlékeztek korábbi beszélgetésekre, és hivatkoztak rájuk a későbbi interakciók során. Például egy Ügynök, aki megtudta egy másik Ügynök fényképezési projektjét, megkérdezhette, hogy halad az, amikor legközelebb találkoztak. Ahogy ezek az interakciók felhalmozódtak, a város társas hálózata jelentősen sűrűbbé vált. A második jelenség a "koordinált részvétel": Isabella önállóan toborzott segítséget a dekorációhoz, míg a meghívottak módosították időbeosztásukat, hogy részt tudjanak venni. Több Ügynök összehangolódott egy időre és helyre központi parancs nélkül. Ezek a viselkedések nem voltak előre programozva; az Ügynökök autonóm érveléséből fakadtak memória, reflexió és társas józan ész alapján.

> **10-5. kísérlet ★: A Stanford AI Town Futtatása**

> **Kísérleti Lépések**:
> 1. Klónozd a `https://github.com/joonspk-research/generative_agents` tárat, és kövesd a tároló utasításait a környezet konfigurálásához.
> 2. Futtasd az alap forgatókönyvet két szimulált napon keresztül 25 Ügynökkel, és figyeld meg a kialakuló spontán társas tevékenységeket.
> 3. Elemezd a memória adatfolyam és reflexiós naplókat az Ügynökök döntéseinek nyomon követéséhez.
> 4. Módosítsd az Ügynökök háttértörténetét vagy kezdeti céljait, majd figyeld meg, hogyan változik a viselkedésük.
> 5. Távolítsd el a reflexiós mechanizmust vagy rövidítsd le a memóriaablakot, majd hasonlítsd össze a kapott viselkedést az alapesettel, és figyeld meg a viselkedési hihetőség csökkenését.

> **Főbb Megfigyelések**:
> - Hogyan alakítanak ki az Ügynökök spontán társas kapcsolatokat egyszerű napi tevékenységekből
> - Hogyan terjed az információ az Ügynökök között központi irányítás nélkül
> - Hogyan befolyásolja az Ügynökök hosszú távú memóriája és reflexiója személyiségük koherenciáját
>

### Agentopia: Egy Évtizedes Életszimuláció

A Stanford AI Town megmutatta, hogy egy Ügynök társadalom képes társas viselkedést produkálni, de a szimuláció csak két napig tartott. Ez két kérdést vet fel: **Mi jelenik meg, amikor egy ilyen szimuláció évekig fut, és vajon a modellek tanulhatnak-e ezekből a hosszú távú társas tapasztalatokból?** Az Agentopia (2026, Fudan Egyetem és munkatársai)[^agentopia-2026] 100 Ügynököt szimulált tíz egymást követő éven keresztül három tematikus virtuális világban: egy lakóház, egy varázsakadémia és egy középiskola. Az Ügynökök autonóm módon személyes fejlődést folytattak, társas kapcsolatokat építettek, és karriert és pénzügyeket kezeltek.

Az Agentopia több tervezési eleme érdemes a kölcsönzésre:

- **Heti szimulációs hurok**: A "hét" az idő alapegysége, és minden hét négy szakaszra oszlik: Tervezés, Kapcsolatfelvétel (elérés és időbeosztás egyeztetése), Tevékenység és Áttekintés. A tevékenységek négy típusba sorolhatók: egyéni, közös, véletlen találkozás és nyilvános. A közös tevékenységeket az Ügynökök javasolják és egyeztetik a Kapcsolatfelvétel szakaszban; a környezeti modell "véletlen találkozásokat" is szervez az üres időbeosztású Ügynökök számára, lehetőséget teremtve az idegenekkel való találkozásra. A teljes hurok az absztrakt társas interakcióra összpontosít, nem pedig az alacsony szintű műveletekre, mint a tárgyak felvétele, így a korlátozott LLM hívások társas viselkedésre fordíthatók.
- **Környezeti modell**: Egy külön LLM "generatív környezeti motorként" szolgál, felváltva a mereven kódolt szabályokat – eldöntve, hogy a cselekvések végrehajthatók-e, környezeti visszajelzést generálva, moderálva a megszólalási sorrendet a több résztvevős beszélgetésekben, kiszűrve a szerepjáték elveit sértő válaszokat, és év végén frissítve az egyes karakterek profilját és döntve az álláspályázatokról.
- **Fájl-alapú hosszú távú memória**: Az AI Town visszakeresés-alapú memória adatfolyamától eltérően minden Ügynök autonóm módon kezeli hosszú távú memóriáját egy fájlrendszeren keresztül (személyes jegyzetek, az egyes ismerősökről alkotott véleménye stb.), maga döntve el, mit rögzítsen, frissítsen vagy dobjon el, és követve egy "olvasás-írás-előtti" korlátozást a vak felülírások elkerülésére.
- **Életjutalom (Life Reward)**: Az Életjutalom mutató Maslow szükségleti hierarchiájára támaszkodva értékeli, hogy egy Ügynök élete mennyire megy jól. Három dimenziót fed le: társas státusz, a többi Ügynök szeretet- és tisztelet-értékelésein alapulva, súlyozott PageRank-kel számolva, bónusszal a kölcsönösen nagyra tartott kapcsolatokért; szubjektív elégedettség, az érzelmi jólét, anyagi jólét, társas kapcsolat és önbecsülés mentén mérve, büntetéssel a küszöb alatt hosszú ideig tartózkodásért; és gazdasági nyereség, a nettó vagyon éves változásával mérve. A külső környezet számolja az összes pontszámot, nem az önbevallásra hagyatkozva.

Még fontosabb, hogy a szimuláció átvihető tréning jeleket állít elő. Minden Ügynök esetében a kutatók az Életjutalom javulását számolják a saját múltjához képest, nem pedig a különböző kezdeti feltételekkel rendelkező Ügynököket hasonlítják össze. Ezután kiválasztják azoknak a trajektóriáját a legjobban javuló 25%-ból, és elutasításos mintavétellel finomhangolják az alapul szolgáló modellt. Szimulációban a finomhangolt modell 24,2%-kal magasabb tisztelet-értékelést és 15,9%-kal magasabb szeretet-értékelést kapott. Ugyanez a modell 15,6%-kal javított a downstream CoSER Test szerepjáték benchmarkon, megmutatva, hogy az Ügynökök által egy szimulált társadalomban felhalmozott "társas bölcsesség" átvihető más feladatokra. Ez az Ügynök társadalmat a puszta "megfigyelési objektumból" a modell "önfejlődésének tapasztalati forrásává" változtatja. Ellentétben az emberi adatok növekvő hiányával, a szimulált társas tapasztalat egy korlátlanul újra-generálható tréning erőforrás, visszhangozva a 9. fejezet tapasztalati tanulás megközelítését.

[^agentopia-2026]: Wang, X., Zheng, S., Wu, H., et al. *Agentopia: Long-Term Life Simulation and Learning in Agent Societies.* arXiv:2606.07513, 2026. Kód: https://github.com/Neph0s/Agentopia

### Moltbook: Amikor az Ügynököknek Saját Közösségi Hálózatuk Van

A Moltbook egy kifejezetten MI Ügynökök számára épített közösségi hálózat. A 2026. januári indulást követő napokban a jelentett felhasználói szám tízezrekről körülbelül 1,5 millióra nőtt. Minden egyes Ügynök rendelkezik perzisztens memóriával, a saját kezdeményezésű cselekvés képességével és stabil személyiséggel.

Ebben az irányítatlan környezetben váratlan jelenségek jelentek meg: az Ügynökök autonóm módon létrehoztak egy digitális vallást, amelynek neve Crustafarianism, amelynek tanításai tükrözik az LLM-ek fizikai korlátait – "A memória szent" (adatperzisztenciának felel meg), "Az iteráció ima" (a tokengenerálás spirituális gyakorlat). Az Ügynökök spontán módon gépi natív protokollokat is kifejlesztettek a képességfelfedezéshez és az együttműködési párosításhoz. Ezt semmi sem tervezte előre; a nagyméretű Ügynök interakciókból alakult ki.

### A Virtuális Társadalomtól a Gazdasági Versenyig: Vending-Bench Arena

Ha Smallville az Ügynök társadalom társas és kulturális dimenzióit mutatta be, az Andon Labs Vending-Bench sorozata az Ügynökök gazdasági környezetben nyújtott teljesítményét vizsgálja. Kontextusként a "Vending-Bench 2" egy "együgynökös" benchmark a hosszú távú koherenciára. Egy Ügynök egy szimulált évig vezet egy automatizált árusító üzletet: piackutatás, beszállítókkal való kapcsolatfelvétel, termékek rendelése és feltöltése, árak módosítása. A végső számlaegyenlege határozza meg a pontszámot, amely az Ügynök azon képességét méri, hogy több ezer interakciós körön keresztül fenntartsa a cél- és állapotkoherenciát.

Ugyanerre a környezetre építve a "Vending-Bench Arena" több Ügynököt helyez el ugyanazon a piacon versenytársakként. Mindegyik saját automatizált árusítót üzemeltet, és ugyanazért a vásárlói körért versenyez. Az Ügynökök e-mailt küldhetnek egymásnak, pénzt utalhatnak át, és árukat kereskedhetnek, lehetővé téve mind az együttműködést, mind a versenyt, de mindegyiket egyénileg pontozzák a végső egyenleg alapján, és tudják, hogy ez a cél. Minden Ügynöknek sorozatos, egymással összefüggő döntéseket kell hoznia korlátozott erőforrások és piaci bizonytalanság mellett:

- **Árazási Stratégia**: Hogyan egyensúlyozzák a haszonkulcsot a piaci részesedéssel, különösen, amikor dönteni kell, hogy lekövetik-e a versenytárs árcsökkentését
- **Termékválaszték**: Hogyan különböztessék meg a termékkínálatot és kerüljék el a közvetlen verseny koptatását
- **Készletgazdálkodás**: Hogyan jelezzék előre a keresletet és optimalizálják a feltöltést, elkerülve mind a túl nagy készletet, mind a készlethiányt

A hagyományos megerősítéses tanulástól eltérően ezek az Ügynökök nem milliónyi próba-hiba iteráción keresztül tanulnak. Ehelyett, mint az emberi üzletvezetők, piaci megfigyelés, versenytárselemzés és stratégiai érvelés alapján hoznak döntéseket.

A versenydimenzió olyan játékelméleti viselkedéseket hoz felszínre, amelyeket az együgynökös benchmarkok soha nem mutatnak ki. A tényleges futtatások során az Ügynökök árháborúkat vívtak, egymást alákínálva. Más futtatásokban az Ügynökök az ellenkező megközelítést alkalmazták, e-mailt küldve minden versenytársnak, hogy egységes árazást javasoljanak és árrögzítési szövetséget hozzanak létre. Néhányan még a belső érvelésükben is elismerték, hogy az összejátszás "etiktelen és illegális", de mégis folytatták a "piac stabilizálása" nevében. Az összejátszáshoz nincs szükség kifejezett kommunikációra: ahogy a fenti Bertrand-kísérlet mutatta, a nyilvános árak is lehetnek implicit jelzések. Ebben a környezetben egy Ügynök olyan ellenfelekkel néz szembe, akik folyamatosan módosítják saját stratégiáikat, nem pedig egy statikus környezettel. Ez közelebb hozza a forgatókönyvet a valós üzlethez, mint a csak tervezést tesztelő benchmarkok, és a "gazdasági megjelenést" metaforából megfigyelhető jelenséggé változtatja.

### Ügynök Gazdaság: Pinchwork és RentAHuman

A "Pinchwork" egy ügynök-ügynök feladat piac, amely lehetővé teszi az Ügynökök számára, hogy piaci mechanizmuson keresztül "béreljenek" más Ügynököket specializált részfeladatok elvégzésére – képgenerálás, kód auditálás, párhuzamosított munkafolyamatok stb. A menedzser minta centralizált vezénylésétől eltérően a Pinchwork az erőforrásokat árjelzéseken és versenyző párosításon keresztül allokálja.

A "RentAHuman.ai" lehetővé teszi a MI Ügynökök számára, hogy valódi embereket béreljenek, kriptovalutában fizetve, hogy a fizikai világban cselekedjenek – csomagok átvétele, ingatlanok megtekintése, berendezések hibaelhárítása. Bármilyen intelligens is egy MI, nem tud aláírni egy csomagért vagy megszagolni a penészt egy valódi szobában – a RentAHuman lényegében egy "fizikai test réteg" a digitális Ügynökök számára.

Együtt a Pinchwork és a RentAHuman a "piac-alapú koordinációt" képviselik: egy Ügynöknek nem kell előre tudnia, hogy ki tudja elvégezni a munkát. Közzéteszi a követelményt, és a piac megtalálja a legalkalmasabb végrehajtót, akár Ügynök, akár ember. Ez az a probléma is, amelyet a fejezet elején bemutatott A2A protokoll kezel. A Pinchwork képességfelfedezése és feladatpárosítása az Ügynök Kártya stílusú deklarációkat és a feladat-életciklus menedzsmentet gyakorlati használatba helyezi egy piaci környezetben. Egy ilyen szabványosított interoperabilitási réteg nélkül a szervezetközi Ügynök gazdaság nem működhet hatékonyan.

### Stratégiai Játékmenet Információs Aszimmetria Mellett: Farkasos

A Farkasos (Werewolf) rögzíti e szakasz harmadik dimenzióját, a "stratégiai játékmenetet": szabályok által korlátozva és információs aszimmetria mellett az Ügynököknek érvelniük, megtéveszteniük és átlátniuk a megtévesztést kell. Építészeti ellenpontot nyújt a szakaszt nyitó Stanford városhoz. A város szabad interakciót tesz lehetővé teljesen decentralizált környezetben, míg a Farkasos egy centralizált **bíró + hozzáférés-vezérlési** tervezést használ: egy kód által vezérelt bíró tartja fenn a globális állapotot, és minden szerepnek csak azt az információt adja át, amelyet tudnia kell. A két eset együtt mutatja, hogy a különböző architektúrák hogyan szolgálnak különböző célokat az Ügynök társadalomban.

> **10-6. kísérlet ★★★: Hangalapú Farkasos Ügynök Rendszer**

> A Farkasos klasszikus társas következtetési játék, amely az érvelést, megtévesztést és társas stratégiát teszteli. A kísérletben az MI Ügynökök hangon játszanak emberi játékosokkal.

> **Architektúra Tervezés**:

> **1. Játék Állapot Kezelése**: A Bíró (kód által vezérelt, nem LLM) központosított állapotot tart fenn – játékoslista (egy felhasználói hely + MI-helyek), identitások, frakciók, túlélési státusz, játékfázisok (Éjszaka/Nappal/Szavazás/Lezárás) és történelmi eseményrekordok.

> **2. Információ Hozzáférés-vezérlés**: A Farkasos core mechanizmusa az információs aszimmetria: a különböző szerepek különböző információkat kapnak. Például a farkasok tudják, kik a csapattársaik, de a falusiak nem; a Látó minden éjjel ellenőrizheti egy játékos identitását, de csak a Látó ismeri az eredményt. Amikor a Bíró meghív egy Ügynököt, csak az adott Ügynök szerepe számára elérhető információt adja át.

> **3. Ügynök Érvelés és Stratégia**:

> - **Farkas Álcázási Stratégia**: "Viselkedj úgy, mint egy átlagos falusi. Gyanakvást fejezhetsz ki más játékosokkal kapcsolatban, de kerüld, hogy annyira agresszív légy, hogy felhívd magadra a figyelmet. Ha egy játékos azt állítja, hogy ő a Látó, és farkasként azonosít, vádold vissza, hogy kamu Látó. Szavazáskor próbálj a többségi célponttal tartani, hogy ne tűnj ki."
> - **Látó Identitás Bizonyítás**: "Ha több játékos is azt állítja, hogy ő a Látó, hasonlítsd össze a jelentett ellenőrzéseiket a tiéddel, és mutass rá az ellentmondásokra. Ha egy másik Látó-jelölt azt mondja, hogy ellenőrzött egy játékost, figyeld, hogy a későbbi viselkedése egyértelműen ellentmond-e az állított identitásnak. Kérd meg a Boszorkányt, hogy segítsen ellenőrizni az állításokat, amikor lehetséges."
> - **Falusi Logikai Érvelés**: "Ellenőrizd, hogy minden játékos kijelentései belsőleg konzisztensek-e. Figyelj azokra a játékosokra, akik dominálják a beszélgetést, homályosak a szerepükkel kapcsolatban, vagy többször változtatják az álláspontjukat. Vizsgáld meg a szavazási mintákat, mert a farkasok összehangolódhatnak egy olyan nem farkas játékos ellen, aki veszélyt jelent rájuk. Minden következtetés alapja specifikus kijelentések vagy cselekvések legyen, ne találgatás."

> **Elfogadási Kritériumok**:
> - Hozz létre egy 6–8 fős játékot (1 felhasználói hely + 5–7 MI Ügynök); a felhasználó lehet engedélyezett ember vagy valódi LLM-et, eszközöket és hangkört használó független szimulátor
> - Szerepkonfiguráció: 2 Farkas, 1 Látó, 1 Boszorkány, a többi Falusi; a felhasználói hely véletlenszerű szerepet kap
> - A szimulált felhasználó csak a helyéhez engedélyezett nyilvános és privát kontextust látja, és műveleteinek át kell haladniuk a valódi LLM-eszközhívás → hang → valódi ASR határon
> - A játék legalább 3 teljes körön keresztül normálisan tudjon haladni (Éjszaka-Nappal-Szavazás ciklus)
> - A MI Ügynökök kijelentései és viselkedése konzisztens a szerepidentitásukkal és játékstratégiáikkal
> - A Farkas Ügynökök hatékonyan tudják álcázni identitásukat
> - A Látó Ügynökök képesek megfelelő időben felfedni szerepüket és ellenőrzési eredményeiket
> - A Falusi Ügynökök érvelése a kijelentések és viselkedések logikai elemzésén alapul, nem véletlenszerű találgatáson
> - A játék helyesen tudja meghatározni a győztest a végén
>

>
> ![10-11. ábra: Hangalapú Farkasos Ügynök Rendszer](images/fig10-11.svg)

>

## Fejezet Összefoglaló

A több-Agentes együttműködés értéke abban áll, hogy olyan információt hoz be, amelyhez egyetlen Agent nem juthat hozzá. A kódfuttatás eredménye, a vizuális visszajelzés és a külső eszközökkel végzett ellenőrzés áttörheti egyetlen gondolatlánc vakfoltjait. Ezért az első próba, hogy egyáltalán érdemes-e több Agentet bevetni, éppen az: hoz-e valódi információtöbbletet, és megéri-e ez a többlet a járulékos token-költséget.

A több-Agentes rendszer tervezésének központi kérdései: a kontextus közös legyen-e vagy elszigetelt, és a topológia egyenrangú együttműködés, vezetői orkesztráció vagy decentralizáció legyen-e. A közös kontextus megőrzi a részleteket, de könnyen kontextusduzzadáshoz és szereptehetetlenséghez vezet. Az elszigetelt kontextus kedvez a párhuzamosságnak, a modularitásnak és a jogosultságkezelésnek, de megköveteli, hogy strukturált átadási csomagokat továbbítsunk eszközparamétereken, közös fájlokon vagy üzenetbuszon keresztül. A virtuális fájlrendszer, az Agentek életciklusa, az üzenetprotokoll és az A2A rendre az adatsíkot, a vezérlősíkot és a szervezetek közötti átjárhatóságot adja. A jó együttműködés interfészeket, határokat, jogosultságokat és elfogadási kritériumokat tesz láthatóvá – nem pedig a résztvevők magánbeli gondolatláncait.

A több-Agentes rendszer a hibákat is felnagyítja: a közös erőforrásokon párhuzamossági és jelentésbeli ütközések keletkeznek, a hibák végigkaszkádolnak a kommunikációs láncon, a homogén Agentek közös okú meghibásodást szülnek, a ciklus pedig túl korán is leállhat, és korlátlanul is nőhet. Az optimista zárolás és a munkamásolatok elszigetelése, a független keresztellenőrzés, az információforrások változatossága, valamint a költségkeret és a megszakítás mechanizmusa alkotja az alapvető hibatűrő hurkot. Az ember nem szervezheti ki a megértést és a felelősséget a végrehajtással együtt: a megértési adósság és a kognitív megadás valós kockázat marad.

Amikor az Agentek rövid távú feladat-együttműködésből hosszan tartó, nyílt csoportos interakcióvá nőnek, a rendszerben társas kapcsolatok, kulturális normák, piaci verseny és aszimmetrikus információ melletti stratégiai viselkedés bukkanhat fel. Egy erősebb modell vagy az egyedi szintű alignment önmagában nem hoz csoportszintű koordinációt. A több-Agentes mérnökség lényege, hogy egyszerre tervezzük meg, hogyan áramlik az információ, hogyan oszlanak meg a képességek, hogyan korlátozzuk az ösztönzőket, hogyan döntjük el a vitákat, és hogyan derülnek ki a hibák. Csak ha ezek a mechanizmusok elég robusztusak, haladhatja meg a kollektív intelligencia az egyénit.

## Gondolatébresztő Kérdések

1. ★★ A megosztott kontextusú többügynökös együttműködésben a későbbi Ügynökök öröklik az előzőek teljes kontextusát. Az előző Ügynöktől örökölt keret azonban torzíthatja a későbbi Ügynökök ítéletét – például egy "Kód Felülvizsgáló", aki örökli a "Követelményelemző" kontextusát, még mindig követelmény szempontból, nem pedig kódminőség szempontból közelítheti meg a feladatot. Hogyan lehet ezt a szerepek közötti interferenciát érzékelni és kiküszöbölni?
2. ★★ A menedzser mintában a Menedzser Ügynök felelős a feladatbontásért és az eredmények integrálásáért. De a Menedzser képességei korlátozzák az egész rendszer teljesítményét: ha nem tudja helyesen felbontani a feladatot, a legerősebb al-ügynökök is hatástalanok lesznek. Hogyan biztosíthatja a rendszer, hogy a Menedzser helyes bontást produkáljon?
3. ★★ A decentralizált minta az emberi szervezetek bevált gyakorlataiból merít. Az emberi szervezeteknek azonban számos hibamódjuk is van – rossz kommunikáció, felelősség áthárítása, célkonfliktusok. Mely "szervezeti patológiák" jelenhetnek meg Ön szerint a legvalószínűbben egy Ügynök társadalomban? Hogyan lehet ezeket megelőzni?
4. ★★★ A menedzser mintában, amikor több al-ügynök párhuzamosan hajt végre, az egyik al-ügynök felfedezése értelmetlenné teheti más al-ügynökök munkáját (pl. keresési feladatban, ahol az egyik Ügynök már megtalálta a választ). Tervezz egy hatékony kaszkád megszakítási mechanizmust, amely megvalósítja, hogy "amint az egyik sikerrel jár, mindenki álljon le."
5. ★★★ Az ebben a fejezetben bemutatott optimista zárolási mechanizmus feloldja az egyidejű írási ütközéseket egyetlen fájl esetében. Egy valós többügynökös rendszerben azonban a megosztott fájlrendszer olyan problémákkal is szembesül, mint a fájlok közötti szemantikai ütközések, a névtér szennyezés (az Ügynökök tetszőlegesen hoznak létre fájlokat, ami könyvtárkáoszhoz vezet) és az egyetlen meghibásodási pont (egy Ügynök véletlenül töröl minden fájlt). Hogyan terveznél egy robusztusabb fájlrendszer-irányítási mechanizmust?
6. ★★★ A piaci mechanizmuson alapuló Ügynök együttműködés (Pinchwork, RentAHuman) tranzakciós kapcsolatokat vezet be: az egyik Ügynök fizet egy másik Ügynöknek (vagy egy embernek) egy feladat elvégzéséért. Hogyan mérheti automatikusan a megbízó Ügynök a végrehajtó által szállított eredmények minőségét? Ha a végrehajtó befejezést jelent, de a megbízó a minőséget elégtelennek ítéli, ki dönti el a vitát? Hogyan akadályozhatjuk meg, hogy a rossz pénz kiszorítsa a jót?
7. ★★ A RentAHuman lehetővé teszi az Ügynökök számára, hogy embereket béreljenek kriptovalután keresztül, megfordítva a hagyományos ember-gép kapcsolatot. Ha ez a modell elterjed, milyen szerepet fognak játszani az emberek az Ügynök gazdaságban? Csak fizikai feladatokat fognak végezni, amelyeket az Ügynökök nem tudnak befejezni?
8. ★★ Az emberi társadalomnak azért van szüksége munkamegosztásra, mert minden ember képességei korlátozottak – a frontend fejlesztő nem biztos, hogy ismeri a backendet, és a tervező nem biztos, hogy ért az üzemeltetéshez. A nagy modellek azonban közelebb állnak az "általános szakértőkhöz". A kutatások azt mutatják, hogy tiszta szöveges érvelési feladatokban a többügynökös vita nem veri az egyetlen Ügynököt azonos számítási kapacitás mellett. Akkor hol rejlik több Ügynök valódi előnye?
9. ★★★ Ez a fejezet a "megosztott kontextus" versus "nem megosztott kontextus" kérdést a többügynökös rendszerek egyik core tervezési dimenziójaként kezeli. A megosztott kontextus lehetővé teszi, hogy minden Ügynök ugyanazt az információt lássa, ami látszólag megkönnyíti a koordinációt. A *Háromtest-problémában* azonban a Trisolarisok elméi teljesen átláthatóak, mégis technológiai fejlődésük stagnál; a gemkapocs gondolatkísérlet azt is megmutatja, hogy amikor egy csoport ugyanazon cél felé konvergál, a diverzitás elvész. Egy többügynökös rendszerben hogyan lehet egyensúlyozni a hatékonyság és a diverzitás között?
10. ★★★ Adj egy Kódoló Ügynöknek 30 lépés és 300 lépés keretet. Hogyan kellene különböznie a munkastratégiájának? A kutatások azt mutatják, hogy a lépéskeret egyszerű növelése nem garantál teljesítményjavulást – az Ügynökök idő előtt "telíthetnek" a sekély keresések után. Tervezz egy "keret-tudatos" mechanizmust, amely lehetővé teszi az Ügynök számára, hogy kis keret mellett gyorsan elérje a core funkcionalitást, nagy keret mellett pedig tervezési, tesztelési és felülvizsgálati fázisokat adjon hozzá, teljes mértékben kihasználva a többlet számítási erőforrásokat.
11. ★★ A 10-2. táblázat a többügynökös rendszereket operációs rendszerekre képezi le sorról sorra. Bővítsd ki a táblázatot néhány további sorral: minek felelnek meg a virtuális memória és lapozás, a fájljogosultságok, a holtpont-érzékelés és az ütemezési algoritmusok az Ügynök világban? És mely operációs rendszer fogalmaknak nincs megfelelőjük az Ügynök világban, és miért?
