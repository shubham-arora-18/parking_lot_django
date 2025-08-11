from django.contrib import admin
from .models import ParkingLot, ParkingSlot


@admin.register(ParkingLot)
class ParkingLotAdmin(admin.ModelAdmin):
    list_display = ['name', 'capacity', 'charge_per_hour', 'total_entry_gate']
    search_fields = ['name']


@admin.register(ParkingSlot)
class ParkingSlotAdmin(admin.ModelAdmin):
    list_display = ['parking_lot', 'slot_number', 'is_available']
    search_fields = ['name']