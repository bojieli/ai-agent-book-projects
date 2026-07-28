# Chương 9 · Đa phương thức và tương tác thời gian thực

> mở rộng cảm nhận và hành động từ văn bản sang giọng nói, GUI và thế giới vật lý. Ba mô thức giọng nói (pipeline nối tầng/đa phương thức đầu cuối/full-duplex), cảm nhận và tổng hợp giọng nói dạng streaming, Computer Use và thao tác robot.

← [Về README chính](../docs/vi/README.md) · 📖 [Đọc nội dung chương](../book-vi/chapter9.vi.md)

## Dự án đi kèm

| Thí nghiệm | Project | Type | Description |
| :--: | --- | :--: | --- |
| 9-1 | [live-audio](live-audio/) | ✅ | Demo chat giọng nói thời gian thực, tích hợp speech-to-text, hội thoại AI và text-to-speech. Hỗ trợ nhiều nhà cung cấp dịch vụ AI (OpenAI, OpenRouter, ARK, Siliconflow), cung cấp trải nghiệm hội thoại độ trễ thấp. |
| 9-2 | [phone-agent](phone-agent/) | ✅ | Minh họa Agent giọng nói “thay người dùng gọi điện tương tác với thế giới bên ngoài”: tầng trên là ReAct Agent tiêu chuẩn; sau khi nhận nhiệm vụ ngôn ngữ tự nhiên, nó tự xác định số điện thoại và mục tiêu cuộc gọi, gọi công cụ `make_phone_call` (dựa trên trừu tượng API giọng nói điện thoại) để hoàn tất toàn bộ cuộc gọi, đọc bản ghi cuộc gọi có cấu trúc, hỏi lại và gọi tiếp khi cần, cuối cùng báo cáo cho người dùng. |
| 9-3 | [streaming-speech](streaming-speech/) | ✅ | Minh họa đánh đổi cốt lõi của cảm nhận giọng nói streaming: chia âm thanh liên tục thành các khối có độ dài tăng dần đưa vào ASR; mỗi khi nhận một đoạn nhỏ thì xuất “kết quả nhận dạng phần hiện tại” để có văn bản cực sớm với độ trễ gói đầu rất thấp. Cái giá là các khối ban đầu có thể sai do thiếu ngữ cảnh nửa sau câu; khi âm thanh tích lũy, kết quả dần hội tụ, đối chiếu với cách “đợi đủ cả câu rồi nhận dạng” có độ chính xác cao nhưng độ trễ cao. |
| 9-4 | [end-to-end-speech](end-to-end-speech/) | ✅ | Tương ứng với mô thức suy nghĩ bằng giọng nói đầu-cuối của Step-Audio R1 (một mô hình duy nhất “nghe → nghĩ → nói”): chạy thông vòng kín “đầu vào giọng nói → suy nghĩ → đầu ra giọng nói”, đồng thời so sánh trực quan với mô thức nối tầng ASR→LLM→TTS về độ trễ và mất mát thông tin cận ngôn ngữ (cảm xúc/ngữ điệu/tốc độ nói). |
| 9-5 | [controllable-tts](controllable-tts/) | ✅ | Cho đầu ra của LLM chính mang theo control tag (cảm xúc/tốc độ/phong cách/ngắt nghỉ/tiếng cười); tầng thực thi phân tích tag và ánh xạ sang profile phong cách tương ứng trong thư viện giọng tham chiếu rồi tổng hợp giọng nói. Quyết định “ngắt ở đâu, dùng giọng điệu nào” được giao cho LLM; cùng một đoạn văn bản có thể được tổng hợp thành nhiều phong cách và cảm xúc khác nhau. |
| 9-6 | `claude-quickstarts/` | 📖 | Ví dụ khởi đầu nhanh và best practice cho Claude API, bao phủ nhiều ngữ cảnh sử dụng. |
| 9-7 | `browser-use/` | 📖 | Browser-Use là framework tự động hóa trình duyệt mạnh mẽ, cho phép LLM điều khiển trình duyệt để hoàn thành nhiệm vụ phức tạp. Hỗ trợ điền form, điều hướng trang web, trích xuất dữ liệu và nhiều ngữ cảnh khác; đây là một triển khai điển hình của tự động hóa GUI (Computer Use). |

## Phân loại dự án

| Biểu tượng | Loại | Ý nghĩa |
| :--: | --- | --- |
| ✅ | **Chạy độc lập** | Có mã đầy đủ trong kho, chạy được sau khi cấu hình API Key |
| 📖 | **Hướng dẫn tái hiện** | Tài liệu chi tiết, cần `git clone` **kho ngoài** |
| 🚧 | **Tài liệu thiết kế** | Chỉ có kiến trúc/phương án, mã chạy được đang hoàn thiện |
