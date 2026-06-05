import uuid
from django.db import models
from django.contrib.auth import get_user_model
from core.models import BaseClassroom, BaseParticipant

User = get_user_model()


class OlympicEvent(models.Model):
    """Модель олимпиадного мероприятия (турнира)"""
    name = models.CharField("Название олимпиады", max_length=255)
    subject = models.CharField("Предмет / Направление", max_length=100, blank=True)
    date = models.DateTimeField("Дата и время проведения", null=True, blank=True)
    
    is_team_event = models.BooleanField("Командная олимпиада", default=False)
    pc_mode = models.BooleanField("Режим компьютеров", default=False)

    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_olympic_events',
        verbose_name="Создатель"
    )

    class Meta:
        verbose_name = "Олимпиадное мероприятие"
        verbose_name_plural = "Олимпиадные мероприятия"

    def __str__(self):
        return self.name


class OlympicClassroom(BaseClassroom):
    """Кабинет для проведения олимпиад"""
    event = models.ForeignKey(
        OlympicEvent,
        on_delete=models.CASCADE,
        related_name='classrooms',
        verbose_name="Олимпиада"
    )
    inspector = models.CharField("ФИО проверяющего", max_length=255, blank=True)

    class Meta:
        verbose_name = "Олимпиадная аудитория"
        verbose_name_plural = "Олимпиадные аудитории"

    def __str__(self):
        return f"Аудитория {self.number} ({self.event.name})"


class Team(models.Model):
    """Отдельная сущность для олимпиадной команды"""
    name = models.CharField(
        "Название или код команды",
        max_length=100,
        help_text="Если не заполнено, сгенерируется автоматически"
    )
    classroom = models.ForeignKey(
        OlympicClassroom,
        on_delete=models.CASCADE,
        related_name='teams',
        verbose_name="Назначенная аудитория"
    )

    class Meta:
        verbose_name = "Команда"
        verbose_name_plural = "Команды"

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = f"TEAM-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Olympian(BaseParticipant):
    """Модель участника олимпиады"""
    school = models.CharField("Учебное заведение (Школа)", max_length=255)
    origin_class = models.CharField("Исходный класс/параллель", max_length=50)

    team = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        related_name='members',
        verbose_name="Команда",
        null=True, blank=True,
        help_text="Оставлять пустым, если олимпиада индивидуальная"
    )
    classroom = models.ForeignKey(
        OlympicClassroom,
        on_delete=models.CASCADE,
        related_name='olympians',
        verbose_name="Назначенная аудитория",
        null=True, blank=True
    )

    class Meta(BaseParticipant.Meta):
        verbose_name = "Олимпиадник"
        verbose_name_plural = "Олимпиадники"

    def __str__(self):
        return f"{self.full_name} | {self.school}"
