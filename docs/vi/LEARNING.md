# Gợi ý học tập

← [Về README chính](README.md)

## Tư tưởng cốt lõi: Agent = LLM + context + tools

Công thức cốt lõi của sách là **Agent = LLM + context + tools**. Chương 1 giải thích cùng một Agent ở ba tầng: tầng hiện thực là công thức này, tầng trực giác là «bộ não + đôi mắt + tay chân», còn tầng học thuật tương ứng với chính sách (Policy), không gian quan sát (Observation Space) và không gian hành động (Action Space).

| Thành phần | Ví von | Vai trò |
| :--: | :--: | --- |
| 🧠 **LLM** | Bộ não | Cung cấp năng lực hiểu, suy luận và ra quyết định |
| 👁️ **Ngữ cảnh (Context)** | Đôi mắt | Toàn bộ thông tin Agent nhìn thấy tại mỗi điểm ra quyết định: system prompt, định nghĩa công cụ, tin nhắn người dùng, phản hồi mô hình, kết quả thực thi công cụ |
| 🤲 **Công cụ (Tools)** | Tay chân | Cảm nhận môi trường, thực thi thao tác và tương tác với thế giới bên ngoài |

Khi đưa vào môi trường sản xuất, chương 1 viết lại cùng hệ thống đó thành **Agent = Model + Harness**, trong đó **Harness = quản lý ngữ cảnh + giao diện công cụ + ràng buộc + kiểm chứng + hiệu chỉnh**. Ba mục sau chính là khoảng cách giữa một bản demo chạy được và một sản phẩm đáng tin cậy.

## Lộ trình học

Phần «Dẫn nhập» đưa ra bố cục tổng thể: **chương 1–6 dựng nên phương pháp hoàn chỉnh để xây dựng một Agent; chương 7–10 bàn về việc nâng cao năng lực theo bốn hướng — đánh giá, hậu huấn luyện, tiến hóa liên tục và cộng tác đa Agent.** Mỗi chương kèm một insight then chốt:

| Phần | Chương | Nội dung bao phủ | Insight then chốt |
| --- | :--: | --- | --- |
| **Xây dựng** | 1 | Ba yếu tố của Agent, vòng lặp ReAct, mẫu điều phối (workflow và tự chủ), kỹ thuật Harness | Khoảng cách giữa bản demo chạy được và sản phẩm đáng tin cậy nằm ở Harness, không nằm ở mô hình |
| | 2 | Cấu trúc message của API, KV Cache, prompt engineering và phòng thủ prompt injection, Agent Skills, thanh trạng thái Agent, nén ngữ cảnh | Chương quan trọng nhất của sách; ngữ cảnh quyết định trần năng lực, prefix càng ổn định thì tỉ lệ trúng cache càng cao |
| | 3 | Bốn chiến lược tiệm tiến cho bộ nhớ người dùng, ngăn xếp RAG, tổ chức và truy xuất tri thức, Agentic RAG, bộ nhớ đa phương thức | Mở rộng ngữ cảnh từ một phiên đơn lẻ thành tri thức tích lũy xuyên phiên |
| | 4 | Năm loại công cụ (cảm nhận / thực thi / cộng tác / kích hoạt sự kiện / giao tiếp người dùng), MCP, nguyên tắc thiết kế chung, khám phá công cụ chủ động | Công cụ cảm nhận kiểm soát lượng thông tin, công cụ thực thi kiểm soát rủi ro; thiết kế công cụ nên tổng quát hóa |
| | 5 | Coding Agent cộng hệ thống tệp, kiến trúc OpenClaw, sáu hướng của mã như một siêu năng lực | Mã không chỉ là viết chương trình, mà là siêu năng lực tạo ra công cụ mới ngay lúc chạy |
| | 6 | Hai trục, phương thức × thời gian: bất đồng bộ và hướng sự kiện, giọng nói, Computer Use, thao tác robot | Bốn loại tương tác dùng chung một bộ nguyên hàm hệ thống: đánh thức, điểm an toàn, hủy, chiếm quyền, tách đường nhanh/chậm |
| **Nâng cao** | 7 | Môi trường đánh giá, hệ chỉ số, thiết kế tập dữ liệu, LLM-as-a-Judge, ý nghĩa thống kê, khả năng quan sát, môi trường mô phỏng | Không có đánh giá thì không phân biệt được «cải thiện do thiết kế» với «dao động ngẫu nhiên» |
| | 8 | Toàn cảnh bốn giai đoạn, mid-training / SFT / RL, thiết kế phần thưởng, gán tín dụng đa lượt, chưng cất | SFT ghi nhớ, RL tổng quát hóa; dữ liệu và môi trường quan trọng hơn thuật toán |
| | 9 | Tín hiệu học (kết quả môi trường / quy tắc quy trình / LLM Rubric), bốn vật mang cập nhật — tri thức, chỉ dẫn, chương trình, tham số — cùng phát hành từng phần và rollback | Vật mang cập nhật phụ thuộc vào cách năng lực được biểu đạt và kiểm chứng |
| | 10 | Khung phân loại (ngữ cảnh chia sẻ hay tách biệt × ngang hàng / quản lý / phi tập trung), giao thức A2A, sáu chế độ thất bại, xã hội Agent | Mọi quyết định thiết kế đa Agent đều tìm được đối ứng trong ba yếu tố của đơn Agent |

