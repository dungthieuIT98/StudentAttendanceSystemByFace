import json
from pathlib import Path

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db import transaction

from main.models import BlogPost, Classroom, Role, StaffInfo, StaffRole, StudentClassDetails, StudentInfo


class Command(BaseCommand):
    help = "Import legacy seed data from Database/*.json and ensure admin login works."

    def handle(self, *args, **options):
        base_dir = Path(__file__).resolve().parents[3] / "Database"

        def load_json(filename):
            path = base_dir / filename
            return json.loads(path.read_text(encoding="utf-8"))

        roles = load_json("Role.json")
        staff = load_json("StaffInfo.json")
        staff_roles = load_json("StaffRole.json")
        students = load_json("StudentInfo.json")
        classrooms = load_json("Classroom.json")
        student_class_details = load_json("StudentClassDetails.json")
        blog_posts = load_json("BlogPost.json")

        with transaction.atomic():
            for item in roles:
                Role.objects.update_or_create(
                    id=item["id"],
                    defaults={"name": item["name"]},
                )

            for item in staff:
                password = item["password"]
                if item["id_staff"] == "admin":
                    password = make_password("admin123")

                StaffInfo.objects.update_or_create(
                    id_staff=item["id_staff"],
                    defaults={
                        "staff_name": item["staff_name"],
                        "email": item["email"],
                        "phone": item["phone"],
                        "address": item["address"],
                        "birthday": item["birthday"],
                        "password": password,
                    },
                )

            for item in staff_roles:
                StaffRole.objects.update_or_create(
                    id=item["id"],
                    defaults={
                        "staff_id": item["staff_id"],
                        "role_id": item["role_id"],
                    },
                )

            for item in students:
                StudentInfo.objects.update_or_create(
                    id_student=item["id_student"],
                    defaults={
                        "student_name": item["student_name"],
                        "email": item["email"],
                        "phone": item["phone"],
                        "address": item["address"],
                        "birthday": item["birthday"],
                        "PathImageFolder": item["PathImageFolder"],
                        "password": item["password"],
                    },
                )

            for item in classrooms:
                defaults = {
                    "name": item["name"],
                    "begin_date": item["begin_date"],
                    "end_date": item["end_date"],
                    "day_of_week_begin": item["day_of_week_begin"],
                    "begin_time": item["begin_time"],
                    "end_time": item["end_time"],
                    "id_lecturer_id": item["id_lecturer_id"],
                }
                Classroom.objects.update_or_create(
                    id_classroom=item["id_classroom"],
                    defaults=defaults,
                )

            for item in student_class_details:
                StudentClassDetails.objects.update_or_create(
                    id=item["id"],
                    defaults={
                        "id_classroom_id": item["id_classroom_id"],
                        "id_student_id": item["id_student_id"],
                    },
                )

            for item in blog_posts:
                BlogPost.objects.update_or_create(
                    id=item["id"],
                    defaults={
                        "title": item["title"],
                        "body": item["body"],
                        "type": item["type"],
                    },
                )

            User = get_user_model()
            user, _created = User.objects.update_or_create(
                username="admin",
                defaults={
                    "email": "admin@example.com",
                    "is_staff": True,
                    "is_superuser": True,
                },
            )
            user.set_password("admin123")
            user.save(update_fields=["password", "email", "is_staff", "is_superuser"])

        self.stdout.write(self.style.SUCCESS("Legacy data imported successfully."))
        self.stdout.write(self.style.SUCCESS("Admin login is ready: id_staff=admin, password=admin123"))
