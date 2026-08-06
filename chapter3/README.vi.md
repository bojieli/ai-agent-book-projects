# Chương 3 · Bộ nhớ người dùng và kho tri thức

> giúp Agent ghi nhớ người dùng qua nhiều phiên và kết nối với tri thức bên ngoài. Bao gồm hệ thống bộ nhớ người dùng, pipeline RAG cơ bản, cũng như tổ chức và truy xuất tri thức vượt ra ngoài văn bản phẳng (chỉ mục cấu trúc, đồ thị tri thức, v.v.).

← [Về README chính](../docs/vi/README.md) · 📖 [Đọc nội dung chương](../book-vi/chapter3.vi.md)

## Dự án đi kèm

| Thí nghiệm | Project | Type | Description |
| :--: | --- | :--: | --- |
| 3-1, 3-2 | [user-memory](user-memory/) | ✅ | Xây dựng hệ thống bộ nhớ người dùng dài hạn, giúp Agent ghi nhớ sở thích và lịch sử tương tác của người dùng để cung cấp dịch vụ cá nhân hóa. |
| 3-1 | [user-memory-evaluation](user-memory-evaluation/) | ✅ | Đánh giá có hệ thống độ chính xác, mức độ liên quan và hiệu quả của hệ thống bộ nhớ người dùng, bao gồm nhiều kịch bản kiểm thử và chỉ số đánh giá. |
| 3-2 | [mem0](mem0/) · [memobase](memobase/) | ✅ | Dùng hai framework bộ nhớ mã nguồn mở mem0 và Memobase để triển khai hai phiên bản bộ nhớ người dùng, làm đối chứng cho thí nghiệm 3-2 “so sánh chiến lược bộ nhớ”, thuận tiện so sánh hình thái trích xuất và chất lượng trả lời của các phương án bộ nhớ khác nhau. |
| 3-3 | [log-sanitization](log-sanitization/) | ✅ | Khử trùng nhật ký thông minh sử dụng mô hình Ollama cục bộ để phát hiện và xóa bí mật cùng PII trong khi vẫn giữ nguyên giá trị gỡ lỗi. |
| 3-4 | [dense-embedding](dense-embedding/) | ✅ | Xây dựng dịch vụ tìm kiếm tương tự vector, so sánh hai thuật toán chỉ mục láng giềng gần đúng ANNOY (dựa trên cây) và HNSW (dựa trên đồ thị). Cho thấy sự đánh đổi giữa các chiến lược chỉ mục về hiệu năng, bộ nhớ và khả năng cập nhật. |
| 3-5 | [sparse-embedding](sparse-embedding/) | ✅ | Triển khai từ đầu công cụ tìm kiếm vector thưa dựa trên thuật toán BM25; thông qua log phong phú và giao diện trực quan để hiển thị cơ chế bên trong của công cụ tìm kiếm, giúp hiểu cách tính trọng số tần suất từ và nguyên lý chỉ mục đảo. |
| 3-6 | [retrieval-pipeline](retrieval-pipeline/) | ✅ | Xây dựng pipeline truy xuất hoàn chỉnh, kết hợp truy xuất dày đặc, truy xuất thưa và neural reranking. Thông qua các test case được thiết kế kỹ, dự án cho thấy hiệu quả bổ sung lẫn nhau của truy xuất lai trong các ngữ cảnh khác nhau. |
| 3-7 | [structured-index](structured-index/) | ✅ | Triển khai và so sánh hai chiến lược chỉ mục tiên tiến RAPTOR (cây trừu tượng đệ quy) và GraphRAG (đồ thị tri thức). Thông qua sổ tay kỹ thuật chỉ mục, dự án minh họa cách xây dựng chỉ mục có cấu trúc phản ánh tầng bậc và liên kết nội tại của tri thức. |
| 3-8 | [agentic-rag](agentic-rag/) | ✅ | So sánh khác biệt hiệu năng giữa RAG truyền thống không tác nhân (Non-Agentic RAG) và Agentic RAG. Cho thấy Agent có thể chủ đạo truy xuất thông tin lặp bằng mô thức ReAct, từ đó nâng cao đáng kể chất lượng câu trả lời khi xử lý hỏi đáp tư pháp phức tạp. |
| 3-9 | [agentic-rag-for-user-memory](agentic-rag-for-user-memory/) | ✅ | Áp dụng framework Agentic RAG vào quản lý lịch sử hội thoại người dùng; thông qua khả năng tìm kiếm lặp nhiều vòng để xử lý truy xuất bộ nhớ xuyên phiên, hiện thực năng lực hồi tưởng cơ bản và truy xuất đa phiên. |
| 3-10 | [contextual-retrieval](contextual-retrieval/) | ✅ | Triển khai kỹ thuật truy xuất nhận biết ngữ cảnh do Anthropic đề xuất: sinh phần tóm tắt tiền tố chứa ngữ cảnh cốt lõi cho từng khối văn bản, giải quyết vấn đề mất ngữ cảnh của phương pháp chia khối truyền thống, giảm tỷ lệ truy xuất thất bại 49–67%. |
| 3-11 | [contextual-retrieval-for-user-memory](contextual-retrieval-for-user-memory/) | ✅ | Áp dụng kỹ thuật truy xuất nhận biết ngữ cảnh vào xây dựng bộ nhớ người dùng, kết hợp Advanced JSON Cards và RAG nhận biết ngữ cảnh để hình thành cấu trúc bộ nhớ hai tầng, hiện thực năng lực phục vụ chủ động ở cấp cao hơn. |
| 3-12 | [structured-knowledge-extraction](structured-knowledge-extraction/) | ✅ | Lấy án lệ tư pháp làm ví dụ để chạy thông pipeline ba giai đoạn “phát hiện yếu tố từ dưới lên → phân cụm thành nguyên mẫu vụ án → Agent tư vấn đối thoại”: không đặt sẵn các trường cứng nhắc, để LLM tự phát hiện yếu tố từ lượng lớn án lệ và quy nạp thành schema mô-đun (yếu tố cốt lõi + yếu tố mở rộng theo tội danh); sau đó phân cụm vụ án thành nhiều nguyên mẫu và tính mức quan trọng của từng yếu tố trong mỗi nguyên mẫu; Agent sẽ khớp vụ việc mới với nguyên mẫu tương tự nhất, hỏi bổ sung thông tin còn thiếu theo mức quan trọng và đưa ra khuyến nghị có căn cứ (kèm tuyên bố miễn trừ trách nhiệm pháp lý). |

## Phân loại dự án

| Biểu tượng | Loại | Ý nghĩa |
| :--: | --- | --- |
| ✅ | **Chạy độc lập** | Có mã đầy đủ trong kho, chạy được sau khi cấu hình API Key |
| 📖 | **Hướng dẫn tái hiện** | Tài liệu chi tiết, cần `git clone` **kho ngoài** |
| 🚧 | **Tài liệu thiết kế** | Chỉ có kiến trúc/phương án, mã chạy được đang hoàn thiện |
