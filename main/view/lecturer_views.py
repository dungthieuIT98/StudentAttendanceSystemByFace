import os
import time
from datetime import date, timedelta

import cv2
import numpy as np
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import check_password, make_password
from django.core.paginator import Paginator
from django.http import Http404
from django.http import JsonResponse
from django.http import StreamingHttpResponse
from django.shortcuts import redirect
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_GET

from main.decorators import lecturer_required
from main.models import StaffInfo, StudentClassDetails
from main.src.utility import parse_model_name
from main.view.reg import *
from main.models import BlogPost, format_clock_sa_ch_from_datetime

# Do NOT instantiate AntiSpoofPredict here.
# The ModelRegistry singleton (loaded by reg.py → model_registry.py) already
# holds a single RetinaFace DNN net and all anti-spoof model weights.
# Creating a second AntiSpoofPredict(0) here would double memory usage.


@lecturer_required
def lecturer_dashboard_view(request):
    blog_posts = BlogPost.objects.filter(type__in=["ALL", "GV"])
    # SPA Support: base_lecturer_dashboard.html checks request.META.HTTP_X_REQUESTED_WITH
    # and renders only content block for AJAX, or full layout for normal requests
    return render(request, 'lecturer/lecturer_home.html', {'blog_posts': blog_posts})


@lecturer_required
def lecturer_schedule_view(request):
    id_lecturer = request.session.get('id_staff')
    week_start_param = request.GET.get('week_start')

    if week_start_param:
        try:
            week_start = date.fromisoformat(week_start_param)
        except ValueError:
            raise Http404("Invalid date format for week_start parameter")
    else:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

    end_of_week = week_start + timedelta(days=6)

    lecturer_classes = Classroom.objects.filter(
        id_lecturer__id_staff=id_lecturer,
        begin_date__lte=end_of_week,
        end_date__gte=week_start
    ).order_by('day_of_week_begin', 'begin_time')

    previous_week_start = week_start - timedelta(days=7)
    next_week_start = week_start + timedelta(days=7)

    previous_week_start = previous_week_start.strftime("%Y-%m-%d")
    next_week_start = next_week_start.strftime("%Y-%m-%d")

    context = {
        'lecturer_classes': lecturer_classes,
        'start_of_week': week_start,
        'end_of_week': end_of_week,
        'previous_week_start': previous_week_start,
        'next_week_start': next_week_start,
    }
    return render(request, 'lecturer/lecturer_schedule.html', context)


@lecturer_required
def lecturer_profile_view(request):
    id_lecturer = request.session['id_staff']
    lecturer = StaffInfo.objects.get(id_staff=id_lecturer)

    if request.method == 'POST':
        lecturer.staff_name = request.POST['lecturer_name']
        lecturer.email = request.POST['email']
        lecturer.phone = request.POST['phone']
        lecturer.address = request.POST['address']
        lecturer.birthday = datetime.strptime(request.POST['birthday'], '%d/%m/%Y').date()
        lecturer.save()
        messages.success(request, 'Thay đổi thông tin thành công.')

    context = {'lecturer': lecturer}

    return render(request, 'lecturer/lecturer_profile.html', context)


@lecturer_required
def lecturer_change_password_view(request):
    id_lecturer = request.session['id_staff']
    lecturer = StaffInfo.objects.get(id_staff=id_lecturer)

    if request.method == 'POST':
        old_password = request.POST['old_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']

        if check_password(old_password, lecturer.password):
            if new_password == confirm_password:
                lecturer.password = make_password(new_password)
                lecturer.save()
                update_session_auth_hash(request, lecturer)
                messages.success(request, 'Đổi mật khẩu thành công.')
            else:
                messages.error(request, 'Mật khẩu mới không khớp.')
        else:
            messages.error(request, 'Mật khẩu cũ không đúng.')

    return render(request, 'lecturer/lecturer_change_password.html')


@lecturer_required
def lecturer_attendance_class_view(request):
    id_lecturer = request.session.get('id_staff')

    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    end_of_week = week_start + timedelta(days=6)

    lecturer_classes = Classroom.objects.filter(
        id_lecturer__id_staff=id_lecturer,
        begin_date__lte=end_of_week,
        end_date__gte=week_start
    ).order_by('day_of_week_begin', 'begin_time')

    day_of_week_today = today.isoweekday()

    context = {
        'lecturer_classes': lecturer_classes,
        'start_of_week': week_start,
        'end_of_week': end_of_week,
        'day_of_week_today': day_of_week_today,
    }

    return render(request, 'lecturer/lecturer_attendance_class.html', context)


