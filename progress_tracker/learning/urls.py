# learning/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('student_dashboard/', views.student_dashboard, name='student_dashboard'),
    path('complete-task/<int:task_id>/', views.complete_task, name='complete_task'),
    path('login/', views.student_login, name='student_login'),
    path('logout/', views.student_logout, name='student_logout'),
    path('submit-review/', views.submit_review, name='submit_review'),

]
