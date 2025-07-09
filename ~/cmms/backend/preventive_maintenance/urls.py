from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MaintenancePlanViewSet,
    PMTaskViewSet,
    PMChecklistItemViewSet,
    PreventiveMaintenanceSOPViewSet
)

router = DefaultRouter()
router.register(r'maintenance-plans', MaintenancePlanViewSet, basename='maintenanceplan')
router.register(r'pm-tasks', PMTaskViewSet, basename='pmtask')
router.register(r'pm-checklist-items', PMChecklistItemViewSet, basename='pmchecklistitem')
router.register(r'pm-sops', PreventiveMaintenanceSOPViewSet, basename='pmsop')

urlpatterns = [
    path('', include(router.urls)),
]
