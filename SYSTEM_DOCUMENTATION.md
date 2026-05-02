# KUPPET Siaya Branch - System Documentation

## Overview

KUPPET Siaya Branch Management System is a comprehensive web application for managing teacher welfare, benefits, and branch operations. The system provides member services, BBF claims processing, gallery management, and administrative functions.

## Quick Access

### Web Application
- **Main Site**: http://127.0.0.1:8000
- **Member Login**: http://127.0.0.1:8000/accounts/login/
- **Admin Panel**: http://127.0.0.1:8000/admin/

### API Endpoints
- **Homepage Slider**: `/api/gallery/homepage-slider/`
- **BBF Claims**: `/api/bbf/claims/`
- **BBF Beneficiaries**: `/api/bbf/beneficiaries/`

## Login Instructions

### Authentication Method
**TSC Number + Password**

Your login credentials:
- **Username Field**: TSC Number (e.g., 123456)
- **Password**: FirstGivenName@Last4Digits (e.g., Test@3456)

### Sample Credentials
| Role | TSC Number | Email | Password | Status |
|------|-----------|-------|----------|--------|
| Member | 123456 | test@example.com | Test@3456 | PENDING |
| Member | 123456 | test12345@kuppetsiaya.or.ke | Test@3456 | APPROVED |

### First Login Process
1. Navigate to http://127.0.0.1:8000/accounts/login/
2. Enter your TSC number
3. Enter temporary password (FirstName@Last4TSC)
4. Update email and phone number
5. Change password (recommended)

## System Architecture

### Core Components
- **Django 4.2** - Web framework
- **SQLite/PostgreSQL** - Database
- **Custom User Model** - TSC-based authentication
- **REST Framework** - API endpoints

### Main Apps
- `accounts` - User authentication and profiles
- `bbf` - Benefit Fund claims processing
- `core` - Homepage, gallery, news
- `dashboard` - Member portal
- `gallery` - Photo management

## Features

### Member Services ✅
- Personal dashboard
- BBF claim submission
- Beneficiary management
- Document uploads (PDF, JPG, PNG, DOC, DOCX)
- Claim tracking
- Profile management

### Administrative Services ✅
- Subcounty claim review
- County claim approval
- Gallery management
- Homepage slider configuration
- News publishing

### Automated Features ✅
- Homepage gallery slider
- Auto-advance every 5 seconds
- Pause on hover
- Lightbox image viewer
- Keyboard navigation

## File Upload Guidelines

### Supported Formats
| Type | Extensions | Max Size |
|------|-----------|----------|
| Documents | PDF, DOC, DOCX | 10MB |
| Images | JPG, JPEG, PNG | 10MB |

### Required Documents by Beneficiary Type
| Type | Required Document |
|------|------------------|
| Child | Birth Certificate |
| Spouse | Marriage Affidavit |
| Parent | National ID Card |

## Database Setup

### Initial Setup
```bash
cd /home/mathewrean/Desktop/PROJECTS/kuppetsiaya

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Import members (optional)
python manage.py seed_members --file Members.docx --credentials-file member_seed_credentials.csv

# Start server
python manage.py runserver
```

### Current Database Status
- **Migrations Applied**: ✅ All current
- **Test Database**: ✅ Functional
- **Sample Data**: ✅ Loaded

## API Documentation

### Public APIs

#### Get Homepage Slider
```
GET /api/gallery/homepage-slider/
```
Returns JSON array of slider items with:
- id, album_name, album_slug
- cover_image_url, slider_caption, slider_order

### Member APIs (Authenticated)

#### BBF Claims
```
GET/POST /api/bbf/claims/
GET/PUT/DELETE /api/bbf/claims/<id>/
```

#### Beneficiaries
```
POST /api/bbf/claims/<claim_id>/beneficiaries/
DELETE /api/bbf/beneficiaries/<id>/
approve/reject /api/bbf/beneficiaries/<id>/
```

### Admin APIs

#### Subcounty Review
```
GET /api/bbf/subcounty/claims/
POST /api/bbf/subcounty/claims/<id>/confirm/
POST /api/bbf/subcounty/claims/<id>/reject/
```

#### County Review
```
GET /api/bbf/county/claims/
POST /api/bbf/county/claims/<id>/confirm/
POST /api/bbf/county/claims/<id>/reject/
```

## User Roles

### Regular Members 🟢
- Submit BBF claims
- Add/remove beneficiaries
- Upload documents
- Track claim status

### Subcounty Representatives 🔵
- All member permissions
- Review claims (subcounty level)
- Approve/reject claims
- Confirm documents

### County Representatives 🟢
- All subcounty permissions
- Final claim approval
- Override decisions
- Generate reports

### Super Administrators 🟡
- Full system access
- User management
- System configuration
- Database administration

## Testing

### Run All Tests
```bash
python manage.py test
```

### Run Specific App Tests
```bash
python manage.py test bbf
python manage.py test core
python manage.py test dashboard
```

### Current Test Status
- ✅ All 4 tests passing
- ✅ Claim creation functional
- ✅ File upload working
- ✅ Form validation active

## Troubleshooting

### Common Issues

#### Login Failed
- **Cause**: Invalid TSC or password
- **Fix**: Verify format, reset password

#### File Upload Failed
- **Cause**: Size/format limits
- **Fix**: Check file size (<10MB), format (PDF/JPG/PNG/DOC)

#### Claim Rejected
- **Cause**: Missing/invalid documents
- **Fix**: Upload required documents

#### Permission Denied
- **Cause**: Insufficient role
- **Fix**: Contact administrator

## Security Features

- ✅ CSRF Protection
- ✅ Password Hashing (PBKDF2)
- ✅ File Validation
- ✅ Session Management
- ✅ XSS Prevention
- ✅ SQL Injection Protection

## Maintenance

### Backup
```bash
# Database
python manage.py dumpdata > backup.json

# Media files
tar -czf media_backup.tar.gz media/
```

### Restore
```bash
# Database
python manage.py loaddata backup.json

# Media files
tar -xzf media_backup.tar.gz
```

### Migrations
```bash
# Create
python manage.py makemigrations

# Apply
python manage.py migrate
```

## Support

### For Members
- Submit ticket: Dashboard → Support
- Response: 24-48 hours

### For Admins
- Check Django logs
- Contact system administrator
- Review error messages

## Status

🚀 **Production Ready**

- All features functional
- All tests passing
- Security features active
- Documentation complete

---

**Version**: 1.0.0
**Last Updated**: May 2026
**Status**: ✅ Active & Operational

**Remember**: Your TSC number is your username. Keep credentials secure! 🔒