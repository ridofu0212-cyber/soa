# F168 — Implementation Roadmap

> **Repository:** ridofu0212-cyber/soa  
> **Branch:** main  
> **Last repository inspection:** 2026-11-17  
> **Purpose:** Chuyển baseline thiết kế trong `F168_PROJECT_PLAN.md` thành các công việc triển khai có thứ tự và tiêu chí nghiệm thu.

## 1. Kết quả kiểm tra repository

Tại thời điểm kiểm tra, nhánh `main` chỉ có:

~~~text
docs/
└── F168_PROJECT_PLAN.md
~~~

Chưa có source code, cấu hình chạy, migrations, test hoặc workflow CI trong repository. Vì vậy:
- Chưa thể xác nhận công nghệ nào đã được nhóm triển khai.
- Chưa thể đánh giá chức năng nào đã hoàn thành.
- Không được xem các service/API trong tài liệu thiết kế là đã tồn tại.
- Tất cả hạng mục triển khai bên dưới bắt đầu ở trạng thái **NOT STARTED**.

## 2. Quy ước trạng thái và cách làm việc

Dùng các trạng thái:
- `NOT STARTED`: chưa bắt đầu.
- `IN PROGRESS`: đang thực hiện.
- `BLOCKED`: bị chặn bởi quyết định hoặc công việc khác.
- `DONE`: đã hoàn thành và có bằng chứng kiểm tra.

Một task chỉ chuyển sang DONE khi:
1. Code/configuration đã được commit.
2. Chạy được theo hướng dẫn trong README.
3. Có test phù hợp hoặc bằng chứng kiểm thử thủ công.
4. Các thay đổi liên quan được cập nhật trong tài liệu.

Không đánh dấu DONE chỉ vì đã tạo file hoặc viết endpoint nhưng chưa chạy thử.

## 3. Thứ tự triển khai tổng thể

~~~mermaid
flowchart TD
    A[Phase 0: Confirm requirements and stack] --> B[Phase 1: Repository foundation]
    B --> C[Phase 2: User Service and email OTP]
    C --> D[Phase 3: Loan Service and approval]
    D --> E[Phase 4: Payment Service]
    E --> F[Phase 5: Frontend integration]
    F --> G[Phase 6: Testing and hardening]
    G --> H[Phase 7: Documentation and demo]
~~~

## 4. Backlog chi tiết

### Phase 0 — Xác nhận yêu cầu và công nghệ

**Mục tiêu:** tránh dựng kiến trúc hoặc chọn stack sai so với source code/rubric của môn học.

| ID | Công việc | Đầu ra / tiêu chí nghiệm thu | Trạng thái |
|---|---|---|---|
| P0-01 | Lấy rubric/yêu cầu chính thức của giảng viên | Danh sách yêu cầu bắt buộc và tiêu chí chấm | NOT STARTED |
| P0-02 | Xác nhận các thành viên và phần việc | Bảng phân công, người phụ trách từng service | NOT STARTED |
| P0-03 | Chốt stack cho frontend/backend | Phiên bản runtime/framework được ghi rõ | NOT STARTED |
| P0-04 | Chốt cách chạy local và Docker | Quy trình chạy thống nhất cho cả nhóm | NOT STARTED |
| P0-05 | Chốt quy tắc xét duyệt, lãi suất, kỳ hạn, ngày đến hạn | Bộ business rules có ví dụ tính toán | NOT STARTED |
| P0-06 | Chốt xác thực giữa service | JWT/API key hoặc cơ chế nội bộ, có mô tả luồng | NOT STARTED |

**Điều kiện hoàn tất phase:** nhóm thống nhất stack và các quy tắc nghiệp vụ có ảnh hưởng trực tiếp đến database/API. Không tự ý bắt đầu code ba service với các giả định khác nhau.

### Phase 1 — Repository foundation

**Mục tiêu:** mọi thành viên có thể clone và chạy skeleton dự án theo cùng một cách.

| ID | Công việc | Đầu ra / tiêu chí nghiệm thu | Trạng thái |
|---|---|---|---|
| P1-01 | Tạo cấu trúc thư mục frontend, services, infra, docs | Cấu trúc thống nhất, không trộn code các service | NOT STARTED |
| P1-02 | Thêm README gốc | Hướng dẫn prerequisites, setup, run, test | NOT STARTED |
| P1-03 | Thêm file cấu hình môi trường mẫu | `.env.example`, không commit secrets | NOT STARTED |
| P1-04 | Thiết lập Docker Compose và PostgreSQL | Các container khởi động được, healthcheck hoạt động | NOT STARTED |
| P1-05 | Thiết lập Nginx API Gateway | Route thử nghiệm tới service mẫu thành công | NOT STARTED |
| P1-06 | Tạo skeleton cho từng backend service | Mỗi service có health endpoint và cấu hình riêng | NOT STARTED |
| P1-07 | Thiết lập logging và error response cơ bản | Log có service/context; không lộ secret/OTP | NOT STARTED |
| P1-08 | Thiết lập Git workflow | Quy tắc branch, commit, pull request được thống nhất | NOT STARTED |

