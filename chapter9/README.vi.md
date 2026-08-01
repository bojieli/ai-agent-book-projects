# Chương 9 · Đa phương thức và tương tác thời gian thực

> mở rộng cảm nhận và hành động từ văn bản sang giọng nói, GUI và thế giới vật lý. Ba mô thức giọng nói (pipeline nối tầng/đa phương thức đầu cuối/full-duplex), cảm nhận và tổng hợp giọng nói dạng streaming, Computer Use và thao tác robot.

← [Về README chính](../docs/vi/README.md) · 📖 [Đọc nội dung chương](../book-vi/chapter9.vi.md)

## Dự án đi kèm

| Thí nghiệm | Project | Type | Description |
| :--: | --- | :--: | --- |
| 9-1 | [live-audio](live-audio/) | ✅ | Demo chat giọng nói thời gian thực, tích hợp speech-to-text, hội thoại AI và text-to-speech. Hỗ trợ nhiều nhà cung cấp dịch vụ AI (OpenAI, OpenRouter, ARK, Siliconflow), cung cấp trải nghiệm hội thoại độ trễ thấp. |
| 9-2 | [phone-agent](phone-agent/) | 🚧 | Đã triển khai đường direct/ReAct của SDK `pine-voice` chính thức, nhưng chưa có đích E.164 được ủy quyền và đồng ý. Preflight ghi rõ không quay số/không transcript; test double không phải nghiệm thu. |
| 9-3 | [streaming-speech](streaming-speech/) | ✅ | Minh họa đánh đổi cốt lõi của cảm nhận giọng nói streaming: chia âm thanh liên tục thành các khối có độ dài tăng dần đưa vào ASR; mỗi khi nhận một đoạn nhỏ thì xuất “kết quả nhận dạng phần hiện tại” để có văn bản cực sớm với độ trễ gói đầu rất thấp. Cái giá là các khối ban đầu có thể sai do thiếu ngữ cảnh nửa sau câu; khi âm thanh tích lũy, kết quả dần hội tụ, đối chiếu với cách “đợi đủ cả câu rồi nhận dạng” có độ chính xác cao nhưng độ trễ cao. |
| 9-4 | [end-to-end-speech](end-to-end-speech/) | ✅ | MiniCPM-o 4.5 ở revision cố định đã chạy cục bộ thật trên một RTX PRO 6000; end-to-end và self-cascade cùng đạt 3/4 nhưng lỗi ngữ nghĩa/cận ngôn ngữ bổ sung cho nhau, kèm âm thanh 24kHz và bằng chứng nghiệm thu. |
| 9-5 | [controllable-tts](controllable-tts/) | 🚧 | Thư viện Fish Audio S1 thật 4×3×2 và media A/B/C đạt cổng cấu trúc; còn thiếu nghiên cứu nghe định tính và đánh giá “gần người thật”. |
| 9-6 | `claude-quickstarts/computer-use-demo/` | 📖 | `anthropics/claude-quickstarts` bên ngoài ghim tại `9bcc95e…`; nội dung sách dùng Computer Use demo với desktop Ubuntu＋vòng Claude agent trong container, không phải toàn bộ quickstarts. |
| 9-7 | `browser-use/` | 📖 | `browser-use/browser-use` bên ngoài ghim tại `ec9277c…`; visual CLI (`use_vision=True`) tìm thời tiết San Francisco trên Google và lưu trajectory action/screenshot. |
| 9-8 | [xlerobot-teleoperation](xlerobot-teleoperation/) | 📖 | XLeRobot bên ngoài `3d14695…` cho keyboard/Xbox/Joy-Con/VR. Chỉ có source/non-actuating preflight; chưa có run phần cứng bốn mode được phép hoặc bằng chứng pick/place/wipe. |
| 9-9 | [gemini-xlerobot-navigation](gemini-xlerobot-navigation/) | 📖 | XLeRobot bên ngoài `3d14695…`＋RoboCrew, dùng đúng `gemini-robotics-er-1.5-preview`, angle annotation và forward/left/right tools. Chưa có run robot navigation được phép. |
| 9-10 | [rgb-sim2real-grasping](rgb-sim2real-grasping/) | 📖 | `lerobot-sim2real` bên ngoài `87d6c1d…`, pipeline năm giai đoạn RGB→PPO→SO-100. Máy thiếu ManiSkill/NVIDIA và chưa có run robot vật lý được phép. |

## Phân loại dự án

| Biểu tượng | Loại | Ý nghĩa |
| :--: | --- | --- |
| ✅ | **Chạy độc lập** | Có mã đầy đủ trong kho, chạy được sau khi cấu hình API Key |
| 📖 | **Hướng dẫn tái hiện** | Tài liệu chi tiết, cần `git clone` **kho ngoài** |
| 🚧 | **Đang thực hiện** | Đã có triển khai, nhưng còn thiếu chạy live, ủy quyền, phần cứng hoặc bằng chứng nghiệm thu theo nội dung sách |
