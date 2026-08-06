# 3. fejezet · Felhasználói memória és tudásbázis

> Lehetővé teszi, hogy az ágens munkameneteken át emlékezzen a felhasználóra, és memórián, RAG-on, strukturált indexeken és tudásgráfokon keresztül külső tudáshoz férjen hozzá.

← [Vissza a magyar főoldalhoz](../docs/hu/README.md) · 📖 [A fejezet olvasása](../book-hu/chapter3.md)

## Kapcsolódó projektek

| Kísérlet | Projekt | Típus | Leírás |
| :--: | --- | :--: | --- |
| 3-1, 3-2 | [user-memory](user-memory/) | ✅ | Hosszú távú felhasználói memóriát épít a preferenciákhoz és az interakciós előzményekhez. |
| 3-1 | [user-memory-evaluation](user-memory-evaluation/) | ✅ | A felhasználói memóriarendszerek pontosságát, relevanciáját és hatékonyságát értékeli. |
| 3-2 | [mem0](mem0/) · [memobase](memobase/) | ✅ | A Mem0 és Memobase keretrendszerekkel készült memóriaimplementációkat hasonlítja össze. |
| 3-3 | [log-sanitization](log-sanitization/) | ✅ | Helyi modellel észleli és maszkolja a naplókban lévő titkokat és személyes adatokat. |
| 3-4 | [dense-embedding](dense-embedding/) | ✅ | Az ANNOY és HNSW közelítő legközelebbi szomszéd indexeket hasonlítja össze. |
| 3-5 | [sparse-embedding](sparse-embedding/) | ✅ | Ritka vektoros, BM25-alapú keresőmotort valósít meg az alapoktól. |
| 3-6 | [retrieval-pipeline](retrieval-pipeline/) | ✅ | A sűrű és ritka visszakeresést neurális újrarangsorolással egyesíti. |
| 3-7 | [structured-index](structured-index/) | ✅ | A RAPTOR és GraphRAG strukturált indexelési megközelítéseit veti össze. |
| 3-8 | [agentic-rag](agentic-rag/) | ✅ | A hagyományos RAG-ot hasonlítja össze az iteratív visszakeresést végző Agentic RAG-gal. |
| 3-9 | [agentic-rag-for-user-memory](agentic-rag-for-user-memory/) | ✅ | Agentic RAG-ot alkalmaz munkameneteken átívelő beszélgetési előzmények visszakeresésére. |
| 3-10 | [contextual-retrieval](contextual-retrieval/) | ✅ | Kontextuselőtagot ad a szövegrészletekhez a visszakeresési hibák csökkentésére. |
| 3-11 | [contextual-retrieval-for-user-memory](contextual-retrieval-for-user-memory/) | ✅ | Az Advanced JSON Cards és Contextual RAG megoldásokat kétrétegű memóriává egyesíti. |
| 3-12 | [structured-knowledge-extraction](structured-knowledge-extraction/) | ✅ | Döntési tényezőket és esetprototípusokat nyer ki bírósági határozatok adathalmazából. |

## Projekttípusok

| Ikon | Típus | Jelentés |
| :--: | --- | --- |
| ✅ | **Önálló** | A teljes kód a repository-ban található, és az API-kulcsok beállítása után futtatható. |
| 📖 | **Reprodukciós útmutató** | Külső repository szükséges, amelyet külön kell `git clone` paranccsal letölteni. |
| 🚧 | **Folyamatban** | Az implementáció vagy az elfogadási bizonyíték még nem teljes. |