**Điều kiện hoàn tất phase:** một thành viên mới clone repo, cấu hình theo README và chạy được toàn bộ skeleton.

### Phase 2 — User Service và email OTP

**Mục tiêu:** hoàn thiện tài khoản, xác thực email và phân quyền.

| ID | Công việc | Đầu ra / tiêu chí nghiệm thu | Trạng thái |
|---|---|---|---|
| P2-01 | Thiết kế User DB và migrations | users, user_profiles, otp_codes; schema được review | NOT STARTED |
| P2-02 | Đăng ký tài khoản | Validate dữ liệu, hash mật khẩu, xử lý email trùng | NOT STARTED |
| P2-03 | Gửi OTP xác thực email | OTP gửi tới email người dùng qua SMTP cấu hình | NOT STARTED |
| P2-04 | Xác thực OTP email | Đúng/sai/hết hạn/đã dùng được xử lý chính xác | NOT STARTED |
| P2-05 | Gửi lại OTP | Có giới hạn tần suất và vô hiệu hóa OTP cũ phù hợp | NOT STARTED |
| P2-06 | Đăng nhập và xác thực phiên | Token/session hoạt động; mật khẩu không lưu dạng rõ | NOT STARTED |
| P2-07 | API profile | Người dùng chỉ xem/sửa hồ sơ của chính mình | NOT STARTED |
| P2-08 | Role Customer/Admin | Endpoint admin bị chặn với Customer | NOT STARTED |
| P2-09 | Unit/integration tests | Bao phủ đăng ký, login, OTP, quyền truy cập | NOT STARTED |

**Điều kiện hoàn tất phase:** có thể đăng ký, nhận OTP thật qua email cấu hình, xác thực và đăng nhập; API được test bằng Postman hoặc automated tests.

### Phase 3 — Loan Service

**Mục tiêu:** quản lý sản phẩm vay, đơn đăng ký, xét duyệt tự động, khoản vay và lịch trả góp.

| ID | Công việc | Đầu ra / tiêu chí nghiệm thu | Trạng thái |
|---|---|---|---|
| P3-01 | Thiết kế Loan DB và migrations | loan_products, loan_applications, loans, installments | NOT STARTED |
| P3-02 | API danh sách/chi tiết gói vay | Chỉ trả các gói được phép hiển thị | NOT STARTED |
| P3-03 | Admin CRUD gói vay | Validate hạn mức, lãi suất, kỳ hạn, trạng thái | NOT STARTED |
| P3-04 | Tích hợp xác minh người dùng | Loan Service xác minh tài khoản/email qua User Service | NOT STARTED |
| P3-05 | Tạo đơn vay | Validate product, amount, term và quyền sở hữu | NOT STARTED |
| P3-06 | Implement approval rules | Mỗi rule có test đạt/không đạt và lý do từ chối | NOT STARTED |
| P3-07 | Tạo loan khi approved | Application, loan được ghi nhất quán trong Loan DB | NOT STARTED |
| P3-08 | Tính lịch trả góp | Có test công thức, lãi suất 0%, làm tròn và kỳ cuối | NOT STARTED |
| P3-09 | API khoản vay và installments | Người dùng chỉ xem khoản vay của mình | NOT STARTED |
| P3-10 | Admin monitoring APIs | Admin xem được đơn, khoản vay theo quyền | NOT STARTED |
| P3-11 | Unit/integration tests | Bao phủ rule, tính tiền, quyền và trạng thái | NOT STARTED |

**Điều kiện hoàn tất phase:** tạo đơn vay từ API, nhận kết quả xét duyệt; đơn được duyệt tạo khoản vay và lịch trả góp có số liệu kiểm chứng được.

### Phase 4 — Payment Service

**Mục tiêu:** mô phỏng thanh toán kỳ trả góp, có OTP và chống ghi nhận trùng.

