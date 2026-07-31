# Tanulási javaslatok

← [Vissza a magyar főoldalhoz](README.md)

## Alapgondolat: Ágens = Modell + Kontextus + Eszközök

A könyv központi kerete az **Ágens = Modell + Kontextus + Eszközök** képlet. A három összetevő együtt hoz létre intelligens viselkedést:

| Összetevő | Hasonlat | Feladat |
| :--: | :--: | --- |
| 🧠 **Modell** | Agy | Megértési, következtetési és döntéshozatali képességet biztosít |
| 💾 **Kontextus** | Operációs rendszer | Tartalmazza a rendszerutasításokat, a párbeszéd előzményeit, a következtetési folyamatot, az eszközhasználat nyomait és minden egyéb releváns információt |
| 🤲 **Eszközök** | Kéz | Érzékelik a környezetet, műveleteket hajtanak végre, és kapcsolatot teremtenek a külvilággal |

## Tanulási útvonal

| Szakasz | Fejezet | Témakör | Legfontosabb felismerés |
| --- | :--: | --- | --- |
| **Alapok** | 1. fejezet | Az ágens definíciója az RL-ben, a hagyományos RL és az LLM+RL mintahatékonysága, a „modell mint ágens” paradigma | Az előzetes tudás gyakran fontosabb, mint az algoritmus vagy a környezet |
| **Kontextus** | 2–3. fejezet | Rendszerprompt, KV Cache, kontextustömörítés, prompttervezés; felhasználói memória, sűrű/ritka/hibrid keresés, Agentic RAG | A teljes kontextus az utasításokat, előzményeket, következtetést, eszközhasználatot, memóriát és külső tudást egyaránt magában foglalja |
| **Eszközök** | 4–5. fejezet | MCP-alapú érzékelési, végrehajtási és együttműködési eszközök, eseményvezérelt aszinkron architektúra, kódoló ágensek | Az eszközök legyenek általánosak; a kód metaképesség új eszközök létrehozására |
| **Értékelés és evolúció** | 6–8. fejezet | Ágensértékelés, SFT és RL, tanulás a nyomvonalakból, a tudás, utasítások, programok és paraméterek frissítése | Ellenőrizhető tanulási jel nélkül nincs megbízható fejlődés; a frissítés hordozója attól függ, hogyan fejeződik ki és hogyan tesztelhető a képesség |
| **Kiterjesztés és együttműködés** | 9–10. fejezet | Beszéd, GUI, fizikai világ és több ágens munkamegosztása | Minden többágenses tervezési döntésnek van egyágenses megfelelője |

## Nehézségi szintek

| Szint | Fejezet | Kinek ajánlott? |
| --- | :--: | --- |
| 🟢 Kezdő | 1–2. fejezet | Az alapfogalmakat megismerni kívánó olvasóknak |
| 🔵 Középhaladó | 3–4. fejezet | Programozási alapismeretekkel és rendszerintegrációs érdeklődéssel rendelkezőknek |
| 🟣 Haladó | 5–6. fejezet | Erős programozási és összetett rendszertervezési tapasztalattal rendelkezőknek |
| 🔴 Szakértő | 7–8. fejezet | Mélytanulásban, modellképzésben vagy önfejlődő rendszerekben jártas olvasóknak |
| 🟠 Alkalmazott | 9–10. fejezet | Az előző részeket valós alkalmazássá összeépíteni kívánóknak |

## Gyakorlati tanácsok

| # | Tanács | Magyarázat |
| :--: | --- | --- |
| 1 | 🛠️ **Gyakorolj közvetlenül** | Futtasd és módosítsd a kapcsolódó projekteket, hogy az elmélet gyakorlati tudássá váljon |
| 2 | 📚 **Olvasd együtt a kézirattal** | A projektek kipróbálása közben olvasd el a megfelelő fejezetet a [`book-hu/`](../../book-hu/) könyvtárban |
| 3 | 🔬 **Hasonlítsd össze a kísérleteket** | Ablációs és összehasonlító vizsgálatokkal értsd meg az egyes összetevők hatását |
| 4 | 🪜 **Haladj fokozatosan** | Kezdd az egyszerű projektekkel, majd lépj tovább az összetettebb rendszerekre |
| 5 | 🔌 **Figyelj a protokollokra** | A 4. fejezet MCP-szerverei megmutatják, miért fontos a szabványosított eszközprotokoll a bővíthető ágensekhez |
