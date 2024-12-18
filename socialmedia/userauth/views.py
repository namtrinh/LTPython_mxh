import uuid

from django.contrib import messages
from django.core.cache import cache
from django.core.mail import send_mail
from  django . shortcuts  import  get_object_or_404, render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .models import Comment, Block, SavedPost
from django.utils import timezone
from .models import Follower, LikePost,  CustomUser

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


            activation_token = str(uuid.uuid4())
            # Kiểm tra số lần gửi email cho tài khoản này
            email_send_count_key = f"email_send_count_{emailid}"
            email_send_count = cache.get(email_send_count_key, 0)

            if email_send_count >= 7:
                invalid = "Bạn đã gửi yêu cầu xác thực quá số lần cho phép trong 10 phút."
                return render(request, 'signup.html', {'invalid': invalid})

            cache.set(activation_token, {'fnm': fnm, 'emailid': emailid, 'pwd': pwd}, timeout=120)
            cache.set(email_send_count_key, email_send_count + 1, timeout=600)
            activation_link = request.build_absolute_uri(reverse('activate', args=[activation_token]))

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

    account_data = cache.get(token)
    if account_data:
        fnm = account_data['fnm']
        emailid = account_data['emailid']
        pwd = account_data['pwd']
        my_user = CustomUser(email=emailid, username=fnm)
        my_user.set_password(pwd)
        my_user.save()
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


from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Post, Profile, Followers


@login_required(login_url='/loginn')
def home(request):
    # Get the logged-in user instance
    current_user = request.user

    # Get users that the logged-in user follows
    following_users = Follower.objects.filter(follower=current_user).values_list('user__username', flat=True)

    # Get users who follow the logged-in user
    followers = Follower.objects.filter(user=current_user).values_list('follower__username', flat=True)

    # Combine posts from the logged-in user, users they follow, and users who follow them
    post = Post.objects.filter(
        Q(user=current_user.username) | Q(user__in=following_users) | Q(user__in=followers)
    ).order_by('-created_at')

    # Get the logged-in user's profile
    profile = Profile.objects.get(user=current_user)

    context = {
        'post': post,
        'profile': profile,
    }
    return render(request, 'main.html', context)

