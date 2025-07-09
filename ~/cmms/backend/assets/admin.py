from django.contrib import admin
from .models import Asset

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('name', 'tag', 'model', 'serial_number', 'location', 'criticality', 'installation_date', 'updated_at')
    search_fields = ('name', 'tag', 'serial_number', 'model', 'location')
    list_filter = ('criticality', 'installation_date', 'location', 'updated_at')
    readonly_fields = ('uuid', 'created_at', 'updated_at')
    date_hierarchy = 'installation_date'

    fieldsets = (
        (None, {
            'fields': ('uuid', 'name', 'tag')
        }),
        ('Details', {
            'fields': ('model', 'serial_number', 'location', 'criticality', 'installation_date')
        }),
        ('Timestamps', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at')
        }),
    )
