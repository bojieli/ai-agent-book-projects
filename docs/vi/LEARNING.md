# Gợi ý học tập

← [Về README chính](README.md)

### Tư tưởng cốt lõi: Agent = mô hình + context + tools

Khung cốt lõi của sách là **Agent = mô hình + context + tools**. Ba thành phần này phối hợp với nhau để hiện thực hành vi thông minh của Agent:

- **Mô hình (Model)**: bộ não của Agent, cung cấp năng lực hiểu, suy luận và ra quyết định
- **Ngữ cảnh (Context)**: hệ điều hành của Agent, bao gồm chỉ dẫn hệ thống, lịch sử hội thoại, quá trình suy luận, bản ghi tương tác công cụ, v.v.
- **Công cụ (Tools)**: đôi tay của Agent, giúp Agent cảm nhận môi trường, thực thi thao tác và tương tác với thế giới bên ngoài

### Lộ trình học

Lộ trình học tương ứng một-một với các chương của sách, triển khai từng lớp quanh ba trụ cột lớn:

- **Chương 1 · Phần nền tảng**: xây dựng khung nhận thức hoàn chỉnh về hệ thống Agent — hiểu định nghĩa Agent trong RL, so sánh khác biệt về hiệu quả mẫu giữa RL truyền thống và mô thức LLM+RL, hiểu mô hình mới “model as Agent”, nắm vững khung cốt lõi **Agent = mô hình + context + tools**. **Insight then chốt**: tầm quan trọng của tri thức tiên nghiệm vượt qua thuật toán và môi trường.

- **Chương 2–3 · Phần ngữ cảnh**: ngữ cảnh là hệ điều hành của Agent. Chương 2 bao phủ system prompt, thiết kế thân thiện KV Cache, nén ngữ cảnh và ablation prompt engineering; chương 3 bao phủ bộ nhớ người dùng, truy xuất dày đặc/thưa/lai, Agentic RAG, truy xuất nhận biết ngữ cảnh và trích xuất tri thức có cấu trúc. **Insight then chốt**: ngữ cảnh hoàn chỉnh bao gồm chỉ dẫn hệ thống, lịch sử hội thoại, quá trình suy luận, bản ghi tương tác công cụ, bộ nhớ người dùng và tri thức bên ngoài.

- **Chương 4–5 · Phần công cụ**: công cụ là cây cầu để Agent tương tác với thế giới. Chương 4 bao phủ ba loại công cụ MCP cảm nhận/thực thi/cộng tác, kích hoạt sự kiện và kiến trúc bất đồng bộ; chương 5 đi sâu vào triển khai đầy đủ Coding Agent cấp sản xuất. **Insight then chốt**: thiết kế công cụ nên tổng quát hóa (code interpreter tốt hơn calculator); mã là siêu năng lực có thể tạo ra công cụ mới.

- **Chương 6–7 · Phần mô hình**: cách đo lường và phóng đại trí tuệ. Chương 6 bao phủ các benchmark đánh giá như Terminal-Bench, SWE-bench, GAIA, OSWorld, Tau2-Bench; chương 7 bao phủ các kỹ thuật hậu huấn luyện như SFT, RL, RLHF và hiệu quả mẫu. **Insight then chốt**: tín hiệu xác minh độc lập đáng tin cậy hơn “để mô hình nghĩ lại một lần”; “model as Agent” dùng RL để nội hóa gọi công cụ thành năng lực nguyên sinh.

- **Chương 8 · Phần tự tiến hóa**: giúp Agent trưởng thành từ kinh nghiệm mà không cần đổi trọng số — học từ kinh nghiệm, ngoại hóa workflow thành công cụ, chưng cất prompt và quan sát vào tham số. **Insight then chốt**: học từ kinh nghiệm là chìa khóa để Agent đi từ “thông minh” tới “thành thạo”.

- **Chương 9–10 · Phần mở rộng và cộng tác**: chương 9 mở rộng cảm nhận và hành động từ văn bản sang giọng nói, GUI và thế giới vật lý; chương 10 xử lý nhiệm vụ phức tạp thông qua phân công cộng tác đa Agent. **Insight then chốt**: mọi quyết định thiết kế trong hệ thống đa Agent đều có thể tìm thấy đối ứng trong ba yếu tố của đơn Agent.

## Phân công giữa văn bản và thí nghiệm

Cuốn sách không phải hướng dẫn từng bước cho một SDK cụ thể. Pseudocode và skeleton chỉ ra luồng trạng thái, điểm dừng và ranh giới kiểm chứng; thí nghiệm cung cấp triển khai, adapter, test, log và bằng chứng.

| Layer | Read first | Skip for now | Question it answers |
| :--: | --- | --- | --- |
| **Starter** | Project README: goal, minimum command, acceptance conditions; matching prose skeleton | credentials, UI, provider adapters, long raw logs | Thí nghiệm này nhằm chứng minh cơ chế nào? |
| **Builder** | entry point, core loop, state/message schema, tools, verifier | compatibility/deployment layers unrelated to the mechanism | Biến nào đã làm thay đổi hành vi? |
| **Maintainer** | tests, failure handling, evidence format, manifest/hash, rollback path | third-party details needed only when changing the experiment | Kết quả có tái lập được không và lỗi có được ghi nhận trung thực không? |

### Phân cấp độ khó

- **Nhập môn** (Chương 1–2): phù hợp với người mới bắt đầu, hiểu khái niệm cơ bản
- **Nâng cao** (Chương 3–4): cần nền tảng lập trình nhất định, liên quan đến tích hợp hệ thống
- **Cao cấp** (Chương 5–6): cần năng lực lập trình mạnh hơn, liên quan đến thiết kế hệ thống phức tạp
- **Chuyên gia** (Chương 7–8): cần kinh nghiệm học sâu và huấn luyện/tự tiến hóa
- **Ứng dụng** (Chương 9–10): tổng hợp kiến thức đã học để xây dựng ứng dụng thực tế

### Gợi ý thực hành

1. **Tự tay thực hành**: mỗi dự án đều được thiết kế để có thể chạy độc lập; khuyến nghị tự chạy và sửa mã
2. **Kết hợp với sách**: đọc cùng các chương tương ứng trong bản thảo tại [`book/`](../../book/) để hiểu sự kết hợp giữa lý thuyết và thực hành
3. **So sánh thí nghiệm**: nhiều dự án chứa nghiên cứu ablation và thí nghiệm đối chứng; hãy dùng so sánh để hiểu sâu hơn
4. **Học tăng dần**: bắt đầu từ dự án đơn giản rồi dần đi sâu vào hệ thống phức tạp
5. **Chú ý giao thức**: các dự án MCP server ở chương 4 minh họa giao thức công cụ chuẩn hóa, đây là chìa khóa để xây dựng Agent có thể mở rộng
