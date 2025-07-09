import uuid
from django.db import models

class Asset(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, help_text="Unique identifier for the asset")
    name = models.CharField(max_length=255, help_text="Name of the asset")
    tag = models.CharField(max_length=100, unique=True, blank=True, null=True, help_text="Asset tag or identification code")
    model = models.CharField(max_length=255, blank=True, null=True, help_text="Model name or number of the asset")
    serial_number = models.CharField(max_length=255, unique=True, blank=True, null=True, help_text="Serial number of the asset")
    location = models.CharField(max_length=255, blank=True, null=True, help_text="Physical location of the asset")
    criticality = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Criticality level (e.g., High, Medium, Low)"
        # Consider using choices for predefined values:
        # choices=[('HIGH', 'High'), ('MEDIUM', 'Medium'), ('LOW', 'Low')],
    )
    installation_date = models.DateField(blank=True, null=True, help_text="Date when the asset was installed")

    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the asset was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp when the asset was last updated")

    def __str__(self):
        return f"{self.name} (Tag: {self.tag or 'N/A'})"

    class Meta:
        ordering = ['name']
        verbose_name = "Asset"
        verbose_name_plural = "Assets"
