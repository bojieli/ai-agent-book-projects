# Bab 1 · Dasar-Dasar Agent

> Memulai dari paradigma “Model sebagai Agent”, membangun rumus inti **Agent = LLM + Context + Tool**, dan memperkenalkan rekayasa Harness sebagai keunggulan di luar model.

← [Kembali ke README utama](../docs/id/README.md) · 📖 [Baca bab](../book-id/chapter1.md)

## Cara Membaca Eksperimen

Teks utama memakai skeleton mekanisme singkat untuk menjelaskan alur kontrol; direktori eksperimen berisi adapter SDK lengkap, log, pengujian, dan bukti penerimaan. Anda tidak perlu membaca setiap berkas baris demi baris.

- **Starter:** Mulai dari tujuan, perintah minimum, dan syarat penerimaan; awali dengan [context](context/);
- **Builder:** Telusuri titik masuk, loop inti, skema status/pesan, alat, dan verifier.
- **Maintainer:** Terakhir, baca pengujian, manifest bukti, penanganan kegagalan, rollback, dan adapter provider.

Pada pembacaan pertama, lewati kredensial, presentasi, dan kompatibilitas provider; kembali saat mereproduksi angka.

## Proyek Pendamping

| Eksperimen | Proyek | Jenis | Deskripsi |
| :--: | --- | :--: | --- |
| 1-1 | [context](context/) | ✅ | Menunjukkan pentingnya komponen context melalui eksperimen ablasi pada beberapa penyedia LLM. |
| 1-2 | [web-search-agent](web-search-agent/) | ✅ | Menerapkan Agent pencarian mendalam dasar dengan pencarian multi-putaran dan integrasi informasi. |
| 1-3 | [search-codegen](search-codegen/) | ✅ | Menggabungkan pencarian web dan sandbox kode untuk analisis yang lebih kompleks. |
| 1-4 | [image-gen-workflow](image-gen-workflow/) | ✅ | Perbandingan nyata dua rute antara kebutuhan konkret/luas × workflow (penulisan ulang kimi-k3 + Tongyi Wanxiang) vs. asli (Gemini / GPT-Image 2): untuk kebutuhan konkret rute asli lebih setia (teks poster dibuang ke prompt negatif oleh node penulisan ulang); untuk kebutuhan luas, konkretisasi adegan menambah imajinasi, tetapi GPT-Image 2 bisa memberikan sudut pandang sendiri—bukti empiris bahwa lapisan adapter diinternalisasi model |
| 7-1, 7-2 | [learning-from-experience](learning-from-experience/) | ✅ | Membandingkan Q-learning dengan in-context learning berbasis LLM pada permainan pencarian harta karun. |

## Jenis Proyek

| Ikon | Jenis | Arti |
| :--: | --- | --- |
| ✅ | **Mandiri** | Kode lengkap tersedia di repositori dan dapat dijalankan setelah API Key dikonfigurasi. |
| 📖 | **Panduan Reproduksi** | Memerlukan repositori eksternal yang harus di-`git clone`. |
| 🚧 | **Dalam Proses** | Implementasi atau bukti penerimaan belum lengkap. |
