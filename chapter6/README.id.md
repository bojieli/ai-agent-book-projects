# Bab 6 · Interaksi: Perluasan Ruang Observasi dan Ruang Aksi

> Memperluas persepsi dan tindakan dari teks ke suara, GUI, dan dunia fisik: streaming speech, Computer Use, serta robotika.

← [Kembali ke README utama](../docs/id/README.md) · 📖 [Baca bab](../book-id/chapter6.md)

## Cara Membaca Eksperimen

Teks utama memakai skeleton mekanisme singkat untuk menjelaskan alur kontrol; direktori eksperimen berisi adapter SDK lengkap, log, pengujian, dan bukti penerimaan. Anda tidak perlu membaca setiap berkas baris demi baris.

- **Starter:** Mulai dari tujuan, perintah minimum, dan syarat penerimaan; awali dengan [live-audio](live-audio/);
- **Builder:** Telusuri titik masuk, loop inti, skema status/pesan, alat, dan verifier.
- **Maintainer:** Terakhir, baca pengujian, manifest bukti, penanganan kegagalan, rollback, dan adapter provider.

Pada pembacaan pertama, lewati kredensial, presentasi, dan kompatibilitas provider; kembali saat mereproduksi angka.

## Proyek Pendamping

| Eksperimen | Proyek | Jenis | Deskripsi |
| :--: | --- | :--: | --- |
| 6-1 | [agent-with-event-trigger](agent-with-event-trigger/) | ✅ | Membangun Agent event-driven berbasis FastAPI dengan sumber event majemuk. |
| 6-2 | [async-agent](async-agent/) | ✅ | Mengimplementasikan queue event, prioritas, tool paralel, interupsi, pembatalan, dan status tugas. |
| 6-3 | [live-audio](live-audio/) | ✅ | Demo percakapan suara real-time yang menggabungkan STT, dialog AI, dan TTS. |
| Add-on | [phone-agent](phone-agent/) | 🚧 | Jalur Pine Voice tersedia, tetapi panggilan PSTN berizin belum dijalankan. |
| 6-4 | [streaming-speech](streaming-speech/) | ✅ | Menunjukkan trade-off latensi dan akurasi pada pengenalan suara streaming. |
| 6-5 | [end-to-end-speech](end-to-end-speech/) | ✅ | MiniCPM-o 4.5 pada revision tetap dijalankan secara lokal di satu RTX PRO 6000; end-to-end dan self-cascade sama-sama 3/4 dengan kegagalan semantik/paralinguistik yang saling melengkapi, serta bukti audio 24kHz nyata. |
| 6-6 | [controllable-tts](controllable-tts/) | 🚧 | Menyiapkan pustaka referensi Fish Audio dan perbandingan media; evaluasi dengar belum lengkap. |
| 6-7 | `claude-quickstarts/computer-use-demo/` | 📖 | Demo Computer Use resmi Anthropic pada desktop Ubuntu terkontainerisasi. |
| 6-8 | `browser-use/` | 📖 | Otomatisasi browser visual dengan trajectory tindakan dan screenshot. |
| 6-9 | [xlerobot-teleoperation](xlerobot-teleoperation/) | 📖 | Teleoperasi XLeRobot nyata untuk satu tugas merapikan meja: masukkan cangkir merah ke nampan, kertas kuning ke tempat sampah, lalu amati dan verifikasi keadaan akhir. |
| 6-10 | [gemini-xlerobot-navigation](gemini-xlerobot-navigation/) | 📖 | Mengukur batas atas kontrol ideal untuk tugas meja yang sama di simulator; bukan klaim bahwa robot nyata telah dijalankan. |
| 6-11 | [gemini-xlerobot-navigation](gemini-xlerobot-navigation/) | 📖 | Gemini Robotics-ER 1.5 mengendalikan XLeRobot nyata secara otonom untuk tugas meja yang sama. |
| 6-12 | [gemini-xlerobot-navigation](gemini-xlerobot-navigation/) | 📖 | Membandingkan strategi open-loop, pemeriksaan bertahap, dan closed-loop prediktif di simulator untuk tugas yang sama. |
| 6-13 | [rgb-sim2real-grasping](rgb-sim2real-grasping/) | 📖 | Uji RGB lintas lingkungan untuk tugas meja yang sama dengan variasi latar, tampilan objek, pencahayaan, dan noise visual. |

## Jenis Proyek

| Ikon | Jenis | Arti |
| :--: | --- | --- |
| ✅ | **Mandiri** | Kode lengkap tersedia di repositori dan dapat dijalankan setelah API Key dikonfigurasi. |
| 📖 | **Panduan Reproduksi** | Memerlukan repositori eksternal yang harus di-`git clone` atau perangkat keras tertentu. |
| 🚧 | **Dalam Proses** | Implementasi atau bukti penerimaan live belum lengkap. |
