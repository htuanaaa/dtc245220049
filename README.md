# Hướng Dẫn Triển Khai Hệ Thống

Tài liệu hướng dẫn triển khai và quản lý dịch vụ Chat WebSocket cùng hệ thống giám sát bằng Docker Compose.

---

## 1. Clone Dự Án

Tải mã nguồn dự án từ GitHub về máy và chuyển vào thư mục làm việc:

```bash
git clone https://github.com/htuanaaa/dtc245220049.git
cd dtc245220049/
```

---

## 2. Chuẩn Bị Môi Trường

Sao chép file cấu hình mẫu `.env.exp` thành `.env` và chỉnh sửa lại các thông số cần thiết:

```bash
cp .env.exp .env
```

---

## 3. Tạo Chứng Chỉ SSL Tự Ký

Vào thư mục `ssl/` và khởi tạo chứng chỉ tự ký (Self-signed Certificate) để Nginx hỗ trợ HTTPS/WSS:

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ssl/nginx.key \
    -out ssl/nginx.crt \
    -subj "/C=VN/ST=Local/L=Local/O=Dev/CN=localhost"
```

---

## 4. Khởi Chạy Hệ Thống

Chạy lệnh sau tại thư mục gốc để khởi tạo mạng ảo, tạo volume và chạy ngầm toàn bộ các dịch vụ:

```bash
docker compose up -d
```

---

## 5. Kiểm Tra Trạng Thái

Kiểm tra danh sách và trạng thái hoạt động của các container:

```bash
docker compose ps
```

---

## 6. Danh Sách Cổng Truy Cập

Toàn bộ các cổng quản trị đều được cấu hình an toàn trên máy chủ (`127.0.0.1`):

* **Ứng Dụng Web Chat:** `http://localhost` (Public Port 80 / 443)
* **Grafana Dashboard:** `http://127.0.0.1:3000` (Localhost only)
* **PgAdmin Dashboard:** `http://127.0.0.1:8081` (Localhost only)


---

## 7. Dừng Hệ Thống

Khi không chạy nữa, dừng và gỡ bỏ toàn bộ container cùng mạng ảo (dữ liệu trên volume vẫn được bảo toàn):

```bash
docker compose down
```