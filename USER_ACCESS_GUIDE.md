# KUPPET Siaya Branch - User Access Guide

## Quick Start

### System Access

**Web Application**: http://127.0.0.1:8000
**Admin Panel**: http://127.0.0.1:8000/admin/

### Login Credentials

**Authentication Method**: TSC Number + Password

Your login credentials depend on your role:

## Role-Based Access

### 1. Regular Members 🟢

**Who**: All registered teachers with approved accounts

**Login**:
- **TSC Number**: Your unique teacher ID (e.g., 785893)
- **Password**: FirstGivenName@Last4Digits (e.g., Bernard@5893)

**Access URL**: http://127.0.0.1:8000/accounts/login/

**Features Available**:
- Dashboard: View personal information
- BBF Claims: Submit and track claims
- Profile: Update email and phone
- Support: Submit help requests

**Sample Credentials** (from seed data):
- TSC: 123456
- Email: teacher@example.com
- Password: Teacher@56 (based on TSC 123456)

### 2. Subcounty Representatives 🔵

**Who**: Designated subcounty reviewers

**Login**: Same as members (TSC + Password)

**Special Access**: 
- Can review and approve claims at subcounty level
- View subcounty dashboard

**Dashboard**: http://127.0.0.1:8000/dashboard/subcounty/dashboard/

**Additional Permissions**:
- Approve/reject claims (awaiting_subcounty status)
- Confirm beneficiary documents
- View subcounty statistics

### 3. County Representatives 🟢

**Who**: Designated county approvers

**Login**: Same as members (TSC + Password)

**Special Access**:
- Final approval authority
- View county dashboard
- Access all claim records

**Dashboard**: http://127.0.0.1:0000/dashboard/county/dashboard/

**Additional Permissions**:
- Final claim approval
- Override subcounty decisions
- Generate reports
- Export data

### 4. Super Administrators 🟡

**Who**: System administrators

**Login**: 
- **Username**: admin (or superuser created during setup)
- **Password**: As configured

**Access URL**: http://127.0.0.1:8000/admin/

**Full System Access**:
- All user management
- Content management
- System configuration
- Database administration

## Login Process

### Step-by-Step Login

1. **Navigate to Login Page**
   - Go to: http://127.0.0.1:8000/accounts/login/
   - Or click "Login" from homepage

2. **Enter Credentials**
   - **TSC Number**: Enter your full TSC number (e.g., 785893)
   - **Password**: Enter your password (e.g., Bernard@5893)

3. **Submit**
   - Click "Login" button
   - System validates credentials

4. **First Time Login**
   - You may be prompted to update email
   - System recommends changing password
   - Complete profile information

### Password Format Examples

| Member Name | TSC Number | Temporary Password | Explanation |
|-------------|-----------|-------------------|-------------|
| Andiwo, Bernard Omondi | 785893 | Bernard@5893 | First name + @ + last 4 TSC digits |
| Wanjiru, Mary Muthoni | 452178 | Mary@2178 | First name + @ + last 4 TSC digits |
| Otieno, John Ochieng | 334455 | John@3455 | First name + @ + last 4 TSC digits |
| Kamau, Peter Kipkorir | 112233 | Peter@2233 | First name + @ + last 4 TSC digits |

## Accessing Services

### Member Services

#### 1. Personal Dashboard
**URL**: http://127.0.0.1:8000/dashboard/

**What You'll See**:
- Welcome message with your name
- BBF contribution status
- Recent activities
- Quick access buttons

#### 2. BBF Claims
**URL**: http://127.0.0.1:0000/dashboard/bbf-claims/

**Features**:
- Submit new claims
- View claim history
- Track claim status
- Download documents

**Workflow**:
1. Click "New BBF Claim"
2. Add beneficiaries (children, spouse, parents)
3. Upload required documents
4. Submit for approval
5. Track status (Pending → Subcounty → County → Approved)

#### 3. Profile Management
**URL**: http://127.0.0.1:0000/dashboard/profile/

**What You Can Do**:
- Update email address
- Update phone number
- Change password (recommended)
- View account details

#### 4. Support
**URL**: http://127.0.0.1:0000/dashboard/request-info/

**Features**:
- Submit support tickets
- Track existing tickets
- Get help with issues

### Administrative Services

#### 5. Subcounty Dashboard
**URL**: http://127.0.0.1:0000/dashboard/subcounty/dashboard/

**Access**: Subcounty representatives only

**Features**:
- Review pending claims
- Approve/reject at subcounty level
- View statistics
- Download reports

#### 6. County Dashboard
**URL**: http://127.0.0.1:0000/dashboard/county/dashboard/

**Access**: County representatives only

