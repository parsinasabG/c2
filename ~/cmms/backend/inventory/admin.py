from django.contrib import admin
from .models import (
    SparePartCategory,
    Vendor,
    Warehouse,
    SparePart,
    StockItem,
    PartReservation
)

@admin.register(SparePartCategory)
class SparePartCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent_category', 'description_short', 'updated_at')
    search_fields = ('name', 'description')
    list_filter = ('parent_category',)
    readonly_fields = ('uuid', 'created_at', 'updated_at')
    autocomplete_fields = ['parent_category']

    def description_short(self, obj):
        return obj.description[:75] + '...' if obj.description and len(obj.description) > 75 else obj.description
    description_short.short_description = 'Description'

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'phone', 'email', 'updated_at')
    search_fields = ('name', 'contact_person', 'email', 'phone', 'address')
    readonly_fields = ('uuid', 'created_at', 'updated_at')

@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('name', 'location_description_short', 'is_active', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'location_description')
    readonly_fields = ('uuid', 'created_at', 'updated_at')

    def location_description_short(self, obj):
        return obj.location_description[:75] + '...' if obj.location_description and len(obj.location_description) > 75 else obj.location_description
    location_description_short.short_description = 'Location'

class StockItemInline(admin.TabularInline):
    model = StockItem
    extra = 1
    fields = ('warehouse', 'quantity_on_hand', 'reorder_point', 'last_stocked_date', 'notes')
    readonly_fields = ('uuid', 'created_at', 'updated_at')
    autocomplete_fields = ['warehouse']
    ordering = ('warehouse__name',)

@admin.register(SparePart)
class SparePartAdmin(admin.ModelAdmin):
    list_display = ('name', 'part_number', 'category_link', 'default_vendor_link', 'cost_per_unit', 'unit_of_measure', 'updated_at')
    list_filter = ('category', 'default_vendor', 'unit_of_measure')
    search_fields = ('name', 'part_number', 'description', 'category__name', 'default_vendor__name')
    readonly_fields = ('uuid', 'created_at', 'updated_at')
    autocomplete_fields = ['category', 'default_vendor']
    inlines = [StockItemInline]
    fieldsets = (
        (None, {'fields': ('uuid', 'name', 'part_number', 'description')}),
        ('Categorization & Supply', {'fields': ('category', 'default_vendor')}),
        ('Details', {'fields': ('cost_per_unit', 'unit_of_measure')}),
        ('Timestamps', {'classes': ('collapse',), 'fields': ('created_at', 'updated_at')}),
    )

    def category_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        if obj.category:
            link = reverse(f"admin:{obj.category._meta.app_label}_{obj.category._meta.model_name}_change", args=[obj.category.uuid])
            return format_html('<a href="{}">{}</a>', link, obj.category.name)
        return "-"
    category_link.short_description = 'Category'

    def default_vendor_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        if obj.default_vendor:
            link = reverse(f"admin:{obj.default_vendor._meta.app_label}_{obj.default_vendor._meta.model_name}_change", args=[obj.default_vendor.uuid])
            return format_html('<a href="{}">{}</a>', link, obj.default_vendor.name)
        return "-"
    default_vendor_link.short_description = 'Default Vendor'


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    list_display = ('spare_part_link', 'warehouse_link', 'quantity_on_hand', 'reorder_point', 'last_stocked_date', 'updated_at')
    list_filter = ('warehouse', 'spare_part__category', 'last_stocked_date')
    search_fields = ('spare_part__name', 'spare_part__part_number', 'warehouse__name', 'notes')
    readonly_fields = ('uuid', 'created_at', 'updated_at')
    autocomplete_fields = ['spare_part', 'warehouse']
    list_select_related = ('spare_part', 'warehouse')
    fieldsets = (
        (None, {'fields': ('uuid', 'spare_part', 'warehouse')}),
        ('Stock Details', {'fields': ('quantity_on_hand', 'reorder_point', 'last_stocked_date', 'notes')}),
        ('Timestamps', {'classes': ('collapse',), 'fields': ('created_at', 'updated_at')}),
    )

    def spare_part_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        link = reverse(f"admin:{obj.spare_part._meta.app_label}_{obj.spare_part._meta.model_name}_change", args=[obj.spare_part.uuid])
        return format_html('<a href="{}">{}</a>', link, obj.spare_part.name)
    spare_part_link.short_description = 'Spare Part'

    def warehouse_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        link = reverse(f"admin:{obj.warehouse._meta.app_label}_{obj.warehouse._meta.model_name}_change", args=[obj.warehouse.uuid])
        return format_html('<a href="{}">{}</a>', link, obj.warehouse.name)
    warehouse_link.short_description = 'Warehouse'

@admin.register(PartReservation)
class PartReservationAdmin(admin.ModelAdmin):
    list_display = ('work_order_link', 'spare_part_link', 'quantity_reserved', 'is_fulfilled', 'reservation_date', 'fulfilled_date')
    list_filter = ('is_fulfilled', 'reservation_date', 'spare_part__category', 'work_order__asset')
    search_fields = ('work_order__work_order_id', 'work_order__title', 'spare_part__name', 'spare_part__part_number', 'notes')
    readonly_fields = ('uuid', 'created_at', 'updated_at', 'reservation_date', 'fulfilled_date')
    autocomplete_fields = ['work_order', 'spare_part']
    list_select_related = ('work_order', 'spare_part')
    actions = ['mark_as_fulfilled_admin', 'mark_as_unfulfilled_admin']

    fieldsets = (
        (None, {'fields': ('uuid', 'work_order', 'spare_part', 'quantity_reserved')}),
        ('Fulfillment', {'fields': ('is_fulfilled', 'fulfilled_date', 'notes')}),
        ('Timestamps', {'classes': ('collapse',), 'fields': ('created_at', 'updated_at', 'reservation_date')}),
    )

    def work_order_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        if obj.work_order:
            link = reverse(f"admin:{obj.work_order._meta.app_label}_{obj.work_order._meta.model_name}_change", args=[obj.work_order.uuid])
            return format_html('<a href="{}">{}</a>', link, obj.work_order.work_order_id)
        return "-"
    work_order_link.short_description = 'Work Order'

    def spare_part_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        link = reverse(f"admin:{obj.spare_part._meta.app_label}_{obj.spare_part._meta.model_name}_change", args=[obj.spare_part.uuid])
        return format_html('<a href="{}">{}</a>', link, obj.spare_part.name)
    spare_part_link.short_description = 'Spare Part'

    @admin.action(description='Mark selected reservations as fulfilled (Admin Action - Does NOT adjust stock)')
    def mark_as_fulfilled_admin(self, request, queryset):
        # This admin action is simplified and does NOT adjust stock.
        # Stock adjustments should ideally be handled via API calls or a more robust service layer.
        updated_count = queryset.filter(is_fulfilled=False).update(is_fulfilled=True, fulfilled_date=timezone.now())
        self.message_user(request, f"{updated_count} reservations marked as fulfilled. Note: Stock levels NOT automatically adjusted by this admin action.")

    @admin.action(description='Mark selected reservations as unfulfilled (Admin Action - Does NOT adjust stock)')
    def mark_as_unfulfilled_admin(self, request, queryset):
        # This admin action is simplified and does NOT adjust stock.
        updated_count = queryset.filter(is_fulfilled=True).update(is_fulfilled=False, fulfilled_date=None)
        self.message_user(request, f"{updated_count} reservations marked as unfulfilled. Note: Stock levels NOT automatically adjusted by this admin action.")
