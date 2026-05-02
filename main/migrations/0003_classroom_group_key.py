import uuid

from django.db import migrations, models


def backfill_group_key(apps, schema_editor):
    Classroom = apps.get_model('main', 'Classroom')
    for c in Classroom.objects.filter(group_key='').iterator():
        c.group_key = str(uuid.uuid4())
        c.save(update_fields=['group_key'])


class Migration(migrations.Migration):
    dependencies = [
        ('main', '0002_default_password_one'),
    ]

    operations = [
        migrations.AddField(
            model_name='classroom',
            name='group_key',
            field=models.CharField(blank=True, db_index=True, default='', max_length=36),
        ),
        migrations.RunPython(backfill_group_key, reverse_code=migrations.RunPython.noop),
    ]

