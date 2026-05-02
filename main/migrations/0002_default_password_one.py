from django.contrib.auth.hashers import make_password
from django.db import migrations


def set_default_password_one(apps, schema_editor):
    StaffInfo = apps.get_model('main', 'StaffInfo')
    StudentInfo = apps.get_model('main', 'StudentInfo')
    Role = apps.get_model('main', 'Role')
    StaffRole = apps.get_model('main', 'StaffRole')

    hashed = make_password('1')

    # Students: set all to default password "1"
    StudentInfo.objects.all().update(password=hashed)

    # Lecturers only (StaffInfo with Role name="Lecturer")
    lecturer_role = Role.objects.filter(name='Lecturer').first()
    if lecturer_role:
        lecturer_ids = StaffRole.objects.filter(role=lecturer_role).values_list('staff_id', flat=True)
        StaffInfo.objects.filter(id_staff__in=list(lecturer_ids)).update(password=hashed)


def noop_reverse(apps, schema_editor):
    # Irreversible: original passwords are unknown.
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(set_default_password_one, reverse_code=noop_reverse),
    ]

