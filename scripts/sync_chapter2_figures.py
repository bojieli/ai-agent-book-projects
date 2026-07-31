#!/usr/bin/env python3
"""Synchronize localized Chapter 2 SVGs with the Chinese golden layouts.

The Chapter 2 figure sequence changed after several translations had copied an
older set of diagrams.  This script keeps the affected layouts tied to the
Chinese edition while applying an explicit, reviewable localization map.  It
also applies the authoritative context-compression experiment measurements to
Figures 2-16 and 2-17 in every edition.

Usage:
    python scripts/sync_chapter2_figures.py            # all editions
    python scripts/sync_chapter2_figures.py --locale es
"""

from __future__ import annotations

import argparse
import html
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

EDITIONS = {
    "zh": "book",
    "ar": "book-ar",
    "en": "book-en",
    "es": "book-es",
    "id": "book-id",
    "ja": "book-ja",
    "ko": "book-ko",
    "ru": "book-ru",
    "ta": "book-ta",
    "tr": "book-tr",
    "vi": "book-vi",
    "zhtw": "book-zhtw",
}

# These editions inherited six diagrams from an obsolete Chapter 2 sequence.
LAYOUT_SYNC_EDITIONS = {"ar", "en", "es", "id", "ja", "ru", "ta", "tr"}
LAYOUT_SYNC_FIGURES = (2, 3, 4, 5, 8, 9)

# English is the complete fallback.  Locale maps below override every piece of
# prose while deliberately retaining API field names and special tokens.
ENGLISH_TEXT = {
    2: [
        "Request (constructed by the agent framework)",
        "system",
        "Rules written by the developer",
        "user",
        '"Hello, who are you?"',
        "Call",
        "Response (returned by the API)",
        "assistant",
        "Model-generated reply",
        '"Hi! I\'m a coding assistant…"',
        "Each call is stateless — all information needed by the model must be fully provided in the request's messages list",
    ],
    3: [
        "First call",
        "messages: system + user",
        "tools: get_current_time,",
        "get_weather",
        "API",
        "assistant: tool_calls",
        "get_current_time()  +",
        "get_weather()  (parallel)",
        "Agent framework executes two tools in parallel",
        "Second call",
        "messages: + tool results",
        "Vancouver time & weather",
        "Append to message history",
        "API",
        "assistant: final reply",
        "No tool call → end loop",
        '"Now it is…, and the weather is…"',
        "With a stateless API, the complete message history must be resent to the model in every round",
    ],
    4: [
        "Static prefix (unchanged across rounds)",
        "System Prompt",
        "Tool Definitions",
        "Conversation history / trajectory (grows with interaction →)",
        "user",
        "assistant",
        "tool result",
        "user",
        "…",
        '"Static prefix + trajectory": keep the prefix fixed for KV Cache; the trajectory can be compressed',
    ],
    5: [
        "User request",
        '"Help me contact Xfinity to negotiate"',
        "Local LLM service",
        "vLLM/Ollama (OpenAI compatible)",
        "Model inference",
        "Decide and generate tool_call",
        "Local tool execution",
        "Call function / external API",
        "Return tool results to the model, then generate the final response",
    ],
    8: [
        "Structured API messages",
        "system",
        '"You are a helpful assistant."',
        "user",
        '"What is the weather in Beijing today?"',
        "assistant",
        "(to be generated)",
        "Chat Template",
        "Linear token stream actually processed by the model",
        "<|im_start|>system",
        "You are a helpful assistant.<|im_end|>",
        "<|im_start|>user",
        "What is the weather in Beijing today?<|im_end|>",
        "<|im_start|>assistant",
        "Special tokens mark roles and message boundaries, forming one continuous sequence",
    ],
    9: [
        "API level (what developers see)",
        "{ ",
        '"role"',
        ": ",
        '"system"',
        ",",
        '"content"',
        ": ",
        '"You are an assistant"',
        " }",
        "{ ",
        '"role"',
        ": ",
        '"user"',
        ",",
        '"content"',
        ": ",
        '"Hello"',
        " }",
        "Model level (after Chat Template conversion)",
        "<|im_start|>",
        "system",
        "You are an assistant",
        "<|im_end|>",
        "<|im_start|>",
        "user",
        "Hello",
        "<|im_end|>",
        "<|im_start|>",
        "assistant",
        "(the model starts generating here)",
    ],
    10: [
        "Request 1",
        "System Prompt + Tools (1200 tokens)",
        'user: "What is the weather?"',
        "→ Generate response",
        "Request 2",
        "System Prompt + Tools (cache hit ✓)",
        'user: "What time is it?"',
        "→ Generate response",
        "KV reuse",
        "Request 3",
        "(system prompt changed)",
        'System + Tools + "Time: 10:30:45"',
        'user: "What is the weather?"',
        "→ Full recomputation ✗",
        "Performance comparison (3000-token total context)",
        "Cache hit",
        "Cache miss",
        "TTFT",
        "~0.5 seconds",
        "3–5 seconds",
        "Cost",
        "Only new tokens billed",
        "All tokens billed again",
    ],
    11: [
        "Layer 1: Metadata (loaded at startup, ~300 tokens)",
        'skills: [{name: "PPTX", desc: "Create PowerPoint presentations from content"}',
        '        {name: "PDF",  desc: "Extract and analyze PDF documents"}, ...]',
        'Task trigger: "Generate PPT from paper"',
        "Layer 2: SKILL.md core flow (loaded on demand, ~2K tokens)",
        "PPTX Skill core flow:",
        "1. markitdown extracts text → 2. Unzip PPTX to access XML",
        "3. Modify slide{N}.xml content → 4. Repackage as .pptx",
        "References: → html2pptx.md | → reference.md | → scripts/",
        'Need detailed method: "Create PPT with an HTML template"',
        "Layer 3: Subdocuments (selective deep dive, loaded on demand)",
        "html2pptx.md",
        "Complete workflow for",
        "HTML template → PPT",
        "reference.md",
        "XML format specification",
        "and technical details",
        "scripts/*.py",
        "Executable tools:",
        "thumbnail.py, etc.",
        "Fixed metadata → KV Cache friendly | Append dynamic content → keep cache valid",
    ],
}