@login_required(login_url='/loginn')
def upload(request):

    if request.method == 'POST':
        user = request.user.username
        image = request.FILES.get('image_upload')
        caption = request.POST['caption']
        video = request.FILES.get('video_upload')

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
    follower = request.user.username
    user = id_user
    post_saved_db = SavedPost.objects.filter(user=request.user)
    user_post_length = len(user_posts)

    follower = CustomUser.objects.get(username=request.user.username)

    # Kiểm tra nếu đã theo dõi hay chưa
    if Follower.objects.filter(follower=follower, user=user_object).exists():
        follow_unfollow = 'Unfollow'
    else:
        follow_unfollow = 'Follow'

    user_follower = Follower.objects.filter(user=user_object)  # Lấy tất cả người theo dõi
    user_following = len(Followers.objects.filter(follower=id_user))

    user_followers_count = user_follower.count()  # Số lượng người theo dõi
    user_following_count = Follower.objects.filter(
        follower=user_object).count()  # Số lượng người mà người dùng này đang theo dõi

    # Kiểm tra nếu đã chặn hay chưa
    is_blocked = Block.objects.filter(blocker=request.user, blocked=user_object).exists()



    context = {
        'user_object': user_object,
        'user_profile': user_profile,
        'user_posts': user_posts,
        'user_post_length': user_post_length,
        'profile': profile,
        'follow_unfollow': follow_unfollow,
        'user_followers': user_follower,  # Truyền danh sách followers vào context
        'user_following': user_following,
        'user_followers_count': user_followers_count,
        'user_following_count': user_following_count,
        'profile_id': profile.user.id,
        'post_saved_db': post_saved_db,
        'is_blocked': is_blocked
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

"""

def profile(request, id_user):
    try:
        user_object = CustomUser.objects.get(username=id_user)
        profile = Profile.objects.get(user=user_object)
        user_profile = Profile.objects.get(user=user_object)
        user_posts = Post.objects.filter(user=id_user).order_by('-created_at')
        user_post_length = len(user_posts)
        post_saved_db = SavedPost.objects.filter(user=request.user)

        # người dùng hiện tại
        follower = CustomUser.objects.get(username=request.user.username)

        # Kiểm tra xem người dùng hiện tại có đang theo dõi người dùng này không
        if Follower.objects.filter(follower=follower, user=user_object).exists():
            follow_unfollow = 'Unfollow'
        else:
            follow_unfollow = 'Follow'

        user_follower = Follower.objects.filter(user=user_object)  # Lấy tất cả người theo dõi
        user_followers_count = user_follower.count()  # Số lượng người theo dõi
        user_following_count = Follower.objects.filter(follower=user_object).count()  # Số lượng người mà người dùng này đang theo dõi

        print(user_followers_count)
        print(user_followers_count)

        context = {
            'user_object': user_object,
            'user_profile': user_profile,
            'user_posts': user_posts,
            'user_post_length': user_post_length,
            'profile': profile,
            'follow_unfollow': follow_unfollow,
            'user_followers': user_follower,  # Truyền danh sách followers vào context
            'user_followers_count': user_followers_count,
            'user_following_count': user_following_count,
            'profile_id': profile.user.id,
            'post_saved_db': post_saved_db,

        }

        if request.user.username == id_user:
            if request.method == 'POST':
                # Cập nhật hồ sơ
                image = request.FILES.get('image', user_profile.profileimg)  # Sử dụng ảnh hiện tại nếu không có ảnh mới
                bio = request.POST['bio']
                location = request.POST['location']
                user_profile.profileimg = image
                user_profile.bio = bio
                user_profile.location = location
                user_profile.save()

                return redirect('/profile/'+id_user)
            else:
                return render(request, 'profile.html', context)

        return render(request, 'profile.html', context)

    except Exception as ex:
        print(ex)
        return HttpResponse("Lỗi rồi")

"""

@login_required(login_url='/loginn')
def delete(request, id):
    post = Post.objects.get(id=id)
    post.delete()



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
    """ if request.method == 'POST':
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
        return redirect('/') """

    if request.method == 'POST':
        follower = CustomUser.objects.get(username=request.POST['follower'])
        user = CustomUser.objects.get(username=request.POST['user'])

        if Follower.objects.filter(follower=follower, user=user).first():
            delete_follower = Follower.objects.get(follower=follower, user=user)
            delete_follower.delete()
            return redirect('/profile/' + user.username)
        else:
            new_follower = Follower.objects.create(follower=follower, user=user)
            new_follower.save()
            return redirect('/profile/' + user.username)
    else:
        return redirect('/')

@login_required(login_url='/login')
def followers_list(request, id_user):
    user_object = CustomUser.objects.get(id=id_user)
    followers = Follower.objects.filter(user=user_object).select_related('follower')

    context = {
        'user_object': user_object,
        'followers': followers
    }

    return render(request, 'followers_list.html', context)

@login_required(login_url='/login')
def following_list(request, id_user):
    user_object = CustomUser.objects.get(id=id_user)
    following = Follower.objects.filter(follower=user_object).select_related('user')

    context = {
        'user_object': user_object,
        'following': following,
    }

    return render(request, 'following_list.html', context)


def block_user(request, user_id):

    if request.method == 'POST':
        user_to_block = get_object_or_404(CustomUser, id=user_id)
        print(user_id)
        # Hủy theo dõi từ phía người chặn
        Follower.objects.filter(follower=request.user.id, user=user_to_block.id).delete()
        # Hủy theo dõi từ phía người bị chặn (nếu có)
        Follower.objects.filter(follower=user_to_block.id, user=request.user.id).delete()
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


def report_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    # Tăng số lượng báo cáo
    post.no_of_reports += 1
    post.save()

    # Redirect về trang chủ hoặc trang bài viết
    return redirect('/')


@login_required(login_url='/loginn')
def save_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    user = request.user

    # Prevent users from saving their own posts
    if post.user is not request.user:
        saved_post, created = SavedPost.objects.get_or_create(user=user, post=post)

        if created:
            messages.success(request, "Post saved successfully!")
        else:
            messages.info(request, "You have already saved this post.")
    else:
        messages.warning(request, "You cannot save your own post.")
        return redirect('/')

    return redirect('/')

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