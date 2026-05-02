import math
import os
import pickle
from datetime import datetime
import uuid

import openpyxl

import cv2
import numpy as np
import tensorflow as tf
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import check_password, make_password
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.db import transaction
from django.http import JsonResponse
from django.http import StreamingHttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from sklearn.svm import SVC
from django.urls import reverse
from django.views.generic.edit import CreateView
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView

from main.forms import BlogForm, EditBlogForm
from main.models import BlogPost

from main import facenet
from main.decorators import admin_required
from main.models import StaffInfo, StudentInfo, StaffRole, Role, Classroom, StudentClassDetails
from main.src.anti_spoof_predict import AntiSpoofPredict
from main.models import BlogPost
from django.views import View
from django.views.decorators.http import require_POST


def _parse_form_date(date_str):
    """dd/mm/yyyy first (VN UI); fallback mm/dd/yyyy or yyyy-mm-dd from pickers/browsers."""
    s = (date_str or '').strip()
    for fmt in ('%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d'):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    raise ValueError(f'Invalid date string: {date_str!r}')


def _weekday_label(day: int) -> str:
    mapping = {
        1: 'Thứ Hai',
        2: 'Thứ Ba',
        3: 'Thứ Tư',
        4: 'Thứ Năm',
        5: 'Thứ Sáu',
        6: 'Thứ Bảy',
        7: 'Chủ Nhật',
    }
    try:
        return mapping.get(int(day), str(day))
    except (TypeError, ValueError):
        return str(day)


color = (255, 0, 0)
thickness = 2
max_images = 300
device_id = 0
CAPTURE_STATUS = 0  # Đặt giá trị ban đầu cho biến toàn cục

TRAIN_STATUS = 0
mode = 'TRAIN'  # Change to 'TRAIN' to train the classifier
data_dir = 'main/Dataset/FaceData/processed'
model = 'main/Models/20180402-114759.pb'
classifier_filename = 'main/Models/facemodel.pkl'
use_split_dataset = False

batch_size = 90
image_size = 160
seed = 666
min_nrof_images_per_class = 20
nrof_train_images_per_class = 10


# The rest of the code remains the same
# Define the function to split the dataset
class AddBlog(SuccessMessageMixin, CreateView, ListView):
    form_class = BlogForm
    model = BlogPost
    template_name = "admin/admin_notification_management.html"
    context_object_name = 'blog_posts'

    def get_success_url(self):
        return reverse('admin_notification_view')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['blog_posts'] = BlogPost.objects.all()
        context['edit_form'] = EditBlogForm()
        context['type_choices'] = BlogPost.TYPE_CHOICES
        return context


class BlogPostDeleteView(View):
    def get(self, request, pk, *args, **kwargs):
        blog_post = get_object_or_404(BlogPost, id=pk)
        blog_post.delete()
        return redirect('admin_notification_view')


class EditBlogView(View):
    template_name = 'admin/admin_edit_notification.html'

    def get(self, request, blog_post_id):
        blog_post_instance = get_object_or_404(BlogPost, id=blog_post_id)
        edit_form = EditBlogForm(instance=blog_post_instance)
        return render(request, self.template_name, {'edit_form': edit_form})

    def post(self, request, blog_post_id):
        blog_post_instance = get_object_or_404(BlogPost, id=blog_post_id)
        edit_form = EditBlogForm(request.POST, instance=blog_post_instance)
        if edit_form.is_valid():
            edit_form.save()
            # Redirect to a success page or another URL
            return redirect('admin_notification_view')  # Replace with your actual success URL name
        else:
            # Form is not valid, handle accordingly
            return render(request, self.template_name, {'edit_form': edit_form})


@admin_required
def admin_notification_get_info(request, blog_post_id):
    blog_post = get_object_or_404(BlogPost, id=blog_post_id)
    return JsonResponse({
        'blog_post': {
            'id': blog_post.id,
            'title': blog_post.title,
            'body': blog_post.body,
            'type': blog_post.type,
        }
    })


@admin_required
@require_POST
def admin_notification_edit(request, blog_post_id):
    blog_post = get_object_or_404(BlogPost, id=blog_post_id)
    form = EditBlogForm(request.POST, instance=blog_post)
    if form.is_valid():
        form.save()
        messages.success(request, 'Cập nhật thông báo thành công.')
    else:
        messages.error(request, 'Cập nhật thông báo thất bại.')
    return redirect('admin_notification_view')


