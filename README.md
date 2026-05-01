# KUPPET Siaya Branch - Member Management System

## Overview

A comprehensive web application for managing KUPPET Siaya Branch operations, including member services, BBF (Benefit and Welfare Fund) claims, gallery management, and administrative functions.

## Features

### Member Services
- **Member Portal**: Login and manage personal profile
- **BBF Claims**: Submit and track welfare benefit claims
- **Beneficiary Management**: Add family members (children, spouse, parents) with required documents
- **Claim Tracking**: Monitor claim status through approval workflow

### Administrative Functions
- **Subcounty Representative**: Review and approve claims at subcounty level
- **County Representative**: Final approval of claims
- **Slider Management**: Manage homepage gallery slider content
- **Gallery Management**: Upload and organize photo albums
- **News Management**: Publish branch updates and announcements

### Core Services
- Homepage with auto-advancing gallery slider
- Gallery with lightbox image viewer
- Document upload and validation (PDF, JPG, PNG, DOC, DOCX)
- File size limits: 10MB maximum
- Responsive design for all devices

## Technology Stack

- **Backend**: Django 4.2 with PostgreSQL
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Database**: SQLite (development), PostgreSQL (production)
- **Authentication**: Custom user model with TSC number login
- **File Storage**: Local storage with Django FileField

## Installation & Setup

### Prerequisites

- Python 3.13+
- Django 4.2+
- PostgreSQL (for production)
- GDAL, GEOS, PROJ (if using spatial features)

### Initial Setup

```bash
# Clone the repository
cd /home/mathewrean/Desktop/PROJECTS/kuppetsiaya

# Install dependencies (if using virtual environment)
pip install -r requirements.txt

# Run database migrations
python manage.py migrate

# Create superuser (for admin access)
python manage.py createsuperuser

# Import member data (if available)
python manage.py seed_members --file Members.docx --credentials-file member_seed_credentials.csv

# Start development server
python manage.py runserver

# Or use ASGI server for concurrent requests (recommended):
uvicorn kuppetsiaya.asgi:application --host 0.0.0.0 --port 8000 --workers 4
```

## Login Instructions

### Authentication Method

**Login uses TSC Number + Password**

- **Username Field**: TSC Number (Teacher Service Commission number)
- **Password**: As assigned by system administrator

### Temporary Password Format

For new members, temporary passwords follow this format:

```
FirstGivenName@Last4Digits
```

**Examples:**

| Member Name | TSC Number | Temporary Password |
|-------------|------------|-------------------|
| Mr Andiwo, Bernard Omondi | 785893 | Bernard@5893 |
| Ms Wanjiru, Mary Muthoni | 452178 | Mary@2178 |
| Mr Otieno, John Ochieng | 334455 | John@3455 |

### First Login Process

1. Navigate to the login page
2. Enter your TSC number
3. Enter your temporary password (format: `FirstName@Last4OfTSC`)
4. Upon successful login, you will be prompted to:
   - Update your email address
   - Change your password (recommended)
   - Verify your phone number

### Password Requirements

- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character

## User Roles & Access

### 1. Regular Members

**Access Level**: Basic member portal

**Permissions**:
- View and edit personal profile
- Submit BBF claims
- Add/remove beneficiaries
- Upload supporting documents
- Track claim status
- View approved claims

**Login URL**: `/accounts/login/`

### 2. Subcounty Representatives

**Access Level**: Claim Reviewer (Subcounty Level)

**Permissions**:
- All member permissions
- Review claims awaiting subcounty approval
- Approve or reject claims at subcounty level
- View subcounty dashboard
- Confirm beneficiary documents

**How to Enable**:
```python
# In Django admin or shell
user = CustomUser.objects.get(tsc_number='TSC_NUMBER')
user.is_subcounty_rep = True
user.save()
```

**Dashboard**: `/dashboard/subcounty/dashboard/`

### 3. County Representatives

**Access Level**: Claim Approver (Final Level)

**Permissions**:
- All subcounty representative permissions
- Final approval of claims
- View county dashboard
- Override subcounty decisions (with reason)
- Access county-level reports

