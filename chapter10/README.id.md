# Bab 10 · Kolaborasi Multi-Agent

> Membahas kapan kecerdasan kolektif mengungguli satu Agent, pola koordinasi, berbagi atau mengisolasi context, mode kegagalan, dan masyarakat Agent.

← [Kembali ke README utama](../docs/id/README.md) · 📖 [Baca bab](../book-id/chapter10.md)

## Cara Membaca Eksperimen

Teks utama memakai skeleton mekanisme singkat untuk menjelaskan alur kontrol; direktori eksperimen berisi adapter SDK lengkap, log, pengujian, dan bukti penerimaan. Anda tidak perlu membaca setiap berkas baris demi baris.

- **Starter:** Mulai dari tujuan, perintah minimum, dan syarat penerimaan; awali dengan [parallel-web-research](parallel-web-research/);
- **Builder:** Telusuri titik masuk, loop inti, skema status/pesan, alat, dan verifier.
- **Maintainer:** Terakhir, baca pengujian, manifest bukti, penanganan kegagalan, rollback, dan adapter provider.

Pada pembacaan pertama, lewati kredensial, presentasi, dan kompatibilitas provider; kembali saat mereproduksi angka.

## Proyek Pendamping

| Eksperimen | Proyek | Jenis | Deskripsi |
| :--: | --- | :--: | --- |
| 10-1 | [multi-role-transfer](multi-role-transfer/) | ✅ | Menunjukkan handoff berantai antarpesan dengan riwayat dialog bersama. |
| 10-2 | [book-translation](book-translation/) | 🚧 | Membandingkan manajer empat peran dengan satu Agent untuk penerjemahan buku. |
| 10-3 | `use-computer-while-calling/` + [autonomous-phone-registration](autonomous-phone-registration/) | 📖 / 🚧 | Arsitektur TalkAct dengan fast/slow agents, shared state, dan queue dua arah. Menggabungkan pengamatan formulir, keputusan LLM, panggilan telepon, dan pengisian paralel. |
| 10-4 | [parallel-web-research](parallel-web-research/) | ✅ | Menjalankan sesi browser paralel dengan isolasi error, cleanup, dan bukti terkutip. |
| 10-5 | `generative_agents/` | 📖 | Reproduksi Stanford AI Town dari repositori generative agents eksternal. |
| 10-6 | [voice-werewolf](voice-werewolf/) | 🚧 | Menambahkan simulator pengguna LLM nyata yang hanya melihat konteks kursinya, wajib memanggil alat, dan masuk hanya lewat audio sintetis serta ASR audio OpenRouter nyata. Revalidasi ketat menolak dua run awal yang salah menganggap transkrip buruk sebagai abstain; v2 lulus E2E, isolasi, pemenang, dan tiga siklus, tetapi gagal strategi karena Villager mengusir Seer. |

## Jenis Proyek

| Ikon | Jenis | Arti |
| :--: | --- | --- |
| ✅ | **Mandiri** | Kode lengkap tersedia di repositori dan dapat dijalankan setelah API Key dikonfigurasi. |
| 📖 | **Panduan Reproduksi** | Memerlukan repositori eksternal yang harus di-`git clone`. |
| 🚧 | **Dalam Proses** | Implementasi atau bukti penerimaan belum lengkap. |
