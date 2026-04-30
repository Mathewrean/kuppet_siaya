#!/usr/bin/env python3
"""
Member Seed Data Ingestion Script
===================================
Migrates member data from CSV into the KUPPET Siaya database.

CSV Format:
- reg_number: TSC registration number (maps to tsc_number)
- officer_name: Full name of member
- work_subcounty: Subcounty (must be validated)
- station_name: School/work station name
- contact: Phone number (optional)
- temporary_password: Initial password
- status: Account status

Author: Senior Backend Engineer
Date: 2026-05-01
"""

import os
import csv
import re
import sys
from collections import defaultdict
from datetime import datetime

# Django setup
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kuppetsiaya.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError

from accounts.models import CustomUser, SubCounty, School

# =============================================================================
# CONFIGURATION
# =============================================================================
CSV_PATH = os.path.join(os.path.dirname(__file__), 'member_seed_credentials.csv')

# Valid subcounties - must match exactly what's in the database
VALID_SUBCOUNTIES = [
    'Alego Usonga',
    'Bondo',
    'Gem',
    'Rarieda',
    'Rangwe',
    'Ugunja',
    'Karachuonyo',
    'Kasipul',
    'Kuria',
    'Mbita',
    'Nyando',
    'Sabatia',
    'Siaya',
    'Ugenya',
    'Ukwala',
]

# Name parsing patterns
NAME_PREFIXES = {'mr', 'mrs', 'miss', 'ms', 'dr', 'prof'}

def normalize_subcounty(raw_value):
    """
    Normalize subcounty names from CSV to match valid list.
    Handles variations like extra spaces, case differences.
    """
    if not raw_value or not isinstance(raw_value, str):
        return None
    
    cleaned = raw_value.strip().title()
    
    # Special mappings for known variations
    mappings = {
        'Alego Usonga': 'Alego Usonga',
        'Ugunja': 'Ugunja',
        'Siaya': 'Siaya',
    }
    
    return mappings.get(cleaned, cleaned)


def parse_name(full_name):
    """
    Parse full name into first_name and last_name.
    Handles formats like "Mr Andiwo, Bernard Omondi" and "John Doe".
    """
    if not full_name or not isinstance(full_name, str):
        return '', ''
    
    name = full_name.strip()
    
    # Remove titles
    name_lower = name.lower()
    for prefix in NAME_PREFIXES:
        if name_lower.startswith(prefix + ' '):
            name = name[len(prefix):].strip()
            break
    
    # Handle "Last, First" format
    if ',' in name:
        parts = [p.strip() for p in name.split(',', 1)]
        if len(parts) == 2:
            last_name = parts[0]
            first_name = parts[1]
        else:
            first_name = parts[0]
            last_name = ''
    else:
        # "First Last" format
        parts = name.split()
        if len(parts) == 0:
            return '', ''
        elif len(parts) == 1:
            first_name = parts[0]
            last_name = ''
        else:
            first_name = parts[0]
            last_name = ' '.join(parts[1:])
    
    # Clean up
    first_name = re.sub(r'[^a-zA-Z\s\-\']', '', first_name).strip()
    last_name = re.sub(r'[^a-zA-Z\s\-\']', '', last_name).strip()
    
    return first_name[:30], last_name[:30]


def clean_phone(phone):
    """
    Clean and validate phone number.
    """
    if not phone or not isinstance(phone, str):
        return ''
    
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Kenyan numbers typically start with 07 or +2547
    if len(digits) == 10 and digits.startswith('07'):
        return digits
    elif len(digits) == 12 and digits.startswith('2547'):
        return '0' + digits[-9:]
    elif len(digits) == 13 and digits.startswith('2547'):
        return '0' + digits[-9:]
    elif len(digits) == 9 and not phone.startswith('0'):
        return '0' + digits
    elif len(digits) >= 10:
        return digits[-10:]
    
    return ''


def generate_username(tsc_number):
    """
    Generate a username from TSC number.
    """
    return str(tsc_number).strip()


