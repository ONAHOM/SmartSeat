from django.core.exceptions import ValidationError


def height_value(value: int) -> None:
    if value < 100 or value > 250:
        raise ValidationError(
            'Ожидается рост от 100 см до 250 см'
        )