**How to Enable**:
```python
# In Django admin or shell
user = CustomUser.objects.get(tsc_number='TSC_NUMBER')
user.is_county_rep = True
user.save()
```

**Dashboard**: `/dashboard/county/dashboard/`

### 4. Super Administrators

**Access Level**: Full System Access

**Permissions**:
- All user permissions
- Django admin panel access
- User management (create/disable accounts)
- System configuration
- Database management
- View all reports

**How to Create**:
```bash
python manage.py createsuperuser
```

## Accessing Different Services

### 1. Member Portal

**URL**: `/dashboard/`

**Features**:
- Personal dashboard with BBF status
- Recent contributions
- Quick links to services
- Profile management

**Navigation**:
- Dashboard: `/dashboard/`
- BBF Status: `/dashboard/bbf-status/`
- Financials: `/dashboard/financials/`
- Profile: `/dashboard/profile/`
- Support: `/dashboard/request-info/`

### 2. BBF Claims System

**URL**: `/dashboard/bbf-claims/`

**Features**:
- Submit new claims
- Track claim status
- Add beneficiaries
- Upload documents

**Workflow**:
1. **New Claim**: `/dashboard/bbf-claims/new/`
   - Add beneficiaries (children, spouse, parents)
   - Upload required documents
   - Submit for approval

2. **Claim Detail**: `/dashboard/bbf-claims/<id>/`
   - View claim details
   - Track approval status
   - Download documents

3. **Approval Process**:
   - Pending → Subcounty Review → County Review → Approved/Rejected

**Status Indicators**:
- 🟡 Pending: Submitted, awaiting review
- 🔵 Awaiting Subcounty: Under subcounty review
- 🟢 Awaiting County: Under county review
- ✅ Approved: Fully approved
- ❌ Rejected: Claim rejected (reason provided)

### 3. Subcounty Review Portal

**URL**: `/dashboard/subcounty/dashboard/`

**Features**:

## API Endpoints by User Role

**Unauthenticated (Public):**
- GET `/` — Homepage (public site content and homepage slider). Authentication: None.
- GET `/about/` — About page. Authentication: None.
- GET `/projects/`, GET `/projects/bbf/`, GET `/projects/bus/`, GET `/projects/kuppet-center/` — Projects pages. Authentication: None.
- GET `/gallery/` — Gallery listing. Authentication: None.
- GET `/gallery/<slug>/` — Gallery album detail. Authentication: None.
- GET `/news/` — News archive. Authentication: None.
- GET `/news/<slug>/` — News detail. Authentication: None.
- POST `/contact/` — Contact form submission. Authentication: None.

**Member (Logged-in with TSC Number):**
- Web pages:
   - GET `/dashboard/` — Member dashboard (requires login).
   - GET `/dashboard/bbf-claims/` — BBF claims list page.
   - GET `/dashboard/bbf-claims/new/` — BBF claim creation page.
   - GET `/dashboard/bbf-claims/<id>/` — BBF claim detail and document upload view.
- API endpoints:
   - GET `/api/bbf/claims/` — List member's BBF claims. Authentication: Member.
   - POST `/api/bbf/claims/` — Create a new BBF claim (with beneficiaries). Authentication: Member.
   - GET `/api/bbf/claims/<id>/` — Retrieve a single BBF claim. Authentication: Member.
   - POST `/api/bbf/claims/<id>/add_beneficiary/` — Add a beneficiary to a pending claim. Authentication: Member.
   - POST `/api/bbf/beneficiaries/<id>/upload_document/` — Upload or replace a beneficiary document (PDF/JPG/PNG, max 5MB). Authentication: Member (must own the claim).
   - DELETE `/api/bbf/beneficiaries/<id>/delete/` — Remove a beneficiary from a pending claim. Authentication: Member.
   - GET `/api/bbf/beneficiaries/` — List beneficiaries for the member's claims. Authentication: Member.
   - GET `/dashboard/bbf-status/` — BBF Status page (web). Authentication: Member.

