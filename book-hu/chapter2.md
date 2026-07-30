# Kontextustervezés

Az 1. fejezet a kontextust az ügynök munkainformáció-halmazaként határozta meg a döntés pillanatában. Ennek a kontextusnak a megtervezése és kezelése – amit "kontextustervezésnek" nevezünk – központi jelentőségű a hatékony ügynökök építésében. A gyakorlatban a kontextus mindent magában foglal, amit a modell egy adott interakció során kap: a beszélgetés történetét, a rendszerutasításokat, az eszközdefiníciókat, a visszakeresett dokumentumokat, a futásidejű állapotot és egyéb feladatspecifikus információkat. Az 1. fejezetben bevezetett Hám nézőpontjából a kontextustervezés valósítja meg a Hám "Kontextus és Eszközök" rétegének nagy részét: eldönti, hogy az ügynök milyen információt lát az egyes döntési pontokon, és hogy az információ hogyan van megszervezve. A jó kontextus kialakítás megadja a modellnek a megfelelő hátteret, korlátokat és műveleti interfészeket, hogy általános érvelési képessége hatékonyan alkalmazható legyen a feladatra.

![Figure 2-1: A Kontextusablak Összetételének Áttekintése](images/fig2-1.png)

## A Kontextus: Az Ügynöki Képesség Felső Korlátja

A nagy nyelvi modellek erős eredményeket érnek el szabványos benchmarkokon, de a valós üzleti környezetben gyakran alulteljesítenek. Az ok egyértelmű: a modell képességei általános célúak, míg a konkrét feladatok helyi ismeretektől függenek, mint a termékarchitektúra, az üzleti szabályok, a működési korlátok és a belső konvenciók. Ez az információ általában hiányzik a modell paramétereiből.

Képzeljünk el egy kiemelkedő képességű mérnököt, aki egy új csapathoz csatlakozik. Lehet, hogy mély elméleti tudással és erős programozási képességgel rendelkezik, de még nem ismeri a termékarchitektúrát, az üzleti logikát, a technikai adósságot vagy a csapat normáit. Ha a kulcsfontosságú architekturális döntések szétszórva vannak az egyének emlékezetében, és a kódbázis gyengén dokumentált, még egy kivételes mérnök is nehezen tud gyorsan értéket szállítani. A mai MI-ügynökök ugyanezzel a problémával szembesülnek.

Vegyünk egy Kódolási Ügynököt. Ugyanarra az utasításra, "Segíts kijavítani ezt a hibát," a kontextus minősége, amelyet az ügynök kap, meghatározza, hogy képes-e elvégezni a feladatot:

- "Kód kontextus": A kódbázis struktúrája, a modulok felelősségi körei, a központi adatstruktúrák és a kódolási szabványok. Ezen információ nélkül az ügynök olyan kódot állíthat elő, amely szintaktikailag helyes, de nem konzisztens a projekt stílusával vagy architektúrájával.
- "Folyamatkövetelmények": Git elágazási stratégia, commit konvenciók, review folyamat és CI/CD követelmények. Ezen információ nélkül az ügynök tesztelés nélküli kódot commitolhat közvetlenül a fő ágba.
- "Környezeti konfiguráció": Fejlesztői környezet beállítása, tesztadatbázis kapcsolati sztringek, staging telepítési eljárások és API-kulcs kezelési gyakorlatok. Ezen információ nélkül egy lokálisan működő javítás azonnal meghiúsulhat a tesztkörnyezetben.

Ez a három kategória – kód, folyamat és környezet – alkotja a minimális kontextust, amelyre egy ügynöknek szüksége van a hatékony munkához. A modell eredendő képessége csak az alap; a kontextus határozza meg az ügynöki képesség felső korlátját. Egy mérsékelten képzett modell jól szervezett kontextussal gyakran felülmúlhat egy erősebb modellt, amely elégtelen kontextussal dolgozik.

A kontextustervezés ezért központi fontosságú a hatékony ügynökök építésében a mai modellekkel. Nem csupán arról van szó, hogy több szöveget adjunk a prompthoz. Szisztematikus tervezést, szervezést és a háttérismeretek biztosítását igényli, amelyre a modellnek szüksége van a feladat elvégzéséhez.
A kontextustervezés technikai probléma, de még alapvetőbben szervezeti probléma. Sok csapatban a kritikus tudás hallgatólagos marad: az architekturális döntések a senior mérnökök emlékezetében élnek, az üzleti szabályokat informálisan adják tovább, és a fontos kontextus privát chat naplókba temetve. Ha maga a csapat is gyenge információs környezet, akkor még egy erős MI-ügynök is korlátozott lesz.

Azok a csapatok, amelyek hatékonyan dolgoznak távoli környezetben, gyakran biztosítanak hatékony környezetet az MI-ügynökök számára is. A nyílt forráskódú projektek, mint a Linux kernel, tanulságos példák: a világban szétszórtan élő fejlesztők több mint harminc éve tartják fenn a projektet. Ez azért működik, mert a projekt átlátható, dokumentáció-vezérelt kommunikációs kultúrával rendelkezik. A megbeszélések nyilvánosak, a döntéseket rögzítik, és az újoncok megérthetik a kód fejlődését a történelem olvasásával. Ugyanez a munkastílus természetesen teremt MI-barát környezetet: az információ nyilvános, visszakereshető és strukturált.

Kezeljük az MI-ügynököt úgy, mint egy új csapattagot, minden alkalommal, amikor egy feladatot elkezd. Megfelelő háttérismeretekkel kiváló minőségű munkát tud végezni; enélkül intelligenciájának nagy része kárba vész. Ezért egy MI-natív csapat építése elsősorban dokumentációs erőfeszítés, nem csupán új eszközök telepítésének kérdése.

Az OpenAI kutatója, Jiayi Weng, világosan kifejezte ezt a pontot: **"Emberek és modellek számára egyaránt a legfontosabb dolog a Kontextus."** Saját munkájára reflektálva megjegyezte: "A munkám az OpenAI-nál nem olyan nehéz. Ha valaki másnak meg lenne az összes kontextusom, ő is meg tudná csinálni." Ugyanez az elv vonatkozik az ügynökökre is: az ügynöki képesség felső korlátját nem csak a modell mérete határozza meg, hanem a kontextus teljessége és pontossága, amelyet az egyes döntési pontokon biztosítanak. Weng azt is megfigyelte, hogy a csapatmunka központi problémája a kontextus inkonzisztenciája, és hogy az MI egyik oka annak, hogy rövid távon nem helyettesítheti az embereket, az, hogy az MI és az emberek nem osztoznak ugyanazon a környezeten. A kontextustervezés pontosan ezt a problémát kezeli: hogyan lehet szisztematikusan eljuttatni a modellhez a strukturált háttérismereteket, amelyekre az ügynöknek szüksége van.

A következő kérdés, hogy ezek a kontextuális információk hogyan jutnak el az LLM-hez technikai szinten.

## Hogyan Hívják az Ügynökök az LLM-eket: A Kontextus API-szintű Szerkezete

Ez a szakasz az OpenAI Chat Completions API-ját használja konkrét példaként. Az Anthropic, a Google és más szolgáltatók részleteikben eltérnek, de az ügynökök felé nyújtott API-ik hasonló mintát követnek: minden modellhívás egy strukturált beszélgetéstörténetből és egy sor elérhető eszközdefinícióból épül fel. Ennek a struktúrának a megértése az alapja a fejezet későbbi részében tárgyalt kontextustervezési technikáknak.

### A Négy Üzenetszerep

A Chat Completions-stílusú API-kban a bemenet magja egy "üzenetlista", általában `messages` néven. Minden üzenetnek van egy `role` mezője, amely megmondja a modellnek, hogyan értelmezze az üzenetet és honnan származik:

- "system": Fejlesztő által írt utasítások, amelyek meghatározzák az ügynök identitását, viselkedését, korlátait és munkafolyamatát. A modell ezt magas prioritású utasításként kezeli. A legtöbb beszélgetésben a rendszerüzenet egyszer jelenik meg az üzenetlista elején.
- "user": A végfelhasználó bemenete, amely azt a kérést képviseli, amelyet az ügynöknek kezelnie kell.
- "assistant": Korábbi modellkimenetek, beleértve a természetes nyelvű válaszokat és az eszközhívási kérelmeket. Többfordulós interakciókban ezek az üzenetek szerepelnek a későbbi kérésekben, hogy a következő állapotmentes modellhívás hozzáférjen az előző trajektóriához.
- "tool": Az ügynök-keretrendszer által végrehajtott eszközök után visszaadott eredmények. Minden eszközeredmény a megfelelő eszközhívás `tool_call_id`-jéhez van kapcsolva, lehetővé téve a modell számára, hogy minden eredményt a létrehozó kéréshez társítson.

Az eszközdefiníciók nem üzenetek. Egy külön `tools` mezőben vannak megadva, amely deklarálja a modell számára elérhető eszközöket és meghatározza az egyes eszközök által elfogadott paramétereket.

### Egymenetű Kérés: A Legegyszerűbb API Hívás

![Figure 2-2: Egymenetű API Hívás Kérés- és Válaszszerkezete](images/fig2-2.png)

Kezdjük a legegyszerűbb esettel: egyetlen kérés eszközhívások nélkül. A felhasználó megkérdezi: "Hello, ki vagy te?" A példa egy lokálisan telepített Qwen3-0.6B modellt használ, összekapcsolva a későbbi szakasz lokális LLM telepítési kísérletével. A példában szereplő időbélyegek csak demonstrációs célokat szolgálnak, és nem kapcsolódnak a könyv idővonalához.

```javascript
// ═══ Az ügynök-keretrendszer által összeállított kérés ═══
{
  "model": "Qwen3-0.6B",
  "messages": [
    {
      "role": "system",                           // ← Fejlesztő által írva
      "content": "You are a helpful coding assistant. Follow user instructions."
    },
    {
      "role": "user",                              // ← Felhasználói bemenet
      "content": "Hello, who are you?"
    }
  ]
}
```

```javascript
// ═══ Az API által visszaadott válasz ═══
{
  "choices": [{
    "message": {
      "role": "assistant",                         // ← Modell által generált
      "content": "Hi! I'm a coding assistant. I can help you write code, debug issues, and explain technical concepts. How can I help?"
    }
  }]
}
```

Ez a kérés csak két üzenetet tartalmaz: egy rendszerüzenetet a fejlesztő által írt szabályokkal és egy felhasználói üzenetet a felhasználó bemenetével. A modell egy asszisztens üzenetet ad vissza válaszként. Ez a legalapvetőbb LLM API interakciós minta: **minden hívás állapotmentes, ezért a kérés üzenetlistájának tartalmaznia kell minden információt, amire a modellnek szüksége van**.

### Többfordulós Interakció Eszközhívásokkal: Az Ügynök Magciklusa

A valós ügynök-munkafolyamatok általában összetettebbek, mint egy egymenetű Kérdés-Válasz. Amikor egy felhasználó megkérdezi: "Mi a jelenlegi idő és időjárás Vancouverben?", a modellnek hozzá kell férnie dinamikus külső információkhoz: a jelenlegi időhöz és a legfrissebb időjáráshoz. A következő példa végigvezeti az ügynök-keretrendszer és a modell közötti egyes interakciókat.

![Figure 2-3: Két Eszközhívás Teljes Interakciós Sorozata](images/fig2-3.png)

**Első API hívás – Az ügynök-keretrendszer elküldi a kezdeti kérést:**

```javascript
// ═══ Az ügynök-keretrendszer által összeállított kérés (1. hívás) ═══
{
  "model": "Qwen3-0.6B",
  "messages": [
    {
      "role": "system",                           // ← Fejlesztő által írva
      "content": "You are a helpful assistant. Use the provided tools to get real-time information when needed."
    },
    {
      "role": "user",                              // ← Felhasználói bemenet
      "content": "What's the current time and weather in Vancouver?"
    }
  ],
  "tools": [                                       // ← Fejlesztő által definiált eszközök
    {
      "type": "function",
      "function": {
        "name": "get_current_time",
        "description": "Get the current date and time in a specific timezone",
        "parameters": {
          "type": "object",
          "properties": {
            "timezone": { "type": "string", "description": "Timezone name, e.g. America/Vancouver" }
          }
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "Get the current weather for a specific city",
        "parameters": {
          "type": "object",
          "properties": {
            "city": { "type": "string", "description": "City name" },
            "unit": { "type": "string", "enum": ["celsius", "fahrenheit"] }
          }
        }
      }
    }
  ]
}
```

**A modell visszaad egy eszközhívási kérelmet (nem egy végső választ):**

```javascript
// ═══ Az API által visszaadott válasz (a modell úgy dönt, hogy eszközöket hív) ═══
{
  "choices": [{
    "message": {
      "role": "assistant",                         // ← Modell által generált
      "content": null,                             // Nincs szöveges válasz
      "tool_calls": [                              // A modell két eszközhívást kér
        {
          "id": "call_abc123",
          "type": "function",
          "function": {
            "name": "get_current_time",
            "arguments": "{\"timezone\": \"America/Vancouver\"}"
          }
        },
        {
          "id": "call_def456",
          "type": "function",
          "function": {
            "name": "get_weather",
            "arguments": "{\"city\": \"Vancouver\", \"unit\": \"celsius\"}"
          }
        }
      ]
    }
  }]
}
```

A modell még nem válaszol a felhasználó kérdésére. Ehelyett két "eszközhívási kérést" ad vissza: egyet a jelenlegi időhöz és egyet az időjáráshoz. Mivel ezek a kérések függetlenek, az ügynök-keretrendszer párhuzamosan is végrehajthatja őket. **A modell kiadja a hívási kéréseket; az ügynök-keretrendszer végzi el a tényleges végrehajtást.** Ez a felelősségi kör megosztása központi az ügynökarchitektúrában: a modell eldönti, hogy melyik eszközt hívja és milyen argumentumokat adjon át, míg a keretrendszer meghívja az API-kat, futtatja a kódot és visszaadja az eredményeket.

**Az ügynök-keretrendszer végrehajtja az eszközöket, majd elindít egy második API hívást:**

Miután megkapta a modell eszközhívási kéréseit, az ügynök-keretrendszer végrehajtja a két eszközt (például egy idő API és egy időjárás API meghívásával), majd elküldi a **teljes beszélgetéstörténetet az eszköz-végrehajtási eredményekkel együtt** vissza a modellnek:

```javascript
// ═══ Az ügynök-keretrendszer által összeállított kérés (2. hívás) ═══
{
  "model": "Qwen3-0.6B",
  "messages": [
    {
      "role": "system",                           // ← Ugyanaz, mint az 1. hívásnál
      "content": "You are a helpful assistant. Use the provided tools to get real-time information when needed."
    },
    {
      "role": "user",                              // ← Ugyanaz, mint az 1. hívásnál
      "content": "What's the current time and weather in Vancouver?"
    },
    {
      "role": "assistant",                         // ← Modell kimenete az 1. hívásból, szó szerint belefoglalva
      "content": null,
      "tool_calls": [
        { "id": "call_abc123", "function": { "name": "get_current_time", "arguments": "{\"timezone\": \"America/Vancouver\"}" } },
        { "id": "call_def456", "function": { "name": "get_weather", "arguments": "{\"city\": \"Vancouver\", \"unit\": \"celsius\"}" } }
      ]
    },
    {
      "role": "tool",                              // ← Ügynök-keretrendszer által generált (eszköz-végrehajtási eredmény)
      "tool_call_id": "call_abc123",
      "content": "{\"timezone\": \"America/Vancouver\", \"datetime\": \"2025-09-13T05:18:47\", \"day_of_week\": \"Saturday\"}"
    },
    {
      "role": "tool",                              // ← Ügynök-keretrendszer által generált (eszköz-végrehajtási eredmény)
      "tool_call_id": "call_def456",
      "content": "{\"city\": \"Vancouver\", \"temperature\": 13.2, \"unit\": \"celsius\", \"conditions\": \"clear\", \"humidity\": 93}"
    }
  ],
  "tools": [ ... ]                                 // ← Ugyanazok az eszközdefiníciók, mint fent, itt kihagyva
}
```

Három kulcsfontosságú részlet van itt:

1. **A második kérés tartalmazza a teljes beszélgetéstörténetet az első kérésből** — a rendszerüzenetet, a felhasználói üzenetet, az eszközhívásokat tartalmazó asszisztens üzenetet és az újonnan hozzáadott eszközeredményeket. Ez illusztrálja az API állapotmentes természetét: az ügynök-keretrendszernek minden kérésben szerepeltetnie kell a releváns történetet.
2. **Az első asszisztens üzenet szó szerint vissza van illesztve az üzenetlistába** — ez lehetővé teszi a következő modellhívás számára, hogy hozzáférjen az előző hívásban hozott eszközhívási döntésekhez.
3. **Az eszközüzenetek a `tool_call_id`-n keresztül kapcsolódnak a megfelelő eszközhívásokhoz** — ez megmondja a modellnek, hogy melyik eredmény melyik kért híváshoz tartozik.

**A modell az eszközeredmények alapján generálja a végső választ:**

```javascript
// ═══ Az API által visszaadott válasz (végső válasz) ═══
{
  "choices": [{
    "message": {
      "role": "assistant",                         // ← Modell által generált
      "content": "It's currently 5:18 AM on Saturday, September 13, 2025 in Vancouver.

Weather: 13.2°C with clear skies and 93% humidity. It's quite cool this morning - you might want to grab a jacket."
    }
  }]
}
```

Ezúttal a modell nem ad vissza `tool_calls`-t; szöveges választ ad vissza, mert az eszközeredmények elegendő információt nyújtanak a felhasználó kérdésének megválaszolásához. Ha több információra van szükség (például ha a felhasználó megkérdezi: "És Tokió?"), a modell ismét `tool_calls`-t adhat vissza, és az ügynök-keretrendszer megismétli ugyanazt a ciklust: végrehajtja az eszközöket, visszaküldi az eredményeket, és ismét meghívja a modellt. **Ez a "kérés → eszközhívás → végrehajtás → eredmények visszaküldése → következő kérés" ciklus az 1. fejezetben bevezetett ReAct hurok API-szintű megvalósítása.**

