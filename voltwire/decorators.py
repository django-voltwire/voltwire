from functools import wraps
from django.utils.decorators import available_attrs


def layout(layout_name):
    """
    Decorator to specify layout for a component.
    Layout templates don't require Python files.
    """

    def decorator(cls):
        cls._layout = layout_name
        return cls

    return decorator


def title(page_title):
    """
    Decorator to specify page title for a component.
    """

    def decorator(cls):
        cls._title = page_title
        return cls

    return decorator


def validate(rules):
    """
    Decorator to add validation rules to component properties.
    Usage: @validate('required|min:3|max:255')
    """

    def decorator(field):
        field_name = field.__name__

        # Store validation rules in the class
        if not hasattr(field, '_validation_rules'):
            field._validation_rules = {}
        field._validation_rules[field_name] = rules

        return field

    return decorator