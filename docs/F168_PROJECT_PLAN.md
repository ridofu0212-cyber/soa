# F168 — Đặc tả phạm vi và thiết kế kiến trúc

> **Đề tài:** Loan Installment  
> **Tên ứng dụng:** F168  
> **Trạng thái:** Baseline thiết kế; cần đối chiếu rubric chính thức và source code trước khi triển khai.

## 1. Định hướng sản phẩm

F168 là ứng dụng mô phỏng quy trình đăng ký vay và thanh toán khoản vay theo kỳ. Phục vụ mục đích học tập; không giải ngân tiền thật, không kết nối ngân hàng và không xử lý tiền thật.

| Hạng mục | Quyết định |
|---|---|
| Giao diện | Fintech/Banking hiện đại, tối giản, rõ ràng |
| Xét duyệt | Tự động theo quy tắc nghiệp vụ |
| Thanh toán | Mô phỏng trong hệ thống |
| AI | Không sử dụng |
| Kiến trúc | Microservices |
| Giao tiếp | REST API |
| Database | PostgreSQL, tách theo service |
| Gateway | Nginx |

Nguyên tắc: ưu tiên nghiệp vụ cốt lõi; service có trách nhiệm và quyền sở hữu dữ liệu rõ ràng; không truy cập database của service khác; API có validation, error handling và tài liệu.

## 2. Phạm vi chức năng

### Customer Portal
1. Đăng ký, đăng nhập, đăng xuất.
2. Xác thực email bằng OTP.
3. Xem/cập nhật thông tin cá nhân cơ bản.
4. Xem danh sách và chi tiết gói vay.
5. Gửi yêu cầu vay và xem kết quả xét duyệt.
6. Xem khoản vay và lịch trả góp.
7. Yêu cầu OTP xác nhận thanh toán.
8. Thanh toán kỳ vay bằng giao dịch mô phỏng.
9. Xem lịch sử giao dịch.

### Admin Portal
1. Quản lý người dùng và trạng thái tài khoản.
2. Tạo, cập nhật, kích hoạt/ngừng kích hoạt gói vay.
3. Theo dõi đơn vay và kết quả xét duyệt tự động.
4. Theo dõi khoản vay, kỳ thanh toán và giao dịch.

Admin không duyệt thủ công trong luồng mặc định vì phương án đã chọn là xét duyệt tự động.

### Ngoài phạm vi phiên bản đầu
- AI chấm điểm tín dụng hoặc chatbot.
- Kết nối ngân hàng, ví điện tử hoặc cổng thanh toán thật.
- Giải ngân/thu tiền thật.
- Kết nối CIC hoặc dịch vụ tín dụng bên ngoài.
- Báo cáo tài chính và quản trị nợ nâng cao.

## 3. Quy tắc nghiệp vụ

### 3.1 Gói vay
Mỗi gói có tên, hạn mức tối thiểu/tối đa, lãi suất năm, kỳ hạn được phép và trạng thái hoạt động.
- Chỉ gói đang hoạt động được hiển thị để đăng ký.
- Số tiền phải nằm trong hạn mức; kỳ hạn phải được gói hỗ trợ.
- Người dùng không được tự sửa lãi suất.

### 3.2 Xét duyệt tự động
Phiên bản đầu dùng rule-based approval, không dùng AI. Điều kiện minh họa:
- Tài khoản đang hoạt động và email đã xác thực.
- Số tiền nằm trong hạn mức gói.
- Kỳ hạn được gói hỗ trợ.
- Người dùng không vượt quá giới hạn khoản vay đang hoạt động do hệ thống quy định.

Đạt tất cả điều kiện thì đơn được duyệt; nếu không, từ chối kèm mã/lý do. Ngưỡng cần được cấu hình, ghi tài liệu và kiểm thử; đây là quy tắc mô phỏng, không phải đánh giá tín dụng thực tế.

Trạng thái đơn: PENDING, APPROVED, REJECTED. Nếu xét duyệt đồng bộ ngay khi tạo đơn, PENDING chỉ tồn tại trong thời gian xử lý; không mô tả như hàng đợi duyệt thủ công.

