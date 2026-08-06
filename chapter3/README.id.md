# Bab 3 · Memori Pengguna dan Knowledge Base

> Memungkinkan Agent mengingat pengguna lintas sesi dan mengakses pengetahuan eksternal melalui memori, RAG, indeks terstruktur, dan knowledge graph.

← [Kembali ke README utama](../docs/id/README.md) · 📖 [Baca bab](../book-id/chapter3.md)

## Proyek Pendamping

| Eksperimen | Proyek | Jenis | Deskripsi |
| :--: | --- | :--: | --- |
| 3-1, 3-2 | [user-memory](user-memory/) | ✅ | Membangun memori pengguna jangka panjang untuk preferensi dan riwayat interaksi. |
| 3-1 | [user-memory-evaluation](user-memory-evaluation/) | ✅ | Mengevaluasi akurasi, relevansi, dan efektivitas sistem memori pengguna. |
| 3-2 | [mem0](mem0/) · [memobase](memobase/) | ✅ | Membandingkan implementasi memori menggunakan framework Mem0 dan Memobase. |
| 3-3 | [log-sanitization](log-sanitization/) | ✅ | Mendeteksi dan menyamarkan secret serta PII pada log dengan model lokal. |
| 3-4 | [dense-embedding](dense-embedding/) | ✅ | Membandingkan indeks approximate nearest neighbor ANNOY dan HNSW. |
| 3-5 | [sparse-embedding](sparse-embedding/) | ✅ | Mengimplementasikan mesin pencarian sparse berbasis BM25 dari awal. |
| 3-6 | [retrieval-pipeline](retrieval-pipeline/) | ✅ | Menggabungkan dense retrieval, sparse retrieval, dan neural reranking. |
| 3-7 | [structured-index](structured-index/) | ✅ | Membandingkan RAPTOR dan GraphRAG sebagai pendekatan pengindeksan terstruktur. |
| 3-8 | [agentic-rag](agentic-rag/) | ✅ | Membandingkan RAG tradisional dengan Agentic RAG yang melakukan retrieval iteratif. |
| 3-9 | [agentic-rag-for-user-memory](agentic-rag-for-user-memory/) | ✅ | Menerapkan Agentic RAG untuk mengambil riwayat percakapan lintas sesi. |
| 3-10 | [contextual-retrieval](contextual-retrieval/) | ✅ | Menambahkan prefix context pada chunk untuk mengurangi kegagalan retrieval. |
| 3-11 | [contextual-retrieval-for-user-memory](contextual-retrieval-for-user-memory/) | ✅ | Menggabungkan Advanced JSON Cards dan Contextual RAG menjadi memori dua lapis. |
| 3-12 | [structured-knowledge-extraction](structured-knowledge-extraction/) | ✅ | Mengekstraksi faktor keputusan dan prototipe kasus dari dataset putusan hukum. |

## Jenis Proyek

| Ikon | Jenis | Arti |
| :--: | --- | --- |
| ✅ | **Mandiri** | Kode lengkap tersedia di repositori dan dapat dijalankan setelah API Key dikonfigurasi. |
| 📖 | **Panduan Reproduksi** | Memerlukan repositori eksternal yang harus di-`git clone`. |
| 🚧 | **Dalam Proses** | Implementasi atau bukti penerimaan belum lengkap. |
