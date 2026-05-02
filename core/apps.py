from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        from kuppetsiaya.admin_security import apply_admin_security
        from kuppetsiaya.compat import apply_compat_patches

        apply_admin_security()
        apply_compat_patches()
