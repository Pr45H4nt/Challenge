from django.utils import timezone
from .models import Session, SystemStatus
from datetime import date

class SessionDeadlineMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        today = date.today()

        last_check_obj, created = SystemStatus.objects.get_or_create(key="last_session_check", defaults={"value": str(today)})

        if created or last_check_obj.value != str(today):
            expired_sessions = Session.objects.filter(
                auto_end=True,
                deadline__lt=today,
                finished_at__isnull=True
            )
            for session in expired_sessions:
                session.updateSessionRanking()
                session.finished_at = timezone.make_aware(
                    timezone.datetime.combine(session.deadline, timezone.datetime.min.time())
                )
                session.save(update_fields=["finished_at"])
            
            last_check_obj.value = str(today)
            last_check_obj.save(update_fields=["value"])
        return self.get_response(request)