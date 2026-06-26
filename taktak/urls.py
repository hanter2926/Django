from django.urls import path
from . import views 

urlpatterns = [
    path('', views.home, name='home'), 
    path('about/', views.about, name='about'),
    path('gallery/', views.gallery, name='gallery'),
    path('privacy-policy/', views.privacy_policy, name='privacy'),
    path('refund-policy/', views.refund_policy, name='refund'),
    path('shipping-policy/', views.shipping_policy, name='shipping'),
    path('terms-conditions/', views.terms_conditions, name='terms'),
    path('our-mission/', views.our_mission, name='mission'),
    path('our-vision/', views.our_vision, name='vision'),
    path('contact/', views.contact, name='contact'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('forget-password/', views.forget_password, name='forget_password'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('verify-registration/', views.verify_register_otp, name='verify_register_otp'),
]