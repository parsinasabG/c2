from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone # For setting dates in actions
from .models import WorkOrderType, Priority, WorkOrder, WorkOrderTask
from .serializers import (
    WorkOrderTypeSerializer,
    PrioritySerializer,
    WorkOrderSerializer,
    WorkOrderTaskSerializer
)

class WorkOrderTypeViewSet(viewsets.ModelViewSet):
    queryset = WorkOrderType.objects.all().order_by('name')
    serializer_class = WorkOrderTypeSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['name', 'description']

class PriorityViewSet(viewsets.ModelViewSet):
    queryset = Priority.objects.all().order_by('level')
    serializer_class = PrioritySerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['name', 'description']

class WorkOrderViewSet(viewsets.ModelViewSet):
    queryset = WorkOrder.objects.all().select_related(
        'work_order_type', 'asset', 'priority',
        'reported_by', 'assigned_to_technician',
        'source_maintenance_plan', 'source_breakdown_report'
    ).prefetch_related('tasks').order_by('-created_at')
    serializer_class = WorkOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'asset': ['exact'],
        'asset__tag': ['exact', 'icontains'],
        'work_order_type': ['exact'],
        'priority': ['exact'],
        'status': ['exact', 'in'],
        'assigned_to_technician': ['exact', 'isnull'], # Allow filtering for unassigned
        'reported_by': ['exact'],
        'scheduled_start_date': ['date__gte', 'date__lte', 'range', 'isnull'],
        'actual_start_date': ['date__gte', 'date__lte', 'range', 'isnull'],
        'actual_end_date': ['date__gte', 'date__lte', 'range', 'isnull'],
        'created_at': ['date__gte', 'date__lte', 'range'],
        'source_maintenance_plan': ['exact', 'isnull'],
        'source_breakdown_report': ['exact', 'isnull'],
    }
    search_fields = ['work_order_id', 'title', 'description', 'asset__name', 'asset__tag']

    def perform_create(self, serializer):
        if not serializer.validated_data.get('reported_by') and self.request.user.is_authenticated:
            serializer.save(reported_by=self.request.user)
        else:
            serializer.save()

    @action(detail=True, methods=['post'], url_path='change-status')
    def change_status(self, request, pk=None):
        work_order = self.get_object()
        new_status = request.data.get('status')

        if not new_status:
            return Response({'error': 'New status not provided.'}, status=status.HTTP_400_BAD_REQUEST)

        valid_statuses = [choice[0] for choice in WorkOrder.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return Response({'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}, status=status.HTTP_400_BAD_REQUEST)

        # Business logic for status transitions
        if new_status == 'IN_PROGRESS' and not work_order.actual_start_date:
            work_order.actual_start_date = timezone.now()
        elif new_status in ['COMPLETED', 'CLOSED'] and not work_order.actual_end_date:
            work_order.actual_end_date = timezone.now()
            if not work_order.actual_start_date: # If started and completed at once
                 work_order.actual_start_date = work_order.actual_end_date

        work_order.status = new_status
        work_order.save()
        return Response(WorkOrderSerializer(work_order, context={'request': request}).data)

    @action(detail=True, methods=['post'], url_path='assign-technician')
    def assign_technician(self, request, pk=None):
        work_order = self.get_object()
        technician_id = request.data.get('technician_id')

        if not technician_id:
            return Response({'error': 'Technician ID not provided.'}, status=status.HTTP_400_BAD_REQUEST)

        User = settings.AUTH_USER_MODEL # Get the User model
        try:
            # Assuming technician_id is the PK of the User model
            technician = User.objects.get(pk=technician_id, is_staff=True) # Ensure they are staff
        except User.DoesNotExist:
            return Response({'error': 'Technician not found or is not staff.'}, status=status.HTTP_404_NOT_FOUND)

        work_order.assigned_to_technician = technician
        if work_order.status == 'NEW': # Or 'OPEN'
            work_order.status = 'ASSIGNED'
        work_order.save()
        return Response(WorkOrderSerializer(work_order, context={'request': request}).data)


class WorkOrderTaskViewSet(viewsets.ModelViewSet):
    queryset = WorkOrderTask.objects.all().select_related('work_order__asset').order_by('work_order', 'sequence_order')
    serializer_class = WorkOrderTaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    # Allow filtering by work_order UUID directly
    filterset_fields = ['work_order', 'status']
    search_fields = ['description', 'notes', 'work_order__title', 'work_order__work_order_id']

    # If you want to ensure tasks are created only for a specific work_order via nested URL
    # (e.g., /api/wo/work-orders/<work_order_pk>/tasks/), you would override perform_create:
    # def perform_create(self, serializer):
    #     work_order_pk = self.kwargs.get('work_order_pk') # From URL
    #     # Fetch work_order instance or raise error
    #     serializer.save(work_order_id=work_order_pk)

    # To list tasks for a specific work order if using nested URL:
    # def get_queryset(self):
    #     work_order_pk = self.kwargs.get('work_order_pk')
    #     return WorkOrderTask.objects.filter(work_order_id=work_order_pk).select_related('work_order__asset').order_by('sequence_order')
