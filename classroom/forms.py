from django import forms
from .models import Classroom


class ClassroomForm(forms.ModelForm):
    class Meta:
        model = Classroom
        fields = ['number', 'letter', 'rows_count', 'desks_per_row', 'teacher']
        labels = {
            'number': 'Номер класса',
            'letter': 'Буква',
            'rows_count': 'Количество рядов',
            'desks_per_row': 'Парт в ряду',
            'teacher': 'Преподаватель',
        }
        widgets = {
            'letter': forms.TextInput(attrs={'placeholder': 'Например, А или Б'}),
        }