### Az Ügynök Magciklusának Megvalósítása Kódban

Most, hogy a JSON struktúra világos, összekapcsolhatjuk a fenti lépéseket Pythonban. Az alábbiakban egy minimális ügynök megvalósítás látható, amely egyetlen hurok köré épül:

```python\nfrom openai import OpenAI

client = OpenAI()

# ── Eszközdefiníciók ──\ntools = [\n    {\n        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current date and time in a specific timezone",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {"type": "string", "description": "Timezone name, e.g. America/Vancouver"}
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a specific city",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name"},
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                },
            },
        },
    },
]

# ── Eszköz-végrehajtási függvény (csonkolt eredményekkel; egy valós
#    implementációnak ki kell elemeznie a JSON `arguments` mezőt és tényleges API-kat kell hívnia) ──
def execute_tool(name, arguments):
    if name == "get_current_time":
        return '{"datetime": "2025-09-13T05:18:47", "day_of_week": "Saturday"}'
    elif name == "get_weather":
        return '{"temperature": 13.2, "unit": "celsius", "conditions": "clear", "humidity": 93}'

# ── Kezdeti üzenetlista ──
messages = [
    {"role": "system", "content": "You are a helpful assistant. Use tools to get real-time information when needed."},
    {"role": "user", "content": "What's the current time and weather in Vancouver?"},
]

# ── Ügynök magciklus ──
# A production kódnak szüksége van egy max_iterations korlátra itt: ahogy a fejezet
# későbbi részében tárgyaljuk, az ügynökök elakadhatnak és ugyanazokat az eszközhívásokat
# ismételhetik a végtelenségig
while True:
    response = client.chat.completions.create(
        model="Qwen3-0.6B", messages=messages, tools=tools
    )
    assistant_message = response.choices[0].message

    # Modell válaszának hozzáfűzése az üzenetlistához (akár szöveg, akár eszközhívások)
    messages.append(assistant_message)

    # Ha nincs kért eszközhívás, a modell előállította a végső választ
    if not assistant_message.tool_calls:
        print(assistant_message.content)
        break

    # A modell által kért összes eszköz végrehajtása, eredmények hozzáfűzése
    for tool_call in assistant_message.tool_calls:
        result = execute_tool(tool_call.function.name, tool_call.function.arguments)
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result,
        })
    # Vissza a hurok tetejére, modell újrahívása a frissített üzenetlistával
```

A huroknak egy fő elágazása van: **ha a modell `tool_calls`-t ad vissza, hajtsa végre az eszközöket és folytassa; egyébként adja ki az eredményt és lépjen ki.** E folyamat során a `messages` lista folyamatosan növekszik, ahogy minden kör hozzáfűzi a modell válaszát és az eszköz-végrehajtási eredményeket.

A `messages` lista a következőképpen változik a körök során:

"Kezdeti állapot (az első hívás előtt):"
```
messages = [
  { role: "system",  content: "You are a helpful assistant..." },     # Fejlesztő által írva
  { role: "user",    content: "What's the current time and weather in Vancouver?" },  # Felhasználói bemenet
]
```

**Az első hívás után (a modell eszközhívásokat ad vissza):**
```
messages = [
  { role: "system",    content: "..." },
  { role: "user",      content: "What's the current time..." },
  { role: "assistant", tool_calls: [get_current_time, get_weather] },  # + Modell által generált
  { role: "tool",      tool_call_id: "call_abc", content: "{time...}" },  # + Keretrendszer által végrehajtott
  { role: "tool",      tool_call_id: "call_def", content: "{weather...}" },  # + Keretrendszer által végrehajtott
]
```

**A második hívás után (a modell visszaadja a végső választ, a hurok véget ér):**
```
messages = [
  { role: "system",    content: "..." },
  { role: "user",      content: "What's the current time..." },
  { role: "assistant", tool_calls: [get_current_time, get_weather] },
  { role: "tool",      tool_call_id: "call_abc", content: "{time...}" },
  { role: "tool",      tool_call_id: "call_def", content: "{weather...}" },
  { role: "assistant", content: "It's currently Saturday, Sep 13, 2025 in Vancouver..." },  # + Végső válasz
]
```

Ez a folyamat megmutatja, hogy **az ügynök-keretrendszer egyik központi feladata az üzenetlista karbantartása**: üzenetek hozzáfűzése a megfelelő időben és a releváns történet elküldése a modellnek. A fejezet kontextustervezési technikái nagyrészt arról szólnak, hogy hogyan lehet javítani e lista tartalmát és szerkezetét.

### Hogyan Épül Fel a Kontextus API-szinten

A fenti példa bemutatja a kontextus teljes összetételét minden alkalommal, amikor az ügynök meghívja a modellt:

![Figure 2-4: A Kontextus Összetétele Minden Alkalommal, Amikor az Ügynök Meghívja a Modellt](images/fig2-4.png)

A felső rész (Rendszer Prompt + Eszközdefiníciók) változatlan marad a beszélgetés során, míg az alsó rész (beszélgetéstörténet, azaz az 1. fejezetben definiált "trajektória") minden interakcióval növekszik. Így jelenik meg az 1. fejezet öt kontextuskomponense API-szinten: a rendszer prompt és az eszközdefiníciók statikus előtagot alkotnak, míg a felhasználói üzenetek, a modellválaszok és az eszköz-végrehajtási eredmények dinamikusan növekvő üzenettörténetet alkotnak. Ez a "statikus előtag + trajektória" struktúra az alapja a későbbi KV Cache optimalizálásról, kontextustömörítésről és kapcsolódó technikákról szóló tárgyalásoknak: az előtagnak stabilnak kell maradnia, míg a későbbi trajektória-szegmensek összefoglalhatók vagy lecserélhetők, ha a kompromisszum megéri.

A fejezet hátralévő része e struktúra minden rétegét megvizsgálja: hogyan használjunk stabil statikus előtagot a következtetés gyorsítására (KV Cache), hogyan tervezzünk hatékony Rendszer Promptot (prompt tervezés), hogyan akadályozzuk meg, hogy külső tartalom eltérítse a kontextust (prompt injekció elleni védelem), hogyan töltsünk be speciális tudást igény szerint (Ügynöki Készségek), hogyan injektáljunk dinamikus állapotot a beszélgetés végére (Ügynöki Állapotsáv), és hogyan tömörítsük a beszélgetéstörténetet, ha az túl nagyra nő (tömörítési stratégiák).

> **Kísérlet 2-1 ★: Lokális LLM Szolgáltatás Telepítése és Eszközhívás**
>
>
> ![Figure 2-5: Lokális LLM Eszközhívási Architektúra](images/fig2-5.png)
>
>
> Ennek a kísérletnek két célja van: először is, egy kis modell eszközhívási képességének megfigyelése, másodszor pedig a nyers token adatfolyam (gondolkodási lánc, speciális tokenek és eszközhívási formátum) vizsgálata, amely API-szinten rejtve van. Eközben megfigyelhető a KV Cache hatása az első token idejére (TTFT), ami megalapozza a következő szakasz intuitív megértését.
>
> Mielőtt a fejezet rátérne az ügynöki kontextus mélyebb mechanikájára, ez a projekt bemutatja, hogy mire képes egy kis modell. A `local_llm_serving` projekt egy fontos pontot illusztrál: a Gondolkodási Láncra (CoT) és eszközhívásra képes modellekhez nem feltétlenül szükséges nagy paraméterszám. Még egy 0,6B paraméteres modell is képes megbízhatóan végrehajtani az eszközhívásokat, ha ésszerű prompt tervezéssel és rendszerarchitektúrával párosul.
>
> A kísérlet során az olvasóknak meg kell tudniuk figyelni:
>
> 1. "Kis Modellek Képességei": Még egy 0,6B modell is pontosan meg tudja érteni és végrehajtani az eszközhívásokat megfelelő prompt tervezéssel (a bemeneti promptok gondos megtervezésének technikája a modell viselkedésének irányításához).
> 2. "Teljesítmény": Apple M2 chipen a modell több mint 100 tokent képes generálni másodpercenként, ami elegendő a valós idejű interaktív alkalmazásokhoz. A token a szövegfeldolgozás alapegysége a modellek számára; egy kínai karakter általában 1-2 tokennek, egy angol szó általában 1-3 tokennek felel meg.
> 3. "ReAct Hurok": Figyeljük meg, hogyan oldja meg a modell az összetett problémákat az érvelés és eszközhívás több fordulóján keresztül.
> 4. "Streamelt Válaszok Előnyei": A streamelt kimenet lehetővé teszi a felhasználók számára, hogy valós időben lássák a modell érvelési folyamatát, beleértve az eszközhívásokkal kapcsolatos döntéseket és az eredmények feldolgozását.
> 5. "A KV Cache Hatása (véletlen megfigyelés)": Tartsuk változatlanul a rendszer promptot, indítsunk két egymást követő beszélgetést, és jegyezzük fel a második TTFT-jét. Ezután változtassunk meg néhány karaktert a rendszer prompt elején, indítsunk egy újabb beszélgetést, és hasonlítsuk össze a TTFT-t. A változatlan előtagú eset jelentősen gyorsabb lesz, mert eltalálja az előtag gyorsítótárat, míg a módosított előtagú esetnek újra kell számolnia a teljes előtagot. Ez a jelenség a következő szakasz témája.
>
> "A ReAct Hurok a Gyakorlatban."
>
> A projekt többlépcsős eszközhívása követi az 1. fejezetben bevezetett ReAct (Gondolkodj-Cselekedj-Figyelj meg) hurkot, ezért annak alapelveit itt nem ismételjük meg. Az előző szakasz már megmutatta ennek a folyamatnak a teljes üzenetstruktúráját az OpenAI API JSON formátumában. Lokális telepítésben a szerver (pl. vLLM vagy Ollama) ezeket az API üzeneteket a modell belső token formátumába alakítja. A `local_llm_serving` projekt lehetővé teszi az olvasók számára, hogy megvizsgálják a modell nyers bemeneti és kimeneti token adatfolyamát, beleértve a következő, API-szinten általában rejtett részleteket:
>
> "Modell Belső Érvelési Folyamata": A gondolkodási láncot támogató modellek (pl. Qwen3) először a `<think>` tagek között érvelnek, mielőtt eszközhívásokat generálnának – elemzik a felhasználói szándékot, értékelik, hogy mely eszközök alkalmasak, és megtervezik a hívási sorrendet. Ez az érvelési folyamat értékes az ügynök viselkedésének hibakereséséhez.
>
> "Kimeneti Sorrend Szerkezete": A modell kimeneti tokenjei rögzített sorrendben generálódnak – először belső érvelés (a `<think>` tageken belül), majd a szöveges válasz a felhasználónak, és végül az eszközhívási kérelem. Ennek a sorrendnek a megértése kulcsfontosságú a streamelt válaszok implementálásához: amikor a `<think>` tag megjelenik, a felület válthat egy "érvelési" állapotra; amint az első eszközhívás paraméterei teljesen legenerálódtak és érvényesítésre kerültek, a végrehajtás azonnal megkezdődhet, anélkül, hogy meg kellene várni a modell további eszközhívásainak generálását.
>
> "Párhuzamos Eszközhívások": A szakasz vancouveri idő és időjárás példájában a modell nem talált függőséget a két részprobléma között, ezért egy kimenetben két eszközhívási kérést generált. Az ügynök-keretrendszer érzékeli ezt, és párhuzamosan hajtja végre mindkét eszközt, csökkentve a teljes késleltetést.
>
> "Modell Megszüntetési Döntése": Amikor az ügynök-keretrendszer visszaküldi az eszközeredményeket, a modell eldönti, hogy van-e elegendő információja a felhasználó megválaszolásához. Ha igen, kiadja a végső választ anélkül, hogy újabb eszközhívást kérne; ellenkező esetben további eszközhívásokat ad ki, és új ReAct kört kezd.
>
> "Kísérlet Összefoglalása."
>
> A kísérlet legfontosabb tanulsága, hogy egy 0,6B modell, ésszerű prompt tervezéssel, megbízhatóan képes végrehajtani az eszközhívásokat. A modell mérete számít, de nem ez az egyetlen meghatározó tényező. Néhány high-end mobil eszköz már képes futtatni 0,6B szintű modelleket, és a készüléken futó modellek gyakorlati képességei folyamatosan javulnak. A készüléken futó ügynökök közelebb vannak, mint sokan gondolnák.
>
> Észrevehettük, hogy a modell első válaszának sebessége lelassul, miután a rendszer prompt módosításra került. Ezt a lassulást a következő szakaszban magyarázott KV Cache viselkedés okozza: az előtag megváltoztatása érvényteleníti a gyorsítótárat és újraszámolást kényszerít ki.
>

## KV Cache-barát Kontextus Tervezés

Mielőtt megvizsgálnánk a példát, tekintsük át a "KV Cache" mögötti intuíciót. Minden alkalommal, amikor a modell egy tokent generál, vissza kell hivatkoznia az előző tokenek közbenső számítási eredményeire. Ezen eredmények minden körben történő újraszámolása egyre költségesebbé válna a kontextus növekedésével. A KV Cache eltárolja a közbenső kulcs-érték állapotokat, így a későbbi számítások újra felhasználhatják őket. **A feltétel az, hogy az előtagnak teljesen változatlannak kell maradnia**: ha egyetlen karaktert is megváltoztatunk benne, az előtag gyorsítótára többé nem használható újra; a modellnek a változtatás pontjától kezdve újra kell számolnia. Egy terminológiai megjegyzés: amikor ez a szakasz "gyorsítótár találatokról" beszél a kérések között, az API szolgáltatók ezt általában Prompt Cache-nek nevezik – egy kérések közötti gyorsítótár, amely a követőmotor KV Cache-ére épül. A két szintet a szakasz végén különböztetjük meg.

Ezzel az intuícióval a fejünkben tekintsünk egy éles incidensre. Egy csapat ügyfélszolgálati ügynöke napi 100 000 beszélgetést kezelt, és a rendszer normálisan működött. Aztán egy mérnök, hogy az ügynök hozzáférjen a jelenlegi időhöz, hozzáadott egy `Current time: {{now}}` sort a rendszer prompthoz, valós időben injektálva az időbélyeget. Másnap a monitoring riasztások beindultak: a TTFT minden beszélgetés esetében 0,5 másodpercről 3-5 másodpercre nőtt, és a havi következtetési számla majdnem megduplázódott. A kód helyesnek tűnt, és a modell nem változott. A probléma a kontextusban volt.

Ez az egy időbélyeg sor érvénytelenítette a KV Cache-t minden kérésnél. A rendszer prompt most minden alkalommal más volt, arra kényszerítve a modellt, hogy az előtag kulcs-érték párjait a semmiből számolja újra (itt a "Kulcs" és az "Érték" kétféle vektor a figyelmi mechanizmusban; a 2-2. kísérlet vizuálisan demonstrálja a szerepüket). Ez a fajta láthatatlan költség ismételten megjelenik az ügynökrendszerekben: egy ártalmatlannak tűnő kódsor egy nagyságrenddel lelassíthatja a teljes következtetési csővezetéket. Ez a szakasz elmagyarázza, hogyan kerüljük el ezeket a buktatókat.

> "Technikai Megjegyzés": Ez a szakasz a Transformer figyelmi mechanizmus és a KV Cache belső elveit érinti, így ez a könyv egyik legtechnikaibb része. Ha nem ismeri ezeket a mögöttes mechanizmusokat, **kihagyhatja a részletes elveket, és megjegyezheti a következő három alapvető következtetést**:
>
> 1. **Ha a rendszer prompt és az eszközdefiníciók véglegesek, ne változtassa meg őket.** Bármilyen módosítás, még egyetlen szóköz hozzáadása is, érvényteleníti a teljes gyorsítótárat, és megsokszorozhatja a késleltetést és növelheti a költségeket (a pontos mérték a modelltől és a konfigurációtól függ).
> 2. **Mindig a dinamikus információkat fűzze a végére** – az olyan változó tartalmakat, mint az időbélyegek és a felhasználói állapot, új üzenetekként kell hozzáfűzni a beszélgetés végéhez, nem pedig a meglévő rendszer prompt módosításával.
> 3. **Használja a szabványos API formátumot; ne fűzze össze manuálisan az üzeneteket**: A strukturált üzeneteket a Chat Template egy rögzített token sorozattá alakítja, amelyet a modell a tanítás során látott. A sztringek manuális összefűzésének alapvető problémája az olyan formátumokba, mint `"USER: ... ASSISTANT: ..."`, hogy eltér ettől a tanítási formátumtól, gyengítve a modell többlépéses érvelési képességét. A gyorsítótárazás azonban csak a kapott token sorozattól függ. Egy manuálisan összefűzött előtag továbbra is gyorsítótárazható, ha bájt szinten stabil marad. A gyorsítótár csak akkor érvénytelenül, ha az előtag megváltozik, például amikor dinamikus tartalmat illesztenek bele.
>
> A három következtés mögötti intuíció egyszerű: amikor az LLM feldolgozza a kontextust, gyorsítótárazza a már feldolgozott előtag számításait, így a következő kérés újra felhasználhatja ezt a munkát. **Ha az előtag bájt szinten azonos, a gyorsítótárazott számítás újra felhasználható; ha az előtag megváltozik, az azon a ponton túli számításokat újra kell építeni.** A rendszer prompt és az eszközdefiníciók általában ennek az előtagnak a legkorábbi és legdrágább részei; ha ezek megváltoznak, a gyorsítótárazott közbenső eredmények azon a ponton túl érvénytelenülnek.
>
> Jegyezze meg ezt a három alapelvet, és még ha kihagyja is az alábbi technikai részleteket, helyesen tudja megtervezni egy ügynök kontextusának szerkezetét. A következő tartalom azoknak az olvasóknak szól, akik mélyebben szeretnék megérteni a "miért"-et.

