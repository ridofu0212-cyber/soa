# F168 · Báo cáo kiểm thử Phase 1

**Ngày chạy:** 24/11/2026. **Trạng thái Phase 1:** BLOCKED ở gate Docker Compose. **Pytest:** 41 passed trên môi trường chạy native. **Phase 2–7:** NOT STARTED.

## Thiết lập đã dùng

- Đọc Git `main` tại `39a7a61fbdd55670df9dfe47ee5eba1874645b50`; cây ở commit này chỉ có ba tài liệu thiết kế. Đã so khớp bản SPEC trong gói với tệp đính kèm theo byte. Toàn bộ mã Foundation được viết trong thư mục mới. Không có thao tác push.
- Linux x86_64, Python 3.13.5, ba virtualenv riêng cho ba service; cài mỗi bộ `requirements.txt` và chạy `pip check`. FastAPI 0.128.0, SQLAlchemy 2.0.45, psycopg2-binary 2.9.11, Uvicorn 0.40.0, Pytest 9.0.2, HTTPX 0.28.1. Các pin khác nằm trong từng service. Thư viện JWT/Argon2 đã được khóa ở service cần dùng cho phase sau; Phase 1 chỉ kiểm tra cài đặt.
- PostgreSQL 16.11 chạy **ba process/cluster riêng**, có password, kết nối TCP. Từng app có DB `f168_user`, `f168_loan`, `f168_payment`. Đã kiểm tra phiên bản, tên DB và 0 bảng trong schema public sau startup. Cả ba Uvicorn cùng chạy trên cổng 8000, ở các địa chỉ loopback khác nhau.
- Nginx 1.28.0 chạy thật trên cổng 8080. Đã kiểm tra cú pháp chính file `infra/nginx.conf` bàn giao. Khi chạy native, bản cấu hình test thay ba tên upstream Docker bằng địa chỉ loopback, đổi thư mục static/log cho môi trường test. Các location, quy tắc proxy, chặn internal, error page và request ID giữ nguyên.
- Node 22.16.0, npm 10.9.2; React 19.2.4, Vite 7.3.1, Tailwind 4.1.18, TypeScript 5.9.3. Chrome for Testing 158.0.8127.88 để thử trang thật. PowerShell 7.5.2 trên Linux để thử script tạo env. Bộ lái trình duyệt và phần mềm chạy test native chỉ dùng trong môi trường kiểm thử.

## Đối chiếu expected và actual

