from django.core.management.base import BaseCommand
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Install and configure VoltWire in the current Django project'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Installing VoltWire...'))

        # Check if VoltWire is in INSTALLED_APPS
        if 'voltwire' not in settings.INSTALLED_APPS:
            self.stdout.write(
                self.style.WARNING('Please add "voltwire" to INSTALLED_APPS in settings.py')
            )

        # Check if middleware is added
        middleware_added = False
        for middleware in settings.MIDDLEWARE:
            if 'voltwire.middleware.VoltWireMiddleware' in middleware:
                middleware_added = True
                break

        if not middleware_added:
            self.stdout.write(
                self.style.WARNING('Please add "voltwire.middleware.VoltWireMiddleware" to MIDDLEWARE in settings.py')
            )

        # Create static directory for VoltWire
        static_dir = os.path.join(settings.BASE_DIR, 'static', 'voltwire', 'js')
        os.makedirs(static_dir, exist_ok=True)

        # Create sample VoltWire component structure
        for app in settings.INSTALLED_APPS:
            if app.startswith('django.') or app in ['voltwire']:
                continue

            # Create VoltWire directory in app
            voltwire_dir = os.path.join(app.replace('.', '/'), 'VoltWire')
            os.makedirs(voltwire_dir, exist_ok=True)

            # Create __init__.py in VoltWire directory
            init_file = os.path.join(voltwire_dir, '__init__.py')
            if not os.path.exists(init_file):
                with open(init_file, 'w') as f:
                    f.write('# VoltWire components directory\n')

        self.stdout.write(
            self.style.SUCCESS('VoltWire installed successfully!')
        )
        self.stdout.write(
            self.style.SUCCESS('You can now create components with: python manage.py makecomponent')
        )