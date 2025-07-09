import uuid
from django.db import models
from django.conf import settings
from assets.models import Asset
from preventive_maintenance.models import MaintenancePlan
# CorrectiveMaintenance model will be referenced as a string 'corrective_maintenance.BreakdownReport' to avoid circular dependency at import time.

def generate_work_order_id():
    from datetime import datetime
    prefix = "WO"
    date_str = datetime.now().strftime("%Y%m%d")
    random_suffix = str(uuid.uuid4()).split('-')[0][:4].upper()
    # Ensure uniqueness if multiple WOs are created in the same second/millisecond.
    # A more robust approach might involve a database sequence or checking for existing IDs.
    # For now, this provides a reasonably unique ID.
    # Consider checking if this ID already exists and regenerating if so, though unlikely with UUID part.
    new_id = f"{prefix}-{date_str}-{random_suffix}"
    while WorkOrder.objects.filter(work_order_id=new_id).exists(): # Check for collisions
        random_suffix = str(uuid.uuid4()).split('-')[0][:4].upper()
        new_id = f"{prefix}-{date_str}-{random_suffix}"
    return new_id

class WorkOrderType(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, help_text="Type of work order (e.g., Preventive, Corrective, Inspection)")
    description = models.TextField(blank=True, null=True, help_text="Detailed description of the work order type")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = "Work Order Type"
        verbose_name_plural = "Work Order Types"

class Priority(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True, help_text="Name of the priority level (e.g., Low, Medium, High, Urgent)")
    description = models.TextField(blank=True, null=True, help_text="Description of what this priority level entails")
    level = models.PositiveIntegerField(unique=True, help_text="Numeric level for sorting (e.g., 1 for High, 4 for Low)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['level']
        verbose_name = "Priority Level"
        verbose_name_plural = "Priority Levels"

class WorkOrder(models.Model):
    STATUS_CHOICES = [
        ('NEW', 'New'),
        ('OPEN', 'Open'), # Often used as a synonym for New or after initial review
        ('ASSIGNED', 'Assigned'),
        ('PLANNING', 'Planning'), # For parts, tools, technician scheduling
        ('WAITING_FOR_PARTS', 'Waiting for Parts'),
        ('READY_TO_START', 'Ready to Start'),
        ('IN_PROGRESS', 'In Progress'),
        ('ON_HOLD', 'On Hold'), # e.g. waiting for external input, asset not available
        ('COMPLETED', 'Completed'), # Work done, pending review/closure
        ('CLOSED', 'Closed'), # Finalized, reviewed
        ('CANCELLED', 'Cancelled'),
    ]

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    work_order_id = models.CharField(max_length=50, unique=True, default=generate_work_order_id, editable=False, help_text="Unique system-generated Work Order ID")
    title = models.CharField(max_length=255, help_text="Brief title for the work order")
    description = models.TextField(blank=True, null=True, help_text="Detailed description of the work to be performed")

    work_order_type = models.ForeignKey(WorkOrderType, on_delete=models.PROTECT, related_name='work_orders')
    asset = models.ForeignKey(Asset, on_delete=models.SET_NULL, blank=True, null=True, related_name='work_orders')
    priority = models.ForeignKey(Priority, on_delete=models.SET_NULL, blank=True, null=True, related_name='work_orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')

    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name='reported_work_orders')
    assigned_to_technician = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name='assigned_work_orders', limit_choices_to={'is_staff': True}) # Assuming technicians are staff

    required_skills = models.TextField(blank=True, null=True, help_text="Comma-separated list of skills or M2M to a Skill model later")

    estimated_hours = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    actual_hours = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)

    scheduled_start_date = models.DateTimeField(blank=True, null=True)
    scheduled_end_date = models.DateTimeField(blank=True, null=True)
    actual_start_date = models.DateTimeField(blank=True, null=True)
    actual_end_date = models.DateTimeField(blank=True, null=True)

    completion_notes = models.TextField(blank=True, null=True)

    source_maintenance_plan = models.ForeignKey(MaintenancePlan, on_delete=models.SET_NULL, blank=True, null=True, related_name='generated_work_orders', help_text="PM Plan that generated this WO, if applicable")
    source_breakdown_report = models.ForeignKey('corrective_maintenance.BreakdownReport', on_delete=models.SET_NULL, blank=True, null=True, related_name='generated_work_orders_from_breakdown', help_text="Breakdown report that this WO addresses, if applicable")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.work_order_id}: {self.title}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Work Order"
        verbose_name_plural = "Work Orders"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.scheduled_start_date and self.scheduled_end_date and self.scheduled_end_date < self.scheduled_start_date:
            raise ValidationError({'scheduled_end_date': "Scheduled end date cannot be before scheduled start date."})
        if self.actual_start_date and self.actual_end_date and self.actual_end_date < self.actual_start_date:
            raise ValidationError({'actual_end_date': "Actual end date cannot be before actual start date."})
        if self.source_maintenance_plan and self.source_breakdown_report:
            raise ValidationError("A work order cannot be linked to both a Maintenance Plan and a Breakdown Report simultaneously.")


class WorkOrderTask(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('SKIPPED', 'Skipped'),
        ('FAILED', 'Failed'),
    ]
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name='tasks')
    description = models.TextField(help_text="Description of the individual task")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    sequence_order = models.PositiveIntegerField(default=0, help_text="Order of this task within the work order")
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    actual_hours = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    notes = models.TextField(blank=True, null=True, help_text="Notes specific to this task")
    # completed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name='completed_wo_tasks')
    # completed_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Task for {self.work_order.work_order_id}: {self.description[:50]}..."

    class Meta:
        ordering = ['work_order', 'sequence_order']
        verbose_name = "Work Order Task"
        verbose_name_plural = "Work Order Tasks"
