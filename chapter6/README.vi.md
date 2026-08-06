# Chương 6 · Đánh giá Agent

> biến biểu hiện của Agent thành tín hiệu có thể so sánh. Từ môi trường đánh giá, thiết kế bộ dữ liệu, hệ thống chỉ số, đến ý nghĩa thống kê, observability, chọn mô hình dựa trên đánh giá, cho tới đánh giá nội bộ và môi trường mô phỏng cấp sản xuất.

← [Về README chính](../docs/vi/README.md) · 📖 [Đọc nội dung chương](../book-vi/chapter6.vi.md)

## Dự án đi kèm

| Thí nghiệm | Project | Type | Description |
| :--: | --- | :--: | --- |
| 6-1 | `tau2-bench/` | 📖 | Tập trung đánh giá năng lực Agent dùng công cụ để suy luận phức tạp, bao gồm tính toán, tìm kiếm, xử lý dữ liệu và các ngữ cảnh khác. |
| 6-2 | `tau2-bench/` | 📖 | Hoàn thành thủ công các nhiệm vụ phân cấp của τ²-bench và ghi lại quỹ đạo. |
| 6-3 | [user-memory-evaluation](../chapter3/user-memory-evaluation/) | ✅ | Chạy rubric bốn mức trên 180 đánh giá có cấu trúc, kèm bằng chứng và quyền phủ quyết hallucination. |
| 6-4 | [user-memory-system-evaluation](user-memory-system-evaluation/) | ✅ | Chạy 60 trường hợp trên ba hệ thống với hạch toán chi phí đầy đủ. |
| 6-5 | [user-memory-policy-eval](user-memory-policy-eval/) | ✅ | Chạy 11 trường hợp lỗi tiền tố quỹ đạo trên các biểu diễn bộ nhớ dạng JSON, Markdown và tương tự Python bằng lời gọi OpenRouter thực cùng các kiểm tra chính sách tất định. |
| 6-11 | [user-memory-system-evaluation](user-memory-system-evaluation/) | ✅ | Ma trận đầy đủ 4×3×2×60 giữ lại 1.440/1.440 quỹ đạo thực, không có lỗi hay lượt dùng chưa tính giá, kèm đủ chỉ số truy hồi/tác vụ, phân tích tương tác và trình xác minh độc lập đạt. |
| 6-13 | [openvla-robotwin2-eval](openvla-robotwin2-eval/) | ✅ | Chiến dịch chính thức trên một GPU đã hoàn thành 256 episode mỗi nhánh; chunk 1 đạt 0/256, chunk 25 đạt 26/256 và lưu hash của 512 rollout. |
| 6-2 | `terminal-bench/` | 📖 | Terminal-Bench là benchmark kiểm thử biểu hiện của AI Agent trong môi trường terminal thực. Từ biên dịch mã đến huấn luyện mô hình, thiết lập server, benchmark đánh giá cách Agent xử lý các nhiệm vụ đầu-cuối thực tế. Bao gồm bộ dữ liệu khoảng 100 nhiệm vụ và framework thực thi, hỗ trợ nhiều triển khai Agent. |
| 6-2 | `SWE-bench/` | 📖 | SWE-bench là benchmark đánh giá khả năng của mô hình ngôn ngữ lớn trong việc giải quyết các vấn đề GitHub thật. Với một codebase và mô tả issue, mô hình cần sinh patch có thể giải quyết vấn đề. Bao gồm nhiều phiên bản: SWE-bench, SWE-bench Lite, SWE-bench Verified và SWE-bench Multimodal. |
| 6-2 | `GAIA/` | 📖 | GAIA nhằm đánh giá thế hệ LLM tiếp theo (LLM có năng lực tăng cường bằng công cụ, prompt hiệu quả, truy cập tìm kiếm, v.v.). Bao gồm hơn 450 câu hỏi phi tầm thường cần mức độ công cụ và tự chủ khác nhau, với đáp án rõ ràng không mơ hồ. Chia thành 3 cấp độ khó. |
| 6-2 | `OSWorld/` | 📖 | Đánh giá năng lực của Agent khi thực thi nhiệm vụ phức tạp trong môi trường hệ điều hành đầy đủ, bao gồm quản lý file, thao tác ứng dụng và cấu hình hệ thống. |
| 6-2, 6-12 | `android_world/` | 📖 | Đánh giá biểu hiện của Agent trong môi trường di động Android, bao gồm điều hướng ứng dụng, tương tác UI và khả năng hoàn thành nhiệm vụ (repo benchmark ngoài). |
| 6-6 | [tts-quality-eval](tts-quality-eval/) | ✅ | Dùng nhiều cấu hình TTS (model/voice/speed khác nhau) để tổng hợp cùng một nhóm văn bản thử thách, sau đó dùng LLM-as-a-Judge đa phương thức chấm điểm từng chiều theo Rubric (độ rõ/naturalness, v.v.), tổng hợp thành bảng so sánh cấu hình có thể tái hiện. |
| 6-7 | [elo-leaderboard](elo-leaderboard/) | ✅ | Triển khai bảng xếp hạng hiệu năng Agent dựa trên hệ thống điểm ELO, đánh giá năng lực tương đối của các Agent khác nhau thông qua so sánh đối đầu. |
| 6-8 | [model-action-threshold](model-action-threshold/) | ✅ | So sánh GPT-5.6-sol và Claude Sonnet 5 tại thời điểm chuyển từ khám phá sang lần chỉnh sửa đầu tiên dưới cùng một Coding Harness trung lập; cả 18/18 ô đều hoàn tất không có lỗi API, và [manifest](model-action-threshold/results/exp6-7-action-threshold-20260731-v1/manifest.json) liên kết trajectory cùng bản tổng hợp bằng các hash có thể kiểm chứng. |
| 6-9 | [agent-cost-analysis](agent-cost-analysis/) | ✅ | Phân rã toàn tuyến chi phí của nhiệm vụ Agent nhiều vòng điển hình (hoàn tiền chăm sóc khách hàng): dùng tracing nhẹ tự xây để ghi lại token input/output/cache, độ trễ và chi phí của từng lần gọi LLM; tổng hợp “bước nào đắt nhất”, rồi dùng A/B để định lượng mức tiết kiệm thực của thiết kế thân thiện KV-cache + nén ngữ cảnh. |
| 6-10 | [model-benchmark](model-benchmark/) | 🚧 | Benchmark ngang nhiều nhà cung cấp LLM API tương thích OpenAI; dùng giao diện streaming để đo chính xác độ trễ token đầu tiên (TTFT), đo các phân vị độ trễ đầu-cuối (p50/p95), throughput và tỷ lệ thành công dưới tải đồng thời. Một lệnh tạo bảng so sánh đa chiều, cho thấy chọn mô hình là đánh đổi nhiều chiều chứ không chỉ nhìn bảng xếp hạng. |
| 6-12 | [android-world](android-world/) | 📖 | Ghi chú phân tích báo cáo đánh giá T3A trên AndroidWorld trong repo này (điểm bắt đầu Thí nghiệm 6-12; không phải mã nguồn benchmark). |
| — | [public-health-reporting-eval](public-health-reporting-eval/) | ✅ | Sử dụng dữ liệu tổng hợp nhân tạo theo phong cách DHIS2 để đánh giá khách quan lời gọi công cụ, độ chính xác tính toán, trích dẫn bằng chứng và các tuyên bố không có căn cứ của Agent báo cáo y tế công cộng. |

> 📖 Các benchmark bên ngoài (tên đặt trong dấu backtick) cần tự clone riêng. [`android-world/`](android-world/) (có gạch nối) là **ghi chú phân tích đánh giá T3A** trong repo này (xem [README](android-world/README.md) của nó), không phải cùng đường dẫn với mã nguồn benchmark `android_world/` bên ngoài.

## Phân loại dự án

| Biểu tượng | Loại | Ý nghĩa |
| :--: | --- | --- |
| ✅ | **Chạy độc lập** | Có mã đầy đủ trong kho, chạy được sau khi cấu hình API Key |
| 📖 | **Hướng dẫn tái hiện** | Tài liệu chi tiết, cần `git clone` **kho ngoài** |
| 🚧 | **Tài liệu thiết kế** | Chỉ có kiến trúc/phương án, mã chạy được đang hoàn thiện |
