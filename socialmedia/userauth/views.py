import uuid
from itertools import chain
from django.core.cache import cache
from django.core.mail import send_mail
from  django . shortcuts  import  get_object_or_404, render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .models import Comment, Block
from django.utils import timezone

from .models import Followers, LikePost, Post, Profile, CustomUser
from django.db.models import Q

from django.contrib.auth.models import User
from .models import Post, LikePost

def signup(request):
    try:
        if request.method == 'POST':
            fnm = request.POST.get('fnm')
            emailid = request.POST.get('emailid')
            pwd = request.POST.get('pwd')

            # Kiểm tra xem tài khoản đã tồn tại hay chưa
            if CustomUser.objects.filter(email=emailid).exists():
                invalid = "email đã tồn tại."
                return render(request, 'signup.html', {'invalid': invalid})

            if CustomUser.objects.filter(username=fnm).exists():
                invalid = "Username đã tồn tại."
                return render(request, 'signup.html', {'invalid': invalid})

            # Tạo token xác minh
            activation_token = str(uuid.uuid4())

            # Kiểm tra số lần gửi email cho tài khoản này
            email_send_count_key = f"email_send_count_{emailid}"
            email_send_count = cache.get(email_send_count_key, 0)

            if email_send_count >= 7:
                invalid = "Bạn đã gửi yêu cầu xác thực quá số lần cho phép trong 10 phút."
                return render(request, 'signup.html', {'invalid': invalid})

            # Lưu thông tin tài khoản vào cache với thời gian timeout là 2 phút cho token
            cache.set(activation_token, {'fnm': fnm, 'emailid': emailid, 'pwd': pwd}, timeout=120)

            # Cập nhật bộ đếm số lần gửi email cho tài khoản trong 10 phút
            cache.set(email_send_count_key, email_send_count + 1, timeout=600)

            # Tạo đường dẫn xác minh
            activation_link = request.build_absolute_uri(reverse('activate', args=[activation_token]))

            # Gửi email xác thực
            send_mail(
                'Xác thực tài khoản của bạn',
                f'Nhấn vào link sau để kích hoạt tài khoản của bạn: {activation_link}',
                'Firefly-Media',
                [emailid],
                fail_silently=False,
            )

            return render(request, 'signup.html', {'message': "Một email xác thực đã được gửi đến bạn."})

    except Exception as e:
        invalid = "Có lỗi xảy ra."
        print(e)  # In ra lỗi nếu có
        return render(request, 'signup.html', {'invalid': invalid})

    return render(request, 'signup.html')


def activate_account(request, token):
    # Lấy thông tin tài khoản từ cache
    account_data = cache.get(token)

    if account_data:
        fnm = account_data['fnm']
        emailid = account_data['emailid']
        pwd = account_data['pwd']

        my_user = CustomUser(email=emailid, username=fnm)
        my_user.set_password(pwd)
        my_user.save()

        # Tạo hồ sơ người dùng và đánh dấu là đã kích hoạt
        new_profile = Profile.objects.create(user=my_user, activation_token=token, is_active=True)
        new_profile.save()
        cache.delete(token)

        return render(request, 'activation_success.html')  # Giao diện thông báo kích hoạt thành công
    else:
        return render(request, 'activation_error.html', {'message': "Liên kết xác thực không hợp lệ hoặc đã hết hạn."})
def loginn(request):
    if request.method == 'POST':
        emailid = request.POST.get('emailid')
        pwd = request.POST.get('pwd')
        print(emailid, pwd)
        userr = authenticate(request, email=emailid, password=pwd)  # Thay đổi đây

        if userr is not None:
            login(request, userr)
            return redirect('/')
        else:
            print("Authentication failed")  # Thêm dòng này để kiểm tra
            invalid = "Invalid Credentials"
            return render(request, 'loginn.html', {'invalid': invalid})

    return render(request, 'loginn.html')


@login_required(login_url='/loginn')
def logoutt(request):
    logout(request)
    return redirect('/loginn')



@login_required(login_url='/loginn')
def home(request):

    following_users = Followers.objects.filter(follower=request.user.username).values_list('user', flat=True)


    post = Post.objects.filter(Q(user=request.user.username) | Q(user__in=following_users)).order_by('-created_at')

    profile = Profile.objects.get(user=request.user)

    context = {
        'post': post,
        'profile': profile,
    }
    return render(request, 'main.html',context)



