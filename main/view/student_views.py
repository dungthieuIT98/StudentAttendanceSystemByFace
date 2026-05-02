from datetime import date, timedelta, datetime

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import make_password, check_password
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils import timezone as dj_tz

from main.decorators import student_required
from main.models import StudentInfo, Classroom, Attendance
from main.models import BlogPost

# ─────────────────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────────────────

# System day-of-week code (1=Mon … 7=Sun) → Python weekday() (0=Mon … 6=Sun)
_DOW_TO_PYTHON = {1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6}

_DOW_LABEL = {
    1: 'Thứ Hai',
    2: 'Thứ Ba',
    3: 'Thứ Tư',
    4: 'Thứ Năm',
    5: 'Thứ Sáu',
    6: 'Thứ Bảy',
    7: 'Chủ Nhật',
}


def _count_sessions_to_date(classrooms, reference_date=None):
    """
    Count total sessions that have occurred across a list of classrooms up to
    (and including) reference_date.
    """
    if reference_date is None:
        reference_date = date.today()

    total = 0
    for cls in classrooms:
        python_dow = _DOW_TO_PYTHON.get(cls.day_of_week_begin, 0)
        end = min(cls.end_date, reference_date)
        if cls.begin_date > end:
            continue
        days_until = (python_dow - cls.begin_date.weekday()) % 7
        first = cls.begin_date + timedelta(days=days_until)
        if first > end:
            continue
        total += (end - first).days // 7 + 1

    return total


def _session_status(attendance_record, session_date, today):
    """
    Resolve display status for a single session:
      2  = attended (on time)
      3  = attended (late)
      1  = absent (recorded or inferred from missing record)
      0  = today — session is happening today, not checked in yet
     -1  = upcoming (future session)
    """
    if attendance_record is not None:
        return attendance_record.attendance_status
    if session_date < today:
        return 1    # past with no record → treat as absent
    if session_date == today:
        return 0    # today, not yet checked in
    return -1       # future


# ─────────────────────────────────────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────────────────────────────────────

def student_login_view(request):
    error_message = None
    if request.method == 'POST':
        id_student = request.POST.get('id_student')
        password = request.POST.get('password')
        try:
            student = StudentInfo.objects.get(id_student=id_student)
            if check_password(password, student.password):
                request.session['id_student'] = student.id_student
                return redirect('student_dashboard')
            else:
                error_message = "Tên đăng nhập hoặc mật khẩu không đúng."
        except StudentInfo.DoesNotExist:
            error_message = "Tên đăng nhập hoặc mật khẩu không đúng."

    return render(request, 'student/student_login.html', {'error_message': error_message})


@student_required
def student_dashboard_view(request):
    blog_posts = BlogPost.objects.filter(type__in=["ALL", "SV"])
    return render(request, 'student/student_home.html', {'blog_posts': blog_posts})


# ─────────────────────────────────────────────────────────────────────────────
# Schedule  (SUBJECT → week sessions with attendance status)
# ─────────────────────────────────────────────────────────────────────────────

@student_required
def student_schedule_view(request):
    id_student = request.session.get('id_student')
    week_start_param = request.GET.get('week_start')

    if week_start_param:
        try:
            week_start = date.fromisoformat(week_start_param)
        except ValueError:
            raise Http404("Invalid date format for week_start parameter")
    else:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())  # always Monday

    end_of_week = week_start + timedelta(days=6)
    today = date.today()

    classrooms = (
        Classroom.objects
        .filter(
            students__id_student=id_student,
            begin_date__lte=end_of_week,
            end_date__gte=week_start,
        )
        .select_related('id_lecturer')
        .order_by('day_of_week_begin', 'begin_time')
    )

    # One DB round-trip for all attendance in this week
    classroom_ids = [c.id_classroom for c in classrooms]
    week_att_qs = Attendance.objects.filter(
        id_student=id_student,
        id_classroom__in=classroom_ids,
        check_in_time__date__range=(week_start, end_of_week),
    )
    week_attendance = {}
    for a in week_att_qs:
        local_date = dj_tz.localtime(a.check_in_time).date()
        week_attendance[(a.id_classroom_id, local_date)] = a

    sessions = []
    for classroom in classrooms:
        python_dow = _DOW_TO_PYTHON.get(classroom.day_of_week_begin, 0)
        session_date = week_start + timedelta(days=python_dow)

        # Skip if this classroom hasn't started or already ended by this week's date
        if session_date < classroom.begin_date or session_date > classroom.end_date:
            continue

        att = week_attendance.get((classroom.id_classroom, session_date))
        status = _session_status(att, session_date, today)

        sessions.append({
            'classroom': classroom,
            'session_date': session_date,
            'day_label': _DOW_LABEL.get(classroom.day_of_week_begin, ''),
            'status': status,
            'attendance': att,
        })

    context = {
        'sessions': sessions,
        'start_of_week': week_start,
        'end_of_week': end_of_week,
        'today': today,
        'previous_week_start': (week_start - timedelta(days=7)).strftime('%Y-%m-%d'),
        'next_week_start': (week_start + timedelta(days=7)).strftime('%Y-%m-%d'),
    }
    return render(request, 'student/student_schedule.html', context)


