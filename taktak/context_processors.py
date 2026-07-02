from .models import Announcement


def active_announcement(request):
    announcement = Announcement.objects.filter(is_active=True).order_by('-created_at').first()
    return {'active_announcement': announcement}
