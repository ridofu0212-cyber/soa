# F168 · Loan Installment

Đồ án SOA của nhóm hai thành viên. **Phase 1 — Repository Foundation** cung cấp một trang trạng thái và ba service chạy độc lập. Mỗi lần kiểm tra, FastAPI gửi `SELECT 1` tới PostgreSQL của chính service đó. Ở mốc này có **0 bảng nghiệp vụ**. Phase 2/3/4 sẽ lần lượt thêm 4/5/3 bảng.

| Mục đích | Tài liệu |
|---|---|
| Xem kế hoạch, phụ thuộc, phân công và gate của bảy phase | [Implementation Plan](docs/IMPLEMENTATION_PLAN.md) |
| Học theo đường đi một request, xem sơ đồ và lộ trình A/B | [Code Walkthrough](docs/CODE_WALKTHROUGH.md) |
| Tra kết quả đã chạy và phần BLOCKED | [Báo cáo kiểm thử Phase 1](docs/TEST_REPORT_PHASE1.md) |
| Tra hợp đồng API, schema và 17 quyết định | [PROJECT_SPEC.md v1.2](docs/PROJECT_SPEC.md) |

## Chạy lần đầu trên Windows

Cần Docker Desktop chạy **Linux containers**, Compose v2 (đã kiểm tra cấu hình với 2.39.4), kết nối mạng cho lần tải image/package đầu tiên và cổng localhost 8080 trống. Python, Node và Nginx nằm trong image. Máy Windows chỉ cần Docker Desktop và PowerShell.

1. Giải nén ZIP. Mở PowerShell trong thư mục `f168` có file `docker-compose.yml`.
2. Kiểm tra Docker Engine và Compose. Lệnh đầu cần có cả phần Server.

   ```powershell
   docker version
   docker compose version
   ```

3. Tạo `.env` một lần. Script sinh riêng ba mật khẩu DB, JWT secret và internal token, giữ trống Gmail/Admin/demo. Nếu đã có `.env`, dùng file hiện có.

   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\init-env.ps1
   ```

   Cũng có thể sao chép `.env.example` thành `.env` và tự điền ba mật khẩu DB khác nhau. Chuỗi hex ngẫu nhiên dễ dùng với phép nội suy của Compose. Chỉ ba mật khẩu DB cần có cho Foundation. Dùng `config -q` để kiểm tra cấu hình mà không in secret.

4. Dùng project name riêng cho bài kiểm tra để các volume test tách khỏi demo. Giữ biến này trong cùng cửa sổ PowerShell.

   ```powershell
   $env:COMPOSE_PROJECT_NAME = "f168_p1test"
   docker compose config -q
   docker compose up --build -d --wait --wait-timeout 180
   docker compose ps
   ```

   Kỳ vọng 7 container healthy; chỉ gateway publish `127.0.0.1:8080`. Lần sau có thể dùng `docker compose up -d --wait`. Khi đổi project test/demo, dừng project đang giữ cổng 8080 trước.

5. Mở [trang trạng thái](http://localhost:8080/). Nhấn **Kiểm tra lại**. Cả ba dòng cần hiện **Sẵn sàng**. Bấm **Swagger**, mở thao tác GET, chọn **Try it out** rồi **Execute**. Response phải mang đúng tên service và database có trạng thái ok.

| Mục đích | Đường dẫn qua Gateway |
|---|---|
| Trang React / trạng thái riêng của Nginx | `/` và `/health/gateway` |
| Health có truy vấn DB | `/health/user`, `/health/loan`, `/health/payment` |
| Swagger UI | `/docs/user`, `/docs/loan`, `/docs/payment` |
| OpenAPI JSON | `/openapi/user.json`, `/openapi/loan.json`, `/openapi/payment.json` |
| Internal public | `/api/v1/internal` và mọi đường dẫn bên dưới trả 403 ngay tại Gateway |

Trong Compose, backend nghe cổng 8000 và có `GET /health`, DB nghe cổng 5432. Các cổng đó chỉ dùng trong mạng container. App dùng DNS `user-db`, `loan-db`, `payment-db`. Đã dành route cho các nhóm API public/Admin ở §4.8. Ví dụ `/api/v1/loans` trả 404 JSON từ Loan trong Phase 1; chức năng xem khoản vay thuộc Phase 3.

## Kiểm thử, tra log và restart

Sau khi stack healthy, chạy trong cùng cửa sổ PowerShell.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1
curl.exe -i http://localhost:8080/health/loan
curl.exe -i http://localhost:8080/api/v1/internal/installments/example
```

Bộ test có 5 test/service và 26 test Gateway. Script dừng với exit code khác 0 khi có lỗi. Health Loan thành công trả HTTP 200 và body sau.

```json
{"service":"loan","status":"ok","database":"ok"}
```

Dùng cùng request ID để tìm đúng dòng log của cả Gateway và Loan.

```powershell
$rid = [guid]::NewGuid().ToString()
curl.exe -s -H "X-Request-ID: $rid" http://localhost:8080/health/loan
docker compose logs --no-color gateway loan-service | Select-String -SimpleMatch $rid
```

