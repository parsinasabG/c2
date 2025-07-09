from rest_framework import viewsets, permissions
from django_filters.rest_framework import DjangoFilterBackend
from .models import FaultCategory, RootCause, BreakdownReport
from .serializers import (
    FaultCategorySerializer,
    RootCauseSerializer,
    BreakdownReportSerializer
)

class FaultCategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Fault Categories.
    """
    queryset = FaultCategory.objects.all().order_by('name')
    serializer_class = FaultCategorySerializer
    permission_classes = [permissions.IsAuthenticated] # Consider IsAdminUser for categories
    # Add search or filter fields if needed, e.g., search_fields = ['name']

class RootCauseViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Root Causes.
    Supports filtering by category.
    """
    queryset = RootCause.objects.all().select_related('category').order_by('category__name', 'name')
    serializer_class = RootCauseSerializer
    permission_classes = [permissions.IsAuthenticated] # Consider IsAdminUser for root causes
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category']
    search_fields = ['name', 'description']

class BreakdownReportViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Breakdown Reports.
    Supports filtering by asset, status, and severity.
    """
    queryset = BreakdownReport.objects.all().select_related(
        'asset', 'reported_by'
    ).prefetch_related(
        'identified_root_causes', 'identified_root_causes__category'
    ).order_by('-report_time')
    serializer_class = BreakdownReportSerializer
    permission_classes = [permissions.IsAuthenticated] # More granular permissions could be added
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'asset': ['exact'],
        'asset__tag': ['exact', 'icontains'],
        'asset__name': ['icontains'],
        'status': ['exact', 'in'],
        'severity': ['exact', 'in'],
        'report_time': ['date__gte', 'date__lte', 'range'],
        'downtime_started_at': ['date__gte', 'date__lte', 'range'],
        'downtime_ended_at': ['date__gte', 'date__lte', 'range'],
        'reported_by': ['exact'],
        'identified_root_causes__name': ['icontains'],
        'identified_root_causes__category__name': ['icontains'],
    }
    search_fields = ['description_of_fault', 'resolution_details', 'root_cause_analysis', 'asset__name', 'asset__tag']

    def perform_create(self, serializer):
        # Automatically set reported_by to the current user if not provided
        if not serializer.validated_data.get('reported_by') and self.request.user.is_authenticated:
            serializer.save(reported_by=self.request.user)
        else:
            serializer.save()

    # Example: Custom action to calculate overall MTTR for an asset (more complex, for future)
    # from rest_framework.decorators import action
    # from rest_framework.response import Response
    # from django.db.models import Avg, F, ExpressionWrapper, DurationField
    # from django.utils import timezone

    # @action(detail=False, methods=['get'], url_path='asset-mttr/(?P<asset_pk>[^/.]+)')
    # def asset_mttr(self, request, asset_pk=None):
    #     try:
    #         asset = Asset.objects.get(pk=asset_pk)
    #     except Asset.DoesNotExist:
    #         return Response({"error": "Asset not found"}, status=status.HTTP_404_NOT_FOUND)

    #     resolved_breakdowns = BreakdownReport.objects.filter(
    #         asset=asset,
    #         status__in=['RESOLVED', 'CLOSED'],
    #         downtime_started_at__isnull=False,
    #         downtime_ended_at__isnull=False
    #     ).annotate(
    #         repair_duration=ExpressionWrapper(F('downtime_ended_at') - F('downtime_started_at'), output_field=DurationField())
    #     )

    #     if not resolved_breakdowns.exists():
    #         return Response({"message": "No resolved breakdowns with downtime data for this asset."}, status=status.HTTP_200_OK)

    #     average_repair_duration = resolved_breakdowns.aggregate(avg_duration=Avg('repair_duration'))

    #     mttr_seconds = average_repair_duration['avg_duration'].total_seconds() if average_repair_duration['avg_duration'] else 0
    #     mttr_hours = round(mttr_seconds / 3600, 2)

    #     return Response({
    #         "asset_name": asset.name,
    #         "asset_uuid": asset.uuid,
    #         "total_resolved_breakdowns_with_downtime": resolved_breakdowns.count(),
    #         "mttr_hours": mttr_hours
    #     })
