from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import WorkOrderType, Priority, WorkOrder, WorkOrderTask
from assets.serializers import AssetSerializer
from preventive_maintenance.serializers import MaintenancePlanSerializer
from corrective_maintenance.serializers import BreakdownReportSerializer
# from accounts.serializers import UserSerializer # Placeholder

User = get_user_model()

class WorkOrderTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkOrderType
        fields = '__all__'
        read_only_fields = ('uuid', 'created_at', 'updated_at')

class PrioritySerializer(serializers.ModelSerializer):
    class Meta:
        model = Priority
        fields = '__all__'
        read_only_fields = ('uuid', 'created_at', 'updated_at')

class WorkOrderTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkOrderTask
        fields = '__all__'
        read_only_fields = ('uuid', 'created_at', 'updated_at')

class WorkOrderSerializer(serializers.ModelSerializer):
    work_order_type_details = WorkOrderTypeSerializer(source='work_order_type', read_only=True)
    asset_details = AssetSerializer(source='asset', read_only=True, allow_null=True)
    priority_details = PrioritySerializer(source='priority', read_only=True, allow_null=True)
    reported_by_details = serializers.StringRelatedField(source='reported_by.username', read_only=True, allow_null=True)
    assigned_to_technician_details = serializers.StringRelatedField(source='assigned_to_technician.username', read_only=True, allow_null=True)

    source_maintenance_plan_details = MaintenancePlanSerializer(source='source_maintenance_plan', read_only=True, allow_null=True)
    source_breakdown_report_details = BreakdownReportSerializer(source='source_breakdown_report', read_only=True, allow_null=True)

    tasks = WorkOrderTaskSerializer(many=True, read_only=True)

    # Ensure related fields are writeable by their PK (UUID in this case)
    # These allow setting the FK by passing the UUID of the related object.
    # DRF handles this by default for ForeignKey if not specified, but being explicit can be clearer.
    asset = serializers.UUIDField(source='asset.uuid', allow_null=True, required=False, write_only=True)
    work_order_type = serializers.UUIDField(source='work_order_type.uuid', write_only=True)
    priority = serializers.UUIDField(source='priority.uuid', allow_null=True, required=False, write_only=True)
    reported_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), allow_null=True, required=False, write_only=True)
    assigned_to_technician = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(is_staff=True), allow_null=True, required=False, write_only=True)
    source_maintenance_plan = serializers.UUIDField(source='source_maintenance_plan.uuid', allow_null=True, required=False, write_only=True)
    source_breakdown_report = serializers.UUIDField(source='source_breakdown_report.uuid', allow_null=True, required=False, write_only=True)


    class Meta:
        model = WorkOrder
        fields = [
            'uuid', 'work_order_id', 'title', 'description',
            'work_order_type', 'work_order_type_details',
            'asset', 'asset_details',
            'priority', 'priority_details',
            'status',
            'reported_by', 'reported_by_details',
            'assigned_to_technician', 'assigned_to_technician_details',
            'required_skills',
            'estimated_hours', 'actual_hours',
            'scheduled_start_date', 'scheduled_end_date',
            'actual_start_date', 'actual_end_date',
            'completion_notes',
            'source_maintenance_plan', 'source_maintenance_plan_details',
            'source_breakdown_report', 'source_breakdown_report_details',
            'tasks',
            'created_at', 'updated_at'
        ]
        read_only_fields = (
            'uuid', 'work_order_id', 'created_at', 'updated_at',
            'work_order_type_details', 'asset_details', 'priority_details',
            'reported_by_details', 'assigned_to_technician_details',
            'source_maintenance_plan_details', 'source_breakdown_report_details',
            'tasks'
        )

    def validate_asset(self, value):
        # value here is the UUID passed for the asset
        if value:
            try:
                return Asset.objects.get(uuid=value)
            except Asset.DoesNotExist:
                raise serializers.ValidationError("Asset with this UUID does not exist.")
        return None

    def validate_work_order_type(self, value):
        try:
            return WorkOrderType.objects.get(uuid=value)
        except WorkOrderType.DoesNotExist:
            raise serializers.ValidationError("WorkOrderType with this UUID does not exist.")

    def validate_priority(self, value):
        if value:
            try:
                return Priority.objects.get(uuid=value)
            except Priority.DoesNotExist:
                raise serializers.ValidationError("Priority with this UUID does not exist.")
        return None

    def validate_source_maintenance_plan(self, value):
        if value:
            try:
                return MaintenancePlan.objects.get(uuid=value)
            except MaintenancePlan.DoesNotExist:
                raise serializers.ValidationError("MaintenancePlan with this UUID does not exist.")
        return None

    def validate_source_breakdown_report(self, value):
        if value:
            try:
                # Assuming BreakdownReport also uses UUID as PK
                return BreakdownReport.objects.get(uuid=value)
            except BreakdownReport.DoesNotExist:
                raise serializers.ValidationError("BreakdownReport with this UUID does not exist.")
        return None

    def validate(self, data):
        instance = getattr(self, 'instance', None)

        # Date validations
        scheduled_start = data.get('scheduled_start_date', getattr(instance, 'scheduled_start_date', None))
        scheduled_end = data.get('scheduled_end_date', getattr(instance, 'scheduled_end_date', None))
        if scheduled_start and scheduled_end and scheduled_end < scheduled_start:
            raise serializers.ValidationError({"scheduled_end_date": "Scheduled end date cannot be before scheduled start date."})

        actual_start = data.get('actual_start_date', getattr(instance, 'actual_start_date', None))
        actual_end = data.get('actual_end_date', getattr(instance, 'actual_end_date', None))
        if actual_start and actual_end and actual_end < actual_start:
            raise serializers.ValidationError({"actual_end_date": "Actual end date cannot be before actual start date."})

        # Source link validation
        source_pm = data.get('source_maintenance_plan', getattr(instance, 'source_maintenance_plan', None))
        source_br = data.get('source_breakdown_report', getattr(instance, 'source_breakdown_report', None))
        if source_pm and source_br:
            raise serializers.ValidationError("A work order cannot be linked to both a Maintenance Plan and a Breakdown Report simultaneously.")

        return data

    def create(self, validated_data):
        # Pop UUID-based FK sources before passing to super().create()
        # DRF expects actual model instances for FKs when creating.
        # Our validate_<field_name> methods already convert UUIDs to instances.
        # So, validated_data should already have the correct instances.
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Similar to create, ensure FKs are instances.
        return super().update(instance, validated_data)
