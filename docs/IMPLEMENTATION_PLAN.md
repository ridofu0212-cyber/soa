# F168 · Implementation Plan

Baseline: [PROJECT_SPEC.md v1.2](PROJECT_SPEC.md), 17 quyết định ở §7.3. Snapshot `main` được đọc tại `39a7a61fbdd55670df9dfe47ee5eba1874645b50`. Cây Git có ba tài liệu thiết kế, chưa có implementation. Gói này là source mới để nhóm kiểm tra trước khi tích hợp vào repository.

## Mốc nghiệm thu

| Phase | Phụ thuộc | Đầu ra cần bàn giao | Trạng thái lượt này |
|---|---|---|---|
| 1 · Repository Foundation | SPEC v1.2, Python 3.13, Node 22, PostgreSQL 16, Compose v2 | Ba skeleton, Gateway, frontend trạng thái, cấu hình, tests, hướng dẫn | BLOCKED ở gate Docker; kết quả chạy native trong [test report](TEST_REPORT_PHASE1.md) |
| 2 · User Service | Foundation được nhóm xác nhận; DB User, Gmail thử nghiệm và tài khoản seed riêng | 4 bảng User, xác thực, profile và hai API nội bộ | NOT STARTED |
| 3 · Loan Service | Foundation, contract xác minh account của User; PostgreSQL test riêng | 5 bảng Loan, preview, duyệt, lịch, settlement | NOT STARTED |
| 4 · Payment Service | API verified-email của User, validate/settle của Loan, SMTP | 3 bảng Payment, OTP, giao dịch, history và recovery | NOT STARTED |
| 5 · Frontend Integration | Contract và API thật của Phase 2–4, dữ liệu demo | Sáu nhóm màn hình Customer/Admin | NOT STARTED |
| 6 · Testing & Hardening | Hệ thống tích hợp, dữ liệu test cô lập, hai email OTP thật | Minh chứng E2E-01–06, C1–C5, regression | NOT STARTED |
| 7 · Documentation & Demo | Source, API, test report và dữ liệu demo đã kiểm chứng | Architecture diagram, ERD, báo cáo, demo, walkthrough A/B | NOT STARTED |

A sở hữu Loan, JWT/login/profile. B sở hữu Payment, register/OTP/SMTP. Hai người cùng review hợp đồng HTTP, Docker, giao dịch qua hai DB và bằng chứng demo. Mỗi phase đối chiếu SPEC → lập checklist → code → chạy test → sửa → cập nhật tài liệu. Chức năng chỉ được ghi DONE khi có bằng chứng chạy. Với gate thiếu môi trường, ghi BLOCKED theo hạng mục và giữ bằng chứng của phần đã chạy độc lập. Phase 2 chờ nhóm xác nhận.

## 1 · Repository Foundation

- [x] Kiểm tra cây Git và ZIP tham khảo. Đưa bản SPEC nguyên gốc vào `docs/`.
- [x] Dựng User, Loan và Payment bằng FastAPI sync, mỗi app có engine, metadata và session riêng. Health phải truy vấn PostgreSQL.
- [x] Khai báo ba DB/volume riêng, ứng dụng và Nginx bằng Compose. Chỉ Gateway có host port. Thêm frontend React/TS/Tailwind/Vite, OpenAPI/Swagger riêng, error envelope và request ID.
- [x] Kiểm tra cài dependency, build UI, khởi động ba app, định tuyến HTTP và chặn internal trong môi trường native. Kiểm tra khi DB/API dừng. Chi tiết ở test report.
- [ ] Nghiệm thu trên Docker Desktop: build image, bảy container healthy, kiểm tra Gateway từ host, chạy bộ test và kiểm tra restart/volume. Cả hai làm theo README từ bản giải nén.

**Phân công học.** A trace `/health/loan` qua Nginx đến `SELECT 1`. B trace `/health/payment`, giải thích 503 và đối chiếu request ID. Hai người đổi vai khi chạy lại.

## 2 · User Service

- [ ] Viết models/constraints cho `users`, `user_profiles`, `otp_codes`, `refresh_tokens`; quan hệ profile 1–1. Chốt DTO, mã lỗi và data dictionary; tạo bảng bằng `create_all`, seed Admin verified từ env chạy lặp an toàn.
- [ ] B triển khai register, chuẩn hóa email, hash password/OTP, verify/resend, SMTP SSL 465. OTP 6 chữ số, TTL 5 phút, 5 lần nhập sai, resend cách 60 giây, tối đa 5 lần/15 phút. Khóa hàng user trước khi đếm/tạo. Commit challenge trước SMTP và vô hiệu đúng challenge nếu gửi lỗi.
- [ ] A triển khai OAuth2 form login bằng email, JWT HS256 60 phút, dependency role, profile và kiểm tra ACTIVE/verified. Hai người review hai API nội bộ và token riêng. Bảng refresh được giữ theo ERD.
- **Test/gate.** Email trùng sau chuẩn hóa, password ngắn, OTP sai/hết hạn/replay/resend song song, SMTP fail, sai attempts phải được lưu; login account inactive/unverified, JWT sai/hết hạn, Customer vào Admin, ownership, internal token thiếu/sai. Chứng minh register → nhận Gmail thật → verify → login (E2E-01) và seed lặp an toàn.