@admin_required
def admin_dashboard_view(request):
    blog_posts = BlogPost.objects.all()
    # SPA Support: base_admin_dashboard.html checks request.META.HTTP_X_REQUESTED_WITH
    # and renders only content block for AJAX, or full layout for normal requests
    return render(request, 'admin/admin_home.html', {'blog_posts': blog_posts})


@admin_required
def admin_notification_view(request):
    blog_posts = BlogPost.objects.all()
    return render(request, 'admin/admin_notification_management.html', {'blog_posts': blog_posts})


@admin_required
def admin_profile_view(request):
    id_admin = request.session['id_staff']
    admin = StaffInfo.objects.get(id_staff=id_admin)
    if request.method == 'POST':
        admin.staff_name = request.POST['admin_name']
        admin.email = request.POST['email']
        admin.phone = request.POST['phone']
        admin.address = request.POST['address']
        admin.birthday = _parse_form_date(request.POST['birthday'])
        admin.save()
        messages.success(request, 'Thay đổi thông tin thành công.')

    context = {'admin': admin}

    return render(request, 'admin/admin_profile.html', context)


@admin_required
def admin_change_password_view(request):
    id_admin = request.session['id_staff']
    admin = StaffInfo.objects.get(id_staff=id_admin)

    if request.method == 'POST':
        old_password = request.POST['old_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']

        if check_password(old_password, admin.password):
            if new_password == confirm_password:
                admin.password = make_password(new_password)
                admin.save()
                update_session_auth_hash(request, admin)
                messages.success(request, 'Đổi mật khẩu thành công.')
            else:
                messages.error(request, 'Mật khẩu mới không khớp.')
        else:
            messages.error(request, 'Mật khẩu cũ không đúng.')

    return render(request, 'admin/admin_change_password.html')


@admin_required
def admin_student_management_view(request):
    students = StudentInfo.objects.all()
    student_per_page = 10
    paginator = Paginator(students, student_per_page)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        'list_students': page,
    }
    return render(request, 'admin/admin_student_management.html', context)


@admin_required
def admin_student_add(request):
    if request.method == 'POST':
        id_student = request.POST['id_student']
        student_name = request.POST['student_name']
        email = request.POST['email']
        phone = request.POST['phone']
        address = request.POST['address']
        birthday = _parse_form_date(request.POST['birthday'])

        PathImageFolder = request.POST['PathImageFolder']
        password = make_password('1')
        student = StudentInfo(id_student=id_student,
                              student_name=student_name,
                              email=email, phone=phone,
                              address=address,
                              birthday=birthday,
                              PathImageFolder=PathImageFolder,
                              password=password)
        student.save()
        messages.success(request, 'Thêm sinh viên thành công.')
        return redirect('admin_student_management')
    return render(request, 'admin/modal-popup/popup_add_student.html')


@admin_required
def admin_student_edit(request, id_student):
    student = StudentInfo.objects.get(id_student=id_student)
    context = {'student': student}
    if request.method == 'POST':
        student.student_name = request.POST['student_name_edit']
        student.email = request.POST['email_edit']
        student.phone = request.POST['phone_edit']
        student.address = request.POST['address_edit']
        student.birthday = _parse_form_date(request.POST['birthday_edit'])
        student.PathImageFolder = request.POST['PathImageFolder_edit']
        print(request.POST['student_name_edit'])
        student.save()
        messages.success(request, 'Thay đổi thông tin thành công.')
        return redirect('admin_student_management')
    return render(request, 'admin/modal-popup/popup_edit_student.html', context)


@admin_required
def admin_student_capture(request, id_student):
    student = StudentInfo.objects.get(id_student=id_student)
    context = {'student': student}
    if request.method == 'POST':
        student.student_name = request.POST['student_name_capture']
        student.email = request.POST['email_capture']
        student.phone = request.POST['phone_capture']
        student.address = request.POST['address_capture']
        student.birthday = _parse_form_date(request.POST['birthday_capture'])
        student.PathImageFolder = request.POST['PathImageFolder_capture']
        student.save()
        messages.success(request, 'Thay đổi thông tin thành công.')
        return redirect('admin_student_management')
    return render(request, 'admin/modal-popup/popup_capture_student.html', context)


@admin_required
@require_POST
def admin_student_delete(request, id_student):
    StudentInfo.objects.filter(id_student=id_student).delete()

    # Directory to check for existence and delete
    folder_path = f"./main/Dataset/FaceData/processed/{id_student}"

    # Check if the directory exists
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        # Remove the directory and its contents recursively
        import shutil
        shutil.rmtree(folder_path)
        print(f"Folder '{folder_path}' and its contents deleted.")
    else:
        print(f"Folder '{folder_path}' does not exist.")

    return redirect('admin_student_management')