**Sub-County Representative:**
- GET `/api/bbf/subcounty/claims/` — List claims awaiting subcounty confirmation. Authentication: Sub-County Representative.
- POST `/api/bbf/subcounty/claims/<id>/confirm/` — Confirm a claim (moves to awaiting county). Authentication: Sub-County Representative.
- POST `/api/bbf/subcounty/claims/<id>/reject/` — Reject a claim at subcounty level. Authentication: Sub-County Representative.
- POST `/api/bbf/beneficiaries/<id>/approve/` — Approve a beneficiary document. Authentication: Sub-County Representative.
- POST `/api/bbf/beneficiaries/<id>/reject/` — Reject a beneficiary document. Authentication: Sub-County Representative.

**County Representative:**
- GET `/api/bbf/county/claims/` — List claims awaiting county confirmation. Authentication: County Representative.
- POST `/api/bbf/county/claims/<id>/confirm/` — Approve a claim at county level. Authentication: County Representative.
- POST `/api/bbf/county/claims/<id>/reject/` — Reject a claim at county level. Authentication: County Representative.
- POST `/api/bbf/beneficiaries/<id>/approve/` — Approve a beneficiary document. Authentication: County Representative.
- POST `/api/bbf/beneficiaries/<id>/reject/` — Reject a beneficiary document. Authentication: County Representative.

**Administrator:**
- Admin site `/admin/` — Full admin management (users, claims, beneficiaries, gallery, news, financial statements). Authentication: Admin.
- API: All of the endpoints above are available to administrators; additionally, administrators can manage users and site content via the admin UI and API views as applicable.

> Note: API endpoints for BBF are mounted under `/api/bbf/`.
- List of claims awaiting review
- Document verification tools
- Bulk approval/rejection
- Status history

**Access**: Requires `is_subcounty_rep = True`

### 4. County Review Portal

**URL**: `/dashboard/county/dashboard/`

**Features**:
- Final approval interface
- Override capabilities
- Reporting tools
- Export functions

**Access**: Requires `is_county_rep = True`

### 5. Gallery Management

**URL**: `/gallery/`

**Features**:
- View all albums
- Lightbox image viewer
- Download images
- Keyboard navigation (← → arrows, ESC to close)

**Admin Access**:
- `/admin/core/galleryalbum/` - Manage albums
- `/admin/core/galleryalbum/slider/` - Manage homepage slider

### 6. Admin Panel

**URL**: `/admin/`

**Features**:
- User management
- Content management
- System configuration
- Database administration

**Access**: Superuser accounts only

## Homepage Features

### Auto-Advancing Gallery Slider

- Displays published albums with cover images
- Auto-advances every 5 seconds
- Pause on hover
- Navigation arrows and dots
- Direct links to album pages
- Collapses if no albums configured

**API Endpoint**: `/api/gallery/homepage-slider/`

Returns JSON array of slider items:
```json
[
  {
    "id": 1,
    "album_name": "Album Title",
    "album_slug": "album-slug",
    "cover_image_url": "/media/gallery_covers/image.jpg",
    "slider_caption": "Caption text",
    "slider_order": 0
  }
]
```

## File Upload Guidelines

### Supported Formats

- **Documents**: PDF, DOC, DOCX
- **Images**: JPG, JPEG, PNG

### Requirements by Document Type

| Beneficiary Type | Required Document | Format | Max Size |
|-----------------|-------------------|---------|----------|
| Child | Birth Certificate | PDF/JPG/PNG | 10MB |
| Spouse | Marriage Affidavit | PDF/DOC/DOCX | 10MB |
| Mother | National ID Card | PDF/JPG/PNG | 10MB |
| Father | National ID Card | PDF/JPG/PNG | 10MB |

### Upload Process

1. Click "Add" button for beneficiary type
2. Fill in full name
3. Click "Choose File" and select document
4. Verify file name appears
5. Repeat for additional beneficiaries
6. Click "Submit Claim"

## Test Credentials (Development)

Use these accounts for local testing. These are example credentials for the development/test environment only — do not use in production.

- Member:
   - TSC Number: TSC12345
   - Password: TestPass!23
   - Access: Member dashboard, BBF claims

- Subcounty Representative:
   - TSC Number: SUBCOUNTY1
   - Password: SubPass!23
   - Access: Subcounty dashboard, claim review

- County Representative:
   - TSC Number: COUNTY1
   - Password: CountyPass!23
   - Access: County dashboard, final approvals

