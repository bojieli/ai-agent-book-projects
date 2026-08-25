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
| 7-2, 7-13 | `android_world/` | 📖 | Mengevaluasi navigasi aplikasi dan interaksi UI pada Android. |
| 7-3 | [user-memory-evaluation](../chapter3/user-memory-evaluation/) | ✅ | Menjalankan Rubric memori multi-dimensi dengan bukti untuk setiap penilaian. |
| 7-4 | [user-memory-system-evaluation](user-memory-system-evaluation/) | ✅ | Membandingkan JSON Cards, RAG, dan sistem hibrida pada kumpulan kasus yang sama. |
| 7-5 | [tts-quality-eval](tts-quality-eval/) | ✅ | Membandingkan konfigurasi TTS menggunakan LLM multimodal sebagai juri berbasis Rubric. |
| 7-6 | [android-world/failure-attribution](android-world/failure-attribution/) | ✅ | Offline failure attribution over the retained T3A log. Population, recomputed from the raw log: 53 task blocks, 1 skipped by the benchmark's own `initialize_task` crash, 52 real failures; 24/52 ended with the Agent declaring completion; 9 failures have goals requiring the current date and only 2 ever obtain it (incidentally, from a form default showing `Sun, Oct 15`); the self-reported "no visible effect" family occurs 55 times across 18/52 episodes. Ten episodes annotated with build-verified step-level citations — 9 silent failures, 7 of 10 first errors on an assistant message, 5 high / 4 medium / 1 low confidence. Third pass: the second moved 7 of 10 first-error steps earlier, the third corrected two population statistics and one record's description, every change retained with its rationale. Includes 3 trajectory-prefix regression tasks and 3 corrections to `t3a_failed_analysis.md` |
| 7-7 | [user-memory-policy-eval](user-memory-policy-eval/) | ✅ | Menjalankan 11 kasus buruk awalan trajectory pada representasi memori JSON, Markdown, dan bergaya Python dengan panggilan OpenRouter nyata serta pemeriksaan kebijakan deterministik. |
| 7-8 | [elo-leaderboard](elo-leaderboard/) | ✅ | Membuat papan peringkat Agent berdasarkan perbandingan berpasangan dan rating ELO. |
| 7-9 | [model-action-threshold](model-action-threshold/) | ✅ | Membandingkan GPT-5.6-sol dan Claude Sonnet 5 saat beralih dari eksplorasi ke edit pertama di bawah Coding Harness netral yang sama; seluruh 18/18 sel selesai tanpa error API, dan [manifest](model-action-threshold/results/exp7-8-action-threshold-20260731-v1/manifest.json) mengikat trajectory serta ringkasan dengan hash yang dapat diverifikasi. |
| 7-10 | [agent-cost-analysis](agent-cost-analysis/) | ✅ | Mengurai biaya end-to-end dan mengukur penghematan desain ramah cache serta kompresi. |
| 7-11 | [model-benchmark](model-benchmark/) | 🚧 | Mengukur TTFT, latensi, throughput, reliabilitas, dan biaya model; kampanye panjang belum selesai. |
| 7-12 | [user-memory-system-evaluation](user-memory-system-evaluation/) | ✅ | Matriks penuh 4×3×2×60 menyimpan 1.440/1.440 trajectory nyata tanpa error atau penggunaan tanpa harga, lengkap dengan metrik retrieval dan tugas, analisis interaksi, serta verifikator independen yang lulus. |
| 7-13 | [android-world](android-world/) | 📖 | Laporan evaluasi T3A dan analisis kegagalan AndroidWorld di dalam repositori. |
| 7-14 | [openvla-robotwin2-eval](openvla-robotwin2-eval/) | ✅ | Kampanye resmi satu GPU menyelesaikan 256 episode per lengan; chunk 1 mendapat 0/256 dan chunk 25 mendapat 26/256, dengan hash untuk seluruh 512 rollout. |
| — | [public-health-reporting-eval](public-health-reporting-eval/) | ✅ | Mengevaluasi panggilan tool, kalkulasi, sitasi, dan klaim laporan kesehatan publik. |

> Benchmark dengan nama berformat kode harus dikloning secara terpisah. `android-world/` adalah catatan analisis lokal, bukan sumber benchmark `android_world/`.

## Jenis Proyek

| Ikon | Jenis | Arti |
| :--: | --- | --- |
| ✅ | **Mandiri** | Kode lengkap tersedia di repositori dan dapat dijalankan setelah API Key dikonfigurasi. |
| 📖 | **Panduan Reproduksi** | Memerlukan repositori eksternal yang harus di-`git clone`. |
| 🚧 | **Dalam Proses** | Implementasi atau bukti penerimaan belum lengkap. |
