# Saran Belajar

← [Kembali ke halaman utama Bahasa Indonesia](README.md)

## Gagasan Inti: Agent = LLM + Konteks + Alat

Rumus inti buku ini adalah **Agent = LLM + Konteks + Alat**. Bab 1 menjelaskan Agent yang sama pada tiga tingkat: tingkat implementasi adalah rumus ini, tingkat intuitif adalah "otak + mata + tangan dan kaki", sedangkan tingkat akademis berpadanan dengan kebijakan (Policy), ruang observasi (Observation Space), dan ruang tindakan (Action Space).

| Komponen | Analogi | Tanggung jawab |
| :--: | :--: | --- |
| 🧠 **LLM** | Otak | Memberikan kemampuan memahami, menalar, dan mengambil keputusan |
| 👁️ **Konteks** | Mata | Seluruh informasi yang dapat dilihat Agent pada setiap titik keputusan: prompt sistem, definisi alat, pesan pengguna, balasan model, hasil eksekusi alat |
| 🤲 **Alat** | Tangan dan kaki | Mengamati lingkungan, menjalankan tindakan, dan berinteraksi dengan dunia luar |

Untuk lingkungan produksi, Bab 1 menuliskan ulang sistem yang sama sebagai **Agent = Model + Harness**, dengan **Harness = pengelolaan konteks + antarmuka alat + batasan + verifikasi + koreksi**. Tiga hal terakhir itulah jarak antara demo yang jalan dan produk yang andal.

## Jalur Belajar

Bagian Pendahuluan menetapkan alur keseluruhan: **Bab 1–6 membangun metode lengkap untuk menyusun sebuah Agent; Bab 7–10 membahas peningkatan kemampuan dari empat arah — evaluasi, pascapelatihan, evolusi berkelanjutan, dan kolaborasi multi-Agent.** Setiap bab disertai satu wawasan utama:

| Bagian | Bab | Cakupan | Wawasan utama |
| --- | :--: | --- | --- |
| **Membangun** | 1 | Tiga unsur Agent, loop ReAct, pola orkestrasi (alur kerja dan otonomi), rekayasa Harness | Jarak antara demo yang jalan dan produk yang andal terletak pada Harness, bukan pada model |
| | 2 | Struktur pesan API, KV Cache, rekayasa prompt dan pertahanan prompt injection, Agent Skills, bilah status Agent, kompresi konteks | Bab terpenting dalam buku ini; konteks menentukan batas atas kemampuan, dan makin stabil prefiksnya makin tinggi cache hit-nya |
| | 3 | Empat strategi bertahap untuk memori pengguna, tumpukan teknologi RAG, pengorganisasian dan pencarian pengetahuan, Agentic RAG, memori multimodal | Memperluas konteks dari satu sesi menjadi pengetahuan yang terakumulasi lintas sesi |
| | 4 | Lima kategori alat (persepsi / eksekusi / kolaborasi / pemicu peristiwa / komunikasi pengguna), MCP, prinsip desain umum, penemuan alat secara aktif | Alat persepsi mengendalikan volume informasi, alat eksekusi mengendalikan risiko; desain alat sebaiknya bersifat umum |
| | 5 | Coding Agent beserta sistem berkas, arsitektur OpenClaw, enam arah kode sebagai kemampuan meta | Kode bukan sekadar menulis program, melainkan kemampuan meta untuk menciptakan alat baru saat runtime |
| | 6 | Dua sumbu, modalitas × waktu: asinkron dan berbasis peristiwa, suara, Computer Use, manipulasi robot | Keempat jenis interaksi berbagi primitif sistem yang sama: pembangunan, titik aman, pembatalan, preemption, pemisahan jalur cepat/lambat |
| **Meningkatkan** | 7 | Lingkungan evaluasi, sistem metrik, desain set data, LLM-as-a-Judge, signifikansi statistik, observabilitas, lingkungan simulasi | Tanpa evaluasi, "peningkatan karena desain" tidak dapat dibedakan dari "fluktuasi acak" |
| | 8 | Panorama empat tahap, mid-training / SFT / RL, desain imbalan, penetapan kredit multi-giliran, distilasi | SFT menghafal, RL menggeneralisasi; data dan lingkungan lebih penting daripada algoritma |
| | 9 | Sinyal pembelajaran (hasil lingkungan / aturan proses / LLM Rubric), empat media pembaruan — pengetahuan, instruksi, program, parameter — serta perilisan bertahap dan rollback | Media pembaruan bergantung pada bagaimana kemampuan dinyatakan dan diverifikasi |
| | 10 | Kerangka klasifikasi (konteks berbagi atau terpisah × setara / manajer / terdesentralisasi), protokol A2A, enam mode kegagalan, masyarakat Agent | Setiap keputusan desain multi-Agent memiliki padanan dalam tiga unsur Agent tunggal |

