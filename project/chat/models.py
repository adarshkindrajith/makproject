from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', default='profile_pics/makbig.png', null=True, blank=True)
    badge = models.ImageField(upload_to='profile_pics/', default='profile_pics/default.jpg', null=True, blank=True)

class Message(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    reported = models.BooleanField(default=False)
    pinned = models.BooleanField(default=False) 
    replied_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies') 
    

    def __str__(self):
        return f'{self.user.username}: {self.content[:50]}'
