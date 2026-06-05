from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import OlympicEvent, OlympicClassroom, Team, Olympian


class OlympicEventForm(forms.ModelForm):
    """Форма для создания и редактирования олимпиадного мероприятия"""
    class Meta:
        model = OlympicEvent
        fields = ['name', 'subject', 'date', 'is_team_event', 'pc_mode']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Например: Всерос по информатике'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Информатика / Математика'
            }),
            'date': forms.DateTimeInput(attrs={
                'class': 'form-control', 
                'type': 'datetime-local'
            }),
            'is_team_event': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'pc_mode': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def clean_date(self):
        date = self.cleaned_data.get('date')
        if date and date < timezone.now():
            raise ValidationError(
                'Дата и время проведения не могут быть в прошлом.'
            )
        return date


class OlympicClassroomForm(forms.ModelForm):
    """Форма для добавления и конфигурирования аудиторий"""
    class Meta:
        model = OlympicClassroom
        fields = ['number', 'rows_count', 'desks_per_row', 'inspector']
        widgets = {
            'number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '401, 23А'}),
            'rows_count': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
            'desks_per_row': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10}),
            'inspector': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Иванов И.И., Петров П.П.'}),
        }


class OlympianForm(forms.ModelForm):
    """Форма индивидуального добавления/редактирования участника"""
    
    team_choice = forms.ModelChoiceField(
        queryset=Team.objects.none(),
        required=False,
        label="Существующая команда",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    new_team_name = forms.CharField(
        required=False,
        label="Или создать новую команду",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Оставьте пустым для автогенерации кода'})
    )

    class Meta:
        model = Olympian
        fields = [
            'full_name', 'height', 'eyesight', 'hearing', 
            'health_group', 'gpa', 'sociability', 'school', 'origin_class'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'min': 100, 'max': 220}),
            'eyesight': forms.NumberInput(attrs={'class': 'form-control', 'step': 0.1}),
            'hearing': forms.Select(attrs={'class': 'form-control'}),
            'health_group': forms.Select(attrs={'class': 'form-control'}),
            'gpa': forms.NumberInput(attrs={'class': 'form-control', 'step': 0.01}),
            'sociability': forms.Select(attrs={'class': 'form-control'}),
            'school': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Лицей №3, МАОУ СОШ №1'}),
            'origin_class': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '11А, 10-2'}),
        }

    def __init__(self, *args, **kwargs):
        classroom = kwargs.pop('classroom', None)
        super().__init__(*args, **kwargs)
        if classroom:
            self.fields['team_choice'].queryset = Team.objects.filter(classroom=classroom)


class OlympicImportForm(forms.Form):
    """Форма для загрузки CSV-файла со списком участников олимпиады"""
    file = forms.FileField(
        label="Выберите файл списка (.csv)",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv'})
    )

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file and not file.name.endswith('.csv'):
            raise ValidationError('Разрешены только файлы с расширением .csv')
        return file
