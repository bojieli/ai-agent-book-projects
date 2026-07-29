# Chương 10 · Cộng tác đa Agent

> trí tuệ tập thể có thể cao hơn cá thể. Khung phân loại đa Agent, khi nào thực sự tốt hơn đơn Agent, cộng tác chia sẻ và không chia sẻ ngữ cảnh, các chế độ thất bại, cũng như “xã hội Agent” nổi lên.

← [Về README chính](../docs/vi/README.md) · 📖 [Đọc nội dung chương](../book-vi/chapter10.vi.md)

## Dự án đi kèm

| Thí nghiệm | Project | Type | Description |
| :--: | --- | :--: | --- |
| 10-1 | [staged-system-prompt](staged-system-prompt/) | ✅ | Cùng một Coding Agent tải system prompt và bộ công cụ khác nhau ở các giai đoạn thực thi khác nhau của nhiệm vụ (làm rõ yêu cầu → triển khai mã → review mã), nhờ đó trong một cuộc hội thoại có thể đóng các vai khác nhau và biểu hiện hành vi khác nhau; lịch sử hội thoại và trạng thái nhiệm vụ được chia sẻ liên tục giữa các giai đoạn, nếu review không đạt còn có thể quay lại giai đoạn triển khai. |
| 10-2 | [multi-role-transfer](multi-role-transfer/) | ✅ | Minh họa handoff dạng chuỗi trong ngữ cảnh chia sẻ: trong một phiên có nhiều Agent vai trò chuyên môn, mỗi Agent có system prompt và bộ công cụ chuyên biệt riêng; thông qua công cụ `transfer_to_agent`, Agent tự chủ phán đoán nên chuyển sang vai trò nào theo tiến triển nhiệm vụ. Vì cùng chia sẻ một lịch sử hội thoại, ngữ cảnh đầy đủ được giữ tự nhiên khi bàn giao. |
| 10-3 | [book-translation](book-translation/) | ✅ | Dùng mô thức quản lý (Orchestration) để chia bản dịch tài liệu dài cho các Agent chuyên trách như thuật ngữ/biên dịch/hiệu đính: Manager chỉ lưu nhiệm vụ, kế hoạch, bản ghi gọi và chỉ mục file; toàn bộ bản dịch được ghi ra đĩa, nên ngữ cảnh gần như ổn định. Đồng thời so sánh với phương án đơn Agent, dùng số token thật để giải thích cách kiểm soát phình ngữ cảnh và dùng bảng thuật ngữ chia sẻ để đảm bảo tính nhất quán toàn sách. |
| 10-4 | `use-computer-while-calling/` | 📖 | Triển khai kiến trúc cộng tác hai Agent gồm Agent gọi điện thoại và Agent sử dụng máy tính. Hai Agent giao tiếp trực tiếp qua WebSocket, không cần coordinator. Agent điện thoại xử lý tương tác giọng nói, Agent máy tính thực thi tự động hóa trình duyệt; hai bên làm việc song song để hoàn thành nhiệm vụ phức tạp cần cả giọng nói và thao tác web; code đã tách thành [TalkAct](https://github.com/19PINE-AI/TalkAct) độc lập, kho này không đóng gói thư mục này (lệnh clone xem phụ lục trong README chính). |
| 10-6 | [parallel-web-research](parallel-web-research/) | ✅ | Minh họa nhiều Agent đồng cấu tìm kiếm song song + điều phối trung tâm: coordinator chính đồng thời khởi động N sub-Agent, mỗi sub-Agent truy cập một nguồn để tìm câu trả lời; khi một bên tìm trúng mục tiêu, các bên còn lại dừng nhẹ nhàng ngay. Message bus, phân phối song song, giám sát thời gian thực, kết thúc dây chuyền và xử lý race condition đều được triển khai thật (dùng nguồn thông tin mô phỏng có kiểm soát thay cho trình duyệt thật). |
| 10-7 | `generative_agents/` | 📖 | Các Agent tạo sinh kiểu "thị trấn AI" của Stanford (dự án đi kèm Thí nghiệm 10-7); kho ngoài `joonspk-research/generative_agents`, cần tự clone (xem phụ lục trong README chính). |
| 10-8 | [voice-werewolf](voice-werewolf/) | ✅ | Dùng trò chơi Ma sói đa Agent để minh họa kiểm soát quyền thông tin khi “không chia sẻ ngữ cảnh”: mỗi người chơi là một LLM Agent độc lập và duy trì ngữ cảnh riêng được cách ly nghiêm ngặt; trọng tài xác định do mã điều khiển sẽ quyết định mỗi thông tin được gửi vào ngữ cảnh của người chơi nào và ghi audit, sau khi game kết thúc tự động kiểm tra cách ly có đúng không. Giọng nói là phần tăng cường tùy chọn. |

## Phân loại dự án

| Biểu tượng | Loại | Ý nghĩa |
| :--: | --- | --- |
| ✅ | **Chạy độc lập** | Có mã đầy đủ trong kho, chạy được sau khi cấu hình API Key |
| 📖 | **Hướng dẫn tái hiện** | Tài liệu chi tiết, cần `git clone` **kho ngoài** |
| 🚧 | **Tài liệu thiết kế** | Chỉ có kiến trúc/phương án, mã chạy được đang hoàn thiện |
