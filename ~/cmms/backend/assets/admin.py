from django.contrib import admin
from .models import Asset

# Register your models here.
# Basic registration for Asset model
@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('name', 'tag', 'model', 'serial_number', 'location', 'criticality', 'installation_date', 'updated_at')
    search_fields = ('name', 'tag', 'serial_number', 'model', 'location')
    list_filter = ('criticality', 'installation_date', 'location')
    readonly_fields = ('uuid', 'created_at', 'updated_at')
