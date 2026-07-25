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
    _pipeline([("Selesaikan tugas", "Hasilkan pengalaman mentah"), ("Sempurnakan pengalaman", "Ringkas, kompresi, susun"),
               ("Simpan di sistem eksternal", "Basis pengetahuan/alat, dapat diambil"), ("Ambil dan gunakan kembali", "Panggil di tugas berikutnya")],
              'fig8-1', feedback="Pengalaman terakumulasi secara persisten, digunakan kembali di berbagai sesi")


def fig8_2():  #GAIA experience learning system
    _pipeline([("Lintasan keberhasilan", "Proses penyelesaian tugas"), ("Ringkasan strategi", "Sempurnakan menjadi ringkasan pengetahuan"),
               ("Basis ringkasan pengetahuan", "Bangun indeks semantik"), ("Injeksi pengambilan", "Agen gunakan saat membuat keputusan")],
              'fig8-2', feedback="Gunakan kembali pengalaman historis untuk tugas serupa")


def fig8_3():  #Hierarchical tool matching (server level → tool level)
    W, H = 620, 354
    s = SVG(W, H)
    cx = W / 2
    s.box(cx - 150, 46, 300, 52, "Kueri pengguna", sublabel="\"Debug file ini\"", bold=True, fill='light')
    s.arrow(cx, 100, cx, 120)
    s.box(cx - 220, 122, 440, 62, "Lapisan 1: Pencarian semantik tingkat server",
          sublabel="Ratusan server MCP → panggil Top-K server relevan", bold=True, fill='light')
    s.arrow(cx, 186, cx, 208)
    s.box(cx - 220, 210, 440, 62, "Lapisan 2: Pencarian semantik tingkat alat",
          sublabel="Cocokkan hanya di dalam alat dari Top-K server → Top-N alat", bold=True, fill='light')
    s.arrow(cx, 274, cx, 296)
    s.box(cx - 150, 298, 300, 46, "Alat terpilih",
          sublabel="Secara signifikan mempersempit cakupan kandidat, mengurangi biaya pemilihan", bold=True, fill='light')
    s.save(os.path.join(OUT, 'fig8-3.svg'))


def fig8_4():  #KV Cache Optimization for Dynamic Tool Loading (Naive vs Optimized)
    W, H = 860, 244
    s = SVG(W, H)
    s.text(220, 46, "Naif: semua definisi alat dalam prompt sistem", size=FS_SMALL, bold=True, fill='darker')
    s.rect(30, 62, 380, 70, fill='#f0d8d8')
    s.text(220, 84, "Prompt sistem + semua definisi alat", size=FS_SMALL, bold=True)
    s.text(220, 108, "Perubahan alat apa pun → seluruh cache KV tidak valid", size=FS_TINY, fill='text_light')
    s.rect(30, 140, 380, 46, fill='light')
    s.text(220, 163, "Dihitung ulang setiap putaran, biaya tinggi", size=FS_SMALL)

    s.text(640, 46, "Dioptimalkan: definisi alat dimuat sesuai permintaan", size=FS_SMALL, bold=True, fill='darker')
    s.rect(450, 62, 380, 40, fill='#d8e8d8')
    s.text(640, 82, "Prompt sistem stabil (awalan cache-hit)", size=FS_SMALL, bold=True)
    s.rect(450, 106, 380, 40, fill='light')
    s.text(640, 126, "Definisi alat ditambahkan sesuai permintaan (bagian yang berubah)", size=FS_SMALL)
    s.rect(450, 150, 380, 40, fill='light')
    s.text(640, 170, "Lintasan percakapan", size=FS_SMALL)
    s.text(640, 206, "Awalan stabil tidak berubah → Cache KV terus digunakan kembali", size=FS_TINY, fill='text_light')
    s.line(430, 54, 430, 220, dash=True)
    s.save(os.path.join(OUT, 'fig8-4.svg'))


def fig8_5():  #Agent Self-Evolution Pipeline (Requirement Identification → Tool Search → Code Encapsulation → Tool Registration)
    _pipeline([("① Identifikasi Kebutuhan", "Alat yang ada tidak mencukupi"), ("② Pencarian Alat", "Pencarian dunia terbuka"),
               ("③ Enkapsulasi Kode", "Hasilkan dan enkapsulasi"), ("④ Registrasi Alat", "Gabungkan ke dalam pustaka untuk digunakan kembali")],
              'fig8-5', feedback="Alat yang baru terdaftar dapat digunakan kembali oleh tugas berikutnya, terus memperluas batas kemampuan")


def fig8_6():  #Voyager Continuous Learning Architecture (Curriculum Generator + Skill Library + Iterative Prompting)
    _pipeline([("Generator Kurikulum", "Usulkan tugas baru yang progresif"), ("Mekanisme Prompting Iteratif", "Hasilkan dan debug kode keahlian"),
               ("Pustaka Keahlian", "Simpan keahlian yang dapat digunakan kembali")],
              'fig8-6', W=760, feedback="Akumulasi keahlian membuka kunci tugas yang lebih sulit (eksplorasi dunia terbuka)")


def fig8_7():  #Experiment 8-5 Self-Evolution Pipeline (Search → Evaluate → Test → Encapsulate → Reuse)
    _pipeline([("① Pencarian", "Temukan alat di jaringan terbuka"), ("② Evaluasi", "Tentukan kesesuaian"), ("③ Uji", "Verifikasi kegunaan"),
               ("④ Kemas", "Bungkus menjadi alat standar"), ("⑤ Gunakan Kembali", "Sertakan dalam pustaka alat")],
              'fig8-7', W=940, feedback="Alat baru diakumulasikan untuk digunakan kembali di tugas berikutnya")


if __name__ == '__main__':
    for fn in (fig8_1, fig8_2, fig8_3, fig8_4, fig8_5, fig8_6, fig8_7):
        fn()
        print('saved', fn.__name__)