| ID | Công việc | Đầu ra / tiêu chí nghiệm thu | Trạng thái |
|---|---|---|---|
| P4-01 | Thiết kế Payment DB và migrations | payment_otps, transactions, idempotency data | NOT STARTED |
| P4-02 | Yêu cầu OTP thanh toán | OTP gửi tới email đã xác thực, có thời hạn | NOT STARTED |
| P4-03 | Xác thực OTP thanh toán | OTP đúng/sai/hết hạn/dùng lại được xử lý | NOT STARTED |
| P4-04 | Tạo transaction PENDING | Lưu operation ID và idempotency key duy nhất | NOT STARTED |
| P4-05 | Tích hợp Loan Service | Gọi API validate/settle kỳ, không truy cập Loan DB | NOT STARTED |
| P4-06 | Cập nhật kết quả giao dịch | SUCCESS/FAILED phản ánh kết quả Loan Service | NOT STARTED |
| P4-07 | Retry an toàn khi timeout | Retry cùng operation ID không trừ tiền/đánh dấu kỳ lần hai | NOT STARTED |
| P4-08 | API lịch sử và chi tiết giao dịch | User chỉ xem giao dịch thuộc mình; Admin có quyền giám sát | NOT STARTED |
| P4-09 | Kiểm thử thanh toán lặp | Hai request cùng kỳ không thể ghi nhận hai lần | NOT STARTED |
| P4-10 | Kiểm thử hai kỳ cùng loan đồng thời | Dư nợ không âm, không mất cập nhật | NOT STARTED |

**Điều kiện hoàn tất phase:** một kỳ trả góp được thanh toán mô phỏng thành công; giao dịch và trạng thái kỳ nhất quán; retry và request đồng thời không gây thanh toán trùng.

### Phase 5 — Frontend integration

**Mục tiêu:** hoàn thiện giao diện Customer/Admin và kết nối API thật.

| ID | Công việc | Đầu ra / tiêu chí nghiệm thu | Trạng thái |
|---|---|---|---|
| P5-01 | Khởi tạo frontend và design system | Layout, màu sắc, typography, component cơ bản | NOT STARTED |
| P5-02 | Login/Register/Email OTP | Luồng giao diện kết nối User Service | NOT STARTED |
| P5-03 | Customer Dashboard | Hiển thị khoản vay, dư nợ, kỳ sắp đến hạn | NOT STARTED |
| P5-04 | Loan Products và Application | Xem gói, nhập đơn, hiển thị kết quả rule | NOT STARTED |
| P5-05 | My Loans và Installments | Hiển thị lịch trả góp từ Loan Service | NOT STARTED |
| P5-06 | Payment flow | Nhập OTP, gửi thanh toán, hiển thị kết quả | NOT STARTED |
| P5-07 | Transaction History | Hiển thị lịch sử từ Payment Service | NOT STARTED |
| P5-08 | Profile | Xem/cập nhật thông tin cá nhân | NOT STARTED |
| P5-09 | Admin Portal | Quản lý user, product và theo dõi nghiệp vụ | NOT STARTED |
| P5-10 | Loading/error/empty states | Các trạng thái lỗi, tải, dữ liệu trống dễ hiểu | NOT STARTED |
| P5-11 | Responsive và accessibility cơ bản | Các trang chính dùng được trên màn hình phổ biến | NOT STARTED |

**Điều kiện hoàn tất phase:** người dùng thực hiện được toàn bộ luồng vay và thanh toán trên UI, không cần sửa dữ liệu trực tiếp trong database.

### Phase 6 — Testing và hardening

| ID | Công việc | Đầu ra / tiêu chí nghiệm thu | Trạng thái |
|---|---|---|---|
| P6-01 | Test API contract | Request/response và HTTP status đúng tài liệu | NOT STARTED |
| P6-02 | Test phân quyền | Customer không gọi được API admin hoặc dữ liệu user khác | NOT STARTED |
| P6-03 | Test OTP security | Hết hạn, brute-force limit, replay, resend | NOT STARTED |
| P6-04 | Test loan calculation | So sánh kết quả với bộ test case tính tay | NOT STARTED |
| P6-05 | Test duplicate payment | Gửi nhiều request cùng idempotency key | NOT STARTED |
| P6-06 | Test concurrency | Hai request thanh toán đồng thời cùng kỳ và khác kỳ | NOT STARTED |
| P6-07 | Test service unavailable/timeout | Hành vi retry, trạng thái PENDING và recovery rõ ràng | NOT STARTED |
| P6-08 | Kiểm tra secrets và dữ liệu nhạy cảm | Không commit credentials; không log token/OTP/password | NOT STARTED |
| P6-09 | End-to-end test | Chạy trọn luồng Customer và Admin | NOT STARTED |
| P6-10 | Regression test | Sửa lỗi không làm hỏng chức năng đã có | NOT STARTED |

### Phase 7 — Tài liệu và demo

| ID | Công việc | Đầu ra / tiêu chí nghiệm thu | Trạng thái |
|---|---|---|---|
| P7-01 | Cập nhật architecture diagram | Khớp với implementation thực tế | NOT STARTED |
| P7-02 | Hoàn thiện ERD từng service | Có PK, field, constraint và ownership | NOT STARTED |
| P7-03 | Hoàn thiện OpenAPI/Swagger | Endpoint, schema, auth, error được mô tả | NOT STARTED |
| P7-04 | Viết hướng dẫn cài đặt/chạy | Thành viên khác chạy lại được | NOT STARTED |
| P7-05 | Viết test report | Test case, expected/actual, pass/fail, evidence | NOT STARTED |
| P7-06 | Chuẩn bị demo script | Kịch bản ngắn, có dữ liệu demo và luồng lỗi | NOT STARTED |
| P7-07 | Chuẩn bị báo cáo thuyết trình | Nêu rõ SOA, service boundary, API, data ownership, consistency | NOT STARTED |

