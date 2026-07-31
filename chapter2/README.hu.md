# 2. fejezet · Kontextustervezés

> A kontextus határozza meg az ágens képességeinek felső korlátját: API-struktúra, KV Cache-barát tervezés, prompttervezés, Agent Skills, állapotsáv és kontextustömörítés.

← [Vissza a magyar főoldalhoz](../docs/hu/README.md) · 📖 [A fejezet olvasása](../book-hu/chapter2.md)

## Kapcsolódó projektek

| Kísérlet | Projekt | Típus | Leírás |
| :--: | --- | :--: | --- |
| 2-1 | [local_llm_serving](local_llm_serving/) | ✅ | Platformfüggetlen helyi LLM-telepítést biztosít vLLM vagy Ollama háttérrendszerrel. |
| 2-2, 2-7 | [attention_visualization](attention_visualization/) | ✅ | Megjeleníti a bemeneti és kimeneti tokeneket, valamint a modell figyelmi súlyainak eloszlását. |
| 2-3 | [kv-cache](kv-cache/) | ✅ | Összehasonlítja a kontextuskezelési mintákat és azok KV Cache-hatékonyságra gyakorolt hatását. |
| 2-4 | [prompt-engineering](prompt-engineering/) | ✅ | Szisztematikus ablációs kísérletekkel méri a prompt különböző elemeinek hatását. |
| 2-5 | [prompt-injection](prompt-injection/) | ✅ | Három támadási forgatókönyvet vet össze négy rétegzett védelmi konfigurációval. |
| 2-6 | [agent-skills-ppt](agent-skills-ppt/) | ✅ | Az Agent Skills fokozatos feltárását alkalmazza valódi PPTX-prezentáció létrehozására. |
| 2-8 | [system-hint](system-hint/) | ✅ | A System Hints ágensviselkedésre és teljesítményre gyakorolt hatását vizsgálja. |
| 2-9 | [context-compression](context-compression/) | ✅ | Több tömörítési stratégiát hasonlít össze a tokenhasználat csökkentésére az alapvető képességek megőrzése mellett. |

## Projekttípusok

| Ikon | Típus | Jelentés |
| :--: | --- | --- |
| ✅ | **Önálló** | A teljes kód a repository-ban található, és az API-kulcsok beállítása után futtatható. |
| 📖 | **Reprodukciós útmutató** | Külső repository szükséges, amelyet külön kell `git clone` paranccsal letölteni. |
| 🚧 | **Folyamatban** | Az implementáció vagy az elfogadási bizonyíték még nem teljes. |