LOCALIZED_TEXT = {
    "ar": {
        2: [
            "الطلب (ينشئه إطار عمل الوكيل)", "system", "القواعد التي كتبها المطوّر", "user",
            '"مرحبًا، من أنت؟"', "استدعاء", "الاستجابة (تعيدها API)", "assistant",
            "رد أنشأه النموذج", '"مرحبًا! أنا مساعد برمجي…"',
            "كل استدعاء عديم الحالة — يجب توفير كل ما يحتاجه النموذج ضمن قائمة messages في الطلب",
        ],
        3: [
            "الاستدعاء الأول", "messages: system + user", "tools: get_current_time,", "get_weather", "API",
            "assistant: tool_calls", "get_current_time()  +", "get_weather()  (بالتوازي)",
            "ينفّذ إطار عمل الوكيل الأداتين بالتوازي", "الاستدعاء الثاني", "messages: + نتائج الأدوات",
            "وقت فانكوفر والطقس", "إلحاق بسجل الرسائل", "API", "assistant: الرد النهائي",
            "لا استدعاء لأداة — إنهاء الحلقة", '"الوقت الآن…، والطقس…"',
            "مع API عديمة الحالة، يجب إعادة إرسال سجل الرسائل الكامل إلى النموذج في كل جولة",
        ],
        4: [
            "بادئة ثابتة (لا تتغير بين الجولات)", "System Prompt (موجّه النظام)", "Tool Definitions (تعريفات الأدوات)",
            "سجل المحادثة / المسار (ينمو مع التفاعل ←)", "user", "assistant", "نتيجة الأداة", "user", "…",
            'بنية "البادئة الثابتة + المسار": تثبيت البادئة يفيد KV Cache، ويمكن ضغط المسار',
        ],
        5: [
            "طلب المستخدم", '"ساعدني في التفاوض مع Xfinity"', "خدمة LLM محلية",
            "vLLM/Ollama (متوافقة مع OpenAI)", "استدلال النموذج", "تحديد tool_call وإنشاؤه",
            "تنفيذ الأدوات محليًا", "استدعاء دالة / API خارجية", "إعادة نتائج الأدوات إلى النموذج ثم إنشاء الرد النهائي",
        ],
        8: [
            "رسائل API منظّمة", "system", '"أنت مساعد مفيد."', "user", '"كيف هو طقس بكين اليوم؟"',
            "assistant", "(في انتظار الإنشاء)", "Chat Template", "تدفق Token الخطي الذي يعالجه النموذج فعليًا",
            "<|im_start|>system", "أنت مساعد مفيد.<|im_end|>", "<|im_start|>user",
            "كيف هو طقس بكين اليوم؟<|im_end|>", "<|im_start|>assistant",
            "تحدد الرموز الخاصة الأدوار وحدود الرسائل لتكوين تسلسل متصل",
        ],
        9: [
            "مستوى API (ما يراه المطوّر)", "{ ", '"role"', ": ", '"system"', ",", '"content"', ": ",
            '"أنت مساعد"', " }", "{ ", '"role"', ": ", '"user"', ",", '"content"', ": ", '"مرحبًا"', " }",
            "مستوى النموذج (بعد تحويل Chat Template)", "<|im_start|>", "system", "أنت مساعد", "<|im_end|>",
            "<|im_start|>", "user", "مرحبًا", "<|im_end|>", "<|im_start|>", "assistant",
            "(يبدأ النموذج الإنشاء من هنا)",
        ],
    },
    "es": {
        2: [
            "Solicitud (construida por el framework del agente)", "system", "Reglas escritas por el desarrollador", "user",
            '"Hola, ¿quién eres?"', "Llamada", "Respuesta (devuelta por la API)", "assistant",
            "Respuesta generada por el modelo", '"¡Hola! Soy un asistente de programación…"',
            "Cada llamada no tiene estado: toda la información necesaria debe incluirse en la lista messages de la solicitud",
        ],
        3: [
            "Primera llamada", "messages: system + user", "tools: get_current_time,", "get_weather", "API",
            "assistant: tool_calls", "get_current_time()  +", "get_weather()  (en paralelo)",
            "El framework del agente ejecuta dos herramientas en paralelo", "Segunda llamada",
            "messages: + resultados de herramientas", "Hora y tiempo de Vancouver", "Añadir al historial de mensajes",
            "API", "assistant: respuesta final", "Sin llamada a herramienta → fin del bucle",
            '"Ahora son las…, y el tiempo…"',
            "Con una API sin estado, hay que reenviar al modelo todo el historial en cada ronda",
        ],
        4: [
            "Prefijo estático (no cambia entre rondas)", "System Prompt (prompt del sistema)",
            "Tool Definitions (definiciones de herramientas)", "Historial / trayectoria (crece con la interacción →)",
            "user", "assistant", "resultado de herramienta", "user", "…",
            'Estructura "prefijo estático + trayectoria": el prefijo se fija para KV Cache; la trayectoria se puede comprimir',
        ],
        5: [
            "Solicitud del usuario", '"Ayúdame a negociar con Xfinity"', "Servicio LLM local",
            "vLLM/Ollama (compatible con OpenAI)", "Inferencia del modelo", "Decidir y generar tool_call",
            "Ejecución local de herramientas", "Llamar a función / API externa",
            "Devolver resultados al modelo y generar la respuesta final",
        ],
        8: [
            "Mensajes estructurados de la API", "system", '"Eres un asistente útil."', "user",
            '"¿Qué tiempo hace hoy en Pekín?"', "assistant", "(pendiente de generar)", "Chat Template",
            "Flujo lineal de tokens que procesa realmente el modelo", "<|im_start|>system",
            "Eres un asistente útil.<|im_end|>", "<|im_start|>user",
            "¿Qué tiempo hace hoy en Pekín?<|im_end|>", "<|im_start|>assistant",
            "Los tokens especiales delimitan roles y mensajes para formar una secuencia continua",
        ],
        9: [
            "Nivel de API (lo que ve el desarrollador)", "{ ", '"role"', ": ", '"system"', ",", '"content"', ": ",
            '"Eres un asistente"', " }", "{ ", '"role"', ": ", '"user"', ",", '"content"', ": ", '"Hola"', " }",
            "Nivel del modelo (tras convertir con Chat Template)", "<|im_start|>", "system", "Eres un asistente",
            "<|im_end|>", "<|im_start|>", "user", "Hola", "<|im_end|>", "<|im_start|>", "assistant",
            "(el modelo empieza a generar aquí)",
        ],
        10: [
            "Solicitud 1", "System Prompt + Tools (1200 tokens)", 'user: "¿Qué tiempo hace?"', "→ Generar respuesta",
            "Solicitud 2", "System Prompt + Tools (acierto de caché ✓)", 'user: "¿Qué hora es?"', "→ Generar respuesta",
            "Reutilización de KV", "Sol. 3", "(prompt del sistema cambiado)",
            'System + Tools + "Time: 10:30:45"', 'user: "¿Qué tiempo hace?"', "→ Recalcular todo ✗",
            "Comparación de rendimiento (contexto total de 3000 tokens)", "Acierto de caché", "Fallo de caché",
            "TTFT", "~0,5 segundos", "3–5 segundos", "Coste", "Solo tokens nuevos",
            "Todos los tokens de nuevo",
        ],
        11: [
            "Capa 1: Metadatos (cargados al inicio, ~300 tokens)",
            'skills: [{name: "PPTX", desc: "Crear presentaciones PowerPoint desde contenido"}',
            '        {name: "PDF",  desc: "Extraer y analizar documentos PDF"}, ...]',
            'Tarea activadora: "Generar PPT desde un artículo"',
            "Capa 2: Flujo principal de SKILL.md (bajo demanda, ~2K tokens)", "Flujo principal de PPTX Skill:",
            "1. markitdown extrae texto → 2. Descomprimir PPTX para acceder al XML",
            "3. Modificar slide{N}.xml → 4. Volver a empaquetar como .pptx",
            "Referencias: → html2pptx.md | → reference.md | → scripts/",
            'Método detallado: "Crear PPT con una plantilla HTML"',
            "Capa 3: Subdocumentos (consulta selectiva, bajo demanda)", "html2pptx.md", "Flujo completo para",
            "plantilla HTML → PPT", "reference.md", "Especificación del formato XML", "y detalles técnicos",
            "scripts/*.py", "Herramientas ejecutables:", "thumbnail.py, etc.",
            "Metadatos fijos → favorecen KV Cache | Contenido dinámico añadido → no invalida la caché",
        ],
    },
    "id": {
        2: [
            "Request (disusun oleh framework Agent)", "system", "Aturan yang ditulis developer", "user",
            '"Halo, siapa kamu?"', "Panggil", "Response (dikembalikan API)", "assistant",
            "Jawaban yang dihasilkan model", '"Hai! Saya asisten pemrograman…"',
            "Setiap panggilan bersifat stateless — semua informasi harus lengkap dalam daftar messages pada request",
        ],
        3: [
            "Panggilan pertama", "messages: system + user", "tools: get_current_time,", "get_weather", "API",
            "assistant: tool_calls", "get_current_time()  +", "get_weather()  (paralel)",
            "Framework Agent menjalankan dua tool secara paralel", "Panggilan kedua", "messages: + hasil tool",
            "Waktu & cuaca Vancouver", "Tambahkan ke riwayat pesan", "API", "assistant: jawaban akhir",
            "Tanpa panggilan tool → akhiri loop", '"Sekarang pukul…, cuacanya…"',
            "Pada API stateless, seluruh riwayat pesan harus dikirim ulang ke model di setiap putaran",
        ],
        4: [
            "Prefix statis (tetap sama di setiap putaran)", "System Prompt", "Tool Definitions",
            "Riwayat percakapan / trajectory (terus bertambah →)", "user", "assistant", "hasil tool", "user", "…",
            'Struktur "prefix statis + trajectory": prefix dijaga tetap untuk KV Cache; trajectory dapat dikompresi',
        ],
        5: [
            "Request pengguna", '"Bantu saya bernegosiasi dengan Xfinity"', "Layanan LLM lokal",
            "vLLM/Ollama (kompatibel dengan OpenAI)", "Inferensi model", "Tentukan dan hasilkan tool_call",
            "Eksekusi tool lokal", "Panggil fungsi / API eksternal", "Kembalikan hasil tool ke model lalu hasilkan jawaban akhir",
        ],
        8: [
            "Pesan API terstruktur", "system", '"Anda adalah asisten yang membantu."', "user",
            '"Bagaimana cuaca Beijing hari ini?"', "assistant", "(belum dihasilkan)", "Chat Template",
            "Aliran Token linear yang benar-benar diproses model", "<|im_start|>system",
            "Anda adalah asisten yang membantu.<|im_end|>", "<|im_start|>user",
            "Bagaimana cuaca Beijing hari ini?<|im_end|>", "<|im_start|>assistant",
            "Token khusus menandai peran dan batas pesan, membentuk satu urutan kontinu",
        ],
        9: [
            "Level API (yang dilihat developer)", "{ ", '"role"', ": ", '"system"', ",", '"content"', ": ",
            '"Anda adalah asisten"', " }", "{ ", '"role"', ": ", '"user"', ",", '"content"', ": ", '"Halo"', " }",
            "Level model (setelah konversi Chat Template)", "<|im_start|>", "system", "Anda adalah asisten",
            "<|im_end|>", "<|im_start|>", "user", "Halo", "<|im_end|>", "<|im_start|>", "assistant",
            "(model mulai menghasilkan dari sini)",
        ],
    },
    "ja": {
        2: [
            "Request（Agent フレームワークが構築）", "system", "開発者が記述したルール", "user",
            '"こんにちは、あなたは誰ですか？"', "呼び出し", "Response（API が返却）", "assistant",
            "モデルが生成した応答", '"こんにちは！コーディングアシスタントです…"',
            "各呼び出しはステートレス — 必要な情報はすべて request の messages に含める",
        ],
        3: [
            "1 回目の呼び出し", "messages: system + user", "tools: get_current_time,", "get_weather", "API",
            "assistant: tool_calls", "get_current_time()  +", "get_weather()（並列）",
            "Agent フレームワークが 2 つの tool を並列実行", "2 回目の呼び出し", "messages: + tool の結果",
            "バンクーバーの時刻と天気", "メッセージ履歴に追加", "API", "assistant: 最終応答",
            "tool 呼び出しなし → ループ終了", '"現在は…、天気は…"',
            "ステートレス API では、毎回すべてのメッセージ履歴をモデルへ再送する",
        ],
        4: [
            "静的プレフィックス（各ラウンドで不変）", "System Prompt（システムプロンプト）",
            "Tool Definitions（ツール定義）", "会話履歴 / 軌跡（対話とともに増加 →）", "user", "assistant",
            "tool の結果", "user", "…", "「静的プレフィックス + 軌跡」：KV Cache のためプレフィックスを固定し、軌跡は圧縮可能",
        ],
        5: [
            "ユーザーの依頼", '"Xfinity との料金交渉を手伝って"', "ローカル LLM サービス",
            "vLLM/Ollama（OpenAI 互換）", "モデル推論", "tool_call を判断して生成",
            "ローカル tool 実行", "関数 / 外部 API を呼び出す", "tool の結果をモデルへ返し、最終応答を生成",
        ],
        8: [
            "構造化された API メッセージ", "system", '"あなたは役に立つアシスタントです。"', "user",
            '"今日の北京の天気は？"', "assistant", "（生成待ち）", "Chat Template",
            "モデルが実際に処理する線形 Token ストリーム", "<|im_start|>system",
            "あなたは役に立つアシスタントです。<|im_end|>", "<|im_start|>user",
            "今日の北京の天気は？<|im_end|>", "<|im_start|>assistant",
            "特殊 Token が役割とメッセージ境界を示し、連続したシーケンスを形成",
        ],
        9: [
            "API レベル（開発者から見える形式）", "{ ", '"role"', ": ", '"system"', ",", '"content"', ": ",
            '"あなたはアシスタントです"', " }", "{ ", '"role"', ": ", '"user"', ",", '"content"', ": ",
            '"こんにちは"', " }", "モデルレベル（Chat Template 変換後）", "<|im_start|>", "system",
            "あなたはアシスタントです", "<|im_end|>", "<|im_start|>", "user", "こんにちは", "<|im_end|>",
            "<|im_start|>", "assistant", "（モデルはここから生成を開始）",
        ],
    },
    "ru": {
        2: [
            "Запрос (сформирован фреймворком агента)", "system", "Правила, заданные разработчиком", "user",
            '"Привет, кто ты?"', "Вызов", "Ответ (возвращён API)", "assistant", "Ответ, созданный моделью",
            '"Привет! Я ассистент по программированию…"',
            "Каждый вызов не хранит состояния — вся нужная информация должна быть в списке messages запроса",
        ],
        3: [
            "Первый вызов", "messages: system + user", "tools: get_current_time,", "get_weather", "API",
            "assistant: tool_calls", "get_current_time()  +", "get_weather()  (параллельно)",
            "Фреймворк агента параллельно запускает два инструмента", "Второй вызов",
            "messages: + результаты инструментов", "Время и погода в Ванкувере", "Добавить в историю сообщений",
            "API", "assistant: итоговый ответ", "Нет вызова инструмента → завершить цикл",
            '"Сейчас…, погода…"', "При stateless API на каждом раунде модели повторно отправляется вся история сообщений",
        ],
        4: [
            "Статический префикс (не меняется между раундами)", "System Prompt (системный промпт)",
            "Tool Definitions (описания инструментов)", "История диалога / траектория (постоянно растёт →)",
            "user", "assistant", "результат инструмента", "user", "…",
            'Структура «статический префикс + траектория»: префикс фиксирован для KV Cache, траекторию можно сжимать',
        ],
        5: [
            "Запрос пользователя", '"Помоги договориться о скидке с Xfinity"', "Локальный сервис LLM",
            "vLLM/Ollama (совместим с OpenAI)", "Инференс модели", "Выбрать и создать tool_call",
            "Локальное выполнение инструмента", "Вызвать функцию / внешний API",
            "Вернуть результаты модели и сформировать итоговый ответ",
        ],
        8: [
            "Структурированные сообщения API", "system", '"Ты полезный ассистент."', "user",
            '"Какая сегодня погода в Пекине?"', "assistant", "(ожидает генерации)", "Chat Template",
            "Линейный поток токенов, который фактически обрабатывает модель", "<|im_start|>system",
            "Ты полезный ассистент.<|im_end|>", "<|im_start|>user", "Какая сегодня погода в Пекине?<|im_end|>",
            "<|im_start|>assistant", "Специальные токены отмечают роли и границы сообщений, образуя непрерывную последовательность",
        ],
        9: [
            "Уровень API (что видит разработчик)", "{ ", '"role"', ": ", '"system"', ",", '"content"', ": ",
            '"Ты ассистент"', " }", "{ ", '"role"', ": ", '"user"', ",", '"content"', ": ", '"Привет"', " }",
            "Уровень модели (после Chat Template)", "<|im_start|>", "system", "Ты ассистент", "<|im_end|>",
            "<|im_start|>", "user", "Привет", "<|im_end|>", "<|im_start|>", "assistant",
            "(модель начинает генерацию здесь)",
        ],
    },
    "ta": {
        2: [
            "Request (Agent framework உருவாக்கியது)", "system", "Developer எழுதிய விதிகள்", "user",
            '"வணக்கம், நீங்கள் யார்?"', "அழைப்பு", "Response (API வழங்கியது)", "assistant",
            "Model உருவாக்கிய பதில்", '"வணக்கம்! நான் coding assistant…"',
            "ஒவ்வொரு அழைப்பும் stateless — தேவையான அனைத்தும் request-இன் messages பட்டியலில் முழுமையாக இருக்க வேண்டும்",
        ],
        3: [
            "முதல் அழைப்பு", "messages: system + user", "tools: get_current_time,", "get_weather", "API",
            "assistant: tool_calls", "get_current_time()  +", "get_weather()  (இணையாக)",
            "Agent framework இரண்டு tools-ஐ இணையாக இயக்குகிறது", "இரண்டாம் அழைப்பு", "messages: + tool முடிவுகள்",
            "Vancouver நேரம் மற்றும் வானிலை", "Message history-இல் சேர்", "API", "assistant: இறுதிப் பதில்",
            "Tool call இல்லை → loop முடிவு", '"இப்போது…, வானிலை…"',
            "Stateless API-இல் ஒவ்வொரு சுற்றிலும் முழு message history-ஐ model-க்கு மீண்டும் அனுப்ப வேண்டும்",
        ],
        4: [
            "நிலையான prefix (ஒவ்வொரு சுற்றிலும் மாறாது)", "System Prompt", "Tool Definitions",
            "உரையாடல் history / trajectory (தொடர்ந்து வளரும் →)", "user", "assistant", "tool முடிவு", "user", "…",
            '"நிலையான prefix + trajectory": KV Cache-க்காக prefix மாறாது; trajectory-ஐ compress செய்யலாம்',
        ],
        5: [
            "பயனர் கோரிக்கை", '"Xfinity-யுடன் விலை பேச உதவுங்கள்"', "உள்ளூர் LLM சேவை",
            "vLLM/Ollama (OpenAI-compatible)", "Model inference", "tool_call-ஐ தீர்மானித்து உருவாக்கு",
            "உள்ளூர் tool இயக்கம்", "Function / வெளிப்புற API அழைப்பு", "Tool முடிவை model-க்கு அளித்து இறுதிப் பதிலை உருவாக்கு",
        ],
        8: [
            "கட்டமைக்கப்பட்ட API messages", "system", '"நீங்கள் உதவிகரமான assistant."', "user",
            '"இன்று Beijing வானிலை எப்படி?"', "assistant", "(உருவாக்கப்பட வேண்டும்)", "Chat Template",
            "Model உண்மையில் செயலாக்கும் தொடர்ச்சியான Token stream", "<|im_start|>system",
            "நீங்கள் உதவிகரமான assistant.<|im_end|>", "<|im_start|>user",
            "இன்று Beijing வானிலை எப்படி?<|im_end|>", "<|im_start|>assistant",
            "Special tokens role மற்றும் message எல்லைகளைக் குறித்து ஒரே தொடரை உருவாக்குகின்றன",
        ],
        9: [
            "API நிலை (developer காண்பது)", "{ ", '"role"', ": ", '"system"', ",", '"content"', ": ",
            '"நீங்கள் ஒரு assistant"', " }", "{ ", '"role"', ": ", '"user"', ",", '"content"', ": ", '"வணக்கம்"', " }",
            "Model நிலை (Chat Template மாற்றத்திற்குப் பின்)", "<|im_start|>", "system", "நீங்கள் ஒரு assistant",
            "<|im_end|>", "<|im_start|>", "user", "வணக்கம்", "<|im_end|>", "<|im_start|>", "assistant",
            "(model இங்கிருந்து உருவாக்கத் தொடங்குகிறது)",
        ],
    },
    "tr": {
        2: [
            "Request (Agent framework tarafından oluşturulur)", "system", "Geliştiricinin yazdığı kurallar", "user",
            '"Merhaba, sen kimsin?"', "Çağrı", "Response (API tarafından döndürülür)", "assistant",
            "Modelin ürettiği yanıt", '"Merhaba! Ben bir kodlama asistanıyım…"',
            "Her çağrı stateless'tır — gereken tüm bilgiler request içindeki messages listesinde eksiksiz verilmelidir",
        ],
        3: [
            "İlk çağrı", "messages: system + user", "tools: get_current_time,", "get_weather", "API",
            "assistant: tool_calls", "get_current_time()  +", "get_weather()  (paralel)",
            "Agent framework iki aracı paralel çalıştırır", "İkinci çağrı", "messages: + araç sonuçları",
            "Vancouver saati ve hava durumu", "Mesaj geçmişine ekle", "API", "assistant: son yanıt",
            "Araç çağrısı yok → döngüyü bitir", '"Şu an…, hava…"',
            "Stateless API'de tüm mesaj geçmişi her turda modele yeniden gönderilmelidir",
        ],
        4: [
            "Statik önek (turlar boyunca değişmez)", "System Prompt (sistem istemi)",
            "Tool Definitions (araç tanımları)", "Konuşma geçmişi / trajectory (etkileşimle büyür →)",
            "user", "assistant", "araç sonucu", "user", "…",
            '"Statik önek + trajectory": KV Cache için önek sabit kalır; trajectory sıkıştırılabilir',
        ],
        5: [
            "Kullanıcı isteği", '"Xfinity ile pazarlık yapmama yardım et"', "Yerel LLM hizmeti",
            "vLLM/Ollama (OpenAI uyumlu)", "Model çıkarımı", "tool_call seç ve oluştur",
            "Yerel araç yürütme", "Fonksiyon / harici API çağır", "Araç sonuçlarını modele verip son yanıtı oluştur",
        ],
        8: [
            "Yapılandırılmış API mesajları", "system", '"Yardımcı bir asistansın."', "user",
            '"Pekin\'de bugün hava nasıl?"', "assistant", "(üretilecek)", "Chat Template",
            "Modelin gerçekte işlediği doğrusal Token akışı", "<|im_start|>system",
            "Yardımcı bir asistansın.<|im_end|>", "<|im_start|>user", "Pekin'de bugün hava nasıl?<|im_end|>",
            "<|im_start|>assistant", "Özel token'lar rol ve mesaj sınırlarını belirleyip kesintisiz bir dizi oluşturur",
        ],
        9: [
            "API katmanı (geliştiricinin gördüğü)", "{ ", '"role"', ": ", '"system"', ",", '"content"', ": ",
            '"Sen bir asistansın"', " }", "{ ", '"role"', ": ", '"user"', ",", '"content"', ": ", '"Merhaba"', " }",
            "Model katmanı (Chat Template dönüşümünden sonra)", "<|im_start|>", "system", "Sen bir asistansın",
            "<|im_end|>", "<|im_start|>", "user", "Merhaba", "<|im_end|>", "<|im_start|>", "assistant",
            "(model burada üretmeye başlar)",
        ],
    },
}

