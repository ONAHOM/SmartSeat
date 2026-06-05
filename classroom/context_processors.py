from .models import Classroom
from django.contrib.auth import get_user_model

user = get_user_model()


def sidebar_classrooms(request):
    if request.user.is_authenticated:
        return {'sidebar_classes': Classroom.objects.filter(teacher=request.user)}
    return {'sidebar_classes': []}
