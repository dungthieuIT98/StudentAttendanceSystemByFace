# Hướng dẫn migration dữ liệu

Tài liệu này mô tả cách khởi tạo database và nạp dữ liệu mẫu để hệ thống chạy được, đặc biệt là tài khoản admin.

## 1) Chuẩn bị

- Bảo đảm PostgreSQL đang chạy nếu bạn dùng Docker.
- Bảo đảm file `.env` hoặc biến môi trường đã trỏ đúng DB.
- Nếu chạy local, hãy dùng đúng virtualenv của dự án.

## 2) Chạy migration schema

Tạo và áp dụng migrations cho toàn bộ model:

```bash
python manage.py makemigrations
python manage.py migrate
```

Nếu dự án đã có sẵn migration thì thường chỉ cần:

```bash
python manage.py migrate
```

## 3) Nạp dữ liệu mẫu

Dữ liệu mẫu nằm trong thư mục `Database/` gồm:

- `Role.json`
- `StaffInfo.json`
- `StaffRole.json`
- `StudentInfo.json`
- `StudentClassDetails.json`
- `Classroom.json`
- `BlogPost.json`

Để nạp toàn bộ dữ liệu và đồng bộ tài khoản admin:

```bash
python manage.py import_legacy_data
```

Command này sẽ:

- import các file JSON vào database
- tạo hoặc cập nhật bản ghi admin
- đảm bảo admin đăng nhập được với:
  - `id_staff=admin`
  - `password=admin123`

## 4) Kiểm tra sau migrate

Kiểm tra nhanh database:

```bash
python manage.py shell
```

Sau đó chạy:

```python
from main.models import StaffInfo, Role, StudentInfo, Classroom

print(StaffInfo.objects.count())
print(Role.objects.count())
print(StudentInfo.objects.count())
print(Classroom.objects.count())
```

Kiểm tra tài khoản admin:

```python
from main.models import StaffInfo
from django.contrib.auth.hashers import check_password

admin = StaffInfo.objects.get(id_staff="admin")
print(check_password("admin123", admin.password))
```

## 5) Đăng nhập

- Trang đăng nhập staff/admin: `/login`
- Trang admin Django: `/admin`

Thông tin admin mặc định:

- Username / ID: `admin`
- Password: `admin123`

## 6) Lưu ý

- `migrate` chỉ tạo cấu trúc bảng, không tự nạp dữ liệu mẫu.
- Nếu muốn reset sạch database, chỉ dùng cách xóa DB/volume khi thật sự cần.
- Các file JSON trong `Database/` là dữ liệu seed, không phải lúc nào cũng là Django fixture chuẩn để `loaddata` trực tiếp.