# Additional layout repairs found during the all-edition visual audit.  These
# maps intentionally use shorter labels where the golden geometry has narrow
# columns; the meaning remains the same as the adjacent translated prose.
LOCALIZED_TEXT.setdefault("ar", {}).update({
    14: [
        "بدون شريط حالة", "مع شريط الحالة", "النظام:", "موجّه النظام + الأدوات", "المستخدم:",
        '"تفاوض مع Xfinity"', "مساعد:", "phone_call(Xfinity) ← المحاولة 1", "الأداة:",
        "النتيجة: انتظار 45 د، لم يتصل", "مساعد:", 'web_search("عروض Xfinity")', "الأداة:",
        "النتيجة: [محتوى بحث كثير…]", "مساعد:", "phone_call(Xfinity) ← المحاولة 2", "الأداة:",
        "النتيجة: اتصال، عرض $65/شهر", "مساعد:", "phone_call(Xfinity) ← المحاولة 3", "الأداة:",
        "النتيجة: تأكيد $59/شهر", "المستخدم:", '"هل تتصل مجددًا؟"',
        "← يمسح النموذج السياق لعد المكالمات", "قد يخطئ في عددها", "النظام:",
        "موجّه النظام + الأدوات", "المستخدم:", '"تفاوض مع Xfinity"', "...:",
        "[محتوى المسار نفسه]", "المستخدم:", '"هل تتصل مجددًا؟"', "<agent_status>",
        "phone_call: 3 مرات (Xfinity: 3)", "حد المكالمات: بلغ (3/3) ✗",
        "TODO: [✓] اتصال [✓] تأكيد السعر", "الوقت: 2025-09-14 10:30",
        "الحالة: انتظار تأكيد المستخدم", "</agent_status>",
        "← يقرأ النموذج الحالة الموجزة مباشرة", "يلتزم بالحد ولا يجري مكالمات أخرى", "VS",
    ],
})

