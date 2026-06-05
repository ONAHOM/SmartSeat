from django.db import models
from core.models import BaseParticipant
from classroom.models import Classroom


class Student(BaseParticipant):
    """Школьный ученик со спецификой социального соседства"""
    preferred_classmates = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='wished_by',
        verbose_name="С кем хочет сидеть"
    )
    disliked_classmates = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='avoided_by',
        verbose_name="С кем НЕ хочет сидеть"
    )
    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.CASCADE,
        related_name='students',
        verbose_name="Класс"
    )

    class Meta(BaseParticipant.Meta):
        verbose_name = "Ученик"
        verbose_name_plural = "Ученики"

    def __str__(self):
        return f"{self.full_name} ({self.classroom.number})"
