from django.urls import path
from . import views

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('bbf-status/', views.BBFStatusView.as_view(), name='bbf_status'),
    path('financials/', views.FinancialsView.as_view(), name='financials'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('request-info/', views.SupportView.as_view(), name='support'),
]