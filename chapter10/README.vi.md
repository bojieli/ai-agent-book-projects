# Chương 10 · Cộng tác đa Agent

> trí tuệ tập thể có thể cao hơn cá thể. Khung phân loại đa Agent, khi nào thực sự tốt hơn đơn Agent, cộng tác chia sẻ và không chia sẻ ngữ cảnh, các chế độ thất bại, cũng như “xã hội Agent” nổi lên.

← [Về README chính](../docs/vi/README.md) · 📖 [Đọc nội dung chương](../book-vi/chapter10.vi.md)

## Cách đọc các thí nghiệm

Phần văn bản dùng skeleton cơ chế ngắn để giải thích luồng điều khiển; thư mục thí nghiệm chứa adapter SDK đầy đủ, log, kiểm thử và bằng chứng nghiệm thu. Không cần đọc từng tệp theo từng dòng.

- **Starter:** Bắt đầu từ mục tiêu, lệnh tối thiểu và điều kiện nghiệm thu; hãy bắt đầu với [parallel-web-research](parallel-web-research/);
- **Builder:** Lần theo điểm vào, vòng lặp lõi, schema trạng thái/tin nhắn, công cụ và verifier.
- **Maintainer:** Sau đó đọc test, manifest bằng chứng, xử lý lỗi, đường rollback và adapter nhà cung cấp.

Lần đầu có thể bỏ qua credential, lớp trình bày và tương thích provider; quay lại khi cần tái tạo số liệu.

## Dự án đi kèm

| Thí nghiệm | Project | Type | Description |
| :--: | --- | :--: | --- |
| 10-1 | [multi-role-transfer](multi-role-transfer/) | ✅ | Minh họa handoff dạng chuỗi trong ngữ cảnh chia sẻ: trong một phiên có nhiều Agent vai trò chuyên môn, mỗi Agent có system prompt và bộ công cụ chuyên biệt riêng; thông qua công cụ `transfer_to_agent`, Agent tự chủ phán đoán nên chuyển sang vai trò nào theo tiến triển nhiệm vụ. Vì cùng chia sẻ một lịch sử hội thoại, ngữ cảnh đầy đủ được giữ tự nhiên khi bàn giao. |
| 10-2 | [book-translation](book-translation/) | 🚧 | Manager bốn vai trò và đối chứng một Agent đã có mẫu nhỏ chạy bằng model thật. Nghiệm thu chính xác vẫn cần cuốn sách kỹ thuật nhiều hình/mã như nội dung sách yêu cầu và so sánh đầy đủ chất lượng, hiệu suất, token, tài nguyên. |
| 10-3 | `use-computer-while-calling/` + [autonomous-phone-registration](autonomous-phone-registration/) | 📖 / 🚧 | [TalkAct](https://github.com/19PINE-AI/TalkAct) bên ngoài, ghim tại commit `7d70007…`: các Agent fast/slow thực sự chạy đồng thời và chia sẻ bảng đen `SharedState` trong cùng tiến trình (rolling digest, transcript/action log) cùng hàng đợi văn bản hai chiều. Phiên bản này không phải cầu WebSocket. Checkout không được đóng gói; xem phụ lục README chính để có lệnh clone và entrypoint benchmark chính xác. Playwright quan sát biểu mẫu thật và LLM thật tự quyết định gọi `initiate_phone_call_agent`; đường Twilio/âm thanh cục bộ có cổng xác nhận đồng ý hỗ trợ kiểm tra, hỏi lại, hỏi/điền song song, trace đã ẩn dữ liệu và chỉ submit khi bật cờ. Bằng chứng hiện tại chỉ xác nhận trình duyệt/LLM/tính đồng thời bằng câu trả lời scripted; PSTN và âm thanh người thật vẫn là `not_run`, nên nghiệm thu trực tiếp chưa hoàn tất. |
| 10-4 | [parallel-web-research](parallel-web-research/) | ✅ | N phiên Playwright độc lập tìm kiếm mười website đại học thật, còn LLM thật trích xuất bằng chứng có thể dẫn nguồn. Bằng chứng nghiệm thu lưu giám sát, cô lập timeout/error, quyết toán một lần, xác nhận dừng dây chuyền, dọn tài nguyên và mức tăng tốc song song cùng site 3.142×. |
| 10-5 | `generative_agents/` | 📖 | Các Agent tạo sinh kiểu "thị trấn AI" của Stanford (dự án đi kèm Thí nghiệm 10-5); kho ngoài `joonspk-research/generative_agents`, cần tự clone (xem phụ lục trong README chính). |
| 10-6 | [voice-werewolf](voice-werewolf/) | 🚧 | Thêm trình mô phỏng người dùng LLM thật chỉ thấy ngữ cảnh ghế mình, phải gọi công cụ và chỉ vào game qua âm thanh tổng hợp cùng ASR âm thanh OpenRouter thật. Tái xác thực nghiêm ngặt bác hai lần chạy sớm nhầm bản chép lỗi là bỏ phiếu trắng; v2 hợp lệ vượt E2E, cách ly, thắng theo luật và ba chu kỳ, nhưng thất bại chiến lược vì dân làng trục xuất nhầm nhà tiên tri. |

## Phân loại dự án

| Biểu tượng | Loại | Ý nghĩa |
| :--: | --- | --- |
| ✅ | **Chạy độc lập** | Có mã đầy đủ trong kho, chạy được sau khi cấu hình API Key |
| 📖 | **Hướng dẫn tái hiện** | Tài liệu chi tiết, cần `git clone` **kho ngoài** |
| 🚧 | **Đang hoàn thiện** | Phần triển khai hoặc bằng chứng nghiệm thu bắt buộc chưa đầy đủ; có mã chạy được không đồng nghĩa đã nghiệm thu hoàn chỉnh |
