import uuid
from django.db import models
# from django.conf import settings # If using AUTH_USER_MODEL for assigned_to
from assets.models import Asset

class MaintenancePlan(models.Model):
    SCHEDULE_TYPES = [
        ('TIME', 'Time-Based'),
        ('USAGE', 'Usage-Based'),
        ('CONDITION', 'Condition-Based'),
    ]

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='maintenance_plans')
    name = models.CharField(max_length=255, help_text="Name of the maintenance plan (e.g., 'Monthly HVAC Check')")
    description = models.TextField(blank=True, null=True, help_text="Detailed description of the maintenance plan")

    schedule_type = models.CharField(max_length=10, choices=SCHEDULE_TYPES, default='TIME')

    # For Time-Based
    interval_days = models.PositiveIntegerField(blank=True, null=True, help_text="Interval in days for time-based schedules")

    # For Usage-Based
    usage_metric = models.CharField(max_length=100, blank=True, null=True, help_text="Metric for usage-based (e.g., 'operating_hours', 'cycles_completed')")
    usage_threshold = models.FloatField(blank=True, null=True, help_text="Threshold for the usage metric to trigger maintenance")

    # For Condition-Based
    condition_threshold_description = models.TextField(blank=True, null=True, help_text="Description of the condition that triggers maintenance (e.g., 'Vibration exceeds X mm/s')")

    is_active = models.BooleanField(default=True, help_text="Is this maintenance plan currently active?")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} for {self.asset.name}"

    class Meta:
        ordering = ['asset__name', 'name']
        verbose_name = "Maintenance Plan"
        verbose_name_plural = "Maintenance Plans"

class PMTask(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    maintenance_plan = models.ForeignKey(MaintenancePlan, on_delete=models.CASCADE, related_name='pm_tasks')
    description = models.TextField(help_text="Description of the task to be performed")
    estimated_duration_hours = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Estimated time in hours to complete the task")
    assigned_to_role = models.CharField(max_length=100, blank=True, null=True, help_text="Role responsible for this task (e.g., 'Technician', 'Electrician')")
    sequence_order = models.PositiveIntegerField(default=0, help_text="Order in which this task should be performed within the plan")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Task for {self.maintenance_plan.name}: {self.description[:50]}..."

    class Meta:
        ordering = ['maintenance_plan', 'sequence_order']
        verbose_name = "PM Task"
        verbose_name_plural = "PM Tasks"

class PMChecklistItem(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pm_task = models.ForeignKey(PMTask, on_delete=models.CASCADE, related_name='checklist_items')
    item_description = models.CharField(max_length=500, help_text="Description of the checklist item")
    is_mandatory = models.BooleanField(default=True, help_text="Is this checklist item mandatory?")
    expected_result = models.CharField(max_length=255, blank=True, null=True, help_text="Expected result or condition for this item (e.g., 'Clean', 'No leaks', 'Value between X and Y')")
    sequence_order = models.PositiveIntegerField(default=0, help_text="Order of this item within the task's checklist")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Checklist item for {self.pm_task.description[:30]}...: {self.item_description[:50]}..."

    class Meta:
        ordering = ['pm_task', 'sequence_order']
        verbose_name = "PM Checklist Item"
        verbose_name_plural = "PM Checklist Items"

class PreventiveMaintenanceSOP(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    maintenance_plan = models.ForeignKey(MaintenancePlan, on_delete=models.CASCADE, related_name='sops', blank=True, null=True)
    pm_task = models.ForeignKey(PMTask, on_delete=models.CASCADE, related_name='sops', blank=True, null=True)

    title = models.CharField(max_length=255, help_text="Title of the SOP document")
    document = models.FileField(upload_to='sops/preventive_maintenance/', help_text="The SOP document file")
    version = models.CharField(max_length=50, blank=True, null=True, help_text="Document version")
    upload_date = models.DateField(auto_now_add=True, help_text="Date when the SOP was uploaded") # auto_now_add for upload_date might be better as default=date.today
    description = models.TextField(blank=True, null=True, help_text="Brief description of the SOP")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.maintenance_plan:
            return f"SOP '{self.title}' for Plan: {self.maintenance_plan.name}"
        elif self.pm_task:
            return f"SOP '{self.title}' for Task: {self.pm_task.description[:30]}..."
        return self.title

    class Meta:
        ordering = ['title', '-upload_date']
        verbose_name = "Preventive Maintenance SOP"
        verbose_name_plural = "Preventive Maintenance SOPs"

    def clean(self):
        from django.core.exceptions import ValidationError
        # Ensure SOP is linked to at least a plan or a task, but not necessarily exclusively one.
        # This logic can be adjusted based on more specific business rules.
        # If an SOP can be general to a plan AND more specific to a task within that plan, this is fine.
        # If it must be EITHER plan OR task, then:
        # if self.maintenance_plan and self.pm_task:
        #     raise ValidationError("SOP cannot be linked to both a Maintenance Plan and a PM Task simultaneously. Choose one.")
        if not self.maintenance_plan and not self.pm_task:
             raise ValidationError("An SOP must be related to either a Maintenance Plan or a PM Task.")

        # If linked to a task, ensure task belongs to the linked plan (if plan is also linked)
        if self.maintenance_plan and self.pm_task:
            if self.pm_task.maintenance_plan != self.maintenance_plan:
                raise ValidationError("The PM Task selected does not belong to the selected Maintenance Plan.")

# Note: MEDIA_ROOT and MEDIA_URL need to be configured in settings.py for FileField.
# The upload_to path 'sops/preventive_maintenance/' is relative to MEDIA_ROOT.