LOCALIZED_TEXT.setdefault("vi", {}).update({
    1: [
        "Từ nhắc hệ thống (System Prompt)",
        '"You are a helpful assistant. You MUST answer concisely."',
        '"Use tools when the user asks for real-time information."',
        "Định nghĩa tool (Tool Definitions)",
        '{"name": "web_search", "description": "Search the web",',
        '"parameters": {"query": {"type": "string"}}}',
        "Lịch sử hội thoại (Conversation History)",
        'user: "Thời tiết ở Bắc Kinh hôm nay thế nào?"',
        'assistant: [tool_call] → get_weather("Bắc Kinh")',
        'tool: {"temp": "23°C", "conditions": "trời quang"}',
        "Suy nghĩ trong lượt này (Reasoning)",
        "<think>Người dùng hỏi về thời tiết và tôi đã có kết quả từ tool,",
        "có thể tóm tắt và trả lời mà không cần gọi lại tool.</think>",
        "Vị trí sinh hiện tại →",
        'assistant: "Bắc Kinh hôm nay trời quang, 23°C…" ← LLM đang sinh',
        "Cửa sổ",
        "ngữ cảnh",
        "Kích thước cửa sổ: Qwen3 = 32K tokens | Claude = 200K | Gemini = 2M",
        "Toàn bộ nội dung được tuần tự thành luồng token → xử lý bởi attention của Transformer",
    ],
    10: [
        "Yêu cầu 1", "System Prompt + Tools (1200 tokens)", 'user: "Thời tiết thế nào?"', "→ Tạo câu trả lời",
        "Yêu cầu 2", "System Prompt + Tools (cache hit ✓)", 'user: "Mấy giờ rồi?"', "→ Tạo câu trả lời",
        "Tái sử dụng KV", "YC 3", "(prompt đổi)", 'System + Tools + "Time: 10:30:45"',
        'user: "Thời tiết thế nào?"', "→ Tính lại toàn bộ ✗",
        "So sánh hiệu năng (tổng ngữ cảnh 3000 token)", "Cache trúng", "Cache trượt", "TTFT",
        "~0,5 giây", "3–5 giây", "Phí", "Chỉ tính token mới", "Tính lại toàn bộ token",
    ],
    14: [
        "Không có thanh trạng thái", "Có thanh trạng thái", "system:", "System Prompt + Tools", "user:",
        '"Thương lượng giá với Xfinity"', "assistant:", "phone_call(Xfinity) → 1", "tool:",
        "KQ: chờ 45 phút, không kết nối", "assistant:", 'web_search("Xfinity deals")', "tool:",
        "KQ: [nhiều nội dung tìm kiếm…]", "assistant:", "phone_call(Xfinity) → 2", "tool:",
        "KQ: kết nối, báo giá $65/tháng", "assistant:", "phone_call(Xfinity) → 3", "tool:",
        "KQ: xác nhận giảm còn $59/tháng", "user:", '"Gọi lại để nhắc họ?"',
        "→ Mô hình quét ngữ cảnh để đếm số cuộc gọi", "Rất dễ đếm sai số cuộc gọi", "system:",
        "System Prompt + Tools", "user:", '"Thương lượng giá với Xfinity"', "...:",
        "[Cùng nội dung trajectory]", "user:", '"Gọi lại để nhắc họ?"', "<agent_status>",
        "phone_call: 3 lần (Xfinity: 3)", "Giới hạn: đã đạt (3/3) ✗",
        "TODO: [✓] Gọi Xfinity [✓] Xác nhận giá", "Thời gian: 2025-09-14 10:30",
        "Trạng thái: chờ người dùng xác nhận", "</agent_status>",
        "→ Mô hình đọc trực tiếp trạng thái cô đọng", "Tuân thủ giới hạn, không gọi thêm", "VS",
    ],
    16: [
        "Chiến lược", "Token", "Tỷ lệ nén", "Số vòng", "Kết quả", "Trực quan (Token)",
        "Không nén", "166,043", "102.1%", "5", "✗ Thất bại",
        "Tóm tắt riêng lẻ", "276,608", "10.9%", "12", "✓ Thành công",
        "Tóm tắt tổng hợp", "93,449", "4.3%", "10", "✓ Thành công",
        "Theo ngữ cảnh", "40,157", "3.0%", "7", "✓ Thành công",
        "Có trích dẫn", "222,992", "4.1%", "10", "✓ Thành công",
        "Cửa sổ thích ứng", "174,601", "102.4%", "7", "✓ Thành công",
        "Nén theo ngữ cảnh: ít hơn 76% token so với không nén, đồng hạng ít vòng lặp nhất",
        "Điểm chính: đưa ý định truy vấn và thông tin hiện có vào quyết định nén",
    ],
})