def validate_tsc(tsc):
    """
    Validate TSC number format.
    """
    if not tsc:
        return False
    tsc_str = str(tsc).strip()
    return len(tsc_str) >= 5 and tsc_str.isdigit()


def extract_school_name(station_name, subcounty):
    """
    Extract or create a school name from station data.
    """
    if not station_name or not isinstance(station_name, str):
        return subcounty + " School" if subcounty else "Unknown School"
    
    return station_name.strip()[:150]

# =============================================================================
# MAIN INGESTION LOGIC
# =============================================================================

@transaction.atomic
def ingest_members(csv_path):
    """
    Main ingestion function.
    Reads CSV, validates data, creates users and related records using bulk operations.
    """
    User = get_user_model()
    
    # Statistics
    stats = {
        'total_rows': 0,
        'successful': 0,
        'failed': 0,
        'skipped_duplicate': 0,
        'errors': defaultdict(list)
    }
    
    print(f"\n{'='*70}")
    print(f"  MEMBER DATA INGESTION")
    print(f"  Source: {csv_path}")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")
    
    # Preload valid subcounties from database
    print("Loading subcounties from database...")
    existing_subcounties = {sc.name.lower(): sc for sc in SubCounty.objects.all()}
    
    # Create any missing subcounties (bulk)
    to_create = []
    for valid_sc in VALID_SUBCOUNTIES:
        key = valid_sc.lower()
        if key not in existing_subcounties:
            to_create.append(SubCounty(name=valid_sc))
    if to_create:
        SubCounty.objects.bulk_create(to_create)
        existing_subcounties.update({sc.name.lower(): sc for sc in SubCounty.objects.filter(name__in=[s.name for s in to_create])})
        print(f"  Created {len(to_create)} subcounties")
    
    print(f"  Total subcounties loaded: {len(existing_subcounties)}\n")
    
    # Read CSV
    if not os.path.exists(csv_path):
        print(f"ERROR: CSV file not found at {csv_path}")
        return stats
    
    with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        if content.startswith('\ufeff'):
            content = content[1:]
        rows = list(csv.DictReader(content.splitlines()))
    
    stats['total_rows'] = len(rows)
    print(f"Loaded {len(rows)} rows from CSV.\n")
    print(f"{'='*70}")
    print(f"  PROCESSING (BATCH MODE)")
    print(f"{'='*70}\n")
    
    # Existing users set
    existing_tscs = set(User.objects.values_list('tsc_number', flat=True))
    school_cache = {}  # school_key -> School
    
    # Batch processing
    BATCH_SIZE = 100
    users_to_create = []
    schools_to_create = []
    
    for i, row in enumerate(rows, 1):
        tsc_number = row.get('reg_number', '').strip()
        officer_name = row.get('officer_name', '').strip()
        work_subcounty_raw = row.get('work_subcounty', '').strip()
        station_name = row.get('station_name', '').strip()
        contact = row.get('contact', '').strip()
        temp_password = row.get('temporary_password', '').strip()
        
        if i % 500 == 0:
            print(f"  ...processed {i}/{len(rows)} rows ({len(users_to_create)} queued)...")
        
        # Validation
        if not validate_tsc(tsc_number):
            stats['failed'] += 1
            stats['errors']['invalid_tsc'].append(tsc_number)
            continue
        
        if tsc_number in existing_tscs:
            stats['skipped_duplicate'] += 1
            continue
        
        first_name, last_name = parse_name(officer_name)
        if not first_name and not last_name:
            stats['failed'] += 1
            stats['errors']['name_parse'].append(tsc_number)
            continue
        
        subcounty_normalized = normalize_subcounty(work_subcounty_raw)
        if not subcounty_normalized or subcounty_normalized.lower() not in existing_subcounties:
            stats['failed'] += 1
            stats['errors']['invalid_subcounty'].append(f"{tsc_number} ({work_subcounty_raw})")
            continue
        
        subcounty = existing_subcounties[subcounty_normalized.lower()]
        
        # Handle school
        school_name = extract_school_name(station_name, subcounty_normalized)
        school_key = f"{school_name}_{subcounty.id}"
        if school_key not in school_cache:
            school = School(name=school_name, sub_county=subcounty)
            school_cache[school_key] = school
            schools_to_create.append(school)
            school_cache[school_key] = school
        
        # Create user
        phone = clean_phone(contact) if contact else ''
        email = f"{tsc_number.lower()}@kuppetsiaya.or.ke"
        is_active = (len(temp_password) > 0)
        
        user = CustomUser(
            tsc_number=tsc_number,
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone,
            sub_county=subcounty_normalized,
            school=school_name,
            is_active=is_active,
            approval_status='APPROVED' if is_active else 'PENDING',
            is_staff=False,
            is_superuser=False,
        )
        user.set_password(temp_password if temp_password else 'Kuppet@2024')
        users_to_create.append(user)
        existing_tscs.add(tsc_number)
        
        # Flush batches
        if len(schools_to_create) >= BATCH_SIZE:
            School.objects.bulk_create(schools_to_create, ignore_conflicts=True)
            schools_to_create = []
        
        if len(users_to_create) >= BATCH_SIZE:
            User.objects.bulk_create(users_to_create)
            stats['successful'] += len(users_to_create)
            users_to_create = []
    
    # Flush remaining
    if schools_to_create:
        School.objects.bulk_create(schools_to_create, ignore_conflicts=True)
    if users_to_create:
        User.objects.bulk_create(users_to_create)
        stats['successful'] += len(users_to_create)
    
    # Print sample
    print("\n  Sample created users:")
    for u in User.objects.exclude(tsc_number__in=['999999', 'TSC001', '111111', 'TSC002', 'TSC003']).order_by('?')[:5]:
        print(f"    {u.tsc_number} - {u.get_full_name()} - {u.sub_county}")
    
    # Summary
    print(f"\n{'='*70}")
    print(f"  INGESTION SUMMARY")
    print(f"{'='*70}")
    print(f"  Total rows:       {stats['total_rows']}")
    print(f"  Successful:       {stats['successful']}")
    print(f"  Failed:           {stats['failed']}")
    print(f"  Duplicates skip:  {stats['skipped_duplicate']}")
    
    if stats['errors']:
        print(f"\n  Top errors:")
        for err, tscs in sorted(stats['errors'].items(), key=lambda x: len(x[1]), reverse=True)[:5]:
            print(f"    {err}: {len(tscs)} rows")
    
    # Verification
    total_users = User.objects.count()
    print(f"\n{'='*70}")
    print(f"  DATABASE STATE")
    print(f"{'='*70}")
    print(f"  Total users: {total_users}")
    print(f"  Active: {User.objects.filter(is_active=True).count()}")
    print(f"  Approved: {User.objects.filter(approval_status='APPROVED').count()}")
    
    from accounts.models import SubCounty
    for sc in SubCounty.objects.all().order_by('name'):
        count = User.objects.filter(sub_county=sc.name).count()
        if count > 0:
            print(f"    {sc.name}: {count}")
    
    print(f"\n{'='*70}")
    print(f"  COMPLETE")
    print(f"{'='*70}\n")
    return stats
    
    with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
        # Skip BOM if present
        content = f.read()
        if content.startswith('\ufeff'):
            content = content[1:]
        
        rows = list(csv.DictReader(content.splitlines()))
    
    stats['total_rows'] = len(rows)
    print(f"Loaded {len(rows)} rows from CSV.\n")
    print(f"{'='*70}")
    print(f"  PROCESSING")
    print(f"{'='*70}\n")
    
    # Process each row
    for i, row in enumerate(rows, 1):
        tsc_number = row.get('reg_number', '').strip()
        officer_name = row.get('officer_name', '').strip()
        work_subcounty_raw = row.get('work_subcounty', '').strip()
        station_name = row.get('station_name', '').strip()
        contact = row.get('contact', '').strip()
        temp_password = row.get('temporary_password', '').strip()
        status = row.get('status', 'created').strip()
        
        # Progress indicator
        if i % 100 == 0:
            print(f"  Processing row {i}/{len(rows)}...")
        
        # Validation
        errors = []
        
        # Check TSC number
        if not validate_tsc(tsc_number):
            errors.append(f"Invalid TSC number: {tsc_number}")
        
        # Check name
        first_name, last_name = parse_name(officer_name)
        if not first_name and not last_name:
            errors.append("Could not parse name")
        
        # Check subcounty
        subcounty_normalized = normalize_subcounty(work_subcounty_raw)
        if not subcounty_normalized:
            errors.append(f"Invalid subcounty: {work_subcounty_raw}")
        else:
            subcounty_key = subcounty_normalized.lower()
            if subcounty_key not in existing_subcounties:
                errors.append(f"Subcounty not in valid list: {subcounty_normalized}")
        
        # Check for duplicates
        if not errors:
            if User.objects.filter(tsc_number=tsc_number).exists():
                stats['skipped_duplicate'] += 1
                continue
        
        if errors:
            stats['failed'] += 1
            for err in errors:
                stats['errors'][err].append(tsc_number)
            continue
        
        # Generate email
        email = f"{tsc_number.lower()}@kuppetsiaya.or.ke"
        
        # Clean phone
        phone = clean_phone(contact) if contact else ''
        
        # Get or create subcounty
        subcounty = existing_subcounties[subcounty_normalized.lower()]
        
        # Get or create school
        school_name = extract_school_name(station_name, subcounty_normalized)
        school_key = f"{school_name}_{subcounty.id}"
        if school_key not in school_cache:
            school, _ = School.objects.get_or_create(
                name=school_name,
                sub_county=subcounty
            )
            school_cache[school_key] = school
        school = school_cache[school_key]
        
        # Determine if account should be active
        # For seed data, we'll activate accounts with valid temp passwords
        is_active = (status == 'created' and len(temp_password) > 0)
        
        # Create user
        try:
            user = User.objects.create_user(
                tsc_number=tsc_number,
                email=email,
                password=temp_password if temp_password else None,
                first_name=first_name,
                last_name=last_name,
                is_active=is_active,
                approval_status='APPROVED' if is_active else 'PENDING',
                sub_county=subcounty_normalized,
                school=school.name,
                phone_number=phone,
            )
            
            stats['successful'] += 1
            
            # Print sample users
            if stats['successful'] <= 5:
                print(f"  ✓ {tsc_number} - {first_name} {last_name} ({subcounty_normalized})")
        
        except Exception as e:
            stats['failed'] += 1
            stats['errors'][str(e)].append(tsc_number)
    
    # Print summary
    print(f"\n{'='*70}")
    print(f"  INGESTION SUMMARY")
    print(f"{'='*70}")
    print(f"  Total rows processed: {stats['total_rows']}")
    print(f"  Successful:          {stats['successful']}")
    print(f"  Failed:              {stats['failed']}")
    print(f"  Duplicates skipped:  {stats['skipped_duplicate']}")
    
    if stats['errors']:
        print(f"\n  Error Details:")
        for error, tscs in sorted(stats['errors'].items(), key=lambda x: len(x[1]), reverse=True)[:10]:
            print(f"    {error}: {len(tscs)} rows")
            if len(tscs) <= 5:
                print(f"      TSCs: {', '.join(tscs)}")
    
    # Verify database state
    print(f"\n{'='*70}")
    print(f"  DATABASE VERIFICATION")
    print(f"{'='*70}")
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    approved_users = User.objects.filter(approval_status='APPROVED').count()
    print(f"  Total users in database: {total_users}")
    print(f"  Active users: {active_users}")
    print(f"  Approved users: {approved_users}")
    
    subcounty_counts = {}
    for sc in SubCounty.objects.all():
        count = User.objects.filter(sub_county=sc.name).count()
        if count > 0:
            subcounty_counts[sc.name] = count
    
    print(f"\n  Users by subcounty:")
    for sc, count in sorted(subcounty_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"    {sc}: {count}")
    
    print(f"\n{'='*70}")
    print(f"  INGESTION COMPLETE")
    print(f"{'='*70}\n")
    
    return stats


if __name__ == '__main__':
    stats = ingest_members(CSV_PATH)
    sys.exit(0 if stats['failed'] == 0 else 1)
