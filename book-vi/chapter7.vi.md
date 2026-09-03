# Đánh giá Agent

Sáu chương đầu đã trình bày cách xây dựng một Agent đơn: ngữ cảnh, tri thức, công cụ, năng lực coding, cùng không gian quan sát và hành động. Tuy nhiên, xây dựng xong không có nghĩa là xây dựng đúng; chỉ khi kết quả được đo lường ổn định thì quá trình training mô hình và tiến hóa hệ thống sau đó mới có phương hướng đáng tin cậy.

Khi xây dựng hệ thống Agent, các nhà phát triển phải đối mặt với một số lựa chọn thiết kế, thường không có câu trả lời đúng rõ ràng:

- Sử dụng mô hình nào?
- Mô hình có thể gọi những công cụ gì?
- Dữ liệu nào cần được lưu trữ trong cơ sở tri thức và nó nên được xây dựng theo cấu trúc nào?
- Làm thế nào để làm bộ nhớ người dùng?
- Cách sắp xếp lời nhắc và kỹ năng của mẫu?
- Cần bổ sung thêm những hạn chế nào cho Harness?
- Làm thế nào để Agent này tự tiến hóa và tự lặp lại?

Đánh giá cung cấp cho chúng ta cơ sở khoa học để đưa ra quyết định: thông qua các thí nghiệm so sánh có hệ thống (thay đổi một biến, quan sát sự thay đổi hiệu ứng) và thí nghiệm cắt bỏ (tắt từng bộ phận một, quan sát sự thay đổi hiệu suất tổng thể, để đánh giá sự đóng góp thực sự của thành phần), chúng ta có thể phân biệt giữa cải thiện năng lực thực sự và biến động hời hợt, tránh "nhặt hạt vừng và mất dưa hấu". Như câu nói trong công nghệ phần mềm, "Không có sự cải tiến nào nếu không đo lường". Nếu không thiết lập hệ thống đánh giá có thể lặp lại, hướng lặp của Agent chỉ có thể dựa vào trực giác.

Từ quan điểm của kỹ thuật Harness được giới thiệu trong Chương 1, việc đánh giá đóng vai trò cốt lõi trong chức năng “xác nhận” trong Harness. Hiểu biết quan trọng là: **Đối tượng đánh giá không chỉ là mô hình mà còn là sự kết hợp giữa mô hình và Harness**. Cùng một mô hình có thể hoạt động rất khác nhau trong các Harness khác nhau - một số nhóm đã cải thiện đáng kể hiệu suất của cùng một mô hình trong các tác vụ đầu cuối chỉ bằng cách tối ưu hóa Harness (xem Chương 5 để biết chi tiết). Điều này có nghĩa là khi Agent hoạt động kém trong quá trình đánh giá, hướng cải tiến có thể không phải là thay đổi mô hình mà là tối ưu hóa một thành phần nhất định của Harness (lời nhắc, thiết kế công cụ, vòng phản hồi). Một hệ thống đánh giá hoàn chỉnh phải có khả năng phân biệt giữa hai loại vấn đề cơ bản khác nhau: "khả năng mô hình không đủ" và "lỗi thiết kế Harness". **Một cách phổ biến để phân biệt giữa hai loại vấn đề này là thử nghiệm hoán đổi mô hình** - giữ nguyên Harness, chỉ thay thế các mô hình mạnh hơn/yếu hơn và quan sát sự thay đổi về điểm số; nếu điểm không tăng khi chuyển sang mẫu mạnh hơn thì có nghĩa nút thắt nằm ở Harness; nếu điểm giảm mạnh khi chuyển sang mô hình yếu và điểm dao động lớn theo khả năng của mô hình, thì cách giải thích trực tiếp nhất là nút thắt cổ chai nằm ở chính khả năng của mô hình và hiệu suất hiện tại chủ yếu được xác định bởi mô hình (về việc liệu điều này là do bản thân nhiệm vụ khó hay Harness quá phụ thuộc vào mô hình trước đó, thì cần phải phân tích thêm). Lưu ý rằng đây là hai phương pháp khác với "thử nghiệm cắt bỏ" được đề cập trước đó: cắt bỏ là **tắt một thành phần của Harness** để xem hiệu suất tổng thể thay đổi như thế nào, trong khi thay thế mô hình là **giữ nguyên Harness và chỉ thay thế mô hình** - phương pháp trước xác định thành phần nào trong Harness là quan trọng và phương pháp sau phân biệt xem nút cổ chai nằm trong mô hình hay trong Harness.

Giá trị của hệ thống đánh giá thậm chí còn nổi bật hơn trong thời đại phát triển mô hình nhanh chóng. Khả năng của mô hình vẫn đang phát triển nhanh chóng, nhưng chỉ vì mô hình mới hoạt động tốt hơn theo điểm chuẩn công khai không có nghĩa là mô hình đó thực hiện tốt hơn nhiệm vụ cụ thể của bạn—ngược lại, có thể xảy ra hiện tượng hồi quy hiệu suất (tức là phiên bản mới không tốt bằng phiên bản cũ ở một số khía cạnh). Các quyết định nâng cấp dựa trên dữ liệu chỉ có thể được đưa ra thông qua thử nghiệm hoàn chỉnh trên tập dữ liệu đánh giá của riêng bạn. Hơn nữa, một hệ thống đánh giá hoàn chỉnh khiến cho việc "phát triển sản phẩm cho các mẫu tương lai" trở thành một chiến lược khả thi - ngay cả khi mô hình hiện tại không đủ để hỗ trợ sử dụng thương mại, trước tiên bạn có thể hoàn thành việc phát triển sản phẩm và thiết lập bộ đánh giá, tiếp tục theo dõi hiệu suất của mô hình mới và khởi chạy nó ngay lập tức khi đạt đến ngưỡng.
Một hệ thống đánh giá có thể tách thành bốn mắt xích: thế nào là thành công, nhiệm vụ đến từ đâu, ai kiểm chứng, và điểm số được chuyển thành quyết định ra sao. Hình 7-1 minh họa điều này.

![Hình 7-1 Bốn mắt xích của hệ thống đánh giá Agent](images/fig7-1.svg)

## Mổ xẻ một nhiệm vụ đánh giá: miền telecom của τ²-bench

Trước hết hãy mổ xẻ trọn vẹn một nhiệm vụ thật trong miền telecom của τ²-bench. τ²-bench là dự án mã nguồn mở của Sierra và không được đưa vào kho đi kèm; hãy clone nó vào `chapter7/tau2-bench` bằng lệnh trong `chapter7/tau2-bench-eval/README.md`, khi đó tệp nhiệm vụ nằm ở `data/tau2/domains/telecom/tasks_small.json`.

### Bốn thành phần của định nghĩa nhiệm vụ

Dưới đây là một nhiệm vụ trong tệp đó, đã lược bớt cho dễ đọc.

```jsonc
{
  "id": "[mobile_data_issue]airplane_mode_on|user_abroad_roaming_enabled_off",

  // Phiếu yêu cầu giao cho Agent
  "ticket": "Điện thoại của người dùng không vào được internet, thanh trạng thái
             hiển thị 'No Service'. Khách hàng John Smith, số 555-123-2002, hiện
             đang ở Pháp. Chỉ khi kiểm tra tốc độ trả về excellent mới coi là đã
             xử lý xong. Không đổi gói cước, nhưng sẵn sàng nạp thêm 2,0 GB dữ
             liệu nếu cần.",

  // Quy tắc hành vi giao cho bộ mô phỏng người dùng
  "user_scenario": { "instructions": {
      "known_info": "You are John Smith with phone number 555-123-2002.
                     You are currently abroad in France.",
      "unknown_info": null,
      "task_instructions":
        "…express mild frustration after the first unsuccessful attempt.
         You will consider the issue resolved only when speed test returns
         excellent internet speed and nothing else. If it returns poor, fair
         or good, you will not consider the issue resolved.
         Whenever the agent asks you about your device, always ground your
         responses on the results of tool calls. …
         Never make up the results of tool calls."
  }},

  // Trước khi chạy, đưa trạng thái hai phía về cùng một điểm xuất phát
  "initial_state": { "initialization_actions": [
      { "env_type": "user",      "func_name": "turn_airplane_mode_on" },
      { "env_type": "user",      "func_name": "turn_roaming_off" },
      { "env_type": "assistant", "func_name": "enable_roaming",
        "arguments": { "customer_id": "C1001", "line_id": "L1002" } }
  ]},

  // Tiêu chí chấm điểm
  "evaluation_criteria": {
      "actions": [
        { "requestor": "user", "name": "toggle_airplane_mode" },
        { "requestor": "user", "name": "toggle_roaming" }
      ],
      "env_assertions": [
        { "func_name": "assert_mobile_data_status", "expected_status": true },
        { "func_name": "assert_internet_speed",
          "expected_speed": 200, "expected_desc": "excellent" }
      ],
      "communicate_info": null,
      "nl_assertions": null,
      "reward_basis": ["ENV_ASSERTION"]
  }
}
```

Trong định nghĩa này có bốn quyết định thiết kế cần nói rõ.

**Ranh giới hiểu biết của người dùng được mô hình hóa tường minh.** `known_info` chỉ chứa ba thông tin: tên, số điện thoại và quốc gia đang ở. Hai nguyên nhân thật sự của sự cố — chế độ máy bay đang bật và chuyển vùng dữ liệu đang tắt — không có trong đó. Người dùng không biết nên không thể tự nói ra, và Agent chỉ có thể lấy được bằng cách hỏi và hướng dẫn người dùng kiểm tra. Đây chính là cách **tiết lộ thông tin tuần tự (Progressive Information Disclosure)** được hiện thực hóa ở tầng định nghĩa nhiệm vụ: không phải ràng buộc bộ mô phỏng bằng một câu prompt "đừng nói hết một lúc", mà mô hình hóa phạm vi hiểu biết của người dùng thành một trường riêng. Phần lớn benchmark đưa ra yêu cầu đầy đủ ngay khi bắt đầu, trong khi câu đầu tiên của người dùng thật thường chỉ là "tôi không vào mạng được". Làm rõ yêu cầu đến mức có thể thực thi tự nó đã là một phần năng lực mà Agent phải có.

**Bộ mô phỏng nhận quy tắc hành vi chứ không phải lời thoại.** `task_instructions` gộp ba loại ràng buộc: thiết lập cảm xúc (tỏ ra hơi khó chịu sau lần khắc phục đầu tiên thất bại), tiêu chí nghiệm thu (chỉ khi kiểm tra tốc độ trả về excellent mới coi là xong; poor, fair, good đều không chấp nhận), và yêu cầu **neo vào sự kiện (Grounding)**, tức mọi câu trả lời về trạng thái thiết bị đều phải dựa trên giá trị mà công cụ trả về: "Never make up the results of tool calls". Điều thứ ba quan trọng nhất: thiếu ràng buộc neo sự kiện, người dùng mô phỏng sẽ theo sự dẫn dắt của Agent mà xác nhận vấn đề đã xong, và việc đánh giá thoái hóa thành hai mô hình xác nhận lẫn nhau.

**Trạng thái ban đầu được chia theo phía điều khiển.** `env_type` nhận hai giá trị `user` và `assistant`: chế độ máy bay và công tắc chuyển vùng thuộc phía người dùng, còn `enable_roaming` phía nhà mạng thuộc phía Agent. Chính cách chia này quyết định hình dạng của sự cố — phía nhà mạng chuyển vùng đã mở, nhưng trên máy người dùng lại đang tắt, nên Agent tra cơ sở dữ liệu chỉ nhận được kết luận "cấu hình bình thường". Sự cố nằm ở phía mà cơ sở dữ liệu không nhìn thấy, và chỉ lộ ra khi hướng dẫn người dùng tự kiểm tra.

**Tiêu chí chấm điểm chia thành bốn tầng, và nhiệm vụ này chỉ dùng một tầng.** `env_assertions` kiểm tra trạng thái cuối (dữ liệu di động dùng được, tốc độ từ 200 Mbps trở lên và xếp hạng excellent), `actions` kiểm tra các hành động then chốt có xảy ra hay không và **do phía nào** thực hiện, còn `communicate_info` và `nl_assertions` kiểm tra thông tin cần thiết đã được báo cho người dùng chưa. `reward_basis` của nhiệm vụ này chỉ khai báo `ENV_ASSERTION`; các tầng còn lại vẫn được tính và ghi nhận nhưng không vào phần thưởng cuối. Căn cứ chấm điểm được khai báo theo từng nhiệm vụ chứ không cố định toàn cục.

### Trajectory của một lần chạy thật

Tiếp theo, chúng tôi mời bạn đọc tự chạy các nhiệm vụ đánh giá của miền telecom trong τ²-bench, quan sát thiết kế nhiệm vụ, thiết kế bộ mô phỏng người dùng, logic kiểm chứng quá trình và kết quả, đồng thời xem trajectory thực thi của Agent để phân tích vì sao Agent thất bại.

> **Thí nghiệm 7-1 ★: Chạy τ²-bench và so sánh bước tiến so với τ-bench**
>
> Thí nghiệm này chạy khung đánh giá τ²-bench để hiểu các điểm mấu chốt trong thiết kế môi trường đánh giá kiểu tương tác người-máy. Trước hết hãy đọc tệp định nghĩa nhiệm vụ theo đúng lộ trình của mục này: mỗi nhiệm vụ gồm bốn phần — thông tin đã biết, chỉ dẫn nhiệm vụ, trạng thái ban đầu và điều kiện thành công. Sau đó chạy trọn quy trình đánh giá, quan sát đối thoại nhiều lượt giữa bộ mô phỏng người dùng và Agent, rồi phân tích các dạng thất bại điển hình (vi phạm chính sách, bỏ sót thông tin, chuyển sang nhân viên quá sớm, v.v.).
>
> ![Hình 7-3 Môi trường điều khiển kép và kiểm chứng phân tầng trong τ²-bench](images/fig7-3.svg)

Kho đi kèm có lưu một bản ghi chạy (`chapter7/tau2-bench-eval`). Dưới đây ta phân tích một lần chạy thành công trong đó.

Hơn mười lượt đầu là giai đoạn xác định tài khoản. Agent tra ra khách hàng C1001 từ số điện thoại, rồi lần lượt tra lưu lượng của ba thuê bao L1001, L1002, L1003, và quay lại hỏi người dùng thực tế đang dùng số nào ở Pháp. Ở tin nhắn thứ 17 nó đưa ra một kết luận sai:

> **Agent** (17): số 555-123-2002 không nằm trong các thuê bao đang hoạt động của bạn, gần nhất là 555-123-2001…

Kết luận này chỉ dựa trên kết quả tra một thuê bao L1001. Sau khi người dùng khẳng định số không sai, Agent tra tiếp L1002 và lúc đó mới khớp. Bước ngoặt then chốt xuất hiện ở tin nhắn 30:

> **Người dùng** (30) → gọi `check_network_status()`, `check_status_bar()`
>
> **Công cụ trả về** (31): `Airplane Mode: ON | Cellular Connection: no_service | Mobile Data Enabled: Yes | Data Roaming Enabled: No`
>
> **Người dùng** (33): tôi thấy điện thoại đang ở chế độ máy bay, nên mới không có sóng. Dữ liệu di động đang bật, nhưng chuyển vùng dữ liệu đang tắt. Tôi tắt chế độ máy bay rồi thử lại nhé?

Bên phát ra lời gọi công cụ là **người dùng**, không phải Agent. Đây chính là cơ chế **điều khiển kép (Dual-Control)**: người dùng mô phỏng có một bộ công cụ riêng như `check_status_bar`, `toggle_airplane_mode`, `reseat_sim_card`, `run_speed_test`.

Việc chẩn đoán sau đó khá trôi chảy: Agent yêu cầu người dùng tắt chế độ máy bay và bật chuyển vùng, người dùng thực hiện (35, 37), thanh trạng thái chuyển sang 5G đầy vạch; Agent yêu cầu đo tốc độ, kết quả trả về 275 Mbps, xếp hạng Excellent (46), và người dùng xác nhận đã xong. Cả hai `env_assertions` đều đạt, `reward = 1.0`.

Trajectory điểm tối đa này còn chứa một vấn đề mà bộ kiểm chứng không bắt được. Ngay đoạn đầu chính sách Agent của telecom đã ghi "You should only make one tool call at a time", nhưng ở tin nhắn thứ 4 Agent phát ra cùng lúc hai lời gọi `get_customer_by_phone` và `get_customer_by_name`. Bộ kiểm chứng không coi đó là lỗi, vì `reward_basis` của nhiệm vụ này chỉ xét trạng thái cuối. Đây không phải sơ suất của τ²-bench mà là cái giá cố hữu của phần thưởng nhị phân: nó đánh đổi độ mịn của quá trình lấy một con số duy nhất có thể so sánh giữa các mô hình. Nhưng hệ thống đánh giá trong môi trường sản xuất thường cần nhiều hơn thế: không chỉ phán đúng sai, mà còn phải chỉ ra vấn đề nằm ở đâu.

Nhiệm vụ thất bại cũng đáng phân tích. Số của người dùng là 555-123-2002, nhưng Agent lại chọn thuê bao L1001 và tiếp tục suy luận dựa trên mức dùng 3,2/5 GB của thuê bao đó. Giữa chừng `get_details_by_id(L1001)` đã trả về rõ ràng rằng số của thuê bao ấy là 555-123-2001; Agent đọc kết quả đó nhưng không sửa lại phán đoán, sau đó tiêu tốn hàng chục tin nhắn cho những kiểm tra không liên quan và cuối cùng chuyển sang nhân viên. Thực ra nó đã làm được một nửa nhiệm vụ — hướng dẫn người dùng tắt chế độ tiết kiệm dữ liệu, và hành động phía người dùng đó đã thực sự xảy ra và được môi trường kiểm chứng. Nhưng chọn sai thuê bao khiến việc nạp 2 GB cần thiết không được thực hiện, và cả ba khẳng định trạng thái cuối đều thất bại. Hình dạng thất bại này rất giống trường hợp AndroidWorld được bàn ở mục "Quy trách nhiệm thất bại" phía sau: bằng chứng cần để sửa phán đoán đã nằm sẵn trong ngữ cảnh, nhưng Agent không dựa vào đó mà quay lại.

Chỉ một nhiệm vụ này đã đặt ra đủ mọi câu hỏi mà một tập đánh giá phải trả lời: thế nào là thành công, nhiệm vụ đến từ đâu, ai kiểm chứng, và điểm số được chuyển thành quyết định ra sao. Các mục sau sẽ lần lượt triển khai.

## Chỉ số đánh giá: định nghĩa thành công

Kết quả đánh giá ở mục trước là bốn trên năm nhiệm vụ đạt. Chỉ với con số 0,8 thì không thể phán đoán hệ thống có dùng được hay không. Nếu đó là Agent chăm sóc khách hàng xử lý hoàn tiền, nghĩa là cứ năm người dùng thì có một người không nhận được khoản hoàn đáng ra thuộc về họ; nếu đó là Agent bảo mật đi tìm lỗ hổng, trúng bốn trên năm đã là khá tốt. Khác biệt nằm ở chỗ bối cảnh nghiệp vụ đòi hỏi tỷ lệ thành công cao đến mức nào.

### Kỳ quan kỹ thuật: trần năng lực với Pass@k

Nhiều mô hình và Agent hiện nay vẫn ở giai đoạn có thể gọi là **"kỳ quan kỹ thuật"**. Kỳ quan ở đây là trần năng lực bộc lộ ra sau rất nhiều lần thử, một ngân sách thời gian rộng rãi và sự sàng lọc của con người: chỉ cần một lần thành công là đủ chứng minh "việc này về nguyên tắc làm được". Đó chính là logic của **Pass@k** — chạy cùng một tác vụ $k$ lần, chỉ cần ít nhất một lần vượt qua thì tính là đạt; nếu đầu ra là điểm liên tục thì lấy lần tốt nhất, gọi là **Best@k**.

Những thảo luận của Anthropic về Agent chạy dài thể hiện rõ loại trần năng lực này: cho Agent tự làm việc suốt một tuần để viết một trình biên dịch C từ đầu; cho nó dò tìm cho tới khi ra được một phản ví dụ cho một giả thuyết toán học quan trọng; hoặc rà đi rà lại phần mềm mã nguồn mở cho tới khi lộ ra một lỗ hổng bảo mật nghiêm trọng đã nằm đó hàng chục năm.

Với loại thăm dò kỹ thuật và khoa học này, thứ được phô diễn thường không phải "lần nào cũng đúng", mà là một quỹ đạo đột phá duy nhất rốt cuộc xuất hiện khi ngân sách thăm dò được kéo đủ dài. Với khám phá khoa học, săn lỗ hổng hay sáng tạo mở, bản thân cái trần đó đã có giá trị: con người có thể chọn ra quỹ đạo tốt nhất trong $k$ ứng viên.

Ngoài các phòng thí nghiệm mô hình nền, nhiều công ty ứng dụng cũng dùng chiến lược "kỳ quan kỹ thuật". Manus gây chú ý rộng rãi vì nó đưa cho người dùng một chiếc máy tính ảo: những người trước đó chưa có hình dung trực quan nào về Agent đã thấy AI có thể thao tác máy tính như người, làm việc liên tục nửa tiếng thậm chí một tiếng và hoàn tất từng bước một tác vụ phức tạp.

OpenClaw thì khiến nhiều người lần đầu cảm nhận được "chất người" của một Agent. Người dùng giao việc cho nó qua ứng dụng nhắn tin y như giao cho một người thật; nó truy cập được mọi tệp trên máy và các dịch vụ trực tuyến, đến một giai đoạn nhất định sẽ chủ động báo lại hoặc hỏi thêm thông tin, thậm chí có thể tự đánh thức mình dậy để kiểm tra và xử lý email.

