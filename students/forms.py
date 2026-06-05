from django import forms
from .models import Student


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        # Исключаем 'classroom', так как он передается через URL во View
        fields = [
            'full_name', 
            'height', 
            'eyesight', 
            'hearing', 
            'health_group', 
            'gpa', 
            'sociability', 
            'preferred_classmates', 
            'disliked_classmates'
        ]
        
        labels = {
            'full_name': 'ФИО ученика',
            'height': 'Рост (см)',
            'eyesight': 'Зрение (диоптрии, например: -2.5 или 0)',
            'hearing': 'Степень тугоухости (0 — норма, 1-4 — степень)',
            'health_group': 'Медицинская группа здоровья (1-5)',
            'gpa': 'Средний балл успеваемости (GPA)',
            'sociability': 'Уровень общительности/лидерства (1-3)',
            'preferred_classmates': 'Желаемые соседи по парте',
            'disliked_classmates': 'Нежелательные соседи по парте',
        }

        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder': 'Иванов Иван Иванович'}),
            'height': forms.NumberInput(attrs={'placeholder': 'Например: 165', 'min': 100, 'max': 220}),
            'eyesight': forms.NumberInput(attrs={'placeholder': '0.0', 'step': '0.25'}),
            'gpa': forms.NumberInput(attrs={'placeholder': '4.50', 'min': '2.0', 'max': '5.0', 'step': '0.01'}),

            # Виджеты множественного выбора для отношений ManyToMany
            'preferred_classmates': forms.SelectMultiple(attrs={
                'class': 'chosen-select',
                'help_text': 'Зажмите Ctrl (или Cmd на Mac), чтобы выбрать несколько человек'
            }),
            'disliked_classmates': forms.SelectMultiple(attrs={
                'class': 'chosen-select',
                'help_text': 'Зажмите Ctrl (или Cmd на Mac), чтобы выбрать несколько человек'
            }),
        }

    def __init__(self, *args, **kwargs):
        # Перехватываем объект класса, если он передан из View, чтобы ограничить списки выбора
        classroom = kwargs.pop('classroom', None)
        super().__init__(*args, **kwargs)

        # Фильтруем списки одноклассников, чтобы показывать только учеников ЭТОГО ЖЕ класса
        if classroom:
            queryset = Student.objects.filter(classroom=classroom)
            if self.instance and self.instance.pk:
                # Исключаем самого себя из списка возможных соседей при редактировании
                queryset = queryset.exclude(pk=self.instance.pk)

            self.fields['preferred_classmates'].queryset = queryset
            self.fields['disliked_classmates'].queryset = queryset


class StudentImportForm(forms.Form):
    file = forms.FileField(
        label="Файл со списком класса (.csv)",
        help_text="Файл должен быть в кодировке UTF-8 с разделителями-запятыми."
    )

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file and not file.name.endswith('.csv'):
            raise forms.ValidationError("Допускаются только файлы с расширением .csv")
        return file