## 3 · Loan Service

- [ ] A tạo `loan_products`, `loan_applications`, `loans`, `installments`, `settlement_operations`; index unique có điều kiện một ACTIVE loan/user. Seed đúng hai gói SPEC §4.2. B kiểm tra contract và dữ liệu cần cho Payment.
- [ ] Dùng một hàm Equal Principal cho preview và tạo loan. Tiền VND nguyên, lãi tính trên gốc đầu kỳ với Decimal/HALF_UP; kỳ cuối bù gốc. Lấy ngày nghiệp vụ Việt Nam, neo ngày gốc khi tháng ngắn. Snapshot điều khoản tại thời điểm duyệt.
- [ ] Xác minh User trước xét duyệt; phân biệt malformed (422), trượt rule (201 REJECTED), dependency lỗi (503). Ghi application/loan/kỳ trong một transaction. Chỉ bắt unique violation đúng index khi hai đơn tranh chấp. Hoàn thiện public/customer/admin API §4.8.
- [ ] Settlement nội bộ khóa loan rồi khóa kỳ, so khớp identity với snapshot khi replay; một commit đánh dấu PAID, trừ riêng gốc, kiểm tra CLOSED và lưu operation.
- **Test/gate.** Rate 0 và 12%, số lẻ, ngày 29/30/31, tổng gốc, snapshot bất biến; rollback giữa chừng, không trả trước hạn, hai đơn đồng thời (C3), owner, User không sẵn sàng. Thử C1/C2 trên PostgreSQL ngay khi endpoint settle sẵn sàng; kiểm tra số dư trước/sau và replay. E2E-02/03.

## 4 · Payment Service

- [ ] B tạo `payment_otps`, `payment_transactions`, `payment_attempts`. Lấy email đã verify và dữ liệu kỳ từ đúng service. Giới hạn OTP trên toàn bộ kỳ của cùng user, dùng transaction-level advisory lock theo UUID user. Verify dưới row lock, cấp vé UUID một lần, TTL 5 phút. OTP mới vô hiệu vé cũ cùng kỳ.
- [ ] Tìm transaction theo user/key và SHA-256 canonical JSON trước khi yêu cầu vé. Với giao dịch mới, khóa OTP row, consume vé và ghi PENDING trong một commit. Cùng key khác fingerprint trả 409. Không log vé.
- [ ] Commit PENDING và attempt trước HTTPX. Mỗi lượt tối đa hai lần gọi, timeout 5s, nghỉ 1s trước retry, giữ cùng operation_id. Chưa rõ kết quả → REQUIRES_RECONCILIATION. Dùng chung nghiệp vụ cho retry và `reconcile.py`. Bảo vệ terminal state; thêm history/detail/Admin.
- **Test/gate.** Nhận Gmail OTP thanh toán thật; sai chủ/hết hạn/vé dùng lại/SMTP lỗi. Double-click, hai key cùng vé, hai request cùng key (C4). Hai nhóm cùng kiểm tra C1/C2 và mô phỏng mất phản hồi sau Loan commit (C5); đối chiếu count/amount ở hai DB, attempt và snapshot. E2E-04/05.

## 5 · Frontend Integration

- [ ] A phụ trách login/profile, gói/preview/nộp đơn, My Loans và Admin gói/đơn/loan; B phụ trách register/verify, payment/OTP, history và Admin giao dịch. Hai người thống nhất sáu nhóm màn hình theo §4.9.
- [ ] Native fetch qua `/api/v1`; Auth Context + sessionStorage cho JWT, xóa khi logout/401. OTP/vé chỉ ở memory. Giữ key/payload khi retry; sau refresh tra history và trạng thái kỳ. Hiển thị loading/empty/error, trạng thái chưa xác định và gói inactive cho Admin.
- [ ] Chuẩn bị `seed_demo.py` cho user và loan đủ điều kiện, ít nhất hai kỳ đã đến hạn. Seed lặp không nhân đôi dữ liệu.
- **Test/gate.** Chạy hai vai qua trình duyệt, dùng API thật, một giao dịch thành công và một retry; kiểm tra key giữ nguyên, giao dịch, kỳ và dư nợ khớp DB. Demo không cần sửa DB bằng tay.

