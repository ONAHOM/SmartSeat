from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class BaseClassroom(models.Model):
    """Абстрактная модель аудитории/кабинета"""
    number = models.CharField("Номер кабинета", max_length=10)
    rows_count = models.PositiveSmallIntegerField("Количество рядов")
    desks_per_row = models.PositiveSmallIntegerField("Парт в ряду")

    seating_chart = models.ImageField(
        "Схема рассадки",
        upload_to='seating_charts/',
        null=True, blank=True
    )
    seating_metrics = models.JSONField("Метрики качества", null=True, blank=True)

    class Meta:
        abstract = True


class BaseParticipant(models.Model):
    """Абстрактная модель физиологических параметров человека"""
    class HearingDegree(models.IntegerChoices):
        NORMAL = 0, 'Нормальный слух (до 25 дБ)'
        DEGREE_1 = 1, '1 степень — Легкая (26-40 дБ)'
        DEGREE_2 = 2, '2 степень — Средней тяжести (41-55 дБ)'
        DEGREE_3 = 3, '3 степень — Тяжелая (56-70 дБ)'
        DEGREE_4 = 4, '4 степень — Очень тяжелая (71-90 дБ)'

    class HealthGroup(models.IntegerChoices):
        GROUP_1 = 1, 'I группа — Здоровые дети'
        GROUP_2 = 2, 'II группа — Функциональные нарушения'
        GROUP_3 = 3, 'III группа — Хронические болезни в ремиссии'
        GROUP_4 = 4, 'IV группа — Хронические болезни в активной стадии'
        GROUP_5 = 5, 'V группа — Тяжелая инвалидность'

    class SociabilityLevel(models.IntegerChoices):
        LOW = 1, 'Низкая (интроверт)'
        MEDIUM = 2, 'Средняя'
        HIGH = 3, 'Высокая (активный)'

    full_name = models.CharField("ФИО", max_length=255)
    height = models.PositiveIntegerField("Рост (см)")

    eyesight = models.FloatField(
        "Зрение (диоптрии)",
        default=0.0,
        validators=[MinValueValidator(-20.0), MaxValueValidator(20.0)]
    )
    hearing = models.PositiveSmallIntegerField(
        "Слух (степень)",
        choices=HearingDegree.choices,
        default=HearingDegree.NORMAL
    )
    health_group = models.PositiveSmallIntegerField(
        "Группа здоровья",
        choices=HealthGroup.choices,
        default=HealthGroup.GROUP_1
    )
    gpa = models.DecimalField(
        "Средний балл (GPA)",
        max_digits=3,
        decimal_places=2,
        default=4.00,
        validators=[MinValueValidator(2.00), MaxValueValidator(5.00)]
    )
    sociability = models.PositiveSmallIntegerField(
        "Уровень общительности",
        choices=SociabilityLevel.choices,
        default=SociabilityLevel.MEDIUM
    )

    class Meta:
        abstract = True
        ordering = ['full_name']
