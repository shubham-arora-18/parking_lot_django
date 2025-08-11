from rest_framework import serializers
from django.utils import timezone
from decimal import Decimal
from .models import ParkingLot, ParkingSlot, Ticket
from vehicle.models import Vehicle


class ParkVehicleSerializer(serializers.Serializer):
    vehicle_id = serializers.IntegerField()
    parking_lot_id = serializers.IntegerField()
    entry_gate = serializers.IntegerField(default=1)

    def validate_vehicle_id(self, value):
        """Validate that vehicle exists"""
        try:
            vehicle = Vehicle.objects.get(id=value)
        except Vehicle.DoesNotExist:
            raise serializers.ValidationError("Vehicle not found")

        # Check if vehicle is already parked
        existing_ticket = Ticket.objects.filter(vehicle=vehicle, exit_time__isnull=True).first()
        if existing_ticket:
            raise serializers.ValidationError("Vehicle is already parked")

        return value

    def validate_parking_lot_id(self, value):
        """Validate that parking lot exists"""
        try:
            parking_lot = ParkingLot.objects.get(id=value)
        except ParkingLot.DoesNotExist:
            raise serializers.ValidationError("Parking lot not found")
        return value

    def validate(self, attrs):
        """Cross-field validation"""
        parking_lot_id = attrs.get('parking_lot_id')
        entry_gate = attrs.get('entry_gate')

        try:
            parking_lot = ParkingLot.objects.get(id=parking_lot_id)

            # Validate entry gate
            if not (1 <= entry_gate <= parking_lot.total_entry_gate):
                raise serializers.ValidationError({
                    'entry_gate': f'Entry gate must be between 1 and {parking_lot.total_entry_gate}'
                })

            # Check for available slots
            available_slot = ParkingSlot.objects.filter(
                parking_lot=parking_lot,
                is_available=True
            ).first()

            if not available_slot:
                raise serializers.ValidationError("No available parking slots")

        except ParkingLot.DoesNotExist:
            # This should be caught by validate_parking_lot_id, but just in case
            raise serializers.ValidationError("Parking lot not found")

        return attrs

    def create(self, validated_data):
        """Create a parking ticket"""
        vehicle = Vehicle.objects.get(id=validated_data['vehicle_id'])
        parking_lot = ParkingLot.objects.get(id=validated_data['parking_lot_id'])
        entry_gate = validated_data['entry_gate']

        # Find available parking slot
        available_slot = ParkingSlot.objects.filter(
            parking_lot=parking_lot,
            is_available=True
        ).first()

        # Mark slot as occupied
        available_slot.is_available = False
        available_slot.save()

        # Create ticket
        ticket = Ticket.objects.create(
            parking_slot=available_slot,
            vehicle=vehicle,
            entry_gate=entry_gate
        )

        return ticket


class RemoveVehicleSerializer(serializers.Serializer):
    ticket_id = serializers.IntegerField()

    def validate_ticket_id(self, value):
        """Validate that ticket exists and vehicle hasn't been removed"""
        try:
            ticket = Ticket.objects.get(id=value)
        except Ticket.DoesNotExist:
            raise serializers.ValidationError("Ticket not found")

        if ticket.exit_time:
            raise serializers.ValidationError("Vehicle has already been removed")

        return value

    def update(self, instance, validated_data):
        """Remove vehicle and calculate charges"""
        ticket = Ticket.objects.get(id=validated_data['ticket_id'])

        # Calculate charges
        exit_time = timezone.now()
        duration = exit_time - ticket.entry_time
        hours = duration.total_seconds() / 3600
        # Round up to next hour for partial hours
        hours_to_charge = int(hours) + (1 if hours % 1 > 0 else 0)

        total_charge = ticket.parking_slot.parking_lot.charge_per_hour * hours_to_charge

        # Update ticket
        ticket.exit_time = exit_time
        ticket.total_charge = total_charge
        ticket.save()

        # Mark slot as available
        ticket.parking_slot.is_available = True
        ticket.parking_slot.save()

        return ticket


class TicketResponseSerializer(serializers.ModelSerializer):
    """Serializer for ticket response data"""
    parking_slot_number = serializers.IntegerField(source='parking_slot.slot_number', read_only=True)
    parking_lot_name = serializers.CharField(source='parking_slot.parking_lot.name', read_only=True)
    parking_lot_id = serializers.IntegerField(source='parking_slot.parking_lot.id', read_only=True)
    charge_per_hour = serializers.DecimalField(
        source='parking_slot.parking_lot.charge_per_hour',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    duration_hours = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = [
            'id', 'entry_time', 'exit_time', 'total_charge', 'entry_gate',
            'parking_slot_number', 'parking_lot_name', 'parking_lot_id',
            'charge_per_hour', 'duration_hours'
        ]

    def get_duration_hours(self, obj):
        """Calculate duration in hours"""
        if obj.exit_time and obj.entry_time:
            duration = obj.exit_time - obj.entry_time
            return round(duration.total_seconds() / 3600, 2)
        return None


class CurrentParkingSerializer(serializers.ModelSerializer):
    """Serializer for current parking data"""
    vehicle_id = serializers.IntegerField(source='vehicle.id', read_only=True)
    vehicle_serial_number = serializers.CharField(source='vehicle.serial_number', read_only=True)
    vehicle_type = serializers.CharField(source='vehicle.type', read_only=True)
    parking_lot_name = serializers.CharField(source='parking_slot.parking_lot.name', read_only=True)
    parking_lot_id = serializers.IntegerField(source='parking_slot.parking_lot.id', read_only=True)
    slot_number = serializers.IntegerField(source='parking_slot.slot_number', read_only=True)
    charge_per_hour = serializers.DecimalField(
        source='parking_slot.parking_lot.charge_per_hour',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = Ticket
        fields = [
            'id', 'vehicle_id', 'vehicle_serial_number', 'vehicle_type',
            'parking_lot_name', 'parking_lot_id', 'slot_number',
            'entry_gate', 'entry_time', 'charge_per_hour'
        ]


class CurrentParkingsQuerySerializer(serializers.Serializer):
    """Serializer for query parameters"""
    parking_lot_id = serializers.IntegerField(required=False)

    def validate_parking_lot_id(self, value):
        """Validate that parking lot exists if provided"""
        if value is not None:
            try:
                ParkingLot.objects.get(id=value)
            except ParkingLot.DoesNotExist:
                raise serializers.ValidationError("Parking lot not found")
        return value