**Features**:
- Final claim approval
- Override decisions
- Generate comprehensive reports
- Manage all claims in jurisdiction

#### 7. Gallery Management
**URL**: http://127.0.0.1:0000/gallery/

**Features**:
- View all photo albums
- Lightbox image viewer
- Download images
- Keyboard navigation

**Admin Access**:
- http://127.0.0.1:0000/admin/core/galleryalbum/
- Manage albums and images
- Configure homepage slider

#### 8. Homepage Slider
**URL**: http://127.0.0.1:0000/admin/core/galleryalbum/slider/

**Access**: Admin users only

**Features**:
- Add albums to homepage slider
- Configure slider order
- Set captions
- Enable/disable display

### System Administration

#### 9. Admin Panel
**URL**: http://127.0.0.1:0000/admin/

**Full System Control**:
- User management
- Content management
- Database administration
- System configuration

## Common Tasks

### Submitting a BBF Claim

1. **Login** to member portal
2. Navigate to **BBF Claims**
3. Click **"New BBF Claim"**
4. **Add Beneficiaries**:
   - Click "Add" for each beneficiary type
   - Enter full name
   - Upload required document
5. **Review** all information
6. **Submit** claim
7. **Track Status** in claims list

### Checking Claim Status

1. Go to **BBF Claims** page
2. Find your claim in the list
3. Check **Status** column:
   - 🟡 Pending: Awaiting initial review
   - 🔵 Awaiting Subcounty: Under subcounty review
   - 🟢 Awaiting County: Under county review
   - ✅ Approved: Fully approved
   - ❌ Rejected: Claim rejected

### Downloading Documents

1. Go to **Claim Detail** page
2. Click download icon next to document
3. File will download to your device

### Updating Profile

1. Go to **Profile** page
2. Update email or phone number
3. Click **Save Changes**
4. (Recommended) Change password

## Troubleshooting

### Login Problems

**Issue**: "Invalid credentials"
- **Solution**: 
  - Verify TSC number (no spaces)
  - Check password format (FirstName@Last4TSC)
  - Caps Lock should be OFF

**Issue**: "Account not approved"
- **Solution**:
  - Contact administrator
  - Wait for approval (may take 24-48 hours)
  - Verify documents are complete

**Issue**: Password reset not working
- **Solution**:
  - Contact system administrator
  - Superuser can reset via admin panel

### Form Submission Issues

**Issue**: "Document required"
- **Solution**:
  - Ensure file is selected
  - Check file size (< 10MB)
  - Verify format (PDF, JPG, PNG, DOC, DOCX)
  - Try different browser

**Issue**: "Maximum beneficiaries exceeded"
- **Solution**:
  - System limit: 5 children per claim
  - Remove excess or create separate claim

### File Upload Issues

**Issue**: File won't upload
- **Solution**:
  - Check file size (< 10MB)
  - Verify format is supported
  - Clear browser cache
  - Try different browser

**Issue**: Image not displaying
- **Solution**:
  - Verify upload completed
  - Check file permissions
  - Refresh page

### Access Denied

**Issue**: "Permission denied"
- **Solution**:
  - Verify your role (member, subcounty, county)
  - Contact administrator to check permissions
  - Ensure account is approved

## Contact Support

### For Members
- Submit support ticket: Dashboard → Support
- Response time: 24-48 hours

### For Administrators
- Check Django logs for errors
- Contact system administrator
- Review error messages for clues

## Security Best Practices

### Password Security
- Change temporary password immediately
- Use strong, unique passwords
- Don't share credentials
- Log out when finished

### Account Security
- Update email and phone number
- Enable two-factor authentication (if available)
- Monitor account activity
- Report suspicious activity

### Data Security
- Download only necessary documents
- Secure downloaded files
- Don't share sensitive information
- Use secure networks

## System Requirements

### Supported Browsers
- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

### Required
- Internet connection
- JavaScript enabled
- Cookies enabled
- Modern browser

## Training Resources

### Video Tutorials
- Login process
- Submitting claims
- Managing beneficiaries
- Downloading documents

### Documentation
- This guide
- In-app help tooltips
- FAQ section
- Contact support

## Updates & Announcements

### System Notifications
- Check dashboard for announcements
- Email notifications (if enabled)
- In-app messages

### New Features
- Regular updates
- New functionality
- Improved interfaces
- Enhanced security

## Feedback

### Submit Feedback
- Dashboard → Support
- Suggestion box
- Contact form

### Report Issues
- Submit support ticket
- Include screenshots
- Describe steps to reproduce
- Note error messages

---

**Last Updated**: May 2026
**Status**: Active
**Support**: Available via support ticket system

**Remember**: Your TSC number is your username. Keep it secure and never share your password! 🔒