# middleware.py
from datetime import datetime
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
