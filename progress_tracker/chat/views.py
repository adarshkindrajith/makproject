from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from .forms import CustomUserCreationForm
from .models import Message, CustomUser
from django.contrib.auth.decorators import login_required

def register_view(request):
    form = CustomUserCreationForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('chatroom')
    return render(request, 'chat/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        uname = request.POST['username']
        pwd = request.POST['password']
        user = authenticate(request, username=uname, password=pwd)
        if user:
            login(request, user)
            return redirect('chatroom')
    return render(request, 'chat/login.html')


@login_required
def chatroom_view(request):
    messages = Message.objects.all().order_by('timestamp')
    reported_msgs = Message.objects.filter(reported=True).order_by('-timestamp') # Fetch all reported messages
    context = {
        'messages': messages,
        'reported_msgs': reported_msgs, # Pass them to the template
        'user': request.user,
    }
    return render(request, 'chat/chatroom.html', context)



@login_required
def owner_panel(request):
    if not request.user.is_superuser:
        return redirect('chatroom')
    users = CustomUser.objects.all()


    reported_msgs = (Message.objects
                     .filter(reported=True)
                     .select_related("user")
                     .order_by("-timestamp"))




    if request.method == 'POST':
        user_id = request.POST['user_id']
        badge = request.FILES.get('badge', None)
        user = CustomUser.objects.get(id=user_id)
        user.badge = badge
        user.save()
    return render(request, 'chat/owner_panel.html', {'users': users, "reported_msgs": reported_msgs})




@login_required
def report_message(request, msg_id):
    Message.objects.filter(id=msg_id).update(reported=True)
    return redirect("chatroom")


@login_required
def delete_message(request, msg_id):
    if request.user.is_superuser:
        Message.objects.get(id=msg_id).delete()
    return redirect('chatroom')
            