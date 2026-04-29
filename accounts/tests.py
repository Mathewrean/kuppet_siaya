import csv
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile
from xml.sax.saxutils import escape

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

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
            self.assertTrue(bernard.check_password("Bernard@5893"))

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


class PasswordLoginTests(TestCase):
    def test_members_can_log_in_with_tsc_number_and_password(self):
        user = CustomUser.objects.create_user(
            tsc_number="123456",
            email=None,
            password="Secret@123",
            first_name="Akinyi",
            approval_status="APPROVED",
            is_active=True,
        )

        response = self.client.post(
            reverse("login"),
            {"tsc_number": "123456", "password": "Secret@123"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], reverse("dashboard"))
        self.assertEqual(self.client.session["_auth_user_id"], str(user.pk))
