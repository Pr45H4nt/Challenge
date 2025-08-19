# middleware.py
from datetime import datetime
from django.http import Http404
from django.utils.timezone import make_aware


class UpdateLastOnlineMiddleware:
    """
    Middleware to update the `last_online` field of the user on each request.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only update if the user is authenticated
        if request.user.is_authenticated:
            # Set the last_online field to the current time
            request.user.last_online = make_aware(datetime.now())  # Ensure timezone-aware datetime
            request.user.save(update_fields=['last_online'])

        response = self.get_response(request)
        return response
     


class SuperuserAdminOnlyMiddleware:
    """
    raise 404 for non-superusers trying to access /admin/
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if request is for admin and user is not superuser
        if request.path.startswith('/admin/') and (not request.user.is_superuser):
            raise Http404

        return self.get_response(request)
