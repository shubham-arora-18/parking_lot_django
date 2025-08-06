import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import ParkingLot, ParkingSlot

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ParkingLot)
def post_parking_lot_create(sender, created, instance, **kwargs):
    for i in range(instance.capacity):
        ParkingSlot.objects.create(parking_lot=instance, slot_number=i)

    print(f"Created {instance.capacity} parking slots for lot: {instance.name}")
