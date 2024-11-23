from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.contrib.admin.models import LogEntry, CHANGE
from django.db import transaction

from socialmedia import settings
# Register your models here.

from .models import *

admin.site.register(Profile)

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
                    'cunnconn01@gmail.com',  # Thay bằng email của bạn
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


from django.core.mail import send_mail
from django.contrib import admin
from .models import CustomUser

class CustomUserAdmin(admin.ModelAdmin):

    def save_model(self, request, obj, form, change):
        # Kiểm tra nếu thuộc tính is_active đã thay đổi
        if change and 'is_active' in form.changed_data:
            # Gửi email nếu trạng thái is_active thay đổi
            if obj.is_active:
                subject = 'Tài khoản của bạn đã được kích hoạt'
                message = f'Chào {obj.username},\n\nTài khoản của bạn đã được kích hoạt và bạn có thể đăng nhập vào hệ thống.'
            else:
                subject = 'Thông báo tài khoản đã bị khóa'
                message = f'Chào {obj.username},\n\nTài khoản của bạn đã bị khóa và bạn không thể đăng nhập vào hệ thống. Nếu bạn có thắc mắc, vui lòng liên hệ với chúng tôi.'

            recipient_email = obj.email
            if recipient_email:
                try:
                    send_mail(
                        subject,
                        message,
                        'cunnconn01@gmail.com',  # Thay bằng email của bạn
                        [recipient_email],  # Gửi email tới người dùng
                        fail_silently=False,
                    )
                except Exception as e:
                    print(f"Error sending email: {e}")

        # Lưu lại thay đổi
        super().save_model(request, obj, form, change)


    def delete_model(self, request, obj):
        # Lấy email của người dùng
        recipient_email = obj.email
        print(recipient_email)
        if recipient_email:
            try:
                send_mail(
                    'Thông báo tài khoản đã bị xóa',
                    f'Chào {obj.username},\n\nTài khoản của bạn đã bị xóa khỏi hệ thống.\n\nNếu bạn có thắc mắc, vui lòng liên hệ với chúng tôi.',
                    'cunnconn01@gmail.com',
                    [recipient_email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Error sending email: {e}")

        super().delete_model(request, obj)

admin.site.register(CustomUser, CustomUserAdmin)
