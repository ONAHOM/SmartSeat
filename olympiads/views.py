from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, FormView
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
import csv
import io
from django.db import transaction
from django.db.models import Q, Prefetch

from .models import OlympicEvent, OlympicClassroom, Team, Olympian
from .forms import OlympicEventForm, OlympicClassroomForm, OlympianForm, OlympicImportForm
from .utils import distribute_olympians_to_classrooms
from .genetic_engine import run_genetic_algorithm_for_classroom

# =========================================================================
# 1. УПРАВЛЕНИЕ МЕРОПРИЯТИЯМИ (OlympicEvent)
# =========================================================================


class OlympicEventListView(LoginRequiredMixin, ListView):
    model = OlympicEvent
    template_name = 'olympiads/event_list.html'
    context_object_name = 'events'

    def get_queryset(self):
        return OlympicEvent.objects.filter(creator=self.request.user)


class OlympicEventDetailView(LoginRequiredMixin, DetailView):
    model = OlympicEvent
    template_name = 'olympiads/event_detail.html'
    context_object_name = 'event'

    def get_queryset(self):
        # ⚡ Bolt: prefetch classrooms to prevent N+1 query in the view's get_context_data
        return OlympicEvent.objects.filter(creator=self.request.user).prefetch_related('classrooms')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['classrooms'] = self.object.classrooms.all()
        return context


class OlympicEventCreateView(LoginRequiredMixin, CreateView):
    model = OlympicEvent
    form_class = OlympicEventForm
    template_name = 'olympiads/event_form.html'
    success_url = reverse_lazy('olympiads:event_list')

    def form_valid(self, form):
        form.instance.creator = self.request.user
        return super().form_valid(form)


class OlympicEventUpdateView(LoginRequiredMixin, UpdateView):
    model = OlympicEvent
    form_class = OlympicEventForm
    template_name = 'olympiads/event_form.html'
    success_url = reverse_lazy('olympiads:event_list')

    def get_queryset(self):
        return OlympicEvent.objects.filter(creator=self.request.user)


class OlympicEventDeleteView(LoginRequiredMixin, DeleteView):
    model = OlympicEvent
    template_name = 'olympiads/event_confirm_delete.html'
    success_url = reverse_lazy('olympiads:event_list')

    def get_queryset(self):
        return OlympicEvent.objects.filter(creator=self.request.user)


# =========================================================================
# 2. УПРАВЛЕНИЕ АУДИТОРИЯМИ (OlympicClassroom)
# =========================================================================

class OlympicClassroomCreateView(LoginRequiredMixin, CreateView):
    model = OlympicClassroom
    form_class = OlympicClassroomForm
    template_name = 'olympiads/classroom_form.html'

    def form_valid(self, form):
        event = get_object_or_404(OlympicEvent, pk=self.kwargs['event_id'], creator=self.request.user)
        form.instance.event = event
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('olympiads:event_detail', kwargs={'pk': self.kwargs['event_id']})


