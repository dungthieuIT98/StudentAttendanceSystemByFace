"""
Management command to fix student schedule links across all weekdays in a group.

This fixes the bug where students are only linked to some classroom records
(e.g., Monday only) and not all weekdays in the same subject group.

Usage:
    python manage.py fix_student_schedule_links
    python manage.py fix_student_schedule_links --dry-run
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from main.models import Classroom, StudentClassDetails


class Command(BaseCommand):
    help = 'Fix student schedule links: ensure students are linked to ALL weekdays in their schedule groups'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without applying them',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be saved'))
        
        # Get all groups (schedules with multiple weekdays)
        groups = {}
        for classroom in Classroom.objects.exclude(group_key='').order_by('group_key', 'day_of_week_begin'):
            group_key = classroom.group_key
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(classroom)
        
        self.stdout.write(f'\nFound {len(groups)} schedule groups to check')
        
        total_fixed = 0
        total_created = 0
        
        for group_key, classrooms in groups.items():
            if len(classrooms) <= 1:
                continue  # Skip single-day schedules
            
            subject_name = classrooms[0].name
            weekdays = [c.day_of_week_begin for c in classrooms]
            self.stdout.write(f'\n[*] Group: {subject_name} (days: {weekdays})')
            
            # Get all students linked to ANY classroom in this group
            all_student_ids = set(
                StudentClassDetails.objects
                .filter(id_classroom__in=classrooms)
                .values_list('id_student_id', flat=True)
            )
            
            if not all_student_ids:
                self.stdout.write(f'  [!] No students found in this group')
                continue
            
            self.stdout.write(f'  [+] Found {len(all_student_ids)} unique students')
            
            # For each classroom, ensure all students are linked
            group_fixed = 0
            group_created = 0
            
            for classroom in classrooms:
                existing_student_ids = set(
                    StudentClassDetails.objects
                    .filter(id_classroom=classroom)
                    .values_list('id_student_id', flat=True)
                )
                
                missing_student_ids = all_student_ids - existing_student_ids
                
                if missing_student_ids:
                    weekday_label = {
                        1: 'Mon', 2: 'Tue', 3: 'Wed', 4: 'Thu',
                        5: 'Fri', 6: 'Sat', 7: 'Sun'
                    }.get(classroom.day_of_week_begin, str(classroom.day_of_week_begin))
                    
                    self.stdout.write(
                        f'  [FIX] Day {weekday_label}: Adding {len(missing_student_ids)} missing student links'
                    )
                    
                    if not dry_run:
                        with transaction.atomic():
                            for student_id in missing_student_ids:
                                StudentClassDetails.objects.create(
                                    id_classroom=classroom,
                                    id_student_id=student_id,
                                )
                    
                    group_created += len(missing_student_ids)
                    group_fixed += 1
            
            if group_fixed > 0:
                total_fixed += 1
                total_created += group_created
                self.stdout.write(self.style.SUCCESS(f'  [OK] Fixed {group_created} student links'))
            else:
                self.stdout.write(f'  [OK] Already correct, no changes needed')
        
        # Also handle classrooms without group_key (legacy single-day schedules)
        self.stdout.write('\n\nChecking legacy schedules without group_key...')
        legacy_classrooms = Classroom.objects.filter(group_key='')
        self.stdout.write(f'Found {legacy_classrooms.count()} legacy classroom records')
        self.stdout.write('[INFO] These are fine - they are single-day schedules')
        
        # Summary
        self.stdout.write('\n' + '='*60)
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN COMPLETE - No changes were saved'))
        else:
            self.stdout.write(self.style.SUCCESS('MIGRATION COMPLETE'))
        
        self.stdout.write(f'\nSummary:')
        self.stdout.write(f'  - Schedule groups fixed: {total_fixed}')
        self.stdout.write(f'  - Student links created: {total_created}')
        
        if total_fixed > 0:
            if dry_run:
                self.stdout.write(f'\n[!] Run without --dry-run to apply these changes')
            else:
                self.stdout.write(f'\n[SUCCESS] Students can now see all weekday sessions!')
        else:
            self.stdout.write(f'\n[INFO] All schedules are already correct!')