## Pembagian teks utama dan eksperimen

Buku ini bukan tutorial langkah demi langkah untuk satu SDK. Pseudocode dan skeleton dalam teks hanya menjawab "bagaimana status mengalir, di langkah mana bisa berhenti, sinyal jenis apa yang ikut memverifikasi"; eksperimen tiap bab menyediakan implementasi lengkap, adapter model/lingkungan, pengujian, log, dan bukti. Saat membaca eksperimen Anda tidak perlu memahami setiap baris dari setiap berkas, dan jangan menganggap cara pemanggilan API pada satu eksperimen sebagai arsitektur umum.

Disarankan membaca dalam tiga lapisan berikut; untuk bab yang rumit, pilihlah beberapa eksperimen mekanisme pada lapisan yang sama alih-alih hanya menjalankan satu proyek:

| Lapisan | Baca terlebih dahulu | Lewati dulu | Pertanyaan yang dijawab |
| :--: | --- | --- | --- |
| **Starter** | README proyek: tujuan, perintah minimum, dan syarat penerimaan; skeleton teks yang sesuai | kredensial, UI, adapter provider, dan log mentah yang panjang | Mekanisme apa yang hendak dibuktikan eksperimen ini? |
| **Builder** | entry point, loop inti, skema state/pesan, tool, dan verifier | lapisan kompatibilitas/deployment yang tidak terkait mekanisme | Variabel mana yang mengubah perilaku? |
| **Maintainer** | test, penanganan kegagalan, format bukti, manifest/hash, dan jalur rollback | detail pihak ketiga yang hanya diperlukan saat mengubah eksperimen | Apakah hasil dapat direproduksi dan kegagalan dicatat dengan jujur? |

README setiap bab sudah menandai titik masuk Starter-nya sendiri. Rangkaian pertama yang disarankan: Bab 1 `context`, Bab 2 `context-compression`, Bab 3 `user-memory`, Bab 4 `execution-tools`, Bab 5 `coding-agent`, Bab 6 `live-audio`, Bab 7 `tau2-bench-eval`, Bab 8 `cot-distillation`, Bab 9 `trajectory-verifier`, Bab 10 `parallel-web-research`. Code map pada tiap direktori menandai Run first, Core behavior, Verifier, dan bagian yang boleh dilewati pada bacaan pertama.

## Tingkat Kesulitan

| Tingkat | Bab | Cocok untuk |
| --- | :--: | --- |
| 🟢 Pemula | 1–2 | Pemula; cukup dengan dasar Python dan pengalaman memakai LLM |
| 🔵 Menengah | 3–4 | Pembaca dengan dasar pemrograman; mencakup sistem pencarian dan integrasi alat |
| 🟣 Lanjutan | 5–6 | Kemampuan pemrograman kuat dan desain sistem kompleks; Bab 6 sebaiknya paham HTTP/WebSocket |
| 🟡 Rekayasa | 7 | Infrastruktur evaluasi dan metode statistik — berat di rekayasa, ringan di matematika |
| 🔴 Ahli | 8 | Satu-satunya bab dalam buku ini yang menuntut pengalaman machine learning dan pelatihan model |
| 🟠 Terapan | 9–10 | Menggabungkan seluruh materi sebelumnya untuk membangun lingkar evolusi berkelanjutan dan sistem multi-Agent |

Eksperimen dan soal renungan dalam teks memiliki penanda kesulitan berbintang: ★ tingkat pengantar, cocok untuk semua pembaca; ★★ sedang, memerlukan sedikit pengalaman rekayasa; ★★★ tantangan lanjutan, biasanya berupa masalah terbuka atau desain sistem yang kompleks.

## Saran Praktis

| # | Saran | Penjelasan |
| :--: | --- | --- |
| 1 | 🛠️ **Praktik langsung** | Jalankan dan ubah proyek pendamping agar konsep tidak berhenti pada teori |
| 2 | 📚 **Padukan dengan naskah** | Baca bab terkait di [`book-id/`](../../book-id/) sambil mengerjakan proyeknya |
| 3 | 🔬 **Bandingkan eksperimen** | Gunakan studi ablasi dan eksperimen perbandingan untuk memahami pengaruh setiap komponen |
| 4 | 🪜 **Belajar bertahap** | Mulai dari proyek sederhana, kemudian lanjutkan ke sistem yang lebih kompleks |
| 5 | 🔌 **Perhatikan protokol** | Proyek alat MCP pada Bab 4 menunjukkan mengapa protokol alat terstandar penting bagi Agent yang dapat diperluas |
