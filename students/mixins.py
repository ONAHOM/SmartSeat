from classroom.models import Classroom
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404


class ClassroomTeacherRequiredMixin:
    """
    Примесь для автоматического получения объекта Classroom
    и проверки, что текущий пользователь является его учителем.
    """
    def get_classroom(self):
        classroom = get_object_or_404(Classroom, pk=self.kwargs['class_id'])
        if classroom.teacher != self.request.user:
            raise PermissionDenied
        return classroom

    def dispatch(self, request, *args, **kwargs):
        self.classroom = self.get_classroom()
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        """Единый адрес перенаправления после успешных действий."""
        return reverse_lazy('classroom:detail', kwargs={'pk': self.classroom.pk})