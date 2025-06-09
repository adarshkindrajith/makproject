
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from learning import views as learning_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    
    # Include learning app URLs (like dashboard, login, etc)
    path('', include('learning.urls')),
     path('staff/', include('staff.urls')),
     path('staff/', lambda request: redirect('staff_login')),  # ✅ This line
    path('review/', include('review.urls')),
    path('', include('chat.urls')),
   
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
