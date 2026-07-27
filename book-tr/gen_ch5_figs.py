#!/usr/bin/env python3
"""Generate all SVG illustrations for Chapter 5 (Code Generation).

Figures (11 total):
  fig5-1:  OpenClaw architecture — Coding Agent as core of general Agent
  fig5-2:  Coding Agent multi-phase workflow (concrete file ops & tool calls)
  fig5-3:  Search tool comparison (4 types with real query examples)
  fig5-4:  File editing approach comparison (5 methods with code diffs)
  fig5-5:  PPT generation pipeline (Proposer-Reviewer with Slidev code)
  fig5-6:  Exp 5.6+5.7 — Paper-to-PPT/Video pipeline
  fig5-7:  Exp 5.10 — Production log diagnosis pipeline
  fig5-8:  Dynamic form generation (LLM → HTML form → JSON → continue)
  fig5-9:  SQL query agent (artifact mode, data bypasses LLM)
  fig5-10: Agent bootstrap cycle (self-replication concept)
  fig5-11: Exp 5.14 — Agent that creates agents (meta-agent)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from svg_lib import (
    SVG, COLORS, FONT, MONO, STROKE_W, CORNER_R, _escape,
    FS_TITLE, FS_BODY, FS_SMALL, FS_TINY, FS_LABEL,
)

OUT = os.path.join(os.path.dirname(__file__), 'images')


def _pill(svg, x, y, w, h, label, fill='light', font_size=FS_SMALL, bold=False):
    svg.rect(x, y, w, h, fill=fill, rx=h // 2)
    c = 'white' if fill in ('dark', 'darker') else 'text'
    svg.text(x + w / 2, y + h / 2, label, size=font_size, fill=c, bold=bold)


# ──────────────────────── fig5-1 (NEW: OpenClaw arch) ──────

def fig5_1():
    """OpenClaw architecture: Coding Agent as core of general Agent"""
    w, h = 980, 600
    svg = SVG(w, h)
    svg.text(w / 2, 30, "OpenClaw mimarisi: Genel Ajanın çekirdeği olarak Coding Agent", size=FS_TITLE, bold=True)

    # Top: multi-platform messaging gateway
    gw_y, gw_h = 58, 66
    svg.group_box(60, gw_y, w - 120, gw_h, "Çok platformlu mesaj ağ geçidi (kullanıcı etkileşim katmanı)")
    channels = ["WhatsApp", "Telegram", "iMessage", "Slack", "CLI"]
    pill_w, pill_h = 130, 32
    total_pw = len(channels) * pill_w + (len(channels) - 1) * 18
    px_start = (w - total_pw) / 2
    for i, ch in enumerate(channels):
        px = px_start + i * (pill_w + 18)
        svg.rect(px, gw_y + 26, pill_w, pill_h, fill='medium', rx=pill_h // 2)
        svg.text(px + pill_w / 2, gw_y + 26 + pill_h / 2, ch, size=FS_SMALL)

    svg.arrow(w / 2, gw_y + gw_h + 2, w / 2, 158)
    svg.text(w / 2 + 12, 134, "Doğal dil isteği", size=FS_LABEL, fill='text_light', anchor='start')

    # Center: Coding Agent runtime — widened to fit 4 tools comfortably
    ca_x, ca_y, ca_w, ca_h = 200, 160, 580, 210
    svg.rect(ca_x, ca_y, ca_w, ca_h, fill='light')
    svg.rect(ca_x, ca_y, ca_w, 40, fill='darker', rx=6)
    svg.text(ca_x + ca_w / 2, ca_y + 20,
             "Coding Agent çalışma zamanı (çıkarım + yürütme çekirdeği)", size=FS_BODY, bold=True, fill='white')

    tools = [
        ("Code Interpreter", "Kod yürütme"), ("Bash Shell", "Sistem komutları"),
        ("Read File", "Dosya oku"), ("Write File", "Dosya yaz"),
        ("Edit File", "Dosya düzenle"), ("Glob", "Dosya arama"), ("Grep", "İçerik arama"),
    ]
    tw, th, tgap = 132, 60, 12
    for ri, row in enumerate([tools[:4], tools[4:]]):
        row_total_w = len(row) * tw + (len(row) - 1) * tgap
        rx_start = ca_x + (ca_w - row_total_w) / 2
        ry = ca_y + 56 + ri * (th + tgap)
        for ci, (name, desc) in enumerate(row):
            tx = rx_start + ci * (tw + tgap)
            svg.rect(tx, ry, tw, th, fill='white')
            svg.text(tx + tw / 2, ry + 22, name, size=FS_TINY, bold=True)
            svg.text(tx + tw / 2, ry + 42, desc, size=FS_TINY, fill='text_light')

    # Left: Deep Research
    dr_x, dr_y, dr_w, dr_h = 22, 198, 158, 86
    svg.rect(dr_x, dr_y, dr_w, dr_h, fill='medium')
    svg.text(dr_x + dr_w / 2, dr_y + 22, "Web arama modülü", size=FS_SMALL, bold=True)
    svg.text(dr_x + dr_w / 2, dr_y + 44, "Deep Research", size=FS_TINY, fill='text_light')
    svg.text(dr_x + dr_w / 2, dr_y + 66, "Web isteği · ayrıştırma", size=FS_TINY, fill='text_light')
    svg.arrow(dr_x + dr_w + 2, dr_y + dr_h / 2, ca_x - 2, ca_y + ca_h / 2)

    # Right: Computer Use
    cu_x, cu_y, cu_w, cu_h = 800, 198, 158, 86
    svg.rect(cu_x, cu_y, cu_w, cu_h, fill='medium')
    svg.text(cu_x + cu_w / 2, cu_y + 22, "Tarayıcı otomasyonu", size=FS_SMALL, bold=True)
    svg.text(cu_x + cu_w / 2, cu_y + 44, "Computer Use", size=FS_TINY, fill='text_light')
    svg.text(cu_x + cu_w / 2, cu_y + 66, "Playwright DOM", size=FS_TINY, fill='text_light')
    svg.arrow(ca_x + ca_w + 2, ca_y + ca_h / 2, cu_x - 2, cu_y + cu_h / 2)

    # Bottom: file system layer
    fs_y, fs_h = 410, 140
    svg.arrow(w / 2, ca_y + ca_h + 2, w / 2, fs_y - 2)
    svg.text(w / 2 + 12, 390, "Dosya oku / yaz", size=FS_LABEL, fill='text_light', anchor='start')
    svg.group_box(60, fs_y, w - 120, fs_h, "Dosya sistemi (bellek · bilgi · yetenek merkezi)")

    mem_items = [
        ("MEMORY.md", "Üst düzey gerçekler / kullanıcı tercihleri"),
        ("daily/YYYY-MM-DD.md", "Günlük arşiv / etkileşim kayıtları"),
        ("SOUL.md", "Ajan kimliği ve davranış kuralları"),
        ("Bilgi tabanı dosyaları", "Görev deneyimi / kendi kendine evrim"),
        ("Git sürüm kontrolü", "Bellek geri alma / geçmiş denetimi"),
    ]
    item_w, item_h, item_gap = 162, 76, 16
    total_iw = len(mem_items) * item_w + (len(mem_items) - 1) * item_gap
    ix_start = (w - total_iw) / 2
    for i, (title, desc) in enumerate(mem_items):
        ix = ix_start + i * (item_w + item_gap)
        iy = fs_y + 34
        svg.rect(ix, iy, item_w, item_h, fill='white')
        svg.text(ix + item_w / 2, iy + 26, title, size=FS_TINY, bold=True)
        svg.text(ix + item_w / 2, iy + 52, desc, size=FS_TINY, fill='text_light')

    # Very bottom: LLM as OS
    os_y = fs_y + fs_h + 16
    svg.rect(60, os_y, w - 120, 38, fill='darker', rx=6)
    svg.text(w / 2, os_y + 19,
             "LLM = yeni işletim sistemi: karmaşıklığı gizle, birleşik soyutlama sağla", size=FS_SMALL, bold=True, fill='white')

    svg.save(os.path.join(OUT, 'fig5-1.svg'))


# ──────────────────────── fig5-2 (was fig5-1) ────────────────────────

def fig5_2():
    """Coding Agent multi-phase workflow (concrete tool calls)"""
    w, h = 880, 580
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Coding Agent katmanlı iş akışı", size=FS_TITLE, bold=True)

    phases = [
        ("① Proje dokümantasyonu", 'medium', [
            ("read_file", "README.md, ARCHITECTURE.md"),
            ("glob", "**/*.py, **/*.ts"),
            ("write_file", "→ CLAUDE.md proje rehberi üret"),
        ]),
        ("② Gereksinim anlama", 'light', [
            ("ask_user", "\"Optimizasyon hedefi gecikme mi verim mi?\""),
            ("grep", "\"latency|throughput\" src/"),
            ("read_file", "src/config.py (mevcut parametreler)"),
        ]),
        ("③ Tasarım Belgesi", 'light', [
            ("write_file", "design.md (Şema Karşılaştırması)"),
            ("ask_user", "Tasarımı gönder → Onay bekle"),
            ("—", "İnsan incelemesinden sonra → Devam et"),
        ]),
        ("④ Kodlama ve Test", 'medium', [
            ("edit_file", "old_str→new_str kod değiştir"),
            ("bash", "pytest tests/ -v"),
            ("edit_file", "Başarısız testleri düzelt → Tekrar çalıştır"),
        ]),
        ("⑤ İnceleme ve Teslimat", 'light', [
            ("bash", "ruff check src/ (lint)"),
            ("read_file", "Kendi kendine inceleme: okunabilirlik/güvenlik/performans"),
            ("edit_file", "ARCHITECTURE.md güncelle"),
        ]),
    ]

    phase_w = 155
    phase_gap = 12
    total_w = len(phases) * phase_w + (len(phases) - 1) * phase_gap
    sx = (w - total_w) / 2

    for i, (title, fill, steps) in enumerate(phases):
        x = sx + i * (phase_w + phase_gap)
        ph = 240
        svg.rect(x, 55, phase_w, ph, fill=fill)
        svg.text(x + phase_w / 2, 78, title, size=FS_SMALL, bold=True)
        svg.line(x + 8, 92, x + phase_w - 8, 92, color='dark')

        for j, (tool, desc) in enumerate(steps):
            ty = 110 + j * 70
            _pill(svg, x + 8, ty, phase_w - 16, 22, tool, fill='dark', font_size=11, bold=True)
            svg.text_block(x + 10, ty + 26, phase_w - 20, desc.split('\n'),
                           size=10, min_size=7, anchor='start', mono=True, line_gap=1.45)

        if i < len(phases) - 1:
            ax = x + phase_w + 2
            svg.arrow(ax, 55 + ph / 2, ax + phase_gap - 4, 55 + ph / 2)

    # Bottom: feedback loops
    svg.line(30, 320, w - 30, 320, color='dark', dash=True)
    svg.text(w / 2, 340, "Kapalı döngü geri bildirim mekanizması", size=FS_BODY, bold=True)

    loops = [
        ("Test başarısız → Kodu değiştir → Yeniden test et", "④ İç döngü: ortalama 2-3 turda yakınsar"),
        ("Lint hatası → Hemen düzelt → Yeniden kontrol et", "⑤ İç döngü: düzenleme sonrası otomatik tetiklenir"),
        ("İncelemede sorun bulundu → ④'e geri dön ve düzelt", "⑤→④ geri dönüş: teslimat kalitesini garanti eder"),
    ]
    ly = 365
    for label, note in loops:
        svg.rect(80, ly, 500, 46, fill='light')
        svg.text(330, ly + 15, label, size=FS_SMALL, bold=True)
        svg.text(330, ly + 34, note, size=FS_TINY, fill='text_light')
        ly += 50

    # Annotations on the right
    annots = [
        "Ajan durum çubuğu: cwd, git dalı",
        "Ajan durum çubuğu: hazırlanmamış değişiklikler",
        "Araç çıktısı: head/tail kırpma",
        "Kalıcı terminal oturumu",
    ]
    for i, ann in enumerate(annots):
        svg.rect(610, 365 + i * 50, 250, 38, fill='code_bg', stroke='dark', rx=4)
        svg.text(735, 384 + i * 50, ann, size=FS_TINY, fill='text_light')

    svg.text(w / 2, 565, "Eylemden önce planla · Baştan sona doğrulama · Dokümantasyon ve kod birlikte gelişir", size=FS_BODY, bold=True, fill='darker')

    svg.save(os.path.join(OUT, 'fig5-2.svg'))


# ──────────────────────── fig5-3 ────────────────────────

def fig5_3():
    """Search tool comparison (four tools + actual query examples)"""
    w, h = 880, 560
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Dört arama aracının karşılaştırması", size=FS_TITLE, bold=True)

    tools = [
        ("Düzenli ifade içerik eşleştirme (grep)", 'medium',
         "rg \"def handle_.*\" --type py",
         ["src/api.py:42:  def handle_request(..)",
          "src/api.py:89:  def handle_timeout(..)",
          "src/ws.py:15:   def handle_connect(..)"],
         "Tam metin → tüm geçiş konumları"),
        ("Dosya adı eşleştirme (glob)", 'light',
         "glob: **/test_*.py",
         ["tests/test_api.py",
          "tests/test_auth.py",
          "tests/unit/test_parser.py"],
         "Yol örüntüsü → dosya içeriğini okumaz"),
        ("Anlamsal Kod Arama", 'light',
         "\"Kullanıcı Girdi Doğrulamasını İşle\"",
         ["[0.91] src/validators.py:validate_input()",
          "[0.87] src/forms.py:sanitize_fields()",
          "[0.82] src/api.py:check_params()"],
         "Doğal Dil → Vektör + BM25 Hibrit"),
        ("Sembol Tanımı/Referansı", 'medium',
         "find_references: UserService",
         ["Tanım: src/services/user.py:12",
          "Referans: src/api/routes.py:34 (import)",
          "Referans: src/api/routes.py:56 (çağrı)",
          "Referans: tests/test_user.py:8 (test)"],
         "AST Düzeyi → Aynı İsimleri Ayırt Et"),
    ]

    col_w = (w - 60) // 2
    col_gap = 20

    for i, (title, fill, query, results, note) in enumerate(tools):
        col = i % 2
        row = i // 2
        x = 20 + col * (col_w + col_gap)
        y = 55 + row * 260

        svg.rect(x, y, col_w, 240, fill='white', stroke='border')
        svg.rect(x, y, col_w, 36, fill=fill, rx=CORNER_R)
        tc = 'white' if fill in ('dark', 'darker') else 'text'
        svg.text(x + col_w / 2, y + 18, title, size=FS_SMALL, bold=True, fill=tc)

        svg.text(x + 12, y + 54, "Sorgu:", size=FS_TINY, bold=True, anchor='start', fill='text_light')
        svg.rect(x + 8, y + 64, col_w - 16, 24, fill='code_bg', stroke='dark', rx=3)
        svg.mono(x + 14, y + 76, query, size=11)

        svg.text(x + 12, y + 102, "Sonuç:", size=FS_TINY, bold=True, anchor='start', fill='text_light')
        rh = len(results) * 20 + 12
        svg.rect(x + 8, y + 112, col_w - 16, rh, fill='code_bg', stroke='dark', rx=3)
        for j, r in enumerate(results):
            svg.mono(x + 14, y + 128 + j * 20, r, size=10)

        svg.text(x + col_w / 2, y + 226, note, size=FS_TINY, fill='text_light')

    svg.save(os.path.join(OUT, 'fig5-3.svg'))


# ──────────────────────── fig5-3 ────────────────────────

def fig5_4():
    """File Editing Scheme Comparison (Five Methods + Code Examples)"""
    w, h = 900, 700
    svg = SVG(w, h)
    svg.text(w / 2, 28, "Beş Dosya Düzenleme Şemasının Karşılaştırması", size=FS_TITLE, bold=True)

    approaches = [
        ("Diff + Apply Modeli", "dark",
         ["LLM Diff Açıklaması Üretir:",
          "- def foo(x):",
          "    return x",
          "+ def foo(x, y=0):",
          "+   return x + y",
          "→ Küçük Model Konumlandırır ve Uygular"],
         "Artı: Sorumluluk Ayrımı",
         "Eksi: Küçük Sapma Hizalama Bozar"),
        ("Eski Dize → Yeni Dize", "medium",
         ['old: "def foo(x):\\n',
          '       return x"',
          'new: "def foo(x, y=0):\\n',
          '       return x + y"',
          "→ Tam Dize Eşleşmesiyle Değiştirme"],
         "Artı: Öngörülebilir, Belirsizliksiz",
         "Eksi: Büyük Silmeler Tam Çıktı Gerektirir"),
        ("Satır Numarası Konumlandırma", "light",
         ["42-43. satırları sil, ekle:",
          "  def foo(x, y=0):",
          "    return x + y",
          "",
          "→ Satır Numarası Tam Aralığı Belirtir"],
         "Artı: Büyük İşlemler için Verimli",
         "Eksi: Uzun Dosyalarda Satır No. Hataya Açık"),
        ("Vim Benzeri Komutlar", "light",
         ["42G  (42. satıra git)",
          "cw   (Kelimeyi değiştir)",
          "dd   (Satırı sil)",
          "yy/p (Kopyala/Yapıştır)",
          "→ Zengin düzenleme semantiği"],
         "Artı: Verimli taşıma/yeniden düzenleme",
         "Eksi: Zayıf modeller daha çok hata üretir"),
        ("Baş-son eşleştirme", "medium",
         ['start: "def foo(x):"',
          'end:   "    return x"',
          'new: "def foo(x, y=0):',
          '       return x + y"',
          "→ Konumlandırmak için sadece sınırlar yeterli"],
         "Artı: Tam çıktı olmadan büyük silme",
         "Eksi: Sınır kombinasyonu benzersiz olmalı"),
    ]

    col_w = 168
    col_gap = 10
    total_cw = len(approaches) * col_w + (len(approaches) - 1) * col_gap
    sx = (w - total_cw) / 2

    max_code_h = max(len(a[2]) for a in approaches) * 17 + 14
    py = 101 + max_code_h + 12   # common top for every Adv/Disadv box (keeps them aligned)
    box_h = 80
    for i, (title, fill, code_lines, pro, con) in enumerate(approaches):
        x = sx + i * (col_w + col_gap)

        svg.rect(x, 55, col_w, 38, fill=fill, rx=CORNER_R)
        tc = 'white' if fill in ('dark', 'darker') else 'text'
        svg.text(x + col_w / 2, 74, title, size=FS_TINY, bold=True, fill=tc)

        code_h = len(code_lines) * 17 + 14
        svg.rect(x, 101, col_w, code_h, fill='code_bg', stroke='dark', rx=3)
        for j, line in enumerate(code_lines):
            svg.mono(x + 6, 117 + j * 17, line, size=11)

        svg.rect(x + 4, py, col_w - 8, box_h, fill='white', stroke='dark', rx=3)
        svg.text_block(x + col_w / 2, py + 5, col_w - 18,
                       [(pro, 'text'), (con, 'text_light')], size=FS_TINY - 2,
                       min_size=9, line_gap=1.18)

    # Adoption bar chart at bottom
    chart_y = py + box_h + 22
    svg.line(30, chart_y, w - 30, chart_y, color='dark', dash=True)
    svg.text(w / 2, chart_y + 24, "Gerçek benimseme oranı", size=FS_BODY, bold=True)

    adoptions = [
        ("Eski→Yeni", "Claude Code", 0.85, 'dark'),
        ("Satır Numarası Konumlandırma", "IDE derin entegrasyon senaryoları", 0.50, 'medium'),
        ("Diff + Apply", "Cursor", 0.40, 'light'),
        ("Baş-son eşleştirme", "Bazı özel çözümler", 0.30, 'light'),
        ("Vim komutları", "Deneysel çözümler", 0.15, 'code_bg'),
    ]
    bar_x, bar_w_max = 250, 480
    by = chart_y + 48
    for label, products, ratio, fill in adoptions:
        svg.text(bar_x - 10, by + 14, label, size=FS_TINY, anchor='end', bold=True)
        bw = bar_w_max * ratio
        svg.rect(bar_x, by, bw, 28, fill=fill, rx=3)
        tc = 'white' if fill in ('dark', 'darker') else 'text'
        svg.text(bar_x + bw / 2, by + 14, products, size=FS_TINY, fill=tc)
        by += 38

    svg.save(os.path.join(OUT, 'fig5-4.svg'))


# ──────────────────────── fig5-4 ────────────────────────

def fig5_5():
    """PPT generation pipeline (Proposer-Reviewer collaboration + Slidev code)"""
    w, h = 880, 560
    svg = SVG(w, h)
    svg.text(w / 2, 30, "PPT üretimi: Proposer-Reviewer işbirliği mekanizması", size=FS_TITLE, bold=True)

    # Proposer Agent (left)
    svg.rect(20, 60, 350, 280, fill='white', stroke='border', dash=True)
    svg.text(195, 82, "Proposer Agent", size=FS_BODY, bold=True)

    svg.text(40, 110, "Girdi: Makale/içerik", size=FS_SMALL, anchor='start', bold=True)
    svg.rect(30, 125, 330, 24, fill='code_bg', stroke='dark', rx=3)
    svg.mono(38, 137, "paper.pdf → Bölüm/argüman/görsel çıkar", size=11)

    svg.text(40, 168, "Çıktı: Slidev Markdown", size=FS_SMALL, anchor='start', bold=True)
    code_lines = [
        "---",
        "layout: two-cols",
        "---",
        "# Transformer Mimarisi",
        "::left::",
        "- Self-attention mekanizması",
        "- Çok başlı dikkat",
        "::right::",
        "<img src=\"fig3.png\" />",
    ]
    ch = svg.code_block(30, 182, 330, code_lines, font_size=10, line_h=14)

    # Reviewer Agent (right)
    svg.rect(510, 60, 350, 280, fill='white', stroke='border', dash=True)
    svg.text(685, 82, "Reviewer Agent", size=FS_BODY, bold=True)

    svg.text(520, 110, "Adım 1: Ekran görüntüsü render et", size=FS_SMALL, anchor='start', bold=True)
    svg.rect(520, 125, 330, 50, fill='light')
    svg.text(685, 142, "slidev export --per-slide", size=FS_TINY, fill='text_light')
    svg.text(685, 160, "→ slide-01.png, slide-02.png ...", size=FS_TINY, fill='text_light')

    svg.text(520, 192, "Adım 2: Görsel LLM incelemesi", size=FS_SMALL, anchor='start', bold=True)
    critique_lines = [
        "İnceleme boyutları:",
        "  ✓ Metin taşma sınırı",
        "  ✓ Yerleşim çok sıkışık",
        "  ✓ Görsel boyutu uygun",
        "  ✗ Slayt 3: Metin sağ sütundan taşıyor",
        "  ✗ Slayt 7: İçerik çok yoğun",
    ]
    svg.rect(520, 208, 330, len(critique_lines) * 16 + 12, fill='code_bg', stroke='dark', rx=3)
    for j, line in enumerate(critique_lines):
        svg.mono(528, 222 + j * 16, line, size=10)

    # Arrows: Proposer → Reviewer → Proposer (loop)
    svg.arrow(370, 200, 508, 150, label="Slidev kodu")
    svg.arrow(508, 300, 370, 260, label="Değişiklik önerileri", dash=True)

    # Iteration badge
    _pill(svg, 395, 220, 100, 24, "2-3 tur yinele", fill='dark', font_size=11, bold=True)

    # Bottom: why separate agents
    svg.line(30, 365, w - 30, 365, color='dark', dash=True)
    svg.text(w / 2, 388, "Neden Proposer ve Reviewer ayrı ajanlar?", size=FS_BODY, bold=True)

    reasons = [
        ("Tekli Ajan Sorunu", [
            "Onlarca sayfalık render görüntüsü → bağlam şişmesi",
            "Kod + görüntü karışımı → dikkat dağılması",
        ]),
        ("Ayrımın Avantajları", [
            "Reviewer bağımsız bağlam → yalnızca görüntü + kod",
            "Proposer koda odaklanır → yalnızca değişiklik önerisi alır",
        ]),
        ("Gerçek Etki", [
            "Bağlam kullanımını önemli ölçüde azaltır",
            "Düzeltme doğruluğu belirgin şekilde artar",
        ]),
    ]
    rx = 30
    for title, items in reasons:
        svg.rect(rx, 405, 270, 130, fill='light')
        svg.text(rx + 135, 425, title, size=FS_SMALL, bold=True)
        for j, item in enumerate(items):
            svg.text(rx + 135, 450 + j * 24, item, size=FS_TINY, fill='text_light')
        rx += 290

    svg.save(os.path.join(OUT, 'fig5-5.svg'))


# ──────────────────────── fig5-5 ────────────────────────

def fig5_6():
    """Experiment 5.6+5.7: Paper→PPT→Video end-to-end pipeline"""
    w, h = 880, 560
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Deney 5.6+5.7: Makale → PPT → Ders videosu", size=FS_TITLE, bold=True)

    # Top pipeline: paper → PPT
    stages_top = [
        ("PDF Girdisi", 'medium', [
            "paper.pdf",
            "Belge yapısını ayrıştır",
            "Görsel referanslarını çıkar",
        ]),
        ("İçerik Planlama", 'light', [
            "10-20 sayfa yapısı",
            "Temel argümanları çıkar",
            "Görselleri sayfalara ata",
        ]),
        ("Slidev Üretimi", 'light', [
            "Sayfa sayfa üret",
            "layout: two-cols",
            "Kod + görsel yerleşimi",
        ]),
        ("Render Kontrolü", 'medium', [
            "export --per-slide",
            "Görsel LLM incelemesi",
            "Taşma tespiti",
        ]),
        ("Yinelemeli Düzeltme", 'light', [
            "Reviewer→Proposer",
            "Slidev kodunu değiştir",
            "Yeniden render et ve doğrula",
        ]),
    ]

    sw = 155
    sgap = 10
    total = len(stages_top) * sw + (len(stages_top) - 1) * sgap
    sx = (w - total) / 2

    svg.text(w / 2, 60, "Aşama 1: PPT Üretimi (Proposer-Reviewer)", size=FS_SMALL, bold=True, fill='text_light')
    for i, (title, fill, details) in enumerate(stages_top):
        x = sx + i * (sw + sgap)
        svg.rect(x, 72, sw, 130, fill=fill)
        svg.text(x + sw / 2, 92, title, size=FS_SMALL, bold=True)
        svg.line(x + 8, 104, x + sw - 8, 104, color='dark')
        for j, line in enumerate(details):
            svg.mono(x + 8, 120 + j * 20, line, size=10)
        if i < len(stages_top) - 1:
            svg.arrow(x + sw + 2, 72 + 65, x + sw + sgap - 2, 72 + 65)

    # Arrow down
    svg.arrow(w / 2, 202, w / 2, 240)
    svg.text(w / 2 + 60, 222, "PPT tamamlandı", size=FS_SMALL, fill='text_light')

    # Bottom pipeline: PPT → Video
    svg.text(w / 2, 255, "Aşama 2: Video sentezi", size=FS_SMALL, bold=True, fill='text_light')

    stages_bot = [
        ("Sayfa başına ekran görüntüsü", 'medium', [
            "slide-01.png",
            "slide-02.png",
            "...",
        ]),
        ("Senaryo üretimi", 'light', [
            "LLM günlük dilde senaryo",
            "Sayfa başı anlatım",
            "Yönlendirici anlatı",
        ]),
        ("TTS sentezi", 'light', [
            "Metin → ses",
            "speech-01.mp3",
            "speech-02.mp3",
        ]),
        ("Ses-video senkronu", 'medium', [
            "ffmpeg sentezi",
            "Ses süresini eşleştir",
            "Geçiş efektleri",
        ]),
        ("Nihai video", 'dark', [
            "output.mp4",
            "5-15 dakika",
            "Ses + görsel çıktı",
        ]),
    ]

    for i, (title, fill, details) in enumerate(stages_bot):
        x = sx + i * (sw + sgap)
        svg.rect(x, 268, sw, 130, fill=fill)
        tc = 'white' if fill in ('dark', 'darker') else 'text'
        svg.text(x + sw / 2, 288, title, size=FS_SMALL, bold=True, fill=tc)
        svg.line(x + 8, 300, x + sw - 8, 300, color='dark')
        for j, line in enumerate(details):
            fc = 'white' if fill in ('dark', 'darker') else 'text'
            svg.mono(x + 8, 316 + j * 20, line, size=10, fill=fc)
        if i < len(stages_bot) - 1:
            svg.arrow(x + sw + 2, 268 + 65, x + sw + sgap - 2, 268 + 65)

    # Bottom: key metrics
    svg.line(30, 420, w - 30, 420, color='dark', dash=True)
    svg.text(w / 2, 440, "Kabul kriterleri", size=FS_BODY, bold=True)

    criteria = [
        ("PPT", "10-20 sayfa · Ana katkıları kapsar · ≥3 özgün grafik"),
        ("Render", "Sıfır metin taşması · Makul yerleşim · Metin-görsel uyumu"),
        ("Video", "5-15 dakika · Ses-video senkronu · Tutarlı anlatım"),
    ]
    cy = 462
    for label, desc in criteria:
        _pill(svg, 180, cy, 92, 26, label, fill='dark', font_size=12, bold=True)
        svg.text(285, cy + 13, desc, size=FS_TINY, fill='text_light', anchor='start')
        cy += 30

    svg.save(os.path.join(OUT, 'fig5-6.svg'))


# ──────────────────────── fig5-7 ────────────────────────

def fig5_8():
    """Dynamic form generation flow (LLM→HTML→JSON→Continue)"""
    w, h = 880, 560
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Dinamik form üretimi: Yapılandırılmış niyet netleştirme", size=FS_TITLE, bold=True)

    # Step 1: User input
    svg.rect(20, 60, 200, 60, fill='medium')
    svg.text(120, 82, "Kullanıcı girdisi", size=FS_SMALL, bold=True)
    svg.text(120, 100, "\"Pekin'e uçuş ayırtmak istiyorum\"", size=FS_TINY, fill='text_light')

    svg.arrow(220, 90, 260, 90)

    # Step 2: LLM analyzes and generates form
    svg.rect(260, 55, 260, 140, fill='white', stroke='border', dash=True)
    svg.text(390, 75, "LLM analizi → Form kodu üret", size=FS_SMALL, bold=True)
    form_code = [
        '<form id="clarify">',
        ' <input type="text"',
        '  name="from" label="Kalkış şehri"/>',
        ' <input type="date"',
        '  name="depart" label="Kalkış tarihi"/>',
        ' <select name="type">',
        '  <option>Tek yön</option>',
        '  <option>Gidiş dönüş</option>',
        ' </select>',
        '</form>',
    ]
    svg.rect(270, 90, 240, len(form_code) * 13 + 10, fill='code_bg', stroke='dark', rx=3)
    for j, line in enumerate(form_code):
        svg.mono(276, 103 + j * 13, line, size=9)

    svg.arrow(520, 130, 560, 130)

    # Step 3: Rendered form (visual representation)
    svg.rect(560, 55, 300, 200, fill='white', stroke='border')
    svg.text(710, 75, "Render edilmiş form arayüzü", size=FS_SMALL, bold=True)

    fields = [
        ("Kalkış Şehri", "Şanghay", 95),
        ("Kalkış Tarihi", "2025-08-15", 135),
        ("Yolculuk Tipi", "Gidiş dönüş ▾", 175),
        ("Dönüş Tarihi", "2025-08-22", 215),
    ]
    for label, value, fy in fields:
        svg.text(580, fy, label, size=FS_TINY, anchor='start', bold=True)
        svg.rect(660, fy - 12, 180, 24, fill='code_bg', stroke='dark', rx=3)
        svg.mono(668, fy, value, size=11)

    _pill(svg, 660, 238, 80, 26, "Gönder", fill='dark', font_size=FS_SMALL, bold=True)

    # Step 4: JSON result
    svg.arrow(710, 268, 710, 300)
    svg.rect(560, 300, 300, 110, fill='white', stroke='border', dash=True)
    svg.text(710, 318, "Yapılandırılmış JSON Yanıtı", size=FS_SMALL, bold=True)
    json_lines = [
        '{"from": "Şanghay",',
        ' "depart": "2025-08-15",',
        ' "type": "Gidiş dönüş",',
        ' "return": "2025-08-22"}',
    ]
    svg.rect(570, 330, 280, len(json_lines) * 16 + 10, fill='code_bg', stroke='dark', rx=3)
    for j, line in enumerate(json_lines):
        svg.mono(578, 344 + j * 16, line, size=11)

    # Step 5: Agent continues with structured data
    svg.arrow(560, 390, 400, 440)

    svg.rect(100, 430, 500, 50, fill='medium')
    svg.text(350, 448, "Ajan tam parametrelerle yürütmeye devam eder", size=FS_BODY, bold=True)
    svg.text(350, 468, "search_flights(from='Şanghay', to='Pekin', depart='2025-08-15', ...)", size=FS_TINY, fill='text_light')

    # Comparison: text vs form
    svg.rect(20, 280, 250, 140, fill='light')
    svg.text(145, 300, "Karşılaştırma: Düz Metin vs Form", size=FS_SMALL, bold=True)
    comp = [
        "Metin Soru-Cevap: 10 tur diyalog",
        "  S1: Kalkış şehri? C: Şanghay",
        "  S2: Tarih? C: 15 Ağustos",
        "  S3: Tek yön mü gidiş dönüş mü? ...",
        "",
        "Dinamik Form: 1 gönderim",
        "  Tüm bilgi tek seferde toplanır",
        "  Basamaklı mantık otomatik işlenir",
    ]
    for j, line in enumerate(comp):
        svg.mono(30, 318 + j * 13, line, size=10)

    # Bottom annotation
    svg.text(w / 2, 510, "Form kodu LLM tarafından dinamik üretilir → Basamaklı mantık: \"Gidiş dönüş\" seçilince dönüş tarihi otomatik gösterilir", size=FS_SMALL, fill='darker')

    svg.save(os.path.join(OUT, 'fig5-8.svg'))


# ──────────────────────── fig5-8 ────────────────────────

def fig5_9():
    """SQL Query Agent (artifact mode — data bypasses LLM)"""
    w, h = 880, 580
    svg = SVG(w, h)
    svg.text(w / 2, 30, "SQL Sorgu Ajanı: Artifact Modu vs Geleneksel Mod", size=FS_TITLE, bold=True)

    # Top: Traditional mode (data through LLM)
    svg.rect(20, 55, w - 40, 200, fill='white', stroke='border', dash=True)
    svg.text(60, 78, "Geleneksel mod: veri LLM üzerinden geçer (verimsiz)", size=FS_BODY, bold=True, anchor='start')
    _pill(svg, w - 110, 65, 80, 24, "✗ Verimsiz", fill='dark', font_size=12, bold=True)

    trad_steps = [
        ("User", 'medium', "\"Departman başına kişi sayısı?\""),
        ("LLM", 'light', "SQL üret"),
        ("DB", 'medium', "Sorguyu \\n çalıştır"),
        ("LLM", 'light', "5000 \\n satır oku"),
        ("User", 'medium', "Metin \\n açıklama"),
    ]
    tsx = 60
    for i, (name, fill, desc) in enumerate(trad_steps):
        svg.rect(tsx, 100, 130, 60, fill=fill)
        svg.text(tsx + 65, 118, name, size=FS_SMALL, bold=True)
        for j, line in enumerate(desc.split('\\n')):
            svg.text(tsx + 65, 138 + j * 16, line, size=FS_TINY, fill='text_light')
        if i < len(trad_steps) - 1:
            svg.arrow(tsx + 130, 130, tsx + 150, 130)
        tsx += 155

    svg.rect(60, 175, w - 120, 30, fill='code_bg', stroke='dark', rx=3)
    svg.mono(70, 190, "Sorun: LLM'in veri kopyalaması hataya açık · çok token tüketir · yüksek gecikme", size=12)

    # Separator
    svg.line(30, 265, w - 30, 265, color='dark', dash=True)

    # Bottom: Artifact mode (data bypasses LLM)
    svg.rect(20, 275, w - 40, 280, fill='white', stroke='border', dash=True)
    svg.text(60, 298, "Artifact modu: veri doğrudan ön uca gider (verimli)", size=FS_BODY, bold=True, anchor='start')
    _pill(svg, w - 110, 285, 80, 24, "✓ Verimli", fill='medium', font_size=12, bold=True)

    # LLM generates code, not data
    svg.rect(40, 315, 250, 120, fill='light')
    svg.text(165, 335, "LLM yalnızca kod üretir", size=FS_SMALL, bold=True)
    sql_code = [
        "build_artifact(",
        '  type="sql",',
        '  code="SELECT dept,',
        '    COUNT(*) as cnt',
        '    FROM employees',
        '    GROUP BY dept")',
    ]
    svg.rect(50, 345, 230, len(sql_code) * 14 + 8, fill='code_bg', stroke='dark', rx=3)
    for j, line in enumerate(sql_code):
        svg.mono(58, 358 + j * 14, line, size=10)

    svg.arrow(290, 380, 340, 380)

    # Frontend executes directly
    svg.rect(340, 315, 250, 120, fill='medium')
    svg.text(465, 335, "Ön uç doğrudan yürütür", size=FS_SMALL, bold=True)
    svg.rect(350, 348, 230, 75, fill='code_bg', stroke='dark', rx=3)
    table = [
        "┌────────┬──────┐",
        "│ dept   │ cnt  │",
        "├────────┼──────┤",
        "│ Ar-Ge Dep. │  42  │",
        "│ Pazarlama Dep. │  28  │",
        "└────────┴──────┘",
    ]
    for j, line in enumerate(table):
        svg.mono(358, 360 + j * 12, line, size=9)

    svg.arrow(590, 380, 640, 380)

    # Visualization artifact
    svg.rect(640, 315, 210, 120, fill='light')
    svg.text(745, 335, "Görselleştirme Artifact'ı", size=FS_SMALL, bold=True)
    svg.text(745, 355, "İkinci artifact:", size=FS_TINY, fill='text_light')
    svg.rect(650, 365, 190, 60, fill='code_bg', stroke='dark', rx=3)
    svg.mono(658, 380, "build_artifact(", size=10)
    svg.mono(658, 394, '  type="chart",', size=10)
    svg.mono(658, 408, '  code="bar(data)")', size=10)

    # Data flow annotation
    svg.rect(180, 450, 520, 45, fill='dark')
    svg.text(440, 465, "Veri akışı: DB → Ön uç → Görselleştirme (LLM'i tamamen atlar)", size=FS_BODY, fill='white', bold=True)
    svg.text(440, 483, "LLM yalnızca kod üretmekten sorumludur, veri aktarımından değil", size=FS_TINY, fill='white')

    # Data flow arrow (bypass)
    svg.arrow_curved(465, 435, 745, 435, curve=25, dash=True, color='dark')

    svg.save(os.path.join(OUT, 'fig5-9.svg'))


# ──────────────────────── fig5-6 ────────────────────────

def fig5_7():
    """Experiment 5.10: Production log intelligent diagnosis pipeline"""
    w, h = 880, 560
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Deney 5.10: Üretim günlüğü akıllı teşhisi", size=FS_TITLE, bold=True)

    # Pipeline: left to right, then down
    # Row 1: ingestion → analysis
    svg.rect(20, 60, 250, 160, fill='white', stroke='border', dash=True)
    svg.text(145, 82, "① Günlük toplama", size=FS_BODY, bold=True)
    log_lines = [
        "trajectory_001.json:",
        '  {"role":"user","content":',
        '   "12345 nolu siparişi iptal et"}',
        '  {"role":"assistant",',
        '   "tool_call":"cancel_order"}',
        '  {"role":"tool","result":',
        '   "ERROR: sigorta yok"}',
        '  → Ajan kullanıcıya nedeni bildirmedi',
    ]
    svg.rect(30, 98, 230, len(log_lines) * 14 + 10, fill='code_bg', stroke='dark', rx=3)
    for j, line in enumerate(log_lines):
        svg.mono(38, 112 + j * 14, line, size=9)

    svg.arrow(270, 140, 310, 140)

    svg.rect(310, 60, 260, 160, fill='white', stroke='border', dash=True)
    svg.text(440, 82, "② LLM analizi", size=FS_BODY, bold=True)
    analysis = [
        "Girdi: iz + mimari belge + PRD",
        "",
        "Analiz boyutları:",
        "  - Yürütme akışı beklentiyi karşılıyor mu",
        "  - Araç çağrıları doğru mu",
        "  - Hata işleme uygun mu",
        "  - Kullanıcı deneyimi tatmin edici mi",
        "",
        "→ Sapan adımı ve modülü belirle",
    ]
    for j, line in enumerate(analysis):
        svg.mono(320, 100 + j * 14, line, size=10)

    svg.arrow(570, 140, 610, 140)

    svg.rect(610, 60, 250, 160, fill='white', stroke='border', dash=True)
    svg.text(735, 82, "③ Yapılandırılmış rapor", size=FS_BODY, bold=True)
    report = [
        "Sorun raporu:",
        "  Öncelik: P1 (Kullanıcı Kaybı Riski)",
        "  Modül: cancellation_handler",
        "  Açıklama: İptal başarısızlığından sonra kullanıcıya",
        "    neden ve alternatifler açıklanmıyor",
        "  Öneri: Başarısızlık nedeni açıklaması",
        "    ve sigorta satın alma rehberliği ekle",
    ]
    svg.rect(620, 98, 230, len(report) * 14 + 10, fill='code_bg', stroke='dark', rx=3)
    for j, line in enumerate(report):
        svg.mono(628, 112 + j * 14, line, size=9)

    # Row 2: test case generation → issue creation
    svg.arrow(w / 2, 220, w / 2, 260)

    svg.rect(60, 260, 370, 160, fill='white', stroke='border', dash=True)
    svg.text(245, 282, "④ Regresyon Test Senaryosu Üretimi", size=FS_BODY, bold=True)
    test_code = [
        "def test_cancel_no_insurance():",
        '  """İzlence #001, Tur 3-5"""',
        "  # Tekrar oynat: Kullanıcı ekonomi sınıfı iptali istiyor",
        "  resp = agent.run(",
        '    "12345 nolu siparişi iptal et")',
        "  # Doğrula: Neden açıklanmalı",
        '  assert "sigorta" in resp.text',
        '  assert "alternatif" in resp.text',
        "  # Doğrula: Doğrudan hata dönmemeli",
        '  assert "ERROR" not in resp.text',
    ]
    svg.rect(70, 298, 350, len(test_code) * 14 + 10, fill='code_bg', stroke='dark', rx=3)
    for j, line in enumerate(test_code):
        svg.mono(78, 312 + j * 14, line, size=10)

    svg.arrow(430, 340, 470, 340)

    svg.rect(470, 260, 380, 160, fill='white', stroke='border', dash=True)
    svg.text(660, 282, "⑤ GitHub Issue Otomatik Oluşturma", size=FS_BODY, bold=True)
    issue = [
        "gh issue create \\",
        '  --title "P1: İptalde kullanıcı',
        '    rehberliği eksik" \\',
        '  --body "**Sorun**: Ajan cancel_order',
        '    başarısız olduktan sonra nedeni',
        '    açıklamadan doğrudan hata döndürüyor...',
        '    **İzlence**: #001 Tur 3-5',
        '    **Test**: test_cancel_..." \\',
        '  --assignee @backend-team',
    ]
    svg.rect(480, 298, 360, len(issue) * 14 + 10, fill='code_bg', stroke='dark', rx=3)
    for j, line in enumerate(issue):
        svg.mono(488, 312 + j * 14, line, size=10)

    # Bottom: full pipeline summary
    svg.rect(100, 445, w - 200, 44, fill='dark')
    svg.text(w / 2, 460, "Uçtan Uca Otomasyon: Günlük → Analiz → Rapor → Test → Issue", size=FS_BODY, fill='white', bold=True)
    svg.text(w / 2, 480, "MCP ile GitHub entegrasyonu · Test çerçevesi otomatik tekrar oynatma doğrulaması", size=FS_TINY, fill='white')

    svg.text(w / 2, 530, "Manuel teşhis maliyetini saatlerden dakikalara indirir", size=FS_SMALL, fill='darker', bold=True)

    svg.save(os.path.join(OUT, 'fig5-7.svg'))


