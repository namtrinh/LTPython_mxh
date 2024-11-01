from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import UserManager
from django.db import models
from django.contrib.auth import get_user_model
import uuid
from datetime import datetime

# Định nghĩa CustomUser ở đây (đảm bảo rằng nó được định nghĩa trước khi được sử dụng)
class CustomUser(AbstractBaseUser):
    email = models.EmailField(unique=True)  # Địa chỉ email là duy nhất
    username = models.CharField(max_length=150, blank=True)  # Không duy nhất
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Không yêu cầu fields khác

    def __str__(self):
        return self.email


# Sử dụng CustomUser trong Profile
class Profile(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # Sửa tên CustomerUser thành CustomUser
    id_user = models.AutoField(primary_key=True)  # Sử dụng AutoField để tự động tăng
    bio = models.TextField(blank=True, default='')
    profileimg = models.ImageField(upload_to='profile_images', default='blank-profile-picture.png')
    location = models.CharField(max_length=100, blank=True, default='')
    activation_token = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


class Post(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.CharField(max_length=100)
    image = models.ImageField(upload_to='post_images')
    caption = models.TextField()
    created_at = models.DateTimeField(default=datetime.now)
    no_of_likes = models.IntegerField(default=0)

    def __str__(self):
        return self.user


class LikePost(models.Model):
    post_id = models.CharField(max_length=500)
    username = models.CharField(max_length=100)

    def __str__(self):
        return self.username


class Followers(models.Model):
    follower = models.CharField(max_length=100)
    user = models.CharField(max_length=100)

    def __str__(self):
        return self.user
