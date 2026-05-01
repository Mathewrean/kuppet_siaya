from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import BBFClaim, BBFBeneficiary
from .serializers import (
    BBFClaimSerializer, BBFClaimCreateSerializer,
    BBFBeneficiarySerializer, BBFBeneficiaryCreateSerializer
)
from accounts.models import Notification


def create_notification(user, title, message, bbf_claim=None):
    """Helper to create notifications"""
    Notification.objects.create(
        user=user,
        title=title,
        message=message,
        bbf_claim=bbf_claim
    )


class BBFClaimViewSet(viewsets.ModelViewSet):
    """API endpoints for BBF claims"""
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return BBFClaimCreateSerializer
        return BBFClaimSerializer
    
    def get_queryset(self):
        # Members can only see their own claims
        return BBFClaim.objects.filter(member=self.request.user).order_by('-submitted_at')
    
    def create(self, request, *args, **kwargs):
        # First create the claim
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        claim = serializer.save()
        
        # Add beneficiaries from request data
        beneficiaries_data = request.data.get('beneficiaries', [])
        created_beneficiaries = []
        
        for beneficiary_data in beneficiaries_data:
            ben_serializer = BBFBeneficiaryCreateSerializer(
                data=beneficiary_data,
                context={'claim': claim}
            )
            ben_serializer.is_valid(raise_exception=True)
            ben = ben_serializer.save()
            created_beneficiaries.append(ben)
        
        if not created_beneficiaries:
            claim.delete()
            return Response(
                {'error': 'At least one beneficiary with document is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update claim status to awaiting_subcounty
        claim.status = 'awaiting_subcounty'
        claim.save()
        
        # Create notification
        create_notification(
            request.user,
            'BBF Claim Submitted',
            f'Your BBF claim {claim.claim_reference} has been submitted.',
            claim
        )
        
        return Response(
            BBFClaimSerializer(claim).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def add_beneficiary(self, request, pk=None):
        """Add a beneficiary to an existing claim"""
        claim = self.get_object()
        
        # Can only add beneficiaries to pending claims
        if claim.status != 'pending':
            return Response(
                {'error': 'Cannot add beneficiaries to a submitted claim'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = BBFBeneficiaryCreateSerializer(
            data=request.data,
            context={'claim': claim}
        )
        serializer.is_valid(raise_exception=True)
        beneficiary = serializer.save()
        
        return Response(
            BBFBeneficiarySerializer(beneficiary).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'])
    def my_claims(self, request):
        """Get current user's claims"""
        claims = self.get_queryset()
        serializer = BBFClaimSerializer(claims, many=True)
        return Response(serializer.data)


class BBFBeneficiaryViewSet(viewsets.ModelViewSet):
    """API endpoints for BBF beneficiaries"""
    permission_classes = [IsAuthenticated]
    serializer_class = BBFBeneficiarySerializer
    
    def get_queryset(self):
        # Only show beneficiaries from user's own claims
        return BBFBeneficiary.objects.filter(
            claim__member=self.request.user
        )
    
    def destroy(self, request, *args, **kwargs):
        beneficiary = self.get_object()
        # Can only delete from pending claims
        if beneficiary.claim.status != 'pending':
            return Response(
                {'error': 'Cannot remove beneficiaries from a submitted claim'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def upload_document(self, request, pk=None):
        """Upload or replace a beneficiary document (member action)"""
        beneficiary = self.get_object()

        # Only the claim owner may upload/replace documents
        if beneficiary.claim.member != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        uploaded_file = request.FILES.get('document')
        if not uploaded_file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate file size (max 5MB) and type
        max_size = 5 * 1024 * 1024
        if uploaded_file.size > max_size:
            return Response({'error': 'File size exceeds 5MB limit'}, status=status.HTTP_400_BAD_REQUEST)

        allowed_types = ['application/pdf', 'image/jpeg', 'image/png']
        content_type = uploaded_file.content_type
        if content_type not in allowed_types:
            return Response({'error': 'Invalid file type. Allowed: PDF, JPG, PNG'}, status=status.HTTP_400_BAD_REQUEST)

        # Save file and set status to pending
        beneficiary.document = uploaded_file
        beneficiary.document_status = 'pending'
        beneficiary.save()

        return Response(self.get_serializer(beneficiary).data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a beneficiary document (for subcounty/county reps)"""
        beneficiary = self.get_object()
        
        # Check permissions
        user = request.user
        if not (user.is_subcounty_rep or user.is_county_rep or user.is_superuser):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        beneficiary.document_status = 'approved'
        beneficiary.approved_by = user
        beneficiary.approved_at = timezone.now()
        beneficiary.save()
        
        return Response(BBFBeneficiarySerializer(beneficiary).data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a beneficiary document (for subcounty/county reps)"""
        beneficiary = self.get_object()
        
        # Check permissions
        user = request.user
        if not (user.is_subcounty_rep or user.is_county_rep or user.is_superuser):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        beneficiary.document_status = 'rejected'
        beneficiary.approved_by = user
        beneficiary.approved_at = timezone.now()
        beneficiary.save()
        
        return Response(BBFBeneficiarySerializer(beneficiary).data)


# Subcounty Representative endpoints
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def subcounty_claims(request):
    """Get all claims awaiting subcounty confirmation"""
    if not request.user.is_subcounty_rep and not request.user.is_superuser:
        return Response(
            {'error': 'Permission denied'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    claims = BBFClaim.objects.filter(
        status='awaiting_subcounty'
    ).order_by('-submitted_at')
    
    return Response(BBFClaimSerializer(claims, many=True).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def subcounty_confirm_claim(request, pk):
    """Subcounty rep confirms a claim, moves to awaiting county"""
    if not request.user.is_subcounty_rep and not request.user.is_superuser:
        return Response(
            {'error': 'Permission denied'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    claim = get_object_or_404(BBFClaim, pk=pk, status='awaiting_subcounty')
    
    # Check all beneficiaries have been reviewed
    pending_docs = claim.beneficiaries.filter(document_status='pending')
    if pending_docs.exists():
        return Response(
            {'error': 'All beneficiary documents must be approved or rejected before confirming'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check no rejected documents
    rejected_docs = claim.beneficiaries.filter(document_status='rejected')
    if rejected_docs.exists():
        return Response(
            {'error': 'Cannot confirm claim with rejected documents'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    claim.status = 'awaiting_county'
    claim.subcounty_confirmed_at = timezone.now()
    claim.subcounty_confirmed_by = request.user
    claim.save()
    
    # Notify member
    create_notification(
        claim.member,
        'BBF Claim Confirmed by Subcounty',
        f'Your BBF claim {claim.claim_reference} has been confirmed by the Subcounty Representative and is now with the County office.',
        claim
    )
    
    return Response(BBFClaimSerializer(claim).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def subcounty_reject_claim(request, pk):
    """Subcounty rep rejects a claim"""
    if not request.user.is_subcounty_rep and not request.user.is_superuser:
        return Response(
            {'error': 'Permission denied'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    claim = get_object_or_404(BBFClaim, pk=pk, status='awaiting_subcounty')
    
    claim.status = 'rejected'
    claim.save()
    
    # Notify member
    create_notification(
        claim.member,
        'BBF Claim Rejected',
        f'Your BBF claim {claim.claim_reference} was rejected at the Subcounty level.',
        claim
    )
    
    return Response(BBFClaimSerializer(claim).data)


# County Representative endpoints
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def county_claims(request):
    """Get all claims awaiting county confirmation"""
    if not request.user.is_county_rep and not request.user.is_superuser:
        return Response(
            {'error': 'Permission denied'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    claims = BBFClaim.objects.filter(
        status='awaiting_county'
    ).order_by('-subcounty_confirmed_at')
    
    return Response(BBFClaimSerializer(claims, many=True).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def county_approve_claim(request, pk):
    """County rep approves a claim"""
    if not request.user.is_county_rep and not request.user.is_superuser:
        return Response(
            {'error': 'Permission denied'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    claim = get_object_or_404(BBFClaim, pk=pk, status='awaiting_county')
    
    claim.status = 'approved'
    claim.county_confirmed_at = timezone.now()
    claim.county_confirmed_by = request.user
    claim.save()
    
    # Notify member
    create_notification(
        claim.member,
        'BBF Claim Approved',
        f'Your BBF claim {claim.claim_reference} has been fully approved.',
        claim
    )
    
    return Response(BBFClaimSerializer(claim).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def county_reject_claim(request, pk):
    """County rep rejects a claim"""
    if not request.user.is_county_rep and not request.user.is_superuser:
        return Response(
            {'error': 'Permission denied'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    claim = get_object_or_404(BBFClaim, pk=pk, status='awaiting_county')
    
    claim.status = 'rejected'
    claim.save()
    
    # Notify member
    create_notification(
        claim.member,
        'BBF Claim Rejected',
        f'Your BBF claim {claim.claim_reference} was rejected at the County level. Please contact your branch.',
        claim
    )
    
    return Response(BBFClaimSerializer(claim).data)
