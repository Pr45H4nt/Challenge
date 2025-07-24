from functools import wraps
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied


def not_demo_user(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.username == 'demouser':
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped_view