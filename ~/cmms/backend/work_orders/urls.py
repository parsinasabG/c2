from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WorkOrderTypeViewSet,
    PriorityViewSet,
    WorkOrderViewSet,
    WorkOrderTaskViewSet
)

router = DefaultRouter()
router.register(r'types', WorkOrderTypeViewSet, basename='workordertype')
router.register(r'priorities', PriorityViewSet, basename='priority')
router.register(r'work-orders', WorkOrderViewSet, basename='workorder')
router.register(r'tasks', WorkOrderTaskViewSet, basename='workordertask')

urlpatterns = [
    path('', include(router.urls)),
]
