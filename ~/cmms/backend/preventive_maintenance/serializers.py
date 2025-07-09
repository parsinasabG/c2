from rest_framework import serializers
from .models import MaintenancePlan, PMTask, PMChecklistItem, PreventiveMaintenanceSOP
from assets.serializers import AssetSerializer

class PMChecklistItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PMChecklistItem
        fields = '__all__'
        read_only_fields = ('uuid', 'created_at', 'updated_at')

class PMTaskSerializer(serializers.ModelSerializer):
    checklist_items = PMChecklistItemSerializer(many=True, read_only=True)

    class Meta:
        model = PMTask
        fields = '__all__'
        read_only_fields = ('uuid', 'created_at', 'updated_at')

class PreventiveMaintenanceSOPSerializer(serializers.ModelSerializer):
    document_url = serializers.SerializerMethodField()

    class Meta:
        model = PreventiveMaintenanceSOP
        fields = [
            'uuid', 'maintenance_plan', 'pm_task', 'title', 'document',
            'document_url', 'version', 'upload_date', 'description',
            'created_at', 'updated_at'
        ]
        read_only_fields = ('uuid', 'created_at', 'updated_at', 'upload_date', 'document_url')

    def get_document_url(self, obj):
        request = self.context.get('request')
        if obj.document and request:
            return request.build_absolute_uri(obj.document.url)
        return None

class MaintenancePlanSerializer(serializers.ModelSerializer):
    pm_tasks = PMTaskSerializer(many=True, read_only=True)
    sops = PreventiveMaintenanceSOPSerializer(many=True, read_only=True, context={'request': None}) # Pass request for document_url
    asset_details = AssetSerializer(source='asset', read_only=True)

    class Meta:
        model = MaintenancePlan
        fields = [
            'uuid', 'asset', 'asset_details', 'name', 'description', 'schedule_type',
            'interval_days', 'usage_metric', 'usage_threshold',
            'condition_threshold_description', 'is_active',
            'pm_tasks', 'sops', 'created_at', 'updated_at'
        ]
        read_only_fields = ('uuid', 'created_at', 'updated_at', 'asset_details', 'pm_tasks', 'sops')

    # To pass request to nested SOP serializer for building full URLs
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # For nested SOPs, we need to ensure the request context is passed
        # This can be done by re-serializing 'sops' with context if not handled by default in older DRF versions
        # Or by ensuring context is passed down if DRF version supports it well.
        # A simpler way for this specific case is to ensure the context is available.
        # The 'sops' field in Meta already uses the SOPSerializer instance.
        # We need to ensure that instance gets the context.
        sops_serializer = PreventiveMaintenanceSOPSerializer(instance.sops.all(), many=True, context=self.context)
        representation['sops'] = sops_serializer.data
        return representation