@login_required(login_url='/loginn')
def upload(request):
    if request.method == 'POST':
        user = request.user.username
        image = request.FILES.get('image_upload')
        video = request.FILES.get('video_upload')
        caption = request.POST['caption']

        # Tạo bài đăng chỉ khi có ít nhất ảnh hoặc video
        if image or video:
            new_post = Post.objects.create(user=user, image=image, video=video, caption=caption)
            new_post.save()

        return redirect('/')
    else:
        return redirect('/')


@login_required(login_url='/loginn')
def likes(request, id):
    if request.method == 'GET':
        username = request.user.username
        post = get_object_or_404(Post, id=id)

        like_filter = LikePost.objects.filter(post_id=id, username=username).first()

        if like_filter is None:
            new_like = LikePost.objects.create(post_id=id, username=username)
            post.no_of_likes = post.no_of_likes + 1
        else:
            like_filter.delete()
            post.no_of_likes = post.no_of_likes - 1

        post.save()

        # Generate the URL for the current post's detail page
        print(post.id)

        # Redirect back to the post's detail page
        return redirect('/#'+id)
    
@login_required(login_url='/loginn')
def comment(request, id):
    if request.method == 'POST':
        post = get_object_or_404(Post, id=id)
        
        # Lấy Profile của người dùng hiện tại
        profile = get_object_or_404(Profile, user=request.user)
        
        text = request.POST.get('text')
        
        # Tạo đối tượng Comment
        Comment.objects.create(post=post, user=request.user, profile=profile, text=text, created_at=timezone.now())
         
        return redirect('/#' + str(post.id))
    else:
        return HttpResponse(status=405)
    


@login_required(login_url='/loginn')
def explore(request):
    post=Post.objects.all().order_by('-created_at')
    profile = Profile.objects.get(user=request.user)

    context={
        'post':post,
        'profile':profile

    }
    return render(request, 'explore.html',context)

@login_required(login_url='/loginn')
def profile(request, id_user):
    user_object = get_object_or_404(CustomUser, username=id_user)

    # Kiểm tra xem người dùng hiện tại có bị chặn bởi người dùng đang xem hồ sơ không
    if Block.objects.filter(blocked=request.user, blocker=user_object).exists():
        return render(request, 'block_error.html', {'message': "Bạn không thể xem hồ sơ của người dùng này."})

    profile = Profile.objects.get(user=request.user)
    user_profile = Profile.objects.get(user=user_object)
    user_posts = Post.objects.filter(user=id_user).order_by('-created_at')
    user_post_length = len(user_posts)

    follower = request.user.username
    user = id_user

    # Kiểm tra nếu đã theo dõi hay chưa
    if Followers.objects.filter(follower=follower, user=user).first():
        follow_unfollow = 'Unfollow'
    else:
        follow_unfollow = 'Follow'

    # Kiểm tra nếu đã chặn hay chưa
    is_blocked = Block.objects.filter(blocker=request.user, blocked=user_object).exists()

    user_followers = len(Followers.objects.filter(user=id_user))
    user_following = len(Followers.objects.filter(follower=id_user))

    context = {
        'user_object': user_object,
        'user_profile': user_profile,
        'user_posts': user_posts,
        'user_post_length': user_post_length,
        'profile': profile,
        'follow_unfollow': follow_unfollow,
        'is_blocked': is_blocked,  # Thêm biến này vào context
        'user_followers': user_followers,
        'user_following': user_following,
    }

    if request.user.username == id_user:
        if request.method == 'POST':
            if request.FILES.get('image') is None:
                image = user_profile.profileimg
                bio = request.POST['bio']
                location = request.POST['location']

                user_profile.profileimg = image
                user_profile.bio = bio
                user_profile.location = location
                user_profile.save()
            else:
                image = request.FILES.get('image')
                bio = request.POST['bio']
                location = request.POST['location']

                user_profile.profileimg = image
                user_profile.bio = bio
                user_profile.location = location
                user_profile.save()

            return redirect('/profile/' + id_user)

    return render(request, 'profile.html', context)

@login_required(login_url='/loginn')
def delete(request, id):
    post = Post.objects.get(id=id)
    post.delete()

    return redirect('/profile/'+ request.user.username)