Manus và OpenClaw thời kỳ đầu không có tỉ lệ thành công cao trên các tác vụ phức tạp, chi phí token cũng rất lớn. Nhưng vì các framework Agent này mang tính đa dụng, khi dùng với mô hình mạnh nhất thì tác vụ phức tạp thường đạt Pass@k cao, cho thấy trần kỹ thuật cao. Việc những "kỳ quan kỹ thuật" đó được chia sẻ ồ ạt trên mạng xã hội chính là chìa khóa thành công của các sản phẩm này.

### Độ tin cậy nghiệp vụ: Pass^k

Nghiệp vụ thực tế thường quan tâm điều ngược lại: qua nhiều lần thử không được sai một lần nào. Chúng tôi gọi mục tiêu này là **Pass^k** (đọc là **Pass consecutive k**): chạy cùng một tác vụ $k$ lần liên tiếp, đòi hỏi lần nào cũng vượt qua và không được kích hoạt bất kỳ mục phủ quyết nào về an toàn, tuân thủ hay ảo giác. Nó trả lời câu hỏi "Agent có giao được kết quả ổn định và đáng tin cậy không", chứ không phải "thỉnh thoảng có tạo được kỳ tích không".

Nếu các lần chạy độc lập với nhau và tỉ lệ thành công một lần là $p$, quan hệ giữa hai chỉ số rất trực quan:

$$
\mathrm{Pass@k}=1-(1-p)^k,\qquad
\mathrm{Pass}^{k}=p^k.
$$

Ví dụ khi tỉ lệ thành công một lần $p=0.6$ và $k=5$: Pass@5 $=1-0.4^5\approx99.0\%$, trông như hầu như luôn "thành công ít nhất một lần"; nhưng Pass consecutive@5 $=0.6^5\approx7.8\%$, cho thấy năm lần liên tiếp không sai vẫn rất khó. Con số đầu hợp để đo trần năng lực khi thăm dò, con số sau mới gần với yêu cầu độ tin cậy của thanh toán, hoàn tiền, đổi quyền hay triển khai production.

Báo cáo đánh giá bắt buộc phải nói rõ $k$ lần thử được hiểu thế nào: là $k$ lần lấy mẫu độc lập của cùng một tác vụ, hay $k$ tác vụ liên tiếp trên dây chuyền production. Với các thao tác có tác dụng phụ, không thể đơn giản "thử lại đến khi thành công", mà phải lấy mẫu trong sandbox hoặc môi trường có thể rollback, và ghi từng lần thất bại vào chỉ số độ tin cậy.

## Môi trường đánh giá

Khi đã rõ cách tính chỉ số, câu hỏi tiếp theo là đo ở đâu. Môi trường đánh giá là một bộ máy có thể chạy lặp lại: cho cùng một trạng thái ban đầu, cùng một Agent phải cho ra kết quả so sánh được.

### Năm thành phần cấu thành

Hãy quay lại nhiệm vụ telecom vừa mổ xẻ. Lấy nó làm mốc, mọi thứ mà một môi trường đánh giá chạy lặp lại cần đến đều đã đủ.

**Tập dữ liệu (Dataset)** chính là tệp nhiệm vụ: trạng thái ban đầu, phiếu yêu cầu cho Agent, quy tắc hành vi cho bộ mô phỏng và tiêu chí nghiệm thu được gói thành một bản ghi, và một bản ghi là một ca kiểm thử.

**Trạng thái môi trường (Environment State)** là phần thông tin biến động trong lúc chạy nhiệm vụ: khách hàng, thuê bao, gói cước và hóa đơn trong cơ sở dữ liệu, cộng thêm chế độ máy bay, chuyển vùng, công tắc tiết kiệm dữ liệu và dung lượng còn lại ở phía thiết bị. Nó phải khôi phục được, và `initialization_actions` chính là kịch bản khôi phục. Tính chân thực đòi hỏi biến đổi trạng thái tuân theo logic nghiệp vụ; tính kiểm soát đòi hỏi trước mỗi lần chạy đều quay về cùng một điểm xuất phát.

**Giao diện công cụ (Tools)** chia về hai phía. Agent gọi được các thao tác phía nhà mạng như tra khách hàng, tra lưu lượng, nạp dữ liệu, chuyển sang nhân viên; người dùng thao tác được các công tắc trên thiết bị. Cả hai bộ công cụ đều là thao tác nguyên tử, không có kiểu trừu tượng cấp cao như "giải quyết vấn đề mạng của người dùng" — mức trừu tượng quá cao sẽ biến việc đánh giá thành kiểm tra một lời gọi hàm duy nhất, còn phần lập kế hoạch và suy luận bị chính công cụ hấp thụ.

**Tiêu chí chấm điểm (Rubric)** là bốn tầng kiểm tra trong `evaluation_criteria` cộng với quy tắc tổng hợp `reward_basis`.

**Giao thức thực thi (Interaction Protocol)** quy định thứ tự tương tác và điều kiện kết thúc. Tín hiệu kết thúc bình thường ở đây là người dùng mô phỏng xuất ra `###STOP###`; ngoài ra còn có giới hạn số lượt, và người dùng mô phỏng có thể tự kết thúc cuộc trò chuyện khi hết kiên nhẫn — hiệu quả giao tiếp quá thấp tự nó đã bị tính là thất bại.

Thiếu một trong năm thành phần, việc đánh giá không còn tạo thành một vòng lặp lặp lại được. Khi xem xét các benchmark khác ở dưới, chúng ta vẫn lấy năm mục này làm khung đối chiếu.

### Môi trường đánh giá kiểu tương tác người-máy và kiểu gọi công cụ

Những nhiệm vụ như telecom bắt buộc phải có đối tượng tương tác, nên phần mô phỏng người dùng trong năm thành phần là không thể thiếu. Còn có một lớp nhiệm vụ lớn khác hoàn toàn không có đối tượng đối thoại: trong sinh mã, phân tích dữ liệu, giải toán, Agent từ đầu đến cuối chỉ tương tác với công cụ, tính đúng đắn do việc có vượt qua kiểm chứng thực thi hay không quyết định, và không cần gán nhãn thủ công lẫn phán xét của mô hình. Loại môi trường này lược bỏ bộ mô phỏng người dùng; bốn thành phần còn lại vẫn tồn tại, chỉ đơn giản hơn về hình thức: trạng thái môi trường là hệ thống tệp hoặc cơ sở dữ liệu, tiêu chí chấm điểm là một đoạn mã kiểm thử, còn giao thức thực thi thu lại thành "cứ gọi công cụ cho đến khi đưa ra câu trả lời hoặc hết lượt".

Khung Verifiers phân tầng loại môi trường này theo hai chiều: nhiệm vụ có cần giữ trạng thái qua các lượt hay không, và có cần cách ly hay không. `SingleTurnEnv` hợp cho việc ra một bài toán rồi kiểm chứng đáp án ngay; `ToolEnv` hợp cho việc tìm nhiều trang web rồi tổng hợp câu trả lời và kiểm chứng kết quả cuối; `StatefulToolEnv` hợp cho việc sửa bản ghi cơ sở dữ liệu rồi kiểm chứng biến đổi trạng thái; `SandboxEnv` hợp cho việc chạy mã trong sandbox rồi kiểm tra tệp kết quả. Bảng 7-1 tổng hợp bốn loại này để tiện chọn theo yêu cầu về trạng thái nhiệm vụ, lời gọi công cụ và cách ly.

Bảng 7-1 So sánh các loại môi trường Verifiers

| Loại môi trường | Giữ trạng thái | Gọi công cụ | Trường hợp điển hình |
|---|---|---|---|
| SingleTurnEnv | Không | Không | Hỏi đáp một lượt, bài toán |
| ToolEnv | Không | Nhiều lượt | Tìm kiếm + tổng hợp thông tin |
| StatefulToolEnv | Có | Nhiều lượt | Sửa bản ghi cơ sở dữ liệu |
| SandboxEnv | Có + cách ly | Nhiều lượt | Chạy mã và kiểm thử |

Khung này hỗ trợ lấy mẫu song song và bộ nhớ đệm trajectory; trajectory đầy đủ của mỗi lần đánh giá (quan sát, hành động, phần thưởng) đều được lưu, tiện cho phân tích và phát lại về sau. Ngoài ra, hiệu quả thực thi của công cụ phụ thuộc vào trạng thái hiện thời, nên khi thất bại nên trả về thông báo lỗi rõ ràng thay vì một cờ thất bại trơ trọi, để Agent điều chỉnh chiến lược theo đó.

Đánh giá kiểu gọi công cụ xét tính đúng đắn của các biến đổi trạng thái quan sát được, còn đánh giá kiểu tương tác người-máy xét tính hợp lý của chiến lược giao tiếp — cái trước kiểm chứng hành động, cái sau kiểm chứng khả năng dẫn dắt. So sánh cấu trúc hai loại môi trường xem Hình 7-2.

![Hình 7-2 Môi trường đánh giá kiểu gọi công cụ và kiểu tương tác người-máy](images/fig7-2.svg)

## Thiết kế tập dữ liệu đánh giá

Nếu môi trường đánh giá là sân khấu thì tập dữ liệu là kịch bản. Vẫn năm thành phần ấy, nhưng đổi sang một lớp nhiệm vụ khác thì cách điền có thể khác hẳn: nhiệm vụ đến từ đâu, bộ kiểm chứng soi được sâu tới mức nào, và làm sao ngăn việc bị ghi nhớ. Mục này khởi đi từ thực tiễn thiết kế của vài benchmark công khai và khép lại bằng một câu hỏi thực tế hơn — nhiệm vụ trong tập đánh giá tự dựng nên đến từ đâu.

### Đối chiếu ngang các lựa chọn thiết kế giữa các benchmark

Việc có hay không có đối tượng tương tác, đã phân biệt ở mục trước, chỉ là lớp khác biệt đầu tiên ở tầng môi trường; những chia rẽ ở tầng tập dữ liệu mới phản ánh rõ hơn các đánh đổi thiết kế. Bảng 7-2 đặt cạnh nhau vài benchmark thường được trích dẫn.

Bảng 7-2 Các lựa chọn thiết kế then chốt của một số benchmark cho Agent

| Benchmark | Năng lực được đo | Nguồn nhiệm vụ | Ai đóng vai môi trường | Bộ kiểm chứng |
|---|---|---|---|---|
| τ²-bench | Tương tác người-máy và gọi công cụ trong chăm sóc khách hàng | Viết tay + sinh tổ hợp | Bộ mô phỏng người dùng + CSDL nghiệp vụ | Bốn tầng kiểm tra được `reward_basis` gộp thành nhị phân |
| SWE-bench Verified | Phát triển phần mềm, coding | Issue thật trên GitHub, sàng lọc thủ công | Kho mã + bộ kiểm thử | Kiểm chứng kép FAIL\_TO\_PASS / PASS\_TO\_PASS |
| AndroidWorld | Thao tác GUI điện thoại Android | Thực thể hóa mẫu có tham số | Trình giả lập Android thật | Khẳng định trạng thái UI cuối |
| OSWorld | Thao tác GUI desktop Linux | Khởi động từ trạng thái trung gian dựng sẵn | Máy ảo thật | 134 hàm đánh giá độc lập |
| Terminal-Bench | Thao tác terminal Linux, coding | Viết tay | Container Docker | Kiểm tra hệ thống tệp + chạy thật |
| GAIA | Trợ lý AI tổng quát thu thập thông tin | Viết tay + tệp đính kèm riêng | Internet mở | So khớp chuỗi chính xác |

### Bộ kiểm chứng

Agent rất dễ viết một bản báo cáo dài dòng nói rằng nhiệm vụ đã hoàn tất trọn vẹn, trong khi thực tế chưa hoàn tất gì cả. Khung đánh giá phải kiểm chứng những sự kiện mà máy có thể đối chiếu độc lập, chứ không phải lời tự thuật của Agent.

**SWE-bench Verified tách "đã sửa xong" thành hai mệnh đề độc lập.** Một là FAIL\_TO\_PASS: trước khi sửa thì trượt, sau khi sửa thì đạt, chứng minh vấn đề thực sự đã được giải quyết. Hai là PASS\_TO\_PASS: trước và sau khi sửa đều đạt, chứng minh không đưa vào khiếm khuyết mới. Chỉ kiểm cái thứ nhất thì Agent có thể lách bằng cách xóa hoặc sửa những khẳng định gây vướng; chỉ kiểm cái thứ hai thì chẳng khác gì không kiểm. Kiểm cả hai mới biến "đã sửa" và "không làm hỏng" thành hai kết luận chứng minh được riêng rẽ. Nó còn xác nhận tính ổn định của chính các bài kiểm thử, loại bỏ những bài lúc đạt lúc trượt (flaky test).

**Bộ kiểm chứng của OSWorld phát hiện được những tình huống bề ngoài đã xong nhưng thực chất lại sai.** Nó được trang bị 134 hàm đánh giá độc lập và quyền truy cập hệ điều hành đầy đủ, kiểm tra được cấu trúc hệ thống tệp, trạng thái tiến trình, kết nối mạng và trạng thái bên trong ứng dụng. Với nhiệm vụ cơ sở dữ liệu, kịch bản đánh giá không chỉ xác nhận tệp báo cáo tồn tại mà còn kết nối vào cơ sở dữ liệu để đối chiếu SQL có chạy đúng không; với nhiệm vụ trình duyệt thì phân tích cây DOM, xem cookie và localStorage, gửi yêu cầu kiểm chứng tới backend để xác nhận biểu mẫu thực sự có hiệu lực.

**Nhiệm vụ `build-linux-kernel-qemu` của Terminal-Bench** đòi hỏi biên dịch nhân Linux 6.9 từ mã nguồn, thêm một printk tùy chỉnh trong `start_kernel`, tạo initramfs và chạy nó trong QEMU; tiêu chí thành công là dòng thông báo tùy chỉnh đó xuất hiện trong log khởi động. Agent không thể ngụy tạo đầu ra, chỉ còn cách làm thật trọn quy trình.

### Phân tầng độ khó của nhiệm vụ

Tập nhiệm vụ đánh giá cần có nhiệm vụ ở các mức khó khác nhau. Nhờ vậy, khi năng lực mô hình tăng lên, tập nhiệm vụ đánh giá không nhanh chóng lỗi thời.

Toàn bộ 466 câu của GAIA chia thành ba mức khó: Level 1 chỉ cần một hai công cụ (người 93,9%, GPT-4 30,3%), Level 2 cần suy nghĩ nhiều bước (91,8% so với 9,7%), Level 3 cần tổ hợp phức tạp (87,3% so với 0%). Cách phân tầng này không chỉ dán nhãn độ khó mà còn có giá trị chẩn đoán: thất bại ở Level 1 trỏ tới việc dùng công cụ cơ bản, Level 2 trỏ tới lập kế hoạch nhiều bước và tích hợp thông tin, Level 3 trỏ tới tư duy chuỗi dài và quản lý độ phức tạp, và ba mức ứng với ba hướng cải thiện khác nhau.

Terminal-Bench trải từ việc đăng ký mô hình mlflow đơn giản, tới phá mật khẩu 7z ở mức trung bình, tới tích hợp nhiều thành phần máy chủ git và webserver ở mức khó, và cao nhất là phân tích mật mã vi sai FEAL.

τ²-bench còn thiết kế riêng **nhiệm vụ bẫy**: người dùng khẳng định "bộ phận chăm sóc khách hàng đã duyệt hủy" trong khi thực tế không đúng chính sách, nhằm kiểm tra Agent có giữ được phán đoán đúng dưới sức ép và thông tin sai lệch hay không.

### Phòng ngừa rò rỉ dữ liệu

**GAIA làm cho đáp án không thể tra thẳng trên internet.** Nhiệm vụ của nó đơn giản về khái niệm nhưng mở về đường đi: chẳng hạn xuất phát từ Ảnh thiên văn trong ngày của NASA ở một ngày cụ thể, nhận diện phi hành gia trong ảnh, tra ra nhóm phi hành gia mà người đó thuộc về, tính xem ai trong nhóm ở trong vũ trụ ít thời gian nhất, và xuất kết quả đúng định dạng "họ, phân tách bằng dấu chấm phẩy, có dấu phân cách hàng nghìn". Đáp án rất cụ thể và đúng sai được quyết định bằng so khớp chuỗi chính xác. Việc chống rò rỉ dựa vào hai điều: một là câu hỏi phải kết hợp nhiều nguồn thông tin mới trả lời được, không trang web đơn lẻ nào cho ngay đáp án; hai là một phần nhiệm vụ có kèm tệp được làm riêng (PDF, âm thanh, hình ảnh không tồn tại trên internet).

**AndroidWorld sinh ra rất nhiều thực thể từ một mẫu duy nhất.** Nhiệm vụ của nó không phải văn bản tĩnh mà là mẫu có thể thực thể hóa động, ví dụ "đổi số điện thoại của liên hệ `[CONTACT_NAME]` thành `[NEW_PHONE]`", với giá trị tham số sinh ngẫu nhiên ở mỗi lần đánh giá. Điều này mang lại ba lợi ích: tham số mỗi lần một khác nên phát lại một chuỗi thao tác cố định là vô dụng; một mẫu có thể sinh ra gần như vô hạn thực thể; cố định một phần tham số và chỉ đổi phần còn lại thì đo được chính xác ảnh hưởng của một yếu tố cụ thể.

**Terminal-Bench nhúng mã định danh chim hoàng yến vào đề bài.** Mỗi câu mang một canary GUID; nếu mô hình xuất được nội dung chứa GUID đó thì tức là dữ liệu benchmark đã lọt vào tập huấn luyện. Nó không ngăn được rò rỉ nhưng khiến rò rỉ trở nên phát hiện được.

### Kiểm soát chất lượng và bảo trì dài hạn

Làm một tập đánh giá chất lượng cao là việc rất khó. Hình hài hiện nay của phần lớn các benchmark trên là kết quả của nhiều vòng vá lỗi sau khi bản đầu tiên được đưa vào dùng và lộ ra vấn đề. Chẳng hạn từ τ-bench sang τ²-bench có năm chỗ được thiết kế lại.

Thứ nhất, **chỉ dẫn nhiệm vụ quá chung chung khiến đáp án có thể đoán được**. Chỉ dẫn của bản đầu viết rộng, nên mô hình không cần thực sự làm rõ yêu cầu, chỉ cần đoán một quy trình theo lẽ thường cũng qua được. τ²-bench tách kịch bản thành hai cột `known_info` và `task_instructions`: cột trước khoanh vùng những gì người dùng biết, cột sau quy định cách tiết lộ. Những gì người dùng không biết thì Agent không đoán được, chỉ có thể tra ra.

Thứ hai, **điều kiện thành công chưa đủ chính xác khiến kiểm chứng phán sai**. Điều kiện kiểu "mạng đã khôi phục" không có ranh giới đối chiếu được. τ²-bench sửa thành "chỉ khi kiểm tra tốc độ trả về excellent mới coi là xong; poor, fair, good đều không chấp nhận". Thay đổi này nhắm vào **kiểu sửa cho có**, tức dập triệu chứng mà không giải quyết căn nguyên.

Thứ ba, **hành vi của bộ mô phỏng người dùng quá máy móc**. Người dùng mô phỏng ở bản đầu chỉ đáp lại thụ động. τ²-bench bổ sung cảm xúc (tỏ ra không hài lòng sau lần sửa đầu tiên thất bại), giới hạn kiên nhẫn (cắt cuộc trò chuyện khi giao tiếp quá kém hiệu quả) và yêu cầu neo vào sự kiện. Ba thứ cùng tác động khiến bộ mô phỏng vừa gần với người dùng thật vừa giữ được tính tái lập.

Thứ tư, **người dùng không chỉ tham gia đối thoại mà còn tham gia thao tác**. Miền telecom đưa vào môi trường điều khiển kép. Ở các đánh giá trước, chỉ Agent mới thay đổi được môi trường, trong khi ở những bối cảnh như hỗ trợ kỹ thuật thì một phần đáng kể hành động vốn phải do chính người dùng thực hiện trên thiết bị của họ. Điều khiển kép còn thêm một chiều cho việc kiểm chứng: sau khi người dùng đổi trạng thái, Agent phải gọi lại công cụ mới biết kết quả, nên kiểm chứng nay bao trùm cả câu hỏi "Agent có thực sự đọc được kết quả thao tác phía người dùng hay không".

Thứ năm, **thực thể nhiệm vụ được sinh động**. Các thực thể cụ thể của τ²-bench (tên người dùng, số máy, tổ hợp sự cố) có thể tham số hóa và sinh hàng loạt, cải thiện đồng thời độ phủ và khả năng chống rò rỉ.

**SWE-bench Verified: trước khi công bố đã loại bỏ 71% nhiệm vụ gốc.** OpenAI lấy ngẫu nhiên 1.699 trong số 2.294 nhiệm vụ gốc để đánh giá thủ công, tuyển 93 lập trình viên thạo Python soi từng cái một: mô tả vấn đề có rõ không, ca kiểm thử có phủ điều kiện biên không, kiểm thử có ổn định không, patch tham chiếu có đưa vào lỗi mới không, độ khó có hợp lý không. Cuối cùng chỉ 500 cái lọt. Tỷ lệ loại cao đem lại tỷ số tín hiệu trên nhiễu tốt hơn, và chi phí đánh giá cũng giảm khoảng 80%. Nhiệm vụ Agent phức tạp thường mất từ vài phút đến vài giờ, và chạy trọn một tập đánh giá bằng mô hình tiên phong nhiều khi tốn hàng nghìn đô la tiền token, nên giảm chi phí đánh giá là điều rất quan trọng.