@admin_required
def admin_student_get_info(request, id_student):
    try:
        student = StudentInfo.objects.get(id_student=id_student)
        student_data = {
            'id_student': student.id_student,
            'student_name': student.student_name,
            'email': student.email,
            'phone': student.phone,
            'address': student.address,
            'birthday': student.birthday.strftime('%d/%m/%Y'),
            'PathImageFolder': student.PathImageFolder,
        }
        return JsonResponse({'student': student_data})
    except StudentInfo.DoesNotExist:
        return JsonResponse({'error': 'Không tìm thấy học sinh'}, status=404)


@admin_required
def admin_lecturer_management_view(request):
    lecturer = StaffInfo.objects.filter(roles__name='Lecturer')
    per_page = 10
    paginator = Paginator(lecturer, per_page)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        'list_lecturers': page,
    }
    return render(request, 'admin/admin_lecturer_management.html', context)


@admin_required
def admin_lecturer_add(request):
    if request.method == 'POST':
        id_lecturer = request.POST['id_lecturer']
        staff_name = request.POST['lecturer_name']
        email = request.POST['email']
        phone = request.POST['phone']
        address = request.POST['address']
        birthday = _parse_form_date(request.POST['birthday'])
        password = make_password('1')
        lecturer = StaffInfo(id_staff=id_lecturer,
                             staff_name=staff_name,
                             email=email, phone=phone,
                             address=address,
                             birthday=birthday,
                             password=password
                             )
        lecturer.save()
        role_obj, _ = Role.objects.get_or_create(name='Lecturer')
        StaffRole.objects.create(staff=lecturer, role=role_obj)
        messages.success(request, 'Thêm giảng viên thành công.')
        return redirect('admin_lecturer_management')
    return redirect('admin_lecturer_management')


@admin_required
@require_POST
def admin_lecturer_delete(request, id_staff):
    StaffInfo.objects.filter(id_staff=id_staff).delete()
    return redirect('admin_lecturer_management')


@admin_required
def admin_lecturer_edit(request, id_staff):
    lecturer = StaffInfo.objects.get(id_staff=id_staff)
    context = {'staff': lecturer}
    if request.method == 'POST':
        lecturer.staff_name = request.POST['lecturer_name']
        lecturer.email = request.POST['email']
        lecturer.phone = request.POST['phone']
        lecturer.address = request.POST['address']
        lecturer.birthday = _parse_form_date(request.POST['birthday'])
        lecturer.save()
        messages.success(request, 'Thay đổi thông tin thành công.')
        return redirect('admin_lecturer_management')
    return render(request, 'admin/modal-popup/popup_edit_lecturer.html', context)


@admin_required
def admin_lecturer_get_info(request, id_staff):
    try:
        lecturer = StaffInfo.objects.get(id_staff=id_staff)
        staff_data = {
            'id_staff': lecturer.id_staff,
            'staff_name': lecturer.staff_name,
            'email': lecturer.email,
            'phone': lecturer.phone,
            'address': lecturer.address,
            'birthday': lecturer.birthday.strftime('%d/%m/%Y'),
        }
        return JsonResponse({'lecturer': staff_data})
    except StaffInfo.DoesNotExist:
        return JsonResponse({'error': 'Không tìm thấy giảng viên'}, status=404)


@admin_required
def admin_schedule_management_view(request):
    schedule = Classroom.objects.all().order_by('group_key', 'id_classroom')
    lecturers = StaffInfo.objects.filter(roles__name='Lecturer').order_by('id_staff')
    schedule_per_page = 10
    # Group by group_key for UI: 1 row with multiple weekdays
    grouped = {}
    for s in schedule:
        key = s.group_key or str(s.id_classroom)
        g = grouped.get(key)
        if not g:
            grouped[key] = {
                'group_key': key,
                'id_classroom': s.id_classroom,
                'name': s.name,
                'begin_date': s.begin_date,
                'end_date': s.end_date,
                'begin_time': s.begin_time,
                'end_time': s.end_time,
                'id_lecturer': s.id_lecturer,
                'days': set([s.day_of_week_begin]),
            }
        else:
            g['days'].add(s.day_of_week_begin)
    grouped_list = list(grouped.values())
    for g in grouped_list:
        g['days_sorted'] = sorted(list(g['days']))
        g['days_label'] = ', '.join([str(d) for d in g['days_sorted']])
    # sort by name then begin_time
    grouped_list.sort(key=lambda x: (x['name'], x['begin_time'], x['group_key']))

    paginator = Paginator(grouped_list, schedule_per_page)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        'list_schedules': page,
        'list_lecturers': lecturers,
    }

    return render(request, 'admin/admin_schedule_management.html', context)