## 5. Các kịch bản nghiệm thu end-to-end bắt buộc

### E2E-01 — Đăng ký và xác thực
1. Customer đăng ký bằng email mới.
2. Hệ thống gửi OTP đến email đó.
3. Customer xác thực OTP hợp lệ.
4. Thử OTP hết hạn/đã dùng và xác nhận bị từ chối.
5. Customer đăng nhập thành công.

**Kết quả mong đợi:** email được đánh dấu verified; OTP không thể tái sử dụng; mật khẩu không lưu dạng rõ.

### E2E-02 — Đăng ký vay bị từ chối
1. Customer đăng nhập.
2. Chọn gói vay.
3. Nhập số tiền hoặc kỳ hạn không hợp lệ.
4. Gửi đơn.

**Kết quả mong đợi:** đơn bị từ chối với lý do/mã lỗi rõ; không tạo loan hoặc installments.

### E2E-03 — Đăng ký vay được duyệt
1. Customer gửi đơn thỏa tất cả rule.
2. Loan Service xác minh tài khoản.
3. Rule engine chạy.
4. Hệ thống tạo loan và installments.

**Kết quả mong đợi:** trạng thái APPROVED; dữ liệu loan và lịch trả góp đầy đủ, số tiền kiểm chứng được.

### E2E-04 — Thanh toán kỳ
1. Customer chọn kỳ UNPAID.
2. Yêu cầu OTP và nhận email.
3. Xác thực OTP.
4. Gửi payment request.
5. Xem trạng thái kỳ và lịch sử giao dịch.

**Kết quả mong đợi:** một transaction SUCCESS; kỳ chuyển PAID; dư nợ cập nhật đúng.

### E2E-05 — Chống thanh toán trùng
1. Gửi hai request đồng thời cho cùng một installment.
2. Thử retry request sau khi client timeout.

**Kết quả mong đợi:** chỉ có một lần settle hiệu lực; retry cùng operation ID trả lại kết quả cũ; không trừ dư nợ hai lần.

### E2E-06 — Phân quyền
1. Customer gọi endpoint admin.
2. Customer thử truy cập loan/transaction của user khác.

**Kết quả mong đợi:** backend trả 403/404 phù hợp; không lộ dữ liệu.

## 6. Thứ tự ưu tiên nếu thời gian có hạn

1. **Bắt buộc:** Phase 0, Phase 1, đăng ký/OTP/login, gói vay, tạo đơn, auto approval, loan/installments, payment mô phỏng, kiểm thử duplicate payment.
2. **Quan trọng:** phân quyền đầy đủ, transaction history, admin quản lý sản phẩm, Docker Compose, API documentation.
3. **Có thể giản lược:** dashboard thống kê nâng cao, animation UI, báo cáo phức tạp, refresh-token rotation nâng cao.

Không giản lược các kiểm tra quyền sở hữu dữ liệu, hash mật khẩu, OTP expiry/one-time-use và chống thanh toán trùng.

## 7. Quy tắc cập nhật roadmap

- Mỗi task cần có người phụ trách và liên kết PR/commit khi bắt đầu triển khai.
- Chỉ đổi trạng thái sau khi có bằng chứng kiểm tra.
- Nếu phát sinh thay đổi phạm vi, cập nhật `F168_PROJECT_PLAN.md` trước rồi mới sửa roadmap.
- Khi code thực tế khác tài liệu, ưu tiên kiểm chứng implementation và cập nhật tài liệu; không sửa code chỉ để khớp sơ đồ nếu chưa đánh giá tác động.
- Sau mỗi phase, cập nhật README và ghi lại cách kiểm thử.

## 8. Snapshot ban đầu

| Hạng mục | Trạng thái tại lần kiểm tra |
|---|---|
| Baseline project plan | Có: `docs/F168_PROJECT_PLAN.md` |
| Application source code | Chưa có trong repo |
| Backend services | Chưa có trong repo |
| Frontend | Chưa có trong repo |
| Database migrations/schema | Chưa có trong repo |
| Docker/Nginx configuration | Chưa có trong repo |
| Automated tests | Chưa có trong repo |
| API documentation | Chưa có trong repo |

> Roadmap này phản ánh repository tại commit kiểm tra ban đầu. Khi nhóm push code mới, cần kiểm tra lại cây thư mục và cập nhật trạng thái theo bằng chứng thực tế.
