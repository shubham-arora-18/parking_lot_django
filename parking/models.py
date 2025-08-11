from django.db import models

from vehicle.models import Vehicle
from django.core.exceptions import ValidationError


class ParkingLot(models.Model):
    name = models.CharField(max_length=255)
    capacity = models.IntegerField(default=10)
    charge_per_hour = models.DecimalField(max_digits=10, decimal_places=2)
    total_entry_gate = models.IntegerField(default=1)


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
    entry_gate = models.IntegerField(default=0)

    def clean(self):
        super().clean()
        if self.parking_slot and self.parking_slot.parking_lot:
            max_gates = self.parking_slot.parking_lot.total_entry_gate
            if not (1 <= self.entry_gate <= max_gates):
                raise ValidationError({
                    'entry_gate': f'Entry gate must be between 1 and {max_gates}'
                })

    def save(self, *args, **kwargs):
        self.full_clean()  # This calls clean() method
        super().save(*args, **kwargs)


