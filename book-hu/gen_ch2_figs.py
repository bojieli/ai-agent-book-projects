#!/usr/bin/env python3
"""Generate Hungarian Chapter 2 SVGs from the Chinese golden layouts.

The Chinese edition owns the diagram geometry and figure numbering.  Hungarian
prose is explicit here instead of being assembled by the generic word-level
figure localizer.  Figure 2-7 is redrawn as vector artwork because the Chinese
golden asset is a raster attention heatmap.

Run from anywhere in the repository:

    python3 book-hu/gen_ch2_figs.py
"""

from __future__ import annotations

import html
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "book" / "images"
OUTPUT_DIR = ROOT / "book-hu" / "images"
FIT_SCRIPT = ROOT / "book-en" / "fit_svg_text.py"

TEXT_RE = re.compile(r"(<text\b[^>]*>)(.*?)(</text>)", re.DOTALL)


FIGURE_TEXT = {
    1: [
        "Rendszerprompt",
        '"Segítőkész asszisztens vagy. Tömören KELL válaszolnod."',
        '"Használj eszközöket, ha a felhasználó valós idejű információt kér."',
        "Eszközdefiníciók",
        '{"name": "web_search", "description": "Keresés a weben",',
        ' "parameters": {"query": {"type": "string"}}}',
        "Beszélgetési előzmények",
        'user: "Milyen ma az időjárás Pekingben?"',
        'assistant: [tool_call] → get_weather("Beijing")',
        'tool: {"temp": "23°C", "conditions": "clear"}',
        "Érvelési nyomvonal",
        "<think>A felhasználó az időjárásról kérdez. Az eszközeredmény már rendelkezésre áll,",
        "ezért közvetlenül összefoglalhatom és válaszolhatok az eszköz újbóli meghívása nélkül.</think>",
        "Aktuális generálási pozíció →",
        'assistant: "Pekingben ma derült az ég, a hőmérséklet 23 °C…"  ← az LLM generál',
        "Kontextus",
        "Ablak",
        "Ablakméret: Qwen3 = 32K token | Claude = 200K | Gemini = 2M",
        "Minden tartalom tokenfolyammá szerializálva → a Transformer figyelmi mechanizmusa dolgozza fel",
    ],
    2: [
        "Kérés (az ágenskeretrendszer állítja össze)",
        "system",
        "A fejlesztő által megadott szabályok",
        "user",
        '"Szia, ki vagy?"',
        "Hívás",
        "Válasz (az API küldi vissza)",
        "assistant",
        "A modell által generált válasz",
        '"Szia! Programozási asszisztens vagyok…"',
        "Minden hívás állapotmentes — a modell számára szükséges összes információt teljes egészében meg kell adni a kérés messages listájában",
    ],
    3: [
        "Első hívás",
        "messages: system + user",
        "tools: get_current_time,",
        "get_weather",
        "API",
        "assistant: tool_calls",
        "get_current_time()  +",
        "get_weather()  (párhuzamosan)",
        "Az ágenskeretrendszer párhuzamosan futtatja a két eszközt",
        "Második hívás",
        "messages: + eszközeredmények",
        "Vancouveri idő és időjárás",
        "Hozzáfűzés az üzenetelőzményekhez",
        "API",
        "assistant: végső válasz",
        "Nincs eszközhívás → a ciklus vége",
        '"Most … van, az időjárás pedig …"',
        "Állapotmentes API esetén minden körben újra el kell küldeni a modellnek a teljes üzenetelőzményt",
    ],
    4: [
        "Statikus előtag (a körök során változatlan)",
        "Rendszerprompt",
        "Eszközdefiníciók",
        "Beszélgetési előzmények / trajektória (az interakciókkal növekszik →)",
        "user",
        "assistant",
        "tool result",
        "user",
        "…",
        "„Statikus előtag + trajektória”: az előtag maradjon változatlan a KV-gyorsítótárhoz; a trajektória tömöríthető",
    ],
    5: [
        "Felhasználói kérés",
        '"Hívd fel az Xfinityt jobb árért"',
        "Helyi LLM-szolgáltatás",
        "vLLM/Ollama (OpenAI-kompatibilis)",
        "Modellkövetkeztetés",
        "Döntés és a tool_call előállítása",
        "Helyi eszközvégrehajtás",
        "Függvény / külső API meghívása",
        "Az eszközeredmények visszaadása a modellnek, majd a végső válasz generálása",
    ],
    6: [
        "① A „怎么样” figyelmi súlyai az előző szavakhoz",
        "北京 (Peking)",
        "Kulcs · súly 0,35",
        "的",
        "Kulcs · súly 0,05",
        "天气 (időjárás)",
        "Kulcs · súly 0,55",
        "怎么样 (milyen?)",
        "Lekérdezés (aktuális)",
        "Lekérdezés–kulcs pontszámok → normalizálás → az értékek súlyozott összege (főként „天气”)",
        "② Figyelmi hőtérkép: minden szó csak önmagára és az előző szavakra figyelhet (kauzális háromszög)",
        "Kulcs →",
        "北京",
        "的",
        "天气",
        "怎么样",
        "Lekérdezés ↓",
        "北京",
        "1,00",
        "的",
        "0,30",
        "0,70",
        "天气",
        "0,20",
        "0,10",
        "0,70",
        "怎么样",
        "0,35",
        "0,05",
        "0,55",
        "0,05",
        "Sötétebb cella = nagyobb figyelem; üres felső háromszög = a még nem generált szavak nem láthatók",
    ],
    8: [
        "Strukturált API-üzenetek",
        "system",
        '"Segítőkész asszisztens vagy."',
        "user",
        '"Mi az időjárás ma Pekingben?"',
        "assistant",
        "(generálandó)",
        "Chat Template",
        "A modell által ténylegesen feldolgozott lineáris tokenfolyam",
        "<|im_start|>system",
        "Segítőkész asszisztens vagy.<|im_end|>",
        "<|im_start|>user",
        "Mi az időjárás ma Pekingben?<|im_end|>",
        "<|im_start|>assistant",
        "Speciális tokenek jelölik a szerepeket és az üzenethatárokat, egyetlen folytonos sorozatot alkotva",
    ],
    9: [
        "API-szint (amit a fejlesztő lát)",
        "{ ",
        '"role"',
        ": ",
        '"system"',
        ",",
        '"content"',
        ": ",
        '"Asszisztens vagy"',
        " }",
        "{ ",
        '"role"',
        ": ",
        '"user"',
        ",",
        '"content"',
        ": ",
        '"Szia"',
        " }",
        "Modellszint (a Chat Template átalakítása után)",
        "<|im_start|>",
        "system",
        "Asszisztens vagy",
        "<|im_end|>",
        "<|im_start|>",
        "user",
        "Szia",
        "<|im_end|>",
        "<|im_start|>",
        "assistant",
        "(a modell itt kezdi a generálást)",
    ],
    10: [
        "1. kérés",
        "Rendszerprompt + eszközök (1200 token)",
        'user: "Milyen az időjárás?"',
        "→ Válasz generálása",
        "2. kérés",
        "Rendszerprompt + eszközök (gyorsítótár-találat ✓)",
        'user: "Mennyi az idő?"',
        "→ Válasz generálása",
        "KV újrafelhasználás",
        "3. kérés",
        "(a rendszerprompt megváltozott)",
        'Rendszer + eszközök + "Idő: 10:30:45"',
        'user: "Milyen az időjárás?"',
        "→ Teljes újraszámítás ✗",
        "Teljesítmény-összehasonlítás (3000 tokenes teljes kontextus)",
        "Gyorsítótár-találat",
        "Gyorsítótár-hiány",
        "TTFT",
        "~0,5 másodperc",
        "3–5 másodperc",
        "Költség",
        "Csak az új tokenek",
        "Minden token újra számlázva",
    ],
    11: [
        "1. réteg: metaadatok (indításkor betöltve, ~300 token)",
        'skills: [{name: "PPTX", desc: "Create PowerPoint presentations from content"}',
        '{name: "PDF",  desc: "Extract and analyze PDF documents"}, ...]',
        'Feladatindító: „PPT készítése tanulmányból”',
        "2. réteg: a SKILL.md alapfolyamata (igény szerint betöltve, ~2K token)",
        "A PPTX-készség alapfolyamata:",
        "1. szövegkinyerés a markitdownnal → 2. a PPTX kicsomagolása az XML eléréséhez",
        "3. a slide{N}.xml tartalmának módosítása → 4. visszacsomagolás .pptx fájlba",
        "Hivatkozások: → html2pptx.md | → reference.md | → scripts/",
        'Részletes módszer szükséges: „PPT készítése HTML-sablonnal”',
        "3. réteg: aldokumentumok (célzott részletek, igény szerint betöltve)",
        "html2pptx.md",
        "Teljes munkafolyamat:",
        "HTML-sablon → PPT",
        "reference.md",
        "XML-formátum specifikációja",
        "és műszaki részletek",
        "scripts/*.py",
        "Futtatható eszközök:",
        "thumbnail.py stb.",
        "Rögzített metaadatok → KV-gyorsítótár-barát | Dinamikus tartalom hozzáfűzve → a gyorsítótár érvényben marad",
    ],
    12: [
        "messages: [",
        '{ role: "system", content: "Claude Code-asszisztens vagy..." }',
        "tools: [Skill, Read, Bash, Edit, Write, ...]",
        "rögzített",
        "(KV-gyorsítótár)",
        '{ role: "user", content: "Segíts PPT-t készíteni ebből a PDF-ből" }',
        '{ role: "user", isMeta: true,',
        '  content: "<system-reminder>',
        '     Elérhető készségek: pdf, pptx, ...</system-reminder>" }',
        "ⓐ Készséglista",
        "A futtatókör egyszer bocsátja ki",
        "~300 token",
        '{ role: "assistant", tool_calls: [Skill(skill: "pptx")] }',
        '{ role: "tool", content: "PPTX-készség indítása" }   ← helyőrző',
        '{ role: "user", isMeta: true,',
        '  content: "Alapkönyvtár: ...\\n# PPTX-készség',
        '  ## Munkafolyamat: 1. A markitdown használata..." }',
        "ⓑ Készségtartalom",
        "A Skill eszköz egyszer bocsátja ki",
        "~2K token",
        '{ role: "assistant", tool_calls: [Read(file: "input.pdf")] }',
        '{ role: "tool", content: "...a PDF szöveges tartalma..." }',
        '{ role: "assistant", tool_calls: [Write(file: "slides.html")] }',
        '{ role: "tool", content: "12345 bájt kiírva" }',
        "Későbbi tool_use /",
        "a tool_result folytatódik",
        "hozzáfűzés a végéhez",
        "... későbbi körök ...",
        "]",
        "ⓐ és ⓑ egyszer kerül kibocsátásra: a cache_creation egyszeri költsége után tartósan a gyorsítótár-előtagban maradnak, és a későbbi tool_use műveletekkel sem mozdulnak el",
    ],
    13: [
        "1. kör kész",
        "2. kör kész",
        "3. kör kész",
        "(a PPTX-készség első betöltése)",
        "(PDF-fájl olvasása)",
        "(HTML írása)",
        "system", "ÚJ", "tools", "ÚJ", "user_q1", "ÚJ", "★ skill_listing", "ÚJ",
        "asst: Skill(pptx)", "ÚJ", "tool_result", "ÚJ", "★ skill_content", "ÚJ",
        "cache_creation ebben a körben", "≈ 2,5K token",
        "system", "HIT", "tools", "HIT", "user_q1", "HIT", "★ skill_listing", "HIT",
        "asst: Skill(pptx)", "HIT", "tool_result", "HIT", "★ skill_content", "HIT",
        "asst: Read(pdf)", "ÚJ", "tool_result", "ÚJ",
        "cache_creation ebben a körben", "≈ 0,5K token",
        "system", "HIT", "tools", "HIT", "user_q1", "HIT", "★ skill_listing", "HIT",
        "asst: Skill(pptx)", "HIT", "tool_result", "HIT", "★ skill_content", "HIT",
        "asst: Read(pdf)", "HIT", "tool_result", "HIT", "asst: Write(html)", "ÚJ",
        "tool_result", "ÚJ", "cache_creation ebben a körben", "≈ 0,4K token",
        "ÚJ = új token; a cache_creation egyszer fizetendő",
        "HIT = már a gyorsítótárban van; ebben a körben ingyenes",
        "— = ebben a körben még nem generált tartalom",
        "★ Az egyszer kibocsátott mellékletek jelölése: cache_creation csak az 1. körben fizetendő,",
        "utána minden további körben tartós HIT, nulla határköltséggel.",
        "Megjegyzés: a beillesztett üzenetek indexpozíciója nem változik; az új tartalom csak a tömb végéhez fűződik.",
    ],
    14: [
        "Állapotsáv nélkül",
        "Állapotsávval",
        "system:",
        "Rendszerprompt + eszközök",
        "user:",
        '"Hívd fel az Xfinityt jobb árért"',
        "assistant:",
        "phone_call(Xfinity) → 1. kísérlet",
        "tool:",
        "Eredmény: 45 perc várakozás után sem kapcsolták",
        "assistant:",
        'web_search("Xfinity deals")',
        "tool:",
        "Eredmény: [nagy mennyiségű keresési tartalom…]",
        "assistant:",
        "phone_call(Xfinity) → 2. kísérlet",
        "tool:",
        "Eredmény: kapcsolva, ajánlat: 65 USD/hó",
        "assistant:",
        "phone_call(Xfinity) → 3. kísérlet",
        "tool:",
        "Eredmény: megerősített árcsökkentés: 59 USD/hó",
        "user:",
        '"Fel tudod hívni újra, hogy utánajárj?"',
        "→ A modellnek át kell néznie a teljes kontextust, hogy „megszámolja”,",
        "hány hívás történt; könnyen elszámolhatja",
        "system:",
        "Rendszerprompt + eszközök",
        "user:",
        '"Hívd fel az Xfinityt jobb árért"',
        "...:",
        "[ Ugyanaz a trajektóriatartalom ]",
        "user:",
        '"Fel tudod hívni újra, hogy utánajárj?"',
        "<agent_status>",
        "phone_call 3-szor meghívva (Xfinity: 3)",
        "Korlátellenőrzés: elérte a korlátot (3/3) ✗",
        "TEENDŐ: [✓] Xfinity felhívása [✓] Árcsökkentés",
        "Aktuális idő: 2025-09-14 10:30",
        "Állapot: válaszra vár",
        "</agent_status>",
        "→ A modell közvetlenül olvassa a finomított állapotot",
        "Pontosan betartja a korlátot, nincs több hívás",
        "VS",
    ],
    15: [
        "messages: [",
        '{ role: "system", content: "Telekommunikációs ügyfélszolgálati ágens vagy..." }',
        "tools: [cancel_plan, query_records, ...]",
        "rögzített",
        "(KV-gyorsítótár)",
        '{ role: "user", content: "Segíts lemondani az előfizetésemet" }',
        '{ role: "assistant", tool_calls: [cancel_plan(...)] }',
        '{ role: "tool", content: "Ennek a csomagnak hűségideje van..." }',
        '{ role: "assistant", content: "A csomagod még hűségidőn belül van..." }',
        "... további beszélgetési körök ...",
        '{ role: "user", content: "Akkor segíts ellenőrizni a híváslistámat" }',
        "felhasználói utánkövetés",
        '{ role: "user", content: "<agent_status>',
        '  3/3 alkalommal meghívva · TEENDŐ: Előfizetés lemondása (folyamatban)</agent_status>" }',
        "Az ágenskeretrendszer beillesztése",
        "Ágens állapotsávja",
        "]",
        "A modell innen kezdi a generálást",
        "← Közvetlenül a generálás kezdete mellett áll, ezért a legnagyobb figyelmi súlyt kapja",
    ],
    16: [
        "Stratégia", "Tokenek", "Arány", "Iter.", "Eredmény", "Tokenhasználat",
        "Nincs tömörítés", "166 043", "102,1%", "5", "✗ Sikertelen",
        "Egyedi összegzés", "276 608", "10,9%", "12", "✓ Sikeres",
        "Összevont összegzés", "93 449", "4,3%", "10", "✓ Sikeres",
        "Kontextustudatos", "40 157", "3,0%", "7", "✓ Sikeres",
        "Tudatos + hivatkozás", "222 992", "4,1%", "10", "✓ Sikeres",
        "Adaptív ablakozás", "174 601", "102,4%", "7", "✓ Sikeres",
        "Kontextustudatos tömörítés: 76%-kal kevesebb token, mint tömörítés nélkül; holtversenyben a legkevesebb iteráció",
        "Lényeg: a lekérdezési szándék és a meglévő információk bevonása a tömörítési döntésekbe",
    ],
    17: [
        "Minden keresés átlagosan ~52K karaktert ad vissza → a stratégiák eltérően kezelik",
        "① Nincs tömörítés", "Közvetlen megőrzés", "A teljes eredeti szöveg bekerül a kontextusba",
        "166K tok · 102,1% · sikertelen",
        "② Egyedi összegzés", "Független összegzés", "Minden eredményből külön 2–3 bekezdéses összegzés",
        "277K tok · 10,9% · 12 kör",
        "③ Összevont összegzés", "Egyesített összegzés", "Az összes eredmény összefűzése, majd egyetlen összegzés",
        "93K tok · 4,3% · 10 kör",
        "④ Kontextustudatos", "Intelligens tömörítés", "Lekérdezés + kontextus → célzott tömörítés",
        "40K tok · 3,0% · 7 kör",
        "⑤ Tudatos + hivatkozás", "Intelligens + követhető",
        "Tömörített tartalom + URL-hivatkozásjelölők megőrzése", "223K tok · 4,1% · 10 kör",
        "⑥ Adaptív ablakozás", "Késleltetett tömörítés",
        "< 80%-os ablaknál eredeti szöveg; túllépéskor kötegelt tömörítés",
        "175K tok · 102,4% · 7 kör",
    ],
}


