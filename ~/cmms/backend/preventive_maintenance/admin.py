from django.contrib import admin
from .models import MaintenancePlan, PMTask, PMChecklistItem, PreventiveMaintenanceSOP

class PMChecklistItemInline(admin.TabularInline):
    model = PMChecklistItem
    extra = 1
    fields = ('sequence_order', 'item_description', 'is_mandatory', 'expected_result')
    readonly_fields = ('uuid',) # 'created_at', 'updated_at' are not in fields
    ordering = ('sequence_order',)

class PMTaskInline(admin.TabularInline):
    model = PMTask
    extra = 1
    fields = ('sequence_order', 'description', 'assigned_to_role', 'estimated_duration_hours')
    readonly_fields = ('uuid',)
    ordering = ('sequence_order',)
    show_change_link = True

class PreventiveMaintenanceSOPInline(admin.TabularInline):
    model = PreventiveMaintenanceSOP
    extra = 1
    fields = ('title', 'document', 'version', 'description')
    readonly_fields = ('uuid', 'upload_date')


@admin.register(MaintenancePlan)
class MaintenancePlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'asset_link', 'schedule_type', 'interval_days', 'usage_threshold', 'is_active', 'updated_at')
    list_filter = ('schedule_type', 'is_active', 'asset')
    search_fields = ('name', 'description', 'asset__name', 'asset__tag')
    readonly_fields = ('uuid', 'created_at', 'updated_at')
    autocomplete_fields = ['asset']
    inlines = [PMTaskInline, PreventiveMaintenanceSOPInline] # SOPs can be directly linked to a plan
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

    def asset_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        if obj.asset:
            link = reverse(f"admin:{obj.asset._meta.app_label}_{obj.asset._meta.model_name}_change", args=[obj.asset.uuid])
            return format_html('<a href="{}">{}</a>', link, obj.asset.name)
        return "-"
    asset_link.short_description = 'Asset'


@admin.register(PMTask)
class PMTaskAdmin(admin.ModelAdmin):
    list_display = ('description_short', 'maintenance_plan_link', 'assigned_to_role', 'estimated_duration_hours', 'sequence_order', 'updated_at')
    list_filter = ('maintenance_plan__asset', 'assigned_to_role', 'maintenance_plan')
    search_fields = ('description', 'maintenance_plan__name', 'maintenance_plan__asset__name')
    readonly_fields = ('uuid', 'created_at', 'updated_at')
    list_select_related = ('maintenance_plan', 'maintenance_plan__asset')
    inlines = [PMChecklistItemInline, PreventiveMaintenanceSOPInline] # SOPs can also be linked to specific tasks
    autocomplete_fields = ['maintenance_plan']

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
    autocomplete_fields = ['pm_task']


    def item_description_short(self, obj):
        return obj.item_description[:75] + '...' if len(obj.item_description) > 75 else obj.item_description
    item_description_short.short_description = 'Item Description'

    def pm_task_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        link = reverse(f"admin:{obj.pm_task._meta.app_label}_{obj.pm_task._meta.model_name}_change", args=[obj.pm_task.uuid])
        # Displaying task's plan name for better context
        task_display = f"Task for {obj.pm_task.maintenance_plan.name} (Seq: {obj.pm_task.sequence_order})"
        return format_html('<a href="{}">{}</a>', link, task_display)
    pm_task_link.short_description = 'PM Task'


@admin.register(PreventiveMaintenanceSOP)
class PreventiveMaintenanceSOPAdmin(admin.ModelAdmin):
    list_display = ('title', 'linked_to', 'version', 'upload_date', 'updated_at')
    list_filter = ('maintenance_plan__asset', 'pm_task__maintenance_plan', 'upload_date')
    search_fields = ('title', 'description', 'maintenance_plan__name', 'pm_task__description')
    readonly_fields = ('uuid', 'created_at', 'updated_at', 'upload_date')
    autocomplete_fields = ['maintenance_plan', 'pm_task']
    fieldsets = (
        (None, {
            'fields': ('uuid', 'title', 'description', 'document', 'version')
        }),
        ('Linkage (link to Plan and/or Task)', { # Clarified linkage
            'fields': ('maintenance_plan', 'pm_task'),
        }),
        ('Timestamps', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at', 'upload_date'),
        }),
    )

    def linked_to(self, obj):
        links = []
        if obj.maintenance_plan:
            links.append(f"Plan: {obj.maintenance_plan.name}")
        if obj.pm_task:
            links.append(f"Task: {obj.pm_task.description[:30]}...")
        return ", ".join(links) if links else "Not linked"
    linked_to.short_description = 'Linked To'
