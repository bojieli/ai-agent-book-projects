# Bab 7 · Evaluasi Agent

> Mengubah performa menjadi sinyal yang dapat dibandingkan melalui lingkungan evaluasi, dataset, metrik, observabilitas, dan pemilihan berbasis evaluasi.

← [Kembali ke README utama](../docs/id/README.md) · 📖 [Baca bab](../book-id/chapter7.md)

## Cara Membaca Eksperimen

Teks utama memakai skeleton mekanisme singkat untuk menjelaskan alur kontrol; direktori eksperimen berisi adapter SDK lengkap, log, pengujian, dan bukti penerimaan. Anda tidak perlu membaca setiap berkas baris demi baris.

- **Starter:** Mulai dari tujuan, perintah minimum, dan syarat penerimaan; awali dengan [tau2-bench-eval](tau2-bench-eval/);
- **Builder:** Telusuri titik masuk, loop inti, skema status/pesan, alat, dan verifier.
- **Maintainer:** Terakhir, baca pengujian, manifest bukti, penanganan kegagalan, rollback, dan adapter provider.

Pada pembacaan pertama, lewati kredensial, presentasi, dan kompatibilitas provider; kembali saat mereproduksi angka.

## Proyek Pendamping

| Eksperimen | Proyek | Jenis | Deskripsi |
| :--: | --- | :--: | --- |
| 7-1 | `tau2-bench/` | 📖 | Menjalankan evaluasi multi-putaran dual-control τ²-bench dan membandingkannya dengan τ-bench. |
| 7-2 | `tau2-bench/` | 📖 | Menyelesaikan sampel tugas τ²-bench secara manual dan mencatat trajectory. |
| 7-2 | `terminal-bench/` | 📖 | Menguji tugas end-to-end pada lingkungan terminal nyata. |
| 7-2 | `SWE-bench/` | 📖 | Mengevaluasi penyelesaian Issue GitHub nyata dengan patch yang dapat diuji. |
| 7-2 | `GAIA/` | 📖 | Mengevaluasi pencarian, penggunaan tool, dan otonomi pada soal bertingkat. |
| 7-2 | `OSWorld/` | 📖 | Mengevaluasi operasi file, aplikasi, dan konfigurasi pada lingkungan OS lengkap. |
| 7-2, 7-12 | `android_world/` | 📖 | Mengevaluasi navigasi aplikasi dan interaksi UI pada Android. |
| 7-3 | [user-memory-evaluation](../chapter3/user-memory-evaluation/) | ✅ | Menjalankan Rubric memori multi-dimensi dengan bukti untuk setiap penilaian. |
| 7-4 | [user-memory-system-evaluation](user-memory-system-evaluation/) | ✅ | Membandingkan JSON Cards, RAG, dan sistem hibrida pada kumpulan kasus yang sama. |
| 7-5 | [user-memory-policy-eval](user-memory-policy-eval/) | ✅ | Menjalankan 11 kasus buruk awalan trajectory pada representasi memori JSON, Markdown, dan bergaya Python dengan panggilan OpenRouter nyata serta pemeriksaan kebijakan deterministik. |
| 7-6 | [tts-quality-eval](tts-quality-eval/) | ✅ | Membandingkan konfigurasi TTS menggunakan LLM multimodal sebagai juri berbasis Rubric. |
| 7-7 | [elo-leaderboard](elo-leaderboard/) | ✅ | Membuat papan peringkat Agent berdasarkan perbandingan berpasangan dan rating ELO. |
| 7-8 | [model-action-threshold](model-action-threshold/) | ✅ | Membandingkan GPT-5.6-sol dan Claude Sonnet 5 saat beralih dari eksplorasi ke edit pertama di bawah Coding Harness netral yang sama; seluruh 18/18 sel selesai tanpa error API, dan [manifest](model-action-threshold/results/exp7-8-action-threshold-20260731-v1/manifest.json) mengikat trajectory serta ringkasan dengan hash yang dapat diverifikasi. |
| 7-9 | [agent-cost-analysis](agent-cost-analysis/) | ✅ | Mengurai biaya end-to-end dan mengukur penghematan desain ramah cache serta kompresi. |
| 7-10 | [model-benchmark](model-benchmark/) | 🚧 | Mengukur TTFT, latensi, throughput, reliabilitas, dan biaya model; kampanye panjang belum selesai. |
| 7-11 | [user-memory-system-evaluation](user-memory-system-evaluation/) | ✅ | Matriks penuh 4×3×2×60 menyimpan 1.440/1.440 trajectory nyata tanpa error atau penggunaan tanpa harga, lengkap dengan metrik retrieval dan tugas, analisis interaksi, serta verifikator independen yang lulus. |
| 7-12 | [android-world](android-world/) | 📖 | Laporan evaluasi T3A dan analisis kegagalan AndroidWorld di dalam repositori. |
| 7-13 | [openvla-robotwin2-eval](openvla-robotwin2-eval/) | ✅ | Kampanye resmi satu GPU menyelesaikan 256 episode per lengan; chunk 1 mendapat 0/256 dan chunk 25 mendapat 26/256, dengan hash untuk seluruh 512 rollout. |
| — | [public-health-reporting-eval](public-health-reporting-eval/) | ✅ | Mengevaluasi panggilan tool, kalkulasi, sitasi, dan klaim laporan kesehatan publik. |

> Benchmark dengan nama berformat kode harus dikloning secara terpisah. `android-world/` adalah catatan analisis lokal, bukan sumber benchmark `android_world/`.

## Jenis Proyek

| Ikon | Jenis | Arti |
| :--: | --- | --- |
| ✅ | **Mandiri** | Kode lengkap tersedia di repositori dan dapat dijalankan setelah API Key dikonfigurasi. |
| 📖 | **Panduan Reproduksi** | Memerlukan repositori eksternal yang harus di-`git clone`. |
| 🚧 | **Dalam Proses** | Implementasi atau bukti penerimaan belum lengkap. |
