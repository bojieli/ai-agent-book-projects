# Bab 9 · Interaksi Multimodal dan Real-Time

> Memperluas persepsi dan tindakan dari teks ke suara, GUI, dan dunia fisik: streaming speech, Computer Use, serta robotika.

← [Kembali ke README utama](../docs/id/README.md) · 📖 [Baca bab](../book-id/chapter9.md)

## Proyek Pendamping

| Eksperimen | Proyek | Jenis | Deskripsi |
| :--: | --- | :--: | --- |
| 9-1 | [live-audio](live-audio/) | ✅ | Demo percakapan suara real-time yang menggabungkan STT, dialog AI, dan TTS. |
| 9-2 | [phone-agent](phone-agent/) | 🚧 | Jalur Pine Voice tersedia, tetapi panggilan PSTN berizin belum dijalankan. |
| 9-3 | [streaming-speech](streaming-speech/) | ✅ | Menunjukkan trade-off latensi dan akurasi pada pengenalan suara streaming. |
| 9-4 | [end-to-end-speech](end-to-end-speech/) | 🚧 | Client Step-Audio R1 tersedia, tetapi endpoint dan CUDA belum tersedia pada host validasi. |
| 9-5 | [controllable-tts](controllable-tts/) | 🚧 | Menyiapkan pustaka referensi Fish Audio dan perbandingan media; evaluasi dengar belum lengkap. |
| 9-6 | `claude-quickstarts/computer-use-demo/` | 📖 | Demo Computer Use resmi Anthropic pada desktop Ubuntu terkontainerisasi. |
| 9-7 | `browser-use/` | 📖 | Otomatisasi browser visual dengan trajectory tindakan dan screenshot. |
| 9-8 | [xlerobot-teleoperation](xlerobot-teleoperation/) | 📖 | Jalur teleoperasi XLeRobot; penerimaan memerlukan perangkat keras yang diotorisasi. |
| 9-9 | [gemini-xlerobot-navigation](gemini-xlerobot-navigation/) | 📖 | Navigasi XLeRobot dengan Gemini Robotics-ER dan RoboCrew. |
| 9-10 | [rgb-sim2real-grasping](rgb-sim2real-grasping/) | 📖 | Pipeline RGB-to-PPO-to-SO-100 untuk zero-shot Sim2Real grasping. |

## Jenis Proyek

| Ikon | Jenis | Arti |
| :--: | --- | --- |
| ✅ | **Mandiri** | Kode lengkap tersedia di repositori dan dapat dijalankan setelah API Key dikonfigurasi. |
| 📖 | **Panduan Reproduksi** | Memerlukan repositori eksternal yang harus di-`git clone` atau perangkat keras tertentu. |
| 🚧 | **Dalam Proses** | Implementasi atau bukti penerimaan live belum lengkap. |
