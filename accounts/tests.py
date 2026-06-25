import csv
import re
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile
from xml.sax.saxutils import escape

from django.contrib.auth.hashers import get_hasher, identify_hasher
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.authentication import ACCOUNT_INIT_SESSION_KEY
from accounts.models import CustomUser, School, SubCounty


def build_docx_table(document_path, rows):
    table_rows = []
    for row in rows:
        cells = []
        for value in row:
            cell_text = escape(value)
            cells.append(
                "<w:tc><w:p><w:r><w:t xml:space=\"preserve\">"
                f"{cell_text}"
                "</w:t></w:r></w:p></w:tc>"
            )
        table_rows.append(f"<w:tr>{''.join(cells)}</w:tr>")

    document_xml = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<w:document xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\">"
        "<w:body><w:tbl>"
        f"{''.join(table_rows)}"
        "</w:tbl></w:body></w:document>"
    )

    with ZipFile(document_path, "w") as archive:
        archive.writestr("word/document.xml", document_xml)


class SeedMembersCommandTests(TestCase):
    def test_seed_members_creates_users_and_exports_credentials(self):
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            document_path = temp_path / "Members.docx"
            credentials_path = temp_path / "member_credentials.csv"

            build_docx_table(
                document_path,
                [
                    ["Reg-Number", "Officer's Name", "Work-SubCounty", "Station-Name", "Contact"],
                    ["785893", "Mr Andiwo, Bernard Omondi", "Alego Usonga", "Achage Pri Sch", ""],
                    ["456945", "Mrs Atieno, Judith", "Alego Usonga", "Agor Lieye Primary School", "0723411098"],
                    ["", "", "", "", ""],
                ],
            )

            stdout = StringIO()
            call_command(
                "seed_members",
                file=str(document_path),
                credentials_file=str(credentials_path),
                stdout=stdout,
            )

            bernard = CustomUser.objects.get(tsc_number="785893")
            judith = CustomUser.objects.get(tsc_number="456945")

            self.assertEqual(bernard.first_name, "Bernard Omondi")
            self.assertEqual(bernard.last_name, "Andiwo")
            self.assertEqual(bernard.phone_number, "")
            self.assertIsNone(bernard.email)
            self.assertEqual(bernard.sub_county, "Alego Usonga")
            self.assertEqual(bernard.school, "Achage Pri Sch")
            self.assertEqual(bernard.approval_status, "APPROVED")
            self.assertTrue(bernard.is_active)
            self.assertEqual(
                identify_hasher(bernard.password).safe_summary(bernard.password)["iterations"],
                120000,
            )
            self.assertTrue(bernard.check_password("Bernard@5893"))
            bernard.refresh_from_db()
            self.assertEqual(
                identify_hasher(bernard.password).safe_summary(bernard.password)["iterations"],
                get_hasher("default").iterations,
            )

            self.assertEqual(judith.first_name, "Judith")
            self.assertEqual(judith.last_name, "Atieno")
            self.assertEqual(judith.phone_number, "0723411098")
            self.assertTrue(judith.check_password("Judith@6945"))

            self.assertEqual(SubCounty.objects.count(), 1)
            self.assertEqual(School.objects.count(), 2)

            with credentials_path.open(newline="", encoding="utf-8") as credentials_file:
                rows = list(csv.DictReader(credentials_file))

            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["reg_number"], "785893")
            self.assertEqual(rows[0]["temporary_password"], "Bernard@5893")
            self.assertEqual(rows[0]["status"], "created")
            self.assertEqual(rows[1]["temporary_password"], "Judith@6945")

    def test_seed_members_updates_existing_members_only_when_requested(self):
        existing_user = CustomUser.objects.create_user(
            tsc_number="785893",
            email="member@example.com",
            password="Original@123",
            first_name="Old",
            last_name="Name",
            phone_number="0700000000",
            sub_county="Old Subcounty",
            school="Old School",
            approval_status="PENDING",
            is_active=False,
        )

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            document_path = temp_path / "Members.docx"
            credentials_path = temp_path / "member_credentials.csv"

            build_docx_table(
                document_path,
                [
                    ["Reg-Number", "Officer's Name", "Work-SubCounty", "Station-Name", "Contact"],
                    ["785893", "Mr Andiwo, Bernard Omondi", "Alego Usonga", "Achage Pri Sch", ""],
                ],
            )

            call_command(
                "seed_members",
                file=str(document_path),
                credentials_file=str(credentials_path),
            )
            existing_user.refresh_from_db()

            self.assertEqual(existing_user.first_name, "Old")
            self.assertFalse(existing_user.check_password("Bernard@5893"))

            call_command(
                "seed_members",
                file=str(document_path),
                credentials_file=str(credentials_path),
                update_existing=True,
            )
            existing_user.refresh_from_db()

            self.assertEqual(existing_user.first_name, "Bernard Omondi")
            self.assertEqual(existing_user.last_name, "Andiwo")
            self.assertEqual(existing_user.phone_number, "0700000000")
            self.assertEqual(existing_user.sub_county, "Alego Usonga")
            self.assertEqual(existing_user.school, "Achage Pri Sch")
            self.assertEqual(existing_user.email, "member@example.com")
            self.assertEqual(existing_user.approval_status, "APPROVED")
            self.assertTrue(existing_user.is_active)
            self.assertTrue(existing_user.check_password("Bernard@5893"))


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="noreply@example.com",
)
class PasswordLoginTests(TestCase):
    def extract_otp(self):
        match = re.search(r"\b(\d{6})\b", mail.outbox[-1].body)
        self.assertIsNotNone(match)
        return match.group(1)

    def test_first_time_login_redirects_to_account_initialization(self):
        user = CustomUser.objects.create_user(
            tsc_number="123456",
            email=None,
            password="Akinyi@3456",
            first_name="Akinyi",
            approval_status="APPROVED",
            is_active=True,
        )

        response = self.client.post(
            reverse("login"),
            {"tsc_number": "123456", "password": "Akinyi@3456"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], reverse("initialize_account"))
        self.assertEqual(self.client.session[ACCOUNT_INIT_SESSION_KEY], user.pk)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_placeholder_email_is_treated_as_uninitialized(self):
        user = CustomUser.objects.create_user(
            tsc_number="123456",
            email="123456@kuppetsiaya.or.ke",
            password="Akinyi@3456",
            first_name="Akinyi",
            approval_status="APPROVED",
            is_active=True,
        )

        response = self.client.post(
            reverse("login"),
            {"tsc_number": "123456", "password": "Akinyi@3456"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], reverse("initialize_account"))
        self.assertEqual(self.client.session[ACCOUNT_INIT_SESSION_KEY], user.pk)

    def test_uninitialized_account_uses_stored_password_even_if_names_changed(self):
        user = CustomUser.objects.create_user(
            tsc_number="654321",
            email=None,
            password="Judith@4321",
            first_name="",
            last_name="",
            approval_status="APPROVED",
            is_active=True,
        )

        response = self.client.post(
            reverse("login"),
            {"tsc_number": "654321", "password": "Judith@4321"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], reverse("initialize_account"))
        self.assertEqual(self.client.session[ACCOUNT_INIT_SESSION_KEY], user.pk)

    def test_email_verification_completes_account_initialization(self):
        user = CustomUser.objects.create_user(
            tsc_number="123456",
            email=None,
            password="Akinyi@3456",
            first_name="Akinyi",
            last_name="Omondi",
            approval_status="APPROVED",
            is_active=True,
        )

        self.client.post(
            reverse("login"),
            {"tsc_number": "123456", "password": "Akinyi@3456"},
        )
        response = self.client.post(
            reverse("initialize_account"),
            {
                "email": "akinyi@example.com",
                "confirm_email": "akinyi@example.com",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], reverse("otp_verify"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["akinyi@example.com"])

        user.refresh_from_db()
        self.assertIsNone(user.email)

        otp = self.extract_otp()
        response = self.client.post(reverse("otp_verify"), {"otp": otp})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], reverse("dashboard"))
        self.assertEqual(self.client.session["_auth_user_id"], str(user.pk))
        user.refresh_from_db()
        self.assertEqual(user.email, "akinyi@example.com")

    def test_members_with_verified_email_must_complete_email_otp_login(self):
        user = CustomUser.objects.create_user(
            tsc_number="123456",
            email="member@example.com",
            password="Akinyi@3456",
            first_name="Akinyi",
            approval_status="APPROVED",
            is_active=True,
        )

        response = self.client.post(
            reverse("login"),
            {"tsc_number": "123456", "password": "Akinyi@3456"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], reverse("otp_verify"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["member@example.com"])
        self.assertNotIn("_auth_user_id", self.client.session)

        otp = self.extract_otp()
        response = self.client.post(reverse("otp_verify"), {"otp": otp})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], reverse("dashboard"))
        self.assertEqual(self.client.session["_auth_user_id"], str(user.pk))

    def test_initialized_account_shows_clear_message_when_default_password_is_used(self):
        user = CustomUser.objects.create_user(
            tsc_number="123456",
            email="member@example.com",
            password="Different@123",
            first_name="Akinyi",
            approval_status="APPROVED",
            is_active=True,
        )

        response = self.client.post(
            reverse("login"),
            {"tsc_number": user.tsc_number, "password": "Akinyi@3456"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This account has already been initialized.")


class AdminCompatibilityTests(TestCase):
    def test_custom_user_changelist_renders_for_admin(self):
        admin_user = CustomUser.objects.create_superuser(
            tsc_number="999999",
            email="admin@example.com",
            password="Admin@123",
            first_name="Admin",
        )

        self.client.force_login(admin_user)
        response = self.client.get(reverse("admin:accounts_customuser_changelist"))

        self.assertEqual(response.status_code, 200)

    def test_verified_member_cannot_access_admin_site(self):
        member = CustomUser.objects.create_user(
            tsc_number="111111",
            email="member@example.com",
            password="Member@123",
            first_name="Member",
            approval_status="APPROVED",
            is_active=True,
        )

        self.client.force_login(member)
        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("admin:login"), response.headers["Location"])

    def test_staff_non_superuser_cannot_log_into_admin(self):
        staff_user = CustomUser.objects.create_user(
            tsc_number="222222",
            email="staff@example.com",
            password="Staff@123",
            first_name="Staff",
            approval_status="APPROVED",
            is_active=True,
            is_staff=True,
        )

        response = self.client.post(
            reverse("admin:login"),
            {"username": staff_user.tsc_number, "password": "Staff@123"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "superuser account")
        self.assertNotIn("_auth_user_id", self.client.session)


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="noreply@example.com",
)
class AdminPasswordResetTests(TestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_superuser(
            tsc_number="999999",
            email="admin@example.com",
            password="Admin@123",
            first_name="Admin",
        )
        self.member = CustomUser.objects.create_user(
            tsc_number="123456",
            email="member@example.com",
            password="OldPass@123",
            first_name="Member",
            approval_status="APPROVED",
            is_active=True,
        )

    def test_admin_can_reset_password_by_tsc(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("admin_reset_password"),
            {"identifier": "123456", "new_password": "NewPass@123", "password_confirm": "NewPass@123"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Password for Member has been reset.")
        self.member.refresh_from_db()
        self.assertTrue(self.member.check_password("NewPass@123"))

    def test_admin_can_reset_password_by_email(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("admin_reset_password"),
            {"identifier": "member@example.com", "new_password": "NewPass@123", "password_confirm": "NewPass@123"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.member.refresh_from_db()
        self.assertTrue(self.member.check_password("NewPass@123"))

    def test_staff_can_reset_password(self):
        staff = CustomUser.objects.create_user(
            tsc_number="222222",
            email="staff@example.com",
            password="Staff@123",
            is_staff=True,
            approval_status="APPROVED",
            is_active=True,
        )
        self.client.force_login(staff)
        response = self.client.post(
            reverse("admin_reset_password"),
            {"identifier": "123456", "new_password": "NewPass@123", "password_confirm": "NewPass@123"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.member.refresh_from_db()
        self.assertTrue(self.member.check_password("NewPass@123"))

    def test_non_staff_cannot_reset_password(self):
        member = CustomUser.objects.create_user(
            tsc_number="777777",
            email="other@example.com",
            password="Member@123",
            approval_status="APPROVED",
            is_active=True,
        )
        self.client.force_login(member)
        response = self.client.post(reverse("admin_reset_password"))
        self.assertEqual(response.status_code, 302)

    def test_unauthenticated_cannot_reset_password(self):
        response = self.client.post(reverse("admin_reset_password"))
        self.assertEqual(response.status_code, 302)

    def test_password_mismatch_shows_error(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("admin_reset_password"),
            {"identifier": "123456", "new_password": "NewPass@123", "password_confirm": "Wrong@123"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Passwords do not match.")

    def test_user_not_found_shows_error(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("admin_reset_password"),
            {"identifier": "000000", "new_password": "NewPass@123", "password_confirm": "NewPass@123"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "User not found.")

    def test_admin_reset_returns_json_for_api_client(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("admin_reset_password"),
            {"identifier": "123456", "new_password": "NewPass@123", "password_confirm": "NewPass@123"},
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("123456", data["message"])


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="noreply@example.com",
)
class UserPasswordResetTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            tsc_number="123456",
            email="member@example.com",
            password="OldPass@123",
            first_name="Member",
            approval_status="APPROVED",
            is_active=True,
        )

    def extract_reset_link(self):
        match = re.search(r"http://[^\s]+/accounts/password-reset-confirm/[^\s]+", mail.outbox[-1].body)
        self.assertIsNotNone(match)
        url = match.group(0).rstrip("/")
        return url

    def test_request_reset_sends_email_for_valid_email(self):
        response = self.client.post(
            reverse("password_reset_request"),
            {"identifier": "member@example.com"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], reverse("password_reset_request"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Reset your KUPPET Siaya password", mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].to, ["member@example.com"])

    def test_request_reset_sends_email_for_valid_tsc(self):
        response = self.client.post(
            reverse("password_reset_request"),
            {"identifier": "123456"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], reverse("password_reset_request"))
        self.assertEqual(len(mail.outbox), 1)

    def test_request_reset_does_not_leak_user_existence(self):
        response = self.client.post(
            reverse("password_reset_request"),
            {"identifier": "000000"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)
        self.assertContains(response, "reset instructions have been sent")

    def test_confirm_reset_updates_password(self):
        self.client.post(
            reverse("password_reset_request"),
            {"identifier": "member@example.com"},
        )
        reset_url = self.extract_reset_link()
        uidb64 = reset_url.split("/password-reset-confirm/")[1].split("/")[0]
        token = reset_url.split("/")[-1]

        response = self.client.post(
            reverse("password_reset_confirm", args=[uidb64, token]),
            {"new_password": "NewPass@123", "password_confirm": "NewPass@123"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], reverse("login"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewPass@123"))
        self.assertFalse(self.user.check_password("OldPass@123"))

    def test_confirm_reset_rejects_invalid_token(self):
        response = self.client.get(
            reverse("password_reset_confirm", args=["baduid", "badtoken"]),
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], reverse("password_reset_request"))

    def test_confirm_reset_rejects_password_mismatch(self):
        self.client.post(
            reverse("password_reset_request"),
            {"identifier": "member@example.com"},
        )
        reset_url = self.extract_reset_link()
        uidb64 = reset_url.split("/password-reset-confirm/")[1].split("/")[0]
        token = reset_url.split("/")[-1]

        response = self.client.post(
            reverse("password_reset_confirm", args=[uidb64, token]),
            {"new_password": "NewPass@123", "password_confirm": "Wrong@123"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Passwords do not match")
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("OldPass@123"))

    def test_complete_page_renders(self):
        response = self.client.get(reverse("password_reset_complete"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Password Reset Complete")
