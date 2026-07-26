# Chương 8 · Tự tiến hóa của Agent

> Agent vẫn có thể trưởng thành mà không cần sửa trọng số. Ba mô thức học tập: học từ kinh nghiệm, và từ “người dùng công cụ” thành “người tạo công cụ”, giúp Agent đi từ “thông minh” tới “thành thạo”.

← [Về README chính](../docs/vi/README.md) · 📖 [Đọc nội dung chương](../book-vi/chapter8.vi.md)

## Dự án đi kèm

| Thí nghiệm | Project | Type | Description |
| :--: | --- | :--: | --- |
| 7-8 | [prompt-distillation](prompt-distillation/) | ✅ | Chưng cất hiệu quả của prompt phức tạp vào tham số mô hình, giảm độ dài prompt khi suy luận và cố định kinh nghiệm trong ngữ cảnh thành tri thức tham số hóa. |
| 8-2 | [gaia-experience](gaia-experience/) | ✅ | Dựa trên framework AWorld và benchmark GAIA, triển khai vòng kín “học - áp dụng” hoàn chỉnh. Agent tự động tóm tắt trajectory nhiệm vụ thành công thành kinh nghiệm có cấu trúc, sau đó truy xuất và áp dụng trong nhiệm vụ mới để hiện thực tự tiến hóa. |
| 8-3 | [prompt-auto-optimization](prompt-auto-optimization/) | ✅ | Học system prompt tự động dựa trên phản hồi con người: lấy vấn đề “chuyển tiếp quá mức” trong chăm sóc khách hàng hàng không kiểu tau-bench làm ví dụ, cho một Coding Agent đọc file system prompt, định vị quy tắc có vấn đề, sinh chỉnh sửa chính xác và thật sự viết lại file prompt, sau đó đánh giá lại để xác minh, tạo thành vòng kín “phản hồi → viết lại → xác minh”. |
| 8-4 | [browser-use-rpa](browser-use-rpa/) | ✅ | Triển khai hệ thống ghi workflow cho tự động hóa trình duyệt, tự động đóng gói chuỗi thao tác lặp lại thành công cụ tham số hóa. Bằng cách chuyển từ suy luận LLM đắt đỏ sang thực thi tự động hóa chính xác, tốc độ tăng 3–5 lần. |
| 8-6 | [self-evolution-eval](self-evolution-eval/) | ✅ | Bộ dữ liệu chuyên dụng và phương pháp xác minh được thiết kế để đánh giá năng lực “tự tiến hóa” của Agent (tự phát hiện, tạo và tái sử dụng công cụ): 20 nhiệm vụ xuyên miền (không ám chỉ tên công cụ) + harness xác minh phân tầng bốn lớp + Agent tham chiếu có kiểm soát, vượt ra ngoài việc “kết quả đúng hay sai” để khảo sát chất lượng phát hiện, tạo và tái sử dụng. |
| — | [self-evolving-tools](self-evolving-tools/) | ✅ | Phong cách Alita “định nghĩa sẵn tối thiểu, tự tiến hóa tối đa”: Agent không cài sẵn công cụ miền nào, chỉ có năm meta-tool tổng quát; khi gặp nhiệm vụ chưa biết làm, nó tự lên mạng tìm thư viện/API mã nguồn mở, đọc tài liệu, kiểm thử trong sandbox, đóng gói phương án khả thi thành công cụ mới đưa vào thư viện công cụ và tái sử dụng, toàn quy trình nhấn mạnh kiểm soát hallucination. |

## Phân loại dự án

| Biểu tượng | Loại | Ý nghĩa |
| :--: | --- | --- |
| ✅ | **Chạy độc lập** | Có mã đầy đủ trong kho, chạy được sau khi cấu hình API Key |
| 📖 | **Hướng dẫn tái hiện** | Tài liệu chi tiết, cần `git clone` **kho ngoài** |
| 🚧 | **Tài liệu thiết kế** | Chỉ có kiến trúc/phương án, mã chạy được đang hoàn thiện |