def replace_text_nodes(svg: str, values: list[str], figure: int) -> str:
    matches = list(TEXT_RE.finditer(svg))
    if len(matches) != len(values):
        raise ValueError(
            f"Figure 2-{figure}: expected {len(values)} text nodes, found {len(matches)}"
        )
    replacements = iter(values)

    def replace(match: re.Match[str]) -> str:
        value = html.escape(next(replacements), quote=False)
        return match.group(1) + value + match.group(3)

    return TEXT_RE.sub(replace, svg)


def set_language(svg: str) -> str:
    if "xml:lang=" in svg[:300]:
        return re.sub(r'xml:lang="[^"]+"', 'xml:lang="hu"', svg, count=1)
    return svg.replace("<svg ", '<svg xml:lang="hu" ', 1)


def apply_geometry_corrections(svg: str, figure: int) -> str:
    if figure == 6:
        svg = svg.replace('viewBox="0 40 760 520"', 'viewBox="0 40 760 570"')
        svg = svg.replace('width="760" height="520"', 'width="760" height="570"', 1)
    if figure == 16:
        widths = {
            "90": "166.043",
            "152": "276.608",
            "214": "93.449",
            "276": "40.157",
            "338": "222.992",
            "400": "174.601",
        }
        for y, width in widths.items():
            pattern = rf'(<rect x="505" y="{y}" width=")[^"]+'
            svg, count = re.subn(pattern, rf'\g<1>{width}', svg, count=1)
            if count != 1:
                raise ValueError(f"Figure 2-16: missing token bar at y={y}")
    return svg


