#!/usr/bin/env python3
import os, django, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE','kuppetsiaya.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.test import Client
from accounts.models import CustomUser
from bbf.models import BBFClaim, BBFBeneficiary

# Create a test user if needed
user, created = CustomUser.objects.get_or_create(
    tsc_number='TEST12345',
    defaults={
        'email': 'test12345@kuppetsiaya.or.ke',
        'first_name': 'Test',
        'last_name': 'User',
        'sub_county': 'TestSubcounty',
        'school': 'Test School',
        'is_active': True,
        'approval_status': 'APPROVED',
        'is_staff': False,
        'is_superuser': False,
    }
)
user.set_password('testpass123')
user.save()
print('Test user:', user.tsc_number, 'created' if created else 'exists')

# Create a test claim
claim, c_created = BBFClaim.objects.get_or_create(
    member=user,
    defaults={'status': 'pending'}
)
if c_created:
    print('Test claim created:', claim.id, claim.claim_reference)

# Create a beneficiary for claim
ben, b_created = BBFBeneficiary.objects.get_or_create(
    claim=claim,
    beneficiary_type='child',
    full_name='Test Child',
    defaults={'document_status': 'pending'}
)
if b_created:
    print('Test beneficiary created:', ben.id)

# Use test client to simulate logged-in user
client = Client()
client.force_login(user)

print('\nTesting endpoints...')
# Dashboard
resp = client.get('/dashboard/')
print('Dashboard:', resp.status_code)
# Claims list
resp = client.get('/dashboard/bbf-claims/')
print('Claims list:', resp.status_code)
# Claims create page
resp = client.get('/dashboard/bbf-claims/new/')
print('Claims create page:', resp.status_code)
# If claim exists, detail page
if claim.id:
    resp = client.get(f'/dashboard/bbf-claims/{claim.id}/')
    print('Claim detail:', resp.status_code)

# Subcounty review page (redirect if not subcounty rep)
resp = client.get(f'/dashboard/subcounty/claims/{claim.id}/')
print('Subcounty review (expect redirect if not rep):', resp.status_code)

# County review page
resp = client.get(f'/dashboard/county/claims/{claim.id}/')
print('County review (expect redirect if not rep):', resp.status_code)

print('\nDone.')