@admin_required
def admin_schedule_add(request):
    if request.method == 'POST':
        name = request.POST['name']
        begin_date = _parse_form_date(request.POST['begin_date'])
        end_date = _parse_form_date(request.POST['end_date'])
        day_of_week_list = request.POST.getlist('day_of_week_begin_list') or []
        begin_time = request.POST['begin_time']
        end_time = request.POST['end_time']
        id_lecturer = request.POST['id_lecturer']
        if not day_of_week_list:
            messages.warning(request, 'Vui lòng chọn ít nhất 1 Thứ.')
            return redirect('admin_schedule_management')

        created = 0
        group_key = str(uuid.uuid4())
        with transaction.atomic():
            for day in day_of_week_list:
                Classroom.objects.create(
                    group_key=group_key,
                    name=name,
                    begin_date=begin_date,
                    end_date=end_date,
                    day_of_week_begin=int(day),
                    begin_time=begin_time,
                    end_time=end_time,
                    id_lecturer_id=id_lecturer
                )
                created += 1
        messages.success(request, f'Thêm {created} Thời Khóa Biểu thành công.')
        return redirect('admin_schedule_management')
    return render(request, 'admin/modal-popup/popup_add_schedule.html')


@admin_required
def admin_schedule_edit(request, id_classroom):
    schedule = Classroom.objects.get(id_classroom=id_classroom)
    context = {'schedule': schedule}
    if request.method == 'POST':
        schedule.name = request.POST['name']
        schedule.begin_date = _parse_form_date(request.POST['begin_date'])
        schedule.end_date = _parse_form_date(request.POST['end_date'])
        day_of_week_list = request.POST.getlist('day_of_week_begin_list') or []
        if not day_of_week_list:
            messages.warning(request, 'Vui lòng chọn ít nhất 1 Thứ.')
            return redirect('admin_schedule_management')

        # Update current record with first selected day
        schedule.day_of_week_begin = int(day_of_week_list[0])
        schedule.begin_time = request.POST['begin_time']
        schedule.end_time = request.POST['end_time']
        schedule.id_lecturer_id = request.POST['id_lecturer']
        schedule.save()

        # Keep all records in the same group in sync
        group_key = schedule.group_key or ''
        if not group_key:
            group_key = str(uuid.uuid4())
            schedule.group_key = group_key
            schedule.save(update_fields=['group_key'])

        # Update shared fields for the entire group
        Classroom.objects.filter(group_key=group_key).update(
            name=schedule.name,
            begin_date=schedule.begin_date,
            end_date=schedule.end_date,
            begin_time=schedule.begin_time,
            end_time=schedule.end_time,
            id_lecturer_id=schedule.id_lecturer_id,
        )

        desired_days = {int(d) for d in day_of_week_list}
        existing_days = set(Classroom.objects.filter(group_key=group_key).values_list('day_of_week_begin', flat=True))

        # Delete days removed
        days_to_delete = existing_days - desired_days
        if days_to_delete:
            Classroom.objects.filter(group_key=group_key, day_of_week_begin__in=list(days_to_delete)).delete()

        # Add missing days
        days_to_add = desired_days - existing_days
        if days_to_add:
            with transaction.atomic():
                for day in sorted(days_to_add):
                    Classroom.objects.create(
                        group_key=group_key,
                        name=schedule.name,
                        begin_date=schedule.begin_date,
                        end_date=schedule.end_date,
                        day_of_week_begin=int(day),
                        begin_time=schedule.begin_time,
                        end_time=schedule.end_time,
                        id_lecturer_id=schedule.id_lecturer_id,
                    )
        messages.success(request, 'Thay đổi thông tin thành công.')
        return redirect('admin_schedule_management')
    return render(request, 'admin/modal-popup/popup_edit_schedule.html', context)


