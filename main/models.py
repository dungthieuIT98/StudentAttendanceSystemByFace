from datetime import time

from django.db import models

from django.db import models
from django.utils.translation import gettext_lazy as _
from ckeditor_uploader.fields import RichTextUploadingField


# Create your models here.
class StaffInfo(models.Model):
    id_staff = models.CharField(max_length=10, primary_key=True)
    staff_name = models.TextField()
    email = models.TextField()
    phone = models.TextField()
    address = models.TextField()
    birthday = models.DateField()
    password = models.TextField()
    roles = models.ManyToManyField('Role', through='StaffRole', related_name='staff_role')

    def __str__(self):
        return self.name


class Role(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name


class StaffRole(models.Model):
    staff = models.ForeignKey(StaffInfo, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.staff.name} - {self.role.name}"


class StudentInfo(models.Model):
    id_student = models.CharField(max_length=10, primary_key=True)
    student_name = models.TextField()
    email = models.TextField()
    phone = models.TextField()
    address = models.TextField()
    birthday = models.DateField()
    PathImageFolder = models.TextField()
    password = models.TextField()


class Classroom(models.Model):
    id_classroom = models.BigAutoField(primary_key=True)
    # Group multiple weekdays into one logical schedule record (UI shows 1 row)
    group_key = models.CharField(max_length=36, db_index=True, blank=True, default='')
    name = models.TextField()
    begin_date = models.DateField()
    end_date = models.DateField()
    day_of_week_begin = models.IntegerField()
    begin_time = models.TimeField()
    end_time = models.TimeField()
    id_lecturer = models.ForeignKey(
        StaffInfo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    students = models.ManyToManyField(StudentInfo, through='StudentClassDetails')

    @property
    def begin_period_code(self):
        """SA / CH theo giờ bắt đầu (trước 12:00 = SA)."""
        return 'SA' if self.begin_time < time(12, 0) else 'CH'

    @property
    def end_period_code(self):
        """SA / CH theo giờ kết thúc."""
        return 'SA' if self.end_time < time(12, 0) else 'CH'


class StudentClassDetails(models.Model):
    id_classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    id_student = models.ForeignKey(StudentInfo, on_delete=models.CASCADE)


class Attendance(models.Model):
    id_attendance = models.BigAutoField(primary_key=True)
    check_in_time = models.DateTimeField()
    attendance_status = models.IntegerField()
    id_classroom = models.ForeignKey('Classroom', on_delete=models.SET_NULL, null=True)
    id_student = models.ForeignKey('StudentInfo', on_delete=models.CASCADE)


class BlogPost(models.Model):
    TYPE_CHOICES = [
        ('SV', _('Sinh viên')),
        ('GV', _('Giảng viên')),
        ('ALL', _('Tất cả')),
    ]

    title = models.CharField(
        _("Blog Title"), max_length=250,
        null=False, blank=False
    )
    body = RichTextUploadingField()
    type = models.CharField(
        _("Type"), max_length=15,
        choices=TYPE_CHOICES, default='ALL'
    )

    def __str__(self):
        return self.title
