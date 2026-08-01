# 9. fejezet · Multimodalitás és valós idejű interakció

> A szövegtől a beszéd, a grafikus felületek és a fizikai világ felé bővíti az érzékelést és a cselekvést: streamelt beszéd, Computer Use és robotika.

← [Vissza a magyar főoldalhoz](../docs/hu/README.md) · 📖 [A fejezet olvasása](../book-hu/chapter9.md)

## Kapcsolódó projektek

| Kísérlet | Projekt | Típus | Leírás |
| :--: | --- | :--: | --- |
| 9-1 | [live-audio](live-audio/) | ✅ | Valós idejű hangbeszélgetési demó, amely STT-t, AI-párbeszédet és TTS-t kapcsol össze. |
| 9-2 | [phone-agent](phone-agent/) | 🚧 | A Pine Voice útvonalai elkészültek, de engedélyezett PSTN-hívás még nem futott. |
| 9-3 | [streaming-speech](streaming-speech/) | ✅ | Bemutatja a streamelt beszédfelismerés késleltetési és pontossági kompromisszumát. |
| 9-4 | [end-to-end-speech](end-to-end-speech/) | ✅ | A rögzített revisionű MiniCPM-o 4.5 helyben futott egy RTX PRO 6000 GPU-n; az end-to-end és self-cascade egyaránt 3/4 lett, egymást kiegészítő szemantikai/paralingvisztikai hibákkal és valódi 24kHz-es hangbizonyítékkal. |
| 9-5 | [controllable-tts](controllable-tts/) | 🚧 | Fish Audio referencia-könyvtárat és média-összehasonlítást készít; a hallgatási értékelés még hiányos. |
| 9-6 | `claude-quickstarts/computer-use-demo/` | 📖 | Az Anthropic hivatalos Computer Use demója konténerizált Ubuntu asztalon. |
| 9-7 | `browser-use/` | 📖 | Vizuális böngésző-automatizálás művelet- és képernyőkép-nyomvonalakkal. |
| 9-8 | [xlerobot-teleoperation](xlerobot-teleoperation/) | 📖 | XLeRobot távvezérlési útvonal; az elfogadás engedélyezett fizikai hardvert igényel. |
| 9-9 | [gemini-xlerobot-navigation](gemini-xlerobot-navigation/) | 📖 | XLeRobot-navigáció Gemini Robotics-ER és RoboCrew használatával. |
| 9-10 | [rgb-sim2real-grasping](rgb-sim2real-grasping/) | 📖 | RGB → PPO → SO-100 folyamat zero-shot Sim2Real tárgymegfogáshoz. |

## Projekttípusok

| Ikon | Típus | Jelentés |
| :--: | --- | --- |
| ✅ | **Önálló** | A teljes kód a repository-ban található, és az API-kulcsok beállítása után futtatható. |
| 📖 | **Reprodukciós útmutató** | Külső repository vagy meghatározott hardver szükséges. |
| 🚧 | **Folyamatban** | Az implementáció vagy az élő elfogadási bizonyíték még nem teljes. |