Thử lỗi kết nối trên project test. Khi Loan DB dừng, Loan phải trả 503, User vẫn trả 200. Sau khi DB khởi động lại, có thể cần vài giây để healthcheck cập nhật.

```powershell
docker compose stop loan-db
curl.exe -i http://localhost:8080/health/loan
curl.exe -i http://localhost:8080/health/user
docker compose up -d --wait
curl.exe -i http://localhost:8080/health/loan
```

Kiểm chứng volume qua một lần hạ/dựng lại. Hai lần đọc mã định danh cluster PostgreSQL phải bằng nhau.

```powershell
$before = docker compose exec -T loan-db psql -U f168_loan -d f168_loan -Atc "SELECT system_identifier FROM pg_control_system()"
if ($LASTEXITCODE -ne 0 -or -not $before) { throw "Khong doc duoc cluster ID ban dau" }
docker compose down
docker compose up -d --wait
$after = docker compose exec -T loan-db psql -U f168_loan -d f168_loan -Atc "SELECT system_identifier FROM pg_control_system()"
if ($LASTEXITCODE -ne 0 -or $before -ne $after) { throw "Kiem tra volume that bai" }
docker compose ps
```

Kết thúc bằng `docker compose down` để giữ volume. Khi thực sự muốn xóa dữ liệu **riêng project test**, dùng `docker compose -p f168_p1test down --volumes` sau khi kiểm tra đúng tên. `create_all()` tạo bảng còn thiếu; đổi cột đã có cần SQL cập nhật hoặc reset DB test có chủ đích.

| Dấu hiệu | Cách xác định nguyên nhân |
|---|---|
| Thiếu phần Server của Docker | Khởi động Docker Desktop, đợi Linux Engine sẵn sàng, chạy lại `docker version`. |
| Compose báo thiếu mật khẩu | Kiểm tra vị trí và ba biến DB trong `.env`, chạy `docker compose config -q`. |
| Cổng 8080 đang dùng | Kiểm tra `docker ps` và `Get-NetTCPConnection -LocalPort 8080`. Dừng đúng project đang giữ cổng. |
| Service unhealthy | Chạy `docker compose logs --tail 50 loan-db loan-service`. Nếu đổi mật khẩu sau khi tạo volume, khôi phục đúng mật khẩu hoặc đổi trong PostgreSQL có chủ đích. |
| 404 khi gọi register/login/loans | Header `X-Service-Name` cho biết request đến service nào. Các API nghiệp vụ nằm trong kế hoạch Phase 2–4. |

## Cây source và vai trò file

```text
f168/
  .dockerignore, .env.example, .gitignore, docker-compose.yml, README.md
  docs/
    PROJECT_SPEC.md, IMPLEMENTATION_PLAN.md, CODE_WALKTHROUGH.md, TEST_REPORT_PHASE1.md
  infra/
    Dockerfile, nginx.conf
  scripts/
    init-env.ps1, verify.ps1
  frontend/
    package.json, package-lock.json, tsconfig.json, vite.config.ts, copy-swagger.mjs
    index.html, public/favicon.svg
    src/main.tsx, src/App.tsx, src/styles.css
  services/
    user_service/                 # loan_service và payment_service có cùng cây con
      .dockerignore, Dockerfile, requirements.txt
      app/
        __init__.py, config.py, database.py, dependencies.py, models.py
        schemas.py, errors.py, main.py
      tests/test_foundation.py
    loan_service/
    payment_service/
  tests/
    test_gateway.py
```

| File | Trách nhiệm |
|---|---|
| `docker-compose.yml`, `.env.example`, `scripts/init-env.ps1` | Khai báo container, mạng, thứ tự khởi động, volume và health; tạo cấu hình local. |
| `infra/Dockerfile`, `infra/nginx.conf` | Build frontend ở stage Node 22, chép static sang Nginx; chọn upstream, chặn internal, thêm request ID. |
| `frontend/src/main.tsx`, `App.tsx`, `styles.css` | Trang chủ/404, native fetch và giao diện hiển thị DB/Swagger. |
| `frontend/package*.json`, `vite.config.ts`, `tsconfig.json`, `copy-swagger.mjs` | Khóa dependency, kiểm tra TypeScript, build Vite/Tailwind và đóng gói Swagger để trình duyệt không cần CDN. |
| `services/*/Dockerfile`, `requirements.txt` | Image độc lập cho từng API; khóa dependency trực tiếp và bắc cầu trên Python 3.13/Linux. |
| `app/config.py`, `database.py`, `models.py`, `dependencies.py` | Đọc env, tạo URL/engine, kiểm tra DB khi khởi động, giữ metadata và cấp session từng request. |
| `app/main.py`, `schemas.py`, `errors.py` | Vòng đời FastAPI, Swagger/health, schema response, lỗi chuẩn và log request ID. |
| `services/*/tests`, `tests/test_gateway.py`, `scripts/verify.ps1` | Kiểm tra từng service với PostgreSQL thật và kiểm tra HTTP qua Gateway. |

Router, hàm nghiệp vụ, seed và reconcile sẽ được thêm ở phase có trách nhiệm tương ứng. Xem Implementation Plan để tra điều kiện nghiệm thu từng phần.
