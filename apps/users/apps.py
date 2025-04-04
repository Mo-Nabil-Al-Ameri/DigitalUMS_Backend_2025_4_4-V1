from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'
    verbose_name = _('Users Management')
    
    def ready(self):
        try:
            import apps.users.signals
        except ImportError:
            pass
