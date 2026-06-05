from django.db import models
from core.models import BaseClassroom
from django.contrib.auth import get_user_model
from .validators import letter_value

User = get_user_model()


class Classroom(BaseClassroom):
    """Школьный класс"""
    teacher = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='school_classrooms',
        verbose_name="Классный руководитель"
    )
    letter = models.CharField(
        "Буква класса",
        max_length=1,
        default='А',
        validators=[letter_value]
    )

    class Meta:
        verbose_name = "Школьный класс"
        verbose_name_plural = "Школьные классы"

    def __str__(self):
        return f"Кабинет {self.number}"
