from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MaintenancePlanViewSet,
    PMTaskViewSet,
    PMChecklistItemViewSet,
    PreventiveMaintenanceSOPViewSet
)

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'maintenance-plans', MaintenancePlanViewSet, basename='maintenanceplan')
router.register(r'pm-tasks', PMTaskViewSet, basename='pmtask')
router.register(r'pm-checklist-items', PMChecklistItemViewSet, basename='pmchecklistitem')
router.register(r'pm-sops', PreventiveMaintenanceSOPViewSet, basename='pmsop')

# The API URLs are now determined automatically by the router.
# These will be included under the /api/ prefix in the project's main urls.py
urlpatterns = [
    path('', include(router.urls)),
]
