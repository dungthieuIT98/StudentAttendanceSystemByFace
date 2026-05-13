## Công nghệ sử dụng

### Backend (Web)

- **Python + Django**
  - Project: `FaceByAttendance/`
  - App chính: `main/`
- **Django ORM**: thao tác dữ liệu qua `main/models.py`
- **Session**: lưu trạng thái đăng nhập và vai trò (ví dụ `id_staff`, `staff_role`, `id_student`)

### Frontend (UI)

- **Django Templates**: giao diện theo vai trò trong `templates/admin/`, `templates/lecturer/`, `templates/student/`
- **Static assets**: `main/static/` (JS/CSS + các thư viện UI)

### AI/Computer Vision (điểm danh bằng khuôn mặt)

- **FaceNet (TensorFlow)**: mã nguồn và các tiện ích train/eval/load model trong `main/facenet.py`
- **Face detection (OpenCV DNN + Caffe)**:
  - Model: `main/resources/detection_model/deploy.prototxt`
  - Weight: `main/resources/detection_model/Widerface-RetinaFace.caffemodel`
- **Anti-spoof (PyTorch)**:
  - Inference: `main/src/anti_spoof_predict.py`
  - Model zoo: `main/src/model_lib/` (MiniFASNet variants)

### Nội dung (CMS đơn giản)

- **CKEditor**: dùng trường Rich Text `RichTextUploadingField` trong model `BlogPost`

## Kiến trúc tổng quan

Dự án có kiến trúc kiểu **monolith Django**:

- **Routing layer**: `FaceByAttendance/urls.py` include sang `main.urls`
- **Controller layer (Views)**:
  - `main/views.py`: các view chung (home, login, logout…)
  - `main/view/*.py`: nhóm view theo vai trò (admin/lecturer/student)
- **Domain/Data layer (Models)**: `main/models.py`
- **Presentation layer**:
  - Template HTML: `templates/**`
  - Static JS/CSS: `main/static/**`

## Luồng request tiêu biểu

### 1) Đăng nhập và điều hướng theo vai trò

- Người dùng gửi form đăng nhập
- Server kiểm tra mật khẩu (hash) và lấy danh sách role
- Lưu session:
  - Staff: `id_staff`, `staff_role` (list role)
  - Student: `id_student` (nếu có luồng login riêng cho sinh viên)
- Redirect về dashboard theo role (Admin/Lecturer/Student)

### 2) Quản lý lớp học và danh sách sinh viên

- Admin/Giảng viên thao tác CRUD lớp học và danh sách sinh viên trong lớp
- Quan hệ dữ liệu chính:
  - `Classroom` ↔ `StudentInfo` (many-to-many qua `StudentClassDetails`)
  - `Classroom` → `StaffInfo` (giảng viên phụ trách)

### 3) Điểm danh bằng webcam/capture (khái niệm kiến trúc)

Ở mức kiến trúc, luồng điểm danh thường gồm:

- **Capture ảnh/video frame** từ webcam (UI ở template + JS)
- **Face detection** để lấy bounding box khuôn mặt
- (Tuỳ tích hợp) **Anti-spoof** để đánh giá “real/fake”
- **Face recognition** (FaceNet embedding + so khớp) để xác định sinh viên
- Ghi bản ghi `Attendance` (thời điểm check-in, trạng thái, lớp, sinh viên)

### 4) Luồng điểm danh khuôn mặt hiện tại

Luồng đang được giữ khá phẳng để dễ đọc:

- Stream MJPEG ở `main/view/reg.py`
- Sau khi nhận diện thành công, backend ghi DB và đẩy một bản ghi pending vào cache
- View `lecturer_live_attendance_today` trả về danh sách đã ghi theo dạng phẳng
- Template `lecturer_mask_attendance_by_face.html` poll API này và hiển thị ngay tên sinh viên mới nhất

Điểm chính của refactor là:

- Dùng helper nhỏ thay vì nhiều nhánh `if/else`
- Tách rõ phần load model, phần ghi attendance, phần render UI
- Giữ dữ liệu trả về cho UI ở dạng đơn giản: `student_id`, `student_name`, `check_in_time`, `attendance_status`

Lưu ý: phần nhận diện/anti-spoof trong repo đang tồn tại dưới dạng module (TensorFlow/PyTorch/OpenCV). Mức độ “gắn” trực tiếp vào view nào sẽ phụ thuộc vào các view trong `main/view/` và các trang `templates/**` (webcam/capture).

## Lưu trữ dữ liệu

- **Database qua Django ORM**: các bảng chính gồm `StaffInfo`, `StudentInfo`, `Classroom`, `Attendance`, `BlogPost`…
- `Database/*.json`: dữ liệu mẫu/seed (phục vụ demo hoặc khởi tạo nhanh)
- `StudentInfo.PathImageFolder`: đường dẫn thư mục ảnh khuôn mặt (dùng cho nhận diện)

## Tổ chức mã nguồn theo module

- `FaceByAttendance/`: entrypoint web (urls, asgi/wsgi)
- `main/`:
  - `models.py`: domain models
  - `views.py` + `view/*.py`: controllers theo vai trò
  - `static/` + `templates/`: UI
  - `facenet.py`: core FaceNet utilities
  - `src/`: anti-spoof + các util/model liên quan
  - `resources/`: model phục vụ detection

