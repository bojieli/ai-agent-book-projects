# Chương 8 · Tự tiến hóa của Agent

> Agent vẫn có thể trưởng thành mà không cần sửa trọng số. Ba mô thức học tập: học từ kinh nghiệm, và từ “người dùng công cụ” thành “người tạo công cụ”, giúp Agent đi từ “thông minh” tới “thành thạo”.

← [Về README chính](../docs/vi/README.md) · 📖 [Đọc nội dung chương](../book-vi/chapter8.vi.md)

## Dự án đi kèm

| Thí nghiệm | Project | Type | Description |
| :--: | --- | :--: | --- |
| 8-1 | [trajectory-verifier](trajectory-verifier/) | ✅ | Thí nghiệm 8-1: kết hợp kết quả môi trường, quy tắc quá trình và rubric ngôn ngữ thành chẩn đoán trajectory chăm sóc khách hàng có bằng chứng |
| 8-2 | [gaia-experience](gaia-experience/) | ✅ | Thí nghiệm 8-2: so sánh trajectory thành công, thành công một phần và thất bại để sinh tài liệu kinh nghiệm Markdown xuyên trajectory |
| 8-3 | [prompt-auto-optimization](prompt-auto-optimization/) | ✅ | Thí nghiệm 8-3: sinh bản vá prompt tối thiểu từ trajectory thất bại, kiểm soát phát hành bằng tập biên và tập giữ lại |
| 8-4 | [browser-use-rpa](browser-use-rpa/) | ✅ | Thí nghiệm 8-4: biên dịch trajectory trình duyệt thành workflow có vị từ trạng thái (state predicates), được kiểm chứng bằng phát lại sau reset |
| 8-5 | [self-modifying-agent](self-modifying-agent/) | ✅ | Thí nghiệm 8-5: lỗi lặp lại kích hoạt bản vá mã retry/circuit-breaker, kiểm thử hồi quy, phát hành canary và rollback |
| 8-6 | [hermes-self-evolution](hermes-self-evolution/) | 📖 | Đưa cho Hermes toàn bộ cuốn sách và mã nguồn của chính nó; Hermes chọn một cải tiến, tự sửa mình và biến mỗi lần Reviewer từ chối thành một vòng học mới cho tới khi được chấp nhận |
| 8-7 | [self-evolution-eval](self-evolution-eval/) | ✅ | Thí nghiệm 8-7: đánh giá tiến hóa dài hạn qua bốn giai đoạn — học, chuyển giao, thay đổi quy tắc và giữ vững |
| 8-8 | [harness-safety-gate](harness-safety-gate/) | ✅ | Cổng xác nhận thao tác rủi ro cao |
| 8-9 | [ai-style-skill](ai-style-skill/) | ✅ | Chuyển phản hồi viết thành Skill có thể kiểm chứng; chương nối Skill dấu ngoặc kép cong với dữ liệu tổng hợp đã kiểm toán và hậu huấn luyện, đồng thời tách lỗi tokenizer/Harness trong sao chép chính xác |

Tất cả thí nghiệm trên đều có lối chạy offline và unit test không cần API Key; các hướng mở rộng cần model thật hoặc trình duyệt được ghi trong README của từng dự án.

## Trường hợp bổ sung

| Thí nghiệm | Project | Quan hệ |
| :--: | --- | --- |
| 7-8 | [prompt-distillation](prompt-distillation/) | Dự án xuyên chương về chưng cất prompt và học tham số hóa; phương pháp huấn luyện thuộc Chương 7 |
| — | [self-evolving-tools](self-evolving-tools/) | Khám phá, đóng gói và tái sử dụng công cụ kiểu Alita — trường hợp bổ sung của “viết kinh nghiệm thành chương trình” |

## Phân loại dự án

| Biểu tượng | Loại | Ý nghĩa |
| :--: | --- | --- |
| ✅ | **Chạy độc lập** | Có mã đầy đủ trong kho, chạy được sau khi cấu hình API Key |
| 📖 | **Hướng dẫn tái hiện** | Tài liệu chi tiết, cần `git clone` **kho ngoài** |
| 🚧 | **Tài liệu thiết kế** | Chỉ có kiến trúc/phương án, mã chạy được đang hoàn thiện |