LOCALIZED_TEXT.setdefault("id", {}).update({
    14: [
        "Tanpa status bar", "Dengan status bar", "system:", "System Prompt + Tools", "user:",
        '"Negosiasikan harga Xfinity"', "assistant:", "phone_call(Xfinity) → ke-1", "tool:",
        "Hasil: tunggu 45 mnt, tak tersambung", "assistant:", 'web_search("Promo Xfinity")', "tool:",
        "Hasil: [banyak hasil pencarian…]", "assistant:", "phone_call(Xfinity) → ke-2", "tool:",
        "Hasil: tersambung, tawaran $65/bln", "assistant:", "phone_call(Xfinity) → ke-3", "tool:",
        "Hasil: harga $59/bln dikonfirmasi", "user:", '"Telepon lagi untuk tindak lanjut?"',
        "→ Model memindai konteks untuk menghitung panggilan", "Rentan salah menghitung jumlah panggilan",
        "system:", "System Prompt + Tools", "user:", '"Negosiasikan harga Xfinity"', "...:",
        "[ Konten lintasan yang sama ]", "user:", '"Telepon lagi untuk tindak lanjut?"', "<agent_status>",
        "phone_call dipanggil 3 kali (Xfinity: 3)", "Cek batas: mencapai batas (3/3) ✗",
        "TODO: [✓]Hubungi [✓]Konfirmasi harga", "Waktu: 2025-09-14 10:30",
        "Status: menunggu konfirmasi pengguna", "</agent_status>",
        "→ Model langsung membaca status ringkas", "Patuh batasan, tidak ada panggilan lagi", "VS",
    ],
})

