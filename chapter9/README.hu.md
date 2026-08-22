# 9. fejezet · Az ágensek folyamatos evolúciója

> Tapasztalatból fejleszti az ágenst: nyomvonalakat ellenőriz, tudást desztillál, promptokat javít, munkafolyamatokat készít, és ellenőrzött módon módosítja önmagát.

← [Vissza a magyar főoldalhoz](../docs/hu/README.md) · 📖 [A fejezet olvasása](../book-hu/chapter9.md)

## Hogyan olvassuk a kísérleteket?

A törzsszöveg rövid mechanizmus-skeletonokkal magyarázza a vezérlési folyamatot; a kísérleti könyvtárakban találhatók a teljes SDK-adapterek, naplók, tesztek és átvételi bizonyítékok. Nem kell minden fájlt sorról sorra elolvasni.

- **Starter:** Kezdje a céllal, a minimális paranccsal és az átvételi feltételekkel; induljon innen: [trajectory-verifier](trajectory-verifier/);
- **Builder:** Kövesse a belépési pontot, a fő ciklust, az állapot-/üzenetsémát, az eszközöket és az ellenőrzőt.
- **Maintainer:** Végül olvassa el a teszteket, a bizonyíték-manifeszteket, a hibakezelést, a visszaállítási útvonalakat és a provider-adaptereket.

Első olvasáskor átugorható a hitelesítő adatok betöltése, a megjelenítési réteg és a provider-kompatibilitás; a számok reprodukálásakor térjen vissza.

## Kapcsolódó projektek

| Kísérlet | Projekt | Típus | Leírás |
| :--: | --- | :--: | --- |
| 9-1 | [trajectory-verifier](trajectory-verifier/) | ✅ | A környezeti eredményeket, folyamatszabályokat és rubrikákat bizonyítékalapú diagnózissá egyesíti. |
| 9-2 | [gaia-experience](gaia-experience/) | ✅ | Sikeres, részben sikeres és sikertelen nyomvonalakból tapasztalati dokumentumot készít. |
| 9-3 | [prompt-auto-optimization](prompt-auto-optimization/) | ✅ | Minimális promptjavítást készít, és határ- valamint megtartási készlettel vezérli a kiadást. |
| 9-4 | Törzsszövegbeli kísérlet | 🚧 | 9-4. kísérlet: felhasználói visszajelzésekből fejleszt ki egy „követelménytisztázás + Spec-megerősítés” Skillt; a szöveg háromkarú A/B tervet, metrikákat és kiadási kapukat ad meg, a hozzá tartozó implementáció még hiányzik |
| 9-5 | [browser-use-rpa](browser-use-rpa/) | ✅ | Böngészőnyomvonalakat fordít reset és visszajátszás segítségével ellenőrzött munkafolyamattá. |
| 9-6 | [self-modifying-agent](self-modifying-agent/) | ✅ | Ismételt hibák után kódjavítást indít, majd regressziót, canary kiadást és visszaállítást végez. |
| 9-7 | [harness-safety-gate](harness-safety-gate/) | ✅ | Magas kockázatú műveletek megerősítési kapuja |
| 9-8 | [hermes-self-evolution](hermes-self-evolution/) | 📖 | Hermes megkapja a teljes könyvet és saját forrását, választ egy javítást, módosítja önmagát, és minden Reviewer-elutasításból új tanulási kört indít az elfogadásig. |
| 9-9 | [self-evolution-eval](self-evolution-eval/) | ✅ | A 9-9. kísérlet hosszú távon értékeli a tanulást, átvitelt, szabályváltozást és megtartást. |

Minden kísérlet kínál offline belépési pontot és API-kulcs nélküli egységtesztet; a valódi modellt vagy böngészőt igénylő útvonalakat az egyes projektek README-je ismerteti.

## Kiegészítő esetek

| Kísérlet | Projekt | Kapcsolat |
| :--: | --- | --- |
| 8-8 | [prompt-distillation](../chapter8/prompt-distillation/) | Prompt-desztilláció és parametrizált tanulás fejezeteken átívelő projektje; a tanítási módszer a 8. fejezethez tartozik |
| — | [self-evolving-tools](self-evolving-tools/) | Alita-stílusú eszközfelfedezés, -becsomagolás és -újrafelhasználás — kiegészítő eset a „tapasztalat programba írására” |
| — | [ai-style-skill](ai-style-skill/) | Az írási visszajelzést ellenőrizhető Skill-lé alakítja; a fejezet a görbe idézőjeles Skillt auditált szintetikus adattal és utóhangolással kapcsolja össze, a pontos másolás tokenizer/Harness hibáit pedig külön kezeli |

## Projekttípusok

| Ikon | Típus | Jelentés |
| :--: | --- | --- |
| ✅ | **Önálló** | A teljes kód a repository-ban található, és az API-kulcsok beállítása után futtatható. |
| 📖 | **Reprodukciós útmutató** | Külső repository szükséges, amelyet külön kell `git clone` paranccsal letölteni. |
| 🚧 | **Folyamatban** | Az implementáció vagy az elfogadási bizonyíték még nem teljes. |
