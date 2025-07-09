import uuid
from django.db import models
from django.conf import settings
from assets.models import Asset

class FaultCategory(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, help_text="Name of the fault category (e.g., Electrical, Mechanical)")
    description = models.TextField(blank=True, null=True, help_text="Detailed description of the fault category")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = "Fault Category"
        verbose_name_plural = "Fault Categories"

class RootCause(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text="Name or brief description of the root cause")
    description = models.TextField(blank=True, null=True, help_text="Detailed explanation of the root cause")
    category = models.ForeignKey(FaultCategory, on_delete=models.SET_NULL, blank=True, null=True, related_name='root_causes', help_text="Optional category for this root cause")
    # For hierarchical root causes, you could add:
    # parent = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True, related_name='child_causes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['category__name', 'name']
        verbose_name = "Root Cause"
        verbose_name_plural = "Root Causes"

class BreakdownReport(models.Model):
    SEVERITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    STATUS_CHOICES = [
        ('REPORTED', 'Reported'),
        ('INVESTIGATING', 'Investigating'),
        ('ACTION_PENDING', 'Action Pending'), # e.g. waiting for parts or WO creation
        ('IN_PROGRESS', 'In Progress'), # e.g. WO is being executed
        ('RESOLVED', 'Resolved'),
        ('CLOSED', 'Closed'),
        ('CANCELLED', 'Cancelled'),
    ]

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name='breakdown_reports', help_text="The asset that experienced the breakdown")
    # Using PROTECT for asset to prevent deletion if breakdowns are logged against it. Consider SET_NULL or other strategies based on requirements.

    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name='reported_breakdowns', help_text="User who reported the breakdown")
    # Alternatively, if non-users can report or if user model is complex:
    # reported_by_name = models.CharField(max_length=255, blank=True, null=True, help_text="Name of the person reporting if not a system user")

    report_time = models.DateTimeField(auto_now_add=True, help_text="Time the breakdown was reported")
    description_of_fault = models.TextField(help_text="Detailed description of the fault or breakdown observed")

    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='MEDIUM', help_text="Severity level of the breakdown")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='REPORTED', help_text="Current status of the breakdown report")

    downtime_started_at = models.DateTimeField(blank=True, null=True, help_text="Timestamp when the asset downtime started")
    downtime_ended_at = models.DateTimeField(blank=True, null=True, help_text="Timestamp when the asset downtime ended (and asset was operational again)")

    resolution_details = models.TextField(blank=True, null=True, help_text="Details of the resolution implemented")
    root_cause_analysis = models.TextField(blank=True, null=True, help_text="Summary of the root cause analysis performed")
    identified_root_causes = models.ManyToManyField(RootCause, blank=True, related_name='breakdowns_caused', help_text="Identified root causes for this breakdown")

    # work_order = models.ForeignKey('work_orders.WorkOrder', on_delete=models.SET_NULL, blank=True, null=True, related_name='related_breakdowns') # To be added when WorkOrder model exists

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Breakdown on {self.asset.name} reported at {self.report_time.strftime('%Y-%m-%d %H:%M')}"

    @property
    def downtime_duration_hours(self):
        if self.downtime_started_at and self.downtime_ended_at:
            duration = self.downtime_ended_at - self.downtime_started_at
            return round(duration.total_seconds() / 3600, 2)
        return None
    downtime_duration_hours.fget.short_description = "Downtime (Hours)"


    class Meta:
        ordering = ['-report_time']
        verbose_name = "Breakdown Report"
        verbose_name_plural = "Breakdown Reports"

# Note: KPIs like MTBF (Mean Time Between Failures) and MTTR (Mean Time To Repair)
# are typically calculated across multiple breakdown instances and asset operational times.
# These would be derived from queries over BreakdownReport data and potentially Asset operational logs,
# rather than being fields directly on a single BreakdownReport.
# The `downtime_duration_hours` property is a step towards calculating MTTR for a single event.
