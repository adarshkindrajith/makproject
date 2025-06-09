from django.db import models
from django.conf import settings


class HelpRequest(models.Model):
    REQUEST_TYPES = [
        ("urgent_review", "Urgent Review"),
        ("doubt_session", "Doubt Session"),
        ("report_issue", "Report Issue"),
        ("week_review", "week Review"),

  ]

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='help_requests')
    accepted_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='accepted_requests')
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_handled = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.username} - {self.request_type}"