def _classroom_ids_same_schedule_group(classroom):
    """Các buổi (row DB) trong cùng TKBG chia sẻ roster sinh viên theo group_key."""
    gk = (getattr(classroom, "group_key", None) or "").strip()
    if gk:
        return list(Classroom.objects.filter(group_key=gk).values_list("pk", flat=True))
    return [classroom.pk]


def _lecturer_roster_for_class(classroom):
    ids = _classroom_ids_same_schedule_group(classroom)
    qs = (
        StudentClassDetails.objects.filter(id_classroom_id__in=ids)
        .select_related("id_student")
        .order_by("id_student_id")
    )
    seen = set()
    roster = []
    for row in qs:
        if row.id_student_id in seen:
            continue
        seen.add(row.id_student_id)
        roster.append(row)
    return roster


@lecturer_required
def lecturer_mark_attendance(request, classroom_id):
    classroom = get_object_or_404(Classroom, pk=classroom_id)
    students_in_class = _lecturer_roster_for_class(classroom)

    today = timezone.localdate()
    day_of_week_today = today.isoweekday()

    if day_of_week_today != classroom.day_of_week_begin:
        return redirect('lecturer_attendance')

    attendance_list = Attendance.objects.filter(id_classroom=classroom, check_in_time__date=today)
    attendance_by_student = {}
    for att in attendance_list:
        attendance_by_student[att.id_student_id] = att

    now = timezone.now()
    for row in students_in_class:
        setattr(row, "today_attendance", attendance_by_student.get(row.id_student_id))

    if request.method == 'POST':
        for student in students_in_class:
            student_id = student.id_student
            attendance_status = request.POST.get(f'attendance_status_{student_id.id_student}')

            if attendance_status is None:
                continue

            attendance, created = Attendance.objects.get_or_create(
                id_student=student_id,
                id_classroom=classroom,
                check_in_time__date=today,
                defaults={
                    'attendance_status': attendance_status,
                    'check_in_time': now,
                },
            )

            if not created and attendance_status != str(attendance.attendance_status):
                attendance.attendance_status = attendance_status
                attendance.check_in_time = now
                attendance.save()

        return redirect('lecturer_mark_attendance', classroom_id=classroom_id)

    context = {
        'students_in_class': students_in_class,
        'classroom': classroom,
        'attendance_list': attendance_list,
        'today': today,
    }

    return render(request, 'lecturer/lecturer_mask_attendance.html', context)


def live_video_feed2(request, classroom_id):
    """
    MJPEG stream for face recognition attendance.

    - gzip removed: JPEG frames are already compressed; gzip adds CPU overhead
      with essentially 0% size reduction and extra latency.
    - generate_frames() removed: it created a new AntiSpoofPredict per call
      (loading the DNN net from disk every time) and was not wired to any URL.
      All inference now goes through ModelRegistry in reg.main().
    """
    return StreamingHttpResponse(
        main(classroom_id),
        content_type="multipart/x-mixed-replace; boundary=frame",
    )


@lecturer_required
def lecturer_mark_attendance_by_face(request, classroom_id):
    classroom = get_object_or_404(Classroom, pk=classroom_id)
    students_in_class = _lecturer_roster_for_class(classroom)
    day_of_week_today = timezone.localdate().isoweekday()

    if day_of_week_today != classroom.day_of_week_begin:
        return redirect('lecturer_attendance')

    # Hoàn tất: chỉ thoát và về danh sách — điểm danh đã được ghi khi nhận diện (stream loop).
    if request.method == 'POST':
        messages.success(request, 'Đã hoàn tất điểm danh bằng khuôn mặt.')
        return redirect('lecturer_attendance')

    today = timezone.localdate()
    # Chỉ coi "đã điểm danh" = có mặt (2) / trễ (3); vắng (1) không vào sidebar này
    attendance_list = (
        Attendance.objects.filter(id_classroom=classroom, check_in_time__date=today)
        .filter(attendance_status__in=(2, 3))
        .select_related('id_student')
        .order_by('-check_in_time')
    )

    context = {
        'students_in_class': students_in_class,
        'classroom': classroom,
        'attendance_list': attendance_list
    }

    return render(request, 'lecturer/lecturer_mask_attendance_by_face.html', context)


