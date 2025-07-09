from django.contrib import admin
from .models import MaintenancePlan, PMTask, PMChecklistItem, PreventiveMaintenanceSOP

@admin.register(MaintenancePlan)
class MaintenancePlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'asset', 'schedule_type', 'interval_days', 'usage_threshold', 'is_active', 'updated_at')
    list_filter = ('schedule_type', 'is_active', 'asset')
    search_fields = ('name', 'description', 'asset__name', 'asset__tag')
    readonly_fields = ('uuid', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('uuid', 'name', 'asset', 'description', 'is_active')
        }),
        ('Schedule Details', {
            'classes': ('collapse',),
            'fields': ('schedule_type', 'interval_days', 'usage_metric', 'usage_threshold', 'condition_threshold_description'),
        }),
        ('Timestamps', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at'),
        }),
    )

@admin.register(PMTask)
class PMTaskAdmin(admin.ModelAdmin):
    list_display = ('description_short', 'maintenance_plan_link', 'assigned_to_role', 'estimated_duration_hours', 'sequence_order', 'updated_at')
    list_filter = ('maintenance_plan__asset', 'assigned_to_role', 'maintenance_plan')
    search_fields = ('description', 'maintenance_plan__name', 'maintenance_plan__asset__name')
    readonly_fields = ('uuid', 'created_at', 'updated_at')
    list_select_related = ('maintenance_plan', 'maintenance_plan__asset')

    def description_short(self, obj):
        return obj.description[:75] + '...' if len(obj.description) > 75 else obj.description
    description_short.short_description = 'Description'

    def maintenance_plan_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        link = reverse(f"admin:{obj.maintenance_plan._meta.app_label}_{obj.maintenance_plan._meta.model_name}_change", args=[obj.maintenance_plan.uuid])
        return format_html('<a href="{}">{}</a>', link, obj.maintenance_plan)
    maintenance_plan_link.short_description = 'Maintenance Plan'


@admin.register(PMChecklistItem)
class PMChecklistItemAdmin(admin.ModelAdmin):
    list_display = ('item_description_short', 'pm_task_link', 'is_mandatory', 'sequence_order', 'updated_at')
    list_filter = ('pm_task__maintenance_plan__asset', 'is_mandatory', 'pm_task__maintenance_plan')
    search_fields = ('item_description', 'pm_task__description')
    readonly_fields = ('uuid', 'created_at', 'updated_at')
    list_select_related = ('pm_task', 'pm_task__maintenance_plan')


    def item_description_short(self, obj):
        return obj.item_description[:75] + '...' if len(obj.item_description) > 75 else obj.item_description
    item_description_short.short_description = 'Item Description'

    def pm_task_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        link = reverse(f"admin:{obj.pm_task._meta.app_label}_{obj.pm_task._meta.model_name}_change", args=[obj.pm_task.uuid])
        return format_html('<a href="{}">Task for {}</a>', link, obj.pm_task.maintenance_plan.name)
    pm_task_link.short_description = 'PM Task'


@admin.register(PreventiveMaintenanceSOP)
class PreventiveMaintenanceSOPAdmin(admin.ModelAdmin):
    list_display = ('title', 'linked_to', 'version', 'upload_date', 'updated_at')
    list_filter = ('maintenance_plan__asset', 'pm_task__maintenance_plan', 'upload_date')
    search_fields = ('title', 'description', 'maintenance_plan__name', 'pm_task__description')
    readonly_fields = ('uuid', 'created_at', 'updated_at', 'upload_date')
    # Add 'document' to fields or fieldsets if you want it to be editable in admin,
    # but be mindful of how FileFields are handled in admin forms.
    fieldsets = (
        (None, {
            'fields': ('uuid', 'title', 'description', 'document', 'version')
        }),
        ('Linkage (link to either Plan or Task, or both if applicable)', {
            'fields': ('maintenance_plan', 'pm_task'),
        }),
        ('Timestamps', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at', 'upload_date'),
        }),
    )

    def linked_to(self, obj):
        if obj.maintenance_plan and obj.pm_task:
            return f"Plan: {obj.maintenance_plan.name}, Task: {obj.pm_task.description[:30]}..."
        elif obj.maintenance_plan:
            return f"Plan: {obj.maintenance_plan.name}"
        elif obj.pm_task:
            return f"Task: {obj.pm_task.description[:30]}..."
        return "Not linked"
    linked_to.short_description = 'Linked To'
