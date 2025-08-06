from django.db import models

from vehicle.models import Vehicle


class ParkingLot(models.Model):
    name = models.CharField(max_length=255)
    capacity = models.IntegerField(default=10)
    charge_per_hour = models.DecimalField(max_digits=10, decimal_places=2)


class ParkingSlot(models.Model):
    parking_lot = models.ForeignKey(ParkingLot, on_delete=models.CASCADE)
    slot_number = models.IntegerField()
    is_available = models.BooleanField(default=True)


class Ticket(models.Model):
    parking_slot = models.ForeignKey(ParkingSlot, on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    entry_time = models.DateTimeField(auto_now_add=True)
    exit_time = models.DateTimeField(null=True)
    total_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