> "Kísérlet 2-2 ★: Figyelmi Mechanizmus Vizualizációja"
>
> Mielőtt elmagyaráznánk a KV Cache-t, először építsünk intuitív megértést a modell belső figyelmi mechanizmusáról egy kísérleten keresztül – ez az alapja annak, hogy megértsük, miért hatékony a KV Cache, és miért támaszt szigorú követelményeket a kontextus tervezésével szemben.
>
> "Mi a Figyelmi Mechanizmus?" Vegyünk egy konkrét példát. Tegyük fel, hogy a modell a "北京的天气怎么样" kínai mondatot dolgozza fel (amelynek szavai: "北京" [Peking], "的" [birtokos partikula], "天气" [időjárás] és "怎么样" [milyen]). Amikor a "怎么样" szót olvassa, a modellnek el kell döntenie: melyik korábbi szavak a legfontosabbak a "怎么样" megértéséhez?
>
> A figyelmi mechanizmus háromféle vektort használ annak eldöntésére, hogy melyik korábbi tokenek a legrelevánsabbak:
>
> A 2-1. táblázat összefoglalja a Lekérdezés (Query), a Kulcs (Key) és az Érték (Value) vektorok szerepét a figyelmi mechanizmusban, segítve az olvasókat az absztrakt számítás leképezésében a "北京的天气怎么样" példamondatra.
>
> 2-1. táblázat: A Lekérdezés, Kulcs és Érték szerepe a Figyelmi Mechanizmusban
>
> | Vektor | Jelentés | Ebben a példában |
> |-------|-----------------------------------------|-----------------------------------------------|
> | "Query" | Az aktuális szó által kiadott "keresési kérelem" | "怎么样" (milyen) megkérdezi: melyik szó a legrelevánsabb számomra? |
> | "Key" | Az egyes szavak "címkéje", a keresés párosításához | A "北京" (Peking) címkéje "helynév" felé hajlik; a "天气" (időjárás) címkéje "meteorológia" felé hajlik |
> | "Value" | Az egyes szavak "tartalma", amelyet sikeres párosítás után kinyerünk | A "天气" (időjárás) párosítása után kivonjuk annak szemantikai információját |
>
> Leegyszerűsítve: minden új szó relevancia alapján pontozza az előző szavakat, majd a legrelevánsabb információt használja fel saját reprezentációjának felépítéséhez.
>
> Pontosabban, a számításnak három lépése van. Először a "怎么样" létrehozza saját Query vektorát, ami azt reprezentálja, hogy az aktuális token mit keres. Másodszor, a Query-t összehasonlítja az egyes előző szavak Key-jével egy pontszorzat segítségével, ami egy relevancia pontszámot ad; a magasabb pontszám erősebb egyezést jelez. Végül ezek a pontszámok figyelmi súlyokká válnak, amelyeket a Value vektorok súlyozott összegének kiszámításához használnak. A magasabb súlyú szavak nagyobb mértékben járulnak hozzá a végső reprezentációhoz, míg az alacsonyabb súlyú szavak kevésbé.
>
>
> ![Figure 2-6: A Figyelmi Mechanizmus Intuitív Megértése](images/fig2-6.png)
>
>
> A 2-6. ábra felső része azt mutatja, hogy "怎么样" (milyen) hogyan párosul az egyes előző szavakkal: a legerősebb egyezés a "天气" (időjárás, 0,55), van némi relevancia a "北京" (Peking, 0,35) felé, szinte semmi a "的" (partikula, 0,05) felé, és a fennmaradó súly körülbelül 0,05 a "怎么样" saját magára jut (az ábrán külön nem látható) – minden súly összege 1. A végső kimenet főként a "天气" információjára támaszkodik, ami pontosan megfelel az intuíciónak.
>
> Egy "figyelmi hőtérkép" az egyes szavak és az összes előző szó közötti figyelmi súlyokat egy mátrixba rendezi. A 2-6. ábra alsó része a teljes hőtérképet mutatja: minden sor egy Query (az éppen feldolgozott szó), minden oszlop egy Key (a figyelem tárgya), és a sötétebb cellák magasabb figyelmi súlyokat jeleznek. A hőtérkép háromszög alakú, mert a modell balról jobbra generál szöveget: minden szó csak önmagára és az előtte lévő szavakra figyelhet, nem pedig a még nem generált tartalomra.
>
> **Miért kell a Key-t és a Value-t gyorsítótárazni?** A hőtérkép megfigyelése feltárja, hogy minden alkalommal, amikor egy új szó generálódik, a Query-jét párosítani kell az "összes" előző szó Key-jével, majd ki kell számítani az összes Value súlyozott összegét. Ha minden K és V értéket minden alkalommal a semmiből számolnánk újra, a számítás a kontextus hosszával nőne. A KV Cache eltárolja a már kiszámított K és V értékeket, lehetővé téve az új szavak számára, hogy közvetlenül újra felhasználják őket – ez az a központi optimalizálás, amelyet a következőkben tárgyalunk.
>
> A figyelmi mechanizmus alapvető megértésével most megfigyelhetjük egy valódi modell figyelmi eloszlását a `attention_visualization` kísérleten keresztül.
>
>
> ![Figure 2-7: Figyelmi Hőtérkép Vizualizációja](images/fig2-7.png)
>
>
> A figyelmi hőtérkép több kulcsfontosságú mintázatot tár fel:
>
> 1. "Figyelmi Nyelő": A sorozat első tokenje gyakran abnormálisan magas figyelmi súlyt vonz magához, néha meghaladva a teljes figyelem 70%-át. A modell ezt a pozíciót "Figyelmi Nyelőként" használja, hogy elnyelje a maradék figyelmi tömeget, amely nem kapcsolódik erősen egyetlen más konkrét tokenhez sem. Más szóval, a modell megtanulja, hogy a másképpen el nem osztott figyelmi súlyt az első tokenhez rendelje – ez szisztematikus jelenség, nem modellhiba.
>
>    A matematikai ok az, hogy a figyelmi mechanizmusnak van egy kemény korlátja: az összes figyelmi súlynak pontosan 100%-ot kell kitennie (ezt egy softmax nevű matematikai függvény garantálja), így a modell nem fejezheti ki, hogy "nem figyel semmire." Még ha az aktuális szó nem is nagyon releváns egyetlen előző szóhoz sem, ezeket a súlyokat el kell helyezni valahol. A modellnek ezért szüksége van egy stabil tartályra ehhez a "maradék súlyhoz," és a sorozat elején lévő rögzített pozíció válik a legtermészetesebb választássá. Ez a softmax matematikai tulajdonságainak elkerülhetetlen következménye, amikor sok tokent dolgoz fel.
> 2. "Érvelési Háromszög Mintázat": A modell gondolkodási lánca (a `<think>` tageken belül) egy háromszög alakú önfigyelmi mintázatot mutat: amikor új érvelési tartalmat generál, gyakran figyel a korábbi érvelési tartalomra és az eszközdefiníciókra.
> 3. "Kimeneti Háromszög Mintázat": Az érvelés befejezése utáni kimeneti folyamat egy másik háromszöget mutat, ahol a modell az érvelési nyomot használja promptként a válasz generálásához.
> 4. "Pozíciós Torzítás"[^lost-in-the-middle]: A modell nagyobb pontossággal idézi vissza a kontextus elején és végén lévő információkat, míg a közepén lévő információk nagyobb valószínűséggel maradnak figyelmen kívül. Ezért a kontextus tervezésekor a legkritikusabb információk elhelyezése az elején vagy a végén fontos gyakorlati alapelv.
>
> Ez a kísérlet azt mutatja, hogy **a hosszú gondolkodási lánc generálása és az eszközhívás is nagymértékben támaszkodik a kontextuson belüli tanulásra** – a modell azon képességére, hogy alkalmazkodjon egy feladathoz a bemenetben biztosított utasítások és példák alapján, anélkül, hogy újratanítanák. A kontextuson belüli tanulás belső mechanizmusához és az ügynökarchitektúra tervezésére gyakorolt hatásaihoz lásd a fejezet Kontextustömörítés szakaszát.
>

