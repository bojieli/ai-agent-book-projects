# Chương 9 · Đa phương thức và tương tác thời gian thực

> mở rộng cảm nhận và hành động từ văn bản sang giọng nói, GUI và thế giới vật lý. Ba mô thức giọng nói (pipeline nối tầng/đa phương thức đầu cuối/full-duplex), cảm nhận và tổng hợp giọng nói dạng streaming, Computer Use và thao tác robot.

← [Về README chính](../docs/vi/README.md) · 📖 [Đọc nội dung chương](../book-vi/chapter9.vi.md)

## Dự án đi kèm

| Thí nghiệm | Project | Type | Description |
| :--: | --- | :--: | --- |
| 9-1 | [live-audio](live-audio/) | ✅ | Demo chat giọng nói thời gian thực, tích hợp speech-to-text, hội thoại AI và text-to-speech. Hỗ trợ nhiều nhà cung cấp dịch vụ AI (OpenAI, OpenRouter, ARK, Siliconflow), cung cấp trải nghiệm hội thoại độ trễ thấp. |
| Add-on | [phone-agent](phone-agent/) | 🚧 | Đã triển khai đường direct/ReAct của SDK `pine-voice` chính thức, nhưng chưa có đích E.164 được ủy quyền và đồng ý. Preflight ghi rõ không quay số/không transcript; test double không phải nghiệm thu. |
| 9-2 | [streaming-speech](streaming-speech/) | ✅ | Minh họa đánh đổi cốt lõi của cảm nhận giọng nói streaming: chia âm thanh liên tục thành các khối có độ dài tăng dần đưa vào ASR; mỗi khi nhận một đoạn nhỏ thì xuất “kết quả nhận dạng phần hiện tại” để có văn bản cực sớm với độ trễ gói đầu rất thấp. Cái giá là các khối ban đầu có thể sai do thiếu ngữ cảnh nửa sau câu; khi âm thanh tích lũy, kết quả dần hội tụ, đối chiếu với cách “đợi đủ cả câu rồi nhận dạng” có độ chính xác cao nhưng độ trễ cao. |
| 9-3 | [end-to-end-speech](end-to-end-speech/) | ✅ | MiniCPM-o 4.5 ở revision cố định đã chạy cục bộ thật trên một RTX PRO 6000; end-to-end và self-cascade cùng đạt 3/4 nhưng lỗi ngữ nghĩa/cận ngôn ngữ bổ sung cho nhau, kèm âm thanh 24kHz và bằng chứng nghiệm thu. |
| 9-4 | [controllable-tts](controllable-tts/) | 🚧 | Thư viện Fish Audio S1 thật 4×3×2 và media A/B/C đạt cổng cấu trúc; còn thiếu nghiên cứu nghe định tính và đánh giá “gần người thật”. |
| 9-5 | `claude-quickstarts/computer-use-demo/` | 📖 | `anthropics/claude-quickstarts` bên ngoài ghim tại `9bcc95e…`; nội dung sách dùng Computer Use demo với desktop Ubuntu＋vòng Claude agent trong container, không phải toàn bộ quickstarts. |
| 9-6 | `browser-use/` | 📖 | `browser-use/browser-use` bên ngoài ghim tại `ec9277c…`; visual CLI (`use_vision=True`) tìm thời tiết San Francisco trên Google và lưu trajectory action/screenshot. |
| 9-7 | [xlerobot-teleoperation](xlerobot-teleoperation/) | 📖 | Teleoperation XLeRobot thật cho cùng một nhiệm vụ dọn bàn: đặt cốc đỏ vào khay, giấy vàng vào thùng rác, rồi quan sát lại và xác minh trạng thái. |
| 9-8 | [gemini-xlerobot-navigation](gemini-xlerobot-navigation/) | 📖 | Đo giới hạn trên của điều khiển lý tưởng cho cùng nhiệm vụ trong simulator; không có nghĩa robot thật đã được chạy. |
| 9-9 | [gemini-xlerobot-navigation](gemini-xlerobot-navigation/) | 📖 | Gemini Robotics-ER 1.5 tự chủ điều khiển XLeRobot thật để hoàn thành cùng nhiệm vụ dọn bàn. |
| 9-10 | [gemini-xlerobot-navigation](gemini-xlerobot-navigation/) | 📖 | So sánh open-loop, kiểm tra từng bước và closed-loop dự đoán trong simulator cho cùng nhiệm vụ. |
| 9-11 | [rgb-sim2real-grasping](rgb-sim2real-grasping/) | 📖 | Kiểm thử RGB xuyên môi trường cho cùng nhiệm vụ với nền, ngoại hình vật thể, ánh sáng và nhiễu thị giác thay đổi. |

## Phân loại dự án

| Biểu tượng | Loại | Ý nghĩa |
| :--: | --- | --- |
| ✅ | **Chạy độc lập** | Có mã đầy đủ trong kho, chạy được sau khi cấu hình API Key |
| 📖 | **Hướng dẫn tái hiện** | Tài liệu chi tiết, cần `git clone` **kho ngoài** |
| 🚧 | **Đang thực hiện** | Đã có triển khai, nhưng còn thiếu chạy live, ủy quyền, phần cứng hoặc bằng chứng nghiệm thu theo nội dung sách |
