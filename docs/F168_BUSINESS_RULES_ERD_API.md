# F168 — Business Rules, ERD và REST API Contract

> Baseline đã được nhóm xác nhận. Đề tài Loan Installment; backend Python + FastAPI; PostgreSQL riêng từng service; SMTP gửi email thật. Đây là thiết kế mục tiêu, không khẳng định source code đã triển khai.

## 1. Quyết định đã chốt

| Hạng mục | Quyết định |
|---|---|
| Phương thức trả nợ | Equal Principal — gốc đều |
| Lãi suất | Cố định trong toàn bộ thời hạn vay |
| Chu kỳ | Hàng tháng |
| Ngày bắt đầu | Ngày Loan được tạo sau khi đơn APPROVED (ngày giải ngân mô phỏng) |
| Trả trước hạn | Không hỗ trợ trong v1 |
| Quá hạn | Chỉ chuyển OVERDUE; không tính phí phạt |
| Thanh toán | Mô phỏng; không có tiền thật di chuyển |
| OTP | OTP tài khoản và OTP thanh toán gửi qua SMTP tới email thật |

## 2. Business Rules

### 2.1 Gói vay và xét duyệt
- Chỉ gói ACTIVE được hiển thị và dùng để tạo đơn.
- requested_amount phải nằm trong min_amount/max_amount; term_months phải thuộc kỳ hạn gói hỗ trợ.
- Customer không được gửi/sửa lãi suất, status, user_id, số tiền kỳ trả hoặc kết quả xét duyệt.
- Chỉ tài khoản ACTIVE và email VERIFIED mới được nộp đơn; Loan Service xác minh qua User Service bằng service authentication.
- Rule-based approval kiểm tra trạng thái user, gói ACTIVE, hạn mức, kỳ hạn và giới hạn khoản vay ACTIVE được cấu hình.
- Đạt mọi rule: application APPROVED và tạo Loan + Installments. Không đạt: REJECTED kèm rejection_code/reason; không tạo Loan/Installments.
- Ngưỡng giới hạn khoản vay ACTIVE phải cấu hình, ghi tài liệu và kiểm thử; không đặt ngầm trong code.
- Application, Loan và lịch Installments phải được tạo trong một transaction Loan DB; lỗi sinh lịch thì rollback.
- Snapshot lãi suất/điều khoản tài chính vào application/loan; thay đổi gói không làm thay đổi khoản vay cũ.

### 2.2 Equal Principal — lãi suất cố định
Ký hiệu P là principal ban đầu (VND), n là term_months, R là annual_interest_rate dạng tỷ lệ (12% = 0.12), B(k) là dư nợ gốc đầu kỳ k.
1. Gốc kỳ thông thường = P / n.
2. Gốc lưu bằng VND nguyên; làm tròn đến đồng gần nhất. Kỳ cuối điều chỉnh bằng gốc còn lại để tổng principal_due đúng bằng P.
3. Lãi kỳ k = B(k) × R / 12; làm tròn đến VND gần nhất.
4. total_due = principal_due + interest_due.
5. Dư nợ cuối kỳ = dư nợ đầu kỳ − principal_due.
6. Lãi suất 0% thì interest_due = 0.
7. Dùng integer cho VND và NUMERIC/DECIMAL cho rate; không dùng float cho tính toán tài chính.

Ví dụ P = 120.000.000 VND, n = 12, R = 0.12: gốc mỗi kỳ 10.000.000; kỳ 1 lãi 1.200.000, tổng 11.200.000; kỳ 2 lãi 1.100.000, tổng 11.100.000; kỳ 12 lãi 100.000, tổng 10.100.000; tổng lãi 7.800.000 VND.

### 2.3 Ngày đến hạn và trạng thái
- loan_start_date là ngày tạo Loan sau khi application APPROVED.
- Kỳ đầu đến hạn sau một tháng; các kỳ sau cùng ngày trong tháng. Nếu tháng không có ngày tương ứng, dùng ngày cuối tháng (ví dụ ngày 31 → ngày cuối tháng).
- Lưu due_date thực tế vào từng installment; kiểm thử ngày 29/30/31.
- Loan tạo ở trạng thái ACTIVE; Installment tạo ở UNPAID.
- UNPAID chuyển OVERDUE khi ngày hiện tại vượt due_date và chưa thanh toán.
- UNPAID hoặc OVERDUE chuyển PAID sau khi settle thành công; không chuyển PAID ngược lại.
- Loan chuyển CLOSED khi outstanding_principal = 0 và mọi installment PAID.
- Không hỗ trợ trả trước hạn trong v1. Quá hạn chỉ đổi trạng thái OVERDUE, không tính phí phạt. Không có phí dịch vụ/phí trễ hạn trong v1.

