from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('initialize-account/', views.initialize_account, name='initialize_account'),
    path('otp-verify/', views.otp_verify, name='otp_verify'),
    path('logout/', views.logout_view, name='logout'),
    path('verify-tsc/', views.verify_tsc, name='verify_tsc'),
    path('api/sub-counties/', views.sub_counties_api, name='sub_counties_api'),
    path('api/schools/', views.schools_api, name='schools_api'),
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset-confirm/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('password-reset-complete/', views.password_reset_complete, name='password_reset_complete'),
    path('admin-reset-password/', views.admin_reset_password, name='admin_reset_password'),
    path('health/', views.health_check, name='health_check'),
]
