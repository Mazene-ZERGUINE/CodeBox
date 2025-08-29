from rest_framework.routers import DefaultRouter
from .views.core import CoreViewSet
from .views.code_execution import CodeExecutionViewSet
from .views.code_with_files import CodeWithFilesViewSet

router = DefaultRouter()
router.register(r"core", CoreViewSet, basename="core")
router.register(r"task", CodeExecutionViewSet, basename="task")
router.register(r'file_task', CodeWithFilesViewSet, basename='file_task')

urlpatterns = router.urls
