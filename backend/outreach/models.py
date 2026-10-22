from django.conf import settings
from django.db import models


class ApplicationEmail(models.Model):
    """Draft email ready to send for one application."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="application_emails",
    )
    analysis = models.ForeignKey(
        "analyses.Analysis",
        on_delete=models.CASCADE,
        related_name="application_emails",
    )
    subject = models.CharField(max_length=200)
    body = models.TextField()
    skills = models.JSONField(default=list, blank=True)
    used_interview = models.BooleanField(default=False)
    language = models.CharField(max_length=5, default="fr")
    ai_mode = models.CharField(max_length=16, default="mock")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"ApplicationEmail #{self.pk}"