# ──────────────────────── fig5-9 ────────────────────────

def fig5_10():
    """Agent Bootstrap Loop (Self-replication and Evolution)"""
    w, h = 880, 555
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Ajan Bootstrap: Koddan Kendi Kendine Çoğalmaya", size=FS_TITLE, bold=True)

    # Evolution timeline at top
    stages = [
        ("Toz → Yıldız", "Fizik Yasaları"),
        ("Yıldız → Gezegen", "Yerçekimsel birikim"),
        ("Gezegen → Yaşam", "DNA kendi kendine çoğalması"),
        ("Yaşam → Ajan", "Kod bootstrap'ı"),
    ]
    sx = 60
    for i, (stage, mechanism) in enumerate(stages):
        fill = 'dark' if i == 3 else ('medium' if i == 2 else 'light')
        svg.rect(sx, 55, 180, 50, fill=fill)
        tc = 'white' if fill in ('dark', 'darker') else 'text'
        svg.text(sx + 90, 72, stage, size=FS_SMALL, bold=True, fill=tc)
        svg.text(sx + 90, 92, mechanism, size=FS_TINY, fill='white' if fill == 'dark' else 'text_light')
        if i < len(stages) - 1:
            svg.arrow(sx + 180, 80, sx + 195, 80)
        sx += 200

    # Key distinction
    svg.line(30, 120, w - 30, 120, color='dark', dash=True)

    svg.rect(30, 135, 400, 70, fill='light')
    svg.text(230, 155, "DNA kendi kendine çoğalması: rastgele mutasyon + doğal seçilim", size=FS_SMALL, bold=True)
    svg.text(230, 177, "Kendini anlamaz · Yönlü değiştiremez · 3.7 milyar yıl kör deneme yanılma", size=FS_TINY, fill='text_light')

    svg.rect(450, 135, 400, 70, fill='dark')
    svg.text(650, 155, "Ajan bootstrap'ı: kodu anlama + yönlü tasarım", size=FS_SMALL, bold=True, fill='white')
    svg.text(650, 177, "Kendi mekanizmasını anlar · Amaçlı yaratır · En iyi uygulamaları miras alır", size=FS_TINY, fill='white')

    # Bootstrap cycle (main diagram)
    svg.rect(20, 225, 390, 295, fill='white', stroke='border', dash=True)
    svg.text(215, 248, "Orijinal Ajan (kendi kodu)", size=FS_BODY, bold=True)

    svg.rect(30, 265, 175, 124, fill='light')
    svg.text(118, 285, "Sistem istemi", size=FS_SMALL, bold=True)
    svg.text(40, 308, "Sen bir havayolu müşteri hizmetleri ajanısın", size=12, anchor='start')
    svg.text(40, 326, "İptal kuralları: ...", size=12, anchor='start')
    svg.text(40, 344, "Aktarım kuralları: ...", size=12, anchor='start')
    svg.text(40, 362, "Araç: cancel_order", size=12, anchor='start')

    svg.rect(215, 265, 185, 124, fill='light')
    svg.text(308, 285, "Ajan çerçeve kodu", size=FS_SMALL, bold=True)
    svg.mono(225, 308, "loop:", size=12)
    svg.mono(225, 326, "  msg = llm(ctx)", size=12)
    svg.mono(225, 344, "  if tool_call:", size=12)
    svg.mono(225, 362, "    exec(tool)", size=12)

    svg.rect(30, 400, 370, 54, fill='code_bg', stroke='dark', rx=4)
    svg.text(215, 419, "Araç tanımı + MCP entegrasyonu + mesaj biçimi", size=FS_SMALL)
    svg.text(215, 438, "Doğrulanmış yüksek kaliteli uygulama", size=FS_TINY, fill='text_light')

    # Arrow: self-replication — label placed above dashed box headers
    svg.text(440, 215, "Kopyala + değiştir", size=FS_TINY, fill='text_light', bold=True)
    svg.arrow(410, 375, 470, 375)

    # New Agent
    svg.rect(470, 225, 390, 295, fill='white', stroke='border', dash=True)
    svg.text(665, 248, "Yeni Ajan (yönlü değişiklik sonrası)", size=FS_BODY, bold=True)

    svg.rect(480, 265, 180, 124, fill='medium')
    svg.text(570, 285, "Yeni sistem istemi", size=FS_SMALL, bold=True)
    svg.text(490, 308, "Sen bir e-ticaret müşteri hizmetleri ajanısın", size=12, anchor='start')
    svg.text(490, 326, "İade kuralları: ...", size=12, anchor='start')
    svg.text(490, 344, "Kargo sorgusu: ...", size=12, anchor='start')
    svg.text(490, 362, "Araç: refund_order", size=12, anchor='start')

    svg.rect(670, 265, 180, 124, fill='light')
    svg.text(760, 285, "Miras alınan çerçeve kodu", size=FS_SMALL, bold=True)
    svg.mono(680, 308, "loop:", size=12)
    svg.mono(680, 326, "  msg = llm(ctx)", size=12)
    svg.mono(680, 344, "  if tool_call:", size=12)
    svg.mono(680, 362, "    exec(tool)", size=12)

    svg.rect(480, 400, 370, 54, fill='code_bg', stroke='dark', rx=4)
    svg.text(665, 419, "Yeni araçlar + yeni iş mantığı", size=FS_SMALL)
    svg.text(665, 438, "Mimari çerçeve tamamen miras alındı → kalite garanti altında", size=FS_TINY, fill='text_light')

    svg.save(os.path.join(OUT, 'fig5-10.svg'))