@login_required(login_url='/loginn')
def search_results(request):
    query = request.GET.get('q')
    current_user = request.user

    # Lấy danh sách các người đã chặn current_user
    blocked_by_users = Block.objects.filter(blocked=current_user).values_list('blocker__username', flat=True)

    # Tìm kiếm người dùng
    users = Profile.objects.filter(user__username__icontains=query)

    # Nếu current_user bị chặn, loại bỏ những người đã chặn current_user khỏi kết quả tìm kiếm
    if blocked_by_users.exists():
        users = users.exclude(user__username__in=blocked_by_users)

    # Nếu current_user không bị chặn, cho phép tìm kiếm tất cả
    # Không cần kiểm tra lại ở đây vì đã lọc ở trên
    # users = Profile.objects.filter(user__username__icontains=query)

    posts = Post.objects.filter(caption__icontains=query)

    context = {
        'query': query,
        'users': users,
        'posts': posts,
    }
    return render(request, 'search_user.html', context)


def home_post(request,id):
    post=Post.objects.get(id=id)
    profile = Profile.objects.get(user=request.user)
    context={
        'post':post,
        'profile':profile
    }
    return render(request, 'main.html',context)



def follow(request):
    if request.method == 'POST':
        follower = request.POST['follower']
        user = request.POST['user']

        if Followers.objects.filter(follower=follower, user=user).first():
            delete_follower = Followers.objects.get(follower=follower, user=user)
            delete_follower.delete()
            return redirect('/profile/'+user)
        else:
            new_follower = Followers.objects.create(follower=follower, user=user)
            new_follower.save()
            return redirect('/profile/'+user)
    else:
        return redirect('/')


def block_user(request, user_id):
    if request.method == 'POST':
        user_to_block = get_object_or_404(CustomUser, id=user_id)
        print(user_id)

        # Hủy theo dõi từ phía người chặn
        Followers.objects.filter(follower=request.user.username, user=user_to_block.username).delete()

        # Hủy theo dõi từ phía người bị chặn (nếu có)
        Followers.objects.filter(follower=user_to_block.username, user=request.user.username).delete()

        # Chặn người dùng
        block_instance, created = Block.objects.get_or_create(blocker=request.user, blocked=user_to_block)

        if created:
            # Người dùng đã được chặn thành công
            return redirect('profile', id_user=user_to_block.username)
        else:
            # Người dùng đã được chặn trước đó
            return redirect('profile', id_user=user_to_block.username)

    return redirect('/')

@login_required(login_url='/loginn')
def unblock_user(request, user_id):
    user_to_unblock = get_object_or_404(CustomUser, id=user_id)

    if request.method == 'POST':
        # Tìm bản ghi chặn
        block_instance = Block.objects.filter(blocker=request.user, blocked=user_to_unblock).first()

        if block_instance:
            block_instance.delete()  # Xóa bản ghi chặn
            return redirect('/profile/' + user_to_unblock.username)

    return render(request, 'error.html', {'message': "Bạn không thể bỏ chặn người dùng này."})

@login_required(login_url='/login')
def likes(request, id):
    if request.method == 'GET':
        username = request.user.username
        post = get_object_or_404(Post, id=id)

        like_filter = LikePost.objects.filter(post_id=id, username=username).first()

        if like_filter is None:
            new_like = LikePost.objects.create(post_id=id, username=username)
            post.no_of_likes = post.no_of_likes + 1
        else:
            like_filter.delete()
            post.no_of_likes = post.no_of_likes - 1

        post.save()

        return redirect('/#'+str(id))

# views.py
from django.shortcuts import render
from .models import Post, LikePost


@login_required(login_url='/loginn')
def like_list(request, post_id):
    post = Post.objects.get(id=post_id)
    liked_users = LikePost.objects.filter(post_id=post.id)

    # Lấy thông tin người dùng đã thích bài viết
    liked_user_profiles = []
    for like in liked_users:
        user = CustomUser.objects.get(username=like.username)  # Lấy đối tượng người dùng
        profile = Profile.objects.get(user=user)  # Lấy profile của người dùng
        liked_user_profiles.append({
            'username': user.username,
            'profile_img': profile.profileimg.url if profile.profileimg else '/static/default_avatar.jpg'  # Đảm bảo có ảnh mặc định
        })

    return render(request, 'like_list.html', {'post': post, 'liked_user_profiles': liked_user_profiles})
