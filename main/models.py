from datetime import time

from django.db import models
from django.utils import dateformat
from django.utils import timezone as dj_tz

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
        return self.staff_name


class Role(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name


class StaffRole(models.Model):
    staff = models.ForeignKey(StaffInfo, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.staff.staff_name} - {self.role.name}"


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

    def classroom_ids_in_group(self):
        """Return all classroom IDs that share the same schedule group."""
        if not self.group_key:
            return [self.id_classroom]
        return list(Classroom.objects.filter(group_key=self.group_key).values_list('id_classroom', flat=True))


class StudentClassDetails(models.Model):
    id_classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    id_student = models.ForeignKey(StudentInfo, on_delete=models.CASCADE)


def _period_code_from_local_time(t):
    return 'SA' if t < time(12, 0) else 'CH'


def format_clock_sa_ch_from_datetime(dt):
    """Giờ địa phương dạng 'G:i:s SA|CH' (đồng bộ filter template)."""
    loc = dj_tz.localtime(dt)
    return f'{dateformat.format(loc, "G:i:s")} {_period_code_from_local_time(loc.time())}'


def format_full_check_in_display(dt):
    """Ngày + giờ điểm danh: 'd/m/Y G:i:s SA|CH'."""
    loc = dj_tz.localtime(dt)
    return (
        f'{dateformat.format(loc, "d/m/Y")} '
        f'{dateformat.format(loc, "G:i:s")} '
        f'{_period_code_from_local_time(loc.time())}'
    )


class Attendance(models.Model):
    ABSENT = 1
    PRESENT = 2
    LATE = 3

    id_attendance = models.BigAutoField(primary_key=True)
    check_in_time = models.DateTimeField()
    attendance_status = models.IntegerField()
    id_classroom = models.ForeignKey('Classroom', on_delete=models.SET_NULL, null=True)
    id_student = models.ForeignKey('StudentInfo', on_delete=models.CASCADE)

    @property
    def check_in_period_code(self):
        return _period_code_from_local_time(dj_tz.localtime(self.check_in_time).time())

    @property
    def check_in_clock_sa_ch(self):
        return format_clock_sa_ch_from_datetime(self.check_in_time)

    @property
    def check_in_display(self):
        return format_full_check_in_display(self.check_in_time)

    @property
    def status_label(self):
        return {
            self.ABSENT: 'Vắng',
            self.PRESENT: 'Đúng giờ',
            self.LATE: 'Trễ',
        }.get(self.attendance_status, 'Khác')

    @property
    def is_recorded(self):
        return self.attendance_status in (self.PRESENT, self.LATE)


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
