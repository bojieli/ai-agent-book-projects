# Az AI-ügynökök mélyreható megértése: tervezési alapelvek és mérnöki gyakorlat

[![PDF](https://img.shields.io/badge/PDF-letöltés-success.svg)](#-e-könyv) [![Online olvasás](https://img.shields.io/badge/🌐_Online_olvasás-bojieli.github.io-success?style=flat-square)](https://bojieli.github.io/ai-agent-book/) [![Stars](https://img.shields.io/github/stars/bojieli/ai-agent-book?style=social)](https://github.com/bojieli/ai-agent-book) [![Licenc](https://img.shields.io/badge/licenc-Apache--2.0-blue.svg)](../../LICENSE) [![Nyelvek](https://img.shields.io/badge/fordítások-13%20nyelv-informational.svg)](#-e-könyv)
[![A nap felkapott GitHub-projektje](https://img.shields.io/badge/GitHub%20Trending-A%20nap%20projektje-orange?logo=github)](https://github.com/trending)

**[中文](../../README.md) · [English](../en/README.md) · [Español](../es/README.md) · [Bahasa Indonesia](../id/README.md) · [العربية](../ar/README.md) · [繁體中文（台灣）](../zh-TW/README.md) · [Русский](../ru/README.md) · [Tiếng Việt](../vi/README.md) · [தமிழ்](../ta/README.md) · [日本語](../ja/README.md) · [Türkçe](../tr/README.md) · [한국어](../ko/README.md) · Magyar ← jelenlegi**

> 📥 **[PDF / EPUB letöltése](#-e-könyv)** (ajánlott) — a PDF- és EPUB-kiadás nyújtja a legjobb olvasási élményt; a könyv [online is olvasható](https://bojieli.github.io/ai-agent-book/), nyelvváltóval, összecsukható fejezetfával és teljes szövegű kereséssel.

**Ágens = NYM + Kontextus + Eszközök** — a könyv erre az alapképletre építve, tíz fejezeten keresztül vezet el az AI-ügynökök alapelveitől a mérnöki gyakorlatig. A teljes szöveg, az ábrák és a **94 kapcsolódó kísérlet** nyílt forráskódú.

| 📚 **10 fejezet** az alapoktól az éles rendszerekig | 📂 **94 kapcsolódó kísérlet**, helyi projektekkel és külső reprodukciós útvonalakkal | 🌐 **13 nyelv**: ZH / EN / ES / ID / AR / zh-TW / RU / TA / VI / JA / TR / KO / HU |
| :---: | :---: | :---: |

## 📖 E-könyv

> 📥 **Letöltés offline olvasáshoz** (teljes szöveg, ingyenes és nyílt forráskódú). Az alábbi hivatkozások mindig a `main` ág legfrissebb buildjére mutatnak; a rögzített verziók a [Releases](https://github.com/bojieli/ai-agent-book/releases) oldalon érhetők el:
> - **Magyar** (közösségi fordítás, [@barmivalami0-ux](https://github.com/barmivalami0-ux)): [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-hu.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-hu.epub)
> - **Kínai (eredeti)**: [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-CN.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-CN.epub)
> - **Angol**: [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-en.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-en.epub)
> - **Spanyol**: [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-es.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-es.epub)
> - **Indonéz**: [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-id.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-id.epub)
> - **Arab**: [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ar.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ar.epub)
> - **Hagyományos kínai (Tajvan)**: [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-TW.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-TW.epub)
> - **Orosz**: [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ru.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ru.epub)
> - **Tamil**: [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ta.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ta.epub)
> - **Vietnámi**: [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-vi.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-vi.epub)
> - **Japán**: [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ja.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ja.epub)
> - **Török**: [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-tr.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-tr.epub)
> - **Koreai**: [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ko.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ko.epub)
>
> 🌐 A könyv [online is olvasható](https://bojieli.github.io/ai-agent-book/). A webhely a `main` ág minden frissítése után automatikusan újraépül.

A magyar kézirat forrása a [`book-hu/`](../../book-hu/) könyvtárban található. Ez közösségi fordítás, ezért előfordulhat, hogy lemarad a kínai eredeti mögött.

<details>
<summary><b>🔧 Saját PDF / EPUB build készítése</b> (a PDF-hez pandoc / xelatex / ElegantBook szükséges)</summary>

- **EPUB**: használd a közös buildrendszert; lásd az [EPUB buildelési útmutatót](../../EPUB.md)
- **Szövegforrás**: `book-hu/introduction.md`, `book-hu/chapter1.md`–`book-hu/chapter10.md` és `book-hu/afterword.md`
- **PDF build**: telepítsd a pandoc, xelatex és ElegantBook eszközöket, valamint a szükséges betűkészleteket, majd futtasd:

  ```bash
  cd book-hu && bash build_pdf.sh
  ```

  Az ábrák a `book-hu/images/` könyvtárban találhatók; a tördelési beállításokat a `book-hu/preamble.tex` és a `book-hu/*.lua` fájlok tartalmazzák.

</details>

## 📑 Tartalmi áttekintés (1–10. fejezet)

| Fejezet | Téma | Rövid összefoglaló | Szöveg | Kód |
| :--: | --- | --- | :--: | :--: |
| 1 | 🚀 **Ismerkedés az AI-ügynökökkel** | **Ágens = NYM + Kontextus + Eszközök**; a harness-mérnökség teremti meg a valódi versenyelőnyt | [Olvasás](../../book-hu/chapter1.md) | [4](../../chapter1/README.md) |
| 2 | 🎯 **Kontextustervezés** | KV Cache, prompttervezés, Agent Skills és kontextustömörítés | [Olvasás](../../book-hu/chapter2.md) | [9](../../chapter2/README.md) |
| 3 | 📚 **Felhasználói memória és tudásbázis** | Munkameneteken átívelő memória, RAG, strukturált indexek és tudásgráfok | [Olvasás](../../book-hu/chapter3.md) | [13](../../chapter3/README.md) |
| 4 | 🛠️ **Eszközök** | MCP, érzékelési, végrehajtási és együttműködési eszközök, eseményvezérelt aszinkron ágensek | [Olvasás](../../book-hu/chapter4.md) | [7](../../chapter4/README.md) |
| 5 | 💻 **Kódoló ágens és kódgenerálás** | A kód mint új eszközöket létrehozó eszköz; éles környezetre kész kódoló ágensek | [Olvasás](../../book-hu/chapter5.md) | [12](../../chapter5/README.md) |
| 6 | 🎯 **Ügynökök kiértékelése** | Értékelési környezetek, mérőszámok, statisztikai szignifikancia és értékelésvezérelt kiválasztás | [Olvasás](../../book-hu/chapter6.md) | [11](../../chapter6/README.md) |
| 7 | 🧠 **Modell-utóképzés** | Előképzés, SFT és RL; eszközhívások internalizálása és mintahatékonyság | [Olvasás](../../book-hu/chapter7.md) | [16](../../chapter7/README.md) |
| 8 | 🔄 **Az ágensek folyamatos evolúciója** | Tanulás a végrehajtási nyomvonalakból; tudás, utasítások, programok és paraméterek frissítése | [Olvasás](../../book-hu/chapter8.md) | [8](../../chapter8/README.md) |
| 9 | 🎙️ **Multimodalitás és valós idejű interakció** | Beszéd, grafikus felületek, Computer Use és robotika | [Olvasás](../../book-hu/chapter9.md) | [10](../../chapter9/README.md) |
| 10 | 🤝 **Többügynökös együttműködés** | Együttműködési struktúrák, kontextusmegosztás és -elszigetelés, ágenstársadalmak | [Olvasás](../../book-hu/chapter10.md) | [8](../../chapter10/README.md) |

> 💡 Az **Olvasás** hivatkozások megnyitják a fejezet magyar szövegét a GitHubon; a **Kód** oszlop számai a kapcsolódó projektek jegyzékére mutatnak. A projektjegyzékek jelenleg nem érhetők el magyar fordításban.

## 💻 A kapcsolódó kísérletek futtatása

A közös alapkövetelmény a **Python 3.10+**. A függőségeket a repository gyökeréből, fejezetenként telepítsd; másik fejezethez a `ch1` helyére `ch2`–`ch10` kerüljön:

```bash
# Ajánlott: reprodukálható környezet a repository-ban tárolt uv.lock alapján
uv sync --locked --extra ch1

# uv nélkül: telepítés pip segítségével a pyproject.toml fájlból
python -m pip install -e ".[ch1]"
```

Egy kísérlet futtatása előtt olvasd el az adott projekt README-jét az API-kulcsokról, a rendszerfüggőségekről és az esetleges további Python-verziókövetelményekről. Például:

```bash
uv run python chapter1/context/main.py
```

## 🔑 API-kulcsok

A modellt használó kísérletekhez legalább egy szolgáltatói API-kulcs szükséges. A modellválasztáshoz lásd [ezt az útmutatót](https://01.me/2025/07/llm-api-setup/); az egyes kísérletek pontos beállításait mindig a saját README-jük tartalmazza.

## 📦 Függelék · Külső repository-k beszerzése

A 6., 7., 9. és 10. fejezet több benchmarkot, tanítási keretrendszert és robotikai platformot külső repository-ból használ. Ezek méretük és licencük miatt nincsenek a projektbe csomagolva. A reprodukálható checkout-parancsok az [angol README függelékében](../en/README.md#-appendix--obtaining-external-repositories) találhatók.

## 🤝 Közreműködés

A könyv és a kapcsolódó kód teljes egészében nyílt forráskódú; örömmel fogadjuk a Pull Requesteket.

| Típus | Leírás |
| --- | --- |
| 📝 **Könyvszöveg** | Elírások javítása, kiegészítések, világosabb megfogalmazás és új fejlemények |
| 🐛 **Kódjavítások** | A kapcsolódó projektek robusztusabbá és könnyebben használhatóvá tétele |
| 🧪 **Új gyakorlóprojektek** | Jobb implementációk vagy új példák hozzáadása |
| 🎨 **Ábrák** | A `book-hu/images/` magyar ábráinak javítása |
| 🌐 **Fordítások** | Új nyelvek hozzáadása vagy a meglévő fordítások fejlesztése |

## 📄 Licenc

A projekt az [Apache License 2.0](../../LICENSE) feltételei szerint érhető el. Egyes alprojektek saját licencinformációkat tartalmazhatnak; ezeknél az adott alprojekt feltételei érvényesek.

## ⭐ Star-előzmények

<a href="https://star-history.com/#bojieli/ai-agent-book&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="../../assets/star-history-dark.png" />
    <source media="(prefers-color-scheme: light)" srcset="../../assets/star-history-light.png" />
    <img alt="Star History Chart" src="../../assets/star-history-light.png" width="100%" />
  </picture>
</a>

<sub>A diagramot a [`scripts/gen_star_history.py`](../../scripts/gen_star_history.py) hozza létre, és a [GitHub Actions](../../.github/workflows/star-history.yml) naponta frissíti.</sub>
