from django.contrib import admin
from django.urls import path
from socialmedia import settings
from userauth import views
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home),
    path('admin/', admin.site.urls),
    path('loginn/', views.loginn),
    path('signup/', views.signup),
    path('logoutt/', views.logoutt),
    path('upload', views.upload),
    path('like-post/<str:id>', views.likes, name='like-post'),
    path('#<str:id>', views.home_post),
    path('explore', views.explore),
    path('profile/<str:id_user>', views.profile, name='profile'),
    path('delete/<str:id>', views.delete),
    path('search-results/', views.search_results, name='search_results'),
    path('follow', views.follow, name='follow'),
    path('activate/<str:token>/', views.activate_account, name='activate'),
    path('comment/<str:id>/', views.comment, name='comment'),
    path('block/<str:user_id>/', views.block_user, name='block_user'),
    path('unblock/<str:user_id>/', views.unblock_user, name='unblock_user'),
    
    path('followers/<str:id_user>', views.followers_list, name='followers_list'),
    path('following/<str:id_user>', views.following_list, name='following_list'),
    path('report_post/<uuid:post_id>/', views.report_post, name='report_post'),


]
