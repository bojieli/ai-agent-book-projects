# Chương 6 · Tương tác: mở rộng không gian quan sát và không gian hành động

> mở rộng cảm nhận và hành động từ văn bản sang giọng nói, GUI và thế giới vật lý. Ba mô thức giọng nói (pipeline nối tầng/đa phương thức đầu cuối/full-duplex), cảm nhận và tổng hợp giọng nói dạng streaming, Computer Use và thao tác robot.

← [Về README chính](../docs/vi/README.md) · 📖 [Đọc nội dung chương](../book-vi/chapter6.vi.md)

## Cách đọc các thí nghiệm

Phần văn bản dùng skeleton cơ chế ngắn để giải thích luồng điều khiển; thư mục thí nghiệm chứa adapter SDK đầy đủ, log, kiểm thử và bằng chứng nghiệm thu. Không cần đọc từng tệp theo từng dòng.

- **Starter:** Bắt đầu từ mục tiêu, lệnh tối thiểu và điều kiện nghiệm thu; hãy bắt đầu với [live-audio](live-audio/);
- **Builder:** Lần theo điểm vào, vòng lặp lõi, schema trạng thái/tin nhắn, công cụ và verifier.
- **Maintainer:** Sau đó đọc test, manifest bằng chứng, xử lý lỗi, đường rollback và adapter nhà cung cấp.

Lần đầu có thể bỏ qua credential, lớp trình bày và tương thích provider; quay lại khi cần tái tạo số liệu.

## Dự án đi kèm

| Thí nghiệm | Project | Type | Description |
| :--: | --- | :--: | --- |
| 6-1 | [agent-with-event-trigger](agent-with-event-trigger/) | ✅ | Agent hướng sự kiện hiện đại xây dựng trên FastAPI, mặc định tích hợp toàn bộ công cụ của ba MCP server phía trên. Dùng kiến trúc bất đồng bộ nguyên sinh để tải công cụ MCP rõ ràng; nhận sự kiện đa nguồn qua HTTP API (Web, tin nhắn tức thời, GitHub, timer, v.v.). Cung cấp tài liệu API tự động (Swagger UI) và khả năng giám sát nền. |
| 6-2 | [async-agent](async-agent/) | ✅ | Triển khai lõi framework Agent bất đồng bộ hướng sự kiện (Flux) dựa trên asyncio một luồng: hàng đợi sự kiện inbox phân phối theo mức khẩn cấp (ngắt/ngay lập tức/xếp hàng), hỗ trợ công cụ bất đồng bộ chạy song song, ngắt turn hiện tại trong lúc đang chạy, đồng thời hủy và truy vấn trạng thái các tác vụ dài mô phỏng. Quyết định được thực hiện bởi LLM thật (function calling). |
| 6-3 | [live-audio](live-audio/) | ✅ | Demo chat giọng nói thời gian thực, tích hợp speech-to-text, hội thoại AI và text-to-speech. Hỗ trợ nhiều nhà cung cấp dịch vụ AI (OpenAI, OpenRouter, ARK, Siliconflow), cung cấp trải nghiệm hội thoại độ trễ thấp. |
| Add-on | [phone-agent](phone-agent/) | 🚧 | Đã triển khai đường direct/ReAct của SDK `pine-voice` chính thức, nhưng chưa có đích E.164 được ủy quyền và đồng ý. Preflight ghi rõ không quay số/không transcript; test double không phải nghiệm thu. |
| 6-4 | [streaming-speech](streaming-speech/) | ✅ | Minh họa đánh đổi cốt lõi của cảm nhận giọng nói streaming: chia âm thanh liên tục thành các khối có độ dài tăng dần đưa vào ASR; mỗi khi nhận một đoạn nhỏ thì xuất “kết quả nhận dạng phần hiện tại” để có văn bản cực sớm với độ trễ gói đầu rất thấp. Cái giá là các khối ban đầu có thể sai do thiếu ngữ cảnh nửa sau câu; khi âm thanh tích lũy, kết quả dần hội tụ, đối chiếu với cách “đợi đủ cả câu rồi nhận dạng” có độ chính xác cao nhưng độ trễ cao. |
| 6-5 | [end-to-end-speech](end-to-end-speech/) | ✅ | MiniCPM-o 4.5 ở revision cố định đã chạy cục bộ thật trên một RTX PRO 6000; end-to-end và self-cascade cùng đạt 3/4 nhưng lỗi ngữ nghĩa/cận ngôn ngữ bổ sung cho nhau, kèm âm thanh 24kHz và bằng chứng nghiệm thu. |
| 6-6 | [controllable-tts](controllable-tts/) | 🚧 | Thư viện Fish Audio S1 thật 4×3×2 và media A/B/C đạt cổng cấu trúc; còn thiếu nghiên cứu nghe định tính và đánh giá “gần người thật”. |
| 6-7 | `claude-quickstarts/computer-use-demo/` | 📖 | `anthropics/claude-quickstarts` bên ngoài ghim tại `9bcc95e…`; nội dung sách dùng Computer Use demo với desktop Ubuntu＋vòng Claude agent trong container, không phải toàn bộ quickstarts. |
| 6-8 | `browser-use/` | 📖 | `browser-use/browser-use` bên ngoài ghim tại `ec9277c…`; visual CLI (`use_vision=True`) tìm thời tiết San Francisco trên Google và lưu trajectory action/screenshot. |
| 6-9 | [xlerobot-teleoperation](xlerobot-teleoperation/) | 📖 | Teleoperation XLeRobot thật cho cùng một nhiệm vụ dọn bàn: đặt cốc đỏ vào khay, giấy vàng vào thùng rác, rồi quan sát lại và xác minh trạng thái. |
| 6-10 | [gemini-xlerobot-navigation](gemini-xlerobot-navigation/) | 📖 | Đo giới hạn trên của điều khiển lý tưởng cho cùng nhiệm vụ trong simulator; không có nghĩa robot thật đã được chạy. |
| 6-11 | [gemini-xlerobot-navigation](gemini-xlerobot-navigation/) | 📖 | Gemini Robotics-ER 1.5 tự chủ điều khiển XLeRobot thật để hoàn thành cùng nhiệm vụ dọn bàn. |
| 6-12 | [gemini-xlerobot-navigation](gemini-xlerobot-navigation/) | 📖 | So sánh open-loop, kiểm tra từng bước và closed-loop dự đoán trong simulator cho cùng nhiệm vụ. |
| 6-13 | [rgb-sim2real-grasping](rgb-sim2real-grasping/) | 📖 | Kiểm thử RGB xuyên môi trường cho cùng nhiệm vụ với nền, ngoại hình vật thể, ánh sáng và nhiễu thị giác thay đổi. |

## Phân loại dự án

| Biểu tượng | Loại | Ý nghĩa |
| :--: | --- | --- |
| ✅ | **Chạy độc lập** | Có mã đầy đủ trong kho, chạy được sau khi cấu hình API Key |
| 📖 | **Hướng dẫn tái hiện** | Tài liệu chi tiết, cần `git clone` **kho ngoài** |
| 🚧 | **Đang thực hiện** | Đã có triển khai, nhưng còn thiếu chạy live, ủy quyền, phần cứng hoặc bằng chứng nghiệm thu theo nội dung sách |