**OSWorld: trong 15 tháng sau khi công bố đã lộ ra hơn 300 vấn đề.** Ra mắt tháng 4 năm 2024, nó nhanh chóng trở thành benchmark quan trọng cho đánh giá Agent đa phương thức, nhưng quá trình dùng rộng rãi sau đó phơi bày bốn loại vấn đề: vấn đề môi trường (trang web chặn thu thập, CAPTCHA, nội dung động thay đổi), vấn đề mô tả nhiệm vụ (diễn đạt mơ hồ), vấn đề logic kiểm chứng (quá chặt hoặc quá lỏng) và vấn đề trạng thái ban đầu (cấu hình chưa đủ). Nhóm ở Đại học Hồng Kông lập một tổ khoảng 10 người, phối hợp chặt chẽ suốt hai tháng với MoonShot AI, OpenAI, ByteDance Seed TARS, Anthropic, Simular và những đơn vị khác để sửa một cách hệ thống: vấn đề môi trường được giải quyết bằng khóa phiên bản và sao lưu ngoại tuyến, vấn đề mô tả bằng cách viết lại các diễn đạt mơ hồ, vấn đề kiểm chứng bằng cách dựng thủ công đường cơ sở đúng rồi chỉnh điều kiện, vấn đề trạng thái ban đầu bằng cách bổ sung kiểm tra tính đầy đủ.

> **Thí nghiệm 7-2 ★: Tự tay làm các nhiệm vụ benchmark**
>
> Hãy chọn nhiệm vụ từ GAIA, AndroidWorld, SWE-Bench Verified, Terminal-Bench và OSWorld-Verified rồi tự tay hoàn thành; với mỗi tập dữ liệu nên làm một dễ, một trung bình và một khó. Mức "khó" cũng là thử thách với con người.
>
> Làm xong hãy trả lời hai câu hỏi. Mô tả nhiệm vụ có nhiều cách hiểu hợp lý không, nếu có thì bộ kiểm chứng công nhận cách nào? Nếu định lách để qua mà không làm thật, đường rẻ nhất là gì, và bộ kiểm chứng có chặn được không?

### Ba nguồn của tập đánh giá

Có một quan điểm phổ biến rằng benchmark công khai phục vụ việc xếp hạng mô hình và ít liên quan tới nghiệp vụ thực. Đúng là điểm số benchmark công khai khó trực tiếp dẫn dắt quyết định sản phẩm, nhưng thủ pháp thiết kế của chúng hoàn toàn có thể chuyển giao. Độ sâu kiểm chứng, sinh có tham số, phòng rò rỉ và duy trì chất lượng — những điều bàn ở trên — chính là chỗ dễ bị bỏ sót nhất khi tự dựng tập đánh giá.

Tập đánh giá trong môi trường sản xuất thường có ba nguồn.

**Benchmark công khai** dùng để sàng lọc thô mô hình và học hỏi thủ pháp thiết kế, thường không dùng cho quyết định sản phẩm. Phân bố nhiệm vụ của chúng không trùng với phân bố nhiệm vụ nghiệp vụ thực; tăng hai điểm phần trăm trên GAIA không có quan hệ tất yếu với tỷ lệ hoàn tiền thành công.

**Tập nghiệp vụ tự dựng** bao phủ phân bố nhiệm vụ thực và có thể làm căn cứ cho việc chọn mô hình cũng như các quyết định thiết kế Harness. Chẳng hạn τ²-bench có thể dùng ngay làm bộ khung cho bất kỳ hệ thống đánh giá nào cần người dùng mô phỏng; chỉ cần thay dữ liệu miền và bộ công cụ.

**Dòng chảy ngược từ trajectory sản xuất** đến từ các thất bại thật trên hệ thống: người dùng đính chính rõ ràng, người dùng bấm không hài lòng, và những ca được phát hiện về sau qua kiểm tra trạng thái, bộ kiểm chứng theo luật hoặc rà soát bằng LLM. Sau khi quy trách nhiệm thất bại, chúng lắng lại thành các ca hồi quy. Cách làm cụ thể xem hai mục "Quy trách nhiệm thất bại" và "Nhiệm vụ hồi quy đầu-cuối và nhiệm vụ hồi quy trajectory prefix" phía sau. Nguồn này tốn kém nhất và cũng chính xác nhất, vì nó đến thẳng từ những vấn đề người dùng thực sự gặp phải.

Ở giai đoạn khởi đầu thường chỉ có benchmark công khai và một ít tập nghiệp vụ viết tay; sau khi hệ thống chạy sản xuất một thời gian, các ca chảy ngược từ trajectory sản xuất sẽ thành phần chính.

## Phương pháp đánh giá tự động

Các benchmark bàn ở những mục trước có một điểm chung: bộ kiểm chứng của chúng gần như đều tất định. SWE-bench chạy bộ kiểm thử, AndroidWorld khẳng định trạng thái UI cuối, GAIA so khớp chuỗi chính xác, và bốn tầng kiểm tra của τ²-bench cũng đều do mã thực thi. Lựa chọn này có lý do đầy đủ: kiểm chứng tất định không phát sinh thêm chi phí mô hình, kết quả tái lập hoàn toàn, có thể đưa vào tích hợp liên tục như một bài kiểm thử đơn vị, và tiện cho việc xếp hạng giữa các mô hình.

Cái giá là nó chỉ đánh giá được kết quả cuối đúng hay sai, chứ không nêu ra nguyên nhân của lỗi. Nhiệm vụ thất bại của τ²-bench rốt cuộc được 0 điểm, và con số 0 ấy không cho biết Agent sai ở khâu chọn thuê bao hay bỏ sót bước nạp dữ liệu, càng không chỉ ra bước tiếp theo cần sửa gì. Với một benchmark công khai dùng để xếp hạng, đây không phải khiếm khuyết; với một hệ thống sản xuất cần cải tiến liên tục, đó lại đúng là thông tin cần nhất.

Bối cảnh sản xuất còn một khó khăn nữa: rất nhiều phán đoán vốn không thể viết thành khẳng định mà mã kiểm tra được. Một thư trả lời khiếu nại có chừng mực hay không, một báo cáo khảo sát có bỏ sót thông tin then chốt hay không, một lần truy hồi ký ức có nhầm quan hệ giữa các nhân vật hay không — những thứ này không có trạng thái cuối duy nhất để tra, cũng không thể phán bằng so khớp từ khóa.

Vì vậy, khi đi từ benchmark công khai sang đánh giá trong môi trường sản xuất, cách kiểm chứng cần dịch sang phải dọc theo một phổ mà trục hoành là **mức độ kiểm chứng được bằng máy** của nhiệm vụ, như Hình 7-4.

![Hình 7-4 Phổ các cách kiểm chứng: từ kiểm chứng tất định đến phán xét bằng mô hình](images/fig7-4.svg)

Hai công cụ ở nửa phải của phổ vì thế trở thành trụ cột của đánh giá sản xuất: **Rubric** tách câu hỏi mơ hồ "tốt hay không" thành nhiều chiều chấm điểm riêng rẽ, còn **LLM-as-a-Judge** đảm nhận việc chấm khi thiếu tiêu chí tất định. Chỉ khi kết hợp cả hai mới có thể quy một tỷ lệ thất bại mơ hồ trở lại thành những vấn đề cụ thể có thể bắt tay vào sửa; kết hợp thêm **quy trách nhiệm thất bại** ở nửa sau mục này thì tạo thành vòng khép kín đầy đủ của đánh giá Agent sản xuất.

Cần nói rõ, dịch sang phải không có nghĩa là từ bỏ nửa trái. Mọi kiểm tra có thể viết thành khẳng định trong chương trình thì nên giữ nguyên là khẳng định, còn phán xét bằng LLM chỉ dùng cho những chiều thực sự không thể phán bằng máy. Kiểm tra tất định rẻ hơn, ổn định hơn, và cũng hợp hơn để chạy lâu dài như một bài kiểm thử hồi quy.

### LLM-as-a-Judge: Cốt lõi của đánh giá tự động

![Hình 7-5 Quy trình LLM-as-a-Judge ](images/fig7-5.svg)

Tại sao bạn cần LLM-as-a-Judge? Đối với các nhiệm vụ mở (chẳng hạn như tạo báo cáo, xử lý khiếu nại của khách hàng, nội dung sáng tạo), không có câu trả lời tiêu chuẩn nào có thể được so sánh tự động và việc đánh giá thủ công rất tốn kém và khó mở rộng quy mô. LLM-as-a-Judge cân bằng quy mô tự động hóa với chuyên môn của con người bằng cách đánh giá các mô hình ngôn ngữ dựa trên tiêu chí chấm điểm do chuyên gia xác định (Rubric). Tuy nhiên, phương pháp này cũng có những hạn chế đã biết: mô hình đánh giá có thể có những thành kiến riêng (điển hình nhất là **thành kiến về độ dài** - có xu hướng cho điểm cao hơn đối với những câu trả lời dài hơn và chi tiết hơn, ngay cả khi nội dung không chính xác hơn) và nhiều đánh giá cho cùng một thông tin đầu vào cũng có thể dao động. Sự thiên vị về chiều dài đặc biệt đáng được đề phòng cho từng cá nhân. Có ba phương pháp thường được sử dụng: xử phạt rõ ràng tính dài dòng trong Rubric và đặt giới hạn trên về độ dài của câu trả lời cho các nhiệm vụ tương tự; khi so sánh cặp đôi, kiểm soát độ dài của hai ứng viên sao cho tương đương nhau trước khi đánh giá; và thường xuyên kiểm tra mối tương quan giữa điểm số và độ dài câu trả lời - nếu điểm cao hầu như luôn đi kèm với câu trả lời dài, điều đó có nghĩa là đánh giá đã bị sai lệch về độ dài và cần phải sửa lại Rubric. Để giải quyết những thách thức này một cách có hệ thống, thiết kế Rubric phải tuân thủ các nguyên tắc sau:

**Rubric (tiêu chí chấm điểm): LLM là cơ sở để đánh giá.**

**Rubric Bốn quy tắc**(Scale AI, “Rubrics as Rewards”):

(1) **Dựa trên hướng dẫn của chuyên gia** - phải phản ánh kiến thức về lĩnh vực đó và nắm bắt được các sự kiện cốt lõi cũng như các bước lập luận. Ví dụ: Rubric dành cho Hỏi đáp y tế cần bao gồm các tiêu chuẩn chẩn đoán và các lỗi y tế cần tránh. Rubric thiếu nền tảng chuyên môn nên chỉ nắm bắt được những đặc điểm bề ngoài như khả năng lưu loát về ngôn ngữ.

(2) **Thông tin toàn diện** - bao gồm tính chính xác thực tế, tính mạch lạc hợp lý, tính đầy đủ, tính an toàn và không chỉ xác định các tiêu chuẩn tích cực mà còn xác định **cạm bẫy** - tức là các lỗi phổ biến có nguy cơ cao, chẳng hạn như đề xuất các liệu pháp chưa được chứng minh trong tư vấn y tế.

(3) **Trọng lượng tầm quan trọng tiêu chuẩn** - được chia thành các vật phẩm thiết yếu (Essential), vật phẩm quan trọng, vật phẩm tùy chọn và vật phẩm bẫy. Hỗ trợ **cơ chế phủ quyết một phiếu (Phủ quyết)**: Ví dụ: trong các tình huống dịch vụ khách hàng, ảo tưởng (bịa đặt thông tin sai lệch) là một phương diện phủ quyết điển hình - cho dù hiệu suất ở các phương diện khác có xuất sắc đến đâu, miễn là thông tin sai lệch xuất hiện thì nó phải được phủ quyết. Điều này cũng giúp ngăn chặn gian lận phần thưởng nhồi nhét từ khóa.

(4) **Đánh giá độc lập** - Mỗi mục đánh giá có thể hoạt động độc lập và không phụ thuộc vào kiến thức miền của người đánh giá. Tránh tiêu chí trừu tượng “câu trả lời thể hiện sự hiểu biết sâu sắc” và thay vào đó hãy sử dụng tiêu chí có thể kiểm chứng được là “trích dẫn ít nhất hai lý thuyết có thẩm quyền và giải thích chính xác cách hỗ trợ kết luận”.

Thực hành chính: Xác định thang điểm có thể kiểm chứng một cách khách quan cho từng khía cạnh và cung cấp các ví dụ cụ thể cũng như các trường hợp đặc biệt để giúp phân biệt các tình huống không rõ ràng. Chúng ta phải chủ động đề phòng **Reward Hacking** - tức là Agent tìm "lối tắt" để đạt điểm cao mà không thực sự hoàn thành nhiệm vụ - trừng phạt rõ ràng những ảo tưởng, làm hài lòng người dùng, nhồi nhét từ khóa, tránh những câu hỏi khó. Rubric là một sản phẩm lặp đi lặp lại - thông qua việc thu thập thử nghiệm và sự đồng thuận của người đánh giá, nó dần dần được cải thiện và dần dần phát triển từ các nguyên tắc trừu tượng thành một bộ trường hợp chi tiết.

Lấy bộ nhớ người dùng Agent làm ví dụ, Rubric hoàn chỉnh đáp ứng bốn tiêu chí sẽ được hiển thị. Câu hỏi kiểm tra: “Bác sĩ nhi khoa của con gái tôi là ai?” (Câu trả lời cần phải có sự liên quan giữa hai cuộc trò chuyện: cuộc trò chuyện đầu tiên đề cập đến "Tên con gái tôi là Lily" và cuộc trò chuyện thứ hai đề cập đến "Tôi đưa Lily đến gặp bác sĩ Chen").

```yaml
rubric:
  dimensions:
- Tên: đúng sự thật
cân nặng: thiết yếu # Vật dụng cần thiết
      scoring:
4_Xuất sắc: "Trả lời bác sĩ Chen chính xác và liên quan đến con gái Lily"
3_Tốt: "Bác sĩ Chen trả lời chính xác, nhưng không đề cập đến việc ông là bác sĩ của Lily"
2_Pass: "Bác sĩ được cung cấp chính xác nhưng có thêm thông tin không chắc chắn"
1_Không thành công: "Tên bác sĩ được đưa sai hoặc câu trả lời là "Tôi không biết"

- Tên: tính toàn vẹn thông tin
trọng lượng: quan trọng # mục quan trọng
      scoring:
4_Excellent: "Chủ động cung cấp các thông tin liên quan (như thời gian điều trị lần cuối, kết quả chẩn đoán)"
3_Tốt: "Đã trả lời các câu hỏi cốt lõi và không bỏ sót"
2_Pass: "Đã trả lời câu hỏi cốt lõi nhưng bỏ qua thông tin liên quan có thể sử dụng được"
1_Fail: "Thiếu thông tin chính"

- Tên: Nghĩ Đúng
      weight: important
      scoring:
4_Xuất sắc: "Liên kết chính xác hai tin nhắn chéo phiên 'con gái=Lily' và 'Bác sĩ của Lily=Bác sĩ Chen'"
3_Tốt: "Mối tương quan đúng nhưng lối suy nghĩ chưa đủ rõ ràng"
2_Pass: "Một số mối tương quan là chính xác"
1_Fail: "Liên kết sai (chẳng hạn như coi bác sĩ của chính người dùng là bác sĩ của con gái mình)"

- Tên: Phát hiện ảo giác
trọng lượng: quyền phủ quyết # Mục quyền phủ quyết: một khi được kích hoạt, tổng số điểm sẽ được đặt lại về 0
      scoring:
pass: "Tất cả thông tin có thể được truy tìm tới các bản ghi cuộc trò chuyện lịch sử"
thất bại: "Thông tin bịa đặt không tồn tại trong cuộc trò chuyện (chẳng hạn như ngày điều trị y tế hư cấu, kết quả chẩn đoán)"

  edge_cases:
- "Nếu người dùng có nhiều con gái và họ gặp các bác sĩ khác nhau, họ nên hỏi đó là con gái nào."
- "Nếu 'Bác sĩ Chen' và 'Bác sĩ Chen' đều tồn tại trong ký ức thì họ nên được công nhận là cùng một người"
```

**Rubric Tốt so với Rubric Xấu**: Mỗi hộp xếp hạng ở trên đưa ra một hành vi cụ thể có thể kiểm chứng ("Tiến sĩ Chen đã trả lời chính xác"), thay vì "thể hiện sự hiểu biết sâu sắc về trí nhớ" và các mô tả khác không thể đánh giá khách quan. Mục từ chối làm rõ điểm mấu chốt: ngay cả khi tất cả các chiều không gian khác đều là điểm đầy đủ, một khi ảo giác xảy ra, nó sẽ bị tính trực tiếp bằng 0.

Đưa Rubric cùng câu trả lời thực tế của Agent cho mô hình đánh giá để nhận điểm và lý do theo từng tiêu chí. Khi tổng hợp hàng chục ca rồi xem lại các trajectory có điểm thấp, ta có thể biến một nhận xét mơ hồ như “tỷ lệ thành công giảm” thành chẩn đoán cụ thể: không truy xuất được dữ kiện, nối sai quan hệ giữa các nhân vật, hay tự thêm thông tin không có căn cứ. Rubric vì thế không chỉ cho biết hệ thống đạt bao nhiêu điểm, mà còn chỉ ra nên sửa ở đâu.

Dưới đây lấy bộ nhớ người dùng làm một trường hợp cụ thể, để cho thấy cách đưa phương pháp tổng quát này xuống thành tập đánh giá và bộ kiểm chứng chạy được.

