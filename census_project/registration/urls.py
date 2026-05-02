from django.urls import path
from . import views 

urlpatterns = [
    path('register/', views.register_citizen, name='register'),
    path('send-otp/', views.send_otp_view, name='send_otp'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
]


