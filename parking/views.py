from datetime import datetime
from decimal import Decimal
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import ParkingLot, ParkingSlot, Ticket
from django.core.exceptions import ValidationError
from vehicle.models import Vehicle


class ParkVehicleAPI(APIView):
    def post(self, request):
        vehicle_id = request.data.get('vehicle_id')
        parking_lot_id = request.data.get('parking_lot_id')
        entry_gate = request.data.get('entry_gate', 0)  # Default to gate 0

        if not vehicle_id or not parking_lot_id:
            return Response(
                {'error': 'vehicle_id and parking_lot_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get vehicle and parking lot
        vehicle = get_object_or_404(Vehicle, id=vehicle_id)
        parking_lot = get_object_or_404(ParkingLot, id=parking_lot_id)

        # Validate entry gate
        if not (1 <= entry_gate <= parking_lot.total_entry_gate):
            return Response(
                {'error': f'Entry gate must be between 1 and {parking_lot.total_entry_gate}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if vehicle is already parked
        existing_ticket = Ticket.objects.filter(vehicle=vehicle, exit_time__isnull=True).first()
        if existing_ticket:
            return Response(
                {'error': 'Vehicle is already parked'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Find available parking slot
        available_slot = ParkingSlot.objects.filter(
            parking_lot=parking_lot,
            is_available=True
        ).first()

        if not available_slot:
            return Response(
                {'error': 'No available parking slots'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create ticket and mark slot as occupied
        available_slot.is_available = False
        available_slot.save()

        try:
            ticket = Ticket.objects.create(
                parking_slot=available_slot,
                vehicle=vehicle,
                entry_gate=entry_gate
            )
        except ValidationError as e:
            # Rollback slot availability if ticket creation fails
            available_slot.is_available = True
            available_slot.save()
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({
            'ticket_id': ticket.id,
            'parking_slot': available_slot.slot_number,
            'entry_gate': ticket.entry_gate,
            'entry_time': ticket.entry_time,
            'message': 'Vehicle parked successfully'
        }, status=status.HTTP_201_CREATED)


class RemoveVehicleAPI(APIView):
    def post(self, request):
        ticket_id = request.data.get('ticket_id')

        if not ticket_id:
            return Response(
                {'error': 'ticket_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get the ticket
        ticket = get_object_or_404(Ticket, id=ticket_id)

        if ticket.exit_time:
            return Response(
                {'error': 'Vehicle has already been removed'},
                status=status.HTTP_400_BAD_REQUEST
            )

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

        return Response({
            'ticket_id': ticket.id,
            'entry_time': ticket.entry_time,
            'exit_time': ticket.exit_time,
            'duration_hours': round(hours, 2),
            'total_charge': ticket.total_charge,
            'message': 'Vehicle removed successfully'
        }, status=status.HTTP_200_OK)


class CurrentParkingsAPI(APIView):
    def get(self, request):
        parking_lot_id = request.query_params.get('parking_lot_id')

        # Filter by parking lot if specified
        if parking_lot_id:
            parking_lot = get_object_or_404(ParkingLot, id=parking_lot_id)
            current_tickets = Ticket.objects.filter(
                exit_time__isnull=True,
                parking_slot__parking_lot=parking_lot
            ).select_related('vehicle', 'parking_slot', 'parking_slot__parking_lot')
        else:
            # Get all current parkings across all lots
            current_tickets = Ticket.objects.filter(
                exit_time__isnull=True
            ).select_related('vehicle', 'parking_slot', 'parking_slot__parking_lot')

        parkings_data = []
        for ticket in current_tickets:
            parkings_data.append({
                'ticket_id': ticket.id,
                'vehicle_id': ticket.vehicle.id,
                'vehicle_serial_number': ticket.vehicle.serial_number,
                'vehicle_type': ticket.vehicle.type,
                'parking_lot_name': ticket.parking_slot.parking_lot.name,
                'parking_lot_id': ticket.parking_slot.parking_lot.id,
                'slot_number': ticket.parking_slot.slot_number,
                'entry_gate': ticket.entry_gate,
                'entry_time': ticket.entry_time,
                'charge_per_hour': ticket.parking_slot.parking_lot.charge_per_hour
            })

        return Response({
            'current_parkings': parkings_data,
            'total_count': len(parkings_data)
        }, status=status.HTTP_200_OK)