> **Thử nghiệm 7-3 ★★: Xây dựng hệ thống đánh giá bộ nhớ người dùng dựa trên Rubric**
>
> **Điều kiện tiên quyết**: Cần phải hoàn thành Thử nghiệm bộ nhớ người dùng Chương 3 (`chapter3/user-memory-evaluation`).
>
> Thử nghiệm này yêu cầu chuyển đổi khung `chapter3/user-memory-evaluation` trong Chương 3 và nâng cấp cơ chế tính điểm hiện tại dựa trên LLM-as-a-Judge đơn giản thành hệ thống đánh giá Rubric đa chiều có cấu trúc. Hệ thống hiện tại sử dụng một lệnh gọi LLM duy nhất để trả về đạt/không đạt cùng với lý do đánh giá và thiếu khả năng chẩn đoán có cấu trúc.
>
> Thiết kế khung Rubric đa chiều thống nhất phù hợp cho tất cả các nhiệm vụ ba cấp. Các khía cạnh đánh giá bao gồm: tính chính xác về mặt thực tế (Độ chính xác - bao nhiêu thông tin được cung cấp là chính xác) để xác minh xem số/ngày/tên có nhất quán với thông tin được ghi nhớ hay không; tính đầy đủ thực tế (Nhớ lại - bao nhiêu thông tin cần cung cấp được thu hồi (tối đa) xác minh rằng tất cả thông tin liên quan đã được cung cấp và không thiếu nội dung chính; tính đúng đắn của tư duy kiểm tra xem các mối quan hệ và logic tiềm ẩn giữa thông tin có được hiểu chính xác hay không; chủ động suy nghĩ đánh giá xem các đề xuất hoặc lời nhắc rủi ro ngoài câu trả lời trực tiếp có được đưa ra khi thích hợp hay không; phát hiện ảo giác đảm bảo rằng thông tin không tồn tại trong bộ nhớ không bị giả mạo.
>
> Hệ thống chấm điểm 4 cấp độ (xuất sắc/tốt/đạt/rớt), mỗi cấp độ được trang bị các tiêu chí cụ thể thay vì mô tả trừu tượng. Thứ nguyên ảo giác được đặt làm vật phẩm phủ quyết. Cung cấp các ví dụ và trường hợp đặc biệt cho từng chiều.
>
> **Thử nghiệm 7-4 ★★: Đánh giá so sánh giữa Thẻ JSON nâng cao và RAG**
>
> **Điều kiện tiên quyết**: Cần phải hoàn thành Chương 3 Bộ nhớ người dùng và Thử nghiệm RAG (`chapter3/user-memory`, `chapter3/agentic-rag-for-user-memory`).
>
> **Mục tiêu**: So sánh công bằng phạm vi hiệu quả của bộ nhớ có cấu trúc và truy xuất phi cấu trúc trên cùng một bộ đánh giá. Tái sử dụng hai dự án ở Chương 3 và so sánh ba cấu hình trên 60 ca của `chapter3/user-memory-evaluation`: chỉ dùng Advanced JSON Cards, chỉ dùng RAG, và cấu hình kết hợp giữ các dữ kiện cốt lõi trong context còn hội thoại gốc được truy xuất khi cần.
>
> **Chấp nhận**: Ghi lại tỷ lệ thành công, số bước trung bình, số lần gọi công cụ, độ trễ và chi phí ở ba mức độ phức tạp (thu hồi cơ bản / phân biệt nhiều phiên / liên kết ẩn giữa các phiên) và làm rõ ranh giới lỗi của từng giải pháp - điều gì bị mất trong cấu trúc, điều gì bị bỏ sót khi truy xuất và liệu có sự phối hợp thực sự trong quá trình trộn hay không. Xem kho lưu trữ hỗ trợ để biết chi tiết cấu hình và trường hợp thử nghiệm.
>

Thử nghiệm đi kèm dùng cùng 60 câu hỏi cho ba hệ thống và lưu lại 180 trajectory gọi API thực. Bảng 7-3 ghi cả số câu thành công bên cạnh tỷ lệ tổng thể để kích thước mẫu không bị che khuất.

Bảng 7-3 Tỷ lệ thành công theo độ khó của ba hệ thống bộ nhớ

| Hệ thống | Nhớ lại cơ bản | Phân giải nhiều phiên | Liên hệ ẩn giữa các phiên | Tổng thể |
|---|---:|---:|---:|---:|
| Advanced JSON Cards | 95% | 60% | 50% | 68.3% (41/60) |
| RAG | 90% | 40% | 15% | 48.3% (29/60) |
| Kết hợp | 80% | 70% | 50% | 66.7% (40/60) |

Đáng chú ý nhất là phương án lai không tự nhiên thắng thế. Ở 3 câu nó làm được điều mà cả hai phương án đơn lẻ đều không làm được, nhưng ở 8 câu khác lại kém phương án đơn lẻ tốt hơn; so với phương án đơn lẻ tốt nhất trên từng câu, tỉ lệ thành công trung bình của nó ngược lại còn thấp hơn. RAG thuần không chênh nhiều so với thẻ có cấu trúc ở các câu hồi tưởng cơ bản, nhưng vừa sang câu liên kết xuyên phiên thì tỉ lệ thành công tụt xuống 15%. Còn một con số dễ bị bỏ qua: trong 180 lần chấm, phủ quyết ảo giác kích hoạt 28 lần—đủ thấy mục phủ quyết tuyệt đối quan trọng đến đâu.

**Các vấn đề về mô hình tương đồng và đánh giá đa nguồn.**

Khi Agent thuộc cùng dòng với mô hình đánh giá, Agent có thể học cách khai thác các sở thích và điểm mù của mô hình đánh giá.

**Đây là điều mà Định luật Goodhart nói: khi một số liệu trở thành mục tiêu tối ưu hóa, thì số liệu đó không còn là một số liệu tốt nữa.** Agent Càng rèn luyện hoặc điều chỉnh theo một hệ thống tính điểm nhất định, bạn càng có xu hướng khai thác những sơ hở của hệ thống này thay vì thực sự cải thiện khả năng của mình.

Bí mật hơn, Agent cũng sẽ dần học cách tránh những loại lỗi mà mô hình đánh giá không giỏi phát hiện, khiến hệ thống tính điểm trông bình thường.

Policy giảm nhẹ là **đánh giá không đồng nhất nhiều nguồn** - sử dụng nhiều LLM từ các họ mô hình khác nhau để đánh giá riêng (ví dụ: Agent sử dụng Claude và GPT-5 và Gemini được sử dụng để đánh giá). Thành kiến của các gia đình khác nhau thường trực giao, Agent khó có thể “lừa dối” tất cả giám khảo cùng một lúc. Sử dụng cùng một Rubric để đảm bảo mọi người đều đánh giá cùng một mục tiêu và tổng hợp kết quả thông qua kiểm tra tính nhất quán hoặc mức trung bình có trọng số. Giai đoạn triển khai có thể được đánh giá nhanh chóng bằng một mô hình duy nhất, nhưng việc kiểm tra chất lượng phải được thực hiện thường xuyên với sự đánh giá hoàn chỉnh từ nhiều nguồn.

Đánh giá đa nguồn giải quyết vấn đề “sử dụng mô hình nào để đánh giá”; Bước tiếp theo là giải quyết vấn đề "đánh giá phương thức nào" - mở rộng khả năng của LLM-as-a-Judge từ văn bản sang giọng nói, hình ảnh và video là một khía cạnh khác của phạm vi đánh giá.

**Đa phương thức LLM-as-a-Judge.**

Đánh giá đa phương thức mở rộng LLM-as-a-Judge sang các lĩnh vực giọng nói, hình ảnh và video. Bốn hướng chung như sau.

- **Đánh giá TTS**(TTS hay còn gọi là Text-to-Speech, chuyển văn bản thành giọng nói): đánh giá độ chính xác, độ tự nhiên, tính nhất quán về âm sắc và biểu hiện cảm xúc. Các kích thước này có thể phát hiện ra các vấn đề về ngữ điệu khó nắm bắt bằng WER (Tỷ lệ lỗi từ) truyền thống.
- **Đánh giá ASR**(ASR là Nhận dạng giọng nói tự động, nhận dạng giọng nói): Đưa ra phán đoán tác động ngữ nghĩa - Lỗi nhận dạng "Today's fashion" là vô hại, nhưng "chuyển một nghìn" thành "mười nghìn" có thể gây ra hậu quả nghiêm trọng.
- **Đánh giá giao diện người dùng**: Sử dụng cơ chế **Người đề xuất-Người đánh giá**(Proposer-Reviewer) để kiểm tra các vấn đề như tràn văn bản, độ tương phản màu, vị trí nút, v.v. Ở đây, người đề xuất-người đánh giá được sử dụng làm phương pháp đánh giá, khác với cách sử dụng làm thành phần hệ thống tạo trong Chương 5, nhưng cơ chế cốt lõi giống nhau - một mô hình được tạo và một mô hình khác được xem xét độc lập.
- **Đánh giá video clip**: Xác minh điểm bắt đầu và điểm kết thúc chính xác của clip cũng như việc áp dụng các hiệu ứng đặc biệt thông qua các khung hình chính.

> **Thử nghiệm 7-5 ★★: Xây dựng quy trình đánh giá chất lượng TTS hoàn toàn tự động**
>
> Thử nghiệm này yêu cầu thiết kế và triển khai hệ thống đánh giá chất lượng LLM-as-a-Judge TTS đa phương thức hoàn chỉnh ngay từ đầu.
>
> Thiết kế TTS đa chiều Rubric: Chiều chính xác xác minh xem tất cả các từ có được đọc chính xác hay không (không thiếu sót/đọc sai/thêm), chiều tự nhiên đánh giá xem lời nói có mượt mà hay không (có cảm giác máy móc, ngắt quãng không tự nhiên và nhịp điệu có phù hợp với thói quen của con người hay không), chiều biểu hiện cảm xúc kiểm tra xem giọng điệu có phù hợp với màu sắc cảm xúc của văn bản hay không (giọng lên của câu nghi vấn, nhấn mạnh) về câu cảm thán, tốc độ nói chậm và âm trầm của nội dung buồn) và chiều nhất quán âm sắc đánh giá độ giống nhau của người nói khi có giọng tham chiếu (mô hình đa phương thức đồng thời nhận cả giọng tham chiếu và so sánh giọng tổng hợp).
>
> Xây dựng kho ngữ liệu đa dạng về độ dài, thể loại, cảm xúc, con số, tên riêng, cách phát âm dễ nhầm và phương ngữ. Mô-đun TTS có thể kết nối OpenAI, ElevenLabs, Fish Audio, Minimax hoặc Doubao. Một judge đa phương thức nhận trực tiếp audio sẽ đánh giá đồng thời giọng tổng hợp, văn bản gốc, audio tham chiếu và Rubric. Ngoài phân tích điểm theo từng chiều, cần lưu tên model đánh giá cùng hash của audio tham chiếu và từng ứng viên để có thể kiểm tra lại kết quả.
>

Kho đi kèm lưu một pilot nghe trực tiếp quy mô nhỏ. OpenAI và Fish Audio mỗi bên tạo bốn mẫu—số, từ dễ đọc nhầm, câu dài và giọng hào hứng—rồi Voxtral chấm cả tám audio theo bốn chiều trên. Hai bên cùng đạt 5.00 về độ chính xác và 4.00 về độ tự nhiên. Fish Audio đạt 4.00 về biểu cảm và 3.00 về độ nhất quán giọng; OpenAI lần lượt là 3.75 và 2.75. Tách các chiều giúp thấy khác biệt về giọng điệu và âm sắc ngay cả khi khả năng đọc đúng văn bản ngang nhau.

Tám mẫu chưa đủ để kết luận dịch vụ nào tốt hơn. Mỗi bên chỉ có bốn mẫu, và quan trọng hơn, audio tham chiếu cố định được tạo bởi Fish S1 nên phép so độ giống giọng vốn đã có lợi cho Fish Audio. Nếu so TTS phổ thông, không nên đưa tiêu chí “giống giọng tham chiếu Fish” vào tổng điểm. Nếu so voice cloning, mọi hệ thống phải bắt chước cùng một người nói và điểm của model cần được hiệu chỉnh bằng nghe mù của con người. **Việc chọn câu trả lời, hình ảnh hay audio tham chiếu là một phần của thiết kế đánh giá, không phải bước chuẩn bị trung tính trước thí nghiệm.**

Rubric viết tay phù hợp để nhanh chóng tạo các chiều chẩn đoán này. Khi quy mô tăng, có thể huấn luyện **mô hình phần thưởng sinh** để tự động hóa việc chấm; Chương 8 trình bày phương pháp huấn luyện.

Điểm số mà mô hình chấm đưa ra chỉ nói kết quả tốt hay xấu; muốn biến kết quả ấy thành một vấn đề sửa được thì còn phải định vị xem thất bại thực sự bắt đầu từ bước nào.

### Quy trách nhiệm thất bại: Định vị lỗi đầu tiên trong trajectory

Đánh giá end-to-end thường chỉ trả lời “đạt” hoặc “không đạt”. Để kết quả dẫn tới sửa chữa, với mỗi trajectory thất bại hãy ghi loại lỗi, bước đầu tiên không chấp nhận được, lời gọi công cụ hoặc đầu ra mô hình liên quan và bằng chứng có thể kiểm tra. Tín hiệu bad case gồm người dùng sửa trực tiếp, phản hồi tiêu cực hoặc kiểm tra trạng thái/quy tắc sau đó. LLM có thể hỗ trợ nhưng vẫn cần người đọc vì nguyên nhân thường là vấn đề sản phẩm.

Với Coding Agent, các nhóm ban đầu là thiếu quy trình/quy tắc kho, lỗi công cụ/định dạng, kết thúc bất thường và lỗi logic/độ hoàn tất. Lưu bản ghi JSON/YAML có số bước, công cụ, quan sát, nguyên nhân gốc so với hậu quả, khả năng khôi phục và độ tin cậy, cùng trạng thái, phiên bản và trajectory đầy đủ.

Xây dựng hệ thống quy trách nhiệm lỗi đòi hỏi lập trình viên kiên nhẫn đọc và phân tích các trajectory có vấn đề trong môi trường thật. LLM có thể hỗ trợ nhưng không thể thay thế con người, vì **quy trách nhiệm lỗi thường phơi ra vấn đề sản phẩm** chứ không chỉ vấn đề kỹ thuật.

Khi sản phẩm hoàn thiện dần, bảng phân loại lỗi có thể gồm nhiều nhóm lớn, mỗi nhóm lại có các nhóm nhỏ, cuối cùng lên tới hàng trăm loại. Chính các nhóm lỗi và cách quy trách nhiệm này sẽ trở thành prompt hoặc Skill cho một Agent chuyên chú giải quy trách nhiệm.

Lấy Coding Agent làm ví dụ, một bảng phân loại khởi đầu dùng được như sau.

| Loại lỗi | Biểu hiện điển hình | Cách định vị lỗi đầu tiên |
| --- | --- | --- |
| Hiểu yêu cầu và xử lý mơ hồ | Thứ làm ra không phải thứ người dùng yêu cầu: bỏ sót một điều kiện trong yêu cầu, hiểu phạm vi rộng quá hoặc hẹp quá; kho có hai tệp cấu hình trùng tên thì chọn đại một cái, không nói cũng không hỏi | Dùng LLM đối chiếu từng mục giữa yêu cầu gốc và **những gì Agent thực sự làm** (chuỗi hành động); định vị điểm lệch đầu tiên ở mức kết quả, rồi truy ngược về lần gọi công cụ hay câu trả lời đã gây ra nó |
| Thiếu quy trình hoặc quy ước | Commit mà không chạy unit test; sửa code trước khi viết Plan; đưa vào phụ thuộc ngoài trong khi kho đã có thứ tương đương nội bộ; đi vòng qua quy ước kiến trúc đã định | Tìm hành động đầu tiên vi phạm quy ước quy trình phát triển — lần `git commit` đầu, lần ghi tệp đầu — rồi xem trước đó nó có đọc nguồn của quy ước hay không |
| Lỗi gọi công cụ | Sửa cùng một tệp thất bại lặp đi lặp lại; sai định dạng JSON/schema hoặc tham số; ký tự đặc biệt làm hỏng việc sao chép, escape hoặc ghi | Ghi lại lần sửa/công cụ thất bại đầu tiên kèm yêu cầu gốc và lỗi trả về; các lần thất bại sau là triệu chứng kế tiếp |
| Hack môi trường kiểm chứng | Sửa thẳng assertion, thêm `skip`, mock mất phần logic đang được kiểm thử; tuyên bố "test đã qua" trong khi chưa hề chạy | Lấy message đầu tiên sửa test hoặc logic kiểm chứng; rồi đối chiếu tuyên bố hoàn thành với các lệnh thực sự đã chạy trong trajectory để xác nhận nó có chạy thật không |
| Sửa không trọn vẹn | Đổi chữ ký hàm, cập nhật ba điểm gọi, nhưng bỏ sót điểm thứ tư — một lời gọi động, một binding ngôn ngữ khác, hoặc một schema | Lấy hiệu của tập phạm vi ảnh hưởng mà Agent tuyên bố với phạm vi thật, chọn thiếu sót đầu tiên, rồi xem lại nó đã tìm kiếm bằng từ khóa nào |
| Báo sai thông tin cho người dùng | Mọi lần gọi công cụ và trạng thái cuối đều đúng, nhưng thông tin nói với người dùng thì sai: sai số tiền, trạng thái, thời gian; mới làm một phần lại nói là xong hết; bỏ sót điều bắt buộc phải báo | Đối chiếu từng khẳng định sự kiện trong câu trả lời với giá trị công cụ trả về, lấy khẳng định đầu tiên không truy nguyên được hoặc mâu thuẫn với giá trị trả về |
| Hồi quy phi chức năng | Đổi API công khai hay schema mà không có script migration; xóa phần kiểm tra để cho qua | Lấy message đầu tiên thực hiện thay đổi đó, xem nó có ý thức được rằng mình đang động vào giao diện công khai hay cấu trúc cần migration hay không |
| Mô hình kết thúc bất thường | Đầu ra bị cắt giữa chừng, dừng vô cớ, quá thời gian, hoặc kết thúc mà chưa làm động tác khép lại | Định vị điểm kết thúc bất thường đầu tiên và phân biệt mô hình tự dừng, Harness hết giờ, và sự cố dịch vụ công cụ |
| Dừng tác vụ quá sớm | Tác vụ nhiều mục tiêu mới xong một phần; tuyên bố bất khả thi khi chưa thử hết các phương án hợp lý | Định vị quyết định đầu tiên bỏ sót mục tiêu hoặc từ bỏ thăm dò, và ghi tách khỏi thất bại ở khâu kiểm chứng cuối |

**Agent chú giải quy trách nhiệm có thể dùng LLM để phân tích nguyên nhân gốc trên quy mô lớn cho rất nhiều trajectory thật**, nhưng không được chỉ xuất ra một câu "nguyên nhân thất bại". **Bản ghi quy trách nhiệm phải có cấu trúc**: dùng JSON hoặc YAML, trích dẫn số bước cụ thể, tên công cụ và bằng chứng quan sát được; đồng thời phải tách nguyên nhân gốc khỏi hệ quả, đánh giá khả năng khôi phục và đưa ra mức tin cậy. Ví dụ, `edit_file` trả về lỗi không khớp `old_string`, sau đó Agent thử lại ba lần vẫn không ghi được tệp: nguyên nhân chính là lỗi sửa tệp và gọi công cụ, còn ba lần thử lại là hệ quả chứ không phải ba nguyên nhân gốc độc lập. Khi nhiều nhóm cùng xuất hiện, chọn nguyên nhân chính theo nguyên tắc "sớm nhất và giải thích được các thất bại tiếp sau", phần còn lại giữ làm nguyên nhân phụ. Ít nhất ba nhóm trong bảng trên có thể lọc trước bằng quy tắc rồi mới giao cho LLM định vị lỗi đầu tiên: đối chiếu tuyên bố hoàn thành với lệnh thực sự đã chạy; diff có chạm vào assertion của test và nhãn `skip` không; diff có đổi API công khai hay schema mà thiếu tệp migration không. Lọc bằng quy tắc trước, để LLM định vị sau, vừa rẻ hơn vừa chuẩn hơn so với đổ toàn bộ trajectory cho LLM.

Khi lưu bản ghi quy trách nhiệm, ngoài đầu ra của LLM còn phải lưu kèm mục tiêu tác vụ, trạng thái môi trường, phiên bản Agent, phiên bản bộ công cụ và toàn bộ trajectory, để có thể chuyển thành bài kiểm thử hồi quy.

Dưới đây trình bày ba loại lỗi tiêu biểu.

#### Vấn đề "làm đúng nhưng nói sai"

"Làm đúng nhưng nói sai" là nhóm dễ bị tỉ lệ thành công tổng thể che khuất nhất, vì phần lớn đánh giá chỉ kiểm tra trạng thái môi trường. τ²-bench chấm nhóm này riêng: trong 704 lượt chạy baseline đã công bố mà tác vụ có yêu cầu truyền đạt thông tin, 240 lượt thất bại, 162 trong số đó trượt ở khâu truyền đạt, và 80 lượt — một phần ba tổng số thất bại — có trạng thái môi trường đúng nhưng thông tin báo lại sai.

Kho đi kèm có một ca tương ứng. Với tác vụ nhập các khoản chi từ `expenses.jpg` vào ứng dụng sổ chi tiêu, Agent dùng 32 bước để cấp quyền, tìm kiếm, mở ảnh, điền từng dòng và lưu, **không bước nào trả về lỗi**, rồi tự tuyên bố hoàn thành; bộ kiểm tra báo rằng dòng lẽ ra phải được ghi — `Dress`, ¥436,35 — không tồn tại, và chẳng liên quan gì tới bốn dòng nó đã nhập. Ở bước 8, chính phần suy luận của nó ghi *"I cannot actually see the content/details of the expenses in the image"*: nó đã biết mình không lấy được dữ liệu, nhưng không dừng cũng không báo, và tới bước 11 bốn khoản chi bịa ra xuất hiện trong ghi chép, để rồi mọi lần nhập sau đó thực thi trung thành đúng những dữ liệu bịa ấy. Lỗi đầu tiên nằm ở bước 8, và bước đó không hề báo lỗi, cũng không phải một lần gọi công cụ. Nguyên nhân gốc của nó cũng dễ bị xếp nhầm: T3A là Agent thuần văn bản, không gian quan sát chỉ có cây phần tử và không có pixel ảnh, nên nguyên nhân không phải "mô hình không biết OCR" mà là thiếu kênh quan sát, cộng với việc không có một hành động thoát hợp lệ kiểu "không lấy được thông tin". Xếp nó thành vấn đề năng lực mô hình thì bước tiếp theo sẽ là đổi mô hình hoặc huấn luyện OCR; cách sửa thật sự là bổ sung kênh quan sát và hành động thoát.

> **Thử nghiệm 7-6 ★★: Quy trách nhiệm lỗi trên các trajectory của AndroidWorld**
>
> Thử nghiệm này luyện tập phương pháp quy trách nhiệm của mục này trên trajectory thật, không cần trình giả lập cũng không cần API mô hình. Tư liệu là bản ghi chạy T3A đã lưu trong `chapter7/android-world`: `t3a.md` chứa `Action`/`Reason`/`Summary` từng bước của mọi tác vụ, còn `t3a_failed.md` gom hơn năm mươi trajectory thất bại, mỗi trajectory kết thúc bằng phán quyết khách quan của bộ kiểm tra.
>
> Bước 1: Lấy mẫu. Rút ít nhất mười thất bại im lặng từ `t3a_failed.md` — những trajectory không hề có lỗi công cụ nào. Không lần gọi công cụ nào trả về lỗi, Agent tự tuyên bố hoàn thành hoặc cạn số bước, và chỉ phán quyết cuối của bộ kiểm tra mới đánh dấu thất bại.
>
> Bước 2: Định vị lỗi đầu tiên. Với mỗi trajectory, ghi số bước của lỗi đầu tiên và nêu rõ bước đó là một lần gọi công cụ hay một assistant message. Thất bại im lặng cần hai kỹ thuật: đối chiếu neo dữ kiện, rà các phát biểu của Agent với giá trị công cụ trả về và lấy điểm lệch đầu tiên; và chia đôi tiền tố trajectory, cắt trajectory tại bước k rồi bàn giao — nếu vẫn cứu được thì lỗi nằm sau k. Tìm từ khóa báo lỗi không thay thế được.
>
> Bước 3: Viết bản ghi có cấu trúc. Mỗi trajectory tạo ra một bản ghi JSON hoặc YAML gồm tên tác vụ, bước lỗi đầu tiên, loại lỗi, bên chịu trách nhiệm cho nguyên nhân gốc, trích dẫn làm bằng chứng, và tách nguyên nhân chính khỏi hệ quả.
>
> Bước 4: Đối chiếu với ghi chú có sẵn. So sánh kết quả với `t3a_failed_analysis.md` theo từng mục và ghi lại mọi bất đồng. Đặc biệt chú ý việc quy nguyên nhân gốc: ghi chú đó từng ghi thất bại chép ảnh là "mô hình thị giác thiếu OCR", nhưng không gian quan sát của T3A hoàn toàn không có pixel ảnh, nên nguyên nhân gốc thật sự là thiếu kênh quan sát. Một ghi chú quy trách nhiệm có sẵn không phải là đáp án chuẩn.
>
> Bước 5: Chuyển thành tác vụ hồi quy. Chọn ba trajectory có lỗi đầu tiên nằm ở assistant message, cắt tiền tố ngay trước lỗi đó, rồi viết tập hành động chấp nhận được và các hành động bị cấm để tạo thành tác vụ hồi quy tiền tố trajectory.
>

#### Lỗi định dạng tài liệu nhạy với phạm vi

