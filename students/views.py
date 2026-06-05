from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, UpdateView, DeleteView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Student
from .forms import StudentForm, StudentImportForm
from .utils import import_students_from_csv
from .mixins import ClassroomTeacherRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404
from django.shortcuts import redirect
from django.contrib.staticfiles.storage import staticfiles_storage


class StudentCreateView(LoginRequiredMixin, ClassroomTeacherRequiredMixin, CreateView):
    model = Student
    form_class = StudentForm
    template_name = "students/student_form.html"

    def get_form_kwargs(self):
        """Передаем текущий класс в форму для фильтрации одноклассников."""
        kwargs = super().get_form_kwargs()
        kwargs['classroom'] = self.classroom
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['classroom'] = self.classroom
        return context

    def form_valid(self, form):
        """Привязываем создаваемого вручную ученика к текущему классу."""
        student = form.save(commit=False)
        student.classroom = self.classroom
        return super().form_valid(form)


class StudentCreateFromFileView(LoginRequiredMixin, ClassroomTeacherRequiredMixin, FormView):
    form_class = StudentImportForm
    template_name = "students/student_import_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['classroom'] = self.classroom
        return context

    def form_valid(self, form):
        """Вызывается автоматически, если файл прошел валидацию в форме."""
        # Передаем файл в изолированный сервис
        success = import_students_from_csv(
            self.request,
            self.classroom,
            self.request.FILES['file']
        )

        if success:
            # redirect() возвращает чистый HttpResponseRedirect, предотвращая дублирование POST
            return redirect(self.get_success_url())

        # Если сервис вернул False, принудительно пишем ошибку в контекст формы
        form.add_error(None, "Критическая ошибка в структуре данных файла. Импорт отменен.")

        # Вызываем родительский метод строго через super(), чтобы избежать рекурсии
        return super().form_invalid(form)


class StudentDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Student
    template_name = "students/student_detail.html"
    context_object_name = "student"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['class'] = self.object.classroom
        return context

    def test_func(self):
        student = self.get_object()
        return student.classroom.teacher == self.request.user


class StudentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Student
    form_class = StudentForm 
    template_name = "students/student_form.html"

    def test_func(self):
        return self.get_object().classroom.teacher == self.user_passes_test_custom()

    def user_passes_test_custom(self):
        return self.request.user

    def get_form_kwargs(self):
        """Передаем класс редактируемого студента в форму."""
        kwargs = super().get_form_kwargs()
        kwargs['classroom'] = self.get_object().classroom
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['classroom'] = self.get_object().classroom
        return context

    def get_success_url(self):
        return reverse_lazy('student:detail', kwargs={'pk': self.object.pk})


class StudentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Student
    template_name = "students/student_confirm_delete.html"

    def test_func(self):
        return self.get_object().classroom.teacher == self.request.user

    def get_success_url(self):
        return reverse_lazy('classroom:detail', kwargs={'pk': self.object.classroom.pk})


@login_required
def download_student_import_template(request):
    # Указываем относительный путь внутри статики
    relative_path = 'students/students_template.csv'

    if staticfiles_storage.exists(relative_path):
        with staticfiles_storage.open(relative_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="text/csv")
            # Заставляем браузер именно скачивать файл, а не открывать вкладку
            response['Content-Disposition'] = 'attachment; filename="students_template.csv"'
            return response

    raise Http404("Файл шаблона не найден в статических файлах")
