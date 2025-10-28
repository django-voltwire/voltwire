from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from voltwire.components import VoltWireComponent
from voltwire.decorators import layout, title, validate


class TestVoltWireComponent(VoltWireComponent):
    """Test component for unit testing"""

    @validate('required|min:3')

    test_property = ''

    def get(self, request):
        return self.render(request)


class VoltWireComponentTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_component_initialization(self):
        """Test component initialization"""
        component = TestVoltWireComponent()
        self.assertEqual(component.test_property, '')

    def test_component_dispatch(self):
        """Test component request dispatch"""
        request = self.factory.get('/test/')
        component = TestVoltWireComponent()

        response = component.dispatch(request)
        self.assertEqual(response.status_code, 200)

    def test_validation(self):
        """Test property validation"""
        component = TestVoltWireComponent()
        component.test_property = 'ab'  # Too short

        is_valid = component.is_valid()
        self.assertFalse(is_valid)
        self.assertIn('test_property', component.get_errors())

    def test_redirect_voltwire_request(self):
        """Test redirect for VoltWire requests"""
        request = self.factory.post('/test/',
                                    HTTP_X_VOLTWIRE_REQUEST='true')
        component = TestVoltWireComponent()
        component.request = request

        response = component.redirect('admin:index')
        self.assertEqual(response.status_code, 200)
        self.assertIn('redirect', response.json())