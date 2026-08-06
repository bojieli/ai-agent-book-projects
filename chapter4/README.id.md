# Bab 4 · Tool

> Tool adalah tangan Agent: klasifikasi dan desain tool, protokol MCP, tool persepsi/eksekusi/kolaborasi, serta Agent asinkron berbasis event.

← [Kembali ke README utama](../docs/id/README.md) · 📖 [Baca bab](../book-id/chapter4.md)

## Proyek Pendamping

| Eksperimen | Proyek | Jenis | Deskripsi |
| :--: | --- | :--: | --- |
| 4-1 | [perception-tools](perception-tools/) | ✅ | Menyediakan tool pencarian web, multimodal, sistem file, dan data publik. |
| 4-2 | [multimodal-agent](multimodal-agent/) | ✅ | Multimodal processing: compare native multimodal, extract-to-text, and tool-based analysis. |
| 4-3 | [execution-tools](execution-tools/) | ✅ | Mengimplementasikan operasi file, interpreter kode, terminal virtual, dan pengamanan eksekusi. |
| 4-4 | [collaboration-tools](collaboration-tools/) | ✅ | Menyediakan browser automation, Human-in-the-Loop, notifikasi, dan timer. |
| 4-5 | [agent-with-event-trigger](agent-with-event-trigger/) | ✅ | Membangun Agent event-driven berbasis FastAPI dengan sumber event majemuk. |
| 4-6 | [async-agent](async-agent/) | ✅ | Mengimplementasikan queue event, prioritas, tool paralel, interupsi, pembatalan, dan status tugas. |
| 4-7 | [active-tool-discovery](active-tool-discovery/) | ✅ | Membandingkan injeksi seluruh schema tool dengan penemuan tool sesuai kebutuhan. |
| — | [active-tool-selection](active-tool-selection/) | ✅ | Memilih kombinasi tool yang paling sesuai berdasarkan kebutuhan tugas. |

> `chapter4/docker-compose.yml` dan `chapter4/DOCKER_DEPLOYMENT.md` menyediakan referensi deployment container untuk server MCP.

## Jenis Proyek

| Ikon | Jenis | Arti |
| :--: | --- | --- |
| ✅ | **Mandiri** | Kode lengkap tersedia di repositori dan dapat dijalankan setelah API Key dikonfigurasi. |
| 📖 | **Panduan Reproduksi** | Memerlukan repositori eksternal yang harus di-`git clone`. |
| 🚧 | **Dalam Proses** | Implementasi atau bukti penerimaan belum lengkap. |
