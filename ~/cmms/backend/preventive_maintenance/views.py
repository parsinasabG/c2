from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend # For filtering

from .models import MaintenancePlan, PMTask, PMChecklistItem, PreventiveMaintenanceSOP
from .serializers import (
    MaintenancePlanSerializer,
    PMTaskSerializer,
    PMChecklistItemSerializer,
    PreventiveMaintenanceSOPSerializer
)

# TODO: Define more granular permissions if needed (e.g., IsAdminOrReadOnly, IsOwnerOrReadOnly)
# For now, IsAuthenticated allows any logged-in user to perform CRUD.

class MaintenancePlanViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Maintenance Plans.
    Allows CRUD operations and filtering by asset UUID.
    """
    queryset = MaintenancePlan.objects.all().select_related('asset').prefetch_related('pm_tasks', 'sops')
    serializer_class = MaintenancePlanSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['asset', 'schedule_type', 'is_active'] # e.g., /api/maintenance-plans/?asset=<asset_uuid>

class PMTaskViewSet(viewsets.ModelViewSet):
    """
    API endpoint for PM Tasks.
    Allows CRUD operations and filtering by maintenance plan UUID.
    """
    queryset = PMTask.objects.all().select_related('maintenance_plan').prefetch_related('checklist_items', 'sops')
    serializer_class = PMTaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['maintenance_plan'] # e.g., /api/pm-tasks/?maintenance_plan=<plan_uuid>

class PMChecklistItemViewSet(viewsets.ModelViewSet):
    """
    API endpoint for PM Checklist Items.
    Allows CRUD operations and filtering by PM task UUID.
    """
    queryset = PMChecklistItem.objects.all().select_related('pm_task')
    serializer_class = PMChecklistItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['pm_task'] # e.g., /api/pm-checklist-items/?pm_task=<task_uuid>

class PreventiveMaintenanceSOPViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Preventive Maintenance SOPs.
    Allows CRUD operations and filtering by maintenance plan or PM task UUID.
    """
    queryset = PreventiveMaintenanceSOP.objects.all().select_related('maintenance_plan', 'pm_task')
    serializer_class = PreventiveMaintenanceSOPSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['maintenance_plan', 'pm_task'] # e.g., /api/pm-sops/?maintenance_plan=<plan_uuid>

    # Example for handling file uploads with SOPs (if not handled by default by DRF with ModelViewSet)
    # def perform_create(self, serializer):
    #     serializer.save(document=self.request.data.get('document'))

    # def perform_update(self, serializer):
    #     serializer.save(document=self.request.data.get('document', serializer.instance.document))

# Note: For more complex scenarios, such as creating tasks or checklist items directly
# under a specific plan or task (e.g., /api/maintenance-plans/<plan_pk>/tasks/),
# you might use nested routers (e.g., from rest_framework_nested.routers) or custom actions.
# For now, these are standard ModelViewSets.
#
# Also, ensure 'django-filter' is added to requirements.txt and INSTALLED_APPS if using DjangoFilterBackend.
# I will add 'django-filter' to requirements.txt in a subsequent step.
