from django.db.models import TextChoices


class VehicleType(TextChoices):
    CAR = 'car'
    BIKE = 'bike'
