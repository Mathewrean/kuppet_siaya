from django.db import models
from django.conf import settings
import uuid
import random
import string

def generate_claim_reference():
    """Generate a unique claim reference like BBF-2024-ABC123"""
    year = datetime.now().year
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"BBF-{year}-{random_part}"

from datetime import datetime

class BBFClaim(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('awaiting_subcounty', 'Awaiting Subcounty'),
        ('awaiting_county', 'Awaiting County'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bbf_claims'
    )
    claim_reference = models.CharField(
        max_length=50,
        unique=True,
        default=generate_claim_reference
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Tracking fields
    subcounty_confirmed_at = models.DateTimeField(null=True, blank=True)
    subcounty_confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subcounty_confirmed_claims'
    )
    county_confirmed_at = models.DateTimeField(null=True, blank=True)
    county_confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='county_confirmed_claims'
    )
    
    def __str__(self):
        return f"{self.claim_reference} - {self.member.get_full_name()}"
    
    @property
    def beneficiaries_count(self):
        return self.beneficiaries.count()


class BBFBeneficiary(models.Model):
    BENEFICIARY_TYPE_CHOICES = [
        ('child', 'Child'),
        ('spouse', 'Spouse'),
        ('parent_mother', 'Mother'),
        ('parent_father', 'Father'),
    ]
    
    DOCUMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    claim = models.ForeignKey(
        BBFClaim,
        on_delete=models.CASCADE,
        related_name='beneficiaries'
    )
    beneficiary_type = models.CharField(
        max_length=20,
        choices=BENEFICIARY_TYPE_CHOICES
    )
    full_name = models.CharField(max_length=200)
    document = models.FileField(
        upload_to='bbf_documents/',
        blank=True,
        null=True
    )
    document_status = models.CharField(
        max_length=20,
        choices=DOCUMENT_STATUS_CHOICES,
        default='pending'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_beneficiaries'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.full_name} ({self.beneficiary_type}) - {self.claim.claim_reference}"
    
    @property
    def required_document_name(self):
        """Return the required document name for this beneficiary type"""
        mapping = {
            'child': 'Birth Certificate',
            'spouse': 'Marriage Affidavit',
            'parent_mother': 'National ID Card',
            'parent_father': 'National ID Card',
        }
        return mapping.get(self.beneficiary_type, 'Document')
