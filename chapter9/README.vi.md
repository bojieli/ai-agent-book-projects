# Chương 9 · Tự tiến hóa của Agent

> Agent vẫn có thể trưởng thành mà không cần sửa trọng số. Ba mô thức học tập: học từ kinh nghiệm, và từ “người dùng công cụ” thành “người tạo công cụ”, giúp Agent đi từ “thông minh” tới “thành thạo”.

← [Về README chính](../docs/vi/README.md) · 📖 [Đọc nội dung chương](../book-vi/chapter9.vi.md)

## Cách đọc các thí nghiệm

Phần văn bản dùng skeleton cơ chế ngắn để giải thích luồng điều khiển; thư mục thí nghiệm chứa adapter SDK đầy đủ, log, kiểm thử và bằng chứng nghiệm thu. Không cần đọc từng tệp theo từng dòng.

- **Starter:** Bắt đầu từ mục tiêu, lệnh tối thiểu và điều kiện nghiệm thu; hãy bắt đầu với [trajectory-verifier](trajectory-verifier/);
- **Builder:** Lần theo điểm vào, vòng lặp lõi, schema trạng thái/tin nhắn, công cụ và verifier.
- **Maintainer:** Sau đó đọc test, manifest bằng chứng, xử lý lỗi, đường rollback và adapter nhà cung cấp.

Lần đầu có thể bỏ qua credential, lớp trình bày và tương thích provider; quay lại khi cần tái tạo số liệu.

## Dự án đi kèm

| Thí nghiệm | Project | Type | Description |
| :--: | --- | :--: | --- |
| 9-1 | [trajectory-verifier](trajectory-verifier/) | ✅ | Thí nghiệm 9-1: kết hợp kết quả môi trường, quy tắc quá trình và rubric ngôn ngữ thành chẩn đoán trajectory chăm sóc khách hàng có bằng chứng |
| 9-2 | [gaia-experience](gaia-experience/) | ✅ | Thí nghiệm 9-2: so sánh trajectory thành công, thành công một phần và thất bại để sinh tài liệu kinh nghiệm Markdown xuyên trajectory |
| 9-3 | [prompt-auto-optimization](prompt-auto-optimization/) | ✅ | Thí nghiệm 9-3: sinh bản vá prompt tối thiểu từ trajectory thất bại, kiểm soát phát hành bằng tập biên và tập giữ lại |
| 9-4 | Thí nghiệm trong sách | 🚧 | Thí nghiệm 9-4: tiến hóa Skill "làm rõ yêu cầu + xác nhận Spec" từ phản hồi người dùng; phần chính đưa ra thiết kế A/B ba nhánh, các chỉ số và cổng phát hành, phần triển khai đi kèm còn thiếu |
| 9-5 | [browser-use-rpa](browser-use-rpa/) | ✅ | Thí nghiệm 9-5: biên dịch trajectory trình duyệt thành workflow có vị từ trạng thái (state predicates), được kiểm chứng bằng phát lại sau reset |
| 9-6 | [self-modifying-agent](self-modifying-agent/) | ✅ | Thí nghiệm 9-6: lỗi lặp lại kích hoạt bản vá mã retry/circuit-breaker, kiểm thử hồi quy, phát hành canary và rollback |
| 9-7 | [harness-safety-gate](harness-safety-gate/) | ✅ | Cổng xác nhận thao tác rủi ro cao |
| 9-8 | [hermes-self-evolution](hermes-self-evolution/) | 📖 | Đưa cho Hermes toàn bộ cuốn sách và mã nguồn của chính nó; Hermes chọn một cải tiến, tự sửa mình và biến mỗi lần Reviewer từ chối thành một vòng học mới cho tới khi được chấp nhận |
| 9-9 | [self-evolution-eval](self-evolution-eval/) | ✅ | Thí nghiệm 9-9: đánh giá tiến hóa dài hạn qua bốn giai đoạn — học, chuyển giao, thay đổi quy tắc và giữ vững |

Tất cả thí nghiệm trên đều có lối chạy offline và unit test không cần API Key; các hướng mở rộng cần model thật hoặc trình duyệt được ghi trong README của từng dự án.

## Trường hợp bổ sung

| Thí nghiệm | Project | Quan hệ |
| :--: | --- | --- |
| 8-8 | [prompt-distillation](../chapter8/prompt-distillation/) | Dự án xuyên chương về chưng cất prompt và học tham số hóa; phương pháp huấn luyện thuộc Chương 8 |
| — | [self-evolving-tools](self-evolving-tools/) | Khám phá, đóng gói và tái sử dụng công cụ kiểu Alita — trường hợp bổ sung của “viết kinh nghiệm thành chương trình” |
| — | [ai-style-skill](ai-style-skill/) | Chuyển phản hồi viết thành Skill có thể kiểm chứng; chương nối Skill dấu ngoặc kép cong với dữ liệu tổng hợp đã kiểm toán và hậu huấn luyện, đồng thời tách lỗi tokenizer/Harness trong sao chép chính xác |

## Phân loại dự án

| Biểu tượng | Loại | Ý nghĩa |
| :--: | --- | --- |
| ✅ | **Chạy độc lập** | Có mã đầy đủ trong kho, chạy được sau khi cấu hình API Key |
| 📖 | **Hướng dẫn tái hiện** | Tài liệu chi tiết, cần `git clone` **kho ngoài** |
| 🚧 | **Tài liệu thiết kế** | Chỉ có kiến trúc/phương án, mã chạy được đang hoàn thiện |
