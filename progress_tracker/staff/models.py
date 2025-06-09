from django.db import models
from learning.models import Task  # ✅ correct import



class StudentTaskProgress(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    student_name = models.CharField(max_length=100)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
       return f"{self.student_name} - {self.task.title}"

