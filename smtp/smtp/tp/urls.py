from django.urls import path, include
from rest_framework import routers
from .api import CourseViewSet, LessonViewSet, PaymentViewSet
from . import views
from django.contrib.auth import views as auth_views
from .api import RegisterView
from rest_framework.authtoken.views import obtain_auth_token

router = routers.DefaultRouter()
router.register(r'courses', CourseViewSet)
router.register(r'lessons', LessonViewSet)
router.register(r'payments', PaymentViewSet, basename='payment')

app_name = 'tp'

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/auth/register/', RegisterView.as_view(), name='api_register'),
    path('api/auth/token/', obtain_auth_token, name='api_token'),
    # Auth web routes
    path('accounts/login/', auth_views.LoginView.as_view(template_name='tp/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='tp:home'), name='logout'),
    path('accounts/register/', views.RegisterView.as_view(), name='register'),

    # Web/UI views
    path('', views.HomeView.as_view(), name='home'),
    path('courses/', views.CourseListView.as_view(), name='course_list'),
    path('courses/create/', views.CourseCreateView.as_view(), name='course_create'),
    path('courses/<int:pk>/', views.CourseDetailView.as_view(), name='course_detail'),
    path('courses/<int:pk>/edit/', views.CourseUpdateView.as_view(), name='course_edit'),
    path('courses/<int:pk>/delete/', views.CourseDeleteView.as_view(), name='course_delete'),
    path('courses/<int:pk>/purchase/', views.CoursePurchaseView.as_view(), name='course_purchase'),
    path('payments/webhook/', views.RazorpayWebhookView.as_view(), name='payment_webhook'),

    path('courses/<int:course_pk>/lessons/create/', views.LessonCreateView.as_view(), name='lesson_create'),
    path('lessons/<int:pk>/', views.LessonDetailView.as_view(), name='lesson_detail'),
    path('lessons/<int:pk>/edit/', views.LessonUpdateView.as_view(), name='lesson_edit'),
    path('lessons/<int:pk>/delete/', views.LessonDeleteView.as_view(), name='lesson_delete'),
]