class OlympicClassroomDetailView(LoginRequiredMixin, DetailView):
    model = OlympicClassroom
    template_name = 'olympiads/classroom_detail.html'
    context_object_name = 'classroom'

    def get_queryset(self):
        # ⚡ Bolt: prefetch olympians with select_related on team to avoid N+1 queries in template
        # Also prefetch teams to optimize context data retrieval
        return OlympicClassroom.objects.filter(event__creator=self.request.user).prefetch_related(
            Prefetch('olympians', queryset=Olympian.objects.select_related('team')),
            'teams'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['olympians'] = self.object.olympians.all()
        context['teams'] = self.object.teams.all()
        return context


class OlympicClassroomUpdateView(LoginRequiredMixin, UpdateView):
    model = OlympicClassroom
    form_class = OlympicClassroomForm
    template_name = 'olympiads/classroom_form.html'

    def get_queryset(self):
        return OlympicClassroom.objects.filter(event__creator=self.request.user)

    def get_success_url(self):
        return reverse('olympiads:event_detail', kwargs={'pk': self.object.event.id})


class OlympicClassroomDeleteView(LoginRequiredMixin, DeleteView):
    model = OlympicClassroom
    template_name = 'olympiads/classroom_confirm_delete.html'

    def get_queryset(self):
        return OlympicClassroom.objects.filter(event__creator=self.request.user)

    def get_success_url(self):
        return reverse('olympiads:event_detail', kwargs={'pk': self.object.event.id})


# =========================================================================
# 3. УПРАВЛЕНИЕ УЧАСТНИКАМИ (Olympian)
# =========================================================================

class OlympianCreateView(LoginRequiredMixin, CreateView):
    model = Olympian
    form_class = OlympianForm
    template_name = 'olympiads/olympian_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['classroom'] = get_object_or_404(
            OlympicClassroom, 
            pk=self.kwargs['classroom_id'], 
            event__creator=self.request.user
        )
        return kwargs

    def form_valid(self, form):
        classroom = get_object_or_404(
            OlympicClassroom, 
            pk=self.kwargs['classroom_id'], 
            event__creator=self.request.user
        )
        form.instance.classroom = classroom

        # Исправлено: is_team_event теперь запрашивается у event
        if classroom.event.is_team_event:
            new_team_name = form.cleaned_data.get('new_team_name')
            team_choice = form.cleaned_data.get('team_choice')

            if new_team_name:
                team = Team.objects.create(name=new_team_name, classroom=classroom)
                form.instance.team = team
            elif team_choice:
                form.instance.team = team_choice
            else:
                team = Team.objects.create(name="", classroom=classroom)
                form.instance.team = team

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Подтягиваем аудиторию по id из URL и передаем ее event в контекст шаблона
        classroom = get_object_or_404(OlympicClassroom, pk=self.kwargs['classroom_id'])
        context['event'] = classroom.event
        return context

    def get_success_url(self):
        return reverse('olympiads:classroom_detail', kwargs={'pk': self.kwargs['classroom_id']})


