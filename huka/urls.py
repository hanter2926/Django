from django.urls import path
from . import views

from django.urls import path
from . import views

urlpatterns = [
    path('', views.game_home, name='game_home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('api/complete-level/', views.complete_level_api, name='complete_level_api'),
    path('social/', views.social_dashboard, name='social_dashboard'),
    path('social/send/<int:user_id>/', views.send_friend_request, name='send_friend_request'),
    path('social/accept/<int:request_id>/', views.accept_friend_request, name='accept_friend_request'),
    path('social/reject/<int:request_id>/', views.reject_friend_request, name='reject_friend_request'),
    path('chat/<int:friend_id>/', views.chat_room, name='chat_room'),
    path('chat/api/<int:friend_id>/', views.send_and_get_messages_api, name='send_and_get_messages_api'),
]