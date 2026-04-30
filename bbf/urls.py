from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'claims', views.BBFClaimViewSet, basename='bbf-claims')
router.register(r'beneficiaries', views.BBFBeneficiaryViewSet, basename='bbf-beneficiaries')

urlpatterns = [
    # API routes
    path('', include(router.urls)),
    
    # Member endpoints
    path('claims/', views.BBFClaimViewSet.as_view({'get': 'list', 'post': 'create'}), name='bbf-claims-list'),
    path('claims/<int:pk>/', views.BBFClaimViewSet.as_view({'get': 'retrieve'}), name='bbf-claims-detail'),
    path('claims/<int:pk>/beneficiaries/', views.BBFClaimViewSet.as_view({'post': 'add_beneficiary'}), name='bbf-claims-add-beneficiary'),
    
    # Subcounty Representative endpoints
    path('subcounty/claims/', views.subcounty_claims, name='subcounty-claims'),
    path('subcounty/claims/<int:pk>/confirm/', views.subcounty_confirm_claim, name='subcounty-confirm-claim'),
    path('subcounty/claims/<int:pk>/reject/', views.subcounty_reject_claim, name='subcounty-reject-claim'),
    
    # County Representative endpoints
    path('county/claims/', views.county_claims, name='county-claims'),
    path('county/claims/<int:pk>/confirm/', views.county_approve_claim, name='county-approve-claim'),
    path('county/claims/<int:pk>/reject/', views.county_reject_claim, name='county-reject-claim'),
    
    # Beneficiary approval endpoints
    path('beneficiaries/<int:pk>/approve/', views.BBFBeneficiaryViewSet.as_view({'post': 'approve'}), name='beneficiary-approve'),
    path('beneficiaries/<int:pk>/reject/', views.BBFBeneficiaryViewSet.as_view({'post': 'reject'}), name='beneficiary-reject'),
]