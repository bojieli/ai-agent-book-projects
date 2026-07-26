# Chương 1 · Kiến thức nền tảng về Agent

> xuất phát từ mô hình mới “model as Agent”, xây dựng công thức cốt lõi **Agent = LLM + context + tools**, đồng thời giới thiệu kỹ thuật Harness — mọi năng lực kỹ thuật nằm ngoài mô hình mới là lợi thế cạnh tranh thực sự.

← [Về README chính](../docs/vi/README.md) · 📖 [Đọc nội dung chương](../book-vi/chapter1.vi.md)

## Dự án đi kèm

| Thí nghiệm | Project | Type | Description |
| :--: | --- | :--: | --- |
| 1-1 | [context](context/) | ✅ | Thông qua thí nghiệm ablation có hệ thống để cho thấy tầm quan trọng của từng thành phần trong ngữ cảnh Agent. Hỗ trợ nhiều nhà cung cấp LLM (SiliconFlow Qwen, ByteDance Doubao, Moonshot Kimi), cấu hình các chế độ ngữ cảnh khác nhau để quan sát thay đổi hành vi của Agent. |
| 1-2 | [web-search-agent](web-search-agent/) | ✅ | Triển khai Agent có khả năng tìm kiếm chuyên sâu cơ bản, có thể tìm kiếm nhiều vòng và tổng hợp thông tin. |
| 1-3 | [search-codegen](search-codegen/) | ✅ | Xây dựng Agent có năng lực tìm kiếm chuyên sâu cơ bản và sandbox chạy mã, tổng hợp sử dụng tìm kiếm web, thực thi mã và các công cụ khác để phân tích phức tạp. |
| 7-1, 7-2 | [learning-from-experience](learning-from-experience/) | ✅ | So sánh học tăng cường truyền thống (Q-learning) với học trong ngữ cảnh dựa trên LLM, tái hiện các insight then chốt trong bài viết “The Second Half” của Shunyu Yao. Thông qua trò chơi săn kho báu, dự án cho thấy LLM có thể vượt RL truyền thống về hiệu quả mẫu tới 250–400 lần. |

## Phân loại dự án

| Biểu tượng | Loại | Ý nghĩa |
| :--: | --- | --- |
| ✅ | **Chạy độc lập** | Có mã đầy đủ trong kho, chạy được sau khi cấu hình API Key |
| 📖 | **Hướng dẫn tái hiện** | Tài liệu chi tiết, cần `git clone` **kho ngoài** |
| 🚧 | **Tài liệu thiết kế** | Chỉ có kiến trúc/phương án, mã chạy được đang hoàn thiện |
