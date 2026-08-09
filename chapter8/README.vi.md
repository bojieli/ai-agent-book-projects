# Chương 8 · Tự tiến hóa của Agent

> Agent vẫn có thể trưởng thành mà không cần sửa trọng số. Ba mô thức học tập: học từ kinh nghiệm, và từ “người dùng công cụ” thành “người tạo công cụ”, giúp Agent đi từ “thông minh” tới “thành thạo”.

← [Về README chính](../docs/vi/README.md) · 📖 [Đọc nội dung chương](../book-vi/chapter8.vi.md)

## Dự án đi kèm

| Thí nghiệm | Project | Type | Description |
| :--: | --- | :--: | --- |
| 8-1 | [trajectory-verifier](trajectory-verifier/) | ✅ | Thí nghiệm 8-1: kết hợp kết quả môi trường, quy tắc quá trình và rubric ngôn ngữ thành chẩn đoán trajectory chăm sóc khách hàng có bằng chứng |
| 8-2 | [gaia-experience](gaia-experience/) | ✅ | Thí nghiệm 8-2: so sánh trajectory thành công, thành công một phần và thất bại để sinh tài liệu kinh nghiệm Markdown xuyên trajectory |
| 8-3 | [prompt-auto-optimization](prompt-auto-optimization/) | ✅ | Thí nghiệm 8-3: sinh bản vá prompt tối thiểu từ trajectory thất bại, kiểm soát phát hành bằng tập biên và tập giữ lại |
| 8-4 | Thí nghiệm văn bản | 🚧 | Thí nghiệm 8-4: phát triển Skill làm rõ yêu cầu từ phản hồi của người dùng |
| 8-5 | [browser-use-rpa](browser-use-rpa/) | ✅ | Thí nghiệm 8-5: biên dịch trajectory trình duyệt thành workflow có vị từ trạng thái |
| 8-6 | [self-modifying-agent](self-modifying-agent/) | ✅ | Thí nghiệm 8-6: lỗi lặp lại kích hoạt bản vá mã retry/circuit-breaker, kiểm thử hồi quy và phát hành canary |
| 8-7 | [harness-safety-gate](harness-safety-gate/) | ✅ | Thí nghiệm 8-7: cổng xác nhận thao tác rủi ro cao |
| 8-8 | [hermes-self-evolution](hermes-self-evolution/) | 📖 | Thí nghiệm 8-8: đưa cho Hermes toàn bộ cuốn sách và mã nguồn của chính nó |
| 8-9 | [self-evolution-eval](self-evolution-eval/) | ✅ | Thí nghiệm 8-9: đánh giá tiến hóa dài hạn qua bốn giai đoạn |

Tất cả thí nghiệm trên đều có lối chạy offline và unit test không cần API Key; các hướng mở rộng cần model thật hoặc trình duyệt được ghi trong README của từng dự án.

## Trường hợp bổ sung

| Thí nghiệm | Project | Quan hệ |
| :--: | --- | --- |
| 7-8 | [prompt-distillation](prompt-distillation/) | Dự án xuyên chương về chưng cất prompt và học tham số hóa; phương pháp huấn luyện thuộc Chương 7 |
| — | [self-evolving-tools](self-evolving-tools/) | Khám phá, đóng gói và tái sử dụng công cụ kiểu Alita — trường hợp bổ sung của “viết kinh nghiệm thành chương trình” |
| — | [ai-style-skill](ai-style-skill/) | Trường hợp bổ sung của Skill viết; ví dụ chính nằm ở Chương 2 |

## Phân loại dự án

| Biểu tượng | Loại | Ý nghĩa |
| :--: | --- | --- |
| ✅ | **Chạy độc lập** | Có mã đầy đủ trong kho, chạy được sau khi cấu hình API Key |
| 📖 | **Hướng dẫn tái hiện** | Tài liệu chi tiết, cần `git clone` **kho ngoài** |
| 🚧 | **Tài liệu thiết kế** | Chỉ có kiến trúc/phương án, mã chạy được đang hoàn thiện |
