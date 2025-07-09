from django.contrib import admin
from .models import FaultCategory, RootCause, BreakdownReport

@admin.register(FaultCategory)
class FaultCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description_short', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    readonly_fields = ('uuid', 'created_at', 'updated_at')

    def description_short(self, obj):
        return obj.description[:75] + '...' if obj.description and len(obj.description) > 75 else obj.description
    description_short.short_description = 'Description'

@admin.register(RootCause)
class RootCauseAdmin(admin.ModelAdmin):
    list_display = ('name', 'category_link', 'description_short', 'created_at', 'updated_at')
    list_filter = ('category',)
    search_fields = ('name', 'description', 'category__name')
    readonly_fields = ('uuid', 'created_at', 'updated_at')
    list_select_related = ('category',)

    def description_short(self, obj):
        return obj.description[:75] + '...' if obj.description and len(obj.description) > 75 else obj.description
    description_short.short_description = 'Description'

    def category_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        if obj.category:
            link = reverse(f"admin:{obj.category._meta.app_label}_{obj.category._meta.model_name}_change", args=[obj.category.uuid])
            return format_html('<a href="{}">{}</a>', link, obj.category.name)
        return "-"
    category_link.short_description = 'Category'


@admin.register(BreakdownReport)
class BreakdownReportAdmin(admin.ModelAdmin):
    list_display = (
        'asset_link',
        'description_of_fault_short',
        'severity',
        'status',
        'report_time',
        'reported_by_user',
        'downtime_duration_hours_display',
        'updated_at'
    )
    list_filter = ('status', 'severity', 'asset', 'report_time', 'reported_by')
    search_fields = (
        'asset__name', 'asset__tag', 'description_of_fault',
        'resolution_details', 'root_cause_analysis', 'reported_by__username'
    )
    readonly_fields = ('uuid', 'created_at', 'updated_at', 'report_time', 'downtime_duration_hours')
    list_select_related = ('asset', 'reported_by')
    filter_horizontal = ('identified_root_causes',) # Better UI for ManyToMany

    fieldsets = (
        (None, {
            'fields': ('uuid', 'asset', ('severity', 'status'), 'description_of_fault')
        }),
        ('Reporting & Timing', {
            'fields': ('reported_by', 'report_time', 'downtime_started_at', 'downtime_ended_at', 'downtime_duration_hours')
        }),
        ('Analysis & Resolution', {
            'classes': ('collapse',),
            'fields': ('root_cause_analysis', 'identified_root_causes', 'resolution_details')
        }),
        ('Timestamps', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at'),
        }),
    )

    def description_of_fault_short(self, obj):
        return obj.description_of_fault[:75] + '...' if len(obj.description_of_fault) > 75 else obj.description_of_fault
    description_of_fault_short.short_description = 'Fault Description'

    def asset_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        link = reverse(f"admin:{obj.asset._meta.app_label}_{obj.asset._meta.model_name}_change", args=[obj.asset.uuid])
        return format_html('<a href="{}">{}</a>', link, obj.asset.name)
    asset_link.short_description = 'Asset'

    def reported_by_user(self,obj):
        return obj.reported_by.username if obj.reported_by else '-'
    reported_by_user.short_description = 'Reported By'

    def downtime_duration_hours_display(self, obj):
        duration = obj.downtime_duration_hours
        return f"{duration} hrs" if duration is not None else "-"
    downtime_duration_hours_display.short_description = 'Downtime (Hours)'
