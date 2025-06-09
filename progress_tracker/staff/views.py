from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from review.models import HelpRequest
from learning.models import Module, Task, StudentTask, StudentCurrentModule  


# Staff login view
def staff_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user and user.is_staff:
            login(request, user)
            return redirect('staff_dashboard')
        return render(request, 'staff/login.html', {
            "error": "Invalid credentials or not a staff member"
        })
    return render(request, 'staff/login.html')


# Staff logout
@login_required(login_url='staff_login')
def staff_logout(request):
    logout(request)
    return redirect('staff_login')


# ✅ Staff Dashboard View
@user_passes_test(lambda u: u.is_authenticated and u.is_staff, login_url='/staff/login/')
def staff_dashboard_view(request):
    student_users = User.objects.filter(is_staff=False)
    students = []

    for student in student_users:
        # ✅ Fetch current module for each student individually
        student_module = StudentCurrentModule.objects.filter(student=student).first()
        current_module = student_module.module if student_module else Module.objects.first()

        tasks = Task.objects.filter(module=current_module) if current_module else []
        total_tasks = tasks.count()

        completed_tasks = StudentTask.objects.filter(
            student=student,
            task__in=tasks,
            is_completed=True
        ).count()

        progress = int((completed_tasks / total_tasks) * 100) if total_tasks else 0

        if progress >= 75:
            status = "On Track"
        elif progress >= 40:
            status = "Needs Help"
        else:
            status = "Behind Schedule"

        students.append({
            'student': student,
            'current_module': current_module.name if current_module else "No Module",
            'current_module_week': current_module.week if current_module else None,
            'completed': completed_tasks,
            'total': total_tasks,
            'progress': progress,
            'status': status,
        })

    help_requests = HelpRequest.objects.order_by('-created_at').select_related('student', 'accepted_by')

    return render(request, 'staff/staff.html', {
        'students': students,
        'help_requests': help_requests,
    })


# Accept a help request
@user_passes_test(lambda u: u.is_authenticated and u.is_staff, login_url='/staff/login/')
def accept_help_request(request, request_id):
    help_request = get_object_or_404(HelpRequest, id=request_id)
    if not help_request.accepted_by:
        help_request.accepted_by = request.user
        help_request.save()
    return redirect('staff_dashboard')


# Mark request as handled
@user_passes_test(lambda u: u.is_authenticated and u.is_staff, login_url='/staff/login/')
def mark_request_handled(request, request_id):
    help_request = get_object_or_404(HelpRequest, id=request_id)
    if help_request.accepted_by == request.user:
        help_request.is_handled = True
        help_request.save()
    return redirect('staff_dashboard')


# Student module progress view
def student_module_progress(request, student_id):
    student = get_object_or_404(User, id=student_id, is_staff=False)
    modules = Module.objects.all()
    module_progress = []

    for module in modules:
        total_tasks = module.tasks.count()
        completed_tasks = StudentTask.objects.filter(
            student=student,
            task__module=module,
            is_completed=True
        ).count()

        if completed_tasks == total_tasks and total_tasks > 0:
            status = "Completed"
        elif completed_tasks > 0:
            status = "In Progress"
        else:
            status = "Not Started"

        module_progress.append({
            "name": module.name,
            "status": status
        })

    return render(request, 'staff/student_module_progress.html', {
        "progress": {
            "student_id": student.id,
            "modules": module_progress
        }
    })


from django.contrib import messages

@user_passes_test(lambda u: u.is_authenticated and u.is_staff, login_url='/staff/login/')
def approve_next_week(request, student_id):
    student = get_object_or_404(User, id=student_id, is_staff=False)
    modules = list(Module.objects.all().order_by('week'))  # Or by 'id' if no 'week' field

    student_module, _ = StudentCurrentModule.objects.get_or_create(student=student)

    if student_module.module in modules:
        current_index = modules.index(student_module.module)
        if current_index + 1 < len(modules):
            student_module.module = modules[current_index + 1]
            student_module.save()
            messages.success(request, f"Approved {student.username} for next module: {student_module.module.name}")
        else:
            messages.info(request, f"{student.username} is already on the last module.")
    elif modules:
        # Assign the first module if student has no module assigned yet
        student_module.module = modules[0]
        student_module.save()
        messages.success(request, f"Assigned first module {modules[0].name} to {student.username}.")
    else:
        messages.error(request, "No modules available to assign.")

    return redirect('staff_dashboard')
