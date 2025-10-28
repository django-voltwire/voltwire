import os
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from voltwire.utils import create_component_structure


class Command(BaseCommand):
    help = 'Create a new VoltWire component'

    def add_arguments(self, parser):
        parser.add_argument('component_path', type=str, help='Path to component (e.g., posts/CreatePost)')
        parser.add_argument('--template', type=str, default='vw.html',
                            choices=['html', 'vw.html'],
                            help='Template extension to use (both work identically)')
        parser.add_argument('--full-page', action='store_true',
                            help='Create a full page component')
        parser.add_argument('--with-form', action='store_true',
                            help='Include form handling')
        parser.add_argument('--with-model', type=str,
                            help='Specify model for CRUD operations')
        parser.add_argument('--layout', type=str,
                            help='Specify layout template')
        parser.add_argument('--crud', action='store_true',
                            help='Create CRUD operations')
        parser.add_argument('--tests', action='store_true',
                            help='Generate test files')

    def handle(self, *args, **options):
        component_path = options['component_path']
        template_extension = f".{options['template']}"

        # Parse component path
        if '/' in component_path:
            app_name, component_name = component_path.split('/', 1)
        else:
            # Try to find app automatically
            app_name = self._find_suitable_app()
            component_name = component_path

        if not app_name:
            raise CommandError('Could not determine app name. Please use format: app_name/ComponentName')

        self.stdout.write(f'Creating component {component_name} in app {app_name}')

        # Create component structure
        component_file, template_file = create_component_structure(
            app_name, component_name, template_extension
        )

        # Create Python component file
        self._create_component_py_file(component_file, component_name, options)

        # Create template file
        self._create_template_file(template_file, component_name, options)

        self.stdout.write(
            self.style.SUCCESS(f'Component {component_name} created successfully!')
        )
        self.stdout.write(f'  Python file: {component_file}')
        self.stdout.write(f'  Template file: {template_file}')

    def _find_suitable_app(self):
        """Find a suitable app for the component"""
        for app in settings.INSTALLED_APPS:
            if not app.startswith('django.') and app != 'voltwire':
                return app
        return None

    def _create_component_py_file(self, file_path, component_name, options):
        """Create the Python component file"""
        template_context = {
            'component_name': component_name,
            'full_page': options['full_page'],
            'with_form': options['with_form'],
            'with_model': options['with_model'],
            'layout': options['layout'],
            'crud': options['crud'],
        }

        content = self._generate_component_py_content(template_context)

        with open(file_path, 'w') as f:
            f.write(content)

    def _generate_component_py_content(self, context):
        """Generate Python component content"""
        component_name = context['component_name']

        lines = [
            "from voltwire import VoltWireComponent",
            "from django.shortcuts import render, redirect, get_object_or_404",
            "from django.contrib import messages",
        ]

        if context['with_model']:
            lines.append(f"from .models import {context['with_model']}")

        lines.extend([
            "",
            f"class {component_name}(VoltWireComponent):",
        ])

        # Add layout decorator if specified
        if context['layout']:
            lines.append(f"    _layout = '{context['layout']}'")

        # Add properties
        lines.extend([
            "    # Reactive properties",
            "    title = ''",
            "    content = ''",
            "    is_published = False",
        ])

        # Add methods
        lines.extend([
            "",
            "    def get(self, request):",
            "        \"\"\"Handle GET requests\"\"\"",
        ])

        if context['with_model'] and context['crud']:
            lines.extend([
                "        if hasattr(self, 'object_id'):",
                f"            self.obj = get_object_or_404({context['with_model']}, pk=self.object_id)",
                "            self.title = self.obj.title",
                "            self.content = self.obj.content",
            ])

        lines.extend([
            "        return self.render(request)",
            "",
            "    def post(self, request):",
            "        \"\"\"Handle POST requests\"\"\"",
            "        action = request.POST.get('voltwire_action')",
        ])

        if context['crud']:
            lines.extend([
                "        if action == 'save':",
                "            return self.save(request)",
                "        elif action == 'delete':",
                "            return self.delete(request)",
            ])

        lines.extend([
            "        return self.render(request)",
        ])

        if context['crud']:
            lines.extend([
                "",
                "    def save(self, request):",
                "        \"\"\"Save action\"\"\"",
                "        if self.is_valid():",
            ])

            if context['with_model']:
                lines.extend([
                    "            if hasattr(self, 'obj'):",
                    "                # Update existing",
                    "                self.obj.title = self.title",
                    "                self.obj.content = self.content",
                    "                self.obj.save()",
                    "            else:",
                    "                # Create new",
                    f"                obj = {context['with_model']}.objects.create(",
                    "                    title=self.title,",
                    "                    content=self.content,",
                    "                )",
                ])

            lines.extend([
                "            self.show_toast('Saved successfully!', type='success')",
                "            return self.redirect('home')",
                "        return self.render(request)",
                "",
                "    def delete(self, request):",
                "        \"\"\"Delete action\"\"\"",
                "        if hasattr(self, 'obj'):",
                "            self.obj.delete()",
                "            self.show_toast('Deleted successfully!', type='success')",
                "            return self.redirect('home')",
                "        return self.render(request)",
            ])

        return '\n'.join(lines)

    def _create_template_file(self, file_path, component_name, options):
        """Create the template file"""
        content = self._generate_template_content(component_name, options)

        with open(file_path, 'w') as f:
            f.write(content)

    def _generate_template_content(self, component_name, options):
        """Generate template content"""
        lines = [
            f"<!-- {component_name} VoltWire Component -->",
            f"<div class=\"component {component_name.lower()}\">",
            "    <h2>{{ voltwire_title|default:\"" + component_name + "\" }}</h2>",
            "",
            "    {% if voltwire_errors %}",
            "        <div class=\"errors\">",
            "            {% for field, errors in voltwire_errors.items %}",
            "                {% for error in errors %}",
            "                    <div class=\"error\">{{ field }}: {{ error }}</div>",
            "                {% endfor %}",
            "            {% endfor %}",
            "        </div>",
            "    {% endif %}",
            "",
        ]

        if options['with_form'] or options['crud']:
            lines.extend([
                "    <form vw:submit=\"save\">",
                "        <div class=\"form-group\">",
                "            <label>Title</label>",
                "            <input type=\"text\" vw:model=\"title\" placeholder=\"Enter title\">",
                "        </div>",
                "",
                "        <div class=\"form-group\">",
                "            <label>Content</label>",
                "            <textarea vw:model=\"content\" placeholder=\"Enter content\"></textarea>",
                "        </div>",
                "",
                "        <div class=\"form-actions\">",
                "            <button type=\"submit\" vw:loading=\"saving\">Save</button>",
            ])

            if options['crud']:
                lines.extend([
                    "            <button type=\"button\" vw:click=\"delete\" vw:confirm=\"Are you sure?\">Delete</button>",
                ])

            lines.extend([
                "        </div>",
                "    </form>",
            ])
        else:
            lines.extend([
                "    <p>Component content goes here.</p>",
                "    <button vw:click=\"handleAction\">Click Me</button>",
            ])

        lines.extend([
            "</div>",
        ])

        return '\n'.join(lines)