"""Generate all Chapter 1 figures."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from svg_lib import *

OUT = os.path.join(os.path.dirname(__file__), 'images')


def fig1_4():
    """Kimi K3 / GPT-5.6 native agent architecture — caption Figure 1-4"""
    s = SVG(820, 520)

    # Title
    s.text(410, 30, '"Ajan Olarak Model" mimarisi: yerel araç çağırma', size=FS_TITLE, bold=True)

    # Central model box
    s.rect(260, 70, 300, 100, fill='medium')
    s.text(410, 100, 'LLM（Kimi K3 / GPT-5.6）', size=FS_BODY, bold=True)
    s.text(410, 130, 'RL eğitimi sonrası yerel ajan yetenekleri', size=FS_SMALL, fill='text_light')

    # Built-in tools on the right
    s.group_box(620, 70, 180, 210, 'Yerel araçlar')
    s.box(635, 105, 150, 50, '$web_search', fill='light', font_size=FS_SMALL)
    s.box(635, 170, 150, 50, 'code_interpreter', fill='light', font_size=FS_SMALL)
    s.box(635, 235, 150, 50, 'Daha fazla araç...', fill='white', font_size=FS_SMALL)

    s.arrow(560, 120, 633, 130)
    s.arrow(633, 195, 560, 145)

    # ReAct loop below
    s.group_box(100, 210, 460, 280, 'ReAct döngüsü (model içinde özerk yürütme)')

    # Step 1: User input
    s.box(120, 250, 200, 55, 'Kullanıcı: Son bir aydaki Bitcoin trendini ara\n', fill='light', font_size=FS_SMALL)

    # Step 2: Think
    s.box(120, 325, 200, 55, 'Düşünce: Gerçek zamanlı veri\naranmalı, sonra kodla analiz edilmeli', fill='#e8e8e8', font_size=FS_SMALL)
    s.arrow(220, 307, 220, 323)

    # Step 3: Tool call
    s.box(340, 250, 200, 55, '$web_search çağrılıyor\n"Son ay BTC fiyatı"', fill='light', font_size=FS_SMALL)
    s.arrow(322, 277, 338, 277)

    # Step 4: Tool result
    s.box(340, 325, 200, 55, 'Sonuç: [fiyat verisi]\n$67,230 → $71,450', fill='#e8e8e8', font_size=FS_SMALL)
    s.arrow(440, 307, 440, 323)

    # Step 5: Code
    s.box(120, 400, 200, 55, 'code_interpreter çağrılıyor\nRSI, MACD hesaplama kodu', fill='light', font_size=FS_SMALL)
    s.arrow(340, 377, 220, 398, color='dark')

    # Step 6: Final
    s.box(340, 400, 200, 55, 'Nihai çıktı: Teknik analiz\nraporu + görselleştirme grafiği', fill='medium', font_size=FS_SMALL)
    s.arrow(322, 427, 338, 427)

    # RL training signal — go through the gap between ReAct/tools on the right, avoid blocking internal content
    s.arrow_curved(565, 480, 410, 172, curve=40, dash=True, color='dark')
    s.text(605, 330, 'RL eğitim sinyali', size=FS_TINY, fill='text_light', bold=True, anchor='start')

    # Left side: what's different from traditional
    s.group_box(15, 70, 230, 120, 'Geleneksel çerçevelerden farklar')
    s.text(130, 110, '✗ Harici orkestrasyon koduna gerek yok', size=FS_SMALL, anchor='middle')
    s.text(130, 135, '✗ Elle ReAct döngüsü yazmaya gerek yok', size=FS_SMALL, anchor='middle')
    s.text(130, 160, '✓ Model tüm süreci özerk şekilde belirler', size=FS_SMALL, anchor='middle')

    s.save(f'{OUT}/fig1-3.svg')  # ReAct execution process → Figure 1-3


def fig1_1():
    """Three learning paradigms — caption Figure 1-1."""
    s = SVG(820, 480)

    s.text(410, 30, 'Ajanlar için üç öğrenme paradigması', size=FS_TITLE, bold=True)

    col_w = 240
    gap = 20
    x_start = (820 - 3 * col_w - 2 * gap) / 2

    for i, (title, time_label, items, example) in enumerate([
        ('Eğitim sonrası', 'Eğitim zamanı', [
            'Model ağırlıklarını değiştirir',
            'Kalıcı · genel',
            'Yüksek maliyet · yavaş güncellenir',
        ], 'ör. bir aracı ne zaman çağıracağını öğrenir'),
        ('Bağlam içi öğrenme', 'Çıkarım zamanı', [
            'Dikkat mekanizmasıyla yumuşak güncelleme',
            'Geçici · anında uyum sağlar',
            'Bağlam penceresiyle sınırlı',
        ], 'ör. 3 örnekten bir biçim öğrenir'),
        ('Dışsallaştırılmış öğrenme', 'Çalışma zamanı', [
            'Bilgi tabanı + üretilen araçlar',
            'Kalıcı · güncellenebilir',
            'Güvenilir · doğrulanabilir',
        ], 'ör. bir iş akışını araca dönüştürür'),
    ]):
        x = x_start + i * (col_w + gap)

        # Header
        s.box(x, 65, col_w, 65, title, fill='medium', bold=True, font_size=FS_BODY)

        # Time badge
        s.badge(x + col_w / 2 - 40, 140, 80, 28, time_label, fill='darker')

        # Items
        for j, item in enumerate(items):
            y = 185 + j * 45
            s.box(x, y, col_w, 38, item, fill='light', font_size=FS_SMALL)

        # Example
        s.rect(x, 330, col_w, 45, fill='code_bg', stroke='dark', rx=4)
        s.text(x + col_w / 2, 352, example, size=FS_SMALL, fill='text_light')

    # Timeline arrow at bottom
    s.arrow(60, 430, 760, 430, color='dark')
    s.text(60, 455, 'Yavaş (Haftalar)', size=FS_SMALL, fill='text_light', anchor='start')
    s.text(410, 455, 'Öğrenme Hızı', size=FS_SMALL, fill='text_light')
    s.text(760, 455, 'Hızlı (Milisaniyeler)', size=FS_SMALL, fill='text_light', anchor='end')

    s.save(f'{OUT}/fig1-4.svg')  #Three Learning Paradigms → Figure 1-4


def fig1_2():
    """Context ablation experiment design — caption Figure 1-2."""
    W = 1000
    s = SVG(W, 470)

    s.text(W / 2, 30, 'Bağlam Ablasyon Deneyi Tasarımı', size=FS_TITLE, bold=True)

    # Two-line column headers so each fits its column without overlap.
    components = [
        ('Sistem', 'istemi'),
        ('Araç', 'tanımları'),
        ('Araç çal.', 'sonuçları'),
        ('Düşünce', 'süreci'),
        ('Geçmiş', 'mesajlar'),
    ]
    comp_w = 108
    comp_gap = 10
    label_x = 168          # row labels right-anchored here
    comp_x = 182           # check grid starts here

    for i, (l1, l2) in enumerate(components):
        x = comp_x + i * (comp_w + comp_gap)
        s.text(x + comp_w / 2, 56, l1, size=FS_SMALL, bold=True)
        s.text(x + comp_w / 2, 76, l2, size=FS_SMALL, bold=True)

    # Result column header
    result_x = comp_x + len(components) * (comp_w + comp_gap) + 12
    s.text(result_x + 90, 66, 'Sonuç', size=FS_SMALL, bold=True)

    # Experiment rows (labels shortened to sit within the left margin)
    conditions = [
        ('Tam referans', [True, True, True, True, True], '✓ Normal çalışır'),
        ('Araç tanımı yok', [True, False, True, True, True], '✗ Araç çağıramaz'),
        ('Araç sonucu yok', [True, True, False, True, True], '✗ Kör döngü'),
        ('Muhakeme yok', [True, True, True, False, True], '△ Tutarsız kararlar'),
        ('Geçmiş yok', [True, True, True, True, False], '△ Tekrarlanan işlemler'),
    ]

    for j, (label, flags, result) in enumerate(conditions):
        y = 100 + j * 68

        # Row label
        s.text(label_x, y + 28, label, size=FS_SMALL, bold=True, anchor='end')

        for i, present in enumerate(flags):
            x = comp_x + i * (comp_w + comp_gap)
            fill = 'light' if present else 'white'
            stroke = 'border' if present else 'dark'
            s.rect(x, y, comp_w, 55, fill=fill, stroke=stroke, dash=not present)
            if present:
                s.text(x + comp_w / 2, y + 28, '✓', size=FS_BODY)
            else:
                s.text(x + comp_w / 2, y + 28, '✗', size=FS_BODY, fill='dark')

        # Result (in its own column to the right of the check grid)
        s.text(result_x + 90, y + 28, result, size=FS_SMALL, anchor='middle',
               fill='text' if '✓' in result else ('text_light' if '△' in result else 'dark'))

    s.save(f'{OUT}/fig1-1.svg')  # Context ablation experiment → Figure 1-1


def fig1_3():
    """Agent trajectory — caption Figure 1-3."""
    s = SVG(820, 680)

    s.text(410, 30, 'Ajan izlencesi: Çoklu para birimi toplama görevi için ReAct döngüsü', size=FS_TITLE, bold=True)

    lx = 40  # left margin
    rw = 480  # box width
    code_w = 460

    y = 60

    # Round 1
    s.badge(lx, y, 80, 26, 'Tur 1', fill='darker')
    y += 36

    # User message
    s.rect(lx, y, rw, 50, fill='light')
    s.text(lx + 10, y + 16, 'user', size=FS_SMALL, bold=True, anchor='start')
    s.text(lx + 10, y + 38, '"Toplam yıllık geliri hesapla: Ç1 $2,5M, Ç2 €2,1M, Ç3 £1,8M"', size=FS_TINY, anchor='start')
    y += 60

    # Assistant reasoning
    s.rect(lx, y, rw, 45, fill='#e8e8e8')
    s.text(lx + 10, y + 14, 'assistant.reasoning', size=FS_SMALL, bold=True, anchor='start', fill='darker')
    s.text(lx + 10, y + 34, '"EUR ve GBP\'yi USD\'ye çevirip toplamak gerekiyor"', size=FS_TINY, anchor='start')
    y += 55

    # Tool calls
    s.rect(lx, y, rw, 70, fill='code_bg', stroke='dark', rx=4)
    s.text(lx + 10, y + 14, 'assistant.tool_calls', size=FS_SMALL, bold=True, anchor='start', fill='darker')
    s.mono(lx + 10, y + 36, 'convert_currency(2100000, "EUR", "USD")', size=FS_TINY)
    s.mono(lx + 10, y + 54, 'convert_currency(1800000, "GBP", "USD")', size=FS_TINY)
    y += 80

    # Tool results
    s.rect(lx, y, rw, 55, fill='light')
    s.text(lx + 10, y + 14, 'tool (result)', size=FS_SMALL, bold=True, anchor='start', fill='darker')
    s.mono(lx + 10, y + 36, 'EUR→USD: 2,282,608.70', size=FS_TINY)
    s.mono(lx + 250, y + 36, 'GBP→USD: 2,278,481.01', size=FS_TINY)
    y += 65

    # Round 2
    s.badge(lx, y, 80, 26, 'Tur 2', fill='darker')
    y += 36

    # Assistant reasoning 2
    s.rect(lx, y, rw, 45, fill='#e8e8e8')
    s.text(lx + 10, y + 14, 'assistant.reasoning', size=FS_SMALL, bold=True, anchor='start', fill='darker')
    s.text(lx + 10, y + 34, '"Döviz kurları alındı, toplamak için code interpreter çağrılıyor"', size=FS_TINY, anchor='start')
    y += 55

    # Code interpreter call
    s.rect(lx, y, rw, 50, fill='code_bg', stroke='dark', rx=4)
    s.text(lx + 10, y + 14, 'assistant.tool_calls', size=FS_SMALL, bold=True, anchor='start', fill='darker')
    s.mono(lx + 10, y + 36, 'code_interpreter("total = 2.5M + 2.28M + 2.28M")', size=FS_TINY)
    y += 60

    # Round 3
    s.badge(lx, y, 80, 26, 'Tur 3', fill='darker')
    y += 36

    # Final answer
    s.rect(lx, y, rw, 45, fill='medium')
    s.text(lx + 10, y + 14, 'assistant.content (final answer)', size=FS_SMALL, bold=True, anchor='start')
    s.text(lx + 10, y + 36, '"Toplam yıllık gelir $7.061.089,71, çeyreklik ortalama $2.353.696,57"', size=FS_TINY, anchor='start')
    y += 55

    # Right side: brace + annotation
    bx = 540
    s.brace_right(bx, 60, y - 10, '')
    s.text(600, 250, 'İzlence', size=FS_BODY, bold=True, anchor='start')
    s.text(600, 280, '=', size=FS_BODY, anchor='start')
    s.text(600, 310, 'LLM\'in her çağrıda', size=FS_BODY, anchor='start')
    s.text(600, 340, 'gördüğü tam', size=FS_BODY, anchor='start')
    s.text(600, 370, 'girdi', size=FS_BODY, anchor='start')

    # Key insight box on right
    s.group_box(570, 410, 230, 140, 'Temel özellikler')
    s.text(685, 445, 'Bağlam birikimi', size=FS_SMALL, bold=True)
    s.text(685, 470, 'Her turda tüm geçmiş görülür', size=FS_TINY, fill='text_light')
    s.text(685, 500, 'Yapılandırılmış izlence', size=FS_SMALL, bold=True)
    s.text(685, 525, 'user / assistant / tool', size=FS_TINY, fill='text_light')

    s.save(f'{OUT}/fig1-2.svg')  # Agent trajectory → Figure 1-2


def fig1_wf_chaining():
    """Prompt chaining — workflow pattern (ch1 Orchestration Patterns section)."""
    s = SVG(820, 300)

    s.text(410, 28, 'İstem zincirleme deseni: çok adımlı içerik üretimi', size=FS_TITLE, bold=True)

    # Nodes with concrete descriptions
    nodes = [
        ('Gereksinim belgesi', 'light', FS_SMALL),
        ('LLM: Taslak oluştur', '#e8e8e8', FS_SMALL),
        ('LLM: Metni yaz', '#e8e8e8', FS_SMALL),
        ('LLM: Çeviri', '#e8e8e8', FS_SMALL),
        ('Çok Dilli Dokümantasyon', 'medium', FS_SMALL),
    ]

    node_w = 130
    node_h = 55
    gap = 15
    total = len(nodes) * node_w + (len(nodes) - 1) * gap
    x_start = (820 - total) / 2
    y = 65

    for i, (label, fill, fs) in enumerate(nodes):
        x = x_start + i * (node_w + gap)
        s.box(x, y, node_w, node_h, label, fill=fill, font_size=fs)
        if i > 0:
            px = x_start + (i - 1) * (node_w + gap) + node_w
            s.arrow(px + 2, y + node_h / 2, x - 2, y + node_h / 2)

    # Gate symbols between steps
    gate_y = y + node_h + 15
    for i in [1, 2]:
        gx = x_start + i * (node_w + gap) + node_w / 2
        s.diamond(gx, gate_y + 22, 60, 40, fill='white', label='Kontrol', font_size=FS_TINY)
        s.line(gx, y + node_h, gx, gate_y + 2, dash=True, color='dark')

    # Example content snippets below
    snippet_y = gate_y + 60
    snippets = [
        (x_start + 15, '"Ürün Sürüm Notları"'),
        (x_start + node_w + gap + 15, '→ 5 Bölümlük Taslak'),
        (x_start + 2 * (node_w + gap) + 15, '→ 3000 Kelimelik Belge'),
        (x_start + 3 * (node_w + gap) + 15, '→ EN / JP / KR'),
    ]
    for sx, txt in snippets:
        s.text(sx, snippet_y, txt, size=FS_TINY, fill='text_light', anchor='start')

    s.save(f'{OUT}/fig1-5.svg')


def fig1_wf_routing():
    """Routing — workflow pattern (ch1 Orchestration Patterns section)."""
    s = SVG(820, 440)

    s.text(410, 28, 'Yönlendirme Deseni: Müşteri Hizmetleri Sınıflandırması', size=FS_TITLE, bold=True)

    # Input
    s.box(30, 130, 150, 55, 'Kullanıcı Sorgusu', fill='medium', font_size=FS_BODY)

    # Router
    s.diamond(300, 157, 140, 80, fill='#e8e8e8', label='Sınıflandırıcı', font_size=FS_SMALL)
    s.arrow(182, 157, 230, 157)

    # Branches
    branches = [
        (55, 'İade Talebi', 'İade Politikası İstemi\n+ Sipariş API', 'light'),
        (155, 'Teknik Destek', 'Tanı İstemi\n+ Log Araçları', 'light'),
        (255, 'SSS', 'SSS İstemi\n+ Bilgi Tabanı', 'light'),
        (355, 'Diğer', 'Haiku (Düşük Maliyet)\n+ Genel İstem', 'white'),
    ]

    bx = 490
    bw = 160
    for i, (by_offset, label, desc, fill) in enumerate(branches):
        by = by_offset
        s.box(bx, by, bw, 50, label, fill=fill, bold=True, font_size=FS_SMALL)
        s.box(bx + bw + 10, by, 140, 50, desc, fill='code_bg', font_size=FS_TINY)
        s.arrow(370, 157, bx - 2, by + 25)

    # Annotation
    s.text(410, 425, 'Not: Sınıflandırma LLM veya geleneksel sınıflandırıcıyla yapılabilir; basit/yaygın sorgular küçük modellere yönlendirilir', size=FS_SMALL, fill='text_light')

    s.save(f'{OUT}/fig1-6.svg')


def fig1_wf_parallel():
    """Parallelization — workflow pattern (ch1 Orchestration Patterns section)."""
    s = SVG(820, 360)

    s.text(410, 28, 'Paralelleştirme Deseni: Çok Yönlü Kod İncelemesi', size=FS_TITLE, bold=True)

    # Input
    s.box(30, 130, 150, 55, 'Kod Commit\'i\nPull Request', fill='medium', font_size=FS_SMALL)

    # Split
    s.text(220, 157, 'Bölümleme', size=FS_SMALL, bold=True)

    # Parallel workers
    workers = [
        (70, 'Güvenlik İnceleme LLM₁', 'SQL Enjeksiyonu\nXSS\nYetki Sızıntısı'),
        (155, 'Stil İnceleme LLM₂', 'İsimlendirme Kuralları\nKod Tekrarı\nKarmaşıklık'),
        (240, 'Mantık İnceleme LLM₃', 'Sınır Koşulları\nNull Göstericiler\nEşzamanlılık Sorunları'),
    ]

    wx = 290
    ww = 155
    for i, (wy, title, items) in enumerate(workers):
        s.box(wx, wy, ww, 55, title, fill='light', bold=True, font_size=FS_SMALL)
        s.box(wx + ww + 5, wy, 130, 55, items, fill='code_bg', font_size=FS_TINY)
        s.arrow(180, 157, wx - 2, wy + 28)

    # Aggregate
    s.box(640, 130, 150, 55, 'Sonuçları Birleştir\nKapsamlı İnceleme Raporu', fill='medium', font_size=FS_SMALL)
    for i, (wy, _, _) in enumerate(workers):
        s.arrow(wx + ww + 135 + 2, wy + 28, 638, 157)

    s.save(f'{OUT}/fig1-7.svg')


def fig1_wf_orchestrator():
    """Orchestrator-workers — workflow pattern (ch1 Orchestration Pattern section)."""
    s = SVG(820, 440)

    s.text(410, 28, 'Orkestratör-işçi deseni: çok dosyalı kod değişikliği', size=FS_TITLE, bold=True)

    # Orchestrator at top: title + internal sub-description arranged vertically
    s.rect(260, 60, 300, 95, fill='medium')
    s.text(410, 82, 'Orkestratör LLM', size=FS_BODY, bold=True)
    s.rect(270, 105, 280, 38, fill='#e8e8e8', rx=4)
    s.text(410, 124, '"Sorunu Analiz Et → Dosyaları Bul → Alt Görevleri Ata"', size=FS_TINY)

    # Workers
    workers = [
        (40, 'İşçi 1', 'auth.py dosyasını değiştir\nOAuth2 desteği ekle', 'Read/Edit\nDosya aracı'),
        (290, 'İşçi 2', 'api.py dosyasını değiştir\nYeni endpoint ekle', 'Read/Edit\nDosya aracı'),
        (540, 'İşçi 3', 'test_auth.py yaz\nTest senaryoları', 'Testleri çalıştır\nAracı'),
    ]

    wy = 220
    ww = 230
    wh = 55
    for wx, title, task, tools in workers:
        s.box(wx, wy, ww, wh, f'{title}：{task}', fill='light', font_size=FS_SMALL)
        s.box(wx + 20, wy + wh + 10, ww - 40, 40, tools, fill='code_bg', font_size=FS_TINY)
        s.arrow(410, 157, wx + ww / 2, wy - 2)

    # Synthesize
    s.box(260, 370, 300, 55, 'Orkestratör: sonuçları birleştir → tutarlılığı doğrula', fill='medium', font_size=FS_SMALL)
    for wx, _, _, _ in workers:
        s.arrow(wx + ww / 2, wy + wh + 52, 410, 368)

    s.save(f'{OUT}/fig1-8.svg')


def fig1_wf_evaluator():
    """Evaluator-optimizer — workflow pattern (ch1 Orchestration Pattern section)."""
    s = SVG(820, 380)

    s.text(410, 28, 'Değerlendirici-optimize edici deseni: edebi çeviri yinelemesi', size=FS_TITLE, bold=True)

    # Generator
    s.box(50, 100, 200, 65, 'Üretici LLM\nİlk çeviriyi oluştur', fill='light', font_size=FS_SMALL)

    # Output
    s.rect(50, 185, 200, 45, fill='code_bg', stroke='dark', rx=4)
    s.text(150, 208, '"Bahar uykusu şafaktan habersiz" → v1 çeviri', size=FS_TINY)
    s.arrow(150, 167, 150, 183)

    # Evaluator
    s.box(330, 100, 200, 65, 'Değerlendirici LLM\nÇok boyutlu puanlama', fill='#e8e8e8', font_size=FS_SMALL)
    s.arrow(252, 207, 330, 160)

    # Evaluation criteria
    s.rect(330, 185, 200, 80, fill='code_bg', stroke='dark', rx=4)
    s.text(340, 205, 'Doğruluk: 4/5', size=FS_TINY, anchor='start')
    s.text(340, 225, 'Akıcılık: 3/5 ← geliştirilmeli', size=FS_TINY, anchor='start')
    s.text(340, 245, 'Kültürel uyum: 4/5', size=FS_TINY, anchor='start')
    s.arrow(430, 167, 430, 183)

    # Feedback loop — label placed above arc to avoid blocking evaluator content
    s.arrow_curved(430, 267, 150, 98, curve=80, dash=True, color='dark')
    s.text(290, 90, 'Geri bildirim + iyileştirme önerileri', size=FS_TINY, fill='text_light', bold=True)

    # Iteration indicator
    s.box(610, 100, 170, 55, 'Yineleme sayısı: n', fill='white', font_size=FS_SMALL)
    s.text(695, 170, 'Çıkış koşulları:', size=FS_SMALL, bold=True, anchor='start')
    s.text(695, 195, '① Tüm boyutlar ≥ 4/5', size=FS_TINY, anchor='start', fill='text_light')
    s.text(695, 218, '② Maksimum tur sayısına ulaşıldı', size=FS_TINY, anchor='start', fill='text_light')

    # Final output
    s.box(220, 310, 380, 55, 'Nihai çıktı: 3 yinelemeden sonra yüksek kaliteli çeviri', fill='medium', font_size=FS_SMALL)

    s.save(f'{OUT}/fig1-9.svg')


def fig1_5():
    """Autonomous Agent loop — caption Figure 1-5."""
    s = SVG(820, 500)

    s.text(410, 28, 'Özerk Ajan yürütme döngüsü', size=FS_TITLE, bold=True)

    # While loop structure
    s.rect(80, 60, 500, 380, fill='white', stroke='border', rx=8, dash=True)
    s.text(330, 82, 'while not done:', size=FS_BODY, bold=True)

    # Step 1: Think — title above box, code inside box
    s.rect(120, 100, 420, 60, fill='#e8e8e8')
    s.text(130, 115, '① Düşün (Muhakeme)', size=FS_SMALL, bold=True, anchor='start')
    s.rect(130, 125, 400, 28, fill='code_bg', rx=4)
    s.mono(140, 140, '"Arama sonuçları analiz ediliyor...bilgi yetersiz, daha fazla arama gerekli"', size=FS_TINY)

    # Step 2: Act
    s.rect(120, 175, 420, 60, fill='light')
    s.text(130, 190, '② Eylem', size=FS_SMALL, bold=True, anchor='start')
    s.rect(130, 200, 400, 28, fill='code_bg', rx=4)
    s.mono(140, 215, 'web_search("2025 Ajan RL eğitim teknikleri")', size=FS_TINY)
    s.arrow(330, 162, 330, 173)

    # Step 3: Observe
    s.rect(120, 250, 420, 60, fill='light')
    s.text(130, 265, '③ Gözlem', size=FS_SMALL, bold=True, anchor='start')
    s.rect(130, 275, 400, 28, fill='code_bg', rx=4)
    s.mono(140, 290, 'tool_result: "3 ilgili makale bulundu..."', size=FS_TINY)
    s.arrow(330, 237, 330, 248)

    # Loop back arrow
    s.arrow_curved(540, 280, 540, 120, curve=-40, label='Döngüye devam', color='dark')

    # Exit conditions on the right
    s.group_box(610, 60, 190, 190, 'Çıkış koşulları')
    exits = [
        '① Görev tamamlandı',
        '② final_answer çağrıldı',
        '③ Araç çağrısı dönmedi',
        '④ Maksimum tur sayısına ulaşıldı',
        '⑤ Hata sayısı aşıldı',
    ]
    for i, ex in enumerate(exits):
        s.text(620, 100 + i * 32, ex, size=FS_SMALL, anchor='start')

    # Bottom: concrete iteration example
    s.rect(80, 360, 500, 70, fill='medium', rx=6)
    s.text(330, 380, 'Pratik yürütme örneği: SWE-bench kod düzeltmesi', size=FS_SMALL, bold=True)
    s.text(330, 405, 'Kodu ara → Hatayı bul → Dosyayı düzenle → Testleri çalıştır → Başarısız → Tekrar düzenle → Testler geçti → Tamam', size=FS_TINY)
    s.text(330, 425, '(5 tur yineleme, 12 araç çağrısı)', size=FS_TINY, fill='text_light')

    # Done arrow
    s.arrow(330, 312, 330, 358, label='done = True')

    s.save(f'{OUT}/fig1-10.svg')


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    # In-chapter figures (referenced as 图 1-1 ~ 图 1-5)
    fig1_1()
    fig1_2()
    fig1_3()
    fig1_4()
    fig1_5()
    # Workflow pattern figures (currently unused in chapter1.md;
    # kept for potential future use)
    fig1_wf_chaining()
    fig1_wf_routing()
    fig1_wf_parallel()
    fig1_wf_orchestrator()
    fig1_wf_evaluator()
    print("Chapter 1: 5 in-chapter + 5 workflow figures generated.")
