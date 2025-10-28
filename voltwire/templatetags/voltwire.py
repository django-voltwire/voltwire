from django import template
from django.template.loader import get_template
from django.utils.safestring import mark_safe
import json

register = template.Library()


@register.simple_tag
def voltwire_scripts():
    """
    Include VoltWire JavaScript files.
    """
    return mark_safe('<script src="/static/voltwire/js/voltwire.js"></script>')


@register.simple_tag
def component(component_name, **props):
    """
    Render a VoltWire component.
    Usage: {% component 'CreatePost' props={user: request.user} %}
    """
    try:
        # Import the component class
        from voltwire.utils import find_component_class
        component_class = find_component_class(component_name)

        if component_class:
            # Create component instance
            component_instance = component_class()

            # Set properties from props
            for prop_name, prop_value in props.items():
                if hasattr(component_instance, prop_name):
                    setattr(component_instance, prop_name, prop_value)

            # Render the component
            from django.template import RequestContext
            context = component_instance.get_voltwire_context()

            # Get template
            template_name = component_instance.get_template_name()
            template_obj = get_template(template_name)

            return template_obj.render(context)
        else:
            return f"<!-- Component {component_name} not found -->"

    except Exception as e:
        return f"<!-- Error rendering component {component_name}: {str(e)} -->"


@register.tag(name='voltwire')
def do_voltwire_component(parser, token):
    """
    Define a component directly in templates using voltwire tag.
    """
    try:
        # Parse the component definition
        components = []
        while True:
            token = parser.next_token()
            if token.contents == 'endvoltwire':
                break
            components.append(token)

        # For now, return empty string - full implementation would parse YAML-like syntax
        return template.Node()
    except template.TemplateSyntaxError:
        return template.Node()


@register.simple_tag
def voltwire_include(template_name):
    """
    Include a template that contains voltwire component definitions.
    """
    try:
        template_obj = get_template(template_name)
        return template_obj.render({})
    except:
        return f"<!-- Error including {template_name} -->"


@register.filter
def voltwire_json(value):
    """
    Convert value to JSON for VoltWire attributes.
    """
    return mark_safe(json.dumps(value))