from datetime import date, timedelta, datetime

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import make_password, check_password
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import redirect, render

from main.decorators import student_required
from main.models import StudentInfo, Classroom, Attendance
from main.models import BlogPost


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
        week_start = today - timedelta(days=today.weekday())

    end_of_week = week_start + timedelta(days=6)

    student_classes = Classroom.objects.filter(
        students__id_student=id_student,
        begin_date__lte=end_of_week,
        end_date__gte=week_start,
    ).order_by('day_of_week_begin', 'begin_time')

    previous_week_start = week_start - timedelta(days=7)
    next_week_start = week_start + timedelta(days=7)

    previous_week_start = previous_week_start.strftime("%Y-%m-%d")
    next_week_start = next_week_start.strftime("%Y-%m-%d")

    context = {
        'student_classes': student_classes,
        'start_of_week': week_start,
        'end_of_week': end_of_week,
        'previous_week_start': previous_week_start,
        'next_week_start': next_week_start,
    }

    return render(request, 'student/student_schedule.html', context)


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

    context = {'student': student}

    return render(request, 'student/student_profile.html', context)


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


@student_required
def student_checkpoint_view(request):
    id_student = request.session['id_student']

    student_classes = Classroom.objects.filter(
        students__id_student=id_student,
    ).order_by('name', 'begin_time', 'day_of_week_begin')

    current_date = date.today()
    classroom_per_page = 5
    page_number = request.GET.get('page')

    grouped_scores = {}
    for classroom in student_classes:
        key = classroom.group_key or str(classroom.id_classroom)
        
        if key not in grouped_scores:
            grouped_scores[key] = {
                'classrooms': [],
                'days': [],
                'name': classroom.name,
                'begin_date': classroom.begin_date,
                'end_date': classroom.end_date,
                'begin_time': classroom.begin_time,
                'end_time': classroom.end_time,
                'absent_count': 0,
                'present_count': 0,
                'late_count': 0,
            }
        
        grouped_scores[key]['classrooms'].append(classroom)
        grouped_scores[key]['days'].append(classroom.day_of_week_begin)
        
        absent_count = Attendance.objects.filter(
            attendance_status=1,
            id_student=id_student,
            id_classroom=classroom.id_classroom,
        ).count()

        present_count = Attendance.objects.filter(
            attendance_status=2,
            id_student=id_student,
            id_classroom=classroom.id_classroom,
        ).count()

        late_count = Attendance.objects.filter(
            attendance_status=3,
            id_student=id_student,
            id_classroom=classroom.id_classroom,
        ).count()
        
        grouped_scores[key]['absent_count'] += absent_count
        grouped_scores[key]['present_count'] += present_count
        grouped_scores[key]['late_count'] += late_count

    attendance_scores = []
    for key, data in grouped_scores.items():
        total_number_attendance = data['absent_count'] + data['late_count'] + data['present_count']
        total_attendance_present = data['late_count'] + data['present_count']
        total_attendance_percentage = round((((data['absent_count'] * 0) + (data['late_count'] * 0.5) + data['present_count']) / 9) * 3, 2) if total_number_attendance > 0 else 0

        attendance_scores.append({
            'name': data['name'],
            'days': sorted(data['days']),
            'begin_date': data['begin_date'],
            'end_date': data['end_date'],
            'begin_time': data['begin_time'],
            'end_time': data['end_time'],
            'absent_count': data['absent_count'],
            'present_count': data['present_count'],
            'late_count': data['late_count'],
            'total_number_attendance': total_number_attendance,
            'total_attendance_present': total_attendance_present,
            'total_attendance_percentage': total_attendance_percentage,
        })

    attendance_scores.sort(key=lambda x: (x['name'], x['begin_time']))

    paginator = Paginator(attendance_scores, classroom_per_page)
    page = paginator.get_page(page_number)

    context = {
        'attendance_scores': page,
        'current_date': current_date,
    }

    return render(request, 'student/student_checkpoint.html', context)


@student_required
def student_list_classroom_view(request):
    id_student = request.session.get('id_student')
    classroom_per_page = 5
    page_number = request.GET.get('page')

    student_classes = Classroom.objects.filter(
        students__id_student=id_student,
    ).order_by('day_of_week_begin', 'begin_time')

    paginator = Paginator(student_classes, classroom_per_page)
    page = paginator.get_page(page_number)

    context = {'classrooms': page}

    return render(request, 'student/student_list_classroom.html', context)


@student_required
def student_attendance_history_view(request, classroom_id):
    id_student = request.session.get('id_student')
    classroom = Classroom.objects.get(pk=classroom_id)
    students_attendance = Attendance.objects.filter(
        id_student=id_student,
        id_classroom=classroom)

    context = {
        'students_attendance': students_attendance,
        'classroom': classroom
    }

    return render(request, 'student/student_attendance_history.html', context)