LOCALIZED_TEXT.setdefault("ta", {}).update({
    16: [
        "உத்தி", "Token", "விகிதம்", "சுற்று", "முடிவு", "காட்சி (Token)",
        "சுருக்கம் இல்லை", "166,043", "102.1%", "5", "✗ தோல்வி",
        "தனிப்பட்ட சுருக்கம்", "276,608", "10.9%", "12", "✓ வெற்றி",
        "ஒருங்கிணைந்த சுருக்கம்", "93,449", "4.3%", "10", "✓ வெற்றி",
        "சூழல்-உணர்வு", "40,157", "3.0%", "7", "✓ வெற்றி",
        "உணர்வு + மேற்கோள்", "222,992", "4.1%", "10", "✓ வெற்றி",
        "தகவமைப்பு சாளரம்", "174,601", "102.4%", "7", "✓ வெற்றி",
        "சூழல்-உணர்வு சுருக்கம்: சுருக்கமின்மையை விட 76% குறைந்த token; குறைந்த சுற்றுகளில் சமநிலை",
        "முக்கியம்: வினவல் நோக்கத்தையும் உள்ள தகவலையும் சுருக்க முடிவில் சேர்க்கவும்",
    ],
    17: [
        "ஒவ்வொரு தேடலும் சராசரியாக ~52K எழுத்துகள் → ஒவ்வொரு உத்தியும் வேறுபடச் செயலாக்கும்",
        "① சுருக்கம் இல்லை", "நேரடியாக வைத்தல்", "முழு அசல் உரையை context-ல் வைத்தல்",
        "166K tok · 102.1% · தோல்வி", "② தனிப்பட்ட சுருக்கம்", "தனிச் சுருக்கம்",
        "ஒவ்வொரு முடிவுக்கும் தனியாக 2–3 பத்தி சுருக்கம்", "277K tok · 10.9% · 12 சுற்று",
        "③ ஒருங்கிணைந்த சுருக்கம்", "ஒன்றிணைந்த சுருக்கம்", "எல்லா முடிவுகளையும் இணைத்து ஒரே சுருக்கம்",
        "93K tok · 4.3% · 10 சுற்று", "④ சூழல்-உணர்வு", "நுண்ணறிவு சுருக்கம்",
        "Query + context → இலக்கு சுருக்கம்", "40K tok · 3.0% · 7 சுற்று",
        "⑤ உணர்வு + மேற்கோள்", "சுருக்கம் + மூலம்", "சுருக்கப்பட்ட உள்ளடக்கம் + URL மேற்கோள்கள்",
        "223K tok · 4.1% · 10 சுற்று", "⑥ தகவமைப்பு சாளரம்", "தாமத சுருக்கம்",
        "< 80% window-ல் அசல் உரை; மீறினால் batch compress", "175K tok · 102.4% · 7 சுற்று",
    ],
})

LOCALIZED_TEXT.setdefault("tr", {}).update({
    16: [
        "Strateji", "Token", "Oran", "Tur", "Sonuç", "Görsel (token kullanımı)",
        "Sıkıştırma yok", "166,043", "102.1%", "5", "✗ Başarısız",
        "Bireysel özet", "276,608", "10.9%", "12", "✓ Başarılı",
        "Birleşik özet", "93,449", "4.3%", "10", "✓ Başarılı",
        "Bağlam duyarlı", "40,157", "3.0%", "7", "✓ Başarılı",
        "Duyarlı + atıf", "222,992", "4.1%", "10", "✓ Başarılı",
        "Uyarlanır pencere", "174,601", "102.4%", "7", "✓ Başarılı",
        "Bağlam duyarlı sıkıştırma: sıkıştırmasız duruma göre %76 az token, en az turda eşit",
        "Anahtar: sorgu amacını ve mevcut bilgiyi sıkıştırma kararına katmak",
    ],
    17: [
        "Her arama ortalama ~52K karakter döndürür → her strateji farklı biçimde işler",
        "① Sıkıştırma yok", "Doğrudan koru", "Özgün metnin tamamını bağlama ekle",
        "166K tok · %102,1 · başarısız", "② Bireysel özet", "Bağımsız özet",
        "Her sonuç için bağımsız 2–3 paragraflık özet", "277K tok · %10,9 · 12 tur",
        "③ Birleşik özet", "Birleşik özet", "Tüm sonuçları birleştirip tek özet oluştur",
        "93K tok · %4,3 · 10 tur", "④ Bağlam duyarlı", "Akıllı sıkıştırma",
        "Sorgu + bağlam → hedefli sıkıştırma", "40K tok · %3,0 · 7 tur",
        "⑤ Duyarlı + atıf", "Akıllı + izlenebilir", "Sıkıştırılmış içerik + URL atıf işaretleri",
        "223K tok · %4,1 · 10 tur", "⑥ Uyarlanır pencere", "Gecikmeli sıkıştırma",
        "< %80 pencerede özgün metin; aşınca toplu sıkıştır", "175K tok · %102,4 · 7 tur",
    ],
})


