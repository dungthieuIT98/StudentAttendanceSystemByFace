# 🔐 THÔNG TIN ĐĂNG NHẬP

## 📚 Student Attendance System (Hệ thống điểm danh)

### 🌐 Truy cập hệ thống
- **URL chính**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin

### 👤 Tài khoản Admin
```
Username: admin
Password: admin123
```

⚠️ **QUAN TRỌNG**: 
- Đổi mật khẩu ngay sau khi đăng nhập lần đầu!
- Tài khoản này có quyền superuser, truy cập toàn bộ hệ thống

---

## 🗄️ PostgreSQL Database

### Kết nối từ bên ngoài
```
Host: localhost
Port: 5432
Database: face_attendance
Username: postgres
Password: postgres
```

### Kết nối từ pgAdmin hoặc DBeaver
```
Connection Type: PostgreSQL
Host: localhost
Port: 5432
Database: face_attendance
Username: postgres
Password: postgres
SSL Mode: disable
```

---

## 🛠️ pgAdmin (Optional)

### Khởi động pgAdmin
```bash
docker-compose --profile tools up -d
```

### Truy cập pgAdmin
- **URL**: http://localhost:5050
- **Email**: admin@example.com
- **Password**: admin

### Kết nối database trong pgAdmin
Sau khi đăng nhập pgAdmin, tạo server mới:
```
General:
  Name: Face Attendance DB

Connection:
  Host: db
  Port: 5432
  Database: face_attendance
  Username: postgres
  Password: postgres
```

---

## 📊 Metabase (Nếu có)

Dựa trên logs, bạn có Metabase container đã dừng:

### Khởi động Metabase
```bash
docker start mb-app mb-postgres
```

### Truy cập Metabase
- **URL**: http://localhost:3000 (hoặc port mặc định)
- **Tài khoản**: Tùy thuộc vào cấu hình khi setup lần đầu

### Kết nối Metabase với Face Attendance Database
Trong Metabase Admin Settings > Databases > Add Database:
```
Database Type: PostgreSQL
Name: Face Attendance
Host: host.docker.internal
Port: 5432
Database: face_attendance
Username: postgres
Password: postgres
```

---

## 🚀 Quick Commands

### Tạo tài khoản admin mới
```bash
docker-compose exec web python manage.py createsuperuser
```

### Thay đổi mật khẩu admin
```bash
docker-compose exec web python manage.py changepassword admin
```

### Xem logs
```bash
docker-compose logs -f web
```

### Restart services
```bash
docker-compose restart
```

---

## 📝 Ghi chú

- Database đã có sẵn:
  - 7 classrooms
  - 1 student
  - 4 attendance records
  
- Tất cả dữ liệu được lưu trong Docker volumes, không bị mất khi restart

- Để backup database:
  ```bash
  docker-compose exec db pg_dump -U postgres face_attendance > backup.sql
  ```

---

**📞 Cần hỗ trợ?** 
- Xem logs: `docker-compose logs -f`
- Check status: `docker-compose ps`
- Restart: `docker-compose restart`
