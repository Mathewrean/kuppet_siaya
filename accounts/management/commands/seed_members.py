import csv
import re
from dataclasses import dataclass
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from accounts.models import CustomUser, School, SubCounty


WORD_NAMESPACE = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
EXPECTED_HEADERS = [
    "Reg-Number",
    "Officer's Name",
    "Work-SubCounty",
    "Station-Name",
    "Contact",
]
TITLE_PATTERN = re.compile(r"^(mr|mrs|miss|ms|dr|prof|rev|hon)\.?\s+", re.IGNORECASE)


@dataclass(frozen=True)
class MemberRow:
    reg_number: str
    officer_name: str
    work_subcounty: str
    station_name: str
    contact: str = ""


@dataclass(frozen=True)
class ParsedOfficerName:
    first_name: str
    last_name: str
    password_seed: str


def normalize_text(value):
    return " ".join((value or "").replace("\xa0", " ").split())


def parse_docx_rows(document_path):
    with ZipFile(document_path) as archive:
        try:
            document_xml = archive.read("word/document.xml")
        except KeyError as exc:
            raise CommandError(f"{document_path} does not contain a readable Word document body.") from exc

    root = ET.fromstring(document_xml)
    rows = []

    for table_row in root.findall(".//w:tbl//w:tr", WORD_NAMESPACE):
        cells = []
        for table_cell in table_row.findall("./w:tc", WORD_NAMESPACE):
            texts = [
                text_node.text
                for text_node in table_cell.findall(".//w:t", WORD_NAMESPACE)
                if text_node.text
            ]
            cells.append(normalize_text("".join(texts)))

        if any(cells):
            rows.append(cells)

    if not rows:
        raise CommandError(f"No table rows were found in {document_path}.")

    header = rows[0]
    if header != EXPECTED_HEADERS:
        raise CommandError(
            f"Unexpected document headers in {document_path}. "
            f"Expected {EXPECTED_HEADERS} but found {header}."
        )

    members = []
    for row_number, cells in enumerate(rows[1:], start=2):
        if not any(cells):
            continue

        if len(cells) != len(EXPECTED_HEADERS):
            raise CommandError(
                f"Row {row_number} in {document_path} has {len(cells)} columns; "
                f"expected {len(EXPECTED_HEADERS)}."
            )

        members.append(
            MemberRow(
                reg_number=normalize_text(cells[0]),
                officer_name=normalize_text(cells[1]),
                work_subcounty=normalize_text(cells[2]),
                station_name=normalize_text(cells[3]),
                contact=normalize_text(cells[4]),
            )
        )

    return members


def strip_title(name_part):
    return TITLE_PATTERN.sub("", normalize_text(name_part)).strip(", ")


def parse_officer_name(officer_name):
    cleaned_name = normalize_text(officer_name)

    if "," in cleaned_name:
        surname_part, given_names_part = cleaned_name.split(",", 1)
        last_name = strip_title(surname_part)
        first_name = strip_title(given_names_part) or last_name or "Member"
    else:
        plain_name = strip_title(cleaned_name)
        name_tokens = plain_name.split()
        if not name_tokens:
            return ParsedOfficerName(first_name="Member", last_name="", password_seed="Member")
        if len(name_tokens) == 1:
            return ParsedOfficerName(
                first_name=name_tokens[0],
                last_name="",
                password_seed=build_password_seed(name_tokens[0]),
            )

        first_name = " ".join(name_tokens[:-1])
        last_name = name_tokens[-1]

    return ParsedOfficerName(
        first_name=first_name,
        last_name=last_name,
        password_seed=build_password_seed(first_name or last_name),
    )


def build_password_seed(name_value):
    for token in normalize_text(name_value).split():
        cleaned_token = re.sub(r"[^0-9A-Za-z]", "", token)
        if cleaned_token:
            candidate = cleaned_token.capitalize()
            if len(candidate) >= 3:
                return candidate
            return f"{candidate}Member"
    return "Member"