@admin_required
def admin_schedule_group_get_info(request, group_key):
    qs = Classroom.objects.filter(group_key=group_key).order_by('day_of_week_begin', 'id_classroom')
    first = qs.first()
    if not first:
        return JsonResponse({'error': 'Không tìm thấy thời khóa biểu'}, status=404)
    days = list(qs.values_list('day_of_week_begin', flat=True))
    schedule_data = {
        'group_key': group_key,
        'id_classroom': first.id_classroom,
        'name': first.name,
        'begin_date': first.begin_date.strftime('%d/%m/%Y'),
        'end_date': first.end_date.strftime('%d/%m/%Y'),
        'day_of_week_begin_list': days,
        'begin_time': first.begin_time,
        'end_time': first.end_time,
        'id_lecturer': first.id_lecturer_id,
    }
    return JsonResponse({'schedule': schedule_data})


@admin_required
@require_POST
def admin_schedule_group_edit(request, group_key):
    day_of_week_list = request.POST.getlist('day_of_week_begin_list') or []
    if not day_of_week_list:
        messages.warning(request, 'Vui lòng chọn ít nhất 1 Thứ.')
        return redirect('admin_schedule_management')

    qs = Classroom.objects.filter(group_key=group_key).order_by('id_classroom')
    first = qs.first()
    if not first:
        messages.error(request, 'Không tìm thấy thời khóa biểu.')
        return redirect('admin_schedule_management')

    name = request.POST['name']
    begin_date = _parse_form_date(request.POST['begin_date'])
    end_date = _parse_form_date(request.POST['end_date'])
    begin_time = request.POST['begin_time']
    end_time = request.POST['end_time']
    id_lecturer = request.POST['id_lecturer']

    # Update shared fields for all records in group
    Classroom.objects.filter(group_key=group_key).update(
        name=name,
        begin_date=begin_date,
        end_date=end_date,
        begin_time=begin_time,
        end_time=end_time,
        id_lecturer_id=id_lecturer,
    )

    desired_days = {int(d) for d in day_of_week_list}
    existing_days = set(Classroom.objects.filter(group_key=group_key).values_list('day_of_week_begin', flat=True))

    # Delete removed days
    days_to_delete = existing_days - desired_days
    if days_to_delete:
        Classroom.objects.filter(group_key=group_key, day_of_week_begin__in=list(days_to_delete)).delete()

    # Add missing days
    days_to_add = desired_days - existing_days
    if days_to_add:
        with transaction.atomic():
            for day in sorted(days_to_add):
                Classroom.objects.create(
                    group_key=group_key,
                    name=name,
                    begin_date=begin_date,
                    end_date=end_date,
                    day_of_week_begin=int(day),
                    begin_time=begin_time,
                    end_time=end_time,
                    id_lecturer_id=id_lecturer,
                )

    messages.success(request, 'Thay đổi thông tin thành công.')
    return redirect('admin_schedule_management')


@admin_required
@require_POST
def admin_schedule_group_delete(request, group_key):
    Classroom.objects.filter(group_key=group_key).delete()
    return redirect('admin_schedule_management')


@admin_required
def admin_schedule_delete(request, id_classroom):
    Classroom.objects.filter(id_classroom=id_classroom).delete()
    return redirect('admin_schedule_management')


@admin_required
def admin_schedule_get_info(request, id_classroom):
    try:
        schedule = Classroom.objects.get(id_classroom=id_classroom)
        lecturer_id = schedule.id_lecturer_id
        lecturer_name = schedule.id_lecturer.staff_name if schedule.id_lecturer else ''
        schedule_data = {
            'id_classroom': schedule.id_classroom,
            'name': schedule.name,
            'begin_date': schedule.begin_date.strftime('%d/%m/%Y'),
            'end_date': schedule.end_date.strftime('%d/%m/%Y'),
            'day_of_week_begin': schedule.day_of_week_begin,
            'begin_time': schedule.begin_time,
            'end_time': schedule.end_time,
            'id_lecturer': lecturer_id,
            'lecturer_name': lecturer_name,
        }
        return JsonResponse({'schedule': schedule_data})
    except Classroom.DoesNotExist:
        return JsonResponse({'error': 'Không tìm thấy lớp học'}, status=404)