# ─────────────────────────────────────────────────────────────────────────────
# Profile & password
# ─────────────────────────────────────────────────────────────────────────────

@student_required
def student_profile_view(request):
    id_student = request.session['id_student']
    student = StudentInfo.objects.get(id_student=id_student)

    if request.method == 'POST':
        student.student_name = request.POST['student_name']
        student.email = request.POST['email']
        student.phone = request.POST['phone']
        student.address = request.POST['address']
        student.birthday = datetime.strptime(request.POST['birthday'], '%d/%m/%Y').date()
        student.save()
        messages.success(request, 'Thay đổi thông tin thành công.')

    return render(request, 'student/student_profile.html', {'student': student})


@student_required
def student_change_password_view(request):
    id_student = request.session['id_student']
    student = StudentInfo.objects.get(id_student=id_student)

    if request.method == 'POST':
        old_password = request.POST['old_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']

        if check_password(old_password, student.password):
            if new_password == confirm_password:
                student.password = make_password(new_password)
                student.save()
                update_session_auth_hash(request, student)
                messages.success(request, 'Đổi mật khẩu thành công.')
            else:
                messages.error(request, 'Mật khẩu mới không khớp.')
        else:
            messages.error(request, 'Mật khẩu cũ không đúng.')

    return render(request, 'student/student_change_password.html')


# ─────────────────────────────────────────────────────────────────────────────
# Checkpoint  (SUBJECT → aggregate attendance stats)
# ─────────────────────────────────────────────────────────────────────────────

@student_required
def student_checkpoint_view(request):
    id_student = request.session.get('id_student')
    today = date.today()

    classrooms = (
        Classroom.objects
        .filter(students__id_student=id_student)
        .select_related('id_lecturer')
        .order_by('name', 'begin_time', 'day_of_week_begin')
    )

    # Group classrooms by subject (group_key, or individual id as fallback)
    grouped = {}
    for cls in classrooms:
        key = cls.group_key or str(cls.id_classroom)
        if key not in grouped:
            grouped[key] = {
                'name': cls.name,
                'classrooms': [],
                'begin_date': cls.begin_date,
                'end_date': cls.end_date,
            }
        g = grouped[key]
        g['classrooms'].append(cls)
        if cls.begin_date < g['begin_date']:
            g['begin_date'] = cls.begin_date
        if cls.end_date > g['end_date']:
            g['end_date'] = cls.end_date

    subjects = []
    for data in grouped.values():
        cls_ids = [c.id_classroom for c in data['classrooms']]
        total_sessions = _count_sessions_to_date(data['classrooms'], today)

        attended = Attendance.objects.filter(
            id_student=id_student,
            id_classroom__in=cls_ids,
            attendance_status=2,
        ).count()

        late = Attendance.objects.filter(
            id_student=id_student,
            id_classroom__in=cls_ids,
            attendance_status=3,
        ).count()

        recorded_absent = Attendance.objects.filter(
            id_student=id_student,
            id_classroom__in=cls_ids,
            attendance_status=1,
        ).count()

        # Unrecorded past sessions (no one used face-scan) also count as absent
        recorded_total = attended + late + recorded_absent
        unrecorded_absent = max(0, total_sessions - recorded_total)
        total_absent = recorded_absent + unrecorded_absent
        total_present = attended + late

        rate = round(total_present / total_sessions * 100, 1) if total_sessions > 0 else 0.0

        subjects.append({
            'name': data['name'],
            'begin_date': data['begin_date'],
            'end_date': data['end_date'],
            'total_sessions': total_sessions,
            'attended': attended,
            'late': late,
            'absent': total_absent,
            'total_present': total_present,
            'attendance_rate': rate,
            # Risk: more than 20% of occurred sessions were absent
            'is_at_risk': total_sessions > 0 and total_absent > (total_sessions * 0.2),
        })

    subjects.sort(key=lambda x: x['name'])

    paginator = Paginator(subjects, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'student/student_checkpoint.html', {
        'subjects': page_obj,
        'today': today,
    })


@student_required
def student_attendance_history_view(request, classroom_id):
    id_student = request.session.get('id_student')
    classroom = Classroom.objects.get(pk=classroom_id)
    students_attendance = Attendance.objects.filter(
        id_student=id_student,
        id_classroom=classroom,
    ).order_by('check_in_time')

    return render(request, 'student/student_attendance_history.html', {
        'students_attendance': students_attendance,
        'classroom': classroom,
    })
