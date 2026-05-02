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
]