@admin_required
def admin_list_classroom_student_view(request):
    classroom_per_page = 10
    page_number = request.GET.get('page')
    search_query = request.GET.get('q', '')
    qs = Classroom.objects.filter(
        Q(id_classroom__icontains=search_query) | Q(name__icontains=search_query)
    ).order_by('group_key', 'id_classroom')

    grouped = {}
    for c in qs:
        key = c.group_key or str(c.id_classroom)
        g = grouped.get(key)
        if not g:
            grouped[key] = {
                'group_key': key,
                'id_classroom': c.id_classroom,
                'name': c.name,
                'begin_date': c.begin_date,
                'end_date': c.end_date,
                'begin_time': c.begin_time,
                'end_time': c.end_time,
                'id_lecturer': c.id_lecturer,
                'days': set([c.day_of_week_begin]),
                'classroom_ids': [c.id_classroom],
            }
        else:
            g['days'].add(c.day_of_week_begin)
            g['classroom_ids'].append(c.id_classroom)

    grouped_list = list(grouped.values())
    for g in grouped_list:
        g['days_sorted'] = sorted(list(g['days']))
        g['days_label'] = ', '.join([_weekday_label(d) for d in g['days_sorted']])
        g['student_count'] = StudentClassDetails.objects.filter(
            id_classroom_id__in=g['classroom_ids']
        ).values('id_student_id').distinct().count()
    
    grouped_list.sort(key=lambda x: (x['name'], x['begin_time'], x['group_key']))

    paginator = Paginator(grouped_list, classroom_per_page)
    page = paginator.get_page(page_number)
    context = {'list_classrooms': page, 'search_query': search_query}
    return render(request, 'admin/admin_list_classroom_student_management.html', context)


@admin_required
def admin_list_student_in_classroom_view(request, classroom_id):
    classroom = Classroom.objects.get(pk=classroom_id)
    group_key = classroom.group_key or ''
    
    if group_key:
        classroom_ids = list(Classroom.objects.filter(group_key=group_key).values_list('id_classroom', flat=True))
        students_in_class = StudentClassDetails.objects.filter(
            id_classroom_id__in=classroom_ids
        ).select_related('id_student').distinct('id_student_id').order_by('id_student_id')
        
        available_students = StudentInfo.objects.exclude(
            studentclassdetails__id_classroom_id__in=classroom_ids
        ).order_by('id_student')
    else:
        students_in_class = StudentClassDetails.objects.filter(id_classroom=classroom)
        available_students = StudentInfo.objects.exclude(
            studentclassdetails__id_classroom=classroom
        ).order_by('id_student')
    
    student_per_page = 10
    page_number = request.GET.get('page')
    paginator = Paginator(students_in_class, student_per_page)
    page = paginator.get_page(page_number)
    context = {
        'students_in_class': page,
        'classroom_id': classroom_id,
        'classroom': classroom,
        'available_students': available_students,
    }
    return render(request, 'admin/admin_list_student_classroom_management.html', context)


@admin_required
def admin_list_student_in_class_add_list(request, classroom_id):
    if request.method == 'POST':
        file_path = request.FILES['file_path']
        try:
            classroom = Classroom.objects.get(id_classroom=classroom_id)
        except Classroom.DoesNotExist:
            return render(request, 'error/error_template.html', {'error_message': 'Lớp học không tồn tại.'})

        group_key = classroom.group_key or ''
        
        if group_key:
            classroom_ids = list(Classroom.objects.filter(group_key=group_key).values_list('id_classroom', flat=True))
        else:
            classroom_ids = [classroom_id]

        workbook = openpyxl.load_workbook(file_path)
        sheet = workbook.active
        list_id_student = [row[0].value for row in sheet.iter_rows(min_row=2, max_col=1)]

        added = 0
        with transaction.atomic():
            for id_student in list_id_student:
                try:
                    student = StudentInfo.objects.get(id_student=id_student)
                except StudentInfo.DoesNotExist:
                    student = StudentInfo(id_student=id_student)
                    student.save()

                already_exists = StudentClassDetails.objects.filter(
                    id_classroom_id__in=classroom_ids,
                    id_student_id=student.id_student
                ).exists()
                
                if not already_exists:
                    for cid in classroom_ids:
                        StudentClassDetails.objects.create(
                            id_classroom_id=cid,
                            id_student_id=student.id_student
                        )
                    added += 1
        
        if len(classroom_ids) > 1:
            messages.success(request, f'Thêm {added} sinh viên vào {len(classroom_ids)} lớp học (cùng môn) thành công.')
        else:
            messages.success(request, f'Thêm {added} sinh viên vào lớp học thành công.')
        return redirect('admin_list_student_in_classroom', classroom_id)
    return render(request, 'admin/admin_list_student_classroom_management.html')


