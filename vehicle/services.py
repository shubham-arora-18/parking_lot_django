from .models import Vehicle


def register_vehicle(serial_number: str, vehicle_type: str) -> Vehicle:
    return Vehicle.objects.create(
        serial_number=serial_number, type=vehicle_type
    )