def apply_text_layout_corrections(svg: str, figure: int) -> str:
    """Apply small locale-specific anchor changes after text replacement."""
    updates = {(10, 20): {"x": "105"}}
    current = -1

    def replace(match: re.Match[str]) -> str:
        nonlocal current
        current += 1
        attrs = updates.get((figure, current))
        if not attrs:
            return match.group(0)
        opening = match.group(1)
        for attribute, value in attrs.items():
            opening, count = re.subn(
                rf'{re.escape(attribute)}="[^"]*"',
                f'{attribute}="{value}"',
                opening,
                count=1,
            )
            if count != 1:
                raise ValueError(
                    f"Figure 2-{figure}: text node {current} has no {attribute} attribute"
                )
        return opening + match.group(2) + match.group(3)

    return TEXT_RE.sub(replace, svg)


def figure_2_7_svg() -> str:
    """Return a compact vector redraw of the Chinese attention heatmap."""
    return """<svg xml:lang="hu" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 250" width="900" height="250" style="background:#ffffff">
<defs>
  <clipPath id="causal"><polygon points="20,20 710,20 880,190 20,190"/></clipPath>
  <linearGradient id="heat" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#fde725"/>
    <stop offset="0.012" stop-color="#6a2c91"/>
    <stop offset="0.35" stop-color="#482475"/>
    <stop offset="0.70" stop-color="#3f1f70"/>
    <stop offset="0.96" stop-color="#365c8d"/>
    <stop offset="1" stop-color="#35b779"/>
  </linearGradient>
  <linearGradient id="legend" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#440154"/>
    <stop offset="0.25" stop-color="#3b528b"/>
    <stop offset="0.5" stop-color="#21918c"/>
    <stop offset="0.75" stop-color="#5ec962"/>
    <stop offset="1" stop-color="#fde725"/>
  </linearGradient>
  <pattern id="minorGrid" width="4" height="4" patternUnits="userSpaceOnUse">
    <path d="M4 0H0V4" fill="none" stroke="#ffffff" stroke-opacity="0.22" stroke-width="0.45"/>
  </pattern>
  <pattern id="bands" width="52" height="34" patternUnits="userSpaceOnUse">
    <rect width="18" height="34" fill="#6c2f91" fill-opacity="0.16"/>
    <rect x="34" width="8" height="34" fill="#2a788e" fill-opacity="0.10"/>
    <rect y="24" width="52" height="4" fill="#8e3a91" fill-opacity="0.12"/>
  </pattern>
</defs>
<g clip-path="url(#causal)">
  <rect x="20" y="20" width="860" height="170" fill="url(#heat)"/>
  <rect x="20" y="20" width="860" height="170" fill="url(#bands)"/>
  <rect x="20" y="20" width="860" height="170" fill="url(#minorGrid)"/>
  <path d="M710 20L880 190" fill="none" stroke="#35b779" stroke-width="3" stroke-opacity="0.9"/>
  <path d="M20 20V190" fill="none" stroke="#fde725" stroke-width="3"/>
</g>
<polygon points="20,20 710,20 880,190 20,190" fill="none" stroke="#d8d8d8" stroke-width="1"/>
<text x="450" y="207" font-family="Arial, 'Helvetica Neue', Helvetica, sans-serif" font-size="12" fill="#333333" text-anchor="middle">Figyelmi súly</text>
<rect x="390" y="214" width="120" height="14" fill="url(#legend)"/>
<text x="390" y="243" font-family="Arial, 'Helvetica Neue', Helvetica, sans-serif" font-size="11" fill="#555555" text-anchor="start">0</text>
<text x="510" y="243" font-family="Arial, 'Helvetica Neue', Helvetica, sans-serif" font-size="11" fill="#555555" text-anchor="end">0,91</text>
</svg>
"""


def generate() -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    for figure in range(1, 18):
        path = OUTPUT_DIR / f"fig2-{figure}.svg"
        if figure == 7:
            svg = figure_2_7_svg()
        else:
            source = (SOURCE_DIR / f"fig2-{figure}.svg").read_text(encoding="utf-8")
            svg = replace_text_nodes(source, FIGURE_TEXT[figure], figure)
            svg = apply_geometry_corrections(svg, figure)
            svg = set_language(svg)
            svg = apply_text_layout_corrections(svg, figure)
        path.write_text(svg.rstrip() + "\n", encoding="utf-8")
        outputs.append(path)

    subprocess.run(
        [sys.executable, str(FIT_SCRIPT), *map(str, outputs)],
        check=True,
    )
    print(f"Generated {len(outputs)} Hungarian Chapter 2 SVGs from Chinese golden layouts.")
    return outputs


if __name__ == "__main__":
    generate()