@admin_required
def admin_list_student_in_class_add(request, classroom_id):
    if request.method == 'POST':
        id_students = request.POST.getlist('id_students')
        if not id_students:
            messages.warning(request, 'Vui lòng chọn ít nhất 1 sinh viên.')
            return redirect('admin_list_student_in_classroom', classroom_id)

        classroom = Classroom.objects.get(id_classroom=classroom_id)
        group_key = classroom.group_key or ''
        
        if group_key:
            classroom_ids = list(Classroom.objects.filter(group_key=group_key).values_list('id_classroom', flat=True))
        else:
            classroom_ids = [classroom_id]

        added = 0
        existed = 0
        with transaction.atomic():
            for id_student in id_students:
                already_exists = StudentClassDetails.objects.filter(
                    id_classroom_id__in=classroom_ids,
                    id_student_id=id_student
                ).exists()
                
                if already_exists:
                    existed += 1
                    continue
                
                for cid in classroom_ids:
                    StudentClassDetails.objects.create(
                        id_classroom_id=cid,
                        id_student_id=id_student
                    )
                added += 1

        if added:
            if len(classroom_ids) > 1:
                messages.success(request, f'Thêm {added} sinh viên vào {len(classroom_ids)} lớp học (cùng môn) thành công.')
            else:
                messages.success(request, f'Thêm {added} sinh viên vào lớp học thành công.')
        if existed:
            messages.warning(request, f'{existed} sinh viên đã tồn tại trong lớp học.')
        return redirect('admin_list_student_in_classroom', classroom_id)
    return render(request, 'admin/modal-popup/popup_add_student_in_class.html')


@admin_required
def admin_list_student_in_class_delete(request, id_classroom, id_student):
    classroom = Classroom.objects.get(id_classroom=id_classroom)
    group_key = classroom.group_key or ''
    
    if group_key:
        classroom_ids = list(Classroom.objects.filter(group_key=group_key).values_list('id_classroom', flat=True))
    else:
        classroom_ids = [id_classroom]
    
    deleted_count = StudentClassDetails.objects.filter(
        id_student_id=id_student, 
        id_classroom_id__in=classroom_ids
    ).delete()[0]
    
    if deleted_count > 1:
        messages.success(request, f'Đã xóa sinh viên khỏi {deleted_count} lớp học (cùng môn).')
    elif deleted_count == 1:
        messages.success(request, 'Đã xóa sinh viên khỏi lớp học.')
    
    return redirect('admin_list_student_in_classroom', id_classroom)


@admin_required
def admin_list_student_in_class_delete_all(request, id_classroom):
    classroom = Classroom.objects.get(id_classroom=id_classroom)
    group_key = classroom.group_key or ''
    
    if group_key:
        classroom_ids = list(Classroom.objects.filter(group_key=group_key).values_list('id_classroom', flat=True))
    else:
        classroom_ids = [id_classroom]
    
    deleted_count = StudentClassDetails.objects.filter(id_classroom_id__in=classroom_ids).delete()[0]
    
    if len(classroom_ids) > 1:
        messages.success(request, f'Đã xóa tất cả sinh viên khỏi {len(classroom_ids)} lớp học (cùng môn).')
    else:
        messages.success(request, 'Đã xóa tất cả sinh viên khỏi lớp học.')
    
    return redirect('admin_list_student_in_classroom', id_classroom)


