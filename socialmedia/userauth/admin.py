from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.contrib.admin.models import LogEntry, CHANGE
from django.db import transaction

# Register your models here.

from .models import *

admin.site.register(Profile)

admin.site.register(CustomUser)



class PostAdmin(admin.ModelAdmin):
    list_display = ('user', 'caption', 'created_at', 'no_of_reports', 'no_of_likes')
    list_filter = ('no_of_reports',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.filter(no_of_reports__gt=0)  # Hiển thị chỉ những bài viết có số báo cáo > 0

    def delete_model(self, request, obj):
        try:
            # Sử dụng transaction để tránh việc ghi log
            with transaction.atomic():
                # Lấy thông tin người dùng từ tên người dùng trong bài đăng
                user = CustomUser.objects.get(username=obj.user)

                # Lấy email người dùng để gửi email thông báo
                user_email = user.email

                # Gửi email thông báo
                send_mail(
                    'Your Post Has Been Deleted',
                    f'Your post "{obj.caption}" has been deleted because it received too many reports.',
                    'your-email@example.com',  # Thay bằng email của bạn
                    [user_email],  # Gửi email tới người dùng
                    fail_silently=False,
                )

                # Thực hiện xóa bài viết mà không ghi log vào django_admin_log
                obj.delete()

        except CustomUser.DoesNotExist:
            # Nếu không tìm thấy người dùng với tên tương ứng
            pass
        except ObjectDoesNotExist:
            # Nếu không tìm thấy đối tượng bài viết hoặc lỗi khác
            pass

admin.site.register(Post, PostAdmin)