### 2.4 Thanh toán mô phỏng
- Customer chỉ thanh toán installment thuộc loan của mình, trạng thái UNPAID hoặc OVERDUE.
- Số tiền chuẩn lấy từ Loan Service: principal_due + interest_due; không tin amount frontend gửi.
- OTP thanh toán gửi qua SMTP tới email VERIFIED; lưu hash, có hạn dùng, giới hạn lần thử, dùng một lần; không trả OTP/hash trong API response/log.
- OTP challenge gắn với user và installment; xác thực thành công tạo payment authorization ngắn hạn, dùng một lần.
- Mọi payment request yêu cầu Idempotency-Key. Cùng key + cùng payload trả kết quả cũ; cùng key nhưng payload khác trả HTTP 409.
- Payment Service tạo transaction PENDING trước khi gọi Loan Service.
- Loan Service khóa loan/installment, xác minh owner/status/amount/operation_id; cập nhật installment, outstanding_principal và settlement operation trong cùng transaction.
- Khi settle thành công, dư nợ gốc chỉ giảm principal_due, không giảm total_due vì total_due gồm cả lãi.
- Retry sau timeout dùng lại operation_id; Loan Service trả kết quả đã lưu, không settle lần hai.
- Timeout không rõ kết quả không được tự đánh dấu FAILED; giữ PENDING/REQUIRES_RECONCILIATION và retry/đối soát.
- Không có tiền thật di chuyển.

## 3. ERD và data ownership

ID từ service khác là external reference; không tạo foreign key vật lý xuyên database.

### 3.1 User Service DB