Khi người dùng nói "định dạng dấu ngoặc kép sai", ta không thể biến điều đó thành một phép thay thế ký tự toàn cục. Ít nhất phải phân biệt dấu ngoặc thẳng ASCII (`"`, `'`), dấu ngoặc cong tiếng Trung (`“”`, `‘’`) và dấu backtick Markdown (`` ` ``). Cùng một ký tự đảm nhận vai trò cú pháp khác nhau trong văn xuôi tiếng Trung, nguyên bản tiếng Anh được trích, mã nội dòng, khối mã, chú thích mã, JSON và đường dẫn.

Dữ liệu đánh giá nên phân tích tài liệu thành các đoạn có phạm vi trước đã — ví dụ `ZH_PROSE`, `EN_PROSE`, `QUOTED_SOURCE`, `INLINE_CODE`, `CODE_BLOCK`, `CODE_COMMENT` và `JSON_OR_SCHEMA`. Mỗi đoạn lưu tập phép biến đổi được phép, các ký tự bắt buộc phải bảo vệ, và kết quả của bộ kiểm tra sau khi sửa. Ba trường hợp dưới đây không thể xử lý bằng cùng một quy tắc thay thế:

```text
Văn xuôi tiếng Trung: gọi phương thức `reset()`.
Nguyên bản tiếng Anh được trích: “Please restart the service.”
# khối mã dưới đây chỉ nhằm minh họa một phạm vi được bảo vệ
# Chú thích tiếng Trung: hiển thị "trạng thái hiện tại"
name = "status"
```

Hồi quy theo tiền tố quỹ đạo phải yêu cầu mô hình sửa tối thiểu, đồng thời kiểm tra phong cách tài liệu tiếng Trung, tỷ lệ giữ nguyên nguyên bản tiếng Anh, cú pháp mã và JSON, cùng khoảng cách chỉnh sửa trên phần văn bản không phải mục tiêu. Khi quy tắc không xác định được phạm vi, giữ nguyên văn bản gốc và yêu cầu làm rõ phải được tính là hành động được phép, chứ không phải một sửa đổi phỏng đoán tình cờ vượt qua.

#### Lỗi sao chép chính xác: từ `old_string` mismatch đến truy vết theo từng lớp

Lỗi `old_string` cũng không thể quy hết cho "mô hình chép sai". Với cùng một chuỗi, hãy lưu hash byte gốc, dãy code point Unicode và dãy token ID của tokenizer, rồi tìm khác biệt đầu tiên dọc theo chuỗi sau:

```text
byte file gốc → tool trả về → serialization của Harness → context model
→ output token → chuỗi decode → parse JSON/tool-call → tool matching
```

Bộ thăm dò đánh giá tối thiểu bao phủ việc nhắc lại trực tiếp, trích xuất từ ngữ cảnh dài, đặt vào đối số của tool, chọn giữa các chuỗi tương tự, cùng với khoảng trắng, xuống dòng, dấu gạch chéo ngược, ký tự tổ hợp Unicode và token tần suất thấp. Các chỉ số gồm byte-exact match, code-point-exact match, token-exact match, vị trí khác biệt đầu tiên và tỷ lệ thành công thực tế của tool. Nếu mô hình đúng ở thăm dò trực tiếp nhưng lời gọi tool vẫn thất bại, hãy sửa tokenizer, serialization, Harness hoặc giao thức tool; chỉ khi khác biệt đầu tiên xuất hiện ở chính đầu ra của mô hình thì mới chuyển trường hợp đó thành dữ liệu huấn luyện sao chép ở Chương 8.

### Tác vụ hồi quy end-to-end và hồi quy tiền tố trajectory

Quy trách nhiệm đã xác định lỗi đầu tiên và loại của nó; bước tiếp theo là viết mục tiêu sửa chữa thành một ca kiểm thử chạy lại được, tức **tác vụ hồi quy** (regression task). Ở đây cần hai lớp bổ trợ nhau: **tác vụ hồi quy end-to-end** kiểm chứng rằng thay đổi không phá vỡ toàn bộ luồng công việc; **tác vụ hồi quy tiền tố trajectory** (trajectory prefix) cắt lấy trạng thái ngay trước lỗi đầu tiên và chỉ kiểm chứng xem ranh giới quyết định đó đã được sửa hay chưa.

**Tác vụ hồi quy end-to-end** bắt đầu từ trạng thái ban đầu và yêu cầu của người dùng, để Agent hoàn tất trọn tác vụ, rồi kiểm tra trạng thái cuối, đầu ra bắt buộc và các điều kiện an toàn. Nó gần với kết quả sản xuất nhất, nhưng lại khó biết thất bại xảy ra ở bước nào. Nói chung, tác vụ hồi quy end-to-end dùng để kiểm chứng năng lực của Agent trên từng lĩnh vực có đúng như kỳ vọng không. Các bộ đánh giá chuẩn nêu trong chương này — OSWorld, AndroidWorld, tau-bench — đều là tác vụ hồi quy end-to-end.

**Tác vụ hồi quy tiền tố trajectory** đóng băng ngữ cảnh, hội thoại, giá trị công cụ trả về và trạng thái môi trường đã có, chỉ yêu cầu Agent suy nghĩ rồi thực hiện một hoặc vài hành động quan sát được kế tiếp. Chi phí thấp hơn, lại cô lập được vấn đề của một chính sách hay một công cụ. Với Agent cấp sản xuất cần độ tin cậy cao, xây bộ tác vụ tiền tố thường quan trọng hơn bộ end-to-end, và đòi hỏi lập trình viên kiên nhẫn dựng nên hệ phân loại thất bại cùng hệ thống quy trách nhiệm đã nói ở mục trước.

Đáp án của tác vụ tiền tố nên được định nghĩa là một **tập hành động chấp nhận được**, chứ không phải một hành động hay một câu trả lời duy nhất: có thể yêu cầu "đọc quy tắc kho trước", "hỏi người dùng trước" hoặc "từ chối thao tác nguy hiểm", đồng thời liệt kê các hành động bị cấm.

**Sau khi quy trách nhiệm xong là có thể dựng bộ dữ liệu đánh giá gồm cả tác vụ hồi quy end-to-end lẫn tiền tố trajectory.** Lấy Coding Agent làm ví dụ: thiếu quy trình thì sinh ra tác vụ end-to-end kèm tài liệu kế hoạch và điều kiện nghiệm thu bằng test; lỗi gọi công cụ thì cắt tiền tố tại chỗ hỏng rồi biên tập thành tác vụ biên, kiểm tra xem mô hình có sửa được định dạng, escape ký tự đặc biệt hay đổi sang công cụ phù hợp không; kết thúc bất thường thì thêm kịch bản phục hồi khi bị cắt, quá giờ và sự cố công cụ; lỗi về độ hoàn thành và logic thì thêm danh sách nhiều mục tiêu, nhắc việc còn lại và ranh giới "chưa chứng minh được là bất khả thi"; nhóm hiểu yêu cầu và mơ hồ thì đóng băng thành tiền tố những tác vụ có nhiều cách hiểu hợp lý, đưa "hỏi cho rõ trước" vào tập hành động chấp nhận được; nhóm vá triệu chứng và ngụy tạo kiểm chứng thì bổ sung vào nghiệm thu hai ràng buộc cứng là "không được sửa assertion của test" và "tuyên bố hoàn thành phải kèm đầu ra của lệnh đã thực sự chạy"; nhóm báo tin cho người dùng thì đặt assertion lên chính nội dung câu trả lời, chứ không chỉ kiểm tra trạng thái môi trường.

Bộ dữ liệu đánh giá là nền tảng cho post-training ở chương 8 và tự tiến hóa của Agent ở chương 9.

> **Thử nghiệm 7-7 ★★: Đánh giá ranh giới trajectory-prefix với nhiều mã hóa**
>
> Cung cấp bộ nhớ người dùng đã biết, chỉ dẫn hiện tại, trajectory prefix, kết quả công cụ và trạng thái môi trường; mô hình chỉ trả về hành động quan sát được kế tiếp. 11 ca được mã hóa bằng JSON Cards, Markdown và Python-like rồi kiểm tra bằng quy tắc xác định. 33/33 ô hoàn tất không lỗi API, mỗi cách mã hóa đạt 6/11; đổi biểu diễn không tự sửa được chính sách sử dụng.

Trong việc lựa chọn mô hình thực tế, câu hỏi chúng ta thường gặp là: "Cái nào tốt hơn, A hay B?" So sánh từng cặp cung cấp một cách đánh giá không dựa vào điểm số tuyệt đối.

### So sánh theo cặp và xếp hạng mô hình

![Hình 7-6 Xếp hạng Elo và xếp hạng so sánh ghép đôi ](images/fig7-6.svg)

**Xếp hạng Elo**(một hệ thống xếp hạng ban đầu được sử dụng trong cờ vua) định lượng khả năng tương đối của một mô hình thông qua một số lượng lớn các trận đấu theo cặp: chênh lệch điểm số càng lớn thì tỷ lệ thắng mong đợi của người chơi mạnh hơn càng cao. Ví dụ: nếu mô hình A đạt 1200 và mô hình B đạt 1000, hệ thống Elo sẽ dự đoán tỷ lệ thắng của A là khoảng 76%. Nếu B bất ngờ thắng, B sẽ được nhiều điểm hơn và A sẽ mất nhiều điểm hơn - kết quả ngược lại sẽ mang đến sự điều chỉnh điểm lớn hơn. Cơ chế này cho phép thứ hạng nhanh chóng hội tụ về đúng đẳng cấp. Cơ sở thống kê đằng sau nó là **mô hình Bradley-Terry**: mỗi mô hình được trừu tượng hóa thành một "điểm sức mạnh" tiềm năng. Xác suất thắng hoặc thua một cặp đấu được xác định bằng chênh lệch tỷ số giữa hai trận đấu. Elo là kỹ thuật triển khai hình thức cập nhật trực tuyến của mô hình này.

Chatbot Arena sử dụng các cuộc đấu tay đôi ngẫu nhiên ẩn danh - người dùng mù quáng chọn những câu trả lời tốt hơn mà không biết danh tính của mô hình, với thứ hạng bắt nguồn từ hàng triệu phiếu bầu. Ưu điểm của phương pháp này là không cần xác định “tiêu chuẩn tuyệt đối”, chỉ cần con người phán đoán “A hay B nào tốt hơn”. Nhưng có những hạn chế: kết quả xếp hạng phụ thuộc vào câu hỏi mà người dùng hỏi - nếu một số lượng lớn người dùng tình cờ đặt câu hỏi về lập trình, một mô hình giỏi lập trình sẽ được xếp hạng cao hơn, điều này có thể không phản ánh đúng đẳng cấp của nó trong các nhiệm vụ khác.

Khi LLM hoàn thành phán quyết ghép đôi thay vì con người bỏ phiếu, chúng ta cũng phải đề phòng Xu hướng vị trí - mô hình đánh giá sẽ ưu tiên một cách có hệ thống ứng cử viên xuất hiện ở một vị trí nhất định (thường là đầu tiên). Cho dù nội dung của hai ứng viên có hoàn toàn trái ngược nhau thì phán quyết cũng có thể không thay đổi. Phương pháp giảm thiểu tiêu chuẩn là trao đổi thứ tự và đánh giá từng trường hợp một lần: A được đánh giá một lần trước đó, B được đánh giá lại trước đó và lấy trung bình cộng của hai kết quả; một cách tiếp cận chặt chẽ hơn là chỉ tính khi hai phán đoán nhất quán và nếu chúng không nhất quán, nó sẽ được ghi là hòa hoặc gửi để xem xét thủ công. Chatbot Arena về cơ bản thực hiện điều tương tự—ngẫu nhiên hóa vị trí của hai phản hồi để các thành kiến về vị trí triệt tiêu lẫn nhau trên một cỡ mẫu lớn.

> **Thử nghiệm 7-8 ★★: Xây dựng thứ hạng mô hình từ dữ liệu so sánh theo cặp**
>
> Thử nghiệm này triển khai hệ thống tính toán xếp hạng Elo từ đầu để hiểu sâu hơn về cách mô hình Bradley-Terry trích xuất xếp hạng khả năng tương đối từ một số lượng lớn so sánh theo cặp. Sử dụng tập dữ liệu bỏ phiếu trong thế giới thực mã nguồn mở của Chatbot Arena gồm hàng triệu phiếu bầu của người dùng mù.
>
> Triển khai thuật toán cập nhật lặp lại xếp hạng Elo: ban đầu tất cả các mô hình được xếp hạng 1000 điểm và hồ sơ biểu quyết được xử lý theo thứ tự thời gian. Đối với mỗi trận đấu, tỷ lệ thắng dự kiến được tính dựa trên chênh lệch xếp hạng hiện tại giữa hai mô hình, kết quả thực tế được so sánh với dự kiến và được điều chỉnh theo tỷ lệ học tập cố định - người thắng cộng điểm, người thua trừ điểm và phạm vi điều chỉnh tỷ lệ thuận với độ lệch dự kiến (thất bại khó chịu sẽ dẫn đến thay đổi điểm lớn hơn). Sắp xếp theo thứ tự giảm dần theo điểm cuối cùng và tính ma trận tỷ lệ thắng theo cặp. So sánh với danh sách chính thức và xác minh rằng thứ hạng nói chung là nhất quán. Không cần phải nghiêm ngặt về việc căn chỉnh từng điểm: Chatbot Arena chính thức sử dụng khả năng phù hợp tối đa của Bradley-Terry (có thể giải quyết tất cả các trò chơi cùng một lúc, bất kể thứ tự bình chọn), trong khi những gì được triển khai ở đây là Elo với các cập nhật gia tăng trực tuyến (kết quả bị ảnh hưởng bởi hệ số K tốc độ học tập và thứ tự xử lý). Hai thuật toán phải nhất quán trong bảng xếp hạng tổng thể nhưng điểm số cụ thể sẽ không hoàn toàn giống nhau.
>
> Phần thứ hai của thử nghiệm tạo ra hoạt ảnh diễn biến tiến hóa xếp hạng lịch sử: chia dữ liệu bỏ phiếu theo thời gian (hàng tuần hoặc hàng tháng) và tính toán ảnh chụp nhanh điểm Elo cho từng thời điểm. Sử dụng D3.js để triển khai hoạt ảnh thi đấu biểu đồ thanh (chiều dài thanh ngang = điểm, vị trí dọc = thứ hạng, thay đổi mượt mà theo thời gian). Bằng cách quan sát thời điểm đột phá của công nghệ hoạt hình (điểm của một mô hình nào đó đột nhiên tăng lên), sự phát triển của ngữ cảnh cạnh tranh và vòng đời của mô hình.
>

## Lựa chọn mô hình dựa trên đánh giá

Lựa chọn mô hình không chỉ đơn giản là “chọn mô hình mạnh nhất” mà còn thực hiện sự cân bằng dựa trên đánh giá giữa nhiều chiều dựa trên các kịch bản ứng dụng.

### Các khía cạnh chính của việc lựa chọn

**Thông lượng** và **Độ trễ** là hai bộ chỉ báo dễ bị nhầm lẫn. Để gỡ rối chúng, bạn chỉ cần biết rằng suy luận mô hình lớn được chia thành hai giai đoạn. **Prefill** đọc ngữ cảnh hoàn chỉnh cùng một lúc và xác định **độ trễ của từ đầu tiên** tính từ khi người dùng nhấn Enter cho đến khi xuất hiện từ đầu tiên (được đo bằng **TTFT**, Thời gian đến mã thông báo đầu tiên trong ngành) - ngữ cảnh càng dài thì việc điền trước càng chậm và TTFT càng lớn. **Giải mã** sau đó tạo mã thông báo câu trả lời theo mã thông báo, xác định tốc độ tạo từ tiếp theo (mã thông báo/giây) và cũng xác định trực tiếp thời gian suy nghĩ: mô hình 50 tokens/s tạo ra 2000 mã thông báo suy nghĩ và chỉ suy nghĩ mất 40 giây.

Xung quanh hai giai đoạn này, các chỉ số thông lượng và độ trễ chính như sau:

- **Thông lượng đầu vào/thông lượng đầu ra**: tương ứng với tốc độ Prefill và Decode tương ứng.
- **TTFT**: Bằng thời gian xếp hàng cộng với thời gian Điền trước và là "tốc độ phản hồi" mà người dùng cảm nhận được.
- **Độ trễ suy nghĩ**: Số lượng mã thông báo suy nghĩ được tạo ra bởi các mô hình khác nhau có thể thay đổi tới nhiều lần và độ dài suy nghĩ không nhất thiết phải tương quan thuận với hiệu quả nhiệm vụ. Bạn thực sự nên đo lường mức độ sử dụng mã thông báo tư duy và lợi ích tương ứng của từng mô hình theo khối lượng công việc của riêng bạn, thay vì chỉ suy luận từ danh sách công khai.
- **độ trễ đuôi p95**: Độ trễ mà 95% yêu cầu sẽ không vượt quá. Nó phản ánh tốt hơn trải nghiệm người dùng thực so với mức trung bình - mức trung bình sẽ bị kéo xuống bởi một số lượng lớn yêu cầu nhanh, che đi độ trễ nghiêm trọng mà một số ít người dùng gặp phải.

**Chi phí**: Giá cho mã thông báo đầu vào/đầu ra/bộ đệm. Không nên đánh giá chi phí một cách riêng biệt - một mô hình giá rẻ với tỷ lệ thành công thấp trên thực tế có thể đắt hơn do phải thử lại thường xuyên. Cần phải tính toán chi phí trung bình và tỷ lệ chi phí/hiệu suất của từng nhiệm vụ.

**Hiệu suất**: Pass@1, Pass^k, Pass@k, Best@k Định nghĩa chính xác của bốn chỉ số được hiển thị trong "Hệ thống chỉ số đánh giá" được đề cập ở trên. Ở đây chúng ta chỉ nói về cách chọn trong ngữ cảnh lựa chọn - Pass@1 (tỷ lệ thành công trung bình duy nhất) được sử dụng phổ biến nhất trong các tình huống hàng ngày; Pass^k được ưu tiên trong các tình huống vận hành chính, tập trung vào tính ổn định “không bao giờ mắc lỗi”; Pass@k hoặc Best@k được ưu tiên trong các nhiệm vụ khám phá, xem xét giới hạn khả năng trên sau khi tạo đủ cơ hội; sử dụng cho các tác vụ mở Rubric Tính điểm đa chiều.

**Giới hạn tốc độ và độ tin cậy**: Giới hạn RPM (yêu cầu mỗi phút) / TPM (mã thông báo mỗi phút) sẽ ảnh hưởng đến tính đồng thời và một số API sẽ tự động điều chỉnh giới hạn trong thời gian cao điểm. Về độ bền, cần chú ý đến dữ liệu ngoài phân phối, đầu vào đối nghịch và độ ổn định khi vận hành lâu dài (liệu có vấn đề như sập chế độ, mất tập trung, v.v.).

**Đường cong ngân sách–năng lực**: Một điểm số đơn lẻ dưới ngân sách cố định không đủ để xác định Agent có thể đảm nhiệm nhiệm vụ dài hạn hay không. Ngoài tỷ lệ thành công, cần báo cáo hiệu năng thay đổi theo thời gian thực, số token, số lần gọi công cụ hoặc ngân sách tính toán. Đối chiếu người–máy trong RE-Bench cho thấy rõ điều này: với tổng ngân sách 2 giờ cho mỗi môi trường, Agent tốt nhất đạt điểm khoảng gấp 4 lần chuyên gia con người; nhưng con người hưởng lợi nhiều hơn khi tăng thời gian, nhỉnh hơn Agent tốt nhất ở mốc 8 giờ và đạt khoảng gấp đôi điểm số khi có tổng cộng 32 giờ qua nhiều lần thử[^re-bench-2025]. Vì vậy, ưu thế ở ngân sách ngắn không thể được ngoại suy trực tiếp thành năng lực vận hành dài; việc chọn mô hình phải so sánh nhiều mốc ngân sách gần với thời lượng nhiệm vụ thực tế.

Trong thực tế, chiến lược cộng tác đa mô hình có thể được áp dụng: sử dụng các mô hình gọn nhẹ để xử lý các yêu cầu đơn giản nhằm giảm chi phí và sử dụng các mô hình mạnh mẽ để xử lý các tác vụ phức tạp nhằm đảm bảo chất lượng; hoặc sử dụng các mô hình chuyên biệt để xử lý các nhiệm vụ con cụ thể (chẳng hạn như hiểu hình ảnh, tạo mã) và cộng tác thông qua cơ chế sub-Agent. Sự kết hợp không đồng nhất này cần được xác minh thông qua đánh giá để xác nhận xem lợi ích tổng thể có lớn hơn độ phức tạp ngày càng tăng của hệ thống hay không (chẳng hạn, coi những câu như "9,9 và 9,11 cái nào lớn hơn?" hay "tôi muốn rửa xe, tiệm rửa cách nhà 50 mét—nên đi bộ hay lái xe?" là câu hỏi đơn giản rồi giao cho mô hình nhẹ, dẫn tới quyết định sai).

### Hành vi mô hình: Khi nào ngừng đọc và bắt đầu chỉnh sửa

Việc chọn mô hình không chỉ so sánh liệu mô hình có hoàn thành được nhiệm vụ hay không, mà còn so sánh **hành vi mặc định của nó**. Một khác biệt dễ quan sát ở Coding Agent là ngưỡng hành động. Với cùng một nhiệm vụ lập trình, một số mô hình khám phá rộng kho mã và xác nhận kiến trúc, các điểm gọi và kiểm thử trước khi chỉnh sửa. Những mô hình khác định vị thay đổi từ ít bằng chứng hơn, chỉnh sửa sớm rồi dùng phản hồi kiểm thử để hoàn thiện hiểu biết. Nhóm đầu đánh giá chi phí của việc sửa quá sớm cao hơn; nhóm sau đánh giá chi phí cơ hội của việc đọc thêm một tệp cao hơn.

Xu hướng ấy của Agent có hai nguồn: một là prompt hệ thống trong Harness, hai là chính sách hành vi của mô hình. Hậu huấn luyện là nguồn then chốt của chính sách hành vi: các quỹ đạo SFT làm mẫu "đọc đến đâu rồi mới bắt tay vào", phần thưởng quá trình thưởng hoặc phạt một lối đi công cụ nào đó, còn phần thưởng kết quả lại củng cố trọn bộ chiến lược cuối cùng đã thành công. Lâu dần, thứ mô hình học được không chỉ là cách viết mã, mà còn là thói quen kỹ thuật.

> **Thí nghiệm 7-9 ★★: Đo ngưỡng hành động của mô hình trong một Coding Harness cố định**
>
> **Mục tiêu**: cô lập yếu tố mô hình, định lượng cách các mô hình Coding mặc định cân bằng giữa tiếp tục thu thập thông tin và bắt đầu chỉnh sửa, đồng thời đánh giá hiệu quả đường đi cùng chất lượng kết quả.
>
> **Phương pháp**: chạy `chapter6/model-action-threshold/experiment.py`. Theo mặc định, chương trình gọi GPT-5.6-sol và Claude Sonnet 5 qua cùng endpoint OpenRouter OpenAI-compatible, đồng thời giữ cố định system prompt, schema công cụ, kho mã nhiệm vụ, lệnh kiểm thử và giới hạn lượt. Prompt trung lập không quy định số tệp tối thiểu phải đọc hay yêu cầu chỉnh sửa nhanh. Lặp lại mỗi loại trong ba loại nhiệm vụ ít nhất ba lần và luân phiên thứ tự mô hình. Ghi số lời gọi công cụ, tệp đã đọc, lượt tìm kiếm và thời gian thực trước lần chỉnh sửa đầu tiên, cùng tỷ lệ chấp nhận bản vá đầu tiên được kiểm thử, số lần làm lại sau kiểm thử, thành công cuối, số tệp thay đổi và mức dùng Token.
>
> **Diễn giải nhân quả**: chiến dịch trung lập hỏi hành vi có thay đổi theo mô hình trong cùng một Harness hay không. Để đo Harness như yếu tố điều chỉnh, hãy chạy một chiến dịch riêng với `--policy explore-first`; không trộn hai policy trong cùng phép so sánh mô hình. Hành vi thay đổi khi đổi mô hình và vẫn giữ nguyên với cùng mô hình qua nhiều Harness là bằng chứng mạnh hơn cho hiệu ứng mô hình; chiều ngược lại ủng hộ hiệu ứng Harness mạnh hơn.
>
> **Tiêu chí nghiệm thu**: mọi unit test offline đều qua; trước tiên phải xác nhận mỗi fixture nhiệm vụ ở trạng thái ban đầu làm kiểm thử thất bại; kết quả chính thức chứa đủ các ô `mô hình × nhiệm vụ × lần lặp`, không có lỗi API, có kiểm thử cuối độc lập và quỹ đạo kiểm toán được; `manifest.json` xác minh hash của cấu hình, quan sát và bản tổng hợp. Thư mục dự án lưu một lần chạy thực tế hoàn chỉnh 18/18 ô. Người đọc nên chạy lại trên phiên bản mô hình và workload thực tế mà mình quan tâm, thay vì coi các số liệu của kho mã nhỏ này là bảng xếp hạng vĩnh viễn.

### Phân tích chi phí của hệ thống Agent

Phần trước liệt kê chi phí là một trong những khía cạnh chính của việc lựa chọn mô hình, nhưng chi phí trong kịch bản Agent phức tạp hơn nhiều so với việc định giá mã thông báo đơn giản—nhiều vòng lý luận, lệnh gọi công cụ và tích lũy ngữ cảnh sẽ khiến chi phí tăng phi tuyến tính. Phân tích chi phí một cách có hệ thống là một phần không thể thiếu trong hệ thống đánh giá và là điều kiện tiên quyết cần thiết để triển khai sản xuất.

**Các thành phần của chi phí.**

Chi phí của hệ thống Agent có thể được chia thành ba cấp độ:

**Chi phí suy luận mô hình** là phần đơn giản nhất và được xác định bởi mức tiêu thụ mã thông báo đầu vào và mã thông báo đầu ra. Tuy nhiên, có hai yếu tố khuếch đại thường bị bỏ qua trong kịch bản Agent. Một là **Hiệu ứng tích lũy ngữ cảnh**: Mỗi khi Agent gọi LLM, tất cả lịch sử hội thoại trước đó và kết quả trả về của công cụ sẽ được gửi cùng nhau (để mô hình có thể hiểu được ngữ cảnh). Nếu bạn không tận dụng tốt KV Cache (nghĩa là lưu vào bộ đệm ngữ cảnh đã xử lý để tránh tính toán lặp lại), chi phí sẽ tăng rất nhanh - 1000 mã thông báo được gửi ở vòng đầu tiên, 2000 mã thông báo được gửi ở vòng thứ hai và 3000 mã thông báo được gửi ở vòng thứ ba. Tổng số tiền là 1000+2000+3000=6000 thay vì 3×1000=3000, càng nhiều vòng thì khoảng cách càng lớn. Thứ hai là **Chi phí mã thông báo tư duy**: Các mô hình hỗ trợ tư duy sẽ tạo ra số lượng lớn mã thông báo tư duy. Mặc dù những mã thông báo này không được hiển thị cho người dùng nhưng chúng cũng được bao gồm trong chi phí.

**Chi phí cuộc gọi công cụ** bao gồm phí API bên ngoài (trả tiền cho mỗi lần xem của công cụ tìm kiếm, truy vấn cơ sở dữ liệu tiêu tốn tài nguyên máy tính), tài nguyên hộp cát để thực thi mã và chi phí gián tiếp dễ bị bỏ qua: phí mã thông báo được tạo sau khi công cụ trả về kết quả và đưa ngữ cảnh vào. Nội dung được tìm kiếm trên web trả về có thể chiếm mã thông báo 2000-5000 và sẽ được tính phí nhiều lần dưới dạng đầu vào trong mỗi vòng suy luận tiếp theo.

**Chi phí cơ sở hạ tầng** bao gồm chi phí vận hành như cơ sở dữ liệu vectơ (để truy xuất RAG), hàng đợi tin nhắn, cơ sở dữ liệu quan hệ, lưu trữ nhật ký và theo dõi (để có thể quan sát).

Để thấy chi phí thực sự phát sinh ở đâu, thí nghiệm đi kèm sử dụng một quy trình hoàn tiền cố định gồm tám lượt: tra cứu đơn hàng, vận chuyển, chính sách hoàn tiền và kho tri thức, sau đó kiểm tra rủi ro, hoàn tiền, thông báo cho khách và đóng vụ việc. Các lệnh gọi gpt-4o-mini thực được chạy với bốn tổ hợp của hai công tắc: tiền tố ổn định hoặc không ổn định, lịch sử đầy đủ hoặc đã nén. Nghiệp vụ ở bốn nhóm hoàn toàn giống nhau; chi phí trong Bảng 7-4 được tính từ lượng token và bảng giá lưu cùng lần chạy.

Bảng 7-4 Chi phí đo được của quy trình Agent tám lượt

| Cấu hình | Token đầu vào | Token được cache | Tổng chi phí | Tiết kiệm so với đường cơ sở |
|---|---:|---:|---:|---:|
| Không cache, không nén | 20,700 | 0 | $0.003776 | — |
| Chỉ dùng tiền tố ổn định | 20,386 | 13,568 | $0.002707 | 28.3% |
| Chỉ nén lịch sử | 16,177 | 0 | $0.003115 | 17.5% |
| Tiền tố ổn định + nén | 16,035 | 6,144 | $0.002643 | 30.0% |

Ở nhóm cơ sở, đầu vào tăng từ 1,113 token ở lượt đầu lên 3,668 token ở lượt cuối. Kết quả công cụ bị mang lặp lại vào các yêu cầu sau, chiếm tổng cộng 9,544 token đầu vào. Khi bật cả hai biện pháp, con số này giảm còn 5,248 và tổng chi phí giảm 30%.

Các mức tiết kiệm không cộng tuyến tính. Tiền tố ổn định riêng lẻ tiết kiệm 28.3%, nén lịch sử riêng lẻ tiết kiệm 17.5%, nhưng kết hợp chỉ tiết kiệm 30%, không phải 45.8%. Nén lịch sử đồng thời làm ngắn phần tiền tố có thể tái sử dụng cache. Vì vậy, **khi kết hợp nhiều cách tối ưu ngữ cảnh, phải đo trên toàn bộ quy trình; không được cộng các tỷ lệ tiết kiệm riêng lẻ.** Nếu đổi mô hình, bảng giá hoặc độ dài nhiệm vụ, con số 30% cũng sẽ đổi. Điều có thể tái sử dụng là thiết kế bốn nhóm đối chứng, không phải chính tỷ lệ đó.

**Policy tối ưu hóa chi phí.**

Ba đòn bẩy phía đầu vào nên được thử trước là **tái sử dụng KV Cache** (giữ tiền tố ổn định), **nén ngữ cảnh** (rút gọn trajectory cũ và kết quả công cụ dài) và **định tuyến mô hình theo tầng** (giao yêu cầu đơn giản cho mô hình nhẹ, suy luận khó cho mô hình mạnh). Chương 2 đã trình bày cách triển khai. Điểm quan trọng ở góc độ vận hành là mỗi biện pháp cần có công tắc riêng, để nhóm đo được cả tác động độc lập lẫn tương tác khi kết hợp. Ngoài ra còn hai cách gắn trực tiếp với đánh giá và vận hành.

**Xử lý hàng loạt không đồng bộ** Tích lũy các tác vụ không theo thời gian thực để xử lý hàng loạt và tận dụng chiết khấu giá hàng loạt của nhà cung cấp API; trong các tình huống tự triển khai, nó cũng có thể cải thiện việc sử dụng GPU trong thời kỳ khó khăn.

**Giám sát chi phí và kiểm soát ngân sách.**

Cần thiết lập hệ thống giám sát chi phí theo thời gian thực trong môi trường sản xuất: theo dõi mức tiêu thụ mã thông báo và chi phí API theo loại nhiệm vụ, mô hình, người dùng và các thứ nguyên khác. Đồng thời, đặt giới hạn chi phí cho từng nhiệm vụ - tự động chấm dứt khi Agent rơi vào vòng lặp hoặc khám phá quá sâu để ngăn một nhiệm vụ đơn lẻ phát sinh chi phí cao bất thường.

> **Thử nghiệm 7-10 ★: Phân tích chi phí toàn diện của các nhiệm vụ Agent**
>
> **Mục tiêu thử nghiệm**: Tái hiện phân tích chi phí của quy trình tám lượt ở trên, sau đó kiểm tra cùng các biện pháp tối ưu trên khối lượng công việc thực tế của bạn.
>
> **Giải pháp kỹ thuật**: Trước hết tái hiện nhiệm vụ cố định trong kho đi kèm, rồi chọn thêm một số nhiệm vụ đại diện của riêng bạn. Dùng LangSmith hoặc hệ thống theo dõi tự xây dựng để ghi token đầu vào/đầu ra và token suy nghĩ, số lần gọi công cụ và kích thước kết quả, cùng độ trễ đầu cuối của từng lệnh gọi LLM. Tính chi phí trung bình, p50/p95/p99 và cơ cấu chi phí theo loại nhiệm vụ.
>
> **Tiêu chí chấp nhận**: Tạo báo cáo chi tiết và xác định các nguồn chi phí chính. Chạy đủ bốn tổ hợp công tắc, đo từng biện pháp riêng và cả hai cùng lúc. Khi đổi mô hình, phải chạy lại thay vì dùng lại tỷ lệ tiết kiệm của trajectory đã lưu.
>
>

### Lặp lại liên tục theo định hướng đánh giá

Lựa chọn mô hình không phải là quyết định một lần mà là một quá trình liên tục đòi hỏi phải điều chỉnh linh hoạt khi mô hình phát triển. Khái niệm cốt lõi về việc “có một hệ thống đánh giá có thể nhanh chóng theo kịp sự phát triển của mô hình” đã được đề xuất ở đầu chương này. Một trường hợp chuyển đổi mô hình cụ thể được sử dụng dưới đây để minh họa cách hệ thống này hoạt động trong quá trình ra quyết định thực tế.

Giả sử rằng hệ thống Agent của bạn hiện được xây dựng trên Claude, hệ thống này hoạt động tốt trong việc gọi công cụ và điều phối phức tạp. Một ngày nọ, Gemini phát hành một mẫu mới và các điểm chuẩn công khai cho thấy nó vượt qua Claude ở nhiều chỉ số và được định giá thấp hơn. Câu hỏi bạn gặp phải tại thời điểm này không phải là "Gemini có tốt hơn Claude" mà là " **Gemini có tốt hơn Claude cho nhiệm vụ cụ thể của tôi không? Tốt hơn bao nhiêu? Chi phí chuyển đổi là bao nhiêu?**"

Các nhóm có hệ thống đánh giá được thiết lập tốt có thể đưa ra câu trả lời trong vài giờ: chạy mô hình mới trên bộ dữ liệu đánh giá của riêng họ và so sánh tỷ lệ thành công của nhiệm vụ, độ chính xác của lệnh gọi công cụ, độ trễ và chi phí. Bạn có thể thấy rằng mô hình mới thực sự tốt hơn và rẻ hơn đối với các tác vụ đơn giản, nhưng trong các tình huống cốt lõi liên quan đến việc điều phối công cụ nhiều vòng phức tạp, tỷ lệ thành công giảm 5%. Sau khi xác nhận rằng sự khác biệt này vượt quá băng thông nhiễu (xem "Đánh giá ý nghĩa thống kê của kết quả" bên dưới), quyết định của bạn trở thành chiến lược khác biệt hóa "chuyển sang mô hình mới cho các nhiệm vụ đơn giản để giảm chi phí và giữ lại mô hình ban đầu cho các nhiệm vụ phức tạp để đảm bảo chất lượng" thay vì mù quáng chuyển đổi toàn bộ. Kiểu ra quyết định dựa trên dữ liệu tinh tế này chỉ có thể thực hiện được nếu hệ thống đánh giá được xây dựng trước.

> **Thử nghiệm 7-11 ★★: Điểm chuẩn hiệu suất mô hình đa chiều**
>
> Tiến hành kiểm tra điểm chuẩn toàn diện trên LLM chính thống và các nhà cung cấp API khác nhau, đồng thời thiết lập cơ sở dữ liệu ra quyết định lựa chọn mô hình đa chiều.
>
> Chọn phạm vi thử nghiệm: các mô hình SOTA nguồn đóng như dòng GPT, dòng Claude, dòng Gemini, dòng Doubao và các mô hình nguồn mở như Qwen, Kimi, DeepSeek. Kiểm tra các nhà cung cấp API khác nhau cho cùng một kiểu máy (ví dụ: DeepSeek chính thức so với Siliconflow) và xác minh kết quả của nền tảng giám sát hiệu suất của bên thứ ba (ví dụ: Phân tích nhân tạo).
>
> Thiết kế khối lượng công việc kiểm tra được tiêu chuẩn hóa: kiểm tra thông lượng đầu vào sử dụng ngữ cảnh có độ dài cố định (mã thông báo 8K/32K/128K) và yêu cầu kiểm tra thông lượng đầu ra tạo ra phản hồi có độ dài cố định (mã thông báo 512/2048). Kiểm tra độ trễ bao gồm TTFT (thời gian tạo mã thông báo đầu tiên) và độ trễ từ đầu đến cuối, đồng thời thời lượng suy nghĩ và độ trễ suy nghĩ được đo riêng cho các mô hình hỗ trợ suy nghĩ. Ít nhất 100 yêu cầu cho mỗi cấu hình, tính toán độ lệch chuẩn/p50/p95/p99 - phương sai độ trễ cao có nghĩa là trải nghiệm người dùng không ổn định.
>
> Đánh giá tính khả dụng và độ ổn định của API: Thăm dò mỗi giờ trong một tuần và ghi lại tỷ lệ thành công, loại lỗi và thời gian lỗi. Tính toán tỷ lệ thất bại, MTTR (Thời gian trung bình để khôi phục) và thời gian khả dụng liên tục tối đa. Kiểm tra ngưỡng thực tế của giới hạn tốc độ - tìm điểm điều tiết bằng cách tăng dần độ đồng thời và ghi lại giới hạn trên RPM/TPM. Tính toán chi phí toàn diện: Thu thập thông tin về giá (đơn giá của mã thông báo đầu vào/đầu ra/bộ đệm), xem xét tác động của KV Cache và tính chi phí trung bình của các nhiệm vụ Agent nhiều vòng điển hình.
>
> **Thử nghiệm 7-12 ★★: Đánh giá lựa chọn toàn diện hệ thống bộ nhớ người dùng**
>
> **Điều kiện tiên quyết**: Bạn cần phải hoàn thành thử nghiệm RAG Truy xuất ngữ cảnh hoặc Thông minh hóa Chương 3.
>
> **Mục tiêu**: Tiến hành đánh giá lựa chọn liên kết đầy đủ để truy xuất bộ nhớ người dùng Agent và xem ba điểm lựa chọn của mô hình nhúng, trình sắp xếp lại và mô hình chính Agent cùng ảnh hưởng như thế nào đến chất lượng truy xuất, độ trễ và chi phí. Sử dụng lại `chapter3/contextual-retrieval-for-user-memory` hoặc `chapter3/agentic-rag-for-user-memory` và so sánh trên 60 trường hợp thử nghiệm.
>
> **Chấp nhận**: Quét ba điểm lựa chọn tương ứng - mô hình được nhúng (BGE-M3 / OpenAI / Beanbao, v.v., ghi lại độ chính xác, độ trễ, chi phí khi truy xuất top-5), trình xếp hạng lại (bao gồm đường cơ sở "không có trình xếp hạng lại" để định lượng giá trị cận biên của nó), mô hình chính (tỷ lệ thành công cụ thể và hiệu quả sử dụng công cụ trong cùng một cấu hình truy xuất). Điều quan trọng là đọc ra sự phối hợp giữa các thành phần: phần nhúng mạnh hơn có thể làm cho trình sắp xếp lại trở nên dư thừa và mô hình chính mạnh hơn có thể bù đắp cho việc thiếu khả năng truy xuất - lựa chọn là sự đánh đổi có hệ thống, không phải là lựa chọn từng cái một của mạnh nhất. Xem kho hỗ trợ để biết chi tiết cấu hình.
>

## Đánh giá ý nghĩa thống kê của kết quả

Tập đánh giá thì hữu hạn, đầu ra của mô hình lại ngẫu nhiên, nên chênh lệch điểm có thể chỉ là nhiễu lấy mẫu. Nếu đo được tỉ lệ thành công $p$ trên $n$ ca, sai số chuẩn có thể ước lượng thô như sau:

$$
\mathrm{SE}(p)\approx\sqrt{\frac{p(1-p)}{n}}
$$

Ví dụ với 100 ca và tỉ lệ thành công 70%, khoảng tin cậy 95% vào khoảng $70\%\pm9$ điểm phần trăm; "mô hình mới 73% so với mô hình cũ 70%" chưa đủ để biện minh cho việc chuyển đổi.

Khi so hai cấu hình trên cùng một mẻ tác vụ, hãy ưu tiên **phân tích ghép cặp**: ghi lại từng bài xem bên nào thắng, rồi dùng kiểm định McNemar hoặc bootstrap ghép cặp để phán đoán chênh lệch, chứ không lấy hai tỉ lệ thành công độc lập trừ thẳng cho nhau. Vì mỗi lần chạy Agent cũng có thể khác nhau, tốt nhất là chạy mỗi cấu hình với nhiều hạt giống ngẫu nhiên (chẳng hạn 3–5 lần) và báo cáo giá trị trung bình kèm biên độ dao động; một lần chạy chỉ dùng để sàng hướng. Nếu mức lợi kỳ vọng chỉ 2–3 điểm phần trăm mà tập đánh giá chỉ có vài chục bài, hãy mở rộng mẫu trước—sai số chuẩn co lại theo $1/\sqrt{n}$.

```python
for task in paired_tasks:
    for seed in fixed_seeds:
        a = run(config_a, task, seed)
        b = run(config_b, task, seed)
        record_paired_delta(verifier(a), verifier(b))

return paired_bootstrap_or_mcnemar(all_deltas)
```

Ghép cặp nghĩa là hai nhóm dùng chung tác vụ và điều kiện ngẫu nhiên, chứ không phải lấy riêng hai mẻ mẫu rồi so trung bình.

Khi kiểm chứng song song nhiều giả thuyết còn phải tính tới **so sánh bội**: siết ngưỡng ý nghĩa, hoặc chạy lại độc lập những kết quả dương tính. Tiêu chí thực dụng rất đơn giản: chênh lệch điểm phải vượt nhiễu, phải đứng vững trong phân tích ghép cặp, và phải tái lập được, thì mới đáng để đổi mô hình hay phát hành thay đổi.

## Observability của Agent

Các quyết định dựa trên đánh giá, dù là lựa chọn mô hình hay lặp lại liên tục, đều dựa vào dữ liệu vận hành chất lượng cao. Trước tiên, chúng tôi mô tả cách thu thập dữ liệu này một cách có hệ thống (observability được), sau đó thảo luận cách chuyển kết quả đánh giá thành cải tiến hệ thống.

![Hình 7-7 Ngăn xếp công nghệ quan sát ](images/fig7-7.svg)

Khái niệm Observability được mượn từ lĩnh vực hệ thống phân tán: bạn không thể trực tiếp mở hệ thống để xem nó đang làm gì. Bạn chỉ có thể suy ra điều gì đang xảy ra thông qua nhật ký, chỉ báo và dữ liệu theo dõi mà nó đưa ra. Cũng giống như bác sĩ không thể nhìn trực tiếp tình trạng cơ thể bệnh nhân mà chỉ có thể chẩn đoán vấn đề thông qua các tín hiệu bên ngoài như nhiệt độ cơ thể, huyết áp, hình ảnh. Hệ thống Agent khiến việc này trở nên khó khăn hơn: cùng một đầu vào có thể tạo ra các đầu ra khác nhau, nhiều vòng lý luận và lệnh gọi công cụ khiến đường dẫn thực thi trở nên cực kỳ phức tạp và quá trình "tư duy" của mô hình hoàn toàn không rõ ràng với thế giới bên ngoài.

Giá trị của observability trước tiên nằm ở **chẩn đoán vấn đề**: trajectory hoàn chỉnh cho phép các nhà phát triển phát lại toàn bộ quá trình thay vì dựa vào phỏng đoán. Thứ hai là cơ sở của **tối ưu hóa liên tục** - bạn có thể xem tác vụ nào yêu cầu lặp lại nhiều lần, công cụ nào có tỷ lệ thành công thấp nhất và truy vấn tìm kiếm nào luôn trả về kết quả trống. Trên **Quản lý chi phí**, chi phí vận hành Agent có thể thay đổi theo một hoặc hai bậc độ lớn đối với các nhiệm vụ khác nhau và việc theo dõi có thể xác định các trường hợp chi phí cao bất thường. Cuối cùng, dữ liệu trajectory tích lũy cũng cung cấp cơ sở cho việc tối ưu hóa hệ thống và cải tiến mô hình tiếp theo.

Cơ sở dữ liệu của observability Agent là **Trace** và cấu trúc dữ liệu của nó tuân theo mô hình cây span của hệ thống phân tán: một lần thực thi tác vụ tương ứng với một trajectory, trong đó mỗi lệnh gọi LLM, mỗi lệnh gọi công cụ và mỗi lần truy xuất là một **span**(đơn vị thực thi ghi lại đầu vào và đầu ra, thời gian bắt đầu và kết thúc, mức tiêu thụ mã thông báo và thông tin lỗi), span Mối quan hệ cha-con giữa chúng tạo thành một cây thực thi - cho ví dụ: trong khoảng "vòng lặp chính Agent", có một số khoảng phụ "cuộc gọi LLM" và "cuộc gọi công cụ". Các giao thức được tiêu chuẩn hóa có sẵn ở lớp này: **OpenTelemetry** là một tiêu chuẩn theo dõi phân tán chung và các thông số kỹ thuật như **OpenInference** xác định các quy ước ngữ nghĩa dành riêng cho ứng dụng LLM trên đó (cách ghi lại các từ nhắc nhở, tham số mô hình, cách sử dụng mã thông báo, v.v.). Ưu điểm của việc sử dụng các giao thức chuẩn là việc thu thập và phân tích được tách rời—cùng một dữ liệu theo dõi có thể được kết nối với các chương trình phụ trợ phân tích khác nhau để tránh bị khóa vào một nền tảng duy nhất.

LangSmith là một trong những nền tảng tiêu biểu trong lĩnh vực này (có vị trí tương tự như Langfuse, Arize Phoenix, v.v.), tích hợp observability, đánh giá và tối ưu hóa thành một vòng khép kín. Mỗi lần thực thi sẽ tạo ra một phiên theo dõi, trong đó các lệnh gọi mô hình, cách sử dụng công cụ và truy xuất kiến thức được ghi lại dưới dạng các đơn vị thực thi độc lập và cây thực thi được hình thành thông qua các liên kết nhân quả. Mỗi đơn vị ghi lại đầy đủ thông tin đầu vào và đầu ra, thông tin thời gian, dữ liệu chi phí và thông tin lỗi. Nền tảng sử dụng tính năng thu thập dữ liệu hàng loạt không đồng bộ để đảm bảo rằng bản thân việc theo dõi không ảnh hưởng đến độ trễ phản hồi của Agent.

Nền tảng này cũng hỗ trợ thử nghiệm A/B (định tuyến một phần lưu lượng truy cập của người dùng sang phiên bản mới, tự động so sánh các chỉ báo khác nhau và hỗ trợ khôi phục nhanh hoặc mở rộng dần dần), quản lý phiên bản từ nhanh chóng (mỗi phiên bản được liên kết với dữ liệu hiệu suất thời gian chạy) và phát triển cộng tác (các thành viên trong nhóm có thể chia sẻ dữ liệu theo dõi và các trường hợp sự cố). Dữ liệu thực khổng lồ trong môi trường sản xuất là mỏ vàng để cải tiến liên tục - nó có thể phát hiện ra các tình huống không mong muốn và xác định các điểm chức năng cần tối ưu hóa nhất.

Đích đến giá trị nhất của dữ liệu khả quan sát là **chảy ngược trở lại và biến thành tài sản đánh giá**. Một vòng khép kín thiết thực là: sàng từ quỹ đạo sản xuất ra những ca thất bại và đáng ngờ → xử lý ẩn danh (bỏ đi quyền riêng tư người dùng, khoá bí mật và các trường nhạy cảm khác) → lắng đọng thành ca mới và bài kiểm thử hồi quy cho tập đánh giá. Nhờ vậy tập đánh giá không còn là một tập tĩnh dựng lên một lần, mà là tài sản sống tiến hoá cùng sản phẩm và liên tục bám sát phân bố người dùng thực. Kiểu thất bại hôm nay lộ ra trên môi trường chạy thật, ngày mai chính là ca hồi quy giữ lấy lằn ranh ấy.

Với một hệ thống đánh giá hoàn chỉnh và bộ dữ liệu sẵn có, điều quan trọng là chuyển các kết quả đánh giá thành những cải tiến hệ thống thực tế.

## Từ báo cáo Điểm chuẩn đến cải tiến hệ thống

Trường hợp sau lấy từ một vòng lặp AndroidWorld có thật nhưng được thu hẹp có chủ đích trong kho đi kèm. Thử nghiệm gồm bốn nhiệm vụ cài đặt Wi-Fi trên trình giả lập API 35, mỗi nhiệm vụ có một cặp chạy đối chứng–thử nghiệm. Đây không phải toàn bộ benchmark 116 nhiệm vụ và cũng không thay thế việc chạy lại trong môi trường tham chiếu API 33. Giá trị của nó nằm ở chuỗi quyết định nối từ kết quả này sang kết quả kế tiếp, không phải ở một điểm số tổng quát.

![Hình 7-8 Điểm chuẩn cho vòng kín cải tiến ](images/fig7-8.svg)

Từ góc độ của kỹ thuật Harness, phần này chủ yếu nói về phương pháp tối ưu hóa lặp lại Harness - xác định các liên kết yếu trong Harness bằng cách đánh giá dữ liệu (không đủ ngữ cảnh? Thiếu các ràng buộc? Xác minh không đầy đủ? Phản hồi không kịp thời?), cải tiến có mục tiêu và sau đó đánh giá lại, tạo thành một vòng khép kín trong quá trình phát triển liên tục của Harness.

Trước khi bắt đầu phân tích báo cáo Điểm chuẩn, có một nguyên tắc dễ bị bỏ qua: **Khi thấy hiệu suất của Agent giảm sút, trước tiên bạn nên kiểm tra chính hệ thống đánh giá trước khi chạm vào Agent**. Một hiểu lầm phổ biến là sửa đổi ngay mã Agent khi điểm giảm xuống, đồng thời bỏ qua rằng bản thân hệ thống đánh giá có thể gặp sự cố trước tiên - hướng điều chỉnh dựa trên tín hiệu bị méo có thể sai ngay từ đầu. Các nguồn lỗi phổ biến trong hệ thống đánh giá bao gồm: không đủ tài nguyên trong môi trường đang chạy dẫn đến dừng quá trình (được hiển thị dưới dạng lỗi ngẫu nhiên), lỗi trong chính trình ghi điểm xác định câu trả lời đúng là lỗi và sự mất kết nối giữa các trường hợp thử nghiệm và kịch bản sản xuất. Những vấn đề này giống hệt về mặt số lượng với sự xuống cấp của mô hình và chỉ có thể được phân biệt bằng cách kiểm tra các trajectory hoàn chỉnh.

### Hiểu báo cáo điểm chuẩn: Nghệ thuật tìm ra vấn đề

Báo cáo ban đầu ghi lại kết quả chạy một lần cho mỗi trong 116 tác vụ, với tỉ lệ thành công tổng thể khoảng 88%. Nhưng các thất bại không rải rác lẻ tẻ: ba trong bốn tác vụ `SystemWifiTurn*` đều hỏng, và trong quỹ đạo còn lặp đi lặp lại hiện tượng điều hướng qua lại, không xác nhận được trạng thái cuối cùng. Ở đây có ít nhất hai cách giải thích: có thể Agent không biết lối vào phần cài đặt, mà cũng có thể thông tin giao diện nó nhận được là không đầy đủ.

Điểm tổng 88% dễ che khuất cụm lỗi nhỏ nhưng nhất quán này. Tăng giới hạn bước cũng không giải quyết đúng vấn đề: nó có thể biến “Agent không nhìn thấy điều khiển” thành “Agent chưa đủ kiên trì”. Cách đọc đúng là đi từ chi tiết lên: tìm cụm theo nhiệm vụ và nhãn năng lực, phát lại trajectory, xác định lỗi nằm ở quan sát, suy luận, hành động hay xác minh, rồi mới chọn một biến để thay đổi. Nhóm nhiệm vụ Wi-Fi ở đây được dùng để chẩn đoán cơ chế với chi phí thấp, không phải để ước lượng hiệu năng toàn hệ thống.

### Từ dữ liệu đến giả thuyết: Xây dựng lộ trình cải tiến

Vòng đầu kiểm tra lời giải thích rẻ nhất. H1 giả định Agent thiếu kiến thức điều hướng, nên chỉ nhóm thử nghiệm nhận thêm chỉ dẫn tìm trang Wi-Fi và kiểm tra trạng thái cuối. Tỷ lệ thành công không tăng; prompt không phải nút thắt.

Vòng hai kiểm tra Agent thực sự nhìn thấy gì. H5 thay nguồn accessibility không tương thích với API 35 bằng cây UIAutomator được AndroidWorld hỗ trợ. Thành công tăng mạnh, nhưng cây đầy đủ làm lượng token tăng vọt. Vì vậy H5C không thêm thông tin mới; nó chỉ loại các nút container vô hình, không có văn bản và không thể thao tác, nhằm xem có thể giữ nguyên thành công với ít nhiễu hơn hay không.

Trong cả ba vòng, mô hình, tham số nhiệm vụ, seed, giới hạn bước và trình giả lập đều được giữ nguyên; thứ tự hai nhánh được luân phiên. Nhờ chỉ thay một biến mỗi vòng, tác dụng phụ còn lại của vòng trước trở thành câu hỏi duy nhất cho vòng sau.

### Từ kết quả đến quyết định: Sự đánh đổi dựa trên dữ liệu

Bảng 7-5 tóm tắt số đo thực tế. Mỗi nhánh chỉ có bốn nhiệm vụ, nên các số này đủ để quyết định có đáng chạy rộng hơn hay không, chứ chưa thể đại diện cho toàn bộ AndroidWorld.

Bảng 7-5 Ba vòng thử nghiệm trên nhóm nhiệm vụ Wi-Fi của AndroidWorld

| Thử nghiệm | Biến duy nhất thay đổi | Thành công đối chứng → thử nghiệm | Token thử nghiệm / đối chứng | Quyết định kế tiếp |
|---|---|---:|---:|---|
| H1 | Thêm chỉ dẫn điều hướng | 25% → 25% | 0.47× | Không tăng thành công; giữ prompt cũ |
| H5 | Accessibility feed → UIAutomator | 25% → 100% | 2.498× | Hiệu quả rõ nhưng quá tốn; tiếp tục tối ưu |
| H5C | Rút gọn cây UIAutomator | 100% → 100% | 0.506× | Giữ thành công, giảm một nửa token; chuyển sang chạy đầy đủ |

Trình tự quan trọng hơn từng tỷ lệ riêng lẻ. Chỉ dẫn chi tiết hơn không thể bù cho thông tin mà Agent chưa từng nhận được; khi nghi ngờ lỗi quan sát, hãy kiểm tra nó trước khi kéo dài prompt. Tuy nhiên, nhiều đầu vào hơn cũng chưa chắc tốt hơn. Cây phần tử đầy đủ khắc phục vấn đề quan sát nhưng đưa quá nhiều nhiễu vào ngữ cảnh. Loại các nút không có ý nghĩa vẫn giữ bốn lượt chạy thành công và giảm lượng token khoảng một nửa. Không hề đổi mô hình: chính cách Harness biểu diễn UI trước hết quyết định nhiệm vụ có làm được hay không, rồi quyết định chi phí để làm được việc đó.

### Lặp lại liên tục: từ cải tiến đầu tiên đến phát triển hệ thống

H5C vượt qua bốn nhiệm vụ mới chỉ đủ điều kiện cho một phép thử lớn hơn, chưa đủ để triển khai. Cổng tiếp theo là chạy cả 116 nhiệm vụ với năm seed trên Pixel 6 / API 33 và đầy đủ ứng dụng bên thứ ba. Tỷ lệ thành công không được kém hơn, tỷ lệ token phải ≤ 0.75 và tỷ lệ độ trễ phải ≤ 1.5. Trước khi hoàn tất phép thử đó, kết quả 4/4 của nhóm nhỏ không được báo cáo thành “100% thành công toàn hệ thống”.

Đó là ý nghĩa thực tế của lặp liên tục: bằng chứng ở mỗi vòng chỉ cho phép hành động tiếp theo trong đúng phạm vi mà nó hỗ trợ. H1 chặn việc tiếp tục nhồi prompt; H5 tìm ra đúng cơ chế nhưng đồng thời lộ vấn đề chi phí; H5C xử lý chi phí và đủ điều kiện bước vào phép thử rộng. Một báo cáo benchmark tốt không chỉ nêu điểm số, mà còn nói rõ kết luận áp dụng ở đâu, guardrail nào chưa đạt và bước tiếp theo phải kiểm tra điều gì.

> **Thử nghiệm 7-13 ★★★: Đánh giá và cải tiến trên AndroidWorld**
>
> Thử nghiệm này thực hành trọn vẹn con đường từ báo cáo đánh giá đến cải tiến hệ thống. Bắt đầu bằng báo cáo lịch sử và ba cặp chạy đã lưu trong `chapter6/android-world`.
>
> Bước một: chẩn đoán. Phân tích chéo các bảng theo từng nhiệm vụ và ma trận nhãn khả năng để ánh xạ các lỗi bề ngoài của nhiệm vụ đến những thiếu sót về năng lực sâu bên trong. Xác định các nhãn năng lực có tỷ lệ thành công thấp hơn mong đợi và các lĩnh vực nhiệm vụ tập trung thất bại.
>
> Bước 2: Xây dựng giả thuyết. Hình thành giả thuyết theo ba lớp (bề mặt → trung gian → sâu); mỗi giả thuyết phải nêu mức cải thiện thành công kỳ vọng và cách xác minh.
>
> Bước 3: Thử nghiệm theo giai đoạn. Tái hiện H1, H5 và H5C, mỗi vòng chỉ đổi một biến. Ghi token, độ trễ và hồi quy bên cạnh tỷ lệ thành công.
>
> Bước 4: Ra quyết định dựa trên dữ liệu. Đưa ra quyết định triển khai dựa trên tỷ lệ chi phí-lợi ích—thay vì chỉ áp dụng tất cả các cải tiến có sẵn, bạn cần cân nhắc phạm vi, tác động về độ trễ và chi phí chung của mỗi cải tiến. Những cải tiến chi phí thấp và năng suất cao được triển khai trước tiên, còn những cải tiến chi phí cao được giới hạn trong các kịch bản chính.
>
> Bước 5: Lặp lại. Một thử nghiệm nhóm nhỏ đạt yêu cầu chỉ được chuyển sang chạy đầy đủ. Chỉ thảo luận triển khai sau phép thử 116×5 trong môi trường tham chiếu; trong báo cáo phải giữ rõ khác biệt môi trường, cỡ mẫu và phạm vi chưa hoàn chỉnh.
>

## Từ đánh giá bên ngoài đến đánh giá nội bộ: cơ sở hạ tầng đánh giá cho Agent cấp sản xuất

Các phần trước đã thảo luận về cách đánh giá hệ thống Agent từ bên ngoài—xây dựng môi trường đánh giá, thiết kế tập dữ liệu và phân tích báo cáo Điểm chuẩn. Nhưng các sản phẩm Agent tốt nhất không chỉ trải qua đánh giá bên ngoài mà còn có cơ sở hạ tầng tích hợp để tự đánh giá liên tục. Phần sau đây lấy OpenClaw Agent phổ biến nguồn mở được giới thiệu trong Chương 5 làm ví dụ, kết hợp với phân tích kỹ thuật công khai của sản phẩm Coding Agent hàng đầu để chia sẻ với những người thực hành, nhằm chứng minh một hệ thống đánh giá nội bộ đáng học hỏi - nó nhúng một cách có hệ thống phương pháp thử nghiệm trong nghiên cứu ML vào kỹ thuật sản phẩm.

### Cơ sở hạ tầng Ablation: Hiểu rõ sự đóng góp thực sự của từng tính năng

Các nhà nghiên cứu ML từ lâu đã sử dụng Nghiên cứu cắt bỏ để hiểu thành phần nào của mô hình thực sự quan trọng - cái gọi là cắt bỏ là "loại bỏ" từng thành phần nhất định để xem hiệu suất tổng thể giảm bao nhiêu. OpenClaw đưa phương pháp này vào kỹ thuật sản phẩm: một công tắc chính được tích hợp vào hệ thống để vô hiệu hóa nhiều tính năng chính (chế độ suy nghĩ, nén ngữ cảnh, bộ nhớ tự động, tác vụ nền, v.v.) cùng lúc, tạo ra đường cơ sở "mô hình trần". Điều này cho phép nhóm trả lời một câu hỏi quan trọng: **Tính năng này có thực sự cải thiện trải nghiệm người dùng hay chỉ cảm thấy hữu ích?**

Việc cắt bỏ thành một phương pháp thực hành kỹ thuật thông thường thay vì nghiên cứu một lần có một số ý nghĩa thực tế. Đầu tiên, các công tắc cắt bỏ phải được đưa vào từ rất sớm trong đường dẫn khởi động—trước khi bất kỳ hằng số cấp mô-đun nào nắm bắt các giá trị cấu hình—có nghĩa là cơ sở hạ tầng cắt bỏ phải được thiết kế vào kiến trúc hệ thống ngay từ đầu, thay vì được cài đặt sau đó. Thứ hai, việc chạy thử nghiệm cắt bỏ thường xuyên (chẳng hạn như trước mỗi bản phát hành chính) có thể phát hiện ra "nợ tính năng"—các tính năng đã từng hoạt động nhưng không còn cần thiết khi mô hình phát triển. Phương pháp được đề xuất cho bất kỳ nhóm nào xây dựng Agent sản xuất là: **Mọi tính năng chính phải có thể chuyển đổi độc lập và nhóm phải thường xuyên xác minh đóng góp thực tế của từng tính năng**.

### Phương pháp kiểm tra AB: Phân biệt giữa cơ chế và mục tiêu

Sản phẩm Agent trưởng thành sẽ tiến hành kiểm tra AB nghiêm ngặt về hành vi của chính nó (nghĩa là người dùng được chia ngẫu nhiên thành hai nhóm, một nhóm sử dụng phiên bản cũ và nhóm còn lại sử dụng phiên bản mới và dữ liệu thực tế của hai nhóm được so sánh để xác định xem các thay đổi có hiệu quả hay không). Trường hợp thử nghiệm Agent AB được thiết kế tốt thể hiện một số nguyên tắc phương pháp chính:

**Đa nhánh thay vì nhị phân**. Không chỉ so sánh "có" và "không", mà còn thiết kế nhiều biến thể lũy tiến (ví dụ: khi kiểm tra các điểm mạnh khác nhau của các ràng buộc từ gợi ý, hãy thiết lập một nhóm kiểm soát và ba nhóm thử nghiệm nghiêm ngặt hơn dần dần). Thiết kế này có thể tiết lộ mối quan hệ giữa liều lượng và phản ứng và giúp tìm ra điểm tối ưu.

**Phân biệt giữa chỉ báo cơ chế và chỉ báo mục tiêu**. Đây là sai lầm dễ mắc phải nhất - coi thứ bạn đang thay đổi là mục tiêu tối ưu hóa. Ví dụ: nếu bạn đang thử nghiệm "giảm độ dài tệp kế hoạch của Agent", thì độ dài kế hoạch là một chỉ số cơ chế (thứ mà bạn thay đổi trực tiếp), nhưng đó không phải là mục tiêu. Mục tiêu thực sự có thể là "giảm chi phí ở cấp độ phiên". Việc rút ngắn tài liệu kế hoạch có thể giảm chi phí nhưng cũng có thể dẫn đến nhiều chu kỳ chỉnh sửa-kiểm tra-chỉnh sửa hơn vì kế hoạch không đủ chi tiết, từ đó làm tăng sản lượng tổng thể. Hãy luôn tự hỏi bản thân: **Điều tôi đang thay đổi (cơ chế) có giống với điều tôi thực sự quan tâm (mục tiêu) không?** Nếu không, mục tiêu sẽ chiếm ưu thế.

**Đặt chỉ báo guardrails**. Ngay cả khi chỉ số mục tiêu được cải thiện, thử nghiệm vẫn nên dừng nếu mức độ hài lòng của người dùng giảm, số lượng thao tác tăng hoặc tỷ lệ lỗi tăng. Chỉ báo guardrails là “điểm mấu chốt không thể tệ hơn”.

**Ghi lại số liệu thống kê cơ bản**. Bao gồm kích thước mẫu, phân vị phân phối và phân tích tương quan (chẳng hạn như "tỷ lệ từ chối tăng đơn điệu với kích thước kế hoạch") để cung cấp ngữ cảnh cần thiết để diễn giải kết quả thử nghiệm. Nếu không có đường cơ sở, bạn không thể biết liệu kết quả thử nghiệm có ý nghĩa thống kê hay không.

### Hệ thống chuyển mạch đặc tính hai lớp

Các sản phẩm Agent cần thiết kế cơ sở hạ tầng chuyển đổi tính năng (Feature Flag) ngay từ ngày đầu tiên - cái gọi là chuyển đổi tính năng là một công tắc có thể được điều khiển từ xa để xác định xem một chức năng nào đó được bật hay tắt cho người dùng mà không cần phải triển khai lại mã. Nó phục vụ đồng thời ba mục đích: thử nghiệm, giải phóng dần dần và ngắt mạch khẩn cấp.

**Chuyển đổi thời gian biên dịch** loại bỏ mã có liên quan khỏi sản phẩm một cách vật lý trong giai đoạn xây dựng. Các tính năng dành riêng cho phần bên trong không tồn tại trong bản dựng bên ngoài - ngay cả kỹ thuật đảo ngược cũng không thể phát hiện ra chức năng đã bị loại bỏ. Đây cũng là một cơ chế cắt bỏ rõ ràng: việc tắt một tính năng không bỏ qua logic khi chạy, nhưng mã tương ứng không tồn tại về mặt vật lý.

Cấu hình của **chuyển đổi thời gian chạy** do máy chủ đưa ra và được lưu vào bộ nhớ đệm trên đĩa cục bộ. Thiết kế thà đọc cấu hình bộ đệm cũ hơn một chút hơn là cho phép Agent chặn khởi động do phải chờ yêu cầu mạng. Các quyết định phân nhóm cụ thể được thực hiện thông qua nền tảng thử nghiệm như GrowthBook, được sử dụng để phân bổ các nhóm thử nghiệm AB. Chi tiết thiết kế quan trọng là các sự kiện hiển thị cho từng tính năng được ghi lại nhiều nhất một lần mỗi phiên để tránh việc ghi lặp lại làm ô nhiễm dữ liệu thử nghiệm.

Nguồn cảm hứng cho các nhà phát triển Agent: Công tắc tính năng không phải là công cụ gỡ lỗi mà là các thành phần kiến trúc hạng nhất.

### Đánh giá độ nhạy của từ nhanh chóng

Lời nhắc hệ thống là "mã" cốt lõi cho hành vi của Agent, nhưng nó thường thiếu kiểm tra hồi quy và kiểm soát phiên bản giống như mã thông thường. Những gì OpenClaw làm là cung cấp một công cụ chuyên dụng có thể trích xuất lời nhắc hệ thống được hiển thị đầy đủ trên một phiên bản git được chỉ định - văn bản cuối cùng bao gồm tất cả các phần mở rộng điều kiện động. Điều này cho phép nhóm trả lời chính xác: **Cam kết nào đã thay đổi từ gợi ý? Tác động lên bộ đánh giá là gì?**

Các phương pháp được đề xuất cho bất kỳ nhóm Agent nào là: (1) Lời nhắc hệ thống phải được hiển thị một cách xác định (với cùng một đầu vào cấu hình, luôn tạo ra cùng một đầu ra); (2) Thiết lập cơ chế chụp nhanh theo phiên bản cho các lời nhắc; (3) Mọi thay đổi nhanh chóng phải chạy thử nghiệm hồi quy trên tập đánh giá - giống như các thay đổi mã cần chạy CI.

### Phân tích nhận thức về quyền riêng tư làm cơ sở để đánh giá

Đánh giá dựa trên dữ liệu tốt, nhưng các sản phẩm Agent thường xử lý nội dung nhạy cảm của người dùng. OpenClaw giải quyết mâu thuẫn này thông qua một hệ thống loại: giao diện phân tích chỉ chấp nhận các giá trị được bao bọc trong một loại đặc biệt và bản thân tên loại là một trajectory kiểm tra - nó có nghĩa đen là "Tôi đã xác minh rằng đây không phải là mã hoặc đường dẫn tệp". Thiết kế này biến các ràng buộc về quyền riêng tư từ các thông số kỹ thuật được ghi lại thành các kiểm tra loại được thực thi tại thời điểm biên dịch.

Nguyên tắc cốt lõi là: **Thiết kế các hạn chế về quyền riêng tư vào hệ thống ngay từ đầu, thay vì thêm chúng vào sau**. Nếu hệ thống phân tích của bạn không thể thu thập dữ liệu một cách an toàn thì bạn không thể đánh giá hiệu quả. Quyền riêng tư và đánh giá không bị đối lập - thiết kế chú trọng đến quyền riêng tư buộc bạn phải suy nghĩ cẩn thận về *những gì thực sự cần đo lường*, từ đó dẫn đến các số liệu đánh giá chính xác hơn.

### Từ ngoài vào trong: Sự chuyển dịch trong tư duy đánh giá

Thông điệp cốt lõi của phần này là: **Các phần trước đã hướng dẫn bạn cách đánh giá Agent từ bên ngoài, phần này cho biết cách các sản phẩm Agent tốt nhất tự đánh giá từ bên trong**. Đánh giá bên ngoài cho bạn biết "Agent tốt như thế nào" và cơ sở hạ tầng đánh giá nội bộ cho bạn biết "những thay đổi nào đã làm cho nó tốt hơn". Thử nghiệm cắt bỏ khám phá những tính năng thực sự quan trọng, thử nghiệm AB định lượng tác động của từng thay đổi, chuyển đổi tính năng cung cấp cơ sở hạ tầng cho thử nghiệm và khôi phục, đánh giá độ nhạy từ nhanh chóng kết hợp lời nhắc của hệ thống vào hệ thống CI và phân tích nhận thức về quyền riêng tư đảm bảo tuân thủ việc thu thập dữ liệu. Cùng với nhau, năm thành phần này tạo nên kỹ thuật sản phẩm dựa trên đánh giá—không phải thỉnh thoảng thực hiện đánh giá mà đưa đánh giá vào mọi quyết định về sản phẩm.

## Môi trường mô phỏng: cầu nối từ đánh giá đến hậu đào tạo

Điểm cuối cùng của việc đánh giá không phải là điểm số mà là sự tiến bộ. Chương này đã chỉ ra hai con đường để cải tiến: điều chỉnh Harness (từ báo cáo Điểm chuẩn đến cải tiến hệ thống) và đưa đánh giá vào Kỹ thuật Sản phẩm (cơ sở hạ tầng đánh giá nội bộ). Hình thức cải thiện mạnh mẽ nhất là đào tạo - khi mục tiêu mở rộng từ "đánh giá các khả năng hiện có" sang "trau dồi các khả năng mới", đặc biệt thông qua công nghệ post-training đã thảo luận ở Chương 8, môi trường đánh giá cần phát triển thành **môi trường mô phỏng**: một sân chơi ảo cho phép Agent luyện tập nhiều lần và tự động ghi điểm. Sự khác biệt cốt lõi giữa môi trường mô phỏng và đánh giá là tần suất tương tác cao hơn nhiều (hàng triệu so với hàng nghìn), nhu cầu ngẫu nhiên hóa (để ngăn chặn việc học vẹt các cấu hình cụ thể) và nhu cầu cung cấp phản hồi ngay lập tức. Từ góc độ các lĩnh vực ứng dụng, môi trường mô phỏng được chia thành hai loại: môi trường kỹ thuật số (nhiệm vụ xử lý thông tin) và môi trường thể hiện (nhận thức và vận hành thế giới vật lý).

Đây là cách nối hai đầu cầu. Tài sản tích lũy ở bên đánh giá có thể được chuyển đổi gần như liền mạch thành tín hiệu đào tạo: một tập hợp Rubric hoặc trình xác thực được xác định rõ ràng về cơ bản là chức năng khen thưởng của RLVR (Học tăng cường với Phần thưởng có thể xác minh) - tập lệnh phán xét trực tiếp là tập lệnh khen thưởng. Bài kiểm tra có đạt hay không và trạng thái có đạt tiêu chuẩn không chỉ là tiêu chí đánh giá mà còn là phần thưởng cho việc học tập củng cố. Nhưng việc đào tạo sẽ tạo ra những yêu cầu mới mà bạn không phải lo lắng trong giai đoạn đánh giá. Một là **ngữ nghĩa thiết lập lại đáng tin cậy**: quá trình đào tạo yêu cầu chạy hàng triệu tập (một tập là một vòng tương tác hoàn chỉnh từ trạng thái ban đầu đến khi kết thúc nhiệm vụ). Mỗi tập phải có khả năng đặt lại môi trường về trạng thái ban đầu nhất định và sạch sẽ, nếu không tín hiệu gradient sẽ bị ảnh hưởng bởi trạng thái dư của vòng trước. Thứ hai là thông lượng cao hơn nhiều so với đánh giá: hàng nghìn đánh giá là đủ để đưa ra kết luận, trong khi quá trình đào tạo yêu cầu cung cấp cho mô hình hàng triệu tương tác trong khoảng thời gian đồng hồ treo tường có thể chấp nhận được. Tính song song của môi trường và chi phí của một phiên bản duy nhất quyết định trực tiếp liệu việc đào tạo có khả thi hay không. Hai điểm này - trình xác thực chức năng khen thưởng, thiết lập lại và thông lượng theo định hướng đào tạo - sẽ được mở rộng trong Chương 8.

![Hình 7-9 Phổ độ trung thực mô phỏng ](images/fig7-9.svg)

**Về mặt môi trường kỹ thuật số**, khung AWorld đã xây dựng hộp cát máy chủ MCP có thể điều khiển cho nhiệm vụ GAIA, cung cấp 26 máy chủ MCP bao gồm 126 chức năng công cụ để tránh các lệnh cấm và tác dụng phụ không thể kiểm soát do truy cập trực tiếp vào API thực. Tất cả các lệnh gọi công cụ đều có thể phát lại và kiểm tra được. Kiến trúc phân tán của AWorld rút ngắn thời gian thực thi nối tiếp truyền thống từ 7695 giây xuống còn 525 giây (tăng tốc 14,6 lần). Thiết kế không trạng thái của môi trường làm cho mỗi phiên bản hoàn toàn độc lập và hỗ trợ tính song song hiệu quả.

Về mặt **môi trường hiện thân**, RoboTwin2 xây dựng nhiệm vụ vận hành hai cánh tay dựa trên công cụ vật lý và môi trường ngẫu nhiên hóa vị trí, hướng và hình thức của các đối tượng để cải thiện khả năng khái quát hóa. Observation Space bao gồm tầm nhìn của nhiều camera và trạng thái khớp, đồng thời đạt được khả năng kiểm soát theo thời gian thực thông qua **Action Chunking** - mô hình lên kế hoạch cho nhiều hành động liên tục cùng một lúc (xem Chương 6 để biết chi tiết). OSWorld Cho phép cài đặt lại thông qua ảnh chụp nhanh máy ảo, AndroidWorld tập trung vào tự động hóa ứng dụng di động. Bất kể môi trường kỹ thuật số hay môi trường được thể hiện, môi trường mô phỏng cũng yêu cầu môi trường thực thi biệt lập và cơ chế nhận dạng ảo (cách ly VM/container, tác nhân dân cư, xác thực Human-in-the-Loop, hệ thống tệp dùng chung) được thảo luận trong Chương 4, sẽ không được lặp lại ở đây.

> **Thử nghiệm 7-14 ★★: Định cấu hình Môi trường thông minh hiện thân với OpenVLA và RoboTwin2**
>
> Xây dựng môi trường mô phỏng hoạt động của robot. Đọc tài liệu `ch7/SimpleVLA-RL` và OpenVLA để hiểu kiến trúc của mô hình hành động-ngôn ngữ-tầm nhìn (tích hợp từ đầu đến cuối của bộ mã hóa hình ảnh + mô hình ngôn ngữ + bộ giải mã hành động, chiếu hình ảnh và văn bản vào một không gian ngữ nghĩa chung). Định cấu hình môi trường RoboTwin2 và hiểu không gian quan sát (trạng thái khớp ba chiều RGB + 14 chiều) và không gian hành động (vectơ điều khiển 14 chiều). Nghiên cứu cơ chế ngẫu nhiên hóa môi trường và logic ràng buộc không gian trong move_can_pot. Chạy đánh giá mô hình được đào tạo trước, ghi lại tỷ lệ thành công, thời gian hoàn thành và các chế độ thất bại, tập trung vào tác động của việc phân chia hành động.
>
>
> ![Hình 7-10 OpenVLA và RoboTwin2 thể hiện môi trường thông minh ](images/fig7-10.svg)
>
>

### Đánh đổi độ trung thực và ngẫu nhiên hóa tên miền

Môi trường có độ chính xác cao có thể được chuyển sang thế giới thực tốt hơn nhưng lại tốn kém về mặt tính toán. Một khía cạnh khác của độ chính xác là mức độ ngẫu nhiên hóa: ngẫu nhiên hóa vừa phải có thể cải thiện việc khái quát hóa, trong khi ngẫu nhiên hóa quá mức có thể khiến nhiệm vụ trở nên quá khó khăn. **Ngẫu nhiên hóa tên miền** là công nghệ then chốt giúp thu hẹp khoảng cách giữa mô phỏng và thực tế (khoảng cách sim-to-real): giới thiệu một loạt các thay đổi ngẫu nhiên về thông số vật lý, hình thức trực quan, nhiễu cảm biến, v.v. - giống như luyện tập cầm nắm dưới nhiều ánh sáng và góc độ khác nhau, bạn sẽ không bỏ lỡ do thay đổi ánh sáng trong môi trường thực. Trong môi trường kỹ thuật số, sim-to-real thể hiện ở sự khác biệt về kết xuất giao diện, thời gian phản hồi, v.v., có thể được giảm thiểu bằng cách đưa ra sự ngẫu nhiên về độ trễ và lỗi.

[^re-bench-2025]: Wijk, Hjalmar, et al. *RE-Bench: Evaluating Frontier AI R&D Capabilities of Language Model Agents against Human Experts.* arXiv:2411.15114, 2025.

## Tóm tắt chương này

Chương này xoay quanh một câu hỏi: làm sao biết Agent thực sự đã tốt hơn? Chuỗi này gồm bốn mắt xích: trước hết làm rõ thế nào là thành công (khác biệt giữa các căn cứ Pass@k, Best@k và Pass consecutive@k), rồi xác định nhiệm vụ đến từ đâu (ba nguồn: benchmark công khai, tập nghiệp vụ tự dựng và dòng chảy ngược từ trajectory sản xuất), tiếp đó chọn cách kiểm chứng (từ bộ kiểm chứng tất định tới danh mục kiểm tra, Rubric cùng phán xét của LLM, cho tới so sánh cặp), và cuối cùng chuyển điểm số thành quyết định (ý nghĩa thống kê, quy trách nhiệm thất bại, nhiệm vụ hồi quy và chọn mô hình). Mắt xích nào cũng ảnh hưởng đến độ tin cậy của kết luận. Các thí nghiệm đo được trong chương bổ sung bốn cảnh báo cụ thể: ghép bộ nhớ có cấu trúc với RAG không mặc nhiên tạo ra hiệp lực; mức tiết kiệm từ cache và nén không thể cộng thẳng; lựa chọn âm thanh tham chiếu làm thay đổi ý nghĩa của điểm đa phương thức; và cách Harness biểu diễn đầu vào có thể quyết định cả thành công lẫn chi phí token. Việc chọn mô hình còn phải so sánh đường cong năng lực theo ngân sách tài nguyên, không chỉ nhìn một điểm số. Với Agent cấp sản xuất, đánh giá không phải kỳ thi thỉnh thoảng mới tổ chức mà là cơ chế xác minh liên tục trong mọi quyết định sản phẩm.

Xét theo cấu trúc toàn sách, chương này dựng đoạn **chứng cứ** trong vòng lặp khám phá của Chương 1: quy trách nhiệm thất bại quyết định các đề xuất về sau có chỗ vững chắc để dựa vào hay không.

Đánh giá biên trên tiền tố quỹ đạo còn cho thấy thêm rằng **lấy được một mẩu thông tin và dùng nó đúng cách cho quyết định hiện tại là hai năng lực khác nhau**: hồi quy đầu-cuối bảo đảm các tác vụ cơ bản không suy giảm, còn tập biên theo trajectory prefix thì kiểm tra trực tiếp việc phán đoán phạm vi, việc chỉ dẫn hiện tại ghi đè, việc hỏi làm rõ và việc xác nhận trước hành động nguy hiểm. Bộ nhớ người dùng chỉ là một trường hợp của phương pháp tổng quát này. Đánh giá Agent cấp sản xuất không phải kỳ thi thi thoảng mới tổ chức, mà là một hệ thống kiểm chứng liên tục sinh ra tác vụ hồi quy và tác vụ biên từ những ca vấn đề thực.

Phương pháp cốt lõi: quan sát → giả thuyết → thử nghiệm → xác minh → hiểu biết mới → giả thuyết mới, khiến dự án Agent chuyển từ “giả kim thuật” dựa trên kinh nghiệm sang kỹ thuật khoa học dựa trên dữ liệu.

Hệ thống đánh giá được giới thiệu trong chương này tạo thành một vòng khép kín hoàn chỉnh: **Môi trường đánh giá** cung cấp cơ sở hạ tầng kiểm thử tự động → **Bộ dữ liệu đánh giá** xác định các trường hợp kiểm thử → **Phương pháp đánh giá tự động**(LLM-as-a-Judge và Rubric) cho điểm hiệu suất Agent → **Phân tích điểm chuẩn** cho thấy hướng cải tiến → **Cải tiến hệ thống** Khắc phục sự cố → Cập nhật môi trường đánh giá và bộ dữ liệu để bắt đầu một lần lặp mới.

Hệ thống đánh giá được thiết lập trong chương này không chỉ phục vụ việc tối ưu hóa hệ thống hiện tại mà còn cung cấp nền tảng chính cho mô hình post-training trong chương tiếp theo - môi trường đánh giá và tập dữ liệu là đầu vào quan trọng cho post-training và môi trường mô phỏng là nền tảng thực hành cho post-training. Chương tiếp theo sẽ chuyển từ đánh giá sang cải tiến ở cấp độ mô hình, đi sâu vào cách viết chiến lược tương tác vào tham số mô hình thông qua SFT và RL.

## Câu hỏi tư duy

1. ★★ LLM-as-a-Judge Sử dụng mô hình ngôn ngữ để đánh giá đầu ra của mô hình ngôn ngữ. Có điểm mù mang tính hệ thống nào trong quá trình “tự đánh giá” này không - ví dụ: mô hình có thể luôn cho điểm cao cho một phong cách trả lời nhất định, nhưng ưu tiên này không phù hợp với phán đoán của con người? Làm thế nào có thể phát hiện và sửa chữa sự thiên vị này?
2. ★★★ Thiết kế “chống rò rỉ” của bộ dữ liệu đánh giá là rất quan trọng. Tuy nhiên, trong hệ sinh thái nguồn mở, một khi dữ liệu điểm chuẩn được công khai, nó sẽ sớm được đưa vào dữ liệu huấn luyện. Liệu “trò chơi mèo vờn chuột” này có hồi kết? Thiết kế một phương pháp đánh giá về cơ bản có khả năng chống rò rỉ dữ liệu.
3. ★★ Thang đo Bốn tiêu chí của AI (dựa trên hướng dẫn của chuyên gia, phạm vi bao quát toàn diện, trọng số tầm quan trọng tiêu chuẩn, đánh giá khép kín) được thiết kế để loại bỏ tính chủ quan trong đánh giá. Nhưng một số khía cạnh nhiệm vụ (chẳng hạn như “liệu câu trả lời có hữu ích hay không” và “liệu giọng điệu có phù hợp”) về bản chất là chủ quan. Làm cách nào để thiết kế Rubric đáng tin cậy cho các kích thước chủ quan này?
4. ★★ τ-bench đánh giá Agent bằng cách mô phỏng hành vi của người dùng thực. Nhưng bản thân người dùng được mô phỏng cũng là LLM - nó có thể đánh giá thấp một cách có hệ thống các tình huống khó khăn nhất định (chẳng hạn như người dùng cảm xúc, thiếu chính xác). Làm cách nào để xác minh chất lượng của chính người dùng mô phỏng?
5. ★★ So sánh theo cặp (mô hình Bradley-Terry) giả định rằng các ưu tiên có tính bắc cầu (nếu A > B và B > C thì A > C). Nhưng sở thích của con người thường vi phạm tính bắc cầu. Trong trường hợp nào các tùy chọn không mang tính bắc cầu có thể xuất hiện trong đánh giá Agent? Điều này ảnh hưởng thế nào đến độ tin cậy của bảng xếp hạng?
6. ★★ Chương này phân biệt Pass@k như trần năng lực với Pass consecutive@k như thước đo độ tin cậy nghiệp vụ. Với một Agent chỉ đạt tỷ lệ thành công 60% trong một lần chạy, bạn sẽ kết hợp chi phí thất bại, chi phí thử lại và tác dụng phụ của tác vụ như thế nào để quyết định nên báo cáo chỉ số nào và lấy $k$ bằng bao nhiêu?
7. ★★ Chương này đề xuất phương pháp khoa học “quan sát→giả thuyết→thí nghiệm→xác minh”. Nhưng trên thực tế, không gian hành vi của Agent là rất lớn và việc xác minh một giả thuyết có thể yêu cầu hàng trăm lần đánh giá. Làm cách nào để tối đa hóa lượng thông tin được đánh giá trong phạm vi ngân sách tính toán hạn chế?
8. ★ Trong thử nghiệm AndroidWorld, cây phần tử đầy đủ nâng tỷ lệ thành công từ 25% lên 100% nhưng làm lượng token tăng lên 2.498× so với đối chứng; sau khi cắt gọn, tỷ lệ thành công vẫn là 100% còn lượng token giảm xuống 0.506×. Bạn sẽ thiết kế quy tắc cắt tỉa tự động như thế nào để loại các nút UI rỗng về ngữ nghĩa mà không làm mất thông tin cần cho khả năng truy cập, xác minh trạng thái hoặc thao tác về sau?
9. ★★ Mô phỏng người dùng của τ-bench áp dụng "tiết lộ thông tin lũy tiến"—không cung cấp tất cả thông tin cùng một lúc mà tiết lộ dần dần dựa trên các câu hỏi do Agent đặt ra. Thiết kế này ảnh hưởng thế nào đến kết quả đánh giá? Nếu chiến lược tiết lộ thông tin của người dùng mô phỏng khác biệt đáng kể so với chiến lược của người dùng thực, liệu kết luận đánh giá có còn đáng tin cậy không?
