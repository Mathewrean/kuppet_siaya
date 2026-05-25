from tempfile import TemporaryDirectory

from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from bbf.models import BBFClaim

class BBFClaimFormTest(TestCase):
    def test_claim_creation(self):
        with TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                User = get_user_model()
                user = User.objects.create(
                    tsc_number='TESTFORM123',
                    email='testform@kuppetsiaya.or.ke',
                    first_name='Test',
                    last_name='Form',
                    sub_county='Siaya',
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
                    'member_doc_payslip': SimpleUploadedFile('payslip.pdf', b'fake payslip', content_type='application/pdf'),
                    'member_doc_national_id': SimpleUploadedFile('national_id.pdf', b'fake id', content_type='application/pdf'),
                    'member_doc_burial_permit': SimpleUploadedFile('burial_permit.pdf', b'fake permit', content_type='application/pdf'),
                    'member_doc_deceased_id': SimpleUploadedFile('deceased_id.pdf', b'fake deceased id', content_type='application/pdf'),
                    'member_doc_relationship': SimpleUploadedFile('relationship.pdf', b'fake relationship', content_type='application/pdf'),
                    'member_doc_introduction': SimpleUploadedFile('introduction.pdf', b'fake introduction', content_type='application/pdf'),
                })

                self.assertEqual(response.status_code, 200)
                claims = BBFClaim.objects.filter(member=user)
                self.assertEqual(claims.count(), 1)
                claim = claims.first()
                self.assertEqual(claim.status, 'awaiting_subcounty')
                self.assertEqual(claim.beneficiaries.count(), 1)
