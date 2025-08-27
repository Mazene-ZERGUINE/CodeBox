from rest_framework.routers import DefaultRouter
from .views.core import CoreViewSet
from .views.task import SimpleTaskViewSet

router = DefaultRouter()
router.register(r"core", CoreViewSet, basename="core")
router.register(r"task", SimpleTaskViewSet, basename="task")

urlpatterns = router.urls
