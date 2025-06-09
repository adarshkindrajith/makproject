

# Create your models here.
from django.db import models
from django.conf import settings

class Module(models.Model):
    name = models.CharField(max_length=100)
    week = models.IntegerField()

    def __str__(self):
        return f"Week {self.week}: {self.name}"

class Task(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=100)
    order = models.PositiveIntegerField()
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class StudentTask(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('student', 'task')

    def __str__(self):
        return f"{self.student.username} - {self.task.title} - {'Completed' if self.is_completed else 'Incomplete'}"
    


class StudentCurrentModule(models.Model):
    student = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    module = models.ForeignKey(Module, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.student.username} - {self.module.name if self.module else 'No Module'}"

class Badge(models.Model):
    name        = models.CharField(max_length=100)
    description = models.TextField()
    module      = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="badges")

    def __str__(self):
        return f"{self.name} (Week {self.module.week})"
    
class StudentBadge(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'badge')  # prevent duplicates

    def __str__(self):
        return f"{self.student.username} - {self.badge.name}"