# Hiểu sâu về AI Agent: Nguyên lý thiết kế và thực hành kỹ thuật

[![Stars](https://img.shields.io/github/stars/bojieli/ai-agent-book?style=social)](https://github.com/bojieli/ai-agent-book) [![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](../../LICENSE) [![PDF](https://img.shields.io/badge/PDF-tải%20về-success.svg)](#-sách-điện-tử) [![Languages](https://img.shields.io/badge/dịch-5%20ngôn%20ngữ-informational.svg)](#-sách-điện-tử)

**[中文](../../README.md) · [台灣正體](../zh-TW/README.md) · [English](../en/README.md) · Tiếng Việt ← hiện tại · [தமிழ்](../ta/README.md) · [Türkçe](../../README.tr.md)**

**Agent = LLM + Context + Tools** — Cuốn sách xây dựng trên công thức cốt lõi này qua 10 chương, đưa AI Agent từ nguyên lý đến thực hành kỹ thuật. Toàn bộ nội dung, hình minh họa và **88 thí nghiệm đi kèm** đều là mã nguồn mở. Hoan nghênh bạn tự chạy các thí nghiệm.

| 📚 **10 chương** nội dung, từ nền tảng đến sản xuất | 📂 **88** dự án đi kèm (70+ chạy độc lập) | 🌐 **6 ngôn ngữ**: Trung / 台灣正體 / Anh / Tamil / Việt / Thổ Nhĩ Kỳ |
| :---: | :---: | :---: |

## 📖 Sách điện tử

> 📥 **Tải xuống PDF / EPUB** (toàn bộ nội dung, mã nguồn mở miễn phí). Các liên kết này luôn trỏ tới bản dựng mới nhất của nhánh `main`; bản cố định xem tại [Releases](https://github.com/bojieli/ai-agent-book/releases):
> - **Bản gốc tiếng Trung**：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-CN.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-CN.epub)
> - **Trung phồn thể (Đài Loan)**（dịch cộng đồng, by [@tigercosmos](https://github.com/tigercosmos)）：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-TW.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-TW.epub)
> - **Tiếng Anh**（dịch cộng đồng, by [@nsdevaraj](https://github.com/nsdevaraj)）：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-en.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-en.epub)
> - **Tiếng Tamil**（dịch cộng đồng, by [@nsdevaraj](https://github.com/nsdevaraj)）：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ta.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ta.epub)
> - **Tiếng Việt**（dịch cộng đồng, by [@toanalien](https://github.com/toanalien)）：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-vi.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-vi.epub)
> - **Tiếng Thổ Nhĩ Kỳ**（dịch cộng đồng, by [@memisemre](https://github.com/memisemre)）：chưa có bản PDF/EPUB — đọc trực tiếp trong [`book-tr/`](../../book-tr/)

Mã nguồn tiếng Trung nằm trong [`book/`](../../book/); các bản Trung phồn thể (Đài Loan)/Anh/Tamil/Việt/Thổ Nhĩ Kỳ là đóng góp cộng đồng (có thể chậm hơn bản gốc), nằm trong [`book-zhtw/`](../../book-zhtw/), [`book-en/`](../../book-en/), [`book-ta/`](../../book-ta/), [`book-vi/`](../../book-vi/), [`book-tr/`](../../book-tr/).

Trình dựng chung tạo sách EPUB 3 cho tiếng Trung giản thể, tiếng Trung phồn thể (Đài Loan), tiếng Anh, tiếng Tamil và tiếng Việt. Xem [hướng dẫn dựng EPUB](../../EPUB.md).

<details>
<summary><b>🔧 Tự build PDF?</b> (cần pandoc / xelatex / ElegantBook)</summary>

- **Mã nguồn**: `book/introduction.md` (mở đầu), `book/chapter1.md` ~ `book/chapter10.md` (Chương 1–10), `book/afterword.md` (bạt từ)
- **Build**: Cài pandoc, xelatex, ElegantBook và font cần thiết, rồi chạy

  ```bash
  cd book && bash build_pdf.sh
  ```

  Hình vẽ do `book/gen_*_figs.py` tạo, lưu trong `book/images/`; chi tiết typography xem `book/preamble.tex` và `book/*.lua`.

</details>

## 📑 Tổng quan nội dung (Chương 1–10)

Sách xoay quanh công thức cốt lõi **Agent = LLM + Context + Tools**, mười chương tuần tự nâng dần:

| Ch | Chủ đề | Tóm tắt một câu | Văn bản | Mã |
| :--: | --- | --- | :--: | :--: |
| 1 | 🚀 **Kiến thức nền tảng về Agent** | Mô hình "Model as Agent" + **Agent = LLM + Context + Tools**; kỹ thuật Harness mới là lợi thế cạnh tranh thực sự | [Đọc](../../book-vi/chapter1.vi.md) | [4](../../chapter1/README.vi.md) |
| 2 | 🎯 **Kỹ thuật ngữ cảnh** | Ngữ cảnh quyết định trần năng lực: KV Cache, prompt engineering, Agent Skills, nén ngữ cảnh | [Đọc](../../book-vi/chapter2.vi.md) | [9](../../chapter2/README.vi.md) |
| 3 | 📚 **Bộ nhớ người dùng và kho tri thức** | Ghi nhớ người dùng qua phiên + tri thức ngoài: bộ nhớ người dùng, RAG, chỉ mục cấu trúc, đồ thị tri thức | [Đọc](../../book-vi/chapter3.vi.md) | [13](../../chapter3/README.vi.md) |
| 4 | 🛠️ **Công cụ** | Công cụ là đôi tay Agent: giao thức MCP, cảm nhận/thực thi/cộng tác, Agent bất đồng bộ hướng sự kiện, khám phá công cụ tích cực | [Đọc](../../book-vi/chapter4.vi.md) | [7](../../chapter4/README.vi.md) |
| 5 | 💻 **Coding Agent và sinh mã** | Mã là "công cụ tạo ra công cụ mới"; Coding Agent cấp sản xuất đầy đủ | [Đọc](../../book-vi/chapter5.vi.md) | [12](../../chapter5/README.vi.md) |
| 6 | 🎯 **Đánh giá Agent** | Biến biểu hiện thành tín hiệu so sánh được: môi trường, chỉ số, ý nghĩa thống kê, chọn mô hình dựa trên đánh giá | [Đọc](../../book-vi/chapter6.vi.md) | [10](../../chapter6/README.vi.md) |
| 7 | 🧠 **Hậu huấn luyện mô hình** | Tiền huấn luyện/SFT/RL ba giai đoạn: khi nào SFT, khi nào RL, nội tại hóa gọi công cụ, hiệu quả mẫu | [Đọc](../../book-vi/chapter7.vi.md) | [14](../../chapter7/README.vi.md) |
| 8 | 🔄 **Tự tiến hóa của Agent** | Trưởng thành không cần sửa trọng số: học từ kinh nghiệm, từ người dùng thành người tạo | [Đọc](../../book-vi/chapter8.vi.md) | [6](../../chapter8/README.vi.md) |
| 9 | 🎙️ **Đa phương thức và tương tác thời gian thực** | Mở rộng từ văn bản sang giọng nói, GUI, thế giới vật lý: ba mô thức giọng nói, Computer Use, robot | [Đọc](../../book-vi/chapter9.vi.md) | [7](../../chapter9/README.vi.md) |
| 10 | 🤝 **Cộng tác đa Agent** | Trí tuệ tập thể cao hơn cá thể: khung cộng tác, chia sẻ/cô lập ngữ cảnh, "xã hội Agent" nổi lên | [Đọc](../../book-vi/chapter10.vi.md) | [6](../../chapter10/README.vi.md) |


> 💡 **Đọc** = đọc nội dung chương trên GitHub (markdown); **N** = số dự án đi kèm, nhấp để xem code. Phân loại (✅ Chạy độc lập / 📖 Tái hiện / 🚧 Thiết kế) xem README từng chương.
>
> 📚 Cách đọc sách hiệu quả? Xem **[Gợi ý học tập](LEARNING.md)** (ý tưởng cốt lõi, lộ trình, phân cấp độ khó, mẹo thực hành).

## 🔑 API Key

Nên đăng ký API key từ vài nền tảng để thuận tiện học tập. Tham khảo [hướng dẫn này](https://01.me/2025/07/llm-api-setup/) để chọn mô hình.

| Nền tảng | Link | Đặc điểm |
| --- | --- | --- |
| **Kimi** (Moonshot) | <https://platform.moonshot.cn/> | Kimi series, ngữ cảnh dài và khả năng Agent mạnh |
| **Zhipu GLM** | <https://open.bigmodel.cn/> | GLM-4.6, tiếng Trung mạnh, hiệu năng/ch giá tốt |
| **Siliconflow** | <https://siliconflow.cn/> | Các mô hình mở (DeepSeek, Qwen, v.v.) |
| **Volcano Engine** | <https://www.volcengine.com/product/ark> | ByteDance Doubao (closed-source), độ trễ thấp trong nước |
| **OpenRouter** | <https://openrouter.ai/> | Truy cập Gemini / Claude / GPT-5 v.v. (API chính thức cần IP/phương thức thanh toán ngoài; OpenAI còn cần xác thực danh tính ngoài) |

## 📦 Phụ lục · Lấy kho ngoài

20 kho ngoài cho benchmark, framework huấn luyện, nền tảng robot ở Chương 6, 7, 9, 10 **không được đóng gói** (do kích thước và bản quyền), cần tự clone vào thư mục tương ứng.

### Script clone một lần

<details>
<summary><b>🔧 Mở rộng lệnh clone</b> (20 kho ngoài)</summary>

```bash
# Chương 6 · Benchmark đánh giá
git clone https://github.com/google-research/android_world.git         chapter6/android_world
git clone https://huggingface.co/datasets/gaia-benchmark/GAIA          chapter6/GAIA
git clone https://github.com/xlang-ai/OSWorld.git                      chapter6/OSWorld
git clone https://github.com/SWE-bench/SWE-bench.git                   chapter6/SWE-bench
git clone https://github.com/sierra-research/tau2-bench.git            chapter6/tau2-bench
git clone https://github.com/laude-institute/terminal-bench.git        chapter6/terminal-bench

# Chương 7 · Framework huấn luyện (bojieli/* là fork phù hợp với sách)
git clone https://github.com/bojieli/minimind.git                      chapter7/MiniMind-pretrain/minimind      # Exp 7-3 train LLM from scratch
git clone https://github.com/bojieli/minimind-v.git                    chapter7/MiniMind-pretrain/minimind-v    # Exp 7-4 train VLM (projection layer)
git clone https://github.com/bojieli/AdaptThink.git                    chapter7/AdaptThink-original
git clone https://github.com/bojieli/AWorld.git                        chapter7/AWorld
git clone https://github.com/bojieli/SFTvsRL.git                       chapter7/SFTvsRL
git clone https://github.com/bojieli/verl.git                          chapter7/verl
git clone https://github.com/thinking-machines-lab/tinker-cookbook.git chapter7/tinker-cookbook
git clone https://github.com/bojieli/lighteval.git                     chapter7/Intuitor/lighteval
git clone https://github.com/19PINE-AI/rlvp.git                        chapter7/RLVP/rlvp                       # Exp 7-14 RLVP paper code
git clone https://github.com/PRIME-RL/SimpleVLA-RL.git                 chapter7/SimpleVLA-RL/SimpleVLA-RL       # Exp 7-13 vision-language-action RL

# Chương 9 · Tự động hóa trình duyệt & ví dụ Claude
git clone https://github.com/browser-use/browser-use.git               chapter9/browser-use
git clone https://github.com/anthropics/claude-quickstarts.git         chapter9/claude-quickstarts

# Chương 10 · Kiến trúc đa Agent (đã độc lập thành TalkAct) + Stanford AI Town
git clone https://github.com/19PINE-AI/TalkAct.git                     chapter10/use-computer-while-calling
git clone https://github.com/joonspk-research/generative_agents.git    chapter10/generative_agents             # Exp 10-7 Stanford AI Town
```

> Nếu README dự án chỉ định commit cụ thể, hãy `git checkout` phiên bản đó để đảm bảo tái hiện. Chương 10 `use-computer-while-calling` đã phát triển thành [19PINE-AI/TalkAct](https://github.com/19PINE-AI/TalkAct) độc lập; kho này chỉ giữ tài liệu trỏ tới.

</details>

### Các đường dẫn tái hiện khác

Các thí nghiệm dưới đây không có lệnh clone riêng nhưng có phương thức tái hiện cụ thể:

| Thí nghiệm | Loại | Mô tả |
| --- | :--: | --- |
| 6-2 / 6-3 / 6-4 / 6-9 | 📝 Bài tập bạn đọc | Human benchmark, đánh giá bộ nhớ, JSON Cards vs RAG, chọn bộ nhớ — cải tạo từ `user-memory` / `user-memory-evaluation` / `contextual-retrieval` chương 3 |
| 5-12 | 📝 Bài tập bạn đọc | Agent tạo Agent — bootstrap từ `chapter5/coding-agent` |
| 7-8 | 📝 Bài tập bạn đọc | Prompt distillation — xem `chapter8/prompt-distillation` (dùng lại xuyên chương) |
| 7-9 | 📝 Bài tập bạn đọc | CoT distillation `[Mở rộng]` — thiết kế và tiêu chí trong sách, không có code riêng |
| 6-11 | 🤖 Đánh giá mô phỏng | OpenVLA + RoboTwin2 — xem README `chapter7/SimpleVLA-RL` về VLA training/env |
| 9-8 / 9-9 | 🔧 Phần cứng thật | XLeRobot teleoperation và LLM Agent control — cần tay máy SO-100, [Teleop](https://xlerobot.readthedocs.io/en/latest/software/getting_started/XLeRobot_teleop.html) · [LLM Agent](https://xlerobot.readthedocs.io/en/latest/software/getting_started/LLM_agent.html) |
| 9-10 | 🔧 Phần cứng thật | RGB zero-shot Sim2Real grasping — [`StoneT2000/lerobot-sim2real`](https://github.com/StoneT2000/lerobot-sim2real) (mô phỏng chạy pure GPU; triển khai cần SO-100) |

## 🤝 Đóng góp

Sách và mã đi kèm hoàn toàn mã nguồn mở. Rất hoan nghênh Pull Request:

| Loại | Mô tả |
| --- | --- |
| 📝 **Cải tiến nội dung sách** | Hiệu đính, bổ sung, diễn đạt rõ hơn, hoặc tiến triển mới (nội dung trong `book/chapter*.md`) |
| 🐛 **Cải tiến code & sửa bug** | Dự án đi kèm mạnh mẽ hơn, dễ dùng hơn, gần sản xuất hơn |
| 🧪 **Dự án thực hành mới** | Bổ sung/thay thế cài đặt tốt hơn cho thí nghiệm, hoặc đóng góp ví dụ mới |
| 🎨 **Cải tiến hình vẽ** | Biểu đồ trong `book/images/` rõ và đẹp hơn (do `book/gen_*_figs.py` tạo) |
| 🌐 **Bản dịch ngôn ngữ mới** | Hoan nghênh dịch sang nhiều ngôn ngữ; xem Trung phồn thể/Đài Loan (`book-zhtw/`), tiếng Anh (`book-en/`), Tamil (`book-ta/`), Việt (`book-vi/`), Thổ Nhĩ Kỳ (`book-tr/`) |

Trước khi gửi, hãy chạy thí nghiệm liên quan để xác nhận tái hiện; có thể mở issue thảo luận trước.

## 📄 Giấy phép

Dự án sử dụng [Apache License 2.0](../../LICENSE). Xem tệp [`LICENSE`](../../LICENSE). Một số dự án con có thể có thông tin giấy phép riêng; xem dự án con để biết chi tiết.

## ⭐ Lịch sử Star

<a href="https://star-history.com/#bojieli/ai-agent-book&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="../../assets/star-history-dark.png" />
    <source media="(prefers-color-scheme: light)" srcset="../../assets/star-history-light.png" />
    <img alt="Star History Chart" src="../../assets/star-history-light.png" width="100%" />
  </picture>
</a>

<sub>Được tạo bởi [`scripts/gen_star_history.py`](../../scripts/gen_star_history.py), cập nhật hàng ngày bởi [GitHub Actions](../../.github/workflows/star-history.yml) · Nhấp vào hình để xem dữ liệu trực tiếp</sub>
