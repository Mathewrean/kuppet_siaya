from django.urls import path
from . import views

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('bbf-status/', views.BBFStatusView.as_view(), name='bbf_status'),
    path('bbf-claims/', views.BBFClaimsListView.as_view(), name='bbf_claims'),
    path('bbf-claims/new/', views.BBFClaimCreateView.as_view(), name='bbf_claim_create'),
    path('bbf-claims/<int:pk>/', views.BBFClaimDetailView.as_view(), name='bbf_claim_detail'),
    path('subcounty/dashboard/', views.SubcountyDashboardView.as_view(), name='subcounty_dashboard'),
    path('subcounty/claims/<int:pk>/', views.SubcountyClaimReviewView.as_view(), name='subcounty_claim_review'),
    path('county/dashboard/', views.CountyDashboardView.as_view(), name='county_dashboard'),
    path('county/claims/<int:pk>/', views.CountyClaimReviewView.as_view(), name='county_claim_review'),
    path('financials/', views.FinancialsView.as_view(), name='financials'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('request-info/', views.SupportView.as_view(), name='support'),
]