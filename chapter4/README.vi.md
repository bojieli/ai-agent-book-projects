# Chương 4 · Công cụ

> công cụ là đôi tay của Agent. Trình bày phân loại công cụ và nguyên tắc thiết kế tổng quát, giao thức MCP và thách thức chọn công cụ, ba loại công cụ cảm nhận/thực thi/cộng tác, cũng như Agent bất đồng bộ hướng sự kiện.

← [Về README chính](../docs/vi/README.md) · 📖 [Đọc nội dung chương](../book-vi/chapter4.vi.md)

## Dự án đi kèm

| Thí nghiệm | Project | Type | Description |
| :--: | --- | :--: | --- |
| 4-1 | [perception-tools](perception-tools/) | ✅ | Xây dựng bộ công cụ cảm nhận toàn diện, cung cấp khả năng tìm kiếm web, hiểu đa phương thức, thao tác hệ thống tệp và truy cập nguồn dữ liệu công cộng. Phần lớn chức năng dựa trên API mở miễn phí (DuckDuckGo, Open-Meteo, Yahoo Finance, OpenStreetMap, v.v.) và không cần API key. |
| 4-2 | [multimodal-agent](multimodal-agent/) | ✅ | Multimodal processing: compare native multimodal, extract-to-text, and tool-based analysis. |
| 4-3 | [execution-tools](execution-tools/) | ✅ | Triển khai bộ công cụ thực thi có cơ chế an toàn, bao gồm thao tác file, code interpreter, terminal ảo và tích hợp hệ thống bên ngoài. Dùng cơ chế phê duyệt lần hai bằng LLM để ngăn thao tác nguy hiểm, tự động tóm tắt đầu ra phức tạp và kiểm tra cú pháp mã. |
| 4-4 | [collaboration-tools](collaboration-tools/) | ✅ | Cung cấp năng lực cộng tác toàn diện, gồm tự động hóa trình duyệt (framework browser-use), phối hợp người-máy (Human-in-the-Loop), thông báo đa kênh (Email, Telegram, Slack, Discord) và quản lý bộ hẹn giờ. Hỗ trợ phê duyệt quản trị viên cho thao tác nhạy cảm và lập lịch tác vụ định kỳ. |
| 4-5 | [agent-with-event-trigger](agent-with-event-trigger/) | ✅ | Agent hướng sự kiện hiện đại xây dựng trên FastAPI, mặc định tích hợp toàn bộ công cụ của ba MCP server phía trên. Dùng kiến trúc bất đồng bộ nguyên sinh để tải công cụ MCP rõ ràng; nhận sự kiện đa nguồn qua HTTP API (Web, tin nhắn tức thời, GitHub, timer, v.v.). Cung cấp tài liệu API tự động (Swagger UI) và khả năng giám sát nền. |
| 4-6 | [async-agent](async-agent/) | ✅ | Triển khai lõi framework Agent bất đồng bộ hướng sự kiện (Flux) dựa trên asyncio một luồng: hàng đợi sự kiện inbox phân phối theo mức khẩn cấp (ngắt/ngay lập tức/xếp hàng), hỗ trợ công cụ bất đồng bộ chạy song song, ngắt turn hiện tại trong lúc đang chạy, đồng thời hủy và truy vấn trạng thái các tác vụ dài mô phỏng. Quyết định được thực hiện bởi LLM thật (function calling). |
| 4-7 | [active-tool-discovery](active-tool-discovery/) | ✅ | So sánh hai mô thức “nhồi toàn bộ hơn 120 tool schema” và “chủ động phát hiện theo nhu cầu”: mô thức sau chỉ giữ một số ít công cụ nền tảng + một meta-tool `discover_tools` trong system, dùng độ tương tự embedding để truy xuất 3–5 công cụ chuyên dụng liên quan nhất từ thư viện công cụ, vừa tiết kiệm token vừa tránh mô hình chọn sai/lạm dụng công cụ chung khi danh sách công cụ quá dài. |
| — | [active-tool-selection](active-tool-selection/) | ✅ | Triển khai cơ chế chọn công cụ thông minh, giúp Agent chủ động chọn tổ hợp công cụ phù hợp nhất theo nhu cầu nhiệm vụ, thay vì thụ động tiếp nhận bộ công cụ định nghĩa sẵn. |

## Phân loại dự án

| Biểu tượng | Loại | Ý nghĩa |
| :--: | --- | --- |
| ✅ | **Chạy độc lập** | Có mã đầy đủ trong kho, chạy được sau khi cấu hình API Key |
| 📖 | **Hướng dẫn tái hiện** | Tài liệu chi tiết, cần `git clone` **kho ngoài** |
| 🚧 | **Tài liệu thiết kế** | Chỉ có kiến trúc/phương án, mã chạy được đang hoàn thiện |