~~~mermaid
erDiagram
    USERS ||--o{ USER_PROFILES : has
    USERS ||--o{ OTP_CODES : receives
    USERS ||--o{ REFRESH_TOKENS : owns
    USERS {
        uuid id PK
        varchar email UK
        varchar password_hash
        varchar role
        varchar status
        boolean email_verified
        timestamptz created_at
        timestamptz updated_at
    }
    USER_PROFILES {
        uuid id PK
        uuid user_id FK
        varchar full_name
        varchar phone
        timestamptz updated_at
    }
    OTP_CODES {
        uuid id PK
        uuid user_id FK
        varchar purpose
        varchar otp_hash
        timestamptz expires_at
        int attempts
        boolean consumed
        timestamptz created_at
    }
    REFRESH_TOKENS {
        uuid id PK
        uuid user_id FK
        varchar token_hash
        timestamptz expires_at
        timestamptz revoked_at
    }
~~~

### 3.2 Loan Service DB

~~~mermaid
erDiagram
    LOAN_PRODUCTS ||--o{ LOAN_APPLICATIONS : selected_for
    LOAN_APPLICATIONS ||--o| LOANS : creates
    LOANS ||--|{ INSTALLMENTS : contains
    LOANS ||--o{ SETTLEMENT_OPERATIONS : records
    LOAN_PRODUCTS {
        uuid id PK
        varchar name
        bigint min_amount
        bigint max_amount
        numeric annual_interest_rate
        jsonb allowed_terms_months
        boolean is_active
        timestamptz created_at
        timestamptz updated_at
    }
    LOAN_APPLICATIONS {
        uuid id PK
        uuid user_id
        uuid product_id FK
        bigint requested_amount
        int term_months
        numeric annual_interest_rate_snapshot
        varchar status
        varchar rejection_code
        text rejection_reason
        timestamptz submitted_at
        timestamptz decided_at
    }
    LOANS {
        uuid id PK
        uuid application_id FK
        uuid user_id
        uuid product_id
        bigint principal_amount
        numeric annual_interest_rate
        int term_months
        date loan_start_date
        bigint outstanding_principal
        varchar status
        timestamptz created_at
    }
    INSTALLMENTS {
        uuid id PK
        uuid loan_id FK
        int installment_number
        date due_date
        bigint opening_principal
        bigint principal_due
        bigint interest_due
        bigint total_due
        bigint principal_paid
        bigint interest_paid
        varchar status
        timestamptz paid_at
    }
    SETTLEMENT_OPERATIONS {
        uuid id PK
        uuid operation_id UK
        uuid installment_id
        bigint amount
        varchar result_status
        jsonb result_snapshot
        timestamptz created_at
    }
~~~

Constraints: loan_applications.product_id FK nội bộ; loans.application_id UNIQUE; installments (loan_id, installment_number) UNIQUE; CHECK principal_due >= 0, interest_due >= 0, total_due = principal_due + interest_due; paid amounts không vượt due amounts; settlement_operations.operation_id UNIQUE. installment_id trong settlement_operations FK nội bộ. user_id là external ID từ User Service, không FK sang User DB. Loan Service sở hữu products, applications, loans, installments và settlement operations.

### 3.3 Payment Service DB

~~~mermaid
erDiagram
    PAYMENT_TRANSACTIONS ||--o{ PAYMENT_ATTEMPTS : has
    PAYMENT_TRANSACTIONS {
        uuid id PK
        uuid user_id
        uuid loan_id
        uuid installment_id
        uuid operation_id UK
        varchar idempotency_key
        varchar request_fingerprint
        bigint amount
        varchar status
        varchar failure_code
        timestamptz created_at
        timestamptz updated_at
        timestamptz completed_at
    }
    PAYMENT_OTPS {
        uuid id PK
        uuid user_id
        uuid installment_id
        varchar otp_hash
        timestamptz expires_at
        int attempts
        boolean consumed
        timestamptz created_at
    }
    PAYMENT_ATTEMPTS {
        uuid id PK
        uuid transaction_id FK
        int attempt_number
        varchar outcome
        text error_summary
        timestamptz created_at
    }
~~~

Constraints: unique (user_id, idempotency_key); operation_id UNIQUE; payment_attempts (transaction_id, attempt_number) UNIQUE. Payment owns transactions/OTP; Loan owns loan/installment/settlement state; User owns identity/email. Không có FK vật lý xuyên service.

## 4. REST API Contract

Base path: /api/v1. JSON; UUID identifiers; timestamps ISO-8601 UTC; VND amounts integer; interest rate decimal string (ví dụ "0.12"). Đây là contract mục tiêu, không khẳng định endpoint đã tồn tại.

### 4.1 Quy tắc bảo mật
- Customer dùng Bearer access token; user_id lấy từ claim sub, không tin user_id trong body.
- Admin endpoint yêu cầu role ADMIN.
- Internal service endpoint dùng credential nội bộ qua private network; không expose cho frontend.
- Không trả password_hash, OTP, OTP hash, SMTP credentials hoặc secrets.
- List API có pagination; validation bằng Pydantic; công bố OpenAPI.

### 4.2 User Service

| Method | Endpoint | Auth | Mục đích |
|---|---|---|---|
| POST | /auth/register | Public | Tạo tài khoản, gửi OTP xác thực qua SMTP |
| POST | /auth/verify-email | Public | Xác thực OTP |
| POST | /auth/resend-verification | Public | Gửi lại OTP có rate limit |
| POST | /auth/login | Public | Đăng nhập, trả access token |
| POST | /auth/refresh | Refresh token | Làm mới access token nếu triển khai |
| POST | /auth/logout | Customer | Thu hồi refresh token nếu triển khai |
| GET | /users/me | Customer | Xem profile |
| PATCH | /users/me | Customer | Cập nhật profile |
| GET | /internal/users/{user_id}/verification | Service auth | Xác minh account ACTIVE và email VERIFIED |
| GET | /internal/users/{user_id}/verified-email | Service auth | Payment lấy email VERIFIED để gửi OTP |

Register body: email, password, full_name. Verify body: email, otp, purpose. Response chỉ xác nhận đã gửi; không trả OTP.

### 4.3 Loan Service

| Method | Endpoint | Auth | Mục đích |
|---|---|---|---|
| GET | /loan-products | Public/Customer | Danh sách gói ACTIVE |
| GET | /loan-products/{product_id} | Public/Customer | Chi tiết gói |
| POST | /loan-applications | Customer | Tạo đơn và auto-approval |
| GET | /loan-applications | Customer | Danh sách đơn của mình |
| GET | /loan-applications/{application_id} | Owner/Admin | Chi tiết đơn |
| GET | /loans | Customer | Khoản vay của mình |
| GET | /loans/{loan_id} | Owner/Admin | Chi tiết khoản vay |
| GET | /loans/{loan_id}/installments | Owner/Admin | Lịch trả góp |
| GET | /installments/{installment_id} | Owner/Admin | Chi tiết kỳ |
| POST | /admin/loan-products | Admin | Tạo gói |
| PATCH | /admin/loan-products/{product_id} | Admin | Cập nhật/ngừng gói |
| GET | /admin/loan-applications | Admin | Theo dõi đơn |
| GET | /admin/loans | Admin | Theo dõi khoản vay |
| POST | /internal/installments/{installment_id}/settlements | Service auth | Settle kỳ bằng operation_id |

Application body chỉ nhận product_id, requested_amount, term_months; không nhận user_id, interest_rate, status hoặc số tiền kỳ. Backend lấy user từ token. Nếu duyệt, response có loan_id và schedule; nếu từ chối, có rejection_code/reason.

Internal settlement body: operation_id, user_id, amount, payment_transaction_id. Loan Service kiểm tra owner và amount = total_due lưu trong DB. Idempotent theo operation_id. Response: settlement status, installment status, principal_paid, interest_paid, outstanding_principal.

### 4.4 Payment Service

| Method | Endpoint | Auth | Mục đích |
|---|---|---|---|
| POST | /payment-otp-requests | Customer | Yêu cầu OTP cho installment |
| POST | /payment-otp-verifications | Customer | Xác thực OTP, cấp authorization dùng một lần |
| POST | /payment-transactions | Customer | Tạo thanh toán mô phỏng |
| GET | /payment-transactions | Customer | Lịch sử của mình |
| GET | /payment-transactions/{transaction_id} | Owner/Admin | Chi tiết giao dịch |
| GET | /admin/payment-transactions | Admin | Theo dõi giao dịch |

Payment body gồm installment_id và payment_authorization; yêu cầu header Idempotency-Key. Backend lấy user từ token và amount từ Loan Service, không nhận amount do client quyết định. Cùng user + key + request fingerprint trả transaction cũ; cùng key khác payload trả 409.

### 4.5 Error response

~~~json
{
  "error": {
    "code": "INSTALLMENT_ALREADY_PAID",
    "message": "This installment has already been settled.",
    "details": {},
    "request_id": "..."
  }
}
~~~

HTTP mapping: 400 input/nghiệp vụ không hợp lệ; 401 unauthenticated; 403 forbidden; 404 không tồn tại/không thuộc quyền (theo chính sách chống dò ID); 409 conflict/idempotency conflict/đã thanh toán; 422 validation; 429 OTP rate limit; 500 lỗi ngoài dự kiến; 503 dependency unavailable. Chỉ dùng 202 nếu thực sự xử lý bất đồng bộ và có resource để truy vấn trạng thái.

## 5. Transaction, consistency và concurrency

Payment DB và Loan DB không thể nằm trong cùng local PostgreSQL transaction. Dùng orchestration kiểu Saga đơn giản:
1. Payment Service tạo transaction PENDING với operation_id ổn định.
2. Gọi internal settle endpoint của Loan Service.
3. Loan Service thực hiện một transaction cục bộ: khóa loan/installment; kiểm tra owner/status/amount; ghi settlement_operations; chuyển installment PAID; giảm outstanding_principal bằng principal_due; đóng loan nếu mọi kỳ đã PAID.
4. Payment Service đánh dấu SUCCESS sau phản hồi settle thành công.
5. Timeout/không rõ kết quả: giữ PENDING/REQUIRES_RECONCILIATION và retry cùng operation_id. Loan Service trả kết quả đã lưu nếu operation đã xử lý.

Concurrency:
- Cùng installment: SELECT FOR UPDATE + unique operation_id + chuyển trạng thái có điều kiện; chỉ một request settle thành công.
- Hai installment khác nhau của cùng loan: khóa loan trước, sau đó khóa installment theo thứ tự ID tăng dần; cập nhật outstanding principal bằng tổng principal_due, không trừ lãi; không cho dư nợ âm.
- Payment unique (user_id, idempotency_key); cùng key khác request fingerprint trả 409.

## 6. Acceptance tests

- Loan 120.000.000 / 12 tháng / 12% năm: gốc mỗi kỳ 10.000.000, tổng lãi 7.800.000.
- Tổng principal_due đúng bằng principal_amount sau điều chỉnh kỳ cuối.
- Rate 0 tạo interest_due bằng 0.
- Sửa lãi suất product không thay đổi lịch khoản vay đã tạo.
- Qua due_date mà chưa trả: OVERDUE; không cộng phí.
- Không hỗ trợ trả trước hạn trong v1.
- Customer không settle được installment của user khác.
- Payment amount phải bằng principal_due + interest_due.
- Settlement thành công chỉ giảm outstanding_principal bằng principal_due.
- Retry cùng operation_id trả kết quả cũ; không settle kỳ hai lần.
- Hai kỳ của cùng loan thanh toán đồng thời không làm dư nợ âm.
- OTP đến mailbox thật, hết hạn, dùng một lần; không xuất hiện trong response/log.
