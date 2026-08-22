# Chương 8 · Hậu huấn luyện mô hình

> Bốn phần—tiền huấn luyện, Mid-training, SFT và RL: curriculum và dữ liệu ngữ cảnh dài, định hình giao thức bằng SFT, môi trường và phần thưởng RL, cùng hiệu quả mẫu từ một vòng đến nhiều vòng.

← [Về README chính](../docs/vi/README.md) · 📖 [Đọc nội dung chương](../book-vi/chapter8.vi.md)

## Cách đọc các thí nghiệm

Phần văn bản dùng skeleton cơ chế ngắn để giải thích luồng điều khiển; thư mục thí nghiệm chứa adapter SDK đầy đủ, log, kiểm thử và bằng chứng nghiệm thu. Không cần đọc từng tệp theo từng dòng.

- **Starter:** Bắt đầu từ mục tiêu, lệnh tối thiểu và điều kiện nghiệm thu; hãy bắt đầu với [cot-distillation](cot-distillation/);
- **Builder:** Lần theo điểm vào, vòng lặp lõi, schema trạng thái/tin nhắn, công cụ và verifier.
- **Maintainer:** Sau đó đọc test, manifest bằng chứng, xử lý lỗi, đường rollback và adapter nhà cung cấp.

Lần đầu có thể bỏ qua credential, lớp trình bày và tương thích provider; quay lại khi cần tái tạo số liệu.

## Dự án đi kèm

