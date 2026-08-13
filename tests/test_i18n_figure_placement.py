from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]

CHAPTER_1_LOCALE_ANCHORS = {
    "es": {
        2: ("Posentrenamiento", "externalizado"),
        3: ("Prompt del sistema", "Sin historial"),
    },
    "ja": {
        2: ("ポストトレーニング", "外部化学習"),
        3: ("システム", "操作の繰り返し"),
    },
    "tr": {
        2: ("Eğitim sonrası", "Dışsallaştırılmış öğrenme"),
        3: ("Sistem istemi", "Tekrarlanan işlemler"),
    },
}

CHAPTER_3_LOCALE_ANCHORS = {
    "ar": {
        10: ("ملخص عالمي", "الوثيقة الأصلية"),
        12: ("غير وكيل RAG", "الجيل المباشر"),
    },
    "es": {
        10: ("Resumen general", "Documento original"),
        12: ("RAG No Agéntico", "Paso único"),
    },
    "hu": {
        10: ("globális összegzés", "Eredeti dokumentum"),
        12: ("Non-Agentic RAG", "Hiányos kontextus"),
    },
    "id": {
        10: ("Ringkasan global", "Dokumen asli"),
        12: ("RAG Non-Agentic", "Retrieval tunggal"),
    },
    "ja": {
        10: ("全体要約", "元の文書"),
        12: ("非エージェント型 RAG", "単一パス"),
    },
    "ru": {
        10: ("Глобальное резюме", "Исходный документ"),
        12: ("Неагентный RAG", "Единичный поиск"),
    },
    "ta": {
        10: ("Global summary", "Original document"),
        12: ("Non-Agentic RAG", "Single retrieval"),
    },
    "tr": {
        10: ("Genel özet", "Orijinal belge"),
        12: ("Ajan Olmayan RAG", "Tek erişim"),
    },
}


def svg_text(locale: str, chapter: int, figure: int) -> str:
    path = ROOT / f"book-{locale}" / "images" / f"fig{chapter}-{figure}.svg"
    root = ElementTree.parse(path).getroot()
    return "\n".join(text.strip() for text in root.itertext() if text.strip())


def assert_anchors(locale: str, chapter: int, figure: int, anchors: tuple[str, ...]) -> None:
    text = " ".join(svg_text(locale, chapter, figure).split()).casefold()
    for anchor in anchors:
        assert (
            anchor.casefold() in text
        ), f"{locale} Figure {chapter}-{figure} is missing {anchor!r}"


def test_chapter_1_localized_figures_match_their_captions():
    for locale, localized_anchors in CHAPTER_1_LOCALE_ANCHORS.items():
        for figure, anchors in localized_anchors.items():
            assert_anchors(locale, 1, figure, anchors)
        assert_anchors(locale, 1, 4, ("convert_currency", "assistant.reasoning"))
        assert_anchors(locale, 1, 5, ("$web_search", "code_interpreter"))

    assert_anchors("es", 1, 6, ("while not done:", "SWE-bench"))


def test_chapter_3_localized_figures_match_their_captions():
    common_anchors = {
        5: ("BM25", "④"),
        6: ("Word2Vec", "2013"),
        7: ("O(",),
        9: ("0.87", "8.4"),
        13: ("knowledge_base_search", "code_interpreter"),
        14: ("ACME", "Anthropic"),
    }

    for locale, localized_anchors in CHAPTER_3_LOCALE_ANCHORS.items():
        for figure, anchors in common_anchors.items():
            assert_anchors(locale, 3, figure, anchors)
        for figure, anchors in localized_anchors.items():
            assert_anchors(locale, 3, figure, anchors)

    for locale in ("ar", "es", "id", "ja", "ru", "ta", "tr"):
        assert_anchors(locale, 3, 11, ("SSE", "AVX"))

    assert_anchors("es", 3, 8, ("Score(Q,D)", "IDF"))


def test_chapter_4_localized_figures_match_their_captions():
    expected_anchors = {
        2: ("on_email_reply", "user.interrupt"),
        3: ("t₁", "user.interrupt"),
        4: ("on_github_pr_update", "on_resource_alert"),
        5: ("get_weather", "tool_result"),
        6: ("B≈", "C≈"),
        7: ("discover_tools", "list_contributors"),
        8: ("get_stock_quote", "KV Cache"),
    }

    for locale in ("es", "tr"):
        for figure, anchors in expected_anchors.items():
            assert_anchors(locale, 4, figure, anchors)
