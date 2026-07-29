#!/usr/bin/env python3
"""Chapter 8 figures — Agent's self-evolution.

NOTE: this generator was previously a stray copy of chapter 9's figures, which
left fig8-1..fig8-7 showing chapter-9 content. It has been rewritten so each
figure matches its caption in chapter8.md. Figures are built with svg_lib;
titles live in the body text (svg_lib strips in-figure titles).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svg_lib import SVG, FS_SMALL, FS_TINY, FS_BODY

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images')


def _pipeline(stages, fname, W=880, feedback=None):
    """Horizontal stage pipeline with an optional dashed feedback loop."""
    n = len(stages)
    bw = min(190, (W - 40 - (n - 1) * 22) // n)
    bh, gap = 84, 22
    H = 234 if feedback else 174   # +24 for the 40px title-crop margin
    s = SVG(W, H)
    x0 = (W - (n * bw + (n - 1) * gap)) / 2
    y = 48                          # start below the TITLE_CROP_PX=40 line
    pos = []
    for i, (lab, sub) in enumerate(stages):
        x = x0 + i * (bw + gap)
        s.box(x, y, bw, bh, lab, sublabel=sub, bold=True, fill='light')
        pos.append(x)
        if i > 0:
            s.arrow(pos[i - 1] + bw + 2, y + bh / 2, x - 2, y + bh / 2)
    if feedback:
        lx = pos[-1] + bw / 2
        fx = pos[0] + bw / 2
        ry = y + bh + 34
        s.line(lx, y + bh, lx, ry, dash=True)
        s.line(lx, ry, fx, ry, dash=True)
        s.arrow(fx, ry, fx, y + bh + 2, dash=True)
        s.text((lx + fx) / 2, ry + 18, feedback, size=FS_SMALL, fill='text_light')
    s.save(os.path.join(OUT, fname + '.svg'))


def fig8_1():  #Externalized learning loop
    _pipeline([("Görevi tamamla", "Ham deneyim üret"), ("Deneyimi rafine et", "Özetle, sıkıştır, yapılandır"),
               ("Harici sistemde sakla", "Bilgi tabanı/araçlar, getirilebilir"), ("Getir ve yeniden kullan", "Sonraki görevde çağır")],
              'fig8-1', feedback="Deneyim kalıcı olarak birikir, oturumlar arası yeniden kullanılır")


def fig8_2():  #GAIA experience learning system
    _pipeline([("Başarılı izlence", "Görevi tamamlama süreci"), ("Strateji özeti", "Bilgi özetine damıt"),
               ("Bilgi özeti tabanı", "Anlamsal indeks oluştur"), ("Erişim enjeksiyonu", "Ajan karar verirken kullanır")],
              'fig8-2', feedback="Benzer görevler için geçmiş deneyimi yeniden kullan")


def fig8_3():  #Hierarchical tool matching (server level → tool level)
    W, H = 620, 354
    s = SVG(W, H)
    cx = W / 2
    s.box(cx - 150, 46, 300, 52, "Kullanıcı sorgusu", sublabel="\"Bu dosyayı hata ayıkla\"", bold=True, fill='light')
    s.arrow(cx, 100, cx, 120)
    s.box(cx - 220, 122, 440, 62, "Katman 1: Sunucu düzeyi anlamsal arama",
          sublabel="Yüzlerce MCP sunucusu → en iyi K sunucuyu getir", bold=True, fill='light')
    s.arrow(cx, 186, cx, 208)
    s.box(cx - 220, 210, 440, 62, "Katman 2: Araç düzeyi anlamsal arama",
          sublabel="Yalnızca en iyi K sunucunun araçları arasında eşleştir → en iyi N araç", bold=True, fill='light')
    s.arrow(cx, 274, cx, 296)
    s.box(cx - 150, 298, 300, 46, "Seçilen araç",
          sublabel="Aday kapsamını belirgin şekilde daraltır, seçim maliyetini azaltır", bold=True, fill='light')
    s.save(os.path.join(OUT, 'fig8-3.svg'))


def fig8_4():  #KV Cache Optimization for Dynamic Tool Loading (Naive vs Optimized)
    W, H = 860, 244
    s = SVG(W, H)
    s.text(220, 46, "Naif: sistem isteminde tüm araç tanımları", size=FS_SMALL, bold=True, fill='darker')
    s.rect(30, 62, 380, 70, fill='#f0d8d8')
    s.text(220, 84, "Sistem istemi + tüm araç tanımları", size=FS_SMALL, bold=True)
    s.text(220, 108, "Herhangi bir araç değişikliği → tüm KV önbelleği geçersiz olur", size=FS_TINY, fill='text_light')
    s.rect(30, 140, 380, 46, fill='light')
    s.text(220, 163, "Her turda yeniden hesaplanır, maliyet yüksek", size=FS_SMALL)

    s.text(640, 46, "Optimize: araç tanımları istendiğinde yüklenir", size=FS_SMALL, bold=True, fill='darker')
    s.rect(450, 62, 380, 40, fill='#d8e8d8')
    s.text(640, 82, "Kararlı sistem istemi (önbellek isabet öneki)", size=FS_SMALL, bold=True)
    s.rect(450, 106, 380, 40, fill='light')
    s.text(640, 126, "İstendiğinde eklenen araç tanımları (değişen kısım)", size=FS_SMALL)
    s.rect(450, 150, 380, 40, fill='light')
    s.text(640, 170, "Konuşma izlencesi", size=FS_SMALL)
    s.text(640, 206, "Kararlı önek değişmez → KV Cache sürekli yeniden kullanılır", size=FS_TINY, fill='text_light')
    s.line(430, 54, 430, 220, dash=True)
    s.save(os.path.join(OUT, 'fig8-4.svg'))


def fig8_5():  #Agent Self-Evolution Pipeline (Requirement Identification → Tool Search → Code Encapsulation → Tool Registration)
    _pipeline([("① Gereksinim Tespiti", "Mevcut araçlar yetersiz"), ("② Araç Arama", "Açık dünya araması"),
               ("③ Kod Kapsülleme", "Üret ve kapsülle"), ("④ Araç Kaydı", "Kütüphaneye ekle, yeniden kullan")],
              'fig8-5', feedback="Yeni kaydedilen araçlar sonraki görevlerde yeniden kullanılabilir, yetenek sınırları sürekli genişler")


def fig8_6():  #Voyager Continuous Learning Architecture (Curriculum Generator + Skill Library + Iterative Prompting)
    _pipeline([("Müfredat Üreteci", "Kademeli yeni görevler öner"), ("Yinelemeli İstem Mekanizması", "Beceri kodu üret ve hata ayıkla"),
               ("Beceri Kütüphanesi", "Yeniden kullanılabilir becerileri sakla")],
              'fig8-6', W=760, feedback="Beceri birikimi daha zor görevlerin kilidini açar (açık dünya keşfi)")


def fig8_7():  #Experiment 8-5 Self-Evolution Pipeline (Search → Evaluate → Test → Encapsulate → Reuse)
    _pipeline([("① Ara", "Açık ağda araç bul"), ("② Değerlendir", "Uygunluğu belirle"), ("③ Test Et", "Kullanılabilirliği doğrula"),
               ("④ Paketle", "Standart araca sar"), ("⑤ Yeniden Kullan", "Araç kütüphanesine ekle")],
              'fig8-7', W=940, feedback="Yeni araçlar sonraki görevlerde yeniden kullanılmak üzere biriktirilir")


if __name__ == '__main__':
    for fn in (fig8_1, fig8_2, fig8_3, fig8_4, fig8_5, fig8_6, fig8_7):
        fn()
        print('saved', fn.__name__)
