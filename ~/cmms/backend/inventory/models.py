import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
# String reference 'work_orders.WorkOrder' will be used for ForeignKey to avoid circular import issues at model definition time.

class SparePartCategory(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150, unique=True, help_text="Name of the spare part category")
    description = models.TextField(blank=True, null=True, help_text="Description of the category")
    parent_category = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True, related_name='child_categories', help_text="Optional parent category for hierarchical structure")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = "Spare Part Category"
        verbose_name_plural = "Spare Part Categories"

class Vendor(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True, help_text="Name of the vendor/supplier")
    contact_person = models.CharField(max_length=255, blank=True, null=True, help_text="Primary contact person at the vendor")
    phone = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    address = models.TextField(blank=True, null=True, help_text="Vendor's physical or mailing address")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = "Vendor"
        verbose_name_plural = "Vendors"

class Warehouse(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150, unique=True, help_text="Name of the warehouse or storage location")
    location_description = models.TextField(blank=True, null=True, help_text="Description of the warehouse's location")
    is_active = models.BooleanField(default=True, help_text="Is this warehouse currently active?")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = "Warehouse"
        verbose_name_plural = "Warehouses"

class SparePart(models.Model):
    UNIT_OF_MEASURE_CHOICES = [
        ('PCS', 'Pieces'),
        ('BOX', 'Box'),
        ('M', 'Meter'),
        ('CM', 'Centimeter'),
        ('L', 'Liter'),
        ('ML', 'Milliliter'),
        ('KG', 'Kilogram'),
        ('G', 'Gram'),
        ('SET', 'Set'),
        ('PAIR', 'Pair'),
        ('ROLL', 'Roll'),
        ('OTHER', 'Other'),
    ]
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text="Descriptive name of the spare part")
    part_number = models.CharField(max_length=100, unique=True, help_text="Manufacturer or internal part number")
    description = models.TextField(blank=True, null=True, help_text="Detailed description of the spare part")
    category = models.ForeignKey(SparePartCategory, on_delete=models.SET_NULL, blank=True, null=True, related_name='spare_parts')
    default_vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, blank=True, null=True, related_name='supplied_parts')
    cost_per_unit = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, help_text="Cost of one unit of this part")
    unit_of_measure = models.CharField(max_length=10, choices=UNIT_OF_MEASURE_CHOICES, default='PCS')
    # image = models.ImageField(upload_to='inventory/spare_parts_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} (PN: {self.part_number})"

    class Meta:
        ordering = ['name', 'part_number']
        verbose_name = "Spare Part"
        verbose_name_plural = "Spare Parts"

class StockItem(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    spare_part = models.ForeignKey(SparePart, on_delete=models.CASCADE, related_name='stock_items')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='stock_items')
    quantity_on_hand = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Current quantity in stock at this warehouse")
    reorder_point = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, help_text="Quantity at which to reorder this part for this warehouse")
    last_stocked_date = models.DateTimeField(default=timezone.now, help_text="Date when stock was last added/updated")
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.spare_part.name} in {self.warehouse.name}: {self.quantity_on_hand} {self.spare_part.unit_of_measure}"

    class Meta:
        ordering = ['spare_part__name', 'warehouse__name']
        unique_together = ('spare_part', 'warehouse')
        verbose_name = "Stock Item"
        verbose_name_plural = "Stock Items"

    def clean(self):
        if self.quantity_on_hand < 0:
            raise ValidationError({'quantity_on_hand': "Quantity on hand cannot be negative."})
        if self.reorder_point is not None and self.reorder_point < 0:
            raise ValidationError({'reorder_point': "Reorder point cannot be negative."})

class PartReservation(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    work_order = models.ForeignKey('work_orders.WorkOrder', on_delete=models.CASCADE, related_name='part_reservations')
    spare_part = models.ForeignKey(SparePart, on_delete=models.PROTECT, related_name='reservations')
    quantity_reserved = models.DecimalField(max_digits=10, decimal_places=2, help_text="Quantity of the part reserved for the work order")
    reservation_date = models.DateTimeField(default=timezone.now, help_text="Date and time of reservation")
    is_fulfilled = models.BooleanField(default=False, help_text="Has this reservation been fulfilled (i.e., parts issued)?")
    fulfilled_date = models.DateTimeField(blank=True, null=True, help_text="Date and time reservation was fulfilled")
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Reservation of {self.quantity_reserved} x {self.spare_part.name} for WO: {self.work_order.work_order_id}"

    class Meta:
        ordering = ['-reservation_date']
        verbose_name = "Part Reservation"
        verbose_name_plural = "Part Reservations"

    def clean(self):
        if self.quantity_reserved <= 0:
            raise ValidationError({'quantity_reserved': "Quantity reserved must be positive."})
        if self.is_fulfilled and not self.fulfilled_date:
            self.fulfilled_date = timezone.now()
        elif not self.is_fulfilled:
            self.fulfilled_date = None
