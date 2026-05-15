from django.urls import path
from . import views

urlpatterns = [

    path('', views.product_list, name='product_list'),
    path('create/', views.product_create, name='product_create'),
    path('edit/<int:pk>/', views.product_edit, name='product_edit'),
    path('delete/<int:pk>/', views.product_delete, name='product_delete'),
    path('settings/', views.profile_settings, name='profile_settings'),
    path('story/upload/', views.upload_story, name='upload_story'),
    path('register/', views.register, name='register'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('logout/', views.custom_logout, name='logout'),
    path('profile/', views.profile_view, name='profile'),
]


