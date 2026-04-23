from django.contrib import admin
from .models import CustomUser, SubCounty, School, BBFContribution, SupportTicket, LegacyTeacher

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('tsc_number', 'email', 'first_name', 'last_name', 'approval_status', 'is_active')
    list_filter = ('approval_status', 'sub_county')
    search_fields = ('tsc_number', 'email', 'first_name', 'last_name')
    actions = ['approve_users', 'reject_users']

    def approve_users(self, request, queryset):
        queryset.update(approval_status='APPROVED', is_active=True)
    approve_users.short_description = "Approve selected users"

    def reject_users(self, request, queryset):
        queryset.update(approval_status='REJECTED', is_active=False)
    reject_users.short_description = "Reject selected users"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.groups.filter(name='Sub-county Rep').exists():
            # Filter to own sub-county
            return qs.filter(sub_county=request.user.sub_county)
        return qs

admin.site.register(SubCounty)
admin.site.register(School)
admin.site.register(BBFContribution)
admin.site.register(SupportTicket)
admin.site.register(LegacyTeacher)
