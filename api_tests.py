import json
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from accounts.models import CustomUser
from bbf.models import BBFClaim, BBFBeneficiary, BBFClaimDocument
from gallery.models import GalleryAlbum, GalleryCategory


class PublicAPITests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_gallery_homepage_slider_returns_200(self):
        resp = self.client.get('/api/gallery/homepage-slider/')
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(json.loads(resp.content), list)

    def test_gallery_public_categories_returns_200(self):
        resp = self.client.get('/api/gallery/categories/')
        self.assertEqual(resp.status_code, 200)

    def test_gallery_public_albums_returns_200(self):
        resp = self.client.get('/api/gallery/albums/')
        self.assertEqual(resp.status_code, 200)

    def test_gallery_public_album_detail_returns_404_when_missing(self):
        resp = self.client.get('/api/gallery/albums/nonexistent-slug/')
        self.assertEqual(resp.status_code, 404)


class MemberBBFAPITests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            tsc_number='MEMBER001',
            email='member@test.com',
            password='Member@123',
            first_name='Member',
            last_name='User',
            sub_county='TestSub',
            approval_status='APPROVED',
            is_active=True,
        )
        self.claim = BBFClaim.objects.create(member=self.user, status='pending')
        self.client = Client()
        self.client.force_login(self.user)

    def test_bbf_claims_list_returns_own_claims(self):
        resp = self.client.get('/api/bbf/claims/')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)

    def test_bbf_claim_create_requires_member_auth(self):
        resp = self.client.post('/api/bbf/claims/', data={})
        self.assertEqual(resp.status_code, 400)

    def test_bbf_claim_detail_returns_200(self):
        resp = self.client.get(f'/api/bbf/claims/{self.claim.pk}/')
        self.assertEqual(resp.status_code, 200)

    def test_bbf_claim_add_beneficiary_to_pending_claim(self):
        pdf = SimpleUploadedFile('doc.pdf', b'%PDF-1.4', content_type='application/pdf')
        resp = self.client.post(
            f'/api/bbf/claims/{self.claim.pk}/add_beneficiary/',
            {
                'beneficiary_type': 'child',
                'full_name': 'Child Two',
                'document': pdf,
            }
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(self.claim.beneficiaries.count(), 1)

    def test_bbf_claim_add_beneficiary_to_submitted_claim_returns_400(self):
        self.claim.status = 'awaiting_subcounty'
        self.claim.save()
        resp = self.client.post(
            f'/api/bbf/claims/{self.claim.pk}/add_beneficiary/',
            {
                'beneficiary_type': 'child',
                'full_name': 'Child',
                'document': SimpleUploadedFile('doc.pdf', b'%PDF-1.4', content_type='application/pdf'),
            }
        )
        self.assertEqual(resp.status_code, 400)

    def test_beneficiary_upload_document_success(self):
        ben = BBFBeneficiary.objects.create(claim=self.claim, beneficiary_type='child', full_name='Child')
        pdf = SimpleUploadedFile('doc.pdf', b'%PDF-1.4', content_type='application/pdf')
        resp = self.client.post(f'/api/bbf/beneficiaries/{ben.pk}/upload_document/', {'document': pdf})
        self.assertEqual(resp.status_code, 200)
        ben.refresh_from_db()
        self.assertTrue(ben.document)

    def test_beneficiary_upload_document_rejects_bad_type(self):
        ben = BBFBeneficiary.objects.create(claim=self.claim, beneficiary_type='child', full_name='Child')
        bad = SimpleUploadedFile('bad.txt', b'hello', content_type='text/plain')
        resp = self.client.post(f'/api/bbf/beneficiaries/{ben.pk}/upload_document/', {'document': bad})
        self.assertEqual(resp.status_code, 400)

    def test_beneficiary_upload_document_rejects_oversize(self):
        ben = BBFBeneficiary.objects.create(claim=self.claim, beneficiary_type='child', full_name='Child')
        big = SimpleUploadedFile('big.pdf', b'x' * (5 * 1024 * 1024 + 1), content_type='application/pdf')
        resp = self.client.post(f'/api/bbf/beneficiaries/{ben.pk}/upload_document/', {'document': big})
        self.assertEqual(resp.status_code, 400)

    def test_beneficiary_delete_from_pending_claim(self):
        ben = BBFBeneficiary.objects.create(claim=self.claim, beneficiary_type='child', full_name='Child')
        resp = self.client.delete(f'/api/bbf/beneficiaries/{ben.pk}/delete/')
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(BBFBeneficiary.objects.filter(pk=ben.pk).exists())

    def test_beneficiary_delete_from_submitted_claim_returns_400(self):
        self.claim.status = 'awaiting_subcounty'
        self.claim.save()
        ben = BBFBeneficiary.objects.create(claim=self.claim, beneficiary_type='child', full_name='Child')
        resp = self.client.delete(f'/api/bbf/beneficiaries/{ben.pk}/delete/')
        self.assertEqual(resp.status_code, 400)


class SubcountyRepAPITests(TestCase):
    def setUp(self):
        self.rep = CustomUser.objects.create_user(
            tsc_number='SUB001',
            email='sub@test.com',
            password='Rep@123',
            first_name='Sub',
            last_name='Rep',
            sub_county='TestSub',
            approval_status='APPROVED',
            is_active=True,
            is_subcounty_rep=True,
        )
        self.member = CustomUser.objects.create_user(
            tsc_number='MEM001',
            email='mem@test.com',
            password='Mem@123',
            first_name='Mem',
            last_name='Ber',
            sub_county='TestSub',
            approval_status='APPROVED',
            is_active=True,
        )
        self.claim = BBFClaim.objects.create(member=self.member, status='awaiting_subcounty')
        self.ben = BBFBeneficiary.objects.create(claim=self.claim, beneficiary_type='child', full_name='Child')
        self.client = Client()
        self.client.force_login(self.rep)

    def test_subcounty_claims_list_returns_200(self):
        resp = self.client.get('/api/bbf/subcounty/claims/')
        self.assertEqual(resp.status_code, 200)

    def test_subcounty_confirm_claim_returns_400_if_pending_docs(self):
        resp = self.client.post(f'/api/bbf/subcounty/claims/{self.claim.pk}/confirm/')
        self.assertEqual(resp.status_code, 400)

    def test_subcounty_reject_claim(self):
        resp = self.client.post(f'/api/bbf/subcounty/claims/{self.claim.pk}/reject/')
        self.assertEqual(resp.status_code, 200)
        self.claim.refresh_from_db()
        self.assertEqual(self.claim.status, 'rejected')

    def test_beneficiary_approve(self):
        resp = self.client.post(f'/api/bbf/beneficiaries/{self.ben.pk}/approve/')
        self.assertEqual(resp.status_code, 200)
        self.ben.refresh_from_db()
        self.assertEqual(self.ben.document_status, 'approved')

    def test_beneficiary_reject(self):
        resp = self.client.post(f'/api/bbf/beneficiaries/{self.ben.pk}/reject/')
        self.assertEqual(resp.status_code, 200)
        self.ben.refresh_from_db()
        self.assertEqual(self.ben.document_status, 'rejected')


class CountyRepAPITests(TestCase):
    def setUp(self):
        self.county_rep = CustomUser.objects.create_user(
            tsc_number='COUNTY001',
            email='county@test.com',
            password='County@123',
            first_name='County',
            last_name='Rep',
            sub_county='TestSub',
            approval_status='APPROVED',
            is_active=True,
            is_county_rep=True,
        )
        self.member = CustomUser.objects.create_user(
            tsc_number='MEM002',
            email='mem2@test.com',
            password='Mem@123',
            first_name='Mem',
            last_name='Ber',
            sub_county='TestSub',
            approval_status='APPROVED',
            is_active=True,
        )
        self.claim = BBFClaim.objects.create(member=self.member, status='awaiting_county')
        self.ben = BBFBeneficiary.objects.create(claim=self.claim, beneficiary_type='child', full_name='Child')
        self.client = Client()
        self.client.force_login(self.county_rep)

    def test_county_claims_list_returns_200(self):
        resp = self.client.get('/api/bbf/county/claims/')
        self.assertEqual(resp.status_code, 200)

    def test_county_approve_claim_returns_400_if_pending_docs(self):
        resp = self.client.post(f'/api/bbf/county/claims/{self.claim.pk}/confirm/')
        self.assertEqual(resp.status_code, 400)

    def test_county_reject_claim(self):
        resp = self.client.post(f'/api/bbf/county/claims/{self.claim.pk}/reject/')
        self.assertEqual(resp.status_code, 200)
        self.claim.refresh_from_db()
        self.assertEqual(self.claim.status, 'rejected')


class ClaimDocumentAPITests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            tsc_number='DOC001',
            email='doc@test.com',
            password='Doc@123',
            first_name='Doc',
            last_name='User',
            sub_county='TestSub',
            approval_status='APPROVED',
            is_active=True,
        )
        self.claim = BBFClaim.objects.create(member=self.user, status='pending')
        self.doc = BBFClaimDocument.objects.create(claim=self.claim, document_type='medical_bill')
        self.client = Client()
        self.client.force_login(self.user)

    def test_claim_documents_list(self):
        resp = self.client.get(f'/api/bbf/claims/{self.claim.pk}/claim-documents/')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)

    def test_claim_document_create(self):
        pdf = SimpleUploadedFile('bill.pdf', b'%PDF-1.4', content_type='application/pdf')
        resp = self.client.post(
            f'/api/bbf/claims/{self.claim.pk}/claim-documents/',
            {'document': pdf, 'document_type': 'death_certificate'}
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(self.claim.claim_documents.count(), 2)

    def test_claim_document_approve_as_member_returns_403(self):
        resp = self.client.post(f'/api/bbf/claim-documents/{self.doc.pk}/approve/')
        self.assertEqual(resp.status_code, 403)

    def test_claim_document_reject_as_member_returns_403(self):
        resp = self.client.post(f'/api/bbf/claim-documents/{self.doc.pk}/reject/')
        self.assertEqual(resp.status_code, 403)


class AuthenticationRequiredTests(TestCase):
    def test_unauthenticated_bbf_claims_list_returns_403(self):
        resp = self.client.get('/api/bbf/claims/')
        self.assertEqual(resp.status_code, 403)

    def test_unauthenticated_gallery_slider_returns_200(self):
        resp = self.client.get('/api/gallery/homepage-slider/')
        self.assertEqual(resp.status_code, 200)
