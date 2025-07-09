from rest_framework import viewsets, permissions
from django_filters.rest_framework import DjangoFilterBackend

from .models import MaintenancePlan, PMTask, PMChecklistItem, PreventiveMaintenanceSOP
from .serializers import (
    MaintenancePlanSerializer,
    PMTaskSerializer,
    PMChecklistItemSerializer,
    PreventiveMaintenanceSOPSerializer
)

class MaintenancePlanViewSet(viewsets.ModelViewSet):
    queryset = MaintenancePlan.objects.all().select_related('asset').prefetch_related('pm_tasks__checklist_items', 'sops')
    serializer_class = MaintenancePlanSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['asset', 'schedule_type', 'is_active']
    search_fields = ['name', 'description', 'asset__name', 'asset__tag']

class PMTaskViewSet(viewsets.ModelViewSet):
    queryset = PMTask.objects.all().select_related('maintenance_plan__asset').prefetch_related('checklist_items', 'sops')
    serializer_class = PMTaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['maintenance_plan', 'maintenance_plan__asset', 'assigned_to_role']
    search_fields = ['description', 'maintenance_plan__name']

class PMChecklistItemViewSet(viewsets.ModelViewSet):
    queryset = PMChecklistItem.objects.all().select_related('pm_task__maintenance_plan__asset')
    serializer_class = PMChecklistItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['pm_task', 'pm_task__maintenance_plan', 'is_mandatory']
    search_fields = ['item_description', 'pm_task__description']

class PreventiveMaintenanceSOPViewSet(viewsets.ModelViewSet):
    queryset = PreventiveMaintenanceSOP.objects.all().select_related('maintenance_plan__asset', 'pm_task__maintenance_plan__asset')
    serializer_class = PreventiveMaintenanceSOPSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['maintenance_plan', 'pm_task', 'maintenance_plan__asset']
    search_fields = ['title', 'description']
