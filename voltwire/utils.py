import os
import importlib
from django.apps import apps
from django.conf import settings


def get_component_template_paths(component_name: str, app_name: str = None):
    """
    Get possible template paths for a component.
    Supports both .vw.html and .html extensions.
    """
    extensions = getattr(settings, 'VOLTWIRE', {}).get('TEMPLATE_EXTENSIONS', ['.vw.html', '.html'])

    template_paths = []
    for ext in extensions:
        if app_name:
            template_paths.append(f"{app_name}/VoltWire/{component_name}{ext}")
        template_paths.append(f"VoltWire/{component_name}{ext}")

    return template_paths


def find_component_class(component_path: str):
    """
    Find and import a component class by its path.
    """
    try:
        module_path, class_name = component_path.rsplit('.', 1)
        module = importlib.import_module(module_path)
        component_class = getattr(module, class_name)
        return component_class
    except (ImportError, AttributeError, ValueError):
        return None


def get_installed_apps():
    """Get all installed Django apps"""
    return [app.name for app in apps.get_app_configs()]


def create_component_structure(app_name: str, component_name: str, template_extension: str = '.vw.html'):
    """
    Create the directory and file structure for a new component.
    """
    # Create VoltWire directory if it doesn't exist
    voltwire_dir = os.path.join(app_name, 'VoltWire')
    os.makedirs(voltwire_dir, exist_ok=True)

    # Component Python file
    component_file = os.path.join(voltwire_dir, f"{component_name}.py")

    # Template file with chosen extension
    template_file = os.path.join(voltwire_dir, f"{component_name}{template_extension}")

    return component_file, template_file