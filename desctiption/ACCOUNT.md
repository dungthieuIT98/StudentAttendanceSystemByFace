# Tài khoản hệ thống (từ DB Docker)

Nguồn dữ liệu: Postgres trong Docker container `face_attendance_db` (DB `face_attendance`).

## Staff (Admin / Lecturer)

| Role | ID đăng nhập | Mật khẩu | Tên | Email |
|---|---|---|---|---|
| Admin | `ADMIN001` | `admin123` | Quan Tri Vien | admin@school.edu.vn |
| Lecturer | `GV001` | `GV001@2026` | Nguyen Van A | gv001@school.edu.vn |

## Student

| Role | ID đăng nhập | Mật khẩu | Tên | Email |
|---|---|---|---|---|
| Student | `02` | `02` | Nguyen Minh An | hvhust1998@gmail.com |
| Student | `SV001` | `SV001@2026` | Tran Thi B | sv001@student.edu.vn |

---

## Hướng dẫn đăng nhập

- **Giảng viên / Admin:** `/login`
- **Sinh viên:** `/student/login`
