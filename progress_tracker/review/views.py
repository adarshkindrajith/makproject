from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import HelpRequest
from learning.models import Module, Task, StudentTask 

@login_required
def student_dashboard(request):
    student = request.user
    module = Module.objects.first()
    tasks = module.tasks.order_by('order') if module else Task.objects.none()

    task_statuses = []
    for task in tasks:
        is_completed = StudentTask.objects.filter(student=student, task=task, is_completed=True).exists()
        task_statuses.append({
            'task': task,
            'is_completed': is_completed,
        })

    completed_count = sum(1 for t in task_statuses if t['is_completed'])
    total_count = len(task_statuses)
    progress = (completed_count / total_count) * 100 if total_count else 0

    return render(request, 'learning/student_dashboard.html', {
        'module': module,
        'task_statuses': task_statuses,
        'progress': int(progress),
        'completed': completed_count,
        'total': total_count,
    })

@login_required
def complete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    student = request.user
    student_task, _ = StudentTask.objects.get_or_create(student=student, task=task)
    student_task.is_completed = not student_task.is_completed
    student_task.save()
    return redirect('student_dashboard')

@login_required
def review_dashboard(request):
    return render(request, 'review.html')  # Returns partial HTML

@csrf_exempt
@login_required
def submit_help_request(request):
    if request.method == "POST":
        request_type = request.POST.get("type")
        message = request.POST.get("message", "")
        HelpRequest.objects.create(
            student=request.user,
            request_type=request_type,
            message=message
        )
        return JsonResponse({"status": "success", "message": "Request submitted!"})
    return JsonResponse({"status": "error", "message": "Invalid request."})