def capture(id, request):
    global CAPTURE_STATUS
    CAPTURE_STATUS = 0  # Sử dụng 'global' ở đầu hàm để thông báo rằng bạn muốn sử dụng biến toàn cục
    image_count = 0
    color = (0, 0, 255)  # BGR color for drawing rectangles
    thickness = 2  # Thickness of the rectangle
    model_test = AntiSpoofPredict(device_id)  # Define the AntiSpoofPredict object (assumed to be a valid class)
    capture = cv2.VideoCapture(0)  # Capture from camera at index 2 (can be adjusted)
    output_dir = f"./main/Dataset/FaceData/processed/{id}"
    os.makedirs(output_dir, exist_ok=True)
    while image_count < 300:
        ret, frame = capture.read()
        if not ret:
            break
        image_bbox = model_test.get_bbox(frame)  # Assuming `get_bbox` returns the bounding box of the face
        if image_bbox is not None:
            frame_h, frame_w = frame.shape[:2]
            x = max(0, image_bbox[0])
            y = max(0, image_bbox[1] - 50)
            w = min(frame_w, image_bbox[0] + image_bbox[2])
            h = min(frame_h, image_bbox[1] + image_bbox[3])

            cropped_face = frame[y:h, x:w]
            if cropped_face is not None and cropped_face.size != 0:
                cropped_face = cv2.resize(cropped_face, (160, 160))
                image_filename = os.path.join(output_dir, f"{id}_{image_count}.jpg")
                cv2.imwrite(image_filename, cropped_face)
                cv2.rectangle(frame, (x, y), (w, h), color, thickness)
                image_count += 1
                cv2.putText(frame, f"Image Count: {image_count}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                            (255, 255, 255), 1)
        _, buffer = cv2.imencode('.jpg', frame)
        if _:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n\r\n')

        if image_count >= 300:
            CAPTURE_STATUS = 1
    capture.release()
    cv2.destroyAllWindows()


def split_dataset(dataset, min_nrof_images_per_class, nrof_train_images_per_class):
    train_set = []
    test_set = []
    for cls in dataset:
        paths = cls.image_paths
        # Remove classes with less than min_nrof_images_per_class
        if len(paths) >= min_nrof_images_per_class:
            np.random.shuffle(paths)
            train_set.append(facenet.ImageClass(cls.name, paths[:nrof_train_images_per_class]))
            test_set.append(facenet.ImageClass(cls.name, paths[nrof_train_images_per_class:]))
    return train_set, test_set


# The main function
def main():
    global TRAIN_STATUS
    TRAIN_STATUS = 0
    model = 'main/Models/20180402-114759.pb'
    with tf.Graph().as_default():
        with tf.compat.v1.Session() as sess:
            np.random.seed(seed)
            if use_split_dataset:
                dataset_tmp = facenet.get_dataset(data_dir)
                train_set, test_set = split_dataset(dataset_tmp, min_nrof_images_per_class, nrof_train_images_per_class)
                if mode == 'TRAIN':
                    dataset = train_set
                elif mode == 'CLASSIFY':
                    dataset = test_set
            else:
                dataset = facenet.get_dataset(data_dir)

            # Check that there are at least one training image per class
            for cls in dataset:
                assert len(cls.image_paths) > 0, 'There must be at least one image for each class in the dataset'

            paths, labels = facenet.get_image_paths_and_labels(dataset)

            print('Number of classes: %d' % len(dataset))
            print('Number of images: %d' % len(paths))

            # Load the model
            print('Loading feature extraction model')
            facenet.load_model(model)

            # Get input and output tensors
            images_placeholder = tf.compat.v1.get_default_graph().get_tensor_by_name("input:0")
            embeddings = tf.compat.v1.get_default_graph().get_tensor_by_name("embeddings:0")
            phase_train_placeholder = tf.compat.v1.get_default_graph().get_tensor_by_name("phase_train:0")
            embedding_size = embeddings.get_shape()[1]

            # Run forward pass to calculate embeddings
            print('Calculating features for images')
            nrof_images = len(paths)
            nrof_batches_per_epoch = int(math.ceil(1.0 * nrof_images / batch_size))
            emb_array = np.zeros((nrof_images, embedding_size))
            for i in range(nrof_batches_per_epoch):
                start_index = i * batch_size
                end_index = min((i + 1) * batch_size, nrof_images)
                paths_batch = paths[start_index:end_index]
                images = facenet.load_data(paths_batch, False, False, image_size)
                feed_dict = {images_placeholder: images, phase_train_placeholder: False}
                emb_array[start_index:end_index, :] = sess.run(embeddings, feed_dict=feed_dict)

            classifier_filename_exp = os.path.expanduser(classifier_filename)

            if mode == 'TRAIN':
                # Train classifier
                print('Training classifier')
                model = SVC(kernel='linear', probability=True)
                model.fit(emb_array, labels)
                # Create a list of class names
                class_names = [cls.name.replace('_', ' ') for cls in dataset]

                # Saving classifier model
                with open(classifier_filename_exp, 'wb') as outfile:
                    pickle.dump((model, class_names), outfile)
                print('Saved classifier model to file "%s"' % classifier_filename_exp)
            TRAIN_STATUS = 1
            output_string = 'Number of classes: %d\nNumber of images: %d\nLoading feature extraction model' % (
                len(dataset), len(paths))
    return TRAIN_STATUS, output_string


@admin_required
def train(request):
    train_result, resuil = main()
    print(train_result, resuil)
    return JsonResponse({'train': train_result, 'resuil': resuil})


@admin_required
def live_video_feed(request, id_student):
    return StreamingHttpResponse(capture(id_student, request), content_type="multipart/x-mixed-replace;boundary=frame")


# Create a view to check the capture status
@admin_required
def check_capture_status(request):
    print(CAPTURE_STATUS)
    return JsonResponse({'capture_status': CAPTURE_STATUS})
