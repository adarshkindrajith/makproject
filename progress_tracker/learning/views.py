# learning/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from learning.models import Module, Task, StudentTask,StudentCurrentModule,StudentBadge,Badge

def student_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user and not user.is_staff:
            login(request, user)
            return redirect('student_dashboard')
        return render(request, 'learning/login.html', {"error": "Invalid credentials or staff user."})
    return render(request, 'learning/login.html')

def student_logout(request):
    logout(request)
    return redirect('student_login')

@login_required
def student_dashboard(request):
    student = request.user

    # Get the current module for the student
    student_module = StudentCurrentModule.objects.filter(student=student).first()
    module = student_module.module if student_module else Module.objects.first()

    # Get tasks for the current module
    tasks = module.tasks.order_by('order') if module else Task.objects.none()

    # Check task completion status
    task_statuses = [
        {
            'task': task,
            'is_completed': StudentTask.objects.filter(student=student, task=task, is_completed=True).exists()
        }
        for task in tasks
    ]

    completed = sum(1 for t in task_statuses if t['is_completed'])
    total = len(task_statuses)
    progress = (completed / total) * 100 if total else 0

    # ✅ Award all badges for weeks <= current module week
    if module:
        badges_to_award = Badge.objects.filter(module__week__lte=module.week)
        for badge in badges_to_award:
            StudentBadge.objects.get_or_create(student=student, badge=badge)

    # ✅ Get all badges earned by the student
    student_badges = StudentBadge.objects.filter(student=student).select_related('badge')

    return render(request, 'learning/student_dashboard.html', {
        'module': module,
        'task_statuses': task_statuses,
        'progress': int(progress),
        'completed': completed,
        'total': total,
        'student_badges': student_badges,
    })

@login_required
def complete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    student_task, _ = StudentTask.objects.get_or_create(student=request.user, task=task)
    student_task.is_completed = not student_task.is_completed
    student_task.save()
    return redirect('student_dashboard')

@login_required
def submit_review(request):
    if request.method == 'POST':
        # Save the review logic (if needed)
        return redirect('student_dashboard')
    return redirect('student_dashboard')
