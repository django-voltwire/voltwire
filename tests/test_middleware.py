from django.test import TestCase, RequestFactory
from django.http import HttpResponse
from voltwire.middleware import VoltWireMiddleware


class VoltWireMiddlewareTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = VoltWireMiddleware(lambda r: HttpResponse())

    def test_voltwire_spa_request(self):
        """Test SPA request detection"""
        request = self.factory.get('/test/',
                                   HTTP_X_VOLTWIRE_SPA='true')

        self.middleware.process_request(request)
        self.assertTrue(hasattr(request, 'is_voltwire_spa'))
        self.assertTrue(request.is_voltwire_spa)

    def test_voltwire_component_request(self):
        """Test component request detection"""
        request = self.factory.post('/test/',
                                    HTTP_X_VOLTWIRE_REQUEST='true')

        self.middleware.process_request(request)
        self.assertTrue(hasattr(request, 'is_voltwire_component'))
        self.assertTrue(request.is_voltwire_component)