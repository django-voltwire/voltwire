import json
import inspect
from typing import Dict, Any, List, Optional
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views import View
from django.core.exceptions import ValidationError
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
import re


class VoltWireComponent(View):
    """
    Base class for all VoltWire components.
    Works exactly like traditional Django class-based views.
    """

    # Component metadata
    _layout = None
    _title = None
    _properties = {}
    _validation_rules = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._errors = {}
        self._is_voltwire_request = False
        self._initialized_properties = False

    def setup(self, request: HttpRequest, *args, **kwargs):
        """Initialize component - similar to Django's setup()"""
        super().setup(request, *args, **kwargs)
        self._initialize_properties()
        self.mount(request, *args, **kwargs)

    def mount(self, request: HttpRequest, *args, **kwargs):
        """
        Called when component initializes.
        Override this in components for initialization logic.
        """
        pass

    def _initialize_properties(self):
        """Initialize reactive properties from class definition"""
        if self._initialized_properties:
            return

        for attr_name in dir(self):
            # Skip private and special methods
            if attr_name.startswith('_'):
                continue

            attr_value = getattr(self, attr_name)

            # Skip methods and callables
            if callable(attr_value):
                continue

            # Skip if already set in instance
            if attr_name in self.__dict__:
                continue

            # Set as instance attribute
            setattr(self, attr_name, attr_value)

        self._initialized_properties = True

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        """Handle requests with VoltWire awareness"""
        self._is_voltwire_request = request.headers.get('X-VoltWire-Request') == 'true'

        if request.method.lower() in self.http_method_names:
            handler = getattr(self, request.method.lower(), self.http_method_not_allowed)
        else:
            handler = self.http_method_not_allowed

        # Handle VoltWire actions
        if self._is_voltwire_request and request.method == 'POST':
            action = request.POST.get('voltwire_action')
            if action and hasattr(self, action):
                return getattr(self, action)(request, *args, **kwargs)

        return handler(request, *args, **kwargs)

    def render(self, request: HttpRequest, template_name: str = None, context: Dict = None) -> HttpResponse:
        """Render component with VoltWire context"""
        if context is None:
            context = {}

        # Get template name from class if not provided
        if template_name is None:
            template_name = self.get_template_name()

        # Add VoltWire context
        context.update(self.get_voltwire_context())

        # Handle VoltWire requests with JSON response
        if self._is_voltwire_request:
            return self._render_voltwire_response(request, context)

        return render(request, template_name, context)

    def _render_voltwire_response(self, request: HttpRequest, context: Dict) -> JsonResponse:
        """Render JSON response for VoltWire requests"""
        from django.template.loader import render_to_string

        html_content = render_to_string(self.get_template_name(), context, request=request)

        response_data = {
            'success': True,
            'html': html_content,
            'title': getattr(self, '_title', None),
            'errors': self._errors,
            'properties': self._get_serialized_properties(),
            'messages': self._get_messages(request),
            'redirect': None,
        }

        return JsonResponse(response_data)

    def get_template_name(self) -> str:
        """Get template name for this component"""
        class_name = self.__class__.__name__
        module = self.__class__.__module__
        app_name = module.split('.')[0]

        # Try both .vw.html and .html extensions
        template_extensions = getattr(self, '_template_extensions', ['.vw.html', '.html'])

        for ext in template_extensions:
            template_name = f"VoltWire/{class_name}{ext}"
            # Check if template exists
            try:
                from django.template.loader import get_template
                get_template(template_name)
                return template_name
            except:
                continue

        # Fallback to default
        return f"VoltWire/{class_name}.html"

    def get_voltwire_context(self) -> Dict[str, Any]:
        """Get VoltWire-specific context data"""
        context = {
            'voltwire_component': self,
            'voltwire_title': getattr(self, '_title', None),
            'voltwire_properties': self._get_serialized_properties(),
            'voltwire_errors': self._errors,
        }

        # Add all public properties to context
        for attr_name in dir(self):
            if not attr_name.startswith('_') and not callable(getattr(self, attr_name)):
                context[attr_name] = getattr(self, attr_name)

        return context

    def _get_serialized_properties(self) -> Dict[str, Any]:
        """Get serializable properties for client-side"""
        properties = {}
        for attr_name in dir(self):
            if attr_name.startswith('_'):
                continue
            attr_value = getattr(self, attr_name)
            if not callable(attr_value):
                try:
                    json.dumps(attr_value)  # Test serialization
                    properties[attr_name] = attr_value
                except (TypeError, ValueError):
                    properties[attr_name] = str(attr_value)
        return properties

    def _get_messages(self, request: HttpRequest) -> List[Dict]:
        """Extract messages for VoltWire response"""
        message_list = []
        for message in messages.get_messages(request):
            message_list.append({
                'text': str(message),
                'type': message.tags,
                'level': message.level,
            })
        return message_list

    def is_valid(self) -> bool:
        """Validate component properties"""
        self._errors = {}

        for property_name, rules in self._validation_rules.items():
            if hasattr(self, property_name):
                value = getattr(self, property_name)
                errors = self._validate_property(property_name, value, rules)
                if errors:
                    self._errors[property_name] = errors

        return len(self._errors) == 0

    def _validate_property(self, property_name: str, value: Any, rules: str) -> List[str]:
        """Validate a single property against rules"""
        errors = []
        rule_list = [rule.strip() for rule in rules.split('|')]

        for rule in rule_list:
            if rule == 'required':
                if value is None or value == '':
                    errors.append('This field is required.')
            elif rule.startswith('min:'):
                min_val = int(rule.split(':')[1])
                if isinstance(value, (int, float)) and value < min_val:
                    errors.append(f'Value must be at least {min_val}.')
                elif isinstance(value, str) and len(value) < min_val:
                    errors.append(f'Must be at least {min_val} characters.')
            elif rule.startswith('max:'):
                max_val = int(rule.split(':')[1])
                if isinstance(value, (int, float)) and value > max_val:
                    errors.append(f'Value must be at most {max_val}.')
                elif isinstance(value, str) and len(value) > max_val:
                    errors.append(f'Must be at most {max_val} characters.')
            elif rule == 'email':
                if value and not re.match(r'^[^@]+@[^@]+\.[^@]+$', value):
                    errors.append('Must be a valid email address.')

        return errors

    def get_errors(self) -> Dict[str, List[str]]:
        """Get validation errors"""
        return self._errors

    def show_toast(self, message: str, type: str = 'info', duration: int = 3000):
        """Show toast message - will be handled by client-side"""
        if hasattr(self, 'request'):
            messages.add_message(self.request, messages.INFO if type == 'info' else messages.SUCCESS, message)

    def redirect(self, view_name: str, *args, **kwargs):
        """Redirect to another view"""
        if self._is_voltwire_request:
            url = reverse(view_name, args=args, kwargs=kwargs)
            return JsonResponse({
                'success': True,
                'redirect': url
            })
        return redirect(view_name, *args, **kwargs)

    def add_error(self, field: str, message: str):
        """Add validation error"""
        if field not in self._errors:
            self._errors[field] = []
        self._errors[field].append(message)