FIG16_FOOTER = {
    "zh": "上下文感知压缩：相比无压缩节省 76% token，并列最少迭代次数",
    "ar": "الضغط المراعي للسياق: رموز أقل بنسبة 76% من عدم الضغط، وتعادل في أقل عدد من التكرارات",
    "en": "Context-aware compression: 76% fewer tokens than no compression, tied for fewest iterations",
    "es": "Compresión sensible al contexto: 76 % menos tokens que sin compresión y mínimo de iteraciones empatado",
    "id": "Kompresi sadar konteks: token 76% lebih sedikit dari tanpa kompresi, setara untuk iterasi paling sedikit",
    "ja": "コンテキスト対応圧縮：圧縮なしより token を76%削減、反復回数は最少タイ",
    "ko": "컨텍스트 인식 압축: 비압축보다 토큰 76% 절감, 최소 반복 횟수 공동 1위",
    "ru": "Контекстное сжатие: на 76% меньше токенов, чем без сжатия; минимум итераций разделён",
    "ta": "சூழல்-உணர்வு சுருக்கம்: சுருக்கமின்மையை விட 76% குறைந்த token; மிகக் குறைந்த சுற்றுகளில் சமநிலை",
    "tr": "Bağlam duyarlı sıkıştırma: sıkıştırmasız duruma göre %76 az token, en az iterasyonda eşit",
    "vi": "Nén theo ngữ cảnh: ít hơn 76% token so với không nén, đồng hạng ít vòng lặp nhất",
    "zhtw": "上下文感知壓縮：相比無壓縮節省 76% token，並列最少迭代次數",
}

FIG17_TEXT = {
    "zh": [
        "每次搜索平均返回 ~52K 字符 → 各策略以不同方式处理",
        "166K tok · 102.1% · 失败", "277K tok · 10.9% · 12轮", "93K tok · 4.3% · 10轮",
        "40K tok · 3.0% · 7轮", "223K tok · 4.1% · 10轮", "175K tok · 102.4% · 7轮",
    ],
    "ar": [
        "يُرجع كل بحث نحو 52 ألف حرف في المتوسط ← لكل استراتيجية معالجة مختلفة",
        "166K tok · 102.1% · فشل", "277K tok · 10.9% · 12 جولة", "93K tok · 4.3% · 10 جولات",
        "40K tok · 3.0% · 7 جولات", "223K tok · 4.1% · 10 جولات", "175K tok · 102.4% · 7 جولات",
    ],
    "en": [
        "Each search returns ~52K characters on average → each strategy handles them differently",
        "166K tok · 102.1% · failed", "277K tok · 10.9% · 12 rounds", "93K tok · 4.3% · 10 rounds",
        "40K tok · 3.0% · 7 rounds", "223K tok · 4.1% · 10 rounds", "175K tok · 102.4% · 7 rounds",
    ],
    "es": [
        "Cada búsqueda devuelve ~52 K caracteres de media → cada estrategia los procesa de forma distinta",
        "166K tok · 102,1 % · fallo", "277K tok · 10,9 % · 12 rondas", "93K tok · 4,3 % · 10 rondas",
        "40K tok · 3,0 % · 7 rondas", "223K tok · 4,1 % · 10 rondas", "175K tok · 102,4 % · 7 rondas",
    ],
    "id": [
        "Setiap pencarian rata-rata mengembalikan ~52K karakter → tiap strategi menanganinya secara berbeda",
        "166K tok · 102,1% · gagal", "277K tok · 10,9% · 12 putaran", "93K tok · 4,3% · 10 putaran",
        "40K tok · 3,0% · 7 putaran", "223K tok · 4,1% · 10 putaran", "175K tok · 102,4% · 7 putaran",
    ],
    "ja": [
        "各検索は平均約52K文字を返す → 戦略ごとに異なる方法で処理",
        "166K tok · 102.1% · 失敗", "277K tok · 10.9% · 12回", "93K tok · 4.3% · 10回",
        "40K tok · 3.0% · 7回", "223K tok · 4.1% · 10回", "175K tok · 102.4% · 7回",
    ],
    "ko": [
        "검색당 평균 약 52K 문자를 반환 → 전략마다 다른 방식으로 처리",
        "166K tok · 102.1% · 실패", "277K tok · 10.9% · 12회", "93K tok · 4.3% · 10회",
        "40K tok · 3.0% · 7회", "223K tok · 4.1% · 10회", "175K tok · 102.4% · 7회",
    ],
    "ru": [
        "Каждый поиск возвращает в среднем ~52K символов → стратегии обрабатывают их по-разному",
        "166K ток. · 102,1% · сбой", "277K ток. · 10,9% · 12 ит.", "93K ток. · 4,3% · 10 ит.",
        "40K ток. · 3,0% · 7 ит.", "223K ток. · 4,1% · 10 ит.", "175K ток. · 102,4% · 7 ит.",
    ],
    "ta": [
        "ஒவ்வொரு தேடலும் சராசரியாக ~52K எழுத்துகள் → ஒவ்வொரு உத்தியும் வேறுபடச் செயலாக்கும்",
        "166K tok · 102.1% · தோல்வி", "277K tok · 10.9% · 12 சுற்று", "93K tok · 4.3% · 10 சுற்று",
        "40K tok · 3.0% · 7 சுற்று", "223K tok · 4.1% · 10 சுற்று", "175K tok · 102.4% · 7 சுற்று",
    ],
    "tr": [
        "Her arama ortalama ~52K karakter döndürür → her strateji farklı biçimde işler",
        "166K tok · %102,1 · başarısız", "277K tok · %10,9 · 12 tur", "93K tok · %4,3 · 10 tur",
        "40K tok · %3,0 · 7 tur", "223K tok · %4,1 · 10 tur", "175K tok · %102,4 · 7 tur",
    ],
    "vi": [
        "Mỗi lượt tìm kiếm trả về trung bình ~52K ký tự → mỗi chiến lược xử lý khác nhau",
        "166K tok · 102,1% · thất bại", "277K tok · 10,9% · 12 vòng", "93K tok · 4,3% · 10 vòng",
        "40K tok · 3,0% · 7 vòng", "223K tok · 4,1% · 10 vòng", "175K tok · 102,4% · 7 vòng",
    ],
    "zhtw": [
        "每次搜尋平均返回 ~52K 字元 → 各策略以不同方式處理",
        "166K tok · 102.1% · 失敗", "277K tok · 10.9% · 12輪", "93K tok · 4.3% · 10輪",
        "40K tok · 3.0% · 7輪", "223K tok · 4.1% · 10輪", "175K tok · 102.4% · 7輪",
    ],
}


TEXT_RE = re.compile(r"(<text\b[^>]*>)(.*?)(</text>)", re.DOTALL)


def replace_text_nodes(svg: str, values: list[str], *, rtl: bool = False) -> str:
    matches = list(TEXT_RE.finditer(svg))
    if len(matches) != len(values):
        raise ValueError(f"expected {len(values)} text nodes, found {len(matches)}")
    replacements = iter(values)

    def replace(match: re.Match[str]) -> str:
        opening = match.group(1)
        if rtl and "direction=" not in opening:
            opening = opening[:-1] + ' direction="rtl" unicode-bidi="plaintext">'
        return opening + html.escape(next(replacements), quote=False) + match.group(3)

    return TEXT_RE.sub(replace, svg)


