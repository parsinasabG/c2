from django.contrib import admin
from .models import WorkOrderType, Priority, WorkOrder, WorkOrderTask

@admin.register(WorkOrderType)
class WorkOrderTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description_short', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    readonly_fields = ('uuid', 'created_at', 'updated_at')

    def description_short(self, obj):
        return obj.description[:75] + '...' if obj.description and len(obj.description) > 75 else obj.description
    description_short.short_description = 'Description'

@admin.register(Priority)
class PriorityAdmin(admin.ModelAdmin):
    list_display = ('name', 'level', 'description_short', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    readonly_fields = ('uuid', 'created_at', 'updated_at')
    ordering = ('level',)

    def description_short(self, obj):
        return obj.description[:75] + '...' if obj.description and len(obj.description) > 75 else obj.description
    description_short.short_description = 'Description'

class WorkOrderTaskInline(admin.TabularInline):
    model = WorkOrderTask
    extra = 1
    fields = ('sequence_order', 'description', 'status', 'estimated_hours', 'actual_hours', 'notes')
    readonly_fields = ('uuid', 'created_at', 'updated_at') # UUID is not editable anyway
    ordering = ('sequence_order',)
    # classes = ['collapse'] # Optional: to make inlines collapsible

@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = (
        'work_order_id', 'title_short', 'asset_link', 'work_order_type', 'priority', 'status',
        'assigned_to_technician_username', 'scheduled_start_date', 'actual_end_date', 'updated_at'
    )
    list_filter = ('status', 'priority', 'work_order_type', 'asset', 'assigned_to_technician', 'scheduled_start_date', 'created_at')
    search_fields = (
        'work_order_id', 'title', 'description', 'asset__name', 'asset__tag',
        'assigned_to_technician__username', 'completion_notes'
    )
    readonly_fields = ('uuid', 'work_order_id', 'created_at', 'updated_at') # 'reported_by' can be set on creation
    list_select_related = ('asset', 'work_order_type', 'priority', 'reported_by', 'assigned_to_technician')
    date_hierarchy = 'created_at'
    inlines = [WorkOrderTaskInline]
    autocomplete_fields = ['asset', 'priority', 'work_order_type', 'reported_by', 'assigned_to_technician', 'source_maintenance_plan', 'source_breakdown_report']


    fieldsets = (
        (None, {
            'fields': ('work_order_id', 'title', 'description')
        }),
        ('Categorization & Asset', {
            'fields': ('work_order_type', 'asset', 'priority', 'status')
        }),
        ('Assignment & Scheduling', {
            'fields': ('reported_by', 'assigned_to_technician', 'required_skills',
                       'scheduled_start_date', 'scheduled_end_date')
        }),
        ('Execution & Completion', {
            'classes': ('collapse',),
            'fields': ('actual_start_date', 'actual_end_date', 'estimated_hours', 'actual_hours', 'completion_notes')
        }),
        ('Source Links (Informational)', {
            'classes': ('collapse',),
            'fields': ('source_maintenance_plan', 'source_breakdown_report')
        }),
        ('Timestamps', {
            'classes': ('collapse',),
            'fields': ('uuid', 'created_at', 'updated_at'),
        }),
    )

    def title_short(self, obj):
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
    title_short.short_description = 'Title'

    def asset_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        if obj.asset:
            link = reverse(f"admin:{obj.asset._meta.app_label}_{obj.asset._meta.model_name}_change", args=[obj.asset.uuid])
            return format_html('<a href="{}">{}</a>', link, obj.asset.name)
        return "-"
    asset_link.short_description = 'Asset'

    def assigned_to_technician_username(self, obj):
        return obj.assigned_to_technician.username if obj.assigned_to_technician else '-'
    assigned_to_technician_username.short_description = 'Assigned To'

    def save_model(self, request, obj, form, change):
        # If creating a new WO and reported_by is not set, set it to current user
        if not change and not obj.reported_by_id and request.user.is_authenticated:
            obj.reported_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(WorkOrderTask)
class WorkOrderTaskAdmin(admin.ModelAdmin):
    list_display = ('description_short', 'work_order_link', 'status', 'sequence_order', 'updated_at')
    list_filter = ('status', 'work_order__asset', 'work_order__work_order_type', 'work_order__priority')
    search_fields = ('description', 'notes', 'work_order__title', 'work_order__work_order_id')
    readonly_fields = ('uuid', 'created_at', 'updated_at')
    list_select_related = ('work_order', 'work_order__asset')
    autocomplete_fields = ['work_order']

    def description_short(self, obj):
        return obj.description[:75] + '...' if len(obj.description) > 75 else obj.description
    description_short.short_description = 'Task Description'

    def work_order_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        link = reverse(f"admin:{obj.work_order._meta.app_label}_{obj.work_order._meta.model_name}_change", args=[obj.work_order.uuid])
        return format_html('<a href="{}">{}</a>', link, obj.work_order.work_order_id)
    work_order_link.short_description = 'Work Order'
