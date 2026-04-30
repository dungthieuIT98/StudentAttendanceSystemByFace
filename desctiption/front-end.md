# Tài liệu Front-End - Hệ thống Quản lý Điểm danh bằng Khuôn mặt (Pseudo-SPA Refactored)

**Major Update (Apr 2026)**: Converted multi-page dashboards to pseudo-SPA using AJAX navigation. 
- **Fixed**: Sidebar and topbar
- **Dynamic**: Only `#main-content` updates via `fetch()` + `X-Requested-With: XMLHttpRequest`
- **History**: `pushState` + `popstate` support
- **Base Templates**: Conditional rendering (`if request.META.get('HTTP_X_REQUESTED_WITH')...`) outputs only content block for AJAX (preserves all DTL, no layout duplication, no backend URL changes)
- JS is self-contained in bases with loading spinner, active nav, re-init hooks via `spa:content-loaded` event.
- Compatible with Bootstrap 5, existing views, modals, face recognition pages.

---

## Mục lục

> Tất cả file giao diện được lưu trong thư mục `templates/` và sử dụng Django Template Language (DTL).  
> Cấu trúc phân theo 3 nhóm: **Chung**, **Admin**, **Giảng viên**, **Sinh viên**.

---

## Mục lục

1. [Trang chung (Dùng chung)](#1-trang-chung)
2. [Admin - Layout & Dashboard](#2-admin---layout--dashboard)
3. [Admin - Quản lý Giảng viên](#3-admin---quản-lý-giảng-viên)
4. [Admin - Quản lý Sinh viên](#4-admin---quản-lý-sinh-viên)
5. [Admin - Quản lý Thời khóa biểu](#5-admin---quản-lý-thời-khóa-biểu)
6. [Admin - Quản lý Thông báo](#6-admin---quản-lý-thông-báo)
7. [Admin - Quản lý Lớp học](#7-admin---quản-lý-lớp-học)
8. [Admin - Hồ sơ & Tài khoản](#8-admin---hồ-sơ--tài-khoản)
9. [Admin - Webcam & Chụp ảnh](#9-admin---webcam--chụp-ảnh)
10. [Admin - Modal Popup](#10-admin---modal-popup)
11. [Giảng viên - Layout & Dashboard](#11-giảng-viên---layout--dashboard)
12. [Giảng viên - Điểm danh](#12-giảng-viên---điểm-danh)
13. [Giảng viên - Lịch & Lớp học](#13-giảng-viên---lịch--lớp-học)
14. [Giảng viên - Hồ sơ & Tài khoản](#14-giảng-viên---hồ-sơ--tài-khoản)
15. [Sinh viên - Layout & Dashboard](#15-sinh-viên---layout--dashboard)
16. [Sinh viên - Lịch & Điểm danh](#16-sinh-viên---lịch--điểm-danh)
17. [Sinh viên - Hồ sơ & Tài khoản](#17-sinh-viên---hồ-sơ--tài-khoản)
18. [Trang lỗi](#18-trang-lỗi)

---

## 1. Trang chung

### `templates/choose_login.html`
**Mô tả:** Trang chọn đối tượng đăng nhập khi truy cập vào hệ thống.

**Chức năng:**
- Hiển thị logo HUTECH và tên hệ thống
- Nút chọn đăng nhập **Giảng viên / Viên chức** → điều hướng đến `login`
- Nút chọn đăng nhập **Sinh viên** → điều hướng đến `student_login`
- Hiệu ứng hover `animation-zoom` trên các lựa chọn

---

### `templates/login.html`
**Mô tả:** Trang đăng nhập dành cho **Giảng viên và Admin**.

**Chức năng:**
- Form đăng nhập với 2 trường: `Mã giảng viên` và `Mật khẩu`
- Gửi form POST với CSRF token
- Hiển thị thông báo lỗi nếu đăng nhập thất bại (`error_message`)
- Nút submit `Đăng nhập`

---

### `templates/student/student_login.html`
**Mô tả:** Trang đăng nhập dành riêng cho **Sinh viên**.

**Chức năng:**
- Form đăng nhập với 2 trường: `Mã số sinh viên` và `Mật khẩu`
- Gửi form POST với CSRF token
- Hiển thị thông báo lỗi nếu đăng nhập thất bại
- Nút submit `Đăng nhập`

---

### `templates/hash_password.html`
**Mô tả:** Trang tiện ích dành cho developer để hash mật khẩu.

---

## 2. Admin - Layout & Dashboard

### `templates/admin/base_admin_dashboard.html`
**Mô tả:** Template layout chung cho toàn bộ trang Admin — mọi trang Admin đều `extends` file này.

**Chức năng:**
- **Topbar (Header):** Logo hệ thống, toggle sidebar, dropdown menu người dùng
- **Dropdown người dùng:** Quản lý hồ sơ, Đổi mật khẩu, Đăng xuất
- **Sidebar (Menu trái):**
  - Trang chủ (`admin_dashboard`)
  - Quản lý > Giảng viên (`admin_lecturer_management`)
  - Quản lý > Sinh viên (`admin_student_management`)
  - Quản lý > Thời khóa biểu (`admin_schedule_management`)
  - Quản lý > Thông báo (`admin_notification_view`)
  - Quản lý > Quản lý lớp học (`admin_list_classroom_student`)
- **Block `content`:** Vùng nội dung chính (được override bởi các trang con)
- **Block `js`:** Vùng nhúng JavaScript riêng từng trang
- Footer hiển thị thông tin hệ thống
- Nhúng các thư viện: Bootstrap 5.3.3, jQuery, Perfect Scrollbar, SweetAlert2, Bootstrap Datepicker

---

### `templates/admin/admin_home.html`
**Mô tả:** Trang chủ dashboard Admin.

**Chức năng:**
- Hiển thị danh sách các bài **Thông báo** (blog posts) được admin đăng
- Render nội dung HTML an toàn của từng thông báo (`body|safe`)
- Hiển thị tiêu đề và nội dung từng thông báo

---

## 3. Admin - Quản lý Giảng viên

### `templates/admin/admin_lecturer_management.html`
**Mô tả:** Trang quản lý danh sách giảng viên.

**Chức năng:**
- Bảng danh sách giảng viên: Mã GV, Họ tên, Email, SĐT, Địa chỉ, Ngày sinh
- Nút **Thêm giảng viên** → redirect đến form thêm mới
- Ô **Tìm kiếm** giảng viên
- Nút **Xóa** từng giảng viên → gọi `confirmDeleteLecturer(id)` → hiện modal xác nhận
- Nút **Sửa** từng giảng viên → gọi `editLecturer(id)`:
  - AJAX GET lấy thông tin giảng viên theo ID
  - Điền dữ liệu vào form modal chỉnh sửa
  - Hiện modal `editLecturerModal`
- **Phân trang:** Điều hướng trang trước/sau, hiển thị số trang hiện tại
- Include modal: `popup_add_lecturer`, `popup_edit_lecturer`, `popup_delete_lecturer`

---

## 4. Admin - Quản lý Sinh viên

### `templates/admin/admin_student_management.html`
**Mô tả:** Trang quản lý danh sách sinh viên.

**Chức năng:**
- Bảng danh sách sinh viên: MSSV, Họ tên, Email, SĐT, Địa chỉ, Ngày sinh, Đường dẫn ảnh
- Nút **Thêm sinh viên** → mở modal thêm mới kèm live video feed từ webcam:
  - Validate form trước khi mở webcam
  - Bật stream video: `GET /admin/student-management/live_video_feed/{id}`
  - Polling mỗi 1 giây kiểm tra trạng thái chụp: `GET /admin/student-management/check_capture_status/`
  - Tự động submit form khi chụp thành công
  - Tự động cập nhật `PathImageFolder` khi nhập MSSV
- Nút **Train** → gọi `GET /admin/student-management/train`:
  - Hiện SweetAlert2 loading trong 20 giây
  - Hiện thông báo thành công/thất bại sau khi hoàn thành
  - Tự động reload trang sau 2 giây
- Nút **Chụp hình** từng sinh viên → gọi `capture(id)`:
  - AJAX GET lấy thông tin sinh viên
  - Mở live video stream webcam cho sinh viên đó
  - Polling trạng thái chụp và tự động submit form
- Nút **Xóa** → gọi `confirmDeleteStudent(id)` → modal xác nhận xóa
- Nút **Sửa** → gọi `editStudent(id)`:
  - AJAX GET lấy thông tin sinh viên
  - Điền vào modal chỉnh sửa
- **Phân trang:** Điều hướng trang trước/sau
- Include modal: `popup_add_student`, `popup_edit_student`, `popup_delete_student`, `popup_capture_student`

---

## 5. Admin - Quản lý Thời khóa biểu

### `templates/admin/admin_schedule_management.html`
**Mô tả:** Trang quản lý thời khóa biểu toàn trường.

**Chức năng:**
- Bảng danh sách lịch học: Mã môn học, Tên môn, Ngày bắt đầu/kết thúc, Thứ trong tuần, Tiết bắt đầu/kết thúc, Giảng viên phụ trách
- Hiển thị tên thứ tiếng Việt (Thứ Hai → Chủ Nhật) theo giá trị số
- Nút **Thêm thời khóa biểu** → redirect đến form thêm mới
- Nút **Xóa** → gọi `confirmDeleteClassroom(id)` → modal xác nhận
- Nút **Sửa** → gọi `editSchedule(id)`:
  - AJAX GET lấy thông tin lịch học theo ID
  - Điền vào modal chỉnh sửa
  - Hiện modal `editScheduleModal`
- **Phân trang:** Điều hướng trang trước/sau
- Include modal: `popup_add_schedule`, `popup_edit_schedule`, `popup_delete_schedule`

---

## 6. Admin - Quản lý Thông báo

### `templates/admin/admin_notification_management.html`
**Mô tả:** Trang quản lý danh sách thông báo/bài đăng.

**Chức năng:**
- Bảng danh sách thông báo: Mã TB, Tiêu đề, Nội dung, Loại thông báo
- Nút **Thêm thông báo** → mở modal `popup_add_notification`
- Nút **Xóa** từng thông báo → gọi `confirmDeleteNotification(id)` → modal xác nhận
- Nút **Sửa** → redirect đến trang chỉnh sửa thông báo (`edit_blog`)
- Include modal: `popup_add_notification`, `popup_delete_notification`

---

### `templates/admin/admin_create_blog.html`
**Mô tả:** Trang tạo bài thông báo mới với trình soạn thảo CKEditor.

**Chức năng:**
- Form tạo thông báo mới với CKEditor rich text editor (từ Django form)
- Hiển thị flash messages (thành công/thất bại)
- Nút submit `Create`
- Hỗ trợ upload file/media qua `enctype="multipart/form-data"`

---

### `templates/admin/admin_edit_notification.html`
**Mô tả:** Trang chỉnh sửa thông báo đã tồn tại.

**Chức năng:**
- Form chỉnh sửa thông báo với CKEditor rich text editor
- Khởi tạo CKEditor với nội dung hiện tại của bài đăng (`initialData`)
- Nút submit `Cập nhật`
- Hỗ trợ upload file/media

---

## 7. Admin - Quản lý Lớp học

### `templates/admin/admin_list_classroom_student_management.html`
**Mô tả:** Trang xem toàn bộ danh sách lớp học trong hệ thống.

**Chức năng:**
- Form tìm kiếm lớp học theo mã hoặc tên lớp (`GET ?q=...`)
- Bảng danh sách lớp: Thứ, Môn học, Giảng viên, Ngày bắt đầu/kết thúc, Giờ học, Số sinh viên
- Nút **Xem danh sách** → redirect đến trang quản lý sinh viên của lớp đó
- **Phân trang:** Điều hướng trang trước/sau

---

### `templates/admin/admin_list_student_classroom_management.html`
**Mô tả:** Trang quản lý sinh viên trong một lớp học cụ thể.

**Chức năng:**
- Bảng danh sách sinh viên trong lớp: MSSV, Họ tên, Email, SĐT, Địa chỉ, Ngày sinh, Đường dẫn ảnh
- Nút **Xóa tất cả sinh viên** → gọi `confirmDeleteAllStudentInClass(classId)` → modal xác nhận
- Nút **Thêm sinh viên** (từng người) → redirect form thêm
- Nút **Thêm danh sách sinh viên** (import file) → redirect form upload:
  - Hàm `addStudents()` validate file được chọn
- Nút **Xóa** từng sinh viên → gọi `confirmDeleteStudentInClass(studentId, classroomId)`
- **Phân trang:** Điều hướng trang trước/sau
- Include modal: `popup_delete_student_in_class`, `popup_delete_all_student_in_class`, `popup_add_student_in_class`, `popup_add_list_students_in_class`

---

## 8. Admin - Hồ sơ & Tài khoản

### `templates/admin/admin_profile.html`
**Mô tả:** Trang xem và chỉnh sửa hồ sơ cá nhân Admin.

**Chức năng:**
- Hiển thị thông tin: Mã nhân viên (chỉ đọc), Họ tên, Email, SĐT, Ngày sinh (datepicker), Địa chỉ
- Form POST cập nhật thông tin cá nhân
- Hiển thị thông báo thành công sau khi cập nhật
- Tích hợp Bootstrap Datepicker cho trường ngày sinh

---

### `templates/admin/admin_change_password.html`
**Mô tả:** Trang đổi mật khẩu cho Admin.

**Chức năng:**
- Form đổi mật khẩu với 3 trường: Mật khẩu hiện tại, Mật khẩu mới, Nhập lại mật khẩu mới
- Tất cả trường bắt buộc (`required`)
- Hiển thị thông báo thành công (màu xanh) hoặc thất bại (màu đỏ) sau khi xử lý

---

## 9. Admin - Webcam & Chụp ảnh

### `templates/admin/webcam.html`
**Mô tả:** Trang thử nghiệm stream webcam (standalone, không dùng base template).

**Chức năng:**
- Nút **Start**: gửi POST `action=start` đến `/admin/webcam` → nhận ảnh base64 và hiển thị
- Nút **Stop**: gửi POST `action=stop` để dừng webcam
- Hiển thị ảnh webcam realtime bằng thẻ `<img>`
- CSRF token xử lý thủ công

---

### `templates/admin/capture.html`
**Mô tả:** Trang thử nghiệm chụp ảnh từ webcam (standalone).

**Chức năng:**
- Nút **Capture**: gọi `GET /admin/capture/`
- Hiển thị ảnh vừa chụp dưới dạng base64
- Hiển thị thông báo lỗi nếu chụp thất bại

---

## 10. Admin - Modal Popup

Các file popup được `{% include %}` vào các trang quản lý, không hiển thị độc lập.

| File | Chức năng |
|------|-----------|
| `popup_add_lecturer.html` | Form thêm giảng viên mới (họ tên, email, SĐT, địa chỉ, ngày sinh) |
| `popup_edit_lecturer.html` | Form chỉnh sửa thông tin giảng viên (điền sẵn dữ liệu qua AJAX) |
| `popup_delete_lecturer.html` | Hộp thoại xác nhận xóa giảng viên |
| `popup_add_student.html` | Form thêm sinh viên mới kèm live video feed chụp khuôn mặt |
| `popup_edit_student.html` | Form chỉnh sửa thông tin sinh viên (điền sẵn qua AJAX) |
| `popup_delete_student.html` | Hộp thoại xác nhận xóa sinh viên |
| `popup_capture_student.html` | Modal hiển thị live video feed để chụp ảnh khuôn mặt sinh viên đã có |
| `popup_add_schedule.html` | Form thêm lịch học mới (tên môn, ngày, thứ, tiết, giảng viên) |
| `popup_edit_schedule.html` | Form chỉnh sửa lịch học (điền sẵn qua AJAX) |
| `popup_delete_schedule.html` | Hộp thoại xác nhận xóa lịch học |
| `popup_add_notification.html` | Form thêm thông báo mới |
| `popup_delete_notification.html` | Hộp thoại xác nhận xóa thông báo |
| `popup_add_student_in_class.html` | Form thêm một sinh viên vào lớp học |
| `popup_add_list_students_in_class.html` | Form upload file danh sách sinh viên vào lớp |
| `popup_delete_student_in_class.html` | Hộp thoại xác nhận xóa một sinh viên khỏi lớp |
| `popup_delete_all_student_in_class.html` | Hộp thoại xác nhận xóa toàn bộ sinh viên khỏi lớp |

---

## 11. Giảng viên - Layout & Dashboard

### `templates/lecturer/base_lecturer_dashboard.html`
**Mô tả:** Template layout chung cho toàn bộ trang Giảng viên.

**Chức năng:**
- **Topbar:** Logo hệ thống, toggle sidebar, dropdown người dùng
- **Dropdown người dùng:** Quản lý hồ sơ, Đổi mật khẩu, Đăng xuất
- **Sidebar (Menu trái):**
  - Trang chủ (`lecturer_dashboard`)
  - Lịch giảng dạy (`lecturer_schedule`)
  - Tính điểm chuyên cần (`lecturer_list_classroom`)
  - Quản lý điểm danh > Điểm danh sinh viên (`lecturer_attendance`)
  - Quản lý điểm danh > Lịch sử điểm danh (`lecturer_history_list_classroom`)
- **Block `content`:** Vùng nội dung chính
- **Block `js`:** Vùng nhúng JavaScript
- Nhúng thư viện: jQuery, Bootstrap, DataTables, Perfect Scrollbar, Bootstrap Datepicker

---

### `templates/lecturer/lecturer_home.html`
**Mô tả:** Trang chủ dashboard Giảng viên.

**Chức năng:**
- Hiển thị danh sách **Thông báo** từ hệ thống (blog posts)
- Render HTML nội dung thông báo an toàn (`body|safe`)

---

## 12. Giảng viên - Điểm danh

### `templates/lecturer/lecturer_attendance_class.html`
**Mô tả:** Trang xem thời khóa biểu tuần hiện tại và thực hiện điểm danh.

**Chức năng:**
- Hiển thị khoảng thời gian tuần hiện tại (ngày bắt đầu → kết thúc)
- Bảng lịch học trong tuần: Thứ, Môn học, Giờ bắt đầu, Giờ kết thúc
- Nếu buổi học **trùng với ngày hôm nay**:
  - Nút **Điểm danh bằng thủ công** → redirect đến form điểm danh thủ công
  - Nút **Điểm danh bằng khuôn mặt** → redirect đến trang nhận diện khuôn mặt
- Nếu **không phải ngày học**: Nút bị disable "Không phải ngày học"

---

### `templates/lecturer/lecturer_mask_attendance.html`
**Mô tả:** Trang điểm danh thủ công - giảng viên chọn trạng thái từng sinh viên.

**Chức năng:**
- Hiển thị tên lớp học
- Bảng danh sách sinh viên trong lớp: MSSV, Họ tên, Email, SĐT, Ngày sinh, Thời gian điểm danh
- Dropdown **Trạng thái điểm danh** cho từng sinh viên:
  - `1` = Vắng mặt
  - `2` = Đúng giờ
  - `3` = Trễ
- Tự động hiển thị trạng thái đã lưu trước đó (nếu có)
- Nút **Lưu trạng thái điểm danh** → submit form POST

---

### `templates/lecturer/lecturer_mask_attendance_by_face.html`
**Mô tả:** Trang điểm danh tự động bằng nhận diện khuôn mặt qua AI.

**Chức năng:**
- Hiển thị tên lớp học
- Stream video live từ camera: `<img src="/lecturer/live-video-feed2/{classroom_id}">`
- Hệ thống tự động nhận diện khuôn mặt sinh viên và ghi nhận điểm danh
- Form POST gửi kết quả điểm danh sau khi hoàn tất

---

### `templates/lecturer/lecturer_history_list_classroom.html`
**Mô tả:** Trang chọn lớp để xem lịch sử điểm danh.

**Chức năng:**
- Bảng danh sách các lớp học của giảng viên: Thứ, Môn học, Giờ bắt đầu/kết thúc
- Nút **Xem danh sách** → redirect đến trang lịch sử điểm danh của lớp đó
- **Phân trang:** Điều hướng trang trước/sau

---

### `templates/lecturer/lecturer_attendance_history.html`
**Mô tả:** Trang xem lịch sử điểm danh chi tiết của một lớp học.

**Chức năng:**
- Hiển thị tên lớp học
- Bảng điểm danh: MSSV, Họ tên, Thời gian check-in, Trạng thái (badge màu)
  - Vắng = badge đỏ
  - Đúng giờ = badge xanh
  - Trễ = badge vàng
- **Phân trang:** Điều hướng trang trước/sau

---

## 13. Giảng viên - Lịch & Lớp học

### `templates/lecturer/lecturer_schedule.html`
**Mô tả:** Trang xem lịch giảng dạy theo tuần với điều hướng tuần trước/sau.

**Chức năng:**
- Nút **Tuần Trước** / **Tuần Sau** → điều hướng qua query param `?week_start=...`
- Hiển thị khoảng thời gian tuần đang xem
- Bảng lịch dạy trong tuần: Thứ, Môn học, Giờ bắt đầu, Giờ kết thúc
- Thông báo "Không có giảng dạy trong tuần này" nếu rỗng

---

### `templates/lecturer/lecturer_list_classroom.html`
**Mô tả:** Trang danh sách lớp học phục vụ tính điểm chuyên cần.

**Chức năng:**
- Bảng danh sách lớp học: Thứ, Môn học, Giờ bắt đầu/kết thúc
- Nút **Xem danh sách** → redirect đến trang tính điểm chuyên cần từng sinh viên
- **Phân trang:** Điều hướng trang trước/sau

---

### `templates/lecturer/lecturer_calculate_attendance_points.html`
**Mô tả:** Trang tính và xem điểm chuyên cần của sinh viên trong một lớp.

**Chức năng:**
- Hiển thị tên lớp học
- Bảng điểm: MSSV, Họ tên, Số buổi đi học / Trễ / Vắng, Điểm chuyên cần (%)
- Badge trạng thái:
  - "Đang trong quá trình học" (vàng) nếu chưa hoàn thành đủ buổi
  - "Nghỉ quá quy định" (đỏ) nếu vắng > 2 buổi
  - "Bình thường" (xanh) nếu đủ điều kiện
- **Phân trang:** Điều hướng trang trước/sau

---

## 14. Giảng viên - Hồ sơ & Tài khoản

### `templates/lecturer/lecturer_profile.html`
**Mô tả:** Trang xem và chỉnh sửa hồ sơ cá nhân Giảng viên.

**Chức năng:**
- Hiển thị: Mã giảng viên (chỉ đọc), Họ tên, Email, SĐT, Ngày sinh (datepicker), Địa chỉ
- Form POST cập nhật thông tin cá nhân
- Hiển thị thông báo thành công sau khi cập nhật

---

### `templates/lecturer/lecturer_change_password.html`
**Mô tả:** Trang đổi mật khẩu cho Giảng viên.

**Chức năng:**
- Form đổi mật khẩu: Mật khẩu hiện tại, Mật khẩu mới, Nhập lại mật khẩu mới
- Tất cả trường bắt buộc
- Hiển thị thông báo thành công (xanh) hoặc thất bại (đỏ)

---

## 15. Sinh viên - Layout & Dashboard

### `templates/student/base_student_dashboard.html`
**Mô tả:** Template layout chung cho toàn bộ trang Sinh viên.

**Chức năng:**
- **Topbar:** Logo hệ thống, dropdown người dùng
- **Dropdown người dùng:** Quản lý hồ sơ, Đổi mật khẩu, Đăng xuất
- **Sidebar (Menu trái):**
  - Trang chủ (`student_dashboard`)
  - Thời khóa biểu (`student_schedule`)
  - Điểm quá trình (`student_checkpoint`)
  - Lịch sử điểm danh (`student_list_classroom`)
- **Block `content`:** Vùng nội dung chính
- Nhúng thư viện: jQuery, Bootstrap, Perfect Scrollbar, Bootstrap Datepicker

---

### `templates/student/student_home.html`
**Mô tả:** Trang chủ dashboard Sinh viên.

**Chức năng:**
- Hiển thị danh sách **Thông báo** từ hệ thống
- Render nội dung HTML thông báo an toàn (`body|safe`)

---

## 16. Sinh viên - Lịch & Điểm danh

### `templates/student/student_schedule.html`
**Mô tả:** Trang xem thời khóa biểu theo tuần của Sinh viên.

**Chức năng:**
- Nút **Tuần Trước** / **Tuần Sau** → điều hướng qua query param `?week_start=...`
- Hiển thị khoảng thời gian tuần đang xem
- Bảng thời khóa biểu: Thứ, Giảng viên, Môn học, Giờ bắt đầu/kết thúc
- Thông báo "Không có lịch học trong tuần này" nếu rỗng

---

### `templates/student/student_checkpoint.html`
**Mô tả:** Trang xem điểm quá trình (điểm chuyên cần) của Sinh viên.

**Chức năng:**
- Hiển thị ngày hiện tại
- Bảng điểm chuyên cần tất cả các lớp: Thứ, Môn học, Ngày bắt đầu/kết thúc, Số buổi đi/trễ/vắng, Điểm chuyên cần
- Badge trạng thái:
  - "Đang trong quá trình học" (vàng)
  - "Nghỉ quá quy định" (đỏ)
  - "Bình thường" (xanh)
- **Phân trang:** Điều hướng trang trước/sau

---

### `templates/student/student_list_classroom.html`
**Mô tả:** Trang danh sách lớp học phục vụ xem lịch sử điểm danh.

**Chức năng:**
- Bảng danh sách lớp học của sinh viên: Thứ, Môn học, Ngày bắt đầu/kết thúc
- Nút **Chi tiết** → redirect đến trang lịch sử điểm danh của lớp đó
- **Phân trang:** Điều hướng trang trước/sau

---

### `templates/student/student_attendance_history.html`
**Mô tả:** Trang xem lịch sử điểm danh chi tiết của một môn học.

**Chức năng:**
- Hiển thị tên lớp học/môn học
- Bảng lịch sử: STT, Thời gian check-in, Trạng thái (badge màu)
  - Vắng = badge đỏ
  - Đúng giờ = badge xanh
  - Trễ = badge vàng

---

## 17. Sinh viên - Hồ sơ & Tài khoản

### `templates/student/student_profile.html`
**Mô tả:** Trang xem và chỉnh sửa hồ sơ cá nhân Sinh viên.

**Chức năng:**
- Hiển thị: MSSV (chỉ đọc), Họ tên, Email, SĐT, Ngày sinh (datepicker), Địa chỉ
- Form POST cập nhật thông tin cá nhân
- Bootstrap Datepicker cho trường ngày sinh (`dd/mm/yyyy`)
- Hiển thị thông báo thành công sau khi cập nhật

---

### `templates/student/student_change_password.html`
**Mô tả:** Trang đổi mật khẩu cho Sinh viên.

**Chức năng:**
- Form đổi mật khẩu: Mật khẩu hiện tại, Mật khẩu mới, Nhập lại mật khẩu mới
- Tất cả trường bắt buộc
- Hiển thị thông báo thành công (xanh) hoặc thất bại (đỏ)

---

## 18. Trang lỗi

### `templates/error/base_error.html`
**Mô tả:** Template layout chung cho các trang lỗi HTTP.

---

### `templates/error/error-403.html`
**Mô tả:** Trang lỗi **403 Forbidden** - Không có quyền truy cập.

**Chức năng:**
- Hiển thị thông báo lỗi quyền truy cập
- Hướng dẫn người dùng quay lại hoặc đăng nhập

---

## Tổng quan cấu trúc

```
templates/
├── choose_login.html           # Trang chọn đối tượng đăng nhập
├── login.html                  # Đăng nhập Giảng viên/Admin
├── hash_password.html          # Tiện ích hash mật khẩu (dev)
│
├── admin/
│   ├── base_admin_dashboard.html          # Layout Admin
│   ├── admin_home.html                    # Trang chủ Admin
│   ├── admin_profile.html                 # Hồ sơ Admin
│   ├── admin_change_password.html         # Đổi mật khẩu Admin
│   ├── admin_lecturer_management.html     # Quản lý Giảng viên
│   ├── admin_student_management.html      # Quản lý Sinh viên
│   ├── admin_schedule_management.html     # Quản lý Thời khóa biểu
│   ├── admin_notification_management.html # Quản lý Thông báo
│   ├── admin_create_blog.html             # Tạo thông báo mới
│   ├── admin_edit_notification.html       # Chỉnh sửa thông báo
│   ├── admin_list_classroom_student_management.html  # Danh sách lớp học
│   ├── admin_list_student_classroom_management.html  # SV trong lớp
│   ├── webcam.html                        # Test stream webcam
│   ├── capture.html                       # Test chụp ảnh
│   └── modal-popup/
│       ├── popup_add_lecturer.html
│       ├── popup_edit_lecturer.html
│       ├── popup_delete_lecturer.html
│       ├── popup_add_student.html
│       ├── popup_edit_student.html
│       ├── popup_delete_student.html
│       ├── popup_capture_student.html
│       ├── popup_add_schedule.html
│       ├── popup_edit_schedule.html
│       ├── popup_delete_schedule.html
│       ├── popup_add_notification.html
│       ├── popup_delete_notification.html
│       ├── popup_add_student_in_class.html
│       ├── popup_add_list_students_in_class.html
│       ├── popup_delete_student_in_class.html
│       └── popup_delete_all_student_in_class.html
│
├── lecturer/
│   ├── base_lecturer_dashboard.html       # Layout Giảng viên
│   ├── lecturer_home.html                 # Trang chủ Giảng viên
│   ├── lecturer_profile.html              # Hồ sơ Giảng viên
│   ├── lecturer_change_password.html      # Đổi mật khẩu GV
│   ├── lecturer_schedule.html             # Lịch giảng dạy theo tuần
│   ├── lecturer_attendance_class.html     # TKB + điểm danh hôm nay
│   ├── lecturer_mask_attendance.html      # Điểm danh thủ công
│   ├── lecturer_mask_attendance_by_face.html  # Điểm danh khuôn mặt AI
│   ├── lecturer_history_list_classroom.html   # Chọn lớp xem lịch sử ĐD
│   ├── lecturer_attendance_history.html   # Lịch sử điểm danh chi tiết
│   ├── lecturer_list_classroom.html       # Chọn lớp tính điểm CC
│   └── lecturer_calculate_attendance_points.html  # Điểm chuyên cần SV
│
├── student/
│   ├── base_student_dashboard.html        # Layout Sinh viên
│   ├── student_login.html                 # Đăng nhập Sinh viên
│   ├── student_home.html                  # Trang chủ Sinh viên
│   ├── student_profile.html               # Hồ sơ Sinh viên
│   ├── student_change_password.html       # Đổi mật khẩu SV
│   ├── student_schedule.html              # Thời khóa biểu theo tuần
│   ├── student_checkpoint.html            # Điểm quá trình / chuyên cần
│   ├── student_list_classroom.html        # Danh sách lớp học
│   └── student_attendance_history.html    # Lịch sử điểm danh chi tiết
│
└── error/
    ├── base_error.html                    # Layout trang lỗi
    └── error-403.html                     # Lỗi 403 Forbidden
```

---

*Tài liệu được tạo ngày 30/04/2026*
