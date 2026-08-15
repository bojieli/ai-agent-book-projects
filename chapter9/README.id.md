# Bab 8 · Evolusi Berkelanjutan Agent

> Membantu Agent berkembang dari pengalaman: memverifikasi trajectory, menyuling pengetahuan, memperbaiki prompt, membuat workflow, dan memodifikasi diri secara terkendali.

← [Kembali ke README utama](../docs/id/README.md) · 📖 [Baca bab](../book-id/chapter8.md)

## Cara Membaca Eksperimen

Teks utama memakai skeleton mekanisme singkat untuk menjelaskan alur kontrol; direktori eksperimen berisi adapter SDK lengkap, log, pengujian, dan bukti penerimaan. Anda tidak perlu membaca setiap berkas baris demi baris.

- **Starter:** Mulai dari tujuan, perintah minimum, dan syarat penerimaan; awali dengan [trajectory-verifier](trajectory-verifier/);
- **Builder:** Telusuri titik masuk, loop inti, skema status/pesan, alat, dan verifier.
- **Maintainer:** Terakhir, baca pengujian, manifest bukti, penanganan kegagalan, rollback, dan adapter provider.

Pada pembacaan pertama, lewati kredensial, presentasi, dan kompatibilitas provider; kembali saat mereproduksi angka.

## Proyek Pendamping

| Eksperimen | Proyek | Jenis | Deskripsi |
| :--: | --- | :--: | --- |
| 8-1 | [trajectory-verifier](trajectory-verifier/) | ✅ | Menggabungkan hasil lingkungan, aturan proses, dan Rubric menjadi diagnosis berbasis bukti. |
| 8-2 | [gaia-experience](gaia-experience/) | ✅ | Membandingkan trajectory sukses, parsial, dan gagal untuk membuat dokumen pengalaman. |
| 8-3 | [prompt-auto-optimization](prompt-auto-optimization/) | ✅ | Menghasilkan patch prompt minimal dan mengendalikan rilis dengan set batas serta retensi. |
| 8-4 | [browser-use-rpa](browser-use-rpa/) | ✅ | Mengompilasi trajectory browser menjadi workflow yang diverifikasi melalui reset dan replay. |
| 8-5 | [self-modifying-agent](self-modifying-agent/) | ✅ | Memicu patch kode setelah kegagalan berulang, lalu melakukan regresi, canary, dan rollback. |
| 8-6 | [hermes-self-evolution](hermes-self-evolution/) | 📖 | Memberi Hermes seluruh buku dan source-nya sendiri; ia memilih peningkatan, mengubah dirinya, dan menjadikan tiap penolakan Reviewer sebagai putaran belajar baru sampai diterima. |
| 8-7 | [self-evolution-eval](self-evolution-eval/) | ✅ | Eksperimen 8-7 mengevaluasi pembelajaran, transfer, perubahan aturan, dan retensi jangka panjang. |
| 8-8 | [harness-safety-gate](harness-safety-gate/) | ✅ | Gerbang konfirmasi operasi berisiko tinggi |
| 8-9 | [ai-style-skill](ai-style-skill/) | ✅ | Mengubah umpan balik tulisan menjadi Skill yang dapat diverifikasi; bab ini menghubungkan Skill tanda kutip lengkung dengan data sintetis yang diaudit dan post-training, serta memisahkan kegagalan tokenizer/Harness pada penyalinan eksak |

Semua eksperimen menyediakan entry point offline dan unit test tanpa API Key; jalur yang membutuhkan model nyata atau browser dijelaskan dalam README proyek.

## Jenis Proyek

| Ikon | Jenis | Arti |
| :--: | --- | --- |
| ✅ | **Mandiri** | Kode lengkap tersedia di repositori dan dapat dijalankan setelah API Key dikonfigurasi. |
| 📖 | **Panduan Reproduksi** | Memerlukan repositori eksternal yang harus di-`git clone`. |
| 🚧 | **Dalam Proses** | Implementasi atau bukti penerimaan belum lengkap. |
