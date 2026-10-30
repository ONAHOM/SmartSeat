from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.db.models import Count
from .models import Classroom


# 1. Список классов текущего преподавателя
class ClassroomListView(LoginRequiredMixin, ListView):
    model = Classroom
    context_object_name = "classrooms"
    ordering = 'number'
    
    def get_queryset(self):
        # ⚡ Bolt: Prevent N+1 queries in template loop over classrooms
        # by annotating the student count here instead of hitting .count() on each iteration.
        return Classroom.objects.filter(teacher=self.request.user).annotate(
            students_count=Count('students')
        )


# 2. Детальная информация о классе
class ClassroomDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Classroom
    context_object_name = "classroom"

    def test_func(self):
        obj = self.get_object()
        return obj.teacher == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ученики уже доступны через classroom.students.all, 
        # но здесь можно добавить форму или статистику
        return context


# 3. Создание нового класса
class ClassroomCreateView(LoginRequiredMixin, CreateView):
    model = Classroom
    template_name = "classroom/classroom_form.html"
    fields = ['number', 'letter', 'rows_count', 'desks_per_row']
    success_url = reverse_lazy('classroom:list')

    def form_valid(self, form):
        form.instance.teacher = self.request.user
        return super().form_valid(form)


# 4. Редактирование класса
class ClassroomUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Classroom
    template_name = "classroom/classroom_form.html"
    fields = ['number', 'letter', 'rows_count', 'desks_per_row']
    success_url = reverse_lazy('classroom:list')

    def test_func(self):
        return self.get_object().teacher == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Берем ID из URL
        context['class_id'] = self.kwargs.get('pk')
        context['classroom'] = get_object_or_404(Classroom, pk=self.kwargs.get('pk'))
        return context


# 5. Удаление класса
class ClassroomDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Classroom
    template_name = "classroom/classroom_confirm_delete.html"
    success_url = reverse_lazy('classroom:list')

    def test_func(self):
        return self.get_object().teacher == self.request.user
