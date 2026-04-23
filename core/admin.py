from django.contrib import admin
from .models import NewsPost, GalleryAlbum, GalleryImage, ContactMessage, BBFStatus, FinancialStatement, BECMember, BGCMember

admin.site.register(NewsPost)
admin.site.register(GalleryAlbum)
admin.site.register(GalleryImage)
admin.site.register(ContactMessage)
admin.site.register(BBFStatus)
admin.site.register(FinancialStatement)
admin.site.register(BECMember)
admin.site.register(BGCMember)
