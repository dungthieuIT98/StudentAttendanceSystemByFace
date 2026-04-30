# Hướng dẫn chạy dự án

## Yêu cầu hệ thống

| Thành phần | Phiên bản | Ghi chú |
|---|---|---|
| Python | 3.10.x | Virtual env tại `C:\Users\hvhus\.venvs\face-attendance\` |
| Docker Desktop | bất kỳ | Cần chạy để khởi động PostgreSQL |
| PostgreSQL | 16 (qua Docker) | Container `face_attendance_db` |

---

## Cách chạy nhanh (dùng script có sẵn)

Mở PowerShell tại thư mục gốc dự án rồi chạy:

```powershell
.\start.ps1
```

Script sẽ tự động:
1. Set các biến môi trường cần thiết
2. Khởi động Docker container PostgreSQL (`docker compose up -d db`)
3. Chạy Django dev server tại `http://127.0.0.1:8000/`

---

## Cách chạy thủ công (từng bước)

### Bước 1 — Khởi động database (Docker)

```powershell
docker compose up -d db
```

Kiểm tra container đã healthy chưa:

```powershell
docker ps
```

Container `face_attendance_db` phải có trạng thái `healthy`.

### Bước 2 — Set biến môi trường

```powershell
$env:POSTGRES_DB       = 'face_attendance'
$env:POSTGRES_USER     = 'postgres'
$env:POSTGRES_PASSWORD = 'postgres'
$env:POSTGRES_HOST     = '127.0.0.1'
$env:POSTGRES_PORT     = '15432'
$env:DEBUG             = '1'
$env:DJANGO_SECRET_KEY = 'change-me'
$env:DJANGO_ALLOWED_HOSTS = 'localhost,127.0.0.1'
```

Hoặc tạo file `.env` từ mẫu:

```powershell
Copy-Item .env.example .env
```

### Bước 3 — Chạy migration (lần đầu hoặc sau khi thay đổi model)

```powershell
$python = "C:\Users\hvhus\.venvs\face-attendance\Scripts\python.exe"
& $python manage.py makemigrations
& $python manage.py migrate
```

### Bước 4 — Khởi động Django server

```powershell
$python = "C:\Users\hvhus\.venvs\face-attendance\Scripts\python.exe"
& $python manage.py runserver --noreload
```

Server chạy tại: **http://127.0.0.1:8000/**

> Dùng `--noreload` vì dự án dùng TensorFlow/PyTorch — auto-reload có thể gây lỗi khi load model.

#### Dừng server

- Trong cửa sổ PowerShell đang chạy `runserver`: nhấn **Ctrl+C** (hoặc **Ctrl+Break** nếu Django ghi chú như vậy).
- Hoặc tìm PID đang lắng nghe port **8000** rồi kết thúc tiến trình (hữu ích khi không còn cửa sổ đó hoặc server chạy nền):

```powershell
netstat -ano | findstr :8000
taskkill /PID <PID_LẮNG_NGHE_8000> /F
```

(`LISTENING` trong cột cuối là PID cần dùng với `taskkill`.)

#### Chạy lại server

1. Mở PowerShell tại thư mục gốc dự án (hoặc `cd` vào đó).
2. Nếu đây là phiên mới, set lại biến môi trường như **Bước 2** (cùng giá trị như khi chạy lần đầu).
3. Chạy lại lệnh **Bước 4** (khối `$python` + `runserver --noreload` ở trên).

---

## Truy cập ứng dụng

| Vai trò | URL đăng nhập |
|---|---|
| Admin / Giảng viên | http://127.0.0.1:8000/login |
| Sinh viên | http://127.0.0.1:8000/student/login |

Tài khoản mẫu xem tại [`ACCOUNT.md`](./ACCOUNT.md).

---

## Chạy toàn bộ bằng Docker Compose (tùy chọn)

Nếu muốn chạy cả web app trong Docker (không cần venv local):

```powershell
docker compose --profile full up
```

Bật thêm pgAdmin (quản lý DB qua giao diện web tại port 5050):

```powershell
docker compose --profile tools up
```

---

## Kiểm tra trạng thái nhanh

```powershell
# Kiểm tra container DB
docker ps

# Kiểm tra server có phản hồi không
Invoke-WebRequest -Uri "http://127.0.0.1:8000/" -UseBasicParsing | Select-Object StatusCode

# Kiểm tra port 8000 đang được lắng nghe
netstat -ano | findstr :8000
```
