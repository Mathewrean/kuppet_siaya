from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'claims', views.BBFClaimViewSet, basename='bbf-claims')
router.register(r'beneficiaries', views.BBFBeneficiaryViewSet, basename='bbf-beneficiaries')

urlpatterns = [
    path('', include(router.urls)),
    # Member endpoints
    path('claims/', views.BBFClaimViewSet.as_view({'get': 'list', 'post': 'create'}), name='bbf-claims-list'),
    path('claims/<int:pk>/', views.BBFClaimViewSet.as_view({'get': 'retrieve'}), name='bbf-claims-detail'),
    path('claims/<int:claim_id>/beneficiaries/', views.BBFBeneficiaryViewSet.as_view({'post': 'create'}), name='bbf-claims-add-beneficiary'),
    path('beneficiaries/<int:pk>/delete/', views.BBFBeneficiaryViewSet.as_view({'delete': 'destroy'}), name='bbf-beneficiary-delete'),
    # Subcounty endpoints
    path('subcounty/claims/', views.subcounty_claims, name='subcounty-claims'),
    path('subcounty/claims/<int:pk>/confirm/', views.subcounty_confirm_claim, name='subcounty-confirm-claim'),
    path('subcounty/claims/<int:pk>/reject/', views.subcounty_reject_claim, name='subcounty-reject-claim'),
    path('beneficiaries/<int:pk>/approve/', views.BBFBeneficiaryViewSet.as_view({'post': 'approve'}), name='beneficiary-approve'),
    path('beneficiaries/<int:pk>/reject/', views.BBFBeneficiaryViewSet.as_view({'post': 'reject'}), name='beneficiary-reject'),
    # County endpoints
    path('county/claims/', views.county_claims, name='county-claims'),
    path('county/claims/<int:pk>/confirm/', views.county_approve_claim, name='county-approve-claim'),
    path('county/claims/<int:pk>/reject/', views.county_reject_claim, name='county-reject-claim'),
]