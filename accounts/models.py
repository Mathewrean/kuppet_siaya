# accounts/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import BaseUserManager


class SubCounty(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class School(models.Model):
    name = models.CharField(max_length=150)
    sub_county = models.ForeignKey(SubCounty, on_delete=models.CASCADE, related_name='schools')

    def __str__(self):
        return f"{self.name} ({self.sub_county.name})"


class CustomUserManager(BaseUserManager):
    def create_user(self, tsc_number, email=None, password=None, **extra_fields):
        if not tsc_number:
            raise ValueError(_('Users must have a TSC number'))

        user = self.model(
            tsc_number=tsc_number,
            email=self.normalize_email(email) if email else None,
            **extra_fields
        )
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, tsc_number, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('approval_status', 'APPROVED') # Superusers are always approved

        if not email:
            raise ValueError(_('Super users must have an email address.'))

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Super user must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Super user must have is_superuser=True.'))

        return self.create_user(tsc_number, email, password, **extra_fields)


class CustomUser(AbstractUser):
    # Unique identifier for teachers
    tsc_number = models.CharField(max_length=50, unique=True)
    email = models.EmailField(_('email address'), unique=True, null=True, blank=True)

    # Fields from registration form
    phone_number = models.CharField(max_length=20, blank=True)
    sub_county = models.CharField(max_length=100, blank=True)
    school = models.CharField(max_length=150, blank=True)

    # Approval fields
    APPROVAL_STATUS_CHOICES = [
        ('PENDING', _('Pending Approval')),
        ('APPROVED', _('Approved')),
        ('REJECTED', _('Rejected')),
    ]
    approval_status = models.CharField(max_length=10, choices=APPROVAL_STATUS_CHOICES, default='PENDING')
    approval_date = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_users'
    )

    # For TOTP (Two-Factor Authentication)
    totp_secret = models.CharField(max_length=16, blank=True)
    totp_enabled = models.BooleanField(default=False)
    
    # Role fields for BBF workflow
    is_subcounty_rep = models.BooleanField(default=False)
    is_county_rep = models.BooleanField(default=False)

    # Usernames are not suitable for this context, use email or TSC number
    username = None
    USERNAME_FIELD = 'tsc_number' # Use TSC number for login
    REQUIRED_FIELDS = ['email']

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.get_full_name()} ({self.tsc_number})"

    def has_perm(self, perm, obj=None):
        # Handle staff and superuser permissions
        if self.is_active and self.is_superuser:
            return True
        return super().has_perm(perm, obj)

    def has_module_perms(self, app_label):
        # Handle staff and superuser permissions
        if self.is_active and self.is_superuser:
            return True
        return super().has_module_perms(app_label)


class BBFContribution(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='bbf_contributions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    contribution_date = models.DateField()
    reference = models.CharField(max_length=100)
    status = models.CharField(max_length=50, default='Pending')

    def __str__(self):
        return f"BBF contribution of {self.amount} by {self.user.get_full_name()} on {self.contribution_date}"

class SupportTicket(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='support_tickets')
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, default='Open') # e.g., 'Open', 'In Progress', 'Resolved'

    def __str__(self):
        return f"Support Ticket #{self.pk} - {self.subject} ({self.status})"


class LegacyTeacher(models.Model):
    tsc_number = models.CharField(max_length=50, unique=True)
    full_name = models.CharField(max_length=200)
    # Add other fields as needed from legacy DB

    class Meta:
        managed = False
        db_table = 'teachers'  # Assuming table name in legacy DB

    def __str__(self):
        return f"{self.full_name} ({self.tsc_number})"


class Notification(models.Model):
    """Notification model for BBF claim status updates"""
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Link to BBF claim if applicable
    bbf_claim = models.ForeignKey(
        'bbf.BBFClaim',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )
    
    def __str__(self):
        return f"{self.title} - {self.user.get_full_name()}"
