# Memahami AI Agent secara Mendalam: Prinsip Desain dan Praktik Rekayasa

[![PDF](https://img.shields.io/badge/PDF-unduh-success.svg)](#-buku-elektronik) [![Baca daring](https://img.shields.io/badge/🌐_Baca_daring-bojieli.github.io-success?style=flat-square)](https://bojieli.github.io/ai-agent-book/) [![Stars](https://img.shields.io/github/stars/bojieli/ai-agent-book?style=social)](https://github.com/bojieli/ai-agent-book) [![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](../../LICENSE) [![Languages](https://img.shields.io/badge/terjemahan-13%20bahasa-informational.svg)](#-buku-elektronik)
[![Trending GitHub Project of the Day](https://img.shields.io/badge/GitHub%20Trending-Project%20of%20the%20Day-orange?logo=github)](https://github.com/trending)

**[中文](../../README.md) · [English](../en/README.md) · [Español](../es/README.md) · Bahasa Indonesia ← saat ini · [العربية](../ar/README.md) · [繁體中文（台灣）](../zh-TW/README.md) · [Русский](../ru/README.md) · [Tiếng Việt](../vi/README.md) · [தமிழ்](../ta/README.md) · [日本語](../ja/README.md) · [Türkçe](../tr/README.md) · [한국어](../ko/README.md) · [Magyar](../hu/README.md)**

> 📥 **[Unduh PDF / EPUB](#-buku-elektronik)** (direkomendasikan) — edisi PDF dan EPUB memberikan pengalaman membaca terbaik. Anda juga dapat [membaca secara daring](https://bojieli.github.io/ai-agent-book/) dengan pemilih bahasa, navigasi bab, dan pencarian teks lengkap.

**Agent = LLM + Konteks + Alat** — buku ini memakai rumus inti tersebut untuk membahas AI Agent, dari prinsip dasar hingga praktik rekayasa, dalam sepuluh bab. Naskah, ilustrasi, dan proyek pendampingnya tersedia sebagai sumber terbuka.

> 🚧 **Reorganisasi versi 2.0 sedang berlangsung:** Buku ini telah berpindah dari versi 1.4 ke 2.0 dan kini mengikuti alur belajar baru. Bab 6–9 sekarang membahas “Interaksi: Perluasan Ruang Observasi dan Aksi”, “Evaluasi Agent”, “Pascapelatihan Model”, dan “Evolusi Berkelanjutan Agent”. PDF yang sudah diterbitkan mungkin sementara masih memakai struktur lama; gunakan README ini dan naskah dalam repositori sebagai acuan penempatan bab, penomoran, dan pintu masuk eksperimen.

| 📚 **10 bab** dari dasar hingga produksi | 📂 **103 proyek** pendamping | 🌐 **13 bahasa**: ZH / EN / ES / ID / AR / zh-TW / RU / TA / VI / JA / TR / KO / HU |
| :---: | :---: | :---: |

## 📖 Buku Elektronik

> 📥 **Unduh untuk dibaca luring** (lengkap, gratis, dan bersumber terbuka). Tautan berikut selalu menunjuk ke hasil build terbaru dari cabang `main`; versi tetap tersedia di halaman [Releases](https://github.com/bojieli/ai-agent-book/releases):
> - **Bahasa Tionghoa (asli)**: [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-CN.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-CN.epub)
> - **Bahasa Inggris**: [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-en.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-en.epub)
> - **Bahasa Spanyol** (terjemahan komunitas oleh [@santhreal](https://github.com/santhreal)): [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-es.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-es.epub)
> - **Bahasa Indonesia** (terjemahan komunitas oleh [@jojixyz666](https://github.com/jojixyz666)): [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-id.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-id.epub)
> - **Bahasa Tionghoa Tradisional (Taiwan)**: [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-TW.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-TW.epub)
> - **Bahasa Rusia**: [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ru.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ru.epub)
> - **Bahasa Tamil**: [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ta.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ta.epub)
> - **Bahasa Vietnam**: [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-vi.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-vi.epub)
> - **Bahasa Jepang**: [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ja.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ja.epub)
> - **Bahasa Arab**: [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ar.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ar.epub)
> - **Bahasa Turki**: [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-tr.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-tr.epub)
> - **Bahasa Korea**: [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ko.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ko.epub)

Sumber naskah Bahasa Indonesia berada di [`book-id/`](../../book-id/). Edisi ini merupakan terjemahan komunitas dan mungkin tertinggal dari naskah asli berbahasa Tionghoa.

<details>
<summary><b>🔧 Ingin membuat PDF / EPUB sendiri?</b> (PDF memerlukan pandoc, XeLaTeX, ElegantBook, dan librsvg)</summary>

- **EPUB**: Gunakan pembuat bersama; lihat [petunjuk build EPUB](../../EPUB.md)
- **Sumber teks**: `book-id/introduction.md`, `book-id/chapter1.md` sampai `book-id/chapter10.md`, dan `book-id/afterword.md`.
- **Build**:

  ```bash
  cd book-id && bash build_pdf.sh
  ```

</details>

## 📑 Ringkasan Isi (Bab 1–10)

| Bab | Topik | Inti Pembahasan | Naskah | Kode |
| :--: | --- | --- | :--: | :--: |
| 1 | 🚀 **Memulai dengan AI Agent** | **Agent = LLM + Konteks + Alat**; rekayasa harness merupakan sumber daya saing | [Baca](../../book-id/chapter1.md) | [3](../../chapter1/README.id.md) |
| 2 | 🎯 **Rekayasa Konteks** | KV Cache, rekayasa prompt, Agent Skills, dan kompresi konteks | [Baca](../../book-id/chapter2.md) | [10](../../chapter2/README.id.md) |
| 3 | 📚 **Memori Pengguna dan Basis Pengetahuan** | Memori lintas sesi, RAG, indeks terstruktur, dan graf pengetahuan | [Baca](../../book-id/chapter3.md) | [12](../../chapter3/README.id.md) |
| 4 | 🛠️ **Alat** | MCP, alat persepsi, eksekusi, kolaborasi, dan penemuan alat secara proaktif | [Baca](../../book-id/chapter4.md) | [5](../../chapter4/README.id.md) |
| 5 | 💻 **Coding Agent dan Pembuatan Kode** | Kode sebagai alat yang dapat membuat alat baru; implementasi Coding Agent tingkat produksi | [Baca](../../book-id/chapter5.md) | [13](../../chapter5/README.id.md) |
| 6 | 🎙️ **Interaksi: Perluasan Ruang Observasi dan Aksi** | Memperluas ruang observasi dan aksi Agent melalui dimensi modalitas dan waktu: sistem asinkron berbasis peristiwa, suara, Computer Use, dan robotika | [Baca](../../book-id/chapter6.md) | [13](../../chapter6/README.id.md) |
| 7 | 🎯 **Evaluasi Agent** | Lingkungan evaluasi, metrik, signifikansi statistik, dan pemilihan berbasis evaluasi | [Baca](../../book-id/chapter7.md) | [13](../../chapter7/README.id.md) |
| 8 | 🧠 **Pascapelatihan Model** | Prapelatihan, SFT, RL, internalisasi pemanggilan alat, dan efisiensi sampel | [Baca](../../book-id/chapter8.md) | [19](../../chapter8/README.id.md) |
| 9 | 🔄 **Evolusi Berkelanjutan Agent** | Belajar dari jejak eksekusi dan memperbarui pengetahuan, instruksi, program, serta parameter | [Baca](../../book-id/chapter9.md) | [9](../../chapter9/README.id.md) |
| 10 | 🤝 **Kolaborasi Multi-Agent** | Kerangka kolaborasi, berbagi/isolasi konteks, dan kemunculan “masyarakat Agent” | [Baca](../../book-id/chapter10.md) | [6](../../chapter10/README.id.md) |
> 💡 **Baca** membuka naskah bab di GitHub; angka pada kolom **Kode** membuka daftar proyek pendamping.
>
> 📚 Untuk jalur belajar yang disarankan, lihat **[Saran Belajar](LEARNING.md)**.

> 🧪 Status pelaksanaan eksperimen, bukti, dan gerbang penerimaan yang belum terpenuhi dicatat secara terpisah di [`EXPERIMENT_STATUS.md`](../EXPERIMENT_STATUS.md); mengkloning atau memasang kode sumber tidak membuktikan bahwa eksperimen telah selesai.

## 📦 Lampiran · Mengambil Repositori Eksternal

Beberapa eksperimen memakai repositori eksternal yang tidak disertakan langsung karena ukuran dan lisensinya. Perintah berikut mengunci setiap checkout ke revisi yang dapat direproduksi.

<details>
<summary><b>🔧 Tampilkan 23 perintah checkout</b></summary>

```bash
# Bab 7 · Tolok ukur evaluasi
git clone https://github.com/google-research/android_world.git chapter7/android_world && git -C chapter7/android_world checkout --detach 0e95d641e244504c22087cc29b013f3b2428a261
git clone https://huggingface.co/datasets/gaia-benchmark/GAIA chapter7/GAIA && git -C chapter7/GAIA checkout --detach 682dd723ee1e1697e00360edccf2366dc8418dd9
git clone https://github.com/xlang-ai/OSWorld.git chapter7/OSWorld && git -C chapter7/OSWorld checkout --detach 8365edc975efd0477a0d62444a5beed562ab5a7b
git clone https://github.com/SWE-bench/SWE-bench.git chapter7/SWE-bench && git -C chapter7/SWE-bench checkout --detach 5cd4be9fb23971679cbbafe5a0ecade27cef99be
git clone https://github.com/sierra-research/tau2-bench.git chapter7/tau2-bench && git -C chapter7/tau2-bench checkout --detach 8d005b0e5b9e4af0bc055886fa7f95fc86d1710e
git clone https://github.com/laude-institute/terminal-bench.git chapter7/terminal-bench && git -C chapter7/terminal-bench checkout --detach 8384a179b1b8688f6ea5233a4d9d51218df1ac96

# Bab 8 · Kerangka pelatihan
git clone https://github.com/bojieli/minimind.git chapter8/MiniMind-pretrain/minimind && git -C chapter8/MiniMind-pretrain/minimind fetch origin 8bdc5d97d5845a8c1ac2ed56a5b8b4c0d0fb0795 && git -C chapter8/MiniMind-pretrain/minimind checkout --detach 8bdc5d97d5845a8c1ac2ed56a5b8b4c0d0fb0795 && test "$(git -C chapter8/MiniMind-pretrain/minimind rev-parse HEAD)" = "8bdc5d97d5845a8c1ac2ed56a5b8b4c0d0fb0795"
git clone https://github.com/bojieli/minimind-v.git chapter8/MiniMind-pretrain/minimind-v && git -C chapter8/MiniMind-pretrain/minimind-v fetch origin ead791c530fa5f9a3549dbfe9e11ec732d18d2e5 && git -C chapter8/MiniMind-pretrain/minimind-v checkout --detach ead791c530fa5f9a3549dbfe9e11ec732d18d2e5 && test "$(git -C chapter8/MiniMind-pretrain/minimind-v rev-parse HEAD)" = "ead791c530fa5f9a3549dbfe9e11ec732d18d2e5"
git clone https://github.com/bojieli/AdaptThink.git chapter8/AdaptThink-original && git -C chapter8/AdaptThink-original checkout --detach 0033ad172dd53ac64004b763477407014f21b838
git clone https://github.com/bojieli/SFTvsRL.git chapter8/SFTvsRL && git -C chapter8/SFTvsRL checkout --detach fef0a4a3367260a0934be1e40b01e4021698e023
git clone https://github.com/bojieli/AWorld.git chapter8/AWorld && git -C chapter8/AWorld checkout --detach a52d61d6d483e66b22ef16970eae5bbf4f4ab2ec
git clone https://github.com/bojieli/verl.git chapter8/verl && git -C chapter8/verl checkout --detach 1593fc3a8cf894debdc3dece2a23ed739c282789
git clone https://github.com/bojieli/SandboxFusion.git chapter8/SandboxFusion && git -C chapter8/SandboxFusion fetch origin 4a0d573ebd64c98234c190a9d1d49e4276199a0c && git -C chapter8/SandboxFusion checkout --detach 4a0d573ebd64c98234c190a9d1d49e4276199a0c && test "$(git -C chapter8/SandboxFusion rev-parse HEAD)" = "4a0d573ebd64c98234c190a9d1d49e4276199a0c"
git clone https://github.com/thinking-machines-lab/tinker-cookbook.git chapter8/tinker-cookbook && git -C chapter8/tinker-cookbook checkout --detach fc8449187041cf102905f3f751e6d2eac7f9f754
git clone https://github.com/19PINE-AI/rlvp.git chapter8/RLVP/rlvp && git -C chapter8/RLVP/rlvp fetch origin 1ad30bc7e338911fb733739393d92c420f4d8bee && git -C chapter8/RLVP/rlvp checkout --detach 1ad30bc7e338911fb733739393d92c420f4d8bee && test "$(git -C chapter8/RLVP/rlvp rev-parse HEAD)" = "1ad30bc7e338911fb733739393d92c420f4d8bee"
git clone https://github.com/PRIME-RL/SimpleVLA-RL.git chapter8/SimpleVLA-RL/SimpleVLA-RL && git -C chapter8/SimpleVLA-RL/SimpleVLA-RL checkout --detach 7c51662df27b586f9e8a1ab35fcf849f2b8852f9

# Bab 6 · GUI dan robotika
git clone https://github.com/anthropics/claude-quickstarts.git chapter6/claude-quickstarts && git -C chapter6/claude-quickstarts checkout --detach 9bcc95e316e5ef6542b4c9d0469f4078829eead5
git clone https://github.com/browser-use/browser-use.git chapter6/browser-use && git -C chapter6/browser-use checkout --detach ec9277c5001f2cb78ee419c927775a3cfc227ff8
git clone https://github.com/Vector-Wangel/XLeRobot.git chapter6/XLeRobot && git -C chapter6/XLeRobot fetch origin 3d14695e40c9c68229c0aacffca6053c75cd3eb6 && git -C chapter6/XLeRobot checkout --detach 3d14695e40c9c68229c0aacffca6053c75cd3eb6 && test "$(git -C chapter6/XLeRobot rev-parse HEAD)" = "3d14695e40c9c68229c0aacffca6053c75cd3eb6"
git clone https://github.com/Grigorij-Dudnik/RoboCrew.git chapter6/RoboCrew && git -C chapter6/RoboCrew fetch origin c749148f29bd14e61347f9fc3530c343fff0d994 && git -C chapter6/RoboCrew checkout --detach c749148f29bd14e61347f9fc3530c343fff0d994 && test "$(git -C chapter6/RoboCrew rev-parse HEAD)" = "c749148f29bd14e61347f9fc3530c343fff0d994"
git clone https://github.com/StoneT2000/lerobot-sim2real.git chapter6/lerobot-sim2real && git -C chapter6/lerobot-sim2real fetch origin 87d6c1d969f6e0ca4dc5697940804e231118a63a && git -C chapter6/lerobot-sim2real checkout --detach 87d6c1d969f6e0ca4dc5697940804e231118a63a && test "$(git -C chapter6/lerobot-sim2real rev-parse HEAD)" = "87d6c1d969f6e0ca4dc5697940804e231118a63a"

# Bab 10 · Arsitektur multi-Agent
git clone https://github.com/19PINE-AI/TalkAct.git chapter10/use-computer-while-calling && git -C chapter10/use-computer-while-calling fetch origin 7d70007f72d45ddfc1a14e8e229b6d444e4919a2 && git -C chapter10/use-computer-while-calling checkout --detach 7d70007f72d45ddfc1a14e8e229b6d444e4919a2 && test "$(git -C chapter10/use-computer-while-calling rev-parse HEAD)" = "7d70007f72d45ddfc1a14e8e229b6d444e4919a2"
git clone https://github.com/joonspk-research/generative_agents.git chapter10/generative_agents && git -C chapter10/generative_agents fetch origin fe05a71d3e4ed7d10bf68aa4eda6dd995ec070f4 && git -C chapter10/generative_agents checkout --detach fe05a71d3e4ed7d10bf68aa4eda6dd995ec070f4 && test "$(git -C chapter10/generative_agents rev-parse HEAD)" = "fe05a71d3e4ed7d10bf68aa4eda6dd995ec070f4"
```

</details>

## 🤝 Kontribusi

Naskah dan kode pendamping buku ini bersumber terbuka. Koreksi, perbaikan terjemahan, peningkatan proyek, dan ilustrasi yang lebih jelas dipersilakan melalui Pull Request.

## 📄 Lisensi

Proyek ini menggunakan [Lisensi Apache 2.0](../../LICENSE). Beberapa subproyek mungkin memiliki lisensinya sendiri; ikuti ketentuan yang tercantum di direktori masing-masing.
