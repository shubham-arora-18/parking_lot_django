from django.urls import path
from .views import ParkVehicleAPI, RemoveVehicleAPI, CurrentParkingsAPI

urlpatterns = [
    path('park/', ParkVehicleAPI.as_view(), name='park-vehicle'),
    path('remove/', RemoveVehicleAPI.as_view(), name='remove-vehicle'),
    path('current/', CurrentParkingsAPI.as_view(), name='current-parkings'),
]