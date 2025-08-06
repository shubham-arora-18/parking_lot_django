from decimal import Decimal

from .models import ParkingLot


def create_parking_lot(
    name: str, capacity: int, charge_per_hour: Decimal
) -> ParkingLot:
    return ParkingLot.objects.create(
        name=name, capacity=capacity, charge_per_hour=charge_per_hour
    )
