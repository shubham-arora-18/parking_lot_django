from django.db import models

from vehicle.constants import VehicleType


class Vehicle(models.Model):
    serial_number = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=VehicleType.choices)
    registered_at = models.DateTimeField(auto_now_add=True)
