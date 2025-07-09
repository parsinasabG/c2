from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import FaultCategory, RootCause, BreakdownReport
from assets.serializers import AssetSerializer # For nested asset details

User = get_user_model()

class FaultCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FaultCategory
        fields = '__all__'
        read_only_fields = ('uuid', 'created_at', 'updated_at')

class RootCauseSerializer(serializers.ModelSerializer):
    # Optional: Show category name instead of ID for read operations
    category_name = serializers.StringRelatedField(source='category.name', read_only=True)

    class Meta:
        model = RootCause
        fields = '__all__' # Includes 'category' as ID for write, 'category_name' for read
        read_only_fields = ('uuid', 'created_at', 'updated_at', 'category_name')

class BreakdownReportSerializer(serializers.ModelSerializer):
    asset_details = AssetSerializer(source='asset', read_only=True)
    reported_by_username = serializers.StringRelatedField(source='reported_by.username', read_only=True, allow_null=True)

    # For write operations, we expect UUIDs for M2M fields
    identified_root_causes = serializers.PrimaryKeyRelatedField(
        queryset=RootCause.objects.all(),
        many=True,
        required=False,
        help_text="List of Root Cause UUIDs."
    )
    # For read operations, we can nest the full RootCause objects if desired
    identified_root_causes_details = RootCauseSerializer(source='identified_root_causes', many=True, read_only=True)

    downtime_duration_hours = serializers.FloatField(read_only=True) # From model property

    class Meta:
        model = BreakdownReport
        fields = [
            'uuid', 'asset', 'asset_details', 'reported_by', 'reported_by_username',
            'report_time', 'description_of_fault', 'severity', 'status',
            'downtime_started_at', 'downtime_ended_at', 'downtime_duration_hours',
            'resolution_details', 'root_cause_analysis',
            'identified_root_causes', 'identified_root_causes_details',
            'created_at', 'updated_at'
            # 'work_order' # Add when WorkOrder model/serializer exists
        ]
        read_only_fields = (
            'uuid', 'report_time', 'created_at', 'updated_at',
            'asset_details', 'reported_by_username',
            'identified_root_causes_details', 'downtime_duration_hours'
        )
        # 'asset' and 'reported_by' will expect PKs (or UUIDs if PK is UUID) for write operations.
        # 'identified_root_causes' is explicitly set up to expect a list of PKs/UUIDs.

    def validate_reported_by(self, value):
        # Ensure the user exists if provided
        # This is often handled by PrimaryKeyRelatedField by default if 'reported_by' was one,
        # but since it's a ForeignKey to settings.AUTH_USER_MODEL, this is a good check.
        if value and not User.objects.filter(pk=value.pk).exists():
            raise serializers.ValidationError("User not found.")
        return value

    def validate(self, data):
        """
        Check that downtime_ended_at is after downtime_started_at if both are provided.
        """
        started_at = data.get('downtime_started_at', getattr(self.instance, 'downtime_started_at', None))
        ended_at = data.get('downtime_ended_at', getattr(self.instance, 'downtime_ended_at', None))

        if started_at and ended_at and ended_at < started_at:
            raise serializers.ValidationError({"downtime_ended_at": "Downtime ended_at cannot be before started_at."})
        return data
