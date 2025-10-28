import importlib
from django.http import HttpRequest, HttpResponse
from django.utils.module_loading import import_string


def voltwire_view(component_path: str):
    """
    View function wrapper for VoltWire components.
    Usage: path('posts/create/', voltwire_view('posts.CreatePost'), name='post_create')
    """

    def view_wrapper(request: HttpRequest, *args, **kwargs):
        # Import and instantiate the component
        try:
            component_class = import_string(f"{component_path}")
            component_instance = component_class()
            return component_instance.dispatch(request, *args, **kwargs)
        except (ImportError, AttributeError) as e:
            from django.http import HttpResponseServerError
            return HttpResponseServerError(f"Component not found: {component_path}")

    return view_wrapper