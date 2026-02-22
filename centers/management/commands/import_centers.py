import pandas as pd
from django.core.management.base import BaseCommand
from centers.models import Center, CenterMobile


class Command(BaseCommand):
    help = "Import centers from Excel file"

    def handle(self, *args, **kwargs):

        file_path = "centersjib.xlsx"  # put file in root (same as manage.py)

        df = pd.read_excel(file_path)

        for _, row in df.iterrows():

            if pd.isna(row.get("serial_no")):
                continue

            center, created = Center.objects.get_or_create(
                serial_no=int(row["serial_no"]),
                defaults={
                    "center_id": str(row["center_id"]).strip(),
                    "center_name": str(row["center_name"]).strip(),
                    "address": str(row["address"]).strip(),
                    "state": str(row["state"]).strip(),
                    "city": str(row["city"]).strip(),
                    "pincode": str(row["pincode"]).strip(),
                }
            )

            if pd.notna(row.get("mobile1")):
                CenterMobile.objects.get_or_create(
                    center=center,
                    mobile=str(row["mobile1"]).strip(),
                    defaults={"is_primary": True}
                )

            if pd.notna(row.get("mobile2")):
                CenterMobile.objects.get_or_create(
                    center=center,
                    mobile=str(row["mobile2"]).strip(),
                    defaults={"is_primary": False}
                )

        self.stdout.write(self.style.SUCCESS("Centers Imported Successfully ✅"))
