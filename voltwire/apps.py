from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class VoltWireConfig(AppConfig):
    name = 'voltwire'
    verbose_name = 'VoltWire'

    def ready(self):
        # Validate settings
        self._validate_settings()

    def _validate_settings(self):
        """Validate VoltWire settings"""
        if not hasattr(settings, 'VOLTWIRE'):
            return

        voltwire_settings = settings.VOLTWIRE

        # Validate template extensions
        if 'TEMPLATE_EXTENSIONS' in voltwire_settings:
            extensions = voltwire_settings['TEMPLATE_EXTENSIONS']
            if not isinstance(extensions, list):
                raise ImproperlyConfigured(
                    "VOLTWIRE['TEMPLATE_EXTENSIONS'] must be a list"
                )