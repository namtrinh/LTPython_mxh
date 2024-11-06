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

    def followers_count(self):
        return self.followers.count()  # Số người theo dõi

    def following_count(self):
        return self.following.count()  # Số người mà người dùng đang theo dõi


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
    
   
#tao Model comment de luu binh luanj 
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE) 
    text = models.TextField()
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.text[:20]}"


class Block(models.Model):
    blocker = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="blocking")
    blocked = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="blocked")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('blocker', 'blocked')

    def __str__(self):
        return f"{self.blocker.email} blocked {self.blocked.email}"

        return f"{self.user.username} - {self.text[:20]}"

class Follower(models.Model):
    user = models.ForeignKey(CustomUser, related_name='following', on_delete=models.CASCADE)  # Người theo dõi
    follower = models.ForeignKey(CustomUser, related_name='followers', on_delete=models.CASCADE)  # Người được theo dõi

    class Meta:
        unique_together = ('user', 'follower')  # Đảm bảo rằng mỗi user chỉ theo dõi một follower một lần

    def __str__(self):
        return f"{self.follower.email} follows {self.user.email}"