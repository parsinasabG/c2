from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Avg, F, ExpressionWrapper, DurationField
# from django.utils import timezone # Not used in this version of asset_mttr

from .models import FaultCategory, RootCause, BreakdownReport
from assets.models import Asset # For custom action
from .serializers import (
    FaultCategorySerializer,
    RootCauseSerializer,
    BreakdownReportSerializer
)

class FaultCategoryViewSet(viewsets.ModelViewSet):
    queryset = FaultCategory.objects.all().order_by('name')
    serializer_class = FaultCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['name', 'description']

class RootCauseViewSet(viewsets.ModelViewSet):
    queryset = RootCause.objects.all().select_related('category').order_by('category__name', 'name')
    serializer_class = RootCauseSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category']
    search_fields = ['name', 'description', 'category__name']

class BreakdownReportViewSet(viewsets.ModelViewSet):
    queryset = BreakdownReport.objects.all().select_related(
        'asset', 'reported_by', 'work_order'
    ).prefetch_related(
        'identified_root_causes__category' # Prefetch category for root causes
    ).order_by('-report_time')
    serializer_class = BreakdownReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'asset': ['exact'],
        'asset__tag': ['exact', 'icontains'],
        'status': ['exact', 'in'],
        'severity': ['exact', 'in'],
        'report_time': ['date__gte', 'date__lte', 'range'],
        'downtime_started_at': ['date__gte', 'date__lte', 'range'],
        'downtime_ended_at': ['date__gte', 'date__lte', 'range'],
        'reported_by': ['exact'],
        'work_order': ['exact', 'isnull'],
        'identified_root_causes__name': ['icontains'],
        'identified_root_causes__category__name': ['icontains'],
    }
    search_fields = ['description_of_fault', 'resolution_details', 'root_cause_analysis', 'asset__name', 'asset__tag', 'work_order__work_order_id']

    def perform_create(self, serializer):
        if not serializer.validated_data.get('reported_by') and self.request.user.is_authenticated:
            serializer.save(reported_by=self.request.user)
        else:
            serializer.save()

    @action(detail=False, methods=['get'], url_path='asset-mttr/(?P<asset_pk>[^/.]+)')
    def asset_mttr(self, request, asset_pk=None):
        try:
            # Ensure asset_pk is a valid UUID if your Asset model uses UUIDs
            asset_uuid = uuid.UUID(asset_pk)
            asset = Asset.objects.get(pk=asset_uuid)
        except (Asset.DoesNotExist, ValueError): # ValueError for invalid UUID format
            return Response({"error": "Asset not found or invalid UUID."}, status=status.HTTP_404_NOT_FOUND)

        resolved_breakdowns = BreakdownReport.objects.filter(
            asset=asset,
            status__in=['RESOLVED', 'CLOSED'],
            downtime_started_at__isnull=False,
            downtime_ended_at__isnull=False
        ).annotate(
            repair_duration=ExpressionWrapper(F('downtime_ended_at') - F('downtime_started_at'), output_field=DurationField())
        )

        if not resolved_breakdowns.exists():
            return Response({
                "asset_name": asset.name,
                "asset_uuid": asset.uuid,
                "message": "No resolved breakdowns with downtime data for this asset.",
                "mttr_hours": None, # Explicitly None
                "total_resolved_breakdowns_with_downtime": 0
            }, status=status.HTTP_200_OK)

        average_repair_duration_result = resolved_breakdowns.aggregate(avg_duration=Avg('repair_duration'))

        avg_duration_obj = average_repair_duration_result.get('avg_duration')
        mttr_hours = None
        if avg_duration_obj:
            mttr_seconds = avg_duration_obj.total_seconds()
            mttr_hours = round(mttr_seconds / 3600, 2)

        return Response({
            "asset_name": asset.name,
            "asset_uuid": asset.uuid,
            "total_resolved_breakdowns_with_downtime": resolved_breakdowns.count(),
            "mttr_hours": mttr_hours
        })