def replace_text_indices(svg: str, updates: dict[int, str]) -> str:
    """Replace selected text nodes without reserializing untouched markup."""
    index = -1

    def replace(match: re.Match[str]) -> str:
        nonlocal index
        index += 1
        if index not in updates:
            return match.group(0)
        return match.group(1) + html.escape(updates[index], quote=False) + match.group(3)

    output = TEXT_RE.sub(replace, svg)
    missing = set(updates) - set(range(index + 1))
    if missing:
        raise ValueError(f"missing text-node indices: {sorted(missing)}")
    return output


def set_language(svg: str, locale: str) -> str:
    if "xml:lang=" in svg[:300]:
        return re.sub(r'xml:lang="[^"]+"', f'xml:lang="{locale}"', svg, count=1)
    return svg.replace("<svg ", f'<svg xml:lang="{locale}" ', 1)


def set_text_attribute(locale: str, figure: int, index: int, attribute: str, value: str) -> None:
    """Adjust one text anchor after localizing a golden layout."""
    path = ROOT / EDITIONS[locale] / "images" / f"fig2-{figure}.svg"
    svg = path.read_text(encoding="utf-8")
    current = -1

    def replace(match: re.Match[str]) -> str:
        nonlocal current
        current += 1
        if current != index:
            return match.group(0)
        opening = re.sub(
            rf'{re.escape(attribute)}="[^"]*"',
            f'{attribute}="{value}"',
            match.group(1),
            count=1,
        )
        return opening + match.group(2) + match.group(3)

    output = TEXT_RE.sub(replace, svg)
    if current < index:
        raise ValueError(f"missing text node {index} in {path}")
    path.write_text(output, encoding="utf-8")


def sync_layout(locale: str, figure: int) -> None:
    source = (ROOT / "book" / "images" / f"fig2-{figure}.svg").read_text(encoding="utf-8")
    values = LOCALIZED_TEXT.get(locale, {}).get(figure)
    if values is None:
        values = ENGLISH_TEXT[figure]
    output = replace_text_nodes(source, values, rtl=False)
    output = set_language(output, locale)
    path = ROOT / EDITIONS[locale] / "images" / f"fig2-{figure}.svg"
    path.write_text(output.rstrip() + "\n", encoding="utf-8")


def fix_figure_6(locale: str) -> None:
    path = ROOT / EDITIONS[locale] / "images" / "fig2-6.svg"
    svg = path.read_text(encoding="utf-8")
    svg = svg.replace('viewBox="0 40 760 520"', 'viewBox="0 40 760 570"')
    svg = svg.replace('width="760" height="520"', 'width="760" height="570"', 1)
    path.write_text(svg, encoding="utf-8")


def fix_figure_16(locale: str) -> None:
    path = ROOT / EDITIONS[locale] / "images" / "fig2-16.svg"
    svg = path.read_text(encoding="utf-8")
    updates = {
        7: "166,043", 8: "102.1%", 9: "5",
        12: "276,608", 13: "10.9%", 14: "12",
        17: "93,449", 18: "4.3%", 19: "10",
        22: "40,157", 23: "3.0%", 24: "7",
        27: "222,992", 28: "4.1%", 29: "10",
        32: "174,601", 33: "102.4%", 34: "7",
        36: FIG16_FOOTER[locale],
    }
    if locale == "es":
        updates[3] = "Iter."
    svg = replace_text_indices(svg, updates)

    # The 280 px visualization scale uses 280,000 tokens as its maximum, so
    # each measured 1,000 tokens corresponds to one pixel.
    widths = {
        "90": "166.043", "152": "276.608", "214": "93.449",
        "276": "40.157", "338": "222.992", "400": "174.601",
    }
    for y, width in widths.items():
        pattern = rf'(<rect x="505" y="{y}" width=")[^"]+'
        svg, count = re.subn(pattern, rf'\g<1>{width}', svg, count=1)
        if count != 1:
            raise ValueError(f"could not find Figure 2-16 bar at y={y} in {path}")
    path.write_text(svg, encoding="utf-8")


def fix_figure_17(locale: str) -> None:
    path = ROOT / EDITIONS[locale] / "images" / "fig2-17.svg"
    svg = path.read_text(encoding="utf-8")
    localized = FIG17_TEXT[locale]
    updates = dict(zip((0, 4, 8, 12, 16, 20, 24), localized))
    svg = replace_text_indices(svg, updates)
    path.write_text(svg, encoding="utf-8")


def normalize_arabic_text_direction() -> set[int]:
    """Keep Arabic glyph shaping while preventing start anchors from escaping boxes."""
    changed = set()
    image_dir = ROOT / EDITIONS["ar"] / "images"
    for figure in (2, 3, 4, 5, 8, 9, 14):
        path = image_dir / f"fig2-{figure}.svg"
        svg = path.read_text(encoding="utf-8")
        fixed = svg.replace(' direction="rtl" unicode-bidi="plaintext"', "")
        if fixed != svg:
            path.write_text(fixed, encoding="utf-8")
            match = re.fullmatch(r"fig2-(\d+)\.svg", path.name)
            if match:
                changed.add(int(match.group(1)))
    return changed


def synchronize(locales: list[str]) -> None:
    for locale in locales:
        changed_figures = {6, 16, 17}
        if locale in LAYOUT_SYNC_EDITIONS:
            for figure in LAYOUT_SYNC_FIGURES:
                sync_layout(locale, figure)
                changed_figures.add(figure)
            if locale == "es":
                sync_layout(locale, 10)
                sync_layout(locale, 11)
                set_text_attribute(locale, 10, 20, "x", "100")
                changed_figures.update((10, 11))

        additional_layouts = {
            "ar": (14,),
            "id": (14,),
            "ta": (16, 17),
            "tr": (16, 17),
            "vi": (1, 10, 14, 16),
        }
        for figure in additional_layouts.get(locale, ()):
            sync_layout(locale, figure)
            changed_figures.add(figure)

        fix_figure_6(locale)
        fix_figure_16(locale)
        fix_figure_17(locale)
        if locale == "ar":
            changed_figures.update(normalize_arabic_text_direction())

        # Reuse the repository's idempotent overflow fitter.  The Arabic copy
        # has the same geometry logic plus RTL-aware width handling; the
        # English copy is the neutral fallback for all other scripts.
        fitter_edition = "book-ar" if locale == "ar" else "book-en"
        fitter = ROOT / fitter_edition / "fit_svg_text.py"
        targets = [
            ROOT / EDITIONS[locale] / "images" / f"fig2-{figure}.svg"
            for figure in sorted(changed_figures)
            if figure != 6  # Figure 2-6 changes only its canvas height.
        ]
        subprocess.run(
            [sys.executable, str(fitter), *(str(path) for path in targets)],
            check=True,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--locale", choices=EDITIONS, action="append", help="edition locale to update; repeatable")
    args = parser.parse_args()
    synchronize(args.locale or list(EDITIONS))


if __name__ == "__main__":
    main()
