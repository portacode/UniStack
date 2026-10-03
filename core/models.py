import uuid

from django.db import models


class ModelInvocation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat_id = models.CharField(max_length=255, db_index=True)
    request_id = models.UUIDField(null=True, db_index=True)
    model = models.CharField(max_length=255)
    response_id = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=16, default="running", choices=[
        ("running", "Running"), ("completed", "Completed"),
        ("failed", "Failed"), ("incomplete", "Incomplete"),
    ])
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True)
    input_tokens = models.PositiveIntegerField(null=True)
    cached_input_tokens = models.PositiveIntegerField(null=True)
    output_tokens = models.PositiveIntegerField(null=True)
    reasoning_tokens = models.PositiveIntegerField(null=True)
    usage = models.JSONField(default=dict)
    error = models.TextField(blank=True)

    class Meta:
        ordering = ["-started_at"]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            previous = type(self).objects.get(pk=self.pk)
            if previous.status != "running":
                raise ValueError("Finished invocation records are immutable")
        return super().save(*args, **kwargs)
