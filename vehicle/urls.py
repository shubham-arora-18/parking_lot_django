from rest_framework.routers import DefaultRouter

from vehicle.views import VehicleViewSet

router = DefaultRouter()
router.register(r'vehicles', VehicleViewSet)

urlpatterns = router.urls
