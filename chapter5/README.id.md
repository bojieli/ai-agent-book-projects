# Bab 5 · Coding Agent dan Pembuatan Kode

> Kode adalah “tool yang dapat menciptakan tool baru” dan menjadi meta-kemampuan Agent serbaguna.

← [Kembali ke README utama](../docs/id/README.md) · 📖 [Baca bab](../book-id/chapter5.md)

## Cara Membaca Eksperimen

Teks utama memakai skeleton mekanisme singkat untuk menjelaskan alur kontrol; direktori eksperimen berisi adapter SDK lengkap, log, pengujian, dan bukti penerimaan. Anda tidak perlu membaca setiap berkas baris demi baris.

- **Starter:** Mulai dari tujuan, perintah minimum, dan syarat penerimaan; awali dengan [coding-agent](coding-agent/);
- **Builder:** Telusuri titik masuk, loop inti, skema status/pesan, alat, dan verifier.
- **Maintainer:** Terakhir, baca pengujian, manifest bukti, penanganan kegagalan, rollback, dan adapter provider.

Pada pembacaan pertama, lewati kredensial, presentasi, dan kompatibilitas provider; kembali saat mereproduksi angka.

## Proyek Pendamping

| Eksperimen | Proyek | Jenis | Deskripsi |
| :--: | --- | :--: | --- |
| 5-1 | [code-for-math](code-for-math/) | ✅ | Membandingkan chain-of-thought murni dengan perhitungan berbantuan kode. |
| 5-2 | [code-for-logic](code-for-logic/) | ✅ | Mengubah teka-teki logika menjadi Constraint Satisfaction Problem. |
| 5-3 | [small-model-codified-rules](small-model-codified-rules/) | ✅ | Memindahkan kebijakan bisnis ke validasi kode agar model kecil lebih patuh. |
| 5-4 | [paper-to-ppt](paper-to-ppt/) | ✅ | Menghasilkan presentasi Slidev melalui loop Proposer dan Reviewer visual. |
| 5-5 | [paper-to-video](paper-to-video/) | ✅ | Mengubah presentasi menjadi video bernarasi menggunakan TTS dan ffmpeg. |
| 5-6 | [video-edit](video-edit/) | ✅ | Menemukan dan memotong adegan video berdasarkan permintaan bahasa alami. |
| 5-7 | [cad-vs-diffusion](cad-vs-diffusion/) | ✅ | Pengujian nyata dua rute pada spesifikasi flange yang sama: CadQuery 17 baris dari Kimi menunjukkan deviasi nol untuk semua dimensi; Hunyuan3D-2.1 (HF Space publik) kehilangan 4 lubang tembus dan menyimpang −99.4% pada diameter luar. Perubahan M5→M6: rute kode mengubah satu baris parameter, 0 panggilan LLM, nol drift; rute generatif menjalankan ulang seluruhnya dengan +283% drift dan pembalikan aksial. Kontrol tanaman: kealamian 3 vs 8, batas penerapan terbalik. |
| 5-8 | [adaptive-log-parser](adaptive-log-parser/) | ✅ | Membuat parser baru secara otomatis saat format log yang belum dikenal muncul. |
| 5-9 | [log-diagnosis](log-diagnosis/) | ✅ | Mendiagnosis trajectory HTTP, memutar ulang regresi, dan membuat Issue terverifikasi. |
| 5-10 | [dynamic-form](dynamic-form/) | ✅ | Menghasilkan formulir HTML dinamis untuk mengklarifikasi permintaan yang belum lengkap. |
| 5-11 | [erp-agent](erp-agent/) | ✅ | Menghasilkan artefak SQL untuk kueri ERP tanpa memindahkan seluruh data melalui LLM. |
| 5-12 | [conversational-ui](conversational-ui/) | ✅ | Memodifikasi UI React berdasarkan bahasa alami dan menerapkan perubahan dengan HMR. |
| 5-13 | [permission-embedded-data-objects](permission-embedded-data-objects/) | ✅ | Penyimpanan objek berbasis PostgreSQL yang menegakkan otorisasi, validasi, dan integritas referensial di bawah kode aplikasi yang dibuat secara dinamis. |
| 5-14 | [agent-creator](agent-creator/) | ✅ | Membandingkan pembuatan Agent dari referensi tervalidasi dengan pembuatan dari nol. |

## Jenis Proyek

| Ikon | Jenis | Arti |
| :--: | --- | --- |
| ✅ | **Mandiri** | Kode lengkap tersedia di repositori dan dapat dijalankan setelah API Key dikonfigurasi. |
| 📖 | **Panduan Reproduksi** | Memerlukan repositori eksternal yang harus di-`git clone`. |
| 🚧 | **Dalam Proses** | Implementasi atau bukti penerimaan belum lengkap. |
