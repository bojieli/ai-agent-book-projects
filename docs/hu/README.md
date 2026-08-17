# Az AI-ügynökök mélyreható megértése: tervezési alapelvek és mérnöki gyakorlat

[![PDF](https://img.shields.io/badge/PDF-letöltés-success.svg)](#-e-könyv) [![Online olvasás](https://img.shields.io/badge/🌐_Online_olvasás-bojieli.github.io-success?style=flat-square)](https://bojieli.github.io/ai-agent-book/) [![Stars](https://img.shields.io/github/stars/bojieli/ai-agent-book?style=social)](https://github.com/bojieli/ai-agent-book) [![Licenc](https://img.shields.io/badge/licenc-Apache--2.0-blue.svg)](../../LICENSE) [![Nyelvek](https://img.shields.io/badge/fordítások-13%20nyelv-informational.svg)](#-e-könyv)
[![A nap felkapott GitHub-projektje](https://img.shields.io/badge/GitHub%20Trending-A%20nap%20projektje-orange?logo=github)](https://github.com/trending)

**[中文](../../README.md) · [English](../en/README.md) · [Español](../es/README.md) · [Bahasa Indonesia](../id/README.md) · [العربية](../ar/README.md) · [繁體中文（台灣）](../zh-TW/README.md) · [Русский](../ru/README.md) · [Tiếng Việt](../vi/README.md) · [தமிழ்](../ta/README.md) · [日本語](../ja/README.md) · [Türkçe](../tr/README.md) · [한국어](../ko/README.md) · Magyar ← jelenlegi**

> 📥 **[PDF / EPUB letöltése](#-e-könyv)** (ajánlott) — a PDF- és EPUB-kiadás nyújtja a legjobb olvasási élményt; a könyv [online is olvasható](https://bojieli.github.io/ai-agent-book/), nyelvváltóval, összecsukható fejezetfával és teljes szövegű kereséssel.

**Ágens = NYM + Kontextus + Eszközök** — a könyv erre az alapképletre építve, tíz fejezeten keresztül vezet el az AI-ügynökök alapelveitől a mérnöki gyakorlatig. A teljes szöveg, az ábrák és a **103 kapcsolódó projekt** nyílt forráskódú.

> 🚧 **A 2.0-s verzió átszervezése folyamatban van:** A könyv az 1.4-es verzióról a 2.0-sra váltott, és a tartalom új tanulási útvonalat követ. A 6–9. fejezet most rendre az interakcióról és a megfigyelési/cselekvési tér bővítéséről, az ágensek kiértékeléséről, a modell utóképzéséről és az ágensek folyamatos evolúciójáról szól. A már közzétett PDF-ek átmenetileg még a korábbi szerkezetet használhatják; a fejezetek helyét, számozását és a kísérletek belépési pontjait ez a README és a repozitórium szövege határozza meg.

| 📚 **10 fejezet** az alapoktól az éles rendszerekig | 📂 **103 kapcsolódó projekt**, helyi projektekkel és külső reprodukciós útvonalakkal | 🌐 **13 nyelv**: ZH / EN / ES / ID / AR / zh-TW / RU / TA / VI / JA / TR / KO / HU |
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
| 1 | 🚀 **Ismerkedés az AI-ügynökökkel** | **Ágens = NYM + Kontextus + Eszközök**; a harness-mérnökség teremti meg a valódi versenyelőnyt | [Olvasás](../../book-hu/chapter1.md) | [3](../../chapter1/README.hu.md) |
| 2 | 🎯 **Kontextustervezés** | KV Cache, prompttervezés, Agent Skills és kontextustömörítés | [Olvasás](../../book-hu/chapter2.md) | [10](../../chapter2/README.hu.md) |
| 3 | 📚 **Felhasználói memória és tudásbázis** | Munkameneteken átívelő memória, RAG, strukturált indexek és tudásgráfok | [Olvasás](../../book-hu/chapter3.md) | [12](../../chapter3/README.hu.md) |
| 4 | 🛠️ **Eszközök** | MCP, érzékelési, végrehajtási és együttműködési eszközök, valamint proaktív eszközfelderítés | [Olvasás](../../book-hu/chapter4.md) | [5](../../chapter4/README.hu.md) |
| 5 | 💻 **Kódoló ágens és kódgenerálás** | A kód mint új eszközöket létrehozó eszköz; éles környezetre kész kódoló ágensek | [Olvasás](../../book-hu/chapter5.md) | [13](../../chapter5/README.hu.md) |
| 6 | 🎙️ **Interakció: a megfigyelési és cselekvési tér kiterjesztése** | A modalitás és az időzítés mentén bővíti az ágens megfigyelési és cselekvési terét: aszinkron és eseményvezérelt rendszerek, beszéd, Computer Use és robotika | [Olvasás](../../book-hu/chapter6.md) | [13](../../chapter6/README.hu.md) |
| 7 | 🎯 **Ügynökök kiértékelése** | Értékelési környezetek, mérőszámok, statisztikai szignifikancia és értékelésvezérelt kiválasztás | [Olvasás](../../book-hu/chapter7.md) | [13](../../chapter7/README.hu.md) |
| 8 | 🧠 **Modell-utóképzés** | Előképzés, SFT és RL; eszközhívások internalizálása és mintahatékonyság | [Olvasás](../../book-hu/chapter8.md) | [19](../../chapter8/README.hu.md) |
| 9 | 🔄 **Az ágensek folyamatos evolúciója** | Tanulás a végrehajtási nyomvonalakból; tudás, utasítások, programok és paraméterek frissítése | [Olvasás](../../book-hu/chapter9.md) | [9](../../chapter9/README.hu.md) |
| 10 | 🤝 **Többügynökös együttműködés** | Együttműködési struktúrák, kontextusmegosztás és -elszigetelés, ágenstársadalmak | [Olvasás](../../book-hu/chapter10.md) | [6](../../chapter10/README.hu.md) |
> 💡 Az **Olvasás** hivatkozások megnyitják a fejezet magyar szövegét a GitHubon; a **Kód** oszlop számai a kapcsolódó projektek magyar jegyzékére mutatnak.
>
> 📚 A javasolt tanulási sorrendet és gyakorlati tippeket a **[Tanulási javaslatok](LEARNING.md)** tartalmazza.

## 💻 A kapcsolódó kísérletek futtatása

A közösen támogatott tartomány a **Python 3.11–3.13**. A függőségeket a repository gyökeréből, fejezetenként telepítsd; másik fejezethez a `ch1` helyére `ch2`–`ch10` kerüljön:

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

> 🧪 A kísérletek futtatási állapotát, bizonyítékait és még teljesítendő kapuit külön az [`EXPERIMENT_STATUS.md`](../EXPERIMENT_STATUS.md) tartalmazza; a forráskód klónozása vagy telepítése önmagában nem igazolja a kísérlet befejezését.

## 📦 Függelék · Külső repository-k beszerzése

A 6., 7., 9. és 10. fejezethez tartozó 22 külső repository, valamint egy kiegészítő tanítási cookbook méret- és licencokokból nincs a projektbe csomagolva. Az alábbi parancsok reprodukálható kiindulópontként rögzített commitokat töltenek le.

<details>
<summary><b>🔧 A klónozási parancsok megjelenítése</b> (23 checkout)</summary>

```bash
# 6. fejezet · Értékelési benchmarkok
git clone https://github.com/google-research/android_world.git chapter7/android_world && git -C chapter7/android_world checkout --detach 0e95d641e244504c22087cc29b013f3b2428a261
git clone https://huggingface.co/datasets/gaia-benchmark/GAIA chapter7/GAIA && git -C chapter7/GAIA checkout --detach 682dd723ee1e1697e00360edccf2366dc8418dd9
git clone https://github.com/xlang-ai/OSWorld.git chapter7/OSWorld && git -C chapter7/OSWorld checkout --detach 8365edc975efd0477a0d62444a5beed562ab5a7b
git clone https://github.com/SWE-bench/SWE-bench.git chapter7/SWE-bench && git -C chapter7/SWE-bench checkout --detach 5cd4be9fb23971679cbbafe5a0ecade27cef99be
git clone https://github.com/sierra-research/tau2-bench.git chapter7/tau2-bench && git -C chapter7/tau2-bench checkout --detach 8d005b0e5b9e4af0bc055886fa7f95fc86d1710e
git clone https://github.com/laude-institute/terminal-bench.git chapter7/terminal-bench && git -C chapter7/terminal-bench checkout --detach 8384a179b1b8688f6ea5233a4d9d51218df1ac96

# 8. fejezet · Tanítási keretrendszerek (a bojieli/* ágak a könyvhöz igazított változatok)
git clone https://github.com/bojieli/minimind.git chapter8/MiniMind-pretrain/minimind && git -C chapter8/MiniMind-pretrain/minimind fetch origin 8bdc5d97d5845a8c1ac2ed56a5b8b4c0d0fb0795 && git -C chapter8/MiniMind-pretrain/minimind checkout --detach 8bdc5d97d5845a8c1ac2ed56a5b8b4c0d0fb0795 && test "$(git -C chapter8/MiniMind-pretrain/minimind rev-parse HEAD)" = "8bdc5d97d5845a8c1ac2ed56a5b8b4c0d0fb0795"  # 8-3. kísérlet
git clone https://github.com/bojieli/minimind-v.git chapter8/MiniMind-pretrain/minimind-v && git -C chapter8/MiniMind-pretrain/minimind-v fetch origin ead791c530fa5f9a3549dbfe9e11ec732d18d2e5 && git -C chapter8/MiniMind-pretrain/minimind-v checkout --detach ead791c530fa5f9a3549dbfe9e11ec732d18d2e5 && test "$(git -C chapter8/MiniMind-pretrain/minimind-v rev-parse HEAD)" = "ead791c530fa5f9a3549dbfe9e11ec732d18d2e5"  # 8-4. kísérlet
git clone https://github.com/bojieli/AdaptThink.git chapter8/AdaptThink-original && git -C chapter8/AdaptThink-original checkout --detach 0033ad172dd53ac64004b763477407014f21b838  # 8-10. kísérlet
git clone https://github.com/bojieli/SFTvsRL.git chapter8/SFTvsRL && git -C chapter8/SFTvsRL checkout --detach fef0a4a3367260a0934be1e40b01e4021698e023  # 8-11. és 8-12. kísérlet
git clone https://github.com/bojieli/AWorld.git chapter8/AWorld && git -C chapter8/AWorld checkout --detach a52d61d6d483e66b22ef16970eae5bbf4f4ab2ec  # 8-15. kísérlet
git clone https://github.com/bojieli/verl.git chapter8/verl && git -C chapter8/verl checkout --detach 1593fc3a8cf894debdc3dece2a23ed739c282789  # 8-14. ReTool-recept és 8-15. tanítási háttérrendszer
git clone https://github.com/bojieli/SandboxFusion.git chapter8/SandboxFusion && git -C chapter8/SandboxFusion fetch origin 4a0d573ebd64c98234c190a9d1d49e4276199a0c && git -C chapter8/SandboxFusion checkout --detach 4a0d573ebd64c98234c190a9d1d49e4276199a0c && test "$(git -C chapter8/SandboxFusion rev-parse HEAD)" = "4a0d573ebd64c98234c190a9d1d49e4276199a0c"  # 8-14. kísérlet, kódsandbox
git clone https://github.com/thinking-machines-lab/tinker-cookbook.git chapter8/tinker-cookbook && git -C chapter8/tinker-cookbook checkout --detach fc8449187041cf102905f3f751e6d2eac7f9f754
git clone https://github.com/19PINE-AI/rlvp.git chapter8/RLVP/rlvp && git -C chapter8/RLVP/rlvp fetch origin 1ad30bc7e338911fb733739393d92c420f4d8bee && git -C chapter8/RLVP/rlvp checkout --detach 1ad30bc7e338911fb733739393d92c420f4d8bee && test "$(git -C chapter8/RLVP/rlvp rev-parse HEAD)" = "1ad30bc7e338911fb733739393d92c420f4d8bee"  # 8-16. kísérlet
git clone https://github.com/PRIME-RL/SimpleVLA-RL.git chapter8/SimpleVLA-RL/SimpleVLA-RL && git -C chapter8/SimpleVLA-RL/SimpleVLA-RL checkout --detach 7c51662df27b586f9e8a1ab35fcf849f2b8852f9  # 8-13. kísérlet

# 6. fejezet · GUI és robotikai reprodukciós útvonalak
git clone https://github.com/anthropics/claude-quickstarts.git chapter6/claude-quickstarts && git -C chapter6/claude-quickstarts checkout --detach 9bcc95e316e5ef6542b4c9d0469f4078829eead5  # 6-7. kísérlet, computer-use-demo/
git clone https://github.com/browser-use/browser-use.git chapter6/browser-use && git -C chapter6/browser-use checkout --detach ec9277c5001f2cb78ee419c927775a3cfc227ff8  # 6-8. kísérlet
git clone https://github.com/Vector-Wangel/XLeRobot.git chapter6/XLeRobot && git -C chapter6/XLeRobot fetch origin 3d14695e40c9c68229c0aacffca6053c75cd3eb6 && git -C chapter6/XLeRobot checkout --detach 3d14695e40c9c68229c0aacffca6053c75cd3eb6 && test "$(git -C chapter6/XLeRobot rev-parse HEAD)" = "3d14695e40c9c68229c0aacffca6053c75cd3eb6"  # a 6-9. és 6-11. kísérlet közös függősége
git clone https://github.com/Grigorij-Dudnik/RoboCrew.git chapter6/RoboCrew && git -C chapter6/RoboCrew fetch origin c749148f29bd14e61347f9fc3530c343fff0d994 && git -C chapter6/RoboCrew checkout --detach c749148f29bd14e61347f9fc3530c343fff0d994 && test "$(git -C chapter6/RoboCrew rev-parse HEAD)" = "c749148f29bd14e61347f9fc3530c343fff0d994"  # 6-10/6-11. kísérlet; RoboCrew v0.3.1
git clone https://github.com/StoneT2000/lerobot-sim2real.git chapter6/lerobot-sim2real && git -C chapter6/lerobot-sim2real fetch origin 87d6c1d969f6e0ca4dc5697940804e231118a63a && git -C chapter6/lerobot-sim2real checkout --detach 87d6c1d969f6e0ca4dc5697940804e231118a63a && test "$(git -C chapter6/lerobot-sim2real rev-parse HEAD)" = "87d6c1d969f6e0ca4dc5697940804e231118a63a"  # 6-13. kísérlet

# 10. fejezet · Kettős ágensarchitektúra és Stanford AI Town
git clone https://github.com/19PINE-AI/TalkAct.git chapter10/use-computer-while-calling && git -C chapter10/use-computer-while-calling fetch origin 7d70007f72d45ddfc1a14e8e229b6d444e4919a2 && git -C chapter10/use-computer-while-calling checkout --detach 7d70007f72d45ddfc1a14e8e229b6d444e4919a2 && test "$(git -C chapter10/use-computer-while-calling rev-parse HEAD)" = "7d70007f72d45ddfc1a14e8e229b6d444e4919a2"  # 10-3. kísérlet (historikus 10-4)
git clone https://github.com/joonspk-research/generative_agents.git chapter10/generative_agents && git -C chapter10/generative_agents fetch origin fe05a71d3e4ed7d10bf68aa4eda6dd995ec070f4 && git -C chapter10/generative_agents checkout --detach fe05a71d3e4ed7d10bf68aa4eda6dd995ec070f4 && test "$(git -C chapter10/generative_agents rev-parse HEAD)" = "fe05a71d3e4ed7d10bf68aa4eda6dd995ec070f4"  # 10-5. kísérlet (historikus 10-7)
```

> A rögzített forráskód csak reprodukálható kiindulópont; nem bizonyítja, hogy a tanítási, hardveres, böngészős vagy többágenses kísérlet sikeresen lefutott.

</details>

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
