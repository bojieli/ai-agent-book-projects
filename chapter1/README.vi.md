# Chương 1 · Kiến thức nền tảng về Agent

> xuất phát từ mô hình mới “model as Agent”, xây dựng công thức cốt lõi **Agent = LLM + context + tools**, đồng thời giới thiệu kỹ thuật Harness — mọi năng lực kỹ thuật nằm ngoài mô hình mới là lợi thế cạnh tranh thực sự.

← [Về README chính](../docs/vi/README.md) · 📖 [Đọc nội dung chương](../book-vi/chapter1.vi.md)

## Cách đọc các thí nghiệm

Phần văn bản dùng skeleton cơ chế ngắn để giải thích luồng điều khiển; thư mục thí nghiệm chứa adapter SDK đầy đủ, log, kiểm thử và bằng chứng nghiệm thu. Không cần đọc từng tệp theo từng dòng.

- **Starter:** Bắt đầu từ mục tiêu, lệnh tối thiểu và điều kiện nghiệm thu; hãy bắt đầu với [context](context/);
- **Builder:** Lần theo điểm vào, vòng lặp lõi, schema trạng thái/tin nhắn, công cụ và verifier.
- **Maintainer:** Sau đó đọc test, manifest bằng chứng, xử lý lỗi, đường rollback và adapter nhà cung cấp.

Lần đầu có thể bỏ qua credential, lớp trình bày và tương thích provider; quay lại khi cần tái tạo số liệu.

## Dự án đi kèm

| Thí nghiệm | Project | Type | Description |
| :--: | --- | :--: | --- |
| 1-1 | [context](context/) | ✅ | Thông qua thí nghiệm ablation có hệ thống để cho thấy tầm quan trọng của từng thành phần trong ngữ cảnh Agent. Hỗ trợ nhiều nhà cung cấp LLM (SiliconFlow Qwen, ByteDance Doubao, Moonshot Kimi), cấu hình các chế độ ngữ cảnh khác nhau để quan sát thay đổi hành vi của Agent. |
| 1-2 | [web-search-agent](web-search-agent/) | ✅ | Triển khai Agent có khả năng tìm kiếm chuyên sâu cơ bản, có thể tìm kiếm nhiều vòng và tổng hợp thông tin. |
| 1-3 | [search-codegen](search-codegen/) | ✅ | Xây dựng Agent có năng lực tìm kiếm chuyên sâu cơ bản và sandbox chạy mã, tổng hợp sử dụng tìm kiếm web, thực thi mã và các công cụ khác để phân tích phức tạp. |
| 1-4 | [image-gen-workflow](image-gen-workflow/) | ✅ | So sánh thực tế hai lộ trình cho yêu cầu cụ thể/rộng × workflow (viết lại kimi-k3 + Tongyi Wanxiang) so với bản địa (Gemini / GPT-Image 2): với yêu cầu cụ thể, lộ trình bản địa trung thực hơn (nút viết lại đã đưa văn bản poster vào negative prompt); với yêu cầu rộng, cụ thể hóa cảnh mang lại sức sáng tạo, nhưng GPT-Image 2 có thể tự cung cấp góc nhìn—bằng chứng thực nghiệm rằng lớp adapter được nội hóa bởi mô hình |
| 7-1, 7-2 | [learning-from-experience](learning-from-experience/) | ✅ | So sánh học tăng cường truyền thống (Q-learning) với học trong ngữ cảnh dựa trên LLM, tái hiện các insight then chốt trong bài viết “The Second Half” của Shunyu Yao. Thông qua trò chơi săn kho báu, dự án cho thấy LLM có thể vượt RL truyền thống về hiệu quả mẫu tới 250–400 lần. |

## Phân loại dự án

| Biểu tượng | Loại | Ý nghĩa |
| :--: | --- | --- |
| ✅ | **Chạy độc lập** | Có mã đầy đủ trong kho, chạy được sau khi cấu hình API Key |
| 📖 | **Hướng dẫn tái hiện** | Tài liệu chi tiết, cần `git clone` **kho ngoài** |
| 🚧 | **Tài liệu thiết kế** | Chỉ có kiến trúc/phương án, mã chạy được đang hoàn thiện |
