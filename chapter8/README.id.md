# Bab 8 · Pasca-Pelatihan Model

> Empat bagian—pre-training, Mid-training, SFT, dan RL: kurikulum serta data konteks panjang, pembentukan protokol SFT, environment dan reward RL, serta efisiensi sampel dari single-turn hingga multi-turn.

← [Kembali ke README utama](../docs/id/README.md) · 📖 [Baca bab](../book-id/chapter8.md)

## Cara Membaca Eksperimen

Teks utama memakai skeleton mekanisme singkat untuk menjelaskan alur kontrol; direktori eksperimen berisi adapter SDK lengkap, log, pengujian, dan bukti penerimaan. Anda tidak perlu membaca setiap berkas baris demi baris.

- **Starter:** Mulai dari tujuan, perintah minimum, dan syarat penerimaan; awali dengan [cot-distillation](cot-distillation/);
- **Builder:** Telusuri titik masuk, loop inti, skema status/pesan, alat, dan verifier.
- **Maintainer:** Terakhir, baca pengujian, manifest bukti, penanganan kegagalan, rollback, dan adapter provider.

Pada pembacaan pertama, lewati kredensial, presentasi, dan kompatibilitas provider; kembali saat mereproduksi angka.

## Proyek Pendamping

| Eksperimen | Proyek | Jenis | Deskripsi |
| :--: | --- | :--: | --- |
| 8-1, 8-2 | [learning-from-experience](../chapter1/learning-from-experience/) | ✅ | Membandingkan Q-learning dan LLM pada lingkungan pencarian harta karun yang sama. |
| 8-3 | [MiniMind-pretrain](MiniMind-pretrain/) · `MiniMind-pretrain/minimind/` | 📖 | Mempelajari proses pre-training LLM kecil dari awal. |
| 8-4 | [MiniMind-pretrain](MiniMind-pretrain/) · `MiniMind-pretrain/minimind-v/` | 📖 | Mempelajari pre-training dan SFT vision-language model kecil. |
| 8-5 | [continued-pretraining](continued-pretraining/) | ✅ | Melanjutkan pre-training pada data domain tertentu. |
| 8-6 | [sesame](sesame/) · [orpheus](orpheus/) | 🚧 | Dua jalur SFT suara untuk tag paralinguistik dan konsistensi timbre lintas kalimat. |
| 8-7 | [MultilingualReasoning](MultilingualReasoning/) | 🚧 | Melatih kemampuan penalaran dalam beberapa bahasa. |
| 8-8 | [prompt-distillation](../chapter8/prompt-distillation/) | ✅ | Membangun data guru, melatih siswa, dan membandingkan kualitas serta biaya. |
| 8-9 | [cot-distillation](cot-distillation/) | 🚧 | Menyaring trajectory CoT yang benar dan menyiapkannya sebagai data SFT. |
| 8-10 | [AdaptThink](AdaptThink/) · `AdaptThink-original/` | 📖 | Mengajarkan model memilih mode Thinking atau NoThinking sesuai kesulitan. |
| 8-11 | `SFTvsRL/` | 📖 | Membandingkan memori dan generalisasi SFT dengan RL pada anggaran yang sama. |
| 8-12 | [SpatialReasoning](SpatialReasoning/) · `SFTvsRL/` | 📖 | Melatih serta mengevaluasi spatial reasoning ID dan OOD. |
| 8-13 | [SimpleVLA-RL](SimpleVLA-RL/) · `SimpleVLA-RL/SimpleVLA-RL/` | 📖 | Menggabungkan visi, bahasa, dan tindakan dalam pelatihan RL. |
| 8-14 | [retool](retool/) · `verl/` · `SandboxFusion/` | 📖 | Melatih penggunaan code interpreter dengan backend veRL dan sandbox eksekusi. |
| 8-15 | [AWorld-train](AWorld-train/) · `AWorld/` | 📖 | Melatih Agent menggunakan tool pada lingkungan GAIA berbasis AWorld. |
| 8-16 | [RLVP](RLVP/) · `RLVP/rlvp/` | 📖 | Mereproduksi riset RLVP: memberi reward pada hasil dan penalti pada jalur. |
| 8-17 | [premature-completion-dpo](premature-completion-dpo/) | ✅ | Perbaikan DPO bad case penyelesaian prematur di GPU. |
| 8-18 | [curly-quote-sft](curly-quote-sft/) | ✅ | SFT tanda kutip lengkung Tionghoa berbasis cakupan yang diaudit: 1.024/256/256 data train/holdout/batas, 10 jenis artikel dan 9 bahasa pemrograman; Qwen3-8B mencapai exact 96,9%/97,7% dan preservasi area terlindungi 100% di GPU. |
| 8-19 | [exact-copy-sft](exact-copy-sft/) | ✅ | SFT penyalinan string khusus byte-exact yang diaudit: 1.024/256/256 data; Qwen3-8B mencapai holdout 78,9% dan batas 80,1%, dengan audit tokenizer Qwen3/Qwen2.5/Mistral. |
| — | `verl/` | 📖 | Framework RLHF efisien untuk PPO, GRPO, DAPO, dan algoritme lain. |
| — | [Intuitor](Intuitor/) | ✅ | Melatih penalaran intuitif tanpa chain-of-thought panjang. |
| — | `tinker-cookbook/` | 📖 | Kumpulan resep dan praktik terbaik pelatihan model. |

## Jenis Proyek

| Ikon | Jenis | Arti |
| :--: | --- | --- |
| ✅ | **Mandiri** | Kode lengkap tersedia di repositori dan dapat dijalankan setelah API Key dikonfigurasi. |
| 📖 | **Panduan Reproduksi** | Memerlukan repositori eksternal yang harus di-`git clone`. |
| 🚧 | **Dalam Proses** | Implementasi, pelatihan, atau bukti penerimaan belum lengkap. |
