from .models import OlympicEvent


def olympic_sidebar_events(request):
    if request.user.is_authenticated:
        return {
            'sidebar_events': OlympicEvent.objects.filter(creator=request.user)
        }
    return {'sidebar_events': []}