from rest_framework.routers import DefaultRouter
from .views.core import CoreViewSet

router = DefaultRouter()
router.register(r"core", CoreViewSet, basename="core")

urlpatterns = router.urls