## Phân công giữa văn bản và thí nghiệm

Cuốn sách không phải hướng dẫn từng bước cho một SDK cụ thể. Pseudocode và skeleton trong sách chỉ trả lời «trạng thái chảy ra sao, bước nào có thể dừng, loại tín hiệu nào tham gia kiểm chứng»; thí nghiệm từng chương cung cấp triển khai đầy đủ, adapter mô hình/môi trường, test, log và bằng chứng. Khi đọc thí nghiệm bạn không cần hiểu từng dòng của từng tệp, và cũng không nên coi cách viết API cụ thể của một thí nghiệm là kiến trúc tổng quát.

Nên đọc theo ba tầng dưới đây; với chương phức tạp, hãy chọn vài thí nghiệm cơ chế ở cùng một tầng thay vì chỉ chạy một dự án:

| Tầng | Đọc trước | Tạm bỏ qua | Câu hỏi mà nó trả lời |
| :--: | --- | --- | --- |
| **Starter** | README dự án: mục tiêu, lệnh tối thiểu và điều kiện nghiệm thu; skeleton tương ứng trong sách | thông tin xác thực, UI, adapter provider và log thô dài | Thí nghiệm này nhằm chứng minh cơ chế nào? |
| **Builder** | điểm vào, vòng lặp lõi, schema state/message, tool và verifier | các lớp tương thích/triển khai không liên quan đến cơ chế | Biến nào đã làm thay đổi hành vi? |
| **Maintainer** | test, xử lý lỗi, định dạng bằng chứng, manifest/hash và đường rollback | chi tiết bên thứ ba chỉ cần khi sửa thí nghiệm | Kết quả có tái lập được không và lỗi có được ghi nhận trung thực không? |

README của mỗi chương đã ghi rõ điểm vào Starter của chương đó. Nhóm đầu tiên được khuyến nghị là: chương 1 `context`, chương 2 `context-compression`, chương 3 `user-memory`, chương 4 `execution-tools`, chương 5 `coding-agent`, chương 6 `live-audio`, chương 7 `tau2-bench-eval`, chương 8 `cot-distillation`, chương 9 `trajectory-verifier`, chương 10 `parallel-web-research`. Code map trong mỗi thư mục sẽ đánh dấu Run first, Core behavior, Verifier và những phần có thể bỏ qua ở lần đọc đầu.

## Phân cấp độ khó

| Cấp độ | Chương | Phù hợp với |
| --- | :--: | --- |
| 🟢 Nhập môn | 1–2 | Người mới bắt đầu; chỉ cần nền tảng Python và kinh nghiệm dùng LLM |
| 🔵 Nâng cao | 3–4 | Có nền tảng lập trình nhất định; liên quan hệ thống truy xuất và tích hợp công cụ |
| 🟣 Cao cấp | 5–6 | Năng lực lập trình mạnh, thiết kế hệ thống phức tạp; chương 6 nên biết HTTP/WebSocket |
| 🟡 Kỹ thuật | 7 | Hạ tầng đánh giá và phương pháp thống kê — nặng về kỹ thuật, nhẹ về toán |
| 🔴 Chuyên gia | 8 | Chương duy nhất trong sách đòi hỏi kinh nghiệm học sâu và huấn luyện mô hình |
| 🟠 Ứng dụng | 9–10 | Tổng hợp toàn bộ phần trước để xây vòng lặp tiến hóa liên tục và hệ thống đa Agent |

Các thí nghiệm và câu hỏi trong sách còn có mức độ khó theo sao: ★ nhập môn, phù hợp mọi bạn đọc; ★★ trung bình, cần một chút kinh nghiệm thực hành kỹ thuật; ★★★ thử thách nâng cao, thường là bài toán mở hoặc thiết kế hệ thống phức tạp.

## Gợi ý thực hành

| # | Gợi ý | Diễn giải |
| :--: | --- | --- |
| 1 | 🛠️ **Tự tay thực hành** | Mỗi dự án đều được thiết kế để chạy độc lập; hãy tự chạy và sửa mã |
| 2 | 📚 **Kết hợp với sách** | Đọc cùng các chương tương ứng trong [`book-vi/`](../../book-vi/) (tiếng Việt) hoặc [`book/`](../../book/) (nguyên bản tiếng Trung) để hiểu sự kết hợp giữa lý thuyết và thực hành |
| 3 | 🔬 **So sánh thí nghiệm** | Nhiều dự án chứa nghiên cứu ablation và thí nghiệm đối chứng; hãy dùng so sánh để hiểu sâu hơn |
| 4 | 🪜 **Học tăng dần** | Bắt đầu từ dự án đơn giản rồi dần đi sâu vào hệ thống phức tạp |
| 5 | 🔌 **Chú ý giao thức** | Các dự án công cụ MCP ở chương 4 minh họa giao thức công cụ chuẩn hóa, đây là chìa khóa để xây dựng Agent có thể mở rộng |
