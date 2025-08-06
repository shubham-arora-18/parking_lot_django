from rest_framework import viewsets

from vehicle.models import Vehicle
from vehicle.serializers import VehicleSerializer


class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
