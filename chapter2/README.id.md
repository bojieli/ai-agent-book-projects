# Bab 2 · Rekayasa Context

> Context menentukan batas atas kemampuan Agent: struktur API, desain ramah KV Cache, prompt engineering, Agent Skills, status bar, dan kompresi context.

← [Kembali ke README utama](../docs/id/README.md) · 📖 [Baca bab](../book-id/chapter2.md)

## Proyek Pendamping

| Eksperimen | Proyek | Jenis | Deskripsi |
| :--: | --- | :--: | --- |
| 2-1 | [local_llm_serving](local_llm_serving/) | ✅ | Menyediakan deployment LLM lokal lintas platform dengan backend vLLM atau Ollama. |
| 2-2, 2-7 | [attention_visualization](attention_visualization/) | ✅ | Memvisualisasikan token input/output dan distribusi bobot attention model. |
| 2-3 | [kv-cache](kv-cache/) | ✅ | Membandingkan pola pengelolaan context dan dampaknya terhadap efisiensi KV Cache. |
| 2-4 | [prompt-engineering](prompt-engineering/) | ✅ | Mengukur pengaruh unsur prompt melalui eksperimen ablasi yang sistematis. |
| 2-5 | [prompt-injection](prompt-injection/) | ✅ | Membandingkan tiga skenario serangan dengan empat konfigurasi pertahanan berlapis. |
| 2-6 | [agent-skills-ppt](agent-skills-ppt/) | ✅ | Mempraktikkan progressive disclosure pada Agent Skills untuk menghasilkan presentasi PPTX. |
| 2-8 | [system-hint](system-hint/) | ✅ | Menguji pengaruh System Hints terhadap perilaku dan kinerja Agent. |
| 2-9 | [context-compression](context-compression/) | ✅ | Membandingkan beberapa strategi kompresi untuk mengurangi token tanpa kehilangan kemampuan utama. |

## Jenis Proyek

| Ikon | Jenis | Arti |
| :--: | --- | --- |
| ✅ | **Mandiri** | Kode lengkap tersedia di repositori dan dapat dijalankan setelah API Key dikonfigurasi. |
| 📖 | **Panduan Reproduksi** | Memerlukan repositori eksternal yang harus di-`git clone`. |
| 🚧 | **Dalam Proses** | Implementasi atau bukti penerimaan belum lengkap. |
