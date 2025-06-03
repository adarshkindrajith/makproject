from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('', views.login_view, name='login'),
    path('chat/', views.chatroom_view, name='chatroom'),
    path('owner/', views.owner_panel, name='owner'),
    path('report/<int:msg_id>/', views.report_message, name='report'),
    path('delete/<int:msg_id>/', views.delete_message, name='delete'),
]
