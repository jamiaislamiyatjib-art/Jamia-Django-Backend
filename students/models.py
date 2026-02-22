
import random
from django.db import models
from centers.models import Center
from datetime import datetime
from django.db import transaction
from django.db.models import Max
from decimal import Decimal

from django.db import models, transaction
from django.db.models.functions import Substr, Cast
from django.db.models import IntegerField

class Student(models.Model):
    RESULT_CHOICES = [('Pass', 'Pass'), ('Fail', 'Fail'), ('Supplie', 'Supplie')]
    DIVISION_CHOICES = [('First Division', 'First Division'), ('Second Division', 'Second Division'), ('Third Division', 'Third Division')]
    GENDER_CHOICES = [('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')]

    student_id = models.CharField(max_length=50, blank=True)
    roll_no = models.CharField(max_length=50, blank=True)
    enroll_no = models.CharField(max_length=50, blank=True, null=True)
    student_name = models.CharField(max_length=200)
    father_husband_name = models.CharField(max_length=200)
    student_class = models.CharField(max_length=50)
    session = models.CharField(max_length=50)
    medium = models.CharField(max_length=50)

    paper1 = models.PositiveIntegerField(null=True, blank=True)
    paper2 = models.PositiveIntegerField(null=True, blank=True)
    paper3 = models.PositiveIntegerField(null=True, blank=True)
    paper4 = models.PositiveIntegerField(null=True, blank=True)

    total = models.PositiveIntegerField(default=0)
    grand_total = models.PositiveIntegerField()
    avg_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, null=True, blank=True)
    division = models.CharField(max_length=30, choices=DIVISION_CHOICES, null=True, blank=True)

    city = models.CharField(max_length=100, null=True, blank=True)
    # center = models.ForeignKey(Center, on_delete=models.SET_NULL, null=True, blank=True, related_name="students")
    center = models.ForeignKey(
    Center,
    to_field='center_id',   
    db_column='center_id', 
    on_delete=models.SET_NULL,
    null=True,
    blank=True
)

    gender = models.CharField(max_length=20, choices=GENDER_CHOICES)
    place = models.CharField(max_length=100, blank=True, null=True)


    is_published = models.BooleanField(default=False)
    is_admit_card_published = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    
    
    def save(self, *args, **kwargs):

        START_NUMBER = 86500

        with transaction.atomic():

            # ================= AUTO STUDENT ID =================
            if not self.student_id:

                students = Student.objects.select_for_update().filter(
                    student_id__startswith="JIB"
                )

                last_number = START_NUMBER - 1

                for s in students:
                    if s.student_id and len(s.student_id) > 3:
                        num_part = s.student_id[3:]
                        if num_part.isdigit():
                            last_number = max(last_number, int(num_part))

                self.student_id = f"JIB{last_number + 1:05d}"


            # ================= AUTO ROLL NO (GLOBAL UNIQUE SAFE) =================
            
            if not self.roll_no:

                rolls = Student.objects.select_for_update().values_list("roll_no", flat=True)

                last_number = START_NUMBER - 1

                for r in rolls:
                    if r and str(r).isdigit():
                        num = int(r)

                        # 🔥 Only allow 5-digit numbers starting from 86500
                        if 86500 <= num <= 99999:
                            last_number = max(last_number, num)

                self.roll_no = str(last_number + 1)
                
            # ================= AUTO ENROLL NO =================
            if not self.enroll_no:

                year_suffix = datetime.now().year % 100

                enrolls = Student.objects.select_for_update().filter(
                    enroll_no__endswith=f"/{year_suffix}"
                ).values_list("enroll_no", flat=True)

                last_number = START_NUMBER - 1

                for e in enrolls:
                    if e and "/" in e:
                        number_part = e.split("/")[0]
                        if number_part.isdigit():
                            last_number = max(last_number, int(number_part))

                self.enroll_no = f"{last_number + 1:06d}/{year_suffix}"


            # ====================================================
            # ================= CLASS-WISE MARKS LOGIC ===========
            # ====================================================

            CLASS_PAPER_COUNT = {
                "IBTIDAI SAAL DOAM": 1,
                "IBTIDAI SAAL AWWAL": 1,
                "SANVIYA SAAL DOAM": 2,
                "SANVIYA SAAL AWWAL": 2,
                "ALIYA SAAL DOAM": 4,
                "ALIYA SAAL AWWAL": 4,
            }

            papers = [self.paper1, self.paper2, self.paper3, self.paper4]

            # required_papers = CLASS_PAPER_COUNT.get(self.student_class, 0)
            normalized_class = self.student_class.replace("_", " ").strip().upper()
            required_papers = CLASS_PAPER_COUNT.get(normalized_class, 0)
            required_marks = papers[:required_papers]

            # ===== No valid class =====
            if required_papers == 0:
                self.total = 0
                self.grand_total = 0
                self.avg_percentage = 0
                self.result = None
                self.division = None

            # ===== Required papers not fully entered =====
            elif any(mark is None for mark in required_marks):
                self.total = 0
                self.grand_total = required_papers * 100
                self.avg_percentage = 0
                self.result = None
                self.division = None

            # ===== Full Calculation =====
            else:
                self.total = sum(required_marks)
                self.grand_total = required_papers * 100

                self.avg_percentage = round(
                    (Decimal(self.total) / Decimal(self.grand_total)) * 100,
                    2
                )

                # Count subjects below passing marks (33)
                failed_subjects = len([m for m in required_marks if m < 33])

                if failed_subjects > 1:
                    self.result = "Fail"
                    self.division = None

                elif failed_subjects == 1:
                    self.result = "Supply"
                    self.division = None

                else:
                    self.result = "Pass"

                    if self.avg_percentage >= 60:
                        self.division = "First Division"
                    elif self.avg_percentage >= 45:
                        self.division = "Second Division"
                    else:
                        self.division = "Third Division"

            super().save(*args, **kwargs)

