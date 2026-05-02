import csv
import os
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from itertools import repeat
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET

from django.contrib.auth.hashers import PBKDF2PasswordHasher
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from accounts.authentication import build_password_seed, format_default_password
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
DEFAULT_PASSWORD_ITERATIONS = min(PBKDF2PasswordHasher.iterations, 120000)
DEFAULT_BATCH_SIZE = 500
DEFAULT_PROGRESS_EVERY = 100
DEFAULT_HASH_WORKERS = max(1, min(4, os.cpu_count() or 1))


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


@dataclass(frozen=True)
class PreparedMember:
    member: MemberRow
    parsed_name: ParsedOfficerName
    temporary_password: str
    status: str


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


def build_temporary_password(parsed_name, reg_number):
    return format_default_password(parsed_name.password_seed, reg_number)


def encode_temporary_password(raw_password, iterations):
    hasher = PBKDF2PasswordHasher()
    return hasher.encode(raw_password, hasher.salt(), iterations=iterations)


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
    help = (
        "Seed member accounts from Members.docx and export temporary passwords. "
        "Imported passwords use PBKDF2 with a reduced iteration count for speed, "
        "and Django will upgrade them to the full project setting after a successful login."
    )

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
        parser.add_argument(
            "--password-iterations",
            type=int,
            default=DEFAULT_PASSWORD_ITERATIONS,
            help=(
                "PBKDF2 iterations to use for imported temporary passwords. "
                f"Default: {DEFAULT_PASSWORD_ITERATIONS}."
            ),
        )
        parser.add_argument(
            "--hash-workers",
            type=int,
            default=DEFAULT_HASH_WORKERS,
            help=f"Number of worker threads for password hashing. Default: {DEFAULT_HASH_WORKERS}.",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=DEFAULT_BATCH_SIZE,
            help=f"Bulk create/update batch size. Default: {DEFAULT_BATCH_SIZE}.",
        )

    def emit(self, message):
        self.stdout.write(message)
        self.stdout.flush()

    def hash_passwords(self, prepared_members, iterations, worker_count):
        total = len(prepared_members)
        if total == 0:
            return []

        raw_passwords = [prepared_member.temporary_password for prepared_member in prepared_members]
        hashed_passwords = []
        progress_every = DEFAULT_PROGRESS_EVERY

        self.emit(
            f"Hashing {total} temporary passwords with PBKDF2 "
            f"({iterations} iterations, {worker_count} worker{'s' if worker_count != 1 else ''})..."
        )

        if worker_count <= 1:
            iterator = map(encode_temporary_password, raw_passwords, repeat(iterations))
            for index, password_hash in enumerate(iterator, start=1):
                hashed_passwords.append(password_hash)
                if index % progress_every == 0 or index == total:
                    self.emit(f"Hashed {index}/{total} passwords...")
            return hashed_passwords

        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            iterator = executor.map(encode_temporary_password, raw_passwords, repeat(iterations))
            for index, password_hash in enumerate(iterator, start=1):
                hashed_passwords.append(password_hash)
                if index % progress_every == 0 or index == total:
                    self.emit(f"Hashed {index}/{total} passwords...")

        return hashed_passwords

    def ensure_subcounties(self, members, batch_size):
        subcounty_names = sorted({member.member.work_subcounty for member in members})
        existing_subcounties = {
            sub_county.name: sub_county
            for sub_county in SubCounty.objects.filter(name__in=subcounty_names)
        }

        missing_subcounties = [
            SubCounty(name=subcounty_name)
            for subcounty_name in subcounty_names
            if subcounty_name not in existing_subcounties
        ]
        if missing_subcounties:
            SubCounty.objects.bulk_create(missing_subcounties, batch_size=batch_size)

        return {
            sub_county.name: sub_county
            for sub_county in SubCounty.objects.filter(name__in=subcounty_names)
        }

    def ensure_schools(self, members, subcounty_map, batch_size):
        school_keys = {(member.member.work_subcounty, member.member.station_name) for member in members}
        school_names = {station_name for _, station_name in school_keys}
        subcounty_names = {subcounty_name for subcounty_name, _ in school_keys}

        existing_schools = {}
        for school in (
            School.objects.select_related("sub_county")
            .filter(sub_county__name__in=subcounty_names, name__in=school_names)
            .order_by("id")
        ):
            existing_schools.setdefault((school.sub_county.name, school.name), school)

        missing_schools = [
            School(name=station_name, sub_county=subcounty_map[subcounty_name])
            for subcounty_name, station_name in school_keys
            if (subcounty_name, station_name) not in existing_schools
        ]
        if missing_schools:
            School.objects.bulk_create(missing_schools, batch_size=batch_size)

        refreshed_school_map = {}
        for school in (
            School.objects.select_related("sub_county")
            .filter(sub_county__name__in=subcounty_names, name__in=school_names)
            .order_by("id")
        ):
            refreshed_school_map.setdefault((school.sub_county.name, school.name), school)

        return refreshed_school_map

    def prepare_members(self, members, existing_users_by_tsc, update_existing):
        prepared_members = []
        credentials_rows = []
        seen_reg_numbers = set()
        skipped_existing_count = 0
        skipped_duplicate_count = 0

        for member in members:
            if not member.reg_number:
                continue

            if member.reg_number in seen_reg_numbers:
                skipped_duplicate_count += 1
                credentials_rows.append(
                    {
                        "reg_number": member.reg_number,
                        "officer_name": member.officer_name,
                        "work_subcounty": member.work_subcounty,
                        "station_name": member.station_name,
                        "contact": member.contact,
                        "temporary_password": "",
                        "status": "skipped_duplicate_source",
                    }
                )
                continue

            seen_reg_numbers.add(member.reg_number)
            existing_user = existing_users_by_tsc.get(member.reg_number)

            if existing_user and not update_existing:
                skipped_existing_count += 1
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

            parsed_name = parse_officer_name(member.officer_name)
            temporary_password = build_temporary_password(parsed_name, member.reg_number)
            status = "updated" if existing_user else "created"
            prepared_members.append(
                PreparedMember(
                    member=member,
                    parsed_name=parsed_name,
                    temporary_password=temporary_password,
                    status=status,
                )
            )

        return prepared_members, credentials_rows, skipped_existing_count, skipped_duplicate_count

    def handle(self, *args, **options):
        document_path = Path(options["file"]).expanduser()
        if not document_path.is_absolute():
            document_path = Path.cwd() / document_path

        credentials_path = Path(options["credentials_file"]).expanduser()
        if not credentials_path.is_absolute():
            credentials_path = Path.cwd() / credentials_path

        password_iterations = options["password_iterations"]
        hash_workers = max(1, options["hash_workers"])
        batch_size = max(1, options["batch_size"])

        if document_path.suffix.lower() != ".docx":
            raise CommandError("The member seed command currently supports only .docx files.")

        if not document_path.exists():
            raise CommandError(f"Member document not found: {document_path}")

        if password_iterations <= 0:
            raise CommandError("--password-iterations must be a positive integer.")

        members = parse_docx_rows(document_path)
        self.emit(f"Loaded {len(members)} member rows from {document_path}.")

        existing_users_by_tsc = CustomUser.objects.in_bulk(
            [member.reg_number for member in members if member.reg_number],
            field_name="tsc_number",
        )
        prepared_members, credentials_rows, skipped_existing_count, skipped_duplicate_count = self.prepare_members(
            members,
            existing_users_by_tsc,
            options["update_existing"],
        )

        self.emit(
            f"Prepared {len(prepared_members)} account(s) to import, "
            f"{skipped_existing_count} existing account(s) skipped, "
            f"{skipped_duplicate_count} duplicate source row(s) skipped."
        )

        if not prepared_members:
            write_credentials_file(credentials_path, credentials_rows)
            self.emit(self.style.SUCCESS(f"No new users to import. Credentials saved to {credentials_path}."))
            return

        hashed_passwords = self.hash_passwords(prepared_members, password_iterations, hash_workers)

        created_users = []
        updated_users = []
        actionable_credentials_rows = []
        created_count = 0
        updated_count = 0
        now = timezone.now()

        with transaction.atomic():
            subcounty_map = self.ensure_subcounties(prepared_members, batch_size)
            school_map = self.ensure_schools(prepared_members, subcounty_map, batch_size)
            self.emit(
                f"Resolved {len(subcounty_map)} sub-counties and {len(school_map)} schools for import."
            )

            for prepared_member, hashed_password in zip(prepared_members, hashed_passwords):
                member = prepared_member.member
                parsed_name = prepared_member.parsed_name
                existing_user = existing_users_by_tsc.get(member.reg_number)
                school = school_map[(member.work_subcounty, member.station_name)]

                if existing_user is None:
                    user = CustomUser(
                        tsc_number=member.reg_number,
                        first_name=parsed_name.first_name,
                        last_name=parsed_name.last_name,
                        email=None,
                        phone_number=member.contact,
                        sub_county=school.sub_county.name,
                        school=school.name,
                        approval_status="APPROVED",
                        approval_date=now,
                        is_active=True,
                        password=hashed_password,
                    )
                    created_users.append(user)
                    created_count += 1
                else:
                    existing_user.first_name = parsed_name.first_name
                    existing_user.last_name = parsed_name.last_name
                    if member.contact:
                        existing_user.phone_number = member.contact
                    existing_user.sub_county = school.sub_county.name
                    existing_user.school = school.name
                    existing_user.approval_status = "APPROVED"
                    existing_user.approval_date = now
                    existing_user.is_active = True
                    existing_user.password = hashed_password
                    updated_users.append(existing_user)
                    updated_count += 1

                actionable_credentials_rows.append(
                    {
                        "reg_number": member.reg_number,
                        "officer_name": member.officer_name,
                        "work_subcounty": member.work_subcounty,
                        "station_name": member.station_name,
                        "contact": member.contact,
                        "temporary_password": prepared_member.temporary_password,
                        "status": prepared_member.status,
                    }
                )

            if created_users:
                self.emit(f"Creating {len(created_users)} user account(s)...")
                CustomUser.objects.bulk_create(created_users, batch_size=batch_size)

            if updated_users:
                self.emit(f"Updating {len(updated_users)} existing user account(s)...")
                CustomUser.objects.bulk_update(
                    updated_users,
                    [
                        "first_name",
                        "last_name",
                        "phone_number",
                        "sub_county",
                        "school",
                        "approval_status",
                        "approval_date",
                        "is_active",
                        "password",
                    ],
                    batch_size=batch_size,
                )

        credentials_rows.extend(actionable_credentials_rows)
        write_credentials_file(credentials_path, credentials_rows)

        self.emit(
            self.style.SUCCESS(
                f"Processed {len(members)} members: "
                f"{created_count} created, {updated_count} updated, "
                f"{skipped_existing_count} skipped existing, "
                f"{skipped_duplicate_count} skipped duplicate source rows. "
                f"Credentials saved to {credentials_path}."
            )
        )