def build_temporary_password(parsed_name, reg_number):
    suffix = reg_number[-4:] if len(reg_number) >= 4 else reg_number.zfill(4)
    return f"{parsed_name.password_seed}@{suffix}"


def write_credentials_file(output_path, credentials_rows):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "reg_number",
                "officer_name",
                "work_subcounty",
                "station_name",
                "contact",
                "temporary_password",
                "status",
            ],
        )
        writer.writeheader()
        writer.writerows(credentials_rows)


class Command(BaseCommand):
    help = "Seed member accounts from Members.docx and export the generated temporary passwords."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            default="Members.docx",
            help="Path to the source .docx file containing the member list.",
        )
        parser.add_argument(
            "--credentials-file",
            default="member_seed_credentials.csv",
            help="CSV file to write the generated login credentials to.",
        )
        parser.add_argument(
            "--update-existing",
            action="store_true",
            help="Update matching members by TSC number and reset their temporary passwords.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        document_path = Path(options["file"]).expanduser()
        if not document_path.is_absolute():
            document_path = Path.cwd() / document_path

        credentials_path = Path(options["credentials_file"]).expanduser()
        if not credentials_path.is_absolute():
            credentials_path = Path.cwd() / credentials_path

        if document_path.suffix.lower() != ".docx":
            raise CommandError("The member seed command currently supports only .docx files.")

        if not document_path.exists():
            raise CommandError(f"Member document not found: {document_path}")

        members = parse_docx_rows(document_path)
        credentials_rows = []
        created_count = 0
        updated_count = 0
        skipped_count = 0
        seen_reg_numbers = set()

        for member in members:
            if not member.reg_number:
                continue

            if member.reg_number in seen_reg_numbers:
                self.stdout.write(
                    self.style.WARNING(f"Skipping duplicate Reg-Number {member.reg_number} in source file.")
                )
                continue
            seen_reg_numbers.add(member.reg_number)

            parsed_name = parse_officer_name(member.officer_name)
            temporary_password = build_temporary_password(parsed_name, member.reg_number)

            existing_user = CustomUser.objects.filter(tsc_number=member.reg_number).first()
            if existing_user and not options["update_existing"]:
                skipped_count += 1
                credentials_rows.append(
                    {
                        "reg_number": member.reg_number,
                        "officer_name": member.officer_name,
                        "work_subcounty": member.work_subcounty,
                        "station_name": member.station_name,
                        "contact": member.contact,
                        "temporary_password": "",
                        "status": "skipped_existing",
                    }
                )
                continue

            sub_county, _ = SubCounty.objects.get_or_create(name=member.work_subcounty)
            school, _ = School.objects.get_or_create(name=member.station_name, sub_county=sub_county)

            user = existing_user or CustomUser(tsc_number=member.reg_number)
            user.first_name = parsed_name.first_name
            user.last_name = parsed_name.last_name
            if member.contact or not existing_user:
                user.phone_number = member.contact
            user.sub_county = sub_county.name
            user.school = school.name
            user.approval_status = "APPROVED"
            user.approval_date = timezone.now()
            user.is_active = True
            if not user.email:
                user.email = None
            user.set_password(temporary_password)
            user.save()

            status = "created" if existing_user is None else "updated"
            if status == "created":
                created_count += 1
            else:
                updated_count += 1

            credentials_rows.append(
                {
                    "reg_number": member.reg_number,
                    "officer_name": member.officer_name,
                    "work_subcounty": member.work_subcounty,
                    "station_name": member.station_name,
                    "contact": member.contact,
                    "temporary_password": temporary_password,
                    "status": status,
                }
            )

        write_credentials_file(credentials_path, credentials_rows)

        self.stdout.write(
            self.style.SUCCESS(
                f"Processed {len(members)} members: "
                f"{created_count} created, {updated_count} updated, {skipped_count} skipped. "
                f"Credentials saved to {credentials_path}."
            )
        )
