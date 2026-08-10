# Chương 2 · Kỹ thuật ngữ cảnh

> ngữ cảnh quyết định trần năng lực của Agent. Đi sâu vào cấu trúc ngữ cảnh của API mô hình lớn, thiết kế thân thiện với KV Cache, prompt engineering, prompt động và Agent Skills, siêu thông tin trên thanh trạng thái, cũng như các chiến lược nén ngữ cảnh.

← [Về README chính](../docs/vi/README.md) · 📖 [Đọc nội dung chương](../book-vi/chapter2.vi.md)

## Cách đọc các thí nghiệm

Phần văn bản dùng skeleton cơ chế ngắn để giải thích luồng điều khiển; thư mục thí nghiệm chứa adapter SDK đầy đủ, log, kiểm thử và bằng chứng nghiệm thu. Không cần đọc từng tệp theo từng dòng.

- **Starter:** Bắt đầu từ mục tiêu, lệnh tối thiểu và điều kiện nghiệm thu; hãy bắt đầu với [context-compression](context-compression/);
- **Builder:** Lần theo điểm vào, vòng lặp lõi, schema trạng thái/tin nhắn, công cụ và verifier.
- **Maintainer:** Sau đó đọc test, manifest bằng chứng, xử lý lỗi, đường rollback và adapter nhà cung cấp.

Lần đầu có thể bỏ qua credential, lớp trình bày và tương thích provider; quay lại khi cần tái tạo số liệu.

## Dự án đi kèm

| Thí nghiệm | Project | Type | Description |
| :--: | --- | :--: | --- |
| 2-1 | [local_llm_serving](local_llm_serving/) | ✅ | Giải pháp triển khai LLM cục bộ đa nền tảng, tự động chọn backend tối ưu (vLLM hoặc Ollama). Cho thấy ngay cả mô hình nhỏ 0.6B cũng có thể đạt năng lực gọi công cụ xuất sắc nhờ thiết kế hệ thống tốt. Hỗ trợ phản hồi streaming và hiển thị quá trình suy nghĩ theo thời gian thực. |
| 2-2, 2-7 | [attention_visualization](attention_visualization/) | ✅ | Trực quan hóa toàn bộ chuỗi token đầu vào/đầu ra và phân bố trọng số attention của LLM, giúp hiểu sâu cách mô hình xử lý ngữ cảnh, suy luận và gọi công cụ. |
| 2-3 | [kv-cache](kv-cache/) | ✅ | Khám phá ảnh hưởng của các chế độ quản lý ngữ cảnh khác nhau lên KV Cache, minh họa các mẫu sai phổ biến làm phá hỏng hiệu quả cache. Thông qua thí nghiệm, dự án cho thấy thiết kế ngữ cảnh đúng có thể giảm đáng kể độ trễ và chi phí. |
| 2-4 | [prompt-engineering](prompt-engineering/) | ✅ | Mở rộng framework Tau-Bench, dùng thí nghiệm ablation có hệ thống để định lượng ảnh hưởng của các yếu tố prompt engineering khác nhau lên hiệu năng Agent. Cho thấy giọng điệu, tổ chức chỉ dẫn, mô tả công cụ và các yếu tố khác ảnh hưởng thế nào tới tỷ lệ hoàn thành nhiệm vụ. |
| 2-5 | [prompt-injection](prompt-injection/) | ✅ | Xây dựng thí nghiệm đối chứng với 3 kịch bản tấn công (tiêm trực tiếp, tiêm gián tiếp, tiêm qua bộ nhớ) × 4 cấu hình phòng thủ (không phòng thủ, gia cố prompt, đánh dấu nguồn, phòng thủ kết hợp), dùng quy tắc xác định để thống kê tỷ lệ tấn công thành công, trực quan cho thấy tỷ lệ tiêm lệnh giảm mạnh khi phòng thủ được chồng lớp. |
| 2-6 | [agent-skills-ppt](agent-skills-ppt/) | ✅ | Tái hiện tư tưởng “tiết lộ tăng dần” của Agent Skills: khi khởi động, Agent chỉ thấy một thư mục Skill mỏng; sau khi nhận diện nhiệm vụ cần Skill `pptx`, nó mới tải dần quy trình đầy đủ, tài liệu chi tiết và script đóng gói, cuối cùng dùng python-pptx tạo file `.pptx` thật. |
| 2-7 | Thí nghiệm văn bản | 🚧 | Tạo một Skill viết nhẹ từ các bài mẫu cá nhân, bao gồm điều kiện kích hoạt, quy tắc, ví dụ, phạm vi và bảo trì lặp lại. |
| 2-8 | [system-hint](system-hint/) | ✅ | Nghiên cứu ảnh hưởng của System Hint tới hành vi Agent, khám phá cách tối ưu system prompt để nâng cao hiệu năng. |
| 2-9 | [context-compression](context-compression/) | ✅ | Triển khai và so sánh nhiều chiến lược nén ngữ cảnh, bao gồm tóm tắt, trích xuất thông tin then chốt, nén ngữ nghĩa, v.v. Mục tiêu là giảm lượng token sử dụng trong khi vẫn giữ năng lực của Agent. |

## Phân loại dự án

| Biểu tượng | Loại | Ý nghĩa |
| :--: | --- | --- |
| ✅ | **Chạy độc lập** | Có mã đầy đủ trong kho, chạy được sau khi cấu hình API Key |
| 📖 | **Hướng dẫn tái hiện** | Tài liệu chi tiết, cần `git clone` **kho ngoài** |
| 🚧 | **Tài liệu thiết kế** | Chỉ có kiến trúc/phương án, mã chạy được đang hoàn thiện |
