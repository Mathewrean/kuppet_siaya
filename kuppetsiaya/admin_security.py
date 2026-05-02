from types import MethodType

from django.contrib import admin
from django.contrib.admin.forms import AdminAuthenticationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class SuperuserAdminAuthenticationForm(AdminAuthenticationForm):
    error_messages = {
        **AdminAuthenticationForm.error_messages,
        "invalid_login": _(
            "Please enter the correct %(username)s and password for a superuser account. "
            "Note that both fields may be case-sensitive."
        ),
    }

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_superuser:
            raise ValidationError(
                self.error_messages["invalid_login"],
                code="invalid_login",
                params={"username": self.username_field.verbose_name},
            )


def _superuser_only_has_permission(self, request):
    return request.user.is_active and request.user.is_superuser


def apply_admin_security():
    admin.site.login_form = SuperuserAdminAuthenticationForm
    admin.site.has_permission = MethodType(_superuser_only_has_permission, admin.site)