## 6 · Testing & Hardening

- [ ] Tạo DB/volume test tách demo. Pytest + HTTPX cho API integration/E2E, ghi expected/actual và phiên bản. Hai lần smoke Gmail thực (User và Payment), mock SMTP trong automated tests.
- [ ] E2E-01 đăng ký đến login; 02 đơn trượt chính sách; 03 duyệt và rollback; 04 kỳ đến hạn thanh toán; 05 duplicate/replay; 06 quyền Admin, ownership và internal token.
- [ ] A chuẩn bị PostgreSQL + hai request độc lập cho C1 (hai operation khác nhau trên cùng kỳ qua Loan internal API) và C2 (hai kỳ cùng loan); C3 một ACTIVE loan. B chuẩn bị C4 vé/key và C5 reconcile. Cả hai ghi response, dữ liệu trước/sau, số operation và attempts; che bí mật.
- **Gate.** Bằng chứng C1 chỉ giảm gốc một lần; C2 giảm đúng tổng hai phần gốc; C3 không orphan; C4 một thanh toán logic; C5 reconcile cùng operation và bảo toàn terminal. Chạy lại deployment, seed, validation, quyền, request ID, UI. Mỗi FAIL có lỗi tái hiện, bản sửa và kết quả chạy lại.

## 7 · Documentation & Demo

- [ ] Cập nhật README, architecture diagram, ERD đủ 4+5+3 bảng, data dictionary, Swagger/OpenAPI, test report, demo script và walkthrough trỏ đến hàm có thật. A viết phần Loan/JWT; B viết Payment/OTP. Đối chiếu diagram, đường dẫn, payload và source.
- [ ] Thành viên còn lại giải nén sạch, build, seed và chạy từ README. Demo register → email OTP → login → vay → kỳ đến hạn → thanh toán OTP → history; tiếp theo C1/C2, rồi recovery C5. Dùng hai kỳ đã đến hạn từ seed.
- **Gate.** Có bằng chứng chạy từ môi trường sạch, có API/DB/UI thật, diagram kiến trúc, hai demo tranh chấp và kiểm tra dư nợ. A giải thích thứ tự khóa và giảm gốc; B giải thích PENDING/operation_id; cả hai liên hệ Units 18–21. Rubric 9.0–9.5+ là mục tiêu đánh giá của nhóm.

## Đối chiếu bài giảng

| Bài của giảng viên | Phần tương ứng trong F168 |
|---|---|
| [Unit 18 · JWT](https://fastapi-docs.duonghuuphuc.com/unit-18-jwt-authentication-with-fastapi) | Phase 2 dùng pwdlib, form login, bearer token và phân quyền. |
| [Unit 19 · Microservices](https://fastapi-docs.duonghuuphuc.com/unit-19-building-and-communicating-microservices) | Phase 1 tách process/DB. Phase 3–4 dùng HTTPX sync và xử lý service không sẵn sàng. |
| [Unit 20 · Third-party services](https://fastapi-docs.duonghuuphuc.com/unit-20-integrating-third-party-services) | Phase 2/4 vận dụng xử lý lỗi, timeout, retry và idempotency vào Gmail SMTP và payment. |
| [Unit 21 · Containerization](https://fastapi-docs.duonghuuphuc.com/unit-21-containerizing-and-deploying-microservices) | Phase 1 dùng Dockerfile, service name, Compose network, env và healthchecks. |
| [Unit 22 · Integration testing](https://fastapi-docs.duonghuuphuc.com/unit-22-end-to-end-microservice-integration-and-testing) | Tham khảo cho E2E qua Gateway ở Phase 6. |

## Checklist nhóm trước khi cho phép Phase 2

- [ ] Chạy build, bộ test và restart trên Docker Desktop theo README. Ghi kết quả, OS, phiên bản Compose và commit/gói đã dùng. Nếu còn lỗi, giữ trạng thái gate tương ứng.
- [ ] A và B tự trace một request health và một request bị chặn tại Gateway.
- [ ] Có email demo nhận thư được, Gmail App Password trong `.env` riêng, Admin/demo credentials và hai secret độc lập. Chuẩn bị DB test riêng. Chỉ cần Gmail từ Phase 2.
- [ ] Cả hai đối chiếu §4.4, §4.8, §5.1; xác nhận ranh giới register/verify và login/profile, cách chạy seed và smoke test Gmail.
- [ ] Nhóm xác nhận bắt đầu Phase 2.
