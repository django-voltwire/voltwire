from django.test import TestCase
from django.template import Template, Context


class VoltWireTemplateTagsTest(TestCase):

    def test_voltwire_scripts_tag(self):
        """Test voltwire_scripts template tag"""
        template = Template('{% load voltwire %}{% voltwire_scripts %}')
        result = template.render(Context({}))
        self.assertIn('voltwire.js', result)

    def test_component_tag(self):
        """Test component template tag"""
        template = Template('{% load voltwire %}{% component "TestComponent" %}')
        result = template.render(Context({}))
        self.assertIn('Component TestComponent not found', result)