class OlympianUpdateView(LoginRequiredMixin, UpdateView):
    model = Olympian
    form_class = OlympianForm
    template_name = 'olympiads/olympian_form.html'

    def get_queryset(self):
        return Olympian.objects.filter(classroom__event__creator=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['classroom'] = self.object.classroom
        return kwargs

    def get_success_url(self):
        return reverse('olympiads:classroom_detail', kwargs={'pk': self.object.classroom.id})


class OlympianDeleteView(LoginRequiredMixin, DeleteView):
    model = Olympian
    template_name = 'olympiads/olympian_confirm_delete.html'

    def get_queryset(self):
        return Olympian.objects.filter(classroom__event__creator=self.request.user)

    def get_success_url(self):
        return reverse('olympiads:classroom_detail', kwargs={'pk': self.object.classroom.id})


class OlympicImportView(LoginRequiredMixin, FormView):
    """Контроллер для пакетного импорта участников через CSV с валидацией регламента турнира"""
    form_class = OlympicImportForm
    template_name = 'olympiads/import_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['event'] = get_object_or_404(OlympicEvent, pk=self.kwargs['event_id'], creator=self.request.user)
        return context

    def form_invalid(self, form):
        """Гарантирует передачу объекта event в контекст при ошибках валидации формы"""
        context = self.get_context_data(form=form)
        return self.render_to_response(context)

    def form_valid(self, form):
        event = get_object_or_404(OlympicEvent, pk=self.kwargs['event_id'], creator=self.request.user)
        csv_file = form.cleaned_data['file']
        
        # Разрешение конфликтов кодировки файла
        try:
            file_data = csv_file.read().decode('utf-8')
        except UnicodeDecodeError:
            csv_file.seek(0)
            file_data = csv_file.read().decode('cp1251')

        io_string = io.StringIO(file_data)
        
        try:
            dialect = csv.Sniffer().sniff(io_string.read(2048), delimiters=',;')
            io_string.seek(0)
            reader = csv.reader(io_string, dialect)
        except csv.Error:
            io_string.seek(0)
            reader = csv.reader(io_string)

        header = next(reader, None)  # Пропускаем заголовок таблицы
        
        olympians_to_create = []
        errors = []
        row_num = 1

        for row in reader:
            row_num += 1
            # Пропуск пустых строк
            if not row or not any(field.strip() for field in row):
                continue
                
            if len(row) < 5:
                errors.append(f"Строка {row_num}: Недостаточно колонок (ожидается минимум 5: ФИО, Рост, Зрение, Школа, Класс).")
                continue
                
            full_name = row[0].strip()
            
            # Безопасный парсинг роста (Защита от ValueError при сдвиге колонок)
            try:
                height = int(row[1].strip() or 160)
            except ValueError:
                errors.append(f"Строка {row_num} [{full_name}]: Неверный формат роста '{row[1]}' (ожидается целое число).")
                continue
            
            # Безопасный парсинг зрения (Защита от ValueError)
            try:
                eyesight_str = row[2].strip().replace(',', '.')
                eyesight = float(eyesight_str or 1.0)
            except ValueError:
                errors.append(f"Строка {row_num} [{full_name}]: Неверный формат зрения '{row[2]}' (ожидается число, например -5.5).")
                continue
                
            school = row[3].strip()
            origin_class = row[4].strip()
            
            # Название команды (6-я колонка, если передана)
            team_name = row[5].strip() if len(row) > 5 else ""

            # Валидация логики соответствия регламенту олимпиады
            if event.is_team_event:
                if not team_name:
                    errors.append(f"Строка {row_num} [{full_name}]: Олимпиада командная, но не указано название команды.")
                    continue
            else:
                if team_name:
                    errors.append(f"Строка {row_num} [{full_name}]: Олимпиада индивидуальная, но обнаружено поле команды ('{team_name}').")
                    continue

            olympian = Olympian(
                full_name=full_name,
                height=height,
                eyesight=eyesight,
                school=school,
                origin_class=origin_class,
                gpa=4.0,
                sociability=2  # Исправлено: Числовое значение MED
            )
            olympian._temp_team_name = team_name  # Временный атрибут для сборки команд в БД
            olympians_to_create.append(olympian)

        # Если обнаружена хотя бы одна ошибка структуры или регламента — прерываем весь импорт
        if errors:
            for error in errors[:10]:
                messages.error(self.request, error)
            if len(errors) > 10:
                messages.error(self.request, f"И еще {len(errors) - 10} ошибок в структуре файла...")
            return self.render_to_response(self.get_context_data(form=form))

        if olympians_to_create:
            with transaction.atomic():
                # Проверяем наличие хотя бы одной аудитории для черновой привязки пулла
                default_classroom = event.classrooms.first()
                if not default_classroom:
                    messages.error(self.request, "Ошибка импорта: Сначала необходимо добавить хотя бы одну аудиторию к мероприятию.")
                    return self.render_to_response(self.get_context_data(form=form))

                # Если олимпиада индивидуальная, принудительно удерживаем школьников в пулле
                if not event.is_team_event:
                    for olympian in olympians_to_create:
                        olympian.classroom = default_classroom

                # Массовое создание участников
                Olympian.objects.bulk_create(olympians_to_create)
                
                # Создание команд и линковка структур (только для командных турниров)
                if event.is_team_event:
                    inserted_olympians = Olympian.objects.filter(
                        full_name__in=[o.full_name for o in olympians_to_create],
                        school__in=[o.school for o in olympians_to_create],
                        classroom=None
                    )
                    
                    team_cache = {}
                    for o_inserted in inserted_olympians:
                        matching_source = next(
                            obj for obj in olympians_to_create 
                            if obj.full_name == o_inserted.full_name and obj.school == o_inserted.school
                        )
                        t_name = matching_source._temp_team_name
                        
                        if t_name not in team_cache:
                            new_team = Team.objects.create(name=t_name, classroom=default_classroom)
                            team_cache[t_name] = new_team
                            
                        o_inserted.team = team_cache[t_name]
                        o_inserted.save()

            messages.success(self.request, f"Успешно импортировано участников: {len(olympians_to_create)}")
        else:
            messages.warning(self.request, "Файл не содержит корректных строк для импорта.")

        return redirect('olympiads:event_detail', pk=event.pk)

class OlympicClassroomImportView(LoginRequiredMixin, FormView):
    """Контроллер для пакетного импорта олимпиадных аудиторий через CSV"""
    form_class = OlympicImportForm
    template_name = 'olympiads/import_classroom_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['event'] = get_object_or_404(OlympicEvent, pk=self.kwargs['event_id'], creator=self.request.user)
        return context

    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        return self.render_to_response(context)

    def form_valid(self, form):
        event = get_object_or_404(OlympicEvent, pk=self.kwargs['event_id'], creator=self.request.user)
        csv_file = form.cleaned_data['file']
        
        try:
            file_data = csv_file.read().decode('utf-8')
        except UnicodeDecodeError:
            csv_file.seek(0)
            file_data = csv_file.read().decode('cp1251')

        io_string = io.StringIO(file_data)
        
        try:
            dialect = csv.Sniffer().sniff(io_string.read(2048), delimiters=',;')
            io_string.seek(0)
            reader = csv.reader(io_string, dialect)
        except csv.Error:
            io_string.seek(0)
            reader = csv.reader(io_string)

        header = next(reader, None)
        
        classrooms_to_create = []
        row_num = 1

        for row in reader:
            row_num += 1
            if not row or not any(field.strip() for field in row):
                continue
                
            if len(row) < 3:
                messages.error(self.request, f"Строка {row_num}: Недостаточно колонок (ожидается минимум 3: Номер, Ряды, Места в ряду).")
                return self.render_to_response(self.get_context_data(form=form))
                
            number = row[0].strip()[:10]
            
            try:
                rows_count = int(row[1].strip() or 3)
                desks_per_row = int(row[2].strip() or 4)
            except ValueError:
                messages.error(self.request, f"Строка {row_num}: Размеры рядов и парт должны быть целыми числами.")
                return self.render_to_response(self.get_context_data(form=form))
                
            inspector = row[3].strip() if len(row) > 3 else ""

            classroom = OlympicClassroom(
                event=event,
                number=number,
                rows_count=rows_count,
                desks_per_row=desks_per_row,
                inspector=inspector
            )
            classrooms_to_create.append(classroom)

        if classrooms_to_create:
            OlympicClassroom.objects.bulk_create(classrooms_to_create)
            messages.success(self.request, f"Успешно импортировано аудиторий: {len(classrooms_to_create)}")
        else:
            messages.warning(self.request, "Файл не содержит корректных строк залов.")

        return redirect('olympiads:event_detail', pk=event.pk)

class CalculateGlobalOlympicSeatingView(LoginRequiredMixin, View):
    """Глобальный контроллер: распределение пулла по залам + запуск генетических алгоритмов локальной посадки"""
    def post(self, request, event_id):
        event = get_object_or_404(OlympicEvent, pk=event_id, creator=request.user)
        classrooms = event.classrooms.all()
        
        # Получение полного пулла участников (включая нераспределенные сущности после CSV)
        event_olympians = Olympian.objects.filter(
            Q(classroom__event=event) | Q(team__classroom__event=event)
        ).distinct()
        
        if not classrooms.exists():
            messages.error(request, "Невозможно запустить расчет: в мероприятии нет аудиторий.")
            return redirect('olympiads:event_detail', pk=event.pk)
            
        if not event_olympians.exists():
            messages.error(request, "Невозможно запустить расчет: отсутствуют зарегистрированные участники.")
            return redirect('olympiads:event_detail', pk=event.pk)
            
        try:
            # Шаг 1: Равномерное Round-Robin распределение участников/команд по залам
            allocation_result = distribute_olympians_to_classrooms(event, event_olympians, classrooms)
            
            # Шаг 2: Фиксация распределения в БД внутри транзакции
            with transaction.atomic():
                updated_teams = set()
                
                for classroom_id, olympians in allocation_result.items():
                    classroom_obj = classrooms.get(id=classroom_id)
                    
                    for olympian in olympians:
                        olympian.classroom = classroom_obj
                        olympian.save()
                        
                        if event.is_team_event and olympian.team_id and (olympian.team_id not in updated_teams):
                            team_obj = olympian.team
                            team_obj.classroom = classroom_obj
                            team_obj.save()
                            updated_teams.add(olympian.team_id)
            
            # Шаг 3: Поочередный запуск локального генетического алгоритма оптимизации мест для каждого зала
            successful_rooms = 0
            for room in classrooms:
                success = run_genetic_algorithm_for_classroom(room.id)
                if success:
                    successful_rooms += 1
            
            if successful_rooms == classrooms.count():
                messages.success(
                    request, 
                    f"Глобальный балансировщик распределил {event_olympians.count()} участников. "
                    f"Генетический алгоритм успешно построил карты рассадки для всех залов ({successful_rooms}/{classrooms.count()})."
                )
            else:
                messages.warning(
                    request, 
                    f"Участники распределены по залам, но карты рассадки построены частично: "
                    f"успешно {successful_rooms} из {classrooms.count()} аудиторий. Проверьте вместимость залов."
                )
            
        except ValueError as e:
            messages.error(request, f"Ошибка оптимизации: {str(e)}")
            
        return redirect('olympiads:event_detail', pk=event.pk)