from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import FaultCategory, RootCause, BreakdownReport
from assets.serializers import AssetSerializer
# from work_orders.serializers import WorkOrderSerializer # Avoid circular import if WorkOrderSerializer imports this

User = get_user_model()

class FaultCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FaultCategory
        fields = '__all__'
        read_only_fields = ('uuid', 'created_at', 'updated_at')

class RootCauseSerializer(serializers.ModelSerializer):
    category_name = serializers.StringRelatedField(source='category.name', read_only=True, allow_null=True)

    class Meta:
        model = RootCause
        fields = '__all__'
        read_only_fields = ('uuid', 'created_at', 'updated_at', 'category_name')

class BreakdownReportSerializer(serializers.ModelSerializer):
    asset_details = AssetSerializer(source='asset', read_only=True)
    reported_by_username = serializers.StringRelatedField(source='reported_by.username', read_only=True, allow_null=True)

    identified_root_causes = serializers.PrimaryKeyRelatedField(
        queryset=RootCause.objects.all(),
        many=True,
        required=False,
        allow_null=True, # Allow empty list for M2M
        help_text="List of Root Cause UUIDs."
    )
    identified_root_causes_details = RootCauseSerializer(source='identified_root_causes', many=True, read_only=True)
    downtime_duration_hours = serializers.FloatField(read_only=True)

    # For work_order, expect UUID for write, provide basic details for read
    work_order_id_display = serializers.StringRelatedField(source='work_order.work_order_id', read_only=True, allow_null=True)
    # work_order = serializers.PrimaryKeyRelatedField(queryset=WorkOrder.objects.all(), allow_null=True, required=False, write_only=True)
    # PrimaryKeyRelatedField is default for FK, so 'work_order' field will handle UUID input.

    class Meta:
        model = BreakdownReport
        fields = [
            'uuid', 'asset', 'asset_details',
            'reported_by', 'reported_by_username',
            'report_time', 'description_of_fault', 'severity', 'status',
            'downtime_started_at', 'downtime_ended_at', 'downtime_duration_hours',
            'resolution_details', 'root_cause_analysis',
            'identified_root_causes', 'identified_root_causes_details',
            'work_order', 'work_order_id_display', # work_order for write, work_order_id_display for read
            'created_at', 'updated_at'
        ]
        read_only_fields = (
            'uuid', 'report_time', 'created_at', 'updated_at',
            'asset_details', 'reported_by_username',
            'identified_root_causes_details', 'downtime_duration_hours',
            'work_order_id_display'
        )

    def validate(self, data):
        # Get instance if available (for updates)
        instance = getattr(self, 'instance', None)

        downtime_started_at = data.get('downtime_started_at', getattr(instance, 'downtime_started_at', None))
        downtime_ended_at = data.get('downtime_ended_at', getattr(instance, 'downtime_ended_at', None))

        if downtime_started_at and downtime_ended_at and downtime_ended_at < downtime_started_at:
            raise serializers.ValidationError({"downtime_ended_at": "Downtime ended_at cannot be before started_at."})

        status = data.get('status', getattr(instance, 'status', None))
        resolution_details = data.get('resolution_details', getattr(instance, 'resolution_details', None))

        if status in ['RESOLVED', 'CLOSED']:
            if not resolution_details:
                raise serializers.ValidationError({'resolution_details': "Resolution details are required for resolved or closed breakdowns."})
            if not downtime_ended_at: # Making this check stricter in serializer
                raise serializers.ValidationError({'downtime_ended_at': "Downtime ended time is required for resolved or closed breakdowns."})
        return data
