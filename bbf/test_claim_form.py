from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from bbf.models import BBFClaim

class BBFClaimFormTest(TestCase):
    def test_claim_creation(self):
        User = get_user_model()
        user = User.objects.create(
            tsc_number='TESTFORM123',
            email='testform@kuppetsiaya.or.ke',
            first_name='Test',
            last_name='Form',
            sub_county='TestSub',
            school='Test School',
            is_active=True,
            approval_status='APPROVED',
        )
        user.set_password('password')
        user.save()
        
        self.client.force_login(user)
        
        response = self.client.post('/dashboard/bbf-claims/new/', {
            'beneficiaries-0-type': 'child',
            'beneficiaries-0-name': 'Test Child',
            'beneficiaries-0-document': SimpleUploadedFile('doc.pdf', b'fake pdf content', content_type='application/pdf'),
        })
        
        print('Response status:', response.status_code)
        print('Response content:', response.content)
        
        # Check if claim created
        claims = BBFClaim.objects.filter(member=user)
        self.assertEqual(claims.count(), 1)
        claim = claims.first()
        self.assertEqual(claim.status, 'awaiting_subcounty')
        self.assertEqual(claim.beneficiaries.count(), 1)
        
        # Clean up
        user.delete()
