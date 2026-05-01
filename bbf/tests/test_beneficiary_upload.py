from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.contrib.auth import get_user_model

from bbf.models import BBFClaim, BBFBeneficiary


User = get_user_model()


class BeneficiaryUploadIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            tsc_number='TSC12345',
            email='test@kuppet.test',
            password='pass1234',
            first_name='Test',
            last_name='User'
        )
        self.claim = BBFClaim.objects.create(member=self.user)
        self.beneficiary = BBFBeneficiary.objects.create(
            claim=self.claim,
            beneficiary_type='child',
            full_name='Test Child'
        )

    def test_successful_pdf_upload_sets_document_and_pending_status(self):
        self.client.force_login(self.user)

        upload_url = reverse('bbfbeneficiary-upload-document', kwargs={'pk': self.beneficiary.pk})
        # Some projects map the view name differently; fallback to constructed path
        if upload_url == '/':
            upload_url = f'/api/bbf/beneficiaries/{self.beneficiary.pk}/upload_document/'

        pdf_file = SimpleUploadedFile('birth.pdf', b'%PDF-1.4 test', content_type='application/pdf')

        resp = self.client.post(upload_url, {'document': pdf_file})
        self.assertIn(resp.status_code, (200, 201), msg=f'Unexpected status: {resp.status_code} - {resp.content}')

        self.beneficiary.refresh_from_db()
        self.assertTrue(self.beneficiary.document)
        self.assertEqual(self.beneficiary.document_status, 'pending')

    def test_reject_invalid_content_type(self):
        self.client.force_login(self.user)
        upload_url = f'/api/bbf/beneficiaries/{self.beneficiary.pk}/upload_document/'

        bad_file = SimpleUploadedFile('script.sh', b'echo hi', content_type='text/plain')
        resp = self.client.post(upload_url, {'document': bad_file})
        self.assertEqual(resp.status_code, 400)

    def test_reject_oversize_file(self):
        self.client.force_login(self.user)
        upload_url = f'/api/bbf/beneficiaries/{self.beneficiary.pk}/upload_document/'

        # Create a file slightly larger than 5MB
        large_content = b'a' * (5 * 1024 * 1024 + 1)
        large_file = SimpleUploadedFile('large.pdf', large_content, content_type='application/pdf')
        resp = self.client.post(upload_url, {'document': large_file})
        self.assertEqual(resp.status_code, 400)
