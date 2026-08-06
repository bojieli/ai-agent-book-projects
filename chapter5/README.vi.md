# Chương 5 · Coding Agent và sinh mã

> mã là “công cụ có thể tạo ra công cụ mới”, là siêu năng lực của Agent tổng quát. Lấy Coding Agent cấp sản xuất làm ví dụ để trình bày triển khai đầy đủ của công cụ tổng quát mạnh nhất này.

← [Về README chính](../docs/vi/README.md) · 📖 [Đọc nội dung chương](../book-vi/chapter5.vi.md)

## Dự án đi kèm

| Thí nghiệm | Project | Type | Description |
| :--: | --- | :--: | --- |
| 5-1 | [code-for-math](code-for-math/) | ✅ | Cho cùng một mô hình đối chiếu hai chế độ “chuỗi suy nghĩ thuần” và “có mã hỗ trợ” trên cùng một tập bài toán thi đấu: chế độ sau hình thức hóa đề thành Python (sympy/numpy/scipy), thực thi qua function calling trong sandbox tiến trình con, dùng tính toán chính xác thay cho tính nhẩm dễ sai, nhờ đó đạt độ chính xác cao hơn đáng kể. |
| 5-2 | [code-for-logic](code-for-logic/) | ✅ | Chuyển các câu đố logic “hiệp sĩ và kẻ nói dối” thành bài toán thỏa mãn ràng buộc (CSP): Agent dùng `python-constraint` để định nghĩa biến và ràng buộc hai chiều rồi gọi solver, so sánh độ đúng của hai chế độ suy luận ngôn ngữ tự nhiên thuần và có mã hỗ trợ trên một tập câu đố K&K. |
| 5-3 | [small-model-codified-rules](small-model-codified-rules/) | ✅ | Thí nghiệm đối chứng dựa trên ngữ cảnh chăm sóc khách hàng hàng không của τ-bench: sau khi chuyển chính sách nghiệp vụ phức tạp (quy tắc hoàn tiền) từ prompt ngôn ngữ tự nhiên vào mã/công cụ, tỷ lệ thành công nhiệm vụ và tính nhất quán chính sách của mô hình nhỏ tăng mạnh; kiểm tra bằng mã trong công cụ có thể chặn nhận thức sai của mô hình theo thời gian thực. |
| 5-4 | [paper-to-ppt](paper-to-ppt/) | ✅ | Tái cấu trúc “làm PPT” thành bài toán sinh mã: Proposer viết mã Slidev (Markdown+HTML), Reviewer render từng trang thành PNG thật và dùng Vision LLM kiểm tra vấn đề dàn trang, rồi lặp sửa theo phản hồi có cấu trúc; phân công hai Agent giúp đỉnh ngữ cảnh nhỏ hơn đáng kể. |
| 5-5 | [paper-to-video](paper-to-video/) | ✅ | Trên nền “bài báo → PPT”, sinh lời thuyết minh nói tự nhiên cho từng trang slide, gọi TTS để tổng hợp giọng nói, rồi dùng ffmpeg ghép ảnh chụp từng trang với âm thanh tương ứng thành một video thuyết minh có lồng tiếng. |
| 5-6 | [video-edit](video-edit/) | ✅ | Người dùng đưa một video nhiều cảnh + một yêu cầu ngôn ngữ tự nhiên; Agent dùng “định vị Vision hai bước” (trước lấy khung hình thô, sau tinh chỉnh đọc ảnh) để xác định ranh giới thời gian của cảnh mục tiêu, cắt đoạn rồi để Reviewer trích khung hình chính của thành phẩm để kiểm tra; nếu không đạt thì lặp lại. |
| 5-7 | [adaptive-log-parser](adaptive-log-parser/) | ✅ | Một hệ thống phân tích log có thể tự tiến hóa: khi gặp định dạng mới không phân tích được, hệ thống không báo lỗi dừng lại mà giao mẫu thất bại và lỗi cho Agent sinh mã để tạo hàm `parse`; sau khi tự động kiểm thử thành công, hàm được hot-update vào engine phân tích, toàn bộ quy trình không cần can thiệp thủ công. |
| 5-8 | [log-diagnosis](log-diagnosis/) | ✅ | Agent chẩn đoán đọc trajectory HTTP thật, tài liệu kiến trúc và PRD, sinh test hồi quy rồi phát lại trước/sau bản sửa; chiến dịch chính thức tạo Issue thật qua máy chủ GitHub MCP chính thức và lưu biên nhận đã loại thông tin xác thực. |
| 5-9 | [dynamic-form](dynamic-form/) | ✅ | Khi đối mặt với yêu cầu thiếu thông tin, Agent không hỏi từng câu một mà sinh động một biểu mẫu HTML tự chứa có logic liên kết để người dùng bổ sung một lần; frontend tổng hợp biểu mẫu thành JSON rồi trả lại Agent để tiếp tục nhiệm vụ. |
| 5-10 | [erp-agent](erp-agent/) | ✅ | Chuyển truy vấn tiếng Trung tự nhiên thành SQL để cơ sở dữ liệu thực thi và hiển thị trực tiếp bảng kết quả. Cốt lõi là mô thức artifact: LLM chỉ sinh artifact SQL, không tự vận chuyển dữ liệu; vừa tiết kiệm token vừa tránh sai do tính tay, ngay cả kết quả hàng chục nghìn dòng cũng trả về trong vài giây. |
| 5-11 | [conversational-ui](conversational-ui/) | ✅ | Người dùng nêu yêu cầu tùy biến UI bằng ngôn ngữ tự nhiên (màu sắc/phông chữ/nội dung/bố cục), Agent tự định vị và sửa mã nguồn frontend React, nhờ hot loading (HMR) của Vite để thay đổi có hiệu lực tức thì, hỗ trợ tùy biến lặp nhiều vòng. |
| 5-12 | [permission-embedded-data-objects](permission-embedded-data-objects/) | ✅ | Kho đối tượng trên PostgreSQL thực thi quyền, kiểm tra và tính toàn vẹn tham chiếu bên dưới mã ứng dụng được sinh động. |
| 5-13 | [agent-creator](agent-creator/) | ✅ | Agent siêu lập trình so sánh sửa đổi một triển khai tham chiếu đã được xác minh với sinh Agent từ đầu; cả hai nhánh đều được biên dịch, kiểm thử và chạy qua API gọi công cụ Kimi K3 thật. |

## Phân loại dự án

| Biểu tượng | Loại | Ý nghĩa |
| :--: | --- | --- |
| ✅ | **Chạy độc lập** | Có mã đầy đủ trong kho, chạy được sau khi cấu hình API Key |
| 📖 | **Hướng dẫn tái hiện** | Tài liệu chi tiết, cần `git clone` **kho ngoài** |
| 🚧 | **Tài liệu thiết kế** | Chỉ có kiến trúc/phương án, mã chạy được đang hoàn thiện |
