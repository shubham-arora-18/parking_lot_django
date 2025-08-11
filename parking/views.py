from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import ParkingLot, Ticket
from .serializers import (
    ParkVehicleSerializer,
    RemoveVehicleSerializer,
    TicketResponseSerializer,
    CurrentParkingSerializer,
    CurrentParkingsQuerySerializer
)


class ParkVehicleAPI(APIView):
    def post(self, request):
        serializer = ParkVehicleSerializer(data=request.data)

        if serializer.is_valid():
            ticket = serializer.save()
            response_serializer = TicketResponseSerializer(ticket)

            return Response({
                **response_serializer.data,
                'message': 'Vehicle parked successfully'
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RemoveVehicleAPI(APIView):
    def post(self, request):
        serializer = RemoveVehicleSerializer(data=request.data)

        if serializer.is_valid():
            # We use update method with a dummy instance since we're updating an existing ticket
            ticket = serializer.update(None, serializer.validated_data)
            response_serializer = TicketResponseSerializer(ticket)

            return Response({
                **response_serializer.data,
                'message': 'Vehicle removed successfully'
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CurrentParkingsAPI(APIView):
    def get(self, request):
        # Validate query parameters
        query_serializer = CurrentParkingsQuerySerializer(data=request.query_params)

        if not query_serializer.is_valid():
            return Response(query_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        parking_lot_id = query_serializer.validated_data.get('parking_lot_id')

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

        # Serialize the data
        serializer = CurrentParkingSerializer(current_tickets, many=True)

        return Response({
            'current_parkings': serializer.data,
            'total_count': len(serializer.data)
        }, status=status.HTTP_200_OK)
