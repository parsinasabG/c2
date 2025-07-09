from rest_framework import serializers
from .models import MaintenancePlan, PMTask, PMChecklistItem, PreventiveMaintenanceSOP
from assets.serializers import AssetSerializer # To show nested asset details if needed

class PMChecklistItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PMChecklistItem
        fields = '__all__'
        read_only_fields = ('uuid', 'created_at', 'updated_at')

class PMTaskSerializer(serializers.ModelSerializer):
    checklist_items = PMChecklistItemSerializer(many=True, read_only=True) # Read-only nested checklist items

    class Meta:
        model = PMTask
        fields = '__all__'
        read_only_fields = ('uuid', 'created_at', 'updated_at')

class PreventiveMaintenanceSOPSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreventiveMaintenanceSOP
        fields = '__all__'
        read_only_fields = ('uuid', 'created_at', 'updated_at', 'upload_date')
        # `document` field will be handled by DRF's FileField for uploads

class MaintenancePlanSerializer(serializers.ModelSerializer):
    # Nested serializers for related objects (read-only for listing/retrieval)
    pm_tasks = PMTaskSerializer(many=True, read_only=True)
    sops = PreventiveMaintenanceSOPSerializer(many=True, read_only=True)

    # To show asset details instead of just asset_id. Use this for read operations.
    # For write operations (create/update), you'd typically expect just the asset's UUID (asset_id).
    # One way to handle this is to have different serializers for read and write,
    # or to make `asset_details` read-only and use `asset` (PrimaryKeyRelatedField) for writes.
    asset_details = AssetSerializer(source='asset', read_only=True)

    # asset field will be a PrimaryKeyRelatedField by default for write operations
    # If you want to accept UUID for asset field on write:
    # asset = serializers.UUIDField(write_only=True)
    # You'd then need to handle fetching the Asset instance in create/update or use source='asset_id' if your FK is asset_id
    # Since our FK is `asset = models.ForeignKey(Asset, ...)` DRF will handle it with PK by default.

    class Meta:
        model = MaintenancePlan
        fields = [
            'uuid', 'asset', 'asset_details', 'name', 'description', 'schedule_type',
            'interval_days', 'usage_metric', 'usage_threshold',
            'condition_threshold_description', 'is_active',
            'pm_tasks', 'sops', 'created_at', 'updated_at'
        ]
        read_only_fields = ('uuid', 'created_at', 'updated_at', 'asset_details', 'pm_tasks', 'sops')
        # 'asset' field will be used for writing (expects PK/UUID of the asset)

    # If you need to customize create/update to handle nested writes for tasks/SOPs,
    # you would override the create() and update() methods here.
    # For now, pm_tasks and sops are read-only in this serializer.
    # Separate endpoints will be used to manage tasks and SOPs.
