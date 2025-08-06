from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from parking.models import ParkingLot
from parking.services import create_parking_lot


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        with transaction.atomic():
            ParkingLot.objects.all().delete()

            for i in range(5):
                create_parking_lot(
                    name=f"lot{i}", capacity=10, charge_per_hour=Decimal(20)
                )

            self.stdout.write(self.style.SUCCESS("Database initialized successfully"))
