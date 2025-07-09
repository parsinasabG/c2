from rest_framework import serializers
from .models import Asset

class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = [
            'uuid',
            'name',
            'tag',
            'model',
            'serial_number',
            'location',
            'criticality',
            'installation_date',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ('uuid', 'created_at', 'updated_at')
