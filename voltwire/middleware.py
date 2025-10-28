import re
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.urls import resolve, Resolver404


class VoltWireMiddleware(MiddlewareMixin):
    """
    Middleware to handle VoltWire-specific functionality:
    - SPA navigation
    - Component updates
    - Request/response processing
    """

    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response

    def process_request(self, request):
        """Process incoming requests for VoltWire features"""
        # Check if this is a VoltWire SPA request
        if self._is_voltwire_spa_request(request):
            request.is_voltwire_spa = True

        # Check if this is a VoltWire component request
        if self._is_voltwire_component_request(request):
            request.is_voltwire_component = True

        return None

    def process_response(self, request, response):
        """Process outgoing responses for VoltWire features"""
        # Add VoltWire headers for SPA requests
        if hasattr(request, 'is_voltwire_spa') and request.is_voltwire_spa:
            response['X-VoltWire-SPA'] = 'true'

        # Add JavaScript for auto-inclusion
        if (getattr(settings, 'VOLTWIRE', {}).get('AUTO_INCLUDE_SCRIPTS', True) and
                response.get('content-type', '').startswith('text/html') and
                not getattr(response, 'streaming', False)):

            content = response.content.decode('utf-8')
            if '</head>' in content:
                script_tag = '<script src="/static/voltwire/js/voltwire.js"></script>'
                content = content.replace('</head>', f'{script_tag}\n</head>')
                response.content = content.encode('utf-8')

        return response

    def _is_voltwire_spa_request(self, request):
        """Check if request is for SPA navigation"""
        return (request.headers.get('X-VoltWire-SPA') == 'true' or
                getattr(request, 'is_voltwire_spa', False))

    def _is_voltwire_component_request(self, request):
        """Check if request is for component update"""
        return request.headers.get('X-VoltWire-Request') == 'true'