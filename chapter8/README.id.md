# Bab 8 · Evolusi Berkelanjutan Agent

> Membantu Agent berkembang dari pengalaman: memverifikasi trajectory, menyuling pengetahuan, memperbaiki prompt, membuat workflow, dan memodifikasi diri secara terkendali.

← [Kembali ke README utama](../docs/id/README.md) · 📖 [Baca bab](../book-id/chapter8.md)

## Proyek Pendamping

| Eksperimen | Proyek | Jenis | Deskripsi |
| :--: | --- | :--: | --- |
| 8-1 | [trajectory-verifier](trajectory-verifier/) | ✅ | Menggabungkan hasil lingkungan, aturan proses, dan Rubric menjadi diagnosis berbasis bukti. |
| 8-2 | [gaia-experience](gaia-experience/) | ✅ | Membandingkan trajectory sukses, parsial, dan gagal untuk membuat dokumen pengalaman. |
| 8-3 | [prompt-auto-optimization](prompt-auto-optimization/) | ✅ | Menghasilkan patch prompt minimal dan mengendalikan rilis dengan set batas serta retensi. |
| 8-4 | Eksperimen teks | 🚧 | Eksperimen 8-4: mengembangkan Skill klarifikasi kebutuhan dari umpan balik pengguna |
| 8-5 | [browser-use-rpa](browser-use-rpa/) | ✅ | Eksperimen 8-5: mengompilasi trajectory browser menjadi workflow |
| 8-6 | [self-modifying-agent](self-modifying-agent/) | ✅ | Eksperimen 8-6: memicu patch kode setelah kegagalan berulang, lalu melakukan regresi dan canary |
| 8-7 | [harness-safety-gate](harness-safety-gate/) | ✅ | Eksperimen 8-7: gerbang konfirmasi operasi berisiko tinggi |
| 8-8 | [hermes-self-evolution](hermes-self-evolution/) | 📖 | Eksperimen 8-8: memberi Hermes seluruh buku dan source-nya sendiri untuk evolusi diri |
| 8-9 | [self-evolution-eval](self-evolution-eval/) | ✅ | Eksperimen 8-9: mengevaluasi pembelajaran, transfer, perubahan aturan, dan retensi jangka panjang |

Semua eksperimen menyediakan entry point offline dan unit test tanpa API Key; jalur yang membutuhkan model nyata atau browser dijelaskan dalam README proyek.
## Kasus Pelengkap

| Eksperimen | Proyek | Hubungan |
| :--: | --- | --- |
| 7-8 | [prompt-distillation](prompt-distillation/) | Proyek lintas bab tentang distilasi prompt (Bab 7) |
| — | [self-evolving-tools](self-evolving-tools/) | Penemuan dan penggunaan kembali alat bergaya Alita |
| — | [ai-style-skill](ai-style-skill/) | Kasus pelengkap Skill penulisan; contoh utama ada di Bab 2 |


## Jenis Proyek

| Ikon | Jenis | Arti |
| :--: | --- | --- |
| ✅ | **Mandiri** | Kode lengkap tersedia di repositori dan dapat dijalankan setelah API Key dikonfigurasi. |
| 📖 | **Panduan Reproduksi** | Memerlukan repositori eksternal yang harus di-`git clone`. |
| 🚧 | **Dalam Proses** | Implementasi atau bukti penerimaan belum lengkap. |
