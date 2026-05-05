# 🚀 Hướng dẫn nhanh Docker

## Khởi động

```bash
docker-compose up -d
```

Truy cập: **http://localhost:8000**

## Đăng nhập

### Tài khoản Admin
- **URL**: http://localhost:8000/admin
- **Username**: `admin`
- **Password**: `admin123`

⚠️ **LƯU Ý**: Đổi mật khẩu ngay sau khi đăng nhập lần đầu!

## Lệnh thường dùng

```bash
# Khởi động
docker-compose up -d

# Dừng
docker-compose down

# Xem logs
docker-compose logs -f web

# Xem status
docker-compose ps

# Tạo superuser mới
docker-compose exec web python manage.py createsuperuser

# Backup database
docker-compose exec db pg_dump -U postgres face_attendance > backup.sql
```

## Xử lý sự cố

### Build lại từ đầu
```bash
docker-compose down
docker-compose build
docker-compose up -d
```

### Reset toàn bộ (XÓA DỮ LIỆU!)
```bash
docker-compose down -v
docker-compose up -d
```

## Cấu trúc

- **db**: PostgreSQL database (port 5432)
- **web**: Django app + Gunicorn (port 8000)
- **pgadmin**: Database tool (port 5050, optional)

## pgAdmin (Optional)

```bash
docker-compose --profile tools up -d
```

- **URL**: http://localhost:5050
- **Email**: admin@example.com
- **Password**: admin

---

**Thắc mắc?** Chạy `docker-compose logs -f` để xem logs chi tiết.
