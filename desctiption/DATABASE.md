## Các bảng trong Database (theo Django Models)

Trong dự án này, các bảng được sinh tự động từ `main/models.py` thông qua Django ORM + migrations (`main/migrations/0001_initial.py`).

### Nhóm tài khoản & phân quyền

- **`main_staffinfo`** (`StaffInfo`)
  - `id_staff` (PK)
  - `staff_name`, `email`, `phone`, `address`, `birthday`, `password`
- **`main_role`** (`Role`)
  - `id` (PK)
  - `name` (unique) — ví dụ: `Admin`, `Lecturer`
- **`main_staffrole`** (`StaffRole`) — bảng trung gian nhiều-nhiều
  - `id` (PK)
  - `staff_id` (FK → `main_staffinfo.id_staff`)
  - `role_id` (FK → `main_role.id`)

### Nhóm sinh viên & lớp học

- **`main_studentinfo`** (`StudentInfo`)
  - `id_student` (PK)
  - `student_name`, `email`, `phone`, `address`, `birthday`, `password`
  - `PathImageFolder` — đường dẫn thư mục ảnh khuôn mặt của sinh viên
- **`main_classroom`** (`Classroom`)
  - `id_classroom` (PK)
  - `name`, `begin_date`, `end_date`, `day_of_week_begin`, `begin_time`, `end_time`
  - `id_lecturer_id` (FK → `main_staffinfo.id_staff`, có thể null)
- **`main_studentclassdetails`** (`StudentClassDetails`) — bảng trung gian nhiều-nhiều
  - `id` (PK)
  - `id_classroom_id` (FK → `main_classroom.id_classroom`)
  - `id_student_id` (FK → `main_studentinfo.id_student`)

### Nhóm điểm danh

- **`main_attendance`** (`Attendance`)
  - `id_attendance` (PK)
  - `check_in_time` (datetime)
  - `attendance_status` (int)
  - `id_classroom_id` (FK → `main_classroom.id_classroom`, có thể null)
  - `id_student_id` (FK → `main_studentinfo.id_student`)

### Nhóm thông báo/bài viết

- **`main_blogpost`** (`BlogPost`)
  - `id` (PK, auto)
  - `title`
  - `body` (RichText / CKEditor)
  - `type` (`SV`/`GV`/`ALL`)

## Quan hệ (ERD dạng chữ)

- `StaffInfo` ⟷ `Role` (N-N) qua `StaffRole`
- `Classroom` → `StaffInfo` (N-1) qua `id_lecturer`
- `Classroom` ⟷ `StudentInfo` (N-N) qua `StudentClassDetails`
- `Attendance` → `Classroom` (N-1)
- `Attendance` → `StudentInfo` (N-1)

## Làm sao để “kết nối” database?

### 1) Cấu hình kết nối trong Django (`DATABASES`)

Thông thường, cấu hình DB nằm trong **`FaceByAttendance/settings.py`** ở biến `DATABASES`.

Lưu ý: trong workspace hiện tại **chưa thấy file `FaceByAttendance/settings.py`**, nhưng `manage.py` đang trỏ tới `FaceByAttendance.settings`. Vì vậy bạn cần:

- **Có/khôi phục** file `FaceByAttendance/settings.py` (từ bản gốc dự án), hoặc
- **Tạo mới** settings Django (nếu bạn muốn mình tạo giúp, mình làm được), rồi cấu hình `DATABASES`.

### 2) Chọn DB và cấu hình ví dụ

#### a) SQLite (dễ nhất cho local/dev)

Trong `DATABASES`:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
```

#### b) PostgreSQL

- Cài driver:

```bash
pip install psycopg2-binary
```

- Cấu hình:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "attendance_db",
        "USER": "postgres",
        "PASSWORD": "your_password",
        "HOST": "127.0.0.1",
        "PORT": "5432",
    }
}
```

#### c) MySQL/MariaDB

- Cài driver:

```bash
pip install mysqlclient
```

- Cấu hình:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "attendance_db",
        "USER": "root",
        "PASSWORD": "your_password",
        "HOST": "127.0.0.1",
        "PORT": "3306",
        "OPTIONS": {"charset": "utf8mb4"},
    }
}
```

### 3) Tạo bảng (migrate)

Sau khi cấu hình `DATABASES`, chạy:

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4) Nạp dữ liệu mẫu (nếu cần)

Thư mục `Database/` có các file JSON như `StudentInfo.json`, `Classroom.json`… Đây **không chắc** là Django fixture chuẩn để dùng trực tiếp `loaddata`.

- Nếu JSON đang đúng định dạng fixture Django, bạn có thể thử:

```bash
python manage.py loaddata Database/StudentInfo.json
```

- Nếu không đúng fixture, cách phù hợp là viết **script import** (đọc JSON và tạo record qua ORM).

