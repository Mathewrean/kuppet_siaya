# core/models.py

from django.db import models
from django.utils import timezone

class NewsPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=200)
    category = models.CharField(max_length=50, blank=True)
    story = models.TextField()
    featured_image = models.ImageField(upload_to='news_images/')
    secondary_image = models.ImageField(upload_to='news_images/', blank=True, null=True)
    published_date = models.DateTimeField(default=timezone.now)
    is_published = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class GalleryAlbum(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=200)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='gallery_covers/', blank=True, null=True)

    def __str__(self):
        return self.title

class GalleryImage(models.Model):
    album = models.ForeignKey(GalleryAlbum, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='gallery_images/')
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image in {self.album.title} - {self.caption or self.pk}"

class ContactMessage(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    tsc_number = models.CharField(max_length=50, blank=True) # Optional for non-members
    phone_number = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    consent = models.BooleanField(default=False)
    received_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.first_name} {self.last_name} ({self.subject})"

class BBFStatus(models.Model):
    # This model is illustrative. Actual BBF contributions and status might be more complex
    # and potentially linked to a user/profile model.
    member_name = models.CharField(max_length=200) # Placeholder, should link to User/Profile
    is_active = models.BooleanField(default=False) # True if contributions are up-to-date
    last_contribution_date = models.DateField(null=True, blank=True)
    eligibility_status = models.CharField(max_length=50, blank=True) # e.g., 'Eligible', 'Pending Arrears', 'Lapsed'

    def __str__(self):
        return f"BBF Status for {self.member_name} - {'Active' if self.is_active else 'Inactive'}"

class FinancialStatement(models.Model):
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='financial_statements/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    fiscal_year = models.CharField(max_length=10) # e.g., '2023-2024'

    def __str__(self):
        return f"{self.title} ({self.fiscal_year})"
