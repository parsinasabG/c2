from rest_framework import serializers
from .models import (
    SparePartCategory,
    Vendor,
    Warehouse,
    SparePart,
    StockItem,
    PartReservation
)
from work_orders.models import WorkOrder # For PrimaryKeyRelatedField queryset

class SparePartCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SparePartCategory
        fields = '__all__'
        read_only_fields = ('uuid', 'created_at', 'updated_at')

class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = '__all__'
        read_only_fields = ('uuid', 'created_at', 'updated_at')

class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = '__all__'
        read_only_fields = ('uuid', 'created_at', 'updated_at')

class SparePartSerializer(serializers.ModelSerializer):
    category_details = SparePartCategorySerializer(source='category', read_only=True, allow_null=True)
    default_vendor_details = VendorSerializer(source='default_vendor', read_only=True, allow_null=True)

    # Use PrimaryKeyRelatedField for writable FKs to accept UUIDs
    category = serializers.PrimaryKeyRelatedField(
        queryset=SparePartCategory.objects.all(),
        allow_null=True, required=False, pk_field=serializers.UUIDField(format='hex_verbose')
    )
    default_vendor = serializers.PrimaryKeyRelatedField(
        queryset=Vendor.objects.all(),
        allow_null=True, required=False, pk_field=serializers.UUIDField(format='hex_verbose')
    )

    class Meta:
        model = SparePart
        fields = [
            'uuid', 'name', 'part_number', 'description',
            'category', 'category_details',
            'default_vendor', 'default_vendor_details',
            'cost_per_unit', 'unit_of_measure',
            'created_at', 'updated_at'
        ]
        read_only_fields = (
            'uuid', 'created_at', 'updated_at',
            'category_details', 'default_vendor_details'
        )

class StockItemSerializer(serializers.ModelSerializer):
    spare_part_details = SparePartSerializer(source='spare_part', read_only=True)
    warehouse_details = WarehouseSerializer(source='warehouse', read_only=True)

    spare_part = serializers.PrimaryKeyRelatedField(
        queryset=SparePart.objects.all(), pk_field=serializers.UUIDField(format='hex_verbose')
    )
    warehouse = serializers.PrimaryKeyRelatedField(
        queryset=Warehouse.objects.all(), pk_field=serializers.UUIDField(format='hex_verbose')
    )

    class Meta:
        model = StockItem
        fields = [
            'uuid', 'spare_part', 'spare_part_details',
            'warehouse', 'warehouse_details',
            'quantity_on_hand', 'reorder_point', 'last_stocked_date', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = (
            'uuid', 'created_at', 'updated_at',
            'spare_part_details', 'warehouse_details'
        )

    def validate_quantity_on_hand(self, value):
        if value < 0:
            raise serializers.ValidationError("Quantity on hand cannot be negative.")
        return value

    def validate_reorder_point(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Reorder point cannot be negative.")
        return value

    def validate(self, data):
        # Ensure unique_together ('spare_part', 'warehouse') is handled if creating
        # On update, these fields are typically not changed, or if they are, it implies a new stock item.
        if not self.instance: # Only on create
            spare_part = data.get('spare_part')
            warehouse = data.get('warehouse')
            if StockItem.objects.filter(spare_part=spare_part, warehouse=warehouse).exists():
                raise serializers.ValidationError(
                    f"Stock item for {spare_part} in {warehouse} already exists."
                )
        return data


class PartReservationSerializer(serializers.ModelSerializer):
    work_order_id_display = serializers.StringRelatedField(source='work_order.work_order_id', read_only=True, allow_null=True)
    spare_part_details = SparePartSerializer(source='spare_part', read_only=True)

    work_order = serializers.PrimaryKeyRelatedField(
        queryset=WorkOrder.objects.all(), pk_field=serializers.UUIDField(format='hex_verbose')
    )
    spare_part = serializers.PrimaryKeyRelatedField(
        queryset=SparePart.objects.all(), pk_field=serializers.UUIDField(format='hex_verbose')
    )

    class Meta:
        model = PartReservation
        fields = [
            'uuid', 'work_order', 'work_order_id_display',
            'spare_part', 'spare_part_details',
            'quantity_reserved', 'reservation_date', 'is_fulfilled', 'fulfilled_date', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = (
            'uuid', 'reservation_date', 'created_at', 'updated_at',
            'work_order_id_display', 'spare_part_details'
        )

    def validate_quantity_reserved(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity reserved must be positive.")
        return value

    def validate(self, data):
        instance = getattr(self, 'instance', None)
        is_fulfilled = data.get('is_fulfilled', getattr(instance, 'is_fulfilled', False) if instance else False)
        fulfilled_date = data.get('fulfilled_date', getattr(instance, 'fulfilled_date', None) if instance else None)

        if is_fulfilled and not fulfilled_date:
            from django.utils import timezone
            data['fulfilled_date'] = timezone.now()
        elif not is_fulfilled:
            data['fulfilled_date'] = None

        return data