# ──────────────────────── fig5-10 ────────────────────────

def fig5_11():
    """Experiment 5.14: Meta-Agent pipeline for creating new Agents"""
    w, h = 880, 610
    svg = SVG(w, h)
    svg.text(w / 2, 30, "Deney 5.14: Ajan yaratabilen bir Ajan", size=FS_TITLE, bold=True)

    # Input: user request
    svg.rect(30, 60, 280, 55, fill='medium')
    svg.text(170, 80, "Kullanıcı gereksinimi", size=FS_SMALL, bold=True)
    svg.text(170, 98, "\"Bir e-ticaret iade müşteri hizmetleri Ajanı oluştur\"", size=FS_TINY, fill='text_light')

    svg.arrow(170, 115, 170, 145)

    # Meta-Agent: the creator
    svg.rect(20, 145, 840, 230, fill='white', stroke='border', dash=True)
    svg.text(440, 168, "Meta-Agent (Coding Agent)", size=FS_BODY, bold=True)

    # Step 1: Read reference
    svg.rect(35, 185, 190, 170, fill='light')
    svg.text(130, 205, "① Referans kodu oku", size=FS_SMALL, bold=True)
    svg.mono(45, 228, "read_file:", size=12)
    svg.mono(45, 248, "  agent.py", size=12)
    svg.mono(45, 268, "  tools/*.py", size=12)
    svg.mono(45, 288, "  system_prompt.md", size=12)
    svg.mono(45, 308, "  config.yaml", size=12)
    svg.text(45, 332, "→ Mimari örüntüleri anla", size=12, anchor='start', fill='text_light')

    svg.arrow(225, 270, 248, 270)

    # Step 2: Copy scaffold
    svg.rect(248, 185, 190, 170, fill='light')
    svg.text(343, 205, "② İskeleti kopyala", size=FS_SMALL, bold=True)
    svg.mono(258, 228, "cp -r reference/", size=12)
    svg.mono(258, 248, "  → new_agent/", size=12)
    svg.text(258, 278, "Koru:", size=12, anchor='start', fill='text_light')
    svg.text(258, 298, "  Ajan döngüsü çerçevesi", size=12, anchor='start', fill='text_light')
    svg.text(258, 318, "  Mesaj biçimi / KV optimizasyonu", size=12, anchor='start', fill='text_light')

    svg.arrow(438, 270, 461, 270)

    # Step 3: Targeted modification
    svg.rect(461, 185, 190, 170, fill='medium')
    svg.text(556, 205, "③ Hedefli değişiklikler", size=FS_SMALL, bold=True)
    svg.mono(471, 228, "edit_file:", size=12)
    svg.mono(471, 248, "  system_prompt.md", size=12)
    svg.text(471, 268, "  → E-ticaret iade kuralları", size=12, anchor='start', fill='text_light')
    svg.mono(471, 290, "  tools/refund.py", size=12)
    svg.text(471, 310, "  → İade aracı ekle", size=12, anchor='start', fill='text_light')
    svg.mono(471, 332, "  config.yaml", size=12)

    svg.arrow(651, 270, 674, 270)

    # Step 4: Validate
    svg.rect(674, 185, 175, 170, fill='light')
    svg.text(761, 205, "④ Doğrulama testi", size=FS_SMALL, bold=True)
    svg.mono(684, 228, "bash:", size=12)
    svg.mono(684, 248, "  python agent.py", size=12)
    svg.text(684, 270, "  → Yeni Ajanı başlat", size=12, anchor='start', fill='text_light')
    svg.text(684, 290, "  → Test mesajları gönder", size=12, anchor='start', fill='text_light')
    svg.text(684, 310, "  → Araç çağrılarını kontrol et", size=12, anchor='start', fill='text_light')
    svg.text(684, 330, "  → Konuşma akışını doğrula", size=12, anchor='start', fill='text_light')

    # Output: new agent
    svg.arrow(w / 2, 375, w / 2, 410)

    svg.rect(115, 410, 700, 90, fill='white', stroke='border', dash=True)
    svg.text(465, 432, "Üretilen yeni Ajan", size=FS_BODY, bold=True)

    outputs = [
        ("system_prompt.md", "E-ticaret iade kuralları"),
        ("tools/refund.py", "İade / sorgu araçları"),
        ("agent.py", "Miras alınan çerçeve kodu"),
        ("config.yaml", "Model / parametre yapılandırması"),
    ]
    ox = 135
    for fname, desc in outputs:
        svg.rect(ox, 448, 170, 42, fill='light')
        svg.mono(ox + 85, 462, fname, size=10, anchor='middle')
        svg.text(ox + 85, 480, desc, size=FS_TINY, fill='text_light')
        ox += 178

    # Bottom: comparison
    svg.line(30, 515, w - 30, 515, color='dark', dash=True)
    svg.rect(60, 530, 350, 54, fill='light')
    svg.text(235, 549, "Sıfırdan üretim: en iyi uygulamalar eksik", size=FS_SMALL, bold=True)
    svg.text(235, 571, "Rastgele bağlam yönetimi · Standart olmayan araç tasarımı · Eski API", size=FS_TINY, fill='text_light')

    svg.rect(470, 530, 350, 54, fill='dark')
    svg.text(645, 549, "Örnekten uyarlama: en iyi uygulamaları miras alır", size=FS_SMALL, bold=True, fill='white')
    svg.text(645, 571, "Standart mesaj biçimi · Standart araç tasarımı · Modern API", size=FS_TINY, fill='white')

    svg.save(os.path.join(OUT, 'fig5-11.svg'))


# ──────────────────────── main ────────────────────────

def main():
    os.makedirs(OUT, exist_ok=True)
    figs = [
        fig5_1, fig5_2, fig5_3, fig5_4, fig5_5, fig5_6,
        fig5_7, fig5_8, fig5_9, fig5_10, fig5_11,
    ]
    for fn in figs:
        fn()
        print(f"  ✓ {fn.__name__}: {fn.__doc__}")
    print(f"\nGenerated {len(figs)} figures in {OUT}/")


if __name__ == '__main__':
    main()
