from django.core.exceptions import ValidationError


def letter_value(value):
    if value not in ('ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮЁ'):
        raise ValidationError(
            'Ожидается одна заглавная русская буква'
        )