- Admin / Superuser:
   - Create with: `python manage.py createsuperuser` (or use your local admin credentials)

To enable rep roles in the Django shell or admin:
```python
# Example: enable subcounty role for a user
from accounts.models import CustomUser
u = CustomUser.objects.get(tsc_number='SUBCOUNTY1')
u.is_subcounty_rep = True
u.save()
```

## Troubleshooting

### Login Issues

**Problem**: "Invalid credentials"
- **Solution**: Verify TSC number format (no spaces, correct case)
- Check if temporary password follows format: `FirstName@Last4TSC`

**Problem**: "Account not approved"
- **Solution**: Contact administrator to verify approval status
- Check if `approval_status` is 'APPROVED' in database

**Problem**: Password reset not working
- **Solution**: Contact system administrator
- Superuser can reset passwords via admin panel

### Form Submission Issues

**Problem**: "At least one beneficiary must have a document"
- **Solution**: Ensure file is selected and uploaded
- Check file size (max 10MB)
- Verify file format is supported

**Problem**: "Document required for [Type]"
- **Solution**: Each beneficiary needs a document
- Upload the required document type

**Problem**: "Maximum of 5 children allowed"
- **Solution**: System limit of 5 child beneficiaries per claim
- Remove excess children or create separate claim

### File Upload Issues

**Problem**: File not uploading
- **Solution**: Check file size (max 10MB)
- Verify file format (PDF, JPG, PNG, DOC, DOCX)
- Try different browser
- Clear browser cache

**Problem**: Image not displaying in gallery
- **Solution**: Verify image is properly uploaded
- Check file permissions
- Regenerate thumbnails if needed

## Database Management

### Backup

```bash
# Backup database
python manage.py dumpdata > backup.json

# Backup media files
tar -czf media_backup.tar.gz media/
```

### Restore

```bash
# Restore database
python manage.py loaddata backup.json

# Restore media files
tar -xzf media_backup.tar.gz
```

### Migrations

```bash
# Create new migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migration status
python manage.py showmigrations
```

## Security Features

- CSRF protection on all forms
- Password hashing (PBKDF2)
- File upload validation
- File type verification
- File size limits
- Session management
- Secure cookie flags
- XSS protection
- SQL injection prevention

## API Endpoints

### Public APIs

- `GET /api/gallery/homepage-slider/` - Get slider data
- `GET /gallery/<slug>/` - Gallery album detail

### Member APIs

- `GET/POST /api/bbf/claims/` - BBF claims (requires authentication)
- `GET/POST /api/bbf/beneficiaries/` - Beneficiary management

### Admin APIs

- `GET /api/bbf/subcounty/claims/` - Subcounty claims
- `POST /api/bbf/subcounty/claims/<id>/confirm/` - Confirm claim
- `POST /api/bbf/subcounty/claims/<id>/reject/` - Reject claim
- `GET /api/bbf/county/claims/` - County claims
- `POST /api/bbf/county/claims/<id>/confirm/` - Approve claim
- `POST /api/bbf/county/claims/<id>/reject/` - Reject claim

## Support

For technical support or issues:
1. Check troubleshooting section above
2. Review error messages carefully
3. Contact system administrator
4. Check Django logs for detailed errors

## Development

### Running Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test bbf
python manage.py test core
python manage.py test dashboard

# Run with verbosity
python manage.py test --verbosity=2
```

### Creating Migrations

```bash
# After model changes
python manage.py makemigrations
python manage.py migrate
```

### Superuser Creation

```bash
python manage.py createsuperuser
```

## Environment Variables

For production deployment, set these environment variables:

```bash
export SECRET_KEY='your-secret-key'
export DEBUG=False
export ALLOWED_HOSTS='your-domain.com'
export DATABASE_URL='postgresql://user:password@localhost/dbname'
export EMAIL_HOST='smtp.example.com'
export EMAIL_PORT=587
export EMAIL_HOST_USER='user@example.com'
export EMAIL_HOST_PASSWORD='password'
```

## License

KUPPET Siaya Branch Management System

## Contact

For questions or support, contact the system administrator or IT department.

---

**Last Updated**: May 2026
**Version**: 1.0.0
**Status**: Production Ready ✅