### 3.3 Tạo khoản vay và lịch trả góp
Khi đơn được duyệt, Loan Service tạo khoản vay và lịch trả góp trong cùng transaction cục bộ.

Khoản vay gồm: Loan ID, Application ID, User ID, tiền gốc, lãi suất, kỳ hạn, ngày bắt đầu, dư nợ, trạng thái.

Kỳ trả góp gồm: Installment ID, Loan ID, số thứ tự kỳ, ngày đến hạn, gốc, lãi, tổng phải trả, trạng thái UNPAID/PAID/OVERDUE.

Công thức trả góp đều (annuity):

\[
A=P\times\frac{r(1+r)^n}{(1+r)^n-1}
\]

P là tiền gốc, r là lãi suất tháng, n là số kỳ. Nếu r = 0 thì A = P/n. Cần thống nhất cách làm tròn và điều chỉnh kỳ cuối.

### 3.4 Thanh toán mô phỏng
- Chỉ kỳ hợp lệ, chưa thanh toán mới được thanh toán.
- OTP gửi đến email đã xác thực; có hạn dùng, chỉ dùng một lần và giới hạn số lần thử.
- Không trả OTP trong API response hoặc ghi vào log.
- Mỗi yêu cầu thanh toán có idempotency key.
- Một kỳ không được ghi nhận thành công nhiều lần.
- Giao dịch có trạng thái PENDING, SUCCESS, FAILED.

## 4. Kiến trúc tổng thể

~~~mermaid
flowchart TB
    FE[F168 Frontend<br/>Customer + Admin Portal]
    GW[Nginx API Gateway]
    US[User Service]
    LS[Loan Service]
    PS[Payment Service]
    UDB[(User PostgreSQL)]
    LDB[(Loan PostgreSQL)]
    PDB[(Payment PostgreSQL)]
    SMTP[SMTP Email]

    FE --> GW
    GW --> US
    GW --> LS
    GW --> PS
    US --> UDB
    LS --> LDB
    PS --> PDB
    US --> SMTP
    LS -. REST: verify user .-> US
    PS -. REST: get verified email .-> US
    PS -. REST: validate and settle installment .-> LS
~~~

### User Service
Trách nhiệm: đăng ký, đăng nhập, xác thực, hồ sơ, role và gửi OTP email. Database riêng gồm:
- users: email, password hash, role, trạng thái, email verified.
- user_profiles: thông tin hồ sơ.
- otp_codes: OTP đã hash, mục đích, hạn dùng, số lần thử, trạng thái.
- refresh_tokens: nếu triển khai refresh-token session.

### Loan Service
Trách nhiệm: gói vay, đơn đăng ký, rule xét duyệt, khoản vay, lịch trả góp. Database riêng gồm:
- loan_products
- loan_applications
- loans
- installments

Loan Service là nguồn dữ liệu chuẩn cho trạng thái khoản vay, kỳ trả góp và dư nợ.

### Payment Service
Trách nhiệm: OTP xác nhận thanh toán, tiếp nhận yêu cầu, quản lý giao dịch và idempotency. Database riêng gồm:
- payment_otps
- transactions
- payment_attempts (nếu cần audit/debug).

Payment Service là nguồn dữ liệu chuẩn cho lịch sử giao dịch; Loan Service là nguồn dữ liệu chuẩn cho trạng thái kỳ thanh toán.

### Nguyên tắc dữ liệu
- Mỗi service chỉ đọc/ghi database do mình sở hữu.
- Không tạo foreign key vật lý xuyên database.
- ID từ service khác được lưu như external reference.
- Không chia sẻ ORM model hoặc truy cập bảng trực tiếp.
- Tương tác liên service qua REST API có xác thực phù hợp.

## 5. Công nghệ đề xuất

| Thành phần | Công nghệ |
|---|---|
| Frontend | React + TypeScript |
| UI | Tailwind CSS |
| User Service | Django REST Framework |
| Loan Service | Django REST Framework |
| Payment Service | FastAPI |
| Database | PostgreSQL |
| API Gateway | Nginx |
| Email | SMTP |
| API testing | Postman |
| Automated testing | Pytest |
| Container | Docker Compose |
| Version control | Git + GitHub |