[^lost-in-the-middle]: Liu et al. ["Lost in the Middle: How Language Models Use Long Contexts"](https://aclanthology.org/2024.tacl-1.9/), TACL, 2024.

### Az API Üzenetektől a Modell Tokenekig: Chat Template

A Chat Template "alapvető fogalom az egész könyvben". Nemcsak a KV Cache viselkedését befolyásolja, hanem olyan mechanizmusokat is, mint a többlépéses eszközhívás, a gondolkodási lánc megtartása és az állapotsáv injektálása. Ezért megérdemel egy külön magyarázatot. A figyelmi vizualizációs kísérletben szereplő token sorozatok (például a `<|im_start|>`, `<|im_end|>` speciális tokenek) nagyon különböznek a korábban bemutatott JSON formátumú API üzenetektől. Az ok az, hogy a strukturált API üzeneteket lineáris token adatfolyammá kell alakítani, amelyet a modell fel tud dolgozni. Az ezt az átalakítást végző komponens a "Chat Template".

![Figure 2-8: A Chat Template Token Szerkezete](images/fig2-8.png)

A Chat Template megértésének egy hasznos módja, ha "borítékformátumként" tekintünk rá. Az API üzenet a levél tartalma, míg a Chat Template határozza meg, hogy a feladó, a címzett és a határok hogyan vannak a borítékra írva. Speciális tokeneket (pl. `<|im_start|>system`, `<|im_end|>`) használ az egyes üzenetek szerepének és határának jelölésére. A különböző modellcsaládok (Qwen, Llama, Gemma) különböző borítékformátumokat használnak. Az API szerver (vLLM, Ollama, stb.) automatikusan elvégzi ezt az átalakítást a modell Chat Template-je alapján, így a fejlesztőknek általában nem kell manuálisan kezelniük.

A Qwen modellsorozatot példaként használva, ugyanaz a beszélgetés teljesen más formában jelenik meg API-szinten és a modell belsejében:

![Figure 2-9: Átalakítás API Üzenetekből Modell Token Adatfolyammá](images/fig2-9.png)

A bal oldalon a strukturált JSON üzenet, a jobb oldalon a lineáris token adatfolyam, amelyet a modell feldolgoz. A `<|im_start|>` és `<|im_end|>` speciális tokenek, amelyek megmondják a modellnek az egyes üzenetek szerepét és határait.

Az ügynökfejlesztőknek **nem kell manuálisan írniuk vagy módosítaniuk a Chat Template-et**; az API szerver automatikusan kezeli. Azonban a létezésének megértésének két gyakorlati haszna van az ügynökfejlesztésben:

**Először is, megmagyarázza, miért kell a szabványos API formátumokat használni.** Ha egy fejlesztő megkerüli az API-t és manuálisan fűzi össze az üzeneteket (például eszközeredményeket közönséges felhasználói üzenetként ad át eszközüzenetek helyett), a Chat Template helytelenül reprezentálhatja a beszélgetést. A Qwen3 Chat Template-jével például a többlépéses eszközhívások megtarthatják a korábbi belső érvelési tartalmat a `<think>` tageken belül, megőrizve a folytonosságot az eszközhívások között. Amikor a sablon érzékeli, hogy új felhasználói kör kezdődött, törli ezt az érvelési kontextust és újat kezd. Ha egy eszközeredményt hibásan felhasználói üzenetként jelölünk meg, az rosszkor indíthatja el ezt a visszaállítást, gyengítve a többlépéses érvelés koherenciáját. Fontos megjegyezni, hogy a különböző modellcsaládok nagyban eltérnek abban, hogyan kezelik a történelmi gondolkodási láncot, és maguk a stratégiák is gyorsan fejlődnek. A DeepSeek R1 korszak hivatalos iránymutatása az volt, hogy "távolítsuk el az összes történelmi érvelést": többfordulós beszélgetésekben csak a `content` kerül vissza, nem a `reasoning_content` – mert a történelmi CoT soha nem jelent meg az R1 tanítási bemenetében, visszacsatolása eloszláson kívüli bemenet, amely zavarhatja a kimenetet, és jelentős tokenszámot is megtakarít. De ennek a stratégiának vannak hibái az ügynöki forgatókönyvekben: a köztes érvelés olyan kritikus állapotokat hordoz, mint "miért hívták ezt az eszközt és mely hipotéziseket zárták ki"; ha eltávolítják, a modell minden körben a semmiből kezdi az érvelést, hajlamos ismételni a hibákat és elveszíteni a hosszú távú terveket. Ezért a DeepSeek "teljesen megfordította" a politikát a V4-ben, előírva, hogy minden asszisztens üzenet `reasoning_content`-jét (beleértve a `tool_calls`-t tartalmazókat is) szó szerint vissza kell adni, különben az API egyértelmű hibát ad vissza – a Kimi K2, GLM-5 és mások is ugyanezt a protokollt fogadták el. Claude eközben megköveteli, hogy a kliens a thinking blokkot (aláírás-ellenőrzéssel) változatlanul adja vissza az API-nak az eszközhívási hurokban, míg a szerver figyelmen kívül hagyja a történelmi gondolkodást egy új felhasználói kör után. Ez az iparági szintű váltás az "eltávolításról" a "kötelező visszaadásra" önmagában is erős bizonyíték: **ügynöki forgatókönyvek esetén a gondolkodás nem hulladék, hanem állapot.** Használat előtt olvassa el a modell legújabb sablon dokumentációját.

**Másodszor, megmagyarázza, miért olyan érzékeny a KV Cache az előtagra.** A Chat Template a rendszerüzeneteket és az eszközdefiníciókat egy rögzített token sorozattá alakítja a bemenet eleje közelében. Ezen tokenek kulcs-érték állapotai gyorsítótárazhatók és újra felhasználhatók a kérések között. Ha bármely token megváltozik ebben az előtagban, még egy extra szóköz is a rendszer promptban, a gyorsítótár azon a ponton túl már nem használható újra.

### A KV Cache Elvei és Korlátai

A KV Cache értékének megértéséhez először gondoljuk át, mi történik nélküle. Tegyük fel, hogy egy ügynök elérte a hatodik beszélgetési kört, és felhalmozott 2000 kontextus tokent. Gyorsítótárazás nélkül minden új tokenhez a modellnek újra kellene számolnia a K és V vektorokat a teljes előtaghoz. Bár az első öt kör változatlan, a hatodik kör mégis újraszámolja őket, és a hosszabb előtag ezt a kört drágábbá teszi, mint az elsőt. Gyorsítótárazás nélkül a figyelmi számítás a prefill fázisban (az a szakasz, ahol a modell feldolgozza az összes bemeneti tokent a válasz generálása előtt) négyzetesen nő a kontextus hosszával, ami a késleltetés és a költség gyors növekedését okozza a beszélgetés előrehaladtával. Ez különösen problémás a sok eszközhívást igénylő ügynöki feladatoknál.

![Figure 2-10: KV Cache Előtag Újrafelhasználási Mechanizmus](images/fig2-10.png)

**A KV Cache megértése egy egyszerű példával.** Tegyük fel, hogy a kontextus 4 tokent tartalmaz [A, B, C, D], és a modell éppen az ötödik tokent, E-t fogja generálni. A figyelmi művelet lényege, hogy összehasonlítja E Query vektorát a meglévő tokenek Key vektoraival az egyezési pontszámok kiszámításához (a pontszorzat intuitív magyarázatához lásd a 2-2. kísérletet). Ezután ezekkel a pontszámokkal számítja ki a Value vektorok súlyozott összegét, előállítva E kimeneti reprezentációját.

KV Cache nélkül minden alkalommal, amikor egy új token generálódik, az összes előző token K és V vektorját a semmiből kell újraszámolni: E generálásához 5 K és V készlet számítása szükséges, a hatodik token generálásához 6 készlet... és az N-edik tokenre N készletet kell számolni, a teljes számítás N²-tel arányos.

KV Cache-szel az A, B, C, D K és V vektorjai gyorsítótárazásra kerülnek az első számítás után. Amikor E-t generáljuk, csak E saját K és V vektorjait kell kiszámítani, majd a figyelmi számítást elvégezni ezekkel és a 4 gyorsítótárazott készlettel. Vegye figyelembe, hogy a KV Cache megspórolja a történelmi tokenek K és V projekcióinak újraszámolását, így minden dekódolási lépés nem igényli a teljes előtag újraszámolását; azonban a figyelmi számítás minden új tokenhez továbbra is végig kell menjen az összes gyorsítótárazott K és V értéken, a számítás lineárisan nő a kontextus hosszával – ezért lesz a hosszú kontextusú dekódolás egyre lassabb, és a KV Cache memória és sávszélesség a következtetés szűk keresztmetszetévé válik.

**Miért érvényteleníti a gyorsítótárat az előtag módosítása?** A nagy nyelvi modellek egymásra épülő Transformer rétegekből állnak (a modern LLM-ek általában több tucatnyi vagy több száz réteggel rendelkeznek), és minden réteg létrehozza a saját K és V gyorsítótárát. Ezek a rétegek sorba vannak kapcsolva: az 1. réteg kimenete a 2. réteg bemenete, a 2. réteg kimenete a 3. réteg bemenete, és így tovább. Amikor feldolgozunk egy szót, az 1. réteg figyelembe veszi azt a szót és az összes előző szót, majd kiad egy köztes reprezentációt; a 2. réteg ezt a reprezentációt veszi és tovább dolgozza fel. Ha egy korai token megváltozik (például egy karakter a rendszer promptban), az 1. réteg kimenete megváltozik, a 2. réteg bemenete megváltozik, és a különbség továbbterjed a következő rétegeken keresztül. A változás utáni gyorsítótárazott állapotokat újra kell számolni. A költség jelentős: a korábban feldolgozott tokeneket újra kell számolni és újra kiszámlázni lehet, és a késleltetés jelentősen megnőhet (a fejezet kísérletei többszörös növekedést mértek). Ezért hangsúlyozza a könyv újra és újra: ha a rendszer prompt be van állítva, ne változtassa meg.

> **Kísérlet 2-3 ★★: Gyakori, de Káros Kontextuskezelési Mintázatok**
>
> A `kv-cache` kísérletben szisztematikusan teszteltünk több gyakori, de káros kontextuskezelési mintázatot. Ezek a mintázatok aláássák a KV Cache hatékonyságát, és néhányuk az ügynök alapvető képességeit is rontja.
>
> "Dinamikus Rendszer Prompt" az egyik leggyakoribb hiba. Egyes fejlesztők időbélyegeket ágyaznak be a rendszer promptba (pl. "Current time: 2025-09-14 10:30:45.123456"), hogy az ügynök "tudja" a jelenlegi időt. Bár ez hasznos kontextust biztosít, az időbélyeg minden kéréssel változik, így a teljes rendszer prompt különbözővé válik, és teljesen érvényteleníti a KV Cache-t. A helyes megközelítés az, ha az időinformációt egy felhasználói üzenet részeként a beszélgetés végéhez fűzzük hozzá, vagy csak akkor szerezzük be eszközhívással, amikor valóban szükség van rá.
>
> "Dinamikus Felhasználói Konfiguráció" megkísérli a felhasználói állapotinformációk (például a fennmaradó API hívások vagy a számlaegyenleg) frissítését minden kéréssel. Ennek az információnak a kontextusba ágyazása tönkreteszi a gyorsítótárat. Jobb megoldás, ha szükség esetén egy dedikált állapotkezelő mechanizmuson keresztül kezeljük.
>
> "Eszközdefiníciók Dinamikus Rendezése" egy másik alattomos csapda. Egyes rendszerek dinamikusan átrendezik az eszközöket a használati gyakoriság alapján, de az eszközdefiníciók gyakran a kontextus nagy részét foglalják el (minden eszköz több száz tokennyi leírást és paraméterspecifikációt tartalmazhat). A sorrend megváltoztatása érvényteleníti a teljes gyorsítótárat. A kísérletek azt mutatják, hogy a rögzített sorrendnek szinte nincs hatása az eszközkiválasztás pontosságára, de jelentősen javítja a teljesítményt.
>
> "Csúszóablakos Beszélgetéstörténet" a kontextus hosszát úgy szabályozza, hogy csak a legutóbbi üzeneteket tartja meg. Például, ha az ablak mérete 10 üzenetre van állítva, a legkorábbi üzenet elvetődik, amikor a 11. üzenet megérkezik. Ennek a megközelítésnek két súlyos problémája van. Először is, megtöri az előtag konzisztenciáját és érvényteleníti a KV Cache-t. Másodszor, kritikus eszközeredményeket vethet el. Például egy 10 körös csúszóablaknál, ha az ügynök a 2. körben elolvas egy fontos fájlt, a 15. körre ismét szüksége lehet arra az eredményre – de az eredeti eredmény már kiesett az ablakból. A modellnek ekkor egy hiányos beszélgetésből kell következtetnie, ami növeli a hibák arányát. A kísérletekben a csúszóablakot használó ügynökök gyakran kerültek hurkokba, újra és újra végrehajtva ugyanazokat az eszközhívásokat, mert a korábbi eredményeket eltávolították.
>
> "Szövegformázási Módszer" az egyik legkárosabb mintázat. Strukturált szerep-tartalom üzeneteket alakít át egyszerű szöveges adatfolyammá, mint például "USER: ... ASSISTANT: ...". A kulcsprobléma nem a gyorsítótárazás: a gyorsítótárazás a tokenek bájt sorozatán működik, így egy bájt szinten stabil, összefűzött előtag továbbra is eltalálhatja a gyorsítótárat. A gyorsítótár csak akkor törik meg, ha maga az összefűzési módszer instabil, például amikor dinamikus tartalmat injektálnak az előtagba minden alkalommal. A valódi kár az, hogy a szövegformázás eltér a modell tanítása során használt szabványos üzenetformátumtól. A modell hatalmas mennyiségű szerepalapú párbeszédadatot látott, és megtanulta annak szerkezetét elemezni. Amikor az üzeneteket egyszerű szöveggé lapítják, a modellnek gyengébb jelekből kell kikövetkeztetnie a szerepek határait és a párbeszéd szerkezetét, ami olyan problémákhoz vezet, mint az ismétlődő műveletek, figyelmen kívül hagyott eszközeredmények, szöveges válaszok, amikor eszközhívásra lenne szükség, és elemzési hibák.
>
> "Összefoglalás": A káros mintázatok orvoslása mind visszavezet a szakasz elején megadott három alapelvhez. Egy további pont: a modellszolgáltatók sokat optimalizáltak a szabványos interfészeikre, és a szabványos formátumtól való eltérés valószínűleg problémákat okoz. Ahogy fentebb említettük, ez elsősorban modellképességi probléma, nem gyorsítótárazási probléma.

### KV Cache és Prompt Cache: A Gyorsítótárazás Két Szintje

Mielőtt továbblépnénk, érdemes megkülönböztetni két gyakran összekevert fogalmat. A "KV Cache" a modellkövetkeztetésen belüli optimalizálás: egyetlen következtetési menet során gyorsítótárazza a már feldolgozott tokenek kulcs-érték állapotait, hogy elkerülje a redundáns számításokat. A "Prompt Cache" egy API szolgáltatási réteg optimalizálás: újra felhasználja az azonos előtagok gyorsítótárazott számításait több API kérés között. Mindkettő az előtag stabilitásától függ, de különböző szinteken működnek. A KV Cache a token generálást gyorsítja fel egy kérésen belül; a Prompt Cache a redundáns előtag számításokat csökkenti a kérések között. A gyakorlatban az API szolgáltató összehasonlítja a kérés előtagját. Ha több kérés ugyanazt az előtagot osztja meg (például a rendszer prompt és az eszközdefiníciók változatlanok maradnak), a szolgáltató újra felhasználhatja a gyorsítótárazott előtag számításokat ahelyett, hogy újraszámolná azokat a tokeneket. A gyorsítótárból való olvasás sokkal olcsóbb, mint az új számítás – körülbelül az ár egytizede az Anthropic és a DeepSeek esetében, és szintén körülbelül egytizede az OpenAI GPT-5 családjánál (a korábbi GPT-4o generáció fele áron volt; a GPT-5.6-tól kezdve a gyorsítótár írások emellett 1,25× felárat viselnek). Hogy a gyorsítótárazás hogyan engedélyezhető és számlázható, az szolgáltatónként eltér: az Anthropic explicit `cache_control` töréspontokat igényel, felárat számít fel a gyorsítótár írásokért, minimális gyorsítótárazható hosszt ír elő (pl. 1024 token), és TTL korlátot alkalmaz (alapértelmezés szerint körülbelül 5 perc); az OpenAI automatikus előtag gyorsítótárazást használ explicit deklarálás nélkül.

A kontextus tervezésekor a gyorsítótárazás mindkét szintje stabil előtagot igényel – de a Prompt Cache nagyobb gazdasági hatással bír, mert közvetlenül befolyásolja az API számlázást.

### A Gyorsítótárazás mint Architekturális Kényszer

A következő szakasz production-szintű ügynökök architekturális részleteit tárgyalja. Az első olvasók kihagyhatják, és később térhetnek vissza hozzá, amikor ügynököt építenek.

A production-szintű ügynökrendszerekben a gyorsítótárazás nem csupán teljesítményoptimalizálás – ez egy "architekturális kényszer", amely számos, egyébként függetlennek tűnő tervezési döntést diktál az egész rendszerben.

A Claude Code egy tágabb mintázatot illusztrál: amikor a Prompt Cache jelentős gazdasági értékkel bír, a gyorsítótár konzisztenciája alakíthatja az architekturális választásokat a rendszer egészében. Számos tervezési döntés tükrözi ezt a kényszert:

**A prompt szerkezetét a gyorsítótár határai alakítják.** A rendszer prompt egy gyorsítótár-határjelzővel van felosztva: a jelző előtti tartalom globálisan gyorsítótárazható a felhasználók és munkamenetek között, míg a jelző utáni tartalom felhasználó- és munkamenet-specifikus információkat tartalmaz. Ez azt jelenti, hogy a prompt sorrendjét elsősorban a gyorsítótárazás gazdaságossága vezérli, és csak másodsorban a szemantikai logika. Minden olyan futásidejű feltétel, amelyet a gyorsítótár határa elé helyeznek (OS típus, aktuális mód, felhasználói preferenciák, stb.), növeli a gyorsítótár-kulcs variánsok számát. Ha minden feltétel bináris, N feltétel 2^N kombinációt eredményez. Például 3 bináris feltétel (macOS/Linux, normál/debug mód, kínai/angol) 2×2×2 = 8 gyorsítótár-kulcsot eredményez. A prompt töredékek ezért vagy "gyorsítótárazható" vagy "gyorsítótár-törő" típusúak, explicit figyelmeztető jelzésekkel az utóbbihoz.

**A részügynököknek bájt szinten kell illeszkedniük a szülő ügynökhöz.** Amikor a fő ügynök egy részügynököt hoz létre vagy egy mellékkérdezést végez, a részügynök promptjának, eszközdefinícióinak, modellkonfigurációjának, üzenet előtagjának és érvelési konfigurációjának bájt szinten meg kell egyeznie a szülő ügynök gyorsítótár-kulcsával. Az ok az, hogy ha a részügynök által kezdeményezett API kérés előtagja megegyezik a szülő ügynök kérésével, akkor eltalálhatja az API szolgáltató Prompt Cache-ét, ezáltal csökkentve a számlázást és a késleltetést. Ez a kényszer alulról felfelé terjed a gyorsítótárazási rétegből, befolyásolva, hogy az ügynökök hogyan generálódnak és hogyan adódnak át a paraméterek.

**Az eszközeredmények helyettesítő sztringjei az első előforduláskor rögzülnek.** Amikor a nagy eszköz kimeneteket összefoglaló előnézetekre cseréljük, a helyettesítő sztring megmarad. Még ha egy munkamenet újraindul is, a rendszer pontosan ugyanazt a helyettesítő sztringet használja újra, hogy a visszaállított üzenetsorozat bájt szinten azonos maradjon a gyorsítótárazott adatfolyammal.

A központi felismerés az, hogy **a gyorsítótárazás gazdaságossága nem utólagos optimalizálás, hanem előzetes architekturális kényszer.** Ha az ügynökrendszere Prompt Cachinget használ, a gyorsítótár-kulcs konzisztenciájának követelménye áthatja a prompt tervezést, a többügynökös koordinációt, a munkamenet-helyreállítást és más rétegeket. Minél korábban építik be ezt a kényszert az architektúrába, annál alacsonyabb a későbbi mérnöki költség.

### A KV Cache Nem Feltétlenül Egyszeri: Szerkeszthető, Összeállítható "Jegyzetek"

(A következők opcionális, haladó anyag a jelenlegi kutatásból. Első olvasásra kihagyható anélkül, hogy a fejezet hátralévő részét érintené; a fenti három gyakorlati következtetés az alap.)

Eddig ez a szakasz egy szigorú szabályt feltételezett: változtass meg egy bájtot az előtagban, és az azt követő gyorsítótár érvénytelenül. Ez a szabály a mai következtető motorokban érvényes, de nem feltétlenül elkerülhetetlen. Egy friss kutatási irány egy ellentmondásos megfigyelésből indul ki[^ch2-2]: a prefill fázisban a modell úgy viselkedik, mintha "jegyzeteket készítene." Amikor elolvas egy mezőt a kontextusban (pl. "Felhasználó városa: Peking"), nem egyszerűen szó szerint gyorsítótárazza azt a mezőt. Ehelyett lejjebb írja a "következtetés" downstream reprezentációit – hogy mit jelent ez a mező – a későbbi KV állapotokba. A mérések azt mutatják, hogy a mező "saját" tokenjeinek KV állapotai gyakran kevesebb mint 1%-ban járulnak hozzá a végső döntéshez; ami jobban befolyásolja a kimenetet, azok a mező által hátrahagyott downstream "jegyzetek."

Ez a felfedezés két olyan műveletet sugall, amelyeket korábban kivitelezhetetlennek tartottak. Az első a "Szerkesztés": mivel a következtetés már be van írva a downstream jegyzetekbe, egy megváltoztatott mező továbbterjedhet a gyorsítótárazott érvelésen keresztül, ha a modell rendelkezik explicit gondolkodási lánccal (CoT), olyan eredményeket produkálva, amelyek közel állnak a teljes újraszámításhoz, a számítás körülbelül 1%-ával. Ezzel szemben CoT nélkül egy elszigetelt mezőváltoztatás figyelmen kívül maradhat, mert a következtetés már be van ágyazva a downstream-be anélkül, hogy lenne egy érvelési út a frissítéséhez. A második az "Összeállítás": egy előre kiszámított "készség" gyorsítótár áthelyezhető a Forgó Pozíció Beágyazás (RoPE) segítségével, és beilleszthető egy másik kontextusba anélkül, hogy újra kellene számolni a figyelmet. Ebben a keretben a kontextus összeállítása moduláris gyorsítótár blokkokból O(L²) újraszámításról O(L) összeillesztésre csökken, a kimenet minősége közel áll a teljes újraszámításhoz.

A lapszéli jegyzet analógia hasznos itt. Amikor egy hosszú dokumentumot olvasunk, nem olvassuk újra a teljes dokumentumot minden alkalommal, amikor egy tény megváltozik; ehelyett frissítjük a jegyzetet, amely rögzíti, hogy a tény mit jelent. A KV Cache mint jegyzetek ötlete hasonló: ha a gyorsítótárazott állapotok már kódolják egy tény következtetését, akkor a tény megváltoztatása megkövetelheti a downstream jegyzet korrigálását ahelyett, hogy mindent újraszámolnánk. Mivel a jegyzetek hordozható formában vannak reprezentálva, az egyik problémából származó jegyzetblokk áthelyezhető (RoPE áthelyezésen keresztül) és újra felhasználható egy másikban. A cikk ezt az ötletet a vLLM-en implementálta, a p90 időt az első tokenre több tízszeresétől több százszorosáig gyorsítva, körülbelül 98,5%-os előtag gyorsítótár találati aránnyal, és a kimenetek közel álltak a tokenenkénti újraszámításhoz (12 modellen, logit koszinusz hasonlóság 0,90–0,999).

Az ügynökök számára a következmény az, hogy a hosszú kontextusoknak nem mindig kell lebontani és újraépíteni, amikor az eszközök, memóriamezők vagy futásidejű állapot megváltozik. Elvben ez változtatható kontextust tehet lehetővé, miközben megőrzi a gyorsítótárazás előnyeit, a kontextus összeállítását O(L²) újraszámításról O(L) jegyzet-összeillesztésre változtatva. Ez még kutatási stádiumban lévő munka; a szakaszban korábban bemutatott három gyakorlati következtetés marad az alapelv a jelenlegi production rendszerek számára.

[^ch2-2]: Li, Bojie. *Models Take Notes at Prefill: KV Cache Can Be Editable and Composable.* arXiv:2606.17107, 2026.

Most, hogy megértettük, hogyan dolgozzák fel és gyorsítótárazza a kontextust, a következő kérdés az, hogyan tervezzük meg magát a tartalmat. A következő szakaszok azt tárgyalják, hogy mi tartozik a kontextusba és hogyan szervezzük azt, három összefüggő szál mentén:

- **Prompt Tervezés, Prompt Injekció és Dinamikus Promptok (Ügynöki Készségek)**: Hogyan írjuk meg a rendszer promptot és mit tartalmazzon. Ez a kontextustervezés legközvetlenebb része. Az eszközdefiníciók, egy másik statikus komponens a rendszer prompt mellett, szintén közvetlenül befolyásolják az ügynök eszközhasználatának pontosságát. Ez a fejezet megadja az alapelveket, a 4. fejezet pedig részletesen kibővíti azokat. A következő kérdés a biztonság: amikor a külső tartalom megkísérli eltéríteni a gondosan megtervezett kontextust, hogyan védekezzen a rendszer kontextus szinten? Ahogy a promptok hosszabbá válnak és egyre több forgatókönyvet fednek le, mindennek egyetlen rendszer promptba helyezése kivitelezhetetlenné válik: tokent pazarl, és szétteríti a figyelmet. Ez természetesen vezet az Ügynöki Készségek progresszív feltárási mechanizmusához, ahol a tudás igény szerint töltődik be, ahelyett, hogy egyszerre lenne minden benne.
- "Ügynöki Állapotsáv": Egy független mechanizmus, amely dinamikus metainformációkat (feladat előrehaladása, környezet állapota, eszközhívások száma, stb.) injektál a kontextus végébe, kompenzálva a modell azon képtelenségét, hogy aktívan összegezze a burkolt állapotokat. Hasonlóan a telefon képernyőjének tetején látható időhöz, akkumulátorhoz és hálózati jelhez, az Ügynöki Állapotsáv lehetővé teszi a modell számára, hogy bármikor hozzáférjen az aktuális futásidejű állapothoz.
- "Kontextustömörítési Stratégiák": A folyamatosan bővülő kontextus problémájának kezelése – mikor kell tömöríteni, hogyan kell tömöríteni, és hogyan fér meg a tömörítés a KV Cache mellett.

## Prompt Tervezés: A Rendszer Prompt Optimalizálása


⚠️ [... középső tartalom kihagyva — az elejét és a végét mutatja ...]


A legközelebbi analógia egy operációs rendszer "állapotsávja". Egy telefonon a képernyő tetején megjelenik az idő, az akkumulátor töltöttsége, a jelerősség és az értesítések száma. Ez az információ nem az alkalmazás fő tartalma, de azonnali hozzáférést biztosít a felhasználók számára az eszköz aktuális állapotához. Az Ügynöki Állapotsáv hasonló célt szolgál a modell számára: nem része a beszélgetés elsődleges tartalmának – nem végfelhasználói kérés, modellkimenet vagy eszközeredmény – hanem egy "állapot-összefoglaló", amelyet az ügynök-keretrendszer injektál a kontextus végébe: "3 hívást indítottál," "Az aktuális idő 10:30," "2 TODO elem van hátra." Minden alkalommal, amikor a modell választ generál, ezt az állapotot felhasználhatja a jobb döntések meghozatalához.

A Rendszer Prompttól való megkülönböztetés világos: a Rendszer Prompt a rögzített működési kézikönyv, míg az Ügynöki Állapotsáv egy valós idejű műszerfal, amely folyamatosan frissül a feladat előrehaladtával.

### Az Ügynöki Állapotsáv Elméleti Alapjai

Az Ügynöki Állapotsáv hatékonysága a figyelmi mechanizmus egy alapvető tulajdonságából ered: a kontextuson belüli tanulás inkább hasonlít a visszakeresésre, mint az érvelésre. A modell jó abban, hogy megtalálja a kontextusban már meglévő információkat, de kevésbé megbízható abban, hogy aktívan összegezze azt a kontextust és levezesse az aggregált állapotot egyetlen előreirányuló menet során. Ez arra vonatkozik, hogy a modell hogyan fogyasztja a meglévő kontextust egy előreirányuló menetben; nem tagadja a modell azon képességét, hogy több lépésből álló érvelést végezzen gondolkodási lánc generálásán keresztül.

Más szavakkal, a figyelem erős, visszakeresésszerű hozzáférést biztosít a modellnek a meglévő tokenekhez. Adott egy kérdés, gyakran képes releváns nyers rekordokat kihúzni több ezer tokenből, így minden előreirányuló menet a Retrieval-Augmented Generation (RAG) egy könnyű formájához hasonlít. Ami hiányzik, az egy automatikus "desztillációs réteg". A kontextus nem kerül automatikusan megszámlálásra, indexelésre vagy összegzésre a helyén. Bármely, a tartalomról szóló következtetést – hogy hány elem van, hogy egy korlátot túlléptek-e, mennyire haladt a feladat – újra kell számolni a nyers rekordokból, amikor a modellnek szüksége van rá. Ennek az újraszámolásnak a költsége a kontextusban felhalmozott tartalom mennyiségével nő.

Vegyünk egy valós forgatókönyvet: egy ügynöknek telefonhívásokat kell kezdeményeznie üzleti feladatok elvégzéséhez, és a rendszer prompt előírja, hogy minden kereskedőt legfeljebb háromszor hívhat. De miután háromszor hívott, az ügynök gyakran elszámolja, hányszor hívott, elindít egy negyedik hívást, vagy akár egy hurokba esik, és ismételten ugyanazt a számot hívja.

A probléma az, hogy a "Hányszor hívtam?" kérdésre a válasz nincs automatikusan explicit ténnyé desztillálva. Ehelyett szétszórva marad a nyers hívási rekordokban a KV Cache-ben. Minden alkalommal, amikor a modell döntést hoz, extra érvelési tokeneket kell költenie a kontextus beolvasására és újraszámolására, ami rendkívül hatástalan és hibákra hajlamos.

Amikor közvetlenül belefoglaljuk az ismételt hívások számát az egyes telefonhívások eszköz eredményébe (pl. "Ez a harmadik hívás ehhez a kereskedőhöz"), a modell azonnal felismerheti, hogy elérte a korlátot, és abbahagyja a hívást, jelentősen csökkentve a hibák arányát.

Ennek a mechanizmusnak a lényege, hogy **a kontextusban szétszórt burkolt állapotokat olyan explicit tudássá desztillálja, amely közvetlenül felhasználható**. A nyers trajektóriában lévő információ rendkívül redundáns – nagy számú token csak kis mennyiségű kulcsfontosságú állapotinformációt tartalmaz. Az Ügynöki Állapotsáv aktívan kivonja ezeket a kulcsfontosságú állapotokat, minimális többlet token költség mellett bemutatva olyan információkat, amelyek egyébként több ezer token beolvasását igényelnék.

Hosszú kontextusú forgatókönyvekben a modell figyelmi erőforrásai korlátozottak. Ahogy a kontextus hossza nő, a modellnek szét kell osztania a figyelmet több jelölt tartalom között, így a kulcsfontosságú információ nem kaphat elegendő súlyt. Összetett ügynöki trajektóriákban a feladat céljait és a korai korlátokat elnyomhatják a későbbi eszközeredmények. A modell hajlamos túlzottan a közeli kontextusra összpontosítani, "figyelmi csillapodást" okozva a kontextus közepén elhelyezkedő információk esetében.

Az Ügynöki Állapotsáv ezt a problémát úgy kezeli, hogy szándékosan a kulcsfontosságú metainformációkat strukturált formátumban a kontextus végére helyezi. Mivel ez az információ közel van a tokenekhez, amelyeket a modell generálni fog, nagyobb valószínűséggel kap figyelmet. Ez a figyelem irányításának egy formája az elhelyezésen keresztül.

> **Kísérlet 2-7 ★★: Az Ügynöki Állapotsáv Hatásának Ellenőrzése Figyelmi Vizualizáción Keresztül**
>
> A `attention_visualization` projektre építve terveztünk egy kontrollált kísérletet, ahol egy ügyfélszolgálati ügynök egy visszatérítési kérelmet kezel. Az ügynök már 3-szor hívta az Xfinity-t, webes keresésekkel megszakítva. A felhasználó megkérdezi: "Fel tudod hívni őket újra, hogy utánanézzenek?"
>
> "A kontrollcsoport (Nincs Állapotsáv):" A kontextus tartalmazza a teljes trajektóriát, de nincs aggregált állapotinformáció. A hőtérkép széles körben elszórt figyelmet mutat, jellegzetes koncentrációkkal a három telefonhívási rekord körül. Az érvelési tokenek azt mutatják, hogy a modell számol és összesít információkat a nyers rekordokból.
>
> "B kontrollcsoport (Állapotsávval):" A következő kerül hozzáfűzésre a trajektória végéhez:
>
> ```xml
> <agent_status>
> Current State:
> - Tool call summary: 'phone_call' has been invoked 3 times (Xfinity: 3 times)
> - Constraint check: Maximum calls to Xfinity reached (3/3)
> </agent_status>
> ```
>
> A figyelem erősen koncentrálódik az állapotsáv információira. Az érvelési folyamat közvetlenül a már desztillált információkat használja, többé nem számol statisztikákat a nyers adatokból. Egy olyan kis modellnél, mint a Qwen3-0.6B, az A kontrollcsoport gyakran megsérti a korlátot és folytatja a hívást, míg a B kontrollcsoport következetesen betartja a korlátot.
>

A 2-7. kísérlet egy kis kvalitatív demonstráció. Ennek az "előre kiszámít és közvetlenül hozzáfér" megközelítésnek az értékének és korlátainak számszerűsítésére a szerző és munkatársai egy dedikált benchmarkkal[^ch2-7] értékelték. Ennek a megközelítésnek általános neve van: "Kontextus Desztilláció". Az Ügynöki Állapotsáv a leggyakoribb formája. A benchmark három feladattípust (számlálás, szabály indukció, állapotkövetés), 11 modellt (a fejlett API-któl egy 2B modellig, amely laptopon is futhat) és közel 24 000 értékelést fedett le. Az eredmények világosak:

- **Gyenge modellek esetén az előre kiszámított állapotsáv helyreállítja a pontosságot** – a leggyengébb modellek 40-54 százalékpontos pontosságnövekedést mutattak, és ezeken a feladatokon egy lokális 2B modell még egy olyan frontier modellt is utolért, amelynek nem volt állapotsávja.
- **Erős modellek esetén, amelyek már helyesen válaszolnak, javítja a hatékonyságot** – ugyanaz az állapotsáv körülbelül egy nagyságrenddel csökkenti az érvelési erőfeszítést, késleltetést és költséget kérésenként (az érvelési tokenek 80-90%-kal vagy még többel csökkennek).
- A legfontosabb változás: állapotsáv nélkül az érvelési erőfeszítés kérésenként "folyamatosan növekszik", ahogy a kontextus hosszabbodik; állapotsávval "lényegében állandóvá" válik – nem számít, milyen hosszú a kontextus, a modell közvetlenül elolvassa azt a néhány állapotbejegyzést. Ez a 2-7. kísérlet hőtérképének számszerűsített változata: eredetileg a figyelem vékonyabbá válik, ahogy N nő; az állapotsáv hozzáadása után szilárdan ráragad azokra a rögzített bejegyzésekre.

(Mellékesen, az állapotsávot gyorsan megtalálható kulcs-érték párokként kell írni, mint `Clothes: 9 items (Pass 7, Defect 2)`, nem prózaként – a cikk kimutatta, hogy ugyanazon állapotinformáció próza formában történő megadása lényegesen rosszabb eredményeket adott, mert a modellnek továbbra is el kell olvasnia és elemeznie a prózát, lényegében visszatérve a beolvasási problémához.)

Azonban **az, hogy az előre számítás hogyan történik, nagyban számít**. A munka legfontosabb tanulságai három közvetlenül alkalmazható lecke:

**1. Az állapotsávot kóddal karbantartani, nem LLM-mel.** Természetesnek tűnhet megkérni egy másik LLM-et, hogy olvassa el a történetet és összegezze az állapotsávot, de a kísérlet azt találta, hogy ez rosszul teljesített. Egy 20 soros reguláris kifejezés függvény elérte a valóság szintű pontosságot, míg egy frontier modell, amely a teljes történetet egy batchben dolgozta fel, sok hibás bejegyzést produkált, és a downstream pontosságot a nincs-állapotsáv alapvonal alá csökkentette. Ha egy LLM-et kérünk meg egy hosszú történet egyetlen menetben történő összegzésére, az csak áthelyezi az eredeti kontextus-beolvasási problémát máshova. Életképes alternatíva, hogy "lehetőség szerint kódot használjunk"; ha LLM szükséges, akkor az **egyenként vonja ki az elemeket, majd a kód aggregálja őket**, ahelyett, hogy a teljes történetet egyetlen menetben összegezné.

**2. Mielőtt törölné az eredeti kontextust, győződjön meg arról, hogy az állapotsáv lefedi az összes kérdést, amely felmerülhet.** Az állapotsáv az eredeti kontextus "veszteséges leképezése": csak azokat a dimenziókat számolja előre, amelyeket *előre lát*, hogy relevánsak lesznek. Ha az állapotsáv elegendő, ahogy az olyan feladatoknál, mint a számlálás és állapotkövetés, az eredeti rekordok törölhetők és csak az állapotsáv tartható meg, sok tokent megtakarítva. A teljesítmény azonban drámaian romolhat, ha egy kérdés olyan információt kérdez, amelyet az állapotsávot nem tervezték rögzíteni. A cikk szélsőséges tesztjében az állapotsáv csak a "páronkénti kombinációk" számait tárolta, míg a kérdés "hármas metszetekre" vonatkozott. Csak az állapotsáv megtartása a pontosság összeomlását okozta, Claude 100%-ról 7,6%-ra esett vissza. Egy hihető, de hiányos állapotsáv ezért "hamis tekintéllyé" válhat, amely magabiztosan félrevezeti a modellt. A gyakorlatban kezeljen egy új típusú kérdést úgy, mint "egy adatbázis tábla sémájának módosítását": vagy adja hozzá a megfelelő mezőt először az állapotsávhoz, vagy tartsa meg mind az állapotsávot, mind az eredeti kontextust. Egyes feladatok, mint a többlépéses következtetés hosszú prózai szövegeken keresztül, nem rögzíthetők egy tiszta strukturált összefoglalóval. Ezeknél a feladatoknál az állapotsáv tokent takaríthat meg, de nem szabad elvárni tőle, hogy javítsa a pontosságot.

**3. Figyelje az állapotsáv pontosságát elsődleges production metrikaként.** A kísérlet egy megdöbbentő eredményt hozott: **a modell szinte feltétel nélkül megbízik az állapotsávban.** Ha azt mondja, "3-szor hívott," a modell elfogadja ezt az értéket ellenőrzés vagy újraszámítás nélkül. Ez a bizalom teszi hatékonnyá az állapotsávot, de lehetővé teszi azt is, hogy a hibák "közvetlenül" belefolyjanak a végső válaszba. A rendszer elviseli a mérsékelt pontatlanságokat: az előnyök nagyrészt megmaradnak, ha az értékek kevesebb mint körülbelül 10%-kal térnek el. Nagyobb hibák esetén azonban egy helytelen állapotsáv rosszabb lehet, mint ha nem lenne. Ez kapcsolódik a korábban tárgyalt "állapotsáv-mérgezés" kockázatához is. Az állapotinformációnak a valós világ megbízható megfigyeléseiből kell származnia, és soha nem olyan adatforrásokból, amelyek kívülről szennyezhetők; különben a műszer rossz állapotot jelent, és félrevezeti a modellt.

[^ch2-7]: Li, Bojie and Noah Shi. *Distill, Don't Retrieve: Inference-Time Context Distillation for LLM Agent Reasoning.* 2026. https://01.me/research/context-distillation

(A következők opcionális, haladó anyag a jelenlegi kutatásból. Első olvasásra kihagyható anélkül, hogy az állapotsáv használatának megértését érintené; a fenti mechanizmusok, bizonyítékok és három lecke elegendő a gyakorlathoz.)

A fenti két alapelv – a burkolt állapot desztillációja és a figyelem irányítása – megmagyarázza, miért működik az állapotsáv. Egy mélyebb pont az, hogy az állapotsáv **olyan információval táplálhatja a modellt, amelyet az egyedül nem tudott volna kikövetkeztetni**[^ch2-5].

Gyakran két módot írunk le arra, hogyan tegyünk erősebbé egy modellt tesztidőben: "hosszabban érveljen" (hosszabb gondolkodási láncot generáljon) és "többet mintavételezzen" (több választ mintavételezzen és válassza ki a legjobbat). Mindkét útnak ugyanaz a korlátja: csak a modell belső számításain belül működnek, rögzített súlyokat és rögzített kontextust használva. **Nem hozhatnak létre olyan információt, amely nem volt már jelen a kontextusban**; csak átrendezhetik a meglévő információt. Az interakció egy harmadik utat biztosít. A modell kimenetet produkál, egy külső műszer megfigyeli annak valós világbeli hatását, és ez a megfigyelés visszaíródik a kontextusba. A megfigyelés tartalmazhat olyan információt, amelyet a modell "önmagában az érveléssel sem tud kikövetkeztetni": hogy a kód átment-e a teszten, hogy egy renderelt gomb túlcsordult-e az oldalon, vagy hogy milyen rendszerállapotot eredményezett egy művelet. Ezek a tények a végrehajtásból és a mérésből származnak, nem a súlyokból vagy a meglévő kontextusból. (Ez a kutatás azt is megállapította, hogy a fejlődés mérésére használt mérőszalagnak magának is valós megfigyeléseken kell alapulnia. Ha egy vizuális modellt használunk, amely csak egy képernyőképet vizsgál a pontozáshoz, előfordulhat, hogy nem érzékeli azokat a hibákat, amelyeket éppen kijavított, ami miatt a hurok nem tesz valódi előrelépést.)

Az Ügynöki Állapotsáv ennek az elvnek a leggyakoribb alkalmazása. A Hám működik műszerként: megfigyeli a futásidejű állapotot (hány hívás történt, az aktuális idő, a feladat előrehaladása, hogy egy eszköz hibát jelzett-e), tömöríti ezeket a megfigyeléseket egy rövid szegmensbe, és visszaírja őket a kontextusba. Az állapotsáv legértékesebb része gyakran nem az az információ, amelyet a modell megszámolhatott volna az átirat beolvasásával, hanem azok a "külső tények, amelyeket nem tudott kikövetkeztetni". Az állapotsáv egy elszigetelt érvelési feladatot valós megfigyelésekben gyökerező feladattá alakít. Ez egy tervezési elvet is ad: minél többet merít az állapotsáv valós megfigyelésekből, annál értékesebb. Ezzel szemben, ha az állapot-összefoglaló kitalált vagy egy szennyezhető adatforrásból származik, a műszer rossz állapotot jelent, és félrevezeti a modellt (ez a korábban tárgyalt állapotsáv-mérgezés kockázatának felel meg).

[^ch2-5]: Li, Bojie and Noah Shi. *Interaction Scaling: Grounding the Third Axis of Test-Time Compute.* arXiv:2607.11598, 2026.

Ebből a perspektívából nézve a Huroktervezés, amelyet az 1. fejezet evolúciós ívének végén vezettünk be, és amelyet a 10. fejezetben továbbfejlesztünk a többügynökös együttműködési rendszerekkel együtt, az interakció e harmadik tengelyét mérnöki gyakorlattá alakítja. Minden iteráció csak akkor tesz valódi előrelépést, amikor a verifikáció a külső világról szóló megfigyeléseket visszaírja a kontextusba. E lépés nélkül a modell csak átrendezi a meglévő információt. Így az az állítás, hogy "a verifikáló, nem a modell a szűk keresztmetszet," és az a megállapítás, hogy a mérőműszernek valós megfigyelésekben kell gyökereznie, ugyanazt az elvet fejezi ki.

### Az Ügynöki Állapotsáv Összetétele

A fenti elméleti alapokra építve az Ügynöki Állapotsáv a következő információtípusokat tartalmazza:

"Feladattervezés": Amikor egy ügynök összetett, több lépésből álló feladatokat kezel, a trajektória nagyon hosszúvá válhat. Az ügynök hajlamos túlzottan az aktuális helyi részfeladatra összpontosítani, elfelejtve a felhasználó eredeti kérését, a kulcsfontosságú korlátokat és a későbbi munkát. Egy TODO lista elhelyezése, amely a feladatot világos lépésekre bontja, a trajektória végén folyamatosan emlékezteti a modellt az aktuális előrehaladására és a jövőbeli célokra, segítve a cselekvések összehangolását az átfogó tervvel.

"Mellékcsatornás Információk Eseményekhez": Csatoljon metaadatokat minden eseményhez – pontos idő, földrajzi hely, az utolsó ügynökválasz óta eltelt idő, stb. A mellékcsatornás információ olyan segécinformációra utal, amely nem a fő adatcsatornában kerül továbbításra, de segít az esemény megértésében. Ez az információ segít a modellnek megérteni az események időbeli kapcsolatait és környezeti kontextusát, lehetővé téve a kontextuálisan megfelelőbb döntéseket.

"Aktuális Környezeti Állapot": Tartalmazza a dinamikus környezeti információkat (rendszeridő, munkakönyvtár, stb.), a rendellenes műveleti riasztásokat ("Ezt az eszközt N-szer hívták meg ismételten") és a burkolt állapotból explicit állapotba történő átalakítást. Ez a tervezési elv az emberi interfészekre is vonatkozik – mind a Parancssori Interfészek (CLI), mind a Grafikus Felhasználói Felületek (GUI) célja, hogy a felhasználók világosan érzékelhessék a rendszer aktuális állapotát.

"Elérhető Képességlista": Amikor az ügynök-keretrendszer támogatja a plugin-alapú képességbővítéseket (mint az előző szakasz Készség rendszere), az összes telepített Készség metaadatlistája szintén ezen a kontextus-végi injektálási csatornán megy keresztül. Ez megmondja a modellnek, hogy mely speciális képességek állnak jelenleg rendelkezésre. Ritkán változik (csak akkor, ha a felhasználó telepít vagy eltávolít egy Készséget), és növekményes küldési mechanizmusát az előző Készségek szakasz részletezte, így itt nem ismételjük meg.

A mellékcsatornás információk és az elérhető képességlista általában nem változnak hozzáadásuk után, így gyorsítótár-barátok, mert nem érvénytelenítik a gyorsítótárazott előtagot. A feladattervezés és a környezeti állapot dinamikus, és speciális felhasználói üzenetként kell a kontextus végéhez fűzni, majd frissíteni a feladat előrehaladtával. A frissítési módszer közvetlenül befolyásolja a KV Cache költséget, amint azt alább tárgyaljuk.

### Az Ügynöki Állapotsáv Konkrét Pozíciója a Kontextusban

![Figure 2-15: Az Ügynöki Állapotsáv Beillesztési Pozíciója az API Üzenetlistában](images/fig2-15.png)

Egy fontos implementációs részlet, hogy az Ügynöki Állapotsáv a kontextus végére kerül beillesztésre "a `user` szerepű üzenetként" API szinten, nem pedig a kezdeti `system` üzenet módosításával. Az ok a korábban tárgyalt KV Cache kényszer: a `system` üzenet módosítása érvénytelenítené a teljes előtag gyorsítótárát. Egy pontosítást igényel: a `user` szerep itt technikai választás az API protokoll szintjén, és nem egyenlő az 1. fejezetben meghatározott "végfelhasználói bemenettel." A Hám kölcsönveszi a `user` szerepű üzenet helyét, hogy az ügynök-keretrendszer által generált rendszerállapot-információkat injektálja. A tartalom nem valódi felhasználótól származik; egyszerűen a `user` üzenetformátumot használja az állapotinformáció kontextus végéhez való csatolásához.

Az alábbiakban az ügynök-keretrendszer által az N-edik API hívás során összeállított tényleges üzenetlista látható:

```
messages: [
  { role: "system",    content: "You are a customer service assistant..." }  ← Rögzített (KV Cache-ben)
  { role: "user",      content: "Help me cancel my Xfinity plan" }  ← Eredeti felhasználói kérés
  { role: "assistant", content: null, tool_calls: [...] }   ← 1. kör: modell úgy dönt, hív
  { role: "tool",      content: "Call log..." }             ← 1. kör: hívás eredménye
  { role: "assistant", content: null, tool_calls: [...] }   ← 2. kör: modell úgy dönt, újra hív
  { role: "tool",      content: "Call log..." }             ← 2. kör: hívás eredménye
  ...(további körök)
  { role: "user",      content: "Can you call them again to follow up?" }  ← Felhasználói utókövetés
  { role: "user",      content: "<agent_status>             ← Állapotsáv az ügynök-keretrendszer által injektálva
      Current State:                                           (user üzenetként)
      - phone_call invoked 3 times (Xfinity: 3/3 max)
      - Current time: 2025-09-14 10:30:45
      - TODO: [1] Cancel plan (in_progress)
    </agent_status>" }
]
```

Figyeljük meg az utolsó üzenetet: a `role`-ja `user`, de a tartalom az ügynök-keretrendszer által automatikusan generált metainformáció, `<agent_status>` tagekbe csomagolva, hogy a modell felismerhesse annak speciális természetét. Ez az üzenet a kontextus legvégén található, közvetlenül szomszédos azokkal az új tokenekkel, amelyeket a modell generálni fog, így kapja a legmagasabb figyelmi súlyt. Ugyanakkor, mivel hozzáfűzésre kerül, nem pedig módosításra, minden korábban gyorsítótárazott tartalom érintetlen marad.

Ez a kialakítás a KV Cache szakasz alapelvét alkalmazza az állapotsávra: dinamikus információkat fűzzünk a végéhez, a statikus információkat pedig tartsuk változatlanul.

### Az Állapotfrissítés Két Implementációja és Gyorsítótár-költségeik

A "hozzáfűzés nem töri meg a gyorsítótárat" csak egyetlen injektálásra érvényes. Az állapot természetesen változik az idők során: a TODO elemek elkészülnek, az eszközszámlálók nőnek, és a korábbi állapotüzenetek elavulnak. Két módszer van az állapotsáv frissítésére, eltérő gyorsítótár-költségekkel:

**1. Implementáció: Csere minden körben.** Minden API hívás előtt távolítsa el az előző kör állapotüzenetét az üzenetlistából, és fűzze hozzá a legfrissebb állapotot a végére. Ez csak egy aktuális állapotot tart a kontextusban. Az ára az, hogy a régi állapot eltávolítása érvényteleníti az összes gyorsítótárazott tartalmat a pozíciója után, ami ugyanaz az érvénytelenítési mechanizmus, amelyet a fejezet "dinamikus időbélyeg" szakasza tárgyal. A különbség az, hogy mivel az állapotüzenet a kontextus vége közelében van, az érvénytelenítési tartomány a legutóbbi néhány kör üzenetére korlátozódik, nem a teljes előtagra.

**2. Implementáció: Tartós hozzáfűzés.** Az állapotüzenet a beinjektálás után véglegesen a trajektóriában marad, és minden körben egy új állapot kerül hozzáfűzésre a végére. A Claude Code `<system-reminder>`-je ezt a megközelítést használja: a történelmi állapotüzenetek az átiratban maradnak, és soha nem törlődnek vagy módosulnak. Ez a módszer teljesen gyorsítótár-barát, mert az üzenetek csak hozzáfűzésre kerülnek, soha nem változnak, így az előtag stabil marad. Az ára az, hogy az elavult állapotok felhalmozódnak a kontextusban, tokeneket fogyasztva, és a modellnek a legfrissebb állapotra kell támaszkodnia, miközben figyelmen kívül hagyja az elavultakat.

A hüvelykujjszabály: **ha az állapotfrissítések gyakoriak és a trajektória hosszú, válassza a 2. implementációt.** Az állapot minden körben történő cseréje ismételten érvényteleníti a gyorsítótár-bejegyzéseket egy hosszú trajektória során, ami többe kerülhet, mint az elavult állapotüzenetek cipelése. **Ha a trajektória rövid vagy egyetlen állapotüzenet nagy** (pl. egy teljes TODO lista plusz környezeti pillanatkép), "válassza az 1. implementációt." A gyorsítótár érvénytelenítése az utolsó néhány kör felett olcsó, és a kontextus tiszta és egyértelmű marad.

> **Kísérlet 2-8 ★★: Néhány Hasznos Ügynöki Állapotsáv Technika**
>
> Az `agent-status-bar` kísérleti keretrendszer öt állapotsáv technikát valósít meg, amelyek mindegyike egymástól függetlenül engedélyezhető vagy letiltható:
>
> "Időbélyeg Követés": Hozzáad egy `[2025-09-14 10:30:45]` formátumú előtagot a felhasználói üzenetekhez és az eszközválaszokhoz (megjegyzés: nem a rendszer promptba helyezve, mert az törné a KV Cache-t). Ez lehetővé teszi az ügynök számára, hogy megértse az időbeli kapcsolatokat, és információt biztosít a hibakereséshez és naplózáshoz. Ez a technika egy idő-szimulációs funkciót is megvalósít, lehetővé téve az ügynök számára, hogy megértse az olyan kapcsolatokat, mint a "tegnapi fájlok" és a "mai módosítások."
>
> "Eszközhívás Számláló": Egy globális szótárat tart fenn, amely rögzíti az egyes eszközök hívásának számát, megjegyzésekkel ellátva a válaszokat: "Tool call #3 for 'read_file'." Ez az explicit számlálás arra ösztönzi a modellt, hogy ismételt kudarcok után változtasson stratégiát: az első kudarc után ellenőrizze az elérési utat; a második kudarc után listázza a könyvtárat; a harmadik után hagyja abba az újrapróbálkozást és keressen alternatívát. Mélyebb értéke a burkolt költségtudatosságban rejlik: az ügynök következtethet arra, hogy már túl sok próbálkozást költött egy adott műveletre.
>
> "TODO Lista Kezelés": A Manus "figyelem manipulálása átfogalmazással" koncepciója által inspirálva, a TODO Lista Kezelés két dedikált eszközt biztosít: `rewrite_todo_list` és `update_todo_status`. Minden TODO elem tartalmaz egy egyedi azonosítót, tartalmat, állapotot (pending/in_progress/completed/cancelled) és egy időbélyeget. A kognitív terheléselmélet szempontjából a TODO lista külső memóriaként szolgál – ahogy az emberek is ellenőrzőlistákat írnak összetett projektek kezelésekor, az ügynöknek is szüksége van egy helyre, ahol rögzítheti, hogy "mi történt meg és mi van hátra." A kísérleti adatok azt mutatják, hogy a TODO támogatással rendelkező ügynökök átlagosan 15 iteráció alatt teljesítik a feladatokat, míg anélkül 21 iterációra van szükségük, és gyakran hiányoznak a részfeladatok.
>
> "Részletes Hiba Információ": Négy réteget tartalmaz – hiba típusa és leírása, teljes paraméter JSON, hívási verem információ és célzott javítási javaslatok (pl. FileNotFoundError esetén javasolja az elérési út ellenőrzését, a munkakönyvtár megtekintését és abszolút elérési utak használatát). Ha engedélyezve van, ez az információ az ügynök hibából való helyreállítási sikerességi arányát 60%-ról 95%-ra emeli. Ahelyett, hogy vakon újrapróbálkozna, az ügynök diagnosztizálhatja a hibát és alternatívát választhat.
>
> "Rendszerállapot Tudatosság": Olyan információkat injektál, mint az aktuális idő, munkakönyvtár, operációs rendszer típusa, shell környezet és Python verzió. A munkakönyvtár követése különösen kritikus – automatikusan frissül, miután az ügynök végrehajt egy `cd` parancsot, biztosítva, hogy a későbbi műveletek a megfelelő kontextusban történjenek. Az operációs rendszer információ lehetővé teszi az ügynök számára, hogy platform-specifikus döntéseket hozzon (pl. `apt` használata Linuxon, `brew` macOS-en).
>
> Ezek a technikák együttesen egy emergens hatást produkálnak (azaz korlátozott hatékonyságúak egyenként, de váratlanul erősek kombinálva). Az időbélyegek és az eszközszámlálók kombinációja lehetővé teszi az ügynök számára, hogy megértse a műveletek gyakoriságát és időbeli eloszlását; a TODO listák és a rendszerállapot kombinációja lehetővé teszi az ügynök számára, hogy a feladatstratégiákat a környezethez igazítsa; a részletes hiba információk és az eszközszámlálók kombinációja lehetővé teszi az ügynök számára, hogy ne csak stratégiát váltson többszöri kudarc után, hanem megértse a kudarc okát is.
>
> Egy ügynök, amelyen minden technika engedélyezve van, nem csupán egy eszköz, amely mechanikusan végrehajtja az utasításokat; állapottudatos asszisztenssé válik. Amikor egy fájl nem található, először ellenőrzi a könyvtárat, majd kilistázza az elérhető fájlokat, és ha még mindig nem találja, a TODO-ban törli a feladatot és hozzáad egy alternatívát. Ezt az adaptív viselkedést egyetlen technika sem képes egyedül elérni.
>

### A Leolvasásoktól a Stratégiáig: Az Ügynök Fizikai Idő Érzékelése

A 2-8. kísérlet öt technikája közül az időbélyeg követés és az eszközhívás számláló egymáshoz nem kapcsolódó metainformációnak tűnhet. Együtt azonban egy alapvetőbb képességre mutatnak: lehetővé teszik az ügynök számára, hogy viselkedését a fizikai időhöz igazítsa és ennek megfelelően szabályozza a tempóját. Amikor egy embert megkérnek, hogy "írjon egy bekezdést három perc alatt" kontra "írjon egy bekezdést harminc perc alatt," a kimenet eltér. A mai csúcskategóriás ügynökök esetében azonban a kimenet gyakran szinte azonos. Az ügynök nehezen tudja megállapítani, hogy egy munka befejeződött-e, egy akadály állandó vagy átmeneti, vagy hogy egy három perce futó eszközhívás még mindig halad-e vagy leállt. A szerző és munkatársai ezt a hiányzó képességet "időérzéknek" nevezik, és három mérhető tengelyre bontják[^ch2-8]:

- "Sürgősség" – A költségvetési tengely: Az erőfeszítés összehangolása az idővel. Ha szűk az idő, határozottan szállítson bizonytalanság mellett; ha bőséges az idő, ásson mélyebbre, ellenőrizzen többet és csiszoljon tovább. Kétirányú: alacsony sürgősség nem azt jelenti, hogy "kevesebbet csinálj," hanem hogy "ne állj meg még; folytasd."
- "Kitartás" – A végpont tengely: A valódi blokkolók megkülönböztetése az átmenetiektől, és annak tudása, hogy egy feladat befejeződött-e. A kudarc mindkét végleten előfordul: egy helyreállíthatatlan hiba ismételt újrapróbálása (egy 410 Gone végpont ötszöri újrapróbálása) vagy egy helyreállítható hiba túl korai feladása ("információ nem található" csak két keresés után).
- "Éberség" – A monitoring tengely: A váratlan időzítés kezelése az eszközválaszokban, mint vizsgálandó bizonyíték. Egy hívás, amelynek 500ms alatt kellene visszatérnie, de 5 másodpercet vesz igénybe, és egy hívás, amely 1ms alatt "sikerül," de üres törzset ad vissza, mindkettő jel – feltéve, hogy az ügynök figyeli ezeket a leolvasásokat.

Ez a háromtengelyű keret közvetlenül leképezhető az állapotsávra: az időbélyegek jeleket szolgáltatnak a sürgősséghez és az éberséghez, míg az eszközhívás számláló a kitartáshoz szolgáltat jeleket. Azonban **a leolvasások egyszerű megmutatása a modellnek nem elég a viselkedés megváltoztatásához**. Egy benchmark négy feltételt hasonlított össze: nincs időinformáció, csak nyers időbélyegek, időbélyegek plusz utasítások az értelmezésükhöz, és egy ügynök által generált tempóértékelés. A nyers időbélyegek majdnem ugyanolyan teljesítményt nyújtottak, mint a semmilyen időinformáció, mindössze két-három százalékpontos eltéréssel. Ami a passz arányt alig több mint 10%-ról 40-50%-ra, azaz 19-49 százalékpontos növekedésre emelte, az a működési iránymutatás volt. Más szóval, a modell láthatja `elapsed_ms=5000 expected_ms=500`, de nem fogja automatikusan beállítani a tempóját. Ami hiányzik, az nem a leolvasás, hanem a "stratégia a leolvasásra való reagáláshoz".

Ez kitölti a korábban a szakaszban hagyott rést. Az eszközhívás számláló képes korrigálni a viselkedést az egyszeri "Ez a #3 hívás (3/3)" leolvasással, mert a döntési szabály nyilvánvaló: állj le, ha a korlát elérésre került. Az olyan tempóbeli döntéseknél, mint "mennyi erőfeszítést fordítsak" vagy "megkerüljem ezt az akadályt," a szabályok kevésbé nyilvánvalóak, és a modell nem tudja megbízhatóan kikövetkeztetni a helyes cselekvést a nyers leolvasásokból. Egy hatékony "tempó állapotsávnak" ezért szüksége van mind a "leolvasásra" (mennyi ideig tartott a feladat, lassú-e ez az eszköz, hányszor találkoztam ezzel az akadállyal), mind egy rövid "működési stratégiára" (szállíts, ha szűk az idő, diagnosztizáld a lassú hívásokat, kerüld meg a kemény blokkolókat). Egyik sem elegendő önmagában. Az explicit leolvasások nyersanyagok; a modellnek szüksége van iránymutatásra is, amely a leolvasásokat cselekvésekké alakítja.

Ez a rés nem specifikus egyetlen modellre sem. Hat modellen keresztül, négy gyártócsaládból – Claude-tól, Gemini-n, GPT-n át Qwenig – működési iránymutatás nélkül a passz arány alig 10% felett maradt. Ez arra utal, hogy a jelenlegi tanítás utáni képzés gyakran nem tanítja meg az időérzékeny irányítási viselkedést, nem pedig azt mutatja, hogy egy adott modell intelligenciahiányban szenved. A rés következtetési időben kezelhető a fent leírt "állapotsáv + működési iránymutatás" megközelítéssel. Ha egy kisebb modellnek szüksége van erre a tempóérzékre anélkül, hogy promptokra támaszkodna, akkor a súlyokba is desztillálható. A 7. fejezet a tanítás utáni képzésről tárgyalja ezt a tanítási utat és egy fontos kontrasztot: a ritka kimeneti jutalmak nem váltották ki a viselkedést, míg a sűrű token szintű jelek sikeresek voltak.

[^ch2-8]: Li, Bojie and Noah Shi. *Agents That Sense Physical Time: Urgency, Persistence, and Vigilance as Missing Controls for LLM Agents.* 2026. https://01.me/research/physical-time-agent

### Tervezési Filozófia

Ennek a technikakészletnek van egy gyakorlati előnye: minden metainformáció ember által olvasható formában jelenik meg a kontextusban, lehetővé téve a fejlesztők számára, hogy ellenőrizzék, milyen információt kapott az ügynök és milyen döntéseket hozott. Még fontosabb, hogy a megközelítés nem igényel változtatásokat a modellen. Nincs szükség finomhangolásra; a technikák bármely nyelvi modellel működnek, és szükség szerint egyenként vagy kombinálva tesztelhetők.

## Kontextustömörítési Stratégiák

Az előző szakaszok arról szóltak, mit vegyünk fel a kontextusba: a prompt tervezés meghatározza, mit írjunk, a Készségek meghatározzák, mit töltsünk be igény szerint, és az Ügynöki Állapotsáv meghatározza, milyen metainformációkat injektáljunk. Ahogy a többfordulós interakciók mélyülnek, a kontextus azonban folyamatosan bővül. Ez a szakasz az ellenkező problémára tér rá: "hogyan csökkentsük a kontextus tartalmát" – mikor kell tömöríteni, hogyan kell tömöríteni, és miért lehet hasznos a tömörítés már azelőtt, hogy a kontextusablak megtelne.

### Miért Van Szükség Tömörítésre: Nem Csak Hosszkérdés

A kontextustömörítésnek két különálló motivációja van. Mindkettő megértése kulcsfontosságú a hatékony tömörítési stratégia kialakításához.

**Először is, a hossz- és költségkorlátok kezelése.** Ez a legintuitívabb ok: a kontextusablak korlátozott (pl. 128K token), az eszközhívási eredmények rutinszerűen több tízezer karaktert tesznek ki, és néhány kör interakció megtöltheti az ablakot, megszakítva a feladatot. A több token magasabb API költségeket és drámaian magasabb következtetési késleltetést is jelent.

**Másodszor, az érvelés minőségének javítása – az összegzett tudás hasznosabb a modell számára, mint a nyers információ.** Ez a motiváció mélyebb és könnyebb figyelmen kívül hagyni. Még ha a kontextusablak elég nagy is, nem mindig a legjobb választás az összes nyers információ hozzáadása a kontextushoz.

Vegyünk egy konkrét példát: egy összetett feladat során egy ügynök 10 webes keresésen keresztül gyűjt információt egy témáról. Ezek a keresési eredmények nyers formájukban szétszórva vannak a kontextusban – a 2. kör eredményei az elején, a 9. kör eredményei a végén vannak. Amikor az ügynöknek mindebből az információból kell végső döntést hoznia, több tízezer token között kell megtalálnia a releváns töredékeket. A figyelme szétszóródik, és könnyen figyelmen kívül hagyhat kulcsfontosságú információkat.

A 10. keresés után azonban egyetlen LLM hívással strukturált összefoglaló készíthető a felhalmozott információkból: "Jelenleg ismert: A..., B..., a C-ről szóló információ még hiányzik." A modell ezt a finomított tudásreprezentációt használhatja a későbbi érvelésben, anélkül, hogy újra kivonná a nyers adatokból.

A kiváltó ok a figyelmi mechanizmus természetében rejlik: **a kontextuson belüli tanulás belső mechanizmusa inkább hasonlít a visszakeresésre, mint az érvelésre.** Az 1. fejezet röviden bevezette ezt a fogalmat, és az Ügynöki Állapotsáv szakasz kibővítette mechanizmusokon, empirikus bizonyítékokon és mérnöki gyakorlatokon keresztül. Ezután megvizsgáljuk, mit jelent ez a tömörítés szempontjából.

### A Kontextuson Belüli Tanulás Belső Mechanizmusa: Visszakeresés, Nem Érvelés

Röviden, a "visszakeresés, nem érvelés" azt jelenti, hogy a figyelem jó a meglévő tartalom felkutatásában, de nem jó az aggregált összefoglalók aktív kiszámításában egyetlen előreirányuló menetben. Ez nem tagadja, hogy a modell lépésről lépésre tud érvelni gondolkodási lánc generálásával; azt jelenti, hogy a meglévő kontextus fogyasztása egyetlen előreirányuló menetben inkább visszakeresésszerű. A tömörítésre gyakorolt következmény világos: az Állapotsáv "hozzáadja" a kiszámított következtetéseket "a" kontextushoz, míg a tömörítés "lecseréli" a dagályos nyers rekordokat "a" kiszámított következtetésekkel. Mindkettő biztosítja azt a desztillációs réteget, amely a nyers figyelemből hiányzik. A különbség az, hogy az Állapotsávot általában determinisztikusan, lépésről lépésre, "kód" tartja karban, míg a tömörítés gyakrabban használ LLM hívást egy nagy blokk eredeti szöveg desztillálására.

Egy egyszerű példa konkrétan megvilágítja a "visszakeresés, nem érvelés" gondolatát. Tegyük fel, hogy a kontextus egy állatkereskedés ellenőrzésének naplóját tartalmazza:

> 1-es ketrec: Fekete macska. 2-es ketrec: Fehér macska. 3-as ketrec: Fekete macska. 4-es ketrec: Fekete macska. 5-ös ketrec: Fehér macska.
> ... (100 ketrec összesen, 90 fekete macska, 10 fehér macska)

Amikor megkérdezzük a modelltől: "Hány fekete macska és hány fehér macska van?" mi történik?

Ha az érvelés nincs engedélyezve, a modell nehezen tudja közvetlenül megadni a helyes választ – mert a figyelmi mechanizmus a "keresésre" jó ("Milyen macska van a 37-es ketrecben?"), nem az "aggregálásra" ("Hány fekete macska van összesen?"). Az utóbbihoz az összes rekordon végig kell menni és számlálási állapotot kell fenntartani, ami lényegében érvelés, nem visszakeresés.

Ha az érvelés engedélyezve van, a modell egyenkénti megszámlálással megkaphatja a helyes választ. Az ára az, hogy minden alkalommal, amikor ezt a kérdést felteszik, a semmiből kell elkezdenie a számolást, sok érvelési tokent generálva. Egy ügynöki forgatókönyvben, ahol ilyen statisztikai információkra ismételten szükség van (pl. minden döntésnél), a halmozott érvelési költség nagyon magas lesz.

Ha azonban előre összefoglaljuk a rekordokat, és "Jelenlegi statisztika: 90 fekete macska, 10 fehér macska" közvetlenül a kontextusba írjuk, a modell kiolvashatja a következtetést anélkül, hogy megismételné a számolást. **Ez a tömörítés második értéke: az érvelést igénylő következtetéseket közvetlenül lekérhető tudássá alakítani.**

A mélyebb probléma az, hogy a hosszú kontextusok csökkentik a visszakeresés pontosságát. Még ha a kontextusablak messze van is a telítettségtől, az ügynök hirtelen nem találhat kulcsfontosságú információt, vagy ismételten egy már megoldott problémára összpontosíthat. Ezt a jelenséget "Kontextus Rotnak" (rothadásnak) nevezik. A kontextus rot különbözik a kontextus túlcsordulástól (az ablakhely kifogyása): a túlcsordulás azt jelenti, hogy "nem fér el több," míg a rot azt jelenti, hogy "elfér, de nem található." Az utóbbi alattomosabb, mert az ügynök látszólag normálisan dolgozik, miközben döntéseinek minősége csendben romlik. Ahogy a kontextus hossza nő, a figyelmi súlyok több token között oszlanak el, csökkentve az egyes tokenek által kapott súlyt. Még fontosabb, hogy ha az irreleváns tartalom uralja a kontextust, az ügynök döntési minősége romlik. A gyakorlatban a leggyakoribb meghibásodási mód nem egy túl kicsi kontextusablak, hanem egy túl alacsony információsűrűség: a csak alkalmanként szükséges tudás minden alkalommal betöltődik, a stabil szabályok összekeverednek a dinamikus állapottal, és a modell több tartalmat lát, miközben a hasznos részeket nehezebb észrevenni. Hasznos analógia, ha egy könyvet keresünk egy nagy könyvtárban: minél több irreleváns könyv van a polcokon, annál nehezebb megtalálni a célt. A 2-2. kísérlet figyelmi vizualizációja világosan demonstrálja ezt a jelenséget: hosszú kontextusokban a modell figyelme erős pozíciós torzítást mutat. Ezt a problémát tárja fel a híres "Tű a szénakazalban" kísérlet, amely egy kulcsfontosságú információt egy nagyon hosszú szöveg közepébe rejt, és teszteli, hogy a modell megtalálja-e.

Andrej Karpathy egy mélyreható felismerést fogalmazott meg: a modell "rossz memóriája" bizonyos mértékig inkább jellemző, mint hiba – a korlátozott kontextusablak arra kényszeríti a modellt, hogy megtanulja általános mintákká absztrahálni a nagy mennyiségű részletet, ahogy az emberek sem emlékeznek minden beszélgetés szó szerinti tartalmára, hanem általános benyomást és viselkedési mintákat desztillálnak.

Ez feltárja a kontextustömörítés tervezési elvét: ahelyett, hogy elvárnánk a modelltől, hogy automatikusan tanuljon a hosszú kontextusból, inkább desztilláljuk explicit módon ezt a tudást. Bár ez további számítást igényel az összegzéshez, tömör, információban gazdag reprezentációkat eredményez. **Ne hagyjuk, hogy a modell passzívan keresgéljen hatalmas mennyiségű nyersanyagban; biztosítsunk finomított, strukturált tudást.**

Ebből a perspektívából a kontextuson belüli tanulás inkább egy gyors alkalmazkodási mechanizmus, mint valódi tanulás. Lehetővé teszi a modell számára, hogy gyorsan igazítsa viselkedését a következtetés során egy adott feladathoz, de ez az igazítás átmeneti és felületes, a munkamenet végétől eltűnik. Friss elméleti kutatás[^ch2-6] alátámasztja ezt az ítéletet: amikor a modell példákat lát a kontextusban, a viselkedése olyan, mintha "ideiglenesen testre lett volna szabva" – anélkül, hogy a modell paraméterei változnának, de egy kisméretű, speciális tréninghez hasonló hatással. Ez megmagyarázza, hogy a prompt tervezés szakaszban lévő kevés lépésből álló példák miért javíthatják jelentősen a kimenet minőségét, és azt is, hogy ez a javulás miért nem halmozódik fel a munkamenetek között – alapvetően különbözik a valódi paramétertanítástól.

[^ch2-6]: Benoit Dherin et al., "Learning without training", 2025.

### Tömörítés és KV Cache: Látszólagos Ellentmondás, Gyakorlati Kiegészítés

Mielőtt konkrét tömörítési stratégiákat tárgyalnánk, fel kell oldanunk egy látszólagos ellentmondást: a korábbi szakaszok hangsúlyozták, hogy a KV Cache megköveteli a kontextus előtagjának változatlanságát, de a tömörítés magában foglalja a kontextus közepén lévő tartalom módosítását.

A kulcs a tömörítés "időzítésének és helyének" megértése. A tömörítés nem módosítja a kontextust egyetlen API hívás során; helyette a "két API hívás között" történik, amikor az ügynök-keretrendszer előfeldolgozza az üzenetlistát:

1.  **A Rendszer Prompt és az Eszközdefiníciók soha nem érintettek** – ez a "statikus előtag" a kontextus legelején, és a KV Cache folyamatosan gyorsítótárazva van.
2.  **A tömörítés célpontja a beszélgetéstörténetben lévő eszközeredmények** – amikor az ügynök-keretrendszer lecseréli az eredeti eszközkimenetet egy tömörített összefoglalóra, a csere pontja utáni gyorsítótár érvénytelenné válik, de az előtte lévő gyorsítótár érvényes marad.
3.  "Ez egy tudatos kompromisszum": tömörítés nélkül a kontextus az ablakkorlát fölé nő, és a feladat teljesen meghiúsul; a tömörítéssel némi gyorsítótár elveszik, de a kontextus hossza ellenőrzés alatt marad, és az információsűrűség nő. Ezért mérlegelni kell a tömörítés gyakoriságát – a gyakori tömörítés gyakran töri meg a gyorsítótárat. A legjobb, ha batch tömörítést végzünk, amikor a kontextus megközelíti a küszöböt, ahelyett, hogy minden körben tömörítenénk.

![Figure 2-16: Kontextustömörítési Stratégiák Összehasonlítása](images/fig2-16.png)

> **Kísérlet 2-9 ★★★: Kontextustömörítési Stratégiák Összehasonlítása**
>
> Terveztünk egy kutatási feladatot: az OpenAI társalapítóinak foglalkoztatási státuszának azonosítása és nyomon követése. Ez a feladat többlépéses információ aggregálást igényel, a keresési eredmények hossza nagyon változó (néhány ezertől több mint százezer karakterig), és vannak egyértelmű sikerességi kritériumok. A Kimi K3-at használva (egy érvelő modell, amely natívan körülbelül 1 millió token kontextussal rendelkezik; ez a kísérlet szándékosan 128K ablakra korlátozta a kontextus költségvetést a tömörítés kiváltásához), hat stratégiát implementáltunk:
>
> **1. stratégia: Nincs tömörítés** – Az összes eredeti eszközhívási eredmény érintetlen marad. A több keresés összesen körülbelül 367 000 karaktert adott vissza (7 eszközhívás, átlagosan körülbelül 52 000 karakter egyenként). Az ötödik iterációra a halmozott kontextus meghaladta a 128K korlátot (körülbelül 165 000 token), kiváltva a túlcsordulás elleni védelmet és a feladat meghiúsulását. Már néhány keresés is elegendő volt a 128K ablak kimerítéséhez.
>
> **2. és 3. stratégia: Nem Feladattudatos Tömörítés** – Az Egyedi Összegzés minden keresési eredményhez egymástól függetlenül 2-3 bekezdéses összefoglalót generál, 10,9%-os tömörítési aránnyal (ebben a könyvben a tömörítési arány "tömörített térfogat / eredeti térfogat"; kisebb szám agresszívebb tömörítést jelent). Képes elvégezni a feladatot, de 12 iterációt és 276 608 tokent igényel. A fő probléma az információ töredezettsége – több oldal ismételten ugyanazt az eseményt írja le, pazaro Helyet. Az Összevont Összegzés az összes eredményt egyetlen átfogó összefoglalóba egyesíti, 4,3%-os tömörítési aránnyal, 10 iterációt és 93 449 tokent igényelve. Azonban ha a bemenet rendkívül hosszú, le kell vágni, potenciálisan elveszítve a végén lévő információkat. Mindkettő közös hibája a szemantikai megértés hiánya, ami lehetetlenné teszi az információk relevanciájának megkülönböztetését.
>
> **4. stratégia: Kontextustudatos Tömörítés** – A központi újítás a jelenlegi lekérdezési szándék és a felhalmozott információ beépítése a tömörítési döntési folyamatba. A tömörítési promptban a "Given the search query: {query}" és "Current context: {context}" megadásával a modellt célzott összefoglalók generálására irányítjuk. Az eredmény csak 7 iterációt és 40 157 tokent igényel, körülbelül 3,0%-os általános tömörítési aránnyal. Egy tömörítési esetben 147 877 karaktert 1 963 karakterre tömörítve (körülbelül 1,3%) továbbra is megőrizte a kulcsfontosságú információkat, mint az alapítók nevei és pozícióváltozások; a későbbi keresések intelligensen ki tudták vonni a kulcsfontosságú információkat, mint a pozícióváltozások és új cégek, kiszűrve az irreleváns történelmi hátteret és duplikált tartalmat. Ez a siker egy kulcsfontosságú felismerésen alapul: a többlépéses feladatokban a szükséges információsűrűség és típus a különböző szakaszokban változik – a korai szakaszokban széles körű információgyűjtésre van szükség, a középső szakaszokban pontos tényellenőrzésre, a későbbi szakaszokban átfogó információszintézisre. A kontextustudatos tömörítés maximalizálja az információértéket a tömörítés fókuszának dinamikus beállításával.
>
> **5. stratégia: Kontextustudatos Idézetekkel** – Hozzáadja az információ származását az intelligens tömörítéshez, minden tényhez forrás URL idézet jelölőt csatolva. A tokenhasználat 222 992-re nő, 4,1%-os tömörítési aránnyal, de az idézetek lehetővé teszik az ellenőrzést. Ez kombinálja a veszteséges szemantikai tömörítést a veszteségmentes indexeléssel: bár a tartalom tömörítve van, a megtartott forráslinkek lehetővé teszik a rendszer számára, hogy visszatérjen az eredeti anyaghoz.
>
> **6. stratégia: Adaptív Ablakozás** – Egy kulcsfontosságú felismerésen alapul: a feladat korai szakaszában a kontextushely bőséges, így nincs szükség a tömörítésre sietni. A tömörítési mechanizmus csak akkor aktiválódik, amikor megközelítjük a kapacitáskorlátot, ezáltal a lehető legnagyobb mértékben megőrizve az eredeti információ integritását. A konkrét implementáció három alapvető mechanizmust foglal magában:
>
> - "Küszöbérték Trigger": Folyamatosan figyeli a kontextushasználatot. A tömörítés csak akkor aktiválódik, ha a prompt tokenek száma meghaladja az ablak 80%-át (102 400 token egy 128K ablak esetén).
> - "Batch Tömörítés": Aktiváláskor az összes megjelöletlen eszközeredményt egyszerre tömöríti. Például a negyedik iteráció körül, amikor a kontextus érzékeli, hogy meghaladja a 102 400 token küszöbértéket (a gyakorlatban körülbelül 135 600 token esetén aktiválódott), mind a 10 tömörítetlen eszközüzenet azonnal tömörítésre kerül.
> - "Duplikáció Megelőzése": Hozzáad egy `[COMPRESSED]` jelölőt, hogy a tömörített tartalom soha ne kerüljön újra feldolgozásra.
>
> Bár a teljes tokenhasználat viszonylag magas (174 601), az első néhány iteráció megtartja a teljes eredeti információt, maximális rugalmasságot biztosítva a kezdeti széles körű információgyűjtéshez.
>
>
> ![Figure 2-17: Hat Tömörítési Stratégia Feldolgozási Folyamata](images/fig2-17.png)
>
>

### Production-szintű Hierarchikus Tömörítési Mechanizmus

A fenti kísérlet bemutatja a tömörítési stratégiák közötti teljesítménybeli különbségeket. Production környezetben az érett ügynökrendszerek általában nem támaszkodnak egyetlen stratégiára. Ehelyett több stratégiát kombinálnak egy hierarchikus tömörítési mechanizmusba. A különböző típusú információk eltérő ideig maradnak hasznosak, ezért a tömörítési stratégiának meg kell egyeznie az információ várható életciklusával. A Claude Code megközelítését referenciaként használva, egy érett kontextuskezelő rendszer általában öt réteget foglal magában:

1.  "Eszközeredmény Költségvetés Vezérlés": A nagy eszköz kimenetek lemezre kerülnek; a modell csak egy előnézeti összefoglalót lát. A cserére vonatkozó döntések az első meghozatalukkor rögzülnek a gyorsítótár konzisztencia biztosítása érdekében.
2.  "Közvetlen Zaj Törlés": Az alacsony értékű tartalom (pl. egy nagy keresési eredményhalmaz tartalma, amelyet csak néhány sorra használtak) eltávolításra kerül összegzés nélkül – a zaj összegzése tokent pazaro.
3.  "API-Szintű Mikro-Tömörítés": Kihasználja az API kontextusszerkesztési képességeit, hogy utasítsa a szervert bizonyos eszközeredmények eltávolítására az előtagból, miközben a helyi üzenetlista változatlan marad. Ennek a rétegnek az előnye a nulla lokális implementációs költség – a szerver egy menetben kezeli. Azonban a fejezet előtagváltozatlansági elve szerint az eltávolítási pont utáni gyorsítótár szintén érvénytelenné válik, ami gyorsítótár újraépítést igényel. Ezért akkor használható, ha a kontextus éppen túl akar csordulni, és a gyorsítótár újraépítésének költségét úgyis ki kell fizetni, nem pedig gyakran aktiválódó mechanizmusként.
4.  "Archiváló Összegzés": Strukturált összegzést végez körönként (mint a `git log`, megtartva egy független rekordot minden körhöz, nem pedig mint a `git squash`, amely egyesíti őket), megőrizve a beszélgetés logikai szálát.
5.  "Teljes Tömörítés": LLM által vezérelt teljes tömörítés, végső megoldásként használva. Még ez is két szakaszban történik: először próbálja meg tömöríteni a munkamenet memóriát; ha ez sikertelen, teljes tömörítést végez. A teljes tömörítés egy megszakítóval is fel van szerelve az egymást követő hibákhoz (egy mechanizmus, amely automatikusan leállítja az újrapróbálkozást bizonyos számú egymást követő hiba után) – production adatok azt mutatják, hogy sok munkamenet elakad az ismétlődő tömörítési hibák hurkaiban, és a megszakító megakadályozza a szükségtelen költekezést ezeken a munkameneteken.

Az öt réteg sorrendje számít. Az első három a legalacsonyabb implementációs költségű, és a gyorsítótárra gyakorolt hatásuk a leginkább kontrollálható, ezért ezeket kell először használni. Az utolsó kettő magasabb költségű, de erősebb tömörítési hatással rendelkezik, és tartalék módszerként kell szolgálniuk.

### Tömörítési Stratégiák Tervezési Elvei

Már elemeztük a tömörítés két motivációját – a hossz szabályozása és az érvelés minőségének javítása – valamint azt a belső mechanizmust, hogy "a kontextuson belüli tanulás lényegében visszakeresés." Ennek alapján négy elvet desztillálhatunk, amelyek irányítják a konkrét tömörítési stratégiák tervezését. Az itt tárgyalt tömörítés a jelenlegi feladatot szolgálja; amikor több feladatból származó trajektóriákat kell offline konszolidálni tartós tapasztalattá, a probléma folyamatos evolúcióvá válik, amelyet a 8. fejezet tárgyal.

- "Az Információérték Nem Egyenletes Eloszlása": A kulcsfontosságú döntési pontok, mint a személyi listák, nagyobb értékkel bírnak, mint a támogató bizonyítékok, mint a hírrészletek; a támogató bizonyítékok nagyobb értékkel bírnak, mint a redundáns zaj, mint a navigációs sávok és lábléc hirdetések.
- "Szemantikai Integritás": "Sutskever elhagyta az OpenAI-t 2024 májusában" nem tömöríthető "Sutskever elhagyta" formára – az idő és a cég neve kritikus, nem alku tárgyát képező információ.
- "Feladat Relevancia": Ugyanaz a tartalom különböző tömörítési eredményeket kell, hogy adjon különböző feladatokhoz, mint "találd meg az alapítók listáját" versus "ismerd meg a személyes hátteret."
- "A Tömörítés Megértés": A hatékony tömörítés mély szemantikai megértést igényel – a kontextus magjának rögzítését finomabb kifejezéssel. Ráadásul az explicit tömörítés eredményei felülvizsgálhatók és újra felhasználhatók a munkamenetek között.

### Következmények az Ügynökarchitektúra Tervezéséhez

A kontextustömörítési stratégiák kutatása az ügynökrendszerek tervezésének alapvető kérdéseire mutat rá. "A Tömörítés Megértés": a tömörítésért felelős modulnak a fő modellhez közeli nyelvi megértési képességekre van szüksége, ami rekurzív modellhívási architektúrát alkot. **A Tömörítési Stratégia Össze van Kapcsolva a Feladat Típussal**: az információ-visszakeresési feladatoknak meg kell őrizniük a szélességet, az elemzési feladatoknak a mélységet, a kreatív feladatoknak pedig az inspirációs triggerjeit. A jövő ügynökeinek adaptívan kell kiválasztaniuk a tömörítési stratégiákat a feladat típusa alapján.

Bár a tömörítés számítási többletköltséggel jár, mert minden tömörítés egy extra LLM hívást igényel, a befektetés megtérülése rendkívül magas lehet a megtakarított token költségekhez és a feladat sikerességének javulásához képest. A kísérletek azt mutatják, hogy a kontextustudatos tömörítés több mint 75%-kal csökkenti a tokenhasználatot.

Amit a tömörítés a legkönnyebben elveszít, az nem maguk a részletek, hanem **a korai architekturális döntések, a korlátok mögötti érvelés és a sikertelen utak** – az LLM-ek általában előnyben részesítik az olyan információk törlését, amelyek úgy tűnik, újra megszerezhetők. Production-szintű ügynökrendszerekben ajánlott explicit módon meghatározni a megtartási prioritásokat a tömörítés során:

1.  "Architekturális Döntések és Kulcsfontosságú Korlátok": Nem szabad összefoglalni.
2.  **Módosított Fájlok Listája és Kulcsfontosságú Változtatási Rekordok**: Teljes egészében megőrizni.
3.  "Ellenőrzési Státusz" (sikerült/megbukott): Meg kell tartani.
4.  "Megoldatlan TODO-k és Visszaállítási Jegyzetek": Meg kell tartani.
5.  "Eszközkimenet": Törölhető, csak a sikerült/megbukott következtetést megtartva.

Továbbá az olyan azonosítókat, mint az UUID-k (Univerzálisan Egyedi Azonosítók), hashek, IP-címek, portszámok, URL-ek és fájlnevek, "pontosan úgy kell megőrizni, ahogy vannak" – ha akár egy számjegy is megváltozik egy PR-számban vagy commit hash-ben, az a későbbi eszközhívások közvetlen meghiúsulását okozza.

### Elszigetelés a Tömörítés Helyett: Részügynök Kontextus Elszigetelés

A tömörítés *utólag* távolítja el az információt, miután az már bekerült a kontextusba. Egy közvetlenebb megközelítés az, ha a terjedelmes köztes információt eleve távol tartjuk a fő kontextustól. Ez a "Részügynök Kontextus Elszigetelés": a fő ügynök olyan feladatokat delegál, amelyek nagy mennyiségű köztes tartalmat generálnak, mint "olvass el egy nagy számú fájlt" vagy "végezz széles körű keresést a kódbázisban," egy független részügynökre. A részügynök elvégzi a feltárást a saját kontextusában, és csak egy tömör, néhány száz tokenes összefoglalót ad vissza a fő ügynöknek.

Hasonlítsuk össze a két megközelítést ugyanarra a feladatra – "találd meg a függvényt, amely kezeli a fizetési visszahívásokat a kódbázisban." Ha a fő ügynök maga keres, több tucat fájlt és több tízezer tokennyi nyers kódot hozhat a fő kontextusba. Miután a cél megtalálásra került, ennek az anyagnak a nagy része tartós zajként marad az ablakban, és később tömörítésen keresztül kell eltávolítani. Ha azonban egy kereső részügynökre delegáljuk, a fő kontextus csak két üzenetet kap: egy feladatleírást és egy következtetést ("A függvény a `handle_callback` a `src/payment/callbacks.py` fájlban, két másik hívási hellyel") – a köztes folyamat több tízezer tokene a részügynök kontextusával együtt eldobásra kerül.

Ez lényegében "a tömörítés cseréje elszigetelésre": a tömörítés veszteséges, utólagos gyógyír, amely extra LLM hívásokat igényel, míg az elszigetelés eleve távol tartja a zajt a fő kontextustól, és nem érinti a fő ügynök KV Cache előtagját. Az ára az, hogy a részügynök nem látja a fő ügynök teljes kontextusát, ezért a feladatleírásnak önállónak kell lennie, és a célnak világosnak kell lennie. Ez visszatér a fejezet központi témájához: a kontextus határozza meg a képesség felső korlátját, és ez a részügynökökre is igaz. A Claude Code Task eszköze és a Deep Research rendszerekben használt visszakereső részügynökök ennek a mintázatnak a production implementációi. A 4. fejezet tárgyalja a részügynökök mint együttműködő eszközök teljes tervezését, a 10. fejezet pedig a többügynökös rendszerek kontextusarchitektúráját.

## Fejezet Összefoglalása

A fejezet számos technikai részlete között egy központi érv húzódik: az, hogy mit mutatunk a modellnek, és hogyan szervezzük azt, többet számít a végeredmény szempontjából, mint az, hogy mennyire képzett maga a modell. Az API üzenetstruktúrája meghatározza a kontextus alapvető szerkezetét; a KV Cache korlátozza, hogy mi változhat és mi nem; a prompt tervezés és az Ügynöki Készségek határozzák meg, hogyan biztosítsunk hatékonyan statikus utasításokat és dinamikus tudást a modell számára; az Ügynöki Állapotsáv a burkolt állapotokat közvetlenül felhasználható explicit információvá alakítja; a tömörítési stratégiák pedig a folyamatosan bővülő kontextus problémáját kezelik – nemcsak a hossz szabályozásával, hanem a nyers adatok aktív összegzésével nagy sűrűségű strukturált tudássá.

Ezeknek a technikáknak a közös szálaz az explicit, tervezett információkezelés: ahelyett, hogy hagynánk a modellt passzívan keresgélni a hatalmas kontextusban, proaktívan biztosítsunk számára finomított, strukturált állapotot. Visszatérve Rich Sutton "Keserű Leckéjéhez," az általános módszerek, amelyek hatékonyabban használnak fel nagyobb számítási kapacitást, végül győzedelmeskednek. A fejezetben bemutatott minden technika – a KV Cache-barát kontextuselrendezésektől a kontextustudatos tömörítésig – annak a mérnöki gyakorlatnak a konkrét megvalósítása, hogy a jelenlegi modellképességi határon maximalizáljuk az információhatékonyságot. Egy megkülönböztetést explicit kell tenni: ez a fejezet az állapotfrissítésekkel és kontextusromlással foglalkozik "egyetlen feladaton belül". A 8. fejezet, "Ügynök Folyamatos Fejlődése," eltérő időskálán működik: azt vizsgálja, hogyan kell értékelni a trajektóriákat a feladatok között, és hogyan lehet közös mintázataikat olyan tartós frissítésekké alakítani, amelyek megváltoztatják a jövőbeli rendszerváltozatokat.

Visszatérve az 1. fejezet Hám keretrendszeréhez, a fejezet minden technikája annak "Kontextus és Eszközök" rétegében működik. Együtt határozzák meg, hogy az ügynök elegendő, finomított és strukturált információt kap-e minden döntési ponton. A Készségek fájlolvasáson keresztül eszközeredményként kerülnek be a trajektóriába, míg a tömörítés a meglévő trajektória-üzeneteket tömörebb reprezentációkkal helyettesíti. Az Ügynöki Állapotsáv csak API-szinten szokatlan: mivel nincs dedikált metainformációs szerep, egy `user` üzenetet használ a környezeti állapot és a feladat előrehaladásának hordozására. Szemantikailag kiegészíti a meglévő öt kontextuskomponenst, nem pedig egy hatodikat hoz létre. Az ötrészes struktúra változatlan; ez a fejezet hozzáadta a mérnöki részletességet.

A következő fejezet túllép az egyetlen kontextusablakon belüli információkezelésen, és a munkameneteken átívelő tartós tudásrendszerek felé halad: a felhasználói memória és a tudásbázisok. Ezek a rendszerek lehetővé teszik az ügynök számára, hogy idővel tapasztalatot halmozzon fel, és fokozatosan domain szakértővé váljon.

## Gondolkodtató Kérdések

1.  ★★★ A 2-3. kísérlet megállapította, hogy a csúszóablakos beszélgetéstörténet az ügynököt ugyanazon eszközhívások ismételt végrehajtására készteti. A teljes történet megtartása azonban a kontextus korlátlan növekedését okozza. Tervezzen egy stratégiát, amely elkerülheti az információvesztést, miközben szabályozza a kontextus hosszát, anélkül, hogy megtörné a KV Cache előtagot.
2.  ★★ A Qwen3 Chat Template gondolkodási lánc megtartási mechanizmusa csak az "utolsó valódi felhasználói üzenet utáni" érvelési tartalmat tartja meg. Ha egy ReAct hurok több száz eszközhívást foglal magában, a felhalmozott érvelési tartalom nagy mennyiségű kontextust fogyaszthat. Hogyan módosítaná ezt a mechanizmust a nagyon hosszú hurkok kezelésére? A DeepSeek R1 egykor az összes történelmi érvelési tartalom eltávolítását írta elő, míg a DeepSeek V4 ezt megfordította, hogy kötelező legyen az összes `reasoning_content` visszaadása – a két ellentétes stratégiát összehasonlítva, melyek az egyes előnyei és hátrányai? Mit jelez ez a fordulat?
3.  ★★ A kontextustudatos tömörítési kísérletben körülbelül 148 000 karakter tömörítése körülbelül 2 000 karakterre – ez a szélsőséges tömörítés kockáztatja a "visszafordíthatatlan információvesztést"? Hogyan lehet ezt kezelni?
4.  ★★ Az Ügynöki Állapotsáv explicité teszi a burkolt állapotokat. Ha azonban az állapotsáv maga hibás információt tartalmaz (pl. egy hiba az eszközszámlálóban), az ügynök helytelen információ alapján hozhat káros döntéseket. Hogyan lehet ezt a "metainformáció-megbízhatósági" problémát enyhíteni?
5.  ★★ A prompt tervezés ablációs kísérlete azt mutatja, hogy a rendezetlen információ több mint 30%-os sikerességi arány csökkenéshez vezet. A valós fejlesztésben azonban a rendszer promptot gyakran többen, különböző időpontokban karbantartják. Milyen mérnöki gyakorlatokat használna annak megakadályozására, hogy a rendszer promptok időben egyre rendezetlenebbé váljanak?
6.  ★★★ Ez a fejezet azt állítja, hogy "a kontextuson belüli tanulás lényegében visszakeresés, nem érvelés." Ha ez az állítás igaz, akkor az összes jelenlegi, "több információ kontextusba helyezésén" alapuló optimalizációs irányt újra kell értékelni. Ön szerint hogyan lehet ezt a korlátot leküzdeni?
7.  ★★★ A Készségek progresszív feltárása csak akkor tölti be a teljes tartalmat, amikor az ügynök úgy ítéli meg, hogy szükség van rá. Ez az ítélet azonban maga is a modell képességétől függ – ha a modell nem tudja, hogy mit nem tud, nem tudja helyesen kiváltani egy Készség betöltését. Hogyan lehet ezt a "metakogníciós" problémát megoldani?
8.  ★★ A Készségek mechanizmusában, miután az ügynök dinamikusan betölti az utasításokat a `SKILL.md`-ből, a későbbi műveletek megbízhatóan követik-e azokat? Milyen különbségek vannak a modelltámogatásban a Készségek mintázatához?
9.  ★★★ Ez a fejezet hangsúlyozza, hogy a dinamikus információk változásai (pl. rendszeridőbélyegek, eszközlista sorrendje) megtörhetik a KV Cache előtag találatokat. Egy nagy számú eszközzel és gyakran változó eszközkészlettel rendelkező production rendszerben hogyan tervezné meg a kontextus elrendezését a gyorsítótár találati arány maximalizálása érdekében?