@lecturer_required
@require_GET
def lecturer_live_attendance_today(request, classroom_id):
    from main.view.reg import get_pending_attendance_for_classroom
    
    classroom = Classroom.objects.get(pk=classroom_id)
    today = timezone.localdate()
    
    # Lấy từ DB (đã commit)
    qs = (
        Attendance.objects
        .filter(id_classroom=classroom, check_in_time__date=today)
        .filter(attendance_status__in=(2, 3))
        .select_related('id_student')
        .order_by('-check_in_time')
    )

    items_dict = {}
    for a in qs:
        items_dict[a.id_student.id_student] = {
            "id_attendance": a.id_attendance,
            "student_id": a.id_student.id_student,
            "student_name": a.id_student.student_name,
            "attendance_status": a.attendance_status,
            "check_in_time": format_clock_sa_ch_from_datetime(a.check_in_time),
            "_sort_ts": a.check_in_time,
        }

    # Merge cache (pending, chưa commit DB) → hiển thị trước
    pending_list = get_pending_attendance_for_classroom(classroom_id)
    for p in pending_list:
        sid = p["student_id"]
        if sid not in items_dict:  # Chưa có từ DB → dùng cache
            ts = p["timestamp"]
            items_dict[sid] = {
                "id_attendance": 0,
                "student_id": sid,
                "student_name": p["student_name"],
                "attendance_status": p["attendance_status"],
                "check_in_time": format_clock_sa_ch_from_datetime(ts),
                "_sort_ts": ts,
            }

    items = list(items_dict.values())
    items.sort(key=lambda x: x["_sort_ts"], reverse=True)
    for it in items:
        it.pop("_sort_ts", None)

    return JsonResponse({"count": len(items), "items": items})


@lecturer_required
def lecturer_history_list_classroom_view(request):
    id_lecturer = request.session.get('id_staff')
    classroom_per_page = 10
    page_number = request.GET.get('page')

    classrooms = Classroom.objects.filter(
        id_lecturer__id_staff=id_lecturer
    ).order_by('day_of_week_begin', 'begin_time')

    paginator = Paginator(classrooms, classroom_per_page)
    page = paginator.get_page(page_number)

    context = {'classrooms': page}

    return render(request, 'lecturer/lecturer_history_list_classroom.html', context)


@lecturer_required
def lecturer_attendance_history_view(request, classroom_id):
    classroom = Classroom.objects.get(pk=classroom_id)
    students_attendance = Attendance.objects.filter(id_classroom=classroom).order_by('id_student')

    student_per_page = 10
    page_number = request.GET.get('page')
    pagniator = Paginator(students_attendance, student_per_page)
    page = pagniator.get_page(page_number)

    context = {
        'students_attendance': page,
        'classroom': classroom
    }

    return render(request, 'lecturer/lecturer_attendance_history.html', context)


@lecturer_required
def lecturer_list_classroom_view(request):
    id_lecturer = request.session.get('id_staff')
    classroom_per_page = 10
    page_number = request.GET.get('page')

    classrooms = Classroom.objects.filter(
        id_lecturer__id_staff=id_lecturer
    ).order_by('day_of_week_begin', 'begin_time')

    paginator = Paginator(classrooms, classroom_per_page)
    page = paginator.get_page(page_number)

    context = {'classrooms': page}

    return render(request, 'lecturer/lecturer_list_classroom.html', context)


@lecturer_required
def lecturer_calculate_attendance_points_view(request, classroom_id):
    classroom = Classroom.objects.get(pk=classroom_id)
    students_in_class = StudentClassDetails.objects.filter(id_classroom=classroom)
    student_per_page = 10
    page_number = request.GET.get('page')

    student_attendance_counts = []
    for student in students_in_class:
        absent_count = Attendance.objects.filter(id_classroom=classroom, id_student=student.id_student,
                                                 attendance_status=1).count()
        present_count = Attendance.objects.filter(id_classroom=classroom, id_student=student.id_student,
                                                  attendance_status=2).count()
        late_count = Attendance.objects.filter(id_classroom=classroom, id_student=student.id_student,
                                               attendance_status=3).count()

        total_number_attendance = absent_count + late_count + present_count
        total_attendance_present = late_count + present_count
        total_attendance_percentage = round((((absent_count * 0) + (late_count * 0.5) + present_count) / 9) * 3, 2)

        student_attendance_counts.append({
            'student': student,
            'absent_count': absent_count,
            'late_count': late_count,
            'present_count': present_count,
            'total_number_attendance': total_number_attendance,
            'total_attendance_present': total_attendance_present,
            'total_attendance_percentage': total_attendance_percentage
        })

        paginator = Paginator(student_attendance_counts, student_per_page)
        page = paginator.get_page(page_number)

    context = {
        'students_in_class': page,
        'classroom': classroom,
    }

    return render(request, 'lecturer/lecturer_calculate_attendance_points.html', context)