| Thí nghiệm | Project | Type | Description |
| :--: | --- | :--: | --- |
| 8-1, 8-2 | [learning-from-experience](../chapter1/learning-from-experience/) | ✅ | Chạy Q-learning và LLM Agent trong cùng môi trường săn kho báu để học từ kinh nghiệm. |
| 8-8 | [prompt-distillation](../chapter8/prompt-distillation/) | ✅ | Chưng cất ví dụ của giáo viên thành prompt học viên và so sánh chất lượng với chi phí. |
| 8-3, 8-4 | [MiniMind-pretrain](MiniMind-pretrain/) | 📖 | Tiền huấn luyện mô hình ngôn ngữ nhỏ từ con số 0, hiểu toàn bộ quy trình và kỹ thuật then chốt của tiền huấn luyện. |
| 8-5 | [continued-pretraining](continued-pretraining/) | ✅ | Tiếp tục tiền huấn luyện trên dữ liệu miền cụ thể để nâng cao biểu hiện của mô hình trong miền mục tiêu. |
| 8-6 | [sesame](sesame/) | ✅ | Sesame CSM speech SFT: tinh chỉnh LoRA mô hình TTS 1B, điều khiển biểu cảm bằng các thẻ cận ngôn ngữ như `<laugh>`, `<sigh>` |
| 8-6 | [orpheus](orpheus/) | ✅ | Orpheus 3B speech SFT: tinh chỉnh LoRA mô hình TTS, nhân bản giọng nói qua âm thanh tham chiếu để giữ chất giọng nhất quán xuyên câu |
| 8-7 | [MultilingualReasoning](MultilingualReasoning/) | ✅ | Huấn luyện năng lực suy luận của mô hình trong môi trường nhiều ngôn ngữ, nâng cao biểu hiện trên các nhiệm vụ xuyên ngôn ngữ. |
| 8-9 | [cot-distillation](cot-distillation/) | ✅ | Chưng cất quỹ đạo CoT từ các mô hình tiên phong như Claude qua OpenRouter; lọc bằng bộ kiểm chứng luật để tạo dữ liệu SFT (kèm Thí nghiệm 8-9). |
| 8-10 | [AdaptThink](AdaptThink/) | 📖 | Cho mô hình suy luận học cách chọn chế độ suy luận thích ứng theo độ khó của câu hỏi (Thinking vs NoThinking). Thông qua tối ưu có ràng buộc và importance sampling, dự án giảm mạnh chi phí suy luận (45–69%) đồng thời nâng cao độ chính xác. Dựa trên mô hình DeepSeek-R1-Distill-Qwen, huấn luyện bằng thuật toán DAPO. |
| 8-11 | `SFTvsRL/` | 📖 | So sánh có hệ thống hiệu quả của fine-tuning có giám sát (SFT) và học tăng cường (RL) trên các nhiệm vụ khác nhau, phân tích ưu nhược điểm và ngữ cảnh phù hợp của hai phương pháp. |
| 8-12 | [SpatialReasoning](SpatialReasoning/) | 📖 | Tập trung huấn luyện năng lực suy luận không gian của mô hình, xử lý các vấn đề liên quan đến vị trí, phương hướng, khoảng cách và các quan hệ không gian khác. |
| 8-13 | [SimpleVLA-RL](SimpleVLA-RL/) | 📖 | Huấn luyện học tăng cường kết hợp thị giác, ngôn ngữ và hành động, giúp mô hình hiểu đầu vào thị giác và thực hiện hành động tương ứng. |
| 8-14 | [retool](retool/) | 📖 | Dùng hội thoại nhiều vòng và sandbox mã để nâng cao năng lực suy luận toán học của mô hình ngôn ngữ lớn. Thông qua hai giai đoạn SFT và RL, mô hình học cách dùng môi trường thực thi mã để hỗ trợ giải bài toán. Dựa trên Qwen2.5-32B-Instruct, huấn luyện trên bộ AIME 2024, dùng thuật toán DAPO và sandbox SandboxFusion. |
| 8-15 | `AWorld/` · [AWorld-train](AWorld-train/) | 📖 | Huấn luyện Agent hiện thân dựa trên framework AWorld, giúp Agent thực thi nhiệm vụ phức tạp trong môi trường ảo và học từ kinh nghiệm. |
| 8-16 | [RLVP](RLVP/) | 📖 | Nghiên cứu hậu huấn luyện RLVP (thưởng cho kết quả, phạt đường đi), dự án đi kèm Thí nghiệm 8-16; mã huấn luyện/đánh giá đầy đủ nằm trong kho bài báo riêng `19PINE-AI/rlvp`, cần tự clone. |
| 8-17 | [premature-completion-dpo](premature-completion-dpo/) | ✅ | Sửa bad case hoàn thành sớm bằng DPO trên GPU. |
| 8-18 | [curly-quote-sft](curly-quote-sft/) | ✅ | SFT dấu ngoặc kép cong tiếng Trung theo phạm vi đã kiểm toán: 1024/256/256 mẫu train/holdout/biên, 10 thể loại và 9 ngôn ngữ lập trình; Qwen3-8B đạt exact 96,9%/97,7%, bảo toàn vùng bảo vệ 100%. |
| 8-19 | [exact-copy-sft](exact-copy-sft/) | ✅ | SFT sao chép chuỗi đặc biệt byte-exact đã kiểm toán: 1024/256/256 mẫu; Qwen3-8B đạt holdout 78,9%, biên 80,1%, kèm kiểm toán tokenizer Qwen3/Qwen2.5/Mistral. |
| — | `verl/` | 📖 | verl là framework học tăng cường hiệu quả được thiết kế riêng cho huấn luyện RLHF của mô hình ngôn ngữ lớn, hỗ trợ nhiều thuật toán như PPO, GRPO, DAPO. |
| — | [Intuitor](Intuitor/) | ✅ | Huấn luyện năng lực suy luận trực giác của mô hình, giúp mô hình có thể nhanh chóng đưa ra phán đoán hợp lý mà không cần chuỗi suy nghĩ chi tiết. |
| — | `tinker-cookbook/` | 📖 | Tập hợp nhiều kỹ thuật thực dụng và best practice cho huấn luyện mô hình. |

## Phân loại dự án

| Biểu tượng | Loại | Ý nghĩa |
| :--: | --- | --- |
| ✅ | **Chạy độc lập** | Có mã đầy đủ trong kho, chạy được sau khi cấu hình API Key |
| 📖 | **Hướng dẫn tái hiện** | Tài liệu chi tiết, cần `git clone` **kho ngoài** |
| 🚧 | **Tài liệu thiết kế** | Chỉ có kiến trúc/phương án, mã chạy được đang hoàn thiện |
