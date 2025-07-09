import uuid
from django.db import models
from django.conf import settings # If using AUTH_USER_MODEL for assigned_to
from assets.models import Asset # Assuming Asset model is in an 'assets' app

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
    # assigned_to_role can be simple CharField or FK to a new 'Role' model if roles are complex
    assigned_to_role = models.CharField(max_length=100, blank=True, null=True, help_text="Role responsible for this task (e.g., 'Technician', 'Electrician')")
    # Or, if assigning to specific users:
    # assigned_to_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name='pm_tasks')
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
    # SOPs can be linked to a whole plan or a specific task
    maintenance_plan = models.ForeignKey(MaintenancePlan, on_delete=models.CASCADE, related_name='sops', blank=True, null=True)
    pm_task = models.ForeignKey(PMTask, on_delete=models.CASCADE, related_name='sops', blank=True, null=True)

    title = models.CharField(max_length=255, help_text="Title of the SOP document")
    document = models.FileField(upload_to='sops/', help_text="The SOP document file")
    version = models.CharField(max_length=50, blank=True, null=True, help_text="Document version")
    upload_date = models.DateField(auto_now_add=True, help_text="Date when the SOP was uploaded")
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
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(maintenance_plan__isnull=False, pm_task__isnull=True) |
                    models.Q(maintenance_plan__isnull=True, pm_task__isnull=False) |
                    models.Q(maintenance_plan__isnull=False, pm_task__isnull=False) # Or allow both if SOP can be general to plan but also specific to task
                ),
                name='sop_linked_to_plan_or_task_or_both_if_needed'
                # If SOP must be linked to EITHER plan OR task, but not both and not neither (and not neither if one is optional):
                # check=(
                #    (models.Q(maintenance_plan__isnull=False) & models.Q(pm_task__isnull=True)) |
                #    (models.Q(maintenance_plan__isnull=True) & models.Q(pm_task__isnull=False))
                # ),
                # name='sop_linked_to_plan_or_task'
                # For now, allowing it to be linked to plan, task, or both, but one must be present if the other isn't.
                # A simpler approach if SOP is always for a plan OR a task but not both:
                # Make pm_task nullable and maintenance_plan nullable. Add a clean method to validate.
                # For now, the constraint above is a bit complex. Let's simplify by making them both optional
                # and relying on application logic or a more specific model if an SOP *must* be tied to one or the other.
                # The current FKs allow an SOP to be tied to a plan, or a task, or both, or neither (if both blank=True, null=True).
                # Let's ensure at least one is chosen or make them mutually exclusive via clean() or more specific models.
                # For now, I'll remove the constraint as it's complex and might be overly restrictive initially.
                # It can be added back with more specific business rules.
            )
        ]

    # def clean(self):
    #     from django.core.exceptions import ValidationError
    #     if self.maintenance_plan and self.pm_task:
    #         # Or, if this is allowed, perhaps check if pm_task belongs to maintenance_plan
    #         pass # Allow SOP to be for a plan and refined for a task within it
    #     if not self.maintenance_plan and not self.pm_task:
    #         raise ValidationError('An SOP must be related to either a Maintenance Plan or a PM Task.')

# Ensure the 'sops/' directory exists in your MEDIA_ROOT if you use FileField.
# MEDIA_URL = '/media/'
# MEDIA_ROOT = BASE_DIR / 'media'
# Need to add these to settings.py and configure URL serving for media files for development.