Đây là stack mục tiêu. Trước khi thay đổi code hiện tại, cần kiểm tra repository và giữ lại công nghệ đã triển khai tốt nếu phù hợp.

## 6. API dự kiến

Các route dưới đây là API contract dự kiến, chưa khẳng định đã tồn tại trong source code.

### User Service — /api/users

| Method | Endpoint | Mục đích |
|---|---|---|
| POST | /register | Đăng ký |
| POST | /login | Đăng nhập |
| POST | /verify-email | Xác thực OTP |
| POST | /resend-otp | Gửi lại OTP |
| GET | /me | Xem profile |
| PUT | /me | Cập nhật profile |

### Loan Service — /api/loans

| Method | Endpoint | Mục đích |
|---|---|---|
| GET | /products | Danh sách gói vay |
| GET | /products/{id} | Chi tiết gói vay |
| POST | /applications | Tạo đơn và chạy rule xét duyệt |
| GET | /applications | Đơn vay của người dùng |
| GET | /applications/{id} | Chi tiết đơn |
| GET | /my-loans | Khoản vay của người dùng |
| GET | /{id}/installments | Lịch trả góp |
| GET | /installments/{id} | Chi tiết kỳ |
| POST | /admin/products | Tạo gói vay |
| PUT | /admin/products/{id} | Cập nhật gói vay |
| GET | /admin/applications | Theo dõi đơn vay |
| GET | /admin/loans | Theo dõi khoản vay |

### Payment Service — /api/payments

| Method | Endpoint | Mục đích |
|---|---|---|
| POST | /otp/request | Yêu cầu OTP |
| POST | /otp/verify | Xác thực OTP |
| POST | /transactions | Tạo và xử lý giao dịch |
| GET | /transactions | Lịch sử giao dịch |
| GET | /transactions/{id} | Chi tiết giao dịch |

Mỗi request thanh toán cần header Idempotency-Key. Backend phải xác thực quyền sở hữu khoản vay/kỳ; không tin user ID do frontend tự gửi.

### Response convention

Thành công:

~~~json
{
  "success": true,
  "message": "Request successful",
  "data": {
    "application_id": "APP-001",
    "status": "APPROVED"
  }
}
~~~

Thất bại:

~~~json
{
  "success": false,
  "message": "Loan amount exceeds product limit",
  "error_code": "INVALID_LOAN_AMOUNT"
}
~~~

Dùng HTTP status phù hợp: 200, 201, 400, 401, 403, 404, 409, 422, 500.

## 7. Luồng nghiệp vụ liên service

### 7.1 Đăng ký vay và xét duyệt

~~~mermaid
sequenceDiagram
    actor Customer
    participant FE as Frontend
    participant Loan as Loan Service
    participant User as User Service
    participant DB as Loan DB
    Customer->>FE: Chọn gói và nhập yêu cầu
    FE->>Loan: POST /applications
    Loan->>User: Xác minh tài khoản/email
    User-->>Loan: Trạng thái xác minh
    Loan->>DB: Kiểm tra gói và điều kiện
    Loan->>DB: Tạo application
    Loan->>Loan: Chạy rule xét duyệt
    alt Đạt điều kiện
        Loan->>DB: APPROVED + tạo loan + installments
        Loan-->>FE: Kết quả APPROVED
    else Không đạt
        Loan->>DB: REJECTED + lý do
        Loan-->>FE: Kết quả REJECTED
    end
    FE-->>Customer: Hiển thị kết quả
~~~

Tạo application, loan và installments phải nằm trong một transaction của Loan DB. Frontend không tự quyết định kết quả xét duyệt.

### 7.2 Thanh toán kỳ trả góp

