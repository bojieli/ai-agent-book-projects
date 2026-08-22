# Bab 9 · Evolusi Berkelanjutan Agent

> Membantu Agent berkembang dari pengalaman: memverifikasi trajectory, menyuling pengetahuan, memperbaiki prompt, membuat workflow, dan memodifikasi diri secara terkendali.

← [Kembali ke README utama](../docs/id/README.md) · 📖 [Baca bab](../book-id/chapter9.md)

## Cara Membaca Eksperimen

Teks utama memakai skeleton mekanisme singkat untuk menjelaskan alur kontrol; direktori eksperimen berisi adapter SDK lengkap, log, pengujian, dan bukti penerimaan. Anda tidak perlu membaca setiap berkas baris demi baris.

- **Starter:** Mulai dari tujuan, perintah minimum, dan syarat penerimaan; awali dengan [trajectory-verifier](trajectory-verifier/);
- **Builder:** Telusuri titik masuk, loop inti, skema status/pesan, alat, dan verifier.
- **Maintainer:** Terakhir, baca pengujian, manifest bukti, penanganan kegagalan, rollback, dan adapter provider.

Pada pembacaan pertama, lewati kredensial, presentasi, dan kompatibilitas provider; kembali saat mereproduksi angka.

## Proyek Pendamping

| Eksperimen | Proyek | Jenis | Deskripsi |
| :--: | --- | :--: | --- |
| 9-1 | [trajectory-verifier](trajectory-verifier/) | ✅ | Menggabungkan hasil lingkungan, aturan proses, dan Rubric menjadi diagnosis berbasis bukti. |
| 9-2 | [gaia-experience](gaia-experience/) | ✅ | Membandingkan trajectory sukses, parsial, dan gagal untuk membuat dokumen pengalaman. |
| 9-3 | [prompt-auto-optimization](prompt-auto-optimization/) | ✅ | Menghasilkan patch prompt minimal dan mengendalikan rilis dengan set batas serta retensi. |
| 9-4 | Eksperimen dalam teks | 🚧 | Eksperimen 9-4: mengembangkan Skill "klarifikasi kebutuhan + konfirmasi Spec" dari umpan balik pengguna; teks utama memberikan desain A/B tiga lengan, metrik, dan gerbang rilis, sedangkan implementasi pendampingnya belum tersedia |
| 9-5 | [browser-use-rpa](browser-use-rpa/) | ✅ | Mengompilasi trajectory browser menjadi workflow yang diverifikasi melalui reset dan replay. |
| 9-6 | [self-modifying-agent](self-modifying-agent/) | ✅ | Memicu patch kode setelah kegagalan berulang, lalu melakukan regresi, canary, dan rollback. |
| 9-7 | [harness-safety-gate](harness-safety-gate/) | ✅ | Gerbang konfirmasi operasi berisiko tinggi |
| 9-8 | [hermes-self-evolution](hermes-self-evolution/) | 📖 | Memberi Hermes seluruh buku dan source-nya sendiri; ia memilih peningkatan, mengubah dirinya, dan menjadikan tiap penolakan Reviewer sebagai putaran belajar baru sampai diterima. |
| 9-9 | [self-evolution-eval](self-evolution-eval/) | ✅ | Eksperimen 9-9 mengevaluasi pembelajaran, transfer, perubahan aturan, dan retensi jangka panjang. |

Semua eksperimen menyediakan entry point offline dan unit test tanpa API Key; jalur yang membutuhkan model nyata atau browser dijelaskan dalam README proyek.

## Kasus Pelengkap

| Eksperimen | Proyek | Keterkaitan |
| :--: | --- | --- |
| 8-8 | [prompt-distillation](../chapter8/prompt-distillation/) | Proyek lintas bab tentang distilasi prompt dan pembelajaran terparameter; metode pelatihannya termasuk Bab 8 |
| — | [self-evolving-tools](self-evolving-tools/) | Penemuan, enkapsulasi, dan penggunaan ulang alat ala Alita — kasus pelengkap dari "menulis pengalaman menjadi program" |
| — | [ai-style-skill](ai-style-skill/) | Mengubah umpan balik tulisan menjadi Skill yang dapat diverifikasi; bab ini menghubungkan Skill tanda kutip lengkung dengan data sintetis yang diaudit dan post-training, serta memisahkan kegagalan tokenizer/Harness pada penyalinan eksak |

## Jenis Proyek

| Ikon | Jenis | Arti |
| :--: | --- | --- |
| ✅ | **Mandiri** | Kode lengkap tersedia di repositori dan dapat dijalankan setelah API Key dikonfigurasi. |
| 📖 | **Panduan Reproduksi** | Memerlukan repositori eksternal yang harus di-`git clone`. |
| 🚧 | **Dalam Proses** | Implementasi atau bukti penerimaan belum lengkap. |
