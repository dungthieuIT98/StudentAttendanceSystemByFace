## Mô tả dự án

`StudentAttendanceSystemByFace` là hệ thống **điểm danh sinh viên bằng nhận diện khuôn mặt**, xây dựng trên **Django**. Ứng dụng cung cấp giao diện và luồng nghiệp vụ cho 3 nhóm người dùng: **Admin**, **Giảng viên**, **Sinh viên**.

## Tính năng chính

### 1) Xác thực & phân quyền

- **Đăng nhập/đăng xuất theo session**.
- **Phân quyền theo vai trò**:
  - **Admin**: quản trị dữ liệu hệ thống.
  - **Lecturer (Giảng viên)**: quản lý lớp học và điểm danh.
  - **Student (Sinh viên)**: theo dõi lịch học/điểm danh của bản thân.

### 2) Quản lý giảng viên, sinh viên, lớp học

- **Quản lý giảng viên**: thông tin cá nhân, tài khoản, vai trò.
- **Quản lý sinh viên**: thông tin cá nhân, tài khoản, liên kết thư mục ảnh khuôn mặt (phục vụ nhận diện).
- **Quản lý lớp học**:
  - Thông tin lớp (tên lớp, thời gian bắt đầu/kết thúc, thứ trong tuần, giờ học).
  - Gán **giảng viên phụ trách**.
  - Danh sách **sinh viên trong lớp**.

### 3) Điểm danh & lịch sử điểm danh

- Lưu **lần điểm danh** theo sinh viên và lớp học (thời điểm check-in, trạng thái).
- Tra cứu **lịch sử điểm danh** theo vai trò (giảng viên xem theo lớp, sinh viên xem theo cá nhân).
- Một số màn hình có luồng sử dụng **webcam/capture** để phục vụ việc xác minh khuôn mặt khi điểm danh.

### 4) Thông báo/Bài viết (Blog)

- Admin có thể tạo nội dung dạng **Rich Text** (CKEditor).
- Hỗ trợ phân loại đối tượng nhận: **Sinh viên / Giảng viên / Tất cả**.

## Công nghệ & thư viện sử dụng

### Backend

- **Python**
- **Django** (project: `FaceByAttendance`, app: `main`)
- **Django ORM** cho mô hình dữ liệu và truy vấn
- **Session-based authentication** (lưu session như `id_staff`, `staff_role`, `id_student`)

### Frontend

- Template HTML trong `templates/` (theo từng vai trò: `admin/`, `lecturer/`, `student/`)
- Static assets trong `main/static/`:
  - **JavaScript** (quản lý sinh viên/giảng viên/lớp học/thông báo…)
  - **CSS/Bootstrap** và các thư viện UI đi kèm

### Nhận diện khuôn mặt & chống giả mạo

- **FaceNet (TensorFlow)**: mã nguồn trong `main/facenet.py` (triplet loss, embedding, các tiện ích train/eval/load model…).
- **Face detection (OpenCV DNN + Caffe)**: sử dụng model RetinaFace/WiderFace trong `main/resources/detection_model/` (deploy `.prototxt` + `.caffemodel`).
- **Anti-spoof (PyTorch)**:
  - Module dự đoán trong `main/src/anti_spoof_predict.py`
  - Các model MiniFASNet trong `main/src/model_lib/`
  - Mục tiêu: giảm rủi ro **điểm danh bằng ảnh/giả mạo** (tùy vào cách tích hợp ở view).

## Mô hình dữ liệu nổi bật (Django Models)

- **StaffInfo / Role / StaffRole**: nhân sự và phân quyền.
- **StudentInfo**: hồ sơ sinh viên (bao gồm đường dẫn thư mục ảnh).
- **Classroom / StudentClassDetails**: lớp học và danh sách sinh viên theo lớp.
- **Attendance**: bản ghi điểm danh (thời gian, trạng thái, lớp, sinh viên).
- **BlogPost**: thông báo/bài viết (RichText, phân loại đối tượng).

## Cấu trúc thư mục (rút gọn)

- `FaceByAttendance/`: cấu hình project Django (urls, asgi/wsgi…)
- `main/`: app chính (models, views, static, logic nhận diện/anti-spoof…)
- `templates/`: giao diện theo vai trò
- `Database/`: một số dữ liệu mẫu dạng JSON
- `main/resources/`: model phục vụ detection