~~~mermaid
sequenceDiagram
    actor Customer
    participant FE as Frontend
    participant Payment as Payment Service
    participant User as User Service
    participant Loan as Loan Service
    participant PDB as Payment DB
    Customer->>FE: Yêu cầu thanh toán
    FE->>Payment: POST /otp/request
    Payment->>User: Lấy email đã xác thực
    User-->>Payment: Email
    Payment->>Payment: Tạo OTP và gửi email
    Customer->>FE: Nhập OTP
    FE->>Payment: POST /otp/verify
    Payment-->>FE: OTP hợp lệ / phiên xác nhận
    FE->>Payment: POST /transactions + Idempotency-Key
    Payment->>PDB: Tạo transaction PENDING
    Payment->>Loan: Validate và settle installment
    Loan->>Loan: Transaction + khóa bản ghi + cập nhật
    Loan-->>Payment: Kết quả xử lý
    Payment->>PDB: SUCCESS hoặc FAILED
    Payment-->>FE: Kết quả giao dịch
    FE-->>Customer: Hiển thị biên nhận
~~~

## 8. Transaction, consistency và concurrency

Do mỗi service sở hữu database riêng, không dùng một transaction PostgreSQL thông thường để bao trùm Payment DB và Loan DB.

Quy trình đề xuất:
1. Payment Service tạo transaction PENDING.
2. Gọi Loan Service bằng operation ID/idempotency key ổn định.
3. Loan Service xử lý kỳ thanh toán trong transaction cục bộ.
4. Loan Service trả kết quả đã xử lý.
5. Payment Service cập nhật SUCCESS hoặc FAILED.
6. Nếu timeout/mất phản hồi, retry cùng operation ID; Loan Service trả kết quả đã lưu, không cập nhật lần hai.

Đây là phối hợp kiểu Saga đơn giản với idempotent operation. Cần có trạng thái xử lý và retry/reconciliation để xử lý trường hợp service dừng giữa các bước.

### Concurrency case 1 — Hai request cùng thanh toán một kỳ
- Dùng SELECT ... FOR UPDATE trên installment ở Loan DB.
- Kiểm tra trạng thái trong transaction.
- Chỉ chuyển UNPAID sang PAID một lần.
- Request thứ hai nhận kết quả đã xử lý hoặc conflict.
- Có unique constraint phù hợp cho operation/idempotency key.

SQL minh họa:

~~~sql
BEGIN;
SELECT id, status
FROM installments
WHERE id = :installment_id
FOR UPDATE;

-- Chỉ tiếp tục nếu trạng thái là UNPAID.

UPDATE installments
SET status = 'PAID'
WHERE id = :installment_id
  AND status = 'UNPAID';

COMMIT;
~~~

Phải kiểm tra số dòng được cập nhật.

### Concurrency case 2 — Hai kỳ của cùng khoản vay được thanh toán đồng thời
- Khóa bản ghi loan khi cập nhật dư nợ.
- Kiểm tra kỳ chưa thanh toán và số tiền hợp lệ.
- Cập nhật dư nợ bằng phép trừ có điều kiện.
- Không cho phép dư nợ âm.
- Cập nhật kỳ và dư nợ trong cùng transaction Loan DB.

SQL minh họa:

~~~sql
BEGIN;
SELECT id, outstanding_balance
FROM loans
WHERE id = :loan_id
FOR UPDATE;

-- Kiểm tra số tiền kỳ và dư nợ hợp lệ.

UPDATE loans
SET outstanding_balance = outstanding_balance - :amount
WHERE id = :loan_id
  AND outstanding_balance >= :amount;

-- Kiểm tra đúng một dòng được cập nhật.
-- Cập nhật installment trong cùng transaction.

COMMIT;
~~~

## 9. Bảo mật và yêu cầu phi chức năng

| ID | Yêu cầu | Cách kiểm chứng |
|---|---|---|
| NFR-01 | Mật khẩu được hash | Kiểm tra dữ liệu DB |
| NFR-02 | Phân quyền Customer/Admin | Test API sai role |
| NFR-03 | OTP có hạn, dùng một lần | Test hết hạn, nhập sai, dùng lại |
| NFR-04 | Database isolation | Kiểm tra service chỉ dùng DB của mình |
| NFR-05 | Không thanh toán trùng | Gửi lặp request |
| NFR-06 | Concurrency an toàn | Chạy hai request song song |
| NFR-07 | Xử lý lỗi liên service | Mô phỏng timeout/retry |
| NFR-08 | API documentation | Swagger/OpenAPI |
| NFR-09 | Automated tests | Unit và integration tests |
| NFR-10 | Container deployment | Docker Compose |

