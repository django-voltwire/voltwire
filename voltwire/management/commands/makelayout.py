import os
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Create a new VoltWire layout template'

    def add_arguments(self, parser):
        parser.add_argument('layout_name', type=str, help='Name of the layout')
        parser.add_argument('--template', type=str, default='html',
                            choices=['html', 'vw.html'],
                            help='Template extension to use')
        parser.add_argument('--full-width', action='store_true',
                            help='Create full-width layout')

    def handle(self, *args, **options):
        layout_name = options['layout_name']
        template_extension = f".{options['template']}"

        # Create layouts directory if it doesn't exist
        layouts_dir = os.path.join(settings.BASE_DIR, 'templates', 'layouts')
        os.makedirs(layouts_dir, exist_ok=True)

        # Create layout file
        layout_file = os.path.join(layouts_dir, f"{layout_name}{template_extension}")

        # Generate layout content
        content = self._generate_layout_content(layout_name, options)

        with open(layout_file, 'w') as f:
            f.write(content)

        self.stdout.write(
            self.style.SUCCESS(f'Layout {layout_name} created successfully!')
        )
        self.stdout.write(f'  Layout file: {layout_file}')

    def _generate_layout_content(self, layout_name, options):
        """Generate layout template content"""
        full_width = options['full_width']

        lines = [
            f"<!DOCTYPE html>",
            f"<html lang=\"en\">",
            f"<head>",
            f"    <meta charset=\"UTF-8\">",
            f"    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">",
            f"    <title>{{{{ voltwire_title|default:\"VoltWire App\" }}}}</title>",
            f"    ",
            f"    {{% voltwire_scripts %}}",
            f"    ",
            f"    {{% style %}}",
            f"    <style>",
            f"        body {{ margin: 0; font-family: Arial, sans-serif; }}",
        ]

        if full_width:
            lines.extend([
                f"        .layout-{layout_name} {{ min-height: 100vh; }}",
                f"        .main-content {{ padding: 20px; }}",
            ])
        else:
            lines.extend([
                f"        .layout-{layout_name} {{ ",
                f"            max-width: 1200px;",
                f"            margin: 0 auto;",
                f"            padding: 20px;",
                f"            min-height: 100vh;",
                f"        }}",
            ])

        lines.extend([
            f"    </style>",
            f"    {{% endstyle %}}",
            f"</head>",
            f"<body>",
            f"    <div class=\"layout-{layout_name}\">",
            f"        {{% if voltwire_messages %}}",
            f"            {{% for message in voltwire_messages %}}",
            f"                <div class=\"alert alert-{{{{ message.type }}}}\">",
            f"                    {{{{ message.text }}}}",
            f"                </div>",
            f"            {{% endfor %}}",
            f"        {{% endif %}}",
            f"        ",
            f"        <!-- Main content slot -->",
            f"        {{{{ slot }}}}",
            f"    </div>",
            f"</body>",
            f"</html>",
        ])

        return '\n'.join(lines)