| Hạng mục | Lệnh hoặc thao tác | Kỳ vọng | Kết quả quan sát |
|---|---|---|---|
| Pin Python | Mỗi service: pip install -r requirements.txt, pip check | Cài được trong Python 3.13, đủ dependency | PASS · 3 virtualenv cài được, cả ba trả No broken requirements found |
| Frontend | npm ci; npm run build | tsc và Vite thành công, có static và Swagger asset | PASS · 41 module build, tạo HTML/CSS/JS và copy bộ Swagger vào dist |
| Env mẫu | Chạy init-env.ps1 trên bản sao sạch rồi chạy lại | 3 mật khẩu, 2 secret độc lập; giữ nguyên file đã có | PASS · 5 giá trị hex khác nhau, Gmail trống. Lần hai từ chối ghi và hash file giữ nguyên |
| Compose | docker compose config -q; kiểm tra mô hình đã resolve | 7 service có healthcheck, 3 mạng DB cô lập, 3 volume, chỉ Gateway publish localhost:8080 | PASS · Compose v2.39.4 chấp nhận; thiếu DB password thì từ chối cấu hình |
| DB và startup | initdb, chạy 3 PostgreSQL và 3 Uvicorn; GET /health | Mỗi app kiểm tra DB riêng và chỉ báo ready sau khi kết nối | PASS · 3 DB đúng tên, PostgreSQL 16.11; 3 endpoint trả 200 |
| Service tests | Từng thư mục service: python -m pytest -q tests | Kiểm DB thật, health, 405 với request ID, lỗi 422/500 được lọc | PASS · User 5/5, Loan 5/5, Payment 5/5 |
| Gateway, Swagger và internal | Từ root: python -m pytest -q tests/test_gateway.py | HTTP tới đúng 3 backend; internal bị chặn trước backend | PASS · 26/26. Có 13 route public/Admin tới đúng owner, 8 tổ hợp method/internal path trả 403, Swagger trỏ đúng schema |
| Correlation | Gửi request có UUID rồi tra access log Nginx và log Loan | Hai dòng có cùng ID | PASS · cùng ID trong hai log |
| Mất DB | Dừng Loan DB, gọi lại 3 health, khởi động lại chính cluster | Loan 503, User/Payment 200, Loan phục hồi 200 | PASS · mã DATABASE_UNAVAILABLE, đúng chuỗi trạng thái |
| Mất API | Dừng tiến trình Loan API, gọi qua Gateway rồi khởi động lại | Gateway trả lỗi chuẩn khi mất upstream | PASS · SERVICE_UNAVAILABLE/503 rồi 200 |
| UI chạy thật | Chrome mở /, bấm Kiểm tra lại, mở Swagger Loan và Execute | 3 dòng sẵn sàng, gọi được /health/loan | PASS · desktop 1280px và mobile 390px không tràn ngang; nút kiểm tra hoạt động; Swagger trên desktop thực sự nhận HTTP 200 từ Loan |
| Build/run bằng Docker | docker compose up --build -d | Build image, chạy 7 container healthy trên mạng Compose | BLOCKED · runtime từ chối kết nối socket Docker Engine trước khi build |
| Docker network, health policy, restart và named volume | Hạ/dựng lại chính Compose project | Host chỉ vào Gateway, service discovery đúng, cluster ID còn nguyên | BLOCKED · cần Docker Engine; đã có lệnh kiểm tra trên Windows trong README |

Trích kết quả Pytest của một lượt chạy đồng bộ ba DB, ba API và Gateway:

```text
user_service/tests       5 passed in 0.82s
loan_service/tests       5 passed in 0.54s
payment_service/tests    5 passed in 0.54s
tests/test_gateway.py   26 passed in 0.18s
```

Các ca 422/500 dùng ứng dụng FastAPI dành riêng cho test để tạo lỗi có kiểm soát; production không có endpoint gây lỗi thử. Health, route, 503/mất DB và request qua Nginx đã chạy với PostgreSQL thật. Các response 404 từ nhóm route nghiệp vụ là kết quả dự kiến của skeleton ở Phase 1.

**Kiểm tra gói bàn giao.** Đã giải nén ZIP vào thư mục sạch, cài lại npm bằng package-lock, build lại frontend và chạy lại 41 test trên source giải nén. Cả 41 đạt. Chrome ở 1280px/390px, Swagger Execute, 503 và phục hồi DB/API cũng đạt ở lượt này.

## Tái lập trên máy nhóm và chốt gate

1. Giải nén, tạo env, đặt project name test, build và chờ healthy theo [README](../README.md#chạy-lần-đầu-trên-windows). Ghi phiên bản Docker Desktop/Compose, output của `docker compose ps` và thời điểm.
2. Chạy `scripts/verify.ps1`, giữ tổng 5 + 5 + 5 + 26. Ghi một response 200 từ health, một 403 từ internal (không có X-Service-Name) và cùng request ID tại hai log.
3. Mở trang trạng thái, thử **Execute** từ Swagger của từng service. Chỉ Gateway publish cổng host; DB và API không có port mapping. Thử stop/start DB và kiểm cluster ID trước/sau `down` + `up` theo README.
4. Nếu lệnh lỗi, ghi đúng lệnh, service, status và đoạn log đã che bí mật. Nếu tất cả đạt, cập nhật báo cáo với bằng chứng Docker. Nhóm xác nhận trước Phase 2.

Docker Desktop trên Windows, container image build và việc giữ named volume qua recreate là các phần còn cần xác minh. Chạy `init-env.ps1` trên PowerShell/Linux chỉ xác nhận logic sinh file; script orchestration `verify.ps1` chờ Docker để kiểm chứng trọn luồng. Gmail, JWT nghiệp vụ, thanh toán và concurrency C1–C5 là gate các phase sau.