## 10. Định hướng giao diện

Phong cách fintech/banking hiện đại, sáng, tối giản, ưu tiên thông tin.
- Nền trắng/xám nhạt, navy và blue làm màu chính.
- Bảng dữ liệu rõ ràng; trạng thái có nhãn dễ nhận biết.
- Hạn chế gradient, animation và hiệu ứng trang trí.
- Không chatbot hoặc tính năng AI.

### Customer Portal

| Trang | Nội dung |
|---|---|
| Login/Register | Đăng nhập, đăng ký |
| Email Verification | Nhập OTP |
| Dashboard | Dư nợ, khoản vay, kỳ đến hạn |
| Loan Products | Danh sách gói vay |
| Loan Application | Gửi yêu cầu vay |
| My Loans | Khoản vay hiện có |
| Installments | Lịch trả góp |
| Payment | OTP và thanh toán |
| Transaction History | Lịch sử giao dịch |
| Profile | Hồ sơ cá nhân |

### Admin Portal

| Trang | Nội dung |
|---|---|
| Dashboard | Tổng quan |
| User Management | Người dùng |
| Loan Products | Quản lý gói vay |
| Applications | Theo dõi kết quả xét duyệt |
| Loans | Theo dõi khoản vay |
| Transactions | Theo dõi giao dịch |

## 11. Kế hoạch triển khai

| Giai đoạn | Công việc | Đầu ra |
|---|---|---|
| 1. Analysis & Design | Use Case, kiến trúc, ERD, API contract | Bộ tài liệu thiết kế |
| 2. Foundation | Services, DB, Gateway, Docker | Service chạy độc lập |
| 3. Authentication | Register/Login, OTP, role | Luồng tài khoản |
| 4. Loan | Products, application, auto approval, installments | Luồng vay |
| 5. Payment | OTP, transaction, idempotency, concurrency | Luồng thanh toán |
| 6. Frontend | Customer/Admin Portal | Demo end-to-end |
| 7. Testing & Delivery | Unit, integration, concurrency, docs | Bản demo và minh chứng |

### Definition of Done

- [ ] Customer đăng ký, xác thực email và đăng nhập được.
- [ ] Customer xem gói vay và gửi đơn được.
- [ ] Hệ thống tự động xét duyệt theo rule đã công bố.
- [ ] Đơn được duyệt tạo khoản vay và lịch trả góp.
- [ ] Customer thanh toán mô phỏng bằng OTP email.
- [ ] Lịch sử giao dịch phản ánh đúng kết quả.
- [ ] Không thể thanh toán trùng một kỳ.
- [ ] Hai tình huống concurrency được kiểm thử.
- [ ] Có sơ đồ kiến trúc và ERD theo từng service.
- [ ] Có API documentation, automated tests và Docker Compose.
- [ ] Có kịch bản demo và kết quả kiểm thử.

## 12. Giả định cần xác nhận trước khi code

1. Quy tắc xét duyệt và giới hạn khoản vay là quy tắc demo; nhóm cần chốt con số cụ thể.
2. Cách tính lãi, lịch đến hạn, làm tròn và xử lý kỳ cuối cần thống nhất.
3. Cần quyết định thời điểm bắt đầu lịch trả góp: ngày duyệt hay ngày tạo khoản vay.
4. Cần thống nhất JWT/session và cách xác thực request giữa các service.
5. Cần kiểm tra source code hiện tại trước khi áp dụng stack và cấu trúc mục tiêu.

> Đây là baseline thiết kế F168, không phải mô tả trạng thái hiện tại. Mọi khác biệt với source code và yêu cầu chính thức của giảng viên cần được ghi nhận trước khi triển khai.
