# Bab 4 · Tool

> Tool adalah tangan Agent: klasifikasi dan desain tool, protokol MCP, tool persepsi/eksekusi/kolaborasi, serta Agent asinkron berbasis event.

← [Kembali ke README utama](../docs/id/README.md) · 📖 [Baca bab](../book-id/chapter4.md)

## Cara Membaca Eksperimen

Teks utama memakai skeleton mekanisme singkat untuk menjelaskan alur kontrol; direktori eksperimen berisi adapter SDK lengkap, log, pengujian, dan bukti penerimaan. Anda tidak perlu membaca setiap berkas baris demi baris.

- **Starter:** Mulai dari tujuan, perintah minimum, dan syarat penerimaan; awali dengan [execution-tools](execution-tools/);
- **Builder:** Telusuri titik masuk, loop inti, skema status/pesan, alat, dan verifier.
- **Maintainer:** Terakhir, baca pengujian, manifest bukti, penanganan kegagalan, rollback, dan adapter provider.

Pada pembacaan pertama, lewati kredensial, presentasi, dan kompatibilitas provider; kembali saat mereproduksi angka.

## Proyek Pendamping

| Eksperimen | Proyek | Jenis | Deskripsi |
| :--: | --- | :--: | --- |
| 4-1 | [perception-tools](perception-tools/) | ✅ | Menyediakan tool pencarian web, multimodal, sistem file, dan data publik. |
| 4-2 | [multimodal-agent](multimodal-agent/) | ✅ | Multimodal processing: compare native multimodal, extract-to-text, and tool-based analysis. |
| 4-3 | [execution-tools](execution-tools/) | ✅ | Mengimplementasikan operasi file, interpreter kode, terminal virtual, dan pengamanan eksekusi. |
| 4-4 | [collaboration-tools](collaboration-tools/) | ✅ | Menyediakan browser automation, Human-in-the-Loop, notifikasi, dan timer. |
| 4-5 | [active-tool-discovery](active-tool-discovery/) | ✅ | Membandingkan injeksi seluruh schema tool dengan penemuan tool sesuai kebutuhan. |
| — | [active-tool-selection](active-tool-selection/) | ✅ | Memilih kombinasi tool yang paling sesuai berdasarkan kebutuhan tugas. |

> `chapter4/docker-compose.yml` dan `chapter4/DOCKER_DEPLOYMENT.md` menyediakan referensi deployment container untuk server MCP.

## Jenis Proyek

| Ikon | Jenis | Arti |
| :--: | --- | --- |
| ✅ | **Mandiri** | Kode lengkap tersedia di repositori dan dapat dijalankan setelah API Key dikonfigurasi. |
| 📖 | **Panduan Reproduksi** | Memerlukan repositori eksternal yang harus di-`git clone`. |
| 🚧 | **Dalam Proses** | Implementasi atau bukti penerimaan belum lengkap. |
